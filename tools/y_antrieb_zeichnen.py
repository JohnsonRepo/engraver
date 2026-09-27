#!/usr/bin/env python3
"""Zeichnung des Y-Antriebs: Y-Motorhalter vorn an einer Ecke.

Draufsicht auf die rechte vordere Ecke und Schnitt durch die Motorachse.
Alle Masse kommen aus Portal.py (lage()); die Zeichnung ist massstaeblich
und wandert mit den Parametern. Die linke Ecke ist spiegelgleich.

    python3 tools/y_antrieb_zeichnen.py   ->  docs/portal-y-antrieb.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (el, f1, text, linie, pfeil, rect_px,  # noqa
                              de, TEXT, GRAU, BLAU, ROT)
from portal_zeichnen import Feld, ORANGE, RIEMEN      # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'portal-y-antrieb.svg')
WANGE = '#efbf91'          # hoehere Teile des Halters (Wange, Anlage)


def quer_mass(f, a0, a1, b, s, dy=-5):
    """Waagerechtes Mass von a0 bis a1 auf Hoehe b, Text darueber."""
    (x0, y), (x1, _) = f.px(a0, b), f.px(a1, b)
    return [linie(x0, y, x1, y, BLAU, 0.8),
            linie(x0, y - 3, x0, y + 3, BLAU, 0.8),
            linie(x1, y - 3, x1, y + 3, BLAU, 0.8),
            text((x0 + x1) / 2, y + dy, s, 8.0, BLAU, 'middle', True,
                 halo=True)]


def langloch(f, a, b0, b1, r, **mehr):
    """Langloch laengs b (zwei Halbkreise, gerade Flanken) als Pfad."""
    (xa, ya), (_, yb) = f.px(a, b0), f.px(a, b1)
    rp = r * f.s
    oben, unten = min(ya, yb), max(ya, yb)
    d = ('M {0} {1} A {2} {2} 0 0 1 {3} {1} L {3} {4} '
         'A {2} {2} 0 0 1 {0} {4} Z').format(
        f1(xa - rp), f1(oben), f1(rp), f1(xa + rp), f1(unten))
    attrs = {'d': d, 'fill': '#ffffff', 'stroke': '#c2621b',
             'stroke-width': '0.8'}
    attrs.update(mehr)
    return el('path', attrs)


# ---- Draufsicht auf die rechte vordere Ecke -------------------------------
def draufsicht(f, w, L):
    R = L['R']
    xu = lambda u: R - u                        # rechte Seite
    ye, um, ym = L['stirn_vorn_y'], L['ym_u'], L['ym_y']
    fl = w('motor_flansch') / 2.0
    lang = (f.b[0] - 5, ye)
    t = []
    gestr = {'stroke_dasharray': '4 3', 'fill_opacity': '0.35'}
    # vorderes 2060 unter dem 2040
    t.append(f.rect(f.a[0] - 5, f.a[1] + 5, *L['quer_y_vorn'], 'profil',
                    **gestr))
    # 2040 mit Schiene, der Ruecklauf in der Nut darunter
    t.append(f.rect(xu(-w('rahmen_b') / 2), xu(w('rahmen_b') / 2), *lang,
                    'profil'))
    t.append(f.rect(xu(-w('y_schiene_b') / 2), xu(w('y_schiene_b') / 2),
                    lang[0], L['y_schiene_y'][1], 'fuehrung'))
    t.append(f.linie(xu(L['yr_rueck_u']), lang[0], xu(L['yr_rueck_u']), ye,
                     RIEMEN, 1.6, '4 3'))
    # Halter: Platte mit Aussparung, Wange nach hinten
    u0, u1 = L['ymh_u']
    ui, ya = L['ymh_aus_u'][0], L['ymh_aus_y'][1]
    y1 = L['ymh_y'][1]
    umriss = [(u0, L['ymh_wange_y'][0]), (L['ymh_wange_u'][1],
                                          L['ymh_wange_y'][0]),
              (L['ymh_wange_u'][1], ye), (ui, ye), (ui, ya), (u1, ya),
              (u1, y1), (u0, y1)]
    t.append(f.poly([(xu(u), y) for u, y in umriss], 'neu'))
    t.append(f.rect(xu(L['ymh_wand_u'][0]), xu(L['ymh_wand_u'][1]),
                    *L['ymh_wand_y'], 'neu', fill=WANGE))
    t.append(f.rect(xu(L['ymh_wange_u'][0]), xu(L['ymh_wange_u'][1]),
                    L['ymh_wange_y'][0], y1, 'neu', fill=WANGE))
    # Langloecher: Bund und Motorschrauben
    weg = w('ym_spannweg')
    t.append(langloch(f, xu(um), ym - weg, ym + weg,
                      (w('motor_bund_d') + w('spiel_locker')) / 2))
    for u, dy in L['ym_schrauben']:
        t.append(langloch(f, xu(u), ym + dy - weg, ym + dy + weg,
                          w('m3_durchgang') / 2))
    # Motor unter der Platte: Umriss
    t.append(f.rect(xu(um - fl), xu(um + fl), ym - fl, ym + fl, 'kauf',
                    fill='none', stroke_dasharray='5 3', stroke_width='1.1'))
    # M5-Koepfe aussen an der Wange
    for y in L['ymh_nut_y']:
        t.append(f.rect(xu(L['ymh_wange_u'][0]),
                        xu(L['ymh_wange_u'][0] - w('m5_kopf_h')),
                        y - w('m5_kopf_d') / 2, y + w('m5_kopf_d') / 2,
                        'stahl'))
    # Ritzel und Riemen (ueber der Platte)
    t.append(f.kreis(xu(um), ym, w('ritzel_flansch_d') / 2, 'stahl'))
    t.append(f.kreis(xu(um), ym, w('ritzel_teilkreis') / 2, 'stahl',
                     fill='none', stroke_dasharray='2 2'))
    t.append(f.kreis(xu(um), ym, w('motor_welle_d') / 2, 'stahl',
                     fill='#ffffff'))
    ug, ur = w('y_riemen_linie'), L['yr_rueck_u']
    t.append(f.linie(xu(ug), lang[0], xu(ug), ym, RIEMEN, 2.4))
    t.append(f.linie(xu(ur), ye, xu(ur), ym, RIEMEN, 2.4))
    (x0, y0), (x1, _) = f.px(xu(ug), ym), f.px(xu(ur), ym)
    r = (ug - ur) / 2.0 * f.s
    t.append(el('path', {'d': 'M {} {} A {} {} 0 0 0 {} {}'.format(
        f1(x0), f1(y0), f1(r), f1(r), f1(x1), f1(y0)), 'fill': 'none',
        'stroke': RIEMEN, 'stroke-width': '2.4'}))
    return t


# ---- Schnitt durch die Motorachse ----------------------------------------
def schnitt(f, w, L):
    """Schnitt bei u = Ritzelachse, rechte Seite, Blick von der
    Maschinenmitte; vorn rechts. 2040, Schiene, Wange und Ruecklauf liegen
    dahinter."""
    ye, ym = L['stirn_vorn_y'], L['ym_y']
    fl = w('motor_flansch') / 2.0
    bo, sp = w('ritzel_bord'), w('ritzel_spur')
    lang = (f.a[0] - 5, ye)
    t = []
    # dahinter, von hinten nach vorn: Wange (aussen am 2040), 2040 mit
    # beiden Nuten, Schiene, Ruecklauf
    t.append(f.rect(L['ymh_wange_y'][0], L['ymh_y'][1], *L['ymh_wange_z'],
                    'hinten', fill='#fbeee2', stroke='#e3b48a'))
    t.append(f.rect(*lang, L['rahmen_z0'], L['rahmen_z1'], 'hinten'))
    nut = (w('rahmen_b') - 2.0 * w('nut_oben')) / 2.0
    for zm in (L['nut_z'], L['nut_z'] - w('rahmen_b')):
        t.append(f.rect(*lang, zm - nut, zm + nut, 'hinten', fill='#ffffff'))
    t.append(f.rect(lang[0], L['y_schiene_y'][1], L['y_schiene_z0'],
                    L['y_schiene_z1'], 'hinten'))
    t.append(f.rect(lang[0], ym, *L['yr_rueck_z'], 'riemen',
                    fill_opacity='0.45'))
    # 2060 (geschnitten) und Tisch
    t.append(f.rect(*L['quer_y_vorn'], *L['quer_z'], 'profil'))
    t.append(f.linie(f.a[0] - 5, L['quer_z'][0], f.a[1] + 5, L['quer_z'][0],
                     GRAU, 1.2))
    # Halter geschnitten: Platte (durch das Bund-Langloch geteilt), Anlage
    weg = w('ym_spannweg')
    rb = (w('motor_bund_d') + w('spiel_locker')) / 2.0
    for y0, y1 in ((ye, ym - weg - rb), (ym + weg + rb, L['ymh_y'][1])):
        t.append(f.rect(y0, y1, L['ymp_z0'], L['ymp_z1'], 'neu'))
    t.append(f.rect(*L['ymh_wand_y'], *L['ymh_wand_z'], 'neu', fill=WANGE))
    # Motor, Bund, Welle
    t.append(f.rect(ym - fl, ym + fl, L['ym_motor_z0'], L['ymp_z0'], 'kauf'))
    t.append(f.rect(ym - w('motor_bund_d') / 2, ym + w('motor_bund_d') / 2,
                    L['ymp_z0'], L['ym_bund_z1'], 'kauf'))
    t.append(f.rect(ym - w('motor_welle_d') / 2, ym + w('motor_welle_d') / 2,
                    L['ym_bund_z1'], L['ym_welle_ist_z1'], 'stahl'))
    # Ritzel: Nabe unten, Bord, Spur, Bord
    z1 = L['ym_ritzel_z1']
    for d, za, zb in ((w('ritzel_nabe_d'), L['ym_ritzel_z0'],
                       L['ym_nabe_z1']),
                      (w('ritzel_flansch_d'), L['ym_nabe_z1'],
                       L['ym_nabe_z1'] + bo),
                      (L['ritzel_fuss_d'], L['ym_nabe_z1'] + bo, z1 - bo),
                      (w('ritzel_flansch_d'), z1 - bo, z1)):
        for sgn in (-1, 1):
            a0 = ym + sgn * w('motor_welle_d') / 2
            a1 = ym + sgn * d / 2
            t.append(f.rect(min(a0, a1), max(a0, a1), za, zb, 'stahl'))
    # Riemen im Schnitt: vorn um das Ritzel
    rw = w('ritzel_teilkreis') / 2
    t.append(f.rect(ym + rw - L['riemen_innen'], ym + rw + L['riemen_aussen'],
                    L['yr_z0'], L['yr_z1'], 'riemen'))
    return t


def main():
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    R = L['R']
    ye, um, ym = L['stirn_vorn_y'], L['ym_u'], L['ym_y']
    fl = w('motor_flansch') / 2.0
    t = [text(24, 30, 'Y-Antrieb vorn — Motor je Ecke, Ritzel direkt auf '
              'der Welle (Portal.py Rev. {})'.format(pm.REVISION), 14, TEXT,
              fett=True),
         text(24, 48, 'Rechte vordere Ecke, die linke ist spiegelgleich. '
              'Maßstäblich, alle Maße aus Portal.py.', 9, GRAU)]

    # ---- Draufsicht --------------------------------------------------------
    s1 = 3.4
    fa = Feld(60, 90, (R - 45.0, R + 24.0), (ye - 62.0, ye + 60.0), s1,
              b_runter=True)
    t += fa.ausschnitt('drauf', draufsicht(fa, w, L))
    t += fa.rahmen('Draufsicht (vorn unten)')
    t += fa.spalte([
        (R - 3.0, ye - 20.0, '2040, Stirnseite bei der\nAnlage'),
        (R - 1.5, L['y_schiene_y'][1] - 4.0, 'Y-Schiene (Ende)'),
        (R - 40.0, L['quer_y_vorn'][0] + 5.0, 'vorderes 2060, {} mm\nhinter '
         'der Stirnseite'.format(de(w('quer_vorn_zurueck'), 0))),
        (R - L['ymh_wange_u'][0] + w('m5_kopf_h') / 2, L['ymh_nut_y'][0],
         'Wange: 2× M5×{} in\nHammermuttern der oberen\nNut außen'.format(
             de(L['ymh_schraube'], 0))),
        (R - 0.0, ye + w('ymh_wand') / 2, 'Anlage an der Stirnseite\n'
         '(nimmt den Riemenzug)'),
        (R - (w('ymh_innen') + 4.0), ye + 2.0, 'Aussparung: Toolhead am\n'
         'Schienenende'),
        (R - um + 9.0, ym + 14.0, 'Motorplatte, Langlöcher\n±{} mm '
         'zum Spannen'.format(de(w('ym_spannweg'), 0))),
        (R - um + 16.0, ym + fl - 1.0, 'NEMA 17 darunter'),
        (R - um, ym - 2.0, 'Ritzel 20 Z auf der\nMotorwelle')],
        fa.ox + fa.breite + 12, 'start', abstand=24.0)
    t += fa.zeiger(R - w('y_riemen_linie'), ye - 45.0, -36, -10,
                   'zur vorderen Klemme', 'end')
    t += fa.zeiger(R - L['yr_rueck_u'], ye - 30.0, -52, 16,
                   'Rücklauf in der Nut', 'end')
    t += fa.mass(R - um + 1.0, ye, ym, '{} ±{}'.format(
        de(w('ym_vor'), 1), de(w('ym_spannweg'), 0)), 4)
    t += quer_mass(fa, R - um, R, ye + 55.0, '{} mm'.format(de(um, 2)), 11)

    # ---- Schnitt D-D -------------------------------------------------------
    s2 = 3.0
    fb = Feld(fa.ox + fa.breite + 330, 90, (ye - 62.0, ye + 60.0),
              (L['quer_z'][0] - 8.0, L['rahmen_z1'] + 14.0), s2)
    t += fb.ausschnitt('schnitt_y', schnitt(fb, w, L))
    t += fb.rahmen('Schnitt D–D durch die Motorachse')
    t.append(text(fb.ox, fb.oy + fb.hoehe + 14, 'rechte Seite, Blick von '
                  'der Maschinenmitte; vorn rechts', 8.0, GRAU))
    t += fb.spalte([
        (ye - 50.0, L['nut_z'], 'obere Nut (dahinter),\nRücklauf mittig'),
        (ye - 50.0, L['rahmen_z1'] - 3.0, '2040 (dahinter)'),
        (L['ymh_y'][1] - 4.0, L['rahmen_z1'] - 3.0, 'Wange (dahinter)'),
        (L['quer_y_vorn'][0] + 3.0, L['quer_z'][0] + 30.0,
         'vorderes 2060,\ngeschnitten'),
        (ye - 50.0, L['quer_z'][0], 'Tisch')],
        fb.ox - 12, 'end', abstand=26.0)
    t += fb.spalte([
        (ym + w('ritzel_flansch_d') / 2 - 1.0, L['ym_ritzel_z1'] - 0.5,
         'Ritzel 20 Z, Nabe unten\nin der Bundbohrung'),
        (ym + w('ritzel_nabe_d') / 2 - 1.0, L['ym_madenschraube_z'],
         'Madenschrauben,\nInbus von vorn'),
        (L['ymh_y'][1] - 3.0, (L['ymp_z0'] + L['ymp_z1']) / 2,
         'Motorplatte {} mm'.format(de(w('mp_dicke'), 1))),
        (ym + fl - 3.0, (L['ym_motor_z0'] + L['ymp_z0']) / 2,
         'NEMA 17,\nWelle nach oben')],
        fb.ox + fb.breite + 12, 'start', abstand=26.0)
    t += fb.zeiger(ye + 1.5, L['ymh_wand_z'][1] - 1.0, 40, -58,
                   'Anlage, {} mm unter dem Riemen'.format(
                       de(w('ymh_wand_luft'), 0)))
    t += fb.mass(ye + 6.0, L['quer_z'][0], L['ym_motor_z0'], '{} mm'.format(
        de(L['ym_motor_z0'] - L['quer_z'][0], 0)), 4)
    t += fb.mass(ye - 4.0, L['yr_z0'], L['rahmen_z1'], '{} mm'.format(
        de(L['rahmen_z1'] - L['yr_z0'], 0)), 4, L['rahmen_z1'] - 4.0)
    # Pfeil: Motor nach vorn spannt den Riemen
    x0, y0 = fb.px(ym - 8.0, L['ym_motor_z0'] - 6.0)
    t += [linie(x0, y0, x0 + 18, y0, ORANGE, 1.4),
          pfeil(x0 + 21, y0, 1, 0, ORANGE),
          text(x0 + 25, y0 + 3, 'Motor nach vorn: spannen', 8.0, ORANGE,
               fett=True, halo=True)]

    # ---- Zahlen und Legende ------------------------------------------------
    ty = max(fa.oy + fa.hoehe, fb.oy + fb.hoehe) + 50
    zeilen = [
        ('Ritzelachse', '{} mm innen neben der Schienenmitte, {} ±{} mm vor '
         'der Stirnseite'.format(de(um, 2), de(w('ym_vor'), 1),
                                 de(w('ym_spannweg'), 0))),
        ('Riemen', 'gezogener Trum {} mm, Rücklauf {} mm neben der '
         'Schienenmitte'.format(de(w('y_riemen_linie'), 1),
                                de(L['yr_rueck_u'], 1))),
        ('', 'Höhe {} bis {} mm unter der Oberkante des 2040'.format(
            de(L['rahmen_z1'] - L['yr_z1'], 0),
            de(L['rahmen_z1'] - L['yr_z0'], 0))),
        ('Motor', 'Flansch {} mm unter der Oberkante des 2040, unten {} mm '
         'über dem Tisch'.format(de(L['rahmen_z1'] - L['ymp_z0'], 1),
                                 de(L['ym_motor_z0'] - L['quer_z'][0], 0))),
        ('', 'Welle {} mm (gemessen), steht {} mm über dem Ritzel'.format(
            de(w('motor_welle_ist'), 0),
            de(L['ym_welle_ist_z1'] - L['ym_ritzel_z1'], 1))),
        ('Y-Riemen', 'offen, je Seite ≈ {} mm von Klemme zu Klemme (hinteres '
         'Ritzel {} mm hinter der Stirnseite angenommen)'.format(
             de(L['yr_laenge'], 0), de(w('yh_hinter'), 0))),
        ('Schrauben', '4× M3×{} (Motor, von oben), 2× M5×{} + Hammermutter '
         '(Wange)'.format(de(L['motor_schraube'], 0),
                          de(L['ymh_schraube'], 0))),
        ('entfällt', 'Eckwelle mit Lagern, unteres Ritzel, Motorhalter in '
         'der Mitte'),
        ('Prüfung', 'tools/portal_check.py, Abschnitte 14 und 15'),
    ]
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('profil', 'Aluprofil'),
                                  ('fuehrung', 'Linearführung'),
                                  ('kauf', 'Motor'),
                                  ('stahl', 'Ritzel, Schrauben'),
                                  ('hinten', 'hinter der Schnittebene'))):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    x, y = 24 + 2 * 170, ly + 18
    t.append(linie(x, y + 4.5, x + 16, y + 4.5, RIEMEN, 2.2))
    t.append(text(x + 21, y + 8, 'GT2-Riemen', 8.5))
    t.append(text(24, ly + 50, 'Gestrichelt: liegt darunter. Wange und '
                  'Anlage (dunkler) stehen höher als die Motorplatte.',
                  8.5, GRAU))
    W = int(fb.ox + fb.breite + 190)
    H = int(ly + 66)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
