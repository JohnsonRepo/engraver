#!/usr/bin/env python3
"""Selbsttest der Gravur-Skripte, ohne Maschine und ohne Pi.

Erzeugt Text, SVG, Bilder und einen Materialtest in einem Temp-Ordner,
spielt jede Datei durch gcode_check und prueft dazu:

  - jede Datei: G21, G90, G54 am Anfang, M5 am Ende, kein Z, keine FEHL,
    Brennen nur mit M4, nur innerhalb des Werkstuecks, nur ASCII
  - Text: Versalhoehe stimmt, Gravur mittig
  - SVG: weisser Hintergrund zaehlt nicht, weisser Stern radiert den Kreis
  - Bild: alle vier Arten, Schwellwert brennt das schwarze Feld
  - Materialtest: je Feld die richtige Kombination S/F
  - Pruefung findet Fehler: Werkstueck zu klein, Z, fehlendes F, M5 fehlt

    python3 selbsttest.py

Exit-Code 0 = alles bestanden.
"""

import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import formen as FO  # noqa: E402
import gcode_check as GC  # noqa: E402

FEHLER = []


def pruefe(bed, text):
    if not bed:
        FEHLER.append(text)
    print('  %s %s' % ('ok  ' if bed else 'FEHL', text))


def gravur(tmp, *args):
    pfad = os.path.join(tmp, 'g%d.gc' % len(os.listdir(tmp)))
    r = subprocess.run([sys.executable, os.path.join(HIER, 'gravur.py')] + list(args) + ['-o', pfad],
                       capture_output=True, text=True)
    return r, pfad


def grundregeln(pfad, werkstueck, name):
    text = open(pfad, encoding='ascii').read()
    code = [z for z in text.splitlines() if z and not z.startswith(';')]
    bew, info = GC.lesen(text)
    b, zahlen = GC.pruefen(bew, info, werkstueck, 'vorn-rechts', 1.0, None, None, None, False, True)
    pruefe(code[:3] == ['G21', 'G90', 'G54'], '%s: beginnt mit G21, G90, G54' % name)
    pruefe(info['ende_spindel'] == 'M5', '%s: endet mit M5' % name)
    pruefe(not any(abs(m[5] - m[2]) > 1e-9 for m in bew), '%s: kein Z' % name)
    pruefe(not b.fehler, '%s: Pruefung ohne FEHL %s' % (name, b.fehler or ''))
    pruefe(all(m[12] == 'M4' for m in bew if m[9]), '%s: brennt nur mit M4' % name)
    pruefe(all(len(z) <= GC.LINIE_MAX for z in code), '%s: Zeilen kurz genug' % name)
    return bew, zahlen


def main():
    tmp = tempfile.mkdtemp(prefix='gravur_test_')

    print('Text')
    r, p = gravur(tmp, 'text', 'HEH', '--hoehe', '10', '--werkstueck', '100x50', '--material', 'spanplatte')
    pruefe(r.returncode == 0, 'text: Exit 0 %s' % r.stderr.strip())
    bew, z = grundregeln(p, (100, 50), 'text')
    rb = z['rahmen']
    pruefe(abs((rb[3] - rb[2]) - 10.0) < 0.15, 'Versalhoehe 10 mm (%.2f)' % (rb[3] - rb[2]))
    pruefe(abs((rb[0] + rb[1]) / 2 + 50) < 0.2 and abs((rb[2] + rb[3]) / 2 - 25) < 0.2,
           'mittig auf dem Werkstueck')
    ys = sorted({round(m[1], 3) for m in bew if m[9]})
    pruefe(all(abs((b - a) - 0.1) < 1e-3 for a, b in zip(ys, ys[1:])), 'Zeilenabstand 0,1 mm')

    print('SVG')
    svg = os.path.join(tmp, 'logo.svg')
    with open(svg, 'w') as d:
        d.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100mm">'
                '<rect width="100" height="100" fill="#fff"/>'
                '<circle cx="50" cy="50" r="40" fill="#000"/>'
                '<circle cx="50" cy="50" r="15" style="fill:white"/></svg>')
    r, p = gravur(tmp, 'svg', svg, '--breite', '40', '--werkstueck', '60x60', '--material', 'spanplatte')
    pruefe(r.returncode == 0, 'svg: Exit 0 %s' % r.stderr.strip())
    bew, z = grundregeln(p, (60, 60), 'svg')
    rb = z['rahmen']
    pruefe(abs((rb[1] - rb[0]) - 40) < 0.3, 'Breite aus dem Kreis, nicht aus dem Hintergrund (%.1f)'
           % (rb[1] - rb[0]))
    mx, my = (rb[0] + rb[1]) / 2, (rb[2] + rb[3]) / 2
    innen = [m for m in bew if m[9] and abs(m[1] - my) < 2 and
             min(m[0], m[3]) < mx < max(m[0], m[3])]
    pruefe(not innen, 'weisser Kreis in der Mitte brennt nicht')

    print('Bild')
    png = os.path.join(tmp, 'bild.png')
    im = Image.new('L', (200, 100), 255)
    dr = ImageDraw.Draw(im)
    dr.rectangle([20, 20, 79, 79], fill=0)
    for x in range(100, 200):
        dr.line([x, 0, x, 99], fill=int(255 * (x - 100) / 100))
    im.save(png)
    for art in ('schwellwert', 'dither', 'graustufen', 'linien'):
        r, p = gravur(tmp, 'bild', png, '--art', art, '--breite', '40', '--werkstueck', '60x40',
                      '--material', 'spanplatte', '--nicht-zuschneiden')
        pruefe(r.returncode == 0, 'bild %s: Exit 0 %s' % (art, r.stderr.strip()))
        bew, z = grundregeln(p, (60, 40), 'bild %s' % art)
        if art == 'schwellwert':
            x0 = z['rahmen'][0]
            mitte = [m for m in bew if m[9] and min(m[0], m[3]) <= x0 + 8 <= max(m[0], m[3])]
            pruefe(len(mitte) > 50, 'schwarzes Feld brennt (%d Zeilen)' % len(mitte))
        if art == 'graustufen':
            pruefe(len({m[7] for m in bew if m[9]}) > 5, 'mehrere Leistungsstufen')

    print('Materialtest')
    r, p = gravur(tmp, 'materialtest', '--leistung', '20,60,100', '--vorschub', '3000,1000',
                  '--werkstueck', '60x50', '--s-schrift', '500', '--f-schrift', '1500', '--intervall', '0.2')
    pruefe(r.returncode == 0, 'materialtest: Exit 0 %s' % r.stderr.strip())
    bew, z = grundregeln(p, (60, 50), 'materialtest')
    kombis = set(z['kombis'])
    soll = {(s, f) for s in (200, 600, 1000) for f in (3000, 1000)} | {(500, 1500)}
    pruefe(kombis == soll, 'Felder S200/600/1000 x F3000/1000, Schrift S500 F1500')

    print('Pruefung findet Fehler')
    r, p = gravur(tmp, 'text', 'Viel zu breit', '--hoehe', '20', '--werkstueck', '40x40', '--s', '300', '--f', '2000')
    pruefe(r.returncode == 2 and 'groesser als das Werkstueck' in r.stderr, 'zu grosse Gravur abgelehnt')
    schlecht = 'G21\nG90\nM4 S300\nG1 X-10 Y10\nG0 Z-3\nG1 X-60 Y10 F1000\n'
    bew, info = GC.lesen(schlecht)
    b, _ = GC.pruefen(bew, info, (40, 40))
    f = ' | '.join(b.fehler)
    pruefe('ohne F' in f, 'fehlendes F erkannt')
    pruefe('Z-Fahrten' in f, 'Z erkannt')
    pruefe('nicht aus' in f, 'fehlendes M5 erkannt')
    pruefe('ueber das Werkstueck' in f, 'Brennen ausserhalb des Werkstuecks erkannt')

    print('Planer')
    t = GC.dauer([(0, 0, 0, 100, 0, 0, 'G1', 0, 3000, False, False, 1, 'M5')], GC.M.grenzen())
    soll = 2 * (50 / 500) + (100 - 2 * 2.5) / 50
    pruefe(abs(t[0] - soll) < 1e-6, '100 mm mit F3000, a 500: %.3f s' % t[0])

    print('Formen')
    ring = FO.form([np.array([[0, 0], [10, 0], [10, 10], [0, 10]])], [True])
    loch = FO.form([np.array([[3, 3], [7, 3], [7, 7], [3, 7]])], [True], 'hell')
    st = FO.zeilen_fuellen([ring, loch], [5.0])[0]
    pruefe(st == [(0.0, 3.0), (7.0, 10.0)], 'Maler-Modell: hell radiert dunkel %s' % st)
    pruefe(math.isclose(FO._bogen(0, 0, 5, 5, 0, 0, 1, 10, 0, 0.01)[-1][0], 10), 'SVG-Bogen endet am Ziel')

    shutil.rmtree(tmp, ignore_errors=True)
    print('\n%s' % ('Alle Pruefungen bestanden.' if not FEHLER else '%d Fehler.' % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
