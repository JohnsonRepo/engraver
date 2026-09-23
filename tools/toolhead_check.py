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
# Zwei Scheiben im Einsatz: gross am schwimmenden Mutternwinkel (deckt das
# Uebermass der Ausrichtbohrung), normal am Laser (Rundloch Ø4,0).
SCHEIBE_GROSS = 9.0                 # DIN 9021 M3
SCHEIBE_NORM = 7.0                  # DIN 125 M3
INBUS_FREI_D = 6.0                  # Platz fuer den 2,5er Inbus
# Kuerzester nutzbarer Schenkel eines 2,5-mm-Inbus. Darunter kommt
# man an die Schraube nicht mehr heran, auch wenn die Bohrung frei ist.
WERKZEUG_LAENGE = 20.0
M3_SCHAFT_D = 3.0
# Frueher an diesem Lasermodul gemessene Lochbilder (hoch, quer). Der aktuelle
# Wert steht in MASSE und ist seit 2026-09-17 mit einer Lehre am Teil
# bestaetigt; diese hier bleiben als Messhistorie im Bericht stehen.
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
                       ('Motorkonsole oben / Adapter unten', 'adapter_z0'),
                       ('Motorflansch / Adapter oben', 'motor_flansch_z'),
                       ('Motor oben', 'motor_z1')):
        p.info(text, L[schl])
    p.info('Wagenmitte zc von', L['zc_min'])
    p.info('Wagenmitte zc bis', L['zc_max'])
    for text, wert in sorted(L['zc_grenzen'].items(), key=lambda t: t[1]):
        p.info('  Grenze: ' + text, wert)
    p.info('bindende Grenze: ' + L['zc_bindend'])
    p.info('mechanischer Z-Verfahrweg', L['z_weg'])
    # Gearbeitet wird nur bis zum Schaltpunkt des Endschalters. Fuer 0 bis
    # werkstueck_max mm Werkstueck muss die Linse genau so weit fahren koennen.
    p.ok('Arbeitsweg bis zum Endschalter deckt 0..{:.0f} mm Werkstueck'.format(
             w('werkstueck_max')),
         L['z_arbeit'] - w('werkstueck_max'), 5.0)
    # Mit dem Motoradapter ragt die Kupplung oben in die Bundbohrung der
    # Konsole. Das darf sie, solange sie dort frei dreht und ihre obere
    # Klemmschraube (etwa in der Mitte der oberen Nabe) unter der Konsole
    # erreichbar bleibt — Kopf und Inbus brauchen dort je ~3 mm.
    p.info('Kupplung ragt in die Bundbohrung der Konsole',
           max(L['kupplung_in_konsole'], 0.0))
    p.ok('Kupplung dreht frei in der Bundbohrung (Luft rundum)',
         (w('motor_bund_d') + w('spiel_locker') - w('kupplung_d')) / 2, 1.0)
    p.ok('obere Klemmschraube der Kupplung unter der Konsole erreichbar',
         L['konsole_z0'] - L['kupplung_klemm_z'], 3.0)
    p.info('Motorwelle unter der Konsole', L['konsole_z0'] - L['welle_z0'])
    p.ok('Einstecktiefe je Seite', w('kupplung_griff'), 6.0)
    p.info('Klemmlaenge bezogen auf den Spindeldurchmesser',
           w('kupplung_griff') / w('spindel_d'), 'x D')
    # Motorwelle und Spindel duerfen sich in der Kupplung nicht beruehren —
    # sonst drueckt das Anziehen der Klemmung auf das Motorlager.
    p.ok('Welle und Spindel stossen in der Kupplung nicht zusammen',
         L['kupplung_frei'], 0.5)
    p.info('benoetigte Laenge der Tr8x2-Spindel', L['spindel_laenge'])
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
        # 0,01 Toleranz: die bindende Verfahrgrenze ist aus luft_bau
        # gerechnet, der Abstand wird an ihr also genau luft_bau — in
        # Gleitkomma knapp darunter.
        p.ok('{} <-> {}{} (engste Stellung zc={:+.1f})'.format(
            a, b, ' [mitbewegt]' if mit else '', zc),
             d + 0.01, 0.5 if mit else w('luft_bau'))

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
    # Die engste Stelle im ganzen Teil: der Sockel darf nicht breiter werden
    # als die Schiene, also begrenzt seine Breite den Einsatzdurchmesser.
    p.ok('Wand um das Insert im Sockel',
         (w('sockel_breite') - w('insert_m3_d')) / 2, 2.0)
    p.info('Einpressbohrung (Einsatz-Aussendurchmesser 5,0 mm)',
           w('insert_m3_d'))
    p.ok('Sockel NICHT breiter als die Schiene (Wagenschuerzen!)',
         w('sockel_breite') - w('z_schiene_breite'), 0.0, '<=')
    p.info('Z-Schiene: Anzahl Befestigungsschrauben',
           len(L['z_schiene_loecher']), 'Stk')
    p.ok('unterste Schienenschraube ueber der Plattenunterkante',
         L['z_schiene_loecher'][0] - w('traeger_z_unten'), 6.0)
    # Die Schiene laeuft jetzt bis in den Kopfbereich hinauf. Entscheidend ist
    # nicht mehr, dass sie unter ihm bleibt, sondern dass jedes Loch noch
    # Material unter sich hat — also unter der Konsole liegt.
    p.ok('oberste Schienenschraube unter der Motorkonsole',
         L['konsole_z0'] - L['z_schiene_loecher'][-1], 6.0)
    p.ok('Sockel traegt die Schiene auf ganzer Laenge',
         L['konsole_z0'] - L['z_schiene_z1'], 0.0)
    # Die Schiene sitzt in Z FEST und ist damit ein dauerhaftes Hindernis:
    # ihr unteres Ende muss ueber dem dicksten Werkstueck bleiben.
    oberkante_werkstueck = -w('bett_abstand') + w('werkstueck_max')
    p.ok('Schienenende ueber dem dicksten Werkstueck',
         L['z_schiene_z0'] - oberkante_werkstueck, 5.0)
    p.ok('Plattenunterkante ueber dem dicksten Werkstueck',
         w('traeger_z_unten') - oberkante_werkstueck, 5.0)
    p.info('moegliche Werkstueckhoehe (feste Teile, 5 mm Luft)',
           L['werkstueck_frei'])
    # Versteifungsrippen: Steifigkeit gegen das Kragmoment des Motors.
    # Flaechenmoment um die X-Achse, Platte + zwei Rippen (Steiner).
    rippe_b = w('saeule_rippe_x1') - w('saeule_rippe_x0')
    breite = w('traeger_x_rechts') - w('traeger_x_links')
    d, tr = w('traeger_dicke'), w('saeule_rippe_tiefe')
    i_platte = breite * d ** 3 / 12.0
    i_rippen = 2 * (rippe_b * tr ** 3 / 12.0
                    + rippe_b * tr * (d + tr / 2.0 - d / 2.0) ** 2)
    hebel = L['konsole_z0'] - w('x_wagen_loch_quer') / 2
    kraft = 0.280 * 9.81                      # NEMA 17
    durchbiegung = lambda i: kraft * hebel ** 3 / (3 * 2000.0 * i)
    p.info('Kragarm Saeule (X-Wagen -> Konsole)', hebel)
    p.info('Durchbiegung am Motor OHNE Rippen', durchbiegung(i_platte))
    p.ok('Durchbiegung am Motor mit Rippen',
         durchbiegung(i_platte + i_rippen), 0.5, '<=')
    p.ok('Rippe laesst den Korridor der Motorschraube frei',
         w('saeule_rippe_x0') - (w('spindel_x') - w('motor_loch') / 2
                                 + INBUS_FREI_D / 2), 0.0)
    p.ok('Rippe bleibt in der Saeule', w('traeger_x_rechts')
         - w('saeule_rippe_x1'), 0.0)

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
    p.info('Motorschraube klemmt Konsole + Adapter', L['motor_klemm'])
    p.ok('Motorschraube M3x{:.0f}: Gewindeeingriff'.format(L['motor_schraube']),
         L['motor_eingriff'], 3.5)
    p.ok('Motorschraube setzt im Motorgewinde nicht auf',
         w('motor_gewinde_tiefe') - L['motor_eingriff'], 0.3)
    # --- Motoradapter: Distanzplatte zwischen Konsole und Motor ----------
    p.info('Motoradapter: Dicke = Motor hoeher als ohne', w('motor_adapter'))
    p.ok('Adapter passt zwischen die Fuehrungsrippen (Spiel gesamt)',
         L['motor_rippe_x'][1][0] - L['motor_rippe_x'][0][1]
         - w('motor_flansch'), 0.2)
    p.ok('Adapter ragt ueber die Rippen hinaus (Motor liegt frei auf)',
         w('motor_adapter') - w('motor_rippe_hoehe'), 2.0)
    p.ok('Adapter: Wand Bundbohrung -> Schraubenloch',
         math.hypot(w('motor_loch') / 2, w('motor_loch') / 2)
         - (w('motor_bund_d') + w('spiel_locker')) / 2
         - w('m3_durchgang') / 2, 2.0)
    p.ok('Adapter: Wand Schraubenloch -> Aussenkante',
         (w('motor_flansch') - w('motor_loch')) / 2 - w('m3_durchgang') / 2,
         2.0)
    # Die Traegerplatte ist gedruckt — der Adapter darf an ihr nichts
    # aendern. Gegenprobe: dieselbe Lage ohne Adapter.
    ohne = dict(mod.MASSE)
    ohne['motor_adapter'] = (0.0, ohne['motor_adapter'][1])
    alt, mod.MASSE = mod.MASSE, ohne
    try:
        L0 = mod.lage()
    finally:
        mod.MASSE = alt
    traeger = ('konsole_z0', 'konsole_z1', 'konsole_x0', 'konsole_x1',
               'motor_rippe_x', 'motor_rippe_y1', 'motor_rippe_z1',
               'motor_schrauben', 'z_schiene_z0', 'z_schiene_z1',
               'z_schiene_loecher', 'saeule_rippe_x', 'x_wagen_loecher',
               'ls_sockel_z0', 'ls_sockel_z1', 'ls_schraub_z', 'ls_sockel_y1')
    anders = [k for k in traeger if L0[k] != L[k]]
    p.ja('Traegerplatte haengt nicht vom Motoradapter ab (bleibt wie '
         'gedruckt)', not anders,
         '   (anders: {})'.format(', '.join(anders)) if anders else '')

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

    p.titel('6) Werkzeugzugang: laesst sich das ueberhaupt montieren?')
    p.ja('Werkzeugkorridor hier und im Skript gleich definiert',
         abs(w('inbus_frei_d') - INBUS_FREI_D) < 1e-9,
         '   (Skript {:.1f} / Pruefung {:.1f} mm)'.format(
             w('inbus_frei_d'), INBUS_FREI_D))
    # Ein Inbus braucht nicht nur einen freien Korridor, sondern auch LAENGE.
    # Eine 6,5-Freibohrung mit dem Laser 6 mm dahinter ist unbenutzbar, auch
    # wenn "nichts in der Bohrung steht". Jede Verbindung wird in dem Zustand
    # geprueft, in dem sie verschraubt wird — Teile, die es dann noch nicht
    # gibt, blockieren nicht.
    kasten = {q.name: q for q in feste}

    def zustand(namen, zc=0.0):
        return ([kasten[n] for n in namen if n in kasten]
                + [q.verschoben(zc) for q in bewegte if q.name in namen])

    def kuerzester(punkte, achse, ri, boxen, eigen=()):
        """(kuerzeste freie Werkzeuglaenge, Hindernis) ueber alle Schrauben."""
        schlecht = (float('inf'), None)
        for pt in punkte:
            d, wer = bauraum.freier_korridor(pt, achse, ri, INBUS_FREI_D / 2,
                                             boxen, eigen)
            if d < schlecht[0]:
                schlecht = (d, wer)
        return schlecht

    def beste_stellung(punkte, achse, ri, namen, eigen=(), mitbewegt=True):
        """Maximum ueber den Verfahrweg: der Wagen laesst sich verschieben.
        mitbewegt=True heisst, die Schraube wandert mit dem Wagen (Z relativ
        zu zc); False sind feste Koordinaten wie die Motorschrauben."""
        best = (-1.0, None, 0.0)
        for i in range(21):
            zc = L['zc_min'] + (L['zc_max'] - L['zc_min']) * i / 20.0
            pkt = [(x, y, zc + z if mitbewegt else z) for x, y, z in punkte]
            d, wer = kuerzester(pkt, achse, ri, zustand(namen, zc), eigen)
            if d > best[0]:
                best = (d, wer, zc)
        return best

    def zugang(text, laenge, hindernis, soll=WERKZEUG_LAENGE, pruefen=True):
        """pruefen=False: nur berichten. Fuer die beiden Reihenfolge-Varianten
        ist EINE ausreichend, also darf die andere nicht als Fehler zaehlen."""
        beschriftung = '{}{}'.format(
            text, '' if laenge >= soll or not hindernis
            else '  [' + hindernis + ']')
        wert = 999.0 if laenge == float('inf') else laenge
        if pruefen:
            p.ok(beschriftung, wert, soll)
        else:
            p.info(beschriftung + ('  ok' if laenge >= soll else '  zu kurz'),
                   wert)
        return laenge >= soll

    # 1) Traegerplatte -> X-Wagen: nur Portal, Schiene, Wagen sind da.
    #    Schlanker Inbus, weil der Korridor den Z-Wagen streift.
    d, wer = kuerzester(
        [(x, L['traeger_y1'], z) for x, z in L['x_wagen_loecher']], 'y', +1,
        zustand(('Portalprofil 2020', 'X-Schiene MGN15', 'X-Wagen MGN15H')))
    zugang('Traegerplatte -> X-Wagen (von vorn, vor allem anderen)', d, wer)

    # 2) Z-Schiene -> Sockel: der Z-Wagen verdeckt je nach Stellung 2 Schrauben,
    #    also muss jede Schraube in MINDESTENS einer Wagenstellung frei sein.
    fehlt = []
    for z in L['z_schiene_loecher']:
        frei = max(bauraum.freier_korridor(
            (0.0, L['sockel_y1'], z), 'y', +1, INBUS_FREI_D / 2,
            zustand(('Z-Wagen MGN9H',), zc_w), ())[0]
            for zc_w in (L['zc_min'], L['zc_max']))
        if frei < WERKZEUG_LAENGE:
            fehlt.append(z)
    p.ja('alle {} Schienenschrauben in einer Wagenstellung erreichbar'.format(
             len(L['z_schiene_loecher'])),
         not fehlt, '' if not fehlt else '   blockiert bei Z=' + str(fehlt))

    # 3) + 4) Die beiden Verbindungen, die sich gegenseitig zubauen koennen:
    #    Schlittenplatte -> Z-Wagen (von vorn durch die Freibohrung) und
    #    Laser -> Schlittenplatte (von hinten, Gewinde sitzt im Laser).
    wagen_pkt = [(x, L['schlitten_y1'], z) for x, z in L['z_wagen_loecher']]
    laser_pkt_rel = [(x, L['schlitten_y1'], rel)
                     for rel in (L['laser_loch_oben_rel'],
                                 L['laser_loch_unten_rel'])
                     for x in (-w('laser_loch_quer') / 2,
                               w('laser_loch_quer') / 2)]
    eigen = ('Schlitten Pad/Rippen', 'Schlittenplatte')

    d_wagen_ohne, h1 = kuerzester(
        wagen_pkt, 'y', +1, zustand(eigen + ('Z-Wagen MGN9H',)), eigen)
    a1 = zugang('A) Platte -> Z-Wagen, Laser noch NICHT montiert',
                d_wagen_ohne, h1, pruefen=False)
    d_wagen_mit, h2 = kuerzester(
        wagen_pkt, 'y', +1,
        zustand(eigen + ('Z-Wagen MGN9H', 'Diodenlaser')), eigen)
    b2 = zugang('B) Platte -> Z-Wagen, Laser schon montiert',
                d_wagen_mit, h2, pruefen=False)

    d_laser_lose, h3 = kuerzester(
        [(x, y, z) for x, y, z in laser_pkt_rel], 'y', -1,
        zustand(eigen), eigen)
    b1 = zugang('B) Laser -> lose Platte (vor der Montage am Wagen)',
                d_laser_lose, h3, pruefen=False)
    d_laser_mont, h4, zc_l = beste_stellung(
        laser_pkt_rel, 'y', -1,
        eigen + ('Z-Wagen MGN9H', 'Z-Schiene MGN9', 'Schienensockel',
                 'Traegerplatte Hauptsaeule', 'Traegerplatte Kopf',
                 'X-Wagen MGN15H', 'X-Schiene MGN15', 'Portalprofil 2020'),
        eigen)
    a2 = zugang('A) Laser -> Platte, Platte schon am Wagen (beste Stellung '
                'zc={:+.1f})'.format(zc_l), d_laser_mont, h4,
                pruefen=False)

    # Es genuegt EINE der beiden Reihenfolgen. Gibt es keine, ist die
    # Baugruppe nicht montierbar — kein Kosmetikfehler, ein Denkfehler.
    p.ja('es gibt eine Montagereihenfolge fuer Laser und Z-Wagen',
         (a1 and a2) or (b1 and b2),
         '   A) Platte zuerst: {} / B) Laser zuerst: {}'.format(
             'ok' if a1 and a2 else 'nein', 'ok' if b1 and b2 else 'nein'))

    # Das Langloch verschiebt die Schraube — nach oben bis dicht an den
    # Z-Wagen. Die Lochmitte (Stellung 0) muss in jedem Fall montierbar sein.
    p.ok('Langloch: Stellbereich nach oben bis zum Z-Wagen',
         L['langloch_auf_max'], 0.0)
    p.ok('Langloch: Stellbereich insgesamt',
         L['langloch_auf_max'] - L['langloch_ab_max'], 4.0)

    # 5) Mutternwinkel: von vorn, mit Laser und Winkel montiert.
    winkel_eigen = ('Winkel Ruecken', 'Winkel Regal')
    d, wer = kuerzester(
        [(x, L['schlitten_y1'], 0.0) for x in L['winkel_schraube_x']], 'y', +1,
        zustand(eigen + winkel_eigen + ('Diodenlaser',)),
        eigen + winkel_eigen)
    zugang('Mutternwinkel -> Platte (von vorn, zuletzt)', d, wer)

    # 5b) Garnitur aufs Regal: von OBEN. Darueber steht irgendwann die
    #     Kupplung im Weg, der Schlitten wird dafuer heruntergefahren.
    alle_namen = tuple(kasten) + tuple(q.name for q in bewegte)
    d, wer, zc_g = beste_stellung(
        [(x, y, L['regal_z1_rel']) for x, y in L['t8_loecher']], 'z', +1,
        alle_namen,
        winkel_eigen + ('Antriebsmutter Tr8x2', 'Tr8x2-Spindel'))
    zugang('Garnitur -> Regal (4x M3 von oben, Schlitten bei zc={:+.1f})'
           .format(zc_g), d, wer)

    # 6) Motorschrauben: von unten, der Z-Schlitten wird dafuer weggefahren.
    #    Gemessen ab dem Kopf, also ab der Konsolenunterseite — Konsole und
    #    Adapter liegen zwischen Kopf und Motor und zaehlen nicht.
    motor_eigen = ('NEMA 17', 'Motoradapter', 'Motorkonsole',
                   'Fuehrungsrippe links', 'Fuehrungsrippe rechts')
    d, wer, zc_m = beste_stellung(
        [(x, y, L['konsole_z0']) for x, y in L['motor_schrauben']],
        'z', -1, alle_namen, motor_eigen, mitbewegt=False)
    zugang('Motor -> Konsole (von unten, Z-Schlitten bei zc={:+.1f})'.format(
        zc_m), d, wer)

    p.titel('7) Mutternwinkel und Tr8x2-Antrieb')
    # --- Regal: Flanschsitz mit vier Gewindeeinsaetzen --------------------
    r_lk = w('t8_lochkreis') / 2.0
    p.info('Regal: Breite', w('winkel_x_rechts') - w('winkel_x_links'))
    p.info('Regal: Tiefe', L['regal_y1'] - L['regal_y0'])
    p.info('Regal: Oberkante ueber der Wagenmitte', L['regal_z1_rel'])
    p.ok('Regal traegt den Flansch in Y rundum',
         (L['regal_y1'] - L['regal_y0']) - w('t8_flansch_d'), 0.0)
    p.ok('Regal traegt den Flansch in X rundum',
         (w('winkel_x_rechts') - w('winkel_x_links')) - w('t8_flansch_d'), 0.0)
    p.ok('Regal liegt ueber der Plattenoberkante',
         L['regal_z0_rel'] - L['schlitten_oben_rel'], 0.3)
    p.ja('genau deshalb: hinter der Platte waere kein Platz fuer den Flansch',
         L['schlitten_y1'] - (w('spindel_y') + w('t8_flansch_d') / 2) < 3.0,
         '   (er wuerde {:.1f} mm in die Platte laufen)'.format(
             (w('spindel_y') + w('t8_flansch_d') / 2) - L['schlitten_y1']))
    # Einsatzbohrungen auf dem um 45 Grad gedrehten Lochkreis.
    r45 = r_lk / math.sqrt(2.0)
    r_ein = w('insert_m3_d') / 2.0
    p.ok('Wand Einsatzbohrung -> Regalkante hinten',
         (w('spindel_y') - r45 - r_ein) - L['regal_y0'], 2.0)
    p.ok('Wand Einsatzbohrung -> Regalkante vorn',
         L['regal_y1'] - (w('spindel_y') + r45 + r_ein), 2.0)
    p.ok('Wand Einsatzbohrung -> Regalkante seitlich',
         (w('spindel_x') - r45 - r_ein) - w('winkel_x_links'), 2.0)
    # Die engste Stelle im Teil: zwischen Einsatz- und Spindelbohrung. Sie
    # laesst sich nicht vergroessern, der Lochkreis ist ein Kaufteilmass.
    p.ok('Wand Einsatzbohrung -> Spindelbohrung',
         r_lk - r_ein - w('spindel_durchgang') / 2.0, 1.2)
    p.ok('Material unter dem Einsatz-Sackloch',
         w('winkel_regal_dicke') - w('insert_m3_t'), 2.0)
    p.ok('Sackloch tiefer als der Einsatz (typisch 5,7 mm) — Schraube setzt '
         'nicht auf', w('insert_m3_t') - 5.7, 1.0)
    p.ok('Schraubenkopf der Garnitur laeuft an der Spindel vorbei',
         (r_lk - M3_KOPF_D / 2) - w('spindel_d') / 2, 1.0)
    p.ok('Einsatz bleibt unter dem Flanschrand',
         w('t8_flansch_d') / 2 - (r_lk + r_ein), 0.5)
    p.ok('Spindel laeuft frei durchs Regal',
         w('spindel_durchgang') - w('spindel_d'), 0.4)

    # --- Flanschverschraubung: glatte Flanschseite direkt auf dem Regal ----
    p.info('Flansch bis zum Einsatz', L['flansch_klemm'])
    p.ok('Schraube M3x{:.0f} greift in den Einsatz'.format(
             L['flansch_schraube']),
         L['flansch_schraube'] - L['flansch_klemm'], 4.0)
    p.ok('Schraube setzt im Sackloch nicht auf',
         w('insert_m3_t') - (L['flansch_schraube'] - L['flansch_klemm']),
         0.5)

    # --- Ruecken: schwimmende Verschraubung an der Lasche -----------------
    p.info('Ruecken: Dicke', w('winkel_ruecken'))
    p.info('Ruecken: Hoehe', L['regal_z1_rel'] - L['winkel_unten_rel'])
    # Die Spindel laeuft mitten durch den Ruecken; davor bleibt eine Haut,
    # die beide Schenkel verbindet und die Anlageflaeche durchgehend haelt.
    p.ok('Haut vor der Spindelbohrung im Ruecken',
         L['schlitten_y1'] - (w('spindel_y') + w('spindel_durchgang') / 2),
         2.0)
    # Die Spindelbohrung nimmt dem Ruecken die Mitte; es bleiben zwei
    # Schenkel, jeder muss eine Schraube mit Mutterntasche tragen.
    p.ok('Schenkel des Ruecken neben dem Spindelkanal',
         (w('spindel_x') - w('spindel_durchgang') / 2) - w('winkel_x_links'),
         6.0)
    p.ja('Spindelkanal ist nach hinten offen — druckt ohne Stuetzen',
         (w('spindel_y') - w('spindel_durchgang') / 2) < L['winkel_y0'],
         '   (Kanal bis Y={:.1f}, Rueckseite bei Y={:.1f})'.format(
             w('spindel_y') - w('spindel_durchgang') / 2, L['winkel_y0']))
    eck3 = (w('m3_mutter_sw') + w('tasche_spiel')) / 1.7320508
    p.ok('M3-Tasche bleibt im Ruecken (links)',
         (L['winkel_schraube_x'][0] - eck3) - w('winkel_x_links'), 1.5)
    p.ok('M3-Tasche bleibt im Ruecken (rechts)',
         w('winkel_x_rechts') - (L['winkel_schraube_x'][1] + eck3), 1.5)
    p.ok('Material unter der Schraubenreihe', w('winkel_unten') - eck3, 1.5)
    p.ok('M3-Tasche laeuft an der Spindelbohrung vorbei',
         (w('spindel_x') - w('spindel_durchgang') / 2)
         - (L['winkel_schraube_x'][0] + eck3), 1.0)
    p.ok('Wand hinter der Mutterntasche',
         w('winkel_ruecken') - (w('m3_mutter_h') + 0.3), 2.0)
    p.ok('Sechskant: Mutter hat Spiel', w('tasche_spiel'), 0.10)
    p.ok('Sechskant: Mutter sitzt nicht zu lose', w('tasche_spiel'), 0.30, '<=')
    # Die Sechskant-Formel des Skripts gegenrechnen: aus den Eckpunkten, die
    # sechskant() erzeugt, muessen Schluesselweite und Eckenweite wieder
    # herauskommen — sonst passt keine echte Mutter in die Tasche.
    sw3 = w('m3_mutter_sw') + w('tasche_spiel')
    r = sw3 / math.sqrt(3.0)
    ecken = [(r * math.cos(math.radians(i * 60.0)),
              r * math.sin(math.radians(i * 60.0))) for i in range(6)]
    p.ok('Sechskant-Formel: Schluesselweite trifft',
         abs(2 * max(abs(v) for _, v in ecken) - sw3), 0.001, '<=')
    p.ok('Sechskant-Formel: Eckenweite trifft',
         abs(2 * max(abs(u) for u, _ in ecken) - 2 * eck3), 0.001, '<=')
    p.info('Klemmlaenge Platte + Ruecken bis zur Mutter', L['winkel_klemm'])
    p.ok('Schraube M3x{:.0f} erreicht die Mutter (mit Ø9-Scheibe)'.format(
             L['winkel_schraube']),
         L['winkel_schraube'] - (L['winkel_klemm'] + 0.8), 0.5)
    p.ok('Ausrichtspiel der schwimmenden Verschraubung',
         w('m3_uebermass') - w('m3_durchgang'), 0.8)
    # Der Winkel liegt nur mit dem Ruecken an der Lasche an (Y). Zur Seite
    # braucht er Luft zum Auflagepad, sonst kann er beim Durchfahren nicht
    # dorthin schwimmen, wo die Spindel ihn haben will. Schwimmweg je
    # Richtung: Schraube im Ø4,6 der Lasche plus im Ø3,4 des Ruecken.
    schwimm = ((w('m3_uebermass') - M3_SCHAFT_D) / 2
               + (w('m3_durchgang') - M3_SCHAFT_D) / 2)
    p.info('Schwimmweg des Winkels je Richtung', schwimm)
    p.ok('Luft Ruecken -> Auflagepad deckt den Schwimmweg',
         (w('winkel_x_links') - w('pad_breite') / 2) - schwimm, 0.0)
    p.ok('Grosse Scheibe deckt das Uebermass',
         SCHEIBE_GROSS - w('m3_uebermass'), 2.0)
    # Gegenstueck an der Lasche der Schlittenplatte: Ø4,6-Bohrung und die
    # grosse Scheibe darauf muessen in die Lasche passen (sie endet mit dem
    # Winkel bei winkel_x_rechts).
    p.ok('Ø4,6-Bohrung bleibt in der Lasche',
         w('winkel_x_rechts')
         - (L['winkel_schraube_x'][1] + w('m3_uebermass') / 2), 2.0)
    p.ok('grosse Scheibe liegt ganz auf der Lasche',
         w('winkel_x_rechts')
         - (L['winkel_schraube_x'][1] + SCHEIBE_GROSS / 2), 0.0)
    p.ok('Winkel laeuft am Z-Wagen vorbei',
         w('winkel_x_links') - w('z_wagen_breite') / 2, 3.0)
    p.ok('Regal laeuft an der Saeulenrippe vorbei',
         L['regal_y0'] - (L['traeger_y1'] + w('saeule_rippe_tiefe')),
         w('luft_bau'))
    # Drucklage: Regaloberseite aufs Bett, der Ruecken haengt darunter. Das
    # geht nur ohne Stuetzen, wenn sein Grundriss im Regal liegt.
    p.ja('Drucklage: Ruecken steht vollstaendig im Regalgrundriss',
         (L['winkel_y0'] >= L['regal_y0'] - 1e-9
          and L['schlitten_y1'] <= L['regal_y1'] + 1e-9),
         '   Ruecken Y {:.1f}..{:.1f}, Regal Y {:.1f}..{:.1f}'.format(
             L['winkel_y0'], L['schlitten_y1'], L['regal_y0'], L['regal_y1']))

    # --- Antrieb: Garnitur, Verfahrweg, Moment ----------------------------
    p.info('Garnitur: Oberkante ueber der Wagenmitte', L['garnitur_z1_rel'])
    p.ja('die Garnitur bindet den Verfahrweg nach oben',
         L['zc_bindend'] == 'Antriebsmutter gegen Kupplung',
         '   (bindend ist: {})'.format(L['zc_bindend']))
    p.info('Reserve im Arbeitsweg ueber dem Werkstueckbedarf',
           L['z_arbeit'] - w('werkstueck_max'))
    p.info('benoetigte Spindellaenge', L['spindel_laenge'])
    p.ok('Zuschnitt ({:.0f} mm) deckt die benoetigte Laenge'.format(
             w('spindel_zuschnitt')),
         w('spindel_zuschnitt') - L['spindel_laenge'], 0.0)
    p.ok('Zuschnitt geht aus der bestellten Laenge hervor',
         w('spindel_bestellt') - w('spindel_zuschnitt'), 0.0)
    p.ok('gekuerzte Spindel laesst das dickste Werkstueck zu',
         L['werkstueck_frei_ist'] - w('werkstueck_max'), 0.0)
    # Warum ueberhaupt kuerzen: ungekuerzt haengt das untere Ende tiefer als
    # Plattenunterkante und Schienenende und wird selbst zur Grenze.
    p.info('Werkstueckhoehe ungekuerzt (deshalb kuerzen)',
           L['werkstueck_frei_lang'])
    # Antriebsmoment und Selbsthemmung: die Frage, ob die Klemmnabe auf den
    # Gewindespitzen durchrutscht, entscheidet sich hier und nicht am Gefuehl.
    masse_z = 0.510                                  # bewegte Masse an Z, kg
    steigung = 0.002                                 # Tr8x2: 2 mm
    # Federkraft der Garnitur: 25 N als Obergrenze angenommen, empfohlen
    # sind 5..10 N (toolhead-z.md, "Wie stark die Feder vorspannen?"). Die
    # Feder drueckt beide Mutternhaelften an, daher 2 * feder im Moment.
    eta, feder = 0.25, 25.0                          # Wirkungsgrad, Federkraft
    moment = lambda kraft: kraft * steigung / (2 * math.pi * eta)
    p.info('Drehmoment zum Heben', moment(masse_z * 9.81) * 1000, 'mNm')
    p.info('Federkraft der Garnitur (Annahme; empfohlen 5..10 N)', feder, 'N')
    p.info('groesste Federkraft, die die Klemmnabe noch treibt',
           (0.120 - moment(masse_z * 9.81)) / moment(2.0), 'N')
    p.info('Drehmoment durch die Federvorspannung der Garnitur',
           moment(2 * feder) * 1000, 'mNm')
    p.ok('Klemmnabe uebertraegt das Betriebsmoment (konservativ 120 mNm)',
         120.0 - (moment(masse_z * 9.81) + moment(2 * feder)) * 1000, 0.0,
         '>=', 'mNm')
    p.ok('NEMA 17 (400 mNm Haltemoment) hat Reserve',
         400.0 - (moment(masse_z * 9.81) + moment(2 * feder)) * 1000, 200.0,
         '>=', 'mNm')
    # Steigungswinkel am Flankendurchmesser d2 = d - 0,5 * P.
    d2 = w('spindel_d') - 0.5 * steigung * 1000
    winkel = math.degrees(math.atan(steigung * 1000 / (math.pi * d2)))
    p.ok('Spindel selbsthemmend (Steigungswinkel unter dem Reibwinkel)',
         6.0 - winkel, 0.0, '>=', 'Grad')
    p.info('Steigungswinkel Tr8x2 am Flankendurchmesser', winkel, 'Grad')
    p.info('Aufloesung bei 1/16-Schritt', steigung * 1000 / 3200.0 * 1000,
           'um')

    # --- Braucht die Spindel oben ein Lager? -------------------------------
    # Die Frage entscheidet sich an drei Groessen: Axiallast im Motorlager,
    # kritische Biegedrehzahl und Seitenkraft aus einem Winkelfehler. Ein
    # Gleit- oder Kugellager kaeme ausserdem nur auf die Gewindespitzen —
    # die Spindel hat keinen angedrehten Zapfen.
    rho, e_stahl = 7850.0, 2.0e11          # Stahl: kg/m3, N/m2
    d2_m = d2 / 1000.0                     # Flankendurchmesser in m
    flaeche = math.pi / 4 * d2_m ** 2
    m_lang = rho * flaeche                 # Masse je Meter
    m_spindel = m_lang * w('spindel_bestellt') / 1000.0
    p.info('Masse der Spindel ({:.0f} mm Stahl)'.format(w('spindel_bestellt')),
           m_spindel * 1000, 'g')
    # Der Motor haelt die Spindel axial: an seinem Lager haengt der ganze
    # Z-Schlitten plus die Spindel selbst.
    p.ok('Axiallast im Motorlager (NEMA17 Datenblatt typ. 10 N)',
         10.0 - (masse_z + m_spindel) * 9.81, 0.0, '>=', 'N')
    # Kritische Biegedrehzahl der laengsten freien Laenge (Kupplung bis
    # Mutter in der tiefsten Stellung), gelenkig/gelenkig und damit
    # konservativ gerechnet.
    l_frei = (L['kupplung_z0'] - (L['zc_min'] + L['regal_z1_rel'])) / 1000.0
    traegheit = math.pi * d2_m ** 4 / 64.0
    n_krit = 60.0 / (2 * math.pi) * (math.pi / l_frei) ** 2 \
        * math.sqrt(e_stahl * traegheit / m_lang)
    z_vorschub = 10.0                      # mm/s, schnell fuer eine Z-Achse
    n_betrieb = z_vorschub / (steigung * 1000) * 60.0
    p.info('freie Spindellaenge Kupplung -> Mutter', l_frei * 1000)
    p.info('Betriebsdrehzahl bei {:.0f} mm/s'.format(z_vorschub),
           n_betrieb, '1/min')
    p.ok('kritische Biegedrehzahl mit Faktor 10 ueber Betrieb',
         n_krit - 10 * n_betrieb, 0.0, '>=', '1/min')
    p.info('kritische Biegedrehzahl', n_krit, '1/min')
    # Was oben wirklich zaehlt, ist nicht ein Lager, sondern der Winkelfehler
    # der Spindelachse: er schiebt die Mutter ueber den Verfahrweg seitlich
    # und stuetzt sich auf der Linearfuehrung ab. Die schwimmende
    # Verschraubung nimmt nur den parallelen Versatz auf, nicht den Winkel.
    drift = L['z_weg'] * math.tan(math.radians(0.2)) / 1000.0
    p.info('Seitenkraft auf die Fuehrung bei 0,2 Grad Winkelfehler',
           3 * e_stahl * traegheit * drift / l_frei ** 3, 'N')

    # --- Wie fein kann die Achse ueberhaupt stehen? -----------------------
    # Die Frage "A4988 (max. 1/16) oder TMC (bis 1/256)?" entscheidet sich
    # hier: der Rotor rueckt erst weiter, wenn das Moment die Reibung
    # ueberwindet (T = T_halt * sin(elektrischer Winkel), 90 el. Grad = ein
    # Vollschritt = 1,8 mech. Grad). Unterhalb dieser Totzone ist ein
    # feinerer Mikroschritt nur eine Zahl im Controller.
    m_halt = 0.400                                   # NEMA 17 Haltemoment, Nm
    m_reib = moment(masse_z * 9.81) + moment(2 * feder)
    winkel_el = math.degrees(math.asin(min(1.0, m_reib / m_halt)))
    totzone = winkel_el / 90.0 * 1.8 / 360.0 * steigung * 1e6
    mikroschritt = steigung * 1e6 / 3200.0           # 1/16 bei 200 Schritten
    p.info('Positions-Totzone aus Reibung + Federvorspannung', totzone, 'um')
    p.ja('1/16 Mikroschritt ist schon feiner als die Totzone',
         mikroschritt <= totzone,
         '   ({:.2f} um Schritt gegen {:.2f} um Totzone — feineres '
         'Microstepping bringt keine Genauigkeit, nur Laufruhe)'.format(
             mikroschritt, totzone))

    p.titel('8) Schlittenplatte und Laser (Konzept aus ToolheadGrundplatte)')
    p.ok('Platte deckt das Laserlochbild quer',
         w('schlitten_breite_l')
         - (w('laser_loch_quer') / 2 + w('laser_loch_d') / 2), 3.0)
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
         (lq - SCHEIBE_NORM / 2) - w('rippe_mitte_breite') / 2, 0.5)
    p.ok('Scheibe der Laserschraube passt neben die Seitenrippe',
         w('rippe_seite_innen') - (lq + SCHEIBE_NORM / 2), 0.5)
    # Rundloch statt Langloch: die Lochbildtoleranz kommt jetzt allein aus dem
    # Uebermass Ø4,0 auf Schaft Ø3 — beide Loecher koennen gegenlaeufig wandern.
    laser_tol = w('laser_loch_d') - M3_SCHAFT_D
    p.ok('Lochbildtoleranz deckt den Schrumpf ueber die Hoehe',
         laser_tol, 0.6)
    p.ok('Kopf kann nicht durch das Loch rutschen',
         M3_KOPF_D - w('laser_loch_d'), 1.0)
    p.ok('Normale Scheibe deckt das Laserloch',
         SCHEIBE_NORM - w('laser_loch_d'), 2.0)
    p.info('Lochbild deckt ab: {:.1f}-{:.1f} hoch, {:.1f}-{:.1f} quer'.format(
        w('laser_loch_hoch') - laser_tol, w('laser_loch_hoch') + laser_tol,
        w('laser_loch_quer') - laser_tol, w('laser_loch_quer') + laser_tol))
    for hoch, quer in LASER_MESSUNGEN:
        drin = (abs(hoch - w('laser_loch_hoch')) <= laser_tol
                and abs(quer - w('laser_loch_quer')) <= laser_tol)
        p.info('frueher gemessen {:.1f} x {:.1f}: {}'.format(
            hoch, quer, 'noch abgedeckt' if drin else 'ausserhalb (ueberholt)'))
    p.ok('Laser haengt unter der Traegerplatte (tiefste Stellung)',
         w('traeger_z_unten') - (L['zc_min'] + L['laser_unten_rel']), 5.0)
    # Lochbilder von Z-Wagen und Laser liegen beide bei X = +-7,5 und duerfen
    # sich in Z nicht in die Quere kommen.
    r_sen, r_schl = w('m3_senkung') / 2, w('laser_loch_d') / 2
    r_frei, r_loch = w('kopf_freiraum') / 2, w('m3_durchgang') / 2
    for rel, name in ((L['laser_loch_oben_rel'], 'obere'),
                      (L['laser_loch_unten_rel'], 'untere')):
        for vz in (-w('z_wagen_loch_laengs') / 2, w('z_wagen_loch_laengs') / 2):
            p.ok('{} Laserreihe <-> Freibohrung Z-Wagen (Platte)'.format(name),
                 abs(rel - vz) - r_sen - r_schl, 1.5)
    # Seit der Laser tiefer haengt, liegt die obere Reihe UNTER dem Pad. Dann
    # entfaellt der Kopffreiraum ganz — sonst muss er geprueft werden.
    if L['laser_oben_im_pad']:
        p.ok('Kopffreiraum bleibt im Auflagepad',
             w('pad_breite') / 2 - (lq + w('kopf_freiraum') / 2), 1.5)
        p.ok('Kopffreiraum <-> Wagenbohrung im Pad',
             abs(L['laser_loch_oben_rel'] - w('z_wagen_loch_laengs') / 2)
             - r_frei - r_loch, 1.0)
        p.ok('Kopffreiraum nimmt Kopf und Scheibe auf',
             w('kopf_freiraum') - SCHEIBE_NORM, 0.5)
        p.ok('obere Laserreihe liegt im Pad (braucht den Freiraum)',
             w('pad_laenge') / 2 - abs(L['laser_loch_oben_rel']), 0.0, '>=')
        pad_rest = (w('pad_breite') * w('pad_laenge')
                    - 2 * 3.1416 * (w('kopf_freiraum') / 2) ** 2)
    else:
        p.info('obere Laserreihe liegt unter dem Pad — kein Kopffreiraum')
        # Kopf und Scheibe sitzen jetzt frei auf der Plattenrueckseite: das
        # ganze Langloch samt Scheibe muss unter dem Pad bleiben.
        p.ok('Langloch oben + Scheibe bleiben unter dem Pad',
             abs(L['laser_loch_oben_rel'] + L['langloch_auf_max'])
             - w('pad_laenge') / 2 - SCHEIBE_NORM / 2, 1.0)
        pad_rest = w('pad_breite') * w('pad_laenge')
    # Langloecher: Enden gegen Plattenkante und gegen die Wagen-Freibohrungen
    hub, r_schlitz = w('laser_langloch_hub'), w('laser_loch_d') / 2
    p.ok('Langloch unten bleibt in der Platte',
         (L['laser_loch_unten_rel'] - hub - r_schlitz)
         - L['schlitten_unten_rel'], 2.0, '>=')
    p.ok('Langloch oben bleibt in der Platte',
         L['schlitten_oben_rel']
         - (L['laser_loch_oben_rel'] + hub + r_schlitz), 2.0, '>=')
    for vz in (-w('z_wagen_loch_laengs') / 2, w('z_wagen_loch_laengs') / 2):
        p.ok('Langlochende <-> Freibohrung Z-Wagen',
             abs(L['laser_loch_oben_rel'] + hub - vz) - r_sen - r_schlitz, 1.5)
    # Die Schlittenplatte reicht 9,5 mm unter die Laserunterkante (sie muss
    # die untere Langlochreihe samt Hub tragen). In der tiefsten Stellung ist
    # sie damit das Teil, das dem Bett am naechsten kommt — die Grenze dafuer,
    # wie tief der Laser am Schlitten haengen darf.
    p.ok('Plattenunterkante bleibt in tiefster Stellung ueber dem Bett',
         L['platte_ueber_bett'], 3.0)
    p.ok('untere Laserreihe liegt ausserhalb des Pads',
         abs(L['laser_loch_unten_rel']) - w('pad_laenge') / 2 - SCHEIBE_NORM / 2,
         1.0)
    p.ok('Restauflage des Pads auf dem Wagen', pad_rest, 400.0, '>=', 'mm2')

    # Fokusfenster: die Langlochstellung ersetzt das Wissen um den genauen
    # Fokusabstand des Moduls. bett_abstand/werkstueck_max sind Maschinenmasse.
    p.info('Bezugsebene -> Bettoberflaeche (gemessen)', w('bett_abstand'))
    p.info('Linse ueber dem Bett, Lochmitte: {:.1f} bis {:.1f} mm'.format(
        L['linse_tief'], L['linse_hoch']))
    p.info('Langloch nutzbar: {:+.1f} bis {:+.1f} mm (oben bindet die '
           'Montage)'.format(L['langloch_ab_max'], L['langloch_auf_max']))
    for zeile in mod.fokus_zeilen(L, w):
        p.info(zeile.strip())
    f_max = (L['linse_hoch'] + L['langloch_auf_max']
             - w('werkstueck_max'))
    p.info('groesster Fokusabstand fuer {:.0f} mm Werkstueck'.format(
        w('werkstueck_max')), f_max)

    p.titel('9) Endschalter: Gabellichtschranke und Schaltfahne')
    p.info('Schaltpunkt (Strahlachse)', L['ls_strahl_z'])
    p.ok('Weg nach dem Schalten bis zur mechanischen Grenze',
         w('ls_ueberfahrt'), 5.0)
    p.ok('Fahne passt in den Gabelspalt (Luft je Seite)',
         (w('ls_schlitz') - w('ls_fahne_dicke')) / 2, 2.0)
    p.ok('Fahne deckt die Strahlhoehe ab (Tiefe quer zur Platine)',
         w('ls_fahne_tiefe'), 6.0)
    p.info('abgedeckte Strahlhoehe ueber der Platine: {:.1f} bis {:.1f} mm'
           .format(w('ls_fahne_luft_pcb'),
                   w('ls_fahne_luft_pcb') + w('ls_fahne_tiefe')))
    p.ok('Fahne bleibt vom Z-Wagen weg',
         -w('z_wagen_breite') / 2 - L['ls_fahne_x1'], w('luft_bau'))
    p.ok('Sockel bleibt vom Z-Wagen weg',
         -w('z_wagen_breite') / 2 - w('ls_sockel_x1'), w('luft_bau'))
    # Der Sockel ist nur so breit, wie er sein darf — also gilt fuer den
    # Einsatz dieselbe Rechnung wie am Schienensockel.
    p.ok('Wand um den Einsatz im Endschaltersockel',
         (w('ls_sockel_x1') - w('traeger_x_links') - w('insert_m3_d')) / 2, 2.0)
    p.ok('Material hinter dem Einsatz im Endschaltersockel',
         w('ls_sockel_hoehe') + w('traeger_dicke') - w('insert_m3_t'), 2.0)
    p.ok('Halter: Langloch bleibt im Flansch',
         (L['ls_schraub_z'][0] - w('ls_justage') - w('m3_durchgang') / 2)
         - L['ls_sockel_z0'], 2.0)
    p.ok('Halter: Platinenloecher liegen in der Wand',
         L['ls_wand_y1'] - (L['ls_pcb_loch_y'][-1] + w('ls_pcb_loch_d') / 2),
         1.0)
    # Diese Pruefung hat gefehlt: der Flansch stand in die untere Bohrung
    # hinein (0,9 mm), aufgefallen erst am gedruckten Teil.
    p.ok('Halter: untere Platinenbohrung frei vom Flansch',
         (L['ls_pcb_loch_y'][0] - w('ls_pcb_loch_d') / 2) - L['ls_flansch_y1'],
         1.5)
    # M2-Einsatz Ø3,2 x 2,5 in der 4-mm-Wand: Einpressbohrung Ø2,8 (0,4 mm
    # Untermass), dahinter Freibohrung — der Einsatz kann nicht durchrutschen.
    p.ok('Halter: Einpressbohrung tiefer als der M2-Einsatz',
         w('ls_pcb_loch_t') - 2.5, 0.4)
    p.ok('Halter: Absatz hinter dem M2-Einsatz',
         (w('ls_pcb_loch_d') - w('ls_pcb_frei_d')) / 2, 0.15)
    p.ok('Halter: Wand tiefer als die Einpressbohrung',
         w('ls_halter_dicke') - w('ls_pcb_loch_t'), 0.5)
    p.ok('Platine ragt nicht ueber den Halter hinaus (oben)',
         L['ls_halter_z1'] - L['ls_pcb_z1'], 2.0)
    # Der Sockel ist gedruckt und steht fest; der Halter nimmt den Versatz
    # des Schaltpunkts auf (Motoradapter). Seine Langloecher liegen auf den
    # Einsaetzen, die Platine sitzt ls_versatz hoeher.
    p.info('Platine im Halter hoeher als bis Rev. 29', L['ls_versatz'])
    p.ok('Halter: Langloecher liegen auf dem Sockel (unten)',
         (L['ls_schraub_z'][0] - w('ls_justage')) - L['ls_sockel_z0'], 2.0)
    p.ok('Halter: Langloecher liegen auf dem Sockel (oben)',
         L['ls_sockel_z1'] - (L['ls_schraub_z'][1] + w('ls_justage')), 2.0)
    p.info('Verstellbereich des Schaltpunkts', 2 * w('ls_justage'))
    p.info('Toolhead-Breite links (Halterwand)', L['ls_wand_x0'])
    p.ja('Halter bleibt im Schatten des X-Wagens',
         L['ls_wand_x0'] >= -w('x_wagen_laenge') / 2 - 3.0,
         '   (X-Wagen bis {:.1f} mm)'.format(-w('x_wagen_laenge') / 2))

    p.titel('10) Druckbarkeit (Bambu Lab A1, Bauraum 256)')
    for name, a, b in (
            ('Traegerplatte (mit Konsole)',
             w('traeger_x_kopf') - w('traeger_x_links'),
             L['motor_rippe_z1'] - w('traeger_z_unten')),
            ('Schlittenplatte', w('winkel_x_rechts') + w('schlitten_breite_l'),
             L['schlitten_oben_rel'] - L['schlitten_unten_rel']),
            ('Mutternwinkel', w('winkel_x_rechts') - w('winkel_x_links'),
             L['regal_z1_rel'] - L['winkel_unten_rel']),
            ('Endschalterhalter', w('ls_sockel_x1') - L['ls_wand_x0'],
             L['ls_halter_z1'] - L['ls_halter_z0']),
            ('Motoradapter', w('motor_flansch'), w('motor_flansch'))):
        p.ok('{}: groesste Kante'.format(name), max(a, b), 250.0, '<=')
    p.ok('Bruecke Schlittenplatte zwischen den Rippen',
         w('rippe_seite_innen') - w('rippe_mitte_breite') / 2, 25.0, '<=')

    p.titel('11) Stueckliste')
    for zeile in (
            'MGN9 Linearschiene {:.0f} mm + Wagen MGN9H'.format(
                w('z_schiene_laenge')),
            'NEMA 17, Koerper {:.0f} mm, Welle 5 mm'.format(w('motor_laenge')),
            'Tr8x2-Trapezgewindespindel {:.0f} mm, auf {:.0f} mm kuerzen '
            '({:.0f} mm gebraucht)'.format(
                w('spindel_bestellt'), w('spindel_zuschnitt'),
                L['spindel_laenge']),
            'Starre Klemmkupplung 5 -> 8 mm, {:.0f} mm lang '
            '(UniTak3D, seitliche Klemmschrauben)'.format(w('kupplung_l')),
            'Anti-Backlash-Garnitur Tr8x2 (Flanschmutter Ø{:.0f} + Feder + '
            'Gleitmutter)'.format(w('t8_flansch_d')),
            '4x M3x{:.0f} + 4x Messing-Einsatz M3 Ø5 (Garnitur -> Regal)'
            .format(L['flansch_schraube']),
            '4x M3x12 Zylinderkopf + Scheibe (Traegerplatte -> X-Wagen)',
            '{}x M3x10 Senkkopf DIN 7991 + {}x Messing-Einsatz M3 Ø5 '
            '(Z-Schiene -> Sockel)'
            .format(len(L['z_schiene_loecher']), len(L['z_schiene_loecher'])),
            '4x M3x{:.0f} Zylinderkopf   (Schlittenplatte -> Z-Wagen)'.format(
                L['z_wagen_schraube']),
            '4x M3x10 + 4x Scheibe DIN 125 (Laser -> Schlittenplatte)',
            '2x M3x{:.0f} + 2x M3-Mutter + 2x Scheibe DIN 9021 Ø9 '
            '(Mutternwinkel, schwimmend)'.format(L['winkel_schraube']),
            '4x M3x{:.0f} Zylinderkopf   (NEMA 17 -> Adapter -> Konsole, alle '
            'vier)'.format(L['motor_schraube']),
            '2x M3x12 + 2x Messing-Einsatz M3 Ø5 (Endschalterhalter -> Sockel)',
            '2x M2x6 + 2x Heat Insert M2 (Ø3,2 x 2,5) '
            '(Lichtschranke -> Halter)',
            'Gabellichtschranke LM393, Platine {:.0f} x {:.0f} mm, '
            'Schlitz {:.0f} mm'.format(w('ls_pcb_laenge'), w('ls_pcb_breite'),
                                       w('ls_schlitz'))):
        p.info(zeile)

    p.titel('12) Statische Pruefung der Schluessel im Skript')
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

    p.titel('13) Validierungsbericht des Fusion-Skripts')
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
