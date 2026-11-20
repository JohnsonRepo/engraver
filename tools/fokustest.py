#!/usr/bin/env python3
"""Fokustest als CNCjs-Makro (docs/fokustest.md).

Brennt eine Reihe kurzer Linien, jede eine Stufe tiefer in Z. Die
duennste, dunkelste Linie zeigt den Fokus. Alles relativ (G91) zur
Position, an der der Kopf beim Start steht: Der Kopf steht ueber der
rechten vorderen Ecke einer freien Flaeche, grob scharfgestellt. Die
Linien laufen nach links und nach hinten, rechts die hoechste, links die
tiefste Z-Stufe. Die lange Linie liegt auf der Starthoehe, mittellange
auf jedem halben Millimeter. Am Ende steht der Kopf wieder auf dem Start.

Z faehrt dabei nur abwaerts, von der hoechsten Stufe Schritt fuer Schritt
nach unten; so liegt jede Stufe auf derselben Seite des Spiels der
Spindel.

    python3 tools/fokustest.py            # schreibt die Makros in pi/cncrc.json
    python3 tools/fokustest.py --pruefen  # prueft nur, ob sie dort stimmen
    python3 tools/fokustest.py --zeigen   # gibt die Makros zum Einfuegen aus

Eine schon eingerichtete ~/.cncrc auf dem Pi aendert pi/einrichten.sh
nicht; dort die Makros in CNCjs von Hand anlegen (--zeigen).
"""

import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
CNCRC = os.path.join(HIER, '..', 'pi', 'cncrc.json')

# Linien: Abstand nach links, Laengen nach hinten (mm)
ABSTAND = 2.0
LAENGE = 10.0          # jede Linie
LAENGE_HALB = 12.5     # auf jedem halben Millimeter
LAENGE_NULL = 15.0     # auf der Starthoehe

# Brennen: wie die Materialprobe auf Spanplatte (S/F >= 0,2 brennt schwarz)
S = 400                # 40 % bei $30=1000
F = 2000               # mm/min

MAKROS = [
    # (Name, Bereich +- mm, Schritt mm)
    ('Fokustest grob (±1 mm)', 1.0, 0.2),
    ('Fokustest fein (±0,5 mm)', 0.5, 0.1),
]

EPS = 1e-9


def stufen(bereich, schritt):
    """Anzahl Schritte je Seite. Bereich muss ein Vielfaches des Schritts sein."""
    if not (0.05 - EPS <= schritt <= 1.0 + EPS):
        raise ValueError('Schritt %.3f mm: erlaubt 0,05 bis 1 mm' % schritt)
    if not (schritt - EPS <= bereich <= 5.0 + EPS):
        raise ValueError('Bereich %.3f mm: erlaubt ein Schritt bis 5 mm' % bereich)
    n = bereich / schritt
    if abs(n - round(n)) > 1e-6:
        raise ValueError('Bereich %.3f mm ist kein Vielfaches des Schritts %.3f mm'
                         % (bereich, schritt))
    n = int(round(n))
    if 2 * n + 1 > 41:
        raise ValueError('%d Linien sind zu viele (hoechstens 41)' % (2 * n + 1))
    return n


def laenge(z):
    """Linienlaenge fuer die Z-Stufe z (mm relativ zur Starthoehe)."""
    if abs(z) < EPS:
        return LAENGE_NULL
    if abs(z / 0.5 - round(z / 0.5)) < 1e-6:
        return LAENGE_HALB
    return LAENGE


def fmt(x):
    s = '%.3f' % x
    return '0.000' if s == '-0.000' else s


def makro(bereich, schritt, s=S, f=F):
    """G-Code des Makros als Text (Zeilen mit \\n)."""
    if not (1 <= s <= 1000):
        raise ValueError('S %d: erlaubt 1 bis 1000' % s)
    if not (100 <= f <= 6000):
        raise ValueError('F %d: erlaubt 100 bis 6000 mm/min' % f)
    n = stufen(bereich, schritt)
    z = [(n - i) * schritt for i in range(2 * n + 1)]       # rechts hoch -> links tief
    zeilen = [
        '; Fokustest: %d Linien, Z %s bis %s mm um die Starthoehe, Schritt %s'
        % (2 * n + 1, fmt(z[0]), fmt(z[-1]), fmt(schritt)),
        '; Start: Kopf grob scharf ueber der rechten vorderen Ecke einer freien',
        '; Flaeche, %d x %d mm nach links und hinten. Rechts hoch, links tief.'
        % (round(2 * n * ABSTAND + 2), round(LAENGE_NULL + 2)),
        'M5',
        'G21',
        'G91',
        'G0 Z%s' % fmt(z[0]),
        'M4 S%d' % s,
    ]
    for i, zi in enumerate(z):
        if i:
            zeilen.append('G0 Z%s' % fmt(-schritt))
            zeilen.append('G0 X%s' % fmt(-ABSTAND))
        l = laenge(zi)
        zeilen.append('G1 Y%s F%d' % (fmt(l), f))
        zeilen.append('G0 Y%s' % fmt(-l))
    zeilen += [
        'M5',
        'G0 Z%s' % fmt(-z[-1]),
        'G0 X%s' % fmt(2 * n * ABSTAND),
        'G90',
    ]
    return '\n'.join(zeilen)


def alle():
    return [{'name': name, 'content': makro(b, s)} for name, b, s in MAKROS]


def cncrc_text(daten):
    t = json.dumps(daten, indent=2, ensure_ascii=False) + '\n'
    # wie von Hand geschrieben: die Baudraten in einer Zeile
    return re.sub(r'\[\s*(\d+)\s*\]', r'[\1]', t)


def cncrc_neu(text):
    """pi/cncrc.json mit den Fokustest-Makros (ersetzt alte Fassungen)."""
    daten = json.loads(text)
    makros = [m for m in daten.get('macros', [])
              if not m.get('name', '').startswith('Fokustest')]
    daten['macros'] = makros + alle()
    return cncrc_text(daten)


def main(argv):
    if '--zeigen' in argv:
        for m in alle():
            print('=== %s ===\n%s\n' % (m['name'], m['content']))
        return 0
    with open(CNCRC, encoding='utf-8') as d:
        alt = d.read()
    neu = cncrc_neu(alt)
    if '--pruefen' in argv:
        if alt == neu:
            print('pi/cncrc.json: Fokustest-Makros aktuell')
            return 0
        print('pi/cncrc.json: Fokustest-Makros veraltet, '
              'python3 tools/fokustest.py ausfuehren')
        return 1
    if alt != neu:
        with open(CNCRC, 'w', encoding='utf-8') as d:
            d.write(neu)
        print('pi/cncrc.json: Fokustest-Makros geschrieben')
    else:
        print('pi/cncrc.json: unveraendert')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
