"""cncjs_client.py — spricht mit CNCjs auf demselben Pi, wie es der Browser
tut: Zustand ueber die REST-Schnittstelle, G-Code ueber den Socket
(socket.io 2 = Engine.io 3 ueber WebSocket). Nur Python-Standardbibliothek.

Den seriellen Port oeffnet es nie selbst. Ist CNCjs nicht mit der Maschine
verbunden, meldet es das: Ein Oeffnen wuerde den Uno zuruecksetzen.

Anmeldung wie bei CNCjs selbst: ein JWT, signiert mit dem `secret` aus
~/.cncrc. Gibt es dort Benutzerkonten, nimmt es das erste aktive.
"""

import base64
import hashlib
import hmac
import json
import os
import socket
import struct
import threading
import time
import urllib.error
import urllib.request

CNCRC = os.path.expanduser('~/.cncrc')
HOST, PORT = '127.0.0.1', 8000


class CncjsFehler(Exception):
    """Fehler mit einer Meldung, die der Nutzer lesen soll."""


# -- Anmeldung ----------------------------------------------------------------

def _b64(daten):
    return base64.urlsafe_b64encode(daten).rstrip(b'=')


def token_erzeugen(cncrc=CNCRC, gueltig_s=24 * 3600, jetzt=None):
    """JWT (HS256) fuer REST und Socket von CNCjs."""
    try:
        with open(cncrc, encoding='utf-8') as f:
            conf = json.load(f)
    except (OSError, ValueError) as e:
        raise CncjsFehler('~/.cncrc nicht lesbar: %s' % e)
    secret = conf.get('secret')
    if not secret:
        raise CncjsFehler('~/.cncrc hat kein secret: CNCjs einmal starten')
    nutzer = {'id': '', 'name': 'autofokus'}
    for u in conf.get('users') or []:
        if isinstance(u, dict) and u.get('enabled', True) is not False:
            nutzer = {'id': u.get('id', ''), 'name': u.get('name', '')}
            break
    jetzt = int(time.time() if jetzt is None else jetzt)
    nutzlast = dict(nutzer, iat=jetzt, exp=jetzt + gueltig_s)
    kopf = _b64(json.dumps({'alg': 'HS256', 'typ': 'JWT'},
                           separators=(',', ':')).encode())
    rumpf = _b64(json.dumps(nutzlast, separators=(',', ':')).encode())
    sig = _b64(hmac.new(secret.encode(), kopf + b'.' + rumpf,
                        hashlib.sha256).digest())
    return (kopf + b'.' + rumpf + b'.' + sig).decode()


# -- REST -----------------------------------------------------------------------

def controller_lesen(token, host=HOST, port=PORT):
    """Liste der offenen Ports mit Zustand (GET /api/controllers)."""
    anfrage = urllib.request.Request(
        'http://%s:%d/api/controllers' % (host, port),
        headers={'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(anfrage, timeout=5) as antwort:
            return json.load(antwort)
    except urllib.error.HTTPError as e:
        raise CncjsFehler('CNCjs lehnt die Anmeldung ab (HTTP %d)' % e.code)
    except (OSError, ValueError) as e:
        raise CncjsFehler('CNCjs nicht erreichbar: %s' % e)


def offener_port(liste):
    """Der Port, mit dem CNCjs gerade verbunden ist, oder Fehler."""
    offen = [c for c in liste if c.get('port') and c.get('ready')]
    if not offen:
        raise CncjsFehler('CNCjs ist nicht mit der Maschine verbunden: '
                          'in CNCjs verbinden und Homing')
    return offen[0]


# -- Zahlen aus dem Zustand ------------------------------------------------------

def _achsen(d):
    return {a: float(d[a]) for a in 'xyz' if a in d and d[a] not in ('', None)}


def mpos(zustand):
    return _achsen(zustand.get('status', {}).get('mpos', {}))


def wpos(zustand):
    return _achsen(zustand.get('status', {}).get('wpos', {}))


def aktiv(zustand):
    return zustand.get('status', {}).get('activeState', '')


def verfahrweg(settings):
    """Maximaler Weg je Achse aus $130..$132 (Maschinenraum -weg..0)."""
    s = settings.get('settings', settings) if isinstance(settings, dict) else {}
    try:
        return {a: float(s['$13%d' % i]) for i, a in enumerate('xyz')}
    except (KeyError, ValueError, TypeError):
        raise CncjsFehler('GRBL-Einstellungen $130..$132 unbekannt: '
                          'in CNCjs einmal $$ senden')


# -- WebSocket mit socket.io 2 ----------------------------------------------------

class Verbindung:
    """Socket zu CNCjs, an einen schon offenen Port angehaengt."""

    def __init__(self, token, port_name, host=HOST, port=PORT):
        self.token, self.port_name = token, port_name
        self.host, self.port = host, port
        self.cv = threading.Condition()
        self.sock = None
        self._puffer = b''
        self._senden_lock = threading.Lock()
        self._ack_nr = 0
        self._acks = {}
        self.verbunden = False      # Namespace '/' bestaetigt
        self.geschlossen = False
        self.fehler = ''
        self.zustand = {}           # controller:state
        self.settings = {}          # controller:settings
        self.feeder = {}            # feeder:status
        self.workflow = ''          # workflow:state
        self.zeilen = []            # (zeit, text) aus serialport:read
        self.zustand_nr = 0
        self.ping_s = 25.0

    # Aufbau und Abbau

    def oeffnen(self, warten=5.0):
        try:
            self.sock = socket.create_connection((self.host, self.port), warten)
        except OSError as e:
            raise CncjsFehler('CNCjs nicht erreichbar: %s' % e)
        schluessel = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            'GET /socket.io/?EIO=3&transport=websocket&token=%s HTTP/1.1\r\n'
            'Host: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
            'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'
            % (self.token, self.host, self.port, schluessel)).encode())
        kopf = b''
        while b'\r\n\r\n' not in kopf:
            stueck = self.sock.recv(4096)
            if not stueck:
                raise CncjsFehler('CNCjs schließt die Verbindung')
            kopf += stueck
        kopf, self._puffer = kopf.split(b'\r\n\r\n', 1)
        erste = kopf.split(b'\r\n', 1)[0].decode('latin-1')
        if ' 101 ' not in erste + ' ':
            raise CncjsFehler('CNCjs lehnt den Socket ab: %s' % erste)
        self.sock.settimeout(None)
        threading.Thread(target=self._lesen_schleife, daemon=True).start()
        with self.cv:
            if not self.cv.wait_for(lambda: self.verbunden or self.fehler,
                                    warten):
                raise CncjsFehler('CNCjs antwortet nicht auf dem Socket')
            if self.fehler:
                raise CncjsFehler(self.fehler)
        threading.Thread(target=self._ping_schleife, daemon=True).start()
        # an den offenen Port anhaengen; CNCjs schickt dann den Zustand
        antwort = self.emit('open', self.port_name,
                            {'controllerType': 'Grbl'}, ack=True)
        if antwort and antwort[0]:
            raise CncjsFehler('CNCjs: %s' % antwort[0])
        with self.cv:
            if not self.cv.wait_for(lambda: self.zustand or self.fehler,
                                    warten):
                raise CncjsFehler('CNCjs schickt keinen Maschinenzustand')
        return self

    def schliessen(self):
        with self.cv:
            self.geschlossen = True
            self.cv.notify_all()
        try:
            self._rahmen_senden(8, b'')
        except OSError:
            pass
        try:
            self.sock.close()
        except (OSError, AttributeError):
            pass

    # Senden

    def emit(self, name, *args, ack=False, warten=5.0):
        nr = ''
        if ack:
            with self.cv:
                self._ack_nr += 1
                nr = self._ack_nr
                self._acks[nr] = None
        self._rahmen_senden(1, ('42%s%s' % (nr, json.dumps(
            [name] + list(args), separators=(',', ':')))).encode())
        if not ack:
            return None
        with self.cv:
            if not self.cv.wait_for(lambda: self._acks.get(nr) is not None
                                    or self.fehler, warten):
                raise CncjsFehler('CNCjs bestätigt "%s" nicht' % name)
            if self.fehler:
                raise CncjsFehler(self.fehler)
            return self._acks.pop(nr)

    def gcode(self, *zeilen):
        """G-Code ueber die Warteschlange von CNCjs (wartet auf ok je Zeile)."""
        self._pruefen()
        self.emit('command', self.port_name, 'gcode', '\n'.join(zeilen))

    def befehl(self, name, *args):
        """CNCjs-Befehl wie 'feedhold' oder 'reset'."""
        self._pruefen()
        self.emit('command', self.port_name, name, *args)

    def _pruefen(self):
        if self.fehler or self.geschlossen:
            raise CncjsFehler(self.fehler or 'Verbindung zu CNCjs zu')

    # Warten

    def warten(self, bedingung, warten_s):
        """Wartet, bis bedingung(self) wahr ist. False bei Zeitablauf."""
        with self.cv:
            ok = self.cv.wait_for(
                lambda: self.fehler or self.geschlossen or bedingung(self),
                warten_s)
            if self.fehler or self.geschlossen:
                raise CncjsFehler(self.fehler or 'Verbindung zu CNCjs zu')
            return bool(ok)

    def meldungen_seit(self, t):
        with self.cv:
            return [z for zeit, z in self.zeilen if zeit >= t]

    # Lesen

    def _lesen(self, n):
        while len(self._puffer) < n:
            stueck = self.sock.recv(65536)
            if not stueck:
                raise EOFError
            self._puffer += stueck
        daten, self._puffer = self._puffer[:n], self._puffer[n:]
        return daten

    def _rahmen_lesen(self):
        teile = []
        while True:
            b0, b1 = self._lesen(2)
            op, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack('>H', self._lesen(2))[0]
            elif n == 127:
                n = struct.unpack('>Q', self._lesen(8))[0]
            maske = self._lesen(4) if b1 & 0x80 else None
            daten = self._lesen(n)
            if maske:
                daten = bytes(b ^ maske[i % 4] for i, b in enumerate(daten))
            if op == 9:                      # Ping des WebSockets
                self._rahmen_senden(10, daten)
                continue
            if op == 10:
                continue
            if op == 8:
                raise EOFError
            teile.append(daten)
            if b0 & 0x80:
                return b''.join(teile)

    def _rahmen_senden(self, op, daten):
        maske = os.urandom(4)
        n = len(daten)
        if n < 126:
            kopf = struct.pack('>BB', 0x80 | op, 0x80 | n)
        elif n < 65536:
            kopf = struct.pack('>BBH', 0x80 | op, 0x80 | 126, n)
        else:
            kopf = struct.pack('>BBQ', 0x80 | op, 0x80 | 127, n)
        daten = bytes(b ^ maske[i % 4] for i, b in enumerate(daten))
        with self._senden_lock:
            self.sock.sendall(kopf + maske + daten)

    def _lesen_schleife(self):
        try:
            while True:
                self._paket(self._rahmen_lesen().decode('utf-8', 'replace'))
        except (EOFError, OSError, ValueError) as e:
            with self.cv:
                if not self.geschlossen and not self.fehler:
                    self.fehler = 'Verbindung zu CNCjs verloren (%s)' % (
                        type(e).__name__)
                self.cv.notify_all()

    def _ping_schleife(self):
        while not self.geschlossen and not self.fehler:
            time.sleep(self.ping_s)
            try:
                self._rahmen_senden(1, b'2')
            except OSError:
                return

    def _paket(self, text):
        """Engine.io 3: 0 open, 2 ping, 3 pong, 4 Nachricht (socket.io)."""
        art, rest = text[:1], text[1:]
        if art == '0':
            try:
                self.ping_s = json.loads(rest).get('pingInterval', 25000) / 1000
            except ValueError:
                pass
        elif art == '4':
            self._sio(rest)
        elif art == '1':
            raise EOFError

    def _sio(self, text):
        """socket.io 2: 0 connect, 2 event, 3 ack, 4 error."""
        art, rest = text[:1], text[1:]
        with self.cv:
            if art == '0':
                self.verbunden = True
            elif art == '4':
                try:
                    meldung = json.loads(rest)
                except ValueError:
                    meldung = rest
                if isinstance(meldung, dict):
                    meldung = meldung.get('message') or meldung
                self.fehler = 'CNCjs lehnt den Socket ab: %s' % meldung
            elif art in '23':
                i = 0
                while i < len(rest) and rest[i].isdigit():
                    i += 1
                nr, daten = rest[:i], json.loads(rest[i:] or '[]')
                if art == '3':
                    self._acks[int(nr)] = daten if daten else [None]
                else:
                    self._ereignis(daten[0], daten[1:])
            self.cv.notify_all()

    def _ereignis(self, name, args):
        if name == 'controller:state' and len(args) >= 2:
            self.zustand = args[1]
            self.zustand_nr += 1
        elif name == 'controller:settings' and len(args) >= 2:
            self.settings = args[1]
        elif name == 'feeder:status' and args:
            self.feeder = args[0]
        elif name == 'workflow:state' and args:
            self.workflow = args[0]
        elif name == 'serialport:read' and args:
            self.zeilen = (self.zeilen + [(time.monotonic(),
                                           str(args[0]).strip())])[-200:]
        elif name == 'serialport:close':
            self.fehler = 'CNCjs hat die Verbindung zur Maschine getrennt'


def verbinden(cncrc=CNCRC, host=HOST, port=PORT):
    """Prueft per REST, dass CNCjs mit der Maschine verbunden ist, und haengt
    sich an diesen Port. Gibt die offene Verbindung zurueck."""
    token = token_erzeugen(cncrc)
    eintrag = offener_port(controller_lesen(token, host, port))
    v = Verbindung(token, eintrag['port'], host, port).oeffnen()
    if not v.settings:
        v.settings = eintrag.get('controller', {}).get('settings', {})
    return v
