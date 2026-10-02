#!/usr/bin/env python3
"""Zeichnung: Opferplatte und Fuehrungsfuesse unter dem Gestell.

Von oben das ganze Gestell mit Platte, Arbeitsfeld und den vier Fuessen,
dazu Schnitte durch einen hinteren und einen vorderen Fuss (von rechts) und
durch den Anschlag am linken Ende (von vorn). Alle Masse aus Opferplatte.py,
Portal.py und ToolheadZ.py; die Zeichnung ist massstaeblich und wandert mit
den Parametern.

    python3 tools/opferplatte_zeichnen.py   ->  docs/opferplatte.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, pfeil, de,  # noqa: E402
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld, quer_mass, ORANGE   # noqa: E402
from endschalter_zeichnen import profil_schnitt      # noqa: E402
from notaus_zeichnen import hoch_mass                 # noqa: E402
from opferplatte_check import OPFERPLATTE, SICHERHEIT  # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'opferplatte.svg')
FARBE.update({'holz': ('#ecd6ad', '#9a7442')})
FELD = '#2f5d92'
TIEF = '#b4342f'


def fuss_drauf(f, OL, ow, s, e):
    """Ein Fuss von oben: was nicht unter dem 2060 liegt (Flansch, Innen-
    teil oder Wand mit Boden, Anschlag), rechts mit der Einfuehrschraege."""
    x0, x1 = OL['fuss_x'][e]
    g, aus = OL['fuehrung_y'][s], OL['aus'][s]
    innen = OL['innen_y'][s]
    q_innen = innen[1] if s == 'vorn' else innen[0]   # Innenseite 2060
    t = [f.rect(x0, x1, *OL['flansch_y'][s], 'neu')]
    if e == 'rechts':
        ee = ow('einfuehr')
        t.append(f.poly([(x0, g), (x1 - ee, g), (x1, g + aus * ee),
                         (x1, q_innen), (x0, q_innen)], 'neu'))
    else:
        t.append(f.rect(x0, x1, g, q_innen, 'neu'))
        t.append(f.rect(*OL['anschlag_x'], *OL['anschlag_y'][s], 'neu'))
    if not OL['voll'][s]:          # Wand an der Platte, Boden niedriger
        wy = OL['wand_y'][s]
        t.append(f.linie(x0, wy[1] if s == 'hinten' else wy[0],
                         x1 - (ow('einfuehr') if e == 'rechts' else 0.0),
                         wy[1] if s == 'hinten' else wy[0], ORANGE, 0.7))
    # M5 mit Scheibe aussen am Flansch
    fy = OL['flansch_y'][s]
    ya = fy[1] if aus > 0 else fy[0]
    yb = ya + aus * (ow('m5_scheibe_h') + ow('m5_kopf_h'))
    for mx in OL['m5_x'][e]:
        t.append(f.rect(mx - 4.25, mx + 4.25, ya, yb, 'stahl'))
    return t


def schnitt_fuss(f, OL, ow, s, platte_bis):
    """Schnitt quer durch einen rechten Fuss (Blick von rechts, vorn
    rechts): Profil 2060 mit Nuten, Fuss mit Feder und Flansch, M5 mit
    Scheibe und Hammermutter, die Platte bis `platte_bis`, der Tisch."""
    q0, q1 = OL['quer_y'][s]
    z0, z1 = OL['quer_z']
    tz = OL['tisch_z']
    aus = OL['aus'][s]
    t = [profil_schnitt(f, q0, q1, z0, z1, 'lruo')]
    py = OL['platte_y']
    kante = py[1] if s == 'vorn' else py[0]
    t.append(f.rect(min(kante, platte_bis), max(kante, platte_bis),
                    *OL['platte_z'], 'holz'))
    t.append(f.rect(q0, q1, *OL['fuss_z'], 'neu'))
    t.append(f.rect(*OL['flansch_y'][s], *OL['flansch_z'], 'neu'))
    t.append(f.rect(*OL['feder_y'][s], *OL['feder_z'], 'neu'))
    if OL['voll'][s]:
        t.append(f.rect(*OL['innen_y'][s], *OL['fuss_z'], 'neu'))
    else:
        t.append(f.rect(*OL['wand_y'][s], *OL['fuss_z'], 'neu'))
        t.append(f.rect(*OL['boden_y'][s], tz, tz + ow('boden_t'), 'neu'))
    # M5: Kopf und Scheibe aussen, Schaft durch den Flansch in die Nut,
    # Hammermutter in der Nut
    fy = OL['flansch_y'][s]
    ya = fy[1] if aus > 0 else fy[0]
    zn = OL['nut_seite_z']
    sch = ow('m5_scheibe_h')
    yk = ya + aus * sch
    yk2 = yk + aus * ow('m5_kopf_h')
    aussen = q1 if aus > 0 else q0
    spitze = yk - aus * OL['m5_schraube']       # Laenge ab Kopfauflage
    t += [f.rect(min(ya, yk), max(ya, yk), zn - 5.0, zn + 5.0, 'stahl'),
          f.rect(min(yk, yk2), max(yk, yk2), zn - 4.25, zn + 4.25, 'stahl'),
          f.rect(min(yk, spitze), max(yk, spitze), zn - 2.5, zn + 2.5,
                 'stahl'),
          f.rect(min(aussen - aus * 1.8, aussen - aus * 5.8),
                 max(aussen - aus * 1.8, aussen - aus * 5.8), zn - 5.0,
                 zn + 5.0, 'messing')]
    return t


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    ow, OL = om.w, om.lage()
    R = OL['R']
    px, py, pz = OL['platte_x'], OL['platte_y'], OL['platte_z']
    top = pz[1]
    tz = OL['tisch_z']
    tief = TL['zc_min'] + TL['schlitten_unten_rel']   # Toolhead, Z unten
    frei = min(tw('traeger_z_unten'), TL['z_schiene_z0']) - top - SICHERHEIT
    fx0, fx1, fy0, fy1 = (ow('feld_x0'), ow('feld_x1'), ow('feld_y0'),
                          ow('feld_y1'))

    t = [text(24, 30, 'Opferplatte und Führungsfüße unter dem Gestell '
              '(Opferplatte.py Rev. {})'.format(om.REVISION), 14, TEXT,
              fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Spanplatte '
              '{} × {} × {} mm [v]; die Füße sind so hoch, wie die Platte '
              'dick ist: Ihre Oberfläche liegt, wo bisher der Tisch '
              'war.'.format(de(ow('platte_l'), 0), de(ow('platte_b'), 0),
                            de(ow('platte_dicke'), 1)), 9, GRAU)]

    # ---- Feld 1: von oben, vorn unten ---------------------------------------
    f1 = Feld(250, 100, (-335.0, 350.0), (-272.0, 240.0), 1.0,
              b_runter=True)
    inhalt = [f1.rect(*px, *py, 'holz')]
    for s in om.SEITEN:
        for e in om.ENDEN:
            inhalt += fuss_drauf(f1, OL, ow, s, e)
    for s in om.SEITEN:
        inhalt.append(f1.rect(*OL['quer_x'], *OL['quer_y'][s], 'profil',
                              fill_opacity='0.92'))
    for sx in (-1, 1):
        inhalt.append(f1.rect(sx * R - 10.0, sx * R + 10.0, *OL['rahmen_y'],
                              'profil', fill_opacity='0.45',
                              stroke_dasharray='4 3'))
    inhalt.append(f1.rect(fx0, fx1, fy0, fy1, 'holz', fill='none',
                          stroke=FELD, stroke_dasharray='6 3',
                          stroke_width='1.1'))
    xa_a = (OL['fuss_x']['rechts'][0] + OL['fuss_x']['rechts'][1]) / 2.0
    ys = (OL['anschlag_y']['vorn'][0] + OL['anschlag_y']['vorn'][1]) / 2.0
    inhalt += [f1.linie(xa_a, -268.0, xa_a, 236.0, BLAU, 0.8, '10 3 2 3'),
               f1.linie(OL['quer_x'][0] - 30.0, ys, -215.0, ys, BLAU, 0.8,
                        '10 3 2 3')]
    t += f1.ausschnitt('drauf', inhalt)
    for a, b, s_ in ((xa_a + 4.0, -262.0, 'A'), (xa_a + 4.0, 228.0, 'A'),
                     (-215.0, ys - 4.0, 'B')):
        xx, yy = f1.px(a, b)
        t.append(text(xx, yy, s_, 9.5, BLAU, fett=True, halo=True))
    t += f1.rahmen('Von oben (vorn unten)')
    xa, ya = f1.px(px[1] + 4.0, py[0] + 60.0)
    t += [linie(xa, ya, xa + 34, ya, ORANGE, 1.6),
          pfeil(xa + 38, ya, 1, 0, ORANGE),
          text(xa + 2, ya - 7, 'herausziehen', 8.5, ORANGE, fett=True,
               halo=True)]
    hl, hr = OL['fuss_x']['links'], OL['fuss_x']['rechts']
    t += f1.spalte([
        (-150.0, OL['quer_y']['hinten'][0] + 10.0, 'hinteres 2060'),
        ((hl[0] + hl[1]) / 2.0, OL['flansch_y']['hinten'][0],
         'Fuß hinten links:\nFlansch mit 2 × M5 außen'),
        (OL['anschlag_x'][1], OL['anschlag_y']['hinten'][1] - 3.0,
         'Anschlag (links, hinten\nund vorn)'),
        (-R, 100.0, '2040 links\n(liegt darüber)'),
        (-150.0, -40.0, 'Opferplatte, Spanplatte\n{} × {} × {} mm'.format(
            de(ow('platte_l'), 0), de(ow('platte_b'), 0),
            de(ow('platte_dicke'), 1))),
        (fx0, 60.0, 'Arbeitsfeld {} × {} mm\n(Strahl, gestrichelt)'.format(
            de(fx1 - fx0, 0), de(fy1 - fy0, 0))),
        ((hl[0] + hl[1]) / 2.0, OL['flansch_y']['vorn'][1],
         'Fuß vorn links'),
        (-150.0, OL['quer_y']['vorn'][0] + 10.0, 'vorderes 2060')],
        f1.ox - 12, 'end', abstand=30.0)
    t += f1.spalte([
        ((hr[0] + hr[1]) / 2.0, OL['flansch_y']['hinten'][0],
         'Fuß hinten rechts'),
        (R, 100.0, '2040 rechts (darüber)'),
        (hr[1] - 1.0, OL['fuehrung_y']['hinten'] + 2.0,
         'Einführschräge {} mm'.format(de(ow('einfuehr'), 0))),
        (px[1] - 3.0, py[0] + 60.0, 'steht {} mm über:\nhier fassen'.format(
            de(OL['platte_ueber'], 0))),
        (hr[1] - 1.0, OL['fuehrung_y']['vorn'] - 2.0,
         'Führung, {} mm Luft\nje Seite'.format(de(ow('platte_spiel'), 1))),
        (OL['m5_x']['rechts'][1], OL['flansch_y']['vorn'][1] + 3.0,
         'M5×{} + Scheibe in\nHammermutter'.format(
             de(OL['m5_schraube'], 0)))],
        f1.ox + f1.breite + 12, 'start', abstand=30.0)
    t += quer_mass(f1, px[0], px[1], OL['quer_y']['vorn'][1] + 14.0,
                   '{} mm'.format(de(px[1] - px[0], 0)), dy=12)
    t += hoch_mass(f1, px[1] + 16.0, py[0], py[1], '{} mm'.format(
        de(py[1] - py[0], 0)))
    t += quer_mass(f1, fx0, fx1, fy0 + 12.0, '{} mm'.format(
        de(fx1 - fx0, 0)), dy=12)

    # ---- Feld 2: Schnitt durch den hinteren rechten Fuss --------------------
    sz = 3.0
    zb = (tz - 8.0, OL['quer_z'][1] + 6.0)
    yh = (OL['flansch_y']['hinten'][0] - 14.0, py[0] + 18.0)
    f2 = Feld(250, f1.oy + f1.hoehe + 110, yh, zb, sz)
    inhalt = schnitt_fuss(f2, OL, ow, 'hinten', yh[1] + 5.0)
    inhalt += [f2.linie(yh[0] - 5, tz, yh[1] + 5, tz, GRAU, 1.4),
               f2.linie(OL['quer_y']['hinten'][1], tief, yh[1] + 5, tief,
                        TIEF, 1.0, '5 3')]
    t += f2.ausschnitt('hinten', inhalt)
    t += f2.rahmen('Schnitt A–A: Fuß hinten rechts (von rechts)')
    t += f2.spalte([
        (OL['quer_y']['hinten'][0] + 3.0, OL['quer_z'][1] - 10.0,
         'hinteres 2060'),
        (OL['nut_unten_y']['hinten'], OL['feder_z'][1] - 0.5,
         'Feder in der\nunteren Nut'),
        (OL['flansch_y']['hinten'][0] - 4.0, OL['nut_seite_z'] + 3.0,
         'M5×{} + Scheibe,\nHammermutter in der\nunteren Seitennut'.format(
             de(OL['m5_schraube'], 0))),
        (OL['flansch_y']['hinten'][0] + 2.0, tz + 30.0, 'Flansch außen'),
        (yh[0] + 4.0, tz, 'Tisch')],
        f2.ox - 12, 'end', abstand=30.0)
    t += f2.spalte([
        (yh[1] - 5.0, tief, 'Toolhead, Z ganz unten'),
        (py[0] + 6.0, pz[1] - 4.0, 'Opferplatte'),
        (OL['wand_y']['hinten'][0] + 3.0, tz + 18.0,
         'Führungswand, {} mm\nLuft zur Platte'.format(
             de(ow('platte_spiel'), 1))),
        (OL['boden_y']['hinten'][0] + 20.0, tz + 2.0, 'Boden {} mm'.format(
            de(ow('boden_t'), 0)))],
        f2.ox + f2.breite + 12, 'start', abstand=30.0)
    t += hoch_mass(f2, yh[1] - 3.0, top, tief, '{} mm'.format(
        de(tief - top, 1)), anker='end')
    t += hoch_mass(f2, OL['quer_y']['hinten'][1] + 4.0, tz, top,
                   '{} mm'.format(de(top - tz, 1)))

    # ---- Feld 3: Schnitt durch den vorderen rechten Fuss --------------------
    yv = (py[1] - 16.0, OL['flansch_y']['vorn'][1] + 14.0)
    f3 = Feld(f2.ox + f2.breite + 260, f2.oy, yv, zb, sz)
    inhalt = schnitt_fuss(f3, OL, ow, 'vorn', yv[0] - 5.0)
    inhalt += [f3.linie(yv[0] - 5, tz, yv[1] + 5, tz, GRAU, 1.4),
               f3.linie(yv[0] - 5, tief, OL['quer_y']['vorn'][0] - 3.0, tief,
                        TIEF, 1.0, '5 3')]
    t += f3.ausschnitt('vorn', inhalt)
    t += f3.rahmen('Schnitt A–A: Fuß vorn rechts')
    t += f3.spalte([
        (yv[0] + 4.0, pz[1] - 4.0, 'Opferplatte'),
        (OL['innen_y']['vorn'][0] + 3.0, tz + 12.0,
         'Innenteil voll\n({} mm breit)'.format(de(
             OL['innen_y']['vorn'][1] - OL['innen_y']['vorn'][0], 1))),
        (yv[0] + 6.0, tief, 'Toolhead, Z ganz unten:\nam vorderen Wegende '
         '3 mm\nvor dem 2060')],
        f3.ox - 12, 'end', abstand=34.0)
    t += f3.spalte([
        (OL['quer_y']['vorn'][1] - 3.0, OL['quer_z'][1] - 10.0,
         'vorderes 2060'),
        (OL['flansch_y']['vorn'][1] + 4.0, OL['nut_seite_z'] - 3.0,
         'M5 von vorn'),
        (OL['flansch_y']['vorn'][1] - 2.0, tz + 30.0, 'Flansch')],
        f3.ox + f3.breite + 12, 'start', abstand=30.0)

    # ---- Feld 4: Schnitt durch den Anschlag (von vorn) ----------------------
    xa4 = (OL['quer_x'][0] - 18.0, OL['fuss_x']['links'][1] + 30.0)
    f4 = Feld(f2.ox, f2.oy + f2.hoehe + 100, xa4, (tz - 8.0, top + 22.0),
              sz)
    inhalt = [f4.rect(*OL['anschlag_x'], *OL['anschlag_z'], 'neu'),
              f4.rect(px[0], xa4[1] + 5.0, *pz, 'holz'),
              f4.linie(xa4[0] - 5, tz, xa4[1] + 5, tz, GRAU, 1.4)]
    t += f4.ausschnitt('anschlag', inhalt)
    t += f4.rahmen('Schnitt B–B: Anschlag links (von vorn, Y {})'.format(
        de(ys, 0, True)))
    t += f4.spalte([
        (OL['anschlag_x'][0] + 2.0, OL['anschlag_z'][1] - 4.0,
         'Anschlag {} × {} mm, {} mm unter der\nOberfläche; sitzt am '
         'Fuß vorn links,\nder vor der Schnittebene liegt'.format(
             de(ow('anschlag_t'), 0), de(ow('anschlag_h'), 0),
             de(top - OL['anschlag_z'][1], 0))),
        (OL['quer_x'][0] - 10.0, tz, 'Tisch')],
        f4.ox - 12, 'end', abstand=30.0)
    t += f4.spalte([
        (px[0] + 20.0, top - 6.0, 'Platte, links am Anschlag')],
        f4.ox + f4.breite + 12, 'start', abstand=30.0)

    # ---- Zahlen und Legende -------------------------------------------------
    tx = f4.ox + f4.breite + 230
    ty = f4.oy + 4
    zeilen = [
        ('Platte', 'Spanplatte {} × {} × {} mm [v], ≈ {} kg'.format(
            de(ow('platte_l'), 0), de(ow('platte_b'), 0),
            de(ow('platte_dicke'), 1),
            de((px[1] - px[0]) * (py[1] - py[0]) * (pz[1] - pz[0]) * 0.65
               / 1e6, 1))),
        ('', 'X {} bis {}: links am Anschlag, rechts {} mm über dem '
         'Gestell'.format(de(px[0], 0, True), de(px[1], 0, True),
                          de(OL['platte_ueber'], 0))),
        ('', 'Y {} bis {}: mittig unter dem Arbeitsfeld'.format(
            de(py[0], 1, True), de(py[1], 1, True))),
        ('Arbeitsfeld', '{} × {} mm; in Y je Seite {} mm Platte darüber '
         'hinaus'.format(
            de(fx1 - fx0, 0), de(fy1 - fy0, 0), de(fy0 - py[0], 1))),
        ('Höhe', 'Oberfläche Z {} = Unterkante der 2060 = bisher der '
         'Tisch'.format(de(top, 0, True))),
        ('', 'Werkstück bis {} mm ({} mm unter dem Toolhead frei)'.format(
            de(frei, 0), de(SICHERHEIT, 0))),
        ('', 'Toolhead mit Z ganz unten: {} mm über Platte und '
         'Füßen'.format(de(tief - top, 1))),
        ('Füße', '{} mm lang, {} mm hoch; der Tisch liegt jetzt {} mm '
         'tiefer'.format(de(ow('fuss_l'), 0), de(OL['fuss_h'], 1),
                         de(OL['fuss_h'], 1))),
        ('Befestigung', 'je Fuß 2 × M5×{} + Scheibe, Hammermuttern in der '
         'unteren Seitennut'.format(de(OL['m5_schraube'], 0))),
        ('Druck', 'PETG, Unterseite aufs Bett, keine Stützen, 4 Teile'),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 78, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu (PETG)'),
                                  ('holz', 'Opferplatte'),
                                  ('profil', 'Aluprofil'),
                                  ('stahl', 'Schrauben'),
                                  ('messing', 'Hammermutter'),
                                  ('hinten', 'hinter der Schnittebene'))):
        xx = tx + (i % 3) * 150
        yy = ly + (i // 3) * 18
        t.append(rect_px(xx, yy, xx + 14, yy + 9, art))
        t.append(text(xx + 19, yy + 8, s, 8.5))
    yy = ly + 40
    t += [linie(tx, yy + 4.5, tx + 16, yy + 4.5, FELD, 1.1, '6 3'),
          text(tx + 21, yy + 8, 'Arbeitsfeld', 8.5),
          linie(tx + 150, yy + 4.5, tx + 166, yy + 4.5, TIEF, 1.0, '5 3'),
          text(tx + 171, yy + 8, 'tiefster Punkt des Toolheads', 8.5)]

    W = int(max(f1.ox + f1.breite + 220, f3.ox + f3.breite + 220,
                tx + 480))
    H = int(max(f4.oy + f4.hoehe + 30, yy + 30))
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
