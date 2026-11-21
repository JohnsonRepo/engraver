#!/usr/bin/env python3
"""Zeichnung: Opferplatte zwischen den 2060 und die Anschlaege am linken
Ende.

Von oben das ganze Gestell mit Platte, Arbeitsfeld und den beiden
Anschlaegen, das linke Ende vergroessert, dazu ein Schnitt durch den
hinteren Anschlag in der Ebene einer M5 (Blick von links) und einer durch
die vordere Nase (Blick von vorn). Alle Masse aus Opferplatte.py und
ToolheadZ.py; die Zeichnung ist massstaeblich und wandert mit den
Parametern.

    python3 tools/opferplatte_zeichnen.py   ->  docs/opferplatte.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, pfeil, de,  # noqa: E402
                              el, f1, TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld, quer_mass, ORANGE   # noqa: E402
from endschalter_zeichnen import profil_schnitt      # noqa: E402
from portal_zeichnen import hoch_mass                 # noqa: E402
from opferplatte_check import OPFERPLATTE, SICHERHEIT  # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'opferplatte.svg')
FARBE.update({'holz': ('#ecd6ad', '#9a7442')})
FELD = '#2f5d92'
TIEF = '#b4342f'


def bogen(f, mitte, r, a0, a1, farbe, breite=0.8, strich=None):
    """Kreisbogen um mitte (a, b) mit Radius r von Winkel a0 bis a1 (Grad,
    0 = +a, 90 = +b) als Linienzug. Auch fuer spannmittel_zeichnen.py."""
    n = max(2, int(abs(a1 - a0) / 5.0) + 1)
    pkt = [f.px(mitte[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i
                                                     / (n - 1.0))),
                mitte[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i
                                                     / (n - 1.0))))
           for i in range(n)]
    return el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in pkt),
        'fill': 'none', 'stroke': farbe, 'stroke-width': breite,
        'stroke-dasharray': strich})


def anschlag_drauf(f, OL, ow, s):
    """Ein Anschlag von oben: Flansch aussen am 2060, Endplatte vor der
    Stirnseite, Nase vor dem Plattenende, dazu Scheiben und Koepfe der
    beiden M5 aussen am Flansch."""
    t = [f.rect(*OL['flansch_x'][s], *OL['flansch_y'][s], 'neu'),
         f.rect(*OL['endplatte_x'][s], *OL['endplatte_y'][s], 'neu'),
         f.rect(*OL['nase_x'][s], *OL['nase_y'][s], 'neu')]
    aus = OL['aus'][s]
    ya = OL['auflage_y'][s]
    yk = ya + aus * ow('m5_scheibe_h')
    yb = yk + aus * ow('m5_kopf_h')
    sr, kr = ow('m5_scheibe_d') / 2.0, ow('m5_kopf_d') / 2.0
    for mx in OL['m5_x'][s]:
        t += [f.rect(mx - sr, mx + sr, ya, yk, 'stahl'),
              f.rect(mx - kr, mx + kr, yk, yb, 'stahl')]
    return t


def profile_drauf(f, OL, R, deckend=0.92):
    """Die beiden 2060 und, gestrichelt darueber, die beiden 2040."""
    t = [f.rect(*OL['quer_x'][s], *OL['quer_y'][s], 'profil',
                fill_opacity=str(deckend)) for s in ('vorn', 'hinten')]
    for sx in (-1, 1):
        t.append(f.rect(sx * R - 10.0, sx * R + 10.0, *OL['rahmen_y'],
                        'profil', fill_opacity='0.45',
                        stroke_dasharray='4 3'))
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
    tief = TL['zc_unten'] + TL['schlitten_unten_rel']  # Toolhead, Softlimit
    frei = min(tw('traeger_z_unten'), TL['z_schiene_z0']) - top - SICHERHEIT
    fx0, fx1, fy0, fy1 = (ow('feld_x0'), ow('feld_x1'), ow('feld_y0'),
                          ow('feld_y1'))
    ev, eh = OL['quer_ende']['vorn'], OL['quer_ende']['hinten']

    t = [text(24, 30, 'Opferplatte zwischen den 2060, Anschläge am linken '
              'Ende (Opferplatte.py Rev. {})'.format(om.REVISION), 14, TEXT,
              fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Spanplatte '
              '{} × {} × {} mm [v]; sie liegt wie die Maschine auf dem '
              'Tisch, ohne Spalt zwischen den 2060 (innen {} mm). Nur links '
              'ein Anschlag, um das Profilende herum.'.format(
                  de(ow('platte_l'), 0), de(ow('platte_b'), 0),
                  de(ow('platte_dicke'), 1), de(ow('quer_innen'), 0)), 9,
              GRAU)]

    # ---- Feld 1: von oben, vorn unten ---------------------------------------
    f1 = Feld(250, 100, (-335.0, 345.0), (-262.0, 262.0), 1.0,
              b_runter=True)
    inhalt = [f1.rect(*px, *py, 'holz')]
    for s in om.SEITEN:
        inhalt += anschlag_drauf(f1, OL, ow, s)
    inhalt += profile_drauf(f1, OL, R)
    inhalt.append(f1.rect(fx0, fx1, fy0, fy1, 'holz', fill='none',
                          stroke=FELD, stroke_dasharray='6 3',
                          stroke_width='1.1'))
    t += f1.ausschnitt('drauf', inhalt)
    t += f1.rahmen('Von oben (vorn unten)')
    xa, ya = f1.px(px[1] + 4.0, py[0] + 110.0)
    t += [linie(xa, ya, xa + 34, ya, ORANGE, 1.6),
          pfeil(xa + 38, ya, 1, 0, ORANGE),
          text(xa + 2, ya - 7, 'herausziehen', 8.5, ORANGE, fett=True,
               halo=True)]
    t += f1.spalte([
        (-150.0, OL['quer_y']['hinten'][0] + 10.0, 'hinteres 2060'),
        (OL['flansch_x']['hinten'][0] + 20.0, OL['flansch_y']['hinten'][0],
         'Anschlag_hinten'),
        (-R, 120.0, '2040 links\n(liegt darüber)'),
        (-150.0, -40.0, 'Opferplatte, Spanplatte\n{} × {} × {} mm'.format(
            de(ow('platte_l'), 0), de(ow('platte_b'), 0),
            de(ow('platte_dicke'), 1))),
        (fx0, 60.0, 'Arbeitsfeld {} × {} mm\n(Strahl, gestrichelt)'.format(
            de(fx1 - fx0, 0), de(fy1 - fy0, 0))),
        (OL['flansch_x']['vorn'][0] + 20.0, OL['flansch_y']['vorn'][1],
         'Anschlag_vorn'),
        (-150.0, OL['quer_y']['vorn'][0] + 10.0, 'vorderes 2060')],
        f1.ox - 12, 'end', abstand=30.0)
    t += f1.spalte([
        (R, 120.0, '2040 rechts (darüber)'),
        (OL['quer_x']['vorn'][1] - 5.0, OL['quer_y']['vorn'][0] + 10.0,
         'die 2060 liegen ohne\nSpalt an der Platte\nund führen sie'),
        (px[1] - 3.0, py[0] + 60.0, 'steht {} mm über:\nhier fassen'.format(
            de(OL['platte_ueber'], 0))),
        (px[1] - 3.0, py[1] - 20.0, 'rechts kein Anschlag')],
        f1.ox + f1.breite + 12, 'start', abstand=30.0)
    t += quer_mass(f1, px[0], px[1], OL['quer_y']['vorn'][1] + 30.0,
                   '{} mm'.format(de(px[1] - px[0], 0)), dy=12)
    t += hoch_mass(f1, px[1] + 16.0, py[0], py[1], '{} mm'.format(
        de(py[1] - py[0], 0)), anker='end')
    t += quer_mass(f1, fx0, fx1, fy0 + 12.0, '{} mm'.format(
        de(fx1 - fx0, 0)), dy=12)

    # ---- Feld 2: linkes Ende vergroessert, von oben: hinten und vorn -----
    s2 = 2.5
    x2 = (OL['endplatte_x']['hinten'][0] - 12.0,
          OL['flansch_x']['vorn'][1] + 22.0)
    xm_a = OL['m5_x']['hinten'][0]            # Schnitt A-A durch eine M5
    yb_ = sum(OL['nase_y']['vorn']) / 2.0     # Schnitt B-B durch die Nase
    felder2 = []
    for s, ox in (('hinten', 250), ('vorn', None)):
        if s == 'hinten':
            y2 = (OL['flansch_y'][s][0] - 10.0, OL['nase_y'][s][1] + 22.0)
        else:
            y2 = (OL['nase_y'][s][0] - 22.0, OL['flansch_y'][s][1] + 10.0)
        if ox is None:
            ox = felder2[0].ox + felder2[0].breite + 300
        f2 = Feld(ox, f1.oy + f1.hoehe + 110, x2, y2, s2, b_runter=True)
        felder2.append(f2)
        inhalt = [f2.rect(px[0], x2[1] + 5.0, *py, 'holz')]
        inhalt += anschlag_drauf(f2, OL, ow, s)
        inhalt += profile_drauf(f2, OL, R)
        if s == 'hinten':
            inhalt.append(f2.linie(xm_a, y2[0] + 2.0, xm_a, y2[1] - 2.0,
                                   BLAU, 0.8, '10 3 2 3'))
        else:
            inhalt.append(f2.linie(x2[0] + 2.0, yb_, px[0] + 30.0, yb_, BLAU,
                                   0.8, '10 3 2 3'))
        t += f2.ausschnitt('links_' + s, inhalt)
        marken = ([(xm_a + 1.5, y2[0] + 4.0, 'A'),
                   (xm_a + 1.5, y2[1] - 6.0, 'A')] if s == 'hinten'
                  else [(px[0] + 31.0, yb_ - 1.5, 'B')])
        for a, b, s_ in marken:
            xx, yy = f2.px(a, b)
            t.append(text(xx, yy, s_, 9.5, BLAU, fett=True, halo=True))
        t += f2.rahmen('Linkes Ende {}, von oben (vorn unten)'.format(s))
        q = OL['quer_y'][s]
        t += f2.spalte([
            (OL['endplatte_x'][s][0] + 1.0, sum(OL['endplatte_y'][s]) / 2.0,
             'Endplatte vor der\nStirnseite'),
            (OL['nase_x'][s][0] + 2.0, sum(OL['nase_y'][s]) / 2.0,
             'Nase {} mm dick,\n{} mm vor das\nPlattenende'.format(
                 de(OL['nase_x'][s][1] - OL['nase_x'][s][0], 0),
                 de(ow('anschlag_tief'), 0))),
            (OL['quer_x'][s][0] + 12.0, sum(q) / 2.0,
             '{} 2060: {} mm\nüber das 2040'.format(
                 'hinteres' if s == 'hinten' else 'vorderes',
                 de(ow('quer_ueber_' + s), 0)))],
            f2.ox - 12, 'end', abstand=30.0)
        t += f2.spalte([
            (OL['m5_x'][s][1], OL['auflage_y'][s] + OL['aus'][s] * 4.0,
             'Flansch außen, 2 × M5×{}\n+ Scheibe in Hammer-\nmuttern der '
             'äußeren\nunteren Seitennut'.format(de(OL['m5_schraube'], 0))),
            (-R + 5.0, sum(q) / 2.0, '2040 links\n(darüber)'),
            (px[0] + 30.0, py[0] + 10.0 if s == 'hinten' else py[1] - 10.0,
             'Opferplatte')],
            f2.ox + f2.breite + 12, 'start', abstand=30.0)
    t += quer_mass(felder2[0], eh, ev, OL['nase_y']['hinten'][1] + 12.0,
                   'Versatz {} mm'.format(de(ev - eh, 0)), dy=-6)
    f2 = max(felder2, key=lambda f: f.oy + f.hoehe)

    # ---- Feld 3: Schnitt A-A durch den hinteren Anschlag (von links) -------
    s3 = 3.0
    q0, q1 = OL['quer_y']['hinten']
    y3 = (OL['flansch_y']['hinten'][0] - 14.0, q1 + 28.0)
    z3 = (tz - 8.0, OL['quer_z'][1] + 6.0)
    f3 = Feld(250, f2.oy + f2.hoehe + 110, y3, z3, s3)
    zn = OL['nut_seite_z']
    ya = OL['auflage_y']['hinten']
    yk = ya - ow('m5_scheibe_h')
    yk2 = yk - ow('m5_kopf_h')
    spitze = yk + OL['m5_schraube']
    aussen = OL['aussen']['hinten']
    inhalt = [f3.rect(*OL['endplatte_y']['hinten'], *OL['anschlag_z'],
                      'hinten'),
              profil_schnitt(f3, q0, q1, *OL['quer_z'], 'lruo'),
              f3.rect(q1, y3[1] + 5.0, *pz, 'holz'),
              f3.rect(*OL['flansch_y']['hinten'], *OL['flansch_z'], 'neu'),
              f3.rect(yk2, yk, zn - ow('m5_kopf_d') / 2.0,
                      zn + ow('m5_kopf_d') / 2.0, 'stahl'),
              f3.rect(yk, ya, zn - 5.0, zn + 5.0, 'stahl'),
              f3.rect(yk, spitze, zn - 2.5, zn + 2.5, 'stahl'),
              f3.rect(aussen + 1.8, aussen + 5.8, zn - 5.0, zn + 5.0,
                      'messing'),
              f3.linie(y3[0] - 5, tz, y3[1] + 5, tz, GRAU, 1.4),
              f3.linie(q1, tief, y3[1] + 5, tief, TIEF, 1.0, '5 3')]
    t += f3.ausschnitt('schnitt_a', inhalt)
    t += f3.rahmen('Schnitt A–A: Anschlag_hinten in der Ebene einer M5 '
                   '(von links, vorn rechts)')
    t += f3.spalte([
        (yk2 + 1.0, zn + 3.0, 'M5×{} + Scheibe,\nvon außen'.format(
            de(OL['m5_schraube'], 0))),
        (OL['flansch_y']['hinten'][0] + 2.0, OL['flansch_z'][1] - 3.0,
         'Flansch {} mm, {} mm hoch'.format(de(ow('flansch_t'), 0),
                                           de(ow('flansch_h'), 0))),
        (y3[0] + 4.0, tz, 'Tisch')],
        f3.ox - 12, 'end', abstand=30.0)
    t += f3.spalte([
        (q0 + 4.0, OL['quer_z'][1] - 10.0, 'hinteres 2060'),
        (aussen + 4.0, zn - 3.0, 'Hammermutter in der\näußeren unteren\n'
         'Seitennut'),
        (y3[1] - 5.0, tief, 'Toolhead, Z ganz unten\n(Softlimit $132)'),
        (q1 + 10.0, pz[1] - 4.0, 'Opferplatte, liegt\nam 2060 an'),
        (OL['endplatte_y']['hinten'][1] - 2.0, OL['anschlag_z'][1] - 2.0,
         'Endplatte (dahinter)')],
        f3.ox + f3.breite + 12, 'start', abstand=30.0)
    t += hoch_mass(f3, y3[1] - 3.0, top, tief, '{} mm'.format(
        de(tief - top, 1)), anker='end')

    # ---- Feld 4: Schnitt B-B durch die vordere Nase (von vorn) -------------
    x4 = (OL['endplatte_x']['vorn'][0] - 18.0, px[0] + 40.0)
    z4 = (tz - 8.0, top + 12.0)
    f4 = Feld(f3.ox + f3.breite + 250, f3.oy, x4, z4, s3)
    inhalt = [f4.rect(*OL['nase_x']['vorn'], *OL['anschlag_z'], 'neu'),
              f4.rect(px[0], x4[1] + 5.0, *pz, 'holz'),
              f4.linie(x4[0] - 5, tz, x4[1] + 5, tz, GRAU, 1.4),
              f4.rect(ev, x4[1] + 5.0, OL['quer_z'][0], z4[1] + 5.0,
                      'profil', fill='none', stroke_dasharray='4 3')]
    xp, yp_ = f4.px(px[0] + 26.0, pz[0] + 8.0)
    inhalt += [linie(xp, yp_, xp - 50, yp_, ORANGE, 1.6),
               pfeil(xp - 54, yp_, -1, 0, ORANGE)]
    t += f4.ausschnitt('schnitt_b', inhalt)
    t += f4.rahmen('Schnitt B–B: Nase vorn (von vorn)')
    t += f4.spalte([
        (OL['nase_x']['vorn'][0] + 1.0, OL['anschlag_z'][1] - 3.0,
         'Nase {} × {} mm, {} mm\nunter der Oberfläche'.format(
             de(ow('endplatte_t'), 0), de(ow('anschlag_h'), 0),
             de(top - OL['anschlag_z'][1], 1))),
        (x4[0] + 3.0, tz, 'Tisch')],
        f4.ox - 12, 'end', abstand=30.0)
    t += f4.spalte([
        (ev + 3.0, z4[1] - 3.0, 'vorderes 2060\n(vor der '
         'Schnittebene, gestrichelt)'),
        (px[0] + 20.0, top - 6.0, 'Platte, links an der Nase'),
        (px[0] + 6.0, pz[0] + 8.0, 'Stoß: die Endplatte\ndrückt auf die '
         'Stirnseite')],
        f4.ox + f4.breite + 12, 'start', abstand=30.0)

    # ---- Zahlen und Legende -------------------------------------------------
    tx = f3.ox
    ty = f3.oy + f3.hoehe + 70
    zeilen = [
        ('Platte', 'Spanplatte {} × {} × {} mm [v], ≈ {} kg'.format(
            de(ow('platte_l'), 0), de(ow('platte_b'), 0),
            de(ow('platte_dicke'), 1),
            de((px[1] - px[0]) * (py[1] - py[0]) * (pz[1] - pz[0]) * 0.65
               / 1e6, 1))),
        ('', 'X {} bis {}: links an den Nasen, rechts {} mm über die '
         '2060'.format(de(px[0], 0, True), de(px[1], 0, True),
                       de(OL['platte_ueber'], 0))),
        ('', 'Y {} bis {}: ohne Spalt zwischen den 2060, mittig unter dem '
         'Arbeitsfeld'.format(de(py[0], 1, True), de(py[1], 1, True))),
        ('Höhe', 'Platte und Maschine auf demselben Tisch: Oberfläche Z {}, '
         '{} mm über der Unterkante der 2060'.format(
             de(top, 1, True), de(top - OL['z_2060'], 1))),
        ('', 'Werkstück bis {} mm ({} mm unter dem Toolhead frei)'.format(
            de(frei, 1), de(SICHERHEIT, 0))),
        ('', 'Toolhead mit Z ganz unten (Softlimit $132): {} mm über '
         'der Platte'.format(de(tief - top, 1))),
        ('Anschläge', '2 × PETG, je um das linke Ende eines 2060: Flansch '
         'außen, Endplatte, Nase'),
        ('Befestigung', 'je 2 × M5×{} + Scheibe in Hammermuttern der '
         'äußeren unteren Seitennut'.format(de(OL['m5_schraube'], 0))),
        ('Rahmen', '2060 innen {} mm, links {} / {} mm über das 2040 (Angabe '
         '2026-11-21; Portal.py noch alt)'.format(
             de(ow('quer_innen'), 0), de(ow('quer_ueber_vorn'), 0),
             de(ow('quer_ueber_hinten'), 0))),
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

    W = int(max(f1.ox + f1.breite + 220, f2.ox + f2.breite + 260,
                f4.ox + f4.breite + 240, tx + 620,
                felder2[1].ox + felder2[1].breite + 220))
    H = int(yy + 30)
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
