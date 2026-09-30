#!/usr/bin/env python3
"""Rechnerische Pruefung der Endschalter-Halter (fusion/Endschalter) — laeuft
ohne Fusion.

Importiert Endschalter.py, Portal.py und ToolheadZ.py mit gestubbtem
adsk-Modul und prueft: Abgleich der Bezugsmasse, Schaltpunkte, Blatt im
Gabelspalt, Freiraum gegen alles, was faehrt (Portal ueber den Y-Weg,
Toolhead ueber X- und Z-Weg), gegen Rahmen, Riemen, die Winkel an den
Kreuzungen und die Y-Motorhalter, Nuten und Schrauben, die Klammern und
den Druck. Gibt die Stueckliste und die GRBL-Werte aus.

    python3 tools/endschalter_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

ENDSCHALTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                           'fusion', 'Endschalter', 'Endschalter.py')
WINKEL = 20.0          # Winkel an den Kreuzungen 2040/2060 [v] Angabe
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
NUT_PLATZ = 6.0        # so weit darf eine Schraube in die Nut (YMotorhalter)
NUT_LIPPE, NUTSTEIN = 1.8, 4.0     # Hammermutter Nut 6 [w]
SCHEIBE_M5, SCHEIBE_M5_D = 1.0, 10.0   # DIN 125 unter dem Kopf (YMotorhalter)
RITZEL_R = 8.0         # Flansch des hinteren Y-Ritzels, Radius [w]
M3_KOPF_D, M3_KOPF_H = 5.5, 3.0
EINSATZ_M3 = (5.0, 5.7)            # Aussendurchmesser, Laenge [w]
EINSATZ_M2 = (3.2, 2.5)            # [v]
X_SCHRITTE, Z_SCHRITTE = 41, 9


def auf(q, dx=0.0, dy=0.0, dz=0.0, name=None):
    return Quader(name or q.name, q.x[0] + dx, q.x[1] + dx, q.y[0] + dy,
                  q.y[1] + dy, q.z[0] + dz, q.z[1] + dz, q.art)


def teile(ew, EL):
    """Die neuen Teile als Quader. Halter_Y und seine Lichtschranke stehen
    fest am Rahmen; Fahne_Y und Halter_X fahren mit dem Portal (relativ zum
    Portal in der Mitte); Klammer_X und Fahne_X mit dem Toolhead (X relativ
    zur Wagenmitte, Y relativ zum Portal)."""
    dy, xs = EL['dy'], EL['xs']
    fx, fz = EL['hy_fuss_x'], EL['hy_fuss_z']
    y = EL['hy_y']
    k = ew('m5_kopf_d') / 2.0
    hy = [Quader('Halter_Y Fuss', *fx, *y, *fz),
          Quader('Halter_Y Boden', *EL['hy_boden_x'], *y, *EL['hy_boden_z']),
          Quader('Halter_Y Fase', fx[1], fx[1] + ew('hy_fase'), *y,
                 EL['hy_boden_z'][0] - ew('hy_fase'), EL['hy_boden_z'][0]),
          Quader('LS_Y Platine', *EL['ly_pcb_x'], *EL['ly_pcb_y'],
                 *EL['ly_pcb_z'])]
    hy += [Quader('LS_Y Gabel {}'.format(i + 1), *a, *EL['ly_gabel_y'],
                  *EL['ly_gabel_z']) for i, a in enumerate(EL['ly_arme_x'])]
    hy += [Quader('Halter_Y M5-Kopf', fx[1], fx[1] + ew('m5_kopf_h'),
                  yy - k, yy + k, zz - k, zz + k) for yy, zz in EL['hy_m5']]

    fyr = EL['fy_y_rel']
    oz, uz = EL['fy_backe_o_z'], EL['fy_backe_u_z']
    fy = [Quader('Fahne_Y Wand', *EL['fy_wand_x'], *fyr, uz[0], oz[1]),
          Quader('Fahne_Y Backe oben', *EL['fy_backe_o_x'], *fyr, *oz),
          Quader('Fahne_Y Backe unten', *EL['fy_backe_u_x'], *fyr, *uz),
          Quader('Fahne_Y Blatt', *EL['fy_blatt_x'], *fyr,
                 *EL['fy_blatt_z']),
          Quader('Fahne_Y Madenschraube', EL['fy_einsatz_x'] - 1.5,
                 EL['fy_einsatz_x'] + 1.5, EL['fy_einsatz_y_rel'] - 1.5,
                 EL['fy_einsatz_y_rel'] + 1.5, oz[1], oz[1] + 2.0)]

    hyr = EL['hx_y_rel']
    zb = ew('hx_zunge_b') / 2.0
    hx = [Quader('Halter_X Block', *EL['hx_x'], *hyr, *EL['hx_z']),
          Quader('Halter_X Zunge', *EL['hx_zunge_x'],
                 hyr[0] - ew('hx_zunge_t'), hyr[0], -zb, zb),
          Quader('LS_X Platine', *EL['lx_pcb_x'], *EL['lx_pcb_y_rel'],
                 *EL['lx_pcb_z'])]
    hx += [Quader('LS_X Gabel {}'.format(i + 1), *EL['lx_gabel_x'],
                  *EL['lx_gabel_y_rel'], *a)
           for i, a in enumerate(EL['lx_arme_z'])]

    bx = EL['kx_backe_x']
    wx = EL['kx_wand_x']
    hz1 = EL['kx_backe_h_z'][1]
    ueber = EL['kx_steg_y0'] - EL['kx_backe_h_y'][0]
    ex, ez = EL['kx_einsatz_v']
    kx, ky = EL['kx_einsatz_kopf']
    kr = M3_KOPF_D / 2.0
    fxr = [Quader('Klammer_X Wand unten', *wx, EL['kx_backe_h_y'][0],
                  EL['kx_backe_v_y'][1], ew('kx_z0'), hz1),
           # 45-Grad-Uebergang als Huelle ueber die ganze Tiefe; die
           # Schraege selbst prueft Abschnitt 6 gegen den Wagen
           Quader('Klammer_X Uebergang', *wx, EL['kx_backe_h_y'][0],
                  EL['kx_backe_v_y'][1], hz1, hz1 + ueber),
           Quader('Klammer_X Wand oben', *wx, EL['kx_steg_y0'],
                  EL['kx_backe_v_y'][1], hz1 + ueber, EL['kx_steg_z1']),
           Quader('Klammer_X Backe hinten', *bx, *EL['kx_backe_h_y'],
                  *EL['kx_backe_h_z']),
           Quader('Klammer_X Backe vorn', *bx, *EL['kx_backe_v_y'],
                  *EL['kx_backe_v_z']),
           Quader('Klammer_X Kopf', *EL['kx_kopf_x'], *EL['fx_y_rel'],
                  EL['kx_kopf_fase_z'], EL['kx_kopf_z'][1]),
           Quader('Klammer_X Madenschraube', ex - 1.5, ex + 1.5,
                  EL['kx_backe_v_y'][1], EL['kx_backe_v_y'][1] + 2.0,
                  ez - 1.5, ez + 1.5),
           Quader('Fahne_X Blatt', *EL['fx_x_rel'], *EL['fx_y_rel'],
                  *EL['fx_z']),
           Quader('Fahne_X Schraubenkopf', kx - kr, kx + kr, ky - kr, ky + kr,
                  EL['fx_z'][1], EL['fx_z'][1] + M3_KOPF_H)]
    return {'halter_y': hy, 'fahne_y': fy, 'halter_x': hx, 'fahne_x': fxr,
            'dy': dy, 'xs': xs}


def engste(a_liste, b_liste, ohne=()):
    best = (float('inf'), None, None)
    for a in a_liste:
        for b in b_liste:
            if (a.name, b.name) in ohne or (b.name, a.name) in ohne:
                continue
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    em = bauraum.modul_laden(ENDSCHALTER, 'endschalter')
    ew, EL = em.w, em.lage()
    p = Pruefung()
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, _, _ = portal_check.y_weg(w, L, TL, feste, bewegte)
    portal_alle, _ = bauraum.portal_bauraeume(w, L)
    P = {q.name: q for q in portal_alle}
    lang = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    rahmen = [q for q in portal_alle if q.name.startswith(lang)]
    portal = [q for q in portal_alle if not q.name.startswith(lang)]
    T = teile(ew, EL)
    R = EL['R']

    # ------------------------------------------------------------------
    p.titel('1) Abgleich Endschalter.py <-> Portal.py / ToolheadZ.py')
    TH = {q.name: q for q in feste}
    abgleich = [
        ('Y-Schienen Mitte (R)', R, L['R']),
        ('Rahmen: hintere Stirnseite der 2040', ew('rahmen_y0'),
         L['rahmen_y'][0]),
        ('Rahmen: Unterkante der 2040', ew('rahmen_z0'), L['rahmen_z0']),
        ('Rahmen: Oberkante der 2040', EL['rahmen_z1'], L['rahmen_z1']),
        ('hinteres 2060: Rueckseite', ew('quer_y1'), L['quer_y_hinten'][0]),
        ('Y-Schiene: hinteres Ende', ew('y_schiene_y0'), L['y_schiene_y'][0]),
        ('Y-Weg bis ans Schienenende', ew('y_weg_hinten'), d_schiene),
        ('Schlittenplatte rechts: Aussenkante', EL['platte_x1'],
         P['Platte rechts'].x[1]),
        ('Schlittenplatte: Hinterkante', ew('platte_y0'),
         P['Platte rechts'].y[0]),
        ('Schlittenplatte: Vorderkante', ew('platte_y1'),
         P['Platte rechts'].y[1]),
        ('Schlittenplatte: Unterseite', EL['platte_z'][0],
         P['Platte rechts'].z[0]),
        ('Schlittenplatte: Oberseite', EL['platte_z'][1],
         P['Platte rechts'].z[1]),
        ('Y-Wagen rechts: Aussenseite', EL['y_wagen_x1'],
         P['Y-Wagen rechts'].x[1]),
        ('Y-Wagen: Hinterkante', ew('y_wagen_y0'), P['Y-Wagen rechts'].y[0]),
        ('Y-Wagen: Vorderkante', ew('y_wagen_y1'), P['Y-Wagen rechts'].y[1]),
        ('Y-Wagen: Unterkante', ew('y_wagen_z0'), P['Y-Wagen rechts'].z[0]),
        ('Wagenschrauben hinten (Y)', ew('wagen_loch_y'),
         min(y for _, y in L['wagen_loecher'])),
        ('Wagenschrauben vorn (Y)', ew('wagen_loch_y2'),
         max(y for _, y in L['wagen_loecher'])),
        ('Portalrohr: linkes Ende', ew('rohr_x0'), P['Portalrohr'].x[0]),
        ('Portalrohr: Rueckseite', ew('rohr_y0'), P['Portalrohr'].y[0]),
        ('Portalrohr: Vorderseite', ew('rohr_y1'), P['Portalrohr'].y[1]),
        ('X-Schiene: linkes Ende', ew('x_schiene_x0'), P['X-Schiene'].x[0]),
        ('X-Schiene: Breite', ew('x_schiene_b'),
         P['X-Schiene'].z[1] - P['X-Schiene'].z[0]),
        ('X-Schiene: Hoehe', ew('x_schiene_h'),
         P['X-Schiene'].y[1] - P['X-Schiene'].y[0]),
        ('X-Wagenmitte am linken Schienenende', ew('xw_min'), L['xw_min']),
        ('Stirnblock links: Aussenkante', ew('stirn_x0'),
         P['Stirnblock links'].x[0]),
        ('Stirnblock links: Hinterkante', ew('stirn_y0'),
         P['Stirnblock links'].y[0]),
        ('Stirnblock links: Vorderkante', ew('stirn_y1'),
         P['Stirnblock links'].y[1]),
        ('Traegerplatte: linke Kante', ew('traeger_x_links'),
         tw('traeger_x_links')),
        ('Traegerplatte: Dicke', ew('traeger_dicke'),
         TH['Traegerplatte Hauptsaeule'].y[1]
         - TH['Traegerplatte Hauptsaeule'].y[0]),
        ('Traegerplatte: Unterkante', ew('traeger_z0'),
         TH['Traegerplatte Hauptsaeule'].z[0]),
        ('Saeulenrippe links: Breite', ew('rippe_b'),
         TH['Saeulenrippe links'].x[1] - TH['Saeulenrippe links'].x[0]),
        ('Saeulenrippe links: Tiefe', ew('rippe_t'),
         TH['Saeulenrippe links'].y[1] - TH['Saeulenrippe links'].y[0]),
        ('X-Wagen: Laenge', ew('x_wagen_laenge'),
         TH['X-Wagen MGN15H'].x[1] - TH['X-Wagen MGN15H'].x[0]),
        ('X-Wagen: Breite', ew('x_wagen_breite'),
         TH['X-Wagen MGN15H'].z[1] - TH['X-Wagen MGN15H'].z[0]),
    ]
    for name in ('ls_pcb_laenge', 'ls_pcb_breite', 'ls_pcb_dicke',
                 'ls_pcb_rand', 'ls_schlitz', 'ls_gabel_rand',
                 'ls_gabel_dicke', 'ls_gabel_hoehe', 'ls_gabel_breite',
                 'ls_strahl_hoehe', 'ls_schlitz_boden', 'ls_pcb_loch_d',
                 'ls_pcb_loch_t', 'ls_pcb_frei_d'):
        abgleich.append(('Lichtschranke {} (ToolheadZ)'.format(name),
                         ew(name), tw(name)))
    for text, ist, soll in abgleich:
        p.ok(text, abs(ist - soll), 0.02, '<=')

    # ------------------------------------------------------------------
    p.titel('2) Y: Schaltpunkt und Blatt im Gabelspalt')
    dy_s = EL['ly_strahl_y'] - EL['fy_y_rel'][0]
    p.info('Portal beim Schalten (ab Mitte)', dy_s)
    p.ok('schaltet vor dem hinteren Schienenende', d_schiene + dy_s,
         ew('schaltabstand') - 0.01)
    wagen_ende = ew('y_wagen_y0') - d_schiene
    p.ok('Y-Wagen am Schienenende buendig (Schiene hinten)',
         abs(wagen_ende - ew('y_schiene_y0')), 0.05, '<=')
    s = ew('ls_schlitz') / 2.0
    bl = EL['fy_blatt_x']
    p.ok('Blatt im Spalt: Luft zum inneren Arm', bl[0] - (EL['gy_x'] - s),
         2.0)
    p.ok('Blatt im Spalt: Luft zum aeusseren Arm', (EL['gy_x'] + s) - bl[1],
         2.0)
    bz = EL['fy_blatt_z']
    p.ok('Blatt ueber dem Schlitzboden [?]', bz[0] - EL['ly_boden_z'], 1.0)
    p.ok('Blatt deckt den Strahl ab', EL['ly_strahl_z'] - bz[0], 1.0)
    p.ok('Blatt reicht ueber die offene Seite der Gabel',
         bz[1] - EL['ly_gabel_z'][1], 2.0)
    vorne = EL['fy_y_rel'][0] - d_schiene
    p.ok('am Schienenende: Blatt kommt nicht hinter die Gabel',
         vorne - EL['ly_gabel_y'][0], 0.0)
    p.info('Halter Y: Abstand zum hinteren 2060',
           EL['quer_y'][0] - EL['hy_y'][1])
    # hinteres Ritzel hinter der Stirnseite der 2040, Lage wie Portal.py [?]
    ritzel = L['yh_y'] + RITZEL_R
    p.ok('Halter Y: vor dem Flansch des hinteren Ritzels (Lage [?])',
         EL['hy_y'][0] - ritzel, 15.0)
    p.ok('Halter Y: vor dem Profilende (Lagerbock der Umlenkung [?])',
         EL['hy_y'][0] - ew('rahmen_y0'), 40.0)

    # ------------------------------------------------------------------
    p.titel('3) Y: Freiraum ueber den ganzen Y-Weg')
    fest_y = T['halter_y']
    dys = [-d_schiene + (d_schiene + d_vorn) * i / 200.0 for i in range(201)]
    fahne_y = T['fahne_y']
    ohne_blatt = [q for q in fahne_y if 'Blatt' not in q.name]
    best = (float('inf'),)
    for dy in dys:
        bew = [auf(q, dy=dy) for q in portal + ohne_blatt]
        d = engste(fest_y, bew)
        if d[0] < best[0]:
            best = d + (dy,)
    p.ok('Halter + Lichtschranke <-> Portal und Klammer ({} / {}, '
         'dy {:+.1f})'.format(best[1], best[2], best[3]), best[0],
         ew('luft_bau') - 0.01)
    best = (float('inf'),)
    blatt = [q for q in fahne_y if 'Blatt' in q.name]
    for dy in dys:
        d = engste([auf(q, dy=dy) for q in blatt],
                   [q for q in fest_y if 'Gabel' not in q.name])
        if d[0] < best[0]:
            best = d + (dy,)
    p.ok('Blatt <-> Halter und Platine ({}, dy {:+.1f})'.format(
        best[2], best[3]), best[0], ew('luft_bau') - 0.01)
    # Rahmen: 2040, Schienen, Riemen, beide 2060, Winkel an den Kreuzungen,
    # Y-Motorhalter vorn; der Ruecklauf laeuft in der AEUSSEREN oberen Nut
    # (hardware-notizen.md) — Portal.py rechnet ihn noch innen.
    quer = portal_check.quer_quader(w, L)
    winkel = []
    for q in quer:
        for s_ in (-1, 1):
            for innen in (False, True):
                xa = s_ * (R + (-1 if innen else 1) * 10.0)
                xb = xa + s_ * (-WINKEL if innen else WINKEL)
                winkel.append(Quader('Winkel {} {}{}'.format(
                    q.name.split()[-1], 'rechts' if s_ > 0 else 'links',
                    ' innen' if innen else ''), min(xa, xb), max(xa, xb),
                    q.y[0], q.y[1], L['rahmen_z0'],
                    L['rahmen_z0'] + WINKEL))
    ruecklauf = []
    for s_ in (-1, 1):
        xr = s_ * (R + 10.0 - 3.6)
        ruecklauf.append(Quader('Y-Ruecklauf aussen {}'.format(
            'rechts' if s_ > 0 else 'links'), xr - 0.7, xr + 0.7,
            L['yh_y'], 400.0, EL['nut_o_z'] - 3.0,
            EL['nut_o_z'] + 3.0))
    gegen = rahmen + quer + winkel + ruecklauf + \
        portal_check.y_halter_quader(w, L)
    best = (float('inf'),)
    for dy in dys:
        d = engste([auf(q, dy=dy) for q in fahne_y], gegen)
        if d[0] < best[0]:
            best = d + (dy,)
    p.ok('Fahne Y <-> Rahmen, Riemen, 2060, Winkel {:.0f} mm ({}, dy '
         '{:+.1f})'.format(WINKEL, best[2], best[3]), best[0],
         ew('luft_bau') - 0.01)
    # der Fuss liegt am 2040 an; den Ruecklauf in der Nut prueft die
    # naechste Zeile (er laeuft dort, egal was aussen an der Flaeche liegt)
    d = engste(fest_y, [q for q in gegen if q.name != 'Rahmen 2040 rechts'
                        and not q.name.startswith('Y-Ruecklauf aussen')])
    p.ok('Halter Y <-> Riemen, 2060, Winkel ({})'.format(d[2]), d[0],
         ew('luft_bau') - 0.01)
    p.ok('Fuss bleibt vor der oberen Nut (Ruecklauf des Riemens)',
         engste(fest_y, ruecklauf)[0], 2.0)

    # ------------------------------------------------------------------
    p.titel('4) Y: Nut, Schrauben, Einsaetze')
    p.ok('M5 in der unteren Nut', abs(EL['hy_m5'][0][1] - EL['nut_u_z']),
         0.01, '<=')
    p.ok('obere Nut frei: Fuss endet ueber keiner Schraube dort',
         EL['nut_o_z'] - EL['hy_m5'][0][1], 15.0)
    # mit Scheibe wie am YMotorhalter; ohne stuende die Spitze genau am
    # Nutgrund
    in_nut = EL['hy_m5_schraube'] - SCHEIBE_M5 - ew('hy_fuss_dicke')
    p.ok('M5x{:.0f} + Scheibe: Spitze vor dem Nutgrund'.format(
        EL['hy_m5_schraube']), NUT_PLATZ - in_nut, 0.5)
    p.ok('   Gewinde im Nutstein',
         min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
    p.ok('zwei Hammermuttern haben Platz nebeneinander',
         EL['hy_m5'][1][0] - EL['hy_m5'][0][0], 11.0)
    k = SCHEIBE_M5_D / 2.0
    p.ok('M5-Scheibe unter dem Boden (Platz fuer Kopf und Inbus)',
         EL['hy_boden_z'][0] - ew('hy_fase') - (EL['hy_m5'][0][1] + k), 3.0)
    p.ok('M5-Scheibe liegt ganz auf dem Fuss (laengs)', min(
        EL['hy_m5'][0][0] - k - EL['hy_y'][0],
        EL['hy_y'][1] - (EL['hy_m5'][1][0] + k)), 0.5)
    p.ok('M5-Scheibe liegt ganz auf dem Fuss (unten)',
         EL['hy_m5'][0][1] - k - EL['hy_fuss_z'][0], 0.5)
    rm = EINSATZ_M2[0] / 2.0
    wand = min(min(x - rm - EL['hy_boden_x'][0],
                   EL['hy_boden_x'][1] - x - rm, y - rm - EL['hy_y'][0])
               for x, y in EL['ly_loecher'])
    p.ok('M2-Einsaetze: Wand im Boden', wand, 1.5)
    p.ok('   Boden dicker als Einsatz + Freibohrung',
         ew('hy_boden'), EINSATZ_M2[1] + 1.0)

    # ------------------------------------------------------------------
    p.titel('5) X: Schaltpunkt und Blatt im Gabelspalt')
    xs = EL['lx_strahl_x'] - EL['fx_spitze_rel']
    p.info('X-Wagenmitte beim Schalten', xs)
    p.ok('schaltet vor dem linken Schienenende', xs - ew('xw_min'),
         ew('schaltabstand') - 0.01)
    for n, v in (('Langloch ganz nach rechts', +ew('fx_verstellung')),
                 ('Langloch ganz nach links', -ew('fx_verstellung'))):
        p.ok('   {}: schaltet vor dem Schienenende'.format(n),
             xs + v - ew('xw_min'), 1.0)
    fz = EL['fx_z']
    p.ok('Blatt im Spalt: Luft nach unten', fz[0] - EL['lx_arme_z'][0][1],
         2.0)
    p.ok('Blatt im Spalt: Luft nach oben', EL['lx_arme_z'][1][0] - fz[1],
         2.0)
    fy_ = EL['fx_y_rel']
    p.ok('Blatt ueber dem Schlitzboden [?]', fy_[0] - EL['lx_boden_y_rel'],
         1.0)
    p.ok('Blatt deckt den Strahl ab', EL['lx_strahl_y_rel'] - fy_[0], 1.0)
    p.ok('Blatt reicht ueber die offene Seite der Gabel',
         fy_[1] - EL['lx_gabel_y_rel'][1], 2.0)
    spitze = EL['fx_spitze_rel'] + ew('xw_min')
    p.ok('am Schienenende: Spitze bleibt in der Gabel',
         spitze - EL['lx_gabel_x'][0], -0.01)
    p.ok('Anschlag: Block stoesst an das Ende der X-Schiene',
         abs(EL['hx_x'][1] - ew('x_schiene_x0')), 0.01, '<=')
    # Rohrnut (2020) wie in Portal.py: Engstelle + Kammer bis zum Grund;
    # der Kopf sitzt ohne Scheibe in der Senkung
    unter_kopf = ew('hx_dicke') - ew('m5_senk_t')
    in_nut = EL['hx_m5_schraube'] - unter_kopf
    p.ok('M5x{:.0f} (Kopf versenkt): Spitze vor dem Grund der Rohrnut'
         .format(EL['hx_m5_schraube']),
         ew('nut_t') + ew('nut_kammer_t') - in_nut, 0.5)
    p.ok('   Gewinde im Nutstein',
         min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
    p.ok('   Kopf ganz in der Senkung (die Platine liegt davor)',
         ew('m5_senk_t') - ew('m5_kopf_h'), 0.1)

    # ------------------------------------------------------------------
    p.titel('6) X: Freiraum ueber X- und Z-Weg')
    halter_x = T['halter_x']
    beruehrt = {('Halter_X Block', 'Portalrohr'),
                ('Halter_X Zunge', 'Portalrohr'),
                ('Halter_X Block', 'X-Schiene')}
    # fest am Portal: darf anliegen (Rohr, Schienenende), nur nicht
    # eindringen; die Zunge steckt in der Nut vor dem ersten Nutstein der
    # Schiene (15 mm hinter ihrem Ende)
    d = engste(halter_x, portal, ohne=beruehrt)
    p.ok('Halter X <-> Portal, fest ({} / {})'.format(d[1], d[2]), d[0],
         0.0)
    p.ok('Zunge endet vor dem ersten Nutstein der X-Schiene',
         ew('x_schiene_x0') + 15.0 - 5.0 - EL['hx_zunge_x'][1], 3.0)
    lang_y = [Quader(q.name, *q.x, -2000.0, 2000.0, *q.z, q.art)
              for q in rahmen]
    d = engste(halter_x, lang_y)
    p.ok('Halter X <-> Rahmen, Y-Schienen, Y-Riemen ({})'.format(d[2]),
         d[0], ew('luft_bau') - 0.01)
    rh0, rh1 = tw('traeger_x_links'), tw('traeger_x_rechts')
    xws = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)] + [xs]
    zcs = [TL['zc_min'] + (TL['zc_max'] - TL['zc_min']) * j
           / (Z_SCHRITTE - 1.0) for j in range(Z_SCHRITTE)]
    fahne_x = T['fahne_x']
    best_betrieb, best_ende = (float('inf'),), (float('inf'),)
    for xw in xws:
        trume = bauraum.x_riemen_trume(L, xw, rh0, rh1)
        fx_th = [q.verschoben(0.0, xw) for q in feste + fahne_x]
        for zc in zcs:
            th_ = fx_th + [q.verschoben(zc, xw) for q in bewegte]
            d = engste(halter_x, th_ + trume)
            if xw >= xs - 1e-6 and d[0] < best_betrieb[0]:
                best_betrieb = d + (xw, zc)
            if d[0] < best_ende[0]:
                best_ende = d + (xw, zc)
    p.ok('Halter X <-> Toolhead, Fahne, Riemen ab dem Schaltpunkt '
         '({} / {})'.format(best_betrieb[1], best_betrieb[2]),
         best_betrieb[0], ew('luft_bau') - 0.01)
    p.ok('   bis ans Schienenende: nichts dringt ein ({} / {}, X {:+.1f})'
         .format(best_ende[1], best_ende[2], best_ende[3]), best_ende[0],
         0.0)
    ls_x = [q for q in halter_x if q.name.startswith('LS_X')]
    d = engste(ls_x, [q.verschoben(0.0, L['xw_min']) for q in feste])
    p.ok('   am Schienenende: Platine und Gabel vor dem Wagen ({})'.format(
        d[1]), d[0], ew('luft_bau') - 0.01)
    kopf = EL['kx_kopf_x'][0] + ew('xw_min')
    p.ok('   am Schienenende: Kopf der Klammer bleibt vor der Gabel',
         kopf - EL['lx_gabel_x'][1], 1.0)
    best = (float('inf'),)
    for xw in xws:
        trume = bauraum.x_riemen_trume(L, xw, rh0, rh1)
        d = engste([q.verschoben(0.0, xw) for q in fahne_x],
                   portal + lang_y + trume)
        if d[0] < best[0]:
            best = d + (xw,)
    p.ok('Klammer + Fahne X <-> Portal, Rahmen, Riemen ({} / {}, X '
         '{:+.1f})'.format(best[1], best[2], best[3]), best[0],
         ew('luft_bau') - 0.01)
    geklemmt = {'Traegerplatte Hauptsaeule', 'Saeulenrippe links'}
    d = engste(fahne_x, [q for q in feste if q.name not in geklemmt])
    p.ok('Klammer + Fahne X <-> Toolhead ({} / {})'.format(d[1], d[2]),
         d[0], ew('luft_bau') - 0.01)
    best = (float('inf'),)
    for zc in zcs:
        d = engste(fahne_x, [q.verschoben(zc) for q in bewegte])
        if d[0] < best[0]:
            best = d + (zc,)
    p.ok('Klammer + Fahne X <-> Z-Schlitten ueber den Z-Weg ({} / {})'
         .format(best[1], best[2]), best[0], ew('luft_bau') - 0.01)
    # Schraege zwischen hinterer Backe und Wand oben: Abstand der 45-Grad-
    # Linie zur unteren vorderen Kante des X-Wagens (Y 0, Z -16)
    y0, z0 = EL['kx_backe_h_y'][0], EL['kx_backe_h_z'][1]
    wz = -ew('x_wagen_breite') / 2.0
    d_schraege = abs((0.0 - y0) - (wz - z0)) / 2.0 ** 0.5
    p.ok('Schraege der Klammer <-> Unterkante X-Wagen', d_schraege,
         ew('luft_bau') - 0.01)

    # ------------------------------------------------------------------
    p.titel('7) Klammern')
    p.ok('Fahne Y: Maul ueber der Platte (Spiel)',
         EL['fy_innen_z'][1] - EL['fy_innen_z'][0] - ew('platte_dicke'),
         0.2)
    p.ok('Fahne Y: untere Backe neben dem Y-Wagen',
         EL['fy_backe_u_x'][0] - EL['y_wagen_x1'], 0.5)
    senk = ew('m3_senkung_d') / 2.0
    p.ok('Fahne Y: Klammer zwischen den Wagenschrauben', min(
        EL['fy_y_rel'][0] - (ew('wagen_loch_y') + senk),
        (ew('wagen_loch_y2') - senk) - EL['fy_y_rel'][1]), 0.5)
    p.ok('Fahne Y: Madenschraube drueckt auf die Platte (nicht daneben)',
         EL['platte_x1'] - EL['fy_einsatz_x'] - 1.5, 1.0)
    p.ok('Fahne Y: Wand um den Einsatz', min(
        EL['fy_einsatz_x'] - EINSATZ_M3[0] / 2.0 - EL['fy_backe_o_x'][0],
        EL['fy_einsatz_y_rel'] - EINSATZ_M3[0] / 2.0 - EL['fy_y_rel'][0]),
        2.0)
    p.ok('Fahne Y: Backe dicker als der Einsatz', ew('fy_backe_o'),
         EINSATZ_M3[1])
    xt = ew('traeger_x_links')
    p.ok('Klammer X: Maul ueber Platte + Rippe (Spiel)',
         EL['kx_innen_y'][1] - EL['kx_innen_y'][0]
         - ew('traeger_dicke') - ew('rippe_t'), 0.2)
    ex, ez = EL['kx_einsatz_v']
    p.ok('Klammer X: Madenschraube trifft die Rippe', min(
        ex - 1.5 - xt, xt + ew('rippe_b') - (ex + 1.5)), 0.0)
    p.ok('Klammer X: Wand um den vorderen Einsatz', min(
        ex - EINSATZ_M3[0] / 2.0 - EL['kx_backe_x'][0],
        EL['kx_backe_x'][1] - ex - EINSATZ_M3[0] / 2.0,
        ez - EINSATZ_M3[0] / 2.0 - ew('kx_z0'),
        ew('kx_z1') - ez - EINSATZ_M3[0] / 2.0), 2.0)
    kx, ky = EL['kx_einsatz_kopf']
    p.ok('Klammer X: Wand um den Einsatz im Kopf', min(
        kx - EINSATZ_M3[0] / 2.0 - EL['kx_kopf_x'][0],
        EL['kx_kopf_x'][1] - kx - EINSATZ_M3[0] / 2.0,
        ky - EINSATZ_M3[0] / 2.0 - EL['fx_y_rel'][0],
        EL['fx_y_rel'][1] - ky - EINSATZ_M3[0] / 2.0), 2.0)
    p.ok('Klammer X: Kopf dicker als der Einsatz', ew('kx_kopf_h'),
         EINSATZ_M3[1])
    p.ok('Fahne X: M3x{:.0f} greift im Einsatz'.format(EL['fx_schraube']),
         EL['fx_schraube'] - ew('fahne_dicke'), 4.0)
    p.ok('   ... und bleibt im Kopf', ew('kx_kopf_h') + ew('fahne_dicke')
         - EL['fx_schraube'], 0.5)
    p.ok('Kopf-Fase 45 Grad (druckt ohne Stuetzen)', abs(
        (EL['kx_kopf_z'][0] - EL['kx_kopf_fase_z'])
        - (EL['kx_wand_x'][0] - EL['kx_kopf_x'][0])), 0.01, '<=')
    p.info('Fahne X: freies Blatt vor dem Kopf',
           EL['kx_kopf_x'][0] - EL['fx_spitze_rel'])

    # ------------------------------------------------------------------
    p.titel('8) Druck (Bambu Lab A1)')
    ausdehnung = {
        'Halter_Y': (EL['hy_boden_x'][1] - EL['hy_fuss_x'][0],
                     EL['hy_y'][1] - EL['hy_y'][0],
                     EL['hy_boden_z'][1] - EL['hy_fuss_z'][0]),
        'Fahne_Y': (EL['fy_wand_x'][1] - EL['fy_backe_o_x'][0],
                    ew('fy_laenge'),
                    EL['fy_backe_o_z'][1] - EL['fy_blatt_z'][0]),
        'Halter_X': (EL['hx_x'][1] - EL['hx_x'][0],
                     ew('hx_dicke') + ew('hx_zunge_t'), ew('hx_h')),
        'Klammer_X': (EL['kx_backe_x'][1] - EL['kx_kopf_x'][0],
                      EL['kx_backe_v_y'][1] - EL['kx_backe_h_y'][0],
                      EL['kx_kopf_z'][1] - ew('kx_z0')),
        'Fahne_X': (EL['fx_x_rel'][1] - EL['fx_x_rel'][0],
                    EL['fx_y_rel'][1] - EL['fx_y_rel'][0],
                    ew('fahne_dicke'))}
    for n, a in ausdehnung.items():
        p.ok('{}: {:.1f} x {:.1f} x {:.1f} mm passt aufs Bett'.format(n, *a),
             max(a), BETT, '<=')
    p.info('Fahnen und Klammern SCHWARZ: helles PETG laesst IR durch')

    # ------------------------------------------------------------------
    p.titel('9) Statische Pruefung der Schluessel in Endschalter.py')
    quelle = open(ENDSCHALTER, encoding='utf-8').read()
    fehlt_m = sorted(set(re.findall(r"\bw\('([^']+)'\)", quelle))
                     - set(em.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(EL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(em.MASSE)
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('10) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in em.hinweise_bauen(EL, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    # ------------------------------------------------------------------
    p.titel('11) Stueckliste und GRBL')
    for zeile in (
            'Druck (PETG): Halter_Y, Halter_X; SCHWARZ: Fahne_Y, Klammer_X, '
            'Fahne_X',
            '2 Gabellichtschranken LM393 (vorhanden), je 2 x M2x6 in '
            'Einsaetze M2 3,2 x 2,5 (vorhanden)',
            'Y: 2 x M5x{:.0f} + 2 Scheiben M5 + 2 Hammermuttern M5 (Nut 6), '
            'untere Aussennut'.format(EL['hy_m5_schraube']),
            'X: 1 x M5x{:.0f} + 1 Hammermutter M5, vordere Rohrnut'.format(
                EL['hx_m5_schraube']),
            'Klammern: 2 x Madenschraube M3x8, 3 x Einsatz M3; Fahne X: '
            '1 x M3x{:.0f}'.format(EL['fx_schraube'])):
        p.info(zeile)
    # Reserve: sonst stuende der Wagen am anderen Ende genau buendig mit
    # dem Schienenende
    x_weg = L['xw_max'] - xs - 1.0 - 2.0
    y_weg = d_vorn + d_schiene - ew('schaltabstand') - 1.0 - 2.0
    p.info('$130 (X: ab Schaltpunkt, 1 mm Rueckzug, 2 mm Reserve)', x_weg)
    p.info('$131 (Y: ab Schaltpunkt, 1 mm Rueckzug, 2 mm Reserve)', y_weg)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
