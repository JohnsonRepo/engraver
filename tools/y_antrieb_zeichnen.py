#!/usr/bin/env python3
"""Skizze des Y-Motorhalters am Ende einer 2040.

Draufsicht und Seitenansicht mit gemeinsamer Y-Achse, daneben der Schnitt
A-A durch die Schenkel (Nutensteine unten, Riemen oben) und ein Detail des
Riemens in der oberen Nut. Alle Masse kommen aus YMotorhalter.py; die Skizze
wandert also mit den Parametern.

    python3 tools/y_antrieb_zeichnen.py   ->  docs/y-antrieb.svg
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import y_motorhalter_check as pruef                   # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'y-antrieb.svg')

S = 3.6                     # px/mm, Draufsicht, Seitenansicht, Schnitt
S_DETAIL = 14.0             # px/mm, Riemen in der Nut
Y_BEREICH = (-52.0, 66.0)   # Draufsicht und Seitenansicht
X_BEREICH = (-32.0, 32.0)   # Draufsicht (hoch) und Schnitt (quer)
Z_BEREICH = (-44.0, 42.0)   # Seitenansicht und Schnitt
DETAIL_X = (2.5, 12.5)
DETAIL_Z = (19.0, 37.0)
SCHNITT_Y = -10.0           # Schnitt A-A: durch das vordere M5-Paar

# Nur Zeichnung, vereinfacht [w]: Nut 6 hinter den Lippen (halbe Hoehe des
# Kanals, Tiefe, ab der er sich verjuengt, halbe Hoehe am Nutgrund),
# Kernbohrung, Ritzelnabe, Nutenstein.
NUT_KANAL = 5.5
NUT_SCHRAEG_AB = 3.8
NUT_GRUND = 3.0
KERNBOHRUNG = 4.2
NABE_D = 12.0
NUTENSTEIN_H = 4.0

FARBE = {
    'druck':   ('#c9d9ec', '#2f5d92'),
    'kauf':    ('#e8ded0', '#8a6d3b'),
    'stahl':   ('#c3c8cf', '#4a4f57'),
    'profil':  ('#dfe3e8', '#6b7480'),
    'nut':     ('#c5ccd4', '#6b7480'),
    'frei':    ('#ffffff', '#6b7480'),
    'hinten':  ('#eef2f7', '#a9b6c8'),
    'riemen':  ('#1c2733', '#1c2733'),
}
TEXT = '#1c2733'
GRAU = '#5b6472'
BLAU = '#2f5d92'
ROT = '#b4342f'
RIEMEN = '#1c2733'
KANTE = '#7f9cc2'


# ---- SVG-Bausteine -----------------------------------------------------------

def de(x, stellen=1, vorzeichen=False):
    """Zahl mit Dezimalkomma und echtem Minus; Nullen am Ende fallen weg."""
    s = (('{:+.%df}' if vorzeichen else '{:.%df}') % stellen).format(x)
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s.replace('.', ',').replace('-', '−')


def f1(x):
    return '{:.1f}'.format(x)


def el(tag, attrs, inhalt=None):
    """SVG-Element; Attribute als dict, damit keines doppelt vorkommt."""
    a = ' '.join('{}="{}"'.format(k, v) for k, v in attrs.items()
                 if v is not None)
    if inhalt is None:
        return '<{} {}/>'.format(tag, a)
    return '<{} {}>{}</{}>'.format(tag, a, inhalt, tag)


def stil(art, mehr):
    fill, stroke = FARBE[art]
    a = {'fill': fill, 'stroke': stroke, 'stroke-width': '0.8'}
    a.update({k.replace('_', '-'): v for k, v in mehr.items()})
    return a


def rect_px(xa, ya, xb, yb, art, **mehr):
    a = {'x': f1(min(xa, xb)), 'y': f1(min(ya, yb)),
         'width': f1(abs(xb - xa)), 'height': f1(abs(yb - ya))}
    a.update(stil(art, mehr))
    return el('rect', a)


def poly_px(punkte, art, **mehr):
    a = {'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte)}
    a.update(stil(art, mehr))
    return el('polygon', a)


def linie(x1, y1, x2, y2, farbe=GRAU, breite=0.7, strich=None):
    return el('line', {'x1': f1(x1), 'y1': f1(y1), 'x2': f1(x2),
                       'y2': f1(y2), 'stroke': farbe, 'stroke-width': breite,
                       'stroke-dasharray': strich})


def pfad(punkte, farbe, breite, strich=None, zu=False):
    d = 'M ' + ' L '.join('{} {}'.format(f1(x), f1(y)) for x, y in punkte)
    return el('path', {'d': d + (' Z' if zu else ''), 'fill': 'none',
                       'stroke': farbe, 'stroke-width': breite,
                       'stroke-dasharray': strich,
                       'stroke-linejoin': 'round'})


def text(x, y, s, gr=8.5, farbe=TEXT, anker='start', fett=False, halo=False):
    a = {'x': f1(x), 'y': f1(y), 'font-size': gr, 'fill': farbe,
         'text-anchor': anker, 'font-weight': '600' if fett else None}
    if halo:
        a.update({'stroke': '#ffffff', 'stroke-width': '3',
                  'stroke-linejoin': 'round', 'paint-order': 'stroke'})
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return el('text', a, s)


def pfeil(x, y, dx, dy, farbe, lang=5.0, halb=2.0):
    """Pfeilspitze mit der Spitze bei (x, y), zeigt in Richtung (dx, dy)."""
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    bx, by = x - dx * lang, y - dy * lang
    return el('polygon', {'points': '{},{} {},{} {},{}'.format(
        f1(x), f1(y), f1(bx - dy * halb), f1(by + dx * halb),
        f1(bx + dy * halb), f1(by - dx * halb)), 'fill': farbe})


def doppelpfeil(xa, ya, xb, yb, farbe):
    return [linie(xa, ya, xb, yb, farbe, 0.8),
            pfeil(xa, ya, xa - xb, ya - yb, farbe, 4.5, 1.8),
            pfeil(xb, yb, xb - xa, yb - ya, farbe, 4.5, 1.8)]


def stadion(u, vc, hub, breite, n=12):
    """Langloch laengs v (Mitte vc, +-hub, Breite breite) als Punktzug."""
    r = breite / 2.0
    p = [(u + r * math.cos(math.radians(180.0 * i / n)),
          vc + hub + r * math.sin(math.radians(180.0 * i / n)))
         for i in range(n + 1)]
    p += [(u + r * math.cos(math.radians(180.0 + 180.0 * i / n)),
           vc - hub + r * math.sin(math.radians(180.0 + 180.0 * i / n)))
          for i in range(n + 1)]
    return p


class Ansicht:
    """Massstaeblicher Ausschnitt: u nach rechts, v nach oben (mm)."""

    def __init__(self, ox, oy, s, ub, vb):
        self.ox, self.oy, self.s, self.ub, self.vb = ox, oy, s, ub, vb
        self.breite = (ub[1] - ub[0]) * s
        self.hoehe = (vb[1] - vb[0]) * s

    def px(self, u, v):
        return (self.ox + (u - self.ub[0]) * self.s,
                self.oy + (self.vb[1] - v) * self.s)

    def rect(self, u0, u1, v0, v1, art, **mehr):
        (xa, ya), (xb, yb) = self.px(u0, v0), self.px(u1, v1)
        return rect_px(xa, ya, xb, yb, art, **mehr)

    def kreis(self, u, v, d, art, **mehr):
        cx, cy = self.px(u, v)
        a = {'cx': f1(cx), 'cy': f1(cy), 'r': f1(d / 2.0 * self.s)}
        a.update(stil(art, mehr))
        return el('circle', a)

    def poly(self, punkte, art, **mehr):
        return poly_px([self.px(u, v) for u, v in punkte], art, **mehr)

    def linie(self, u0, v0, u1, v1, farbe=GRAU, breite=0.7, strich=None):
        (xa, ya), (xb, yb) = self.px(u0, v0), self.px(u1, v1)
        return linie(xa, ya, xb, yb, farbe, breite, strich)

    def pfad(self, punkte, farbe, breite, strich=None):
        return pfad([self.px(u, v) for u, v in punkte], farbe, breite, strich)

    def ausschnitt(self, name, inhalt):
        rahmen = el('rect', {'x': f1(self.ox), 'y': f1(self.oy),
                             'width': f1(self.breite),
                             'height': f1(self.hoehe)})
        return ([el('clipPath', {'id': name}, rahmen),
                 '<g clip-path="url(#{})">'.format(name)] + inhalt + ['</g>'])

    def rahmen(self):
        return rect_px(self.ox, self.oy, self.ox + self.breite,
                       self.oy + self.hoehe, 'frei', fill='none',
                       stroke='#d5dae1')

    def z_skala(self, schritt=10):
        t = []
        v = math.ceil(self.vb[0] / schritt) * schritt
        while v <= self.vb[1]:
            _, yy = self.px(self.ub[0], v)
            t.append(linie(self.ox - 6, yy, self.ox, yy, GRAU, 0.6))
            t.append(text(self.ox - 9, yy + 3, de(v, 0, True), 7.5, GRAU,
                          'end'))
            v += schritt
        return t


def beschriften(a, eintraege, x_r, abstand=11.0):
    """Beschriftung mit Fuehrungslinien rechts neben einer Ansicht;
    eintraege = [(u, v, text)], von oben nach unten ohne Ueberlappung."""
    t, belegt = [], -1e9
    for u, v, s in sorted(eintraege, key=lambda e: -e[1]):
        px, py = a.px(u, v)
        ty = max(py + 3, belegt + abstand)
        belegt = ty
        t += [linie(px, py, x_r - 3, ty - 3, GRAU, 0.6),
              el('circle', {'cx': f1(px), 'cy': f1(py), 'r': '1.4',
                            'fill': GRAU}),
              text(x_r, ty, s, 7.5)]
    return t


def ueberschrift(a, zeile1, zeile2):
    return [text(a.ox, a.oy - 20, zeile1, 10, BLAU, fett=True),
            text(a.ox, a.oy - 7, zeile2, 8, GRAU)]


# ---- Geometrie fuer mehrere Ansichten -----------------------------------------

def nut_seite(w, seite, zc, halb):
    """Nut in einer Seitenflaeche, (X, Z): Oeffnung durch die Lippe,
    dahinter der Kanal, zum Nutgrund verjuengt. Flaeche bei X = seite*halb."""
    o, lip, tief = w('nut_breite') / 2.0, w('nut_lippe'), w('nut_tiefe')
    lokal = [(0.0, -o), (lip, -o), (lip, -NUT_KANAL),
             (NUT_SCHRAEG_AB, -NUT_KANAL), (tief, -NUT_GRUND),
             (tief, NUT_GRUND), (NUT_SCHRAEG_AB, NUT_KANAL),
             (lip, NUT_KANAL), (lip, o), (0.0, o)]
    return [(seite * (halb - t), zc + dz) for t, dz in lokal]


def nut_quer(w, flaeche_z, richtung):
    """Nut in der oberen oder unteren 20-mm-Flaeche, Mitte X = 0; richtung
    = -1 fuer die Oberseite (die Nut geht nach unten), +1 fuer die
    Unterseite."""
    o, lip, tief = w('nut_breite') / 2.0, w('nut_lippe'), w('nut_tiefe')
    lokal = [(-o, 0.0), (-o, lip), (-NUT_KANAL, lip),
             (-NUT_KANAL, NUT_SCHRAEG_AB), (-NUT_GRUND, tief),
             (NUT_GRUND, tief), (NUT_KANAL, NUT_SCHRAEG_AB),
             (NUT_KANAL, lip), (o, lip), (o, 0.0)]
    return [(dx, flaeche_z + richtung * t) for dx, t in lokal]


def nutenstein(w, seite, zc, halb):
    """Hammermutter im Kanal hinter der Lippe (X, Z), vereinfacht."""
    lip = w('nut_lippe')
    a, b = halb - lip, halb - lip - NUTENSTEIN_H
    k = NUT_KANAL - 0.5
    g = NUT_GRUND + 0.2
    lokal = [(a, -k), (halb - NUT_SCHRAEG_AB, -k), (b, -g), (b, g),
             (halb - NUT_SCHRAEG_AB, k), (a, k)]
    return [(seite * x, zc + dz) for x, dz in lokal]


def ritzel_umriss(w, L, y):
    """Ritzel von der Seite (Y, Z): Nabe unten, zwei Flansche, Spur."""
    fr = w('ritzel_flansch_d') / 2.0
    nr = NABE_D / 2.0
    sr = L['rp']
    z0 = L['ritzel_z0']
    z_n = z0 + L['ritzel_nabe']
    z_f = z_n + w('ritzel_flansch_h')
    z_s = z_f + w('ritzel_spur')
    z1 = L['ritzel_z1']
    rechts = [(y + nr, z0), (y + nr, z_n), (y + fr, z_n), (y + fr, z_f),
              (y + sr, z_f), (y + sr, z_s), (y + fr, z_s), (y + fr, z1)]
    links = [(2.0 * y - u, v) for u, v in reversed(rechts)]
    return rechts + links


# ---- Ansichten ------------------------------------------------------------------

def draufsicht(w, L, ox, oy, x_r):
    """Von oben: Y nach rechts, X nach oben. Gezeichnet von unten nach oben
    (Hoehe Z), damit Hoeheres das Tiefere verdeckt."""
    a = Ansicht(ox, oy, S, Y_BEREICH, X_BEREICH)
    ym = L['motor_y_mitte']
    hb = L['halbe_breite']
    halb = w('profil_breite') / 2.0
    h = w('motor_loch') / 2.0
    m = w('motor_flansch') / 2.0
    hub = w('spann_weg') / 2.0
    r_mitte = (L['trum_ruecken_x'] + L['trum_zahn_x']) / 2.0
    t = ueberschrift(a, 'Draufsicht', 'Motor in der Mitte des Spannwegs; '
                     'verdeckt gestrichelt')
    inhalt = [a.rect(Y_BEREICH[0], 0.0, -halb, halb, 'profil')]
    for sx in (-1, 1):
        inhalt.append(a.pfad([(Y_BEREICH[0], sx * r_mitte),
                              (0.0, sx * r_mitte)], RIEMEN, 1.0, '4 2'))
    # Halter: Schenkel und Platte, oben buendig; Joch und Waende darunter
    for sx in (-1, 1):
        inhalt.append(a.rect(L['wange_y0'], 0.0, sx * L['wange_x0'],
                             sx * L['wange_x1'], 'druck'))
    inhalt.append(a.rect(0.0, L['platte_y1'], -hb, hb, 'druck'))
    inhalt.append(a.linie(L['joch_y1'], -hb, L['joch_y1'], hb, KANTE, 0.6,
                          '2 2'))
    for sx in (-1, 1):
        inhalt.append(a.linie(0.0, sx * L['fuehrung_x0'], L['platte_y1'],
                              sx * L['fuehrung_x0'], KANTE, 0.6, '2 2'))
    inhalt.append(a.rect(ym - m, ym + m, -m, m, 'kauf', fill='none',
                         stroke_dasharray='4 2'))
    # Langloecher: im Bundschlitz sieht man den Motor, in den kleinen die M3
    inhalt.append(a.poly([(v, u) for u, v in
                          stadion(0.0, ym, hub, L['bund_schlitz_b'])],
                         'frei'))
    inhalt.append(a.kreis(ym, 0.0, w('motor_bund_d'), 'kauf'))
    for x, y in L['motor_langloecher']:
        inhalt.append(a.poly([(v, u) for u, v in
                              stadion(x, y, hub, w('m3_durchgang'))],
                             'frei'))
        inhalt.append(a.kreis(y, x, w('m3_scheibe_d'), 'stahl'))
        inhalt.append(a.kreis(y, x, w('m3_kopf_d'), 'stahl'))
    # Riemen frei von der Stirnseite ums Ritzel; der obere Flansch deckt ihn
    bogen = [(ym + r_mitte * math.sin(math.radians(g)),
              r_mitte * math.cos(math.radians(g))) for g in range(0, 181, 6)]
    inhalt.append(a.pfad([(0.0, r_mitte)] + bogen + [(0.0, -r_mitte)],
                         RIEMEN, w('riemen_dicke') * S))
    inhalt.append(a.kreis(ym, 0.0, w('ritzel_flansch_d'), 'kauf'))
    inhalt.append(a.kreis(ym, 0.0, 5.0, 'stahl'))
    # M5-Koepfe an den Schenkeln (von oben: liegende Zylinder)
    for y, _ in L['m5_loecher']:
        for sx in (-1, 1):
            x0 = L['wange_x1']
            x1 = x0 + w('m5_scheibe_h')
            x2 = x1 + w('m5_kopf_h')
            inhalt.append(a.rect(y - w('m5_scheibe_d') / 2,
                                 y + w('m5_scheibe_d') / 2, sx * x0, sx * x1,
                                 'stahl'))
            inhalt.append(a.rect(y - w('m5_kopf_d') / 2,
                                 y + w('m5_kopf_d') / 2, sx * x1, sx * x2,
                                 'stahl'))
    inhalt.append(a.linie(Y_BEREICH[0], 0.0, Y_BEREICH[1], 0.0, ROT, 0.5,
                          '8 3 2 3'))
    inhalt.append(a.linie(SCHNITT_Y, X_BEREICH[0] + 2, SCHNITT_Y,
                          X_BEREICH[1] - 2, ROT, 0.8, '8 3 2 3'))
    t += a.ausschnitt('drauf', inhalt)
    t.append(a.rahmen())
    for v, dy in ((X_BEREICH[1] - 2, 9), (X_BEREICH[0] + 2, -3)):
        px, py = a.px(SCHNITT_Y, v)
        t.append(text(px + 3, py + dy, 'A', 9, ROT, fett=True))
    # Spannweg des Motors
    xa, ya = a.px(L['motor_y_min'], -(m + 5.5))
    xb, yb = a.px(L['motor_y_max'], -(m + 5.5))
    t += doppelpfeil(xa, ya, xb, yb, BLAU)
    t.append(text(xb + 5, yb + 3, 'Motor ±{} mm'.format(de(hub, 0)), 7.5,
                  BLAU))
    eintraege = [
        (-28.0, L['wange_x1'] - 1, 'Schenkel an beiden Seiten, je 2 × M5'),
        (L['joch_y1'] / 2, hb - 1.5, 'Joch, liegt an der Stirnseite an'),
        (L['platte_y1'] - 3, hb - 1.5,
         'Platte {} mm, Führungswände darunter'.format(
             de(w('platte_dicke')))),
        (ym + h, h + 1.2, 'M3 im Langloch'),
        (ym + 5.0, w('ritzel_flansch_d') / 2 - 2.0,
         'Ritzel {} Z, mittig zur {}'.format(de(w('ritzel_z'), 0),
                                              L['profil_name'])),
        (ym - w('motor_bund_d') / 2 + 1.0, -5.0, 'Zentrierbund im Langloch'),
        (L['motor_y_max'] + m - 1.5, -m + 1.5,
         'NEMA 17 unter der Platte (verdeckt)'),
        (12.0, -r_mitte, 'Riemen frei bis zur Stirnseite'),
        (-30.0, -r_mitte, 'Riemen in der oberen Nut (verdeckt)'),
        (-45.0, -halb + 1.5, '{}, Stirnseite bei Y = 0'.format(
            L['profil_name']))]
    t += beschriften(a, eintraege, x_r)
    return t, a


def seitenansicht(w, L, ox, oy, x_r):
    """Von aussen (+X): Y nach rechts, Z nach oben. Gezeichnet von hinten
    nach vorn (Abstand X)."""
    a = Ansicht(ox, oy, S, Y_BEREICH, Z_BEREICH)
    ym = L['motor_y_mitte']
    m = w('motor_flansch') / 2.0
    h = w('motor_loch') / 2.0
    rr = L['trum_ruecken_x']
    t = ueberschrift(a, 'Seitenansicht von außen', 'die Nuten sind offen: '
                     'oben läuft der Riemen, unten sitzen die Nutensteine')
    o = w('nut_breite') / 2.0
    inhalt = [a.rect(Y_BEREICH[0], 0.0, 0.0, w('profil_hoehe'), 'profil')]
    for zc in (L['nut_unten_z'], L['nut_oben_z']):
        inhalt.append(a.rect(Y_BEREICH[0], 0.0, zc - o, zc + o, 'nut'))
    inhalt.append(a.rect(Y_BEREICH[0], ym + rr, L['riemen_z0'],
                         L['riemen_z1'], 'riemen'))
    inhalt.append(a.rect(ym - m, ym + m, L['motor_z0'], L['motor_flansch_z'],
                         'kauf'))
    inhalt.append(a.rect(ym - 2.5, ym + 2.5, L['platte_z1'], L['ritzel_z0'],
                         'stahl'))
    inhalt.append(a.poly(ritzel_umriss(w, L, ym), 'kauf'))
    inhalt.append(a.rect(ym - rr, ym + rr, L['riemen_z0'], L['riemen_z1'],
                         'riemen'))
    # Motorschrauben oben auf der Platte
    zk = L['platte_z1'] + w('m3_scheibe_h')
    for y in (ym - h, ym + h):
        inhalt.append(a.rect(y - w('m3_scheibe_d') / 2,
                             y + w('m3_scheibe_d') / 2, L['platte_z1'], zk,
                             'stahl'))
        inhalt.append(a.rect(y - w('m3_kopf_d') / 2, y + w('m3_kopf_d') / 2,
                             zk, zk + w('m3_kopf_h'), 'stahl'))
    # Halter: Schenkel; Fuehrungswand mit Joch und Plattenkante (buendig)
    inhalt.append(a.rect(L['wange_y0'], 0.0, L['halter_z0'], L['halter_z1'],
                         'druck'))
    inhalt.append(a.rect(0.0, L['platte_y1'], L['halter_z0'],
                         L['halter_z1'], 'druck'))
    inhalt.append(a.linie(0.0, L['platte_z0'], L['platte_y1'],
                          L['platte_z0'], KANTE, 0.6, '2 2'))
    for y, z in L['m5_loecher']:
        inhalt.append(a.kreis(y, z, w('m5_scheibe_d'), 'stahl'))
        inhalt.append(a.kreis(y, z, w('m5_kopf_d'), 'stahl'))
        inhalt.append(a.kreis(y, z, 4.0, 'stahl', fill='#8e959e'))
    t += a.ausschnitt('seite', inhalt)
    t.append(a.rahmen())
    t += a.z_skala()
    t.append(text(ox - 40, oy - 4, 'Z', 8, GRAU))
    for y in range(-50, 61, 10):
        xx, _ = a.px(y, Z_BEREICH[0])
        t.append(linie(xx, oy + a.hoehe, xx, oy + a.hoehe + 5, GRAU, 0.6))
        t.append(text(xx, oy + a.hoehe + 14, de(y, 0, True), 7.5, GRAU,
                      'middle'))
    t.append(text(ox + a.breite, oy + a.hoehe + 27, 'Y ab der Stirnseite, '
                  'nach außen positiv', 8, GRAU, 'end'))
    # Spannweg
    xa, ya = a.px(L['motor_y_min'], L['motor_z0'] - 3.0)
    xb, yb = a.px(L['motor_y_max'], L['motor_z0'] - 3.0)
    t += doppelpfeil(xa, ya, xb, yb, BLAU)
    eintraege = [
        (ym + w('ritzel_flansch_d') / 2, L['ritzel_z1'] - 0.5,
         'Ritzel oben = Wellenende, Z = {}'.format(
             de(L['ritzel_z1'], 1, True))),
        (-20.0, L['riemen_z'], 'Riemen in der oberen Nut, Mitte Z = {}'.format(
            de(L['riemen_z'], 0, True))),
        (ym - NABE_D / 2 + 0.5, L['ritzel_z0'] + 3.0,
         'Nabe unten, {} mm über der Platte'.format(de(L['ritzel_luft']))),
        (ym + h + 2.0, zk + w('m3_kopf_h') - 0.5,
         'M3×{} von oben in den Motor'.format(de(L['motor_schraube'], 0))),
        (L['platte_y1'] - 2.0, L['platte_z1'] - 1.0,
         'Platte, Oberseite = Bettseite beim Druck'),
        (L['platte_y1'] - 2.0, L['halter_z0'] + 3.0,
         'Führungswand neben dem Motor'),
        (-10.0 + 3.5, L['nut_unten_z'] + 3.5,
         'M5×{} in die untere Nut, beide Seiten'.format(
             de(L['m5_schraube'], 0))),
        (L['wange_y0'] + 3.0, L['halter_z0'] + 2.0,
         'Schenkel bis Z = {}, obere Nut bleibt frei'.format(
             de(L['halter_z1'], 1, True))),
        (ym + m - 2.0, L['motor_z0'] + 8.0,
         'NEMA 17, hängt bis Z = {} ({}er)'.format(
             de(L['motor_z0'], 1, True), de(w('motor_laenge'), 0))),
        ((L['motor_y_min'] + L['motor_y_max']) / 2, L['motor_z0'] - 3.0,
         'Spannweg ±{} mm'.format(de(w('spann_weg') / 2.0, 0))),
        (-45.0, 1.5, '{} hochkant, Unterkante Z = 0'.format(
            L['profil_name']))]
    t += beschriften(a, eintraege, x_r)
    return t, a


def schnitt(w, L, ox, oy, x_r):
    """Schnitt A-A quer durch Profil und Schenkel, Blick zum Motor (+Y):
    X nach rechts, Z nach oben."""
    a = Ansicht(ox, oy, S, X_BEREICH, Z_BEREICH)
    halb = w('profil_breite') / 2.0
    hb = L['halbe_breite']
    m = w('motor_flansch') / 2.0
    fr = w('ritzel_flansch_d') / 2.0
    z = L['nut_unten_z']
    t = ueberschrift(a, 'Schnitt A–A (Y = {})'.format(de(SCHNITT_Y, 0, True)),
                     'Blick zum Motor; hell = dahinter')
    inhalt = [a.rect(-hb, hb, L['halter_z0'], L['halter_z1'], 'hinten'),
              a.rect(-m, m, L['motor_z0'], L['halter_z0'], 'hinten'),
              a.rect(-halb, halb, 0.0, w('profil_hoehe'), 'profil')]
    for zc in (L['nut_unten_z'], L['nut_oben_z']):
        for sx in (-1, 1):
            inhalt.append(a.poly(nut_seite(w, sx, zc, halb), 'frei'))
        inhalt.append(a.kreis(0.0, zc, KERNBOHRUNG, 'frei'))
    inhalt.append(a.poly(nut_quer(w, w('profil_hoehe'), -1), 'frei'))
    inhalt.append(a.poly(nut_quer(w, 0.0, 1), 'frei'))
    inhalt.append(a.rect(-fr, fr, L['ritzel_z0'], L['ritzel_z1'], 'hinten',
                         fill='none', stroke_dasharray='3 2'))
    for sx in (-1, 1):
        inhalt.append(a.rect(sx * L['trum_zahn_x'], sx * L['trum_ruecken_x'],
                             L['riemen_z0'], L['riemen_z1'], 'riemen'))
        inhalt.append(a.rect(sx * L['wange_x0'], sx * L['wange_x1'],
                             L['halter_z0'], L['halter_z1'], 'druck'))
        inhalt.append(a.poly(nutenstein(w, sx, z, halb), 'stahl',
                             fill='#aab1ba'))
        x_s = L['wange_x1'] + w('m5_scheibe_h')
        inhalt.append(a.rect(sx * L['wange_x1'], sx * x_s,
                             z - w('m5_scheibe_d') / 2,
                             z + w('m5_scheibe_d') / 2, 'stahl'))
        inhalt.append(a.rect(sx * x_s, sx * (x_s + w('m5_kopf_h')),
                             z - w('m5_kopf_d') / 2, z + w('m5_kopf_d') / 2,
                             'stahl'))
        inhalt.append(a.rect(sx * (halb - L['m5_ueberstand']),
                             sx * L['wange_x1'], z - 2.5, z + 2.5, 'stahl'))
    t += a.ausschnitt('schnitt', inhalt)
    t.append(a.rahmen())
    t += a.z_skala()
    eintraege = [
        (L['trum_ruecken_x'] - 0.5, L['riemen_z1'] - 1.0,
         'Riemen in beiden oberen Nuten'),
        (fr - 0.5, L['ritzel_z1'] - 1.0, 'Ritzel dahinter (verdeckt)'),
        (L['wange_x1'] - 1.0, L['halter_z1'] - 1.0,
         'Schenkel an beiden Seiten'),
        (L['wange_x1'] + w('m5_scheibe_h') + w('m5_kopf_h') - 1.0, z + 2.0,
         'M5×{} mit Scheibe'.format(de(L['m5_schraube'], 0))),
        (halb - w('nut_lippe') - 2.0, z - 3.0,
         'Nutenstein, {} mm Eingriff'.format(de(L['m5_eingriff']))),
        (hb - 1.0, L['halter_z0'] + 1.0, 'Joch, Platte, Wände dahinter'),
        (m - 2.0, L['motor_z0'] + 6.0, 'NEMA 17 dahinter')]
    t += beschriften(a, eintraege, x_r)
    return t, a


def detail(w, L, ox, oy, x_r):
    """Rechte obere Nut im Schnitt A-A, vergroessert."""
    a = Ansicht(ox, oy, S_DETAIL, DETAIL_X, DETAIL_Z)
    halb = w('profil_breite') / 2.0
    t = ueberschrift(a, 'Detail: Riemen in der Nut', 'rechte obere Nut aus '
                     'A–A; Nutform vereinfacht')
    zg = L['trum_zahn_x'] + w('riemen_zahn')
    inhalt = [a.rect(DETAIL_X[0], halb, DETAIL_Z[0], DETAIL_Z[1], 'profil'),
              a.poly(nut_seite(w, 1, L['nut_oben_z'], halb), 'frei'),
              a.poly(nut_quer(w, w('profil_hoehe'), -1), 'frei'),
              a.rect(L['trum_zahn_x'], L['trum_ruecken_x'], L['riemen_z0'],
                     L['riemen_z1'], 'riemen'),
              a.linie(zg, L['riemen_z0'], zg, L['riemen_z1'], '#8e959e', 0.8,
                      '2 2')]
    t += a.ausschnitt('detail', inhalt)
    t.append(a.rahmen())
    # Masse ab der Seitenflaeche, unter der Nut
    xf, _ = a.px(halb, 0.0)
    _, y_oben = a.px(0.0, DETAIL_Z[1])
    t.append(linie(xf, y_oben, xf, y_oben + a.hoehe, BLAU, 0.6, '3 2'))
    masse = [(halb - w('nut_lippe'), de(w('nut_lippe'))),
             (L['trum_ruecken_x'], de(L['trum_tiefe_ruecken'], 2)),
             (L['trum_zahn_x'], de(L['trum_tiefe_zahn'], 2)),
             (halb - w('nut_tiefe'), de(w('nut_tiefe')))]
    for i, (x, s) in enumerate(masse):
        v = 23.6 - i * 1.2
        xa, ya = a.px(halb, v)
        xb, yb = a.px(x, v)
        t += [linie(xa, ya, xb, yb, BLAU, 0.7),
              pfeil(xb, yb, xb - xa, 0.0, BLAU, 4.0, 1.6),
              text(xb - 3, yb + 3, s, 7.5, BLAU, 'end', halo=True)]
    eintraege = [
        (halb - w('nut_lippe') / 2, L['nut_oben_z'] + w('nut_breite') / 2
         + 0.6, 'Lippe {} mm; {} mm Luft zum Riemenrücken'.format(
             de(w('nut_lippe')), de(L['luft_lippe'], 2))),
        (L['trum_ruecken_x'] - 0.3, L['riemen_z'] + 1.5,
         'Riemen {} × {} mm, Rücken außen'.format(
             de(w('riemen_breite'), 0), de(w('riemen_dicke'), 2))),
        (zg - 0.4, L['riemen_z'] - 1.0,
         'Zähne innen, Wirklinie X = ±{}'.format(de(L['rp'], 2))),
        (halb - w('nut_tiefe') + 0.3, L['nut_oben_z'] - 2.2,
         'Nutgrund: {} mm Luft zu den Zahnspitzen'.format(
             de(L['luft_nutgrund'], 2))),
        (halb - 0.3, 20.0, 'Maße ab der Seitenfläche der {}'.format(
            L['profil_name']))]
    t += beschriften(a, eintraege, x_r, 12.0)
    return t, a


def main():
    mod = pruef.modul_laden()
    w, L = mod.w, mod.lage()
    breite = 1380.0
    t = [el('rect', {'width': '100%', 'height': '100%', 'fill': '#ffffff'}),
         text(18, 24, 'Y-Motorhalter am Ende der {} — je Seite einer, '
              'dasselbe Teil links und rechts'.format(L['profil_name']), 13,
              TEXT, fett=True),
         text(18, 40, 'Der Y-Riemen läuft in den oberen Nuten beider '
              'Seitenflächen und um das Ritzel direkt auf der Motorwelle. '
              'Der Halter sitzt mit {} × M5 in den unteren Nuten.'.format(
                  L['n_m5']), 8.5, GRAU),
         text(18, 53, 'Aus YMotorhalter.py Rev. {} · Y = 0 Stirnseite, '
              'Z = 0 Unterkante, X = 0 Mitte der {} · Maße in mm'.format(
                  mod.REVISION, L['profil_name']), 8.5, GRAU)]

    x_links = 64.0
    oben = 106.0
    x_label = x_links + (Y_BEREICH[1] - Y_BEREICH[0]) * S + 12
    x_rechts = 846.0
    teil, a_drauf = draufsicht(w, L, x_links, oben, x_label)
    t += teil
    teil, a_detail = detail(w, L, x_rechts, oben, x_rechts
                            + (DETAIL_X[1] - DETAIL_X[0]) * S_DETAIL + 12)
    t += teil
    unten = oben + max(a_drauf.hoehe, a_detail.hoehe) + 70
    teil, a_seite = seitenansicht(w, L, x_links, unten, x_label)
    t += teil
    teil, a_schnitt = schnitt(w, L, x_rechts, unten, x_rechts
                              + (X_BEREICH[1] - X_BEREICH[0]) * S + 12)
    t += teil
    hoehe = unten + max(a_seite.hoehe, a_schnitt.hoehe) + 78

    ly = hoehe - 24
    for i, (art, s) in enumerate((
            ('druck', 'gedruckt (PETG)'),
            ('kauf', 'Kaufteil'),
            ('stahl', 'Schrauben, Welle, Nutenstein'),
            ('riemen', 'GT2-Riemen'),
            ('profil', 'Aluprofil ' + L['profil_name']),
            ('hinten', 'dahinter'))):
        x = 18 + i * 190
        t.append(rect_px(x, ly, x + 14, ly + 9, art))
        t.append(text(x + 19, ly + 8, s, 8.5))

    svg = '\n'.join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" '
        'height="{:.0f}" viewBox="0 0 {:.0f} {:.0f}" font-family="Inter, '
        'Helvetica, Arial, sans-serif">'.format(breite, hoehe, breite, hoehe)]
        + t + ['</svg>'])
    xml.dom.minidom.parseString(svg.encode('utf-8'))   # wirft bei Fehlern
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg + '\n')
    print('geschrieben: {}  ({:.0f} x {:.0f} px)'.format(
        os.path.relpath(ZIEL), breite, hoehe))


if __name__ == '__main__':
    main()
