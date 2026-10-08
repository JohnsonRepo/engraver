#!/usr/bin/env python3
"""Zeichnung der Kabelhalter: links der Schnitt am linken 2040 mit
Hammermutter, Schraube und den Kabeln des vollsten Abschnitts so, wie sie in
die Rinne fallen; rechts die Plaetze an beiden 2040 mit allem, was dort am
Rahmen sitzt. Masse, Plaetze und Kabel kommen aus fusion/Kabelhalter,
Portal.py und tools/verkabelung.py ueber tools/kabelhalter_check.py.

    python3 tools/kabelhalter_zeichnen.py   ->  docs/kabelhalter.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import el, text, TEXT, GRAU, BLAU       # noqa: E402
import kabelhalter_check as kc                                # noqa: E402
import verkabelung_zeichnen as vz                             # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'kabelhalter.svg')

W, H = 1000, 640
ALU = ('#e9ecef', '#868e96')
PETG = ('#d0e2f5', '#2f5d92')
STAHL = ('#adb5bd', '#495057')
RAHMEN = ('#f1f3f5', '#adb5bd')
TEIL = ('#fff4e6', '#d9480f')
MOTORKABEL = '#343a40'


def vieleck(punkte, fill, rand, b=1.2):
    return el('polygon', {'points': vz.punkte_text(punkte), 'fill': fill,
                          'stroke': rand, 'stroke-width': b,
                          'stroke-linejoin': 'round'})


def massketten(x0, y0, x1, y1, s, gr=9.5, seite=1, abstand=12.0):
    """Masslinie mit Text in der Mitte; waagerecht oder senkrecht."""
    t = []
    if abs(y1 - y0) < 0.01:
        y = y0 + seite * abstand
        t += [vz.linie([(x0, y0), (x0, y + 3 * seite)], GRAU, 0.6),
              vz.linie([(x1, y1), (x1, y + 3 * seite)], GRAU, 0.6),
              vz.linie([(x0, y), (x1, y)], GRAU, 0.8)]
        t.append(text((x0 + x1) / 2.0, y + (12 if seite > 0 else -4), s, gr,
                      GRAU, 'middle', halo=True))
    else:
        x = x0 + seite * abstand
        t += [vz.linie([(x0, y0), (x + 3 * seite, y0)], GRAU, 0.6),
              vz.linie([(x1, y1), (x + 3 * seite, y1)], GRAU, 0.6),
              vz.linie([(x, y0), (x, y1)], GRAU, 0.8)]
        t.append(text(x + 4 * seite, (y0 + y1) / 2.0 + 3.5, s, gr, GRAU,
                      'start' if seite > 0 else 'end', halo=True))
    return t


def kabel_farben(s):
    """[(d, Fuellfarbe, Rand)] der Kabel eines Abschnitts, Reihenfolge wie
    kabelhalter_check.packen (dickstes zuerst, sonst wie in der Liste)."""
    z = []
    for lt in s['leitungen']:
        if lt['art'].startswith('Litzen'):
            for ad, (_, d) in zip(lt['adern'], kc.kabel(lt)):
                f = vz.ADERFARBE.get(ad[1], GRAU)
                z.append((d, f, vz.ADERRAND.get(ad[1], '#343a40'), lt['nr']))
        else:
            for _, d in kc.kabel(lt):
                z.append((d, MOTORKABEL, '#000000', lt['nr']))
    return sorted(z, key=lambda k: -k[0])


def schnitt(A):
    """Querschnitt am linken 2040: aussen links, Profil rechts (innen
    abgebrochen), Beschriftung rechts daneben. Lokale Koordinaten: Ursprung
    = Aussenflaeche auf Hoehe der Nutmitte."""
    km, KL = A['km'], A['KL']
    kw = km.w
    s = 9.0                                   # px je mm

    def p(a, z):
        return (-a * s, -z * s)

    t = []
    # Profil: unterer, aeusserer Teil des 2040, oben und innen abgebrochen
    unten, oben, innen = KL['unterkante'], 15.0, -12.0
    t.append(vieleck([p(0, unten), p(innen, unten), p(innen, oben),
                      p(0, oben)], *ALU))
    h0 = (kw('rahmen_b') - 2.0 * kw('nut_oben')) / 2.0
    h1, h2 = kw('nut_b') / 2.0, kw('nut_kammer_b') / 2.0
    tv, tt, tk = kw('nut_v_t'), kw('nut_t'), kw('nut_kammer_t')
    nut = [(0, h0), (-tv, h1), (-tt, h1), (-tt, h2), (-tk, h2), (-tk, -h2),
           (-tt, -h2), (-tt, -h1), (-tv, -h1), (0, -h0)]
    t.append(vieleck([p(a, z) for a, z in nut], '#ffffff', ALU[1], 1.0))
    zick = [p(innen, oben)]
    for k in range(1, 9):
        zick.append(p(innen + (0.5 if k % 2 else -0.5),
                      oben - k * (oben - unten) / 8.0))
    t.append(vz.linie(zick, ALU[1], 1.0))
    t.append(vz.linie([p(0, oben), p(innen, oben)], '#ffffff', 2.0))
    t.append(vz.linie([p(0.3, oben + 0.4), p(innen / 2, oben - 0.6),
                       p(innen - 0.3, oben + 0.4)], ALU[1], 1.0))
    # Hammermutter, Schraube
    hq = kw('nut_kammer_b') / 2.0 - 0.1
    t.append(vieleck([p(-tt - 0.1, hq), p(-tk + 0.1, hq), p(-tk + 0.1, -hq),
                      p(-tt - 0.1, -hq)], *STAHL))
    ta = kw('anlage_t')
    # Halter, darueber die Schraube (der Schnitt geht durch ihre Achse)
    t.append(vieleck([p(a, z) for a, z in KL['querschnitt']], *PETG, b=1.6))
    t.append(vieleck([p(ta, 2.5), p(ta - kw('m5_l'), 2.5),
                      p(ta - kw('m5_l'), -2.5), p(ta, -2.5)], *STAHL))
    k0, k1 = KL['kopf_a']
    r = kw('m5_kopf_d') / 2.0
    t.append(vieleck([p(k0, r), p(k1, r), p(k1, -r), p(k0, -r)], *STAHL))
    # Kabel des vollsten Abschnitts, so wie sie hineinfallen
    voll = max(A['ab'], key=lambda x: sum(d * d for _, d in x['kabel']))
    lage = kc.packen(KL, [d for _, d in voll['kabel']])
    for (a, z, d), (_, f, rd, _) in zip(lage, kabel_farben(voll)):
        t.append(vz.kreis(*p(a, z), d / 2.0 * s, f, rd, 0.8))
    # Bezugslinien bis in die Beschriftung
    xr = p(innen, 0)[0] + 14                  # Spalte rechts
    tw = A['PL']['ytr_wand_z'][0] - KL['nut_z']
    t.append(vz.linie([p(KL['a'][1] + 0.5, tw), (xr - 4, p(0, tw)[1])],
                      '#d9480f', 1.0, '4 3'))
    t += vz.zeilen(xr, p(0, tw)[1] - 3, ['Wand der Träger Y', 'endet hier'],
                   9.5, '#d9480f', 12)
    t.append(vz.linie([p(KL['a'][1] + 0.5, unten), (xr - 4, p(0, unten)[1])],
                      GRAU, 0.7, '2 3'))
    t.append(text(xr, p(0, unten)[1] + 13, 'Unterkante 2040', 9.5, GRAU))

    def zeiger(ziel, y, zeilen_, farbe=TEXT):
        """Beschriftung rechts mit Linie zum Teil."""
        u = [vz.linie([(xr - 4, y - 4), ziel], GRAU, 0.6)]
        u += vz.zeilen(xr, y, zeilen_, 10, farbe, 12)
        u.append(vz.kreis(*ziel, 1.8, GRAU))
        return u
    t += zeiger(p(-(tt + tk) / 2.0, hq - 1.0), p(0, 9.5)[1],
                ['Hammermutter M5', '(Nut 6)'])
    t += zeiger(p(-kw('feder_t') / 2.0, 2.7), p(0, 4.0)[1],
                ['Feder {} × {}'.format(kc.de(kw('feder_b'), 1),
                                        kc.de(kw('feder_t'), 1)),
                 'in der Nutöffnung'])
    t += zeiger(p(-1.0, -1.2), p(0, -1.6)[1],
                ['M5×{} ohne'.format(kc.de(kw('m5_l'))), 'Scheibe'])
    t.append(text(*p(innen / 2.0, oben - 2.6), '2040', 11, GRAU, 'middle',
                  fett=True))
    # Masse
    a_w = KL['wand_a'][0]
    zb, ko = KL['kanal_z']
    t += massketten(*p(ta, KL['z'][0]), *p(a_w, KL['z'][0]),
                    'Rinne {} × {} mm, oben {} mm offen'.format(
                        kc.de(kw('kanal_b')), kc.de(kw('kanal_h')),
                        kc.de(KL['oeffnung'])), seite=1, abstand=16)
    t += massketten(*p(KL['a'][1], zb), *p(KL['a'][1], ko),
                    kc.de(kw('kanal_h')), seite=-1, abstand=-10)
    t += massketten(*p(0, KL['z'][1]), *p(ta, KL['z'][1]),
                    kc.de(ta, 1), seite=-1, abstand=10)
    la = (KL['lippe_a'][0] + KL['wand_a'][0]) / 2.0
    t += [text(*p(la + 2.5, ko + 2.4), 'Lippe', 9.5, GRAU, 'middle'),
          vz.linie([p(la + 1.2, ko + 1.7), p(la, ko - 0.2)], GRAU, 0.6)]
    # Legende unter dem Schnitt
    nrn = ', '.join(lt['nr'] for lt in voll['leitungen'])
    fg = (100.0 * sum(math.pi * d * d / 4.0 for _, d in voll['kabel'])
          / KL['kanal_flaeche'])
    x0 = p(KL['a'][1], 0)[0]
    t += vz.zeilen(x0, p(0, KL['z'][0])[1] + 50, [
        'Im Boden neben der Anlage ein Fenster für einen Kabelbinder.',
        'Kabel {}: {}, so wie sie hineinfallen —'.format(voll['name'], nrn),
        'schwarz die Motorkabel mit Schlauch (Ø{} angenommen),'.format(
            kc.de(kc.KABEL_D['Motorkabel'][0], 1)),
        'farbig die Litzen einzeln. Füllgrad {} %.'.format(kc.de(fg))],
        10, GRAU, 13)
    return t


def streifen(A, seite, breite):
    """Seitenansicht einer 2040 von aussen: hinten links, vorn rechts."""
    PL = A['PL']
    y0, y1 = PL['rahmen_y']
    s = breite / (y1 - y0)

    def x(y):
        return (y - y0) * s
    t = []
    zt = 34.0                                   # Hoehe 40 mm -> Streifen
    t.append(vz.rechteck(0, 0, breite, zt, *RAHMEN, 1.0, 2))
    t.append(vz.linie([(0, zt * 0.75), (breite, zt * 0.75)], RAHMEN[1], 1.0,
                      '5 3'))
    for n in ('hinten', 'vorn'):
        a, b = PL['quer_y_' + n]
        t.append(vz.rechteck(x(a), zt, x(b) - x(a), 22, *RAHMEN, 1.0, 1))
        t.append(text((x(a) + x(b)) / 2.0, zt + 15, '2060', 9, GRAU,
                      'middle'))
    teile = A['teile'][seite]
    for q in teile:
        if q.name.startswith('2060') or q.name.startswith('Fahne'):
            continue
        if q.name.startswith('Kettenwanne Y'):
            if 'Lasche' in q.name:
                continue
            t.append(vz.rechteck(x(q.y[0]), -9, x(q.y[1]) - x(q.y[0]), 7,
                                 '#f8f9fa', '#adb5bd', 0.8, 1))
            t.append(text(x((q.y[0] + q.y[1]) / 2.0), -12, 'Wanne Y '
                          '(darüber)', 9, GRAU, 'middle'))
            continue
        if 'Arm' in q.name:
            continue
        t.append(vz.rechteck(x(q.y[0]), zt * 0.5, x(q.y[1]) - x(q.y[0]),
                             zt * 0.5, *TEIL, 0.8, 1))
    namen = {'Winkel': 'Winkel', 'Traeger': 'Träger', 'Halter_Y': 'Halter_Y',
             'Y-Motorhalter': 'Motor'}
    gesehen = set()
    for q in teile:
        for k, v in namen.items():
            if q.name.startswith(k) and 'Arm' not in q.name:
                ym = x((q.y[0] + q.y[1]) / 2.0)
                if k == 'Winkel' or (k, round(ym)) not in gesehen:
                    gesehen.add((k, round(ym)))
                    if k == 'Y-Motorhalter':
                        t.append(text(breite, zt * 0.5 - 3, v, 8.5,
                                      '#d9480f', 'end'))
                    elif k != 'Winkel':
                        t.append(text(ym, zt * 0.5 - 3, v, 8.5, '#d9480f',
                                      'middle'))
    if seite < 0:
        xe = x(A['EL']['kabel_links_y'])
        t += [vz.linie([(xe, zt + 30), (xe, zt + 2)], GRAU, 1.0),
              text(xe - 4, zt + 44, 'aus dem Gehäuse', 9, GRAU, 'start')]
        t.append(el('polygon', {'points': vz.punkte_text(
            [(xe - 3.5, zt + 7), (xe + 3.5, zt + 7), (xe, zt + 1)]),
            'fill': GRAU}))
    hb = A['km'].w('kh_b') / 2.0
    for ab in A['ab']:
        if ab['seite'] != seite:
            continue
        for nm, y in zip(ab['namen'], ab['plaetze']):
            t.append(vz.rechteck(x(y - hb), zt * 0.62, 2 * hb * s,
                                 zt * 0.38 + 9, *PETG, 1.2, 1))
            t.append(text(x(y), zt + 22, nm, 11, BLAU, 'middle', fett=True))
            t.append(text(x(y), zt + 35, kc.bezug(PL, y).split(' mm')[0],
                          9.5, GRAU, 'middle'))
    return t


def main():
    A = kc.alles()
    PL = A['PL']
    t = [text(24, 36, 'Kabelhalter für die untere Seitennut der 2040', 19,
              TEXT, fett=True),
         text(24, 58, 'Außen an der 2040, Feder in der Nutöffnung, M5×10 in '
              'einer Hammermutter. Die Kabel liegen in der Rinne darunter, '
              'unter den Wänden der Träger Y durch.', 11.5, GRAU),
         text(24, 76, 'Links und rechts derselbe Halter (um 180° gedreht). '
              'Druck: Querschnitt flach, Seite mit der Fase aufs Bett, PETG, '
              'ohne Stützen.', 11.5, GRAU)]
    # Feld 1: Schnitt
    t += [vz.rechteck(24, 96, 452, 520, '#ffffff', '#d0d7de', 1.0, 8),
          vz.kreis(46, 119, 13, BLAU),
          text(46, 124, '1', 14, '#ffffff', 'middle', fett=True),
          text(68, 124.5, 'Schnitt am linken 2040', 14.5, TEXT, fett=True)]
    t.append(vz.gruppe(236, 288, schnitt(A)))
    # Feld 2: Plaetze
    t += [vz.rechteck(492, 96, 484, 520, '#ffffff', '#d0d7de', 1.0, 8),
          vz.kreis(514, 119, 13, BLAU),
          text(514, 124, '2', 14, '#ffffff', 'middle', fett=True),
          text(536, 124.5, 'Plätze, von außen gesehen', 14.5, TEXT,
               fett=True)]
    bs = 440.0
    for i, (seite, titel) in enumerate(((-1, 'linkes 2040'),
                                        (1, 'rechtes 2040'))):
        y = 186 + 196 * i
        t += [text(514, y - 26, titel, 12.5, TEXT, fett=True),
              text(514 + bs, y - 26, 'hinten ← → vorn', 10, GRAU, 'end')]
        t.append(vz.gruppe(514, y, streifen(A, seite, bs)))
    hinten = PL['quer_y_hinten']
    t += vz.zeilen(514, 550, [
        'Zahlen: Mitte des Halters in mm vor der Vorderseite des hinteren',
        '2060 (L1: hinter seiner Rückseite). Orange: belegt (Winkel, Träger',
        'der Wanne Y, Halter_Y, Y-Motorhalter), {} mm Luft.'.format(
            kc.de(kc.LUFT)),
        'Liste und Kabel: docs/kabelhalter.md.'], 10, GRAU, 13)
    assert hinten
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
