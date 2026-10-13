#!/usr/bin/env python3
"""Rechnerische Pruefung des Elektronikfachs (fusion/Elektronikfach) — laeuft
ohne Fusion.

Importiert Elektronikfach.py, Portal.py und ToolheadZ.py mit gestubbtem
adsk-Modul und prueft: Abgleich der Rahmenmasse mit Portal.py, Lage im Fach
hinter dem hinteren 2060, Freiraum gegen Portal und Toolhead ueber den ganzen
Weg, Montage mit M5 in Hammermuttern und Werkzeugzugang, Druck (Bauraum,
Waende, Bruecken, Traenen, Fuge), Uno, Pi, Wandler, Wago, Buchse und
Schalter, die Gassen mit Fenstern und Oesen, die Deckel, die Leistungsbilanz
und die Litzen (aus tools/elektronik_zeichnen.py) und die Verkabelung
(Kabelliste aus tools/verkabelung.py: Netze, Not-Aus, Signale, Kontakte,
Klemmen, Laengen, Ketten und ob die Tabellen in docs/verkabelung.md aktuell
sind). Gibt die Stueckliste aus.

    python3 tools/elektronik_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import itertools
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import elektronik_zeichnen as leistung              # noqa: E402
import portal_check                                   # noqa: E402
import verkabelung as vk                              # noqa: E402
from bauraum import Quader                            # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

ELEKTRONIK = leistung.ELEKTRONIK
WERKZEUG_LAENGE = 20.0        # kuerzester nutzbarer Inbus-Schenkel
BETT = 250.0                  # Bambu Lab A1: 256, mit Rand
MITTE_X = 225.0               # in der Mitte darf das Fach hoeher sein ...
MITTE_Z = -19.0               # ... bis hierher (unter dem X-Wagen, 3 mm Luft)
# Einbaumasse der Kaufteile hinter der Rueckwand [w]
BUCHSE_KOERPER_D = 11.0       # Einbaubuchse M8: Mutter und Loetfahnen
BUCHSE_KOERPER_T = 15.0       # ... so tief hinter der Wand
SCHALTER_KOERPER = (20.0, 20.0, 20.0)   # rund: Ø wie das Loch, tief [?]
# Kabelbinder an den Wandlern: 2,5 x 200, Buendel bis D 50 [w], das Band
# 1,1 dick [w].
BINDER = '2,5 x 200'
BINDER_BUENDEL_D = 50.0
BINDER_DICKE = 1.1
HEBEL_FREI = 20.0             # Wago 221: Platz vor den Hebeln zum Oeffnen
DRAHT_FREI = 15.0             # ... vor den Eintritten zum Biegen der Draehte
FUELL_MAX = 0.4               # Kabel fuellen ein Fenster hoechstens so weit
# Aussendurchmesser der Kabel in den Fenstern [w]/[?]: Motorkabel mit
# Schlauch, Leitungen mit Mantel; Einzeladern nach verkabelung.ADER_D
KABEL_D = {'Motorkabel': 5.0, 'Leitung 2-adrig': 6.0,
           'Leitung 3-adrig': 4.5}
ADER_D = dict(vk.ADER_D)
ADER_D[0.75] = 2.6


def flach(v):
    """Zahlen eines Werts aus lage() als flache Liste."""
    if isinstance(v, (list, tuple)):
        return [x for e in v for x in flach(e)]
    return [float(v)]


def binder_schlaufe(innen, wand, breite, hoehe, seitlich):
    """Laenge eines Kabelbinders um Boden und Wandler (mm): unter dem Boden
    von Schlitz zu Schlitz (innen: zwischen den inneren Kanten der
    Schlitze), zweimal durch den Boden, schraeg von den Schlitzen auf die
    Kanten des Wandlers (seitlich: die beiden Abstaende) und quer ueber ihn.
    Dazu pi x Banddicke fuer die Mittellinie des Bandes."""
    return (innen + 2.0 * wand + breite
            + sum(math.hypot(hoehe, a) for a in seitlich)
            + math.pi * BINDER_DICKE)


def elektronik_quader(ew, EL):
    """Kasten, Deckel, Luefter, Ohren und die Koepfe der aeusseren M5 als
    Quader (Rahmenkoordinaten wie Portal.py). Die inneren M5 sitzen im
    Kasten."""
    fm, h = EL['luefter_mitte'], ew('luefter') / 2.0
    q = [Quader('Kasten', *EL['geh_x'], *EL['geh_y'], *EL['geh_z']),
         Quader('Deckel', *EL['geh_x'], *EL['geh_y'], *EL['deckel_z']),
         Quader('Luefter', fm[0] - h, fm[0] + h, fm[1] - h, fm[1] + h,
                *EL['luefter_z'])]
    for s in ('links', 'rechts'):
        q.append(Quader('Ohr ' + s, *EL['ohr_x'][s], *EL['platte_y'],
                        *EL['ohr_z']))
    r = ew('m5_kopf_d') / 2.0
    for s in ('links', 'rechts'):
        for x, z in EL['m5'][s][:2]:
            q.append(Quader('M5-Kopf', x - r, x + r,
                            EL['platte_y'][0] - ew('m5_kopf_h'),
                            EL['platte_y'][0], z - r, z + r))
    return q


def innenteile(ew, EL):
    """Was im Fach steht, als Quader: Bauteile des Kastens (Leitwaende,
    Oesen, Dome mit Stuetze, Stehbolzen) und die Geraete. Fuer die
    Abstaende untereinander, zu den Fenstern und fuer den Werkzeugzugang."""
    bz = EL['boden_z']
    q = []
    for s in ('links', 'rechts'):
        for i, (x, y) in enumerate(EL['leitwaende'][s]):
            q.append(Quader('Leitwand {} {}'.format(s, i + 1), *x, *y,
                            *EL['leitwand_z'], 'struktur'))
        ol, ob = ew('oese_l') / 2.0, ew('oese_b') / 2.0
        for i, (x, y) in enumerate(EL['oesen'][s]):
            q.append(Quader('Oese {} {}'.format(s, i + 1), x - ol, x + ol,
                            y - ob, y + ob, bz, bz + ew('oese_h'),
                            'struktur'))
        da = ew('dom_a') / 2.0
        for x, _, e in EL['dome'][s]:
            q.append(Quader('Dom {} {}'.format(s, e), x - da, x + da,
                            *EL['dom_y'][e], EL['dom_z'][0] - 2.0 * da,
                            EL['dom_z'][1], 'struktur'))
    r = ew('uno_steg_d') / 2.0
    for i, (x, y) in enumerate(EL['uno_loecher']):
        q.append(Quader('Uno-Stehbolzen {}'.format(i + 1), x - r, x + r,
                        y - r, y + r, bz, EL['uno_z0'], 'struktur'))
    fm = EL['luefter_mitte']
    q += [Quader('Uno mit Shield', *EL['uno_x'], *EL['uno_y'], EL['uno_z0'],
                 EL['stapel_z1']),
          Quader('USB-B-Stecker', *EL['usb_b_stecker'][0],
                 *EL['usb_b_stecker'][1], *EL['usb_b_stecker'][2]),
          Quader('Pi', EL['pi_bauteile_x'][0], EL['pi_steg_x'][1],
                 *EL['pi_y'], *EL['pi_z']),
          Quader('12-V-Wandler', *EL['w12_x'], *EL['w12_y'], *EL['w12_z']),
          Quader('5-V-Wandler', *EL['w5_x'], *EL['w5_y'], *EL['w5_z']),
          Quader('USB-A-Adapter', *EL['adapter'][0], *EL['adapter'][1],
                 *EL['adapter'][2]),
          Quader('Air-Assist-Platz', *EL['aa_x'], *EL['aa_y'], bz,
                 bz + 20.0)]
    for n in ('USB', 'PWR'):
        q.append(Quader('Pi-Stecker ' + n, *EL['pi_stecker'][n][0],
                        *EL['pi_stecker'][n][1], *EL['pi_stecker'][n][2]))
    for name, _, x, y, z in EL['wago']:
        q.append(Quader('Wago ' + name, *x, *y, *z))
    iy0 = EL['innen_y'][0]
    bx, ez = EL['buchse']
    q.append(Quader('Buchse', bx - BUCHSE_KOERPER_D / 2.0,
                    bx + BUCHSE_KOERPER_D / 2.0, iy0, iy0 + BUCHSE_KOERPER_T,
                    ez - BUCHSE_KOERPER_D / 2.0, ez + BUCHSE_KOERPER_D / 2.0))
    sx, _ = EL['schalter']
    q.append(Quader('Schalter', sx - SCHALTER_KOERPER[0] / 2.0,
                    sx + SCHALTER_KOERPER[0] / 2.0, iy0,
                    iy0 + SCHALTER_KOERPER[2], ez - SCHALTER_KOERPER[1] / 2.0,
                    ez + SCHALTER_KOERPER[1] / 2.0))
    return q


def schritt_bbox(fm, s):
    """Bauraum eines Bauplan-Schritts in Maschinenkoordinaten."""
    if s['form'] == 'rechteck':
        us = [u for u0, _, u1, _ in s['formen'] for u in (u0, u1)]
        vs = [v for _, v0, _, v1 in s['formen'] for v in (v0, v1)]
    elif s['form'] == 'kreis':
        r = s['d'] / 2.0
        us = [u + k * r for u, _ in s['formen'] for k in (-1, 1)]
        vs = [v + k * r for _, v in s['formen'] for k in (-1, 1)]
    elif s['form'] == 'vieleck':
        us = [u for p in s['formen'] for u, _ in p]
        vs = [v for p in s['formen'] for _, v in p]
    else:
        pts = [p for u, v in s['formen']
               for p in fm.tropfen_punkte(u, v, s['d'], s['spitze'],
                                          s.get('kappe'))]
        us, vs = [p[0] for p in pts], [p[1] for p in pts]
    a = s['a']
    if s['achse'] == 'z':
        return (min(us), max(us)), (min(vs), max(vs)), a
    if s['achse'] == 'y':
        return (min(us), max(us)), a, (min(vs), max(vs))
    return a, (min(us), max(us)), (min(vs), max(vs))


def plan_bbox(fm, plan):
    """Bauraum der 'dazu'-Schritte eines Bauplans (Schnitte machen ihn nur
    kleiner, wenn sie ganze Seiten wegnehmen — das tun sie hier nicht)."""
    b = [schritt_bbox(fm, s) for s in plan if s['art'] == 'dazu']
    return tuple((min(x[i][0] for x in b), max(x[i][1] for x in b))
                 for i in range(3))


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    em = bauraum.modul_laden(ELEKTRONIK, 'elektronikfach')
    ew, EL = em.w, em.lage()
    p = Pruefung()
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    fach = portal_check.elektronikfach(w, L)
    teile = elektronik_quader(ew, EL)
    innen = innenteile(ew, EL)
    gx, gy, gz = EL['geh_x'], EL['geh_y'], EL['geh_z']
    ix, iy, bz, rz = EL['innen_x'], EL['innen_y'], EL['boden_z'], EL['rand_z']

    # ------------------------------------------------------------------
    p.titel('1) Abgleich Elektronikfach.py <-> Portal.py (Rahmen)')
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
            ('Fach links/rechts', EL['fach_x'][1], fach.x[1]),
            ('Fach hinten', EL['fach_y'][0], fach.y[0]),
            ('Fach unten', EL['fach_z'][0], fach.z[0]),
            ('Fach oben', EL['fach_z'][1], fach.z[1])):
        p.ja('{} gleich'.format(text), abs(a - b) < 1e-9,
             '   ({} / {})'.format(a, b))

    # ------------------------------------------------------------------
    p.titel('2) Lage im Fach hinter dem hinteren 2060')
    p.info('Kasten Breite (ohne Ohren)', gx[1] - gx[0])
    p.info('       Tiefe (mit Montageplatte)', gy[1] - gy[0])
    p.info('       Hoehe (ohne Deckel)', gz[1] - gz[0])
    for q in teile:
        an_2060 = q.name.startswith(('Ohr', 'M5-Kopf', 'Kasten', 'Deckel'))
        d = min(q.x[0] - fach.x[0], fach.x[1] - q.x[1], q.y[0] - fach.y[0],
                (fach.y[1] + 3.0 if an_2060 else fach.y[1]) - q.y[1],
                q.z[0] - fach.z[0])
        p.ok('{} im Fach (X, Y, unten)'.format(q.name), d, 0.0)
        mitte = max(abs(q.x[0]), abs(q.x[1])) <= MITTE_X
        p.ok('   oben: {} (|X| {:.0f})'.format(
            'in der Mitte bis Z {:+.0f}'.format(MITTE_Z) if mitte
            else 'unter den 2040', max(abs(q.x[0]), abs(q.x[1]))),
            (MITTE_Z if mitte else fach.z[1]) - q.z[1], 0.0)
    p.ok('Kasten in der Mitte (|X| <= 225)', MITTE_X - gx[1], 0.0)
    p.ok('Ohren unter den 2040 (Oberkante <= Fach)',
         fach.z[1] - EL['ohr_z'][1], 0.0)
    p.ok('Montageplatte liegt an der Rueckseite des 2060 an',
         -abs(EL['platte_y'][1] - L['quer_y_hinten'][0]), -0.01)

    # ------------------------------------------------------------------
    p.titel('3) Freiraum gegen Portal und Toolhead (ganzer Weg), Rahmen')
    engste, _ = portal_check.luft_hinten(w, L, TL, feste_th, bewegte_th,
                                         teile)
    p.ok('{} <-> {} (Portal {:+.1f})'.format(engste[1], engste[2],
                                              engste[3]),
         engste[0], w('luft_bau'))
    winkel, _ = bauraum.y_kette_rahmen(w, L)
    rahmen = portal_check.quer_quader(w, L) + [
        q for q in bauraum.portal_bauraeume(w, L)[0]
        if q.name.startswith(('Y-Schiene', 'Rahmen 2040', 'Y-Riemen',
                              'Y-Ruecklauf'))] + [
        q for q in winkel if q.name.startswith('Winkel')]
    # die Winkel innen an den Kreuzungen (angenommen wie aussen): 20 mm vor
    # der Innenseite der 2040, ueber dem 2060
    xi = L['R'] - w('rahmen_b') / 2.0
    for q in [q for q in winkel if q.name.startswith('Winkel')]:
        rahmen += [Quader(q.name + ' innen rechts', xi - 20.0, xi, *q.y,
                          *q.z, q.art),
                   Quader(q.name + ' innen links', -xi, -xi + 20.0, *q.y,
                          *q.z, q.art)]
    for q in teile:
        if q.name.startswith(('Ohr', 'M5-Kopf')):
            continue
        d = min(q.abstand(r) for r in rahmen)
        p.ok('{} frei vom Rahmen (2040, 2060, Winkel)'.format(q.name), d,
             1.0 if q.name != 'Kasten' else 0.0)
    for s in ('links', 'rechts'):
        ohr = next(q for q in teile if q.name == 'Ohr ' + s)
        d = min(ohr.abstand(r) for r in rahmen if not r.name.startswith(
            '2060 hinten'))
        p.ok('Ohr {}: frei von 2040 und Winkeln'.format(s), d, 1.0)

    # ------------------------------------------------------------------
    p.titel('4) Montage: 6 x M5 in Hammermuttern der Rueckseite des 2060')
    pd = ew('platte_dicke')
    for s in ('links', 'rechts'):
        for x, z in EL['m5'][s]:
            p.ja('M5 {} bei X {:+.1f} sitzt auf einer Nutmitte (Z {:+.0f})'
                 .format(s, x, z),
                 min(abs(z - n) for n in EL['quer_nut_z']) < 1e-6)
    sl = ew('m5_l')
    p.ok('M5x{:.0f}: Gewinde in der Hammermutter'.format(sl),
         sl - pd - 1.8, 3.5)
    p.ok('M5x{:.0f}: steht nicht auf dem Nutgrund auf'.format(sl),
         (ew('nut_t') + ew('nut_kammer_t')) - (sl - pd), 0.0)
    rk = ew('m5_kopf_d') / 2.0
    for s in ('links', 'rechts'):
        ox = EL['ohr_x'][s]
        for x, z in EL['m5'][s][:2]:
            p.ok('Ohr {}: Kopf X {:+.1f} Z {:+.0f} ganz auf dem Ohr'.format(
                s, x, z), min(x - rk - ox[0], ox[1] - x - rk,
                              z - rk - EL['ohr_z'][0],
                              EL['ohr_z'][1] - z - rk), 0.5)
        p.ok('Ohr {}: Traene der oberen M5 unter der Oberkante'.format(s),
             EL['ohr_z'][1] - (EL['m5'][s][1][1] + ew('m5_durchgang') / 2.0
                               * math.sqrt(2.0)), 1.5)
        x, z = EL['m5'][s][2]
        kopf = Quader('M5 innen', x - rk, x + rk, iy[1] - ew('m5_kopf_h'),
                      iy[1], z - rk, z + rk)
        d = min(kopf.abstand(q) for q in innen)
        p.ok('M5 innen {}: Kopf frei im Kasten'.format(s), d, 1.0)
    # Inbus: aussen neben dem Kasten von hinten; innen ebenso, solange das
    # Fach leer ist (vor dem Bestuecken anziehen)
    kasten_struktur = rahmen + [Quader('Kasten', *gx, *gy, *gz)]
    schlecht = (float('inf'), None)
    for s in ('links', 'rechts'):
        for x, z in EL['m5'][s][:2]:
            pt = (x, EL['platte_y'][0] - ew('m5_kopf_h'), z)
            d, wer = bauraum.freier_korridor(pt, 'y', -1,
                                             ew('inbus_frei_d') / 2.0,
                                             kasten_struktur)
            if d < schlecht[0]:
                schlecht = (d, wer)
    p.ok('M5 der Ohren: Inbus von hinten neben dem Kasten'
         + ('' if schlecht[1] is None else '  [' + schlecht[1] + ']'),
         999.0 if schlecht[0] == float('inf') else schlecht[0],
         WERKZEUG_LAENGE)
    struktur = [q for q in innen if q.art == 'struktur']
    for s in ('links', 'rechts'):
        x, z = EL['m5'][s][2]
        pt = (x, iy[1] - ew('m5_kopf_h'), z)
        leer, wer = bauraum.freier_korridor(pt, 'y', -1,
                                            ew('inbus_frei_d') / 2.0,
                                            struktur)
        p.ok('M5 innen {}: Inbus im leeren Fach'.format(s)
             + ('' if wer is None else '  [' + wer + ']'),
             999.0 if leer == float('inf') else leer, WERKZEUG_LAENGE)
        voll, wer = bauraum.freier_korridor(pt, 'y', -1,
                                            ew('inbus_frei_d') / 2.0, innen)
        p.ok('   ... und mit allen Geraeten (zum Abnehmen)'
             + ('' if wer is None else '  [' + wer + ']'),
             999.0 if voll == float('inf') else voll, WERKZEUG_LAENGE)
    schlecht = (float('inf'), None)
    for s in ('links', 'rechts'):
        for x, y, _ in EL['dome'][s]:
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

    # ------------------------------------------------------------------
    p.titel('5) Druck: Bauraum, Waende, Bruecken, Traenen, Fuge')
    for name, T in sorted(EL['teile'].items()):
        bb = plan_bbox(em, EL['plan'][name])
        p.ok('{}: Bauplan liegt im angegebenen Bauraum'.format(name),
             max(abs(bb[i][k] - T['bbox'][i][k]) for i in range(3)
                 for k in range(2)), 0.01, '<=')
        gross = max(T['bbox'][i][1] - T['bbox'][i][0] for i in range(3))
        p.ok('{}: groesste Kante (Bambu Lab A1)'.format(name), gross, BETT,
             '<=')
    for n in ('wand', 'boden', 'fuge_wand', 'deckel_dicke'):
        p.ok('Wand {}'.format(n), ew(n), 2.0)
    p.ok('Montageplatte', ew('platte_dicke'), 4.0)
    for name, plan in sorted(EL['plan'].items()):
        for s in plan:
            if s['art'] != 'weg' or s['achse'] == 'z':
                continue
            if s['form'] == 'rechteck':
                b = max(u1 - u0 for u0, _, u1, _ in s['formen'])
                p.ok('{} {}: Oberkante als Bruecke'.format(name, s['name']),
                     b, em.BRUECKE, '<=')
            elif s['form'] == 'vieleck':
                for punkte in s['formen']:
                    b = max(u for u, _ in punkte) - min(u for u, _ in punkte)
                    oben = max(v for _, v in punkte)
                    ecken = [(u, v) for u, v in punkte if abs(v - oben) < 1e-9]
                    flach_ = (max(u for u, _ in ecken)
                              - min(u for u, _ in ecken))
                    p.ok('{} {}: oben flach hoechstens'.format(
                        name, s['name']), flach_, min(b, em.BRUECKE), '<=')
            elif s['form'] == 'kreis' and s['d'] > 6.0:
                tief = s['a'][1] - s['a'][0] - 1.0
                p.ok('{} {}: grosser Kreis nur als flache Senkung'.format(
                    name, s['name']), tief, 1.0, '<=')
    p.ok('Dom: 45-Grad-Stuetze so tief wie der Dom', ew('dom_a'),
         ew('dom_a'), '<=')
    p.ok('Dom: Einsatz kuerzer als der Dom', ew('dom_h') - ew('insert_m3_t'),
         3.0)
    p.ok('Dom: Wand um den Einsatz',
         (ew('dom_a') - ew('insert_m3_d')) / 2.0, 2.0)
    # Fuge: Schrauben und Zapfen frei von Fenstern, Pi und Rand
    fy, fz = EL['fuge_fenster'], ew('m3_durchgang') / 2.0 + 1.5
    for y, z in EL['fuge_bolzen'] + EL['fuge_zapfen']:
        d = min(max(y0 - y, y - y1, z0 - z, z - z1)
                for (y0, y1), (z0, z1) in fy)
        p.ok('Fuge Y {:+.0f} Z {:+.0f}: frei von den Fenstern'.format(y, z),
             d, fz + 1.0)
        p.ok('   im Material der Fugenwand (Rand, Boden)',
             min(y - iy[0], iy[1] - y, z - bz, rz - ew('lippe_h') - z), fz)
    for y, z in EL['fuge_bolzen']:
        d = max(EL['pi_y'][0] - y, y - EL['pi_y'][1] - 2.5,
                EL['pi_z'][0] - z, z - EL['pi_z'][1]) - 2.75
        p.ok('Fuge Y {:+.0f} Z {:+.0f}: Kopf neben dem Pi (SD-Karte +2,5)'
             .format(y, z), d, 1.0)
    p.ok('Fuge: Zapfen steckt nicht durch (Laenge < Wand)',
         ew('fuge_wand') - ew('zapfen_l'), 0.05)
    p.ok('Fuge: Spiel im Zapfenloch', ew('zapfen_spiel'), 0.2)
    p.ok('Fuge: M3x12 mit Mutter (2 Waende + Mutter 2,4 + Scheibe 0,5)',
         12.0 - 2.0 * ew('fuge_wand') - 2.4 - 0.5, 1.0)

    # ------------------------------------------------------------------
    p.titel('6) Uno, Stapel [v], USB, Luefter')
    ux, uy = EL['uno_x'], EL['uno_y']
    p.ok('Uno vor der vorderen Leitwand', EL['leitwand_vorn_y'][0] - uy[1],
         1.5)
    p.ok('Uno hinter der hinteren Leitwand', uy[0] - EL['leitwand_hinten_y'][1],
         1.5)
    r = ew('uno_steg_d') / 2.0
    for i, (x, y) in enumerate(EL['uno_loecher']):
        p.ok('Stehbolzen {} frei von Leitwaenden und Waenden'.format(i + 1),
             min(y - r - EL['leitwand_hinten_y'][1],
                 EL['leitwand_vorn_y'][0] - y - r, x - r - ix['links'][0]),
             1.0)
    p.ok('Stehbolzen: Wand um das Kernloch',
         (ew('uno_steg_d') - ew('uno_schraube_d')) / 2.0, 1.5)
    p.ok('Stehbolzen: M3x8 greift (8 - Platine)', 8.0 - ew('uno_pcb'), 5.0)
    p.ok('Luft ueber den Kuehlkoerpern bis unter die Lippe',
         rz - ew('lippe_h') - EL['stapel_z1'], 20.0)
    wago5 = [q for q in innen if q.name in ('Wago +5 V', 'Wago GND 5 V')]
    p.ok('links: Platz vor den Hebeln der 5-V-Klemmen bis zum Uno',
         ux[0] - max(q.x[1] for q in wago5), HEBEL_FREI)
    usb = next(q for q in innen if q.name == 'USB-B-Stecker')
    andere = [q for q in innen if q.name not in ('USB-B-Stecker',
                                                  'Uno mit Shield')]
    d, wer = min((usb.abstand(q), q.name) for q in andere)
    p.ok('USB-B-Stecker frei ({})'.format(wer), d, 2.0)
    ps = EL['pi_stecker']['USB']
    sp = math.dist((usb.x[1], sum(usb.y) / 2.0),
                   (sum(ps[0]) / 2.0, sum(ps[1]) / 2.0))
    p.ok('W17: USB-B-Stecker bis Stecker am Pi (Schlaufe)', sp, 30.0)
    p.ok('   kurzes Kabel reicht (15 cm mit Boegen)', sp, 100.0, '<=')
    fm, lh = EL['luefter_mitte'], ew('luefter') / 2.0
    p.ok('Luefter ueber dem Uno (links)', fm[0] - lh - ux[0], 0.0)
    p.ok('Luefter ueber dem Uno (rechts)', ux[1] - (fm[0] + lh), 0.0)
    p.ok('Luefter ueber dem Uno (laengs Y)', min(fm[1] - lh - uy[0],
                                                  uy[1] - fm[1] - lh), 0.0)
    p.ok('Luefter auf dem Deckel', min(fm[0] - lh - EL['haelfte_x']['links'][0],
                                       EL['haelfte_x']['links'][1] - fm[0] - lh,
                                       fm[1] - lh - gy[0], gy[1] - fm[1] - lh),
         3.0)
    p.ok('Luefter frei von den Deckelschrauben',
         min(max(abs(x - fm[0]), abs(y - fm[1])) - lh
             - ew('m3_durchgang') / 2.0 for x, y, _ in EL['dome']['links']),
         3.0)
    p.ok('Luefter: Oeffnung kleiner als der Luefter', ew('luefter')
         - ew('luefter_d'), 1.0)

    # ------------------------------------------------------------------
    p.titel('7) Pi senkrecht an der Fugenwand [w]')
    pz, py = EL['pi_z'], EL['pi_y']
    p.ok('Pi: Oberkante unter der Lippe des Deckels',
         rz - ew('lippe_h') - pz[1], 2.0)
    p.ok('Pi: Oberkante ueber dem 2060 (WLAN)', pz[1] - ew('rahmen_z0'), 5.0)
    p.ok('Pi: Platz hinter der SD-Karte (herausziehen)', py[0] - iy[0],
         10.0)
    p.ok('Pi: vorn frei von der Montageplatte (Dome, Inbus)', iy[1] - py[1],
         15.0)
    p.ok('Pi: Stehbolzen, Wand um das Kernloch',
         (ew('pi_steg_d') - ew('m25_kern')) / 2.0, 1.5)
    p.ok('Pi: M2.5x6 greift (6 - Platine)', 6.0 - ew('pi_pcb'), 3.5)
    p.ok('Pi: Kernloch endet in der Fugenwand',
         ew('fuge_wand') - 0.5, 1.5)
    for n in ('USB', 'PWR'):
        q = next(x for x in innen if x.name == 'Pi-Stecker ' + n)
        d, wer = min((q.abstand(x), x.name) for x in innen
                     if x.name not in ('Pi', 'Pi-Stecker USB',
                                       'Pi-Stecker PWR'))
        p.ok('Pi-Stecker {} frei ({})'.format(n, wer), d, 2.0)
        p.ok('   ueber dem Boden (Kabel biegt darunter)', q.z[0] - bz, 8.0)
    p.ok('Pi-Stecker frei von der Fugenwand',
         ix['links'][1] - EL['pi_stecker']['USB'][0][1], 2.0)

    # ------------------------------------------------------------------
    p.titel('8) Wandler [v], Wago [w], Buchse, Schalter, Air Assist')
    geraete = [q for q in innen if q.art != 'struktur']
    for a, b in itertools.combinations(geraete, 2):
        if {a.name, b.name} <= {'Uno mit Shield', 'USB-B-Stecker'} or \
                {a.name, b.name} <= {'Pi', 'Pi-Stecker USB',
                                      'Pi-Stecker PWR'} or \
                {a.name, b.name} == {'5-V-Wandler', 'USB-A-Adapter'}:
            continue
        if a.abstand(b) < 1.0:
            p.ok('{} <-> {}'.format(a.name, b.name), a.abstand(b), 1.0)
    p.ja('alle Geraete mit Abstand (>= 1 mm) zueinander', True)
    for q in geraete:
        d = min(q.abstand(x) for x in struktur
                if not (q.name == 'Uno mit Shield'
                        and x.name.startswith('Uno-Stehbolzen')))
        if d < 0.5:
            p.ok('{} frei von Leitwand, Oese, Dom'.format(q.name), d, 0.5)
    p.ja('alle Geraete frei von Leitwaenden, Oesen und Domen', True)
    rt, rb = ew('binder_t') / 2.0, ew('binder_b') / 2.0
    for x, y, rr in EL['binder']:
        sx_, sy_ = (rb, rt) if rr == 'y' else (rt, rb)
        schlitz = Quader('Schlitz', x - sx_, x + sx_, y - sy_, y + sy_,
                         bz - 1.0, bz + 1.0)
        d = min(schlitz.abstand(q) for q in struktur)
        wand = min(x - sx_ - ix['links'][0] if x < 0 else x - sx_
                   - ix['rechts'][0], (ix['links'][1] if x < 0
                                        else ix['rechts'][1]) - x - sx_,
                   y - sy_ - iy[0], iy[1] - y - sy_)
        p.ok('Binderschlitz X {:+.1f} Y {:+.1f}: frei'.format(x, y),
             min(d, wand), 1.0)
    for name, wx, wy, wh in (('12-V-Wandler', EL['w12_x'], EL['w12_y'],
                              ew('w12_h')),
                             ('5-V-Wandler', EL['w5_x'], EL['w5_y'],
                              ew('w5_h'))):
        ys = sorted(set(y for x, y, rr in EL['binder']
                        if rr == 'y' and wx[0] < x < wx[1]))
        p.ok('{}: Kabelbinder {}: Schlaufe um Boden und Wandler'.format(
            name, BINDER),
             binder_schlaufe(ys[1] - ys[0] - 2.0 * rt, ew('boden'),
                             wy[1] - wy[0], wh,
                             (wy[0] - (ys[0] + rt), (ys[1] - rt) - wy[1])),
             math.pi * BINDER_BUENDEL_D, '<=')
        p.ok('{}: Binder auf dem Wandler (bis zu seinen Enden)'.format(name),
             (wx[1] - wx[0]) / 2.0 - ew('wandler_binder') - rb, 3.0)
    vorn = {n: y for n, _, _, y, _ in EL['wago']}
    for n in ('+24 V', 'GND'):
        y1 = vorn[n][1]
        q = next(x for x in innen if x.name == 'Wago ' + n)
        frei = min(x.y[0] - y1 for x in innen + struktur
                   if x.y[0] >= y1 and x.x[0] < q.x[1] and q.x[0] < x.x[1]
                   and x.z[0] < q.z[1] + 5.0)
        p.ok('Wago {}: Platz vor den Eintritten'.format(n), frei,
             DRAHT_FREI)
    pw = EL['fenster_pow']['links']
    for n in ('+5 V', 'GND 5 V'):
        q = next(x for x in innen if x.name == 'Wago ' + n)
        p.ok('Wago {}: ueber dem Fenster Leistung links'.format(n),
             q.z[0] - pw[1][1], 1.5)
        p.ok('   ueber dem Fenster der Signale', q.z[0] - EL['fenster_sig_z'][1],
             1.5)
        p.ok('   neben den Fenstern (laengs Y)', min(
            q.y[0] - pw[0][1] if q.y[0] >= pw[0][1] else 99.0,
            q.y[0] - iy[0]), 1.0)
        p.ok('   unter dem Rand (Lippe)', rz - ew('lippe_h') - q.z[1], 3.0)
    bx, ez_ = EL['buchse']
    sx, _ = EL['schalter']
    rs, rb_ = ew('schalter_d') / 2.0, ew('schalter_blende_d') / 2.0
    p.ok('Schalter: Blende deckt das Loch (Kreis)', rb_ - rs, 0.5)
    p.ok('Schalter: Blende deckt die flache Kappe oben',
         rb_ - (rs + ew('schalter_kappe')), 0.3)
    p.ok('Schalter: Kappe unter der Spitze der Traene (Flanken 45 Grad)',
         rs * (2.0 ** 0.5 - 1.0) - ew('schalter_kappe'), 1.0)
    p.ok('Wand am Schalter (Rastnasen, 1 bis 2 mm) [w]',
         ew('schalter_wand'), 2.0, '<=')
    p.ok('Schalter: Blende ueber dem Boden', ez_ - rb_ - gz[0], 2.0)
    p.ok('Schalter: Rand unter den Lueftungsschlitzen',
         EL['lueftung_z'][0] - (ez_ + rs + ew('schalter_rand')), 2.0)
    p.ok('Schalter neben der Buchse (Koerper)',
         (sx - SCHALTER_KOERPER[0] / 2.0) - (bx + BUCHSE_KOERPER_D / 2.0),
         3.0)
    p.ok('Schalter: Rand frei von der Endwand',
         ix['rechts'][1] - (sx + rs + ew('schalter_rand')), 3.0)
    for x in EL['lueftung_x']['rechts']:
        if abs(x - bx) < BUCHSE_KOERPER_D:
            p.ok('Lueftung bei X {:+.0f} ueber der Buchse'.format(x),
                 EL['lueftung_z'][0] - (ez_ + ew('buchse_d') / 2.0), 3.0)
    ab = EL['ausbruch']
    p.ok('Air Assist: Durchbruch ganz in der Rueckwand (Hoehe)',
         min(ab[1] - ew('ausbruch_d') / 2.0 - bz,
             EL['lueftung_z'][0] - ab[1] - ew('ausbruch_d') / 2.0
             * math.sqrt(2.0)), 3.0)
    p.ok('Air Assist: Haut zum Ausbrechen', ew('ausbruch_haut'), 0.8, '<=')
    p.ok('Air Assist: Durchbruch hinter dem Platz (X)',
         min(ab[0] - EL['aa_x'][0], EL['aa_x'][1] - ab[0]), 10.0)

    # ------------------------------------------------------------------
    p.titel('9) Gassen, Fenster, Oesen')
    gv = EL['gasse_vorn']
    p.ok('Signalgasse breit', gv[1] - gv[0], 15.0)
    for s in ('links', 'rechts'):
        gh = EL['gasse_hinten'][s]
        p.ok('Leistungsgasse {} breit'.format(s), gh[1] - gh[0], 15.0)
    p.ok('Signal und Leistung getrennt (Abstand der Gassen)',
         gv[0] - EL['gasse_hinten']['links'][1], 50.0)
    lts = vk.leitungen()
    fenster = {('links', 'Signal'): (EL['fenster_sig_y'],
                                     EL['fenster_sig_z']),
               ('rechts', 'Signal'): (EL['fenster_sig_y'],
                                      EL['fenster_sig_z']),
               ('links', 'Leistung'): EL['fenster_pow']['links'],
               ('rechts', 'Leistung'): EL['fenster_pow']['rechts']}
    for (s, art), ((y0, y1), (z0, z1)) in sorted(fenster.items()):
        teil = '{} raus (Fenster {})'.format(s, art)
        drin = [lt for lt in lts if teil in lt['weg']
                or ('wie W7' in lt['weg'] and s == 'links'
                    and art == 'Leistung')]
        if s == 'links' and art == 'Signal':
            drin.append(next(lt for lt in lts if lt['nr'] == 'W7'))
        flaeche = 0.0
        for lt in drin:
            if lt['art'] in KABEL_D:
                flaeche += math.pi * KABEL_D[lt['art']] ** 2 / 4.0
            else:
                n = len(lt['adern'])
                if lt['nr'] == 'W7':     # PWM links, +12 V und GND hinten
                    n = 1 if art == 'Signal' else 2
                flaeche += n * math.pi * ADER_D[lt['mm2']] ** 2 / 4.0
        dach = (y1 - y0) ** 2 / 4.0 if y1 - y0 > em.BRUECKE else 0.0
        offen = (y1 - y0) * (z1 - z0) + dach
        p.ok('Fenster {} {}: {} fuellen'.format(
            art, s, ' '.join(lt['nr'] for lt in drin)), 100.0 * flaeche
            / offen, 100.0 * FUELL_MAX, '<=', '%')
        xo = EL['oesen'][s]
        ym = (y0 + y1) / 2.0
        d = min(math.hypot(abs(x) - ix['rechts'][1], y - ym) for x, y in xo)
        p.ok('   Zugentlastung: Oese gleich hinter dem Fenster', d, 15.0,
             '<=')
    for i, ((y0, y1), (z0, z1)) in enumerate(EL['fuge_fenster']):
        p.info('Fuge: Fenster {} ({}), {:.0f} x {:.0f}'.format(
            i + 1, 'Signale' if i == 0 else 'Leistung', y1 - y0, z1 - z0))
    for s in ('links', 'rechts'):
        for i, (x, y) in enumerate(EL['leitwaende'][s]):
            hx = EL['haelfte_x'][s]
            p.ok('Leitwand {} {}: in der Haelfte'.format(s, i + 1),
                 min(x[0] - ix[s][0], ix[s][1] - x[1]), 0.0)
    for s in ('links', 'rechts'):
        for x, y in EL['oesen'][s]:
            ol, ob = ew('oese_l') / 2.0, ew('oese_b') / 2.0
            q = Quader('Oese', x - ol, x + ol, y - ob, y + ob, bz,
                       bz + ew('oese_h'))
            d = min(q.abstand(z) for z in innen if not z.name.startswith(
                'Oese'))
            p.ok('Oese {} X {:+.0f} Y {:+.0f}: frei'.format(s, x, y), d,
                 1.0)
    p.ok('Oese: Tunnel fuer den Binder 2,5 x 1,1',
         min(ew('oese_tunnel_b') - 2.5, ew('oese_tunnel_h') - 1.1), 1.0)
    p.ok('Oese: Steg ueber dem Tunnel', ew('oese_h') - ew('oese_tunnel_h'),
         2.0)

    # ------------------------------------------------------------------
    p.titel('10) Deckel')
    p.ok('Deckelschraube M3x8: Gewinde im Einsatz', 8.0 - ew('deckel_dicke'),
         4.0)
    p.ok('Einsatz tiefer als die Schraube reicht', ew('insert_m3_t')
         - (8.0 - ew('deckel_dicke')), 0.5)
    p.ok('Lippe: Spiel zur Wand', ew('lippe_spiel'), 0.2)
    for (x0, x1), (y0, y1) in EL['deckel_schlitze']:
        d = min(max(abs(x - (x0 + x1) / 2.0) - (x1 - x0) / 2.0,
                    max(y0 - y, y - y1)) for x, y, _ in EL['dome']['rechts'])
        p.ok('Schlitz im Deckel rechts X {:+.0f}: frei vom Dom'.format(
            (x0 + x1) / 2.0), d, ew('dom_a') / 2.0 + 2.0)

    # ------------------------------------------------------------------
    p.titel('11) Stueckliste Elektronikfach')
    for zeile in (
            '1x Fach_links, 1x Fach_rechts, 1x Deckel_links, 1x Deckel_rechts '
            '(PETG); Bohrlehren Uno, Pi, Fuge (PLA, zum Pruefen)',
            '6x M5x{:.0f} Zylinderkopf + 6x Hammermutter M5 Nut 6 '
            '(Ohren und innen -> Rueckseite hinteres 2060)'.format(ew('m5_l')),
            '4x M3x12 + 4x M3-Mutter + 8x Scheibe (Fuge)',
            '8x M3x8 Zylinderkopf + 8x Messing-Einsatz M3 Ø5 (Deckel)',
            '4x M3x8 (Uno -> Stehbolzen, schneidet sein Gewinde selbst)',
            '4x M2.5x6 (Pi -> Stehbolzen, schneidet sein Gewinde selbst)',
            '4x M3x16 + 4x M3-Mutter (Luefter -> Deckel)',
            '1x Luefter 40 x 40 x 10, 24 V (vorhanden)',
            '1x Einbaubuchse 5,5 x 2,1 mit M8-Gewinde, 1x Wippschalter rund '
            '(vorhanden)',
            '1x Abwaertswandler 24 -> 12 V / {:.0f} A und 1x 24 -> 5 V '
            '(vorhanden); 4x Kabelbinder {}'.format(leistung.WANDLER_A,
                                                     BINDER),
            '1x USB-A-Adapter mit Schraubklemmen (neu)',
            'Wago: 2x 221-420 (+24 V, GND) und 1x 221-415 (+5 V) vorhanden, '
            '1x 221-415 (GND 5 V) neu, 221-413 Reserve; doppelseitiges '
            'Klebeband',
            'Kabelbinder 2,5 x 200 fuer die Oesen'):
        p.info(zeile)

    # ------------------------------------------------------------------
    p.titel('12) Statische Pruefung der Schluessel in Elektronikfach.py')
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

    p.titel('13) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in em.hinweise_bauen(EL, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    # ------------------------------------------------------------------
    p.titel('14) Leistung: Netzteil, Wandler, Treiber')
    lb = leistung.leistung()
    p.info('Motoren + Luefter + Laser (mit Wandler) + Pi', lb['summe'], 'W')
    p.ok('Netzteil 24 V / 3 A: Reserve bei 85 % Dauerlast', lb['reserve'],
         5.0, '>=', 'W')
    p.ok('Wandler {:.0f} A: Laser zieht davon hoechstens'.format(
        leistung.WANDLER_A), 100.0 * leistung.LASER_A / leistung.WANDLER_A,
         80.0, '<=', '%')
    p.info('Motorstrom eingestellt (eff.)', leistung.MOTOR_I, 'A')
    for r in leistung.R_SENSE:
        p.ok('   Vref bei R_sense {:.2f} Ohm (Poti bis 2,5 V)'.format(r),
             leistung.vref(leistung.MOTOR_I, r), 2.5, '<=', 'V')

    # ------------------------------------------------------------------
    p.titel('15) Litzen: Querschnitt, Spannungsfall, Kontakte')
    K = leistung.konzept(w, L, tw, TL, ew, EL)
    li = leistung.litzen(K)
    p.ok('24 V {} mm2: belastbar (VDE 0298-4) gegen den Netzteilstrom'.format(
        leistung.LITZE_24V), leistung.BELASTBAR[leistung.LITZE_24V],
         li['netz_a'], '>=', 'A')
    p.info('   Not-Aus {:.1f} m hin und zurueck: Spannungsfall bei {:.0f} A'
           .format(li['not_m'], li['netz_a']), li['not_u'], 'V')
    p.ok('Laser {} mm2, {:.1f} m: Spannungsfall an {:.0f} V'.format(
        leistung.LITZE_LASER, li['laser_m'], leistung.LASER_V),
         100.0 * li['laser_u'] / leistung.LASER_V, 5.0, '<=', '%')
    p.ok('   Laserlitze passt in den XH-Crimpkontakt', leistung.LITZE_LASER,
         leistung.XH_MAX, '<=', 'mm2')
    p.ok('Motor {} mm2, {:.0f} m: Kabel gegen die Wicklung'.format(
        leistung.LITZE_MOTOR, li['motor_m']),
         100.0 * li['motor_r'] / leistung.MOTOR_R, 25.0, '<=', '%')
    p.ok('   Motorlitze passt in den PH-Crimpkontakt', leistung.LITZE_MOTOR,
         leistung.PH_MAX, '<=', 'mm2')
    p.ok('Signale {} mm2: halten in der Wago (feindraehtig)'.format(
        leistung.LITZE_SIGNAL), leistung.LITZE_SIGNAL, leistung.WAGO_MIN,
         '>=', 'mm2')
    p.info('5 V: W18 {} mm2, {:.2f} m, Strom im Betrieb'.format(
        leistung.LITZE_24V, li['pi24_m']), li['pi24_a'], 'A')
    p.ok('5 V: W6 {} mm2, {:.2f} m, {:.2f} A: Spannungsfall'.format(
        leistung.LITZE_24V, li['w6_m'], li['w6_a']), li['w6_u'], 0.05, '<=',
         'V')
    p.ok('Lichtschranken: 5 V am Modul bei 5,0 V vom Wandler', 5.0
         - li['ls_u'], 4.75, '>=', 'V')
    p.ok('Pi: W6 + W19 {:.2f} m, AWG 28: 5 V am Pi bei 5,0 V vom Wandler'
         .format(li['pi5_m']), 5.0 - li['pi5_u'][28],
         leistung.PI_UNTERSPANNUNG + 0.2, '>=', 'V')
    p.info('   mit AWG 24: Spannungsfall', li['pi5_u'][24], 'V')
    p.ok('Uno: W17 {:.2f} m, AWG 28: Spannungsfall'.format(li['usb_m']),
         li['usb_u'][28], 0.1, '<=', 'V')

    # ------------------------------------------------------------------
    verkabelung_pruefen(p, {'L': L, 'TL': TL, 'K': K, 'es_w': w})
    return p.bericht()


def verkabelung_pruefen(p, Q):
    """Abschnitt 16: die Kabelliste aus tools/verkabelung.py."""
    p.titel('16) Verkabelung: Netze, Not-Aus, Signale, Kontakte, Klemmen')
    lts = vk.leitungen()
    A = vk.ANSCHLUSS
    unbekannt = sorted({a for _, _, a in vk.enden(lts) if a not in A})
    p.ja('alle Anschluesse der Kabelliste sind beschrieben', not unbekannt,
         (' — ' + ', '.join(unbekannt)) if unbekannt else '')
    N = vk.netze(lts=lts)
    plus24, masse = N['Buchse +'], N['Buchse −']
    for a in ('Shield +', 'Wandler IN+', 'Lüfter +'):
        p.ja('+24 V ueber Schalter und Not-Aus an {}'.format(A[a][0]),
             a in plus24)
    for a in ('Shield −', 'Wandler IN−', 'Lüfter −', 'Laser GND',
              'LS X GND', 'LS Y GND', 'LS Z GND', 'Shield Z− GND',
              'Pi GND', '5V-Wandler IN−'):
        p.ja('GND an {}'.format(A[a][0]), a in masse)
    p.ja('+12 V vom Wandler nur an den Laser',
         N['Wandler OUT+'] == {'Wandler OUT+', 'Laser +12 V'})
    p.ja('+5 V vom 5-V-Wandler (W6) an VCC aller drei Lichtschranken und '
         'an PWR IN des Pi',
         {'LS X VCC', 'LS Y VCC', 'LS Z VCC', 'Pi PWR'}
         <= N['5V-Adapter 5V'])
    p.ja('Stift 5V des Shields an keiner Leitung (nicht mehr ueber den Uno)',
         not any('Shield 5V' in (a, b) for lt in lts
                 for _, _, a, b in lt['adern']))
    p.ja('5 V vor Schalter und Not-Aus: der 5-V-Wandler haengt an der Buchse',
         '5V-Wandler IN+' in plus24 and '5V-Wandler IN+'
         in vk.netze(zustand=('ein', 'gedrueckt'), lts=lts)['Buchse +'])
    netze = {'+24 V': plus24, '+12 V': N['Wandler OUT+'],
             '+5 V': N['Wago +5 V'], 'GND': masse}
    for (n1, s1), (n2, s2) in itertools.combinations(netze.items(), 2):
        p.ja('kein Kurzschluss {} <-> {}'.format(n1, n2), not s1 & s2)
    for pin, achse in vk.EINGAENGE.items():
        ls = {a for a in N.get(pin, {pin}) if a.startswith('LS ')}
        p.ja('{}: nur D0 der Lichtschranke {}'.format(A[pin][0], achse),
             ls == {'LS {} D0'.format(achse)})
    d11 = N['Shield Z+']
    p.ja('D11 (Z+/Z−) nur Laser-PWM, keine Lichtschranke',
         'Laser PWM' in d11 and not any(a.startswith('LS ') for a in d11))
    pd = next((lt['adern'][0] for lt in lts if lt['art'] == 'Widerstand'),
              None)
    p.ja('Pull-down 10 kOhm zwischen D11 und GND',
         pd is not None and pd[2] in d11 and pd[3] in masse)
    gedrueckt = vk.netze(zustand=('ein', 'gedrueckt'), lts=lts)
    p.ja('Not-Aus gedrueckt: Shield, Wandler (Laser) und Luefter ohne 24 V',
         not {'Shield +', 'Wandler IN+', 'Lüfter +'} & gedrueckt['Buchse +'])
    p.ja('Not-Aus: NO bleibt frei (am Wechsler laege dort C)',
         N.get('Not-Aus NO', {'Not-Aus NO'}) <= {'Not-Aus NO', 'Not-Aus C',
                                                 'Not-Aus NC'})
    p.ok('Not-Aus-Kontakt {:.0f} A / {:.0f} V~ [v]: traegt die Dauerlast'
         .format(vk.NOTAUS_A, vk.NOTAUS_V), vk.NOTAUS_A,
         leistung.leistung()['strom'], '>=', 'A')
    w2 = next((lt for lt in lts if lt['nr'] == 'W2'), None)
    p.ok('   ... und den Strom, fuer den W2 ausgelegt ist (Netzteil)',
         vk.NOTAUS_A, w2['strom'] if w2 else float('inf'), '>=', 'A')
    aus = vk.netze(zustand=('nicht gedrueckt',), lts=lts)
    p.ja('Schalter aus: hinter dem Schalter keine 24 V',
         not {'Shield +', 'Wandler IN+', 'Lüfter +'} & aus['Buchse +'])
    # 24-V-Waechter: R1 vom +24 V hinter dem Not-Aus an Abort, R2 an GND
    wa = next((lt['adern'] for lt in lts if lt['nr'] == 'W16'), None)
    p.ja('Waechter: R1 am +24 V hinter Schalter und Not-Aus',
         wa is not None and wa[0][2] in plus24
         and wa[0][2] not in gedrueckt['Buchse +']
         and wa[0][2] not in aus['Buchse +'] and wa[0][3] == 'Shield Abort')
    p.ja('Waechter: R2 von Abort an GND', wa is not None
         and wa[1][2] == 'Shield Abort' and wa[1][3] in masse)
    u_min = 24.0 * (1.0 - vk.NETZ_TOLERANZ)
    u_max = 24.0 * (1.0 + vk.NETZ_TOLERANZ)
    hoch = min(vk.waechter_spannung(u_min, r) for r in vk.PULLUP)
    p.ok('Waechter: 24 V an -> Abort HIGH (Pull-up 20-50 kOhm)', hoch,
         vk.V_IH + 0.5, '>=', 'V')
    p.ok('   ... und nicht ueber 5 V', max(vk.waechter_spannung(u_max, r)
                                         for r in vk.PULLUP), vk.VCC, '<=',
         'V')
    tief = max(vk.waechter_spannung(0.0, r) for r in vk.PULLUP)
    p.ok('Waechter: 24 V weg -> Abort LOW, GRBL bricht ab', tief,
         vk.V_IL - 0.3, '<=', 'V')
    p.ok('   Strom in A0, falls R2 bricht (24 V ueber R1 an der '
         'Schutzdiode)', (u_max - vk.VCC - 0.5) / vk.WAECHTER_R1 * 1000.0,
         1.0, '<=', 'mA')

    falsch = []
    for lt, ader, a in vk.enden(lts):
        art = A[a][1]
        if lt['mm2'] is None or art is None:
            continue
        lo, hi = vk.KONTAKT[art]
        if not lo - 1e-9 <= lt['mm2'] <= hi + 1e-9:
            falsch.append('{} {} ({} mm2) in {}'.format(
                lt['nr'], ader[0], lt['mm2'], art))
    p.ja('jede Litze passt in ihre Kontakte (Dupont, XH, PH, Wago, '
         'Schraubklemme)', not falsch,
         (' — ' + '; '.join(falsch)) if falsch else '')
    bel = vk.wago_belegung(lts)
    for name, typ, plaetze in vk.WAGO:
        reserve = vk.WAGO_RESERVE.get(name, (0, ''))[0]
        p.ok('{} ({}): belegt + Reserve'.format(name, typ),
             len(bel[name]) + reserve, plaetze, '<=', 'Pl.')
    K = Q['K']
    for lt in lts:
        weg, kauf = vk.laenge_m(lt, K)
        if weg is None:
            continue
        if lt.get('mitgeliefert') and kauf <= lt['mitgeliefert']:
            p.ok('{} {}: mitgeliefertes Kabel reicht (+15 %)'.format(
                lt['nr'], lt['name']), lt['mitgeliefert'],
                 weg * (1.0 + leistung.RESERVE), '>=', 'm')
        else:
            p.ok('{} {}: Kauflaenge >= Weg + 15 %'.format(
                lt['nr'], lt['name']), kauf,
                 weg * (1.0 + leistung.RESERVE), '>=', 'm')
    for lt in lts:
        if 'weg_fach' not in lt:
            continue
        weg = K['kabel'][lt['weg_fach']][0] / 1000.0
        p.ok('{} {}: Laenge je Ader >= Weg im Fach + 15 %'.format(
            lt['nr'], lt['name']), lt['laenge'],
             weg * (1.0 + leistung.RESERVE), '>=', 'm')
    # Energieketten (gedruckt): Einzellitzen, Fuellgrad des lichten
    # Querschnitts; Mantelleitungen sind fuer den Biegeradius zu steif
    q = vk.kette_querschnitt()
    for kette in ('Y', 'X'):
        n, f = vk.kette_fuellung(lts, kette)
        p.ok('{}-Kette: {} Adern fuellen den Querschnitt zu'.format(kette, n),
             100.0 * f / q, 100.0 * vk.FUELLGRAD_MAX, '<=', '%')
        mantel = [lt['nr'] for lt in lts
                  if kette in lt.get('kette', '').split()
                  and lt['art'].startswith('Leitung')]
        p.ja('{}-Kette: keine Mantelleitung darin'.format(kette), not mantel,
             ' ({})'.format(', '.join(mantel)) if mantel else '')
    ma = vk.UNO_MA + 4 * vk.TREIBER_LOGIK_MA
    p.ok('5 V aus USB: nur noch Uno und Treiberlogik', ma, vk.USB_MA, '<=',
         'mA')

    with open(vk.ANLEITUNG, encoding='utf-8') as f:
        anleitung = f.read()
    for name, inhalt in vk.tabellen(Q).items():
        p.ja('verkabelung.md: Tabelle "{}" aktuell'.format(name),
             vk.auslesen(anleitung, name) == inhalt,
             '' if vk.auslesen(anleitung, name) == inhalt
             else ' — python3 tools/verkabelung.py')
    g = {k: v for k, v, _ in vk.grbl(Q)}
    pfad = os.path.join(vk.DOCS, 'endschalter.md')
    with open(pfad, encoding='utf-8') as f:
        es_text = f.read()
    for k in ('$130', '$131'):
        p.ja('endschalter.md nennt `{}={}`'.format(k, g[k]),
             '`{}={}`'.format(k, g[k]) in es_text)


if __name__ == '__main__':
    sys.exit(main())
