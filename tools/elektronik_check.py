#!/usr/bin/env python3
"""Rechnerische Pruefung des Elektronikgehaeuses (fusion/Elektronik) — laeuft
ohne Fusion.

Importiert Elektronik.py, Portal.py und ToolheadZ.py mit gestubbtem
adsk-Modul und prueft: Abgleich der Rahmenmasse mit Portal.py, Lage im Fach
hinter dem hinteren 2060, Freiraum gegen Portal und Toolhead ueber den ganzen
Weg, Montage mit M5 in Hammermuttern, Werkzeugzugang, Uno und Stapelhoehe,
Verteiler (Buchse, Schalter, Wandler, Wago), Waende, Druckbarkeit und den
Kabelkanal. Gibt am Ende die Stueckliste aus.

    python3 tools/elektronik_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

ELEKTRONIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                          'fusion', 'Elektronik', 'Elektronik.py')
WERKZEUG_LAENGE = 20.0        # kuerzester nutzbarer Inbus-Schenkel
BETT = 250.0                  # Bambu Lab A1: 256, mit Rand
# Einbaumasse der Kaufteile hinter der Rueckwand [w]
BUCHSE_KOERPER_D = 11.0       # Einbaubuchse M8: Mutter und Loetfahnen
SCHALTER_KOERPER = (21.0, 15.0, 20.0)   # KCD1: breit, hoch, tief


def elektronik_quader(ew, EL):
    """Gehaeuse, Deckel, Luefter, Dome und M5-Koepfe als Quader
    (Rahmenkoordinaten wie Portal.py)."""
    Q = bauraum.Quader
    fm, h = EL['luefter_mitte'], ew('luefter') / 2.0
    q = [Q('Kasten', *EL['geh_x'], *EL['geh_y'], *EL['geh_z']),
         Q('Montageplatte', *EL['platte_x'], *EL['platte_y'],
           *EL['platte_z']),
         Q('Kanalboden', *EL['geh_x'], EL['geh_y'][1], EL['platte_y'][0],
           EL['geh_z'][0], EL['boden_z']),
         Q('Deckel', *EL['deckel_x'], *EL['geh_y'], *EL['deckel_z']),
         Q('Luefter', fm[0] - h, fm[0] + h, fm[1] - h, fm[1] + h,
           *EL['luefter_z'])]
    r = ew('dom_d') / 2.0
    for i, (x, y) in enumerate(EL['dome']):
        q.append(Q('Dom {}'.format(i + 1), x - r, x + r, y - r, y + r,
                   *EL['geh_z']))
    r = ew('m5_kopf_d') / 2.0
    for x, z in EL['m5']:
        q.append(Q('M5-Kopf', x - r, x + r,
                   EL['platte_y'][0] - ew('m5_kopf_h'), EL['platte_y'][0],
                   z - r, z + r))
    return q


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    em = bauraum.modul_laden(ELEKTRONIK, 'elektronik')
    ew, EL = em.w, em.lage()
    p = Pruefung()
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, d_hinten, _ = portal_check.y_weg(w, L, TL, feste_th,
                                                        bewegte_th)
    fach = portal_check.elektronikfach(w, L)
    teile = elektronik_quader(ew, EL)

    # ------------------------------------------------------------------
    p.titel('1) Abgleich Elektronik.py <-> Portal.py (Rahmen)')
    for name in ('y_schienen_abstand', 'rahmen_b', 'rahmen_h', 'quer_h',
                 'quer_laenge', 'nut_oben', 'nut_v_t', 'nut_b', 'nut_t',
                 'nut_kammer_b', 'nut_kammer_t', 'kern_d', 'm3_durchgang',
                 'm5_durchgang', 'm5_kopf_d', 'm5_kopf_h', 'insert_m3_d',
                 'insert_m3_t', 'inbus_frei_d', 'luft_bau', 'fase_fuss'):
        p.ja('{} gleich in beiden Skripten'.format(name),
             abs(ew(name) - w(name)) < 1e-9,
             '   ({} / {})'.format(ew(name), w(name)))
    for text, a, b in (
            ('hintere Stirnseite der 2040', ew('rahmen_y0'),
             L['rahmen_y'][0]),
            ('Unterkante der 2040', ew('rahmen_z0'), L['rahmen_z0']),
            ('Rueckseite hinteres 2060', ew('quer_y1'),
             L['quer_y_hinten'][0]),
            ('Tisch (Unterkante 2060)', EL['tisch_z'], L['quer_z'][0]),
            ('Fach unten', EL['fach_z'][0], fach.z[0]),
            ('Fach oben', EL['fach_z'][1], fach.z[1])):
        p.ja('{} gleich'.format(text), abs(a - b) < 1e-9,
             '   ({} / {})'.format(a, b))

    # ------------------------------------------------------------------
    p.titel('2) Lage im Fach hinter dem hinteren 2060')
    gx, gy, gz = EL['geh_x'], EL['geh_y'], EL['geh_z']
    p.info('Kasten Breite', gx[1] - gx[0])
    p.info('       Tiefe', gy[1] - gy[0])
    p.info('       Hoehe (ohne Deckel)', gz[1] - gz[0])
    y_tr = portal_check.hohe_zone_y(w, TL, d_schiene)
    for q in teile:
        if q.name == 'Luefter':
            continue
        d = min(q.x[0] - fach.x[0], fach.x[1] - q.x[1], q.y[0] - fach.y[0],
                fach.y[1] - q.y[1] + (ew('platte_dicke') + 3.0
                                      if q.name in ('Montageplatte',
                                                    'M5-Kopf') else 0.0),
                q.z[0] - fach.z[0], fach.z[1] - q.z[1])
        p.ok('{} im Fach'.format(q.name), d, 0.0)
    lf = next(q for q in teile if q.name == 'Luefter')
    p.info('Luefter ragt ueber das Fach hinaus bis Z', lf.z[1])
    p.ok('   dafuer steht er in der Mitte (|X| <= 225)',
         225.0 - max(abs(lf.x[0]), abs(lf.x[1])), 0.0)
    p.ok('   und weit genug hinter dem 2060 (ab Y {:.1f})'.format(y_tr),
         y_tr - lf.y[1], 0.0)
    p.info('Kasten hinter der Rueckseite des 2060', ew('quer_y1') - gy[1])

    # ------------------------------------------------------------------
    p.titel('3) Freiraum gegen Portal und Toolhead (ganzer Weg)')
    engste, _ = portal_check.luft_hinten(w, L, TL, feste_th, bewegte_th,
                                         teile)
    p.ok('{} <-> {} (Portal {:+.1f})'.format(engste[1], engste[2],
                                              engste[3]),
         engste[0], w('luft_bau'))
    # feste Teile des Rahmens: 2060 (die Platte liegt an), 2040, Schienen,
    # Riemen
    rahmen = portal_check.quer_quader(w, L) + [
        q for q in bauraum.portal_bauraeume(w, L)[0]
        if q.name.startswith(('Y-Schiene', 'Rahmen 2040', 'Y-Riemen',
                              'Y-Ruecklauf'))]
    for q in teile:
        d = min(q.abstand(r) for r in rahmen)
        if q.name in ('Montageplatte', 'M5-Kopf'):
            continue
        p.ok('{} frei vom Rahmen'.format(q.name), d, 1.0)
    platte = next(q for q in teile if q.name == 'Montageplatte')
    hinten = next(r for r in rahmen if r.name == '2060 hinten')
    p.ok('Montageplatte liegt an der Rueckseite des 2060 an',
         -abs(platte.y[1] - hinten.y[0]), -0.01)

    # ------------------------------------------------------------------
    p.titel('4) Montage: 4 x M5 in Hammermuttern der Rueckseite des 2060')
    pd = ew('platte_dicke')
    for x, z in EL['m5']:
        p.ja('M5 bei X {:+.1f} sitzt auf einer Nutmitte (Z {:+.0f})'.format(
            x, z), min(abs(z - n) for n in EL['quer_nut_z']) < 1e-6)
    s = EL['m5_schraube']
    p.ok('M5x{:.0f}: Gewinde in der Hammermutter'.format(s),
         s - pd - 1.8, 3.5)
    p.ok('M5x{:.0f}: steht nicht auf dem Nutgrund auf'.format(s),
         (ew('nut_t') + ew('nut_kammer_t')) - (s - pd), 0.0)
    rk = ew('m5_kopf_d') / 2.0
    p.ok('Kopf innerhalb der Platte (seitlich)',
         min(min(x - EL['platte_x'][0], EL['platte_x'][1] - x)
             for x, _ in EL['m5']) - rk, 0.5)
    p.ok('Kopf innerhalb der Platte (unten)',
         min(z for _, z in EL['m5']) - rk - EL['platte_z'][0], 0.5)
    p.ok('Kopf innerhalb der Platte (oben)',
         EL['platte_z'][1] - max(z for _, z in EL['m5']) - rk, 0.5)
    p.ok('Kopf neben dem Kasten',
         min(min(abs(x - gx[0]), abs(x - gx[1])) for x, _ in EL['m5']) - rk,
         3.0)

    # ------------------------------------------------------------------
    p.titel('5) Werkzeugzugang')
    boxen = [q for q in teile if q.name not in ('Montageplatte', 'M5-Kopf',
                                                'Kanalboden')] + rahmen
    schlecht = (float('inf'), None)
    for x, z in EL['m5']:
        pt = (x, EL['platte_y'][0] - ew('m5_kopf_h'), z)
        d, wer = bauraum.freier_korridor(pt, 'y', -1,
                                         ew('inbus_frei_d') / 2.0, boxen)
        if d < schlecht[0]:
            schlecht = (d, wer)
    p.ok('M5 der Platte: Inbus von hinten neben dem Kasten'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)
    schlecht = (float('inf'), None)
    for x, y in EL['dome']:
        pt = (x, y, EL['deckel_z'][1] + 3.0)
        d, wer = bauraum.freier_korridor(pt, 'z', +1,
                                         ew('inbus_frei_d') / 2.0,
                                         [q for q in rahmen
                                          if q.name != '2060 vorn'])
        if d < schlecht[0]:
            schlecht = (d, wer)
    p.ok('Deckelschrauben: Inbus von oben (Portal nach vorn gefahren)'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)
    p.info('Uno-Schrauben: vor dem Aufstecken des Shields anziehen — '
           'danach liegt das Shield darueber')

    # ------------------------------------------------------------------
    p.titel('6) Uno, Stapel, Luefter [w]')
    ux, uy = EL['uno_x'], EL['uno_y']
    ix, iy = EL['innen_x'], EL['innen_y']
    p.ok('Uno links neben der Wand', ux[0] - ix[0], 3.0)
    p.ok('Uno vorn vor der Wand', iy[1] - uy[1], 5.0)
    p.ok('USB-Buchse vor der Rueckwand (steht {:.1f} ueber)'.format(
        ew('uno_buchse_vor')), (uy[0] - ew('uno_buchse_vor')) - iy[0], 0.5)
    p.ok('Fenster deckt die Buchsen (links)',
         ux[0] - EL['fenster_x'][0], 0.5)
    p.ok('Fenster deckt die Buchsen (rechts)',
         EL['fenster_x'][1] - (ux[0] + ew('uno_buchse_b')), 0.5)
    p.ok('Fenster deckt die Buchsen (oben)',
         EL['fenster_z'][1] - (EL['uno_z1'] + ew('uno_buchse_h')), 1.0)
    p.ok('Fenster endet ueber dem Boden',
         EL['fenster_z'][0] - EL['boden_z'], 3.0)
    p.ok('Fenster: Bruecke oben', EL['fenster_x'][1] - EL['fenster_x'][0],
         50.0, '<=')
    r = ew('uno_steg_d') / 2.0
    for i, (x, y) in enumerate(EL['uno_loecher']):
        p.ok('Stehbolzen {} frei von den Waenden'.format(i + 1),
             min(x - r - ix[0], ix[1] - x - r, y - r - iy[0],
                 iy[1] - y - r), 1.0)
    p.ok('Stehbolzen: Wand um das Kernloch',
         (ew('uno_steg_d') - ew('uno_schraube_d')) / 2.0, 1.5)
    p.ok('Stehbolzen: M3x8 greift (8 - Platine)',
         8.0 - ew('uno_pcb'), 5.0)
    p.ok('Stapel bis unter den Deckel (Luft ueber den Kuehlkoerpern)',
         EL['deckel_z'][0] - EL['stapel_z1'], 5.0)
    p.ok('Deckellippe ueber dem Stapel', (EL['deckel_z'][0] - ew('lippe_h'))
         - EL['stapel_z1'], 2.0)
    fm, lh = EL['luefter_mitte'], ew('luefter') / 2.0
    p.ok('Luefter ueber dem Fach des Uno (links)', fm[0] - lh - ix[0], 0.0)
    p.ok('Luefter ueber dem Fach des Uno (rechts)',
         EL['vert_x'][0] - (fm[0] + lh), 0.0)
    p.ok('Luefter auf dem Deckel', min(fm[0] - lh - EL['deckel_x'][0],
                                       EL['deckel_x'][1] - fm[0] - lh,
                                       fm[1] - lh - gy[0],
                                       gy[1] - fm[1] - lh), 3.0)
    p.ok('Luefter frei von den Deckelschrauben',
         min(max(abs(x - fm[0]), abs(y - fm[1])) - lh
             - ew('m3_durchgang') / 2.0 for x, y in EL['dome']), 3.0)

    # ------------------------------------------------------------------
    p.titel('7) Verteiler: Buchse, Schalter, Wandler, Wago [w]')
    vx = EL['vert_x']
    p.ok('Verteiler breit genug fuer 3 Wago nebeneinander',
         (vx[1] - vx[0]) - ew('wago_b'), 1.0)
    bx, ez = EL['buchse_x'], EL['eingang_z']
    sx = EL['schalter_x']
    sb, sh, sr = ew('schalter_b') / 2.0, ew('schalter_h') / 2.0, \
        ew('schalter_rand')
    p.ok('Buchse ueber dem Boden', ez - ew('buchse_d') / 2.0 - EL['boden_z'],
         3.0)
    p.ok('Buchse unter der Oberkante', gz[1] - (ez + ew('buchse_d') / 2.0),
         10.0)
    p.ok('Buchse rechts neben dem USB-Fenster',
         bx - ew('buchse_d') / 2.0 - EL['fenster_x'][1], 5.0)
    p.ok('Schalterrand ueber dem Boden', ez - sh - sr - EL['boden_z'], 1.0)
    p.ok('Schalterrand unter der Oberkante', gz[1] - (ez + sh + sr), 3.0)
    p.ok('Schalter rechts neben der Buchse (Koerper)',
         (sx - SCHALTER_KOERPER[0] / 2.0) - (bx + BUCHSE_KOERPER_D / 2.0),
         3.0)
    p.ok('Schalterrand innerhalb der Rueckwand (rechts)',
         ix[1] - (sx + sb + sr), 2.0)
    p.ok('Wand am Schalter (KCD1: 0,8 bis 2 mm) [w]',
         ew('schalter_wand'), 2.0, '<=')
    tiefe = max(SCHALTER_KOERPER[2], 15.0)
    p.ok('Buchse und Schalter reichen nicht bis zum Wandler',
         ew('eingang_tiefe') - tiefe + (ew('geh_wand')
                                        - ew('schalter_wand')), 0.5)
    rt = ew('binder_t') / 2.0
    for x, y in EL['binder']:
        p.ok('Binderschlitz X {:+.1f} im Verteiler'.format(x),
             min(x - ew('binder_b') / 2.0 - vx[0],
                 vx[1] - x - ew('binder_b') / 2.0), 1.5)
        if y < EL['wandler_y'][0]:           # hinterer Schlitz
            p.ok('   neben Buchse und Schalter (X {:+.1f})'.format(x),
                 min(abs(x - bx) - BUCHSE_KOERPER_D / 2.0,
                     abs(x - sx) - SCHALTER_KOERPER[0] / 2.0)
                 - ew('binder_b') / 2.0, 1.0)
            p.ok('   vor der Rueckwand', y - rt - iy[0], 1.0)
    p.ok('Wago-Klemmen vor den Binderschlitzen',
         EL['wago_y'][0] - (max(y for _, y in EL['binder']) + rt), 1.0)
    p.ok('Wago-Klemmen: Platz vorn fuer die Draehte',
         iy[1] - EL['wago_y'][1], 8.0)

    # ------------------------------------------------------------------
    p.titel('8) Waende, Dome, Lueftung, Druck')
    p.ok('Dom: Wand um den Einsatz', (ew('dom_d') - ew('insert_m3_d')) / 2.0,
         2.0)
    p.ok('Dom endet innen an der Wand (ragt nicht hinein)',
         -(EL['dome'][0][0] + ew('dom_d') / 2.0 - ix[0]), 0.0)
    p.ok('Deckelschraube M3x8: Gewinde im Einsatz',
         8.0 - ew('deckel_dicke'), 4.0)
    p.ok('Einsatz kuerzer als der Dom', gz[1] - gz[0] - ew('insert_m3_t'),
         10.0)
    yd = sorted(y for _, y in EL['dome'])
    lue = EL['lueftung_y']
    p.ok('Lueftungsschlitze neben den Domen',
         min(abs(y - d) for y in lue for d in yd) - ew('dom_d') / 2.0
         - ew('lueftung_b') / 2.0, 2.0)
    p.ok('Lueftung unter der Oberkante', gz[1] - EL['lueftung_z'][1], 3.0)
    p.ok('Kabelausschnitt links neben den Domen',
         min(abs(EL['kabel_links_y'] - d) for d in yd)
         - ew('kabel_links_b') / 2.0 - ew('dom_d') / 2.0, 2.0)
    gross = max(EL['platte_x'][1] - EL['platte_x'][0],
                EL['platte_y'][1] - gy[0], EL['platte_z'][1] - gz[0])
    p.ok('Gehaeuse (mit Platte): groesste Kante', gross, BETT, '<=')
    p.ok('Deckel: groesste Kante', EL['deckel_x'][1] - EL['deckel_x'][0],
         BETT, '<=')

    # ------------------------------------------------------------------
    p.titel('9) Kabelkanal zwischen Platte und Kasten')
    p.ok('Kanal breit genug', ew('geh_abstand'), 10.0)
    p.ok('Rippen unter dem Kabelausschnitt vorn',
         EL['kabel_z0'] - EL['rippe_z1'], 5.0)
    p.ok('Kanal ueber den Rippen hoch genug',
         EL['platte_z'][1] - EL['rippe_z1'], 20.0)

    # ------------------------------------------------------------------
    p.titel('10) Stueckliste Elektronikgehaeuse')
    for zeile in (
            '1x Gehaeuse, 1x Deckel (PETG); Bohrlehre_Uno (PLA, zum Pruefen)',
            '4x M5x{:.0f} Zylinderkopf + 4x Hammermutter M5 Nut 6 '
            '(Platte -> Rueckseite hinteres 2060)'.format(EL['m5_schraube']),
            '4x M3x8 (Uno -> Stehbolzen, schneidet sein Gewinde selbst)',
            '4x M3x8 Zylinderkopf + 4x Messing-Einsatz M3 Ø5 (Deckel)',
            '4x M3x16 + 4x M3-Mutter (Luefter -> Deckel)',
            '1x Luefter 40 x 40 x 10, 24 V',
            '1x Einbaubuchse 5,5 x 2,1 mm mit M8-Gewinde (Loch {:.1f})'
            .format(ew('buchse_d')),
            '1x Wippschalter KCD1, Ausschnitt {:.1f} x {:.1f}'.format(
                ew('schalter_b'), ew('schalter_h')),
            '1x Abwaertswandler 24 -> 12 V, >= 3 A; 2x Kabelbinder',
            '3x Wago 221-415 (vorhanden), doppelseitiges Klebeband'):
        p.info(zeile)

    # ------------------------------------------------------------------
    p.titel('11) Statische Pruefung der Schluessel in Elektronik.py')
    quelle = open(ELEKTRONIK, encoding='utf-8').read()
    fehlt_m = sorted(set(re.findall(r"\bw\('([^']+)'\)", quelle))
                     - set(em.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(EL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(em.MASSE)
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('12) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in em.hinweise_bauen(EL, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
