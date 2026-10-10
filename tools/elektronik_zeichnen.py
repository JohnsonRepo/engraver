#!/usr/bin/env python3
"""Zeichnung: Platz fuer die Elektronik — Vorschlag.

Draufsicht auf die ganze Maschine und Seitenansicht von links: das
Elektronikfach hinter dem hinteren 2060 mit dem Gehaeuse der Steuerung, die
Endschalter, die festen Kabelwege und die beiden Energieketten. Rahmen,
Portal und Toolhead kommen aus Portal.py und ToolheadZ.py, das Gehaeuse aus
Elektronik.py, das Fach und der Y-Weg aus tools/portal_check.py
(Abschnitte 14 und 16). Die Ketten sind gedruckt und liegen wie in
Portal.py, jede mit Wanne, Festpunkt und Kettenhalter (X seit Rev. 19, Y
seit Rev. 21). Das Netzteil ist ein Steckernetzteil und steht ausserhalb.

    python3 tools/elektronik_zeichnen.py   ->  docs/elektronik-platz.svg

Gibt ausserdem die Kabellaengen und die Spannungsfaelle der Litzen aus.
"""

import math
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import portal_check                                   # noqa: E402
from bauraum import Quader                            # noqa: E402
from antrieb_zeichnen import (el, f1, text, linie, rect_px,  # noqa: E402
                              de, TEXT, GRAU, BLAU, ROT, FARBE)
from portal_zeichnen import Feld, ORANGE              # noqa: E402
from portal_zeichnen import quer_mass                 # noqa: E402
from kette_zeichnen import schleife_y                 # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs',
                    'elektronik-platz.svg')
ELEKTRONIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                          'fusion', 'Elektronik', 'Elektronik.py')
NOTAUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                      'fusion', 'NotAus', 'NotAus.py')
PIHALTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                        'fusion', 'PiHalter', 'PiHalter.py')

# ---- Ketten ----------------------------------------------------------------
# Gedruckt (Portal.py, seit Rev. 19, aus der 3MF ausgemessen): aussen
# 18 x 14, Biegeradius 20 mm (Schleife am gedruckten Teil gemessen, seit
# Rev. 22), die Endstuecke je 36 mm hinter dem Gelenk. Beide Ketten liegen
# wie in Portal.py (Y seit Rev. 21: Arbeitsweg plus Reserve nach vorn).
_PM = bauraum.modul_laden(bauraum.PORTAL, 'portal')
KETTE_R = _PM.w('kette_r')
KETTE_ENDEN = 2.0 * _PM.w('endstueck_l')
RESERVE = 0.15                   # Kabel: Boegen, Zugentlastung, Stecker
KAUFLAENGEN = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)   # m

# Leistung: Steckernetzteil GIDEALED 24 V / 3 A. Die Motoren: je 2 Phasen
# x I^2 x R plus Treiber, mit dem Strom, der am Vref-Poti eingestellt wird
# (70 % des Nennstroms), und dem Wicklungswiderstand des Stepperonline
# 17HE15-1504S [v] Etikett: 1,5 A, 2,3 Ohm [w]. Laser: LASER TREE 4 W,
# 12 V 1,6 A (1,4-1,8 A) [v] Angabe, ueber den Abwaertswandler 12 V / 5 A
# [v] Angabe.
NETZTEIL_W = 72.0
DAUERLAST = 0.85                 # dauernd nicht mehr als 85 % ziehen
MOTOR_NENN, MOTOR_ANTEIL = 1.5, 0.7    # A je Phase [w]; davon eingestellt
MOTOREN, MOTOR_R, TREIBER_W = 4, 2.3, 0.6
MOTOR_I = MOTOR_NENN * MOTOR_ANTEIL    # Effektivstrom je Phase
# TMC2209 standalone, Strom ueber das Vref-Poti [w]:
#   I_eff = 0,325 V / (R_sense + 0,02 Ohm) / Wurzel 2 x Vref / 2,5 V
# R_sense haengt vom Modul ab. Auf den GERUI V2.0 steht kein R110 (Angabe
# 2026-09-27), deshalb die ueblichen Werte; der kleinste ist der sichere.
R_SENSE = (0.10, 0.11, 0.15)     # Ohm
LUEFTER_W = 2.0
LASER_V, LASER_A = 12.0, 1.8     # obere Grenze der Angabe
WANDLER_A = 5.0                  # Abwaertswandler 24 -> 12 V, 5 A [v]
WANDLER_ETA = 0.9                # sein Wirkungsgrad [w]
# 5 V: Der Pi (docs/pi.md) haengt mit seinem Abwaertswandler 24 -> 5 V vor
# Schalter und Not-Aus an der Buchse und versorgt ueber USB den Uno, der
# Uno ueber seinen 5-V-Stift die Lichtschranken [w].
USB_MA = 500.0          # Polyfuse am USB-Eingang des Uno
LS_MA = 25.0            # je Lichtschranke: IR-Diode, Komparator, zwei LEDs
UNO_MA = 60.0           # Uno mit USB-Wandler
TREIBER_LOGIK_MA = 5.0  # je TMC2209, VIO
PI_MA = 600.0           # Pi Zero 2 W unter Last, mit WLAN [w]
PI_WANDLER_A = 3.0      # Abwaertswandler 24 -> 5 V: mindestens so viel
PI_WANDLER_ETA = 0.85   # sein Wirkungsgrad [w]
# Fertige USB-Kabel (W17, W19): Querschnitt der Stromadern; billige Kabel
# haben nur AWG 28. Unter etwa 4,63 V meldet der Pi Unterspannung [w].
AWG_MM2 = {24: 0.205, 28: 0.081}
PI_UNTERSPANNUNG = 4.63  # V

# Litzen: Kupfer, feindraehtig, in den Ketten hochflexibel. Der Querschnitt
# folgt aus Strom und Laenge und aus dem, was die Kontakte nehmen [w]:
# XH-Crimpkontakt 0,08-0,34 mm2 (AWG 28-22), PH 0,05-0,22 mm2 (AWG 30-24),
# Dupont AWG 28-22, Wago 221 feindraehtig 0,14-4 mm2. Belastbarkeit
# flexibler Leitungen nach VDE 0298-4, Tabelle 11 (2 Adern belastet, 30 C).
RHO_CU = 0.0175                  # Ohm mm2/m
BELASTBAR = {0.5: 3.0, 0.75: 6.0, 1.0: 10.0}    # mm2: A
LITZE_24V = 0.75     # mm2 (AWG 18): Eingang, Schalter, Not-Aus, Wago, Shield
LITZE_LASER = 0.34   # mm2 (AWG 22): mehr nimmt der XH-Kontakt am Laser nicht
LITZE_MOTOR = 0.2    # mm2 (AWG 24): mehr nimmt der PH-Kontakt am Motor nicht
# Signale (Lichtschranken, 24-V-Waechter) 0,25: 0,14 ist das Minimum der
# Wago (AWG 26 hat nur 0,13); in den Dupont-Kontakt passen bis 0,34
LITZE_SIGNAL = 0.25  # mm2 (AWG 24)
XH_MAX, PH_MAX, WAGO_MIN = 0.34, 0.22, 0.14     # mm2

KABEL = '#6d3fb5'
FARBE.update({'kette': ('#a3abb8', '#3d4552')})


def konzept(w, L, tw, TL, ew, EL):
    """Lage aller Teile, Rahmenkoordinaten wie portal_check.py Abschnitt 14
    (Portal in der Mitte seines Wegs). ew, EL: Masse und Lagen aus
    Elektronik.py."""
    feste, bewegte, _ = bauraum.bauraeume(tw, TL)
    feste = [q for q in feste if q.name not in portal_check.TOOLHEAD_OHNE]
    d_schiene, d_vorn, d_2060, _ = portal_check.y_weg(w, L, TL, feste,
                                                      bewegte)
    # Hinten begrenzt seit Portal Rev. 14 die Schiene: das hintere 2060
    # liegt weiter hinten, als der Wagen kommt.
    d_hinten = min(d_2060, d_schiene)
    portal = {q.name: q for q in bauraum.portal_bauraeume(w, L)[0]}
    R = L['R']
    K = {'feste': feste, 'bewegte': bewegte, 'portal': portal,
         'd_schiene': d_schiene, 'd_vorn': d_vorn, 'd_hinten': d_hinten,
         # Toolhead mit Z unten an der hinteren Grenze: Luft zum 2060
         'luft_2060': d_2060 - d_hinten + 3.0}
    K['grenze_hinten'] = ('am hinteren Schienenende' if d_schiene < d_2060
                          else '3 mm vor dem hinteren 2060')
    fach = portal_check.elektronikfach(w, L)
    K['fach'] = fach
    # engste Stelle zwischen Fach und allem, was faehrt (wie portal_check
    # Abschnitt 16): (Luft, Fach, Teil, Portalstellung)
    K['fach_engste'] = portal_check.luft_hinten(w, L, TL, feste, bewegte,
                                                [fach])[0]
    # hoehere Zone in der Mitte: ab vor der Traegerplatte am hinteren
    # Schienenende — seit Portal Rev. 14 liegt die vor dem 2060, die Zone
    # beginnt dann am Fach
    K['y_tr'] = min(TL['traeger_y0'] - d_schiene - w('luft_bau'), fach.y[1])

    # Gehaeuse aus Elektronik.py
    K['EL'] = EL
    K['steuerung'] = Quader('Gehaeuse', *EL['geh_x'], *EL['geh_y'],
                            *EL['geh_z'])
    K['platte'] = Quader('Montageplatte', *EL['platte_x'], *EL['platte_y'],
                         *EL['platte_z'])
    K['deckel'] = Quader('Deckel', *EL['deckel_x'], *EL['geh_y'],
                         *EL['haube_z'])
    fm, h = EL['luefter_mitte'], ew('luefter') / 2.0
    K['luefter'] = Quader('Luefter', fm[0] - h, fm[0] + h, fm[1] - h,
                          fm[1] + h, *EL['luefter_z'])
    K['uno'] = Quader('Uno', *EL['uno_x'], *EL['uno_y'], EL['uno_z0'],
                      EL['stapel_z1'])
    K['eingang'] = Quader('Eingang', EL['buchse_x'] - 6.0,
                          EL['schalter_x'] + 11.0, EL['innen_y'][0],
                          EL['innen_y'][0] + ew('eingang_tiefe'),
                          EL['boden_z'], EL['boden_z'] + 25.0)
    K['verteiler'] = Quader('Verteiler', *EL['wago_x'], EL['wandler_y'][0],
                            EL['wago_y'][1], EL['boden_z'],
                            EL['boden_z'] + 25.0)
    K['leistung'] = leistung()

    # Aussenseiten der 2040 und ihre untere Nut
    K['x_aussen'] = R + w('rahmen_b') / 2.0 + 5.0
    K['z_nut_u'] = L['rahmen_z0'] + w('rahmen_b') / 2.0

    # Y-Kette (Portal.py, Rev. 21): aussen am linken 2040, neben der Platte
    # des linken Schlittens; Schleife nach vorn. Der Festpunkt (Endstueck
    # 180) sitzt hinten in der Wanne Y, die auf drei Traegern an der
    # unteren Seitennut haengt; das bewegte Ende auf dem Kettenhalter Y.
    # Die Litzen gehen hinten in das Endstueck 180 und kommen hinten aus
    # dem Anfangsstueck.
    K['ky_x'] = L['yk_x']
    K['ky_hub'] = L['y_weg_hinten'] + w('y_weg_vorn')
    K['ky_fest'] = L['yk_fest']
    K['ky_eintritt'] = L['yk_fest'] - w('endstueck_l')
    K['ky_austritt'] = w('yk_gelenk_y') - w('endstueck_l')  # Portal Mitte
    K['ky_wanne'] = L['ywanne_y']
    K['ky_z_unten'] = L['yk_achse_unten']
    K['ky_z_oben'] = L['yk_achse_oben']
    K['ky_glieder'] = L['yk_glieder']
    K['ky_laenge'] = L['yk_laenge'] + KETTE_ENDEN

    # X-Kette (Portal.py, Rev. 19): direkt hinter der Traegerplatte, die
    # Wanne ueber dem Riemen. Festpunkt (Gelenk des Endstuecks 180) in der
    # Mitte des Wegs des bewegten Gelenks, Schleife nach rechts (links
    # stuende der X-Motor im Weg); das bewegte Ende auf dem Kettenhalter.
    # Die Litzen gehen am Ende des Endstuecks 180 hinein.
    K['kx_y'] = L['xk_y']
    K['kx_hub'] = L['xk_hub']
    K['kx_fest'] = L['xk_fest']
    K['kx_eintritt'] = L['xk_fest'] - _PM.w('endstueck_l')
    K['kx_wanne'] = L['wanne_x']
    K['kx_wanne_y'] = L['wanne_y']
    K['kx_bogen'] = _PM.xk_bogen(L, L['xw_mitte'])
    K['kx_z_wanne'] = L['wanne_z'][0]
    K['kx_z_unten'] = L['xk_achse_unten']
    K['kx_z_oben'] = L['xk_achse_oben']
    K['kx_glieder'] = L['xk_glieder']
    K['kx_laenge'] = L['xk_laenge'] + KETTE_ENDEN

    # Endschalter (Gabellichtschranken LM393, seit Rev. 15 in Portal.py): Y
    # aussen am rechten 2040 hinter dem hinteren 2060 (links laeuft die
    # Y-Kette), X vor dem linken Ende der 2020; jeweils der Strahl.
    K['es_y'] = (L['gy_x'], L['ly_strahl_y'])
    K['es_x'] = (L['lx_strahl_x'], L['lx_strahl_y_rel'])
    xm = L['xw_mitte']                  # Toolhead in der Mitte des X-Wegs
    K['es_z'] = (xm - 27.0, 32.0)
    K['xm'] = xm
    # Y-Motoren am Y-Motorhalter (seit Rev. 16 in Portal.py): mittig zur
    # 2040, die Achse in der Mitte des Spannwegs
    YL = L['ymh']
    ys, zs = L['rahmen_y'][1], L['rahmen_z0']
    K['ym_y'] = ys + YL['motor_y_mitte']
    K['ym_z'] = (zs + YL['motor_z0'], zs + YL['platte_z0'])
    # Not-Aus-Gehaeuse vorn am vorderen 2060 (NotAus.py); das Kabel kommt
    # von rechts in der oberen Nut vorn am 2060
    NA = bauraum.modul_laden(NOTAUS, 'notaus').lage()
    K['notaus'] = Quader('Not-Aus', NA['lasche_x'][0][0],
                         NA['lasche_x'][1][1], *NA['geh_y'], *NA['geh_z'])
    K['notaus_kabel'] = (NA['geh_x'][1], NA['kabel'][0], NA['kabel'][1])
    K['notaus_nut_z'] = NA['nuten_z'][0]
    # Pi-Halter (PiHalter.py): rechts neben der Montageplatte an der
    # Rueckseite des hinteren 2060; Pi und 5-V-Wandler ueber dem 2060
    PH = bauraum.modul_laden(PIHALTER, 'pihalter').lage()
    K['PH'] = PH
    K['pihalter'] = Quader('Pi-Halter', *PH['x'], *PH['platte_y'],
                           *PH['z'])
    K['pi'] = Quader('Pi', *PH['pi_x'], PH['bauteile_y'][0],
                     PH['pcb_y'][1], *PH['pi_z'])
    K['wandler5'] = Quader('5-V-Wandler', *PH['wandler_x'],
                           *PH['wandler_y'], *PH['wandler_z'])
    K['pihaube'] = Quader('Pi-Haube', *PH['haube_x'], *PH['haube_y'],
                          *PH['haube_z'])
    K['kabel'] = kabelwege(w, L, TL, K)
    return K


def fuenf_volt_ma():
    """Strom aus dem 5-V-Wandler des Pi in mA: der Pi selbst und ueber USB
    der Uno mit Treiberlogik und den drei Lichtschranken."""
    return PI_MA + UNO_MA + 4 * TREIBER_LOGIK_MA + 3 * LS_MA


def leistung():
    """Leistungsbilanz am 24-V-Netzteil in W: Motoren, Luefter, der Laser
    samt Wandlerverlust und der Pi mit Uno und Lichtschranken ueber den
    5-V-Wandler, gegen das, was das Netzteil dauernd liefert."""
    motoren = MOTOREN * (2.0 * MOTOR_I ** 2 * MOTOR_R + TREIBER_W)
    laser = LASER_V * LASER_A / WANDLER_ETA
    pi = fuenf_volt_ma() / 1000.0 * 5.0 / PI_WANDLER_ETA
    dauer = NETZTEIL_W * DAUERLAST
    summe = motoren + LUEFTER_W + laser + pi
    return {'motoren': motoren, 'luefter': LUEFTER_W, 'laser': laser,
            'pi': pi, 'summe': summe, 'dauer': dauer,
            'reserve': dauer - summe, 'strom': summe / 24.0}


def vref(i_eff, r_sense):
    """Vref am Poti eines TMC2209 (standalone) fuer den Effektivstrom
    i_eff in A bei Messwiderstaenden r_sense in Ohm."""
    return i_eff * (r_sense + 0.02) * math.sqrt(2.0) * 2.5 / 0.325


def spannungsfall(mm2, laenge_m, strom):
    """Spannungsfall in V an einer Leitung aus Hin- und Rueckleiter, je
    laenge_m lang, Kupfer mit mm2 Querschnitt (strom = 1: Widerstand)."""
    return RHO_CU * 2.0 * laenge_m / mm2 * strom


def litzen(K):
    """Folgen der Querschnitte an den laengsten Wegen (Kauflaengen):
    Spannungsfall am Laser, Widerstand im Z-Motorkabel, Not-Aus bei vollem
    Netzteilstrom — dessen Kabel laeuft zum Gehaeuse vorn am vorderen 2060
    und zurueck. Dazu der Zweig zum Pi: W18 mit 24 V, W19 mit 5 V fuer
    alles am Pi, W17 mit dem Strom des Uno (AWG 24 und das duenne AWG 28)."""
    kab = K['kabel']
    netz_a = NETZTEIL_W / 24.0
    m_laser = kauflaenge(kab['Laser (12 V + PWM)'][0])
    m_motor = kauflaenge(kab['Z-Motor'][0])
    m_not = kauflaenge(kab['Not-Aus'][0])
    m_pi24 = kauflaenge(kab['Pi 24 V'][0])
    m_pi5 = kauflaenge(kab['Pi 5 V'][0])
    m_usb = kauflaenge(kab['USB Pi–Uno'][0])
    pi24_a = leistung()['pi'] / 24.0
    pi5_a = fuenf_volt_ma() / 1000.0
    usb_a = (UNO_MA + 4 * TREIBER_LOGIK_MA + 3 * LS_MA) / 1000.0
    return {'netz_a': netz_a,
            'laser_m': m_laser,
            'laser_u': spannungsfall(LITZE_LASER, m_laser, LASER_A),
            'motor_m': m_motor,
            'motor_r': spannungsfall(LITZE_MOTOR, m_motor, 1.0),
            'not_m': m_not,
            'not_u': spannungsfall(LITZE_24V, m_not, netz_a),
            'pi24_m': m_pi24, 'pi24_a': pi24_a,
            'pi24_u': spannungsfall(LITZE_24V, m_pi24, pi24_a),
            'pi5_m': m_pi5, 'pi5_a': pi5_a,
            'pi5_u': {awg: spannungsfall(mm2, m_pi5, pi5_a)
                      for awg, mm2 in AWG_MM2.items()},
            'usb_m': m_usb, 'usb_a': usb_a,
            'usb_u': {awg: spannungsfall(mm2, m_usb, usb_a)
                      for awg, mm2 in AWG_MM2.items()}}


def laenge(punkte):
    return sum(math.dist(a, b) for a, b in zip(punkte, punkte[1:]))


def kabelwege(w, L, TL, K):
    """Kabelwege als 3D-Streckenzuege (Portal in der Mitte). Die Ketten
    zaehlen mit ihrer Laenge. Liefert {Name: (Laenge mm, Streckenzug
    in XY fuer die Draufsicht)}."""
    R, st, EL = L['R'], K['steuerung'], K['EL']
    xa, zn = K['x_aussen'], K['z_nut_u']
    # links aus dem Kabelausschnitt, unter dem linken 2040 durch nach aussen
    yc = EL['kabel_links_y']
    z_k = EL['kabel_z0'] + 8.0
    raus = [(st.x[0], yc, z_k), (-xa, yc, z_k), (-xa, yc, zn)]
    zm = sum(K['ym_z']) / 2.0
    fl = w('motor_flansch') / 2.0
    # vorn verlaesst das Kabel die untere Nut zwischen dem 2060 und den
    # Schenkeln des Y-Motorhalters
    y_vor = L['quer_y_vorn'][1] + 2.0
    # links geht die Litze an jedem Traeger der Wanne Y kurz aus der Nut,
    # unter seiner Wand durch (Portal.py, seit Rev. 22)
    z_unter = L['ytr_wand_z'][0] - 2.5
    umweg = []
    for y0, y1 in sorted(L['ytr_y'].values()):
        umweg += [(-xa, y0 - 8.0, zn), (-xa, y0, z_unter),
                  (-xa, y1, z_unter), (-xa, y1 + 8.0, zn)]

    def y_motor(s):
        return (umweg if s < 0 else []) + [
            (s * xa, y_vor, zn), (s * (R + fl + 3.0), K['ym_y'], zm)]

    # vorn aus dem Kabelausschnitt in den Kanal, darin nach rechts, dann an
    # der Rueckseite des 2060 (mittlere Nut) zum rechten 2040
    xv = EL['kabel_vorn_x']
    y_kanal = (st.y[1] + EL['platte_y'][0]) / 2.0
    y_2060 = L['quer_y_hinten'][0] - 1.0
    z_2060 = L['quer_z'][0] + 30.0
    x_ende = EL['platte_x'][1] + 5.0
    rechts = [(xv, st.y[1], z_k), (xv, y_kanal, z_k), (x_ende, y_kanal, z_k),
              (x_ende, y_2060, z_2060), (xa, y_2060, z_2060),
              (xa, y_2060, zn)]
    # zur Y-Kette: in der Seitennut nach vorn bis hinter die Wanne Y, dort
    # aus der Nut nach aussen und hinten in das Endstueck 180
    xk = sum(K['ky_x']) / 2.0
    y_wanne = K['ky_wanne'][0] - 5.0
    zur_kette = raus + [(-xa, y_wanne, zn), (xk, y_wanne, K['ky_z_unten']),
                        (xk, K['ky_eintritt'], K['ky_z_unten'])]
    # bewegtes Ende (Portal in der Mitte): hinten aus dem Anfangsstueck, ein
    # Kabelbinder am Kettenhalter Y
    aus_y = (xk, K['ky_austritt'], K['ky_z_oben'])
    binder = (xk, L['khy_binder'][0][1], L['khy_z'][1] + 2.0)
    # zur X-Kette (seit Rev. 21): auf der Platte hinter Rueckwand und
    # Motorhalter nach innen, rechts neben ihnen in die obere Nut des
    # Rohrs, darin bis an den Kabelfluegel, vor ihm hoch und oben ueber
    # den Riemen nach vorn in das Endstueck 180
    zp = L['platte_z1'] + 3.0
    x0, x1 = L['kf_nut_x']
    yn = (L['profil_y0'] + L['portal_y']) / 2.0
    zr = L['profil_z1'] - 3.0
    xb, yb = sum(L['kf_buendel_x']) / 2.0, sum(L['kf_buendel_y']) / 2.0
    zq = sum(L['kf_quer_z']) / 2.0
    yk = sum(K['kx_y']) / 2.0
    zur_x = [aus_y, binder, (x0, binder[1], zp),
             (x0, L['profil_y0'] - 3.0, zp), (x0, yn, zr), (x1, yn, zr),
             (xb, yb, L['profil_z1']), (xb, yb, zq), (xb, yk, zq),
             (K['kx_eintritt'], yk, K['kx_z_unten'])]
    K['weg_portal'] = zur_x
    # X-Motor: hinter dem Motorhalter hoch, seine Litze kommt seitlich aus
    # dem Motor (links angenommen); X-Endschalter ueber das Rohr nach vorn
    motor = K['portal']['X-Motor']
    yh = L['stirn_y'][0] - 3.0
    x_motor = [aus_y, binder, (motor.x[0] - 3.0, yh, zp),
               (motor.x[0] - 3.0, yh, 65.0), (motor.x[0], -16.4, 65.0)]
    x_es = [aus_y, binder, (x0, binder[1], zp), (x0, yh, zp),
            (x0, yn, L['profil_z1'] + 3.0),
            (K['es_x'][0], K['es_x'][1], 20.0)]
    xm = K['xm']
    am_th = [(xm, yk, K['kx_z_oben']), (xm, 0.0, K['kx_z_oben'])]
    z_motor = am_th + [(xm, 0.0, 183.0), (xm + 30.0, 7.4, 183.0)]
    laser_oben = 23.8 + TL['zc_min']                  # Z ganz unten
    laser = am_th + [(xm, 0.0, laser_oben), (xm, 41.0, laser_oben)]
    z_es = am_th + [(xm - 20.0, 16.0, 112.0)]
    ky, kx = K['ky_laenge'], K['kx_laenge']
    na_x, na_y, na_z = K['notaus_kabel']
    z_nut = K['notaus_nut_z']
    notaus = rechts + [(xa, y_vor, zn), (xa, y_vor, z_nut),
                       (na_x + 3.0, y_vor, z_nut), (na_x + 3.0, na_y, na_z),
                       (na_x, na_y, na_z)]
    # Pi (PiHalter.py). 24 V: an den Loetfahnen der Buchse, im Kasten nach
    # vorn, durch den Kanal nach rechts, an der Flaeche des 2060 unter dem
    # Halter durch, von unten in die Haube und zwischen ihrer linken Wand
    # und dem Wandler, hinter dem Kopf der M5, hoch zu seinem Eingang
    PH = K['PH']
    zw = sum(PH['wandler_z']) / 2.0
    yw = sum(PH['wandler_y']) / 2.0
    xw = (PH['haube_innen'][0][0] + PH['wandler_x'][0]) / 2.0
    y_hinter = PH['kopf_y'][0] - 3.0
    pi24 = [(EL['buchse_x'], EL['innen_y'][0] + 6.0, EL['eingang_z']),
            rechts[0], rechts[1], rechts[2], rechts[3],
            (xw, y_2060, z_2060), (xw, y_hinter, z_2060), (xw, y_hinter, zw),
            (PH['wandler_x'][0], yw, zw)]
    # 5 V: aus dem USB-A-Stecker rechts im Wandler (zeigt zum Pi) nach
    # unten und von unten in PWR
    ps, sa = PH['stecker']['PWR'], PH['stecker_a']
    sx, sy = sum(ps[0]) / 2.0, sum(ps[1]) / 2.0
    ya, za = sum(sa[1]) / 2.0, sum(sa[2]) / 2.0
    pi5 = [(sa[0][1], ya, za), (sa[0][1] + 5.0, ya, za - 5.0),
           (sa[0][1] + 5.0, ya, ps[2][0] - 8.0),
           (sx, sy, ps[2][0] - 8.0), (sx, sy, ps[2][0])]
    # USB: aus dem Stecker in "USB" nach unten und hinten, nach links bis
    # neben den Kasten, an seiner rechten Wand nach hinten, hinter ihm nach
    # links und von hinten in die USB-B-Buchse des Uno (Mitte 38,1 mm von
    # der Kante unter der Hohlbuchse [w]); der Stecker steht 30 mm ueber
    us = PH['stecker']['USB']
    ux, uy = sum(us[0]) / 2.0, sum(us[1]) / 2.0
    y_usb = PH['wandler_y'][0] - 5.0
    z_usb = us[2][0] - 7.0
    x_b = EL['uno_x'][0] + 38.1
    z_b = EL['uno_z1'] + 5.5
    y_b = st.y[0] - 30.0
    usb = [(ux, uy, us[2][0]), (ux, y_usb, z_usb), (st.x[1] + 5.0, y_usb,
                                                    z_usb),
           (st.x[1] + 5.0, y_b, z_usb), (x_b, y_b, z_b), (x_b, st.y[0], z_b)]
    wege = {
        'Not-Aus': (laenge(notaus), notaus),
        'Y-Motor links': (laenge(raus + y_motor(-1)), raus + y_motor(-1)),
        'Y-Motor rechts': (laenge(rechts + y_motor(1)), rechts + y_motor(1)),
        'Y-Endschalter': (laenge(rechts + [(xa, K['es_y'][1], zn)]),
                          rechts + [(xa, K['es_y'][1], zn)]),
        'X-Motor': (laenge(zur_kette) + ky + laenge(x_motor), zur_kette),
        'X-Endschalter': (laenge(zur_kette) + ky + laenge(x_es), None),
        'Z-Motor': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                    + laenge(z_motor), None),
        'Laser (12 V + PWM)': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                               + laenge(laser), None),
        'Z-Endschalter': (laenge(zur_kette) + ky + laenge(zur_x) + kx
                          + laenge(z_es), None),
        'Pi 24 V': (laenge(pi24), pi24),
        'Pi 5 V': (laenge(pi5), pi5),
        'USB Pi–Uno': (laenge(usb), usb),
    }
    return wege


def kauflaenge(mm):
    m = mm * (1.0 + RESERVE) / 1000.0
    return next((k for k in KAUFLAENGEN if k >= m - 1e-9), KAUFLAENGEN[-1])


def linienzug(f, punkte, farbe=KABEL, breite=1.6, strich='5 3'):
    return el('polyline', {
        'points': ' '.join('{},{}'.format(*map(f1, f.px(a, b)))
                           for a, b in punkte),
        'fill': 'none', 'stroke': farbe, 'stroke-width': breite,
        'stroke-dasharray': strich, 'stroke-linejoin': 'round'})


def punkt(f, a, b, farbe=ROT, r=4.5):
    x, y = f.px(a, b)
    return el('circle', {'cx': f1(x), 'cy': f1(y), 'r': f1(r),
                         'fill': farbe, 'stroke': '#ffffff',
                         'stroke-width': '1.2'})


def fach_rect(f, a0, a1, b0, b1):
    (xa, ya), (xb, yb) = f.px(a0, b0), f.px(a1, b1)
    return el('rect', {'x': f1(min(xa, xb)), 'y': f1(min(ya, yb)),
                       'width': f1(abs(xb - xa)), 'height': f1(abs(yb - ya)),
                       'fill': 'url(#schraffur)', 'stroke': ORANGE,
                       'stroke-width': '1.3'})


# ---- Draufsicht auf die ganze Maschine ------------------------------------
def draufsicht(f, w, L, K):
    R = L['R']
    P = K['portal']
    t = []
    for y in (L['quer_y_vorn'], L['quer_y_hinten']):
        t.append(f.rect(L['quer_x'][0], L['quer_x'][1], y[0], y[1],
                        'profil'))
    for s in (-1, 1):
        t.append(f.rect(s * (R - w('rahmen_b') / 2), s * (R + w('rahmen_b')
                                                           / 2),
                        *L['rahmen_y'], 'profil'))
        t.append(f.rect(s * (R - 6.0), s * (R + 6.0), *L['y_schiene_y'],
                        'fuehrung'))
    fach = K['fach']
    t.append(fach_rect(f, fach.x[0], fach.x[1], fach.y[0], fach.y[1]))
    # Arbeitsflaeche: so weit reicht der Strahl mit Z unten
    sy = K['strahl_y']
    t.append(f.rect(L['xw_min'], L['xw_max'], sy - K['d_hinten'],
                    sy + K['d_vorn'], 'toolhead', fill_opacity='0.18',
                    stroke_dasharray='6 4'))
    # Portal in der Mitte
    for n in ('Platte links', 'Platte rechts', 'Portalrohr', 'X-Schiene',
              'Stirnblock links', 'Stirnblock rechts', 'Spannbock Boden',
              'Motorhalter Saeule hinten'):
        q = P[n]
        art = 'profil' if n == 'Portalrohr' else (
            'fuehrung' if 'Schiene' in n else 'druck')
        t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art))
    q = P['X-Motor']
    t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], 'kauf'))
    xm = K['xm']
    for q in K['feste'] + K['bewegte']:
        t.append(f.rect(q.x[0] + xm, q.x[1] + xm, q.y[0], q.y[1], 'toolhead',
                        fill_opacity='0.55'))
    # Portal an der hinteren Grenze (Softlimit)
    dh = K['d_hinten']
    for n in ('Portalrohr', 'Platte links', 'Platte rechts'):
        q = P[n]
        t.append(f.rect(q.x[0], q.x[1], q.y[0] - dh, q.y[1] - dh, 'druck',
                        fill='none', stroke_dasharray='4 3'))
    # Y-Motoren vorn (Portal.py), Not-Aus-Gehaeuse (NotAus.py)
    fl = w('motor_flansch') / 2.0
    for s in (-1, 1):
        x = s * R
        t.append(f.rect(x - fl, x + fl, K['ym_y'] - fl, K['ym_y'] + fl,
                        'kauf'))
    q = K['notaus']
    t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], 'neu'))
    # Energieketten: Traeger, Wanne und Kettenhalter, die Huelle der Kette
    # mit dem Portal in der Mitte (Y: vom Festpunkt bis vorn an den Bogen)
    for y in L['ytr_y'].values():
        t.append(f.rect(L['ytr_arm_x'][0], L['ytr_wand_x'][1], *y, 'neu'))
    t.append(f.rect(*L['ywanne_x'], *K['ky_wanne'], 'neu',
                    fill_opacity='0.6'))
    t.append(f.rect(*L['khy_x'], *L['khy_y'], 'neu'))
    _, yb = schleife_y(L, w, 0.0)
    t.append(f.rect(K['ky_x'][0], K['ky_x'][1], K['ky_eintritt'],
                    yb + L['xk_bogen_r'][1], 'kette'))
    t.append(f.rect(K['kx_wanne'][0], K['kx_wanne'][1], *K['kx_wanne_y'],
                    'neu', fill_opacity='0.6'))
    # Toolhead in der Mitte: das bewegte Ende steht ueber dem Festpunkt
    t.append(f.rect(K['kx_eintritt'], K['kx_bogen'] + L['xk_bogen_r'][1],
                    *K['kx_y'], 'kette'))
    # Gehaeuse (Elektronik.py) mit Platte; darin Uno, Eingang, Verteiler;
    # obenauf der Luefter
    for n, art, mehr in (('platte', 'neu', {}), ('steuerung', 'neu', {}),
                         ('uno', 'druck', {'fill_opacity': '0.7'}),
                         ('eingang', 'kauf', {'stroke_dasharray': '4 3'}),
                         ('verteiler', 'kauf', {'stroke_dasharray': '4 3'}),
                         ('luefter', 'kauf', {'fill_opacity': '0.85'})):
        q = K[n]
        t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art, **mehr))
    # Pi-Halter (PiHalter.py) rechts neben dem Kasten, dahinter Wandler und
    # Pi unter der Haube (gestrichelt)
    for n, art, mehr in (('pihalter', 'neu', {}),
                         ('wandler5', 'kauf', {'stroke_dasharray': '4 3'}),
                         ('pi', 'kauf', {}),
                         ('pihaube', 'neu', {'fill': 'none',
                                             'stroke_dasharray': '6 3'})):
        q = K[n]
        t.append(f.rect(q.x[0], q.x[1], q.y[0], q.y[1], art, **mehr))
    # feste Kabelwege, dazu der Weg mit dem Portal von der Y- zur X-Kette
    for n in ('Y-Motor links', 'Y-Motor rechts', 'Y-Endschalter', 'X-Motor',
              'Not-Aus', 'Pi 24 V', 'USB Pi–Uno'):
        weg = K['kabel'][n][1]
        t.append(linienzug(f, [(p[0], p[1]) for p in weg]))
    t.append(linienzug(f, [(p[0], p[1]) for p in K['weg_portal'][1:]]))
    # Endschalter
    for a, b in (K['es_x'], K['es_y'], K['es_z']):
        t.append(punkt(f, a, b))
    return t


# ---- Seitenansicht von links ----------------------------------------------
def seitenansicht(f, w, L, TL, K):
    P = K['portal']
    t = []
    fach = K['fach']
    zt = L['quer_z'][0]
    t.append(f.rect(f.a[0] - 5, f.a[1] + 5, zt - 12.0, zt, 'profil',
                    fill='#f1efe9', stroke='none'))
    t.append(f.linie(f.a[0], zt, f.a[1], zt, GRAU, 1.0))
    t.append(f.rect(L['rahmen_y'][0], L['rahmen_y'][1], L['rahmen_z0'],
                    L['rahmen_z1'], 'profil'))
    t.append(f.rect(L['y_schiene_y'][0], L['y_schiene_y'][1],
                    L['rahmen_z1'], L['rahmen_z1'] + 8.0, 'fuehrung'))
    for y in (L['quer_y_vorn'], L['quer_y_hinten']):
        t.append(f.rect(y[0], y[1], *L['quer_z'], 'profil'))
    fl = w('motor_flansch') / 2.0
    t.append(f.rect(K['ym_y'] - fl, K['ym_y'] + fl, *K['ym_z'], 'kauf'))
    # Fach und die hoehere Zone in der Mitte
    t.append(fach_rect(f, fach.y[0], fach.y[1], fach.z[0], fach.z[1]))
    t.append(f.rect(fach.y[0], K['y_tr'], fach.z[1], K['z_frei'] - 0.0,
                    'neu', fill='none', stroke_dasharray='3 3'))
    for n, art, mehr in (('platte', 'neu', {}), ('steuerung', 'neu', {}),
                         ('deckel', 'neu', {}),
                         ('uno', 'druck', {'fill_opacity': '0.7'}),
                         ('luefter', 'kauf', {}),
                         ('wandler5', 'kauf', {'stroke_dasharray': '4 3'}),
                         ('pi', 'kauf', {}), ('pihalter', 'neu', {}),
                         ('pihaube', 'neu', {'fill': 'none',
                                             'stroke_dasharray': '6 3'})):
        q = K[n]
        t.append(f.rect(q.y[0], q.y[1], q.z[0], q.z[1], art, **mehr))
    # Portal an der hinteren Grenze, Z unten
    dh = -K['d_hinten']
    for n in ('Platte links', 'Portalrohr', 'Y-Wagen links',
              'Klemmturm hinten links', 'Klemmturm hinten links oben',
              'Klemmturm vorn links', 'Klemmturm vorn links oben',
              'Stirnblock links'):
        q = P[n]
        art = 'profil' if n == 'Portalrohr' else (
            'fuehrung' if 'Wagen' in n else 'druck')
        t.append(f.rect(q.y[0] + dh, q.y[1] + dh, q.z[0], q.z[1], art))
    for q in K['feste'] + [b.verschoben(TL['zc_min']) for b in K['bewegte']]:
        t.append(f.rect(q.y[0] + dh, q.y[1] + dh, q.z[0], q.z[1], 'toolhead',
                        fill_opacity='0.55'))
    # Traegerplatte am hinteren Schienenende, Z oben
    ds = -K['d_schiene']
    for q in K['feste']:
        if q.name in ('Traegerplatte Hauptsaeule', 'X-Wagen MGN15H'):
            t.append(f.rect(q.y[0] + ds, q.y[1] + ds, q.z[0], q.z[1],
                            'toolhead', fill='none', stroke_dasharray='4 3',
                            stroke_width='1.1'))
    q = P['Portalrohr']
    t.append(f.rect(q.y[0] + ds, q.y[1] + ds, q.z[0], q.z[1], 'profil',
                    fill='none', stroke_dasharray='4 3'))
    # Y-Kette (davor): Traeger, Wanne; die Kette mit dem Portal an der
    # hinteren Grenze, der Untertrum dann fast ganz im Obertrum
    for y in L['ytr_y'].values():
        t.append(f.rect(*y, *L['ytr_wand_z'], 'neu'))
    t.append(f.rect(*K['ky_wanne'], *L['ywanne_z'], 'neu',
                    fill_opacity='0.6'))
    umr, _ = schleife_y(L, w, dh)
    t.append(f.poly(umr, 'kette', fill_opacity='0.8'))
    q = P['Kettenhalter Y']
    t.append(f.rect(q.y[0] + dh, q.y[1] + dh, q.z[0], q.z[1], 'neu'))
    return t


def main():
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    em = bauraum.modul_laden(ELEKTRONIK, 'elektronik')
    hm = bauraum.modul_laden(PIHALTER, 'pihalter')
    K = konzept(w, L, tw, TL, em.w, em.lage())
    K['strahl_y'] = TL['strahl_y']
    K['z_frei'] = -16.0 - w('luft_bau')         # unter dem X-Wagen
    fach = K['fach']
    R = L['R']
    t = [el('defs', {}, '<pattern id="schraffur" width="7" height="7" '
            'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="7" height="7" fill="#fbeee2"/>'
            '<line x1="0" y1="0" x2="0" y2="7" stroke="#e8a871" '
            'stroke-width="1.4"/></pattern>'),
         text(24, 30, 'Platz für die Elektronik (Elektronik.py Rev. {}, '
              'PiHalter.py Rev. {}, Portal.py Rev. {}, ToolheadZ.py Rev. {})'
              .format(em.REVISION, hm.REVISION, pm.REVISION, th.REVISION),
              14, TEXT, fett=True),
         text(24, 48, 'Maßstäblich, alle Maße aus den Skripten. Ketten '
              'gedruckt, beide mit Wanne, Festpunkt und Kettenhalter wie in '
              'Portal.py. Das Netzteil (24 V / 3 A) steht außerhalb.',
              9, GRAU)]

    # ---- Draufsicht --------------------------------------------------------
    s1 = 0.86
    fa = Feld(262, 92, (-338.0, 338.0), (-392.0, 305.0), s1, b_runter=True)
    t += fa.ausschnitt('drauf', draufsicht(fa, w, L, K))
    t += fa.rahmen('Draufsicht (vorn unten)')
    eg = K['eingang']
    xm = K['xm']
    t += fa.spalte([
        (-R, L['rahmen_y'][0] + 20.0, 'linkes 2040 (600 mm)'),
        (-150.0, L['quer_y_hinten'][0] + 8.0, 'hinteres 2060'),
        (-150.0, L['quer_y_vorn'][0] + 8.0, 'vorderes 2060'),
        (L['xw_min'] + 15.0, K['strahl_y'] + K['d_vorn'] - 12.0,
         'Arbeitsfläche: Strahl mit\nZ unten ({} × {} mm)'.format(
             de(L['xw_max'] - L['xw_min'], 0),
             de(K['d_vorn'] + K['d_hinten'], 0))),
        (-R, K['ym_y'], 'Y-Motor links'),
        (sum(K['ky_x']) / 2, K['ky_fest'] + 30.0,
         'Energiekette Y außen am\nlinken 2040, Schleife vorn'),
        (L['ywanne_x'][0], K['ky_wanne'][0] + 4.0,
         'Wanne Y auf drei Trägern\n(untere Seitennut), Festpunkt'),
        (K['es_x'][0], K['es_x'][1], 'X-Endschalter auf der 2020\n'
         '(fährt mit dem Portal)'),
        (-200.0, K['portal']['Portalrohr'].y[0] - K['d_hinten'] + 5.0,
         'Portal an der hinteren\nGrenze (Softlimit Y)')],
        fa.ox - 12, 'end', abstand=24.0)
    t += fa.spalte([
        (K['luefter'].x[1] - 6.0, K['luefter'].y[0] + 6.0,
         'Gehäuse: Uno + CNC Shield\nV3, Lüfter 24 V im Deckel'),
        ((eg.x[0] + eg.x[1]) / 2, eg.y[0] + 4.0,
         '24 V vom Steckernetzteil:\nBuchse und Schalter hinten'),
        (sum(K['verteiler'].x) / 2, K['verteiler'].y[0] + 10.0,
         'Wandler 24 → 12 V und\nWago-Klemmen'),
        (K['platte'].x[1] - 8.0, K['platte'].y[0] + 2.0,
         'Montageplatte: 4 × M5 in die\nRückseite des 2060, Kabelkanal'),
        (K['pi'].x[1] - 6.0, K['pi'].y[0] + 2.0,
         'Pi-Halter: Pi Zero 2 W und\n5-V-Wandler über dem 2060'),
        (K['es_y'][0], K['es_y'][1], 'Y-Endschalter außen am\nrechten 2040 '
         '(links die Kette)'),
        (fach.x[1] - 10.0, fach.y[1] - 10.0,
         'Elektronikfach unter den\n2040, {} × {} × {} mm'.format(
             de(fach.x[1] - fach.x[0], 0), de(fach.y[1] - fach.y[0], 0),
             de(fach.z[1] - fach.z[0], 0))),
        (K['kx_wanne'][1] - 20.0, K['kx_y'][0],
         'Energiekette X: direkt hinter der\nTrägerplatte, über dem Riemen'),
        (xm + 20.0, 40.0, 'Toolhead (Mitte)'),
        (K['es_z'][0], K['es_z'][1], 'Z-Endschalter (vorhanden)'),
        (R, K['ym_y'], 'Y-Motor rechts'),
        (sum(K['notaus'].x) / 2.0, K['notaus'].y[1],
         'Not-Aus vorn am 2060'),
        (R + 10.0, 60.0, 'Kabel Y-Motor rechts\nin der unteren Nut außen')],
        fa.ox + fa.breite + 12, 'start', abstand=24.0)

    # ---- Seitenansicht -----------------------------------------------------
    s2 = 1.45
    fb = Feld(262, fa.oy + fa.hoehe + 70, (-392.0, 20.0), (-146.0, 72.0),
              s2)
    t += fb.ausschnitt('seite', seitenansicht(fb, w, L, TL, K))
    t += fb.rahmen('Seitenansicht von links, hinterer Teil (vorn rechts): '
                   'Portal an der hinteren Grenze, Z unten')
    t += fb.spalte([
        (fach.y[0] + 15.0, fach.z[0] + 12.0, 'Elektronikfach'),
        (-300.0, K['z_frei'] - 6.0,
         'in der Mitte darf es höher\nwerden (gestrichelt)'),
        (K['ky_wanne'][0] + 20.0, L['ywanne_z'][0],
         'Wanne Y und Träger (davor)'),
        (-200.0, K['ky_z_oben'], 'Energiekette Y (davor),\nPortal hinten'),
        (L['quer_y_hinten'][0] + 5.0, L['quer_z'][0] + 10.0,
         'hinteres 2060'),
        (-150.0, L['quer_z'][0], 'Tisch')],
        fb.ox - 12, 'end', abstand=24.0)
    tr = next(q for q in K['feste'] if q.name == 'Traegerplatte Hauptsaeule')
    t += fb.spalte([
        (tr.y[1] - K['d_schiene'], tr.z[0] + 30.0,
         'Trägerplatte am Schienenende\n(nur mit Z oben, gestrichelt)'),
        (K['strahl_y'] - K['d_hinten'], -110.0,
         'Toolhead mit Z unten: {} mm\nvor dem hinteren 2060'.format(
             de(K['luft_2060'], 0))),
        (-60.0, L['rahmen_z1'] - 8.0, '2040 (davor die Kette)'),
        (K['pi'].y[0], K['pi'].z[1] - 4.0,
         'Pi und 5-V-Wandler auf dem\nPi-Halter, über dem 2060'),
        (-211.0, 66.0, 'Toolhead oben abgeschnitten')],
        fb.ox + fb.breite + 12, 'start', abstand=26.0)
    t += fb.mass(fach.y[0] + 12.0, fach.z[0], fach.z[1], '{} mm'.format(
        de(fach.z[1] - fach.z[0], 0)), 4)
    t += quer_mass(fb, fach.y[0], fach.y[1], fach.z[0] + 6.0, '{} mm'.format(
        de(fach.y[1] - fach.y[0], 0)), -4)
    # engste Stelle ueber dem Fach: das Teil in seiner Stellung
    luft, _, teil, dy = K['fach_engste']
    q = K['portal'].get(teil)
    if q is not None and abs(q.z[0] - fach.z[1] - luft) < 0.05:
        ym = (q.y[0] + q.y[1]) / 2.0 + dy
        t += fb.luft(ym, fach.z[1], ym, q.z[0], '{} mm'.format(de(luft, 0)),
                     dx=5, dy=-2)

    # ---- Zahlen ------------------------------------------------------------
    ty = fb.oy + fb.hoehe + 50
    kab = K['kabel']
    zeilen = [
        ('Fach', '{} × {} × {} mm (B × T × H) hinter dem hinteren 2060, '
         'unter den 2040 — dort fährt nichts hin, engste Stelle {} mm '
         '({}'.format(
             de(fach.x[1] - fach.x[0], 0), de(fach.y[1] - fach.y[0], 0),
             de(fach.z[1] - fach.z[0], 0), de(K['fach_engste'][0], 0),
             K['fach_engste'][2].replace('ue', 'ü'))),
        ('', 'darüber, Portal am hinteren Schienenende). Die Tiefe hängt an '
         'der Lage des hinteren 2060 (die 2040 stehen hinten {} mm über, '
         'gemessen).'.format(de(L['quer_y_hinten'][0] - L['rahmen_y'][0],
                                0))),
        ('höher', 'in der Mitte (|X| ≤ 225) ab {} mm hinter dem 2060 frei bis '
         'Z {} — {} mm über der Oberkante der 2040'.format(
             de(L['quer_y_hinten'][0] - K['y_tr'], 0), de(K['z_frei'], 0),
             de(K['z_frei'] - L['rahmen_z1'], 0))),
        ('Netzteil', 'Steckernetzteil 24 V / 3 A ({} W), steht außerhalb; '
         'Motoren ≈ {} W, Lüfter ≈ {} W, Laser über den Wandler ≈ {} W, Pi '
         'mit Uno ≈ {} W — zusammen ≈ {} W, dauernd gehen {} W'.format(
             de(NETZTEIL_W, 0), de(K['leistung']['motoren'], 0),
             de(LUEFTER_W, 0), de(K['leistung']['laser'], 0),
             de(K['leistung']['pi'], 0),
             de(K['leistung']['summe'], 0), de(K['leistung']['dauer'], 0))),
        ('Pi', 'Pi Zero 2 W auf dem Pi-Halter rechts neben dem Kasten, ganz '
         'über dem 2060; sein 5-V-Wandler hängt vor Schalter und Not-Aus an '
         'der Buchse (docs/pi.md)'),
        ('Endschalter', 'LM393-Gabellichtschranken: X links auf der 2020 '
         'des Portals, Y '
         'außen am rechten 2040 — schaltet {} (Toolhead mit Z unten {} mm '
         'vor dem 2060); Z vorhanden'.format(K['grenze_hinten'],
                                             de(K['luft_2060'], 0))),
        ('Kette Y', '{} mm Hub + {} mm Reserve, Festpunkt hinten in der '
         'Wanne Y ({} mm vom hinteren Ende des 2040), Schleife nach vorn, '
         '{} Glieder, {} mm mit Endstücken (R{})'.format(
             de(K['ky_hub'], 0), de(L['yk_reserve_vorn'], 0),
             de(K['ky_fest'] - L['rahmen_y'][0], 0), K['ky_glieder'],
             de(K['ky_laenge'], 0), de(KETTE_R, 0))),
        ('Kette X', '{} mm Hub, Festpunkt in der Mitte des Wegs, Schleife '
         'nach rechts (links steht der X-Motor), {} Glieder, {} mm mit '
         'Endstücken (R{})'.format(
             de(K['kx_hub'], 0), K['kx_glieder'], de(K['kx_laenge'], 0),
             de(KETTE_R, 0))),
    ]
    for n in ('Y-Motor links', 'Y-Motor rechts', 'X-Motor', 'Z-Motor',
              'Laser (12 V + PWM)', 'X-Endschalter', 'Y-Endschalter',
              'Z-Endschalter', 'Not-Aus', 'Pi 24 V', 'USB Pi–Uno'):
        mm = kab[n][0]
        zeilen.append(('Kabel' if n == 'Y-Motor links' else '',
                       '{}: Weg ≈ {} m → {} m kaufen'.format(
                           n, de(mm / 1000.0, 2), de(kauflaenge(mm), 2))))
    t.append(text(24, ty - 8, 'Zahlen', 10.5, BLAU, fett=True))
    for i, (k, v) in enumerate(zeilen):
        t.append(text(24, ty + 10 + i * 15, k, 8.5, GRAU))
        t.append(text(110, ty + 10 + i * 15, v, 8.5, TEXT))
    ly = ty + 10 + len(zeilen) * 15 + 20
    for i, (art, s) in enumerate((('neu', 'neu zu drucken (PETG)'),
                                  ('druck', 'Portal (vorhanden)'),
                                  ('toolhead', 'Toolhead'),
                                  ('profil', 'Aluprofil'),
                                  ('fuehrung', 'Linearführung'),
                                  ('kauf', 'Kaufteil'),
                                  ('kette', 'Energiekette (gedruckt)'))):
        x = 24 + (i % 4) * 170
        y = ly + (i // 4) * 18
        t.append(rect_px(x, y, x + 14, y + 9, art))
        t.append(text(x + 19, y + 8, s, 8.5))
    x, y = 24 + 3 * 170, ly + 18
    t.append(linie(x, y + 4.5, x + 16, y + 4.5, KABEL, 1.6, '5 3'))
    t.append(text(x + 21, y + 8, 'Kabel, fest verlegt', 8.5))
    y = ly + 36
    t.append(el('rect', {'x': '24', 'y': f1(y), 'width': '14', 'height': '9',
                         'fill': 'url(#schraffur)', 'stroke': ORANGE}))
    t.append(text(43, y + 8, 'Elektronikfach', 8.5))
    t.append(el('circle', {'cx': f1(24 + 170 + 7), 'cy': f1(y + 4.5),
                           'r': '4.5', 'fill': ROT}))
    t.append(text(24 + 170 + 19, y + 8, 'Endschalter', 8.5))
    t.append(text(24, ly + 66, 'Gestrichelt: Platzhalter bzw. andere '
                  'Stellung. Kabelwege mit {} % Reserve aufgerundet; die '
                  'Ketten zählen mit ihrer ganzen Länge.'.format(
                      de(RESERVE * 100, 0)), 8.5, GRAU))
    W = int(fa.ox + fa.breite + 250)
    H = int(ly + 82)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
           'viewBox="0 0 {0} {1}" font-family="Inter, Helvetica, Arial, '
           'sans-serif">'.format(W, H) + '\n'.join(t) + '</svg>')
    xml.dom.minidom.parseString(svg.encode('utf-8'))
    with open(ZIEL, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('geschrieben:', os.path.relpath(ZIEL), W, 'x', H)
    for n, (mm, _) in K['kabel'].items():
        print('  {:<22} Weg {:6.0f} mm  -> {} m'.format(n, mm,
                                                        kauflaenge(mm)))
    print('  Kette Y {:.0f} mm, Kette X {:.0f} mm'.format(K['ky_laenge'],
                                                         K['kx_laenge']))
    li = litzen(K)
    print('  Litze 24 V {} mm2: Not-Aus {} m hin und zurueck, {:.2f} V bei '
          '{:.0f} A'.format(LITZE_24V, li['not_m'], li['not_u'],
                            li['netz_a']))
    print('  Litze Laser {} mm2, {} m: {:.2f} V = {:.1f} % von {:.0f} V'
          .format(LITZE_LASER, li['laser_m'], li['laser_u'],
                  100.0 * li['laser_u'] / LASER_V, LASER_V))
    print('  Litze Motor {} mm2, {} m: {:.2f} Ohm = {:.0f} % der Wicklung'
          .format(LITZE_MOTOR, li['motor_m'], li['motor_r'],
                  100.0 * li['motor_r'] / MOTOR_R))
    print('  Pi: W18 {} mm2, {} m: {:.2f} A, {:.3f} V; W19 {} m: {:.2f} A, '
          '{:.2f} V (AWG 24) bis {:.2f} V (AWG 28); W17 {} m: {:.2f} A, '
          '{:.2f} V (AWG 28)'.format(
              LITZE_24V, li['pi24_m'], li['pi24_a'], li['pi24_u'],
              li['pi5_m'], li['pi5_a'], li['pi5_u'][24], li['pi5_u'][28],
              li['usb_m'], li['usb_a'], li['usb_u'][28]))


if __name__ == '__main__':
    main()
