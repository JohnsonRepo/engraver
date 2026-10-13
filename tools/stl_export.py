#!/usr/bin/env python3
"""STL-Dateien zum Drucken, ohne Fusion: die vier Teile des Elektronikfachs
(fusion/Elektronikfach) und der Kabelhalter (fusion/Kabelhalter).

Die Geometrie entsteht aus denselben Massen wie in Fusion — lage() der
Skripte wird mit gestubbtem adsk-Modul importiert. Das Elektronikfach
bringt seinen Bauplan mit (Schritte aus Quadern, Zylindern, Vielecken und
Traenen); hier fuehrt ihn manifold3d (Boolesche Operationen auf
Dreiecksnetzen) Schritt fuer Schritt aus, wie plan_bauen() in Fusion. Der
Kabelhalter wird wie bau_halter() nachgebaut. Massgeblich bleibt das
Fusion-Modell; die Pruefung am Ende vergleicht den Bauraum.

Alle Teile liegen schon in Drucklage, die Auflage bei z = 0, mit der Fase
gegen den Elefantenfuss (0,4 mm, in vier Stufen):
  Fach links/rechts  auf dem Boden, Waende, Platte und Ohr senkrecht
  Deckel links/rechts Oberseite aufs Bett, Lippe nach oben
  Kabelhalter        Querschnitt flach, die 16 mm Breite nach oben, die
                     Spitze der Traene oben

    pip install manifold3d
    python3 tools/stl_export.py               ->  stl/*.stl
    python3 tools/stl_export.py Elektronikfach  ->  nur das Fach
"""

import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402

try:
    from manifold3d import CrossSection, JoinType, Manifold, OpType
except ImportError:                                   # pragma: no cover
    sys.exit('manifold3d fehlt: pip install manifold3d')

HIER = os.path.dirname(os.path.abspath(__file__))
FUSION = os.path.join(HIER, '..', 'fusion')
ZIEL = os.path.join(HIER, '..', 'stl')
SEHNE = 0.4            # Kreise: hoechstens so lange Sehnen (mm)
FASE_STUFEN = 4
BETT = 250.0           # Bambu Lab A1: 256, mit Rand


def segmente(d):
    return max(24, int(math.ceil(math.pi * d / SEHNE)))


def quader(x, y, z):
    """Achsparalleler Quader aus drei Bereichen (mm)."""
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate(
        [x[0], y[0], z[0]])


def prisma_y(punkte_xz, y):
    """Vieleck in (X, Z) entlang Y von y[0] bis y[1]. Gedreht, nicht
    gespiegelt: lokal (u, v, w) -> (X, Y, Z) = (u, y0 + w, -v)."""
    q = vieleck([(x, -z) for x, z in punkte_xz])
    return Manifold.extrude(q, y[1] - y[0]).transform(
        [[1, 0, 0, 0], [0, 0, 1, y[0]], [0, -1, 0, 0]])


def vieleck(punkte):
    """CrossSection aus einem Linienzug, gegen den Uhrzeigersinn."""
    s = sum(a0 * b1 - a1 * b0 for (a0, b0), (a1, b1)
            in zip(punkte, punkte[1:] + punkte[:1]))
    return CrossSection([punkte if s > 0 else punkte[::-1]])


def vereinen(teile):
    return Manifold.batch_boolean(list(teile), OpType.Add) if len(teile) > 1 \
        else teile[0]


def fussfase(teil, fase):
    """Fase gegen den Elefantenfuss an der Auflage z = 0: Die unteren
    `fase` mm werden durch Schnitte ersetzt, die nach unten um bis zu
    `fase` schmaler werden (Stufen, je Schicht die Mitte der Fase). Gilt
    fuer Teile, deren Unterseite auf dieser Hoehe prismatisch ist."""
    schnitt = teil.slice(min(0.1, fase / 2.0))
    x0, y0, _, x1, y1, _ = teil.bounding_box()
    rest = teil - quader((x0 - 1, x1 + 1), (y0 - 1, y1 + 1), (-1.0, fase))
    h = fase / FASE_STUFEN
    lagen = [rest]
    for i in range(FASE_STUFEN):
        d = fase - (i + 0.5) * h
        lagen.append(Manifold.extrude(
            schnitt.offset(-d, JoinType.Miter, 2.0), h).translate(
                [0, 0, i * h]))
    return vereinen(lagen)


# ---- Elektronikfach: Bauplan aus Elektronikfach.py ---------------------------
def prisma(achse, punkte, a0, a1):
    """Vieleck in der Ebene quer zu `achse`, entlang `achse` von a0 bis a1.
    (u, v) wie im Bauplan: (X, Y) fuer 'z', (X, Z) fuer 'y', (Y, Z) fuer
    'x'. Gedreht, nie gespiegelt."""
    if achse == 'z':
        return Manifold.extrude(vieleck(punkte), a1 - a0).translate(
            [0.0, 0.0, a0])
    if achse == 'y':
        return prisma_y(punkte, (a0, a1))
    # lokal (u, v, w) -> (X, Y, Z) = (a0 + w, u, v)
    return Manifold.extrude(vieleck(punkte), a1 - a0).transform(
        [[0, 0, 1, a0], [1, 0, 0, 0], [0, 1, 0, 0]])


def schritt_umrisse(fm, s):
    """Die Formen eines Bauplan-Schritts als Vielecke in (u, v)."""
    f = s['form']
    if f == 'rechteck':
        return [[(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
                for u0, v0, u1, v1 in s['formen']]
    if f == 'kreis':
        r, n = s['d'] / 2.0, segmente(s['d'])
        return [[(u + r * math.cos(2.0 * math.pi * i / n),
                  v + r * math.sin(2.0 * math.pi * i / n)) for i in range(n)]
                for u, v in s['formen']]
    if f == 'vieleck':
        return [list(p) for p in s['formen']]
    if f == 'tropfen':
        return [fm.tropfen_punkte(u, v, s['d'], s['spitze'], s.get('kappe'),
                                  SEHNE) for u, v in s['formen']]
    raise ValueError('unbekannte Form ' + f)


def plan_ausfuehren(fm, plan):
    """Wie plan_bauen() in Elektronikfach.py: der erste Schritt legt den
    Koerper an, danach vereinen ('dazu') bzw. schneiden ('weg') in der
    Reihenfolge des Plans; gleiche Schritte am Stueck in einem Rutsch."""
    k, i = None, 0
    while i < len(plan):
        art, j = plan[i]['art'], i
        stueck = []
        while j < len(plan) and plan[j]['art'] == art:
            stueck += [prisma(plan[j]['achse'], p, *plan[j]['a'])
                       for p in schritt_umrisse(fm, plan[j])]
            j += 1
        b = vereinen(stueck)
        k = b if k is None else (k + b if art == 'dazu' else k - b)
        i = j
    return k


def fach_teil(fm, name):
    """Ein Teil des Elektronikfachs in Drucklage, dazu der Soll-Bauraum."""
    L = fm.lage()
    T = L['teile'][name]
    k = plan_ausfuehren(fm, L['plan'][name]).transform(T['druck'])
    (x0, x1), (y0, y1), (z0, z1) = T['bbox']
    return fussfase(k, fm.w('fase_fuss')), (x1 - x0, y1 - y0, z1 - z0)


# ---- Kabelhalter ------------------------------------------------------------
def kabelhalter(km):
    """Wie bau_halter() in Kabelhalter.py, gleich in Drucklage:
    x = a (vom 2040 weg), y = z (ueber der Nutmitte), z = 0 .. kh_b
    (Maschine Y, die Seite bei Y-Anfang liegt auf dem Bett)."""
    w, L = km.w, km.lage()
    b = w('kh_b')
    k = Manifold.extrude(vieleck(list(L['querschnitt'])), b)
    # Traene: Achse entlang x, Spitze nach +z (beim Druck oben)
    r, c = w('m5_durchgang') / 2.0, b / 2.0
    n = segmente(w('m5_durchgang'))
    bogen = [(r * math.cos(t), c + r * math.sin(t))
             for t in (math.radians(135.0 + 270.0 * i / n)
                       for i in range(n + 1))]
    traene = vieleck(bogen + [(0.0, c + r * math.sqrt(2.0))])
    a0, a1 = -w('feder_t') - 1.0, w('anlage_t') + 1.0
    loch = Manifold.extrude(traene, a1 - a0).transform(
        [[0, 0, 1, a0], [1, 0, 0, 0], [0, 1, 0, 0]])
    ba, hb = L['binder_a'], w('binder_b') / 2.0
    fenster = quader(ba, (L['z'][0] - 1.0, L['kanal_z'][0] + 1.0),
                     (c - hb, c + hb))
    fl, fb = L['feder_luecke'], w('feder_b') / 2.0 + 1.0
    feder_frei = quader((-w('feder_t') - 1.0, 0.0), (-fb, fb),
                        (c - fl, c + fl))
    k = k - loch - fenster - feder_frei
    soll = (L['a'][1] - L['a'][0], L['z'][1] - L['z'][0], b)
    return fussfase(k, w('fase_fuss')), soll


# ---- STL ----------------------------------------------------------------------
def stl_schreiben(pfad, teil, name):
    """Binaere STL, Masse in mm."""
    mesh = teil.to_mesh()
    v = mesh.vert_properties
    dreiecke = mesh.tri_verts
    with open(pfad, 'wb') as f:
        kopf = '{} — engraver, tools/stl_export.py'.format(name).encode(
            'utf-8')[:80]
        f.write(kopf.ljust(80, b' '))
        f.write(struct.pack('<I', len(dreiecke)))
        for i0, i1, i2 in dreiecke:
            p0, p1, p2 = v[i0][:3], v[i1][:3], v[i2][:3]
            u = [p1[j] - p0[j] for j in range(3)]
            t = [p2[j] - p0[j] for j in range(3)]
            nx = u[1] * t[2] - u[2] * t[1]
            ny = u[2] * t[0] - u[0] * t[2]
            nz = u[0] * t[1] - u[1] * t[0]
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            f.write(struct.pack('<12fH', nx / ln, ny / ln, nz / ln,
                                *p0, *p1, *p2, 0))
    return len(dreiecke)


def main(nur=()):
    """Schreibt alle Teile; mit Namen (Anfang genuegt, z. B. Elektronikfach)
    nur diese."""
    fm = bauraum.modul_laden(os.path.join(FUSION, 'Elektronikfach',
                                          'Elektronikfach.py'),
                             'elektronikfach')
    km = bauraum.modul_laden(os.path.join(FUSION, 'Kabelhalter',
                                          'Kabelhalter.py'), 'kabelhalter')
    os.makedirs(ZIEL, exist_ok=True)
    fehler = 0
    teile = [('Elektronikfach_{}_r{}'.format(n, fm.REVISION),
              lambda n=n: fach_teil(fm, n))
             for n in ('Fach_links', 'Fach_rechts', 'Deckel_links',
                       'Deckel_rechts')]
    teile.append(('Kabelhalter_r{}'.format(km.REVISION),
                  lambda: kabelhalter(km)))
    for name, bauen in teile:
        if nur and not name.startswith(tuple(nur)):
            continue
        teil, soll = bauen()
        material = 'PETG'
        bb = teil.bounding_box()
        ist = tuple(bb[3 + i] - bb[i] for i in range(3))
        gut = (teil.status().name == 'NoError' and teil.genus() >= 0
               and all(abs(a - b) < 0.01 for a, b in zip(ist, soll))
               and abs(bb[2]) < 1e-6 and max(ist) <= BETT)
        fehler += 0 if gut else 1
        pfad = os.path.join(ZIEL, name + '.stl')
        n = stl_schreiben(pfad, teil, name)
        print('{} {}: {:.1f} x {:.1f} x {:.1f} mm (soll {:.1f} x {:.1f} x '
              '{:.1f}), {:.1f} cm3 = {:.0f} g {}, {} Dreiecke, Geschlecht {}'
              .format('OK  ' if gut else 'FEHL', os.path.relpath(pfad),
                      *ist, *soll, teil.volume() / 1000.0,
                      teil.volume() / 1000.0 * 1.27, material, n,
                      teil.genus()))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
