#!/usr/bin/env python3
"""Zeichnung: Platz fuer die Elektronik — Vorschlag.

Draufsicht auf die ganze Maschine und Seitenansicht von links: das
Elektronikfach hinter dem hinteren 2060 mit Steuerung und Netzteil, die
Endschalter, die festen Kabelwege und die beiden Energieketten. Rahmen,
Portal und Toolhead kommen aus Portal.py und ToolheadZ.py, das Fach und der
Y-Weg aus tools/portal_check.py (Abschnitte 14 und 16). Steuerung, Netzteil
und Ketten sind Platzhalter — ihre Masse stehen noch aus.

    python3 tools/elektronik_zeichnen.py   ->  docs/elektronik-platz.svg

Gibt ausserdem die Kabellaengen aus.
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from antrieb_zeichnen import (el, f1, text, linie, rect_px,  # noqa: E402
                              de, TEXT, GRAU, BLAU, ROT, FARBE)
from portal_zeichnen import Feld, ORANGE              # noqa: E402
from y_antrieb_zeichnen import quer_mass              # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-platz.svg')

# ---- Vorschlag: Platzhalter, die Kaufteile sind noch nicht festgelegt ----
STEUERUNG = (95.0, 80.0, 55.0)   # Gehaeuse Uno + CNC Shield V3: X, Y, Z
NETZTEIL = (159.0, 97.0, 30.0)   # Beispiel Mean Well LRS-150-24 [w]
NETZBUCHSE = (50.0, 30.0)        # Kaltgeraetebuchse mit Schalter, Sicherung
KETTE_B, KETTE_H, KETTE_R = 18.0, 15.0, 18.0   # Kette aussen, Biegeradius
KETTE_ENDEN = 40.0               # beide Anschlussglieder zusammen
RESERVE = 0.15                   # Kabel: Boegen, Zugentlastung, Stecker
KAUFLAENGEN = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)   # m

KABEL = '#6d3fb5'
FARBE.update({'kette': ('#a3abb8', '#3d4552')})


def konzept(w, L, tw, TL):
    """Lage aller Teile im Vorschlag, Rahmenkoordinaten wie
    portal_check.py Abschnitt 14 (Portal in der Mitte seines Wegs)."""
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, d_hinten, _ = portal_check.y_weg(w, L, TL, feste,
                                                        bewegte)
    portal = {q.name: q for q in bauraum.portal_bauraeume(w, L)[0]}
    R = L['R']
    K = {'feste': feste, 'bewegte': bewegte, 'portal': portal,
         'd_schiene': d_schiene, 'd_vorn': d_vorn, 'd_hinten': d_hinten}
    fach = portal_check.elektronikfach(w, L)
    K['fach'] = fach
    K['y_tr'] = TL['traeger_y0'] - d_schiene - w('luft_bau')

    sb, st, sh = STEUERUNG
    x0 = fach.x[0] + 20.0
    K['steuerung'] = Quader('Steuerung', x0, x0 + sb, fach.y[1] - st,
                            fach.y[1], fach.z[0], fach.z[0] + sh)
    nb, nt, nh = NETZTEIL
    K['netzteil'] = Quader('Netzteil', -30.0, -30.0 + nb, fach.y[1] - nt,
                           fach.y[1], fach.z[0] + 3.0, fach.z[0] + 3.0 + nh)
    bb, bt = NETZBUCHSE
    K['netzbuchse'] = Quader('Netzbuchse', 165.0, 165.0 + bb, fach.y[0],
                             fach.y[0] + bt, fach.z[0], fach.z[0] + 30.0)

    # Aussenseiten der 2040 und ihre untere Nut
    K['x_aussen'] = R + w('rahmen_b') / 2.0 + 5.0
    K['z_nut_u'] = L['rahmen_z0'] + w('rahmen_b') / 2.0

    # Y-Kette: aussen am linken 2040, ausserhalb des Schlittens (der steht
    # bis X = -279 ueber). Festpunkt auf halbem Weg, Schleife nach hinten;
    # die Wanne haengt in der unteren Nut aussen am 2040.
    stirn = portal['Stirnblock links']
    xk1 = stirn.x[0] - 3.0
    K['ky_x'] = (xk1 - KETTE_B, xk1)
    ym = (stirn.y[0] + stirn.y[1]) / 2.0        # bewegtes Ende, Portal Mitte
    K['ky_ende0'] = ym
    K['ky_bewegt'] = (ym - d_hinten, ym + d_vorn)
    K['ky_hub'] = d_hinten + d_vorn
    K['ky_fest'] = ym + (d_vorn - d_hinten) / 2.0
    K['ky_wanne'] = (K['ky_bewegt'][0] - KETTE_R - KETTE_H / 2.0,
                     K['ky_fest'])
    K['ky_z_wanne'] = L['quer_z'][1]            # Unterkante wie die 2040
    K['ky_z_unten'] = K['ky_z_wanne'] + 3.0 + KETTE_H / 2.0
    K['ky_z_oben'] = K['ky_z_unten'] + 2.0 * KETTE_R
    K['ky_laenge'] = K['ky_hub'] / 2.0 + math.pi * KETTE_R + KETTE_ENDEN

    # X-Kette: ueber dem Portalrohr hinter dem X-Riemen, Festpunkt in der
    # Mitte des X-Wegs, Schleife nach rechts (links stuende der X-Motor im
    # Weg). Bewegtes Ende hinten an der Traegerplatte.
    K['kx_y'] = (L['portal_y'] - 20.0 - 12.0, L['portal_y'] - 20.0 + 6.0)
    K['kx_hub'] = L['xw_max'] - L['xw_min']
    K['kx_fest'] = (L['xw_min'] + L['xw_max']) / 2.0
    K['kx_wanne'] = (K['kx_fest'], L['xw_max'] + KETTE_R + KETTE_H / 2.0)
    K['kx_z_wanne'] = 33.0
    K['kx_z_unten'] = K['kx_z_wanne'] + 3.0 + KETTE_H / 2.0
    K['kx_z_oben'] = K['kx_z_unten'] + 2.0 * KETTE_R
    K['kx_laenge'] = K['kx_hub'] / 2.0 + math.pi * KETTE_R + KETTE_ENDEN

    # Endschalter (Gabellichtschranken LM393)
    platte = portal['Platte links']
    K['es_y'] = (-(R + w('rahmen_b') / 2.0 + 8.0), platte.y[0] - d_hinten)
    motor = portal['X-Motor']
    K['es_x'] = (motor.x[1] + 3.0, motor.y[1] + 6.0)
    xm = K['kx_fest']
    K['es_z'] = (xm - 27.0, 32.0)
    K['xm'] = xm
    K['kabel'] = kabelwege(w, L, TL, K)
    return K


def laenge(punkte):
    return sum(math.dist(a, b) for a, b in zip(punkte, punkte[1:]))


def kabelwege(w, L, TL, K):
    """Kabelwege als 3D-Streckenzuege (Portal in der Mitte). Die Ketten
    zaehlen mit ihrer Laenge. Liefert {Name: (Laenge mm, Streckenzug
    in XY fuer die Draufsicht)}."""
    R, st = L['R'], K['steuerung']
    xa, zn = K['x_aussen'], K['z_nut_u']
    yc = (st.y[0] + st.y[1]) / 2.0
    z_boden = K['fach'].z[0] + 25.0
    raus = [(st.x[0], yc, z_boden), (-xa, yc, z_boden), (-xa, yc, zn)]
    zm = (L['ym_motor_z0'] + L['ymp_z0']) / 2.0
    fl = w('motor_flansch') / 2.0

    def y_motor(s):
        return [(s * xa, L['ym_y'] - fl, zn),
                (s * (R - L['ym_u']), L['ym_y'], zm)]

    xst = (st.x[0] + st.x[1]) / 2.0
    y_2060 = L['quer_y_hinten'][0] - 1.0
    z_2060 = L['quer_z'][0] + 30.0
    rechts = [(xst, st.y[1], z_boden), (xst, y_2060, z_2060),
              (xa, y_2060, z_2060), (xa, y_2060, zn)]
    xk = sum(K['ky_x']) / 2.0
    zur_kette = raus + [(-xa, K['ky_fest'], zn),
                        (xk, K['ky_fest'], K['ky_z_unten'])]
    ende_y = (xk, K['ky_ende0'], K['ky_z_oben'])     # Portal in der Mitte
    motor = K['portal']['X-Motor']
    x_motor = [ende_y, (xk, ende_y[1], 65.0), (motor.x[0], -16.4, 65.0)]
    x_es = [ende_y, (xk, ende_y[1], 20.0), (K['es_x'][0], K['es_x'][1], 20.0)]
    yk = sum(K['kx_y']) / 2.0
    zur_x = [ende_y, (xk, yk, K['kx_z_unten']),
             (K['kx_fest'], yk, K['kx_z_unten'])]
    xm = K['xm']
    am_th = [(xm, yk, K['kx_z_oben']), (xm, 0.0, K['kx_z_oben'])]
    z_motor = am_th + [(xm, 0.0, 183.0), (xm + 30.0, 7.4, 183.0)]
    laser_oben = 23.8 + TL['zc_min']                  # Z ganz unten
    laser = am_th + [(xm, 0.0, laser_oben), (xm, 41.0, laser_oben)]
    z_es = am_th + [(xm - 20.0, 16.0, 112.0)]
    ky, kx = K['ky_laenge'], K['kx_laenge']
    wege = {
        'Y-Motor links': (laenge(raus + y_motor(-1)), raus + y_motor(-1)),
        'Y-Motor rechts': (laenge(rechts + y_motor(1)), rechts + y_motor(1)),
        'Y-Endschalter': (laenge(raus + [(-xa, K['es_y'][1], zn)]),
                          raus + [(-xa, K['es_y'][1], zn)]),
        'X-Motor': (laenge(zur_kette) + ky + laenge(x_motor), zur_kette),
        'X-Endschalter': (laenge(zur_kette) + ky + laenge(x_es), None),
        'Z-Motor': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                    + laenge(z_motor), None),
        'Laser (24 V + PWM)': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                               + laenge(laser), None),
        'Z-Endschalter': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                          + laenge(z_es), None),
    }
    return wege


def kauflaenge(mm):
    m = mm * (1.0 + RESERVE) / 1000.0
    return next((k for k in KAUFLAENGEN if k >= m - 1e-9), KAUFLAENGEN[-1])


def linienzug(f, punkte, farbe=KABEL, breite=1.6, strich='5 3'):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(*map(f1, f.px(a, b)))
                           for a, b in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': breite,
        'stroke-dasharray': strich, 'stroke-linejoin': 'round'})


def punkt(f, a, b, farbe=ROT, r=4.5):
    x, y = f.px(a, b)
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': f1(r),
                         'fill': farbe, 'stroke': '#ffffff',
                         'stroke-width': '1.2'})


def fach_rect(f, a0, a1, b0, b1):
    (xa, ya), (xb, yb) = f.px(a0, b0), f.px(a1, b1)
    return el('rect', {'x': f1(min(xa, xb)), 'y': f1(min(ya, yb)),
                       'width': f1(abs(xb - xa)), 'height': f1(abs(yb - ya)),
                       'fill': 'url(#schraffur)', 'stroke': ORANGE,
                       'stroke-width': '1.3'})


# ---- Draufsicht auf die ganze Maschine ------------------------------------
def draufsicht(f, w, L, K):
    R = L['R']
    P = K['portal']
    t = []
    for y in (L['quer_y_vorn'], L['quer_y_hinten']):
        t.append(f.rect(L['quer_x'][0], L['quer_x'][1], y[0], y[1],
                        'profil'))
    for s in (-1, 1):
        t.append(f.rect(s * (R - w('rahmen_b') / 2), s * (R + w('rahmen_b')
                                                           / 2),
                        *L['rahmen_y'], 'profil'))
        t.append(f.rect(s * (R - 6.0), s * (R + 6.0), *L['y_schiene_y'],
                        'fuehrung'))
    fach = K['fach']
    t.append(fach_rect(f, fach.x[0], fach.x[1], fach.y[0], fach.y[1]))
    # Arbeitsflaeche: so weit reicht der Strahl mit Z unten
    sy = K['strahl_y']
    t.append(f.rect(L['xw_min'], L['xw_max'], sy - K['d_hinten'],
                    sy + K['d_vorn'], 'toolhead', fill_opacity='0.18',
                    stroke_dasharray='6 4'))
    # Portal in der Mitte
    for n in ('Platte links', 'Platte rechts', 'Portalrohr', 'X-Schiene',
              'Stirnblock links', 'Stirnblock rechts', 'Umlenkhalter Saeule',
              'Motorhalter Saeule hinten'):
        q = P[n]
        art = 'profil' if n == 'Portalrohr' else (
            'fuehrung' if 'Schiene' in n else 'druck')
        t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art))
    q = P['X-Motor']
    t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], 'kauf'))
    xm = K['xm']
    for q in K['feste'] + K['bewegte']:
        t.append(f.rect(q.x[0] + xm, q.x[1] + xm, q.y[0], q.y[1], 'toolhead',
                        fill_opacity='0.55'))
    # Portal an der hinteren Grenze (Softlimit)
    dh = K['d_hinten']
    for n in ('Portalrohr', 'Platte links', 'Platte rechts'):
        q = P[n]
        t.append(f.rect(q.x[0], q.x[1], q.y[0] - dh, q.y[1] - dh, 'druck',
                        fill='none', stroke_dasharray='4 3'))
    # Y-Motoren vorn
    fl = w('motor_flansch') / 2.0
    for s in (-1, 1):
        x = s * (R - L['ym_u'])
        t.append(f.rect(x - fl, x + fl, L['ym_y'] - fl, L['ym_y'] + fl,
                        'kauf'))
    # Energieketten: Wanne und die Huelle der Kette in der Mitte
    t.append(f.rect(K['ky_x'][0] - 2, K['ky_x'][1] + 2, *K['ky_wanne'], 'neu',
                    stroke_dasharray='4 3', fill_opacity='0.6'))
    # Schleife nach hinten: sie steht auf halbem Weg zwischen Festpunkt und
    # bewegtem Ende, um den halben Hub nach hinten versetzt
    ym0 = K['ky_ende0']
    y_schleife = (K['ky_fest'] + ym0 - K['ky_hub'] / 2.0) / 2.0
    t.append(f.rect(K['ky_x'][0], K['ky_x'][1],
                    y_schleife - KETTE_R - KETTE_H / 2.0,
                    max(K['ky_fest'], ym0), 'kette'))
    t.append(f.rect(K['kx_wanne'][0], K['kx_wanne'][1], K['kx_y'][0] - 2,
                    K['kx_y'][1] + 2, 'neu', stroke_dasharray='4 3',
                    fill_opacity='0.6'))
    x_schleife = (K['kx_fest'] + K['xm'] + K['kx_hub'] / 2.0) / 2.0
    t.append(f.rect(min(K['kx_fest'], K['xm']),
                    x_schleife + KETTE_R + KETTE_H / 2.0, *K['kx_y'],
                    'kette'))
    # Steuerung, Netzteil, Netzbuchse
    for n, art in (('steuerung', 'neu'), ('netzteil', 'kauf'),
                   ('netzbuchse', 'kauf')):
        q = K[n]
        t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art,
                        stroke_dasharray='5 3', stroke_width='1.2'))
    # feste Kabelwege
    for n in ('Y-Motor links', 'Y-Motor rechts', 'Y-Endschalter', 'X-Motor'):
        weg = K['kabel'][n][1]
        t.append(linienzug(f, [(p[0], p[1]) for p in weg]))
    # Endschalter
    for a, b in (K['es_x'], K['es_y'], K['es_z']):
        t.append(punkt(f, a, b))
    return t


# ---- Seitenansicht von links ----------------------------------------------
def seitenansicht(f, w, L, TL, K):
    P = K['portal']
    t = []
    fach = K['fach']
    zt = L['quer_z'][0]
    t.append(f.rect(f.a[0] - 5, f.a[1] + 5, zt - 12.0, zt, 'profil',
                    fill='#f1efe9', stroke='none'))
    t.append(f.linie(f.a[0], zt, f.a[1], zt, GRAU, 1.0))
    t.append(f.rect(L['rahmen_y'][0], L['rahmen_y'][1], L['rahmen_z0'],
                    L['rahmen_z1'], 'profil'))
    t.append(f.rect(L['y_schiene_y'][0], L['y_schiene_y'][1],
                    L['rahmen_z1'], L['rahmen_z1'] + 8.0, 'fuehrung'))
    for y in (L['quer_y_vorn'], L['quer_y_hinten']):
        t.append(f.rect(y[0], y[1], *L['quer_z'], 'profil'))
    fl = w('motor_flansch') / 2.0
    t.append(f.rect(L['ym_y'] - fl, L['ym_y'] + fl, L['ym_motor_z0'],
                    L['ymp_z0'], 'kauf'))
    # Fach und die hoehere Zone in der Mitte
    t.append(fach_rect(f, fach.y[0], fach.y[1], fach.z[0], fach.z[1]))
    t.append(f.rect(fach.y[0], K['y_tr'], fach.z[1], K['z_frei'] - 0.0,
                    'neu', fill='none', stroke_dasharray='3 3'))
    for n, art in (('netzteil', 'kauf'), ('steuerung', 'neu')):
        q = K[n]
        t.append(f.rect(q.y[0], q.y[1], q.z[0], q.z[1], art,
                        stroke_dasharray='5 3', stroke_width='1.2'))
    # Portal an der hinteren Grenze, Z unten
    dh = -K['d_hinten']
    for n in ('Platte links', 'Portalrohr', 'Y-Wagen links',
              'Klemmturm hinten links', 'Klemmturm vorn links',
              'Stirnblock links'):
        q = P[n]
        art = 'profil' if n == 'Portalrohr' else (
            'fuehrung' if 'Wagen' in n else 'druck')
        t.append(f.rect(q.y[0] + dh, q.y[1] + dh, q.z[0], q.z[1], art))
    for q in K['feste'] + [b.verschoben(TL['zc_min']) for b in K['bewegte']]:
        t.append(f.rect(q.y[0] + dh, q.y[1] + dh, q.z[0], q.z[1], 'toolhead',
                        fill_opacity='0.55'))
    # Traegerplatte am hinteren Schienenende, Z oben
    ds = -K['d_schiene']
    for q in K['feste']:
        if q.name in ('Traegerplatte Hauptsaeule', 'X-Wagen MGN15H'):
            t.append(f.rect(q.y[0] + ds, q.y[1] + ds, q.z[0], q.z[1],
                            'toolhead', fill='none', stroke_dasharray='4 3',
                            stroke_width='1.1'))
    q = P['Portalrohr']
    t.append(f.rect(q.y[0] + ds, q.y[1] + ds, q.z[0], q.z[1], 'profil',
                    fill='none', stroke_dasharray='4 3'))
    # Y-Kette mit dem Portal an der hinteren Grenze: ganz abgerollt, die
    # Schleife steht am bewegten Ende
    yb = K['ky_bewegt'][0]
    zu, zo = K['ky_z_unten'], K['ky_z_oben']
    t.append(f.rect(K['ky_wanne'][0], K['ky_wanne'][1], K['ky_z_wanne'],
                    K['ky_z_wanne'] + 3.0, 'neu', stroke_dasharray='4 3'))
    x0, y0 = f.px(K['ky_fest'], zu)
    x1, y1 = f.px(yb, zu)
    _, y2 = f.px(yb, zo)
    r = (y1 - y2) / 2.0
    d = 'M {} {} L {} {} A {} {} 0 0 1 {} {}'.format(
        f1(x0), f1(y0), f1(x1), f1(y1), f1(r), f1(r), f1(x1), f1(y2))
    t.append(el('path', {'d': d, 'fill': 'none', 'stroke': '#a3abb8',
                         'stroke-width': f1(KETTE_H * f.s),
                         'stroke-linecap': 'butt'}))
    t.append(el('path', {'d': d, 'fill': 'none', 'stroke': '#3d4552',
                         'stroke-width': '0.8', 'stroke-dasharray': '3 2'}))
    return t


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    K = konzept(w, L, tw, TL)
    K['strahl_y'] = TL['strahl_y']
    K['z_frei'] = -16.0 - w('luft_bau')         # unter dem X-Wagen
    fach = K['fach']
    R = L['R']
    t = [el('defs', {}, '<pattern id="schraffur" width="7" height="7" '
            'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="7" height="7" fill="#fbeee2"/>'
            '<line x1="0" y1="0" x2="0" y2="7" stroke="#e8a871" '
            'stroke-width="1.4"/></pattern>'),
         text(24, 30, 'Platz für die Elektronik — Vorschlag (Portal.py Rev. '
              '{}, ToolheadZ.py Rev. {})'.format(pm.REVISION, th.REVISION),
              14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich. Rahmen, Portal und Toolhead aus den '
              'Skripten; Steuerung, Netzteil und Ketten sind Platzhalter, '
              'ihre Maße stehen noch aus.', 9, GRAU)]

    # ---- Draufsicht --------------------------------------------------------
    s1 = 0.86
    fa = Feld(262, 92, (-338.0, 338.0), (-392.0, 305.0), s1, b_runter=True)
    t += fa.ausschnitt('drauf', draufsicht(fa, w, L, K))
    t += fa.rahmen('Draufsicht (vorn unten)')
    st, nt = K['steuerung'], K['netzteil']
    xm = K['xm']
    t += fa.spalte([
        (-R, L['rahmen_y'][0] + 20.0, 'linkes 2040 (600 mm)'),
        (-150.0, L['quer_y_hinten'][0] + 8.0, 'hinteres 2060'),
        (-150.0, L['quer_y_vorn'][0] + 8.0, 'vorderes 2060'),
        (L['xw_min'] + 15.0, K['strahl_y'] + K['d_vorn'] - 12.0,
         'Arbeitsfläche: Strahl mit\nZ unten ({} × {} mm)'.format(
             de(L['xw_max'] - L['xw_min'], 0),
             de(K['d_vorn'] + K['d_hinten'], 0))),
        (-R + L['ym_u'], L['ym_y'], 'Y-Motor links'),
        (sum(K['ky_x']) / 2, K['ky_fest'] - 30.0,
         'Energiekette Y außen\nam linken 2040'),
        (sum(K['ky_x']) / 2, K['ky_wanne'][0] + 6.0,
         'Kettenwanne, hängt außen\nam 2040 (untere Nut)'),
        (K['es_y'][0], K['es_y'][1], 'Y-Endschalter'),
        (K['es_x'][0], K['es_x'][1], 'X-Endschalter'),
        (-200.0, K['portal']['Portalrohr'].y[0] - K['d_hinten'] + 5.0,
         'Portal an der hinteren\nGrenze (Softlimit Y)')],
        fa.ox - 12, 'end', abstand=24.0)
    t += fa.spalte([
        ((st.x[0] + st.x[1]) / 2, st.y[0] + 12.0,
         'Steuerung: Uno + CNC Shield\nV3 + 4 × TMC2209, Lüfter'),
        ((nt.x[0] + nt.x[1]) / 2, nt.y[0] + 12.0,
         'Netzteil 24 V (Platzhalter\n{} × {} × {})'.format(
             *[de(v, 0) for v in NETZTEIL])),
        (sum(K['netzbuchse'].x) / 2, sum(K['netzbuchse'].y) / 2,
         'Netz: Kaltgerätebuchse mit\nSchalter und Sicherung'),
        (fach.x[1] - 10.0, fach.y[1] - 10.0,
         'Elektronikfach unter den\n2040, {} × {} × {} mm'.format(
             de(fach.x[1] - fach.x[0], 0), de(fach.y[1] - fach.y[0], 0),
             de(fach.z[1] - fach.z[0], 0))),
        (K['kx_wanne'][1] - 20.0, K['kx_y'][0],
         'Energiekette X über dem\nRohr, hinter dem Riemen'),
        (xm + 20.0, 40.0, 'Toolhead (Mitte)'),
        (K['es_z'][0], K['es_z'][1], 'Z-Endschalter (vorhanden)'),
        (R - L['ym_u'], L['ym_y'], 'Y-Motor rechts'),
        (R + 10.0, 60.0, 'Kabel Y-Motor rechts\nin der unteren Nut außen')],
        fa.ox + fa.breite + 12, 'start', abstand=24.0)

    # ---- Seitenansicht -----------------------------------------------------
    s2 = 1.45
    fb = Feld(262, fa.oy + fa.hoehe + 70, (-392.0, 20.0), (-146.0, 72.0),
              s2)
    t += fb.ausschnitt('seite', seitenansicht(fb, w, L, TL, K))
    t += fb.rahmen('Seitenansicht von links, hinterer Teil (vorn rechts): '
                   'Portal an der hinteren Grenze, Z unten')
    t += fb.spalte([
        (fach.y[0] + 15.0, fach.z[0] + 12.0, 'Elektronikfach'),
        (-300.0, K['z_frei'] - 6.0,
         'in der Mitte darf es höher\nwerden (gestrichelt)'),
        (K['ky_wanne'][0] + 30.0, K['ky_z_unten'],
         'Energiekette Y (davor),\nSchleife am Portal'),
        (L['quer_y_hinten'][0] + 5.0, L['quer_z'][0] + 10.0,
         'hinteres 2060'),
        (-150.0, L['quer_z'][0], 'Tisch')],
        fb.ox - 12, 'end', abstand=24.0)
    tr = next(q for q in K['feste'] if q.name == 'Traegerplatte Hauptsaeule')
    t += fb.spalte([
        (tr.y[1] - K['d_schiene'], tr.z[0] + 30.0,
         'Trägerplatte am Schienenende\n(nur mit Z oben, gestrichelt)'),
        (K['strahl_y'] - K['d_hinten'], -110.0,
         'Toolhead mit Z unten: 3 mm\nvor dem hinteren 2060'),
        (-60.0, L['rahmen_z1'] - 8.0, '2040 (davor die Kette)'),
        (-211.0, 66.0, 'Toolhead oben abgeschnitten')],
        fb.ox + fb.breite + 12, 'start', abstand=26.0)
    t += fb.mass(fach.y[0] + 12.0, fach.z[0], fach.z[1], '{} mm'.format(
        de(fach.z[1] - fach.z[0], 0)), 4)
    t += quer_mass(fb, fach.y[0], fach.y[1], fach.z[0] + 6.0, '{} mm'.format(
        de(fach.y[1] - fach.y[0], 0)), -4)
    t += fb.luft(tr.y[0] - K['d_schiene'] + 4.0, fach.z[1],
                 tr.y[0] - K['d_schiene'] + 4.0, tr.z[0],
                 '{} mm'.format(de(tr.z[0] - fach.z[1], 0)), dx=5, dy=-2)

    # ---- Zahlen ------------------------------------------------------------
    ty = fb.oy + fb.hoehe + 50
    kab = K['kabel']
    zeilen = [
        ('Fach', '{} × {} × {} mm (B × T × H) hinter dem hinteren 2060, '
         'unter den 2040 — dort fährt nichts hin, engste Stelle {} mm '
         '(Trägerplatte'.format(
             de(fach.x[1] - fach.x[0], 0), de(fach.y[1] - fach.y[0], 0),
             de(fach.z[1] - fach.z[0], 0), de(tr.z[0] - fach.z[1], 0))),
        ('', 'am hinteren Schienenende, nur mit Z oben). Die Tiefe hängt an '
         'der Lage des hinteren 2060 (400 mm Mitte zu Mitte angenommen).'),
        ('höher', 'in der Mitte (|X| ≤ 225) ab {} mm hinter dem 2060 frei bis '
         'Z {} — {} mm über der Oberkante der 2040'.format(
             de(L['quer_y_hinten'][0] - K['y_tr'], 0), de(K['z_frei'], 0),
             de(K['z_frei'] - L['rahmen_z1'], 0))),
        ('Endschalter', 'LM393-Gabellichtschranken: X links am Portal, Y '
         'außen am linken 2040 — schaltet, wenn der Toolhead mit Z unten '
         '3 mm vor dem hinteren 2060 steht; Z vorhanden'),
        ('Kette Y', '{} mm Hub, Festpunkt {} mm vom hinteren Ende des 2040, '
         'Schleife nach hinten, ≈ {} mm Kette (R{})'.format(
             de(K['ky_hub'], 0), de(K['ky_fest'] - L['rahmen_y'][0], 0),
             de(K['ky_laenge'], 0), de(KETTE_R, 0))),
        ('Kette X', '{} mm Hub, Festpunkt in der Mitte, Schleife nach rechts '
         '(links steht der X-Motor), ≈ {} mm Kette (R{})'.format(
             de(K['kx_hub'], 0), de(K['kx_laenge'], 0), de(KETTE_R, 0))),
    ]
    for n in ('Y-Motor links', 'Y-Motor rechts', 'X-Motor', 'Z-Motor',
              'Laser (24 V + PWM)', 'X-Endschalter', 'Y-Endschalter',
              'Z-Endschalter'):
        mm = kab[n][0]
        zeilen.append(('Kabel' if n == 'Y-Motor links' else '',
                       '{}: Weg ≈ {} m → {} m kaufen'.format(
                           n, de(mm / 1000.0, 2), de(kauflaenge(mm), 1))))
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('druck', 'Portal (vorhanden)'),
                                  ('toolhead', 'Toolhead'),
                                  ('profil', 'Aluprofil'),
                                  ('fuehrung', 'Linearführung'),
                                  ('kauf', 'Kaufteil'),
                                  ('kette', 'Energiekette'))):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    x, y = 24 + 3 * 170, ly + 18
    t.append(linie(x, y + 4.5, x + 16, y + 4.5, KABEL, 1.6, '5 3'))
    t.append(text(x + 21, y + 8, 'Kabel, fest verlegt', 8.5))
    y = ly + 36
    t.append(el('rect', {'x': '24', 'y': f1(y), 'width': '14', 'height': '9',
                         'fill': 'url(#schraffur)', 'stroke': ORANGE}))
    t.append(text(43, y + 8, 'Elektronikfach', 8.5))
    t.append(el('circle', {'cx': f1(24 + 170 + 7), 'cy': f1(y + 4.5),
                           'r': '4.5', 'fill': ROT}))
    t.append(text(24 + 170 + 19, y + 8, 'Endschalter', 8.5))
    t.append(text(24, ly + 66, 'Gestrichelt: Platzhalter bzw. andere '
                  'Stellung. Kabelwege mit {} % Reserve aufgerundet; die '
                  'Ketten zählen mit ihrer ganzen Länge.'.format(
                      de(RESERVE * 100, 0)), 8.5, GRAU))
    W = int(fa.ox + fa.breite + 250)
    H = int(ly + 82)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)
    for n, (mm, _) in K['kabel'].items():
        print('  {:<22} Weg {:6.0f} mm  -> {} m'.format(n, mm,
                                                        kauflaenge(mm)))
    print('  Kette Y {:.0f} mm, Kette X {:.0f} mm'.format(K['ky_laenge'],
                                                         K['kx_laenge']))


if __name__ == '__main__':
    main()
