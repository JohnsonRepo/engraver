#!/usr/bin/env python3
"""Zeichnung des Pi-Halters: links die Ansicht von hinten (so, wie man ihn
an der Maschine sieht und anschraubt; X waechst dort nach links), rechts
der Schnitt durch den Pi mit dem hinteren 2060. Masse aus
fusion/PiHalter/PiHalter.py, Kasten und Rahmen aus Elektronik.py und
Portal.py, das Kabelbuendel wie in tools/pihalter_check.py.

    python3 tools/pihalter_zeichnen.py   ->  docs/pihalter.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import el, text, de, TEXT, GRAU, BLAU, FARBE  # noqa
from portal_zeichnen import Feld, quer_mass                    # noqa: E402
import pihalter_check as pc                                    # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'pihalter.svg')

FARBE.update({
    'platine': ('#cfe6d2', '#2b8a3e'),
    'kabel':   ('#e5dbff', '#7048e8'),
    'nut':     ('#ffffff', '#8c939e'),
})


def von_hinten(f, hw, HL, EL, kb):
    """Ansicht von hinten: X nach links (a_rueck), Z nach oben."""
    t = []
    a0, a1 = f.a
    zt = HL['tisch_z']
    # Tisch, hinteres 2060 mit den drei Nuten der Rueckseite
    t.append(f.linie(a0, zt, a1, zt, GRAU, 1.0))
    t.append(f.rect(a0, a1, zt, hw('rahmen_z0'), 'profil'))
    for z in HL['quer_nut_z']:
        t.append(f.rect(a0, a1, z - hw('nut_b') / 2.0, z + hw('nut_b') / 2.0,
                        'nut'))
    # Kabel in der mittleren Nut
    t.append(f.rect(max(kb.x[0], a0), min(kb.x[1], a1), *kb.z, 'kabel'))
    # Kasten (naeher am Betrachter) und Montageplatte
    t.append(f.rect(a0, EL['platte_x'][1], EL['platte_z'][0],
                    EL['platte_z'][1], 'druck'))
    t.append(f.rect(a0, EL['geh_x'][1], EL['geh_z'][0], EL['haube_z'][1],
                    'hinten', stroke_dasharray='4 3'))
    # Platte
    t.append(f.rect(*HL['x'], *HL['z'], 'neu'))
    for x0, z0, x1, z1 in HL['binder_rechtecke']:
        t.append(f.rect(x0, x1, z0, z1, 'nut'))
    # Wandler und USB-A-Stecker (gestrichelt: groesster, der passt)
    t.append(f.rect(*HL['wandler_x'], *HL['wandler_z'], 'kauf',
                    stroke_dasharray='4 3', fill_opacity='0.6'))
    sa = HL['stecker_a']
    t.append(f.rect(*sa[0], *sa[2], 'kauf', stroke_dasharray='3 2',
                    fill_opacity='0.4'))
    # Pi: Platine, Schrauben, Buchsen, Stecker
    t.append(f.rect(*HL['pi_x'], *HL['pi_z'], 'platine'))
    for x, z in HL['pi_loecher']:
        t.append(f.kreis(x, z, hw('m25_kopf_d') / 2.0, 'stahl'))
    for n, (sx, sy, sz) in sorted(HL['stecker'].items()):
        t.append(f.rect(*sx, *sz, 'kauf', stroke_dasharray='3 2',
                        fill_opacity='0.5'))
    for n, x in sorted(HL['buchse_x'].items()):
        xp, yp = f.px(x, HL['pi_z'][0] + 2.5)
        t.append(text(xp, yp + 1, n, 6.5, TEXT, 'middle'))
    xp, yp = f.px(HL['pi_x'][1] - 2.5, sum(HL['pi_z']) / 2.0)
    t.append(text(xp, yp + 2, 'SD', 6.5, TEXT, 'middle'))
    # M5-Koepfe
    for x, z in HL['m5']:
        t.append(f.kreis(x, z, hw('m5_kopf_d') / 2.0, 'stahl'))
    return t


def schnitt(f, hw, HL, kb):
    """Schnitt durch den Pi, von links gesehen: Y nach rechts (vorn),
    Z nach oben."""
    t = []
    a0, a1 = f.a
    zt = HL['tisch_z']
    yq0, yq1 = HL['quer_y']
    t.append(f.linie(a0, zt, a1, zt, GRAU, 1.0))
    t.append(f.rect(yq0, min(yq1, a1), zt, hw('rahmen_z0'), 'profil'))
    for z in HL['quer_nut_z']:
        t.append(f.rect(yq0, yq0 + hw('nut_t'), z - hw('nut_b') / 2.0,
                        z + hw('nut_b') / 2.0, 'nut', stroke='none'))
        t.append(f.rect(yq0 + hw('nut_t'), yq0 + hw('nut_kammer_t'),
                        z - hw('nut_kammer_b') / 2.0,
                        z + hw('nut_kammer_b') / 2.0, 'nut', stroke='none'))
    t.append(f.rect(*kb.y, *kb.z, 'kabel'))
    y0, y1 = HL['platte_y']
    t.append(f.rect(*HL['wandler_y'], *HL['wandler_z'], 'kauf',
                    stroke_dasharray='4 3', fill_opacity='0.35'))
    t.append(f.rect(y0, y1, *HL['z'], 'neu'))
    r = hw('steg_d') / 2.0
    for z in sorted({z for _, z in HL['pi_loecher']}):
        t.append(f.rect(*HL['steg_y'], z - r, z + r, 'neu'))
    t.append(f.rect(*HL['pcb_y'], *HL['pi_z'], 'platine'))
    t.append(f.rect(*HL['bauteile_y'], HL['pi_z'][0] + 1.0,
                    HL['pi_z'][1] - 1.0, 'platine', fill_opacity='0.45'))
    sx, sy, sz = HL['stecker']['USB']
    t.append(f.rect(*sy, *sz, 'kauf', stroke_dasharray='3 2',
                    fill_opacity='0.5'))
    # M5 mit Hammermutter in der oberen Nut
    zn, rk = HL['nut_z'], hw('m5_kopf_d') / 2.0
    t.append(f.rect(*HL['kopf_y'], zn - rk, zn + rk, 'stahl'))
    t.append(f.rect(y0, y0 + hw('m5_l'), zn - 2.5, zn + 2.5, 'stahl'))
    hq = hw('nut_kammer_b') / 2.0 - 0.1
    t.append(f.rect(y1 + hw('nut_t') + 0.1, y1 + hw('nut_kammer_t') - 0.1,
                    zn - hq, zn + hq, 'stahl'))
    return t


def main():
    th, pm, em, hm = pc.laden()
    w, L = pm.w, pm.lage()
    ew, EL = em.w, em.lage()
    hw, HL = hm.w, hm.lage()
    kb = pc.kabelbuendel(L, EL)
    (x0, x1), (z0, z1) = HL['x'], HL['z']
    t = [text(24, 30, 'Pi-Halter (PiHalter.py Rev. {}) — Pi Zero 2 W und '
              '5-V-Wandler an der Rückseite des hinteren 2060'.format(
                  hm.REVISION), 14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Rechts '
              'neben dem Elektronik-Kasten, 2 × M5×12 in der oberen Nut; '
              'Pi und Wandler ganz über dem 2060.', 9, GRAU)]

    # ---- Ansicht von hinten ------------------------------------------------
    s = 3.2
    fa = Feld(150, 92, (-62.0, 172.0), (-131.0, -14.0), s, a_rueck=True)
    t += fa.ausschnitt('hinten', von_hinten(fa, hw, HL, EL, kb))
    t += fa.rahmen('Von hinten gesehen (X wächst nach links)')
    wx, wz = HL['wandler_x'], HL['wandler_z']
    px, pz = HL['pi_x'], HL['pi_z']
    t += fa.spalte([
        (px[1] - 3.0, pz[1] - 3.0, 'SD-Karte zeigt hierher'),
        (px[0] + 30.0, pz[1] - 6.0, 'Pi Zero 2 W, Bauteile\nnach hinten, '
         '4 × M2.5×6'),
        (sum(HL['stecker']['USB'][0]) / 2.0, HL['stecker']['USB'][2][0] + 4.0,
         'Stecker in USB (W17)\nund PWR IN (W19)'),
        (HL['m5'][1][0], HL['m5'][1][1], 'M5×12 in die obere Nut'),
        (x1 - 5.0, kb.z[1] - 3.0, 'Kabel in der mittleren Nut'),
        (x1 - 5.0, HL['tisch_z'] + 8.0, 'hinteres 2060')],
        fa.ox - 12, 'end', abstand=26.0)
    t += fa.spalte([
        (sum(wx) / 2.0, wz[1] - 4.0, '5-V-Wandler: Platz\n{} × {} mm, '
         'Eingang links'.format(de(wx[1] - wx[0], 0), de(wz[1] - wz[0], 0))),
        (HL['binder_x'][0], HL['binder_z'][1], 'Schlitze für die\n'
         'Kabelbinder'),
        (sum(HL['stecker_a'][0]) / 2.0, sum(HL['stecker_a'][2]) / 2.0,
         'USB-A-Stecker am\nWandler (W19)'),
        (EL['platte_x'][1] - 6.0, EL['platte_z'][0] + 10.0,
         'Montageplatte und\nKasten (davor)'),
        (HL['m5'][0][0], HL['m5'][0][1], 'M5×12')],
        fa.ox + fa.breite + 12, 'start', abstand=26.0)
    t += quer_mass(fa, x0, x1, z1, '{} mm'.format(de(x1 - x0, 0)), -6)
    t += fa.mass(x1 + 6.0, z0, z1, '{} mm'.format(de(z1 - z0, 0)), 4)
    t += fa.luft(px[0] + 8.0, hw('rahmen_z0'), px[0] + 8.0, pz[0],
                 '{} mm über dem 2060'.format(de(pz[0] - hw('rahmen_z0'), 0)),
                 dx=5, dy=4)

    # ---- Schnitt durch den Pi ----------------------------------------------
    s2 = 3.2
    fb = Feld(fa.ox + fa.breite + 270, 92, (-288.0, -224.0), (-131.0, -14.0),
              s2)
    t += fb.ausschnitt('schnitt', schnitt(fb, hw, HL, kb))
    t += fb.rahmen('Schnitt durch den Pi (vorn rechts)')
    y0, y1 = HL['platte_y']
    t += fb.spalte([
        (y0 - 2.0, z1 - 4.0, 'Platte {} mm'.format(de(hw('platte_dicke'), 0))),
        (HL['pcb_y'][0], sum(HL['pi_z']) / 2.0, 'Pi auf Stehbolzen\n'
         '{} mm'.format(de(hw('steg_h'), 0))),
        (sum(HL['stecker']['USB'][1]) / 2.0,
         HL['stecker']['USB'][2][0] + 3.0, 'Stecker hängt\nnach unten'),
        (HL['wandler_y'][0] + 2.0, HL['wandler_z'][1] - 3.0,
         'Wandler (dahinter)'),
        (sum(kb.y) / 2.0, kb.z[0] + 2.0, 'Kabelbündel W2, W10,\nW14, W18')],
        fb.ox - 12, 'end', abstand=26.0)
    t += fb.spalte([
        (y1 + 10.0, -74.0, 'hinteres 2060'),
        (y1 + hw('nut_t') + 1.0, HL['nut_z'] + 3.0, 'Hammermutter in\nder '
         'oberen Nut')],
        fb.ox + fb.breite + 12, 'start', abstand=26.0)
    t += fb.luft(y1 - 2.0, kb.z[1], y1 - 2.0, z0, '{} mm'.format(
        de(z0 - kb.z[1], 0)), dx=-5, dy=12, anker='end')

    # ---- Zahlen ------------------------------------------------------------
    ty = fa.oy + fa.hoehe + 44
    zeilen = [
        ('Platte', '{} × {} × {} mm, PETG; die Seite am 2060 aufs Bett, '
         'Stehbolzen nach oben, keine Stützen'.format(
             de(x1 - x0, 0), de(z1 - z0, 0), de(hw('platte_dicke'), 0))),
        ('Lage', 'X {} bis {} (Maschinenkoordinaten), {} mm rechts neben '
         'der Montageplatte des Kastens'.format(
             de(x0, 0), de(x1, 0), de(x0 - EL['platte_x'][1], 1))),
        ('Montage', '2 Hammermuttern M5 in die obere Nut der Rückseite des '
         '2060, 2 × M5×{} bei X {} und {}'.format(
             de(hw('m5_l'), 0), de(HL['m5'][0][0], 0),
             de(HL['m5'][1][0], 0))),
        ('Pi', 'Lochbild 58 × 23 mm, 4 × M2.5×{} selbstschneidend '
         '(Kernloch {}); Buchsen unten, von hinten gesehen von links: HDMI, '
         'USB, PWR IN'.format(de(hw('m25_l'), 0), de(hw('m25_kern'), 1))),
        ('Wandler', 'bis {} × {} × {} mm, Eingang zur Kastenseite, USB-A '
         'zum Pi; 2 Kabelbinder senkrecht über seine Rückseite'.format(
             de(hw('wandler_l'), 0), de(hw('wandler_b'), 0),
             de(hw('wandler_h'), 0))),
    ]
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(100, ty + 10 + i * 15, v, 8.5, TEXT))
    W = int(fb.ox + fb.breite + 170)
    H = int(ty + 10 + len(zeilen) * 15 + 16)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="{0}" height="{1}" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
