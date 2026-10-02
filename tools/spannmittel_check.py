#!/usr/bin/env python3
"""Rechnerische Pruefung der Spannmittel (fusion/Spannmittel) — laeuft ohne
Fusion.

Importiert Spannmittel.py, Opferplatte.py, Portal.py und ToolheadZ.py mit
gestubbtem adsk-Modul und prueft: Abgleich von Platte und Arbeitsfeld,
Hoehe unter dem Toolhead (auch ueber den ganzen Weg, mit und ohne
Werkstueck), Lage des Anschlagwinkels, Selbsthemmung und Spannweg des
Exzenters, Niederhalter (Platz, Hebel, Biegung), Schrauben in der
Spanplatte, das Beispiel und den Druck. Gibt die Stueckliste aus.

    python3 tools/spannmittel_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from opferplatte_check import OPFERPLATTE             # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SPANNMITTEL = os.path.join(HIER, '..', 'fusion', 'Spannmittel',
                           'Spannmittel.py')
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
PETG = 1.27            # g/cm3
MU = 0.3               # Reibwert PETG auf Holz/PETG, trocken (vorsichtig)
F_SCHRAUBE = 50.0      # N: Niederhalter handfest angezogen
SIGMA_SCHICHT = 15.0   # MPa: PETG in der Schichtebene (~45), Sicherheit 3
IM_BRETT = 10.0        # so tief muss die Spanplattenschraube mindestens fassen
LUFT_FEST = 0.5        # Toolhead ueber Anschlag und Exzenter, Z ganz unten
LUFT_WERKSTUECK = 1.0  # Toolhead ueber dem Niederhalter
X_SCHRITTE, Y_SCHRITTE = 41, 25


def engste(a_liste, b_liste):
    best = (float('inf'), None, None)
    for a in a_liste:
        for b in b_liste:
            d = a.abstand(b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def auf(q, dy):
    return Quader(q.name, q.x[0], q.x[1], q.y[0] + dy, q.y[1] + dy, q.z[0],
                  q.z[1], q.art)


def anschlag_quader(SL):
    (hx, hy), (lx, ly) = SL['aw_hinten'], SL['aw_links']
    return [Quader('Anschlag hinten', *hx, *hy, *SL['aw_z']),
            Quader('Anschlag links', *lx, *ly, *SL['aw_z'])]


def exzenter_quader(sw, SL, ex):
    """Scheibe als umschreibender Quader (sicher), dazu der Hebel."""
    (cx, cy), R = ex['mitte'], sw('ex_r')
    hx = [x for x, _ in ex['hebel']]
    hy = [y for _, y in ex['hebel']]
    n = ex['name'].replace('_', ' ')
    return [Quader(n, cx - R, cx + R, cy - R, cy + R, *SL['ex_z']),
            Quader(n + ' Hebel', min(hx), max(hx), min(hy), max(hy),
                   *SL['ex_z'])]


def niederhalter_quader(nh):
    n = nh['name'].replace('_', ' ')
    return [Quader(n, *nh['steg'][0], *nh['steg'][1], *nh['steg'][2]),
            Quader(n + ' Ferse', *nh['ferse'][0], *nh['ferse'][1],
                   *nh['ferse'][2])]


def senkung_extra(sw, SL):
    """Volumen (mm3), das die 90-Grad-Senkung ueber das Loch hinaus nimmt."""
    rs, rl, t = sw('senk_d') / 2.0, sw('sch_loch') / 2.0, SL['senk_tief']
    return math.pi * t / 3.0 * (rs * rs + rs * rl + rl * rl) - \
        math.pi * rl * rl * t


def hebel_flaeche(sw):
    """Flaeche des Hebels ausserhalb der Scheibe (mm2), numerisch."""
    R, hb = sw('ex_r'), sw('ex_hebel_b') / 2.0
    a, b = R - 2.0, R + sw('ex_hebel_l')
    n, innen = 2000, 0.0
    for i in range(n):
        x = a + (min(b, R) - a) * (i + 0.5) / n
        innen += 2.0 * min(hb, math.sqrt(max(0.0, R * R - x * x))) * \
            (min(b, R) - a) / n
    return (b - a) * 2.0 * hb - innen


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    om = bauraum.modul_laden(OPFERPLATTE, 'opferplatte')
    ow, OL = om.w, om.lage()
    sm = bauraum.modul_laden(SPANNMITTEL, 'spannmittel')
    sw, SL = sm.w, sm.lage()
    p = Pruefung()
    top = OL['platte_z'][1]
    loch = math.pi * (sw('sch_loch') / 2.0) ** 2

    # ------------------------------------------------------------------
    p.titel('1) Abgleich Spannmittel.py <-> Opferplatte.py, ToolheadZ.py')
    for text, ist, soll in (
            ('Platte links', SL['platte_x'][0], OL['platte_x'][0]),
            ('Platte rechts', SL['platte_x'][1], OL['platte_x'][1]),
            ('Platte hinten', SL['platte_y'][0], OL['platte_y'][0]),
            ('Platte vorn', SL['platte_y'][1], OL['platte_y'][1]),
            ('Platte unten (Tisch)', SL['platte_z'][0], OL['platte_z'][0]),
            ('Plattenoberflaeche', SL['platte_z'][1], OL['platte_z'][1]),
            ('Arbeitsfeld links', sw('feld_x0'), ow('feld_x0')),
            ('Arbeitsfeld rechts', sw('feld_x1'), ow('feld_x1')),
            ('Arbeitsfeld hinten', sw('feld_y0'), ow('feld_y0')),
            ('Arbeitsfeld vorn', sw('feld_y1'), ow('feld_y1'))):
        p.ok(text, abs(ist - soll), 0.01, '<=')
    platte_tief = TL['zc_min'] + TL['schlitten_unten_rel']
    laser_tief = (TL['zc_min'] + TL['laser_unten_rel']
                  - tw('laser_langloch_hub'))
    frei = platte_tief - top
    p.ok('toolhead_frei = Schlittenplatte ueber der Platte, Z ganz unten '
         '({:.2f})'.format(frei), abs(sw('toolhead_frei') - frei), 0.05, '<=')
    p.ok('   tiefster Punkt ist die Schlittenplatte, nicht der Laser',
         laser_tief - platte_tief, 0.0)

    # ------------------------------------------------------------------
    p.titel('2) Hoehe: der Toolhead faehrt ueber alles')
    p.info('Fokus auf dem Werkstueck: Toolhead mindestens so weit darueber '
           '(sonst kaeme der Fokus nicht bis auf die leere Platte)', frei)
    p.ok('Anschlag: Toolhead darueber, Z ganz unten, ohne Werkstueck',
         frei - sw('aw_h'), LUFT_FEST)
    p.ok('Exzenter: Toolhead darueber, Z ganz unten, ohne Werkstueck',
         frei - sw('ex_h'), LUFT_FEST)
    p.ok('Niederhalter: Toolhead ueber dem Steg (ueber dem Werkstueck)',
         frei - sw('nh_d'), LUFT_WERKSTUECK)
    feste_th, bewegte_th, _ = bauraum.bauraeume(tw, TL)
    feste_th = [q for q in feste_th
                if q.name not in portal_check.TOOLHEAD_OHNE]
    dys = [-L['y_weg_hinten'] + (L['y_weg_hinten'] + w('y_weg_vorn')) * i
           / (Y_SCHRITTE - 1.0) for i in range(Y_SCHRITTE)]
    xws = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / (X_SCHRITTE - 1.0)
           for i in range(X_SCHRITTE)]
    anschlag = anschlag_quader(SL)
    exzenter = [q for ex in SL['ex'] for q in exzenter_quader(sw, SL, ex)]
    nieder = [q for nh in SL['nh'] for q in niederhalter_quader(nh)]
    werkstueck = Quader('Beispielwerkstueck', *SL['wst_x'], *SL['wst_y'],
                        *SL['wst_z'])
    t_bsp = sw('nh_t')
    for text, hub, teile, grenze in (
            ('ohne Werkstueck, Z ganz unten: Toolhead <-> Anschlag', 0.0,
             anschlag, LUFT_FEST),
            ('Beispiel {:.0f} mm, Fokus darauf: Toolhead <-> Spannmittel'
             .format(t_bsp), t_bsp, anschlag + exzenter + nieder
             + [werkstueck], LUFT_FEST)):
        best = (float('inf'),)
        for dy in dys:
            for xw in xws:
                th_ = ([auf(q.verschoben(0.0, xw), dy) for q in feste_th]
                       + [auf(q.verschoben(TL['zc_min'] + hub, xw), dy)
                          for q in bewegte_th])
                d = engste(th_, teile)
                if d[0] < best[0]:
                    best = d + (xw, dy)
        p.ok('{} ({} / {}, X {:+.0f}, Portal {:+.0f})'.format(
            text, best[1], best[2], best[3], best[4]), best[0], grenze)

    # ------------------------------------------------------------------
    p.titel('3) Anschlagwinkel: fest hinten links')
    xi, yi = SL['aw_ecke']
    sp = ow('platte_spiel')
    p.ok('Innenecke im Arbeitsfeld (X), Platte links am Anschlag',
         xi - sw('feld_x0'), 1.0)
    p.ok('Innenecke im Arbeitsfeld (Y), Platte ganz nach hinten geschoben',
         yi - sp - sw('feld_y0'), 1.0)
    (hx, hy), (lx, ly) = SL['aw_hinten'], SL['aw_links']
    p.ok('hinterer Schenkel ganz auf der Platte', hy[0] - SL['platte_y'][0],
         1.0)
    p.ok('linker Schenkel ganz auf der Platte', lx[0] - SL['platte_x'][0],
         1.0)
    p.ok('Platte samt Anschlag laesst sich herausziehen (hinter der '
         'Fuehrung frei)', hy[0] - OL['fuehrung_y']['hinten'], 1.0)
    rand = min(min(sw('aw_b_hinten'), sw('aw_b_links')) / 2.0,
               sw('aw_schraube_ende')) - sw('senk_d') / 2.0
    p.ok('Senkungen: Wand zum Schenkelrand', rand, 1.5)
    p.ok('   Material unter der Senkung', sw('aw_h') - SL['senk_tief'], 1.0)
    p.info('Schenkel {:.0f} mm, dahinter Platz fuer Niederhalter'.format(
        sw('aw_l')))

    # ------------------------------------------------------------------
    p.titel('4) Exzenter: selbsthemmend, Spannweg, Hebel')
    R, e = sw('ex_r'), sw('ex_e')
    p.ok('selbsthemmend: groesste Steigung <= Reibwinkel (mu {:.1f})'.format(
        MU), SL['ex_winkel'], math.degrees(math.atan(MU)), '<=', 'Grad')
    p.ok('Spannweg (Hebel quer -> Hebel nach aussen)', e, 3.0)
    p.info('Schraube so weit neben die Werkstueckkante: {:.0f} bis {:.0f} '
           'mm'.format(*SL['ex_fenster']))
    p.ok('Senkung: Wand zum Scheibenrand (kleinster Radius)',
         R - e - sw('senk_d') / 2.0, 3.0)
    p.ok('   Material unter der Senkung', sw('ex_h') - SL['senk_tief'], 1.0)
    for ex in SL['ex']:
        hebel = exzenter_quader(sw, SL, ex)[1]
        p.ok('{}: Hebel gespannt hinter der Scheibenmitte (vom Werkstueck '
             'weg)'.format(ex['name'].replace('_', ' ')),
             hebel.abstand(werkstueck), R)

    # ------------------------------------------------------------------
    p.titel('5) Niederhalter: Spanneisen je Materialstaerke')
    ul = -sw('nh_lippe') / 2.0                       # Mitte der Lippe
    uf = sw('nh_ende') - sw('nh_ferse') / 2.0        # Mitte der Ferse
    us = sw('nh_schraube')
    p.ok('Schraube zwischen Lippe und Ferse (Loch vor der Ferse)',
         (sw('nh_ende') - sw('nh_ferse')) - (us + sw('sch_loch') / 2.0), 0.5)
    p.ok('Schraube neben dem Werkstueck (Loch zur Kante)',
         us - sw('sch_loch') / 2.0, 1.0)
    lippe = F_SCHRAUBE * (uf - us) / (uf - ul)
    p.info('Lippe drueckt bei {:.0f} N an der Schraube mit'.format(
        F_SCHRAUBE), lippe, 'N')
    netto = sw('nh_b') - sw('sch_loch')
    p.ok('Steg an der Schraube: Biegung (in der Schichtebene)',
         lippe * (us - ul) / (netto * sw('nh_d') ** 2 / 6.0), SIGMA_SCHICHT,
         '<=', 'MPa')
    p.ok('   Material unter der Senkung', sw('nh_d') - SL['senk_tief'], 0.8)
    p.ok('passt hinter die hintere Werkstueckkante (Platte dahinter)',
         (yi - SL['platte_y'][0]) - sw('nh_ende'), 1.0)
    p.info('Gravur mindestens so weit vom Rand, wo ein Niederhalter sitzt',
           sw('nh_lippe') + 1.0)

    # ------------------------------------------------------------------
    p.titel('6) Schrauben: Spanplattenschraube 3,0 x {:.0f} Senkkopf'.format(
        sw('sch_l')))
    p.ok('Kopf unter der Oberseite (Senkung 90 Grad)', SL['kopf_tiefer'],
         0.1)
    dicke = OL['platte_z'][1] - OL['platte_z'][0]
    teile = [('Anschlag', sw('aw_h')), ('Exzenter', sw('ex_h'))] + [
        ('Niederhalter {:.0f} mm'.format(t), t + sw('nh_d'))
        for t in sm.NH_STAERKEN]
    for text, hoehe in teile:
        tief = sw('sch_l') - (hoehe - SL['kopf_tiefer'])
        p.ok('{}: Schraube fasst in der Platte'.format(text), tief, IM_BRETT)
        p.ok('   und kommt unten nicht heraus', dicke - tief, 3.0)

    # ------------------------------------------------------------------
    p.titel('7) Beispiel: Werkstueck {:.0f} x {:.0f} x {:.0f} mm in der '
            'Ecke'.format(sw('wst_l'), sw('wst_b'), t_bsp))
    p.ok('Werkstueck im Arbeitsfeld (rechts)', sw('feld_x1')
         - SL['wst_x'][1], 0.0)
    p.ok('Werkstueck im Arbeitsfeld (vorn)', sw('feld_y1') - SL['wst_y'][1],
         0.0)
    ausserhalb = [q.name for q in anschlag + exzenter + nieder
                  if q.x[0] < SL['platte_x'][0] or q.x[1] > SL['platte_x'][1]
                  or q.y[0] < SL['platte_y'][0]
                  or q.y[1] > SL['platte_y'][1]]
    p.ja('alle Spannmittel des Beispiels liegen auf der Platte',
         not ausserhalb, ' — ' + ', '.join(ausserhalb) if ausserhalb else '')
    gruppen = ([anschlag] + [exzenter_quader(sw, SL, ex) for ex in SL['ex']]
               + [niederhalter_quader(nh) for nh in SL['nh']])
    best = (float('inf'),)
    for i, a in enumerate(gruppen):
        for b in gruppen[i + 1:]:
            d = engste(a, b)
            if d[0] < best[0]:
                best = d
    p.ok('Spannmittel beruehren sich nicht ({} / {})'.format(best[1],
                                                           best[2]),
         best[0], 1.0)
    for ex in SL['ex']:
        k, c = ex['kontakt'], ex['mitte']
        p.ok('{} liegt an der Werkstueckkante'.format(ex['name'].replace(
            '_', ' ')), abs(math.hypot(k[0] - c[0], k[1] - c[1]) - R), 0.01,
            '<=')

    # ------------------------------------------------------------------
    p.titel('8) Druck (Bambu Lab A1, PETG)')
    a_fl = ((hx[1] - hx[0]) * (hy[1] - hy[0])
            + (lx[1] - lx[0]) * (ly[1] - ly[0])
            - sw('aw_b_links') * sw('aw_b_hinten'))
    extra = senkung_extra(sw, SL)
    v_aw = (a_fl * sw('aw_h') - 3 * (loch * sw('aw_h') + extra)) / 1000.0
    v_ex = ((math.pi * R * R + hebel_flaeche(sw)) * sw('ex_h')
            - loch * sw('ex_h') - extra) / 1000.0
    gr_aw = (lx[1] - lx[0] + hx[1] - hx[0] - sw('aw_b_links'),
             hy[1] - hy[0] + ly[1] - ly[0] - sw('aw_b_hinten'), sw('aw_h'))
    gr_ex = (2.0 * R + sw('ex_hebel_l'), 2.0 * R, sw('ex_h'))
    for text, v, gr in (('Anschlagwinkel', v_aw, gr_aw),
                        ('Exzenter', v_ex, gr_ex)):
        p.ok('{}: {:.0f} x {:.0f} x {:.0f} mm, {:.1f} cm3 ({:.1f} g voll)'
             .format(text, gr[0], gr[1], gr[2], v, v * PETG), max(gr), BETT,
             '<=')
    for t in sm.NH_STAERKEN:
        lang = sw('nh_lippe') + sw('nh_ende')
        v = (lang * sw('nh_b') * sw('nh_d')
             + sw('nh_ferse') * sw('nh_b') * t
             - loch * sw('nh_d') - extra) / 1000.0
        p.info('Niederhalter {:.0f} mm: {:.1f} x {:.0f} x {:.1f} mm, {:.2f} '
               'cm3 ({:.1f} g)'.format(t, lang, sw('nh_b'), t + sw('nh_d'),
                                       v, v * PETG))
    p.info('Anschlag und Exzenter: Unterseite aufs Bett; Niederhalter: '
           'Oberseite aufs Bett; keine Stuetzen')

    # ------------------------------------------------------------------
    p.titel('9) Statische Pruefung der Schluessel in Spannmittel.py')
    quelle = open(SPANNMITTEL, encoding='utf-8').read()
    benutzt = set(re.findall(r"\bw\('([^']+)'\)", quelle))
    fehlt_m = sorted(benutzt - set(sm.MASSE))
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(SL))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(set(sm.MASSE) - benutzt)
    if unbenutzt:
        p.info('nur fuer die Pruefung: ' + ', '.join(unbenutzt))

    p.titel('10) Validierungsbericht des Fusion-Skripts')
    try:
        zeilen = sm.hinweise_bauen(SL, [])
        for zeile in zeilen:
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
        p.ok('Berichtszeilen hoechstens 74 Zeichen',
             max(len(z) for z in zeilen), 74, '<=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    p.titel('11) Stueckliste')
    for zeile in (
            'Druck (PETG): 1 Anschlagwinkel, 2 Exzenter, Niederhalter je '
            'Materialstaerke ({} mm), fuer jede benutzte 4 Stueck'.format(
                '/'.join('{:.0f}'.format(t) for t in sm.NH_STAERKEN)),
            'Spanplattenschrauben 3,0 x {:.0f} Senkkopf TX10: 3 fuer den '
            'Anschlag, je eine fuer jeden Exzenter und Niederhalter'.format(
                sw('sch_l'))):
        p.info(zeile)
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
