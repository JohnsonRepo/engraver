# YMotorhalter.py — Halter fuer den NEMA 17 der Y-Achse an der hinteren 2040
#
# Bauteil (ein Druckteil, keine Baugruppe): der Halter bewegt sich nicht, und
# Motor, Ritzel und Rollen sind Kaufteile.
#
# Antrieb der Y-Achse (Nutzerangaben 2026-09-24 und -26):
#   * jede Seite hat eine eigene SENKRECHTE Edelstahlwelle Ø5 in 625ZZ-Lagern,
#     hinter der hinteren Traverse; das ist eine 2040 hochkant (bis Rev. 1
#     als 2060 angenommen)
#   * auf jeder Welle zwei GT2-Ritzel: das OBERE treibt den Y-Riemen des
#     Wagens, das UNTERE sitzt auf Hoehe der oberen Nut der 2040 und haengt
#     am Motorriemen — der laeuft also auf beiden Seiten des Halters vor der
#     oberen Nut, die Nutensteine kommen in die untere
#   * EIN geschlossener Motorriemen laeuft um beide unteren Ritzel; dieser
#     Halter bringt den Motor in der Mitte dazu
#
# Warum zwei Umlenkrollen: laeuft der Riemen gerade von Welle zu Welle, fasst
# ein Motorritzel in der Mitte nur rund einen Zahn. Die Rollen legen den
# hinteren Trum als Omega um das Motorritzel — 180 Grad, 10 Zaehne im
# Eingriff. Der Motor steht OBEN auf dem Boden des Halters (Welle nach unten),
# Ritzel und Rollen haengen darunter in der Riemenebene. Gespannt wird, indem
# der Motor in Langloechern nach hinten rueckt: jeder Millimeter macht den
# Riemenweg 2 mm laenger.
#
# Koordinatensystem (Maschinenkoordinaten, in mm):
#   X = laengs der Traverse (Mitte des Halters = 0)
#   Y = nach HINTEN, weg von der Maschine; Y = 0 ist die Rueckseite der 2040
#   Z = senkrecht nach oben; Z = 0 ist die Oberkante der 2040
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
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Gestell: hintere Traverse 2040, hochkant (Nutzerangabe) -----------
    # Zwei Nuten auf der 40-mm-Rueckseite, 10 und 30 mm unter der Oberkante
    # [w] (20er Raster). In der OBEREN laeuft auf beiden Seiten des Halters
    # der Riemen, die Nutensteine sitzen deshalb nur in der UNTEREN
    # (Nutzerangabe 2026-09-26; Rev. 1 hatte eine 2060 mit drei Nuten).
    # Mit profil_hoehe = 60 baut das Skript wieder fuer eine 2060: dann
    # Nutensteine in allen Nuten ausser der obersten.
    'profil_hoehe':        (40.0,  'Traverse hochkant: Hoehe (2040)'),
    'profil_tiefe':        (20.0,  'Traverse: Tiefe (Maschine Y)'),
    'nut_raster':          (20.0,  'Traverse: Nutabstand'),
    'nut_oben':            (10.0,  'Traverse: obere Nut unter der Oberkante'),
    # Nutenstein M5 (Hammermutter, Nut 6) [w]: Lippe vor dem Stein, Gewinde-
    # laenge im Stein, Platz unter der Nutoeffnung. Die Schraube muss im
    # Stein greifen und darf hinten nicht aufsitzen.
    'nut_lippe':            (1.8,  'Nut: Dicke der Lippe vor dem Nutenstein'),
    'nutenstein_h':         (4.0,  'Nutenstein M5: Gewindelaenge'),
    'nut_tiefe':            (6.0,  'Nut: Platz ab Profilflaeche nach innen'),

    # --- Lage der Wellen und des Riemens (Nutzerangaben) -------------------
    # Riemenlauf, auf den Rollen und Motor ausgerichtet sind: Wellenachsen so
    # weit hinter der Traverse. Rev. 2: 20 -> 35 mm, der Motor sitzt damit
    # 15 mm weiter aussen (Nutzerangabe 2026-09-26) — und die beiden Rollen
    # mit ihm, sonst liefe der vordere Trum bei Wellen ueber 30 mm in die
    # Rollenflansche. Wo die Wellen wirklich stehen, ist NICHT gemessen [?]:
    # der Halter passt fuer 14..45 mm, der hintere Trum laeuft dann leicht
    # schraeg an die Rollen (Pruefung, Abschnitt 11).
    'welle_y':             (35.0,  'Riemenlauf: Wellenachsen hinter der Traverse'),
    # NICHT gemessen [?]: Abstand der beiden Wellen. Erzeugt keine
    # Geometrie, nur die Riemenlaenge im Bericht.
    'welle_abstand':      (500.0,  'Abstand der beiden senkrechten Wellen'),
    # Die unteren Ritzel sitzen auf Hoehe der oberen Nut (Nutzerangabe);
    # sie lassen sich auf der Welle etwas verschieben.
    'riemen_z':           (-10.0,  'Riemenmitte unter der Traversen-Oberkante'),

    # --- Kaufteil: NEMA 17 (hardware.md [w], wie an der Z-Achse) -----------
    'motor_flansch':       (42.3,  'NEMA17: Flanschmass'),
    'motor_loch':          (31.0,  'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0,  'NEMA17: Zentrierbund Durchmesser'),
    'motor_bund_h':         (2.0,  'NEMA17: Zentrierbund Hoehe'),
    'motor_welle_l':       (24.0,  'NEMA17: Wellenlaenge ab Flansch'),
    # Nur Umhuellende: mit 48 mm gerechnet, ein 40er steht 8 mm niedriger.
    'motor_laenge':        (48.0,  'NEMA17: Koerperlaenge (nur Freiraum)'),
    'motor_gewinde_tiefe':  (4.5,  'NEMA17: Gewindetiefe im Flansch'),

    # --- Kaufteil: GT2-Riementrieb (hardware.md [w]) -----------------------
    'gt2_teilung':          (2.0,  'GT2: Teilung'),
    'riemen_breite':        (6.0,  'GT2-Riemen: Breite'),
    'riemen_dicke':        (1.38,  'GT2-Riemen: Gesamtdicke'),
    'riemen_zahn':         (0.75,  'GT2-Riemen: Zahnhoehe'),
    'riemen_pld':         (0.254,  'GT2: Wirklinie ueber dem Zahngrund'),
    # Zaehnezahlen sind einheitenlos (EINHEITENLOS unten).
    'ritzel_z_motor':      (20.0,  'Motorritzel: Zaehne'),
    'ritzel_z_welle':      (20.0,  'unteres Wellenritzel: Zaehne'),
    'ritzel_flansch_d':    (16.0,  'GT2-Ritzel 20Z: Flanschdurchmesser'),
    'ritzel_laenge':       (16.0,  'GT2-Ritzel: Gesamtlaenge'),
    'ritzel_spur':          (7.0,  'GT2-Ritzel: Breite der Riemenspur'),
    'ritzel_flansch_h':     (1.0,  'GT2-Ritzel: Flanschdicke'),

    # --- Kaufteil: Umlenkrolle = 2x F625ZZ Ruecken an Ruecken --------------
    # Laeuft auf dem glatten Riemenruecken (hardware.md: "Glatte Umlenkung").
    # Flansche aussen, dazwischen 8 mm Laufflaeche fuer den 6-mm-Riemen.
    'rolle_d':             (16.0,  'Umlenkrolle: Laufdurchmesser (F625ZZ)'),
    'rolle_flansch_d':     (18.0,  'Umlenkrolle: Flanschdurchmesser'),
    'rolle_h':             (10.0,  'Umlenkrolle: Hoehe (2x F625ZZ)'),
    'rolle_flansch_h':      (1.0,  'Umlenkrolle: Flanschdicke'),

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
    'm5_mutter_h':          (5.0,  'M5 Sicherungsmutter DIN 985: Hoehe'),
    # Die vorhandenen Messingeinsaetze (Ø5 aussen) [v], wie am Toolhead.
    'insert_m3_d':          (4.6,  'Gewindeeinsatz M3: Einpressbohrung'),
    'insert_m3_t':          (7.0,  'Gewindeeinsatz M3: Sacklochtiefe'),

    # --- Halter ------------------------------------------------------------
    # Anlageplatte an der Traverse: unten 2 mm ueber der Profilunterkante,
    # oben buendig mit Block und Fuehrungsrippen.
    'grund_dicke':          (6.0,  'Anlageplatte: Dicke'),
    'grund_rand_unten':     (2.0,  'Anlageplatte: endet so weit ueber der Profilunterkante'),
    'schraube_x':          (15.0,  'M5-Schrauben: Abstand von der Mitte'),
    # Boden: der Motor steht darauf, Ritzel und Rollen haengen darunter.
    # Hoechstens motor_welle_l - Ritzellaenge - Luft dick, sonst reicht die
    # Motorwelle nicht mehr durch das Ritzel (Pruefung).
    'boden_dicke':          (6.0,  'Boden: Dicke'),
    'block_hoehe':         (10.0,  'Block und Fuehrungsrippen ueber dem Boden'),
    'rippe_breite':         (3.0,  'Fuehrungsrippe: Breite'),
    'spiel_locker':         (0.4,  'Montagespiel, diametral'),
    # Kuerzeste Omega-Tiefe (Rollenachsen -> Motorachse): kleiner laufen die
    # vorderen Motorschrauben unter dem Boden in die Rollenflansche (29,0
    # rechnet die Pruefung). Groesser = fuer einen laengeren Riemen.
    'omega_min':           (30.0,  'Omega-Tiefe mit dem Motor ganz vorn'),
    # Spannweg: jeder mm macht den Riemenweg 2 mm laenger.
    'spann_weg':           (20.0,  'Spannweg des Motors in den Langloechern'),
    'block_rand':           (5.5,  'Block hinter den Rollenachsen'),
    'rand_hinten':          (2.5,  'Boden hinter dem Motor (ganz hinten)'),
    'wellen_schlitz':       (8.0,  'Langloch fuer Motorwelle: Breite'),
    # Lasche fuer die Spannschraube, oben auf dem Block. Vorderseite unter
    # 45 Grad, damit sie in der Drucklage ohne Stuetzen waechst.
    'lasche_hoehe':        (10.0,  'Spannlasche: Hoehe ueber dem Block'),
    'lasche_breite':       (12.0,  'Spannlasche: Breite'),
    'lasche_tiefe_oben':    (5.0,  'Spannlasche: Tiefe an der Oberkante'),
    'luft_min':             (1.0,  'Mindestluft zwischen Teilen'),
    'fase_fuss':            (0.4,  'Fase gegen Elefantenfuss an der Anlage'),
}

# Werte ohne Einheit (werden als einheitenlose User-Parameter angelegt)
EINHEITENLOS = {'ritzel_z_motor', 'ritzel_z_welle'}

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


def riemenlaenge(L, abstand, omega):
    """Laenge des geschlossenen Motorriemens (Wirklinie) fuer Wellenabstand
    und Omega-Tiefe: vorderer Trum + zwei halbe Umschlingungen an den Wellen
    + hinterer Trum bis zu den Rollen + zwei Viertel an den Rollen + Omega
    hin und zurueck + halbe Umschlingung am Motor."""
    return 2.0 * abstand + L['riemen_konst'] + 2.0 * omega


def lage():
    """Alle abgeleiteten Ebenen, Achsen und Lochbilder in Maschinen-
    koordinaten (mm). Einzige Quelle fuer Geometrie UND Pruefung."""
    L = {}

    # ---- Riementrieb: Wirkradien -------------------------------------------
    # Der Riemen umschlingt die Ritzel mit der Zahnseite (Wirkradius =
    # Teilkreis) und die Rollen mit dem Ruecken: dort liegt die Wirklinie
    # um (Dicke - Zahnhoehe - PLD) ausserhalb der Laufflaeche.
    L['rp_motor'] = teilkreis_r(w('ritzel_z_motor'))
    L['rp_welle'] = teilkreis_r(w('ritzel_z_welle'))
    L['wirk_ruecken'] = w('riemen_dicke') - w('riemen_zahn') - w('riemen_pld')
    L['wirk_zahn'] = w('riemen_pld') + w('riemen_zahn')      # bis Zahnspitze
    L['rp_rolle'] = w('rolle_d') / 2.0 + L['wirk_ruecken']
    # Konstanter Teil der Riemenlaenge (siehe riemenlaenge()):
    #   2*pi*rp_welle + (pi - 2) * (rp_motor + rp_rolle)
    L['riemen_konst'] = (2.0 * math.pi * L['rp_welle']
                         + (math.pi - 2.0) * (L['rp_motor'] + L['rp_rolle']))

    # ---- Y-Kette: von der Traversen-Rueckseite nach hinten -------------------
    L['grund_y1'] = w('grund_dicke')
    L['trum_vorn_y'] = w('welle_y') - L['rp_welle']          # Wirklinie
    L['trum_hinten_y'] = w('welle_y') + L['rp_welle']
    # Die Rollen liegen so, dass der hintere Trum gerade (parallel zur
    # Traverse) an sie anlaeuft, und so weit auseinander, dass die beiden
    # Omega-Trume parallel ans Motorritzel gehen: 180 Grad Umschlingung in
    # jeder Spannstellung.
    L['rolle_y'] = L['trum_hinten_y'] + L['rp_rolle']
    L['rolle_x'] = L['rp_motor'] + L['rp_rolle']
    L['block_y1'] = L['rolle_y'] + w('block_rand')
    L['motor_y_min'] = L['rolle_y'] + w('omega_min')
    L['motor_y_max'] = L['motor_y_min'] + w('spann_weg')
    L['motor_y_mitte'] = (L['motor_y_min'] + L['motor_y_max']) / 2.0
    L['boden_y1'] = (L['motor_y_max'] + w('motor_flansch') / 2.0
                     + w('rand_hinten'))
    # Die Wellenlage ist nicht gemessen. Ohne neuen Lauf passt der Halter,
    # solange der vordere Trum zwischen Anlageplatte (Riemenruecken) und
    # Rollenflanschen (Zahnseite) durchgeht; der hintere laeuft dann nur
    # leicht schraeg an die Rollen.
    L['welle_y_von'] = (L['grund_y1'] + L['wirk_ruecken'] + L['rp_welle']
                        + w('luft_min'))
    L['welle_y_bis'] = (L['rolle_y'] - w('rolle_flansch_d') / 2.0
                        - L['wirk_zahn'] + L['rp_welle'] - w('luft_min'))

    # ---- Z-Kette -------------------------------------------------------------
    # Nuten auf der Rueckseite der Traverse: 2040 -> zwei, 2060 -> drei. In
    # der obersten laeuft der Riemen, alle anderen tragen Nutensteine.
    n_nuten = int(round(w('profil_hoehe') / w('nut_raster')))
    L['nut_z'] = [-w('nut_oben') - i * w('nut_raster') for i in range(n_nuten)]
    L['profil_name'] = '20{:.0f}'.format(w('profil_hoehe'))
    L['grund_z0'] = -w('profil_hoehe') + w('grund_rand_unten')
    L['riemen_z0'] = w('riemen_z') - w('riemen_breite') / 2.0
    L['riemen_z1'] = w('riemen_z') + w('riemen_breite') / 2.0
    # Unter dem Boden: M5-Scheibe, dann die Rolle, deren Mitte in der
    # Riemenebene liegt. Daraus folgt die Unterseite des Bodens.
    L['boden_z0'] = w('riemen_z') + w('rolle_h') / 2.0 + w('m5_scheibe_h')
    L['boden_z1'] = L['boden_z0'] + w('boden_dicke')
    L['rolle_z1'] = L['boden_z0'] - w('m5_scheibe_h')
    L['rolle_z0'] = L['rolle_z1'] - w('rolle_h')
    L['block_z1'] = L['boden_z1'] + w('block_hoehe')
    L['lasche_z1'] = L['block_z1'] + w('lasche_hoehe')
    L['spann_z'] = (L['block_z1'] + L['lasche_z1']) / 2.0
    L['grund_z1'] = L['block_z1']
    # Motor steht auf dem Boden, Welle nach unten; das Ritzel sitzt mit der
    # Riemenspur in der Riemenebene, Nabe nach unten.
    L['motor_flansch_z'] = L['boden_z1']
    L['motor_z1'] = L['motor_flansch_z'] + w('motor_laenge')
    L['welle_z0'] = L['motor_flansch_z'] - w('motor_welle_l')
    L['ritzel_z1'] = (w('riemen_z') + w('ritzel_spur') / 2.0
                      + w('ritzel_flansch_h'))
    L['ritzel_z0'] = L['ritzel_z1'] - w('ritzel_laenge')
    L['ritzel_luft'] = L['boden_z0'] - L['ritzel_z1']
    # Madenschrauben in der Mitte der Nabe
    nabe = w('ritzel_laenge') - w('ritzel_spur') - 2.0 * w('ritzel_flansch_h')
    L['ritzel_nabe'] = nabe
    L['madenschraube_z'] = L['ritzel_z0'] + nabe / 2.0

    # ---- Breite: Fuehrungsrippen fassen den Motor mit spiel_locker ---------
    L['rippe_x0'] = w('motor_flansch') / 2.0 + w('spiel_locker') / 2.0
    L['halbe_breite'] = L['rippe_x0'] + w('rippe_breite')

    # ---- Lochbilder ------------------------------------------------------
    # M5 in jede Nut ausser der obersten (bei der 2040: nur die untere), je
    # zwei Nutensteine
    L['m5_loecher'] = [(sx * w('schraube_x'), z)
                       for z in L['nut_z'][1:] for sx in (-1, 1)]
    L['rolle_loecher'] = [(-L['rolle_x'], L['rolle_y']),
                          (L['rolle_x'], L['rolle_y'])]
    # Motorschrauben: Langloecher in Y, Mitte = Mitte des Spannwegs
    h = w('motor_loch') / 2.0
    L['motor_langloecher'] = [(sx * h, L['motor_y_mitte'] + sy * h)
                              for sy in (-1, 1) for sx in (-1, 1)]
    L['bund_schlitz_b'] = w('motor_bund_d') + w('spiel_locker')
    L['bund_tasche_t'] = w('motor_bund_h') + w('spiel_locker')

    # ---- Spannlasche und Spannschraube -------------------------------------
    # Profil in Y-Z: hinten senkrecht (buendig mit dem Block), vorn 45 Grad.
    L['lasche_y0_unten'] = (L['block_y1'] - w('lasche_tiefe_oben')
                            - w('lasche_hoehe'))
    L['lasche_y0_oben'] = L['block_y1'] - w('lasche_tiefe_oben')
    # Tiefe der Lasche auf Hoehe der Schraube (45 Grad: linear)
    L['spann_tiefe'] = w('lasche_tiefe_oben') + (L['lasche_z1']
                                                 - L['spann_z'])
    # Wie weit die Spitze hinten aus der Lasche ragen muss, um die Motor-
    # vorderseite zu erreichen — ganz vorn und ganz hinten gespannt.
    vorn = L['block_y1']
    L['spann_spitze_min'] = L['motor_y_min'] - w('motor_flansch') / 2.0 - vorn
    L['spann_spitze_max'] = L['motor_y_max'] - w('motor_flansch') / 2.0 - vorn
    L['spann_schraube'] = normlaenge(
        L['spann_tiefe'] + L['spann_spitze_max'] + 1.0, M3_LAENGEN)
    # Kopf ganz vorn (Motor ganz vorn): liegt er noch hinter der Anlage?
    L['spann_kopf_y'] = (vorn + L['spann_spitze_min'] - L['spann_schraube'])

    # ---- Schraubenlaengen -------------------------------------------------
    # M5 in den Nutenstein: Platte + Scheibe, dann ueber die Lippe in den
    # Stein. Ueberstand hinter der Profilflaeche = was in die Nut ragt.
    L['m5_schraube'] = normlaenge(
        w('grund_dicke') + w('m5_scheibe_h') + w('nut_lippe') + 3.0,
        M5_LAENGEN)
    L['m5_ueberstand'] = (L['m5_schraube'] - w('grund_dicke')
                          - w('m5_scheibe_h'))
    L['m5_eingriff'] = (min(L['m5_ueberstand'],
                            w('nut_lippe') + w('nutenstein_h'))
                        - w('nut_lippe'))
    # Rollenachse M5 von oben: Scheibe, Block + Boden, Scheibe, Rolle,
    # Scheibe, Sicherungsmutter, zwei Gewindegaenge Ueberstand.
    L['rolle_klemm'] = (3.0 * w('m5_scheibe_h') + (L['block_z1']
                                                    - L['boden_z0'])
                        + w('rolle_h') + w('m5_mutter_h'))
    L['rolle_schraube'] = normlaenge(L['rolle_klemm'] + 1.6, M5_LAENGEN)
    L['rolle_schraube_z0'] = (L['block_z1'] + w('m5_scheibe_h')
                              - L['rolle_schraube'])
    # Motorschrauben von unten: Boden + Scheibe, dann in den Motor —
    # mindestens 3 mm Eingriff und 0,5 mm vor dem Gewindegrund.
    L['motor_klemm'] = w('boden_dicke') + w('m3_scheibe_h')
    L['motor_schraube'] = normlaenge(L['motor_klemm'] + 3.0, M3_LAENGEN)
    L['motor_eingriff'] = L['motor_schraube'] - L['motor_klemm']

    # ---- Riemen -------------------------------------------------------------
    L['riemen_l_min'] = riemenlaenge(L, w('welle_abstand'), w('omega_min'))
    L['riemen_l_max'] = riemenlaenge(L, w('welle_abstand'),
                                     w('omega_min') + w('spann_weg'))
    L['zaehne_im_eingriff'] = w('ritzel_z_motor') / 2.0      # 180 Grad
    L['mm_pro_umdrehung'] = w('ritzel_z_welle') * w('gt2_teilung')
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


def ebene_y(comp, y_mm, name):
    """Ebene senkrecht zu Maschinen-Y. Skizzenkoordinaten (Maschine X, Z)."""
    if abs(y_mm) < 1e-9:
        return comp.xYConstructionPlane
    return _offsetebene(comp, comp.xYConstructionPlane, y_mm / 10.0, 'z', name)


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


def vieleck(sk, ecken):
    """Geschlossenes Vieleck durch die Ecken (u, v) in mm. Die Linien werden
    ueber ihre SketchPoints verkettet (wie das Sechskant in ToolheadZ),
    damit das Profil sicher schliesst."""
    linien = sk.sketchCurves.sketchLines
    erste = linien.addByTwoPoints(punkt(sk, *ecken[0]), punkt(sk, *ecken[1]))
    vorher = erste
    for i in range(2, len(ecken)):
        vorher = linien.addByTwoPoints(vorher.endSketchPoint,
                                       punkt(sk, *ecken[i]))
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


def _symmetrisch(comp, prof, laenge_mm, operation, ziel=None):
    """Extrusion symmetrisch um die Skizzenebene (Gesamtlaenge laenge_mm):
    die Richtung der Ebenennormale spielt dann keine Rolle."""
    ein = comp.features.extrudeFeatures.createInput(prof, operation)
    ein.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(laenge_mm / 10.0), True)
    if ziel is not None:
        ein.participantBodies = [ziel]
    return comp.features.extrudeFeatures.add(ein)


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
    """Y-Motorhalter, ein Druckteil.

    ANLAGEPLATTE an der Rueckseite der 2040, zwei M5 in die untere Nut — in
    der oberen laeuft der Riemen. Darauf oben der BODEN, der nach hinten
    auskragt: der
    Motor steht auf ihm (Welle nach unten), Ritzel und Umlenkrollen haengen
    darunter in der Riemenebene. Vorn auf dem Boden ein BLOCK, durch den die
    Achsen der beiden Rollen gehen, seitlich zwei FUEHRUNGSRIPPEN, zwischen
    denen der Motor zum Spannen nach hinten rueckt. Auf dem Block die
    SPANNLASCHE mit Gewindeeinsatz fuer die Spannschraube, die den Motor
    nach hinten drueckt.

    Unter dem Boden bleibt alles frei: der vordere Trum laeuft zwischen
    Anlageplatte und Rollen durch, der Riemen laesst sich von unten
    einlegen.

    Drucklage: ANLAGEFLAECHE aufs Bett (Aufbaurichtung = Maschine Y). Boden,
    Block und Rippen wachsen als Wand nach oben, die Lasche hat eine
    45-Grad-Unterseite — keine Stuetzen. Die M5-Bohrungen und die Spann-
    schraube stehen senkrecht und werden rund."""
    hb = L['halbe_breite']
    e_vorn = ebene_y(comp, 0.0, 'E_Anlage')

    # Anlageplatte
    sk = skizze(comp, e_vorn, 'Sk_Anlageplatte')
    rechteck(sk, -hb, L['grund_z0'], hb, L['grund_z1'])
    koerper = neu(comp, groesstes_profil(sk), w('grund_dicke')).bodies.item(0)
    koerper.name = 'YMotorhalter'

    # Boden: kragt nach hinten aus, der Motor steht darauf
    sk = skizze(comp, e_vorn, 'Sk_Boden')
    rechteck(sk, -hb, L['boden_z0'], hb, L['boden_z1'])
    dazu(comp, groesstes_profil(sk), L['boden_y1'], koerper)

    # Fuehrungsrippen: fassen den Motor seitlich, ueber die ganze Laenge
    sk = skizze(comp, e_vorn, 'Sk_Fuehrungsrippen')
    for sx in (-1, 1):
        rechteck(sk, sx * L['rippe_x0'], L['boden_z1'], sx * hb,
                 L['block_z1'])
    dazu(comp, alle_profile(sk), L['boden_y1'], koerper)

    # Block: traegt die Rollenachsen, zwischen den Rippen bis hinter die
    # Rollen
    sk = skizze(comp, e_vorn, 'Sk_Block')
    rechteck(sk, -L['rippe_x0'], L['boden_z1'], L['rippe_x0'], L['block_z1'])
    dazu(comp, groesstes_profil(sk), L['block_y1'], koerper)

    # Spannlasche: Profil in Y-Z, vorn 45 Grad (Drucklage ohne Stuetzen)
    e_mitte_x = ebene_x(comp, 0.0, 'E_Mitte_X')
    sk = skizze(comp, e_mitte_x, 'Sk_Spannlasche')
    vieleck(sk, [(L['lasche_y0_unten'], L['block_z1']),
                 (L['block_y1'], L['block_z1']),
                 (L['block_y1'], L['lasche_z1']),
                 (L['lasche_y0_oben'], L['lasche_z1'])])
    dazu_mittig(comp, groesstes_profil(sk), w('lasche_breite'), koerper)

    # M5-Bohrungen fuer die Nutensteine
    sk = skizze(comp, e_vorn, 'Sk_Bohrungen_M5')
    for x, z in L['m5_loecher']:
        kreis(sk, x, z, w('m5_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Rollenachsen senkrecht durch Block und Boden
    e_boden = ebene_z(comp, (L['boden_z0'] + L['boden_z1']) / 2.0,
                      'E_Boden_mitte')
    sk = skizze(comp, e_boden, 'Sk_Rollenachsen')
    for x, y in L['rolle_loecher']:
        kreis(sk, x, y, w('m5_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Motorschrauben: Langloecher in Y ueber den Spannweg
    sk = skizze(comp, e_boden, 'Sk_Langloecher_Motor')
    for x, y in L['motor_langloecher']:
        langloch(sk, x, y, w('m3_durchgang'), w('spann_weg') / 2.0)
    durch(comp, alle_profile(sk), koerper)

    # Motorwelle: Langloch durch den Boden
    sk = skizze(comp, e_boden, 'Sk_Wellenschlitz')
    langloch(sk, 0.0, L['motor_y_mitte'], w('wellen_schlitz'),
             w('spann_weg') / 2.0)
    durch(comp, alle_profile(sk), koerper)

    # Zentrierbund: flache Tasche von oben, ebenfalls als Langloch
    e_bund = ebene_z(comp, L['boden_z1'] - L['bund_tasche_t'] / 2.0,
                     'E_Bundtasche')
    sk = skizze(comp, e_bund, 'Sk_Bundtasche')
    langloch(sk, 0.0, L['motor_y_mitte'], L['bund_schlitz_b'],
             w('spann_weg') / 2.0)
    tasche(comp, alle_profile(sk), L['bund_tasche_t'], koerper)

    # Spannschraube: Durchgang laengs Y durch die Lasche, hinten Einpress-
    # bohrung fuer den Messingeinsatz (von der Motorseite eingeschmolzen:
    # die Last drueckt ihn tiefer in die Bohrung, nicht heraus).
    sk = skizze(comp, ebene_y(comp, L['block_y1'] - L['spann_tiefe'] / 2.0,
                              'E_Spannschraube'), 'Sk_Spannschraube')
    kreis(sk, 0.0, L['spann_z'], w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    sk = skizze(comp, ebene_y(comp, L['block_y1'] - w('insert_m3_t') / 2.0,
                              'E_Spanneinsatz'), 'Sk_Spanneinsatz')
    kreis(sk, 0.0, L['spann_z'], w('insert_m3_d'))
    tasche(comp, alle_profile(sk), w('insert_m3_t'), koerper)

    fussfase(comp, koerper, 'z', 0.0, w('fase_fuss'), fehler, 'Y-Motorhalter')
    bbox_pruefen(koerper, 'Y-Motorhalter',
                 ((-hb, hb), (0.0, L['boden_y1']),
                  (L['grund_z0'], L['lasche_z1'])), fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/y_motorhalter_check.py)."""
    S = w('welle_abstand')
    h = [
        'BEZUG: Y = 0 ist die Rueckseite der hinteren {} (hochkant),'.format(
            L['profil_name']),
        '  Z = 0 ihre Oberkante, X = 0 die Mitte des Halters. Y zaehlt nach',
        '  HINTEN, weg von der Maschine. Im Modell ist Y und Z getauscht.',
        '',
        'RIEMENLAUF: ein geschlossener GT2-Riemen um die unteren Ritzel',
        '  beider Wellen. In der Mitte legen zwei Umlenkrollen (je 2x F625ZZ)',
        '  den hinteren Trum als OMEGA um das Motorritzel: 180 Grad,',
        '  {:.0f} Zaehne im Eingriff. Gerade durchlaufend waere es ~1 Zahn.'
        .format(L['zaehne_im_eingriff']),
        '  Riemenebene Z = {:+.1f} mm (Hoehe der oberen Nut).'.format(
            w('riemen_z')),
        '  Ausgerichtet auf Wellen {:.1f} mm hinter der {} -> vorderer'
        .format(w('welle_y'), L['profil_name']),
        '  Trum bei Y = {:.1f}, hinterer bei Y = {:.1f} mm (Wirklinie).'.format(
            L['trum_vorn_y'], L['trum_hinten_y']),
        '  Seit Rev. 2 sitzen Motor und Rollen 15 mm weiter aussen als in',
        '  Rev. 1 (welle_y 20 -> 35). Wo die Wellen wirklich stehen, ist NICHT',
        '  gemessen: der Halter passt fuer {:.0f} bis {:.0f} mm, der hintere Trum'
        .format(L['welle_y_von'], L['welle_y_bis']),
        '  laeuft dann leicht schraeg an die Rollen (bei 20 mm: {:.1f} Grad).'
        .format(math.degrees(math.atan(
            (w('welle_y') - 20.0) / (w('welle_abstand') / 2.0
                                     - L['rolle_x'])))),
        '  Rollen bei X = +-{:.2f}, Y = {:.2f} mm.'.format(
            L['rolle_x'], L['rolle_y']),
        '  Motorachse Y = {:.1f} (ganz vorn) bis {:.1f} mm (ganz hinten).'.format(
            L['motor_y_min'], L['motor_y_max']),
        '',
        'DREHRICHTUNG: beide Wellen drehen GLEICHSINNIG (ein Riemen kann',
        '  nicht anders). Damit beide Y-Wagen in dieselbe Richtung fahren,',
        '  muss der linke Wagen am inneren und der rechte am aeusseren Trum',
        '  seines Y-Riemens haengen (oder umgekehrt) — NICHT spiegelbildlich.',
        '  Vor dem Festziehen von Hand durchdrehen und pruefen!',
        '',
        'RIEMENLAENGE (geschlossen, GT2, 6 mm): L = 2*S + {:.1f} + 2*Omega'
        .format(L['riemen_konst']),
        '  S = Abstand der Wellen (NICHT gemessen, hier {:.0f} mm)'.format(S),
        '  Omega = {:.0f} (Motor vorn) bis {:.0f} mm (Motor hinten)'.format(
            w('omega_min'), w('omega_min') + w('spann_weg')),
        '  -> passender Riemen: {:.0f} bis {:.0f} mm, am besten ~{:.0f} mm'
        .format(L['riemen_l_min'], L['riemen_l_max'],
                (L['riemen_l_min'] + L['riemen_l_max']) / 2.0),
        '  S messen, dann Riemen waehlen. Ist keiner im Fenster zu haben:',
        '  omega_min groesser (laengerer Riemen) oder spann_weg groesser.',
        '',
        'SPANNEN: Motor rueckt in Langloechern nach hinten, jeder mm macht',
        '  den Riemenweg 2 mm laenger. Spannschraube M3x{:.0f} von vorn durch'
        .format(L['spann_schraube']),
        '  die Lasche (Messingeinsatz Ø{:.1f} von hinten eingeschmolzen), sie'
        .format(w('insert_m3_d')),
        '  drueckt auf die Motorvorderseite und haelt ihn gegen den Zug fest.',
        '  Richtwert ~20 N Vorspannung: vorderer Trum schwingt dann mit',
        '  ~{:.0f} Hz (bei S = {:.0f} mm), oder 1 N (100 g) in der Mitte'.format(
            1.0 / (2.0 * S / 1000.0) * math.sqrt(20.0 / 0.008), S),
        '  drueckt ihn ~{:.0f} mm durch. Dann die 4 Motorschrauben fest.'.format(
            1.0 * S / (4.0 * 20.0)),
        '',
        'MOTOR steht OBEN (Welle nach unten), Flansch bei Z = {:+.1f}, Oberkante'
        .format(L['motor_flansch_z']),
        '  bei Z = {:+.0f} mm ({:.0f}er Motor). Freiraum hinter der Traverse'
        .format(L['motor_z1'], w('motor_laenge')),
        '  pruefen: Y {:.0f}..{:.0f} mm — Portal und Toolhead duerfen in der'
        .format(L['motor_y_min'] - w('motor_flansch') / 2.0,
                L['motor_y_max'] + w('motor_flansch') / 2.0),
        '  hintersten Stellung nicht hineinfahren.',
        '  RITZEL mit der Nabe nach unten aufschieben, {:.1f} mm unter dem'
        .format(L['ritzel_luft']),
        '  Boden (dann liegt die Spur in der Riemenebene), Madenschraube',
        '  auf die Abflachung.',
        '',
        'VERSCHRAUBUNG:',
        '  Halter -> {} ...... {}x M5x{:.0f} + Scheibe + Nutenstein M5 in der'
        .format(L['profil_name'], len(L['m5_loecher']), L['m5_schraube']),
        '                        {}, {:.1f} mm Eingriff. Die obere Nut'.format(
            'unteren Nut' if len(L['nut_z']) == 2 else 'mittleren + unteren Nut',
            L['m5_eingriff']),
        '                        bleibt frei: vor ihr laeuft der Riemen.',
        '  Umlenkrollen ........ 2x M5x{:.0f} von oben + 3 Scheiben + Sicherungs-'
        .format(L['rolle_schraube']),
        '                        mutter, je 2x F625ZZ (Flansche aussen)',
        '  NEMA 17 -> Boden .... 4x M3x{:.0f} + Scheibe von unten, {:.1f} mm Eingriff'
        .format(L['motor_schraube'], L['motor_eingriff']),
        '  Spannschraube ....... 1x M3x{:.0f} + 1x Messingeinsatz M3'.format(
            L['spann_schraube']),
        '',
        'DRUCK (PETG, Bambu Lab A1): ANLAGEFLAECHE aufs Bett. Boden, Block',
        '  und Rippen wachsen als Wand nach oben, die Lasche hat eine 45-Grad-',
        '  Unterseite — keine Stuetzen. {:.0f} mm hoch. 4 Wandlinien, >=40 %'
        .format(L['boden_y1']),
        '  Infill. PETG, weil der Motor warm wird.',
        '',
        'KEINE BOHRLEHRE: der Halter verbindet kein zweites Druckteil, die',
        '  {} wird nicht gebohrt (Nutensteine), und das NEMA-17-Lochbild'
        .format(L['profil_name']),
        '  31 x 31 sitzt schon an der Z-Achse.',
        '',
        'NOCH ZU MESSEN: Wellenabstand S, Lage der Wellen hinter der {}'
        .format(L['profil_name']),
        '  (welle_y), Motorlaenge. Nach dem Eintragen neu laufen lassen und',
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
