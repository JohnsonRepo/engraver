#!/usr/bin/env python3
"""kamera.py — Live-Bild der Autofokus-Kamera im Browser.

Der Pi hat keinen Bildschirm, rpicam-hello zeigt dort nichts. Dieser kleine
Server zeigt das Bild der Kamera stattdessen im Browser
(docs/kamerahalter.md, docs/pi.md):

    http://laser.local:8080            Seite mit Bild, Schaerfe und Licht
    http://laser.local:8080/stream     nur das Bild (MJPEG), z. B. fuer das
                                       Webcam-Fenster in CNCjs
    http://laser.local:8080/bild.jpg   ein Einzelbild
    http://laser.local:8080/autofokus  Autofokus, fuer das Custom Widget
                                       in CNCjs (autofokus.py)

Die Kamera laeuft nur, solange jemand zusieht. 5 s nach dem letzten
Zuschauer gibt der Server sie wieder frei, fuer rpicam-still. Fuer eine
Messung des Autofokus nimmt er sie dem Live-Bild kurz weg. Braucht nur
Python 3 und rpicam-vid (beides auf Pi OS Lite).

Von Hand starten:  python3 pi/kamera.py
Als Dienst:        pi/einrichten.sh installiert ihn als kamera-live
"""

import contextlib
import http.server
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time

import autofokus

HIER = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('KAMERA_PORT') or 8080)   # anderer Port zum Testen
BREITE, HOEHE = 1296, 972   # halbe Sensoraufloesung, ganzes Bildfeld
BILDRATE = 10
QUALITAET = 70              # JPEG; gut 100 kB je Bild bei wenig Licht
NACHLAUF = 5.0              # s ohne Zuschauer, dann Kamera aus
EINSCHWINGEN = 1.5          # s nach dem Start, bis die Belichtung steht


class Kamera:
    """Ein rpicam-vid fuer alle Zuschauer; laeuft nur, solange jemand
    zusieht."""

    def __init__(self):
        self.cv = threading.Condition()
        self.proc = None
        self.start_zeit = 0.0
        self.bild = None           # letztes JPEG
        self.nummer = 0            # zaehlt jedes neue Bild
        self.zuschauer = 0
        self.leer_seit = time.monotonic()
        self.fom = None            # FocusFoM des ISP: hoeher = schaerfer
        self.lux = None
        self.fehler = ''
        self.messend = False       # Autofokus hat die Kamera
        threading.Thread(target=self._waechter, daemon=True).start()

    # -- Zuschauer ----------------------------------------------------------

    def anmelden(self):
        with self.cv:
            self.zuschauer += 1
            if self.proc is None and not self.messend:
                self._starten()

    def abmelden(self):
        with self.cv:
            self.zuschauer -= 1
            if self.zuschauer == 0:
                self.leer_seit = time.monotonic()

    def naechstes(self, nummer, warten):
        """Wartet auf ein Bild neuer als `nummer`. (None, nummer), wenn keins
        kommt oder die Kamera nicht laeuft."""
        with self.cv:
            # bild ist None, bis nach einem Start das erste Bild da ist
            def neu():
                return self.nummer != nummer and self.bild is not None
            # waehrend einer Messung warten statt aufgeben
            self.cv.wait_for(
                lambda: neu() or (self.proc is None and not self.messend),
                warten)
            if neu():
                return self.bild, self.nummer
            return None, nummer

    def zustand(self):
        with self.cv:
            return {'laeuft': self.proc is not None,
                    'messung': self.messend,
                    'zuschauer': self.zuschauer,
                    'schaerfe': self.fom, 'lux': self.lux,
                    'fehler': self.fehler}

    # -- rpicam-vid ---------------------------------------------------------

    def _starten(self):
        lesen, schreiben = os.pipe()
        befehl = ['rpicam-vid', '-n', '-t', '0', '-v', '0',
                  '--codec', 'mjpeg', '--quality', str(QUALITAET),
                  '--width', str(BREITE), '--height', str(HOEHE),
                  '--framerate', str(BILDRATE), '--flush',
                  '--metadata', '/dev/fd/%d' % schreiben,
                  '--metadata-format', 'txt', '-o', '-']
        umgebung = dict(os.environ, LIBCAMERA_LOG_LEVELS='*:ERROR')
        try:
            proc = subprocess.Popen(
                befehl, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL, pass_fds=(schreiben,),
                env=umgebung)
        except OSError as e:
            os.close(lesen)
            os.close(schreiben)
            self.fehler = 'rpicam-vid startet nicht: %s' % e
            return
        os.close(schreiben)
        self.proc = proc
        self.start_zeit = time.monotonic()
        self.fehler = ''
        self.bild = None
        self.fom = self.lux = None
        proc.gestoppt = False
        proc.meldungen = []
        for ziel, arg in ((self._bilder_lesen, proc),
                          (self._meldungen_lesen, proc),
                          (self._metadaten_lesen, lesen)):
            threading.Thread(target=ziel, args=(arg,), daemon=True).start()

    def _bilder_lesen(self, proc):
        """Zerlegt den MJPEG-Strom an den JPEG-Markern SOI/EOI."""
        puffer = b''
        while True:
            stueck = proc.stdout.read1(65536)
            if not stueck:
                break
            puffer += stueck
            while True:
                a = puffer.find(b'\xff\xd8')
                if a < 0:
                    puffer = puffer[-1:]
                    break
                e = puffer.find(b'\xff\xd9', a + 2)
                if e < 0:
                    puffer = puffer[a:]
                    break
                with self.cv:
                    self.bild = puffer[a:e + 2]
                    self.nummer += 1
                    self.cv.notify_all()
                puffer = puffer[e + 2:]
        rc = proc.wait()
        with self.cv:
            if self.proc is proc:
                self.proc = None
            if not proc.gestoppt:
                letzte = [z for z in proc.meldungen if z.strip()][-3:]
                self.fehler = ('Kamera nicht verfügbar (rpicam-vid %d): %s'
                               % (rc, ' | '.join(letzte) or 'ohne Meldung'))
                print(self.fehler, file=sys.stderr)
            self.cv.notify_all()

    def _meldungen_lesen(self, proc):
        for zeile in proc.stderr:
            proc.meldungen = (proc.meldungen + [
                zeile.decode('utf-8', 'replace').strip()])[-20:]

    def _metadaten_lesen(self, fd):
        with open(fd, 'r', errors='replace') as f:
            for zeile in f:
                schluessel, _, wert = zeile.partition('=')
                try:
                    if schluessel == 'FocusFoM':
                        self.fom = int(float(wert))
                    elif schluessel == 'Lux':
                        self.lux = round(float(wert), 1)
                except ValueError:
                    pass

    def _waechter(self):
        while True:
            time.sleep(1.0)
            with self.cv:
                proc = self.proc
                aus = (proc is not None and self.zuschauer == 0
                       and time.monotonic() - self.leer_seit > NACHLAUF)
                if aus:
                    proc.gestoppt = True
                    self.proc = None
                    self.cv.notify_all()
            if aus:
                self._beenden(proc)

    @staticmethod
    def _beenden(proc):
        proc.terminate()
        try:
            proc.wait(3)
        except subprocess.TimeoutExpired:
            proc.kill()

    def aus(self):
        with self.cv:
            proc, self.proc = self.proc, None
        if proc is not None:
            proc.gestoppt = True
            self._beenden(proc)

    @contextlib.contextmanager
    def messung(self, belichtung_us, verstaerkung):
        """Kamera fuer eine Messung: Live-Bild aus, RohKamera an, danach
        wieder Live-Bild, falls jemand zusieht."""
        with self.cv:
            if self.messend:
                raise autofokus.AfFehler('Die Kamera misst schon')
            self.messend = True
            alt, self.proc = self.proc, None
            if alt is not None:
                alt.gestoppt = True
            self.cv.notify_all()
        roh = None
        try:
            if alt is not None:
                self._beenden(alt)
            roh = RohKamera(belichtung_us, verstaerkung)
            yield roh
        finally:
            if roh is not None:
                roh.stop()
            with self.cv:
                self.messend = False
                self.leer_seit = time.monotonic()
                if self.zuschauer > 0 and self.proc is None:
                    self._starten()
                self.cv.notify_all()


class RohKamera:
    """rpicam-vid mit fester Belichtung; liefert die Y-Ebene jedes Bildes
    (YUV420, 1280 x 960: Breite durch 64 teilbar, also ohne Rand)."""

    def __init__(self, belichtung_us, verstaerkung,
                 b=autofokus.B, h=autofokus.H):
        self.b, self.h = b, h
        self.groesse = b * h * 3 // 2
        self.cv = threading.Condition()
        self.bild, self.zeit, self.nummer, self.geholt = None, 0.0, 0, 0
        self.fehler = ''
        self.meldungen = []
        self.gestoppt = False
        befehl = ['rpicam-vid', '-n', '-t', '0', '-v', '0',
                  '--codec', 'yuv420', '--width', str(b), '--height', str(h),
                  '--framerate', '10', '--shutter', str(int(belichtung_us)),
                  '--gain', str(verstaerkung), '--awbgains', '1.5,1.5',
                  '--denoise', 'off', '--flush', '-o', '-']
        try:
            self.proc = subprocess.Popen(
                befehl, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=dict(os.environ, LIBCAMERA_LOG_LEVELS='*:ERROR'))
        except OSError as e:
            raise autofokus.AfFehler('rpicam-vid startet nicht: %s' % e)
        threading.Thread(target=self._lesen, daemon=True).start()
        threading.Thread(target=self._meldungen_lesen, daemon=True).start()

    def _lesen(self):
        while True:
            daten = self.proc.stdout.read(self.groesse)
            if len(daten) < self.groesse:
                break
            with self.cv:
                self.bild = daten[:self.b * self.h]
                self.zeit = time.monotonic()
                self.nummer += 1
                self.cv.notify_all()
        rc = self.proc.wait()
        with self.cv:
            if not self.gestoppt:
                letzte = [z for z in self.meldungen if z][-2:]
                self.fehler = ('Kamera für die Messung nicht verfügbar '
                               '(rpicam-vid %d): %s'
                               % (rc, ' | '.join(letzte) or 'ohne Meldung'))
            self.cv.notify_all()

    def _meldungen_lesen(self):
        for zeile in self.proc.stderr:
            self.meldungen = (self.meldungen + [
                zeile.decode('utf-8', 'replace').strip()])[-20:]

    def naechstes(self, nach=None, warten=4.0):
        """Naechstes noch nicht geholte Bild, das nach `nach` (monotonic)
        ankam. Gibt (zeit, y_ebene)."""
        with self.cv:
            ok = self.cv.wait_for(
                lambda: self.fehler or (self.nummer > self.geholt and
                                        (nach is None or self.zeit >= nach)),
                warten)
            if self.fehler:
                raise autofokus.AfFehler(self.fehler)
            if not ok:
                raise autofokus.AfFehler('Die Kamera liefert kein Messbild')
            self.geholt = self.nummer
            return self.zeit, self.bild

    def stop(self):
        with self.cv:
            self.gestoppt = True
        Kamera._beenden(self.proc)


KAMERA = Kamera()
AF = autofokus.Autofokus(KAMERA)

SEITE = '''<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kamera – Engraver</title>
<style>
:root { color-scheme: dark; --grund: #111; --text: #ddd; --leise: #888;
        --knopf: #2a2a2a; --warn: #f0b040; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--grund); color: var(--text);
       font: 15px/1.4 -apple-system, system-ui, sans-serif; }
header { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center;
         padding: 10px 16px; }
header h1 { font-size: 16px; margin: 0 8px 0 0; }
.wert { font-variant-numeric: tabular-nums; }
.leise { color: var(--leise); }
.warn { color: var(--warn); }
button { background: var(--knopf); color: var(--text); border: 1px solid #444;
         border-radius: 6px; padding: 5px 10px; font: inherit; }
#rahmen { position: relative; width: 100%; overflow: hidden;
          background: #000; }
#bild { position: absolute; top: 50%; left: 50%; display: block; }
#hinweis { position: absolute; inset: 0; display: none; padding: 24px 16px;
           text-align: center; color: var(--leise); }
</style></head><body>
<header>
  <h1>Kamera</h1>
  <span>Schärfe <b class="wert" id="fom">–</b>
    <span class="leise">(bester <span class="wert" id="best">–</span>)</span>
  </span>
  <button id="neu" title="Bestwert zurücksetzen">neu</button>
  <span>Licht <b class="wert" id="lux">–</b> <span id="luxhinweis"></span></span>
  <button id="drehen" title="Bild um 90° drehen">↻ 90°</button>
  <a href="/bild.jpg" download="kamera.jpg"><button>Foto</button></a>
</header>
<div id="rahmen"><img id="bild" alt="Kamerabild">
  <div id="hinweis"></div></div>
<script>
const bild = document.getElementById('bild');
const rahmen = document.getElementById('rahmen');
const hinweis = document.getElementById('hinweis');
const B = @BREITE@, H = @HOEHE@;
let dreh = 0, best = null, versuch = 0;
try { dreh = +localStorage.getItem('dreh') || 0; } catch (e) {}

function auslegen() {
  const quer = dreh % 180 === 0;
  const w = quer ? B : H, h = quer ? H : B;
  const s = Math.min(rahmen.clientWidth / w,
                     Math.max(innerHeight - rahmen.offsetTop - 8, 120) / h);
  rahmen.style.height = Math.round(h * s) + 'px';
  bild.style.width = Math.round(B * s) + 'px';
  bild.style.height = Math.round(H * s) + 'px';
  bild.style.transform = 'translate(-50%,-50%) rotate(' + dreh + 'deg)';
}
function verbinden() {
  if (Date.now() - versuch < 3000) return;   // belegte Kamera nicht dauernd starten
  versuch = Date.now();
  bild.src = '/stream?' + versuch;
}

document.getElementById('drehen').onclick = () => {
  dreh = (dreh + 90) % 360;
  try { localStorage.setItem('dreh', dreh); } catch (e) {}
  auslegen();
};
document.getElementById('neu').onclick = () => {
  best = null; document.getElementById('best').textContent = '–';
};
addEventListener('resize', auslegen);
bild.onerror = () => setTimeout(verbinden, 3000);

async function abfragen() {
  try {
    const z = await (await fetch('/status', {cache: 'no-store'})).json();
    if (z.schaerfe != null) {
      document.getElementById('fom').textContent = z.schaerfe;
      if (best == null || z.schaerfe > best) best = z.schaerfe;
      document.getElementById('best').textContent = best;
    }
    document.getElementById('lux').textContent =
      z.lux == null ? '–' : z.lux + ' Lux';
    const dunkel = z.lux != null && z.lux < 30;
    const lh = document.getElementById('luxhinweis');
    lh.textContent = dunkel ? 'zu dunkel, Lampe an' : '';
    lh.className = dunkel ? 'warn' : '';
    hinweis.textContent = z.fehler;
    hinweis.style.display = z.fehler && !z.laeuft && !z.messung ? 'block' : 'none';
    if (!z.laeuft && !z.messung) verbinden();
  } catch (e) {}
}
auslegen(); verbinden();
setInterval(abfragen, 1000);
</script></body></html>
'''.replace('@BREITE@', str(BREITE)).replace('@HOEHE@', str(HOEHE))


class Anfrage(http.server.BaseHTTPRequestHandler):
    server_version = 'kamera-live'

    def do_GET(self):
        pfad = self.path.split('?', 1)[0]
        if pfad == '/':
            self._antwort(200, 'text/html; charset=utf-8', SEITE.encode())
        elif pfad == '/stream':
            self._stream()
        elif pfad == '/bild.jpg':
            self._einzelbild()
        elif pfad == '/status':
            self._json(200, KAMERA.zustand())
        elif pfad == '/autofokus':
            with open(os.path.join(HIER, 'autofokus.html'), 'rb') as f:
                self._antwort(200, 'text/html; charset=utf-8', f.read())
        elif pfad == '/api/af':
            self._json(200, dict(AF.zustand(), kamera=KAMERA.zustand()))
        elif pfad == '/api/af/bild.png' and AF.png():
            self._antwort(200, 'image/png', AF.png())
        else:
            self._antwort(404, 'text/plain; charset=utf-8', b'nicht da\n')

    def do_POST(self):
        """Aktionen des Autofokus. Nur mit JSON und eigenem Kopf: So kann
        keine fremde Webseite im Browser den Laser ausloesen (CORS)."""
        pfad = self.path.split('?', 1)[0]
        if (self.headers.get('X-Autofokus') != '1' or not self.headers.get(
                'Content-Type', '').startswith('application/json')):
            self._json(403, {'fehler': 'nur von der Autofokus-Seite'})
            return
        try:
            laenge = min(int(self.headers.get('Content-Length') or 0), 10000)
            daten = json.loads(self.rfile.read(laenge) or b'{}')
        except ValueError:
            self._json(400, {'fehler': 'kein JSON'})
            return
        aktion = pfad[len('/api/af/'):] if pfad.startswith('/api/af/') else ''
        try:
            if aktion in ('messen', 'lernen', 'messpunkt'):
                AF.starten(aktion, str(daten.get('name', ''))[:40])
            elif aktion == 'abbrechen':
                AF.abbrechen()
            elif aktion == 'loeschen':
                AF.loeschen(None if daten.get('alle') else int(daten['index']))
            else:
                self._json(404, {'fehler': 'unbekannte Aktion'})
                return
        except (autofokus.AfFehler, KeyError, ValueError, IndexError) as f:
            self._json(409, {'fehler': str(f)})
            return
        self._json(200, {'ok': True})

    def _json(self, code, daten):
        self._antwort(code, 'application/json',
                      json.dumps(daten, ensure_ascii=False).encode())

    def _antwort(self, code, art, daten):
        self.send_response(code)
        self.send_header('Content-Type', art)
        self.send_header('Content-Length', str(len(daten)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(daten)

    def _stream(self):
        KAMERA.anmelden()
        try:
            self.send_response(200)
            self.send_header('Content-Type',
                             'multipart/x-mixed-replace; boundary=bild')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            nummer = 0
            while True:
                daten, nummer = KAMERA.naechstes(nummer, 10.0)
                if daten is None:
                    break
                self.wfile.write(b'--bild\r\nContent-Type: image/jpeg\r\n'
                                 b'Content-Length: %d\r\n\r\n' % len(daten))
                self.wfile.write(daten)
                self.wfile.write(b'\r\n')
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        finally:
            KAMERA.abmelden()

    def _einzelbild(self):
        KAMERA.anmelden()
        try:
            nummer, daten = 0, None
            ende = time.monotonic() + 10.0
            while time.monotonic() < ende:
                daten, nummer = KAMERA.naechstes(nummer, 5.0)
                if daten is None:
                    break
                if time.monotonic() - KAMERA.start_zeit > EINSCHWINGEN:
                    break
            if daten is None:
                self._antwort(503, 'text/plain; charset=utf-8',
                              (KAMERA.fehler or 'kein Bild').encode() + b'\n')
            else:
                self._antwort(200, 'image/jpeg', daten)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        finally:
            KAMERA.abmelden()

    def log_message(self, *args):
        pass   # kein Eintrag je Anfrage im Journal


class Server(http.server.ThreadingHTTPServer):
    """Lauscht auf IPv6 und IPv4; laser.local loest am Mac oft zuerst
    IPv6 auf."""
    daemon_threads = True
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def main():
    try:
        server = Server(('::', PORT), Anfrage)
    except OSError:          # ohne IPv6
        server = http.server.ThreadingHTTPServer(('', PORT), Anfrage)
        server.daemon_threads = True

    def ende(*_):
        KAMERA.aus()
        sys.exit(0)

    signal.signal(signal.SIGTERM, ende)
    signal.signal(signal.SIGINT, ende)
    print('Kamera-Livebild auf Port %d' % PORT, flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
