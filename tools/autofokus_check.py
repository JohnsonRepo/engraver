#!/usr/bin/env python3
"""Pruefung des Autofokus (pi/autofokus.py, pi/cncjs_client.py, pi/kamera.py)
— laeuft ohne Pi, Kamera und Maschine.

1. Bildauswertung an kuenstlichen Bildern: Punkt klein und unscharf, gross
   und uebersteuert, kein Punkt, zwei Punkte, Laser wieder aus.
2. Lerntabelle: Interpolation, Grenzen, Widersprueche, Speichern.
3. Ablauf gegen eine simulierte Maschine und Kamera: Messpunkt setzen,
   lernen, messen; Reihenfolge der Fahrten (erst Z hoch), Laser nur im
   G4-Block, Vorpruefungen ohne Fahrt, kein Punkt, Laser bleibt an, Abbruch.
4. Socket zu CNCjs gegen einen nachgebauten socket.io-2-Server: Handshake,
   Anhaengen an den Port, G-Code, Zustand, lange und geteilte Rahmen.
5. Webserver: Seite, Zustand, POST nur mit JSON und eigenem Kopf.

    python3 tools/autofokus_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import base64
import contextlib
import hashlib
import json
import os
import random
import socket
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib

HIER = os.path.dirname(os.path.abspath(__file__))
PI = os.path.join(HIER, '..', 'pi')
sys.path.insert(0, HIER)
sys.path.insert(0, PI)
TMP = tempfile.mkdtemp(prefix='autofokus_check_')
os.environ['AUTOFOKUS_DATEI'] = os.path.join(TMP, 'server.json')

from toolhead_check import Pruefung        # noqa: E402
import autofokus as af                     # noqa: E402
import cncjs_client as cc                  # noqa: E402

B, H = af.B, af.H


# -- kuenstliche Bilder ------------------------------------------------------------

def grund(seed=1):
    """Dunkles Bild mit etwas Struktur (Holz, Profil), gleich fuer an und aus."""
    r = random.Random(seed)
    zeile = bytes(min(255, 8 + (x // 37) % 5 + r.randrange(3)) for x in range(B))
    bild = bytearray(zeile * H)
    for y in range(700, 760):                 # helles Profil unten
        bild[y * B + 1000:y * B + 1200] = bytes([60]) * 200
    return bytes(bild)


GRUND = grund()


def rauschen(bild, seed):
    """Etwas Sensorrauschen in jede 7. Zeile, damit an != aus."""
    r = random.Random(seed)
    b = bytearray(bild)
    for y in range(0, H, 7):
        for x in range(r.randrange(7), B, 13):
            b[y * B + x] = max(0, min(255, b[y * B + x] + r.randrange(-3, 4)))
    return bytes(b)


def mit_punkt(bild, u, v, sigma=4.0, spitze=200, voll=0):
    """Gausspunkt bei (u, v); voll > 0: uebersteuerte Scheibe mit Radius voll."""
    b = bytearray(bild)
    r = int(max(4 * sigma, voll + 4 * sigma)) + 1
    for y in range(int(v) - r, int(v) + r + 1):
        for x in range(int(u) - r, int(u) + r + 1):
            if 0 <= x < B and 0 <= y < H:
                d = ((x - u) ** 2 + (y - v) ** 2) ** 0.5
                w = 255 if voll and d <= voll else spitze * pow(
                    2.718281828, -((d - voll) ** 2) / (2 * sigma ** 2))
                b[y * B + x] = min(255, int(b[y * B + x] + w))
    return bytes(b)


def pruefe_bild(p):
    p.titel('1. Bildauswertung')
    aus = rauschen(GRUND, 1)
    an = rauschen(mit_punkt(GRUND, 612.3, 401.7), 2)
    t = time.perf_counter()
    q = af.punkt_finden(an, aus)
    dauer = time.perf_counter() - t
    p.ok('kleiner Punkt: Abweichung', abs(q['u'] - 612.3) + abs(q['v'] - 401.7),
         0.3, '<=', 'px')
    p.info('Dauer der Suche hier (am Pi etwa 5-mal so lang)', dauer * 1000, 'ms')
    an = rauschen(mit_punkt(GRUND, 201.6, 822.2, sigma=3, voll=24), 3)
    q = af.punkt_finden(an, aus)
    p.ok('grosser, uebersteuerter Punkt: Abweichung',
         abs(q['u'] - 201.6) + abs(q['v'] - 822.2), 0.5, '<=', 'px')
    p.ok('  Pixel ueber der halben Spitze', q['pixel'], 1000, '>=', 'px')
    an = rauschen(mit_punkt(GRUND, 1100, 730, spitze=150), 4)   # auf dem Profil
    q = af.punkt_finden(an, aus)
    p.ok('Punkt auf hellem Profil: Abweichung',
         abs(q['u'] - 1100) + abs(q['v'] - 730), 0.3, '<=', 'px')

    for text, bild, erwartet in (
            ('kein Punkt', rauschen(GRUND, 5), 'Kein Laserpunkt'),
            ('schwacher Punkt (Anstieg 30)',
             rauschen(mit_punkt(GRUND, 500, 500, spitze=30), 6), 'Kein Laserpunkt'),
            ('zwei Punkte', rauschen(mit_punkt(mit_punkt(GRUND, 300, 300), 900,
                                               600, spitze=180), 7),
             'Zwei helle Stellen')):
        try:
            af.punkt_finden(bild, aus)
            p.ja(text + ': Fehler gemeldet', False)
        except af.AfFehler as f:
            p.ja(text + ': Fehler gemeldet', erwartet in str(f), ' (%s)' % f)

    an = mit_punkt(GRUND, 640, 480)
    p.ok('Rest nach "Laser aus" ohne Punkt',
         af.rest_anstieg(rauschen(GRUND, 8), aus, 640, 480), 10, '<=', '')
    p.ok('Rest mit Punkt', af.rest_anstieg(an, aus, 640, 480), 150, '>=', '')

    png = af.messbild_png(an, {'u': 640, 'v': 480})
    roh = zlib.decompress(png[png.index(b'IDAT') + 4:])
    p.ja('Messbild ist ein PNG 640 x 480',
         png[:8] == b'\x89PNG\r\n\x1a\n'
         and struct.unpack('>II', png[16:24]) == (640, 480)
         and len(roh) == 480 * 641)
    p.ja('  Kreuz auf dem Punkt, Mitte frei',
         roh[240 * 641 + 1 + 320 + 20] in (0, 255)
         and roh[240 * 641 + 1 + 320] != 0)


# -- Lerntabelle -------------------------------------------------------------------

def linie(h):
    """Simulierte Kamera: Punkt fuer Oberflaechenhoehe h (mm ueber Platte).
    Perspektive wie bei einer Lochkamera: zur Ferne hin gestaucht."""
    k = 1.0 / (1.0 + 0.012 * h)
    return 600.0 + 4.0 * h * k, 300.0 + 18.0 * h * k


def z_fokus(h):
    return -60.0 + h


def pruefe_tabelle(p):
    p.titel('2. Lerntabelle')
    datei = os.path.join(TMP, 'tab.json')
    t = af.Tabelle(datei)
    t.messpunkt_setzen(-155.0, -34.2)
    for h, name in ((0, 'leere Platte'), (4, '4 mm'), (10, '10 mm'), (18, '18 mm')):
        u, v = linie(h)
        t.hinzufuegen({'u': u, 'v': v}, z_fokus(h), name)
    t2 = af.Tabelle(datei)
    p.ja('gespeichert und wieder gelesen', t2.punkte == t.punkte
         and t2.messpunkt == [-155.0, -34.2])
    fehler = max(abs(t.z_fuer(*linie(h))[0] - z_fokus(h))
                 for h in (0, 2, 4, 7, 10, 14, 18))
    p.ok('Fokus-Z dazwischen: groesster Fehler', fehler, 0.05, '<=')
    z, info = t.z_fuer(*linie(7))
    p.ok('  Hoehe ueber der leeren Platte bei 7 mm', info['ueber'], 7 - 0.05, '>=')
    p.ja('  tiefster Eintrag heisst "leere Platte"', info['unten'] == 'leere Platte')
    p.ja('  Kurve projektiv (ab drei Punkten)', info['kurve'] == 'projektiv')
    z, _ = t.z_fuer(*linie(20))
    p.ok('wenig darueber (20 mm): extrapoliert, Fehler', abs(z - z_fokus(20)),
         0.05, '<=')
    def fehlt(text, *uv, tab=t):
        try:
            tab.z_fuer(*uv)
            p.ja(text, False)
        except af.AfFehler as f:
            p.ja(text, True, ' (%s)' % str(f)[:60])

    u, v = linie(8)
    fehlt('Punkt 40 px neben der Linie: abgelehnt', u + 40, v - 9)
    fehlt('viel dicker (40 mm): abgelehnt', *linie(40))
    fehlt('unter der Platte (-8 mm): abgelehnt', *linie(-8))
    t2 = af.Tabelle(os.path.join(TMP, 'tab2.json'))
    t2.messpunkt_setzen(0, 0)
    for h in (0, 18):
        t2.hinzufuegen(dict(zip('uv', linie(h))), z_fokus(h), '')
    fehlt('nur zwei Dicken: abgelehnt (Perspektive braucht drei)',
          *linie(9), tab=t2)
    v0, v9, v18 = linie(0)[1], linie(9)[1], linie(18)[1]
    p.info('  linear zwischen 0 und 18 waere bei 9 mm daneben um',
           abs(z_fokus(0) + 18 * (v9 - v0) / (v18 - v0) - z_fokus(9)))


    t3 = af.Tabelle(os.path.join(TMP, 'tab3.json'))
    t3.messpunkt_setzen(0, 0)
    t3.hinzufuegen({'u': 600, 'v': 300}, -60, 'a')
    fehlt('ein Eintrag: abgelehnt', 600, 300, tab=t3)
    t3.hinzufuegen({'u': 660, 'v': 560}, -50, 'e')
    t3.hinzufuegen({'u': 600.5, 'v': 300.5}, -59, 'b')
    fehlt('zwei Eintraege am selben Ort: abgelehnt', 600, 300, tab=t3)
    t3.loeschen(2)
    t3.hinzufuegen({'u': 640, 'v': 480}, -61, 'c')    # dicker, aber Z tiefer
    t3.hinzufuegen({'u': 620, 'v': 390}, -58, 'd')
    fehlt('Z nicht steigend mit der Dicke: abgelehnt', 620, 390, tab=t3)
    try:
        t3.loeschen(7)
        p.ja('Loeschen eines fehlenden Eintrags: Fehler', False)
    except af.AfFehler:
        p.ja('Loeschen eines fehlenden Eintrags: Fehler', True)
    t3.messpunkt_setzen(1, 2)
    p.ja('neuer Messpunkt leert die Tabelle', t3.punkte == [])

    kaputt = os.path.join(TMP, 'kaputt.json')
    with open(kaputt, 'w') as f:
        f.write('{kein json')
    t4 = af.Tabelle(kaputt)
    p.ja('kaputte Datei: beiseite gelegt, leer begonnen',
         t4.punkte == [] and os.path.exists(kaputt + '.kaputt'))


# -- simulierte Maschine und Kamera ---------------------------------------------------

class Maschine:
    """CNCjs + GRBL im Kleinen: Fahrten, Laser, G4, Feeder, Zustand."""

    def __init__(self, x=-366.0, y=-325.0, z=-1.0):
        self.cv = threading.Condition()
        self.pos = {'x': x, 'y': y, 'z': z}
        self.zustand_text = 'Idle'
        self.spindel = 0
        self.modal = 'G0'
        self.hoehe = 0.0              # Oberflaeche unter dem Messpunkt
        self.messpunkt = None
        self.workflow = 'idle'
        self.queue = []
        self.pending = False
        self.log = []
        self.befehle = []
        self.wco_z = 0.0
        self.m5_wirkt = True
        self.halt = False
        self.fahrzeit = 0.02
        threading.Thread(target=self._arbeiten, daemon=True).start()

    # was die Kamera sieht
    def laser_an(self):
        return self.spindel > 0 and self.modal != 'G0'

    def _arbeiten(self):
        while True:
            with self.cv:
                self.cv.wait_for(lambda: self.queue and not self.halt)
                zeile = self.queue.pop(0)
                self.pending = True
                self.cv.notify_all()
            self._ausfuehren(zeile)
            with self.cv:
                self.pending = False
                self.cv.notify_all()

    def _ausfuehren(self, zeile):
        w = zeile.split()
        if w[:2] == ['G53', 'G0'] or w[:1] == ['G0']:
            ziel = {a[0].lower(): float(a[1:]) for a in w if a[0] in 'XYZ'}
            with self.cv:
                self.zustand_text = 'Run'
                self.modal = 'G0'
                self.cv.notify_all()
            time.sleep(self.fahrzeit)
            with self.cv:
                if not self.halt:
                    self.pos.update(ziel)
                    self.zustand_text = 'Idle'
                self.cv.notify_all()
        elif w[0] == 'G1':
            self.modal = 'G1'
        elif w[0] == 'M3':
            with self.cv:
                self.spindel = int(w[1][1:])
                self.cv.notify_all()
        elif w[0] == 'G4':
            time.sleep(float(w[1][1:]))
        elif w[0] == 'M5':
            with self.cv:
                if self.m5_wirkt:
                    self.spindel = 0
                self.cv.notify_all()
        elif w[:3] == ['G10', 'L20', 'P1']:
            self.wco_z = self.pos['z']

    def senden(self, zeilen):
        with self.cv:
            self.log += zeilen
            self.queue += zeilen
            self.cv.notify_all()

    def zustand(self):
        return {'status': {'activeState': self.zustand_text,
                           'mpos': {a: '%.3f' % v for a, v in self.pos.items()},
                           'spindle': str(self.spindel)}}


class Verbindung:
    """Stellt sich wie cncjs_client.Verbindung."""

    def __init__(self, m):
        self.m = m
        self.cv = m.cv
        self.settings = {'settings': {'$130': '367', '$131': '326',
                                      '$132': '82'}}

    @property
    def zustand(self):
        return self.m.zustand()

    @property
    def feeder(self):
        return {'queue': len(self.m.queue), 'pending': self.m.pending}

    @property
    def workflow(self):
        return self.m.workflow

    def gcode(self, *zeilen):
        self.m.senden(list(zeilen))

    def befehl(self, name, *args):
        self.m.befehle.append(name)
        if name in ('feedhold', 'reset'):
            with self.m.cv:
                self.m.halt = name == 'feedhold'
                if name == 'reset':
                    self.m.queue.clear()
                    self.m.spindel = 0
                    self.m.zustand_text = 'Alarm'
                    self.m.halt = False
                self.m.cv.notify_all()

    def warten(self, bedingung, warten_s):
        with self.cv:
            return bool(self.cv.wait_for(lambda: bedingung(self), warten_s))

    def meldungen_seit(self, t):
        return []

    def schliessen(self):
        pass


class CncjsModul:
    def __init__(self, m):
        self.m = m
        self.verbunden = 0

    def verbinden(self):
        self.verbunden += 1
        return Verbindung(self.m)

    verfahrweg = staticmethod(cc.verfahrweg)
    mpos = staticmethod(cc.mpos)
    aktiv = staticmethod(cc.aktiv)


class Kamera:
    """Messkamera: Punkt nur bei Laser an und Kopf ueber dem Messpunkt."""

    def __init__(self, m):
        self.m = m
        self.messungen = 0

    @contextlib.contextmanager
    def messung(self, belichtung_us, verstaerkung):
        self.messungen += 1
        yield self

    def naechstes(self, nach=None, warten=4.0):
        time.sleep(0.02)
        m = self.m
        bild = rauschen(GRUND, random.randrange(1000))
        ueber = (m.messpunkt and abs(m.pos['x'] - m.messpunkt[0]) < 0.01
                 and abs(m.pos['y'] - m.messpunkt[1]) < 0.01)
        if m.laser_an() and ueber and m.hoehe is not None:
            bild = mit_punkt(bild, *linie(m.hoehe), sigma=5, spitze=220)
        return time.monotonic(), bild


def lauf(a, art, name='', warten_s=20):
    a.starten(art, name)
    ende = time.monotonic() + warten_s
    while a.zustand()['laeuft'] and time.monotonic() < ende:
        time.sleep(0.01)
    return a.zustand()


def pruefe_ablauf(p):
    p.titel('3. Ablauf mit simulierter Maschine')
    m = Maschine()
    modul = CncjsModul(m)
    a = af.Autofokus(Kamera(m), modul, os.path.join(TMP, 'ablauf.json'))
    a.e.update(laser_dauer_s=0.2)

    z = lauf(a, 'messen')
    p.ja('ohne Messpunkt: Fehler, keine Verbindung',
         'Messpunkt' in z['fehler'] and modul.verbunden == 0 and not m.log)

    m.pos.update(x=-155.0, y=-34.2)
    z = lauf(a, 'messpunkt')
    m.messpunkt = a.tabelle.messpunkt
    p.ja('Messpunkt = aktuelle Position', z['messpunkt'] == [-155.0, -34.2]
         and not m.log, ' (%s)' % (z['fehler'] or z['meldung'])[:60])

    for h, name in ((0, 'leere Platte'), (6, '6 mm'), (15, '15 mm')):
        m.hoehe = h
        m.pos.update(x=-200.0, y=-100.0, z=z_fokus(h))   # von Hand scharf
        m.log.clear()
        z = lauf(a, 'lernen', name)
        if z['fehler']:
            p.ja('lernen %s' % name, False, ' (%s)' % z['fehler'])
            continue
    p.ok('drei Dicken gelernt', len(a.tabelle.punkte), 3, '>=', '')
    p.ja('  Z der Eintraege = Z beim Scharfstellen',
         [q['z'] for q in a.tabelle.punkte] == [z_fokus(0), z_fokus(6), z_fokus(15)])
    p.ok('  nach dem Lernen zurueck auf dem Fokus-Z',
         abs(m.pos['z'] - z_fokus(15)), 0.01, '<=')
    erste_z = next(i for i, l in enumerate(m.log) if 'Z' in l and 'G53' in l)
    erste_xy = next(i for i, l in enumerate(m.log) if 'X' in l and 'G53' in l)
    p.ja('  erst Z hoch (G53 G0 Z-2), dann X/Y',
         erste_z < erste_xy and m.log[erste_z].endswith('Z-2.000'))
    i = m.log.index('M3 S10')
    p.ja('  Laser nur im Block G1 F600 / M3 S10 / G4 / M5',
         m.log[i - 1] == 'G1 F600' and m.log[i + 1].startswith('G4 P')
         and m.log[i + 2] == 'M5')

    m.hoehe = 9.5
    m.log.clear()
    z = lauf(a, 'messen')
    p.ja('messen bei 9,5 mm: ohne Fehler', not z['fehler'], ' (%s)' % z['fehler'])
    p.ok('  Fokus-Z getroffen: Abweichung', abs(m.pos['z'] - z_fokus(9.5)),
         0.05, '<=')
    p.ja('  G54 Z0 dort gesetzt', 'G10 L20 P1 Z0' in m.log
         and abs(m.wco_z - m.pos['z']) < 1e-6)
    p.ok('  Hoehe ueber der leeren Platte', (z['ergebnis'] or {}).get('ueber', 0),
         9.5 - 0.2, '>=')
    p.ja('  Messbild vorhanden', a.png() is not None and z['bild'] >= 4)

    # Vorpruefungen: keine Fahrt
    for text, vorher, nachher in (
            ('Alarm', lambda: setattr(m, 'zustand_text', 'Alarm'),
             lambda: setattr(m, 'zustand_text', 'Idle')),
            ('Auftrag laeuft', lambda: setattr(m, 'workflow', 'running'),
             lambda: setattr(m, 'workflow', 'idle'))):
        vorher()
        m.log.clear()
        z = lauf(a, 'messen')
        nachher()
        p.ja('%s: Fehler, keine Fahrt' % text, z['fehler'] != '' and not m.log,
             ' (%s)' % z['fehler'][:60])
    a.tabelle.messpunkt = [-155.0, 40.0]
    m.log.clear()
    z = lauf(a, 'messen')
    a.tabelle.messpunkt = [-155.0, -34.2]
    p.ja('Messpunkt ausserhalb des Verfahrwegs: Fehler, keine Fahrt',
         'Verfahrwegs' in z['fehler'] and not m.log)

    m.hoehe = None                       # kein Werkstueck unter dem Messpunkt
    m.log.clear()
    z = lauf(a, 'messen')
    p.ja('kein Punkt: Fehler', 'Kein Laserpunkt' in z['fehler'],
         ' (%s)' % z['fehler'][:50])
    p.ja('  Z bleibt oben, kein G10', abs(m.pos['z'] + 2) < 1e-6
         and 'G10 L20 P1 Z0' not in m.log)
    p.ja('  Laser wieder aus', m.spindel == 0)

    m.hoehe = 9.5
    m.m5_wirkt = False                   # Laser bleibt an
    m.log.clear()
    z = lauf(a, 'messen')
    m.m5_wirkt = True
    p.ja('Laser geht nicht aus: Fehler und M5 noch einmal',
         ('nicht aus' in z['fehler'] or 'noch zu sehen' in z['fehler'])
         and m.log.count('M5') >= 2, ' (%s)' % z['fehler'][:50])
    m.spindel = 0

    m.fahrzeit = 1.0
    m.pos.update(z=-30.0)
    a.starten('messen')
    time.sleep(0.4)
    a.abbrechen()
    ende = time.monotonic() + 5
    while a.zustand()['laeuft'] and time.monotonic() < ende:
        time.sleep(0.01)
    z = a.zustand()
    p.ja('Abbruch waehrend der Fahrt: Feedhold und Reset',
         'Abgebrochen' in z['fehler'] and m.befehle[-2:] == ['feedhold', 'reset'],
         ' (%s)' % z['fehler'][:50])


# -- nachgebauter CNCjs-Socket ---------------------------------------------------------

def _ws_senden(s, text, teilen=False):
    daten = text.encode()
    if teilen and len(daten) > 4:        # in zwei Rahmen: Text + Fortsetzung
        h = len(daten) // 2
        s.sendall(bytes([0x01, h]) + daten[:h])
        s.sendall(bytes([0x89, 2]) + b'hi')           # Ping dazwischen
        rest = daten[h:]
        s.sendall(bytes([0x80, len(rest)]) + rest)
        return
    n = len(daten)
    kopf = bytes([0x81, n]) if n < 126 else bytes([0x81, 126]) + struct.pack('>H', n)
    s.sendall(kopf + daten)


def _ws_lesen(s, puffer):
    def lesen(n):
        while len(puffer[0]) < n:
            d = s.recv(65536)
            if not d:
                raise EOFError
            puffer[0] += d
        x, puffer[0] = puffer[0][:n], puffer[0][n:]
        return x
    b0, b1 = lesen(2)
    n = b1 & 0x7F
    if n == 126:
        n = struct.unpack('>H', lesen(2))[0]
    maske = lesen(4)
    d = bytes(c ^ maske[i % 4] for i, c in enumerate(lesen(n)))
    return b0 & 0x0F, d.decode()


def socket_server(empfangen, token_soll):
    srv = socket.socket()
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)

    def bedienen():
        s, _ = srv.accept()
        kopf = b''
        while b'\r\n\r\n' not in kopf:
            kopf += s.recv(4096)
        zeile = kopf.split(b'\r\n')[0].decode()
        empfangen.append(zeile)
        schl = [z for z in kopf.decode().split('\r\n')
                if z.lower().startswith('sec-websocket-key')][0].split(':')[1].strip()
        acc = base64.b64encode(hashlib.sha1(
            (schl + '258EAFA5-E914-47DA-95CA-C5AB0DC11B11').encode()).digest())
        s.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n'
                  b'Connection: Upgrade\r\nSec-WebSocket-Accept: ' + acc + b'\r\n\r\n')
        _ws_senden(s, '0{"sid":"x","pingInterval":25000,"pingTimeout":5000}')
        if 'token=' + token_soll not in zeile:
            _ws_senden(s, '44"Unauthorized"')
            return
        _ws_senden(s, '40')
        puffer = [b'']
        while True:
            try:
                op, text = _ws_lesen(s, puffer)
            except (EOFError, OSError):
                return
            if op == 8:
                return
            if op != 1:
                continue
            empfangen.append(text)
            if text.startswith('421['):
                _ws_senden(s, '431[null]')
                zustand = {'status': {'activeState': 'Idle', 'mpos': {
                    'x': '-366.000', 'y': '-325.000', 'z': '-1.000'},
                    'spindle': '0'}, 'pad': 'x' * 300}    # > 125 Bytes
                _ws_senden(s, '42' + json.dumps(['controller:state', 'Grbl',
                                                 zustand]))
                _ws_senden(s, '42' + json.dumps(['feeder:status', {
                    'queue': 0, 'pending': False}]), teilen=True)
                _ws_senden(s, '42' + json.dumps(['serialport:read', 'ok']))

    threading.Thread(target=bedienen, daemon=True).start()
    return srv.getsockname()[1]


def pruefe_socket(p):
    p.titel('4. Socket zu CNCjs (nachgebaut)')
    cncrc = os.path.join(TMP, 'cncrc')
    with open(cncrc, 'w') as f:
        json.dump({'secret': 'geheim', 'users': [
            {'id': 'u1', 'name': 'jonas', 'enabled': False},
            {'id': 'u2', 'name': 'iPad'}]}, f)
    token = cc.token_erzeugen(cncrc, jetzt=1000)
    kopf, rumpf, sig = token.split('.')
    roh = json.loads(base64.urlsafe_b64decode(rumpf + '=='))
    import hmac
    soll = base64.urlsafe_b64encode(hmac.new(b'geheim', (kopf + '.' + rumpf).encode(),
                                             hashlib.sha256).digest()).rstrip(b'=')
    p.ja('JWT HS256 mit dem secret signiert', sig.encode() == soll)
    p.ja('  erster aktiver Benutzer im Token', roh['id'] == 'u2'
         and roh['name'] == 'iPad' and roh['exp'] == 1000 + 24 * 3600)

    empfangen = []
    port = socket_server(empfangen, token)
    v = cc.Verbindung(token, '/dev/ttyACM0', '127.0.0.1', port).oeffnen()
    p.ja('Handshake mit EIO=3 und Token', 'EIO=3&transport=websocket&token='
         in empfangen[0])
    p.ja('an den Port angehaengt (open mit Bestaetigung)',
         empfangen[1].startswith('421["open","/dev/ttyACM0",'))
    p.ja('Zustand empfangen (Rahmen > 125 Bytes)',
         cc.aktiv(v.zustand) == 'Idle' and cc.mpos(v.zustand)['z'] == -1.0)
    v.warten(lambda v: v.feeder, 2)
    p.ja('geteilter Rahmen mit Ping dazwischen', v.feeder.get('queue') == 0)
    v.warten(lambda v: v.zeilen, 2)
    p.ja('Meldungen der Maschine mitgelesen', v.meldungen_seit(0) == ['ok'])
    v.gcode('G90', 'G53 G0 Z-2.000')
    ende = time.monotonic() + 2
    while len(empfangen) < 3 and time.monotonic() < ende:
        time.sleep(0.01)
    p.ja('G-Code als command/gcode gesendet', empfangen[2:3] ==
         ['42["command","/dev/ttyACM0","gcode","G90\\nG53 G0 Z-2.000"]'])
    v.schliessen()

    empfangen2 = []
    port = socket_server(empfangen2, 'anderes')
    try:
        cc.Verbindung(token, '/dev/ttyACM0', '127.0.0.1', port).oeffnen()
        p.ja('falsches Token: Fehler', False)
    except cc.CncjsFehler as f:
        p.ja('falsches Token: Fehler', 'lehnt' in str(f), ' (%s)' % f)

    try:
        cc.offener_port([{'port': '/dev/ttyACM0', 'ready': False}])
        p.ja('CNCjs ohne Verbindung zur Maschine: Fehler', False)
    except cc.CncjsFehler:
        p.ja('CNCjs ohne Verbindung zur Maschine: Fehler', True)


# -- Webserver --------------------------------------------------------------------------

def pruefe_server(p):
    p.titel('5. Webserver')
    import kamera
    srv = kamera.http.server.ThreadingHTTPServer(('127.0.0.1', 0), kamera.Anfrage)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    basis = 'http://127.0.0.1:%d' % srv.server_address[1]

    def holen(pfad, daten=None, kopf=None):
        anfrage = urllib.request.Request(basis + pfad, data=daten,
                                         headers=kopf or {})
        try:
            with urllib.request.urlopen(anfrage, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    code, inhalt = holen('/autofokus')
    p.ja('Seite /autofokus', code == 200 and b'Fokus lernen' in inhalt)
    code, inhalt = holen('/api/af')
    z = json.loads(inhalt)
    p.ja('Zustand /api/af als JSON', code == 200 and 'punkte' in z
         and 'kamera' in z)
    code, _ = holen('/api/af/messpunkt', b'{}', {'Content-Type': 'text/plain'})
    p.ja('POST ohne JSON und Kopf: abgelehnt (403)', code == 403)
    code, _ = holen('/api/af/messpunkt', b'{}',
                    {'Content-Type': 'application/json'})
    p.ja('POST ohne X-Autofokus: abgelehnt (403)', code == 403)
    code, inhalt = holen('/api/af/loeschen', b'{"index": 3}',
                         {'Content-Type': 'application/json', 'X-Autofokus': '1'})
    p.ja('Loeschen eines fehlenden Eintrags: 409 mit Meldung', code == 409
         and 'gibt es nicht' in json.loads(inhalt)['fehler'])
    code, _ = holen('/api/af/bild.png')
    p.ja('noch kein Messbild: 404', code == 404)
    srv.shutdown()


def main():
    p = Pruefung()
    pruefe_bild(p)
    pruefe_tabelle(p)
    pruefe_ablauf(p)
    pruefe_socket(p)
    pruefe_server(p)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
