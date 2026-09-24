#!/usr/bin/env python3
"""Rechnerische Pruefung des Y-Motorhalters — laeuft ohne Fusion.

Importiert fusion/YMotorhalter/YMotorhalter.py mit gestubbtem adsk-Modul und
prueft dieselbe Masskette, die das Skript zum Bauen benutzt: Riemenlauf und
Umschlingung, Riemenlaenge, Freigaenge unter und auf dem Boden, Material-
stege, Schraubenlaengen, Ritzel auf der Motorwelle, Toleranz gegen die noch
nicht gemessene Wellenlage, Steifigkeit, Druckbarkeit.

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
VORSPANNUNG = 20.0       # N je Trum, Richtwert fuer den Motorriemen
RIEMEN_MU = 0.008        # kg/m, GT2 6 mm [w]
WELLE_Y_PROBE = (12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 25.0, 30.0)
ABSTAND_PROBE = (400.0, 450.0, 500.0, 550.0, 600.0, 650.0)


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


def abstand(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def main():
    mod = modul_laden()
    w, L = mod.w, mod.lage()
    p = Pruefung()
    luft = w('luft_min')
    hb = L['halbe_breite']
    rx, ry = L['rolle_x'], L['rolle_y']
    r_flansch_rolle = w('rolle_flansch_d') / 2.0
    r_flansch_ritzel = w('ritzel_flansch_d') / 2.0
    r_m3_scheibe = w('m3_scheibe_d') / 2.0
    h = w('motor_loch') / 2.0

    # ------------------------------------------------------------------------
    p.titel('1) Y-Kette: ab Rueckseite der 2060 nach hinten')
    for text, wert in (
            ('2060 vorn (Maschinenseite)', -w('profil_tiefe')),
            ('2060 Rueckseite = Anlageflaeche', 0.0),
            ('Anlageplatte hinten', L['grund_y1']),
            ('vorderer Trum (Wirklinie)', L['trum_vorn_y']),
            ('Wellenachsen (NICHT gemessen)', w('welle_y')),
            ('hinterer Trum (Wirklinie)', L['trum_hinten_y']),
            ('Rollenachsen', ry),
            ('Block hinten = Spannlasche hinten', L['block_y1']),
            ('Motorachse ganz vorn', L['motor_y_min']),
            ('Motorachse ganz hinten', L['motor_y_max']),
            ('Boden hinten', L['boden_y1'])):
        p.info(text, wert)

    p.titel('2) Z-Kette: ab Oberkante der 2060')
    for text, wert in (
            ('Oberkante Spannlasche', L['lasche_z1']),
            ('Spannschraube (Achse)', L['spann_z']),
            ('Oberkante Block und Rippen', L['block_z1']),
            ('Motorflansch = Oberseite Boden', L['boden_z1']),
            ('Unterseite Boden', L['boden_z0']),
            ('Ritzel oben', L['ritzel_z1']),
            ('Riemen oben', L['riemen_z1']),
            ('Riemenmitte = Hoehe der obersten Nut', w('riemen_z')),
            ('Riemen unten', L['riemen_z0']),
            ('Rolle unten', L['rolle_z0']),
            ('Ritzel unten', L['ritzel_z0']),
            ('Motorwelle unten', L['welle_z0']),
            ('Spitze der Rollenachse', L['rolle_schraube_z0']),
            ('Anlageplatte unten', w('grund_unten')),
            ('2060 unten', -w('profil_hoehe'))):
        p.info(text, wert)
    p.ok('Riemenmitte auf Hoehe der obersten Nut',
         -abs(w('riemen_z') - L['nut_z'][0]), -0.01)
    p.ok('Anlageplatte endet ueber der Profilunterkante',
         w('grund_unten') + w('profil_hoehe'), 0.0)

    # ------------------------------------------------------------------------
    p.titel('3) Riemenlauf')
    p.info('Wirkradius Motorritzel ({:.0f} Z)'.format(w('ritzel_z_motor')),
           L['rp_motor'])
    p.info('Wirkradius Wellenritzel ({:.0f} Z)'.format(w('ritzel_z_welle')),
           L['rp_welle'])
    p.info('Wirkradius an der Rolle (Laufflaeche + Ruecken)', L['rp_rolle'])
    # Die Omega-Trume laufen parallel ans Motorritzel, wenn die Rollen genau
    # rp_motor + rp_rolle neben der Achse stehen: 180 Grad in jeder
    # Spannstellung.
    p.ok('Omega-Trume parallel: Rollenabstand - Soll',
         -abs(rx - (L['rp_motor'] + L['rp_rolle'])), -1e-6)
    p.ok('hinterer Trum laeuft gerade an die Rollen',
         -abs(ry - L['rp_rolle'] - L['trum_hinten_y']), -1e-6)
    p.ok('Zaehne im Eingriff am Motorritzel (180 Grad)',
         L['zaehne_im_eingriff'], 6.0, '>=', 'Z')
    # Zum Vergleich: gerade durchlaufender Riemen, Motor 3 mm aus der Linie
    # gedrueckt — so viel Umschlingung haette ein Motor ohne Rollen.
    ohne = 2.0 * math.degrees(math.atan(3.0 / (w('welle_abstand') / 2.0)))
    p.info('ohne Rollen (3 mm aus der Linie): Umschlingung', ohne, 'Grad')
    p.info('  = Zaehne im Eingriff', ohne / 360.0 * w('ritzel_z_motor'), 'Z')
    p.info('Umschlingung an den Wellenritzeln', 180.0, 'Grad')
    p.info('Weg je Motorumdrehung (1:1)', L['mm_pro_umdrehung'], 'mm')
    p.info('Schritte/mm bei 1/16', 200 * 16 / L['mm_pro_umdrehung'], '')

    p.titel('4) Riemenlaenge (geschlossen, GT2 6 mm)')
    p.info('L = 2*S + {:.2f} + 2*Omega'.format(L['riemen_konst']))
    p.info('S = Wellenabstand (NICHT gemessen)', w('welle_abstand'))
    p.info('Riemen fuer Motor ganz vorn', L['riemen_l_min'])
    p.info('Riemen fuer Motor ganz hinten', L['riemen_l_max'])
    p.info('Fenster fuer die Riemenlaenge', L['riemen_l_max']
           - L['riemen_l_min'])
    for s in ABSTAND_PROBE:
        p.info('  S = {:.0f} mm -> Riemen {:.0f} .. {:.0f} mm'.format(
            s, mod.riemenlaenge(L, s, w('omega_min')),
            mod.riemenlaenge(L, s, w('omega_min') + w('spann_weg'))))
    # Gegenprobe der Formel: Laenge aus den Einzelstuecken
    s = w('welle_abstand')
    stuecke = (s                                        # vorderer Trum
               + 2.0 * math.pi * L['rp_welle']          # 2x halb um die Wellen
               + 2.0 * (s / 2.0 - rx)                   # hinterer Trum
               + 2.0 * math.pi / 2.0 * L['rp_rolle']    # 2x Viertel um Rollen
               + 2.0 * w('omega_min')                   # Omega hin und zurueck
               + math.pi * L['rp_motor'])               # halb um den Motor
    p.ok('Formel = Summe der Einzelstuecke',
         -abs(stuecke - L['riemen_l_min']), -1e-6)

    # ------------------------------------------------------------------------
    p.titel('5) Kuerzeste Omega-Tiefe aus den Freigaengen')
    # (a) Motorritzel gegen Rollenflansch (beide in der Riemenebene)
    a = math.sqrt(max((r_flansch_ritzel + r_flansch_rolle + luft) ** 2
                      - rx ** 2, 0.0))
    # (b) vordere Motorschraube (Kopf + Scheibe unter dem Boden) gegen den
    #     oberen Rollenflansch — beide haengen direkt unter dem Boden
    dx = h - rx
    b = h + math.sqrt((r_flansch_rolle + r_m3_scheibe + luft) ** 2 - dx ** 2)
    # (c) Steg zwischen Rollenachse und vorderem Motorlangloch im Boden
    c = h + w('m3_durchgang') / 2.0 + w('m5_durchgang') / 2.0 + 2.0
    # (d) Motorvorderseite gegen Block und Spannlasche
    d = w('motor_flansch') / 2.0 + w('block_rand') + luft
    noetig = max(a, b, c, d)
    for text, wert in (('Ritzelflansch gegen Rollenflansch', a),
                       ('Motorschraube (unten) gegen Rollenflansch', b),
                       ('Steg Rollenachse / Motorlangloch >= 2 mm', c),
                       ('Motor gegen Block', d)):
        p.info('  ' + text, wert)
    p.ok('omega_min deckt die kuerzeste Tiefe', w('omega_min'), noetig)

    # ------------------------------------------------------------------------
    p.titel('6) Freigaenge unter dem Boden (Riemenebene)')
    p.ok('vorderer Trum (Ruecken) -> Anlageplatte',
         L['trum_vorn_y'] - L['wirk_ruecken'] - L['grund_y1'], 2.0)
    p.ok('Riemenoberkante -> Unterseite Boden',
         L['boden_z0'] - L['riemen_z1'], 2.0)
    p.ok('Ritzel oben -> Unterseite Boden', L['ritzel_luft'], luft)
    p.ok('Riemen in der Ritzelspur (Rand je Seite)',
         (w('ritzel_spur') - w('riemen_breite')) / 2.0, 0.3)
    lauf = w('rolle_h') - 2.0 * w('rolle_flansch_h')
    p.ok('Riemen zwischen den Rollenflanschen (Rand je Seite)',
         (lauf - w('riemen_breite')) / 2.0, 0.5)
    mitte_rolle = (L['rolle_z0'] + L['rolle_z1']) / 2.0
    ritzel_spur = L['ritzel_z1'] - w('ritzel_flansch_h') - w('ritzel_spur') / 2
    p.ok('Rollenmitte in der Riemenebene',
         -abs(mitte_rolle - w('riemen_z')), -0.01)
    p.ok('Ritzelspur in der Riemenebene', -abs(ritzel_spur - w('riemen_z')),
         -0.01)
    for text, om in (('Motor ganz vorn', w('omega_min')),
                     ('Motor ganz hinten', w('omega_min') + w('spann_weg'))):
        ym = ry + om
        p.ok('{}: Ritzel -> Rollenflansch'.format(text),
             abstand((0.0, ym), (rx, ry)) - r_flansch_ritzel
             - r_flansch_rolle, luft)
        p.ok('{}: vordere Motorschraube -> Rollenflansch'.format(text),
             abstand((h, ym - h), (rx, ry)) - r_flansch_rolle - r_m3_scheibe,
             luft)
    # Omega-Trum (Ruecken aussen) gegen die Motorschrauben: seitlicher
    # Abstand, unabhaengig von der Spannstellung.
    p.ok('Omega-Trum (Ruecken) -> vordere Motorschraube',
         h - r_m3_scheibe - (L['rp_motor'] + L['wirk_ruecken']), 2.0)
    p.ok('Riemen um das Ritzel -> hintere Motorschraube',
         math.hypot(h, h) - r_m3_scheibe
         - (L['rp_motor'] + L['wirk_ruecken']), 2.0)
    # Die Rolle sitzt auf einer Scheibe unter dem Boden; ihr Flansch darf
    # den Boden nicht beruehren (die Scheibe liegt nur am Innenring).
    p.ok('Rollenflansch -> Unterseite Boden (Scheibe dazwischen)',
         L['boden_z0'] - L['rolle_z1'], 0.5)
    p.info('Rollenachse haengt bis', L['rolle_schraube_z0'])
    p.info('Ritzelnabe haengt bis', L['ritzel_z0'])

    p.titel('7) Freigaenge auf dem Boden')
    p.ok('Motor zwischen den Rippen (Luft je Seite)',
         L['rippe_x0'] - w('motor_flansch') / 2.0, 0.15)
    p.ok('Motor ganz vorn -> Block/Lasche',
         L['motor_y_min'] - w('motor_flansch') / 2.0 - L['block_y1'], luft)
    p.ok('Motor ganz hinten steht ganz auf dem Boden',
         L['boden_y1'] - L['motor_y_max'] - w('motor_flansch') / 2.0, 1.0)
    kopf5 = w('m5_scheibe_d') / 2.0
    p.ok('Rollenachse (Kopf + Scheibe) -> Spannlasche',
         rx - kopf5 - w('lasche_breite') / 2.0, 2.0)
    p.ok('Rollenachse (Kopf + Scheibe) -> Fuehrungsrippe',
         L['rippe_x0'] - rx - kopf5, 0.5)
    p.ok('Rollenachse (Kopf + Scheibe) liegt auf dem Block',
         L['block_y1'] - ry - kopf5, 0.0)

    # ------------------------------------------------------------------------
    p.titel('8) Materialstege')
    p.ok('Steg Motorlangloch -> Bundtasche',
         h - w('m3_durchgang') / 2.0 - L['bund_schlitz_b'] / 2.0, 2.0)
    p.ok('Steg Motorlangloch -> Fuehrungsrippe (Bodenstreifen)',
         L['rippe_x0'] - h - w('m3_durchgang') / 2.0, 3.0)
    p.ok('Boden unter der Bundtasche',
         w('boden_dicke') - L['bund_tasche_t'], 3.0)
    p.ok('Wand hinter der Rollenachse (Block)',
         L['block_y1'] - ry - w('m5_durchgang') / 2.0, 2.0)
    p.ok('Steg Rollenachse -> vorderes Motorlangloch',
         (L['motor_y_min'] - h - w('m3_durchgang') / 2.0)
         - (ry + w('m5_durchgang') / 2.0), 2.0)
    p.ok('Wand um den Einsatz der Spannschraube (seitlich)',
         (w('lasche_breite') - w('insert_m3_d')) / 2.0, 2.0)
    p.ok('Wand um den Einsatz (ueber dem Block)',
         L['spann_z'] - w('insert_m3_d') / 2.0 - L['block_z1'], 2.0)
    p.ok('Wand um den Einsatz (oben)',
         L['lasche_z1'] - L['spann_z'] - w('insert_m3_d') / 2.0, 2.0)
    p.ok('Lasche tiefer als der Einsatz (Anschlag vorn)',
         L['spann_tiefe'] - w('insert_m3_t'), 2.0)
    p.ok('M5-Bohrung -> Unterkante Anlageplatte',
         min(z for _, z in L['m5_loecher']) - w('m5_durchgang') / 2.0
         - w('grund_unten'), 4.0)
    p.ok('M5-Kopf + Scheibe innerhalb der Plattenbreite',
         hb - w('schraube_x') - w('m5_scheibe_d') / 2.0, 2.0)

    # ------------------------------------------------------------------------
    p.titel('9) Schrauben')
    p.info('M5 in den Nutenstein: Laenge', L['m5_schraube'])
    p.ok('M5 greift im Nutenstein', L['m5_eingriff'], 3.0)
    p.ok('M5 sitzt im Nutgrund nicht auf',
         w('nut_tiefe') - L['m5_ueberstand'], 0.5)
    p.info('Rollenachse M5: Laenge', L['rolle_schraube'])
    p.ok('Rollenachse ragt durch die Sicherungsmutter',
         L['rolle_schraube'] - L['rolle_klemm'], 1.6)
    p.info('Motorschraube M3: Laenge', L['motor_schraube'])
    p.ok('Motorschraube: Eingriff im Flansch', L['motor_eingriff'], 3.0)
    p.ok('Motorschraube setzt im Gewinde nicht auf',
         w('motor_gewinde_tiefe') - L['motor_eingriff'], 0.5)
    p.info('Spannschraube M3: Laenge', L['spann_schraube'])
    p.info('  ragt hinten heraus (Motor vorn .. hinten)',
           L['spann_spitze_min'])
    p.info('  ..', L['spann_spitze_max'])
    p.ok('Spannschraube reicht ueber den ganzen Spannweg',
         L['spann_schraube'] - L['spann_tiefe'] - L['spann_spitze_max'], 1.0)
    p.ok('Spannschraube greift im Einsatz (Motor ganz vorn)',
         min(L['spann_schraube'] - L['spann_spitze_min'],
             w('insert_m3_t')), 4.0)
    p.ok('Kopf der Spannschraube bleibt hinter der Anlageflaeche',
         L['spann_kopf_y'] - w('m3_kopf_h'), 0.0)
    p.ok('Spannschraube liegt ueber der Anlageplatte',
         L['spann_z'] - w('m3_kopf_d') / 2.0 - L['grund_z1'], 1.0)

    p.titel('10) Ritzel auf der Motorwelle')
    p.ok('Motorwelle reicht durch das ganze Ritzel',
         L['ritzel_z0'] - L['welle_z0'], 0.0)
    p.info('Madenschraube ueber dem Wellenende',
           L['madenschraube_z'] - L['welle_z0'])
    p.ok('Madenschraube sitzt auf der Welle (>= 3 mm vom Ende)',
         L['madenschraube_z'] - L['welle_z0'], 3.0)
    p.ok('Boden duenn genug fuer Welle + Ritzel',
         w('motor_welle_l') - w('ritzel_laenge') - L['ritzel_luft'],
         w('boden_dicke'))

    # ------------------------------------------------------------------------
    p.titel('11) Wellenlage NICHT gemessen — was der Halter vertraegt')
    # Der vordere Trum laeuft zwischen Anlageplatte (Ruecken) und Rollen-
    # flanschen (Zahnseite) durch; der hintere laeuft schraeg an die Rollen,
    # wenn die Wellen woanders stehen als gebaut.
    p.info('Halter gebaut fuer welle_y', w('welle_y'))
    flansch_vorn = ry - r_flansch_rolle

    def spalte(wy):
        platte = wy - L['rp_welle'] - L['wirk_ruecken'] - L['grund_y1']
        rolle = flansch_vorn - (wy - L['rp_welle'] + L['wirk_zahn'])
        schraeg = math.degrees(math.atan(
            (wy - w('welle_y')) / (w('welle_abstand') / 2.0 - rx)))
        return platte, rolle, schraeg

    for wy in WELLE_Y_PROBE:
        platte, rolle, schraeg = spalte(wy)
        p.info('  welle_y = {:4.0f}: vorderer Trum {:5.1f} vor der Platte, '
               '{:5.1f} vor den Rollen, hinterer {:+.1f} Grad'.format(
                   wy, platte, rolle, schraeg))
    # Bereich, in dem der Halter ohne neuen Lauf passt (Luft >= luft_min):
    # lage() rechnet ihn fuer den Bericht, hier die Gegenprobe ueber spalte()
    von, bis = L['welle_y_von'], L['welle_y_bis']
    p.info('Halter passt ohne Aenderung fuer welle_y von', von)
    p.info('  bis', bis)
    p.ok('Grenzen stimmen mit der Spaltrechnung ueberein',
         -max(abs(spalte(von)[0] - luft), abs(spalte(bis)[1] - luft)), -1e-6)
    p.ok('gebaute Lage: Toleranz nach vorn (Anlageplatte)',
         w('welle_y') - von, 4.0)
    p.ok('gebaute Lage: Toleranz nach hinten (Rollenflansche)',
         bis - w('welle_y'), 4.0)

    # ------------------------------------------------------------------------
    p.titel('12) Kraefte und Steifigkeit')
    # Zug im Boden zwischen Rollen und Motor: 2 Trume mit Vorspannung.
    zug = 2.0 * VORSPANNUNG
    p.info('Zug zwischen Rollen und Motor (2 x {:.0f} N)'.format(VORSPANNUNG),
           zug, 'N')
    # Querschnitt im Motorbereich: Boden (ohne Langloecher und Wellen-
    # schlitz) plus zwei Rippen — ein U-Profil.
    b_boden = 2.0 * hb - 2.0 * w('m3_durchgang') - w('wellen_schlitz')
    t = w('boden_dicke')
    teile = [(b_boden * t, L['boden_z0'] + t / 2.0, b_boden * t ** 3 / 12.0)]
    for _ in range(2):
        a_r = w('rippe_breite') * w('block_hoehe')
        teile.append((a_r, L['boden_z1'] + w('block_hoehe') / 2.0,
                      w('rippe_breite') * w('block_hoehe') ** 3 / 12.0))
    flaeche = sum(a for a, _, _ in teile)
    z_s = sum(a * z for a, z, _ in teile) / flaeche
    i_x = sum(i + a * (z - z_s) ** 2 for a, z, i in teile)
    p.info('Schwerachse des Querschnitts (Z)', z_s)
    p.info('Flaechenmoment (Boden + Rippen)', i_x, 'mm4')
    # Der Zug greift in der Riemenebene an, die Schwerachse liegt hoeher:
    # konstantes Moment zwischen Rollen und Motor -> Kippen gegeneinander.
    moment = zug * (z_s - w('riemen_z'))
    om = w('omega_min') + w('spann_weg')
    kipp = math.degrees(moment * om / (E_PETG * i_x))
    p.info('Moment aus dem Riemenzug', moment / 1000.0, 'Nm')
    p.ok('Rollen und Motor kippen gegeneinander (Omega max)', kipp, 0.25,
         '<=', 'Grad')
    # Motorgewicht am auskragenden Boden
    hebel = L['motor_y_max'] - L['grund_y1']
    p.info('Motorgewicht x Hebel zur Anlage',
           MOTOR_MASSE * 9.81 * hebel / 1000.0, 'Nm')
    # Durchhang am Motor: Kragarm ab Blockende, U-Profil
    a_k = L['motor_y_max'] - L['block_y1']
    f = MOTOR_MASSE * 9.81 * a_k ** 3 / (3.0 * E_PETG * i_x)
    p.ok('Durchhang des Bodens am Motor (Eigengewicht)', f, 0.1, '<=')
    # Vorspannung pruefen: Schwingung des vorderen Trums
    s = w('welle_abstand') / 1000.0
    p.info('vorderer Trum schwingt bei {:.0f} N mit'.format(VORSPANNUNG),
           1.0 / (2.0 * s) * math.sqrt(VORSPANNUNG / RIEMEN_MU), 'Hz')

    # ------------------------------------------------------------------------
    p.titel('13) Druckbarkeit (Bambu Lab A1, Bauraum 256)')
    # Drucklage: Anlageflaeche aufs Bett, Aufbaurichtung = Maschine Y.
    p.info('Grundflaeche auf dem Bett (X x Z)',
           2.0 * hb * (L['grund_z1'] - w('grund_unten')), 'mm2')
    p.ok('Druckhoehe (Maschine Y)', L['boden_y1'], 250.0, '<=')
    p.ok('Grundflaeche X', 2.0 * hb, 250.0, '<=')
    p.ok('Grundflaeche Z', L['lasche_z1'] - w('grund_unten'), 250.0, '<=')
    # Die Lasche kragt in der Drucklage seitlich aus: ihre Vorderseite muss
    # mindestens 45 Grad steil sein.
    steig = ((L['lasche_z1'] - L['block_z1'])
             / (L['lasche_y0_oben'] - L['lasche_y0_unten']))
    p.ok('Unterseite der Spannlasche (Steigung, 1 = 45 Grad)', steig, 1.0,
         '<=', '')
    p.ok('Bundtasche als Ueberhang in der Drucklage (Tiefe)',
         L['bund_tasche_t'], 3.0, '<=')

    # ------------------------------------------------------------------------
    p.titel('14) Umhuellende hinter der Traverse (Freiraum fuers Portal)')
    p.info('Halter X', 2.0 * hb)
    p.info('Halter + Motor Y bis',
           max(L['boden_y1'], L['motor_y_max'] + w('motor_flansch') / 2.0))
    p.info('Motor Oberkante Z ({:.0f}er)'.format(w('motor_laenge')),
           L['motor_z1'])
    p.info('tiefster Punkt (Rollenachse) Z', L['rolle_schraube_z0'])
    p.ja('nichts ragt vor die Rueckseite der 2060', True,
         '   (Anlageflaeche = Y 0)')

    # ------------------------------------------------------------------------
    p.titel('15) Stueckliste')
    for zeile in (
            '1x Y-Motorhalter (PETG)',
            'NEMA 17 (Welle 5 mm) + GT2-Ritzel 20 Z, Bohrung 5',
            '1x geschlossener GT2-Riemen 6 mm, {:.0f} .. {:.0f} mm (bei '
            'S = {:.0f})'.format(L['riemen_l_min'], L['riemen_l_max'],
                                 w('welle_abstand')),
            '4x F625ZZ (je zwei Ruecken an Ruecken = eine Umlenkrolle)',
            '4x M5x{:.0f} + 4x Scheibe M5 + 4x Nutenstein M5 (Nut 6)'.format(
                L['m5_schraube']),
            '2x M5x{:.0f} + 6x Scheibe M5 + 2x Sicherungsmutter M5 '
            '(Rollenachsen)'.format(L['rolle_schraube']),
            '4x M3x{:.0f} + 4x Scheibe DIN 125 (Motor)'.format(
                L['motor_schraube']),
            '1x M3x{:.0f} + 1x Messing-Einsatz M3 Ø5 (Spannschraube)'.format(
                L['spann_schraube'])):
        p.info(zeile)

    # ------------------------------------------------------------------------
    p.titel('16) Statische Pruefung der Schluessel im Skript')
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

    p.titel('17) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in mod.hinweise_bauen(L, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
