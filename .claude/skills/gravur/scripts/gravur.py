#!/usr/bin/env python3
"""Erzeugt Gravuren als G-Code fuer den Engraver (GRBL 1.1h, Lasermodus M4).

    gravur.py text "Werkstatt" --hoehe 12 --werkstueck 150x60 --material spanplatte
    gravur.py bild foto.jpg --art dither --breite 80 --werkstueck 100x100 --material mdf
    gravur.py svg logo.svg --breite 60 --werkstueck 80x80 --material spanplatte
    gravur.py materialtest --material sperrholz_birke --werkstueck 70x70
    gravur.py materialien

Nullpunkt G54 = Innenecke des Anschlagwinkels vorn rechts. Das Werkstueck
liegt links davon und dahinter (X <= 0, Y >= 0). Oben im Bild = hinten an
der Maschine; die Gravur liest sich von vorn. --werkstueck BREITExTIEFE
heisst: Breite in X (links-rechts), Tiefe in Y (vorn-hinten).

Schreibt <name>.gc und <name>_vorschau.png (Standard: ~/Documents/Gravuren/
<Datum>_<name>/), prueft die Datei mit gcode_check.py und gibt den Bericht
aus. Exit-Code 0 = keine FEHL. Z bewegt die Datei nie: Fokus vorher.
"""

import argparse
import datetime
import math
import os
import re
import shlex
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import bild as B  # noqa: E402
import formen as FO  # noqa: E402
import gcode_check as GC  # noqa: E402
import maschine as M  # noqa: E402


# ---------------------------------------------------------------- G-Code

def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def ascii_text(s):
    ersatz = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
              '€': 'EUR', '–': '-', '—': '-', '„': '"', '“': '"', '”': '"', '’': "'",
              '×': 'x', '°': ' Grad', '\n': ' / '}
    return ''.join(ersatz.get(c, c if 32 <= ord(c) < 127 else '?') for c in s)


class GCode:
    """Schreibt G-Code und laesst modale Woerter weg (weniger Zeichen fuer den Uno)."""

    def __init__(self):
        self.zeilen = []
        self.mod = None
        self.w = {'X': None, 'Y': None, 'S': None, 'F': None}
        self.pos = (0.0, 0.0)

    def roh(self, t):
        self.zeilen.append(t)
        if t.startswith('G0') or t.startswith('G1'):
            self.mod = t[:2]

    def _woerter(self, **kw):
        teile = []
        for k in ('X', 'Y', 'S', 'F'):
            v = kw.get(k)
            if v is None:
                continue
            t = fmt(v) if k in 'XY' else ('%d' % round(v))
            if t != self.w[k]:
                teile.append(k + t)
                self.w[k] = t
        return teile

    def g0(self, x, y):
        t = self._woerter(X=x, Y=y)
        if not t:
            return
        self.zeilen.append(('G0 ' if self.mod != 'G0' else '') + ' '.join(t))
        self.mod = 'G0'
        self.pos = (x, y)

    def g1(self, x=None, y=None, s=None, f=None):
        alt = dict(self.w)
        t = self._woerter(X=x, Y=y, S=s, F=f)
        if not any(w[0] in 'XY' for w in t):
            self.w = alt            # ohne Fahrt nichts schreiben
            return
        self.zeilen.append(('G1 ' if self.mod != 'G1' else '') + ' '.join(t))
        self.mod = 'G1'
        self.pos = (x if x is not None else self.pos[0], y if y is not None else self.pos[1])


def overscan_mm(f):
    v = f / 60.0
    return round(min(5.0, max(0.5, 1.3 * v * v / (2 * M.BESCHL))), 2)


def raster(gc, zeilen, f, overscan=None, bidi=True, versatz=0.0):
    """zeilen: [(y, [(xa, xb, s)])]; schreibt hinten zuerst, abwechselnd."""
    os_ = overscan_mm(f) if overscan is None else overscan
    richtung = 1
    for y, segs in sorted(zeilen, key=lambda z: -z[0]):
        segs = sorted(s for s in segs if s[1] - s[0] > 1e-6)
        if not segs:
            continue
        if richtung > 0:
            folge = [(a, b, s) for a, b, s in segs]
        else:
            folge = [(b + versatz, a + versatz, s) for a, b, s in reversed(segs)]
        start = folge[0][0] - richtung * os_
        gc.g0(start, y)
        pos = start
        for a, b, s in folge:
            if abs(a - pos) > 1e-6:
                gc.g1(x=a, s=0, f=f)
            gc.g1(x=b, s=s, f=f)
            pos = b
        gc.g1(x=pos + richtung * os_, s=0, f=f)
        if bidi:
            richtung = -richtung


def ausduennen(z, abstand=0.05):
    """Punkte naeher als abstand am Vorgaenger weglassen (Ende bleibt)."""
    aus = [z[0]]
    for p in z[1:-1]:
        if math.hypot(p[0] - aus[-1][0], p[1] - aus[-1][1]) >= abstand:
            aus.append(p)
    aus.append(z[-1])
    return np.asarray(aus)


def linien(gc, zuege, s, f):
    for z in FO.ordnen(zuege, gc.pos):
        z = ausduennen(z)
        gc.g0(z[0][0], z[0][1])
        for p in z[1:]:
            gc.g1(x=p[0], y=p[1], s=s, f=f)


# ---------------------------------------------------------------- Ebenen

def ebene_rahmen(e):
    if e['typ'] == 'fuellen':
        return FO.rahmen_dunkel(e["formen"])
    if e['typ'] == 'linie':
        pts = np.vstack([z for z, _ in e['zuege']])
        return pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max()
    ny, nx = e['S'].shape
    return e['x0'], e['x0'] + nx * e['p'], e['y0'], e['y0'] + ny * e['p']


def platzieren(w, h, a):
    """G54-Lage (x0, y0) der vorderen linken Ecke des Gravurrahmens w x h."""
    if a.werkstueck:
        bw, bt = a.werkstueck
        if w > bw + 1e-6 or h > bt + 1e-6:
            raise ValueError('Gravur %.1f x %.1f mm ist groesser als das Werkstueck %g x %g mm'
                             % (w, h, bw, bt))
        lage = a.lage or 'mitte'
        if a.links is not None:
            xl = a.links
        elif a.rechts is not None:
            xl = bw - a.rechts - w
        elif 'links' in lage:
            xl = a.abstand
        elif 'rechts' in lage:
            xl = bw - a.abstand - w
        else:
            xl = (bw - w) / 2.0
        if a.vorn is not None:
            yv = a.vorn
        elif a.hinten is not None:
            yv = bt - a.hinten - h
        elif 'vorn' in lage:
            yv = a.abstand
        elif 'hinten' in lage:
            yv = bt - a.abstand - h
        else:
            yv = (bt - h) / 2.0
        ox, oy = M.ursprung_punkt(a.ursprung, bw, bt)
        return xl - ox, yv - oy
    u = a.ursprung
    if u == 'mitte':
        return -w / 2.0, -h / 2.0
    rechts, vorn = 'rechts' in u, 'vorn' in u
    ax = (a.rechts if rechts else a.links)
    ay = (a.vorn if vorn else a.hinten)
    ax = a.abstand if ax is None else ax
    ay = a.abstand if ay is None else ay
    return (-ax - w if rechts else ax), (ay if vorn else -ay - h)


def g_code(ebenen, a, titel, kopf_extra=()):
    r = [ebene_rahmen(e) for e in ebenen]
    rb = (min(x[0] for x in r), max(x[1] for x in r), min(x[2] for x in r), max(x[3] for x in r))
    w, h = rb[1] - rb[0], rb[3] - rb[2]
    x0, y0 = platzieren(w, h, a)
    x0, y0 = round(x0, 2), round(y0, 2)
    dx, dy = x0 - rb[0], y0 - rb[2]
    gc = GCode()
    for t in ('G21', 'G90', 'G54', 'M5', 'M4 S0'):
        gc.roh(t)
    gc.w['S'] = '0'
    for durchgang in range(a.durchgaenge):
        for e in ebenen:
            if e['typ'] == 'fuellen':
                fo = FO.skalieren_verschieben(e['formen'], 1.0, dx, dy)
                fr = FO.rahmen(fo)
                p = e['intervall']
                k0 = int(math.floor((fr[2] - y0) / p))
                k1 = int(math.ceil((fr[3] - y0) / p))
                ys = y0 + (np.arange(k0, k1) + 0.5) * p
                st = FO.zeilen_fuellen(fo, ys)
                zl = [(y, [(xa, xb, e['s']) for xa, xb in segs if xb - xa > 0.01])
                      for y, segs in zip(ys, st)]
                raster(gc, zl, e['f'], a.overscan, not a.einseitig, a.zeilenversatz)
            elif e['typ'] == 'pixel':
                zl = B.zeilen(e['S'], e['x0'] + dx, e['y0'] + dy, e['p'])
                raster(gc, zl, e['f'], a.overscan, not a.einseitig, a.zeilenversatz)
            else:
                zuege = [(z + np.array([dx, dy]), zu) for z, zu in e['zuege']]
                linien(gc, zuege, e['s'], e['f'])
    gc.roh('M5')
    if a.ende == 'ecke':
        gc.g0(0.0, 0.0)
    kopf = ['; Gravur: %s' % ascii_text(titel),
            '; erzeugt %s mit .claude/skills/gravur/scripts/gravur.py'
            % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            '; Befehl: %s' % ascii_text(' '.join(shlex.quote(x) for x in sys.argv[1:]))]
    kopf += ['; ' + ascii_text(t) for t in kopf_extra]
    kopf += ['; Nullpunkt G54: %s' % ('Innenecke Anschlag vorn rechts' if a.ursprung == 'vorn-rechts'
                                      else a.ursprung),
             '; Rahmen der Gravur: X %.1f..%.1f Y %.1f..%.1f (%.1f x %.1f mm)'
             % (x0, x0 + w, y0, y0 + h, w, h),
             '; Z faehrt nicht: vorher fokussieren (Autofokus oder Fokustest)']
    return kopf, gc.zeilen, (x0, y0, w, h)


# ---------------------------------------------------------------- Werte

def material(a):
    if not a.material:
        return None
    mats = M.materialien()
    if a.material not in mats:
        raise ValueError('Material %r unbekannt. Vorhanden: %s' % (a.material, ', '.join(mats)))
    return mats[a.material]


def werte_fuellen(a):
    m = material(a) or {}
    v = m.get('fuellen', {})
    s, f = a.s or v.get('s'), a.f or v.get('f')
    p = a.intervall or v.get('intervall') or 0.1
    if not s or not f:
        raise ValueError('Leistung fehlt: --material NAME oder --s und --f angeben')
    return float(s), float(f), float(p)


def werte_linie(a):
    m = material(a) or {}
    v = m.get('linie', {})
    s = a.s_linie or v.get('s') or a.s
    f = a.f_linie or v.get('f') or a.f
    if not s or not f:
        raise ValueError('Leistung fuer Linien fehlt: --material NAME oder --s-linie und --f-linie')
    return float(s), float(f)


def pruefe_werte(s, f, p=None):
    if not (0 < s <= M.S_MAX):
        raise ValueError('S %g: erlaubt 1 bis %g' % (s, M.S_MAX))
    if not (50 <= f <= M.F_MAX):
        raise ValueError('F %g: erlaubt 50 bis %g mm/min ($110)' % (f, M.F_MAX))
    if p is not None and not (0.05 <= p <= 1.0):
        raise ValueError('Intervall %g mm: erlaubt 0,05 bis 1' % p)


# ---------------------------------------------------------------- Befehle

def cmd_text(a):
    f0, schrift, idx = FO.text_formen(a.text.replace('\\n', '\n'), a.schrift, a.hoehe, a.breite,
                                      a.zeilenfaktor, a.ausrichtung)
    fo = FO.drehen_spiegeln([f0], a.drehen, a.spiegeln)
    ebenen, info = [], ['Schrift: %s%s' % (schrift, ' (Index %d)' % idx if idx else '')]
    if a.art in ('fuellen', 'beides'):
        s, f, p = werte_fuellen(a)
        pruefe_werte(s, f, p)
        ebenen.append({'typ': 'fuellen', 'formen': fo, 's': s, 'f': f, 'intervall': p})
        info.append('Fuellen: S%g F%g Intervall %g mm' % (s, f, p))
    if a.art in ('kontur', 'beides'):
        s, f = werte_linie(a)
        pruefe_werte(s, f)
        ebenen.append({'typ': 'linie', 'zuege': FO.linienzuege(fo), 's': s, 'f': f})
        info.append('Kontur: S%g F%g' % (s, f))
    return ebenen, 'Text "%s"' % a.text, info


def cmd_svg(a):
    formen, hinweise, mm_je = FO.svg_lesen(a.datei)
    formen = FO.sichtbare(formen)
    r = FO.rahmen_dunkel(formen)
    if r is None:
        raise ValueError('Im SVG sind keine dunklen Formen (Text erst in Pfade umwandeln)')
    w, h = r[1] - r[0], r[3] - r[2]
    k = 1.0
    if a.breite and a.hoehe:
        k = min(a.breite / w, a.hoehe / h)
    elif a.breite:
        k = a.breite / w
    elif a.hoehe:
        k = a.hoehe / h
    if abs(k - 1.0) > 1e-9:
        formen, hinweise, _ = FO.svg_lesen(a.datei, mm_je_einheit_ziel=mm_je * k)
        formen = FO.skalieren_verschieben(FO.sichtbare(formen), k, 0, 0)
    formen = FO.drehen_spiegeln(formen, a.drehen, a.spiegeln)
    ebenen, info = [], list(hinweise)
    if a.art in ('fuellen', 'beides'):
        voll = [f for f in formen if f['fill']]
        if not any(f['fill'] == 'dunkel' for f in voll):
            raise ValueError('Keine gefuellten dunklen Flaechen im SVG: --art linie nehmen')
        s, f, p = werte_fuellen(a)
        pruefe_werte(s, f, p)
        ebenen.append({'typ': 'fuellen', 'formen': voll, 's': s, 'f': f, 'intervall': p})
        info.append('Fuellen: S%g F%g Intervall %g mm' % (s, f, p))
    if a.art in ('linie', 'beides'):
        mit_strich = [f for f in formen if f.get('strich')]
        quelle = mit_strich or formen
        s, f = werte_linie(a)
        pruefe_werte(s, f)
        ebenen.append({'typ': 'linie', 'zuege': FO.linienzuege(quelle), 's': s, 'f': f})
        info.append('Linien: S%g F%g (%s)' % (s, f, 'nur Konturen mit Strich' if mit_strich
                                               else 'Umrisse aller Formen'))
    return ebenen, 'SVG %s' % os.path.basename(a.datei), info


def cmd_bild(a):
    s, f, p = werte_fuellen(a)
    if a.intervall is None and a.art in ('dither', 'graustufen'):
        p = max(p, 0.15)
    pruefe_werte(s, f, p)
    g = B.laden(a.datei, not a.nicht_zuschneiden)
    L, w, h = B.zuschnitt(g, a.breite, a.hoehe, p, a.drehen, a.spiegeln)
    info = ['Bild %d x %d Pixel zu %g mm, %s x %s mm' % (L.shape[1], L.shape[0], p, fmt(w), fmt(h))]
    if a.art == 'linien':
        L2 = 1.0 - L if a.invertieren else L
        maske = B.linienbild(L2, p, a.detail, a.staerke, a.dunkel)
        S = np.where(maske, int(s), 0)
        info.append('Linienbild: Detail %g mm, Staerke %g, dunkel %g' % (a.detail, a.staerke, a.dunkel))
    else:
        d = B.anpassen(L, not a.kein_autokontrast, a.gamma, a.invertieren)
        if a.art == 'schwellwert':
            S = np.where(B.schwellwert(d, a.schwelle), int(s), 0)
        elif a.art == 'dither':
            S = np.where(B.dithern(d), int(s), 0)
        else:
            s_min = a.s_min if a.s_min is not None else round(0.4 * s)
            S = B.graustufen(d, s_min, s, a.stufen)
            info.append('Graustufen S%g..S%g in %d Stufen' % (s_min, s, a.stufen))
    info.append('%s: S%g F%g Intervall %g mm, %d %% der Pixel brennen'
                % (a.art, s, f, p, round(100 * float((S > 0).mean()))))
    ebene = {'typ': 'pixel', 'S': S, 'p': p, 'f': f, 'x0': 0.0, 'y0': 0.0}
    return [ebene], 'Bild %s (%s)' % (os.path.basename(a.datei), a.art), info


def _liste(s):
    return [float(x) for x in re.split(r'[,; ]+', s.strip()) if x]


def cmd_materialtest(a):
    m = material(a) or {}
    test = m.get('test', {})
    leistung = _liste(a.leistung) if a.leistung else test.get('leistung', [20, 40, 60, 80, 100])
    vorschub = _liste(a.vorschub) if a.vorschub else test.get('vorschub', [3000, 2000, 1500, 1000, 600])
    p = a.intervall or m.get('fuellen', {}).get('intervall') or 0.1
    s_t = a.s_schrift or m.get('fuellen', {}).get('s') or 600
    f_t = a.f_schrift or (m.get('fuellen', {}).get('f') if m else None) or 1000
    for pr in leistung:
        if not 0 < pr <= 100:
            raise ValueError('Leistung %g %%: erlaubt 1 bis 100' % pr)
    for v in vorschub:
        pruefe_werte(1, v)
    pruefe_werte(s_t, f_t, p)
    sh, feld, luecke = a.schrifthoehe, a.feld, a.luecke
    schrift = 'Arial Bold'
    zeilen_text = ['%g' % v for v in vorschub]
    proben = [FO.text_formen(t, schrift, sh)[0] for t in zeilen_text]
    lw = max(FO.rahmen([q])[1] - FO.rahmen([q])[0] for q in proben) + 1.5
    kopf = sh + 1.5
    nx, ny = len(leistung), len(vorschub)
    hoehe = kopf + ny * feld + (ny - 1) * luecke
    ebenen, tabelle = [], []
    kr = min(lw, kopf) - 1.0
    cx, cy = lw / 2.0 - 0.5, hoehe - kopf / 2.0
    kreuz = {'typ': 'linie', 's': float(s_t), 'f': float(f_t),
             'zuege': [(np.array([[cx - kr / 2, cy], [cx + kr / 2, cy]]), False),
                       (np.array([[cx, cy - kr / 2], [cx, cy + kr / 2]]), False)]}
    if not a.kein_kreuz:
        ebenen.append(kreuz)
    for r, v in enumerate(vorschub):
        y1 = hoehe - kopf - r * (feld + luecke)
        for c, pr in enumerate(leistung):
            x0 = lw + c * (feld + luecke)
            s = round(pr * M.S_MAX / 100.0)
            ring = np.array([[x0, y1 - feld], [x0 + feld, y1 - feld], [x0 + feld, y1], [x0, y1],
                             [x0, y1 - feld]])
            ebenen.append({'typ': 'fuellen', 'formen': [FO.form([ring], [True])],
                           's': float(s), 'f': float(v), 'intervall': p})
            tabelle.append((r, c, s, v))
    for c, pr in enumerate(leistung):
        t = FO.text_formen('%g' % pr, schrift, sh)[0]
        tr = FO.rahmen([t])
        mx = lw + c * (feld + luecke) + feld / 2.0
        t = FO.skalieren_verschieben([t], 1, mx - (tr[0] + tr[1]) / 2, hoehe - sh - tr[2])[0]
        ebenen.append({'typ': 'fuellen', 'formen': [t], 's': float(s_t), 'f': float(f_t), 'intervall': p})
    for r, q in enumerate(proben):
        tr = FO.rahmen([q])
        y1 = hoehe - kopf - r * (feld + luecke)
        t = FO.skalieren_verschieben([q], 1, lw - 1.5 - tr[1], y1 - feld / 2.0 - (tr[2] + tr[3]) / 2)[0]
        ebenen.append({'typ': 'fuellen', 'formen': [t], 's': float(s_t), 'f': float(f_t), 'intervall': p})
    if not a.kein_kreuz:
        ebenen.append(kreuz)
    info = ['Materialtest %s: Spalten Leistung %s %%, Zeilen Vorschub %s mm/min, Felder %g mm, Intervall %g'
            % (m.get('name', 'ohne Material'), ', '.join('%g' % x for x in leistung),
               ', '.join('%g' % x for x in vorschub), feld, p),
            'Beschriftung und Kreuz S%g F%g; das Kreuz brennt am Anfang und am Ende: '
            'doppelt = Schritte verloren' % (s_t, f_t)]
    for r, v in enumerate(vorschub):
        info.append('Zeile %d von hinten, F%g: %s' % (r + 1, v, ', '.join(
            'S%d (E %.3f)' % (s, s / v) for rr, c, s, vv in tabelle if rr == r)))
    return ebenen, 'Materialtest %s' % (a.material or ''), info, tabelle


def cmd_materialien(a):
    for k, m in M.materialien().items():
        fu, li = m.get('fuellen', {}), m.get('linie', {})
        print('%-17s %s' % (k, m['name']))
        print('%17s fuellen S%s F%s Intervall %s, linie S%s F%s, schwarz ab E %s'
              % ('', fu.get('s'), fu.get('f'), fu.get('intervall'), li.get('s'), li.get('f'),
                 m.get('schwarz_ab_e')))
        print('%17s %s' % ('', m.get('stand', '')))
        if m.get('notiz'):
            print('%17s %s' % ('', m['notiz']))
    return 0


# ---------------------------------------------------------------- main

def _name(a, titel):
    if a.name:
        n = a.name
    elif a.befehl == 'text':
        n = a.text[:24]
    elif a.befehl in ('bild', 'svg'):
        n = os.path.splitext(os.path.basename(a.datei))[0]
    else:
        n = 'materialtest_%s' % (a.material or 'eigen')
    n = re.sub(r'[^A-Za-z0-9_-]+', '_', ascii_text(n)).strip('_') or 'gravur'
    return n


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split('\n\n', 1)[1])
    gem = argparse.ArgumentParser(add_help=False)
    g = gem.add_argument_group('Werkstueck und Lage')
    g.add_argument('--werkstueck', type=GC.groesse, help='BREITExTIEFE in mm (X x Y), z. B. 140x100')
    g.add_argument('--dicke', type=float, help='Werkstueckdicke in mm (nur Pruefung, hoechstens 32)')
    g.add_argument('--ursprung', default='vorn-rechts', choices=M.URSPRUENGE,
                   help='wo G54 X0 Y0 am Werkstueck liegt (Standard vorn-rechts = Anschlagecke)')
    g.add_argument('--lage', choices=M.URSPRUENGE,
                   help='Lage der Gravur auf dem Werkstueck (Standard mitte, ohne Werkstueck die Ursprungsecke)')
    g.add_argument('--abstand', type=float, default=5.0, help='Abstand zu den Kanten bei Eck-Lagen (mm)')
    for k in ('links', 'rechts', 'vorn', 'hinten'):
        g.add_argument('--' + k, type=float, help='Abstand der Gravur zur %sen Werkstueckkante (mm)' % k
                       if k != 'vorn' else 'Abstand zur vorderen Werkstueckkante (mm)')
    g.add_argument('--drehen', type=int, default=0, choices=(0, 90, 180, 270),
                   help='Grad gegen den Uhrzeigersinn')
    g.add_argument('--spiegeln', action='store_true', help='links-rechts spiegeln')
    g.add_argument('--rand', type=float, default=1.0, help='Pruefung: Mindestabstand zur Kante (mm)')
    w = gem.add_argument_group('Laser')
    w.add_argument('--material', help='Voreinstellung aus materialien.json')
    w.add_argument('--s', type=float, help='Leistung zum Fuellen, 0..1000')
    w.add_argument('--f', type=float, help='Vorschub zum Fuellen, mm/min')
    w.add_argument('--intervall', type=float, help='Zeilenabstand in mm (auch Pixelgroesse bei Bildern)')
    w.add_argument('--s-linie', type=float)
    w.add_argument('--f-linie', type=float)
    w.add_argument('--durchgaenge', type=int, default=1)
    w.add_argument('--einseitig', action='store_true', help='Zeilen nur von links nach rechts')
    w.add_argument('--zeilenversatz', type=float, default=0.0,
                   help='mm, um die die Rueckwaerts-Zeilen nach rechts geschoben werden')
    w.add_argument('--overscan', type=float, help='mm Anlauf je Zeilenende (Standard aus F und a)')
    w.add_argument('--ende', choices=('ecke', 'bleiben'), default='ecke',
                   help='ecke: am Ende auf G54 X0 Y0 fahren')
    d = gem.add_argument_group('Ausgabe')
    d.add_argument('-o', '--ausgabe', help='Datei .gc (Standard ~/Documents/Gravuren/<Datum>_<name>/)')
    d.add_argument('--name')
    d.add_argument('--pi', help='Zustand vom Pi (grbl_lesen.js) fuer die Feldpruefung')

    sub = ap.add_subparsers(dest='befehl', required=True)
    t = sub.add_parser('text', parents=[gem], help='Schrift')
    t.add_argument('text', help='Text; \\n fuer neue Zeile')
    t.add_argument('--schrift', default='Arial', help='Name (z. B. "Arial Bold", Georgia) oder Pfad')
    t.add_argument('--hoehe', type=float, help='Versalhoehe in mm (Hoehe eines H)')
    t.add_argument('--breite', type=float, help='Breite der ganzen Schrift in mm')
    t.add_argument('--art', choices=('fuellen', 'kontur', 'beides'), default='fuellen')
    t.add_argument('--ausrichtung', choices=('links', 'mitte', 'rechts'), default='mitte')
    t.add_argument('--zeilenfaktor', type=float, default=1.25, help='Zeilenabstand in Schriftgroessen')

    s = sub.add_parser('svg', parents=[gem], help='Vektorgrafik (Logo, Zeichnung)')
    s.add_argument('datei')
    s.add_argument('--breite', type=float)
    s.add_argument('--hoehe', type=float)
    s.add_argument('--art', choices=('fuellen', 'linie', 'beides'), default='fuellen')

    b = sub.add_parser('bild', parents=[gem], help='Foto, Logo als PNG/JPG')
    b.add_argument('datei')
    b.add_argument('--art', required=True, choices=('schwellwert', 'dither', 'graustufen', 'linien'))
    b.add_argument('--breite', type=float)
    b.add_argument('--hoehe', type=float)
    b.add_argument('--schwelle', type=float, default=0.5, help='schwellwert: Dunkelheit 0..1')
    b.add_argument('--gamma', type=float, default=1.0, help='>1 hellere Mitteltoene')
    b.add_argument('--invertieren', action='store_true')
    b.add_argument('--kein-autokontrast', action='store_true')
    b.add_argument('--nicht-zuschneiden', action='store_true', help='weisse Raender behalten')
    b.add_argument('--s-min', type=float, help='graustufen: Leistung fuer das hellste Grau')
    b.add_argument('--stufen', type=int, default=16, help='graustufen: Anzahl Stufen')
    b.add_argument('--detail', type=float, default=0.4, help='linien: Linienbreite in mm')
    b.add_argument('--staerke', type=float, default=1.0, help='linien: groesser = weniger Linien')
    b.add_argument('--dunkel', type=float, default=0.0, help='linien: dunkle Flaechen fuellen (0..1)')

    m = sub.add_parser('materialtest', parents=[gem], help='Raster Leistung x Vorschub')
    m.add_argument('--leistung', help='Prozent, z. B. 20,40,60,80,100')
    m.add_argument('--vorschub', help='mm/min, z. B. 3000,2000,1500,1000,600')
    m.add_argument('--feld', type=float, default=6.0)
    m.add_argument('--luecke', type=float, default=2.0)
    m.add_argument('--schrifthoehe', type=float, default=2.5)
    m.add_argument('--s-schrift', type=float)
    m.add_argument('--f-schrift', type=float)
    m.add_argument('--kein-kreuz', action='store_true')

    sub.add_parser('materialien', help='Voreinstellungen auflisten')
    return ap


def main(argv=None):
    a = parser().parse_args(argv)
    if a.befehl == 'materialien':
        return cmd_materialien(a)
    try:
        tabelle = None
        if a.befehl == 'text':
            ebenen, titel, info = cmd_text(a)
        elif a.befehl == 'svg':
            ebenen, titel, info = cmd_svg(a)
        elif a.befehl == 'bild':
            ebenen, titel, info = cmd_bild(a)
        else:
            ebenen, titel, info, tabelle = cmd_materialtest(a)
        if a.durchgaenge < 1:
            raise ValueError('--durchgaenge mindestens 1')
        mat = material(a)
        if mat:
            info.insert(0, 'Material: %s (%s)' % (mat['name'], mat.get('stand', '')))
        if a.werkstueck:
            info.append('Werkstueck %g x %g mm%s' % (a.werkstueck[0], a.werkstueck[1],
                                                     ', %g mm dick' % a.dicke if a.dicke else ''))
        kopf, code, (x0, y0, w, h) = g_code(ebenen, a, titel, info)
    except ValueError as e:
        print('Fehler: %s' % e, file=sys.stderr)
        return 2

    name = _name(a, titel)
    if a.ausgabe:
        pfad = os.path.abspath(os.path.expanduser(a.ausgabe))
    else:
        ordner = os.path.expanduser('~/Documents/Gravuren/%s_%s'
                                    % (datetime.date.today().isoformat(), name))
        pfad = os.path.join(ordner, name + '.gc')
    os.makedirs(os.path.dirname(pfad), exist_ok=True)

    zustand = None
    if a.pi:
        import json
        with open(a.pi, encoding='utf-8') as dd:
            zustand = json.load(dd)
    text = '\n'.join(kopf + code) + '\n'
    bew, bericht, zahlen = GC.alles(text, a.werkstueck, a.ursprung, a.rand, a.material, zustand, a.dicke,
                                    test=(a.befehl == 'materialtest'))
    kopf.insert(3, '; Dauer etwa %s (Schaetzung)' % GC._dauer_text(zahlen.get('dauer', 0)))
    text = '\n'.join(kopf + code) + '\n'
    with open(pfad, 'w', encoding='ascii') as dd:
        dd.write(text)
    vb = os.path.splitext(pfad)[0] + '_vorschau.png'
    m = M.materialien().get(a.material or '', {})
    GC.vorschau(bew, vb, a.werkstueck, a.ursprung, m.get('schwarz_ab_e', 0.2),
                '%s  %s' % (os.path.basename(pfad), GC._dauer_text(zahlen.get('dauer', 0))))

    print('Gravur: %s' % titel)
    for t in info:
        print('  %s' % t)
    print('Datei:    %s' % pfad)
    print('Vorschau: %s' % vb)
    print('Pruefung:')
    print(bericht.text())
    print('\n%s' % ('Keine Fehler.' if not bericht.fehler else '%d Fehler.' % len(bericht.fehler)))
    return 1 if bericht.fehler else 0


if __name__ == '__main__':
    sys.exit(main())
