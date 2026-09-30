#!/usr/bin/env python3
"""Rechnerische Pruefung des Not-Aus-Gehaeuses (fusion/NotAus) — laeuft ohne
Fusion.

Importiert NotAus.py, Portal.py, ToolheadZ.py und YMotorhalter.py mit
gestubbtem adsk-Modul und prueft: Abgleich der Bezugsmasse, Lage vor dem
vorderen 2060, Freiraum zum rechten Y-Motorhalter samt Motor, zu den
Winkeln und zum Tisch, dass nichts, was faehrt, vor das 2060 kommt, die
Verschraubung in der Nut, den Taster im Gehaeuse, Kabeldurchlass und Druck.
Gibt die Stueckliste aus.

    python3 tools/notaus_check.py

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

HIER = os.path.dirname(os.path.abspath(__file__))
NOTAUS = os.path.join(HIER, '..', 'fusion', 'NotAus', 'NotAus.py')
YMOTOR = os.path.join(HIER, '..', 'fusion', 'YMotorhalter', 'YMotorhalter.py')
WINKEL = 20.0          # Winkel an den Kreuzungen 2040/2060 [v] Angabe
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
NUT_PLATZ = 6.0        # so weit darf eine Schraube in die Nut (YMotorhalter)
NUT_LIPPE, NUTSTEIN = 1.8, 4.0     # Hammermutter Nut 6 [w]
INBUS = 4.0            # M5-Zylinderkopf: Inbus SW 4
X_SCHRITTE, Z_SCHRITTE = 41, 9


def auf(q, dx=0.0, dy=0.0, dz=0.0):
    return Quader(q.name, q.x[0] + dx, q.x[1] + dx, q.y[0] + dy,
                  q.y[1] + dy, q.z[0] + dz, q.z[1] + dz, q.art)


def engste(a_liste, b_liste):
    best = (float('inf'), None, None)
    for a in a_liste:
        for b in b_liste:
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def teile(nw, NL):
    """Gehaeuse, Laschen, Rippen und Taster als Quader (fest am Rahmen)."""
    Q = Quader
    x, zm = NL['schalter']
    r = nw('schalter_kopf_d') / 2.0
    q = [Q('Gehaeuse', *NL['geh_x'], *NL['geh_y'], *NL['geh_z']),
         Q('Taster Pilzkopf', x - r, x + r, *NL['kopf_y'], zm - r, zm + r)]
    for i, lx in enumerate(NL['lasche_x']):
        q.append(Q('Lasche {}'.format(i + 1), *lx, NL['lasche_y'][0],
                   NL['lasche_y'][1] + nw('lasche_b'), *NL['lasche_z']))
    return q


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    nm = bauraum.modul_laden(NOTAUS, 'notaus')
    nw, NL = nm.w, nm.lage()
    ym = bauraum.modul_laden(YMOTOR, 'ymotorhalter')
    yw, YL = ym.w, ym.lage()
    p = Pruefung()
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, _, _ = portal_check.y_weg(w, L, TL, feste, bewegte)
    R = NL['R']
    T = teile(nw, NL)

    # ------------------------------------------------------------------
    p.titel('1) Abgleich NotAus.py <-> Portal.py / YMotorhalter.py')
    fl = yw('motor_flansch')
    for text, ist, soll in (
            ('Y-Schienen Mitte (R)', R, L['R']),
            ('Rahmen: vordere Stirnseite der 2040', nw('rahmen_y1'),
             L['rahmen_y'][1]),
            ('Rahmen: Unterkante der 2040', nw('rahmen_z0'), L['rahmen_z0']),
            ('vorderes 2060: Rueckseite', NL['quer_y'][0],
             L['quer_y_vorn'][0]),
            ('vorderes 2060: Vorderseite', NL['quer_y'][1],
             L['quer_y_vorn'][1]),
            ('vorderes 2060: Unterkante (Tisch)', NL['quer_z'][0],
             L['quer_z'][0]),
            ('vorderes 2060: Oberkante', NL['quer_z'][1], L['quer_z'][1]),
            ('Y-Motorhalter: halbe Breite', nw('ymh_halbe_b'),
             YL['halbe_breite']),
            ('Y-Motorhalter: Schenkel hinten', nw('ymh_y0'), YL['wange_y0']),
            ('Y-Motorhalter: Platte vorn', nw('ymh_y1'), YL['platte_y1']),
            ('Y-Motorhalter: unten', nw('ymh_z0'), YL['halter_z0']),
            ('Y-Motorhalter: oben', nw('ymh_z1'), YL['halter_z1']),
            ('NEMA 17: Flansch', nw('motor_b'), fl),
            ('Motorachse ganz innen', nw('motor_y_min'), YL['motor_y_min']),
            ('Motorachse ganz aussen', nw('motor_y_max'), YL['motor_y_max']),
            ('Motor unten', nw('motor_z0'), YL['motor_z0']),
            ('Motorflansch', nw('motor_z1'), YL['platte_z0'])):
        p.ok(text, abs(ist - soll), 0.02, '<=')

    # ------------------------------------------------------------------
    p.titel('2) Lage vor dem vorderen 2060')
    p.ok('Gehaeuse liegt an der Vorderseite des 2060',
         abs(NL['geh_y'][0] - L['quer_y_vorn'][1]), 0.01, '<=')
    p.ok('M5 in der mittleren Nut vorn', abs(NL['m5'][0][1]
                                            - (L['quer_z'][0] + 30.0)),
         0.01, '<=')
    p.ok('Gehaeuse ueber dem Tisch', NL['geh_z'][0] - L['quer_z'][0],
         nw('luft_bau') - 0.01)
    p.ok('Gehaeuse unter der Oberkante des 2060 (Winkel oben frei)',
         L['quer_z'][1] - NL['geh_z'][1], nw('luft_bau') - 0.01)
    kopf_unten = NL['schalter'][1] - nw('schalter_kopf_d') / 2.0
    p.info('Pilzkopf: Unterkante ueber dem Tisch',
           kopf_unten - L['quer_z'][0])
    p.info('Pilzkopf: vorn vor der Stirnseite der 2040',
           NL['kopf_y'][1] - L['rahmen_y'][1])

    # ------------------------------------------------------------------
    p.titel('3) Freiraum: Y-Motorhalter rechts, Winkel, alles was faehrt')
    ys, zs = L['rahmen_y'][1], L['rahmen_z0']
    halter = Quader('Y-Motorhalter rechts', R - YL['halbe_breite'],
                    R + YL['halbe_breite'], ys + YL['wange_y0'],
                    ys + YL['platte_y1'], zs + YL['halter_z0'],
                    zs + YL['halter_z1'])
    motor = Quader('Y-Motor rechts', R - fl / 2.0, R + fl / 2.0,
                   ys + YL['motor_y_min'] - fl / 2.0,
                   ys + YL['motor_y_max'] + fl / 2.0, zs + YL['motor_z0'],
                   zs + YL['platte_z0'])
    d = engste(T, [halter, motor])
    p.ok('Gehaeuse <-> Y-Motorhalter und Motor ({} / {})'.format(d[1],
                                                                d[2]),
         d[0], nw('luft_bau'))
    qy = L['quer_y_vorn']
    winkel = []
    for s in (-1, 1):
        for innen in (False, True):
            xa = s * (R + (-1 if innen else 1) * 10.0)
            xb = xa + s * (-WINKEL if innen else WINKEL)
            winkel.append(Quader('Winkel {}{}'.format(
                'rechts' if s > 0 else 'links', ' innen' if innen else ''),
                min(xa, xb), max(xa, xb), qy[0], qy[1], L['rahmen_z0'],
                L['rahmen_z0'] + WINKEL))
    d = engste(T, winkel)
    p.ok('Gehaeuse <-> Winkel an der Kreuzung ({})'.format(d[2]), d[0],
         nw('luft_bau'))
    # Portal und Toolhead am vorderen Ende des Y-Wegs, ueber X- und Z-Weg
    lang = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    portal = [auf(q, dy=d_vorn) for q in bauraum.portal_bauraeume(w, L)[0]
              if not q.name.startswith(lang)]
    d = engste(T, portal)
    p.ok('Gehaeuse <-> Portal am vorderen Wegende ({})'.format(d[2]), d[0],
         nw('luft_bau'))
    xws = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)]
    zcs = [TL['zc_min'] + (TL['zc_max'] - TL['zc_min']) * j
           / (Z_SCHRITTE - 1.0) for j in range(Z_SCHRITTE)]
    best = (float('inf'),)
    for xw in xws:
        fest = [auf(q.verschoben(0.0, xw), dy=d_vorn) for q in feste]
        for zc in zcs:
            th_ = fest + [auf(q.verschoben(zc, xw), dy=d_vorn)
                          for q in bewegte]
            d = engste(T, th_)
            if d[0] < best[0]:
                best = d + (xw, zc)
    p.ok('Gehaeuse <-> Toolhead am vorderen Wegende ({}, X {:+.0f}, Z '
         '{:+.0f})'.format(best[2], best[3], best[4]), best[0],
         nw('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('4) Verschraubung: 2 x M5 in Hammermuttern der mittleren Nut')
    in_nut = NL['m5_schraube'] - nw('m5_scheibe_h') - nw('lasche_t')
    p.ok('M5x{:.0f} + Scheibe: Spitze vor dem Nutgrund'.format(
        NL['m5_schraube']), NUT_PLATZ - in_nut, 0.5)
    p.ok('   Gewinde im Nutstein',
         min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
    sr = nw('m5_scheibe_d') / 2.0
    p.ok('Scheibe liegt ganz auf der Lasche (X)',
         nw('lasche_b') / 2.0 - sr, 1.0)
    p.ok('Scheibe zwischen den Rippen (Z)',
         (nw('lasche_h') / 2.0 - nw('rippe_d')) - sr, 1.0)
    p.ok('Inbus von vorn zwischen den Rippen',
         (nw('lasche_h') / 2.0 - nw('rippe_d')) - INBUS / 2.0, 3.0)
    p.ok('Hammermuttern nebeneinander (Abstand der M5)',
         NL['m5'][1][0] - NL['m5'][0][0], 11.0)

    # ------------------------------------------------------------------
    p.titel('5) Taster im Gehaeuse [?]')
    p.info('Loch fuer das Gewinde (Ø{:.0f} [?] + {:.1f})'.format(
        nw('schalter_d'), nw('schalter_spiel')), NL['loch_d'])
    p.ok('Frontwand nicht dicker als der Klemmbereich [?]', nw('na_front'),
         nw('klemm_max'), '<=')
    p.ok('Tiefe: Taster + Platz fuer die Litze an den Loetfahnen',
         NL['innen_y'][1] - NL['innen_y'][0],
         nw('schalter_tiefe') + nw('draht_biegen'))
    innen = min(NL['innen_x'][1] - NL['innen_x'][0],
                NL['innen_z'][1] - NL['innen_z'][0])
    p.ok('Mutter dreht sich innen (ueber Eck + 2 x 2 mm)', innen,
         nw('schalter_mutter') + 4.0)
    for d_ in (16.0, 19.0, 22.0):
        p.ok('   passt auch fuer {:.0f} mm (Mutter ~{:.0f} ueber Eck)'.format(
            d_, 1.45 * d_), innen, 1.45 * d_ + 4.0)
    p.ok('Pilzkopf ueber dem Tisch', kopf_unten - L['quer_z'][0], 5.0)
    ky, kz = NL['kabel']
    p.ok('Kabeldurchlass unter der Decke (Steg)', (NL['innen_z'][1]
                                                   - (kz + nw('kabel_d')
                                                      / 2.0)), 1.0)
    p.ok('Kabeldurchlass vor den Laschen und Rippen (Z)',
         (kz - nw('kabel_d') / 2.0) - NL['lasche_z'][1], 2.0)
    p.ok('Schlitze fuer den Kabelbinder in der Wand',
         min(b[0] for b in NL['binder']) - NL['geh_y'][0], 2.0)
    p.ok('   ... und hinter der Frontwand',
         NL['front_y'][0] - max(b[2] for b in NL['binder']), 5.0)

    # ------------------------------------------------------------------
    p.titel('6) Druck (Bambu Lab A1): Frontwand aufs Bett')
    bx = NL['lasche_x'][1][1] - NL['lasche_x'][0][0]
    by = NL['geh_y'][1] - NL['geh_y'][0]
    bz = NL['geh_z'][1] - NL['geh_z'][0]
    p.ok('Gehaeuse: {:.0f} x {:.0f} x {:.0f} mm passt aufs Bett'.format(
        bx, bz, by), max(bx, by, bz), BETT, '<=')
    abweichung = max(abs((yb - ya) / abs(aussen - wand) - 1.0)
                     for (wand, ya), (aussen, _), (_, yb) in NL['rippen'])
    p.ok('Rippen unter den Laschen: 45 Grad (druckt ohne Stuetzen)',
         abweichung, 0.01, '<=')
    p.ok('Bruecke unter der Lasche zwischen den Rippen',
         nw('lasche_h') - 2.0 * nw('rippe_d'), 20.0, '<=')
    p.ok('Kabeldurchlass waagerecht: ohne Tropfenform bis Ø8',
         nw('kabel_d'), 8.0, '<=')
    p.info('Rueckseite offen, Waende senkrecht: keine Decke ueber dem Kasten')

    # ------------------------------------------------------------------
    p.titel('7) Statische Pruefung der Schluessel in NotAus.py')
    quelle = open(NOTAUS, encoding='utf-8').read()
    benutzt = set(re.findall(r"\bw\('([^']+)'\)", quelle))
    fehlt_m = sorted(benutzt - set(nm.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(NL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(nm.MASSE) - benutzt)
    if unbenutzt:
        p.info('nur fuer die Pruefung: ' + ', '.join(unbenutzt))

    p.titel('8) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in nm.hinweise_bauen(NL, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    p.titel('9) Stueckliste')
    for zeile in (
            'Druck (PETG, gelb wenn vorhanden): Gehaeuse_NotAus',
            'Not-Aus-Pilztaster, Wechsler C/NO/NC (vorhanden)',
            '2 x M5x{:.0f} + 2 Scheiben M5 + 2 Hammermuttern M5 (Nut 6), '
            'mittlere Nut vorn am 2060'.format(NL['m5_schraube']),
            '1 Kabelbinder 2,5 mm (Zugentlastung)'):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
