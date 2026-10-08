# Kabelhalter.py — Kabelhalter fuer die untere Seitennut aussen an den 2040
#
# Ein Druckteil, dazu Referenzteile nur zur Ansicht:
#   Kabelhalter  Anlage aussen an der Seitenflaeche der 2040, mit einer Feder
#               in der Oeffnung der unteren Nut und 1 x M5x10 in einer
#               Hammermutter. Darunter haengt eine offene Rinne, oben mit
#               einer Lippe an der Aussenwand: Die Kabel werden von oben
#               eingelegt und liegen unter der Unterkante der Traegerwaende
#               der Wanne Y, sie gehen dort also ohne Umweg durch. Im Boden
#               ein Fenster fuer einen Kabelbinder, wo die Kabel abzweigen.
#               Derselbe Halter passt links und rechts (um 180 Grad gedreht).
#   Referenz_nicht_drucken  ein Stueck linkes 2040, Hammermutter (vereinfacht)
#               und Schraube.
#
# Gezeigt wird EIN Halter am linken 2040 bei Y = kh_y. Wie viele es braucht
# und wohin sie kommen, rechnet tools/kabelhalter_check.py aus Portal.py
# (Winkel, Traeger der Wanne Y, Halter_Y, Y-Motorhalter) und den Kabeln aus
# tools/verkabelung.py; die Liste steht in docs/kabelhalter.md.
#
# Drucklage: der Querschnitt liegt flach, die Seite mit der Fase aufs Bett,
# die 16 mm Breite wachsen nach oben. So liegen Rinne, Lippe und Feder ganz
# in der Lage, nichts haengt ueber; das Loch fuer die M5 ist eine Traene mit
# der Spitze nach oben.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: X nach rechts, Y nach
# vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im Fusion-Modell
# sind Y und Z getauscht (Modell-Z = Maschine Y).
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback
import math

SKRIPT_NAME = 'Kabelhalter'
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen (wie Portal.py) [v] -----------------------------------------
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'nut_mitte':           (10.0, 'Profil: Nutmitte 10 mm von der Kante'),
    # Nut 6 [w], wie Portal.py
    'nut_lippe':            (1.8, 'Nut 6: Dicke der Lippe'),
    'nut_tiefe':            (6.0, 'Nut 6 (2040): Platz ab Profilflaeche bis zum Nutgrund'),
    'nutenstein_h':         (4.0, 'Nutenstein M5: Gewindelaenge'),
    # V-Slot vereinfacht (nur Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),

    # --- Halter ---------------------------------------------------------------
    # Rev. 1: erster Stand.
    # Rev. 2: Feder um die Schraube ganz weg (Rev. 1 liess neben der Traene
    #         nur 0,15 mm duenne Stege stehen).
    'kh_y':              (-173.0, 'Modell: Mitte des gezeigten Halters (Maschine Y)'),
    'kh_b':                (16.0, 'Halter: Breite laengs der Nut'),
    # M5x10 ohne Scheibe: 4,5 Anlage, dann 5,5 in der Nut — 3,7 im Stein,
    # 0,5 vor dem Nutgrund
    'anlage_t':             (4.5, 'Anlage am 2040: Dicke'),
    'anlage_oben':          (7.0, 'Anlage: reicht so weit ueber die Nutmitte'),
    'feder_b':              (5.8, 'Feder in der Nutoeffnung: Breite'),
    'feder_t':              (1.5, 'Feder: Tiefe (kuerzer als die Lippe der Nut)'),
    'feder_luft':           (0.5, 'Feder: endet so weit vor der Traene'),
    # Rinne: Oberkante 7 unter der Nutmitte = 3 ueber der Unterkante der
    # 2040, also unter den Traegerwaenden der Wanne Y (enden 4 darueber)
    'kanal_oben':           (7.0, 'Rinne: Oberkante so weit unter der Nutmitte'),
    'kanal_b':             (13.0, 'Rinne: lichte Breite (vom 2040 weg)'),
    'kanal_h':             (12.0, 'Rinne: lichte Hoehe'),
    'kanal_wand':           (2.5, 'Rinne: Boden und Aussenwand'),
    'lippe_b':              (3.0, 'Lippe oben an der Aussenwand: ragt so weit nach innen'),
    'lippe_h':              (2.0, 'Lippe: Dicke'),
    'zwickel':              (1.5, 'Fase in der Ecke Boden/Aussenwand'),
    'binder_b':             (4.0, 'Fenster fuer den Kabelbinder: laengs (Y)'),
    'binder_t':             (2.2, 'Fenster fuer den Kabelbinder: quer'),
    'binder_abstand':       (0.5, 'Fenster: so weit neben der Anlage'),

    # --- Normteile und Regeln ------------------------------------------------
    'm5_l':                (10.0, 'Schraube M5x10 (Zylinderkopf, ohne Scheibe)'),
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'hammer_b':             (6.0, 'Hammermutter M5: laengs der Nut (Referenz)'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def flaeche(punkte):
    """Flaeche eines Vielecks (Gausssche Trapezformel), mm2."""
    s = 0.0
    for (a0, b0), (a1, b1) in zip(punkte, punkte[1:] + punkte[:1]):
        s += a0 * b1 - a1 * b0
    return abs(s) / 2.0


def lage():
    """Querschnitt und Lage in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/kabelhalter_check.py).

    Der Querschnitt steht in (a, z): a ist der Abstand von der Aussenflaeche
    der 2040 nach aussen (negativ = in der Nut), z die Hoehe ueber der
    Mitte der unteren Seitennut."""
    L = {}
    R = w('y_schienen_abstand') / 2.0
    L['R'] = R
    L['flaeche_x'] = -R - w('rahmen_b') / 2.0      # aussen am linken 2040
    L['rahmen_z'] = (w('rahmen_z0'), w('rahmen_z0') + w('rahmen_h'))
    L['nut_z'] = w('rahmen_z0') + w('nut_mitte')   # untere Seitennut
    L['unterkante'] = -w('nut_mitte')              # Unterkante der 2040

    t, ob = w('anlage_t'), w('anlage_oben')
    ko = -w('kanal_oben')
    kb, kh, kw = w('kanal_b'), w('kanal_h'), w('kanal_wand')
    lb, lh, zw = w('lippe_b'), w('lippe_h'), w('zwickel')
    fb, ft = w('feder_b') / 2.0, w('feder_t')
    aw = t + kb                         # Innenseite der Aussenwand
    aa = aw + kw                        # aussen
    zb = ko - kh                        # Boden der Rinne (oben)
    zu = zb - kw                        # Unterkante des Halters
    L['a'], L['z'] = (-ft, aa), (zu, ob)
    L['anlage_a'], L['feder_a'] = (0.0, t), (-ft, 0.0)
    L['feder_z'] = (-fb, fb)
    L['kanal_a'], L['kanal_z'] = (t, aw), (zb, ko)
    L['wand_a'] = (aw, aa)
    L['lippe_a'], L['lippe_z'] = (aw - lb, aa), (ko - lh, ko)
    L['oeffnung'] = aw - lb - t         # oben frei zwischen Anlage und Lippe
    L['querschnitt'] = [
        (0.0, ob), (0.0, fb), (-ft, fb), (-ft, -fb), (0.0, -fb),
        (0.0, zu), (aa, zu), (aa, ko), (aw - lb, ko), (aw - lb, ko - lh),
        (aw, ko - lh), (aw, zb + zw), (aw - zw, zb), (t, zb), (t, ob)]
    # lichter Raum fuer die Kabel, oben bis zur Oberkante der Lippe
    L['kanal'] = [(t, ko), (aw - lb, ko), (aw - lb, ko - lh), (aw, ko - lh),
                  (aw, zb + zw), (aw - zw, zb), (t, zb)]
    L['kanal_flaeche'] = flaeche(L['kanal'])

    # M5 in die Hammermutter: Kopf aussen auf der Anlage
    # Feder nur neben der Schraube: um die Traene (Spitze r * Wurzel 2)
    # herum frei, laengs je Seite
    L['feder_luecke'] = (w('m5_durchgang') / 2.0 * math.sqrt(2.0)
                         + w('feder_luft'))
    L['m5_spitze'] = w('m5_l') - t      # so tief in der Nut, ab der Flaeche
    L['m5_eingriff'] = (min(L['m5_spitze'], w('nut_lippe')
                            + w('nutenstein_h')) - w('nut_lippe'))
    L['kopf_a'] = (t, t + w('m5_kopf_h'))
    L['kopf_z'] = (-w('m5_kopf_d') / 2.0, w('m5_kopf_d') / 2.0)

    # Fenster fuer den Kabelbinder im Boden, dicht an der Anlage
    a0 = t + w('binder_abstand')
    L['binder_a'] = (a0, a0 + w('binder_t'))

    # ---- der gezeigte Halter am linken 2040 --------------------------------
    y, hb = w('kh_y'), w('kh_b') / 2.0
    fx, zn = L['flaeche_x'], L['nut_z']
    L['y'] = (y - hb, y + hb)
    L['x'] = (fx - aa, fx + ft)
    L['zm'] = (zn + zu, zn + ob)
    L['punkte'] = [(fx - a, zn + z) for a, z in L['querschnitt']]
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


def traene(comp, name, mitte, d, a0, a1, ziel):
    """Loch Ø d entlang Maschinen-X von a0 bis a1 als Traene: Spitze nach
    +Y, beim Druck also oben (die Seite bei Y-Anfang liegt auf dem Bett).
    mitte = (Y, Z). Die Flanken stehen unter 45 Grad, die Decke druckt so
    ohne Bruecke."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, 'x', m, 'E_{}_X{:.1f}'.format(
        comp.name, m)), 'Sk_' + name)
    y, z = mitte
    r = d / 2.0
    s = r / math.sqrt(2.0)
    bogen = sk.sketchCurves.sketchArcs.addByThreePoints(
        punkt(sk, y + s, z + s), punkt(sk, y - r, z), punkt(sk, y + s, z - s))
    linien = sk.sketchCurves.sketchLines
    l1 = linien.addByTwoPoints(bogen.startSketchPoint,
                               punkt(sk, y + r * math.sqrt(2.0), z))
    linien.addByTwoPoints(l1.endSketchPoint, bogen.endSketchPoint)
    tasche(comp, groesstes_profil(sk), abs(a1 - a0), ziel)


def bau_halter(app, design, comp, L, fehler):
    """Kabelhalter am linken 2040: Querschnitt entlang Y extrudiert, dann
    das Loch fuer die M5 (Traene, auch durch die Feder) und das Fenster fuer
    den Kabelbinder im Boden. Fase am Fuss auf der Seite bei Y-Anfang."""
    k = prisma_vieleck(comp, 'Querschnitt_KH', 'y', L['punkte'], L['y'][0],
                       L['y'][1], 'neu').bodies.item(0)
    k.name = 'Kabelhalter'
    fx, zn = L['flaeche_x'], L['nut_z']
    ym = sum(L['y']) / 2.0
    traene(comp, 'M5_KH', (ym, zn), w('m5_durchgang'),
           fx - w('anlage_t') - 1.0, fx + w('feder_t') + 1.0, k)
    fl, fb = L['feder_luecke'], w('feder_b') / 2.0 + 1.0
    quader(comp, 'Feder_frei_KH', (fx, fx + w('feder_t') + 1.0),
           (ym - fl, ym + fl), (zn - fb, zn + fb), 'weg', k)
    ba, hb = L['binder_a'], w('binder_b') / 2.0
    prismen(comp, 'Binder_KH', 'z', [(fx - ba[1], ym - hb, fx - ba[0],
                                      ym + hb)],
            zn + L['z'][0] - 1.0, zn + L['kanal_z'][0] + 1.0, 'weg', k)
    fussfase(comp, k, 'z', L['y'][0], w('fase_fuss'), fehler, 'Kabelhalter')
    bbox_pruefen(k, 'Kabelhalter', (L['x'], L['y'], L['zm']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_referenz(app, design, comp, L, fehler):
    """Stueck linkes 2040, Hammermutter (vereinfacht, in der Kammer des
    vereinfachten V-Slot) und M5x10 — nur zur Ansicht, NICHT drucken."""
    R, b = L['R'], w('rahmen_b')
    fx, zn = L['flaeche_x'], L['nut_z']
    ym = sum(L['y']) / 2.0

    def sicher(name, mat, bauen, *args):
        try:
            k = bauen(*args)
            if hasattr(k, 'bodies'):
                k = k.bodies.item(0)
            k.name = name
            material_zuweisen(app, design, k, mat, fehler)
            return k
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    sicher('2040_links', 'Aluminum 6061', bau_profil, comp, '2040_links',
           'y', (L['y'][0] - 30.0, L['y'][1] + 30.0),
           (-R - b / 2.0, -R + b / 2.0), L['rahmen_z'])
    hq = w('nut_kammer_b') / 2.0 - 0.1
    hl = w('hammer_b') / 2.0
    sicher('Hammermutter_M5', 'Steel', quader, comp, 'Hammermutter_M5',
           (fx + w('nut_t') + 0.1, fx + w('nut_kammer_t') - 0.1),
           (ym - hl, ym + hl), (zn - hq, zn + hq), 'neu')
    t = w('anlage_t')
    sicher('M5x10_Kopf', 'Steel', zylinder, comp, 'M5x10_Kopf', 'x',
           (ym, zn), w('m5_kopf_d'), fx - t - w('m5_kopf_h'), fx - t, 'neu')
    sicher('M5x10_Schaft', 'Steel', zylinder, comp, 'M5x10_Schaft', 'x',
           (ym, zn), 5.0, fx - t, fx - t + w('m5_l'), 'neu')


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/kabelhalter_check.py)."""
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py (X rechts, Y nach vorn).',
        '  Gezeigt ist ein Halter aussen am linken 2040 bei Y {:+.0f},'.format(
            w('kh_y')),
        '  untere Seitennut (Z {:+.0f}).'.format(L['nut_z']),
        '',
        'MONTAGE: Hammermutter M5 in die untere Seitennut aussen, Halter mit',
        '  der Feder in die Nutoeffnung, Rinne unten. 1 x M5x{:.0f} ohne'.format(
            w('m5_l')),
        '  Scheibe: {:.1f} mm im Stein, Spitze {:.1f} mm vor dem Nutgrund.'
        .format(L['m5_eingriff'], w('nut_tiefe') - L['m5_spitze']),
        '  Rechts derselbe Halter, um 180 Grad gedreht. Plaetze und Anzahl:',
        '  docs/kabelhalter.md (python3 tools/kabelhalter_check.py).',
        'KABEL: von oben einlegen und unter die Lippe schieben; Oeffnung',
        '  {:.0f} mm, Rinne {:.0f} x {:.0f} mm ({:.0f} mm2). Wo Kabel'.format(
            L['oeffnung'], w('kanal_b'), w('kanal_h'), L['kanal_flaeche']),
        '  abzweigen: Kabelbinder durch das Fenster im Boden, um Kabel und',
        '  Aussenwand.',
        '',
        'DRUCK (PETG, Bambu Lab A1): Querschnitt flach, die Seite mit der',
        '  Fase aufs Bett, keine Stuetzen. 4 Wandlinien, 30 % Infill.',
        '',
        'NICHT GEMESSEN [w]: Nut 6 (Lippe 1,8, Platz 6,0 bis zum Nutgrund).',
        '  Ist die Nut flacher, eine Scheibe M5 unter den Kopf legen.',
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

        # Baugruppe nur, um Druckteil und Referenz zu trennen: alle
        # Komponenten am globalen Ursprung, nichts bewegt sich, alles fixiert.
        einheit = adsk.core.Matrix3D.create()
        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Kabelhalter'
        bau_halter(app, design, o.component, L, fehler)
        o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        oo = ref.component.occurrences.addNewComponent(einheit)
        oo.component.name = 'Ref_Rahmen'
        bau_referenz(app, design, oo.component, L, fehler)
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
