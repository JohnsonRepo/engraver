#!/usr/bin/env python3
"""Zeichnung: das Elektronikfach — Draufsicht, Rueckwand, Fugenwand.

Draufsicht mit abgenommenen Deckeln: beide Haelften mit Ohren und
Montageplatte am hinteren 2060, die Signalgasse vorn und die
Leistungsgasse hinten mit Leitwaenden und Oesen, Uno, Pi, Wandler, Wago,
Buchse und Schalter, der Luefter im Deckel gestrichelt, und die Kabelwege
im Fach aus tools/elektronik_zeichnen.py. Dazu die Rueckwand von hinten
(Buchse, Schalter, Lueftung, Durchbruch fuer Air Assist) und die Fugenwand
von links mit dem Pi, den Fenstern, Schrauben und Zapfen. Alle Masse aus
Elektronikfach.py (lage()); die Zeichnung ist massstaeblich.

    python3 tools/elektronikfach_zeichnen.py   ->  docs/elektronikfach.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import elektronik_zeichnen as ez                      # noqa: E402
import elektronik_check as ec                         # noqa: E402
from antrieb_zeichnen import (text, linie, pfeil, rect_px, de,  # noqa
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld, ORANGE              # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronikfach.svg')

BODEN = '#fdf1e6'                # Boden, tiefer als die Waende
FACH = {'fill': '#fdf8f2', 'stroke': ORANGE, 'stroke_dasharray': '6 4',
        'stroke_width': '1.0'}
VERDECKT = '#5b6472'
LUEFTER = '#1864ab'
SIGNAL = '#1971c2'               # Signalgasse und ihre Kabel
LEISTUNG = '#c92a2a'             # Leistungsgasse und ihre Kabel
FUENF = '#8e44ad'                # 5 V
FARBE.update({
    'platine': ('#d3e9da', '#2f7a4f'),     # Uno, Pi
    'wandler': ('#d6e0f2', '#3b5b92'),
    'gasse_s': ('#e7f1fb', '#a5c8ec'),
    'gasse_l': ('#fbe9e9', '#e3a5a5'),
})
# Kabelwege im Fach: Name in elektronik_zeichnen.kabelwege, Farbe, Leitung
WEGE = (('X-Endschalter', SIGNAL, 'W9'), ('Y-Endschalter', SIGNAL, 'W10'),
        ('5 V vom Wandler', FUENF, 'W6'), ('Pi 5 V', FUENF, 'W19'),
        ('USB Pi–Uno', '#495057', 'W17'), ('Wächter', SIGNAL, 'W16'),
        ('Laser (12 V + PWM)', LEISTUNG, 'W7'),
        ('Y-Motor rechts', LEISTUNG, 'W14'),
        ('Shield 24 V', LEISTUNG, 'W3'), ('Lüfter', LEISTUNG, 'W5'),
        ('Not-Aus', LEISTUNG, 'W2'), ('Pi 24 V', LEISTUNG, 'W18'))


def verdeckt(f, a0, a1, b0, b1):
    """Oeffnung unter der Oberkante: von oben nicht zu sehen."""
    return f.rect(a0, a1, b0, b1, 'neu', fill='#ffffff', fill_opacity='0.7',
                  stroke=VERDECKT, stroke_dasharray='2.5 2',
                  stroke_width='0.7')


def zug(f, punkte, farbe, breite=1.5, strich='5 3', spitze=False):
    """Streckenzug (Draufsicht), wahlweise mit Pfeilspitze am Ende."""
    t = [ez.linienzug(f, punkte, farbe, breite, strich)]
    if spitze and len(punkte) > 1:
        (x0, y0), (x1, y1) = f.px(*punkte[-2]), f.px(*punkte[-1])
        lang = math.hypot(x1 - x0, y1 - y0) or 1.0
        t.append(pfeil(x1, y1, (x1 - x0) / lang, (y1 - y0) / lang, farbe))
    return t


def im_fach(weg, EL):
    """Nur die Punkte eines Kabelwegs im Fach und die ersten danach."""
    gx = EL['geh_x'][1]
    pts, raus = [], False
    for x, y, _ in weg:
        if raus:
            break
        pts.append((x, y))
        raus = abs(x) > gx + 1.0 or y > EL['geh_y'][1] + 1.0
    return pts


# ---- Draufsicht -------------------------------------------------------------
def draufsicht(f, ew, EL, K):
    t, schrift = [], []
    R, rb = EL['R'], ew('rahmen_b')
    gx, gy, iy = EL['geh_x'], EL['geh_y'], EL['innen_y']
    py = EL['platte_y']
    a = f.a
    # Fach, hinteres 2060, die Enden der 2040 (darueber)
    t.append(f.rect(*EL['fach_x'], *EL['fach_y'], 'neu', **FACH))
    t.append(f.rect(a[0] - 5, a[1] + 5, *EL['quer_y'], 'profil'))
    for s in (-1, 1):
        x = sorted((s * (R - rb / 2.0), s * (R + rb / 2.0)))
        t.append(f.rect(*x, ew('rahmen_y0'), f.b[1] + 5, 'profil',
                        fill_opacity='0.35'))
    # Kasten: aussen, innen (Boden), Gassen
    for s in ('links', 'rechts'):
        hx, ix = EL['haelfte_x'][s], EL['innen_x'][s]
        t.append(f.rect(*hx, gy[0], py[0], 'neu'))
        t.append(f.rect(*ix, iy[0], iy[1], 'neu', fill=BODEN))
        t.append(f.rect(*ix, *EL['gasse_vorn'], 'gasse_s', stroke='none'))
        t.append(f.rect(*ix, *EL['gasse_hinten'][s], 'gasse_l',
                        stroke='none'))
        t.append(f.rect(*EL['ohr_x'][s], *py, 'neu'))
    t.append(f.rect(*gx, *py, 'neu'))
    # Fenster in Endwaenden und Fuge (Oeffnungen, verdeckt)
    for s in ('links', 'rechts'):
        ex = EL['endwand_x'][s]
        t.append(verdeckt(f, *ex, *EL['fenster_sig_y']))
        t.append(verdeckt(f, *ex, *EL['fenster_pow'][s][0]))
    for (y0, y1), _ in EL['fuge_fenster']:
        t.append(verdeckt(f, -ew('fuge_wand'), ew('fuge_wand'), y0, y1))
    # Leitwaende, Oesen, Dome, Binderschlitze
    for s in ('links', 'rechts'):
        for x, y in EL['leitwaende'][s]:
            t.append(f.rect(*x, *y, 'neu'))
        ol, ob = ew('oese_l') / 2.0, ew('oese_b') / 2.0
        tb = ew('oese_tunnel_b') / 2.0
        for x, y in EL['oesen'][s]:
            t.append(f.rect(x - ol, x + ol, y - ob, y + ob, 'neu'))
            t.append(f.rect(x - tb, x + tb, y - ob, y + ob, 'neu',
                            fill='#e9d8c7', stroke='none'))
        da = ew('dom_a') / 2.0
        for x, y, e in EL['dome'][s]:
            t.append(f.rect(x - da, x + da, *EL['dom_y'][e], 'neu'))
            t.append(f.kreis(x, y, ew('insert_m3_d') / 2.0, 'messing'))
    rt, rl = ew('binder_t') / 2.0, ew('binder_b') / 2.0
    for x, y, r in EL['binder']:
        sx, sy = (rl, rt) if r == 'y' else (rt, rl)
        t.append(f.rect(x - sx, x + sx, y - sy, y + sy, 'neu',
                        fill='#4a3526', stroke='none'))
    # M5: Koepfe hinter der Platte
    k = ew('m5_kopf_d') / 2.0
    for s in ('links', 'rechts'):
        for x, _ in EL['m5'][s]:
            t.append(f.rect(x - k, x + k, py[0] - ew('m5_kopf_h'), py[0],
                            'stahl'))

    # Geraete
    ux, uy = EL['uno_x'], EL['uno_y']
    t.append(f.rect(*ux, *uy, 'platine'))
    for x, y in EL['uno_loecher']:
        t.append(f.kreis(x, y, ew('uno_steg_d') / 2.0, 'neu', fill='none',
                         stroke=VERDECKT, stroke_dasharray='2 1.5'))
    ub = EL['usb_b_stecker']
    t.append(f.rect(ux[1], ub[0][0], *ub[1], 'stahl'))
    t.append(f.rect(*ub[0], *ub[1], 'kauf'))
    t.append(f.rect(EL['pi_bauteile_x'][0], EL['pi_steg_x'][1], *EL['pi_y'],
                    'platine'))
    for n in ('USB', 'PWR'):
        q = EL['pi_stecker'][n]
        t.append(f.rect(*q[0], *q[1], 'kauf', stroke_dasharray='2 1.5'))
    for n, wx, wy in (('12 V', EL['w12_x'], EL['w12_y']),
                      ('5 V', EL['w5_x'], EL['w5_y'])):
        t.append(f.rect(*wx, *wy, 'wandler'))
        x, y = f.px((wx[0] + wx[1]) / 2.0, (wy[0] + wy[1]) / 2.0)
        schrift.append(text(x, y - 1, 'Wandler', 8.0, TEXT, 'middle',
                            fett=True, halo=True))
        schrift.append(text(x, y + 9, '24 → ' + n, 7.5, TEXT, 'middle',
                            halo=True))
    ad = EL['adapter']
    t.append(f.rect(*ad[0], *ad[1], 'kauf'))
    for name, typ, x, y, _ in EL['wago']:
        t.append(f.rect(*x, *y, 'kauf'))
        if not name.endswith('5 V'):
            cx, cy = f.px((x[0] + x[1]) / 2.0, (y[0] + y[1]) / 2.0)
            schrift.append(text(cx, cy, name, 8.0, TEXT, 'middle',
                                fett=True, halo=True))
    t.append(f.rect(*EL['aa_x'], *EL['aa_y'], 'neu', fill='none',
                    stroke=GRAU, stroke_dasharray='4 3'))
    cx, cy = f.px(sum(EL['aa_x']) / 2.0, sum(EL['aa_y']) / 2.0)
    schrift.append(text(cx, cy + 3, 'Air Assist', 7.5, GRAU, 'middle',
                        halo=True))
    for q in ec.innenteile(ew, EL):
        if q.name in ('Buchse', 'Schalter'):
            t.append(f.rect(*q.x, *q.y, 'kauf'))
    # Luefter im Deckel (gestrichelt)
    fm, h = EL['luefter_mitte'], ew('luefter') / 2.0
    stil = {'fill': 'none', 'stroke': LUEFTER, 'stroke_dasharray': '5 3',
            'stroke_width': '1.1'}
    t.append(f.rect(fm[0] - h, fm[0] + h, fm[1] - h, fm[1] + h, 'neu',
                    **stil))
    t.append(f.kreis(fm[0], fm[1], ew('luefter_d') / 2.0, 'neu', **stil))
    cx, cy = f.px(*fm)
    schrift.append(text(cx, cy - 2, 'Uno + Shield', 8.5, TEXT, 'middle',
                        fett=True, halo=True))
    schrift.append(text(cx, cy + 9, '4 × TMC2209', 7.5, TEXT, 'middle',
                        halo=True))

    # Kabelwege im Fach
    for name, farbe, _ in WEGE:
        weg = K['kabel'][name][1]
        if weg is None:
            continue
        pts = im_fach(weg, EL)
        t += zug(f, pts, farbe, 1.3, '4 2.5',
                 spitze=len(pts) < len(weg))
    return t + schrift


# ---- Rueckwand von hinten ---------------------------------------------------
def rueckwand(f, ew, EL):
    """Blick von hinten auf die Rueckwand (X nach links, Z nach oben)."""
    t = []
    gz, bz = EL['geh_z'], EL['boden_z']
    t.append(f.rect(*EL['fach_x'], *EL['fach_z'], 'neu', **FACH))
    t.append(f.rect(*EL['geh_x'], *gz, 'neu'))
    for s in ('links', 'rechts'):
        t.append(f.rect(*EL['ohr_x'][s], *EL['ohr_z'], 'neu',
                        fill_opacity='0.5'))
    t.append(f.linie(0.0, gz[0], 0.0, gz[1], ORANGE, 1.2))
    lz, lb = EL['lueftung_z'], ew('lueftung_b') / 2.0
    for s in ('links', 'rechts'):
        for x in EL['lueftung_x'][s]:
            t.append(f.rect(x - lb, x + lb, *lz, 'neu', fill='#ffffff'))
    bx, ez_ = EL['buchse']
    fm = _fm()
    t.append(f.poly(fm.tropfen_punkte(bx, ez_, ew('buchse_d')), 'neu',
                    fill='#ffffff'))
    sx, _ = EL['schalter']
    t.append(f.kreis(sx, ez_, ew('schalter_blende_d') / 2.0, 'kauf'))
    t.append(f.poly(fm.tropfen_punkte(sx, ez_, ew('schalter_d'), 1.0,
                                      ew('schalter_kappe')), 'neu',
                    fill='none', stroke=VERDECKT, stroke_dasharray='2.5 2',
                    stroke_width='0.7'))
    ab = EL['ausbruch']
    t.append(f.poly(fm.tropfen_punkte(ab[0], ab[1], ew('ausbruch_d')), 'neu',
                    fill='#f3e6d8', stroke_dasharray='3 2'))
    t.append(f.linie(f.a[0], EL['tisch_z'], f.a[1], EL['tisch_z'], GRAU,
                     1.0))
    return t


_FM = []


def _fm():
    """Elektronikfach.py, einmal geladen (Traenen und Rauten)."""
    if not _FM:
        _FM.append(bauraum.modul_laden(ec.ELEKTRONIK, 'elektronikfach'))
    return _FM[0]


# ---- Fugenwand von links ----------------------------------------------------
def fugenwand(f, ew, EL):
    """Blick von links (aus der linken Haelfte) auf die Fugenwand: Y nach
    rechts (vorn), Z nach oben. Der Pi steht davor."""
    t = []
    gy, gz, iy, bz = EL['geh_y'], EL['geh_z'], EL['innen_y'], EL['boden_z']
    t.append(f.rect(gy[0], EL['platte_y'][1], *gz, 'neu'))
    t.append(f.rect(*iy, bz, gz[1], 'neu', fill=BODEN))
    for (y0, y1), (z0, z1) in EL['fuge_fenster']:
        t.append(f.rect(y0, y1, z0, z1, 'neu', fill='#ffffff'))
    for y, z in EL['fuge_bolzen']:
        t.append(f.kreis(y, z, ew('m3_durchgang') / 2.0, 'neu',
                         fill='#ffffff'))
        t.append(f.kreis(y, z, 2.75, 'stahl', fill='none'))
    for y, z in EL['fuge_zapfen']:
        t.append(f.poly(_fm().raute(y, z, ew('zapfen_r')), 'neu',
                        fill='#f3e6d8'))
    # Pi davor (Platine, Stehbolzen, Stecker)
    t.append(f.rect(*EL['pi_y'], *EL['pi_z'], 'platine', fill_opacity='0.85'))
    for y, z in EL['pi_loecher']:
        t.append(f.kreis(y, z, ew('pi_steg_d') / 2.0, 'neu'))
        t.append(f.kreis(y, z, ew('m25_kern') / 2.0, 'stahl'))
    for n in ('USB', 'PWR'):
        q = EL['pi_stecker'][n]
        t.append(f.rect(*q[1], *q[2], 'kauf'))
    py0, pz1 = EL['pi_y'][0], EL['pi_z'][1]
    t.append(f.rect(py0 - 2.5, py0, pz1 - 18.0, pz1 - 6.0, 'stahl'))
    t.append(f.linie(f.a[0], ew('rahmen_z0'), f.a[1], ew('rahmen_z0'),
                     GRAU, 0.8, '4 3'))
    return t


def main():
    em = bauraum.modul_laden(ec.ELEKTRONIK, 'elektronikfach')
    ew, EL = em.w, em.lage()
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    K = ez.konzept(w, L, tw, TL, ew, EL)
    gx, gy, gz = EL['geh_x'], EL['geh_y'], EL['geh_z']
    t = [text(24, 30, 'Elektronikfach (Elektronikfach.py Rev. {}) — zwei '
              'Hälften mit Signalgasse vorn und Leistungsgasse hinten'.format(
                  em.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus dem Skript. Deckel '
              'abgenommen, der Lüfter im Deckel gestrichelt; hinten oben, '
              'vorn (zum hinteren 2060) unten.', 9, GRAU)]

    # ---- Draufsicht --------------------------------------------------------
    f = Feld(262, 96, (-262.0, 262.0), (-372.0, -224.0), 1.62, b_runter=True)
    t += f.ausschnitt('drauf', draufsicht(f, ew, EL, K))
    t += f.rahmen('Draufsicht, Deckel abgenommen (hinten oben)')
    sy = sum(EL['fenster_sig_y']) / 2.0
    unten = f.oy + f.hoehe + 18
    t += f.spalte([
        (gx[0], sy, 'Fenster Signale: Licht-\nschranken X, Z, Laser-PWM'),
        (gx[0], sum(EL['fenster_pow']['links'][0]) / 2.0,
         'Fenster Leistung: Motoren\nX, Y, Z, Laser 12 V'),
        (EL['wago'][0][2][1], sum(EL['wago'][0][3]) / 2.0,
         '5-V-Klemmen an der Endwand\n(Hebel nach innen)'),
        (EL['ohr_x']['links'][0] + 4.0, sum(EL['platte_y']) / 2.0,
         'Ohr: 2 × M5 in die\nRückseite des 2060'),
        (EL['oesen']['links'][3][0], EL['oesen']['links'][3][1] - 4.0,
         'Öse = Zugentlastung\n(Kabelbinder)'),
        (EL['w12_x'][0] + 4.0, EL['w12_y'][0] + 4.0,
         'Wandler 24 → 12 V für den\nLaser, Ausgang zum Fenster'),
        (EL['pi_bauteile_x'][0], EL['pi_y'][0] + 6.0,
         'Pi Zero 2 W senkrecht an\nder Fugenwand, Buchsen unten')],
        f.ox - 12, 'end', abstand=25.0, unten=unten)
    t += f.spalte([
        (EL['adapter'][0][0] + 4.0, sum(EL['adapter'][1]) / 2.0,
         'USB-A-Adapter mit Klemmen:\n5 V über W6 an die Wago'),
        (EL['aa_x'][1] - 4.0, EL['aa_y'][0] + 4.0,
         'Platz für Air Assist,\nDurchbruch in der Rückwand'),
        (EL['wago'][3][2][1], EL['wago'][3][3][0] + 4.0,
         'Wago +24 V und GND\n(221-420, Klebeband)'),
        (EL['schalter'][0], EL['innen_y'][0] + 6.0,
         'Buchse und Schalter in\nder Rückwand'),
        (gx[1], sy, 'Fenster Signale:\nLichtschranke Y'),
        (gx[1], sum(EL['fenster_pow']['rechts'][0]) / 2.0,
         'Fenster Leistung: Y-Motor\nrechts, Not-Aus'),
        (EL['m5']['rechts'][2][0], EL['platte_y'][0] - 2.5,
         'M5 innen (obere Nut), vor\ndem Bestücken anziehen')],
        f.ox + f.breite + 12, 'start', abstand=25.0, unten=unten)
    for xm, ym, s_, farbe in ((-150.0, sum(EL['gasse_vorn']) / 2.0,
                               'Signalgasse', SIGNAL),
                              (150.0, sum(EL['gasse_vorn']) / 2.0,
                               'Signalgasse', SIGNAL),
                              (-150.0, sum(EL['gasse_hinten']['links']) / 2.0,
                               'Leistungsgasse', LEISTUNG),
                              (100.0, sum(EL['gasse_hinten']['rechts']) / 2.0,
                               'Leistungsgasse', LEISTUNG)):
        x, y = f.px(xm, ym)
        t.append(text(x, y + 3, s_, 8.0, farbe, 'middle', fett=True,
                      halo=True))

    # ---- Rueckwand ---------------------------------------------------------
    fr = Feld(262, f.oy + f.hoehe + 80, (-262.0, 262.0), (-134.0, -42.0),
              1.62, a_rueck=True)
    t += fr.ausschnitt('rueck', rueckwand(fr, ew, EL))
    t += fr.rahmen('Rückwand von hinten (rechte Hälfte links im Bild)')
    bx, ez_ = EL['buchse']
    t += fr.spalte([
        (bx, ez_, 'Einbaubuchse 5,5 × 2,1\n(Loch {} mm, Traene)'.format(
            de(ew('buchse_d'), 1))),
        (EL['schalter'][0], ez_ + ew('schalter_blende_d') / 2.0,
         'Wippschalter rund\n(Blende Ø{})'.format(
             de(ew('schalter_blende_d'), 1)))],
        fr.ox - 12, 'end', abstand=24.0)
    t += fr.spalte([
        (EL['ausbruch'][0], EL['ausbruch'][1],
         'Air Assist: Durchbruch\n{} mm, Haut zum Ausbrechen'.format(
             de(ew('ausbruch_d'), 0))),
        (-100.0, EL['lueftung_z'][1], 'Lüftungsschlitze\n'
         '(Luft vom Lüfter)')],
        fr.ox + fr.breite + 12, 'start', abstand=24.0)

    # ---- Fugenwand ---------------------------------------------------------
    s3 = 3.0
    ff = Feld(262, fr.oy + fr.hoehe + 60, (-362.0, -246.0), (-132.0, -44.0),
              s3)
    t += ff.ausschnitt('fuge', fugenwand(ff, ew, EL))
    t += ff.rahmen('Fugenwand von links, mit dem Pi davor (vorn rechts)')
    t += ff.spalte([
        (EL['fuge_fenster'][1][0][0], sum(EL['fuge_fenster'][1][1]) / 2.0,
         'Fenster Leistung'),
        (EL['fuge_bolzen'][0][0], EL['fuge_bolzen'][0][1],
         'M3×12 mit Mutter (4 ×)'),
        (EL['fuge_zapfen'][1][0], EL['fuge_zapfen'][1][1],
         'Rauten-Zapfen (2 ×)'),
        (EL['pi_y'][0], EL['pi_z'][1] - 12.0, 'SD-Karte')],
        ff.ox - 12, 'end', abstand=26.0)
    t += ff.spalte([
        (EL['pi_y'][1] - 6.0, EL['pi_z'][1] - 6.0,
         'Pi Zero 2 W auf 4 Stehbolzen\n(Traene, Spitze unten)'),
        (sum(EL['pi_stecker']['USB'][1]) / 2.0,
         EL['pi_stecker']['USB'][2][0], 'Stecker USB (W17)'),
        (sum(EL['pi_stecker']['PWR'][1]) / 2.0,
         EL['pi_stecker']['PWR'][2][0], 'Stecker PWR IN (W19)'),
        (EL['fuge_fenster'][0][0][1], sum(EL['fuge_fenster'][0][1]) / 2.0,
         'Fenster Signale'),
        (EL['pi_y'][1], ew('rahmen_z0'),
         'Oberkante 2060: der Pi\nsteht {} mm darüber (WLAN)'.format(
             de(EL['pi_z'][1] - ew('rahmen_z0'), 0)))],
        ff.ox + ff.breite + 12, 'start', abstand=26.0)

    # ---- Zahlen ------------------------------------------------------------
    z0 = gz[0]
    kab = K['kabel']
    zeilen = [
        ('Teile', 'Fach links {} × {} × {} mm, Fach rechts {} × {} × {} mm, '
         'Deckel je {} × {} × {} mm — alles PETG, jedes Teil ≤ 250 mm'.format(
             *(de(EL['teile']['Fach_links']['bbox'][i][1]
                  - EL['teile']['Fach_links']['bbox'][i][0], 1)
               for i in range(3)),
             *(de(EL['teile']['Fach_rechts']['bbox'][i][1]
                  - EL['teile']['Fach_rechts']['bbox'][i][0], 1)
               for i in range(3)),
             *(de(EL['teile']['Deckel_links']['bbox'][i][1]
                  - EL['teile']['Deckel_links']['bbox'][i][0], 1)
               for i in range(3)))),
        ('Lage', 'Kasten {} × {} × {} mm hinter dem hinteren 2060, in der '
         'Mitte (|X| ≤ 225) und deshalb höher als das Fach ({} mm); der '
         'Lüfter endet {} mm über dem Fachboden'.format(
             de(gx[1] - gx[0], 0), de(gy[1] - gy[0], 0),
             de(gz[1] - gz[0], 0), de(EL['fach_z'][1] - EL['fach_z'][0], 0),
             de(EL['luefter_z'][1] - z0, 1))),
        ('Montage', 'je Ohr 2 × M5×{0} (untere und obere Nut), innen je '
         '1 × M5×{0} (obere Nut); die Hälften mit 4 × M3×12 und 2 Zapfen in '
         'der Fuge'.format(de(ew('m5_l'), 0))),
        ('Gassen', 'vorn {} mm Signale, hinten {} mm Leistung; Leitwände {} '
         'mm hoch, Ösen für Kabelbinder; je Gasse ein Fenster in jeder '
         'Endwand und in der Fuge'.format(
             de(EL['gasse_vorn'][1] - EL['gasse_vorn'][0], 0),
             de(EL['gasse_hinten']['links'][1]
                - EL['gasse_hinten']['links'][0], 0),
             de(ew('leitwand_h'), 0))),
        ('5 V', 'vom Wandler über den USB-A-Adapter (W6, {} m 0,75 mm²) an '
         'die Wago +5 V und GND 5 V; daran die Lichtschranken und der Pi '
         '(W19), der Uno über USB (W17)'.format(
             de(kab['5 V vom Wandler'][0] / 1000.0, 2))),
        ('Höhen', 'über der Unterkante: Boden {}, Uno {}, Treiber oben {}, '
         'Pi {}–{}, Rand {}, Deckel {}, Lüfter {} mm'.format(
             de(EL['boden_z'] - z0), de(EL['uno_z0'] - z0),
             de(EL['stapel_z1'] - z0), de(EL['pi_z'][0] - z0),
             de(EL['pi_z'][1] - z0), de(EL['rand_z'] - z0),
             de(EL['deckel_z'][1] - z0), de(EL['luefter_z'][1] - z0))),
    ]
    ty = ff.oy + ff.hoehe + 50
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k_, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k_, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))

    # ---- Legende -----------------------------------------------------------
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'Fach (PETG)'),
                                  ('platine', 'Uno, Pi'),
                                  ('wandler', 'Wandler'),
                                  ('kauf', 'Kaufteil, Stecker'),
                                  ('gasse_s', 'Signalgasse'),
                                  ('gasse_l', 'Leistungsgasse'),
                                  ('messing', 'Gewindeeinsatz'),
                                  ('profil', 'Aluprofil'))):
        x = 24 + (i % 4) * 190
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    y = ly + 36
    for i, (farbe, strich, breite, s) in enumerate((
            (SIGNAL, '4 2.5', 1.3, 'Signale'),
            (FUENF, '4 2.5', 1.3, '5 V'),
            (LEISTUNG, '4 2.5', 1.3, '24 V, 12 V, Motoren'),
            (LUEFTER, '5 3', 1.1, 'Lüfter im Deckel'))):
        x = 24 + i * 190
        t.append(linie(x, y + 4.5, x + 16, y + 4.5, farbe, breite, strich))
        t.append(text(x + 21, y + 8, s, 8.5))
    t.append(text(24, ly + 62, 'Gestrichelt: verdeckt oder im Deckel. Die '
                  'Lage der Stifte auf dem Shield ist angenommen [?]; die '
                  'Kabel laufen in ihrer Gasse und verlassen das Fach durch '
                  'das Fenster ihrer Art.', 8.5, GRAU))
    W = int(f.ox + f.breite + 230)
    H = int(ly + 78)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="{0}" height="{1}" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as fd:
        fd.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
