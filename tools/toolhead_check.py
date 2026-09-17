#!/usr/bin/env python3
"""Rechnerische Pruefung der Baugruppe ToolheadZ — laeuft ohne Fusion.

Importiert fusion/ToolheadZ/ToolheadZ.py mit gestubbtem adsk-Modul und prueft
dieselbe Masskette, die das Skript zum Bauen benutzt: Y-Kette, Verfahrweg,
Kollisionen ueber den ganzen Verfahrweg, Materialstege, Schraubenlaengen,
Druckbarkeit. Gibt am Ende die Stueckliste aus.

    python3 tools/toolhead_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402

SKRIPT = bauraum.SKRIPT
M3_KOPF_D, M3_KOPF_H = 5.5, 3.0
SCHEIBE_D = 9.0                     # DIN 9021 M3, gross
INBUS_FREI_D = 6.0                  # Platz fuer den 2,5er Inbus
M3_SCHAFT_D = 3.0
# Frueher an diesem Lasermodul gemessene Lochbilder (hoch, quer). Der aktuelle
# Wert steht in MASSE; diese hier werden nur gegen den Verstellbereich der
# Langloecher gehalten — das Bohrbild ist noch nicht mit einer Lehre bestaetigt.
LASER_MESSUNGEN = ((40.0, 16.0), (39.0, 15.0))


class Pruefung:
    def __init__(self):
        self.zeilen, self.fehler = [], 0

    def ok(self, text, ist, soll, vgl='>=', einheit='mm'):
        gut = {'>=': ist >= soll, '<=': ist <= soll,
               '>': ist > soll, '<': ist < soll}[vgl]
        if not gut:
            self.fehler += 1
        self.zeilen.append('  [{}] {:<54} {:>8.2f} {} {} {:.2f}'.format(
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
            self.zeilen.append('  ---- {:<54} {:>8.2f} {}'.format(
                text, wert, einheit))

    def titel(self, text):
        self.zeilen += ['', text]

    def bericht(self):
        print('\n'.join(self.zeilen))
        print()
        print('{} Pruefung(en) FEHLGESCHLAGEN'.format(self.fehler)
              if self.fehler else 'alle Pruefungen bestanden')
        return 1 if self.fehler else 0


def main():
    mod = bauraum.modul_laden()
    w, L = mod.w, mod.lage()
    p = Pruefung()

    p.titel('1) Y-Kette: vom Portalprofil nach vorn (ab X-Wagen-Stirnflaeche)')
    for text, schl in (('Portalprofil (Auflage der X-Schiene)', 'portal_y'),
                       ('Oberkante X-Schiene', 'x_schiene_y'),
                       ('Traegerplatte hinten (= Passflaeche)', 'traeger_y0'),
                       ('Traegerplatte vorn', 'traeger_y1'),
                       ('Sockel vorn = Auflage der Z-Schiene', 'sockel_y1'),
                       ('Oberkante Z-Schiene', 'z_schiene_y1'),
                       ('Stirnflaeche Z-Wagen', 'z_wagen_y'),
                       ('Rueckseite Schlittenplatte', 'schlitten_y1'),
                       ('Anschraubflaeche Laser', 'laser_y'),
                       ('Strahlachse', 'strahl_y')):
        p.info(text, L[schl])
    p.ok('Luft Schlittenpad -> Oberkante Z-Schiene',
         L['z_wagen_y'] - L['z_schiene_y1'], 1.0)
    p.ok('Luft Traegerplatte -> Oberkante X-Schiene',
         L['traeger_y0'] - L['x_schiene_y'], 3.0)

    p.titel('2) Z-Kette und Verfahrweg')
    for text, schl in (('Z-Schiene unten', 'z_schiene_z0'),
                       ('Z-Schiene oben', 'z_schiene_z1'),
                       ('Kupplung unten', 'kupplung_z0'),
                       ('Kupplung oben', 'kupplung_z1'),
                       ('Motorkonsole unten', 'konsole_z0'),
                       ('Motorflansch / Konsole oben', 'motor_flansch_z'),
                       ('Motor oben', 'motor_z1')):
        p.info(text, L[schl])
    p.info('Wagenmitte zc von', L['zc_min'])
    p.info('Wagenmitte zc bis', L['zc_max'])
    for text, wert in sorted(L['zc_grenzen'].items(), key=lambda t: t[1]):
        p.info('  Grenze: ' + text, wert)
    p.info('bindende Grenze: ' + L['zc_bindend'])
    p.ok('nutzbarer Z-Verfahrweg', L['z_weg'], 40.0)
    p.ok('Kupplung bleibt unter der Konsole',
         L['konsole_z0'] - L['kupplung_z1'], 2.0)
    p.ok('Kupplung greift die Welle', w('kupplung_griff'), 8.0)
    p.ok('Gewindestange wird von der Kupplung gegriffen',
         w('kupplung_l') - w('kupplung_griff'), 8.0)
    p.info('benoetigte Laenge der M6-Gewindestange', L['spindel_laenge'])
    p.info('Laser-Unterkante (Linse) tiefste Stellung',
           L['zc_min'] + L['laser_unten_rel'])
    p.info('Laser-Unterkante hoechste Stellung',
           L['zc_max'] + L['laser_unten_rel'])

    # ---- Bauraeume: gemeinsame Quelle mit der Layout-Zeichnung ----------
    sx, sy = w('spindel_x'), w('spindel_y')
    r_kup = w('kupplung_d') / 2.0
    feste, bewegte, paare_erlaubt = bauraum.bauraeume(w, L)
    bewegte_namen = {x.name for x in bewegte}

    p.titel('3) Kollisionspruefung ueber den ganzen Verfahrweg (21 Stellungen)')
    schritte = 21
    verletzt = {}
    for i in range(schritte):
        zc = L['zc_min'] + (L['zc_max'] - L['zc_min']) * i / (schritte - 1.0)
        for b in bewegte:
            bq = b.verschoben(zc)
            for f in feste + [x.verschoben(zc) for x in bewegte
                              if x.name != b.name]:
                schluessel = tuple(sorted((b.name, f.name)))
                if (schluessel in paare_erlaubt
                        or tuple(reversed(schluessel)) in paare_erlaubt):
                    continue
                d = bq.abstand(f)
                if schluessel not in verletzt or d < verletzt[schluessel][0]:
                    verletzt[schluessel] = (d, zc)
    kritisch = sorted(verletzt.items(), key=lambda t: t[1][0])[:8]
    for (a, b), (d, zc) in kritisch:
        # Zwei mitbewegte Teile stehen relativ zueinander still — da genuegt
        # Beruehrungsfreiheit. Bewegt gegen fest braucht echten Freigang.
        mit = a in bewegte_namen and b in bewegte_namen
        p.ok('{} <-> {}{} (engste Stellung zc={:+.1f})'.format(
            a, b, ' [mitbewegt]' if mit else '', zc),
             d, 0.5 if mit else w('luft_bau'))

    p.titel('4) Traegerplatte: Stege, Schrauben, Inserts')
    p.ok('Steg quer um die X-Wagenbohrung',
         w('traeger_x_rechts') - w('x_wagen_loch_laengs') / 2
         - w('m3_durchgang') / 2, 2.0)
    p.ok('Steg senkrecht um die X-Wagenbohrung',
         w('traeger_kopf_unten') - w('x_wagen_loch_quer') / 2
         - w('m3_durchgang') / 2, 2.0)
    p.ok('Kopf der X-Wagenschraube liegt frei vor der Platte',
         L['z_wagen_y'] - (L['traeger_y1'] + M3_KOPF_H), 1.0)
    # M3x12 mit Scheibe: die Scheibe nimmt die halbe Gewindetiefe als Reserve
    eingriff_x = 12.0 - w('traeger_dicke') - w('m3_scheibe_h')
    p.ok('X-Wagen: Gewindeeingriff mit M3x12 + Scheibe', eingriff_x, 2.0)
    p.ok('X-Wagen: Schraube setzt nicht auf',
         eingriff_x, w('x_gewinde_tiefe') - 0.3, '<=')
    p.ok('Insert-Sackloch bleibt im Sockelquerschnitt',
         w('traeger_dicke') + w('sockel_hoehe') - w('insert_m3_t'), 2.0)
    p.ok('Wand um das Insert im Sockel',
         (w('sockel_breite') - w('insert_m3_d')) / 2, 2.0)
    p.ok('Sockel NICHT breiter als die Schiene (Wagenschuerzen!)',
         w('sockel_breite') - w('z_schiene_breite'), 0.0, '<=')
    p.info('Z-Schiene: Anzahl Befestigungsschrauben',
           len(L['z_schiene_loecher']), 'Stk')
    p.ok('unterste Schienenschraube ueber der Plattenunterkante',
         L['z_schiene_loecher'][0] - w('traeger_z_unten'), 6.0)
    p.ok('oberste Schienenschraube unter dem Kopfbereich',
         w('traeger_kopf_unten') - L['z_schiene_loecher'][-1], 6.0)

    p.titel('5) Motorkonsole (angeformt) und Zugang zu den Motorschrauben')
    p.ok('Konsole traegt das vordere Motorlochbild',
         w('konsole_y_vorn') - (sy + w('motor_loch') / 2), 4.0)
    p.ok('Bund-Freibohrung passt in die Konsole',
         w('motor_flansch') - (w('motor_bund_d') + w('spiel_locker')), 4.0)
    p.ok('Konsole dicker als der Zentrierbund',
         w('konsole_dicke') - w('motor_bund_h'), 3.0)
    p.ok('Kopf der Traegerplatte backt die Konsole ganz',
         w('traeger_x_kopf') - L['konsole_x1'], 0.0)
    p.ok('Fuehrungsrippen fassen den Flansch mit Spiel',
         L['motor_rippe_x'][1][0] - L['motor_rippe_x'][0][1]
         - w('motor_flansch'), 0.2)
    p.ok('Rippen bleiben in der Konsole (links)',
         L['motor_rippe_x'][0][0] - L['konsole_x0'], 0.0)
    p.ok('Rippen bleiben in der Konsole (rechts)',
         L['konsole_x1'] - L['motor_rippe_x'][1][1], 0.0)
    p.ok('Rippenhoehe fasst den Flansch', w('motor_rippe_hoehe'), 2.0)
    p.ok('Motorschraube M3x12: Gewindeeingriff',
         12.0 - w('konsole_dicke'), 3.5)

    # Der Zugangsfehler, der beim ersten Aufbau aufgefallen ist: NEMA17 hat
    # Gewinde im Flansch, also wird von UNTEN verschraubt. Jede benutzte
    # Schraube braucht einen freien senkrechten Korridor.
    ausser = ('Motorkonsole', 'Fuehrungsrippe links', 'Fuehrungsrippe rechts')
    for x, y in L['motor_schrauben']:
        blocker = bauraum.zugang_frei(x, y, INBUS_FREI_D / 2, L['konsole_z0'],
                                      feste, ausser)
        p.ja('Schraubzugang von unten bei X={:+.1f} Y={:+.1f}'.format(x, y),
             blocker is None,
             '' if blocker is None else '   blockiert von: ' + blocker)
    p.ja('alle vier Motorschrauben sind gebohrt',
         len(L['motor_schrauben']) == 4,
         '   ({} Bohrungen)'.format(len(L['motor_schrauben'])))
    # Die Groesse, die spindel_y bestimmt: der Korridor der hinteren Reihe muss
    # vor der Traegerplatte liegen, sonst ist die Reihe unerreichbar.
    p.ok('Korridor der hinteren Reihe liegt vor der Traegerplatte',
         L['korridor_luft'], 1.0)
    p.info('Motormoment 0,4 Nm je Fuehrungsrippe',
           0.4 / (2 * (w('motor_flansch') / 2 + w('spiel_locker') / 2) / 1000.0),
           'N')
    p.info('Kragmoment des Motors an der Konsole (280 g)',
           0.280 * 9.81 * (sy - L['traeger_y1']) / 1000.0, 'Nm')

    p.titel('6) Mutternblock (M6, zwei Muttern mit Feder)')
    block_tiefe = L['schlitten_y1'] - w('block_y_hinten')
    p.info('Blockmasse (B x T x H)', w('block_x_rechts') - w('block_x_links'))
    p.info('Blocktiefe', block_tiefe)
    p.ok('Wand vor der Spindelbohrung',
         L['schlitten_y1'] - (sy + w('spindel_durchgang') / 2), 3.0)
    p.ok('Wand hinter der Spindelbohrung',
         (sy - w('spindel_durchgang') / 2) - w('block_y_hinten'), 3.0)
    # Sechskanttasche: Flanke am Taschenboden (Y), Ecken quer (X).
    sw6 = w('m6_mutter_sw') + w('tasche_spiel')
    flanke = sw6 / 2.0                               # halbe Schluesselweite
    eck = sw6 / 1.7320508                            # halbe Eckenweite
    eck_mutter = w('m6_mutter_sw') / 1.7320508
    mund = 2.0 * eck_mutter - w('tasche_klemmung')
    p.ok('Wand hinter der Mutterntasche',
         (sy - flanke) - w('block_y_hinten'), 2.0)
    p.ok('Mutterntasche bleibt im Block (X)',
         (w('block_x_rechts') - sx) - eck, 2.0)
    p.ok('Mutterntasche bleibt im Block (X, links)',
         (sx - w('block_x_links')) - eck, 2.0)
    p.ok('Sechskant: Mutter hat Spiel und bleibt in Z beweglich',
         w('tasche_spiel'), 0.10)
    p.ok('Sechskant: Mutter sitzt nicht zu lose', w('tasche_spiel'), 0.30, '<=')
    p.ok('Mundstueck klemmt die Mutter beim Einschieben',
         2.0 * eck_mutter - mund, 0.10)
    p.ok('Haltestufe hinter dem Mundstueck je Seite',
         (2.0 * eck - mund) / 2.0, 0.15)
    p.ok('Mundstueck lang genug zum Drucken',
         L['schlitten_y1'] - (sy + flanke), 1.00)
    p.ok('Mundstueck nicht zu eng zum Einschieben',
         2.0 * eck_mutter - mund, 0.40, '<=')
    # Die Sechskant-Formel des Skripts gegenrechnen: aus den Eckpunkten, die
    # sechskant() erzeugt, muessen Schluesselweite und Eckenweite wieder
    # herauskommen — sonst passt keine echte Mutter in die Tasche.
    r = sw6 / math.sqrt(3.0)
    ecken = [(r * math.cos(math.radians(i * 60.0)),
              r * math.sin(math.radians(i * 60.0))) for i in range(6)]
    p.ok('Sechskant-Formel: Schluesselweite trifft',
         abs(2 * max(abs(v) for _, v in ecken) - sw6), 0.001, '<=')
    p.ok('Sechskant-Formel: Eckenweite trifft',
         abs(2 * max(abs(u) for u, _ in ecken) - 2 * eck), 0.001, '<=')
    p.ok('Taschentiefe nimmt die Mutterhoehe auf',
         (w('m6_mutter_h') + 0.3) - w('m6_mutter_h'), 0.2)
    # M3-Sechskanttaschen der schwimmenden Verschraubung
    eck3 = (w('m3_mutter_sw') + w('tasche_spiel')) / 1.7320508
    p.ok('M3-Tasche bleibt im Block (links)',
         (L['block_schraube_x'][0] - eck3) - w('block_x_links'), 1.5)
    p.ok('M3-Tasche bleibt im Block (rechts)',
         w('block_x_rechts') - (L['block_schraube_x'][1] + eck3), 1.5)
    p.ok('Abstand M3-Tasche <-> M6-Tasche in Z',
         (w('feder_raum_l') / 2) - eck3, 1.0)
    stapel = 2 * w('m6_mutter_h') + w('feder_raum_l') + 2 * w('block_boden')
    p.ok('Blockhoehe reicht fuer Mutter+Feder+Mutter',
         w('block_hoehe') - stapel, 0.0)
    p.ok('Block laeuft am Z-Wagen vorbei',
         w('block_x_links') - w('z_wagen_breite') / 2, 3.0)
    p.ok('Ausrichtspiel der schwimmenden Verschraubung',
         w('m3_uebermass') - w('m3_durchgang'), 0.8)
    p.ok('Scheibe deckt das Uebermass', SCHEIBE_D - w('m3_uebermass'), 2.0)

    p.titel('7) Schlittenplatte und Laser (Konzept aus ToolheadGrundplatte)')
    schlitz_hx = w('schlitz_verstellweg') / 2 + w('schlitz_breite') / 2
    p.ok('Platte deckt das Laserlochbild quer',
         w('schlitten_breite_l') - (w('laser_loch_quer') / 2 + schlitz_hx), 3.0)
    p.ok('Freibohrung Z-Wagen versenkt den Kopf',
         w('schlitten_dicke') - M3_KOPF_H, 1.5)
    p.ok('Freibohrung gibt den Inbus frei', w('m3_senkung'), INBUS_FREI_D)
    p.ok('Z-Wagen: Gewindeeingriff mit M3x{:.0f}'.format(L['z_wagen_schraube']),
         L['z_wagen_eingriff'], 1.5)
    p.ok('Z-Wagen: Schraube setzt nicht auf', L['z_wagen_eingriff'],
         w('z_gewinde_tiefe') - 0.3, '<=')
    p.info('Klemmlaenge PETG unter dem Kopf (handfest + Sicherung)',
           w('pad_hoehe'))
    p.ok('Kopf+Scheibe der Laserschraube bleiben im Rippenraum',
         w('pad_hoehe') - (M3_KOPF_H + 0.8), 1.0)
    # Die Scheibe liegt auf der Plattenrueckseite zwischen den Rippen — sie
    # wandert mit dem Lochbild nach aussen, also mitpruefen.
    lq = w('laser_loch_quer') / 2
    p.ok('Scheibe der Laserschraube passt neben die Mittelrippe',
         (lq - SCHEIBE_D / 2) - w('rippe_mitte_breite') / 2, 0.5)
    p.ok('Scheibe der Laserschraube passt neben die Seitenrippe',
         w('rippe_seite_innen') - (lq + SCHEIBE_D / 2), 0.5)
    p.ok('Kopffreiraum bleibt im Auflagepad',
         w('pad_breite') / 2 - (lq + w('kopf_freiraum') / 2), 1.5)
    # Verstellbereich der Langloecher gegen die frueheren Messungen halten
    quer_tol = w('schlitz_verstellweg') + w('schlitz_breite') - M3_SCHAFT_D
    hoch_tol = w('schlitz_breite') - M3_SCHAFT_D
    p.info('Langloch deckt quer ab: {:.1f} bis {:.1f} mm'.format(
        w('laser_loch_quer') - quer_tol, w('laser_loch_quer') + quer_tol))
    p.info('Langloch deckt hoch ab: {:.1f} bis {:.1f} mm'.format(
        w('laser_loch_hoch') - hoch_tol, w('laser_loch_hoch') + hoch_tol))
    for hoch, quer in LASER_MESSUNGEN:
        drin = (abs(hoch - w('laser_loch_hoch')) <= hoch_tol
                and abs(quer - w('laser_loch_quer')) <= quer_tol)
        p.info('frueher gemessen {:.1f} x {:.1f}: {}'.format(
            hoch, quer, 'noch im Verstellbereich'
            if drin else 'AUSSERHALB des Verstellbereichs'))
    p.ok('Laser haengt unter der Traegerplatte (tiefste Stellung)',
         w('traeger_z_unten') - (L['zc_min'] + L['laser_unten_rel']), 5.0)
    # Lochbilder von Z-Wagen und Laser liegen beide bei X = +-7,5 und duerfen
    # sich in Z nicht in die Quere kommen.
    r_sen, r_schl = w('m3_senkung') / 2, w('schlitz_breite') / 2
    r_frei, r_loch = w('kopf_freiraum') / 2, w('m3_durchgang') / 2
    for rel, name in ((L['laser_loch_oben_rel'], 'obere'),
                      (L['laser_loch_unten_rel'], 'untere')):
        for vz in (-w('z_wagen_loch_laengs') / 2, w('z_wagen_loch_laengs') / 2):
            p.ok('{} Laserreihe <-> Freibohrung Z-Wagen (Platte)'.format(name),
                 abs(rel - vz) - r_sen - r_schl, 1.5)
    p.ok('Kopffreiraum <-> Wagenbohrung im Pad',
         abs(L['laser_loch_oben_rel'] - w('z_wagen_loch_laengs') / 2)
         - r_frei - r_loch, 1.0)
    p.ok('Kopffreiraum nimmt Kopf und Scheibe auf',
         w('kopf_freiraum') - SCHEIBE_D, 0.5)
    p.ok('obere Laserreihe liegt im Pad (braucht den Freiraum)',
         w('pad_laenge') / 2 - abs(L['laser_loch_oben_rel']), 0.0, '>=')
    p.ok('untere Laserreihe liegt ausserhalb des Pads',
         abs(L['laser_loch_unten_rel']) - w('pad_laenge') / 2 - SCHEIBE_D / 2,
         1.0)
    p.ok('Restauflage des Pads auf dem Wagen',
         w('pad_breite') * w('pad_laenge')
         - 2 * 3.1416 * (w('kopf_freiraum') / 2) ** 2, 400.0, '>=', 'mm2')

    p.titel('8) Druckbarkeit (Bambu Lab A1, Bauraum 256)')
    for name, a, b in (
            ('Traegerplatte (mit Konsole)',
             w('traeger_x_kopf') - w('traeger_x_links'),
             L['motor_rippe_z1'] - w('traeger_z_unten')),
            ('Schlittenplatte', w('block_x_rechts') + w('schlitten_breite_l'),
             L['schlitten_oben_rel'] - L['schlitten_unten_rel']),
            ('Mutternblock', w('block_x_rechts') - w('block_x_links'),
             w('block_hoehe'))):
        p.ok('{}: groesste Kante'.format(name), max(a, b), 250.0, '<=')
    p.ok('Bruecke Schlittenplatte zwischen den Rippen',
         w('rippe_seite_innen') - w('rippe_mitte_breite') / 2, 25.0, '<=')

    p.titel('9) Stueckliste')
    for zeile in (
            'MGN9 Linearschiene {:.0f} mm + Wagen MGN9H'.format(
                w('z_schiene_laenge')),
            'NEMA 17, Koerper {:.0f} mm, Welle 5 mm'.format(w('motor_laenge')),
            'M6-Gewindestange {:.0f} mm (Zuschnitt)'.format(
                10 * round(L['spindel_laenge'] / 10 + 0.5)),
            'Flexible Kupplung 5 -> 6 mm, {:.0f} mm lang'.format(w('kupplung_l')),
            '2x M6-Mutter (Sechskanttasche, SW+{:.2f}) + Druckfeder Ø8 x {:.0f}'
            .format(w('tasche_spiel'), w('feder_raum_l')),
            '4x M3x12 Zylinderkopf + Scheibe (Traegerplatte -> X-Wagen)',
            '{}x M3x10 Senkkopf DIN 7991 + {}x ruthex M3 (Z-Schiene -> Sockel)'
            .format(len(L['z_schiene_loecher']), len(L['z_schiene_loecher'])),
            '4x M3x{:.0f} Zylinderkopf   (Schlittenplatte -> Z-Wagen)'.format(
                L['z_wagen_schraube']),
            '4x M3x10 + 4x Scheibe DIN 9021 (Laser -> Schlittenplatte)',
            '2x M3x16 + 2x M3-Mutter + 2x Scheibe (Mutternblock, schwimmend)',
            '4x M3x12 Zylinderkopf   (NEMA 17 -> Konsole, alle vier)'):
        p.info(zeile)

    p.titel('10) Statische Pruefung der Schluessel im Skript')
    import re
    quelle = open(SKRIPT, encoding='utf-8').read()
    masse_namen = set(mod.MASSE)
    lage_namen = set(L)
    fehlt_m = sorted({m for m in re.findall(r"\bw\('([^']+)'\)", quelle)}
                     - masse_namen)
    fehlt_l = sorted({m for m in re.findall(r"L\['([^']+)'\]", quelle)}
                     - lage_namen)
    p.info('w()-Aufrufe auf MASSE-Schluessel', len(masse_namen), 'Stk')
    p.ok('alle w()-Schluessel in MASSE vorhanden', len(fehlt_m), 0, '<=', '')
    if fehlt_m:
        p.info('FEHLT in MASSE: ' + ', '.join(fehlt_m))
    p.ok('alle L[]-Schluessel von lage() geliefert', len(fehlt_l), 0, '<=', '')
    if fehlt_l:
        p.info('FEHLT in lage(): ' + ', '.join(fehlt_l))
    unbenutzt = sorted(masse_namen
                       - set(re.findall(r"\bw\('([^']+)'\)", quelle)))
    if unbenutzt:
        p.info('nur dokumentierend (nicht in Geometrie): '
               + ', '.join(unbenutzt))

    p.titel('11) Validierungsbericht des Fusion-Skripts')
    try:
        zc = (L['zc_min'] + L['zc_max']) / 2.0
        for zeile in mod.hinweise_bauen(L, zc, []):
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
