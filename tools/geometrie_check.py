#!/usr/bin/env python3
"""Rechnerische Pruefung der ToolheadGrundplatte — laeuft ohne Fusion.

Liest die Masse direkt aus fusion/ToolheadGrundplatte/ToolheadGrundplatte.py
(dict MASSE, einzige Quelle) und prueft Freigaenge, Materialstege,
Schraubenlaengen, Langloch-Toleranzen und Druckbarkeit.

    python3 tools/geometrie_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import ast
import os
import sys

SKRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                      'fusion', 'ToolheadGrundplatte', 'ToolheadGrundplatte.py')

# Kaufteil-Varianten, gegen die geprueft wird (hardware.md)
WAGEN_VARIANTEN = {
    'MGN9C': {'loch_laengs': 10.0, 'laenge': 28.9, 'gewinde_tiefe': 2.5},
    'MGN9H': {'loch_laengs': 16.0, 'laenge': 39.9, 'gewinde_tiefe': 2.5},
}
# Normteile (hardware.md): M3-Zylinderkopf DIN 912, Scheibe DIN 9021 (gross)
M3_KOPF_D = 5.5
M3_KOPF_H = 3.0
M3_SCHAFT_D = 3.0
SCHEIBE_D = 9.0
SCHEIBE_H = 0.8
INBUS_FREIRAUM_D = 6.0      # Platzbedarf fuer einen 2,5er Inbusschluessel
# Lochbild-Alternative aus hardware.md (eigene Messung am Laser, Status [?])
LASER_ALTERNATIVE = (40.0, 16.0)   # (hoch, quer)


def masse_laden(pfad):
    """Holt das dict MASSE per AST aus dem Fusion-Skript — ohne adsk-Import."""
    with open(pfad, encoding='utf-8') as f:
        baum = ast.parse(f.read())
    for knoten in baum.body:
        if isinstance(knoten, ast.Assign):
            for ziel in knoten.targets:
                if isinstance(ziel, ast.Name) and ziel.id == 'MASSE':
                    return {k: v[0] for k, v in
                            ast.literal_eval(knoten.value).items()}
    raise SystemExit('MASSE nicht gefunden in ' + pfad)


class Pruefung:
    def __init__(self):
        self.zeilen = []
        self.fehler = 0

    def ok(self, text, ist, soll, vergleich='>=', einheit='mm'):
        bestanden = {'>=': ist >= soll, '<=': ist <= soll,
                     '>': ist > soll, '<': ist < soll}[vergleich]
        if not bestanden:
            self.fehler += 1
        self.zeilen.append('  [{}] {:<52} {:>7.2f} {} {} {:.2f} {}'.format(
            'OK ' if bestanden else 'FEHL', text, ist, einheit,
            vergleich, soll, einheit))
        return bestanden

    def info(self, text, wert=None, einheit='mm'):
        if wert is None:
            self.zeilen.append('  ---- ' + text)
        else:
            self.zeilen.append('  ---- {:<52} {:>7.2f} {}'.format(
                text, wert, einheit))

    def titel(self, text):
        self.zeilen.append('')
        self.zeilen.append(text)

    def bericht(self):
        print('\n'.join(self.zeilen))
        print()
        if self.fehler:
            print('{} Pruefung(en) FEHLGESCHLAGEN'.format(self.fehler))
        else:
            print('alle Pruefungen bestanden')
        return 1 if self.fehler else 0


def bericht_rendern():
    """Importiert das Fusion-Skript mit gestubbtem adsk-Modul und rendert die
    Hinweiszeilen des Validierungsberichts. Prueft damit, dass alle
    Format-Strings des Berichts aufgehen — das Skript nutzt adsk erst
    innerhalb der Funktionen, der Import geht also ohne Fusion durch."""
    import importlib.util
    import types
    for name in ('adsk', 'adsk.core', 'adsk.fusion'):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules['adsk'].core = sys.modules['adsk.core']
    sys.modules['adsk'].fusion = sys.modules['adsk.fusion']
    spec = importlib.util.spec_from_file_location('toolhead_grundplatte', SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul.hinweise_bauen([])


def main():
    m = masse_laden(SKRIPT)
    p = Pruefung()

    # Abgeleitete Kanten (alles ab Mitte / ab Wagen-Stirnflaeche)
    platte_x = m['platte_breite'] / 2.0          # 17,5
    platte_y = m['platte_hoehe'] / 2.0           # 26,0
    pad_x = m['pad_breite'] / 2.0                # 14,0
    pad_y = m['pad_laenge'] / 2.0                # 13,0
    rippe_m_x = m['rippe_mitte_breite'] / 2.0    # 2,5
    rippe_s_x = m['rippe_seite_innen']           # 13,0
    wagen_x = m['wagen_breite'] / 2.0            # 10,0

    loch_w_x = m['wagen_loch_quer'] / 2.0        # 7,5
    loch_w_y = m['wagen_loch_laengs'] / 2.0      # 8,0
    loch_l_x = m['laser_loch_quer'] / 2.0        # 7,5
    loch_l_y = m['laser_loch_hoch'] / 2.0        # 19,5

    r_durchgang = m['m3_durchgang'] / 2.0        # 1,70
    r_senkung = m['m3_senkung'] / 2.0            # 3,25
    r_kopf = M3_KOPF_D / 2.0                     # 2,75
    r_scheibe = SCHEIBE_D / 2.0                  # 4,50

    # Langloch: halber Versatz + Radius nach jeder Seite
    schlitz_r = m['schlitz_breite'] / 2.0
    schlitz_hx = m['schlitz_verstellweg'] / 2.0 + schlitz_r
    schlitz_x0, schlitz_x1 = loch_l_x - schlitz_hx, loch_l_x + schlitz_hx
    schlitz_y0, schlitz_y1 = loch_l_y - schlitz_r, loch_l_y + schlitz_r

    laserflaeche = m['pad_hoehe'] + m['dicke_platte']

    p.titel('1) Masskette in Modell-Z (ab Wagen-Stirnflaeche = 0)')
    p.info('Auflageebene der Schiene (Flaeche Z-Platte)', -m['wagen_hoehe'])
    p.info('Oberkante Schiene', -m['wagen_hoehe'] + m['schiene_hoehe'])
    p.info('Rueckseite Platte (= Pad-Hoehe)', m['pad_hoehe'])
    p.info('Anschraubflaeche Laser', laserflaeche)
    p.info('Strahlachse ab Wagen-Stirnflaeche',
           laserflaeche + m['laser_tiefe'] / 2.0)
    p.info('Strahlachse ab Schienen-Auflageebene',
           laserflaeche + m['laser_tiefe'] / 2.0 + m['wagen_hoehe'])

    p.titel('2) Freigang zur Fuehrung (der Fehler beim ersten Versuch)')
    p.ok('Luft Teilrueckseite -> Oberkante Schiene',
         m['wagen_hoehe'] - m['schiene_hoehe'], 1.0)
    p.ok('Luft Teilrueckseite -> Flaeche der Z-Platte', m['wagen_hoehe'], 5.0)
    p.ok('Seitenrippe innen ausserhalb des Wagens', rippe_s_x - wagen_x, 0.5)
    p.ok('Laser laeuft vor der Schiene vorbei (Anschraubflaeche > 0)',
         laserflaeche, 0.0, '>')

    p.titel('3) Materialstege um die Bohrungen')
    p.ok('Pad-Steg quer um Wagenbohrung', pad_x - (loch_w_x + r_durchgang), 2.0)
    p.ok('Pad-Steg hoch um Wagenbohrung', pad_y - (loch_w_y + r_durchgang), 2.0)
    p.ok('Platten-Steg quer um Freibohrung',
         platte_x - (loch_w_x + r_senkung), 2.0)
    p.ok('Abstand Freibohrung -> Langloch', schlitz_y0 - (loch_w_y + r_senkung), 1.5)
    p.ok('Platten-Steg quer aussen am Langloch', platte_x - schlitz_x1, 3.0)
    p.ok('Platten-Steg hoch aussen am Langloch', platte_y - schlitz_y1, 2.5)

    p.titel('4) Schraubenkopf + Scheibe der Laserverschraubung')
    p.info('Langloch quer von/bis (ab Mitte)', schlitz_x0)
    p.info('Langloch quer bis', schlitz_x1)
    p.ok('Scheibe passt zwischen Mittel- und Seitenrippe',
         (rippe_s_x - rippe_m_x) - SCHEIBE_D, 0.3)
    p.ok('Scheibenauflage quer, innen', schlitz_x0 - (loch_l_x - r_scheibe), 1.0)
    p.ok('Scheibenauflage quer, aussen', (loch_l_x + r_scheibe) - schlitz_x1, 1.0)
    p.ok('Scheibenauflage hoch', schlitz_y0 - (loch_l_y - r_scheibe), 1.0)
    p.ok('Scheibe deckt das Langloch in der Laenge',
         SCHEIBE_D - (schlitz_x1 - schlitz_x0), 1.5)
    p.ok('Kopf kann nicht ins Langloch rutschen (Breite)',
         M3_KOPF_D - m['schlitz_breite'], 0.5)
    p.ok('Kopf+Scheibe bleiben hinter der Wagenflaeche',
         m['pad_hoehe'] - (M3_KOPF_H + SCHEIBE_H), 1.0)
    p.ok('Scheibe liegt neben dem Auflagepad',
         (loch_l_y - r_scheibe) - pad_y, 1.0)

    p.titel('5) Wagenverschraubung: Freibohrung und Schraubenlaenge')
    p.ok('Freibohrung gibt den Inbus frei', m['m3_senkung'], INBUS_FREIRAUM_D)
    p.ok('Kopf versinkt unter der Laser-Anschraubflaeche',
         m['dicke_platte'] - M3_KOPF_H, 1.5)
    for name, v in sorted(WAGEN_VARIANTEN.items()):
        laenge = 8.0                       # empfohlene M3x8
        eingriff = laenge - m['pad_hoehe']
        p.info('{}: Gewindeeingriff mit M3x{:.0f}'.format(name, laenge), eingriff)
        p.ok('{}: Eingriff traegt'.format(name), eingriff, 1.5)
        p.ok('{}: Schraube setzt nicht auf'.format(name),
             eingriff, v['gewinde_tiefe'], '<=')
        p.ok('{}: Pad liegt ganz auf dem Wagen'.format(name),
             v['laenge'] / 2.0 - pad_y, 0.0, '>=')

    p.titel('6) Werkzeugzugang zu den Laserschrauben (nur Komfort)')
    for name, v in sorted(WAGEN_VARIANTEN.items()):
        frei = loch_l_y - v['laenge'] / 2.0 - r_kopf
        if frei >= 0:
            p.info('{}: Kopf liegt frei neben dem Wagen (+{:.1f})'.format(
                name, frei))
        else:
            p.info('{}: Kopf liegt ueber dem Wagen -> erst Laser, dann '
                   'Platte montieren'.format(name))

    p.titel('7) Langloch-Toleranz gegen das unsichere Lochbild [?]')
    quer_tol = m['schlitz_verstellweg'] + m['schlitz_breite'] - M3_SCHAFT_D
    hoch_tol = m['schlitz_breite'] - M3_SCHAFT_D
    p.info('abgedeckt quer von', m['laser_loch_quer'] - quer_tol)
    p.info('abgedeckt quer bis', m['laser_loch_quer'] + quer_tol)
    p.info('abgedeckt hoch von', m['laser_loch_hoch'] - hoch_tol)
    p.info('abgedeckt hoch bis', m['laser_loch_hoch'] + hoch_tol)
    alt_hoch, alt_quer = LASER_ALTERNATIVE
    p.ok('hardware.md-Variante {:.0f} quer liegt im Verstellbereich'.format(
        alt_quer), quer_tol - abs(alt_quer - m['laser_loch_quer']), 0.0, '>=')
    p.ok('hardware.md-Variante {:.0f} hoch liegt im Verstellbereich'.format(
        alt_hoch), hoch_tol - abs(alt_hoch - m['laser_loch_hoch']), 0.0, '>=')

    p.titel('8) Druckbarkeit (Bambu Lab A1, 0,4er Duese)')
    p.ok('Bruecke Platte zwischen den Rippen', rippe_s_x - rippe_m_x, 25.0, '<=')
    p.ok('Pad ueberlappt die Seitenrippe (ein Koerper)', pad_x - rippe_s_x, 0.0, '>')
    p.ok('Mittelrippe traegt mehr als eine Bahn', m['rippe_mitte_breite'], 1.7)
    p.ok('Seitenrippe traegt mehr als eine Bahn', platte_x - rippe_s_x, 1.7)
    p.ok('Erste Lage passt auf das Bett (Breite)', m['platte_breite'], 250.0, '<=')
    p.ok('Erste Lage passt auf das Bett (Hoehe)', m['platte_hoehe'], 250.0, '<=')
    p.ok('Fussfase gesetzt (gegen Elefantenfuss)', m['fase_fuss'], 0.3)

    p.titel('9) Laser sitzt vollflaechig auf')
    p.ok('Platte mindestens so breit wie der Laser',
         m['platte_breite'] - m['laser_breite'], 0.0, '>=')
    p.ok('Platte deckt das Lochbild hoch ab',
         m['platte_hoehe'] - (m['laser_loch_hoch'] + m['schlitz_breite']), 6.0)

    p.titel('10) Massenabschaetzung PETG (1,27 g/cm3, 100% Fuellung)')
    flaeche_rueck = (m['pad_breite'] * m['pad_laenge']
                     + m['rippe_mitte_breite'] * (m['platte_hoehe'] - m['pad_laenge'])
                     + 2 * (platte_x - rippe_s_x) * (m['platte_hoehe'] - m['pad_laenge']))
    vol = (flaeche_rueck * m['pad_hoehe']
           + m['platte_breite'] * m['platte_hoehe'] * m['dicke_platte']
           - 4 * 3.1416 * r_senkung ** 2 * m['dicke_platte']
           - 4 * 3.1416 * r_durchgang ** 2 * m['pad_hoehe'])
    p.info('Volumen', vol / 1000.0, 'cm3')
    p.info('Masse (voll)', vol / 1000.0 * 1.27, 'g')

    p.titel('11) Validierungsbericht des Fusion-Skripts')
    try:
        for zeile in bericht_rendern():
            p.info(zeile if zeile else '.')
        p.ok('Bericht rendert ohne Fehler', 1.0, 1.0, '>=', '')
    except Exception as exc:                      # Format-String kaputt
        p.info('Bericht NICHT renderbar: {}'.format(exc))
        p.ok('Bericht rendert ohne Fehler', 0.0, 1.0, '>=', '')

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
