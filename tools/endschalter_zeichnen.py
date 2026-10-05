#!/usr/bin/env python3
"""Zeichnung: Halter und Fahnen der Gabellichtschranken X und Y.

Y: rechte Seite von hinten und von rechts aussen — Halter aussen am rechten
2040 hinter dem hinteren 2060, Fahne an der Schlittenplatte. X: linkes
Rohrende von vorn und von oben, dazu die Klammer an der Traegerplatte von
links. Portal und Toolhead stehen am Schaltpunkt (3 mm vor dem
Schienenende). Alle Masse aus Portal.py (dort stehen seit Rev. 15 auch die
Endschalter) und ToolheadZ.py;
die Zeichnung ist massstaeblich und wandert mit den Parametern.

    python3 tools/endschalter_zeichnen.py   ->  docs/endschalter.svg
"""

import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from antrieb_zeichnen import (text, linie, rect_px, de,  # noqa: E402
                              TEXT, GRAU, BLAU, FARBE)
from portal_zeichnen import Feld                      # noqa: E402
from portal_zeichnen import quer_mass                 # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'endschalter.svg')
FARBE.update({
    'platine': ('#d3e9da', '#2f7a4f'),
    'gabel':   ('#8a919c', '#3d4450'),
    'fahne':   ('#2b2f36', '#111418'),
    'th':      ('#e6def5', '#6a4fa3'),
    'nut':     ('#ffffff', '#8c939e'),
})
NUT_TIEFE = 6.0        # Nut im Profilschnitt (vereinfacht)


def profil_schnitt(f, a0, a1, b0, b1, seiten, nb=6.2, art='profil'):
    """Profilquerschnitt als Umriss mit den Nuten (vereinfacht: gerade
    Kerben nb breit, NUT_TIEFE tief, mittig auf jeder 20er-Teilung).
    seiten: welche Seiten Nuten haben ('l', 'r', 'u', 'o')."""
    h, t = nb / 2.0, NUT_TIEFE
    am = [a0 + 10.0 + 20.0 * i for i in range(int(round((a1 - a0) / 20.0)))]
    bm = [b0 + 10.0 + 20.0 * i for i in range(int(round((b1 - b0) / 20.0)))]
    p = [(a0, b0)]
    if 'u' in seiten:
        for m in am:
            p += [(m - h, b0), (m - h, b0 + t), (m + h, b0 + t), (m + h, b0)]
    p.append((a1, b0))
    if 'r' in seiten:
        for m in bm:
            p += [(a1, m - h), (a1 - t, m - h), (a1 - t, m + h), (a1, m + h)]
    p.append((a1, b1))
    if 'o' in seiten:
        for m in reversed(am):
            p += [(m + h, b1), (m + h, b1 - t), (m - h, b1 - t), (m - h, b1)]
    p.append((a0, b1))
    if 'l' in seiten:
        for m in reversed(bm):
            p += [(a0, m + h), (a0 + t, m + h), (a0 + t, m - h), (a0, m - h)]
    return f.poly(p, art, stroke_width='0.9')


def ansicht(f, teile, ax, bx, tiefe, blick):
    """Quader (und Vielecke) auf die Ebene (ax, bx) projizieren, das Ferne
    zuerst. blick = +1: der Betrachter steht bei +unendlich auf der
    Tiefenachse, -1 bei -unendlich. teile: (Quader, art, mehr) oder
    ('vieleck', punkte, art, mehr, tiefe_wert) oder ('svg', element,
    tiefe_wert)."""
    liste = []
    for t in teile:
        if t[0] == 'vieleck':
            _, pkt, art, mehr, tw_ = t
            liste.append((tw_ * blick, f.poly(pkt, art, **mehr)))
        elif t[0] == 'svg':
            liste.append((t[2] * blick, t[1]))
        else:
            q, art, mehr = t
            r = getattr(q, tiefe)
            key = r[1] if blick > 0 else r[0]
            a, b = getattr(q, ax), getattr(q, bx)
            liste.append((key * blick, f.rect(a[0], a[1], b[0], b[1], art,
                                              **mehr)))
    return [e for _, e in sorted(liste, key=lambda t: t[0])]


def auf(q, dx=0.0, dy=0.0, dz=0.0):
    return Quader(q.name, q.x[0] + dx, q.x[1] + dx, q.y[0] + dy,
                  q.y[1] + dy, q.z[0] + dz, q.z[1] + dz, q.art)


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    ew, EL = w, L                  # Endschalter: seit Rev. 15 in Portal.py
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    TH = {q.name: q for q in feste}
    portal, _ = bauraum.portal_bauraeume(w, L)
    P = {q.name: q for q in portal}
    dy, xs, R = EL['schalt_dy'], EL['schalt_xs'], EL['R']
    Q = Quader
    leer = {}
    gestr = {'fill': 'none', 'stroke_dasharray': '4 3', 'stroke_width': '1.0'}

    # ---- Teile Y (Rahmenkoordinaten, Portal am Schaltpunkt) ----------------
    hy_y = EL['hy_y']
    k = ew('m5_kopf_d') / 2.0
    ruecklauf = Q('Ruecklauf', EL['aussen_x'] - 4.3, EL['aussen_x'] - 2.9,
                  L['rahmen_y'][0] + 11.0, 240.0, EL['nut_o_z'] - 3.0,
                  EL['nut_o_z'] + 3.0)
    y_rahmen = [
        (Q('Y-Schiene', R - 6.0, R + 6.0, L['y_schiene_y'][0], 190.0,
           EL['rahmen_z1'], EL['rahmen_z1'] + 8.0), 'fuehrung', leer),
        (ruecklauf, 'riemen', leer)]
    for i, (yy, zz) in enumerate(EL['hy_m5']):
        y_rahmen.append((Q('Nutstein', EL['aussen_x'] - 1.8 - 4.0,
                           EL['aussen_x'] - 1.8, yy - 5.0, yy + 5.0, zz - 4.0,
                           zz + 4.0), 'stahl', leer))
    y_portal = [(auf(P[n], dy=dy), a, leer) for n, a in (
        ('Y-Wagen rechts', 'fuehrung'), ('Platte rechts', 'druck'),
        ('Stirnblock rechts', 'druck'), ('Rueckwand rechts', 'druck'),
        ('Klemmturm hinten rechts', 'druck'),
        ('Klemmturm hinten rechts oben', 'druck'),
        ('Klemmturm vorn rechts', 'druck'),
        ('Klemmturm vorn rechts oben', 'druck'), ('Portalrohr', 'profil'))]
    fyr = EL['fy_y']
    oz, uz = EL['fy_backe_o_z'], EL['fy_backe_u_z']
    y_neu = [
        (Q('Fuss', *EL['hy_fuss_x'], *hy_y, *EL['hy_fuss_z']), 'neu', leer),
        (Q('Boden', *EL['hy_boden_x'], *hy_y, *EL['hy_boden_z']), 'neu',
         leer),
        (Q('Platine', *EL['ly_pcb_x'], *EL['ly_pcb_y'], *EL['ly_pcb_z']),
         'platine', leer)]
    y_neu += [(Q('Gabel', *a, *EL['ly_gabel_y'], *EL['ly_gabel_z']), 'gabel',
               leer) for a in EL['ly_arme_x']]
    y_neu += [(Q('M5-Kopf', EL['hy_fuss_x'][1],
                 EL['hy_fuss_x'][1] + ew('m5_kopf_h'), yy - k, yy + k,
                 zz - k, zz + k), 'stahl', leer) for yy, zz in EL['hy_m5']]
    y_fahne = [
        (Q('Wand', *EL['fy_wand_x'], *fyr, uz[0], oz[1]), 'fahne', leer),
        (Q('Backe oben', *EL['fy_backe_o_x'], *fyr, *oz), 'fahne', leer),
        (Q('Backe unten', *EL['fy_backe_u_x'], *fyr, *uz), 'fahne', leer),
        (Q('Blatt', *EL['fy_blatt_x'], *fyr, *EL['fy_blatt_z']), 'fahne',
         leer)]
    fase_y = ('vieleck', EL['hy_fase_pkt'], 'neu', leer, hy_y[0])

    t = [text(24, 30, 'Endschalter X und Y: Halter und Fahnen '
              '(Portal.py Rev. {})'.format(pm.REVISION), 14, TEXT,
              fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Portal und '
              'Toolhead stehen am Schaltpunkt, {} mm vor dem Schienenende. '
              'Orange: neu (PETG), schwarz: Fahnen und Klammer (schwarz '
              'drucken).'.format(de(ew('schaltabstand'), 0)), 9, GRAU)]

    # ---- Feld 1: Y von hinten (X nach rechts, Z nach oben) -----------------
    f1 = Feld(250, 100, (236.0, 300.0), (-72.0, 14.0), 4.4)
    rahmen_2040 = ('svg', profil_schnitt(f1, R - 10.0, R + 10.0,
                                         L['rahmen_z0'], EL['rahmen_z1'],
                                         'lruo'), -L['rahmen_y'][0])
    teile1 = (y_rahmen + y_portal + y_neu + y_fahne + [fase_y, rahmen_2040])
    t += f1.ausschnitt('y1', ansicht(f1, teile1, 'x', 'z', 'y', -1))
    t += f1.rahmen('Y: rechte Seite, von hinten gesehen')
    t += f1.spalte([
        (R, -64.0, 'rechtes 2040 (Stirnseite)'),
        (EL['aussen_x'] - 3.6, EL['nut_o_z'],
         'obere Nut: Rücklauf des\nY-Riemens — bleibt frei'),
        (EL['aussen_x'] - 3.0, EL['nut_u_z'] + 3.0,
         'untere Nut: 2 Hammermuttern'),
        (R + 8.0, -24.0, 'Y-Wagen'), (240.0, -13.0, 'Schlittenplatte')],
        f1.ox - 12, 'end', abstand=24.0)
    t += f1.spalte([
        (EL['fy_blatt_x'][1], EL['fy_blatt_z'][0] + 4.0,
         'Fahne: Klammer um die\nPlattenkante, Blatt in der\nGabel'),
        (EL['ly_arme_x'][1][1], EL['ly_gabel_z'][1] - 2.0,
         'Lichtschranke, Gabel oben'),
        (EL['hy_boden_x'][1], EL['hy_boden_z'][0] + 1.0,
         'Halter Y: Boden mit zwei\nM2-Einsätzen'),
        (EL['hy_fuss_x'][1] + ew('m5_kopf_h'), EL['hy_m5'][0][1],
         '2 × M5×{} in die untere Nut'.format(de(EL['hy_m5_schraube'], 0)))],
        f1.ox + f1.breite + 12, 'start', abstand=26.0)
    t += quer_mass(f1, EL['aussen_x'], EL['gy_x'], -69.0,
                   '{} mm'.format(de(EL['gy_x'] - EL['aussen_x'], 1)), dy=13)
    t += f1.mass(295.5, EL['ly_pcb_z'][1], EL['rahmen_z1'],
                 '{} mm'.format(de(EL['rahmen_z1'] - EL['ly_pcb_z'][1], 1)))
    t.append(f1.linie(EL['aussen_x'], EL['rahmen_z1'], 298.0,
                      EL['rahmen_z1'], '#9aa4b1', 0.5))
    t += f1.luft(EL['y_wagen_x1'], -24.0, EL['ly_arme_x'][0][0], -24.0,
                 '{} mm'.format(de(EL['ly_arme_x'][0][0] - EL['y_wagen_x1'],
                                   2)), dx=4, dy=-4)

    # ---- Feld 2: Y von rechts aussen (Y nach rechts = vorn) ----------------
    # von rechts gesehen liegt vorn links: Y laeuft nach links
    f2 = Feld(f1.ox + f1.breite + 230, 100, (-372.0, -196.0), (-134.0, 14.0),
              2.05, a_rueck=True)
    quer_schnitt = ('svg', profil_schnitt(
        f2, L['quer_y_hinten'][0], L['quer_y_hinten'][1], L['quer_z'][0],
        L['quer_z'][1], 'lruo'), 300.0)
    winkel = (Q('Winkel', EL['aussen_x'], EL['aussen_x'] + 20.0,
                *L['quer_y_hinten'], L['rahmen_z0'], L['rahmen_z0'] + 20.0),
              'stahl', {'fill_opacity': '0.8'})
    nut_linien = []
    for zn in (EL['nut_u_z'], EL['nut_o_z']):
        for s in (-1, 1):
            nut_linien.append(('svg', f2.linie(
                L['rahmen_y'][0], zn + s * 3.1, -196.0, zn + s * 3.1,
                '#8c939e', 0.6), EL['aussen_x'] + 0.01))
    teile2 = ([(Q('2040', R - 10.0, R + 10.0, L['rahmen_y'][0], 240.0,
                  L['rahmen_z0'], EL['rahmen_z1']), 'profil', leer)]
              + nut_linien + y_rahmen + y_portal + y_neu + y_fahne
              + [winkel, quer_schnitt])
    kreise = [('svg', f2.kreis(yy, zz, k, 'stahl'), 400.0)
              for yy, zz in EL['hy_m5']]
    t += f2.ausschnitt('y2', ansicht(f2, teile2 + kreise, 'y', 'z', 'x', 1))
    t += f2.rahmen('Y: von rechts außen (vorn links, hinten rechts)')
    t += f2.spalte([
        (-240.0, -100.0, 'hinteres 2060'),
        (-240.0, L['rahmen_z0'] + 10.0, 'Winkel an der\nKreuzung (20 mm)'),
        (-275.0, -20.0, 'Y-Wagen: {} mm vor dem\nSchienenende'.format(
            de(ew('schaltabstand'), 0))),
        (-250.0, -12.0, 'Schlittenplatte')],
        f2.ox - 12, 'end', abstand=26.0)
    t += f2.spalte([
        (-356.0, -45.0, 'rechtes 2040, Ende'),
        (-340.0, EL['nut_o_z'], 'Rücklauf in der oberen Nut'),
        (EL['ly_strahl_y'], EL['ly_gabel_z'][1],
         'Fahne am Strahl'),
        (hy_y[0] + 4.0, EL['nut_u_z'], 'Halter Y, M5 in der unteren Nut')],
        f2.ox + f2.breite + 12, 'start', abstand=26.0)
    t += quer_mass(f2, hy_y[1], L['quer_y_hinten'][0], -122.0,
                   '{} mm'.format(de(L['quer_y_hinten'][0] - hy_y[1], 0)))
    for yy, zz in ((L['y_schiene_y'][0], EL['rahmen_z1'] + 8.0),
                   (L['wagen_y0'] + dy, L['y_wagen_z0'])):
        t.append(f2.linie(yy, zz, yy, 5.5, '#9aa4b1', 0.5))
    t += quer_mass(f2, L['y_schiene_y'][0], L['wagen_y0'] + dy, 4.0,
                   'Schienenende {} mm'.format(de(L['wagen_y0'] + dy
                                                  - L['y_schiene_y'][0], 0)))

    # ---- Teile X (relativ zum Portal; Toolhead am Schaltpunkt) -------------
    hyr = EL['hx_y_rel']
    zb = ew('hx_zunge_b') / 2.0
    x_neu = [
        (Q('Block', *EL['hx_x'], *hyr, *EL['hx_z']), 'neu', leer),
        (Q('Zunge', *EL['hx_zunge_x'], hyr[0] - ew('hx_zunge_t'), hyr[0],
           -zb, zb), 'neu', leer),
        (Q('Platine', *EL['lx_pcb_x'], *EL['lx_pcb_y_rel'], *EL['lx_pcb_z']),
         'platine', leer)]
    x_neu += [(Q('Gabel', *EL['lx_gabel_x'], *EL['lx_gabel_y_rel'], *a),
               'gabel', leer) for a in EL['lx_arme_z']]
    wx = (EL['kx_wand_x'][0] + xs, EL['kx_wand_x'][1] + xs)
    bx = (EL['kx_backe_x'][0] + xs, EL['kx_backe_x'][1] + xs)
    kx = (EL['kx_kopf_x'][0] + xs, EL['kx_kopf_x'][1] + xs)
    fx = (EL['fx_x_rel'][0] + xs, EL['fx_x_rel'][1] + xs)
    hz1 = EL['kx_backe_h_z'][1]
    ueber = EL['kx_steg_y0'] - EL['kx_backe_h_y'][0]
    x_klammer = [
        (Q('Wand', *wx, EL['kx_backe_h_y'][0], EL['kx_backe_v_y'][1],
           ew('kx_z0'), EL['kx_steg_z1']), 'fahne', leer),
        (Q('Backe hinten', *bx, *EL['kx_backe_h_y'], *EL['kx_backe_h_z']),
         'fahne', leer),
        (Q('Backe vorn', *bx, *EL['kx_backe_v_y'], *EL['kx_backe_v_z']),
         'fahne', leer),
        (Q('Blatt', *fx, *EL['fx_y_rel'], *EL['fx_z']), 'fahne',
         {'fill': '#3d434c'})]
    kopf_xz = [(kx[1], EL['kx_kopf_z'][1]), (kx[0], EL['kx_kopf_z'][1]),
               (kx[0], EL['kx_kopf_z'][0]), (wx[0], EL['kx_kopf_fase_z']),
               (kx[1], EL['kx_kopf_fase_z'])]
    x_portal = [(P[n], a, leer) for n, a in (
        ('Portalrohr', 'profil'), ('X-Schiene', 'fuehrung'),
        ('Stirnblock links', 'druck'), ('Rueckwand links', 'druck'),
        ('Platte links', 'druck'), ('Y-Wagen links', 'fuehrung'),
        ('Klemmturm vorn links', 'druck'),
        ('Klemmturm vorn links oben', 'druck'),
        ('Klemmturm hinten links', 'druck'),
        ('Klemmturm hinten links oben', 'druck'),
        ('Motorhalter Saeule hinten', 'druck'),
        ('Motorhalter Saeule aussen', 'druck'), ('Motorplatte', 'druck'),
        ('X-Motor', 'kauf'), ('X-Ritzel', 'kauf'))]
    trum = bauraum.x_riemen_trume(L, xs, tw('traeger_x_links'),
                                  tw('traeger_x_rechts'))[0]
    x_portal.append((trum, 'riemen', leer))
    x_th = [(TH[n].verschoben(0.0, xs), 'th', leer) for n in (
        'X-Wagen MGN15H', 'Traegerplatte Hauptsaeule', 'Saeulenrippe links',
        'Riemenhalter', 'Schienensockel')]
    x_rahmen = [(Q(q.name, *q.x, -500.0, 500.0, *q.z), a, leer)
                for q, a in ((P['Rahmen 2040 links'], 'profil'),
                             (P['Y-Schiene links'], 'fuehrung'),
                             (P['Y-Riemen links'], 'riemen'),
                             (P['Y-Ruecklauf links'], 'riemen'))]

    # ---- Feld 3: X von vorn (X nach links, Z nach oben) --------------------
    oy2 = max(f1.oy + f1.hoehe, f2.oy + f2.hoehe) + 90
    f3 = Feld(250, oy2, (-292.0, -186.0), (-72.0, 44.0), 3.3, a_rueck=True)
    teile3 = (x_rahmen[:2] + x_portal + x_th + x_neu + x_klammer
              + [('vieleck', kopf_xz, 'fahne', leer, 30.0)])
    t += f3.ausschnitt('x3', ansicht(f3, teile3, 'x', 'z', 'y', 1))
    t += f3.rahmen('X: linkes Ende, von vorn gesehen')
    t += f3.spalte([
        (xs - 5.0, 30.0, 'Trägerplatte (Toolhead)'),
        (xs - 27.0, 12.0, 'X-Wagen'),
        (bx[1] - 2.0, -36.0, 'Klammer X an der\nTrägerplatte'),
        (fx[0] + 2.0, 0.0, 'Fahne X: Blatt mitten\nim Spalt, Langloch ±{} mm'
         .format(de(ew('fx_verstellung'), 0)))],
        f3.ox - 12, 'end', abstand=26.0)
    t += f3.spalte([
        (-250.0, 40.0, 'X-Motor'), (-250.0, 26.0, 'Ritzel, X-Riemen'),
        (-262.0, 0.0, 'Stirnblock am Rohrende'),
        (EL['lx_pcb_x'][0] + 4.0, -8.0, 'Lichtschranke senkrecht,\nGabel '
         'nach vorn'),
        (EL['hx_x'][0] + 2.0, -10.5, 'Halter X: M5 in der vorderen\n'
         'Nut der 2020 (Portalrohr)'),
        (-257.0, -50.0, 'linkes 2040, Y-Schiene')],
        f3.ox + f3.breite + 12, 'start', abstand=26.0)

    # ---- Feld 4: X von oben (vorn unten) -----------------------------------
    f4 = Feld(f3.ox + f3.breite + 230, oy2, (-292.0, -186.0), (-52.0, 26.0),
              3.3, b_runter=True)
    oben = ('X-Motor', 'Motorplatte', 'Motorhalter Saeule hinten',
            'Motorhalter Saeule aussen', 'X-Ritzel')
    x_portal4 = [(q, a, gestr if q.name in oben else m)
                 for q, a, m in x_portal]
    teile4 = x_rahmen + x_portal4 + x_th + x_neu + x_klammer
    t += f4.ausschnitt('x4', ansicht(f4, teile4, 'x', 'y', 'z', 1))
    t += f4.rahmen('X: linkes Ende, von oben (vorn unten)')
    t += f4.spalte([
        (-240.0, -26.0, 'Portalrohr 2020'), (-265.0, -40.0, 'X-Motor darüber '
                                             '(Umriss)'),
        (EL['hx_x'][0] + 3.0, -10.0, 'Halter X'),
        (EL['lx_gabel_x'][0], 8.0, 'Gabel, Spalt waagerecht'),
        (fx[0] + 3.0, 10.0, 'Fahne X'), (xs, 4.0, 'Trägerplatte')],
        f4.ox + f4.breite + 12, 'start', abstand=24.0)
    t += quer_mass(f4, EL['lx_pcb_x'][1], L['x_schiene_x'][0], 23.0,
                   '{} mm'.format(de(ew('hx_luft_wagen'), 0)), dy=-4)

    # ---- Feld 5: Klammer X von links (Y nach links = vorn) -----------------
    oy3 = max(f3.oy + f3.hoehe, f4.oy + f4.hoehe) + 90
    f5 = Feld(250, oy3, (-22.0, 26.0), (-46.0, 20.0), 4.2, a_rueck=True)
    ys = EL['kx_backe_h_y'][0]
    wand_yz = [(ys, ew('kx_z0')), (EL['kx_backe_v_y'][1], ew('kx_z0')),
               (EL['kx_backe_v_y'][1], EL['kx_steg_z1']),
               (EL['kx_steg_y0'], EL['kx_steg_z1']),
               (EL['kx_steg_y0'], hz1 + ueber), (ys, hz1)]
    kopf = (Q('Kopf', *kx, *EL['fx_y_rel'], EL['kx_kopf_fase_z'],
              EL['kx_kopf_z'][1]), 'fahne', leer)
    ex, ez = EL['kx_einsatz_v']
    teile5 = [
        (TH['Traegerplatte Hauptsaeule'], 'th', leer),
        (TH['Saeulenrippe links'], 'th', leer),
        (TH['X-Wagen MGN15H'], 'th', leer),
        ('vieleck', wand_yz, 'fahne', {'fill': '#40464f'}, -30.0),
        kopf,
        (Q('Madenschraube', ex - 1.5, ex + 1.5, EL['kx_backe_v_y'][1],
           EL['kx_backe_v_y'][1] + 2.0, ez - 1.5, ez + 1.5), 'stahl', leer),
        (Q('Blatt', *EL['fx_x_rel'], *EL['fx_y_rel'], *EL['fx_z']), 'fahne',
         {'fill': '#3d434c'})]
    t += f5.ausschnitt('x5', ansicht(f5, teile5, 'y', 'z', 'x', -1))
    t += f5.rahmen('Klammer X von links')
    t += f5.spalte([
        (4.0, 10.0, 'Trägerplatte'), (11.0, 10.0, 'Seitenrippe'),
        (-8.0, 8.0, 'X-Wagen')],
        f5.ox + f5.breite + 12, 'start', abstand=24.0)
    t += f5.spalte([
        (EL['kx_backe_v_y'][1] + 1.0, ez, 'Madenschraube M3 auf\ndie Rippe'),
        (EL['fx_y_rel'][1], 0.0, 'Kopf und Blatt'),
        (EL['kx_backe_h_y'][0], -32.0, 'Klammer: hinten hinter der\nPlatte, '
         'vorn vor der Rippe'),
        (EL['kx_steg_y0'], -18.0, '45°: über dem Wagen nur\nvor der Platte')],
        f5.ox - 12, 'end', abstand=26.0)

    # ---- Zahlen ------------------------------------------------------------
    ty = f5.oy + 30
    tx = f5.ox + f5.breite + 200
    zeilen = [
        ('Y', 'Halter aussen am rechten 2040, {} mm hinter dem hinteren 2060, '
         '2 × M5×{} in der unteren Nut'.format(
             de(L['quer_y_hinten'][0] - hy_y[1], 0),
             de(EL['hy_m5_schraube'], 0))),
        ('', 'Gabel {} mm neben der Profilfläche, Platine {} mm unter der '
         'Oberkante der 2040'.format(de(EL['gy_x'] - EL['aussen_x'], 1),
                                      de(EL['rahmen_z1'] - EL['ly_pcb_z'][1],
                                         1))),
        ('', 'Fahne: Klammer an der rechten Schlittenplatte, {} mm vor '
         'ihrer Hinterkante, verschiebbar'.format(
             de(ew('fy_hinten') - L['platte_y0'], 0))),
        ('X', 'Halter vor dem linken Ende der 2020, M5×{} in ihrer '
         'vorderen Nut, stößt an die X-Schiene; fährt mit dem Portal'.format(
             de(EL['hx_m5_schraube'], 0))),
        ('', 'Platine {} mm vor dem Wagenende am Schienenende; Blatt '
         'verstellbar ±{} mm'.format(de(ew('hx_luft_wagen'), 0),
                                     de(ew('fx_verstellung'), 0))),
        ('Blatt', '{} mm dick, je {} mm Luft im Spalt, bis {} mm an die '
         'Platine ({} mm über den Strahl)'.format(
             de(ew('fahne_dicke'), 0),
             de((ew('ls_schlitz') - ew('fahne_dicke')) / 2.0, 1),
             de(ew('fahne_ab_platine'), 1),
             de(ew('ls_strahl_hoehe') - ew('fahne_ab_platine'), 1))),
        ('Druck', 'PETG; Fahnen und Klammer schwarz (helles PETG lässt IR '
         'durch); keine Stützen'),
        ('GRBL', '$23=1 (X nach links), $130={}, $131={} (1 mm Rückzug, '
         '2 mm Reserve)'
         .format(de(L['xw_max'] - xs - 1.0 - 2.0, 0),
                 de(portal_check.y_weg(w, L, TL, feste, bewegte)[1]
                    + EL['y_weg_hinten'] - ew('schaltabstand') - 3.0, 0))),
    ]
    t.append(text(tx, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k_, v) in enumerate(zeilen):
        t.append(text(tx, ty + 10 + i * 15, k_, 8.5, GRAU))
        t.append(text(tx + 44, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 18
    for i, (art, s) in enumerate((('neu', 'Halter (PETG)'),
                                  ('fahne', 'Fahne, Klammer (schwarz)'),
                                  ('platine', 'Lichtschranke: Platine'),
                                  ('gabel', 'Gabel'),
                                  ('druck', 'Portal'), ('th', 'Toolhead'),
                                  ('profil', 'Aluprofil'),
                                  ('fuehrung', 'Schiene, Wagen'))):
        x = tx + (i % 4) * 150
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    y = ly + 36
    t.append(linie(tx, y + 4.5, tx + 16, y + 4.5, '#2b2f36', 3.0))
    t.append(text(tx + 21, y + 8, 'Riemen', 8.5))
    t.append(rect_px(tx + 150, y, tx + 164, y + 9, 'stahl'))
    t.append(text(tx + 169, y + 8, 'Schrauben, Nutsteine, Winkel', 8.5))

    W = int(max(f2.ox + f2.breite, f4.ox + f4.breite) + 230)
    H = int(max(f5.oy + f5.hoehe, ly + 60) + 30)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as fd:
        fd.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)


if __name__ == '__main__':
    main()
