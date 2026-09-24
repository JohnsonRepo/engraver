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
                 'x_wagen_breite', 'x_wagen_hoehe', 'insert_m3_d'):
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
    # Ritzel: Spur 7 mm zwischen den Borden, Riemen muss hineinpassen
    spur0 = L['ritzel_z0'] + w('ritzel_bord')
    p.ok('Riemen in der Spur des Ritzels (unten)', L['xr_z0'] - spur0 + 0.01,
         0.0)
    p.ok('Riemen in der Spur des Ritzels (oben)',
         spur0 + 7.0 - L['xr_z1'], 0.5)
    p.ok('Ritzelnabe unter der Motorplatte', L['mp_z0'] - L['ritzel_z1'], 0.3)
    p.ok('Welle reicht in die Ritzelbohrung (Eingriff)',
         L['ritzel_z1'] - L['welle_z0'], 12.0)
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
    p.ok('Riemenhalter unter der Motorplatte', L['mp_z0'] - TL['rh_z1'], 3.0)
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
    p.titel('6) Y-Riemen und Riemenblock')
    p.info('Riemen Unterkante', L['yr_z0'])
    luft = w('klemm_schlitz') - w('riemen_dicke')
    p.ok('Klemmschlitz nimmt den Riemen auf (Luft)', luft, 0.1)
    p.ok('Rippen greifen zwischen die Zaehne', w('klemm_rippe') - luft, 0.5)
    p.ok('Riemenmitte auf der Linie von v8',
         -abs((L['yr_wand_u'] - w('riemen_dicke') / 2)
              - w('y_riemen_linie')), -0.01)
    p.info('Rippen in der festen Klemme', len(L['rb_rippen_y']), 'Stk')
    p.info('Rippen im Spannschieber', len(L['sch_rippen_y']), 'Stk')
    p.ok('Riemenblock neben dem Y-Wagen', w('rb_u0')
         - w('y_wagen_breite') / 2, 0.8)
    p.ok('Riemenblock neben dem Rahmen (2040)', w('rb_u0')
         - w('rahmen_b') / 2, 3.0)
    p.ok('Kanal: Wand zur Schiene', L['kanal_u'][0] - L['rb_u'][0], 2.5)
    p.ok('Kanal: Wand nach innen', L['rb_u'][1] - L['kanal_u'][1], 2.5)
    p.ok('Kanal: Boden unter dem Riemen', L['kanal_z'][0] - L['rb_z'][0], 3.0)
    p.ok('Kanal: Decke bis zur Platte', L['rb_z'][1] - L['kanal_z'][1], 6.0)
    p.ok('Stiftbohrung: Boden darunter', (L['stift_z']
                                         - w('klemm_stift_d') / 2)
         - L['rb_z'][0], 2.0)
    mutter_dick = w('m3_mutter_h') + 0.3
    p.ok('Anschlag: Wand hinter der Mutter (traegt den Riemenzug)',
         (L['mutter_y'] - mutter_dick / 2) - L['anschlag_y'][0], 2.5)
    p.ok('Anschlag: Wand vor der Mutter',
         L['anschlag_y'][1] - (L['mutter_y'] + mutter_dick / 2), 2.5)
    p.ok('Druckschraube: ueber dem Riemen (Bohrung)',
         (L['druck_z'] - w('m3_durchgang') / 2) - L['yr_decke_z'], 1.5)
    p.ok('Druckschraube: unter dem Kanaldach',
         L['sch_z'][1] - (L['druck_z'] + w('m3_durchgang') / 2), 2.0)
    p.ok('Druckschraube M3x{:.0f}: entspannt durch die Mutter'.format(
        L['druck_schraube']),
         L['kanal_y'][0] + L['druck_schraube']
         - (L['mutter_y'] + w('m3_mutter_h') / 2), 0.5)
    p.ok('Druckschraube: gespannt noch im Block (vorn)',
         L['rb_y'][1] - L['druck_spitze_max'], 0.0)
    p.ok('Spannschieber: Weg', L['kanal_y'][1] - L['kanal_y'][0]
         - w('schieber_laenge'), 10.0)
    p.ok('Einsaetze ueber dem Kanal', (L['rb_z'][1] - w('insert_m3_t'))
         - L['kanal_z'][1], 3.0)
    for i, (u, y) in enumerate(L['rb_schrauben']):
        p.ok('Einsatz {} ueber Kanal/Anschlag im Block (Y)'.format(i + 1),
             min(y - L['rb_y'][0], L['rb_y'][1] - y), 5.0)
    p.ok('Mutterntasche neben dem vorderen Einsatz (Y)',
         (L['mutter_y'] - mutter_dick / 2)
         - (L['rb_schrauben'][0][1] + w('insert_m3_d') / 2), 1.0)
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
    p.ok('Ruecklauf liegt in der Nut des 2040 (hinter der Flanke)',
         L['rahmen_flanke_u'] - (L['yr_rueck_u'] + w('riemen_dicke') / 2),
         0.0)
    p.ok('Riemenblock neben dem Ruecklauf',
         L['rb_u'][0] - (L['yr_rueck_u'] + w('riemen_dicke') / 2), 3.0)
    p.info('Riemen: Oberkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z1'])
    p.info('Riemen: Unterkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z0'])

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
    for u, y in L['rb_schrauben']:
        p.ok('Riemenblock-Schraube bei Y={:+.0f}: hinter der Rueckwand'.format(
            y), L['rueck_y0'] - (y + INBUS_FREI_D / 2), 0.9)
    p.ok('Riemenblock-Schraube M3x{:.0f}: Gewinde im Einsatz'.format(
        L['rb_schraube']), L['rb_eingriff'], 4.0)
    p.ok('Riemenblock-Schraube: setzt nicht auf',
         w('insert_m3_t') - L['rb_eingriff'], 0.5)
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
        korridor('Riemenblock-Schrauben {} (von oben)'.format(n),
                 [(x(u), y, L['platte_z1']) for u, y in L['rb_schrauben']],
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
                 ohne_wand + ('Portalrohr', 'Riemenblock ' + n) + halter,
                 r=2.5)
        ohne_block = tuple(t for t in schlitten if t != 'Stirnblock ' + n)
        korridor('Kernschraube {} (von aussen)'.format(n),
                 [(x(L['stirn_u'][0]), L['kern_y'], L['kern_z'])], 'x', s,
                 ohne_block + ('Portalrohr',) + halter, r=2.5)
        korridor('Druckschraube Spannschieber {} (von hinten)'.format(n),
                 [(x(L['yr_mitte_u']), L['kanal_y'][0] - 3.0, L['druck_z'])],
                 'y', -1, schlitten + ('Riemenblock ' + n, 'Y-Wagen ' + n,
                                       'Y-Schiene ' + n, 'Rahmen 2040 ' + n),
                 r=2.5)
        korridor('Stift feste Klemme {} (von vorn)'.format(n),
                 [(x(L['yr_mitte_u']), L['rb_y'][1], L['stift_z'])],
                 'y', +1, schlitten + ('Portalrohr', 'X-Schiene',
                                       'Riemenblock ' + n, 'Y-Wagen ' + n,
                                       'Y-Schiene ' + n, 'Rahmen 2040 ' + n),
                 r=2.0)
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
            ('Riemenblock', (L['rb_u'][1] - L['rb_u'][0],
                             L['rb_y'][1] - L['rb_y'][0],
                             L['rb_z'][1] - L['rb_z'][0])),
            ('Motorhalter', (L['mp_u'][1] - L['mp_u'][0],
                             L['mp_y'][1] - L['mp_y'][0],
                             L['mp_z1'] - L['mh_z'][0])),
            ('Umlenkhalter', (L['uh_innen_u'] - L['uh_saeule_u'][0],
                              L['uh_y'][1] - L['uh_saeule_y'][0],
                              L['klotz_z'][1] - L['wand_z1']))):
        p.ok('{}: groesste Kante'.format(name), max(masse), 250.0, '<=')
    p.ok('Bruecke im Riemenblock ueber dem Kanal (Anschlag, stehend)',
         L['kanal_u'][1] - L['kanal_u'][0], 25.0, '<=')
    p.ok('Bruecke Mutternschlitz Umlenkung (stehend)',
         (L['rolle_u'][1] - L['rolle_u'][0])
         + w('m5_mutter_sw') / math.cos(math.radians(30)) + 0.4, 25.0, '<=')

    # ------------------------------------------------------------------
    p.titel('11) Stueckliste Portal')
    for zeile in (
            '2x Y-Schlitten, 2x Riemenblock, 2x Spannschieber (links/rechts '
            'gespiegelt), 1x Motorhalter, 1x Umlenkhalter, 1x Spannklotz',
            '8x M3x{:.0f} Zylinderkopf (Schlitten -> Y-Wagen)'.format(
                L['wagen_schraube']),
            '4x M3x{:.0f} Zylinderkopf + 4x Messing-Einsatz M3 Ø5 '
            '(Riemenblock -> Platte)'.format(L['rb_schraube']),
            '4x M5x{:.0f} Zylinderkopf + 4x Hammermutter M5 Nut 6 '
            '(Rueckwand -> Rohr)'.format(L['rueck_schraube']),
            '2x M5x{:.0f} Zylinderkopf (Kernbohrung, M5 schneiden)'.format(
                L['kern_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x M3-Mutter (Druckschraube '
            'Spannschieber)'.format(L['druck_schraube']),
            '2x Stift Ø3 x 20 oder M3x20 (feste Y-Klemme)',
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

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
