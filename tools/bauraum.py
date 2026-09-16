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
    r_kup, r_spi = w('kupplung_d') / 2.0, w('spindel_durchgang') / 2.0

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
        Quader('NEMA 17', sx - w('motor_flansch') / 2,
               sx + w('motor_flansch') / 2, sy - w('motor_flansch') / 2,
               sy + w('motor_flansch') / 2, L['motor_flansch_z'], L['motor_z1'],
               'kaufteil'),
        Quader('Kupplung', sx - r_kup, sx + r_kup, sy - r_kup, sy + r_kup,
               L['kupplung_z0'], L['kupplung_z1'], 'kaufteil'),
        Quader('M6-Gewindestange', sx - r_spi, sx + r_spi, sy - r_spi,
               sy + r_spi, L['spindel_z0'], L['spindel_z1'], 'kaufteil'),
    ]
    bewegte = [
        Quader('Z-Wagen MGN9H', -w('z_wagen_breite') / 2,
               w('z_wagen_breite') / 2, L['sockel_y1'], L['z_wagen_y'],
               -w('z_wagen_laenge') / 2, w('z_wagen_laenge') / 2, 'fuehrung'),
        Quader('Schlitten Pad/Rippen', -w('pad_breite') / 2,
               w('pad_breite') / 2, L['schlitten_y0'], L['schlitten_y1'],
               L['schlitten_unten_rel'], L['schlitten_oben_rel']),
        Quader('Schlittenplatte', -w('schlitten_breite_l'),
               w('block_x_rechts'), L['schlitten_y1'], L['laser_y'],
               L['schlitten_unten_rel'], L['schlitten_oben_rel']),
        Quader('Mutternblock', w('block_x_links'), w('block_x_rechts'),
               w('block_y_hinten'), L['schlitten_y1'], L['block_unten_rel'],
               L['block_oben_rel']),
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
        ('Schlittenplatte', 'Mutternblock'),
        ('Mutternblock', 'M6-Gewindestange'),
        ('Kupplung', 'M6-Gewindestange'),
        ('Motorkonsole', 'NEMA 17'),
        ('Motorkonsole', 'Fuehrungsrippe links'),
        ('Motorkonsole', 'Fuehrungsrippe rechts'),
        ('Fuehrungsrippe links', 'NEMA 17'),
        ('Fuehrungsrippe rechts', 'NEMA 17'),
        ('Motorkonsole', 'Traegerplatte Kopf'),
        ('Motorkonsole', 'Traegerplatte Hauptsaeule'),
        ('Traegerplatte Hauptsaeule', 'Traegerplatte Kopf'),
        ('Traegerplatte Hauptsaeule', 'Schienensockel'),
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
