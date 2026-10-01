#!/usr/bin/env python3
"""Zeichnung der X-Energiekette: Wanne, Wannenstuetzen, Kettenhalter.

Ansicht von vorn mit der Schleife — Toolhead in der Mitte des X-Wegs,
gestrichelt an beiden Enden — und ein Querschnitt (Blick von links)
durch mittlere Stuetze, Wanne und Kettenhalter mit den Luftmassen. Alle
Masse kommen aus Portal.py (Kette, Wanne, Stuetzen) und ToolheadZ.py
(Kettenhalter); die Zeichnung ist massstaeblich.

    python3 tools/kette_zeichnen.py   ->  docs/energiekette.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, de, TEXT, GRAU, BLAU,  # noqa: E402
                              FARBE, rect_px)
from portal_zeichnen import Feld, quer_mass           # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'energiekette.svg')
FARBE.update({'kette': ('#8d96a3', '#3d4552'),
              'innen': ('#ffffff', '#3d4552')})
NB = 13                     # Punkte je Viertelbogen der Schleife


def bogen(xb, zc, r, von, bis, n=NB):
    """Punkte auf dem Kreis um (xb, zc), Winkel von..bis (Grad, 0 = +X)."""
    return [(xb + r * math.cos(math.radians(von + (bis - von) * i / n)),
             zc + r * math.sin(math.radians(von + (bis - von) * i / n)))
            for i in range(n + 1)]


def schleife(L, w, xw):
    """Umriss der X-Kette (X, Z) bei X-Wagenmitte xw: Untertrum ab dem
    Festpunkt-Endstueck, Bogen, Obertrum bis an das Ende des Anfangsstuecks."""
    xb = (L['xk_fest'] + xw + w('xk_gelenk_x') + L['xk_laenge']
          - math.pi * w('kette_r')) / 2.0
    zc, (ri, ra) = L['xk_bogen_z'], L['xk_bogen_r']
    u0, u1 = L['xk_unter_z']
    o0, o1 = L['xk_ober_z']
    x_fest = L['xk_fest'] - w('endstueck_l')
    x_ende = xw + w('xk_gelenk_x') - w('endstueck_l')
    aussen = [(x_fest, u0), (xb, u0)] + bogen(xb, zc, ra, -90, 90)[1:] \
        + [(x_ende, o1)]
    innen = [(x_ende, o0), (xb, o0)] + bogen(xb, zc, ri, 90, -90)[1:] \
        + [(x_fest, u1)]
    return aussen + innen, xb


def ansicht(f, w, L, tw, TL, portal):
    """Von vorn (Blick entlang Y): Rohr, Antrieb, Stuetzen, Wanne, Kette und
    Kettenhalter; die Traegerplatte davor nur als Umriss."""
    t = []
    q = {p.name: p for p in portal}
    hell = {'fill_opacity': '0.35'}
    # Stuetzen zuerst: ihre Platte sitzt hinter dem Rohr
    for x in L['st_x'].values():
        t.append(f.rect(x[0], x[1], L['st_platte_z'][0], L['st_arm_z'][1],
                        'neu'))
    t.append(f.rect(-w('profil_laenge') / 2, w('profil_laenge') / 2,
                    L['profil_z0'], L['profil_z1'], 'profil'))
    for n in ('Motorhalter Saeule hinten', 'Motorplatte', 'Spannbock Boden',
              'Spannbock Wand', 'Lagerschlitten unten',
              'Lagerschlitten Ruecken', 'Lagerschlitten oben'):
        b = q[n]
        t.append(f.rect(b.x[0], b.x[1], b.z[0], b.z[1], 'druck', **hell))
    for n in ('X-Motor', 'X-Ritzel', 'X-Umlenkritzel'):
        b = q[n]
        t.append(f.rect(b.x[0], b.x[1], b.z[0], b.z[1], 'kauf', **hell))
    r = q['X-Riemen Ruecklauf']
    t.append(f.rect(r.x[0], r.x[1], r.z[0], r.z[1], 'riemen'))
    # Wanne: Boden kraeftig, die Waende heller davor
    t.append(f.rect(*L['wanne_x'], *L['wanne_boden_z'], 'neu'))
    t.append(f.rect(*L['wanne_x'], L['wanne_boden_z'][1], L['wanne_z'][1],
                    'neu', fill_opacity='0.45'))
    # Kette an beiden Enden des X-Wegs gestrichelt, in der Mitte gefuellt
    for xw in (L['xw_min'], L['xw_max']):
        umriss, _ = schleife(L, w, xw)
        t.append(f.poly(umriss, 'kette', fill='none',
                        stroke_dasharray='4 3'))
        t.append(f.rect(xw + tw('traeger_x_links'), xw + tw('xk_gelenk_x'),
                        TL['kh_fuss_z0'], TL['kh_leiste_z'][1], 'neu',
                        fill='none', stroke_dasharray='4 3'))
    xm = L['xw_mitte']
    umriss, _ = schleife(L, w, xm)
    t.append(f.poly(umriss, 'kette', fill_opacity='0.85'))
    # Kettenhalter, Riemenhalter, X-Wagen; die Traegerplatte als Umriss
    t.append(f.rect(xm + tw('traeger_x_links'), xm + tw('xk_gelenk_x'),
                    TL['kh_fuss_z0'], TL['kh_leiste_z'][1], 'neu'))
    t.append(f.rect(xm - tw('x_wagen_laenge') / 2, xm + tw('x_wagen_laenge')
                    / 2, -tw('x_wagen_breite') / 2, tw('x_wagen_breite') / 2,
                    'fuehrung', fill_opacity='0.5'))
    t.append(f.rect(xm + tw('traeger_x_links'), xm + tw('traeger_x_rechts'),
                    TL['rh_z0'], TL['rh_z1'], 'toolhead'))
    t.append(f.rect(xm + tw('traeger_x_links'), xm + tw('traeger_x_rechts'),
                    tw('traeger_z_unten'), tw('traeger_kopf_unten'),
                    'toolhead', fill='none', stroke_dasharray='5 3'))
    t.append(f.rect(xm + tw('traeger_x_links'), xm + tw('traeger_x_kopf'),
                    tw('traeger_kopf_unten'), TL['konsole_z0'], 'toolhead',
                    fill='none', stroke_dasharray='5 3'))
    # Gelenke der Endstuecke
    for x, z in ((L['xk_fest'], L['xk_achse_unten']),
                 (xm + w('xk_gelenk_x'), L['xk_achse_oben'])):
        t.append(f.kreis(x, z, 1.6, 'innen'))
    return t


def querschnitt(f, w, L, tw, TL):
    """Schnitt durch die mittlere Stuetze (Blick von links, vorn rechts):
    Rohr, Schiene, Wagen, Traegerplatte, Riemenhalter, Riemen, Stuetze,
    Wanne mit Lasche, Unter- und Obertrum, Kettenhalter."""
    t = []
    pz = L['profil_z0'], L['profil_z1']
    t.append(f.rect(L['profil_y0'], L['portal_y'], *pz, 'profil'))
    t.append(f.rect(L['portal_y'], L['x_schiene_y1'], -w('x_schiene_b') / 2,
                    w('x_schiene_b') / 2, 'fuehrung'))
    t.append(f.rect(L['portal_y'] + w('x_wagen_boden'), 0.0,
                    -w('x_wagen_breite') / 2, w('x_wagen_breite') / 2,
                    'fuehrung', fill_opacity='0.7'))
    t.append(f.rect(0.0, tw('traeger_dicke'), f.b[0] - 5, f.b[1] + 5,
                    'toolhead'))
    t.append(f.rect(TL['rh_y0'], TL['rh_y1'], TL['rh_z0'], TL['rh_z1'],
                    'toolhead'))
    for ym, s in ((L['xr_y'], 1), (L['xr_y_rueck'], 1)):
        t.append(f.rect(ym - L['riemen_innen'], ym + L['riemen_aussen'],
                        L['xr_z0'], L['xr_z1'], 'riemen'))
    # Stuetze als Profil
    py, pzs = L['st_platte_y'], L['st_platte_z']
    by, bz = L['st_block_y'], L['st_block_z']
    ay, az = L['st_arm_y'], L['st_arm_z']
    fs = w('profil_fase')                 # Fase in der Innenecke
    t.append(f.poly([(py[0], pzs[0]), (py[1], pzs[0]), (py[1], bz[0] + fs),
                     (py[1] + fs, bz[0]),
                     (by[1], bz[0]), (by[1], az[0]), (ay[1], az[0]),
                     (ay[1], az[1]), (py[0], az[1])], 'neu'))
    # Wanne: U mit der Lasche hinten (an dieser Stuetze)
    yi, y = L['wanne_innen_y'], L['wanne_y']
    zb, z = L['wanne_boden_z'], L['wanne_z']
    t.append(f.poly([(L['wanne_lasche_y'][0], zb[0]), (y[1], zb[0]),
                     (y[1], z[1]), (yi[1], z[1]), (yi[1], zb[1]),
                     (yi[0], zb[1]), (yi[0], z[1]), (y[0], z[1]),
                     (y[0], zb[1]), (L['wanne_lasche_y'][0], zb[1])], 'neu'))
    # Glieder im Schnitt: aussen 18 x 14, innen 10 x 8,8; der Boden liegt
    # innen in der Schleife (unten oben, oben unten)
    yk = L['xk_y']
    ib, ih = w('kette_innen_b'), w('kette_innen_h')
    ym = L['xk_y_mitte']
    for z0, z1, boden_unten in ((L['xk_unter_z'][0], L['xk_unter_z'][1],
                                 False),
                                (L['xk_ober_z'][0], L['xk_ober_z'][1], True)):
        t.append(f.rect(yk[0], yk[1], z0, z1, 'kette'))
        if boden_unten:
            i0 = z0 + (w('kette_h') / 2.0 - 5.0)
        else:
            i0 = z1 - (w('kette_h') / 2.0 - 5.0) - ih
        t.append(f.rect(ym - ib / 2, ym + ib / 2, i0, i0 + ih, 'innen'))
    # Kettenhalter: Fuss, Auflage, Leisten
    fy, kz = TL['kh_fuss_y'], TL['kh_auflage_z1']
    hy, vy, lz = TL['kh_leiste_hinten_y'], TL['kh_leiste_vorn_y'], \
        TL['kh_leiste_z']
    t.append(f.poly([(fy[1], TL['kh_fuss_z0']), (fy[1], lz[1]),
                     (vy[0], lz[1]), (vy[0], kz), (hy[1], kz),
                     (hy[1], lz[1]), (hy[0], lz[1]),
                     (hy[0], TL['kh_auflage_z0']), (fy[0],
                                                     TL['kh_auflage_z0']),
                     (fy[0], TL['kh_fuss_z0'])], 'neu'))
    # Schrauben: M5 hinten in die Nut, M3 durch die Lasche, M3 von vorn
    # durch die Traegerplatte in den Fuss
    t.append(f.rect(py[0] - w('m5_kopf_h'), py[0] - 0.0, -4.25, 4.25,
                    'stahl'))
    t.append(f.rect(py[0], L['profil_y0'] + 5.0, -2.5, 2.5, 'stahl'))
    _, yl = L['wanne_laschen'][0]
    t.append(f.rect(yl - 2.75, yl + 2.75, zb[1], zb[1] + 3.0, 'stahl'))
    t.append(f.rect(yl - 1.5, yl + 1.5, zb[1] - L['wanne_schraube'] + 3.0,
                    zb[1], 'stahl'))
    zs = tw('kh_schraube_z')
    t.append(f.rect(tw('traeger_dicke') - tw('rh_senkung_t'),
                    tw('traeger_dicke') - tw('rh_senkung_t') + 3.0,
                    zs - 2.75, zs + 2.75, 'stahl'))
    t.append(f.rect(tw('traeger_dicke') - tw('rh_senkung_t')
                    - TL['kh_schraube'], tw('traeger_dicke')
                    - tw('rh_senkung_t'), zs - 1.5, zs + 1.5, 'stahl'))
    return t


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    portal, _ = bauraum.portal_bauraeume(w, L)
    FARBE.setdefault('stahl', ('#c3c8cf', '#4a4f57'))
    t = [text(24, 30, 'Energiekette X: Wanne, Wannenstützen, Kettenhalter '
              '(Portal.py Rev. {}, ToolheadZ.py Rev. {})'.format(
                  pm.REVISION, th.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Gedruckte '
              'Kette: Teilung {}, außen {} × {}, innen {} × {} mm, '
              'Biegeradius {} mm.'.format(
                  de(w('kette_teilung'), 0), de(w('kette_b'), 0),
                  de(w('kette_h'), 0), de(w('kette_innen_b'), 0),
                  de(w('kette_innen_h'), 1), de(w('kette_r'), 0)), 9, GRAU)]

    # ---- Ansicht von vorn --------------------------------------------------
    fa = Feld(250, 92, (-290.0, 290.0),
              (-30.0, L['xk_ober_z'][1] + 9.0), 1.5)
    t += fa.ausschnitt('vorn', ansicht(fa, w, L, tw, TL, portal))
    t += fa.rahmen('Ansicht von vorn: Toolhead in der Mitte, gestrichelt an '
                   'beiden Enden des X-Wegs (Trägerplatte davor als Umriss)')
    xm = L['xw_mitte']
    _, xb_m = schleife(L, w, xm)
    _, xb_r = schleife(L, w, L['xw_max'])
    t += fa.spalte([
        (L['xk_fest'] - w('endstueck_l') + 8.0, L['xk_unter_z'][0] + 3.0,
         'Festpunkt: Endstück 180,\nPlatte unten auf Wanne\nund Stütze'),
        (-150.0, 0.0, 'Portalrohr 2020'),
        (-249.0, 60.0, 'X-Motor'),
        (sum(L['st_x']['Festpunkt']) / 2.0, L['st_platte_z'][0] + 4.0,
         'Wannenstütze am Festpunkt\n(breit, 2 Einsätze im Arm)'),
        (xm + tw('traeger_x_links') + 4.0, TL['kh_fuss_z0'] + 6.0,
         'Kettenhalter (ToolheadZ.py)\nmit dem Anfangsstück'),
        (xm - 18.0, -40.0 + 30.0, 'Trägerplatte (Umriss),\nX-Wagen, '
         'Riemenhalter')],
        fa.ox - 12, 'end', abstand=30.0)
    t += fa.spalte([
        (xb_m + L['xk_bogen_r'][1] - 2.0, L['xk_bogen_z'],
         'Schleife nach rechts\n(Toolhead in der Mitte)'),
        (xb_r + L['xk_bogen_r'][1] - 4.0, L['xk_bogen_z'] + 12.0,
         'am rechten Ende: über\ndem Lagerschlitten'),
        (L['wanne_x'][1] - 30.0, L['wanne_z'][1] - 2.0,
         'Kettenwanne, {} mm'.format(de(L['wanne_x'][1] - L['wanne_x'][0],
                                        1))),
        (w('st_x_rechts'), L['st_platte_z'][0] + 4.0,
         'Wannenstützen mitte\nund rechts'),
        (230.0, 38.0, 'Lagerschlitten,\nSpannbock'),
        (120.0, sum(L['xk_unter_z']) / 2.0, 'Untertrum auf den\nRiegeln')],
        fa.ox + fa.breite + 12, 'start', abstand=30.0)
    # Masse: Boden, 2 R, Luft ueber dem Lagerschlitten
    xr = -150.0                       # frei zwischen X-Motor und Wanne
    t += fa.mass(xr, L['profil_z1'], L['wanne_boden_z'][1],
                 'Wannenboden Z {}'.format(de(L['wanne_boden_z'][1], 1,
                                              True)),
                 b_text=36.0)         # ueber dem Riemen, nicht darauf
    t += fa.mass(xr + 70.0, L['xk_achse_unten'], L['xk_achse_oben'],
                 '2 R = {} mm'.format(de(2.0 * w('kette_r'), 0)))
    ls = next(p for p in portal if p.name == 'Lagerschlitten oben')
    t += fa.luft(xb_r + 8.0, ls.z[1], xb_r + 8.0, L['xk_unter_z'][0],
                 '{} mm'.format(de(L['xk_unter_z'][0] - ls.z[1], 2)),
                 dx=6, dy=10)

    # ---- Querschnitt -------------------------------------------------------
    fb = Feld(250, fa.oy + fa.hoehe + 80, (-50.0, 18.0),
              (-14.0, L['xk_ober_z'][1] + 7.0), 3.4)
    t += fb.ausschnitt('quer', querschnitt(fb, w, L, tw, TL))
    t += fb.rahmen('Querschnitt durch die mittlere Stütze (Blick von links, '
                   'vorn rechts)')
    yk = L['xk_y']
    t += fb.spalte([
        (L['profil_y0'] + 6.0, 0.0, 'Portalrohr 2020'),
        (L['st_platte_y'][0] - 2.0, 0.0, 'M5 + Hammermutter\nin der hinteren '
         'Nut'),
        (sum(L['st_block_y']) / 2.0, 20.0, 'Block hinter dem\nRücklauf'),
        (L['xr_y_rueck'], L['xr_z1'] - 1.0, 'Rücklauf des\nX-Riemens'),
        (L['wanne_laschen'][0][1], L['wanne_boden_z'][1] + 2.0,
         'Lasche der Wanne,\nM3 in den Einsatz'),
        (yk[0] + 2.0, sum(L['xk_unter_z']) / 2.0, 'Untertrum\n(Boden oben)'),
        (yk[0] + 2.0, sum(L['xk_ober_z']) / 2.0, 'Obertrum\n(Boden unten)')],
        fb.ox - 12, 'end', abstand=32.0)
    t += fb.spalte([
        (8.0, L['xk_ober_z'][1], 'Trägerplatte'),
        (-4.0, TL['kh_leiste_z'][1] - 1.0, 'Kettenhalter: Auflage,\n'
         'Leisten, Fuß an der Platte'),
        (6.0, tw('kh_schraube_z'), 'M3 von vorn in den\nEinsatz im Fuß'),
        (-6.0, 24.0, 'Riemenhalter'),
        (-10.3, 23.0, 'gezogenes Trum'),
        (-1.0, 0.0, 'X-Wagen, Schiene'),
        (-9.0, L['st_arm_z'][1] - 1.0, 'Arm der Stütze\nunter der Wanne')],
        fb.ox + fb.breite + 12, 'start', abstand=32.0)
    # Luftmasse
    t += fb.luft(L['wanne_y'][1], 50.0, 0.0, 50.0, '{} mm'.format(
        de(-L['wanne_y'][1], 1)), dx=4, dy=-8)
    t += fb.luft(-11.0, TL['rh_z1'], -11.0, L['st_arm_z'][0], '{} mm'.format(
        de(L['st_arm_z'][0] - TL['rh_z1'], 1)), dx=4, dy=4)
    rl = L['xr_y_rueck'] - L['riemen_aussen']
    t += fb.luft(L['st_block_y'][1], 23.0, rl, 23.0, '{} mm'.format(
        de(rl - L['st_block_y'][1], 1)), dx=-4, dy=-8, anker='end')
    t += fb.luft(-6.6, L['xk_unter_z'][1], -6.6, TL['kh_fuss_z0'],
                 '{} mm'.format(de(TL['kh_fuss_z0'] - L['xk_unter_z'][1], 1)),
                 dx=4, dy=4)
    t += fb.mass(-46.0, L['xk_achse_unten'], L['xk_achse_oben'],
                 '2 R', dx=4)
    t += quer_mass(fb, yk[0], yk[1], L['xk_ober_z'][1] + 3.0, '{} mm'.format(
        de(w('kette_b'), 0)))

    # ---- Zahlen ------------------------------------------------------------
    ty = fb.oy + fb.hoehe + 46
    zeilen = [
        ('Kette', '{} Glieder = {} mm zwischen den Gelenken ({} gebraucht: '
         'halber Hub {} + Bogen {}), mit Anfangsstück und Endstück 180 {} mm'
         .format(L['xk_glieder'], de(L['xk_laenge'], 0),
                 de(L['xk_noetig'], 1), de(L['xk_hub'] / 2.0, 1),
                 de(math.pi * w('kette_r'), 1),
                 de(L['xk_laenge'] + 2.0 * w('endstueck_l'), 0))),
        ('Festpunkt', 'Gelenk des Endstücks 180 bei X {} (Mitte des Wegs des '
         'bewegten Gelenks, {} mm rechts der X-Wagenmitte)'.format(
             de(L['xk_fest'], 2, True), de(w('xk_gelenk_x'), 0))),
        ('Höhen', 'Wannenboden Z {}, Untertrum bis {}; Obertrum ab {} (= '
         'Auflage des Kettenhalters, {} mm über der Oberkante des X-Wagens)'
         .format(de(L['wanne_boden_z'][1], 1, True),
                 de(L['xk_unter_z'][1], 1, True),
                 de(L['xk_ober_z'][0], 1, True),
                 de(TL['kh_auflage_z1'] - tw('x_wagen_breite') / 2.0, 1))),
        ('Wanne', 'X {} bis {}, liegt auf den Armen der Stützen; vorn {} mm '
         'Luft zur Trägerplatte, am Ende {} mm vor dem Lagerschlitten'.format(
             de(L['wanne_x'][0], 2, True), de(L['wanne_x'][1], 2, True),
             de(-L['wanne_y'][1], 1), de(L['ls_innen_x'] - L['wanne_x'][1],
                                        1))),
        ('Schrauben', '3 × M5 × {} + Hammermutter (Stützen), 2 × M3 × {} + '
         'Einsatz (Laschen), 2 × M3 × {} + Scheibe + Einsatz (Endstück 180); '
         'Kettenhalter: 2 × M3 × {} von vorn, 2 × M3 × {} + Scheibe '
         '(Anfangsstück)'.format(
             de(L['st_m5_schraube'], 0), de(L['wanne_schraube'], 0),
             de(L['xk_fest_schraube'], 0), de(TL['kh_schraube'], 0),
             de(TL['kh_ende_schraube'], 0))),
    ]
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 18
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('kette', 'Energiekette (gedruckt)'),
                                  ('toolhead', 'Toolhead'),
                                  ('druck', 'Portal'),
                                  ('kauf', 'Kaufteil'),
                                  ('profil', 'Aluprofil'),
                                  ('fuehrung', 'Linearführung'),
                                  ('stahl', 'Schraube'))):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    t.append(text(24, ly + 46, 'Gestrichelt: Kette und Kettenhalter an den '
                  'Enden des X-Wegs, die Trägerplatte (sie steht vor der '
                  'Kette).', 8.5, GRAU))
    W = int(fa.ox + fa.breite + 200)
    H = int(ly + 62)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="100%" height="100%" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
