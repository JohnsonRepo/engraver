#!/usr/bin/env python3
"""CNC Shield V3 von oben: alle Anschluesse und was daran haengt.

Das Shield in der Lage des Fotos (Reset oben links, Schraubklemme unten
links, USB des Uno links), massstaeblich nach dem Bestueckungsdruck und dem
Schaltplan des Protoneer V3.00, den die Nachbauten uebernehmen [w]:

* links die Schraubklemme 12-36 V, die 2x6-Leiste EN/GND, STEP/DIR und
  5V/GND, die Jumper fuer den Klon der A-Achse und der Reset-Taster,
* in der Mitte vier Treibersockel mit den Mikroschritt-Jumpern darunter und
  rechts daneben je ein Motorstecker 2B 2A 1A 1B (am Shield abgelesen [v]),
* oben rechts RX/TX/5V/3V3 und SCL/SDA/GND/RST,
* am rechten Rand Endschalter, SpnEn/SpnDir/CoolEn, Abort/Hold/Resume und
  E-STOP, jede Reihe mit einem Signal- und einem GND-Stift.

Neben jedem Stift steht sein Uno-Pin unter GRBL 1.1 (hardware-notizen.md)
und was daran haengt. Nummern, Adern und Farben kommen aus der Kabelliste
(tools/verkabelung.py), wie in den anderen Bildern der Verkabelung. Jeder
Anschluss der Kabelliste am Shield muss gezeichnet sein, und jeder
gezeichnete Uno-Pin muss zur Tabelle der Kabelliste passen — sonst bricht
das Skript ab.

    python3 tools/shield_zeichnen.py   ->  docs/cnc-shield.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import (el, f1, text, de,                 # noqa: E402
                              TEXT, GRAU, BLAU, ROT)
import elektronik_zeichnen as ez                                 # noqa: E402
import verkabelung as vk                                         # noqa: E402
import verkabelung_zeichnen as vz                                # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'cnc-shield.svg')

W, H = 1340, 900
S = 8.0                        # px je mm
X0, Y0 = 380.0, 182.0          # linke obere Ecke der Platine
R = 2.54                       # Raster der Stiftleisten
PLATINE = ('#fbe3df', '#c92a2a')   # rotes Shield, aufgehellt, wie im Motorbild
DRUCK = PLATINE[1]                 # Bestueckungsdruck
LEISTE = '#2b2f36'                 # Kunststoff der Stiftleisten
STIFTFARBE, STIFTRAND = '#dee2e6', '#868e96'
DUPONT = '#111418'
FREI = '#adb5bd'                   # Hinweislinie an einem freien Stift
LS_X, LS_UNO, LS_TEXT = 946, 1008, 1070   # Spalten rechts: Stift, Uno, Text
LI_X = 318                                # rechte Kante der Texte links

LTS = vk.leitungen()
# Seit dem Elektronikfach kommt W6 (5 V der Lichtschranken) vom
# 5-V-Wandler; der 5V-Stift des Shields bleibt dann frei.
FUENF_V_FREI = not any('Shield 5V' in (a, b)
                       for lt in LTS for _, _, a, b in lt['adern'])
GEZEICHNET = set()             # Shield-Anschluesse der Kabelliste im Bild

# ---- Lage in mm: Ursprung oben links an der Platine, y nach unten ---------
# Umriss des Uno R3 (Arduino-Massblatt, in mil: 2540/2600/2700 lang, Stufen
# bei 100, 200, 1490, 1590 und 2040 quer), gespiegelt auf y nach unten.
UMRISS = ((0, 0), (64.52, 0), (66.04, 1.52), (66.04, 12.95), (68.58, 15.49),
          (68.58, 48.26), (66.04, 50.80), (66.04, 53.34), (0, 53.34))
# Buchsen des Uno unter dem Shield (x, y, Laenge, Breite): USB 6,3 mm ueber
# der Kante wie in Elektronik.py, Mitte 1,5" bzw. 0,3" ueber der Unterkante
USB = (-6.3, 9.24, 16.0, 12.0)
HOHL = (-1.8, 41.22, 14.0, 9.0)
LOECHER = ((13.5, 2.7), (13.5, 50.6))
RESET = (5.7, 4.5)
# 2x6-Leiste links: Spalte EN, STEP, 5V und Spalte GND, DIR, GND
LINKS_X = (11.22, 13.76)
LINKS_Y = tuple(9.95 + R * k for k in range(6))
LINKS = ('EN/GND', 'X.STEP/DIR', 'Y.STEP/DIR', 'Z.STEP/DIR', 'A.STEP/DIR',
         '5V/GND')
# Klon der A-Achse: Reihen X, Y, Z, D12/D13; Spalten A.STP (2) und A.DIR (2)
KLON_X = tuple(3.81 + R * k for k in range(4))
KLON_Y = tuple(25.40 + R * k for k in range(4))
KLON = ('X', 'Y', 'Z', 'D12')
KLON_JUMPER = 'Y'              # A klont Y (hardware-notizen.md)
# Schraubklemme RM 5,08: Koerper, Schrauben; Adern gehen nach unten heraus
KLEMME = (0.7, 37.2, 10.8, 43.0)
KLEMME_X = {'−': 3.23, '+': 8.31}   # Polung nach dem Aufdruck [w]
KLEMME_Y = 39.74
# Treibersockel: oberer linker Stift (EN) je Achse [v] Lage am Shield
SOCKEL = {'X': (16.56, 5.77), 'Y': (37.52, 5.77), 'Z': (16.56, 29.90),
          'A': (37.52, 29.90)}
SOCKEL_B = 12.70               # Abstand der Stiftreihen (0,5")
MOTOR_DX, MOTOR_DY = 16.51, 5.08    # Motorstecker neben den Treiberstiften 3-6
MOTORSTIFTE = ('2B', '2A', '1A', '1B')
M_DX, M_DY = 3.81, 15.24            # Jumper M0 M1 M2 unter dem Treiber
M_GESTECKT = ('M0', 'M1')           # MS1 + MS2 = 1/16 (TMC2209 standalone)
# oben rechts 2x4: Spalte RX TX 5V 3V3 und Spalte SCL SDA GND RST
OBEN_X = (59.74, 62.28)
OBEN_Y = tuple(6.40 + R * k for k in range(4))
OBEN = (('RX', 'SCL', 'D0', 'A5'), ('TX', 'SDA', 'D1', 'A4'),
        ('5V', 'GND', '5V', 'GND'), ('3V3', 'RST', '3V3', 'RST'))
# rechter Rand: je Reihe innen das Signal, aussen GND [w] (beim E-STOP ist
# im Schaltplan der aeussere, eckige Stift GND)
RECHTS_X = (63.55, 66.09)
RECHTS_Y = tuple(16.56 + R * k for k in range(13))
RECHTS = (('Z+', 'D11'), ('Z−', 'D11'), ('Y+', 'D10'), ('Y−', 'D10'),
          ('X+', 'D9'), ('X−', 'D9'), ('SpnEn', 'D12'), ('SpnDir', 'D13'),
          ('CoolEn', 'A3'), ('Abort', 'A0'), ('Hold', 'A1'),
          ('Resume', 'A2'), ('E-STOP', 'RST'))
GRUPPEN = ((0, 6, 'END STOPS'), (6, 9, None), (9, 12, None), (12, 13, None))
# Stift -> Schluessel der Kabelliste
AM_RAND = {'Z+': 'Shield Z+', 'Z−': 'Shield Z− S', 'Y+': 'Shield Y+',
           'X−': 'Shield X−', 'SpnEn': 'Shield SpnEn',
           'Abort': 'Shield Abort'}
# freie Stifte am Rand: wofuer GRBL 1.1 sie haette
RAND_FREI = {'Y−': 'frei — derselbe Pin wie Y+',
             'X+': 'frei — derselbe Pin wie X−',
             'SpnDir': 'frei (Spindelrichtung)',
             'CoolEn': 'frei (Kühlmittel, M8)',
             'Hold': 'frei (Taster Pause)',
             'Resume': 'frei (Taster Start/Weiter)',
             'E-STOP': 'frei — Reset des Uno, nicht der Not-Aus'}
OBEN_FREI = {'RX': 'frei (RX: USB · SCL: Probe-Eingang)',
             'TX': 'frei (TX: USB)', '3V3': 'frei'}


def P(x, y):
    """mm auf der Platine -> px in der Zeichnung."""
    return X0 + S * x, Y0 + S * y


def r_mm(x0, y0, x1, y1, fill, rand='none', b=1.0, rx=1.0, strich=None,
         deckkraft=None):
    (a, c), (d, e) = P(x0, y0), P(x1, y1)
    return el('rect', {'x': f1(a), 'y': f1(c), 'width': f1(d - a),
                       'height': f1(e - c), 'rx': rx, 'fill': fill,
                       'fill-opacity': deckkraft, 'stroke': rand,
                       'stroke-width': b, 'stroke-dasharray': strich})


def druck(x, y, s, gr=8.0, anker='middle', fett=True, farbe=DRUCK,
          drehen=False):
    """Bestueckungsdruck an (x, y) in mm; drehen: senkrecht, von unten
    nach oben zu lesen."""
    px, py = P(x, y)
    a = {'x': f1(px), 'y': f1(py), 'font-size': gr, 'fill': farbe,
         'text-anchor': anker, 'font-weight': '700' if fett else None,
         'transform': 'rotate(-90 {} {})'.format(f1(px), f1(py))
         if drehen else None}
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return el('text', a, s)


def zeile(x, y, teile, gr=10.5, anker='start'):
    """Textzeile aus Stuecken [(Text, fett, Farbe)]."""
    inhalt = ''.join(
        '<tspan{}{}>{}</tspan>'.format(
            ' font-weight="600"' if fett else '',
            ' fill="{}"'.format(farbe) if farbe else '',
            s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        for s, fett, farbe in teile)
    return el('text', {'x': f1(x), 'y': f1(y), 'font-size': gr,
                       'fill': TEXT, 'text-anchor': anker}, inhalt)


def stiftleiste(xs, ys):
    """Stiftleiste von oben: schwarzer Koerper, je Stift ein Quadrat."""
    t = [r_mm(min(xs) - R / 2, min(ys) - R / 2, max(xs) + R / 2,
              max(ys) + R / 2, LEISTE, '#000000', 0.6, rx=1.5)]
    for x in xs:
        for y in ys:
            px, py = P(x, y)
            t.append(vz.rechteck(px - 3.2, py - 3.2, 6.4, 6.4, STIFTFARBE,
                                 STIFTRAND, 0.6, rx=0.8))
    return t


def buchsenleiste(x, ys):
    """Buchsenleiste fuer den Treiber: schwarz, je Kontakt ein Loch."""
    t = [r_mm(x - R / 2 + 0.15, ys[0] - R / 2, x + R / 2 - 0.15,
              ys[-1] + R / 2, LEISTE, '#000000', 0.6, rx=1.2)]
    for y in ys:
        t.append(vz.kreis(*P(x, y), 2.4, '#5c636a'))
    return t


def dupont(x0, y0, x1=None, y1=None):
    """Dupont-Gehaeuse auf einem Stift (oder ueber zwei Stifte)."""
    x1 = x0 if x1 is None else x1
    y1 = y0 if y1 is None else y1
    return r_mm(min(x0, x1) - 1.12, min(y0, y1) - 1.12,
                max(x0, x1) + 1.12, max(y0, y1) + 1.12, DUPONT, '#000000',
                0.6, rx=1.6)


def jumper_mm(x0, y0, x1, y1):
    return r_mm(min(x0, x1) - 1.05, min(y0, y1) - 1.05, max(x0, x1) + 1.05,
                max(y0, y1) + 1.05, '#212529', '#000000', 0.8, rx=2.0)


def an(schluessel):
    """Adern der Kabelliste, die an diesem Shield-Anschluss enden:
    [(Nr, Funktion, Farbe, Gegenstelle)]. Zaehlt den Anschluss als
    gezeichnet."""
    z = []
    for lt in LTS:
        for f, farbe, a, b in lt['adern']:
            if schluessel in (a, b):
                z.append((lt['nr'], f, farbe, b if a == schluessel else a))
    if not z:
        raise SystemExit('{}: steht nicht in der Kabelliste'.format(
            schluessel))
    GEZEICHNET.add(schluessel)
    return z


def ziel(gegen):
    """'Lichtschranke Y, D0' — Name der Gegenstelle aus der Kabelliste,
    ohne die Stiftangabe hinter dem Doppelpunkt."""
    return vk.ANSCHLUSS[gegen][0].split(':')[0]


def badge_breite(nr):
    return 10.0 + 7.0 * len(nr)


# ---- Platine ---------------------------------------------------------------

def platine():
    t = []
    # Buchsen des Uno zuerst: das Shield liegt darueber
    for x, y, lang, breit in (USB, HOHL):
        t.append(r_mm(x, y, x + lang, y + breit, '#ced4da', '#868e96', 1.0,
                      rx=1.5))
    t.append(druck(USB[0] / 2, USB[1] + USB[3] / 2 + 1.0, 'USB', 8.5,
                   farbe='#495057'))
    t.append(el('polygon', {
        'points': ' '.join('{},{}'.format(*(f1(v) for v in P(x, y)))
                           for x, y in UMRISS),
        'fill': PLATINE[0], 'stroke': PLATINE[1], 'stroke-width': '1.4',
        'stroke-linejoin': 'round'}))
    for x, y in LOECHER:
        t.append(vz.kreis(*P(x, y), 1.6 * S, '#ffffff', PLATINE[1], 1.0))
    # zwischen den Linien zu den Motoren Z und A
    t.append(druck(43.5, 52.0, 'CNC SHIELD V3', 9.5))
    # Reset-Taster
    x, y = RESET
    t += [r_mm(0.8, 0.6, 10.85, 7.95, 'none', DRUCK, 0.8, rx=0.5),
          r_mm(x - 3.0, y - 3.0, x + 3.0, y + 3.0, '#495057', '#212529', 0.8,
               rx=1.0),
          vz.kreis(*P(x, y), 1.8 * S, '#212529'),
          druck(10.15, 4.3, 'RST', 7.5, drehen=True)]
    t += links()
    t += klon()
    t += klemme()
    for achse in SOCKEL:
        t += treiber(achse)
    t += oben_rechts()
    t += rechter_rand()
    return t


def links():
    """2x6-Leiste: EN/GND, STEP/DIR der vier Achsen, 5V/GND."""
    t = stiftleiste(LINKS_X, LINKS_Y)
    t.append(r_mm(9.85, LINKS_Y[0] - 1.45, LINKS_X[1] + 1.45,
                  LINKS_Y[-1] + 1.45, 'none', DRUCK, 0.7, rx=0.5))
    for y, s in zip(LINKS_Y, LINKS):
        t.append(druck(9.55, y + 0.95, s, 7.6, 'end'))
    return t


def klon():
    """Jumper fuer die A-Achse: A.STP und A.DIR je an X, Y, Z oder D12/D13."""
    t = stiftleiste(KLON_X, KLON_Y)
    t.append(r_mm(0.25, KLON_Y[0] - 1.45, KLON_X[-1] + 1.45,
                  KLON_Y[-1] + 1.45, 'none', DRUCK, 0.7, rx=0.5))
    for y, s in zip(KLON_Y, KLON):
        if s == 'D12':
            t += [druck(1.35, y - 0.15, 'D', 6.5), druck(1.35, y + 1.0, '12',
                                                         6.5)]
        else:
            t.append(druck(1.35, y + 1.0, s, 8.0))
    t += [druck(KLON_X[-1] + 2.55, KLON_Y[-1] - 0.15, 'D', 6.5),
          druck(KLON_X[-1] + 2.55, KLON_Y[-1] + 1.0, '13', 6.5),
          druck((KLON_X[0] + KLON_X[1]) / 2, KLON_Y[-1] + 3.6, 'A.STP', 7.2),
          druck((KLON_X[2] + KLON_X[3]) / 2, KLON_Y[-1] + 3.6, 'A.DIR', 7.2)]
    y = KLON_Y[KLON.index(KLON_JUMPER)]
    t += [jumper_mm(KLON_X[0], y, KLON_X[1], y),
          jumper_mm(KLON_X[2], y, KLON_X[3], y)]
    return t


def klemme():
    """Schraubklemme 12-36 V; W3 geht unten heraus, rot und schwarz."""
    x0, y0, x1, y1 = KLEMME
    t = [r_mm(x0, y0, x1, y1, '#1c7ed6', '#1864ab', 0.9, rx=1.0)]
    for pol, x in KLEMME_X.items():
        t += [vz.kreis(*P(x, KLEMME_Y), 1.65 * S, '#a5d8ff', '#1864ab', 0.9),
              el('line', {'x1': f1(P(x - 1.0, 0)[0]),
                          'y1': f1(P(0, KLEMME_Y)[1]),
                          'x2': f1(P(x + 1.0, 0)[0]),
                          'y2': f1(P(0, KLEMME_Y)[1]),
                          'stroke': '#1864ab', 'stroke-width': '1.4'}),
              r_mm(x - 1.0, y1 - 1.1, x + 1.0, y1, '#0b4f8a', 'none', rx=0.4),
              druck(x + 1.6, y1 + 2.3, pol, 10.0, 'middle')]
    t.append(druck((KLEMME_X['−'] + KLEMME_X['+']) / 2, y1 + 5.1, '12–36V',
                   7.2))
    return t


def treiber(achse):
    """Sockel, Mikroschritt-Jumper, Treiber (durchsichtig) und Motorstecker."""
    x0, y0 = SOCKEL[achse]
    reihen = tuple(y0 + R * k for k in range(8))
    t = buchsenleiste(x0, reihen) + buchsenleiste(x0 + SOCKEL_B, reihen)
    # EN-Aufdruck am oberen linken Stift
    t += [vz.kreis(*P(x0, y0), 3.0, '#fcc419', '#b08900', 0.8),
          druck(x0 + 1.75, y0 - 0.35, 'EN', 6.8, 'start')]
    # Mikroschritt-Jumper M0 M1 M2 (unter dem Treiber)
    mx = tuple(x0 + M_DX + R * k for k in range(3))
    my = (y0 + M_DY, y0 + M_DY + R)
    t += stiftleiste(mx, my)
    for x, s in zip(mx, ('M0', 'M1', 'M2')):
        t.append(druck(x, my[0] - 1.75, s, 6.6))
        if s in M_GESTECKT:
            t.append(jumper_mm(x, my[0], x, my[1]))
    # Treiber TMC2209, durchsichtig: Jumper und Sockel bleiben sichtbar
    t += [r_mm(x0 - R / 2, y0 - R / 2, x0 + SOCKEL_B + R / 2,
               reihen[-1] + R / 2, '#2b2f36', '#2b2f36', 1.0, rx=1.5,
               strich='4 3', deckkraft=0.10),
          druck(x0 + SOCKEL_B / 2, y0 + 3.4, 'TMC2209', 7.5, farbe='#495057')]
    # Motorstecker mit dem Dupont-Stecker des Motorkabels
    hx = x0 + MOTOR_DX
    hy = tuple(y0 + MOTOR_DY + R * k for k in range(4))
    paare = an('Shield {} 2B·2A'.format(achse)) + \
        an('Shield {} 1A·1B'.format(achse))
    farben = vz.farben(paare[0][2]) + vz.farben(paare[1][2])
    t += stiftleiste((hx,), hy)
    t.append(dupont(hx, hy[0], hx, hy[-1]))
    for y, f in zip(hy, farben):
        t.append(vz.kreis(*P(hx, y), 3.0, vz.ADERFARBE[f], '#ffffff', 1.0))
    if achse == 'X':
        for y, s in zip(hy, MOTORSTIFTE):
            t.append(druck(hx + 1.75, y + 0.75, s, 6.6, 'start'))
    # Achsbuchstabe im Kaestchen unter dem Stecker
    by = hy[-1] + 2.0
    t += [r_mm(hx - 1.55, by, hx + 1.55, by + 2.9, '#ffffff', DRUCK, 0.9,
               rx=0.4),
          druck(hx, by + 2.3, achse, 9.5)]
    return t


def oben_rechts():
    """2x4: RX TX 5V 3V3 | SCL SDA GND RST."""
    t = stiftleiste(OBEN_X, OBEN_Y)
    t.append(r_mm(OBEN_X[0] - 1.45, OBEN_Y[0] - 1.45, OBEN_X[1] + 1.45,
                  OBEN_Y[-1] + 1.45, 'none', DRUCK, 0.7, rx=0.5))
    for y, (a, b, _, _) in zip(OBEN_Y, OBEN):
        t += [druck(OBEN_X[0] - 1.6, y + 0.8, a, 6.8, 'end'),
              druck(OBEN_X[1] + 1.6, y + 0.8, b, 6.8, 'start')]
    return t


def rechter_rand():
    """Endschalter, SpnEn/SpnDir/CoolEn, Abort/Hold/Resume, E-STOP."""
    t = stiftleiste(RECHTS_X, RECHTS_Y)
    for i0, i1, name in GRUPPEN:
        xl = 57.2 if name else 55.9
        t.append(r_mm(xl, RECHTS_Y[i0] - 1.3, RECHTS_X[1] + 1.4,
                      RECHTS_Y[i1 - 1] + 1.3, 'none', DRUCK, 0.7, rx=0.5))
        if name:
            t.append(druck(58.45, (RECHTS_Y[i0] + RECHTS_Y[i1 - 1]) / 2,
                           name, 7.4, drehen=True))
    for y, (s, _) in zip(RECHTS_Y, RECHTS):
        t.append(druck(62.1, y + 0.8, s, 7.2, 'end'))
    return t


# ---- Beschriftung rechts ---------------------------------------------------

def leitung_rechts(y, punkte, farbe):
    """Ader vom Stift bis an die Spalte rechts, auf Hoehe der Reihe y."""
    t = vz.draht([P(*p) for p in punkte] + [(LS_X - 10, P(0, y)[1])], farbe,
                 b=2.2)
    return t


def frei_linie(x, y):
    a, b = P(x + 1.3, y)
    return el('line', {'x1': f1(a), 'y1': f1(b), 'x2': f1(LS_X - 10),
                       'y2': f1(b), 'stroke': FREI, 'stroke-width': '1',
                       'stroke-dasharray': '2 3'})


def spalten(y, stift, uno, rest):
    """Eine Zeile rechts: Stift fett, Uno-Pin grau, dann rest (Liste von
    SVG-Teilen, die bei LS_TEXT beginnen)."""
    py = P(0, y)[1] + 3.6
    return [text(LS_X, py, stift, 10.5, TEXT, fett=True),
            text(LS_UNO, py, uno, 10, GRAU)] + rest(py)


def mit_marke(nr, teile):
    """Nummer der Leitung und Text dahinter, ab LS_TEXT."""
    def rest(py):
        return vz.marke(LS_TEXT, py, nr) + [
            zeile(LS_TEXT + badge_breite(nr) + 6, py, teile, 10.5)]
    return rest


def nur_text(s):
    def rest(py):
        return [text(LS_TEXT, py, s, 10.5, GRAU)]
    return rest


def rechts():
    t = [text(LS_X, P(0, OBEN_Y[0])[1] - 22, 'Stift', 9.5, GRAU),
         text(LS_UNO, P(0, OBEN_Y[0])[1] - 22, 'Uno', 9.5, GRAU),
         text(LS_TEXT, P(0, OBEN_Y[0])[1] - 22,
              'GRBL 1.1 und was daran hängt', 9.5, GRAU)]
    pin = dict((s, (u, k)) for k, (s, u) in enumerate(RECHTS))
    # Uno-Pins gegen die Tabelle der Kabelliste
    for s, schluessel in AM_RAND.items():
        soll = next(p for k, p, _ in vk.SHIELD if k == schluessel)
        if pin[s][0] != soll:
            raise SystemExit('{}: Bild {}, Kabelliste {}'.format(
                s, pin[s][0], soll))
    # oben rechts
    xi, xa = OBEN_X
    for y, (a, b, ua, ub) in zip(OBEN_Y, OBEN):
        if a == '5V' and not FUENF_V_FREI:
            (nr, f, farbe, gegen), = an('Shield 5V')
            # unter dem GND-Stift und seinem Aufdruck durch
            t += [dupont(xi, y)]
            t += leitung_rechts(y, [(xi, y), (xi + 1.5, y + 1.5),
                                    (67.6, y + 1.5), (69.0, y)], farbe)
            t += spalten(y, '5V · GND', '5 V · GND', mit_marke(nr, [
                ('5V → ', False, None), (ziel(gegen), True, None),
                (' · GND frei', False, GRAU)]))
        elif a == '5V':
            # seit dem Elektronikfach kommt W6 vom 5-V-Wandler, nicht vom
            # Shield: beide Stifte frei
            t.append(frei_linie(xa, y))
            t += spalten(y, '5V · GND', '5 V · GND', nur_text(
                'frei (die Lichtschranken bekommen 5 V vom Wandler, W6)'))
        else:
            t.append(frei_linie(xa, y))
            t += spalten(y, '{} · {}'.format(a, b), '{} · {}'.format(ua, ub),
                         nur_text(OBEN_FREI[a]))
    # rechter Rand
    xi, xa = RECHTS_X
    for k, ((s, uno), y) in enumerate(zip(RECHTS, RECHTS_Y)):
        if s == 'Z−':
            (nr, f, farbe, gegen), = an('Shield Z− S')
            if gegen != 'Shield Z− GND':
                raise SystemExit('Z−: {} statt Pull-down'.format(gegen))
            an('Shield Z− GND')
            # der Widerstand steckt mit beiden Beinen im 2-poligen Gehaeuse
            px, py = P(xa + 1.12, y)
            t += [dupont(xi, y, xa, y),
                  el('line', {'x1': f1(px), 'y1': f1(py),
                              'x2': f1(LS_X - 10), 'y2': f1(py),
                              'stroke': vz.STIFT, 'stroke-width': '1.4'}),
                  vz.widerstand(px + 10, py, lang=16)]
            t += spalten(y, s, uno, mit_marke(nr, [
                ('Pull-down {} zwischen Signal und GND'.format(f), False,
                 None)]))
        elif s in AM_RAND:
            adern = an(AM_RAND[s])
            nr, f, farbe, gegen = adern[0]
            # um den GND-Stift herum: durch die Luecke zur freien Nachbarreihe
            frei_oben = k > 0 and RECHTS[k - 1][0] not in AM_RAND and \
                RECHTS[k - 1][0] != 'Z−'
            d = -R / 2 if (k == 0 or frei_oben) else R / 2
            t += [dupont(xi, y)]
            t += leitung_rechts(y, [(xi, y), (xi + R / 2, y + d),
                                    (xa + R / 2 + 0.2, y + d),
                                    (xa + R / 2 + 1.5, y)], farbe)
            if s == 'Abort':
                # Spannungsteiler: eine Ader zur Wago +24 V, eine zur GND
                ziele = ' und '.join(vk.ANSCHLUSS[g][0].replace('Wago ', '')
                                     for _, _, _, g in adern)
                teile = [('24-V-Wächter', True, None),
                         (' → Wago ' + ziele, False, None)]
            elif s == 'Z+':
                teile = [('Laser-PWM', True, None),
                         (' → {}'.format(ziel(gegen)), False, None)]
            else:
                achse = {'X−': 'X', 'Y+': 'Y', 'SpnEn': 'Z'}[s]
                teile = [('Endschalter {}'.format(achse), True, None),
                         (' → {}'.format(vk.ANSCHLUSS[gegen][0]), False,
                          None)]
            t += spalten(y, s, uno, mit_marke(nr, teile))
        else:
            t.append(frei_linie(xa, y))
            t += spalten(y, s, uno, nur_text(RAND_FREI[s]))
    # Signal innen, GND aussen
    xs, ys = P(xi, RECHTS_Y[-1] + 2.4)
    xg = P(xa, 0)[0]
    t += [text(xs, ys + 4, 'S', 8.5, BLAU, 'middle', fett=True),
          text(xg, ys + 4, 'G', 8.5, BLAU, 'middle', fett=True)]
    return t


# ---- Beschriftung links, oben und unten ------------------------------------

def hinweis_links(y_mm, teile, x_ende=0.3, zweite=None, marke=None):
    """Text rechtsbuendig bis LI_X, Linie bis an die Platine (x_ende mm)."""
    py = P(0, y_mm)[1]
    t = [el('line', {'x1': f1(LI_X + 6), 'y1': f1(py),
                     'x2': f1(P(x_ende, 0)[0]), 'y2': f1(py),
                     'stroke': '#868e96', 'stroke-width': '1'}),
         vz.kreis(P(x_ende, 0)[0], py, 2.2, '#495057')]
    x = LI_X
    if marke:
        t += vz.marke(x, py + 3.6, marke, 'end')
        x -= badge_breite(marke) + 6
    t.append(zeile(x, py + 3.6, teile, 10.5, 'end'))
    if zweite:
        t.append(text(LI_X, py + 17.5, zweite, 9.5, GRAU, 'end'))
    return t


def beschriftung_links():
    t = []
    t += hinweis_links(LINKS_Y[0], [('EN/GND', True, None),
                                    (' offen lassen', False, None)],
                       zweite='GRBL schaltet die Treiber über D8')
    # STEP/DIR der vier Achsen: Klammer an der Kante
    ya, yb = LINKS_Y[1] - 0.9, LINKS_Y[4] + 0.9
    t.append(vz.linie([P(1.6, ya), P(0.8, ya), P(0.8, yb), P(1.6, yb)],
                      '#495057', 1.2))
    t += hinweis_links((LINKS_Y[1] + LINKS_Y[4]) / 2, [
        ('STEP/DIR', True, None), (' X, Y, Z, A: frei', False, GRAU)],
        x_ende=0.8, zweite='für externe Treiber (D2–D7)')
    t += hinweis_links(LINKS_Y[5], [('5V/GND', True, None),
                                    (' frei', False, GRAU)],
                       zweite='dasselbe 5 V wie oben rechts')
    t += hinweis_links(KLON_Y[1], [('Jumper Y', True, None),
                                   (': A klont Y (A.STP, A.DIR)', False,
                                    None)],
                       zweite='Reihen X und Z ohne Jumper')
    t += hinweis_links(KLON_Y[3], [('D12/D13', True, ROT),
                                   (' nicht stecken', False, ROT)],
                       zweite='D12 ist der Z-Endschalter')
    t += hinweis_links(HOHL[1] + HOHL[3] / 2, [
        ('Hohlbuchse des Uno', True, None), (' frei', False, GRAU)],
        x_ende=HOHL[0], zweite='der Uno läuft über USB')
    # W3 an der Schraubklemme: unten heraus, dann nach links
    (nr_p, f_p, farbe_p, gegen_p), = an('Shield +')
    (nr_m, f_m, farbe_m, gegen_m), = an('Shield −')
    for pol, ya, nr, farbe, gegen in (('−', 55.6, nr_m, farbe_m, gegen_m),
                                      ('+', 58.4, nr_p, farbe_p, gegen_p)):
        x = KLEMME_X[pol]
        weg = [P(x, KLEMME[3] - 0.5), P(x, ya), (LI_X + 6, P(0, ya)[1])]
        t += vz.draht(weg, farbe, b=2.4)
        py = P(0, ya)[1] + 3.6
        t += vz.marke(LI_X, py, nr, 'end')
        t.append(zeile(LI_X - badge_breite(nr) - 6, py, [
            ('Klemme {}'.format(pol), True, None),
            (' ← {} ({})'.format(vk.ANSCHLUSS[gegen][0], farbe), False,
             None)], 10.5, 'end'))
    t.append(text(LI_X, P(0, 58.4)[1] + 21, '24 V für die Treiber, '
                  'Polung am Aufdruck prüfen', 9.5, GRAU, 'end'))
    return t


def nach_oben(x_mm, y_mm, y_text, nr, teile, zweite=None, anker='start'):
    """Linie vom Bauteil nach oben ueber die Platine, Text daneben."""
    x, y = P(x_mm, y_mm)
    t = [el('line', {'x1': f1(x), 'y1': f1(y), 'x2': f1(x),
                     'y2': f1(y_text - 4), 'stroke': '#868e96',
                     'stroke-width': '1'}),
         vz.kreis(x, y, 2.2, '#495057')]
    t += beschriftung(x, y_text, nr, teile, zweite, anker)
    return t


def nach_unten(x_mm, y_mm, y_text, nr, teile, zweite=None):
    x, y = P(x_mm, y_mm)
    t = [el('line', {'x1': f1(x), 'y1': f1(y), 'x2': f1(x),
                     'y2': f1(y_text - 12), 'stroke': '#868e96',
                     'stroke-width': '1'}),
         vz.kreis(x, y, 2.2, '#495057')]
    t += beschriftung(x, y_text, nr, teile, zweite, 'start')
    return t


def beschriftung(x, y, nr, teile, zweite, anker):
    """Marke und Text an der Linie bei x; anker 'start': rechts davon,
    'end': links davon."""
    t = []
    if anker == 'start':
        xm = x + 6
        if nr:
            t += vz.marke(xm, y, nr)
            xm += badge_breite(nr) + 6
        t.append(zeile(xm, y, teile, 10.5))
        if zweite:
            t.append(text(x + 6, y + 14, zweite, 9.5, GRAU))
    else:
        xm = x - 6
        t.append(zeile(xm, y, teile, 10.5, 'end'))
        if nr:
            breit = sum(vz.breite(s, 10.5, fett) for s, fett, _ in teile)
            t += vz.marke(xm - breit - 6, y, nr, 'end')
        if zweite:
            t.append(text(x - 6, y + 14, zweite, 9.5, GRAU, 'end'))
    return t


def motoren():
    """Je Steckplatz Leitung und Motor: X und Y nach oben, Z und A nach
    unten."""
    t = []
    y_oben, y_unten = Y0 - 34, P(0, 57.6)[1]
    for achse in ('X', 'Y', 'Z', 'A'):
        x0, y0 = SOCKEL[achse]
        hx = x0 + MOTOR_DX
        lt = next(lt for lt in LTS if lt['adern'][0][2] ==
                  'Shield {} 2B·2A'.format(achse))
        teile = [('Motor {} '.format(achse), True, None),
                 ('→ {}'.format(lt['name']), False, None)]
        zweite = None
        if 'getauscht' in lt['adern'][0][0]:
            zweite = 'Schwarz und Blau getauscht: dreht gegen Y'
        elif achse == 'X':
            zweite = 'Schwarz oben an 2B'
        if achse in 'XY':
            t += nach_oben(hx, y0 + MOTOR_DY - R / 2 - 0.1, y_oben,
                           lt['nr'], teile, zweite)
        else:
            t += nach_unten(hx, y0 + MOTOR_DY + 3 * R + 2.0 + 2.9, y_unten,
                            lt['nr'], teile, zweite)
    return t


def oben_links():
    """USB des Uno und Reset-Taster: Linien nach oben."""
    y_text = Y0 - 34
    # die USB-Buchse gehoert zum Uno, nicht zum Shield: nur anzeigen
    nr, gegen = next((lt['nr'], b) for lt in LTS
                     for _, _, a, b in lt['adern'] if a == 'Uno USB')
    # Linie aus der Mitte der Oberkante: an der Ecke laeuft EN/GND vorbei
    t = nach_oben(USB[0] / 2, USB[1], y_text, nr,
                  [('USB-B des Uno', True, None),
                   (' → {}'.format(vk.ANSCHLUSS[gegen][0]), False, None)],
                  zweite='versorgt Uno, Shield-Logik und die 5 V',
                  anker='end')
    t += nach_oben(RESET[0], RESET[1] - 3.0, y_text, None,
                   [('RST', True, None), (' Reset-Taster', False, None)],
                   zweite='startet GRBL neu')
    return t


# ---- Legende und Hinweise --------------------------------------------------

def legende(y):
    t = [text(24, y, 'Zeichen', 12, BLAU, fett=True)]
    z = y + 22
    eintraege = [
        ('ader', 'Ader in ihrer Farbe aus der Anschlussliste'),
        ('dupont', 'Dupont-Gehäuse auf dem Stift'),
        ('jumper', 'Jumper (Steckbrücke)'),
        ('frei', 'freier Stift (gestrichelte Linie)'),
        ('treiber', 'Treiber TMC2209, durchsichtig gezeichnet'),
    ]
    for i, (art, s) in enumerate(eintraege):
        yy = z + 18 * i
        if art == 'ader':
            t += vz.draht([(28, yy - 4), (58, yy - 4)], 'gelb', b=2.2)
            t += vz.marke(64, yy, 'W9')
            t.append(text(64 + badge_breite('W9') + 8, yy, s + ', Nummer wie '
                          'in der Kabelliste', 10, TEXT))
            continue
        if art == 'dupont':
            t.append(vz.rechteck(36, yy - 12, 16, 16, DUPONT, '#000000', 0.6,
                                 rx=2))
        elif art == 'jumper':
            t.append(vz.rechteck(30, yy - 11, 28, 14, '#212529', '#000000',
                                 0.8, rx=3))
        elif art == 'frei':
            t.append(el('line', {'x1': '28', 'y1': f1(yy - 4), 'x2': '58',
                                 'y2': f1(yy - 4), 'stroke': FREI,
                                 'stroke-width': '1',
                                 'stroke-dasharray': '2 3'}))
        else:
            t.append(el('rect', {'x': '30', 'y': f1(yy - 13), 'width': '28',
                                 'height': '18', 'rx': '2',
                                 'fill': '#2b2f36', 'fill-opacity': '0.1',
                                 'stroke': '#2b2f36', 'stroke-width': '1',
                                 'stroke-dasharray': '4 3'}))
        t.append(text(64, yy, s, 10, TEXT))
    return t


def hinweise(x, y):
    t = [text(x, y, 'Hinweise', 12, BLAU, fett=True)]
    # Spannungsteiler an Abort und Vref aus Kabelliste und Leistungsrechnung
    teiler = {g: f for _, f, _, g in an('Shield Abort')}
    r1 = teiler['Wago +24 V'].split(' ', 1)[1]
    r2 = teiler['Wago GND'].split(' ', 1)[1]
    vref = min(ez.vref(ez.MOTOR_I, r) for r in ez.R_SENSE)
    zeilen = [
        [('Aufdruck aus GRBL 0.8: ', True, None),
         ('Z+/Z− (D11) ist unter GRBL 1.1 die Laser-PWM, SpnEn (D12) der '
          'Z-Endschalter.', False, None)],
        [('', False, None),
         ('X+/X− sind beide D9, Y+/Y− beide D10: je Achse nur ein '
          'Endschalter.', False, None)],
        [('Rechter Rand: ', True, None),
         ('innen das Signal (S), außen GND (G) [w] — vor dem Stecken '
          'messen (Prüfung D):', False, None)],
        [('', False, None),
         ('mit GRBL liegen an S von X−, Y+ und SpnEn etwa 5 V, G hat '
          'Durchgang zur Klemme −.', False, None)],
        [('W16 an Abort: ', True, None),
         ('{} von der Wago +24 V, {} an die Wago GND; ohne 24 V bricht '
          'GRBL ab.'.format(r1, r2), False, None)],
        [('Unter jedem Treiber: ', True, None),
         ('Jumper M0 + M1 (MS1 + MS2 = 1/16), M2 frei. Treiber mit EN zum '
          'EN-Aufdruck, Vref {} V.'.format(de(vref, 2)), False, None)],
        [('5V gibt es zweimal, ', True, None),
         ('beide am 5-V-Pin des Uno; W6 an den oben rechts, er liegt der '
          'Wago +5 V am nächsten.', False, None)] if not FUENF_V_FREI else
        [('5V gibt es zweimal, ', True, None),
         ('beide am 5-V-Pin des Uno und frei: W6 kommt vom 5-V-Wandler.',
          False, None)],
        [('Im Elektronikfach ', True, None),
         ('liegt das Shield wie in elektronikfach.svg gezeigt.', False,
          None)],
        [('Nur stromlos stecken. ', True, ROT),
         ('Einschalten: erst USB, dann 24 V (verkabelung.md).', False,
          None)],
    ]
    for i, teile in enumerate(zeilen):
        t.append(zeile(x, y + 22 + 15 * i, teile, 10))
    return t


def main():
    t = [text(24, 36, 'CNC Shield V3 — alle Anschlüsse und ihre Belegung',
              19, TEXT, fett=True),
         text(24, 58, 'Shield von oben wie in motoren-anschluss.svg: Reset '
              'oben links, Schraubklemme unten links, USB des Uno links. '
              'Maßstäblich (68,6 × 53,3 mm), Stifte im Raster 2,54 mm.', 11.5,
              GRAU),
         text(24, 76, 'Uno-Pins unter GRBL 1.1 (hardware-notizen.md). '
              'Nummern, Adern und Farben wie in der Kabelliste '
              '(verkabelung.md, W1–W17). Grau: frei.', 11.5, GRAU),
         text(24, 94, 'Lage der Stiftleisten nach Bestückungsdruck und '
              'Schaltplan des Protoneer V3.00 [w]; Treiber und Motorstecker '
              'am Shield abgelesen [v].', 11.5, GRAU)]
    t += platine()
    t += rechts()
    t += beschriftung_links()
    t += oben_links()
    t += motoren()
    y = P(0, 66.5)[1]
    t += legende(y)
    t += hinweise(470, y)
    # jeder Anschluss der Kabelliste am Shield muss im Bild sein
    soll = {a for lt in LTS for _, _, a, b in lt['adern'] for a in (a, b)
            if a.startswith('Shield')}
    fehlt = sorted(soll - GEZEICHNET)
    if fehlt:
        raise SystemExit('nicht gezeichnet: {}'.format(', '.join(fehlt)))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="{0}" height="{1}" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
