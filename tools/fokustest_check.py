#!/usr/bin/env python3
"""Pruefung des Fokustests (tools/fokustest.py, pi/cncrc.json).

Spielt jedes Makro durch einen kleinen GRBL-Nachbau im Lasermodus ($32=1):
Der Laser brennt nur bei G1 mit M3/M4 und S > 0, bei G0 und im Stillstand
nicht (M4). Geprueft wird:

1. Nur Linien nach hinten (+Y), jede an eigenem X, rechts hoch, links tief,
   die Stufen genau im Schritt, die Starthoehe und jeder halbe Millimeter
   laenger markiert.
2. Z faehrt zwischen den Linien nur abwaerts, das Feld bleibt links und
   hinter dem Start, am Ende steht der Kopf wieder auf dem Start, der Laser
   ist aus (M5) und G90 gilt wieder.
3. Nichts, was CNCjs in einem Makro anders liest: keine eckigen Klammern
   (Ausdruecke), kein % am Zeilenanfang, nur ASCII im G-Code.
4. pi/cncrc.json enthaelt genau diese Makros, die anderen unveraendert.
5. Unsinnige Werte werden abgelehnt.

    python3 tools/fokustest_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import json
import os
import re
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import fokustest as ft  # noqa: E402

FEHLER = []
EPS = 1e-6


def pruefe(bed, text):
    if not bed:
        FEHLER.append(text)
    print('  %s %s' % ('ok  ' if bed else 'FEHL', text))


def grbl(text):
    """Minimaler GRBL-Nachbau. Gibt Endzustand und gebrannte Strecken."""
    st = {'abs': True, 'bewegung': 'G0', 'spindel': 'M5', 's': 0.0, 'f': 0.0,
          'pos': [0.0, 0.0, 0.0], 'mm': False}
    brennen, z_fahrten = [], []
    for roh in text.split('\n'):
        zeile = re.sub(r';.*', '', roh).strip()            # wie CNCjs
        if not zeile:
            continue
        woerter = re.findall(r'([A-Z])(-?\d+(?:\.\d+)?)', zeile.upper())
        if ''.join(b + w for b, w in woerter) != zeile.replace(' ', '').upper():
            raise ValueError('nicht lesbar: %r' % zeile)
        ziel = list(st['pos'])
        achse = False
        for b, w in woerter:
            v = float(w)
            if b == 'G':
                g = int(v)
                if g in (0, 1):
                    st['bewegung'] = 'G%d' % g
                elif g == 90:
                    st['abs'] = True
                elif g == 91:
                    st['abs'] = False
                elif g == 21:
                    st['mm'] = True
                else:
                    raise ValueError('unerwartet G%d' % g)
            elif b == 'M':
                if int(v) not in (3, 4, 5):
                    raise ValueError('unerwartet M%d' % v)
                st['spindel'] = 'M%d' % int(v)
            elif b == 'S':
                st['s'] = v
            elif b == 'F':
                st['f'] = v
            elif b in 'XYZ':
                i = 'XYZ'.index(b)
                ziel[i] = v if st['abs'] else st['pos'][i] + v
                achse = True
            else:
                raise ValueError('unerwartet %s' % b)
        if achse:
            an = (st['bewegung'] == 'G1' and st['spindel'] in ('M3', 'M4')
                  and st['s'] > 0)
            if an:
                if st['f'] <= 0:
                    raise ValueError('G1 ohne F')
                brennen.append((tuple(st['pos']), tuple(ziel), st['s'], st['f']))
            if abs(ziel[2] - st['pos'][2]) > EPS:
                z_fahrten.append((st['pos'][2], ziel[2], an))
            st['pos'] = ziel
    return st, brennen, z_fahrten


def makro_pruefen(name, bereich, schritt, text):
    print('\n%s' % name)
    st, brennen, z_fahrten = grbl(text)
    n = int(round(bereich / schritt))
    pruefe(len(brennen) == 2 * n + 1, '%d Linien gebrannt' % len(brennen))
    pruefe(all(abs(a[0] - b[0]) < EPS and abs(a[2] - b[2]) < EPS
               and b[1] - a[1] > 0 and abs(a[1]) < EPS for a, b, _, _ in brennen),
           'jede Linie nur nach hinten (+Y), ab derselben vorderen Kante')
    xs = [a[0] for a, _, _, _ in brennen]
    zs = [a[2] for a, _, _, _ in brennen]
    pruefe(len(set(round(x, 6) for x in xs)) == len(xs), 'jede Linie an eigenem X')
    paare = sorted(zip(xs, zs))                              # links -> rechts
    pruefe(all(paare[i + 1][1] - paare[i][1] > 0 for i in range(len(paare) - 1)),
           'rechts hoch, links tief')
    pruefe(all(abs((paare[i + 1][1] - paare[i][1]) - schritt) < EPS
               for i in range(len(paare) - 1)),
           'Stufen genau %.2f mm' % schritt)
    pruefe(abs(max(zs) - bereich) < EPS and abs(min(zs) + bereich) < EPS,
           'Z von +%.2f bis -%.2f mm um die Starthoehe' % (bereich, bereich))
    pruefe(all(abs(x2 - x1 - ft.ABSTAND) < EPS
               for (x1, _), (x2, _) in zip(paare, paare[1:])),
           'Abstand %.1f mm' % ft.ABSTAND)
    laengen = {round(a[2], 6): b[1] - a[1] for a, b, _, _ in brennen}
    lang = [z for z, l in laengen.items() if abs(l - max(laengen.values())) < EPS]
    pruefe(lang == [0.0], 'die laengste Linie liegt auf der Starthoehe')
    halbe = [z for z in laengen if abs(z) > EPS
             and abs(z / 0.5 - round(z / 0.5)) < EPS]
    pruefe(all(abs(laengen[z] - ft.LAENGE_HALB) < EPS for z in halbe)
           and all(abs(laengen[z] - ft.LAENGE) < EPS for z in laengen
                   if abs(z) > EPS and z not in halbe),
           'halbe Millimeter mittellang (%s), die anderen kurz'
           % ', '.join('%+.1f' % z for z in sorted(halbe)) if halbe else
           'keine halben Millimeter im Bereich, die anderen kurz')
    pruefe(all(s == ft.S and f == ft.F for _, _, s, f in brennen),
           'S%d F%d' % (ft.S, ft.F))
    pruefe(not any(an for _, _, an in z_fahrten), 'Z faehrt nie mit Laser')
    zwischen = z_fahrten[1:-1]
    pruefe(all(z2 < z1 for z1, z2, _ in zwischen),
           'zwischen den Linien faehrt Z nur abwaerts')
    alle_pos = [p for a, b, _, _ in brennen for p in (a, b)]
    pruefe(all(p[0] <= EPS and p[1] >= -EPS for p in alle_pos),
           'Feld links und hinter dem Start (%.0f x %.0f mm)'
           % (-min(p[0] for p in alle_pos), max(p[1] for p in alle_pos)))
    pruefe(all(abs(v) < EPS for v in st['pos']), 'am Ende wieder auf dem Start')
    pruefe(st['spindel'] == 'M5' and st['abs'] and st['mm'],
           'am Ende M5, G90, mm')
    zeilen = text.split('\n')
    pruefe(zeilen[[z.strip().startswith(';') for z in zeilen].index(False)] == 'M5',
           'erst M5 (falls „Laserpunkt 1 %“ noch an ist)')
    g = '\n'.join(re.sub(r';.*', '', z) for z in zeilen)
    pruefe('[' not in text and ']' not in text
           and not any(z.lstrip().startswith('%') for z in zeilen),
           'keine CNCjs-Ausdrücke ([...], %)')
    pruefe(all(ord(c) < 128 for c in text), 'nur ASCII')
    pruefe('G0 X' in g and 'G0 Y' in g, 'Fahrten ohne Laser mit G0')


def main():
    for name, bereich, schritt in ft.MAKROS:
        makro_pruefen(name, bereich, schritt, ft.makro(bereich, schritt))

    print('\nWerte')
    for b, s in [(1.0, 0.3), (0.0, 0.1), (1.0, 0.0), (6.0, 1.0), (3.0, 0.05)]:
        try:
            ft.makro(b, s)
            pruefe(False, 'Bereich %.2f, Schritt %.2f abgelehnt' % (b, s))
        except ValueError as f:
            pruefe(True, 'Bereich %.2f, Schritt %.2f abgelehnt: %s' % (b, s, f))
    for s, f in [(0, 2000), (1200, 2000), (400, 50)]:
        try:
            ft.makro(1.0, 0.2, s, f)
            pruefe(False, 'S%d F%d abgelehnt' % (s, f))
        except ValueError:
            pruefe(True, 'S%d F%d abgelehnt' % (s, f))
    pruefe(ft.fmt(-0.0) == '0.000' and ft.fmt(-1e-12) == '0.000', 'keine -0.000')

    print('\npi/cncrc.json')
    with open(ft.CNCRC, encoding='utf-8') as d:
        text = d.read()
    daten = json.loads(text)
    pruefe(ft.cncrc_neu(text) == text,
           'Makros aktuell (sonst python3 tools/fokustest.py)')
    namen = [m['name'] for m in daten['macros']]
    for name, b, s in ft.MAKROS:
        m = [x for x in daten['macros'] if x['name'] == name]
        pruefe(len(m) == 1 and m[0]['content'] == ft.makro(b, s),
               '„%s“ einmal, Inhalt wie erzeugt' % name)
    pruefe(namen[:3] == ['Rahmen', 'Laserpunkt 1 %', 'Laser aus'],
           'Rahmen, Laserpunkt 1 %, Laser aus unverändert vorn')
    pruefe(ft.cncrc_text(daten) == text, 'Format wie von Hand (Baudraten in einer Zeile)')
    r = subprocess.run([sys.executable, os.path.join(HIER, 'fokustest.py'), '--pruefen'],
                       capture_output=True, text=True)
    pruefe(r.returncode == 0, 'fokustest.py --pruefen: %s' % r.stdout.strip())

    print('\n%s' % ('Alle Prüfungen bestanden.' if not FEHLER
                    else '%d Fehler.' % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
