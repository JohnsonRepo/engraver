# ToolheadZ.py — kompletter Laser-Toolhead mit NEMA17-Z-Achse
#
# Baugruppe (vier gedruckte Teile), weil sich Teile relativ zueinander bewegen:
#   Traegerplatte   — geerdet, sitzt auf dem MGN15H-Wagen der Portalfuehrung,
#                     traegt die MGN9-Z-Schiene (Sockel) und die Motorkonsole
#   Motorhalter     — U-Konsole oben, traegt den NEMA 17 (Welle nach unten)
#   Schlittenplatte — auf dem MGN9H-Z-Wagen, traegt den Diodenlaser
#   Mutternblock    — zwei M6-Muttern mit Druckfeder gegeneinander verspannt,
#                     schwimmend an der Schlittenplatte verschraubt
#
# Koordinatensystem = Maschinenkoordinaten, global fuer alle Komponenten:
#   X = quer, laengs des Portals          Y = nach vorn, weg vom Portal
#   Z = senkrecht (Verfahrrichtung Z)     Ursprung = Mitte des X-Wagen-
#   Lochbildes AUF seiner Stirnflaeche (die Passflaeche der Traegerplatte).
#
# Alle Ebenen und Achsen leitet `lage()` aus MASSE ab — eine Quelle fuer
# Geometrie und fuer die Pruefung in tools/toolhead_check.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'ToolheadZ'
REVISION = 9

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Kaufteil: Portalfuehrung MGN15H (hardware.md [w]) ------------------
    # quer = senkrecht zur Schiene = Z, laengs = laengs der Schiene = X
    'x_wagen_loch_quer':   (25.0,  'MGN15H Wagen: Lochabstand in Z'),
    'x_wagen_loch_laengs': (25.0,  'MGN15H Wagen: Lochabstand in X'),
    'x_wagen_breite':      (32.0,  'MGN15H Wagen: Breite (in Z)'),
    'x_wagen_laenge':      (58.8,  'MGN15H Wagen: Laenge (in X)'),
    'x_wagen_hoehe':       (16.0,  'MGN15 Montagehoehe: Wagenflaeche ueber Profil'),
    'x_schiene_hoehe':     (10.0,  'MGN15 Schiene: Hoehe'),
    'x_gewinde_tiefe':     (4.0,   'MGN15 Wagen: M3-Gewindetiefe'),

    # --- Kaufteil: Z-Fuehrung MGN9H (hardware.md [w]) ----------------------
    # quer = X, laengs = Z (Schiene steht senkrecht)
    'z_wagen_loch_quer':   (15.0,  'MGN9H Wagen: Lochabstand in X'),
    'z_wagen_loch_laengs': (16.0,  'MGN9H Wagen: Lochabstand in Z'),
    'z_wagen_breite':      (20.0,  'MGN9H Wagen: Breite (in X)'),
    'z_wagen_laenge':      (39.9,  'MGN9H Wagen: Laenge (in Z)'),
    'z_wagen_hoehe':       (10.0,  'MGN9 Montagehoehe: Wagenflaeche ueber Sockel'),
    'z_schiene_breite':    (9.0,   'MGN9 Schiene: Breite'),
    'z_schiene_hoehe':     (6.5,   'MGN9 Schiene: Hoehe'),
    'z_schiene_laenge':    (95.0,  'MGN9 Schiene: Laenge (2*7,5 + 4*20)'),
    'z_schiene_lochab':    (20.0,  'MGN9 Schiene: Lochabstand'),
    'z_schiene_randab':    (7.5,   'MGN9 Schiene: Randabstand'),
    'z_schiene_senkung':   (3.3,   'MGN9 Schiene: Tiefe der Senkung'),
    'z_gewinde_tiefe':     (2.5,   'MGN9 Wagen: M3-Gewindetiefe'),

    # --- Kaufteil: NEMA 17 (hardware.md [w]) -------------------------------
    'motor_flansch':       (42.3,  'NEMA17: Flanschmass'),
    'motor_loch':          (31.0,  'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0,  'NEMA17: Zentrierbund Durchmesser'),
    'motor_bund_h':        (2.0,   'NEMA17: Zentrierbund Hoehe'),
    'motor_welle_l':       (24.0,  'NEMA17: Wellenlaenge'),
    'motor_laenge':        (40.0,  'NEMA17: Koerperlaenge (nur Freigang)'),

    # --- Kaufteil: Antrieb -------------------------------------------------
    'spindel_d':           (6.0,   'M6-Gewindestange: Nenndurchmesser'),
    'spindel_durchgang':   (6.6,   'M6 Durchgang (hardware.md)'),
    'kupplung_d':          (19.0,  'Flexible Kupplung 5->6: Durchmesser'),
    'kupplung_l':          (25.0,  'Flexible Kupplung 5->6: Laenge'),
    'kupplung_griff':      (12.0,  'Kupplung: Einstecktiefe je Seite'),
    'm6_mutter_sw':        (10.0,  'M6 Mutter: Schluesselweite (hardware.md)'),
    'm6_mutter_h':         (5.2,   'M6 Mutter: Hoehe (hardware.md)'),
    'feder_raum_l':        (11.0,  'Federkammer zwischen den beiden Muttern'),
    'feder_raum_d':        (10.0,  'Federkammer: Durchmesser'),

    # --- Kaufteil: Diodenlaser (Nutzerangabe + hardware.md) ----------------
    # 40,5 x 16,5 — am 2026-09-17 mit Bohrlehre_Laser (Ø3,4 Rundloecher) am
    # Modul geprueft und bestaetigt [v]. Dritte Messung an diesem Modul,
    # vorher 39 x 15 und 40 x 16.
    # Die Befestigungen sind weiterhin Langloecher. Der Grund dafuer ist jetzt
    # nicht mehr das unsichere Bohrbild, sondern nur noch Toleranzausgleich
    # (Schrumpf ueber 40,5 mm PETG). Rundloecher Ø4,0 wuerden auch reichen —
    # siehe docs/toolhead-z.md.
    'laser_loch_quer':     (16.5,  'Laser: Lochabstand quer (X)'),
    'laser_loch_hoch':     (40.5,  'Laser: Lochabstand senkrecht (Z)'),
    'laser_breite':        (35.0,  'Laser: Gehaeusebreite'),
    'laser_tiefe':         (35.0,  'Laser: Gehaeusetiefe — treibt die Strahlachse'),
    'laser_laenge':        (99.6,  'Laser: Gehaeuselaenge (senkrecht)'),
    'laser_loch_ab_unten': (4.5,   'Laser: untere Lochreihe ueber Gehaeuseunterkante'),

    # --- Normteile ---------------------------------------------------------
    'm3_durchgang':        (3.4,   'M3 Durchgang'),
    'm3_uebermass':        (4.6,   'M3 Durchgang mit Ausrichtspiel (Mutternblock)'),
    'm3_senkung':          (6.5,   'Freibohrung fuer M3-Zylinderkopf + Werkzeug'),
    'm3_mutter_sw':        (5.5,   'M3 Mutter: Schluesselweite'),
    'm3_mutter_h':         (2.4,   'M3 Mutter: Hoehe'),
    # Mutterntaschen bewusst enger als die Faustregel in hardware.md
    # (SW + 0,2..0,3): die Muttern sollen VOR dem Festschrauben von allein
    # sitzen. Falls eine Tasche zu stramm wird, hier erhoehen.
    'tasche_spiel':        (0.15,  'Mutterntasche: Spiel auf die Schluesselweite'),
    'tasche_klemmung':     (0.20,  'Mutterntasche: Untermass im Mundstueck'),
    'm3_scheibe_h':        (0.5,   'M3 Scheibe DIN 125: Dicke'),
    'insert_m3_d':         (4.0,   'ruthex M3: Einpressbohrung'),
    'insert_m3_t':         (7.0,   'ruthex M3: Sacklochtiefe'),

    # --- Traegerplatte -----------------------------------------------------
    'traeger_dicke':       (8.0,   'Traegerplatte: Dicke'),
    'traeger_x_links':    (-22.0,  'Traegerplatte: linke Kante'),
    'traeger_x_rechts':    (22.0,  'Traegerplatte: rechte Kante der Hauptsaeule'),
    'traeger_x_kopf':      (56.0,  'Traegerplatte: rechte Kante des Kopfbereichs'),
    'traeger_z_unten':    (-66.0,  'Traegerplatte: Unterkante'),
    'traeger_kopf_unten':  (44.0,  'Traegerplatte: Unterkante des Kopfbereichs'),
    'sockel_breite':        (9.0,  'Schienensockel: Breite = Schienenbreite!'),
    'sockel_hoehe':        (5.0,   'Schienensockel: Hoehe ueber der Plattenvorderseite'),

    # --- Lage der Spindelachse und der Motorkonsole ------------------------
    'spindel_x':           (30.0,  'Spindelachse: X (Abstand von der Schienenachse)'),
    # 28,5 statt 21: nur so liegt die hintere Motorschraubenreihe
     # (spindel_y - motor_loch/2) vor der Traegerplatte und ist von unten
     # erreichbar. Nach vorn begrenzt die Wand vor der Spindelbohrung im
     # Mutternblock (schlitten_y1 - spindel_y - spindel_durchgang/2 >= 3).
    'spindel_y':           (28.5,  'Spindelachse: Y ab X-Wagen-Stirnflaeche'),
    # Die Konsole ist Teil der Traegerplatte (ein Druckteil) — keine Laschen.
    'konsole_unten':       (68.0,  'Motorkonsole: Unterseite (= Oberkante Saeule)'),
    'konsole_dicke':       (8.0,   'Motorkonsole: Dicke'),
    'konsole_y_vorn':      (56.0,  'Motorkonsole: vordere Kante'),
    'konsole_rand':        (4.5,   'Motorkonsole: Rand neben den Fuehrungsrippen'),
    'motor_rippe_breite':  (3.0,   'Fuehrungsrippe am Motorflansch: Breite'),
    'motor_rippe_hoehe':   (3.0,   'Fuehrungsrippe: Hoehe ueber der Konsole'),
    'endschalter_x':      (-16.0,  'Endschalter-Befestigung: X (Platzhalter)'),

    # --- Schlittenplatte (Konzept aus ToolheadGrundplatte) -----------------
    # 12 statt 6: schiebt die Schlittenplatte so weit nach vorn, dass der
    # Mutternblock hinter ihr Platz hat, obwohl die Spindelachse bei 28,5 liegt.
    'pad_hoehe':           (12.0,  'Auflagepad: Versatz Wagenflaeche -> Platte'),
    # 30 statt 28: der Kopffreiraum sitzt jetzt bei X = +-8,25 und braucht
    # noch Wand zum Padrand.
    'pad_breite':          (30.0,  'Auflagepad: Breite'),
    'pad_laenge':          (26.0,  'Auflagepad: Hoehe'),
    'schlitten_dicke':     (6.0,   'Schlittenplatte: Dicke'),
    'schlitten_breite_l':  (17.5,  'Schlittenplatte: Kante links der Schienenachse'),
    'schlitten_rand':      (4.0,   'Schlittenplatte: Rand um das Lochfeld'),
    'rippe_mitte_breite':  (5.0,   'Mittelrippe: Breite'),
    # 13,5 statt 13: die Scheibe der Laserschraube (Ø9) wandert mit dem
    # Lochbild nach aussen und braucht Platz neben der Rippe.
    'rippe_seite_innen':   (13.5,  'Seitenrippe links: Innenkante'),
    # -laser_loch_hoch/2: die OBERE Laser-Schraubenreihe liegt damit genau auf
    # der Wagenmitte — mittig zwischen den beiden Wagen-Schraubenreihen (+-8),
    # sonst ueberschneiden sich Langloch und Freibohrung.
    'laser_versatz_z':   (-20.25,  'Laser-Lochbildmitte gegen die Wagenmitte'),
    'kopf_freiraum':       (10.0,  'Freiraum im Pad fuer Kopf+Scheibe der Laserschraube'),
    'schlitz_breite':      (4.4,   'Laser-Langloch: Breite'),
    'schlitz_verstellweg': (1.2,   'Laser-Langloch: Mittenversatz quer'),

    # --- Mutternblock ------------------------------------------------------
    'block_x_links':       (16.0,  'Mutternblock: linke Kante'),
    'block_x_rechts':      (44.0,  'Mutternblock: rechte Kante'),
    'block_y_hinten':      (18.0,  'Mutternblock: hintere Kante'),
    'block_hoehe':         (26.0,  'Mutternblock: Hoehe'),
    'block_boden':         (2.0,   'Mutternblock: Boden/Decke unter der Mutter'),

    # --- Druckgerecht + Freigaenge -----------------------------------------
    'luft_bau':            (3.0,   'Mindestfreigang zwischen bewegten Teilen'),
    'fase_fuss':           (0.4,   'Fase gegen Elefantenfuss an Auflageflaechen'),
    'spiel_locker':        (0.4,   'Montagespiel, diametral'),
    'lehre_dicke':         (3.0,   'Bohrlehren: Plattendicke'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def c(name):
    """Wert in cm (API-Einheit fuer Point3D)."""
    return MASSE[name][0] / 10.0


def lage():
    """Alle abgeleiteten Ebenen, Achsen und Verfahrgrenzen in globalen
    Maschinenkoordinaten (mm). Einzige Quelle fuer Geometrie UND Pruefung."""
    L = {}

    # ---- Y-Kette: vom Portal nach vorn --------------------------------------
    L['portal_y'] = -w('x_wagen_hoehe')                      # Profilflaeche
    L['x_schiene_y'] = -w('x_wagen_hoehe') + w('x_schiene_hoehe')
    L['traeger_y0'] = 0.0                                    # = X-Wagen-Stirnflaeche
    L['traeger_y1'] = w('traeger_dicke')
    L['sockel_y1'] = L['traeger_y1'] + w('sockel_hoehe')     # Auflage der Z-Schiene
    L['z_schiene_y1'] = L['sockel_y1'] + w('z_schiene_hoehe')
    L['z_wagen_y'] = L['sockel_y1'] + w('z_wagen_hoehe')     # Stirnflaeche Z-Wagen
    L['schlitten_y0'] = L['z_wagen_y']
    L['schlitten_y1'] = L['z_wagen_y'] + w('pad_hoehe')      # Rueckseite Platte
    L['laser_y'] = L['schlitten_y1'] + w('schlitten_dicke')  # Anschraubflaeche
    L['laser_vorn_y'] = L['laser_y'] + w('laser_tiefe')
    L['strahl_y'] = L['laser_y'] + w('laser_tiefe') / 2.0

    # ---- Z-Kette: Schiene, Wagen, Kupplung, Motor ---------------------------
    L['z_schiene_ueberstand'] = 6.0        # Schienenende ueber der Plattenunterkante
    L['z_schiene_z0'] = w('traeger_z_unten') + L['z_schiene_ueberstand']
    L['z_schiene_z1'] = L['z_schiene_z0'] + w('z_schiene_laenge')
    L['konsole_z0'] = w('konsole_unten')
    L['konsole_z1'] = L['konsole_z0'] + w('konsole_dicke')
    L['motor_flansch_z'] = L['konsole_z1']                   # Motor sitzt oben auf
    L['motor_z1'] = L['motor_flansch_z'] + w('motor_laenge')
    L['welle_z0'] = L['motor_flansch_z'] - w('motor_welle_l')
    L['kupplung_z1'] = L['welle_z0'] + w('kupplung_griff')
    L['kupplung_z0'] = L['kupplung_z1'] - w('kupplung_l')
    L['spindel_z1'] = L['welle_z0']                          # Oberkante Gewindestange

    # ---- Schlittenplatte und Laser, relativ zur Wagenmitte zc ---------------
    lochmitte = w('laser_versatz_z')                         # Lochbildmitte ueber zc
    L['laser_loch_unten_rel'] = lochmitte - w('laser_loch_hoch') / 2.0
    L['laser_loch_oben_rel'] = lochmitte + w('laser_loch_hoch') / 2.0
    L['laser_unten_rel'] = L['laser_loch_unten_rel'] - w('laser_loch_ab_unten')
    L['laser_oben_rel'] = L['laser_unten_rel'] + w('laser_laenge')
    L['schlitten_oben_rel'] = w('pad_laenge') / 2.0 + w('schlitten_rand')
    L['schlitten_unten_rel'] = L['laser_loch_unten_rel'] \
        - w('schlitz_breite') / 2.0 - w('schlitten_rand')
    L['block_oben_rel'] = w('block_hoehe') / 2.0
    L['block_unten_rel'] = -w('block_hoehe') / 2.0

    # ---- Verfahrgrenzen: jede Begrenzung einzeln, damit sichtbar bleibt,
    #      welche bindet ------------------------------------------------------
    luft = w('luft_bau')
    L['zc_min'] = L['z_schiene_z0'] + w('z_wagen_laenge') / 2.0
    grenzen = {
        'Schiene (Wagen am obersten Ende)':
            L['z_schiene_z1'] - w('z_wagen_laenge') / 2.0,
        'Laser-Oberkante gegen Motorkonsole':
            L['konsole_z0'] - luft - L['laser_oben_rel'],
        'Schlittenplatte gegen Kupplung':
            L['kupplung_z0'] - luft - L['schlitten_oben_rel'],
        'Mutternblock gegen Kupplung':
            L['kupplung_z0'] - luft - L['block_oben_rel'],
    }
    L['zc_grenzen'] = grenzen
    L['zc_max'] = min(grenzen.values())
    L['zc_bindend'] = min(grenzen, key=lambda k: grenzen[k])
    L['z_weg'] = L['zc_max'] - L['zc_min']

    # ---- Schraubenlaenge Schlittenplatte -> Z-Wagen -------------------------
    # Naechste gerade Laenge ueber pad_hoehe + Mindesteingriff. Nicht
    # verdrahten: sie muss mit pad_hoehe mitwandern, sonst passt sie nach einer
    # Parameteraenderung stillschweigend nicht mehr.
    L['z_wagen_schraube'] = 2.0 * int((w('pad_hoehe') + 1.5) / 2.0 + 0.999)
    L['z_wagen_eingriff'] = L['z_wagen_schraube'] - w('pad_hoehe')

    # ---- Benoetigte Laenge der Gewindestange --------------------------------
    L['spindel_z0'] = L['zc_min'] + L['block_unten_rel'] - 5.0
    L['spindel_laenge'] = L['spindel_z1'] - L['spindel_z0']

    # ---- Lochbilder (absolute Lagen, X/Z) -----------------------------------
    L['x_wagen_loecher'] = [
        (sx * w('x_wagen_loch_laengs') / 2.0, sz * w('x_wagen_loch_quer') / 2.0)
        for sx in (-1, 1) for sz in (-1, 1)]
    n = int(round((w('z_schiene_laenge') - 2 * w('z_schiene_randab'))
                  / w('z_schiene_lochab'))) + 1
    L['z_schiene_loecher'] = [
        L['z_schiene_z0'] + w('z_schiene_randab') + i * w('z_schiene_lochab')
        for i in range(n)]
    # Motorkonsole: Teil der Traegerplatte, kein eigenes Bauteil.
    L['konsole_x0'] = w('spindel_x') - w('motor_flansch') / 2.0 - w('konsole_rand')
    L['konsole_x1'] = w('spindel_x') + w('motor_flansch') / 2.0 + w('konsole_rand')

    # Der Motor wird von UNTEN verschraubt — NEMA17 hat Gewinde im Flansch, ein
    # Durchstecken von oben ist nicht moeglich. Beide Schraubenreihen liegen
    # jetzt vor der Traegerplatte, es sind also alle VIER erreichbar. Die
    # Fuehrungsrippen bleiben: der Motor findet damit beim Einsetzen selbst
    # seine Lage und die Schrauben muessen kein Moment uebertragen.
    # Pruefung der Zugangskorridore: tools/toolhead_check.py.
    innen = w('motor_flansch') / 2.0 + w('spiel_locker') / 2.0
    L['motor_rippe_x'] = [
        (w('spindel_x') - innen - w('motor_rippe_breite'),
         w('spindel_x') - innen),
        (w('spindel_x') + innen,
         w('spindel_x') + innen + w('motor_rippe_breite'))]
    L['motor_rippe_y1'] = w('spindel_y') + w('motor_flansch') / 2.0
    L['motor_rippe_z1'] = L['konsole_z1'] + w('motor_rippe_hoehe')
    L['motor_schrauben'] = [
        (w('spindel_x') + sx * w('motor_loch') / 2.0,
         w('spindel_y') + sy * w('motor_loch') / 2.0)
        for sy in (-1, 1) for sx in (-1, 1)]
    # Freie Luft zwischen dem Zugangskorridor der hinteren Reihe und der
    # Vorderseite der Traegerplatte — die Groesse, die spindel_y bestimmt.
    L['korridor_luft'] = (w('spindel_y') - w('motor_loch') / 2.0
                          - 3.0 - w('traeger_dicke'))
    L['endschalter_z'] = [20.0, 40.0]

    # Lochbild des Z-Wagens, relativ zur Wagenmitte zc
    L['z_wagen_loecher'] = [
        (sx * w('z_wagen_loch_quer') / 2.0, sz * w('z_wagen_loch_laengs') / 2.0)
        for sx in (-1, 1) for sz in (-1, 1)]
    # Schwimmende Verschraubung des Mutternblocks, links und rechts der Tasche.
    # 5 mm Randabstand: die Sechskanttasche der M3-Mutter ist ueber Eck 6,5 mm
    # breit und braucht noch Wand zum Blockrand.
    L['block_schraube_x'] = [w('block_x_links') + 5.0, w('block_x_rechts') - 5.0]

    L['motor_loecher'] = [
        (w('spindel_x') + sx * w('motor_loch') / 2.0,
         w('spindel_y') + sy * w('motor_loch') / 2.0)
        for sx in (-1, 1) for sy in (-1, 1)]
    return L


# --- Materialien (Standardblock, siehe SKILL.md) -----------------------------
EIGENE_MATERIALIEN = {
    'PLA':  ('ABS Plastic', 1.06, 1.24),
    'PETG': ('ABS Plastic', 1.06, 1.27),
}


def material_zuweisen(app, design, ziel, name):
    """Setzt das physikalische Material auf `ziel` (BRepBody oder Component)."""
    mat = design.materials.itemByName(name)
    if not mat and name in EIGENE_MATERIALIEN:
        basis_name, d_basis, d_ziel = EIGENE_MATERIALIEN[name]
        basis = _bibliotheksmaterial(app, basis_name)
        if basis:
            mat = design.materials.addByCopy(basis, name)
            prop = adsk.core.FloatProperty.cast(
                mat.materialProperties.itemByName('Density'))
            prop.value *= d_ziel / d_basis      # relativ skalieren, einheitenfrei
    if not mat:
        gefunden = _bibliotheksmaterial(app, name)
        mat = design.materials.addByCopy(gefunden, name) if gefunden else None
    if mat:
        ziel.material = mat
    return mat        # None = nicht gefunden -> Fusion-Default bleibt, kein Abbruch


def _bibliotheksmaterial(app, name):
    """Alle Materialbibliotheken durchsuchen: erst exakter Name, dann Teilstring."""
    libs = app.materialLibraries
    for k in range(libs.count):
        m = libs.item(k).materials.itemByName(name)
        if m:
            return m
    nl = name.lower()
    for k in range(libs.count):
        mats = libs.item(k).materials
        for i in range(mats.count):
            if nl in mats.item(i).name.lower():
                return mats.item(i)
    return None


# --- Validierung (Standardblock, siehe SKILL.md) ------------------------------
def validierungs_bericht(app, design, ui, hinweise=None):
    """Meldet am Skriptende alle Koerper mit Masse und Abmessungen per
    messageBox. Scheitert nie — Validierung darf das Skript nicht abbrechen."""
    try:
        zeilen = ['{} (Rev. {})'.format(SKRIPT_NAME, REVISION), '']
        comps = design.allComponents
        for k in range(comps.count):
            comp = comps.item(k)
            for i in range(comp.bRepBodies.count):
                b = comp.bRepBodies.item(i)
                bb = b.boundingBox
                gr = ((bb.maxPoint.x - bb.minPoint.x) * 10,
                      (bb.maxPoint.y - bb.minPoint.y) * 10,
                      (bb.maxPoint.z - bb.minPoint.z) * 10)
                praefix = '' if comps.count == 1 else comp.name + ' > '
                status = '' if b.isLightBulbOn else '  [ausgeblendet]'
                zeilen.append('{}{}: {:.1f} g, {:.0f} x {:.0f} x {:.0f} mm{}'.format(
                    praefix, b.name, b.physicalProperties.mass * 1000,
                    gr[0], gr[1], gr[2], status))
        if hinweise:
            zeilen += [''] + list(hinweise)
        ui.messageBox('\n'.join(zeilen), 'Validierung')
    except:
        pass


# --- Geometrie-Helfer --------------------------------------------------------
def _offsetebene(comp, basis, ziel_cm, achse, name):
    """Offsetebene, deren Lage nachgemessen und bei falschem Vorzeichen
    korrigiert wird. In welche Richtung die Normale der Fusion-Basisebenen
    zeigt, ist nicht verlaesslich vorhersagbar — nachmessen ist billiger als
    raten. `achse` ist die Modellachse, auf der die Ebene liegen soll."""
    if abs(ziel_cm) < 1e-9:
        return basis
    for vorzeichen in (1.0, -1.0):
        ein = comp.constructionPlanes.createInput()
        ein.setByOffset(basis, adsk.core.ValueInput.createByReal(
            vorzeichen * ziel_cm))
        pl = comp.constructionPlanes.add(ein)
        if abs(getattr(pl.geometry.origin, achse) - ziel_cm) < 1e-6:
            pl.name = name
            return pl
        pl.deleteMe()
    raise RuntimeError('Ebene {} laesst sich nicht auf {:.3f} cm legen'.format(
        name, ziel_cm))


def ebene_y(comp, y_mm, name):
    """Konstruktionsebene senkrecht zu Maschinen-Y (Plattenebene).
    Skizzenkoordinaten darauf sind (Maschine X, Maschine Z)."""
    if abs(y_mm) < 1e-9:
        return comp.xYConstructionPlane
    # Modell-Z entspricht Maschine Y
    return _offsetebene(comp, comp.xYConstructionPlane, y_mm / 10.0, 'z', name)


def ebene_z(comp, z_mm, name):
    """Konstruktionsebene senkrecht zu Maschinen-Z (waagerecht).
    Skizzenkoordinaten darauf sind (Maschine X, Maschine Y)."""
    # Modell-Y entspricht Maschine Z
    return _offsetebene(comp, comp.xZConstructionPlane, z_mm / 10.0, 'y', name)


def skizze(comp, ebene, name):
    sk = comp.sketches.add(ebene)
    sk.name = name
    return sk


def _ebene_info(sk):
    """Welche beiden Maschinenachsen liegen in der Ebene dieser Skizze, und wo
    liegt die Ebene? Liefert (feste Achse, Wert in mm). Wird aus der echten
    Ebenengeometrie gelesen, nicht angenommen."""
    pl = adsk.core.Plane.cast(sk.referencePlane.geometry)
    if abs(pl.normal.z) > 0.9:       # Modell-Z = Maschine Y
        return 'y', pl.origin.z * 10.0
    return 'z', pl.origin.y * 10.0   # Modell-Y = Maschine Z


def punkt(sk, u_mm, v_mm):
    """Punkt in Maschinenkoordinaten -> Skizzenkoordinaten (cm).
    u ist immer Maschine X; v ist Maschine Z bei senkrechten Ebenen und
    Maschine Y bei waagerechten. Der Umweg ueber modelToSketchSpace macht das
    Ergebnis unabhaengig davon, wie Fusion die Achsen der Ebene orientiert —
    eine gespiegelte Skizze wuerde sonst ohne Fehlermeldung durchgehen."""
    fest, wert = _ebene_info(sk)
    if fest == 'y':                  # Ebene bei konstantem Maschinen-Y
        modell = adsk.core.Point3D.create(u_mm / 10.0, v_mm / 10.0, wert / 10.0)
    else:                            # Ebene bei konstantem Maschinen-Z
        modell = adsk.core.Point3D.create(u_mm / 10.0, wert / 10.0, v_mm / 10.0)
    sp = sk.modelToSketchSpace(modell)
    return adsk.core.Point3D.create(sp.x, sp.y, 0)


def rechteck(sk, u0, v0, u1, v1):
    """Achsparalleles Rechteck, Angaben in Maschinenkoordinaten (mm)."""
    return sk.sketchCurves.sketchLines.addTwoPointRectangle(
        punkt(sk, u0, v0), punkt(sk, u1, v1))


def kreis(sk, u, v, d_mm):
    return sk.sketchCurves.sketchCircles.addByCenterRadius(
        punkt(sk, u, v), d_mm / 20.0)


def langloch(sk, cu, cv, halb_versatz, radius):
    """Langloch als zwei Kreise plus Rechteck, Masse in mm. Beim Schneiden
    werden ALLE Profile der Skizze entfernt; die Vereinigung ergibt das
    Langloch. Robuster als ein aus Linien und Boegen zusammengesetztes
    Profil, das bei Rundungsfehlern nicht schliesst.
    """
    kreis(sk, cu - halb_versatz, cv, 2 * radius)
    kreis(sk, cu + halb_versatz, cv, 2 * radius)
    rechteck(sk, cu - halb_versatz, cv - radius,
             cu + halb_versatz, cv + radius)


def sechskant(sk, cu, cv, sw, flach_quer=True):
    """Regelmaessiges Sechskant ueber die Schluesselweite sw (Abstand der
    parallelen Flanken), Masse in mm.

    flach_quer=True: zwei Flanken stehen senkrecht zur v-Achse. Die Mutter wird
    dann in v-Richtung eingeschoben und liegt am Taschenboden mit einer FLANKE
    an, nicht mit einer Ecke — sie kann nicht kippen und sitzt formschluessig
    auf allen sechs Flanken.

    Die Ecken werden ueber die SketchPoints der Nachbarlinien verkettet, damit
    das Profil sicher schliesst.
    """
    r = sw / math.sqrt(3.0)                      # Umkreisradius
    start = 0.0 if flach_quer else 30.0
    ecken = [(cu + r * math.cos(math.radians(start + i * 60.0)),
              cv + r * math.sin(math.radians(start + i * 60.0)))
             for i in range(6)]
    linien = sk.sketchCurves.sketchLines
    erste = linien.addByTwoPoints(punkt(sk, *ecken[0]), punkt(sk, *ecken[1]))
    vorher = erste
    for i in range(1, 5):
        vorher = linien.addByTwoPoints(vorher.endSketchPoint,
                                       punkt(sk, *ecken[i + 1]))
    linien.addByTwoPoints(vorher.endSketchPoint, erste.startSketchPoint)
    return erste


def groesstes_profil(sk):
    """Flaechengroesstes Profil einer Skizze (nie blind profiles.item(0))."""
    return max((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: p.areaProperties().area)


def alle_profile(sk):
    coll = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        coll.add(sk.profiles.item(i))
    return coll


def extrudieren(comp, prof, hoehe_mm, operation, ziel=None):
    ein = comp.features.extrudeFeatures.createInput(prof, operation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(hoehe_mm / 10.0))
    if ziel is not None:
        ein.participantBodies = [ziel]
    return comp.features.extrudeFeatures.add(ein)


def neu(comp, prof, hoehe_mm):
    return extrudieren(comp, prof, hoehe_mm,
                       adsk.fusion.FeatureOperations.NewBodyFeatureOperation)


def dazu(comp, prof, hoehe_mm, ziel):
    return extrudieren(comp, prof, hoehe_mm,
                       adsk.fusion.FeatureOperations.JoinFeatureOperation, ziel)


def weg(comp, prof, hoehe_mm, ziel):
    return extrudieren(comp, prof, hoehe_mm,
                       adsk.fusion.FeatureOperations.CutFeatureOperation, ziel)


def _symmetrisch(comp, prof, laenge_mm, operation, ziel=None):
    """Extrusion symmetrisch um die Skizzenebene: `laenge_mm` ist die
    Gesamtlaenge, die Ebene liegt in der Mitte. Damit ist die Richtung der
    Ebenennormale irrelevant — ein einseitiger Schnitt bricht sonst mit
    EXTRUDE_ZERO_DISTANCE_ERROR ab, sobald die Normale vom Material wegzeigt."""
    ein = comp.features.extrudeFeatures.createInput(prof, operation)
    ein.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(laenge_mm / 10.0), True)
    if ziel is not None:
        ein.participantBodies = [ziel]
    return comp.features.extrudeFeatures.add(ein)


def neu_mittig(comp, prof, dicke_mm):
    """Neuer Koerper, symmetrisch um die Skizzenebene."""
    return _symmetrisch(comp, prof, dicke_mm,
                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)


def tasche(comp, prof, tiefe_mm, ziel):
    """Tasche symmetrisch um die Skizzenebene (Ebene = Taschenmitte)."""
    return _symmetrisch(comp, prof, tiefe_mm,
                        adsk.fusion.FeatureOperations.CutFeatureOperation, ziel)


def durch(comp, prof, ziel, reichweite_mm=400.0):
    """Durchgangsschnitt: symmetrisch und grosszuegig statt ThroughAll, damit
    die Normalenrichtung der Skizzenebene keine Rolle spielt. participantBodies
    begrenzt die Wirkung auf den Zielkoerper."""
    return tasche(comp, prof, reichweite_mm, ziel)


def kanten_bei(koerper, achse, wert_cm, toleranz=1e-4):
    """Kanten aller ebenen Flaechen, deren Schwerpunkt auf achse == wert liegt.
    achse: 'x' | 'y' | 'z' im MODELL (Modell-Z = Maschine Y)."""
    kanten = adsk.core.ObjectCollection.create()
    gesehen = set()
    flaechen = []
    for i in range(koerper.faces.count):
        f = koerper.faces.item(i)
        if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        if abs(getattr(f.centroid, achse) - wert_cm) < toleranz:
            flaechen.append(f)
    for f in flaechen:
        for i in range(f.edges.count):
            k = f.edges.item(i)
            if k.tempId not in gesehen:
                gesehen.add(k.tempId)
                kanten.add(k)
    return kanten


def bbox_pruefen(koerper, name, erwartet, fehler, toleranz=0.8):
    """Vergleicht die Bounding Box mit dem erwarteten Bauraum in
    Maschinenkoordinaten. Noetig, weil eine anders orientierte Skizzenachse in
    Fusion keinen Fehler wirft — ein falsch platziertes Teil wuerde sonst
    unbemerkt durchgehen. erwartet: ((x0,x1),(y0,y1),(z0,z1)) in mm."""
    bb = koerper.boundingBox
    # Modell -> Maschine: X=x, Y=z, Z=y (cm -> mm)
    ist = ((bb.minPoint.x * 10, bb.maxPoint.x * 10),
           (bb.minPoint.z * 10, bb.maxPoint.z * 10),
           (bb.minPoint.y * 10, bb.maxPoint.y * 10))
    for achse, i, e in zip('XYZ', ist, erwartet):
        if abs(i[0] - e[0]) > toleranz or abs(i[1] - e[1]) > toleranz:
            fehler.append('{}: {} liegt {:.1f}..{:.1f}, erwartet {:.1f}..{:.1f}'
                          .format(name, achse, i[0], i[1], e[0], e[1]))


def fussfase(comp, koerper, achse, wert_mm, fase_mm, fehler, was):
    """Fase gegen den Elefantenfuss an der Auflageflaeche. Ohne sie hebt die
    aufgequollene erste Druckschicht das Teil von der Passflaeche ab."""
    try:
        kanten = kanten_bei(koerper, achse, wert_mm / 10.0)
        if not kanten.count:
            fehler.append('{}: keine Flaeche fuer die Fussfase'.format(was))
            return
        ein = comp.features.chamferFeatures.createInput2()
        ein.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            kanten, adsk.core.ValueInput.createByReal(fase_mm / 10.0), True)
        comp.features.chamferFeatures.add(ein)
    except:
        fehler.append('{}: Fussfase uebersprungen — Auflageflaeche pruefen!'
                      .format(was))


# --- Bauteile ----------------------------------------------------------------
def bau_traegerplatte(app, design, comp, L, fehler):
    """Traegerplatte MIT angeformter Motorkonsole — ein Druckteil.

    Ein separater Motorhalter brachte keinen Vorteil: die hintere
    Schraubenreihe des NEMA 17 liegt ueber dem Querschnitt der Platte und ist
    von unten so oder so nicht erreichbar. Angeformt entfaellt dafuer die
    Verschraubung Halter/Platte vollstaendig, und die Konsole wird steifer.

    Der Motor sitzt oben auf der Konsole (Welle nach unten durch die
    Bundbohrung), gehalten von der vorderen Schraubenreihe und zwei
    Fuehrungsrippen, die den Flansch seitlich fassen und das Motormoment
    formschluessig aufnehmen.

    Drucklage: Rueckseite (Passflaeche) aufs Bett, Aufbaurichtung = Maschine Y.
    Platte, Sockel, Konsole und Rippen stehen dann alle auf dem Bett — kein
    Stuetzmaterial, und alle Kraefte liegen in der Schicht."""
    e_hinten = ebene_y(comp, 0.0, 'E_Traeger_hinten')
    e_vorn = ebene_y(comp, L['traeger_y1'], 'E_Traeger_vorn')
    e_sockel = ebene_y(comp, L['sockel_y1'], 'E_Sockel_vorn')
    e_konsole = ebene_z(comp, (L['konsole_z0'] + L['konsole_z1']) / 2.0,
                        'E_Konsole_mitte')

    sk = skizze(comp, e_hinten, 'Sk_Hauptsaeule')
    rechteck(sk, w('traeger_x_links'), w('traeger_z_unten'),
             w('traeger_x_rechts'), w('traeger_kopf_unten'))
    koerper = neu(comp, groesstes_profil(sk), w('traeger_dicke')).bodies.item(0)
    koerper.name = 'Traegerplatte'

    # Kopfbereich: verbreitert sich nach rechts und traegt die Konsole
    sk = skizze(comp, e_hinten, 'Sk_Kopfbereich')
    rechteck(sk, w('traeger_x_links'), w('traeger_kopf_unten'),
             w('traeger_x_kopf'), L['konsole_z0'])
    dazu(comp, groesstes_profil(sk), w('traeger_dicke'), koerper)

    # Motorkonsole: waagerechte Platte, kragt nach vorn aus
    sk = skizze(comp, e_hinten, 'Sk_Motorkonsole')
    rechteck(sk, L['konsole_x0'], L['konsole_z0'], L['konsole_x1'],
             L['konsole_z1'])
    dazu(comp, groesstes_profil(sk), w('konsole_y_vorn'), koerper)

    # Fuehrungsrippen: fassen den Motorflansch links und rechts
    sk = skizze(comp, e_hinten, 'Sk_Fuehrungsrippen')
    for x0, x1 in L['motor_rippe_x']:
        rechteck(sk, x0, L['konsole_z1'], x1, L['motor_rippe_z1'])
    dazu(comp, alle_profile(sk), L['motor_rippe_y1'], koerper)

    # Schienensockel: genau so breit wie die Schiene, damit die Schuerzen des
    # Wagens frei laufen; 5 mm hoch, damit die M3-Inserts 7 mm tief sitzen.
    sk = skizze(comp, e_vorn, 'Sk_Schienensockel')
    rechteck(sk, -w('sockel_breite') / 2, L['z_schiene_z0'],
             w('sockel_breite') / 2, L['z_schiene_z1'])
    dazu(comp, groesstes_profil(sk), w('sockel_hoehe'), koerper)

    # Verschraubung zum X-Wagen (Kopf liegt frei vor der Platte)
    sk = skizze(comp, e_hinten, 'Sk_Bohrungen_XWagen')
    for x, z in L['x_wagen_loecher']:
        kreis(sk, x, z, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Sacklochbohrungen fuer die Gewindeeinsaetze der Z-Schiene: von der
    # Sockelflaeche NACH HINTEN, deshalb negative Extrusion.
    sk = skizze(comp, e_sockel, 'Sk_Inserts_Schiene')
    for z in L['z_schiene_loecher']:
        kreis(sk, 0.0, z, w('insert_m3_d'))
    weg(comp, alle_profile(sk), -w('insert_m3_t'), koerper)

    # Bundbohrung und die beiden erreichbaren Motorschrauben
    sk = skizze(comp, e_konsole, 'Sk_Motorbefestigung')
    kreis(sk, w('spindel_x'), w('spindel_y'),
          w('motor_bund_d') + w('spiel_locker'))
    for x, y in L['motor_schrauben']:
        kreis(sk, x, y, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Universalbefestigung fuer einen Z-Endschalter — Lochbild ist ein
    # Platzhalter, an den eigenen Schalter anpassen.
    sk = skizze(comp, e_hinten, 'Sk_Endschalter')
    for z in L['endschalter_z']:
        kreis(sk, w('endschalter_x'), z, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    fussfase(comp, koerper, 'z', 0.0, w('fase_fuss'), fehler, 'Traegerplatte')
    bbox_pruefen(koerper, 'Traegerplatte',
                 ((w('traeger_x_links'), w('traeger_x_kopf')),
                  (L['traeger_y0'], w('konsole_y_vorn')),
                  (w('traeger_z_unten'), L['motor_rippe_z1'])), fehler)
    material_zuweisen(app, design, koerper, 'PETG')
    return koerper


def bau_schlittenplatte(app, design, comp, L, zc, fehler):
    """Auf dem MGN9H-Z-Wagen: Auflagepad + Rippen, davor die Platte mit dem
    Laser-Lochbild, rechts eine Lasche fuer den Mutternblock.
    Drucklage: Laser-Anschraubflaeche aufs Bett, Aufbaurichtung = -Maschine Y
    (im Slicer spiegeln/drehen), oder Pad-Rueckseite unten mit Stuetzen."""
    e_pad = ebene_y(comp, L['schlitten_y0'], 'E_Pad_hinten')
    e_platte = ebene_y(comp, L['schlitten_y1'], 'E_Platte_hinten')
    z_u = zc + L['schlitten_unten_rel']
    z_o = zc + L['schlitten_oben_rel']

    sk = skizze(comp, e_pad, 'Sk_Auflagepad')
    rechteck(sk, -w('pad_breite') / 2, zc - w('pad_laenge') / 2,
             w('pad_breite') / 2, zc + w('pad_laenge') / 2)
    koerper = neu(comp, groesstes_profil(sk), w('pad_hoehe')).bodies.item(0)
    koerper.name = 'Schlittenplatte'

    sk = skizze(comp, e_pad, 'Sk_Mittelrippe')
    rechteck(sk, -w('rippe_mitte_breite') / 2, z_u,
             w('rippe_mitte_breite') / 2, z_o)
    dazu(comp, groesstes_profil(sk), w('pad_hoehe'), koerper)

    # Nur links eine Seitenrippe — rechts sitzt der Mutternblock.
    sk = skizze(comp, e_pad, 'Sk_Seitenrippe')
    rechteck(sk, -w('schlitten_breite_l'), z_u, -w('rippe_seite_innen'), z_o)
    dazu(comp, groesstes_profil(sk), w('pad_hoehe'), koerper)

    sk = skizze(comp, e_platte, 'Sk_Platte')
    rechteck(sk, -w('schlitten_breite_l'), z_u, w('schlitten_breite_l'), z_o)
    dazu(comp, groesstes_profil(sk), w('schlitten_dicke'), koerper)

    sk = skizze(comp, e_platte, 'Sk_Lasche_Mutternblock')
    rechteck(sk, w('schlitten_breite_l'), zc - w('block_hoehe') / 2 - 3.0,
             w('block_x_rechts'), zc + w('block_hoehe') / 2 + 3.0)
    dazu(comp, groesstes_profil(sk), w('schlitten_dicke'), koerper)

    # Verschraubung zum Z-Wagen: Durchgang im Pad, Freibohrung in der Platte
    sk = skizze(comp, e_pad, 'Sk_Bohrungen_ZWagen')
    for x, z in L['z_wagen_loecher']:
        kreis(sk, x, zc + z, w('m3_durchgang'))
    weg(comp, alle_profile(sk), w('pad_hoehe') + w('schlitten_dicke'), koerper)

    sk = skizze(comp, e_platte, 'Sk_Freibohrungen_ZWagen')
    for x, z in L['z_wagen_loecher']:
        kreis(sk, x, zc + z, w('m3_senkung'))
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    # Freiraum im Pad fuer Kopf + Scheibe der OBEREN Laserschraubenreihe:
    # nur durch das Pad, damit die Scheibenauflage an der Platte stehen bleibt.
    sk = skizze(comp, e_pad, 'Sk_Kopffreiraum_Laser')
    for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2):
        kreis(sk, x, zc + L['laser_loch_oben_rel'], w('kopf_freiraum'))
    weg(comp, alle_profile(sk), w('pad_hoehe'), koerper)

    # Laser: Langloecher quer, weil das Bohrbild noch nicht verifiziert ist
    sk = skizze(comp, e_platte, 'Sk_Langloecher_Laser')
    for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2):
        for rel in (L['laser_loch_oben_rel'], L['laser_loch_unten_rel']):
            langloch(sk, x, zc + rel, w('schlitz_verstellweg') / 2,
                     w('schlitz_breite') / 2)
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    # Schwimmende Verschraubung des Mutternblocks: Uebermass zum Ausrichten
    sk = skizze(comp, e_platte, 'Sk_Bohrungen_Mutternblock')
    for x in L['block_schraube_x']:
        kreis(sk, x, zc, w('m3_uebermass'))
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    fussfase(comp, koerper, 'z', L['schlitten_y0'], w('fase_fuss'), fehler,
             'Schlittenplatte')
    bbox_pruefen(koerper, 'Schlittenplatte',
                 ((-w('schlitten_breite_l'), w('block_x_rechts')),
                  (L['schlitten_y0'], L['laser_y']), (z_u, z_o)), fehler)
    material_zuweisen(app, design, koerper, 'PETG')
    return koerper


def bau_mutternblock(app, design, comp, L, zc, fehler):
    """Zwei M6-Muttern, von einer Druckfeder gegeneinander verspannt: die eine
    liegt auf dem Boden, die andere unter der Decke, die Feder drueckt sie
    auseinander. Damit tragen die Gewindeflanken gegenlaeufig — kein Spiel.
    Drucklage: Unterseite aufs Bett, Aufbaurichtung = Maschine Z, damit die
    Spindelbohrung rund wird."""
    e_mitte = ebene_z(comp, zc, 'E_Block_mitte')
    e_hinten = ebene_y(comp, w('block_y_hinten'), 'E_Block_hinten')
    sx, sy = w('spindel_x'), w('spindel_y')

    sk = skizze(comp, e_mitte, 'Sk_Block')
    rechteck(sk, w('block_x_links'), w('block_y_hinten'),
             w('block_x_rechts'), L['schlitten_y1'])
    koerper = neu_mittig(comp, groesstes_profil(sk),
                         w('block_hoehe')).bodies.item(0)
    koerper.name = 'Mutternblock'

    sk = skizze(comp, e_mitte, 'Sk_Spindelbohrung')
    kreis(sk, sx, sy, w('spindel_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Mutterntaschen fuer die beiden M6-Muttern: Sechskant mit einer Flanke am
    # Taschenboden, davor ein etwas engeres Mundstueck. Die Mutter wird einmal
    # hineingedrueckt, rastet hinter der Stufe ein und kann danach nicht mehr
    # herausfallen — auch nicht, bevor die Schlittenplatte die Tasche
    # verschliesst. Im Sechskant selbst hat sie Spiel und bleibt in Z
    # beweglich, sonst koennte die Feder sie nicht gegen Boden bzw. Decke
    # druecken. Jede Tasche wird um ihre eigene Mittelebene geschnitten.
    tiefe = w('m6_mutter_h') + 0.3
    sw = w('m6_mutter_sw') + w('tasche_spiel')
    flanke = sw / 2.0                             # halbe Schluesselweite
    mund = 2.0 * w('m6_mutter_sw') / math.sqrt(3.0) - w('tasche_klemmung')
    versatz = w('feder_raum_l') / 2 + tiefe / 2
    for name, z_mitte in (('unten', zc - versatz), ('oben', zc + versatz)):
        sk = skizze(comp, ebene_z(comp, z_mitte, 'E_Tasche_' + name),
                    'Sk_Mutterntasche_' + name)
        sechskant(sk, sx, sy, sw, flach_quer=True)
        rechteck(sk, sx - mund / 2, sy + flanke, sx + mund / 2,
                 L['schlitten_y1'])
        tasche(comp, alle_profile(sk), tiefe, koerper)

    sk = skizze(comp, e_mitte, 'Sk_Federkammer')
    kreis(sk, sx, sy, w('feder_raum_d'))
    tasche(comp, groesstes_profil(sk), w('feder_raum_l'), koerper)

    sk = skizze(comp, e_hinten, 'Sk_Bohrungen_Block')
    for x in L['block_schraube_x']:
        kreis(sk, x, zc, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Mutterntaschen der schwimmenden Verschraubung: Sechskant, damit die
    # M3-Mutter beim Anziehen von der Tasche gehalten wird und man sie nicht
    # von hinten gegenhalten muss.
    sk = skizze(comp, e_hinten, 'Sk_Mutterntaschen_Block')
    for x in L['block_schraube_x']:
        sechskant(sk, x, zc, w('m3_mutter_sw') + w('tasche_spiel'))
    weg(comp, alle_profile(sk), w('m3_mutter_h') + 0.3, koerper)

    fussfase(comp, koerper, 'y', zc - w('block_hoehe') / 2, w('fase_fuss'),
             fehler, 'Mutternblock')
    bbox_pruefen(koerper, 'Mutternblock',
                 ((w('block_x_links'), w('block_x_rechts')),
                  (w('block_y_hinten'), L['schlitten_y1']),
                  (zc - w('block_hoehe') / 2, zc + w('block_hoehe') / 2)),
                 fehler)
    material_zuweisen(app, design, koerper, 'PETG')
    return koerper


def bau_bohrlehren(app, design, comp, L, zc, fehler):
    """Duenne Lehrenplatten mit den kritischen Lochbildern — auflegen,
    anzeichnen, pruefen. Nach dem Lauf ausgeblendet (Konvention SKILL.md).
    Alle Lehren liegen hinter der Maschine auf einer eigenen Ebene.

    Eine Lehre gibt es nur fuer Lochbilder von Teilen, die dieses Skript NICHT
    selbst erzeugt: Kaufteile (X-Wagen, Z-Wagen, Laser). Damit weicht das
    bewusst von der SKILL.md-Konvention ab, die auch fuer Verbindungen zwischen
    zwei getrennt gedruckten Teilen eine Lehre vorsieht — fuer
    Mutternblock <-> Schlittenplatte waere sie ohne Nutzen: beide Lochbilder
    haengen an derselben Variable (block_schraube_x), und die Bohrung in der
    Platte ist mit m3_uebermass absichtlich groesser als die im Block, damit
    sich der Block schwimmend ausrichten laesst. Was eine Lehre pruefen
    wuerde, ist dort also schon als Verstellbarkeit eingebaut."""
    ebene = ebene_y(comp, -40.0, 'E_Bohrlehren')
    lehren = [
        ('XWagen', (-95.0, 0.0), L['x_wagen_loecher']),
        # Frueher trug diese Lehre beide MGN9-Lochbilder (10 und 16 mm laengs),
        # weil offen war, welcher Wagen verbaut ist. Am 2026-09-17 am Teil
        # geprueft: MGN9H, 16 mm. Die Lehre folgt jetzt dem Parameter.
        ('ZWagen', (-40.0, 55.0),
         [(x, z)
          for x in (-w('z_wagen_loch_quer') / 2, w('z_wagen_loch_quer') / 2)
          for z in (-w('z_wagen_loch_laengs') / 2,
                    w('z_wagen_loch_laengs') / 2)]),
        ('Laser', (-40.0, -45.0),
         [(x, z) for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2)
          for z in (L['laser_loch_unten_rel'] - L['laser_loch_oben_rel'], 0.0)]),
    ]
    for name, (mx, mz), punkte in lehren:
        sk = skizze(comp, ebene, 'Sk_Bohrlehre_' + name)
        for u, v in punkte:
            kreis(sk, mx + u, mz + v, w('m3_durchgang'))
        us = [mx + u for u, _ in punkte]
        vs = [mz + v for _, v in punkte]
        rand = 8.0
        rechteck(sk, min(us) - rand, min(vs) - rand,
                 max(us) + rand, max(vs) + rand)
        lehre = neu(comp, groesstes_profil(sk), w('lehre_dicke')).bodies.item(0)
        lehre.name = 'Bohrlehre_' + name
        material_zuweisen(app, design, lehre, 'PLA')
        lehre.isLightBulbOn = False


def hinweise_bauen(L, zc, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/toolhead_check.py)."""
    # Verstellbereich der Laser-Langloecher (Schaft Ø3 im Schlitz)
    quer_tol = w('schlitz_verstellweg') + w('schlitz_breite') - 3.0
    hoch_tol = w('schlitz_breite') - 3.0
    h = [
        'BEZUGSEBENE: Ursprung = Mitte des X-Wagen-Lochbildes AUF seiner',
        '  Stirnflaeche. X = quer, Y = nach vorn, Z = senkrecht.',
        '  Im Modell ist Y und Z getauscht (Modell-Z = Maschine Y), damit',
        '  alle Plattenskizzen in einer Ebenenfamilie liegen.',
        '',
        'Y-KETTE (ab X-Wagen-Stirnflaeche):',
        '  Portalprofil ............ {:+.1f} mm'.format(L['portal_y']),
        '  Traegerplatte vorn ...... {:+.1f} mm'.format(L['traeger_y1']),
        '  Auflage der Z-Schiene ... {:+.1f} mm'.format(L['sockel_y1']),
        '  Stirnflaeche Z-Wagen .... {:+.1f} mm'.format(L['z_wagen_y']),
        '  Laser-Anschraubflaeche .. {:+.1f} mm'.format(L['laser_y']),
        '  Strahlachse ............. {:+.1f} mm'.format(L['strahl_y']),
        '',
        'Z-ACHSE:',
        '  Wagenmitte zc von {:+.1f} bis {:+.1f} mm'.format(
            L['zc_min'], L['zc_max']),
        '  nutzbarer Verfahrweg: {:.1f} mm'.format(L['z_weg']),
        '  begrenzt durch: {}'.format(L['zc_bindend']),
        '  gebaut bei zc = {:+.1f} mm (Mitte des Verfahrwegs)'.format(zc),
        '  Laser-Unterkante: {:+.1f} bis {:+.1f} mm'.format(
            L['zc_min'] + L['laser_unten_rel'],
            L['zc_max'] + L['laser_unten_rel']),
        '  M6-Gewindestange: {:.0f} mm benoetigt (Zuschnitt {:.0f} mm)'.format(
            L['spindel_laenge'], 10 * round(L['spindel_laenge'] / 10 + 0.5)),
        '',
        'MOTORBEFESTIGUNG: NEMA17 hat Gewinde im Flansch, es wird also von',
        '  UNTEN verschraubt — durchstecken von oben geht nicht. Alle VIER',
        '  Schrauben (4x M3x12) sind erreichbar: die hintere Reihe liegt bei',
        '  Y={:+.1f} und damit {:.1f} mm vor der Traegerplatte (Y=0..{:.0f}).'.format(
            w('spindel_y') - w('motor_loch') / 2, L['korridor_luft'],
            w('traeger_dicke')),
        '  Genau dafuer sitzt die Spindelachse bei Y={:+.1f} und die'.format(
            w('spindel_y')),
        '  Schlittenplatte entsprechend weiter vorn (pad_hoehe={:.0f}).'.format(
            w('pad_hoehe')),
        '  Zwei Fuehrungsrippen ({:.0f} mm hoch) fassen den Flansch seitlich —'.format(
            w('motor_rippe_hoehe')),
        '  der Motor findet beim Einsetzen selbst seine Lage.',
        '  Die Konsole ist an die Traegerplatte angeformt: ein Druckteil,',
        '  keine Verschraubung Halter/Platte.',
        '',
        'ANTRIEB: NEMA 17 oben, Welle nach unten, flexible Kupplung 5->6 mm.',
        '  Zwei M6-Muttern im Mutternblock, von einer Druckfeder auseinander-',
        '  gedrueckt: die untere liegt auf dem Boden, die obere unter der',
        '  Decke. Die Gewindeflanken tragen damit gegenlaeufig — spielfrei.',
        '  MUTTERNTASCHEN: Sechskant mit SW+{:.2f}, eine Flanke liegt am'.format(
            w('tasche_spiel')),
        '  Taschenboden. Davor ein um {:.2f} mm engeres Mundstueck: die'.format(
            w('tasche_klemmung')),
        '  Mutter wird einmal hineingedrueckt und rastet dahinter ein —',
        '  sie fallt beim Zusammenbauen nicht mehr heraus. Im Sechskant selbst',
        '  hat sie Spiel und bleibt in Z beweglich, damit die Feder sie gegen',
        '  Boden bzw. Decke druecken kann.',
        '  Die beiden M3-Muttern der schwimmenden Verschraubung sitzen',
        '  ebenfalls in Sechskanttaschen und muessen nicht gegengehalten werden.',
        '  Der Block ist mit Uebermass ({:.1f} mm statt {:.1f}) verschraubt:'.format(
            w('m3_uebermass'), w('m3_durchgang')),
        '  Z-Achse mehrmals durchfahren, DANN festziehen. So kaempft die',
        '  krumme Gewindestange nicht gegen die Linearfuehrung.',
        '',
        'MONTAGEREIHENFOLGE (wichtig, sonst kommt man nicht mehr dran):',
        '  1. Gewindeeinsaetze in den Schienensockel einschmelzen',
        '  2. Traegerplatte an den X-Wagen (4x M3x12 + Scheibe) — die Koepfe',
        '     sind spaeter von der Schlittenplatte verdeckt',
        '  3. Z-Schiene auf den Sockel (Senkkopf M3x10 in die Inserts)',
        '  4. Laser an die Schlittenplatte (Koepfe liegen im Pad-Freiraum)',
        '  5. Schlittenplatte auf den Z-Wagen (4x M3x{:.0f})'.format(
            L['z_wagen_schraube']),
        '  6. Motor zwischen die Fuehrungsrippen setzen, 4x M3x12 von unten',
        '  7. Kupplung + Gewindestange, Mutternblock zuletzt ausrichten',
        '',
        'LEHREN — nur fuer KAUFTEIL-Lochbilder; fuer',
        '  Mutternblock <-> Schlittenplatte braucht es keine, beide kommen aus',
        '  diesem Skript und die Platte hat dort Uebermass zum Ausrichten:',
        '  Bohrlehre_XWagen ...... {:.0f} x {:.0f} mm (MGN15H)'.format(
            w('x_wagen_loch_laengs'), w('x_wagen_loch_quer')),
        '  Bohrlehre_ZWagen ...... {:.0f} x {:.0f} mm (MGN9H, am Teil bestaetigt)'.format(
            w('z_wagen_loch_laengs'), w('z_wagen_loch_quer')),
        '  Bohrlehre_Laser ....... {:.2f} x {:.2f} mm (am Teil bestaetigt)'.format(
            w('laser_loch_hoch'), w('laser_loch_quer')),
        '    Langloch deckt quer {:.1f}-{:.1f} und hoch {:.1f}-{:.1f} mm ab —'.format(
            w('laser_loch_quer') - quer_tol, w('laser_loch_quer') + quer_tol,
            w('laser_loch_hoch') - hoch_tol, w('laser_loch_hoch') + hoch_tol),
        '    jetzt nur noch Toleranzausgleich, nicht mehr Unsicherheit.',
        '  OFFEN ist nur noch der X-Wagen: die alte Messung "26 x 25 mm am',
        '  Toolhead-Wagen" gehoert zu ihm (MGN15H), nicht zur Z-Achse. Vor dem',
        '  Druck der Traegerplatte mit Bohrlehre_XWagen pruefen — er traegt den',
        '  ganzen Toolhead, und ein MGN15C haette 25 x 20 statt 25 x 25.',
        '',
        'ANZIEHEN: die Z-Wagen-Schrauben klemmen {:.0f} mm PETG (Kopf sitzt in'.format(
            w('pad_hoehe')),
        '  der Freibohrung auf der Pad-Vorderseite). Handfest anziehen und',
        '  Schraubensicherung verwenden — eine lange Kunststoffsaeule setzt',
        '  sich mehr als eine kurze.',
        '',
        'DRUCK (PETG, Bambu Lab A1):',
        '  Traegerplatte ... Rueckseite (Passflaeche) aufs Bett. Platte, Sockel,',
        '                    Konsole und Rippen stehen alle auf dem Bett —',
        '                    keine Stuetzen, alle Kraefte in der Schicht.',
        '  Schlittenplatte . Laser-Anschraubflaeche aufs Bett',
        '  Mutternblock .... Unterseite aufs Bett (Spindelbohrung wird rund)',
        '  4 Wandlinien, >=40% Infill. PETG wegen der Abwaerme des Lasers.',
        '',
        'PARAMETRIK: MASSE landet als User-Parameter im Dialog. Die absoluten',
        '  Lagen rechnet lage() in Python — nach einer Parameteraenderung das',
        '  Skript neu laufen lassen und tools/toolhead_check.py ausfuehren.',
    ]
    if fehler:
        h += ['', 'NICHT GESETZT (Geometrie trotzdem masshaltig):'] \
            + ['  ' + z for z in fehler]
    return h


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = '{}_r{}'.format(SKRIPT_NAME, REVISION)
        except RuntimeError:
            pass

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        fehler = []

        up = design.userParameters
        for name in sorted(MASSE):
            wert, kommentar = MASSE[name]
            if up.itemByName(name) is None:
                up.add(name, adsk.core.ValueInput.createByString(
                    '{} mm'.format(wert)), 'mm', kommentar)

        L = lage()
        zc = (L['zc_min'] + L['zc_max']) / 2.0      # Bauzustand: Mitte des Wegs

        # Baugruppe: alle Komponenten am globalen Maschinenursprung. Damit
        # stehen sie bereits richtig zueinander und As-Built-Joints genuegen.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Traegerplatte', 'Schlittenplatte',
                     'Mutternblock', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o

        bau_traegerplatte(app, design, occ['Traegerplatte'].component, L, fehler)
        bau_schlittenplatte(app, design, occ['Schlittenplatte'].component,
                            L, zc, fehler)
        bau_mutternblock(app, design, occ['Mutternblock'].component, L, zc, fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, zc, fehler)

        occ['Traegerplatte'].isGrounded = True
        occ['Bohrlehren'].isGrounded = True

        # Starrer As-Built-Joint fuer die feste Verschraubung ...
        for a, b in (('Mutternblock', 'Schlittenplatte'),):
            try:
                ein = root.asBuiltJoints.createInput(occ[a], occ[b], None)
                ein.setAsRigidJointMotion()
                root.asBuiltJoints.add(ein)
            except:
                fehler.append('Joint {} <-> {} nicht gesetzt'.format(a, b))

        # ... und ein Schubgelenk fuer die Z-Achse, damit sich der Verfahrweg
        # im Modell pruefen laesst. Richtung Maschine Z = Modell-Y.
        try:
            koerper = occ['Schlittenplatte'].component.bRepBodies.item(0)
            flaeche = None
            for i in range(koerper.faces.count):
                f = koerper.faces.item(i)
                if (f.geometry.surfaceType
                        == adsk.core.SurfaceTypes.PlaneSurfaceType
                        and abs(f.centroid.z - L['schlitten_y0'] / 10.0) < 1e-4
                        and (flaeche is None or f.area > flaeche.area)):
                    flaeche = f
            geo = adsk.fusion.JointGeometry.createByPlanarFace(
                flaeche.createForAssemblyContext(occ['Schlittenplatte']), None,
                adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            ein = root.asBuiltJoints.createInput(
                occ['Schlittenplatte'], occ['Traegerplatte'], geo)
            ein.setAsSliderJointMotion(
                adsk.fusion.JointDirections.YAxisJointDirection)
            root.asBuiltJoints.add(ein)
        except:
            fehler.append('Schubgelenk der Z-Achse nicht gesetzt — '
                          'Teile stehen trotzdem richtig (starr pruefen)')

        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        app.activeViewport.fit()
        validierungs_bericht(app, design, ui,
                             hinweise=hinweise_bauen(L, zc, fehler))

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
