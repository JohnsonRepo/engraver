#!/usr/bin/env python3
"""Verkabelung Schritt fuer Schritt: jede Ader von Klemme zu Klemme.

Das Bild zur Anleitung docs/verkabelung.md. Oben eine schematische
Draufsicht mit den Leitungen, die das Gehaeuse verlassen, und ihren Wegen
durch Kanal und Energieketten bis zum Pi-Halter; darunter die acht
Schritte der Anleitung,
jeder fuer sich gezeichnet, mit den Aderfarben der Anschlussliste. Zwei
Kreuzungen gibt es: eine bei den Lichtschranken, die sich nicht vermeiden
laesst (drei Lichtschranken an drei Klemmen ergeben einen K3,3), und die
getauschte Spule am Y-Motor rechts, die Absicht ist.

Alles kommt aus tools/verkabelung.py: Nummern, Adern mit Farbe und
Anschluss, Querschnitte, Laengen, Wago-Belegung. Die Titel der Schritte
und Pruefungen liest das Skript aus der Anleitung. Jede gezeichnete Ader
wird gegen die Kabelliste geprueft, und am Ende muss jede Ader der Liste
genau einmal gezeichnet sein, in dem Schritt, der sie nennt — sonst bricht
das Skript ab.

    python3 tools/verkabelung_zeichnen.py  ->  docs/elektronik-verkabelung.svg
"""

import math
import os
import re
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from antrieb_zeichnen import (el, f1, text, de,      # noqa: E402
                              TEXT, GRAU, BLAU, ROT)
from anschluss_zeichnen import P24, MASSE, P5        # noqa: E402
import elektronik_zeichnen as ez                     # noqa: E402
import verkabelung as vk                             # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-verkabelung.svg')

W = 1240                        # Breite der Zeichnung
RX = 24                         # Rand links und rechts
PB, PH, LUECKE = 588, 340, 16   # Schritt-Felder: Breite, Hoehe, Abstand
UEB_H = 480                     # Hoehe der Uebersicht
FILL, RAND = '#f4f6f9', '#8c939e'
SHIELD = ('#eef4fb', BLAU)
WANDLER = ('#fff7ec', '#e67700')
GEH_FILL, GEH_RAND = '#fdf6ee', '#c2621b'   # Gehaeuse wie im Anschlussplan
KABELWEG = ez.KABEL                          # wie in der Platz-Zeichnung
HEBEL, HEBEL_RAND = '#f08c00', '#c46a00'     # Hebel der Wago 221
GELB, GELB_RAND = '#ffd43b', '#b08900'       # Warndreieck
PRUEF = '#0b7285'                            # Verweis auf eine Pruefung
STIFT = '#495057'
WAGO_FARBE = {'Wago +24 V': P24, 'Wago GND': MASSE, 'Wago +5 V': P5}

# Aderfarben der Anschlussliste; weiss und gelb bekommen einen Rand. Die
# Adern von W2 fuehren beide +24 V und werden rot markiert.
ADERFARBE = {'rot': '#e03131', 'schwarz': '#212529', 'weiß': '#ffffff',
             'gelb': '#fcc419', 'grün': '#2f9e44', 'blau': '#1c7ed6',
             'Ader 1': '#e03131', 'Ader 2': '#e03131', '—': STIFT}
ADERRAND = {'weiß': '#868e96', 'gelb': '#b08900'}

LTS = vk.leitungen()
LT = {lt['nr']: lt for lt in LTS}
GEZEICHNET = {}                 # (Nr, Ader) -> Schritt


# ---- Daten ---------------------------------------------------------------

def anleitung():
    """Schritte [(Nr, Titel, [W...])] und Pruefungen [(Buchstabe, Titel)]
    aus den Ueberschriften von docs/verkabelung.md."""
    with open(vk.ANLEITUNG, encoding='utf-8') as f:
        zeilen_ = f.read().splitlines()
    schritte, pruefungen, teil = [], [], None
    for z in zeilen_:
        if z.startswith('## '):
            teil = z[3:].strip()
        m = re.match(r'### (\d+)\. (.+)$', z)
        if m and teil == 'Schritt für Schritt':
            titel, nrn = m.group(2), []
            k = re.search(r'\s*\((W[^)]*)\)$', titel)
            if k:
                titel = titel[:k.start()]
                for s in k.group(1).split(','):
                    a, _, b = s.strip().partition('–')
                    for n in range(int(a[1:]), int((b or a)[1:]) + 1):
                        nrn.append('W{}'.format(n))
            schritte.append((int(m.group(1)), titel, nrn))
        m = re.match(r'### ([A-Z])\. (.+)$', z)
        if m and teil == 'Inbetriebnahme':
            pruefungen.append((m.group(1), m.group(2)))
    alle = [n for _, _, nrn in schritte for n in nrn]
    if sorted(alle) != sorted(LT) or len(alle) != len(set(alle)):
        raise SystemExit('Schritte der Anleitung nennen nicht jede Leitung '
                         'genau einmal: {}'.format(alle))
    return schritte, pruefungen


SCHRITTE, PRUEFUNGEN = anleitung()
SCHRITT_VON = {n: s for s, _, nrn in SCHRITTE for n in nrn}
_SCHRITT = [None]               # Schritt, der gerade gezeichnet wird


def ader(nr, i, von, an):
    """Ader i der Leitung nr: (Funktion, Farbe). Prueft, dass sie in der
    Kabelliste von `von` nach `an` geht, und zaehlt sie als gezeichnet."""
    f, farbe, a, b = LT[nr]['adern'][i]
    if {a, b} != {von, an}:
        raise SystemExit('{} Ader {}: Kabelliste {} – {}, gezeichnet '
                         '{} – {}'.format(nr, i + 1, a, b, von, an))
    if (nr, i) in GEZEICHNET:
        raise SystemExit('{} Ader {} doppelt gezeichnet'.format(nr, i + 1))
    GEZEICHNET[(nr, i)] = _SCHRITT[0]
    return f, farbe


def farben(farbe):
    """'schwarz · grün' -> ['schwarz', 'grün']."""
    return [s.strip() for s in farbe.split('·')]


def platz(wago, nr, gegen=None):
    """Platz (1-5 bzw. 1-10) der Leitung nr in der Wago, nach der
    Reihenfolge in der Kabelliste (wie in der Tabelle "Klemmen")."""
    for i, (n, _, d) in enumerate(vk.wago_belegung(LTS)[wago]):
        if n == nr and (gegen is None or d == gegen):
            return i + 1
    raise SystemExit('{} nicht an {}'.format(nr, wago))


def plaetze_frei(wago):
    n = dict((a, c) for a, _, c in vk.WAGO)[wago]
    return n, len(vk.wago_belegung(LTS)[wago])


def laenge_text(lt, K):
    """'1,57 → 2 m', '0,81 m, mitgeliefert' oder ''."""
    weg, kauf = vk.laenge_m(lt, K)
    if weg is None:
        return ''
    if lt.get('mitgeliefert') and kauf <= lt['mitgeliefert']:
        return '{} m, mitgeliefert'.format(de(weg, 2))
    return '{} → {} m'.format(de(weg, 2), de(kauf, 2))


def litze_kurz(lt):
    """Litze wie in der Kabelliste, ohne AWG: '3 Silikonlitzen 0,34 mm²'."""
    return re.sub(r' \(AWG \d+\)', '', vk._litze(lt))


def nrn_text(nrn):
    """['W3', 'W4', 'W5'] -> 'W3–W5', ['W6', 'W9', 'W10'] -> 'W6, W9, W10'."""
    z = [int(n[1:]) for n in nrn]
    teile, i = [], 0
    while i < len(z):
        j = i
        while j + 1 < len(z) and z[j + 1] == z[j] + 1:
            j += 1
        teile.append('W{}'.format(z[i]) if j - i < 2 else
                     'W{}–W{}'.format(z[i], z[j]))
        if j - i == 1:
            teile.append('W{}'.format(z[j]))
        i = j + 1
    return ', '.join(teile)


# ---- Bausteine -----------------------------------------------------------

def breite(s, gr, fett=False):
    """Geschaetzte Textbreite in px (Inter/Helvetica)."""
    return len(s) * gr * (0.6 if fett else 0.55)


def gruppe(x, y, inhalt):
    """Inhalt in lokalen Koordinaten, verschoben nach (x, y)."""
    return el('g', {'transform': 'translate({},{})'.format(f1(x), f1(y))},
              '\n'.join(inhalt))


def rechteck(x, y, b, h, fill=FILL, rand=RAND, strich_b=1.0, rx=5,
             strich=None):
    return el('rect', {'x': f1(x), 'y': f1(y), 'width': f1(b),
                       'height': f1(h), 'rx': rx, 'fill': fill,
                       'stroke': rand, 'stroke-width': strich_b,
                       'stroke-dasharray': strich})


def kreis(x, y, r, fill, rand='none', strich_b=1.0):
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': f1(r), 'fill': fill,
                         'stroke': rand, 'stroke-width': strich_b})


def punkte_text(punkte):
    return ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte)


def linie(punkte, farbe, b=1.0, strich=None):
    return el('polyline', {'points': punkte_text(punkte), 'fill': 'none',
                           'stroke': farbe, 'stroke-width': b,
                           'stroke-dasharray': strich,
                           'stroke-linejoin': 'round'})


def draht(punkte, farbe, b=2.4, bruecke=None):
    """Ader in ihrer Farbe (Name aus der Anschlussliste oder #rgb).
    bruecke=(x, y): an dieser Stelle springt die Ader in einem Bogen ueber
    eine andere (nur auf waagrechten Stuecken)."""
    rand = ADERRAND.get(farbe)
    farbe = ADERFARBE.get(farbe, farbe)
    if bruecke:
        xb, yb = bruecke
        d = ['M {} {}'.format(f1(punkte[0][0]), f1(punkte[0][1]))]
        for (x0, y0), (x1, y1) in zip(punkte, punkte[1:]):
            if abs(y0 - yb) < 0.1 and abs(y1 - yb) < 0.1 and \
                    min(x0, x1) < xb < max(x0, x1):
                s = 1 if x1 > x0 else -1
                d += ['L {} {}'.format(f1(xb - 6 * s), f1(yb)),
                      'A 6 6 0 0 {} {} {}'.format(1 if s > 0 else 0,
                                                  f1(xb + 6 * s), f1(yb))]
            d.append('L {} {}'.format(f1(x1), f1(y1)))
        form = ('path', {'d': ' '.join(d)})
        t = [kreis(xb, yb, 4.5, '#ffffff')]
    else:
        form = ('polyline', {'points': punkte_text(punkte)})
        t = []
    for f, bb in (((rand, b + 2.2), (farbe, b)) if rand else ((farbe, b),)):
        a = dict(form[1])
        a.update({'fill': 'none', 'stroke': f, 'stroke-width': bb,
                  'stroke-linejoin': 'round', 'stroke-linecap': 'round'})
        t.append(el(form[0], a))
    return t


def zeilen(x, y, liste, gr=11.0, farbe=TEXT, abstand=14.0, anker='start',
           fett_erste=False):
    return [text(x, y + abstand * i, s, gr, farbe, anker,
                 fett=fett_erste and i == 0)
            for i, s in enumerate(liste) if s]


def kasten(x, y, b, h, liste, fill=FILL, rand=RAND, fett=1, gr=12.0,
           abstand=15.0, dx=9.0, dy=19.0, strich=None):
    """Kasten mit Textzeilen; die ersten `fett` Zeilen fett und dunkel."""
    t = [rechteck(x, y, b, h, fill, rand, strich=strich)]
    for i, s in enumerate(liste):
        if s:
            t.append(text(x + dx, y + dy + abstand * i, s,
                          gr if i < fett else gr - 1.0,
                          TEXT if i < fett else GRAU, fett=i < fett))
    return t


def klemme(x, y, s=None, seite='r', gr=10.0, farbe=TEXT, fett=False):
    """Anschlusspunkt, Beschriftung rechts, links, oben oder unten."""
    t = [kreis(x, y, 3.3, '#ffffff', TEXT, 1.2)]
    if s:
        dx, dy, anker = {'r': (7, 4, 'start'), 'l': (-7, 4, 'end'),
                         'o': (0, -8, 'middle'),
                         'u': (0, 15, 'middle')}[seite]
        t.append(text(x + dx, y + dy, s, gr, farbe, anker, fett, halo=True))
    return t


def marke(x, y, nr, anker='start'):
    """Leitungsnummer wie im Anschlussplan (W7 ...); y ist die Grundlinie."""
    b = 10.0 + 7.0 * len(nr)
    x0 = {'start': x, 'end': x - b, 'middle': x - b / 2}[anker]
    return [rechteck(x0, y - 11, b, 15, '#ffffff', STIFT, 1.1, rx=7.5),
            text(x0 + b / 2, y + 0.5, nr, 10.5, TEXT, 'middle', fett=True)]


def marken_reihe(xm, y, nrn, luecke=4.0):
    """Mehrere Leitungsnummern nebeneinander, mittig um xm."""
    breiten = [10.0 + 7.0 * len(n) for n in nrn]
    x = xm - (sum(breiten) + luecke * (len(nrn) - 1)) / 2
    t = []
    for n, b in zip(nrn, breiten):
        t += marke(x, y, n)
        x += b + luecke
    return t


def pruefung(x, y, s, anker='start'):
    """Verweis auf eine Pruefung der Inbetriebnahme."""
    b = 12.0 + breite(s, 10.0, True)
    x0 = {'start': x, 'end': x - b, 'middle': x - b / 2}[anker]
    return [rechteck(x0, y - 11, b, 15, PRUEF, PRUEF, rx=7.5),
            text(x0 + b / 2, y + 0.5, s, 10.0, '#ffffff', 'middle',
                 fett=True)]


def warndreieck(x, y):
    """Gelbes Warndreieck, (x, y) = linke obere Ecke, 17 x 15 px."""
    return [el('polygon', {
        'points': '{},{} {},{} {},{}'.format(f1(x), f1(y + 15),
                                             f1(x + 8.5), f1(y),
                                             f1(x + 17), f1(y + 15)),
        'fill': GELB, 'stroke': GELB_RAND, 'stroke-width': '1',
        'stroke-linejoin': 'round'}),
        text(x + 8.5, y + 13.2, '!', 10.5, TEXT, 'middle', fett=True)]


def warnung(x, y, liste, gr=10.5, abstand=13.5, farbe=TEXT):
    """Warndreieck bei (x, y), Text rechts daneben (erste Zeile fett)."""
    return warndreieck(x, y) + zeilen(x + 23, y + 12, liste, gr, farbe,
                                      abstand, fett_erste=True)


def schrittmarke(x, y, nr):
    """Kleiner Verweis auf einen anderen Schritt: blaue Nummer im Kreis."""
    return [kreis(x, y, 8.5, BLAU),
            text(x, y + 4, str(nr), 10.5, '#ffffff', 'middle', fett=True)]


def wago(xo, yo, name, seite, n=None, teilung=26.0, tiefe=38.0):
    """Wago 221 von oben, die Plaetze nummeriert wie in der Tabelle
    "Klemmen" der Anleitung. (xo, yo) ist die Oeffnung von Platz 1; seite
    sagt, von wo die Adern kommen: 'u' (unten), 'o' (oben), 'l' (links)
    oder 'r' (rechts). Liefert (svg, {Platz: Oeffnung})."""
    n = n or plaetze_frei(name)[0]
    farbe = WAGO_FARBE[name]
    hebel_b = min(16.0, teilung - 6.0)
    t, auf = [], {}
    if seite in 'uo':
        x, b, h = xo - teilung / 2, teilung * n, tiefe
        y = yo - tiefe if seite == 'u' else yo
    else:
        x = xo if seite == 'l' else xo - tiefe
        y, b, h = yo - teilung / 2, tiefe, teilung * n
    t.append(rechteck(x, y, b, h, '#eef1f4', farbe, 1.6, rx=4))
    for i in range(n):
        if seite in 'uo':
            px, py = xo + teilung * i, yo
            hy = y + 5 if seite == 'u' else y + h - 27
            t += [rechteck(px - hebel_b / 2, hy, hebel_b, 22, HEBEL,
                           HEBEL_RAND, 0.8, rx=2),
                  text(px, hy + 15.5, str(i + 1), 10.0 if i < 9 else 8.5,
                       '#ffffff', 'middle', fett=True)]
            oy = yo - 7 if seite == 'u' else yo + 1
            t.append(rechteck(px - 4.5, oy, 9, 6, STIFT, STIFT, 0.5,
                              rx=1.5))
        else:
            px, py = xo, yo + teilung * i
            hx = x + b - 27 if seite == 'l' else x + 5
            t += [rechteck(hx, py - hebel_b / 2, 22, hebel_b, HEBEL,
                           HEBEL_RAND, 0.8, rx=2),
                  text(hx + 11, py + 3.5, str(i + 1), 9.5 if i < 9 else 8.0,
                       '#ffffff', 'middle', fett=True)]
            ox = xo + 1 if seite == 'l' else xo - 7
            t.append(rechteck(ox, py - 4.5, 6, 9, STIFT, STIFT, 0.5,
                              rx=1.5))
        auf[i + 1] = (px, py)
    return t, auf


def wago_rest(name, hier):
    """Kurztext, wohin die uebrigen Plaetze gehen: 'Platz 2–4: Schritt 3
    · 9, 10 frei'."""
    n, belegt = plaetze_frei(name)
    gruppen = []
    for i, (nr, _, _) in enumerate(vk.wago_belegung(LTS)[name]):
        s = SCHRITT_VON[nr]
        if s == hier:
            continue
        if gruppen and gruppen[-1][1] == s and gruppen[-1][0][-1] == i:
            gruppen[-1][0].append(i + 1)
        else:
            gruppen.append(([i + 1], s))
    teile = ['{}: {}'.format(
        str(p[0]) if len(p) == 1 else '{}–{}'.format(p[0], p[-1]),
        'Schritt {}'.format(s)) for p, s in gruppen]
    if belegt < n:
        frei = list(range(belegt + 1, n + 1))
        teile.append('{} frei'.format(
            str(frei[0]) if len(frei) == 1 else
            ', '.join(str(f) for f in frei) if len(frei) == 2 else
            '{}–{}'.format(frei[0], frei[-1])))
    return teile


def stift(x, y):
    """Einzelner Stift einer Stiftleiste (Draufsicht)."""
    return rechteck(x - 4.5, y - 4.5, 9, 9, '#adb5bd', STIFT, 0.8, rx=1)


def jumper(x0, y0, x1, y1):
    """Schwarze Steckbruecke ueber zwei Stifte."""
    b, h = abs(x1 - x0) + 14, abs(y1 - y0) + 14
    return rechteck(min(x0, x1) - 7, min(y0, y1) - 7, b, h, '#212529',
                    '#000000', 0.8, rx=3)


def widerstand(x, y, senkrecht=False, lang=26.0):
    """Widerstand als Kaestchen, Mitte bei (x, y)."""
    if senkrecht:
        return rechteck(x - 5, y - lang / 2, 10, lang, '#ffffff', STIFT,
                        1.4, rx=1.5)
    return rechteck(x - lang / 2, y - 5, lang, 10, '#ffffff', STIFT, 1.4,
                    rx=1.5)


def kondensator(x, y):
    """Kondensator, senkrecht, Mitte bei (x, y)."""
    return [linie([(x - 8, y - 3), (x + 8, y - 3)], STIFT, 2.2),
            linie([(x - 8, y + 3), (x + 8, y + 3)], STIFT, 2.2)]


def motor_symbol(x, y, a=34):
    """NEMA 17 von vorn: Flansch, Zentrierbund, Welle."""
    return [rechteck(x, y, a, a, '#ced4da', STIFT, 1.0, rx=4),
            kreis(x + a / 2, y + a / 2, a * 0.28, '#e9ecef', STIFT, 0.8),
            kreis(x + a / 2, y + a / 2, 2.6, STIFT)]


def feld(nr, unter, inhalt, b=PB, h=PH):
    """Rahmen eines Schritts: Nummer, Titel aus der Anleitung, rechts die
    Leitungen und die Pruefung danach."""
    titel = next(t for s, t, _ in SCHRITTE if s == nr)
    t = [rechteck(0, 0, b, h, '#ffffff', '#d0d7de', 1.0, rx=8),
         kreis(22, 23, 13, BLAU),
         text(22, 28, str(nr), 14, '#ffffff', 'middle', fett=True),
         text(44, 28.5, titel, 14.5, TEXT, fett=True)]
    x = b - 14
    for art, s in reversed(unter):
        if art == 'p':
            t += pruefung(x, 28, s, 'end')
            x -= 12.0 + breite(s, 10.0, True) + 6
        else:
            t.append(text(x, 28, s, 11, GRAU, 'end'))
            x -= breite(s, 11) + 6
    return t + inhalt


# ---- 1. Vorbereiten ------------------------------------------------------

def schritt_vorbereiten():
    t = [text(16, 62, 'Mikroschritt-Jumper', 12, TEXT, fett=True),
         text(16, 77, 'unter jedem Treiber: X, Y, Z und A', 10.5, GRAU)]
    bx, by = 28, 96
    t.append(rechteck(bx - 12, by - 12, 132, 60, SHIELD[0], '#9bb7d4', 1,
                      rx=4))
    for i, (name, alt, steckt) in enumerate((('MS1', 'M0', True),
                                             ('MS2', 'M1', True),
                                             ('MS3', 'M2', False))):
        cx = bx + 8 + 46 * i
        t += [stift(cx, by + 4), stift(cx, by + 28)]
        if steckt:
            t.append(jumper(cx, by + 4, cx, by + 28))
        t += [text(cx, by + 66, name, 11, TEXT, 'middle', fett=True),
              text(cx, by + 79, '(' + alt + ')', 10, GRAU, 'middle'),
              text(cx, by + 94, 'stecken' if steckt else 'frei', 10.5,
                   TEXT if steckt else ROT, 'middle', fett=not steckt)]
    t.append(text(166, 112, '= 1/16 Schritt', 12, TEXT, fett=True))
    t += zeilen(166, 128, ['TMC2209 ohne UART,', 'intern auf 1/256',
                           'interpoliert'], 10.5, GRAU)
    # Treiber richtig herum
    t.append(text(16, 222, 'Treiber richtig herum stecken', 12, TEXT,
                  fett=True))
    dx, dy = 22, 234
    t += [rechteck(dx, dy, 124, 56, SHIELD[0], '#9bb7d4', 1, rx=3),
          rechteck(dx + 22, dy + 6, 94, 44, '#2b2f36', '#000000', 0.8,
                   rx=2)]
    for k in range(7):                       # Kuehlkoerper
        x = dx + 44 + 9 * k
        t.append(linie([(x, dy + 12), (x, dy + 44)], '#868e96', 2.2))
    t += [kreis(dx + 29, dy + 13, 3.4, '#fa5252'),
          text(dx + 4, dy + 17, 'EN', 9.5, BLAU, fett=True),
          text(dx + 36, dy + 17, 'EN', 8.5, '#f8f9fa', fett=True)]
    t += zeilen(162, 248, ['EN-Pin des Treibers', 'an den EN-Aufdruck.',
                           'Strom erst in', 'Prüfung E (Vref).'], 10.5,
                GRAU, 13.5)
    vref = min(ez.vref(ez.MOTOR_I, r) for r in ez.R_SENSE)
    t += zeilen(16, 312, ['Vref {} V an allen vier: höchstens {} A'.format(
        de(vref, 2), de(ez.MOTOR_I, 2)), 'bei jedem üblichen '
        'Messwiderstand.'], 10.5, GRAU, 13.5)

    # A klont Y
    ax = 310
    t += [text(ax, 62, 'A klont Y: zwei Jumper', 12, TEXT, fett=True),
          text(ax, 77, 'neben dem A-Treiber (zweiter Y-Motor)', 10.5, GRAU)]
    spalten = (('X', 384), ('Y', 428), ('Z', 472), ('D12/D13', 530))
    reihen = (('A.STEP', 110), ('A.DIR', 140))
    t.append(rechteck(ax + 50, 88, 214, 70, SHIELD[0], '#9bb7d4', 1, rx=4))
    for s, x in spalten:
        t.append(text(x, 100, s, 10.5, ROT if s == 'D12/D13' else TEXT,
                      'middle', fett=True))
    for s, y in reihen:
        t.append(text(ax, y + 4, s, 10.5, TEXT, fett=True))
        for sp, x in spalten:
            t += [stift(x - 8, y), stift(x + 8, y)]
            if sp == 'Y':
                t.append(jumper(x - 8, y, x + 8, y))
            if sp == 'D12/D13':
                t += [linie([(x - 15, y - 8), (x + 15, y + 8)], ROT, 2),
                      linie([(x - 15, y + 8), (x + 15, y - 8)], ROT, 2)]
    t.append(text(ax, 176, 'Gesteckt: A.STEP ↔ Y.STEP, A.DIR ↔ Y.DIR.',
                  10.5, GRAU))
    t += warnung(ax, 188, ['Nie auf D12/D13: D12 ist bei',
                           'GRBL 1.1 der Z-Endschalter.'])
    t += warnung(ax, 224, ['EN/GND offen lassen:',
                           'GRBL schaltet die Treiber über D8.'])
    # Wago-Klemmen von links +5 V, GND, +24 V
    t.append(text(ax, 274, 'Wago-Klemmen, von links:', 10.5, TEXT,
                  fett=True))
    x = ax
    for name in ('Wago +5 V', 'Wago GND', 'Wago +24 V'):
        n = plaetze_frei(name)[0]
        b = 10 + 7 * n
        t.append(rechteck(x, 282, b, 18, '#eef1f4', WAGO_FARBE[name], 1.6,
                          rx=3))
        for k in range(n):
            t.append(rechteck(x + 6 + 7 * k, 286, 4, 10, HEBEL, HEBEL_RAND,
                              0.6, rx=1))
        t.append(text(x + b / 2, 314, name[5:], 10.5, WAGO_FARBE[name],
                      'middle', fett=True))
        x += b + 12
    t.append(text(ax, 330, 'W-Nummer an beide Enden jeder Leitung.', 10,
                  GRAU))
    return feld(1, [('t', 'vor dem Verdrahten, stromlos')], t)


# ---- 2. 24 V: Buchse, Schalter, Not-Aus ----------------------------------

def schritt_24v():
    t = []
    wand = 116
    t += [linie([(wand, 44), (wand, 140)], GEH_RAND, 1.4, '6 4'),
          text(wand - 6, 56, 'außen', 10, GRAU, 'end'),
          text(wand + 6, 56, 'im Gehäuse (Rückwand)', 10, GEH_RAND)]
    t += kasten(14, 66, 88, 62, ['Netzteil', '24 V / 3 A'])
    t += [linie([(102, 97), (114, 97)], '#495057', 5),
          rechteck(110, 91, 14, 12, '#868e96', STIFT, 0.8, rx=2)]
    t += kasten(126, 66, 76, 62, ['Buchse', '5,5 × 2,1'])
    t += [text(194, 84, '+', 12, P24, 'end', fett=True),
          text(194, 120, '−', 12, MASSE, 'end', fett=True)]
    t += kasten(234, 66, 72, 40, ['Schalter', 'EIN/AUS'])
    t += [text(228, 96, '1', 10, GRAU, 'end'), text(312, 96, '2', 10, GRAU)]
    # Not-Aus vorn am vorderen 2060
    t += [rechteck(336, 44, 238, 132, '#ffffff', P24, 1.0, rx=6,
                   strich='5 3'),
          text(566, 58, 'vorn am vorderen 2060', 10, P24, 'end')]
    t += kasten(352, 62, 118, 58, ['Not-Aus', 'Wechsler'], '#fff4f4', P24)
    t += [kreis(442, 86, 10, GELB, GELB_RAND), kreis(442, 86, 6.5,
                                                     '#e03131'),
          text(477, 84, 'NO frei', 10, GRAU)]
    # Wagos: GND links, +24 V rechts, Oeffnungen oben
    wg, og = wago(214, 250, 'Wago GND', 'o', teilung=22, tiefe=34)
    wp, op = wago(440, 250, 'Wago +24 V', 'o', teilung=22, tiefe=34)
    t += wg + wp
    t += [text(316, 243, 'Wago GND', 11, MASSE, 'middle', fett=True),
          text(500, 243, 'Wago +24 V', 11, P24, 'middle', fett=True)]
    # W1: Buchse + an den Schalter, Buchse − an die Wago GND
    _, f = ader('W1', 0, 'Buchse +', 'Schalter 1')
    t += draht([(202, 80), (234, 80)], f)
    _, f = ader('W1', 1, 'Buchse −', 'Wago GND')
    p1 = og[platz('Wago GND', 'W1')]
    t += draht([(202, 114), (p1[0], 114), p1], f)
    # W2: Schalter 2 an C, NC an die Wago +24 V
    _, f = ader('W2', 0, 'Schalter 2', 'Not-Aus C')
    t += draht([(306, 80), (352, 80)], f)
    _, f = ader('W2', 1, 'Not-Aus NC', 'Wago +24 V')
    p2 = op[platz('Wago +24 V', 'W2')]
    t += draht([(p2[0], 120), p2], f)
    for x, y in ((202, 80), (202, 114), (234, 80), (306, 80), (352, 80),
                 (p2[0], 120), (470, 80)):
        t += klemme(x, y)
    t += [text(346, 74, 'C', 10, TEXT, 'end', fett=True),
          text(p2[0] + 7, 134, 'NC', 10, TEXT, fett=True)]
    t += marke(p1[0], 196, 'W1', 'middle')
    lt2 = LT['W2']
    t += marke(p2[0] + 30, 150, 'W2')
    t += [text(p2[0] + 66, 150, litze_kurz(lt2), 10, GRAU),
          text(p2[0] + 30, 165, laenge_text(lt2, Q['K']), 10, GRAU)]
    t += zeilen(14, 154, ['Mittelstift +24 V, Hülse GND:',
                          'mit dem Netzteil messen.',
                          'Not-Aus: C–NC geschlossen,',
                          'gedrückt offen. NO bleibt frei,',
                          'dort läge beim Drücken +24 V.',
                          'Alles löten, Schrumpfschlauch.'], 10.5, GRAU,
                13.5)
    t.append(text(14, 306, 'Wago GND, übrige Plätze: ' + ' · '.join(
        wago_rest('Wago GND', 2)), 10, GRAU))
    t.append(text(14, 320, 'Wago +24 V, übrige Plätze: ' + ' · '.join(
        wago_rest('Wago +24 V', 2)), 10, GRAU))
    return feld(2, [('t', 'W1, W2 · dann'), ('p', 'Prüfung A, B')], t)


# ---- 3. Shield, Wandler, Lüfter ------------------------------------------

def verbraucher(x, y, plus, minus, liste, fill=FILL, rand=RAND):
    """Verbraucher mit + oben links, − unten links (Klemmen am Rand)."""
    t = [rechteck(x, y, 152, 92, fill, rand),
         text(x + 8, y + 22, plus, 11, P24, fett=True),
         text(x + 8, y + 78, minus, 11, MASSE, fett=True),
         text(x + 40, y + 22, liste[0], 12, TEXT, fett=True)]
    return t + zeilen(x + 40, y + 40, liste[1:], 11, GRAU, 15)


def schritt_verteilen():
    t = []
    wp, op = wago(230, 88, 'Wago +24 V', 'u')
    wm, om = wago(160, 270, 'Wago GND', 'o', teilung=24)
    t += wp + wm
    t += [text(356, 72, 'Wago +24 V', 12, P24, fett=True),
          text(396, 296, 'Wago GND', 12, MASSE, fett=True)]
    vx = (24, 216, 416)
    t += verbraucher(vx[0], 140, '+', '−', ['CNC Shield V3', 'Schraubklemme',
                                            '(12–36 V)'], *SHIELD)
    t += verbraucher(vx[1], 140, 'IN+', 'IN−', [
        'Wandler', '24 → 12 V, {} A'.format(de(ez.WANDLER_A, 0)),
        'OUT: Schritt 5'], *WANDLER)
    t += verbraucher(vx[2], 140, '+', '−', ['Lüfter', '24 V, im Deckel',
                                           'bläst auf die Treiber'])
    pp = [platz('Wago +24 V', n) for n in ('W3', 'W4', 'W5')]
    pm = [platz('Wago GND', n) for n in ('W3', 'W4', 'W5')]
    if pp != [2, 3, 4] or pm != [2, 3, 4]:
        raise SystemExit('Schritt 3 ist fuer die Plaetze 2-4 gezeichnet, '
                         'Kabelliste: {} / {}'.format(pp, pm))
    # +24 V von oben: Shield, Wandler, Luefter
    ziele = (('W3', 'Shield +', 112, 12), ('W4', 'Wandler IN+', 126, 204),
             ('W5', 'Lüfter +', 126, 404))
    for (nr, an, yq, xv), p, x in zip(ziele, pp, vx):
        _, f = ader(nr, 0, 'Wago +24 V', an)
        o = op[p]
        t += draht([o, (o[0], yq), (xv, yq), (xv, 158), (x, 158)], f)
    # GND von unten, gespiegelt
    ziele = (('W3', 'Shield −', 248, 12), ('W4', 'Wandler IN−', None, None),
             ('W5', 'Lüfter −', 240, 404))
    for (nr, an, yq, xv), p, x in zip(ziele, pm, vx):
        _, f = ader(nr, 1, 'Wago GND', an)
        o = om[p]
        if yq is None:
            t += draht([o, (o[0], 214), (x, 214)], f)
        else:
            t += draht([o, (o[0], yq), (xv, yq), (xv, 214), (x, 214)], f)
    for x in vx:
        t += klemme(x, 158) + klemme(x, 214)
    # Einspeisung und spaetere Schritte an den Enden
    o = op[platz('Wago +24 V', 'W2')]
    t += draht([o, (o[0], 100), (196, 100)], 'rot', 2.0) + klemme(196, 100)
    t += schrittmarke(178, 100, 2) + marke(164, 105, 'W2', 'end')
    o = op[platz('Wago +24 V', 'W16')]
    t += draht([o, (o[0], 100), (440, 100)], 'rot', 2.0) + klemme(440, 100)
    t += schrittmarke(458, 100, 7) + marke(472, 105, 'W16')
    o = om[platz('Wago GND', 'W1')]
    t += draht([o, (o[0], 262), (126, 262)], 'schwarz', 2.0)
    t += klemme(126, 262) + schrittmarke(108, 262, 2) + \
        marke(94, 267, 'W1', 'end')
    rest = wago_rest('Wago GND', 3)
    t += zeilen(396, 312, [' · '.join(rest[:2]), ' · '.join(rest[2:])], 9.5,
                GRAU, 12)
    t += warnung(14, 46, ['Shield-Klemme: Polung', 'neben der Klemme, nicht',
                          'vertauschen.'])
    t += zeilen(452, 48, ['Schraubklemmen mit Ader-',
                          'endhülse, die Wago ohne;',
                          '11 mm abisolieren.'], 10, GRAU, 12.5)
    t += zeilen(426, 244, ['Wandler: IN− und OUT−',
                           'verbunden? (Schritt 3 der',
                           'Anleitung, Masse)'], 9.5, GRAU, 12)
    return feld(3, [('t', 'W3–W5 · dann'), ('p', 'Prüfung C')], t)


# ---- 4. 5 V und Lichtschranken -------------------------------------------

def schritt_lichtschranken():
    ys, yo, yu = 100, 146, 210       # Shield unten, Sensor oben und unten
    adern = [LT[n]['adern'] for n in ('W9', 'W10', 'W11')]
    fb = '{} {}, {} {}, {} {}'.format('VCC', adern[0][0][1], 'GND',
                                      adern[0][1][1], 'D0', adern[0][2][1])
    t = [rechteck(14, 44, 560, 56, *SHIELD),
         text(24, 62, 'CNC Shield V3', 12, TEXT, fett=True),
         text(564, 62, 'Z+ / Z− (D11) = Laser: hier nichts', 10.5, ROT,
              'end', fett=True),
         text(24, 78, 'X+/X− beide D9, Y+/Y− beide D10 · am Modul: ' + fb +
              ', A0 frei', 10, GRAU)]
    # Wago +5 V links (Oeffnungen rechts), Wago GND unten (Oeffnungen oben)
    w5, o5 = wago(60, 126, 'Wago +5 V', 'r', teilung=16, tiefe=38)
    wg, og = wago(126, 274, 'Wago GND', 'o', teilung=24, tiefe=36)
    t += w5 + wg
    t += [text(41, 294, 'Wago +5 V', 10.5, P5, 'middle', fett=True),
          text(41, 307, '5–10 frei', 9.5, GRAU, 'middle'),
          text(362, 292, 'Wago GND', 11, MASSE, fett=True)]
    rest = wago_rest('Wago GND', 4)
    t += zeilen(362, 306, [' · '.join(rest[:2]), ' · '.join(rest[2:])], 9.5,
                GRAU, 12)
    # W6: Stift 5V an die Wago +5 V
    _, f = ader('W6', 0, 'Shield 5V', 'Wago +5 V')
    p = o5[platz('Wago +5 V', 'W6')]
    t += draht([(90, ys), (90, p[1]), p], f)
    t += [text(90, 92, '5V', 10, TEXT, 'middle', fett=True)] + klemme(90, ys)
    sensoren = (('W9', 'X', 'Shield X−', 'X− (D9)', 116),
                ('W10', 'Y', 'Shield Y+', 'Y+ (D10)', 268),
                ('W11', 'Z', 'Shield SpnEn', 'SpnEn (D12)', 420))
    # Wege der VCC-Adern: X und Y links heraus, Z rechts herum und unter
    # der Wago GND durch; die VCC von Y springt ueber die GND von X
    gnd_lage = (252, 244, 260)
    for k, (nr, a, pin, druck, bx) in enumerate(sensoren):
        lt = LT[nr]
        vcc_y, gnd_x, d0_x = 178, bx + 68, bx + 80
        t += [rechteck(bx, yo, 136, yu - yo, FILL, RAND),
              text(d0_x, yo + 14, 'D0', 9.5, GRAU, 'middle'),
              text(gnd_x, yu - 6, 'GND', 9.5, GRAU, 'middle')]
        if a == 'Z':
            t += [text(bx + 130, vcc_y + 4, 'VCC', 9.5, GRAU, 'end'),
                  text(bx + 14, 188, a, 15, BLAU, fett=True),
                  text(bx + 28, 187, 'Lichtschranke', 10, GRAU)]
        else:
            t += [text(bx + 6, vcc_y + 4, 'VCC', 9.5, GRAU),
                  text(bx + 40, 188, a, 15, BLAU, fett=True),
                  text(bx + 54, 187, 'Lichtschranke', 10, GRAU)]
        t += [text(d0_x, 92, druck, 10, BLAU, 'middle', fett=True)]
        # D0 gerade hoch
        _, f = ader(nr, 2, pin, 'LS {} D0'.format(a))
        t += draht([(d0_x, yo), (d0_x, ys)], f)
        t += marke(d0_x, 128, nr, 'middle')
        t.append(text(d0_x + 6 + 5 + 3.5 * len(nr), 128,
                      laenge_text(lt, Q['K']), 10, GRAU))
        # GND hinunter in die Wago GND
        _, f = ader(nr, 1, 'Wago GND', 'LS {} GND'.format(a))
        g = og[platz('Wago GND', nr)]
        t += draht([(gnd_x, yu), (gnd_x, gnd_lage[k]), (g[0], gnd_lage[k]),
                    g], f)
        # VCC an die Wago +5 V
        _, f = ader(nr, 0, 'Wago +5 V', 'LS {} VCC'.format(a))
        v = o5[platz('Wago +5 V', nr)]
        if a == 'X':
            weg = [(bx, vcc_y), (100, vcc_y), (100, v[1]), v]
            t += draht(weg, f)
        elif a == 'Y':
            weg = [(bx, vcc_y), (260, vcc_y), (260, 226), (84, 226),
                   (84, v[1]), v]
            t += draht(weg, f, bruecke=(sensoren[0][4] + 68, 226))
        else:
            weg = [(bx + 136, vcc_y), (570, vcc_y), (570, 330), (72, 330),
                   (72, v[1]), v]
            t += draht(weg, f)
        t += klemme(d0_x, ys) + klemme(d0_x, yo) + klemme(gnd_x, yu) + \
            klemme(weg[0][0], vcc_y)
    return feld(4, [('t', 'W6, W9–W11 · dann'), ('p', 'Prüfung D')], t)


# ---- 5. Laser ------------------------------------------------------------

def schritt_laser():
    t = kasten(14, 46, 184, 96, ['CNC Shield V3', 'Z+ und Z− sind beide',
                                 'D11, die Laser-PWM.'], *SHIELD)
    t += [text(190, 82, 'Z+', 10.5, BLAU, 'end', fett=True),
          text(122, 134, 'Z− S', 9.5, GRAU, 'middle'),
          text(162, 134, 'GND', 9.5, GRAU, 'middle')]
    t += kasten(14, 184, 184, 90, ['Abwärtswandler', 'IN aus Schritt 3',
                                   'OUT auf 12,0 V (C)'], *WANDLER)
    t += [text(190, 210, 'OUT−', 10.5, MASSE, 'end', fett=True),
          text(190, 250, 'OUT+', 10.5, P24, 'end', fett=True)]
    # W8: 10 kOhm von Z− (Signal) an Z− (GND)
    f8, _ = ader('W8', 0, 'Shield Z− S', 'Shield Z− GND')
    t += draht([(122, 142), (122, 160), (162, 160), (162, 142)], '—', 1.6)
    t += [widerstand(142, 160)] + klemme(122, 142) + klemme(162, 142)
    t += marke(112, 165, 'W8', 'end') + [text(82, 165, f8, 10, GRAU,
                                              'end')]
    # W7 zum Laser
    k0, k1 = 272, 398
    t.append(rechteck(k0, 138, k1 - k0, 52, '#e9ecef', '#868e96', 1.2,
                      rx=12))
    spur = {'Laser PWM': 150, 'Laser GND': 164, 'Laser +12 V': 178}
    wege = {'Shield Z+': [(198, 78), (240, 78), (240, 150)],
            'Wandler OUT−': [(198, 206), (228, 206), (228, 164)],
            'Wandler OUT+': [(198, 246), (252, 246), (252, 178)]}
    for i, (_, farbe, von, an) in enumerate(LT['W7']['adern']):
        ader('W7', i, von, an)
        t += draht(wege[von] + [(k1 + 8, spur[an])], farbe)
    t.append(rechteck(k1, 138, 16, 52, '#f8f9fa', STIFT, 1.0, rx=2))
    for y in spur.values():
        t += klemme(k1 + 8, y)
    for p in ((198, 78), (198, 206), (198, 246)):
        t += klemme(*p)
    lt7 = LT['W7']
    t += marke(k0, 130, 'W7') + [text(k0 + 32, 130, litze_kurz(lt7), 10,
                                      GRAU)]
    t.append(text(k0, 206, '{}, Kette {}'.format(laenge_text(lt7, Q['K']),
                                                 lt7['kette']), 10, GRAU))
    # Laser mit XH-Buchse
    reihe = []
    for an in spur:
        m = re.search(r'XH (\w+): (.+)$', vk.ANSCHLUSS[an][0])
        reihe.append(({'links': 0, 'Mitte': 1, 'rechts': 2}[m.group(1)],
                      m.group(2)))
    t += kasten(430, 62, 144, 196, ['Laser', 'LASER TREE 4 W',
                                    '12 V · 1,6 A'], '#eef6ff', '#1864ab',
                dy=20)
    for an, y in spur.items():
        s = re.search(r': (.+)$', vk.ANSCHLUSS[an][0]).group(1)
        t.append(text(438, y + 4, s, 10.5, TEXT, fett=True))
    lx, ly = 500, 128
    t.append(rechteck(lx, ly, 56, 74, '#495057', '#212529', 1, rx=3))
    for k in range(6):
        y = ly + 8 + 11 * k
        t.append(linie([(lx + 6, y), (lx + 50, y)], '#adb5bd', 2))
    t += [el('polygon', {'points': '{},{} {},{} {},{} {},{}'.format(
        lx + 16, ly + 74, lx + 40, ly + 74, lx + 34, ly + 86, lx + 22,
        ly + 86), 'fill': '#868e96'}),
        linie([(lx + 28, ly + 88), (lx + 28, ly + 112)], '#4dabf7', 3)]
    t += zeilen(438, 232, ['XH, von links:', ' · '.join(
        s for _, s in sorted(reihe))], 9.5, GRAU, 12.5)
    t += warnung(214, 274, ['Stecker erst bei Prüfung H aufstecken,',
                            'vorher die Reihenfolge am Aufdruck der',
                            'Laserbuchse prüfen: vertauscht bekäme',
                            'der PWM-Eingang 12 V.'])
    t += zeilen(14, 296, ['W8 hält den Laser aus,', 'solange der Uno '
                          'startet', 'oder ohne USB ist.'], 10, GRAU, 13)
    return feld(5, [('t', 'W7, W8 · Stecker erst bei'), ('p', 'Prüfung H')],
                t)


# ---- 6. Motoren ----------------------------------------------------------

def schritt_motoren():
    t = [rechteck(14, 46, 172, 238, *SHIELD),
         text(24, 66, 'CNC Shield V3', 12, TEXT, fett=True)]
    # Motoren in der Reihenfolge der Treiber; welcher wohin, steht in der
    # Kabelliste (Shield X 2B·2A ...)
    motoren = []
    for achse in ('X', 'Y', 'Z', 'A'):
        nr = next(n for n, lt in LT.items()
                  if lt['adern'][0][2] == 'Shield {} 2B·2A'.format(achse))
        motoren.append((achse, nr))
    xs, xm = 186, 392
    lose = [nr for _, nr in motoren if 'lose' in LT[nr].get('hinweis', '')]
    for i, (achse, nr) in enumerate(motoren):
        lt = LT[nr]
        g = 86 + 52 * i
        pins = [g, g + 11, g + 22, g + 33]
        t += [text(26, g + 22, achse, 17, BLAU, fett=True),
              text(46, g + 21, 'Treiber ' + achse, 10.5, GRAU)]
        if achse == 'A':
            t.append(text(46, g + 34, 'klont Y (Schritt 1)', 10, GRAU))
        for p, s in zip(pins, ('2B', '2A', '1A', '1B')):
            t.append(text(xs - 8, p + 3.5, s, 9.5, GRAU, 'end'))
        # Motor
        t.append(rechteck(xm, g - 6, 182, 46, FILL, RAND))
        _, fa, va, aa = lt['adern'][0]
        _, fb, vb, ab = lt['adern'][1]
        ader(nr, 0, va, aa)
        ader(nr, 1, vb, ab)
        motor_a = re.search(r'Spule A: (.+)$', vk.ANSCHLUSS[aa][0]).group(1)
        motor_b = re.search(r'Spule B: (.+)$', vk.ANSCHLUSS[ab][0]).group(1)
        enden = [s.strip() for s in motor_a.split('·')] + \
            [s.strip() for s in motor_b.split('·')]
        fa, fb = farben(fa), farben(fb)
        # Shield-Stift k geht an den Motorstift mit demselben Namen in
        # der Reihenfolge des Steckers ab Werk; getauscht kreuzen sich die
        # Adern
        ordnung = list(vk.MOTOR_STECKER)
        for k, (p, f) in enumerate(zip(pins, fa + fb)):
            ziel = pins[ordnung.index(enden[k])]
            if ziel == p:
                t += draht([(xs, p), (xm, p)], f)
            else:
                t += draht([(xs, p), (262, p), (292, ziel), (xm, ziel)], f)
        for p, s in zip(pins, ordnung):
            t.append(text(xm + 6, p + 3.5, s, 9.5, GRAU))
        t += [text(xm + 30, g + 11, lt['name'], 12, TEXT, fett=True)]
        if lt.get('kette'):
            t.append(text(xm + 176, g + 11, 'Kette ' + lt['kette'], 9.5,
                          GRAU, 'end'))
        t += marke(xm + 30, g + 29, nr)
        t.append(text(xm + 30 + 10 + 7 * len(nr) + 6, g + 29,
                      laenge_text(lt, Q['K']), 10, GRAU))
        for p in pins:
            t += klemme(xs, p) + klemme(xm, p)
        if 'getauscht' in lt['adern'][0][0]:
            t += warnung(196, g + 48, ['Spule A getauscht: dreht gegen den '
                                       'linken',
                                       '(oder den Stecker um 180° drehen)'])
    g = 86
    sp_a, sp_b = (LT[motoren[0][1]]['adern'][k][0] for k in (0, 1))
    t += [text(289, g + 9, sp_a, 10, TEXT, 'middle', fett=True, halo=True),
          text(289, g + 31, sp_b, 10, TEXT, 'middle', fett=True, halo=True)]
    t += zeilen(14, 300, ['Spule finden: 2–3 Ω zwischen',
                          'ihren Adern. In den Ketten nur',
                          'lose Adern ({}).'.format(', '.join(lose))], 10,
                GRAU, 13)
    return feld(6, [('t', 'W12–W15 · vorher'), ('p', 'Prüfung E'),
                    ('t', 'dann'), ('p', 'F')], t)


# ---- 7. 24-V-Wächter -----------------------------------------------------

def schritt_waechter():
    t = []
    wp, op = wago(60, 84, 'Wago +24 V', 'u', teilung=22, tiefe=34)
    wg, og = wago(60, 280, 'Wago GND', 'o', teilung=22, tiefe=34)
    t += wp + wg
    t += [text(170, 70, 'Wago +24 V', 11, P24, fett=True),
          text(280, 302, 'Wago GND', 11, MASSE, fett=True)]
    (f1_, _, a1, b1), (f2, _, a2, b2) = LT['W16']['adern']
    ader('W16', 0, a1, b1)
    ader('W16', 1, a2, b2)
    p = op[platz('Wago +24 V', 'W16')]
    q = og[platz('Wago GND', 'W16')]
    x, kn = p[0], 170                       # Knoten an Abort
    t += draht([p, (x, 110)], 'rot', 2.0)
    t += draht([(x, 146), (x, kn), (330, kn)], '—', 1.8)
    t.append(widerstand(x, 128, senkrecht=True, lang=32))
    t += draht([(x, kn), (x, 190), (x + 36, 190)], '—', 1.8)
    t += draht([(x, 190), (x, 198)], '—', 1.8)
    t.append(widerstand(x, 214, senkrecht=True, lang=32))
    t += draht([(x + 36, 190), (x + 36, 211)], '—', 1.8)
    t += kondensator(x + 36, 214)
    t += draht([(x + 36, 217), (x + 36, 238)], '—', 1.8)
    t += draht([(x, 230), (x, 238), (q[0], 238), q], 'schwarz', 2.0)
    t += [kreis(x, kn, 3.2, STIFT), kreis(x, 190, 3.2, STIFT),
          kreis(x + 36, 238, 3.2, STIFT)]
    t += [text(x + 12, 124, f1_, 10.5, TEXT, fett=True),
          text(x + 52, 210, f2.split('∥')[0].strip(), 10.5, TEXT,
               fett=True),
          text(x + 52, 224, '∥ ' + f2.split('∥')[1].strip(), 10.5, TEXT,
               fett=True)]
    t += marke(x + 12, 152, 'W16')
    t += kasten(330, 140, 244, 60, ['CNC Shield V3', 'Abort (A0)'], *SHIELD)
    t += klemme(330, kn)
    lo = min(vk.waechter_spannung(24.0 * (1 - vk.NETZ_TOLERANZ), r)
             for r in vk.PULLUP)
    hi = max(vk.waechter_spannung(24.0 * (1 + vk.NETZ_TOLERANZ), r)
             for r in vk.PULLUP)
    aus = max(vk.waechter_spannung(0.0, r) for r in vk.PULLUP)
    t += zeilen(330, 222, [
        'Mit 24 V liegen an A0 {}–{} V: HIGH.'.format(de(lo, 1), de(hi, 1)),
        'Ohne 24 V (Not-Aus, Schalter, Netzteil)',
        'unter {} V: GRBL bricht ab, ALARM, Pn:R.'.format(
            de(math.ceil(aus), 0))], 10.5, TEXT, 14)
    t += warnung(330, 272, ['Nie den NO-Kontakt des Not-Aus an',
                            'A0: dort läge beim Drücken +24 V.'])
    t += zeilen(14, 326, ['Widerstände anlöten, Schrumpfschlauch, '
                          'Dupont 1-polig auf Abort.'], 10, GRAU)
    return feld(7, [('t', 'W16 · geprüft in'), ('p', 'Prüfung I')], t)


# ---- 8. Pi und Inbetriebnahme --------------------------------------------

def schritt_pi():
    usb = '#868e96'
    # W18: an die Loetfahnen der Buchse (vor dem Schalter), zum 5-V-Wandler
    t = kasten(14, 46, 92, 58, ['Buchse', 'Lötfahnen'])
    t += [text(98, 66, '+', 12, P24, 'end', fett=True),
          text(98, 96, '−', 12, MASSE, 'end', fett=True)]
    t += kasten(190, 46, 118, 58, ['5-V-Wandler', '24 → 5 V, ≥ {} A'.format(
        de(ez.PI_WANDLER_A, 0))], '#f8f0fc', P5)
    t += [text(198, 66 + 30, 'IN', 10, GRAU)]
    for i, (a, b, y) in enumerate((('Buchse +', '5V-Wandler IN+', 62),
                                   ('Buchse −', '5V-Wandler IN−', 92))):
        _, f = ader('W18', i, a, b)
        t += draht([(106, y), (190, y)], f)
        t += klemme(106, y) + klemme(190, y)
    t += marke(148, 81, 'W18', 'middle')
    # W19: USB-A rechts am Wandler in PWR IN des Pi
    t += kasten(392, 46, 182, 58, ['Pi Zero 2 W', 'PWR IN · USB (unten)'],
                *SHIELD)
    ader('W19', 0, '5V-Wandler USB', 'Pi PWR')
    t += draht([(308, 75), (392, 75)], usb, 5)
    t += klemme(308, 75) + klemme(392, 75)
    t += marke(350, 71, 'W19', 'middle')
    # W17: USB des Pi zum Uno
    t += kasten(392, 132, 182, 40, ['Uno', 'USB-B, hinten im Fenster'],
                *SHIELD)
    ader('W17', 0, 'Pi USB', 'Uno USB')
    t += draht([(483, 104), (483, 132)], usb, 5)
    t += klemme(483, 104) + klemme(483, 132)
    t += marke(493, 123, 'W17')
    t += zeilen(14, 128, ['Vor Schalter und Not-Aus: Pi und Uno',
                          'laufen weiter, der Wächter W16 meldet.',
                          'W17 in „USB“, W19 in „PWR IN“.'], 10.5, GRAU,
                13.5)
    # Einschaltreihenfolge
    t.append(text(14, 190, 'Einschalten', 12, TEXT, fett=True))
    for k, (s_, x) in enumerate((('Netzteil: Pi und Uno starten', 14),
                                 ('Schalter EIN: 24 V', 262))):
        t += schrittmarke(x + 8, 206, k + 1)
        t.append(text(x + 20, 210, s_, 11, TEXT))
    t += [linie([(212, 206), (254, 206)], GRAU, 1.4),
          el('polygon', {'points': '254,206 248,203 248,209',
                         'fill': GRAU}),
          text(420, 210, 'aus: umgekehrt, den Pi', 10.5, GRAU),
          text(420, 223, 'vorher herunterfahren', 10.5, GRAU)]
    # Inbetriebnahme
    t.append(text(14, 246, 'Inbetriebnahme, Prüfungen der Anleitung', 12,
                  TEXT, fett=True))
    wann = {'A': 'nach 2', 'B': 'nach 2', 'C': 'nach 3', 'D': 'nach 4',
            'E': 'vor 6', 'F': 'nach 6', 'J': 'nach 8'}
    for i, (b, titel) in enumerate(PRUEFUNGEN):
        x, y = (14, 266 + 15.5 * i) if i < 5 else (300, 266 + 15.5 * (i - 5))
        t += pruefung(x, y, b)
        t.append(text(x + 26, y, titel, 10.5, TEXT))
        if b in wann:
            t.append(text(x + 274, y, wann[b], 10, GRAU, 'end'))
    return feld(8, [('t', 'W17–W19 · dann'), ('p', 'Prüfung J')], t)


# ---- Uebersicht: Leitungen aus dem Gehaeuse ------------------------------

def uebersicht():
    t = [rechteck(0, 0, W - 2 * RX, UEB_H, '#ffffff', '#d0d7de', 1.0, rx=8),
         text(16, 28, 'Übersicht — welche Leitung wohin', 14.5, TEXT,
              fett=True),
         text(16, 46, 'Draufsicht, schematisch: hinten oben, vorn unten. '
              'Maßstäblich: elektronik-platz.svg', 11, GRAU)]
    px, cx, yh = 0.52, 330.0, 104.0      # px/mm, Mitte, hinteres Ende

    def X(mm):
        return cx + mm * px

    def Y(mm):                       # ab hinterem Ende der 2040, nach vorn
        return yh + mm * px

    def quader(x0, x1, y0, y1, fill, rand, b=1.0, rx=2):
        return rechteck(X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0), fill,
                        rand, b, rx=rx)

    profil = ('#e9ecef', '#868e96')
    kette = ('#ced4da', '#495057')
    t += [quader(-300, 300, 110, 130, *profil),
          quader(-300, 300, 545, 565, *profil),
          quader(-267, -247, 0, 600, *profil),
          quader(247, 267, 0, 600, *profil),
          quader(-205, -45, 12, 100, GEH_FILL, GEH_RAND, 1.4, rx=3),
          text(X(-125), Y(60), 'Gehäuse', 11, GEH_RAND, 'middle', fett=True),
          quader(-287, -273, 262, 420, *kette, rx=3),
          quader(0, 215, 306, 320, *kette, rx=3),
          quader(-250, 250, 320, 340, *profil),
          quader(-287, -227, 300, 370, '#dbe4ef', '#6b84a3'),
          quader(227, 287, 300, 370, '#dbe4ef', '#6b84a3'),
          quader(-25, 25, 340, 400, '#dbe4ef', BLAU),
          quader(-225, -183, 296, 338, '#ced4da', STIFT),
          quader(-278, -236, 606, 648, '#ced4da', STIFT),
          quader(236, 278, 606, 648, '#ced4da', STIFT),
          quader(150, 210, 574, 606, '#fff4f4', P24, 1.2, rx=3),
          kreis(X(180), Y(590), 5.5, '#e03131')]
    for x, y in ((-170, 352), (-27, 372), (285, 40)):
        t.append(kreis(X(x), Y(y), 4.5, ROT))
    # Wege (wie in verkabelung.md, Kabelwege und Ketten)
    weg = dict(farbe=KABELWEG, b=2.0, strich='6 3')
    xl, xr, yk = X(-300), X(285), Y(105)
    t += [linie([(X(-205), Y(56)), (xl, Y(56)), (xl, Y(627)),
                 (X(-278), Y(627))], **weg),
          linie([(xl, Y(262)), (X(-287), Y(262))], **weg),
          linie([(X(-227), Y(312)), (X(0), Y(312))], **weg),
          linie([(X(-204), Y(312)), (X(-204), Y(296))], **weg),
          linie([(X(-170), Y(312)), (X(-170), Y(347))], **weg),
          linie([(X(12), Y(320)), (X(12), Y(340))], **weg),
          linie([(X(-110), Y(100)), (X(-110), yk), (xr, yk), (xr, Y(627)),
                 (X(278), Y(627))], **weg),
          linie([(xr, Y(40)), (xr, yk)], **weg),
          linie([(xr, Y(570)), (X(210), Y(570)), (X(210), Y(580))], **weg)]
    # Netzteil hinter dem Gehaeuse; Pi-Halter rechts neben dem Kasten an
    # der Rueckseite des hinteren 2060 (PiHalter.py), das USB-Kabel W17 um
    # den Kasten herum ins Fenster hinten
    t += kasten(X(-75) - 50, 58, 100, 24, ['Steckernetzteil'], gr=10.5,
                dy=16, dx=8)
    t += [linie([(X(-75), 82), (X(-75), Y(12))], P24, 2.0)]
    t += [quader(-18, 157, 90, 110, '#fff4e6', '#d9480f', 1.2, rx=2),
          text(X(70), Y(100) + 4, 'Pi', 10, '#d9480f', 'middle', fett=True)]
    t += [linie([(X(110), Y(90)), (X(110), Y(84)), (X(-38), Y(84)),
                 (X(-38), Y(4)), (X(-160), Y(4)), (X(-160), Y(12))],
                '#495057', 2.0)]
    t += marke(X(-38) + 6, Y(40), 'W17')

    def schild(x, y, nr, s, anker='start'):
        """Leitungsnummer und Name an einem Geraet."""
        b = 10.0 + 7.0 * len(nr)
        if anker == 'end':
            return marke(x, y, nr, 'end') + [
                text(x - b - 6, y, s, 10.5, TEXT, 'end')]
        return marke(x, y, nr) + [text(x + b + 6, y, s, 10.5, TEXT)]

    ky = ' '.join(lt['nr'] for lt in LTS
                  if 'Y' in lt.get('kette', '').split())
    kx = ' '.join(lt['nr'] for lt in LTS
                  if 'X' in lt.get('kette', '').split())
    t += [text(xl - 10, Y(53), 'links raus, unter dem', 10.5, GRAU, 'end'),
          text(xl - 10, Y(53) + 13, '2040 durch, untere Nut', 10.5, GRAU,
               'end'),
          text(xl - 10, Y(300), 'Y-Kette:', 10.5, GRAU, 'end'),
          text(xl - 10, Y(300) + 13, ky, 10.5, TEXT, 'end'),
          text(X(108), Y(298), 'X-Kette: ' + kx, 10, GRAU, 'middle',
               halo=True)]
    t += schild(X(-278) - 6, Y(632), 'W13', 'Y-Motor links', 'end')
    t += schild(X(-225), Y(284), 'W12', 'X-Motor')
    t += [linie([(X(-176), Y(352)), (xl - 4, Y(352))], GRAU, 0.8)]
    t += schild(xl - 10, Y(352) + 4, 'W9', 'Lichtschranke X', 'end')
    t += marken_reihe(X(0), Y(426), [lt['nr'] for lt in LTS
                                     if 'X' in lt.get('kette', '').split()])
    t.append(text(X(0), Y(448), 'Toolhead: Laser, Lichtschranke Z, Z-Motor',
                  9.5, GRAU, 'middle'))
    t += schild(xr + 14, Y(40) + 4, 'W10', 'Lichtschranke Y')
    t += [text(xr + 14, Y(150), 'vorn raus, Kanal,', 10.5, GRAU),
          text(xr + 14, Y(150) + 13, 'Rückseite hinteres 2060,', 10.5, GRAU),
          text(xr + 14, Y(150) + 26, 'untere Nut rechts', 10.5, GRAU)]
    t += schild(xr + 14, Y(612), 'W14', 'Y-Motor rechts')
    t += schild(X(150) - 8, Y(598), 'W2', 'Not-Aus', 'end')
    t += marke(X(20), Y(72), 'W18') + [
        text(X(20) + 40, Y(72), 'Pi-Halter', 10.5, TEXT)]

    # Kabelliste der Leitungen, die das Gehaeuse verlassen
    kx0 = 676
    sp = (kx0, kx0 + 42, kx0 + 154, kx0 + 330, kx0 + 438)
    t.append(text(kx0, 76, 'Leitungen aus dem Gehäuse', 12, TEXT, fett=True))
    for x, s in zip(sp[1:], ('Leitung', 'Litze', 'Länge', 'Kette')):
        t.append(text(x, 96, s, 10.5, GRAU))
    t.append(linie([(kx0, 103), (W - 2 * RX - 16, 103)], '#d0d7de', 1))
    aussen = [lt for lt in LTS if not lt['weg'].startswith(
        ('im Kasten', 'auf dem', 'am Pi-Halter'))]
    for i, lt in enumerate(aussen):
        y = 122 + 21 * i
        t += marke(kx0, y, lt['nr'])
        t += [text(sp[1], y, lt['name'], 11, TEXT),
              text(sp[2], y, litze_kurz(lt), 10.5, TEXT),
              text(sp[3], y, laenge_text(lt, Q['K']) or '—', 10.5, TEXT),
              text(sp[4], y, lt.get('kette', '') or '—', 10.5, GRAU)]
    innen = [lt['nr'] for lt in LTS
             if lt['weg'].startswith(('im Kasten', 'auf dem'))]
    halter = [lt['nr'] for lt in LTS if lt['weg'].startswith('am Pi-Halter')]
    y = 122 + 21 * len(aussen) + 6
    t += zeilen(kx0, y, [
        'Im Gehäuse: {}. Am Pi-Halter: {}.'.format(nrn_text(innen),
                                                   nrn_text(halter)),
        'In den Ketten nur Einzellitzen, keine Mantelleitung; Motorkabel',
        'ohne Schlauch. „Länge“: Weg → kaufen (+{} %, aufgerundet).'.format(
            de(ez.RESERVE * 100, 0))], 10.5, GRAU)
    return t


# ---- Rahmen der ganzen Zeichnung -----------------------------------------

def legende(y):
    t, x = [], RX
    for s in ('rot', 'schwarz', 'weiß', 'gelb', 'grün', 'blau'):
        t += draht([(x, y - 4), (x + 22, y - 4)], s, 2.6)
        t.append(text(x + 28, y, s, 11))
        x += 28 + breite(s, 11) + 18
    t += [linie([(x, y - 4), (x + 22, y - 4)], KABELWEG, 2.0, '6 3'),
          text(x + 28, y, 'Kabelweg', 11)]
    x += 28 + breite('Kabelweg', 11) + 18
    t += marke(x, y, 'W7') + [text(x + 30, y, 'Leitung', 11)]
    x += 30 + breite('Leitung', 11) + 18
    t += schrittmarke(x + 8, y - 4, 3) + [text(x + 22, y, 'Schritt', 11)]
    x += 22 + breite('Schritt', 11) + 18
    t += pruefung(x, y, 'C') + [text(x + 26, y, 'Prüfung', 11)]
    x += 26 + breite('Prüfung', 11) + 18
    t += warndreieck(x, y - 12) + [text(x + 23, y, 'Achtung', 11)]
    return t


Q = {}                           # Kabelwege (vk.laden), in main gesetzt


def main():
    Q.update(vk.laden())
    nrn = [s for s, _, _ in SCHRITTE]
    if nrn != list(range(1, 9)):
        raise SystemExit('Die Zeichnung hat acht Schritte, die Anleitung '
                         '{}'.format(nrn))
    t = [text(RX, 38, 'Verkabelung Schritt für Schritt — jede Ader von '
              'Klemme zu Klemme', 19, TEXT, fett=True),
         text(RX, 60, 'Leitungen W1–W{} wie in verkabelung.md, Farben wie '
              'in der Anschlussliste. Schematisch, nicht maßstäblich; '
              'Wago-Plätze in der Reihenfolge der Tabelle „Klemmen“.'.format(
                  len(LTS)), 11.5, GRAU),
         text(RX, 77, 'Alles stromlos verdrahten, nichts unter Spannung '
              'an- oder abstecken. Einschalten: erst Netzteil (Pi und Uno '
              'starten), dann Schalter EIN.', 11.5, GRAU)]
    t += legende(102)
    y = 118
    t.append(gruppe(RX, y, uebersicht()))
    y += UEB_H + LUECKE
    felder = (schritt_vorbereiten, schritt_24v, schritt_verteilen,
              schritt_lichtschranken, schritt_laser, schritt_motoren,
              schritt_waechter, schritt_pi)
    for i, fn in enumerate(felder):
        _SCHRITT[0] = i + 1
        x = RX + (i % 2) * (PB + LUECKE)
        t.append(gruppe(x, y + (i // 2) * (PH + LUECKE), fn()))
    # jede Ader genau einmal, im Schritt der Anleitung
    fehlt = ['{} Ader {}'.format(lt['nr'], i + 1) for lt in LTS
             for i in range(len(lt['adern']))
             if (lt['nr'], i) not in GEZEICHNET]
    falsch = ['{} in Schritt {}'.format(nr, s)
              for (nr, _), s in GEZEICHNET.items() if SCHRITT_VON[nr] != s]
    if fehlt or falsch:
        raise SystemExit('nicht gezeichnet: {}; im falschen Schritt: '
                         '{}'.format(fehlt, falsch))
    H = int(y + 4 * (PH + LUECKE) - LUECKE + RX)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif"><rect width="{0}" height="{1}" fill="#ffffff"/>'
           .format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)
    print('  {} Adern aus {} Leitungen gezeichnet, jede genau einmal'.format(
        len(GEZEICHNET), len(LTS)))


if __name__ == '__main__':
    main()
