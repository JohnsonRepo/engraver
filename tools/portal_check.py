#!/usr/bin/env python3
"""Rechnerische Pruefung des Portals (fusion/Portal) zusammen mit dem
Toolhead (fusion/ToolheadZ) — laeuft ohne Fusion.

Importiert beide Fusion-Skripte mit gestubbtem adsk-Modul und prueft:
Abgleich der gemeinsamen Masse, Kollisionen des Toolheads mit Schlitten,
Motor, Umlenkung, Riemen und Rahmen ueber den ganzen X- und Z-Weg, die
Portal-Teile untereinander, beide Riemen, Werkzeugzugang, Waende,
Schraubenlaengen und Druckbarkeit. Gibt am Ende die Stueckliste aus.

    python3 tools/portal_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

INBUS_FREI_D = 6.0            # Platz fuer den Inbus (wie toolhead_check)
WERKZEUG_LAENGE = 20.0        # kuerzester nutzbarer Inbus-Schenkel
X_SCHRITTE = 81               # Stellungen ueber den X-Weg
Z_SCHRITTE = 11               # Stellungen ueber den Z-Weg
# Teile des Toolhead-Modells, die das Portal selbst richtig abbildet
TOOLHEAD_OHNE = ('Portalprofil 2020', 'X-Schiene MGN15')


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    p = Pruefung()
    R = L['R']

    # ------------------------------------------------------------------
    p.titel('1) Abgleich ToolheadZ.py <-> Portal.py')
    for name in ('x_riemen_y', 'x_riemen_z0', 'riemen_breite', 'riemen_dicke',
                 'riemen_zahn_h', 'riemen_pld', 'klemm_schlitz', 'klemm_rippe',
                 'klemm_rippe_b', 'klemm_stift_d', 'x_wagen_laenge',
                 'x_wagen_breite', 'x_wagen_hoehe', 'insert_m3_d',
                 'traeger_x_links', 'traeger_x_rechts', 'rh_tiefe',
                 'rh_hoehe'):
        p.ja('{} gleich in beiden Skripten'.format(name),
             abs(tw(name) - w(name)) < 1e-9,
             '   ({} / {})'.format(tw(name), w(name)))
    p.ja('Rohrvorderseite gleich (portal_y)',
         abs(TL['portal_y'] - L['portal_y']) < 1e-9,
         '   ({} / {})'.format(TL['portal_y'], L['portal_y']))
    p.ok('Teilkreis 20 Z = 20 x 2 / pi', -abs(w('ritzel_teilkreis')
                                             - 40.0 / math.pi), -0.01)

    # ------------------------------------------------------------------
    p.titel('2) Portal: Schienenabstand und X-Weg')
    p.info('Y-Schienen Mitte zu Mitte', w('y_schienen_abstand'))
    p.info('Rohrende innen neben der Schienenmitte', L['profil_ende_u'])
    p.info('X-Schiene von', L['x_schiene_x'][0])
    p.info('X-Schiene bis', L['x_schiene_x'][1])
    p.info('X-Wagenmitte links', L['xw_min'])
    p.info('X-Wagenmitte rechts', L['xw_max'])
    p.ok('X-Weg = Schiene - Wagen (nichts nimmt davon weg)', L['x_weg'],
         w('x_schiene_laenge') - w('x_wagen_laenge') - 0.01)
    p.ok('X-Schiene liegt ganz auf dem Rohr (links)',
         L['x_schiene_x'][0] + w('profil_laenge') / 2, 0.0)
    p.ok('X-Schiene liegt ganz auf dem Rohr (rechts)',
         w('profil_laenge') / 2 - L['x_schiene_x'][1], 0.0)
    # Toolhead-Ausladung links/rechts neben der Wagenmitte, unten am Riemen
    feste_th, bewegte_th, erlaubt_th = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th if q.name not in TOOLHEAD_OHNE]

    # ------------------------------------------------------------------
    p.titel('3) Kollision Toolhead <-> Portal ueber den ganzen Weg '
            '({} X- x {} Z-Stellungen)'.format(X_SCHRITTE, Z_SCHRITTE))
    portal, erlaubt_p = bauraum.portal_bauraeume(w, L)
    rh_x0, rh_x1 = tw('traeger_x_links'), tw('traeger_x_rechts')
    # Paare Toolhead <-> Portal, die sich beruehren duerfen
    erlaubt_x = {
        ('X-Wagen MGN15H', 'X-Schiene'),
        ('X-Wagen MGN15H', 'Portalrohr'),         # faehrt auf der Schiene
        ('Riemenhalter', 'X-Riemen links'),       # klemmt die Riemenenden
        ('Riemenhalter', 'X-Riemen rechts'),
    }
    engste = {}
    xs_ = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)]
    zs_ = [TL['zc_min'] + (TL['zc_max'] - TL['zc_min']) * j
           / (Z_SCHRITTE - 1.0) for j in range(Z_SCHRITTE)]
    for xw in xs_:
        trume = bauraum.x_riemen_trume(L, xw, rh_x0, rh_x1)
        gegen = portal + trume
        feste_x = [q.verschoben(0.0, xw) for q in feste_th]
        for zc in zs_:
            teile = feste_x + [q.verschoben(zc, xw) for q in bewegte_th]
            for a in teile:
                for b in gegen:
                    paar = (a.name, b.name)
                    if paar in erlaubt_x:
                        continue
                    d = a.abstand(b)
                    if paar not in engste or d < engste[paar][0]:
                        engste[paar] = (d, xw, zc)
    kritisch = sorted(engste.items(), key=lambda t: t[1][0])[:12]
    for (a, b), (d, xw, zc) in kritisch:
        p.ok('{} <-> {} (X-Wagen {:+.1f}, zc {:+.1f})'.format(a, b, xw, zc),
             d + 0.01, w('luft_bau'))
    # die gezogenen Trume duerfen den Toolhead sonst nirgends beruehren —
    # steht oben mit drin; hier noch die beiden X-Enden einzeln
    for name, xw in (('links', L['xw_min']), ('rechts', L['xw_max'])):
        trume = bauraum.x_riemen_trume(L, xw, rh_x0, rh_x1)
        laenge = trume[0].x[1] - trume[0].x[0] if name == 'links' \
            else trume[1].x[1] - trume[1].x[0]
        p.ok('Riemenstueck am {} Ende bleibt frei (Laenge)'.format(name),
             laenge, 10.0)

    # ------------------------------------------------------------------
    p.titel('4) Portal-Teile untereinander (fest)')
    trume_mitte = bauraum.x_riemen_trume(L, 0.0, rh_x0, rh_x1)
    alle = portal + trume_mitte
    schlechteste = []
    for i, a in enumerate(alle):
        for b in alle[i + 1:]:
            if (a.name, b.name) in erlaubt_p or (b.name, a.name) in erlaubt_p:
                continue
            if 'X-Riemen' in a.name and 'X-Riemen' in b.name:
                continue                     # Trume untereinander
            if {'X-Ritzel', 'X-Riemen links'} == {a.name, b.name} or \
                    {'X-Umlenkrolle', 'X-Riemen rechts'} == {a.name, b.name}:
                continue                     # der Riemen laeuft auf ihnen
            schlechteste.append((a.abstand(b), a.name, b.name))
    schlechteste.sort()
    for d, a, b in schlechteste[:10]:
        p.ok('{} <-> {}'.format(a, b), d + 0.01, 0.0)

    # ------------------------------------------------------------------
    p.titel('5) X-Riemen')
    fl = w('motor_flansch') / 2.0
    p.ok('Riemen ueber der Flanke des X-Wagens',
         L['xr_z0'] - w('x_wagen_breite') / 2, 3.0)
    p.ok('Riemen ueber dem Rohr', L['xr_z0'] - L['profil_z1'], 3.0)
    # Ritzel: der Riemen laeuft mittig in der Spur zwischen den Borden
    spur0 = L['ritzel_z0'] + w('ritzel_bord')
    p.ok('Riemen in der Spur des Ritzels (unten)', L['xr_z0'] - spur0, 0.5)
    p.ok('Riemen in der Spur des Ritzels (oben)',
         spur0 + w('ritzel_spur') - L['xr_z1'], 0.5)
    # Ausgelegt auf 20 mm Welle: sie muss das ganze Ritzel tragen. Dafuer
    # steht der Motor tief, und die Nabe taucht in die Bundbohrung. Die
    # gemessene Welle (23 mm) steht weiter heraus und muss frei enden.
    p.ok('Welle ({:.0f} mm) reicht durch das ganze Ritzel'.format(
        w('motor_welle_l')), L['ritzel_z0'] - L['welle_z0'], 0.0)
    p.ok('Ritzel unter dem Zentrierbund (Luft)',
         L['bund_z0'] - L['ritzel_z1'], 0.5)
    p.ok('Ritzel dreht frei in der Bundbohrung (Luft rundum)',
         (w('motor_bund_d') + w('spiel_locker') - w('ritzel_flansch_d')) / 2,
         2.0)
    p.info('Nabe taucht in die Bundbohrung', L['ritzel_z1'] - L['mp_z0'])
    p.ok('Madenschrauben unter der Motorplatte (Inbus von vorn)',
         L['mp_z0'] - L['madenschraube_z'], 2.0)
    p.ok('Wellenende ueber dem Rohr (gemessene Welle {:.0f} mm)'.format(
        w('motor_welle_ist')), L['welle_ist_z0'] - L['profil_z1'], 3.0)
    p.info('laengste Welle, die noch 1 mm ueber dem Rohr endet',
           L['mp_z1'] - L['profil_z1'] - 1.0)
    p.ok('Umlenkrolle mittig auf dem Riemen',
         -abs((L['rolle_z0'] + L['rolle_z1']) / 2 - L['xr_zm']), -0.01)
    p.ok('Riemen zwischen den Platten der Umlenkung (unten)',
         L['xr_z0'] - L['uh_unten_z'][1], 2.0)
    p.ok('Riemen zwischen den Platten der Umlenkung (oben)',
         L['uh_oben_z'][0] - L['xr_z1'], 2.0)
    p.ok('Ruecklauf hinter dem Riemenhalter',
         TL['rh_y0'] - (L['xr_y_rueck'] + L['riemen_innen']), 3.0)
    p.ok('Ruecklauf vor der Saeule des Motorhalters',
         (L['xr_y_rueck'] - L['riemen_aussen']) - L['mh_hinten_y'][1], 3.0)
    p.ok('Ruecklauf vor der Saeule des Umlenkhalters',
         (L['xr_y_rueck'] - L['riemen_aussen']) - L['uh_saeule_y'][1], 3.0)
    # Am linken Ende steht der Riemenhalter neben der Motorplatte (in X
    # getrennt), nicht unter ihr
    p.ok('Riemenhalter neben der Motorplatte (X, linkes Ende)',
         (L['xw_min'] + tw('traeger_x_links'))
         - (L['x_motor'] + w('motor_flansch') / 2.0), 3.0)
    # Motorflansch gegen Traegerplatte am linken Ende (auch in 3), hier
    # ausdruecklich, weil motor_u daran haengt
    p.ok('Motorflansch <-> Traegerplatte am linken Ende (X)',
         (L['xw_min'] + tw('traeger_x_links')) - (L['x_motor'] + fl), 3.0)
    riemen_x = 2.0 * (L['x_rolle'] - L['x_motor']) \
        + math.pi * w('ritzel_teilkreis')
    p.info('Riemenschleife (Rolle in Mittelstellung)', riemen_x)
    p.info('Spannweg der Rolle = Riemenlaenge', 4.0 * w('rolle_weg'))
    p.ok('Zugschraube: Spitze entspannt durch die Mutter',
         L['zug_spitze_ist'] - L['zug_spitze'][0], 0.0)
    p.ok('Zugschraube: Spitze gespannt vor der M5',
         L['zug_spitze'][1] - L['zug_spitze_ist'], 0.0)
    p.ok('Spannklotz gespannt vor der Lasche',
         (L['rolle_u'][0] + L['klotz_u_rel'][0]) - L['uh_lasche_u'][1], 0.3)
    p.ok('M5-Achse: Spitze ueber dem Rohr', L['uh_spitze_z'] - L['profil_z1'],
         0.5)
    p.ok('M5-Achse: Gewinde in der Mutter',
         L['uh_mutter_z'][1] - L['uh_spitze_z'], 3.5)
    p.ok('Umlenkung: obere Platte dick genug',
         L['uh_oben_z'][1] - L['uh_oben_z'][0], 4.0)
    p.ok('Umlenkung: Platte ueber dem Mutternschlitz',
         L['uh_unten_z'][1] - L['uh_mutter_z'][1], 2.0)
    p.ok('Umlenkung: Rolle innen 3 mm vor der Traegerplatte (rechts)',
         (R - (L['rolle_u'][1] + w('rolle_d') / 2))
         - (L['xw_max'] + tw('traeger_x_rechts')), 3.0)
    p.ok('Umlenkung: Rolle aussen 3 mm vor dem Steg',
         (L['rolle_u'][0] - w('rolle_d') / 2) - L['uh_steg_u1'], 2.99)
    p.ok('Umlenkung: Langloch innen 2 mm vor dem Plattenrand',
         L['uh_innen_u'] - (L['rolle_u'][1] + w('m5_durchgang') / 2), 2.0)
    p.ok('Umlenkung: Mutternschlitz innen vor dem Plattenrand',
         L['uh_innen_u'] - (L['rolle_u'][1] + w('m5_mutter_sw')
                            / math.cos(math.radians(30)) / 2 + 0.2), 2.0)

    # ------------------------------------------------------------------
    p.titel('6) Y-Riemen und Klemmtuerme (wie v8)')
    p.info('Riemen Unterkante', L['yr_z0'])
    luft = w('klemm_schlitz') - w('riemen_dicke')
    p.ok('Klemmschlitz nimmt den Riemen auf (Luft)', luft, 0.1)
    p.ok('Rippen greifen zwischen die Zaehne', w('klemm_rippe') - luft, 0.5)
    p.ok('Riemenmitte auf der Linie von v8',
         -abs((L['yr_wand_u'] - w('riemen_dicke') / 2)
              - w('y_riemen_linie')), -0.01)
    p.info('Rippen je Klemmturm', len(L['kt_rippen_y_vorn']), 'Stk')
    # Zwei gleiche Tuerme wie in v8, symmetrisch zur Wagenmitte
    p.ok('Tuerme symmetrisch zur Wagenmitte (wie v8)',
         -abs((w('wagen_y') - L['kt_y_hinten'][0])
              - (L['kt_y_vorn'][1] - w('wagen_y'))), -0.01)
    p.ok('Tuerme gleich lang',
         -abs((L['kt_y_hinten'][1] - L['kt_y_hinten'][0])
              - (L['kt_y_vorn'][1] - L['kt_y_vorn'][0])), -0.01)
    p.ok('Luecke zwischen den Tuermen',
         L['kt_y_vorn'][0] - L['kt_y_hinten'][1], 10.0)
    p.ok('Klemmturm vorn hinter der Plattenkante (X-Wagen faehrt vorbei)',
         L['platte_y1'] - L['kt_y_vorn'][1], 0.0)
    p.ok('Klemmturm hinten auf der Platte',
         L['kt_y_hinten'][0] - L['platte_y0'], 0.0)
    p.ok('Klemmtuerme neben dem Y-Wagen',
         L['kt_u'][0] - w('y_wagen_breite') / 2, 0.8)
    p.ok('Klemmtuerme neben dem Rahmen (2040)',
         L['kt_u'][0] - w('rahmen_b') / 2, 3.0)
    p.ok('Klemmtuerme unter der Platte', L['platte_u'][1] - L['kt_u'][1], 0.0)
    # Querschnitt wie v8: Schlitz mit Rippen, Querstift unter dem Riemen
    p.ok('Klemmturm: Wand neben dem Schlitz (zur Schiene)',
         L['yr_rippe_u0'] - L['kt_u'][0], 3.0)
    p.ok('Klemmturm: Wand neben dem Schlitz (innen)',
         L['kt_u'][1] - L['yr_wand_u'], 3.0)
    p.ok('Klemmturm: Stift traegt den Riemen (Oberkante = Unterkante Riemen)',
         -abs(L['stift_z'] + w('klemm_stift_d') / 2 - L['yr_z0']), -0.01)
    p.ok('Klemmturm: Boden unter der Stiftbohrung',
         (L['stift_z'] - w('klemm_stift_d') / 2) - L['kt_z'][0], 3.0)
    p.ok('Klemmturm: Stift reicht durch beide Waende',
         L['kt_stift_l'] - (L['kt_u'][1] - L['kt_u'][0]), 0.5)
    p.ok('Klemmturm: Einsaetze ueber der Schlitzdecke',
         (L['kt_z'][1] - w('insert_m3_t')) - L['yr_decke_z'], 3.0)
    p.ok('Klemmturm: Einsatz, Wand seitlich',
         (L['kt_u'][1] - L['kt_u'][0] - w('insert_m3_d')) / 2, 1.5)
    for t in ('hinten', 'vorn'):
        ty = L['kt_y_' + t]
        ys = [y for _, y in L['kt_schrauben_' + t]]
        p.ok('Klemmturm {}: Einsatz, Wand zu den Enden (Y)'.format(t),
             min(min(ys) - ty[0], ty[1] - max(ys)) - w('insert_m3_d') / 2,
             2.0)
        p.ok('Klemmturm {}: Steg zwischen den Einsaetzen'.format(t),
             (max(ys) - min(ys)) - w('insert_m3_d'), 2.0)
    # Riemenfuehrung am Aufbau: Ritzel mit senkrechter Achse an beiden
    # Enden, der Ruecklauf laeuft in der oberen Nut des 2040. Die Zaehne
    # zeigen zur Innenseite der Schleife, also zum Ruecklauf — nur dort
    # greifen die Rippen, auf dem glatten Ruecken rutscht der Riemen durch.
    rippen_seite = math.copysign(1.0, L['yr_rippe_u1'] - L['yr_wand_u'])
    rueck_seite = math.copysign(1.0, L['yr_rueck_u'] - w('y_riemen_linie'))
    p.ja('Rippen auf der Zahnseite (zur Innenseite der Schleife)',
         rippen_seite == rueck_seite,
         '   (Ruecklauf {:.2f} mm neben der Schienenmitte, Rippen {})'.format(
             L['yr_rueck_u'], 'zur Schiene' if rippen_seite < 0
             else 'nach innen'))
    # Auf dem Teilkreis liegen die Wirklinien, nicht die Riemenmitten: die
    # Mitten beider Trume liegen um 2x den Versatz naeher beieinander
    p.ok('Trume: Riemenmitten = Teilkreis - 2x Wirklinienversatz',
         -abs((w('y_riemen_linie') - L['yr_rueck_u'])
              - (w('ritzel_teilkreis') - 2.0 * L['yr_wirk_versatz'])), -0.01)
    p.ok('Ruecklauf: Ruecken liegt in der Nut (hinter der Flanke)',
         L['rahmen_flanke_u'] - (L['yr_rueck_u'] - w('riemen_dicke') / 2),
         0.5)
    p.ok('Ruecklauf: Zahnspitzen hoechstens 0,5 mm vor der Flanke',
         0.5 - ((L['yr_rueck_u'] + w('riemen_dicke') / 2)
                - L['rahmen_flanke_u']), 0.0)
    p.ok('Klemmtuerme neben dem Ruecklauf',
         L['kt_u'][0] - (L['yr_rueck_u'] + w('riemen_dicke') / 2), 3.0)
    p.info('Riemen: Oberkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z1'])
    p.info('Riemen: Unterkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z0'])
    # Ruecklauf mittig in der oberen Seitennut: er muss in die Oeffnung
    # passen, in der Hoehe wie in der Tiefe
    p.ok('Ruecklauf passt in die Nutoeffnung (Hoehe)',
         w('nut_b') / 2 - (abs((L['yr_rueck_z'][0] + L['yr_rueck_z'][1]) / 2
                               - L['nut_z']) + w('riemen_breite') / 2), 0.05)
    p.ok('Ruecklauf steckt nicht tiefer als die Nutoeffnung',
         (L['yr_rueck_u'] - w('riemen_dicke') / 2)
         - (L['rahmen_flanke_u'] - w('nut_t')), 0.0)
    # Der Riemen laeuft nur in der oberen Nut: die Klemme haelt ihn auf
    # derselben Hoehe, und ihr Schlitz reicht bis ueber die Nut-Oberkante
    p.ok('Riemen in der Klemme mittig auf Hoehe der Nut',
         -abs((L['yr_z0'] + L['yr_z1']) / 2 - L['nut_z']), -0.05)
    p.ok('Riemen unter der Oberkante der Nut', L['nut_oberkante_z']
         - L['yr_z1'], 0.5)
    p.ok('Schlitzdecke der Klemmtuerme ueber der Nut-Oberkante',
         L['yr_decke_z'] - L['nut_oberkante_z'], 0.0)

    # ------------------------------------------------------------------
    p.titel('7) Schlitten: Waende, Schrauben, Wagen')
    p.ok('Platte endet hinter der Rohrvorderseite (X-Wagen faehrt vorbei)',
         L['portal_y'] - L['platte_y1'], 3.0)
    p.ok('Rohr liegt auf der Platte (Auflage in X)',
         L['platte_u'][1] - L['profil_ende_u'], 15.0)
    p.ok('Rohr liegt auf der Platte (Auflage in Y)',
         L['platte_y1'] - L['profil_y0'], 15.0)
    for u, y in L['wagen_loecher']:
        pass
    vorn = max(y for _, y in L['wagen_loecher'])
    p.ok('Wagenschrauben: vordere Reihe hinter der Rueckwand (Werkzeug)',
         L['rueck_y0'] - (vorn + INBUS_FREI_D / 2), 0.9)
    p.ok('Wagenschrauben: Senkung neben der Rueckwand',
         L['rueck_y0'] - (vorn + w('m3_senkung') / 2), 0.5)
    p.ok('Wagenschraube M3x{:.0f}: nicht tiefer als das Gewinde'.format(
        L['wagen_schraube']),
         w('y_gewinde_tiefe') - (L['wagen_schraube'] - L['wagen_klemm']), 0.0)
    p.ok('Wagenschraube: Gewinde im Wagen',
         L['wagen_schraube'] - L['wagen_klemm'], 3.0)
    for u, y in L['kt_schrauben_hinten']:
        p.ok('Schraube Klemmturm hinten bei Y={:+.0f}: hinter der Rueckwand'
             .format(y), L['rueck_y0'] - (y + INBUS_FREI_D / 2), 0.9)
    # Die Schrauben des vorderen Turms liegen unter dem Rohr: er kommt vor
    # dem Rohr an die Platte, der Kopf verschwindet ganz in der Senkung.
    p.info('Schrauben Klemmturm vorn unter dem Rohr (vor dem Rohr montieren)',
           len(L['kt_schrauben_vorn']), 'Stk')
    p.ok('Klemmturm vorn: Kopf unter der Auflage des Rohrs',
         w('m3_senkung_t') - w('m3_kopf_h'), 0.0)
    p.ok('Klemmturm vorn: Senkung neben der Rueckwand',
         min(y for _, y in L['kt_schrauben_vorn']) - w('m3_senkung') / 2
         - L['rueck_y1'], 0.5)
    p.ok('Turmschraube M3x{:.0f}: Gewinde im Einsatz'.format(
        L['turm_schraube']), L['turm_eingriff'], 4.0)
    p.ok('Turmschraube: setzt nicht auf',
         w('insert_m3_t') - L['turm_eingriff'], 0.5)
    p.ok('Rueckwand: Kopf versenkt, Wand darunter',
         w('rueckwand_dicke') - w('m5_senk_t'), 4.0)
    p.ok('Rueckwand: M5-Koepfe nebeneinander',
         (L['rueck_schrauben_u'][1] - L['rueck_schrauben_u'][0])
         - w('m5_senkung'), 1.0)
    p.ok('Rueckwand: Senkung am inneren Ende',
         L['rueck_u'][1] - (L['rueck_schrauben_u'][1] + w('m5_senkung') / 2),
         0.0)
    p.ok('Rueckwand: Senkung am Rohrende',
         (L['rueck_schrauben_u'][0] - w('m5_senkung') / 2)
         - L['profil_ende_u'], 0.0)
    # Hammermutter M5 fuer Nut 6 ist rund 10,5 mm lang
    p.ok('Rueckwand: erste Hammermutter liegt ganz im Rohr',
         w('rueck_schraube_1') - 10.5 / 2, 0.0)
    p.ok('Rueckwand-Schraube M5x{:.0f} greift in den Nutenstein'.format(
        L['rueck_schraube']),
         L['rueck_schraube'] - L['rueck_klemm'] - 1.8, 4.0)
    p.ok('Kernschraube M5x{:.0f}: Gewinde im Rohr'.format(L['kern_schraube']),
         L['kern_gewinde'], 10.0)
    p.ok('Stirnblock: Senkung der Kernschraube in der Wand',
         (L['kern_y'] - w('m5_senkung') / 2) - L['stirn_y'][0], 3.0)
    for u, y in L['halter_schrauben']:
        abst = min(abs(y - L['kern_y']) - w('insert_m3_d') / 2
                   - w('m5_senkung') / 2,
                   y - w('insert_m3_d') / 2 - L['stirn_y'][0])
        p.ok('Einsatz Halter bei Y={:+.1f}: Wand zu Senkung/Kante'.format(y),
             abst, 1.0)
        p.ok('Einsatz Halter bei Y={:+.1f}: Wand zur Aussenkante (u)'.format(
            y), u - w('insert_m3_d') / 2 - L['stirn_u'][0], 1.0)

    # ------------------------------------------------------------------
    p.titel('8) Motorhalter und Umlenkhalter')
    p.ok('Motorbund-Bohrung: Wand zur Hinterkante der Platte',
         (L['xr_yc'] - (w('motor_bund_d') + w('spiel_locker')) / 2)
         - L['mp_y'][0], 3.0)
    for u, y in L['motor_schrauben']:
        # alle vier von unten: nichts unter dem Kopf bis zur Rohroberseite
        pass
    hinten = min(y for _, y in L['motor_schrauben'])
    aussen = min(u for u, _ in L['motor_schrauben'])
    p.ok('hintere Motorschrauben vor der Saeule (Werkzeug)',
         (hinten - INBUS_FREI_D / 2) - L['mh_hinten_y'][1], 0.0)
    p.ok('aeussere Motorschrauben neben der Saeule (Werkzeug)',
         (aussen - INBUS_FREI_D / 2) - L['mh_aussen_u'][1], 0.0)
    p.ok('Werkzeuglaenge unter den Motorschrauben (bis Rohr/Stirnblock)',
         (L['mp_z0'] - w('m3_kopf_h')) - L['wand_z1'], WERKZEUG_LAENGE)
    p.ok('Motorschraube M3x{:.0f}: Gewinde im Flansch'.format(
        L['motor_schraube']), L['motor_schraube'] - w('mp_dicke'), 3.5)
    p.ok('Motorschraube: nicht tiefer als das Flanschgewinde',
         w('motor_gewinde_tiefe') - (L['motor_schraube'] - w('mp_dicke')),
         0.0)
    for u, y in L['halter_schrauben']:
        p.ok('Halterschraube bei Y={:+.1f}: Kopf neben dem Motorflansch'.format(
            y), (w('motor_u') - w('motor_flansch') / 2)
             - (u + w('m3_senkung') / 2), 0.5)
    for name, klemm, schraube in (('Motorhalter', L['mh_klemm'],
                                   L['mh_schraube']),
                                  ('Umlenkhalter', L['uh_klemm'],
                                   L['uh_schraube'])):
        p.ok('{}: M3x{:.0f} greift in den Einsatz'.format(name, schraube),
             schraube - klemm, 4.0)
        p.ok('{}: M3x{:.0f} setzt im Sackloch nicht auf'.format(
            name, schraube), w('insert_tief_t') - (schraube - klemm), 0.5)
    p.ok('Umlenkhalter-Saeule deckt die Halterschrauben',
         min(y for _, y in L['halter_schrauben']) - L['uh_saeule_y'][0]
         - w('m3_durchgang') / 2, 2.0)
    p.ok('Umlenkhalter-Saeule vorn hinter den Halterschrauben',
         L['uh_saeule_y'][1] - (max(y for _, y in L['halter_schrauben'])
                                + w('m3_durchgang') / 2), 2.0)
    p.ok('Motorhalter: aeussere Saeule deckt die vordere Halterschraube',
         L['mh_aussen_u'][1] - (w('halter_schraube_u')
                                + w('m3_durchgang') / 2), 2.0)
    p.ok('Lasche: Wand um die Zugschraube (Y)',
         (L['klotz_y'][1] - L['klotz_y'][0]) / 2 - w('m3_durchgang') / 2, 3.0)
    p.ok('Spannklotz: Mutter liegt auf (Boden unter der Tasche)',
         (L['uh_zug_z'] - (w('m3_mutter_sw') + w('tasche_spiel')) / 2)
         - L['klotz_z'][0], 0.5)
    p.ok('Spannklotz: Wand zwischen Mutter und M5',
         w('klotz_versatz') - (w('m3_mutter_h') + 0.3) / 2
         - w('m5_durchgang') / 2, 5.0)

    # ------------------------------------------------------------------
    p.titel('9) Werkzeugzugang')
    fest = {q.name: q for q in portal}

    def korridor(text, punkte, achse, ri, namen, soll=WERKZEUG_LAENGE,
                 r=INBUS_FREI_D / 2):
        boxen = [fest[n] for n in namen]
        schlecht = (float('inf'), None)
        for pt in punkte:
            d, wer = bauraum.freier_korridor(pt, achse, ri, r, boxen)
            if d < schlecht[0]:
                schlecht = (d, wer)
        d, wer = schlecht
        p.ok(text + ('' if d >= soll or wer is None else '  [' + wer + ']'),
             999.0 if d == float('inf') else d, soll)

    for n, s in (('links', -1), ('rechts', 1)):
        x = lambda u, s=s: s * (R - u)
        schlitten = ('Platte ' + n, 'Rueckwand ' + n, 'Stirnblock ' + n)
        korridor('Wagenschrauben {} (von oben, vor dem Rohr)'.format(n),
                 [(x(u), y, L['platte_z1']) for u, y in L['wagen_loecher']],
                 'z', +1, schlitten)
        korridor('Schrauben Klemmturm hinten {} (von oben)'.format(n),
                 [(x(u), y, L['platte_z1'])
                  for u, y in L['kt_schrauben_hinten']], 'z', +1, schlitten)
        korridor('Schrauben Klemmturm vorn {} (von oben, vor dem Rohr)'
                 .format(n), [(x(u), y, L['platte_z1'])
                              for u, y in L['kt_schrauben_vorn']],
                 'z', +1, schlitten)
        # mit Rohr und Haltern, die dann schon sitzen
        halter = (('Motorplatte', 'Motorhalter Saeule hinten',
                   'Motorhalter Saeule aussen', 'X-Motor') if s < 0 else
                  ('Umlenkhalter Saeule', 'Umlenkhalter oben',
                   'Umlenkhalter unten', 'Umlenkhalter Steg',
                   'Umlenkhalter Lasche'))
        # Die Koepfe sitzen in Senkungen der Wand selbst — die kennt der
        # Quader nicht. Der Korridor beginnt deshalb an der Aussenflaeche
        # der Wand; die Senkung (5 bzw. 17 mm) reicht der Schluessel hinein.
        ohne_wand = tuple(t for t in schlitten if t != 'Rueckwand ' + n)
        korridor('Rueckwand-Schrauben {} (von hinten)'.format(n),
                 [(x(u), L['rueck_y0'], L['kern_z'])
                  for u in L['rueck_schrauben_u']], 'y', -1,
                 ohne_wand + ('Portalrohr', 'Klemmturm hinten ' + n)
                 + halter,
                 r=2.5)
        ohne_block = tuple(t for t in schlitten if t != 'Stirnblock ' + n)
        korridor('Kernschraube {} (von aussen)'.format(n),
                 [(x(L['stirn_u'][0]), L['kern_y'], L['kern_z'])], 'x', s,
                 ohne_block + ('Portalrohr',) + halter, r=2.5)
        # Querstift im Klemmturm: von innen (zur Maschinenmitte) quer rein
        for t in ('hinten', 'vorn'):
            korridor('Querstift Klemmturm {} {} (von innen)'.format(t, n),
                     [(x(L['kt_u'][1]), L['kt_stift_y_' + t], L['stift_z'])],
                     'x', -s, schlitten + ('Klemmturm hinten ' + n,
                                           'Klemmturm vorn ' + n,
                                           'Y-Wagen ' + n, 'Y-Schiene ' + n,
                                           'Rahmen 2040 ' + n), r=2.0)
        korridor('Halterschrauben {} (von oben)'.format(n),
                 [(x(u), y, (L['mp_z1'] if s < 0 else L['uh_oben_z'][1])
                   + w('m3_kopf_h')) for u, y in L['halter_schrauben']],
                 'z', +1, schlitten + halter)
    korridor('Motorschrauben (von unten, bis Rohr/Stirnblock)',
             [(-(R - u), y, L['mp_z0'] - w('m3_kopf_h'))
              for u, y in L['motor_schrauben']], 'z', -1,
             ('Motorplatte', 'Motorhalter Saeule hinten',
              'Motorhalter Saeule aussen', 'Portalrohr', 'Stirnblock links',
              'Rueckwand links', 'X-Ritzel'))
    korridor('Zugschraube Umlenkung (von aussen)',
             [(R - L['uh_lasche_u'][0] + 3.0, L['xr_yc'], L['uh_zug_z'])],
             'x', +1, ('Umlenkhalter Saeule', 'Umlenkhalter oben',
                       'Umlenkhalter Lasche', 'Stirnblock rechts',
                       'Platte rechts'), r=2.5)
    korridor('M5-Achse Umlenkung (von oben)',
             [(R - u, L['xr_yc'], L['uh_kopf_z1']) for u in L['rolle_u']],
             'z', +1, ('Umlenkhalter Saeule', 'Umlenkhalter oben',
                       'Umlenkhalter Lasche', 'Spannklotz'), r=3.5)

    # ------------------------------------------------------------------
    p.titel('10) Druckbarkeit (Bambu Lab A1, Bauraum 256)')
    for name, masse in (
            ('Schlitten', (L['platte_u'][1] - L['platte_u'][0],
                           L['platte_y1'] - L['platte_y0'],
                           L['wand_z1'] - L['platte_z0'])),
            ('Klemmturm', (L['kt_u'][1] - L['kt_u'][0],
                           L['kt_y_vorn'][1] - L['kt_y_vorn'][0],
                           L['kt_z'][1] - L['kt_z'][0])),
            ('Motorhalter', (L['mp_u'][1] - L['mp_u'][0],
                             L['mp_y'][1] - L['mp_y'][0],
                             L['mp_z1'] - L['mh_z'][0])),
            ('Umlenkhalter', (L['uh_innen_u'] - L['uh_saeule_u'][0],
                              L['uh_y'][1] - L['uh_saeule_y'][0],
                              L['klotz_z'][1] - L['wand_z1'])),
            ('Y-Motorhalter', (L['ymh_u'][1] - L['ymh_u'][0],
                               L['ymh_y'][1] - L['ymh_wange_y'][0],
                               L['rahmen_z1'] - L['ymp_z0']))):
        p.ok('{}: groesste Kante'.format(name), max(masse), 250.0, '<=')
    p.ok('Bruecke Mutternschlitz Umlenkung (stehend)',
         (L['rolle_u'][1] - L['rolle_u'][0])
         + w('m5_mutter_sw') / math.cos(math.radians(30)) + 0.4, 25.0, '<=')

    # ------------------------------------------------------------------
    p.titel('11) Stueckliste Portal')
    for zeile in (
            '2x Y-Schlitten, 4x Klemmturm, 2x Y-Motorhalter (links/rechts '
            'gespiegelt), 1x Motorhalter, 1x Umlenkhalter, 1x Spannklotz',
            '8x M3x{:.0f} Zylinderkopf (Schlitten -> Y-Wagen)'.format(
                L['wagen_schraube']),
            '8x M3x{:.0f} Zylinderkopf + 8x Messing-Einsatz M3 Ø5 '
            '(Klemmtuerme -> Platte)'.format(L['turm_schraube']),
            '4x M5x{:.0f} Zylinderkopf + 4x Hammermutter M5 Nut 6 '
            '(Rueckwand -> Rohr)'.format(L['rueck_schraube']),
            '2x M5x{:.0f} Zylinderkopf (Kernbohrung, M5 schneiden)'.format(
                L['kern_schraube']),
            '4x Stift Ø3 x {0:.0f} oder M3x{0:.0f} (Querstift im Klemmturm)'
            .format(L['kt_stift_l']),
            '4x Messing-Einsatz M3 Ø5 (Stirnbloecke, fuer die Halter)',
            '4x M3x{:.0f} Zylinderkopf (NEMA 17 -> Motorhalter)'.format(
                L['motor_schraube']),
            '2x M3x{:.0f} Zylinderkopf (Motorhalter -> Stirnblock)'.format(
                L['mh_schraube']),
            '2x M3x{:.0f} Zylinderkopf (Umlenkhalter -> Stirnblock)'.format(
                L['uh_schraube']),
            '1x M5x{:.0f} Zylinderkopf + M5-Mutter + 3x Scheibe M5 '
            '(Achse Umlenkrolle)'.format(w('uh_bolzen')),
            '1x M3x{:.0f} + 1x M3-Mutter (Zugschraube Umlenkung)'.format(
                L['zug_schraube']),
            '1x GT2-Umlenkrolle 20 Z mit Kugellager, Bohrung 5',
            '1x GT2-Ritzel 20 Z, Bohrung 5 (X-Motor)',
            '1x NEMA 17 (X)',
            '2x NEMA 17 (Y), je ein GT2-Ritzel 20 Z Bohrung 5 direkt auf der '
            'Welle (das obere Ritzel der alten Eckwelle)',
            '8x M3x{:.0f} Zylinderkopf (NEMA 17 -> Y-Motorhalter, von oben)'
            .format(L['motor_schraube']),
            '4x M5x{:.0f} Zylinderkopf + 4x Hammermutter M5 Nut 6 '
            '(Y-Motorhalter -> obere Nut aussen am 2040)'.format(
                L['ymh_schraube']),
            '2x GT2-Riemen 6 mm, je ca. {:.0f} mm (Y, offen, von Klemme zu '
            'Klemme; hinteres Ritzel {:.0f} mm hinter der Stirnseite '
            'angenommen)'.format(L['yr_laenge'], w('yh_hinter')),
            'entfallen: die vorderen Eckwellen, ihre Lager und die unteren '
            'Ritzel, der Motorhalter in der Mitte des vorderen 2060',
            '1x GT2-Riemen 6 mm, ca. {:.0f} mm (X)'.format(
                2.0 * (L['x_rolle'] - L['x_motor'])
                + math.pi * w('ritzel_teilkreis')),
            'dazu am Toolhead: Riemenhalter, 2x M3x{:.0f} + 2x Einsatz, '
            '2x Stift Ø3 (siehe toolhead_check.py)'.format(TL['rh_schraube'])):
        p.info(zeile)

    # ------------------------------------------------------------------
    p.titel('12) Statische Pruefung der Schluessel in Portal.py')
    quelle = open(bauraum.PORTAL, encoding='utf-8').read()
    masse_namen = set(pm.MASSE)
    fehlt_m = sorted(set(re.findall(r"\bw\('([^']+)'\)", quelle))
                     - masse_namen)
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(L))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(masse_namen
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('13) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in pm.hinweise_bauen(L, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    # ------------------------------------------------------------------
    # Referenz: die 2060 liegen quer unter den 2040. Laser und Schlittenplatte
    # haengen tiefer als ihre Oberkante — mit Z unten begrenzt das vordere
    # 2060 den Y-Weg, nicht die Schiene. Lage wie im Modell: 2040 und
    # Schienen mittig zum Y-Wagen [?], das vordere 2060 35 mm hinter der
    # Stirnseite [v], das hintere 400 mm Mitte zu Mitte dahinter [?].
    p.titel('14) Y-Weg gegen die 2060 und die Y-Motorhalter (Referenz)')
    oben = L['quer_z'][1] + 3.0              # 3 mm Luft ueber dem 2060

    def tief(zc):
        return [q.verschoben(zc) for q in bewegte_th] + feste_th

    def unter_oben(zc):
        return [q for q in tief(zc) if q.z[0] < oben
                and 'Portal' not in q.name and 'Schiene' not in q.name]

    zc0 = TL['zc_min']
    d_schiene, d_vorn, d_hinten, teile = y_weg(w, L, TL, feste_th,
                                               bewegte_th)
    p.info('Toolhead-Teile unter der 2060-Oberkante (Z unten): '
           + ', '.join(sorted(set(q.name for q in teile))))
    p.info('Y-Wagen ab Schienenmitte bis Schienenende', d_schiene)
    p.info('ab Mitte nach vorn (Laserseite) bis 3 mm vor das 2060, Z unten',
           d_vorn)
    p.info('ab Mitte nach hinten bis 3 mm vor das 2060, Z unten', d_hinten)
    strahl = TL['strahl_y'] - w('wagen_y')    # ab Rahmenmitte
    p.info('Strahl erreicht mit Z unten ab Rahmenmitte von',
           strahl - min(d_schiene, d_hinten))
    p.info('                                          bis',
           strahl + min(d_schiene, d_vorn))
    zc_frei = next((zc / 10.0 for zc in range(int(zc0 * 10),
                                              int(TL['zc_max'] * 10) + 1)
                    if not unter_oben(zc / 10.0)), None)
    if zc_frei is not None:
        p.info('ueber die 2060 hinweg ab Wagenmitte zc', zc_frei)
        p.info('Linse dann ueber dem Bett',
               zc_frei + TL['laser_unten_rel'] + tw('bett_abstand'))

    # Vor dem vorderen 2060 stehen die Y-Motorhalter hoeher als das 2060.
    # Am vorderen Schienenende faehrt das Portal ueber sie; der Toolhead an
    # den X-Enden kommt ihnen nahe. Gerechnet in Rahmenkoordinaten, das
    # Portal um den Schienenweg nach vorn verschoben.
    halter = y_halter_quader(w, L)
    lang_fest = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    portal_bewegt = [q for q in portal
                     if not any(q.name.startswith(t) for t in lang_fest)]

    def vor(q, dy):
        return bauraum.Quader(q.name, q.x[0], q.x[1], q.y[0] + dy,
                              q.y[1] + dy, q.z[0], q.z[1], q.art)

    d_p = min(vor(q, d_schiene).abstand(h) for q in portal_bewegt
              for h in halter)
    p.ok('Portal (Schlitten, Klemmtuerme, Halter) am vorderen Schienenende '
         'frei ueber den Y-Motorhaltern', d_p, w('luft_bau'))

    def luft_toolhead(zc, ritzel):
        d = float('inf')
        for xw in xs_:
            for q in ([t.verschoben(0.0, xw) for t in feste_th]
                      + [t.verschoben(zc, xw) for t in bewegte_th]):
                qv = vor(q, d_schiene)
                for h in halter:
                    if ('Ritzel' in h.name) == ritzel:
                        d = min(d, qv.abstand(h))
        return d

    p.ok('Toolhead mit Z oben (nach dem Referenzieren) am vorderen '
         'Schienenende frei ueber Haltern und Motoren',
         luft_toolhead(TL['zc_max'], False), w('luft_bau'))
    zc_halter = next((zc / 2.0 for zc in range(int(zc0 * 2),
                                               int(TL['zc_max'] * 2) + 1)
                      if luft_toolhead(zc / 2.0, False) >= w('luft_bau')),
                     None)
    if zc_halter is not None:
        p.info('am vorderen Schienenende ueber Halter und Motoren ab zc',
               zc_halter)
        p.info('Linse dann ueber dem Bett',
               zc_halter + TL['laser_unten_rel'] + tw('bett_abstand'))
        # Der Ritzelbord steht 1,26 mm weiter innen als der Ruecken des
        # Riemens, an dem der Toolhead mit 3,4 mm vorbeifaehrt — seitlich
        # bleibt am Bord weniger, aber nur am vorderen Schienenende.
        d_r = min(luft_toolhead(zc / 2.0, True)
                  for zc in range(int(zc_halter * 2),
                                  int(TL['zc_max'] * 2) + 1))
        p.ok('Toolhead neben dem Ritzelbord (vorderes Schienenende, '
             'rechtes X-Ende)', d_r, 2.0)
    p.info('tiefer nur mit Softlimit fuer Y (vorn endet die Arbeitsflaeche '
           'ohnehin am 2060)')

    # ------------------------------------------------------------------
    p.titel('15) Y-Antrieb: Motor je Ecke vorn, Ritzel direkt auf der Welle')
    fl = w('motor_flansch') / 2.0
    ye = L['stirn_vorn_y']
    y_hinten, y_vorn = L['ym_y_bereich']
    bo = w('ritzel_bord')
    p.info('Ritzelachse innen neben der Schienenmitte', L['ym_u'])
    p.info('Ritzelachse vor der Stirnseite des 2040 (Mitte)', w('ym_vor'))
    p.info('   Langloch von', y_hinten - ye)
    p.info('             bis', y_vorn - ye)
    p.ok('gezogener Trum laeuft gerade von der Klemme zum Ritzel',
         -abs(L['ym_u'] + w('ritzel_teilkreis') / 2 - L['yr_wirk_u']), -0.01)
    p.ok('Ritzelspur mittig auf dem Riemen',
         -abs((L['ym_nabe_z1'] + bo + L['ym_ritzel_z1'] - bo) / 2
              - L['yr_zm']), -0.01)
    p.ok('Welle reicht durch das ganze Ritzel',
         L['ym_welle_z1'] - L['ym_ritzel_z1'], 0.0)
    p.ok('Ritzelnabe taucht in die Bundbohrung',
         L['ymp_z1'] - L['ym_ritzel_z0'], 0.5)
    p.ok('Ritzelnabe bleibt ueber dem Motorbund',
         L['ym_ritzel_z0'] - L['ym_bund_z1'], 0.5)
    p.ok('Madenschrauben ueber der Platte (Inbus von vorn)',
         (L['ym_madenschraube_z'] - 1.5) - L['ymp_z1'], 0.5)
    p.ok('Motor ganz hinten: vor der Stirnseite des 2040',
         (y_hinten - fl) - ye, 1.0)
    p.ok('Motor neben der Wange', (L['ym_u'] - fl) - L['ymh_wange_u'][1],
         3.0)
    p.ok('Motor vor dem vorderen 2060', (y_hinten - fl)
         - L['quer_y_vorn'][1], w('luft_bau'))
    p.info('gemessene Welle ({:.0f} mm) steht ueber dem Ritzel'.format(
        w('motor_welle_ist')), L['ym_welle_ist_z1'] - L['ym_ritzel_z1'])
    p.ok('   und endet unter der Oberkante des 2040',
         L['rahmen_z1'] - L['ym_welle_ist_z1'], 0.0)
    p.ok('Motor unten ueber der Unterkante der 2060 (Tisch)',
         L['ym_motor_z0'] - L['quer_z'][0], 10.0)
    p.ok('Motorplatte: Rand vor den vorderen Schrauben',
         L['ymh_y'][1] - (y_vorn + w('motor_loch') / 2
                          + w('m3_durchgang') / 2), 2.0)
    p.ok('Motorplatte: Rand hinter den hinteren Schrauben',
         (y_hinten - w('motor_loch') / 2 - w('m3_durchgang') / 2) - ye, 2.0)
    p.ok('Motorplatte: Rand innen neben den Schrauben',
         L['ymh_u'][1] - (L['ym_u'] + w('motor_loch') / 2
                          + w('m3_durchgang') / 2), 2.0)
    p.ok('Motorplatte traegt den Flansch auch ganz vorn',
         L['ymh_y'][1] - (y_vorn + fl), 0.0)
    p.ok('hintere Motorschrauben: Kopf vor der Anlage (Motor ganz hinten)',
         (y_hinten - w('motor_loch') / 2 - w('m3_senkung') / 2)
         - L['ymh_wand_y'][1], 0.5)
    p.ok('Ausschnitt: Rand hinter der inneren hinteren Schraube',
         (y_hinten - w('motor_loch') / 2 - w('m3_durchgang') / 2)
         - L['ymh_aus_y'][1], 2.0)
    p.ok('Ausschnitt: Anlage reicht ueber die ganze Stirnseite',
         L['ymh_wand_u'][1] - w('rahmen_b') / 2, 3.0)
    p.ok('Ritzelbord vor der Anlage (Motor ganz hinten)',
         (y_hinten - w('ritzel_flansch_d') / 2) - L['ymh_wand_y'][1], 3.0)
    p.ok('Anlage endet unter dem Riemen', L['yr_z0'] - L['ymh_wand_z'][1],
         1.5)
    nut_unten = L['nut_z'] - (w('rahmen_b') - 2.0 * w('nut_oben')) / 2.0
    p.ok('Anlage endet unter der Nutoeffnung (Ruecklauf tritt aus)',
         nut_unten - L['ymh_wand_z'][1], 0.5)
    p.ok('Motorschraube M3x{:.0f}: Gewinde im Flansch'.format(
        L['motor_schraube']), L['motor_schraube'] - w('mp_dicke'), 3.5)
    p.ok('Wange: 1. Hammermutter ganz in der Nut (~10,5 lang)',
         w('ymh_nut_y1') - 10.5 / 2, 1.0)
    p.ok('Wange: Hammermuttern nebeneinander',
         (w('ymh_nut_y2') - w('ymh_nut_y1')) - 10.5, 1.0)
    p.ok('Wange: Rand hinter der 2. M5',
         w('ymh_hinten') - w('ymh_nut_y2') - w('m5_durchgang') / 2, 3.0)
    p.ok('Wange: Rand ueber der M5', L['rahmen_z1']
         - (L['nut_z'] + w('m5_durchgang') / 2), 3.0)
    p.ok('Wange endet vor dem vorderen 2060',
         L['ymh_wange_y'][0] - L['quer_y_vorn'][1], 3.0)
    p.ok('M5x{:.0f}: Gewinde in der Hammermutter'.format(L['ymh_schraube']),
         L['ymh_schraube'] - w('ymh_wange') - 1.8, 3.5)
    p.ok('M5x{:.0f}: steht nicht auf dem Nutgrund auf'.format(
        L['ymh_schraube']), (w('nut_t') + w('nut_kammer_t'))
         - (L['ymh_schraube'] - w('ymh_wange')), 0.0)
    # Riemen: offen, von Klemme zu Klemme um beide Ritzel. Hinteres Ritzel
    # 11 mm hinter der Stirnseite angenommen (wie vorn die alte Eckwelle).
    wagen_min = L['y_schiene_y'][0] + w('y_wagen_laenge') / 2
    wagen_max = L['y_schiene_y'][1] - w('y_wagen_laenge') / 2
    rr = w('ritzel_flansch_d') / 2
    p.ok('vorderer Klemmturm am Schienenende hinter dem Ritzel des Motors',
         (y_hinten - rr) - (wagen_max + w('turm_abstand')), 10.0)
    p.ok('hinterer Klemmturm am Schienenende vor dem hinteren Ritzel',
         (wagen_min - w('turm_abstand')) - (L['yh_y'] + rr), 10.0)
    p.info('Y-Riemen je Seite, Klemme zu Klemme (Wirklinie)', L['yr_laenge'])
    p.info('   ueber den Spannweg des Motors von',
           L['yr_laenge'] - 2 * w('ym_spannweg'))
    p.info('                                 bis',
           L['yr_laenge'] + 2 * w('ym_spannweg'))
    # Motorschrauben von oben: senkrecht bis ins Freie
    # Rahmen und Riemen in ihrer wirklichen Laenge (die Quader des Portals
    # laufen endlos durch): das 2040 endet an der Stirnseite, beide Trume
    # am Ritzel
    boxen = [h for h in halter if 'Ritzel' in h.name]
    d_r = w('riemen_dicke') / 2.0
    for s_ in (-1, 1):
        for name, u, y, z in (
                ('Rahmen 2040', (-w('rahmen_b') / 2, w('rahmen_b') / 2),
                 L['rahmen_y'], (L['rahmen_z0'], L['rahmen_z1'])),
                ('Y-Riemen', (w('y_riemen_linie') - d_r,
                              w('y_riemen_linie') + d_r),
                 (L['rahmen_y'][0], y_vorn), (L['yr_z0'], L['yr_z1'])),
                ('Y-Ruecklauf', (L['yr_rueck_u'] - d_r,
                                 L['yr_rueck_u'] + d_r),
                 (L['rahmen_y'][0], y_vorn), L['yr_rueck_z'])):
            a, b = s_ * (R - u[0]), s_ * (R - u[1])
            boxen.append(bauraum.Quader(name, min(a, b), max(a, b), y[0],
                                        y[1], z[0], z[1]))
    schlecht = (float('inf'), None)
    for s_ in (-1, 1):
        for u, dy in L['ym_schrauben']:
            for y in (y_hinten + dy, y_vorn + dy):
                pt = (s_ * (R - u), y, L['ymp_z1'] + w('m3_kopf_h'))
                d, wer = bauraum.freier_korridor(pt, 'z', +1,
                                                 INBUS_FREI_D / 2, boxen)
                if d < schlecht[0]:
                    schlecht = (d, wer)
    p.ok('Motorschrauben von oben erreichbar'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)

    # ------------------------------------------------------------------
    # Elektronikfach: hinter dem hinteren 2060, unter den 2040. Rahmen-
    # koordinaten wie Abschnitt 14, das Portal faehrt bis an beide
    # Schienenenden. Stellungen, in denen der Toolhead ein 2060
    # durchdringen muesste, gibt es nicht — mit Z unten steht das hintere
    # 2060 davor — und werden uebersprungen.
    p.titel('16) Elektronikfach hinter dem hinteren 2060 (Referenz)')
    fach = elektronikfach(w, L)
    p.info('Fach X von', fach.x[0])
    p.info('       bis', fach.x[1])
    p.info('Fach Y von (vor der Stirnseite hinten)', fach.y[0])
    p.info('       bis (hinter dem hinteren 2060)', fach.y[1])
    p.info('Fach Z von (ueber dem Tisch)', fach.z[0])
    p.info('       bis (unter den 2040)', fach.z[1])
    p.info('Fach Breite', fach.x[1] - fach.x[0])
    p.info('     Tiefe (haengt am hinteren 2060 [?])', fach.y[1] - fach.y[0])
    p.info('     Hoehe', fach.z[1] - fach.z[0])
    quer = quer_quader(w, L)
    # nur die hintere Haelfte des Wegs: von vorn kommt nichts bis ans Fach
    dys = sorted(set([-d_schiene, -d_hinten, 0.0]
                     + [-d_schiene + 2.5 * i
                        for i in range(int(d_schiene / 2.5) + 1)]))
    xs_f = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / 20.0
            for i in range(21)]
    engste_f = (float('inf'), None)
    # Ueber dem Fach: in der Mitte (neben Schlitten und Klemmtuermen) reicht
    # nur die Traegerplatte tief herunter, und die hoechstens bis vor ihre
    # Lage am hinteren Schienenende. Dahinter bleibt viel mehr Hoehe.
    y_tr = TL['traeger_y0'] - d_schiene - w('luft_bau')
    hoch = {}          # tiefster bewegter Punkt ueber dem Fach, je Zone
    zonen = {'mitte': (225.0, y_tr), 'mitte16': (225.0, fach.y[1])}
    for dy in dys:
        teile_p = [vor(q, dy) for q in portal_bewegt]
        for xw in xs_f:
            fx = [vor(q.verschoben(0.0, xw), dy) for q in feste_th]
            for zc in zs_:
                th_ = fx + [vor(q.verschoben(zc, xw), dy)
                            for q in bewegte_th]
                if any(t.abstand(k) < 0 for t in th_ for k in quer):
                    continue
                for q in th_ + teile_p:
                    d = q.abstand(fach)
                    if d < engste_f[0]:
                        engste_f = (d, q.name, dy)
                    for zn, (xb, yv) in zonen.items():
                        if (q.x[0] < xb and -xb < q.x[1] and q.y[0] < yv
                                and fach.y[0] < q.y[1]
                                and q.z[0] < hoch.get(zn, (1e9,))[0]):
                            hoch[zn] = (q.z[0], q.name)
    p.ok('Fach frei von Portal und Toolhead, alle Stellungen [{}, Portal '
         '{:+.1f}]'.format(engste_f[1], engste_f[2]), engste_f[0],
         w('luft_bau'))
    zm = hoch.get('mitte', (1e9, None))
    zd = hoch.get('mitte16', (1e9, None))
    p.info('hoeher darf es in der Mitte (|X| <= 225) ab {:.1f} mm hinter dem '
           '2060: frei bis Z [{}]'.format(L['quer_y_hinten'][0] - y_tr,
                                          zm[1]), zm[0] - w('luft_bau'))
    p.info('   direkt hinter dem 2060 nur bis Z [{}]'.format(zd[1]),
           zd[0] - w('luft_bau'))

    return p.bericht()


def y_weg(w, L, TL, feste_th, bewegte_th, luft=3.0):
    """Y-Weg ab der Mitte, Rahmenkoordinaten wie Abschnitt 14: bis zum
    Schienenende und, mit Z unten, bis `luft` vor das vordere bzw. hintere
    2060. Liefert (d_schiene, d_vorn, d_hinten, Teile unter der
    2060-Oberkante)."""
    oben = L['quer_z'][1] + luft
    teile = [q for q in ([t.verschoben(TL['zc_min']) for t in bewegte_th]
                         + feste_th)
             if q.z[0] < oben and 'Portal' not in q.name
             and 'Schiene' not in q.name]
    d_schiene = w('y_schiene_laenge') / 2 - w('y_wagen_laenge') / 2
    d_vorn = L['quer_y_vorn'][0] - luft - max(q.y[1] for q in teile)
    d_hinten = min(q.y[0] for q in teile) - luft - L['quer_y_hinten'][1]
    return d_schiene, d_vorn, d_hinten, teile


def quer_quader(w, L):
    """Beide 2060 als Quader in Rahmenkoordinaten (Portal in der Mitte)."""
    return [bauraum.Quader('2060 ' + n, L['quer_x'][0], L['quer_x'][1],
                           y[0], y[1], L['quer_z'][0], L['quer_z'][1],
                           'kaufteil')
            for n, y in (('hinten', L['quer_y_hinten']),
                         ('vorn', L['quer_y_vorn']))]


def elektronikfach(w, L, rand=3.0, tisch=2.0):
    """Freier Raum fuer die Elektronik hinter dem hinteren 2060: zwischen
    den Innenseiten der 2040, bis vor ihre hintere Stirnseite, vom Tisch
    bis unter die 2040 — jeweils mit `rand` Abstand, zum Tisch `tisch`.
    Rahmenkoordinaten wie Abschnitt 14 (Portal in der Mitte)."""
    xi = L['R'] - w('rahmen_b') / 2.0 - rand
    return bauraum.Quader('Elektronikfach', -xi, xi, L['rahmen_y'][0] + rand,
                          L['quer_y_hinten'][0] - rand,
                          L['quer_z'][0] + tisch, L['rahmen_z0'] - rand)


def y_halter_quader(w, L):
    """Y-Motorhalter, Motor und Ritzel beider Seiten als Quader in
    Rahmenkoordinaten (Portal in der Mitte). Motor und Ritzel als Huelle
    ueber ihren ganzen Spannweg."""
    R = L['R']
    fl = w('motor_flansch') / 2.0
    rr = w('ritzel_flansch_d') / 2.0
    y0, y1 = L['ym_y_bereich']
    q = []
    for s in (-1, 1):
        n = 'links' if s < 0 else 'rechts'

        def xb(u0, u1):
            a, b = s * (R - u0), s * (R - u1)
            return min(a, b), max(a, b)

        for name, u, y, z in (
                ('Y-Motorplatte', (L['ymh_u'][0], L['ymh_aus_u'][0]),
                 L['ymh_y'], (L['ymp_z0'], L['ymp_z1'])),
                ('Y-Motorplatte innen', (L['ymh_aus_u'][0], L['ymh_u'][1]),
                 (L['ymh_aus_y'][1], L['ymh_y'][1]),
                 (L['ymp_z0'], L['ymp_z1'])),
                ('Y-Anlage', L['ymh_wand_u'], L['ymh_wand_y'],
                 L['ymh_wand_z']),
                ('Y-Wange', L['ymh_wange_u'], L['ymh_wange_y'],
                 L['ymh_wange_z']),
                ('Y-Motor', (L['ym_u'] - fl, L['ym_u'] + fl),
                 (y0 - fl, y1 + fl), (L['ym_motor_z0'], L['ymp_z0'])),
                ('Y-Ritzel', (L['ym_u'] - rr, L['ym_u'] + rr),
                 (y0 - rr, y1 + rr),
                 (L['ym_ritzel_z0'], L['ym_welle_z1']))):
            x = xb(*u)
            q.append(bauraum.Quader('{} {}'.format(name, n), x[0], x[1],
                                    y[0], y[1], z[0], z[1]))
    return q


if __name__ == '__main__':
    sys.exit(main())
