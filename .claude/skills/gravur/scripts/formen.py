"""Vektorformen fuer gravur.py: Schrift (fontTools), SVG, Fuellen in Zeilen.

Eine Form ist ein dict:
  zuege   Liste von numpy-Arrays (n, 2) in mm, Designrahmen: x rechts, y oben
  zu      je Zug: geschlossen?
  fill    None (keine Flaeche), 'dunkel' (brennen) oder 'hell' (radiert,
          was darunter liegt: weisse Flaechen in Logos)
  regel   'nonzero' oder 'evenodd'
Formen werden in ihrer Reihenfolge gemalt (Maler-Modell wie in SVG).
"""

import glob
import math
import os
import re
import xml.etree.ElementTree as ET

import numpy as np

TOL_MM = 0.02           # Sehnenfehler beim Aufloesen von Kurven


# ---------------------------------------------------------------- Kurven

def _kubisch(p0, p1, p2, p3, tol):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    m = max(np.hypot(*(p0 - 2 * p1 + p2)), np.hypot(*(p1 - 2 * p2 + p3)))
    n = int(min(500, max(1, math.ceil(math.sqrt(6 * m / (8 * tol))))))
    t = np.linspace(0, 1, n + 1)[1:, None]
    u = 1 - t
    return (u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3).tolist()


def _quadratisch(p0, p1, p2, tol):
    p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
    m = np.hypot(*(p0 - 2 * p1 + p2))
    n = int(min(500, max(1, math.ceil(math.sqrt(2 * m / (8 * tol))))))
    t = np.linspace(0, 1, n + 1)[1:, None]
    u = 1 - t
    return (u * u * p0 + 2 * u * t * p1 + t * t * p2).tolist()


def _winkel(ux, uy, vx, vy):
    return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)


def _bogen(x1, y1, rx, ry, phi, fa, fs, x2, y2, tol):
    """SVG-Bogen (Endpunktform) als Punkte ohne den Startpunkt."""
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [[x2, y2]]
    rx, ry = abs(rx), abs(ry)
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx2, dy2 = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p, y1p = c * dx2 + s * dy2, -s * dx2 + c * dy2
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    zaehler = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    nenner = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    k = math.sqrt(max(0.0, zaehler / nenner)) if nenner else 0.0
    if fa == fs:
        k = -k
    cxp, cyp = k * rx * y1p / ry, -k * ry * x1p / rx
    cx = c * cxp - s * cyp + (x1 + x2) / 2.0
    cy = s * cxp + c * cyp + (y1 + y2) / 2.0
    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry
    th1 = _winkel(1, 0, ux, uy)
    dth = _winkel(ux, uy, vx, vy)
    if not fs and dth > 0:
        dth -= 2 * math.pi
    elif fs and dth < 0:
        dth += 2 * math.pi
    r = max(rx, ry)
    schritt = 2 * math.acos(max(-1.0, 1 - tol / r)) if tol < r else math.pi / 2
    n = int(min(720, max(2, math.ceil(abs(dth) / max(schritt, 1e-3)))))
    pts = []
    for i in range(1, n + 1):
        t = th1 + dth * i / n
        pts.append([cx + rx * math.cos(t) * c - ry * math.sin(t) * s,
                    cy + rx * math.cos(t) * s + ry * math.sin(t) * c])
    pts[-1] = [x2, y2]
    return pts


# ---------------------------------------------------------------- Formen

def form(zuege, zu, fill='dunkel', regel='nonzero'):
    return {'zuege': [np.asarray(z, float) for z in zuege], 'zu': list(zu),
            'fill': fill, 'regel': regel}


def rahmen(formen):
    """(xmin, xmax, ymin, ymax) ueber alle Zuege, None wenn leer."""
    pts = [z for f in formen for z in f['zuege'] if len(z)]
    if not pts:
        return None
    a = np.vstack(pts)
    return a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()


def abbilden(formen, fn):
    """Wendet fn(array (n,2)) -> array auf alle Zuege an (neue Formen)."""
    return [dict(f, zuege=[fn(z) for z in f['zuege']]) for f in formen]


def drehen_spiegeln(formen, drehen=0, spiegeln=False):
    """Dreht um 0/90/180/270 Grad gegen den Uhrzeigersinn, spiegelt links-rechts."""
    def fn(z):
        z = z.copy()
        if spiegeln:
            z[:, 0] = -z[:, 0]
        for _ in range((drehen // 90) % 4):
            z = np.column_stack([-z[:, 1], z[:, 0]])
        return z
    return abbilden(formen, fn)


def skalieren_verschieben(formen, faktor, dx, dy):
    return abbilden(formen, lambda z: z * faktor + np.array([dx, dy]))


def sichtbare(formen):
    """Nur Formen, die etwas brennen oder radieren: dunkel gefuellt, mit
    Strich, oder hell gefuellt ueber einer frueheren dunklen Form (weisser
    Stern im schwarzen Kreis). Ein weisser Hintergrund faellt weg."""
    aus, dunkle = [], []
    for f in formen:
        r = rahmen([f])
        if r is None:
            continue
        if f['fill'] == 'dunkel' or f.get('strich'):
            aus.append(f)
            if f['fill'] == 'dunkel':
                dunkle.append(r)
        elif f['fill'] == 'hell' and any(r[0] < d[1] and d[0] < r[1] and r[2] < d[3] and d[2] < r[3]
                                         for d in dunkle):
            aus.append(f)
    return aus


def rahmen_dunkel(formen):
    """Rahmen ohne hell gefuellte Formen (die brennen nichts)."""
    return rahmen([f for f in formen if f['fill'] != 'hell' or f.get('strich')])


# ---------------------------------------------------------------- Fuellen

def _vereinigen(a, b):
    alle = sorted(a + b)
    aus = []
    for x0, x1 in alle:
        if aus and x0 <= aus[-1][1] + 1e-9:
            if x1 > aus[-1][1]:
                aus[-1] = (aus[-1][0], x1)
        else:
            aus.append((x0, x1))
    return aus


def _abziehen(a, b):
    aus = []
    for x0, x1 in a:
        teile = [(x0, x1)]
        for y0, y1 in b:
            neu = []
            for p0, p1 in teile:
                if y1 <= p0 or y0 >= p1:
                    neu.append((p0, p1))
                    continue
                if y0 > p0:
                    neu.append((p0, y0))
                if y1 < p1:
                    neu.append((y1, p1))
            teile = neu
        aus += teile
    return aus


def _strecken(xs, w, regel):
    """Schnittpunkte einer Zeile -> innere Strecken."""
    o = np.argsort(xs, kind='mergesort')
    xs, w = xs[o], w[o]
    aus = []
    if regel == 'evenodd':
        for i in range(0, len(xs) - 1, 2):
            if xs[i + 1] > xs[i]:
                aus.append((float(xs[i]), float(xs[i + 1])))
        return aus
    summe, start = 0, None
    for x, wi in zip(xs, w):
        neu = summe + wi
        if summe == 0 and neu != 0:
            start = x
        elif summe != 0 and neu == 0 and x > start:
            aus.append((float(start), float(x)))
        summe = neu
    return aus


def zeilen_fuellen(formen, ys):
    """Fuellt die Formen auf den Zeilen ys (Maler-Modell).

    Gibt je Zeile eine sortierte Liste dunkler Strecken (x0, x1)."""
    ys = np.asarray(ys, float)
    erg = [[] for _ in ys]
    for f in formen:
        if not f['fill']:
            continue
        kanten = []
        for z in f['zuege']:
            if len(z) < 2:
                continue
            kanten.append(np.hstack([z, np.roll(z, -1, axis=0)]))
        if not kanten:
            continue
        e = np.vstack(kanten)
        e = e[e[:, 1] != e[:, 3]]
        if not len(e):
            continue
        w = np.where(e[:, 3] > e[:, 1], 1, -1)
        lo, hi = np.minimum(e[:, 1], e[:, 3]), np.maximum(e[:, 1], e[:, 3])
        for k in np.nonzero((ys >= lo.min()) & (ys < hi.max()))[0]:
            y = ys[k]
            m = (lo <= y) & (y < hi)
            if not m.any():
                continue
            em = e[m]
            xs = em[:, 0] + (y - em[:, 1]) / (em[:, 3] - em[:, 1]) * (em[:, 2] - em[:, 0])
            st = _strecken(xs, w[m], f['regel'])
            if f['fill'] == 'dunkel':
                erg[k] = _vereinigen(erg[k], st)
            else:
                erg[k] = _abziehen(erg[k], st)
    return erg


# ---------------------------------------------------------------- Linien

def linienzuege(formen):
    """Alle Zuege als (array, geschlossen), ohne leere."""
    aus = []
    for f in formen:
        for z, zu in zip(f['zuege'], f['zu']):
            if len(z) >= 2:
                aus.append((z, zu))
    return aus


def ordnen(zuege, start=(0.0, 0.0)):
    """Naechster-Nachbar-Reihenfolge; offene Zuege duerfen rueckwaerts,
    geschlossene beginnen am naechsten Punkt."""
    rest = list(zuege)
    aus = []
    pos = np.asarray(start, float)
    while rest:
        best, wert, art = None, None, None
        for i, (z, zu) in enumerate(rest):
            if zu:
                d = np.hypot(z[:, 0] - pos[0], z[:, 1] - pos[1])
                j = int(np.argmin(d))
                kand = [(d[j], ('ring', j))]
            else:
                kand = [(math.hypot(*(z[0] - pos)), ('vor', 0)),
                        (math.hypot(*(z[-1] - pos)), ('rueck', 0))]
            for dist, a in kand:
                if wert is None or dist < wert:
                    best, wert, art = i, dist, a
        z, zu = rest.pop(best)
        if art[0] == 'ring':
            j = art[1]
            ring = z[:-1] if np.allclose(z[0], z[-1]) else z
            z = np.vstack([ring[j:], ring[:j], ring[j:j + 1]])
        elif art[0] == 'rueck':
            z = z[::-1]
        elif zu and not np.allclose(z[0], z[-1]):
            z = np.vstack([z, z[:1]])
        aus.append(z)
        pos = z[-1]
    return aus


# ---------------------------------------------------------------- Schrift

SCHRIFT_ORDNER = ['/System/Library/Fonts', '/System/Library/Fonts/Supplemental',
                  '/Library/Fonts', os.path.expanduser('~/Library/Fonts'),
                  '/usr/share/fonts', os.path.expanduser('~/.fonts')]


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def schriften():
    dateien = []
    for o in SCHRIFT_ORDNER:
        for endung in ('ttf', 'otf', 'ttc', 'TTF', 'OTF', 'TTC'):
            dateien += glob.glob(os.path.join(o, '**', '*.' + endung), recursive=True)
    return sorted(set(dateien))


def schrift_finden(name):
    """Pfad zur Schriftdatei: Pfad direkt oder Name (z. B. 'Arial Bold')."""
    if os.path.isfile(os.path.expanduser(name)):
        return os.path.expanduser(name)
    n = _norm(name)
    dateien = schriften()
    basis = {d: _norm(os.path.splitext(os.path.basename(d))[0]) for d in dateien}
    for test in (lambda b: b == n, lambda b: b.startswith(n), lambda b: n in b):
        treffer = sorted((d for d in dateien if test(basis[d])), key=lambda d: len(basis[d]))
        if treffer:
            return treffer[0]
    raise ValueError('Schrift %r nicht gefunden. Vorhanden z. B.: %s' % (
        name, ', '.join(sorted({os.path.splitext(os.path.basename(d))[0]
                                for d in dateien})[:40])))


def _ttc_index(pfad, name):
    """In einer .ttc die Schrift waehlen, deren vollstaendiger Name passt."""
    from fontTools.ttLib import TTCollection
    n = _norm(name)
    besten = (None, 0)
    for i, f in enumerate(TTCollection(pfad).fonts):
        voll = _norm(f['name'].getDebugName(4) or '')
        if voll == n:
            return i
        if n in voll and (besten[0] is None or len(voll) < besten[1]):
            besten = (i, len(voll))
    return besten[0] or 0


def text_formen(text, schrift='Arial', hoehe=None, breite=None,
                zeilenfaktor=1.25, ausrichtung='links', index=None):
    """Text als eine Form (nonzero) in mm, Designrahmen.

    hoehe = Versalhoehe (Hoehe eines 'H') in mm, breite = Breite der Tinte."""
    from fontTools.pens.basePen import BasePen
    from fontTools.ttLib import TTFont

    pfad = schrift_finden(schrift)
    if index is None:
        index = _ttc_index(pfad, schrift) if pfad.lower().endswith('.ttc') else 0
    font = TTFont(pfad, fontNumber=index)
    upm = font['head'].unitsPerEm
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font['hmtx']
    kern = {}
    if 'kern' in font:
        for t in font['kern'].kernTables:
            if hasattr(t, 'kernTable'):
                kern.update(t.kernTable)

    cap = 0
    if 'OS/2' in font and getattr(font['OS/2'], 'sCapHeight', 0):
        cap = font['OS/2'].sCapHeight
    if not cap and ord('H') in cmap:
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(gs)
        gs[cmap[ord('H')]].draw(bp)
        cap = bp.bounds[3] if bp.bounds else 0
    cap = cap or 0.7 * upm

    zeilen = text.split('\n')
    fehlt = sorted({c for c in text if c != '\n' and ord(c) not in cmap})
    if fehlt:
        raise ValueError('Die Schrift %s hat keine Zeichen fuer: %s'
                         % (os.path.basename(pfad), ' '.join(fehlt)))
    breiten = []
    for z in zeilen:
        x, vor = 0, None
        for c in z:
            g = cmap[ord(c)]
            if vor is not None:
                x += kern.get((vor, g), 0)
            x += hmtx[g][0]
            vor = g
        breiten.append(x)
    if hoehe:
        faktor = hoehe / cap
    elif breite:
        faktor = breite / max(1, max(breiten))
    else:
        faktor = 10.0 / cap
    tol = TOL_MM / faktor

    class Stift(BasePen):
        def __init__(self):
            super().__init__(gs)
            self.zuege, self.zu, self.akt, self.ox, self.oy = [], [], None, 0, 0

        def _p(self, p):
            return [p[0] + self.ox, p[1] + self.oy]

        def _fertig(self, zu):
            if self.akt and len(self.akt) >= 2:
                self.zuege.append(self.akt)
                self.zu.append(zu)
            self.akt = None

        def _moveTo(self, p):
            self._fertig(False)
            self.akt = [self._p(p)]

        def _lineTo(self, p):
            self.akt.append(self._p(p))

        def _curveToOne(self, p1, p2, p3):
            p0 = self.akt[-1]
            self.akt += _kubisch(p0, self._p(p1), self._p(p2), self._p(p3), tol)

        def _qCurveToOne(self, p1, p2):
            p0 = self.akt[-1]
            self.akt += _quadratisch(p0, self._p(p1), self._p(p2), tol)

        def _closePath(self):
            self._fertig(True)

        def _endPath(self):
            self._fertig(False)

    stift = Stift()
    maxb = max(breiten) if breiten else 0
    for i, z in enumerate(zeilen):
        x, vor = 0, None
        if ausrichtung == 'mitte':
            x = (maxb - breiten[i]) / 2.0
        elif ausrichtung == 'rechts':
            x = maxb - breiten[i]
        for c in z:
            g = cmap[ord(c)]
            if vor is not None:
                x += kern.get((vor, g), 0)
            stift.ox, stift.oy = x, -i * zeilenfaktor * upm
            gs[g].draw(stift)
            x += hmtx[g][0]
            vor = g
    if not stift.zuege:
        raise ValueError('Text ergibt keine Linien (nur Leerzeichen?)')
    f = form([np.asarray(z) * faktor for z in stift.zuege], stift.zu, 'dunkel', 'nonzero')
    if breite and not hoehe:
        r = rahmen([f])
        f = skalieren_verschieben([f], breite / (r[1] - r[0]), 0, 0)[0]
    return f, os.path.basename(pfad), index


# ---------------------------------------------------------------- SVG

_ZAHL = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
_EINHEIT_MM = {'mm': 1.0, 'cm': 10.0, 'in': 25.4, 'pt': 25.4 / 72, 'pc': 25.4 / 6,
               'px': 25.4 / 96, '': 25.4 / 96}
_UEBERSPRINGEN = {'defs', 'clipPath', 'mask', 'symbol', 'marker', 'pattern',
                  'metadata', 'title', 'desc', 'style', 'script', 'linearGradient',
                  'radialGradient', 'filter', 'namedview'}
_NAMEN = {'black': 0, 'white': 255, 'red': 54, 'green': 92, 'blue': 18, 'gray': 128,
          'grey': 128, 'silver': 192, 'yellow': 237, 'orange': 180, 'navy': 9,
          'maroon': 27, 'purple': 46, 'lime': 182, 'aqua': 200, 'cyan': 200,
          'fuchsia': 73, 'magenta': 73, 'teal': 91, 'olive': 115, 'brown': 64}


def _laenge_mm(s):
    m = re.match(r'\s*([-+]?[\d.]+(?:[eE][-+]?\d+)?)\s*([a-z%]*)', s or '')
    if not m or m.group(2) == '%':
        return None
    return float(m.group(1)) * _EINHEIT_MM.get(m.group(2), 25.4 / 96)


def _matrix(a, b):
    """a * b fuer 2x3 (a b c d e f wie SVG)."""
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
            a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5])


def _transform(s):
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', s or ''):
        v = [float(x) for x in _ZAHL.findall(args)]
        if name == 'matrix' and len(v) == 6:
            t = tuple(v)
        elif name == 'translate':
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            a = math.radians(v[0])
            t = (math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            if len(v) == 3:
                t = _matrix(_matrix((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == 'skewX':
            t = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == 'skewY':
            t = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            continue
        m = _matrix(m, t)
    return m


def _hell(farbe):
    """'keine', 'dunkel' oder 'hell' fuer eine SVG-Farbe."""
    f = (farbe or '').strip().lower()
    if f in ('none', 'transparent'):
        return 'keine'
    if f.startswith('url('):
        return 'dunkel'
    lum = None
    if f.startswith('#'):
        h = f[1:]
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h[:3])
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        except ValueError:
            lum = None
    elif f.startswith('rgb'):
        v = _ZAHL.findall(f)
        if len(v) >= 3:
            k = [float(x) * (2.55 if '%' in f else 1) for x in v[:3]]
            lum = 0.2126 * k[0] + 0.7152 * k[1] + 0.0722 * k[2]
    elif f in _NAMEN:
        lum = _NAMEN[f]
    if lum is None:
        return 'dunkel'
    return 'dunkel' if lum < 128 else 'hell'


_EIGENSCHAFTEN = ('fill', 'stroke', 'fill-rule', 'display', 'visibility')


def _deklarationen(text):
    aus = {}
    for teil in (text or '').split(';'):
        if ':' in teil:
            k, v = teil.split(':', 1)
            if k.strip() in _EIGENSCHAFTEN:
                aus[k.strip()] = v.replace('!important', '').strip()
    return aus


def _klassen(wurzel):
    """Einfache CSS-Klassen aus <style> (.cls-1{fill:#fff}), wie Illustrator sie schreibt."""
    regeln = {}
    for el in wurzel.iter():
        if el.tag.split('}')[-1] != 'style' or not el.text:
            continue
        text = re.sub(r'/\*.*?\*/', '', el.text, flags=re.S)
        for auswahl, inhalt in re.findall(r'([^{}]+)\{([^}]*)\}', text):
            dekl = _deklarationen(inhalt)
            for sel in auswahl.split(','):
                sel = sel.strip()
                if re.match(r'^\.[\w-]+$', sel):
                    regeln.setdefault(sel[1:], {}).update(dekl)
    return regeln


def _stil(el, erbe, klassen=None):
    """Erbt, dann Attribute, dann CSS-Klassen, dann style= (wie im Browser)."""
    s = dict(erbe)
    for k in _EIGENSCHAFTEN:
        if el.get(k) is not None:
            s[k] = el.get(k)
    for k in (el.get('class') or '').split():
        s.update((klassen or {}).get(k, {}))
    s.update(_deklarationen(el.get('style')))
    return s


class _Leser:
    def __init__(self, d):
        self.d, self.i = d, 0

    def _ws(self):
        while self.i < len(self.d) and self.d[self.i] in ' \t\r\n,':
            self.i += 1

    def befehl(self):
        self._ws()
        if self.i < len(self.d) and self.d[self.i] in 'MmLlHhVvCcSsQqTtAaZz':
            self.i += 1
            return self.d[self.i - 1]
        return None

    def hat_zahl(self):
        self._ws()
        return self.i < len(self.d) and self.d[self.i] in '+-.0123456789'

    def zahl(self):
        self._ws()
        m = _ZAHL.match(self.d, self.i)
        if not m:
            raise ValueError('SVG-Pfad nicht lesbar bei %r' % self.d[self.i:self.i + 20])
        self.i = m.end()
        return float(m.group())

    def flag(self):
        self._ws()
        c = self.d[self.i:self.i + 1]
        if c not in ('0', '1'):
            raise ValueError('SVG-Bogen: Flag erwartet bei %r' % self.d[self.i:self.i + 20])
        self.i += 1
        return int(c)


def _pfad(d, tol):
    """SVG-Pfad -> Liste (punkte, geschlossen) in lokalen Einheiten."""
    le = _Leser(d)
    zuege, akt = [], None
    x = y = sx = sy = 0.0
    letzte_k = letzte_q = None
    cmd = None

    def fertig(zu):
        nonlocal akt
        if akt and len(akt) >= 2:
            zuege.append((akt, zu))
        akt = None

    while True:
        c = le.befehl()
        if c is None:
            if le.i >= len(le.d):
                break
            if cmd is None or not le.hat_zahl():
                raise ValueError('SVG-Pfad nicht lesbar bei %r' % le.d[le.i:le.i + 20])
            c = {'M': 'L', 'm': 'l'}.get(cmd, cmd)
        cmd = c
        rel = c.islower()
        C = c.upper()
        if C == 'Z':
            if akt:
                akt.append([sx, sy])
            fertig(True)
            x, y = sx, sy
            letzte_k = letzte_q = None
            continue
        if C == 'M':
            nx, ny = le.zahl(), le.zahl()
            if rel:
                nx, ny = nx + x, ny + y
            fertig(False)
            x, y, sx, sy = nx, ny, nx, ny
            akt = [[x, y]]
            letzte_k = letzte_q = None
            continue
        if akt is None:
            akt = [[x, y]]
            sx, sy = x, y
        if C in 'LHV':
            if C == 'L':
                nx, ny = le.zahl(), le.zahl()
                if rel:
                    nx, ny = nx + x, ny + y
            elif C == 'H':
                nx = le.zahl() + (x if rel else 0)
                ny = y
            else:
                ny = le.zahl() + (y if rel else 0)
                nx = x
            akt.append([nx, ny])
            x, y = nx, ny
            letzte_k = letzte_q = None
        elif C in 'CS':
            if C == 'C':
                x1, y1 = le.zahl(), le.zahl()
                if rel:
                    x1, y1 = x1 + x, y1 + y
            else:
                x1, y1 = (2 * x - letzte_k[0], 2 * y - letzte_k[1]) if letzte_k else (x, y)
            x2, y2, nx, ny = le.zahl(), le.zahl(), le.zahl(), le.zahl()
            if rel:
                x2, y2, nx, ny = x2 + x, y2 + y, nx + x, ny + y
            akt += _kubisch((x, y), (x1, y1), (x2, y2), (nx, ny), tol)
            letzte_k, letzte_q = (x2, y2), None
            x, y = nx, ny
        elif C in 'QT':
            if C == 'Q':
                x1, y1 = le.zahl(), le.zahl()
                if rel:
                    x1, y1 = x1 + x, y1 + y
            else:
                x1, y1 = (2 * x - letzte_q[0], 2 * y - letzte_q[1]) if letzte_q else (x, y)
            nx, ny = le.zahl(), le.zahl()
            if rel:
                nx, ny = nx + x, ny + y
            akt += _quadratisch((x, y), (x1, y1), (nx, ny), tol)
            letzte_q, letzte_k = (x1, y1), None
            x, y = nx, ny
        elif C == 'A':
            rx, ry, phi = le.zahl(), le.zahl(), le.zahl()
            fa, fs = le.flag(), le.flag()
            nx, ny = le.zahl(), le.zahl()
            if rel:
                nx, ny = nx + x, ny + y
            akt += _bogen(x, y, rx, ry, phi, fa, fs, nx, ny, tol)
            x, y = nx, ny
            letzte_k = letzte_q = None
    fertig(False)
    return zuege


def _ellipse(cx, cy, rx, ry, tol):
    r = max(rx, ry)
    n = int(min(720, max(12, math.ceil(math.pi / math.acos(max(-1.0, 1 - tol / r))))))
    t = np.linspace(0, 2 * math.pi, n + 1)
    return np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)]).tolist()


def _element(tag, el, tol):
    def g(k, std=0.0):
        v = _ZAHL.findall(el.get(k) or '')
        return float(v[0]) if v else std

    if tag == 'path':
        return _pfad(el.get('d', ''), tol)
    if tag == 'rect':
        x, y, w, h = g('x'), g('y'), g('width'), g('height')
        if w <= 0 or h <= 0:
            return []
        rx = g('rx', -1)
        ry = g('ry', -1)
        rx = ry if rx < 0 else rx
        ry = rx if ry < 0 else ry
        rx, ry = min(max(rx, 0), w / 2), min(max(ry, 0), h / 2)
        if rx <= 0 or ry <= 0:
            return [([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], True)]
        d = ('M%f,%f H%f A%f,%f 0 0 1 %f,%f V%f A%f,%f 0 0 1 %f,%f H%f '
             'A%f,%f 0 0 1 %f,%f V%f A%f,%f 0 0 1 %f,%f Z' % (
                 x + rx, y, x + w - rx, rx, ry, x + w, y + ry, y + h - ry, rx, ry,
                 x + w - rx, y + h, x + rx, rx, ry, x, y + h - ry, y + ry, rx, ry, x + rx, y))
        return _pfad(d, tol)
    if tag == 'circle':
        r = g('r')
        return [(_ellipse(g('cx'), g('cy'), r, r, tol), True)] if r > 0 else []
    if tag == 'ellipse':
        rx, ry = g('rx'), g('ry')
        return [(_ellipse(g('cx'), g('cy'), rx, ry, tol), True)] if rx > 0 and ry > 0 else []
    if tag == 'line':
        return [([[g('x1'), g('y1')], [g('x2'), g('y2')]], False)]
    if tag in ('polyline', 'polygon'):
        v = [float(z) for z in _ZAHL.findall(el.get('points', ''))]
        pts = [[v[i], v[i + 1]] for i in range(0, len(v) - 1, 2)]
        if len(pts) < 2:
            return []
        if tag == 'polygon':
            return [(pts + [pts[0]], True)]
        return [(pts, False)]
    return None


def svg_lesen(pfad, tol_mm=TOL_MM, mm_je_einheit_ziel=None):
    """SVG -> (Formen in mm, Hinweise). Designrahmen: y nach oben.

    mm_je_einheit_ziel: spaetere Skalierung (mm je SVG-Einheit), damit die
    Kurven fein genug aufgeloest werden; None = Originalgroesse."""
    baum = ET.parse(pfad)
    wurzel = baum.getroot()
    hinweise = []
    vb = [float(v) for v in _ZAHL.findall(wurzel.get('viewBox', ''))]
    breite_mm = _laenge_mm(wurzel.get('width'))
    if len(vb) == 4 and vb[2] > 0 and breite_mm:
        mm_je = breite_mm / vb[2]
    else:
        mm_je = 25.4 / 96       # ohne viewBox oder width: Einheiten sind px
    skala_ziel = mm_je_einheit_ziel or mm_je
    formen = []
    zaehler = {'text': 0, 'image': 0, 'use': 0}
    klassen = _klassen(wurzel)

    def gehe(el, m, stil):
        tag = el.tag.split('}')[-1]
        if tag in _UEBERSPRINGEN:
            return
        s = _stil(el, stil, klassen)
        if s.get('display') == 'none' or s.get('visibility') == 'hidden':
            return
        m = _matrix(m, _transform(el.get('transform')))
        if tag in zaehler:
            zaehler[tag] += 1
            return
        det = abs(m[0] * m[3] - m[1] * m[2]) ** 0.5 or 1.0
        tol = tol_mm / skala_ziel / det
        zuege = _element(tag, el, tol)
        if zuege is not None:
            if zuege:
                fill = _hell(s.get('fill', 'black'))
                arr = []
                for pts, zu in zuege:
                    a = np.asarray(pts, float)
                    xy = np.column_stack([m[0] * a[:, 0] + m[2] * a[:, 1] + m[4],
                                          m[1] * a[:, 0] + m[3] * a[:, 1] + m[5]])
                    arr.append(xy)
                f = form(arr, [zu for _, zu in zuege],
                         None if fill == 'keine' else fill,
                         'evenodd' if s.get('fill-rule') == 'evenodd' else 'nonzero')
                f['strich'] = _hell(s.get('stroke', 'none')) != 'keine'
                formen.append(f)
            return
        for kind in el:
            gehe(kind, m, s)

    gehe(wurzel, (1, 0, 0, 1, 0, 0), {})
    for k, n in zaehler.items():
        if n:
            hinweise.append('%d <%s> ignoriert%s' % (
                n, k, {'text': ' (Text in Inkscape: Pfad > Objekt in Pfad)',
                       'image': ' (eingebettete Bilder: mit "bild" gravieren)',
                       'use': ' (Klone: in Inkscape Bearbeiten > Klon > Verknuepfung loesen)'}[k]))
    # SVG-y zeigt nach unten -> spiegeln, in mm umrechnen
    formen = abbilden(formen, lambda z: np.column_stack([z[:, 0] * mm_je, -z[:, 1] * mm_je]))
    return formen, hinweise, mm_je
