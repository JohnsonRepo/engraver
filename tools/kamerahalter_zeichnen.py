#!/usr/bin/env python3
"""Zeichnung: Kamerahalter fuer den Autofokus.

Oben links der Halter von oben auf dem hinteren 2060 vor dem Elektronikfach,
mit der Grenze, bis zu der die Traegerplatte faehrt, und dem Kabelweg;
oben rechts der Blick von der Kamera zur Anschlagecke mit Bildwinkel und
Messpunkt; unten links ein Schnitt laengs der Sichtlinie mit den Linien zum
Punkt fuer das duennste und das dickste Werkstueck; unten rechts der
Halter von vorn mit Polstern, Zapfen, Schrauben und der Kamera. Alle Masse
aus Kamerahalter.py (lage()), Spannmittel.py, Opferplatte.py und
ToolheadZ.py; die Zeichnung ist massstaeblich.

    python3 tools/kamerahalter_zeichnen.py   ->  docs/kamerahalter.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, de,  # noqa: E402
                              TEXT, GRAU, BLAU, ROT, FARBE)
from portal_zeichnen import Feld, quer_mass           # noqa: E402
from notaus_zeichnen import hoch_mass, KABEL          # noqa: E402
from opferplatte_check import OPFERPLATTE             # noqa: E402
from spannmittel_check import SPANNMITTEL             # noqa: E402
from kamerahalter_check import KAMERAHALTER, FACH     # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'kamerahalter.svg')
FARBE.update({
    'holz': ('#ecd6ad', '#9a7442'),
    'werkstueck': ('#f7ecd6', '#a8783a'),
    'platine': ('#cfe8cf', '#2b8a3e'),
    'schwarz': ('#495057', '#212529'),
    'fach': ('#eef0f3', '#868e96'),
    'blick': ('#dbe7f6', '#2f5d92'),
})


def ecken(KL, x, y):
    """Umriss eines lokalen Rechtecks (x, y) im Maschinenrahmen (X, Y)."""
    return [KL_welt(KL, a, b) for a, b in ((x[0], y[0]), (x[1], y[0]),
                                           (x[1], y[1]), (x[0], y[1]))]


def KL_welt(KL, x, y):
    return (KL['linse'][0] + x * KL['sin'] + y * KL['cos'],
            KL['linse'][1] - x * KL['cos'] + y * KL['sin'])


def richtung(KL, grad, laenge):
    a = math.radians(grad)
    return (KL['linse'][0] + laenge * math.cos(a),
            KL['linse'][1] + laenge * math.sin(a))


def main():
    km = bauraum.modul_laden(KAMERAHALTER, 'kamerahalter')
    kw, KL = km.w, km.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    sw, SL = sm.w, sm.lage()
    OL = bauraum.modul_laden(OPFERPLATTE, 'opferplatte').lage()
    TL = bauraum.modul_laden().lage()
    FL = bauraum.modul_laden(FACH, 'elektronikfach').lage()
    lx, ly, lz = KL['linse']
    mx, my = KL['mp']
    s0, s1 = KL['sicht'][0], KL['sicht'][-1]
    az = kw('blick_az')
    hq, hh = KL['bild_halb']
    q0, q1 = KL['quer_y']
    fv = kw('fach_vorn_y')

    t = [text(24, 30, 'Kamerahalter für den Autofokus (Kamerahalter.py Rev. '
              '{})'.format(km.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Die Kamera '
              'sitzt hochkant auf dem hinteren 2060 vor dem Elektronikfach '
              'und sieht den Laserpunkt am Messpunkt je nach Werkstückdicke '
              'höher oder tiefer im Bild.', 9, GRAU)]

    # ---- Feld 1: von oben, Halter auf dem 2060 -------------------------
    f1 = Feld(40, 100, (-74.0, 8.0), (-263.0, -221.0), 7.6, b_runter=True)
    a1 = [f1.rect(-74.0, 8.0, fv - 12.0, fv, 'fach'),
          f1.rect(-74.0, 8.0, q0, q1, 'profil'),
          f1.linie(-74.0, kw('th_hinten_y'), 8.0, kw('th_hinten_y'), ROT,
                   1.0, '6 3'),
          f1.poly(KL['fuss_welt'], 'neu')]
    a1 += [f1.kreis(X, Y, kw('m5_kopf_d') / 2.0, 'stahl')
           for X, Y in KL['m5_welt']]
    wx, wy = KL['wand'][0], KL['wand'][1]
    a1 += [f1.poly(ecken(KL, wx, wy), 'neu'),
           f1.poly(ecken(KL, KL['rippe'][0], (wy[0] - kw('rippe_l'), wy[0])),
                   'neu')]
    pl = KL['platine']
    a1 += [f1.poly(ecken(KL, pl[0], pl[1]), 'platine'),
           f1.poly(ecken(KL, KL['stecker'][0], KL['stecker'][1]), 'schwarz'),
           f1.poly(ecken(KL, KL['block'][0], KL['block'][1]), 'schwarz'),
           f1.poly(ecken(KL, KL['tubus'][0], KL['tubus'][1]), 'schwarz')]
    # Kabel: Austritt, steifes Ende, aussen nach links, ins Fach, zum Pi
    ax, ay, _ = KL['kabel_aus_welt']
    sx, sy, _ = KL['kabel_steif_welt']
    ex = KL['kabel_eintritt_x']
    yk = fv + 1.2
    innen = fv - kw('fach_wand') - 2.0
    weg = [(ax, ay), (sx, sy), (sx - 2.0, yk), (ex, yk), (ex, innen),
           (kw('pi_buchse_x'), innen)]
    a1 += [f1.linie(*a, *b, KABEL, 1.6, '5 3') for a, b in zip(weg, weg[1:])]
    # Blickrichtung und Sichtlinie
    a1.append(f1.linie(lx, ly, *richtung(KL, az, 60.0), BLAU, 0.9, '2 2'))
    a1.append(f1.linie(lx, ly, mx, my, BLAU, 1.2))
    t += f1.ausschnitt('drauf', a1)
    t += f1.rahmen('Von oben: Halter auf dem hinteren 2060, vor dem Fach')
    t += f1.zeiger(-60.0, (q0 + q1) / 2.0, -10, 40, '2060 hinten (oben)',
                   'start')
    t += f1.zeiger(-70.0, fv - 6.0, 0, -18, 'Elektronikfach, Vorderwand '
                   'und Deckel', 'start')
    t += f1.zeiger(2.0, kw('th_hinten_y'), 0, 22, 'bis hier fährt die '
                   'Trägerplatte', 'end')
    t += f1.zeiger(KL['m5_welt'][0][0], KL['m5_welt'][0][1], -14, 108,
                   '2 × M5×{} in Hammermuttern der Nut'.format(
                       de(kw('m5_l'), 0)), 'start')
    t += f1.zeiger(*richtung(KL, az, 18.0), -8, 2, 'Blickrichtung {}°'
                   .format(de(az, 0)), 'end')
    t += f1.zeiger((weg[2][0] + weg[3][0]) / 2.0, yk, 20, -30,
                   'Kabel außen nach links, über die Wand ins Fach, '
                   'innen zum Pi', 'start')

    # ---- Feld 2: Blick zur Ecke ---------------------------------------
    f2 = Feld(740, 100, (-216.0, 14.0), (-262.0, -100.0), 1.95, b_runter=True)
    px_, py_ = OL['platte_x'], OL['platte_y']
    (hx, hy), (lx_, ly_) = SL['aw_hinten'], SL['aw_links']
    ex_, ey_ = SL['aw_ecke']
    a2 = [f2.rect(px_[0], px_[1], py_[0], py_[1], 'holz'),
          f2.rect(ex_, ex_ + 120.0, ey_, ey_ + 90.0, 'werkstueck'),
          f2.rect(*hx, *hy, 'neu'), f2.rect(*lx_, *ly_, 'neu'),
          f2.rect(-216.0, 14.0, q0, q1, 'profil'),
          f2.rect(-216.0, 14.0, fv - 12.0, fv, 'fach'),
          f2.linie(-216.0, kw('th_hinten_y'), 14.0, kw('th_hinten_y'), ROT,
                   0.9, '6 3')]
    keil = [(lx, ly), richtung(KL, az - hq, 240.0), richtung(KL, az + hq,
                                                             240.0)]
    a2.append(f2.poly(keil, 'blick', fill_opacity='0.45'))
    a2.append(f2.linie(lx, ly, mx, my, BLAU, 1.2))
    a2.append(f2.poly(ecken(KL, pl[0], pl[1]), 'platine'))
    a2 += [f2.kreis(mx, my, 2.2, 'stahl', fill=ROT, stroke=ROT),
           f2.linie(mx - 6, my, mx + 6, my, ROT, 0.8),
           f2.linie(mx, my - 6, mx, my + 6, ROT, 0.8)]
    t += f2.ausschnitt('blick', a2)
    t += f2.rahmen('Blick zur Anschlagecke ({}° Bildwinkel quer)'.format(
        de(2.0 * hq, 0)))
    t += f2.zeiger(mx, my, 22, 22, 'Messpunkt: {} rechts, {} vor der Ecke'
                   .format(de(kw('mp_rechts'), 0), de(kw('mp_vorn'), 0)),
                   'start')
    t += f2.zeiger(ex_ + 100.0, ey_ + 50.0, 10, 20, 'Werkstück in der Ecke',
                   'start')
    t += f2.zeiger(ex_ + 2.0, ey_ - 3.0, -4, -40, 'Anschlag', 'end')
    t += f2.zeiger(lx, ly, 30, -20, 'Kamera', 'start')

    # ---- Feld 3: Schnitt laengs der Sichtlinie ---------------------------
    D = math.hypot(mx - lx, my - ly)
    ux, uy = (mx - lx) / D, (my - ly) / D

    def s_von(Y):
        return (Y - ly) / uy

    f3 = Feld(40, 490, (-42.0, D + 30.0), (-140.0, -8.0), 2.4)
    pz = kw('platte_z1')
    a3 = [f3.rect(s_von(py_[0]), D + 30.0, pz - 25.3, pz, 'holz'),
          f3.rect(s_von(q0), s_von(q1), kw('rahmen_z0') - kw('quer_h'),
                  kw('rahmen_z0'), 'profil'),
          f3.rect(-42.0, s_von(fv), FL['fach_z'][0], kw('deckel_z1'), 'fach'),
          f3.linie(-42.0, kw('xwagen_z0'), D + 30.0, kw('xwagen_z0'), ROT,
                   0.9, '6 3')]
    for dicke, art in ((3.0, 'werkstueck'), (kw('werkstueck_max'), None)):
        a3.append(f3.rect(D - 45.0, D + 30.0, pz, pz + dicke, 'werkstueck',
                          fill='none' if art is None else FARBE[art][0],
                          stroke_dasharray=None if art else '4 3'))
    # Laser am Messpunkt, Z oben (Unterkante des Gehaeuses, Langloch tief)
    zl_u = TL['zc_arbeit_max'] + TL['laser_unten_rel'] - 8.0
    a3.append(f3.rect(D - 17.5, D + 17.5, zl_u, -8.0, 'toolhead'))
    # Kamera grob: Platine senkrecht, dahinter Wand und Fuss
    a3 += [f3.rect(-KL['platine'][1][1] * 0 - 8.6, -7.4, lz - 12.5, lz + 12.5,
                   'platine'),
           f3.rect(-7.4, 0.0, lz - 2.9, lz + 2.9, 'schwarz'),
           f3.rect(-14.6, -10.6, kw('rahmen_z0') + kw('fuss_t'),
                   KL['wand'][2][1], 'neu'),
           f3.rect(-24.0, 6.0, kw('rahmen_z0'), kw('rahmen_z0')
                   + kw('fuss_t'), 'neu')]
    for wink in (-hh, hh):
        e = (D + 30.0, lz - (D + 30.0) * math.tan(math.radians(wink)))
        a3.append(f3.linie(0.0, lz, *e, BLAU, 0.7, '3 3'))
    for s_ in (s0, s1):
        a3.append(f3.linie(0.0, lz, D, pz + s_['t'], BLAU, 1.2))
        a3.append(f3.kreis(D, pz + s_['t'], 1.0, 'stahl', fill=ROT,
                           stroke=ROT))
    t += f3.ausschnitt('schnitt', a3)
    t += f3.rahmen('Schnitt längs der Sichtlinie (Kamera hochkant: {}° '
                   'Bildwinkel senkrecht)'.format(de(2.0 * hh, 0)))
    t += f3.zeiger(D, pz + s0['t'], -40, 20, '{} mm: {}° unter der Achse'
                   .format(de(s0['t'], 0), de(s0['unter'], 1)), 'end')
    t += f3.zeiger(D, pz + s1['t'], -50, -24, '{} mm: {}° unter der Achse'
                   .format(de(s1['t'], 0), de(s1['unter'], 1)), 'end')
    t += f3.zeiger(D + 10.0, zl_u + 6.0, 8, -12, 'Laser am Messpunkt, '
                   'Z oben', 'start')
    t += f3.zeiger(20.0, kw('xwagen_z0'), 0, -12, 'X-Wagen fährt bis hier '
                   'herunter', 'start')
    t += f3.zeiger(-20.0, kw('rahmen_z0') + kw('fuss_t') / 2.0, 34, 40,
                   'Fuß auf dem 2060', 'start')
    t += f3.zeiger(-36.0, -120.0, 20, 40, 'Elektronikfach', 'start')
    t += [f3.linie(0.0, lz, 30.0, lz, GRAU, 0.6)]

    # ---- Feld 4: Halter von vorn ----------------------------------------
    f4 = Feld(760, 490, (-26.0, 34.0), (-76.0, -27.0), 6.2)
    zf0, zf1 = KL['fuss_z']
    xf = [x for x, _ in KL['fuss']]
    a4 = [f4.rect(min(xf), max(xf), zf0, zf1, 'neu'),
          f4.rect(KL['rippe'][0][0], KL['rippe'][0][1], zf1,
                  zf1 + kw('rippe_l'), 'neu', stroke_dasharray='3 2'),
          f4.rect(wx[0], wx[1], zf1, KL['wand'][2][1], 'neu')]
    for x, z in KL['loecher']:
        a4.append(f4.poly(km.tropfen_punkte(x, z, kw('pad_d'), -1.0,
                                            KL['pad_kappe']), 'neu',
                          stroke='#8a4b12'))
    for x, z in KL['loecher_zapfen']:
        a4.append(f4.poly(km.tropfen_punkte(x, z, kw('zapfen_d'), -1.0,
                                            kw('zapfen_kappe')), 'stahl',
                          fill='#f6d7b8'))
    for x, z in KL['loecher_schraube']:
        a4.append(f4.kreis(x, z, kw('m2_kopf_d') / 2.0, 'stahl'))
    a4 += [f4.rect(pl[0][0], pl[0][1], pl[2][0], pl[2][1], 'platine',
                   fill='none', stroke_dasharray='5 3'),
           f4.rect(KL['stecker'][0][0], KL['stecker'][0][1],
                   KL['stecker'][2][0], KL['stecker'][2][1], 'schwarz',
                   fill='none', stroke_dasharray='2 2'),
           f4.rect(KL['block'][0][0], KL['block'][0][1], KL['block'][2][0],
                   KL['block'][2][1], 'schwarz', fill='none'),
           f4.kreis(0.0, lz, kw('cam_tubus_d') / 2.0, 'schwarz', fill='none')]
    xs_, xz_ = KL['loecher_schraube'][0][0], KL['loecher_zapfen'][0][0]
    za, zb = KL['loecher'][0][1], KL['loecher'][1][1]
    t += f4.ausschnitt('vorn', a4)
    t += f4.rahmen('Halter von vorn, Kamera gestrichelt (hochkant)')
    t += quer_mass(f4, xs_, xz_, KL['wand'][2][1] + 3.0,
                   de(kw('cam_loch_ab'), 1))
    t += hoch_mass(f4, xz_ + 6.0, za, zb, de(zb - za, 0))
    t += quer_mass(f4, pl[0][0], pl[0][1], zf0 - 3.5, de(kw('cam_h'), 3))
    t += hoch_mass(f4, pl[0][1] + 13.0, pl[2][0], pl[2][1],
                   de(kw('cam_b'), 0))
    t += f4.zeiger(xs_, za, -26, 22, 'M2×{} mit Mutter dahinter'.format(
        de(kw('m2_l'), 0)), 'end')
    t += f4.zeiger(xz_, zb, 24, -26, 'Zapfen', 'start')
    t += f4.zeiger(KL['stecker'][0][0], lz + 6.0, -14, -64,
                   'Kabelkante (Stecker hinten)', 'end')
    t += f4.zeiger(KL['rippe'][0][1], zf1 + 3.0, 60, 24, 'Rippe hinter der '
                   'Wand', 'start')

    # ---- Zahlen und Legende ----------------------------------------------
    tx, ty = 40, 860
    zeilen = [
        ('Kamera', 'Camera Module 3, Normalobjektiv, hochkant; Linse {} mm '
         'über der Platte, Blick {}°'.format(de(lz - pz, 1), de(az, 0))),
        ('Messpunkt', 'G54 X{} Y{} (Nullpunkt in der Anschlagecke); {} bis '
         '{} mm von der Linse'.format(de(kw('mp_rechts'), 0),
                                      de(-kw('mp_vorn'), 0),
                                      de(s1['abstand'], 0),
                                      de(s0['abstand'], 0))),
        ('Bild', 'Punkt {}° neben der Achse, {}–{}° darunter; {} Pixel je '
         'mm Höhe'.format(de(abs(s0['quer']), 1), de(s1['unter'], 1),
                           de(s0['unter'], 1), de(KL['px_je_mm'], 1))),
        ('Luft', '{} mm zur Trägerplatte, {} mm unter dem X-Wagen, {} mm zum '
         'Fach'.format(de(kw('th_hinten_y') - KL['vorn_y'], 1),
                       de(kw('xwagen_z0') - KL['oben_z'], 0),
                       de(KL['hinten_y'] - fv, 1))),
        ('Schrauben', '2 × M5×{} in Hammermuttern; 2 × M2×{} mit Mutter, '
         '2 Zapfen'.format(de(kw('m5_l'), 0), de(kw('m2_l'), 0))),
        ('Druck', 'PETG, Fuß aufs Bett, keine Stützen; Kabel Standard–Mini '
         '{} mm (Weg etwa {})'.format(de(kw('kabel_l'), 0),
                                       de(KL['kabel_weg'], 0))),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 78, ty + 10 + i * 15, v, 8.5, TEXT))
    lx0 = 760
    t.append(text(lx0, ty - 8, 'Legende', 10.5, BLAU, fett=True))
    for i, (art, s_) in enumerate((('neu', 'Halter (PETG)'),
                                   ('platine', 'Kamera'),
                                   ('profil', '2060'),
                                   ('fach', 'Elektronikfach'),
                                   ('holz', 'Opferplatte'),
                                   ('werkstueck', 'Werkstück'))):
        xx = lx0 + (i % 2) * 150
        yy = ty + 2 + (i // 2) * 18
        t.append(rect_px(xx, yy, xx + 14, yy + 9, art))
        t.append(text(xx + 19, yy + 8, s_, 8.5))
    yy = ty + 2 + 3 * 18
    t += [linie(lx0, yy + 4.5, lx0 + 16, yy + 4.5, BLAU, 1.2),
          text(lx0 + 21, yy + 8, 'Sichtlinie', 8.5),
          linie(lx0 + 150, yy + 4.5, lx0 + 166, yy + 4.5, KABEL, 1.6, '5 3'),
          text(lx0 + 171, yy + 8, 'Kamerakabel', 8.5),
          linie(lx0, yy + 22.5, lx0 + 16, yy + 22.5, ROT, 1.0, '6 3'),
          text(lx0 + 21, yy + 26, 'Grenze bewegter Teile', 8.5)]

    W = int(max(f2.ox + f2.breite, f4.ox + f4.breite) + 40)
    H = int(max(ty + 10 + len(zeilen) * 15, yy + 30) + 20)
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
