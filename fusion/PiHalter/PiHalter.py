# PiHalter.py — Halter fuer den Raspberry Pi Zero 2 W und seinen 5-V-Wandler
# an der Rueckseite des hinteren 2060
#
# Ein Druckteil, dazu Referenzteile nur zur Ansicht:
#   Pi-Halter   Platte, 5 mm dick, rechts neben der Montageplatte des
#               Elektronik-Kastens an der Rueckseite des hinteren 2060, mit
#               2 x M5x12 in Hammermuttern der oberen Nut (wie die
#               Montageplatte). Oben steht sie ueber die Oberkante des 2060
#               hinaus: Dort sitzen rechts der Pi auf vier Stehbolzen, die
#               Bauteile nach hinten, die Buchsen nach unten, und links der
#               Abwaertswandler 24 -> 5 V unter zwei senkrechten
#               Kabelbindern. Vor der
#               Antenne des Pi liegt so kein Aluminium. Die Kabel in der
#               mittleren Nut des 2060 (W2, W10, W14, W18) laufen unter der
#               Platte durch.
#   Referenz_nicht_drucken  Stueck hinteres 2060, Pi (Platine und Bauteile
#               als Huelle), die beiden Micro-USB-Stecker, der groesste
#               Wandler, der passt, Schrauben und Hammermuttern.
#
# Drucklage: die Seite am 2060 aufs Bett, die Stehbolzen nach oben; keine
# Stuetzen.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: X nach rechts, Y nach
# vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im Fusion-Modell
# sind Y und Z getauscht (Modell-Z = Maschine Y). tools/pihalter_check.py
# vergleicht die Rahmenmasse mit Portal.py und Elektronik.py und prueft den
# Halter gegen Kasten, Kabel und alles, was faehrt.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'PiHalter'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen (wie Portal.py und Elektronik.py) [v] -----------------------
    'quer_y1':           (-250.0, 'Rahmen: Rueckseite des hinteren 2060'),
    'rahmen_b':            (20.0, '2060: Dicke (20er Raster)'),
    'rahmen_z0':          (-69.0, 'Rahmen: Oberkante 2060 = Unterkante der 2040'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
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

    # --- Platte ---------------------------------------------------------------
    # Rev. 1: erster Stand. Links 5,7 mm neben der Montageplatte des Kastens
    # (endet bei X -23,66), damit das USB-Kabel zum Uno kurz bleibt.
    'ph_x0':              (-18.0, 'Platte: linke Kante (X)'),
    'platte_dicke':         (5.0, 'Platte: Dicke (liegt an der Rueckseite des 2060)'),
    'unter_nut':            (6.0, 'Platte: reicht so weit unter die Mitte der oberen Nut'),
    'rand_oben':            (3.0, 'Platte: reicht so weit ueber Pi und oberen Schlitz'),
    'm5_rand':             (12.0, 'M5: so weit von den Enden der Platte'),

    # --- Raspberry Pi Zero 2 W [w] (Massblatt der Zero-Reihe) ----------------
    'pi_l':                (65.0, 'Pi Zero 2 W: Platine, lange Seite (liegt laengs X)'),
    'pi_b':                (30.0, 'Pi Zero 2 W: Platine, kurze Seite (Z)'),
    'pi_pcb':               (1.4, 'Pi: Platinendicke [?]'),
    'pi_bauteile':          (4.0, 'Pi: hoechstes Bauteil ueber der Platine [?]'),
    'pi_loch_rand':         (3.5, 'Pi: Bohrungen so weit von den Kanten (58 x 23)'),
    'pi_loch_d':           (2.75, 'Pi: Bohrung fuer M2.5'),
    # Buchsen an der langen Kante, Mitte ab der kurzen Kante mit der SD-Karte
    'pi_hdmi':             (12.4, 'Pi: Mini-HDMI, Mitte ab der Kante mit der SD-Karte'),
    'pi_usb':              (41.4, 'Pi: Micro-USB "USB" (Daten), Mitte ab der SD-Kante'),
    'pi_pwr':              (54.0, 'Pi: Micro-USB "PWR IN", Mitte ab der SD-Kante'),
    'pi_rand':              (6.0, 'Pi: so weit von der rechten Kante der Platte'),
    # Der USB-A-Stecker steckt rechts im Wandler und zeigt zum Pi; mit
    # Knickschutz ist er 35 bis 40 mm lang, erst dahinter biegt das Kabel
    # nach unten ab [w]
    'usb_a_platz':         (40.0, 'Wandler bis Pi: Platz fuer den USB-A-Stecker'),
    'usb_a_l':             (38.0, 'USB-A-Stecker mit Knickschutz: Laenge [w]'),
    'usb_a_b':             (16.0, 'USB-A-Stecker: Breite (Z) [w]'),
    'usb_a_t':              (9.0, 'USB-A-Stecker: Dicke (Y) [w]'),
    'usb_a_mitte':          (6.0, 'USB-A-Buchse: Mitte so weit hinter der Platte [?]'),
    # 5 mm: die Stecker unter dem Pi bleiben so ueber den Kabeln in der
    # mittleren Nut des 2060
    'pi_ueber':             (5.0, 'Pi: Unterkante so weit ueber der Oberkante des 2060'),
    'steg_h':               (5.0, 'Stehbolzen: Hoehe (Platine frei von der Platte)'),
    'steg_d':               (6.0, 'Stehbolzen: Durchmesser'),
    'm25_kern':             (2.2, 'Stehbolzen: Kernloch fuer M2.5 selbstschneidend'),
    'kernloch_platte':      (2.0, 'Kernloch: reicht so weit in die Platte'),
    'm25_l':                (6.0, 'Schraube M2.5x6 (Pi -> Stehbolzen)'),
    'm25_kopf_d':           (4.5, 'M2.5 Zylinderkopf: Durchmesser'),
    'm25_kopf_h':           (2.5, 'M2.5 Zylinderkopf: Hoehe'),
    # Micro-USB-Stecker mit Knickschutz [w]: haengen unter dem Pi
    'stecker_b':           (11.0, 'Micro-USB-Stecker: Breite'),
    'stecker_t':            (7.5, 'Micro-USB-Stecker: Dicke'),
    'stecker_l':           (24.0, 'Micro-USB-Stecker: Laenge ab der Platinenkante'),
    'stecker_mitte':        (1.4, 'Micro-USB: Steckermitte ueber der Platine'),

    # --- Abwaertswandler 24 -> 5 V [?] ----------------------------------------
    # Nicht festgelegt, welcher: der Platz nimmt einen bis zu dieser Groesse
    # auf. Links der Eingang, rechts die USB-A-Buchse. Zwei Kabelbinder
    # laufen senkrecht ueber seine Rueckseite, die Enden mit Eingang und
    # Buchse bleiben frei; die Schlitze sitzen ueber und unter ihm.
    'wandler_l':           (60.0, '5-V-Wandler: hoechstens so lang (X)'),
    'wandler_b':           (30.0, '5-V-Wandler: hoechstens so hoch (Z)'),
    'wandler_h':           (20.0, '5-V-Wandler: hoechstens so dick (Y)'),
    'wandler_rand':         (4.0, 'Wandler: so weit von der linken Plattenkante'),
    'binder_b':             (5.0, 'Kabelbinder-Schlitz: Laenge (X)'),
    'binder_t':             (2.2, 'Kabelbinder-Schlitz: Breite (Z)'),
    'binder_luft':          (2.0, 'Schlitze: so weit ueber und unter dem Wandler'),
    'binder_ueber':         (3.0, 'unterer Schlitz: so weit ueber dem 2060'),
    'binder_abstand':      (20.0, 'die beiden Kabelbinder: Abstand (X)'),

    # --- Normteile und Regeln ------------------------------------------------
    'm5_l':                (12.0, 'Schraube M5x12 (wie die Montageplatte des Kastens)'),
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'hammer_l':            (10.0, 'Hammermutter M5 Nut 6: laengs der Nut [w]'),
    'inbus_frei_d':         (6.0, 'Werkzeugkorridor fuer den Inbus'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/pihalter_check.py)."""
    L = {}
    L['tisch_z'] = w('rahmen_z0') - w('quer_h')
    L['quer_y'] = (w('quer_y1'), w('quer_y1') + w('rahmen_b'))
    L['quer_nut_z'] = [L['tisch_z'] + w('quer_nut_1') + i * w('quer_nut_teilung')
                       for i in range(3)]
    zn = L['quer_nut_z'][2]                      # obere Nut der Rueckseite
    L['nut_z'] = zn

    # Platte an der Rueckseite des 2060; ihre Breite folgt aus Wandler,
    # Stecker und Pi
    y1 = w('quer_y1')
    y0 = y1 - w('platte_dicke')
    x0 = w('ph_x0')
    L['platte_y'] = (y0, y1)

    # Wandler links; die Kabelbinder laufen senkrecht ueber ihn, der untere
    # Schlitz knapp ueber der Oberkante des 2060
    bt, bl = w('binder_t'), w('binder_luft')
    wx0 = x0 + w('wandler_rand')
    L['wandler_x'] = (wx0, wx0 + w('wandler_l'))
    zs0 = w('rahmen_z0') + w('binder_ueber') + bt / 2.0
    wz0 = zs0 + bt / 2.0 + bl
    L['wandler_z'] = (wz0, wz0 + w('wandler_b'))
    zs1 = L['wandler_z'][1] + bl + bt / 2.0

    # Pi rechts daneben, hinter dem USB-A-Stecker: Bauteile nach hinten
    # (-Y), Buchsen unten, die Kante mit der SD-Karte rechts (+X), ganz
    # ueber der Oberkante des 2060
    px0 = L['wandler_x'][1] + w('usb_a_platz')
    px1 = px0 + w('pi_l')
    x1 = px1 + w('pi_rand')
    L['x'] = (x0, x1)
    pz0 = w('rahmen_z0') + w('pi_ueber')
    pz1 = pz0 + w('pi_b')
    L['pi_x'], L['pi_z'] = (px0, px1), (pz0, pz1)
    r = w('pi_loch_rand')
    L['pi_loecher'] = [(x, z) for x in (px0 + r, px1 - r)
                       for z in (pz0 + r, pz1 - r)]
    L['steg_y'] = (y0 - w('steg_h'), y0)
    L['pcb_y'] = (L['steg_y'][0] - w('pi_pcb'), L['steg_y'][0])
    L['bauteile_y'] = (L['pcb_y'][0] - w('pi_bauteile'), L['pcb_y'][0])
    L['kernloch_y'] = (L['steg_y'][0], y0 + w('kernloch_platte'))
    # M2.5: so tief im Stehbolzen (ab seiner Stirn)
    L['m25_eingriff'] = w('m25_l') - w('pi_pcb')
    # Buchsen an der Unterkante, Mitte gezaehlt ab der SD-Kante (rechts)
    L['buchse_x'] = {'HDMI': px1 - w('pi_hdmi'), 'USB': px1 - w('pi_usb'),
                     'PWR': px1 - w('pi_pwr')}
    # Stecker in USB (zum Uno) und PWR (vom Wandler), nach unten
    ym = L['pcb_y'][0] - w('stecker_mitte')
    hb, ht = w('stecker_b') / 2.0, w('stecker_t') / 2.0
    L['stecker'] = {n: ((L['buchse_x'][n] - hb, L['buchse_x'][n] + hb),
                        (ym - ht, ym + ht), (pz0 - w('stecker_l'), pz0))
                    for n in ('USB', 'PWR')}

    L['wandler_y'] = (y0 - w('wandler_h'), y0)
    xm = sum(L['wandler_x']) / 2.0
    zm = sum(L['wandler_z']) / 2.0
    a = w('binder_abstand') / 2.0
    L['binder_x'] = (xm - a, xm + a)
    L['binder_z'] = (zs0, zs1)
    hx = w('binder_b') / 2.0
    L['binder_rechtecke'] = [(x - hx, z - bt / 2.0, x + hx, z + bt / 2.0)
                             for x in L['binder_x'] for z in L['binder_z']]
    # USB-A-Stecker rechts im Wandler, auf halber Hoehe
    ya = y0 - w('usb_a_mitte')
    L['stecker_a'] = ((L['wandler_x'][1], L['wandler_x'][1] + w('usb_a_l')),
                      (ya - w('usb_a_t') / 2.0, ya + w('usb_a_t') / 2.0),
                      (zm - w('usb_a_b') / 2.0, zm + w('usb_a_b') / 2.0))

    # Hoehe der Platte: unter der Nut bis ueber Pi und oberen Schlitz
    L['z'] = (zn - w('unter_nut'),
              max(pz1, zs1 + bt / 2.0) + w('rand_oben'))

    # M5 in der oberen Nut, Kopf hinten auf der Platte
    L['m5'] = [(x0 + w('m5_rand'), zn), (x1 - w('m5_rand'), zn)]
    L['m5_spitze'] = w('m5_l') - w('platte_dicke')     # in der Nut ab Flaeche
    L['m5_eingriff'] = L['m5_spitze'] - 1.8            # Lippe 1,8 [w]
    L['kopf_y'] = (y0 - w('m5_kopf_h'), y0)
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



def bau_halter(app, design, comp, L, fehler):
    """Platte an der Rueckseite des 2060, nach hinten (-Y) die vier
    Stehbolzen fuer den Pi mit Kernloch; durch die Platte die beiden M5 und
    die vier Schlitze fuer die Kabelbinder am Wandler. Fase am Fuss auf der
    Seite am 2060 (beim Druck auf dem Bett)."""
    y0, y1 = L['platte_y']
    k = quader(comp, 'Platte_PH', L['x'], L['platte_y'], L['z'],
               'neu').bodies.item(0)
    k.name = 'Pi-Halter'
    for i, (x, z) in enumerate(L['pi_loecher']):
        zylinder(comp, 'Steg{}_PH'.format(i + 1), 'y', (x, z), w('steg_d'),
                 L['steg_y'][0], y0 + 0.5, 'dazu', k)
    bohrung(comp, 'M25_PH', 'y', L['pi_loecher'], w('m25_kern'),
            L['kernloch_y'][0] - 0.5, L['kernloch_y'][1], k)
    bohrung(comp, 'M5_PH', 'y', L['m5'], w('m5_durchgang'), y0 - 1.0,
            y1 + 1.0, k)
    prismen(comp, 'Binder_PH', 'y', L['binder_rechtecke'], y0 - 1.0,
            y1 + 1.0, 'weg', k)
    fussfase(comp, k, 'z', y1, w('fase_fuss'), fehler, 'Pi-Halter')
    bbox_pruefen(k, 'Pi-Halter', (L['x'], (L['steg_y'][0], y1), L['z']),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_referenz(app, design, comp, L, fehler):
    """Stueck hinteres 2060, Pi als Platine und Huelle der Bauteile, die
    zwei Micro-USB-Stecker, der Wandler als groesster Quader, der passt,
    Schrauben und Hammermuttern — nur zur Ansicht, NICHT drucken."""
    y0, y1 = L['platte_y']

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

    sicher('2060_hinten', 'Aluminum 6061', bau_profil, comp, '2060_hinten',
           'x', (L['x'][0] - 30.0, L['x'][1] + 30.0), L['quer_y'],
           (L['tisch_z'], w('rahmen_z0')))
    sicher('Pi_Zero_2_W', 'Leiterplatte', quader, comp, 'Pi_Zero_2_W',
           L['pi_x'], L['pcb_y'], L['pi_z'], 'neu')
    sicher('Pi_Bauteile', 'Kunststoff', quader, comp, 'Pi_Bauteile',
           (L['pi_x'][0] + 1.0, L['pi_x'][1] - 1.0), L['bauteile_y'],
           (L['pi_z'][0], L['pi_z'][1] - 1.0), 'neu')
    for n, (sx, sy, sz) in sorted(L['stecker'].items()):
        sicher('Stecker_' + n, 'Kunststoff', quader, comp, 'Stecker_' + n,
               sx, sy, sz, 'neu')
    sicher('Wandler_5V', 'Kunststoff', quader, comp, 'Wandler_5V',
           L['wandler_x'], L['wandler_y'], L['wandler_z'], 'neu')
    sicher('Stecker_USB_A', 'Kunststoff', quader, comp, 'Stecker_USB_A',
           *L['stecker_a'], 'neu')
    for i, (x, z) in enumerate(L['pi_loecher']):
        sicher('M25x6_{}'.format(i + 1), 'Steel', zylinder, comp,
               'M25x6_{}'.format(i + 1), 'y', (x, z), w('m25_kopf_d'),
               L['pcb_y'][0] - w('m25_kopf_h'), L['pcb_y'][0], 'neu')
    hq = w('nut_kammer_b') / 2.0 - 0.1
    hl = w('hammer_l') / 2.0
    for i, (x, z) in enumerate(L['m5']):
        sicher('M5x12_Kopf_{}'.format(i + 1), 'Steel', zylinder, comp,
               'M5x12_Kopf_{}'.format(i + 1), 'y', (x, z), w('m5_kopf_d'),
               L['kopf_y'][0], L['kopf_y'][1], 'neu')
        sicher('M5x12_Schaft_{}'.format(i + 1), 'Steel', zylinder, comp,
               'M5x12_Schaft_{}'.format(i + 1), 'y', (x, z), 5.0, y0,
               y0 + w('m5_l'), 'neu')
        sicher('Hammermutter_{}'.format(i + 1), 'Steel', quader, comp,
               'Hammermutter_{}'.format(i + 1), (x - hl, x + hl),
               (y1 + w('nut_t') + 0.1, y1 + w('nut_kammer_t') - 0.1),
               (z - hq, z + hq), 'neu')


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/pihalter_check.py)."""
    (x0, x1), (z0, z1) = L['x'], L['z']
    px, pz = L['pi_x'], L['pi_z']
    wx, wz = L['wandler_x'], L['wandler_z']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py (X rechts, Y nach vorn,',
        '  Z senkrecht). Im Modell sind Y und Z getauscht (Modell-Z = Y).',
        '',
        'LAGE: an der Rueckseite des hinteren 2060, rechts neben der',
        '  Montageplatte des Elektronik-Kastens: X {:+.1f}..{:+.1f},'.format(
            x0, x1),
        '  Z {:+.1f}..{:+.1f}. Oben steht die Platte {:.0f} mm ueber das 2060'
        .format(z0, z1, z1 - w('rahmen_z0')),
        '  hinaus; dort ist in der Mitte frei — Pruefung:',
        '  tools/pihalter_check.py.',
        '',
        'MONTAGE: 2 Hammermuttern M5 in die obere Nut der Rueckseite des',
        '  2060, Platte ansetzen, 2 x M5x{:.0f} bei X {:+.1f} und {:+.1f}.'
        .format(w('m5_l'), L['m5'][0][0], L['m5'][1][0]),
        '  Inbus von hinten. Die Kabel in der mittleren Nut laufen unter',
        '  der Platte durch.',
        'PI: Bauteile nach hinten, Buchsen nach unten, die SD-Karte rechts;',
        '  4 x M2.5x{:.0f} selbstschneidend in die Stehbolzen (Kernloch {:.1f}).'
        .format(w('m25_l'), w('m25_kern')),
        '  Pi X {:+.1f}..{:+.1f}, Z {:+.1f}..{:+.1f}: ganz ueber dem 2060.'
        .format(px[0], px[1], pz[0], pz[1]),
        '  Buchsen von links: PWR (X {:+.1f}), USB (X {:+.1f}), HDMI frei.'
        .format(L['buchse_x']['PWR'], L['buchse_x']['USB']),
        'WANDLER 24 -> 5 V: links, Eingang zur Kastenseite, USB-Ausgang zum',
        '  Pi; 2 Kabelbinder senkrecht ueber seine Rueckseite, durch die',
        '  Schlitze ueber und unter ihm. Platz {:.0f} x {:.0f} x {:.0f}'
        .format(w('wandler_l'), w('wandler_b'), w('wandler_h')),
        '  (X {:+.1f}..{:+.1f}, Z {:+.1f}..{:+.1f}).'.format(
            wx[0], wx[1], wz[0], wz[1]),
        'KABEL: W18 (24 V) vom Kasten unter der Platte zum Eingang des',
        '  Wandlers, W19 vom USB-Ausgang in PWR, W17 von USB um den Kasten',
        '  zum Uno (docs/verkabelung.md).',
        '',
        'DRUCK (PETG, Bambu Lab A1): die Seite am 2060 aufs Bett, Stehbolzen',
        '  nach oben; keine Stuetzen. 4 Wandlinien, 30 % Infill.',
        '',
        'NICHT GEMESSEN [w]: Lochbild und Buchsen des Pi nach dem Massblatt',
        '  der Zero-Reihe; Platinendicke und Bauteilhoehe [?]. Den Pi vor dem',
        '  Druck auf die Zeichnung (docs/pihalter.svg) legen.',
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
        o.component.name = 'Pi-Halter'
        bau_halter(app, design, o.component, L, fehler)
        o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        oo = ref.component.occurrences.addNewComponent(einheit)
        oo.component.name = 'Ref_Rahmen_Pi'
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
