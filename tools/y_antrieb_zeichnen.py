#!/usr/bin/env python3
"""Skizze des Y-Antriebs: Riemenlauf von oben, Halter von oben, Schnitt.

Oben der ganze Motorriemen um die beiden senkrechten Wellen mit dem Omega am
Motor und der Drehrichtung, darunter der Halter massstaeblich von oben und
geschnitten in seiner Mitte. Alle Masse kommen aus YMotorhalter.py; die
Skizze wandert also mit den Parametern.

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

S_LAUF = 1.6                # px/mm, Riemenlauf von oben
S_HALTER = 3.0              # px/mm, Halter von oben und Schnitt
LAUF_Y = (-78.0, 130.0)     # Maschinen-Y im Riemenlauf
DRAUF_X = (-44.0, 44.0)     # Halter von oben
DRAUF_Y = (-24.0, 128.0)
SCHNITT_Y = (-26.0, 128.0)  # Schnitt X = 0
SCHNITT_Z = (-46.0, 56.0)

KOPF_M3, SCHEIBE_M3 = 5.5, 7.0
WELLE_D = 5.0

FARBE = {
    'druck':   ('#c9d9ec', '#2f5d92'),
    'kauf':    ('#e8ded0', '#8a6d3b'),
    'stahl':   ('#c3c8cf', '#4a4f57'),
    'messing': ('#e3c46b', '#8a6d1b'),
    'hinten':  ('#eef2f7', '#a9b6c8'),
    'profil':  ('#dfe3e8', '#6b7480'),
    'frei':    ('#ffffff', '#2f5d92'),
}
TEXT = '#1c2733'
GRAU = '#5b6472'
BLAU = '#2f5d92'
BRAUN = '#8a6d3b'
ROT = '#b4342f'
RIEMEN = '#1c2733'
Y_RIEMEN = '#c77d1a'


# ---- SVG-Bausteine (wie in antrieb_zeichnen.py) -----------------------------

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


def kreis_px(cx, cy, r, art, **mehr):
    a = {'cx': f1(cx), 'cy': f1(cy), 'r': f1(r)}
    a.update(stil(art, mehr))
    return el('circle', a)


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


def bogen(cx, cy, r, w0, w1, n=24):
    """Punkte auf einem Kreisbogen (Winkel in Grad, mathematisch positiv,
    Bildschirm-y nach unten: deshalb Minus beim Sinus)."""
    return [(cx + r * math.cos(math.radians(w0 + (w1 - w0) * i / n)),
             cy - r * math.sin(math.radians(w0 + (w1 - w0) * i / n)))
            for i in range(n + 1)]


def drehpfeil(cx, cy, r, farbe):
    """Pfeil gegen den Uhrzeigersinn um (cx, cy) — von oben gesehen."""
    pts = bogen(cx, cy, r, 190, 340, 20)
    ende = pts[-1]
    vor = pts[-2]
    return [pfad(pts, farbe, 1.6),
            pfeil(ende[0], ende[1], ende[0] - vor[0], ende[1] - vor[1],
                  farbe, 6.0, 2.6)]


class Draufsicht:
    """Von oben: Maschinen-X nach rechts, Maschinen-Y (nach hinten) nach
    oben."""

    def __init__(self, ox, oy, s, xb, yb):
        self.ox, self.oy, self.s, self.xb, self.yb = ox, oy, s, xb, yb
        self.breite = (xb[1] - xb[0]) * s
        self.hoehe = (yb[1] - yb[0]) * s

    def px(self, x, y):
        return (self.ox + (x - self.xb[0]) * self.s,
                self.oy + (self.yb[1] - y) * self.s)

    def rect(self, x0, x1, y0, y1, art, **mehr):
        (xa, ya), (xb, yb) = self.px(x0, y0), self.px(x1, y1)
        return rect_px(xa, ya, xb, yb, art, **mehr)

    def kreis(self, x, y, d, art, **mehr):
        cx, cy = self.px(x, y)
        return kreis_px(cx, cy, d / 2.0 * self.s, art, **mehr)

    def poly(self, punkte, art, **mehr):
        return poly_px([self.px(x, y) for x, y in punkte], art, **mehr)

    def ausschnitt(self, name, inhalt):
        rahmen = el('rect', {'x': f1(self.ox), 'y': f1(self.oy),
                             'width': f1(self.breite),
                             'height': f1(self.hoehe)})
        return ([el('clipPath', {'id': name}, rahmen),
                 '<g clip-path="url(#{})">'.format(name)] + inhalt + ['</g>'])


class Schnitt(Draufsicht):
    """Schnitt X = 0, Blick von +X: Maschinen-Y nach rechts, Z nach oben.
    Wiederverwendet die Draufsicht mit (Y, Z) statt (X, Y)."""


def stadion(x, yc, hub, breite, n=12):
    """Langloch laengs Y (Mitte yc, +-hub, Breite breite) als Punktzug in
    Maschinenkoordinaten."""
    r = breite / 2.0
    p = [(x + r * math.cos(math.radians(180.0 * i / n)),
          yc + hub + r * math.sin(math.radians(180.0 * i / n)))
         for i in range(n + 1)]
    p += [(x + r * math.cos(math.radians(180.0 + 180.0 * i / n)),
           yc - hub + r * math.sin(math.radians(180.0 + 180.0 * i / n)))
          for i in range(n + 1)]
    return p


def riemenweg(L, w, s_welle, n=16):
    """Wirklinie des Motorriemens in Maschinen-X/Y, als geschlossener Zug:
    vorderer Trum, um die rechte Welle, hinterer Trum bis zur rechten
    Rolle, Omega um den Motor (Motor ganz vorn), linke Rolle, hinterer Trum,
    um die linke Welle."""
    xs = s_welle / 2.0
    wy = w('welle_y')
    rw, rr, rm = L['rp_welle'], L['rp_rolle'], L['rp_motor']
    rx, ry = L['rolle_x'], L['rolle_y']
    ym = L['motor_y_min']
    p = [(-xs, wy - rw), (xs, wy - rw)]
    p += [(xs + rw * math.cos(math.radians(a)),
           wy + rw * math.sin(math.radians(a)))
          for a in [-90 + 180 * i / n for i in range(n + 1)]]
    p.append((rx, ry - rr))
    # rechte Rolle: vom unteren Punkt im Uhrzeigersinn zum linken Punkt
    p += [(rx + rr * math.cos(math.radians(a)),
           ry + rr * math.sin(math.radians(a)))
          for a in [-90 - 90 * i / n for i in range(n + 1)]]
    p.append((rm, ym))
    p += [(rm * math.cos(math.radians(a)), ym + rm * math.sin(math.radians(a)))
          for a in [180 * i / n for i in range(n + 1)]]
    p.append((-rx + rr, ry))
    p += [(-rx + rr * math.cos(math.radians(a)),
           ry + rr * math.sin(math.radians(a)))
          for a in [0 - 90 * i / n for i in range(n + 1)]]
    p.append((-xs, wy + rw))
    p += [(-xs + rw * math.cos(math.radians(a)),
           wy + rw * math.sin(math.radians(a)))
          for a in [90 + 180 * i / n for i in range(n + 1)]]
    return p


def riemenlauf(w, L, ox, oy, breite):
    """Ganzer Motorriemen von oben, S wie in MASSE."""
    s_welle = w('welle_abstand')
    s = min(S_LAUF, (breite - 60.0) / (s_welle + 40.0))
    xb = (-s_welle / 2.0 - 20.0, s_welle / 2.0 + 20.0)
    a = Draufsicht(ox + (breite - (xb[1] - xb[0]) * s) / 2.0, oy, s, xb,
                   LAUF_Y)
    t = [text(ox, oy - 22, 'Motorriemen von oben', 10, BLAU, fett=True),
         text(ox, oy - 9, 'maßstäblich für S = {} mm; hinten (weg von der '
              'Maschine) = oben; die Y-Riemen laufen über der {} nach vorn'
              .format(de(s_welle, 0), L['profil_name']), 8, GRAU)]
    inhalt = []
    # Traverse und Halter
    inhalt.append(a.rect(xb[0], xb[1], -w('profil_tiefe'), 0.0, 'profil'))
    hb = L['halbe_breite']
    inhalt.append(a.rect(-hb, hb, 0.0, L['boden_y1'], 'druck',
                         fill_opacity='0.55'))
    inhalt.append(a.rect(-w('motor_flansch') / 2, w('motor_flansch') / 2,
                         L['motor_y_min'] - w('motor_flansch') / 2,
                         L['motor_y_min'] + w('motor_flansch') / 2, 'kauf',
                         stroke_dasharray='3 2', fill_opacity='0.6'))
    # Y-Riemen an den oberen Ritzeln (gleiche Achse, hoeher), nach vorn
    rw = L['rp_welle']
    for sx in (-1, 1):
        xw = sx * s_welle / 2.0
        for dx in (-rw, rw):
            inhalt.append(pfad([a.px(xw + dx, w('welle_y')),
                                a.px(xw + dx, LAUF_Y[0])], Y_RIEMEN, 1.6))
        inhalt.append(pfad([a.px(xw + rw * math.cos(math.radians(g)),
                                 w('welle_y') + rw * math.sin(
                                     math.radians(g)))
                            for g in range(0, 181, 15)], Y_RIEMEN, 1.6))
    # Motorriemen
    inhalt.append(pfad([a.px(x, y) for x, y in riemenweg(L, w, s_welle)],
                       RIEMEN, 1.5, zu=True))
    # Rollen, Ritzel
    for x, y in L['rolle_loecher']:
        inhalt.append(a.kreis(x, y, w('rolle_d'), 'stahl'))
    inhalt.append(a.kreis(0.0, L['motor_y_min'], 2 * L['rp_motor'], 'stahl'))
    for sx in (-1, 1):
        inhalt.append(a.kreis(sx * s_welle / 2.0, w('welle_y'),
                              2 * L['rp_welle'], 'stahl'))
    t += a.ausschnitt('lauf', inhalt)

    # Drehrichtung: alle drei Ritzel gleichsinnig
    for x, y in ((-s_welle / 2.0, w('welle_y')), (s_welle / 2.0,
                                                   w('welle_y')),
                 (0.0, L['motor_y_min'])):
        cx, cy = a.px(x, y)
        t += drehpfeil(cx, cy, 17.0, ROT)
    # Laufrichtung der Trume
    for x, y, dx in ((-s_welle / 4.0, L['trum_vorn_y'], 1),
                     (s_welle / 4.0, L['trum_hinten_y'], -1),
                     (-s_welle / 4.0, L['trum_hinten_y'], -1)):
        px, py = a.px(x, y)
        t.append(pfeil(px + dx * 5, py, dx, 0, RIEMEN, 6.0, 2.4))
    # Y-Riemen: rechter Trum faehrt nach hinten (oben), linker nach vorn
    for sx in (-1, 1):
        xw = sx * s_welle / 2.0
        for dx, dy in ((rw, 1), (-rw, -1)):
            px, py = a.px(xw + dx, -52.0)
            t.append(pfeil(px, py - dy * 6, 0, -dy, Y_RIEMEN, 6.0, 2.4))
        # Wagen am rechten Trum
        px, py = a.px(xw + rw, -64.0)
        t.append(rect_px(px - 5, py - 7, px + 5, py + 7, 'kauf',
                         stroke=ROT, stroke_width='1.2'))
    # Beschriftung
    xl, _ = a.px(-s_welle / 2.0, 0)
    xr, _ = a.px(s_welle / 2.0, 0)
    _, y_w = a.px(0, w('welle_y'))
    _, y_prof = a.px(0, -w('profil_tiefe') / 2.0)
    _, y_unten = a.px(0, LAUF_Y[0])
    t.append(text(xl + 20, y_w - 22, 'Welle links: unteres Ritzel (Motor'
                  'riemen) + oberes (Y-Riemen)', 8, TEXT, halo=True))
    t.append(text(xr - 20, y_w - 22, 'Welle rechts', 8, TEXT, 'end',
                  halo=True))
    t.append(text((xl + xr) / 2.0 - 180, y_prof + 3, '{} hinten, hochkant'
                  .format(L['profil_name']), 8, TEXT, 'middle', halo=True))
    cx, cy = a.px(0.0, L['motor_y_min'])
    t.append(text(cx + 36, cy - 30, 'Motor + zwei Umlenkrollen: Omega, '
                  '180° am Motorritzel', 8, TEXT, halo=True))
    t.append(text(xl + 14, y_unten - 4, 'Wagen am rechten Trum', 8, ROT,
                  halo=True))
    t.append(text(xr + 14, y_unten - 4, 'Wagen am rechten Trum', 8, ROT,
                  halo=True))
    t.append(text((xl + xr) / 2.0, y_unten + 14,
                  'Alle drei Ritzel drehen gleichsinnig (rote Pfeile). Damit '
                  'beide Wagen gleich fahren, hängen beide am selben Trum '
                  '(hier: rechts, vom Bediener aus) — nicht spiegelbildlich.',
                  8.5, ROT, 'middle'))
    return t, a.hoehe + 40


def halter_oben(w, L, ox, oy):
    """Halter massstaeblich von oben, Motor ganz vorn."""
    a = Draufsicht(ox, oy, S_HALTER, DRAUF_X, DRAUF_Y)
    hb = L['halbe_breite']
    h = w('motor_loch') / 2.0
    ym0, ym1, ymm = L['motor_y_min'], L['motor_y_max'], L['motor_y_mitte']
    t = [text(ox, oy - 22, 'Halter von oben', 10, BLAU, fett=True),
         text(ox, oy - 9, 'Motor ganz vorn (gestrichelt), unter dem Boden '
              'grau', 8, GRAU)]
    inhalt = [a.rect(DRAUF_X[0], DRAUF_X[1], -w('profil_tiefe'), 0.0,
                     'profil')]
    # Boden mit Rippen und Block
    inhalt.append(a.rect(-hb, hb, 0.0, L['boden_y1'], 'druck'))
    for sx in (-1, 1):
        inhalt.append(a.rect(sx * L['rippe_x0'], sx * hb, 0.0,
                             L['boden_y1'], 'druck', fill='#b3c8e2'))
    inhalt.append(a.rect(-L['rippe_x0'], L['rippe_x0'], 0.0, L['block_y1'],
                         'druck', fill='#b3c8e2'))
    inhalt.append(a.rect(-w('lasche_breite') / 2, w('lasche_breite') / 2,
                         L['lasche_y0_unten'], L['block_y1'], 'druck',
                         fill='#9db7d8'))
    inhalt.append(a.rect(-hb, hb, 0.0, L['grund_y1'], 'druck',
                         fill='#9db7d8'))
    # Ausschnitte im Boden: Bundtasche (flach, gestrichelt), Wellenschlitz
    # und die vier Langloecher der Motorschrauben (durch)
    hub = w('spann_weg') / 2.0
    inhalt.append(a.poly(stadion(0.0, ymm, hub, L['bund_schlitz_b']),
                         'druck', fill='#dde8f4', stroke_dasharray='2 2'))
    inhalt.append(a.poly(stadion(0.0, ymm, hub, w('wellen_schlitz')),
                         'frei'))
    for x, yc in L['motor_langloecher']:
        inhalt.append(a.poly(stadion(x, yc, hub, w('m3_durchgang')), 'frei'))
    # unter dem Boden: Rollen, Ritzel, Riemen (grau, gestrichelt)
    for x, y in L['rolle_loecher']:
        inhalt.append(a.kreis(x, y, w('rolle_flansch_d'), 'hinten',
                              stroke_dasharray='3 2', fill_opacity='0.7'))
    inhalt.append(a.kreis(0.0, ym0, w('ritzel_flansch_d'), 'hinten',
                          stroke_dasharray='3 2', fill_opacity='0.7'))
    s_welle = w('welle_abstand')
    inhalt.append(pfad([a.px(x, y) for x, y in riemenweg(L, w, s_welle)],
                       '#4a4f57', 1.4, '5 2', zu=True))
    for x, y in L['rolle_loecher']:
        inhalt.append(a.kreis(x, y, 8.5, 'stahl'))          # M5-Kopf oben
    # Motor (ganz vorn) und Spannschraube
    m = w('motor_flansch') / 2.0
    inhalt.append(a.rect(-m, m, ym0 - m, ym0 + m, 'kauf',
                         stroke_dasharray='4 2', fill_opacity='0.35'))
    for x, y in [(sx * h, ym0 + sy * h) for sx in (-1, 1) for sy in (-1, 1)]:
        inhalt.append(a.kreis(x, y, SCHEIBE_M3, 'stahl', fill_opacity='0.7'))
    inhalt.append(a.rect(-1.5, 1.5, L['spann_kopf_y'],
                         L['block_y1'] + L['spann_spitze_min'], 'stahl'))
    inhalt.append(a.rect(-KOPF_M3 / 2, KOPF_M3 / 2,
                         L['spann_kopf_y'] - 3.0, L['spann_kopf_y'],
                         'stahl'))
    t += a.ausschnitt('halter_oben', inhalt)

    # Beschriftung rechts daneben
    x_r = ox + a.breite + 10
    eintraege = [
        (hb, L['boden_y1'] - 6, 'Führungsrippe, Motor mit 0,2 mm Luft'),
        (0.0, ym1 + 11, 'Wellen- und Bundschlitz: {} mm Spannweg'.format(
            de(w('spann_weg'), 0))),
        (h, ym0 + h, 'Motorschraube M3 im Langloch'),
        (0.0, ym0, 'Motorritzel unter dem Boden'),
        (w('lasche_breite') / 2, L['block_y1'] - 4,
         'Spannlasche, Spannschraube M3x{} drückt'.format(
             de(L['spann_schraube'], 0))),
        (L['rolle_x'] + 4, L['rolle_y'], 'Umlenkrolle 2x F625ZZ, Achse M5'),
        (hb, L['trum_hinten_y'], 'hinterer Trum zur Welle'),
        (hb, L['trum_vorn_y'], 'vorderer Trum, läuft unter dem Boden durch'),
        (hb, L['grund_y1'] / 2, 'Anlageplatte an der {}'.format(
            L['profil_name'])),
        (DRAUF_X[1] - 2, -w('profil_tiefe') / 2, L['profil_name'])]
    belegt = -1e9
    for x, y, s in sorted(eintraege, key=lambda e: -e[1]):
        px, py = a.px(x, y)
        ty = max(py + 3, belegt + 11)
        belegt = ty
        t += [linie(px, py, x_r - 3, ty - 3, GRAU, 0.6),
              el('circle', {'cx': f1(px), 'cy': f1(py), 'r': '1.4',
                            'fill': GRAU}),
              text(x_r, ty, s, 7.5)]
    t.append(text(ox, oy + a.hoehe + 13, 'oben = hinten (weg von der '
                  'Maschine) · Riemen unter dem Boden gestrichelt', 7.5,
                  GRAU))
    return t, a.breite, a.hoehe


def schnitt(w, L, ox, oy):
    """Schnitt in der Mitte des Halters (X = 0), Blick von +X, Motor ganz
    vorn. Hinter der Schnittebene (hell): Rolle, Rippe, M5-Schrauben."""
    a = Schnitt(ox, oy, S_HALTER, SCHNITT_Y, SCHNITT_Z)
    ym = L['motor_y_min']
    m = w('motor_flansch') / 2.0
    z_b0, z_b1 = L['boden_z0'], L['boden_z1']
    t = [text(ox, oy - 22, 'Schnitt in der Mitte (X = 0)', 10, BLAU,
              fett=True),
         text(ox, oy - 9, 'Blick von der Seite, hinten = rechts; Motor ganz '
              'vorn; hell = hinter der Schnittebene', 8, GRAU)]
    inhalt = []
    # ---- dahinter ---------------------------------------------------------
    # Boden neben dem Wellenschlitz und die Fuehrungsrippe
    inhalt.append(a.rect(0.0, L['boden_y1'], z_b0, z_b1, 'hinten'))
    inhalt.append(a.rect(0.0, L['boden_y1'], z_b1, L['block_z1'], 'hinten'))
    ry = L['rolle_y']
    inhalt.append(a.rect(ry - w('rolle_flansch_d') / 2,
                         ry + w('rolle_flansch_d') / 2, L['rolle_z1']
                         - w('rolle_flansch_h'), L['rolle_z1'], 'hinten'))
    inhalt.append(a.rect(ry - w('rolle_d') / 2, ry + w('rolle_d') / 2,
                         L['rolle_z0'] + w('rolle_flansch_h'),
                         L['rolle_z1'] - w('rolle_flansch_h'), 'hinten'))
    inhalt.append(a.rect(ry - w('rolle_flansch_d') / 2,
                         ry + w('rolle_flansch_d') / 2, L['rolle_z0'],
                         L['rolle_z0'] + w('rolle_flansch_h'), 'hinten'))
    inhalt.append(a.rect(ry - 2.5, ry + 2.5, L['rolle_schraube_z0'],
                         L['block_z1'] + w('m5_scheibe_h'), 'hinten',
                         stroke='#8c96a3'))
    inhalt.append(a.rect(ry - 4.25, ry + 4.25, L['block_z1']
                         + w('m5_scheibe_h'), L['block_z1']
                         + w('m5_scheibe_h') + 5.0, 'hinten',
                         stroke='#8c96a3'))
    for _, z in L['m5_loecher'][::2]:
        inhalt.append(a.rect(-w('nut_tiefe'), L['grund_y1'] + 1.0, z - 2.5,
                             z + 2.5, 'hinten', stroke='#8c96a3'))
        inhalt.append(a.rect(L['grund_y1'] + 1.0, L['grund_y1'] + 6.0,
                             z - 4.25, z + 4.25, 'hinten', stroke='#8c96a3'))
    # Omega-Trum hinter der Ebene (X = -rp_motor): Wirklinie als Band
    inhalt.append(a.rect(ry, ym, w('riemen_z') - 3, w('riemen_z') + 3,
                         'hinten', stroke='#8c96a3'))

    # ---- Traverse im Schnitt, Nuten an der Rueckseite --------------------
    inhalt.append(a.rect(-w('profil_tiefe'), 0.0, -w('profil_hoehe'), 0.0,
                         'profil'))
    for z in L['nut_z']:
        inhalt.append(a.rect(-w('nut_tiefe'), 0.0, z - 3.0, z + 3.0, 'frei',
                             stroke='#6b7480'))
    # ---- Halter geschnitten ----------------------------------------------
    b = w('wellen_schlitz') / 2.0
    r = L['bund_schlitz_b'] / 2.0
    ym0, ym1 = L['motor_y_min'], L['motor_y_max']
    inhalt.append(a.rect(0.0, L['grund_y1'], L['grund_z0'],
                         L['grund_z1'], 'druck'))
    inhalt.append(a.rect(0.0, L['block_y1'], z_b1, L['block_z1'], 'druck'))
    inhalt.append(a.poly([(L['lasche_y0_unten'], L['block_z1']),
                          (L['block_y1'], L['block_z1']),
                          (L['block_y1'], L['lasche_z1']),
                          (L['lasche_y0_oben'], L['lasche_z1'])], 'druck'))
    # Boden: vorn bis zum Bundschlitz voll, dann Tasche + Wellenschlitz
    z_t = z_b1 - L['bund_tasche_t']
    inhalt.append(a.poly([(0.0, z_b0), (ym0 - b, z_b0), (ym0 - b, z_t),
                          (ym0 - r, z_t), (ym0 - r, z_b1), (0.0, z_b1)],
                         'druck'))
    inhalt.append(a.poly([(ym1 + b, z_b0), (L['boden_y1'], z_b0),
                          (L['boden_y1'], z_b1), (ym1 + r, z_b1),
                          (ym1 + r, z_t), (ym1 + b, z_t)], 'druck'))
    # Einsatz und Spannschraube
    inhalt.append(a.rect(L['block_y1'] - w('insert_m3_t'), L['block_y1'],
                         L['spann_z'] - 2.5, L['spann_z'] + 2.5, 'messing'))
    inhalt.append(a.rect(L['spann_kopf_y'],
                         L['block_y1'] + L['spann_spitze_min'],
                         L['spann_z'] - 1.5, L['spann_z'] + 1.5, 'stahl'))
    inhalt.append(a.rect(L['spann_kopf_y'] - 3.0, L['spann_kopf_y'],
                         L['spann_z'] - KOPF_M3 / 2, L['spann_z']
                         + KOPF_M3 / 2, 'stahl'))
    # Motor, Bund, Welle, Ritzel
    inhalt.append(a.rect(ym - m, ym + m, L['motor_flansch_z'],
                         L['motor_z1'], 'kauf'))
    inhalt.append(a.rect(ym - w('motor_bund_d') / 2,
                         ym + w('motor_bund_d') / 2,
                         L['motor_flansch_z'] - w('motor_bund_h'),
                         L['motor_flansch_z'], 'kauf'))
    inhalt.append(a.rect(ym - WELLE_D / 2, ym + WELLE_D / 2, L['welle_z0'],
                         L['motor_flansch_z'] - w('motor_bund_h'), 'stahl'))
    fr = w('ritzel_flansch_d') / 2.0
    zr1, zr0 = L['ritzel_z1'], L['ritzel_z0']
    fh = w('ritzel_flansch_h')
    for v in (-1, 1):
        inhalt.append(a.poly([
            (ym + v * WELLE_D / 2, zr1), (ym + v * fr, zr1),
            (ym + v * fr, zr1 - fh), (ym + v * L['rp_motor'], zr1 - fh),
            (ym + v * L['rp_motor'], zr1 - fh - w('ritzel_spur')),
            (ym + v * fr, zr1 - fh - w('ritzel_spur')),
            (ym + v * fr, zr0), (ym + v * WELLE_D / 2, zr0)], 'kauf'))
    # Riemen im Schnitt: vorderer Trum und hinten um das Motorritzel
    z0, z1 = L['riemen_z0'], L['riemen_z1']
    inhalt.append(a.rect(L['trum_vorn_y'] - L['wirk_ruecken'],
                         L['trum_vorn_y'] + L['wirk_zahn'], z0, z1, 'stahl',
                         fill=RIEMEN))
    inhalt.append(a.rect(ym + L['rp_motor'] - L['wirk_zahn'],
                         ym + L['rp_motor'] + L['wirk_ruecken'], z0, z1,
                         'stahl', fill=RIEMEN))
    # Motorschraube vorn (in die Schnittebene gedreht)
    for yy in (ym - w('motor_loch') / 2, ym + w('motor_loch') / 2):
        inhalt.append(a.rect(yy - 1.5, yy + 1.5, z_b1 + L['motor_eingriff'],
                             z_b0, 'stahl'))
        inhalt.append(a.rect(yy - KOPF_M3 / 2, yy + KOPF_M3 / 2,
                             z_b0 - w('m3_scheibe_h') - 3.0,
                             z_b0 - w('m3_scheibe_h'), 'stahl'))
    t += a.ausschnitt('schnitt', inhalt)

    # Z-Skala links
    for z in range(-40, 51, 10):
        _, yy = a.px(SCHNITT_Y[0], z)
        t.append(linie(ox - 6, yy, ox, yy, GRAU, 0.6))
        t.append(text(ox - 9, yy + 3, de(z, 0, True), 7.5, GRAU, 'end'))
    t.append(text(ox - 36, oy - 30 + 8, 'Z [mm]', 8, GRAU))
    # Beschriftung rechts
    x_r = ox + a.breite + 10
    eintraege = [
        (ym + m, L['motor_z1'] - 8,
         'NEMA 17, steht auf dem Boden (bis Z = {})'.format(
             de(L['motor_z1'], 0, True))),
        (L['block_y1'], L['spann_z'],
         'Spannschraube M3 in Messingeinsatz, drückt den Motor nach hinten'),
        (L['block_y1'] - 4, L['block_z1'] - 3,
         'Block, trägt die Rollenachsen (M5, hell dahinter)'),
        (ym + r, z_b1 - 1, 'Boden {} mm, Bundtasche {} mm'.format(
            de(w('boden_dicke')), de(L['bund_tasche_t']))),
        (ym + fr, zr1 - 3, 'Motorritzel 20 Z, {} mm unter dem Boden'.format(
            de(L['ritzel_luft']))),
        (ym + L['rp_motor'], w('riemen_z') - 2,
         'Riemen um das Ritzel — Riemenebene Z = {}'.format(
             de(w('riemen_z'), 0, True))),
        (ry + 8, L['rolle_z0'] + 2, 'Umlenkrolle (dahinter), Mitte in der '
         'Riemenebene'),
        (L['trum_vorn_y'], w('riemen_z') - 3,
         'vorderer Trum, {} mm hinter der Anlageplatte'.format(
             de(L['trum_vorn_y'] - L['wirk_ruecken'] - L['grund_y1']))),
        (L['grund_y1'] + 3.0, min(z for _, z in L['m5_loecher']),
         '{}x M5 in Nutensteine, nur untere Nut (oben läuft der Riemen)'
         .format(len(L['m5_loecher']))),
        (-w('profil_tiefe') / 2, -w('profil_hoehe') + 5.0,
         '{} hochkant, Nuten bei {}'.format(
             L['profil_name'], ', '.join(de(z, 0, True)
                                         for z in L['nut_z'])))]
    belegt = -1e9
    for y, z, s in sorted(eintraege, key=lambda e: -e[1]):
        px, py = a.px(y, z)
        ty = max(py + 3, belegt + 11)
        belegt = ty
        t += [linie(px, py, x_r - 3, ty - 3, GRAU, 0.6),
              el('circle', {'cx': f1(px), 'cy': f1(py), 'r': '1.4',
                            'fill': GRAU}),
              text(x_r, ty, s, 7.5)]
    return t, a.breite, a.hoehe


def main():
    mod = pruef.modul_laden()
    w, L = mod.w, mod.lage()
    breite = 1380.0
    oben = 100.0
    t = [el('rect', {'width': '100%', 'height': '100%', 'fill': '#ffffff'}),
         text(18, 22, 'Y-Antrieb — Motorhalter an der hinteren {}'.format(
             L['profil_name']), 13,
              TEXT, fett=True),
         text(18, 37, 'Ein geschlossener GT2-Riemen um die unteren Ritzel '
              'der beiden senkrechten Wellen; zwei Umlenkrollen legen ihn als '
              'Omega um das Motorritzel.', 8.5, GRAU),
         text(18, 49, 'Aus YMotorhalter.py Rev. {} · Wellenlage und '
              'Wellenabstand noch NICHT gemessen (welle_y = {} mm, S = {} mm)'
              .format(mod.REVISION, de(w('welle_y')),
                      de(w('welle_abstand'), 0)), 8.5, GRAU)]

    teil, h_lauf = riemenlauf(w, L, 18.0, oben, breite - 36.0)
    t += teil
    y2 = oben + h_lauf + 44
    teil, b_oben, h_oben = halter_oben(w, L, 30.0, y2)
    t += teil
    x_schnitt = 30.0 + b_oben + 250.0
    teil, b_schnitt, h_schnitt = schnitt(w, L, x_schnitt, y2)
    t += teil
    hoehe = y2 + max(h_oben, h_schnitt) + 64

    ly = hoehe - 26
    for i, (art, s) in enumerate((
            ('druck', 'gedruckt (PETG)'),
            ('kauf', 'Kaufteil'),
            ('stahl', 'Stahl, Riemen'),
            ('messing', 'Messing-Einsatz'),
            ('profil', 'Aluprofil ' + L['profil_name']),
            ('hinten', 'hinter der Schnittebene'))):
        x = 18 + i * 170
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
