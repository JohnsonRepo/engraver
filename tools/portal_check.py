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
# Gedruckte Energiekette: um 180 Grad bis an die Anschlaege gebogen ist die
# Schleife aussen so hoch (Messschieber, 4 Gelenke im Bogen, 2026-10-02).
# Die Konstruktion darf nicht enger sein, sonst drueckt die Kette den
# Kettenhalter hoch, und nur wenig weiter, sonst haengt der Bogen durch.
KETTE_SCHLEIFE = 50.0       # mm aussen, gemessen
KETTE_SCHLEIFE_WEITER = 5.0     # so viel weiter darf die Konstruktion sein
KETTE_ANSCHLAG_MODELL = 47.0    # Grad je Glied im Modell der 3MF
# X-Riemen am Motorhalter (Rechnung wie y_motorhalter_check.py): Richtwert
# 20 N je Trum; kraeftig ueberspannt das Dreifache. Bis Rev. 23 hielt den
# Halter nur die Reibung unter den zwei M3, seit Rev. 24 ein Anschlag.
VORSPANNUNG = 20.0          # N je Trum, Richtwert
VORSPANNUNG_MAX = 60.0      # N je Trum, kraeftig ueberspannt
M3_KLEMMKRAFT = 300.0       # N je M3, vorsichtig: PETG unter dem Kopf
REIBWERT = 0.2              # PETG auf PETG
PETG_SCHICHT = 20.0         # N/mm2, Zugfestigkeit quer zu den Schichten


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
                 'rh_hoehe', 'kette_b', 'kette_h', 'kette_riegel',
                 'kette_r', 'kette_spiel', 'endstueck_l', 'endstueck_auge',
                 'endstueck_loch_a', 'endstueck_loch_ab',
                 'endstueck_loch_d', 'endstueck_platte', 'xk_y_vorn',
                 'xk_boden_z', 'xk_gelenk_x'):
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
                    {'X-Umlenkritzel', 'X-Riemen rechts'} == {a.name, b.name}:
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
    # Umlenkung (seit Rev. 18): Ritzel wie am Motor fest auf der Welle,
    # Nabe oben, die Spur auf dem Riemen. Die Welle laeuft oben im
    # Kugellager, unten im Gleitlager, beide im Lagerschlitten.
    spur0 = L['rolle_z0'] + w('ritzel_bord')
    p.ok('Riemen in der Spur des Umlenkritzels (unten)', L['xr_z0'] - spur0,
         0.5)
    p.ok('Riemen in der Spur des Umlenkritzels (oben)',
         spur0 + w('ritzel_spur') - L['xr_z1'], 0.5)
    p.ok('Umlenkritzel liegt mit dem Bord auf dem Gleitlager',
         -abs(L['gl_z'][1] - L['rolle_z0']), -0.01)
    p.ok('Gleitlager steht ueber den Arm (nur es beruehrt den Bord)',
         L['gl_z'][1] - L['ls_unten_z'][1], 0.3)
    p.ok('Gleitlager ganz im unteren Arm', L['gl_z'][0] - L['ls_unten_z'][0],
         0.5)
    p.ok('Nabe frei unter dem Kugellager', L['kl_z'][0] - L['rolle_z1'], 0.3)
    p.ok('Decke ueber dem Kugellager', L['ls_oben_z'][1] - L['kl_z'][1], 1.5)
    p.ok('Welle Ø{:.0f}x{:.0f}: im Gleitlager'.format(
        w('uw_d'), w('uw_laenge')), L['gl_z'][1] - L['uw_z'][0], 6.0)
    p.ok('Welle: ganz durch das Kugellager', L['uw_z'][1] - L['kl_z'][1], 1.0)
    p.ok('Welle: endet ueber dem Rohr', L['uw_z'][0] - L['profil_z1'], 0.5)
    p.ok('Riemen ueber dem unteren Arm des Schlittens',
         L['xr_z0'] - L['ls_unten_z'][1], 2.0)
    p.ok('Riemen unter dem oberen Arm des Schlittens',
         L['ls_oben_z'][0] - L['xr_z1'], 2.0)
    p.ok('Ruecklauf hinter dem Riemenhalter',
         TL['rh_y0'] - (L['xr_y_rueck'] + L['riemen_innen']), 3.0)
    p.ok('Ruecklauf vor der Saeule des Motorhalters',
         (L['xr_y_rueck'] - L['riemen_aussen']) - L['mh_hinten_y'][1], 3.0)
    p.ok('Ruecklauf vor dem Ruecken des Lagerschlittens',
         (L['xr_y_rueck'] - L['riemen_aussen']) - L['ls_ruecken_y'][1], 3.0)
    p.ok('Gezogener Trum hinter dem Pfosten des Lagerschlittens',
         L['ls_pfosten_y'][0] - (L['xr_y'] + L['riemen_aussen']), 3.0)
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
    p.info('Riemenschleife (Schlitten in Mittelstellung)', riemen_x)
    p.info('Spannweg des Schlittens = Riemenlaenge', 4.0 * w('rolle_weg'))
    # Zugschraube: Kopf aussen am Spannbock, Gewindeeinsatz im Ruecken
    p.ok('Zugschraube M3x{:.0f}: ganz entspannt im Einsatz'.format(
        L['zug_schraube']), L['zug_eingriff_ist'], w('zug_eingriff'))
    p.ok('Zugschraube: ganz gespannt endet die Spitze im Ruecken',
         L['zug_rest'], 1.0)
    p.ok('Schlitten ganz gespannt vor dem Spannbock',
         (L['rolle_u'][0] + L['ls_u_rel'][0]) - L['sb_wand_u'][1], 0.3)
    p.ok('Feder: ganz gespannt noch im Rohr',
         (L['rolle_u'][0] + L['ls_feder_u_rel'][0]) - L['profil_ende_u'], 3.0)
    p.ok('Feder: Spiel in der Nut je Seite',
         (w('nut_b') - w('ls_feder_b')) / 2.0, 0.1)
    p.ok('Feder: nicht tiefer als die Engstelle der Nut',
         w('nut_t') - w('ls_feder_t'), 0.3)
    # Am rechten Ende steht der X-Wagen neben der Umlenkung (in X getrennt);
    # der Bord des Ritzels steht nur 2,75 mm ueber dem Wagen
    wagen_ende = L['xw_max'] + tw('x_wagen_laenge') / 2.0
    rf = w('ritzel_flansch_d') / 2.0
    p.ok('Umlenkritzel ganz innen neben dem X-Wagen (rechtes Ende)',
         (R - (L['rolle_u'][1] + rf)) - wagen_ende, 3.0)
    p.ok('Lagerschlitten ganz innen neben dem X-Wagen (rechtes Ende)',
         (R - (L['rolle_u'][1] + L['ls_u_rel'][1])) - wagen_ende, 3.0)
    p.ok('Umlenkritzel innen vor der Traegerplatte (rechtes Ende)',
         (R - (L['rolle_u'][1] + rf))
         - (L['xw_max'] + tw('traeger_x_rechts')), 3.0)
    p.ok('Lagerschlitten: Wand um das Kugellager (innen)',
         L['ls_u_rel'][1] - (w('kl_d') + w('spiel_press')) / 2.0, 2.0)
    p.ok('Lagerschlitten: Wand um das Gleitlager (innen)',
         L['ls_u_rel'][1] - (w('gl_d') + w('spiel_press')) / 2.0, 2.0)
    p.ok('Lagerschlitten: Wand um den Einsatz im Ruecken (Y)',
         (w('ls_ruecken') - w('insert_m3_d')) / 2.0, 1.5)

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
    # Riemenfuehrung (seit Rev. 16): beide Ritzel mittig zur 2040, die
    # Trume der Wagen laufen schraeg von der Klemme in die innere obere Nut,
    # der Ruecklauf gerade in der aeusseren. Die Zaehne zeigen zur
    # Innenseite der Schleife, also zur Schiene — nur dort greifen die
    # Rippen, auf dem glatten Ruecken rutscht der Riemen durch.
    H = L['ymh']
    rippen_seite = math.copysign(1.0, L['yr_rippe_u1'] - L['yr_wand_u'])
    innen_seite = math.copysign(1.0, 0.0 - L['yr_wirk_u'])   # zum Ritzel
    p.ja('Rippen auf der Zahnseite (zur Innenseite der Schleife)',
         rippen_seite == innen_seite,
         '   (Ritzel mittig zur 2040, Rippen {})'.format(
             'zur Schiene' if rippen_seite < 0 else 'nach innen'))
    # Auf dem Teilkreis liegen die Wirklinien, nicht die Riemenmitten: der
    # Ruecklauf liegt um den Versatz naeher an der Profilmitte
    p.ok('Ruecklauf im Portal = Riemen im Y-Motorhalter (Riemenmitte)',
         -abs(-L['yr_rueck_u'] - (H['trum_zahn_x'] + H['trum_ruecken_x'])
              / 2.0), -0.01)
    p.ok('Ruecklauf: Ruecken hinter der Lippe der aeusseren Nut',
         H['luft_lippe'], 1.0)
    p.ok('Ruecklauf: Zahnspitzen vor dem Nutgrund', H['luft_nutgrund'], 1.0)
    p.info('Riemen: Oberkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z1'])
    p.info('Riemen: Unterkante unter der Oberkante des 2040',
           L['rahmen_z1'] - L['yr_z0'])
    # Beide Trume laufen mittig in einer oberen Seitennut: der Riemen muss
    # in der Hoehe durch die Oeffnung passen
    p.ok('Riemen passt in die Nutoeffnung (Hoehe)',
         w('nut_b') / 2 - (abs((L['yr_rueck_z'][0] + L['yr_rueck_z'][1]) / 2
                               - L['nut_z']) + w('riemen_breite') / 2), 0.05)
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
    p.titel('8) Motorhalter und Spannbock')
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
                                  ('Spannbock', L['sb_klemm'],
                                   L['sb_schraube'])):
        p.ok('{}: M3x{:.0f} greift in den Einsatz'.format(name, schraube),
             schraube - klemm, 4.0)
        p.ok('{}: M3x{:.0f} setzt im Sackloch nicht auf'.format(
            name, schraube), w('insert_tief_t') - (schraube - klemm), 0.5)
    p.ok('Spannbock deckt die Halterschrauben (hinten)',
         min(y for _, y in L['halter_schrauben']) - L['sb_y'][0]
         - w('m3_durchgang') / 2, 2.0)
    p.ok('Spannbock deckt die Halterschrauben (vorn)',
         L['sb_y'][1] - (max(y for _, y in L['halter_schrauben'])
                         + w('m3_durchgang') / 2), 2.0)
    p.ok('Motorhalter: aeussere Saeule deckt die vordere Halterschraube',
         L['mh_aussen_u'][1] - (w('halter_schraube_u')
                                + w('m3_durchgang') / 2), 2.0)
    # Anschlag (Rev. 24): Beide Trume ziehen das Ritzel nach innen. Bis
    # Rev. 23 hielt den Halter dagegen nur die Reibung unter den zwei
    # Halterschrauben, die durch 28 mm PETG klemmen.
    reib = 2 * M3_KLEMMKRAFT * REIBWERT
    p.info('ohne Anschlag (bis Rev. 23): Reibung unter 2 x M3', reib, 'N')
    p.info('   so rutscht er ab {:.0f} N je Trum (Richtwert {:.0f} N)'
           .format(reib / 2.0, VORSPANNUNG))
    sp = L['mha_u'][0] - L['mh_aussen_u'][1]
    p.ok('Anschlag Motorhalter: Luft zur aeusseren Saeule', sp, 0.1)
    p.ok('   Halter erreicht ihn im Spiel seiner Schrauben', sp,
         (w('m3_durchgang') - 3.0) / 2.0 + 1e-9, '<=')
    p.ok('Anschlag: hinter ihm frei fuer die aeussere Motorschraube',
         L['mha_y'][0] - (hinten + INBUS_FREI_D / 2), 0.0)
    p.ok('Anschlag endet an der Vorderkante des Stirnblocks',
         L['stirn_y'][1] - L['mha_y'][1], 0.0)
    p.ok('Anschlag: neben dem Ritzel',
         (w('motor_u') - w('ritzel_flansch_d') / 2) - L['mha_u'][1], 2.0)
    p.ok('Anschlag: unter dem Riemen', L['xr_z0'] - L['mha_z'][1], 3.0)
    zug = 2.0 * VORSPANNUNG_MAX
    lang = L['mha_y'][1] - L['mha_y'][0]
    hoch = L['mha_z'][1] - L['mha_z'][0]
    dick = L['mha_u'][1] - L['mha_u'][0]
    p.info('Riemenzug, kraeftig ueberspannt ({:.0f} N je Trum)'.format(
        VORSPANNUNG_MAX), zug, 'N')
    p.ok('Anschlag: Flaechenpressung an der Saeule', zug / (lang * hoch),
         5.0, '<=', 'MPa')
    # Biegung am Fuss (Kraft in halber Hoehe) zieht quer an den Schichten
    sig = zug * hoch / 2.0 / (lang * dick ** 2 / 6.0)
    p.ok('Anschlag: Biegespannung am Fuss (Schichten), Sicherheit',
         PETG_SCHICHT / sig, 4.0, '>=', 'x')
    # Der Zug greift vor dem Anschlag an: das kleine Moment um die
    # Hochachse halten Reibung und Schrauben
    p.ok('Anschlag: Riemenzug greift so weit vor seinem Ende an',
         L['xr_yc'] - L['mha_y'][1], 5.0, '<=')
    p.ok('Spannbock: Wand um die Zugschraube (Y)',
         w('sb_wand_b') / 2 - w('m3_durchgang') / 2, 3.0)
    p.ok('Spannbock: Wand ueber der Zugschraube',
         L['sb_wand_z'][1] - (L['zug_z'] + w('m3_durchgang') / 2), 2.5)
    p.ok('Spannbock: Kopf der Zugschraube ueber dem Boden',
         (L['zug_z'] - w('m3_kopf_d') / 2) - L['sb_boden_z'][1], 0.5)

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
        if s < 0:
            schlitten += ('Anschlag Motorhalter',)
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
                  ('Spannbock Boden', 'Spannbock Wand'))
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
                 [(x(u), y, (L['mp_z1'] if s < 0 else L['sb_boden_z'][1])
                   + w('m3_kopf_h')) for u, y in L['halter_schrauben']],
                 'z', +1, schlitten + halter)
    korridor('Motorschrauben (von unten, bis Rohr/Stirnblock)',
             [(-(R - u), y, L['mp_z0'] - w('m3_kopf_h'))
              for u, y in L['motor_schrauben']], 'z', -1,
             ('Motorplatte', 'Motorhalter Saeule hinten',
              'Motorhalter Saeule aussen', 'Portalrohr', 'Stirnblock links',
              'Rueckwand links', 'X-Ritzel', 'Anschlag Motorhalter'))
    korridor('Zugschraube Umlenkung (von aussen)',
             [(R - L['sb_wand_u'][0] + w('m3_kopf_h'), L['zug_y'],
               L['zug_z'])],
             'x', +1, ('Spannbock Boden', 'Spannbock Wand',
                       'Stirnblock rechts', 'Platte rechts'), r=2.5)
    # Madenschrauben der Nabe: das Ritzel so drehen, dass eine nach innen
    # zeigt, dann kommt der Schluessel durch die offene Seite des Schlittens
    korridor('Madenschrauben Umlenkritzel (von innen)',
             [(R - w('rolle_u') - w('ritzel_nabe_d') / 2, L['xr_yc'],
               L['rolle_maden_z'])], 'x', -1,
             ('Lagerschlitten unten', 'Lagerschlitten oben',
              'Lagerschlitten Ruecken', 'Lagerschlitten Pfosten',
              'X-Riemen Ruecklauf'), r=2.0)
    # Wannenstuetzen: M5 von hinten in die Hammermutter, an allem vorbei,
    # was hinter dem Rohr steht
    hinten = tuple(n for n in fest if n.startswith(
        ('Klemmturm', 'Y-Wagen', 'Platte ', 'Rueckwand', 'Stirnblock',
         'Motorhalter', 'Spannbock', 'Anschlag')))
    korridor('Wannenstuetzen: M5 von hinten',
             [((x[0] + x[1]) / 2.0, L['st_platte_y'][0] - w('m5_kopf_h'),
               L['kern_z']) for x in L['st_x'].values()], 'y', -1, hinten)
    # Laschen der Wanne: M3 von oben, ueber ihnen nichts
    korridor('Wanne: Laschen-Schrauben (von oben)',
             [(x, y, L['wanne_boden_z'][1] + w('m3_kopf_h'))
              for x, y in L['wanne_laschen']], 'z', +1,
             tuple(n for n in fest if n != 'Kettenwanne'
                   and not n.startswith('Kettenwanne Lasche')))
    # Kettenhalter Y: 2x M3 von unten durch die Platte des linken
    # Schlittens; darunter stehen Y-Wagen, Klemmturm, Schiene und 2040
    unten = tuple(n for n in fest if n.startswith(
        ('Y-Wagen', 'Klemmturm', 'Y-Schiene', 'Rahmen 2040', 'Y-Riemen',
         'Y-Ruecklauf')))
    korridor('Kettenhalter Y: M3 von unten durch die Schlittenplatte',
             [(x, y, L['platte_z0'] - w('m3_kopf_h'))
              for x, y in L['khy_schrauben']], 'z', -1, unten)
    # Anfangsstueck Y: von oben, ueber ihm nichts
    korridor('Anfangsstueck Y -> Kettenhalter Y (von oben)',
             [(x, y, L['khy_z'][1] + w('endstueck_platte')
               + w('m3_kopf_h')) for x, y in L['khy_loecher']], 'z', +1,
             tuple(n for n in fest if not n.startswith(
                 ('Kettenhalter Y', 'Y-Kette'))))

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
            ('Spannbock', (L['sb_u'][1] - L['sb_u'][0],
                           L['sb_y'][1] - L['sb_y'][0],
                           L['sb_wand_z'][1] - L['wand_z1'])),
            ('Lagerschlitten', (L['ls_u_rel'][1] - L['ls_u_rel'][0],
                                L['ls_y'][1] - L['ls_y'][0],
                                L['ls_oben_z'][1] - L['ls_feder_z'][0])),
            ('Y-Motorhalter', (2.0 * L['ymh']['halbe_breite'],
                               L['ymh']['platte_y1'] - L['ymh']['wange_y0'],
                               L['ymh']['halter_z1']
                               - L['ymh']['halter_z0'])),
            ('Kettenwanne', (L['wanne_x'][1] - L['wanne_x'][0],
                             L['wanne_y'][1] - L['wanne_lasche_y'][0],
                             L['wanne_z'][1] - L['wanne_z'][0])),
            ('Wannenstuetze Festpunkt (mit Fluegel)',
             (L['st_x']['Festpunkt'][1] - L['kf_x'][0],
              L['st_arm_y'][1] - L['st_platte_y'][0],
              L['st_platte_z'][1] - L['st_platte_z'][0])),
            ('Kettenwanne Y', (L['ywanne_lasche_x'][1] - L['ywanne_x'][0],
                               L['ywanne_y'][1] - L['ywanne_y'][0],
                               L['ywanne_z'][1] - L['ywanne_z'][0])),
            ('Kettenhalter Y', (L['khy_x'][1] - L['khy_x'][0],
                                L['khy_y'][1] - L['khy_y'][0],
                                L['khy_leiste_z'][1] - L['khy_z'][0])),
            ('Traeger Y Festpunkt',
             (L['ytr_wand_x'][1] - L['ytr_arm_x'][0],
              L['ytr_y']['Festpunkt'][1] - L['ytr_y']['Festpunkt'][0],
              L['ytr_wand_z'][1] - L['ytr_wand_z'][0]))):
        p.ok('{}: groesste Kante'.format(name), max(masse), 250.0, '<=')
    # Lagerschlitten auf dem Ruecken liegend: der Pfosten ueberbrueckt
    # die Oeffnung zwischen den Armen
    p.ok('Bruecke Pfosten Lagerschlitten (auf dem Ruecken)',
         L['ls_oben_z'][0] - L['ls_unten_z'][1], 25.0, '<=')

    # ------------------------------------------------------------------
    p.titel('11) Stueckliste Portal')
    for zeile in (
            '2x Y-Schlitten, 4x Klemmturm (links/rechts gespiegelt), '
            '2x Y-Motorhalter (zweimal dasselbe Teil), 1x Motorhalter, '
            '1x Spannbock, 1x Lagerschlitten',
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
            '2x M3x{:.0f} Zylinderkopf (Spannbock -> Stirnblock)'.format(
                L['sb_schraube']),
            '1x M3x{:.0f} Zylinderkopf + 1x Messing-Einsatz M3 Ø5 '
            '(Zugschraube, Einsatz im Lagerschlitten)'.format(
                L['zug_schraube']),
            '1x GT2-Ritzel 20 Z, Bohrung 5 (Umlenkung, Nabe oben)',
            '1x Welle Ø{:.0f} x {:.0f} (Umlenkung)'.format(w('uw_d'),
                                                          w('uw_laenge')),
            '1x Rillenkugellager {:.0f}x{:.0f}, Bohrung 5 (z. B. MR105ZZ)'
            .format(w('kl_d'), w('kl_b')),
            '1x Gleitlager Ø{:.0f} x {:.0f}, Bohrung 5 (Sinterbronze)'.format(
                w('gl_d'), w('gl_l')),
            '1x GT2-Ritzel 20 Z, Bohrung 5 (X-Motor)',
            '1x NEMA 17 (X)',
            '2x NEMA 17 (Y), je ein GT2-Ritzel 20 Z Bohrung 5 direkt auf der '
            'Welle (das obere Ritzel der alten Eckwelle)',
            '8x M3x{:.0f} Zylinderkopf + 8x Scheibe DIN 125 (NEMA 17 -> '
            'Y-Motorhalter, von oben)'.format(L['ymh']['motor_schraube']),
            '{n}x M5x{:.0f} Zylinderkopf + {n}x Scheibe + {n}x Nutenstein M5 '
            'Nut 6 (Y-Motorhalter -> untere Nuten beider Seiten)'.format(
                L['ymh']['m5_schraube'], n=2 * L['ymh']['n_m5']),
            '2x GT2-Riemen 6 mm, je ca. {:.0f} mm (Y, offen, von Klemme zu '
            'Klemme; hinteres Ritzel {:.0f} mm hinter der Stirnseite '
            'angenommen)'.format(L['yr_laenge'], w('yh_hinter')),
            'entfallen: die vorderen Eckwellen, ihre Lager und die unteren '
            'Ritzel, der Motorhalter in der Mitte des vorderen 2060',
            '1x GT2-Riemen 6 mm, ca. {:.0f} mm (X)'.format(
                2.0 * (L['x_rolle'] - L['x_motor'])
                + math.pi * w('ritzel_teilkreis')),
            'dazu am Toolhead: Riemenhalter, 2x M3x{:.0f} + 2x Einsatz, '
            '2x Stift Ø3 (siehe toolhead_check.py)'.format(TL['rh_schraube']),
            'X-Energiekette, gedruckt (Modell "Energiekette"): 1x '
            'Anfangsstueck, {}x Kettenglied mit Riegel, 1x Endstueck 180'
            .format(L['xk_glieder']),
            '1x Kettenwanne, 3x Wannenstuetze (am Festpunkt die breite)',
            '3x M5x{:.0f} Zylinderkopf + 3x Hammermutter M5 Nut 6 '
            '(Wannenstuetzen -> hintere Nut des Rohrs)'.format(
                L['st_m5_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x Messing-Einsatz M3 Ø5 '
            '(Laschen der Wanne -> Wannenstuetzen)'.format(
                L['wanne_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x Scheibe DIN 125 + 2x Messing-'
            'Einsatz M3 Ø5 (Endstueck 180 -> Wanne -> Stuetze)'.format(
                L['xk_fest_schraube']),
            'dazu am Toolhead: Kettenhalter, 2x M3x{:.0f} + 2x Einsatz (von '
            'vorn), 2x M3x{:.0f} + Scheibe + 2x Einsatz (Anfangsstueck)'
            .format(TL['kh_schraube'], TL['kh_ende_schraube']),
            'Kabelweg X: Nutabdeckung Nut 6 oder Clips, ca. {:.0f} mm (obere '
            'Nut des Rohrs), 2x Kabelbinder am Kabelfluegel'.format(
                L['kf_nut_x'][1] - L['kf_nut_x'][0]),
            'Y-Energiekette, gedruckt: 1x Anfangsstueck, {}x Kettenglied '
            'mit Riegel, 1x Endstueck 180'.format(L['yk_glieder']),
            '1x Kettenhalter Y, 1x Kettenwanne Y, 3x Traeger Y (am '
            'Festpunkt der breite)',
            '2x M3x{:.0f} Zylinderkopf + 2x Messing-Einsatz M3 Ø5 '
            '(Kettenhalter Y, von unten durch die Schlittenplatte)'.format(
                L['khy_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x Scheibe DIN 125 + 2x Messing-'
            'Einsatz M3 Ø5 (Anfangsstueck -> Kettenhalter Y)'.format(
                L['khy_ende_schraube']),
            '3x M5x{:.0f} Zylinderkopf + 3x Hammermutter M5 Nut 6 (Traeger Y '
            '-> untere Seitennut des linken 2040)'.format(
                L['ytr_m5_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x Messing-Einsatz M3 Ø5 (Laschen '
            'der Wanne Y -> Traeger)'.format(L['wanne_schraube']),
            '2x M3x{:.0f} Zylinderkopf + 2x Scheibe DIN 125 + 2x Messing-'
            'Einsatz M3 Ø5 (Endstueck 180 -> Wanne Y -> Traeger)'.format(
                L['xk_fest_schraube']),
            '2x Kabelbinder (Zugentlastung Y: Kettenhalter Y und Wanne Y)'):
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
    # Stirnseite [v], das hintere 435 mm Mitte zu Mitte dahinter (110 mm
    # Ueberstand hinten gemessen [v]).
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
    p.info('  nach hinten begrenzt {}'.format(
        'die Schiene, das 2060 liegt dahinter' if d_schiene < d_hinten
        else 'das 2060, nicht die Schiene'))
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

    def luft_portal(dy):
        return min((vor(q, dy).abstand(h), q.name, h.name)
                   for q in portal_bewegt for h in halter)

    # Im Betrieb begrenzt das Softlimit das Portal vorn (3 mm vor dem 2060,
    # Z unten); das Schienenende selbst erreicht es nur von Hand. Dort
    # endet der vordere Klemmturm hinter dem inneren Schenkel des Halters,
    # ueber ihm und daneben — in allen drei Achsen getrennt (die Kanten
    # 3,8 mm auseinander), achsweise gemessen aber knapper als luft_bau.
    d_b = luft_portal(d_vorn)
    p.ok('Portal an der vorderen Grenze frei ueber den Y-Motorhaltern '
         '({} / {})'.format(d_b[1], d_b[2]), d_b[0], w('luft_bau'))
    d_e = luft_portal(d_schiene)
    p.ok('   am Schienenende (nur von Hand) beruehrungsfrei ({} / {})'.format(
        d_e[1], d_e[2]), d_e[0], 2.0)

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
    p.titel('15) Y-Antrieb: Y-Motorhalter vorn, Ritzel mittig zur 2040')
    # Der Halter selbst (Riemen in der Nut, Ritzel, Motor, Stege, Schrauben,
    # Kraefte, Druck) steht in tools/y_motorhalter_check.py; hier, wie er
    # im Portal sitzt und wie der Riemen von den Klemmen zu ihm laeuft.
    H = L['ymh']
    ye, zu = L['stirn_vorn_y'], L['rahmen_z0']
    y_hinten, y_vorn = L['ym_y_bereich']
    rr = w('ritzel_flansch_d') / 2
    p.info('Ritzelachse vor der Stirnseite der 2040, von', y_hinten - ye)
    p.info('                                          bis', y_vorn - ye)
    p.ok('Ritzelspur auf Hoehe des Riemens in den Klemmen',
         -abs(zu + H['riemen_z'] - L['yr_zm']), -0.01)
    p.ok('Ritzel unter der Oberkante der 2040 (Schiene, Wagen)',
         L['rahmen_z1'] - L['ym_ritzel_z'][1], 2.0)
    p.ok('Motor unten ueber der Unterkante der 2060 (Tisch)',
         L['ym_motor_z'][0] - L['quer_z'][0], 10.0)
    p.ok('Schenkel enden vor dem vorderen 2060 (dort sitzen Winkel)',
         (ye + H['wange_y0']) - L['quer_y_vorn'][1], 3.0)
    # Riemen: offen, von Klemme zu Klemme um beide Ritzel. Hinteres Ritzel
    # mittig zur 2040, 11 mm hinter der Stirnseite angenommen.
    wagen_min = L['y_schiene_y'][0] + w('y_wagen_laenge') / 2
    wagen_max = L['y_schiene_y'][1] - w('y_wagen_laenge') / 2
    p.ok('vorderer Klemmturm am Schienenende hinter dem Ritzel des Motors',
         (y_hinten - rr) - (wagen_max + w('turm_abstand')), 10.0)
    p.ok('hinterer Klemmturm am Schienenende vor dem hinteren Ritzel',
         (wagen_min - w('turm_abstand')) - (L['yh_y'] + rr), 10.0)
    # Die Trume der Wagen laufen schraeg von der Klemme (Wirklinie
    # yr_wirk_u) an die mittigen Ritzel. Ihre Neigung aendert sich mit der
    # Stellung des Portals, und damit die Laenge des Riemenwegs: in der
    # Mitte ist er am kuerzesten.
    stellungen = [-d_schiene + 2.0 * d_schiene * i / 40.0 for i in range(41)]
    wege = [(dy, y_weg_riemen(pm, L, dy)) for dy in stellungen]
    lang = max(wege, key=lambda e: e[1]['laenge'])
    kurz = min(wege, key=lambda e: e[1]['laenge'])
    p.info('Y-Riemen je Seite, Klemme zu Klemme (Wirklinie, Portal Mitte)',
           L['yr_laenge'])
    p.info('   ueber den Spannweg des Motors +-',
           H['riemen_verstellung'] / 2.0)
    p.info('   Riemenweg am kuerzesten bei Portal {:+.0f}'.format(kurz[0]),
           kurz[1]['laenge'])
    p.info('   am laengsten bei Portal {:+.0f} (Riemen dort gedehnt)'.format(
        lang[0]), lang[1]['laenge'] - kurz[1]['laenge'])
    # Wo ein Trum durch die Oeffnung der inneren oberen Nut in den Kanal
    # laeuft, muss der Riemen mit seiner Breite durch die Engstelle
    for dy, text in ((d_schiene, 'vorderes Schienenende'),
                     (d_vorn, 'vordere Grenze, Z unten'), (0.0, 'Mitte'),
                     (-d_schiene, 'hinteres Schienenende')):
        g = y_weg_riemen(pm, L, dy)
        p.info('Portal {:+.1f} ({}):'.format(dy, text))
        for teil in ('vorn', 'hinten'):
            t = g[teil]
            p.info('   Trum {}: {:.0f} mm, {:.1f} Grad, {}'.format(
                teil, t['trum'], t['schraeg'], nut_durchgang(w, L, t, teil)))
    steil = max(max(g['vorn']['schraeg'], g['hinten']['schraeg'])
                for _, g in wege)
    p.info('Trume der Wagen: steilster Winkel ueber den ganzen Y-Weg', steil,
           'Grad')
    # Motorschrauben von oben: senkrecht bis ins Freie. Rahmen, Ritzel und
    # die Trume vor der Stirnseite in ihrer wirklichen Lage.
    boxen = [h for h in halter if 'Ritzel' in h.name]
    r_w = w('ritzel_teilkreis') / 2.0
    for s_ in (-1, 1):
        xm = s_ * R
        boxen.append(bauraum.Quader('Rahmen 2040', xm - w('rahmen_b') / 2,
                                    xm + w('rahmen_b') / 2, L['rahmen_y'][0],
                                    L['rahmen_y'][1], L['rahmen_z0'],
                                    L['rahmen_z1']))
        for sx in (-1, 1):
            u0, u1 = sorted((sx * (r_w - L['riemen_innen']),
                             sx * (r_w + L['riemen_aussen'])))
            boxen.append(bauraum.Quader('Y-Riemen vor der Stirnseite',
                                        xm + u0, xm + u1, ye, y_vorn,
                                        L['yr_z0'], L['yr_z1']))
    schlecht = (float('inf'), None)
    kopf_z = zu + H['platte_z1'] + w('m3_scheibe_h') + w('m3_kopf_h')
    weg = w('ymh_spann_weg') / 2.0
    for s_ in (-1, 1):
        for x, y in H['motor_langloecher']:
            for dy in (-weg, weg):
                pt = (s_ * R + x, ye + y + dy, kopf_z)
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
    p.info('     Tiefe (hinteres 2060 gemessen [v])', fach.y[1] - fach.y[0])
    p.info('     Hoehe', fach.z[1] - fach.z[0])
    # Ueber dem Fach: in der Mitte (neben Schlitten und Klemmtuermen) reicht
    # nur die Traegerplatte tief herunter, und die hoechstens bis vor ihre
    # Lage am hinteren Schienenende. Dahinter bleibt viel mehr Hoehe.
    y_tr = hohe_zone_y(w, TL, d_schiene)
    zonen = {'mitte': (225.0, y_tr, fach.y[0]),
             'mitte16': (225.0, fach.y[1], fach.y[0])}
    engste_f, hoch = luft_hinten(w, L, TL, feste_th, bewegte_th, [fach],
                                 zonen)
    p.ok('Fach frei von Portal und Toolhead, alle Stellungen [{}, Portal '
         '{:+.1f}]'.format(engste_f[2], engste_f[3]), engste_f[0],
         w('luft_bau'))
    zm = hoch.get('mitte', (1e9, None))
    zd = hoch.get('mitte16', (1e9, None))
    p.info('hoeher darf es in der Mitte (|X| <= 225) ab {:.1f} mm hinter dem '
           '2060: frei bis Z [{}]'.format(L['quer_y_hinten'][0] - y_tr,
                                          zm[1]), zm[0] - w('luft_bau'))
    p.info('   direkt hinter dem 2060 nur bis Z [{}]'.format(zd[1]),
           zd[0] - w('luft_bau'))

    # ------------------------------------------------------------------
    p.titel('17) Energiekette X: gedruckte Kette, Wanne, Kettenhalter')
    tk, rk = w('kette_teilung'), w('kette_r')
    # Wie eng sich die Kette biegen laesst, zeigt die gemessene Schleife;
    # die Konstruktion (2 R + Hoehe + beide Riegel) darf nicht enger sein.
    schleife = 2.0 * rk + w('kette_h') + 2.0 * w('kette_riegel')
    p.info('Schleife aussen gemessen (Messschieber, 4 Gelenke im Bogen)',
           KETTE_SCHLEIFE)
    p.ok('Schleife der Konstruktion (R{:.0f}) nicht enger als gemessen'
         .format(rk), schleife - KETTE_SCHLEIFE, 0.0)
    p.ok('   und hoechstens {:.0f} mm weiter'.format(KETTE_SCHLEIFE_WEITER),
         schleife - KETTE_SCHLEIFE, KETTE_SCHLEIFE_WEITER, '<=')
    p.info('Gelenkwinkel fuer R{:.0f} bei Teilung {:.0f} (Modell: {:.0f})'
           .format(rk, tk, KETTE_ANSCHLAG_MODELL),
           math.degrees(2.0 * math.asin(tk / (2.0 * rk))), 'Grad')
    p.info('Glieder', L['xk_glieder'], 'Stk')
    p.info('Kette zwischen den Gelenken', L['xk_laenge'])
    p.info('  gebraucht: halber Hub + Bogen (pi R)', L['xk_noetig'])
    p.info('  mit beiden Endstuecken', L['xk_laenge'] + 2.0 * w('endstueck_l'))
    p.ok('Kette reicht (Schlupf)', L['xk_schlupf'], 0.0)
    p.ok('kein Glied zu viel (Schlupf kleiner als eine Teilung)',
         L['xk_schlupf'], tk, '<')
    mitte = (L['xw_min'] + L['xw_max']) / 2.0 + w('xk_gelenk_x')
    p.ok('Festpunkt in der Mitte des Wegs des bewegten Gelenks',
         -abs(L['xk_fest'] - mitte), -0.01)
    p.ok('Bogen beginnt links nicht vor dem Festpunkt',
         L['xk_bogen_x'][0] - L['xk_fest'], 0.0)
    p.ok('Untertrum am rechten Ende noch auf der Wanne',
         L['wanne_x'][1] - L['xk_bogen_x'][1], 0.0)
    # Toolhead <-> Portal: das Anfangsstueck liegt auf der Linie der Kette
    p.ok('Auflage des Kettenhalters = Unterseite des Obertrums',
         -abs(TL['kh_auflage_z1'] - L['xk_ober_z'][0]), -0.01)
    p.ok('Anfangsstueck auf der Linie der Kette (Y)',
         -abs(TL['kh_kette_y'][0] - L['xk_y'][0]), -0.01)
    p.ok('Fuss des Kettenhalters ueber dem Untertrum',
         TL['kh_fuss_z0'] - L['xk_unter_z'][1] + 0.01, w('luft_bau'))
    # Bogen und Obertrum fahren mit: gegen das Portal und den Toolhead
    ra = L['xk_bogen_r'][1]
    yk, zu, zo = L['xk_y'], L['xk_unter_z'], L['xk_ober_z']
    engste_k = {}
    for xw in xs_:
        xb_ = pm.xk_bogen(L, xw)
        xm_ = xw + w('xk_gelenk_x')
        kette = [bauraum.Quader('X-Kette Bogen', xb_, xb_ + ra, yk[0], yk[1],
                                zu[0], zo[1]),
                 bauraum.Quader('X-Kette Obertrum', xm_, xb_, yk[0], yk[1],
                                zo[0], zo[1])]
        # die Kette laeuft in der Wanne: sie und ihre Laschen (hinter der
        # Rueckwand) zaehlen nicht, der Untertrum ist dieselbe Kette
        gegen = ([q for q in portal
                  if not q.name.startswith(('Kettenwanne',
                                            'X-Kette Untertrum'))]
                 + [q.verschoben(0.0, xw) for q in feste_th
                    if q.name != 'Kette Anfangsstueck'])
        for a in kette:
            for b in gegen:
                # der Obertrum geht am Kettenhalter in das Anfangsstueck
                if (a.name == 'X-Kette Obertrum'
                        and b.name.startswith('Kettenhalter')):
                    continue
                d = a.abstand(b)
                if (a.name, b.name) not in engste_k \
                        or d < engste_k[(a.name, b.name)][0]:
                    engste_k[(a.name, b.name)] = (d, xw)
    for (a, b), (d, xw) in sorted(engste_k.items(),
                                  key=lambda t: t[1][0])[:6]:
        p.ok('{} <-> {} (X-Wagen {:+.1f})'.format(a, b, xw), d + 0.01,
             w('luft_bau'))
    # Wanne und Stuetzen ueber Riemen, Riemenhalter und Lagerschlitten
    rh_oben = tw('x_wagen_breite') / 2.0 + tw('rh_hoehe')
    p.ok('Wanne: Luft zur Traegerplatte (vorn)', -L['wanne_y'][1] + 0.01,
         w('luft_bau'))
    p.ok('Arme der Stuetzen ueber dem Riemenhalter',
         L['st_arm_z'][0] - rh_oben, w('luft_bau'))
    p.ok('Arme ueber dem X-Riemen', L['st_arm_z'][0] - L['xr_z1'],
         w('luft_bau'))
    p.ok('Block der Stuetzen hinter dem Ruecklauf',
         (L['xr_y_rueck'] - L['riemen_aussen']) - L['st_block_y'][1],
         w('luft_bau'))
    p.ok('Wanne endet vor dem Lagerschlitten',
         L['ls_innen_x'] - L['wanne_x'][1] + 0.01, w('luft_bau'))
    p.ok('Kette im Bogen ueber dem Lagerschlitten',
         L['xk_unter_z'][0] - L['ls_oben_z'][1], w('luft_bau'))
    # Schrauben und Einsaetze
    e = L['xk_fest_schraube'] - L['xk_fest_klemm']
    p.ok('Endstueck 180: M3x{:.0f} greift in den Einsatz im Arm'.format(
        L['xk_fest_schraube']), e, 4.0)
    p.ok('   und endet im Arm (er ist nicht dicker)', w('st_arm') - e, 0.5)
    e = L['wanne_schraube'] - w('wanne_boden')
    p.ok('Laschen: M3x{:.0f} greift in den Einsatz im Block'.format(
        L['wanne_schraube']), e, 4.0)
    p.ok('   setzt im Sackloch nicht auf', w('insert_m3_t') - e, 0.5)
    e = L['st_m5_schraube'] - w('st_platte') - w('nut_lippe')
    p.ok('Stuetzen: M5x{:.0f} greift in die Hammermutter'.format(
        L['st_m5_schraube']), e, 3.5)
    r_e = w('insert_m3_d') / 2.0
    _, yl = L['wanne_laschen'][0]
    p.ok('Block: Wand vor dem Einsatz', L['st_block_y'][1] - (yl + r_e), 2.0)
    p.ok('Lasche: Schraubenkopf liegt ganz auf',
         (yl - w('m3_kopf_d') / 2.0) - L['wanne_lasche_y'][0], 0.5)
    p.ok('Stuetze am Festpunkt: Rand neben den Einsaetzen',
         w('st_rand') - r_e, 2.0)
    p.ok('Stuetze am Festpunkt: Einsaetze vor dem Ende des Arms',
         w('st_arm_vorn') - (L['xk_y_mitte'] + r_e), 2.0)
    p.ok('Scheibe DIN 125 deckt die Loecher Ø{:.1f} der Endstuecke'.format(
        w('endstueck_loch_d')), w('m3_scheibe_d') - w('endstueck_loch_d'),
         1.0)
    # Schrauben am Festpunkt: von oben, der Toolhead steht dafuer rechts —
    # dann reicht der Obertrum nur von seinem Gelenk bis zum Bogen
    links_frei = (L['xw_max'] + w('xk_gelenk_x')) - (
        max(x for x, _ in L['xk_fest_loecher']) + INBUS_FREI_D / 2.0)
    p.ok('Schrauben am Festpunkt von oben frei (Toolhead rechts)',
         links_frei, 0.0)
    # Kabelweg am Festpunkt (Rev. 21): die Litzen kommen links neben der
    # Stuetze aus der oberen Nut, laufen vor dem Kabelfluegel hoch und oben
    # ueber den Riemen nach vorn in die Wanne
    rl = L['xr_y_rueck'] - L['riemen_aussen']
    p.ok('Litzen am Kabelfluegel hinter dem Ruecklauf', rl
         - L['kf_buendel_y'][1], w('luft_bau'))
    p.ok('Litzen ueber den Riemen: ueber dem Riemenhalter',
         L['kf_quer_z'][0] - TL['rh_z1'], w('luft_bau'))
    p.ok('Litzen zur Wanne: hinter dem Fuss des Kettenhalters',
         TL['kh_fuss_y'][0] - (L['xk_y_mitte'] + w('kf_buendel_t') / 2.0),
         w('luft_bau'))
    p.ok('Kabelfluegel: Wand neben den Schlitzen', w('kf_steg'), 2.0)
    p.ok('Kabelfluegel: unterer Schlitz ueber dem Rohr',
         w('kf_binder_z1') - w('kf_binder_b') / 2.0 - L['kf_z'][0], 2.0)
    p.ok('Kabelfluegel: oberer Schlitz unter der Oberkante',
         L['kf_z'][1] - (w('kf_binder_z2') + w('kf_binder_b') / 2.0), 2.0)
    p.info('Litzen in der oberen Nut, von X {:+.0f} bis'.format(
        L['kf_nut_x'][0]), L['kf_nut_x'][1])

    # ------------------------------------------------------------------
    p.titel('18) Energiekette Y: Kettenhalter Y, Wanne Y, Traeger (Y-Weg)')
    frei = L['yk_frei']
    p.info('Glieder', L['yk_glieder'], 'Stk')
    p.info('Kette zwischen den Gelenken', L['yk_laenge'])
    p.info('  gebraucht: Y-Weg + Reserve + 2 Luft, halb, + pi R',
           L['yk_noetig'])
    p.info('  mit beiden Endstuecken', L['yk_laenge'] + 2.0 * w('endstueck_l'))
    p.ok('Kette reicht', L['yk_laenge'] - L['yk_noetig'], 0.0)
    p.ok('kein Glied zu viel', L['yk_laenge'] - L['yk_noetig'], tk, '<')
    p.ok('y_weg_vorn wie in Abschnitt 14 (Z unten, 3 mm vor dem 2060)',
         abs(w('y_weg_vorn') - d_vorn), 0.5, '<=')
    p.ok('y_weg_hinten bis ans Schienenende wie in Abschnitt 14',
         abs(L['y_weg_hinten'] - d_schiene), 0.01, '<=')
    dy_lo, dy_hi = -d_schiene, L['yk_dy_bereich'][1]
    p.ok('Reserve nach vorn ueber den Y-Weg', L['yk_reserve_vorn'],
         w('yk_reserve'))
    p.ok('am hinteren Schienenende bleibt Untertrum',
         (frei + (dy_lo - L['yk_dy_fest'])) / 2.0, w('luft_bau') - 0.01)
    p.ok('Untertrum am vorderen Ende der Kette noch in der Wanne',
         L['ywanne_y'][1] - (L['yk_fest'] + frei), 0.0)
    p.ok('Wanne Y passt in den A1', L['ywanne_y'][1] - L['ywanne_y'][0],
         250.0, '<=')
    # Ueber den Weg: was mit dem Portal faehrt (Schlitten, Kettenhalter Y,
    # Obertrum, Bogen) gegen den Rahmen (2040, 2060, Winkel, Y-Motorhalter,
    # Elektronikfach) und die rahmenfesten Teile der Kette (Wanne, Traeger,
    # Untertrum). Rahmenkoordinaten wie Abschnitt 14.
    rahmen, erl_r = bauraum.y_kette_rahmen(w, L)
    durch = ('Rahmen 2040 links', 'Y-Schiene links', 'Y-Ruecklauf links',
             'Y-Riemen links')
    fest_r = (rahmen + quer_quader(w, L) + y_halter_quader(w, L)
              + [elektronikfach(w, L)]
              + [q for q in portal if q.name in durch])
    mit_portal = [q for q in portal if q.x[1] < -200.0
                  and q.name not in durch]
    kette_teile = ('Kettenhalter Y', 'Y-Kette')
    ra = L['xk_bogen_r'][1]
    xk = L['yk_x']
    # die Kette laeuft in der Wanne: sie und ihre Laschen (hinter der
    # Innenwand) zaehlen nicht, der Untertrum ist dieselbe Kette
    erlaubt_y = erl_r | {
        ('Y-Kette Untertrum', 'Kettenwanne Y'),
        ('Y-Kette Bogen', 'Kettenwanne Y'),
        ('Y-Kette Untertrum', 'Kettenwanne Y Lasche 1'),
        ('Y-Kette Untertrum', 'Kettenwanne Y Lasche 2'),
        ('Y-Kette Bogen', 'Kettenwanne Y Lasche 1'),
        ('Y-Kette Bogen', 'Kettenwanne Y Lasche 2'),
        ('Y-Kette Bogen', 'Y-Kette Untertrum'),
        ('Y-Kette Bogen', 'Y-Kette Obertrum'),
        ('Y-Kette Obertrum', 'Y-Kette Anfangsstueck'),
        ('Y-Kette Obertrum', 'Kettenhalter Y'),
        ('Y-Kette Obertrum', 'Kettenhalter Y Leiste aussen'),
        ('Y-Kette Obertrum', 'Kettenhalter Y Leiste innen')}

    def vor_y(qq, dy):
        return bauraum.Quader(qq.name, qq.x[0], qq.x[1], qq.y[0] + dy,
                              qq.y[1] + dy, qq.z[0], qq.z[1], qq.art)

    engste = {}
    n_y = int((dy_hi - dy_lo) / 2.5) + 1
    for i in range(n_y + 1):
        dy = min(dy_lo + 2.5 * i, dy_hi)
        ym = w('yk_gelenk_y') + dy
        yb = (frei + L['yk_fest'] + ym) / 2.0
        unter = bauraum.Quader('Y-Kette Untertrum', xk[0], xk[1],
                               L['yk_fest'] - w('endstueck_l'), yb,
                               *L['yk_unter_z'], 'kette')
        bogen = bauraum.Quader('Y-Kette Bogen', xk[0], xk[1], yb, yb + ra,
                               L['yk_unter_z'][0], L['yk_ober_z'][1],
                               'kette')
        ober = bauraum.Quader('Y-Kette Obertrum', xk[0], xk[1], ym, yb,
                              *L['yk_ober_z'], 'kette')
        faehrt = [vor_y(q, dy) for q in mit_portal] + [ober, bogen]
        steht = fest_r + [unter]
        for a_ in faehrt:
            for b_ in steht:
                if ((a_.name, b_.name) in erlaubt_y
                        or (b_.name, a_.name) in erlaubt_y):
                    continue
                # nur Paare, an denen die Kette beteiligt ist
                if not (a_.name.startswith(kette_teile)
                        or b_.name.startswith(kette_teile)
                        or b_.name.startswith(('Kettenwanne Y',
                                               'Traeger Y'))):
                    continue
                d = a_.abstand(b_)
                k_ = (a_.name, b_.name)
                if d < engste.get(k_, (float('inf'),))[0]:
                    engste[k_] = (d, dy)
        # Obertrum und Bogen gegen den Schlitten (faehrt mit)
        for a_ in (ober, bogen):
            for b_ in [vor_y(q, dy) for q in mit_portal]:
                if ((a_.name, b_.name) in erlaubt_y
                        or (b_.name, a_.name) in erlaubt_y
                        or b_.name.startswith(kette_teile)):
                    continue
                d = a_.abstand(b_)
                k_ = (a_.name, b_.name)
                if d < engste.get(k_, (float('inf'),))[0]:
                    engste[k_] = (d, dy)
    for (a_, b_), (d, dy) in sorted(engste.items(),
                                    key=lambda t: t[1][0])[:8]:
        p.ok('{} <-> {} (Portal {:+.1f})'.format(a_, b_, dy), d,
             w('luft_bau'))
    # Kettenhalter Y auf dem Schlitten
    e = L['khy_schraube'] - w('platte_dicke')
    p.ok('Kettenhalter Y: M3x{:.0f} von unten greift in den Einsatz'.format(
        L['khy_schraube']), e, 4.0)
    p.ok('   setzt im Sackloch nicht auf', w('insert_m3_t') - e, 0.5)
    p.ok('Kettenhalter Y: Wand ueber bzw. unter den Einsaetzen',
         w('khy_dicke') - w('insert_m3_t'), 1.0)
    e = L['khy_ende_schraube'] - w('m3_scheibe_h') - w('endstueck_platte')
    p.ok('Anfangsstueck Y: M3x{:.0f} greift in den Einsatz'.format(
        L['khy_ende_schraube']), e, 4.0)
    p.ok('   setzt im Sackloch nicht auf', w('insert_m3_t') - e, 0.5)
    # die Loecher im linken Schlitten (Neudruck) bzw. nach der Bohrlehre:
    # neben den Senkungen der Wagenschrauben
    d_w = min(math.dist(pk, (u - L['R'], y)) - (w('m3_durchgang')
                                                + w('m3_senkung')) / 2.0
              for pk in L['khy_schrauben'] for u, y in L['wagen_loecher'])
    p.ok('Schlitten links: Loecher Kettenhalter Y neben den Senkungen der '
         'Wagenschrauben', d_w, 2.0)
    xs_ = L['khy_schrauben'][0][0]
    p.ok('Schlittenplatte: Rand neben den Loechern',
         (xs_ - w('m3_durchgang') / 2.0) + L['platte_x1'], 2.0)
    p.ok('Schraubenkopf unter der Platte neben dem Y-Wagen',
         -L['y_wagen_x1'] - (xs_ + w('m3_kopf_d') / 2.0), 1.0)
    p.ok('Kettenhalter Y endet vor dem Stirnblock',
         L['stirn_y'][0] - L['khy_y'][1], 0.3)
    p.ok('Anfangsstueck Y liegt ganz auf dem Halter (hinten)',
         L['khy_ende_y'][0] - L['khy_y'][0], 0.0)
    # Wanne Y und Traeger
    e = L['wanne_schraube'] - w('wanne_boden')
    p.ok('Laschen Y: M3x{:.0f} greift in den Einsatz im Arm'.format(
        L['wanne_schraube']), e, 4.0)
    p.ok('   endet im Arm', w('ytr_arm') - e, 0.5)
    e = L['xk_fest_schraube'] - L['xk_fest_klemm']
    p.ok('Festpunkt Y: M3x{:.0f} greift in den Einsatz im Arm'.format(
        L['xk_fest_schraube']), e, 4.0)
    p.ok('   endet im Arm', w('ytr_arm') - e, 0.5)
    e = L['ytr_m5_schraube'] - w('ytr_wand') - w('nut_lippe')
    p.ok('Traeger Y: M5x{:.0f} greift in die Hammermutter'.format(
        L['ytr_m5_schraube']), e, 3.5)
    p.ok('Traeger Y: Wand ueber dem M5-Kopf',
         L['ytr_wand_z'][1] - (L['nut_u_z'] + w('m5_kopf_d') / 2.0), 1.0)
    p.ok('Traeger Y: Wand unter dem M5-Kopf',
         (L['nut_u_z'] - w('m5_kopf_d') / 2.0) - L['ytr_wand_z'][0], 1.0)
    p.ok('Traeger Y: M5-Kopf unter dem Arm (Inbus von aussen, auch mit '
         'Wanne)', L['ytr_arm_z'][0] - (L['nut_u_z'] + w('m5_kopf_d') / 2.0),
         2.0)
    for n in L['ytr_y']:
        pt = (L['ytr_wand_x'][0] - w('m5_kopf_h'), L['ytr_m5_y'][n],
              L['nut_u_z'])
        d, wer = bauraum.freier_korridor(pt, 'x', -1, INBUS_FREI_D / 2.0,
                                         rahmen)
        p.ok('   M5 am Traeger {} von aussen frei{}'.format(
            n, '' if wer is None else '  [' + wer + ']'),
             999.0 if d == float('inf') else d, WERKZEUG_LAENGE)
    p.ok('Traeger Y: Rand neben der M5',
         w('ytr_b') / 2.0 - w('ytr_versatz') - w('m5_durchgang') / 2.0, 2.0)
    p.ok('Traeger Y: M5-Kopf neben der Laschenschraube',
         2.0 * w('ytr_versatz') - (w('m5_kopf_d') + w('m3_kopf_d')) / 2.0,
         2.0)
    p.ok('Lasche Y: Luft zur Wand des Traegers',
         L['ytr_wand_x'][0] - L['ywanne_lasche_x'][1], 0.5)
    p.ok('Laschenschraube: Kopf zwischen Wanne und Traeger',
         L['ytr_wand_x'][0] - L['ywanne_x'][1] - w('m3_kopf_d'), 1.0)
    # W13 in der Seitennut geht an jedem Traeger kurz aus der Nut und unter
    # der Wand durch (oben sitzen Arm und Wanne, vor der Wand der M5-Kopf);
    # darunter ist bis zum Tisch frei.
    p.info('W13 unter der Wand des Traegers: Wand endet ueber der '
           'Unterkante des 2040', L['ytr_wand_z'][0] - L['rahmen_z0'])
    # Schrauben der Wanne Y von oben (Laschen, Endstueck 180): mit dem
    # Portal in der Mitte sind Schlitten, Kettenhalter Y und Kette weg
    ym0 = w('yk_gelenk_y')
    yb0_ = (frei + L['yk_fest'] + ym0) / 2.0
    ueber = mit_portal + [
        bauraum.Quader('Y-Kette Obertrum', xk[0], xk[1],
                       ym0 - w('endstueck_l'), yb0_, *L['yk_ober_z']),
        bauraum.Quader('Y-Kette Bogen', xk[0], xk[1], yb0_, yb0_ + ra,
                       L['yk_unter_z'][0], L['yk_ober_z'][1])]
    zb1 = L['ywanne_boden_z'][1]
    for text_, pkt in (
            ('Laschen', [(x, y, zb1 + w('m3_kopf_h'))
                         for x, y in L['ywanne_laschen']]),
            ('Endstueck 180', [(x, y, zb1 + w('endstueck_platte')
                                + w('m3_scheibe_h') + w('m3_kopf_h'))
                               for x, y in L['yk_fest_loecher']])):
        d, wer = float('inf'), None
        for pt in pkt:
            d_, wer_ = bauraum.freier_korridor(pt, 'z', +1,
                                               INBUS_FREI_D / 2.0, ueber)
            if d_ < d:
                d, wer = d_, wer_
        p.ok('Wanne Y: {} von oben frei (Portal in der Mitte){}'.format(
            text_, '' if wer is None else '  [' + wer + ']'),
             999.0 if d == float('inf') else d, WERKZEUG_LAENGE)
    yb0 = L['ywanne_binder'][0][1]
    p.ok('Binderschlitze Wanne Y hinter dem Endstueck 180',
         (L['yk_fest'] - w('endstueck_l')) - (yb0 + w('khy_binder_b') / 2.0),
         1.0)
    p.ok('Binderschlitze Wanne Y hinter dem Traeger (darunter frei)',
         L['ytr_y']['Festpunkt'][0] - (yb0 + w('khy_binder_b') / 2.0), 1.0)

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


def hohe_zone_y(w, TL, d_schiene):
    """Ab hier (nach hinten) ist ueber dem Fach in der Mitte mehr Hoehe
    frei: vor die Traegerplatte am hinteren Schienenende, mit Luft."""
    return TL['traeger_y0'] - d_schiene - w('luft_bau')


def luft_hinten(w, L, TL, feste_th, bewegte_th, ziele, zonen=None):
    """Kleinste Luft zwischen festen Quadern `ziele` (Rahmenkoordinaten wie
    Abschnitt 14) und allem, was sich bewegt: das Portal ueber die hintere
    Haelfte des Y-Wegs bis ans Schienenende, der Toolhead dazu ueber X und
    Z. Stellungen, in denen der Toolhead ein 2060 durchdringen muesste, gibt
    es nicht — mit Z unten steht das 2060 davor — und werden uebersprungen.

    Liefert ((luft, ziel, teil, dy), tief). tief: je Zone aus `zonen`
    ({name: (xb, y_vorn, y_hinten)}) der tiefste bewegte Punkt (z, teil) in
    |X| < xb, y_hinten < Y < y_vorn."""
    d_schiene, _, d_hinten, _ = y_weg(w, L, TL, feste_th, bewegte_th)
    lang_fest = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    portal = [q for q in bauraum.portal_bauraeume(w, L)[0]
              if not any(q.name.startswith(t) for t in lang_fest)]
    quer = quer_quader(w, L)

    def vor(q, dy):
        return bauraum.Quader(q.name, q.x[0], q.x[1], q.y[0] + dy,
                              q.y[1] + dy, q.z[0], q.z[1], q.art)

    # nur die hintere Haelfte des Wegs: von vorn kommt nichts bis hierher.
    # Hinter das Schienenende kommt der Wagen nicht, auch wenn das 2060
    # weiter hinten liegt (seit Portal Rev. 14 so).
    dys = sorted(set([-d_schiene, -min(d_hinten, d_schiene), 0.0]
                     + [-d_schiene + 2.5 * i
                        for i in range(int(d_schiene / 2.5) + 1)]))
    xs = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / 20.0
          for i in range(21)]
    zs = [TL['zc_min'] + (TL['zc_max'] - TL['zc_min']) * j
          / (Z_SCHRITTE - 1.0) for j in range(Z_SCHRITTE)]
    engste = (float('inf'), None, None, None)
    tief = {}
    for dy in dys:
        teile_p = [vor(q, dy) for q in portal]
        for xw in xs:
            fx = [vor(q.verschoben(0.0, xw), dy) for q in feste_th]
            for zc in zs:
                th = fx + [vor(q.verschoben(zc, xw), dy)
                           for q in bewegte_th]
                if any(t.abstand(k) < 0 for t in th for k in quer):
                    continue
                for q in th + teile_p:
                    for z in ziele:
                        d = q.abstand(z)
                        if d < engste[0]:
                            engste = (d, z.name, q.name, dy)
                    for zn, (xb, yv, yh) in (zonen or {}).items():
                        if (q.x[0] < xb and -xb < q.x[1] and q.y[0] < yv
                                and yh < q.y[1]
                                and q.z[0] < tief.get(zn, (1e9,))[0]):
                            tief[zn] = (q.z[0], q.name)
    return engste, tief


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


def y_weg_riemen(pm, L, dy):
    """Riemenweg einer Seite aus Portal.py (y_riemen_weg), Portal dy aus
    der Mitte verschoben."""
    return pm.y_riemen_weg(L, dy)


def nut_durchgang(w, L, t, teil):
    """Wo der Trum t der Wagenseite (aus y_riemen_weg) durch die Oeffnung
    der inneren oberen Nut laeuft: der Bereich, in dem ein Teil des Riemens
    zwischen Lippe und Seitenflaeche der 2040 liegt, als Abstand vom
    Profilende. Die Wirklinie ist gerade; Zahnspitzen und Ruecken liegen
    senkrecht zum Trum riemen_innen bzw. riemen_aussen daneben."""
    (uk, yk), (tu, tv) = t['klemme'], t['tangente']
    c = math.cos(math.radians(t['schraeg']))
    innen, aussen = L['riemen_innen'] / c, L['riemen_aussen'] / c
    flaeche = w('rahmen_b') / 2.0
    lippe = flaeche - w('nut_lippe')
    y0, y1 = L['rahmen_y']
    ende = y1 if teil == 'vorn' else y0

    def y_bei(u):
        return yk + (u - uk) * (tv - yk) / (tu - uk)

    ya, yb = sorted((y_bei(lippe - aussen), y_bei(flaeche + innen)))
    lo, hi = max(ya, min(yk, tv), y0), min(yb, max(yk, tv), y1)
    if lo >= hi:
        u_ende = uk + (tu - uk) * (ende - yk) / (tv - yk)
        return ('aussen an der Nut vorbei (Zahnspitzen am Profilende '
                '{:.1f} mm neben der Seitenflaeche)'.format(
                    u_ende - innen - flaeche))
    a, b = sorted((abs(ende - lo), abs(ende - hi)))
    return 'in der Nutoeffnung {:.1f} bis {:.1f} mm vom Profilende'.format(
        b, a)


def y_halter_quader(w, L):
    """Y-Motorhalter (Platte, Joch, Schenkel, Fuehrungswaende), Motor und
    Ritzel beider Seiten als Quader in Rahmenkoordinaten (Portal in der
    Mitte). Motor und Ritzel als Huelle ueber ihren ganzen Spannweg."""
    H = L['ymh']
    R = L['R']
    ye, zu = L['rahmen_y'][1], L['rahmen_z0']
    fl = w('motor_flansch') / 2.0
    rr = w('ritzel_flansch_d') / 2.0
    hb = H['halbe_breite']
    za, ze = zu + H['halter_z0'], zu + H['halter_z1']
    q = []
    for s in (-1, 1):
        n = 'links' if s < 0 else 'rechts'
        xm = s * R
        teile = [('Y-Motorplatte', (xm - hb, xm + hb),
                  (ye, ye + H['platte_y1']),
                  (zu + H['platte_z0'], zu + H['platte_z1'])),
                 ('Y-Joch', (xm - hb, xm + hb), (ye, ye + H['joch_y1']),
                  (za, ze)),
                 ('Y-Motor', (xm - fl, xm + fl),
                  (ye + H['motor_y_min'] - fl, ye + H['motor_y_max'] + fl),
                  (zu + H['motor_z0'], zu + H['motor_flansch_z'])),
                 ('Y-Ritzel', (xm - rr, xm + rr),
                  (ye + H['motor_y_min'] - rr, ye + H['motor_y_max'] + rr),
                  (zu + H['ritzel_z0'], zu + H['welle_z1']))]
        for sx, seite_ in ((-1, 'links'), (1, 'rechts')):
            teile += [('Y-Schenkel ' + seite_,
                       tuple(sorted((xm + sx * H['wange_x0'],
                                     xm + sx * H['wange_x1']))),
                       (ye + H['wange_y0'], ye), (za, ze)),
                      ('Y-Fuehrung ' + seite_,
                       tuple(sorted((xm + sx * H['fuehrung_x0'],
                                     xm + sx * hb))),
                       (ye, ye + H['platte_y1']), (za, ze))]
        for name, x, y, z in teile:
            q.append(bauraum.Quader('{} {}'.format(name, n), x[0], x[1],
                                    y[0], y[1], z[0], z[1]))
    return q


if __name__ == '__main__':
    sys.exit(main())
