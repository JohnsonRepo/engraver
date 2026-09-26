# YMotorhalter.py — Halter fuer die NEMA 17 der Y-Achse am Ende jeder 2040
#
# Bauteil (ein Druckteil, keine Baugruppe): der Halter bewegt sich nicht,
# Motor und Ritzel sind Kaufteile. Das Teil ist symmetrisch zur Mitte der
# 2040 und passt deshalb links wie rechts — zweimal drucken, nichts spiegeln.
#
# Antrieb der Y-Achse (Nutzerangaben 2026-09-26, mit Foto):
#   * jede Seite hat ihren eigenen NEMA 17 am Ende ihrer 2040; die 2040
#     steht hochkant, liegt auf der hinteren 2060 und steht ueber sie hinaus
#   * der Y-Riemen laeuft INNERHALB der oberen Nuten beider Seitenflaechen
#     der 2040 und am Profilende um das Ritzel
#   * das Ritzel (GT2 20 Z, Bohrung 5) sitzt direkt auf der Motorwelle,
#     mittig zur 2040; der Motor haengt unter einer Platte etwa auf Hoehe der
#     unteren Nut, Welle nach oben
#   * befestigt wird mit Nutensteinen in den UNTEREN Nuten beider Seiten
#     (U-Buegel), in den oberen laeuft der Riemen
#   * gespannt wird, indem der Motor in Langloechern der Platte vom
#     Profilende weg rueckt
# Rev. 1 und 2 (ein Motor mittig an der hinteren Traverse, Omega-Trieb zu
# zwei senkrechten Wellen) beruhten auf einem Missverstaendnis; Rev. 3
# ersetzt sie ganz.
#
# Koordinatensystem (Maschinenkoordinaten an EINEM Profilende, in mm):
#   X = quer zur 2040, X = 0 ist ihre Mitte (das Teil ist symmetrisch)
#   Y = laengs der 2040, Y = 0 ist ihre Stirnseite, +Y zeigt vom Profil weg
#   Z = senkrecht nach oben, Z = 0 ist die Unterkante der 2040
# Im Fusion-Modell sind Y und Z getauscht (Modell-Z = Maschine Y) wie in
# ToolheadZ — die Helfer unten sind von dort uebernommen und in Fusion
# gelaufen.
#
# Alle Lagen leitet `lage()` aus MASSE ab — eine Quelle fuer Geometrie und
# fuer die Pruefung in tools/y_motorhalter_check.py.
#
# Konventionen: siehe fusion-python/SKILL.md.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'YMotorhalter'
REVISION = 3

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Profil: 2040 hochkant, Y-Schiene (Nutzerangabe) --------------------
    # Auf jeder 40-mm-Seitenflaeche zwei Nuten, 10 mm ueber der Unter- und
    # 10 mm unter der Oberkante [w] (20er Raster). In der OBEREN laeuft der
    # Riemen, in die UNTERE kommen die Nutensteine.
    'profil_breite':       (20.0,  '2040: Breite (Abstand der Seitenflaechen)'),
    'profil_hoehe':        (40.0,  '2040 hochkant: Hoehe'),
    'nut_unten':           (10.0,  'untere Nut ueber der Profilunterkante'),
    'nut_oben':            (10.0,  'obere Nut unter der Profiloberkante'),
    # Nut 6 [w]: Oeffnung, Lippe vor dem Nutenstein, Platz bis zum Nutgrund.
    # Der Riemen laeuft hinter den Lippen im Nutkanal.
    'nut_breite':           (6.2,  'Nut: Oeffnung'),
    'nut_lippe':            (1.8,  'Nut: Dicke der Lippe'),
    'nut_tiefe':            (6.0,  'Nut: Platz ab Profilflaeche nach innen'),
    'nutenstein_h':         (4.0,  'Nutenstein M5: Gewindelaenge'),

    # --- Kaufteil: NEMA 17 (hardware.md [w], wie an der Z-Achse) -----------
    'motor_flansch':       (42.3,  'NEMA17: Flanschmass'),
    'motor_loch':          (31.0,  'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0,  'NEMA17: Zentrierbund Durchmesser'),
    'motor_bund_h':         (2.0,  'NEMA17: Zentrierbund Hoehe'),
    'motor_welle_l':       (24.0,  'NEMA17: Wellenlaenge ab Flansch'),
    'motor_flach_l':       (15.0,  'NEMA17: Abflachung ab Wellenende'),
    'motor_gewinde_tiefe':  (4.5,  'NEMA17: Gewindetiefe im Flansch'),
    # Nur Freiraum nach unten: mit 48 mm gerechnet, ein 40er endet 8 mm hoeher.
    'motor_laenge':        (48.0,  'NEMA17: Koerperlaenge (nur Freiraum)'),

    # --- Kaufteil: GT2-Riemen und Ritzel (hardware.md [w]) -----------------
    'gt2_teilung':          (2.0,  'GT2: Teilung'),
    'riemen_breite':        (6.0,  'GT2-Riemen: Breite'),
    'riemen_dicke':        (1.38,  'GT2-Riemen: Gesamtdicke'),
    'riemen_zahn':         (0.75,  'GT2-Riemen: Zahnhoehe'),
    'riemen_pld':         (0.254,  'GT2: Wirklinie ueber dem Zahngrund'),
    # Mit 20 Zaehnen laufen beide Trume mittig im Nutkanal (Pruefung,
    # Abschnitt 3); die Zaehnezahl ist einheitenlos (EINHEITENLOS unten).
    'ritzel_z':            (20.0,  'Motorritzel: Zaehne'),
    'ritzel_flansch_d':    (16.0,  'GT2-Ritzel 20Z: Flanschdurchmesser'),
    'ritzel_laenge':       (16.0,  'GT2-Ritzel: Gesamtlaenge'),
    'ritzel_spur':          (7.0,  'GT2-Ritzel: Breite der Riemenspur'),
    'ritzel_flansch_h':     (1.0,  'GT2-Ritzel: Flanschdicke'),

    # --- Normteile ---------------------------------------------------------
    'm3_durchgang':         (3.4,  'M3 Durchgang'),
    'm3_kopf_d':            (5.5,  'M3 Zylinderkopf: Durchmesser'),
    'm3_kopf_h':            (3.0,  'M3 Zylinderkopf: Hoehe'),
    'm3_scheibe_d':         (7.0,  'M3 Scheibe DIN 125: Durchmesser'),
    'm3_scheibe_h':         (0.5,  'M3 Scheibe DIN 125: Dicke'),
    'm5_durchgang':         (5.5,  'M5 Durchgang'),
    'm5_kopf_d':            (8.5,  'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0,  'M5 Zylinderkopf: Hoehe'),
    'm5_scheibe_d':        (10.0,  'M5 Scheibe DIN 125: Durchmesser'),
    'm5_scheibe_h':         (1.0,  'M5 Scheibe DIN 125: Dicke'),

    # --- Halter ------------------------------------------------------------
    # Platte: Unterseite = Motorflansch. Hoechstens motor_welle_l -
    # ritzel_laenge - luft_min dick, sonst stoesst das Ritzel an (Pruefung).
    'platte_dicke':         (6.0,  'Motorplatte: Dicke'),
    # Schenkel an beiden Seitenflaechen, je zwei M5 in die untere Nut. Die
    # letzten 40 mm der 2040 sind frei (Nutzerangabe).
    'wange_dicke':          (6.0,  'Schenkel: Dicke'),
    'wange_laenge':        (40.0,  'Schenkel: Laenge hinter der Stirnseite'),
    'schraube_y':          (10.0,  'vordere M5: Abstand hinter der Stirnseite'),
    'schraube_abstand':    (20.0,  'Abstand der beiden M5 je Schenkel'),
    'halter_rand_unten':    (1.0,  'Halter endet so weit ueber der Profilunterkante'),
    # Joch: verbindet die Schenkel vor der Stirnseite und liegt an ihr an.
    'joch_dicke':           (4.0,  'Joch vor der Stirnseite: Dicke'),
    'fuehrung_dicke':       (4.0,  'Fuehrungswand neben dem Motor: Dicke'),
    'spiel_locker':         (0.4,  'Montagespiel, diametral'),
    # Spannweg: jeder mm macht den Riemenweg 2 mm laenger.
    'spann_weg':            (8.0,  'Spannweg des Motors in den Langloechern'),
    'rand_vorn':            (1.5,  'Platte vor dem Motor (ganz aussen)'),
    'luft_min':             (1.0,  'Mindestluft zwischen Teilen'),
    'fase_fuss':            (0.4,  'Fase gegen Elefantenfuss an der Bettseite'),
}

# Werte ohne Einheit (werden als einheitenlose User-Parameter angelegt)
EINHEITENLOS = {'ritzel_z'}

# Normlaengen fuer die Schraubenwahl
M3_LAENGEN = (6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40)
M5_LAENGEN = (8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50)


def w(name):
    """Wert in mm (bzw. Anzahl)."""
    return MASSE[name][0]


def normlaenge(mindest, reihe):
    """Kuerzeste Normlaenge, die mindestens `mindest` lang ist."""
    for laenge in reihe:
        if laenge >= mindest - 1e-6:
            return float(laenge)
    return float(reihe[-1])


def teilkreis_r(zaehne):
    """Wirkradius eines GT2-Ritzels (Teilkreis / 2)."""
    return zaehne * w('gt2_teilung') / (2.0 * math.pi)


def lage():
    """Alle abgeleiteten Ebenen, Achsen und Lochbilder in Maschinen-
    koordinaten (mm). Einzige Quelle fuer Geometrie UND Pruefung."""
    L = {}
    halb = w('profil_breite') / 2.0

    # ---- Profil: je Seitenflaeche zwei Nuten -------------------------------
    L['profil_name'] = '20{:.0f}'.format(w('profil_hoehe'))
    L['nut_unten_z'] = w('nut_unten')
    L['nut_oben_z'] = w('profil_hoehe') - w('nut_oben')
    # Unterkante der oberen Nutoeffnung: bis hierhin darf der Halter an der
    # Seitenflaeche reichen, darueber bleibt sie fuer den Riemen frei.
    L['nut_oben_z0'] = L['nut_oben_z'] - w('nut_breite') / 2.0

    # ---- Riemen: laeuft in den oberen Nuten, Mitte = Nutmitte --------------
    L['riemen_z'] = L['nut_oben_z']
    L['riemen_z0'] = L['riemen_z'] - w('riemen_breite') / 2.0
    L['riemen_z1'] = L['riemen_z'] + w('riemen_breite') / 2.0
    # Der Riemen umschlingt das Ritzel mit der Zahnseite: Wirklinie auf dem
    # Teilkreis, Ruecken aussen, Zahnspitzen innen.
    L['rp'] = teilkreis_r(w('ritzel_z'))
    L['wirk_ruecken'] = w('riemen_dicke') - w('riemen_zahn') - w('riemen_pld')
    L['wirk_zahn'] = w('riemen_pld') + w('riemen_zahn')
    # Ritzel mittig: beide Trume laufen parallel zur 2040 in ihre Nuten.
    # Lage im Nutkanal, gemessen ab der Seitenflaeche nach innen.
    L['trum_ruecken_x'] = L['rp'] + L['wirk_ruecken']
    L['trum_zahn_x'] = L['rp'] - L['wirk_zahn']
    L['trum_tiefe_ruecken'] = halb - L['trum_ruecken_x']
    L['trum_tiefe_zahn'] = halb - L['trum_zahn_x']
    L['luft_lippe'] = L['trum_tiefe_ruecken'] - w('nut_lippe')
    L['luft_nutgrund'] = w('nut_tiefe') - L['trum_tiefe_zahn']
    L['zaehne_im_eingriff'] = w('ritzel_z') / 2.0           # 180 Grad
    L['mm_pro_umdrehung'] = w('ritzel_z') * w('gt2_teilung')

    # ---- Ritzel auf der Motorwelle, Nabe nach unten -------------------------
    # Die Spur sitzt in Riemenmitte; darunter Flansch und Nabe mit den
    # Madenschrauben.
    nabe = w('ritzel_laenge') - w('ritzel_spur') - 2.0 * w('ritzel_flansch_h')
    L['ritzel_nabe'] = nabe
    L['ritzel_z0'] = (L['riemen_z'] - w('ritzel_spur') / 2.0
                      - w('ritzel_flansch_h') - nabe)
    L['ritzel_z1'] = L['ritzel_z0'] + w('ritzel_laenge')
    L['madenschraube_z'] = L['ritzel_z0'] + nabe / 2.0

    # ---- Motor: die Welle reicht genau durch das ganze Ritzel -----------------
    # Daraus folgt die Hoehe des Motorflansches und damit der Platte.
    L['welle_z1'] = L['ritzel_z1']
    L['motor_flansch_z'] = L['welle_z1'] - w('motor_welle_l')
    L['motor_z0'] = L['motor_flansch_z'] - w('motor_laenge')
    L['bund_z1'] = L['motor_flansch_z'] + w('motor_bund_h')
    L['flach_z0'] = L['welle_z1'] - w('motor_flach_l')

    # ---- Platte und Halter in Z ---------------------------------------------
    L['platte_z0'] = L['motor_flansch_z']
    L['platte_z1'] = L['platte_z0'] + w('platte_dicke')
    L['ritzel_luft'] = L['ritzel_z0'] - L['platte_z1']
    # Joch, Schenkel und Fuehrungswaende enden oben buendig mit der Platte:
    # diese Flaeche liegt beim Druck auf dem Bett.
    L['halter_z0'] = w('halter_rand_unten')
    L['halter_z1'] = L['platte_z1']

    # ---- Breite (X) -----------------------------------------------------------
    L['wange_x0'] = halb + w('spiel_locker') / 2.0
    L['wange_x1'] = L['wange_x0'] + w('wange_dicke')
    L['fuehrung_x0'] = w('motor_flansch') / 2.0 + w('luft_min')
    L['halbe_breite'] = L['fuehrung_x0'] + w('fuehrung_dicke')

    # ---- Laenge (Y) -----------------------------------------------------------
    # Der Motor haengt in Hoehe des Profils (bis Z = motor_flansch_z) und muss
    # deshalb ganz vor der Stirnseite bleiben — vor dem Joch, das an ihr
    # anliegt.
    L['wange_y0'] = -w('wange_laenge')
    L['joch_y1'] = w('joch_dicke')
    L['motor_y_min'] = (L['joch_y1'] + w('luft_min')
                        + w('motor_flansch') / 2.0)
    L['motor_y_max'] = L['motor_y_min'] + w('spann_weg')
    L['motor_y_mitte'] = (L['motor_y_min'] + L['motor_y_max']) / 2.0
    L['platte_y1'] = (L['motor_y_max'] + w('motor_flansch') / 2.0
                      + w('rand_vorn'))

    # ---- Lochbilder -----------------------------------------------------------
    # M5 in die untere Nut: je Schenkel zwei, (Y, Z) — beide Schenkel gleich
    L['m5_loecher'] = [(-(w('schraube_y') + i * w('schraube_abstand')),
                        L['nut_unten_z']) for i in range(2)]
    L['n_m5'] = 2 * len(L['m5_loecher'])
    h = w('motor_loch') / 2.0
    L['motor_langloecher'] = [(sx * h, L['motor_y_mitte'] + sy * h)
                              for sy in (-1, 1) for sx in (-1, 1)]
    L['bund_schlitz_b'] = w('motor_bund_d') + w('spiel_locker')

    # ---- Schrauben ------------------------------------------------------------
    # M5 in den Nutenstein: Scheibe, Schenkel, Spalt zur Seitenflaeche, dann
    # ueber die Lippe in den Stein. Ueberstand = was in die Nut ragt.
    L['m5_klemm'] = (w('m5_scheibe_h') + w('wange_dicke')
                     + w('spiel_locker') / 2.0)
    L['m5_schraube'] = normlaenge(L['m5_klemm'] + w('nut_lippe') + 3.0,
                                  M5_LAENGEN)
    L['m5_ueberstand'] = L['m5_schraube'] - L['m5_klemm']
    L['m5_eingriff'] = (min(L['m5_ueberstand'],
                            w('nut_lippe') + w('nutenstein_h'))
                        - w('nut_lippe'))
    # Motorschrauben von oben: Scheibe, Platte, dann in den Flansch —
    # mindestens 3 mm Eingriff und 0,5 mm vor dem Gewindegrund.
    L['motor_klemm'] = w('platte_dicke') + w('m3_scheibe_h')
    L['motor_schraube'] = normlaenge(L['motor_klemm'] + 3.0, M3_LAENGEN)
    L['motor_eingriff'] = L['motor_schraube'] - L['motor_klemm']

    # ---- Spannen --------------------------------------------------------------
    L['riemen_verstellung'] = 2.0 * w('spann_weg')
    return L


# --- Materialien -------------------------------------------------------------
# Uebernommen aus ToolheadZ (dort erklaert): Basismaterial ueber eine
# Kandidatenliste suchen, nie per Teilstring auf den eigenen Namen, und die
# Dichte NACH der Zuweisung einmessen und nachziehen. In einer deutschen
# Fusion-Installation landet der Koerper sonst stillschweigend bei Stahl.

ZIELDICHTE = {'PLA': 1.24, 'PETG': 1.27}        # g/cm3
BASIS_KANDIDATEN = ('ABS Plastic', 'ABS', 'ABS-Kunststoff', 'Nylon',
                    'Polycarbonate', 'Polyethylene', 'Polypropylene',
                    'Kunststoff', 'Plastic')
DICHTE_PROPERTY = ('Density', 'Dichte')


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
    entspricht. Danach Teilstring-Suche, aber nur mit den Kandidaten."""
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
    """Notnagel: das erste Material ueberhaupt — die Dichte wird hinterher
    ohnehin eingemessen."""
    libs = app.materialLibraries
    for k in range(libs.count):
        if libs.item(k).materials.count:
            return libs.item(k).materials.item(0)
    return None


def material_zuweisen(app, design, ziel, name, fehler=None):
    """Setzt das physikalische Material auf `ziel` (BRepBody oder Component).
    Fuer eigene Materialien (ZIELDICHTE) wird die Dichte nach der Zuweisung
    eingemessen und korrigiert."""
    mat = design.materials.itemByName(name)
    if not mat:
        if name in ZIELDICHTE:
            basis = (_bibliotheksmaterial(app, BASIS_KANDIDATEN)
                     or _irgendein_material(app))
        else:
            basis = _bibliotheksmaterial(app, (name,))
        mat = design.materials.addByCopy(basis, name) if basis else None
    if not mat:
        if fehler is not None:
            fehler.append('Material {} nicht gesetzt — Masse im Bericht ist '
                          'der Fusion-Default'.format(name))
        return None

    ziel.material = mat
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


# --- Geometrie-Helfer (aus ToolheadZ, dort in Fusion gelaufen) ----------------
def _offsetebene(comp, basis, ziel_cm, achse, name):
    """Offsetebene, deren Lage nachgemessen und bei falschem Vorzeichen
    korrigiert wird — in welche Richtung die Normale der Fusion-Basisebenen
    zeigt, ist nicht verlaesslich vorhersagbar."""
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




def ebene_x(comp, x_mm, name):
    """Ebene senkrecht zu Maschinen-X. Skizzenkoordinaten (Maschine Y, Z)."""
    return _offsetebene(comp, comp.yZConstructionPlane, x_mm / 10.0, 'x', name)


def ebene_z(comp, z_mm, name):
    """Waagerechte Ebene. Skizzenkoordinaten (Maschine X, Y)."""
    return _offsetebene(comp, comp.xZConstructionPlane, z_mm / 10.0, 'y', name)


def skizze(comp, ebene, name):
    sk = comp.sketches.add(ebene)
    sk.name = name
    return sk


def _ebene_info(sk):
    """Welche Maschinenachse steht senkrecht auf der Skizzenebene, und wo
    liegt die Ebene? Aus der echten Ebenengeometrie gelesen."""
    pl = adsk.core.Plane.cast(sk.referencePlane.geometry)
    if abs(pl.normal.z) > 0.9:       # Modell-Z = Maschine Y
        return 'y', pl.origin.z * 10.0
    if abs(pl.normal.x) > 0.9:       # Modell-X = Maschine X
        return 'x', pl.origin.x * 10.0
    return 'z', pl.origin.y * 10.0   # Modell-Y = Maschine Z


def punkt(sk, u_mm, v_mm):
    """Punkt in Maschinenkoordinaten -> Skizzenkoordinaten (cm).
    Ebene senkrecht zu Y: (u, v) = (X, Z); zu X: (Y, Z); zu Z: (X, Y).
    Der Umweg ueber modelToSketchSpace macht das Ergebnis unabhaengig davon,
    wie Fusion die Achsen der Ebene orientiert."""
    fest, wert = _ebene_info(sk)
    if fest == 'y':
        modell = adsk.core.Point3D.create(u_mm / 10.0, v_mm / 10.0, wert / 10.0)
    elif fest == 'x':
        modell = adsk.core.Point3D.create(wert / 10.0, v_mm / 10.0, u_mm / 10.0)
    else:
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


def langloch(sk, u, v, breite_mm, hub_mm):
    """Langloch laengs der v-Achse der Skizze (+-hub_mm um v) als zwei Kreise
    plus Rechteck. Geschnitten werden ALLE Profile der Skizze; die
    Vereinigung ergibt das Langloch (in ToolheadZ als langloch_senkrecht
    gelaufen)."""
    r = breite_mm / 2.0
    kreis(sk, u, v - hub_mm, breite_mm)
    kreis(sk, u, v + hub_mm, breite_mm)
    rechteck(sk, u - r, v - hub_mm, u + r, v + hub_mm)




def groesstes_profil(sk):
    """Flaechengroesstes Profil einer Skizze (nie blind profiles.item(0))."""
    return max((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: p.areaProperties().area)


def alle_profile(sk):
    coll = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        coll.add(sk.profiles.item(i))
    return coll




def _symmetrisch(comp, prof, laenge_mm, operation, ziel=None):
    """Extrusion symmetrisch um die Skizzenebene (Gesamtlaenge laenge_mm):
    die Richtung der Ebenennormale spielt dann keine Rolle."""
    ein = comp.features.extrudeFeatures.createInput(prof, operation)
    ein.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(laenge_mm / 10.0), True)
    if ziel is not None:
        ein.participantBodies = [ziel]
    return comp.features.extrudeFeatures.add(ein)


def neu_mittig(comp, prof, dicke_mm):
    """Neuer Koerper, symmetrisch um die Skizzenebene (aus ToolheadZ)."""
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


def durch(comp, prof, ziel, reichweite_mm=400.0):
    """Durchgangsschnitt, symmetrisch und grosszuegig statt ThroughAll;
    participantBodies begrenzt ihn auf den Zielkoerper."""
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
    Maschinenkoordinaten — eine anders orientierte Skizzenachse wirft in
    Fusion keinen Fehler. erwartet: ((x0,x1),(y0,y1),(z0,z1)) in mm."""
    bb = koerper.boundingBox
    ist = ((bb.minPoint.x * 10, bb.maxPoint.x * 10),
           (bb.minPoint.z * 10, bb.maxPoint.z * 10),
           (bb.minPoint.y * 10, bb.maxPoint.y * 10))
    for achse, i, e in zip('XYZ', ist, erwartet):
        if abs(i[0] - e[0]) > toleranz or abs(i[1] - e[1]) > toleranz:
            fehler.append('{}: {} liegt {:.1f}..{:.1f}, erwartet {:.1f}..{:.1f}'
                          .format(name, achse, i[0], i[1], e[0], e[1]))


def fussfase(comp, koerper, achse, wert_mm, fase_mm, fehler, was):
    """Fase gegen den Elefantenfuss an der Auflageflaeche."""
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
        fehler.append('{}: Fussfase uebersprungen — Anlageflaeche pruefen!'
                      .format(was))


# --- Bauteil -----------------------------------------------------------------
def bau_halter(app, design, comp, L, fehler):
    """Y-Motorhalter, ein Druckteil, symmetrisch zur Mitte der 2040.

    PLATTE vor der Stirnseite: der Motor haengt darunter, Flansch an ihrer
    Unterseite, Welle nach oben; das Ritzel sitzt darueber in Hoehe der
    oberen Nut. Zentrierbund und Motorschrauben in Langloechern laengs der
    2040 — der Motor rueckt darin zum Spannen vom Profil weg.
    JOCH: Wand quer vor der Stirnseite, liegt an ihr an (Anschlag) und
    verbindet alles. SCHENKEL an beiden Seitenflaechen, je zwei M5 in die
    untere Nut. FUEHRUNGSWAENDE links und rechts neben dem Motor unter der
    Platte: fuehren ihn beim Spannen und steifen die Platte aus.

    Unter der Platte ist der Motor vorn und unten offen, er wird von unten
    eingesetzt. An den Seitenflaechen endet der Halter unter der oberen Nut.

    Drucklage: OBERSEITE (Platte, Joch, Schenkel, Waende buendig) aufs Bett.
    Alles waechst senkrecht aus der Platte — keine Stuetzen. Die Motor-
    auflage ist dann Oberseite, die Langloecher stehen senkrecht."""
    hb = L['halbe_breite']
    z0, z1 = L['halter_z0'], L['halter_z1']

    # Platte
    e_platte = ebene_z(comp, (L['platte_z0'] + L['platte_z1']) / 2.0,
                       'E_Platte_mitte')
    sk = skizze(comp, e_platte, 'Sk_Platte')
    rechteck(sk, -hb, 0.0, hb, L['platte_y1'])
    koerper = neu_mittig(comp, groesstes_profil(sk),
                         w('platte_dicke')).bodies.item(0)
    koerper.name = 'YMotorhalter'

    # Rahmen in voller Hoehe: Joch, Schenkel, Fuehrungswaende
    e_rahmen = ebene_z(comp, (z0 + z1) / 2.0, 'E_Rahmen_mitte')
    sk = skizze(comp, e_rahmen, 'Sk_Rahmen')
    rechteck(sk, -hb, 0.0, hb, L['joch_y1'])
    for sx in (-1, 1):
        rechteck(sk, sx * L['wange_x0'], L['wange_y0'], sx * L['wange_x1'],
                 0.0)
        rechteck(sk, sx * L['fuehrung_x0'], 0.0, sx * hb, L['platte_y1'])
    dazu_mittig(comp, alle_profile(sk), z1 - z0, koerper)

    # M5 fuer die Nutensteine: quer durch beide Schenkel
    sk = skizze(comp, ebene_x(comp, 0.0, 'E_Mitte_X'), 'Sk_Bohrungen_M5')
    for y, z in L['m5_loecher']:
        kreis(sk, y, z, w('m5_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Zentrierbund und Welle: ein Langloch durch die Platte
    sk = skizze(comp, e_platte, 'Sk_Bundschlitz')
    langloch(sk, 0.0, L['motor_y_mitte'], L['bund_schlitz_b'],
             w('spann_weg') / 2.0)
    durch(comp, alle_profile(sk), koerper)

    # Motorschrauben: Langloecher laengs der 2040 ueber den Spannweg
    sk = skizze(comp, e_platte, 'Sk_Langloecher_Motor')
    for x, y in L['motor_langloecher']:
        langloch(sk, x, y, w('m3_durchgang'), w('spann_weg') / 2.0)
    durch(comp, alle_profile(sk), koerper)

    fussfase(comp, koerper, 'y', z1, w('fase_fuss'), fehler, 'Y-Motorhalter')
    bbox_pruefen(koerper, 'Y-Motorhalter',
                 ((-hb, hb), (L['wange_y0'], L['platte_y1']), (z0, z1)),
                 fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/y_motorhalter_check.py)."""
    p = L['profil_name']
    h = [
        'BEZUG: Y = 0 ist die Stirnseite der {}, +Y zeigt vom Profil weg;'
        .format(p),
        '  Z = 0 ist ihre Unterkante, X = 0 ihre Mitte. Im Modell sind Y und',
        '  Z getauscht. Das Teil ist symmetrisch: dasselbe fuer links und',
        '  rechts, zweimal drucken.',
        '',
        'RIEMEN: laeuft in den OBEREN Nuten beider Seitenflaechen (Z = {:.0f})'
        .format(L['riemen_z']),
        '  und am Profilende um das Ritzel {:.0f} Z direkt auf der Motorwelle.'
        .format(w('ritzel_z')),
        '  Motorachse mittig (X = 0), {:.2f} bis {:.2f} mm vor der Stirnseite.'
        .format(L['motor_y_min'], L['motor_y_max']),
        '  Trume bei X = +-{:.2f} (Wirklinie): Ruecken {:.1f} mm, Zahnspitzen'
        .format(L['rp'], L['trum_tiefe_ruecken']),
        '  {:.1f} mm hinter der Seitenflaeche — {:.1f} mm Luft zur Lippe, {:.1f}'
        .format(L['trum_tiefe_zahn'], L['luft_lippe'], L['luft_nutgrund']),
        '  zum Nutgrund. 180 Grad umschlungen, {:.0f} Zaehne im Eingriff,'
        .format(L['zaehne_im_eingriff']),
        '  {:.0f} mm je Motorumdrehung.'.format(L['mm_pro_umdrehung']),
        '',
        'MOTOR haengt unter der Platte, Welle nach oben: Flansch bei Z = {:+.1f},'
        .format(L['motor_flansch_z']),
        '  Motor bis Z = {:+.1f} ({:.0f}er), also {:.1f} mm unter der {}.'.format(
            L['motor_z0'], w('motor_laenge'), -L['motor_z0'], p),
        '  RITZEL mit der Nabe nach UNTEN bis ans Wellenende schieben (Ober-',
        '  kante = Wellenende, Z = {:+.1f}): dann sitzt die Spur in der oberen'
        .format(L['welle_z1']),
        '  Nut, {:.1f} mm ueber der Platte. Eine Madenschraube (Z = {:+.1f}) auf'
        .format(L['ritzel_luft'], L['madenschraube_z']),
        '  die Abflachung.',
        '',
        'SPANNEN: der Motor rueckt in Langloechern +-{:.0f} mm laengs der {};'
        .format(w('spann_weg') / 2.0, p),
        '  jeder mm macht den Riemenweg 2 mm laenger ({:.0f} mm Verstellung).'
        .format(L['riemen_verstellung']),
        '  Motor vom Profil weg ziehen, dann die 4 M3 von oben festziehen.',
        '',
        'VERSCHRAUBUNG:',
        '  Halter -> {} ...... {}x M5x{:.0f} + Scheibe + Nutenstein M5 (Nut 6) in'
        .format(p, L['n_m5'], L['m5_schraube']),
        '                        den UNTEREN Nuten beider Seiten, {:.1f} mm'
        .format(L['m5_eingriff']),
        '                        Eingriff. Die oberen Nuten bleiben frei.',
        '  NEMA 17 -> Platte ... 4x M3x{:.0f} + Scheibe von oben, {:.1f} mm'
        .format(L['motor_schraube'], L['motor_eingriff']),
        '                        Eingriff',
        '',
        'DRUCK (PETG, Bambu Lab A1): OBERSEITE (Z = {:+.1f}) aufs Bett, also'
        .format(L['halter_z1']),
        '  kopfueber. Joch, Schenkel und Fuehrungswaende wachsen senkrecht',
        '  aus der Platte, {:.1f} mm hoch — keine Stuetzen. Die Motorauflage'
        .format(L['halter_z1'] - L['halter_z0']),
        '  ist dann Oberseite und plan. 4 Wandlinien, >= 40 % Infill. PETG,',
        '  weil der Motor warm wird.',
        '',
        'FREIRAUM: vor der Stirnseite bis Y = {:.1f}, unter der {} bis'
        .format(L['platte_y1'], p),
        '  Z = {:+.1f} (Motor). Nichts ragt ueber ihre Oberkante (hoechster'
        .format(L['motor_z0']),
        '  Punkt: Ritzel, Z = {:+.1f}), an den Seitenflaechen endet der Halter'
        .format(L['ritzel_z1']),
        '  bei Z = {:+.1f}, unter der oberen Nut.'.format(L['halter_z1']),
        '',
        'KEINE BOHRLEHRE: die {} wird nicht gebohrt (Nutensteine), das'.format(
            p),
        '  NEMA-17-Lochbild sitzt schon an der Z-Achse, die Langloecher',
        '  gleichen laengs aus.',
        '',
        'Nach dem Aendern von MASSE: Skript neu laufen lassen und',
        '  python3 tools/y_motorhalter_check.py ausfuehren.',
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
            if up.itemByName(name) is not None:
                continue
            if name in EINHEITENLOS:
                up.add(name, adsk.core.ValueInput.createByReal(wert), '',
                       kommentar)
            else:
                up.add(name, adsk.core.ValueInput.createByString(
                    '{} mm'.format(wert)), 'mm', kommentar)

        L = lage()
        bau_halter(app, design, root, L, fehler)

        app.activeViewport.fit()
        validierungs_bericht(app, design, ui,
                             hinweise=hinweise_bauen(L, fehler))

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
