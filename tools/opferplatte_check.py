#!/usr/bin/env python3
"""Rechnerische Pruefung der Halter und der Opferplatte
(fusion/Opferplatte) — laeuft ohne Fusion.

Importiert Opferplatte.py, Portal.py, ToolheadZ.py und
Elektronikfach.py mit gestubbtem adsk-Modul und prueft: Abgleich der
Rahmenmasse und des Arbeitsfelds, Lage und Hoehe der Platte (Maschine und
Platte auf demselben Tisch), Werkstueckhoehe und Softlimit Z, dass
Toolhead und Portal ueber den ganzen Weg ueber Platte und Haltern
bleiben, Fuehrung, Anschlag, Einfuehrschraege und Endplatte, den Riegel
(Ueberdeckung, freie Bahn, Auflage zu und offen, Schwenkkreis, Schraube,
Festigkeit), Freiraum zu Elektronikfach (mit Not-Aus), Y-Motoren, Halter
Y, Winkeln und Y-Kette, die Verschraubung in der inneren Seitennut,
Werkzeugzugang und Druck. Gibt die Stueckliste aus.

    python3 tools/opferplatte_check.py

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
OPFERPLATTE = os.path.join(HIER, '..', 'fusion', 'Opferplatte',
                           'Opferplatte.py')
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
NUT_PLATZ = 6.0        # so weit darf eine Schraube in die Nut (Y-Motorhalter)
NUT_LIPPE, NUTSTEIN = 1.8, 4.0     # Hammermutter Nut 6 [w]
HAMMERMUTTER_L = 10.5  # Hammermutter M5 Nut 6, Laenge [w]
INBUS = 4.0            # M5-Zylinderkopf: Inbus SW 4
WERKZEUG_LAENGE = 20.0  # kuerzester nutzbarer Inbus-Schenkel
WINKEL = 20.0          # Winkel an den Kreuzungen 2040/2060 [v] Angabe
SICHERHEIT = 5.0       # Werkstueckhoehe: Abstand unter dem Toolhead (wie
                       # werkstueck_frei in ToolheadZ.py)
SPANPLATTE = 0.65      # g/cm3
PETG = 1.27
X_SCHRITTE, Y_SCHRITTE = 41, 25
F_STOSS = 100.0        # N: kraeftiger Stoss von Hand gegen die Platte
SIGMA_SCHICHT = 15.0   # MPa: PETG in der Schichtebene (~45), Sicherheit 3
SIGMA_QUER = 8.0       # MPa: PETG quer zu den Schichten (~25), Sicherheit 3
PRESSUNG = 10.0        # MPa: Flaechenpressung PETG unter Kopf und Scheibe


def engste(a_liste, b_liste):
    best = (float('inf'), None, None)
    for a in a_liste:
        for b in b_liste:
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def auf(q, dx=0.0, dy=0.0, dz=0.0):
    return Quader(q.name, q.x[0] + dx, q.x[1] + dx, q.y[0] + dy,
                  q.y[1] + dy, q.z[0] + dz, q.z[1] + dz, q.art)


def halter_quader(ow, OL, s, e):
    """Ein Halter als Quader (Rahmenkoordinaten wie Portal.py, Portal in
    der Mitte). Die Einfuehrschraege fehlt, die Bohrungen auch: fuer
    Kollisionen liegt das auf der sicheren Seite. Die Quader ueberlappen
    sich nicht, damit das Volumen stimmt."""
    n = '{} {}'.format(s, e)
    x, Q, tz = OL['halter_x'][e], Quader, OL['tisch_z']
    if OL['voll'][s]:
        q = [Q('Halter {} Block'.format(n), *x, *OL['innen_y'][s],
               *OL['halter_z'])]
    else:
        q = [Q('Halter {} Wand'.format(n), *x, *OL['wand_y'][s],
               *OL['halter_z']),
             Q('Halter {} Boden'.format(n), *x, *OL['boden_y'][s],
               tz, tz + ow('boden_t')),
             Q('Halter {} Flansch'.format(n), *x, *OL['flansch_y'][s],
               *OL['flansch_z'])]
    if e == 'links':
        # liegt ganz vor der Fuehrung, Block und Wand beginnen dort
        q.append(Q('Halter {} Anschlag'.format(n), *OL['anschlag_x'],
                   *OL['anschlag_y'][s], *OL['anschlag_z']))
    if (s, e) == OL['riegel_an']:
        # Ausleger ab der Endplatte, Lagerbock ab der Oberseite des
        # Auslegers
        ep = OL['endplatte_x']
        q += [Q('Halter {} Endplatte'.format(n), *ep, *OL['endplatte_y'],
                *OL['endplatte_z']),
              Q('Halter {} Ausleger'.format(n), ep[1], OL['ausleger_x'][1],
                *OL['ausleger_y'], *OL['ausleger_z']),
              Q('Halter {} Lagerbock'.format(n), *OL['lager_x'],
                *OL['lager_y'], OL['ausleger_z'][1], OL['lager_z'][1])]
    return q


def halter_volumen(ow, OL, s, e):
    """Volumen eines Halters (mm3): Quader minus Bohrungen, Senkungen und
    Schraege."""
    v = sum((q.x[1] - q.x[0]) * (q.y[1] - q.y[0]) * (q.z[1] - q.z[0])
            for q in halter_quader(ow, OL, s, e))
    loch = math.pi * (ow('m5_durchgang') / 2.0) ** 2
    if OL['voll'][s]:
        b = OL['innen_y'][s][1] - OL['innen_y'][s][0]
        st = abs(OL['fuehrung_y'][s] - OL['auflage_y'][s])
        v -= 2 * (loch * b + math.pi / 4.0 * (ow('senk_d') ** 2
                                              - ow('m5_durchgang') ** 2) * st)
    else:
        v -= 2 * loch * ow('flansch_t')
    if e == 'rechts':
        h = (OL['endplatte_z'][1] - OL['endplatte_z'][0]
             if (s, e) == OL['riegel_an']
             else OL['halter_z'][1] - OL['halter_z'][0])
        v -= ow('einfuehr') ** 2 / 2.0 * h
    if (s, e) == OL['riegel_an']:
        v -= loch * ow('lager_t')
    return v


def riegel_masse(ow, OL):
    """Halbe Hoehe, Laenge Achse-Nase und Radius des Schwenkkreises (mm)."""
    rh = ow('riegel_h') / 2.0
    rl = OL['riegel_l']
    return rh, rl, math.hypot(rl, rh)


def riegel_quader(ow, OL):
    """Riegel zu, offen und sein Schwenkbereich (er klappt ueber oben),
    dazu Scheibe, Stoppmutter und Schraubenende hinter dem Lagerbock."""
    (yp, zp), rx = OL['riegel_achse'], OL['riegel_x']
    rh, rl, rs = riegel_masse(ow, OL)
    rs_ = ow('m5_scheibe_d') / 2.0
    x_ende = OL['lager_x'][1] + ow('m5_scheibe_h') + ow('m5_mutter_h') + \
        riegel_ueberstand(ow, OL)
    Q = Quader
    return {'zu': Q('Riegel zu', *rx, OL['riegel_nase_y'], yp + rh,
                    *OL['riegel_z']),
            'offen': Q('Riegel offen', *rx, yp - rh, yp + rl,
                       *OL['riegel_z']),
            'schwenk': Q('Riegel, Schwenkbereich', *rx, yp - rs, yp + rs,
                         zp - rh, zp + rs),
            'mutter': Q('Riegel: Scheibe, Stoppmutter', OL['lager_x'][1],
                        x_ende, yp - rs_, yp + rs_, zp - rs_, zp + rs_)}


def riegel_ueberstand(ow, OL):
    """So weit steht die Schraube ueber die Stoppmutter (mm)."""
    unter_kopf = ow('riegel_dicke') - OL['riegel_tasche_t']
    return (OL['riegel_schraube'] - unter_kopf - ow('lager_t')
            - ow('m5_scheibe_h') - ow('m5_mutter_h'))


def riegel_neigung(ow, OL):
    """Winkel (rad), um den die Nase des geschlossenen Riegels sinkt, bis
    seine Unterseite auf der hinteren Kante des Auslegers liegt (im Modell
    steht er waagerecht, riegel_luft ueber dem Ausleger)."""
    yp, zp = OL['riegel_achse']
    rh = ow('riegel_h') / 2.0
    d = yp - OL['ausleger_y'][0]            # Kante hinter der Achse
    soll = OL['ausleger_z'][1] - zp         # Oberseite Ausleger, relativ
    lo, hi = 0.0, math.pi / 4.0
    for _ in range(60):
        t = (lo + hi) / 2.0
        # Punkt der Unterseite ueber der Kante (gedreht um t, Nase runter)
        dy = (-d - rh * math.sin(t)) / math.cos(t)
        if dy * math.sin(t) - rh * math.cos(t) > soll:
            lo = t
        else:
            hi = t
    return (lo + hi) / 2.0


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    ow, OL = om.w, om.lage()
    em = bauraum.modul_laden(elektronik_check.ELEKTRONIK, 'elektronik')
    ew, EL = em.w, em.lage()
    p = Pruefung()
    R = L['R']
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    HALTER = {(s, e): halter_quader(ow, OL, s, e)
              for s in om.SEITEN for e in om.ENDEN}
    alle_halter = [q for v in HALTER.values() for q in v]
    RQ = riegel_quader(ow, OL)
    riegel = [RQ['schwenk'], RQ['mutter']]
    platte = Quader('Opferplatte', *OL['platte_x'], *OL['platte_y'],
                    *OL['platte_z'], 'holz')
    unten = alle_halter + riegel + [platte]
    top = OL['platte_z'][1]

    # ------------------------------------------------------------------
    p.titel('1) Abgleich Opferplatte.py <-> Portal.py (Rahmen)')
    for text, ist, soll in (
            ('Y-Schienen Mitte (R)', OL['R'], R),
            ('Profilbreite', ow('rahmen_b'), w('rahmen_b')),
            ('2040: hintere Stirnseite', OL['rahmen_y'][0], L['rahmen_y'][0]),
            ('2040: vordere Stirnseite', OL['rahmen_y'][1], L['rahmen_y'][1]),
            ('2040: Unterkante', OL['rahmen_z'][0], L['rahmen_z0']),
            ('2040: Oberkante', OL['rahmen_z'][1],
             L['rahmen_z0'] + w('rahmen_h')),
            ('2060: links', OL['quer_x'][0], L['quer_x'][0]),
            ('2060: rechts', OL['quer_x'][1], L['quer_x'][1]),
            ('2060: Unterkante', OL['quer_z'][0], L['quer_z'][0]),
            ('2060: Oberkante', OL['quer_z'][1], L['quer_z'][1]),
            ('vorderes 2060: innen', OL['quer_y']['vorn'][0],
             L['quer_y_vorn'][0]),
            ('vorderes 2060: aussen', OL['quer_y']['vorn'][1],
             L['quer_y_vorn'][1]),
            ('hinteres 2060: aussen', OL['quer_y']['hinten'][0],
             L['quer_y_hinten'][0]),
            ('hinteres 2060: innen', OL['quer_y']['hinten'][1],
             L['quer_y_hinten'][1])):
        p.ok(text, abs(ist - soll), 0.02, '<=')

    # ------------------------------------------------------------------
    p.titel('2) Arbeitsfeld (Strahl) aus Portal.py und ToolheadZ.py')
    # Der Laser sitzt mittig auf dem Toolhead: Strahl in X = X-Wagenmitte.
    # Y: Strahlachse plus Y-Weg des Portals (hinten Schienenende, vorn mit
    # Z unten 3 mm vor dem 2060; portal_check.py Abschnitt 14).
    feld = {'feld_x0': L['xw_min'], 'feld_x1': L['xw_max'],
            'feld_y0': TL['strahl_y'] - L['y_weg_hinten'],
            'feld_y1': TL['strahl_y'] + w('y_weg_vorn')}
    for k, soll in feld.items():
        p.ok('{} wie in Portal.py/ToolheadZ.py ({:+.2f})'.format(k, soll),
             abs(ow(k) - soll), 0.05, '<=')
    p.info('Arbeitsfeld X', feld['feld_x1'] - feld['feld_x0'])
    p.info('Arbeitsfeld Y', feld['feld_y1'] - feld['feld_y0'])

    # ------------------------------------------------------------------
    p.titel('3) Opferplatte: Lage (Maschine und Platte auf demselben Tisch)')
    px, py, pz = OL['platte_x'], OL['platte_y'], OL['platte_z']
    for text, wert in (('links', feld['feld_x0'] - px[0]),
                       ('rechts', px[1] - feld['feld_x1']),
                       ('hinten', feld['feld_y0'] - py[0]),
                       ('vorn', py[1] - feld['feld_y1'])):
        p.ok('Platte deckt das Arbeitsfeld ({})'.format(text), wert, 5.0)
    p.ok('Platte mittig unter dem Feld (Y)',
         abs((py[0] + py[1]) - (feld['feld_y0'] + feld['feld_y1'])) / 2.0,
         0.05, '<=')
    p.ok('Platte liegt auf dem Tisch = Unterkante der 2060',
         abs(pz[0] - L['quer_z'][0]), 0.01, '<=')
    p.ok('Oberflaeche = Unterkante der 2060 + gemessene Dicke',
         abs(pz[1] - (L['quer_z'][0] + ow('platte_dicke'))), 0.01, '<=')
    p.ok('Platte steht rechts ueber das Gestell (zum Fassen)',
         OL['platte_ueber'], 15.0)
    p.ok('Platte links am Anschlag', abs(px[0] - OL['anschlag_x'][1]),
         0.01, '<=')
    p.ok('Platte zwischen den 2060 (vorn)',
         L['quer_y_vorn'][0] - py[1], ow('wand_t'))
    p.ok('Platte zwischen den 2060 (hinten)',
         py[0] - L['quer_y_hinten'][1], ow('wand_t'))
    p.ok('Platte unter den 2040 durch (Unterkante 2040 ueber der Platte)',
         L['rahmen_z0'] - top, ow('luft_bau'))
    p.info('Masse der Platte ({:.2f} g/cm3)'.format(SPANPLATTE),
           (px[1] - px[0]) * (py[1] - py[0]) * (pz[1] - pz[0]) * SPANPLATTE
           / 1e6, 'kg')

    # ------------------------------------------------------------------
    p.titel('4) Hoehen: Werkstueck, Fokus, Softlimit Z ueber der Platte')
    fest_unten = min(tw('traeger_z_unten'), TL['z_schiene_z0'])
    frei = fest_unten - top - SICHERHEIT
    p.ok('Werkstueckhoehe ueber der Platte (wie ToolheadZ.py, {:.0f} mm '
         'Sicherheit)'.format(SICHERHEIT), frei, tw('werkstueck_max'))
    p.info('   ToolheadZ.py rechnet mit', TL['werkstueck_frei'])
    p.ok('Bett laut ToolheadZ.py = Plattenoberflaeche',
         abs(tw('bett_abstand') + top), 0.05, '<=')
    platte_tief = TL['zc_unten'] + TL['schlitten_unten_rel']
    p.ok('Z unten (Softlimit): Schlittenplatte ueber der Platte',
         platte_tief - top, ow('luft_bau'))
    laser_tief = (TL['zc_unten'] + TL['laser_unten_rel']
                  - tw('laser_langloch_hub'))
    p.ok('Z unten (Softlimit), Laser ganz unten im Langloch: ueber der '
         'Platte', laser_tief - top, ow('luft_bau'))
    p.info('Z mechanisch ganz unten: Schlittenplatte ueber der Platte '
           '(negativ: nur das Softlimit schuetzt)',
           TL['zc_min'] + TL['schlitten_unten_rel'] - top)
    # $132 wie tools/verkabelung.py: Arbeitsweg minus 1 mm Rueckzug und
    # 2 mm Reserve, abgerundet. MPos 0 liegt 1 mm unter dem Schaltpunkt.
    s132 = math.floor(TL['z_arbeit'] - 1.0 - 2.0)
    zc_132 = TL['zc_arbeit_max'] - 1.0 - s132
    p.info('$132 (Z-Weg ab dem Schaltpunkt)', s132)
    p.ok('mit $132={:.0f}: Schlittenplatte bei MPos Z -{:.0f} ueber der '
         'Platte'.format(s132, s132),
         zc_132 + TL['schlitten_unten_rel'] - top, tw('bett_luft'))
    p.info('Fokusfenster: Gehaeuseunterkante ueber der Platte, Z unten',
           TL['linse_tief'] + tw('bett_abstand') + top)
    p.info('   ... Z oben (Schaltpunkt)',
           TL['linse_hoch'] + tw('bett_abstand') + top)

    # ------------------------------------------------------------------
    p.titel('5) Toolhead und Portal ueber Platte und Haltern (ganzer Weg, '
            'Z unten am Softlimit)')
    dys = [-L['y_weg_hinten'] + (L['y_weg_hinten'] + w('y_weg_vorn')) * i
           / (Y_SCHRITTE - 1.0) for i in range(Y_SCHRITTE)]
    xws = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)]
    best = (float('inf'),)
    for dy in dys:
        for xw in xws:
            th_ = ([auf(q.verschoben(0.0, xw), dy=dy) for q in feste_th]
                   + [auf(q.verschoben(TL['zc_unten'], xw), dy=dy)
                      for q in bewegte_th])
            d = engste(th_, unten)
            if d[0] < best[0]:
                best = d + (xw, dy)
    p.ok('Toolhead <-> Platte, Halter, Riegel ({} / {}, X {:+.0f}, Portal '
         '{:+.0f})'.format(best[1], best[2], best[3], best[4]), best[0],
         ow('luft_bau'))
    lang = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    portal = [q for q in bauraum.portal_bauraeume(w, L)[0]
              if not q.name.startswith(lang)]
    best = (float('inf'),)
    for dy in dys:
        d = engste([auf(q, dy=dy) for q in portal], unten)
        if d[0] < best[0]:
            best = d + (dy,)
    p.ok('Portal <-> Platte, Halter, Riegel ({} / {}, Portal {:+.0f})'.format(
        best[1], best[2], best[3]), best[0], ow('luft_bau'))
    innen_oben = max(q.z[1] for v in HALTER.values() for q in v)
    p.ok('Halter nicht hoeher als die Platte', innen_oben - top, 0.01, '<=')

    # ------------------------------------------------------------------
    p.titel('6) Freiraum: Gestell, Elektronikfach, Y-Motoren, Halter Y, '
            'Winkel, Y-Kette')
    # Die Halter liegen innen am 2060 an, die Endplatte vor seinem Ende:
    # beruehren ja, durchdringen nein
    gestell = portal_check.quer_quader(w, L) + [
        Quader('2040 ' + n, sx * R - 10.0, sx * R + 10.0, *L['rahmen_y'],
               L['rahmen_z0'], L['rahmen_z0'] + w('rahmen_h'))
        for sx, n in ((-1, 'links'), (1, 'rechts'))]
    d = engste(alle_halter + [platte], gestell)
    p.ok('Halter und Platte durchdringen das Gestell nicht ({} / {})'.format(
        d[1], d[2]), d[0], 0.0)
    for (s, e), v in sorted(HALTER.items()):
        anlage = min(abs(q.y[1] - OL['innen'][s]) if s == 'vorn'
                     else abs(q.y[0] - OL['innen'][s]) for q in v)
        p.ok('Halter {} {} liegt innen am 2060 an'.format(s, e), anlage,
             0.01, '<=')
    # Seit Elektronikfach Rev. 2 sitzt der Not-Aus in der Frontwand des
    # Fachs; ein eigenes Gehaeuse gibt es nicht mehr
    fremd = [('Elektronikfach', elektronik_check.elektronik_quader(ew, EL))]
    YL, fl = L['ymh'], w('motor_flansch')
    ys, zs = L['rahmen_y'][1], L['rahmen_z0']
    ym = []
    for sx, n in ((-1, 'links'), (1, 'rechts')):
        xm = sx * R
        ym += [Quader('Y-Motorhalter ' + n, xm - YL['halbe_breite'],
                      xm + YL['halbe_breite'], ys + YL['wange_y0'],
                      ys + YL['platte_y1'], zs + YL['halter_z0'],
                      zs + YL['halter_z1']),
               Quader('Y-Motor ' + n, xm - fl / 2.0, xm + fl / 2.0,
                      ys + YL['motor_y_min'] - fl / 2.0,
                      ys + YL['motor_y_max'] + fl / 2.0, zs + YL['motor_z0'],
                      zs + YL['platte_z0'])]
    fremd.append(('Y-Motorhalter und Motoren', ym))
    hz = (min(L['hy_boden_z'][0], L['hy_fuss_z'][0]),
          max(L['hy_boden_z'][1], L['hy_fuss_z'][1]))
    fremd.append(('Halter Y', [Quader('Halter Y', L['aussen_x'],
                                      max(L['hy_boden_x'][1],
                                          L['hy_fuss_x'][1]),
                                      *L['hy_y'], *hz)]))
    winkel = []
    for qn in ('quer_y_vorn', 'quer_y_hinten'):
        for sx in (-1, 1):
            for innen in (False, True):
                xa = sx * (R + (-1 if innen else 1) * 10.0)
                xb = xa + sx * (-WINKEL if innen else WINKEL)
                winkel.append(Quader('Winkel', min(xa, xb), max(xa, xb),
                                     *L[qn], L['rahmen_z0'],
                                     L['rahmen_z0'] + WINKEL))
    fremd.append(('Winkel an den Kreuzungen', winkel))
    fremd.append(('Wanne und Traeger der Y-Kette',
                  bauraum.y_kette_rahmen(w, L)[0]))
    for text, liste in fremd:
        d = engste(alle_halter + riegel + [platte], liste)
        p.ok('Halter, Riegel, Platte <-> {} ({} / {})'.format(
            text, d[1], d[2]), d[0], ow('luft_bau'))
    fach = portal_check.elektronikfach(w, L)
    d = engste(alle_halter, [fach])
    p.ok('Halter ausserhalb des Elektronikfachs ({})'.format(d[1]), d[0],
         0.0)
    # Riegel und Lagerbock gegen das Gestell (Endplatte und Ausleger liegen
    # am Ende des 2060 an)
    aussen = riegel + [q for q in HALTER[OL['riegel_an']]
                       if q.name.endswith('Lagerbock')]
    d = engste(aussen, gestell)
    p.ok('Riegel (Schwenkbereich), Lagerbock <-> Gestell ({} / {})'.format(
        d[1], d[2]), d[0], ow('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('7) Verschraubung: je Halter 2 x M5 in Hammermuttern der '
            'inneren unteren Seitennut')
    p.ok('M5 in der unteren Seitennut (10 mm ueber der Unterkante)',
         abs(OL['nut_seite_z'] - (L['quer_z'][0] + 10.0)), 0.01, '<=')
    sr = ow('m5_scheibe_d') / 2.0
    for s in om.SEITEN:
        ls = OL['m5_schraube'][s]
        in_nut = (ls - OL['unter_kopf'][s]
                  - (ow('m5_scheibe_h') if OL['m5_scheibe'][s] else 0.0))
        art = ('ohne Scheibe, versenkt' if not OL['m5_scheibe'][s]
               else '+ Scheibe')
        p.ok('{}: M5x{:.0f} {}: Spitze vor dem Nutgrund'.format(s, ls, art),
             NUT_PLATZ - in_nut, 0.5)
        p.ok('   Gewinde im Nutstein',
             min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
        p.ok('   Material unter dem Kopf', OL['unter_kopf'][s], 4.0)
        if OL['voll'][s]:
            tiefe = abs(OL['fuehrung_y'][s] - OL['auflage_y'][s])
            p.ok('   Kopf unter der Fuehrungsflaeche (Senkung {:.2f} mm)'
                 .format(tiefe), tiefe - ow('m5_kopf_h'), ow('senk_luft'))
            p.ok('   Senkung weiter als der Kopf (Ø{:.1f})'.format(
                ow('m5_kopf_d')), ow('senk_d') - ow('m5_kopf_d'), 1.0)
            p.ok('   Senkung ueber dem Tisch',
                 OL['nut_seite_z'] - ow('senk_d') / 2.0 - OL['tisch_z'], 2.0)
            rand = ow('senk_d') / 2.0
        else:
            p.ok('   Scheibe liegt ganz auf dem Flansch (oben)',
                 OL['flansch_z'][1] - (OL['nut_seite_z'] + sr), 1.0)
            rand = sr
        for e in om.ENDEN:
            mx = sorted(OL['m5_x'][e])
            p.ok('   {} {}: Senkung/Scheibe ganz im Halter (X)'.format(s, e),
                 min(min(abs(x - OL['halter_x'][e][0]),
                         abs(x - OL['halter_x'][e][1])) for x in mx) - rand,
                 1.0)
    for e in om.ENDEN:
        mx = sorted(OL['m5_x'][e])
        p.ok('Hammermuttern {} nebeneinander (Abstand der M5)'.format(e),
             mx[1] - mx[0], HAMMERMUTTER_L + 1.0)
        rand = min(abs(x - L['quer_x'][i]) for x in mx for i in (0, 1))
        p.ok('Hammermutter {} ganz im Profil (vor dem Ende)'.format(e),
             rand - HAMMERMUTTER_L / 2.0, 1.0)
    # Inbus von der Plattenseite (ohne Platte montiert). Hinten steht die
    # eigene Fuehrungswand im Weg: so lang muss der kurze Schenkel passen.
    hindernisse = ([q for _, liste in fremd for q in liste]
                   + portal_check.quer_quader(w, L))
    for s in om.SEITEN:
        aus = OL['aus'][s]
        y_kopf = OL['auflage_y'][s] - aus * (
            ow('m5_kopf_h')
            + (ow('m5_scheibe_h') if OL['m5_scheibe'][s] else 0.0))
        eigene = [q for e in om.ENDEN for q in HALTER[(s, e)]
                  if q.name.endswith('Wand')]
        pkt = [(x, y_kopf, OL['nut_seite_z']) for e in om.ENDEN
               for x in OL['m5_x'][e]]
        laenge = min(bauraum.freier_korridor(pt, 'y', -aus, INBUS / 2.0 + 1.0,
                                             hindernisse + eigene)[0]
                     for pt in pkt)
        p.ok('Inbus an den M5 der Halter {} (von der Plattenseite)'.format(s),
             999.0 if laenge == float('inf') else laenge, WERKZEUG_LAENGE)
    p.info('Gegen einen Stoss nach links halten die Anschlaege nur durch die '
           'Klemmung der M5 (Reibung): je Schraube {:.0f} N noetig'.format(
               F_STOSS / (2 * 0.3)))

    # ------------------------------------------------------------------
    p.titel('8) Fuehrung, Anschlag, Einfuehrschraege, Endplatte')
    for s in om.SEITEN:
        g = OL['fuehrung_y'][s]
        kante = py[1] if s == 'vorn' else py[0]
        p.ok('Luft Platte <-> Fuehrung {}'.format(s), abs(g - kante),
             ow('platte_spiel') - 0.01)
        p.info('Halter {} {} mm breit: {}'.format(
            s, '{:.2f}'.format(OL['innen_y'][s][1] - OL['innen_y'][s][0]),
            'voller Block' if OL['voll'][s] else 'Flansch, Boden, Wand'))
        p.ok('Anschlag {} greift vor das Plattenende'.format(s),
             OL['anschlag_y'][s][1] - OL['anschlag_y'][s][0], 10.0)
        p.ok('Fuehrung rechts {} (vor der Einfuehrschraege)'.format(s),
             OL['fuehrung_ende_x'][s] - OL['halter_x']['rechts'][0]
             - ow('einfuehr'), 30.0)
    p.ok('Anschlag unter der Plattenoberflaeche',
         top - OL['anschlag_z'][1], 1.0)
    p.ok('Fuehrung links (hinter dem Anschlag)',
         OL['halter_x']['links'][1] - OL['anschlag_x'][1], 30.0)
    p.ok('Einfuehrschraege', ow('einfuehr'), 3.0)
    p.ok('Endplatte liegt am Ende des vorderen 2060',
         abs(OL['endplatte_x'][0] - L['quer_x'][1]), 0.01, '<=')
    p.ok('Endplatte deckt das Profilende (Y)',
         OL['endplatte_y'][1] - L['quer_y_vorn'][1], 0.0)
    p.ok('Endplatte in der Flucht der Fuehrung',
         abs(OL['endplatte_y'][0] - OL['fuehrung_y']['vorn']), 0.01, '<=')
    p.ok('Endplatte unter der Plattenoberflaeche',
         top - OL['endplatte_z'][1], 1.0)
    p.info('Platte zwischen den Fuehrungen gefuehrt (Abstand links-rechts)',
           OL['halter_x']['rechts'][0] - OL['halter_x']['links'][1])

    # ------------------------------------------------------------------
    p.titel('9) Riegel vorn rechts: klappt um eine M5 laengs X')
    (yp, zp), rx = OL['riegel_achse'], OL['riegel_x']
    rh, rl, rs = riegel_masse(ow, OL)
    nase = OL['riegel_nase_y']
    p.ok('Riegel greift vor das Plattenende (Platte hinten an der '
         'Fuehrung)', py[1] - ow('platte_spiel') - nase, 10.0)
    p.ok('Riegel deckt das Plattenende in der Hoehe', ow('riegel_h'), 10.0)
    p.ok('Luft Plattenende <-> Riegel (X)', rx[0] - px[1], 0.5)
    p.ok('Riegel rechts der Endplatte', rx[0] - OL['endplatte_x'][1], 5.0)
    p.info('   Platz zwischen Anschlag und Riegel = laengste Platte',
           rx[0] - OL['anschlag_x'][1])
    p.ok('Riegel unter der Plattenoberflaeche', top - OL['riegel_z'][1], 1.0)
    t = riegel_neigung(ow, OL)
    p.info('Riegel zu: Nase sinkt, bis er auf der Kante des Auslegers liegt',
           math.degrees(t), 'Grad')
    p.ok('   Nase dann noch ueber dem Tisch',
         zp - rl * math.sin(t) - rh * math.cos(t) - OL['tisch_z'], 2.0)
    p.ok('Riegel zu: Auflage auf dem Ausleger hinter der Achse',
         yp - OL['ausleger_y'][0], 5.0)
    p.ok('Riegel offen: liegt ganz auf dem Ausleger (Y)',
         OL['ausleger_y'][1] - (yp + rl), 0.5)
    p.ok('Nabe dreht frei ueber dem Ausleger', ow('riegel_luft'), 0.3)
    p.info('Schwenkkreis (klappt ueber oben, Gestell siehe 6): Radius', rs)
    g = OL['fuehrung_y']['vorn']
    for text, y0 in (('Ausleger', OL['ausleger_y'][0]),
                     ('Lagerbock', OL['lager_y'][0]),
                     ('Riegel offen', RQ['offen'].y[0]),
                     ('Scheibe und Stoppmutter', RQ['mutter'].y[0])):
        p.ok('Bahn der Platte frei: {} vor der Fuehrung'.format(text),
             y0 - g, 1.5)
    p.info('Stoss gegen die Platte (+X) wirkt parallel zur Achse: kein '
           'Moment, das ihn aufklappt')
    kontakt = (nase + py[1]) / 2.0          # Mitte der Auflage am Plattenende
    hebel = OL['lager_y'][0] - kontakt      # ab der Kante des Lagerbocks
    p.ok('Nase biegt sich bei {:.0f} N Stoss (in der Schichtebene)'.format(
        F_STOSS), F_STOSS * hebel / (ow('riegel_h') * ow('riegel_dicke') ** 2
                                     / 6.0), SIGMA_SCHICHT, '<=', 'MPa')
    p.ok('Lagerbock biegt sich am Ausleger (quer zu den Schichten)',
         F_STOSS * (zp - OL['ausleger_z'][1])
         / (ow('lager_b') * ow('lager_t') ** 2 / 6.0), SIGMA_QUER, '<=',
         'MPa')
    yb = (min(OL['ausleger_y'][1], OL['endplatte_y'][1])
          - max(OL['ausleger_y'][0], OL['endplatte_y'][0]))
    ta = ow('ausleger_t')
    p.ok('Ausleger an der Endplatte: Biegung und Zug (in der Schichtebene)',
         F_STOSS * (zp - OL['tisch_z'] - ta / 2.0) / (yb * ta ** 2 / 6.0)
         + F_STOSS / (yb * ta), SIGMA_SCHICHT, '<=', 'MPa')
    # Hals: Endplatte am Block, Schnitt am Ende des 2060. Der Stoss greift
    # in Y versetzt (an der Nase) und in Z ueber der Mitte an.
    hb = OL['innen_y']['vorn'][1] - OL['innen_y']['vorn'][0]
    hh = OL['endplatte_z'][1] - OL['endplatte_z'][0]
    hebel_y = abs(sum(OL['innen_y']['vorn']) / 2.0 - kontakt)
    hebel_z = abs(zp - (OL['tisch_z'] + hh / 2.0))
    p.ok('Endplatte am Block (Schnitt am Ende des 2060): Zug und Biegung',
         F_STOSS / (hb * hh) + F_STOSS * hebel_y / (hh * hb ** 2 / 6.0)
         + F_STOSS * hebel_z / (hb * hh ** 2 / 6.0), SIGMA_SCHICHT, '<=',
         'MPa')
    zug = F_STOSS * hebel / (yp - OL['lager_y'][0])
    p.info('Schraube: Zug, wenn der Riegel um die Kante des Lagerbocks '
           'kippt', zug, 'N')
    loch = math.pi * (ow('m5_durchgang') / 2.0) ** 2
    p.ok('   Pressung unter dem Sechskantkopf',
         zug / (math.sqrt(3.0) / 2.0 * ow('m5_sw') ** 2 - loch), PRESSUNG,
         '<=', 'MPa')
    p.ok('Schraube M5x{:.0f}: Ueberstand ueber die Stoppmutter'.format(
        OL['riegel_schraube']), riegel_ueberstand(ow, OL), ow('ueberstand'))
    p.ok('   Kopf in der Tasche unter der Flaeche zur Platte',
         OL['riegel_tasche_t'] - ow('m5_sk_k'), 0.3)
    p.ok('   Boden unter dem Kopf', ow('riegel_dicke') - OL['riegel_tasche_t'],
         4.0)
    p.ok('   Wand zwischen Tasche (Ecken) und Nabe',
         rh - OL['riegel_tasche_sw'] / math.sqrt(3.0), 2.0)
    p.ok('   Tasche: Zugabe auf SW {:.0f}'.format(ow('m5_sw')),
         OL['riegel_tasche_sw'] - ow('m5_sw'), 0.2)
    sr = ow('m5_scheibe_d') / 2.0
    p.ok('Scheibe ganz auf dem Lagerbock (Y)', ow('lager_b') / 2.0 - sr, 1.0)
    p.ok('   (oben)', ow('lager_ueber') - sr, 1.0)
    p.ok('Stoppmutter (Ecke) ueber dem Ausleger',
         zp - ow('m5_sw') / math.sqrt(3.0) - OL['ausleger_z'][1], 1.0)
    pt = ((RQ['mutter'].x[0] + RQ['mutter'].x[1]) / 2.0, yp, zp)
    laenge = bauraum.freier_korridor(pt, 'x', 1.0, 10.0, hindernisse)[0]
    p.ok('Maulschluessel SW {:.0f} an der Stoppmutter (von rechts)'.format(
        ow('m5_sw')), 999.0 if laenge == float('inf') else laenge, 40.0)

    # ------------------------------------------------------------------
    p.titel('10) Druck (Bambu Lab A1)')
    gesamt = 0.0
    for (s, e), q in sorted(HALTER.items()):
        n = om.halter_name(s, e)
        xb, yb = OL['halter_bb_x'][n], OL['halter_bb_y'][n]
        bx, by = xb[1] - xb[0], yb[1] - yb[0]
        bz = OL['halter_z'][1] - OL['halter_z'][0]
        v = halter_volumen(ow, OL, s, e) / 1000.0
        gesamt += v
        p.ok('{}: {:.0f} x {:.1f} x {:.1f} mm, {:.1f} cm3 ({:.0f} g voll)'
             .format(n, bx, by, bz, v, v * PETG), max(bx, by, bz), BETT,
             '<=')
    p.info('Halter: Unterseite aufs Bett. Block, Flansch, Wand, Anschlag, '
           'Endplatte und Lagerbock senkrecht; M5 und Senkungen waagerecht')
    sw_a = math.sqrt(3.0) / 2.0 * OL['riegel_tasche_sw'] ** 2
    d_r, tt = ow('riegel_dicke'), OL['riegel_tasche_t']
    v = (rl * 2.0 * rh * d_r + math.pi * rh ** 2 / 2.0 * d_r - sw_a * tt
         - loch * (d_r - tt)) / 1000.0
    gesamt += v
    p.ok('Riegel: {:.0f} x {:.1f} x {:.0f} mm, {:.1f} cm3 ({:.0f} g voll)'
         .format(d_r, rl + rh, 2.0 * rh, v, v * PETG),
         max(d_r, rl + rh, 2.0 * rh), BETT, '<=')
    p.info('Riegel: Seite ohne Tasche aufs Bett, Bohrung senkrecht')
    p.info('Druckteile zusammen', gesamt, 'cm3')

    # ------------------------------------------------------------------
    p.titel('11) Statische Pruefung der Schluessel in Opferplatte.py')
    quelle = open(OPFERPLATTE, encoding='utf-8').read()
    benutzt = set(re.findall(r"\bw\('([^']+)'\)", quelle))
    fehlt_m = sorted(benutzt - set(om.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(OL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(om.MASSE) - benutzt)
    if unbenutzt:
        p.info('nur fuer die Pruefung: ' + ', '.join(unbenutzt))

    p.titel('12) Validierungsbericht des Fusion-Skripts')
    try:
        zeilen = om.hinweise_bauen(OL, [])
        for zeile in zeilen:
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
        p.ok('Berichtszeilen hoechstens 74 Zeichen',
             max(len(z) for z in zeilen), 74, '<=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    p.titel('13) Stueckliste')
    for zeile in (
            'Druck (PETG): Anschlag_vorn, Anschlag_hinten, Fuehrung_vorn '
            '(mit Endplatte, Ausleger und Lagerbock), Fuehrung_hinten, Riegel',
            '4 x M5x{:.0f} Zylinderkopf ohne Scheibe (vorn, versenkt) + 4 x '
            'M5x{:.0f} + 4 Scheiben M5 (hinten)'.format(
                OL['m5_schraube']['vorn'], OL['m5_schraube']['hinten']),
            '8 Hammermuttern M5 (Nut 6) in der unteren Seitennut INNEN an den '
            '2060, je 2 nahe jedem Ende',
            '1 x Sechskantschraube M5x{:.0f} (ISO 4017) + 1 Scheibe M5 + 1 '
            'Stoppmutter M5 (DIN 985): Achse des Riegels'.format(
                OL['riegel_schraube']),
            'Opferplatte: Spanplatte {:.0f} x {:.0f} x {:.1f} mm '
            '(vorhanden)'.format(ow('platte_l'), ow('platte_b'),
                                 ow('platte_dicke'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
