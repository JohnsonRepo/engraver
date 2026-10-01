#!/usr/bin/env python3
"""Zeichnungen der Energieketten X und Y.

X: Ansicht von vorn mit der Schleife — Toolhead in der Mitte des X-Wegs,
gestrichelt an beiden Enden — samt Kabelweg aus der oberen Nut am
Kabelfluegel hoch, ein Querschnitt (Blick von links) durch mittlere
Stuetze, Wanne und Kettenhalter mit den Luftmassen und ein Schnitt durch
den Kabelfluegel. Y: Ansicht von links mit der Schleife — Portal in der
Mitte, gestrichelt an beiden Enden des Y-Wegs — und ein Schnitt durch den
mittleren Traeger der Wanne Y. Alle Masse kommen aus Portal.py (Ketten,
Wannen, Stuetzen, Traeger, Kettenhalter Y) und ToolheadZ.py (Kettenhalter);
die Zeichnungen sind massstaeblich.

    python3 tools/kette_zeichnen.py   ->  docs/energiekette.svg
                                          docs/energiekette-y.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (el, f1, text, de, TEXT, GRAU,  # noqa: E402
                              BLAU, FARBE, rect_px)
from portal_zeichnen import Feld, quer_mass           # noqa: E402

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
ZIEL = os.path.join(DOCS, 'energiekette.svg')
ZIEL_Y = os.path.join(DOCS, 'energiekette-y.svg')
KABEL = '#6d3fb5'                    # wie in tools/elektronik_zeichnen.py
FARBE.update({'kette': ('#8d96a3', '#3d4552'),
              'innen': ('#ffffff', '#3d4552'),
              'kabel': ('#b9a3e3', KABEL)})
NB = 13                     # Punkte je Viertelbogen der Schleife


def bogen(xb, zc, r, von, bis, n=NB):
    """Punkte auf dem Kreis um (xb, zc), Winkel von..bis (Grad, 0 = +X)."""
    return [(xb + r * math.cos(math.radians(von + (bis - von) * i / n)),
             zc + r * math.sin(math.radians(von + (bis - von) * i / n)))
            for i in range(n + 1)]


def umriss(fest, gelenk, frei, zc, r, unter, ober, e):
    """Umriss einer Kette mit der Schleife nach plus (waagerecht a, Z
    senkrecht): Untertrum ab dem Ende des Endstuecks 180 (Gelenk bei fest),
    Bogen um zc mit den Radien r = (innen, aussen), Obertrum bis an das Ende
    des Anfangsstuecks (Gelenk bei gelenk); frei: Unter- plus Obertrum,
    e: Endstueck hinter dem Gelenk. Liefert (Punkte, Mitte des Bogens)."""
    b = (fest + gelenk + frei) / 2.0
    ri, ra = r
    u0, u1 = unter
    o0, o1 = ober
    a_fest, a_ende = fest - e, gelenk - e
    aussen = [(a_fest, u0), (b, u0)] + bogen(b, zc, ra, -90, 90)[1:] \
        + [(a_ende, o1)]
    innen = [(a_ende, o0), (b, o0)] + bogen(b, zc, ri, 90, -90)[1:] \
        + [(a_fest, u1)]
    return aussen + innen, b


def schleife(L, w, xw):
    """Umriss der X-Kette (X, Z) bei X-Wagenmitte xw."""
    return umriss(L['xk_fest'], xw + w('xk_gelenk_x'),
                  L['xk_laenge'] - math.pi * w('kette_r'), L['xk_bogen_z'],
                  L['xk_bogen_r'], L['xk_unter_z'], L['xk_ober_z'],
                  w('endstueck_l'))


def schleife_y(L, w, dy):
    """Umriss der Y-Kette (Y, Z), das Portal um dy aus der Mitte
    (Rahmenkoordinaten)."""
    return umriss(L['yk_fest'], w('yk_gelenk_y') + dy, L['yk_frei'],
                  L['yk_bogen_z'], L['xk_bogen_r'], L['yk_unter_z'],
                  L['yk_ober_z'], w('endstueck_l'))


def glieder_schnitt(f, w, a, unter, ober):
    """Unter- und Obertrum im Schnitt: aussen 18 x 14, innen 10 x 8,8; der
    Boden liegt innen in der Schleife (unten oben, oben unten)."""
    t = []
    ib, ih = w('kette_innen_b'), w('kette_innen_h')
    am = (a[0] + a[1]) / 2.0
    for (z0, z1), boden_unten in ((unter, False), (ober, True)):
        t.append(f.rect(a[0], a[1], z0, z1, 'kette'))
        if boden_unten:
            i0 = z0 + (w('kette_h') / 2.0 - 5.0)
        else:
            i0 = z1 - (w('kette_h') / 2.0 - 5.0) - ih
        t.append(f.rect(am - ib / 2, am + ib / 2, i0, i0 + ih, 'innen'))
    return t


def band(f, punkte, breite_mm, deckung='0.8'):
    """Litzenbuendel als breiter Streckenzug (Breite in mm)."""
    return el('polyline', {
        'points': ' '.join('{},{}'.format(*map(f1, f.px(a, b)))
                           for a, b in punkte),
        'fill': 'none', 'stroke': KABEL, 'stroke-opacity': deckung,
        'stroke-width': f1(breite_mm * f.s), 'stroke-linejoin': 'round'})


def ansicht(f, w, L, tw, TL, portal):
    """Von vorn (Blick entlang Y): Rohr, Antrieb, Stuetzen, Wanne, Kette und
    Kettenhalter; die Traegerplatte davor nur als Umriss. Dazu der Kabelweg:
    in der oberen Nut, am Kabelfluegel hoch, oben in die Wanne."""
    t = []
    q = {p.name: p for p in portal}
    hell = {'fill_opacity': '0.35'}
    # Stuetzen zuerst: ihre Platte sitzt hinter dem Rohr; die am Festpunkt
    # mit dem Kabelfluegel ueber dem Rohr
    for x in L['st_x'].values():
        t.append(f.rect(x[0], x[1], L['st_platte_z'][0], L['st_arm_z'][1],
                        'neu'))
    t.append(f.rect(*L['kf_x'], *L['kf_z'], 'neu'))
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
    # Litzen: in der oberen Nut (gestrichelt), vor dem Fluegel hoch, oben
    # nach vorn und in das linke Ende der Wanne bis an das Endstueck 180;
    # der Ruecklauf des Riemens laeuft davor
    zn = L['profil_z1'] - 3.0
    xb = sum(L['kf_buendel_x']) / 2.0
    zq = sum(L['kf_quer_z']) / 2.0
    t.append(f.linie(L['kf_nut_x'][0], L['platte_z1'] + 3.0,
                     L['kf_nut_x'][0], zn, KABEL, 1.6, '5 3'))
    t.append(f.linie(L['kf_nut_x'][0], zn, L['kf_nut_x'][1], zn, KABEL, 1.6,
                     '5 3'))
    t.append(band(f, [(L['kf_nut_x'][1], zn), (xb, L['profil_z1']),
                      (xb, zq), (L['xk_fest'] - w('endstueck_l'), zq)],
                  w('kf_buendel_b')))
    for z in (w('kf_binder_z1'), w('kf_binder_z2')):
        t.append(f.rect(L['kf_x'][0] + w('kf_steg'),
                        L['st_x']['Festpunkt'][0] - w('kf_steg'),
                        z - 0.6, z + 0.6, 'riemen'))
    r = q['X-Riemen Ruecklauf']
    t.append(f.rect(r.x[0], r.x[1], r.z[0], r.z[1], 'riemen'))
    # Wanne: Boden kraeftig, die Waende heller davor
    t.append(f.rect(*L['wanne_x'], *L['wanne_boden_z'], 'neu'))
    t.append(f.rect(*L['wanne_x'], L['wanne_boden_z'][1], L['wanne_z'][1],
                    'neu', fill_opacity='0.45'))
    # Kette an beiden Enden des X-Wegs gestrichelt, in der Mitte gefuellt
    for xw in (L['xw_min'], L['xw_max']):
        umr, _ = schleife(L, w, xw)
        t.append(f.poly(umr, 'kette', fill='none', stroke_dasharray='4 3'))
        t.append(f.rect(xw + tw('traeger_x_links'), xw + tw('xk_gelenk_x'),
                        TL['kh_fuss_z0'], TL['kh_leiste_z'][1], 'neu',
                        fill='none', stroke_dasharray='4 3'))
    xm = L['xw_mitte']
    umr, _ = schleife(L, w, xm)
    t.append(f.poly(umr, 'kette', fill_opacity='0.85'))
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


def stuetze_profil(w, L):
    """Profil der Wannenstuetzen (Y, Z): Platte hinter dem Rohr mit der
    Freifase an der Rohrkante, Block, Arm."""
    py, pzs = L['st_platte_y'], L['st_platte_z']
    by, bz = L['st_block_y'], L['st_block_z']
    ay, az = L['st_arm_y'], L['st_arm_z']
    fs = w('profil_fase')                 # Fase in der Innenecke
    return [(py[0], pzs[0]), (py[1], pzs[0]), (py[1], bz[0] + fs),
            (py[1] + fs, bz[0]), (by[1], bz[0]), (by[1], az[0]),
            (ay[1], az[0]), (ay[1], az[1]), (py[0], az[1])]


def portal_schnitt(f, w, L, tw, TL):
    """Rohr, Schiene, Wagen, Traegerplatte, Riemenhalter und beide Trume
    des X-Riemens im Schnitt (Blick von links)."""
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
    for ym in (L['xr_y'], L['xr_y_rueck']):
        t.append(f.rect(ym - L['riemen_innen'], ym + L['riemen_aussen'],
                        L['xr_z0'], L['xr_z1'], 'riemen'))
    return t


def querschnitt(f, w, L, tw, TL):
    """Schnitt durch die mittlere Stuetze (Blick von links, vorn rechts):
    Rohr, Schiene, Wagen, Traegerplatte, Riemenhalter, Riemen, Stuetze,
    Wanne mit Lasche, Unter- und Obertrum, Kettenhalter."""
    t = portal_schnitt(f, w, L, tw, TL)
    py = L['st_platte_y']
    t.append(f.poly(stuetze_profil(w, L), 'neu'))
    # Wanne: U mit der Lasche hinten (an dieser Stuetze)
    yi, y = L['wanne_innen_y'], L['wanne_y']
    zb, z = L['wanne_boden_z'], L['wanne_z']
    t.append(f.poly([(L['wanne_lasche_y'][0], zb[0]), (y[1], zb[0]),
                     (y[1], z[1]), (yi[1], z[1]), (yi[1], zb[1]),
                     (yi[0], zb[1]), (yi[0], z[1]), (y[0], z[1]),
                     (y[0], zb[1]), (L['wanne_lasche_y'][0], zb[1])], 'neu'))
    t += glieder_schnitt(f, w, L['xk_y'], L['xk_unter_z'], L['xk_ober_z'])
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
    # Schrauben: M5 hinten in die Nut, M3 durch die Lasche in den Block,
    # M3 von vorn durch die Traegerplatte in den Fuss
    t.append(f.rect(py[0] - w('m5_kopf_h'), py[0] - 0.0, -4.25, 4.25,
                    'stahl'))
    t.append(f.rect(py[0], L['profil_y0'] + 5.0, -2.5, 2.5, 'stahl'))
    _, yl = L['wanne_laschen'][0]
    t.append(f.rect(yl - 2.75, yl + 2.75, zb[1], zb[1] + 3.0, 'stahl'))
    t.append(f.rect(yl - 1.5, yl + 1.5, zb[1] - L['wanne_schraube'], zb[1],
                    'stahl'))
    zs = tw('kh_schraube_z')
    t.append(f.rect(tw('traeger_dicke') - tw('rh_senkung_t'),
                    tw('traeger_dicke') - tw('rh_senkung_t') + 3.0,
                    zs - 2.75, zs + 2.75, 'stahl'))
    t.append(f.rect(tw('traeger_dicke') - tw('rh_senkung_t')
                    - TL['kh_schraube'], tw('traeger_dicke')
                    - tw('rh_senkung_t'), zs - 1.5, zs + 1.5, 'stahl'))
    return t


def schnitt_fluegel(f, w, L, tw, TL):
    """Schnitt durch den Kabelfluegel in der Mitte des Buendels (Blick von
    links, vorn rechts): Rohr mit der oberen Nut, Fluegel, die Litzen und
    ihre Binder, beide Trume; dahinter Stuetze, Wanne und Endstueck 180,
    gestrichelt der Fuss des Kettenhalters, wenn der Toolhead links steht."""
    t = portal_schnitt(f, w, L, tw, TL)
    yn = (L['profil_y0'] + L['portal_y']) / 2.0
    zt = L['profil_z1']
    t.append(f.rect(yn - 3.1, yn + 3.1, zt - 6.0, zt, 'innen'))
    # dahinter: Stuetze, Wanne (U), Endstueck 180 auf dem Boden
    t.append(f.poly(stuetze_profil(w, L), 'neu', fill_opacity='0.35'))
    y, zb, z = L['wanne_y'], L['wanne_boden_z'], L['wanne_z']
    t.append(f.rect(y[0], y[1], zb[0], z[1], 'neu', fill_opacity='0.35'))
    t.append(f.rect(*L['xk_y'], *L['xk_unter_z'], 'kette',
                    fill_opacity='0.5'))
    # Fluegel im Schnitt, davor die Litzen: aus der Nut hoch, ueber den
    # Riemen nach vorn; je ein Binder um Buendel und Fluegel
    t.append(f.rect(*L['kf_y'], *L['kf_z'], 'neu'))
    yb = sum(L['kf_buendel_y']) / 2.0
    zq = sum(L['kf_quer_z']) / 2.0
    t.append(f.rect(yn - 2.6, yn + 2.6, zt - 5.6, zt - 0.4, 'kabel'))
    t.append(band(f, [(yn, zt - 3.0), (yb, zt + 3.0), (yb, zq),
                      (L['xk_y_mitte'], zq)], w('kf_buendel_t'), '0.75'))
    for zbi in (w('kf_binder_z1'), w('kf_binder_z2')):
        t.append(f.rect(L['kf_y'][0] - 0.8, L['kf_buendel_y'][1] + 0.8,
                        zbi - 0.6, zbi + 0.6, 'riemen', fill='none',
                        stroke_width='1.2'))
    # Fuss des Kettenhalters, wenn der Toolhead links steht
    fy = TL['kh_fuss_y']
    t.append(f.rect(fy[0], fy[1], TL['kh_fuss_z0'], f.b[1] + 5, 'neu',
                    fill='none', stroke_dasharray='4 3'))
    return t


# ---- Energiekette Y --------------------------------------------------------
def ansicht_y(f, w, L, portal, rahmen):
    """Von links (Blick nach +X, vorn rechts): beide 2060 im Schnitt, das
    linke 2040 mit der Schiene, Traeger, Wanne Y und Kette; der linke
    Schlitten mit dem Kettenhalter Y in der Mitte, Kette und Halter
    gestrichelt an beiden Enden des Y-Wegs."""
    t = []
    q = {p.name: p for p in portal}
    r = {p.name: p for p in rahmen}
    hell = {'fill_opacity': '0.35'}
    for y in (L['quer_y_hinten'], L['quer_y_vorn']):
        t.append(f.rect(y[0], y[1], *L['quer_z'], 'profil'))
    t.append(f.rect(*L['rahmen_y'], L['rahmen_z0'], L['rahmen_z1'],
                    'profil'))
    s = q['Y-Schiene links']
    t.append(f.rect(*L['y_schiene_y'], s.z[0], s.z[1], 'fuehrung'))
    for n in ('hinten', 'vorn'):
        b = r['Winkel 2040/2060 ' + n]
        t.append(f.rect(b.y[0], b.y[1], b.z[0], b.z[1], 'kauf',
                        fill_opacity='0.5', stroke_dasharray='4 3'))
    # Schlitten in der Mitte (davor liegen Kette und Halter)
    for n in ('X-Motor', 'Motorplatte', 'Motorhalter Saeule hinten',
              'Motorhalter Saeule aussen', 'Stirnblock links',
              'Platte links', 'Y-Wagen links'):
        b = q[n]
        art = 'kauf' if n == 'X-Motor' else (
            'fuehrung' if 'Wagen' in n else 'druck')
        t.append(f.rect(b.y[0], b.y[1], b.z[0], b.z[1], art, **hell))
    # Traeger: Wand am 2040, der Arm unter der Wanne (von der Seite deckt
    # die Wand den Arm)
    for y in L['ytr_y'].values():
        t.append(f.rect(*y, *L['ytr_wand_z'], 'neu'))
    # Wanne: Boden kraeftig, die Waende heller davor
    t.append(f.rect(*L['ywanne_y'], *L['ywanne_boden_z'], 'neu'))
    t.append(f.rect(L['ywanne_y'][0], L['ywanne_y'][1],
                    L['ywanne_boden_z'][1], L['ywanne_z'][1], 'neu',
                    fill_opacity='0.45'))
    # Kette und Halter an den Enden des Wegs gestrichelt, Portal in der
    # Mitte gefuellt
    kh = (q['Kettenhalter Y'], q['Kettenhalter Y Leiste aussen'])
    for dy in (-L['y_weg_hinten'], w('y_weg_vorn')):
        umr, _ = schleife_y(L, w, dy)
        t.append(f.poly(umr, 'kette', fill='none', stroke_dasharray='4 3'))
        b = q['Platte links']
        t.append(f.rect(b.y[0] + dy, b.y[1] + dy, b.z[0], b.z[1], 'druck',
                        fill='none', stroke_dasharray='4 3'))
        for b in kh:
            t.append(f.rect(b.y[0] + dy, b.y[1] + dy, b.z[0], b.z[1], 'neu',
                            fill='none', stroke_dasharray='4 3'))
    umr, _ = schleife_y(L, w, 0.0)
    t.append(f.poly(umr, 'kette', fill_opacity='0.85'))
    t.append(f.rect(kh[0].y[0], kh[0].y[1], kh[0].z[0], kh[0].z[1], 'neu'))
    t.append(f.rect(kh[1].y[0], kh[1].y[1], kh[1].z[0], kh[1].z[1], 'neu',
                    fill_opacity='0.6'))
    # Gelenke der Endstuecke
    for y, z in ((L['yk_fest'], L['yk_achse_unten']),
                 (w('yk_gelenk_y'), L['yk_achse_oben'])):
        t.append(f.kreis(y, z, 1.6, 'innen'))
    return t


def querschnitt_y(f, w, L, portal):
    """Schnitt durch den mittleren Traeger an der Laschenschraube (Blick
    von vorn, Portal in der Mitte): 2040 mit Schiene, Traeger, Wanne Y mit
    Lasche, Unter- und Obertrum; dahinter Schlitten, Kettenhalter Y und die
    M5 des Traegers. W13 geht hier aus der Nut, ueber die Wand."""
    t = []
    q = {p.name: p for p in portal}
    hell = {'fill_opacity': '0.4'}
    for n, art in (('Stirnblock links', 'druck'), ('Platte links', 'druck'),
                   ('Y-Wagen links', 'fuehrung')):
        b = q[n]
        t.append(f.rect(b.x[0], b.x[1], b.z[0], b.z[1], art, **hell))
    for n in ('Kettenhalter Y', 'Kettenhalter Y Leiste aussen',
              'Kettenhalter Y Leiste innen'):
        b = q[n]
        t.append(f.rect(b.x[0], b.x[1], b.z[0], b.z[1], 'neu', **hell))
    # 2040 mit den Nuten aussen und unten; darauf die Schiene
    xa = -L['aussen_x']
    z0, z1 = L['rahmen_z0'], L['rahmen_z1']
    t.append(f.rect(xa, xa + w('rahmen_b'), z0, z1, 'profil'))
    for zn in (L['nut_u_z'], L['nut_u_z'] + w('rahmen_b')):
        t.append(f.rect(xa, xa + 6.0, zn - 3.1, zn + 3.1, 'innen'))
    xm = xa + w('rahmen_b') / 2.0
    t.append(f.rect(xm - 3.1, xm + 3.1, z0, z0 + 6.0, 'innen'))
    s = q['Y-Schiene links']
    t.append(f.rect(s.x[0], s.x[1], s.z[0], s.z[1], 'fuehrung'))
    # M5 des Traegers (12 mm hinter dem Schnitt): Kopf aussen, Schaft durch
    # die Wand in die Hammermutter der unteren Seitennut
    xw0 = L['ytr_wand_x'][0]
    zn = L['nut_u_z']
    t.append(f.rect(xw0 - w('m5_kopf_h'), xw0, zn - w('m5_kopf_d') / 2.0,
                    zn + w('m5_kopf_d') / 2.0, 'stahl', fill_opacity='0.6'))
    # Traeger im Schnitt: Wand am 2040, Arm unter der Wanne
    wx, wz = L['ytr_wand_x'], L['ytr_wand_z']
    ax, az = L['ytr_arm_x'], L['ytr_arm_z']
    t.append(f.poly([(wx[1], wz[1]), (wx[0], wz[1]), (wx[0], az[1]),
                     (ax[0], az[1]), (ax[0], az[0]), (wx[1], az[0])], 'neu'))
    t.append(f.rect(xw0, xw0 + L['ytr_m5_schraube'], zn - 2.5, zn + 2.5,
                    'stahl', fill_opacity='0.6', stroke_dasharray='3 2'))
    # Wanne: U mit der Lasche innen (auf dem Arm)
    x, xi = L['ywanne_x'], L['ywanne_innen_x']
    zb, z = L['ywanne_boden_z'], L['ywanne_z']
    lx = L['ywanne_lasche_x'][1]
    t.append(f.poly([(x[0], zb[0]), (lx, zb[0]), (lx, zb[1]), (x[1], zb[1]),
                     (x[1], z[1]), (xi[1], z[1]), (xi[1], zb[1]),
                     (xi[0], zb[1]), (xi[0], z[1]), (x[0], z[1])], 'neu'))
    t += glieder_schnitt(f, w, L['yk_x'], L['yk_unter_z'], L['yk_ober_z'])
    # Laschenschraube: Kopf auf der Lasche, M3 x 8 in den Einsatz im Arm
    xl = L['ywanne_laschen'][0][0]
    k = w('m3_kopf_d') / 2.0
    t.append(f.rect(xl - k, xl + k, zb[1], zb[1] + 3.0, 'stahl'))
    t.append(f.rect(xl - 1.5, xl + 1.5, zb[1] - L['wanne_schraube'], zb[1],
                    'stahl'))
    # W13 (Y-Motor links) geht am Traeger aus der Nut, ueber die Wand
    t.append(f.kreis(sum(wx) / 2.0, wz[1] + 2.5, 2.25, 'kabel'))
    return t


def zahlen_block(t, ty, zeilen):
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))
    return ty + 10 + len(zeilen) * 15 + 18


def legende(t, ly, arten):
    for i, (art, s) in enumerate(arten):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    return ly + ((len(arten) + 3) // 4) * 18


def schreiben(ziel, t, W, H):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="100%" height="100%" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ziel, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ziel), W, 'x', H)


def kopf(titel, w):
    return [text(24, 30, titel, 14, TEXT, fett=True),
            text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Gedruckte '
                 'Kette: Teilung {}, außen {} × {}, innen {} × {} mm, '
                 'Biegeradius {} mm.'.format(
                     de(w('kette_teilung'), 0), de(w('kette_b'), 0),
                     de(w('kette_h'), 0), de(w('kette_innen_b'), 0),
                     de(w('kette_innen_h'), 1), de(w('kette_r'), 0)), 9,
                 GRAU)]


def zeichnung_x(w, L, tw, TL, portal, rev, th_rev):
    t = kopf('Energiekette X: Wanne, Wannenstützen, Kettenhalter, Kabelweg '
             '(Portal.py Rev. {}, ToolheadZ.py Rev. {})'.format(rev, th_rev),
             w)

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
        (L['kf_x'][0] + 1.0, w('kf_binder_z2'),
         'Kabelflügel: davor die Litzen,\n2 Binder durch die Schlitze'),
        (-190.0, L['profil_z1'] - 3.0, 'Litzen von der Y-Kette in der\n'
         'oberen Nut (gestrichelt)'),
        (xm + tw('traeger_x_links') + 4.0, TL['kh_fuss_z0'] + 6.0,
         'Kettenhalter (ToolheadZ.py)\nmit dem Anfangsstück'),
        (xm - 18.0, -40.0 + 30.0, 'Trägerplatte (Umriss),\nX-Wagen, '
         'Riemenhalter')],
        fa.ox - 12, 'end', abstand=25.0, unten=fa.oy + fa.hoehe + 4.0)
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

    # ---- Schnitt durch den Kabelfluegel -----------------------------------
    fc = Feld(780, fb.oy, (-46.0, 4.0), (-14.0, 66.0), 3.4)
    t += fc.ausschnitt('fluegel', schnitt_fluegel(fc, w, L, tw, TL))
    t += fc.rahmen('Kabelweg am Festpunkt: Schnitt durch den Kabelflügel')
    yb = sum(L['kf_buendel_y']) / 2.0
    zq = sum(L['kf_quer_z']) / 2.0
    t += fc.spalte([
        (L['xk_y_mitte'] + 2.0, zq, 'Litzen oben über den Riemen\n'
         'nach vorn in die Wanne'),
        (L['kf_y'][0], L['kf_z'][1] - 3.0, 'Kabelflügel (Schnitt), dahinter '
         'die\nStütze, die Wanne, das Endstück 180'),
        (yb, w('kf_binder_z2'), 'je ein Binder um Litzen und\nFlügel, durch '
         'die Schlitze'),
        (TL['kh_fuss_y'][0] + 2.0, 62.0, 'Fuß des Kettenhalters\n'
         '(Toolhead links, gestrichelt)'),
        (L['xr_y_rueck'], L['xr_z1'] - 1.0, 'Rücklauf'),
        (-26.0, L['profil_z1'] - 3.0, 'Litzen in der oberen\nNut des Rohrs'),
        (-1.0, 0.0, 'X-Wagen, Schiene')],
        fc.ox + fc.breite + 12, 'start', abstand=30.0)
    rl = L['xr_y_rueck'] - L['riemen_aussen']
    t += fc.luft(L['kf_buendel_y'][1], 14.0, rl, 14.0, '{} mm'.format(
        de(rl - L['kf_buendel_y'][1], 1)), dx=-4, dy=-6, anker='end')
    t += fc.luft(-3.0, TL['rh_z1'], -3.0, L['kf_quer_z'][0], '{} mm'.format(
        de(L['kf_quer_z'][0] - TL['rh_z1'], 1)), dx=4, dy=14)
    vorn = L['xk_y_mitte'] + w('kf_buendel_t') / 2.0
    t += fc.luft(vorn, 58.0, TL['kh_fuss_y'][0], 58.0, '{} mm'.format(
        de(TL['kh_fuss_y'][0] - vorn, 1)), dx=4, dy=-4)

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
        ('Kabelweg', 'in der oberen Nut des Rohrs von X {} bis {}, am '
         'Kabelflügel hoch ({} mm hinter dem Rücklauf, 2 Binder), oben {} mm '
         'über dem Riemenhalter nach vorn in die Wanne'.format(
             de(L['kf_nut_x'][0], 0, True), de(L['kf_nut_x'][1], 1, True),
             de(rl - L['kf_buendel_y'][1], 1),
             de(L['kf_quer_z'][0] - TL['rh_z1'], 1))),
        ('Schrauben', '3 × M5 × {} + Hammermutter (Stützen), 2 × M3 × {} + '
         'Einsatz (Laschen), 2 × M3 × {} + Scheibe + Einsatz (Endstück 180); '
         'Kettenhalter: 2 × M3 × {} von vorn, 2 × M3 × {} + Scheibe '
         '(Anfangsstück)'.format(
             de(L['st_m5_schraube'], 0), de(L['wanne_schraube'], 0),
             de(L['xk_fest_schraube'], 0), de(TL['kh_schraube'], 0),
             de(TL['kh_ende_schraube'], 0))),
    ]
    ly = zahlen_block(t, ty, zeilen)
    ly = legende(t, ly, (('neu', 'neu zu drucken (PETG)'),
                         ('kette', 'Energiekette (gedruckt)'),
                         ('toolhead', 'Toolhead'),
                         ('druck', 'Portal'),
                         ('kauf', 'Kaufteil'),
                         ('profil', 'Aluprofil'),
                         ('fuehrung', 'Linearführung'),
                         ('stahl', 'Schraube'),
                         ('kabel', 'Litzen')))
    t.append(text(24, ly + 10, 'Gestrichelt: Kette und Kettenhalter an den '
                  'Enden des X-Wegs, die Trägerplatte (sie steht vor der '
                  'Kette).', 8.5, GRAU))
    schreiben(ZIEL, t, int(fa.ox + fa.breite + 200), int(ly + 26))


def zeichnung_y(w, L, portal, rev):
    t = kopf('Energiekette Y: Wanne Y, Träger, Kettenhalter Y '
             '(Portal.py Rev. {})'.format(rev), w)
    rahmen, _ = bauraum.y_kette_rahmen(w, L)
    hinten, vorn = -L['y_weg_hinten'], w('y_weg_vorn')

    # ---- Ansicht von links -------------------------------------------------
    fa = Feld(250, 92, (-275.0, 235.0), (-135.0, 82.0), 1.5)
    t += fa.ausschnitt('links', ansicht_y(fa, w, L, portal, rahmen))
    t += fa.rahmen('Ansicht von links (vorn rechts): Portal in der Mitte, '
                   'gestrichelt am hinteren Schienenende und an der '
                   'vorderen Grenze')
    q = {p.name: p for p in portal}
    ra = L['xk_bogen_r'][1]
    _, yb_m = schleife_y(L, w, 0.0)
    _, yb_v = schleife_y(L, w, vorn)
    wi = next(p for p in rahmen if p.name == 'Winkel 2040/2060 hinten')
    mo = q['X-Motor']
    t += fa.spalte([
        (sum(L['quer_y_hinten']) / 2.0, L['quer_z'][0] + 10.0,
         'hinteres 2060'),
        (wi.y[1] - 4.0, wi.z[1] - 3.0, 'Winkel 20 mm\n(Lage angenommen)'),
        (-185.0, L['rahmen_z1'] - 4.0, 'linkes 2040 (Rahmen)\nmit der '
         'Y-Schiene'),
        (L['ywanne_binder'][0][1], L['ywanne_boden_z'][1],
         'Binderschlitze\n(Zugentlastung)'),
        (L['yk_fest'] - 14.0, L['yk_achse_unten'],
         'Festpunkt: Endstück 180,\n2 × M3 in den Träger'),
        (sum(L['ytr_y']['Festpunkt']) / 2.0, L['ytr_wand_z'][0] + 2.0,
         'Träger am Festpunkt'),
        (-210.0, L['yk_ober_z'][1], 'am hinteren Schienen-\nende '
         '(gestrichelt)'),
        (L['khy_y'][0] + 4.0, L['khy_z'][0] + 2.0,
         'Kettenhalter Y auf der Platte\ndes linken Schlittens')],
        fa.ox - 12, 'end', abstand=28.0)
    t += fa.spalte([
        ((mo.y[0] + mo.y[1]) / 2.0, mo.z[1] - 6.0, 'X-Motor (linker '
         'Schlitten)'),
        (yb_m + ra - 2.0, L['yk_bogen_z'], 'Schleife nach vorn\n(Portal in '
         'der Mitte)'),
        (yb_v + ra - 1.0, L['yk_bogen_z'] + 14.0, 'vordere Grenze, Z unten\n'
         '(gestrichelt)'),
        (L['ywanne_y'][1] - 20.0, L['ywanne_z'][1] - 2.0,
         'Wanne Y, {} mm'.format(de(L['ywanne_y'][1] - L['ywanne_y'][0],
                                    1))),
        (sum(L['ytr_y']['vorn']) / 2.0, L['ytr_wand_z'][0] + 2.0,
         'Träger mitte und vorn:\nM5 in der unteren Seitennut'),
        (sum(L['quer_y_vorn']) / 2.0, L['quer_z'][0] + 10.0,
         'vorderes 2060'),
        (40.0, sum(L['yk_unter_z']) / 2.0, 'Untertrum auf den Riegeln')],
        fa.ox + fa.breite + 12, 'start', abstand=28.0)
    t += fa.mass(150.0, L['yk_achse_unten'], L['yk_achse_oben'],
                 '2 R = {} mm'.format(de(2.0 * w('kette_r'), 0)))
    t += quer_mass(fa, L['ywanne_y'][0], L['ywanne_y'][1], -92.0,
                   '{} mm'.format(de(L['ywanne_y'][1] - L['ywanne_y'][0], 1)))
    g_v = w('yk_gelenk_y') + vorn
    g_max = w('yk_gelenk_y') + L['yk_dy_bereich'][1]
    t += fa.luft(g_v, L['yk_ober_z'][1] + 8.0, g_max,
                 L['yk_ober_z'][1] + 8.0, 'Reserve {} mm'.format(
                     de(L['yk_reserve_vorn'], 1)), dx=4, dy=-4)

    # ---- Schnitt durch den mittleren Traeger -------------------------------
    fb = Feld(250, fa.oy + fa.hoehe + 80, (-312.0, -238.0), (-82.0, 22.0),
              3.4)
    t += fb.ausschnitt('quer_y', querschnitt_y(fb, w, L, portal))
    t += fb.rahmen('Schnitt durch den mittleren Träger an der Laschen'
                   'schraube (Blick von vorn)')
    x = L['ywanne_x']
    xw0 = L['ytr_wand_x'][0]
    t += fb.spalte([
        (L['khy_leiste_aussen_x'][0] + 1.0, L['khy_z'][0] + 2.0,
         'Kettenhalter Y mit den\nLeisten (dahinter)'),
        (L['yk_x'][0] + 2.0, sum(L['yk_ober_z']) / 2.0,
         'Obertrum\n(Boden unten)'),
        (L['yk_x'][0] + 2.0, sum(L['yk_unter_z']) / 2.0,
         'Untertrum\n(Boden oben)'),
        (x[0] + 1.0, L['ywanne_z'][1] - 2.0, 'Wanne Y'),
        (L['ytr_arm_x'][0] + 3.0, L['ytr_arm_z'][0] + 2.0,
         'Arm des Trägers\nunter der Wanne')],
        fb.ox - 12, 'end', abstand=32.0)
    t += fb.spalte([
        (-262.0, 4.0, 'Stirnblock, Platte\n(dahinter)'),
        (-247.0, -22.0, 'Y-Wagen, Y-Schiene'),
        (-250.0, -45.0, 'linkes 2040'),
        (xw0 - 2.0, L['nut_u_z'] + 3.0, 'M5 + Hammermutter in der\nunteren '
         'Seitennut ({} mm dahinter)'.format(
             de(L['ywanne_laschen'][0][1] - L['ytr_m5_y']['mitte'], 0))),
        (sum(L['ytr_wand_x']) / 2.0, L['ytr_wand_z'][1] + 3.5,
         'W13 (Y-Motor links): hier\naus der Nut, über die Wand'),
        (L['ywanne_laschen'][0][0], L['ywanne_boden_z'][1] + 2.0,
         'Lasche: M3 × {} in den\nEinsatz im Arm'.format(
             de(L['wanne_schraube'], 0))),
        (-257.0, L['rahmen_z0'] + 3.0, 'untere Nut (belegt)')],
        fb.ox + fb.breite + 12, 'start', abstand=32.0)
    t += fb.luft(L['yk_x'][1], 7.0, -L['platte_x1'], 7.0, '{} mm'.format(
        de(-L['platte_x1'] - L['yk_x'][1], 0)), dx=4, dy=-6)
    t += fb.luft(x[1], -62.0, xw0, -62.0, '{} mm'.format(
        de(xw0 - x[1], 1)), dx=4, dy=12)
    t += fb.mass(-309.0, L['yk_achse_unten'], L['yk_achse_oben'], '2 R',
                 dx=4)
    t += quer_mass(fb, L['yk_x'][0], L['yk_x'][1], L['yk_ober_z'][1] + 3.0,
                   '{} mm'.format(de(w('kette_b'), 0)))

    # ---- Zahlen ------------------------------------------------------------
    ty = fb.oy + fb.hoehe + 46
    zeilen = [
        ('Kette', '{} Glieder = {} mm zwischen den Gelenken ({} gebraucht: '
         '(Weg {} + Reserve {} + 2 × {} Luft) / 2 + Bogen {}), mit '
         'Anfangsstück und Endstück 180 {} mm'.format(
             L['yk_glieder'], de(L['yk_laenge'], 0), de(L['yk_noetig'], 1),
             de(L['y_weg_hinten'] + w('y_weg_vorn'), 1),
             de(w('yk_reserve'), 0), de(w('luft_bau'), 0),
             de(math.pi * w('kette_r'), 1),
             de(L['yk_laenge'] + 2.0 * w('endstueck_l'), 0))),
        ('Y-Weg', 'Portal von {} (hinteres Schienenende) bis {} (Z unten, '
         '3 mm vor dem vorderen 2060); die Kette ließe es bis {}: {} mm '
         'Reserve'.format(de(hinten, 1, True), de(vorn, 0, True),
                          de(L['yk_dy_bereich'][1], 1, True),
                          de(L['yk_reserve_vorn'], 1))),
        ('Festpunkt', 'Gelenk des Endstücks 180 bei Y {}: am hinteren '
         'Schienenende bleiben {} mm Untertrum in der Wanne'.format(
             de(L['yk_fest'], 1, True), de(w('luft_bau'), 0))),
        ('Höhen', 'Kettenhalter Y {} mm auf der Platte, Obertrum ab Z {}, '
         'Untertrum ab {} (2 R tiefer), Wannenboden {}'.format(
             de(w('khy_dicke'), 0), de(L['yk_ober_z'][0], 1, True),
             de(L['yk_unter_z'][0], 1, True),
             de(L['ywanne_boden_z'][0], 1, True))),
        ('Wanne', 'Y {} bis {} ({} mm, passt in den A1), auf drei Trägern: '
         'am Festpunkt, mitte bei Y {}, vorn bei Y {}'.format(
             de(L['ywanne_y'][0], 1, True), de(L['ywanne_y'][1], 1, True),
             de(L['ywanne_y'][1] - L['ywanne_y'][0], 1),
             de(w('ytr_y_mitte'), 0, True), de(w('ytr_y_vorn'), 0, True))),
        ('Schrauben', '3 × M5 × {} + Hammermutter (Träger), 2 × M3 × {} + '
         'Einsatz (Laschen), 2 × M3 × {} + Scheibe + Einsatz (Endstück '
         '180); Kettenhalter Y: 2 × M3 × {} von unten, 2 × M3 × {} + '
         'Scheibe (Anfangsstück)'.format(
             de(L['ytr_m5_schraube'], 0), de(L['wanne_schraube'], 0),
             de(L['xk_fest_schraube'], 0), de(L['khy_schraube'], 0),
             de(L['khy_ende_schraube'], 0))),
    ]
    ly = zahlen_block(t, ty, zeilen)
    ly = legende(t, ly, (('neu', 'neu zu drucken (PETG)'),
                         ('kette', 'Energiekette (gedruckt)'),
                         ('druck', 'Portal'),
                         ('kauf', 'Kaufteil, Winkel'),
                         ('profil', 'Aluprofil'),
                         ('fuehrung', 'Linearführung'),
                         ('stahl', 'Schraube'),
                         ('kabel', 'Kabel')))
    t.append(text(24, ly + 10, 'Gestrichelt: Kette, Platte und Kettenhalter '
                  'Y an den Enden des Y-Wegs, die Winkel an den 2060 '
                  '(20 mm, ihre Lage angenommen).', 8.5, GRAU))
    schreiben(ZIEL_Y, t, int(fa.ox + fa.breite + 200), int(ly + 26))


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    portal, _ = bauraum.portal_bauraeume(w, L)
    FARBE.setdefault('stahl', ('#c3c8cf', '#4a4f57'))
    zeichnung_x(w, L, tw, TL, portal, pm.REVISION, th.REVISION)
    zeichnung_y(w, L, portal, pm.REVISION)


if __name__ == '__main__':
    main()
