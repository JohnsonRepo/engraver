#!/usr/bin/env python3
"""Motoren anschliessen: welcher Stift am Shield an welche Ader.

Links das CNC Shield V3 von oben, so wie es im Gehaeuse liegt (Reset-Taster
oben links, Schraubklemme unten links): die Motorstecker rechts neben den
Treibern X (oben links), Y (oben rechts), Z (unten links) und A (unten
rechts) mit ihren Aderfarben, und die Jumper, die A zum Klon von Y machen.
Rechts je
Achse die vier Stifte 2B · 2A · 1A · 1B mit den Adern der StepperOnline-
Motorkabel und dem Motor, der daran gehoert. Zuordnung, Farben, Nummern
und Laengen kommen aus tools/verkabelung.py (W12-W15), wie im Schritt
"Motoren" von docs/elektronik-verkabelung.svg.

    python3 tools/motoren_zeichnen.py   ->  docs/motoren-anschluss.svg
"""

import os
import re
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import text, TEXT, GRAU, BLAU              # noqa: E402
import verkabelung as vk                                         # noqa: E402
import verkabelung_zeichnen as vz                                # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'motoren-anschluss.svg')

W, H = 1000, 732
PLATINE = ('#fbe3df', '#c92a2a')     # rotes Shield, aufgehellt
TREIBER = '#2b2f36'
STIFTE = ('2B', '2A', '1A', '1B')    # Motorstecker von oben nach unten


def motoren():
    """[(Achse, Leitung)] in der Reihenfolge X, Y, Z, A — welcher Motor an
    welchem Treiber haengt, steht in der Kabelliste (Shield X 2B·2A ...)."""
    z = []
    for achse in ('X', 'Y', 'Z', 'A'):
        nr = next(n for n, lt in vz.LT.items()
                  if lt['adern'][0][2] == 'Shield {} 2B·2A'.format(achse))
        z.append((achse, vz.LT[nr]))
    return z


def treiber(x0, y0, b, h):
    """TMC2209 wie auf dem Foto: Poti oben rechts, goldene Kuehlflaeche."""
    t = [vz.rechteck(x0, y0, b, h, TREIBER, '#000000', 0.8, rx=2),
         vz.rechteck(x0 + b * 0.24, y0 + h * 0.36, b * 0.52, h * 0.44,
                     '#d8c48a', '#b59a4c', 0.6, rx=1),
         vz.kreis(x0 + b * 0.72, y0 + h * 0.12, b * 0.07, '#e9ecef',
                  '#868e96', 0.8)]
    for k in range(8):
        y = y0 + h * (k + 0.5) / 8
        t += [vz.kreis(x0 + b * 0.08, y, 1.8, '#adb5bd'),
              vz.kreis(x0 + b * 0.92, y, 1.8, '#adb5bd')]
    return t


def shield():
    """Linkes Feld: das Shield von oben."""
    t = [vz.rechteck(0, 0, 470, 600, '#ffffff', '#d0d7de', 1.0, rx=8),
         vz.kreis(22, 23, 13, BLAU),
         text(22, 28, '1', 14, '#ffffff', 'middle', fett=True),
         text(44, 28.5, 'Wo die Motorstecker sitzen', 14.5, TEXT, fett=True)]
    s, ox, oy = 0.5, 20.0, 56.0       # Massstab zum Foto, Lage der Platine

    def P(px, py):                    # Fotokoordinaten -> Zeichnung
        return ox + (px - 230) * s, oy + (py - 605) * s

    x0, y0 = P(230, 605)
    x1, y1 = P(1065, 1320)
    t.append(vz.rechteck(x0, y0, x1 - x0, y1 - y0, *PLATINE, 1.4, rx=6))
    # Reset-Taster, Schraubklemme
    a, b = P(245, 625), P(345, 715)
    t += [vz.rechteck(a[0], a[1], b[0] - a[0], b[1] - a[1], '#495057',
                      '#212529', 0.8, rx=2),
          vz.kreis((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 9, '#212529'),
          text(b[0] + 4, a[1] + 12, 'RST', 9, PLATINE[1], fett=True)]
    a, b = P(235, 1090), P(390, 1200)
    t += [vz.rechteck(a[0], a[1], b[0] - a[0], b[1] - a[1], '#1c7ed6',
                      '#1864ab', 0.8, rx=2),
          vz.kreis(a[0] + 20, (a[1] + b[1]) / 2, 11, '#a5d8ff', '#1864ab'),
          vz.kreis(b[0] - 20, (a[1] + b[1]) / 2, 11, '#a5d8ff', '#1864ab'),
          text((a[0] + b[0]) / 2, b[1] + 13, '12–36 V', 9.5, PLATINE[1],
               'middle', fett=True)]
    # A-Klon: Reihen X, Y, Z, D12/D13, je STEP und DIR; gebrueckt nur Y
    xs, xd, yr = P(282, 0)[0], P(358, 0)[0], P(0, 958)[1]
    teilung = 135 * s / 4
    for i, reihe in enumerate(('X', 'Y', 'Z', 'D12')):
        y = yr + teilung * i
        t.append(text(xs - 9, y + 3.5, reihe, 8.5, PLATINE[1], 'end',
                      fett=True))
        for xb in (xs, xd):
            t += [vz.stift(xb + 4, y), vz.stift(xb + 18, y)]
            if reihe == 'Y':
                t.append(vz.jumper(xb + 4, y, xb + 18, y))
    t += [text(xs + 11, yr - 11, 'STEP', 8, PLATINE[1], 'middle',
               fett=True),
          text(xd + 11, yr - 11, 'DIR', 8, PLATINE[1], 'middle', fett=True)]
    # Treiber und ihre Motorstecker, rechts daneben in den Reihen 3-6
    # Steckplaetze am Shield abgelesen (Foto 2026-10-08) [v]
    plaetze = {'X': (440, 650, 665, 950), 'Y': (745, 650, 950, 950),
               'Z': (440, 1000, 665, 1290), 'A': (745, 1000, 950, 1290)}
    adern = {a: vz.farben(lt['adern'][0][1]) + vz.farben(lt['adern'][1][1])
             for a, lt in motoren()}
    for achse, (px0, py0, px1, py1) in plaetze.items():
        a, b = P(px0, py0), P(px1, py1)
        bt, ht = b[0] - a[0], b[1] - a[1]
        t += treiber(a[0], a[1], bt, ht)
        hx = b[0] + 4
        ya, yb = a[1] + ht * 2 / 8, a[1] + ht * 6 / 8
        t.append(vz.rechteck(hx, ya, 10, yb - ya, '#212529', '#000000', 0.8,
                             rx=1.5))
        for k, f in enumerate(adern[achse]):
            t.append(vz.kreis(hx + 5, a[1] + ht * (k + 2.5) / 8, 3.0,
                              vz.ADERFARBE[f], '#ffffff', 1.0))
        t += [vz.rechteck(hx - 2, yb + 5, 14, 14, '#ffffff', PLATINE[1], 1.0,
                          rx=1),
              text(hx + 5, yb + 16, achse, 10, PLATINE[1], 'middle',
                   fett=True)]
        if achse == 'X':
            for k, s_ in enumerate(STIFTE):
                t.append(text(hx + 14, a[1] + ht * (k + 2.5) / 8 + 3, s_,
                              7.5, TEXT, fett=True))
    # Hinweise unter der Platine
    t += vz.zeilen(20, y1 + 30, [
        'Motorstecker: rechts neben jedem Treiber, die vier Stifte von',
        'oben nach unten 2B · 2A · 1A · 1B.',
        'Achsbuchstabe im Kästchen unter dem Stecker: X oben links,',
        'Y oben rechts, Z unten links, A unten rechts. Die Punkte am',
        'Stecker zeigen die Aderfarben (rechts im Einzelnen).',
        'A klont Y: je ein Jumper in der Reihe Y, für STEP und DIR,',
        'sonst keiner — auf D12/D13 läge der Z-Endschalter.',
        'Treiber: Poti oben rechts wie auf dem Foto, EN zum EN-Aufdruck.'],
        10.5, TEXT, 14)
    return t


def achsen(Q):
    """Rechtes Feld: je Achse die Stifte, die Adern und der Motor."""
    t = [vz.rechteck(0, 0, 470, 600, '#ffffff', '#d0d7de', 1.0, rx=8),
         vz.kreis(22, 23, 13, BLAU),
         text(22, 28, '2', 14, '#ffffff', 'middle', fett=True),
         text(44, 28.5, 'Welche Ader an welchen Stift', 14.5, TEXT,
              fett=True)]
    xs, xk, xm = 96, 270, 284         # Stifte, Ende der Adern, Motor
    for i, (achse, lt) in enumerate(motoren()):
        g = 74 + 134 * i
        pins = [g + 18 * k for k in range(4)]
        (fa, ca, va, aa), (fb, cb, vb, ab) = lt['adern']
        t += [text(18, g + 34, achse, 26, BLAU, fett=True),
              text(18, g + 50, 'Steckplatz', 9.5, GRAU)]
        t.append(vz.rechteck(xs - 6, g - 9, 12, 72, '#212529', '#000000',
                             0.8, rx=1.5))
        t.append(vz.rechteck(xs + 6, g - 9, 24, 72, '#e9ecef', '#868e96',
                             0.8, rx=2))
        t.append(text(xs + 18, g + 75, 'Dupont', 8.5, GRAU, 'middle'))
        for p, s in zip(pins, STIFTE):
            t.append(text(xs - 11, p + 3.5, s, 10, TEXT, 'end', fett=True))
        # Adern: Spule A auf 2B · 2A, Spule B auf 1A · 1B; am Motor die
        # Stifte in der Reihenfolge des Steckers ab Werk
        enden = [e.strip() for a in (aa, ab)
                 for e in re.search(r': (.+)$', vk.ANSCHLUSS[a][0])
                 .group(1).split('·')]
        ordnung = list(vk.MOTOR_STECKER)
        for k, (p, f) in enumerate(zip(pins, vz.farben(ca) + vz.farben(cb))):
            ziel = pins[ordnung.index(enden[k])]
            if ziel == p:
                t += vz.draht([(xs + 30, p), (xk, p)], f)
            else:
                t += vz.draht([(xs + 30, p), (150, p), (176, ziel),
                               (xk, ziel)], f)
        for p in pins:
            t.append(vz.kreis(xs, p, 2.4, '#fcc419'))
        t += [text(214, g + 12, fa.split(',')[0], 9.5, TEXT, 'middle',
                   fett=True, halo=True),
              text(214, g + 48, fb, 9.5, TEXT, 'middle', fett=True,
                   halo=True)]
        # Motor mit PH-Stecker ab Werk
        t += [vz.rechteck(xk, g - 9, 12, 72, '#f8f9fa', '#868e96', 0.8,
                          rx=2),
              vz.rechteck(xm, g - 14, 172, 82, vz.FILL, vz.RAND)]
        t += vz.motor_symbol(xm + 8, g - 4)
        t += [text(xm + 50, g + 6, lt['name'], 12, TEXT, fett=True)]
        t += vz.marke(xm + 50, g + 26, lt['nr'])
        if lt.get('kette'):
            t.append(text(xm + 50 + 10 + 7 * len(lt['nr']) + 6, g + 26,
                          'Kette ' + lt['kette'], 9.5, GRAU))
        t += [text(xm + 50, g + 44, vz.laenge_text(lt, Q['K']), 9.5, GRAU),
              text(xm + 8, g + 61, 'PH-Stecker am Motor (ab Werk)', 9.5,
                   GRAU)]
        if 'getauscht' in fa:
            t += vz.warnung(xs - 10, g + 86, [
                'Schwarz und Grün getauscht: dreht gegen Y.',
                'Oder den ganzen Stecker um 180° gedreht aufstecken.'],
                10, 13)
        elif 'lose' in lt.get('hinweis', ''):
            t.append(text(xs - 10, g + 98, 'In der Kette nur die losen '
                          'Adern, ohne Schlauch.', 9.5, GRAU))
    return t


def main():
    Q = vk.laden()
    t = [text(24, 36, 'Motoren anschließen — CNC Shield V3, StepperOnline '
              'NEMA 17', 19, TEXT, fett=True),
         text(24, 58, 'Shield von oben wie im Gehäuse. Farben der Motorkabel '
              'wie in der Anschlussliste (verkabelung.md, W12–W15).', 11.5,
              GRAU),
         text(24, 76, 'Der Stecker ab Werk (schwarz · grün · blau · rot) '
              'passt, wie er ist: Schwarz oben an 2B. Nur an A Schwarz und '
              'Grün tauschen.', 11.5, GRAU),
         text(24, 94, 'Nur stromlos stecken. Vorher mit dem Ohmmeter: '
              'schwarz–grün und blau–rot je 2–3 Ω, zwischen den Paaren '
              'offen.', 11.5, GRAU)]
    t.append(vz.gruppe(24, 112, shield()))
    t.append(vz.gruppe(506, 112, achsen(Q)))
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
