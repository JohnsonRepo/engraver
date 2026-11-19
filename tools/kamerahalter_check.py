#!/usr/bin/env python3
"""Rechnerische Pruefung des Kamerahalters (fusion/Kamerahalter) — laeuft
ohne Fusion.

Importiert Kamerahalter.py, ToolheadZ.py, Portal.py, Opferplatte.py,
Spannmittel.py und Elektronikfach.py mit gestubbtem adsk-Modul und prueft:
Abgleich der Masse, Lage auf dem hinteren 2060, Freiraum zu allem, was der
Toolhead und das Portal ueber den ganzen Weg ueberstreichen, Abstand zum
Elektronikfach, Kamera auf dem Halter, Sicht zum Messpunkt fuer jede
Werkstueckdicke (frei, im Bild, scharf), Schrauben, Druck und Kabel. Gibt
die Stueckliste aus.

Teile, die im Halter gedreht stehen, gehen als umschreibender Quader in
Maschinenkoordinaten ein; der echte Abstand ist also mindestens so gross
wie gemeldet.

    python3 tools/kamerahalter_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from bauraum import Quader                            # noqa: E402
from opferplatte_check import OPFERPLATTE             # noqa: E402
from spannmittel_check import SPANNMITTEL             # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
KAMERAHALTER = os.path.join(HIER, '..', 'fusion', 'Kamerahalter',
                            'Kamerahalter.py')
FACH = os.path.join(HIER, '..', 'fusion', 'Elektronikfach',
                    'Elektronikfach.py')
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
PETG = 1.27            # g/cm3
KUENSTLICH = ('Portalprofil 2020', 'X-Schiene MGN15')   # Stellvertreter
RAND_BILD = 5.0        # Grad: so weit muss der Punkt im Bild liegen
LUFT_FACH = 1.5        # Deckel geht ab, nichts liegt an
KABEL_LUFT = 2.5       # steifes Kabelende bis zur Vorderwand des Fachs
KABEL_RESERVE = 30.0   # so viel bleibt vom Kamerakabel uebrig
SCHRITTE = 600         # Stuetzpunkte je Sichtlinie


def flaeche(punkte):
    s = 0.0
    for (a0, b0), (a1, b1) in zip(punkte, punkte[1:] + punkte[:1]):
        s += a0 * b1 - a1 * b0
    return abs(s) / 2.0


def quader_aus(name, punkte):
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    zs = [p[2] for p in punkte]
    return Quader(name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def engste(teile, andere):
    best = (float('inf'), None, None)
    for a in teile:
        for b in andere:
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def schneidet(p0, p1, q):
    for i in range(1, SCHRITTE):
        s = i / float(SCHRITTE)
        x, y, z = (p0[k] + (p1[k] - p0[k]) * s for k in range(3))
        if (q.x[0] < x < q.x[1] and q.y[0] < y < q.y[1]
                and q.z[0] < z < q.z[1]):
            return True
    return False


def ueberstrichen(tw, TL, w, L):
    """Toolhead und Portal ueber den ganzen Weg: Quader + Weg."""
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    dy0, dy1 = -L['y_weg_hinten'], w('y_weg_vorn')
    xw0, xw1 = L['xw_min'], L['xw_max']
    zc0, zc1 = TL['zc_min'], TL['zc_max']
    u = []
    for q in feste:
        if q.name not in KUENSTLICH:
            u.append(Quader('Toolhead ' + q.name, q.x[0] + xw0, q.x[1] + xw1,
                            q.y[0] + dy0, q.y[1] + dy1, q.z[0], q.z[1]))
    for q in bewegte:
        u.append(Quader('Toolhead ' + q.name, q.x[0] + xw0, q.x[1] + xw1,
                        q.y[0] + dy0, q.y[1] + dy1, q.z[0] + zc0,
                        q.z[1] + zc1))
    R = L['R']
    py = L['portal_y']
    u.append(Quader('Portalrohr', -R, R, py - 20.0 + dy0, py + dy1,
                    L['profil_z0'], L['profil_z1']))
    u.append(Quader('X-Schiene', *L['x_schiene_x'], py + dy0,
                    L['x_schiene_y1'] + dy1, -7.5, 7.5))
    for n, (a, b) in L['st_x'].items():
        u.append(Quader('Stuetze X-Kette ' + n, a, b,
                        L['st_platte_y'][0] + dy0, L['st_arm_y'][1] + dy1,
                        L['st_platte_z'][0], L['st_platte_z'][1]))
    u.append(Quader('Wanne X-Kette', *L['wanne_x'], L['wanne_y'][0] + dy0,
                    L['wanne_y'][1] + dy1, *L['wanne_z']))
    for s in (-1, 1):
        def ux(v):
            return s * (R - v)
        for n, (ya, yb) in (('hinten', L['kt_y_hinten']),
                            ('vorn', L['kt_y_vorn'])):
            xa, xb = sorted((ux(L['kt_u'][0]), ux(L['kt_u'][1])))
            u.append(Quader('Klemmturm ' + n, xa, xb, ya + dy0, yb + dy1,
                            *L['kt_z']))
        xa, xb = sorted((ux(L['platte_u'][0]), ux(L['platte_u'][1])))
        u.append(Quader('Y-Schlitten', xa, xb, L['platte_y0'] + dy0,
                        L['platte_y1'] + dy1, *L['platte_z']))
    return u


def toolhead_am_messpunkt(tw, TL, L, KL):
    """Toolhead und Portalrohr, wenn der Strahl auf dem Messpunkt steht,
    Z am Schaltpunkt oben, der Laser 8 mm tief im Langloch."""
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    mx, my = KL['mp']
    dy = my - TL['strahl_y']
    zc = TL['zc_arbeit_max']
    q = [Quader('Portalrohr am Messpunkt', -L['R'], L['R'],
                L['portal_y'] - 20.0 + dy, L['portal_y'] + dy,
                L['profil_z0'], L['profil_z1'])]
    for b in feste:
        if b.name not in KUENSTLICH:
            q.append(Quader(b.name, b.x[0] + mx, b.x[1] + mx, b.y[0] + dy,
                            b.y[1] + dy, b.z[0], b.z[1]))
    for b in bewegte:
        tief = tw('laser_langloch_hub') if b.name == 'Diodenlaser' else 0.0
        q.append(Quader(b.name, b.x[0] + mx, b.x[1] + mx, b.y[0] + dy,
                        b.y[1] + dy, b.z[0] + zc - tief, b.z[1] + zc))
    return q


def volumen(km, KL):
    """Volumen des Halters (mm3): die Schritte 'dazu' beruehren sich nur,
    die Schritte 'weg' liegen ganz im Material."""
    w = km.w
    v = 0.0
    for s in KL['plan']['Kamerahalter']:
        lang = s['a'][1] - s['a'][0]
        if s['form'] == 'rechteck':
            a = sum((u1 - u0) * (v1 - v0) for u0, v0, u1, v1 in s['formen'])
        elif s['form'] == 'kreis':
            a = len(s['formen']) * math.pi * (s['d'] / 2.0) ** 2
        elif s['form'] == 'vieleck':
            a = sum(flaeche(list(p)) for p in s['formen'])
        else:
            a = sum(flaeche(km.tropfen_punkte(u, vv, s['d'], s['spitze'],
                                              s.get('kappe')))
                    for u, vv in s['formen'])
        if s['art'] == 'weg':
            # M2 und Taschen nur durch Wand und Polster, M5 durch den Fuss
            if s['name'] == 'M2_Loecher':
                lang = w('wand_t') + w('pad_h')
            elif s['name'] == 'Muttertaschen':
                lang = KL['tasche_y'][1] - KL['tasche_y'][0]
            elif s['name'] == 'M5_Loecher':
                lang = w('fuss_t')
            v -= a * lang
        else:
            v += a * lang
    return v


def main():
    km = bauraum.modul_laden(KAMERAHALTER, 'kamerahalter')
    kw, KL = km.w, km.lage()
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    ow, OL = om.w, om.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    SL = sm.lage()
    fm = bauraum.modul_laden(FACH, 'elektronikfach')
    FL = fm.lage()
    p = Pruefung()
    lx, ly, lz = KL['linse']
    teile = {n: quader_aus(n, ps) for n, ps in KL['welt'].items()}
    kamera = [teile[n] for n in KL['kamera_teile']]
    halter = [teile[n] for n in list(KL['halter_teile']) + ['Fuss']]

    # ------------------------------------------------------------------
    p.titel('1) Abgleich mit Portal.py, Opferplatte.py, Spannmittel.py, '
            'Elektronikfach.py')
    for text, ist, soll in (
            ('hinteres 2060: Rueckseite', kw('quer_y1'), L['quer_y_hinten'][0]),
            ('hinteres 2060: Vorderseite', kw('quer_y1') + kw('rahmen_b'),
             L['quer_y_hinten'][1]),
            ('Oberseite 2060', kw('rahmen_z0'), L['quer_z'][1]),
            ('Unterseite 2060', kw('rahmen_z0') - kw('quer_h'),
             L['quer_z'][0]),
            ('Oberseite Opferplatte', kw('platte_z1'), OL['platte_z'][1]),
            ('Anschlag: Innenecke X', kw('ecke_x'), SL['aw_ecke'][0]),
            ('Anschlag: Innenecke Y', kw('ecke_y'), SL['aw_ecke'][1]),
            ('Fach: Vorderwand aussen', kw('fach_vorn_y'), FL['fach_y'][1]),
            ('Fach: Oberkante der Waende', kw('fach_rand_z'), FL['rand_z']),
            ('Fach: Oberseite Deckel', kw('deckel_z1'), FL['deckel_z'][1]),
            ('Fach: Unterseite', kw('fach_boden_z'), FL['fach_z'][0]),
            ('Fach: Vorderwand innen', kw('fach_vorn_y') - kw('fach_wand'),
             FL['gasse_vorn'][1]),
            ('Pi: Vorderkante (Kamerabuchse) Y', kw('pi_buchse_y'),
             FL['pi_y'][1]),
            ('Pi: Mitte der Schmalseite Z', kw('pi_buchse_z'),
             sum(FL['pi_z']) / 2.0)):
        p.ok(text, abs(ist - soll), 0.01, '<=')
    p.ja('Pi: Kamerabuchse auf der Bauteilseite (X zwischen Platine und '
         'Bauteilen)', FL['pi_bauteile_x'][0] - 0.5 <= kw('pi_buchse_x')
         <= FL['pi_pcb_x'][0] + 0.5)
    # Die Werte oben sind Fachkoordinaten. Kamerahalter Rev. 1 setzt voraus,
    # dass das Fach dort auch steht: hinter dem hinteren 2060, direkt hinter
    # dem Halter. Seit Elektronikfach Rev. 2 steht es vor dem vorderen 2060
    # (so verbaut), und die Kamera sitzt an der Maschine vorn rechts.
    fach_m = fm.bereich_nach_maschine(FL['geh_x'], FL['geh_y'], FL['geh_z'])
    fach_hinten = fach_m[1][1] <= L['quer_y_hinten'][0] + 0.01
    p.ja('Elektronikfach hinter dem hinteren 2060, wie Rev. 1 annimmt',
         fach_hinten, '' if fach_hinten else
         ' — es steht seit Elektronikfach Rev. 2 vorn (Y {:+.0f}..{:+.0f}); '
         'Kamerahalter auf die Kamera vorn rechts umstellen'.format(
             *fach_m[1]))
    u = ueberstrichen(tw, TL, w, L)
    # was vom Toolhead unter den obersten Punkt der Kamera reicht und ueber
    # Kamera und Halter in X faehrt
    xs = [q for t in KL['welt'].values() for q in t]
    xa, xb = min(q[0] for q in xs), max(q[0] for q in xs)
    tief = [q for q in u if q.name.startswith('Toolhead')
            and q.z[0] < KL['oben_z'] and q.x[0] < xb and xa < q.x[1]]
    th_y = min(q.y[0] for q in tief)
    th_z = min(q.z[0] for q in tief if abs(q.y[0] - th_y) < 1e-6)
    p.ok('Toolhead: hinterste Lage ueber X der Kamera (th_hinten_y)',
         abs(kw('th_hinten_y') - th_y), 0.01, '<=')
    p.ok('   ab Z (th_hinten_z, Unterkante Traegerplatte)',
         abs(kw('th_hinten_z') - th_z), 0.01, '<=')
    xwa = [q for q in u if q.name == 'Toolhead X-Wagen MGN15H'][0]
    p.ok('X-Wagen: hinterste Lage (xwagen_hinten_y)',
         abs(kw('xwagen_hinten_y') - xwa.y[0]), 0.01, '<=')
    p.ok('X-Wagen: Unterkante (xwagen_z0)', abs(kw('xwagen_z0') - xwa.z[0]),
         0.01, '<=')
    p.ok('dickstes Werkstueck <= frei unter dem Toolhead (ToolheadZ.py)',
         kw('werkstueck_max'), TL['werkstueck_frei'], '<=')

    # ------------------------------------------------------------------
    p.titel('2) Lage: Fuss auf der Oberseite des hinteren 2060')
    fx, fy = KL['fuss_x'], KL['fuss_y']
    q0, q1 = KL['quer_y']
    p.ok('Fuss hinten auf dem 2060', fy[0] - q0, 0.0)
    p.ok('Fuss vorn auf dem 2060', q1 - fy[1], 0.0)
    p.ok('M5 in der Nutmitte (Y)', abs(KL['nut_y'] - (q0 + q1) / 2.0), 0.01,
         '<=')
    R = L['R']
    p.ok('Fuss links weit genug von den Winkeln am linken 2040',
         fx[0] - (-R + w('rahmen_b') / 2.0 + 20.0), 3.0)
    p.ok('Fuss rechts weit genug von den Winkeln am rechten 2040',
         (R - w('rahmen_b') / 2.0 - 20.0) - fx[1], 3.0)
    p.info('Fuss X {:+.1f}..{:+.1f}, Y {:+.1f}..{:+.1f}; Pi hinten bei X '
           '{:+.1f}'.format(fx[0], fx[1], fy[0], fy[1], kw('pi_buchse_x')))
    for name in ('Wand', 'Rippe'):
        ps = KL['welt'][name]
        auf = min(min(X - fx[0], fx[1] - X, Y - fy[0], fy[1] - Y)
                  for X, Y, Z in ps if abs(Z - KL['fuss_z'][1]) < 1e-6)
        p.ok('{} steht ganz auf dem Fuss'.format(name), auf, 0.0)

    # ------------------------------------------------------------------
    p.titel('3) Freiraum zu Toolhead und Portal ueber den ganzen Weg')
    d, a, b = engste(kamera, u)
    p.ok('Kamera ({} / {})'.format(a, b), d, kw('luft_bau'))
    d, a, b = engste(halter, u)
    p.ok('Halter ({} / {})'.format(a, b), d, kw('luft_bau'))
    p.ok('vorderster Punkt hinter der Traegerplatte',
         kw('th_hinten_y') - KL['vorn_y'], kw('luft_bau') - 0.01)
    p.ok('unter dem X-Wagen (oberster Punkt)', kw('xwagen_z0')
         - KL['oben_z'], kw('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('4) Freiraum zu Elektronikfach, 2060 und Kabel')
    fx_, fy_, fz_ = fm.bereich_nach_maschine(
        FL['fach_x'], FL['fach_y'], (FL['fach_z'][0], FL['deckel_z'][1]))
    fach = Quader('Elektronikfach mit Deckel', *fx_, *fy_, *fz_)
    d, a, _ = engste(kamera + halter, [fach])
    p.ok('Fach und Deckel ({}); der Deckel geht ab'.format(a), d, LUFT_FACH)
    q2060 = Quader('2060 hinten', *L['quer_x'], *L['quer_y_hinten'],
                   *L['quer_z'])
    d, a, _ = engste(kamera + [x for x in halter if x.name != 'Fuss'],
                     [q2060])
    p.ok('ueber dem 2060 (nur der Fuss liegt auf; {})'.format(a), d, 3.0)
    p.ok('Fuss liegt auf dem 2060', abs(KL['fuss_z'][0] - L['quer_z'][1]),
         0.01, '<=')
    p.ok('Kabel tritt aus: Abstand zur Vorderwand', KL['kabel_wand'],
         KABEL_LUFT)
    p.ok('   steifes Kabelende bis zur Vorderwand', KL['kabel_steif_wand'],
         KABEL_LUFT)
    p.ok('Kabel tritt ueber dem Fuss aus (Unterkante Kabel)',
         KL['kabel_aus_welt'][2] - kw('kabel_b') / 2.0 - KL['fuss_z'][1],
         3.0)
    # Gasse fuer das Kabel: vom steifen Ende aussen an der Vorderwand nach
    # links bis zum Eintritt, so hoch wie das Kabel breit ist. Gilt nur mit
    # dem Fach hinten (Rev. 1); die Zeilen zeigen den Stand des Halters.
    if not fach_hinten:
        p.info('Kabelgasse und Eintritt unten gelten fuer das Fach hinten '
               '(Rev. 1), nicht fuer die Lage vorn')
    sx, sy, sz = KL['kabel_steif_welt']
    hb = kw('kabel_b') / 2.0
    gasse = Quader('Kabelgasse', KL['kabel_eintritt_x'], sx,
                   kw('fach_vorn_y'), sy, sz - hb, sz + hb)
    zu = [t.name for t in kamera + halter
          if t.name not in ('Stecker', 'Platine') and t.abstand(gasse) < 0.0]
    p.ja('Kabelgasse aussen an der Vorderwand frei (X {:+.0f}..{:+.0f})'
         .format(KL['kabel_eintritt_x'], sx), not zu,
         ' — ' + ', '.join(zu) if zu else '')
    p.ok('Eintritt ins Fach links neben dem Fuss', KL['fuss_x'][0]
         - KL['kabel_eintritt_x'], 3.0)
    p.ok('Eintritt im Fach (linke Haelfte, Signalgasse)',
         KL['kabel_eintritt_x'] - FL['innen_x']['links'][0], 5.0)

    # ------------------------------------------------------------------
    p.titel('5) Kamera auf dem Halter (Camera Module 3, Massblatt [w])')
    p.ok('Polster im freien Ring um die Loecher (Durchmesser)',
         kw('pad_d'), kw('cam_pad_frei'), '<=')
    p.ok('   auch die flache Spitze der Traene (Radius)',
         kw('pad_d') / 2.0 + KL['pad_kappe'], kw('cam_pad_frei') / 2.0
         + 1e-9, '<=')
    p.ok('Polsterhoehe: Platz fuer Bauteile hinten', kw('pad_h'), 1.5)
    p.ok('Wand endet vor dem Stecker (Stecker ragt hinter die Polster)',
         KL['wand'][0][0] - KL['stecker'][0][1], kw('stecker_luft') - 1e-9)
    zr, zk = kw('zapfen_d') / 2.0, kw('zapfen_kappe')
    b_ = zr * math.sqrt(2.0) - (zr + zk)
    p.ok('Zapfen passt ins Loch (weitester Punkt)',
         kw('cam_loch_d') / 2.0 - max(zr, math.hypot(b_, zr + zk)), 0.05)
    p.ok('Zapfen ragt vor die Platine', KL['zapfen_y'][1]
         - KL['platine'][1][1], 0.5)
    p.ok('Platine ueber dem Fuss', KL['platine'][2][0] - KL['fuss_z'][1],
         3.0)
    p.ok('Wand reicht ueber die Platine', KL['wand'][2][1]
         - KL['platine'][2][1], 0.5)
    lochabst = [math.hypot(a[0] - b[0], a[1] - b[1])
                for a in KL['loecher'] for b in KL['loecher'] if a < b]
    p.ok('Lochbild: kleinster Abstand (12,5 laut Massblatt)',
         abs(min(lochabst) - kw('cam_loch_ab')), 0.01, '<=')
    p.ok('Lochbild: Diagonale', abs(max(lochabst) - math.hypot(
        kw('cam_b') - 2.0 * kw('cam_loch_rand'), kw('cam_loch_ab'))), 0.01,
        '<=')
    bk = KL['block']
    for (x, z), kopf in zip(KL['loecher_schraube'], KL['koepfe']):
        frei = max(kopf[0][0] - bk[0][1], bk[0][0] - kopf[0][1],
                   kopf[2][0] - bk[2][1], bk[2][0] - kopf[2][1])
        p.ok('M2-Kopf neben dem Linsenblock (z {:+.1f})'.format(z), frei, 1.0)

    # ------------------------------------------------------------------
    p.titel('6) Sicht zum Messpunkt ({:.0f} rechts, {:.0f} vor der Innenecke)'
            .format(kw('mp_rechts'), kw('mp_vorn')))
    mx, my = KL['mp']
    p.ja('Strahl erreicht den Messpunkt (Arbeitsfeld)',
         sm.w('feld_x0') <= mx <= sm.w('feld_x1')
         and sm.w('feld_y0') <= my <= sm.w('feld_y1'))
    hin = toolhead_am_messpunkt(tw, TL, L, KL)
    (hx, hy), (lx_, ly_) = SL['aw_hinten'], SL['aw_links']
    hindernisse = (hin + [Quader('Anschlag hinten', *hx, *hy, *SL['aw_z']),
                          Quader('Anschlag links', *lx_, *ly_, *SL['aw_z']),
                          q2060, fach]
                   + [t for t in halter])
    hq, hh = KL['bild_halb']
    for s in KL['sicht']:
        punkt = (mx, my, kw('platte_z1') + s['t'])
        zu = [q.name for q in hindernisse if schneidet(KL['linse'], punkt, q)]
        p.ja('t = {:4.0f} mm: frei, {:5.1f} Grad neben, {:5.1f} unter der '
             'Achse'.format(s['t'], s['quer'], s['unter']), not zu,
             ' — ' + ', '.join(zu) if zu else '')
    s0, s1 = KL['sicht'][0], KL['sicht'][-1]
    p.ok('im Bild quer (Bildwinkel {:.1f} je Seite)'.format(hq),
         hq - max(abs(s['quer']) for s in KL['sicht']), RAND_BILD, '>=',
         'Grad')
    p.ok('im Bild unten (duennstes Werkstueck)', hh - s0['unter'],
         RAND_BILD, '>=', 'Grad')
    p.ok('im Bild oben (dickstes Werkstueck)', hh + s1['unter'], RAND_BILD,
         '>=', 'Grad')
    p.ok('scharf: naechster Punkt weiter als der Fokus', s1['abstand'],
         kw('cam_fokus'))
    p.ok('Pixel quer im Bild (halbe Breite {:.0f})'.format(
        KL['bild_px_halb'][0]), KL['bild_px_halb'][0]
        - abs(s0['px_quer']), 0.0, '>=', 'px')
    p.ok('Pixel hoch im Bild (halbe Hoehe {:.0f})'.format(
        KL['bild_px_halb'][1]), KL['bild_px_halb'][1] - s0['px_hoch'], 0.0,
        '>=', 'px')
    p.ok('Aufloesung: mm Hoehe je Pixel', 1.0 / KL['px_je_mm'], 0.1, '<=')
    p.info('Abstand Linse -> Punkt {:.0f} bis {:.0f} mm, {:.1f} Pixel je mm '
           'Hoehe'.format(s1['abstand'], s0['abstand'], KL['px_je_mm']))

    # ------------------------------------------------------------------
    p.titel('7) Schrauben')
    p.ok('M5x{:.0f}: Gewinde im Nutenstein'.format(kw('m5_l')),
         KL['m5_eingriff'], 3.0)
    p.ok('M5: Spitze vor dem Nutgrund', kw('nut_tiefe') - KL['m5_in_nut'],
         0.3)
    rk = kw('m5_kopf_d') / 2.0 + 1.0
    for i, (X, Y) in enumerate(KL['m5_welt']):
        kopf = Quader('M5', X - rk, X + rk, Y - rk, Y + rk, KL['fuss_z'][1],
                      KL['fuss_z'][1] + 60.0)
        d, a, _ = engste(kamera + [t for t in halter if t.name != 'Fuss'],
                         [kopf])
        p.ok('M5 {} bei X {:+.0f}: Kopf und Inbus von oben frei ({})'.format(
            i + 1, X, a), d, 0.5)
    p.ok('M2x{:.0f}: reicht durch die Mutter'.format(kw('m2_l')),
         KL['m2_rest'], 0.0)
    p.ok('   ragt hinten aus der Wand', kw('m2_l') - KL['m2_stapel'], 2.0,
         '<=')
    rx = KL['rippe'][0]
    frei = min(abs(x - (rx[0] + rx[1]) / 2.0) - (rx[1] - rx[0]) / 2.0
               - KL['tasche_sw'] / math.sqrt(3.0)
               for x, _ in KL['loecher_schraube'])
    p.ok('Muttertasche neben der Rippe', frei, 1.0)

    # ------------------------------------------------------------------
    p.titel('8) Druck (Bambu Lab A1, PETG, Fuss aufs Bett)')
    bb = KL['teile']['Kamerahalter']['bbox']
    gr = [b[1] - b[0] for b in bb]
    p.ok('passt aufs Bett ({:.1f} x {:.1f} x {:.1f})'.format(*gr), max(gr),
         BETT, '<=')
    p.ok('Polster um das Loch (Wand)', (kw('pad_d') - kw('m2_durchgang'))
         / 2.0, 0.9)
    p.ok('Wand vor der Muttertasche', kw('wand_t') - (KL['tasche_y'][1]
                                                     - KL['tasche_y'][0]),
         1.5)
    p.ok('Fuss: Dicke', kw('fuss_t'), 4.0)
    p.ja('Rippe mit 45 Grad (gleich lang und hoch)',
         abs(KL['rippe'][1][1][0] - KL['rippe'][1][0][0])
         == abs(KL['rippe'][1][2][1] - KL['rippe'][1][0][1]))
    p.ja('Polster und Zapfen als Traene mit der Spitze unten, Loecher mit '
         'der Spitze oben', all(
             (s['spitze'] < 0) == (s['art'] == 'dazu')
             for s in KL['plan']['Kamerahalter'] if s['form'] == 'tropfen'))
    v = volumen(km, KL) / 1000.0
    p.info('Volumen {:.1f} cm3 = {:.1f} g PETG (voll)'.format(v, v * PETG))

    # ------------------------------------------------------------------
    p.titel('9) Kabel zum Pi')
    if fach_hinten:
        p.ok('Weg (geschaetzt) mit {:.0f} mm Reserve'.format(KABEL_RESERVE),
             kw('kabel_l') - KL['kabel_weg'], KABEL_RESERVE)
        p.info('geschaetzter Weg', KL['kabel_weg'])
    else:
        # Kamerabuchse des Pi an der Maschine (Fach gedreht); als Untergrenze
        # der Weg in geraden Stuecken laengs X, Y und Z, ohne Umweg um den
        # Arbeitsbereich
        pb = fm.nach_maschine(kw('pi_buchse_x'), kw('pi_buchse_y'),
                              kw('pi_buchse_z'))
        ka = KL['kabel_aus_welt']
        weg = sum(abs(a_ - b_) for a_, b_ in zip(ka, pb))
        p.info('Pi-Kamerabuchse an der Maschine X {:+.0f} Y {:+.0f} Z {:+.0f}'
               .format(*pb))
        p.info('Weg mindestens (gerade Stuecke, ohne Umweg)', weg)
        p.ok('Kabel {:.0f} mm reicht bis zum Pi vorn (offen: Kamera vorn '
             'rechts, Halter neu)'.format(kw('kabel_l')),
             kw('kabel_l') - weg, KABEL_RESERVE)

    # ------------------------------------------------------------------
    p.titel('10) Statische Pruefung der Schluessel in Kamerahalter.py')
    quelle = open(KAMERAHALTER, encoding='utf-8').read()
    benutzt = set(re.findall(r"\bw\('([^']+)'\)", quelle))
    fehlt_m = sorted(benutzt - set(km.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(KL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(km.MASSE) - benutzt)
    if unbenutzt:
        p.info('nur fuer die Pruefung: ' + ', '.join(unbenutzt))

    p.titel('11) Validierungsbericht des Fusion-Skripts')
    try:
        zeilen = km.hinweise_bauen(KL, [])
        for zeile in zeilen:
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
        p.ok('Berichtszeilen hoechstens 74 Zeichen',
             max(len(z) for z in zeilen), 74, '<=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    p.titel('12) Stueckliste')
    for zeile in (
            'Druck (PETG): 1 Kamerahalter; Bohrlehre_Kamera (PLA) bei Bedarf',
            'Raspberry Pi Camera Module 3, Normalobjektiv (nicht Wide)',
            'Kamerakabel Standard-Mini (15 auf 22 Pole), {:.0f} mm'.format(
                kw('kabel_l')),
            '2 x M5x{:.0f} Zylinderkopf + 2 Hammermuttern M5 Nut 6'.format(
                kw('m5_l')),
            '2 x M2x{:.0f} Zylinderkopf + 2 Muttern M2'.format(kw('m2_l'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
