#!/usr/bin/env python3
"""Zeichnung des Portals: Y-Schlitten, X-Antrieb und beide Spanner.

Draufsicht auf beide Portalenden mit dem Toolhead am Ende des X-Wegs,
Schnitt durch die Y-Klemmtuerme (Spanner), Schnitte durch Umlenkung und
Motorhalter, dazu quer durch einen Klemmturm (seit Portal Rev. 25). Alle
Masse kommen aus Portal.py und ToolheadZ.py; die Zeichnung ist
massstaeblich und wandert mit den Parametern.

    python3 tools/portal_zeichnen.py   ->  docs/portal-y-schlitten.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
from antrieb_zeichnen import (el, f1, text, linie, pfeil, rect_px,  # noqa
                              kreis_px, poly_px, de, TEXT, GRAU, BLAU, ROT,
                              FARBE)

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'portal-y-schlitten.svg')

FARBE.update({
    'neu':      ('#f6d7b8', '#c2621b'),     # neue Druckteile
    'fuehrung': ('#d7d7dc', '#55555e'),
    'profil':   ('#e4e6ea', '#8c939e'),
    'riemen':   ('#2b2f36', '#2b2f36'),
    'toolhead': ('#c9d9ec', '#2f5d92'),     # vorhandener Toolhead
})
ORANGE = '#c2621b'
RIEMEN = '#2b2f36'


def _schneiden(p1, p2, p3, p4):
    """Kreuzen sich die Strecken p1-p2 und p3-p4 (echt, nicht nur am
    Ende beruehrend)?"""
    def kreuz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    return (kreuz(p3, p4, p1) * kreuz(p3, p4, p2) < 0
            and kreuz(p1, p2, p3) * kreuz(p1, p2, p4) < 0)


def quer_mass(f, a0, a1, b, s, dy=-5):
    """Waagerechtes Mass von a0 bis a1 auf Hoehe b, Text darueber (bis
    Portal Rev. 15 in y_antrieb_zeichnen.py)."""
    (x0, y), (x1, _) = f.px(a0, b), f.px(a1, b)
    return [linie(x0, y, x1, y, BLAU, 0.8),
            linie(x0, y - 3, x0, y + 3, BLAU, 0.8),
            linie(x1, y - 3, x1, y + 3, BLAU, 0.8),
            text((x0 + x1) / 2, y + dy, s, 8.0, BLAU, 'middle', True,
                 halo=True)]


class Feld:
    """Ansicht: waagerecht a, senkrecht b (beides mm), Massstab s px/mm.
    a_rueck: a waechst nach links. b_runter: b waechst nach unten
    (Draufsicht: Y nach vorn unten), sonst nach oben (Z)."""

    def __init__(self, ox, oy, a, b, s, a_rueck=False, b_runter=False):
        self.ox, self.oy, self.a, self.b, self.s = ox, oy, a, b, s
        self.a_rueck, self.b_runter = a_rueck, b_runter
        self.breite = (a[1] - a[0]) * s
        self.hoehe = (b[1] - b[0]) * s

    def px(self, a, b):
        x = (self.ox + (self.a[1] - a) * self.s if self.a_rueck
             else self.ox + (a - self.a[0]) * self.s)
        y = (self.oy + (b - self.b[0]) * self.s if self.b_runter
             else self.oy + (self.b[1] - b) * self.s)
        return x, y

    def rect(self, a0, a1, b0, b1, art, **mehr):
        (xa, ya), (xb, yb) = self.px(a0, b0), self.px(a1, b1)
        return rect_px(xa, ya, xb, yb, art, **mehr)

    def kreis(self, a, b, r, art, **mehr):
        x, y = self.px(a, b)
        return kreis_px(x, y, r * self.s, art, **mehr)

    def poly(self, punkte, art, **mehr):
        return poly_px([self.px(a, b) for a, b in punkte], art, **mehr)

    def linie(self, a0, b0, a1, b1, farbe=GRAU, breite=0.7, strich=None):
        (x0, y0), (x1, y1) = self.px(a0, b0), self.px(a1, b1)
        return linie(x0, y0, x1, y1, farbe, breite, strich)

    def ausschnitt(self, name, inhalt):
        r = el('rect', {'x': f1(self.ox), 'y': f1(self.oy),
                        'width': f1(self.breite), 'height': f1(self.hoehe)})
        return ([el('clipPath', {'id': name}, r),
                 '<g clip-path="url(#{})">'.format(name)] + inhalt + ['</g>'])

    def rahmen(self, titel):
        return [el('rect', {'x': f1(self.ox), 'y': f1(self.oy),
                            'width': f1(self.breite),
                            'height': f1(self.hoehe), 'fill': 'none',
                            'stroke': '#b9c2cf', 'stroke-width': '0.8'}),
                text(self.ox, self.oy - 8, titel, 10.5, BLAU, fett=True)]

    def zeiger(self, a, b, dx, dy, s, anker='start', gr=8.0):
        x, y = self.px(a, b)
        return [linie(x, y, x + dx, y + dy, GRAU, 0.6),
                el('circle', {'cx': f1(x), 'cy': f1(y), 'r': '1.4',
                              'fill': GRAU}),
                text(x + dx + (3 if anker == 'start' else -3), y + dy + 3,
                     s, gr, TEXT, anker, halo=True)]

    def spalte(self, eintraege, x_text, anker, abstand=26.0, gr=8.0,
               unten=None):
        """Beschriftungen in einer Spalte neben dem Feld. eintraege:
        [(a, b, text)], text darf Zeilenumbrueche enthalten. Jede steht so
        nah an der Hoehe ihres Ziels wie moeglich, ohne Ueberlappung; die
        Reihenfolge wird so getauscht, dass sich moeglichst wenige
        Zeigerlinien kreuzen. unten: tiefste Grundlinie der letzten
        Zeile — reicht der Platz nicht, rueckt die Spalte nach oben."""
        ziele = sorted(((self.px(a, b), s) for a, b, s in eintraege),
                       key=lambda t: t[0][1])
        xl = x_text - 3 if anker == 'start' else x_text + 3

        def setzen(reihe):
            extra = [(len(s.split('\n')) - 1) * 10 for _, s in reihe]
            ty, belegt = [], -1e9
            for ((_, y), _), e in zip(reihe, extra):
                ty.append(max(y + 3, belegt + abstand))
                belegt = ty[-1] + e
            if unten is not None:
                grenze = unten
                for i in range(len(reihe) - 1, -1, -1):
                    ty[i] = min(ty[i], grenze - extra[i])
                    grenze = ty[i] - abstand
            return ty

        def kreuzungen(reihe):
            ty = setzen(reihe)
            linien = [(p, (xl, t - 3)) for (p, _), t in zip(reihe, ty)]
            return sum(_schneiden(*linien[i], *linien[j])
                       for i in range(len(linien))
                       for j in range(i + 1, len(linien)))

        # benachbarte Eintraege tauschen, solange das Kreuzungen spart
        n = kreuzungen(ziele)
        while n:
            besser = None
            for i in range(len(ziele) - 1):
                probe = ziele[:i] + [ziele[i + 1], ziele[i]] + ziele[i + 2:]
                k = kreuzungen(probe)
                if k < n and (besser is None or k < besser[0]):
                    besser = (k, probe)
            if besser is None:
                break
            n, ziele = besser
        out = []
        for ((x, y), s), ty in zip(ziele, setzen(ziele)):
            out += [linie(x, y, xl, ty - 3, GRAU, 0.6),
                    el('circle', {'cx': f1(x), 'cy': f1(y), 'r': '1.5',
                                  'fill': GRAU})]
            for i, z in enumerate(s.split('\n')):
                out.append(text(x_text, ty + i * 10, z, gr, TEXT, anker,
                                halo=True))
        return out

    def luft(self, a0, b0, a1, b1, s, anker='start', dx=6, dy=-6):
        """Rotes Luftmass zwischen zwei Punkten, Text neben dem zweiten."""
        (x0, y0), (x1, y1) = self.px(a0, b0), self.px(a1, b1)
        lang = math.hypot(x1 - x0, y1 - y0) or 1.0
        ux, uy = (x1 - x0) / lang, (y1 - y0) / lang
        return [linie(x0, y0, x1, y1, ROT, 0.9),
                pfeil(x0, y0, -ux, -uy, ROT), pfeil(x1, y1, ux, uy, ROT),
                text(x1 + dx, y1 + dy, s, 8.0, ROT, anker, True, halo=True)]

    def mass(self, a, b0, b1, s, dx=5, b_text=None):
        """Senkrechtes Mass bei a von b0 bis b1, Text rechts daneben (auf
        Hoehe b_text, sonst in der Mitte)."""
        (x, y0), (_, y1) = self.px(a, b0), self.px(a, b1)
        yt = (y0 + y1) / 2 if b_text is None else self.px(a, b_text)[1]
        return [linie(x, y0, x, y1, BLAU, 0.8),
                linie(x - 3, y0, x + 3, y0, BLAU, 0.8),
                linie(x - 3, y1, x + 3, y1, BLAU, 0.8),
                text(x + dx, yt + 3, s, 8.0, BLAU, 'start', True, halo=True)]


# ---- Draufsicht auf ein Portalende --------------------------------------
def draufsicht(f, s, w, L, tw, TL, feste_th):
    """Ein Portalende von oben (vorn unten), Toolhead am Ende des X-Wegs.
    Gemalt von unten nach oben: Rahmen und Riemen unter der Platte zuerst
    (gestrichelt), dann Schlitten, Rohr, Toolhead, Halter und Motor."""
    R = L['R']
    xu = lambda u: s * (R - u)
    t = []
    gestr = {'stroke_dasharray': '4 3', 'fill_opacity': '0.35'}
    # Rahmen, Schiene, Wagen, Klemmtuerme: unter der Platte
    for u0, u1, art in ((-w('rahmen_b') / 2, w('rahmen_b') / 2, 'profil'),
                        (-w('y_schiene_b') / 2, w('y_schiene_b') / 2,
                         'fuehrung')):
        t.append(f.rect(xu(u0), xu(u1), f.b[0] - 5, f.b[1] + 5, art, **gestr))
    t.append(f.rect(xu(-w('y_wagen_breite') / 2), xu(w('y_wagen_breite') / 2),
                    L['wagen_y0'], L['wagen_y1'], 'fuehrung', **gestr))
    for ty in (L['kt_y_hinten'], L['kt_y_vorn']):
        t.append(f.rect(xu(L['kt_u'][0]), xu(L['kt_u'][1]), *ty, 'neu',
                        stroke_dasharray='4 3', fill_opacity='0.3'))
    # Y-Riemen (unter der Platte): zwei Enden, je eines in einem Klemmturm.
    # Der Ruecklauf laeuft in der aeusseren oberen Nut des 2040.
    enden = ((f.b[0] - 5, L['kt_y_hinten'][1] - 1.0),
             (L['kt_y_vorn'][0] + 1.0, f.b[1] + 5))
    for y0, y1 in enden:
        t.append(f.linie(xu(L['y_riemen_linie']), y0,
                         xu(L['y_riemen_linie']), y1, RIEMEN, 2.0, '7 3'))
    t.append(f.linie(xu(L['yr_rueck_u']), f.b[0] - 5, xu(L['yr_rueck_u']),
                     f.b[1] + 5, RIEMEN, 1.2, '2 3'))
    # Schlitten
    t.append(f.rect(xu(L['platte_u'][0]), xu(L['platte_u'][1]),
                    L['platte_y0'], L['platte_y1'], 'neu'))
    for (u0, u1), (y0, y1) in ((L['rueck_u'], (L['rueck_y0'], L['rueck_y1'])),
                               (L['stirn_u'], L['stirn_y'])):
        t.append(f.rect(xu(u0), xu(u1), y0, y1, 'neu', fill='#efbf91'))
    for u, y in (L['wagen_loecher'] + L['kt_schrauben_hinten']
                 + L['kt_schrauben_vorn']):
        t.append(f.kreis(xu(u), y, w('m3_senkung') / 2, 'neu',
                         fill='#ffffff'))
    # verdeckt unter der Platte: Kanten der Klemmtuerme, Y-Riemen
    for ty in (L['kt_y_hinten'], L['kt_y_vorn']):
        t.append(f.rect(xu(L['kt_u'][0]), xu(L['kt_u'][1]), *ty, 'neu',
                        fill='none', stroke_dasharray='4 3'))
    for y0, y1 in enden:
        y0, y1 = max(y0, L['platte_y0']), min(y1, L['platte_y1'])
        t.append(f.linie(xu(L['y_riemen_linie']), y0,
                         xu(L['y_riemen_linie']), y1, RIEMEN, 1.2, '7 3'))
    t.append(f.linie(xu(L['yr_rueck_u']), L['platte_y0'],
                     xu(L['yr_rueck_u']), L['platte_y1'], RIEMEN, 1.0,
                     '2 3'))
    # Portalrohr und X-Schiene
    t.append(f.rect(-w('profil_laenge') / 2, w('profil_laenge') / 2,
                    L['profil_y0'], L['portal_y'], 'profil'))
    t.append(f.rect(L['x_schiene_x'][0], L['x_schiene_x'][1], L['portal_y'],
                    L['x_schiene_y1'], 'fuehrung'))
    # Toolhead am Ende des X-Wegs: X-Wagen, Traegerplatte, Riemenhalter,
    # der Rest als Umriss
    xw = L['xw_min'] if s < 0 else L['xw_max']
    th = {q.name: q for q in feste_th}
    for name, art in (('X-Wagen MGN15H', 'fuehrung'),
                      ('Traegerplatte Hauptsaeule', 'toolhead'),
                      ('Traegerplatte Kopf', 'toolhead'),
                      ('Riemenhalter', 'toolhead')):
        q = th[name]
        t.append(f.rect(q.x[0] + xw, q.x[1] + xw, q.y[0], q.y[1], art))
    umriss_x = (xw + TL['ls_wand_x0'], xw + tw('winkel_x_rechts'))
    t.append(f.rect(umriss_x[0], umriss_x[1], TL['traeger_y1'],
                    TL['laser_vorn_y'], 'toolhead', fill='#f3f6fa',
                    stroke_dasharray='3 2', fill_opacity='0.6'))
    # X-Riemen: Ruecklauf und gezogener Trum, um Ritzel und Umlenkritzel
    ya, yr = L['xr_y'], L['xr_y_rueck']
    rp = w('ritzel_teilkreis') / 2
    if s < 0:
        xa, xe = L['x_motor'], xw + tw('traeger_x_links')
        t.append(f.linie(L['x_motor'], ya, xe, ya, RIEMEN, 2.2))
        t.append(f.linie(L['x_motor'], yr, f.a[1] + 5, yr, RIEMEN, 2.2))
        x0, y0 = f.px(L['x_motor'], ya)
        _, y1 = f.px(L['x_motor'], yr)
        r = rp * f.s
        t.append(el('path', {'d': 'M {} {} A {} {} 0 0 1 {} {}'.format(
            f1(x0), f1(y0), f1(r), f1(r), f1(x0), f1(y1)), 'fill': 'none',
            'stroke': RIEMEN, 'stroke-width': '2.2'}))
    else:
        xs_ = xw + tw('traeger_x_rechts')
        t.append(f.linie(xs_, ya, L['x_rolle'], ya, RIEMEN, 2.2))
        t.append(f.linie(f.a[0] - 5, yr, L['x_rolle'], yr, RIEMEN, 2.2))
        x0, y0 = f.px(L['x_rolle'], yr)
        _, y1 = f.px(L['x_rolle'], ya)
        r = rp * f.s
        t.append(el('path', {'d': 'M {} {} A {} {} 0 0 1 {} {}'.format(
            f1(x0), f1(y0), f1(r), f1(r), f1(x0), f1(y1)), 'fill': 'none',
            'stroke': RIEMEN, 'stroke-width': '2.2'}))
    if s < 0:
        # Motorhalter: Platte von oben, Motor darauf, Ritzel darunter
        t.append(f.rect(xu(L['mp_u'][0]), xu(L['mp_u'][1]), *L['mp_y'], 'neu'))
        fl = w('motor_flansch') / 2
        t.append(f.rect(L['x_motor'] - fl, L['x_motor'] + fl,
                        L['xr_yc'] - fl, L['xr_yc'] + fl, 'kauf',
                        fill_opacity='0.55'))
        t.append(f.kreis(L['x_motor'], L['xr_yc'],
                         w('ritzel_flansch_d') / 2, 'stahl', fill='none',
                         stroke_dasharray='2 2'))
        for u, y in L['halter_schrauben']:
            t.append(f.kreis(xu(u), y, 2.75, 'stahl'))
        # Anschlag (Rev. 24) auf dem Stirnblock, unter der Motorplatte
        t.append(f.rect(xu(L['mha_u'][0]), xu(L['mha_u'][1]),
                        *L['mha_y'], 'neu', fill='none',
                        stroke_dasharray='3 2'))
    else:
        # Spannbock auf dem Stirnblock, davor der Lagerschlitten (oberer
        # Arm, in der Mitte des Spannwegs) mit Kugellager und Welle; das
        # Ritzel darunter gestrichelt
        t.append(f.rect(xu(L['sb_u'][0]), xu(L['sb_u'][1]), *L['sb_y'],
                        'neu'))
        t.append(f.rect(xu(L['sb_wand_u'][0]), xu(L['sb_wand_u'][1]),
                        *L['sb_wand_y'], 'neu'))
        for u, y in L['halter_schrauben']:
            t.append(f.kreis(xu(u), y, 2.75, 'stahl'))
        ua = w('rolle_u')
        t.append(f.rect(xu(ua + L['ls_u_rel'][0]), xu(ua + L['ls_u_rel'][1]),
                        *L['ls_y'], 'neu', fill='#f3c79b'))
        t.append(f.kreis(L['x_rolle'], L['xr_yc'], w('ritzel_flansch_d') / 2,
                         'stahl', fill='none', stroke_dasharray='2 2'))
        t.append(f.kreis(L['x_rolle'], L['xr_yc'], w('kl_d') / 2, 'stahl'))
        t.append(f.kreis(L['x_rolle'], L['xr_yc'], w('uw_d') / 2, 'stahl',
                         fill='#ffffff'))
        xk = xu(L['sb_wand_u'][0])
        t.append(f.rect(xk, xk + w('m3_kopf_h'), L['zug_y'] - 2.75,
                        L['zug_y'] + 2.75, 'stahl'))
        t.append(f.linie(xk, L['zug_y'], xu(L['zug_spitze_u']),
                         L['zug_y'], '#4a4f57', 1.6, '3 2'))
    # Der vordere Klemmturm liegt unter Motorhalter bzw. Lagerschlitten:
    # Umriss
    # obendrauf
    t.append(f.rect(xu(L['kt_u'][0]), xu(L['kt_u'][1]), *L['kt_y_vorn'],
                    'neu', fill='none', stroke_dasharray='3 2'))
    return t


# ---- Schnitt durch die Y-Klemmtuerme --------------------------------------
def schnitt_tuerme(f, w, L):
    """Schnitt in der Mitte des Klemmschlitzes, rechte Seite, Blick von der
    Maschinenmitte nach aussen: vorn rechts. Zwei gleiche Klemmtuerme wie
    v8, einer je Riemenende. Geschnitten ist nur das Dach ueber dem Schlitz;
    die Wand zur Schiene mit den Rippen, Wagen, Schiene und Rahmen liegen
    dahinter und sind hell gezeichnet."""
    t = []
    lang = (f.a[0] - 5, f.a[1] + 5)
    # dahinter
    t.append(f.rect(*lang, L['rahmen_z0'], L['rahmen_z1'], 'hinten'))
    t.append(f.rect(*lang, L['y_schiene_z0'], L['y_schiene_z1'], 'hinten'))
    t.append(f.rect(L['wagen_y0'], L['wagen_y1'], L['y_wagen_z0'],
                    L['y_wagen_z1'], 'hinten'))
    t.append(f.rect(L['portal_y'], L['x_schiene_y1'],
                    -w('x_schiene_b') / 2, w('x_schiene_b') / 2, 'hinten'))
    # geschnitten: Platte, Rueckwand, Rohr
    t.append(f.rect(L['platte_y0'], L['platte_y1'], L['platte_z0'],
                    L['platte_z1'], 'neu'))
    t.append(f.rect(L['rueck_y0'], L['rueck_y1'], L['platte_z1'],
                    L['wand_z1'], 'neu'))
    t.append(f.rect(L['profil_y0'], L['portal_y'], L['profil_z0'],
                    L['profil_z1'], 'profil'))
    # Klemmtuerme: Wand zur Schiene mit Rippen dahinter, Dach geschnitten
    kz0, kz1 = L['kt_z']
    for tl in ('hinten', 'vorn'):
        k0, k1 = L['kt_y_' + tl]
        t.append(f.rect(k0, k1, kz0, L['yr_decke_z'], 'neu', fill='#f1d9c2',
                        stroke='#d9a67c'))
        for y in L['kt_rippen_y_' + tl]:
            t.append(f.rect(y, y + w('klemm_rippe_b'), kz0, L['yr_decke_z'],
                            'hinten', fill='#e8c19c', stroke='#d9a67c',
                            stroke_width='0.5'))
        t.append(f.rect(k0, k1, L['yr_decke_z'], kz1, 'neu'))
    # Y-Riemen: je ein Ende in jedem Turm, dazwischen kein Riemen
    for ya_, yb_ in ((f.a[0] - 5, L['kt_y_hinten'][1] - 1.0),
                     (L['kt_y_vorn'][0] + 1.0, f.a[1] + 5)):
        t.append(f.rect(ya_, yb_, L['yr_z0'], L['yr_z1'], 'riemen',
                        fill_opacity='0.9'))
    # Querstifte unter dem Riemen (gehen quer durch die Tuerme)
    for tl in ('hinten', 'vorn'):
        t.append(f.kreis(L['kt_stift_y_' + tl], L['stift_z'],
                         w('klemm_stift_d') / 2 - 0.1, 'stahl'))
    return t


# ---- Schnitt quer durch einen Klemmturm (seit Rev. 25) -------------------
def profil_quer(f, u0, u1, z0, z1, X, nb=6.2, tiefe=6.0):
    """Querschnitt der 2040 (hochkant) mit allen sechs Nuten, vereinfacht
    als gerade Kerben nb breit und tiefe tief (wie profil_schnitt in
    endschalter_zeichnen.py). u quer, X(u) die Zeichenkoordinate."""
    h = nb / 2.0
    um = (u0 + u1) / 2.0
    p = [(u0, z0), (um - h, z0), (um - h, z0 + tiefe), (um + h, z0 + tiefe),
         (um + h, z0), (u1, z0)]
    for zm in (z0 + 10.0, z0 + 30.0):
        p += [(u1, zm - h), (u1 - tiefe, zm - h), (u1 - tiefe, zm + h),
              (u1, zm + h)]
    p += [(u1, z1), (um + h, z1), (um + h, z1 - tiefe), (um - h, z1 - tiefe),
          (um - h, z1), (u0, z1)]
    for zm in (z0 + 30.0, z0 + 10.0):
        p += [(u0, zm + h), (u0 + tiefe, zm + h), (u0 + tiefe, zm - h),
              (u0, zm - h)]
    return f.poly([(X(u), z) for u, z in p], 'profil', stroke_width='0.9')


def schnitt_turm_quer(f, w, L):
    """Schnitt quer durch den hinteren Klemmturm am Stift, rechte Seite,
    Blick nach vorn — die Maschinenmitte liegt rechts. Geschnitten: 2040,
    Schiene, Platte, Turm mit Absatz und Fase, das Riemenende im Schlitz,
    der Stift im Sackloch und der Ruecklauf in der aeusseren Nut.
    Dahinter: Y-Wagen, Rippen und die Winkel am vorderen 2060, ueber die
    der Turm faehrt. Seit Rev. 26 steht der Rahmen so, wie er am Aufbau
    zum Turm steht: kt_luft_mehr weiter aussen als im Modell, das die
    Schiene mittig rechnet. Mit ihm ruecken Winkel und Ruecklauf."""
    R = L['R']
    X = lambda u: R - u
    t = []
    hb = w('rahmen_b') / 2.0
    e = w('kt_luft_mehr')                  # Rahmen am Aufbau weiter aussen
    z0, z1 = L['rahmen_z0'], L['rahmen_z1']
    # dahinter: Oberkante des vorderen 2060 mit dem Winkel innen
    t.append(f.rect(X(-40.0), X(50.0), L['quer_z'][1] - 10.0,
                    L['quer_z'][1], 'hinten'))
    wh = w('winkel_h')
    t.append(f.poly([(X(u - e), z) for u, z in (
        (hb, z0), (hb + wh, z0), (hb + wh, z0 + 3.0), (hb + 3.0, z0 + wh),
        (hb, z0 + wh))], 'hinten', stroke_dasharray='3 2'))
    hw = w('y_wagen_breite') / 2.0
    t.append(f.rect(X(-hw), X(hw), L['y_wagen_z0'], L['y_wagen_z1'],
                    'hinten'))
    t.append(f.rect(X(L['yr_rippe_u0']), X(L['yr_rippe_u1']),
                    L['kt_z'][0], L['yr_decke_z'], 'hinten', fill='#e8c19c',
                    stroke='#d9a67c', stroke_width='0.5'))
    # geschnitten: 2040 (am Aufbau), Schiene, Platte
    t.append(profil_quer(f, -hb - e, hb - e, z0, z1, X))
    hs = w('y_schiene_b') / 2.0
    t.append(f.rect(X(-hs), X(hs), L['y_schiene_z0'], L['y_schiene_z1'],
                    'fuehrung'))
    t.append(f.rect(X(L['platte_u'][0]), X(L['platte_u'][1]),
                    L['platte_z0'], L['platte_z1'], 'neu'))
    # Turm: Schlitz von unten, oben der Absatz neben dem Wagen mit Fase
    (u0, u1), (kz0, kz1) = L['kt_u'], L['kt_z']
    ua, za = L['kt_absatz_u'], L['kt_absatz_z']
    rg, rw = L['yr_rippe_u0'], L['yr_wand_u']
    turm = [(u0, kz0), (rg, kz0), (rg, L['yr_decke_z']),
            (rw, L['yr_decke_z']), (rw, kz0), (u1, kz0), (u1, kz1),
            (ua, kz1), (ua, za), (u0, za - (ua - u0))]
    t.append(f.poly([(X(u), z) for u, z in turm], 'neu'))
    # Riemenende im Schlitz (Zaehne zur 2040), Stift darunter, Ruecklauf
    d2 = w('riemen_dicke') / 2.0
    ym = L['y_riemen_linie']
    t.append(f.rect(X(ym - d2), X(ym + d2), L['yr_z0'], L['yr_z1'],
                    'riemen'))
    t.append(f.rect(X(L['yr_rueck_u'] - e - d2), X(L['yr_rueck_u'] - e + d2),
                    L['yr_rueck_z'][0], L['yr_rueck_z'][1], 'riemen'))
    r = w('klemm_stift_d') / 2.0 - 0.1
    t.append(f.rect(X(L['kt_stift_ende_u']), X(u1), L['stift_z'] - r,
                    L['stift_z'] + r, 'stahl'))
    return t


# ---- Schnitt durch die Umlenkung ------------------------------------------
def schnitt_umlenkung(f, w, L, tw, TL):
    """XZ-Schnitt durch die Achse des Umlenkritzels (Y = Ritzelachsen),
    Blick von vorn. Vor der Schnittebene stehen der X-Wagen (nur als
    Umriss) und der Pfosten des Lagerschlittens (weggelassen); dahinter
    der Ruecken des Schlittens, der Spannbock und die Zugschraube."""
    R = L['R']
    xu = lambda u: R - u
    t = []
    ua, xr = w('rolle_u'), L['x_rolle']
    x_ls = (xu(ua + L['ls_u_rel'][1]), xu(ua + L['ls_u_rel'][0]))
    # dahinter: Stirnblock, Platte, Spannbock, Ruecken des Schlittens
    t.append(f.rect(xu(L['stirn_u'][0]), xu(L['stirn_u'][1]),
                    L['platte_z1'], L['wand_z1'], 'hinten'))
    t.append(f.rect(xu(L['platte_u'][0]), xu(L['platte_u'][1]),
                    L['platte_z0'], L['platte_z1'], 'hinten'))
    t.append(f.rect(xu(L['sb_u'][0]), xu(L['sb_u'][1]), *L['sb_boden_z'],
                    'hinten'))
    t.append(f.rect(xu(L['sb_wand_u'][0]), xu(L['sb_wand_u'][1]),
                    *L['sb_wand_z'], 'hinten'))
    t.append(f.rect(*x_ls, L['ls_unten_z'][1], L['ls_oben_z'][0], 'hinten'))
    # Zugschraube (dahinter): Kopf aussen am Spannbock, Einsatz im Ruecken
    xk, zz = xu(L['sb_wand_u'][0]), L['zug_z']
    e = L['ls_einsatz_u_rel']
    t.append(f.rect(xu(ua + e[1]), xu(ua + e[0]), zz - w('insert_m3_d') / 2,
                    zz + w('insert_m3_d') / 2, 'stahl', fill='#e8d9a8'))
    t.append(f.rect(xu(L['zug_spitze_u']), xk, zz - 1.5, zz + 1.5, 'stahl'))
    t.append(f.rect(xk, xk + w('m3_kopf_h'), zz - 2.75, zz + 2.75, 'stahl'))
    # Rohr (geschnitten, die Ebene liegt knapp hinter seiner Vorderseite)
    t.append(f.rect(f.a[0] - 5, w('profil_laenge') / 2, L['profil_z0'],
                    L['profil_z1'], 'profil'))
    # Lagerschlitten geschnitten: unterer Arm mit dem Gleitlager, oberer
    # mit dem Kugellager und der Decke darueber
    gl, kl = w('gl_d') / 2, w('kl_d') / 2
    ws = (w('uw_d') + 1.0) / 2
    uz0, uz1 = L['ls_unten_z']
    oz0, oz1 = L['ls_oben_z']
    kz1 = L['kl_z'][1]
    for a, b, z0_, z1_ in ((x_ls[0], xr - gl, uz0, uz1),
                           (xr + gl, x_ls[1], uz0, uz1),
                           (x_ls[0], xr - kl, oz0, kz1),
                           (xr + kl, x_ls[1], oz0, kz1),
                           (x_ls[0], xr - ws, kz1, oz1),
                           (xr + ws, x_ls[1], kz1, oz1)):
        t.append(f.rect(a, b, z0_, z1_, 'neu', fill='#f3c79b'))
    t.append(f.rect(xr - gl, xr + gl, *L['gl_z'], 'kauf', fill='#d8b877'))
    t.append(f.rect(xr - kl, xr + kl, *L['kl_z'], 'stahl'))
    # Umlenkritzel wie am Motor, Nabe oben, fest auf der Welle
    rr, rf = w('ritzel_flansch_d') / 2, L['ritzel_fuss_d'] / 2
    z0, zn, bo = L['rolle_z0'], L['rolle_nabe_z0'], w('ritzel_bord')
    for a, b, r in ((z0, z0 + bo, rr), (zn - bo, zn, rr),
                    (zn, L['rolle_z1'], w('ritzel_nabe_d') / 2)):
        t.append(f.rect(xr - r, xr + r, a, b, 'kauf'))
    t.append(f.rect(xr - rf, xr + rf, z0 + bo, zn - bo, 'kauf',
                    fill='#d9ccb8'))
    t.append(f.rect(xr - w('uw_d') / 2, xr + w('uw_d') / 2, *L['uw_z'],
                    'stahl'))
    # ganz innen (entspannt) als Umriss: dort steht es dem X-Wagen am
    # rechten Ende am naechsten
    xi_r = xu(L['rolle_u'][1])
    t.append(f.rect(xi_r - rr, xi_r + rr, z0, zn, 'kauf', fill='none',
                    stroke_dasharray='2 2'))
    # Riemen um das Umlenkritzel: die Achsebene schneidet ihn nur aussen,
    # wo er vom gezogenen Trum auf den Ruecklauf umlenkt (Zaehne innen)
    t.append(f.rect(xr + w('ritzel_teilkreis') / 2 - L['riemen_innen'],
                    xr + w('ritzel_teilkreis') / 2 + L['riemen_aussen'],
                    L['xr_z0'], L['xr_z1'], 'riemen'))
    # X-Wagen am rechten Ende und Traegerplatte: vor der Ebene, Umriss
    xw = L['xw_max']
    t.append(f.rect(f.a[0] - 5, xw + tw('x_wagen_laenge') / 2,
                    -tw('x_wagen_breite') / 2, tw('x_wagen_breite') / 2,
                    'fuehrung', fill='none', stroke_dasharray='4 3'))
    t.append(f.rect(f.a[0] - 5, xw + tw('traeger_x_rechts'), TL['rh_z0'],
                    f.b[1] + 5, 'toolhead', fill='none',
                    stroke_dasharray='4 3'))
    return t


# ---- Schnitt durch den Motorhalter ---------------------------------------
def schnitt_motor(f, w, L, tw, TL):
    """XZ-Schnitt durch die Motorachse, Blick von vorn; hinten die Saeule,
    vorn (weggeschnitten) die Traegerplatte am linken Ende."""
    R = L['R']
    xu = lambda u: -(R - u)
    t = []
    xm = L['x_motor']
    fl = w('motor_flansch') / 2
    t.append(f.rect(xu(L['mh_hinten_u'][0]), xu(L['mh_hinten_u'][1]),
                    *L['mh_z'], 'hinten'))
    t.append(f.rect(xu(L['stirn_u'][0]), xu(L['stirn_u'][1]),
                    L['platte_z1'], L['wand_z1'], 'hinten'))
    t.append(f.rect(xu(L['platte_u'][0]), xu(L['platte_u'][1]),
                    L['platte_z0'], L['platte_z1'], 'hinten'))
    # Anschlag (Rev. 24) auf dem Stirnblock, hinter der Schnittebene: die
    # aeussere Saeule liegt innen an ihm an
    t.append(f.rect(xu(L['mha_u'][0]), xu(L['mha_u'][1]), *L['mha_z'],
                    'neu', fill_opacity='0.55'))
    t.append(f.rect(-w('profil_laenge') / 2, f.a[1] + 5, L['profil_z0'],
                    L['profil_z1'], 'profil'))
    # Motorplatte mit Bundbohrung, aeussere Saeule
    rb = (w('motor_bund_d') + w('spiel_locker')) / 2
    t.append(f.rect(xu(L['mp_u'][0]), xm - rb, L['mp_z0'], L['mp_z1'], 'neu'))
    t.append(f.rect(xm + rb, xu(L['mp_u'][1]), L['mp_z0'], L['mp_z1'], 'neu'))
    t.append(f.rect(xu(L['mh_aussen_u'][0]), xu(L['mh_aussen_u'][1]),
                    *L['mh_z'], 'neu'))
    # Motor mit Zentrierbund, Welle, Ritzel (Nabe oben, taucht in die
    # Bundbohrung), Riemen am Ritzel
    t.append(f.rect(xm - fl, xm + fl, L['mp_z1'], L['motor_z1'], 'kauf'))
    t.append(f.rect(xm - w('motor_bund_d') / 2, xm + w('motor_bund_d') / 2,
                    L['bund_z0'], L['mp_z1'], 'kauf'))
    t.append(f.rect(xm - 2.5, xm + 2.5, L['welle_ist_z0'], L['bund_z0'],
                    'stahl'))
    rf = w('ritzel_flansch_d') / 2
    bo, sp = w('ritzel_bord'), w('ritzel_spur')
    z0 = L['ritzel_z0']
    t.append(f.rect(xm - rf, xm + rf, z0, z0 + bo, 'stahl'))
    t.append(f.rect(xm - 6.1, xm + 6.1, z0 + bo, z0 + bo + sp, 'stahl'))
    t.append(f.rect(xm - rf, xm + rf, z0 + bo + sp, L['ritzel_nabe_z0'],
                    'stahl'))
    rn = w('ritzel_nabe_d') / 2
    t.append(f.rect(xm - rn, xm + rn, L['ritzel_nabe_z0'], L['ritzel_z1'],
                    'stahl'))
    # Welle im Ritzel (verdeckt) und Madenschraube vorn in der Nabe
    t.append(f.rect(xm - 2.5, xm + 2.5, L['welle_ist_z0'], L['ritzel_z1'],
                    'stahl', fill='none', stroke_dasharray='3 2'))
    t.append(f.kreis(xm, L['madenschraube_z'], 1.5, 'stahl',
                     fill='#555b66'))
    t.append(f.rect(xm - w('ritzel_teilkreis') / 2 - L['riemen_aussen'],
                    xm - w('ritzel_teilkreis') / 2 + L['riemen_innen'],
                    L['xr_z0'], L['xr_z1'], 'riemen'))
    for u, _ in L['motor_schrauben'][:1] + L['motor_schrauben'][2:3]:
        t.append(f.rect(xu(u) - 2.75, xu(u) + 2.75, L['mp_z0'] - 3.0,
                        L['mp_z0'], 'stahl'))
    # Traegerplatte am linken Ende (vor der Ebene) und Riemenhalter
    xw = L['xw_min']
    t.append(f.rect(xw + tw('traeger_x_links'), f.a[1] + 5, f.b[0] - 5,
                    f.b[1] + 5, 'toolhead', fill='none',
                    stroke_dasharray='4 3'))
    t.append(f.rect(xw + tw('traeger_x_links'), f.a[1] + 5, TL['rh_z0'],
                    TL['rh_z1'], 'toolhead', fill_opacity='0.35',
                    stroke_dasharray='4 3'))
    t.append(f.rect(xw - tw('x_wagen_laenge') / 2, f.a[1] + 5,
                    -tw('x_wagen_breite') / 2, tw('x_wagen_breite') / 2,
                    'fuehrung', fill='none', stroke_dasharray='4 3'))
    return t


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    feste_th, _, _ = bauraum.bauraeume(tw, TL)
    R = L['R']
    xu = lambda u, s: s * (R - u)
    t = [el('rect', {'width': '100%', 'height': '100%', 'fill': '#ffffff'}),
         text(24, 28, 'Portal — Y-Schlitten, X-Antrieb und Spanner', 14,
              TEXT, fett=True),
         text(24, 45, 'Maßstäblich aus Portal.py Rev. {} und ToolheadZ.py '
              'Rev. {}. Toolhead am Ende des X-Wegs, Z-Schlitten ganz unten. '
              'Y-Schienen {} mm Mitte zu Mitte, Rohr {} mm.'.format(
                  pm.REVISION, th.REVISION, de(w('y_schienen_abstand'), 0),
                  de(w('profil_laenge'), 0)), 9, GRAU)]

    # ---- Reihe 1: Draufsichten, Beschriftung in Randspalten --------------
    s1 = 2.55
    yb = (-112.0, 84.0)
    fl_ = Feld(230, 92, (-R - 36, -R + 76), yb, s1, b_runter=True)
    fr_ = Feld(fl_.ox + fl_.breite + 36, 92, (R - 76, R + 36), yb, s1,
               b_runter=True)
    for f, s, name in ((fl_, -1, 'linkes'), (fr_, 1, 'rechtes')):
        t += f.ausschnitt('drauf_' + name, draufsicht(f, s, w, L, tw, TL,
                                                       feste_th))
        t += f.rahmen('Draufsicht {} Portalende'.format(name))
    xw0, xw1 = L['xw_min'], L['xw_max']
    # Rueckwand: links deckt der Motorhalter sie bis auf einen Streifen zu
    u_rw = (L['mp_u'][1] + L['rueck_u'][1]) / 2
    t += fl_.spalte([
        (xu(10, -1), -70, 'Y-Wagen MGN12H, 4× M3 von oben'),
        (xu(19, -1), L['kt_stift_y_hinten'], 'Klemmturm hinten\n'
         '(unter der Platte)'),
        (xu(19, -1), -21.5, 'Klemmturm vorn\n(unter dem Motorhalter)'),
        (xu(L['y_riemen_linie'], -1), L['platte_y0'] - 5,
         'Y-Riemen (zwei Enden)'),
        (xu(L['yr_rueck_u'], -1), -80, 'Y-Rücklauf in der äußeren\n'
         'oberen Nut des 2040'),
        (xu(u_rw, -1), L['rueck_y0'] + 1.0,
         'Rückwand: 2× M5 in\nHammermuttern'),
        (-215, -26, 'Portalrohr 2020'),
        (L['x_motor'] - 12, L['xr_yc'] + 12, 'Motorhalter mit NEMA 17\n'
         '(Ritzel darunter)'),
        (xu((L['mha_u'][0] + L['mha_u'][1]) / 2, -1),
         (L['mha_y'][0] + L['mha_y'][1]) / 2,
         'Anschlag für den Motorhalter\n(unter der Motorplatte)'),
        (-227.3, L['xr_y'], 'X-Riemen, gezogener Trum'),
        (-200, L['xr_y_rueck'], 'X-Riemen, Rücklauf'),
        (xw0 - 10, -7, 'Riemenhalter am Toolhead'),
        (xw0 + 10, 50, 'Toolhead am linken\nEnde des X-Wegs (Umriss)')],
        fl_.ox - 12, 'end')
    t += fr_.spalte([
        (xu(-10, 1), -70, 'Y-Wagen MGN12H'),
        (xu(19, 1), L['kt_stift_y_hinten'], 'Klemmturm hinten'),
        (xu(19, 1), -21.5, 'Klemmturm vorn'),
        (xu(L['y_riemen_linie'], 1), L['platte_y0'] - 5, 'Y-Riemen'),
        (xu(-10, 1), L['sb_y'][0] + 4.0, 'Spannbock (2× M3 von oben)'),
        # der Stirnblock schaut vor dem Spannbock heraus
        (xu((L['stirn_u'][0] + L['stirn_u'][1]) / 2, 1),
         (L['sb_y'][1] + L['stirn_y'][1]) / 2,
         'Stirnblock: M5 in die\nKernbohrung des Rohrs'),
        (xu(L['sb_wand_u'][0], 1) + 1.5, L['zug_y'],
         'Zugschraube M3×{} (von außen)'.format(de(L['zug_schraube'], 0))),
        (L['x_rolle'] - 5.0, L['ls_pfosten_y'][0] + 1.0, 'Lagerschlitten'),
        (L['x_rolle'], L['xr_yc'], 'Welle im Kugellager,\n'
         'darunter das Umlenkritzel'),
        # Riemen und Riemenhalter stehen schon links angeschrieben
        (xw1 + 30, 50, 'Toolhead am rechten\nEnde des X-Wegs (Umriss)')],
        fr_.ox + fr_.breite + 12, 'start')
    t += fl_.luft(L['x_motor'] + w('motor_flansch') / 2, 2.0,
                  xw0 + tw('traeger_x_links'), 2.0,
                  '{} mm'.format(de(xw0 + tw('traeger_x_links')
                                    - L['x_motor']
                                    - w('motor_flansch') / 2, 1)),
                  'start', 4, 16)

    # ---- Reihe 2: Schnitt A-A (Y-Klemmtuerme) und B-B (X-Umlenkung) -----
    y2 = fl_.oy + fl_.hoehe + 78
    s2 = 3.9
    fc = Feld(60, y2, (-112.0, -8.0), (-58.0, 14.0), s2)
    t += fc.ausschnitt('schnitt_rb', schnitt_tuerme(fc, w, L))
    t += fc.rahmen('Schnitt A–A: Y-Klemmtürme wie v8')
    t.append(text(fc.ox, fc.oy + fc.hoehe + 14,
                  'rechte Seite, Mitte des Klemmschlitzes, Blick von der '
                  'Maschinenmitte; vorn rechts', 8.0, GRAU))
    t += fc.spalte([
        (-26, 3, 'Portalrohr'),
        (-41, 3, 'Rückwand'),
        (-70, L['platte_z0'] + 3, 'Platte des Schlittens'),
        (L['kt_stift_y_hinten'], L['kt_z'][1] - 5, 'Klemmturm hinten'),
        (L['kt_stift_y_vorn'], L['yr_decke_z'] + 5, 'Klemmturm vorn'),
        (L['kt_rippen_y_vorn'][-2] + 0.5, L['yr_z0'] + 3,
         'Rippen an der Wand zur Schiene\n(dahinter), greifen in die Zähne'),
        (L['kt_stift_y_vorn'], L['stift_z'], 'Querstift Ø3×{} unter dem '
         'Riemen\n(in jedem Turm)'.format(de(L['kt_stift_l'], 0))),
        (-13, (L['y_schiene_z0'] + L['y_schiene_z1']) / 2,
         'Y-Schiene und Rahmen\n(dahinter)'),
        (L['wagen_y0'] + 20, L['y_wagen_z0'] + 3, 'Y-Wagen (dahinter)')],
        fc.ox + fc.breite + 12, 'start', abstand=24.0,
        unten=fc.oy + fc.hoehe + 16)
    ah = L['kt_y_hinten'][0] - 6.0
    xa, ya = fc.px(ah, L['yr_z1'])
    _, yo = fc.px(ah, L['platte_z1'] + 3.0)
    t += fc.zeiger(ah, L['yr_z1'] - 1.0, 0.0, yo - ya, 'Y-Riemen hinten, '
                   'zum Ritzel')

    s3 = 4.2
    fd = Feld(fc.ox + fc.breite + 250, y2, (R - 46.0, R + 26.0),
              (2.0, 50.0), s3)
    t += fd.ausschnitt('schnitt_uh', schnitt_umlenkung(fd, w, L, tw, TL))
    t += fd.rahmen('Schnitt B–B: X-Umlenkung')
    t.append(text(fd.ox, fd.oy + fd.hoehe + 14,
                  'durch die Achse, Blick von vorn; X-Wagen und', 8.0, GRAU))
    t.append(text(fd.ox, fd.oy + fd.hoehe + 25,
                  'Trägerplatte am rechten Ende als Umriss (liegen davor)',
                  8.0, GRAU))
    kz = L['kl_z']
    t += fd.spalte([
        (L['x_rolle'], L['uw_z'][1] - 1.0, 'Welle Ø{} × {}'.format(
            de(w('uw_d'), 0), de(w('uw_laenge'), 0))),
        (L['x_rolle'] + w('kl_d') / 2 - 1.0, (kz[0] + kz[1]) / 2,
         'Kugellager {} × {}'.format(de(w('kl_d'), 0), de(w('kl_b'), 0))),
        (L['x_rolle'] - 6.0, L['ls_oben_z'][1] - 1.5,
         'Lagerschlitten (Pfosten davor\nweggelassen)'),
        (R - L['sb_wand_u'][0] + 1.5, L['zug_z'] + 1.0,
         'Zugschraube M3×{} im Einsatz\n(dahinter)'.format(
             de(L['zug_schraube'], 0))),
        (R - L['sb_wand_u'][1] + 1.0, L['sb_wand_z'][1] - 1.5,
         'Spannbock (dahinter)'),
        (L['x_rolle'] + w('ritzel_nabe_d') / 2 - 1.0,
         (L['rolle_nabe_z0'] + L['rolle_z1']) / 2,
         'Nabe oben, Madenschrauben'),
        (L['x_rolle'] + 4.2, L['xr_zm'] + 1.5, 'Ritzel 20 Z wie am Motor'),
        (L['x_rolle'] + w('ritzel_teilkreis') / 2, L['xr_zm'] - 1.5,
         'X-Riemen (außen um das Ritzel)'),
        (L['x_rolle'] + w('gl_d') / 2 - 1.0,
         (L['gl_z'][0] + L['gl_z'][1]) / 2,
         'Gleitlager Ø{} × {}'.format(de(w('gl_d'), 0), de(w('gl_l'), 0))),
        (w('profil_laenge') / 2 - 5, (L['profil_z1'] + fd.b[0]) / 2,
         'Portalrohr'),
        (w('profil_laenge') / 2 + 10, (L['profil_z1'] + fd.b[0]) / 2,
         'Stirnblock (dahinter)')],
        fd.ox + fd.breite + 12, 'start', abstand=21.0,
        unten=fd.oy + fd.hoehe + 16)
    # Der untere Bord steht nur 2,75 mm ueber dem X-Wagen; ganz innen
    # (Umriss) bleibt er am rechten Ende 3 mm daneben
    xw_ende = L['xw_max'] + tw('x_wagen_laenge') / 2
    x_bord = R - (L['rolle_u'][1] + w('ritzel_flansch_d') / 2)
    zb = L['rolle_z0'] + w('ritzel_bord') / 2
    t += fd.luft(x_bord, zb, xw_ende, zb, '{} mm'.format(
        de(x_bord - xw_ende, 1)), 'end', -5, 4)
    # Pfeil ueber dem Lagerschlitten: die Zugschraube zieht ihn nach aussen
    x0, y0 = fd.px(L['x_rolle'] + w('uw_d') / 2 + 2.0,
                   L['ls_oben_z'][1] + 1.8)
    t += [linie(x0, y0, x0 + 22, y0, ORANGE, 1.4),
          pfeil(x0 + 25, y0, 1, 0, ORANGE),
          text(x0 + 30, y0 + 3, 'spannen', 8.0, ORANGE, fett=True,
               halo=True)]

    # ---- Reihe 3: Schnitt C-C (Motorhalter), Zahlen ----------------------
    y3 = max(fc.oy + fc.hoehe, fd.oy + fd.hoehe) + 80
    s4 = 3.3
    fe = Feld(60, y3, (-R - 26.0, -R + 36.0), (-14.0, 96.0), s4)
    t += fe.ausschnitt('schnitt_mh', schnitt_motor(fe, w, L, tw, TL))
    t += fe.rahmen('Schnitt C–C: Motorhalter')
    t.append(text(fe.ox, fe.oy + fe.hoehe + 14, 'durch die Motorachse, '
                  'Blick von vorn', 8.0, GRAU))
    t += fe.mass(L['x_motor'] + 9.8, L['welle_ist_z0'], L['mp_z1'],
                 'Welle {} mm'.format(de(w('motor_welle_ist'), 0)), 4,
                 L['welle_ist_z0'] + 3.0)
    t += fe.spalte([
        (L['x_motor'] - 8, 72, 'NEMA 17'),
        (L['x_motor'] + 16, L['mp_z1'] - 2, 'Motorplatte {} mm'.format(
            de(w('mp_dicke'), 1))),
        (L['x_motor'] + 4, L['ritzel_z1'] - 0.8,
         'Ritzel 20 Z, Nabe oben in der\nBundbohrung: ganz auf der Welle'),
        (L['x_motor'] + 1.5, L['madenschraube_z'],
         'Madenschraube, Inbus von vorn'),
        (L['x_motor'] - w('ritzel_teilkreis') / 2, L['xr_zm'],
         'X-Riemen, mittig in der Spur'),
        (xu(-17, -1), 20, 'äußere Säule'),
        (xu((L['mha_u'][0] + L['mha_u'][1]) / 2, -1),
         (L['mha_z'][0] + L['mha_z'][1]) / 2,
         'Anschlag (dahinter, {} mm Luft):\nhält den Halter gegen den '
         'Riemenzug'.format(de(w('mha_spiel'), 1))),
        (xu(26, -1), 14, 'hintere Säule (dahinter)'),
        (-R + 25, 3, 'Portalrohr'),
        (xu(-10, -1), -3, 'Stirnblock (dahinter)'),
        (L['xw_min'] + tw('traeger_x_links') + 2, 85,
         'Trägerplatte am linken Ende\n(Umriss, liegt davor)')],
        fe.ox + fe.breite + 12, 'start', abstand=22.0,
        unten=fe.oy + fe.hoehe + 16)
    t += fe.luft(L['x_motor'] + w('motor_flansch') / 2, 58,
                 L['xw_min'] + tw('traeger_x_links'), 58,
                 '{} mm'.format(de(L['xw_min'] + tw('traeger_x_links')
                                   - L['x_motor']
                                   - w('motor_flansch') / 2, 1)),
                 'start', 4, -8)

    riemen_x = 2.0 * (L['x_rolle'] - L['x_motor']) + math.pi * w(
        'ritzel_teilkreis')
    # engste Luft am Ende des X-Wegs (portal_check.py misst dasselbe)
    luft_motor = (L['xw_min'] + tw('traeger_x_links') - L['x_motor']
                  - w('motor_flansch') / 2)
    luft_rolle = (R - (L['rolle_u'][1] + w('ritzel_flansch_d') / 2)
                  - (L['xw_max'] + tw('x_wagen_laenge') / 2))
    # Fahnenlasche links neben dem Y-Riemen (rechts gleich weit, siehe
    # x_schiene_versatz)
    luft_yr = (L['xw_min'] + TL['ls_lasche_x0']
               - (-R + L['y_riemen_linie'] + w('riemen_dicke') / 2))
    tx, ty = fe.ox + fe.breite + 260, y3 + 6
    zeilen = [
        ('X-Weg', '{} mm (Schiene {} − Wagen {})'.format(
            de(L['x_weg'], 1), de(w('x_schiene_laenge'), 0),
            de(w('x_wagen_laenge'), 1))),
        ('X-Schiene', '{} mm nach links versetzt'.format(
            de(w('x_schiene_versatz'), 2))),
        ('Y-Wagen', 'Mitte {} mm hinter der Rohrmitte:'.format(
            de(L['profil_y0'] + w('profil_b') / 2 - w('wagen_y'), 0))),
        ('', 'alle 4 Wagenschrauben bleiben von oben frei'),
        ('Rohr', 'liegt auf der 6-mm-Platte, Höhe wie bisher'),
        ('Y-Riemen', 'Mitte {} mm innen, am Aufbau {} mm vor der 2040,'
         .format(de(L['y_riemen_linie'], 2),
                 de(L['y_riemen_linie'] - L['profil_aufbau_u'], 1))),
        ('', 'Unterkante {} mm; {} mm neben dem Toolhead'.format(
            de(L['yr_z0'], 1), de(luft_yr, 1))),
        ('', 'Rücklauf in der äußeren oberen Nut, Zähne zur Schiene'),
        ('Y-Klemmen', 'zwei Türme wie v8, je {} mm vor und hinter'.format(
            de(w('turm_abstand'), 1))),
        ('', 'der Wagenmitte, am Aufbau {} mm neben der 2040 (Rev. 26)'
         .format(de(L['kt_u'][0] - L['profil_aufbau_u'], 1))),
        ('X-Riemen', 'Unterkante {} mm, Schleife ≈ {} mm'.format(
            de(L['xr_z0'], 2), de(riemen_x, 0))),
        ('X-Spanner', 'Lagerschlitten ±{} mm, M3×{} von außen'.format(
            de(w('rolle_weg'), 0), de(L['zug_schraube'], 0))),
        ('X-Motor', 'Ritzel ganz auf der Welle schon ab {} mm (gemessen {}):'
         .format(de(w('motor_welle_l'), 0), de(w('motor_welle_ist'), 0))),
        ('', 'Platte {} mm, Nabe {} mm in der Bundbohrung'.format(
            de(w('mp_dicke'), 1), de(L['ritzel_z1'] - L['mp_z0'], 0))),
        ('engste Luft', '{} mm: Motor ↔ Trägerplatte, Umlenkritzel ↔ X-Wagen,'
         .format(de(min(luft_motor, luft_rolle), 1))),
        ('', 'Platte ↔ X-Wagen am Ende des X-Wegs'),
        ('', '{} mm: X-Wagen ↔ vorderer Klemmturm, am linken Ende'
         .format(de(L['portal_y'] - L['kt_y_vorn'][1], 1))),
        ('Prüfung', 'tools/portal_check.py (X- und Z-Weg)'),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(tx + 86, ty + 10 + i * 15, v, 8.5, TEXT))

    # ---- Reihe 4: Schnitt D-D (Klemmturm quer, seit Rev. 25, Rev. 26) -----
    y4 = max(fe.oy + fe.hoehe + 40, ty + 10 + len(zeilen) * 15) + 70
    s5 = 6.0
    fg = Feld(250, y4, (R - 38.0, R + 16.0), (-75.0, -6.0), s5, a_rueck=True)
    t += fg.ausschnitt('schnitt_kq', schnitt_turm_quer(fg, w, L))
    t += fg.rahmen('Schnitt D–D: Klemmturm quer, seit Rev. 26 am Aufbau '
                   '{} mm neben der 2040'.format(
                       de(L['kt_u'][0] - L['profil_aufbau_u'], 0)))
    t.append(text(fg.ox, fg.oy + fg.hoehe + 14, 'rechte Seite, durch den '
                  'Stift des hinteren Turms, Blick nach vorn; die 2040 so, '
                  'wie sie am Aufbau zum Turm steht', 8.0, GRAU))
    t.append(text(fg.ox, fg.oy + fg.hoehe + 25, 'mit Rev. 25 gemessen 3,0 '
                  'statt der gerechneten 2,0 mm; im Modell (Schiene mittig) '
                  'liegt der Turm an der 2040 an', 8.0, GRAU))
    X = lambda u: R - u
    hb = w('rahmen_b') / 2.0
    fl = L['profil_aufbau_u']               # Seitenflaeche am Aufbau
    e = w('kt_luft_mehr')
    (u0, u1), kz0 = L['kt_u'], L['kt_z'][0]
    t += fg.spalte([
        (X(-hb - e + 3.0), L['rahmen_z0'] + 4.0, '2040 hochkant'),
        (X(L['yr_rueck_u'] - e), L['yr_rueck_z'][1] - 1.0,
         'Rücklauf in der\näußeren oberen Nut'),
        (X(-4.0), (L['y_schiene_z0'] + L['y_schiene_z1']) / 2,
         'Y-Schiene MGN12'),
        (X(-9.0), (L['y_wagen_z0'] + L['y_wagen_z1']) / 2,
         'Y-Wagen (dahinter)'),
        (X(-16.0), L['platte_z0'] + 3.0, 'Platte des Schlittens'),
        (X(-13.0), L['quer_z'][1] - 3.0,
         'vorderes 2060 (dahinter)')],
        fg.ox - 12, 'end', abstand=24.0)
    t += fg.spalte([
        ((X(L['kt_absatz_u']) + X(u0)) / 2, L['kt_absatz_z'] - 1.0,
         'Absatz {} mm neben dem Wagen,\ndarunter Fase 45° (stützfrei)'
         .format(de(L['kt_absatz_u'] - w('y_wagen_breite') / 2, 1))),
        (X((u0 + u1) / 2 + 3.0), -22.0, 'Klemmturm, Schrauben wie bisher'),
        (X(L['y_riemen_linie']), L['yr_z1'] - 1.0,
         'Riemenende im Schlitz, Zähne zur 2040;\nMitte {} mm vor der '
         'Seitenfläche'.format(de(L['y_riemen_linie'] - fl, 1))),
        (X(L['yr_rippe_u0'] + 0.4), L['kt_z'][0] + 2.0,
         'Rippen (dahinter)'),
        (X(u1 - 3.0), L['stift_z'],
         'Querstift Ø3×{} im Sackloch, innen\nbündig; {} mm Wand zur 2040'
         .format(de(L['kt_stift_l'], 0),
                 de(L['kt_stift_ende_u'] - u0, 1))),
        (X(hb - e + 10.0), L['rahmen_z0'] + 8.0,
         'Winkel {} mm: der Turm fährt\n{} mm darüber'.format(
             de(w('winkel_h'), 0),
             de(kz0 - (L['rahmen_z0'] + w('winkel_h')), 1)))],
        fg.ox + fg.breite + 12, 'start', abstand=24.0)
    # Luft zur 2040 (ueber der oberen Nut) und ueber dem Winkel
    zl = (L['rahmen_z1'] + L['nut_oberkante_z']) / 2.0
    t += fg.luft(X(fl), zl, X(u0), zl, '{} mm'.format(
        de(u0 - fl, 1)), 'start', 6, 4)
    uw = u0 + 0.6
    t += fg.luft(X(uw), L['rahmen_z0'] + w('winkel_h'), X(uw), kz0,
                 '{} mm'.format(de(kz0 - (L['rahmen_z0'] + w('winkel_h')),
                                   1)), 'start', 8, 16)

    # ---- Legende -----------------------------------------------------------
    ly = max(fg.oy + fg.hoehe + 50, ty + 10 + len(zeilen) * 15 + 24)
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('toolhead', 'Toolhead (vorhanden)'),
                                  ('fuehrung', 'Linearführung'),
                                  ('profil', 'Aluprofil'),
                                  ('kauf', 'Motor, Ritzel'),
                                  ('stahl', 'Stahl'),
                                  ('hinten', 'hinter der Schnittebene'))):
        x = 24 + (i % 4) * 190
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    x, y = 24 + 3 * 190, ly + 18
    t.append(linie(x, y + 4.5, x + 16, y + 4.5, RIEMEN, 2.2))
    t.append(text(x + 21, y + 8, 'GT2-Riemen', 8.5))
    t.append(text(24, ly + 50, 'Gestrichelt: liegt darunter bzw. vor der '
                  'Schnittebene. Rot: engste Luft. Spanner in der Mitte '
                  'ihres Wegs.', 8.5, GRAU))
    W = int(max(fr_.ox + fr_.breite + 190, fd.ox + fd.breite + 170,
                tx + 330, fg.ox + fg.breite + 200))
    H = int(ly + 70)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
