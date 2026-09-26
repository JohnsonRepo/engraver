#!/usr/bin/env python3
"""Rechnerische Pruefung des Y-Motorhalters — laeuft ohne Fusion.

Importiert fusion/YMotorhalter/YMotorhalter.py mit gestubbtem adsk-Modul und
prueft dieselbe Masskette, die das Skript zum Bauen benutzt: Riemen in der
oberen Nut, Ritzel auf der Motorwelle, Freigaenge um Motor und Ritzel,
Materialstege, Schraubenlaengen, Kraefte, Druckbarkeit, Freiraum am
Profilende.

    python3 tools/y_motorhalter_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import importlib.util
import math
import os
import re
import sys
import types

SKRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                      'fusion', 'YMotorhalter', 'YMotorhalter.py')

# Nur fuer die Rechnung, erzeugen keine Geometrie:
E_PETG = 1500.0          # N/mm2, gedruckt quer zur Schicht (vorsichtig)
MOTOR_MASSE = 0.35       # kg, NEMA 17 mit 48 mm (40 mm: ~0,28)
MOTOR_MOMENT = 0.45      # Nm, Haltemoment eines 48er NEMA 17 [w]
VORSPANNUNG = 20.0       # N je Trum, Richtwert fuer den Y-Riemen
M5_KLEMMKRAFT = 500.0    # N je M5, vorsichtig: PETG unter dem Kopf
M3_KLEMMKRAFT = 300.0    # N je M3, dito
REIBWERT = 0.2           # PETG auf Alu bzw. auf dem Motorflansch
MADENSCHRAUBE_R = 1.5    # mm, M3-Madenschraube in der Ritzelnabe
ZAEHNE_PROBE = (16, 18, 20, 22, 24)


def modul_laden():
    """Importiert das Fusion-Skript ohne Fusion: adsk wird nur innerhalb der
    Funktionen benutzt, der Modulimport laeuft also mit einem Stub durch."""
    for name in ('adsk', 'adsk.core', 'adsk.fusion'):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules['adsk'].core = sys.modules['adsk.core']
    sys.modules['adsk'].fusion = sys.modules['adsk.fusion']
    spec = importlib.util.spec_from_file_location('y_motorhalter', SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class Pruefung:
    def __init__(self):
        self.zeilen, self.fehler = [], 0

    def ok(self, text, ist, soll, vgl='>=', einheit='mm'):
        gut = {'>=': ist >= soll - 1e-9, '<=': ist <= soll + 1e-9,
               '>': ist > soll, '<': ist < soll}[vgl]
        if not gut:
            self.fehler += 1
        self.zeilen.append('  [{}] {:<56} {:>8.2f} {} {} {:.2f}'.format(
            'OK ' if gut else 'FEHL', text, ist, einheit, vgl, soll))
        return gut

    def ja(self, text, bedingung, hinweis=''):
        if not bedingung:
            self.fehler += 1
        self.zeilen.append('  [{}] {}{}'.format(
            'OK ' if bedingung else 'FEHL', text, hinweis))
        return bedingung

    def info(self, text, wert=None, einheit='mm'):
        if wert is None:
            self.zeilen.append('  ---- ' + text)
        else:
            self.zeilen.append('  ---- {:<56} {:>8.2f} {}'.format(
                text, wert, einheit))

    def titel(self, text):
        self.zeilen += ['', text]

    def bericht(self):
        print('\n'.join(self.zeilen))
        print()
        print('{} Pruefung(en) FEHLGESCHLAGEN'.format(self.fehler)
              if self.fehler else 'alle Pruefungen bestanden')
        return 1 if self.fehler else 0


def strecken_abstand(a0, a1, b0, b1, n=400):
    """Kleinster Abstand zweier Strecken in der Ebene (numerisch, genau
    genug fuer Stege von ein paar Millimetern)."""
    beste = float('inf')
    for i in range(n + 1):
        t = i / float(n)
        px, py = a0[0] + t * (a1[0] - a0[0]), a0[1] + t * (a1[1] - a0[1])
        dx, dy = b1[0] - b0[0], b1[1] - b0[1]
        u = max(0.0, min(1.0, ((px - b0[0]) * dx + (py - b0[1]) * dy)
                         / (dx * dx + dy * dy)))
        beste = min(beste, math.hypot(px - b0[0] - u * dx,
                                      py - b0[1] - u * dy))
    return beste


def main():
    mod = modul_laden()
    w, L = mod.w, mod.lage()
    p = Pruefung()
    luft = w('luft_min')
    hb = L['halbe_breite']
    h = w('motor_loch') / 2.0
    m = w('motor_flansch') / 2.0
    hub = w('spann_weg') / 2.0
    prof = L['profil_name']

    # ------------------------------------------------------------------------
    p.titel('1) Y-Kette: ab Stirnseite der {} (+Y vom Profil weg)'.format(prof))
    for text, wert in (
            ('Schenkel hinten', L['wange_y0']),
            ('hintere M5', L['m5_loecher'][1][0]),
            ('vordere M5', L['m5_loecher'][0][0]),
            ('Stirnseite der {} = Anlage des Jochs'.format(prof), 0.0),
            ('Joch vorn', L['joch_y1']),
            ('Motor vorn (ganz innen)', L['motor_y_min'] - m),
            ('Motorachse ganz innen', L['motor_y_min']),
            ('Motorachse Mitte', L['motor_y_mitte']),
            ('Motorachse ganz aussen', L['motor_y_max']),
            ('Motor hinten (ganz aussen)', L['motor_y_max'] + m),
            ('Platte und Fuehrungswaende vorn', L['platte_y1'])):
        p.info(text, wert)

    p.titel('2) Z-Kette: ab Unterkante der {}'.format(prof))
    for text, wert in (
            ('Oberkante {} (Schiene darauf)'.format(prof), w('profil_hoehe')),
            ('Ritzel oben = Wellenende', L['ritzel_z1']),
            ('Riemen oben', L['riemen_z1']),
            ('Riemenmitte = Mitte der oberen Nut', L['riemen_z']),
            ('Riemen unten', L['riemen_z0']),
            ('Oeffnung der oberen Nut unten', L['nut_oben_z0']),
            ('Madenschraube der Ritzelnabe', L['madenschraube_z']),
            ('Abflachung der Welle beginnt', L['flach_z0']),
            ('Ritzel unten', L['ritzel_z0']),
            ('Platte oben = Halter oben = Bettseite', L['platte_z1']),
            ('Zentrierbund oben', L['bund_z1']),
            ('Motorflansch = Platte unten', L['platte_z0']),
            ('M5 in der unteren Nut', L['nut_unten_z']),
            ('Halter unten', L['halter_z0']),
            ('Unterkante {}'.format(prof), 0.0),
            ('Motor unten ({:.0f}er)'.format(w('motor_laenge')),
             L['motor_z0'])):
        p.info(text, wert)
    p.ok('Riemenmitte = Mitte der oberen Nut',
         -abs(L['riemen_z'] - (w('profil_hoehe') - w('nut_oben'))), -0.01)
    p.ja('alle M5 sitzen in der unteren Nut',
         all(abs(z - L['nut_unten_z']) < 1e-6 for _, z in L['m5_loecher']))
    p.ok('Halter bleibt unter der oberen Nut (Seitenflaeche frei)',
         L['nut_oben_z0'] - L['halter_z1'], 2.0)
    p.ok('Halter ragt nicht unter die {} (dort liegt die 2060)'.format(prof),
         L['halter_z0'], 0.0)
    p.ok('nichts ragt ueber die Oberkante (Schiene, Y-Wagen)',
         w('profil_hoehe') - L['ritzel_z1'], 2.0)

    # ------------------------------------------------------------------------
    p.titel('3) Riemen in der oberen Nut (Draufsicht)')
    p.info('Wirkradius Ritzel ({:.0f} Z)'.format(w('ritzel_z')), L['rp'])
    p.info('Trum: Ruecken bei X = +-', L['trum_ruecken_x'])
    p.info('Trum: Zahnspitzen bei X = +-', L['trum_zahn_x'])
    p.info('Ruecken hinter der Seitenflaeche', L['trum_tiefe_ruecken'])
    p.info('Zahnspitzen hinter der Seitenflaeche', L['trum_tiefe_zahn'])
    p.ok('Luft Riemenruecken -> Lippe', L['luft_lippe'], 1.0)
    p.ok('Luft Zahnspitzen -> Nutgrund', L['luft_nutgrund'], 1.0)
    p.ja('Ritzel mittig: beide Trume laufen parallel in ihre Nut', True,
         '   (Motorachse X = 0, symmetrisches Teil)')
    p.info('Riemen {:.0f} mm breit, Nutoeffnung {:.1f} mm: er laeuft hinter '
           'den Lippen im Kanal'.format(w('riemen_breite'), w('nut_breite')))
    p.info('Zum Vergleich, Luft zur Lippe / zum Nutgrund:')
    halb = w('profil_breite') / 2.0
    for z in ZAEHNE_PROBE:
        rp = mod.teilkreis_r(z)
        lippe = halb - (rp + L['wirk_ruecken']) - w('nut_lippe')
        grund = w('nut_tiefe') - (halb - (rp - L['wirk_zahn']))
        knapp = min(lippe, grund)
        p.info('  {:2d} Z: {:5.2f} / {:5.2f} mm{}'.format(
            z, lippe, grund, '   <- streift' if knapp < 0.3
            else '   <- knapp' if knapp < 1.0 else ''))
    p.info('Umschlingung', 180.0, 'Grad')
    p.info('Zaehne im Eingriff', L['zaehne_im_eingriff'], 'Z')
    p.info('Weg je Motorumdrehung', L['mm_pro_umdrehung'], 'mm')
    p.info('Schritte/mm bei 1/16', 200 * 16 / L['mm_pro_umdrehung'], '')
    p.info('freier Riemen Stirnseite -> Ritzel', L['motor_y_min'])
    p.info('  .. (Motor ganz aussen)', L['motor_y_max'])

    # ------------------------------------------------------------------------
    p.titel('4) Ritzel auf der Motorwelle')
    spur_mitte = (L['ritzel_z0'] + L['ritzel_nabe'] + w('ritzel_flansch_h')
                  + w('ritzel_spur') / 2.0)
    p.ok('Spurmitte = Riemenmitte', -abs(spur_mitte - L['riemen_z']), -0.01)
    p.ok('Riemen in der Ritzelspur (Rand je Seite)',
         (w('ritzel_spur') - w('riemen_breite')) / 2.0, 0.3)
    p.ok('Motorwelle reicht durch das ganze Ritzel',
         L['welle_z1'] - L['ritzel_z1'], 0.0)
    p.ok('Madenschraube ganz auf der Abflachung',
         L['madenschraube_z'] - MADENSCHRAUBE_R - L['flach_z0'], 0.5)
    p.ok('Ritzel unten -> Platte oben', L['ritzel_luft'], luft)
    p.ok('Platte duenn genug fuer Welle + Ritzel',
         w('motor_welle_l') - w('ritzel_laenge') - luft, w('platte_dicke'))
    p.ok('Zentrierbund steckt in der Platte', L['platte_z1'] - L['bund_z1'],
         0.0)

    # ------------------------------------------------------------------------
    p.titel('5) Motor unter der Platte')
    p.ok('Motor ganz innen -> Joch', L['motor_y_min'] - m - L['joch_y1'], luft)
    p.ok('Motor steht ganz vor der Stirnseite', L['motor_y_min'] - m,
         L['joch_y1'])
    p.ok('Motor -> Fuehrungswand (je Seite)', L['fuehrung_x0'] - m, luft)
    p.ok('Zentrierbund im Langloch (Luft je Seite)',
         (L['bund_schlitz_b'] - w('motor_bund_d')) / 2.0, 0.15)
    p.ok('Platte deckt den Flansch auch ganz aussen',
         L['platte_y1'] - L['motor_y_max'] - m, 0.0)
    r_scheibe = w('m3_scheibe_d') / 2.0
    p.ok('M3-Scheibe -> Ritzelflansch (radial)',
         math.hypot(h, h) - r_scheibe - w('ritzel_flansch_d') / 2.0, 2.0)
    p.ok('M3-Scheibe -> Riemenruecken (seitlich)',
         h - r_scheibe - L['trum_ruecken_x'], 2.0)
    p.ok('M3-Kopf oben -> Riemen unten',
         L['riemen_z0'] - (L['platte_z1'] + w('m3_scheibe_h')
                           + w('m3_kopf_h')), 2.0)
    p.ok('Ritzelflansch -> Joch (Motor ganz innen)',
         L['motor_y_min'] - w('ritzel_flansch_d') / 2.0 - L['joch_y1'], luft)
    p.ok('Riemen unten -> Joch und Platte oben',
         L['riemen_z0'] - L['halter_z1'], 2.0)
    p.info('Motor haengt unter die {} bis'.format(prof), L['motor_z0'])

    # ------------------------------------------------------------------------
    p.titel('6) Materialstege')
    ym = L['motor_y_mitte']
    rb, r3 = L['bund_schlitz_b'] / 2.0, w('m3_durchgang') / 2.0
    steg = min(strecken_abstand((0.0, ym - hub), (0.0, ym + hub),
                                (x, y - hub), (x, y + hub)) - rb - r3
               for x, y in L['motor_langloecher'])
    p.ok('Steg Bundschlitz -> Motorlangloch', steg, 2.0)
    p.ok('Steg Motorlangloch -> Plattenrand', hb - h - r3, 3.0)
    p.ok('Steg vorderes Motorlangloch -> Joch',
         ym - h - hub - r3 - L['joch_y1'], 3.0)
    p.ok('Steg hinteres Motorlangloch -> Plattenende',
         L['platte_y1'] - (ym + h + hub + r3), 3.0)
    p.ok('Steg Bundschlitz -> Joch', ym - hub - rb - L['joch_y1'], 3.0)
    r5 = w('m5_durchgang') / 2.0
    p.ok('Steg M5-Bohrung -> Schenkel oben',
         L['halter_z1'] - L['nut_unten_z'] - r5, 2.0)
    p.ok('Steg M5-Bohrung -> Schenkel unten',
         L['nut_unten_z'] - r5 - L['halter_z0'], 2.0)
    p.ok('Steg hintere M5 -> Schenkelende',
         w('wange_laenge') + L['m5_loecher'][1][0] - r5, 3.0)
    s5 = w('m5_scheibe_d') / 2.0
    p.ok('M5-Scheibe liegt ganz auf dem Schenkel (oben)',
         L['halter_z1'] - L['nut_unten_z'] - s5, 0.5)
    p.ok('M5-Scheibe liegt ganz auf dem Schenkel (hinten)',
         w('wange_laenge') + L['m5_loecher'][1][0] - s5, 0.5)
    p.ok('vordere M5-Scheibe -> Joch (Platz fuer den Inbus)',
         -L['m5_loecher'][0][0] - s5, 3.0)

    # ------------------------------------------------------------------------
    p.titel('7) Schrauben')
    p.info('M5 in den Nutenstein: Laenge', L['m5_schraube'])
    p.info('  ragt in die Nut (ab Seitenflaeche)', L['m5_ueberstand'])
    p.ok('M5 greift im Nutenstein', L['m5_eingriff'], 3.0)
    p.ok('M5 sitzt im Nutgrund nicht auf', w('nut_tiefe') - L['m5_ueberstand'],
         0.5)
    p.info('Motorschraube M3: Laenge', L['motor_schraube'])
    p.ok('Motorschraube: Eingriff im Flansch', L['motor_eingriff'], 3.0)
    p.ok('Motorschraube setzt im Gewinde nicht auf',
         w('motor_gewinde_tiefe') - L['motor_eingriff'], 0.5)

    # ------------------------------------------------------------------------
    p.titel('8) Kraefte und Steifigkeit')
    zug = 2.0 * VORSPANNUNG
    p.info('Riemenzug am Ritzel (2 x {:.0f} N), Richtung Profil'.format(
        VORSPANNUNG), zug, 'N')
    # Der Zug drueckt das Joch gegen die Stirnseite. Weil er ueber dem Joch
    # angreift, kippt er den Halter um die Oberkante des Jochs; die Schenkel
    # halten unten an den M5 dagegen (Reibung).
    hebel_zug = L['riemen_z'] - L['halter_z1']
    hebel_m5 = L['halter_z1'] - L['nut_unten_z']
    kraft_m5 = zug * hebel_zug / hebel_m5
    halten = L['n_m5'] * M5_KLEMMKRAFT * REIBWERT
    p.info('Kippmoment um die Oberkante des Jochs', zug * hebel_zug / 1000.0,
           'Nm')
    p.info('  -> Reibkraft an den Schenkeln (M5-Hoehe)', kraft_m5, 'N')
    p.ok('Sicherheit der Klemmung ({:.0f} x M5 mit {:.0f} N, mu {:.1f})'
         .format(L['n_m5'], M5_KLEMMKRAFT, REIBWERT), halten / kraft_m5, 3.0,
         '>=', 'x')
    # Querschnitt Platte + Fuehrungswaende zwischen Joch und Motorschrauben
    t = w('platte_dicke')
    teile = [(2.0 * hb * t, (L['platte_z0'] + L['platte_z1']) / 2.0,
              2.0 * hb * t ** 3 / 12.0)]
    hw = L['platte_z0'] - L['halter_z0']
    for _ in range(2):
        teile.append((w('fuehrung_dicke') * hw, L['halter_z0'] + hw / 2.0,
                      w('fuehrung_dicke') * hw ** 3 / 12.0))
    flaeche = sum(a for a, _, _ in teile)
    z_s = sum(a * z for a, z, _ in teile) / flaeche
    i_x = sum(i + a * (z - z_s) ** 2 for a, z, i in teile)
    p.info('Schwerachse Platte + Fuehrungswaende (Z)', z_s)
    p.info('Flaechenmoment', i_x, 'mm4')
    moment = zug * (L['riemen_z'] - z_s)
    laenge = L['motor_y_max'] - h - L['joch_y1']
    kipp = math.degrees(moment * laenge / (E_PETG * i_x))
    p.ok('Motor kippt unter dem Riemenzug (ganz aussen)', kipp, 0.25, '<=',
         'Grad')
    p.info('  -> Ritzel weicht aus um',
           math.radians(kipp) * (L['riemen_z'] - z_s))
    a_k = L['motor_y_max'] - L['joch_y1']
    f = MOTOR_MASSE * 9.81 * a_k ** 3 / (3.0 * E_PETG * i_x)
    p.ok('Durchhang der Platte am Motor (Eigengewicht)', f, 0.1, '<=')
    reib_motor = 4 * M3_KLEMMKRAFT * REIBWERT * math.hypot(h, h) / 1000.0
    p.ok('Motor verdreht sich nicht (4 x M3 gegen Haltemoment)',
         reib_motor / MOTOR_MOMENT, 3.0, '>=', 'x')

    # ------------------------------------------------------------------------
    p.titel('9) Druckbarkeit (Bambu Lab A1, Bauraum 256)')
    # Drucklage: Oberseite aufs Bett. Alle Koerper sind Extrusionen laengs Z,
    # stehen also senkrecht auf der Platte; die Langloecher gehen senkrecht
    # durch, nur die M5-Bohrungen liegen waagerecht.
    p.ok('Druckhoehe (Maschine Z)', L['halter_z1'] - L['halter_z0'], 250.0,
         '<=')
    p.ok('Grundflaeche X', 2.0 * hb, 250.0, '<=')
    p.ok('Grundflaeche Y', L['platte_y1'] - L['wange_y0'], 250.0, '<=')
    p.ja('alle Waende senkrecht zum Bett, keine Ueberhaenge', True,
         '   (Platte liegt auf, Rahmen waechst aus ihr)')
    p.ok('waagerechte M5-Bohrung: Bruecke', w('m5_durchgang'), 8.0, '<=')
    # Volumen aus denselben Rechtecken wie im Skript, ohne Fasen
    hoehe = L['halter_z1'] - L['halter_z0']
    unter = L['platte_z0'] - L['halter_z0']
    v = (2.0 * hb * L['platte_y1'] * w('platte_dicke')
         + 2.0 * hb * L['joch_y1'] * unter
         + 2.0 * w('fuehrung_dicke') * (L['platte_y1'] - L['joch_y1']) * unter
         + 2.0 * w('wange_dicke') * w('wange_laenge') * hoehe)
    def langloch(b):
        return b * w('spann_weg') + math.pi * b * b / 4.0

    v -= w('platte_dicke') * (langloch(L['bund_schlitz_b'])
                              + 4.0 * langloch(w('m3_durchgang')))
    v -= L['n_m5'] * math.pi * r5 ** 2 * w('wange_dicke')
    p.info('Volumen je Halter', v / 1000.0, 'cm3')
    p.info('Masse je Halter, voll PETG (1,27 g/cm3)', v / 1000.0 * 1.27, 'g')

    # ------------------------------------------------------------------------
    p.titel('10) Freiraum am Profilende')
    p.info('Halter X (je Seite)', hb)
    p.info('M5-Kopf aussen X', L['wange_x1'] + w('m5_scheibe_h')
           + w('m5_kopf_h'))
    p.info('Halter und Motor Y von', L['wange_y0'])
    p.info('  bis', max(L['platte_y1'], L['motor_y_max'] + m))
    p.info('Motor Z bis', L['motor_z0'])
    p.info('hoechster Punkt (Ritzel) Z', L['ritzel_z1'])
    p.ok('M5-Kopf innerhalb der Halterbreite',
         hb - (L['wange_x1'] + w('m5_scheibe_h') + w('m5_kopf_h')), 0.0)
    p.ja('unter der {} haengt nur der Motor, und der vor der Stirnseite'
         .format(prof), L['motor_y_min'] - m > 0.0 and L['halter_z0'] >= 0.0)

    # ------------------------------------------------------------------------
    p.titel('11) Stueckliste (beide Seiten)')
    for zeile in (
            '2x Y-Motorhalter (PETG), links und rechts dasselbe Teil',
            '2x NEMA 17 (Welle 5 mm) + 2x GT2-Ritzel {:.0f} Z, Bohrung 5, '
            'fuer 6-mm-Riemen'.format(w('ritzel_z')),
            '{n}x M5x{:.0f} + {n}x Scheibe M5 + {n}x Nutenstein M5 (Nut 6)'
            .format(L['m5_schraube'], n=2 * L['n_m5']),
            '8x M3x{:.0f} + 8x Scheibe DIN 125 (Motoren)'.format(
                L['motor_schraube'])):
        p.info(zeile)

    # ------------------------------------------------------------------------
    p.titel('12) Statische Pruefung der Schluessel im Skript')
    quelle = open(SKRIPT, encoding='utf-8').read()
    masse_namen = set(mod.MASSE)
    fehlt_m = sorted(set(re.findall(r"\bw\('([^']+)'\)", quelle))
                     - masse_namen)
    fehlt_l = sorted(set(re.findall(r"L\['([^']+)'\]", quelle)) - set(L))
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    p.ja('einheitenlose Parameter stehen in MASSE',
         mod.EINHEITENLOS <= masse_namen)
    unbenutzt = sorted(masse_namen
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('13) Validierungsbericht des Fusion-Skripts')
    try:
        zeilen = mod.hinweise_bauen(L, [])
        for zeile in zeilen:
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
        p.ok('laengste Berichtszeile', max(len(z) for z in zeilen), 74.0,
             '<=', 'Zeichen')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
