#!/usr/bin/env python3
"""Zeichnung: Spannsystem mit Werkstueckerkennung — Konzept.

Draufsicht auf das Bett mit Anschlagleiste, linkem Anschlag, Spannbacke
und ihrem Antrieb unter dem linken 2040; dazu ein Querschnitt durch die
linke Seite: Fuehrung, Halter und Backe gegen den Toolhead am Z-Softlimit.
Alle Lagen kommen aus tools/spannsystem_check.py (und damit aus Portal.py
und ToolheadZ.py); der Antrieb ist als Bauraum gezeichnet, bis die Teile in
Fusion stehen.

    python3 tools/spannsystem_zeichnen.py   ->  docs/spannsystem.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spannsystem_check as sc                        # noqa: E402
from spannsystem_check import w, bei                  # noqa: E402
from antrieb_zeichnen import (el, f1, text, linie, pfeil,  # noqa: E402
                              rect_px, de, TEXT, GRAU, BLAU, ROT, FARBE)
from portal_zeichnen import Feld, ORANGE, RIEMEN      # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'spannsystem.svg')

FARBE.update({
    'alu':    ('#d5dbe3', '#5c6670'),       # Alu-Flachstange
    'holz':   ('#f4efe4', '#b3a07c'),       # Opferplatte
    'platte': ('#d9ead0', '#4f7d3a'),       # Werkstueck
})
BEISPIEL = (300.0, 200.0)       # Werkstueck B x T fuer die Zeichnung
TOOLHEAD_BIS = -80.0            # Querschnitt: Toolhead darueber abgeschnitten
STRICH = {'stroke_dasharray': '4 3'}


def _q(f, q, art, **mehr):
    return f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art, **mehr)


def _qz(f, q, art, **mehr):
    """Quader im Querschnitt (X waagerecht, Z senkrecht)."""
    return f.rect(q.x[0], q.x[1], q.z[0], q.z[1], art, **mehr)


def punkt(f, a, b, farbe=ROT, r=4.0):
    x, y = f.px(a, b)
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': f1(r),
                         'fill': farbe, 'stroke': '#ffffff',
                         'stroke-width': '1.2'})


# ---- Draufsicht -------------------------------------------------------------
def draufsicht(f, K, c):
    L = K['L']
    R = L['R']
    t = []
    # Opferplatte auf dem Tisch, darauf Leiste, Anschlag, Werkstueck
    t.append(_q(f, K['opfer'], 'holz'))
    # Arbeitsflaeche (Strahl) und Reichweite der tiefen Teile
    ax, ay = K['arbeit_x'], K['arbeit_y']
    t.append(f.rect(ax[0], ax[1], ay[0], ay[1], 'toolhead', fill='none',
                    stroke_dasharray='6 4', stroke_width='1.1'))
    rx, ry = K['reich_x'], K['reich_y']
    t.append(f.rect(rx[0], rx[1], ry[0], ry[1], 'toolhead', fill='none',
                    stroke=ROT, stroke_dasharray='2 3', stroke_width='0.9'))
    x0, yf = K['x0'], K['yf']
    b, h = BEISPIEL
    t.append(f.rect(x0, x0 + b, yf - h, yf, 'platte'))
    for n in ('leiste', 'anschlag'):
        t.append(_q(f, K[n], 'alu'))
    t.append(_q(f, K['halter_r'], 'neu'))
    # 2060 quer (auf dem Tisch)
    for y in (L['quer_y_vorn'], L['quer_y_hinten']):
        t.append(f.rect(L['quer_x'][0], L['quer_x'][1], y[0], y[1],
                        'profil'))
    # Antrieb: Schiene, Wagen und Halterplatte liegen unter dem 2040,
    # Motor und Riemen daneben
    t.append(_q(f, K['halter_h'], 'neu'))
    t.append(_q(f, K['halter_v'], 'neu', fill_opacity='0.75'))
    t.append(_q(f, K['motor'], 'kauf'))
    t.append(_q(f, K['ritzel'], 'kauf'))
    t.append(_q(f, K['rolle'], 'kauf'))
    rz = K['riemen']
    t.append(f.rect(rz.x[0] + 1.5, rz.x[1] - 1.5, rz.y[0], rz.y[1], 'kauf',
                    fill=RIEMEN, stroke=RIEMEN))
    # Backe offen (hinten, gestrichelt) und gespannt am Beispiel
    for m in K['schlitten']:
        if m.name in ('Backe', 'Backenblock'):
            t.append(_q(f, bei(m, K['c'][0]),
                        'alu' if m.name == 'Backe' else 'neu', fill='none',
                        **STRICH))
    for m in K['schlitten']:
        q = bei(m, c)
        art = {'Backe': 'alu', 'Wagen MGN9H': 'fuehrung'}.get(m.name, 'neu')
        mehr = {} if m.name in ('Backe', 'Backenblock',
                                'Riemenklemme') else dict(
            fill_opacity='0.55', **STRICH)
        t.append(_q(f, q, art, **mehr))
    t.append(_q(f, K['schiene'], 'fuehrung', fill_opacity='0.5', **STRICH))
    # 2040 laengs: liegen oben auf den 2060, ueber allem
    for s in (-1, 1):
        t.append(f.rect(s * (R - 10.0), s * (R + 10.0), *L['rahmen_y'],
                        'profil', fill_opacity='0.45', **STRICH))
    # Toolhead (tiefe Teile) vorn links und hinten links
    for dy, mehr in ((K['d_vorn'], {'fill_opacity': '0.6'}),
                     (-K['d_hinten'], dict(fill='none', **STRICH))):
        for q in K['tief']:
            t.append(f.rect(q.x[0] + ax[0], q.x[1] + ax[0], q.y[0] + dy,
                            q.y[1] + dy, 'toolhead', **mehr))
    # Lichtschranken (fest): Anlage der Leiste, Referenz hinten
    t.append(punkt(f, K['leiste'].x[0] + 3.0, K['yv'] - 6.0))
    t.append(punkt(f, K['halter_h'].x[1] + 4.0, K['halter_h'].y[1] - 6.0))
    # Spannrichtung und gemessene Tiefe
    xm = x0 + 60.0
    t += f.mass(xm, yf - h, yf, 'T = {} mm gemessen'.format(de(h, 0)),
                b_text=yf - h / 2.0)
    xa, ya = f.px(-150.0, yf - h - 22.0)
    _, yb = f.px(-150.0, yf - h - 6.0)
    t.append(linie(xa, ya, xa, yb, ORANGE, 1.6))
    t.append(pfeil(xa, yb, 0.0, 1.0, ORANGE))
    t.append(punkt(f, x0, yf, BLAU, 3.5))
    return t


# ---- Querschnitt links ----------------------------------------------------
def querschnitt(f, K, c, s_laser):
    L, TL = K['L'], K['TL']
    R = L['R']
    t = []
    zt = K['z_tisch']
    t.append(f.rect(f.a[0] - 5, f.a[1] + 5, zt - 8.0, zt, 'profil',
                    fill='#f1efe9', stroke='none'))
    t.append(f.linie(f.a[0], zt, f.a[1], zt, GRAU, 1.0))
    t.append(_qz(f, K['opfer'], 'holz'))
    # Werkstueck (3 mm) liegt vor der Schnittebene: nur der Umriss
    t.append(f.rect(K['x0'], f.a[1] + 5, K['z_b'], K['z_b'] + 3.0,
                    'platte', fill='none', **STRICH))
    # 2040 mit Y-Schiene, MGN9 darunter
    t.append(f.rect(-R - 10.0, -R + 10.0, L['rahmen_z0'], L['rahmen_z1'],
                    'profil'))
    t.append(f.rect(-R - 6.0, -R + 6.0, L['rahmen_z1'],
                    L['rahmen_z1'] + 8.0, 'fuehrung'))
    t.append(_qz(f, K['schiene'], 'fuehrung'))
    # Motor und Ritzel stehen vorn am Ende des Wegs (gestrichelt)
    for n in ('motor', 'ritzel'):
        t.append(_qz(f, K[n], 'kauf', fill='none', **STRICH))
    rz = K['riemen']
    zo, zu = K['riemen_oben_z'], 2.0 * K['motor_achse'][1] - K['riemen_oben_z']
    for z in (zo, zu):
        t.append(f.rect(rz.x[0], rz.x[1], z - 0.7, z + 0.7, 'kauf',
                        fill=RIEMEN, stroke=RIEMEN))
    for m in K['schlitten']:
        art = {'Backe': 'alu', 'Wagen MGN9H': 'fuehrung'}.get(m.name, 'neu')
        t.append(_qz(f, bei(m, c), art))
    # Toolhead ganz links am Z-Softlimit, Laser in der empfohlenen Stellung
    # (nur der untere Teil, oben abgeschnitten)
    zc = K['zc_soft']
    for q in K['tief']:
        dz = zc + (s_laser if q.name == 'Diodenlaser' else 0.0)
        t.append(f.rect(q.x[0] + L['xw_min'], q.x[1] + L['xw_min'],
                        q.z[0] + dz, min(q.z[1] + dz, TOOLHEAD_BIS),
                        'toolhead', fill_opacity='0.45'))
    t.append(f.linie(L['xw_min'] - 25.0, TOOLHEAD_BIS, L['xw_min'] + 50.0,
                     TOOLHEAD_BIS, '#2f5d92', 0.8, '2 2'))
    # Grenze: links davon kommt der Toolhead nicht hin
    t.append(f.linie(K['x_frei'], f.b[0], K['x_frei'], f.b[1], ROT, 0.9,
                     '5 3'))
    return t


def main():
    K = sc.konzept()
    L, TL, tw = K['L'], K['TL'], K['tw']
    th, pm = K['th'], K['pm']
    b, h = BEISPIEL
    c = K['yf'] - h - w('backe_vor')            # Haltermitte am Beispiel
    hmin, hmax = K['tiefe']
    t = [text(24, 30, 'Spannsystem mit Werkstückerkennung — Konzept '
              '(Portal.py Rev. {}, ToolheadZ.py Rev. {})'.format(
                  pm.REVISION, th.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, Lagen aus tools/spannsystem_check.py. '
              'Der Antrieb ist als Bauraum gezeichnet, die Teile folgen in '
              'Fusion. Beispiel: Platte {} × {} mm.'.format(de(b, 0),
                                                            de(h, 0)),
              9, GRAU)]

    # ---- Draufsicht --------------------------------------------------------
    s1 = 1.1
    fa = Feld(262, 92, (-312.0, 274.0), (-222.0, 214.0), s1, b_runter=True)
    t += fa.ausschnitt('drauf', draufsicht(fa, K, c))
    t += fa.rahmen('Draufsicht auf das Bett (vorn unten), Backe gespannt')
    ax, ay = K['arbeit_x'], K['arbeit_y']
    sch = next(m for m in K['schlitten'] if m.name == 'Halterplatte')
    t += fa.spalte([
        (-L['R'], -120.0, 'linkes 2040 (oben,\ngestrichelt)'),
        (K['riemen'].x[0], -60.0, 'GT2-Riemen außen\nneben dem 2040'),
        (-257.0, 40.0, 'MGN9 unter dem 2040,\nWagen + Backenhalter'),
        (K['motor'].x[0] + 6.0, K['motor'].y[0] + 10.0,
         'NEMA 17 quer unter dem\n2040, Welle nach außen'),
        (K['leiste'].x[0] + 3.0, K['yv'] - 6.0,
         'Lichtschranke „Anlage“:\nLeiste federt 1 mm'),
        (K['halter_h'].x[1] + 4.0, K['halter_h'].y[1] - 6.0,
         'Lichtschranke „Referenz“\n(Backe ganz offen)'),
        (-280.0, L['quer_y_hinten'][0] + 10.0, 'hinteres 2060'),
        (-280.0, L['quer_y_vorn'][0] + 10.0, 'vorderes 2060'),
        (sch.x[0] + 4.0, c, 'Backenhalter\n(unter dem 2040)'),
        (ax[0] - 10.0, ay[1] - 4.0,
         'Toolhead vorn links\n(Laser, Schlittenplatte)')],
        fa.ox - 12, 'end', abstand=24.0)
    t += fa.spalte([
        (K['x0'] + 2.0, K['yf'] - 2.0, 'Nullpunkt: Plattenecke'),
        (K['x0'] + 150.0, K['yf'] - 100.0, 'Werkstück {} × {}'.format(
            de(b, 0), de(h, 0))),
        (-100.0, c + w('backe_vor') - 7.0,
         'Spannbacke (Alu 15 × 3),\ndrückt nach vorn'),
        (-60.0, K['c'][0] + w('backe_vor') - 7.0,
         'Backe offen (Parkstellung)'),
        (100.0, K['yv'] - 12.0, 'Anschlagleiste (Alu 25 × 3)\nam vorderen '
         '2060'),
        (K['halter_r'].x[1] - 4.0, K['yv'] - 8.0, 'Leistenhalter rechts'),
        (K['anschlag'].x[1] - 4.0, K['anschlag'].y[0] + 4.0,
         'linker Anschlag'),
        (ax[1] - 10.0, ay[0] + 30.0,
         'Arbeitsfläche (Strahl)\n{} × {} mm'.format(
             de(ax[1] - ax[0], 0), de(ay[1] - ay[0], 0))),
        (K['reich_x'][1] - 5.0, K['reich_y'][0] + 70.0,
         'Reichweite Laser +\nSchlittenplatte (rot)')],
        fa.ox + fa.breite + 12, 'start', abstand=24.0)

    # ---- Querschnitt --------------------------------------------------------
    s2 = 2.2
    s_laser = sc.fokus(K, 10.0, tw('werkstueck_max'))[2]
    fb = Feld(262, fa.oy + fa.hoehe + 80, (-306.0, -130.0), (-133.0, -20.0),
              s2)
    t += fb.ausschnitt('quer', querschnitt(fb, K, c, s_laser))
    t += fb.rahmen('Querschnitt links, von vorn: Antrieb unter dem 2040, '
                   'Toolhead ganz links am Z-Softlimit')
    bk = next(m for m in K['schlitten'] if m.name == 'Backe')
    bl = next(m for m in K['schlitten'] if m.name == 'Backenblock')
    pl = next(q for q in K['tief'] if q.name == 'Schlittenplatte')
    z_pl = pl.z[0] + K['zc_soft']
    t += fb.spalte([
        (-260.0, -45.0, 'linkes 2040 mit\nY-Schiene MGN12'),
        (-257.0, K['schiene'].z[0] + 2.0, 'MGN9-Schiene, darunter\nder '
         'Wagen'),
        (K['riemen'].x[0] + 1.0, K['riemen_oben_z'],
         'Riemen (oben: Klemme)'),
        (K['motor'].x[0] + 4.0, K['motor'].z[0] + 6.0,
         'Motor vorn am Ende des\nWegs (gestrichelt)'),
        (-280.0, K['z_tisch'] - 3.0, 'Tisch'),
        (-200.0, K['z_tisch'] + 2.0, 'Opferplatte {} mm'.format(
            de(w('opfer_dicke'), 0)))],
        fb.ox - 12, 'end', abstand=26.0)
    t += fb.spalte([
        (sch.x[1] - 4.0, sch.z[0] + 2.0,
         'Halterplatte: fährt über\nden Motor hinweg'),
        (bl.x[0] + 2.0, -105.0, 'Block mit Feder\n(Spannkraft)'),
        (-150.0, bk.z[1] - 0.5, 'Backe {} mm über\nder Opferplatte'.format(
            de(bk.z[1] - K['z_b'], 1))),
        (-160.0, z_pl + 4.0, 'Toolhead: Schlittenplatte\nam Z-Softlimit'),
        (-185.0, TOOLHEAD_BIS, 'Toolhead darüber\nabgeschnitten'),
        (-120.0, K['z_b'] + 1.5, 'Werkstück 3 mm\n(vor dem Schnitt)'),
        (K['x_frei'], -40.0, 'bis hier kommt der\nToolhead nicht (3 mm)')],
        fb.ox + fb.breite + 12, 'start', abstand=26.0)
    t += fb.luft(-170.0, bk.z[1], -170.0, z_pl, '{} mm'.format(
        de(z_pl - bk.z[1], 1)), dx=5, dy=-4)

    # ---- Zahlen ------------------------------------------------------------
    ty = fb.oy + fb.hoehe + 120         # unter den Beschriftungen
    zc_soft = K['zc_soft']
    f_tief = (zc_soft + TL['laser_unten_rel'] + TL['langloch_ab_max']
              - K['z_b'])
    f_hoch = (TL['zc_arbeit_max'] + TL['laser_unten_rel']
              + TL['langloch_auf_max'] - K['z_b'] - tw('werkstueck_max'))
    kraft = (w('feder_vor') + w('feder_k') * w('spann_leicht'),
             w('feder_vor') + w('feder_k') * w('spann_fest'))
    b_l = sc.leistung_mit_spannmotor()
    zeilen = [
        ('Nullpunkt', 'Plattenecke vorn links: Leiste am vorderen 2060 '
         '(Y), linker Anschlag (X) — immer dieselbe Maschinenkoordinate'),
        ('Werkstück', 'erkannt: liegt an (ja/nein) und seine Tiefe T, {} '
         'bis {} mm; Breite und Dicke nicht — dafür später ein Taster am '
         'Toolhead'.format(de(hmin, 0), de(hmax, 0))),
        ('Strahl', 'erreicht ab der Ecke {} × {} mm (B × T)'.format(
            de(ax[1] - K['x0'], 0), de(K['yf'] - ay[0], 0))),
        ('Höhe', 'Leiste, Anschlag und Backe höchstens {} mm über der '
         'Opferplatte; Z-Softlimit $132 ≈ {} statt 84: die Schlittenplatte '
         'bleibt {} mm darüber'.format(
             de(K['h_flach'], 1), de(TL['zc_arbeit_max'] - zc_soft - 1.5,
                                     0),
             de(w('luft_kopf'), 0))),
        ('Fokus', 'f von {} bis {} mm für 0 … {} mm Werkstück; '
         'Langlochstellung je f in spannsystem.md'.format(
             de(math.ceil(f_tief - 1e-6), 0), de(math.floor(f_hoch), 0),
             de(tw('werkstueck_max'), 0))),
        ('Kraft', 'Feder der Backe: leicht {} N, fest {} N; die Leiste '
         'schaltet bei {} N — der Motor schiebt nur'.format(
             de(kraft[0], 0), de(kraft[1], 0), de(w('leiste_vor'), 0))),
        ('Antrieb', 'NEMA 17, GT2 20 Z, {} Schritte/mm, {} mm Weg, '
         'Spannen ≈ 10 s; Steuerung: Arduino Nano + TMC2209'.format(
             de(200.0 * w('mikroschritte') / 40.0, 0),
             de(K['c'][1] - K['c'][0], 0))),
        ('Leistung', '≈ {} W mit Spannmotor, Netzteil dauernd {} W'.format(
            de(b_l['summe_neu'], 0), de(b_l['dauer'], 0))),
    ]
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(100, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('alu', 'Alu-Flachstange'),
                                  ('kauf', 'Kaufteil'),
                                  ('fuehrung', 'Linearführung'),
                                  ('profil', 'Aluprofil'),
                                  ('toolhead', 'Toolhead (tiefe Teile)'),
                                  ('holz', 'Opferplatte'),
                                  ('platte', 'Werkstück'))):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    y = ly + 36
    t.append(el('circle', {'cx': '31', 'cy': f1(y + 4.5), 'r': '4.5',
                           'fill': ROT}))
    t.append(text(43, y + 8, 'Gabellichtschranke (fest)', 8.5))
    t.append(linie(24 + 170, y + 4.5, 24 + 186, y + 4.5, BLAU, 1.1, '6 4'))
    t.append(text(24 + 191, y + 8, 'Arbeitsfläche (Strahl)', 8.5))
    t.append(linie(24 + 340, y + 4.5, 24 + 356, y + 4.5, ROT, 0.9, '2 3'))
    t.append(text(24 + 361, y + 8, 'Reichweite der tiefen Teile', 8.5))
    t.append(text(24, ly + 66, 'Gestrichelt: unter dem 2040 bzw. andere '
                  'Stellung (Backe offen, Toolhead hinten links).', 8.5,
                  GRAU))
    W = int(fa.ox + fa.breite + 250)
    H = int(ly + 82)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
