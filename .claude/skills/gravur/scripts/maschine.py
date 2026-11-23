"""Feste Werte der Maschine fuer die Gravur-Skripte.

Quellen im Repo (Stand 2026-11-23):
  docs/spannmittel.md   Nullpunkt G54 = Innenecke des Anschlagwinkels vorn
                        rechts; das Werkstueck liegt bei X <= 0, Y >= 0
  docs/opferplatte.md   Arbeitsfeld 391 x 285 mm, Werkstueck bis 32 mm dick
  docs/verkabelung.md   GRBL-Tabelle: $30=1000, $32=1, $130=385, $131=282
  docs/autofokus.md     Messpunkt des Autofokus G54 X-30 Y58
  2026-11-18 an der Maschine gesetzt (nicht in der Doku-Tabelle):
                        $110=$111=3000 mm/min, $120=$121=500 mm/s^2

Koordinaten wie GRBL: X+ nach rechts, Y+ nach hinten (von vorn gesehen).
"""

import json
import os

HIER = os.path.dirname(os.path.abspath(__file__))

S_MAX = 1000.0          # $30: S1000 = volle Leistung
F_MAX = 3000.0          # $110/$111 mm/min
BESCHL = 500.0          # $120/$121 mm/s^2
JD = 0.01               # $11 Junction Deviation (GRBL-Standard)

# Arbeitsfeld relativ zum Nullpunkt G54, aus dem Modell (Portal Rev. 36,
# $130=385, $131=282). Gilt nur, wenn G54 an der Anschlagecke sitzt.
# An der Maschine stand $130 am 2026-11-18 auf 367: dann endet das Feld
# rechts womoeglich frueher. Genau sagt es nur der Zustand vom Pi.
FELD_X = (-387.2, 4.0)
FELD_Y = (-4.0, 281.0)

DICKE_MAX = 32.0            # mm Werkstueck unter dem Toolhead
AUTOFOKUS = (-30.0, 58.0)   # Messpunkt in G54 (Werkstueck muss ihn bedecken)
ANSCHLAG_SCHENKEL = 50.0    # Anschlagwinkel: Schenkel 50 lang, 10 breit, 3 hoch
ANSCHLAG_BREITE = 10.0
NIEDERHALTER_RAND = 6.0     # mm Gravur bis Werkstueckrand, wo ein Niederhalter sitzt

URSPRUENGE = ('vorn-rechts', 'vorn-links', 'hinten-rechts', 'hinten-links', 'mitte')


def materialien():
    with open(os.path.join(HIER, 'materialien.json'), encoding='utf-8') as d:
        daten = json.load(d)
    return {k: v for k, v in daten.items() if not k.startswith('_')}


def ursprung_punkt(ursprung, b, t):
    """Lage des Nullpunkts im Werkstueck (x nach rechts ab linker Kante,
    y nach hinten ab vorderer Kante)."""
    if ursprung == 'mitte':
        return b / 2.0, t / 2.0
    x = b if 'rechts' in ursprung else 0.0
    y = t if 'hinten' in ursprung else 0.0
    return x, y


def werkstueck_g54(b, t, ursprung):
    """Werkstueck als (xmin, xmax, ymin, ymax) in G54."""
    ox, oy = ursprung_punkt(ursprung, b, t)
    return (-ox, b - ox, -oy, t - oy)


def feld_aus_pi(zustand):
    """Arbeitsfeld in G54 aus dem Zustand vom Pi (grbl_lesen.js).

    GRBL rechnet den Maschinenraum negativ: X von -$130 bis 0, Y von -$131
    bis 0. G54 = Maschinenposition - WCO. Gibt None, wenn etwas fehlt."""
    try:
        e = zustand['einstellungen']
        wco = zustand['wco']
        x130, x131 = float(e['$130']), float(e['$131'])
        return ((-x130 - wco['x'], -wco['x']), (-x131 - wco['y'], -wco['y']))
    except (KeyError, TypeError, ValueError):
        return None


def grenzen(zustand=None):
    """S_MAX, F_MAX, BESCHL, JD, Feld und Quelle; vom Pi, sonst aus der Doku."""
    g = {'s_max': S_MAX, 'f_max': F_MAX, 'beschl': BESCHL, 'jd': JD,
         'feld': (FELD_X, FELD_Y), 'quelle': 'Doku/Modell'}
    if not zustand:
        return g
    e = zustand.get('einstellungen') or {}

    def wert(k, std):
        try:
            return float(e[k])
        except (KeyError, TypeError, ValueError):
            return std
    g['s_max'] = wert('$30', S_MAX)
    g['f_max'] = min(wert('$110', F_MAX), wert('$111', F_MAX))
    g['beschl'] = min(wert('$120', BESCHL), wert('$121', BESCHL))
    g['jd'] = wert('$11', JD)
    feld = feld_aus_pi(zustand)
    if feld:
        g['feld'] = feld
        g['quelle'] = 'Pi %s' % zustand.get('zeit', '')
    return g
