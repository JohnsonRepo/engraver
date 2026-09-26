# Elektronik.py — Gehaeuse fuer die Steuerung hinter dem hinteren 2060
#
# Baugruppe aus zwei Druckteilen und einer Bohrlehre:
#   Gehaeuse     Kasten fuer Arduino Uno R3 mit CNC Shield V3 und 4 x TMC2209,
#                daneben Platz fuer drei Wago-Klemmen und den Abwaerts-
#                wandler 24 -> 12 V (Kabelbinder). Hinten Fenster fuer USB,
#                Einbaubuchse fuer den Hohlstecker 5,5 x 2,1 und Wipp-
#                schalter; Kabelausschnitte links und vorn, Lueftungs-
#                schlitze rechts. Vorn eine Montageplatte mit 4 x M5 in
#                Hammermuttern der Rueckseite des hinteren 2060; zwischen
#                Platte und Kasten laeuft ein Kabelkanal.
#   Deckel       mit dem 24-V-Luefter (40 x 40 x 10) ueber den Treibern,
#                4 x M3 in Gewindeeinsaetze der Eckdome.
#   Bohrlehren   ausgeblendet: Lochbild des Uno zum Anhalten, bevor das
#                Gehaeuse gedruckt wird.
#   Referenz_nicht_drucken  nur zur Ansicht: hinteres 2060, Enden der 2040,
#                Uno mit Shield und Treibern (Huelle), Luefter.
#
# Das Gehaeuse steht im Fach hinter dem hinteren 2060, unter den 2040
# (docs/elektronik.md). Dorthin faehrt nichts; nur der Luefter ragt ueber
# das Fach hinaus, er steht aber weit genug hinter dem 2060 — Pruefung:
# tools/elektronik_check.py.
#
# Koordinaten = Maschinenkoordinaten wie in Portal.py, Portal in der Mitte
# seines Wegs: Y nach vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs,
# X = 0 in der Mitte des Portalrohrs. Im Fusion-Modell sind Y und Z
# getauscht (Modell-Z = Maschine Y). Die Rahmenmasse stehen hier noch einmal
# (Fusion-Skripte sind eigenstaendig); tools/elektronik_check.py vergleicht
# sie mit Portal.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'Elektronik'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # Rahmen, Portal in der Mitte — muss zu Portal.py passen [v]
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_y0':         (-360.0, 'Rahmen: hintere Stirnseite der 2040'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'quer_y1':           (-215.0, 'Rahmen: Rueckseite des hinteren 2060'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
    'quer_laenge':        (600.0, '2060 quer: Laenge'),
    'quer_nut_1':          (10.0, '2060: 1. Nut ueber der Unterkante'),
    'quer_nut_teilung':    (20.0, '2060: Nutabstand'),
    # V-Slot vereinfacht (Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),
    # Fach: Abstand zu Rahmen und Tisch (wie tools/portal_check.py)
    'fach_rand':            (3.0, 'Fach: Abstand zu 2060 und 2040'),
    'fach_tisch':           (2.0, 'Fach: Abstand zum Tisch'),

    # Arduino Uno R3 [w] — Lochbild mit Bohrlehre_Uno pruefen
    'uno_l':              (68.58, 'Uno: Platine, lange Seite'),
    'uno_b':              (53.34, 'Uno: Platine, kurze Seite'),
    'uno_pcb':              (1.6, 'Uno: Platinendicke'),
    'uno_buchse_vor':       (6.3, 'Uno: USB-Buchse steht so weit ueber die Kante'),
    'uno_buchse_h':        (11.0, 'Uno: USB- und Hohlbuchse, Hoehe ueber der Platine'),
    'uno_buchse_b':        (46.0, 'Uno: Bereich der Buchsen an der Kante'),
    # Stapel: Unterseite Uno bis Oberkante Kuehlkoerper der Treiber [w]
    'stapel_h':            (34.0, 'Uno + Shield + Treiber: Hoehe ab Unterseite Uno'),
    'luft_luefter':         (8.0, 'Luft zwischen Kuehlkoerpern und Deckel'),

    # Gehaeuse
    'geh_x0':            (-205.0, 'Gehaeuse: linke Aussenkante'),
    'geh_abstand':         (12.0, 'Gehaeuse: Kabelkanal zwischen Platte und Kasten'),
    'geh_wand':             (2.5, 'Gehaeuse: Wand'),
    'geh_boden':            (2.5, 'Gehaeuse: Boden'),
    'uno_rand':             (4.0, 'Uno: Luft zur Wand links und rechts'),
    'uno_hinten':           (7.0, 'Uno: Buchsenkante bis Innenseite Rueckwand'),
    'uno_vorn':            (10.0, 'Uno: Luft vorn (Stecker, Kabel)'),
    'uno_steg_h':           (5.0, 'Uno: Stehbolzen, Hoehe ueber dem Boden'),
    'uno_steg_d':           (6.5, 'Uno: Stehbolzen, Durchmesser'),
    'uno_schraube_d':       (2.8, 'Uno: Kernloch fuer M3 selbstschneidend'),
    'vert_b':              (94.0, 'Verteiler: Innenbreite (3 Wago nebeneinander)'),
    'buchse_d':             (8.2, 'Einbaubuchse 5,5 x 2,1, Gewinde M8'),
    'schalter_b':          (19.2, 'Wippschalter KCD1: Ausschnitt breit'),
    'schalter_h':          (12.9, 'Wippschalter KCD1: Ausschnitt hoch'),
    'schalter_wand':        (1.6, 'Wippschalter: Wand am Ausschnitt'),
    'schalter_rand':        (3.0, 'Wippschalter: verduennter Rand um den Ausschnitt'),
    'eingang_z':           (16.0, 'Buchse und Schalter: Mitte ueber dem Boden'),
    'kabel_links_b':       (36.0, 'Kabelausschnitt links: Breite'),
    'kabel_vorn_b':        (30.0, 'Kabelausschnitt vorn: Breite'),
    'kabel_t':             (20.0, 'Kabelausschnitte: Tiefe ab Oberkante'),
    'lueftung_b':           (3.0, 'Lueftungsschlitz: Breite'),
    'lueftung_h':          (22.0, 'Lueftungsschlitz: Hoehe'),
    'binder_b':             (5.0, 'Kabelbinder-Schlitz: Laenge'),
    'binder_t':             (2.2, 'Kabelbinder-Schlitz: Breite'),
    # Platz im Verteiler (Masse der Teile [w]): hinten Buchse und Schalter,
    # davor der Wandler quer, davor die drei Wago-Klemmen nebeneinander
    # (221-415: 30,2 breit, 18,6 tief, Draehte von vorn oder hinten)
    'eingang_tiefe':       (22.0, 'Verteiler: Buchse und Schalter reichen so weit hinein'),
    'wandler_t':           (30.0, 'Verteiler: Platz fuer den Wandler (Tiefe)'),
    'wandler_binder':      (20.0, 'Verteiler: Kabelbinder so weit neben der Mitte'),
    'wago_t':              (20.0, 'Verteiler: Platz fuer die Wago-Klemmen (Tiefe)'),
    'wago_b':              (92.0, 'Verteiler: Platz fuer 3 Wago-Klemmen (Breite)'),
    'dom_d':                (9.0, 'Deckelschrauben: Dom aussen an der Wand'),
    'dom_raus':             (2.0, 'Deckelschrauben: Dommitte vor der Wand'),
    'dom_ende':            (12.0, 'Deckelschrauben: Dommitte vor der Rueck-/Vorderwand'),
    'insert_m3_d':          (4.6, 'Gewindeeinsatz M3: Einpressbohrung'),
    'insert_m3_t':          (7.0, 'Gewindeeinsatz M3: Sacklochtiefe'),
    # Montageplatte am hinteren 2060
    'platte_dicke':         (5.0, 'Montageplatte: Dicke'),
    'ohr_b':               (21.0, 'Montageplatte: Ohr neben dem Kasten'),
    'ohr_loch':            (12.0, 'Montageplatte: M5 so weit neben dem Kasten'),
    'rippe_b':              (4.0, 'Kanal: Rippe, Breite'),
    'rippe_h':             (17.0, 'Kanal: Rippe, Hoehe ueber dem Boden'),
    # Deckel und Luefter
    'deckel_dicke':         (2.5, 'Deckel: Dicke'),
    'lippe_b':              (1.2, 'Deckel: Lippe, Breite'),
    'lippe_h':              (3.0, 'Deckel: Lippe, Hoehe'),
    'lippe_spiel':          (0.3, 'Deckel: Lippe, Spiel zur Wand'),
    'luefter':             (40.0, 'Luefter 40 x 40 x 10, 24 V'),
    'luefter_h':           (10.0, 'Luefter: Hoehe'),
    'luefter_loch':        (32.0, 'Luefter: Lochabstand'),
    'luefter_d':           (38.0, 'Luefter: Oeffnung im Deckel'),
    'gitter_b':             (2.0, 'Deckel: Steg in der Luefteroeffnung'),
    # Normteile und Regeln
    'm3_durchgang':         (3.4, 'M3 Durchgang'),
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'inbus_frei_d':         (6.0, 'Werkzeugkorridor fuer den Inbus'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
    'lehre_dicke':          (2.0, 'Bohrlehre: Plattendicke'),
}

# Lochbild des Uno R3 in Platinenkoordinaten (mm): x laengs ab der Kante mit
# USB- und Hohlbuchse, y quer ab der Kante unter der Hohlbuchse [w]
# (Arduino-Massblatt, in mil: 550/100, 600/2000, 2600/300, 2600/1400).
UNO_LOECHER = ((13.97, 2.54), (15.24, 50.80), (66.04, 7.62), (66.04, 35.56))
LUEFTUNG_N = 6                   # Lueftungsschlitze rechts


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/elektronik_check.py)."""
    L = {}
    L['R'] = w('y_schienen_abstand') / 2.0
    L['tisch_z'] = w('rahmen_z0') - w('quer_h')
    L['quer_y'] = (w('quer_y1'), w('quer_y1') + w('rahmen_b'))
    L['quer_nut_z'] = [L['tisch_z'] + w('quer_nut_1') + i * w('quer_nut_teilung')
                       for i in range(3)]
    # Fach wie tools/portal_check.py (elektronikfach)
    L['fach_z'] = (L['tisch_z'] + w('fach_tisch'), w('rahmen_z0') - w('fach_rand'))

    wa, bo = w('geh_wand'), w('geh_boden')
    z0 = L['fach_z'][0]
    # Montageplatte an der Rueckseite des 2060, Kasten dahinter mit Kanal
    L['platte_y'] = (w('quer_y1') - w('platte_dicke'), w('quer_y1'))
    y1 = L['platte_y'][0] - w('geh_abstand')
    innen_t = w('uno_hinten') + w('uno_l') + w('uno_vorn')
    innen_b = 2.0 * w('uno_rand') + w('uno_b') + w('vert_b')
    L['geh_x'] = (w('geh_x0'), w('geh_x0') + innen_b + 2.0 * wa)
    L['geh_y'] = (y1 - innen_t - 2.0 * wa, y1)
    L['innen_x'] = (L['geh_x'][0] + wa, L['geh_x'][1] - wa)
    L['innen_y'] = (L['geh_y'][0] + wa, L['geh_y'][1] - wa)
    L['boden_z'] = z0 + bo
    L['uno_z0'] = L['boden_z'] + w('uno_steg_h')             # Unterseite Uno
    L['uno_z1'] = L['uno_z0'] + w('uno_pcb')
    L['stapel_z1'] = L['uno_z0'] + w('stapel_h')
    L['geh_z'] = (z0, L['stapel_z1'] + w('luft_luefter'))
    L['deckel_z'] = (L['geh_z'][1], L['geh_z'][1] + w('deckel_dicke'))
    L['luefter_z'] = (L['deckel_z'][1], L['deckel_z'][1] + w('luefter_h'))
    L['platte_x'] = (L['geh_x'][0] - w('ohr_b'), L['geh_x'][1] + w('ohr_b'))
    L['platte_z'] = (z0, L['fach_z'][1])

    # Uno: Buchsenkante hinten, Platine laengs Y. Platinen-x -> Maschinen-Y,
    # Platinen-y -> Maschinen-X (von oben gesehen eine Drehung, keine
    # Spiegelung: die Bauteilseite bleibt oben).
    ux = L['innen_x'][0] + w('uno_rand')
    uy = L['innen_y'][0] + w('uno_hinten')
    L['uno_x'] = (ux, ux + w('uno_b'))
    L['uno_y'] = (uy, uy + w('uno_l'))
    L['uno_loecher'] = [(ux + yb, uy + xb) for xb, yb in UNO_LOECHER]
    L['luefter_mitte'] = (ux + w('uno_b') / 2.0, uy + w('uno_l') / 2.0)
    fm, h = L['luefter_mitte'], w('luefter_loch') / 2.0
    L['luefter_loecher'] = [(fm[0] + a * h, fm[1] + b * h)
                            for a in (-1, 1) for b in (-1, 1)]
    # Fenster hinten: USB- und Hohlbuchse des Uno
    L['fenster_x'] = (ux - 1.0, ux + w('uno_buchse_b') + 1.0)
    L['fenster_z'] = (L['uno_z1'] - 1.0, L['uno_z1'] + w('uno_buchse_h') + 2.0)
    # Verteiler rechts vom Uno: Wago, Wandler; Buchse und Schalter hinten
    L['vert_x'] = (L['uno_x'][1] + w('uno_rand'), L['innen_x'][1])
    L['eingang_z'] = L['boden_z'] + w('eingang_z')
    L['buchse_x'] = L['vert_x'][0] + 14.0
    L['schalter_x'] = L['vert_x'][0] + 44.0     # Binder laufen daneben
    # Wandler quer vor Buchse und Schalter, mit zwei Kabelbindern laengs Y:
    # je ein Schlitzpaar vor und hinter ihm, der Binder laeuft unter dem
    # Boden durch. Die Binder laufen zwischen Buchse und Schalter bzw.
    # rechts am Schalter vorbei. Davor die Wago-Klemmen (Klebeband).
    vx, vy = L['vert_x'], L['innen_y']
    xm = (vx[0] + vx[1]) / 2.0
    y_w0 = vy[0] + w('eingang_tiefe')
    L['wandler_y'] = (y_w0, y_w0 + w('wandler_t'))
    vor = w('binder_t') + 2.5                  # vor den Binderschlitzen
    L['wago_y'] = (L['wandler_y'][1] + vor,
                   L['wandler_y'][1] + vor + w('wago_t'))
    L['wago_x'] = (xm - w('wago_b') / 2.0, xm + w('wago_b') / 2.0)
    rand = w('binder_t') / 2.0 + 1.0
    L['binder_x_lage'] = (xm - w('wandler_binder'), xm + w('wandler_binder'))
    L['binder'] = [(x, y) for x in L['binder_x_lage']
                   for y in (L['wandler_y'][0] - rand,
                             L['wandler_y'][1] + rand)]
    # Kabelausschnitte
    L['kabel_links_y'] = (L['innen_y'][0] + L['innen_y'][1]) / 2.0
    L['kabel_vorn_x'] = (L['geh_x'][0] + L['geh_x'][1]) / 2.0
    L['kabel_z0'] = L['geh_z'][1] - w('kabel_t')
    # Lueftung rechts, oben — zwischen den Deckeldomen, mit Abstand zu ihnen
    n = LUEFTUNG_N
    ya = L['geh_y'][0] + w('dom_ende') + w('dom_d') / 2.0 + 4.0
    ye = L['geh_y'][1] - w('dom_ende') - w('dom_d') / 2.0 - 4.0
    L['lueftung_y'] = [ya + (ye - ya) * i / (n - 1.0) for i in range(n)]
    L['lueftung_z'] = (L['geh_z'][1] - 5.0 - w('lueftung_h'),
                       L['geh_z'][1] - 5.0)
    # Deckeldome aussen an den Seitenwaenden
    xd = (L['geh_x'][0] - w('dom_raus'), L['geh_x'][1] + w('dom_raus'))
    yd = (L['geh_y'][0] + w('dom_ende'), L['geh_y'][1] - w('dom_ende'))
    L['dome'] = [(x, y) for x in xd for y in yd]
    L['deckel_x'] = (xd[0] - w('dom_d') / 2.0, xd[1] + w('dom_d') / 2.0)
    # Montage: M5 in der unteren und oberen Nut der Rueckseite des 2060
    xo = (L['geh_x'][0] - w('ohr_loch'), L['geh_x'][1] + w('ohr_loch'))
    L['m5'] = [(x, z) for x in xo for z in (L['quer_nut_z'][0],
                                           L['quer_nut_z'][2])]
    L['m5_schraube'] = 12.0
    # Rippen im Kanal: an beiden Enden und in der Mitte
    rb = w('rippe_b')
    L['rippen_x'] = [(L['geh_x'][0] + 1.0, L['geh_x'][0] + 1.0 + rb),
                     (L['kabel_vorn_x'] + w('kabel_vorn_b') / 2.0 + 4.0,
                      L['kabel_vorn_x'] + w('kabel_vorn_b') / 2.0 + 4.0 + rb),
                     (L['geh_x'][1] - 1.0 - rb, L['geh_x'][1] - 1.0)]
    L['rippe_z1'] = z0 + w('rippe_h')
    return L


# --- Materialien -------------------------------------------------------------
# Weicht vom Standardblock der SKILL.md ab. Der dortige Helfer sucht das
# Basismaterial unter dem englischen Namen "ABS Plastic" und faellt sonst auf
# eine TEILSTRING-Suche nach dem eigenen Namen zurueck. In einer deutschen
# Fusion-Installation ist die Folge:
#   PETG -> Teilstring "petg" findet nichts -> kein Material gesetzt ->
#           der Koerper behaelt den Design-Default, also STAHL (7,85 g/cm3)
#   PLA  -> Teilstring "pla"  findet z.B. "Plaster"/"Plastic" -> ~1,8 g/cm3
# Beides laeuft ohne Fehlermeldung durch; in ToolheadZ.py standen deshalb
# 608 g fuer die Traegerplatte im Bericht. Deshalb hier (Block unveraendert
# aus ToolheadZ.py):
#   1. Basismaterial ueber eine Kandidatenliste suchen, nie per Teilstring
#      auf den eigenen Namen.
#   2. Die Dichte NACH der Zuweisung einmessen (Masse/Volumen) und das
#      Property so nachziehen, dass die Zieldichte herauskommt. Damit ist es
#      gleichgueltig, von welchem Material kopiert wurde und in welcher
#      Einheit das Density-Property rechnet.
#   3. Bleibt die Dichte daneben, landet das als Zeile im Bericht statt
#      stillschweigend falsche Massen zu melden.



ZIELDICHTE = {'PLA': 1.24, 'PETG': 1.27,        # g/cm3
              'Leiterplatte': 1.85,            # nur Referenz: FR4
              'Kunststoff': 1.10}              # nur Referenz: Luefter, Huelle


# Kandidaten fuer das Basismaterial, aus dem kopiert wird (Reihenfolge = Vorzug)
BASIS_KANDIDATEN = ('ABS Plastic', 'ABS', 'ABS-Kunststoff', 'Nylon',
                    'Polycarbonate', 'Polyethylene', 'Polypropylene',
                    'Kunststoff', 'Plastic')


DICHTE_PROPERTY = ('Density', 'Dichte')


# Bibliotheksmaterialien der Referenzteile: Namen sind je nach Installation
# lokalisiert, deshalb Ausweichnamen (erst exakt, dann als Teilstring —
# jede Aluminium- bzw. Stahlsorte taugt fuer eine Ansicht).
BIBLIOTHEK_KANDIDATEN = {
    'Aluminum 6061': ('Aluminum 6061', 'Aluminium 6061', 'Aluminum',
                      'Aluminium'),
    'Steel': ('Steel', 'Stahl'),
}


def _dichte(ziel):
    """Dichte von `ziel` in g/cm3, gemessen statt angenommen.
    physicalProperties.mass ist in kg, volume in cm3."""
    try:
        pp = ziel.physicalProperties
        if pp.volume > 1e-9:
            return pp.mass * 1000.0 / pp.volume
    except:
        pass
    return None


def _bibliotheksmaterial(app, namen):
    """Erstes Material, dessen Name (case-insensitiv) einem der Kandidaten
    entspricht. Danach Teilstring-Suche, aber nur mit den Kandidaten — nie
    mit einem eigenen Kurznamen wie 'PLA', der auf 'Plaster' passt."""
    libs = app.materialLibraries
    kandidaten = [n.lower() for n in namen]
    for exakt in (True, False):
        for k in range(libs.count):
            mats = libs.item(k).materials
            for i in range(mats.count):
                ist = mats.item(i).name.lower()
                for kand in kandidaten:
                    if (ist == kand) if exakt else (kand in ist):
                        return mats.item(i)
    return None


def _irgendein_material(app):
    """Notnagel: das erste Material ueberhaupt. Weil die Dichte hinterher
    eingemessen wird, taugt jedes als Kopiervorlage."""
    libs = app.materialLibraries
    for k in range(libs.count):
        if libs.item(k).materials.count:
            return libs.item(k).materials.item(0)
    return None


# Bibliotheksmaterialien (Aluminium, Stahl) werden direkt zugewiesen, Fusion
# legt sie dabei selbst im Design an. Eine Kopie unter dem Bibliotheksnamen
# (addByCopy) liess sich dem zweiten Koerper nicht mehr zuweisen — Fusion
# brach mit "InternalValidationError : assetInst" ab (Rev. 8, beim zweiten
# Aluprofil). Kopiert werden nur die eigenen Materialien aus ZIELDICHTE, die
# einen eigenen Namen tragen. Wird in run() geleert.
_BIBLIOTHEK = {}


def material_zuweisen(app, design, ziel, name, fehler=None):
    """Setzt das physikalische Material auf `ziel` (BRepBody oder Component).
    Fuer eigene Materialien (ZIELDICHTE) wird die Dichte nach der Zuweisung
    eingemessen und korrigiert. Scheitert die Zuweisung, steht das in
    `fehler` — ein Abbruch wegen Kosmetik darf nie passieren."""
    if name in ZIELDICHTE:
        mat = design.materials.itemByName(name)
        if not mat:
            basis = (_bibliotheksmaterial(app, BASIS_KANDIDATEN)
                     or _irgendein_material(app))
            mat = design.materials.addByCopy(basis, name) if basis else None
    else:
        if name not in _BIBLIOTHEK:
            _BIBLIOTHEK[name] = _bibliotheksmaterial(
                app, BIBLIOTHEK_KANDIDATEN.get(name, (name,)))
        mat = _BIBLIOTHEK[name]
    if not mat:
        if fehler is not None:
            fehler.append('Material {} nicht gesetzt — Masse im Bericht ist '
                          'der Fusion-Default'.format(name))
        return None

    try:
        ziel.material = mat
    except Exception as exc:
        if fehler is not None:
            fehler.append('{}: Material {} nicht gesetzt ({}) — Masse im '
                          'Bericht ist der Fusion-Default'.format(
                              getattr(ziel, 'name', '?'), name, exc))
        return None
    ziel_dichte = ZIELDICHTE.get(name)
    if ziel_dichte:
        ist = _dichte(ziel)
        if ist and abs(ist - ziel_dichte) > 0.01:
            prop = None
            for pn in DICHTE_PROPERTY:
                prop = adsk.core.FloatProperty.cast(
                    mat.materialProperties.itemByName(pn))
                if prop:
                    break
            if prop:
                prop.value *= ziel_dichte / ist
            nachher = _dichte(ziel)
            if fehler is not None and (
                    nachher is None or abs(nachher - ziel_dichte) > 0.02):
                fehler.append(
                    '{}: Dichte {:.2f} statt {:.2f} g/cm3 — Massen im Bericht '
                    'stimmen nicht'.format(
                        name, nachher if nachher else 0.0, ziel_dichte))
    return mat


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
                if comp.name.startswith('Ref_'):
                    status += '  [Referenz, nicht drucken]'
                # Material und Dichte mit ausgeben: eine fehlgeschlagene
                # Materialzuweisung faellt sonst nur ueber eine unplausibel
                # grosse Masse auf.
                try:
                    mat_name = b.material.name
                except:
                    mat_name = '?'
                dichte = _dichte(b)
                zeilen.append(
                    '{}{}: {:.1f} g  ({}, {} g/cm3)  {:.0f} x {:.0f} x {:.0f} mm{}'
                    .format(praefix, b.name, b.physicalProperties.mass * 1000,
                            mat_name,
                            '{:.2f}'.format(dichte) if dichte else '?',
                            gr[0], gr[1], gr[2], status))
        if hinweise:
            zeilen += [''] + list(hinweise)
        ui.messageBox('\n'.join(zeilen), 'Validierung')
    except:
        pass


# --- Geometrie-Helfer (wie Portal.py) ------------------------------------------
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


def ebene_x(comp, x_mm, name):
    """Konstruktionsebene senkrecht zu Maschinen-X (Seitenwand).
    Skizzenkoordinaten darauf sind (Maschine Y, Maschine Z)."""
    return _offsetebene(comp, comp.yZConstructionPlane, x_mm / 10.0, 'x', name)


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
    if abs(pl.normal.x) > 0.9:       # Modell-X = Maschine X
        return 'x', pl.origin.x * 10.0
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
    elif fest == 'x':                # Ebene bei konstantem Maschinen-X
        modell = adsk.core.Point3D.create(wert / 10.0, v_mm / 10.0, u_mm / 10.0)
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


def dazu_mittig(comp, prof, dicke_mm, ziel):
    """Anfuegen, symmetrisch um die Skizzenebene."""
    return _symmetrisch(comp, prof, dicke_mm,
                        adsk.fusion.FeatureOperations.JoinFeatureOperation,
                        ziel)


def tasche(comp, prof, tiefe_mm, ziel):
    """Tasche symmetrisch um die Skizzenebene (Ebene = Taschenmitte)."""
    return _symmetrisch(comp, prof, tiefe_mm,
                        adsk.fusion.FeatureOperations.CutFeatureOperation, ziel)


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


# --- Helfer der Baugruppe (wie Portal.py) --------------------------------------
# --- Helfer dieser Baugruppe ---------------------------------------------------
# Konstruktionsebenen je Bauteil und Lage nur einmal anlegen. Wird in run()
# geleert: Fusion kann das Modul zwischen zwei Laeufen behalten, die Ebenen
# gehoeren aber zum alten Dokument.
_EBENEN = {}


def _ebene(comp, achse, wert, name):
    schluessel = (comp.name, achse, round(wert, 4))
    if schluessel not in _EBENEN:
        bauen = {'x': ebene_x, 'y': ebene_y, 'z': ebene_z}[achse]
        _EBENEN[schluessel] = bauen(comp, wert, name)
    return _EBENEN[schluessel]


def _op(art):
    F = adsk.fusion.FeatureOperations
    return {'neu': F.NewBodyFeatureOperation, 'dazu': F.JoinFeatureOperation,
            'weg': F.CutFeatureOperation}[art]


def quader(comp, name, x, y, z, art, ziel=None):
    """Achsparalleler Quader in Maschinenkoordinaten (mm). x, y, z sind
    Bereiche. Rechteck in X/Z auf der Ebene Y = y-Anfang, nach +Y
    extrudiert — die Normale der XY-Ebene zeigt verlaesslich nach Modell-Z
    (= Maschine Y), das haben Traeger- und Schlittenplatte in ToolheadZ.py
    schon gezeigt."""
    y0, y1 = min(y), max(y)
    sk = skizze(comp, _ebene(comp, 'y', y0, 'E_{}_Y{:.1f}'.format(
        comp.name, y0)), 'Sk_' + name)
    rechteck(sk, x[0], z[0], x[1], z[1])
    return extrudieren(comp, groesstes_profil(sk), y1 - y0, _op(art), ziel)


def bohrung(comp, name, achse, punkte, d, a0, a1, ziel):
    """Bohrung(en) Ø d entlang `achse` von a0 bis a1 (mm). punkte liegen in
    der Ebene: fuer 'z' (X, Y), fuer 'y' (X, Z), fuer 'x' (Y, Z).
    Symmetrisch um die Mitte geschnitten, also unabhaengig davon, wohin die
    Normale der Ebene zeigt."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, achse, m, 'E_{}_{}{:.1f}'.format(
        comp.name, achse.upper(), m)), 'Sk_' + name)
    for u, v in punkte:
        kreis(sk, u, v, d)
    tasche(comp, alle_profile(sk), abs(a1 - a0), ziel)


def prismen(comp, name, achse, rechtecke, a0, a1, art, ziel=None):
    """Rechtecke (u0, v0, u1, v1) quer zu `achse`, entlang `achse` von a0
    bis a1 — symmetrisch um die Mitte extrudiert, unabhaengig von der
    Richtung der Ebenennormale. u, v wie bei bohrung: fuer 'y' (X, Z),
    fuer 'x' (Y, Z), fuer 'z' (X, Y)."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, achse, m, 'E_{}_{}{:.1f}'.format(
        comp.name, achse.upper(), m)), 'Sk_' + name)
    for u0, v0, u1, v1 in rechtecke:
        rechteck(sk, u0, v0, u1, v1)
    return _symmetrisch(comp, alle_profile(sk), abs(a1 - a0), _op(art), ziel)


def zylinder(comp, name, achse, mitte, d, a0, a1, art, ziel=None):
    """Zylinder Ø d entlang `achse` von a0 bis a1; mitte in der Ebene wie
    bei bohrung."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, achse, m, 'E_{}_{}{:.1f}'.format(
        comp.name, achse.upper(), m)), 'Sk_' + name)
    kreis(sk, mitte[0], mitte[1], d)
    return _symmetrisch(comp, groesstes_profil(sk), abs(a1 - a0), _op(art),
                        ziel)


# --- Referenzprofil (wie Portal.py) --------------------------------------------
def bau_profil(comp, name, laengs, bereich, quer, z):
    """Aluprofil als Referenz, V-Slot vereinfacht: an jeder 20er-Teilung
    aller vier Seiten eine Nut (Oeffnung nut_b, dahinter die breitere
    Kammer), in jeder Zelle die Kernbohrung. laengs: 'x' oder 'y';
    bereich: laengs, quer: waagerecht quer dazu, z: senkrecht (mm)."""
    b = w('rahmen_b')                           # 20er Raster
    if laengs == 'y':
        k = quader(comp, name, quer, bereich, z, 'neu').bodies.item(0)
    else:
        k = quader(comp, name, bereich, quer, z, 'neu').bodies.item(0)
    k.name = name
    (q0, q1), (z0, z1) = quer, z
    qm = [q0 + b / 2.0 + i * b for i in range(int(round((q1 - q0) / b)))]
    zm = [z0 + b / 2.0 + i * b for i in range(int(round((z1 - z0) / b)))]
    r = []
    for breite, t0, t1 in ((b - 2.0 * w('nut_oben'), -1.0, w('nut_v_t')),
                           (w('nut_b'), w('nut_v_t'), w('nut_t')),
                           (w('nut_kammer_b'), w('nut_t'),
                            w('nut_kammer_t'))):
        h = breite / 2.0
        for m in qm:                            # oben und unten
            r.append((m - h, z1 - t1, m + h, z1 - t0))
            r.append((m - h, z0 + t0, m + h, z0 + t1))
        for m in zm:                            # beide Seiten
            r.append((q0 + t0, m - h, q0 + t1, m + h))
            r.append((q1 - t1, m - h, q1 - t0, m + h))
    prismen(comp, 'Nuten_' + name, laengs, r, bereich[0] - 1.0,
            bereich[1] + 1.0, 'weg', k)
    bohrung(comp, 'Kern_' + name, laengs, [(a, c) for a in qm for c in zm],
            w('kern_d'), bereich[0] - 1.0, bereich[1] + 1.0, k)
    return k


# --- Bauteile ------------------------------------------------------------------
def bau_gehaeuse(app, design, comp, L, fehler):
    """Kasten fuer Uno mit CNC Shield, daneben der Verteiler (Wago-Klemmen,
    Abwaertswandler). Die Montageplatte liegt an der Rueckseite des hinteren
    2060 und traegt den Kasten ueber den Kanalboden und drei Rippen; im
    Kanal dazwischen laufen die Kabel nach rechts.

    Kasten und Deckel bleiben im Fach, unter der Traegerplatte, die mit Z
    oben am hinteren Schienenende darueber steht. Nur der Luefter ragt
    hoeher; er steht ueber der Mitte des Uno, weit hinter dem 2060 — dort ist
    in der Mitte Platz bis unter den X-Wagen.

    Drucklage: Boden aufs Bett, Waende und Platte stehen senkrecht — keine
    Stuetzen. Die Oberkante des USB-Fensters ist eine Bruecke."""
    wa = w('geh_wand')
    gx, gy, gz = L['geh_x'], L['geh_y'], L['geh_z']
    k = quader(comp, 'Kasten', gx, gy, gz, 'neu').bodies.item(0)
    k.name = 'Gehaeuse'
    quader(comp, 'Innenraum', L['innen_x'], L['innen_y'],
           (L['boden_z'], gz[1] + 1.0), 'weg', k)
    # Kanalboden, Montageplatte, Rippen im Kanal
    quader(comp, 'Kanalboden', gx, (gy[1], L['platte_y'][0]),
           (gz[0], L['boden_z']), 'dazu', k)
    quader(comp, 'Montageplatte', L['platte_x'], L['platte_y'], L['platte_z'],
           'dazu', k)
    prismen(comp, 'Kanalrippen', 'z',
            [(x0, gy[1] - 0.5, x1, L['platte_y'][0] + 0.5)
             for x0, x1 in L['rippen_x']], gz[0], L['rippe_z1'], 'dazu', k)
    # Dome fuer die Deckelschrauben aussen an den Seitenwaenden
    for i, p in enumerate(L['dome']):
        zylinder(comp, 'Dom_{}'.format(i + 1), 'z', p, w('dom_d'), gz[0],
                 gz[1], 'dazu', k)
    bohrung(comp, 'Dom_Einsatz', 'z', L['dome'], w('insert_m3_d'),
            gz[1] - w('insert_m3_t'), gz[1] + 1.0, k)
    # Stehbolzen fuer den Uno: Kernloch fuer M3 selbstschneidend, 1 mm
    # Boden bleibt darunter
    for i, p in enumerate(L['uno_loecher']):
        zylinder(comp, 'Steg_{}'.format(i + 1), 'z', p, w('uno_steg_d'),
                 L['boden_z'] - 0.5, L['uno_z0'], 'dazu', k)
    bohrung(comp, 'Steg_Kernloch', 'z', L['uno_loecher'],
            w('uno_schraube_d'), gz[0] + 1.0, L['uno_z0'] + 1.0, k)
    # hinten: Fenster fuer USB- und Hohlbuchse des Uno, Einbaubuchse und
    # Wippschalter; die Wand um den Schalter ist verduennt, damit seine
    # Rastnasen greifen
    ya, yi = gy[0] - 1.0, gy[0] + wa + 1.0
    prismen(comp, 'Fenster_USB', 'y',
            [(L['fenster_x'][0], L['fenster_z'][0], L['fenster_x'][1],
              L['fenster_z'][1])], ya, yi, 'weg', k)
    bohrung(comp, 'Buchse', 'y', [(L['buchse_x'], L['eingang_z'])],
            w('buchse_d'), ya, yi, k)
    sb, sh, sr = w('schalter_b') / 2.0, w('schalter_h') / 2.0, \
        w('schalter_rand')
    xs_, zs_ = L['schalter_x'], L['eingang_z']
    prismen(comp, 'Schalter', 'y', [(xs_ - sb, zs_ - sh, xs_ + sb, zs_ + sh)],
            ya, yi, 'weg', k)
    prismen(comp, 'Schalter_Rand', 'y',
            [(xs_ - sb - sr, zs_ - sh - sr, xs_ + sb + sr, zs_ + sh + sr)],
            gy[0] + w('schalter_wand'), yi, 'weg', k)
    # Kabelausschnitte von oben: links zur Y-Kette und zum linken Y-Motor,
    # vorn in den Kanal (rechter Y-Motor, Y-Endschalter, Not-Aus)
    b = w('kabel_links_b') / 2.0
    prismen(comp, 'Kabel_links', 'x',
            [(L['kabel_links_y'] - b, L['kabel_z0'], L['kabel_links_y'] + b,
              gz[1] + 1.0)], gx[0] - 1.0, gx[0] + wa + 1.0, 'weg', k)
    b = w('kabel_vorn_b') / 2.0
    prismen(comp, 'Kabel_vorn', 'y',
            [(L['kabel_vorn_x'] - b, L['kabel_z0'], L['kabel_vorn_x'] + b,
              gz[1] + 1.0)], gy[1] - wa - 1.0, gy[1] + 1.0, 'weg', k)
    # Lueftungsschlitze rechts oben: der Luefter blaest auf die Treiber,
    # die Luft geht ueber den Wandler hinaus
    b = w('lueftung_b') / 2.0
    prismen(comp, 'Lueftung', 'x',
            [(y - b, L['lueftung_z'][0], y + b, L['lueftung_z'][1])
             for y in L['lueftung_y']], gx[1] - wa - 1.0, gx[1] + 1.0, 'weg',
            k)
    # Kabelbinder fuer den Wandler: Schlitze durch den Boden, quer zum
    # Binder (der laeuft laengs Y)
    rt, rb = w('binder_t') / 2.0, w('binder_b') / 2.0
    prismen(comp, 'Kabelbinder', 'z',
            [(x - rb, y - rt, x + rb, y + rt) for x, y in L['binder']],
            gz[0] - 1.0, L['boden_z'] + 1.0, 'weg', k)
    # Montage: 4 x M5 durch die Ohren der Platte in Hammermuttern
    bohrung(comp, 'Platte_M5', 'y', L['m5'], w('m5_durchgang'),
            L['platte_y'][0] - 1.0, L['platte_y'][1] + 1.0, k)
    fussfase(comp, k, 'y', gz[0], w('fase_fuss'), fehler, 'Gehaeuse')
    bbox_pruefen(k, 'Gehaeuse', (L['platte_x'], (gy[0], L['platte_y'][1]),
                                 (gz[0], max(gz[1], L['platte_z'][1]))),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_deckel(app, design, comp, L, fehler):
    """Deckel mit dem 24-V-Luefter ueber den Treibern. Eine Lippe innen an
    den Waenden richtet ihn aus, 4 x M3 in die Dome halten ihn. Der Luefter
    sitzt oben auf dem Deckel und blaest durch die Oeffnung nach unten; zwei
    Stege halten Kabel aus den Fluegeln.

    Drucklage: Oberseite aufs Bett, die Lippe waechst nach oben."""
    dz = L['deckel_z']
    k = quader(comp, 'Deckelplatte', L['deckel_x'], L['geh_y'], dz,
               'neu').bodies.item(0)
    k.name = 'Deckel'
    sp, lb = w('lippe_spiel'), w('lippe_b')
    ix = (L['innen_x'][0] + sp, L['innen_x'][1] - sp)
    iy = (L['innen_y'][0] + sp, L['innen_y'][1] - sp)
    z_l = (dz[0] - w('lippe_h'), dz[0])
    quader(comp, 'Lippe', ix, iy, z_l, 'dazu', k)
    quader(comp, 'Lippe_innen', (ix[0] + lb, ix[1] - lb),
           (iy[0] + lb, iy[1] - lb), (z_l[0] - 1.0, dz[0]), 'weg', k)
    bohrung(comp, 'Deckel_Schrauben', 'z', L['dome'], w('m3_durchgang'),
            z_l[0] - 1.0, dz[1] + 1.0, k)
    fm = L['luefter_mitte']
    bohrung(comp, 'Luefter_Oeffnung', 'z', [fm], w('luefter_d'), dz[0] - 1.0,
            dz[1] + 1.0, k)
    r, g = w('luefter_d') / 2.0 + 0.5, w('gitter_b') / 2.0
    prismen(comp, 'Gitter', 'z',
            [(fm[0] - r, fm[1] - g, fm[0] + r, fm[1] + g),
             (fm[0] - g, fm[1] - r, fm[0] + g, fm[1] + r)], dz[0], dz[1],
            'dazu', k)
    bohrung(comp, 'Luefter_Schrauben', 'z', L['luefter_loecher'],
            w('m3_durchgang'), dz[0] - 1.0, dz[1] + 1.0, k)
    fussfase(comp, k, 'y', dz[1], w('fase_fuss'), fehler, 'Deckel')
    bbox_pruefen(k, 'Deckel', (L['deckel_x'], L['geh_y'], (z_l[0], dz[1])),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_bohrlehren(app, design, comp, L, fehler):
    """Lochbild des Uno zum Anhalten, bevor das Gehaeuse gedruckt wird: die
    Platine auf die Lehre legen, alle vier Loecher muessen fluchten. Die
    Aussenkante ist der Platinenumriss. Liegt unter dem Tisch, ausgeblendet
    (Konvention SKILL.md).

    Weitere Lehren gibt es bewusst nicht: Deckel und Gehaeuse haengen an
    denselben Variablen, die M5 gehen in Hammermuttern."""
    z = L['tisch_z'] - 20.0
    sk = skizze(comp, ebene_z(comp, z, 'E_Bohrlehre_Uno'),
                'Sk_Bohrlehre_Uno')
    for x, y in L['uno_loecher']:
        kreis(sk, x, y, w('m3_durchgang'))
    rechteck(sk, L['uno_x'][0], L['uno_y'][0], L['uno_x'][1], L['uno_y'][1])
    lehre = neu_mittig(comp, groesstes_profil(sk),
                       w('lehre_dicke')).bodies.item(0)
    lehre.name = 'Bohrlehre_Uno'
    material_zuweisen(app, design, lehre, 'PLA', fehler)
    lehre.isLightBulbOn = False


# --- Referenz (nicht drucken) --------------------------------------------------
def bau_referenz(app, design, teile, L, fehler):
    """Hinteres 2060, die hinteren Enden der 2040, Uno mit der Huelle von
    Shield und Treibern, Luefter — nur zur Ansicht, NICHT drucken. Jedes Teil
    wird fuer sich gebaut: scheitert eines, steht das im Bericht."""
    R = L['R']

    def sicher(name, bauen, *args):
        try:
            k = bauen(*args)
            return k
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    pr = teile['Ref_Profile']
    k = sicher('2060', bau_profil, pr, '2060_hinten', 'x',
               (-w('quer_laenge') / 2.0, w('quer_laenge') / 2.0),
               L['quer_y'], (L['tisch_z'], w('rahmen_z0')))
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)
    for s in (-1, 1):
        n = 'links' if s < 0 else 'rechts'
        x = sorted((s * (R - w('rahmen_b') / 2.0),
                    s * (R + w('rahmen_b') / 2.0)))
        k = sicher('2040 ' + n, bau_profil, pr, '2040_hinten_' + n, 'y',
                   (w('rahmen_y0'), L['quer_y'][1] + 40.0), tuple(x),
                   (w('rahmen_z0'), w('rahmen_z0') + w('rahmen_h')))
        if k:
            material_zuweisen(app, design, k, 'Aluminum 6061', fehler)

    el = teile['Ref_Elektronik']
    fm, h = L['luefter_mitte'], w('luefter') / 2.0
    for name, x, y, z, mat in (
            ('Uno', L['uno_x'], L['uno_y'], (L['uno_z0'], L['uno_z1']),
             'Leiterplatte'),
            ('Shield_und_Treiber', L['uno_x'], L['uno_y'],
             (L['uno_z1'], L['stapel_z1']), 'Kunststoff'),
            ('Luefter', (fm[0] - h, fm[0] + h), (fm[1] - h, fm[1] + h),
             L['luefter_z'], 'Kunststoff')):
        def quader_ref(name=name, x=x, y=y, z=z):
            kk = quader(el, name, x, y, z, 'neu').bodies.item(0)
            kk.name = name
            return kk
        k = sicher(name, quader_ref)
        if k:
            material_zuweisen(app, design, k, mat, fehler)


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/elektronik_check.py)."""
    gx, gy, gz = L['geh_x'], L['geh_y'], L['geh_z']
    fm = L['luefter_mitte']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py, Portal in der Mitte',
        '  seines Wegs (Y nach vorn, Z senkrecht, X = 0 Mitte Portalrohr).',
        '  Im Modell sind Y und Z getauscht (Modell-Z = Maschine Y).',
        '',
        'LAGE: im Fach hinter dem hinteren 2060, unter den 2040.',
        '  Kasten X {:+.1f}..{:+.1f}, Y {:+.1f}..{:+.1f}, Z {:+.1f}..{:+.1f}'
        .format(gx[0], gx[1], gy[0], gy[1], gz[0], gz[1]),
        '  ({:.0f} x {:.0f} x {:.0f} mm), {:.0f} mm hinter dem 2060.'.format(
            gx[1] - gx[0], gy[1] - gy[0], gz[1] - gz[0],
            w('quer_y1') - gy[1]),
        '  Nur der Luefter ragt ueber das Fach hinaus (bis Z {:+.1f}); dort'
        .format(L['luefter_z'][1]),
        '  ist in der Mitte frei — Pruefung: tools/elektronik_check.py.',
        '',
        'MONTAGE: Platte an die Rueckseite des hinteren 2060, 4 x M5x{:.0f} in'
        .format(L['m5_schraube']),
        '  Hammermuttern der unteren und oberen Nut (Z {:+.0f} / {:+.0f}).'
        .format(L['m5'][0][1], L['m5'][1][1]),
        '  Inbus von hinten, neben dem Kasten vorbei.',
        'UNO: Buchsenkante nach hinten, 4 x M3x8 selbstschneidend in die',
        '  Stehbolzen (Kernloch {:.1f}). USB durch das Fenster hinten.'.format(
            w('uno_schraube_d')),
        'DECKEL: 4 x M3x8 in Gewindeeinsaetze der Dome (Einpressbohrung',
        '  {:.1f}). Luefter 24 V oben auf dem Deckel ueber der Mitte des Uno'
        .format(w('insert_m3_d')),
        '  (X {:+.1f}, Y {:+.1f}), 4 x M3x16 mit Mutter; er blaest nach unten.'
        .format(fm[0], fm[1]),
        'EINGANG hinten rechts: Einbaubuchse 5,5 x 2,1 mit M8-Gewinde',
        '  (Loch {:.1f}) und Wippschalter KCD1 (Ausschnitt {:.1f} x {:.1f},'
        .format(w('buchse_d'), w('schalter_b'), w('schalter_h')),
        '  Wand dort {:.1f} mm, damit die Rastnasen greifen).'.format(
            w('schalter_wand')),
        'VERTEILER: hinten Buchse und Schalter, davor der Wandler 24 -> 12 V',
        '  quer (2 Kabelbinder, Schlitze im Boden, bis {:.0f} mm tief), davor'
        .format(w('wandler_t')),
        '  3 x Wago 221-415 nebeneinander (doppelseitiges Klebeband).',
        'KABEL: links zur Y-Kette und zum linken Y-Motor; vorn in den Kanal',
        '  zwischen Platte und Kasten ({:.0f} mm), dort nach rechts: rechter'
        .format(w('geh_abstand')),
        '  Y-Motor, Y-Endschalter, Not-Aus.',
        '',
        'DRUCK (PETG, Bambu Lab A1): Gehaeuse auf dem Boden, Deckel mit der',
        '  Oberseite nach unten. Keine Stuetzen; das USB-Fenster ist oben',
        '  eine {:.0f}-mm-Bruecke.'.format(
            L['fenster_x'][1] - L['fenster_x'][0]),
        '',
        'NICHT GEMESSEN [w]: Lochbild des Uno (vor dem Druck mit der',
        '  ausgeblendeten Bohrlehre_Uno pruefen); Hoehe von Uno + Shield +',
        '  Treibern mit Kuehlkoerper {:.0f} mm (Deckel {:.0f} mm darueber);'
        .format(w('stapel_h'), w('luft_luefter')),
        '  Buchse (M8), Schalter (KCD1), Wago 221-415.',
    ]
    if fehler:
        h += ['', 'FEHLER / WARNUNGEN:'] + ['  ' + f for f in fehler]
    return h


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        _EBENEN.clear()
        _BIBLIOTHEK.clear()

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

        # Baugruppe: alle Komponenten am globalen Ursprung, jedes Teil steht
        # damit schon an seinem Platz; nichts bewegt sich, alles fixiert.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Gehaeuse', 'Deckel', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o
        bau_gehaeuse(app, design, occ['Gehaeuse'].component, L, fehler)
        bau_deckel(app, design, occ['Deckel'].component, L, fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, fehler)
        for o in occ.values():
            o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Profile', 'Ref_Elektronik'):
            o = ref.component.occurrences.addNewComponent(einheit)
            o.component.name = name
            teile[name] = o.component
        bau_referenz(app, design, teile, L, fehler)
        ref.isGrounded = True

        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        app.activeViewport.fit()
        validierungs_bericht(app, design, ui,
                             hinweise=hinweise_bauen(L, fehler))

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
