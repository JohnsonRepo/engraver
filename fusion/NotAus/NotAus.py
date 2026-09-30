# NotAus.py — Gehaeuse fuer den Not-Aus vorn am vorderen 2060
#
# Ein Druckteil, dazu Referenzteile nur zur Ansicht:
#   Gehaeuse_NotAus  offener Kasten vor der Vorderseite des vorderen 2060,
#               rechts innen neben dem rechten 2040. Die Frontwand traegt den
#               Pilztaster (Gewinde durch, Mutter innen), die Rueckseite ist
#               offen und liegt am 2060 an. Links und rechts eine Lasche mit
#               M5 in einer Hammermutter der mittleren Nut; laengs der Nut
#               laesst sich das Gehaeuse verschieben. Zwei 45-Grad-Rippen an
#               den Kanten jeder Lasche tragen sie beim Druck (Front aufs
#               Bett) und lassen Schraube, Scheibe und Inbus frei. Rechts
#               oben der Kabeldurchlass, davor und dahinter je ein Schlitz
#               fuer einen Kabelbinder (Zugentlastung).
#   Referenz_nicht_drucken  vorderes 2060, rechtes 2040 vorn, Y-Motorhalter
#               und Motor rechts (als Huelle, wie YMotorhalter.py) und der
#               Taster.
#
# Der Taster [v] (Bild und Angabe vom 2026-09-30): Pilzkopf, rastet beim
# Druecken ein, Drehen loest; ein Wechsler C, NO, NC mit Loetfahnen, Gewinde
# 16 mm. Verdrahtet wird C und NC (Oeffner) in der 24-V-Leitung, NO bleibt
# frei (docs/verkabelung.md). Kopf, Tiefe und Mutter sind nicht gemessen [?]:
# sie dienen nur der Referenz und der Pruefung, das Gehaeuse hat Reserve.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: X nach rechts, Y nach
# vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im Fusion-Modell
# sind Y und Z getauscht (Modell-Z = Maschine Y). tools/notaus_check.py
# vergleicht die Rahmenmasse mit Portal.py und den Motorhalter mit
# YMotorhalter.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'NotAus'
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen (wie Portal.py) [v] -----------------------------------------
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_y1':          (240.0, 'Rahmen: vordere Stirnseite der 2040'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'quer_y0':            (185.0, 'vorderes 2060: Rueckseite'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
    'nut_mitte':           (10.0, 'Profil: Nutmitte 10 mm von der Kante'),
    # V-Slot vereinfacht (Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),

    # --- Y-Motorhalter rechts, Huelle (wie YMotorhalter.py) [v] -------------
    # Y ab der Stirnseite der 2040, Z ab ihrer Unterkante, X ab ihrer Mitte
    'ymh_halbe_b':        (26.15, 'Y-Motorhalter: halbe Breite'),
    'ymh_y0':             (-30.0, 'Y-Motorhalter: Schenkel hinten'),
    'ymh_y1':              (56.8, 'Y-Motorhalter: Platte vorn'),
    'ymh_z0':               (1.0, 'Y-Motorhalter: unten'),
    'ymh_z1':              (17.5, 'Y-Motorhalter: oben'),
    'motor_b':             (42.3, 'NEMA 17: Flansch'),
    'motor_y_min':        (26.15, 'Motorachse ganz innen'),
    'motor_y_max':        (34.15, 'Motorachse ganz aussen'),
    'motor_z0':           (-25.5, 'Motor unten'),
    'motor_z1':            (11.5, 'Motorflansch = Platte unten'),

    # --- Taster (Pilzkopf, Wechsler C/NO/NC) --------------------------------
    # Rev. 2: Gewinde 16 mm [v] Angabe 2026-09-30 (Rev. 1: 19 mm angenommen).
    # Kopf, Tiefe, Mutter und Klemmbereich sind nicht gemessen [?].
    'schalter_d':          (16.0, 'Not-Aus: Gewindedurchmesser [v] Angabe'),
    'schalter_spiel':       (0.3, 'Loch so viel groesser als das Gewinde'),
    'schalter_kopf_d':     (32.0, 'Not-Aus: Pilzkopf [?]'),
    'schalter_kopf_h':     (22.0, 'Not-Aus: Kopf vor der Frontwand [?]'),
    'schalter_tiefe':      (30.0, 'Not-Aus: hinter der Frontwand mit Loetfahnen [?]'),
    'schalter_mutter':     (24.0, 'Not-Aus: Mutter ueber Eck [?]'),
    'klemm_max':            (6.0, 'Not-Aus: so dick darf die Wand sein [?]'),
    'draht_biegen':        (10.0, 'hinter den Loetfahnen fuer die Litze'),

    # --- Gehaeuse -----------------------------------------------------------
    # rechts innen neben dem rechten 2040, gut mit der rechten Hand; laengs der
    # mittleren Nut verschiebbar
    'na_x':               (180.0, 'Gehaeuse: Mitte in X'),
    'na_b':                (50.0, 'Gehaeuse: Breite (X)'),
    'na_h':                (50.0, 'Gehaeuse: Hoehe (Z)'),
    'na_t':                (46.0, 'Gehaeuse: Tiefe vor dem 2060 (Y)'),
    'na_wand':              (3.0, 'Gehaeuse: Seiten, oben, unten'),
    'na_front':             (3.0, 'Gehaeuse: Frontwand, der Taster klemmt darauf'),
    'lasche_b':            (14.0, 'Lasche: neben dem Gehaeuse (X)'),
    'lasche_h':            (20.0, 'Lasche: Hoehe (Z)'),
    'lasche_t':             (6.0, 'Lasche: Dicke an der Anlage (Y)'),
    'rippe_d':              (3.0, 'Rippe an der Laschenkante: Dicke (Z)'),
    'kabel_d':              (7.0, 'Kabeldurchlass (2 x 0,75 mm2, aussen ~6)'),
    'kabel_z_oben':         (8.0, 'Kabeldurchlass: Mitte so weit unter der Oberkante'),
    'kabel_y':             (14.0, 'Kabeldurchlass: Mitte so weit vor dem 2060'),
    'binder_b':             (4.5, 'Schlitz fuer den Kabelbinder (Z)'),
    'binder_t':             (2.5, 'Schlitz fuer den Kabelbinder (Y)'),
    'binder_abstand':       (9.0, 'Schlitze so weit vor und hinter dem Durchlass'),

    # --- Normteile und Regeln ------------------------------------------------
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_scheibe_d':        (10.0, 'M5 Scheibe DIN 125: Durchmesser'),
    'm5_scheibe_h':         (1.0, 'M5 Scheibe DIN 125: Dicke'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'luft_bau':             (3.0, 'Mindestfreigang'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/notaus_check.py)."""
    L = {}
    R = w('y_schienen_abstand') / 2.0
    L['R'] = R
    L['quer_y'] = (w('quer_y0'), w('quer_y0') + w('rahmen_b'))
    L['quer_z'] = (w('rahmen_z0') - w('quer_h'), w('rahmen_z0'))
    L['tisch_z'] = L['quer_z'][0]
    # Nuten der Vorderseite des 2060: oben, Mitte, unten
    L['nuten_z'] = [L['quer_z'][1] - w('nut_mitte') - 2.0 * w('nut_mitte')
                    * i for i in range(3)]
    zm = L['nuten_z'][1]
    L['zm'] = zm

    # ---- Gehaeuse: liegt an der Vorderseite des 2060, Mitte auf der
    #      mittleren Nut ------------------------------------------------------
    y0 = L['quer_y'][1]
    x, b, h, t = w('na_x'), w('na_b'), w('na_h'), w('na_t')
    L['geh_x'] = (x - b / 2.0, x + b / 2.0)
    L['geh_y'] = (y0, y0 + t)
    L['geh_z'] = (zm - h / 2.0, zm + h / 2.0)
    wd = w('na_wand')
    L['innen_x'] = (L['geh_x'][0] + wd, L['geh_x'][1] - wd)
    L['innen_z'] = (L['geh_z'][0] + wd, L['geh_z'][1] - wd)
    L['front_y'] = (L['geh_y'][1] - w('na_front'), L['geh_y'][1])
    L['innen_y'] = (y0, L['front_y'][0])
    L['loch_d'] = w('schalter_d') + w('schalter_spiel')
    L['schalter'] = (x, zm)

    # ---- Laschen mit M5, Rippen an ihren Kanten ----------------------------
    lb, lh, lt = w('lasche_b'), w('lasche_h'), w('lasche_t')
    L['lasche_x'] = [(L['geh_x'][0] - lb, L['geh_x'][0]),
                     (L['geh_x'][1], L['geh_x'][1] + lb)]
    L['lasche_y'] = (y0, y0 + lt)
    L['lasche_z'] = (zm - lh / 2.0, zm + lh / 2.0)
    L['m5'] = [((a + c) / 2.0, zm) for a, c in L['lasche_x']]
    # Scheibe 1 + Lasche 6, dann 5 mm in die Nut: 1,8 Lippe, 3,2 im Stein,
    # 1 mm vor dem Nutgrund (wie Halter_Y in Endschalter.py)
    L['m5_schraube'] = 12.0
    rd = w('rippe_d')
    L['rippe_z'] = [(L['lasche_z'][0], L['lasche_z'][0] + rd),
                    (L['lasche_z'][1] - rd, L['lasche_z'][1])]
    ya = y0 + lt
    L['rippen'] = []
    for (lx0, lx1), wand in zip(L['lasche_x'], (L['geh_x'][0],
                                                 L['geh_x'][1])):
        aussen = lx0 if wand == lx1 else lx1
        # 45 Grad: so weit an der Wand nach vorn, wie die Lasche breit ist
        L['rippen'].append([(wand, ya), (aussen, ya), (wand, ya + lb)])

    # ---- Kabeldurchlass rechts oben, Schlitze fuer den Kabelbinder ---------
    ky = y0 + w('kabel_y')
    kz = L['geh_z'][1] - w('kabel_z_oben')
    L['kabel'] = (ky, kz)
    ba = w('binder_abstand')
    bb, bt = w('binder_b') / 2.0, w('binder_t') / 2.0
    L['binder'] = [(y - bt, kz - bb, y + bt, kz + bb)
                   for y in (ky - ba, ky + ba)]

    # ---- Taster (Referenz) --------------------------------------------------
    L['kopf_y'] = (L['geh_y'][1], L['geh_y'][1] + w('schalter_kopf_h'))
    L['koerper_y'] = (L['front_y'][0] - w('schalter_tiefe'), L['front_y'][0])

    # ---- Y-Motorhalter und Motor rechts (Huelle, YMotorhalter.py) ----------
    ys, zs = w('rahmen_y1'), w('rahmen_z0')
    hb = w('ymh_halbe_b')
    L['ymh_x'] = (R - hb, R + hb)
    L['ymh_y'] = (ys + w('ymh_y0'), ys + w('ymh_y1'))
    L['ymh_z'] = (zs + w('ymh_z0'), zs + w('ymh_z1'))
    mb = w('motor_b') / 2.0
    L['motor_x'] = (R - mb, R + mb)
    L['motor_y'] = (ys + w('motor_y_min') - mb, ys + w('motor_y_max') + mb)
    L['motor_z'] = (zs + w('motor_z0'), zs + w('motor_z1'))
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




def vieleck(sk, punkte):
    """Geschlossener Linienzug, Punkte in Maschinenkoordinaten (u, v wie bei
    rechteck). Die Ecken sind ueber die SketchPoints der Nachbarlinien
    verkettet (wie sechskant in ToolheadZ.py), damit das Profil sicher
    schliesst."""
    linien = sk.sketchCurves.sketchLines
    erste = linien.addByTwoPoints(punkt(sk, *punkte[0]), punkt(sk, *punkte[1]))
    vorher = erste
    for p in punkte[2:]:
        vorher = linien.addByTwoPoints(vorher.endSketchPoint, punkt(sk, *p))
    linien.addByTwoPoints(vorher.endSketchPoint, erste.startSketchPoint)


def prisma_vieleck(comp, name, achse, punkte, a0, a1, art, ziel=None):
    """Vieleck quer zu `achse` (u, v wie bei prismen), entlang `achse` von a0
    bis a1, symmetrisch um die Mitte extrudiert."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, achse, m, 'E_{}_{}{:.1f}'.format(
        comp.name, achse.upper(), m)), 'Sk_' + name)
    vieleck(sk, punkte)
    return _symmetrisch(comp, groesstes_profil(sk), abs(a1 - a0), _op(art),
                        ziel)


def bau_gehaeuse(app, design, comp, L, fehler):
    """Gehaeuse vor dem vorderen 2060: Kasten mit offener Rueckseite, Frontwand
    mit dem Loch fuer den Taster, Laschen mit M5, Rippen, Kabeldurchlass.

    Drucklage: Frontwand aufs Bett, die Waende stehen senkrecht, die Laschen
    liegen oben und werden an ihren Kanten von 45-Grad-Rippen getragen,
    dazwischen eine kurze Bruecke — keine Stuetzen. Gelb drucken, wenn
    vorhanden: roter Pilz auf gelbem Grund ist die uebliche Kennzeichnung."""
    gx, gy, gz = L['geh_x'], L['geh_y'], L['geh_z']
    k = quader(comp, 'Kasten_NA', gx, gy, gz, 'neu').bodies.item(0)
    k.name = 'Gehaeuse_NotAus'
    quader(comp, 'Innen_NA', L['innen_x'], (gy[0] - 1.0, L['front_y'][0]),
           L['innen_z'], 'weg', k)
    x, zm = L['schalter']
    bohrung(comp, 'Taster_NA', 'y', [(x, zm)], L['loch_d'],
            L['front_y'][0] - 1.0, L['front_y'][1] + 1.0, k)
    for i, lx in enumerate(L['lasche_x']):
        quader(comp, 'Lasche_NA_{}'.format(i + 1), lx, L['lasche_y'],
               L['lasche_z'], 'dazu', k)
        for j, rz in enumerate(L['rippe_z']):
            prisma_vieleck(comp, 'Rippe_NA_{}{}'.format(i + 1, j + 1), 'z',
                           L['rippen'][i], rz[0], rz[1], 'dazu', k)
    bohrung(comp, 'M5_NA', 'y', L['m5'], w('m5_durchgang'), gy[0] - 1.0,
            L['lasche_y'][1] + 1.0, k)
    wand = (L['geh_x'][1] - w('na_wand') - 1.0, L['geh_x'][1] + 1.0)
    bohrung(comp, 'Kabel_NA', 'x', [L['kabel']], w('kabel_d'), wand[0],
            wand[1], k)
    prismen(comp, 'Binder_NA', 'x', L['binder'], wand[0], wand[1], 'weg', k)
    fussfase(comp, k, 'z', gy[1], w('fase_fuss'), fehler, 'Gehaeuse_NotAus')
    bbox_pruefen(k, 'Gehaeuse_NotAus', ((L['lasche_x'][0][0],
                                         L['lasche_x'][1][1]), gy, gz),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_referenz(app, design, teile, L, fehler):
    """Vorderes 2060, rechtes 2040 vorn, Y-Motorhalter und Motor rechts als
    Huelle und der Taster — nur zur Ansicht, NICHT drucken. Jedes Teil wird
    fuer sich gebaut: scheitert eines, steht das im Bericht."""
    R, b = L['R'], w('rahmen_b')

    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    def box(comp, name, x, y, z, mat):
        def bauen():
            kk = quader(comp, name, x, y, z, 'neu').bodies.item(0)
            kk.name = name
            return kk
        k = sicher(name, bauen)
        if k:
            material_zuweisen(app, design, k, mat, fehler)
        return k

    def rund(comp, name, mitte, d, a0, a1, mat):
        def bauen():
            kk = zylinder(comp, name, 'y', mitte, d, a0, a1,
                          'neu').bodies.item(0)
            kk.name = name
            return kk
        k = sicher(name, bauen)
        if k:
            material_zuweisen(app, design, k, mat, fehler)
        return k

    pr = teile['Ref_Rahmen']
    z0 = w('rahmen_z0')
    for name, laengs, bereich, quer, z in (
            ('2060_vorn', 'x', (L['geh_x'][0] - 60.0, R + 43.0),
             L['quer_y'], L['quer_z']),
            ('2040_rechts', 'y', (L['quer_y'][0] - 40.0, w('rahmen_y1')),
             (R - b / 2.0, R + b / 2.0), (z0, z0 + w('rahmen_h')))):
        k = sicher(name, bau_profil, pr, name, laengs, bereich, quer, z)
        if k:
            material_zuweisen(app, design, k, 'Aluminum 6061', fehler)

    ym = teile['Ref_YMotor']
    box(ym, 'YMotorhalter_rechts', L['ymh_x'], L['ymh_y'], L['ymh_z'],
        'PETG')
    box(ym, 'Motor_rechts', L['motor_x'], L['motor_y'], L['motor_z'],
        'Steel')

    ta = teile['Ref_Taster']
    rund(ta, 'Pilzkopf', L['schalter'], w('schalter_kopf_d'), *L['kopf_y'],
         'Kunststoff')
    rund(ta, 'Tasterkoerper', L['schalter'], w('schalter_d'),
         *L['koerper_y'], 'Steel')


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/notaus_check.py)."""
    x, zm = L['schalter']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py (X rechts, Y nach vorn).',
        '  Das Gehaeuse liegt an der Vorderseite des vorderen 2060, Mitte bei',
        '  X {:+.0f}, auf der mittleren Nut (Z {:+.0f}).'.format(x, zm),
        '',
        'GEHAEUSE: 2 Hammermuttern M5 in die mittlere Nut vorn am 2060,',
        '  2 x M5x{:.0f} mit Scheibe durch die Laschen. Laengs der Nut'.format(
            L['m5_schraube']),
        '  verschiebbar; rechts bleibt Abstand zum Y-Motorhalter.',
        'TASTER: Gewinde Ø{:.0f} [v], von vorn durch das Loch (Ø{:.1f}),'.format(
            w('schalter_d'), L['loch_d']),
        '  Mutter innen. Vor dem Einbau anloeten: C und NC (Oeffner), NO',
        '  bleibt frei.',
        'KABEL: rechts oben durch den Durchlass (Ø{:.0f}), innen mit einem'.format(
            w('kabel_d')),
        '  Kabelbinder durch die zwei Schlitze festlegen (Zugentlastung).',
        '',
        'DRUCK (PETG, Bambu Lab A1): Frontwand aufs Bett, keine Stuetzen.',
        '  Gelb, wenn vorhanden. 4 Wandlinien, 30 % Infill.',
        '',
        'NICHT GEMESSEN [?]: Kopf, Tiefe, Mutter und Klemmbereich des',
        '  Tasters; nur fuer Referenz und Pruefung, das Gehaeuse hat Reserve.',
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
        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Gehaeuse_NotAus'
        bau_gehaeuse(app, design, o.component, L, fehler)
        o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Rahmen', 'Ref_YMotor', 'Ref_Taster'):
            oo = ref.component.occurrences.addNewComponent(einheit)
            oo.component.name = name
            teile[name] = oo.component
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
