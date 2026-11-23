"""Bilder fuer gravur.py: Schwellwert, Dithern, Graustufen, Linienbild.

Ergebnis ist eine Matrix S[j, i] (Zeile j = 0 hinten/oben im Bild), je
Pixel die Leistung 0..1000; ein Pixel ist intervall x intervall mm gross.
"""

import numpy as np
from PIL import Image, ImageOps


def laden(pfad, zuschneiden=True):
    """Graustufenbild 0..1 (1 = weiss). Transparenz wird weiss, Handyfotos
    werden nach EXIF gedreht, weisse Raender abgeschnitten."""
    img = ImageOps.exif_transpose(Image.open(pfad))
    if img.mode in ('RGBA', 'LA', 'PA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGBA')
        weiss = Image.new('RGBA', img.size, (255, 255, 255, 255))
        weiss.alpha_composite(img)
        img = weiss
    g = img.convert('L')
    if zuschneiden:
        box = g.point(lambda v: 255 if v < 245 else 0).getbbox()
        if box:
            g = g.crop(box)
    return g


def zuschnitt(g, breite=None, hoehe=None, intervall=0.1, drehen=0, spiegeln=False):
    """Dreht/spiegelt und rechnet auf das Pixelraster um. Gibt (L, b, h)."""
    if spiegeln:
        g = ImageOps.mirror(g)
    if drehen % 360:
        g = g.rotate(drehen % 360, expand=True, fillcolor=255)
    w, h = g.size
    if breite and hoehe:
        k = min(breite / w, hoehe / h)
    elif breite:
        k = breite / w
    elif hoehe:
        k = hoehe / h
    else:
        raise ValueError('Bild: --breite oder --hoehe in mm angeben')
    nx = max(1, int(round(w * k / intervall)))
    ny = max(1, int(round(h * k / intervall)))
    g = g.resize((nx, ny), Image.LANCZOS)
    return np.asarray(g, dtype=float) / 255.0, nx * intervall, ny * intervall


def anpassen(L, autokontrast=True, gamma=1.0, invertieren=False):
    """Dunkelheit 0..1 (1 = schwarz)."""
    d = 1.0 - L
    if invertieren:
        d = 1.0 - d
    if autokontrast:
        lo, hi = np.percentile(d, [1, 99])
        if hi - lo > 0.05:
            d = np.clip((d - lo) / (hi - lo), 0, 1)
    if gamma != 1.0:
        d = d ** gamma
    return d


def schwellwert(d, schwelle=0.5):
    return d >= schwelle


def dithern(d):
    """Floyd-Steinberg, schlangenfoermig. Gibt bool (True = brennen)."""
    h, w = d.shape
    a = d.tolist()
    aus = np.zeros((h, w), bool)
    for y in range(h):
        zeile = a[y]
        naechste = a[y + 1] if y + 1 < h else None
        if y % 2 == 0:
            xs, s = range(w), 1
        else:
            xs, s = range(w - 1, -1, -1), -1
        for x in xs:
            alt = zeile[x]
            neu = 1.0 if alt >= 0.5 else 0.0
            if neu:
                aus[y, x] = True
            e = alt - neu
            if 0 <= x + s < w:
                zeile[x + s] += e * 0.4375
            if naechste is not None:
                if 0 <= x - s < w:
                    naechste[x - s] += e * 0.1875
                naechste[x] += e * 0.3125
                if 0 <= x + s < w:
                    naechste[x + s] += e * 0.0625
    return aus


def linienbild(L, intervall, detail=0.4, staerke=1.0, dunkel=0.0, min_flaeche=0.03):
    """Linienzeichnung aus einem Foto (Differenz zweier Gauss-Filter).

    detail: Linienbreite in mm (groesser = weniger, kraeftigere Linien),
    staerke: Schwelle (groesser = weniger Linien), dunkel: Flaechen dunkler
    als dieser Wert (0..1) zusaetzlich fuellen, min_flaeche: Fleckchen unter
    so vielen mm^2 entfernen."""
    from scipy import ndimage
    s = max(0.7, detail / intervall / 2.0)
    g1 = ndimage.gaussian_filter(L, s)
    g2 = ndimage.gaussian_filter(L, 1.6 * s)
    dog = g1 - g2
    t = staerke * 0.6 * float(np.std(dog))
    linien = dog < -t
    if dunkel > 0:
        linien |= ndimage.gaussian_filter(L, s) < dunkel
    marken, n = ndimage.label(linien)
    if n:
        groessen = ndimage.sum(linien, marken, range(1, n + 1))
        klein = np.nonzero(groessen < max(1.0, min_flaeche / (intervall * intervall)))[0] + 1
        linien[np.isin(marken, klein)] = False
    return linien


def graustufen(d, s_min, s_max, stufen=16, aus_unter=0.04):
    st = np.round(d * (stufen - 1)) / (stufen - 1)
    S = s_min + st * (s_max - s_min)
    S[d < aus_unter] = 0
    return np.round(S).astype(int)


def zeilen(S, x0, y0, p):
    """Matrix -> [(y, [(xa, xb, s), ...])], hinten zuerst."""
    ny, nx = S.shape
    aus = []
    for j in range(ny):
        r = S[j]
        if not (r > 0).any():
            continue
        wechsel = np.flatnonzero(np.diff(r) != 0) + 1
        anf = np.r_[0, wechsel]
        end = np.r_[wechsel, nx]
        segs = [(x0 + a * p, x0 + e * p, int(r[a])) for a, e in zip(anf, end) if r[a] > 0]
        aus.append((y0 + (ny - j - 0.5) * p, segs))
    return aus
