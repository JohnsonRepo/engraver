#!/usr/bin/env python3
"""Zeichnung: Opferplatte mit Anschlag und Fuehrung am Gestell.

Von oben das ganze Gestell mit Platte, Arbeitsfeld, den vier Haltern und
dem Riegel, dazu Schnitte durch einen hinteren und einen vorderen Halter
(Blick von links), durch den Riegel (von links, mit der offenen Lage und
dem Schwenkkreis), laengs seiner Achse (von vorn) und durch den Anschlag am
linken Ende (von vorn). Alle Masse aus Opferplatte.py, Portal.py und
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
from opferplatte_check import (OPFERPLATTE, SICHERHEIT,  # noqa: E402
                               riegel_masse, riegel_ueberstand)

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'opferplatte.svg')
FARBE.update({'holz': ('#ecd6ad', '#9a7442')})
FELD = '#2f5d92'
TIEF = '#b4342f'


def halter_drauf(f, OL, ow, s, e):
    """Ein Halter von oben: innen am 2060 der volle Block (vorn) oder
    Flansch, Boden und Wand (hinten), links der Anschlag, rechts die
    Einfuehrschraege; vorn rechts Endplatte, Ausleger und Lagerbock. Dazu
    die Koepfe der M5 (vorn versenkt, hinten mit Scheibe)."""
    x0, x1 = OL['halter_x'][e]
    g, aus = OL['fuehrung_y'][s], OL['aus'][s]
    innen = OL['innen'][s]
    t = []
    if (s, e) == OL['riegel_an']:  # Ausleger mit dem Lagerbock
        t += [f.rect(*OL['ausleger_x'], *OL['ausleger_y'], 'neu'),
              f.rect(*OL['lager_x'], *OL['lager_y'], 'neu')]
    if e == 'rechts':
        ee, xe = ow('einfuehr'), OL['fuehrung_ende_x'][s]
        pkt = [(x0, g), (xe - ee, g), (xe, g + aus * ee)]
        if xe > x1:                # Endplatte vor dem Ende des 2060
            ey = OL['endplatte_y'][1] if aus > 0 else OL['endplatte_y'][0]
            pkt += [(xe, ey), (x1, ey), (x1, innen)]
        else:
            pkt += [(x1, innen)]
        t.append(f.poly(pkt + [(x0, innen)], 'neu'))
    else:
        t.append(f.rect(x0, x1, g, innen, 'neu'))
        t.append(f.rect(*OL['anschlag_x'], *OL['anschlag_y'][s], 'neu'))
    if not OL['voll'][s]:          # Wand an der Platte, Flansch am 2060
        xr = x1 - (ow('einfuehr') if e == 'rechts' else 0.0)
        for y in (g + aus * ow('wand_t'), innen - aus * ow('flansch_t')):
            t.append(f.linie(x0, y, xr if y != innen else x1, y, ORANGE,
                             0.7))
    # Koepfe der M5 (und Scheibe) auf der Plattenseite
    ya = OL['auflage_y'][s]
    sch = ow('m5_scheibe_h') if OL['m5_scheibe'][s] else 0.0
    yk = ya - aus * sch
    yb = yk - aus * ow('m5_kopf_h')
    r = ow('m5_kopf_d') / 2.0
    for mx in OL['m5_x'][e]:
        if sch:
            t.append(f.rect(mx - ow('m5_scheibe_d') / 2.0,
                            mx + ow('m5_scheibe_d') / 2.0, ya, yk, 'stahl'))
        t.append(f.rect(mx - r, mx + r, yk, yb, 'stahl'))
    return t


def riegel_umriss(OL, ow, offen=False):
    """Umriss des Riegels quer zur Achse (Y, Z): Leiste bis zur Nase, um
    die Achse die halbrunde Nabe. offen: um 180 Grad nach vorn geklappt."""
    (yp, zp), rh = OL['riegel_achse'], ow('riegel_h') / 2.0
    nase = OL['riegel_nase_y']
    pkt = [(nase, zp - rh), (yp, zp - rh)]
    pkt += [(yp + rh * math.cos(math.radians(a)),
             zp + rh * math.sin(math.radians(a))) for a in range(-80, 90, 10)]
    pkt += [(yp, zp + rh), (nase, zp + rh)]
    if offen:
        pkt = [(2.0 * yp - y, 2.0 * zp - z) for y, z in pkt]
    return pkt


def bogen(f, mitte, r, a0, a1, farbe, breite=0.8, strich=None):
    """Kreisbogen um mitte (a, b) mit Radius r von Winkel a0 bis a1 (Grad,
    0 = +a, 90 = +b) als Linienzug."""
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


def riegel_drauf(f, OL, ow):
    """Riegel von oben: zu (Nase vor dem Plattenende), offen gestrichelt,
    dazu Scheibe, Stoppmutter und Schraubenende hinter dem Lagerbock."""
    (yp, _), rx = OL['riegel_achse'], OL['riegel_x']
    rh, rl, _ = riegel_masse(ow, OL)
    x0 = OL['lager_x'][1]
    xs = x0 + ow('m5_scheibe_h')
    xm = xs + ow('m5_mutter_h')
    sr, mr = ow('m5_scheibe_d') / 2.0, ow('m5_sw') / 2.0
    return [f.rect(*rx, OL['riegel_nase_y'], yp + rh, 'neu'),
            f.rect(*rx, yp - rh, yp + rl, 'neu', fill='none', stroke=ORANGE,
                   stroke_dasharray='3 2'),
            f.rect(x0, xs, yp - sr, yp + sr, 'stahl'),
            f.rect(xs, xm, yp - mr, yp + mr, 'stahl'),
            f.rect(xm, xm + riegel_ueberstand(ow, OL), yp - 2.5, yp + 2.5,
                   'stahl')]


def schnitt_halter(f, OL, ow, s, platte_bis):
    """Schnitt quer durch einen rechten Halter in der Ebene einer M5 (Blick
    von links, vorn rechts): Profil 2060 mit Nuten auf dem Tisch, Halter
    (Block mit Senkung oder Flansch, Boden, Wand), M5 mit Kopf auf der
    Plattenseite, Hammermutter in der inneren Seitennut, die Platte bis
    `platte_bis`."""
    q0, q1 = OL['quer_y'][s]
    z0, z1 = OL['quer_z']
    tz = OL['tisch_z']
    aus = OL['aus'][s]
    innen = OL['innen'][s]
    t = [profil_schnitt(f, q0, q1, z0, z1, 'lruo')]
    py = OL['platte_y']
    kante = py[1] if s == 'vorn' else py[0]
    t.append(f.rect(min(kante, platte_bis), max(kante, platte_bis),
                    *OL['platte_z'], 'holz'))
    zn = OL['nut_seite_z']
    if OL['voll'][s]:
        t.append(f.rect(*OL['innen_y'][s], *OL['halter_z'], 'neu'))
        t.append(f.rect(*OL['senk_y'][s], zn - ow('senk_d') / 2.0,
                        zn + ow('senk_d') / 2.0, 'neu', fill='#ffffff'))
    else:
        t.append(f.rect(*OL['wand_y'][s], *OL['halter_z'], 'neu'))
        t.append(f.rect(*OL['boden_y'][s], tz, tz + ow('boden_t'), 'neu'))
        t.append(f.rect(*OL['flansch_y'][s], *OL['flansch_z'], 'neu'))
    # M5: Kopf (und Scheibe) auf der Plattenseite, Schaft durch den Halter
    # in die Nut, Hammermutter in der inneren Seitennut
    ya = OL['auflage_y'][s]
    sch = ow('m5_scheibe_h') if OL['m5_scheibe'][s] else 0.0
    yk = ya - aus * sch
    yk2 = yk - aus * ow('m5_kopf_h')
    spitze = yk + aus * OL['m5_schraube'][s]    # Laenge ab Kopfauflage
    if sch:
        t.append(f.rect(min(ya, yk), max(ya, yk), zn - 5.0, zn + 5.0,
                        'stahl'))
    t += [f.rect(min(yk, yk2), max(yk, yk2), zn - ow('m5_kopf_d') / 2.0,
                 zn + ow('m5_kopf_d') / 2.0, 'stahl'),
          f.rect(min(yk, spitze), max(yk, spitze), zn - 2.5, zn + 2.5,
                 'stahl'),
          f.rect(min(innen + aus * 1.8, innen + aus * 5.8),
                 max(innen + aus * 1.8, innen + aus * 5.8), zn - 5.0,
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
    tief = TL['zc_unten'] + TL['schlitten_unten_rel']  # Toolhead, Softlimit
    frei = min(tw('traeger_z_unten'), TL['z_schiene_z0']) - top - SICHERHEIT
    fx0, fx1, fy0, fy1 = (ow('feld_x0'), ow('feld_x1'), ow('feld_y0'),
                          ow('feld_y1'))

    t = [text(24, 30, 'Opferplatte mit Anschlag und Führung am Gestell '
              '(Opferplatte.py Rev. {})'.format(om.REVISION), 14, TEXT,
              fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Spanplatte '
              '{} × {} × {} mm [v]; sie liegt wie die Maschine auf dem '
              'Tisch, vier Halter innen an den 2060 führen sie. Rechts hält '
              'sie ein Klappriegel.'.format(
                  de(ow('platte_l'), 0), de(ow('platte_b'), 0),
                  de(ow('platte_dicke'), 1)), 9, GRAU)]

    # ---- Feld 1: von oben, vorn unten ---------------------------------------
    f1 = Feld(250, 100, (-335.0, 362.0), (-272.0, 240.0), 1.0,
              b_runter=True)
    inhalt = [f1.rect(*px, *py, 'holz')]
    for s in om.SEITEN:
        for e in om.ENDEN:
            inhalt += halter_drauf(f1, OL, ow, s, e)
    inhalt += riegel_drauf(f1, OL, ow)
    (yp, zp), rx = OL['riegel_achse'], OL['riegel_x']
    rh, rl, rs = riegel_masse(ow, OL)
    xc = (rx[0] + rx[1]) / 2.0               # Schnitt C-C
    inhalt += [f1.linie(xc, OL['riegel_nase_y'] - 14.0, xc,
                        OL['ausleger_y'][1] + 8.0, BLAU, 0.8, '10 3 2 3'),
               f1.linie(OL['quer_x'][1] - 12.0, yp, rx[1] + 26.0, yp, BLAU,
                        0.8, '10 3 2 3')]
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
    xa_a = OL['m5_x']['rechts'][1]           # Schnitt A-A durch eine M5
    ys = (OL['anschlag_y']['vorn'][0] + OL['anschlag_y']['vorn'][1]) / 2.0
    inhalt += [f1.linie(xa_a, -268.0, xa_a, 236.0, BLAU, 0.8, '10 3 2 3'),
               f1.linie(OL['quer_x'][0] - 30.0, ys, -215.0, ys, BLAU, 0.8,
                        '10 3 2 3')]
    t += f1.ausschnitt('drauf', inhalt)
    for a, b, s_ in ((xa_a + 4.0, -262.0, 'A'), (xa_a + 4.0, 228.0, 'A'),
                     (-215.0, ys - 4.0, 'B'),
                     (xc - 3.0, OL['riegel_nase_y'] - 16.0, 'C'),
                     (rx[1] + 20.0, yp - 3.0, 'D')):
        xx, yy = f1.px(a, b)
        t.append(text(xx, yy, s_, 9.5, BLAU, fett=True, halo=True))
    t += f1.rahmen('Von oben (vorn unten)')
    xa, ya = f1.px(px[1] + 4.0, py[0] + 60.0)
    t += [linie(xa, ya, xa + 34, ya, ORANGE, 1.6),
          pfeil(xa + 38, ya, 1, 0, ORANGE),
          text(xa + 2, ya - 7, 'herausziehen', 8.5, ORANGE, fett=True,
               halo=True)]
    hl, hr = OL['halter_x']['links'], OL['halter_x']['rechts']
    t += f1.spalte([
        (-150.0, OL['quer_y']['hinten'][0] + 10.0, 'hinteres 2060'),
        ((hl[0] + hl[1]) / 2.0, OL['flansch_y']['hinten'][1] + 2.0,
         'Anschlag_hinten: Flansch\ninnen am 2060, 2 × M5'),
        (OL['anschlag_x'][1], OL['anschlag_y']['hinten'][1] - 3.0,
         'Anschlag (links, hinten\nund vorn)'),
        (-R, 100.0, '2040 links\n(liegt darüber)'),
        (-150.0, -40.0, 'Opferplatte, Spanplatte\n{} × {} × {} mm'.format(
            de(ow('platte_l'), 0), de(ow('platte_b'), 0),
            de(ow('platte_dicke'), 1))),
        (fx0, 60.0, 'Arbeitsfeld {} × {} mm\n(Strahl, gestrichelt)'.format(
            de(fx1 - fx0, 0), de(fy1 - fy0, 0))),
        ((hl[0] + hl[1]) / 2.0, OL['innen_y']['vorn'][1] - 3.0,
         'Anschlag_vorn: voller\nBlock, M5 versenkt'),
        (-150.0, OL['quer_y']['vorn'][0] + 10.0, 'vorderes 2060')],
        f1.ox - 12, 'end', abstand=30.0)
    t += f1.spalte([
        ((hr[0] + hr[1]) / 2.0, OL['flansch_y']['hinten'][1] + 2.0,
         'Führung_hinten'),
        (R, 100.0, '2040 rechts (darüber)'),
        (hr[1] - 1.0, OL['fuehrung_y']['hinten'] + 2.0,
         'Einführschräge {} mm'.format(de(ow('einfuehr'), 0))),
        (px[1] - 3.0, py[0] + 60.0, 'steht {} mm über:\nhier fassen'.format(
            de(OL['platte_ueber'], 0))),
        (hr[0] + 10.0, OL['fuehrung_y']['vorn'] - 0.5,
         'Führung, {} mm Luft\nje Seite'.format(de(ow('platte_spiel'), 1))),
        (xc, OL['riegel_nase_y'] + 3.0,
         'Riegel zu (C–C, D–D),\noffen nach vorn geklappt\n(gestrichelt)'),
        (OL['endplatte_x'][1] - 1.0, OL['endplatte_y'][1] - 2.0,
         'Endplatte vor dem 2060,\nAusleger mit Lagerbock'),
        (OL['m5_x']['rechts'][0], OL['auflage_y']['vorn'] - 3.0,
         'M5×{} versenkt, Hammer-\nmutter innen im 2060'.format(
             de(OL['m5_schraube']['vorn'], 0)))],
        f1.ox + f1.breite + 12, 'start', abstand=30.0)
    t += quer_mass(f1, px[0], px[1], OL['ausleger_y'][1] + 8.0,
                   '{} mm'.format(de(px[1] - px[0], 0)), dy=12)
    t += hoch_mass(f1, px[1] + 36.0, py[0], py[1], '{} mm'.format(
        de(py[1] - py[0], 0)), anker='end')
    t += quer_mass(f1, fx0, fx1, fy0 + 12.0, '{} mm'.format(
        de(fx1 - fx0, 0)), dy=12)

    # ---- Feld 2: Schnitt durch den hinteren rechten Halter -----------------
    sz = 3.0
    zb = (tz - 8.0, OL['quer_z'][1] + 6.0)
    yh = (OL['quer_y']['hinten'][0] - 8.0, py[0] + 18.0)
    f2 = Feld(250, f1.oy + f1.hoehe + 110, yh, zb, sz)
    inhalt = schnitt_halter(f2, OL, ow, 'hinten', yh[1] + 5.0)
    inhalt += [f2.linie(yh[0] - 5, tz, yh[1] + 5, tz, GRAU, 1.4),
               f2.linie(OL['quer_y']['hinten'][1], tief, yh[1] + 5, tief,
                        TIEF, 1.0, '5 3')]
    t += f2.ausschnitt('hinten', inhalt)
    t += f2.rahmen('Schnitt A–A: Führung_hinten (von links, vorn '
                   'rechts)')
    t += f2.spalte([
        (OL['quer_y']['hinten'][0] + 3.0, OL['quer_z'][1] - 10.0,
         'hinteres 2060'),
        (OL['innen']['hinten'] - 3.0, OL['nut_seite_z'] + 4.0,
         'Hammermutter in der\ninneren unteren\nSeitennut'),
        (yh[0] + 4.0, tz, 'Tisch')],
        f2.ox - 12, 'end', abstand=30.0)
    t += f2.spalte([
        (yh[1] - 5.0, tief, 'Toolhead, Z ganz unten\n(Softlimit $132)'),
        (py[0] + 6.0, pz[1] - 4.0, 'Opferplatte'),
        (OL['wand_y']['hinten'][0] + 3.0, tz + 18.0,
         'Führungswand, {} mm\nLuft zur Platte'.format(
             de(ow('platte_spiel'), 1))),
        (OL['boden_y']['hinten'][0] + 20.0, tz + 2.0, 'Boden {} mm'.format(
            de(ow('boden_t'), 0))),
        (OL['auflage_y']['hinten'] + 4.0, OL['nut_seite_z'],
         'M5×{} + Scheibe durch\nden Flansch innen'.format(
             de(OL['m5_schraube']['hinten'], 0)))],
        f2.ox + f2.breite + 12, 'start', abstand=30.0)
    t += hoch_mass(f2, yh[1] - 3.0, top, tief, '{} mm'.format(
        de(tief - top, 1)), anker='end')
    t += hoch_mass(f2, OL['wand_y']['hinten'][0] - 4.0, tz, top,
                   '{} mm'.format(de(top - tz, 1)))

    # ---- Feld 3: Schnitt durch den vorderen rechten Halter -----------------
    yv = (py[1] - 16.0, OL['quer_y']['vorn'][1] + 10.0)
    f3 = Feld(f2.ox + f2.breite + 260, f2.oy, yv, zb, sz)
    inhalt = schnitt_halter(f3, OL, ow, 'vorn', yv[0] - 5.0)
    inhalt += [f3.linie(yv[0] - 5, tz, yv[1] + 5, tz, GRAU, 1.4),
               f3.linie(yv[0] - 5, tief, OL['quer_y']['vorn'][0] - 3.0, tief,
                        TIEF, 1.0, '5 3')]
    t += f3.ausschnitt('vorn', inhalt)
    t += f3.rahmen('Schnitt A–A: Führung_vorn')
    t += f3.spalte([
        (yv[0] + 4.0, pz[1] - 4.0, 'Opferplatte'),
        (OL['innen_y']['vorn'][0] + 2.0, tz + 20.0,
         'voller Block\n({} mm breit)'.format(de(
             OL['innen_y']['vorn'][1] - OL['innen_y']['vorn'][0], 2))),
        (OL['auflage_y']['vorn'] - 3.0, OL['nut_seite_z'] - 3.0,
         'M5×{} ohne Scheibe\nin der Senkung'.format(
             de(OL['m5_schraube']['vorn'], 0))),
        (yv[0] + 6.0, tief, 'Toolhead, Z ganz unten:\nam vorderen Wegende '
         '3 mm\nvor dem 2060')],
        f3.ox - 12, 'end', abstand=34.0)
    t += f3.spalte([
        (OL['quer_y']['vorn'][1] - 3.0, OL['quer_z'][1] - 10.0,
         'vorderes 2060'),
        (OL['innen']['vorn'] + 3.0, OL['nut_seite_z'] + 4.0,
         'Hammermutter in der\ninneren Seitennut'),
        (OL['quer_y']['vorn'][1] + 2.0, tz, 'Tisch')],
        f3.ox + f3.breite + 12, 'start', abstand=30.0)

    # ---- Feld 5: Schnitt C-C quer durch den Riegel (von links) -------------
    # Die Platte liegt vor der Schnittebene (zwischen Betrachter und
    # Schnitt): nur ihr Umriss, gestrichelt. Der Lagerbock liegt dahinter.
    s5 = 3.5
    nase = OL['riegel_nase_y']
    yc = (nase - 12.0, OL['ausleger_y'][1] + 6.0)
    f5 = Feld(250, f2.oy + f2.hoehe + 110, yc, (tz - 6.0, zp + rs + 6.0), s5)
    pz_ = (pz[0], pz[1])
    inhalt = [f5.rect(yc[0] - 5.0, py[1], *pz_, 'holz', fill_opacity='0.3',
                      stroke_dasharray='4 3'),
              f5.rect(*OL['lager_y'], OL['ausleger_z'][1], OL['lager_z'][1],
                      'hinten'),
              f5.rect(*OL['ausleger_y'], *OL['ausleger_z'], 'neu'),
              f5.poly(riegel_umriss(OL, ow), 'neu'),
              f5.poly(riegel_umriss(OL, ow, offen=True), 'neu', fill='none',
                      stroke=ORANGE, stroke_dasharray='3 2'),
              bogen(f5, (yp, zp), rs, 180.0, 4.0, GRAU, 0.7, '2 3'),
              f5.kreis(yp, zp, ow('m5_durchgang') / 2.0, 'neu',
                       fill='#ffffff'),
              f5.kreis(yp, zp, 2.5, 'stahl'),
              f5.linie(yc[0] - 5, tz, yc[1] + 5, tz, GRAU, 1.4)]
    a = math.radians(30.0)                   # Pfeil: klappt nach vorn
    inhalt.append(pfeil(*f5.px(yp + rs * math.cos(a), zp + rs * math.sin(a)),
                        math.sin(a), math.cos(a), GRAU))
    t += f5.ausschnitt('riegel_c', inhalt)
    t += f5.rahmen('Schnitt C–C: Riegel (von links, vorn rechts)')
    t += quer_mass(f5, nase, py[1], OL['riegel_z'][0] - 3.5, '{} mm'.format(
        de(py[1] - nase, 0)), dy=-4)
    t += f5.spalte([
        (yc[0] + 3.0, pz[1] - 3.0, 'Plattenende (vor der\nSchnittebene, '
         'gestrichelt)'),
        (nase + 3.0, zp + 2.0, 'Riegel zu: {} mm vor dem\nPlattenende, '
         'liegt auf der\nhinteren Kante des Auslegers'.format(
             de(ow('riegel_ueber'), 0))),
        (yc[0] + 3.0, tz, 'Tisch')],
        f5.ox - 12, 'end', abstand=34.0)
    t += f5.spalte([
        (yp + rs * math.cos(math.radians(60.0)),
         zp + rs * math.sin(math.radians(60.0)),
         'klappt über oben nach vorn\n(Radius {} mm)'.format(de(rs, 0))),
        (yp + rl - 4.0, zp + rh - 1.0, 'Riegel offen: liegt\nauf dem '
         'Ausleger'),
        (yp + 1.5, zp - 1.5, 'Achse: M5 längs X'),
        (OL['lager_y'][1] - 0.5, OL['lager_z'][1] - 1.0,
         'Lagerbock (dahinter)'),
        (OL['ausleger_y'][1] - 3.0, tz + 3.0, 'Ausleger {} mm'.format(
            de(ow('ausleger_t'), 0)))],
        f5.ox + f5.breite + 12, 'start', abstand=30.0)

    # ---- Feld 6: Schnitt D-D laengs der Achse (von vorn) ------------------
    # Die Platte liegt hinter der Schnittebene.
    xs = OL['lager_x'][1] + ow('m5_scheibe_h')
    xm = xs + ow('m5_mutter_h')
    xd = (OL['quer_x'][1] - 14.0, xm + riegel_ueberstand(ow, OL) + 8.0)
    f6 = Feld(f5.ox + f5.breite + 270, f5.oy, xd,
              (tz - 6.0, OL['lager_z'][1] + 6.0), 4.5)
    tt, sw = OL['riegel_tasche_t'], ow('m5_sw')
    inhalt = [f6.rect(xd[0] - 5.0, px[1], *pz_, 'holz', fill_opacity='0.45'),
              f6.rect(xd[0] - 5.0, OL['quer_x'][1], OL['quer_z'][0],
                      OL['lager_z'][1] + 11.0, 'profil'),
              f6.rect(*OL['endplatte_x'], *OL['endplatte_z'], 'neu'),
              f6.rect(*OL['ausleger_x'], *OL['ausleger_z'], 'neu'),
              f6.rect(*OL['lager_x'], OL['ausleger_z'][1], OL['lager_z'][1],
                      'neu'),
              f6.rect(*rx, *OL['riegel_z'], 'neu'),
              f6.rect(rx[0], OL['lager_x'][1], zp - ow('m5_durchgang') / 2.0,
                      zp + ow('m5_durchgang') / 2.0, 'neu', fill='#ffffff'),
              f6.rect(rx[0], rx[0] + tt, zp - OL['riegel_tasche_sw'] / 2.0,
                      zp + OL['riegel_tasche_sw'] / 2.0, 'neu',
                      fill='#ffffff'),
              f6.rect(rx[0] + tt - ow('m5_sk_k'), rx[0] + tt, zp - sw / 2.0,
                      zp + sw / 2.0, 'stahl'),
              f6.rect(rx[0] + tt, xm + riegel_ueberstand(ow, OL), zp - 2.5,
                      zp + 2.5, 'stahl'),
              f6.rect(OL['lager_x'][1], xs, zp - ow('m5_scheibe_d') / 2.0,
                      zp + ow('m5_scheibe_d') / 2.0, 'stahl'),
              f6.rect(xs, xm, zp - sw / 2.0, zp + sw / 2.0, 'stahl'),
              f6.linie(xd[0] - 5, tz, xd[1] + 5, tz, GRAU, 1.4)]
    t += f6.ausschnitt('riegel_d', inhalt)
    t += f6.rahmen('Schnitt D–D: Riegel längs der Achse (von vorn)')
    xa, ya = f6.px(px[1] - 1.0, zp - 4.0)
    t += [linie(xa - 50, ya, xa - 4, ya, ORANGE, 1.6),
          pfeil(xa, ya, 1, 0, ORANGE)]
    t += f6.spalte([
        (xd[0] + 3.0, OL['quer_z'][0] + 8.0, 'vorderes 2060'),
        (px[1] - 6.0, pz[1] - 2.5, 'Plattenende (dahinter)'),
        (rx[0] + tt - 1.5, zp + sw / 2.0 - 0.5, 'Sechskantkopf M5×{} in\nder '
         'Tasche, dreht mit'.format(de(OL['riegel_schraube'], 0))),
        (px[1] - 9.0, zp - 4.0, 'Stoß der Platte: wirkt längs\nder Achse '
         'auf den Lagerbock'),
        (OL['endplatte_x'][0] + 1.0, OL['endplatte_z'][1] - 2.0,
         'Endplatte (Führung_vorn)\nam Ende des 2060'),
        (xd[0] + 3.0, tz, 'Tisch')],
        f6.ox - 12, 'end', abstand=30.0)
    t += f6.spalte([
        (OL['lager_x'][1] - 2.0, OL['lager_z'][1] - 1.0, 'Lagerbock {} mm'
         .format(de(ow('lager_t'), 0))),
        (xm - 1.0, zp + 2.0, 'Scheibe + Stoppmutter\nM5 (SW {})'.format(
            de(sw, 0))),
        (rx[1] - 1.5, zp - 6.0, 'Riegel, {} mm Luft\nzum Plattenende'.format(
            de(ow('riegel_spiel'), 0))),
        (OL['ausleger_x'][1] - 3.0, tz + 3.0, 'Ausleger')],
        f6.ox + f6.breite + 12, 'start', abstand=30.0)

    # ---- Feld 4: Schnitt durch den Anschlag (von vorn) ----------------------
    xa4 = (OL['quer_x'][0] - 18.0, OL['halter_x']['links'][1] + 30.0)
    f4 = Feld(f2.ox, f5.oy + max(f5.hoehe, f6.hoehe) + 100, xa4,
              (tz - 8.0, top + 22.0), sz)
    inhalt = [f4.rect(*OL['anschlag_x'], *OL['anschlag_z'], 'neu'),
              f4.rect(px[0], xa4[1] + 5.0, *pz, 'holz'),
              f4.linie(xa4[0] - 5, tz, xa4[1] + 5, tz, GRAU, 1.4)]
    t += f4.ausschnitt('anschlag', inhalt)
    t += f4.rahmen('Schnitt B–B: Anschlag links (von vorn, Y {})'.format(
        de(ys, 0, True)))
    t += f4.spalte([
        (OL['anschlag_x'][0] + 2.0, OL['anschlag_z'][1] - 4.0,
         'Anschlag {} × {} mm, {} mm unter der\nOberfläche; sitzt am '
         'Halter Anschlag_vorn,\nder vor der Schnittebene liegt'.format(
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
        ('Höhe', 'Platte und Maschine auf demselben Tisch: Oberfläche Z {}, '
         '{} mm über der Unterkante der 2060'.format(
             de(top, 1, True), de(top - OL['z_2060'], 1))),
        ('', 'Werkstück bis {} mm ({} mm unter dem Toolhead frei)'.format(
            de(frei, 1), de(SICHERHEIT, 0))),
        ('', 'Toolhead mit Z ganz unten (Softlimit $132): {} mm über '
         'der Platte'.format(de(tief - top, 1))),
        ('Halter', '4 × {} mm lang, so hoch wie die Platte, innen am 2060 '
         'auf dem Tisch'.format(de(ow('halter_l'), 0))),
        ('Befestigung', 'je 2 × M5 in Hammermuttern der inneren unteren '
         'Seitennut: vorn M5×{} versenkt,'.format(
             de(OL['m5_schraube']['vorn'], 0))),
        ('', 'hinten M5×{} + Scheibe durch den Flansch'.format(
            de(OL['m5_schraube']['hinten'], 0))),
        ('Riegel', 'klappt um eine M5×{} längs X; zu {} mm vor dem '
         'Plattenende, {} mm Luft'.format(
             de(OL['riegel_schraube'], 0), de(ow('riegel_ueber'), 0),
             de(ow('riegel_spiel'), 0))),
        ('', 'ein Stoß gegen die Platte wirkt längs der Achse und klappt '
         'ihn nicht auf'),
        ('', 'Platte höchstens {} mm lang (Anschlag bis Riegel)'.format(
            de(rx[0] - OL['anschlag_x'][1], 0))),
        ('Druck', 'PETG, keine Stützen, 5 Teile: 4 Halter und der Riegel'),
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
          text(tx + 171, yy + 8, 'tiefster Punkt des Toolheads', 8.5),
          linie(tx + 300, yy + 4.5, tx + 316, yy + 4.5, ORANGE, 1.0, '3 2'),
          text(tx + 321, yy + 8, 'Riegel offen', 8.5)]

    W = int(max(f1.ox + f1.breite + 220, f3.ox + f3.breite + 220,
                f6.ox + f6.breite + 220, tx + 480))
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
