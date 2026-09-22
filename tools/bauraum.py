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


def modul_laden():
    """Importiert das Fusion-Skript ohne Fusion: adsk wird nur innerhalb der
    Funktionen benutzt, der Modulimport laeuft also mit einem Stub durch."""
    for name in ('adsk', 'adsk.core', 'adsk.fusion'):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules['adsk'].core = sys.modules['adsk.core']
    sys.modules['adsk'].fusion = sys.modules['adsk.fusion']
    spec = importlib.util.spec_from_file_location('toolhead_z', SKRIPT)
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

    def verschoben(self, dz):
        return Quader(self.name, self.x[0], self.x[1], self.y[0], self.y[1],
                      self.z[0] + dz, self.z[1] + dz, self.art)

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
        # Endschalter: Sockel an der Platte, Halter (Flansch + Wand) und die
        # Platine der Gabellichtschranke.
        Quader('Endschaltersockel', w('traeger_x_links'), w('ls_sockel_x1'),
               L['traeger_y1'], L['ls_sockel_y1'],
               L['ls_sockel_z0'], L['ls_sockel_z1']),
        Quader('Halter Flansch', L['ls_wand_x0'], w('ls_sockel_x1'),
               L['ls_sockel_y1'], L['ls_flansch_y1'],
               L['ls_sockel_z0'], L['ls_sockel_z1']),
        Quader('Halter Wand', L['ls_wand_x0'], L['ls_wand_x1'],
               L['ls_sockel_y1'], L['ls_wand_y1'],
               L['ls_sockel_z0'], L['ls_sockel_z1']),
        Quader('Lichtschranke', L['ls_wand_x1'],
               L['ls_wand_x1'] + w('ls_pcb_dicke'),
               L['ls_pcb_y0'], L['ls_pcb_y1'],
               L['ls_pcb_z0'], L['ls_pcb_z1'], 'kaufteil'),
        Quader('NEMA 17', sx - w('motor_flansch') / 2,
               sx + w('motor_flansch') / 2, sy - w('motor_flansch') / 2,
               sy + w('motor_flansch') / 2, L['motor_flansch_z'], L['motor_z1'],
               'kaufteil'),
        Quader('Kupplung', sx - r_kup, sx + r_kup, sy - r_kup, sy + r_kup,
               L['kupplung_z0'], L['kupplung_z1'], 'kaufteil'),
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
        # Die Platte ist an der oberen linken Ecke verbreitert — sie traegt
        # dort die Schaltfahne.
        Quader('Schlittenplatte', L['ls_fahne_x0'],
               w('winkel_x_rechts'), L['schlitten_y1'], L['laser_y'],
               L['schlitten_unten_rel'], L['schlitten_oben_rel']),
        Quader('Schaltfahne', L['ls_fahne_x0'], L['ls_fahne_x1'],
               L['ls_fahne_y0'], L['schlitten_y1'],
               L['ls_fahne_z0_rel'], L['ls_fahne_z1_rel']),
        # Mutternwinkel: senkrechter Ruecken an der Platte, Regal darueber,
        # und darauf die Garnitur (Flanschmutter + Feder + Gleitmutter).
        Quader('Winkel Ruecken', w('winkel_x_links'), w('winkel_x_rechts'),
               L['winkel_y0'], L['schlitten_y1'], L['winkel_unten_rel'],
               L['regal_z1_rel']),
        Quader('Winkel Regal', w('winkel_x_links'), w('winkel_x_rechts'),
               L['regal_y0'], L['regal_y1'],
               L['regal_z0_rel'], L['regal_z1_rel']),
        # Zwischen Regal und Flansch: der Ring, der den Zentrierbund freihaelt.
        Quader('Flanschring',
               w('spindel_x') - w('t8_flansch_d') / 2,
               w('spindel_x') + w('t8_flansch_d') / 2,
               L['regal_y0'], L['regal_y1'],
               L['regal_z1_rel'], L['ring_z1_rel']),
        Quader('Antriebsmutter Tr8x2',
               w('spindel_x') - w('t8_flansch_d') / 2,
               w('spindel_x') + w('t8_flansch_d') / 2,
               L['regal_y0'], L['regal_y1'],
               L['ring_z1_rel'], L['garnitur_z1_rel'], 'kaufteil'),
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
        ('Winkel Regal', 'Flanschring'),
        ('Winkel Ruecken', 'Flanschring'),
        ('Flanschring', 'Antriebsmutter Tr8x2'),
        ('Flanschring', 'Tr8x2-Spindel'),
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
        ('Schlittenplatte', 'Schaltfahne'),
        ('Schlitten Pad/Rippen', 'Schaltfahne'),
        # Die Fahne laeuft mit Absicht dicht an der Platine vorbei — sie muss
        # in den Gabelspalt. Der Abstand wird einzeln geprueft.
        ('Schaltfahne', 'Lichtschranke'),
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
