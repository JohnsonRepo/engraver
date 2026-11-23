#!/usr/bin/env python3
"""Gravur: Hanfblatt mit sieben gezahnten Fiedern und Stiel.

Eine Geometrie, vier Dateien in gravur/:

    hanfblatt-linie.svg    Umriss und Adern als Linien   (LightBurn: Line)
    hanfblatt-flaeche.svg  Umriss mit ausgesparten Adern (LightBurn: Fill)
    hanfblatt-linie.gc     G-Code fuer CNCjs/GRBL: Strichgravur
    hanfblatt-flaeche.gc   G-Code fuer CNCjs/GRBL: Flaeche zeilenweise, dann Umriss

Der G-Code bezieht sich auf den Werkstuecknullpunkt G54 an der Innenecke des
Anschlags vorn rechts (docs/spannmittel.md): das Motiv liegt bei X <= 0 und
Y >= 0, die Spitze zeigt nach hinten. Laser mit M4 (dynamisch), S0..1000
($30=1000). Der Vorschub bleibt bei 500 mm/min, solange $110/$111 auf dem
GRBL-Standard stehen: GRBL begrenzt einen hoeheren Vorschub, rechnet die
M4-Leistung aber gegen den programmierten Wert, der Laser braennte also zu
schwach.

Das Skript prueft am Ende: Umriss ohne Selbstschnitt, Adern ganz im Blatt
und ohne Ueberlappung, alle Fahrten im Arbeitsfeld, Laser nur im Motiv.
Exit-Code 0 = alles bestanden. Nur Standardbibliothek.

    python3 tools/gravur_hanfblatt.py                  # 80 mm hoch, 10 mm vom Nullpunkt
    python3 tools/gravur_hanfblatt.py --hoehe 60 --abstand 5
"""

import argparse
import math
import os
import sys

WURZEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
AUSGABE = os.path.join(WURZEL, 'gravur')
NAME = 'hanfblatt'

# --- Form, relativ zur Laenge der mittleren Fieder ---------------------------
# Winkel zur Senkrechten (+ = rechts), Laenge, groesste halbe Breite,
# Zaehne je Seite, Biegung der Spitze nach oben. Jede Zeile ausser der
# ersten gilt gespiegelt auch links.
FIEDERN = [
    (0.0, 1.00, 0.100, 19, 0.000),
    (30.0, 0.86, 0.094, 17, 0.030),
    (61.0, 0.64, 0.082, 14, 0.050),
    (97.0, 0.35, 0.062, 9, 0.040),
]
H0 = 0.007           # halbe Breite der Fiedern am Ansatz
FORM_A = 2.20        # Anstieg vom Ansatz (groesser = schlanker Keil)
FORM_B = 2.00        # Abfall zur Spitze (groesser = laengere Spitze)
ZAHN_TIEFE = 0.24    # Zahntiefe als Anteil der halben Breite
ZAHN_VON = 0.13      # Zaehne ab hier (Anteil der Fiederlaenge) ...
ZAHN_BIS = 0.975     # ... bis hier
ZAHN_SPITZE = 0.80   # Lage der Zahnspitze im Zahn: Ruecken kurz und steil
STIEL_L = 0.30       # Stiel: Laenge,
STIEL_B0 = 0.022     # halbe Breite am Blatt,
STIEL_B1 = 0.016     # halbe Breite am Ende,
STIEL_BIEG = 0.06    # Biegung nach rechts

# --- Adern, absolut in mm ----------------------------------------------------
ADER_WINKEL = 36.0   # Seitenader zur Mittelrippe (Grad)
ADER_REICHT = 0.74   # Seitenader endet so weit auf dem Weg zur Zahnspitze
ADER_MIN_HW = 1.1    # keine Seitenader, wo die Fieder schmaler ist (halbe Breite)
RIPPE_ANSATZ = 2.6   # Mittelrippe beginnt so weit vom Blattansatz (Flaeche)
RIPPE_ANSATZ_L = 1.2  # ... als Linie
RIPPE_BIS = 0.90     # Mittelrippe endet hier (Anteil der Fiederlaenge)

# --- Maschine ------------------------------------------------------------------
# Arbeitsfeld in Werkstueckkoordinaten (Nullpunkt an der Innenecke des Anschlags,
# X +183,35 / Y +160,5 in Portal.py, dort zeigt +Y nach vorn): docs/opferplatte.md
FELD_X = (-203.85 - 183.35, 187.35 - 183.35)
FELD_Y = (160.5 - 164.5, 160.5 + 168.8)
GRBL_MAX_F = 500.0   # $110/$111 GRBL-Standard
GRBL_ACC = 10.0      # $120/$121 GRBL-Standard, mm/s^2
GRBL_JD = 0.010      # $11 GRBL-Standard, mm


# =============================================================================
# Geometrie
# =============================================================================

def form(s):
    """Breitenverlauf 0..1..0, Maximum 1 bei s = A/(A+B)."""
    if s <= 0.0 or s >= 1.0:
        return 0.0
    sm = FORM_A / (FORM_A + FORM_B)
    return (s / sm) ** FORM_A * ((1.0 - s) / (1.0 - sm)) ** FORM_B


class Glied:
    """Eine Fieder oder der Stiel: Mittellinie s = 0..1 (Ansatz..Spitze),
    Punkte als (s, n) mit n quer dazu in mm, + = links der Laufrichtung."""

    def __init__(self, winkel, laenge, biegung, nach_rechts=False):
        a = math.radians(winkel)
        self.L = laenge
        self.d = (math.sin(a), math.cos(a))
        links = (-self.d[1], self.d[0])
        if nach_rechts:
            self.auf = links if links[0] >= 0 else (-links[0], -links[1])
        else:
            self.auf = links if links[1] >= 0 else (-links[0], -links[1])
        self.b = biegung
        self.math_winkel = math.degrees(math.atan2(self.d[1], self.d[0])) % 360.0

    def xy(self, s, n=0.0):
        L, d, u, b = self.L, self.d, self.auf, self.b
        px = s * L * d[0] + b * L * s * s * u[0]
        py = s * L * d[1] + b * L * s * s * u[1]
        tx = L * d[0] + 2.0 * b * L * s * u[0]
        ty = L * d[1] + 2.0 * b * L * s * u[1]
        t = math.hypot(tx, ty)
        return (px - n * ty / t, py + n * tx / t)


class Fieder(Glied):
    def __init__(self, winkel, laenge, hw_max, zaehne, biegung):
        super().__init__(winkel, laenge, biegung)
        self.hw_max = hw_max
        self.zaehne = zaehne
        self.spitzen = []          # (s, n) der Zahnspitzen, n > 0
        self.rand = self._rand()   # (s, n) eine Seite, Ansatz..Spitze, n > 0

    def hw(self, s):
        """Halbe Breite in mm an der Stelle s (Zahnspitzenlinie)."""
        return self.L * (H0 * (1.0 - s) + self.hw_max * form(s))

    def _rand(self):
        tal = 1.0 - ZAHN_TIEFE
        pkt = [(ZAHN_VON * i / 8.0, tal * self.hw(ZAHN_VON * i / 8.0))
               for i in range(8)]
        grenzen = [ZAHN_VON + (ZAHN_BIS - ZAHN_VON) * k / self.zaehne
                   for k in range(self.zaehne + 1)]
        for k in range(self.zaehne):
            sa, sb = grenzen[k], grenzen[k + 1]
            sp = sa + ZAHN_SPITZE * (sb - sa)
            pkt.append((sa, tal * self.hw(sa)))
            for u in (0.2, 0.4, 0.6, 0.8, 1.0):         # Flanke gewoelbt, Spitze spitz
                s = sa + u * (sp - sa)
                e = u ** 0.75
                pkt.append((s, self.hw(s) * (tal + ZAHN_TIEFE * e)))
            self.spitzen.append((sp, self.hw(sp)))
        pkt.append((ZAHN_BIS, tal * self.hw(ZAHN_BIS)))
        pkt.append((1.0, 0.0))
        return pkt

    def umriss(self):
        """Rechte Seite Ansatz..Spitze, linke Seite Spitze..Ansatz (xy)."""
        rechts = [self.xy(s, -n) for s, n in self.rand]
        links = [self.xy(s, n) for s, n in reversed(self.rand[:-1])]
        return rechts + links, len(rechts) - 1


class Stiel(Glied):
    def __init__(self, laenge):
        super().__init__(180.0, laenge, STIEL_BIEG, nach_rechts=True)

    def hw(self, s):
        b0, b1 = STIEL_B0 * self.L / STIEL_L, STIEL_B1 * self.L / STIEL_L
        return b0 + (b1 - b0) * s + 0.6 * b0 * (1.0 - s) ** 6   # leicht ausgestellt

    def umriss(self):
        ss = [i / 24.0 for i in range(25)]
        r = self.hw(1.0)
        rechts = [self.xy(s, -self.hw(s)) for s in ss]
        kappe = []
        for i in range(1, 6):                       # Ende flach gerundet
            phi = math.pi * i / 6.0
            kappe.append(self.xy(1.0 + 0.45 * r * math.sin(phi) / self.L,
                                 -r * math.cos(phi)))
        links = [self.xy(s, self.hw(s)) for s in reversed(ss)]
        return rechts + kappe + links, len(rechts) + 2


def blatt(L):
    """Fiedern und Stiel fuer eine mittlere Fiederlaenge L (mm)."""
    fiedern = []
    for w, l, hw, z, b in FIEDERN:
        for vz in ((1,) if w == 0 else (1, -1)):
            fiedern.append(Fieder(vz * w, l * L, hw, z, b))
    stiel = Stiel(STIEL_L * L)
    return fiedern, stiel


# =============================================================================
# Ebene Geometrie
# =============================================================================

def schnitt(p1, p2, p3, p4):
    """Schnitt der Strecken p1p2 und p3p4 -> (t, u) oder None."""
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-12:
        return None
    ex, ey = p3[0] - p1[0], p3[1] - p1[1]
    t = (ex * d2y - ey * d2x) / den
    u = (ex * d1y - ey * d1x) / den
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return t, u
    return None


def vereinigung(glieder):
    """Aeusserer Umriss aller Glieder als ein Polygon (gegen den Uhrzeigersinn).

    Die Glieder stehen wie ein Faecher um den Ansatz. Zwischen zwei
    Nachbarn gilt der aeusserste Schnitt der linken Kante des einen mit der
    rechten Kante des naechsten; dort wechselt der Umriss das Glied."""
    glieder = sorted(glieder, key=lambda g: (g.math_winkel - 260.0) % 360.0)
    umr = [g.umriss() for g in glieder]
    n = len(glieder)
    wechsel = []        # (Parameter im Glied i, Parameter im Glied i+1, Punkt)
    for i in range(n):
        (pa, ka), (pb, kb) = umr[i], umr[(i + 1) % n]
        best = None
        for a in range(ka, len(pa) - 1):
            for b in range(0, kb):
                r = schnitt(pa[a], pa[a + 1], pb[b], pb[b + 1])
                if r is None:
                    continue
                ta = a + r[0]
                if best is None or ta < best[0]:
                    x = pa[a][0] + r[0] * (pa[a + 1][0] - pa[a][0])
                    y = pa[a][1] + r[0] * (pa[a + 1][1] - pa[a][1])
                    best = (ta, b + r[1], (x, y))
            if best is not None and best[0] < a:
                break
        if best is None:
            raise SystemExit('Glieder %d und %d schneiden sich nicht' % (i, i + 1))
        wechsel.append(best)
    poly = []
    for i in range(n):
        p, _ = umr[i]
        von = wechsel[i - 1][1]          # Eintritt auf der rechten Kante
        bis = wechsel[i][0]              # Austritt auf der linken Kante
        poly.append(wechsel[i - 1][2])
        poly.extend(p[int(math.floor(von)) + 1:int(math.floor(bis)) + 1])
    return poly


def flaeche(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]
        x2, y2 = poly[i]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def innen(p, poly):
    x, y = p
    drin = False
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]
        x2, y2 = poly[i]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                drin = not drin
    return drin


def strecken(poly, zu=True):
    m = len(poly) if zu else len(poly) - 1
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(m)]


def schnitte_finden(segs_a, segs_b=None, raster=1.0):
    """Echte Schnitte zwischen Strecken (Nachbarn im selben Zug zaehlen nicht)."""
    eigene = segs_b is None
    if eigene:
        segs_b = segs_a
    zellen = {}
    for j, (p, q) in enumerate(segs_b):
        for cx in range(int(math.floor(min(p[0], q[0]) / raster)),
                        int(math.floor(max(p[0], q[0]) / raster)) + 1):
            for cy in range(int(math.floor(min(p[1], q[1]) / raster)),
                            int(math.floor(max(p[1], q[1]) / raster)) + 1):
                zellen.setdefault((cx, cy), []).append(j)
    treffer = set()
    n = len(segs_a)
    for i, (p, q) in enumerate(segs_a):
        kand = set()
        for cx in range(int(math.floor(min(p[0], q[0]) / raster)),
                        int(math.floor(max(p[0], q[0]) / raster)) + 1):
            for cy in range(int(math.floor(min(p[1], q[1]) / raster)),
                            int(math.floor(max(p[1], q[1]) / raster)) + 1):
                kand.update(zellen.get((cx, cy), ()))
        for j in kand:
            if eigene and (j <= i or j == i + 1 or (i == 0 and j == n - 1)):
                continue
            if schnitt(p, q, segs_b[j][0], segs_b[j][1]) is not None:
                treffer.add((i, j))
    return treffer


# =============================================================================
# Adern
# =============================================================================

def seitenadern(f, ansatz_mm, vz, fremde):
    """Seitenadern zu den Zahnspitzen als ((s, n) Start, (s, n) Ende) in mm,
    Start auf der Mittelrippe, n > 0; vz = +1 links, -1 rechts. Adern, die in
    eine Nachbarfieder (fremde: Umrisse) hineinliefen, entfallen."""
    tan_a = math.tan(math.radians(ADER_WINKEL))
    ende_rippe = RIPPE_BIS * f.L
    adern = []
    for sp, hw in f.spitzen:
        if hw < ADER_MIN_HW:
            continue
        s_spitze = sp * f.L
        s0 = s_spitze - hw / tan_a
        if s0 < ansatz_mm + 0.8 or s0 > ende_rippe - 1.5:
            continue
        se = s0 + ADER_REICHT * (s_spitze - s0)
        ne = min(ADER_REICHT * hw, 0.8 * (1.0 - ZAHN_TIEFE) * f.hw(se / f.L))
        probe = [f.xy((s0 + k * (se - s0)) / f.L, vz * k * ne) for k in (0.3, 0.6, 1.0, 1.25)]
        if any(innen(p, u) for u in fremde for p in probe):
            continue
        adern.append(((s0, 0.0), (se, ne)))
    return adern


def adern_linie(f, fremde):
    """Mittelrippe und Seitenadern als offene Linienzuege (xy)."""
    s0, s1 = RIPPE_ANSATZ_L / f.L, RIPPE_BIS
    rippe = [f.xy(s0 + (s1 - s0) * i / 40.0) for i in range(41)]
    zuege = [rippe]
    for vz in (1, -1):
        for (sa, _), (se, ne) in seitenadern(f, RIPPE_ANSATZ_L, vz, fremde):
            zuege.append([f.xy((sa + (se - sa) * k / 4.0) / f.L, vz * ne * k / 4.0)
                          for k in range(5)])
    return zuege


def adern_flaeche(f, b_rippe, b_ader, fremde):
    """Mittelrippe mit Seitenadern als ein Polygon (Fischgraete, xy)."""
    s0 = RIPPE_ANSATZ
    s1 = RIPPE_BIS * f.L

    def wr(s):                       # halbe Breite der Mittelrippe
        t = min(1.0, max(0.0, (s - s0) / (s1 - s0)))
        frei = 0.35 * (1.0 - ZAHN_TIEFE) * f.hw(s / f.L)   # am Ansatz schmaler
        return min(0.5 * (b_rippe + (0.45 * b_rippe - b_rippe) * t), frei)

    def seite_bauen(vz):
        """(s, n) auf einer Seite, n > 0, Ansatz..Spitze."""
        seite = []
        letzte = s0
        for (sa, _), (se, ne) in seitenadern(f, s0, vz, fremde):
            ux, uy = se - sa, ne
            lg = math.hypot(ux, uy)
            ux, uy = ux / lg, uy / lg
            qx, qy = uy, -ux             # quer zur Ader, zur Spitze hin
            w0, w1 = 0.5 * b_ader, 0.5 * 0.7 * b_ader

            def an_rippe(k):
                # Kante (Spitzenseite k = +1, Ansatzseite -1) trifft den Rand der Rippe
                ax, ay = sa + k * qx * w0, k * qy * w0
                bx, by = se + k * qx * w1, ne + k * qy * w1
                r = wr(sa)
                t = (r - ay) / (by - ay)
                return (ax + t * (bx - ax), r), (bx, by)

            (a1, e1), (a2, e2) = an_rippe(-1), an_rippe(1)
            if a1[0] < letzte + 0.15:     # zu dicht an der vorigen Ader
                continue
            # Rippenrand bis zur Ader in kleinen Schritten (die Fieder ist gebogen)
            schritte = max(1, int((a1[0] - letzte) / 0.8))
            for k in range(1, schritte):
                s = letzte + (a1[0] - letzte) * k / schritte
                seite.append((s, wr(s)))
            spitze = (se + ux * 0.35 * w1, ne + uy * 0.35 * w1)
            seite += [a1, e1, spitze, e2, a2]
            letzte = a2[0]
        schritte = max(1, int((s1 - letzte) / 0.8))
        for k in range(1, schritte + 1):
            s = letzte + (s1 - letzte) * k / schritte
            seite.append((s, wr(s)))
        return seite

    spitze = (s1 + 4.0 * wr(s1), 0.0)
    pkt = [(s0, -wr(s0))]
    pkt += [(s, -n) for s, n in seite_bauen(-1)]
    pkt.append(spitze)
    pkt += [(s, n) for s, n in reversed(seite_bauen(1))]
    pkt.append((s0, wr(s0)))
    return [f.xy(s / f.L, n) for s, n in pkt]


# =============================================================================
# Ausgabe: SVG
# =============================================================================

def svg(pfad, zuege_zu, zuege_offen, kasten, voll):
    x0, y0, x1, y1 = kasten
    w, h = x1 - x0, y1 - y0

    def d(z, zu):
        s = 'M' + ' L'.join('%.3f,%.3f' % (x - x0, y1 - y) for x, y in z)
        return s + (' Z' if zu else '')

    teile = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%.3fmm" height="%.3fmm" '
        'viewBox="0 0 %.3f %.3f">' % (w, h, w, h),
        '<title>Hanfblatt %.1f x %.1f mm</title>' % (w, h),
    ]
    if voll:
        teile.append('<path fill="#000000" fill-rule="evenodd" stroke="#000000" '
                     'stroke-width="0.05" d="%s"/>'
                     % ' '.join(d(z, True) for z in zuege_zu))
    else:
        for z in zuege_zu:
            teile.append('<path fill="none" stroke="#000000" stroke-width="0.15" '
                         'stroke-linejoin="round" d="%s"/>' % d(z, True))
        for z in zuege_offen:
            teile.append('<path fill="none" stroke="#000000" stroke-width="0.15" '
                         'stroke-linecap="round" d="%s"/>' % d(z, False))
    teile.append('</svg>')
    with open(pfad, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(teile) + '\n')


# =============================================================================
# Ausgabe: G-Code
# =============================================================================

def zahl(v):
    s = '%.3f' % v
    s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def kopf(titel, kasten, zeilen):
    x0, y0, x1, y1 = kasten
    return [
        '; ' + titel,
        '; erzeugt von tools/gravur_hanfblatt.py',
        '; Groesse %.1f x %.1f mm, Motiv bei X %.1f .. %.1f, Y %.1f .. %.1f'
        % (x1 - x0, y1 - y0, x0, x1, y0, y1),
        '; Nullpunkt G54 = Innenecke des Anschlags vorn rechts (docs/spannmittel.md)',
        '; Spitze zeigt nach hinten (Y+). Laser M4 dynamisch, S0..1000 ($30=1000)',
    ] + ['; ' + z for z in zeilen] + ['G21', 'G90', 'G54', 'M5']


def zuege_ordnen(zuege, start=(0.0, 0.0)):
    """Naechster-Nachbar-Reihenfolge, Zuege bei Bedarf umgedreht."""
    rest = list(zuege)
    pos, aus = start, []
    while rest:
        best, bi, um = None, 0, False
        for i, z in enumerate(rest):
            for r, p in ((False, z[0]), (True, z[-1])):
                dd = (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2
                if best is None or dd < best:
                    best, bi, um = dd, i, r
        z = rest.pop(bi)
        z = list(reversed(z)) if um else z
        aus.append(z)
        pos = z[-1]
    return aus


def gcode_linien(zuege, f, s):
    out = ['M4 S0', 'G1 F%s' % zahl(f)]
    for z in zuege:
        out.append('G0 X%s Y%s' % (zahl(z[0][0]), zahl(z[0][1])))
        out.append('G1 X%s Y%s S%d' % (zahl(z[1][0]), zahl(z[1][1]), s))
        for x, y in z[2:]:
            out.append('G1 X%s Y%s' % (zahl(x), zahl(y)))
    return out


def zeilen_fuellen(polys, kasten, abstand, mindest=0.05):
    """Gerade-ungerade-Fuellung: je Zeile die Abschnitte (x_von, x_bis)."""
    kanten = []
    for p in polys:
        for (a, b) in strecken(p):
            if a[1] == b[1]:
                continue
            if a[1] > b[1]:
                a, b = b, a
            kanten.append((a[1], b[1], a[0], (b[0] - a[0]) / (b[1] - a[1])))
    kanten.sort()
    _, y0, _, y1 = kasten
    n = int(math.floor((y1 - y0) / abstand))
    rand = 0.5 * ((y1 - y0) - n * abstand)
    zeilen = []
    aktiv, k = [], 0
    for j in range(n + 1):
        y = y0 + rand + j * abstand
        while k < len(kanten) and kanten[k][0] <= y:
            aktiv.append(kanten[k])
            k += 1
        aktiv = [e for e in aktiv if e[1] > y]
        xs = sorted(e[2] + (y - e[0]) * e[3] for e in aktiv if e[0] <= y < e[1])
        abschn = []
        for i in range(0, len(xs) - 1, 2):
            a, b = xs[i], xs[i + 1]
            if abschn and a - abschn[-1][1] < mindest:
                abschn[-1] = (abschn[-1][0], b)
            elif b - a >= mindest:
                abschn.append((a, b))
        if abschn:
            zeilen.append((y, abschn))
    return zeilen


def gcode_flaeche(zeilen, f, s, ueber):
    out = ['M4 S0', 'G1 F%s' % zahl(f)]
    erste = True
    for j, (y, abschn) in enumerate(zeilen):
        vor = j % 2 == 0
        folge = abschn if vor else [(b, a) for a, b in reversed(abschn)]
        rein = folge[0][0] - ueber if vor else folge[0][0] + ueber
        raus = folge[-1][1] + ueber if vor else folge[-1][1] - ueber
        if erste:
            out.append('G0 X%s Y%s' % (zahl(rein), zahl(y)))
            erste = False
        else:
            out.append('G1 X%s Y%s S0' % (zahl(rein), zahl(y)))
        for a, b in folge:
            out.append('G1 X%s S0' % zahl(a))
            out.append('G1 X%s S%d' % (zahl(b), s))
        out.append('G1 X%s S0' % zahl(raus))
    return out


def fahrten(zeilen_gc):
    """G-Code lesen -> Liste (x0, y0, x1, y1, F mm/min, S, schnell)."""
    x = y = 0.0
    f, s, modus, an = GRBL_MAX_F, 0, 0, False
    out = []
    for z in zeilen_gc:
        z = z.split(';')[0].strip()
        if not z:
            continue
        w = {}
        for t in z.split():
            w[t[0]] = float(t[1:])
        if 'G' in w and w['G'] in (0, 1):
            modus = int(w['G'])
        if 'M' in w:
            an = w['M'] in (3, 4)
        if 'F' in w:
            f = w['F']
        if 'S' in w:
            s = w['S']
        if 'X' in w or 'Y' in w:
            nx, ny = w.get('X', x), w.get('Y', y)
            out.append((x, y, nx, ny, f, s if (an and modus == 1) else 0, modus == 0))
            x, y = nx, ny
    return out


def dauer(fahrt):
    """Laufzeit in s mit dem Planer von GRBL (Beschleunigung, Ecken)."""
    segs = []
    for x0, y0, x1, y1, f, _, schnell in fahrt:
        lg = math.hypot(x1 - x0, y1 - y0)
        if lg < 1e-9:
            continue
        v = min(GRBL_MAX_F if schnell else f, GRBL_MAX_F) / 60.0
        segs.append((lg, v, ((x1 - x0) / lg, (y1 - y0) / lg)))
    if not segs:
        return 0.0
    a = GRBL_ACC
    n = len(segs)
    vmax_ein = [0.0] * (n + 1)
    for i in range(1, n):
        u0, u1 = segs[i - 1][2], segs[i][2]
        cos_t = -(u0[0] * u1[0] + u0[1] * u1[1])
        if cos_t > 0.999999:
            vj = 0.0
        elif cos_t < -0.999999:
            vj = 1e9
        else:
            sd2 = math.sqrt(0.5 * (1.0 - cos_t))
            vj = math.sqrt(a * GRBL_JD * sd2 / (1.0 - sd2))
        vmax_ein[i] = min(vj, segs[i - 1][1], segs[i][1])
    v = vmax_ein[:]
    for i in range(n - 1, -1, -1):                     # rueckwaerts
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * a * segs[i][0]))
    for i in range(n):                                 # vorwaerts
        v[i + 1] = min(v[i + 1], math.sqrt(v[i] ** 2 + 2 * a * segs[i][0]))
    t = 0.0
    for i, (lg, vn, _) in enumerate(segs):
        vi, vo = v[i], v[i + 1]
        vp = min(vn, math.sqrt((2 * a * lg + vi * vi + vo * vo) / 2.0))
        d_auf = (vp * vp - vi * vi) / (2 * a)
        d_ab = (vp * vp - vo * vo) / (2 * a)
        t += (vp - vi) / a + (vp - vo) / a + max(0.0, lg - d_auf - d_ab) / vp
    return t


def minuten(t):
    m = int(round(t / 60.0))
    return '%d h %02d min' % (m // 60, m % 60) if m >= 60 else '%d min' % max(1, m)


# =============================================================================
# Hauptprogramm
# =============================================================================

def main():
    global GRBL_MAX_F, GRBL_ACC
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--hoehe', type=float, default=80.0,
                    help='Hoehe des Blatts mit Stiel in mm (80)')
    ap.add_argument('--abstand', type=float, default=10.0,
                    help='Abstand des Motivs vom Nullpunkt in X und Y, mm (10)')
    ap.add_argument('--linie-f', type=float, default=500.0,
                    help='Vorschub Linien und Umriss, mm/min (500)')
    ap.add_argument('--linie-s', type=int, default=600,
                    help='Leistung Linien und Umriss, S0..1000 (600)')
    ap.add_argument('--flaeche-f', type=float, default=500.0,
                    help='Vorschub Flaeche, mm/min (500)')
    ap.add_argument('--flaeche-s', type=int, default=200,
                    help='Leistung Flaeche, S0..1000 (200)')
    ap.add_argument('--zeilen', type=float, default=0.1,
                    help='Zeilenabstand der Flaeche, mm (0,1)')
    ap.add_argument('--ueberlauf', type=float, default=2.0,
                    help='Ueberlauf der Zeilen mit Laser aus, mm (2)')
    ap.add_argument('--rippe', type=float, default=0.8,
                    help='Breite der Mittelrippe am Ansatz (Flaeche), mm (0,8)')
    ap.add_argument('--ader', type=float, default=0.45,
                    help='Breite der Seitenadern (Flaeche), mm (0,45)')
    ap.add_argument('--max-f', type=float, default=GRBL_MAX_F,
                    help='$110/$111 der Maschine, mm/min (500, GRBL-Standard)')
    ap.add_argument('--beschl', type=float, default=GRBL_ACC,
                    help='$120/$121 der Maschine, mm/s^2 (10, GRBL-Standard), fuer die Laufzeit')
    arg = ap.parse_args()
    GRBL_MAX_F, GRBL_ACC = arg.max_f, arg.beschl

    # Groesse: erst mit L = 1 messen, dann auf die Hoehe bringen
    fi, st = blatt(1.0)
    poly = vereinigung(fi + [st])
    ys = [p[1] for p in poly]
    L = arg.hoehe / (max(ys) - min(ys))
    fi, st = blatt(L)
    umriss = vereinigung(fi + [st])
    xs, ys = [p[0] for p in umriss], [p[1] for p in umriss]
    dx, dy = -arg.abstand - max(xs), arg.abstand - min(ys)

    def schieben(z):
        return [(x + dx, y + dy) for x, y in z]

    umriss = schieben(umriss)
    eigen = [f.umriss()[0] for f in fi]
    fremde = [[u for j, u in enumerate(eigen) if j != i] for i in range(len(fi))]
    linien = [schieben(z) for i, f in enumerate(fi) for z in adern_linie(f, fremde[i])]
    loecher = [schieben(adern_flaeche(f, arg.rippe, arg.ader, fremde[i]))
               for i, f in enumerate(fi)]
    kasten = (min(p[0] for p in umriss), min(p[1] for p in umriss),
              max(p[0] for p in umriss), max(p[1] for p in umriss))
    bx, by = kasten[2] - kasten[0], kasten[3] - kasten[1]

    # --- Dateien ---------------------------------------------------------------
    os.makedirs(AUSGABE, exist_ok=True)
    datei = lambda endung: os.path.join(AUSGABE, NAME + endung)  # noqa: E731
    svg(datei('-linie.svg'), [umriss], linien, kasten, voll=False)
    svg(datei('-flaeche.svg'), [umriss] + loecher, [], kasten, voll=True)

    for f in (arg.linie_f, arg.flaeche_f):
        if f > GRBL_MAX_F:
            print('Hinweis: F%s liegt ueber $110/$111 = %s. GRBL faehrt dann %s, '
                  'rechnet M4 aber gegen F%s: Der Laser brennt schwaecher. '
                  'Erst $110/$111 erhoehen und --max-f angeben.'
                  % (zahl(f), zahl(GRBL_MAX_F), zahl(GRBL_MAX_F), zahl(f)))

    ordnung = zuege_ordnen(linien + [umriss + [umriss[0]]],
                           start=(kasten[2], kasten[1]))
    gc_linie = gcode_linien(ordnung, arg.linie_f, arg.linie_s)
    t_linie = dauer(fahrten(gc_linie))
    gc_linie = kopf('Hanfblatt - Strichgravur: Umriss, Mittelrippen, Seitenadern', kasten, [
        'Linien F%s S%d, Laufzeit etwa %s' % (zahl(arg.linie_f), arg.linie_s,
                                              minuten(t_linie))]) + gc_linie + ['M5', 'M2']

    zeilen = zeilen_fuellen([umriss] + loecher, kasten, arg.zeilen)
    gc_fl = gcode_flaeche(zeilen, arg.flaeche_f, arg.flaeche_s, arg.ueberlauf)
    gc_um = gcode_linien([umriss + [umriss[0]]], arg.linie_f, arg.linie_s)[1:]
    t_fl, t_um = dauer(fahrten(gc_fl)), dauer(fahrten(gc_um))
    gc_flaeche = kopf('Hanfblatt - Flaeche mit ausgesparten Adern, dann Umriss', kasten, [
        'Flaeche F%s S%d, Zeilenabstand %s mm, Ueberlauf %s mm'
        % (zahl(arg.flaeche_f), arg.flaeche_s, zahl(arg.zeilen), zahl(arg.ueberlauf)),
        'Umriss F%s S%d' % (zahl(arg.linie_f), arg.linie_s),
        'Laufzeit etwa %s' % minuten(t_fl + t_um)]) + gc_fl + gc_um + ['M5', 'M2']

    for endung, gc in (('-linie.gc', gc_linie), ('-flaeche.gc', gc_flaeche)):
        with open(datei(endung), 'w', encoding='ascii', newline='\n') as fh:
            fh.write('\n'.join(gc) + '\n')

    # --- Pruefungen ------------------------------------------------------------
    fehler = []

    def pruefe(ok, text):
        print('  %s  %s' % ('ok  ' if ok else 'FEHL', text))
        if not ok:
            fehler.append(text)

    print('Hanfblatt %.1f x %.1f mm, mittlere Fieder %.1f mm, Nullpunkt-Abstand %s mm'
          % (bx, by, L, zahl(arg.abstand)))
    pruefe(flaeche(umriss) > 0, 'Umriss gegen den Uhrzeigersinn, %d Punkte' % len(umriss))
    pruefe(not schnitte_finden(strecken(umriss)), 'Umriss ohne Selbstschnitt')
    for i, l in enumerate(loecher):
        pruefe(not schnitte_finden(strecken(l)), 'Adern Fieder %d ohne Selbstschnitt' % (i + 1))
    alle_l = [s for l in loecher for s in strecken(l)]
    pruefe(not schnitte_finden(alle_l, strecken(umriss)), 'Adern schneiden den Umriss nicht')
    pruefe(all(innen(p, umriss) for l in loecher for p in l), 'Adern ganz im Blatt')
    kreuz = 0
    for i in range(len(loecher)):
        for j in range(i + 1, len(loecher)):
            kreuz += len(schnitte_finden(strecken(loecher[i]), strecken(loecher[j])))
            kreuz += innen(loecher[i][0], loecher[j]) + innen(loecher[j][0], loecher[i])
    pruefe(kreuz == 0, 'Adern verschiedener Fiedern ueberlappen nicht')
    pruefe(all(innen(p, umriss) or min(math.hypot(p[0] - q[0], p[1] - q[1])
                                       for q in umriss) < 0.3
               for z in linien for p in z), 'Aderlinien im Blatt')
    nseit = sum(len(z) == 5 for z in linien)
    pruefe(nseit > 100, '%d Seitenadern' % nseit)

    for name, gc in (('Linie', gc_linie), ('Flaeche', gc_flaeche)):
        fa = fahrten(gc)
        alle = [(x, y) for x0, y0, x1, y1, *_ in fa for x, y in ((x0, y0), (x1, y1))][1:]
        brennt = [(x, y) for x0, y0, x1, y1, f, s, _ in fa if s > 0
                  for x, y in ((x0, y0), (x1, y1))]
        pruefe(all(FELD_X[0] <= x <= FELD_X[1] and FELD_Y[0] <= y <= FELD_Y[1]
                   for x, y in alle), '%s: alle Fahrten im Arbeitsfeld' % name)
        pruefe(all(x <= 0.0 and y >= 0.0 for x, y in alle),
               '%s: alle Fahrten bei X <= 0, Y >= 0 (auf dem Werkstueck)' % name)
        e = 0.01
        pruefe(all(kasten[0] - e <= x <= kasten[2] + e and kasten[1] - e <= y <= kasten[3] + e
                   for x, y in brennt), '%s: Laser nur im Motiv an' % name)
        pruefe(all(not schnell for *_, s, schnell in fa if s > 0),
               '%s: keine Eilfahrt mit Laser' % name)
        pruefe(max(f for *_, f, s, schnell in fa if not schnell) <= GRBL_MAX_F,
               '%s: Vorschub hoechstens $110/$111 = %s mm/min' % (name, zahl(GRBL_MAX_F)))
    print('  Strichgravur:  %d Zeilen G-Code, etwa %s' % (len(gc_linie), minuten(t_linie)))
    print('  Flaeche:       %d Zeilen G-Code, etwa %s (Flaeche %s, Umriss %s)'
          % (len(gc_flaeche), minuten(t_fl + t_um), minuten(t_fl), minuten(t_um)))
    print('Dateien in gravur/: %s' % ', '.join(
        NAME + e for e in ('-linie.svg', '-flaeche.svg', '-linie.gc', '-flaeche.gc')))
    if fehler:
        print('%d Pruefung(en) fehlgeschlagen' % len(fehler))
        sys.exit(1)
    print('alle Pruefungen bestanden')


if __name__ == '__main__':
    main()
