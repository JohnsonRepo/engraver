#!/usr/bin/env python3
"""Zeichnung: Kamerahalter fuer den Autofokus (Rev. 2, vorn rechts).

Oben links der Halter von oben auf dem vorderen 2060 vor dem Elektronikfach,
mit der Grenze, bis zu der Laser und Schlitten fahren, und dem Kabel; oben
rechts der Blick von der Kamera zur Anschlagecke vorn rechts mit Bildwinkel
und Messpunkt; unten links ein Schnitt laengs der Sichtlinie mit dem Laser
am Messpunkt und den Linien zum Punkt fuer das duennste und das dickste
Werkstueck; unten Mitte der Halter im selben Schnitt, groesser; unten rechts
die Wand in Blickrichtung mit Polstern, Zapfen, Schrauben und der Kamera.
Alle Masse aus Kamerahalter.py (lage()), Spannmittel.py, Opferplatte.py,
Elektronikfach.py, Portal.py und ToolheadZ.py; die Zeichnung ist
massstaeblich.

    python3 tools/kamerahalter_zeichnen.py   ->  docs/kamerahalter.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import spannmittel_check as smc                       # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, de,  # noqa: E402
                              TEXT, GRAU, BLAU, ROT, FARBE)
from portal_zeichnen import Feld, quer_mass           # noqa: E402
from portal_zeichnen import hoch_mass, KABEL          # noqa: E402
from opferplatte_check import OPFERPLATTE             # noqa: E402
from spannmittel_check import SPANNMITTEL             # noqa: E402
from kamerahalter_check import (KAMERAHALTER, FACH, huelle,  # noqa: E402
                                toolhead_am_messpunkt)

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'kamerahalter.svg')
FARBE.update({
    'holz': ('#ecd6ad', '#9a7442'),
    'werkstueck': ('#f7ecd6', '#a8783a'),
    'platine': ('#cfe8cf', '#2b8a3e'),
    'schwarz': ('#495057', '#212529'),
    'fach': ('#eef0f3', '#868e96'),
    'blick': ('#dbe7f6', '#2f5d92'),
    'riemen': ('#ffe3c2', '#b0671b'),
})


def strecke_im_rechteck(p, u, xr, yr):
    """s-Bereich, in dem p + s*u (waagerecht) im Rechteck xr x yr liegt,
    oder None."""
    s0, s1 = -1e9, 1e9
    for k, (lo, hi) in ((0, xr), (1, yr)):
        if abs(u[k]) < 1e-12:
            if not lo <= p[k] <= hi:
                return None
            continue
        a, b = (lo - p[k]) / u[k], (hi - p[k]) / u[k]
        s0, s1 = max(s0, min(a, b)), min(s1, max(a, b))
    return (s0, s1) if s1 > s0 else None


def main():
    km = bauraum.modul_laden(KAMERAHALTER, 'kamerahalter')
    kw, KL = km.w, km.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    SL = sm.lage()
    OL = bauraum.modul_laden(OPFERPLATTE, 'opferplatte').lage()
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    fm = bauraum.modul_laden(FACH, 'elektronikfach')
    FL = fm.lage()
    fach_x, fach_y, fach_z = fm.bereich_nach_maschine(
        FL['geh_x'], FL['geh_y'], FL['geh_z'])
    riemen = next(q for q in bauraum.portal_bauraeume(w, L)[0]
                  if q.name == 'Y-Riemen rechts')
    lx, ly, lz = KL['linse']
    mx, my = KL['mp']
    s0, s1 = KL['sicht'][0], KL['sicht'][-1]
    az = KL['blick_az']
    hq, hh = KL['bild_halb']
    q0, q1 = KL['quer_y']
    xi = kw('rahmen_x_innen')
    xa = xi + kw('rahmen_b')
    rz = kw('rahmen_z0')
    pz = kw('platte_z1')
    ex, ey = SL['aw_ecke_maschine']
    lv, lr, sv = kw('laser_vorn_y'), kw('laser_x1'), kw('schlitten_vorn_y')
    wst = smc.gedreht(bauraum.Quader('Werkstueck', *SL['wst_x'],
                                     *SL['wst_y'], *SL['wst_z']), SL)
    anschlag = smc.anschlag_quader(SL)
    nieder = [q for nh in SL['nh'] for q in smc.niederhalter_quader(nh, SL)]

    def richtung(grad, laenge):
        a = math.radians(grad)
        return (lx + laenge * math.cos(a), ly + laenge * math.sin(a))

    def drauf(n):
        return huelle(KL['welt'][n])

    def grenze(f, x0, x1):
        """Bis hier fahren Laser und Schlittenplatte (Softlimit vorn)."""
        pkt = [(x0, lv), (lr, lv), (lr, sv), (x1, sv)]
        return [f.linie(*a, *b, ROT, 1.0, '6 3') for a, b in zip(pkt, pkt[1:])]

    def kamera_oben(f, a):
        a += [f.poly(drauf('Fuss'), 'neu')]
        a += [f.kreis(X, Y, kw('m5_kopf_d') / 2.0, 'stahl')
              for X, Y in KL['m5_welt']]
        a += [f.poly(drauf('Steg'), 'neu'), f.poly(drauf('Wand'), 'neu'),
              f.poly(drauf('Platine'), 'platine', fill_opacity='0.85'),
              f.poly(drauf('Linsenblock'), 'schwarz'),
              f.poly(drauf('Objektiv'), 'schwarz')]

    t = [text(24, 30, 'Kamerahalter für den Autofokus (Kamerahalter.py Rev. '
              '{})'.format(km.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Die Kamera '
              'sitzt hochkant und geneigt auf dem vorderen 2060 am rechten '
              '2040, vor dem Elektronikfach, und sieht den Laserpunkt am '
              'Messpunkt je nach Werkstückdicke höher oder tiefer im Bild.',
              9, GRAU)]

    # ---- Feld 1: von oben, Halter auf dem vorderen 2060 ------------------
    X1, Y1 = (176.0, 272.0), (140.0, 228.0)
    f1 = Feld(40, 100, X1, Y1, 5.0, b_runter=True)
    a1 = [f1.rect(X1[0], fach_x[1], fach_y[0], Y1[1], 'fach'),
          f1.rect(X1[0], xi, q0, q1, 'profil'),
          f1.rect(xi, xa, Y1[0], Y1[1], 'profil'),
          f1.rect(riemen.x[0], riemen.x[1], Y1[0], Y1[1], 'riemen',
                  fill_opacity='0.6')]
    a1 += grenze(f1, X1[0], xi)
    a1.append(f1.rect(*KL['winkel'][0], *KL['winkel'][1], 'stahl',
                      fill_opacity='0.5', stroke_dasharray='3 2'))
    kamera_oben(f1, a1)
    ax, ay, _ = KL['kabel_aus_welt']
    sx, sy, _ = KL['kabel_steif_welt']
    weg = [(ax, ay), (sx, sy), (sx, fach_y[0] + 8.0)]
    a1 += [f1.linie(*a, *b, KABEL, 1.6, '5 3') for a, b in zip(weg, weg[1:])]
    a1.append(f1.linie(lx, ly, mx, my, BLAU, 1.2))
    a1.append(f1.linie(lx, ly, *richtung(az, 70.0), BLAU, 0.9, '2 2'))
    t += f1.ausschnitt('drauf', a1)
    t += f1.rahmen('Von oben: Halter auf dem vorderen 2060, vor dem Fach')
    t += f1.zeiger(182.0, (q0 + q1) / 2.0, 6, 34, '2060 vorn (oben, Nut)',
                   'start')
    t += f1.zeiger(186.0, fach_y[0] + 20.5, 10, 0, 'Elektronikfach',
                   'start')
    t += f1.zeiger(xa - 4.0, 150.0, -6, -26, 'rechtes 2040', 'end')
    t += f1.zeiger(riemen.x[0] + 2.0, 160.0, -12, 30, 'Y-Riemen (Z {} bis '
                   '{})'.format(de(riemen.z[0], 0), de(riemen.z[1], 0)),
                   'end')
    t += f1.zeiger(190.0, lv, 0, -26, 'bis hier fahren Laser und Schlitten',
                   'start')
    t += f1.zeiger(KL['m5_welt'][0][0], KL['m5_welt'][0][1], -4, 52,
                   '2 × M5×{} in Hammermuttern'.format(de(kw('m5_l'), 0)),
                   'start')
    t += f1.zeiger(KL['winkel'][0][1] - 3.0, KL['winkel'][1][1] - 2.0, -10,
                   78, 'Eckwinkel in der Nut (Hülle), Halter darüber 45° '
                   'ausgespart', 'end')
    t += f1.zeiger(weg[-1][0], weg[-1][1] - 2.0, 30, 10,
                   'Kabel über das 2060 ins Fach', 'start')
    t += f1.zeiger(*richtung(az, 40.0), 12, 4, 'Blick {}°, {}° geneigt'
                   .format(de(az, 0), de(KL['neige'], 0)), 'start')

    # ---- Feld 2: Blick zur Anschlagecke -----------------------------------
    X2, Y2 = (60.0, 272.0), (40.0, 228.0)
    f2 = Feld(580, 100, X2, Y2, 2.2, b_runter=True)
    a2 = [f2.rect(*OL['platte_x'], *OL['platte_y'], 'holz'),
          f2.rect(*wst.x, *wst.y, 'werkstueck')]
    a2 += [f2.rect(*q.x, *q.y, 'neu') for q in anschlag]
    a2 += [f2.rect(*q.x, *q.y, 'stahl') for q in nieder]
    a2 += [f2.rect(X2[0], fach_x[1], fach_y[0], Y2[1], 'fach'),
           f2.rect(X2[0], xi, q0, q1, 'profil'),
           f2.rect(xi, xa, Y2[0], Y2[1], 'profil')]
    a2 += grenze(f2, X2[0], xi)
    keil = [(lx, ly), richtung(az - hq, 260.0), richtung(az + hq, 260.0)]
    a2.append(f2.poly(keil, 'blick', fill_opacity='0.45'))
    a2.append(f2.linie(lx, ly, mx, my, BLAU, 1.2))
    a2 += [f2.poly(drauf('Fuss'), 'neu'), f2.poly(drauf('Wand'), 'neu'),
           f2.poly(drauf('Platine'), 'platine')]
    a2 += [f2.kreis(mx, my, 2.2, 'stahl', fill=ROT, stroke=ROT),
           f2.linie(mx - 6, my, mx + 6, my, ROT, 0.8),
           f2.linie(mx, my - 6, mx, my + 6, ROT, 0.8)]
    t += f2.ausschnitt('blick', a2)
    t += f2.rahmen('Blick zur Anschlagecke vorn rechts ({}° Bildwinkel quer)'
                   .format(de(2.0 * hq, 0)))
    t += f2.zeiger(mx, my, -24, -24, 'Messpunkt: {} links, {} hinter der '
                   'Ecke'.format(de(kw('mp_links'), 0),
                                 de(kw('mp_hinten'), 0)), 'end')
    t += f2.zeiger(110.0, 70.0, 0, -12, 'Werkstück in der Ecke', 'middle')
    t += f2.zeiger(150.0, ey + 6.0, -10, 44, 'Anschlag (Ecke vorn rechts)',
                   'end')
    t += f2.zeiger(lx, ly, -40, 26, 'Kamera', 'end')

    # ---- Feld 3: Schnitt laengs der Sichtlinie ---------------------------
    D = math.hypot(mx - lx, my - ly)
    u = ((mx - lx) / D, (my - ly) / D)
    p0 = (lx, ly)
    S3, Z3 = (-55.0, D + 28.0), (-162.0, 16.0)
    f3 = Feld(40, 600, S3, Z3, 2.5)

    def schnitt(f, xr, yr, zr, art, **mehr):
        s = strecke_im_rechteck(p0, u, xr, yr)
        return [f.rect(s[0], s[1], zr[0], zr[1], art, **mehr)] if s else []

    def k_poly(box):
        """Teil im Rahmen K, geschnitten in der Ebene x = 0 (Blickebene)."""
        (x0, x1), (y0, y1), (z0, z1) = box
        if not x0 <= 0.0 <= x1:
            return None
        return [km.k_nach_h(KL, 0.0, y, z)[1:] for y, z in
                ((y0, z0), (y1, z0), (y1, z1), (y0, z1))]

    def halter_schnitt(f, a):
        a += schnitt(f, KL['fuss_x'], KL['fuss_y'], KL['fuss_z'], 'neu')
        (_, _), (sy0, sy1), (sz0, sz1) = KL['steg']
        a.append(f.rect(sy0, sy1, sz0, sz1, 'neu'))
        for box, art in ((KL['wand'], 'neu'),
                         (KL['wand_teile']['Polster'], 'neu'),
                         (KL['platine'], 'platine'),
                         (KL['stecker'], 'schwarz'),
                         (KL['block'], 'schwarz'),
                         (KL['tubus'], 'schwarz')):
            pg = k_poly(box)
            if pg:
                a.append(f.poly(pg, art))

    a3 = (schnitt(f3, OL['platte_x'], OL['platte_y'], OL['platte_z'], 'holz')
          + schnitt(f3, L['quer_x'], L['quer_y_vorn'], L['quer_z'],
                    'profil')
          + schnitt(f3, fach_x, fach_y, (fach_z[0], kw('deckel_z1')),
                    'fach'))
    for q in anschlag:
        a3 += schnitt(f3, q.x, q.y, q.z, 'neu')
    th_mp = toolhead_am_messpunkt(tw, TL, L, KL)
    for q in th_mp:
        a3 += schnitt(f3, q.x, q.y, q.z, 'toolhead', fill_opacity='0.8')
    laser = next(q for q in th_mp if q.name == 'Diodenlaser')
    s_laser = strecke_im_rechteck(p0, u, laser.x, laser.y)
    sw_ = strecke_im_rechteck(p0, u, wst.x, wst.y)
    for dicke, voll in ((3.0, True), (kw('werkstueck_max'), False)):
        a3.append(f3.rect(sw_[0], sw_[1], pz, pz + dicke, 'werkstueck',
                          fill=FARBE['werkstueck'][0] if voll else 'none',
                          stroke_dasharray=None if voll else '4 3'))
    halter_schnitt(f3, a3)
    nu = KL['neige']
    for wink, strich, br in ((nu - hh, '3 3', 0.7), (nu + hh, '3 3', 0.7),
                             (nu, '8 3 2 3', 0.7)):
        e = S3[1]
        a3.append(f3.linie(0.0, lz, e, lz - e * math.tan(math.radians(wink)),
                           BLAU, br, strich))
    for s_ in (s0, s1):
        a3.append(f3.linie(0.0, lz, D, pz + s_['t'], BLAU, 1.2))
        a3.append(f3.kreis(D, pz + s_['t'], 1.0, 'stahl', fill=ROT,
                           stroke=ROT))
    t += f3.ausschnitt('schnitt', a3)
    t += f3.rahmen('Schnitt längs der Sichtlinie ({}° Bildwinkel senkrecht)'
                   .format(de(2.0 * hh, 0)))
    t += f3.zeiger(D, pz + s0['t'], -60, 22, '{} mm: {}° unter der Achse'
                   .format(de(s0['t'], 0), de(s0['unter'], 1)), 'end')
    t += f3.zeiger(D, pz + s1['t'], -46, -30, '{} mm: {}° über der Achse'
                   .format(de(s1['t'], 0), de(-s1['unter'], 1)), 'end')
    t += f3.zeiger(s_laser[0] + 4.0, laser.z[0] + 4.0, -24, -26,
                   'Laser am Messpunkt, Z oben', 'end')
    t += f3.zeiger(-20.0, rz - 30.0, 30, 54, '2060 vorn', 'start')
    t += f3.zeiger(D - 20.0, pz - 10.0, -30, 22, 'Opferplatte', 'end')
    s_an = [r for q in anschlag
            for r in [strecke_im_rechteck(p0, u, q.x, q.y)] if r]
    if s_an:
        t += f3.zeiger(min(r[0] for r in s_an) + 1.0, pz + 2.0, -10, -26,
                       'Anschlag', 'end')

    # ---- Feld 4: Halter im selben Schnitt, groesser ----------------------
    S4, Z4 = (-36.0, 10.0), (-73.0, -20.0)
    f4 = Feld(560, 600, S4, Z4, 6.4)
    a4 = (schnitt(f4, L['quer_x'], L['quer_y_vorn'], L['quer_z'], 'profil')
          + schnitt(f4, fach_x, fach_y, (fach_z[0], kw('deckel_z1')),
                    'fach'))
    halter_schnitt(f4, a4)
    for X, Y in KL['m5_welt']:
        xh, yh = km.lokal(KL, X, Y)
        r = kw('m5_kopf_d') / 2.0
        a4.append(f4.rect(yh - r, yh + r, KL['fuss_z'][1],
                          KL['fuss_z'][1] + kw('m5_kopf_h'), 'stahl',
                          fill='none', stroke_dasharray='2 2'))
    for wink in (nu - hh, nu, nu + hh):
        e = S4[1]
        a4.append(f4.linie(0.0, lz, e, lz - e * math.tan(math.radians(wink)),
                           BLAU, 0.7, '8 3 2 3' if wink == nu else '3 3'))
    t += f4.ausschnitt('halter', a4)
    t += f4.rahmen('Halter im Schnitt durch die Linse')
    t += hoch_mass(f4, 6.0, rz, lz, de(lz - rz, 0))
    t += f4.zeiger(-30.0, rz - 2.0, 4, 18, '2060 vorn (oben)', 'start')
    t += f4.zeiger(KL['steg'][1][0] + 1.0, -58.0, 30, 10, 'Steg', 'start')
    t += f4.zeiger(-6.0, KL['fuss_z'][1] - 1.0, 18, 18, 'Fuß, M5 '
                   'gestrichelt', 'start')
    pw = k_poly(KL['wand'])
    t += f4.zeiger(*pw[2], -14, -10, 'Wand {}° geneigt'.format(de(nu, 1)),
                   'end')
    t += f4.zeiger(0.0, lz, 18, -40, 'Linse', 'start')

    # ---- Feld 5: Wand in Blickrichtung ----------------------------------
    wx, wz = KL['wand'][0], KL['wand'][2]
    pl = KL['platine']
    X5 = (min(wx[0], pl[0][0]) - 6.0, max(wx[1], pl[0][1]) + 24.0)
    Z5 = (wz[0] - 9.0, wz[1] + 9.0)
    f5 = Feld(890, 600, X5, Z5, 6.2)
    a5 = [f5.rect(wx[0], wx[1], wz[0], wz[1], 'neu')]
    for x, z in KL['loecher']:
        a5.append(f5.poly(km.tropfen_punkte(x, z, kw('pad_d'), -1.0,
                                            KL['pad_kappe']), 'neu',
                          stroke='#8a4b12'))
    for x, z in KL['loecher_zapfen']:
        a5.append(f5.poly(km.tropfen_punkte(x, z, kw('zapfen_d'), -1.0,
                                            kw('zapfen_kappe')), 'stahl',
                          fill='#f6d7b8'))
    for x, z in KL['loecher_schraube']:
        a5.append(f5.kreis(x, z, kw('m2_kopf_d') / 2.0, 'stahl'))
    a5 += [f5.rect(pl[0][0], pl[0][1], pl[2][0], pl[2][1], 'platine',
                   fill='none', stroke_dasharray='5 3'),
           f5.rect(KL['stecker'][0][0], KL['stecker'][0][1],
                   KL['stecker'][2][0], KL['stecker'][2][1], 'schwarz',
                   fill='none', stroke_dasharray='2 2'),
           f5.rect(KL['block'][0][0], KL['block'][0][1], KL['block'][2][0],
                   KL['block'][2][1], 'schwarz', fill='none'),
           f5.kreis(0.0, 0.0, kw('cam_tubus_d') / 2.0, 'schwarz',
                    fill='none')]
    (xs_, za), (xz_, zb) = KL['loecher_schraube'][0], \
        KL['loecher_zapfen'][0]
    xs2 = KL['loecher_schraube'][1][0]
    t += f5.ausschnitt('wand', a5)
    t += f5.rahmen('Wand in Blickrichtung, Kamera gestrichelt')
    t += quer_mass(f5, min(xs_, xs2), max(xs_, xs2), wz[1] + 4.0,
                   de(kw('cam_loch_ab'), 1))
    xr = max(wx[1], pl[0][1])
    t += hoch_mass(f5, xr + 4.0, zb, za, de(za - zb, 0))
    t += quer_mass(f5, pl[0][0], pl[0][1], wz[0] - 4.5, de(kw('cam_h'), 3))
    t += hoch_mass(f5, xr + 14.0, pl[2][0], pl[2][1], de(kw('cam_b'), 0))
    t += f5.zeiger(xs_, za, -16, -22, 'M2×{}, Mutter hinten'.format(
        de(kw('m2_l'), 0)), 'end')
    t += f5.zeiger(xz_, zb, -18, 24, 'Zapfen', 'end')
    kx = pl[0][1] if KL['kabel_seite'] < 0 else pl[0][0]
    t += f5.zeiger(kx, pl[2][1] - 2.0, 30, -30, 'Kabelkante', 'start')

    # ---- Zahlen und Legende ----------------------------------------------
    tx, ty = 40, 1080
    zeilen = [
        ('Kamera', 'Raspberry Pi Kamera v1.3 (OV5647, wie verbaut), '
         'hochkant; Linse {} mm über der Platte, {} mm vom rechten 2040'
         .format(de(lz - pz, 0), de(xi - lx, 1))),
        ('Fokus', 'fest ab Werk (1 m bis ∞): Linse auf {} mm drehen, dann '
         'höchstens {} Pixel unscharf'.format(
             de(KL['fokus_auf'], 0),
             de(max(x['unschaerfe_px'] for x in KL['sicht']), 1))),
        ('Blick', '{}° (schräg nach hinten links), {}° nach unten geneigt'
         .format(de(az, 1), de(nu, 1))),
        ('Messpunkt', 'G54 X−{} Y+{} (Nullpunkt in der Anschlagecke); {} '
         'bis {} mm von der Linse'.format(
             de(kw('mp_links'), 0), de(kw('mp_hinten'), 0),
             de(s1['abstand'], 0), de(s0['abstand'], 0))),
        ('Bild', 'Punkt auf der Achse quer, {} bis {}° senkrecht (Bild ±{}°); '
         '{} Pixel je mm Höhe'.format(
             de(-abs(s0['unter']), 1), de(abs(s1['unter']), 1),
             de(hh, 1), de(KL['px_je_mm'], 1))),
        ('Luft', 'Laser bis X {} / Y {}, Halter ab X {}; Fach {} mm hinter '
         'dem Fuß'.format(de(lr, 1), de(lv, 0), de(KL['links_x'], 1),
                          de(fach_y[0] - KL['fuss_y'][1], 1))),
        ('Schrauben', '2 × M5×{} in Hammermuttern; 2 × M2×{} mit Mutter, '
         '2 Zapfen'.format(de(kw('m5_l'), 0), de(kw('m2_l'), 0))),
        ('Druck', 'PETG, Fuß aufs Bett, keine Stützen; Kabel Standard–Mini '
         '{} mm'.format(de(kw('kabel_l'), 0))),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 78, ty + 10 + i * 15, v, 8.5, TEXT))
    lx0 = 760
    t.append(text(lx0, ty - 8, 'Legende', 10.5, BLAU, fett=True))
    for i, (art, s_) in enumerate((('neu', 'Halter, Anschlag (PETG)'),
                                   ('platine', 'Kamera'),
                                   ('profil', 'Rahmenprofile'),
                                   ('fach', 'Elektronikfach'),
                                   ('holz', 'Opferplatte'),
                                   ('werkstueck', 'Werkstück'),
                                   ('toolhead', 'Toolhead'),
                                   ('riemen', 'Y-Riemen'))):
        xx = lx0 + (i % 2) * 170
        yy = ty + 2 + (i // 2) * 18
        t.append(rect_px(xx, yy, xx + 14, yy + 9, art))
        t.append(text(xx + 19, yy + 8, s_, 8.5))
    yy = ty + 2 + 4 * 18
    t += [linie(lx0, yy + 4.5, lx0 + 16, yy + 4.5, BLAU, 1.2),
          text(lx0 + 21, yy + 8, 'Sichtlinie', 8.5),
          linie(lx0 + 170, yy + 4.5, lx0 + 186, yy + 4.5, KABEL, 1.6, '5 3'),
          text(lx0 + 191, yy + 8, 'Kamerakabel', 8.5),
          linie(lx0, yy + 22.5, lx0 + 16, yy + 22.5, ROT, 1.0, '6 3'),
          text(lx0 + 21, yy + 26, 'Grenze bewegter Teile (Softlimit vorn)',
               8.5)]

    W = int(max(f2.ox + f2.breite, f5.ox + f5.breite) + 40)
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
