#!/usr/bin/env python3
"""Rechnerische Pruefung der Anschlaege und der Opferplatte
(fusion/Opferplatte) — laeuft ohne Fusion.

Importiert Opferplatte.py, Portal.py, ToolheadZ.py und
Elektronikfach.py mit gestubbtem adsk-Modul und prueft: Abgleich des
Rahmens mit Portal.py (die neue Lage der 2060 kennt bisher nur
Opferplatte.py: das steht als offen im Bericht), Arbeitsfeld, Lage und
Hoehe der Platte (Maschine und Platte auf demselben Tisch, die 2060 ohne
Spalt an der Platte), Werkstueckhoehe und Softlimit Z, dass Toolhead und
Portal ueber den ganzen Weg ueber Platte und Anschlaegen bleiben, die
Anschlaege selbst (Nase, Endplatte an der Stirnseite, Festigkeit),
Freiraum zu Elektronikfach, Y-Motoren, Halter Y, Winkeln und Y-Kette,
die Verschraubung in der aeusseren Seitennut, Werkzeugzugang und Druck.
Gibt die Stueckliste aus.

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
PRESSUNG = 10.0        # MPa: Flaechenpressung PETG an der Stirnseite


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


def anschlag_quader(OL, s):
    """Ein Anschlag als Quader ohne Ueberlappung (das Volumen stimmt):
    Flansch aussen am 2060, Endplatte vor der Stirnseite, Nase in der Bahn
    der Platte. Die Bohrungen fehlen: fuer Kollisionen sicher."""
    Q = Quader
    return [Q('Anschlag {} Flansch'.format(s), *OL['flansch_x'][s],
              *OL['flansch_y'][s], *OL['flansch_z']),
            Q('Anschlag {} Endplatte'.format(s), *OL['endplatte_x'][s],
              *OL['endplatte_y'][s], *OL['anschlag_z']),
            Q('Anschlag {} Nase'.format(s), *OL['nase_x'][s],
              *OL['nase_y'][s], *OL['anschlag_z'])]


def anschlag_volumen(ow, OL, s):
    """Volumen eines Anschlags (mm3): Quader minus die beiden M5-Loecher."""
    v = sum((q.x[1] - q.x[0]) * (q.y[1] - q.y[0]) * (q.z[1] - q.z[0])
            for q in anschlag_quader(OL, s))
    return v - 2 * math.pi * (ow('m5_durchgang') / 2.0) ** 2 * ow('flansch_t')


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
    ANSCHLAG = {s: anschlag_quader(OL, s) for s in om.SEITEN}
    alle = [q for v in ANSCHLAG.values() for q in v]
    platte = Quader('Opferplatte', *OL['platte_x'], *OL['platte_y'],
                    *OL['platte_z'], 'holz')
    unten = alle + [platte]
    top = OL['platte_z'][1]
    px, py, pz = OL['platte_x'], OL['platte_y'], OL['platte_z']
    # Die 2060 in der Lage, die Opferplatte.py kennt (seit Rev. 5)
    quer = {s: Quader('2060 ' + s, *OL['quer_x'][s], *OL['quer_y'][s],
                      *OL['quer_z'], 'profil') for s in om.SEITEN}
    rahmen = list(quer.values()) + [
        Quader('2040 ' + n, sx * R - 10.0, sx * R + 10.0, *OL['rahmen_y'],
               *OL['rahmen_z'], 'profil')
        for sx, n in ((-1, 'links'), (1, 'rechts'))]

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
            ('2060: Unterkante', OL['quer_z'][0], L['quer_z'][0]),
            ('2060: Oberkante', OL['quer_z'][1], L['quer_z'][1]),
            ('2060: Laenge', ow('quer_laenge'),
             L['quer_x'][1] - L['quer_x'][0])):
        p.ok(text, abs(ist - soll), 0.02, '<=')
    # Die neue Lage der 2060 (Angabe 2026-11-21) steht nur hier. Bis
    # Portal.py sie kennt, ist das ein offener Punkt, kein Fehler.
    innen_portal = L['quer_y_vorn'][0] - L['quer_y_hinten'][1]
    innen = OL['quer_y']['vorn'][0] - OL['quer_y']['hinten'][1]
    p.info('OFFEN: 2060 innen auseinander, hier {:.0f} mm, Portal.py noch '
           '{:.0f} mm'.format(innen, innen_portal))
    for s, qn in (('vorn', 'quer_y_vorn'), ('hinten', 'quer_y_hinten')):
        p.info('OFFEN: {} 2060 Y {:+.2f}..{:+.2f}, in Portal.py '
               '{:+.2f}..{:+.2f}'.format(s, *OL['quer_y'][s], *L[qn]))
        p.info('OFFEN: {} 2060 linkes Ende X {:+.1f}, in Portal.py {:+.1f}'
               .format(s, OL['quer_ende'][s], L['quer_x'][0]))

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
    p.info('OFFEN: Y-Weg vorn mit Z unten ist in Portal.py gegen die alte '
           'Lage des vorderen 2060 gerechnet (hier {:.2f} mm weiter hinten)'
           .format(L['quer_y_vorn'][0] - OL['quer_y']['vorn'][0]))

    # ------------------------------------------------------------------
    p.titel('3) Opferplatte: Lage (auf dem Tisch, ohne Spalt zwischen den '
            '2060)')
    for text, wert in (('links', feld['feld_x0'] - px[0]),
                       ('rechts', px[1] - feld['feld_x1']),
                       ('hinten', feld['feld_y0'] - py[0]),
                       ('vorn', py[1] - feld['feld_y1'])):
        p.ok('Platte deckt das Arbeitsfeld ({})'.format(text), wert, 5.0)
    p.ok('Platte mittig unter dem Feld (Y)',
         abs((py[0] + py[1]) - (feld['feld_y0'] + feld['feld_y1'])) / 2.0,
         0.05, '<=')
    p.ok('Platte liegt auf dem Tisch = Unterkante der 2060',
         abs(pz[0] - OL['quer_z'][0]), 0.01, '<=')
    p.ok('Oberflaeche = Unterkante der 2060 + gemessene Dicke',
         abs(pz[1] - (OL['quer_z'][0] + ow('platte_dicke'))), 0.01, '<=')
    p.ok('vorderes 2060 liegt an der Platte an (kein Spalt)',
         abs(OL['quer_y']['vorn'][0] - py[1]), 0.01, '<=')
    p.ok('hinteres 2060 liegt an der Platte an (kein Spalt)',
         abs(py[0] - OL['quer_y']['hinten'][1]), 0.01, '<=')
    p.ok('Platte links an beiden Nasen',
         max(abs(px[0] - OL['nase_x'][s][1]) for s in om.SEITEN), 0.01, '<=')
    p.ok('Platte steht rechts ueber beide 2060 (zum Fassen)',
         OL['platte_ueber'], 10.0)
    p.ok('Platte unter den 2040 durch (Unterkante 2040 ueber der Platte)',
         OL['rahmen_z'][0] - top, ow('luft_bau'))
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
    p.titel('5) Toolhead und Portal ueber Platte und Anschlaegen (ganzer '
            'Weg, Z unten am Softlimit)')
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
    p.ok('Toolhead <-> Platte, Anschlaege ({} / {}, X {:+.0f}, Portal '
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
    p.ok('Portal <-> Platte, Anschlaege ({} / {}, Portal {:+.0f})'.format(
        best[1], best[2], best[3]), best[0], ow('luft_bau'))
    p.ok('Anschlaege nicht hoeher als die Platte',
         max(q.z[1] for q in alle) - top, 0.01, '<=')

    # ------------------------------------------------------------------
    p.titel('6) Freiraum: Rahmen, Elektronikfach, Y-Motoren, Halter Y, '
            'Winkel, Y-Kette')
    d = engste(alle + [platte], rahmen)
    p.ok('Anschlaege und Platte durchdringen den Rahmen nicht ({} / {})'
         .format(d[1], d[2]), d[0], 0.0)
    for s in om.SEITEN:
        p.ok('Anschlag {}: Endplatte liegt an der Stirnseite des 2060'
             .format(s), abs(OL['endplatte_x'][s][1] - OL['quer_ende'][s]),
             0.01, '<=')
        p.ok('Anschlag {}: Flansch liegt aussen am 2060'.format(s),
             abs(min(abs(y - OL['aussen'][s]) for y in OL['flansch_y'][s])),
             0.01, '<=')
        p.ok('Anschlag {}: nichts zwischen Platte und 2060'.format(s),
             min(abs(q.y[0] - OL['innen'][s]) if s == 'hinten'
                 else abs(q.y[1] - OL['innen'][s])
                 for q in ANSCHLAG[s] if q.name.endswith('Nase')), 0.01,
             '<=')
    # Fach, Motoren, Halter Y, Winkel und Kette rechnet Portal.py noch mit
    # der alten Lage der 2060. Fuer den Vergleich wandert jeder Anschlag mit
    # seinem 2060 dorthin: Was am 2060 sitzt (Fach), steht dann richtig zu
    # ihm; was am 2040 sitzt, um die Verschiebung daneben (Bericht).
    dyp = {'vorn': L['quer_y_vorn'][0] - OL['quer_y']['vorn'][0],
           'hinten': L['quer_y_hinten'][0] - OL['quer_y']['hinten'][0]}
    dxp = {s: L['quer_x'][0] - OL['quer_ende'][s] for s in om.SEITEN}
    im_portal = [auf(q, dx=dxp[s], dy=dyp[s]) for s in om.SEITEN
                 for q in ANSCHLAG[s]]
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
        d = engste(im_portal, liste)
        p.ok('Anschlaege <-> {} ({} / {})'.format(text, d[1], d[2]), d[0],
             ow('luft_bau'))
    p.info('   (verglichen in der alten Lage aus Portal.py: jeder Anschlag '
           'um {:+.2f} / {:+.2f} mm in Y mit seinem 2060 verschoben)'.format(
               dyp['vorn'], dyp['hinten']))
    fach = elektronik_check.elektronik_quader(ew, EL)
    fx = (min(q.x[0] for q in fach), max(q.x[1] for q in fach))
    p.ok('Flansch vorn neben dem Elektronikfach (beide vorn am 2060, X)',
         min(abs(OL['flansch_x']['vorn'][1] - fx[0]),
             abs(fx[1] - OL['flansch_x']['vorn'][0]))
         if (OL['flansch_x']['vorn'][1] <= fx[0]
             or OL['flansch_x']['vorn'][0] >= fx[1]) else -1.0,
         ow('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('7) Verschraubung: je Anschlag 2 x M5 in Hammermuttern der '
            'aeusseren unteren Seitennut')
    p.ok('M5 in der unteren Seitennut (10 mm ueber der Unterkante)',
         abs(OL['nut_seite_z'] - (OL['quer_z'][0] + 10.0)), 0.01, '<=')
    ls = OL['m5_schraube']
    in_nut = ls - ow('flansch_t') - ow('m5_scheibe_h')
    p.ok('M5x{:.0f} + Scheibe: Spitze vor dem Nutgrund'.format(ls),
         NUT_PLATZ - in_nut, 0.5)
    p.ok('   Gewinde im Nutstein',
         min(in_nut, NUT_LIPPE + NUTSTEIN) - NUT_LIPPE, 3.0)
    sr = ow('m5_scheibe_d') / 2.0
    p.ok('Scheibe liegt ganz auf dem Flansch (oben)',
         OL['flansch_z'][1] - (OL['nut_seite_z'] + sr), 1.0)
    for s in om.SEITEN:
        mx = sorted(OL['m5_x'][s])
        p.ok('{}: Hammermuttern nebeneinander (Abstand der M5)'.format(s),
             mx[1] - mx[0], HAMMERMUTTER_L + 1.0)
        p.ok('{}: Hammermutter ganz im Profil (hinter dem Ende)'.format(s),
             mx[0] - OL['quer_ende'][s] - HAMMERMUTTER_L / 2.0, 1.0)
        p.ok('{}: Scheibe ganz auf dem Flansch (X)'.format(s),
             min(min(abs(x - OL['flansch_x'][s][0]),
                     abs(x - OL['flansch_x'][s][1])) for x in mx) - sr, 1.0)
    # Inbus von aussen: vorn nach vorn, hinten nach hinten (in der alten
    # Lage aus Portal.py, mit dem 2060 verschoben)
    hindernisse = ([q for _, liste in fremd for q in liste]
                   + portal_check.quer_quader(w, L))
    for s in om.SEITEN:
        aus = OL['aus'][s]
        y_kopf = OL['auflage_y'][s] + aus * (ow('m5_scheibe_h')
                                              + ow('m5_kopf_h'))
        pkt = [(x + dxp[s], y_kopf + dyp[s], OL['nut_seite_z'])
               for x in OL['m5_x'][s]]
        laenge = min(bauraum.freier_korridor(pt, 'y', aus, INBUS / 2.0 + 1.0,
                                             hindernisse)[0] for pt in pkt)
        p.ok('Inbus an den M5 des Anschlags {} (von aussen)'.format(s),
             999.0 if laenge == float('inf') else laenge, WERKZEUG_LAENGE)

    # ------------------------------------------------------------------
    p.titel('8) Nase und Endplatte: die Platte drueckt auf die Stirnseite')
    for s in om.SEITEN:
        ny, nx = OL['nase_y'][s], OL['nase_x'][s]
        p.ok('Nase {} greift vor das Plattenende'.format(s), ny[1] - ny[0],
             10.0)
        p.ok('Endplatte {} deckt die Stirnseite des 2060 (Y)'.format(s),
             min(OL['quer_y'][s][1] - OL['endplatte_y'][s][0]
                 if s == 'vorn' else OL['endplatte_y'][s][1]
                 - OL['quer_y'][s][0],
                 OL['endplatte_y'][s][1] - OL['endplatte_y'][s][0])
             - ow('rahmen_b'), 0.0)
        p.info('Nase {}: {:.0f} mm dick in X'.format(s, nx[1] - nx[0]))
        # Biegung der Nase um Z: Kragarm in Y, Kraft am halben Ueberstand,
        # Wurzel nur so breit wie die Endplatte
        t = ow('endplatte_t')
        h = ow('anschlag_h')
        sig = F_STOSS * (ny[1] - ny[0]) / 2.0 / (h * t ** 2 / 6.0)
        p.ok('Nase {}: Biegung bei {:.0f} N Stoss (in der Schichtebene)'
             .format(s, F_STOSS), sig, SIGMA_SCHICHT, '<=', 'MPa')
        flaeche = ow('rahmen_b') * min(h, OL['quer_z'][1] - OL['quer_z'][0])
        p.ok('Endplatte {}: Pressung an der Stirnseite'.format(s),
             F_STOSS / flaeche, PRESSUNG, '<=', 'MPa')
    p.ok('Nasen unter der Plattenoberflaeche', top - OL['anschlag_z'][1],
         1.0)
    p.ok('beide Nasen in einer Flucht (X)',
         abs(OL['nase_x']['vorn'][1] - OL['nase_x']['hinten'][1]), 0.01,
         '<=')
    p.info('Versatz der Profilenden (hinteres endet weiter links)',
           OL['quer_ende']['vorn'] - OL['quer_ende']['hinten'])
    p.info('Rechts haelt nichts: die 2060 fuehren die Platte in Y, '
           'herausgezogen wird sie nach rechts')

    # ------------------------------------------------------------------
    p.titel('9) Druck (Bambu Lab A1)')
    gesamt = 0.0
    for s in om.SEITEN:
        xb, yb, zb = OL['bb_x'][s], OL['bb_y'][s], OL['bb_z']
        bx, by, bz = xb[1] - xb[0], yb[1] - yb[0], zb[1] - zb[0]
        v = anschlag_volumen(ow, OL, s) / 1000.0
        gesamt += v
        p.ok('{}: {:.0f} x {:.0f} x {:.0f} mm, {:.1f} cm3 ({:.0f} g voll)'
             .format(om.anschlag_name(s), bx, by, bz, v, v * PETG),
             max(bx, by, bz), BETT, '<=')
    p.info('Unterseite aufs Bett: Flansch, Endplatte und Nase senkrecht, '
           'M5 waagerecht')
    p.info('Druckteile zusammen', gesamt, 'cm3')

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
            'Druck (PETG): Anschlag_vorn, Anschlag_hinten',
            '4 x M5x{:.0f} Zylinderkopf + 4 Scheiben M5 (DIN 125)'.format(
                OL['m5_schraube']),
            '4 Hammermuttern M5 (Nut 6) in der unteren Seitennut AUSSEN am '
            'linken Ende beider 2060',
            'Opferplatte: Spanplatte {:.0f} x {:.0f} x {:.1f} mm '
            '(vorhanden)'.format(ow('platte_l'), ow('platte_b'),
                                 ow('platte_dicke'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
