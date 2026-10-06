#!/usr/bin/env python3
"""Verkabelungsplan der Elektronik: jede Ader von Klemme zu Klemme.

Oben eine schematische Draufsicht mit den Kabeln K1-K11 und ihren Wegen
durch Kanal und Energieketten, darunter sechs Schritte in der Reihenfolge,
in der verdrahtet wird: Shield vorbereiten, Strom-Eingang mit Not-Aus,
24 V verteilen, Motoren, Endschalter, Laser. Jede Ader hat in den
Wago-Klemmen einen festen, nummerierten Platz. Die Schritte sind
kreuzungsfrei gezeichnet; die einzige Kreuzung ist die getauschte Spule
am zweiten Y-Motor, und die ist Absicht.

Pins nach GRBL 1.1 (docs/hardware-notizen.md), Farben wie im Anschlussplan
(tools/anschluss_zeichnen.py), Kabellaengen aus tools/elektronik_zeichnen.py,
damit alle Zeichnungen dieselben Zahlen zeigen.

    python3 tools/verkabelung_zeichnen.py   ->  docs/elektronik-verkabelung.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import (el, f1, text, de,     # noqa: E402
                              TEXT, GRAU, BLAU, ROT)
from anschluss_zeichnen import (P24, P12, MASSE,    # noqa: E402
                                SIGNAL, P5, MOTOR)
import elektronik_zeichnen as ez                    # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-verkabelung.svg')

W = 1240                        # Breite der Zeichnung
RX = 24                         # Rand links und rechts
PB, PH, LUECKE = 588, 340, 16   # Schritt-Felder: Breite, Hoehe, Abstand
UEB_H = 480                     # Hoehe der Uebersicht
FILL, RAND = '#f4f6f9', '#8c939e'
SHIELD = ('#eef4fb', BLAU)
GEH_FILL, GEH_RAND = '#fdf6ee', '#c2621b'   # Gehaeuse wie im Anschlussplan
KABELWEG = ez.KABEL                          # wie in der Platz-Zeichnung
SPULE2 = '#74b816'              # zweite Motorspule, heller als MOTOR
HEBEL, HEBEL_RAND = '#f08c00', '#c46a00'     # Hebel der Wago 221
GELB, GELB_RAND = '#ffd43b', '#b08900'
STIFT = '#495057'


# ---- Bausteine -----------------------------------------------------------

def breite(s, gr, fett=False):
    """Geschaetzte Textbreite in px (Inter/Helvetica)."""
    return len(s) * gr * (0.6 if fett else 0.55)


def gruppe(x, y, inhalt):
    """Inhalt in lokalen Koordinaten, verschoben nach (x, y)."""
    return el('g', {'transform': 'translate({},{})'.format(f1(x), f1(y))},
              '\n'.join(inhalt))


def rechteck(x, y, b, h, fill=FILL, rand=RAND, strich_b=1.0, rx=5,
             strich=None):
    return el('rect', {'x': f1(x), 'y': f1(y), 'width': f1(b),
                       'height': f1(h), 'rx': rx, 'fill': fill,
                       'stroke': rand, 'stroke-width': strich_b,
                       'stroke-dasharray': strich})


def kreis(x, y, r, fill, rand='none', strich_b=1.0):
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': f1(r), 'fill': fill,
                         'stroke': rand, 'stroke-width': strich_b})


def linie(punkte, farbe, b=1.0, strich=None):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': b,
        'stroke-dasharray': strich, 'stroke-linejoin': 'round'})


def draht(punkte, farbe, b=2.2):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': b,
        'stroke-linejoin': 'round', 'stroke-linecap': 'round'})


def zeilen(x, y, liste, gr=11.0, farbe=TEXT, abstand=14.0, anker='start',
           fett_erste=False):
    return [text(x, y + abstand * i, s, gr, farbe, anker,
                 fett=fett_erste and i == 0)
            for i, s in enumerate(liste) if s]


def kasten(x, y, b, h, liste, fill=FILL, rand=RAND, fett=1, gr=12.0,
           abstand=15.0, dx=9.0, dy=19.0, strich=None):
    """Kasten mit Textzeilen; die ersten `fett` Zeilen fett und dunkel."""
    t = [rechteck(x, y, b, h, fill, rand, strich=strich)]
    for i, s in enumerate(liste):
        if s:
            t.append(text(x + dx, y + dy + abstand * i, s,
                          gr if i < fett else gr - 1.0,
                          TEXT if i < fett else GRAU, fett=i < fett))
    return t


def klemme(x, y, s=None, seite='r', gr=10.5, farbe=TEXT, fett=False):
    """Anschlusspunkt, Beschriftung rechts, links, oben oder unten."""
    t = [kreis(x, y, 3.3, '#ffffff', TEXT, 1.2)]
    if s:
        dx, dy, anker = {'r': (7, 4, 'start'), 'l': (-7, 4, 'end'),
                         'o': (0, -8, 'middle'),
                         'u': (0, 15, 'middle')}[seite]
        t.append(text(x + dx, y + dy, s, gr, farbe, anker, fett, halo=True))
    return t


def kabelnr(x, y, nr, anker='start'):
    """Kabelnummer als Marke (K3 ...); y ist die Grundlinie."""
    b = 10.0 + 7.0 * len(nr)
    x0 = {'start': x, 'end': x - b, 'middle': x - b / 2}[anker]
    return [rechteck(x0, y - 11, b, 15, KABELWEG, KABELWEG, rx=7.5),
            text(x0 + b / 2, y + 0.5, nr, 10.5, '#ffffff', 'middle',
                 fett=True)]


def warndreieck(x, y):
    """Gelbes Warndreieck, (x, y) = linke obere Ecke, 17 x 15 px."""
    return [el('polygon', {
        'points': '{},{} {},{} {},{}'.format(f1(x), f1(y + 15),
                                             f1(x + 8.5), f1(y),
                                             f1(x + 17), f1(y + 15)),
        'fill': GELB, 'stroke': GELB_RAND, 'stroke-width': '1',
        'stroke-linejoin': 'round'}),
        text(x + 8.5, y + 13.2, '!', 10.5, TEXT, 'middle', fett=True)]


def warnung(x, y, liste, gr=11.0, abstand=14.0, farbe=TEXT):
    """Warndreieck bei (x, y), Text rechts daneben (erste Zeile fett)."""
    return warndreieck(x, y) + zeilen(x + 23, y + 12, liste, gr, farbe,
                                      abstand, fett_erste=True)


def wago(xo, yo, farbe, seite, teilung=32.0, tiefe=40.0, rueckwaerts=False):
    """Wago 221-415 von oben mit fuenf nummerierten Plaetzen. (xo, yo) ist
    die erste Oeffnung (links bzw. oben), seite sagt, von wo die Adern
    kommen: 'u' (unten), 'o' (oben) oder 'l' (links); rueckwaerts zaehlt
    von der anderen Seite. Liefert (svg, Oeffnungen nach Platz 1-5)."""
    t, auf = [], []
    if seite in 'uo':
        x, b, h = xo - teilung / 2, teilung * 5, tiefe
        y = yo - tiefe if seite == 'u' else yo
    else:
        x, y, b, h = xo, yo - teilung / 2, tiefe, teilung * 5
    t.append(rechteck(x, y, b, h, '#eef1f4', farbe, 1.6, rx=4))
    for i in range(5):
        if seite in 'uo':
            px, py = xo + teilung * i, yo
            hy = y + 5 if seite == 'u' else y + h - 27
            t.append(rechteck(px - 8, hy, 16, 22, HEBEL, HEBEL_RAND, 0.8,
                              rx=2))
            t.append(text(px, hy + 15.5, str(5 - i if rueckwaerts else i + 1),
                          10.5, '#ffffff', 'middle', fett=True))
            oy = yo - 7 if seite == 'u' else yo + 1
            t.append(rechteck(px - 5, oy, 10, 6, STIFT, STIFT, 0.5, rx=1.5))
        else:
            px, py = xo, yo + teilung * i
            hx = x + b - 27
            t.append(rechteck(hx, py - 8, 22, 16, HEBEL, HEBEL_RAND, 0.8,
                              rx=2))
            t.append(text(hx + 11, py + 4,
                          str(5 - i if rueckwaerts else i + 1), 10.5,
                          '#ffffff', 'middle', fett=True))
            t.append(rechteck(xo + 1, py - 5, 6, 10, STIFT, STIFT, 0.5,
                              rx=1.5))
        auf.append((px, py))
    return t, auf[::-1] if rueckwaerts else auf


def stift(x, y):
    """Einzelner Stift einer Stiftleiste (Draufsicht)."""
    return rechteck(x - 4.5, y - 4.5, 9, 9, '#adb5bd', STIFT, 0.8, rx=1)


def jumper(x0, y0, x1, y1):
    """Schwarze Steckbruecke ueber zwei Stifte."""
    b, h = abs(x1 - x0) + 14, abs(y1 - y0) + 14
    return rechteck(min(x0, x1) - 7, min(y0, y1) - 7, b, h, '#212529',
                    '#000000', 0.8, rx=3)


def motor_symbol(x, y, a=34):
    """NEMA 17 von vorn: Flansch, Zentrierbund, Welle."""
    return [rechteck(x, y, a, a, '#ced4da', STIFT, 1.0, rx=4),
            kreis(x + a / 2, y + a / 2, a * 0.28, '#e9ecef', STIFT, 0.8),
            kreis(x + a / 2, y + a / 2, 2.6, STIFT)]


def schrittmarke(x, y, nr):
    """Kleiner Verweis auf einen anderen Schritt: blaue Nummer im Kreis."""
    return [kreis(x, y, 8.5, BLAU),
            text(x, y + 4, str(nr), 10.5, '#ffffff', 'middle', fett=True)]


def feld(nr, titel, unter, inhalt, b=PB, h=PH):
    """Rahmen eines Schritts: Nummer, Titel, rechts eine Kurzangabe."""
    t = [rechteck(0, 0, b, h, '#ffffff', '#d0d7de', 1.0, rx=8),
         kreis(22, 23, 13, BLAU),
         text(22, 28, str(nr), 14, '#ffffff', 'middle', fett=True),
         text(44, 28.5, titel, 14.5, TEXT, fett=True)]
    if unter:
        t.append(text(b - 14, 28, unter, 11, GRAU, 'end'))
    return t + inhalt


# ---- Schritt 1: Shield vorbereiten ---------------------------------------

def schritt_shield():
    t = [text(16, 62, 'Mikroschritt-Jumper', 12, TEXT, fett=True),
         text(16, 77, 'unter jedem Treiber: X, Y, Z und A', 10.5, GRAU)]
    # 3 x 2 Stifte, MS1 und MS2 gesteckt
    bx, by = 28, 96
    t.append(rechteck(bx - 12, by - 12, 132, 60, SHIELD[0], '#9bb7d4', 1,
                      rx=4))
    for i, (name, alt, steckt) in enumerate((('MS1', 'M0', True),
                                             ('MS2', 'M1', True),
                                             ('MS3', 'M2', False))):
        cx = bx + 8 + 46 * i
        t += [stift(cx, by + 4), stift(cx, by + 28)]
        if steckt:
            t.append(jumper(cx, by + 4, cx, by + 28))
        t += [text(cx, by + 66, name, 11, TEXT, 'middle', fett=True),
              text(cx, by + 79, '(' + alt + ')', 10, GRAU, 'middle'),
              text(cx, by + 94, 'stecken' if steckt else 'frei', 10.5,
                   TEXT if steckt else ROT, 'middle', fett=not steckt)]
    t.append(text(166, 112, '= 1/16 Schritt', 12, TEXT, fett=True))
    t += zeilen(166, 128, ['TMC2209 ohne UART,', 'intern auf 1/256',
                           'interpoliert'], 10.5, GRAU)

    # Treiber richtig herum
    t.append(text(16, 222, 'Treiber richtig herum stecken', 12, TEXT,
                  fett=True))
    dx, dy = 22, 234
    t.append(rechteck(dx, dy, 124, 56, SHIELD[0], '#9bb7d4', 1, rx=3))
    t.append(rechteck(dx + 22, dy + 6, 94, 44, '#2b2f36', '#000000', 0.8,
                      rx=2))
    for k in range(7):                       # Kuehlkoerper
        x = dx + 44 + 9 * k
        t.append(linie([(x, dy + 12), (x, dy + 44)], '#868e96', 2.2))
    t += [kreis(dx + 29, dy + 13, 3.4, '#fa5252'),
          text(dx + 4, dy + 17, 'EN', 9.5, BLAU, fett=True),
          text(dx + 36, dy + 17, 'EN', 8.5, '#f8f9fa', fett=True)]
    t += zeilen(162, 248, ['EN-Pin des Treibers', 'an den EN-Aufdruck.',
                           'Verkehrt herum ist', 'der Treiber hin.'], 10.5,
                GRAU)
    t += zeilen(16, 312, ['Strom am Poti: ≈ 70 % des Motornennstroms',
                          '(Formel des Moduls, je nach Messwiderstand).'],
                10.5, GRAU)

    # A klont Y
    ax = 310
    t += [text(ax, 62, 'A klont Y: zwei Jumper', 12, TEXT, fett=True),
          text(ax, 77, 'neben dem A-Treiber (zweiter Y-Motor)', 10.5, GRAU)]
    spalten = (('X', 384), ('Y', 428), ('Z', 472), ('D12/D13', 530))
    reihen = (('A.STEP', 112), ('A.DIR', 144))
    t.append(rechteck(ax + 50, 90, 214, 74, SHIELD[0], '#9bb7d4', 1, rx=4))
    for s, x in spalten:
        t.append(text(x, 102, s, 10.5, ROT if s == 'D12/D13' else TEXT,
                      'middle', fett=True))
    for s, y in reihen:
        t.append(text(ax, y + 4, s, 10.5, TEXT, fett=True))
        for sp, x in spalten:
            t += [stift(x - 8, y), stift(x + 8, y)]
            if sp == 'Y':
                t.append(jumper(x - 8, y, x + 8, y))
            if sp == 'D12/D13':
                t += [linie([(x - 15, y - 8), (x + 15, y + 8)], ROT, 2),
                      linie([(x - 15, y + 8), (x + 15, y - 8)], ROT, 2)]
    t += zeilen(ax, 186, ['Gesteckt: A.STEP ↔ Y.STEP und A.DIR ↔ Y.DIR.',
                          'Aufdruck je nach Shield etwas anders',
                          '(A.STP, Y.STP …).'], 10.5, GRAU)
    t += warnung(ax, 236, ['Nie auf D12/D13 stecken:',
                           'D12 ist bei GRBL 1.1 der',
                           'Z-Endschalter (Schritt 5).'], 10.5, 13.5)
    t += warnung(ax, 288, ['Y und A gleich bestücken:',
                           'gleiche Treiber, Jumper und Ströme.'], 10.5,
                 13.5)
    return feld(1, 'Shield vorbereiten', 'vor dem Verdrahten, stromlos', t)


# ---- Schritt 2: Strom-Eingang und Not-Aus --------------------------------

def schritt_strom(lk):
    t = []
    wand = 154
    t += [linie([(wand, 44), (wand, 226)], GEH_RAND, 1.4, '6 4'),
          text(wand - 6, 56, 'außen', 10, GRAU, 'end'),
          text(wand + 6, 56, 'im Gehäuse (Rückwand)', 10, GEH_RAND)]
    # Steckernetzteil mit Hohlstecker
    t += kasten(14, 66, 98, 64, ['Netzteil', '24 V / 3 A', 'Stecker-NT'])
    t += [draht([(112, 98), (140, 98)], '#495057', 5),
          rechteck(140, 92, 14, 12, '#868e96', STIFT, 0.8, rx=2)]
    t += kabelnr(14, 152, 'K1')
    t += zeilen(42, 152, ['Hohlstecker 5,5 × 2,1'], 10.5, GRAU)
    # Einbaubuchse, Schalter
    t += kasten(158, 66, 74, 64, ['Buchse', '5,5 × 2,1', 'Einbau'])
    t += kasten(262, 66, 72, 42, ['Schalter', 'EIN/AUS'])
    # Not-Aus vorn an der Maschine
    t.append(rechteck(356, 46, 122, 106, '#ffffff', P24, 1.0, rx=6,
                      strich='5 3'))
    t += kasten(364, 66, 106, 42, ['Not-Aus', 'Öffner (NC)'], '#fff4f4', P24)
    t += [kreis(452, 81, 10, GELB, GELB_RAND), kreis(452, 81, 6.5, '#e03131')]
    t += kabelnr(364, 128, 'K2')
    t += zeilen(394, 128, ['2-adrig, {} m'.format(lk['notaus'])], 10.5, GRAU)
    t += zeilen(417, 145, ['vorn an der Maschine'], 10, P24, anker='middle')
    # Wago-Klemmen, Adern von links
    wp, op = wago(526, 86, P24, 'l', 22, 46, rueckwaerts=True)
    wm, om = wago(526, 214, MASSE, 'l', 22, 46, rueckwaerts=True)
    t += wp + wm
    t += [text(549, 66, '+24 V', 11, P24, 'middle', fett=True),
          text(549, 198, 'GND', 11, MASSE, 'middle', fett=True)]
    # Adern
    t += [draht([(232, 86), (262, 86)], P24),
          draht([(334, 86), (364, 86)], P24),
          draht([(470, 86), op[4]], P24),
          draht([(232, 116), (248, 116), (248, om[4][1]), om[4]], MASSE)]
    for x, y in ((232, 86), (232, 116), (262, 86), (334, 86), (364, 86),
                 (470, 86)):
        t += klemme(x, y)
    t += [text(238, 80, '+', 12, P24, fett=True),
          text(238, 132, '−', 12, MASSE, fett=True)]
    # Plaetze 1-3 gehen zu Schritt 3, Platz 4 bleibt frei
    for o in (op, om):
        t += [linie([(o[0][0] - 12, o[0][1]), (o[2][0] - 12, o[2][1])],
                    GRAU, 1.0)]
        t += schrittmarke(o[1][0] - 24, o[1][1], 3)
        t.append(text(o[3][0] - 8, o[3][1] + 4, 'frei', 10, GRAU, 'end'))
    # Hinweise
    t += warnung(14, 240, ['Polung: Symbol auf dem Netzteil prüfen '
                           '(Mitte = +).'], 11)
    t += zeilen(14, 274, [
        'Not-Aus: Öffner — nicht gedrückt Durchgang (Multimeter).',
        'Gedrückt sind Motoren, Laser und Lüfter stromlos;',
        'der Uno läuft über USB weiter.',
        'K2 läuft mit dem Y-Motor rechts nach vorn (Übersicht).'], 11, TEXT)
    return feld(2, 'Strom-Eingang und Not-Aus',
                'Adern im Gehäuse: 0,5 mm²', t)


# ---- Schritt 3: 24 V verteilen -------------------------------------------

def verbraucher(x, y, plus, minus, liste, b=152, h=92, fill=FILL,
                rand=RAND):
    """Verbraucher mit + oben links, − unten links (Klemmen am Rand)."""
    t = [rechteck(x, y, b, h, fill, rand)]
    t += [text(x + 8, y + 22, plus, 11, P24, fett=True),
          text(x + 8, y + 78, minus, 11, MASSE, fett=True)]
    t += [text(x + 40, y + 22, liste[0], 12, TEXT, fett=True)]
    t += zeilen(x + 40, y + 40, liste[1:], 11, GRAU, 15)
    return t


def schritt_verteilen():
    t = []
    wp, op = wago(230, 88, P24, 'u')
    wm, om = wago(230, 270, MASSE, 'o')
    t += wp + wm
    t += [text(382, 72, 'Wago +24 V', 12, P24, fett=True),
          text(382, 296, 'Wago GND', 12, MASSE, fett=True)]
    # Verbraucher: Shield, Wandler, Luefter
    vx = (24, 216, 416)
    t += verbraucher(vx[0], 140, '+', '−', ['CNC Shield V3',
                                            'Schraubklemme', '(12–36 V)'],
                     fill=SHIELD[0], rand=SHIELD[1])
    t += verbraucher(vx[1], 140, 'IN+', 'IN−', ['Wandler', '24 → 12 V',
                                               'OUT: Schritt 6'],
                     fill='#fff7ec', rand=P12)
    t += verbraucher(vx[2], 140, '+', '−', ['Lüfter', '24 V, im Deckel',
                                           'rot +, schwarz −'])
    # +24 V von oben: Platz 1 -> Shield, 2 -> Wandler, 3 -> Luefter
    t += [draht([op[0], (op[0][0], 108), (12, 108), (12, 158),
                 (vx[0], 158)], P24),
          draht([op[1], (op[1][0], 122), (204, 122), (204, 158),
                 (vx[1], 158)], P24),
          draht([op[2], (op[2][0], 122), (404, 122), (404, 158),
                 (vx[2], 158)], P24),
          draht([op[4], (op[4][0], 100), (446, 100)], P24)]
    # GND von unten, gespiegelt
    t += [draht([om[0], (om[0][0], 254), (12, 254), (12, 214),
                 (vx[0], 214)], MASSE),
          draht([om[1], (om[1][0], 240), (204, 240), (204, 214),
                 (vx[1], 214)], MASSE),
          draht([om[2], (om[2][0], 240), (404, 240), (404, 214),
                 (vx[2], 214)], MASSE),
          draht([om[4], (om[4][0], 258), (446, 258)], MASSE)]
    for x in vx:
        t += klemme(x, 158) + klemme(x, 214)
    t += klemme(446, 100) + klemme(446, 258)
    t += [text(452, 104, 'vom Not-Aus (Schritt 2)', 10.5, GRAU),
          text(452, 262, 'von der Buchse (Schritt 2)', 10.5, GRAU),
          text(op[3][0], 104, 'frei', 10, GRAU, 'middle'),
          text(om[3][0], 262, 'frei', 10, GRAU, 'middle')]
    t += warnung(14, 50, ['Polung an der Shield-',
                          'Klemme prüfen: verpolt',
                          'sind die Treiber hin.'], 10.5, 13.5)
    t += zeilen(14, 282, ['Wago: 11 mm abisolieren,',
                          'Ader bis zum Anschlag,',
                          'dann Hebel zu.'], 10.5, GRAU, 13.5)
    t += zeilen(452, 290, ['Lüfter bläst nach',
                           'unten auf die Treiber.'], 10.5, GRAU, 13.5)
    return feld(3, '24 V verteilen', 'Wago-Plätze 1–3, Platz 5 = Einspeisung',
                t)


# ---- Schritt 4: Motoren --------------------------------------------------

def schritt_motoren(lk):
    t = [rechteck(14, 46, 172, 238, SHIELD[0], SHIELD[1]),
         text(24, 66, 'CNC Shield V3', 12, TEXT, fett=True)]
    motoren = (('X', 'X-Motor', 'K3', lk['X-Motor'], ''),
               ('Y', 'Y-Motor links', 'K4', lk['Y-Motor links'], ''),
               ('Z', 'Z-Motor', 'K5', lk['Z-Motor'], ''),
               ('A', 'Y-Motor rechts', 'K6', lk['Y-Motor rechts'],
                'klont Y'))
    xs, xm = 186, 392
    for i, (achse, name, k, m, zusatz) in enumerate(motoren):
        g = 86 + 52 * i
        pins = [g, g + 11, g + 22, g + 33]
        t += [text(26, g + 22, achse, 17, BLAU, fett=True),
              text(46, g + 21, 'Treiber ' + achse, 10.5, GRAU)]
        if zusatz:
            t.append(text(46, g + 34, zusatz + ' (Schritt 1)', 10, GRAU))
        for p, s in zip(pins, ('2B', '2A', '1A', '1B')):
            t.append(text(xs - 8, p + 3.5, s, 9.5, GRAU, 'end'))
        # Motor
        t += [rechteck(xm, g - 6, 182, 46, FILL, RAND)]
        t += motor_symbol(xm + 8, g + 0)
        t += [text(xm + 52, g + 13, name, 12, TEXT, fett=True)]
        t += kabelnr(xm + 52, g + 31, k)
        t.append(text(xm + 52 + 10 + 7 * len(k) + 6, g + 31,
                      '{} m, 4-adrig'.format(m), 10.5, GRAU))
        # Adern: 2B, 2A = Spule 2, 1A, 1B = Spule 1
        farben = (SPULE2, SPULE2, MOTOR, MOTOR)
        if achse == 'A':
            t += [draht([(xs, pins[0]), (xm, pins[0])], farben[0]),
                  draht([(xs, pins[1]), (xm, pins[1])], farben[1]),
                  draht([(xs, pins[2]), (262, pins[2]), (292, pins[3]),
                         (xm, pins[3])], MOTOR),
                  draht([(xs, pins[3]), (262, pins[3]), (292, pins[2]),
                         (xm, pins[2])], MOTOR)]
        else:
            for p, f in zip(pins, farben):
                t.append(draht([(xs, p), (xm, p)], f))
        for p in pins:
            t += klemme(xs, p) + klemme(xm, p)
    # Spulen am ersten Motor benannt
    g = 86
    t += [text(289, g + 9, 'Spule 2', 10, '#5c940d', 'middle', fett=True,
               halo=True),
          text(289, g + 31, 'Spule 1', 10, MOTOR, 'middle', fett=True,
               halo=True)]
    t += warnung(196, 280, ['1A ↔ 1B getauscht: dreht gegenläufig'], 10.5)
    t += zeilen(219, 306, ['(oder den Stecker um 180° drehen)'], 10.5, GRAU)
    t += zeilen(14, 302, [
        'Spule finden: Multimeter auf Ω —',
        'wenige Ω = zwei Adern einer Spule.',
        'Nie unter Spannung stecken.'], 10.5, GRAU, 13.5)
    return feld(4, 'Motoren', 'Shield: Dupont 4-polig · Motor: meist '
                'JST-PH 6-polig', t)


# ---- Schritt 5: Endschalter ----------------------------------------------

def schritt_endschalter(lk):
    t = [rechteck(14, 44, 560, 66, SHIELD[0], SHIELD[1]),
         text(24, 62, 'CNC Shield V3 — Eingänge', 12, TEXT, fett=True),
         text(564, 62, 'Z+ / Z− (D11) = Laser: hier nichts!', 10.5, ROT,
              'end', fett=True)]
    sensoren = (('X-Endschalter', 'X+ (D9)', 'K7', lk['X-Endschalter'], 44),
                ('Y-Endschalter', 'Y+ (D10)', 'K8', lk['Y-Endschalter'],
                 224),
                ('Z-Endschalter', 'SpnEn (D12)', 'K9', lk['Z-Endschalter'],
                 404))
    wo, oo = wago(230, 282, P5, 'o', 32, 36)
    t += wo
    t.append(text(382, 306, 'Wago +5 V', 12, P5, fett=True))
    ys, ye = 110, 166                 # Unterkante Shield, Oberkante Sensor
    # 5 V vom Shield in Platz 5
    x5 = 562
    t += [text(x5, 100, '5V', 10, TEXT, 'middle', fett=True),
          draht([(x5, ys), (x5, 272), (oo[4][0], 272), oo[4]], P5)]
    ebenen = (258, 246, 240)          # Hoehe der VCC-Adern unten
    for i, (name, eingang, k, m, bx) in enumerate(sensoren):
        vcc, gnd, d0 = bx + 24, bx + 60, bx + 96
        # Shield-Stifte
        t += [text((gnd + d0) / 2, 84, eingang, 10.5, BLAU, 'middle',
                   fett=True),
              text(gnd, 100, 'GND', 9.5, GRAU, 'middle'),
              text(d0, 100, 'S', 9.5, GRAU, 'middle')]
        # Sensor
        t += [rechteck(bx, ye, 140, 64, FILL, RAND),
              text(vcc, ye + 16, 'VCC', 9.5, GRAU, 'middle'),
              text(gnd, ye + 16, 'GND', 9.5, GRAU, 'middle'),
              text(d0, ye + 16, 'D0', 9.5, GRAU, 'middle'),
              text(bx + 10, ye + 36, name, 12, TEXT, fett=True)]
        t += kabelnr(bx + 10, ye + 55, k)
        t.append(text(bx + 10 + 10 + 7 * len(k) + 6, ye + 55,
                      '{} m, 3-adrig'.format(m), 10.5, GRAU))
        # Adern: GND und D0 gerade hoch, VCC links herum nach unten
        ziel = oo[i]
        t += [draht([(gnd, ye), (gnd, ys)], MASSE),
              draht([(d0, ye), (d0, ys)], SIGNAL),
              draht([(vcc, ye), (vcc, ye - 14), (bx - 12, ye - 14),
                     (bx - 12, ebenen[i]), (ziel[0], ebenen[i]), ziel],
                    P5)]
        t += klemme(gnd, ys) + klemme(d0, ys) + klemme(gnd, ye) + \
            klemme(d0, ye) + klemme(vcc, ye)
    t += klemme(x5, ys)
    t.append(text(oo[3][0], 276, 'frei', 10, GRAU, 'middle'))
    t += zeilen(14, 288, ['X+ = X− (D9), Y+ = Y− (D10):',
                          'je ein Stift, GND daneben.'], 10.5, GRAU, 13.5)
    t += zeilen(460, 292, ['Test: GRBL ? zeigt Pn:X',
                           'nur, solange die Gabel',
                           'unterbrochen ist ($5).'], 10.5, GRAU, 13.5)
    return feld(5, 'Endschalter (Gabellichtschranken LM393)', '', t)


# ---- Schritt 6: Laser ----------------------------------------------------

def schritt_laser(lk):
    t = kasten(14, 50, 182, 96, ['Abwärtswandler', '24 → 12 V, ≥ 3 A',
                                 'IN aus Schritt 3', 'Poti: OUT-Spannung'],
               '#fff7ec', P12)
    t += [text(188, 80, 'OUT+', 10.5, P12, 'end', fett=True),
          text(188, 120, 'OUT−', 10.5, MASSE, 'end', fett=True)]
    t += kasten(14, 214, 182, 58, ['CNC Shield V3', 'Z+ (D11): Laser-PWM'],
                SHIELD[0], SHIELD[1])
    t.append(text(188, 254, 'S', 10.5, SIGNAL, 'end', fett=True))
    # Adern zum Kabel K10
    k0, k1 = 270, 400
    t += [draht([(196, 76), (238, 76), (238, 152), (k0, 152)], P12),
          draht([(196, 116), (226, 116), (226, 166), (k0, 166)], MASSE),
          draht([(196, 250), (250, 250), (250, 180), (k0, 180)], SIGNAL)]
    t += [rechteck(k0, 140, k1 - k0, 52, '#e9ecef', '#868e96', 1.2, rx=12)]
    t += [draht([(k0, 152), (k1 + 30, 152)], P12),
          draht([(k0, 166), (k1 + 30, 166)], MASSE),
          draht([(k0, 180), (k1 + 30, 180)], SIGNAL)]
    t += kabelnr(k0, 130, 'K10')
    t += [text(k0 + 38, 130, '3-adrig, {} m'.format(
        lk['Laser (12 V + PWM)']), 10.5, GRAU),
        text(k0, 208, 'durch Y- und X-Kette', 10.5, GRAU)]
    # XH-Stecker und Laser
    t += [rechteck(k1, 140, 16, 52, '#f8f9fa', STIFT, 1.0, rx=2),
          text(k1 + 8, 206, 'XH2.54', 10, GRAU, 'middle')]
    t += kasten(430, 64, 144, 186, ['Laser', 'LASER TREE 4 W',
                                    '12 V · 1,6 A'], '#eef6ff', SIGNAL,
                dy=20)
    for y, s, f in ((152, '12 V', P12), (166, 'GND', MASSE),
                    (180, 'PWM', SIGNAL)):
        t.append(text(440, y + 4, s, 10.5, f, fett=True))
    lx, ly = 500, 130                # Lasermodul: Kuehlkoerper, Linse
    t.append(rechteck(lx, ly, 56, 74, '#495057', '#212529', 1, rx=3))
    for k in range(6):
        y = ly + 8 + 11 * k
        t.append(linie([(lx + 6, y), (lx + 50, y)], '#adb5bd', 2))
    t += [el('polygon', {'points': '{},{} {},{} {},{} {},{}'.format(
        lx + 16, ly + 74, lx + 40, ly + 74, lx + 34, ly + 86, lx + 22,
        ly + 86), 'fill': '#868e96'}),
        linie([(lx + 28, ly + 88), (lx + 28, ly + 112)], '#4dabf7', 3)]
    for y in (76, 116, 250):
        t += klemme(196, y)
    for y in (152, 166, 180):
        t += klemme(k1 + 8, y)
    t += zeilen(14, 164, ['Gemeinsames GND: Wandler',
                          'mit gemeinsamem Minus',
                          '(üblich). Sonst OUT−',
                          'zusätzlich an Wago GND 4.'], 10.5, GRAU, 13.5)
    t += zeilen(14, 296, ['GRBL: $32=1 (Lasermodus),',
                          '$30=1000 (S-Maximum)'], 10.5, GRAU, 13.5)
    t += warnung(244, 258, ['Wandler zuerst ohne Laser einstellen:'], 11)
    t += [text(267, 284, '1', 10.5, BLAU, fett=True),
          text(267, 312, '2', 10.5, BLAU, fett=True)]
    t += zeilen(280, 284, [
        'einschalten, an OUT+ / OUT− messen,',
        'Poti auf 12,0 V (fester Wandler: nur messen);',
        'ausschalten, Laser anstecken — Pins am',
        'Aufdruck der Laserplatine prüfen.'], 10.5, TEXT, 14)
    return feld(6, 'Laser — zuletzt', '', t)


# ---- Uebersicht: Kabelwege -----------------------------------------------

def uebersicht(lk):
    t = [rechteck(0, 0, W - 2 * RX, UEB_H, '#ffffff', '#d0d7de', 1.0, rx=8),
         text(16, 28, 'Übersicht — welches Kabel wohin', 14.5, TEXT,
              fett=True),
         text(16, 46, 'Draufsicht, schematisch: hinten oben, vorn unten. '
              'Maßstäblich: elektronik-platz.svg', 11, GRAU)]
    px, cx, yh = 0.55, 330.0, 100.0      # px/mm, Mitte, hinteres Ende

    def X(mm):
        return cx + mm * px

    def Y(mm):                       # ab hinterem Ende der 2040, nach vorn
        return yh + mm * px

    def quader(x0, x1, y0, y1, fill, rand, b=1.0, rx=2):
        return rechteck(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0), fill,
                        rand, b, rx=rx)

    profil = ('#e9ecef', '#868e96')
    # Rahmen
    t += [quader(-300, 300, 145, 165, *profil),
          quader(-300, 300, 545, 565, *profil),
          quader(-267, -247, 0, 600, *profil),
          quader(247, 267, 0, 600, *profil)]
    # Gehaeuse hinter dem hinteren 2060
    t += [quader(-205, -45, 37, 128, GEH_FILL, GEH_RAND, 1.4, rx=3),
          text(X(-125), Y(78), 'Gehäuse', 11, GEH_RAND, 'middle', fett=True),
          text(X(-125), Y(96), 'Uno + Shield', 9.5, GEH_RAND, 'middle')]
    # Ketten
    kette = ('#ced4da', '#495057')
    t += [quader(-287, -273, 200, 355, *kette, rx=3),
          quader(0, 215, 330, 345, *kette, rx=3)]
    # Portal, Schlitten, Motoren, Toolhead
    t += [quader(-250, 250, 345, 365, *profil),
          quader(-287, -227, 320, 390, '#dbe4ef', '#6b84a3'),
          quader(227, 287, 320, 390, '#dbe4ef', '#6b84a3'),
          quader(-25, 25, 365, 425, '#dbe4ef', '#2f5d92'),
          quader(-225, -183, 318, 360, '#ced4da', STIFT),
          quader(-278, -236, 606, 648, '#ced4da', STIFT),
          quader(236, 278, 606, 648, '#ced4da', STIFT)]
    # Kabelwege
    weg = dict(farbe=KABELWEG, b=2.0, strich='6 3')
    xl = X(-300)                                    # links aussen
    xr = X(285)                                     # rechts aussen
    ykanal = Y(137)
    t += [linie([(X(-205), Y(90)), (xl, Y(90)), (xl, Y(627)),
                 (X(-278), Y(627))], **weg),
          linie([(xl, Y(210)), (X(-287), Y(210))], **weg),
          linie([(X(-227), Y(338)), (X(-195), Y(338))], **weg),
          linie([(X(-183), Y(338)), (X(0), Y(338))], **weg),
          linie([(X(-160), Y(338)), (X(-160), Y(378))], **weg),
          linie([(X(10), Y(345)), (X(10), Y(365))], **weg),
          linie([(X(-100), Y(128)), (X(-100), ykanal), (xr, ykanal),
                 (xr, Y(627)), (X(278), Y(627))], **weg),
          linie([(xr, Y(60)), (xr, ykanal)], **weg),
          linie([(xr, Y(640)), (X(330), Y(640))], **weg)]
    # Endschalter und Not-Aus
    for x, y in ((-160, 380), (-27, 395), (285, 60)):
        t.append(kreis(X(x), Y(y), 4.5, ROT))
    t += [kreis(X(338), Y(640), 9, GELB, GELB_RAND),
          kreis(X(338), Y(640), 5.5, '#e03131')]
    # Netzteil und PC hinter dem Gehaeuse
    t += kasten(X(-75) - 50, 58, 100, 26, ['Steckernetzteil'], gr=10.5,
                dy=17, dx=8)
    t += kasten(X(-300) - 64, 58, 64, 26, ['PC'], gr=10.5, dy=17, dx=22)
    t += [linie([(X(-75), 84), (X(-75), Y(37))], P24, 2.0),
          linie([(X(-300), 71), (X(-185), 71), (X(-185), Y(37))], '#495057',
                2.0)]
    t += kabelnr(X(-75) + 6, 98, 'K1') + kabelnr(X(-185) + 6, 98, 'K11')

    # Beschriftung links
    links = [(Y(90) - 3, 'Kabel links aus dem Gehäuse,'),
             (Y(90) + 10, 'unter dem 2040 durch'),
             (Y(250), 'Y-Kette: K3 K5 K7 K9 K10'),
             (Y(500), 'untere Nut außen am 2040')]
    for y, s in links:
        t.append(text(xl - 10, y, s, 10.5, GRAU, 'end', halo=True))
    t += kabelnr(X(-278) - 6, Y(632), 'K4', 'end')
    t.append(text(X(-278) - 44, Y(632), 'Y-Motor links', 10.5, TEXT, 'end'))
    # Portal
    t += kabelnr(X(-225), Y(300), 'K3')
    t.append(text(X(-225) + 30, Y(300), 'X-Motor', 9.5, GRAU))
    t += kabelnr(X(-160), Y(410), 'K7', 'middle')
    t.append(text(X(-160), Y(432), 'X-End.', 9.5, GRAU, 'middle'))
    t += [text(X(108), Y(322), 'X-Kette: K5 K9 K10', 10, GRAU, 'middle',
               halo=True)]
    t += kabelnr(X(0), Y(448), 'K5', 'end')
    t += kabelnr(X(4), Y(448), 'K9') + kabelnr(X(4) + 30, Y(448), 'K10')
    t.append(text(X(0), Y(468), 'Toolhead: Z-Motor, Z-End., Laser', 9.5,
                  GRAU, 'middle'))
    # rechts
    rechts = [(xr + 14, Y(55), 'K8', 'Y-Endschalter'),
              (xr + 14, Y(612), 'K6', 'Y-Motor rechts'),
              (X(338) + 16, Y(640) + 4, 'K2', 'Not-Aus (vorn)')]
    for x, y, k, s in rechts:
        t += kabelnr(x, y, k)
        t.append(text(x + 10 + 7 * len(k) + 6, y, s, 10.5, TEXT))
    t += [text(xr + 14, Y(150), 'Kanal, Rückseite des', 10.5, GRAU),
          text(xr + 14, Y(150) + 13, 'hinteren 2060', 10.5, GRAU),
          text(xr + 14, Y(400), 'untere Nut außen', 10.5, GRAU),
          text(xr + 14, Y(400) + 13, 'am rechten 2040', 10.5, GRAU)]

    # Kabelliste rechts
    kx = 668
    t.append(text(kx, 76, 'Kabel', 12, TEXT, fett=True))
    sp = (kx, kx + 40, kx + 160, kx + 290)
    for x, s in zip(sp[1:], ('Gerät', 'Adern, Länge', 'Weg')):
        t.append(text(x, 76, s, 10.5, GRAU))
    t.append(linie([(kx, 84), (W - 2 * RX - 16, 84)], '#d0d7de', 1))
    liste = [
        ('K1', 'Steckernetzteil', 'Hohlstecker 5,5 × 2,1',
         'hinten in die Buchse'),
        ('K2', 'Not-Aus', '2 × 0,5 mm², {} m'.format(lk['notaus']),
         'Kanal → rechts → vorn'),
        ('K3', 'X-Motor', '4-adrig, {} m'.format(lk['X-Motor']),
         'links → Y-Kette'),
        ('K4', 'Y-Motor links', '4-adrig, {} m'.format(lk['Y-Motor links']),
         'links, untere Nut'),
        ('K5', 'Z-Motor', '4-adrig, {} m'.format(lk['Z-Motor']),
         'Y-Kette → X-Kette'),
        ('K6', 'Y-Motor rechts', '4-adrig, {} m'.format(lk['Y-Motor rechts']),
         'Kanal → rechts → vorn'),
        ('K7', 'X-Endschalter', '3-adrig, {} m'.format(lk['X-Endschalter']),
         'links → Y-Kette'),
        ('K8', 'Y-Endschalter', '3-adrig, {} m'.format(lk['Y-Endschalter']),
         'Kanal → rechts → hinten'),
        ('K9', 'Z-Endschalter', '3-adrig, {} m'.format(lk['Z-Endschalter']),
         'Y-Kette → X-Kette'),
        ('K10', 'Laser', '3-adrig, {} m'.format(lk['Laser (12 V + PWM)']),
         'Y-Kette → X-Kette'),
        ('K11', 'PC', 'USB A auf B', 'hinten (USB-Fenster)')]
    for i, (k, g, a, w) in enumerate(liste):
        y = 104 + 22 * i
        t += kabelnr(kx, y, k)
        t += [text(sp[1], y, g, 11, TEXT), text(sp[2], y, a, 11, TEXT),
              text(sp[3], y, w, 11, GRAU)]
    y = 104 + 22 * len(liste) + 8
    t += zeilen(kx, y, [
        'In den Ketten nur hochflexible Schleppkettenlitze.',
        'Längen: Weg + {} % Reserve, aufgerundet (elektronik_zeichnen.py);'
        .format(de(ez.RESERVE * 100, 0)),
        'K2 wie Y-Motor rechts, der Ort des Not-Aus ist noch frei.'],
        10.5, GRAU)
    return t


# ---- Rahmen der ganzen Zeichnung -----------------------------------------

def legende(y):
    t = []
    x = RX
    eintraege = ((P24, '+24 V'), (P12, '+12 V (Laser)'), (MASSE, 'GND'),
                 (P5, '+5 V'), (SIGNAL, 'Signal'),
                 (MOTOR, 'Motorspule 1A/1B'), (SPULE2, 'Motorspule 2A/2B'))
    for farbe, s in eintraege:
        t += [draht([(x, y - 4), (x + 22, y - 4)], farbe, 2.6),
              text(x + 28, y, s, 11)]
        x += 28 + breite(s, 11) + 22
    t += [linie([(x, y - 4), (x + 22, y - 4)], KABELWEG, 2.0, '6 3'),
          text(x + 28, y, 'Kabelweg', 11)]
    x += 28 + breite('Kabelweg', 11) + 22
    t += kabelnr(x, y, 'K3')
    t.append(text(x + 30, y, 'Kabelnummer', 11))
    x += 30 + breite('Kabelnummer', 11) + 22
    t += warndreieck(x, y - 12)
    t.append(text(x + 23, y, 'Achtung', 11))
    return t


def pruefliste(b):
    t = [rechteck(0, 0, b, 118, '#f8f9fa', '#d0d7de', 1.0, rx=8),
         text(16, 26, 'Vor dem ersten Einschalten', 14.5, TEXT, fett=True)]
    links = ['1  Sichtprüfung: rot an +, schwarz an −, keine abstehenden '
             'Litzen, alle Wago-Hebel zu.',
             '2  Nur das Netzteil (kein USB, kein Laser): an der '
             'Shield-Klemme 24 V messen, + an +.',
             '3  Wandler auf 12,0 V stellen (Schritt 6), ausschalten, '
             'Laser anstecken.']
    rechts = ['4  USB zum PC: ? zeigt Pn:X, Y oder Z nur, solange eine '
              'Gabel unterbrochen ist ($5).',
              '5  Y-Motoren testen, bevor das Portal an beiden Riemen hängt: '
              'Wellen gegenläufig.',
              '6  Not-Aus drücken: Motoren lassen sich von Hand drehen, '
              'der Laser ist aus.']
    for spalte, liste in ((16, links), (b / 2 + 8, rechts)):
        for i, s in enumerate(liste):
            nr, rest = s.split('  ', 1)
            t += [text(spalte, 54 + 21 * i, nr, 11, BLAU, fett=True),
                  text(spalte + 14, 54 + 21 * i, rest, 11, TEXT)]
    return t


def main():
    kab = ez.kabel()
    lk = {n: de(kauf, 1) for n, (_, kauf) in kab.items()}
    lk['notaus'] = lk['Y-Motor rechts']      # gleicher Weg nach vorn
    t = [text(RX, 38, 'Verkabelungsplan Elektronik — jede Ader von Klemme '
              'zu Klemme', 19, TEXT, fett=True),
         text(RX, 60, 'Steckernetzteil 24 V, CNC Shield V3 auf Arduino Uno '
              'R3 (GRBL 1.1), 4 × TMC2209, Laser 12 V über einen '
              'Abwärtswandler. Schematisch, nicht maßstäblich.', 11.5, GRAU),
         text(RX, 77, 'In der Reihenfolge 1–6 verdrahten, alles stromlos. '
              'Linienfarbe = Funktion, nicht Aderfarbe. Nichts unter '
              'Spannung an- oder abstecken.', 11.5, GRAU)]
    t += legende(102)
    y = 118
    t.append(gruppe(RX, y, uebersicht(lk)))
    y += UEB_H + LUECKE
    felder = [schritt_shield(), schritt_strom(lk), schritt_verteilen(),
              schritt_motoren(lk), schritt_endschalter(lk), schritt_laser(lk)]
    for i, f in enumerate(felder):
        x = RX + (i % 2) * (PB + LUECKE)
        t.append(gruppe(x, y + (i // 2) * (PH + LUECKE), f))
    y += 3 * (PH + LUECKE)
    t.append(gruppe(RX, y, pruefliste(W - 2 * RX)))
    H = int(y + 118 + RX)
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
