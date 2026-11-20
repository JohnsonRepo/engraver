"""autofokus.py — Autofokus ueber Z mit der Kamera (docs/kamerahalter.md).

Messen: Z ganz hoch, Kopf zum Messpunkt, Laser kurz mit 1 % an. Die Kamera
sieht den Punkt schraeg von vorn rechts; je hoeher die Oberflaeche, desto
weiter wandert er im Bild. Aus seiner Lage folgt ueber die Lerntabelle das
Z, bei dem der Laser scharf ist. Z faehrt dorthin, G54 Z0 wird dort gesetzt.

Lernen: Von Hand scharfstellen wie bisher, dann "lernen". Das Programm
merkt sich Z (Maschinenkoordinate) und die Lage des Punkts. Zwei bis vier
Werkstueckdicken genuegen; den Fokusabstand des Lasers muss niemand kennen.
Ab drei Punkten passt eine projektive Kurve (wie die Kamera abbildet).

Der Messpunkt ist eine feste Stelle in Maschinenkoordinaten (X, Y). Er wird
einmal gesetzt; dabei wird die Tabelle geleert, denn sie gilt nur fuer ihn.

Die Kamera und CNCjs kommen von aussen (kamera.py, cncjs_client.py), damit
sich alles ohne Maschine pruefen laesst (tools/autofokus_check.py).
"""

import json
import math
import operator
import os
import struct
import threading
import time
import zlib

import cncjs_client

B, H = 1280, 960                 # Messbild: Y-Ebene von YUV420, ohne Rand
DATEI = os.environ.get('AUTOFOKUS_DATEI') or os.path.expanduser(
    '~/.config/engraver/autofokus.json')

EINSTELLUNGEN = {
    'z_mess': -2.0,              # Maschinen-Z beim Messen: ganz oben
    'laser_s': 10,               # 1 % bei $30=1000, wie "Laserpunkt 1 %"
    'laser_dauer_s': 1.0,        # G4: so lange brennt der Punkt hoechstens
    'belichtung_us': 2048,       # 2 PWM-Perioden des Uno (976 Hz)
    'verstaerkung': 1.0,
    'min_anstieg': 40,           # Helligkeit (0..255), darunter kein Punkt
    'grob_schritt': 4,           # Raster der groben Suche in Pixeln
    'fenster': 96,               # halbe Kante des Feinfensters in Pixeln
    'quer_min_px': 15,           # erlaubter Abstand neben der Lernlinie
    'ueberstand': 0.25,          # Extrapolation: Anteil der gelernten Spanne
}


class AfFehler(Exception):
    """Abbruch mit einer Meldung fuer den Nutzer."""


class AfAbbruch(AfFehler):
    pass


# -- Bildauswertung (reine Funktionen auf der Y-Ebene) ----------------------------

def grob_suchen(an, aus, schritt=4, b=B, h=H, abstand=100):
    """Groesster Anstieg an - aus auf einem Raster. Gibt das beste
    (anstieg, x, y) und das beste mehr als `abstand` px davon entfernt."""
    zeilen = []
    for y in range(0, h, schritt):
        d = list(map(operator.sub, an[y * b:(y + 1) * b:schritt],
                     aus[y * b:(y + 1) * b:schritt]))
        m = max(d)
        zeilen.append((m, d.index(m) * schritt, y))
    bester = max(zeilen)
    rest = [z for z in zeilen
            if abs(z[1] - bester[1]) > abstand or abs(z[2] - bester[2]) > abstand]
    return bester, (max(rest) if rest else (0, 0, 0))


def verfeinern(an, aus, x0, y0, r=96, b=B, h=H):
    """Schwerpunkt des Punkts im Fenster um (x0, y0): gewichtet mit dem
    Anstieg ueber der halben Spitze. Gibt (x, y, spitze, pixel)."""
    x1, x2 = max(0, x0 - r), min(b, x0 + r + 1)
    y1, y2 = max(0, y0 - r), min(h, y0 + r + 1)
    feld = [list(map(operator.sub, an[y * b + x1:y * b + x2],
                     aus[y * b + x1:y * b + x2])) for y in range(y1, y2)]
    spitze = max(max(z) for z in feld)
    schwelle = spitze / 2.0
    sw = sx = sy = 0.0
    n = 0
    for j, zeile in enumerate(feld):
        for i, v in enumerate(zeile):
            if v > schwelle:
                g = v - schwelle
                sw += g
                sx += g * i
                sy += g * j
                n += 1
    if sw <= 0:
        return float(x0), float(y0), spitze, 0
    return x1 + sx / sw, y1 + sy / sw, spitze, n


def rest_anstieg(nach, aus, x, y, r=12, b=B, h=H):
    """Groesster Anstieg nahe (x, y) in einem spaeteren Bild."""
    x, y = int(round(x)), int(round(y))
    x1, x2 = max(0, x - r), min(b, x + r + 1)
    werte = [max(map(operator.sub, nach[yy * b + x1:yy * b + x2],
                     aus[yy * b + x1:yy * b + x2]))
             for yy in range(max(0, y - r), min(h, y + r + 1))]
    return max(werte) if werte else 0


def punkt_finden(an, aus, e=EINSTELLUNGEN, b=B, h=H):
    """Laserpunkt im Bild `an` gegenueber `aus`. Gibt ein dict oder Fehler."""
    (anstieg, x0, y0), (zweiter, _, _) = grob_suchen(
        an, aus, e['grob_schritt'], b, h)
    if anstieg < e['min_anstieg']:
        raise AfFehler('Kein Laserpunkt im Bild (Anstieg %d, nötig %d). Liegt '
                       'das Werkstück unter dem Messpunkt?'
                       % (anstieg, e['min_anstieg']))
    if zweiter > 0.7 * anstieg:
        raise AfFehler('Zwei helle Stellen im Bild (%d und %d): Spiegelung oder '
                       'Licht an- und ausgegangen? Noch einmal messen.'
                       % (anstieg, zweiter))
    x, y, spitze, n = verfeinern(an, aus, x0, y0, e['fenster'], b, h)
    return {'u': round(x, 2), 'v': round(y, 2), 'spitze': spitze, 'pixel': n,
            'zweiter': zweiter}


# -- Messbild als PNG (fuer die Seite) ---------------------------------------------

_HELLER = bytes(int(255 * (i / 255.0) ** 0.4 + 0.5) for i in range(256))


def png_grau(breite, hoehe, zeilen):
    def block(art, daten):
        return (struct.pack('>I', len(daten)) + art + daten
                + struct.pack('>I', zlib.crc32(art + daten) & 0xFFFFFFFF))
    roh = b''.join(b'\x00' + z for z in zeilen)
    return (b'\x89PNG\r\n\x1a\n'
            + block(b'IHDR', struct.pack('>IIBBBBB', breite, hoehe, 8, 0, 0, 0, 0))
            + block(b'IDAT', zlib.compress(roh, 3)) + block(b'IEND', b''))


def messbild_png(an, punkt=None, b=B, h=H):
    """Halbe Aufloesung, Schatten aufgehellt, Kreuz auf dem Punkt."""
    zeilen = [bytearray(an[y * b:(y + 1) * b:2].translate(_HELLER))
              for y in range(0, h, 2)]
    if punkt:
        px, py = int(punkt['u'] / 2), int(punkt['v'] / 2)
        for k in range(-30, 31):
            if 6 <= abs(k):
                farbe = 255 if (abs(k) // 4) % 2 else 0
                if 0 <= px + k < b // 2 and 0 <= py < h // 2:
                    zeilen[py][px + k] = farbe
                if 0 <= py + k < h // 2 and 0 <= px < b // 2:
                    zeilen[py + k][px] = farbe
    return png_grau(b // 2, h // 2, [bytes(z) for z in zeilen])


# -- Lerntabelle --------------------------------------------------------------------

def projektiv(tz, ueberstand=0.25, max_rest=0.1):
    """z(t) = (a t + b) / (c t + 1) durch die gelernten Punkte (kleinste
    Quadrate, ab drei Punkten). So bildet eine Kamera Punkte einer Geraden,
    hier des senkrechten Strahls, auf eine Bildgerade ab. None, wenn es zu
    wenige Punkte sind oder die Kurve nicht taugt; dann gilt linear."""
    if len(tz) < 3:
        return None
    # a t + b - c t z = z, Normalgleichungen 3 x 3
    zeilen = [([t, 1.0, -t * z], z) for t, z in tz]
    m = [[sum(r[i] * r[j] for r, _ in zeilen) for j in range(3)]
         + [sum(r[i] * w for r, w in zeilen)] for i in range(3)]
    for k in range(3):
        piv = max(range(k, 3), key=lambda i: abs(m[i][k]))
        if abs(m[piv][k]) < 1e-12:
            return None
        m[k], m[piv] = m[piv], m[k]
        for i in range(3):
            if i != k:
                f = m[i][k] / m[k][k]
                m[i] = [x - f * y for x, y in zip(m[i], m[k])]
    a, b, c = (m[i][3] / m[i][i] for i in range(3))
    t0, t1 = tz[0][0], tz[-1][0]
    rand = ueberstand * (t1 - t0)
    nenner = [c * t + 1.0 for t in (t0 - rand, t1 + rand)]
    if min(nenner) < 0.2:                 # Pol im Bereich oder zu stark gekruemmt
        return None
    if a - b * c <= 0:                    # muss mit t steigen
        return None
    if max(abs((a * t + b) / (c * t + 1.0) - z) for t, z in tz) > max_rest:
        return None
    return a, b, c


class Tabelle:
    """Messpunkt (Maschinen-X/Y) und gelernte Punkte (u, v, z) in JSON."""

    def __init__(self, datei=DATEI):
        self.datei = datei
        self.messpunkt = None
        self.punkte = []
        self.einstellungen = {}
        self.laden()

    def laden(self):
        try:
            with open(self.datei, encoding='utf-8') as f:
                d = json.load(f)
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            os.replace(self.datei, self.datei + '.kaputt')
            return
        self.messpunkt = d.get('messpunkt')
        self.punkte = d.get('punkte', [])
        self.einstellungen = d.get('einstellungen', {})

    def speichern(self):
        os.makedirs(os.path.dirname(self.datei), exist_ok=True)
        tmp = self.datei + '.neu'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({'messpunkt': self.messpunkt, 'punkte': self.punkte,
                       'einstellungen': self.einstellungen},
                      f, indent=1, ensure_ascii=False)
        os.replace(tmp, self.datei)

    def messpunkt_setzen(self, x, y):
        self.messpunkt = [round(x, 3), round(y, 3)]
        self.punkte = []
        self.speichern()

    def hinzufuegen(self, punkt, z, name):
        self.punkte.append({'u': punkt['u'], 'v': punkt['v'], 'z': round(z, 3),
                            'name': name or '', 'spitze': punkt.get('spitze'),
                            'zeit': time.strftime('%Y-%m-%d %H:%M')})
        self.speichern()

    def loeschen(self, index=None):
        if index is None:
            self.punkte = []
        elif 0 <= index < len(self.punkte):
            del self.punkte[index]
        else:
            raise AfFehler('Diesen Eintrag gibt es nicht')
        self.speichern()

    def modell(self):
        """Gerade durch die gelernten Punkte im Bild (Hauptachse), Position
        t entlang ihr steigt mit z. Fehler, wenn die Tabelle nicht taugt."""
        p = self.punkte
        if len(p) < 3:                   # zwei: Perspektive nicht erfasst
            raise AfFehler('Erst mindestens drei Dicken lernen (jetzt %d)'
                           % len(p))
        mu = sum(q['u'] for q in p) / len(p)
        mv = sum(q['v'] for q in p) / len(p)
        suu = sum((q['u'] - mu) ** 2 for q in p)
        svv = sum((q['v'] - mv) ** 2 for q in p)
        suv = sum((q['u'] - mu) * (q['v'] - mv) for q in p)
        w = 0.5 * math.atan2(2 * suv, suu - svv)
        ex, ey = math.cos(w), math.sin(w)
        tz = [((q['u'] - mu) * ex + (q['v'] - mv) * ey, q['z'], q) for q in p]
        mz = sum(q['z'] for q in p) / len(p)
        if sum(t * (z - mz) for t, z, _ in tz) < 0:
            ex, ey = -ex, -ey
            tz = [(-t, z, q) for t, z, q in tz]
        tz.sort(key=lambda a: a[0])
        for (t1, z1, q1), (t2, z2, q2) in zip(tz, tz[1:]):
            if t2 - t1 < 2.0 or z2 - z1 < 0.05:
                raise AfFehler('Gelernte Punkte "%s" und "%s" widersprechen sich '
                               'oder liegen zu nah beieinander: einen löschen'
                               % (q1['name'] or q1['zeit'],
                                  q2['name'] or q2['zeit']))
        quer = max(abs(-(q['u'] - mu) * ey + (q['v'] - mv) * ex) for q in p)
        tz2 = [(t, z) for t, z, _ in tz]
        return {'mu': mu, 'mv': mv, 'ex': ex, 'ey': ey, 'quer': quer,
                'tz': tz2, 'proj': projektiv(tz2),
                'namen': [q['name'] for _, _, q in tz]}

    def z_fuer(self, u, v, e=EINSTELLUNGEN):
        """Fokus-Z fuer einen Punkt im Bild, mit Pruefung auf Plausibilitaet."""
        m = self.modell()
        du, dv = u - m['mu'], v - m['mv']
        t = du * m['ex'] + dv * m['ey']
        s = -du * m['ey'] + dv * m['ex']
        grenze = max(e['quer_min_px'], 3 * m['quer'])
        if abs(s) > grenze:
            raise AfFehler('Der Punkt liegt %.0f px neben der gelernten Linie '
                           '(erlaubt %.0f): Messpunkt, Kamera oder Halter bewegt? '
                           'Dann Tabelle neu lernen.' % (abs(s), grenze))
        tz = m['tz']
        spanne = tz[-1][0] - tz[0][0]
        if not (tz[0][0] - e['ueberstand'] * spanne <= t
                <= tz[-1][0] + e['ueberstand'] * spanne):
            raise AfFehler('Die Dicke liegt außerhalb des Gelernten: eine '
                           'Platte dieser Dicke von Hand scharfstellen und lernen')
        if m['proj']:
            a, b, c = m['proj']
            z = (a * t + b) / (c * t + 1.0)
        else:
            i = 0
            while i < len(tz) - 2 and t > tz[i + 1][0]:
                i += 1
            (t1, z1), (t2, z2) = tz[i], tz[i + 1]
            z = z1 + (z2 - z1) * (t - t1) / (t2 - t1)
        return z, {'t': round(t, 1), 'quer': round(s, 1),
                   'kurve': 'projektiv' if m['proj'] else 'linear',
                   'ueber': round(z - tz[0][1], 2), 'unten': m['namen'][0]}


# -- Ablauf an der Maschine ----------------------------------------------------------

class Autofokus:
    """Ein Lauf zur Zeit: messen, lernen oder Messpunkt setzen. Laeuft in einem
    Thread; zustand() ist fuer die Seite."""

    def __init__(self, kamera, cncjs=cncjs_client, datei=DATEI):
        self.kamera = kamera
        self.cncjs = cncjs
        self.tabelle = Tabelle(datei)
        self.e = dict(EINSTELLUNGEN, **self.tabelle.einstellungen)
        self.lock = threading.Lock()
        self.abbruch = threading.Event()
        self._z = {'laeuft': False, 'art': '', 'schritt': '', 'meldung': '',
                   'fehler': '', 'ergebnis': None, 'punkt': None, 'bild': 0}
        self._png = None
        self._v = None

    # fuer die Seite

    def zustand(self):
        with self.lock:
            z = dict(self._z)
        z['messpunkt'] = self.tabelle.messpunkt
        z['punkte'] = self.tabelle.punkte
        try:
            self.tabelle.modell()
            z['tabelle'] = ''
        except AfFehler as f:
            z['tabelle'] = str(f)
        z['laser_s'] = self.e['laser_s']
        z['bildgroesse'] = [B, H]
        return z

    def png(self):
        return self._png

    def starten(self, art, name=''):
        with self.lock:
            if self._z['laeuft']:
                raise AfFehler('Es läuft schon: %s' % self._z['schritt'])
            self._z.update(laeuft=True, art=art, schritt='Start', fehler='',
                           meldung='')
        self.abbruch.clear()
        threading.Thread(target=self._lauf, args=(art, name),
                         daemon=True).start()

    def abbrechen(self):
        self.abbruch.set()

    def loeschen(self, index=None):
        if self._z['laeuft']:
            raise AfFehler('Bitte warten, bis der Lauf fertig ist')
        self.tabelle.loeschen(index)

    def _schritt(self, text):
        if self.abbruch.is_set():
            raise AfAbbruch('Abgebrochen')
        with self.lock:
            self._z['schritt'] = text

    # der Lauf

    def _lauf(self, art, name):
        v = None
        try:
            if art in ('messen', 'lernen') and not self.tabelle.messpunkt:
                raise AfFehler('Erst den Messpunkt setzen (unter Einlernen)')
            if art == 'messen':
                self.tabelle.modell()      # Tabelle vor jeder Fahrt pruefen
            self._schritt('Verbinde mit CNCjs')
            try:
                v = self._v = self.cncjs.verbinden()
            except cncjs_client.CncjsFehler as f:
                raise AfFehler(str(f))
            self._bereit(v)
            weg = self.cncjs.verfahrweg(v.settings)
            pos = self.cncjs.mpos(v.zustand)
            if art == 'messpunkt':
                self.tabelle.messpunkt_setzen(pos['x'], pos['y'])
                self._fertig('Messpunkt gesetzt: X %.2f Y %.2f (Maschine). Die '
                             'Tabelle ist leer, jetzt Dicken lernen.'
                             % (pos['x'], pos['y']))
                return
            z_mess = self.e['z_mess']
            mx, my = self.tabelle.messpunkt
            self._im_weg(weg, x=mx, y=my, z=z_mess)
            if art == 'lernen':
                z_fokus = pos['z']
                if z_fokus > z_mess - 1.0:
                    raise AfFehler('Z steht ganz oben: erst von Hand scharfstellen, '
                                   'dann lernen')
            self._schritt('Z hoch')
            v.gcode('G90', 'G53 G0 Z%.3f' % z_mess)
            self._ruhe(v, {'z': z_mess})
            self._schritt('Zum Messpunkt')
            v.gcode('G53 G0 X%.3f Y%.3f' % (mx, my))
            self._ruhe(v, {'x': mx, 'y': my})
            punkt = self._messen(v)
            if art == 'lernen':
                self.tabelle.hinzufuegen(punkt, z_fokus, name)
                self._schritt('Zurück auf den Fokus')
                v.gcode('G53 G0 Z%.3f' % z_fokus)
                self._ruhe(v, {'z': z_fokus})
                self._fertig('Gelernt: Z %.2f%s, Punkt bei Bildzeile %.0f. '
                             '%d Dicken in der Tabelle.'
                             % (z_fokus, ' (%s)' % name if name else '',
                                punkt['v'], len(self.tabelle.punkte)))
                return
            z, info = self.tabelle.z_fuer(punkt['u'], punkt['v'], self.e)
            self._im_weg(weg, z=z)
            self._schritt('Z auf den Fokus')
            v.gcode('G53 G0 Z%.3f' % z)
            self._ruhe(v, {'z': z})
            self._schritt('G54 Z0 setzen')
            v.gcode('G10 L20 P1 Z0')
            self._ruhe(v, None)
            with self.lock:
                self._z['ergebnis'] = dict(info, z=round(z, 3))
            self._fertig('Fokus: Z %.2f (Maschine), dort G54 Z0. Oberfläche '
                         '%.1f mm über "%s".'
                         % (z, info['ueber'], info['unten'] or 'dem tiefsten Punkt'))
        except AfFehler as f:
            self._fehler(v, f)
        except Exception as f:                      # unerwartet: trotzdem melden
            self._fehler(v, AfFehler('%s: %s' % (type(f).__name__, f)))
        finally:
            if v is not None:
                v.schliessen()
            self._v = None
            with self.lock:
                self._z['laeuft'] = False

    def _fertig(self, text):
        with self.lock:
            self._z.update(meldung=text, schritt='fertig', fehler='')

    def _fehler(self, v, f):
        text = str(f)
        if isinstance(f, AfAbbruch) and v is not None:
            try:
                if self.cncjs.aktiv(v.zustand) in ('Run', 'Jog', 'Hold'):
                    v.befehl('feedhold')
                    v.befehl('reset')
                    text = ('Abgebrochen, die Maschine wurde angehalten. Vor dem '
                            'Weiterarbeiten Homing.')
            except cncjs_client.CncjsFehler:
                pass
        with self.lock:
            self._z.update(fehler=text, schritt='Fehler')

    # Bausteine

    def _bereit(self, v):
        c = self.cncjs
        if v.workflow not in ('idle', ''):
            raise AfFehler('In CNCjs läuft ein Auftrag (%s)' % v.workflow)
        if c.aktiv(v.zustand) != 'Idle':
            raise AfFehler('Die Maschine ist nicht bereit (%s): Homing, dann '
                           'noch einmal' % (c.aktiv(v.zustand) or 'unbekannt'))
        f = v.feeder or {}
        if f.get('queue') or f.get('pending'):
            raise AfFehler('CNCjs sendet noch Befehle, bitte warten')

    @staticmethod
    def _im_weg(weg, **ziel):
        for a, w in ziel.items():
            if not (-weg[a] + 0.5 <= w <= -0.5):
                raise AfFehler('%s %.2f liegt außerhalb des Verfahrwegs '
                               '(%.1f bis 0)' % (a.upper(), w, -weg[a]))

    def _ruhe(self, v, ziel, warten_s=90.0, mindest_s=0.5):
        """Bis alles gesendet, die Maschine steht und ggf. am Ziel ist."""
        c = self.cncjs
        t0 = time.monotonic()

        def fertig(v):
            f = v.feeder or {}
            if f.get('queue') or f.get('pending') or c.aktiv(v.zustand) != 'Idle':
                return False
            if ziel:
                p = c.mpos(v.zustand)
                return all(abs(p.get(a, 1e9) - w) < 0.02 for a, w in ziel.items())
            return time.monotonic() - t0 > mindest_s

        while not v.warten(fertig, 0.1):
            self._grbl_pruefen(v, t0)
            if self.abbruch.is_set():
                raise AfAbbruch('Abgebrochen')
            if time.monotonic() - t0 > warten_s:
                raise AfFehler('Die Maschine kommt nicht zur Ruhe (%s)'
                               % c.aktiv(v.zustand))
        self._grbl_pruefen(v, t0)

    def _grbl_pruefen(self, v, t0):
        if self.cncjs.aktiv(v.zustand) == 'Alarm':
            raise AfFehler('GRBL meldet Alarm: Homing, dann noch einmal')
        for z in v.meldungen_seit(t0):
            if z.startswith('error:') or z.startswith('ALARM:'):
                raise AfFehler('GRBL meldet %s' % z)

    def _messen(self, v):
        """Laser kurz an, bestes Bild suchen, pruefen, dass er wieder aus ist."""
        e = self.e
        with self.kamera.messung(e['belichtung_us'], e['verstaerkung']) as k:
            self._schritt('Kamera vorbereiten')
            for _ in range(3):                   # Belichtung einschwingen lassen
                k.naechstes()
            _, aus = k.naechstes()
            self._schritt('Laser %d %% an' % round(e['laser_s'] / 10))
            t0 = time.monotonic()
            v.gcode('G1 F600', 'M3 S%d' % e['laser_s'],
                    'G4 P%.2f' % e['laser_dauer_s'], 'M5')
            bestes = (-1, None)
            ende = t0 + e['laser_dauer_s'] + 2.0
            while time.monotonic() < ende:
                _, bild = k.naechstes()
                (anstieg, _, _), _ = grob_suchen(bild, aus, 8)
                if anstieg > bestes[0]:
                    bestes = (anstieg, bild)
                f = v.feeder or {}
                if (time.monotonic() > t0 + e['laser_dauer_s']
                        and not f.get('queue') and not f.get('pending')
                        and bestes[0] >= e['min_anstieg']
                        and float(v.zustand.get('status', {})
                                  .get('spindle', 0) or 0) == 0):
                    break
            self._schritt('Laser aus?')
            self._ruhe(v, None, warten_s=10.0)
            if not v.warten(lambda v: float(v.zustand.get('status', {})
                                            .get('spindle', 0) or 0) == 0, 3.0):
                v.gcode('M5')
                raise AfFehler('Der Laser meldet sich nicht aus: M5 gesendet')
            nach_ab = time.monotonic() + 0.3
            _, nach = k.naechstes(nach=nach_ab)
        an = bestes[1]
        punkt = None
        try:
            punkt = punkt_finden(an, aus, e)
        finally:                       # Messbild auch zeigen, wenn nichts da ist
            self._png = messbild_png(an, punkt)
            with self.lock:
                self._z['punkt'] = punkt
                self._z['bild'] += 1
        rest = rest_anstieg(nach, aus, punkt['u'], punkt['v'])
        if rest > 0.3 * punkt['spitze']:
            v.gcode('M5')
            raise AfFehler('Der Punkt ist nach M5 noch zu sehen: M5 noch einmal '
                           'gesendet, bitte prüfen')
        return punkt
