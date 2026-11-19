#!/usr/bin/env python3
"""Rechnerische Pruefung des Kamerahalters (fusion/Kamerahalter, Rev. 2) —
laeuft ohne Fusion.

Seit Rev. 2 sitzt die Kamera vorn rechts auf dem vorderen 2060, vor dem
Elektronikfach, geneigt zum Messpunkt kurz innerhalb der Anschlagecke vorn
rechts. Importiert Kamerahalter.py, ToolheadZ.py, Portal.py, Opferplatte.py,
Spannmittel.py und Elektronikfach.py mit gestubbtem adsk-Modul und prueft:
Abgleich der Masse, Lage auf dem 2060, Freiraum zu allem, was Toolhead und
Portal ueber den ganzen Weg ueberstreichen, zu Fach und Deckel, 2060, 2040,
Y-Riemen und Y-Motor, Kamera auf dem Halter, Sicht zum Messpunkt fuer jede
Werkstueckdicke (frei, im Bild, scharf), Schrauben mit Werkzeugzugang, Druck
und Kabel. Gibt die Stueckliste aus.

Die Teile stehen im Halter gedreht; Abstaende und Sichtlinien rechnen mit
ihren echten Ecken (Spat), nicht mit dem umschreibenden Quader.

    python3 tools/kamerahalter_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
import spannmittel_check as smc                       # noqa: E402
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
UNSCHAERFE_MAX = 6.0   # Pixel Zerstreuungskreis: Punktmitte bleibt genau
LUFT_FACH = 1.0        # Deckel geht ab, nichts liegt an
LUFT_2040 = 2.0        # zum rechten 2040
UEBERHANG_MAX = 45.0   # Grad aus der Senkrechten, ohne Stuetzen
SCHRITTE = 600         # Stuetzpunkte je Sichtlinie
LINSE_2040 = (30.0, 80.0)   # Linse so weit vom rechten 2040 (Angabe)


def quader_aus(name, punkte):
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    zs = [p[2] for p in punkte]
    return Quader(name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


class Teil(object):
    """Gedrehter Quader des Halters: Spat aus den 8 Ecken von
    ecken_quader() (Reihenfolge x, y, z). Abstand und Enthalten exakt."""

    def __init__(self, name, ecken, achsparallel=False):
        self.name = name
        self.q = quader_aus(name, ecken)
        self.o = ecken[0]
        if achsparallel:
            self.e = None
        else:
            self.e = [tuple(ecken[i][k] - ecken[0][k] for k in range(3))
                      for i in (4, 2, 1)]

    def punkt(self, u, v, t):
        return tuple(self.o[k] + u * self.e[0][k] + v * self.e[1][k]
                     + t * self.e[2][k] for k in range(3))

    def abstand(self, q):
        """Kleinster Abstand zum achsparallelen Quader q. Die Entfernung ist
        im Spat konvex: geschachtelte Dreiteilung ist exakt genug."""
        grob = self.q.abstand(q)
        if self.e is None or grob > 20.0:
            return grob

        def d(u, v, t):
            p = self.punkt(u, v, t)
            return math.sqrt(sum(max(lo - p[k], 0.0, p[k] - hi) ** 2
                                 for k, (lo, hi) in enumerate(
                                     (q.x, q.y, q.z))))

        def minimum(f):
            a, b = 0.0, 1.0
            for _ in range(28):
                m1, m2 = a + (b - a) / 3.0, b - (b - a) / 3.0
                if f(m1) <= f(m2):
                    b = m2
                else:
                    a = m1
            return f((a + b) / 2.0)
        return minimum(lambda u: minimum(lambda v: minimum(
            lambda t: d(u, v, t))))

    def enthaelt(self, p):
        if self.e is None:
            q = self.q
            return (q.x[0] < p[0] < q.x[1] and q.y[0] < p[1] < q.y[1]
                    and q.z[0] < p[2] < q.z[1])
        r = [p[k] - self.o[k] for k in range(3)]
        a, b, c = self.e
        det = (a[0] * (b[1] * c[2] - b[2] * c[1])
               - a[1] * (b[0] * c[2] - b[2] * c[0])
               + a[2] * (b[0] * c[1] - b[1] * c[0]))

        def ersetzt(i):
            m = [list(a), list(b), list(c)]
            m[i] = r
            x, y, z = m
            return (x[0] * (y[1] * z[2] - y[2] * z[1])
                    - x[1] * (y[0] * z[2] - y[2] * z[0])
                    + x[2] * (y[0] * z[1] - y[1] * z[0])) / det
        return all(0.0 < ersetzt(i) < 1.0 for i in range(3))


def engste(teile, andere):
    """Engstes Paar. Der Quaderabstand ist eine untere Schranke: genau
    gerechnet wird nur, solange er unter dem bisher besten liegt."""
    paare = sorted(((a.q.abstand(b) if isinstance(a, Teil) else
                     a.abstand(b)), i, a, b)
                   for i, (a, b) in enumerate((a, b) for a in teile
                                              for b in andere))
    best = (float('inf'), None, None)
    for grob, _, a, b in paare:
        if grob >= best[0]:
            break
        d = a.abstand(b)
        if d < best[0]:
            best = (d, a.name, b.name)
    return best


def schneidet(p0, p1, q, ab=0.0):
    """Liegt ein Punkt der Strecke p0-p1 (ab dem Anteil `ab`) im Quader
    oder Teil?"""
    for i in range(1, SCHRITTE):
        s = i / float(SCHRITTE)
        if s < ab:
            continue
        p = tuple(p0[k] + (p1[k] - p0[k]) * s for k in range(3))
        if isinstance(q, Teil):
            if q.enthaelt(p):
                return True
        elif (q.x[0] < p[0] < q.x[1] and q.y[0] < p[1] < q.y[1]
                and q.z[0] < p[2] < q.z[1]):
            return True
    return False


def huelle(punkte):
    """Konvexe Huelle (X, Y) — Grundriss eines gedrehten Teils."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in punkte))

    def kreuz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    unten, oben = [], []
    for p in pts:
        while len(unten) >= 2 and kreuz(unten[-2], unten[-1], p) <= 0:
            unten.pop()
        unten.append(p)
    for p in reversed(pts):
        while len(oben) >= 2 and kreuz(oben[-2], oben[-1], p) <= 0:
            oben.pop()
        oben.append(p)
    return unten[:-1] + oben[:-1]


def abstand_vieleck(c, poly):
    """Abstand eines Punkts zu einem konvexen Vieleck (0 = drin)."""
    kanten = list(zip(poly, poly[1:] + poly[:1]))
    if all((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) >= 0
           for a, b in kanten):
        return 0.0
    best = float('inf')
    for (ax, ay), (bx, by) in kanten:
        dx, dy = bx - ax, by - ay
        ll = dx * dx + dy * dy
        t = 0.0 if ll == 0 else max(0.0, min(1.0, ((c[0] - ax) * dx
                                                   + (c[1] - ay) * dy) / ll))
        best = min(best, math.hypot(c[0] - ax - t * dx, c[1] - ay - t * dy))
    return best


def ueberstrichen(tw, TL, w, L):
    """Toolhead und Portal ueber den ganzen Weg: Quader + Weg. Nach vorn
    bis zum Softlimit (y_weg_vorn)."""
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


def stl_volumen(km):
    """Volumen (mm3) und Mass des Halters ueber tools/stl_export.py
    (manifold3d), oder None, wenn manifold3d fehlt."""
    try:
        import stl_export
        k, gr = stl_export.kamerahalter(km)
        return k.volume(), gr, len(k.decompose())
    except Exception:
        return None


def main():
    km = bauraum.modul_laden(KAMERAHALTER, 'kamerahalter')
    kw, KL = km.w, km.lage()
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    OL = om.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    sw, SL = sm.w, sm.lage()
    fm = bauraum.modul_laden(FACH, 'elektronikfach')
    FL = fm.lage()
    p = Pruefung()
    lx, ly, lz = KL['linse']
    teile = {n: Teil(n, ps, achsparallel=(n == 'Fuss'))
             for n, ps in KL['welt'].items()}
    kamera = [teile[n] for n in KL['kamera_teile']]
    halter = [teile[n] for n in list(KL['wand_teile']) + ['Steg', 'Fuss']]
    u = ueberstrichen(tw, TL, w, L)

    # ------------------------------------------------------------------
    p.titel('1) Abgleich mit Portal.py, Elektronikfach.py, Spannmittel.py, '
            'Opferplatte.py, ToolheadZ.py')
    fach_x, fach_y, fach_z = fm.bereich_nach_maschine(
        FL['geh_x'], FL['geh_y'], FL['geh_z'])
    pi = fm.nach_maschine(-10.5, -275.0, -73.0)
    riemen = next(q for q in bauraum.portal_bauraeume(w, L)[0]
                  if q.name == 'Y-Riemen rechts')
    laser = next(q for q in u if q.name == 'Toolhead Diodenlaser')
    schlitten = next(q for q in u if q.name == 'Toolhead Schlittenplatte')
    for text, ist, soll in (
            ('vorderes 2060: Innenseite', kw('quer_vorn_y0'),
             L['quer_y_vorn'][0]),
            ('vorderes 2060: Vorderseite', kw('quer_vorn_y1'),
             L['quer_y_vorn'][1]),
            ('Oberseite 2060', kw('rahmen_z0'), L['quer_z'][1]),
            ('Unterseite 2060', kw('rahmen_z0') - kw('quer_h'),
             L['quer_z'][0]),
            ('rechtes 2040: Innenseite', kw('rahmen_x_innen'),
             L['R'] - w('rahmen_b') / 2.0),
            ('Oberseite Opferplatte', kw('platte_z1'), OL['platte_z'][1]),
            ('Anschlag vorn rechts: Innenecke X', kw('ecke_x'),
             SL['aw_ecke_maschine'][0]),
            ('Anschlag vorn rechts: Innenecke Y', kw('ecke_y'),
             SL['aw_ecke_maschine'][1]),
            ('Fach: Montageplatte am 2060', kw('fach_y0'), fach_y[0]),
            ('Fach: halbe Breite', kw('fach_x1'), fach_x[1]),
            ('Fach: Oberkante der Waende', kw('fach_rand_z'), FL['rand_z']),
            ('Fach: Oberseite Deckel', kw('deckel_z1'), FL['deckel_z'][1]),
            ('Pi: Kamerabuchse im Modell X', kw('pi_buchse_x'), pi[0]),
            ('Pi: Kamerabuchse im Modell Y', kw('pi_buchse_y'), pi[1]),
            ('Pi: Kamerabuchse im Modell Z', kw('pi_buchse_z'), pi[2]),
            ('Laser: vorderste Lage (Softlimit)', kw('laser_vorn_y'),
             laser.y[1]),
            ('Laser: rechteste Lage', kw('laser_x1'), laser.x[1]),
            ('Schlittenplatte: vorderste Lage', kw('schlitten_vorn_y'),
             schlitten.y[1]),
            ('Y-Riemen rechts: Innenseite', kw('riemen_x0'), riemen.x[0]),
            ('Y-Riemen rechts: Unterkante', kw('riemen_z0'), riemen.z[0]),
            ('Eckwinkel 2040/2060: Schenkel', kw('winkel_l'),
             w('winkel_h'))):
        p.ok(text, abs(ist - soll), 0.15, '<=')

    # ------------------------------------------------------------------
    p.titel('2) Lage: Fuss auf der Oberseite des vorderen 2060, Kamera vorn '
            'rechts')
    fx, fy = KL['fuss_x'], KL['fuss_y']
    p.info('Fuss X {:+.1f} .. {:+.1f}, Y {:+.1f} .. {:+.1f}'.format(
        fx[0], fx[1], fy[0], fy[1]))
    p.ok('Fuss liegt auf dem 2060', abs(KL['fuss_z'][0] - L['quer_z'][1]),
         0.01, '<=')
    p.ok('Fuss ganz auf dem 2060 (innen)', fy[0] - L['quer_y_vorn'][0], 0.0)
    p.ok('Fuss ganz auf dem 2060 (aussen, Fach)', L['quer_y_vorn'][1] - fy[1],
         0.0)
    p.ok('Fuss neben dem rechten 2040', kw('rahmen_x_innen') - fx[1],
         LUFT_2040)
    p.info('Fuss endet unten bei X {:+.1f}, oben bei {:+.1f}: dort beginnt '
           'der 45-Grad-Schnitt ueber dem Eckwinkel'.format(
               KL['winkel_schnitt_x'], fx[1]))
    p.info('Linse X {:+.1f}, Y {:+.1f}, Z {:+.1f}; Blick {:.1f} Grad, '
           'Neigung {:.1f} Grad'.format(lx, ly, lz, KL['blick_az'],
                                        KL['neige']))
    d40 = kw('rahmen_x_innen') - lx
    p.ok('Linse {:.0f} mm vom rechten 2040 (an der Maschine 30 bis 80, '
         'Angabe)'.format(d40), d40, LINSE_2040[0] - 1.0)
    p.ok('   und nicht weiter weg', d40, LINSE_2040[1], '<=')
    steg = huelle(KL['welt']['Steg'])
    # rechts vom Fuss liegt der Steg ueber dem Eckwinkel: Dort ist er
    # unten unter 45 Grad weggeschnitten, genau in der Flucht der
    # Fussschraege; er haengt also nirgends waagerecht in der Luft.
    p.ok('Steg steht auf dem Fuss (rechts davon die 45-Grad-Schraege)', min(
        min(x - fx[0], y - fy[0], fy[1] - y) for x, y in steg), 0.0)
    xs_ = [x for x, _ in steg]
    ys_ = [y for _, y in steg]
    n_in = n_auf = 0
    for i in range(80):
        for j in range(80):
            x = min(xs_) + (max(xs_) - min(xs_)) * (i + 0.5) / 80.0
            y = min(ys_) + (max(ys_) - min(ys_)) * (j + 0.5) / 80.0
            if abstand_vieleck((x, y), steg) == 0.0:
                n_in += 1
                n_auf += x <= fx[1]
    flaeche = (max(xs_) - min(xs_)) * (max(ys_) - min(ys_)) / 6400.0
    p.ok('Steg: Flaeche ueber dem Fuss', n_auf * flaeche, 20.0, '>=',
         'mm2')
    p.info('   von {:.0f} mm2 Querschnitt'.format(n_in * flaeche))
    for i, (x, y) in enumerate(KL['m5_welt']):
        p.ok('M5 {} auf der Nutmitte (Y {:+.1f})'.format(i + 1, y),
             -abs(y - (L['quer_y_vorn'][0] + w('rahmen_b') / 2.0)), -0.01)
        rk = kw('m5_kopf_d') / 2.0
        p.ok('M5 {}: Kopf ganz auf dem Fuss'.format(i + 1),
             min(x - rk - fx[0], fx[1] - x - rk, y - rk - fy[0],
                 fy[1] - y - rk), 0.5)
        p.ok('M5 {}: Kopf neben dem Steg'.format(i + 1),
             abstand_vieleck((x, y), steg) - rk, 0.5)

    # ------------------------------------------------------------------
    p.titel('3) Freiraum zu Toolhead und Portal ueber den ganzen Weg')
    d, a, b = engste(kamera + halter, u)
    p.ok('Halter und Kamera <-> {} ({})'.format(b, a), d, kw('luft_bau'))
    p.info('Laser rechts bis X {:+.1f}, vorn bis Y {:+.1f}; die Kamera ragt '
           'nur rechts davon ueber das 2060'.format(laser.x[1], laser.y[1]))

    # ------------------------------------------------------------------
    p.titel('4) Freiraum zu Fach, Rahmen, Y-Riemen und Y-Motor')
    # Fach: Kasten und darueber frei, damit der Deckel abgeht
    fach_saeule = Quader('Fach und Raum ueber dem Deckel', *fach_x,
                         *fach_y, fach_z[0], 500.0)
    d, a, b = engste(kamera + halter, [fach_saeule])
    p.ok('Fach: frei, der Deckel geht ab ({})'.format(a), d, LUFT_FACH)
    q2060 = Quader('2060 vorn', *L['quer_x'], *L['quer_y_vorn'],
                   *L['quer_z'])
    d, a, b = engste(kamera + [x for x in halter if x.name != 'Fuss'],
                     [q2060])
    p.ok('ueber dem 2060 (nur der Fuss liegt auf; {})'.format(a), d, 0.0)
    q2040 = Quader('2040 rechts', kw('rahmen_x_innen'),
                   kw('rahmen_x_innen') + w('rahmen_b'), -400.0, 400.0,
                   kw('rahmen_z0'), kw('rahmen_z0') + 2.0 * w('rahmen_b'))
    d, a, b = engste(kamera + halter, [q2040])
    p.ok('neben dem rechten 2040 ({})'.format(a), d, LUFT_2040)
    d, a, b = engste(kamera + halter, [riemen])
    p.ok('Y-Riemen rechts ({})'.format(a), d, kw('luft_bau'))
    # Eckwinkel innen am rechten 2040 (Huelle: Dreieck unter der Schraege)
    (wx0, wx1), (wy0, wy1), (wz0, wz1) = KL['winkel']
    schraege = [min((pt[2] - wz0 - (pt[0] - wx0)) / math.sqrt(2.0)
                    for pt in KL['welt'][n])
                for n in list(KL['kamera_teile']) + list(KL['wand_teile'])]
    p.ok('Eckwinkel: Kamera und Wand ueber seiner Schraege',
         min(schraege), kw('winkel_luft'))
    v = stl_volumen(km)
    if v:
        import stl_export
        luft = kw('winkel_luft') - 0.05
        s2 = luft * math.sqrt(2.0)
        huelle_w = stl_export.prisma(
            'y', [(wx0 - s2, wz0), (wx1, wz0), (wx1, wz1 + s2)], wy0, wy1)
        T = KL['teile']['Kamerahalter']
        huelle_w = huelle_w.transform(KL['maschine_nach_h']).transform(
            T['druck'])
        stl_k = stl_export.kamerahalter(km)[0]
        schnitt_v = (stl_k ^ huelle_w).volume()
        p.ok('Eckwinkel: Fuss und Steg mindestens {:.2f} mm von der '
             'Schraege'.format(luft), schnitt_v, 0.0005, '<=', 'mm3')
    else:
        p.info('Eckwinkel: Fuss und Steg nicht geprueft (manifold3d fehlt)')
    yh = portal_check.y_halter_quader(w, L)
    d, a, b = engste(kamera + halter, yh)
    p.ok('Y-Motorhalter und Y-Motor ({} / {})'.format(a, b), d,
         kw('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('5) Kamera auf dem Halter (v1.3, Lochbild wie Module 2/3 [w])')
    p.ok('Platine liegt auf den Polstern', abs(KL['pad_y'][1]
                                               - KL['platine'][1][0]), 0.01,
         '<=')
    p.ok('Zapfen passt ins Loch (Spiel)', kw('cam_loch_d')
         - kw('zapfen_d') - 2.0 * kw('zapfen_kappe'), 0.2)
    p.ok('Zapfen ragt durch die Platine', KL['zapfen_y'][1]
         - KL['platine'][1][1], 0.3)
    wx, st = KL['wand'][0], KL['stecker'][0]
    frei = (wx[0] - st[1]) if KL['kabel_seite'] > 0 else (st[0] - wx[1])
    p.ok('Wand endet vor dem Stecker (Kabel geht hinten raus)', frei, 0.3)
    p.ok('M2x{:.0f}: Gewinde reicht durch die Mutter'.format(kw('m2_l')),
         KL['m2_rest'], 0.0)
    p.ok('   und steht hinten hoechstens 2 mm ueber', KL['m2_rest'], 2.0,
         '<=')
    p.ok('Muttertasche in der Wand', kw('wand_t') - (KL['tasche_y'][1]
                                                     - KL['tasche_y'][0]),
         1.5)

    # ------------------------------------------------------------------
    p.titel('6) Sicht zum Messpunkt ({:.0f} links, {:.0f} hinter der '
            'Innenecke vorn rechts)'.format(kw('mp_links'), kw('mp_hinten')))
    mx, my = KL['mp']
    p.info('Messpunkt X {:+.1f}, Y {:+.1f}'.format(mx, my))
    wst = smc.gedreht(Quader('Beispielwerkstueck', *SL['wst_x'],
                             *SL['wst_y'], *SL['wst_z']), SL)
    p.ok('Messpunkt liegt auf dem Beispielwerkstueck (Rand)', min(
        mx - wst.x[0], wst.x[1] - mx, my - wst.y[0], wst.y[1] - my), 10.0)
    p.ok('Messpunkt im Arbeitsfeld', min(
        mx - sw('feld_x0'), sw('feld_x1') - mx, my - sw('feld_y0'),
        sw('feld_y1') - my), 5.0)
    spann = (smc.anschlag_quader(SL)
             + [q for ex in SL['ex'] for q in smc.exzenter_quader(sw, SL, ex)]
             + [q for nh in SL['nh'] for q in smc.niederhalter_quader(nh, SL)])
    p.ok('Spannmittel frei vom Messpunkt (Lippe, Anschlag)', min(
        max(q.x[0] - mx, mx - q.x[1], q.y[0] - my, my - q.y[1])
        for q in spann), 5.0)
    th_mp = toolhead_am_messpunkt(tw, TL, L, KL)
    eigene = list(teile.values())
    hindernisse = th_mp + spann + [q2060, fach_saeule, q2040] + eigene
    for s_ in KL['sicht']:
        punkt = (mx, my, kw('platte_z1') + s_['t'])
        zu = [q.name for q in hindernisse
              if schneidet(KL['linse'], punkt, q, ab=0.02)]
        p.ja('t = {:.0f} mm: Sichtlinie frei'.format(s_['t']), not zu,
             ' — ' + ', '.join(zu) if zu else '')
        p.ok('   quer im Bild ({:+.1f} Grad)'.format(s_['quer']),
             KL['bild_halb'][0] - abs(s_['quer']), RAND_BILD, '>=', 'Grad')
        p.ok('   hoch im Bild ({:+.1f} Grad unter der Achse)'.format(
            s_['unter']), KL['bild_halb'][1] - abs(s_['unter']), RAND_BILD,
            '>=', 'Grad')
        p.ok('   {:.0f} mm weit, unscharf (Fokus {:.0f} mm)'.format(
            s_['abstand'], KL['fokus_auf']), s_['unschaerfe_px'],
            UNSCHAERFE_MAX, '<=', 'px')
    p.ok('Aufloesung: Pixel je mm Hoehe', KL['px_je_mm'], 10.0, '>=', 'px')

    # ------------------------------------------------------------------
    p.titel('7) Schrauben')
    p.ok('M5x{:.0f}: Gewinde in der Hammermutter'.format(kw('m5_l')),
         KL['m5_eingriff'], 3.5)
    p.ok('M5x{:.0f}: steht nicht auf dem Nutgrund auf'.format(kw('m5_l')),
         kw('nut_tiefe') - KL['m5_in_nut'], 0.3)
    r = kw('inbus_frei_d') / 2.0
    ueber = {n: huelle(ps) for n, ps in KL['welt'].items()
             if n not in ('Fuss',)}
    for i, (x, y) in enumerate(KL['m5_welt']):
        d_h = min(abstand_vieleck((x, y), ueber[n])
                  for n in list(KL['wand_teile']) + ['Steg'])
        d_k = min(abstand_vieleck((x, y), ueber[n])
                  for n in KL['kamera_teile'])
        p.ok('M5 {} (X {:+.0f}): Inbus von oben neben der Wand'.format(
            i + 1, x), d_h, r)
        p.ok('   ... auch mit eingesetzter Kamera', d_k, r)

    # ------------------------------------------------------------------
    p.titel('8) Druck (Bambu Lab A1, PETG, Fuss aufs Bett)')
    bb = KL['teile']['Kamerahalter']['bbox']
    gr = [b1 - b0 for b0, b1 in bb]
    p.ok('passt aufs Bett ({:.0f} x {:.0f} x {:.0f} mm)'.format(*gr),
         max(gr), BETT, '<=')
    p.ok('Wand lehnt hoechstens {:.0f} Grad (Kameraseite haengt so weit '
         'ueber)'.format(UEBERHANG_MAX), KL['neige'], UEBERHANG_MAX, '<=',
         'Grad')
    p.ok('Schnitt ueber dem Eckwinkel: Unterseite unter 45 Grad', 45.0,
         UEBERHANG_MAX, '<=', 'Grad')
    v = stl_volumen(km)
    if v:
        vol, groesse, n_teile = v
        p.info('Volumen {:.1f} cm3 = {:.1f} g PETG (voll)'.format(
            vol / 1000.0, vol / 1000.0 * PETG))
        p.ja('ein zusammenhaengender Koerper (Wand auf dem Steg)',
             n_teile == 1, '' if n_teile == 1 else ' — {} Teile'.format(
                 n_teile))
    else:
        p.info('Volumen: manifold3d fehlt (pip install manifold3d)')
    p.info('Polster und Zapfen stehen 2 bzw. 0,8 mm vor der geneigten '
           'Wand; so kurz drucken sie ohne Stuetzen')

    # ------------------------------------------------------------------
    p.titel('9) Kabel zum Pi')
    p.info('Austritt X {:+.1f}, Y {:+.1f}, Z {:+.1f} (Kabelkante zum Fach)'
           .format(*KL['kabel_aus_welt']))
    p.info('Weg zur Kamerabuchse im Modell (gerade Stuecke)', KL['kabel_weg'])
    p.info('Am Aufbau liegt der Pi anders als im Modell (Fach Zwischenstand);'
           ' dort reicht das {:.0f}-mm-Kabel laut Angabe'.format(
               kw('kabel_l')))

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
            'Druck (PETG): 1 Kamerahalter (Rev. {})'.format(km.REVISION),
            'Raspberry Pi Kamera v1.3 (verbaut; Camera Module 3 passt auch)',
            'Kamerakabel Standard-Mini (15 auf 22 Pole), {:.0f} mm'.format(
                kw('kabel_l')),
            '2x M5x{:.0f} Zylinderkopf + 2x Hammermutter M5 (Nut 6)'.format(
                kw('m5_l')),
            '2x M2x{:.0f} Zylinderkopf + 2x Mutter M2'.format(kw('m2_l'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
