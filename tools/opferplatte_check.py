#!/usr/bin/env python3
"""Rechnerische Pruefung der Fuehrungsfuesse und der Opferplatte
(fusion/Opferplatte) — laeuft ohne Fusion.

Importiert Opferplatte.py, Portal.py, ToolheadZ.py, NotAus.py und
Elektronik.py mit gestubbtem adsk-Modul und prueft: Abgleich der
Rahmenmasse und des Arbeitsfelds, Lage und Hoehe der Platte, Werkstueck-
hoehe, dass Toolhead und Portal ueber den ganzen Weg ueber Platte und
Fuessen bleiben, Fuehrung, Anschlag und Einfuehrschraege, Freiraum zu
Not-Aus, Elektronik, Y-Motoren, Halter Y, Winkeln und Y-Kette, die
Verschraubung in der Nut, Werkzeugzugang und Druck. Gibt die Stueckliste
aus.

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
import notaus_check                                   # noqa: E402
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


def fuss_quader(ow, OL, s, e):
    """Ein Fuss als Quader (Rahmenkoordinaten wie Portal.py, Portal in der
    Mitte). Die Einfuehrschraege fehlt, die Bohrungen auch: fuer
    Kollisionen liegt das auf der sicheren Seite."""
    n = '{} {}'.format(s, e)
    x, Q = OL['fuss_x'][e], Quader
    q = [Q('Fuss {} Block'.format(n), *x, *OL['block_y'][s], *OL['fuss_z']),
         Q('Fuss {} Flansch'.format(n), *x, *OL['flansch_y'][s],
           *OL['flansch_z']),
         Q('Fuss {} Feder'.format(n), *x, *OL['feder_y'][s],
           *OL['feder_z'])]
    if OL['voll'][s]:
        q.append(Q('Fuss {} innen'.format(n), *x, *OL['innen_y'][s],
                   *OL['fuss_z']))
    else:
        q += [Q('Fuss {} Wand'.format(n), *x, *OL['wand_y'][s],
                *OL['fuss_z']),
              Q('Fuss {} Boden'.format(n), *x, *OL['boden_y'][s],
                OL['tisch_z'], OL['tisch_z'] + ow('boden_t'))]
    if e == 'links':
        q.append(Q('Fuss {} Anschlag'.format(n), *OL['anschlag_x'],
                   *OL['anschlag_y'][s], *OL['anschlag_z']))
    return q


def fuss_volumen(ow, OL, s, e):
    """Volumen eines Fusses (mm3): Quader minus Bohrungen und Schraege."""
    v = sum((q.x[1] - q.x[0]) * (q.y[1] - q.y[0]) * (q.z[1] - q.z[0])
            for q in fuss_quader(ow, OL, s, e))
    v -= 2 * math.pi * (ow('m5_durchgang') / 2.0) ** 2 * ow('flansch_t')
    if e == 'rechts':
        v -= ow('einfuehr') ** 2 / 2.0 * (OL['fuss_z'][1] - OL['fuss_z'][0])
    return v


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    ow, OL = om.w, om.lage()
    nm = bauraum.modul_laden(notaus_check.NOTAUS, 'notaus')
    nw, NL = nm.w, nm.lage()
    em = bauraum.modul_laden(elektronik_check.ELEKTRONIK, 'elektronik')
    ew, EL = em.w, em.lage()
    p = Pruefung()
    R = L['R']
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    FUESSE = {(s, e): fuss_quader(ow, OL, s, e)
              for s in om.SEITEN for e in om.ENDEN}
    alle_fuesse = [q for v in FUESSE.values() for q in v]
    platte = Quader('Opferplatte', *OL['platte_x'], *OL['platte_y'],
                    *OL['platte_z'], 'holz')
    unten = alle_fuesse + [platte]
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
    p.titel('3) Opferplatte: Lage')
    px, py, pz = OL['platte_x'], OL['platte_y'], OL['platte_z']
    for text, wert in (('links', feld['feld_x0'] - px[0]),
                       ('rechts', px[1] - feld['feld_x1']),
                       ('hinten', feld['feld_y0'] - py[0]),
                       ('vorn', py[1] - feld['feld_y1'])):
        p.ok('Platte deckt das Arbeitsfeld ({})'.format(text), wert, 5.0)
    p.ok('Platte mittig unter dem Feld (Y)',
         abs((py[0] + py[1]) - (feld['feld_y0'] + feld['feld_y1'])) / 2.0,
         0.05, '<=')
    p.ok('Oberflaeche = Unterkante der 2060 (bisher der Tisch)',
         abs(pz[1] - L['quer_z'][0]), 0.01, '<=')
    p.ok('Fuesse so hoch wie die Platte dick ist',
         abs(OL['fuss_h'] - ow('platte_dicke')), 0.01, '<=')
    p.info('Tisch jetzt bei Z (Maschine steht so viel hoeher)', OL['tisch_z'])
    p.ok('Platte steht rechts ueber das Gestell (zum Fassen)',
         OL['platte_ueber'], 15.0)
    p.ok('Platte links am Anschlag', abs(px[0] - OL['anschlag_x'][1]),
         0.01, '<=')
    p.ok('Platte zwischen den 2060 (vorn)',
         L['quer_y_vorn'][0] - py[1], ow('wand_t'))
    p.ok('Platte zwischen den 2060 (hinten)',
         py[0] - L['quer_y_hinten'][1], ow('wand_t'))
    p.info('Masse der Platte ({:.2f} g/cm3)'.format(SPANPLATTE),
           (px[1] - px[0]) * (py[1] - py[0]) * (pz[1] - pz[0]) * SPANPLATTE
           / 1e6, 'kg')

    # ------------------------------------------------------------------
    p.titel('4) Hoehen: Werkstueck, Fokus, Toolhead ueber der Platte')
    fest_unten = min(tw('traeger_z_unten'), TL['z_schiene_z0'])
    frei = fest_unten - top - SICHERHEIT
    p.ok('Werkstueckhoehe ueber der Platte (wie ToolheadZ.py, {:.0f} mm '
         'Sicherheit)'.format(SICHERHEIT), frei, tw('werkstueck_max'))
    p.info('   ToolheadZ.py rechnet mit (Bett {:.0f} mm [?])'.format(
        tw('bett_abstand')), TL['werkstueck_frei'])
    p.ok('Bett laut ToolheadZ.py [?, auf cm gerundet] <-> Plattenoberflaeche',
         abs(tw('bett_abstand') + top), 5.0, '<=')
    platte_tief = TL['zc_min'] + TL['schlitten_unten_rel']
    p.ok('Z ganz unten: Schlittenplatte ueber der Platte', platte_tief - top,
         ow('luft_bau'))
    laser_tief = (TL['zc_min'] + TL['laser_unten_rel']
                  - tw('laser_langloch_hub'))
    p.ok('Z ganz unten, Laser ganz unten im Langloch: ueber der Platte',
         laser_tief - top, ow('luft_bau'))
    p.info('Fokusfenster: Gehaeuseunterkante ueber der Platte, Z unten',
           TL['linse_tief'] + tw('bett_abstand') + top)
    p.info('   ... Z oben (Schaltpunkt)',
           TL['linse_hoch'] + tw('bett_abstand') + top)

    # ------------------------------------------------------------------
    p.titel('5) Toolhead und Portal ueber Platte und Fuessen (ganzer Weg, Z '
            'unten)')
    dys = [-L['y_weg_hinten'] + (L['y_weg_hinten'] + w('y_weg_vorn')) * i
           / (Y_SCHRITTE - 1.0) for i in range(Y_SCHRITTE)]
    xws = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)]
    best = (float('inf'),)
    for dy in dys:
        for xw in xws:
            th_ = ([auf(q.verschoben(0.0, xw), dy=dy) for q in feste_th]
                   + [auf(q.verschoben(TL['zc_min'], xw), dy=dy)
                      for q in bewegte_th])
            d = engste(th_, unten)
            if d[0] < best[0]:
                best = d + (xw, dy)
    p.ok('Toolhead <-> Platte und Fuesse ({} / {}, X {:+.0f}, Portal '
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
    p.ok('Portal <-> Platte und Fuesse ({} / {}, Portal {:+.0f})'.format(
        best[1], best[2], best[3]), best[0], ow('luft_bau'))
    innen_oben = max(q.z[1] for (s, e), v in FUESSE.items() for q in v
                     if q.y[1] <= L['quer_y_vorn'][0] + 0.01
                     and q.y[0] >= L['quer_y_hinten'][1] - 0.01)
    p.ok('Fuesse innen nicht hoeher als die Platte', innen_oben - top, 0.01,
         '<=')

    # ------------------------------------------------------------------
    p.titel('6) Freiraum: Not-Aus, Elektronik, Y-Motoren, Halter Y, Winkel, '
            'Y-Kette')
    fremd = [('Not-Aus', notaus_check.teile(nw, NL)),
             ('Elektronik', elektronik_check.elektronik_quader(ew, EL))]
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
        d = engste(alle_fuesse + [platte], liste)
        p.ok('Fuesse und Platte <-> {} ({} / {})'.format(text, d[1], d[2]),
             d[0], ow('luft_bau'))
    fach = portal_check.elektronikfach(w, L)
    d = engste(alle_fuesse, [fach])
    p.ok('Fuesse ausserhalb des Elektronikfachs ({})'.format(d[1]), d[0],
         0.0)

    # ------------------------------------------------------------------
    p.titel('7) Verschraubung: je Fuss 2 x M5 in Hammermuttern der unteren '
            'Seitennut')
    in_nut = OL['m5_schraube'] - ow('m5_scheibe_h') - ow('flansch_t')
    p.ok('M5x{:.0f} + Scheibe: Spitze vor dem Nutgrund'.format(
        OL['m5_schraube']), NUT_PLATZ - in_nut, 0.5)
    p.ok('   Gewinde im Nutstein',
         min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
    p.ok('M5 in der unteren Seitennut (10 mm ueber der Unterkante)',
         abs(OL['nut_seite_z'] - (L['quer_z'][0] + 10.0)), 0.01, '<=')
    sr = ow('m5_scheibe_d') / 2.0
    p.ok('Scheibe liegt ganz auf dem Flansch (oben)',
         OL['flansch_z'][1] - (OL['nut_seite_z'] + sr), 1.0)
    for e in om.ENDEN:
        mx = sorted(OL['m5_x'][e])
        p.ok('Hammermuttern {} nebeneinander (Abstand der M5)'.format(e),
             mx[1] - mx[0], HAMMERMUTTER_L + 1.0)
        rand = min(abs(x - L['quer_x'][i]) for x in mx for i in (0, 1))
        p.ok('Hammermutter {} ganz im Profil (vor dem Ende)'.format(e),
             rand - HAMMERMUTTER_L / 2.0, 1.0)
        p.ok('Scheibe {} ganz auf dem Flansch (X)'.format(e),
             min(min(abs(x - OL['fuss_x'][e][0]), abs(x - OL['fuss_x'][e][1]))
                 for x in mx) - sr, 1.0)
    p.ok('Feder schmaler als die Nutoeffnung (6,2)', 6.2 - ow('feder_b'),
         0.3)
    p.ok('Feder nicht tiefer als die Nut', (ow('nut_v_t') + ow('nut_t'))
         - ow('feder_t'), 0.5)
    # Inbus von aussen: vorn nach vorn, hinten nach hinten
    hindernisse = ([q for _, liste in fremd for q in liste]
                   + portal_check.quer_quader(w, L))
    for s in om.SEITEN:
        aus = OL['aus'][s]
        fy = OL['flansch_y'][s]
        y_kopf = (fy[1] if aus > 0 else fy[0]) + aus * (ow('m5_scheibe_h')
                                                         + ow('m5_kopf_h'))
        pkt = [(x, y_kopf, OL['nut_seite_z']) for e in om.ENDEN
               for x in OL['m5_x'][e]]
        laenge = min(bauraum.freier_korridor(pt, 'y', aus, INBUS / 2.0 + 1.0,
                                             hindernisse)[0] for pt in pkt)
        p.ok('Inbus an den M5 der Fuesse {} (von aussen)'.format(s),
             999.0 if laenge == float('inf') else laenge, WERKZEUG_LAENGE)

    # ------------------------------------------------------------------
    p.titel('8) Fuehrung, Anschlag, Einfuehrschraege')
    for s in om.SEITEN:
        g = OL['fuehrung_y'][s]
        kante = py[1] if s == 'vorn' else py[0]
        p.ok('Luft Platte <-> Fuehrung {}'.format(s), abs(g - kante),
             ow('platte_spiel') - 0.01)
        p.info('Innenteil {} {} mm breit: {}'.format(
            s, '{:.1f}'.format(OL['innen_y'][s][1] - OL['innen_y'][s][0]),
            'voll' if OL['voll'][s] else 'Boden + Fuehrungswand'))
        p.ok('Anschlag {} greift vor das Plattenende'.format(s),
             OL['anschlag_y'][s][1] - OL['anschlag_y'][s][0], 10.0)
    p.ok('Anschlag unter der Plattenoberflaeche',
         top - OL['anschlag_z'][1], 1.0)
    p.ok('Fuehrung links (hinter dem Anschlag)',
         OL['fuss_x']['links'][1] - OL['anschlag_x'][1], 30.0)
    p.ok('Fuehrung rechts (vor der Einfuehrschraege)',
         OL['fuss_x']['rechts'][1] - OL['fuss_x']['rechts'][0]
         - ow('einfuehr'), 30.0)
    p.ok('Einfuehrschraege', ow('einfuehr'), 3.0)
    p.info('Platte zwischen den Fuehrungen gefuehrt (Abstand links-rechts)',
           OL['fuss_x']['rechts'][0] - OL['fuss_x']['links'][1])

    # ------------------------------------------------------------------
    p.titel('9) Druck (Bambu Lab A1): Unterseite aufs Bett')
    gesamt = 0.0
    for (s, e), q in sorted(FUESSE.items()):
        bx = OL['fuss_x'][e][1] - OL['fuss_x'][e][0]
        yb = OL['fuss_bb_y'][s + '_' + e]
        by = yb[1] - yb[0]
        bz = OL['flansch_z'][1] - OL['flansch_z'][0]
        v = fuss_volumen(ow, OL, s, e) / 1000.0
        gesamt += v
        p.ok('Fuss {} {}: {:.0f} x {:.1f} x {:.0f} mm, {:.1f} cm3 ({:.0f} g '
             'voll)'.format(s, e, bx, by, bz, v, v * PETG),
             max(bx, by, bz), BETT, '<=')
    p.info('Fuesse zusammen', gesamt, 'cm3')
    p.info('Flansch, Wand, Anschlag senkrecht; Feder oben; M5 waagerecht')

    # ------------------------------------------------------------------
    p.titel('10) Statische Pruefung der Schluessel in Opferplatte.py')
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

    p.titel('11) Validierungsbericht des Fusion-Skripts')
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

    p.titel('12) Stueckliste')
    for zeile in (
            'Druck (PETG): Fuss_vorn_links, Fuss_vorn_rechts, '
            'Fuss_hinten_links, Fuss_hinten_rechts',
            '8 x M5x{:.0f} + 8 Scheiben M5 + 8 Hammermuttern M5 (Nut 6), '
            'untere Seitennut aussen an den 2060'.format(OL['m5_schraube']),
            'Opferplatte: Spanplatte {:.0f} x {:.0f} x {:.1f} mm '
            '(vorhanden)'.format(ow('platte_l'), ow('platte_b'),
                                 ow('platte_dicke'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
