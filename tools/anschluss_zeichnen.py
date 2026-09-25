#!/usr/bin/env python3
"""Anschlussplan der Elektronik (Blockschaltbild, nicht massstaeblich).

Steckernetzteil 24 V, Schalter und Not-Aus, Verteilung ueber Wago-Klemmen,
Abwaertswandler 24 -> 12 V fuer den Laser, CNC Shield V3 auf dem Uno mit
Pins nach GRBL 1.1 (docs/hardware-notizen.md), Motoren, Laser und die drei
Gabellichtschranken. Die Leistungsbilanz kommt aus
tools/elektronik_zeichnen.py, damit beide Zeichnungen dieselben Zahlen
zeigen.

    python3 tools/anschluss_zeichnen.py   ->  docs/elektronik-anschluss.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import el, f1, text, TEXT, GRAU, BLAU   # noqa: E402
import elektronik_zeichnen as ez                              # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-anschluss.svg')

P24 = '#c62828'        # +24 V
P12 = '#e67700'        # +12 V
MASSE = '#1f2328'      # GND
SIGNAL = '#1864ab'     # PWM, Endschalter
P5 = '#8e44ad'         # 5 V
MOTOR = '#2b8a3e'      # Motorspulen


def block(x, y, b, h, zeilen, fill='#f4f6f9', stroke='#8c939e', fett=0,
          strich=None):
    """Kasten mit Textzeilen; die ersten `fett` Zeilen fett."""
    t = [el('rect', {'x': f1(x), 'y': f1(y), 'width': f1(b),
                     'height': f1(h), 'rx': '3', 'fill': fill,
                     'stroke': stroke, 'stroke-width': '1',
                     'stroke-dasharray': strich})]
    y0 = y + 15
    for i, z in enumerate(zeilen):
        t.append(text(x + 7, y0 + 13 * i, z, 9.0 if i < fett else 8.3,
                      TEXT if i < fett else GRAU, fett=i < fett))
    return t


def draht(punkte, farbe, breite=1.8, strich=None):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': breite,
        'stroke-linejoin': 'round', 'stroke-dasharray': strich})


def pin(x, y, s, anker='start', farbe=TEXT):
    return [el('circle', {'cx': f1(x), 'cy': f1(y), 'r': '2.4',
                          'fill': '#ffffff', 'stroke': TEXT,
                          'stroke-width': '1'}),
            text(x + (5 if anker == 'start' else -5), y + 3, s, 8.0, farbe,
                 anker, halo=True)]


def main():
    lb = ez.leistung()
    t = [text(24, 30, 'Anschlussplan Elektronik — Steckernetzteil 24 V, '
              'CNC Shield V3, Laser 12 V', 14, TEXT, fett=True),
         text(24, 48, 'Blockschaltbild, nicht maßstäblich. Pins nach GRBL 1.1 '
              '(hardware-notizen.md, Elektronik). Nichts unter Spannung '
              'an- oder abstecken.', 9, GRAU)]
    # Legende der Farben
    for i, (farbe, s) in enumerate(((P24, '+24 V'), (P12, '+12 V'),
                                    (MASSE, 'Masse (GND)'), (P5, '+5 V'),
                                    (SIGNAL, 'Signal'),
                                    (MOTOR, 'Motorspulen'))):
        x = 24 + i * 118
        t += [draht([(x, 66), (x + 22, 66)], farbe, 2.4),
              text(x + 28, 69, s, 8.5)]

    # Elektronikfach
    t.append(el('rect', {'x': '226', 'y': '92', 'width': '560',
                         'height': '668', 'rx': '6', 'fill': '#fdf6ee',
                         'stroke': '#c2621b', 'stroke-width': '1.2',
                         'stroke-dasharray': '6 4'}))
    t.append(text(236, 108, 'im Elektronikfach (hinter dem hinteren 2060)',
                  9, '#c2621b', fett=True))

    # ---- Einspeisung: Netzteil, Buchse, Schalter, Not-Aus ------------------
    t += block(24, 120, 180, 58, ['Steckernetzteil 24 V / 3 A',
                                  '72 W, 230 V bleibt außerhalb',
                                  'Hohlstecker'], fett=1)
    t += block(290, 124, 120, 44, ['Einbaubuchse', 'für den Hohlstecker'],
               fett=1)
    t += block(290, 196, 120, 44, ['Schalter EIN/AUS', '≥ 3 A Gleichstrom'],
               fett=1)
    t += block(24, 258, 180, 58, ['Not-Aus, vorn', 'Pilzschalter, Öffner',
                                  '≥ 3 A Gleichstrom'], fett=1,
               fill='#fff4f4', stroke=P24)
    t += [draht([(204, 140), (290, 140)], P24),            # Netzteil +
          draht([(204, 156), (290, 156)], MASSE)]          # Netzteil −
    t += [draht([(350, 168), (350, 196)], P24),        # Buchse + -> Schalter
          draht([(290, 218), (232, 218), (232, 272), (204, 272)], P24),
          draht([(204, 300), (350, 300), (350, 336)], P24)]  # -> Wago +24
    # Buchse − -> Wago GND, rechts an Schalter und Wago +24 vorbei
    t.append(draht([(410, 156), (424, 156), (424, 400), (410, 400)], MASSE))

    # ---- Verteilung: Wago-Klemmen, Wandler, Lüfter -------------------------
    t += block(290, 336, 120, 40, ['Wago +24 V', '221-415, 5 Plätze'],
               fett=1, fill='#fff4f4', stroke=P24)
    t += block(290, 390, 120, 40, ['Wago GND', '221-415, 5 Plätze'], fett=1,
               fill='#f1f3f5', stroke=MASSE)
    t += block(290, 466, 120, 58, ['Abwärtswandler', '24 → 12 V, ≥ 3 A',
                                   'Ausgang auf 12,0 V'], fett=1,
               fill='#fff7ec', stroke=P12)
    t += block(290, 556, 120, 58, ['Lüfter 40 mm', 'über den Treibern',
                                   '12-V-Typ: am Wandler'], fett=1)
    t += block(290, 660, 120, 44, ['Wago +5 V', 'für die Lichtschranken'],
               fett=1, fill='#f8f0fc', stroke=P5)
    # +24 V und GND links hinunter zu Wandler und Lüfter
    t += [draht([(290, 350), (262, 350), (262, 480), (290, 480)], P24),
          draht([(262, 480), (262, 568), (290, 568)], P24),
          draht([(290, 414), (250, 414), (250, 496), (290, 496)], MASSE),
          draht([(250, 496), (250, 586), (290, 586)], MASSE)]

    # ---- CNC Shield V3 auf dem Uno -----------------------------------------
    sx, sy, sb, sh = 470, 124, 300, 400
    t += block(sx, sy, sb, sh, [
        'CNC Shield V3 auf Arduino Uno R3',
        '4 × TMC2209, Jumper MS1 + MS2 = 1/16, MS3 frei',
        'A klont Y: A.STEP ↔ Y.STEP, A.DIR ↔ Y.DIR',
        'Treiber: EN-Pin zum EN-Aufdruck',
        'Strom am Vref-Poti, ≈ 70 % des Motornennstroms',
        'GRBL 1.1h: $32=1 (Laser), $30=1000'], fett=1, fill='#eef4fb',
        stroke=BLAU)
    # Schraubklemme links
    t += pin(sx, 250, 'Klemme + (12–36 V)')
    t += pin(sx, 272, 'Klemme −')
    t += [draht([(410, 350), (438, 350), (438, 250), (sx, 250)], P24),
          draht([(410, 404), (448, 404), (448, 272), (sx, 272)], MASSE)]
    # Wandler: Eingang von den Wagos, Ausgang zum Laser (unter dem Shield)
    # USB
    t += pin(sx, 470, 'USB (Uno)')
    # Motorausgänge rechts
    motoren = (('X', 'X-Motor'), ('Y', 'Y-Motor links'), ('Z', 'Z-Motor'),
               ('A', 'Y-Motor rechts'))
    for i, (n, _) in enumerate(motoren):
        t += pin(sx + sb, 250 + 30 * i, 'Motor ' + n, 'end')
    t += pin(sx + sb, 380, 'Z+ (D11): Laser-PWM', 'end')
    unten = ((520, 'X+ (D9)'), (590, 'Y+ (D10)'), (660, 'SpnEn (D12)'),
             (730, '5V'))
    for x, s in unten:
        t.append(el('circle', {'cx': f1(x), 'cy': f1(sy + sh), 'r': '2.4',
                               'fill': '#ffffff', 'stroke': TEXT,
                               'stroke-width': '1'}))
        t.append(text(x, sy + sh - 7, s, 8.0, TEXT, 'middle', halo=True))

    # ---- Geräte an der Maschine --------------------------------------------
    gx, gb = 846, 250
    t.append(text(gx, 108, 'an der Maschine', 9, BLAU, fett=True))
    for i, (n, s) in enumerate(motoren):
        y = 236 + 30 * i
        zusatz = ' — eine Spule getauscht' if n == 'A' else ''
        t += block(gx, y, gb, 26, [s + zusatz], fett=1)
        t.append(draht([(sx + sb, 250 + 30 * i), (gx, 250 + 30 * i)], MOTOR,
                       2.2))
    t.append(text(gx, 364, '4 Adern je Motor, durch die Ketten: X, Z',
                  7.8, GRAU))
    t += block(gx, 396, gb, 72, ['Laser LASER TREE 4 W (450 nm)',
                                 '12 V, 1,6 A (1,4–1,8 A)',
                                 'Buchse XH2.54, 3-polig:',
                                 '12 V · GND · PWM (5 V) — Aufdruck prüfen'],
               fett=1, fill='#eef6ff', stroke=SIGNAL)
    t += [draht([(sx + sb, 380), (812, 380), (812, 440), (gx, 440)], SIGNAL),
          draht([(410, 480), (430, 480), (430, 548), (800, 548), (800, 412),
                 (gx, 412)], P12),
          draht([(410, 510), (440, 510), (440, 560), (824, 560), (824, 426),
                 (gx, 426)], MASSE)]
    t.append(text(gx, 484, '12 V und GND vom Wandler, PWM vom Shield:',
                  7.8, GRAU))
    t.append(text(gx, 495, 'ein 3-adriges Kabel, 2 m, durch beide Ketten',
                  7.8, GRAU))
    # Endschalter
    es = (('X-Endschalter', 520), ('Y-Endschalter', 590),
          ('Z-Endschalter', 660))
    for i, (s, x) in enumerate(es):
        y = 600 + 44 * i
        t += block(gx, y, gb, 34, [s + ' (LM393)',
                                   'VCC 5 V · GND · D0'], fett=1)
        t.append(draht([(x, sy + sh), (x, y + 17), (gx, y + 17)], SIGNAL))
    t.append(draht([(730, sy + sh), (730, 682), (410, 682)], P5))
    t.append(draht([(410, 690), (836, 690), (836, 612), (gx, 612)], P5,
                   1.4, '4 3'))
    t += [draht([(836, 656), (gx, 656)], P5, 1.4, '4 3'),
          draht([(836, 690), (836, 700), (gx, 700)], P5, 1.4, '4 3')]
    t.append(text(gx, 752, 'GND der Lichtschranken an den GND-Stift',
                  7.8, GRAU))
    t.append(text(gx, 763, 'neben dem jeweiligen Eingang', 7.8, GRAU))
    # PC
    t += block(24, 470, 180, 40, ['PC', 'LightBurn o. ä., USB'], fett=1)
    t.append(draht([(sx, 470), (456, 470), (456, 454), (204, 454),
                    (204, 470)], SIGNAL, 1.4, '5 3'))

    # ---- Zahlen ------------------------------------------------------------
    ty = 796
    zeilen = [
        ('Leistung', 'Motoren ≈ {} W, Lüfter ≈ {} W, Laser über den Wandler '
         '≈ {} W — zusammen ≈ {} W von {} W (dauernd {} W)'.format(
             ez.de(lb['motoren'], 0), ez.de(lb['luefter'], 0),
             ez.de(lb['laser'], 0), ez.de(lb['summe'], 0),
             ez.de(ez.NETZTEIL_W, 0), ez.de(lb['dauer'], 0))),
        ('Wandler', 'Laser 12 V × {} A = {} W, bei {} % Wirkungsgrad {} W '
         'aus dem Netzteil; Ausgang vor dem Anschließen des Lasers auf '
         '12,0 V'.format(ez.de(ez.LASER_A, 1),
                         ez.de(ez.LASER_V * ez.LASER_A, 1),
                         ez.de(ez.WANDLER_ETA * 100, 0),
                         ez.de(lb['laser'], 0))),
        ('Masse', 'Netzteil, Shield, Wandler und Laser haben ein gemeinsames '
         'GND; ein isolierter Wandler braucht dafür eine Brücke OUT− → GND'),
    ]
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 15 * i, k, 8.5, GRAU))
        t.append(text(96, ty + 15 * i, v, 8.5, TEXT))
    W, H = 1120, ty + 15 * len(zeilen) + 14
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
