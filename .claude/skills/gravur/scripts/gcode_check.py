#!/usr/bin/env python3
"""Prueft G-Code fuer den Engraver und zeichnet eine Vorschau.

Spielt die Datei durch einen GRBL-Nachbau im Lasermodus ($32=1): Der Laser
brennt nur bei G1/G2/G3 mit M3/M4 und S > 0, bei G0 nie. Geprueft wird:

  FEHL  Brennen ausserhalb des Werkstuecks (mit --werkstueck), Ziele
        ausserhalb des Arbeitsfelds (Softlimits, sonst ALARM:2 mitten im
        Auftrag), Z-Fahrten, G1 ohne F, S ueber $30, G28/G30, Zeilen zu lang
        fuer GRBL, Laser am Ende nicht aus, Werkstueck zu dick
  WARN  M3 statt M4, F ueber $110, G92, anderes WCS, relative Koordinaten,
        viele sehr kurze Befehle (der Uno kommt nicht nach), viel Energie
        oder sehr langsam (Brandgefahr)
  info  Rahmen der Gravur, Abstand zu den Kanten, Dauer (Planer wie GRBL),
        Messpunkt des Autofokus

Geht fuer Dateien aus gravur.py und aus LightBurn.

    python3 gcode_check.py datei.gc --werkstueck 140x100 [--material spanplatte]
        [--ursprung vorn-rechts] [--rand 1] [--pi zustand.json] [--vorschau bild.png]

Exit-Code 0 = keine FEHL.
"""

import argparse
import json
import math
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import maschine as M  # noqa: E402

WORT = re.compile(r'([A-Z])([-+]?(?:\d+\.?\d*|\.\d+))')
LINIE_MAX = 79          # GRBL 1.1: LINE_BUFFER_SIZE 80


class Bericht:
    def __init__(self):
        self.eintraege = []         # (art, text)

    def add(self, art, text):
        self.eintraege.append((art, text))

    def fehl(self, t):
        self.add('FEHL', t)

    def warn(self, t):
        self.add('WARN', t)

    def ok(self, t):
        self.add('ok', t)

    def info(self, t):
        self.add('info', t)

    @property
    def fehler(self):
        return [t for a, t in self.eintraege if a == 'FEHL']

    def text(self):
        return '\n'.join('  %-4s %s' % (a, t) for a, t in self.eintraege)


def _zeilen_liste(nummern, n=5):
    s = ', '.join(str(x) for x in nummern[:n])
    return s + (' ...' if len(nummern) > n else '')


# ---------------------------------------------------------------- lesen

def _bogen(p0, p1, ij, r, uhrzeiger):
    x0, y0 = p0[0], p0[1]
    x1, y1 = p1[0], p1[1]
    if ij:
        cx, cy = x0 + ij.get('I', 0.0), y0 + ij.get('J', 0.0)
    else:
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        h = 4 * r * r - dx * dx - dy * dy
        if d == 0 or h < -1e-6:
            raise ValueError('Bogen mit R nicht moeglich')
        h = -math.sqrt(max(0.0, h)) / d
        if not uhrzeiger:
            h = -h
        if r < 0:
            h = -h
        cx, cy = x0 + 0.5 * (dx - dy * h), y0 + 0.5 * (dy + dx * h)
    rad = math.hypot(x0 - cx, y0 - cy)
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    d = a1 - a0
    if uhrzeiger:
        if d >= -1e-9:
            d -= 2 * math.pi
    elif d <= 1e-9:
        d += 2 * math.pi
    n = max(2, int(math.ceil(abs(d) * rad / 0.3)))
    pts = []
    for i in range(1, n + 1):
        a = a0 + d * i / n
        z = p0[2] + (p1[2] - p0[2]) * i / n
        pts.append([cx + rad * math.cos(a), cy + rad * math.sin(a), z])
    pts[-1] = list(p1)
    return pts


def lesen(text):
    """G-Code -> (Bewegungen, Bericht, Infos).

    Bewegung: (x0, y0, z0, x1, y1, z1, art, s, f, brennt, sync, nr, spindel)
    sync = Planer haelt vor dieser Bewegung an (M3/M4/M5 geaendert, G4)."""
    st = {'abs': True, 'mm': True, 'bew': 'G0', 'sp': 'M5', 's': 0.0, 'f': None,
          'pos': [0.0, 0.0, 0.0], 'wcs': 'G54'}
    bew = []
    info = {'zeilen': 0, 'g91': False, 'g53': 0, 'pausen': 0.0, 'm3': 0}
    probleme = {}

    def merke(schluessel, nr):
        probleme.setdefault(schluessel, []).append(nr)

    sync = False
    for nr, roh in enumerate(text.splitlines(), 1):
        z = roh.strip()
        if not z or z.startswith('%'):
            continue
        z = re.sub(r'\([^)]*\)', '', z).split(';', 1)[0].strip()
        if not z:
            continue
        info['zeilen'] += 1
        if z.startswith('$'):
            merke('$-Befehl in der Datei (gehoert in die Konsole)', nr)
            continue
        if z.startswith('/'):
            z = z[1:]
        code = z.upper().replace(' ', '').replace('\t', '')
        if len(code) > LINIE_MAX:
            merke('Zeile laenger als %d Zeichen (GRBL error:11)' % LINIE_MAX, nr)
        woerter = WORT.findall(code)
        if ''.join(a + w for a, w in woerter) != code:
            merke('nicht lesbare Zeile', nr)
            continue
        ziel = list(st['pos'])
        achse, g4, g53, ij, r, p = False, False, False, {}, None, None
        m_neu = None
        for a, w in woerter:
            v = float(w)
            if a == 'G':
                g = round(v, 1)
                if g in (0, 1, 2, 3):
                    st['bew'] = 'G%d' % int(g)
                elif g == 4:
                    g4 = True
                elif g == 90:
                    st['abs'] = True
                elif g == 91:
                    st['abs'] = False
                    info['g91'] = True
                elif g == 20:
                    st['mm'] = False
                    merke('G20: Zoll statt mm', nr)
                elif g == 21:
                    st['mm'] = True
                elif g == 53:
                    g53 = True
                elif g in (54, 55, 56, 57, 58, 59):
                    st['wcs'] = 'G%d' % int(g)
                    if g != 54:
                        merke('G%d statt G54: Nullpunkt nicht die Anschlagecke' % int(g), nr)
                elif g == 92:
                    merke('G92 verschiebt den Nullpunkt (nicht nachgebildet)', nr)
                elif g in (28, 30):
                    merke('G28/G30 faehrt an eine gespeicherte Position', nr)
                elif g in (17, 40, 49, 61, 80, 94, 90.1, 91.1, 43.1):
                    pass
                else:
                    merke('G%g unbekannt' % g, nr)
            elif a == 'M':
                m = int(v)
                if m in (3, 4, 5):
                    m_neu = 'M%d' % m
                elif m in (2, 30):
                    m_neu = 'M5'
                    st['abs'], st['bew'] = True, 'G1'
                elif m in (7, 8, 9):
                    pass
                elif m in (0, 1):
                    merke('M0/M1: Pause, wartet auf Weiter', nr)
                else:
                    merke('M%d unbekannt' % m, nr)
            elif a == 'S':
                st['s'] = v
            elif a == 'F':
                st['f'] = v * (1 if st['mm'] else 25.4)
            elif a in 'XYZ':
                v *= 1 if st['mm'] else 25.4
                i = 'XYZ'.index(a)
                ziel[i] = v if (st['abs'] or g53) else st['pos'][i] + v
                achse = True
            elif a in 'IJ':
                ij[a] = v * (1 if st['mm'] else 25.4)
            elif a == 'R':
                r = v * (1 if st['mm'] else 25.4)
            elif a == 'P':
                p = v
            elif a in 'NK':
                pass
            else:
                merke('Wort %s unbekannt' % a, nr)
        if m_neu and m_neu != st['sp']:
            st['sp'] = m_neu
            sync = True
        if m_neu == 'M3':
            info['m3'] += 1
        if g4:
            sync = True
            info['pausen'] += p or 0.0
            if st['sp'] == 'M3' and st['s'] > 0 and st['bew'] != 'G0':
                merke('G4-Pause mit M3 und Laser an: brennt im Stillstand', nr)
        if not achse:
            continue
        if g53:
            info['g53'] += 1
            st['pos'] = ziel
            sync = True
            continue
        art = st['bew']
        brennt = art != 'G0' and st['sp'] in ('M3', 'M4') and st['s'] > 0
        if art != 'G0' and not st['f']:
            merke('G1/G2/G3 ohne F (GRBL error:22)', nr)
        if art in ('G2', 'G3'):
            try:
                punkte = _bogen(st['pos'], ziel, ij, r, art == 'G2')
            except ValueError:
                merke('Bogen nicht berechenbar', nr)
                punkte = [ziel]
        else:
            punkte = [ziel]
        vor = st['pos']
        for q in punkte:
            bew.append((vor[0], vor[1], vor[2], q[0], q[1], q[2], 'G0' if art == 'G0' else 'G1',
                        st['s'], st['f'] or 0.0, brennt, sync, nr, st['sp']))
            sync = False
            vor = q
        st['pos'] = list(ziel)
    info['ende_spindel'] = st['sp']
    info['ende_abs'] = st['abs']
    info['probleme'] = probleme
    return bew, info


# ---------------------------------------------------------------- Planer

def dauer(bew, g):
    """Zeit je Bewegung in s, wie der GRBL-Planer (Junction Deviation, Trapez)."""
    n = len(bew)
    if not n:
        return []
    a_xy = g['beschl']
    jd = g['jd']
    fmax = g['f_max']
    L, v, u, acc = [], [], [], []
    for m in bew:
        dx, dy, dz = m[3] - m[0], m[4] - m[1], m[5] - m[2]
        l = math.sqrt(dx * dx + dy * dy + dz * dz)
        L.append(l)
        if abs(dz) > 1e-9:
            vmax, a = 500.0, 10.0
        else:
            vmax, a = fmax, a_xy
        f = vmax if m[6] == 'G0' else min(m[8] or vmax, vmax)
        v.append(f / 60.0)
        acc.append(a)
        u.append((dx / l, dy / l, dz / l) if l > 0 else (0.0, 0.0, 0.0))
    vj = [0.0] * (n + 1)
    for i in range(1, n):
        if bew[i][10] or L[i - 1] == 0 or L[i] == 0:
            continue
        c = -(u[i - 1][0] * u[i][0] + u[i - 1][1] * u[i][1] + u[i - 1][2] * u[i][2])
        if c > 0.999999:
            w = 0.0
        elif c < -0.999999:
            w = float('inf')
        else:
            sh = math.sqrt(0.5 * (1 - c))
            w = math.sqrt(min(acc[i], acc[i - 1]) * jd * sh / (1 - sh))
        vj[i] = min(w, v[i - 1], v[i])
    for i in range(n - 1, -1, -1):
        vj[i] = min(vj[i], math.sqrt(vj[i + 1] ** 2 + 2 * acc[i] * L[i]))
    for i in range(n):
        vj[i + 1] = min(vj[i + 1], math.sqrt(vj[i] ** 2 + 2 * acc[i] * L[i]))
    t = []
    for i in range(n):
        l, a, vm, v0, v1 = L[i], acc[i], v[i], vj[i], vj[i + 1]
        if l == 0:
            t.append(0.0)
            continue
        da = (vm * vm - v0 * v0) / (2 * a)
        dd = (vm * vm - v1 * v1) / (2 * a)
        if da + dd <= l:
            t.append((vm - v0) / a + (vm - v1) / a + (l - da - dd) / vm)
        else:
            vp = math.sqrt(max(0.0, (2 * a * l + v0 * v0 + v1 * v1) / 2))
            t.append((vp - v0) / a + (vp - v1) / a)
    return t


# ---------------------------------------------------------------- pruefen

def _mm(x):
    return ('%.1f' % x).replace('.', ',')


def pruefen(bew, info, werkstueck=None, ursprung='vorn-rechts', rand=1.0,
            material=None, zustand=None, dicke=None, z_ok=False, test=False):
    """Prueft die gelesenen Bewegungen. Gibt (Bericht, Zahlen)."""
    b = Bericht()
    g = M.grenzen(zustand)
    zahlen = {}
    mats = M.materialien()
    mat = mats.get(material) if material else None
    if material and not mat:
        b.warn('Material %r unbekannt (vorhanden: %s)' % (material, ', '.join(mats)))

    # Probleme beim Lesen
    schwer = ('G1/G2/G3 ohne F', 'Zeile laenger', 'nicht lesbare', 'G28/G30', 'Bogen nicht')
    for text, nummern in info['probleme'].items():
        art = 'FEHL' if text.startswith(schwer) else 'WARN'
        b.add(art, '%s (Zeile %s)' % (text, _zeilen_liste(nummern)))

    if zustand:
        e = zustand.get('einstellungen') or {}
        if str(e.get('$32', '1')).strip() not in ('1', '1.0'):
            b.fehl('$32=%s: Lasermodus aus, der Laser brennt auch im Stillstand und bei G0-Uebergaengen'
                   % e.get('$32'))
        wcs = zustand.get('wcs')
        if wcs and wcs != 'G54':
            b.warn('An der Maschine ist %s aktiv; die Datei waehlt G54 nur, wenn sie G54 enthaelt' % wcs)
        if (zustand.get('status') or {}).get('activeState', '').lower().startswith('alarm'):
            b.info('GRBL steht in ALARM: vor dem Auftrag $H')

    brenn = [m for m in bew if m[9] and (m[0] != m[3] or m[1] != m[4])]
    if not brenn:
        b.fehl('Die Datei brennt nichts (kein G1 mit M3/M4 und S > 0)')
    if info['g91']:
        b.warn('Relative Koordinaten (G91): die Lage haengt davon ab, wo der Kopf beim Start steht; '
               'die Pruefung nimmt X0 Y0 als Start an')
    if info['g53']:
        b.warn('%d Fahrten in Maschinenkoordinaten (G53), nicht geprueft' % info['g53'])

    # Ende
    if info['ende_spindel'] != 'M5':
        b.fehl('Am Ende ist der Laser nicht aus (letztes %s statt M5)' % info['ende_spindel'])
    else:
        b.ok('Am Ende M5')

    # Z
    z_fahrten = [m for m in bew if abs(m[5] - m[2]) > 1e-9]
    if z_fahrten and not z_ok:
        b.fehl('%d Z-Fahrten (Zeile %s): Fokus vorher einstellen, die Datei soll Z nicht bewegen'
               % (len(z_fahrten), _zeilen_liste([m[11] for m in z_fahrten])))
    elif not z_fahrten:
        b.ok('Keine Z-Fahrten')

    # Leistung, Vorschub, M3
    s_zu_hoch = sorted({m[7] for m in brenn if m[7] > g['s_max'] + 1e-9})
    if s_zu_hoch:
        b.fehl('S bis %g, erlaubt %g ($30)' % (max(s_zu_hoch), g['s_max']))
    f_zu_hoch = sorted({m[8] for m in bew if m[6] == 'G1' and m[8] > g['f_max'] + 1e-9})
    if f_zu_hoch:
        b.warn('F bis %g, GRBL faehrt hoechstens %g ($110): dauert laenger, brennt dunkler als geplant'
               % (max(f_zu_hoch), g['f_max']))
    m3 = [m for m in brenn if m[12] == 'M3']
    if m3:
        b.warn('%d Brennstrecken mit M3 (konstante Leistung): Ecken und Zeilenenden brennen dunkler; '
               'besser M4 (in LightBurn: Constant Power Mode aus)' % len(m3))
    elif brenn:
        b.ok('Brennen mit M4 (Leistung folgt der Geschwindigkeit)')

    # Energie
    kombis = {}
    for m in brenn:
        if m[8] <= 0:
            continue                # ohne F: schon oben als FEHL gemeldet
        l = math.hypot(m[3] - m[0], m[4] - m[1])
        k = (m[7], m[8])
        kombis[k] = kombis.get(k, 0.0) + l
    zahlen['kombis'] = kombis
    if kombis:
        haupt = sorted(kombis.items(), key=lambda kv: -kv[1])[:6]
        b.info('Leistung/Vorschub (nach Strecke): ' + ', '.join(
            'S%g F%g (E %.3f, %s mm)' % (s, f, s / f if f else 0, _mm(l)) for (s, f), l in haupt)
            + (' ...' if len(kombis) > 6 else ''))
        langsam = sorted({f for s, f in kombis if f < 300})
        if langsam:
            b.warn('Sehr langsam gebrannt (F %s): Brandgefahr, dabei bleiben'
                   % ', '.join('%g' % f for f in langsam))
        if mat and mat.get('schwarz_ab_e'):
            e0 = mat['schwarz_ab_e']
            e_max = max(s / f for s, f in kombis if f)
            if e_max > 3 * e0 and not test:
                b.warn('E bis %.2f, %s wird schon ab E %.2f schwarz: Brandraender, Flammen moeglich'
                       % (e_max, mat['name'], e0))
            if mat.get('stand', '').startswith('Startwert'):
                b.warn('%s: Werte sind Startwerte, an dieser Maschine nicht getestet -> erst Materialtest'
                       % mat['name'])

    # Rahmen der Gravur und Werkstueck
    if brenn:
        xs = [c for m in brenn for c in (m[0], m[3])]
        ys = [c for m in brenn for c in (m[1], m[4])]
        rb = (min(xs), max(xs), min(ys), max(ys))
        zahlen['rahmen'] = rb
        b.info('Gravur in G54: X %s bis %s, Y %s bis %s (%s x %s mm)'
               % (_mm(rb[0]), _mm(rb[1]), _mm(rb[2]), _mm(rb[3]),
                  _mm(rb[1] - rb[0]), _mm(rb[3] - rb[2])))
        if werkstueck:
            wb, wt = werkstueck
            w = M.werkstueck_g54(wb, wt, ursprung)
            zahlen['werkstueck'] = w
            abst = {'links': rb[0] - w[0], 'rechts': w[1] - rb[1],
                    'vorn': rb[2] - w[2], 'hinten': w[3] - rb[3]}
            zahlen['abstand'] = abst
            text = ', '.join('%s %s' % (k, _mm(v)) for k, v in abst.items())
            if min(abst.values()) < rand - 1e-6:
                b.fehl('Gravur reicht ueber das Werkstueck %g x %g mm hinaus oder naeher als %g mm '
                       'an die Kante: %s mm' % (wb, wt, rand, text))
            else:
                b.ok('Gravur auf dem Werkstueck %g x %g mm (Ursprung %s), Abstand zu den Kanten: %s mm'
                     % (wb, wt, ursprung, text))
                eng = [k for k, v in abst.items() if v < M.NIEDERHALTER_RAND]
                if eng:
                    b.info('Unter %g mm Rand (%s): dort keinen Niederhalter setzen'
                           % (M.NIEDERHALTER_RAND, ', '.join(eng)))
        else:
            b.info('Ohne --werkstueck: nicht geprueft, ob die Gravur auf das Werkstueck passt')
        if ursprung == 'vorn-rechts' and (rb[0] <= M.AUTOFOKUS[0] <= rb[1]
                                           and rb[2] <= M.AUTOFOKUS[1] <= rb[3]):
            b.info('Die Gravur liegt ueber dem Messpunkt des Autofokus (X-30 Y58): vorher fokussieren')

    # Arbeitsfeld (Softlimits)
    fx, fy = g['feld']
    raus = [m for m in bew if not (fx[0] - 1e-6 <= m[3] <= fx[1] + 1e-6
                                   and fy[0] - 1e-6 <= m[4] <= fy[1] + 1e-6)]
    if g['quelle'] == 'Doku/Modell' and ursprung != 'vorn-rechts':
        b.info('Arbeitsfeld nicht geprueft: das Feld aus der Doku gilt nur mit G54 an der Anschlagecke')
    elif raus:
        b.fehl('%d Ziele ausserhalb des Arbeitsfelds (%s: X %s..%s, Y %s..%s), Zeile %s: '
               'GRBL bricht dort mit ALARM:2 ab' % (
                   len(raus), g['quelle'], _mm(fx[0]), _mm(fx[1]), _mm(fy[0]), _mm(fy[1]),
                   _zeilen_liste([m[11] for m in raus])))
    else:
        b.ok('Alle Ziele im Arbeitsfeld (%s)' % g['quelle'])
        if g['quelle'] == 'Doku/Modell' and any(m[3] > 0 for m in bew):
            b.info('Fahrten rechts vom Nullpunkt (X > 0): $130 war an der Maschine zuletzt kleiner als '
                   'in der Doku, mit dem Makro Rahmen pruefen')

    if dicke is not None:
        if dicke > M.DICKE_MAX:
            b.fehl('Werkstueck %g mm dick, unter den Toolhead passen hoechstens %g mm' % (dicke, M.DICKE_MAX))
        else:
            b.ok('Werkstueck %g mm dick (passt, hoechstens %g)' % (dicke, M.DICKE_MAX))

    # Dauer und Befehlsrate
    t = dauer(bew, g)
    gesamt = sum(t) + info['pausen']
    zahlen['dauer'] = gesamt
    zeit_brenn = sum(ti for ti, m in zip(t, bew) if m[9])
    kurz = sum(ti for ti, m in zip(t, bew) if 0 < ti < 0.004)
    bewegt = sum(t) or 1.0
    zahlen['kurz_anteil'] = kurz / bewegt
    if kurz / bewegt > 0.1:
        b.warn('%d %% der Fahrzeit in Befehlen unter 4 ms: der Uno kommt mit dem Lesen evtl. nicht nach '
               'und die Fahrt stockt (Erfahrungswert, nicht gemessen). Abhilfe: groeberes Intervall, '
               'kleineres F oder Bild als Schwellwert statt Dithern' % round(100 * kurz / bewegt))
    b.info('%d Zeilen G-Code, %d Bewegungen, davon %d brennend' % (info['zeilen'], len(bew), len(brenn)))
    b.info('Dauer etwa %s (Brennen %s), Planer mit a = %g mm/s^2, F max %g'
           % (_dauer_text(gesamt), _dauer_text(zeit_brenn), g['beschl'], g['f_max']))
    return b, zahlen


def _dauer_text(s):
    s = int(round(s))
    if s < 60:
        return '%d s' % s
    if s < 3600:
        return '%d min %02d s' % (s // 60, s % 60)
    return '%d h %02d min' % (s // 3600, (s % 3600) // 60)


# ---------------------------------------------------------------- Vorschau

HOLZ = (226, 196, 150)
BRAND = (45, 28, 18)


def vorschau(bew, pfad, werkstueck=None, ursprung='vorn-rechts', e_schwarz=0.2, titel=''):
    """PNG von oben, hinten oben im Bild, vorn unten (Blick von vorn auf die Maschine)."""
    from PIL import Image, ImageDraw, ImageFont

    brenn = [m for m in bew if m[9]]
    pts_x = [0.0] + [c for m in brenn for c in (m[0], m[3])]
    pts_y = [0.0] + [c for m in brenn for c in (m[1], m[4])]
    w = None
    if werkstueck:
        w = M.werkstueck_g54(werkstueck[0], werkstueck[1], ursprung)
        pts_x += [w[0], w[1]]
        pts_y += [w[2], w[3]]
    if ursprung == 'vorn-rechts':
        pts_x += [12.0]
        pts_y += [-12.0]
    rand = 8.0
    x0, x1 = min(pts_x) - rand, max(pts_x) + rand
    y0, y1 = min(pts_y) - rand, max(pts_y) + rand
    k = min(12.0, 2400.0 / max(x1 - x0, y1 - y0, 1.0))
    kopf = 28
    bild = Image.new('RGB', (int((x1 - x0) * k) + 1, int((y1 - y0) * k) + 1 + kopf), (246, 246, 246))
    d = ImageDraw.Draw(bild)

    def p(x, y):
        return ((x - x0) * k, (y1 - y) * k + kopf)

    if w:
        d.rectangle([p(w[0], w[3]), p(w[1], w[2])], fill=HOLZ, outline=(160, 130, 90))
    if ursprung == 'vorn-rechts':
        grau = (150, 150, 155)
        d.rectangle([p(0, M.ANSCHLAG_SCHENKEL), p(M.ANSCHLAG_BREITE, -M.ANSCHLAG_BREITE)], fill=grau)
        d.rectangle([p(-M.ANSCHLAG_SCHENKEL, 0), p(M.ANSCHLAG_BREITE, -M.ANSCHLAG_BREITE)], fill=grau)
    # Linienbreite = Zeilenabstand der Rasterzeilen (sonst Streifen), mindestens 0,1 mm
    ys = sorted({round(m[1], 4) for m in brenn if abs(m[4] - m[1]) < 1e-9})
    abst = [b - a for a, b in zip(ys, ys[1:]) if 0.02 < b - a < 1.0]
    zeile = sorted(abst)[len(abst) // 2] if abst else 0.1
    breite = max(1, int(math.ceil(max(0.1, zeile) * k - 0.05)))
    fahrt = [m for m in bew if not m[9] and m[6] == 'G0']
    if len(fahrt) <= 3000:
        for m in fahrt:
            d.line([p(m[0], m[1]), p(m[3], m[4])], fill=(120, 170, 230), width=1)
    for m in brenn:
        e = (m[7] / m[8]) if m[8] else 1.0
        t = min(1.0, e / e_schwarz) if e_schwarz else 1.0
        farbe = tuple(int(HOLZ[i] + (BRAND[i] - HOLZ[i]) * t) for i in range(3))
        d.line([p(m[0], m[1]), p(m[3], m[4])], fill=farbe, width=breite)
    # Nullpunkt, Autofokus
    ox, oy = p(0, 0)
    d.line([ox - 8, oy, ox + 8, oy], fill=(220, 30, 30), width=2)
    d.line([ox, oy - 8, ox, oy + 8], fill=(220, 30, 30), width=2)
    if ursprung == 'vorn-rechts':
        ax, ay = p(*M.AUTOFOKUS)
        d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], outline=(30, 90, 220), width=2)
    try:
        schrift = ImageFont.load_default(size=14)
    except TypeError:
        schrift = ImageFont.load_default()
    d.text((6, 6), (titel + '   ' if titel else '') + 'hinten', fill=(60, 60, 60), font=schrift)
    d.text((6, bild.height - 20), 'vorn  |  rot: Nullpunkt G54  blau: Messpunkt Autofokus', fill=(60, 60, 60),
           font=schrift)
    # Massstab 10 mm
    sx, sy = bild.width - 10 - 10 * k, bild.height - 12
    d.line([sx, sy, sx + 10 * k, sy], fill=(0, 0, 0), width=2)
    d.text((sx, sy - 18), '10 mm', fill=(0, 0, 0), font=schrift)
    bild.save(pfad)
    return pfad


# ---------------------------------------------------------------- CLI

def groesse(s):
    m = re.match(r'^\s*([\d.,]+)\s*[xX*]\s*([\d.,]+)\s*$', s or '')
    if not m:
        raise argparse.ArgumentTypeError('Groesse als BREITExTIEFE in mm, z. B. 140x100')
    return float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.'))


def alles(text, werkstueck=None, ursprung='vorn-rechts', rand=1.0, material=None,
          zustand=None, dicke=None, z_ok=False, test=False):
    bew, info = lesen(text)
    b, zahlen = pruefen(bew, info, werkstueck, ursprung, rand, material, zustand, dicke, z_ok, test)
    return bew, b, zahlen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('datei')
    ap.add_argument('--werkstueck', type=groesse, help='BREITExTIEFE in mm (X x Y)')
    ap.add_argument('--ursprung', default='vorn-rechts', choices=M.URSPRUENGE,
                    help='wo G54 X0 Y0 am Werkstueck liegt (Standard: Anschlagecke vorn rechts)')
    ap.add_argument('--rand', type=float, default=1.0, help='Mindestabstand Gravur-Kante in mm')
    ap.add_argument('--material')
    ap.add_argument('--dicke', type=float, help='Werkstueckdicke in mm')
    ap.add_argument('--pi', help='Zustand vom Pi (grbl_lesen.js) als JSON')
    ap.add_argument('--vorschau', help='PNG-Datei fuer die Vorschau')
    ap.add_argument('--z-ok', action='store_true', help='Z-Fahrten erlauben')
    a = ap.parse_args(argv)
    with open(a.datei, encoding='utf-8', errors='replace') as d:
        text = d.read()
    zustand = None
    if a.pi:
        with open(a.pi, encoding='utf-8') as d:
            zustand = json.load(d)
    bew, b, zahlen = alles(text, a.werkstueck, a.ursprung, a.rand, a.material, zustand, a.dicke, a.z_ok)
    print('Pruefung: %s' % a.datei)
    print(b.text())
    if a.vorschau:
        mat = M.materialien().get(a.material or '', {})
        vorschau(bew, a.vorschau, a.werkstueck, a.ursprung, mat.get('schwarz_ab_e', 0.2),
                 os.path.basename(a.datei))
        print('Vorschau: %s' % a.vorschau)
    print('\n%s' % ('Keine Fehler.' if not b.fehler else '%d Fehler.' % len(b.fehler)))
    return 1 if b.fehler else 0


if __name__ == '__main__':
    sys.exit(main())
