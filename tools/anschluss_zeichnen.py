#!/usr/bin/env python3
"""Anschlussplan der Elektronik (Blockschaltbild, nicht massstaeblich).

Steckernetzteil 24 V, Schalter und Not-Aus, Verteilung ueber Wago-Klemmen,
Abwaertswandler 24 -> 12 V fuer den Laser, CNC Shield V3 auf dem Uno mit
Pins nach GRBL 1.1 (docs/hardware-notizen.md), Motoren, Laser und die drei
Gabellichtschranken; der Pi mit seinem 5-V-Wandler auf dem Pi-Halter. Jede Leitung traegt ihre Nummer aus der Kabelliste
(tools/verkabelung.py); die Liste steht unten in der Zeichnung. Die
Leistungsbilanz kommt aus tools/elektronik_zeichnen.py, damit alle
Zeichnungen dieselben Zahlen zeigen.

    python3 tools/anschluss_zeichnen.py   ->  docs/elektronik-anschluss.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import el, f1, text, TEXT, GRAU, BLAU   # noqa: E402
import elektronik_zeichnen as ez                              # noqa: E402
import verkabelung as vk                                      # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-anschluss.svg')

P24 = '#c62828'        # +24 V
P12 = '#e67700'        # +12 V
MASSE = '#1f2328'      # GND
SIGNAL = '#1864ab'     # PWM, Endschalter, Abort
P5 = '#8e44ad'         # 5 V
MOTOR = '#2b8a3e'      # Motorspulen
USB = '#868e96'


def block(x, y, b, h, zeilen, fill='#f4f6f9', stroke='#8c939e', fett=0,
          strich=None, tx=7):
    """Kasten mit Textzeilen; die ersten `fett` Zeilen fett."""
    t = [el('rect', {'x': f1(x), 'y': f1(y), 'width': f1(b),
                     'height': f1(h), 'rx': '3', 'fill': fill,
                     'stroke': stroke, 'stroke-width': '1',
                     'stroke-dasharray': strich})]
    y0 = y + 15
    for i, z in enumerate(zeilen):
        t.append(text(x + tx, y0 + 13 * i, z, 9.0 if i < fett else 8.3,
                      TEXT if i < fett else GRAU, fett=i < fett))
    return t


def draht(punkte, farbe, breite=1.8, strich=None):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': breite,
        'stroke-linejoin': 'round', 'stroke-dasharray': strich})


def pin(x, y, s='', anker='start', farbe=TEXT, gr=8.0):
    t = [el('circle', {'cx': f1(x), 'cy': f1(y), 'r': '2.4',
                       'fill': '#ffffff', 'stroke': TEXT,
                       'stroke-width': '1'})]
    if s:
        t.append(text(x + (5 if anker == 'start' else -5), y + 3, s, gr,
                      farbe, anker, halo=True))
    return t


def punkt(x, y, farbe):
    """Verbindungspunkt: hier sind Leitungen verbunden (ohne Punkt kreuzen
    sie nur)."""
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': '2.6',
                         'fill': farbe})


def marke(x, y, s):
    """Nummer der Leitung aus der Kabelliste, auf die Linie gesetzt."""
    b = 6.0 + 5.2 * len(s)
    return [el('rect', {'x': f1(x - b / 2), 'y': f1(y - 6), 'width': f1(b),
                        'height': '12', 'rx': '6', 'fill': '#ffffff',
                        'stroke': '#495057', 'stroke-width': '0.9'}),
            text(x, y + 3, s, 7.6, TEXT, 'middle', fett=True)]


def masse_zeichen(x, y):
    """Massezeichen, Spitze bei (x, y)."""
    return [draht([(x, y - 6), (x, y)], MASSE, 1.4),
            draht([(x - 6, y), (x + 6, y)], MASSE, 1.6),
            draht([(x - 3.5, y + 3), (x + 3.5, y + 3)], MASSE, 1.4),
            draht([(x - 1.5, y + 6), (x + 1.5, y + 6)], MASSE, 1.2)]


def main():
    lb = ez.leistung()
    Q = vk.laden()
    t = [text(24, 30, 'Anschlussplan — Stromversorgung, Motoren, '
              'Lichtschranken, Laser, Pi (Leitungen W1–W{})'.format(
                  len(vk.leitungen())), 14, TEXT, fett=True),
         text(24, 48, 'Blockschaltbild, nicht maßstäblich. Pins nach GRBL 1.1 '
              '(hardware-notizen.md). Nummern und Adern wie in '
              'verkabelung.md. Nichts unter Spannung an- oder abstecken.',
              9, GRAU)]
    # Legende der Farben
    for i, (farbe, s) in enumerate(((P24, '+24 V'), (P12, '+12 V'),
                                    (MASSE, 'Masse (GND)'), (P5, '+5 V'),
                                    (SIGNAL, 'Signal'),
                                    (MOTOR, 'Motorspulen'))):
        x = 24 + i * 118
        t += [draht([(x, 66), (x + 22, 66)], farbe, 2.4),
              text(x + 28, 69, s, 8.5)]
    t += marke(24 + 6 * 118 + 11, 66, 'W7')
    t.append(text(24 + 6 * 118 + 28, 69, 'Leitung (Liste unten)', 8.5))
    t += [punkt(24 + 7 * 118 + 60, 66, TEXT),
          text(24 + 7 * 118 + 68, 69, 'verbunden', 8.5)]

    # Elektronikfach
    t.append(el('rect', {'x': '226', 'y': '92', 'width': '580',
                         'height': '724', 'rx': '6', 'fill': '#fdf6ee',
                         'stroke': '#c2621b', 'stroke-width': '1.2',
                         'stroke-dasharray': '6 4'}))
    t.append(text(236, 86, 'im Elektronikfach (hinter dem hinteren 2060)',
                  9, '#c2621b', fett=True))
    t.append(text(846, 86, 'an der Maschine', 9, BLAU, fett=True))

    # ---- Einspeisung: Netzteil, Buchse, Schalter, Not-Aus ------------------
    t += block(24, 118, 180, 58, ['Steckernetzteil 24 V / 3 A',
                                  '72 W, 230 V bleibt außerhalb',
                                  'Hohlstecker 5,5 × 2,1'], fett=1)
    t += block(290, 118, 120, 42, ['Einbaubuchse', 'Mitte +, Hülse −'],
               fett=1)
    t += block(290, 186, 120, 40, ['Schalter EIN/AUS', 'rund, ≥ 3 A'],
               fett=1)
    t += block(24, 232, 180, 104, ['Not-Aus, vorn am 2060',
                                   'Pilztaster, Drehen löst',
                                   'Wechsler: C–NC trennt 24 V',
                                   'NO bleibt frei',
                                   'Kontakte {:.0f} A / {:.0f} V'.format(
                                       vk.NOTAUS_A, vk.NOTAUS_V),
                                   'Gehäuse: NotAus.py'], fett=1,
               fill='#fff4f4', stroke=P24)
    for y, s in ((250, 'C'), (268, 'NC'), (300, 'NO')):
        t += pin(204, y)
        t.append(text(198, y + 3, s, 7.5, GRAU, 'end'))
    t += [draht([(204, 132), (290, 132)], P24),              # Netzteil +
          draht([(204, 150), (290, 150)], MASSE),            # Netzteil −
          text(258, 145, 'Hohlstecker', 7.2, GRAU, 'middle')]
    # W1: Buchse + -> Schalter, Buchse − -> Wago GND (rechts herum)
    t += [draht([(350, 160), (350, 186)], P24),
          draht([(410, 150), (424, 150), (424, 410), (410, 410)], MASSE)]
    t += marke(366, 173, 'W1') + marke(424, 300, 'W1')
    # W2: Schalter -> Öffner 11, Öffner 12 -> Wago +24 V
    t += [draht([(290, 206), (238, 206), (238, 250), (204, 250)], P24),
          draht([(204, 268), (230, 268), (230, 358), (290, 358)], P24)]
    t += marke(262, 206, 'W2') + marke(262, 358, 'W2')

    # ---- Verteilung: Wago-Klemmen, Wandler, Lüfter -------------------------
    t += block(290, 350, 120, 36, ['Wago +24 V', '221-415, 5 Plätze'],
               fett=1, fill='#fff4f4', stroke=P24)
    t += block(290, 404, 120, 36, ['Wago GND', '221-420, 10 Plätze'],
               fett=1, fill='#f1f3f5', stroke=MASSE)
    t += block(290, 470, 120, 58, [
        'Abwärtswandler', '24 → 12 V, {} A'.format(ez.de(ez.WANDLER_A, 0)),
        'ohne Laser auf 12,0 V'], fett=1, fill='#fff7ec', stroke=P12)
    t += block(290, 552, 120, 40, ['Lüfter 40 mm, 24 V',
                                   'bläst auf die Treiber'], fett=1)
    t += block(290, 690, 120, 36, ['Wago +5 V', '221-420, 10 Plätze'],
               fett=1, fill='#f8f0fc', stroke=P5)
    # W4 (Wandler) innen, W5 (Lüfter) außen; die Masse der Lichtschranken
    # und des Not-Aus-Schließers ganz außen
    t += [draht([(290, 374), (276, 374), (276, 486), (290, 486)], P24),
          draht([(290, 426), (266, 426), (266, 500), (290, 500)], MASSE),
          draht([(290, 366), (256, 366), (256, 566), (290, 566)], P24),
          draht([(290, 418), (246, 418), (246, 580), (290, 580)], MASSE)]
    t += marke(271, 456, 'W4') + marke(251, 540, 'W5')

    # ---- CNC Shield V3 auf dem Uno -----------------------------------------
    sx, sy, sb, sh = 470, 118, 316, 482
    t.append(el('rect', {'x': f1(sx), 'y': f1(sy), 'width': f1(sb),
                         'height': f1(sh), 'rx': '3', 'fill': '#eef4fb',
                         'stroke': BLAU, 'stroke-width': '1'}))
    zeilen = [
        'CNC Shield V3 auf Arduino Uno R3',
        '4 × TMC2209, Jumper MS1 + MS2 = 1/16, MS3 frei',
        'A klont Y: A.STEP ↔ Y.STEP, A.DIR ↔ Y.DIR',
        'Jumper D12/D13 für A nicht stecken (D12 = Z-Endschalter)',
        'Treiber: EN-Pin zum EN-Aufdruck',
        'Strom {} A eff. = {} % von {} A, Vref je nach R_sense:'.format(
            ez.de(ez.MOTOR_I, 2), ez.de(ez.MOTOR_ANTEIL * 100, 0),
            ez.de(ez.MOTOR_NENN, 1)),
        ' · '.join('{} V (R{:03.0f})'.format(ez.de(ez.vref(ez.MOTOR_I, r), 2),
                                            r * 1000)
                   for r in ez.R_SENSE),
        'GRBL 1.1h: $32=1 (Laser), $30=1000, $5 nach dem Test']
    for i, z in enumerate(zeilen):
        t.append(text(sx + 12, 392 + 13 * i, z, 9.0 if i == 0 else 8.3,
                      TEXT if i == 0 else GRAU, fett=i == 0))
    # Schraubklemme links, W3 von den Wagos
    t += pin(sx, 250, 'Klemme + (12–36 V)') + pin(sx, 272, 'Klemme −')
    t += [draht([(410, 362), (438, 362), (438, 250), (sx, 250)], P24),
          draht([(410, 420), (450, 420), (450, 272), (sx, 272)], MASSE)]
    t += marke(444, 318, 'W3')
    # USB links unten
    t += pin(sx, 578, 'USB (Uno)')
    # Laser-PWM und Pull-down rechts oben, Motoren rechts
    t += pin(sx + sb, 170, 'Z+ (D11): Laser-PWM', 'end')
    t += pin(sx + sb, 196, 'Z− (D11): Pull-down', 'end')
    motoren = (('X', 'X-Motor', 'W12'), ('Y', 'Y-Motor links', 'W13'),
               ('Z', 'Z-Motor', 'W15'),
               ('A', 'Y-Motor rechts — eine Spule getauscht', 'W14'))
    for i, (n, _, _) in enumerate(motoren):
        t += pin(sx + sb, 250 + 30 * i, 'Motor ' + n + ' (2B 2A 1A 1B)',
                 'end')
    unten = ((520, 'X− (D9)'), (580, 'Y+ (D10)'), (640, 'SpnEn (D12)'),
             (760, '5V'))
    for x, s in unten:
        t += pin(x, sy + sh)
        t.append(text(x, sy + sh - 8, s, 8.0, TEXT, 'middle', halo=True))

    # ---- Geräte an der Maschine --------------------------------------------
    gx, gb = 846, 284
    # Laser oben rechts: W7 von Wandler (über den Kasten) und Shield
    t += block(gx, 118, gb, 64, ['Laser LASER TREE 4 W', '450 nm, 12 V, '
                                 '1,6 A (1,4–1,8 A)', 'XH2.54, von links:',
                                 'PWM · GND · +12 V'], fett=1,
               fill='#eef6ff', stroke=SIGNAL, tx=66)
    for y, s in ((134, '+12 V'), (152, 'GND'), (170, 'PWM')):
        t += pin(gx, y, s)
    t += [draht([(410, 486), (456, 486), (456, 98), (822, 98), (822, 134),
                 (gx, 134)], P12),
          draht([(410, 500), (464, 500), (464, 104), (812, 104), (812, 152),
                 (gx, 152)], MASSE),
          draht([(sx + sb, 170), (gx, 170)], SIGNAL)]
    t += marke(640, 101, 'W7') + marke(826, 170, 'W7')
    # W8: Pull-down 10 kΩ auf Z− (Signal- und GND-Stift)
    t += [draht([(sx + sb, 196), (796, 196), (796, 200)], SIGNAL, 1.4),
          el('rect', {'x': '792', 'y': '200', 'width': '8', 'height': '20',
                      'fill': '#ffffff', 'stroke': TEXT,
                      'stroke-width': '1.1'}),
          draht([(796, 220), (796, 226)], MASSE, 1.4)]
    t += masse_zeichen(796, 232)
    t.append(text(781, 216, '10 kΩ', 7.5, GRAU, 'end'))
    t += marke(796, 184, 'W8')
    # Motoren
    for i, (n, s, nr) in enumerate(motoren):
        y = 236 + 30 * i
        t += block(gx, y, gb, 26, [s], fett=1)
        t.append(draht([(sx + sb, 250 + 30 * i), (gx, 250 + 30 * i)], MOTOR,
                       2.2))
        t += marke(818, 250 + 30 * i, nr)
    t.append(text(gx, 372, 'je Spule ein Adernpaar: 2B·2A und 1A·1B',
                  7.8, GRAU))
    t.append(text(gx, 384, 'Y-Kette: W7, W9, W11, W12, W15 · X-Kette: '
                  'W7, W11, W15', 7.8, GRAU))

    # Lichtschranken: +5 V und GND als Sammelschiene, D0 einzeln vom Shield
    ls = (('X', 624, 520, 'W9', 'vor dem linken Rohrende'),
          ('Y', 676, 580, 'W10', 'außen am rechten 2040, hinten'),
          ('Z', 728, 640, 'W11', 'am Toolhead'))
    for a, y0, xs, nr, wo in ls:
        t += block(gx, y0, gb, 44, ['Lichtschranke {} (LM393)'.format(a), wo],
                   fett=1, tx=50)
        for dy, s in ((10, 'VCC'), (22, 'GND'), (34, 'D0')):
            t += pin(gx, y0 + dy, s, gr=7.4)
        t += [draht([(xs, sy + sh), (xs, y0 + 34), (gx, y0 + 34)], SIGNAL),
              draht([(822, y0 + 10), (gx, y0 + 10)], P5, 1.4),
              draht([(834, y0 + 22), (gx, y0 + 22)], MASSE, 1.4),
              punkt(822, y0 + 10, P5), punkt(834, y0 + 22, MASSE)]
        t += marke(796, y0 + 34, nr)
    # W6: 5V-Stift -> Wago +5 V; Sammelschiene +5 V -> VCC
    t += [draht([(760, sy + sh), (760, 698), (410, 698)], P5),
          draht([(410, 718), (822, 718)], P5, 1.6),
          draht([(822, 634), (822, 738)], P5, 1.6), punkt(822, 718, P5)]
    t += marke(700 - 40, 698, 'W6')
    # Masse: Wago GND -> Sammelschiene -> GND der Lichtschranken
    t += [draht([(290, 410), (240, 410), (240, 792), (834, 792), (834, 646)],
                MASSE, 1.6),
          punkt(834, 750, MASSE), punkt(834, 698, MASSE)]
    t += marke(540, 792, 'W9–11')
    # W16: 24-V-Waechter an Abort — R1 vom +24 V hinter dem Not-Aus,
    # R2 und 100 nF nach GND
    ya, xk = 470, 822
    t += pin(sx + sb, ya, 'Abort (A0)', 'end')
    t += [draht([(sx + sb, ya), (xk, ya)], SIGNAL, 1.6),
          punkt(xk, ya, SIGNAL),
          draht([(xk, ya), (xk, 452)], SIGNAL, 1.4),
          el('rect', {'x': f1(xk - 4), 'y': '432', 'width': '8',
                      'height': '20', 'fill': '#ffffff', 'stroke': TEXT,
                      'stroke-width': '1.1'}),
          draht([(xk, 432), (xk, 420)], P24, 1.4),
          draht([(xk - 6, 420), (xk + 6, 420)], P24, 2.0),
          text(xk + 10, 423, '+24 V hinter dem Not-Aus (Wago)', 8.0, P24),
          text(xk + 8, 446, '22 kΩ', 7.5, GRAU),
          draht([(xk, ya), (xk, 488)], SIGNAL, 1.4),
          el('rect', {'x': f1(xk - 4), 'y': '488', 'width': '8',
                      'height': '20', 'fill': '#ffffff', 'stroke': TEXT,
                      'stroke-width': '1.1'}),
          draht([(xk, 508), (xk, 516)], MASSE, 1.4),
          draht([(xk, 478), (xk + 18, 478), (xk + 18, 494)], SIGNAL, 1.2),
          draht([(xk + 12, 494), (xk + 24, 494)], TEXT, 2.0),
          draht([(xk + 12, 499), (xk + 24, 499)], TEXT, 2.0),
          draht([(xk + 18, 499), (xk + 18, 516), (xk, 516)], MASSE, 1.2),
          text(xk + 28, 500, '4,7 kΩ ∥ 100 nF', 7.5, GRAU)]
    t += masse_zeichen(xk, 522)
    t += marke(803, ya, 'W16')
    # Pi-Halter (im Fach rechts neben dem Kasten): 5-V-Wandler und Pi.
    # W18 an der Buchse, vor Schalter und Not-Aus; W19 5 V in PWR IN; W17
    # USB zum Uno
    t.append(el('rect', {'x': '14', 'y': '470', 'width': '200',
                         'height': '214', 'rx': '6', 'fill': 'none',
                         'stroke': BLAU, 'stroke-width': '1.1',
                         'stroke-dasharray': '6 4'}))
    t.append(text(20, 464, 'Pi-Halter (im Fach, rechts neben dem Kasten)',
                  8.5, BLAU, fett=True))
    t += block(24, 486, 180, 58, ['Abwärtswandler 24 → 5 V',
                                  '≥ {} A, Ausgang USB-A'.format(
                                      ez.de(ez.PI_WANDLER_A, 0)),
                                  'vor Schalter und Not-Aus'],
               fett=1, fill='#f8f0fc', stroke=P5)
    t += pin(204, 500, 'IN+', 'end') + pin(204, 516, 'IN−', 'end')
    t += [draht([(300, 160), (300, 172), (220, 172), (220, 500), (204, 500)],
                P24),
          draht([(316, 160), (316, 178), (212, 178), (212, 516), (204, 516)],
                MASSE)]
    t += pin(300, 160) + pin(316, 160)
    t += marke(220, 440, 'W18')
    t += block(24, 590, 180, 58, ['Raspberry Pi Zero 2 W',
                                  'CNCjs im Browser, WLAN 2,4 GHz',
                                  'Pi-Halter: PiHalter.py'], fett=1)
    t += [draht([(114, 544), (114, 590)], P5)]
    t += pin(114, 544) + pin(114, 590)
    t.append(text(120, 556, 'USB-A', 7.5, GRAU))
    t.append(text(120, 586, 'PWR IN', 7.5, GRAU))
    t += marke(140, 568, 'W19')
    t += pin(204, 630, 'USB', 'end')
    t.append(draht([(204, 630), (460, 630), (460, 578), (sx, 578)], USB,
                   1.6, '5 3'))
    t += marke(330, 630, 'W17')

    # ---- Kabelliste -------------------------------------------------------
    ty = 846
    t.append(text(24, ty, 'Kabelliste', 10.5, BLAU, fett=True))
    lts = vk.leitungen()
    halb = (len(lts) + 1) // 2
    spalten = (0, 36, 176, 360, 452)
    for i, lt in enumerate(lts):
        x0 = 24 + (i // halb) * 580
        y = ty + 18 + 14 * (i % halb)
        weg, kauf = vk.laenge_m(lt, Q['K'])
        if weg is not None:
            laenge = '{} → {} m'.format(ez.de(weg, 2), ez.de(kauf, 2))
            if lt.get('mitgeliefert') and kauf <= lt['mitgeliefert']:
                laenge = '{} m, mitgeliefert'.format(ez.de(weg, 2))
        elif lt.get('laenge'):
            laenge = '≈ {} m'.format(ez.de(lt['laenge'], 2))
        else:
            laenge = '—'
        kette = 'Kette ' + lt['kette'] if lt.get('kette') else ''
        for x, s, fett in ((spalten[0], lt['nr'], True),
                           (spalten[1], lt['name'], False),
                           (spalten[2], vk._litze(lt), False),
                           (spalten[3], laenge, False),
                           (spalten[4], kette, False)):
            t.append(text(x0 + x, y, s, 8.2, TEXT if fett else GRAU,
                          fett=fett))

    # ---- Zahlen ------------------------------------------------------------
    ty = ty + 18 + 14 * halb + 12
    zeilen = [
        ('Leistung', 'Motoren ≈ {} W, Lüfter ≈ {} W, Laser über den Wandler '
         '≈ {} W, Pi mit Uno und Lichtschranken ≈ {} W — zusammen ≈ {} W '
         'von {} W (dauernd {} W)'.format(
             ez.de(lb['motoren'], 0), ez.de(lb['luefter'], 0),
             ez.de(lb['laser'], 0), ez.de(lb['pi'], 0),
             ez.de(lb['summe'], 0), ez.de(ez.NETZTEIL_W, 0),
             ez.de(lb['dauer'], 0))),
        ('Wandler', 'Laser 12 V × {} A = {} W, bei {} % Wirkungsgrad {} W '
         'aus dem Netzteil; der Wandler ({} A) ist damit zu {} % belastet. '
         'Ausgang vor dem Anschließen des Lasers messen: 12,0 V'.format(
             ez.de(ez.LASER_A, 1), ez.de(ez.LASER_V * ez.LASER_A, 1),
             ez.de(ez.WANDLER_ETA * 100, 0), ez.de(lb['laser'], 0),
             ez.de(ez.WANDLER_A, 0),
             ez.de(100.0 * ez.LASER_A / ez.WANDLER_A, 0))),
        ('Masse', 'Netzteil, Shield, Wandler, Laser und Lichtschranken haben '
         'ein gemeinsames GND, Stern an der Wago GND; ein isolierter Wandler '
         'braucht dafür eine Brücke OUT− → GND'),
        ('Not-Aus', 'Wechsler C/NO/NC: C und NC trennen die 24 V von '
         'Shield, Wandler und Lüfter, NO bleibt frei. Fehlen sie (Not-Aus, '
         'Schalter), zieht der Wächter W16 Abort auf LOW, und GRBL bricht ab'),
        ('Pi', 'sein 5-V-Wandler hängt mit W18 an der Buchse, vor Schalter '
         'und Not-Aus: Pi und Uno laufen weiter, der Wächter meldet; über '
         'USB (W17) versorgt der Pi den Uno und damit die Lichtschranken'),
        ('Einschalten', 'Netzteil einstecken: Pi und Uno starten, GRBL läuft '
         '(der Pull-down W8 hält den Laser aus); dann Schalter EIN: 24 V. '
         'Ausschalten umgekehrt, den Pi vor dem Ausstecken herunterfahren'),
    ]
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 15 * i, k, 8.5, GRAU))
        t.append(text(100, ty + 15 * i, v, 8.5, TEXT))
    W, H = 1180, ty + 15 * len(zeilen) + 14
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
