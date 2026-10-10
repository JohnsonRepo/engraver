#!/usr/bin/env python3
"""Rechnerische Pruefung des Pi-Halters (fusion/PiHalter) — laeuft ohne
Fusion.

Importiert PiHalter.py, Elektronik.py, Portal.py und ToolheadZ.py mit
gestubbtem adsk-Modul und prueft: Abgleich der Rahmenmasse, Lage an der
Rueckseite des hinteren 2060 rechts neben dem Elektronik-Kasten, Freiraum
gegen Portal und Toolhead ueber den ganzen Weg, gegen Kasten, Haube, Rahmen
und die Kabel in der mittleren Nut, die Verschraubung in der Nut mit
Werkzeugzugang, den Pi (Lochbild, Stehbolzen, Schrauben, Stecker, ganz
ueber dem 2060), den Wandler mit seinen Kabelbindern, die Haube (innen frei,
Dome, Schrauben, Lueftung) und den Druck. Gibt die Stueckliste aus.

    python3 tools/pihalter_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import elektronik_check                               # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
PIHALTER = os.path.join(HIER, '..', 'fusion', 'PiHalter', 'PiHalter.py')
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
WERKZEUG_LAENGE = 20.0  # kuerzester nutzbarer Inbus-Schenkel
NUT_LIPPE = 1.8         # Hammermutter Nut 6 [w], wie elektronik_check
# Buendel in der mittleren Nut der Rueckseite (W2, W10, W14, W18), wie es
# an der Flaeche anliegt [w]: so hoch und so dick
KABEL_H, KABEL_T = 12.0, 8.0
SD_UEBERSTAND = 2.5     # SD-Karte steht so weit ueber die Platine [w]


def laden():
    """Module und Lagen: Toolhead, Portal, Elektronik, Pi-Halter."""
    th = bauraum.modul_laden()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    em = bauraum.modul_laden(elektronik_check.ELEKTRONIK, 'elektronik')
    hm = bauraum.modul_laden(PIHALTER, 'pihalter')
    return th, pm, em, hm


def teile(hw, HL):
    """Halter mit allem, was daran sitzt, als Quader (fest am Rahmen):
    Platte, Stehbolzen (als ein Quader), Pi mit Bauteilen, die zwei
    Stecker, der Wandler, die Koepfe der M5 und die Dome fuer die Haube.
    Die Haube selbst liefert haube(): Sie umschliesst all das."""
    Q = Quader
    y0, y1 = HL['platte_y']
    xs = [x for x, _ in HL['pi_loecher']]
    zs = [z for _, z in HL['pi_loecher']]
    r = hw('steg_d') / 2.0
    q = [Q('Platte', *HL['x'], y0, y1, *HL['z']),
         Q('Stehbolzen', min(xs) - r, max(xs) + r, *HL['steg_y'],
           min(zs) - r, max(zs) + r),
         Q('Pi', *HL['pi_x'], HL['bauteile_y'][0], HL['pcb_y'][1],
           *HL['pi_z']),
         Q('Wandler', *HL['wandler_x'], *HL['wandler_y'], *HL['wandler_z'])]
    for n, (sx, sy, sz) in sorted(HL['stecker'].items()):
        q.append(Q('Stecker ' + n, *sx, *sy, *sz))
    q.append(Q('Stecker USB-A', *HL['stecker_a'][0], *HL['stecker_a'][1],
               *HL['stecker_a'][2]))
    rk = hw('m5_kopf_d') / 2.0
    for i, (x, z) in enumerate(HL['m5']):
        q.append(Q('M5-Kopf {}'.format(i + 1), x - rk, x + rk,
                   *HL['kopf_y'], z - rk, z + rk))
    rd = hw('dom_d') / 2.0
    for i, (x, z) in enumerate(HL['dome']):
        q.append(Q('Dom {}'.format(i + 1), x - rd, x + rd, *HL['dom_y'],
                   z - rd, z + rd))
    return q


def haube(HL):
    """Die Haube als Huelle (fuer alles, was von aussen kommt)."""
    return Quader('Haube', *HL['haube_x'], *HL['haube_y'], *HL['haube_z'])


def kabelbuendel(L, EL):
    """Kabel in der mittleren Nut der Rueckseite des hinteren 2060: vom Ende
    des Kanals (rechts neben der Montageplatte) zum rechten 2040, wie die
    Kabelwege in tools/elektronik_zeichnen.py."""
    zm = L['quer_z'][0] + 30.0
    y = L['quer_y_hinten'][0]
    return Quader('Kabel mittlere Nut', EL['platte_x'][1], L['R'] + 15.0,
                  y - KABEL_T, y, zm - KABEL_H / 2.0, zm + KABEL_H / 2.0)


def engste(a_liste, b_liste):
    best = (float('inf'), None, None)
    for a in a_liste:
        for b in b_liste:
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def main():
    th, pm, em, hm = laden()
    tw, TL = th.w, th.lage()
    w, L = pm.w, pm.lage()
    ew, EL = em.w, em.lage()
    hw, HL = hm.w, hm.lage()
    p = Pruefung()
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, _, _, _ = portal_check.y_weg(w, L, TL, feste_th, bewegte_th)
    fach = portal_check.elektronikfach(w, L)
    T = teile(hw, HL)
    TA = T + [haube(HL)]               # von aussen gesehen: mit Haube
    (x0, x1), (y0, y1), (z0, z1) = HL['x'], HL['platte_y'], HL['z']

    # ------------------------------------------------------------------
    p.titel('1) Abgleich PiHalter.py <-> Portal.py und Elektronik.py')
    for text, ist, soll in (
            ('Rueckseite hinteres 2060', hw('quer_y1'),
             L['quer_y_hinten'][0]),
            ('Oberkante 2060 = Unterkante 2040', hw('rahmen_z0'),
             L['rahmen_z0']),
            ('Tisch (Unterkante 2060)', HL['tisch_z'], L['quer_z'][0]),
            ('obere Nut der Rueckseite', HL['nut_z'], EL['quer_nut_z'][2]),
            ('M5-Schraube wie die Montageplatte', hw('m5_l'),
             EL['m5_schraube']),
            ('Platte so dick wie die Montageplatte', hw('platte_dicke'),
             ew('platte_dicke'))):
        p.ok(text, abs(ist - soll), 0.01, '<=')
    for name in ('nut_oben', 'nut_v_t', 'nut_b', 'nut_t', 'nut_kammer_b',
                 'nut_kammer_t', 'kern_d', 'm5_durchgang', 'm5_kopf_d',
                 'm5_kopf_h', 'inbus_frei_d', 'luft_bau', 'fase_fuss',
                 'insert_m3_d', 'insert_m3_t', 'm3_durchgang'):
        p.ja('{} gleich in PiHalter.py und Elektronik.py'.format(name),
             abs(hw(name) - ew(name)) < 1e-9,
             '   ({} / {})'.format(hw(name), ew(name)))

    # ------------------------------------------------------------------
    p.titel('2) Lage: Rueckseite des hinteren 2060, rechts neben dem Kasten')
    p.info('Platte X', x0)
    p.info('       bis', x1)
    p.info('Platte Z', z0)
    p.info('       bis', z1)
    p.ok('Platte liegt an der Rueckseite des 2060',
         abs(y1 - L['quer_y_hinten'][0]), 0.01, '<=')
    for x, z in HL['m5']:
        p.ok('M5 bei X {:+.1f} auf der Mitte der oberen Nut'.format(x),
             abs(z - HL['nut_z']), 0.01, '<=')
    p.ok('rechts neben der Montageplatte des Kastens',
         x0 - EL['platte_x'][1], 3.0)
    p.ok('zwischen den 2040 (Fach links und rechts)',
         min(x0 - fach.x[0], fach.x[1] - x1), 0.0)
    p.ok('ueber dem Fach nur in der Mitte (|X| <= 225)',
         225.0 - max(abs(x0), abs(x1)), 0.0)
    y_tr = portal_check.hohe_zone_y(w, TL, d_schiene)
    p.ok('   und hinter dem Anfang der hohen Zone (Y {:.1f})'.format(y_tr),
         y_tr - y1, 0.0)
    p.ok('alles vor dem hinteren Ende des Fachs',
         min(q.y[0] for q in TA) - fach.y[0], 0.0)
    p.ok('alles ueber dem Tisch (Fach unten)',
         min(q.z[0] for q in TA) - fach.z[0], 0.0)
    p.ok('Pi ganz ueber der Oberkante des 2060 (kein Alu vor der Antenne)',
         HL['pi_z'][0] - hw('rahmen_z0'), 1.0)

    # ------------------------------------------------------------------
    p.titel('3) Freiraum gegen Portal und Toolhead (ganzer Weg)')
    eng, _ = portal_check.luft_hinten(w, L, TL, feste_th, bewegte_th, TA)
    p.ok('{} <-> {} (Portal {:+.1f})'.format(eng[1], eng[2], eng[3]),
         eng[0], hw('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('4) Freiraum gegen Kasten, Haube, Rahmen und Kabel')
    kasten = elektronik_check.elektronik_quader(ew, EL)
    d, a, b = engste(TA, kasten)
    p.ok('{} <-> {} (Elektronik-Kasten)'.format(a, b), d, 3.0)
    rahmen = portal_check.quer_quader(w, L) + [
        q for q in bauraum.portal_bauraeume(w, L)[0]
        if q.name.startswith(('Y-Schiene', 'Rahmen 2040', 'Y-Riemen',
                              'Y-Ruecklauf'))]
    d, a, b = engste([q for q in TA if q.name != 'Platte'], rahmen)
    p.ok('{} <-> {} (Rahmen)'.format(a, b), d, 1.0)
    d, a, b = engste([T[0]], [r for r in rahmen if r.name != '2060 hinten'])
    p.ok('Platte <-> {} (Rahmen ausser dem 2060, an dem sie liegt)'.format(b),
         d, 1.0)
    kb = kabelbuendel(L, EL)
    d, a, b = engste([q for q in TA if not q.name.startswith('Stecker')],
                     [kb])
    p.ok('{} ueber den Kabeln in der mittleren Nut'.format(a), d, 3.0)
    d, a, b = engste([q for q in T if q.name.startswith('Stecker')], [kb])
    p.ok('{} ueber den Kabeln in der mittleren Nut'.format(a), d, 2.0)
    m5_kasten = [x for x, z in EL['m5'] if abs(z - HL['nut_z']) < 1e-6]
    hl = hw('hammer_l') / 2.0
    p.ok('Hammermutter neben der des Kastens in derselben Nut',
         min(abs(x - xk) for x, _ in HL['m5'] for xk in m5_kasten) - 2 * hl,
         2.0)

    # ------------------------------------------------------------------
    p.titel('5) Montage: 2 x M5 in Hammermuttern der oberen Nut')
    p.ok('M5x{:.0f}: Gewinde in der Hammermutter'.format(hw('m5_l')),
         HL['m5_spitze'] - NUT_LIPPE, 3.5)
    p.ok('M5x{:.0f}: steht nicht auf dem Nutgrund auf'.format(hw('m5_l')),
         (hw('nut_t') + hw('nut_kammer_t')) - HL['m5_spitze'], 0.0)
    rk = hw('m5_kopf_d') / 2.0
    p.ok('Kopf innerhalb der Platte (seitlich)',
         min(min(x - x0, x1 - x) for x, _ in HL['m5']) - rk, 0.5)
    p.ok('Kopf innerhalb der Platte (unten)',
         min(z for _, z in HL['m5']) - rk - z0, 0.5)
    koepfe = [q for q in T if q.name.startswith('M5-Kopf')]
    rest = [q for q in T if q.name not in ('Platte',)
            and not q.name.startswith('M5-Kopf')]
    d, a, b = engste(koepfe, rest)
    p.ok('{} frei von {}'.format(a, b), d, 1.0)
    boxen = rest + kasten
    schlecht = (float('inf'), None)
    for x, z in HL['m5']:
        pt = (x, HL['kopf_y'][0], z)
        dk, wer = bauraum.freier_korridor(pt, 'y', -1,
                                          hw('inbus_frei_d') / 2.0, boxen)
        if dk < schlecht[0]:
            schlecht = (dk, wer)
    p.ok('Inbus von hinten an beide Koepfe (vor der Haube)'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)

    # ------------------------------------------------------------------
    p.titel('6) Pi Zero 2 W [w]: Lochbild, Stehbolzen, Schrauben, Stecker')
    xs = sorted({round(x, 6) for x, _ in HL['pi_loecher']})
    zs = sorted({round(z, 6) for _, z in HL['pi_loecher']})
    p.ok('Lochbild laengs 58 mm', abs(xs[1] - xs[0] - 58.0), 0.01, '<=')
    p.ok('Lochbild quer 23 mm', abs(zs[1] - zs[0] - 23.0), 0.01, '<=')
    p.ok('Stehbolzen: Wand um das Kernloch',
         (hw('steg_d') - hw('m25_kern')) / 2.0, 1.5)
    for pcb in (hw('pi_pcb') - 0.4, hw('pi_pcb') + 0.2):
        p.ok('M2.5x{:.0f} greift bei {:.1f} mm Platine'.format(
            hw('m25_l'), pcb), hw('m25_l') - pcb, 3.5)
    p.ok('Kernloch tiefer als die Schraube reicht',
         (HL['kernloch_y'][1] - HL['kernloch_y'][0]) - HL['m25_eingriff'],
         1.0)
    p.ok('Kernloch endet in der Platte (bleibt geschlossen)',
         y1 - HL['kernloch_y'][1], 2.0)
    for n, (sx, sy, sz) in sorted(HL['stecker'].items()):
        p.ok('Stecker {}: frei von der Platte'.format(n), y0 - sy[1], 1.0)
    u, pw = HL['stecker']['USB'], HL['stecker']['PWR']
    p.ok('Stecker USB und PWR nebeneinander',
         max(u[0][0] - pw[0][1], pw[0][0] - u[0][1]), 0.5)
    p.ok('Stehbolzen unter den Loechern frei vom Rand der Platine',
         hw('pi_loch_rand') - hw('steg_d') / 2.0, 0.0)
    p.ok('SD-Karte rechts: frei bis zum Rand des Fachs',
         fach.x[1] - (HL['pi_x'][1] + SD_UEBERSTAND), 20.0)

    # ------------------------------------------------------------------
    p.titel('7) Wandler 24 -> 5 V: Lage und Kabelbinder')
    bt, bb = hw('binder_t'), hw('binder_b')
    wx, wz, wy = HL['wandler_x'], HL['wandler_z'], HL['wandler_y']
    p.info('Wandler [v]: laengs X', wx[1] - wx[0])
    p.info('             hoch (Z)', wz[1] - wz[0])
    p.info('             nach hinten (Y), hoechstens', wy[1] - wy[0])
    p.ok('Wandler links in der Platte', wx[0] - x0, 1.5)
    p.ok('Kabelbinder senkrecht: auf einem Wandler ab so viel Laenge',
         HL['binder_x'][1] - HL['binder_x'][0] + bb, 40.0, '<=')
    p.ok('Kabelbinder laufen nicht ueber die Enden (Eingang, USB-Buchse)',
         min(HL['binder_x'][0] - bb / 2.0 - wx[0],
             wx[1] - HL['binder_x'][1] - bb / 2.0), 5.0)
    p.ok('USB-A-Stecker rechts im Wandler: frei vom Pi',
         HL['pi_x'][0] - HL['stecker_a'][0][1], 1.0)
    p.ok('oberer Schlitz unter der Oberkante der Platte',
         z1 - (max(HL['binder_z']) + bt / 2.0), 1.5)
    p.ok('unterer Schlitz ueber der Oberkante des 2060 (Binder laufen vorn '
         'um die Platte)', min(HL['binder_z']) - bt / 2.0 - hw('rahmen_z0'),
         2.0)
    p.ok('Wandler ueber den M5-Koepfen (Inbus frei)',
         wz[0] - (HL['nut_z'] + rk), 1.0)
    # Schlaufe: auf der Seite am 2060 von Schlitz zu Schlitz, zweimal durch
    # die Platte und hinten ueber den Wandler
    ec = elektronik_check
    schlaufe = ec.binder_schlaufe(
        max(HL['binder_z']) - min(HL['binder_z']) - bt, hw('platte_dicke'),
        wz[1] - wz[0], wy[1] - wy[0], (hw('binder_luft'),) * 2)
    p.ok('Kabelbinder {}: Schlaufe um Platte und Wandler'.format(ec.BINDER),
         schlaufe, math.pi * ec.BINDER_BUENDEL_D, '<=')

    # ------------------------------------------------------------------
    p.titel('8) Haube: innen frei, Dome, Schrauben, Lueftung')
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = (HL['haube_x'], HL['haube_y'],
                                          HL['haube_z'])
    (ix0, ix1), (iy0, iy1), (iz0, iz1) = HL['haube_innen']
    ht = hw('haube_wand')
    p.ok('Haube im Umriss der Platte (X, Z)',
         max(abs(hx0 - x0), abs(hx1 - x1), abs(hz0 - z0), abs(hz1 - z1)),
         0.01, '<=')
    p.ok('Waende stehen auf der Platte', abs(hy1 - y0), 0.01, '<=')
    p.ok('Wandstaerke (druckgerecht: 1,7 bis 2,0 robust)', ht, 1.7)
    dome = [q for q in T if q.name.startswith('Dom')]
    innen = [q for q in T if q.name != 'Platte' and q not in dome]
    rand = min(min(q.x[0] - ix0, ix1 - q.x[1], q.y[0] - iy0, iz1 - q.z[1])
               for q in innen)
    p.ok('alles am Halter innen (Seiten, Rueckwand, Dach)', rand, 1.0)
    p.ok('Rueckwand hinter Wandler und Kopf des Kabelbinders',
         HL['wandler_y'][0] - hw('binder_kopf') - iy0, 1.0)
    p.ok('Rueckwand hinter dem Pi (Platz fuer einen Kuehlkoerper)',
         HL['bauteile_y'][0] - iy0, 10.0)
    p.ok('SD-Karte frei von der rechten Wand',
         ix1 - (HL['pi_x'][1] + SD_UEBERSTAND), 2.0)
    p.ok('links Platz fuer W18 bis zum Eingang des Wandlers',
         HL['wandler_x'][0] - ix0, 10.0)
    p.ok('Dach ueber dem Kabelbinder im oberen Schlitz',
         iz1 - (max(HL['binder_z']) + hw('binder_t') / 2.0), 2.0)
    d, a, b = engste(dome, innen)
    p.ok('{} frei von {}'.format(a, b), d, 1.5)
    p.ok('Dome frei von Seiten und Dach',
         min(min(q.x[0] - ix0, ix1 - q.x[1], iz1 - q.z[1]) for q in dome),
         1.0)
    p.ok('Dom: Wand um den Einsatz',
         (hw('dom_d') - hw('insert_m3_d')) / 2.0, 2.0)
    p.ok('Dom: Einsatz kuerzer als der Dom',
         HL['dom_y'][1] - HL['dom_y'][0] - hw('insert_m3_t'), 10.0)
    p.ok('Dom endet vor der Rueckwand (Haube steht auf den Waenden)',
         HL['dom_y'][0] - iy0, 0.1)
    p.ok('M3x{:.0f}: Gewinde im Einsatz'.format(hw('m3_l')),
         HL['m3_eingriff'], 4.0)
    p.ok('M3x{:.0f}: Spitze im Sackloch'.format(hw('m3_l')),
         hw('insert_m3_t') - (hw('m3_l') - ht), 0.5)
    kr = hw('m3_kopf_d') / 2.0
    p.ok('M3-Koepfe ganz auf der Rueckwand',
         min(min(x - kr - hx0, hx1 - x - kr, z - kr - hz0, hz1 - z - kr)
             for x, z in HL['dome']), 1.0)
    schlecht = (float('inf'), None)
    for x, z in HL['dome']:
        dk, wer = bauraum.freier_korridor((x, HL['m3_kopf_y'][0], z), 'y',
                                          -1, hw('inbus_frei_d') / 2.0,
                                          kasten + rahmen)
        if dk < schlecht[0]:
            schlecht = (dk, wer)
    p.ok('Inbus von hinten an die M3'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)
    ls = HL['lueftung']
    p.info('Lueftungsschlitze in der Rueckwand', len(ls), '')
    p.info('   Querschnitt zusammen (Zuluft: unten offen)',
           sum((u1 - u0) * (v1 - v0) for u0, v0, u1, v1 in ls), 'mm2')
    p.ok('Schlitze ueber Pi und Wandler (keine Platine dahinter)',
         min(v0 for _, v0, _, _ in ls)
         - max(HL['pi_z'][1], HL['wandler_z'][1]), 2.0)
    p.ok('Schlitze unter dem Dach', iz1 - max(v1 for _, _, _, v1 in ls), 0.5)
    p.ok('Schlitze innerhalb der Seitenwaende',
         min(min(u0 - ix0, ix1 - u1) for u0, _, u1, _ in ls), 1.0)
    p.ok('Schlitze neben den M3-Koepfen',
         min(max(u0 - (x + kr), (x - kr) - u1, v0 - (z + kr), (z - kr) - v1)
             for u0, v0, u1, v1 in ls for x, z in HL['dome']), 2.0)

    # ------------------------------------------------------------------
    p.titel('9) Druck: Halter mit der Seite am 2060, Haube mit der Rueckwand '
            'aufs Bett')
    p.ok('Halter: groesste Kante', max(x1 - x0, z1 - z0), BETT, '<=')
    p.info('Halter: Hoehe beim Druck (Platte + Dome)',
           y1 - min(HL['steg_y'][0], HL['dom_y'][0]))
    rd = hw('dom_d') / 2.0
    vol = ((x1 - x0) * (z1 - z0) * (y1 - y0) + len(HL['dome']) * 3.14159
           * rd * rd * (HL['dom_y'][1] - HL['dom_y'][0])) / 1000.0
    p.info('Halter: Volumen voll (ohne Loecher)', vol, 'cm3')
    p.info('Halter: Masse voll (PETG 1,27 g/cm3)', vol * 1.27, 'g')
    p.ok('Haube: groesste Kante', max(hx1 - hx0, hz1 - hz0), BETT, '<=')
    p.info('Haube: Hoehe beim Druck', hy1 - hy0)
    vol = ((hx1 - hx0) * (hy1 - hy0) * (hz1 - hz0)
           - (ix1 - ix0) * (iy1 - iy0) * (iz1 - iz0)
           - sum((u1 - u0) * (v1 - v0) for u0, v0, u1, v1 in ls) * ht) / 1000.0
    p.info('Haube: Volumen voll', vol, 'cm3')
    p.info('Haube: Masse voll (PETG 1,27 g/cm3)', vol * 1.27, 'g')
    p.info('keine Ueberhaenge: Loecher und Schlitze senkrecht, Stehbolzen '
           'und Dome stehen auf der Platte, die Waende der Haube auf der '
           'Rueckwand')

    # ------------------------------------------------------------------
    p.titel('10) Stueckliste Pi-Halter')
    for zeile in (
            '1x Pi-Halter (PETG), 1x Haube (PETG)',
            '2x M5x{:.0f} Zylinderkopf + 2x Hammermutter M5 Nut 6 (Platte -> '
            'obere Nut der Rueckseite hinteres 2060)'.format(hw('m5_l')),
            '4x M2.5x{:.0f} Zylinderkopf (Pi -> Stehbolzen, schneidet sein '
            'Gewinde selbst)'.format(hw('m25_l')),
            '2x Kabelbinder {} (Wandler; 2,5 x 100 ist zu kurz)'.format(
                ec.BINDER),
            '3x M3x{:.0f} Zylinderkopf + 3x Messing-Einsatz M3 Ø5 (Haube -> '
            'Dome)'.format(hw('m3_l')),
            'Raspberry Pi Zero 2 W, microSD 16-32 GB',
            'Abwaertswandler 24 -> 5 V, >= 3 A, Eingang Schraubklemme, '
            'Ausgang USB-A, {:.0f} x {:.0f} mm, hoechstens {:.0f} mm hoch'
            .format(hw('wandler_l'), hw('wandler_b'), hw('wandler_h'))):
        p.info(zeile)

    # ------------------------------------------------------------------
    p.titel('11) Statische Pruefung der Schluessel in PiHalter.py')
    quelle = open(PIHALTER, encoding='utf-8').read()
    fehlt_m = sorted(set(re.findall(r"\bw\('([^']+)'\)", quelle))
                     - set(hm.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(HL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(hm.MASSE)
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('12) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in hm.hinweise_bauen(HL, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
