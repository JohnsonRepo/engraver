#!/usr/bin/env python3
"""Bauraeume der Baugruppe ToolheadZ als achsparallele Quader.

Gemeinsame Quelle fuer die Kollisionspruefung (toolhead_check.py) und die
Layout-Zeichnung (layout_zeichnen.py). Die Masse kommen aus dem Fusion-Skript,
damit Pruefung, Zeichnung und Geometrie nicht auseinanderlaufen koennen.
"""

import importlib.util
import os
import sys
import types

SKRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                      'fusion', 'ToolheadZ', 'ToolheadZ.py')
PORTAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                      'fusion', 'Portal', 'Portal.py')


def modul_laden(pfad=SKRIPT, name='toolhead_z'):
    """Importiert das Fusion-Skript ohne Fusion: adsk wird nur innerhalb der
    Funktionen benutzt, der Modulimport laeuft also mit einem Stub durch."""
    for n in ('adsk', 'adsk.core', 'adsk.fusion'):
        sys.modules.setdefault(n, types.ModuleType(n))
    sys.modules['adsk'].core = sys.modules['adsk.core']
    sys.modules['adsk'].fusion = sys.modules['adsk.fusion']
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class Quader:
    """Achsparalleler Bauraum in Maschinenkoordinaten (mm)."""

    def __init__(self, name, x0, x1, y0, y1, z0, z1, art='druck'):
        self.name = name
        self.art = art                      # druck | kaufteil | fuehrung
        self.x = (min(x0, x1), max(x0, x1))
        self.y = (min(y0, y1), max(y0, y1))
        self.z = (min(z0, z1), max(z0, z1))

    def verschoben(self, dz, dx=0.0):
        return Quader(self.name, self.x[0] + dx, self.x[1] + dx, self.y[0],
                      self.y[1], self.z[0] + dz, self.z[1] + dz, self.art)

    def abstand(self, other):
        """Kleinster Achsabstand; >= 0 heisst: in mindestens einer Achse
        getrennt, also keine Durchdringung."""
        return max(max(a[0] - b[1], b[0] - a[1])
                   for a, b in ((self.x, other.x), (self.y, other.y),
                                (self.z, other.z)))


def zugang_frei(x, y, r, z_von, boxen, ausser=()):
    """Ist der senkrechte Korridor mit Radius r ab z_von nach unten frei?
    Liefert den Namen des ersten blockierenden Quaders oder None. Geprueft
    werden nur feste Teile — bewegte kann man vor der Montage wegfahren.

    Genau diese Pruefung fehlte, als die hintere Schraubenreihe des NEMA 17
    ueber dem Querschnitt der Traegerplatte landete.
    """
    for q in boxen:
        if q.name in ausser or q.z[0] >= z_von:
            continue
        if (q.x[0] < x + r and x - r < q.x[1]
                and q.y[0] < y + r and y - r < q.y[1]):
            return q.name
    return None


def bauraeume(w, L):
    """(feste, bewegte, erlaubte_paare). Die bewegten Quader stehen relativ
    zur Wagenmitte zc = 0 und werden mit .verschoben(zc) positioniert."""
    sx, sy = w('spindel_x'), w('spindel_y')
    # Fuer die Kollisionspruefung zaehlt das Kaufteil, nicht die Bohrung:
    # die Spindel ist Ø8 (Gewindeaussendurchmesser).
    r_kup, r_spi = w('kupplung_d') / 2.0, w('spindel_d') / 2.0

    feste = [
        # Kein 20 x 20: eine Wand ueber die ganze Hoehe der Traegerplatte.
        # Sie steht fuer "hinter dem Toolhead ist das Portal" und haelt
        # Werkzeugkorridore von hinten ehrlich. Das echte Rohr (Z -10..+10)
        # steht in tools/portal_check.py.
        Quader('Portalprofil 2020', w('traeger_x_links') - 10,
               w('traeger_x_kopf') + 10, L['portal_y'] - 20, L['portal_y'],
               w('traeger_z_unten'), L['konsole_z1'], 'kaufteil'),
        Quader('X-Schiene MGN15', w('traeger_x_links') - 10,
               w('traeger_x_kopf') + 10, L['portal_y'], L['x_schiene_y'],
               -w('x_schiene_hoehe') / 2 - 2.5,
               w('x_schiene_hoehe') / 2 + 2.5, 'fuehrung'),
        Quader('X-Wagen MGN15H', -w('x_wagen_laenge') / 2,
               w('x_wagen_laenge') / 2, L['portal_y'], L['traeger_y0'],
               -w('x_wagen_breite') / 2, w('x_wagen_breite') / 2, 'fuehrung'),
        Quader('Traegerplatte Hauptsaeule', w('traeger_x_links'),
               w('traeger_x_rechts'), L['traeger_y0'], L['traeger_y1'],
               w('traeger_z_unten'), w('traeger_kopf_unten')),
        Quader('Traegerplatte Kopf', w('traeger_x_links'), w('traeger_x_kopf'),
               L['traeger_y0'], L['traeger_y1'], w('traeger_kopf_unten'),
               L['konsole_z0']),
        Quader('Schienensockel', -w('sockel_breite') / 2, w('sockel_breite') / 2,
               L['traeger_y1'], L['sockel_y1'], L['z_schiene_z0'],
               L['z_schiene_z1']),
        # Versteifungsrippen der Saeule — angeformt, aber eigene Quader, weil
        # sie in den Bauraum vor der Platte ragen.
        Quader('Saeulenrippe links', L['saeule_rippe_x'][0][0],
               L['saeule_rippe_x'][0][1], L['traeger_y1'],
               L['traeger_y1'] + w('saeule_rippe_tiefe'),
               w('traeger_z_unten'), L['konsole_z0']),
        Quader('Saeulenrippe rechts', L['saeule_rippe_x'][1][0],
               L['saeule_rippe_x'][1][1], L['traeger_y1'],
               L['traeger_y1'] + w('saeule_rippe_tiefe'),
               w('traeger_z_unten'), L['konsole_z0']),
        Quader('Z-Schiene MGN9', -w('z_schiene_breite') / 2,
               w('z_schiene_breite') / 2, L['sockel_y1'], L['z_schiene_y1'],
               L['z_schiene_z0'], L['z_schiene_z1'], 'fuehrung'),
        # Konsole und Fuehrungsrippen sind an die Traegerplatte angeformt
        Quader('Motorkonsole', L['konsole_x0'], L['konsole_x1'], 0.0,
               w('konsole_y_vorn'), L['konsole_z0'], L['konsole_z1']),
        Quader('Fuehrungsrippe links', L['motor_rippe_x'][0][0],
               L['motor_rippe_x'][0][1], 0.0, L['motor_rippe_y1'],
               L['konsole_z1'], L['motor_rippe_z1']),
        Quader('Fuehrungsrippe rechts', L['motor_rippe_x'][1][0],
               L['motor_rippe_x'][1][1], 0.0, L['motor_rippe_y1'],
               L['konsole_z1'], L['motor_rippe_z1']),
        # Distanzplatte zwischen Konsole und Motor, eigenes Druckteil
        Quader('Motoradapter', sx - w('motor_flansch') / 2,
               sx + w('motor_flansch') / 2, sy - w('motor_flansch') / 2,
               sy + w('motor_flansch') / 2, L['adapter_z0'], L['adapter_z1']),
        # Endschalter: Sockel an der Platte, Halter (Flansch + Wand) und die
        # Platine der Gabellichtschranke.
        Quader('Endschaltersockel', w('traeger_x_links'), w('ls_sockel_x1'),
               L['traeger_y1'], L['ls_sockel_y1'],
               L['ls_sockel_z0'], L['ls_sockel_z1']),
        Quader('Halter Flansch', L['ls_wand_x0'], w('ls_sockel_x1'),
               L['ls_sockel_y1'], L['ls_flansch_y1'],
               L['ls_halter_z0'], L['ls_halter_z1']),
        Quader('Halter Wand', L['ls_wand_x0'], L['ls_wand_x1'],
               L['ls_sockel_y1'], L['ls_wand_y1'],
               L['ls_halter_z0'], L['ls_halter_z1']),
        Quader('Lichtschranke', L['ls_wand_x1'], L['ls_pcb_x1'],
               L['ls_pcb_y0'], L['ls_pcb_y1'],
               L['ls_pcb_z0'], L['ls_pcb_z1'], 'kaufteil'),
        # Die Gabel steht auf der Platine nach +X: zwei Arme, dazwischen der
        # Schlitz mit seinem Boden. Ihr Grundriss liegt ueber Platte,
        # Seitenrippe und Pad — nur das Blatt der Schaltfahne darf hinein.
        Quader('Gabel hinten', L['ls_pcb_x1'], L['ls_gabel_x1'],
               L['ls_gabel_y'][0], L['ls_schlitz_y'][0],
               L['ls_gabel_z0'], L['ls_gabel_z1'], 'kaufteil'),
        Quader('Gabel vorn', L['ls_pcb_x1'], L['ls_gabel_x1'],
               L['ls_schlitz_y'][1], L['ls_gabel_y'][1],
               L['ls_gabel_z0'], L['ls_gabel_z1'], 'kaufteil'),
        Quader('Gabel Boden', L['ls_pcb_x1'], L['ls_boden_x'],
               L['ls_schlitz_y'][0], L['ls_schlitz_y'][1],
               L['ls_gabel_z0'], L['ls_gabel_z1'], 'kaufteil'),
        Quader('NEMA 17', sx - w('motor_flansch') / 2,
               sx + w('motor_flansch') / 2, sy - w('motor_flansch') / 2,
               sy + w('motor_flansch') / 2, L['motor_flansch_z'], L['motor_z1'],
               'kaufteil'),
        Quader('Kupplung', sx - r_kup, sx + r_kup, sy - r_kup, sy + r_kup,
               L['kupplung_z0'], L['kupplung_z1'], 'kaufteil'),
        # X-Riemenhalter (Rev. 33): hinten an der Traegerplatte, steht auf
        # der Flanke des X-Wagens. Den Riemen selbst, Motor und Umlenkung
        # prueft tools/portal_check.py — dort liegt das Portalrohr richtig
        # (20 x 20), nicht als die Wand, die es hier fuer den Werkzeug-
        # zugang von hinten darstellt.
        Quader('Riemenhalter', w('traeger_x_links'), w('traeger_x_rechts'),
               L['rh_y0'], L['rh_y1'], L['rh_z0'], L['rh_z1']),
        # Kettenhalter (Rev. 35): hinten an der Traegerplatte ueber dem
        # Riemenhalter, darauf das Anfangsstueck der X-Kette. Wanne, Kette
        # und Festpunkt prueft tools/portal_check.py (Abschnitt 17).
        Quader('Kettenhalter Fuss', *L['kh_x'], *L['kh_fuss_y'],
               L['kh_fuss_z0'], L['kh_auflage_z1']),
        Quader('Kettenhalter Auflage', *L['kh_x'], L['kh_y0'],
               L['traeger_y0'], L['kh_auflage_z0'], L['kh_auflage_z1']),
        Quader('Kettenhalter Leiste hinten', *L['kh_x'],
               *L['kh_leiste_hinten_y'], *L['kh_leiste_z']),
        Quader('Kettenhalter Leiste vorn', *L['kh_x'],
               *L['kh_leiste_vorn_y'], *L['kh_leiste_z']),
        Quader('Kette Anfangsstueck', *L['kh_endstueck_x'], *L['kh_kette_y'],
               *L['kh_endstueck_z']),
        # Die Spindel in ihrer gekuerzten Laenge — sie haengt unter der
        # Mutter frei weiter und ist dort die tiefste feste Kante.
        Quader('Tr8x2-Spindel', sx - r_spi, sx + r_spi, sy - r_spi,
               sy + r_spi, L['spindel_z0_ist'], L['spindel_z1'], 'kaufteil'),
    ]
    bewegte = [
        Quader('Z-Wagen MGN9H', -w('z_wagen_breite') / 2,
               w('z_wagen_breite') / 2, L['sockel_y1'], L['z_wagen_y'],
               -w('z_wagen_laenge') / 2, w('z_wagen_laenge') / 2, 'fuehrung'),
        Quader('Schlitten Pad/Rippen', -w('pad_breite') / 2,
               w('pad_breite') / 2, L['schlitten_y0'], L['schlitten_y1'],
               L['schlitten_unten_rel'], L['schlitten_oben_rel']),
        Quader('Schlittenplatte', -w('schlitten_breite_l'),
               w('winkel_x_rechts'), L['schlitten_y1'], L['laser_y'],
               L['schlitten_unten_rel'], L['schlitten_oben_rel']),
        # Lasche links an der Platte, dahinter die Schaltfahne (eigenes
        # Teil): Fuss, Steg ueber der Seitenrippe und das Blatt fuer die
        # Gabel. Gezeigt in der Mitte ihres Langlochs.
        Quader('Fahnenlasche', L['ls_lasche_x0'], L['ls_lasche_x1'],
               L['schlitten_y1'], L['laser_y'],
               L['ls_lasche_z0_rel'], L['ls_lasche_z1_rel']),
        Quader('Schaltfahne Fuss', L['ls_fuss_x0'], L['ls_fuss_x1'],
               L['ls_fuss_y0'], L['ls_fuss_y1'],
               L['ls_fuss_z0_rel'], L['ls_fuss_z1_rel']),
        Quader('Schaltfahne Steg', L['ls_fuss_x1'], L['ls_fahne_x1'],
               L['ls_fuss_y0'], L['ls_fuss_y1'],
               L['ls_steg_z0_rel'], L['ls_fuss_z1_rel']),
        Quader('Schaltfahne', L['ls_fahne_x0'], L['ls_fahne_x1'],
               L['ls_fahne_y0'], L['ls_fahne_y1'],
               L['ls_steg_z0_rel'], L['ls_fahne_z1_rel']),
        # Mutternwinkel: senkrechter Ruecken an der Platte, Regal darueber,
        # und darauf die Garnitur (Flanschmutter + Feder + Gleitmutter).
        Quader('Winkel Ruecken', w('winkel_x_links'), w('winkel_x_rechts'),
               L['winkel_y0'], L['schlitten_y1'], L['winkel_unten_rel'],
               L['regal_z1_rel']),
        Quader('Winkel Regal', w('winkel_x_links'), w('winkel_x_rechts'),
               L['regal_y0'], L['regal_y1'],
               L['regal_z0_rel'], L['regal_z1_rel']),
        Quader('Antriebsmutter Tr8x2',
               w('spindel_x') - w('t8_flansch_d') / 2,
               w('spindel_x') + w('t8_flansch_d') / 2,
               L['regal_y0'], L['regal_y1'],
               L['regal_z1_rel'], L['garnitur_z1_rel'], 'kaufteil'),
        Quader('Diodenlaser', -w('laser_breite') / 2, w('laser_breite') / 2,
               L['laser_y'], L['laser_vorn_y'], L['laser_unten_rel'],
               L['laser_oben_rel'], 'kaufteil'),
    ]
    erlaubt = {
        # konstruktiv aneinanderliegend
        ('Z-Wagen MGN9H', 'Z-Schiene MGN9'),
        ('Z-Wagen MGN9H', 'Schlitten Pad/Rippen'),
        ('Schlitten Pad/Rippen', 'Schlittenplatte'),
        ('Schlittenplatte', 'Diodenlaser'),
        ('Schlittenplatte', 'Winkel Ruecken'),
        ('Winkel Ruecken', 'Winkel Regal'),
        # Das Regal liegt mit winkel_luft ueber der Plattenoberkante — die
        # Stirnflaechen laufen mit Absicht dicht aneinander vorbei.
        ('Schlittenplatte', 'Winkel Regal'),
        ('Schlitten Pad/Rippen', 'Winkel Regal'),
        ('Winkel Regal', 'Antriebsmutter Tr8x2'),
        ('Winkel Regal', 'Tr8x2-Spindel'),
        ('Winkel Ruecken', 'Tr8x2-Spindel'),
        ('Winkel Ruecken', 'Antriebsmutter Tr8x2'),
        # Die Spindel laeuft mit Absicht dicht hinter der Schlittenplatte —
        # spindel_y ist nach hinten durch den Zugang zu den Motorschrauben
        # und nach vorn durch genau diesen Abstand festgelegt. Er ist ueber
        # den ganzen Verfahrweg konstant (die Platte haengt ueber den
        # Mutternwinkel starr an der Spindelmutter) und wird in
        # toolhead_check.py Abschnitt 7 einzeln geprueft.
        ('Schlittenplatte', 'Tr8x2-Spindel'),
        ('Antriebsmutter Tr8x2', 'Tr8x2-Spindel'),
        ('Kupplung', 'Tr8x2-Spindel'),
        ('Motorkonsole', 'NEMA 17'),
        ('Motorkonsole', 'Motoradapter'),
        ('Motoradapter', 'NEMA 17'),
        # Mit Adapter ragt die Kupplung oben in die Bundbohrung der Konsole.
        # Der Quader der Konsole kennt die Bohrung nicht; Luft rundum und
        # Erreichbarkeit der Klemmschraube prueft toolhead_check.py, Abschnitt 2.
        ('Motorkonsole', 'Kupplung'),
        ('Motorkonsole', 'Fuehrungsrippe links'),
        ('Motorkonsole', 'Fuehrungsrippe rechts'),
        ('Fuehrungsrippe links', 'NEMA 17'),
        ('Fuehrungsrippe rechts', 'NEMA 17'),
        ('Motorkonsole', 'Traegerplatte Kopf'),
        ('Motorkonsole', 'Traegerplatte Hauptsaeule'),
        ('Traegerplatte Hauptsaeule', 'Traegerplatte Kopf'),
        ('Traegerplatte Hauptsaeule', 'Schienensockel'),
        ('Traegerplatte Hauptsaeule', 'Endschaltersockel'),
        ('Traegerplatte Kopf', 'Endschaltersockel'),
        ('Endschaltersockel', 'Halter Flansch'),
        ('Halter Flansch', 'Halter Wand'),
        ('Halter Wand', 'Lichtschranke'),
        ('Lichtschranke', 'Gabel hinten'),
        ('Lichtschranke', 'Gabel vorn'),
        ('Lichtschranke', 'Gabel Boden'),
        ('Gabel hinten', 'Gabel Boden'),
        ('Gabel vorn', 'Gabel Boden'),
        # Lasche und Fahne: verschraubt bzw. ein Teil
        ('Schlittenplatte', 'Fahnenlasche'),
        ('Fahnenlasche', 'Schaltfahne Fuss'),
        ('Fahnenlasche', 'Schaltfahne Steg'),
        # Die Lasche setzt die Anschraubflaeche der Platte nach links fort:
        # der Laser liegt in derselben Ebene und stoesst nur an ihre Kante.
        # Kopf und Scheibe der Fahnenschrauben daneben prueft Abschnitt 9.
        ('Diodenlaser', 'Fahnenlasche'),
        ('Schaltfahne Fuss', 'Schaltfahne Steg'),
        ('Schaltfahne Fuss', 'Schaltfahne'),
        ('Schaltfahne Steg', 'Schaltfahne'),
        # Das Blatt laeuft mit Absicht durch den Gabelspalt, 2,5 mm neben
        # den Armen und ueber dem Schlitzboden — einzeln geprueft in
        # toolhead_check.py, Abschnitt 9.
        ('Schaltfahne', 'Gabel hinten'),
        ('Schaltfahne', 'Gabel vorn'),
        ('Schaltfahne', 'Gabel Boden'),
        ('Traegerplatte Hauptsaeule', 'Saeulenrippe links'),
        ('Traegerplatte Hauptsaeule', 'Saeulenrippe rechts'),
        ('Traegerplatte Kopf', 'Saeulenrippe links'),
        ('Traegerplatte Kopf', 'Saeulenrippe rechts'),
        ('Motorkonsole', 'Saeulenrippe links'),
        ('Motorkonsole', 'Saeulenrippe rechts'),
        ('Traegerplatte Kopf', 'Schienensockel'),
        ('Schienensockel', 'Z-Schiene MGN9'),
        ('Traegerplatte Hauptsaeule', 'X-Wagen MGN15H'),
        ('Traegerplatte Kopf', 'X-Wagen MGN15H'),
        ('X-Wagen MGN15H', 'X-Schiene MGN15'),
        ('X-Schiene MGN15', 'Portalprofil 2020'),
        # Der Sockel liegt vollstaendig im Schienenquerschnitt: was die
        # Wagenschuerzen an der Schiene vorbeilaesst, laesst sie auch am
        # Sockel vorbei (eigene Pruefung in Abschnitt 4).
        ('Schienensockel', 'Z-Wagen MGN9H'),
        # Die Traegerplatte steht nur so weit vor, wie der X-Wagen hoch ist.
        ('Traegerplatte Hauptsaeule', 'X-Schiene MGN15'),
        ('Traegerplatte Kopf', 'X-Schiene MGN15'),
        # Riemenhalter: verschraubt an der Platte, steht auf der Wagenflanke
        ('Riemenhalter', 'Traegerplatte Hauptsaeule'),
        ('Riemenhalter', 'X-Wagen MGN15H'),
        # Kettenhalter: ein Teil, verschraubt an der Platte; das Anfangsstueck
        # liegt auf der Auflage zwischen den Leisten
        ('Kettenhalter Fuss', 'Traegerplatte Hauptsaeule'),
        ('Kettenhalter Auflage', 'Traegerplatte Hauptsaeule'),
        ('Kettenhalter Leiste vorn', 'Traegerplatte Hauptsaeule'),
        ('Kettenhalter Fuss', 'Kettenhalter Auflage'),
        ('Kettenhalter Fuss', 'Kettenhalter Leiste vorn'),
        ('Kettenhalter Auflage', 'Kettenhalter Leiste hinten'),
        ('Kettenhalter Auflage', 'Kettenhalter Leiste vorn'),
        ('Kettenhalter Auflage', 'Kette Anfangsstueck'),
    }
    return feste, bewegte, erlaubt


def freier_korridor(punkt, achse, richtung, r, boxen, ausser=()):
    """Freie Werkzeuglaenge ab `punkt` (x, y, z) entlang `achse` in
    `richtung` (+1/-1), fuer einen Korridor mit Radius `r`.

    Liefert (laenge_mm, name_des_ersten_hindernisses). laenge = float('inf'),
    wenn nichts im Weg ist. Damit laesst sich pruefen, ob ein Inbus in eine
    Schraube gesteckt werden kann — die reine Ja/Nein-Frage (zugang_frei)
    genuegt nicht, weil ein Hindernis 60 mm weiter weg keines ist.
    """
    i = {'x': 0, 'y': 1, 'z': 2}[achse]
    quer = [j for j in (0, 1, 2) if j != i]
    laenge, schuld = float('inf'), None
    for q in boxen:
        if q.name in ausser:
            continue
        kasten = (q.x, q.y, q.z)
        if not all(kasten[j][0] < punkt[j] + r and punkt[j] - r < kasten[j][1]
                   for j in quer):
            continue
        if richtung > 0 and kasten[i][1] > punkt[i]:
            d = max(kasten[i][0] - punkt[i], 0.0)
        elif richtung < 0 and kasten[i][0] < punkt[i]:
            d = max(punkt[i] - kasten[i][1], 0.0)
        else:
            continue
        if d < laenge:
            laenge, schuld = d, q.name
    return laenge, schuld


# --- Portal: Y-Schlitten, X-Antrieb, Rahmen (fusion/Portal) --------------------
def portal_bauraeume(w, L):
    """(feste, erlaubte_paare) des Portals in Portal-Koordinaten: X = 0 in
    der Mitte des Portalrohrs, Y und Z wie beim Toolhead. Links und rechts
    gespiegelt, die Namen tragen die Seite. Was das Portal nur in Y bewegt
    (Y-Schiene, Rahmen, Y-Riemen), laeuft als langer Quader durch.

    Lagerschlitten und Umlenkritzel stehen als Huelle ueber ihren
    ganzen Stellweg; der Riemen als Koerper um seine Wirklinie."""
    R = L['R']
    lang = 800.0
    fl = w('motor_flansch') / 2.0

    def xb(s, u0, u1):
        a, b = s * (R - u0), s * (R - u1)
        return min(a, b), max(a, b)

    def q(name, x, y, z, art='druck'):
        return Quader(name, x[0], x[1], y[0], y[1], z[0], z[1], art)

    feste = [
        q('Portalrohr', (-w('profil_laenge') / 2, w('profil_laenge') / 2),
          (L['profil_y0'], L['portal_y']), (L['profil_z0'], L['profil_z1']),
          'kaufteil'),
        q('X-Schiene', L['x_schiene_x'], (L['portal_y'], L['x_schiene_y1']),
          (-w('x_schiene_b') / 2, w('x_schiene_b') / 2), 'fuehrung'),
    ]
    for s in (-1, 1):
        n = 'links' if s < 0 else 'rechts'
        feste += [
            q('Platte ' + n, xb(s, *L['platte_u']),
              (L['platte_y0'], L['platte_y1']),
              (L['platte_z0'], L['platte_z1'])),
            q('Rueckwand ' + n, xb(s, *L['rueck_u']),
              (L['rueck_y0'], L['rueck_y1']), (L['platte_z1'], L['wand_z1'])),
            q('Stirnblock ' + n, xb(s, *L['stirn_u']), L['stirn_y'],
              (L['platte_z1'], L['wand_z1'])),
            # Klemmtuerme (seit Rev. 25 dicht an der 2040): unten bis unter
            # den Y-Wagen, seit Rev. 27 innen nur bis kt_u_unten; oben der
            # Absatz neben ihm mit dem Block um die Einsaetze (Hals und Fase
            # darunter gehoeren ganz zum oberen, die 45-Grad-Fase zur 2040
            # ganz zum unteren Quader)
            q('Klemmturm hinten ' + n, xb(s, L['kt_u'][0], L['kt_u_unten']),
              L['kt_y_hinten'], (L['kt_z'][0], L['kt_absatz_z'])),
            q('Klemmturm hinten ' + n + ' oben',
              xb(s, L['kt_absatz_u'], L['kt_u'][1]), L['kt_y_hinten'],
              (L['kt_absatz_z'], L['kt_z'][1])),
            q('Klemmturm vorn ' + n, xb(s, L['kt_u'][0], L['kt_u_unten']),
              L['kt_y_vorn'], (L['kt_z'][0], L['kt_absatz_z'])),
            q('Klemmturm vorn ' + n + ' oben',
              xb(s, L['kt_absatz_u'], L['kt_u'][1]), L['kt_y_vorn'],
              (L['kt_absatz_z'], L['kt_z'][1])),
            # Schieber ueber den ganzen Weg, hinten mit dem Kopf der
            # Druckschraube (ganz entspannt)
            q('Y-Wagen ' + n,
              xb(s, -w('y_wagen_breite') / 2, w('y_wagen_breite') / 2),
              (L['wagen_y0'], L['wagen_y1']),
              (L['y_wagen_z0'], L['y_wagen_z1']), 'fuehrung'),
            q('Y-Schiene ' + n,
              xb(s, -w('y_schiene_b') / 2, w('y_schiene_b') / 2),
              (-lang, lang), (L['y_schiene_z0'], L['y_schiene_z1']),
              'fuehrung'),
            q('Rahmen 2040 ' + n,
              xb(s, -w('rahmen_b') / 2, w('rahmen_b') / 2), (-lang, lang),
              (L['rahmen_z0'], L['rahmen_z1']), 'kaufteil'),
            q('Y-Riemen ' + n,
              xb(s, L['y_riemen_linie'] - w('riemen_dicke') / 2,
                 L['y_riemen_linie'] + w('riemen_dicke') / 2),
              (-lang, lang), (L['yr_z0'], L['yr_z1']), 'riemen'),
            # Ruecklauf: in der oberen Nut des 2040, auf der Schienenseite
            q('Y-Ruecklauf ' + n,
              xb(s, L['yr_rueck_u'] - w('riemen_dicke') / 2,
                 L['yr_rueck_u'] + w('riemen_dicke') / 2),
              (-lang, lang), L['yr_rueck_z'], 'riemen'),
        ]
    s = -1
    xm, yc = s * (R - w('motor_u')), L['xr_yc']
    feste += [
        q('Motorplatte', xb(s, *L['mp_u']), L['mp_y'],
          (L['mp_z0'], L['mp_z1'])),
        q('Motorhalter Saeule hinten', xb(s, *L['mh_hinten_u']),
          L['mh_hinten_y'], L['mh_z']),
        q('Motorhalter Saeule aussen', xb(s, *L['mh_aussen_u']),
          (L['mh_hinten_y'][1], L['mp_y'][1]), L['mh_z']),
        # Anschlag (Rev. 24) auf dem linken Stirnblock, innen neben der
        # aeusseren Saeule: nimmt den Riemenzug auf
        q('Anschlag Motorhalter', xb(s, *L['mha_u']), L['mha_y'],
          L['mha_z']),
        q('X-Motor', (xm - fl, xm + fl), (yc - fl, yc + fl),
          (L['mp_z1'], L['motor_z1']), 'kaufteil'),
        q('X-Ritzel', (xm - w('ritzel_flansch_d') / 2,
                       xm + w('ritzel_flansch_d') / 2),
          (yc - w('ritzel_flansch_d') / 2, yc + w('ritzel_flansch_d') / 2),
          (L['ritzel_z0'], L['ritzel_z1']), 'kaufteil'),
    ]
    s = 1
    ru, rel = L['rolle_u'], L['ls_u_rel']
    rf = w('ritzel_flansch_d') / 2.0
    rn = w('ritzel_nabe_d') / 2.0
    ls_x = xb(s, ru[0] + rel[0], ru[1] + rel[1])      # ueber den Spannweg
    fu = L['ls_feder_u_rel']
    zw = (L['ls_unten_z'][1], L['ls_oben_z'][0])
    feste += [
        q('Spannbock Boden', xb(s, *L['sb_u']), L['sb_y'], L['sb_boden_z']),
        q('Spannbock Wand', xb(s, *L['sb_wand_u']), L['sb_wand_y'],
          L['sb_wand_z']),
        # Lagerschlitten: Rahmen um das Umlenkritzel
        q('Lagerschlitten unten', ls_x, L['ls_y'], L['ls_unten_z']),
        q('Lagerschlitten oben', ls_x, L['ls_y'], L['ls_oben_z']),
        q('Lagerschlitten Ruecken', ls_x, L['ls_ruecken_y'], zw),
        q('Lagerschlitten Pfosten', ls_x, L['ls_pfosten_y'], zw),
        q('Lagerschlitten Feder', xb(s, ru[0] + fu[0], ru[1] + fu[1]),
          L['ls_feder_y'], L['ls_feder_z']),
        # Umlenkritzel mit der Nabe nach oben: Borde und Spur, darueber
        # die schmalere Nabe
        q('X-Umlenkritzel', xb(s, ru[0] - rf, ru[1] + rf), (yc - rf, yc + rf),
          (L['rolle_z0'], L['rolle_nabe_z0']), 'kaufteil'),
        q('X-Umlenkritzel Nabe', xb(s, ru[0] - rn, ru[1] + rn),
          (yc - rn, yc + rn), (L['rolle_nabe_z0'], L['rolle_z1']),
          'kaufteil'),
        q('Zugschraube Kopf', xb(s, L['sb_wand_u'][0] - 3.0,
                                 L['sb_wand_u'][0]),
          (L['zug_y'] - 2.75, L['zug_y'] + 2.75),
          (L['zug_z'] - 2.75, L['zug_z'] + 2.75), 'stahl'),
        # Ruecklauf des X-Riemens: fest zwischen Motor und Umlenkung
        q('X-Riemen Ruecklauf', (L['x_motor'], L['x_rolle_bereich'][1]),
          (L['xr_y_rueck'] - L['riemen_aussen'],
           L['xr_y_rueck'] + L['riemen_innen']),
          (L['xr_z0'], L['xr_z1']), 'riemen'),
        # X-Energiekette (Rev. 19): Wanne direkt hinter der Traegerplatte, der
        # Untertrum als Huelle ueber seinen ganzen Weg (vom Endstueck am
        # Festpunkt bis zum Bogenanfang am rechten Ende). Bogen und Obertrum
        # fahren mit: tools/portal_check.py, Abschnitt 17.
        q('Kettenwanne', L['wanne_x'], L['wanne_y'], L['wanne_z']),
        q('X-Kette Untertrum', (L['xk_fest'] - w('endstueck_l'),
                                L['xk_bogen_x'][1]),
          L['xk_y'], L['xk_unter_z']),
    ]
    hb = w('wanne_lasche_b') / 2.0
    for i, (xl, _) in enumerate(L['wanne_laschen']):
        feste.append(q('Kettenwanne Lasche {}'.format(i + 1),
                       (xl - hb, xl + hb), L['wanne_lasche_y'],
                       L['wanne_boden_z']))
    for n, x in L['st_x'].items():
        feste += [
            q('Wannenstuetze {} Platte'.format(n), x, L['st_platte_y'],
              L['st_platte_z']),
            q('Wannenstuetze {} Block'.format(n), x, L['st_block_y'],
              L['st_block_z']),
            q('Wannenstuetze {} Arm'.format(n), x, L['st_arm_y'],
              L['st_arm_z'])]
    # Kabelfluegel am Festpunkt (Rev. 21) und die Litzen davor: aus der
    # oberen Nut hoch, oben ueber den Riemen nach vorn in die Wanne
    feste += [
        q('Wannenstuetze Festpunkt Fluegel', L['kf_x'], L['kf_y'],
          L['kf_z']),
        q('Litzen X am Fluegel', L['kf_buendel_x'], L['kf_buendel_y'],
          (L['profil_z1'], L['kf_quer_z'][1]), 'kabel'),
        q('Litzen X zur Wanne', (L['kf_buendel_x'][0], L['wanne_x'][0]),
          (L['kf_buendel_y'][0], L['xk_y_mitte'] + w('kf_buendel_t') / 2.0),
          L['kf_quer_z'], 'kabel')]
    # Y-Kette (Rev. 21): was mit dem Portal faehrt — Kettenhalter Y auf dem
    # linken Schlitten und das Anfangsstueck darauf. Wanne, Traeger und
    # Kette selbst: y_kette_rahmen() und tools/portal_check.py, Abschnitt 18
    feste += [
        q('Kettenhalter Y', L['khy_x'], L['khy_y'], L['khy_z']),
        q('Kettenhalter Y Leiste aussen', L['khy_leiste_aussen_x'],
          L['khy_leiste_y'], L['khy_leiste_z']),
        q('Kettenhalter Y Leiste innen', L['khy_leiste_innen_x'],
          L['khy_leiste_y'], L['khy_leiste_z']),
        q('Y-Kette Anfangsstueck', L['yk_x'], L['khy_ende_y'],
          L['yk_ober_z'], 'kette')]
    erlaubt = {
        ('Portalrohr', 'X-Schiene'),
        ('Motorplatte', 'Motorhalter Saeule hinten'),
        ('Motorplatte', 'Motorhalter Saeule aussen'),
        ('Motorhalter Saeule hinten', 'Motorhalter Saeule aussen'),
        ('Motorplatte', 'X-Motor'),
        # die Ritzelnabe taucht in die Bundbohrung der Motorplatte (Ø22,4
        # um den Bord Ø16) — portal_check.py prueft die Luft rundum
        ('Motorplatte', 'X-Ritzel'),
        # der Motorhalter steht auf Stirnblock, Rueckwand und Rohr
        ('Motorhalter Saeule hinten', 'Stirnblock links'),
        ('Motorhalter Saeule hinten', 'Rueckwand links'),
        ('Motorhalter Saeule hinten', 'Portalrohr'),
        ('Motorhalter Saeule aussen', 'Stirnblock links'),
        ('Anschlag Motorhalter', 'Stirnblock links'),     # ein Teil
        # Spannbock auf Stirnblock, Rueckwand und Rohrende
        ('Spannbock Boden', 'Spannbock Wand'),
        ('Spannbock Boden', 'Stirnblock rechts'),
        ('Spannbock Boden', 'Rueckwand rechts'),
        ('Spannbock Boden', 'Portalrohr'),
        ('Spannbock Wand', 'Zugschraube Kopf'),
        # Lagerschlitten: ein Teil, liegt auf dem Rohr, die Feder in der Nut
        ('Lagerschlitten unten', 'Lagerschlitten Ruecken'),
        ('Lagerschlitten unten', 'Lagerschlitten Pfosten'),
        ('Lagerschlitten oben', 'Lagerschlitten Ruecken'),
        ('Lagerschlitten oben', 'Lagerschlitten Pfosten'),
        ('Lagerschlitten unten', 'Lagerschlitten Feder'),
        ('Lagerschlitten unten', 'Portalrohr'),
        ('Lagerschlitten Feder', 'Portalrohr'),
        # der Riemen laeuft um Ritzel und Rolle
        ('X-Riemen Ruecklauf', 'X-Ritzel'),
        ('X-Riemen Ruecklauf', 'X-Umlenkritzel'),
        ('X-Umlenkritzel', 'X-Umlenkritzel Nabe'),     # ein Teil
        # Kette: der Untertrum liegt in der Wanne, sie auf den Armen, ihre
        # Laschen auf den Bloecken; die Stuetzen an und auf dem Rohr
        ('Kettenwanne', 'X-Kette Untertrum'),
        ('Kettenwanne', 'Kettenwanne Lasche 1'),
        ('Kettenwanne', 'Kettenwanne Lasche 2'),
        ('Kettenwanne Lasche 1', 'Wannenstuetze mitte Block'),
        ('Kettenwanne Lasche 2', 'Wannenstuetze rechts Block'),
        # Kabelfluegel: ein Teil mit der Stuetze, steht auf dem Rohr; die
        # Litzen kommen aus der Nut, liegen am Fluegel und gehen in die Wanne
        ('Wannenstuetze Festpunkt Fluegel', 'Wannenstuetze Festpunkt Platte'),
        ('Wannenstuetze Festpunkt Fluegel', 'Wannenstuetze Festpunkt Block'),
        ('Wannenstuetze Festpunkt Fluegel', 'Portalrohr'),
        ('Litzen X am Fluegel', 'Wannenstuetze Festpunkt Fluegel'),
        ('Litzen X am Fluegel', 'Portalrohr'),
        ('Litzen X am Fluegel', 'Litzen X zur Wanne'),
        ('Litzen X zur Wanne', 'Kettenwanne'),
        # Kettenhalter Y: ein Teil, liegt auf der Platte des linken
        # Schlittens, das Anfangsstueck liegt zwischen den Leisten darauf
        ('Kettenhalter Y', 'Platte links'),
        ('Kettenhalter Y', 'Kettenhalter Y Leiste aussen'),
        ('Kettenhalter Y', 'Kettenhalter Y Leiste innen'),
        ('Kettenhalter Y', 'Y-Kette Anfangsstueck'),
        ('Kettenhalter Y Leiste innen', 'Platte links'),
    }
    for n in L['st_x']:
        erlaubt |= {
            ('Kettenwanne', 'Wannenstuetze {} Arm'.format(n)),
            ('Wannenstuetze {} Platte'.format(n),
             'Wannenstuetze {} Block'.format(n)),
            ('Wannenstuetze {} Block'.format(n),
             'Wannenstuetze {} Arm'.format(n)),
            ('Wannenstuetze {} Platte'.format(n),
             'Wannenstuetze {} Arm'.format(n)),
            ('Wannenstuetze {} Platte'.format(n), 'Portalrohr'),
            ('Wannenstuetze {} Block'.format(n), 'Portalrohr'),
        }
    for n in ('links', 'rechts'):
        erlaubt |= {
            ('Portalrohr', 'Platte ' + n), ('Portalrohr', 'Rueckwand ' + n),
            ('Portalrohr', 'Stirnblock ' + n),
            ('Platte ' + n, 'Rueckwand ' + n), ('Platte ' + n, 'Stirnblock ' + n),
            ('Rueckwand ' + n, 'Stirnblock ' + n),
            ('Platte ' + n, 'Klemmturm hinten ' + n + ' oben'),
            ('Platte ' + n, 'Klemmturm vorn ' + n + ' oben'),
            ('Klemmturm hinten ' + n, 'Klemmturm hinten ' + n + ' oben'),
            ('Klemmturm vorn ' + n, 'Klemmturm vorn ' + n + ' oben'),
            ('Platte ' + n, 'Y-Wagen ' + n),
            ('Klemmturm hinten ' + n, 'Y-Riemen ' + n),
            ('Klemmturm vorn ' + n, 'Y-Riemen ' + n),
            # Seit Rev. 26 liegen die Tuerme im Modell an der 2040 an, das
            # die Schiene mittig rechnet; am Aufbau bleibt kt_luft_profil
            # (portal_check.py, Abschnitt 6, mit kt_luft_mehr)
            ('Klemmturm hinten ' + n, 'Rahmen 2040 ' + n),
            ('Klemmturm vorn ' + n, 'Rahmen 2040 ' + n),
            ('Y-Wagen ' + n, 'Y-Schiene ' + n),
            ('Y-Schiene ' + n, 'Rahmen 2040 ' + n),
            ('Y-Ruecklauf ' + n, 'Rahmen 2040 ' + n),   # laeuft in der Nut
        }
    return feste, erlaubt



def y_kette_rahmen(w, L):
    """Rahmenfeste Teile der Y-Kette (Portal.py Rev. 21) in Rahmenkoordinaten
    (Portal in der Mitte, wie Abschnitt 14 von portal_check.py): Wanne Y mit
    Laschen, die drei Traeger (Wand und Arm) und — angenommen — die Winkel
    an den Kreuzungen aussen am linken 2040 (je 20 mm vom Profil und ueber
    dem 2060, vor und hinter dem 2060). Liefert (quader, erlaubte_paare)."""
    def q(name, x, y, z, art='druck'):
        return Quader(name, x[0], x[1], y[0], y[1], z[0], z[1], art)

    xw, yw = L['ywanne_x'], L['ywanne_y']
    teile = [q('Kettenwanne Y', xw, yw, L['ywanne_z'])]
    hb = w('wanne_lasche_b') / 2.0
    for i, (_, yl) in enumerate(L['ywanne_laschen']):
        teile.append(q('Kettenwanne Y Lasche {}'.format(i + 1),
                       L['ywanne_lasche_x'], (yl - hb, yl + hb),
                       L['ywanne_boden_z']))
    erlaubt = set()
    for n, y in L['ytr_y'].items():
        wand, arm = 'Traeger Y {} Wand'.format(n), 'Traeger Y {} Arm'.format(n)
        teile += [q(wand, L['ytr_wand_x'], y, L['ytr_wand_z']),
                  q(arm, L['ytr_arm_x'], y, L['ytr_arm_z'])]
        erlaubt |= {(wand, arm), (arm, 'Kettenwanne Y'),
                    (wand, 'Rahmen 2040 links')}
    for i in (1, 2):
        erlaubt.add(('Kettenwanne Y', 'Kettenwanne Y Lasche {}'.format(i)))
    erlaubt |= {('Kettenwanne Y Lasche 1', 'Traeger Y mitte Arm'),
                ('Kettenwanne Y Lasche 2', 'Traeger Y vorn Arm')}
    # Winkel an den Kreuzungen: 20 mm, in der unteren Nut der 2040 (Angaben
    # 2026-09-27/29); aussen am linken 2040 direkt am 2060 angenommen
    xa = -L['aussen_x']
    zq = L['quer_z'][1]
    for n, (y0, y1) in (('hinten', L['quer_y_hinten']),
                        ('vorn', L['quer_y_vorn'])):
        teile.append(q('Winkel 2040/2060 ' + n, (xa - 20.0, xa),
                       (y0 - 20.0, y1 + 20.0), (zq, zq + 20.0), 'kaufteil'))
    return teile, erlaubt


def x_riemen_trume(L, xw, rh_x0, rh_x1):
    """Die beiden Stuecke des gezogenen Trums bei X-Wagenmitte xw: vom Motor
    bis zum Riemenhalter und vom Riemenhalter bis zum Umlenkritzel (Mitte des
    Spannwegs). rh_x0/rh_x1: Enden des Riemenhalters relativ zum X-Wagen."""
    y0 = L['xr_y'] - L['riemen_innen']
    y1 = L['xr_y'] + L['riemen_aussen']
    return [Quader('X-Riemen links', L['x_motor'], xw + rh_x0, y0, y1,
                   L['xr_z0'], L['xr_z1'], 'riemen'),
            Quader('X-Riemen rechts', xw + rh_x1, L['x_rolle'], y0, y1,
                   L['xr_z0'], L['xr_z1'], 'riemen')]
