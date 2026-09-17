# ToolheadGrundplatte.py — Grundplatte fuer den Laser-Toolhead der Z-Achse
#
# Erzeugt ein Bauteil (ein Koerper) als Versatzplatte:
#   Auflagepad  -> liegt auf der Stirnflaeche des MGN9-Z-Wagens
#   Grundplatte -> traegt den Diodenlaser, um pad_hoehe nach vorn versetzt
#   Rippen      -> Mittelrippe + zwei Seitenrippen auf der Rueckseite
#
# Koordinatensystem (Modell = Druckorientierung, Teil liegt flach auf dem Bett):
#   Modell-X = Maschine X  (quer, laengs des Portals)
#   Modell-Y = Maschine Z  (senkrecht, Verfahrrichtung der Z-Achse)
#   Modell-Z = Maschine Y  (nach vorn, weg vom Portal) — zugleich Druckrichtung
#   Ursprung = Mitte des Wagen-Lochbildes AUF der Stirnflaeche des Z-Wagens
#              (das ist die Passflaeche — genau die Bezugsebene, die beim
#               ersten Versuch gefehlt hat)
#
# Bezugskette in Modell-Z (alles ab Wagen-Stirnflaeche = 0):
#   -wagen_hoehe ............... Auflageebene der MGN9-Schiene (Flaeche der Z-Platte)
#   -wagen_hoehe+schiene_hoehe . Oberkante Schiene  -> 3,5 mm Luft zum Teil
#    0 ......................... Wagen-Stirnflaeche = Rueckseite Pad/Rippen
#    pad_hoehe ................. Rueckseite Grundplatte
#    pad_hoehe+dicke_platte .... Anschraubflaeche des Lasers
#
# Konventionen: siehe fusion-python/SKILL.md (neues Dokument, Bauteil,
# User-Parameter, Material je Koerper, Bohrlehren ausgeblendet, Bericht am Ende).

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'ToolheadGrundplatte'
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
# Status der Kaufteilmasse: siehe docs/hardware-notizen.md.
MASSE = {
    # MGN9-Linearfuehrung Z-Achse (hardware.md, Status [w])
    'wagen_loch_quer':     (15.0,  'MGN9 Wagen: Lochabstand quer'),
    'wagen_loch_laengs':   (16.0,  'MGN9H=16, MGN9C=10 — am Wagen pruefen!'),
    'wagen_breite':        (20.0,  'MGN9 Wagen: Breite (nur Doku/Pruefung)'),
    'wagen_hoehe':         (10.0,  'MGN9 Montagehoehe: Wagenflaeche ueber Schiene'),
    'schiene_hoehe':       (6.5,   'MGN9 Schiene: Hoehe (nur Doku/Pruefung)'),

    # Diodenlaser (Nutzerangabe: Bohrbild 39 hoch x 15 quer, 4 Bohrungen)
    'laser_loch_quer':     (16.5,  'Laser: Lochabstand quer'),
    'laser_loch_hoch':     (40.5,  'Laser: Lochabstand senkrecht'),
    'laser_breite':        (35.0,  'Laser: Gehaeusebreite (nur Doku/Pruefung)'),
    'laser_tiefe':         (35.0,  'Laser: Gehaeusetiefe — treibt die Strahlachse'),

    # Grundplatte
    'platte_breite':       (35.0,  'Grundplatte: Breite (quer)'),
    'platte_hoehe':        (52.0,  'Grundplatte: Hoehe (senkrecht)'),
    'dicke_platte':        (6.0,   'Grundplatte: Dicke'),

    # Auflagepad + Rippen (Rueckseite)
    'pad_hoehe':           (6.0,   'Auflagepad: Versatz Wagenflaeche -> Platte'),
    'pad_breite':          (28.0,  'Auflagepad: Breite'),
    'pad_laenge':          (26.0,  'Auflagepad: Hoehe'),
    'rippe_mitte_breite':  (5.0,   'Mittelrippe: Breite'),
    'rippe_seite_innen':   (13.0,  'Seitenrippe: Innenkante ab Mitte'),

    # Verschraubung
    'm3_durchgang':        (3.4,   'M3 Durchgang (hardware.md)'),
    'm3_senkung':          (6.5,   'Freibohrung fuer M3-Zylinderkopf + Werkzeug'),
    'schlitz_breite':      (4.4,   'Laser-Langloch: Breite (senkrechte Toleranz)'),
    'schlitz_verstellweg': (1.2,   'Laser-Langloch: Mittenversatz quer'),

    # Druckgerecht (references/druckgerecht.md)
    'fase_fuss':           (0.4,   'Fase gegen Elefantenfuss an der Auflageflaeche'),
    'radius_uebergang':    (1.2,   'Verrundung Rippe/Pad -> Platte'),
    'lehre_dicke':         (3.0,   'Bohrlehren: Plattendicke'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def c(name):
    """Wert in cm (API-Einheit fuer Point3D)."""
    return MASSE[name][0] / 10.0


def vi(ausdruck):
    """ValueInput aus einem Parameter-Ausdruck, z.B. 'dicke_platte' oder
    'platte_breite / 2'."""
    return adsk.core.ValueInput.createByString(ausdruck)


def P(x, y):
    """Skizzenpunkt in cm."""
    return adsk.core.Point3D.create(x, y, 0)


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
# -----------------------------------------------------------------------------


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
# -----------------------------------------------------------------------------


# --- Skizzen-Helfer ----------------------------------------------------------
def rechteck(sk, x0, y0, x1, y1):
    """Achsparalleles Rechteck in Skizzenkoordinaten (cm)."""
    return sk.sketchCurves.sketchLines.addTwoPointRectangle(P(x0, y0), P(x1, y1))


def rechteck_kanten(rect):
    """Die vier Linien eines achsparallelen Rechtecks nach Lage sortiert:
    (links, rechts, unten, oben). Verlaesst sich nicht auf die Reihenfolge,
    in der addTwoPointRectangle die Linien liefert."""
    senkrecht, waagerecht = [], []
    for i in range(rect.count):
        linie = rect.item(i)
        a = linie.startSketchPoint.geometry
        b = linie.endSketchPoint.geometry
        if abs(a.x - b.x) < 1e-7:
            senkrecht.append((a.x, linie))
        else:
            waagerecht.append((a.y, linie))
    senkrecht.sort(key=lambda t: t[0])
    waagerecht.sort(key=lambda t: t[0])
    return (senkrecht[0][1], senkrecht[-1][1],
            waagerecht[0][1], waagerecht[-1][1])


def mass_zu_linie(sk, linie, ausdruck, textpos, fehler):
    """Abstandsmass Ursprung -> Linie, an einen Parameter-Ausdruck gebunden.
    Die Geometrie ist bereits masshaltig gezeichnet; schlaegt ein Mass fehl,
    bleibt das Teil korrekt und nur die Parametrik dieser Kante fehlt."""
    try:
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, linie,
            adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
            textpos)
        d.parameter.expression = ausdruck
    except:
        fehler.append('{}: Mass "{}" nicht gesetzt'.format(sk.name, ausdruck))


def rechteck_bemassen(sk, rect, links, rechts, unten, oben, fehler):
    """Bindet die vier Kanten an Parameter-Ausdruecke (Abstand vom Ursprung)."""
    k_li, k_re, k_un, k_ob = rechteck_kanten(rect)
    mass_zu_linie(sk, k_li, links,  P(-2.0, -3.0), fehler)
    mass_zu_linie(sk, k_re, rechts, P(2.0, -3.0), fehler)
    mass_zu_linie(sk, k_un, unten,  P(-3.0, -2.0), fehler)
    mass_zu_linie(sk, k_ob, oben,   P(-3.0, 2.0), fehler)


def mass_zu_mittelpunkt(sk, kurve, quer_ausdruck, hoch_ausdruck, fehler):
    """Bindet den Mittelpunkt eines Kreises/Bogens per Abstandsmass in X und Y
    an Parameter-Ausdruecke. hoch_ausdruck darf None sein (dann nur X)."""
    mitte = kurve.centerSketchPoint
    paare = [(adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
              quer_ausdruck, P(-0.5, -3.2))]
    if hoch_ausdruck is not None:
        paare.append(
            (adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
             hoch_ausdruck, P(-3.2, -0.5)))
    for orientierung, ausdruck, textpos in paare:
        try:
            d = sk.sketchDimensions.addDistanceDimension(
                sk.originPoint, mitte, orientierung, textpos)
            d.parameter.expression = ausdruck
        except:
            fehler.append('{}: Mass "{}" nicht gesetzt'.format(sk.name, ausdruck))


def langloch(sk, cx, cy, halb_versatz, radius):
    """Langloch mit Achse in X: zwei Linien + zwei Halbkreise als EIN
    geschlossenes Profil. Alle Masse in cm. Die Boegen laufen ueber die
    vorhandenen SketchPoints der Linien, damit das Profil sicher schliesst.
    Liefert (bogen_links, bogen_rechts)."""
    linien = sk.sketchCurves.sketchLines
    boegen = sk.sketchCurves.sketchArcs
    oben = linien.addByTwoPoints(P(cx - halb_versatz, cy + radius),
                                 P(cx + halb_versatz, cy + radius))
    unten = linien.addByTwoPoints(P(cx - halb_versatz, cy - radius),
                                  P(cx + halb_versatz, cy - radius))
    b_re = boegen.addByThreePoints(unten.endSketchPoint,
                                   P(cx + halb_versatz + radius, cy),
                                   oben.endSketchPoint)
    b_li = boegen.addByThreePoints(oben.startSketchPoint,
                                   P(cx - halb_versatz - radius, cy),
                                   unten.startSketchPoint)
    try:
        sk.geometricConstraints.addHorizontal(oben)
        sk.geometricConstraints.addHorizontal(unten)
    except:
        pass
    return b_li, b_re


def groesstes_profil(sk):
    """Flaechengroesstes Profil einer Skizze (nie blind profiles.item(0))."""
    return max((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: p.areaProperties().area)
# -----------------------------------------------------------------------------


# --- Feature-Helfer ----------------------------------------------------------
def extrudieren(feats, prof, hoehe_ausdruck, operation, ziel=None):
    ein = feats.extrudeFeatures.createInput(prof, operation)
    ein.setDistanceExtent(False, vi(hoehe_ausdruck))
    if ziel is not None:
        ein.participantBodies = [ziel]
    return feats.extrudeFeatures.add(ein)


def schnitt_durch_alles(feats, prof, ziel):
    ein = feats.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ein.setOneSideExtent(
        adsk.fusion.ThroughAllExtentDefinition.create(),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ein.participantBodies = [ziel]
    return feats.extrudeFeatures.add(ein)


def muster_2x2(feats, root, feature, abstand_x, abstand_y):
    """Setzt ein Loch/Langloch auf die vier Ecken des Lochbildes."""
    coll = adsk.core.ObjectCollection.create()
    coll.add(feature)
    ein = feats.rectangularPatternFeatures.createInput(
        coll, root.xConstructionAxis,
        adsk.core.ValueInput.createByReal(2), vi(abstand_x),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    ein.directionTwoEntity = root.yConstructionAxis
    ein.quantityTwo = adsk.core.ValueInput.createByReal(2)
    ein.distanceTwo = vi(abstand_y)
    return feats.rectangularPatternFeatures.add(ein)


def ebene_flaechen_bei_z(koerper, z_cm, toleranz=1e-4):
    """Alle ebenen Flaechen eines Koerpers auf Hoehe z (cm), groesste zuerst."""
    treffer = []
    for i in range(koerper.faces.count):
        f = koerper.faces.item(i)
        if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        if abs(f.centroid.z - z_cm) < toleranz:
            treffer.append(f)
    treffer.sort(key=lambda f: f.area, reverse=True)
    return treffer


def alle_kanten_bei_z(koerper, z_cm):
    """Alle Kanten der ebenen Flaechen auf Hoehe z — fuer die Fussfase."""
    kanten = adsk.core.ObjectCollection.create()
    gesehen = set()
    for f in ebene_flaechen_bei_z(koerper, z_cm):
        for i in range(f.edges.count):
            kante = f.edges.item(i)
            if kante.tempId in gesehen:
                continue
            gesehen.add(kante.tempId)
            kanten.add(kante)
    return kanten


def uebergangskanten(koerper, z_cm, grenzen_x, grenzen_y, toleranz=2e-3):
    """Gerade Kanten auf Hoehe z, die auf einer Rippen- oder Pad-Grenze liegen.
    Langloch- und Aussenkanten bleiben bewusst draussen: eine Verrundung dort
    wuerde die Auflageflaeche der Unterlegscheiben anfressen bzw. ist nur
    Kosmetik."""
    kanten = adsk.core.ObjectCollection.create()
    gesehen = set()
    for f in ebene_flaechen_bei_z(koerper, z_cm):
        for i in range(f.edges.count):
            kante = f.edges.item(i)
            if kante.tempId in gesehen:
                continue
            if kante.geometry.curveType != adsk.core.Curve3DTypes.Line3DCurveType:
                continue
            a = kante.startVertex.geometry
            b = kante.endVertex.geometry
            mx = abs((a.x + b.x) / 2.0)
            my = abs((a.y + b.y) / 2.0)
            auf_grenze = (any(abs(mx - g) < toleranz for g in grenzen_x)
                          or any(abs(my - g) < toleranz for g in grenzen_y))
            if auf_grenze:
                gesehen.add(kante.tempId)
                kanten.add(kante)
    return kanten
# -----------------------------------------------------------------------------


def bohrlehre_erzeugen(app, design, root, ebene, punkte_xy_cm, name,
                       loch_mm=3.4, dicke_mm=3.0, rand_mm=8.0):
    """Duenne Lehrenplatte mit Durchgangsloechern an punkte_xy_cm (cm, im
    Koordinatensystem von `ebene`). Wird benannt, bekommt PLA und ist danach
    ausgeblendet (Konvention SKILL.md)."""
    sk = root.sketches.add(ebene)
    sk.name = 'Skizze_Bohrlehre_' + name
    kreise = sk.sketchCurves.sketchCircles
    for x, y in punkte_xy_cm:
        kreise.addByCenterRadius(P(x, y), loch_mm / 20.0)
    xs = [p[0] for p in punkte_xy_cm]
    ys = [p[1] for p in punkte_xy_cm]
    r = rand_mm / 10.0
    rechteck(sk, min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)
    ext = root.features.extrudeFeatures.addSimple(
        groesstes_profil(sk),
        adsk.core.ValueInput.createByReal(dicke_mm / 10.0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    lehre = ext.bodies.item(0)
    lehre.name = 'Bohrlehre_' + name
    material_zuweisen(app, design, lehre, 'PLA')
    lehre.isLightBulbOn = False   # Konvention: standardmaessig ausgeblendet
    return lehre


def hinweise_bauen(fehler):
    """Baut die Hinweiszeilen des Validierungsberichts. Modulebene, damit der
    Block ohne Fusion getestet werden kann (tools/bericht_check.py)."""
    luft_schiene = w('wagen_hoehe') - w('schiene_hoehe')
    laserflaeche = w('pad_hoehe') + w('dicke_platte')
    strahl_wagen = laserflaeche + w('laser_tiefe') / 2
    quer_tol = w('schlitz_verstellweg') + w('schlitz_breite') - 3.0
    hoch_tol = w('schlitz_breite') - 3.0
    hinweise = [
        'BEZUGSEBENE: Ursprung = Mitte Wagen-Lochbild auf der Stirnflaeche',
        '  des Z-Wagens. Modell-Z = nach vorn = Druckrichtung.',
        '',
        'MASSKETTE (ab Wagen-Stirnflaeche):',
        '  Rueckseite Platte ....... {:.1f} mm (Auflagepad)'.format(
            w('pad_hoehe')),
        '  Laser-Anschraubflaeche .. {:.1f} mm'.format(laserflaeche),
        '  Strahlachse ............. {:.1f} mm'.format(strahl_wagen),
        '  Strahlachse ab Schienen-Auflageebene (Z-Platte): {:.1f} mm'.format(
            strahl_wagen + w('wagen_hoehe')),
        '  Luft Teil <-> Schienenoberkante: {:.1f} mm'.format(luft_schiene),
        '  Luft Teil <-> Z-Platte: {:.1f} mm'.format(w('wagen_hoehe')),
        '',
        'PRUEFEN VOR DEM DRUCK (beide Lochbilder Status [?]):',
        '  Bohrlehre_Laser: 4x M3 auf {:.0f} x {:.0f} mm — an den Laser'.format(
            w('laser_loch_hoch'), w('laser_loch_quer')),
        '    halten. hardware.md nennt 40 x 16 aus eigener Messung.',
        '    Langloch deckt ab: quer {:.1f}-{:.1f}, hoch {:.1f}-{:.1f} mm.'.format(
            w('laser_loch_quer') - quer_tol, w('laser_loch_quer') + quer_tol,
            w('laser_loch_hoch') - hoch_tol, w('laser_loch_hoch') + hoch_tol),
        '  Bohrlehre_Wagen: inneres Lochpaar = MGN9C (10 mm), aeusseres =',
        '    MGN9H (16 mm). Gebaut ist: {:.0f} mm.'.format(
            w('wagen_loch_laengs')),
        '    ACHTUNG hardware.md: Messung am Toolhead-Wagen war 26 x 25 mm',
        '    (= MGN15H). Passt nicht zu MGN9 — am Wagen klaeren.',
        '',
        'VERSCHRAUBUNG:',
        '  Wagen: 4x M3x8 Zylinderkopf. {:.1f} mm Kunststoff, ca. 2 mm'.format(
            w('pad_hoehe')),
        '    Einschraubtiefe (MGN9 bietet ~2,5 mm) — nicht laenger nehmen,',
        '    sonst setzt die Schraube auf dem Gewindegrund auf.',
        '  Laser: 4x M3x10 + grosse Scheibe (DIN 9021, Ø9) wegen Langloch.',
        '  Reihenfolge: erst Laser an die Platte, dann Platte an den Wagen',
        '    (die Laser-Schraubenkoepfe liegen im Rippenraum hinter der Platte).',
        '',
        'DRUCK (PETG, Bambu Lab A1): Laser-Anschraubflaeche NACH UNTEN aufs',
        '  Bett, Modell-Z = Aufbaurichtung. Keine Stuetzen; die Platte',
        '  ueberbrueckt 10,5 mm zwischen den Rippen. 4 Wandlinien, >=40% Infill.',
    ]
    if fehler:
        hinweise += ['', 'NICHT GESETZT (Geometrie trotzdem masshaltig):'] \
            + ['  ' + z for z in fehler]
    return hinweise


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # 1) Neues Dokument — nie ins aktive Dokument bauen
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = '{}_r{}'.format(SKRIPT_NAME, REVISION)   # rein kosmetisch
        except RuntimeError:
            pass

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        feats = root.features
        fehler = []

        # 2) User-Parameter aus MASSE — danach alles im Dialog aenderbar
        up = design.userParameters
        for name in sorted(MASSE):
            wert, kommentar = MASSE[name]
            if up.itemByName(name) is None:
                up.add(name, vi('{} mm'.format(wert)), 'mm', kommentar)

        XY = root.xYConstructionPlane

        # Ebene auf Hoehe der Plattenrueckseite (= Vorderseite des Pads)
        pl_ein = root.constructionPlanes.createInput()
        pl_ein.setByOffset(XY, vi('pad_hoehe'))
        ebene_platte = root.constructionPlanes.add(pl_ein)
        ebene_platte.name = 'Ebene_Plattenrueckseite'

        # 3) Auflagepad — liegt auf der Stirnflaeche des Z-Wagens
        sk_pad = root.sketches.add(XY)
        sk_pad.name = 'Skizze_Auflagepad'
        r_pad = rechteck(sk_pad, -c('pad_breite') / 2, -c('pad_laenge') / 2,
                         c('pad_breite') / 2, c('pad_laenge') / 2)
        rechteck_bemassen(sk_pad, r_pad, 'pad_breite / 2', 'pad_breite / 2',
                          'pad_laenge / 2', 'pad_laenge / 2', fehler)
        ext_pad = extrudieren(
            feats, groesstes_profil(sk_pad), 'pad_hoehe',
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        koerper = ext_pad.bodies.item(0)
        koerper.name = 'Toolhead_Grundplatte'

        # 4) Mittelrippe — stuetzt die Platte und haelt die Druckbruecke kurz
        sk_rm = root.sketches.add(XY)
        sk_rm.name = 'Skizze_Mittelrippe'
        r_rm = rechteck(sk_rm, -c('rippe_mitte_breite') / 2,
                        -c('platte_hoehe') / 2,
                        c('rippe_mitte_breite') / 2, c('platte_hoehe') / 2)
        rechteck_bemassen(sk_rm, r_rm, 'rippe_mitte_breite / 2',
                          'rippe_mitte_breite / 2',
                          'platte_hoehe / 2', 'platte_hoehe / 2', fehler)
        extrudieren(feats, groesstes_profil(sk_rm), 'pad_hoehe',
                    adsk.fusion.FeatureOperations.JoinFeatureOperation, koerper)

        # 5) Seitenrippe rechts — ausserhalb des Wagens, danach gespiegelt
        sk_rs = root.sketches.add(XY)
        sk_rs.name = 'Skizze_Seitenrippe'
        r_rs = rechteck(sk_rs, c('rippe_seite_innen'), -c('platte_hoehe') / 2,
                        c('platte_breite') / 2, c('platte_hoehe') / 2)
        rechteck_bemassen(sk_rs, r_rs, 'rippe_seite_innen', 'platte_breite / 2',
                          'platte_hoehe / 2', 'platte_hoehe / 2', fehler)
        ext_rs = extrudieren(feats, groesstes_profil(sk_rs), 'pad_hoehe',
                             adsk.fusion.FeatureOperations.JoinFeatureOperation,
                             koerper)
        sp = adsk.core.ObjectCollection.create()
        sp.add(ext_rs)
        feats.mirrorFeatures.add(
            feats.mirrorFeatures.createInput(sp, root.yZConstructionPlane))

        # 6) Grundplatte — traegt den Laser
        sk_pl = root.sketches.add(ebene_platte)
        sk_pl.name = 'Skizze_Grundplatte'
        r_pl = rechteck(sk_pl, -c('platte_breite') / 2, -c('platte_hoehe') / 2,
                        c('platte_breite') / 2, c('platte_hoehe') / 2)
        rechteck_bemassen(sk_pl, r_pl, 'platte_breite / 2', 'platte_breite / 2',
                          'platte_hoehe / 2', 'platte_hoehe / 2', fehler)
        extrudieren(feats, groesstes_profil(sk_pl), 'dicke_platte',
                    adsk.fusion.FeatureOperations.JoinFeatureOperation, koerper)

        # 7) Wagenverschraubung: M3-Durchgang durch das Pad ...
        sk_bw = root.sketches.add(XY)
        sk_bw.name = 'Skizze_Bohrungen_Wagen'
        k_bw = sk_bw.sketchCurves.sketchCircles.addByCenterRadius(
            P(-c('wagen_loch_quer') / 2, -c('wagen_loch_laengs') / 2),
            c('m3_durchgang') / 2)
        try:
            sk_bw.sketchDimensions.addDiameterDimension(
                k_bw, P(-1.0, -1.5)).parameter.expression = 'm3_durchgang'
        except:
            fehler.append('Skizze_Bohrungen_Wagen: Durchmessermass nicht gesetzt')
        mass_zu_mittelpunkt(sk_bw, k_bw, 'wagen_loch_quer / 2',
                            'wagen_loch_laengs / 2', fehler)
        cut_bw = schnitt_durch_alles(feats, groesstes_profil(sk_bw), koerper)
        muster_2x2(feats, root, cut_bw, 'wagen_loch_quer', 'wagen_loch_laengs')

        # ... und Freibohrung in der Platte: versenkt den Schraubenkopf und gibt
        # den Inbus frei. Der Kopf liegt damit unter der Laser-Anschraubflaeche,
        # der Laser kann plan aufliegen.
        sk_sw = root.sketches.add(ebene_platte)
        sk_sw.name = 'Skizze_Freibohrungen_Wagen'
        k_sw = sk_sw.sketchCurves.sketchCircles.addByCenterRadius(
            P(-c('wagen_loch_quer') / 2, -c('wagen_loch_laengs') / 2),
            c('m3_senkung') / 2)
        try:
            sk_sw.sketchDimensions.addDiameterDimension(
                k_sw, P(-1.0, -1.5)).parameter.expression = 'm3_senkung'
        except:
            fehler.append('Skizze_Freibohrungen_Wagen: Durchmessermass fehlt')
        mass_zu_mittelpunkt(sk_sw, k_sw, 'wagen_loch_quer / 2',
                            'wagen_loch_laengs / 2', fehler)
        cut_sw = extrudieren(feats, groesstes_profil(sk_sw), 'dicke_platte',
                             adsk.fusion.FeatureOperations.CutFeatureOperation,
                             koerper)
        muster_2x2(feats, root, cut_sw, 'wagen_loch_quer', 'wagen_loch_laengs')

        # 8) Laser-Langloecher — quer geschlitzt, weil das Bohrbild noch [?] ist
        sk_sl = root.sketches.add(XY)
        sk_sl.name = 'Skizze_Langloecher_Laser'
        b_li, b_re = langloch(
            sk_sl, -c('laser_loch_quer') / 2, -c('laser_loch_hoch') / 2,
            c('schlitz_verstellweg') / 2, c('schlitz_breite') / 2)
        # Hoehe nur einmal bemassen — die waagerechten Linien halten den
        # zweiten Bogen bereits auf gleicher Hoehe.
        mass_zu_mittelpunkt(sk_sl, b_li,
                            'laser_loch_quer / 2 + schlitz_verstellweg / 2',
                            'laser_loch_hoch / 2', fehler)
        mass_zu_mittelpunkt(sk_sl, b_re,
                            'laser_loch_quer / 2 - schlitz_verstellweg / 2',
                            None, fehler)
        for bogen in (b_li, b_re):
            try:
                sk_sl.sketchDimensions.addRadialDimension(
                    bogen, P(-1.0, -2.5)).parameter.expression = \
                    'schlitz_breite / 2'
            except:
                fehler.append('Skizze_Langloecher_Laser: Radiusmass fehlt')
        cut_sl = schnitt_durch_alles(feats, groesstes_profil(sk_sl), koerper)
        muster_2x2(feats, root, cut_sl, 'laser_loch_quer', 'laser_loch_hoch')

        # 9) Fase an der Auflageflaeche — sonst hebt der Elefantenfuss das Teil
        #    vom Wagen ab, und genau das war der Fehler beim ersten Versuch.
        try:
            kanten = alle_kanten_bei_z(koerper, 0.0)
            if kanten.count:
                ch_ein = feats.chamferFeatures.createInput2()
                ch_ein.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                    kanten, vi('fase_fuss'), True)
                feats.chamferFeatures.add(ch_ein)
            else:
                fehler.append('Fussfase: keine Flaeche bei z=0 gefunden')
        except:
            fehler.append('Fussfase uebersprungen — Auflageflaeche pruefen!')

        # 10) Verrundung Rippe/Pad -> Platte (Kerbwirkung; nicht tragend)
        try:
            kanten = uebergangskanten(
                koerper, c('pad_hoehe'),
                grenzen_x=(c('rippe_mitte_breite') / 2, c('rippe_seite_innen')),
                grenzen_y=(c('pad_laenge') / 2,))
            if kanten.count:
                fi_ein = feats.filletFeatures.createInput()
                fi_ein.edgeSetInputs.addConstantRadiusEdgeSet(
                    kanten, vi('radius_uebergang'), True)
                feats.filletFeatures.add(fi_ein)
            else:
                fehler.append('Uebergangsverrundung: keine Kanten gefunden')
        except:
            fehler.append('Uebergangsverrundung uebersprungen (nicht tragend)')

        # 11) Material — PETG: der Laser gibt Abwaerme ab
        material_zuweisen(app, design, koerper, 'PETG')

        # 12) Bohrlehren: beide Lochbilder sind noch [?] — vor dem Druck der
        #     Platte am echten Teil gegenpruefen. Ausgeblendet.
        lehren_ein = root.constructionPlanes.createInput()
        lehren_ein.setByOffset(XY, vi('-20 mm'))
        ebene_lehren = root.constructionPlanes.add(lehren_ein)
        ebene_lehren.name = 'Ebene_Bohrlehren'

        lq = c('laser_loch_quer') / 2
        lh = c('laser_loch_hoch') / 2
        bohrlehre_erzeugen(
            app, design, root, ebene_lehren,
            [(-4.5 - lq, -lh), (-4.5 + lq, -lh),
             (-4.5 - lq, lh), (-4.5 + lq, lh)],
            'Laser', loch_mm=w('m3_durchgang'), dicke_mm=w('lehre_dicke'))

        wq = c('wagen_loch_quer') / 2
        bohrlehre_erzeugen(
            app, design, root, ebene_lehren,
            [(4.5 - wq, -0.5), (4.5 + wq, -0.5), (4.5 - wq, 0.5), (4.5 + wq, 0.5),
             (4.5 - wq, -0.8), (4.5 + wq, -0.8), (4.5 - wq, 0.8), (4.5 + wq, 0.8)],
            'Wagen', loch_mm=w('m3_durchgang'), dicke_mm=w('lehre_dicke'))

        # 13) Ergebnis einpassen und Bericht ausgeben
        app.activeViewport.fit()

        hinweise = hinweise_bauen(fehler)
        validierungs_bericht(app, design, ui, hinweise=hinweise)

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
