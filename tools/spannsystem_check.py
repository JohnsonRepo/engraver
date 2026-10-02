#!/usr/bin/env python3
"""Spannsystem mit Werkstueckerkennung — Konzeptpruefung, laeuft ohne
Fusion.

Fester Anschlag vorn links: eine Anschlagleiste liegt am vorderen 2060 an,
ein linker Anschlag daneben. Eine Spannbacke drueckt die Platte von hinten
gegen die Leiste; ein eigener NEMA 17 unter dem linken 2040 verfaehrt sie
in Y ueber einen GT2-Riemen. Beim Spannen misst sie die Tiefe der Platte:
Schritte vom Referenzschalter bis zu dem Moment, in dem die Platte die
Leiste 0,6 mm gegen ihre Federn an das 2060 drueckt — dort sitzt eine
Gabellichtschranke. Beide Schalter stehen fest, kein Kabel faehrt mit.

Importiert Portal.py und ToolheadZ.py mit gestubbtem adsk-Modul und
prueft: wohin die tiefen Teile des Toolheads kommen, welches Z-Softlimit
Leiste, Anschlag und Backe schuetzt und welche Fokusabstaende damit gehen,
ob der Antrieb neben dem Arbeitsbereich frei bleibt (ganzer X-, Y- und
Z-Weg), welche Plattentiefen die Backe abdeckt, Kraft, Zeit, Aufloesung und
die Leistung am Netzteil.

    python3 tools/spannsystem_check.py

Exit-Code 0 = alle Pruefungen bestanden. Die Masse stehen hier, bis die
Teile in Fusion gezeichnet werden — dann wandern sie ins Skript.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

# --- Masse (einzige Quelle fuer Pruefung und Zeichnung) ----------------------
# Name: (Wert, Kommentar). Laengen in mm. Koordinaten wie portal_check.py,
# Abschnitt 14: Rahmen fest, Portal in der Mitte seines Wegs, X = 0 in der
# Rahmenmitte, Y nach vorn (zum Bediener), Z = 0 in der Mitte des Portalrohrs.
MASSE = {
    # --- Opferplatte: liegt auf dem Tisch zwischen den 2060 ----------------
    'opfer_dicke':        (6.0, 'Opferplatte: Dicke [?] (MDF/Sperrholz)'),
    'opfer_x0':        (-224.0, 'Opferplatte: linke Kante (endet vor dem Backenhalter)'),
    'opfer_x1':         (230.0, 'Opferplatte: rechte Kante'),
    'opfer_spiel':        (1.0, 'Opferplatte: Spiel zu jedem 2060'),

    # --- fester Anschlag ----------------------------------------------------
    # Alu-Flachstange 25 x 3, liegt auf der Opferplatte, die Vorderkante am
    # vorderen 2060: das 2060 nimmt die Spannkraft auf und legt die Leiste
    # parallel zu X (feinjustieren mit Folie dahinter). Rechts fest
    # geklemmt, links haelt eine Feder sie 1 mm vom 2060 weg — drueckt die
    # Platte sie an, meldet das eine Gabellichtschranke im Antriebshalter.
    'leiste_b':          (25.0, 'Anschlagleiste: Breite (Alu-Flach 25 x 3)'),
    'leiste_h':           (3.0, 'Anschlagleiste: Dicke = Anschlaghoehe'),
    'leiste_x0':       (-232.0, 'Anschlagleiste: linkes Ende (im Antriebshalter)'),
    # Linker Anschlag: ein Stueck derselben Stange hinter der Leiste, links
    # im Antriebshalter geklemmt, Langloch in X zum Einstellen.
    'anschlag_x':      (-198.0, 'linker Anschlag: Anlageflaeche (X)'),
    'anschlag_l':        (20.0, 'linker Anschlag: Laenge in Y hinter der Leiste'),
    'halter_r_b':        (18.0, 'Leistenhalter rechts: Breite (X)'),
    'halter_h':          (14.0, 'Leistenhalter: Hoehe ueber dem Bett'),

    # --- Spannbacke ---------------------------------------------------------
    # Alu-Flach 15 x 3, schwebt 0,5 mm ueber der Opferplatte, damit sie nicht
    # in Brandspuren haengen bleibt. Sitzt auf einem Block, der im
    # Backenhalter in Y federt: die Feder bestimmt die Spannkraft.
    'backe_b':           (15.0, 'Backe: Breite in Y'),
    'backe_h':            (3.0, 'Backe: Hoehe'),
    'backe_schwebt':      (0.5, 'Backe: Luft ueber der Opferplatte'),
    'backe_x1':         (-90.0, 'Backe: rechtes Ende'),
    'backe_vor':          (8.0, 'Backe: Anlageflaeche vor der Haltermitte'),
    'halter_l':          (20.0, 'Backenhalter: Laenge in Y'),
    'block_b':            (5.0, 'Backenhalter: Block innen, Dicke in X'),
    'platte_d':           (4.0, 'Backenhalter: Platte unter dem Wagen'),
    'klemme_y0':          (4.0, 'Riemenklemme: beginnt so weit vor der Haltermitte'),
    'klemme_l':          (12.0, 'Riemenklemme: Laenge in Y'),
    'klemme_b':           (8.0, 'Riemenklemme: Breite in X'),
    'wagen_vor':          (5.0, 'Wagen: Mitte so weit vor der Haltermitte'),

    # --- Fuehrung: MGN9H unter dem linken 2040 [w] ---------------------------
    # MGN9 statt MGN12: mit 10 mm Bauhoehe passt die Halterplatte ueber den
    # Motor hinweg, die Backe faehrt so bis ganz nach vorn.
    'schiene_b':          (9.0, 'MGN9: Schienenbreite'),
    'schiene_h':          (6.5, 'MGN9: Schienenhoehe'),
    'wagen_b':           (20.0, 'MGN9H: Wagenbreite'),
    'wagen_l':           (39.9, 'MGN9H: Wagenlaenge'),
    'wagen_h':           (10.0, 'MGN9H: Montagehoehe (Schienenfuss -> Wagen)'),

    # --- Antrieb: NEMA 17 vorn, GT2-Riemen aussen neben dem 2040 -------------
    # Motor liegt quer unter dem 2040 auf Tischhoehe, Welle nach aussen; das
    # Ritzel treibt einen offenen Riemen, der aussen neben dem 2040 laeuft —
    # dort kommt weder Toolhead noch Portal hin. Umlenkrolle hinten am 2060.
    'riemen_x':        (-282.0, 'Riemenebene (X), aussen neben dem 2040'),
    'motor_flansch':     (42.3, 'NEMA 17: Flanschmass'),
    'motor_laenge':      (37.0, 'NEMA 17: Koerper ohne Welle [?] wie die anderen'),
    'motor_tisch':        (0.5, 'Motor: Luft zum Tisch'),
    'motor_y_luft':       (1.0, 'Motor: Luft zum vorderen 2060'),
    'motorplatte':        (4.0, 'Antriebshalter: Platte am Motorflansch'),
    'ritzel_d':          (16.0, 'GT2 20 Z: Flansch'),
    'ritzel_teilkreis': (12.73, 'GT2 20 Z: Teilkreis'),
    'rolle_d':           (18.0, 'Umlenkrolle 20 Z mit Lager: Huelle'),
    'rolle_b':            (8.5, 'Umlenkrolle: Breite'),
    'umlenk_y':          (25.0, 'Umlenkhalter hinten: Tiefe ab dem 2060'),
    'umlenk_b':          (20.0, 'Umlenkhalter: Breite (X)'),

    # --- Luft ----------------------------------------------------------------
    # Ueber den flachen Teilen haelt das Z-Softlimit den Toolhead auf
    # Abstand; der Antrieb bleibt seitlich luft_bau (Portal.py) davon weg.
    'luft_kopf':          (2.0, 'Toolhead (Softlimit) -> flache Teile'),
    'luft_backe':         (2.0, 'Backe -> linker Anschlag'),
    'einlege_luft':       (5.0, 'offene Backe hinter der tiefsten Platte'),
    'h_min_soll':        (30.0, 'kleinste Plattentiefe, die gespannt werden soll'),

    # --- Kraft ---------------------------------------------------------------
    # Der Laser uebt keine Kraft aus: die Backe haelt die Platte nur gegen
    # Stoesse und Luft. Die Feder der Backe bestimmt die Kraft, nicht der
    # Motor. Sie ist staerker vorgespannt als die Leiste — so bleibt die
    # Backe starr, bis die Leiste geschaltet hat, und die Messung haengt
    # nicht an der Feder.
    'leiste_vor':         (2.0, 'Leiste: Federvorspannung in N'),
    'leiste_weg':         (1.0, 'Leiste: Weg bis an das 2060'),
    'leiste_schalt':      (0.6, 'Leiste: Lichtschranke schaltet nach'),
    'feder_vor':          (3.0, 'Backe: Federvorspannung in N'),
    'feder_k':            (1.0, 'Backe: Federrate in N/mm'),
    'feder_weg':         (15.0, 'Backe: Federweg im Halter'),
    'spann_leicht':       (2.0, 'Backe: Nachschub nach dem Schalten, leicht'),
    'spann_fest':        (12.0, 'Backe: Nachschub nach dem Schalten, fest'),
    'motor_moment':      (0.30, 'NEMA 17: Haltemoment in Nm [?]'),
    'moment_nutz':       (0.50, 'davon beim langsamen Fahren nutzbar'),
    'reibung':            (2.0, 'Wagen und Riemen: Reibung in N'),

    # --- Fahrt ---------------------------------------------------------------
    'mikroschritte':     (16.0, 'TMC2209: MS1 + MS2 = 1/16'),
    'v_fahrt':           (40.0, 'Fahrt in mm/s'),
    'v_tasten':           (3.0, 'Antasten in mm/s'),
    'v_spannen':         (10.0, 'Feder spannen in mm/s'),
    'zurueck':            (3.0, 'nach dem ersten Schalten so weit zurueck'),
    'schritte_max':    (4000.0, 'Schritte/s, die ein Nano sicher erzeugt'),

    # --- Werkstueck ----------------------------------------------------------
    't_min':              (1.5, 'duennste Platte, die gespannt wird'),
    # Knickprobe: Acryl 1,5 mm, 100 breit, 300 tief [w]
    'knick_e':         (3000.0, 'Acryl: E-Modul in N/mm2'),
    'knick_b':          (100.0, 'Knickprobe: Breite'),
    'knick_l':          (300.0, 'Knickprobe: Laenge in Spannrichtung'),

    # --- Leistung ------------------------------------------------------------
    'spann_strom':        (0.6, 'Spannmotor: Strom am Vref in A'),
}


def w(name):
    return MASSE[name][0]


# --- Konzept: alle Lagen ----------------------------------------------------
def konzept():
    """Lagen aller Teile des Spannsystems in Rahmenkoordinaten (Portal in
    der Mitte seines Wegs). Liefert ein dict mit den Quadern und den Werten,
    die Pruefung und Zeichnung brauchen."""
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    pw, L = pm.w, pm.lage()
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, d_hinten, _ = portal_check.y_weg(pw, L, TL, feste,
                                                        bewegte)
    K = {'th': th, 'pm': pm, 'tw': tw, 'TL': TL, 'pw': pw, 'L': L,
         'feste': feste, 'bewegte': bewegte, 'd_schiene': d_schiene,
         'd_vorn': d_vorn, 'd_hinten': d_hinten}
    luft = pw('luft_bau')
    K['luft'] = luft

    # ---- Arbeitsflaeche und Reichweite der tiefen Teile ---------------------
    sy = TL['strahl_y']
    K['arbeit_x'] = (L['xw_min'], L['xw_max'])
    K['arbeit_y'] = (sy - d_hinten, sy + d_vorn)
    # Tief sind die Teile, die mit Z unten unter die Oberkante der 2060
    # haengen: Laser, Schlittenplatte, Pad. Der Laser wandert mit der
    # Langlochstellung, Platte und Pad nicht.
    K['tief'] = [q for q in bewegte
                 if q.z[0] + TL['zc_min'] < L['quer_z'][1]]
    K['schlitten_z0'] = min(q.z[0] for q in K['tief']
                            if q.name != 'Diodenlaser')
    K['reich_x'] = reichweite_x(K)
    K['reich_y'] = (min(q.y[0] for q in K['tief']) - d_hinten,
                    max(q.y[1] for q in K['tief']) + d_vorn)
    K['x_frei'] = K['reich_x'][0] - luft            # links davon: Antrieb

    # ---- Bett ---------------------------------------------------------------
    z_tisch = L['quer_z'][0]
    z_b = z_tisch + w('opfer_dicke')
    K['z_tisch'], K['z_b'] = z_tisch, z_b
    yv = L['quer_y_vorn'][0]                     # Innenseite vorderes 2060
    yh = L['quer_y_hinten'][1]                   # Innenseite hinteres 2060
    K['yv'], K['yh'] = yv, yh
    K['opfer'] = Quader('Opferplatte', w('opfer_x0'), w('opfer_x1'),
                        yh + w('opfer_spiel'), yv - w('opfer_spiel'),
                        z_tisch, z_b, 'kaufteil')

    # ---- fester Anschlag ---------------------------------------------------
    yf = yv - w('leiste_b')                      # Plattenvorderkante
    x0 = w('anschlag_x')                         # Plattenlinkskante
    K['yf'], K['x0'] = yf, x0
    # Rechts haelt ein Halter die Leiste, ausserhalb der Reichweite des
    # Lasers in diesem Streifen (Platte und Pad kommen nicht so weit vor).
    K['reich_x_leiste'] = reichweite_x(K, yf, yv)
    xr0 = K['reich_x_leiste'][1] + luft
    xr1 = xr0 + w('halter_r_b')
    K['leiste'] = Quader('Anschlagleiste', w('leiste_x0'), xr1 - 2.0, yf, yv,
                         z_b, z_b + w('leiste_h'), 'kaufteil')
    # endet hinter der Leiste, auch wenn ihre Feder sie 1 mm zurueckschiebt
    K['anschlag'] = Quader('linker Anschlag', w('leiste_x0'), x0,
                           yf - w('anschlag_l'),
                           yf - w('leiste_weg') - 0.5, z_b,
                           z_b + w('leiste_h'), 'kaufteil')
    K['halter_r'] = Quader('Leistenhalter rechts', xr0, xr1, yf, yv, z_b,
                           z_b + w('halter_h'))

    # ---- Antrieb vorn: Motor quer unter dem 2040, Ritzel aussen ------------
    fl = w('motor_flansch')
    rx = w('riemen_x')
    # Ritzel: Spur um die Riemenebene, Nabe zum Motor hin; der Flansch des
    # Motors liegt an der Platte des Halters, die Nabe taucht in ihre
    # Bohrung (wie am X-Motor).
    rit_x = (rx - 4.5, rx + 11.5)
    mx0 = rit_x[1] + 0.5
    my1 = yv - w('motor_y_luft')
    mz0 = z_tisch + w('motor_tisch')
    K['motor'] = Quader('Spannmotor', mx0, mx0 + w('motor_laenge'),
                        my1 - fl, my1, mz0, mz0 + fl, 'kaufteil')
    ym, zm = my1 - fl / 2.0, mz0 + fl / 2.0
    K['motor_achse'] = (ym, zm)
    rr = w('ritzel_d') / 2.0
    K['ritzel'] = Quader('Ritzel', rit_x[0], rit_x[1], ym - rr, ym + rr,
                         zm - rr, zm + rr, 'kaufteil')
    # Antriebshalter: Wiege um den Motor, Platte am Flansch, vorn am 2060
    # verschraubt; innen klemmt er Leiste und Anschlag. Oben nicht hoeher
    # als der Motor — darueber faehrt die Halterplatte der Backe.
    K['halter_v'] = Quader('Antriebshalter', mx0 - w('motorplatte'),
                           K['x_frei'], my1 - fl - luft, yv, z_tisch,
                           mz0 + fl)
    # ---- Umlenkung hinten ---------------------------------------------------
    ry = yh + luft + w('rolle_d') / 2.0
    K['rolle'] = Quader('Umlenkrolle', rx - w('rolle_b') / 2.0,
                        rx + w('rolle_b') / 2.0, ry - w('rolle_d') / 2.0,
                        ry + w('rolle_d') / 2.0, zm - w('rolle_d') / 2.0,
                        zm + w('rolle_d') / 2.0, 'kaufteil')
    K['halter_h'] = Quader('Umlenkhalter', rx - w('umlenk_b') / 2.0,
                           rx + w('umlenk_b') / 2.0, yh, yh + w('umlenk_y'),
                           z_tisch, zm + w('rolle_d') / 2.0 + 3.0)
    K['rolle_y'] = ry
    t2 = w('ritzel_teilkreis') / 2.0
    K['riemen'] = Quader('Riemen', rx - 3.0, rx + 3.0, ry, ym, zm - t2 - 0.7,
                         zm + t2 + 0.7, 'kaufteil')
    K['riemen_oben_z'] = zm + t2                 # Wirklinie, gezogener Trum

    # ---- Schlitten: Wagen, Halter, Klemme, Block, Backe (relativ zu c) -----
    xs = -L['R']                                 # Mitte des linken 2040
    wz1 = L['rahmen_z0']                         # Schienenfuss = 2040 unten
    wz0 = wz1 - w('wagen_h')                     # Montageflaeche des Wagens
    hl = w('halter_l') / 2.0
    pz0 = wz0 - w('platte_d')
    kx = (rx - w('klemme_b') / 2.0, rx + w('klemme_b') / 2.0)
    bz0 = z_b + w('backe_schwebt')
    K['wagen_z'] = (wz0, wz1)
    K['schlitten'] = [
        Quader('Wagen MGN9H', xs - w('wagen_b') / 2.0, xs + w('wagen_b') / 2.0,
               w('wagen_vor') - w('wagen_l') / 2.0,
               w('wagen_vor') + w('wagen_l') / 2.0, wz0, wz1 - 1.0,
               'fuehrung'),
        Quader('Halterplatte', kx[0], K['x_frei'], -hl, hl, pz0, wz0),
        Quader('Riemenklemme', kx[0], kx[1], w('klemme_y0'),
               w('klemme_y0') + w('klemme_l'), K['riemen_oben_z'] - 4.0, pz0),
        Quader('Backenblock', K['x_frei'] - w('block_b'), K['x_frei'], -hl,
               hl, bz0, pz0),
        Quader('Backe', K['x_frei'], w('backe_x1'),
               w('backe_vor') - w('backe_b'), w('backe_vor'), bz0,
               bz0 + w('backe_h'), 'kaufteil')]

    # ---- Weg des Schlittens: bis luft vor jedes feste Teil ------------------
    fest = [K['halter_v'], K['motor'], K['ritzel'], K['rolle'], K['halter_h'],
            K['leiste'], K['anschlag']] + portal_check.quer_quader(pw, L)
    c_vorn, c_hinten = math.inf, -math.inf
    K['grenze_vorn'] = K['grenze_hinten'] = None
    for m in K['schlitten']:
        for f in fest:
            d = (w('luft_backe') if 'Backe' == m.name
                 and f.name in ('Anschlagleiste', 'linker Anschlag') else luft)
            if not (m.x[0] < f.x[1] + d and f.x[0] < m.x[1] + d
                    and m.z[0] < f.z[1] + d and f.z[0] < m.z[1] + d):
                continue
            if f.y[0] > 0:
                c = f.y[0] - d - m.y[1]
                if c < c_vorn:
                    c_vorn, K['grenze_vorn'] = c, (m.name, f.name)
            else:
                c = f.y[1] + d - m.y[0]
                if c > c_hinten:
                    c_hinten, K['grenze_hinten'] = c, (m.name, f.name)
    K['c'] = (c_hinten, c_vorn)
    K['backe_y'] = (c_hinten + w('backe_vor'), c_vorn + w('backe_vor'))
    K['tiefe'] = (yf - K['backe_y'][1], yf - K['backe_y'][0])  # H min, max
    wagen = K['schlitten'][0]
    K['schiene'] = Quader('Schiene MGN9', xs - w('schiene_b') / 2.0,
                          xs + w('schiene_b') / 2.0, c_hinten + wagen.y[0],
                          c_vorn + wagen.y[1], wz1 - w('schiene_h'), wz1,
                          'fuehrung')
    # offener Riemen: Klemme -> Ritzel -> unten zurueck -> Rolle -> Klemme,
    # in der Mitte des Wegs gemessen
    K['riemen_l'] = (2.0 * (ym - ry) + math.pi * w('ritzel_teilkreis')
                     + 2.0 * w('klemme_l'))

    # ---- Z-Softlimit: Schlitten bleibt luft_kopf ueber den flachen Teilen ---
    h_flach = max(w('leiste_h'), w('backe_schwebt') + w('backe_h'))
    K['h_flach'] = h_flach
    K['zc_soft'] = z_b + h_flach + w('luft_kopf') - K['schlitten_z0']
    return K


def reichweite_x(K, y0=None, y1=None):
    """X-Bereich, den die tiefen Teile des Toolheads ueber den ganzen X-Weg
    und den Y-Weg zwischen den 2060 ueberstreichen. y0, y1: nur die Teile,
    die in diesen Y-Streifen kommen."""
    L = K['L']
    xs = [(L['xw_min'] + q.x[0], L['xw_max'] + q.x[1]) for q in K['tief']
          if y0 is None or (q.y[0] - K['d_hinten'] < y1
                            and q.y[1] + K['d_vorn'] > y0)]
    return min(a for a, _ in xs), max(b for _, b in xs)


def bei(m, c):
    """Teil des Schlittens m mit der Haltermitte bei Y = c."""
    return Quader(m.name, m.x[0], m.x[1], m.y[0] + c, m.y[1] + c, m.z[0],
                  m.z[1], m.art)


def ueber_weg(m, K):
    """Huelle eines Schlittenteils ueber den ganzen Weg."""
    return Quader(m.name + ' (Weg)', m.x[0], m.x[1], m.y[0] + K['c'][0],
                  m.y[1] + K['c'][1], m.z[0], m.z[1], m.art)


def fokus(K, f, t_max):
    """Langlochstellung (mm nach oben) fuer Fokusabstand f mit Softlimit:
    duennes Material braucht die Linse bei f, dickes (t_max) bei t_max + f
    ueber dem Bett. Liefert (von, bis, stellung); von > bis: geht nicht."""
    TL, z_b = K['TL'], K['z_b']
    tief = K['zc_soft'] + TL['laser_unten_rel'] - z_b
    hoch = TL['zc_arbeit_max'] + TL['laser_unten_rel'] - z_b
    von = max(TL['langloch_ab_max'], t_max + f - hoch)
    bis = min(TL['langloch_auf_max'], f - tief)
    # wie fokus_zeilen in ToolheadZ.py: Lochmitte, wenn sie passt
    return von, bis, min(max(0.0, von), bis)


def luft_ganz(K, ziele, schritt_y=2.5):
    """Kleinste Luft zwischen den festen Quadern `ziele` und allem, was
    sich bewegt: Portal ueber den ganzen Y-Weg bis an beide Schienenenden,
    der Toolhead dazu ueber X und Z. Stellungen, in denen der Toolhead ein
    2060 oder einen Y-Motorhalter durchdringen muesste, gibt es nicht und
    werden uebersprungen. Liefert (luft, ziel, teil, dy).

    Gerechnet wird Paar fuer Paar, das naechste zuerst: Ist schon die
    Huelle eines Teils ueber alle Stellungen weiter weg als die bisher
    engste Stelle, kann das Paar sie nicht unterbieten."""
    pw, L, TL = K['pw'], K['L'], K['TL']
    lang_fest = ('Y-Schiene', 'Rahmen 2040', 'Y-Riemen', 'Y-Ruecklauf')
    portal = [q for q in bauraum.portal_bauraeume(pw, L)[0]
              if not q.name.startswith(lang_fest)]
    quer = portal_check.quer_quader(pw, L)
    halter = [q for q in portal_check.y_halter_quader(pw, L)
              if 'Ritzel' not in q.name]
    ds = K['d_schiene']
    n = int(ds / schritt_y)
    dys = sorted(set([-ds, ds, -K['d_hinten'], K['d_vorn']]
                     + [i * schritt_y for i in range(-n, n + 1)]))
    xs = [L['xw_min'] + (L['xw_max'] - L['xw_min']) * i / 20.0
          for i in range(21)]
    zs = [TL['zc_min'] + (TL['zc_max'] - TL['zc_min']) * j / 10.0
          for j in range(11)]

    def lage(q, dy, xw=0.0, zc=0.0):
        return Quader(q.name, q.x[0] + xw, q.x[1] + xw, q.y[0] + dy,
                      q.y[1] + dy, q.z[0] + zc, q.z[1] + zc, q.art)

    # Gueltige Stellungen. Die 2060 reichen ueber die ganze Breite, ob der
    # Toolhead sie durchdringt, haengt nur an Y und Z.
    toolhead = [(q, False) for q in K['feste']] + [(q, True)
                                                   for q in K['bewegte']]
    halter_y0 = min(h.y[0] for h in halter)
    gueltig = []
    for dy in dys:
        for zc in zs:
            th = [lage(q, dy, 0.0, zc if b else 0.0) for q, b in toolhead]
            if any(t.y[0] < h.y[1] and h.y[0] < t.y[1] and t.z[0] < h.z[1]
                   and h.z[0] < t.z[1] for t in th for h in quer):
                continue
            # die Y-Motorhalter stehen vor dem vorderen 2060
            vorn = [t for t in th if t.y[1] > halter_y0]
            for xw in xs:
                if not any(lage(t, 0.0, xw).abstand(h) < 0 for t in vorn
                           for h in halter):
                    gueltig.append((dy, xw, zc))

    def huelle(q, art):
        """Was das Teil ueber alle Stellungen ueberstreicht."""
        dx = (0.0, 0.0) if art == 'portal' else (xs[0], xs[-1])
        dz = (zs[0], zs[-1]) if art == 'bewegt' else (0.0, 0.0)
        return Quader(q.name, q.x[0] + dx[0], q.x[1] + dx[1],
                      q.y[0] + dys[0], q.y[1] + dys[-1], q.z[0] + dz[0],
                      q.z[1] + dz[1])

    paare = sorted(((huelle(q, art).abstand(z), i, q, art, z)
                    for i, (q, art) in enumerate(
                        [(q, 'portal') for q in portal]
                        + [(q, 'fest') for q in K['feste']]
                        + [(q, 'bewegt') for q in K['bewegte']])
                    for z in ziele), key=lambda t: (t[0], t[1]))
    engste = (math.inf, None, None, None)
    for schranke, _, q, art, z in paare:
        if schranke >= engste[0]:
            break
        if art == 'portal':
            stellungen = [(dy, 0.0, 0.0) for dy in dys]
        else:
            stellungen = gueltig
        for dy, xw, zc in stellungen:
            d = lage(q, dy, xw, zc if art == 'bewegt' else 0.0).abstand(z)
            if d < engste[0]:
                engste = (d, z.name, q.name, dy)
    return engste


def leistung_mit_spannmotor():
    """Leistungsbilanz aus elektronik_zeichnen.py plus Spannmotor. Er
    laeuft nur beim Spannen (Laser aus) und haelt danach mit Strom."""
    import elektronik_zeichnen as ez                  # noqa: E402
    b = ez.leistung()
    spann = 2.0 * w('spann_strom') ** 2 * ez.MOTOR_R + ez.TREIBER_W
    b['spann'] = spann
    b['summe_neu'] = b['summe'] + spann
    b['reserve_neu'] = b['dauer'] - b['summe_neu']
    return b


def main():
    K = konzept()
    pw, L, TL, tw = K['pw'], K['L'], K['TL'], K['tw']
    p = Pruefung()
    luft = K['luft']
    z_b, yf, x0 = K['z_b'], K['yf'], K['x0']

    # ------------------------------------------------------------------
    p.titel('1) Arbeitsflaeche und Reichweite des Toolheads unten')
    ax, ay = K['arbeit_x'], K['arbeit_y']
    p.info('Strahl erreicht X von', ax[0])
    p.info('                 bis', ax[1])
    p.info('Strahl erreicht Y von (hinten)', ay[0])
    p.info('                 bis (vorn)', ay[1])
    p.info('tiefe Teile: ' + ', '.join(q.name for q in K['tief']))
    p.info('tiefe Teile erreichen X von', K['reich_x'][0])
    p.info('                        bis', K['reich_x'][1])
    p.info('tiefe Teile erreichen Y von', K['reich_y'][0])
    p.info('                        bis', K['reich_y'][1])
    p.info('links davon frei fuer den Antrieb ab X', K['x_frei'])
    p.info('Schlittenplatte haengt unter dem Laser (Lochmitte)',
           TL['laser_unten_rel'] - K['schlitten_z0'])

    # ------------------------------------------------------------------
    p.titel('2) Fester Anschlag: Leiste am vorderen 2060, Anschlag links')
    p.info('Opferplatte', w('opfer_dicke'))
    p.info('Bett (Oberseite Opferplatte) Z', z_b)
    p.info('Plattenvorderkante (Anlage der Leiste) Y', yf)
    p.info('Plattenlinkskante (Anlage links) X', x0)
    p.ok('Strahl reicht ueber die Plattenvorderkante hinaus', ay[1] - yf,
         2.0)
    p.ok('Strahl reicht ueber die Plattenlinkskante hinaus', x0 - ax[0],
         2.0)
    p.info('groesste Platte, die der Strahl ganz erreicht (B)',
           ax[1] - x0)
    p.info('                                          (T)', yf - ay[0])
    hr = K['halter_r']
    p.ok('Leistenhalter rechts neben dem Laser (nur er kommt so weit vor)',
         hr.x[0] - K['reich_x_leiste'][1], luft)
    p.ok('Anschlag und Leiste enden links im Antriebshalter',
         K['halter_v'].x[1] - K['leiste'].x[0], 5.0)
    p.ok('Backe steht links hoechstens 1 mm ueber die Opferplatte',
         w('opfer_x0') - K['schlitten'][4].x[0], 1.0, '<=')

    # ------------------------------------------------------------------
    p.titel('3) Hoehen: Z-Softlimit schuetzt Leiste, Anschlag und Backe')
    zc_soft = K['zc_soft']
    p.info('hoechstes flaches Teil ueber dem Bett', K['h_flach'])
    p.info('Schlittenplatte bleibt darueber mindestens', w('luft_kopf'))
    p.info('tiefste Wagenmitte zc (Softlimit)', zc_soft)
    p.info('   statt mechanisch', TL['zc_min'])
    z132 = TL['zc_arbeit_max'] - zc_soft
    p.info('GRBL $132 hoechstens (vom Schaltpunkt nach unten, ohne Rueckzug)',
           z132)
    p.info('   bisher', TL['zc_arbeit_max'] - TL['zc_min'])
    tief_sl = [q.verschoben(zc_soft) for q in K['tief']]
    for s in (TL['langloch_ab_max'], TL['langloch_auf_max']):
        d = min((q.z[0] + (s if q.name == 'Diodenlaser' else 0.0)) - z_b
                for q in tief_sl) - K['h_flach']
        p.ok('am Softlimit ueber den flachen Teilen, Laser {:+.1f}'.format(s),
             d, w('luft_kopf'))
    t_max = tw('werkstueck_max')
    frei = min(tw('traeger_z_unten'), TL['z_schiene_z0']) - 5.0 - z_b
    p.info('Werkstueck moeglich bis (feste Teile, 5 mm Luft)', frei)
    p.ok('   deckt das dickste Werkstueck', frei, t_max)
    f_tief = (zc_soft + TL['laser_unten_rel'] + TL['langloch_ab_max']
              - z_b)
    f_hoch = (TL['zc_arbeit_max'] + TL['laser_unten_rel']
              + TL['langloch_auf_max'] - z_b - t_max)
    p.info('Fokusfenster fuer 0..{:.0f} mm Werkstueck: f von'.format(t_max),
           f_tief)
    p.info('                                         bis', f_hoch)
    p.ok('kurze Fokusabstaende gehen (Module ab 10 mm)', 10.0 - f_tief, 0.0)
    p.ok('lange Fokusabstaende gehen (Module bis 40 mm)', f_hoch - 40.0, 0.0)
    for f in (8.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0):
        von, bis, s = fokus(K, f, t_max)
        if von <= bis:
            p.info('   f = {:2.0f} mm: Laser {:+.1f} (geht {:+.1f} bis '
                   '{:+.1f})'.format(f, s, von, bis))
        else:
            p.info('   f = {:2.0f} mm: geht nicht fuer 0..{:.0f} mm'.format(
                f, t_max))
    p.ok('Backe fasst die duennste Platte (Anlage ueber der Opferplatte)',
         w('t_min') - w('backe_schwebt'), 0.8)

    # ------------------------------------------------------------------
    p.titel('4) Antrieb unter dem linken 2040: Bauraum')
    fest_aussen = [K['halter_v'], K['motor'], K['ritzel'], K['rolle'],
                   K['halter_h'], K['riemen'], K['schiene']]
    weg = [ueber_weg(m, K) for m in K['schlitten'] if m.name != 'Backe']
    for q in fest_aussen + weg:
        p.ok('{} links der Reichweite des Toolheads'.format(q.name),
             K['x_frei'] - q.x[1], 0.0)
    for q in fest_aussen + weg:
        p.ok('{} im Rahmen (X ab 2060-Ende, Z unter dem 2040)'.format(q.name),
             min(q.x[0] - L['quer_x'][0], L['rahmen_z0'] - q.z[1],
                 q.z[0] - K['z_tisch']), 0.0)
    quer = portal_check.quer_quader(pw, L)
    for q in fest_aussen + weg:
        p.ok('{} zwischen den 2060'.format(q.name),
             min(q.abstand(h) for h in quer), 0.0)
    p.ok('Halterplatte faehrt ueber den Motor (Luft)',
         K['schlitten'][1].z[0] - K['motor'].z[1], luft)
    p.ok('Motor unter der Schiene', K['schiene'].z[0] - K['motor'].z[1],
         luft)
    p.ok('Riemenklemme neben dem Motor (X)',
         K['motor'].x[0] - K['schlitten'][2].x[1], luft)
    p.ok('Backenblock neben dem Motor (X)',
         K['schlitten'][3].x[0] - K['motor'].x[1], luft)
    engste = luft_ganz(K, fest_aussen + weg + [K['halter_r']])
    p.ok('Antrieb frei von Portal und Toolhead [{} <-> {}, Portal '
         '{:+.1f}]'.format(engste[1], engste[2], engste[3]), engste[0],
         luft)

    # ------------------------------------------------------------------
    p.titel('5) Weg der Backe und Plattentiefe')
    hmin, hmax = K['tiefe']
    p.info('Haltermitte von', K['c'][0])
    p.info('            bis', K['c'][1])
    p.info('   vorn begrenzt: {} an {}'.format(*K['grenze_vorn']))
    p.info('   hinten begrenzt: {} an {}'.format(*K['grenze_hinten']))
    p.info('Weg der Backe', K['c'][1] - K['c'][0])
    p.info('Plattentiefe von', hmin)
    p.info('             bis', hmax)
    p.ok('kleine Platten: spannt ab', w('h_min_soll'), hmin)
    p.ok('offene Backe hinter der tiefsten Platte im Strahlbereich',
         hmax - (yf - ay[0]), w('einlege_luft'))
    p.info('Schiene MGN9, mindestens', K['schiene'].y[1] - K['schiene'].y[0])
    p.ok('   passt zwischen die 2060',
         min(K['schiene'].y[0] - K['yh'], K['yv'] - K['schiene'].y[1]), 0.0)
    p.info('Riemen GT2 6 mm, offen, etwa', K['riemen_l'])

    # ------------------------------------------------------------------
    p.titel('6) Kraft: die Feder spannt, der Motor schiebt nur')
    k = w('feder_k')
    f_leicht = w('feder_vor') + k * w('spann_leicht')
    f_fest = w('feder_vor') + k * w('spann_fest')
    p.info('Leiste schaltet bei (Platte liegt an)', w('leiste_vor'), 'N')
    p.ok('Backe bleibt starr, bis die Leiste geschaltet hat',
         w('feder_vor') / w('leiste_vor'), 1.2, '>=', 'x')
    p.ok('Leiste schaltet vor dem 2060', w('leiste_weg')
         - w('leiste_schalt'), 0.3)
    p.info('gespannt leicht', f_leicht, 'N')
    p.info('gespannt fest', f_fest, 'N')
    p.ok('Federweg der Backe reicht fuer fest', w('feder_weg'),
         w('spann_fest') + w('leiste_weg'))
    r = w('ritzel_teilkreis') / 2.0 / 1000.0
    f_motor = w('motor_moment') * w('moment_nutz') / r
    p.info('Motor schiebt am Ritzel (langsam)', f_motor, 'N')
    p.ok('Motor: Reserve ueber fest + Reibung', f_motor
         / (f_fest + w('reibung')), 1.3, '>=', 'x')
    t = w('t_min')
    p_krit = (math.pi ** 2 * w('knick_e') * w('knick_b') * t ** 3
              / (12.0 * w('knick_l') ** 2))
    p.info('Knicklast Acryl {:.1f} x {:.0f} x {:.0f} mm'.format(
        t, w('knick_b'), w('knick_l')), p_krit, 'N')
    p.ok('   leicht gespannt knickt sie nicht (Faktor)', p_krit / f_leicht,
         1.5, '>=', 'x')
    p.info('   fest gespannt waere das Faktor', p_krit / f_fest, 'x')

    # ------------------------------------------------------------------
    p.titel('7) Zeit und Aufloesung')
    spm = 200.0 * w('mikroschritte') / (20.0 * 2.0)
    p.info('Schritte je mm (GT2, 20 Z, 1/16)', spm, '1/mm')
    p.info('Aufloesung', 1.0 / spm)
    p.ok('Schrittrate bei Fahrt', w('schritte_max'), w('v_fahrt') * spm,
         '>=', '1/s')
    # schnell bis die Leiste schaltet, zurueck, langsam nachmessen, spannen
    zeit = ((hmax - hmin) / w('v_fahrt') + w('zurueck') / w('v_fahrt')
            + (w('zurueck') + w('leiste_schalt')) / w('v_tasten')
            + w('spann_fest') / w('v_spannen'))
    p.info('Spannen von ganz offen bis zur kleinsten Platte, fest', zeit,
           's')

    # ------------------------------------------------------------------
    p.titel('8) Leistung am Netzteil')
    b = leistung_mit_spannmotor()
    p.info('bisher (Motoren, Luefter, Laser)', b['summe'], 'W')
    p.info('Spannmotor ({:.1f} A, haelt mit Strom)'.format(
        w('spann_strom')), b['spann'], 'W')
    p.info('zusammen', b['summe_neu'], 'W')
    p.ok('Netzteil dauernd', b['dauer'], b['summe_neu'], '>=', 'W')
    p.info('Reserve', b['reserve_neu'], 'W')

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
