#!/usr/bin/env python3
"""Zeichnung: Elektronik-Gehaeuse von oben, Deckel abgenommen.

Draufsicht auf Kasten, Kabelkanal und Montageplatte am hinteren 2060:
links der Uno mit CNC Shield und Treibern, darueber gestrichelt der Luefter
im Deckel; rechts der Verteiler mit Einbaubuchse, Schalter, Wandler und
Wago-Klemmen; dazu Kabelausschnitte, Dome, Stehbolzen, Kabelbinder und die
Kabelwege aus dem Kasten. Alle Masse aus Elektronik.py (lage()); die
Zeichnung ist massstaeblich und wandert mit den Parametern. Was unter der
Oberkante liegt (Fenster und Loecher in der Rueckwand, Lueftungsschlitze,
M5 durch die Platte, Stehbolzen unter dem Uno), ist gestrichelt.

    python3 tools/elektronik_box_zeichnen.py   ->  docs/elektronik-box.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (text, linie, pfeil, rect_px, de,  # noqa
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld, ORANGE              # noqa: E402
from y_antrieb_zeichnen import quer_mass              # noqa: E402
from elektronik_zeichnen import ELEKTRONIK, KABEL, linienzug  # noqa: E402
from elektronik_check import (BUCHSE_KOERPER_D, BUCHSE_KOERPER_T,  # noqa
                              SCHALTER_KOERPER)

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-box.svg')

S = 3.0                          # px/mm
X_BEREICH = (-272.0, -4.0)       # Maschinen-X
Y_BEREICH = (-382.0, -216.0)     # Maschinen-Y, vorn (zur Maschine) unten

# Buchse und Schalter hinter der Rueckwand mit der Huelle aus
# tools/elektronik_check.py (nicht gemessen); dazu nur fuers Bild [?]:
BUCHSE_MUTTER = 2.0              # Einbaubuchse: Mutter innen, dick
BUCHSE_BUND = (10.0, 2.0)        # ... Bund aussen: breit, dick
SCHALTER_RAHMEN = 3.0            # KCD1: Rahmen aussen, tief
BINDER_B = 3.6                   # Kabelbinder: Breite

BODEN = '#fdf1e6'                # Boden und Kanal, tiefer als die Waende
FACH = {'fill': '#fdf8f2', 'stroke': ORANGE, 'stroke_dasharray': '6 4',
        'stroke_width': '1.0'}
VERDECKT = '#5b6472'
LUEFTER = '#1864ab'
LUFT = '#4dabf7'
FARBE.update({
    'platine': ('#d3e9da', '#2f7a4f'),     # Uno mit Shield und Treibern
    'wandler': ('#d6e0f2', '#3b5b92'),
})


def verdeckt(f, a0, a1, b0, b1):
    """Oeffnung unter der Oberkante: von oben nicht zu sehen."""
    return f.rect(a0, a1, b0, b1, 'neu', fill='#ffffff', fill_opacity='0.7',
                  stroke=VERDECKT, stroke_dasharray='2.5 2',
                  stroke_width='0.7')


def kerbe(f, a0, a1, b0, b1):
    """Kabelausschnitt: die Wand ist dort von oben her ausgeschnitten."""
    return f.rect(a0, a1, b0, b1, 'neu', fill=BODEN, stroke_dasharray='3 2')


def pfeilzug(f, punkte, farbe, breite=1.6, strich='5 3'):
    """Streckenzug mit Pfeilspitze am letzten Punkt."""
    (x0, y0), (x1, y1) = f.px(*punkte[-2]), f.px(*punkte[-1])
    lang = math.hypot(x1 - x0, y1 - y0) or 1.0
    return [linienzug(f, punkte, farbe, breite, strich),
            pfeil(x1, y1, (x1 - x0) / lang, (y1 - y0) / lang, farbe)]


def hilfslinie(f, a0, b0, a1, b1):
    return f.linie(a0, b0, a1, b1, '#9aa4b1', 0.5)


def mitte_px(f, a0, a1, b0, b1):
    return f.px((a0 + a1) / 2.0, (b0 + b1) / 2.0)


# ---- Draufsicht -------------------------------------------------------------
def draufsicht(f, ew, EL):
    """Alle Teile von oben in Maschinenkoordinaten: X nach rechts, Y nach
    vorn (unten im Bild)."""
    t, schrift = [], []           # Schrift zuletzt, ueber den Pfeilen
    R, rb = EL['R'], ew('rahmen_b')
    gx, gy, ix, iy = EL['geh_x'], EL['geh_y'], EL['innen_x'], EL['innen_y']
    py = EL['platte_y']
    a, b = f.a, f.b
    # Fach (Hintergrund), hinteres 2060, darueber das linke 2040 mit der
    # Nut in der Oberseite
    xi = R - rb / 2.0 - ew('fach_rand')
    t.append(f.rect(-xi, xi, ew('rahmen_y0') + ew('fach_rand'),
                    ew('quer_y1') - ew('fach_rand'), 'neu', **FACH))
    qy = EL['quer_y']
    t.append(f.rect(a[0] - 5, a[1] + 5, qy[0], qy[1], 'profil'))
    nb = ew('nut_b') / 2.0
    for s in (-1, 1):
        y = sum(qy) / 2.0 + s * nb
        t.append(f.linie(a[0] - 5, y, a[1] + 5, y, '#8c939e', 0.6))
    t.append(f.rect(-R - rb / 2.0, -R + rb / 2.0, ew('rahmen_y0'), b[1] + 5,
                    'profil'))
    for s in (-1, 1):
        t.append(f.linie(-R + s * nb, ew('rahmen_y0'), -R + s * nb, b[1] + 5,
                         '#8c939e', 0.6))

    # Kanalboden mit Rippen, Montageplatte, M5 (Kopf hinter der Platte,
    # Schaft verdeckt in der Platte)
    t.append(f.rect(gx[0], gx[1], gy[1], py[0], 'neu', fill=BODEN))
    for x0, x1 in EL['rippen_x']:
        t.append(f.rect(x0, x1, gy[1], py[0], 'neu'))
    t.append(f.rect(*EL['platte_x'], *py, 'neu'))
    for x in sorted({p[0] for p in EL['m5']}):
        d, k = ew('m5_durchgang') / 2.0, ew('m5_kopf_d') / 2.0
        t.append(verdeckt(f, x - d, x + d, py[0], py[1]))
        t.append(f.rect(x - k, x + k, py[0] - ew('m5_kopf_h'), py[0],
                        'stahl'))

    # Kasten: Waende, Boden, Kabelausschnitte oben offen
    t.append(f.rect(gx[0], gx[1], gy[0], gy[1], 'neu'))
    t.append(f.rect(ix[0], ix[1], iy[0], iy[1], 'neu', fill=BODEN))
    yc, h = EL['kabel_links_y'], ew('kabel_links_b') / 2.0
    t.append(kerbe(f, gx[0], ix[0], yc - h, yc + h))
    xv, h = EL['kabel_vorn_x'], ew('kabel_vorn_b') / 2.0
    t.append(kerbe(f, xv - h, xv + h, iy[1], gy[1]))
    # verdeckt: Fenster fuer USB und Hohlbuchse, Loch der Buchse und
    # Ausschnitt des Schalters in der Rueckwand; Lueftungsschlitze rechts
    fx = EL['fenster_x']
    t.append(verdeckt(f, fx[0], fx[1], gy[0], iy[0]))
    for x, h in ((EL['buchse_x'], ew('buchse_d') / 2.0),
                 (EL['schalter_x'], ew('schalter_b') / 2.0)):
        t.append(verdeckt(f, x - h, x + h, gy[0], iy[0]))
    h = ew('lueftung_b') / 2.0
    for y in EL['lueftung_y']:
        t.append(verdeckt(f, ix[1], gx[1], y - h, y + h))
    # Dome mit Gewindeeinsatz
    for x, y in EL['dome']:
        t.append(f.kreis(x, y, ew('dom_d') / 2.0, 'neu'))
        t.append(f.kreis(x, y, ew('insert_m3_d') / 2.0, 'messing'))
    # Schlitze fuer die Kabelbinder im Boden
    rt, rl = ew('binder_t') / 2.0, ew('binder_b') / 2.0
    for x, y in EL['binder']:
        t.append(f.rect(x - rl, x + rl, y - rt, y + rt, 'neu',
                        fill='#4a3526', stroke='none'))

    # Uno mit Shield und Treibern; die Buchsen stehen hinten ueber die
    # Platine, die Stehbolzen liegen verdeckt darunter
    ux, uy = EL['uno_x'], EL['uno_y']
    t.append(f.rect(ux[0], ux[0] + ew('uno_buchse_b'),
                    uy[0] - ew('uno_buchse_vor'), uy[0], 'stahl'))
    t.append(f.rect(*ux, *uy, 'platine'))
    for x, y in EL['uno_loecher']:
        t.append(f.kreis(x, y, ew('uno_steg_d') / 2.0, 'neu', fill='none',
                         stroke=VERDECKT, stroke_dasharray='2 1.5'))
        t.append(f.kreis(x, y, ew('uno_schraube_d') / 2.0, 'neu',
                         fill='none', stroke=VERDECKT,
                         stroke_dasharray='2 1.5'))

    # Verteiler: hinten Buchse und Schalter (mit ihren Teilen vor der
    # Rueckwand), davor der Wandler mit zwei Kabelbindern, davor die Wago
    x, y0 = EL['buchse_x'], iy[0]
    h = BUCHSE_KOERPER_D / 2.0
    t.append(f.rect(x - h, x + h, y0, y0 + BUCHSE_MUTTER, 'stahl'))
    h = ew('buchse_d') / 2.0
    t.append(f.rect(x - h, x + h, y0 + BUCHSE_MUTTER, y0 + BUCHSE_KOERPER_T,
                    'kauf'))
    bb, bd = BUCHSE_BUND
    t.append(f.rect(x - bb / 2.0, x + bb / 2.0, gy[0] - bd, gy[0], 'stahl'))
    x, h = EL['schalter_x'], SCHALTER_KOERPER[0] / 2.0
    t.append(f.rect(x - h, x + h, y0, y0 + SCHALTER_KOERPER[2], 'kauf'))
    cx, cy = mitte_px(f, x, x, y0, y0 + SCHALTER_KOERPER[2])
    schrift.append(text(cx, cy - 1, 'Schalter', 8.0, TEXT, 'middle',
                        fett=True))
    schrift.append(text(cx, cy + 9, 'KCD1', 7.5, GRAU, 'middle'))
    t.append(f.rect(x - h, x + h, gy[0] - SCHALTER_RAHMEN, gy[0], 'kauf'))
    wx, wy = EL['wandler_x'], EL['wandler_koerper_y']
    t.append(f.rect(*wx, *wy, 'wandler'))
    ya, yb = EL['binder'][0][1], EL['binder'][1][1]
    for x in EL['binder_x_lage']:
        t.append(f.rect(x - BINDER_B / 2.0, x + BINDER_B / 2.0, ya, yb, 'neu',
                        fill='#3a3f47', fill_opacity='0.85', stroke='none'))
    cx, cy = mitte_px(f, *wx, *wy)
    schrift.append(text(cx, cy - 9, 'Wandler', 8.5, TEXT, 'middle',
                        fett=True, halo=True))
    schrift.append(text(cx, cy + 2, '24 → 12 V', 8.0, TEXT, 'middle',
                        halo=True))
    for name, typ, (x0, x1), (y0, y1), _ in EL['wago']:
        t.append(f.rect(x0, x1, y0, y1, 'kauf'))
        cx, cy = mitte_px(f, x0, x1, y0, y1)
        schrift.append(text(cx, cy - 1, name, 8.5, TEXT, 'middle',
                            fett=True))
        schrift.append(text(cx, cy + 10, typ, 7.5, GRAU, 'middle'))

    # Luefter im Deckel, darueber (gestrichelt)
    fm, h = EL['luefter_mitte'], ew('luefter') / 2.0
    stil = {'fill': 'none', 'stroke': LUEFTER, 'stroke_dasharray': '5 3',
            'stroke_width': '1.1'}
    t.append(f.rect(fm[0] - h, fm[0] + h, fm[1] - h, fm[1] + h, 'neu',
                    **stil))
    t.append(f.kreis(fm[0], fm[1], ew('luefter_d') / 2.0, 'neu', **stil))
    for x, y in EL['luefter_loecher']:
        t.append(f.kreis(x, y, ew('m3_durchgang') / 2.0, 'neu', fill='none',
                         stroke=LUEFTER, stroke_width='0.8'))

    # Luft: vom Luefter ueber die Treiber und den Wandler zum naechsten
    # Lueftungsschlitz
    ys = min(EL['lueftung_y'], key=lambda y: abs(y - fm[1]))
    t += pfeilzug(f, [(fm[0] + 22.0, fm[1]), (ix[1] - 8.0, fm[1]),
                      (ix[1] - 0.5, ys)], LUFT, 1.4, '6 3')
    # Kabel: links unter dem 2040 durch nach aussen, vorn in den Kanal und
    # darin nach rechts, hinten 24 V und USB hinein
    t += pfeilzug(f, [(ux[0] + 6.0, yc), (-R + rb / 2.0 + 3.0, yc)], KABEL)
    ykan = (gy[1] + py[0]) / 2.0
    t += pfeilzug(f, [(xv, iy[1] - 5.0), (xv, ykan),
                      (EL['platte_x'][1] + 1.0, ykan)], KABEL)
    for x, y in ((EL['buchse_x'], gy[0] - BUCHSE_BUND[1] - 0.5),
                 ((fx[0] + fx[1]) / 2.0, gy[0] - 0.5)):
        t += pfeilzug(f, [(x, gy[0] - 17.0), (x, y)], KABEL)
    return t + schrift


# ---- Masse ------------------------------------------------------------------
def masse(f, ew, EL):
    """Masskette unten (quer) und rechts (Tiefe), mit Hilfslinien."""
    t = []
    gx, gy, py, px_ = EL['geh_x'], EL['geh_y'], EL['platte_y'], EL['platte_x']
    x2040 = -EL['R'] + ew('rahmen_b') / 2.0
    yq = -224.0
    for x, y in ((px_[0], py[0]), (gx[0], gy[1]), (gx[1], gy[1]),
                 (px_[1], py[0])):
        t.append(hilfslinie(f, x, y, x, yq + 1.5))
    kette = [x2040, px_[0], gx[0], gx[1], px_[1]]
    for a0, a1 in zip(kette, kette[1:]):
        t += quer_mass(f, a0, a1, yq, '{} mm'.format(de(a1 - a0, 1)))
    xt = -18.0
    for x, y in ((gx[1], gy[0]), (gx[1], gy[1]), (px_[1], py[0]),
                 (px_[1], py[1])):
        t.append(hilfslinie(f, x, y, xt + 1.5, y))
    # das Mass des Kanals oben in den Kanal: in der Mitte laeuft der Pfeil
    for b0, b1, bt in ((gy[0], gy[1], None), (gy[1], py[0], gy[1] + 3.0),
                       (py[0], py[1], None)):
        t += f.mass(xt, b0, b1, '{} mm'.format(de(b1 - b0, 1)), b_text=bt)
    return t


def main():
    em = bauraum.modul_laden(ELEKTRONIK, 'elektronik')
    ew, EL = em.w, em.lage()
    gx, gy, gz = EL['geh_x'], EL['geh_y'], EL['geh_z']
    ix, iy = EL['innen_x'], EL['innen_y']
    ux, uy = EL['uno_x'], EL['uno_y']
    fm = EL['luefter_mitte']
    fx = EL['fenster_x']
    R = EL['R']
    t = [text(24, 30, 'Elektronik-Gehäuse von oben (Elektronik.py Rev. {})'
              .format(em.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus dem Skript. Deckel '
              'abgenommen, der Lüfter im Deckel gestrichelt; hinten oben, '
              'vorn (zur Maschine) unten.', 9, GRAU)]

    f = Feld(262, 96, X_BEREICH, Y_BEREICH, S, b_runter=True)
    t += f.ausschnitt('box', draufsicht(f, ew, EL))
    t += f.rahmen('Draufsicht (hinten oben), Deckel abgenommen')
    t += masse(f, ew, EL)
    # Beschriftung der Pfeile hinten
    for x, s in ((EL['buchse_x'], '24 V vom Netzteil in die\n'
                  'Einbaubuchse 5,5 × 2,1 (M8)'),
                 ((fx[0] + fx[1]) / 2.0, 'USB')):
        xp, yp = f.px(x, gy[0] - 17.0)
        zeilen = s.split('\n')
        for i, z in enumerate(zeilen):
            t.append(text(xp, yp - 4 - 10 * (len(zeilen) - 1 - i), z, 8.0,
                          TEXT, 'middle', halo=True))

    yc = EL['kabel_links_y']
    t += f.spalte([
        (-R, gy[0] + 12.0, 'linkes 2040 (darüber)'),
        (-R + ew('rahmen_b') / 2.0 + 4.0, yc,
         'Kabel links raus, unter dem 2040\ndurch: zur Y-Kette (X-, Z-Motor,\n'
         'Laser, Endschalter X, Z) und\nzum linken Y-Motor'),
        (EL['dome'][0][0] - 3.0, EL['dome'][0][1],
         'Dom mit Gewindeeinsatz M3\n(4 ×, Deckelschrauben)'),
        (fx[0] + 6.0, gy[0] + 1.2,
         'Fenster für USB und Hohlbuchse\n(verdeckt, {} mm breit)'.format(
             de(fx[1] - fx[0], 0))),
        (fm[0] - ew('luefter') / 2.0, fm[1] - 10.0,
         'Lüfter {0} × {0} im Deckel\n(gestrichelt), bläst nach unten'.format(
             de(ew('luefter'), 0))),
        (EL['uno_loecher'][0][0], EL['uno_loecher'][0][1],
         'Stehbolzen für M3 (4 ×, verdeckt)'),
        ((ux[0] + ux[1]) / 2.0 - 3.0, uy[1] - 6.0,
         'Uno + CNC Shield V3 + 4 × TMC2209\n({} mm hoch)'.format(
             de(ew('stapel_h'), 0))),
        (EL['rippen_x'][0][0] + 2.0, (gy[1] + EL['platte_y'][0]) / 2.0,
         'Kabelkanal {} mm, 3 Rippen'.format(de(ew('geh_abstand'), 0))),
        (EL['m5'][0][0], EL['platte_y'][0] - 2.5,
         'Montageplatte: 4 × M5×{} in\nHammermuttern des 2060'.format(
             de(EL['m5_schraube'], 0))),
        (-235.0, sum(EL['quer_y']) / 2.0, 'hinteres 2060')],
        f.ox - 12, 'end', abstand=24.0)
    wx, wy = EL['wandler_x'], EL['wandler_koerper_y']
    wago = EL['wago']
    t += f.spalte([
        (EL['binder_x_lage'][1] + 1.0, EL['binder'][0][1] + 4.0,
         'Kabelbinder (2 ×) durch Schlitze\nim Boden, {} mm neben der '
         'Mitte'.format(de(ew('wandler_binder'), 0))),
        (wx[1] - 3.0, wy[1] - 3.0,
         'Wandler 24 → 12 V / 5 A ({} × {} × {}),\nVorschlag: Eingang '
         'rechts, Ausgang links'.format(de(ew('wandler_l'), 0),
                                        de(ew('wandler_b'), 0),
                                        de(ew('wandler_h'), 0))),
        (gx[1] - 1.2, EL['lueftung_y'][0],
         'Lüftungsschlitze (6 ×, verdeckt):\ndie Luft geht über den Wandler'),
        (wago[2][2][1], sum(wago[2][3]) / 2.0,
         'Wago-Klemmen auf Klebeband'),
        (EL['platte_x'][1] + 1.0, (gy[1] + EL['platte_y'][0]) / 2.0,
         'Kabel vorn durch den Ausschnitt\n({} mm) in den Kanal, darin nach\n'
         'rechts: rechter Y-Motor,\nY-Endschalter, Not-Aus'.format(
             de(ew('kabel_vorn_b'), 0)))],
        f.ox + f.breite + 12, 'start', abstand=24.0)

    # ---- Zahlen ------------------------------------------------------------
    z0 = gz[0]
    zeilen = [
        ('Kasten', '{} × {} × {} mm (B × T × H), Wand und Boden {} mm; innen '
         '{} × {} mm und {} mm hoch'.format(
             de(gx[1] - gx[0]), de(gy[1] - gy[0]), de(gz[1] - gz[0]),
             de(ew('geh_wand')), de(ix[1] - ix[0]), de(iy[1] - iy[0]),
             de(gz[1] - EL['boden_z']))),
        ('Lage', 'Montageplatte {} × {} mm, {} mm hoch, an der Rückseite des '
         'hinteren 2060; der Kasten steht {} mm dahinter (Kanal {} + Platte '
         '{}),'.format(
             de(EL['platte_x'][1] - EL['platte_x'][0]),
             de(ew('platte_dicke')),
             de(EL['platte_z'][1] - EL['platte_z'][0]),
             de(ew('quer_y1') - gy[1]), de(ew('geh_abstand')),
             de(ew('platte_dicke')))),
        ('', 'endet {} mm vor dem Ende der 2040 und {} mm links der Mitte der '
         'Maschine'.format(de(gy[0] - ew('rahmen_y0')), de(-gx[1]))),
        ('Montage', '4 × M5×{} in Hammermuttern der unteren und oberen Nut '
         'des 2060, {} mm neben dem Kasten; Inbus von hinten'.format(
             de(EL['m5_schraube'], 0), de(ew('ohr_loch'), 0))),
        ('Uno', '{} mm von der linken Wand, Buchsenkante {} mm vor der '
         'Rückwand; 4 × M3×8 selbstschneidend in Stehbolzen ({} mm '
         'hoch)'.format(de(ew('uno_rand')), de(ew('uno_hinten')),
                        de(ew('uno_steg_h')))),
        ('Verteiler', '{} mm breit: hinten Buchse und Schalter ({} mm), davor '
         'der Wandler quer ({} mm), davor die Wago ({} mm): von links '.format(
             de(ix[1] - EL['vert_x'][0]), de(ew('eingang_tiefe')),
             de(ew('wandler_t')), de(ew('wago_t')))
         + ', '.join('{} {}'.format(n, typ) for n, typ, _, _, _ in wago)),
        ('Wandler', 'mittig vor dem Schalter, 2 Kabelbinder {} mm neben '
         'seiner Mitte. Vorschlag: Eingang rechts (kurz zu +24 V und GND), '
         'Ausgang links zum Laserkabel'.format(de(ew('wandler_binder'), 0))),
        ('Lüfter', '{0} × {0} × {1} mm, 24 V, auf dem Deckel über der Mitte '
         'des Uno, 4 × M3×16 mit Mutter; bläst auf die Treiber'.format(
             de(ew('luefter'), 0), de(ew('luefter_h'), 0))),
        ('Höhen', 'über der Unterkante: Boden innen {}, Uno unten {}, '
         'Treiber oben {}, Kasten {}, Deckel {}, Lüfter {} mm'.format(
             de(EL['boden_z'] - z0), de(EL['uno_z0'] - z0),
             de(EL['stapel_z1'] - z0), de(gz[1] - z0),
             de(EL['deckel_z'][1] - z0), de(EL['luefter_z'][1] - z0))),
        ('Kabel', 'links raus: über die Y-Kette X-, Z-Motor, Laser, '
         'Endschalter X und Z, dazu der linke Y-Motor; vorn in den Kanal: '
         'rechter Y-Motor, Y-Endschalter,'),
        ('', 'Not-Aus; hinten hinein: 24 V vom Steckernetzteil und USB'),
    ]
    ty = f.oy + f.hoehe + 50
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))

    # ---- Legende -----------------------------------------------------------
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'Gehäuse (PETG)'),
                                  ('platine', 'Uno + Shield + Treiber'),
                                  ('wandler', 'Wandler'),
                                  ('kauf', 'Kaufteil'),
                                  ('stahl', 'Metall (Schraube, Buchse)'),
                                  ('messing', 'Gewindeeinsatz'),
                                  ('profil', 'Aluprofil'))):
        x = 24 + (i % 4) * 190
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    x, y = 24 + 3 * 190, ly + 18
    t.append(rect_px(x, y, x + 14, y + 9, 'neu', **FACH))
    t.append(text(x + 19, y + 8, 'Elektronikfach (frei)', 8.5))
    y = ly + 36
    for i, (farbe, strich, breite, s) in enumerate((
            (VERDECKT, '2.5 2', 0.9, 'verdeckt, unter der Oberkante'),
            (LUEFTER, '5 3', 1.1, 'Lüfter im Deckel'),
            (KABEL, '5 3', 1.6, 'Kabel'),
            (LUFT, '6 3', 1.4, 'Luft'))):
        x = 24 + i * 190
        t.append(linie(x, y + 4.5, x + 16, y + 4.5, farbe, breite, strich))
        t.append(text(x + 21, y + 8, s, 8.5))
    t.append(text(24, ly + 62, 'Buchse und Schalter sind nur skizziert '
                  '(nicht gemessen); die Kabelausschnitte sind von oben '
                  'offen, die Wand ist dort {} mm niedriger.'.format(
                      de(ew('kabel_t'), 0)), 8.5, GRAU))
    W = int(f.ox + f.breite + 250)
    H = int(ly + 78)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as fd:
        fd.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
