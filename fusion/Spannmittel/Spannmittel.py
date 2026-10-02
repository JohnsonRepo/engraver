# Spannmittel.py — Werkstueck auf der Opferplatte festhalten
#
# Ein Laser drueckt nicht auf das Werkstueck. Gespannt wird nur, damit es an
# einer bekannten Stelle liegt, nicht verrutscht und duennes, verzogenes
# Material flach bleibt. Druckteile (PETG):
#   Anschlagwinkel   fest auf der Opferplatte hinten links, in der Ecke der
#                    Referenzfahrt. Seine Innenecke ist der Nullpunkt fuer
#                    das Werkstueck. 3 mm hoch, 3 Spanplattenschrauben.
#   Exzenter         Scheibe mit aussermittiger Schraube und Hebel, 3 mm
#                    hoch. Neben das Werkstueck geschraubt und vom
#                    Werkstueck weg gedreht, schiebt er es in die Ecke;
#                    selbsthemmend.
#   Niederhalter     Spanneisen je Materialstaerke (2 bis 6 mm): Lippe auf
#                    dem Werkstueckrand, Ferse auf der Platte, die Schraube
#                    dazwischen zieht beides herunter. Haelt duenne,
#                    verzogene Platten flach.
#   Referenz_nicht_drucken  Opferplatte und ein Beispielwerkstueck.
#
# Hoehe: Liegt der Fokus auf dem Werkstueck, faehrt der Toolhead mindestens
# toolhead_frei (3,7 mm) darueber. So tief kommt er mit Z ganz unten an die
# Platte, und weniger waere es nur, wenn der Laser nicht mehr auf die leere
# Platte fokussieren koennte. Anschlag und Exzenter sind deshalb 3 mm hoch,
# der Niederhalter ragt 2,5 mm ueber das Werkstueck: Der Toolhead faehrt
# ueberall darueber, auch bei Leerfahrten.
#
# Koordinaten = Maschinenkoordinaten wie Opferplatte.py: X nach rechts, Y
# nach vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im
# Fusion-Modell sind Y und Z getauscht (Modell-Z = Maschine Y).
# tools/spannmittel_check.py vergleicht Platte und Arbeitsfeld mit
# Opferplatte.py und den Freiraum mit ToolheadZ.py.
#
# Konventionen: siehe fusion-python/SKILL.md. Eine Bohrlehre gibt es nicht:
# Die Spanplattenschrauben gehen ohne Vorbohren in die Opferplatte.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'Spannmittel'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Opferplatte und Arbeitsfeld (wie Opferplatte.py) [v] ---------------
    'platte_x0':         (-295.0, 'Opferplatte: linke Kante (am Anschlag)'),
    'platte_x1':          (320.0, 'Opferplatte: rechte Kante'),
    'platte_y0':        (-176.65, 'Opferplatte: hintere Kante'),
    'platte_y1':         (172.35, 'Opferplatte: vordere Kante'),
    'platte_z0':         (-154.3, 'Opferplatte: Unterseite = Tisch'),
    'platte_z1':         (-129.0, 'Opferplatte: Oberflaeche'),
    'feld_x0':          (-203.85, 'Arbeitsfeld: links'),
    'feld_x1':           (187.35, 'Arbeitsfeld: rechts'),
    'feld_y0':           (-168.8, 'Arbeitsfeld: hinten'),
    'feld_y1':            (164.5, 'Arbeitsfeld: vorn'),
    'toolhead_frei':        (3.7, 'Toolhead mit Z ganz unten ueber der Platte'),

    # --- Anschlagwinkel: fest hinten links ----------------------------------
    # Hinten hat die Platte nur 7,85 mm Rand hinter dem Arbeitsfeld. Mit der
    # Innenecke 4 mm im Feld bleibt hinter einem Werkstueck an diesem
    # Schenkel Platz fuer einen Niederhalter.
    'aw_rand':              (4.0, 'Anschlag: Innenecke so weit im Arbeitsfeld'),
    'aw_h':                 (3.0, 'Anschlag: Hoehe'),
    'aw_l':                (50.0, 'Anschlag: Schenkel ab der Innenecke'),
    'aw_b_hinten':         (10.0, 'Anschlag: Breite des hinteren Schenkels'),
    'aw_b_links':          (10.0, 'Anschlag: Breite des linken Schenkels'),
    'aw_schraube_ende':     (7.0, 'Anschlag: Schraube so weit vor dem Schenkelende'),

    # --- Exzenter ------------------------------------------------------------
    'ex_r':                (20.0, 'Exzenter: Radius der Scheibe'),
    'ex_e':                 (4.0, 'Exzenter: Schraube so weit aussermittig'),
    'ex_h':                 (3.0, 'Exzenter: Hoehe'),
    'ex_hebel_l':          (14.0, 'Exzenter: Hebel ragt so weit ueber die Scheibe'),
    'ex_hebel_b':           (8.0, 'Exzenter: Breite des Hebels'),

    # --- Niederhalter (Spanneisen) -------------------------------------------
    # u laeuft von der Werkstueckkante nach aussen: Lippe -nh_lippe..0 auf
    # dem Werkstueck, Schraube bei nh_schraube, Ferse bis nh_ende.
    'nh_b':                (14.0, 'Niederhalter: Breite laengs der Kante'),
    'nh_d':                 (2.5, 'Niederhalter: Dicke des Stegs'),
    'nh_lippe':             (5.0, 'Niederhalter: liegt so weit auf dem Werkstueck'),
    'nh_schraube':          (3.5, 'Niederhalter: Schraube so weit neben der Kante'),
    'nh_ferse':             (3.0, 'Niederhalter: Laenge der Ferse'),
    'nh_ende':              (9.5, 'Niederhalter: reicht so weit neben die Kante'),
    'nh_t':                 (3.0, 'Beispiel: Materialstaerke'),

    # --- Beispielwerkstueck --------------------------------------------------
    'wst_l':              (200.0, 'Beispiel: Werkstueck in X'),
    'wst_b':              (150.0, 'Beispiel: Werkstueck in Y'),

    # --- Normteile und Regeln ------------------------------------------------
    # Spanplattenschraube 3,0 x 20 Senkkopf 90 Grad (TX10)
    'sch_l':               (20.0, 'Spanplattenschraube 3,0: Laenge'),
    'sch_loch':             (3.4, 'Spanplattenschraube 3,0: Durchgang'),
    'sch_kopf_d':           (6.0, 'Senkkopf: Durchmesser'),
    'senk_d':               (6.4, 'Senkung 90 Grad: Durchmesser oben'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
}

# Niederhalter je Materialstaerke (mm): je einer wird gebaut, der fuer nh_t
# dazu viermal am Beispielwerkstueck. Eine Liste, kein User-Parameter.
NH_STAERKEN = (2.0, 3.0, 4.0, 5.0, 6.0)


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def nh_lage(name, achse, kante, aussen, s, t, z_basis):
    """Lage eines Niederhalters an einer Kante. achse: 'y' fuer eine Kante
    bei konstantem Y (vorn, hinten), 'x' bei konstantem X (links, rechts);
    aussen: +1 oder -1, Richtung von der Kante nach aussen; s: Mitte laengs
    der Kante; t: Materialstaerke; z_basis: worauf die Ferse steht."""
    hb = w('nh_b') / 2.0

    def quer(u0, u1):                       # u-Bereich -> Koordinate
        a, b = kante + aussen * u0, kante + aussen * u1
        return (min(a, b), max(a, b))

    def zu_xy(ub, wb):
        return (ub, wb) if achse == 'x' else (wb, ub)

    laengs = (s - hb, s + hb)
    zs = (z_basis + t, z_basis + t + w('nh_d'))
    steg = zu_xy(quer(-w('nh_lippe'), w('nh_ende')), laengs) + (zs,)
    ferse = zu_xy(quer(w('nh_ende') - w('nh_ferse'), w('nh_ende')),
                  laengs) + ((z_basis, z_basis + t),)
    u = kante + aussen * w('nh_schraube')
    schraube = (u, s) if achse == 'x' else (s, u)
    return {'name': name, 't': t, 'achse': achse, 'kante': kante,
            'aussen': aussen, 's': s, 'z_basis': z_basis, 'steg': steg,
            'ferse': ferse, 'schraube': schraube,
            'bbox': (steg[0], steg[1], (z_basis, zs[1]))}


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/spannmittel_check.py)."""
    L = {}
    z0 = w('platte_z1')
    L['z0'] = z0
    L['platte_x'] = (w('platte_x0'), w('platte_x1'))
    L['platte_y'] = (w('platte_y0'), w('platte_y1'))
    L['platte_z'] = (w('platte_z0'), z0)
    L['feld_x'] = (w('feld_x0'), w('feld_x1'))
    L['feld_y'] = (w('feld_y0'), w('feld_y1'))

    # ---- Anschlagwinkel: Innenecke aw_rand im Feld; der hintere Schenkel
    #      laeuft nach rechts, der linke nach vorn
    xi, yi = w('feld_x0') + w('aw_rand'), w('feld_y0') + w('aw_rand')
    bh, bl = w('aw_b_hinten'), w('aw_b_links')
    L['aw_ecke'] = (xi, yi)
    L['aw_hinten'] = ((xi - bl, xi + w('aw_l')), (yi - bh, yi))
    L['aw_links'] = ((xi - bl, xi), (yi - bh, yi + w('aw_l')))
    L['aw_z'] = (z0, z0 + w('aw_h'))
    ende = w('aw_l') - w('aw_schraube_ende')
    L['aw_schrauben'] = [(xi - bl / 2.0, yi - bh / 2.0),
                         (xi + ende, yi - bh / 2.0),
                         (xi - bl / 2.0, yi + ende)]

    # ---- Beispielwerkstueck in der Ecke
    L['wst_x'] = (xi, xi + w('wst_l'))
    L['wst_y'] = (yi, yi + w('wst_b'))
    L['wst_z'] = (z0, z0 + w('nh_t'))
    wx, wy = L['wst_x'], L['wst_y']

    # ---- Exzenter, gespannt: Der groesste Radius liegt am Werkstueck.
    #      n zeigt vom Exzenter zum Werkstueck; die Schraube sitzt ex_e
    #      hinter der Scheibenmitte, der Hebel auf der Seite des kleinsten
    #      Radius zeigt vom Werkstueck weg.
    R, e = w('ex_r'), w('ex_e')
    hb = w('ex_hebel_b') / 2.0
    L['ex'] = []
    for name, kontakt, n in (
            ('Exzenter_rechts', (wx[1], (wy[0] + wy[1]) / 2.0), (-1.0, 0.0)),
            ('Exzenter_vorn', ((wx[0] + wx[1]) / 2.0, wy[1]), (0.0, -1.0))):
        c = (kontakt[0] - n[0] * R, kontakt[1] - n[1] * R)
        p = (c[0] - n[0] * e, c[1] - n[1] * e)
        q = (-n[1], n[0])
        hebel = [(c[0] - n[0] * a + q[0] * b, c[1] - n[1] * a + q[1] * b)
                 for a, b in ((R - 2.0, -hb), (R + w('ex_hebel_l'), -hb),
                              (R + w('ex_hebel_l'), hb), (R - 2.0, hb))]
        L['ex'].append({'name': name, 'n': n, 'kontakt': kontakt,
                        'mitte': c, 'achse': p, 'hebel': hebel})
    L['ex_z'] = (z0, z0 + w('ex_h'))
    # Abstand Schraube - Werkstueckkante: vom Hebel quer zur Kante (R) bis
    # zum groessten Radius (R + e); groesster Steigungswinkel asin(e/R)
    L['ex_fenster'] = (R, R + e)
    L['ex_winkel'] = math.degrees(math.asin(e / R))

    # ---- Niederhalter: der fuer nh_t an allen vier Kanten des Beispiels,
    #      vorn und rechts frei, hinten und links neben den Schenkeln; die
    #      uebrigen Staerken als Satz rechts neben der Platte auf dem Tisch
    t = w('nh_t')
    L['nh'] = [nh_lage('Niederhalter_{:.0f}mm_{}'.format(t, wo), achse,
                       kante, aussen, s, t, z0)
               for wo, achse, kante, aussen, s in (
                   ('vorn', 'y', wy[1], 1.0, wx[0] + 40.0),
                   ('rechts', 'x', wx[1], 1.0, wy[0] + 25.0),
                   ('hinten', 'y', wy[0], -1.0, xi + w('aw_l') + 40.0),
                   ('links', 'x', wx[0], -1.0, yi + w('aw_l') + 40.0))]
    andere = [s_ for s_ in NH_STAERKEN if abs(s_ - t) > 1e-9]
    L['nh_satz'] = [nh_lage('Niederhalter_{:.0f}mm'.format(s_), 'y',
                            L['platte_y'][0] + 50.0, 1.0,
                            L['platte_x'][1] + 50.0 + 25.0 * i, s_,
                            w('platte_z0'))
                    for i, s_ in enumerate(andere)]

    # ---- Schrauben: Kopf in der Senkung 90 Grad versenkt
    L['kopf_tiefer'] = (w('senk_d') - w('sch_kopf_d')) / 2.0
    L['senk_tief'] = (w('senk_d') - w('sch_loch')) / 2.0
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
              'Spanplatte': 0.65,              # die Opferplatte
              'Sperrholz': 0.6}                # das Beispielwerkstueck


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


def senkung(comp, name, mitte, d_loch, d_senk, z_oben, ziel):
    """Kegelsenkung 90 Grad fuer einen Senkkopf: oben (z_oben) Durchmesser
    d_senk, nach unten bis zum Loch d_loch. Drehschnitt um die senkrechte
    Lochachse in einer Ebene Y = konstant — wie die anderen Schnitte
    unabhaengig davon, wohin die Normale der Ebene zeigt. Das Profil reicht
    1 mm ueber die Oberseite, damit der Schnitt sauber austritt."""
    x, y = mitte
    rs, rl = d_senk / 2.0, d_loch / 2.0
    tief = rs - rl                        # 90 Grad: Tiefe = Radiusdifferenz
    sk = skizze(comp, _ebene(comp, 'y', y, 'E_{}_Y{:.1f}'.format(
        comp.name, y)), 'Sk_' + name)
    pkt = [(x, z_oben + 1.0), (x + rs + 1.0, z_oben + 1.0),
           (x + rl, z_oben - tief), (x, z_oben - tief)]
    linien = sk.sketchCurves.sketchLines
    a = linien.addByTwoPoints(punkt(sk, *pkt[0]), punkt(sk, *pkt[1]))
    b = linien.addByTwoPoints(a.endSketchPoint, punkt(sk, *pkt[2]))
    c = linien.addByTwoPoints(b.endSketchPoint, punkt(sk, *pkt[3]))
    achse = linien.addByTwoPoints(c.endSketchPoint, a.startSketchPoint)
    ein = comp.features.revolveFeatures.createInput(
        groesstes_profil(sk), achse, _op('weg'))
    ein.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    ein.participantBodies = [ziel]
    return comp.features.revolveFeatures.add(ein)


def bau_anschlag(app, design, comp, L, fehler):
    """Anschlagwinkel hinten links: zwei Schenkel, 3 Senkschrauben.

    Drucklage: Unterseite aufs Bett, Senkungen oben — keine Stuetzen."""
    (hx, hy), (lx, ly) = L['aw_hinten'], L['aw_links']
    z0, z1 = L['aw_z']
    k = quader(comp, 'Schenkel_hinten', hx, hy, L['aw_z'],
               'neu').bodies.item(0)
    k.name = 'Anschlagwinkel'
    quader(comp, 'Schenkel_links', lx, ly, L['aw_z'], 'dazu', k)
    bohrung(comp, 'Loecher_Anschlag', 'z', L['aw_schrauben'], w('sch_loch'),
            z0 - 1.0, z1 + 1.0, k)
    for i, p in enumerate(L['aw_schrauben']):
        senkung(comp, 'Senkung_Anschlag_{}'.format(i + 1), p, w('sch_loch'),
                w('senk_d'), z1, k)
    fussfase(comp, k, 'y', z0, w('fase_fuss'), fehler, 'Anschlagwinkel')
    bbox_pruefen(k, 'Anschlagwinkel', ((lx[0], hx[1]), (hy[0], ly[1]),
                                       L['aw_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_exzenter(app, design, comp, ex, L, fehler):
    """Exzenter: Scheibe, Schraube aussermittig, Hebel auf der Seite des
    kleinsten Radius. Gebaut gespannt (groesster Radius am Werkstueck).

    Drucklage: Unterseite aufs Bett, Senkung oben — keine Stuetzen."""
    c, p, name = ex['mitte'], ex['achse'], ex['name']
    z0, z1 = L['ex_z']
    k = zylinder(comp, 'Scheibe_' + name, 'z', c, 2.0 * w('ex_r'), z0, z1,
                 'neu').bodies.item(0)
    k.name = name
    prisma_vieleck(comp, 'Hebel_' + name, 'z', ex['hebel'], z0, z1, 'dazu',
                   k)
    bohrung(comp, 'Loch_' + name, 'z', [p], w('sch_loch'), z0 - 1.0,
            z1 + 1.0, k)
    senkung(comp, 'Senkung_' + name, p, w('sch_loch'), w('senk_d'), z1, k)
    fussfase(comp, k, 'y', z0, w('fase_fuss'), fehler, name.replace('_', ' '))
    R = w('ex_r')
    xs = [x for x, _ in ex['hebel']] + [c[0] - R, c[0] + R]
    ys = [y for _, y in ex['hebel']] + [c[1] - R, c[1] + R]
    bbox_pruefen(k, name.replace('_', ' '), ((min(xs), max(xs)),
                                            (min(ys), max(ys)), L['ex_z']),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_niederhalter(app, design, comp, nh, fehler):
    """Niederhalter (Spanneisen): Steg mit Lippe auf dem Werkstueck, Ferse
    auf der Platte, Senkschraube dazwischen.

    Drucklage: Oberseite aufs Bett (die Ferse steht nach oben), die
    Senkung oeffnet sich zum Bett — keine Stuetzen."""
    name = nh['name']
    k = quader(comp, 'Steg_' + name, *nh['steg'], 'neu').bodies.item(0)
    k.name = name
    quader(comp, 'Ferse_' + name, *nh['ferse'], 'dazu', k)
    zs = nh['steg'][2]
    bohrung(comp, 'Loch_' + name, 'z', [nh['schraube']], w('sch_loch'),
            zs[0] - 1.0, zs[1] + 1.0, k)
    senkung(comp, 'Senkung_' + name, nh['schraube'], w('sch_loch'),
            w('senk_d'), zs[1], k)
    # Die Oberseite liegt beim Druck auf dem Bett
    fussfase(comp, k, 'y', zs[1], w('fase_fuss'), fehler,
             name.replace('_', ' '))
    bbox_pruefen(k, name.replace('_', ' '), nh['bbox'], fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_referenz(app, design, comp, L, fehler):
    """Opferplatte und Beispielwerkstueck — nur zur Ansicht, NICHT drucken."""
    k = quader(comp, 'Platte', L['platte_x'], L['platte_y'], L['platte_z'],
               'neu').bodies.item(0)
    k.name = 'Opferplatte'
    material_zuweisen(app, design, k, 'Spanplatte', fehler)
    k = quader(comp, 'Werkstueck', L['wst_x'], L['wst_y'], L['wst_z'],
               'neu').bodies.item(0)
    k.name = 'Beispielwerkstueck'
    bbox_pruefen(k, 'Beispielwerkstueck', (L['wst_x'], L['wst_y'],
                                           L['wst_z']), fehler)
    material_zuweisen(app, design, k, 'Sperrholz', fehler)


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/spannmittel_check.py)."""
    xi, yi = L['aw_ecke']
    sch = 'Spanplattenschraube 3,0 x {:.0f} Senkkopf'.format(w('sch_l'))
    h = [
        'WOZU: Ein Laser drueckt nicht auf das Werkstueck. Gespannt wird,',
        '  damit es an einer bekannten Stelle liegt, nicht verrutscht und',
        '  duennes, verzogenes Material flach bleibt.',
        '',
        'HOEHE: Liegt der Fokus auf dem Werkstueck, faehrt der Toolhead',
        '  mindestens {:.1f} mm darueber. Anschlag und Exzenter sind {:.0f} mm'
        .format(w('toolhead_frei'), w('aw_h')),
        '  hoch, der Niederhalter ragt {:.1f} mm ueber das Werkstueck: Der'
        .format(w('nh_d')),
        '  Toolhead faehrt ueberall darueber, auch bei Leerfahrten.',
        '',
        'ANSCHLAGWINKEL (fest): hinten links auf der Platte, Innenecke',
        '  X {:+.2f}, Y {:+.2f} ({:.0f} mm im Arbeitsfeld). Schenkel {:.0f} mm,'
        .format(xi, yi, w('aw_rand'), w('aw_l')),
        '  3 x {}.'.format(sch),
        '  Die Innenecke ist der Nullpunkt: Laser mit 1 % daraufstellen,',
        '  G10 L20 P1 X0 Y0. Vorher die Platte nach links und hinten',
        '  schieben, dann liegt der Nullpunkt jedes Mal gleich.',
        '',
        'EXZENTER (2 x): Scheibe d {:.0f}, Schraube {:.0f} mm aussermittig,'
        .format(2.0 * w('ex_r'), w('ex_e')),
        '  Hebel. Mit dem Hebel quer zur Kante an das Werkstueck legen,',
        '  festschrauben, den Hebel vom Werkstueck weg drehen: Er schiebt',
        '  es bis {:.0f} mm weit in die Ecke. Selbsthemmend ({:.1f} Grad).'
        .format(w('ex_e'), L['ex_winkel']),
        '',
        'NIEDERHALTER je Staerke {} mm: Lippe {:.0f} mm auf dem Rand,'
        .format('/'.join('{:.0f}'.format(s) for s in NH_STAERKEN),
                w('nh_lippe')),
        '  Ferse auf der Platte, die Schraube dazwischen zieht beides',
        '  herunter. Handfest anziehen. Wo einer sitzt, {:.0f} mm Abstand'
        .format(w('nh_lippe') + 1.0),
        '  zwischen Gravur und Werkstueckrand lassen.',
        '',
        'DRUCK (PETG, Bambu Lab A1): Anschlag und Exzenter mit der',
        '  Unterseite aufs Bett, Niederhalter mit der Oberseite. Keine',
        '  Stuetzen.',
        '',
        'SCHRAUBEN: {} (TX10), ohne Vorbohren'.format(sch),
        '  in die Spanplatte. Der Kopf liegt {:.1f} mm unter der Oberseite.'
        .format(L['kopf_tiefer']),
        '',
        'KEINE BOHRLEHRE: gebohrt wird nichts.',
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
        o.component.name = 'Anschlagwinkel'
        bau_anschlag(app, design, o.component, L, fehler)
        o.isGrounded = True

        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Exzenter'
        for ex in L['ex']:
            bau_exzenter(app, design, o.component, ex, L, fehler)
        o.isGrounded = True

        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Niederhalter'
        for nh in L['nh'] + L['nh_satz']:
            bau_niederhalter(app, design, o.component, nh, fehler)
        o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        oo = ref.component.occurrences.addNewComponent(einheit)
        oo.component.name = 'Ref_Platte'
        try:
            bau_referenz(app, design, oo.component, L, fehler)
        except Exception:
            fehler.append('Referenz nicht gebaut: {}'.format(
                traceback.format_exc().strip().splitlines()[-1]))
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
