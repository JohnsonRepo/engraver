#!/usr/bin/env python3
"""Erzeugt docs/toolhead-z-layout.svg — maßstaebliche Seiten- und
Vorderansicht der Baugruppe ToolheadZ, direkt aus den Massen des
Fusion-Skripts. Zeichnung und Pruefung koennen so nicht auseinanderlaufen.

    python3 tools/layout_zeichnen.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'toolhead-z-layout.svg')

S = 2.1                      # px je mm
RAND = 16
ANZEIGE = {          # Anzeigenamen (bauraum.py haelt die Schluessel in ASCII)
    'Traegerplatte Hauptsaeule': 'Trägerplatte Hauptsäule',
    'Traegerplatte Kopf': 'Trägerplatte Kopf',
    'Saeulenrippe links': 'Säulenrippe links',
    'Saeulenrippe rechts': 'Säulenrippe rechts',
    'Winkel Ruecken': 'Mutternwinkel: Rücken',
    'Winkel Regal': 'Mutternwinkel: Regal',
    'Antriebsmutter Tr8x2': 'Antriebsmutter Tr8×2 (Garnitur)',
    'Tr8x2-Spindel': 'Tr8×2-Spindel',
    'Gabel hinten': 'Gabel: Arm hinten',
    'Gabel vorn': 'Gabel: Arm vorn',
    'Gabel Boden': 'Gabel: Boden des Schlitzes',
    'Schaltfahne Fuss': 'Schaltfahne: Fuß',
    'Schaltfahne Steg': 'Schaltfahne: Steg',
    'Schaltfahne': 'Schaltfahne: Blatt',
}
FARBE = {
    'druck':    ('#c9d9ec', '#2f5d92'),      # gedruckte Teile
    'kaufteil': ('#e8ded0', '#8a6d3b'),      # Kaufteile
    'fuehrung': ('#d7d7dc', '#55555e'),      # Schiene / Wagen
}
def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Ansicht:
    """Eine orthogonale Ansicht: waagerecht `h`, senkrecht immer Z."""

    def __init__(self, titel, achse_h, grenzen, ox):
        self.titel, self.achse_h = titel, achse_h
        (self.h0, self.h1), (self.z0, self.z1) = grenzen
        self.ox = ox
        self.belegt = []          # gesetzte Nummernkreise, gegen Ueberlappung
        self.breite = (self.h1 - self.h0) * S
        self.hoehe = (self.z1 - self.z0) * S

    def px(self, h, z):
        return (self.ox + (h - self.h0) * S,
                RAND + 34 + (self.z1 - z) * S)

    def rect(self, q, gestrichelt=False):
        h = getattr(q, self.achse_h)
        x0, y0 = self.px(h[0], q.z[1])
        x1, y1 = self.px(h[1], q.z[0])
        fill, stroke = FARBE[q.art]
        if gestrichelt:
            return ('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" '
                    'fill="none" stroke="{}" stroke-width="0.9" '
                    'stroke-dasharray="4 3" opacity="0.75"/>').format(
                        x0, y0, x1 - x0, y1 - y0, stroke)
        deck = 0.45 if q.art == 'kaufteil' else 0.95
        return ('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" '
                'fill="{}" fill-opacity="{}" stroke="{}" '
                'stroke-width="0.9"/>').format(
                    x0, y0, x1 - x0, y1 - y0, fill, deck, stroke)

    def nummer(self, q, n):
        """Positionsnummer im Kreis — Text im Bauteil wuerde bei so vielen
        ueberlappenden Quadern unleserlich werden."""
        h = getattr(q, self.achse_h)
        x, y = self.px((h[0] + h[1]) / 2.0, (q.z[0] + q.z[1]) / 2.0)
        while any(abs(x - bx) < 14 and abs(y - by) < 14
                  for bx, by in self.belegt):
            y += 14.5
        self.belegt.append((x, y))
        return ('<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="#ffffff" '
                'stroke="#1c2733" stroke-width="0.8"/>'
                '<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
                'dominant-baseline="central" font-size="8" '
                'font-weight="600" fill="#1c2733">{n}</text>').format(
                    x=x, y=y, n=n)


def masslinie(a, h, z0, z1, text, seite=1):
    """Senkrechte Masslinie bei h mit Text."""
    x, y0 = a.px(h, z0)
    _, y1 = a.px(h, z1)
    return (
        '<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}" '
        'stroke="#b4342f" stroke-width="0.8"/>'
        '<line x1="{xa:.1f}" y1="{y0:.1f}" x2="{xb:.1f}" y2="{y0:.1f}" '
        'stroke="#b4342f" stroke-width="0.8"/>'
        '<line x1="{xa:.1f}" y1="{y1:.1f}" x2="{xb:.1f}" y2="{y1:.1f}" '
        'stroke="#b4342f" stroke-width="0.8"/>'
        '<text x="{xt:.1f}" y="{ym:.1f}" font-size="8.5" fill="#b4342f" '
        'text-anchor="{anc}" dominant-baseline="middle">{t}</text>').format(
            x=x, y0=y0, y1=y1, xa=x - 3, xb=x + 3,
            xt=x + 5 * seite, ym=(y0 + y1) / 2.0,
            anc='start' if seite > 0 else 'end', t=esc(text))


def hoehenlinie(a, z, text, bis_h):
    """Waagerechte Hilfslinie auf Hoehe z mit Beschriftung."""
    x0, y = a.px(a.h0, z)
    x1, _ = a.px(bis_h, z)
    return ('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
            'stroke="#8c96a3" stroke-width="0.6" stroke-dasharray="2 3"/>'
            '<text x="{:.1f}" y="{:.1f}" font-size="7.5" fill="#5b6472" '
            'dominant-baseline="middle">{}</text>').format(
                x0, y, x1, y, x1 + 3, y, esc(text))


def main():
    mod = bauraum.modul_laden()
    w, L = mod.w, mod.lage()
    feste, bewegte, _ = bauraum.bauraeume(w, L)
    zc_u, zc_o = L['zc_min'], L['zc_max']

    z0 = min(min(q.z[0] for q in feste),
             min(q.z[0] for q in bewegte) + zc_u) - 4
    z1 = max(max(q.z[1] for q in feste),
             max(q.z[1] for q in bewegte) + zc_o) + 4
    y0 = min(q.y[0] for q in feste) - 4
    y1 = max(max(q.y[1] for q in feste),
             max(q.y[1] for q in bewegte)) + 30
    x0 = min(min(q.x[0] for q in feste), min(q.x[0] for q in bewegte)) - 4
    x1 = max(max(q.x[1] for q in feste), max(q.x[1] for q in bewegte)) + 62

    seite = Ansicht('Seitenansicht (Blick entlang X)', 'y', ((y0, y1), (z0, z1)),
                    RAND)
    vorn = Ansicht('Vorderansicht (Blick entlang Y)', 'x', ((x0, x1), (z0, z1)),
                   RAND + seite.breite + 58)

    # Positionsliste: Zeilenzahl steht vor der Leinwandhoehe, sonst laeuft
    # die Liste unten aus dem Bild (sie waechst mit jedem neuen Bauraum).
    namen = [q.name for q in feste] + [q.name for q in bewegte]
    spalten = 3
    pro = (len(namen) + spalten - 1) // spalten

    breite = vorn.ox + vorn.breite + RAND
    hoehe = RAND + 34 + seite.hoehe + 74 + pro * 11

    t = ['<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" '
         'height="{:.0f}" viewBox="0 0 {:.0f} {:.0f}" '
         'font-family="Inter, Helvetica, Arial, sans-serif">'.format(
             breite, hoehe, breite, hoehe),
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         '<text x="{}" y="20" font-size="13" font-weight="600" fill="#1c2733">'
         'Toolhead Z-Achse — Laser auf MGN9, NEMA 17 mit Tr8x2-Spindel'
         '</text>'.format(RAND),
         '<text x="{}" y="32" font-size="8.5" fill="#5b6472">Ursprung = Mitte '
         'des X-Wagen-Lochbildes auf seiner Stirnfläche · Maßstab '
         '{:.2f} px/mm · erzeugt aus ToolheadZ.py</text>'.format(RAND, S)]

    for a in (seite, vorn):
        t.append('<text x="{:.1f}" y="{:.1f}" font-size="10" '
                 'font-weight="600" fill="#2f5d92">{}</text>'.format(
                     a.ox, RAND + 26, esc(a.titel)))
        # Nullkreuz
        xo, yo = a.px(0, 0)
        t.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
                 'stroke="#b4342f" stroke-width="0.7"/>'.format(
                     xo - 7, yo, xo + 7, yo))
        t.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
                 'stroke="#b4342f" stroke-width="0.7"/>'.format(
                     xo, yo - 7, xo, yo + 7))
        for q in feste:
            t.append(a.rect(q))
        for q in bewegte:                       # oberste Stellung: gestrichelt
            t.append(a.rect(q.verschoben(zc_o), gestrichelt=True))
        for q in bewegte:                       # tiefste Stellung: ausgefuellt
            t.append(a.rect(q.verschoben(zc_u)))
        for i, q in enumerate(feste):
            t.append(a.nummer(q, i + 1))
        for i, q in enumerate(bewegte):
            t.append(a.nummer(q.verschoben(zc_u), len(feste) + i + 1))

    # Y-Kette als beschriftete Hilfslinien in der Seitenansicht
    for wert, txt in (
            (0.0, 'X-Wagen-Stirnfläche  Y=0'),
            (L['traeger_y1'], 'Trägerplatte vorn  Y={:+.0f}'.format(L['traeger_y1'])),
            (L['sockel_y1'], 'Z-Schiene auf  Y={:+.0f}'.format(L['sockel_y1'])),
            (L['z_wagen_y'], 'Z-Wagen  Y={:+.0f}'.format(L['z_wagen_y'])),
            (L['laser_y'], 'Laser  Y={:+.0f}'.format(L['laser_y'])),
            (L['strahl_y'], 'Strahlachse  Y={:+.1f}'.format(L['strahl_y']))):
        x, ytop = seite.px(wert, z1)
        _, ybot = seite.px(wert, z0)
        t.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
                 'stroke="#7a8a9e" stroke-width="0.5" '
                 'stroke-dasharray="2 4"/>'.format(x, ytop, x, ybot + 2))
        t.append('<text x="{:.1f}" y="{:.1f}" font-size="7.5" fill="#5b6472" '
                 'transform="rotate(-90 {:.1f} {:.1f})" '
                 'text-anchor="start">{}</text>'.format(
                     x + 3, ybot + 6, x + 3, ybot + 6, esc(txt)))

    # Verfahrweg als Mass in der Vorderansicht
    t.append(masslinie(vorn, x1 - 40, zc_u, zc_o,
                       'Z-Weg {:.1f}'.format(L['z_weg'])))
    t.append(hoehenlinie(vorn, L['konsole_z0'],
                         'Konsole {:+.0f}'.format(L['konsole_z0']), x1 - 52))
    t.append(hoehenlinie(vorn, L['kupplung_z0'],
                         'Kupplung {:+.0f}'.format(L['kupplung_z0']), x1 - 52))
    t.append(hoehenlinie(vorn, zc_u + L['laser_unten_rel'],
                         'Linse tief {:+.0f}'.format(zc_u + L['laser_unten_rel']),
                         x1 - 52))

    # Legende
    ly = RAND + 34 + seite.hoehe + 24
    t.append('<text x="{}" y="{:.1f}" font-size="9" font-weight="600" '
             'fill="#1c2733">Legende</text>'.format(RAND, ly))
    for i, (art, txt) in enumerate((
            ('druck', 'gedrucktes Teil (PETG)'),
            ('fuehrung', 'Linearführung (Schiene / Wagen)'),
            ('kaufteil', 'Kaufteil'))):
        fill, stroke = FARBE[art]
        t.append('<rect x="{}" y="{:.1f}" width="16" height="10" fill="{}" '
                 'stroke="{}" stroke-width="0.9"/>'.format(
                     RAND + i * 210, ly + 10, fill, stroke))
        t.append('<text x="{}" y="{:.1f}" font-size="8.5" fill="#1c2733" '
                 'dominant-baseline="middle">{}</text>'.format(
                     RAND + i * 210 + 21, ly + 15.5, esc(txt)))
    t.append('<line x1="{}" y1="{:.1f}" x2="{}" y2="{:.1f}" stroke="#2f5d92" '
             'stroke-width="0.9" stroke-dasharray="4 3"/>'.format(
                 RAND, ly + 32, RAND + 16, ly + 32))
    t.append('<text x="{}" y="{:.1f}" font-size="8.5" fill="#1c2733" '
             'dominant-baseline="middle">bewegte Gruppe oben (zc={:+.1f}); '
             'ausgefüllt = tiefste Stellung (zc={:+.1f})</text>'.format(
                 RAND + 21, ly + 32, zc_o, zc_u))

    # Positionsliste
    for i, name in enumerate(namen):
        sp, zeile = i // pro, i % pro
        t.append('<text x="{:.0f}" y="{:.1f}" font-size="8" fill="#1c2733">'
                 '{}&#160;&#160;{}</text>'.format(
                     RAND + sp * 210, ly + 52 + zeile * 11, i + 1,
                     esc(ANZEIGE.get(name, name))))
    t.append('</svg>')

    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(t))
    print('geschrieben: {}  ({:.0f} x {:.0f} px)'.format(
        os.path.relpath(ZIEL), breite, hoehe))


if __name__ == '__main__':
    main()
