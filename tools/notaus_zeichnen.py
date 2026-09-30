#!/usr/bin/env python3
"""Zeichnung: Gehaeuse fuer den Not-Aus vorn am vorderen 2060.

Von vorn, im Schnitt durch die Mitte von rechts und von oben: das Gehaeuse
an der Vorderseite des vorderen 2060 mit Laschen, Rippen, Taster und
Kabelweg, daneben das rechte 2040 mit Y-Motorhalter und Motor. Alle Masse
aus NotAus.py, Portal.py und YMotorhalter.py; die Zeichnung ist
massstaeblich und wandert mit den Parametern.

    python3 tools/notaus_zeichnen.py   ->  docs/notaus.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from bauraum import Quader                            # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, de,  # noqa: E402
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld                      # noqa: E402
from y_antrieb_zeichnen import quer_mass              # noqa: E402
from endschalter_zeichnen import profil_schnitt, ansicht  # noqa: E402
from notaus_check import NOTAUS                       # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'notaus.svg')
FARBE.update({
    'taster': ('#e03131', '#a51111'),
    'nut':    ('#ffffff', '#8c939e'),
})
KABEL = '#6d3fb5'


def hoch_mass(f, a, b0, b1, s, dx=6, anker='start'):
    """Senkrechtes Mass bei a von b0 bis b1, Text daneben."""
    (x, y0), (_, y1) = f.px(a, b0), f.px(a, b1)
    return [linie(x, y0, x, y1, BLAU, 0.8),
            linie(x - 3, y0, x + 3, y0, BLAU, 0.8),
            linie(x - 3, y1, x + 3, y1, BLAU, 0.8),
            text(x + dx if anker == 'start' else x - dx, (y0 + y1) / 2 + 3,
                 s, 8.0, BLAU, anker, True, halo=True)]


def kabel(f, punkte):
    """Kabelweg als gestrichelter Linienzug."""
    return [f.linie(*a, *b, KABEL, 1.6, '5 3')
            for a, b in zip(punkte, punkte[1:])]


def main():
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    L = pm.lage()
    nm = bauraum.modul_laden(NOTAUS, 'notaus')
    nw, NL = nm.w, nm.lage()
    R, Q = NL['R'], Quader
    leer = {}
    gestr = {'fill': 'none', 'stroke_dasharray': '4 3', 'stroke_width': '1.0'}
    x, zm = NL['schalter']
    gx, gy, gz = NL['geh_x'], NL['geh_y'], NL['geh_z']
    r_kopf = nw('schalter_kopf_d') / 2.0
    r_loch = NL['loch_d'] / 2.0
    ys, zs = L['rahmen_y'][1], L['rahmen_z0']
    qy, qz = L['quer_y_vorn'], L['quer_z']
    ky, kz = NL['kabel']
    x_nut = R + 10.0 + 5.0                    # Kabel aussen am 2040
    y_vor = qy[1] + 2.0
    z_nut = NL['nuten_z'][0]

    # ---- Teile als Quader ------------------------------------------------
    rahmen = [
        (Q('2060', 110.0, 300.0, *qy, *qz), 'profil', leer),
        (Q('2040', R - 10.0, R + 10.0, 150.0, ys, zs, zs + 40.0), 'profil',
         leer)]
    winkel = [(Q('Winkel', a, a + 20.0, *qy, zs, zs + 20.0), 'stahl',
               {'fill_opacity': '0.8'}) for a in (R - 30.0, R + 10.0)]
    ymh = [(Q('Y-Motorhalter', *NL['ymh_x'], *NL['ymh_y'], *NL['ymh_z']),
            'druck', leer),
           (Q('Y-Motor', *NL['motor_x'], *NL['motor_y'], *NL['motor_z']),
            'kauf', leer)]
    geh = [(Q('Gehaeuse', *gx, *gy, *gz), 'neu', leer)]
    for lx in NL['lasche_x']:
        geh.append((Q('Lasche', *lx, *NL['lasche_y'], *NL['lasche_z']),
                    'neu', leer))
        for rz in NL['rippe_z']:
            geh.append((Q('Rippe', *lx, NL['lasche_y'][1], NL['lasche_y'][1]
                          + nw('lasche_b'), *rz), 'neu', leer))
    kopf = (Q('Pilzkopf', x - r_kopf, x + r_kopf, *NL['kopf_y'], zm - r_kopf,
              zm + r_kopf), 'taster', leer)

    t = [text(24, 30, 'Not-Aus vorn am vorderen 2060: Gehäuse '
              '(NotAus.py Rev. {})'.format(nm.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Orange: neu '
              '(PETG, gelb wenn vorhanden). Taster: Gewinde Ø{} mm [v], '
              'Kopf und Tiefe angenommen [?].'.format(
                  de(nw('schalter_d'), 0)), 9, GRAU)]

    # ---- Feld 1: von vorn (X nach rechts, Z nach oben) ---------------------
    f1 = Feld(250, 100, (110.0, 300.0), (-136.0, -22.0), 2.6)
    nuten = []
    for zn in NL['nuten_z']:
        for s in (-1, 1):
            nuten.append(('svg', f1.linie(110.0, zn + s * 3.1, 300.0,
                                          zn + s * 3.1, '#8c939e', 0.6),
                          qy[1] + 0.01))
    kreise = []
    for mx, mz in NL['m5']:
        kreise += [('svg', f1.kreis(mx, mz, nw('m5_scheibe_d') / 2.0,
                                    'stahl'), 500.0),
                   ('svg', f1.kreis(mx, mz, 4.25, 'stahl'), 501.0)]
    kreise += [('svg', f1.kreis(x, zm, r_kopf, 'taster'), 600.0),
               ('svg', f1.kreis(x, zm, r_loch, 'taster', fill='none',
                                stroke_dasharray='3 2'), 601.0)]
    teile1 = rahmen + nuten + winkel + ymh + geh + kreise
    t += f1.ausschnitt('vorn', ansicht(f1, teile1, 'x', 'z', 'y', 1)
                       + [f1.linie(110.0, qz[0], 300.0, qz[0], GRAU, 1.2)]
                       + kabel(f1, [(x_nut, zs + 10.0), (x_nut, z_nut),
                                    (gx[1] + 3.0, z_nut), (gx[1], kz)]))
    t += f1.rahmen('Von vorn')
    t += f1.spalte([
        (130.0, qz[0] + 50.0, 'vorderes 2060,\nmittlere Nut: Z {}'.format(
            de(zm, 0))),
        (NL['m5'][0][0], zm, 'M5×{} mit Scheibe\nin der mittleren Nut'.format(
            de(NL['m5_schraube'], 0))),
        (x - r_kopf * 0.7, zm + r_kopf * 0.7, 'Pilzkopf Ø{} [?],\nLoch Ø{} '
         'dahinter'.format(de(nw('schalter_kopf_d'), 0),
                          de(NL['loch_d'], 1))),
        (150.0, qz[0], 'Tisch')],
        f1.ox - 12, 'end', abstand=28.0)
    t += f1.spalte([
        (R, zs + 30.0, 'rechtes 2040, Ende'),
        (R - 20.0, zs + 10.0, 'Winkel an der\nKreuzung (20 mm)'),
        (R + 8.0, NL['ymh_z'][1] - 4.0, 'Y-Motorhalter'),
        (R + 10.0, NL['motor_z'][0] + 10.0, 'Y-Motor rechts'),
        (x_nut, z_nut + 4.0, 'W2 aus der unteren Nut\ndes 2040, in der '
         'oberen\nNut des 2060 nach links')],
        f1.ox + f1.breite + 12, 'start', abstand=30.0)
    t += quer_mass(f1, gx[0], gx[1], gz[1] + 8.0, '{} mm'.format(
        de(gx[1] - gx[0], 0)))
    t += quer_mass(f1, NL['lasche_x'][1][1], NL['motor_x'][0],
                   NL['motor_z'][0] + 4.0, '{} mm'.format(
                       de(NL['motor_x'][0] - NL['lasche_x'][1][1], 0)))
    t += hoch_mass(f1, x + r_kopf + 6.0, qz[0], zm - r_kopf, '{} mm'.format(
        de(zm - r_kopf - qz[0], 0)))

    # ---- Feld 2: Schnitt durch die Mitte, von rechts (vorn links) ----------
    f2 = Feld(f1.ox + f1.breite + 230, 100, (178.0, 285.0), (-136.0, -22.0),
              2.6, a_rueck=True)
    wd, fr = nw('na_wand'), nw('na_front')
    lz = NL['lasche_z']
    teile2 = [
        (Q('linke Wand innen', 0, 1, gy[0], NL['front_y'][0], *NL['innen_z']),
         'hinten', leer),
        (Q('linke Lasche', 0, 1, *NL['lasche_y'], *lz), 'hinten',
         {'stroke_dasharray': '3 2'}),
        (Q('Decke', 0, 1, *gy, gz[1] - wd, gz[1]), 'neu', leer),
        (Q('Boden', 0, 1, *gy, gz[0], gz[0] + wd), 'neu', leer),
        (Q('Front oben', 0, 1, NL['front_y'][0], gy[1], zm + r_loch, gz[1]),
         'neu', leer),
        (Q('Front unten', 0, 1, NL['front_y'][0], gy[1], gz[0], zm - r_loch),
         'neu', leer),
        (Q('Taster', 0, 1, *NL['koerper_y'], zm - nw('schalter_d') / 2.0,
           zm + nw('schalter_d') / 2.0), 'stahl', leer),
        (Q('Mutter', 0, 1, NL['front_y'][0] - 4.0, NL['front_y'][0],
           zm - nw('schalter_mutter') / 2.0, zm + nw('schalter_mutter')
           / 2.0), 'stahl', {'fill_opacity': '0.8'}),
        (Q('Pilzkopf', 0, 1, *NL['kopf_y'], zm - r_kopf, zm + r_kopf),
         'taster', leer),
        (Q('Loetfahnen', 0, 1, NL['koerper_y'][0] - 5.0, NL['koerper_y'][0],
           zm - 6.0, zm + 6.0), 'kauf', leer)]
    t += f2.ausschnitt('schnitt', [profil_schnitt(f2, *qy, *qz, 'lruo')]
                       + ansicht(f2, teile2, 'y', 'z', 'x', 1)
                       + [f2.linie(178.0, qz[0], 285.0, qz[0], GRAU, 1.2)]
                       + [f2.rect(*NL['ymh_y'], *NL['ymh_z'], 'druck',
                                  **gestr),
                          f2.rect(*NL['motor_y'], *NL['motor_z'], 'kauf',
                                  **gestr)])
    t += f2.rahmen('Schnitt durch die Mitte, von rechts (vorn links)')
    t += f2.spalte([
        (NL['kopf_y'][1] - 4.0, zm + r_kopf - 4.0, 'Pilzkopf, rastet ein;\n'
         'Drehen löst'),
        (NL['koerper_y'][0] + 8.0, zm, 'Taster: Gewinde\ndurch, Mutter innen'),
        (NL['koerper_y'][0] - 2.0, zm - 5.0, 'Lötfahnen C, NO, NC\n(NO bleibt '
         'frei)'),
        (NL['motor_y'][0] + 6.0, NL['motor_z'][0] + 6.0, 'Y-Motor und '
         'Halter\n(vor der Schnittebene)'),
        (gy[1] - 10.0, gz[0] + 1.5, 'Front aufs Bett')],
        f2.ox - 12, 'end', abstand=30.0)
    t += f2.spalte([
        (qy[0] + 3.0, qz[0] + 20.0, 'vorderes 2060'),
        (gy[0] + 3.0, lz[1] - 3.0, 'Lasche links (dahinter)'),
        (gy[0] + 15.0, gz[1] - 1.5, 'Rückseite offen,\nliegt am 2060 an')],
        f2.ox + f2.breite + 12, 'start', abstand=28.0)
    t += quer_mass(f2, gy[0], gy[1], gz[1] + 8.0, '{} mm'.format(
        de(gy[1] - gy[0], 0)))
    t += quer_mass(f2, NL['kopf_y'][0], NL['kopf_y'][1], zm + r_kopf + 6.0,
                   '{} mm [?]'.format(de(nw('schalter_kopf_h'), 0)))
    t += hoch_mass(f2, gy[1] + 26.0, gz[0], gz[1], '{} mm'.format(
        de(gz[1] - gz[0], 0)), anker='end')

    # ---- Feld 3: von oben (X nach rechts, vorn unten) ----------------------
    f3 = Feld(250, f1.oy + f1.hoehe + 90, (110.0, 300.0), (170.0, 305.0),
              2.6, b_runter=True)
    rippen = [('vieleck', pkt, 'neu', leer, gz[1]) for pkt in NL['rippen']]
    koepfe = [(Q('M5-Kopf', mx - 4.25, mx + 4.25, NL['lasche_y'][1],
                 NL['lasche_y'][1] + nw('m5_scheibe_h') + nw('m5_kopf_h'),
                 zm - 4.25, zm + 4.25), 'stahl', leer)
              for mx, _ in NL['m5']]
    teile3 = (rahmen + [(ymh[1][0], 'kauf', gestr), ymh[0]] + winkel + geh
              + rippen + koepfe + [kopf])
    t += f3.ausschnitt('oben', ansicht(f3, teile3, 'x', 'y', 'z', 1)
                       + kabel(f3, [(x_nut, 175.0), (x_nut, y_vor),
                                    (gx[1] + 3.0, y_vor), (gx[1] + 3.0, ky),
                                    (gx[1], ky)]))
    t += f3.rahmen('Von oben (vorn unten)')
    t += f3.spalte([
        (130.0, qy[0] + 10.0, 'vorderes 2060'),
        (NL['lasche_x'][0][0] + 4.0, NL['lasche_y'][0] + 3.0,
         'Lasche mit M5'),
        (NL['rippen'][0][0][0] - 4.0, NL['rippen'][0][0][1] + 4.0,
         'Rippe, 45°: druckt\nohne Stützen'),
        (x - r_kopf + 3.0, NL['kopf_y'][1] - 3.0, 'Pilzkopf')],
        f3.ox - 12, 'end', abstand=28.0)
    t += f3.spalte([
        (R, 180.0, 'rechtes 2040'),
        (R + 12.0, NL['ymh_y'][1] - 12.0, 'Y-Motorhalter,\ndarunter der '
         'Motor'),
        (x_nut, 190.0, 'W2 in der unteren\nNut außen am 2040'),
        (gx[1] + 3.0, ky, 'Kabeldurchlass Ø{} und\nzwei Schlitze für den\n'
         'Kabelbinder'.format(de(nw('kabel_d'), 0)))],
        f3.ox + f3.breite + 12, 'start', abstand=30.0)
    t += quer_mass(f3, NL['m5'][0][0], NL['m5'][1][0], gy[0] - 6.0,
                   '{} mm'.format(de(NL['m5'][1][0] - NL['m5'][0][0], 0)))
    t += quer_mass(f3, NL['lasche_x'][1][1], R - 10.0, qy[0] - 6.0,
                   '{} mm'.format(de(R - 10.0 - NL['lasche_x'][1][1], 0)))

    # ---- Zahlen und Legende -------------------------------------------------
    tx = f3.ox + f3.breite + 230
    ty = f3.oy + 10
    zeilen = [
        ('Gehäuse', '{} × {} × {} mm, Wände {} mm, Front {} mm'.format(
            de(gx[1] - gx[0], 0), de(gz[1] - gz[0], 0), de(gy[1] - gy[0], 0),
            de(wd, 0), de(fr, 0))),
        ('', 'Mitte X {}, auf der mittleren Nut; längs verschiebbar'.format(
            de(x, 0, True))),
        ('Befestigung', '2 × M5×{} mit Scheibe, Hammermuttern M5'.format(
            de(NL['m5_schraube'], 0))),
        ('Taster', 'Gewinde Ø{} rund [v] → Loch Ø{}; Mutter innen, fest '
         'anziehen'.format(de(nw('schalter_d'), 0), de(NL['loch_d'], 1))),
        ('', 'Kopf Ø{} und {} mm Tiefe angenommen [?]'.format(
            de(nw('schalter_kopf_d'), 0), de(nw('schalter_tiefe'), 0))),
        ('Kabel', 'W2, 2 × 0,75 mm²: C und NC, NO bleibt frei; Kontakte '
         '3 A / 250 V [v]'),
        ('Druck', 'PETG, Front aufs Bett, keine Stützen'),
        ('Luft', '{} mm zum Y-Motor, {} mm zum Tisch'.format(
            de(NL['motor_x'][0] - NL['lasche_x'][1][1], 0),
            de(gz[0] - qz[0], 0))),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 78, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu (PETG)'),
                                  ('druck', 'Y-Motorhalter'),
                                  ('kauf', 'Motor, Kaufteil'),
                                  ('profil', 'Aluprofil'),
                                  ('stahl', 'Schrauben, Winkel, Taster'),
                                  ('taster', 'Pilzkopf'))):
        xx = tx + (i % 3) * 150
        yy = ly + (i // 3) * 18
        t.append(rect_px(xx, yy, xx + 14, yy + 9, art))
        t.append(text(xx + 19, yy + 8, s, 8.5))
    yy = ly + 36
    t.append(linie(tx, yy + 4.5, tx + 16, yy + 4.5, KABEL, 1.6, '5 3'))
    t.append(text(tx + 21, yy + 8, 'Kabel W2 zum Not-Aus', 8.5))

    W = int(max(f2.ox + f2.breite + 220, tx + 480))
    H = int(max(f3.oy + f3.hoehe, yy + 20) + 30)
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
