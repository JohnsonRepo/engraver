#!/usr/bin/env python3
"""Skizze des Z-Antriebs: Motor, Kupplung, Spindel, Garnitur, Mutternwinkel.

Zwei Seitenansichten, geschnitten durch die Spindelachse (Schlitten ganz
unten und ganz oben), eine vergroesserte Einzelheit des Flanschsitzes und eine
Draufsicht auf das Regal. Alle Masse kommen aus ToolheadZ.py; die Skizze ist
also massstaeblich und wandert mit den Parametern.

    python3 tools/antrieb_zeichnen.py   ->  docs/toolhead-z-antrieb.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'toolhead-z-antrieb.svg')

S = 2.0                     # px/mm in den Seitenansichten
S_DETAIL = 5.0              # px/mm in der Einzelheit A
S_DRAUF = 4.0               # px/mm in der Draufsicht
Y_BEREICH = (-6.0, 62.0)    # Maschinen-Y in den Seitenansichten
Z_BEREICH = (-72.0, 212.0)  # Maschinen-Z
OBEN = 80                   # Platz fuer Titel
# Ausschnitt der Einzelheit A, relativ zu Spindelachse und Regaloberseite
DETAIL_Y = (-12.5, 13.5)
DETAIL_Z = (-14.0, 10.0)
# Ausschnitt der Draufsicht in Maschinen-X und -Y
DRAUF_X = (12.0, 48.0)
DRAUF_Y = (0.0, 43.0)

# Masse, die keine Druckteilgeometrie treiben und deshalb nicht in MASSE
# stehen — nur fuer das Bild:
BUND_D, BUND_H = 10.0, 2.0     # Zentrierbund der Flanschmutter [v] am Teil
GLEIT_D, GLEIT_H = 14.0, 15.0  # Gleitmutter [w] (hardware-notizen.md)
KOPF_D, KOPF_H = 5.5, 3.0      # M3-Zylinderkopf DIN 912
SCHAFT_D = 3.0
WELLE_D = 5.0                  # NEMA 17
MGN_H1 = 2.0                   # MGN9: Wagenunterkante ueber der Auflage
N_FEDER = 9                    # Zickzack-Striche der Feder

FARBE = {
    'druck':   ('#c9d9ec', '#2f5d92'),
    'kauf':    ('#e8ded0', '#8a6d3b'),
    'stahl':   ('#c3c8cf', '#4a4f57'),
    'messing': ('#e3c46b', '#8a6d1b'),
    'hinten':  ('#eef2f7', '#a9b6c8'),
}
TEXT = '#1c2733'
GRAU = '#5b6472'
BLAU = '#2f5d92'
BRAUN = '#8a6d3b'
ROT = '#b4342f'


# ---- SVG-Bausteine ----------------------------------------------------------

def de(x, stellen=1, vorzeichen=False):
    """Zahl mit Dezimalkomma und echtem Minus, wie in der restlichen Doku.
    Nullen am Ende fallen weg: 36,50 -> 36,5, 3,0 -> 3."""
    s = (('{:+.%df}' if vorzeichen else '{:.%df}') % stellen).format(x)
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s.replace('.', ',').replace('-', '−')


def f1(x):
    return '{:.1f}'.format(x)


def el(tag, attrs, inhalt=None):
    """SVG-Element. Attribute als dict, damit keines doppelt vorkommen kann —
    ein doppeltes Attribut macht die ganze Datei fuer XML-Parser ungueltig,
    und dann zeigen Browser und GitHub gar nichts an."""
    a = ' '.join('{}="{}"'.format(k, v) for k, v in attrs.items()
                 if v is not None)
    if inhalt is None:
        return '<{} {}/>'.format(tag, a)
    return '<{} {}>{}</{}>'.format(tag, a, inhalt, tag)


def stil(art, mehr):
    """Fuellung und Rand einer Materialart; mehr (stroke_dasharray=...)
    ueberschreibt oder ergaenzt, Unterstriche werden Bindestriche."""
    fill, stroke = FARBE[art]
    a = {'fill': fill, 'stroke': stroke, 'stroke-width': '0.8'}
    a.update({k.replace('_', '-'): v for k, v in mehr.items()})
    return a


def rect_px(xa, ya, xb, yb, art, **mehr):
    a = {'x': f1(min(xa, xb)), 'y': f1(min(ya, yb)),
         'width': f1(abs(xb - xa)), 'height': f1(abs(yb - ya))}
    a.update(stil(art, mehr))
    return el('rect', a)


def poly_px(punkte, art, **mehr):
    a = {'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte)}
    a.update(stil(art, mehr))
    return el('polygon', a)


def kreis_px(cx, cy, r, art, **mehr):
    a = {'cx': f1(cx), 'cy': f1(cy), 'r': f1(r)}
    a.update(stil(art, mehr))
    return el('circle', a)


def linie(x1, y1, x2, y2, farbe=GRAU, breite=0.7, strich=None):
    return el('line', {'x1': f1(x1), 'y1': f1(y1), 'x2': f1(x2),
                       'y2': f1(y2), 'stroke': farbe, 'stroke-width': breite,
                       'stroke-dasharray': strich})


def text(x, y, s, gr=8.5, farbe=TEXT, anker='start', fett=False, halo=False):
    a = {'x': f1(x), 'y': f1(y), 'font-size': gr, 'fill': farbe,
         'text-anchor': anker, 'font-weight': '600' if fett else None}
    if halo:        # weisser Rand, damit Text ueber Linien lesbar bleibt
        a.update({'stroke': '#ffffff', 'stroke-width': '3',
                  'stroke-linejoin': 'round', 'paint-order': 'stroke'})
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return el('text', a, s)


def pfeil(x, y, dx, dy, farbe):
    """Pfeilspitze mit der Spitze bei (x, y), zeigt in Richtung (dx, dy)."""
    lang, halb = 5.0, 2.0
    bx, by = x - dx * lang, y - dy * lang
    return el('polygon', {'points': '{},{} {},{} {},{}'.format(
        f1(x), f1(y), f1(bx - dy * halb), f1(by + dx * halb),
        f1(bx + dy * halb), f1(by - dx * halb)), 'fill': farbe})


def masslinie_z(a, y, z0, z1, farbe):
    """Senkrechte Masslinie bei Maschinen-Y = y von z0 bis z1 (z0 < z1),
    Pfeile innen."""
    x, ya = a.px(y, z1)
    _, yb = a.px(y, z0)
    return [linie(x, ya, x, yb, farbe, 0.8),
            pfeil(x, ya, 0, -1, farbe), pfeil(x, yb, 0, 1, farbe)]


class Ansicht:
    """Seitenansicht, Maschinen-Y nach rechts, Maschinen-Z nach oben; (ox, oy)
    ist die linke obere Ecke des Ausschnitts y_bereich x z_bereich."""

    def __init__(self, ox, oy, s, y_bereich, z_bereich):
        self.ox, self.oy, self.s = ox, oy, s
        self.yb, self.zb = y_bereich, z_bereich
        self.breite = (y_bereich[1] - y_bereich[0]) * s
        self.hoehe = (z_bereich[1] - z_bereich[0]) * s

    def px(self, y, z):
        return (self.ox + (y - self.yb[0]) * self.s,
                self.oy + (self.zb[1] - z) * self.s)

    def rect(self, y0, y1, z0, z1, art, **mehr):
        (xa, ya), (xb, yb) = self.px(y0, z1), self.px(y1, z0)
        return rect_px(xa, ya, xb, yb, art, **mehr)

    def poly(self, punkte, art, **mehr):
        return poly_px([self.px(y, z) for y, z in punkte], art, **mehr)

    def ausschnitt(self, name, inhalt):
        """Inhalt auf den Rahmen der Ansicht beschnitten."""
        rahmen = el('rect', {'x': f1(self.ox), 'y': f1(self.oy),
                             'width': f1(self.breite),
                             'height': f1(self.hoehe)})
        return ([el('clipPath', {'id': name}, rahmen),
                 '<g clip-path="url(#{})">'.format(name)] + inhalt + ['</g>'])


def hinweis(a, y, z, tx, ty, s, gr=8.5):
    """Beschriftung mit Fuehrungslinie vom Punkt (y, z) der Ansicht zu (tx, ty)."""
    x, yy = a.px(y, z)
    return [linie(x, yy, tx - 3, ty - 3, GRAU, 0.6),
            el('circle', {'cx': f1(x), 'cy': f1(yy), 'r': '1.6',
                          'fill': GRAU}),
            text(tx, ty, s, gr)]


def beschriften(a, eintraege, tx, oben, abstand=12.0):
    """Beschriftungen von oben nach unten, jede so nah an ihrem Punkt wie
    moeglich, aber ohne sich zu ueberlappen."""
    t, belegt = [], oben
    for y, z, s in sorted(eintraege, key=lambda e: -e[1]):
        ty = max(a.px(y, z)[1] + 3, belegt + abstand)
        belegt = ty
        t += hinweis(a, y, z, tx, ty, s)
    return t


# ---- die Teile --------------------------------------------------------------

def zeichne_seite(a, w, L, zc):
    """Alle Teile einer Seitenansicht fuer die Wagenmitte zc. Gemalt wird von
    hinten nach vorn: erst was hinter der Schnittebene liegt (hell), dann der
    Schnitt. Blickrichtung -X: alles mit X < spindel_x liegt dahinter."""
    sy = w('spindel_y')
    r_s = w('spindel_d') / 2
    r_b = w('spindel_durchgang') / 2
    r_lk = w('t8_lochkreis') / 2
    r_mot = w('motor_flansch') / 2
    t = []

    # ---- dahinter ------------------------------------------------------
    # Saeule der Traegerplatte: bis traeger_kopf_unten nur X = +-22, reicht
    # also nicht bis zur Spindel; darueber wird sie breit (Schnitt unten).
    t.append(a.rect(0.0, L['traeger_y1'], w('traeger_z_unten'),
                    w('traeger_kopf_unten'), 'hinten'))
    t.append(a.rect(L['sockel_y1'], L['z_schiene_y1'], L['z_schiene_z0'],
                    L['z_schiene_z1'], 'hinten'))            # MGN9-Schiene
    t.append(a.rect(L['traeger_y1'],
                    L['traeger_y1'] + w('saeule_rippe_tiefe'),
                    w('traeger_z_unten'), L['konsole_z0'], 'hinten'))
    t.append(a.rect(L['sockel_y1'] + MGN_H1, L['z_wagen_y'],
                    zc - w('z_wagen_laenge') / 2,
                    zc + w('z_wagen_laenge') / 2, 'hinten'))  # Z-Wagen
    # Schlittenplatte samt Pad und Rippen: Y = Wagenflaeche bis Laserflaeche
    t.append(a.rect(L['schlitten_y0'], L['laser_y'],
                    zc + L['schlitten_unten_rel'],
                    zc + L['schlitten_oben_rel'], 'hinten'))
    t.append(a.rect(L['laser_y'], L['laser_vorn_y'],
                    zc + L['laser_unten_rel'], zc + L['laser_oben_rel'],
                    'hinten'))                               # Diodenlaser
    t.append(a.rect(0.0, L['motor_rippe_y1'], L['konsole_z1'],
                    L['motor_rippe_z1'], 'hinten'))          # Fuehrungsrippe
    # Linker Schenkel des Ruecken, durch den Spindelkanal sichtbar
    t.append(a.rect(L['winkel_y0'], sy + r_b, zc + L['winkel_unten_rel'],
                    zc + L['regal_z0_rel'], 'hinten', stroke='#7f93ad'))

    # ---- geschnitten: Kopfbereich + Konsole mit Bundbohrung ------------
    r_zb = (w('motor_bund_d') + w('spiel_locker')) / 2
    t.append(a.poly([(0.0, w('traeger_kopf_unten')),
                     (L['traeger_y1'], w('traeger_kopf_unten')),
                     (L['traeger_y1'], L['konsole_z0']),
                     (sy - r_zb, L['konsole_z0']),
                     (sy - r_zb, L['konsole_z1']),
                     (0.0, L['konsole_z1'])], 'druck'))
    t.append(a.rect(sy + r_zb, w('konsole_y_vorn'), L['konsole_z0'],
                    L['konsole_z1'], 'druck'))
    # Motoradapter auf der Konsole: so gross wie der Motorflansch, dieselbe
    # Bohrung Ø22,4 (geschnitten)
    for y0, y1 in ((sy - r_mot, sy - r_zb), (sy + r_zb, sy + r_mot)):
        t.append(a.rect(y0, y1, L['adapter_z0'], L['adapter_z1'], 'druck'))
    # Motor: sitzt auf dem Adapter, Zentrierbund in dessen Bohrung
    t.append(a.rect(sy - r_mot, sy + r_mot, L['motor_flansch_z'],
                    L['motor_z1'], 'kauf'))
    bund_z0 = L['motor_flansch_z'] - w('motor_bund_h')
    t.append(a.rect(sy - w('motor_bund_d') / 2, sy + w('motor_bund_d') / 2,
                    bund_z0, L['motor_flansch_z'], 'kauf'))
    t.append(a.rect(sy - WELLE_D / 2, sy + WELLE_D / 2, L['welle_z0'],
                    bund_z0, 'stahl'))

    # ---- geschnitten: Lasche, Ruecken (Wand vor dem Kanal), Regal ------
    t.append(a.rect(L['schlitten_y1'], L['laser_y'],
                    zc + L['winkel_unten_rel'] - 3.0,
                    zc + L['schlitten_oben_rel'], 'druck'))
    t.append(a.rect(sy + r_b, L['schlitten_y1'], zc + L['winkel_unten_rel'],
                    zc + L['regal_z0_rel'], 'druck'))
    for y0, y1 in ((L['regal_y0'], sy - r_b), (sy + r_b, L['regal_y1'])):
        t.append(a.rect(y0, y1, zc + L['regal_z0_rel'],
                        zc + L['regal_z1_rel'], 'druck'))
    oben = zc + L['regal_z1_rel']          # Regaloberseite = Flanschsitz
    for ys in (sy - r_lk, sy + r_lk):      # in die Schnittebene gedreht
        t.append(a.rect(ys - w('insert_m3_d') / 2, ys + w('insert_m3_d') / 2,
                        oben - w('insert_m3_t'), oben, 'messing'))

    # ---- Spindel mit Gewindeschraffur ----------------------------------
    z0, z1 = L['spindel_z0_ist'], L['spindel_z1']
    t.append(a.rect(sy - r_s, sy + r_s, z0, z1, 'stahl'))
    z = z0 + 1.0
    while z < z1 - 1.0:
        (xa, ya), (xb, yb) = a.px(sy - r_s, z), a.px(sy + r_s, z + 1.2)
        t.append(linie(xa, ya, xb, yb, '#7d838c', 0.5))
        z += 2.0                            # Steigung 2 mm

    # ---- Kupplung im Schnitt: oben Bohrung Ø5, unten Ø8 ----------------
    r_k = w('kupplung_d') / 2
    k0, k1 = L['kupplung_z0'], L['kupplung_z1']
    km = (k0 + k1) / 2
    for v in (-1, 1):
        t.append(a.poly([(sy + v * r_k, k0), (sy + v * r_s, k0),
                         (sy + v * r_s, km), (sy + v * WELLE_D / 2, km),
                         (sy + v * WELLE_D / 2, k1), (sy + v * r_k, k1)],
                        'kauf'))

    # ---- Garnitur: Flanschmutter, Schrauben, Feder, Gleitmutter --------
    d_f = w('t8_flansch_dicke')
    for v in (-1, 1):                      # Flansch und Bund, ein Teil
        t.append(a.poly([(sy + v * w('t8_flansch_d') / 2, oben),
                         (sy + v * r_s, oben),
                         (sy + v * r_s, oben + d_f + BUND_H),
                         (sy + v * BUND_D / 2, oben + d_f + BUND_H),
                         (sy + v * BUND_D / 2, oben + d_f),
                         (sy + v * w('t8_flansch_d') / 2, oben + d_f)],
                        'kauf'))
    klemm = L['flansch_klemm']
    for ys in (sy - r_lk, sy + r_lk):
        t.append(a.rect(ys - SCHAFT_D / 2, ys + SCHAFT_D / 2,
                        oben + klemm - L['flansch_schraube'], oben + klemm,
                        'stahl'))
        t.append(a.rect(ys - KOPF_D / 2, ys + KOPF_D / 2, oben + klemm,
                        oben + klemm + KOPF_H, 'stahl'))
    feder0 = oben + d_f + BUND_H
    gleit0 = oben + w('t8_garnitur_h') - GLEIT_H
    punkte = [a.px(sy + (BUND_D / 2 if i % 2 else -BUND_D / 2),
                   feder0 + (gleit0 - feder0) * i / N_FEDER)
              for i in range(N_FEDER + 1)]
    t.append(el('polyline', {
        'points': ' '.join('{},{}'.format(f1(x), f1(y)) for x, y in punkte),
        'fill': 'none', 'stroke': BRAUN, 'stroke-width': '1.1'}))
    for v in (-1, 1):
        t.append(a.rect(sy + v * r_s, sy + v * GLEIT_D / 2, gleit0,
                        oben + w('t8_garnitur_h'), 'kauf'))
    return t


def feder_punkt(w, L, zc, i):
    """Ein Knick der Feder (rechte Seite fuer ungerade i) in Maschinen-Y/Z."""
    oben = zc + L['regal_z1_rel']
    feder0 = oben + w('t8_flansch_dicke') + BUND_H
    gleit0 = oben + w('t8_garnitur_h') - GLEIT_H
    return (w('spindel_y') + BUND_D / 2,
            feder0 + (gleit0 - feder0) * i / N_FEDER)


def main():
    mod = bauraum.modul_laden()
    w, L = mod.w, mod.lage()
    sy = w('spindel_y')
    zc_u, zc_o = L['zc_min'], L['zc_max']
    oben = zc_o + L['regal_z1_rel']        # Regaloberseite, Schlitten oben

    links = Ansicht(72, OBEN, S, Y_BEREICH, Z_BEREICH)
    rechts = Ansicht(72 + links.breite + 96, OBEN, S, Y_BEREICH, Z_BEREICH)
    x_text = rechts.ox + rechts.breite + 18
    dx0 = x_text + 250                     # rechte Spalte
    breite = dx0 + 300
    hoehe = OBEN + links.hoehe + 66

    t = [el('rect', {'width': '100%', 'height': '100%', 'fill': '#ffffff'}),
         text(18, 22, 'Z-Antrieb — Aufbau der Spindel', 13, TEXT, fett=True),
         text(18, 37, 'Seitenansichten geschnitten durch die Spindelachse, '
              'Blick von der Seite des Mutternwinkels, vorn (Laser) rechts. '
              'Schrauben und Einsätze in die Schnittebene gedreht.', 8.5,
              GRAU),
         text(18, 49, 'Maßstäblich aus ToolheadZ.py Rev. {} · hell = liegt '
              'hinter der Schnittebene'.format(mod.REVISION), 8.5, GRAU)]

    # Z-Skala
    for z in range(-60, 201, 20):
        _, yy = links.px(0, z)
        t.append(linie(58, yy, 64, yy, GRAU, 0.6))
        t.append(text(54, yy + 3, de(z, 0, True), 7.5, GRAU, 'end'))
    t.append(text(14, OBEN - 8, 'Z [mm]', 8, GRAU))

    for a, zc, titel, name in (
            (links, zc_u, 'Schlitten ganz unten', 'ansicht_unten'),
            (rechts, zc_o, 'Schlitten ganz oben', 'ansicht_oben')):
        t += a.ausschnitt(name, zeichne_seite(a, w, L, zc))
        t.append(text(a.ox, OBEN - 8, '{}  (zc = {})'.format(
            titel, de(zc, 2, True)), 10, BLAU, fett=True))
        # Schaltpunkt: die Schaltfahne sitzt links neben der Saeule, nicht
        # in diesem Schnitt. Eingezeichnet ist deshalb, wie hoch die
        # Gleitmutter steht, wenn die Fahne den Strahl erreicht.
        z_schalt = L['zc_arbeit_max'] + L['garnitur_z1_rel']
        xa, ya = a.px(Y_BEREICH[0], z_schalt)
        xb, _ = a.px(Y_BEREICH[1], z_schalt)
        t.append(linie(xa, ya, xb, ya, ROT, 0.9, '4 3'))

    # ---- rechte Ansicht: Beschriftung --------------------------------------
    a = rechts
    i_feder = 5                            # ein Knick rechts, etwa mittig
    t += beschriften(a, [
        (sy - 6, L['motor_z1'] - 14,
         'NEMA 17, Zentrierbund in der Bohrung des Adapters'),
        (sy + w('motor_flansch') / 2 - 3, (L['adapter_z0']
                                           + L['adapter_z1']) / 2,
         'Motoradapter {:.0f} mm (neu) auf der Konsole, die bleibt'.format(
             w('motor_adapter'))),
        (sy + WELLE_D / 2, (L['kupplung_z1'] + L['adapter_z0']) / 2,
         'Motorwelle Ø{:.0f}, zeigt nach unten'.format(WELLE_D)),
        (sy + w('kupplung_d') / 2, L['kupplung_z1'] - 7,
         'Klemmkupplung 5→8, {:.0f} mm, oben {:.0f} mm in der Konsole'.format(
             w('kupplung_l'), max(L['kupplung_in_konsole'], 0.0))),
        (sy, (L['spindel_z1'] + L['welle_z0']) / 2,
         '{:.0f} mm Spalt: Welle und Spindel je {:.0f} mm drin'.format(
             L['kupplung_frei'], w('kupplung_griff'))),
        (sy + GLEIT_D / 2, oben + w('t8_garnitur_h') - 7,
         'Gleitmutter Ø{:.0f}, verdrehgesichert — oberstes bewegtes '
         'Teil'.format(GLEIT_D)),
        feder_punkt(w, L, zc_o, i_feder) + (
            'Feder drückt die Gleitmutter nach oben',),
        (sy + DETAIL_Y[1], oben + DETAIL_Z[1] - 4,
         'Flansch, Schrauben, Regal: siehe Einzelheit A'),
        (sy + r_wand(w) + 0.9, zc_o + 4,
         'Rücken des Mutternwinkels, Spindel läuft im Kanal'),
        (L['laser_y'] - 1.5, zc_o - 5,
         'Lasche der Schlittenplatte, trägt den Winkel'),
        ((L['sockel_y1'] + MGN_H1 + L['z_wagen_y']) / 2, zc_o - 14,
         'Z-Wagen auf der MGN9-Schiene: führt den Schlitten'),
        (56.0, zc_o - 32, 'Diodenlaser (dahinter)'),
        (sy + w('spindel_d') / 2, L['spindel_z0_ist'] + 12,
         'Tr8×2-Spindel, {:.0f} mm: hängt an der Kupplung, unten '
         'frei'.format(w('spindel_zuschnitt'))),
    ], x_text, OBEN)

    # Garniturhoehe und Luft zur Kupplung als Masskette links der Spindel
    z_r, z_g, z_k = oben, oben + w('t8_garnitur_h'), L['kupplung_z0']
    y_g, y_l = sy - 15.0, sy - 18.5        # Masslinien Garnitur / Luft
    for z, y_von in ((z_r, sy - w('t8_flansch_d') / 2 - 0.8),
                     (z_g, sy - GLEIT_D / 2 - 0.8),
                     (z_k, sy - w('kupplung_d') / 2 - 0.8)):
        xa, yy = a.px(y_von, z)
        xb, _ = a.px((y_g if z == z_r else y_l) - 1.5, z)
        t.append(linie(xa, yy, xb, yy, GRAU, 0.5))
    t += masslinie_z(a, y_g, z_r, z_g, BRAUN)
    x, y_mitte = a.px(y_g - 1.5, (z_r + z_g) / 2)
    t.append(text(x, y_mitte - 2, 'Garnitur', 8, BRAUN, 'end', halo=True))
    t.append(text(x, y_mitte + 9, '{} mm'.format(
        de(w('t8_garnitur_h'))), 8, BRAUN, 'end', True, halo=True))
    # Luft: zu klein fuer Pfeile innen, also von aussen
    x, ya = a.px(y_l, z_k)
    _, yb = a.px(y_l, z_g)
    t += [linie(x, ya - 9, x, yb + 9, ROT, 0.8),
          pfeil(x, ya, 0, 1, ROT), pfeil(x, yb, 0, -1, ROT)]
    luft = z_k - z_g
    t.append(text(x - 4, ya - 4, '{} mm Luft'.format(de(luft)), 8, ROT,
                  'end', True, halo=True))
    # Rahmen der Einzelheit A
    (xa, ya), (xb, yb) = (a.px(sy + DETAIL_Y[0], oben + DETAIL_Z[1]),
                          a.px(sy + DETAIL_Y[1], oben + DETAIL_Z[0]))
    t.append(el('rect', {'x': f1(xa), 'y': f1(ya), 'width': f1(xb - xa),
                         'height': f1(yb - ya), 'fill': 'none',
                         'stroke': TEXT, 'stroke-width': '0.9',
                         'stroke-dasharray': '3 2', 'rx': '3'}))
    t.append(text(xa + 2, ya - 3, 'A', 10, TEXT, fett=True, halo=True))

    # ---- Draufsicht auf das Regal ------------------------------------------
    dy0 = OBEN + 30
    t += draufsicht(w, L, dx0, dy0)

    # ---- Einzelheit A ------------------------------------------------------
    ey0 = dy0 + (DRAUF_Y[1] - DRAUF_Y[0]) * S_DRAUF + 62
    t += einzelheit(w, L, zc_o, dx0, ey0)

    # ---- Legende -----------------------------------------------------------
    ly = hoehe - 36
    for i, (art, s) in enumerate((
            ('druck', 'gedruckt (PETG), geschnitten'),
            ('kauf', 'Kaufteil'),
            ('stahl', 'Stahl: Welle, Spindel, Schrauben'),
            ('messing', 'Messing-Einsatz'),
            ('hinten', 'hinter der Schnittebene'))):
        x = 18 + i * 196
        t.append(rect_px(x, ly, x + 14, ly + 9, art))
        t.append(text(x + 19, ly + 8, s, 8.5))
    t.append(linie(18, ly + 23, 32, ly + 23, ROT, 0.9, '4 3'))
    t.append(text(37, ly + 26, 'Endschalter: die Schaltfahne (links neben '
                  'der Säule) erreicht den Strahl, wenn die Oberkante der '
                  'Gleitmutter hier steht — {} mm vor der oberen Grenze, '
                  '{} mm unter der Kupplung'.format(
                      de(w('ls_ueberfahrt')),
                      de(w('ls_ueberfahrt') + w('luft_bau'))), 8.5))

    svg = '\n'.join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" '
        'height="{:.0f}" viewBox="0 0 {:.0f} {:.0f}" font-family="Inter, '
        'Helvetica, Arial, sans-serif">'.format(breite, hoehe, breite, hoehe)]
        + t + ['</svg>'])
    xml.dom.minidom.parseString(svg.encode('utf-8'))   # wirft bei Fehlern
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg + '\n')
    print('geschrieben: {}  ({:.0f} x {:.0f} px)'.format(
        os.path.relpath(ZIEL), breite, hoehe))


def r_wand(w):
    """Radius der Spindelbohrung: dort beginnt die Wand vor dem Kanal."""
    return w('spindel_durchgang') / 2


def draufsicht(w, L, dx0, dy0):
    """Draufsicht auf das Regal, alles ueber dem Flansch weggelassen. Von
    oben gesehen mit vorn (Laser) unten zeigt Maschinen-X nach LINKS."""
    def dp(x, y):
        return (dx0 + (DRAUF_X[1] - x) * S_DRAUF,
                dy0 + (y - DRAUF_Y[0]) * S_DRAUF)

    def drect(x0, x1, y0, y1, art, **mehr):
        (xa, ya), (xb, yb) = dp(x0, y0), dp(x1, y1)
        return rect_px(xa, ya, xb, yb, art, **mehr)

    def dkreis(x, y, d, art, **mehr):
        cx, cy = dp(x, y)
        return kreis_px(cx, cy, d / 2 * S_DRAUF, art, **mehr)

    sx, sy = w('spindel_x'), w('spindel_y')
    x_rechts = dx0 + (DRAUF_X[1] - DRAUF_X[0]) * S_DRAUF
    t = [text(dx0, dy0 - 18, 'Draufsicht auf das Regal', 10, BLAU,
              fett=True),
         text(dx0, dy0 - 6, 'von oben, alles über dem Flansch weggelassen',
              8, GRAU)]
    # tiefer liegend: Schlittenplatte mit Lasche und Pad (gestrichelt)
    t.append(poly_px([dp(DRAUF_X[0], L['schlitten_y0']),
                      dp(w('pad_breite') / 2, L['schlitten_y0']),
                      dp(w('pad_breite') / 2, L['schlitten_y1']),
                      dp(w('winkel_x_rechts'), L['schlitten_y1']),
                      dp(w('winkel_x_rechts'), L['laser_y']),
                      dp(DRAUF_X[0], L['laser_y'])], 'hinten',
                     stroke_dasharray='3 2'))
    # geschnitten: Saeule und Saeulenrippe (die Saeule endet bei X = 22)
    t.append(drect(DRAUF_X[0], w('traeger_x_rechts'), 0.0, L['traeger_y1'],
                   'druck'))
    t.append(drect(w('saeule_rippe_x0'), w('saeule_rippe_x1'),
                   L['traeger_y1'], L['traeger_y1'] + w('saeule_rippe_tiefe'),
                   'druck'))
    t.append(drect(w('winkel_x_links'), w('winkel_x_rechts'), L['regal_y0'],
                   L['regal_y1'], 'druck'))
    t.append(dkreis(sx, sy, w('t8_flansch_d'), 'kauf'))
    t.append(dkreis(sx, sy, w('t8_lochkreis'), 'kauf', fill='none',
                    stroke_dasharray='2 2'))
    for x, y in L['t8_loecher']:
        t.append(dkreis(x, y, KOPF_D, 'stahl'))
    t.append(dkreis(sx, sy, BUND_D, 'kauf'))
    t.append(dkreis(sx, sy, w('spindel_d'), 'stahl'))
    cx, cy = dp(sx, sy)
    t.append(text(cx, cy + 3, 'Tr8', 7, TEXT, 'middle'))

    # Beschriftung rechts daneben
    rippe_y1 = L['traeger_y1'] + w('saeule_rippe_tiefe')
    for x, y, s in (
            ((DRAUF_X[0] + w('traeger_x_rechts')) / 2, L['traeger_y1'] / 2,
             'Trägerplatte (Säule)'),
            ((w('saeule_rippe_x0') + w('saeule_rippe_x1')) / 2,
             (L['traeger_y1'] + rippe_y1) / 2,
             'Säulenrippe, {} mm Luft zum Regal'.format(
                 de(L['regal_y0'] - rippe_y1))),
            (DRAUF_X[0] + 1.0, (L['schlitten_y1'] + L['laser_y']) / 2,
             'Schlittenplatte, tiefer')):
        px, py = dp(x, y)
        t += [linie(px, py, x_rechts + 9, py, GRAU, 0.6),
              el('circle', {'cx': f1(px), 'cy': f1(py), 'r': '1.6',
                            'fill': GRAU}),
              text(x_rechts + 12, py + 3, s, 7.5)]
    _, y_unten = dp(0, DRAUF_Y[1])
    t.append(text(dx0, y_unten + 14, 'unten = vorn (Laser) · Lochkreis '
                  'Ø{:.0f}, um 45° gedreht'.format(w('t8_lochkreis')), 8,
                  TEXT))
    return t


def einzelheit(w, L, zc, dx0, ey0):
    """Einzelheit A: Flanschsitz vergroessert, derselbe Schnitt wie die
    Seitenansicht (Schlitten oben)."""
    sy = w('spindel_y')
    oben = zc + L['regal_z1_rel']
    a = Ansicht(dx0, ey0, S_DETAIL, (sy + DETAIL_Y[0], sy + DETAIL_Y[1]),
                (oben + DETAIL_Z[0], oben + DETAIL_Z[1]))
    t = [text(dx0, ey0 - 18, 'Einzelheit A: Flansch auf dem Regal', 10, BLAU,
              fett=True),
         text(dx0, ey0 - 6, '{}-fach gegenüber den Seitenansichten'.format(
             de(S_DETAIL / S)), 8, GRAU)]
    t += a.ausschnitt('einzelheit_a', zeichne_seite(a, w, L, zc))
    t.append(el('rect', {'x': f1(a.ox), 'y': f1(a.oy),
                         'width': f1(a.breite), 'height': f1(a.hoehe),
                         'fill': 'none', 'stroke': TEXT,
                         'stroke-width': '0.9'}))
    r_lk = w('t8_lochkreis') / 2
    d_f = w('t8_flansch_d') / 2
    t += beschriften(a, [
        (sy + BUND_D / 2 - 0.4, oben + w('t8_flansch_dicke') + BUND_H - 0.6,
         'Bund Ø{} × {} zeigt nach oben'.format(de(BUND_D), de(BUND_H))),
        (sy + r_lk + KOPF_D / 2 - 0.6, oben + w('t8_flansch_dicke') + 1.6,
         'M3×{:.0f} Zylinderkopf, ohne Scheibe'.format(
             L['flansch_schraube'])),
        (sy + d_f - 0.6, oben + w('t8_flansch_dicke') / 2,
         'Flansch Ø{:.0f} × {}, glatte Seite unten'.format(
             w('t8_flansch_d'), de(w('t8_flansch_dicke')))),
        (sy + r_lk + w('insert_m3_d') / 2 - 0.5, oben - 5.5,
         'Messing-Einsatz M3, Bohrung Ø{} × {:.0f}'.format(
             de(w('insert_m3_d')), w('insert_m3_t'))),
        (sy + r_lk, oben - (w('insert_m3_t') + w('winkel_regal_dicke')) / 2,
         'Regal {:.0f} mm'.format(w('winkel_regal_dicke'))),
        (sy + (r_wand(w) + L['schlitten_y1'] - sy) / 2, oben - 12.5,
         'Rücken: Wand vor dem Spindelkanal'),
        ((L['schlitten_y1'] + L['laser_y']) / 2 + 1.5, oben - 13.0,
         'Lasche, {} mm unter dem Regal'.format(de(w('winkel_luft')))),
    ], a.ox + a.breite + 14, ey0 - 4, 13.0)
    return t


if __name__ == '__main__':
    main()
