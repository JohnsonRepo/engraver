#!/usr/bin/env python3
"""Zeichnung: Spannmittel auf der Opferplatte.

Von oben die hintere linke Ecke der Platte mit Anschlagwinkel, einem
Beispielwerkstueck, zwei Exzentern und vier Niederhaltern; dazu Schnitte
durch einen Niederhalter und durch den Anschlag, beide mit der Hoehe des
Toolheads, und der Exzenter im Detail. Alle Masse aus Spannmittel.py,
Opferplatte.py und ToolheadZ.py; die Zeichnung ist massstaeblich und
wandert mit den Parametern.

    python3 tools/spannmittel_zeichnen.py   ->  docs/spannmittel.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, pfeil, de,  # noqa: E402
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld, quer_mass, ORANGE   # noqa: E402
from notaus_zeichnen import hoch_mass                 # noqa: E402
from opferplatte_zeichnen import bogen, FELD, TIEF    # noqa: E402
from spannmittel_check import SPANNMITTEL             # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'spannmittel.svg')
FARBE.update({'werkstueck': ('#f7ecd6', '#a8783a')})


def exzenter_drauf(f, sw, ex, mit_achse=True):
    """Exzenter von oben: Scheibe, Hebel, Kopf der Schraube."""
    (cx, cy), (px, py) = ex['mitte'], ex['achse']
    t = [f.poly(ex['hebel'], 'neu'), f.kreis(cx, cy, sw('ex_r'), 'neu')]
    if mit_achse:
        t.append(f.kreis(px, py, sw('sch_kopf_d') / 2.0, 'stahl'))
    return t


def niederhalter_drauf(f, sw, nh):
    """Niederhalter von oben: Steg (die Ferse liegt darunter), Kopf."""
    (x, y, _) = nh['steg']
    return [f.rect(*x, *y, 'neu'),
            f.kreis(*nh['schraube'], sw('sch_kopf_d') / 2.0, 'stahl')]


def schraube_schnitt(f, sw, SL, u, z_oben):
    """Spanplattenschraube im Schnitt: Senkkopf in der Senkung, Schaft bis
    zur Spitze. u: Lage quer (Schnittachse), z_oben: Oberseite des Teils."""
    zk = z_oben - SL['kopf_tiefer']
    rk, rs = sw('sch_kopf_d') / 2.0, 1.5
    zu = zk - (rk - rs)
    return [f.poly([(u - rk, zk), (u + rk, zk), (u + rs, zu), (u - rs, zu)],
                   'stahl'),
            f.rect(u - rs, u + rs, zk - sw('sch_l'), zu, 'stahl')]


def senkung_schnitt(f, sw, SL, u, z_oben, z_unten):
    """Bohrung mit 90-Grad-Senkung im Schnitt (weiss ausgespart)."""
    rs, rl = sw('senk_d') / 2.0, sw('sch_loch') / 2.0
    zu = z_oben - SL['senk_tief']
    return [f.poly([(u - rs, z_oben), (u + rs, z_oben), (u + rl, zu),
                    (u - rl, zu)], 'neu', fill='#ffffff', stroke='none'),
            f.rect(u - rl, u + rl, z_unten, zu, 'neu', fill='#ffffff',
                   stroke='none')]


def main():
    TL = bauraum.modul_laden().lage()
    om = bauraum.modul_laden(os.path.join(os.path.dirname(SPANNMITTEL), '..',
                                          'Opferplatte', 'Opferplatte.py'),
                             'opferplatte')
    OL = om.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    sw, SL = sm.w, sm.lage()
    z0 = SL['z0']
    frei = TL['zc_min'] + TL['schlitten_unten_rel'] - OL['platte_z'][1]
    xi, yi = SL['aw_ecke']
    wx, wy, wz = SL['wst_x'], SL['wst_y'], SL['wst_z']
    t_bsp = sw('nh_t')
    px_, py_ = SL['platte_x'], SL['platte_y']
    (hx, hy), (lx, ly) = SL['aw_hinten'], SL['aw_links']
    nh = {n['name'].rsplit('_', 1)[1]: n for n in SL['nh']}
    ex = {e['name'].rsplit('_', 1)[1]: e for e in SL['ex']}

    t = [text(24, 30, 'Spannmittel auf der Opferplatte (Spannmittel.py Rev. '
              '{})'.format(sm.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Anschlag '
              'hinten links als Nullpunkt, Exzenter schieben das Werkstück '
              'in die Ecke, Niederhalter halten dünne Platten flach; alles '
              'flach genug für den Toolhead.', 9, GRAU)]

    # ---- Feld 1: von oben, vorn unten -------------------------------------
    f1 = Feld(250, 100, (px_[0] - 8.0, ex['rechts']['hebel'][1][0] + 16.0),
              (py_[0] - 8.0, ex['vorn']['hebel'][1][1] + 9.0), 2.0,
              b_runter=True)
    inhalt = [f1.rect(px_[0], px_[1], py_[0], py_[1], 'holz'),
              f1.rect(sw('feld_x0'), sw('feld_x1'), sw('feld_y0'),
                      sw('feld_y1'), 'holz', fill='none', stroke=FELD,
                      stroke_dasharray='6 3', stroke_width='1.1'),
              f1.rect(*wx, *wy, 'werkstueck'),
              f1.rect(*hx, *hy, 'neu'), f1.rect(*lx, *ly, 'neu')]
    inhalt += [f1.kreis(x, y, sw('sch_kopf_d') / 2.0, 'stahl')
               for x, y in SL['aw_schrauben']]
    for e in SL['ex']:
        inhalt += exzenter_drauf(f1, sw, e)
    for n in SL['nh']:
        inhalt += niederhalter_drauf(f1, sw, n)
    # Schnittlinien A (Niederhalter vorn) und B (Anschlag, hintere Schraube)
    xa, xb = nh['vorn']['s'], SL['aw_schrauben'][1][0]
    inhalt += [f1.linie(xa, wy[1] - 22.0, xa, wy[1] + 24.0, BLAU, 0.8,
                        '10 3 2 3'),
               f1.linie(xb, py_[0] - 6.0, xb, yi + 16.0, BLAU, 0.8,
                        '10 3 2 3')]
    t += f1.ausschnitt('drauf', inhalt)
    for a, b, s_ in ((xa + 3.0, wy[1] + 22.0, 'A'), (xb + 3.0, yi + 15.0,
                                                      'B')):
        xx, yy = f1.px(a, b)
        t.append(text(xx, yy, s_, 9.5, BLAU, fett=True, halo=True))
    t += f1.rahmen('Von oben: hintere linke Ecke der Platte (vorn unten)')
    t += f1.spalte([
        (lx[0] + 2.0, ly[1] - 6.0, 'Anschlagwinkel, fest\n{} mm hoch, '
         '3 Schrauben'.format(de(sw('aw_h'), 0))),
        (xi, yi, 'Innenecke = Nullpunkt,\n{} mm im Arbeitsfeld'.format(
            de(sw('aw_rand'), 0))),
        (sw('feld_x0'), yi + 40.0, 'Arbeitsfeld\n(Strahl, gestrichelt)'),
        (px_[0] + 20.0, -60.0, 'Opferplatte'),
        (nh['links']['schraube'][0], nh['links']['schraube'][1],
         'Niederhalter links,\nneben dem Schenkel')],
        f1.ox - 12, 'end', abstand=30.0)
    t += f1.spalte([
        (nh['hinten']['schraube'][0], nh['hinten']['schraube'][1],
         'Niederhalter hinten: passt\nhinter die Werkstückkante'),
        (ex['rechts']['achse'][0] + 2.0, ex['rechts']['achse'][1],
         'Exzenter rechts: schiebt\nnach links an den Schenkel'),
        (nh['rechts']['schraube'][0], nh['rechts']['schraube'][1],
         'Niederhalter rechts'),
        (wx[1] - 30.0, wy[1] - 25.0,
         'Beispielwerkstück\n{} × {} × {} mm'.format(
             de(sw('wst_l'), 0), de(sw('wst_b'), 0), de(t_bsp, 0))),
        (nh['vorn']['schraube'][0], nh['vorn']['schraube'][1],
         'Niederhalter vorn ({} mm)'.format(de(t_bsp, 0))),
        (ex['vorn']['achse'][0] + 2.0, ex['vorn']['achse'][1],
         'Exzenter vorn: schiebt\nnach hinten an den Schenkel')],
        f1.ox + f1.breite + 12, 'start', abstand=30.0)

    # ---- Feld 2: Schnitt A-A durch den Niederhalter vorn ------------------
    s2 = 8.0
    n = nh['vorn']
    ya = (wy[1] - 14.0, wy[1] + sw('nh_ende') + 8.0)
    za = (z0 - 22.0, z0 + t_bsp + frei + 5.0)
    f2 = Feld(250, f1.oy + f1.hoehe + 110, ya, za, s2)
    zs = n['steg'][2]
    us = n['schraube'][1]
    inhalt = [f2.rect(ya[0] - 5, ya[1] + 5, za[0] - 5, z0, 'holz'),
              f2.rect(ya[0] - 5, wy[1], *wz, 'werkstueck'),
              f2.rect(*n['steg'][1], *zs, 'neu'),
              f2.rect(*n['ferse'][1], *n['ferse'][2], 'neu')]
    inhalt += senkung_schnitt(f2, sw, SL, us, zs[1], zs[0])
    inhalt += schraube_schnitt(f2, sw, SL, us, zs[1])
    zt = z0 + t_bsp + frei
    inhalt.append(f2.linie(ya[0] - 5, zt, ya[1] + 5, zt, TIEF, 1.0, '5 3'))
    t += f2.ausschnitt('schnitt_a', inhalt)
    t += f2.rahmen('Schnitt A–A: Niederhalter an der Vorderkante (von '
                   'links, vorn rechts)')
    t += hoch_mass(f2, n['steg'][1][1] - 1.5, zs[1], zt, '{} mm'.format(
        de(zt - zs[1], 1)), anker='end')
    t += hoch_mass(f2, n['steg'][1][1] + 2.0, zs[0], zs[1], '{} mm'.format(
        de(sw('nh_d'), 1)))
    t += hoch_mass(f2, ya[0] + 3.0, z0, wz[1], '{} mm'.format(
        de(t_bsp, 0)))
    t += f2.spalte([
        (ya[0] + 8.0, zt, 'Toolhead, Fokus auf dem\nWerkstück: mindestens '
         '{} mm\ndarüber'.format(de(frei, 1))),
        (ya[0] + 8.0, z0 + t_bsp / 2.0, 'Werkstück'),
        (ya[0] + 8.0, z0 - 10.0, 'Opferplatte')],
        f2.ox - 12, 'end', abstand=34.0)
    t += f2.spalte([
        (wy[1] - sw('nh_lippe') / 2.0, zs[1] - 0.5, 'Lippe {} mm auf dem '
         'Rand'.format(de(sw('nh_lippe'), 0))),
        (us + 1.0, zs[1] - SL['kopf_tiefer'] - 0.5,
         'Spanplattenschraube\n3,0 × {} Senkkopf'.format(de(sw('sch_l'),
                                                             0))),
        (n['ferse'][1][1] - 1.0, z0 + 1.0, 'Ferse {} mm hoch,\nsteht auf der '
         'Platte'.format(de(t_bsp, 0))),
        (us + 0.8, z0 - 8.0, 'fasst {} mm in\nder Platte'.format(
            de(sw('sch_l') - (t_bsp + sw('nh_d') - SL['kopf_tiefer']), 1)))],
        f2.ox + f2.breite + 12, 'start', abstand=30.0)

    # ---- Feld 3: Schnitt B-B durch den Anschlag (hintere Schraube) --------
    yb = (py_[0] - 5.0, yi + 14.0)
    f3 = Feld(f2.ox + f2.breite + 280, f2.oy, yb, za, s2)
    ub = SL['aw_schrauben'][1][1]
    inhalt = [f3.rect(py_[0], yb[1] + 5, za[0] - 5, z0, 'holz'),
              f3.rect(yi, yb[1] + 5, *wz, 'werkstueck'),
              f3.rect(*hy, *SL['aw_z'], 'neu')]
    inhalt += senkung_schnitt(f3, sw, SL, ub, SL['aw_z'][1], z0)
    inhalt += schraube_schnitt(f3, sw, SL, ub, SL['aw_z'][1])
    inhalt += [f3.linie(sw('feld_y0'), za[0] - 5, sw('feld_y0'), za[1] + 5,
                        FELD, 1.1, '6 3'),
               f3.linie(yb[0] - 5, z0 + frei, yb[1] + 5, z0 + frei, TIEF,
                        1.0, '2 3'),
               f3.linie(yb[0] - 5, zt, yb[1] + 5, zt, TIEF, 1.0, '5 3')]
    t += f3.ausschnitt('schnitt_b', inhalt)
    t += f3.rahmen('Schnitt B–B: Anschlagwinkel, hinterer Schenkel')
    t += hoch_mass(f3, hy[0] + 1.5, SL['aw_z'][1], z0 + frei, '{} mm'.format(
        de(z0 + frei - SL['aw_z'][1], 1)))
    t += f3.spalte([
        (py_[0] + 0.5, z0 - 4.0, 'Kante der Opferplatte'),
        (hy[0] + 1.0, SL['aw_z'][1] - 1.0, 'Anschlag {} mm hoch'.format(
            de(sw('aw_h'), 0))),
        (yb[0] + 2.0, z0 + frei, 'Toolhead, Z ganz unten\n(ohne Werkstück)')],
        f3.ox - 12, 'end', abstand=30.0)
    t += f3.spalte([
        (yb[1] - 3.0, zt, 'Toolhead, Fokus auf\n{} mm Material'.format(
            de(t_bsp, 0))),
        (sw('feld_y0') + 0.3, za[1] - 2.0, 'Arbeitsfeld beginnt'),
        (yi + 4.0, z0 + t_bsp / 2.0, 'Werkstück an der\nInnenseite = '
         'Nullpunkt'),
        (yb[1] - 3.0, z0 - 10.0, 'Opferplatte')],
        f3.ox + f3.breite + 12, 'start', abstand=30.0)

    # ---- Feld 4: Exzenter im Detail (von oben) ----------------------------
    e = ex['rechts']
    (cx, cy), (ax, ay) = e['mitte'], e['achse']
    R = sw('ex_r')
    f4 = Feld(250, f2.oy + f2.hoehe + 100, (wx[1] - 14.0,
                                            e['hebel'][1][0] + 8.0),
              (cy - R - 8.0, cy + R + 8.0), 5.0, b_runter=True)
    inhalt = [f4.rect(wx[1] - 20.0, wx[1], cy - R - 20.0, cy + R + 20.0,
                      'werkstueck')]
    inhalt += exzenter_drauf(f4, sw, e)
    inhalt += [f4.linie(cx - 1.5, cy, cx + 1.5, cy, GRAU, 0.8),
               f4.linie(cx, cy - 1.5, cx, cy + 1.5, GRAU, 0.8),
               bogen(f4, (ax, ay), R + 7.0, -75.0, -12.0, ORANGE, 1.4)]
    # Pfeilspitze: im Uhrzeigersinn (von oben), vom Werkstueck weg
    a = math.radians(-12.0)
    rr = R + 7.0
    inhalt.append(pfeil(*f4.px(ax + rr * math.cos(a), ay + rr * math.sin(a)),
                        -math.sin(a), math.cos(a), ORANGE))
    t += f4.ausschnitt('exzenter', inhalt)
    t += f4.rahmen('Exzenter rechts im Detail (von oben)')
    t += quer_mass(f4, wx[1], ax, cy + R + 4.0, '{}–{} mm'.format(
        de(SL['ex_fenster'][0], 0), de(SL['ex_fenster'][1], 0)), dy=12)
    t += f4.spalte([
        (wx[1] - 6.0, cy - 10.0, 'Werkstück'),
        (wx[1] + 0.5, cy, 'gespannt: größter\nRadius am Werkstück')],
        f4.ox - 12, 'end', abstand=30.0)
    t += f4.spalte([
        (cx, cy + 0.5, 'Scheibenmitte'),
        (ax + 1.5, ay - 1.5, 'Schraube {} mm außermittig'.format(
            de(sw('ex_e'), 0))),
        (e['hebel'][1][0] - 3.0, cy - sw('ex_hebel_b') / 2.0 + 1.0,
         'Hebel: im Uhrzeigersinn\nvom Werkstück weg drehen'),
        (cx + R * 0.7, cy + R * 0.7, 'Schraube {}–{} mm neben\ndie Kante: '
         'Spannweg {} mm'.format(de(SL['ex_fenster'][0], 0),
                                 de(SL['ex_fenster'][1], 0),
                                 de(sw('ex_e'), 0)))],
        f4.ox + f4.breite + 12, 'start', abstand=30.0)

    # ---- Zahlen und Legende ------------------------------------------------
    tx = f3.ox - 20
    ty = f4.oy + 4
    zeilen = [
        ('Höhe', 'Toolhead mindestens {} mm über dem Werkstück, mit Z ganz '
         'unten über der Platte'.format(de(frei, 1))),
        ('Anschlag', '{} × {} mm Schenkel, {} mm hoch, Innenecke {} mm im '
         'Feld'.format(de(hx[1] - hx[0], 0), de(ly[1] - ly[0], 0),
                       de(sw('aw_h'), 0), de(sw('aw_rand'), 0))),
        ('Exzenter', 'Ø {}, Schraube {} mm außermittig, {} mm hoch, '
         'selbsthemmend ({}°)'.format(
             de(2.0 * R, 0), de(sw('ex_e'), 0), de(sw('ex_h'), 0),
             de(SL['ex_winkel'], 1))),
        ('Niederhalter', 'je Materialstärke {} mm; Steg {} mm, Lippe {} mm '
         'auf dem Rand'.format('/'.join(de(s_, 0) for s_ in sm.NH_STAERKEN),
                               de(sw('nh_d'), 1), de(sw('nh_lippe'), 0))),
        ('Schrauben', 'Spanplattenschraube 3,0 × {} Senkkopf, ohne '
         'Vorbohren'.format(de(sw('sch_l'), 0))),
        ('Druck', 'PETG, keine Stützen; Niederhalter mit der Oberseite aufs '
         'Bett'),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 78, ty + 10 + i * 15, v, 8.5, TEXT))
    ly_ = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s_) in enumerate((('neu', 'neu (PETG)'),
                                   ('holz', 'Opferplatte'),
                                   ('werkstueck', 'Werkstück'),
                                   ('stahl', 'Schrauben'))):
        xx = tx + (i % 2) * 150
        yy = ly_ + (i // 2) * 18
        t.append(rect_px(xx, yy, xx + 14, yy + 9, art))
        t.append(text(xx + 19, yy + 8, s_, 8.5))
    yy = ly_ + 40
    t += [linie(tx, yy + 4.5, tx + 16, yy + 4.5, FELD, 1.1, '6 3'),
          text(tx + 21, yy + 8, 'Arbeitsfeld', 8.5),
          linie(tx + 150, yy + 4.5, tx + 166, yy + 4.5, TIEF, 1.0, '5 3'),
          text(tx + 171, yy + 8, 'tiefster Punkt des Toolheads', 8.5)]

    W = int(max(f1.ox + f1.breite + 230, f3.ox + f3.breite + 230,
                f4.ox + f4.breite + 230, tx + 520))
    H = int(max(f4.oy + f4.hoehe + 40, yy + 30))
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
