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

    Spannklotz und Umlenkrolle stehen als Huelle ueber ihren
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
            q('Klemmturm hinten ' + n, xb(s, *L['kt_u']), L['kt_y_hinten'],
              L['kt_z']),
            q('Klemmturm vorn ' + n, xb(s, *L['kt_u']), L['kt_y_vorn'],
              L['kt_z']),
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
              xb(s, w('y_riemen_linie') - w('riemen_dicke') / 2,
                 w('y_riemen_linie') + w('riemen_dicke') / 2),
              (-lang, lang), (L['yr_z0'], L['yr_z1']), 'riemen'),
            # Ruecklauf: in der oberen Nut des 2040, auf der Schienenseite
            q('Y-Ruecklauf ' + n,
              xb(s, L['yr_rueck_u'] - w('riemen_dicke') / 2,
                 L['yr_rueck_u'] + w('riemen_dicke') / 2),
              (-lang, lang), (L['yr_z0'], L['yr_z1']), 'riemen'),
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
        q('X-Motor', (xm - fl, xm + fl), (yc - fl, yc + fl),
          (L['mp_z1'], L['motor_z1']), 'kaufteil'),
        q('X-Ritzel', (xm - w('ritzel_flansch_d') / 2,
                       xm + w('ritzel_flansch_d') / 2),
          (yc - w('ritzel_flansch_d') / 2, yc + w('ritzel_flansch_d') / 2),
          (L['ritzel_z0'], L['ritzel_z1']), 'kaufteil'),
    ]
    s = 1
    ru = L['rolle_u']
    rr = w('rolle_d') / 2.0
    kopf = w('m5_kopf_d') / 2.0
    feste += [
        q('Umlenkhalter Saeule', xb(s, *L['uh_saeule_u']), L['uh_saeule_y'],
          (L['wand_z1'], L['uh_oben_z'][1])),
        q('Umlenkhalter oben', xb(s, *L['uh_oben_u']), L['uh_y'],
          L['uh_oben_z']),
        q('Umlenkhalter unten', xb(s, L['uh_oben_u'][0], L['uh_innen_u']),
          L['uh_y'], L['uh_unten_z']),
        q('Umlenkhalter Steg', xb(s, L['uh_oben_u'][0], L['uh_steg_u1']),
          L['uh_y'], (L['uh_unten_z'][1], L['uh_oben_z'][0])),
        q('Umlenkhalter Lasche', xb(s, *L['uh_lasche_u']), L['klotz_y'],
          (L['uh_oben_z'][1], L['klotz_z'][1])),
        q('Spannklotz', xb(s, ru[0] + L['klotz_u_rel'][0],
                           ru[1] + L['klotz_u_rel'][1]),
          L['klotz_y'], L['klotz_z']),
        q('X-Umlenkrolle', xb(s, ru[0] - rr, ru[1] + rr), (yc - rr, yc + rr),
          (L['rolle_z0'], L['rolle_z1']), 'kaufteil'),
        q('M5-Kopf Umlenkung', xb(s, ru[0] - kopf, ru[1] + kopf),
          (yc - kopf, yc + kopf),
          (L['klotz_z'][1] + w('m5_scheibe_h'), L['uh_kopf_z1']), 'stahl'),
        q('Zugschraube Kopf', xb(s, L['uh_lasche_u'][0] - 3.0,
                                 L['uh_lasche_u'][0]),
          (yc - 2.75, yc + 2.75), (L['uh_zug_z'] - 2.75, L['uh_zug_z'] + 2.75),
          'stahl'),
        # Ruecklauf des X-Riemens: fest zwischen Motor und Umlenkung
        q('X-Riemen Ruecklauf', (L['x_motor'], L['x_rolle_bereich'][1]),
          (L['xr_y_rueck'] - L['riemen_aussen'],
           L['xr_y_rueck'] + L['riemen_innen']),
          (L['xr_z0'], L['xr_z1']), 'riemen'),
    ]
    erlaubt = {
        ('Portalrohr', 'X-Schiene'),
        ('Motorplatte', 'Motorhalter Saeule hinten'),
        ('Motorplatte', 'Motorhalter Saeule aussen'),
        ('Motorhalter Saeule hinten', 'Motorhalter Saeule aussen'),
        ('Motorplatte', 'X-Motor'),
        # der Motorhalter steht auf Stirnblock, Rueckwand und Rohr
        ('Motorhalter Saeule hinten', 'Stirnblock links'),
        ('Motorhalter Saeule hinten', 'Rueckwand links'),
        ('Motorhalter Saeule hinten', 'Portalrohr'),
        ('Motorhalter Saeule aussen', 'Stirnblock links'),
        ('Umlenkhalter Saeule', 'Umlenkhalter oben'),
        ('Umlenkhalter Saeule', 'Umlenkhalter Steg'),
        ('Umlenkhalter Saeule', 'Umlenkhalter unten'),
        ('Umlenkhalter oben', 'Umlenkhalter Steg'),
        ('Umlenkhalter unten', 'Umlenkhalter Steg'),
        ('Umlenkhalter oben', 'Umlenkhalter Lasche'),
        ('Umlenkhalter Saeule', 'Stirnblock rechts'),
        ('Umlenkhalter Saeule', 'Rueckwand rechts'),
        ('Umlenkhalter Saeule', 'Portalrohr'),
        ('Umlenkhalter unten', 'Portalrohr'),
        ('Umlenkhalter unten', 'Stirnblock rechts'),
        ('Umlenkhalter oben', 'Spannklotz'),
        ('Umlenkhalter Lasche', 'Zugschraube Kopf'),
        # der Riemen laeuft um Ritzel und Rolle
        ('X-Riemen Ruecklauf', 'X-Ritzel'),
        ('X-Riemen Ruecklauf', 'X-Umlenkrolle'),
    }
    for n in ('links', 'rechts'):
        erlaubt |= {
            ('Portalrohr', 'Platte ' + n), ('Portalrohr', 'Rueckwand ' + n),
            ('Portalrohr', 'Stirnblock ' + n),
            ('Platte ' + n, 'Rueckwand ' + n), ('Platte ' + n, 'Stirnblock ' + n),
            ('Rueckwand ' + n, 'Stirnblock ' + n),
            ('Platte ' + n, 'Klemmturm hinten ' + n),
            ('Platte ' + n, 'Klemmturm vorn ' + n),
            ('Platte ' + n, 'Y-Wagen ' + n),
            ('Klemmturm hinten ' + n, 'Y-Riemen ' + n),
            ('Klemmturm vorn ' + n, 'Y-Riemen ' + n),
            ('Y-Wagen ' + n, 'Y-Schiene ' + n),
            ('Y-Schiene ' + n, 'Rahmen 2040 ' + n),
            ('Y-Ruecklauf ' + n, 'Rahmen 2040 ' + n),   # laeuft in der Nut
        }
    return feste, erlaubt


def x_riemen_trume(L, xw, rh_x0, rh_x1):
    """Die beiden Stuecke des gezogenen Trums bei X-Wagenmitte xw: vom Motor
    bis zum Riemenhalter und vom Riemenhalter bis zur Umlenkrolle (Mitte des
    Spannwegs). rh_x0/rh_x1: Enden des Riemenhalters relativ zum X-Wagen."""
    y0 = L['xr_y'] - L['riemen_innen']
    y1 = L['xr_y'] + L['riemen_aussen']
    return [Quader('X-Riemen links', L['x_motor'], xw + rh_x0, y0, y1,
                   L['xr_z0'], L['xr_z1'], 'riemen'),
            Quader('X-Riemen rechts', xw + rh_x1, L['x_rolle'], y0, y1,
                   L['xr_z0'], L['xr_z1'], 'riemen')]
