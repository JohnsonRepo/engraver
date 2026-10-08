#!/usr/bin/env python3
"""STL-Dateien zum Drucken, ohne Fusion: Haube des Elektronik-Gehaeuses
(fusion/Elektronik, Rev. 3) und Kabelhalter (fusion/Kabelhalter).

Die Geometrie entsteht aus denselben Massen wie in Fusion — lage() der
Skripte wird mit gestubbtem adsk-Modul importiert — und wird hier mit
manifold3d (Boolesche Operationen auf Dreiecksnetzen) nachgebaut, Schritt
fuer Schritt wie bau_deckel() bzw. bau_halter(). Massgeblich bleibt das
Fusion-Modell; die Pruefung am Ende vergleicht Bauraum und Volumen.

Beide Teile liegen schon in Drucklage, die Auflage bei z = 0, mit der Fase
gegen den Elefantenfuss (0,4 mm, in vier Stufen):
  Haube       Oberseite aufs Bett, Waende und Lippe nach oben
  Kabelhalter Querschnitt flach, die 16 mm Breite nach oben, die Spitze der
              Traene oben

    pip install manifold3d
    python3 tools/stl_export.py        ->  stl/*.stl
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


def segmente(d):
    return max(24, int(math.ceil(math.pi * d / SEHNE)))


def quader(x, y, z):
    """Achsparalleler Quader aus drei Bereichen (mm)."""
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate(
        [x[0], y[0], z[0]])


def zylinder_z(mitte, d, z):
    """Senkrechter Zylinder Ø d, mitte = (x, y), z = (unten, oben)."""
    return Manifold.cylinder(z[1] - z[0], d / 2.0, -1.0,
                             segmente(d)).translate([mitte[0], mitte[1],
                                                     z[0]])


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


# ---- Haube des Elektronik-Gehaeuses ----------------------------------------
def haube(em):
    """Wie bau_deckel() in Elektronik.py (Rev. 3), in Maschinen-
    koordinaten; danach um 180 Grad um X gedreht: Oberseite aufs Bett."""
    w, L = em.w, em.lage()
    dz, hz, lz = L['deckel_z'], L['haube_z'], L['lippe_z']
    sp, lb = w('lippe_spiel'), w('lippe_b')
    ix = (L['innen_x'][0] + sp, L['innen_x'][1] - sp)
    iy = (L['innen_y'][0] + sp, L['innen_y'][1] - sp)
    innen_lippe = ((ix[0] + lb, ix[1] - lb), (iy[0] + lb, iy[1] - lb))
    teile = [quader(L['deckel_x'], L['geh_y'], dz)]
    if dz[0] - hz[0] > 1e-6:
        teile.append(quader(L['geh_x'], L['geh_y'], (hz[0], dz[0]))
                     - quader(L['innen_x'], L['innen_y'],
                              (hz[0] - 1.0, dz[0] + 1.0)))
        zr = (hz[0], hz[0] + w('haube_ring'))
        teile.append(quader(L['innen_x'], L['innen_y'], zr)
                     - quader(*innen_lippe, (zr[0] - 1.0, zr[1] + 1.0)))
        teile += [zylinder_z(m, w('haube_dom_d'), (hz[0], dz[0]))
                  for m in L['dome']]
    teile.append(quader(ix, iy, lz)
                 - quader(*innen_lippe, (lz[0] - 1.0, lz[1] + 1.0)))
    k = vereinen(teile)
    weg = [zylinder_z(m, w('m3_durchgang'), (lz[0] - 1.0, dz[1] + 1.0))
           for m in L['dome']]
    if dz[0] - hz[0] > 1e-6:
        weg += [zylinder_z(m, w('haube_kanal_d'),
                           (hz[0] + w('haube_boden'), dz[1] + 1.0))
                for m in L['dome']]
    fm = L['luefter_mitte']
    weg.append(zylinder_z(fm, w('luefter_d'), (dz[0] - 1.0, dz[1] + 1.0)))
    k = k - vereinen(weg)
    r, g = w('luefter_d') / 2.0 + 0.5, w('gitter_b') / 2.0
    k = vereinen([k, quader((fm[0] - r, fm[0] + r), (fm[1] - g, fm[1] + g),
                            dz),
                  quader((fm[0] - g, fm[0] + g), (fm[1] - r, fm[1] + r),
                         dz)])
    k = k - vereinen([zylinder_z(m, w('m3_durchgang'),
                                 (dz[0] - 1.0, dz[1] + 1.0))
                      for m in L['luefter_loecher']])
    # Drucklage: (X, Y, Z) -> (X - x0, y1 - Y, z_oben - Z)
    k = k.transform([[1, 0, 0, -L['deckel_x'][0]],
                     [0, -1, 0, L['geh_y'][1]],
                     [0, 0, -1, dz[1]]])
    soll = (L['deckel_x'][1] - L['deckel_x'][0], L['geh_y'][1] - L['geh_y'][0],
            dz[1] - lz[0])
    return fussfase(k, w('fase_fuss')), soll


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


def main():
    em = bauraum.modul_laden(os.path.join(FUSION, 'Elektronik',
                                          'Elektronik.py'), 'elektronik')
    km = bauraum.modul_laden(os.path.join(FUSION, 'Kabelhalter',
                                          'Kabelhalter.py'), 'kabelhalter')
    os.makedirs(ZIEL, exist_ok=True)
    fehler = 0
    for name, (teil, soll), material in (
            ('Elektronik_Deckel_r{}'.format(em.REVISION), haube(em), 'PETG'),
            ('Kabelhalter_r{}'.format(km.REVISION), kabelhalter(km),
             'PETG')):
        bb = teil.bounding_box()
        ist = tuple(bb[3 + i] - bb[i] for i in range(3))
        gut = (teil.status().name == 'NoError' and teil.genus() >= 0
               and all(abs(a - b) < 0.01 for a, b in zip(ist, soll))
               and abs(bb[2]) < 1e-6)
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
    sys.exit(main())
