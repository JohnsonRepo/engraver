# Portal.py — Y-Schlitten des Portals (MGN12H) mit X-Antrieb
#
# Baugruppe aus neun Druckteilen. Getrennt, weil jedes Teil nur so ohne
# Stuetzmaterial druckbar ist — die Y-Riemenklemme haengt unter der Platte,
# die Rohrhalterung steht auf ihr:
#   Schlitten_links/rechts     Platte auf dem MGN12H-Wagen. Das Portalrohr
#                              liegt unten auf, eine Rueckwand (2x M5 in
#                              Nutensteinen) und ein Stirnblock (M5 in die
#                              Kernbohrung) halten es. Die Vorderseite bleibt
#                              frei — dort sitzt die X-Schiene.
#   Riemenblock_links/rechts   haengt unter der Platte neben dem Wagen und
#                              klemmt den Y-Riemen: vorn fest mit Stift,
#                              hinten ueber den Spannschieber.
#   Spannschieber_links/rechts haelt das hintere Riemenende; eine M3 von
#                              hinten drueckt ihn nach vorn und spannt.
#   Motorhalter                X-Motor (NEMA 17) stehend ueber dem linken
#                              Rohrende, Welle nach unten.
#   Umlenkhalter + Spannklotz  X-Umlenkung rechts: 20-Z-Rolle mit Lager auf
#                              einer M5 im Langloch; eine M3 von aussen zieht
#                              den Spannklotz und damit die Rolle nach aussen.
#   Bohrlehren                 ausgeblendet
#
# Den X-Riemen klemmt der Riemenhalter hinten an der Traegerplatte
# (ToolheadZ.py, Rev. 33). Seine Lage (x_riemen_y, x_riemen_z0) steht in
# beiden Skripten, tools/portal_check.py vergleicht sie.
#
# Koordinaten = Maschinenkoordinaten wie in ToolheadZ.py: Y nach vorn (weg
# vom Portal), Z senkrecht, Y = 0 an der Stirnflaeche des X-Wagens, Z = 0 in
# der Mitte seines Lochbildes (= Mitte des Portalrohrs). ABWEICHEND liegt
# X = 0 in der Mitte des Portalrohrs, nicht am X-Wagen — der faehrt.
# Was fuer beide Seiten gleich ist, steht als u: Abstand von der Mitte der
# Y-Schiene nach innen (zur Maschinenmitte). X = s * (R - u), s = -1 links,
# +1 rechts, R = halber Schienenabstand.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'Portal'
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Portal: Kaufteile, Werte wie in ToolheadZ.py ----------------------
    'profil_laenge':      (500.0, 'Portalrohr 2020 V-Slot: Laenge'),
    'profil_b':            (20.0, 'Portalrohr: Kantenlaenge'),
    'x_schiene_laenge':   (450.0, 'X-Schiene MGN15: Laenge'),
    # Der Toolhead ragt rechts 44 mm (Mutternwinkel), links 27,5 mm
    # (Fahnenlasche) neben die Wagenmitte. Um 8,25 mm nach links versetzt
    # steht er an beiden Enden des X-Wegs gleich weit vom Y-Riemen weg.
    'x_schiene_versatz':   (8.25, 'X-Schiene: nach links versetzt'),
    'x_schiene_b':         (15.0, 'MGN15: Schienenbreite (in Z)'),
    'x_schiene_h':         (10.0, 'MGN15: Schienenhoehe'),
    'x_wagen_laenge':      (58.8, 'MGN15H: Wagenlaenge'),
    'x_wagen_breite':      (32.0, 'MGN15H: Wagenbreite (in Z)'),
    'x_wagen_hoehe':       (16.0, 'MGN15: Montagehoehe'),

    # --- Y-Achse: MGN12H auf 2040 hochkant ----------------------------------
    # 514 = kleinster Abstand, bei dem die ganze X-Schiene nutzbar bleibt:
    # am Ende des X-Wegs faehrt der Toolhead unten 3,35 mm am Y-Riemen
    # vorbei (docs/hardware-notizen.md). Das 500er-Rohr endet dann 7 mm vor
    # jeder Schienenmitte.
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    # Lochbild aus RiemenklemmeSchlitten v8 (.3mf), der auf dem Wagen sitzt [v]
    'y_wagen_loch':        (20.0, 'MGN12H: Lochbild 20 x 20'),
    'y_wagen_breite':      (27.0, 'MGN12H: Wagenbreite (in X)'),
    'y_wagen_laenge':      (45.4, 'MGN12H: Wagenlaenge (in Y)'),
    'y_wagen_hoehe':       (13.0, 'MGN12: Montagehoehe (Schienenfuss -> Wagen)'),
    'y_wagen_boden':        (3.0, 'MGN12: Luft unter dem Wagenkoerper'),
    'y_schiene_b':         (12.0, 'MGN12: Schienenbreite'),
    'y_schiene_h':          (8.0, 'MGN12: Schienenhoehe'),
    'y_gewinde_tiefe':      (3.5, 'MGN12H: M3-Gewindetiefe'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),

    # --- Y-Riemen: Lage wie in RiemenklemmeSchlitten v8 ---------------------
    # Der Riemen laeuft weiter wie bisher: Mitte 21,6 mm innen neben der
    # Schienenmitte, hochkant, Zaehne zur Schiene, Unterkante 28,9 mm unter
    # der Wagenoberseite. Ritzel und Umlenkungen am Rahmen bleiben.
    'y_riemen_linie':      (21.6, 'Y-Riemen: Mitte neben der Schienenmitte'),
    'y_riemen_tiefe':      (28.9, 'Y-Riemen: Unterkante unter der Wagenoberseite'),

    # --- GT2 (hardware.md) -------------------------------------------------
    'riemen_breite':        (6.0, 'GT2: Riemenbreite'),
    'riemen_dicke':        (1.38, 'GT2: Gesamtdicke'),
    'riemen_zahn_h':       (0.75, 'GT2: Zahnhoehe'),
    'riemen_pld':         (0.254, 'GT2: Wirklinie ueber dem Zahngrund'),
    'riemen_teilung':       (2.0, 'GT2: Teilung'),
    'ritzel_teilkreis':   (12.73, 'GT2 20 Z: Teilkreis = Abstand der Trume'),
    'ritzel_flansch_d':    (16.0, 'GT2 20 Z Ritzel: Flansch'),
    'ritzel_laenge':       (16.0, 'GT2 20 Z Ritzel: Gesamtlaenge'),
    'ritzel_bord':          (1.0, 'Ritzel: unterer Bord unter dem Riemen'),
    # Umlenkung: 20-Z-Rolle mit Kugellager, Bohrung 5 [w]. Aussendurchmesser
    # nicht gemessen — 18 ist die Huelle mit Bord [?].
    'rolle_d':             (18.0, 'Umlenkrolle 20 Z: Huelle (Bord)'),
    'rolle_breite':         (8.5, 'Umlenkrolle: Breite'),

    # --- X-Riemen: Lage wie in ToolheadZ.py (Riemenhalter) -----------------
    'x_riemen_y':         (-10.0, 'X-Riemen: Wirklinie des gezogenen Trums'),
    'x_riemen_z0':        (20.25, 'X-Riemen: Unterkante'),

    # --- Riemenklemmen: wie der Riemenhalter in ToolheadZ.py ----------------
    'klemm_schlitz':        (1.6, 'Riemenklemme: Rippengrund bis glatte Wand'),
    'klemm_rippe':          (0.8, 'Riemenklemme: Rippenhoehe'),
    'klemm_rippe_b':        (1.0, 'Riemenklemme: Rippenbreite'),
    'klemm_stift_d':        (3.2, 'Riemenklemme: Bohrung fuer den Stift'),

    # --- NEMA 17 fuer X (hardware.md [w]) -----------------------------------
    'motor_flansch':       (42.3, 'NEMA17: Flanschmass'),
    'motor_loch':          (31.0, 'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0, 'NEMA17: Zentrierbund'),
    'motor_welle_l':       (24.0, 'NEMA17: Wellenlaenge ab Flansch'),
    # Nicht gemessen: welcher Motor an X kommt. 48 ist der laengste
    # gaengige, fuer die Pruefung die sichere Seite [?].
    'motor_laenge':        (48.0, 'NEMA17: Koerperlaenge (nur Freigang)'),
    'motor_gewinde_tiefe':  (4.5, 'NEMA17: Gewindetiefe im Flansch'),

    # --- Normteile ---------------------------------------------------------
    'm3_durchgang':         (3.4, 'M3 Durchgang'),
    'm3_senkung':           (6.5, 'Senkung fuer M3-Zylinderkopf'),
    'm3_senkung_t':         (3.2, 'Senkung M3: Tiefe'),
    'm3_kopf_h':            (3.0, 'M3 Zylinderkopf: Hoehe'),
    'm3_mutter_sw':         (5.5, 'M3 Mutter: Schluesselweite'),
    'm3_mutter_h':          (2.4, 'M3 Mutter: Hoehe'),
    'tasche_spiel':        (0.15, 'Mutterntasche: Spiel'),
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'm5_senkung':           (9.5, 'Senkung fuer M5-Zylinderkopf'),
    'm5_mutter_sw':         (8.0, 'M5 Mutter: Schluesselweite'),
    'm5_mutter_h':          (4.7, 'M5 Mutter: Hoehe'),
    'm5_scheibe_h':         (1.0, 'M5 Scheibe: Dicke'),
    # Die vorhandenen Messingeinsaetze: 5 mm aussen [v], Einpressbohrung 4,6
    'insert_m3_d':          (4.6, 'Gewindeeinsatz M3: Einpressbohrung'),
    'insert_m3_t':          (7.0, 'Gewindeeinsatz M3: Sacklochtiefe'),
    # Tiefer fuer die langen Schrauben der Halter: die Laenge der Schraube
    # darf dann um 2 mm streuen, ohne aufzusetzen.
    'insert_tief_t':        (9.0, 'Gewindeeinsatz M3: tiefes Sackloch'),
    'inbus_frei_d':         (6.0, 'Werkzeugkorridor fuer den Inbus'),
    'kanal_spiel':          (0.2, 'Spannschieber: Spiel je Seite im Kanal'),
    'spiel_locker':         (0.4, 'Montagespiel, diametral'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
    'lehre_dicke':          (3.0, 'Bohrlehren: Plattendicke'),

    # --- Schlitten ---------------------------------------------------------
    'platte_dicke':         (6.0, 'Platte: Dicke (Rohr liegt direkt darauf)'),
    'platte_aussen':       (22.0, 'Platte: reicht so weit aussen neben die Schiene'),
    # 30: die Rueckwand braucht zwischen Rohrende und Plattenkante Platz
    # fuer zwei versenkte M5 (Ø9,5) — und die Kante liegt hinter dem Rohr,
    # wo der X-Wagen nicht hinkommt.
    'platte_innen':        (30.0, 'Platte: reicht so weit innen neben die Schiene'),
    'platte_luft_vorn':     (3.0, 'Platte endet so weit hinter der Rohrvorderseite'),
    # Wagen HINTER dem Rohr: dann bleiben alle vier Wagenschrauben von oben
    # erreichbar. Unter dem Rohr laegen zwei unter seinen Kanten, vor dem
    # Rohr unter dem X-Motor. Die Wagenmitte liegt so, dass die vordere
    # Reihe 1 mm neben der Rueckwand bleibt.
    'wagen_y':            (-60.0, 'Y-Wagen: Mitte (Y)'),
    'rueckwand_dicke':     (10.0, 'Rueckwand hinter dem Rohr: Dicke'),
    # Hammermutter ~10,5 lang: die erste steht ganz im Rohr
    'rueck_schraube_1':     (5.5, 'Rueckwand: 1. M5 so weit vom Rohrende'),
    'rueck_schraube_2':    (17.5, 'Rueckwand: 2. M5 so weit vom Rohrende'),
    'm5_senk_t':            (5.0, 'Rueckwand: M5-Kopf versenkt'),
    # Kernbohrung: M5 durch den Stirnblock; unter dem Kopf bleiben 12 mm
    'kern_steg':           (12.0, 'Stirnblock: Material unter dem M5-Kopf'),
    # Einsaetze im Stirnblock fuer Motor- bzw. Umlenkhalter (u, Y). Aussen
    # neben dem Motorflansch, damit die Koepfe neben dem Motor liegen.
    'halter_schraube_u':  (-18.5, 'Halterschrauben: u'),
    'halter_schraube_y1': (-41.0, 'Halterschrauben: Y hinten'),
    'halter_schraube_y2': (-34.5, 'Halterschrauben: Y vorn'),

    # --- Riemenblock und Spannschieber -------------------------------------
    'rb_u0':               (14.5, 'Riemenblock: Innenseite (zur Schiene)'),
    'rb_boden':             (5.6, 'Riemenblock: Boden unter dem Riemen'),
    'schieber_breite':      (7.5, 'Spannschieber: Breite'),
    'schieber_hoehe':      (15.2, 'Spannschieber: Hoehe'),
    'schieber_laenge':     (20.0, 'Spannschieber: Laenge'),
    'schieber_weg':        (14.0, 'Spannschieber: Verstellweg'),
    # 8 mm: die Mutter drueckt gegen die hintere Wand ihrer Tasche, dort
    # bleiben so 2,65 mm
    'anschlag_dicke':       (8.0, 'Riemenblock: Anschlag mit Mutter'),
    'riemen_luecke':        (4.0, 'Riemenblock: Platz fuers vordere Riemenende'),
    'druck_ueber_riemen':   (4.4, 'Druckschraube: Achse ueber der Riemenoberkante'),
    'rb_schraube_y1':     (-50.0, 'Riemenblock: Schraube vorn (Y)'),
    'rb_schraube_y2':     (-76.0, 'Riemenblock: Schraube hinten (Y)'),

    # --- Motorhalter (links) ------------------------------------------------
    # Motorachse ueber dem Rohrende: weiter innen stiesse der Flansch am
    # Ende des X-Wegs an die Traegerplatte (3 mm Luft, portal_check.py).
    'motor_u':              (7.0, 'X-Motor: Achse (u)'),
    'mp_dicke':             (8.0, 'Motorplatte: Dicke'),
    'ritzel_luft':          (0.5, 'Luft zwischen Ritzelnabe und Motorplatte'),
    'saeule_aussen_b':     (10.0, 'Motorhalter: aeussere Saeule, Breite'),

    # --- Umlenkhalter + Spannklotz (rechts) ---------------------------------
    'rolle_u':            (26.35, 'X-Umlenkrolle: Achse in Mittelstellung (u)'),
    'rolle_weg':            (4.0, 'X-Umlenkrolle: Spannweg je Richtung'),
    # M5 x 30 von oben: Kopf auf dem Spannklotz, Mutter im Schlitz der
    # unteren Platte. Die Plattendicken ergeben sich daraus.
    'uh_bolzen':           (30.0, 'Umlenkung: Laenge der M5-Achse'),
    'klotz_dicke':          (7.0, 'Spannklotz: Dicke'),
    'klotz_versatz':       (16.0, 'Spannklotz: Mutter so weit aussen neben der Achse'),
    'uh_lasche_b':          (5.0, 'Umlenkhalter: Lasche fuer die Zugschraube'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm); je Seite gleiche
    Masse als u (Abstand von der Y-Schienenmitte nach innen). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/portal_check.py)."""
    L = {}
    R = w('y_schienen_abstand') / 2.0
    L['R'] = R

    # ---- Portalrohr, X-Schiene, X-Weg ---------------------------------------
    L['portal_y'] = -w('x_wagen_hoehe')              # Rohrvorderseite
    L['profil_y0'] = L['portal_y'] - w('profil_b')   # Rohrrueckseite
    L['profil_z0'] = -w('profil_b') / 2.0
    L['profil_z1'] = w('profil_b') / 2.0
    L['profil_ende_u'] = R - w('profil_laenge') / 2.0
    L['kern_y'] = L['portal_y'] - w('profil_b') / 2.0     # Kernbohrung
    L['kern_z'] = 0.0
    L['x_schiene_y1'] = L['portal_y'] + w('x_schiene_h')
    L['x_schiene_x'] = (-w('x_schiene_laenge') / 2.0 - w('x_schiene_versatz'),
                        w('x_schiene_laenge') / 2.0 - w('x_schiene_versatz'))
    halb = w('x_schiene_laenge') / 2.0 - w('x_wagen_laenge') / 2.0
    L['xw_min'] = -halb - w('x_schiene_versatz')      # X-Wagenmitte links
    L['xw_max'] = halb - w('x_schiene_versatz')       # X-Wagenmitte rechts
    L['x_weg'] = 2.0 * halb

    # ---- Y-Fuehrung und Rahmen ----------------------------------------------
    L['platte_z1'] = L['profil_z0']                  # Rohr liegt auf der Platte
    L['platte_z0'] = L['platte_z1'] - w('platte_dicke')
    L['y_wagen_z1'] = L['platte_z0']
    L['y_schiene_z0'] = L['y_wagen_z1'] - w('y_wagen_hoehe')   # = 2040 oben
    L['y_schiene_z1'] = L['y_schiene_z0'] + w('y_schiene_h')
    L['y_wagen_z0'] = L['y_schiene_z0'] + w('y_wagen_boden')
    L['rahmen_z1'] = L['y_schiene_z0']
    L['rahmen_z0'] = L['rahmen_z1'] - w('rahmen_h')
    L['wagen_y0'] = w('wagen_y') - w('y_wagen_laenge') / 2.0
    L['wagen_y1'] = w('wagen_y') + w('y_wagen_laenge') / 2.0
    L['wagen_loecher'] = [(su * w('y_wagen_loch') / 2.0,
                           w('wagen_y') + sy * w('y_wagen_loch') / 2.0)
                          for su in (-1, 1) for sy in (-1, 1)]      # (u, Y)
    # Wagenschraube: unter dem Kopf der Rest der Platte, dann hoechstens die
    # Gewindetiefe des Wagens — abgerundet, laenger setzt sie auf.
    L['wagen_klemm'] = w('platte_dicke') - w('m3_senkung_t')
    L['wagen_schraube'] = 2.0 * int((L['wagen_klemm'] + w('y_gewinde_tiefe'))
                                    / 2.0)

    # ---- Y-Riemen -----------------------------------------------------------
    L['yr_z0'] = L['y_wagen_z1'] - w('y_riemen_tiefe')   # Unterkante
    L['yr_z1'] = L['yr_z0'] + w('riemen_breite')
    # Klemmschlitz: glatte Wand am Riemenruecken (von der Schiene weg), die
    # Rippen an der Seite zur Schiene; die Riemenmitte bleibt auf der Linie.
    L['yr_wand_u'] = w('y_riemen_linie') + w('riemen_dicke') / 2.0
    L['yr_rippe_u0'] = L['yr_wand_u'] - w('klemm_schlitz')      # Rippengrund
    L['yr_rippe_u1'] = L['yr_rippe_u0'] + w('klemm_rippe')      # Spitze
    L['yr_mitte_u'] = L['yr_wand_u'] - w('klemm_schlitz') / 2.0
    L['yr_decke_z'] = L['yr_z1'] + 0.5          # Decke des Klemmschlitzes

    # ---- Schlitten: Platte, Rueckwand, Stirnblock ---------------------------
    L['platte_u'] = (-w('platte_aussen'), w('platte_innen'))
    L['platte_y0'] = L['wagen_y0'] - 0.3
    L['platte_y1'] = L['portal_y'] - w('platte_luft_vorn')
    L['wand_z1'] = L['profil_z1']                 # Oberkante wie das Rohr
    L['rueck_y0'] = L['profil_y0'] - w('rueckwand_dicke')
    L['rueck_y1'] = L['profil_y0']
    L['rueck_u'] = (L['profil_ende_u'], L['platte_u'][1])
    L['stirn_u'] = (L['platte_u'][0], L['profil_ende_u'])
    L['stirn_y'] = (L['rueck_y0'], L['platte_y1'])
    L['rueck_schrauben_u'] = [L['profil_ende_u'] + w('rueck_schraube_1'),
                              L['profil_ende_u'] + w('rueck_schraube_2')]
    L['kern_senk_u'] = L['profil_ende_u'] - w('kern_steg')
    L['halter_schrauben'] = [(w('halter_schraube_u'), w('halter_schraube_y1')),
                             (w('halter_schraube_u'), w('halter_schraube_y2'))]
    # Rueckwand-Schraube: Wand unter dem Kopf, Nutstein-Lippe 1,8, Nutstein 4
    L['rueck_klemm'] = w('rueckwand_dicke') - w('m5_senk_t')
    L['rueck_schraube'] = 2.0 * int((L['rueck_klemm'] + 1.8 + 4.0) / 2.0
                                    + 0.999)
    # Kernbohrungs-Schraube: Steg des Stirnblocks + 10 mm Gewinde im Rohr
    L['kern_schraube'] = 5.0 * int((w('kern_steg') + 10.0) / 5.0 + 0.999)
    L['kern_gewinde'] = L['kern_schraube'] - w('kern_steg')

    # ---- Riemenblock: haengt neben dem Wagen unter der Platte ----------------
    L['rb_u'] = (w('rb_u0'), L['platte_u'][1])
    L['rb_y'] = (L['platte_y0'], L['platte_y1'])
    L['rb_z'] = (L['yr_z0'] - w('rb_boden'), L['platte_z0'])
    # Laengs von hinten: Kanal fuer den Spannschieber, Anschlag mit der
    # Mutter der Druckschraube, Luecke fuers Riemenende, feste Klemme vorn.
    y = L['rb_y'][0]
    L['kanal_y'] = (y, y + w('schieber_laenge') + w('schieber_weg'))
    L['anschlag_y'] = (L['kanal_y'][1], L['kanal_y'][1] + w('anschlag_dicke'))
    L['luecke_y'] = (L['anschlag_y'][1],
                     L['anschlag_y'][1] + w('riemen_luecke'))
    L['klemme_y'] = (L['luecke_y'][1], L['rb_y'][1])
    # Spannschieber mittig auf dem Klemmschlitz; Kanal mit Spiel drumherum.
    # Er steht auf dem Kanalboden, der Riemen darin auch.
    hb = w('schieber_breite') / 2.0
    L['sch_u'] = (L['yr_mitte_u'] - hb, L['yr_mitte_u'] + hb)
    L['sch_z'] = (L['yr_z0'], L['yr_z0'] + w('schieber_hoehe'))
    L['kanal_u'] = (L['sch_u'][0] - w('kanal_spiel'),
                    L['sch_u'][1] + w('kanal_spiel'))
    L['kanal_z'] = (L['sch_z'][0], L['sch_z'][1] + w('kanal_spiel'))
    L['druck_z'] = L['yr_z1'] + w('druck_ueber_riemen')
    L['stift_z'] = L['yr_z0'] - w('klemm_stift_d') / 2.0
    L['mutter_y'] = (L['anschlag_y'][0] + L['anschlag_y'][1]) / 2.0
    # Stellung im Modell: Mitte des Verstellwegs
    L['sch_y'] = (L['kanal_y'][0] + w('schieber_weg') / 2.0,
                  L['kanal_y'][0] + w('schieber_weg') / 2.0
                  + w('schieber_laenge'))
    # Druckschraube: Kopf hinten am Schieber. Ganz entspannt (Schieber
    # hinten) muss sie 0,5 mm durch die Mutter reichen; ganz gespannt ragt
    # die Spitze in die Klemme — ueber dem Riemen, dort ist eine Bohrung.
    reicht = (L['mutter_y'] + w('m3_mutter_h') / 2.0 + 0.5) - L['kanal_y'][0]
    L['druck_schraube'] = 5.0 * int(reicht / 5.0 + 0.999)
    L['druck_spitze_max'] = (L['kanal_y'][1] - w('schieber_laenge')
                             + L['druck_schraube'])
    # Schraube Platte -> Riemenblock: Platte unter der Senkung, dann
    # mindestens 5 mm im Einsatz, ohne im Sackloch aufzusetzen
    L['rb_schraube'] = 2.0 * int((L['wagen_klemm'] + 5.0) / 2.0 + 0.999)
    L['rb_eingriff'] = L['rb_schraube'] - L['wagen_klemm']
    L['rb_schrauben'] = [((L['rb_u'][0] + L['rb_u'][1]) / 2.0,
                          w('rb_schraube_y1')),
                         ((L['rb_u'][0] + L['rb_u'][1]) / 2.0,
                          w('rb_schraube_y2'))]
    # Rippen: Teilung 2, in der festen Klemme und im Schieber
    def rippen(y0, y1):
        n = int((y1 - y0 - w('klemm_rippe_b')) / w('riemen_teilung')) + 1
        rand = (y1 - y0 - (n - 1) * w('riemen_teilung')
                - w('klemm_rippe_b')) / 2.0
        return [y0 + rand + i * w('riemen_teilung') for i in range(n)]
    L['rb_rippen_y'] = rippen(L['klemme_y'][0] + 1.0, L['klemme_y'][1] - 1.0)
    L['sch_rippen_y'] = rippen(L['sch_y'][0] + 1.0, L['sch_y'][1] - 1.0)
    # Ruecklauf-Trum: laeuft in der oberen Nut des 2040, auf der Seite zur
    # Schiene — Ritzel mit senkrechter Achse an beiden Enden, Abstand der
    # Trume = Teilkreis. Die Zaehne zeigen damit zur Schiene (Innenseite der
    # Schleife), deshalb stehen die Rippen der Klemmen auf der Schienenseite.
    L['yr_rueck_u'] = w('y_riemen_linie') - w('ritzel_teilkreis')
    L['rahmen_flanke_u'] = w('rahmen_b') / 2.0

    # ---- X-Riemen -------------------------------------------------------------
    L['xr_y'] = w('x_riemen_y')                            # gezogener Trum
    L['xr_y_rueck'] = w('x_riemen_y') - w('ritzel_teilkreis')   # Ruecklauf
    L['xr_yc'] = w('x_riemen_y') - w('ritzel_teilkreis') / 2.0  # Ritzelachsen
    L['xr_z0'] = w('x_riemen_z0')
    L['xr_z1'] = L['xr_z0'] + w('riemen_breite')
    L['xr_zm'] = (L['xr_z0'] + L['xr_z1']) / 2.0
    # Koerper des Riemens um die Wirklinie: Ruecken aussen, Zaehne innen
    steg = w('riemen_dicke') - w('riemen_zahn_h')
    L['riemen_aussen'] = steg - w('riemen_pld')              # Wirklinie->Ruecken
    L['riemen_innen'] = w('riemen_pld') + w('riemen_zahn_h')  # ->Zahnspitze

    # ---- Motorhalter (links) --------------------------------------------------
    fl = w('motor_flansch') / 2.0
    # Ritzel mit der Nabe nach oben: unterer Bord knapp unter dem Riemen
    L['ritzel_z0'] = L['xr_z0'] - w('ritzel_bord')
    L['ritzel_z1'] = L['ritzel_z0'] + w('ritzel_laenge')
    L['mp_z0'] = L['ritzel_z1'] + w('ritzel_luft')
    L['mp_z1'] = L['mp_z0'] + w('mp_dicke')
    L['motor_z1'] = L['mp_z1'] + w('motor_laenge')
    L['welle_z0'] = L['mp_z1'] - w('motor_welle_l')
    L['motor_schrauben'] = [(w('motor_u') + su * w('motor_loch') / 2.0,
                             L['xr_yc'] + sy * w('motor_loch') / 2.0)
                            for su in (-1, 1) for sy in (-1, 1)]     # (u, Y)
    L['mp_u'] = (L['platte_u'][0], w('motor_u') + fl)
    L['mp_y'] = (L['rueck_y0'], L['xr_yc'] + fl)
    # Saeulen unter der Motorplatte: hinten hinter den hinteren, aussen neben
    # den aeusseren Motorschrauben — alle vier bleiben von unten erreichbar.
    frei = w('motor_loch') / 2.0 + w('inbus_frei_d') / 2.0
    L['mh_hinten_y'] = (L['rueck_y0'], L['xr_yc'] - frei)
    L['mh_hinten_u'] = (L['platte_u'][0], min(L['rueck_u'][1], L['mp_u'][1]))
    L['mh_aussen_u'] = (L['platte_u'][0],
                        L['platte_u'][0] + w('saeule_aussen_b'))
    L['mh_z'] = (L['wand_z1'], L['mp_z0'])
    # Motorschrauben: Platte + Gewinde im Flansch (hoechstens die Tiefe)
    L['motor_schraube'] = 2.0 * int((w('mp_dicke') + w('motor_gewinde_tiefe'))
                                    / 2.0)
    # Halterschrauben von oben durch Platte und Saeule in den Stirnblock
    L['mh_klemm'] = L['mp_z1'] - L['wand_z1']
    L['mh_schraube'] = 5.0 * int((L['mh_klemm'] + 5.0) / 5.0 + 0.999)

    # ---- Umlenkhalter (rechts) -----------------------------------------------
    L['rolle_u'] = (w('rolle_u') - w('rolle_weg'), w('rolle_u') + w('rolle_weg'))
    L['rolle_z0'] = L['xr_zm'] - w('rolle_breite') / 2.0
    L['rolle_z1'] = L['xr_zm'] + w('rolle_breite') / 2.0
    # Stapel auf der M5 von unten: Mutter im Schlitz der unteren Platte,
    # Platte, Scheibe, Rolle, Scheibe, obere Platte, Spannklotz, Scheibe, Kopf
    L['uh_unten_z'] = (L['wand_z1'], L['rolle_z0'] - w('m5_scheibe_h'))
    L['uh_mutter_z'] = (L['uh_unten_z'][0],
                        L['uh_unten_z'][0] + w('m5_mutter_h') + 0.3)
    L['uh_spitze_z'] = L['uh_mutter_z'][1] - w('m5_mutter_h') + 0.7
    L['klotz_z'] = (L['uh_spitze_z'] + w('uh_bolzen') - w('m5_scheibe_h')
                    - w('klotz_dicke'),
                    L['uh_spitze_z'] + w('uh_bolzen') - w('m5_scheibe_h'))
    L['uh_oben_z'] = (L['rolle_z1'] + w('m5_scheibe_h'), L['klotz_z'][0])
    L['uh_kopf_z1'] = L['klotz_z'][1] + w('m5_scheibe_h') + w('m5_kopf_h')
    L['uh_zug_z'] = (L['klotz_z'][0] + L['klotz_z'][1]) / 2.0   # Zugschraube
    # Platten: vorn und hinten 3 mm um die Rolle; innen so weit, dass die
    # untere am Ende des X-Wegs 3 mm neben dem X-Wagen bleibt.
    L['uh_y'] = (L['xr_yc'] - w('rolle_d') / 2.0 - 3.0,
                 L['xr_yc'] + w('rolle_d') / 2.0 + 3.0)
    L['uh_innen_u'] = R - (L['x_schiene_x'][1] + w('luft_bau'))
    L['uh_steg_u1'] = L['rolle_u'][0] - w('rolle_d') / 2.0 - 3.0
    # Saeule hinten: traegt beide Platten, steht auf Stirnblock und Rueckwand
    L['uh_saeule_y'] = (L['rueck_y0'], L['uh_y'][0])
    L['uh_saeule_u'] = (L['platte_u'][0], L['rueck_u'][1])
    # Spannklotz: Bohrung fuer die M5 innen, Mutter der Zugschraube
    # klotz_versatz weiter aussen. Die Zugschraube zieht ihn nach aussen.
    L['klotz_u_rel'] = (-w('klotz_versatz') - (w('m3_mutter_h') + 0.3) / 2.0
                        - 2.0,
                        w('m5_durchgang') / 2.0 + 3.0)
    L['klotz_y'] = (L['xr_yc'] - 6.0, L['xr_yc'] + 6.0)
    # Lasche aussen: der Klotz kommt ganz gespannt bis 0,5 mm heran
    L['uh_lasche_u'] = (L['rolle_u'][0] + L['klotz_u_rel'][0] - 0.5
                        - w('uh_lasche_b'),
                        L['rolle_u'][0] + L['klotz_u_rel'][0] - 0.5)
    L['uh_oben_u'] = (L['uh_lasche_u'][0], L['uh_innen_u'])
    # Zugschraube: Kopf aussen an der Lasche. Die Spitze muss ganz entspannt
    # durch die Mutter reichen und darf ganz gespannt die M5 nicht erreichen.
    spitze_min = (L['rolle_u'][1] - w('klotz_versatz')
                  + (w('m3_mutter_h') + 0.3) / 2.0)
    spitze_max = L['rolle_u'][0] - w('m5_durchgang') / 2.0 - 1.0
    L['zug_spitze'] = (spitze_min, spitze_max)
    L['zug_schraube'] = 2.0 * int((spitze_max - L['uh_lasche_u'][0]) / 2.0)
    L['zug_spitze_ist'] = L['uh_lasche_u'][0] + L['zug_schraube']
    L['uh_klemm'] = L['uh_oben_z'][1] - L['wand_z1']
    L['uh_schraube'] = 5.0 * int((L['uh_klemm'] + 5.0) / 5.0 + 0.999)

    # ---- X-Riemen: Laenge ueber Motor, Umlenkung (Mitte) und Halter -----------
    x_m = -(R - w('motor_u'))
    x_u = R - w('rolle_u')
    L['x_motor'] = x_m
    L['x_rolle'] = x_u
    L['x_rolle_bereich'] = (R - L['rolle_u'][1], R - L['rolle_u'][0])
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

ZIELDICHTE = {'PLA': 1.24, 'PETG': 1.27}        # g/cm3
# Kandidaten fuer das Basismaterial, aus dem kopiert wird (Reihenfolge = Vorzug)
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


def xs(L, s, u):
    """Maschinen-X aus u (Abstand von der Y-Schienenmitte nach innen)."""
    return s * (L['R'] - u)


def xb(L, s, u0, u1):
    """X-Bereich (klein, gross) zu einem u-Bereich."""
    a, b = xs(L, s, u0), xs(L, s, u1)
    return (min(a, b), max(a, b))


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


def rippen(comp, name, rechtecke, z0, z1, ziel):
    """Klemmrippen: Rechtecke in X/Y, ueber z0..z1 an den Koerper gefuegt."""
    zm = (z0 + z1) / 2.0
    sk = skizze(comp, _ebene(comp, 'z', zm, 'E_{}_Z{:.1f}'.format(
        comp.name, zm)), 'Sk_' + name)
    for xa, ya, xe, ye in rechtecke:
        rechteck(sk, xa, ya, xe, ye)
    dazu_mittig(comp, alle_profile(sk), abs(z1 - z0), ziel)


def langloch_x(sk, xa, xe, y, breite):
    """Waagerechtes Langloch laengs X auf einer Z-Ebene: zwei Kreise plus
    Rechteck; beim Schneiden aller Profile ergibt die Vereinigung das Loch."""
    r = breite / 2.0
    kreis(sk, xa, y, breite)
    kreis(sk, xe, y, breite)
    rechteck(sk, min(xa, xe), y - r, max(xa, xe), y + r)


def seite(s):
    return 'links' if s < 0 else 'rechts'


# --- Bauteile ------------------------------------------------------------------
def bau_schlitten(app, design, comp, L, s, fehler):
    """Platte auf dem MGN12H-Wagen, Rueckwand und Stirnblock fuer das Rohr.

    Das Rohr liegt direkt auf der Platte (Portalhoehe wie bisher), die
    Rueckwand zieht es mit 2x M5 in Nutensteinen an sich, der Stirnblock
    haelt das Ende mit einer M5 in der Kernbohrung. Die Vorderseite des
    Rohrs bleibt frei: dort sitzt die X-Schiene, die bei 450 mm auf 500 mm
    Rohr an den Enden keinen Platz fuer Laschen laesst.

    Der Wagen sitzt HINTER dem Rohr, damit alle vier Wagenschrauben von
    oben erreichbar bleiben. Die Platte endet 3 mm hinter der Rohrvorder-
    seite: am Ende des X-Wegs faehrt dort der X-Wagen vorbei.

    Drucklage: Unterseite aufs Bett, Rueckwand und Stirnblock stehen senk-
    recht darauf. Alle Senkungen oeffnen nach oben oder zur Seite."""
    n = seite(s)
    xu = lambda u: xs(L, s, u)
    x_platte = xb(L, s, *L['platte_u'])
    k = quader(comp, 'Platte_' + n, x_platte,
               (L['platte_y0'], L['platte_y1']),
               (L['platte_z0'], L['platte_z1']), 'neu').bodies.item(0)
    k.name = 'Schlitten_' + n
    quader(comp, 'Rueckwand_' + n, xb(L, s, *L['rueck_u']),
           (L['rueck_y0'], L['rueck_y1']), (L['platte_z1'], L['wand_z1']),
           'dazu', k)
    quader(comp, 'Stirnblock_' + n, xb(L, s, *L['stirn_u']), L['stirn_y'],
           (L['platte_z1'], L['wand_z1']), 'dazu', k)

    # Wagenschrauben und Schrauben des Riemenblocks: Durchgang + Senkung
    # von oben, der Kopf verschwindet in der Platte.
    for name, lagen in (('Wagen', L['wagen_loecher']),
                        ('Riemenblock', L['rb_schrauben'])):
        pkt = [(xu(u), y) for u, y in lagen]
        bohrung(comp, name + '_' + n, 'z', pkt, w('m3_durchgang'),
                L['platte_z0'] - 1.0, L['platte_z1'] + 1.0, k)
        bohrung(comp, name + '_Senkung_' + n, 'z', pkt, w('m3_senkung'),
                L['platte_z1'] - w('m3_senkung_t'), L['platte_z1'] + 1.0, k)

    # Rueckwand: 2x M5 nach vorn in die Nutensteine der hinteren Nut, Kopf
    # versenkt — er steht sonst in den Zugangskorridoren der Wagenschrauben.
    pkt = [(xu(u), L['kern_z']) for u in L['rueck_schrauben_u']]
    bohrung(comp, 'Rueckwand_M5_' + n, 'y', pkt, w('m5_durchgang'),
            L['rueck_y0'] - 1.0, L['rueck_y1'] + 1.0, k)
    bohrung(comp, 'Rueckwand_Senkung_' + n, 'y', pkt, w('m5_senkung'),
            L['rueck_y0'] - 1.0, L['rueck_y0'] + w('m5_senk_t'), k)

    # Stirnblock: M5 laengs in die Kernbohrung des Rohrs, Kopf versenkt
    pkt = [(L['kern_y'], L['kern_z'])]
    bohrung(comp, 'Kern_' + n, 'x', pkt, w('m5_durchgang'),
            xu(L['stirn_u'][0] - 1.0), xu(L['stirn_u'][1] + 1.0), k)
    bohrung(comp, 'Kern_Senkung_' + n, 'x', pkt, w('m5_senkung'),
            xu(L['stirn_u'][0] - 1.0), xu(L['kern_senk_u']), k)

    # Einsaetze fuer Motor- bzw. Umlenkhalter, von oben in den Stirnblock
    pkt = [(xu(u), y) for u, y in L['halter_schrauben']]
    bohrung(comp, 'Halter_Einsatz_' + n, 'z', pkt, w('insert_m3_d'),
            L['wand_z1'] - w('insert_tief_t'), L['wand_z1'] + 1.0, k)

    fussfase(comp, k, 'y', L['platte_z0'], w('fase_fuss'), fehler,
             'Schlitten ' + n)
    bbox_pruefen(k, 'Schlitten ' + n,
                 (x_platte, (L['platte_y0'], L['platte_y1']),
                  (L['platte_z0'], L['wand_z1'])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_riemenblock(app, design, comp, L, s, fehler):
    """Haengt unter der Platte neben dem Wagen und haelt beide Enden des
    Y-Riemens auf der Linie von v8 (hochkant, Zaehne zur Schiene).

    Von hinten nach vorn: Kanal fuer den Spannschieber (hinten offen, dort
    kommt das hintere Riemenende herein), Anschlag mit der Mutter der
    Druckschraube, Luecke fuers vordere Riemenende, feste Klemme vorn.
    Die feste Klemme ist unten offen: Riemen von unten eindruecken, dann
    einen Stift Ø3 von vorn unter ihm durchschieben.

    Die Mutter wird von oben in ihre Tasche gelegt, bevor der Block an die
    Platte kommt — die Platte haelt sie dann.

    Drucklage: auf der Rueckseite stehend. Kanal und Stiftbohrung laufen
    senkrecht, die Rippen werden zu waagerechten Stegen (1 mm = 5 Lagen)."""
    n = seite(s)
    xu = lambda u: xs(L, s, u)
    x_block = xb(L, s, *L['rb_u'])
    k = quader(comp, 'Riemenblock_' + n, x_block, L['rb_y'], L['rb_z'],
               'neu').bodies.item(0)
    k.name = 'Riemenblock_' + n

    # Kanal fuer den Spannschieber, hinten offen
    quader(comp, 'Kanal_' + n, xb(L, s, *L['kanal_u']),
           (L['kanal_y'][0] - 1.0, L['kanal_y'][1]), L['kanal_z'], 'weg', k)
    # Klemmschlitz der festen Klemme samt Luecke, unten offen
    quader(comp, 'Klemmschlitz_' + n, xb(L, s, L['yr_rippe_u0'],
                                          L['yr_wand_u']),
           (L['luecke_y'][0], L['rb_y'][1] + 1.0),
           (L['rb_z'][0] - 1.0, L['yr_decke_z']), 'weg', k)
    xr = xb(L, s, L['yr_rippe_u0'], L['yr_rippe_u1'])
    rippen(comp, 'Rippen_' + n,
           [(xr[0], y, xr[1], y + w('klemm_rippe_b'))
            for y in L['rb_rippen_y']],
           L['rb_z'][0], L['yr_decke_z'], k)
    # Stift unter dem Riemen, von vorn eingeschoben
    bohrung(comp, 'Stift_' + n, 'y', [(xu(L['yr_mitte_u']), L['stift_z'])],
            w('klemm_stift_d'), L['klemme_y'][0], L['rb_y'][1] + 1.0, k)
    # Druckschraube: durch den Anschlag und frei weiter bis vorn (die
    # Spitze ragt ganz gespannt in die Klemme, ueber dem Riemen)
    bohrung(comp, 'Druckschraube_' + n, 'y',
            [(xu(L['yr_mitte_u']), L['druck_z'])], w('m3_durchgang'),
            L['anschlag_y'][0] - 1.0, L['rb_y'][1] + 1.0, k)
    # Mutterntasche im Anschlag, von oben; Mutter liegt auf einer Flanke
    ueber_eck = (w('m3_mutter_sw') / math.cos(math.radians(30.0))
                 + w('tasche_spiel'))
    dick = w('m3_mutter_h') + 0.3
    quader(comp, 'Mutter_' + n,
           xb(L, s, L['yr_mitte_u'] - ueber_eck / 2.0,
              L['yr_mitte_u'] + ueber_eck / 2.0),
           (L['mutter_y'] - dick / 2.0, L['mutter_y'] + dick / 2.0),
           (L['druck_z'] - (w('m3_mutter_sw') + w('tasche_spiel')) / 2.0,
            L['rb_z'][1] + 1.0), 'weg', k)
    # Gewindeeinsaetze fuer die Schrauben von der Platte, von oben
    bohrung(comp, 'RB_Einsatz_' + n, 'z',
            [(xu(u), y) for u, y in L['rb_schrauben']], w('insert_m3_d'),
            L['rb_z'][1] - w('insert_m3_t'), L['rb_z'][1] + 1.0, k)

    fussfase(comp, k, 'z', L['rb_y'][0], w('fase_fuss'), fehler,
             'Riemenblock ' + n)
    bbox_pruefen(k, 'Riemenblock ' + n, (x_block, L['rb_y'], L['rb_z']),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_spannschieber(app, design, comp, L, s, fehler):
    """Haelt das hintere Ende des Y-Riemens im Kanal des Riemenblocks.
    Riemen von unten in den Schlitz druecken (Zaehne zu den Rippen), dann
    den Schieber von hinten in den Kanal schieben — der Kanalboden haelt
    den Riemen unten. Die Druckschraube (Kopf hinten) geht durch den
    Schieber in die Mutter im Anschlag: eindrehen schiebt ihn nach vorn
    und spannt. Gezeichnet in der Mitte seines Wegs.

    Drucklage: auf der Rueckseite stehend (Rippen als waagerechte Stege)."""
    n = seite(s)
    xu = lambda u: xs(L, s, u)
    x_sch = xb(L, s, *L['sch_u'])
    k = quader(comp, 'Spannschieber_' + n, x_sch, L['sch_y'], L['sch_z'],
               'neu').bodies.item(0)
    k.name = 'Spannschieber_' + n
    quader(comp, 'Schieber_Schlitz_' + n,
           xb(L, s, L['yr_rippe_u0'], L['yr_wand_u']),
           (L['sch_y'][0] - 1.0, L['sch_y'][1] + 1.0),
           (L['sch_z'][0] - 1.0, L['yr_decke_z']), 'weg', k)
    xr = xb(L, s, L['yr_rippe_u0'], L['yr_rippe_u1'])
    rippen(comp, 'Schieber_Rippen_' + n,
           [(xr[0], y, xr[1], y + w('klemm_rippe_b'))
            for y in L['sch_rippen_y']],
           L['sch_z'][0], L['yr_decke_z'], k)
    bohrung(comp, 'Schieber_Schraube_' + n, 'y',
            [(xu(L['yr_mitte_u']), L['druck_z'])], w('m3_durchgang'),
            L['sch_y'][0] - 1.0, L['sch_y'][1] + 1.0, k)
    fussfase(comp, k, 'z', L['sch_y'][0], w('fase_fuss'), fehler,
             'Spannschieber ' + n)
    bbox_pruefen(k, 'Spannschieber ' + n, (x_sch, L['sch_y'], L['sch_z']),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_motorhalter(app, design, comp, L, fehler):
    """X-Motor stehend ueber dem linken Rohrende, Welle nach unten. Das
    Ritzel sitzt mit der Nabe nach oben, seine Spur in Riemenhoehe.

    Die Motorplatte ruht auf zwei Saeulen: hinten hinter den hinteren
    Motorschrauben, aussen neben den aeusseren. So bleiben alle vier
    Schrauben von unten erreichbar, und die Platte ist an zwei Kanten
    gehalten — der Riemenzug greift unter ihr am Ritzel an und wuerde eine
    nur hinten gehaltene Platte verdrillen. Befestigt mit 2x M3 von oben
    in die Einsaetze des Stirnblocks; die Koepfe liegen neben dem Flansch.

    Drucklage: Motorplatte (Oberseite) aufs Bett, die Saeulen wachsen nach
    oben — keine Stuetzen."""
    s = -1
    xu = lambda u: xs(L, s, u)
    x_platte = xb(L, s, *L['mp_u'])
    k = quader(comp, 'Motorplatte', x_platte, L['mp_y'],
               (L['mp_z0'], L['mp_z1']), 'neu').bodies.item(0)
    k.name = 'Motorhalter'
    quader(comp, 'Saeule_hinten', xb(L, s, *L['mh_hinten_u']),
           L['mh_hinten_y'], L['mh_z'], 'dazu', k)
    quader(comp, 'Saeule_aussen', xb(L, s, *L['mh_aussen_u']),
           (L['mh_hinten_y'][1], L['mp_y'][1]), L['mh_z'], 'dazu', k)
    # Motor: Zentrierbund und vier Schrauben von unten
    bohrung(comp, 'Motor_Bund', 'z', [(xu(w('motor_u')), L['xr_yc'])],
            w('motor_bund_d') + w('spiel_locker'),
            L['mp_z0'] - 1.0, L['mp_z1'] + 1.0, k)
    bohrung(comp, 'Motor_Schrauben', 'z',
            [(xu(u), y) for u, y in L['motor_schrauben']],
            w('m3_durchgang'), L['mp_z0'] - 1.0, L['mp_z1'] + 1.0, k)
    # Halterschrauben: von oben durch Platte und Saeule in den Stirnblock
    bohrung(comp, 'Motorhalter_Schrauben', 'z',
            [(xu(u), y) for u, y in L['halter_schrauben']],
            w('m3_durchgang'), L['mh_z'][0] - 1.0, L['mp_z1'] + 1.0, k)
    fussfase(comp, k, 'y', L['mp_z1'], w('fase_fuss'), fehler, 'Motorhalter')
    bbox_pruefen(k, 'Motorhalter',
                 (x_platte, L['mp_y'], (L['mh_z'][0], L['mp_z1'])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_umlenkhalter(app, design, comp, L, fehler):
    """X-Umlenkung rechts: 20-Z-Rolle mit Lager auf einer M5 zwischen zwei
    Platten, die M5 laeuft in Langloechern. Die Mutter liegt im Schlitz
    unter der unteren Platte und dreht nicht mit.

    Spannen: auf der oberen Platte sitzt der Spannklotz (eigenes Teil) auf
    der M5; eine M3 von aussen durch die Lasche zieht ihn nach aussen. Erst
    ziehen, dann die M5 festziehen — sie haelt, die M3 stellt nur ein.

    Die untere Platte liegt auf Rohr und Stirnblock; innen endet sie 3 mm
    vor dem X-Wagen am Ende des X-Wegs. Befestigt wie der Motorhalter mit
    2x M3 von oben in den Stirnblock.

    Drucklage: auf der Rueckseite (Saeule) stehend; beide Platten stehen
    senkrecht, Langloecher und Mutternschlitz werden kurze Bruecken."""
    s = +1
    xu = lambda u: xs(L, s, u)
    k = quader(comp, 'UH_Saeule', xb(L, s, *L['uh_saeule_u']),
               L['uh_saeule_y'], (L['wand_z1'], L['uh_oben_z'][1]),
               'neu').bodies.item(0)
    k.name = 'Umlenkhalter'
    quader(comp, 'UH_oben', xb(L, s, *L['uh_oben_u']), L['uh_y'],
           L['uh_oben_z'], 'dazu', k)
    quader(comp, 'UH_unten', xb(L, s, L['uh_oben_u'][0], L['uh_innen_u']),
           L['uh_y'], L['uh_unten_z'], 'dazu', k)
    quader(comp, 'UH_Steg', xb(L, s, L['uh_oben_u'][0], L['uh_steg_u1']),
           L['uh_y'], (L['uh_unten_z'][1], L['uh_oben_z'][0]), 'dazu', k)
    quader(comp, 'UH_Lasche', xb(L, s, *L['uh_lasche_u']), L['klotz_y'],
           (L['uh_oben_z'][1], L['klotz_z'][1]), 'dazu', k)

    # Langloecher fuer die M5 durch beide Platten
    z0, z1 = L['uh_unten_z'][0] - 1.0, L['uh_oben_z'][1] + 1.0
    zm = (z0 + z1) / 2.0
    sk = skizze(comp, _ebene(comp, 'z', zm, 'E_UH_Langloch'), 'Sk_UH_Langloch')
    langloch_x(sk, xu(L['rolle_u'][0]), xu(L['rolle_u'][1]), L['xr_yc'],
               w('m5_durchgang'))
    tasche(comp, alle_profile(sk), z1 - z0, k)
    # Mutternschlitz von unten: die M5-Mutter gleitet mit, dreht nicht
    ueber_eck = w('m5_mutter_sw') / math.cos(math.radians(30.0))
    quader(comp, 'UH_Mutternschlitz',
           xb(L, s, L['rolle_u'][0] - ueber_eck / 2.0 - 0.2,
              L['rolle_u'][1] + ueber_eck / 2.0 + 0.2),
           (L['xr_yc'] - (w('m5_mutter_sw') + 0.2) / 2.0,
            L['xr_yc'] + (w('m5_mutter_sw') + 0.2) / 2.0),
           (L['uh_mutter_z'][0] - 1.0, L['uh_mutter_z'][1]), 'weg', k)
    # Zugschraube durch die Lasche
    bohrung(comp, 'UH_Zugschraube', 'x', [(L['xr_yc'], L['uh_zug_z'])],
            w('m3_durchgang'), xu(L['uh_lasche_u'][0] - 1.0),
            xu(L['uh_lasche_u'][1] + 1.0), k)
    # Halterschrauben von oben durch die Saeule in den Stirnblock
    bohrung(comp, 'UH_Schrauben', 'z',
            [(xu(u), y) for u, y in L['halter_schrauben']],
            w('m3_durchgang'), L['wand_z1'] - 1.0, L['uh_oben_z'][1] + 1.0,
            k)
    fussfase(comp, k, 'z', L['uh_saeule_y'][0], w('fase_fuss'), fehler,
             'Umlenkhalter')
    bbox_pruefen(k, 'Umlenkhalter',
                 (xb(L, s, L['uh_saeule_u'][0], L['uh_innen_u']),
                  (L['uh_saeule_y'][0], L['uh_y'][1]),
                  (L['wand_z1'], L['klotz_z'][1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_spannklotz(app, design, comp, L, fehler):
    """Sitzt auf der oberen Platte des Umlenkhalters auf der M5. Innen die
    Bohrung fuer die M5, aussen (klotz_versatz weiter) die Mutter der
    Zugschraube, von oben eingelegt, auf einer Flanke liegend. Die Zug-
    schraube kommt aus der Lasche, ihre Spitze bleibt ganz gespannt 1 mm vor
    der M5. Gezeichnet in der Mitte des Spannwegs.

    Drucklage: Unterseite aufs Bett."""
    s = +1
    xu = lambda u: xs(L, s, u)
    u_i = w('rolle_u')
    ku = (u_i + L['klotz_u_rel'][0], u_i + L['klotz_u_rel'][1])
    x_klotz = xb(L, s, *ku)
    k = quader(comp, 'Spannklotz', x_klotz, L['klotz_y'], L['klotz_z'],
               'neu').bodies.item(0)
    k.name = 'Spannklotz'
    bohrung(comp, 'Klotz_M5', 'z', [(xu(u_i), L['xr_yc'])],
            w('m5_durchgang'), L['klotz_z'][0] - 1.0, L['klotz_z'][1] + 1.0,
            k)
    bohrung(comp, 'Klotz_M3', 'x', [(L['xr_yc'], L['uh_zug_z'])],
            w('m3_durchgang'), xu(ku[0] - 1.0),
            xu(u_i - w('m5_durchgang') / 2.0 - 1.5), k)
    u_m = u_i - w('klotz_versatz')
    ueber_eck = (w('m3_mutter_sw') / math.cos(math.radians(30.0))
                 + w('tasche_spiel'))
    dick = w('m3_mutter_h') + 0.3
    quader(comp, 'Klotz_Mutter', xb(L, s, u_m - dick / 2.0, u_m + dick / 2.0),
           (L['xr_yc'] - ueber_eck / 2.0, L['xr_yc'] + ueber_eck / 2.0),
           (L['uh_zug_z'] - (w('m3_mutter_sw') + w('tasche_spiel')) / 2.0,
            L['klotz_z'][1] + 1.0), 'weg', k)
    fussfase(comp, k, 'y', L['klotz_z'][0], w('fase_fuss'), fehler,
             'Spannklotz')
    bbox_pruefen(k, 'Spannklotz', (x_klotz, L['klotz_y'], L['klotz_z']),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_bohrlehren(app, design, comp, L, fehler):
    """Bohrlehre fuer das Lochbild des Y-Wagens (MGN12H, 20 x 20) — zum
    Aufstecken auf den Wagen, bevor die Schlitten gedruckt werden. Liegt
    abseits hinter der Maschine, ausgeblendet (Konvention SKILL.md).

    Weitere Lehren gibt es bewusst nicht: alle anderen Verbindungen liegen
    zwischen Teilen dieses Skripts und haengen an denselben Variablen
    (dieselbe Begruendung wie in ToolheadZ.py)."""
    y0, z = -160.0, L['platte_z0'] - 20.0
    sk = skizze(comp, ebene_z(comp, z, 'E_Bohrlehre_YWagen'),
                'Sk_Bohrlehre_YWagen')
    halb = w('y_wagen_loch') / 2.0
    pkt = [(su * halb, y0 + sy * halb) for su in (-1, 1) for sy in (-1, 1)]
    for x, y in pkt:
        kreis(sk, x, y, w('m3_durchgang'))
    rand = 8.0
    rechteck(sk, -halb - rand, y0 - halb - rand, halb + rand, y0 + halb + rand)
    lehre = neu_mittig(comp, groesstes_profil(sk),
                       w('lehre_dicke')).bodies.item(0)
    lehre.name = 'Bohrlehre_YWagen'
    material_zuweisen(app, design, lehre, 'PLA', fehler)
    lehre.isLightBulbOn = False


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/portal_check.py)."""
    R = L['R']
    riemen_x = (2.0 * (L['x_rolle'] - L['x_motor'])
                + math.pi * w('ritzel_teilkreis'))
    h = [
        'BEZUG: Maschinenkoordinaten wie ToolheadZ.py (Y nach vorn, Z',
        '  senkrecht, Y=0 an der Stirnflaeche des X-Wagens, Z=0 in der Mitte',
        '  des Portalrohrs). X=0 ist hier die MITTE DES PORTALROHRS.',
        '  Im Modell sind Y und Z getauscht (Modell-Z = Maschine Y).',
        '',
        'PORTAL:',
        '  Y-Schienen {:.0f} mm Mitte zu Mitte (X = +-{:.1f}), Rohr {:.0f} mm,'
        .format(w('y_schienen_abstand'), R, w('profil_laenge')),
        '  es endet {:.1f} mm vor jeder Schienenmitte.'.format(
            L['profil_ende_u']),
        '  X-Schiene {:.0f} mm, {:.2f} mm nach LINKS versetzt: X {:+.2f} bis'
        .format(w('x_schiene_laenge'), w('x_schiene_versatz'),
                L['x_schiene_x'][0]),
        '  {:+.2f}. X-Wagenmitte {:+.2f} bis {:+.2f} = {:.1f} mm X-Weg.'.format(
            L['x_schiene_x'][1], L['xw_min'], L['xw_max'], L['x_weg']),
        '  Das Rohr liegt wie bisher direkt auf der 6-mm-Platte: Portalhoehe',
        '  und damit die 130 mm zum Bett bleiben.',
        '  Schienenabstand: erst das Portal mit beiden Schlitten verschrauben,',
        '  dann die Y-Schienen parallel dazu ausrichten. Er ergibt sich aus',
        '  der Rohrlaenge + 2 x {:.1f} mm; ein kuerzeres Rohr zieht die'
        .format(L['profil_ende_u']),
        '  Kernschrauben an die Stirnbloecke.',
        '',
        'Y-SCHLITTEN (links und rechts spiegelgleich):',
        '  Wagen MGN12H, Mitte bei Y={:+.0f}: HINTER dem Rohr. So bleiben alle'
        .format(w('wagen_y')),
        '  vier Wagenschrauben (4x M3x{:.0f}, Kopf versenkt) von oben frei.'
        .format(L['wagen_schraube']),
        '  Rohr: liegt auf der Platte, Rueckwand mit 2x M5x{:.0f} in Hammer-'
        .format(L['rueck_schraube']),
        '  muttern der hinteren Nut (Kopf versenkt), Stirnblock mit 1x',
        '  M5x{:.0f} in die Kernbohrung — dort M5 schneiden, >= {:.0f} mm tief.'
        .format(L['kern_schraube'], L['kern_gewinde'] + 2.0),
        '  Die Vorderseite des Rohrs bleibt frei fuer die X-Schiene.',
        '',
        'Y-RIEMEN (Lage wie RiemenklemmeSchlitten v8, laeuft weiter wie',
        '  bisher): Mitte {:.1f} mm innen neben der Schienenmitte, hochkant,'
        .format(w('y_riemen_linie')),
        '  Zaehne zur Schiene, Unterkante Z={:+.1f}.'.format(L['yr_z0']),
        '  Der Ruecklauf laeuft in der oberen Nut des 2040 ({:.1f} mm neben'
        .format(L['yr_rueck_u']),
        '  der Schienenmitte). Die Zaehne zeigen zur Innenseite der Schleife,',
        '  also zur Schiene: dort stehen die Rippen beider Klemmen.',
        '  Zwei Klemmen je Schlitten, eine je Riemenende:',
        '  VORN feste Klemme: Riemen von unten in den Schlitz druecken,',
        '  Stift Ø3 (oder M3x20) von vorn unter ihm durchschieben.',
        '  HINTEN Spannschieber: Riemen von unten einlegen, Schieber von',
        '  hinten in den Kanal, M3x{:.0f} von hinten durch den Schieber in die'
        .format(L['druck_schraube']),
        '  Mutter im Anschlag. Eindrehen schiebt ihn nach vorn = spannen.',
        '  Weg {:.0f} mm; reicht er nicht, das Riemenende einen Zahn weiter'
        .format(w('schieber_weg')),
        '  in die vordere Klemme setzen (2 mm).',
        '  Klemmschlitz {:.1f} mm, Rippen {:.1f} mm: laesst sich der Riemen'
        .format(w('klemm_schlitz'), w('klemm_rippe')),
        '  nicht eindruecken, klemm_schlitz um 0,1 erhoehen; rutscht er,',
        '  verringern (gilt auch fuer den Riemenhalter in ToolheadZ.py).',
        '  Rechtwinklig stellen: beide Seiten ueber den Spannschieber, bis',
        '  das Portal an beiden Schienenenden gleich weit steht.',
        '',
        'X-ANTRIEB (GT2 20 Z, Riemen hochkant, Unterkante Z={:+.2f}):'.format(
            L['xr_z0']),
        '  Motor links, Achse X={:+.1f} Y={:+.2f}: stehend, Welle nach unten,'
        .format(L['x_motor'], L['xr_yc']),
        '  Ritzel mit der Nabe nach OBEN, Spur auf Riemenhoehe ({:+.1f} bis'
        .format(L['ritzel_z0']),
        '  {:+.1f}). 4x M3x{:.0f} von unten, alle vier erreichbar.'.format(
            L['ritzel_z1'], L['motor_schraube']),
        '  Motorhalter: 2x M3x{:.0f} von oben in die Einsaetze des Stirnblocks.'
        .format(L['mh_schraube']),
        '  Umlenkung rechts, Achse X={:+.2f} (Spannweg {:+.2f} bis {:+.2f}):'
        .format(L['x_rolle'], L['x_rolle_bereich'][0],
                L['x_rolle_bereich'][1]),
        '  20-Z-Rolle mit Kugellager, Bohrung 5, auf M5x{:.0f} von oben'.format(
            w('uh_bolzen')),
        '  (Kopf auf dem Spannklotz, Scheibe ueber und unter der Rolle,',
        '  Mutter im Schlitz unter der unteren Platte).',
        '  Spannen: M3x{:.0f} aussen durch die Lasche in die Mutter im'.format(
            L['zug_schraube']),
        '  Spannklotz — eindrehen zieht die Rolle nach aussen. Dann die M5',
        '  festziehen; sie haelt, die M3 stellt nur ein.',
        '  Umlenkhalter: 2x M3x{:.0f} von oben in die Einsaetze des Stirnblocks.'
        .format(L['uh_schraube']),
        '  Riemenlaenge: Schleife {:.0f} mm, beide Enden im Riemenhalter'
        .format(riemen_x),
        '  (ToolheadZ.py) — mit der Rolle in Mittelstellung ablaengen.',
        '',
        'MONTAGEREIHENFOLGE:',
        '  1. Einsaetze einschmelzen: 2 je Riemenblock (oben), 2 je',
        '     Stirnblock (oben).',
        '  2. M3-Mutter von oben in die Tasche des Riemenblocks, Block unter',
        '     die Platte (2x M3x{:.0f} von oben) — die Platte haelt die Mutter.'
        .format(L['rb_schraube']),
        '  3. Schlitten auf die Y-Wagen, 4x M3x{:.0f} (Kopf in der Senkung).'
        .format(L['wagen_schraube']),
        '  4. Hammermuttern in die hintere Nut des Rohrs, Kernbohrungen M5',
        '     schneiden. Portal (Rohr mit X-Schiene und Toolhead) auf die',
        '     Platten legen, an Rueckwand und Stirnblock: 2x M5x{:.0f} hinten,'
        .format(L['rueck_schraube']),
        '     1x M5x{:.0f} stirnseitig je Seite.'.format(L['kern_schraube']),
        '  5. Motor auf den Motorhalter (4x M3x{:.0f} von unten), Ritzel auf'
        .format(L['motor_schraube']),
        '     Riemenhoehe, Halter aufs linke Rohrende (2x M3x{:.0f}).'.format(
            L['mh_schraube']),
        '  6. Umlenkhalter aufs rechte Rohrende (2x M3x{:.0f}), Spannklotz,'
        .format(L['uh_schraube']),
        '     Rolle und M5 einsetzen, Zugschraube lose.',
        '  7. X-Riemen: ein Ende in den Riemenhalter, um Motor und Rolle,',
        '     zweites Ende einlegen, spannen.',
        '  8. Y-Riemen wie oben (vorn fest, hinten Spannschieber).',
        '',
        'DRUCK (PETG, Bambu Lab A1, 4 Wandlinien, >=40 % Infill):',
        '  Schlitten ....... Unterseite aufs Bett, Waende stehen darauf',
        '  Riemenblock ..... auf der Rueckseite stehend (Kanal senkrecht,',
        '                    Rippen als waagerechte Stege)',
        '  Spannschieber ... auf der Rueckseite stehend',
        '  Motorhalter ..... Motorplatte (Oberseite) aufs Bett',
        '  Umlenkhalter .... auf der Rueckseite (Saeule) stehend',
        '  Spannklotz ...... Unterseite aufs Bett',
        '  Keine Stuetzen noetig. Rechter Schlitten, Riemenblock und',
        '  Spannschieber sind gespiegelt — im Slicer NICHT spiegeln, die',
        '  Koerper so exportieren, wie sie im Modell liegen.',
        '',
        'NICHT GEMESSEN — vor dem Druck pruefen [?]:',
        '  Umlenkrolle: Aussendurchmesser {:.0f} mm und Breite {:.1f} mm sind'
        .format(w('rolle_d'), w('rolle_breite')),
        '    angenommen (20-Z-Rolle mit Lager, Bohrung 5).',
        '  X-Motor: Laenge {:.0f} mm angenommen (nur Freigang).'.format(
            w('motor_laenge')),
        '',
        'PARAMETRIK: MASSE landet als User-Parameter im Dialog. Die absoluten',
        '  Lagen rechnet lage() in Python — nach einer Parameteraenderung das',
        '  Skript neu laufen lassen und tools/portal_check.py ausfuehren.',
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
        _EBENEN.clear()

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
        # damit schon an seinem Platz. Nichts bewegt sich gegeneinander (die
        # Spanner sind Einstellungen), also alles fixiert statt Joints.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Schlitten_links', 'Riemenblock_links',
                     'Spannschieber_links', 'Motorhalter',
                     'Schlitten_rechts', 'Riemenblock_rechts',
                     'Spannschieber_rechts', 'Umlenkhalter', 'Spannklotz',
                     'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o

        for s in (-1, 1):
            n = seite(s)
            bau_schlitten(app, design, occ['Schlitten_' + n].component, L, s,
                          fehler)
            bau_riemenblock(app, design, occ['Riemenblock_' + n].component,
                            L, s, fehler)
            bau_spannschieber(app, design,
                              occ['Spannschieber_' + n].component, L, s,
                              fehler)
        bau_motorhalter(app, design, occ['Motorhalter'].component, L, fehler)
        bau_umlenkhalter(app, design, occ['Umlenkhalter'].component, L,
                         fehler)
        bau_spannklotz(app, design, occ['Spannklotz'].component, L, fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, fehler)

        for o in occ.values():
            o.isGrounded = True

        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        app.activeViewport.fit()
        validierungs_bericht(app, design, ui,
                             hinweise=hinweise_bauen(L, fehler))

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
