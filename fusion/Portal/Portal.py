# Portal.py — Y-Schlitten des Portals (MGN12H) mit X- und Y-Antrieb
#
# Baugruppe aus fuenfundzwanzig Druckteilen. Getrennt, weil jedes Teil nur
# so ohne Stuetzmaterial druckbar ist — die Y-Klemmtuerme haengen unter der
# Platte, die Rohrhalterung steht auf ihr:
#   Schlitten_links/rechts     Platte auf dem MGN12H-Wagen. Das Portalrohr
#                              liegt unten auf, eine Rueckwand (2x M5 in
#                              Nutensteinen) und ein Stirnblock (M5 in die
#                              Kernbohrung) halten es. Die Vorderseite bleibt
#                              frei — dort sitzt die X-Schiene. Links mit
#                              den 2 Loechern fuer den Kettenhalter Y und
#                              (seit Rev. 24) dem Anschlag, an dem der
#                              Motorhalter gegen den Riemenzug anliegt.
#   Klemmturm_vorn/hinten_*    zwei gleiche Y-Klemmtuerme je Schlitten wie
#                              in v8, einer je Riemenende: Schlitz mit
#                              Rippen, Querstift unter dem Riemen. Gespannt
#                              wird am Y-Motor (Langloecher).
#   Motorhalter                X-Motor (NEMA 17) stehend ueber dem linken
#                              Rohrende, Welle nach unten. Duenne Motor-
#                              platte, die Ritzelnabe taucht in ihre Bund-
#                              bohrung: die 20-mm-Welle traegt das ganze
#                              Ritzel.
#   Lagerschlitten + Spannbock X-Umlenkung rechts: ein Ritzel wie am Motor
#                              (Nabe oben) fest auf einer Welle Ø5, die oben
#                              in einem Kugellager, unten in einem Gleitlager
#                              laeuft. Beide Lager sitzen im Lagerschlitten,
#                              der auf dem Rohr gleitet (Feder in der oberen
#                              Nut); eine M3 von aussen durch den Spannbock
#                              zieht ihn nach aussen.
#   Y-Motorhalter_links/rechts vorn an jeder 2040 (bis Rev. 15 eigenes
#                              Skript YMotorhalter.py, Rev. 5): U-Buegel mit
#                              Schenkeln an beiden Seitenflaechen, je 2x M5
#                              in Nutensteinen der UNTEREN Nut, Joch an der
#                              Stirnseite, Platte davor. Der NEMA 17 haengt
#                              darunter, Welle nach oben, das Ritzel mittig
#                              zur 2040 direkt auf der Welle; gespannt wird
#                              in Langloechern. Symmetrisch: links und
#                              rechts dasselbe Teil.
#   Halter_Y, Fahne_Y          Endschalter Y (Gabellichtschranke LM393): der
#                              Halter aussen am rechten 2040 hinter dem
#                              hinteren 2060, 2x M5 in der UNTEREN Nut (in
#                              der oberen laeuft der Ruecklauf des Y-Riemens);
#                              die Fahne klemmt an der Aussenkante der
#                              rechten Schlittenplatte.
#   Halter_X, Klammer_X,       Endschalter X: der Halter vor dem linken Ende
#   Fahne_X                    der 2020, M5 in ihrer vorderen Nut, stoesst
#                              an das Ende der X-Schiene; Klammer und Fahne
#                              unten an der Traegerplatte des Toolheads.
#                              Bis Rev. 14 in Endschalter.py; Montage und
#                              Einstellen: docs/endschalter.md.
#   Kettenwanne,               X-Energiekette (seit Rev. 19, gedruckte Kette):
#   Wannenstuetze_*            sie liegt direkt hinter der Traegerplatte. Die
#                              Wanne fuehrt den Untertrum ueber Riemen und
#                              Riemenhalter hinweg; drei Stuetzen tragen sie,
#                              je mit einer Platte hinten am Rohr (M5 in der
#                              hinteren Nut), einem Block hinter dem
#                              Ruecklauf und einem Arm unter der Wanne. Am
#                              Festpunkt sitzt das Endstueck 180 auf Wanne
#                              und Stuetze; das bewegte Ende traegt der
#                              Kettenhalter am Toolhead (ToolheadZ.py).
#                              Seit Rev. 21 traegt die Stuetze am Festpunkt
#                              links einen Kabelfluegel fuer die Litzen.
#                              docs/energiekette.md.
#   Kettenhalter_Y,            Y-Energiekette (seit Rev. 21): dieselbe Kette
#   Kettenwanne_Y,             aussen am linken 2040. Der Kettenhalter Y
#   Wannentraeger_Y_*          sitzt auf dem linken Schlitten, die Wanne Y
#                              mit dem Festpunkt auf drei Traegern in der
#                              unteren Seitennut des 2040.
#   Bohrlehren                 ausgeblendet: Y-Wagen, Lichtschranke und die
#                              Loecher fuer den Kettenhalter Y im Schlitten
#   Referenz_nicht_drucken     nur zur Ansicht, NICHT drucken: Aluprofile,
#                              Linearfuehrungen, X- und Y-Riemen, X- und
#                              Y-Motoren mit Ritzel, Umlenkritzel, vom
#                              Toolhead Riemenhalter, Traegerplatte und
#                              Kettenhalter (vereinfacht), X- und Y-Kette,
#                              die beiden Lichtschranken
#
# Im Modell steht das Portal in der Mitte seines Wegs und der Toolhead in der
# Mitte des X-Wegs; die Fahnen sitzen also dort, wo sie montiert werden, und
# nicht in ihrer Gabel. Den Schaltpunkt rechnet lage() (schalt_dy,
# schalt_xs), tools/endschalter_check.py prueft ihn und den Freiraum ueber
# den ganzen Weg, docs/endschalter.svg zeigt ihn.
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
REVISION = 24

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
    'x_wagen_boden':        (4.0, 'MGN15: Luft unter dem Wagenkoerper'),

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

    # --- Y-Riemen -----------------------------------------------------------
    # Linie wie in RiemenklemmeSchlitten v8: Mitte 21,6 mm innen neben der
    # Schienenmitte, hochkant, Zaehne zur Schiene. Hoehe [v]: der Riemen
    # laeuft nur in der oberen Nut des 2040 — deren Oeffnung beginnt 6 mm
    # unter der Oberkante des Profils, ihre Mitte liegt 10 mm darunter. Der
    # Riemen liegt mittig darin, 7 bis 13 mm unter der Profilkante; der
    # Wagen steht 13 mm ueber ihr. Ruecklauf und Klemme auf gleicher Hoehe.
    'y_riemen_linie':      (21.6, 'Y-Riemen: Mitte neben der Schienenmitte'),
    'y_riemen_tiefe':      (26.0, 'Y-Riemen: Unterkante unter der Wagenoberseite'),

    # --- GT2 (hardware.md) -------------------------------------------------
    'riemen_breite':        (6.0, 'GT2: Riemenbreite'),
    'riemen_dicke':        (1.38, 'GT2: Gesamtdicke'),
    'riemen_zahn_h':       (0.75, 'GT2: Zahnhoehe'),
    'riemen_pld':         (0.254, 'GT2: Wirklinie ueber dem Zahngrund'),
    'riemen_teilung':       (2.0, 'GT2: Teilung'),
    'ritzel_teilkreis':   (12.73, 'GT2 20 Z: Teilkreis = Abstand der Trume'),
    'ritzel_flansch_d':    (16.0, 'GT2 20 Z Ritzel: Flansch'),
    'ritzel_laenge':       (16.0, 'GT2 20 Z Ritzel: Gesamtlaenge'),
    'ritzel_bord':          (1.0, 'GT2 20 Z Ritzel: Bord (je Seite)'),
    # Spur fuer den 6-mm-Riemen; der Rest der 16 mm ist die Nabe mit den
    # Madenschrauben in ihrer Mitte [w]
    'ritzel_spur':          (7.0, 'GT2 20 Z Ritzel: Spur zwischen den Borden'),
    'ritzel_nabe_d':       (13.0, 'GT2 20 Z Ritzel: Nabe'),
    # Umlenkung seit Rev. 18: ein normales Ritzel wie am X-Motor (ritzel_*)
    # sitzt mit den Madenschrauben fest auf einer Welle Ø5. Die Welle laeuft
    # oben in einem Rillenkugellager, unten in einem Gleitlager (Masse
    # Angabe 2026-09-30, Bohrung 5 angenommen [?]). Eingebaut mit der Nabe
    # nach OBEN — die Spur steht auf dem Riemen, darunter ist bis zum Rohr
    # gerade Platz fuer das Gleitlager.
    'kl_d':                (10.0, 'Kugellager (Umlenkung): Aussendurchmesser'),
    'kl_b':                 (4.0, 'Kugellager (Umlenkung): Breite'),
    'gl_d':                 (7.0, 'Gleitlager (Umlenkung): Aussendurchmesser'),
    'gl_l':                 (8.0, 'Gleitlager (Umlenkung): Laenge'),
    'uw_d':                 (5.0, 'Welle der Umlenkung: Durchmesser'),
    'uw_laenge':           (30.0, 'Welle der Umlenkung: Laenge'),

    # --- X-Riemen: Lage wie in ToolheadZ.py (Riemenhalter) -----------------
    'x_riemen_y':         (-10.0, 'X-Riemen: Wirklinie des gezogenen Trums'),
    'x_riemen_z0':        (20.25, 'X-Riemen: Unterkante'),

    # --- Riemenklemmen: wie der Riemenhalter in ToolheadZ.py ----------------
    'klemm_schlitz':        (1.6, 'Riemenklemme: Rippengrund bis glatte Wand'),
    'klemm_rippe':          (0.8, 'Riemenklemme: Rippenhoehe'),
    'klemm_rippe_b':        (1.0, 'Riemenklemme: Rippenbreite'),
    'klemm_stift_d':        (3.2, 'Riemenklemme: Bohrung fuer den Stift'),
    # Nur die Y-Klemmtuerme: der Schlitz reicht bis knapp ueber die Oberkante
    # der Nut im 2040 — hoeher kann der Riemen nicht laufen. So war es auch in
    # v8 (Schlitzdecke 19,0 mm unter der Wagenoberseite = Oberkante der Nut).
    'kt_decke':             (0.5, 'Klemmturm: Schlitzdecke ueber der Nut-Oberkante'),

    # --- NEMA 17 fuer X und Y (hardware.md [w]) -----------------------------
    'motor_flansch':       (42.3, 'NEMA17: Flanschmass'),
    'motor_loch':          (31.0, 'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0, 'NEMA17: Zentrierbund'),
    'motor_bund_h':         (2.0, 'NEMA17: Zentrierbund, Hoehe'),
    'motor_welle_d':        (5.0, 'NEMA17: Wellendurchmesser'),
    # Die Halter sind auf 20 mm Welle ausgelegt (erste Angabe am Aufbau):
    # so traegt die Welle das ganze Ritzel schon ab 20 mm. Gemessen sind
    # 37 mm Motor und 60 mm mit Welle [v] — die Welle ragt also 23 mm heraus
    # und steht 3 mm weiter ueber das Ritzel hinaus; portal_check.py prueft,
    # dass sie dort frei endet.
    'motor_welle_l':       (20.0, 'NEMA17: Wellenlaenge, auf die die Halter ausgelegt sind'),
    'motor_welle_ist':     (23.0, 'NEMA17: Welle ragt so weit heraus (60 - 37, gemessen)'),
    'motor_laenge':        (37.0, 'NEMA17: Koerperlaenge ohne Welle (gemessen)'),
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
    'spiel_locker':         (0.4, 'Montagespiel, diametral'),
    'spiel_press':         (0.05, 'Presspassung, diametral (Lagersitze)'),
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
    # Einsaetze im Stirnblock fuer Motorhalter bzw. Spannbock (u, Y). Aussen
    # neben dem Motorflansch, damit die Koepfe neben dem Motor liegen.
    'halter_schraube_u':  (-18.5, 'Halterschrauben: u'),
    'halter_schraube_y1': (-41.0, 'Halterschrauben: Y hinten'),
    'halter_schraube_y2': (-34.5, 'Halterschrauben: Y vorn'),

    # --- Y-Klemmtuerme (wie v8) ---------------------------------------------
    # Zwei gleiche Tuerme je Schlitten wie in v8, symmetrisch zur Wagenmitte,
    # einer je Riemenende. Gespannt wird an den Ritzeln der Y-Enden.
    'turm_abstand':        (40.5, 'Y-Klemmtuerme: Aussenkante ab Wagenmitte (v8)'),
    'kt_laenge':           (18.0, 'Klemmturm: Laenge (v8)'),
    'kt_wand':              (3.5, 'Klemmturm: Wand neben dem Schlitz (v8)'),
    'kt_boden':             (3.4, 'Klemmturm: Material unter der Stiftbohrung (v8)'),
    'kt_rand':              (2.0, 'Klemmturm: rippenfreier Rand an den Enden (v8)'),

    # --- Motorhalter (links) ------------------------------------------------
    # Motorachse ueber dem Rohrende: weiter innen stiesse der Flansch am
    # Ende des X-Wegs an die Traegerplatte (3 mm Luft, portal_check.py).
    'motor_u':              (7.0, 'X-Motor: Achse (u)'),
    # Die Welle traegt das ganze Ritzel: der Motor steht so tief, dass sie
    # welle_ueberstand unter dem Ritzel endet, die Nabe taucht dafuer in die
    # Bundbohrung. 4,5 mm Platte: M3x8 fasst 3,5 mm im Flansch, und die
    # Madenschrauben liegen 2,5 mm unter der Platte (Inbus von vorn).
    'welle_ueberstand':     (0.5, 'X-Motor: Welle steht unter dem Ritzel vor'),
    'mp_dicke':             (4.5, 'Motorplatte: Dicke'),
    'saeule_aussen_b':     (10.0, 'Motorhalter: aeussere Saeule, Breite'),
    # Anschlag (seit Rev. 24, nur links): Der Riemenzug schiebt den Halter
    # nach innen; bis Rev. 23 hielt ihn dagegen nur die Reibung unter den
    # zwei Schrauben, und bei kraeftig gespanntem Riemen rutschte er. Der
    # Anschlag steht auf dem Stirnblock innen neben der aeusseren Saeule
    # und passt auch an den schon gedruckten Halter. Nach hinten endet er
    # vor dem Werkzeug der hinteren aeusseren Motorschraube.
    'mha_spiel':            (0.2, 'Anschlag Motorhalter: Luft zur aeusseren Saeule'),
    'mha_dicke':            (8.0, 'Anschlag Motorhalter: Dicke nach innen'),
    'mha_hoehe':            (6.0, 'Anschlag Motorhalter: Hoehe ueber dem Stirnblock'),

    # --- Umlenkung (rechts): Lagerschlitten + Spannbock (seit Rev. 18) ------
    # Beide Lager sitzen im Lagerschlitten, einem Rahmen um das Ritzel. Er
    # liegt auf dem Rohr, eine Feder unter ihm laeuft in der oberen Nut.
    # Eine M3 von aussen durch den Spannbock (fest auf dem Stirnblock) in
    # einen Gewindeeinsatz im Ruecken des Schlittens zieht ihn nach aussen.
    # Der untere Bord des Ritzels steht 2,75 mm ueber dem X-Wagen (Z +16):
    # die Achse liegt so weit aussen, dass es am rechten Ende des X-Wegs
    # auch ganz innen 3 mm neben dem Wagen bleibt (bis Rev. 16: 26,35).
    'rolle_u':            (25.25, 'X-Umlenkung: Achse in Mittelstellung (u)'),
    'rolle_weg':            (4.0, 'X-Umlenkung: Spannweg je Richtung'),
    'ls_luft':              (0.5, 'Lagerschlitten: Luft Ritzel - Kugellager und Arme'),
    'ls_wand':              (2.5, 'Lagerschlitten: Wand um die Lager'),
    'ls_decke':             (2.0, 'Lagerschlitten: Decke ueber dem Kugellager'),
    # 8 mm: darin der Gewindeeinsatz der Zugschraube (Ø4,6)
    'ls_ruecken':           (8.0, 'Lagerschlitten: Ruecken hinter dem Ritzel'),
    'ls_pfosten':           (5.0, 'Lagerschlitten: Pfosten vor dem Ritzel'),
    'ls_aussen':            (8.0, 'Lagerschlitten: reicht so weit aussen neben die Achse'),
    'ls_feder_b':           (5.8, 'Lagerschlitten: Feder in der oberen Nut, Breite'),
    'ls_feder_t':           (1.5, 'Lagerschlitten: Feder, Tiefe'),
    'sb_boden':             (6.0, 'Spannbock: Boden auf dem Stirnblock'),
    'sb_wand':              (6.0, 'Spannbock: Wand fuer die Zugschraube, Dicke'),
    'sb_wand_b':           (14.0, 'Spannbock: Wand, Breite'),
    'zug_eingriff':         (5.0, 'Zugschraube: mindestens so weit im Einsatz'),

    # --- Energiekette X (seit Rev. 19) -------------------------------------
    # Gedruckte Kette (Modell "Energiekette" von lingnau.florian, aus der
    # 3MF ausgemessen am 2026-10-01): Teilung 16, aussen 18 x 14, innen
    # 10 x 8,8. Gemessen am gedruckten Teil (2026-10-02): um 180 Grad bis
    # an die Anschlaege gebogen ist die Schleife aussen 50 mm hoch, 4 Gelenke
    # knicken im Bogen (je etwa 45 Grad; im Modell schlagen die Glieder bei
    # 47 Grad an, R = 16 / (2 sin 23,5 Grad) = 20,1). Gerechnet wird mit
    # R 20: aussen 2 R + 14 + 2 x 0,3 = 54,6 mm, also nie enger, als die
    # Kette biegt, und hoechstens 5 mm weiter. Rev. 20 und 21 rechneten mit
    # R 32 (30 Grad je Glied, geschaetzt), Rev. 19 mit R 20 aus dem Modell.
    # Der Riegel steht 0,3 ueber die Laschen. Endstuecke: Platte 2 mm mit
    # zwei Loechern Ø5,5 im Abstand 12, das erste 18 mm hinter dem Gelenk;
    # sie reichen 36 mm hinter das Gelenk, das Auge 7 mm davor. Anfangs-
    # und Endstueck tragen die Platte auf der Bodenseite, das Endstueck 180
    # auf der Riegelseite. Der Boden liegt innen in der Schleife: am
    # Toolhead das Anfangsstueck mit der Platte nach unten auf dem Ketten-
    # halter (ToolheadZ.py), am Festpunkt das Endstueck 180, Platte nach
    # unten auf der Wanne.
    # Die Kette liegt direkt hinter der Traegerplatte, die Schleife zeigt
    # nach rechts und laeuft am Ende des X-Wegs ueber den Lagerschlitten:
    # deshalb liegt der Wannenboden so hoch (3,25 mm ueber ihm). Vorn bleibt
    # luft_bau bis zur Traegerplatte, dann Wand 2 und Spiel 0,5 (seit
    # Rev. 23, vorher 0,3: gedruckte Kette, Elefantenfuss).
    # kette_*, endstueck_*, xk_* stehen gleich in ToolheadZ.py,
    # tools/portal_check.py vergleicht sie.
    'kette_teilung':      (16.0, 'Energiekette: Teilung'),
    'kette_b':            (18.0, 'Energiekette: Breite aussen'),
    'kette_h':            (14.0, 'Energiekette: Hoehe der Laschen'),
    'kette_riegel':        (0.3, 'Energiekette: Riegel steht ueber die Laschen'),
    'kette_r':            (20.0, 'Energiekette: Biegeradius der Gelenkachse'),
    'kette_innen_b':      (10.0, 'Energiekette: innen, Breite'),
    'kette_innen_h':       (8.8, 'Energiekette: innen, Boden bis Riegel'),
    'kette_spiel':         (0.5, 'Energiekette: Spiel je Seite in Wanne und Halter'),
    'endstueck_l':        (36.0, 'Endstueck: Gelenk bis Ende'),
    'endstueck_auge':      (7.0, 'Endstueck: Auge vor dem Gelenk'),
    'endstueck_loch_a':   (18.0, 'Endstueck: Gelenk bis erstes Loch'),
    'endstueck_loch_ab':  (12.0, 'Endstueck: Lochabstand'),
    'endstueck_loch_d':    (5.5, 'Endstueck: Loecher'),
    'endstueck_platte':    (2.0, 'Endstueck: Platte, Dicke'),
    'xk_y_vorn':          (-5.5, 'X-Kette: Vorderseite'),
    'xk_boden_z':         (44.5, 'X-Kette: Oberkante Wannenboden'),
    'xk_gelenk_x':        (22.0, 'X-Kette: bewegtes Gelenk rechts der X-Wagenmitte'),
    'wanne_boden':         (3.0, 'Kettenwanne: Boden'),
    'wanne_wand':          (2.0, 'Kettenwanne: Wand'),
    'wanne_wand_h':       (10.0, 'Kettenwanne: Wand ueber dem Boden'),
    'wanne_rand':          (3.0, 'Kettenwanne: beginnt so weit vor dem Endstueck'),
    'wanne_lasche':       (10.0, 'Kettenwanne: Lasche hinter der Rueckwand'),
    'wanne_lasche_b':     (12.0, 'Kettenwanne: Lasche, Breite'),
    # Stuetzen: Platte hinten am Rohr, Block auf dem Rohr hinter dem
    # Ruecklauf, Arm vorn unter der Wanne — ueber Riemen und Riemenhalter
    'st_platte':           (4.0, 'Wannenstuetze: Platte hinter dem Rohr'),
    'st_unten':            (8.0, 'Wannenstuetze: Platte reicht unter die Nutmitte'),
    'st_arm':              (6.0, 'Wannenstuetze: Arm unter der Wanne'),
    'st_arm_vorn':        (-8.0, 'Wannenstuetze: Arm endet bei Y'),
    'st_block_y':        (-27.0, 'Wannenstuetze: Block hinter dem Ruecklauf bis Y'),
    'st_b':               (16.0, 'Wannenstuetze: Breite'),
    'st_rand':             (7.0, 'Festpunkt-Stuetze: Rand neben den Loechern'),
    'st_x_mitte':         (95.0, 'Wannenstuetze mitte: X'),
    'st_x_rechts':       (200.0, 'Wannenstuetze rechts: X'),
    'profil_fase':         (1.0, 'Stuetzen: Fase in der Innenecke (Rohrkante)'),

    # --- Kabelfluegel an der Stuetze am Festpunkt (seit Rev. 21) ------------
    # Die Litzen der X-Kette (W7, W11, W15) kommen in der oberen Nut des
    # Rohrs vom linken Y-Schlitten, treten links neben der Stuetze am
    # Festpunkt aus der Nut und laufen vor einem Fluegel der Stuetze hinter
    # dem Ruecklauf hoch, dann ueber den Riemen nach vorn und von links in
    # das Endstueck 180. Zwei Kabelbinder durch je zwei Schlitze im Fluegel
    # halten sie (Zugentlastung, die Koepfe hinten).
    'kf_buendel_b':        (8.0, 'Kabelfluegel: Platz fuer die Litzen (X)'),
    'kf_buendel_t':        (6.0, 'Kabelfluegel: Litzen vor dem Fluegel (Y)'),
    'kf_steg':             (2.0, 'Kabelfluegel: Wand neben den Schlitzen'),
    'kf_binder_b':         (4.5, 'Kabelfluegel: Schlitz, hoch (Binderbreite)'),
    'kf_binder_t':         (2.2, 'Kabelfluegel: Schlitz, quer (Binderdicke)'),
    'kf_binder_z1':       (18.0, 'Kabelfluegel: unterer Kabelbinder bei Z'),
    'kf_binder_z2':       (34.0, 'Kabelfluegel: oberer Kabelbinder bei Z'),

    # --- Energiekette Y (seit Rev. 21) ---------------------------------------
    # Dieselbe gedruckte Kette wie X, aussen am linken 2040, Schleife nach
    # vorn. Das bewegte Ende (Anfangsstueck) liegt auf dem Kettenhalter Y,
    # der hinter dem Stirnblock auf der Platte des linken Y-Schlittens sitzt
    # (2x M3 von unten durch die Platte). Der Untertrum laeuft in der
    # Wanne Y zwischen den beiden 2060, sie liegt auf drei Traegern an der
    # unteren Seitennut des 2040 (die Nut an der Unterseite ist belegt,
    # Angabe 2026-10-01). Der Festpunkt (Endstueck 180) sitzt hinten in der
    # Wanne: die Litzen kommen dort aus der Nut direkt hinein.
    # Laenge: Arbeitsweg (hinten bis ans Schienenende, vorn bis luft_bau vor
    # das vordere 2060, y_weg_vorn) plus yk_reserve nach vorn (Wahl vom
    # 2026-10-01). Der Festpunkt liegt so, dass am hinteren Schienenende noch
    # luft_bau Untertrum bleibt; vorn bleibt so mehr als die Reserve.
    'y_weg_vorn':        (106.0, 'Y-Weg nach vorn, Z unten, bis 3 mm vor das 2060'),
    'yk_reserve':         (26.0, 'Y-Kette: Reserve nach vorn ueber den Y-Weg'),
    'yk_abstand':          (3.0, 'Y-Kette: aussen neben der Schlittenplatte'),
    'yk_gelenk_y':       (-48.0, 'Y-Kette: bewegtes Gelenk bei Y (Portal)'),
    'khy_dicke':            (8.0, 'Kettenhalter Y: Dicke (Einsaetze)'),
    'khy_auflage_b':        (8.0, 'Kettenhalter Y: liegt so breit auf der Platte'),
    'khy_hinten':          (12.0, 'Kettenhalter Y: reicht hinter das Anfangsstueck'),
    'khy_leiste':           (3.0, 'Kettenhalter Y: aeussere Leiste, Dicke'),
    'khy_leiste_h':         (3.0, 'Kettenhalter Y: Leisten, Hoehe'),
    'khy_schraube_y1':    (-56.0, 'Kettenhalter Y: vordere M3 bei Y'),
    'khy_binder_b':         (4.0, 'Binderschlitze Y-Kette: laengs'),
    'khy_binder_t':         (2.2, 'Binderschlitze Y-Kette: quer'),
    'khy_binder_abstand':   (9.0, 'Binderschlitze Y-Kette: Abstand'),
    'ywanne_hinten':      (12.0, 'Wanne Y: Boden hinter dem Endstueck 180'),
    'ywanne_lasche':       (7.7, 'Wanne Y: Lasche zum 2040 hin'),
    'ytr_wand':            (4.0, 'Traeger Y: Wand am 2040'),
    'ytr_arm':             (6.0, 'Traeger Y: Arm unter der Wanne'),
    'ytr_m5_rand':         (6.0, 'Traeger Y: Wand reicht so weit ueber/unter die M5'),
    'ytr_b':              (24.0, 'Traeger Y mitte/vorn: Breite'),
    'ytr_versatz':         (6.0, 'Traeger Y: M5 hinten, Laschenschraube vorn'),
    'ytr_y_mitte':       (-15.0, 'Traeger Y mitte: Y'),
    'ytr_y_vorn':         (75.0, 'Traeger Y vorn: Y'),

    # --- Y-Antrieb: je Ecke vorn ein NEMA 17 am Y-Motorhalter ---------------
    # Bis Rev. 15 eigenes Skript YMotorhalter.py (Rev. 5); der alte Halter
    # dieses Skripts (Achse 15,55 mm neben der Profilmitte, M5 in der oberen
    # Nut) ist ersetzt. Der Riemen laeuft in den oberen Nuten beider
    # Seitenflaechen der 2040 (in der inneren zur Klemme, in der aeusseren
    # zurueck) und am Profilende um das Ritzel, das mittig zur 2040 direkt
    # auf der Motorwelle sitzt. Der Motor haengt unter einer Platte, Welle
    # nach oben; Nutensteine in den UNTEREN Nuten beider Seiten (U-Buegel).
    # Gespannt wird, indem der Motor in Langloechern vom Profilende weg
    # rueckt. Das Teil ist symmetrisch: links und rechts dasselbe.
    # Platte: hoechstens Welle - Ritzel - Luft dick, sonst stoesst das
    # Ritzel an (tools/y_motorhalter_check.py).
    'ymh_platte_dicke':     (6.0, 'Y-Motorhalter: Motorplatte, Dicke'),
    'ymh_wange_dicke':      (6.0, 'Y-Motorhalter: Schenkel, Dicke'),
    # Am vorderen 2060 halten Winkel die 2040 (2026-09-27): die Schenkel
    # enden 5 mm davor, die M5 sitzen 8 und 22 mm hinter der Stirnseite.
    'ymh_wange_laenge':    (30.0, 'Y-Motorhalter: Schenkel hinter der Stirnseite'),
    'ymh_schraube_y':       (8.0, 'Y-Motorhalter: vordere M5 hinter der Stirnseite'),
    'ymh_schraube_abstand': (14.0, 'Y-Motorhalter: Abstand der M5 je Schenkel'),
    'ymh_rand_unten':       (1.0, 'Y-Motorhalter: endet so weit ueber der Unterkante der 2040'),
    'ymh_joch_dicke':       (4.0, 'Y-Motorhalter: Joch vor der Stirnseite'),
    'ymh_fuehrung_dicke':   (4.0, 'Y-Motorhalter: Fuehrungswand neben dem Motor'),
    # jeder mm Spannweg macht den Riemenweg 2 mm laenger
    'ymh_spann_weg':        (8.0, 'Y-Motorhalter: Spannweg in den Langloechern'),
    'ymh_rand_vorn':        (1.5, 'Y-Motorhalter: Platte vor dem Motor (ganz aussen)'),
    'ymh_luft_min':         (1.0, 'Y-Motorhalter: Mindestluft zwischen Teilen'),
    # Nut 6 der 2040 [w]: Lippe vor dem Nutenstein, Platz bis zum Nutgrund;
    # der Riemen laeuft hinter den Lippen im Nutkanal
    'nut_lippe':            (1.8, 'Nut 6: Dicke der Lippe'),
    'nut_tiefe':            (6.0, 'Nut 6 (2040): Platz ab Profilflaeche bis zum Nutgrund'),
    'nutenstein_h':         (4.0, 'Nutenstein M5: Gewindelaenge'),
    'motor_flach_l':       (15.0, 'NEMA17: Abflachung ab Wellenende'),
    'm3_kopf_d':            (5.5, 'M3 Zylinderkopf: Durchmesser'),
    'm3_scheibe_d':         (7.0, 'M3 Scheibe DIN 125: Durchmesser'),
    'm3_scheibe_h':         (0.5, 'M3 Scheibe DIN 125: Dicke'),
    'm5_scheibe_d':        (10.0, 'M5 Scheibe DIN 125: Durchmesser'),

    # --- Referenz (nicht drucken, nur zur Ansicht) --------------------------
    # Angaben am Aufbau [v]: 2040 600 mm, Y-Schienen 500 mm, darunter quer
    # zwei 2060 hochkant, 600 mm lang; das vordere sitzt 35 mm hinter der
    # Stirnseite der 2040, hinten stehen die 2040 110 mm ueber das hintere
    # 2060 (gemessen 2026-09-27, Rev. 14) — die 2060 liegen damit 435 mm
    # Mitte zu Mitte auseinander (bis Rev. 13: 400 [?]). Gezeichnet sind
    # 2040 und Schienen mittig zum Y-Wagen [?].
    # V-Slot vereinfacht: Nutoeffnung 6,2 und Kernbohrung 4,2 [w], dahinter
    # eine 8 mm breite Kammer.
    'rahmen_laenge':      (600.0, 'Referenz: Laenge der 2040'),
    'y_schiene_laenge':   (500.0, 'Referenz: Laenge der Y-Schienen'),
    'quer_laenge':        (600.0, 'Referenz: 2060 quer: Laenge'),
    'quer_abstand':       (435.0, 'Referenz: 2060 quer: Abstand Mitte zu Mitte'),
    'quer_vorn_zurueck':   (35.0, 'Referenz: vorderes 2060 so weit hinter der Stirnseite der 2040'),
    # Hinten: Ritzel auf einer Edelstahlwelle, Kugellager und Gleitlager [v].
    # Wo die Achse steht, ist nicht gemessen — angenommen wie vorn die alte
    # Eckwelle, 11 mm hinter der Stirnseite [?]. Davon haengt nur die
    # Riemenlaenge ab.
    'yh_hinter':           (11.0, 'Referenz: hinteres Ritzel so weit hinter der Stirnseite der 2040'),
    'quer_h':              (60.0, 'Referenz: 2060 quer, hochkant: Hoehe'),
    # Oeffnung aussen [v]: beginnt 6 mm unter der Profilkante, also 8 mm
    # breit um die Nutmitte; innen verengt sie sich auf 6,2 [w]
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),
    # Riemenhalter des Toolheads (ToolheadZ.py), portal_check.py vergleicht
    'traeger_x_links':    (-22.0, 'Toolhead: linke Kante (Riemenhalter)'),
    'traeger_x_rechts':    (22.0, 'Toolhead: rechte Kante (Riemenhalter)'),
    'rh_tiefe':            (14.0, 'Riemenhalter: Tiefe hinter der Traegerplatte'),
    'rh_hoehe':            (16.0, 'Riemenhalter: Hoehe ueber der Wagenflanke'),
    # Traegerplatte links, dort klemmt die Fahne X (ToolheadZ.py);
    # tools/endschalter_check.py vergleicht
    'traeger_dicke':        (8.0, 'Toolhead: Traegerplatte, Dicke (Y 0 bis 8)'),
    'traeger_z0':         (-66.0, 'Toolhead: Traegerplatte, Unterkante'),
    'rippe_b':              (4.0, 'Toolhead: Saeulenrippe links, Breite (X)'),
    'rippe_t':              (6.0, 'Toolhead: Saeulenrippe links, Tiefe vor der Platte'),

    # --- Endschalter X und Y (bis Rev. 14 in Endschalter.py) ---------------
    # Gabellichtschranke LM393 (Hailege), wie ToolheadZ.py [v]
    'ls_pcb_laenge':       (25.0, 'Lichtschranke: Platinenlaenge'),
    'ls_pcb_breite':       (20.0, 'Lichtschranke: Platinenbreite'),
    'ls_pcb_dicke':         (1.8, 'Lichtschranke: Platinendicke'),
    'ls_pcb_rand':          (2.5, 'Lichtschranke: Lochmitte von der Kante'),
    'ls_schlitz':          (10.0, 'Lichtschranke: Schlitzbreite (Gabelspalt)'),
    'ls_gabel_rand':        (1.0, 'Gabel: Abstand zur Stirnkante der Platine'),
    'ls_gabel_dicke':       (6.0, 'Gabel: Dicke entlang der Platine'),
    'ls_gabel_hoehe':      (15.0, 'Gabel: Hoehe ueber der Platine'),
    'ls_gabel_breite':     (18.5, 'Gabel: aussen, quer zum Schlitz'),
    'ls_strahl_hoehe':      (9.0, 'Gabel: Lichtfenster ueber der Platine'),
    # nicht gemessen [?], wie in ToolheadZ.py: das Blatt bleibt 1,5 mm darueber
    'ls_schlitz_boden':     (6.0, 'Gabel: Boden des Schlitzes ueber der Platine'),
    # M2-Einsaetze 3,2 x 2,5 [v] (vorhanden): Einpressbohrung 0,4 kleiner,
    # dahinter eine Freibohrung fuer die Schraubenspitze (M2x6)
    'ls_pcb_loch_d':        (2.8, 'Lichtschranke: Einpressbohrung M2-Einsatz'),
    'ls_pcb_loch_t':        (3.0, 'Lichtschranke: Tiefe der Einpressbohrung'),
    'ls_pcb_frei_d':        (2.4, 'Lichtschranke: Freibohrung fuer die Schraubenspitze'),
    'ls_pin_tasche':        (1.5, 'Tasche unter der Gabel fuer ihre Loetstifte'),
    # Schaltpunkt und Blatt, beide Achsen. Das Blatt reicht bis 7,5 mm an
    # die Platine (1,5 ueber den Schlitzboden, 1,5 ueber den Strahl hinaus)
    # und 2 mm ueber die offene Seite der Gabel.
    'schaltabstand':        (3.0, 'Schalter schaltet so weit vor dem Schienenende'),
    'fahne_dicke':          (3.0, 'Blatt: Dicke im Gabelspalt (wie Z)'),
    'fahne_ab_platine':     (7.5, 'Blatt: Kante so weit ueber der Platine'),
    'fahne_ueber_gabel':    (2.0, 'Blatt: reicht so weit ueber die offene Gabelseite'),
    # Halter Y. 16: der innere Arm der Gabel bleibt 3 mm neben dem Y-Wagen,
    # der am Schienenende ueber die Gabel faehrt
    'gy_mitte_aussen':     (16.0, 'Y: Spaltmitte so weit neben der Aussenflaeche des 2040'),
    'ly_unter_kante':       (8.0, 'Y: Platine so weit unter der Oberkante der 2040'),
    'hy_fuss_dicke':        (6.0, 'Halter Y: Fuss am 2040 (wie Y-Motorhalter)'),
    'hy_fuss_unten':        (2.0, 'Halter Y: Fuss endet so weit ueber der Unterkante'),
    'hy_boden':             (5.0, 'Halter Y: Boden unter der Platine'),
    'hy_rand':              (1.5, 'Halter Y: Boden steht so weit um die Platine'),
    'hy_m5_rand':           (6.0, 'Halter Y: M5 so weit von den Enden'),
    'hy_fase':              (3.0, 'Halter Y: Fase unter dem Boden am Fuss'),
    # Fahne Y: Hinterkante auf der Platte zwischen den Wagenschrauben (Y -70
    # und -50), so steht der Halter 35 mm hinter dem 2060 und weit vor dem
    # hinteren Ritzel
    'fy_hinten':          (-66.0, 'Fahne Y: Hinterkante (Y, Portal in der Mitte)'),
    'fy_laenge':           (12.0, 'Fahne Y: Laenge laengs der Plattenkante'),
    'kl_spiel':             (0.3, 'Klammern: Spiel auf die geklemmte Dicke'),
    'kl_kante':             (0.2, 'Klammern: Luft zur geklemmten Kante'),
    'fy_backe_o':           (6.0, 'Fahne Y: obere Backe (Einsatz M3)'),
    'fy_backe_u':           (2.5, 'Fahne Y: untere Backe'),
    'fy_backe_innen':       (9.0, 'Fahne Y: obere Backe reicht so weit auf die Platte'),
    'fy_wagen_luft':        (1.0, 'Fahne Y: untere Backe neben dem Y-Wagen'),
    # Halter X
    'hx_luft_wagen':        (3.0, 'X: Platine so weit links vom Wagenende am Schienenende'),
    'hx_dicke':            (11.0, 'Halter X: Block vor dem Rohr (Y)'),
    'hx_h':                (22.0, 'Halter X: Hoehe des Blocks (Z)'),
    'hx_rand':              (1.0, 'Halter X: Block steht links so weit ueber die Platine'),
    'hx_zunge_b':           (5.8, 'Halter X: Zunge in der Rohrnut (Breite)'),
    'hx_zunge_t':           (2.0, 'Halter X: Zunge in der Rohrnut (Tiefe)'),
    'hx_senk_t':            (5.2, 'Halter X: M5-Kopf versenkt, unter der Platine'),
    # Klammer X und Fahne X: X relativ zur X-Wagenmitte, Z absolut.
    # kx_backe_v 5,85: 3 mm vor dem Pad des Z-Schlittens, der Einsatz ist
    # 5,7 lang; kx_breite: bis 3 mm vor den Z-Wagen (linke Kante -10)
    'kx_z0':              (-40.0, 'Klammer X: Unterkante'),
    'kx_z1':              (-20.0, 'Klammer X: Oberkante der Backen'),
    'kx_wand':              (3.0, 'Klammer X: Seitenwand'),
    'kx_backe_h':           (2.5, 'Klammer X: hintere Backe'),
    'kx_backe_v':          (5.85, 'Klammer X: vordere Backe (Einsatz M3)'),
    'kx_breite':            (9.2, 'Klammer X: Backen reichen so weit auf die Platte'),
    'kx_wagen_luft':        (3.0, 'Klammer X: ueber dem Wagen nur vor der Platte'),
    'kx_kopf_b':            (6.0, 'Klammer X: Kopf steht links ueber die Wand'),
    'kx_kopf_h':            (6.0, 'Klammer X: Kopf (Einsatz M3 fuer die Fahne)'),
    'fx_verstellung':       (2.0, 'Fahne X: Langloch je Richtung'),
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
    # Schlitzdecke: knapp ueber der Oberkante der Nut im 2040
    L['nut_oberkante_z'] = L['rahmen_z1'] - w('nut_oben')
    L['yr_decke_z'] = L['nut_oberkante_z'] + w('kt_decke')

    # ---- Schlitten: Platte, Rueckwand, Stirnblock ---------------------------
    L['platte_u'] = (-w('platte_aussen'), w('platte_innen'))
    L['platte_y0'] = min(L['wagen_y0'] - 0.3,
                         w('wagen_y') - w('turm_abstand') - 0.5)
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

    # ---- Y-Klemmtuerme: zwei gleiche Tuerme wie v8 ---------------------------
    # Symmetrisch zur Wagenmitte, je einer vor und hinter dem Wagen; jeder
    # haelt ein Riemenende: Schlitz mit Rippen an der Wand zur Schiene,
    # unten und an beiden Enden offen, Querstift Ø3 unter dem Riemen.
    # Dazwischen laeuft kein Riemen. Gespannt wird an den Ritzeln der Y-Enden.
    L['stift_z'] = L['yr_z0'] - w('klemm_stift_d') / 2.0
    L['kt_u'] = (L['yr_rippe_u0'] - w('kt_wand'),
                 L['yr_wand_u'] + w('kt_wand'))
    L['kt_z'] = (L['stift_z'] - w('klemm_stift_d') / 2.0 - w('kt_boden'),
                 L['platte_z0'])
    wy, ta, tl = w('wagen_y'), w('turm_abstand'), w('kt_laenge')
    L['kt_y_hinten'] = (wy - ta, wy - ta + tl)
    L['kt_y_vorn'] = (wy + ta - tl, wy + ta)
    for t in ('hinten', 'vorn'):
        L['kt_stift_y_' + t] = (L['kt_y_' + t][0] + L['kt_y_' + t][1]) / 2.0
    # Schrauben Platte -> Turm: Platte unter der Senkung, dann mindestens
    # 5 mm im Einsatz, ohne im Sackloch aufzusetzen. Zwei je Turm, laengs
    # in der Mitte. Die des vorderen liegen unter dem Rohr (der Turm kommt
    # vor dem Rohr an die Platte): hinten 1 mm Luft zwischen Senkung und
    # Rueckwand, vorn 2 mm Wand vor dem Einsatz.
    L['turm_schraube'] = 2.0 * int((L['wagen_klemm'] + 5.0) / 2.0 + 0.999)
    L['turm_eingriff'] = L['turm_schraube'] - L['wagen_klemm']
    km = (L['kt_u'][0] + L['kt_u'][1]) / 2.0
    m = L['kt_stift_y_hinten']
    L['kt_schrauben_hinten'] = [(km, m - 4.5), (km, m + 4.5)]
    y_h = max(L['kt_y_vorn'][0] + w('insert_m3_d') / 2.0 + 2.0,
              L['rueck_y1'] + w('m3_senkung') / 2.0 + 1.0)
    y_v = L['kt_y_vorn'][1] - w('insert_m3_d') / 2.0 - 2.2
    L['kt_schrauben_vorn'] = [(km, y_h), (km, y_v)]
    # Querstift durch beide Waende: Turmbreite + 1 mm, auf gerade Laenge
    L['kt_stift_l'] = 2.0 * int((L['kt_u'][1] - L['kt_u'][0] + 1.0) / 2.0
                                + 0.999)
    # Rippen: Teilung 2, rippenfreier Rand an den Turmenden wie v8
    def rippen(y0, y1):
        n = int((y1 - y0 - w('klemm_rippe_b')) / w('riemen_teilung')) + 1
        rand = (y1 - y0 - (n - 1) * w('riemen_teilung')
                - w('klemm_rippe_b')) / 2.0
        return [y0 + rand + i * w('riemen_teilung') for i in range(n)]
    for t in ('hinten', 'vorn'):
        y0, y1 = L['kt_y_' + t]
        L['kt_rippen_y_' + t] = rippen(y0 + w('kt_rand'), y1 - w('kt_rand'))
    # Riemen um die Ritzel: beide sitzen seit Rev. 16 mittig zur 2040
    # (u = 0, Y-Motorhalter). Die Trume der Wagen laufen schraeg von der
    # Klemme in die innere obere Nut, der Ruecklauf gerade in der aeusseren
    # (y_riemen_weg). Die Zaehne zeigen zur Innenseite der Schleife, also
    # zur Schiene: deshalb stehen die Rippen der Klemmen auf der
    # Schienenseite. Auf dem Teilkreis liegen die Wirklinien, 0,31 mm neben
    # der Riemenmitte zum Ruecken hin.
    steg = w('riemen_dicke') - w('riemen_zahn_h')
    L['yr_wirk_versatz'] = w('riemen_dicke') / 2.0 - (steg - w('riemen_pld'))
    L['yr_wirk_u'] = w('y_riemen_linie') + L['yr_wirk_versatz']  # Klemme
    # Ruecklauf: Riemenmitte in der aeusseren oberen Nut (u < 0)
    L['yr_rueck_u'] = -w('ritzel_teilkreis') / 2.0 + L['yr_wirk_versatz']
    L['rahmen_flanke_u'] = w('rahmen_b') / 2.0
    # Hoehe des Ruecklaufs: mittig in der oberen Seitennut des 2040. Die
    # Klemme haelt den Riemen auf der am Aufbau gemessenen Hoehe; den
    # Unterschied gleicht er zu den Ritzeln an den Y-Enden hin aus.
    L['nut_z'] = L['rahmen_z1'] - w('rahmen_b') / 2.0
    L['yr_rueck_z'] = (L['nut_z'] - w('riemen_breite') / 2.0,
                       L['nut_z'] + w('riemen_breite') / 2.0)

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
    # Ritzel mit der Nabe nach oben, der Riemen mittig in der Spur. Die
    # Madenschrauben sitzen in der Mitte der Nabe.
    L['ritzel_z0'] = L['xr_zm'] - w('ritzel_spur') / 2.0 - w('ritzel_bord')
    L['ritzel_z1'] = L['ritzel_z0'] + w('ritzel_laenge')
    L['ritzel_nabe_z0'] = (L['ritzel_z0'] + 2.0 * w('ritzel_bord')
                           + w('ritzel_spur'))
    L['madenschraube_z'] = (L['ritzel_nabe_z0'] + L['ritzel_z1']) / 2.0
    # Flanschflaeche = Oberseite der Motorplatte, so tief, dass die Welle
    # durch das ganze Ritzel reicht. Die Nabe steht dann in der Bundbohrung.
    L['mp_z1'] = L['ritzel_z0'] - w('welle_ueberstand') + w('motor_welle_l')
    L['mp_z0'] = L['mp_z1'] - w('mp_dicke')
    L['bund_z0'] = L['mp_z1'] - w('motor_bund_h')
    L['motor_z1'] = L['mp_z1'] + w('motor_laenge')
    L['welle_z0'] = L['mp_z1'] - w('motor_welle_l')
    L['welle_ist_z0'] = L['mp_z1'] - w('motor_welle_ist')     # gemessen
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
    # Anschlag (seit Rev. 24) auf dem linken Stirnblock: innen mha_spiel
    # neben der aeusseren Saeule, von 0,5 mm hinter dem Werkzeug der
    # hinteren aeusseren Motorschraube bis an die Vorderkante des Blocks
    y_ms = min(y for u, y in L['motor_schrauben'] if u < w('motor_u'))
    u_a = L['mh_aussen_u'][1] + w('mha_spiel')
    L['mha_u'] = (u_a, u_a + w('mha_dicke'))
    L['mha_y'] = (y_ms + w('inbus_frei_d') / 2.0 + 0.5, L['stirn_y'][1])
    L['mha_z'] = (L['wand_z1'], L['wand_z1'] + w('mha_hoehe'))

    # ---- Umlenkung (rechts): Lagerschlitten und Spannbock --------------------
    L['rolle_u'] = (w('rolle_u') - w('rolle_weg'), w('rolle_u') + w('rolle_weg'))
    # Umlenkritzel wie am Motor, Nabe oben, der Riemen mittig in der Spur
    L['rolle_z0'] = L['xr_zm'] - w('ritzel_spur') / 2.0 - w('ritzel_bord')
    L['rolle_z1'] = L['rolle_z0'] + w('ritzel_laenge')
    L['rolle_nabe_z0'] = (L['rolle_z0'] + 2.0 * w('ritzel_bord')
                          + w('ritzel_spur'))
    L['rolle_maden_z'] = (L['rolle_nabe_z0'] + L['rolle_z1']) / 2.0
    # Lager: das Ritzel liegt mit dem Bord auf dem Gleitlager, das ls_luft
    # aus dem unteren Arm steht; ueber der Nabe ls_luft bis zum Kugellager
    L['gl_z'] = (L['rolle_z0'] - w('gl_l'), L['rolle_z0'])
    L['kl_z'] = (L['rolle_z1'] + w('ls_luft'),
                 L['rolle_z1'] + w('ls_luft') + w('kl_b'))
    # Lagerschlitten: unten und oben die Arme mit den Lagern, hinten der
    # Ruecken, vorn der Pfosten, je luft_bau neben dem Bord des Ritzels
    rf = w('ritzel_flansch_d') / 2.0
    L['ls_unten_z'] = (L['wand_z1'], L['gl_z'][1] - w('ls_luft'))
    L['ls_oben_z'] = (L['kl_z'][0], L['kl_z'][1] + w('ls_decke'))
    L['ls_ruecken_y'] = (L['xr_yc'] - rf - w('luft_bau') - w('ls_ruecken'),
                         L['xr_yc'] - rf - w('luft_bau'))
    L['ls_pfosten_y'] = (L['xr_yc'] + rf + w('luft_bau'),
                         L['xr_yc'] + rf + w('luft_bau') + w('ls_pfosten'))
    L['ls_y'] = (L['ls_ruecken_y'][0], L['ls_pfosten_y'][1])
    # u relativ zur Achse: aussen ls_aussen, innen die Wand um das Kugellager
    L['ls_u_rel'] = (-w('ls_aussen'), w('kl_d') / 2.0 + w('ls_wand'))
    # Feder unter dem unteren Arm, mittig in der oberen Nut des Rohrs; ihre
    # hintere Flanke (zum Druckbett) unter 45 Grad
    ym = L['profil_y0'] + w('profil_b') / 2.0
    L['ls_feder_y'] = (ym - w('ls_feder_b') / 2.0, ym + w('ls_feder_b') / 2.0)
    L['ls_feder_z'] = (L['wand_z1'] - w('ls_feder_t'), L['wand_z1'])
    L['ls_feder_u_rel'] = (L['ls_u_rel'][0] + 1.0, L['ls_u_rel'][1] - 1.0)
    # Welle: oben buendig mit dem Schlitten
    L['uw_z'] = (L['ls_oben_z'][1] - w('uw_laenge'), L['ls_oben_z'][1])
    # Zugschraube auf Riemenhoehe mitten im Ruecken: so kippt der Schlitten
    # nicht; dass sie in Y neben der Achse zieht, faengt die Feder ab.
    # Gewindeeinsatz von aussen in den Ruecken, dahinter Durchgang bis innen.
    L['zug_y'] = (L['ls_ruecken_y'][0] + L['ls_ruecken_y'][1]) / 2.0
    L['zug_z'] = L['xr_zm']
    L['ls_einsatz_u_rel'] = (L['ls_u_rel'][0],
                             L['ls_u_rel'][0] + w('insert_m3_t'))
    # Spannbock: Wand 0,5 mm aussen vor dem ganz gespannten Schlitten, Boden
    # auf Rohrende, Rueckwand und Stirnblock, 2x M3 in dessen Einsaetze
    aussen = L['rolle_u'][0] + L['ls_u_rel'][0]        # Schlitten ganz aussen
    innen = L['rolle_u'][1] + L['ls_u_rel'][0]         # ... und ganz innen
    L['sb_wand_u'] = (aussen - 0.5 - w('sb_wand'), aussen - 0.5)
    L['sb_u'] = (L['platte_u'][0], L['sb_wand_u'][1])
    L['sb_wand_y'] = (L['zug_y'] - w('sb_wand_b') / 2.0,
                      L['zug_y'] + w('sb_wand_b') / 2.0)
    L['sb_y'] = (L['rueck_y0'], L['sb_wand_y'][1])
    L['sb_boden_z'] = (L['wand_z1'], L['wand_z1'] + w('sb_boden'))
    L['sb_wand_z'] = (L['sb_boden_z'][1],
                      L['zug_z'] + w('m3_durchgang') / 2.0 + 3.0)
    # Zugschraube: Kopf aussen an der Wand. Ganz entspannt (Schlitten innen)
    # greift sie mindestens zug_eingriff in den Einsatz, ganz gespannt
    # bleibt ihre Spitze im Ruecken.
    L['zug_schraube'] = normlaenge(innen + w('zug_eingriff')
                                   - L['sb_wand_u'][0], M3_LAENGEN)
    L['zug_spitze_u'] = L['sb_wand_u'][0] + L['zug_schraube']
    L['zug_eingriff_ist'] = min(L['zug_spitze_u'] - innen, w('insert_m3_t'))
    L['zug_rest'] = L['rolle_u'][0] + L['ls_u_rel'][1] - L['zug_spitze_u']
    # Spannbock -> Stirnblock: Boden + 5 mm Gewinde im Einsatz
    L['sb_klemm'] = w('sb_boden')
    L['sb_schraube'] = normlaenge(L['sb_klemm'] + 5.0, M3_LAENGEN)

    # ---- X-Riemen: Laenge ueber Motor, Umlenkung (Mitte) und Halter -----------
    x_m = -(R - w('motor_u'))
    x_u = R - w('rolle_u')
    L['x_motor'] = x_m
    L['x_rolle'] = x_u
    L['x_rolle_bereich'] = (R - L['rolle_u'][1], R - L['rolle_u'][0])

    # ---- Referenz (nicht drucken) ---------------------------------------------
    # Rahmen mittig unter dem Y-Wagen, Toolhead in der Mitte des X-Wegs.
    # Ritzel mit dem Fuss der Verzahnung: dort liegen die Zaehne
    # des Riemens an, der Riemenkoerper durchdringt sie so nicht.
    L['rahmen_y'] = (w('wagen_y') - w('rahmen_laenge') / 2.0,
                     w('wagen_y') + w('rahmen_laenge') / 2.0)
    L['y_schiene_y'] = (w('wagen_y') - w('y_schiene_laenge') / 2.0,
                        w('wagen_y') + w('y_schiene_laenge') / 2.0)
    # 2060 quer unter den 2040: das vordere quer_vorn_zurueck hinter der
    # Stirnseite [v], das hintere quer_abstand (Mitte zu Mitte) dahinter [v]
    # (aus 110 mm Ueberstand der 2040 hinten, Rev. 14)
    L['quer_x'] = (-w('quer_laenge') / 2.0, w('quer_laenge') / 2.0)
    L['quer_z'] = (L['rahmen_z0'] - w('quer_h'), L['rahmen_z0'])
    v1 = L['rahmen_y'][1] - w('quer_vorn_zurueck')
    L['quer_y_vorn'] = (v1 - w('rahmen_b'), v1)
    L['quer_y_hinten'] = (v1 - w('rahmen_b') - w('quer_abstand'),
                          v1 - w('quer_abstand'))
    L['xw_mitte'] = (L['xw_min'] + L['xw_max']) / 2.0
    L['rh_x'] = (L['xw_mitte'] + w('traeger_x_links'),
                 L['xw_mitte'] + w('traeger_x_rechts'))
    L['ritzel_fuss_d'] = w('ritzel_teilkreis') - 2.0 * L['riemen_innen']

    # ---- Y-Antrieb: je Ecke vorn ein Y-Motorhalter ---------------------------
    # Seine Masse stehen in eigenen Koordinaten in lage_y_motorhalter(); er
    # liegt an beiden vorderen Ecken, die Mitte der 2040 bei X = +-R, die
    # Stirnseite bei Y = ye, die Unterkante der 2040 bei Z = rahmen_z0.
    # Motor und Ritzel mittig zur 2040, der Motor in der Mitte seines
    # Spannwegs.
    H = lage_y_motorhalter()
    L['ymh'] = H
    ye, zu = L['rahmen_y'][1], L['rahmen_z0']
    L['stirn_vorn_y'] = ye
    L['yr_zm'] = (L['yr_z0'] + L['yr_z1']) / 2.0
    L['ym_y'] = ye + H['motor_y_mitte']
    L['ym_y_bereich'] = (ye + H['motor_y_min'], ye + H['motor_y_max'])
    L['ym_ritzel_z'] = (zu + H['ritzel_z0'], zu + H['ritzel_z1'])
    L['ym_nabe_z1'] = zu + H['ritzel_z0'] + H['ritzel_nabe']
    L['ym_motor_z'] = (zu + H['motor_z0'], zu + H['motor_flansch_z'])
    L['ym_bund_z1'] = zu + H['bund_z1']
    L['ym_welle_z1'] = zu + H['welle_z1']

    # ---- Y-Riemen: hinteres Ritzel und Laenge ------------------------------
    # Hinten ein Ritzel auf einer Welle [v], mittig zur 2040 [v], laengs
    # angenommen [?]. Der Riemen ist offen (y_riemen_weg): vordere Klemme ->
    # Ritzel vorn -> Ruecklauf in der aeusseren Nut -> Ritzel hinten ->
    # hintere Klemme. Seine Enden stehen bis 1 mm vor das innere Ende der
    # Klemmtuerme; Laenge auf der Wirklinie, Portal in der Mitte, Motor in
    # der Mitte des Spannwegs.
    L['yh_y'] = L['rahmen_y'][0] - w('yh_hinter')
    L['yr_ende_vorn'] = L['kt_y_vorn'][0] + 1.0
    L['yr_ende_hinten'] = L['kt_y_hinten'][1] - 1.0
    L['yr_laenge'] = y_riemen_weg(L)['laenge']

    # ---- Endschalter X und Y (bis Rev. 14 in Endschalter.py) ---------------
    # Schaltpunkt: das Portal steht schalt_dy von der Mitte, schaltabstand
    # vor dem hinteren Schienenende (dort sind die Y-Wagen buendig mit ihm);
    # die X-Wagenmitte bei schalt_xs, schaltabstand vor dem linken. Schluessel
    # mit _rel liegen relativ zum Portal in der Mitte (Fahne_Y, Halter_X)
    # bzw. zur X-Wagenmitte (Klammer_X, Fahne_X). Der Halter Y steht fest am
    # Rahmen, dort, wo die Fahne am Schaltpunkt durch seine Gabel laeuft. Im
    # Modell steht alles in der Stellung von oben: Portal in der Mitte,
    # Toolhead bei xw_mitte.
    b = w('rahmen_b')
    L['nut_u_z'] = L['rahmen_z0'] + b / 2.0            # untere Seitennut
    L['nut_o_z'] = L['rahmen_z1'] - b / 2.0            # obere: Y-Riemen
    L['aussen_x'] = R + b / 2.0                         # rechtes 2040 aussen
    L['tisch_z'] = L['quer_z'][0]
    L['y_weg_hinten'] = L['wagen_y0'] - L['y_schiene_y'][0]
    L['schalt_dy'] = -(L['y_weg_hinten'] - w('schaltabstand'))
    L['schalt_dy_ende'] = -L['y_weg_hinten']
    L['schalt_xs'] = L['xw_min'] + w('schaltabstand')
    pl, pb, pd = w('ls_pcb_laenge'), w('ls_pcb_breite'), w('ls_pcb_dicke')
    r = w('ls_pcb_rand')
    s, gb = w('ls_schlitz') / 2.0, w('ls_gabel_breite') / 2.0

    # Y: Fahne auf der Platte, am Schaltpunkt der Strahl an ihrer Hinterkante
    L['fy_y_rel'] = (w('fy_hinten'), w('fy_hinten') + w('fy_laenge'))
    L['fy_y'] = tuple(y + L['schalt_dy'] for y in L['fy_y_rel'])
    L['ly_strahl_y'] = L['fy_y'][0]
    xg = L['aussen_x'] + w('gy_mitte_aussen')          # Spaltmitte
    zp = L['rahmen_z1'] - w('ly_unter_kante')           # Oberseite Platine
    L['gy_x'] = xg
    L['ly_pcb_x'] = (xg - pb / 2.0, xg + pb / 2.0)
    L['ly_pcb_z'] = (zp - pd, zp)
    # Gabel an der vorderen Stirnkante (dorther kommt die Fahne), Strahl in
    # ihrer Mitte; die Platine reicht von dort nach hinten.
    g1 = L['ly_strahl_y'] + w('ls_gabel_dicke') / 2.0
    L['ly_gabel_y'] = (g1 - w('ls_gabel_dicke'), g1)
    L['ly_pcb_y'] = (g1 + w('ls_gabel_rand') - pl, g1 + w('ls_gabel_rand'))
    L['ly_gabel_z'] = (zp, zp + w('ls_gabel_hoehe'))
    L['ly_strahl_z'] = zp + w('ls_strahl_hoehe')
    L['ly_boden_z'] = zp + w('ls_schlitz_boden')
    L['ly_arme_x'] = [(xg - gb, xg - s), (xg + s, xg + gb)]
    L['ly_loecher'] = [(L['ly_pcb_x'][0] + r, L['ly_pcb_y'][0] + r),
                       (L['ly_pcb_x'][1] - r, L['ly_pcb_y'][0] + r)]

    # Halter Y
    rand = w('hy_rand')
    L['hy_y'] = (L['ly_pcb_y'][0] - rand, L['ly_pcb_y'][1] + rand)
    L['hy_boden_z'] = (L['ly_pcb_z'][0] - w('hy_boden'), L['ly_pcb_z'][0])
    L['hy_boden_x'] = (L['aussen_x'], L['ly_pcb_x'][1] + rand)
    L['hy_fuss_x'] = (L['aussen_x'], L['aussen_x'] + w('hy_fuss_dicke'))
    L['hy_fuss_z'] = (L['rahmen_z0'] + w('hy_fuss_unten'),
                      L['hy_boden_z'][1])
    L['hy_m5'] = [(y, L['nut_u_z']) for y in (L['hy_y'][0] + w('hy_m5_rand'),
                                            L['hy_y'][1] - w('hy_m5_rand'))]
    # mit Scheibe (1) wie am Y-Motorhalter: Fuss 6, dann 5 mm in die Nut —
    # 1,8 Lippe, 3,2 im Stein, 1 mm vor dem Nutgrund
    L['hy_m5_schraube'] = 12.0
    # Tasche fuer die Loetstifte der Gabel, so breit wie die Platine
    L['hy_tasche'] = (L['ly_pcb_x'][0], L['ly_pcb_x'][1],
                      L['ly_gabel_y'][0] - 0.75, L['ly_gabel_y'][1] + 0.75)
    fa = w('hy_fase')
    L['hy_fase_pkt'] = [(L['hy_fuss_x'][1], L['hy_boden_z'][0]),
                        (L['hy_fuss_x'][1] + fa, L['hy_boden_z'][0]),
                        (L['hy_fuss_x'][1], L['hy_boden_z'][0] - fa)]

    # Fahne Y: Klammer um die Kante der rechten Schlittenplatte, Blatt aussen
    pz0, pz1 = L['platte_z0'], L['platte_z1']
    L['platte_z'] = (pz0, pz1)
    L['platte_x1'] = R + w('platte_aussen')
    L['y_wagen_x1'] = R + w('y_wagen_breite') / 2.0
    sp = w('kl_spiel') / 2.0
    L['fy_innen_z'] = (pz0 - sp, pz1 + sp)              # Maul der Klammer
    L['fy_wand_x'] = (L['platte_x1'] + w('kl_kante'),
                      xg + w('fahne_dicke') / 2.0)
    L['fy_backe_o_x'] = (L['platte_x1'] - w('fy_backe_innen'),
                         L['fy_wand_x'][1])
    L['fy_backe_o_z'] = (L['fy_innen_z'][1],
                         L['fy_innen_z'][1] + w('fy_backe_o'))
    L['fy_backe_u_x'] = (L['y_wagen_x1'] + w('fy_wagen_luft'),
                         L['fy_wand_x'][1])
    L['fy_backe_u_z'] = (L['fy_innen_z'][0] - w('fy_backe_u'),
                         L['fy_innen_z'][0])
    L['fy_blatt_x'] = (xg - w('fahne_dicke') / 2.0, xg + w('fahne_dicke') / 2.0)
    L['fy_blatt_z'] = (zp + w('fahne_ab_platine'), L['fy_backe_u_z'][0])
    # Madenschraube mitten ueber dem Plattenrand neben dem Wagen
    L['fy_einsatz_x'] = (L['fy_backe_o_x'][0] + L['platte_x1']) / 2.0
    L['fy_einsatz_y_rel'] = sum(L['fy_y_rel']) / 2.0

    # X: Lichtschranke senkrecht vor dem linken Ende der 2020. Die Platine
    # endet hx_luft_wagen vor dem Wagen, wenn er am Schienenende steht; die
    # Gabel an ihrer rechten Stirnkante (dorther kommt die Fahne), Spalt
    # waagerecht.
    x_rohr0 = -w('profil_laenge') / 2.0
    x_schiene0 = L['x_schiene_x'][0]
    px1 = x_schiene0 - w('hx_luft_wagen')
    L['lx_pcb_x'] = (px1 - pl, px1)
    L['hx_y_rel'] = (L['portal_y'], L['portal_y'] + w('hx_dicke'))
    yb = L['hx_y_rel'][1]                               # Rueckseite Platine
    L['lx_pcb_y_rel'] = (yb, yb + pd)
    L['lx_pcb_z'] = (-pb / 2.0, pb / 2.0)
    L['lx_gabel_x'] = (px1 - w('ls_gabel_rand') - w('ls_gabel_dicke'),
                       px1 - w('ls_gabel_rand'))
    L['lx_strahl_x'] = sum(L['lx_gabel_x']) / 2.0
    L['lx_gabel_y_rel'] = (yb + pd, yb + pd + w('ls_gabel_hoehe'))
    L['lx_strahl_y_rel'] = yb + pd + w('ls_strahl_hoehe')
    L['lx_boden_y_rel'] = yb + pd + w('ls_schlitz_boden')
    L['lx_arme_z'] = [(-gb, -s), (s, gb)]
    L['lx_loecher'] = [(L['lx_pcb_x'][0] + r, z) for z in
                       (L['lx_pcb_z'][0] + r, L['lx_pcb_z'][1] - r)]

    # Halter X: Block vor der 2020, stoesst an das Schienenende
    L['hx_x'] = (L['lx_pcb_x'][0] - w('hx_rand'), x_schiene0)
    L['hx_z'] = (-w('hx_h') / 2.0, w('hx_h') / 2.0)
    # M5 mitten im freien Stueck links der Schiene, auf der Nut; ohne
    # Scheibe (Kopf in der Senkung): 5,8 Block, dann 6,2 in die Nut —
    # 1,8 Lippe, 4 im Stein, 1,3 vor dem Grund
    L['hx_m5_x'] = (x_rohr0 + x_schiene0) / 2.0
    L['hx_m5_schraube'] = 12.0
    L['hx_zunge_x'] = (x_rohr0 + 0.5, x_schiene0 - 0.75)
    L['hx_tasche'] = (L['lx_gabel_x'][0] - 0.75, L['lx_gabel_x'][1] + 0.75,
                      -gb - 0.75, gb + 0.75)

    # Klammer X (relativ zur X-Wagenmitte; Z absolut)
    xt = w('traeger_x_links')
    ty1 = w('traeger_dicke')
    ry1 = ty1 + w('rippe_t')                            # Vorderseite Rippe
    L['kx_innen_x'] = xt - w('kl_kante')                # Seitenwand innen
    L['kx_wand_x'] = (L['kx_innen_x'] - w('kx_wand'), L['kx_innen_x'])
    L['kx_innen_y'] = (-w('kl_spiel') / 2.0, ry1 + w('kl_spiel') / 2.0)
    L['kx_backe_h_y'] = (L['kx_innen_y'][0] - w('kx_backe_h'),
                         L['kx_innen_y'][0])
    L['kx_backe_v_y'] = (L['kx_innen_y'][1],
                         L['kx_innen_y'][1] + w('kx_backe_v'))
    L['kx_backe_x'] = (L['kx_wand_x'][0], L['kx_innen_x'] + w('kx_breite'))
    # hintere Backe endet unter dem Wagen; ueber dem Wagen (Z -16..16) bleibt
    # die Wand vor der Platte, 45 Grad dazwischen (druckt ohne Stuetzen)
    L['kx_steg_y0'] = w('kx_wagen_luft')
    uebergang = L['kx_steg_y0'] - L['kx_backe_h_y'][0]
    L['kx_backe_h_z'] = (w('kx_z0'), -w('x_wagen_breite') / 2.0
                         - w('kx_wagen_luft') - uebergang)
    L['kx_backe_v_z'] = (w('kx_z0'), w('kx_z1'))
    # Fahne X: Blatt waagerecht mitten im Spalt; die Spitze erreicht den
    # Strahl, wenn der Wagen am Schaltpunkt steht
    L['fx_z'] = (-w('fahne_dicke') / 2.0, w('fahne_dicke') / 2.0)
    L['fx_spitze_rel'] = L['lx_strahl_x'] - L['schalt_xs']
    L['fx_y_rel'] = (L['lx_pcb_y_rel'][1] + w('fahne_ab_platine'),
                     L['lx_gabel_y_rel'][1] + w('fahne_ueber_gabel'))
    L['fx_x_rel'] = (L['fx_spitze_rel'], L['kx_innen_x'])
    # Kopf unter dem Blatt, links ueber die Wand hinaus, mit Fase darunter
    kz1 = L['fx_z'][0]
    L['kx_kopf_x'] = (L['kx_wand_x'][0] - w('kx_kopf_b'), L['kx_innen_x'])
    L['kx_kopf_z'] = (kz1 - w('kx_kopf_h'), kz1)
    L['kx_kopf_fase_z'] = L['kx_kopf_z'][0] - w('kx_kopf_b')
    L['kx_steg_z1'] = L['kx_kopf_z'][0]
    # vordere Madenschraube mitten auf die Seitenrippe
    L['kx_einsatz_v'] = ((L['kx_innen_x'] + xt + w('rippe_b')) / 2.0,
                         (w('kx_z0') + w('kx_z1')) / 2.0)
    L['kx_einsatz_kopf'] = ((L['kx_kopf_x'][0] + L['kx_wand_x'][1]) / 2.0,
                            sum(L['fx_y_rel']) / 2.0)
    L['fx_schraube'] = 8.0          # Blatt 3 + 5 im Einsatz

    # ---- Energiekette X (seit Rev. 19) ---------------------------------------
    # Bewegtes Ende: das Gelenk des Anfangsstuecks xk_gelenk_x rechts der
    # X-Wagenmitte, das Endstueck reicht nach links. Der Festpunkt (Endstueck
    # 180) liegt in der Mitte des Wegs dieses Gelenks, der Untertrum laeuft
    # von dort nach rechts in den Bogen. Im Untertrum liegt der Boden der
    # Glieder oben: sie liegen auf ihren Riegeln.
    yv, zb = w('xk_y_vorn'), w('xk_boden_z')
    L['xk_y'] = (yv - w('kette_b'), yv)
    L['xk_y_mitte'] = yv - w('kette_b') / 2.0
    L['xk_achse_unten'] = zb + w('kette_riegel') + w('kette_h') / 2.0
    L['xk_achse_oben'] = L['xk_achse_unten'] + 2.0 * w('kette_r')
    L['xk_unter_z'] = (zb, zb + w('kette_riegel') + w('kette_h'))
    L['xk_ober_z'] = (L['xk_achse_oben'] - w('kette_h') / 2.0,
                      L['xk_achse_oben'] + w('kette_h') / 2.0
                      + w('kette_riegel'))
    L['xk_bogen_z'] = (L['xk_achse_unten'] + L['xk_achse_oben']) / 2.0
    L['xk_bogen_r'] = (w('kette_r') - w('kette_h') / 2.0,
                       w('kette_r') + w('kette_h') / 2.0 + w('kette_riegel'))
    L['xk_hub'] = L['xw_max'] - L['xw_min']
    L['xk_fest'] = L['xw_mitte'] + w('xk_gelenk_x')
    # Glieder: halber Hub plus Bogen, auf ganze Glieder aufgerundet
    L['xk_noetig'] = L['xk_hub'] / 2.0 + math.pi * w('kette_r')
    L['xk_glieder'] = int(math.ceil(L['xk_noetig'] / w('kette_teilung')
                                    - 1e-9))
    L['xk_laenge'] = L['xk_glieder'] * w('kette_teilung')
    L['xk_schlupf'] = L['xk_laenge'] - L['xk_noetig']
    L['xk_bogen_x'] = (xk_bogen(L, L['xw_min']), xk_bogen(L, L['xw_max']))
    # Endstueck 180 am Festpunkt: Platte unten auf der Wanne, die Loecher
    # links neben dem Gelenk
    a, ab = w('endstueck_loch_a'), w('endstueck_loch_ab')
    L['xk_fest_loecher'] = [(L['xk_fest'] - a, L['xk_y_mitte']),
                            (L['xk_fest'] - a - ab, L['xk_y_mitte'])]
    # Wanne: Boden unter dem Untertrum, vorn luft_bau vor der Traegerplatte.
    # Sie beginnt wanne_rand vor dem Endstueck (dort kommen die Kabel herein)
    # und endet luft_bau vor dem Lagerschlitten: ihr Boden liegt nur 0,25 mm
    # hoeher als er, die Kette im Bogen 3,25.
    sp, wd = w('kette_spiel'), w('wanne_wand')
    L['wanne_innen_y'] = (L['xk_y'][0] - sp, L['xk_y'][1] + sp)
    L['wanne_y'] = (L['wanne_innen_y'][0] - wd, L['wanne_innen_y'][1] + wd)
    L['wanne_boden_z'] = (zb - w('wanne_boden'), zb)
    L['wanne_z'] = (zb - w('wanne_boden'), zb + w('wanne_wand_h'))
    L['ls_innen_x'] = R - (L['rolle_u'][1] + L['ls_u_rel'][1])
    L['wanne_x'] = (L['xk_fest'] - w('endstueck_l') - w('wanne_rand'),
                    L['ls_innen_x'] - w('luft_bau'))
    # Stuetzen: Platte hinten am Rohr (M5 in einer Hammermutter der hinteren
    # Nut), Block auf dem Rohr hinter dem Ruecklauf, Arm vorn unter der Wanne
    L['st_platte_y'] = (L['profil_y0'] - w('st_platte'), L['profil_y0'])
    L['st_platte_z'] = (L['kern_z'] - w('st_unten'), L['wanne_z'][0])
    L['st_block_y'] = (L['profil_y0'], w('st_block_y'))
    L['st_block_z'] = (L['profil_z1'], L['wanne_z'][0])
    L['st_arm_y'] = (w('st_block_y'), w('st_arm_vorn'))
    L['st_arm_z'] = (L['wanne_z'][0] - w('st_arm'), L['wanne_z'][0])
    xl = [x for x, _ in L['xk_fest_loecher']]
    L['st_x'] = {
        'Festpunkt': (min(xl) - w('st_rand'), max(xl) + w('st_rand')),
        'mitte': (w('st_x_mitte') - w('st_b') / 2.0,
                  w('st_x_mitte') + w('st_b') / 2.0),
        'rechts': (w('st_x_rechts') - w('st_b') / 2.0,
                   w('st_x_rechts') + w('st_b') / 2.0)}
    # Laschen der Wanne hinter ihrer Rueckwand, auf den Bloecken der
    # beiden anderen Stuetzen; die Schraube mitten im Block
    yl = (L['st_block_y'][0] + L['st_block_y'][1]) / 2.0
    L['wanne_lasche_y'] = (L['wanne_y'][0] - w('wanne_lasche'),
                           L['wanne_y'][0])
    L['wanne_laschen'] = [(w(n), yl) for n in ('st_x_mitte', 'st_x_rechts')]
    # Schrauben: Endstueck -> Wanne -> Arm (Scheibe, Platte, Boden, dann
    # >= 4 mm im Einsatz; der Arm ist nur so dick wie der Einsatz lang),
    # Lasche -> Block, Platte -> Hammermutter
    L['xk_fest_klemm'] = (w('m3_scheibe_h') + w('endstueck_platte')
                          + w('wanne_boden'))
    L['xk_fest_schraube'] = normlaenge(L['xk_fest_klemm'] + 4.0, M3_LAENGEN)
    L['wanne_schraube'] = normlaenge(w('wanne_boden') + 5.0, M3_LAENGEN)
    L['st_m5_schraube'] = normlaenge(w('st_platte') + w('nut_lippe')
                                     + w('nutenstein_h'), M5_LAENGEN)

    # ---- Kabelfluegel an der Stuetze am Festpunkt (seit Rev. 21) -----------
    # Fluegel links an der Platte der Stuetze, ueber dem Rohr. Davor laufen
    # die Litzen hoch, je ein Kabelbinder durch die zwei Schlitze links und
    # rechts von ihnen. Oben laufen sie ueber den Riemen nach vorn, knapp
    # ueber dem Wannenboden in das offene linke Ende der Wanne.
    xs0, tb = L['st_x']['Festpunkt'][0], w('kf_binder_t')
    xr = xs0 - w('kf_steg') - tb / 2.0
    xl = xr - tb - w('kf_buendel_b')
    L['kf_x'] = (xl - tb / 2.0 - w('kf_steg'), xs0)
    L['kf_y'] = L['st_platte_y']
    L['kf_z'] = (L['profil_z1'], L['st_platte_z'][1])
    L['kf_schlitze'] = [(x, z) for x in (xl, xr)
                        for z in (w('kf_binder_z1'), w('kf_binder_z2'))]
    L['kf_buendel_x'] = (xl + tb / 2.0, xr - tb / 2.0)
    L['kf_buendel_y'] = (L['kf_y'][1], L['kf_y'][1] + w('kf_buendel_t'))
    L['kf_quer_z'] = (L['xk_unter_z'][0] + 1.0,
                      L['xk_unter_z'][0] + 1.0 + w('kf_buendel_t'))
    # in der oberen Nut: von rechts neben Rueckwand und Motorhalter des
    # linken Schlittens bis links neben den Kabelfluegel
    L['kf_nut_x'] = (-(L['R'] - L['rueck_u'][1]) + w('luft_bau'),
                     L['kf_buendel_x'][0] - w('kf_steg'))

    # ---- Energiekette Y (seit Rev. 21) -------------------------------------
    # Kette aussen neben der Platte des linken Y-Schlittens. Hoehen: der
    # Halter liegt auf der Platte, der Obertrum darauf, der Untertrum 2 R
    # tiefer auf den Riegeln in der Wanne.
    xa = -(L['platte_x1'] + w('yk_abstand'))
    L['yk_x'] = (xa - w('kette_b'), xa)
    L['yk_x_mitte'] = xa - w('kette_b') / 2.0
    L['khy_z'] = (L['platte_z1'], L['platte_z1'] + w('khy_dicke'))
    zo = L['khy_z'][1]
    L['yk_ober_z'] = (zo, zo + w('kette_h') + w('kette_riegel'))
    L['yk_achse_oben'] = zo + w('kette_h') / 2.0
    L['yk_achse_unten'] = L['yk_achse_oben'] - 2.0 * w('kette_r')
    zu = L['yk_achse_unten'] - w('kette_h') / 2.0 - w('kette_riegel')
    L['yk_unter_z'] = (zu, zu + w('kette_riegel') + w('kette_h'))
    L['yk_bogen_z'] = (L['yk_achse_unten'] + L['yk_achse_oben']) / 2.0
    # Laenge aus Arbeitsweg und Reserve; der Festpunkt so, dass am hinteren
    # Schienenende luft_bau Untertrum bleibt. yk_dy_*: Stellung des Portals
    # aus der Mitte (wie y_weg_hinten), yk_frei: Unter- plus Obertrum.
    hinten, vorn, lb = L['y_weg_hinten'], w('y_weg_vorn'), w('luft_bau')
    pr = math.pi * w('kette_r')
    L['yk_noetig'] = (hinten + vorn + w('yk_reserve') + 2.0 * lb) / 2.0 + pr
    L['yk_glieder'] = int(math.ceil(L['yk_noetig'] / w('kette_teilung')
                                    - 1e-9))
    L['yk_laenge'] = L['yk_glieder'] * w('kette_teilung')
    frei = L['yk_laenge'] - pr
    L['yk_frei'] = frei
    L['yk_dy_fest'] = -hinten + frei - 2.0 * lb
    L['yk_fest'] = w('yk_gelenk_y') + L['yk_dy_fest']
    L['yk_dy_bereich'] = (L['yk_dy_fest'] - frei, L['yk_dy_fest'] + frei)
    L['yk_reserve_vorn'] = L['yk_dy_bereich'][1] - vorn
    a, ab = w('endstueck_loch_a'), w('endstueck_loch_ab')
    L['yk_fest_loecher'] = [(L['yk_x_mitte'], L['yk_fest'] - a),
                            (L['yk_x_mitte'], L['yk_fest'] - a - ab)]
    # Wanne Y: hinten ywanne_hinten Boden hinter dem Endstueck 180 (Binder-
    # schlitze), vorn so weit, wie der Untertrum am Ende der Kette reicht
    sp = w('kette_spiel')
    L['ywanne_innen_x'] = (L['yk_x'][0] - sp, L['yk_x'][1] + sp)
    L['ywanne_x'] = (L['ywanne_innen_x'][0] - w('wanne_wand'),
                     L['ywanne_innen_x'][1] + w('wanne_wand'))
    L['ywanne_boden_z'] = (zu - w('wanne_boden'), zu)
    L['ywanne_z'] = (zu - w('wanne_boden'), zu + w('wanne_wand_h'))
    L['ywanne_y'] = (L['yk_fest'] - w('endstueck_l') - w('ywanne_hinten'),
                     L['yk_fest'] + frei + lb)
    L['ywanne_binder'] = [(L['yk_x_mitte'] + s * w('khy_binder_abstand') / 2.0,
                           L['ywanne_y'][0] + w('ywanne_hinten') / 2.0)
                          for s in (-1, 1)]
    L['ywanne_lasche_x'] = (L['ywanne_x'][1],
                            L['ywanne_x'][1] + w('ywanne_lasche'))
    # Laschen vor der M5 des Traegers, damit sich die Koepfe nicht treffen
    xlm = sum(L['ywanne_lasche_x']) / 2.0
    L['ywanne_laschen'] = [(xlm, w(n) + w('ytr_versatz'))
                           for n in ('ytr_y_mitte', 'ytr_y_vorn')]
    # Traeger Y: Wand an der Aussenseite des 2040 (M5 in der unteren
    # Seitennut), der Arm nach aussen unter die Wanne. Die Wand reicht von
    # ytr_m5_rand unter der M5 (der Kopf liegt ganz auf) bis an den Arm; mit
    # R 20 sitzt der Arm oben, die Wanne liegt hoeher als die Nut.
    xf = -L['aussen_x']
    L['ytr_wand_x'] = (xf - w('ytr_wand'), xf)
    L['ytr_arm_x'] = (L['ywanne_x'][0] - 1.0, xf - w('ytr_wand'))
    L['ytr_arm_z'] = (L['ywanne_z'][0] - w('ytr_arm'), L['ywanne_z'][0])
    zn = L['nut_u_z']
    L['ytr_wand_z'] = (min(zn - w('ytr_m5_rand'), L['ytr_arm_z'][0]),
                       max(zn + w('ytr_m5_rand'), L['ytr_arm_z'][1]))
    yl = [y for _, y in L['yk_fest_loecher']]
    hb = w('ytr_b') / 2.0
    L['ytr_y'] = {
        'Festpunkt': (min(yl) - w('st_rand'), max(yl) + w('st_rand')),
        'mitte': (w('ytr_y_mitte') - hb, w('ytr_y_mitte') + hb),
        'vorn': (w('ytr_y_vorn') - hb, w('ytr_y_vorn') + hb)}
    # M5: am Festpunkt in der Mitte (die Einsaetze liegen aussen unter dem
    # Endstueck), sonst ytr_versatz hinter der Mitte
    L['ytr_m5_y'] = {
        'Festpunkt': sum(L['ytr_y']['Festpunkt']) / 2.0,
        'mitte': w('ytr_y_mitte') - w('ytr_versatz'),
        'vorn': w('ytr_y_vorn') - w('ytr_versatz')}
    L['ytr_m5_schraube'] = normlaenge(w('ytr_wand') + w('nut_lippe')
                                      + w('nutenstein_h'), M5_LAENGEN)
    # Kettenhalter Y auf der Platte des linken Schlittens (Portal in der
    # Mitte): aussen die Leiste, innen liegt er khy_auflage_b breit auf, vorn
    # endet er vor dem Stirnblock. Das Anfangsstueck liegt mit der Platte
    # nach unten zwischen den Leisten, sein Gelenk bei yk_gelenk_y.
    yg = w('yk_gelenk_y')
    L['khy_leiste_aussen_x'] = (L['ywanne_innen_x'][0] - w('khy_leiste'),
                               L['ywanne_innen_x'][0])
    L['khy_leiste_innen_x'] = (L['ywanne_innen_x'][1], -L['platte_x1'])
    L['khy_x'] = (L['khy_leiste_aussen_x'][0],
                 -L['platte_x1'] + w('khy_auflage_b'))
    L['khy_y'] = (yg - w('endstueck_l') - w('khy_hinten'),
                 L['stirn_y'][0] - 0.5)
    L['khy_ende_y'] = (yg - w('endstueck_l'), yg + w('endstueck_auge'))
    L['khy_leiste_y'] = (L['khy_ende_y'][0], L['khy_y'][1])
    L['khy_leiste_z'] = (zo, zo + w('khy_leiste_h'))
    L['khy_loecher'] = [(L['yk_x_mitte'], yg - a),
                       (L['yk_x_mitte'], yg - a - ab)]
    L['khy_binder'] = [(L['yk_x_mitte'] + s * w('khy_binder_abstand') / 2.0,
                       yg - w('endstueck_l') - w('khy_hinten') / 2.0)
                      for s in (-1, 1)]
    xsy = -L['platte_x1'] + w('khy_auflage_b') / 2.0
    L['khy_schrauben'] = [(xsy, w('khy_schraube_y1')),
                         (xsy, L['khy_binder'][0][1])]
    L['khy_schraube'] = normlaenge(w('platte_dicke') + 5.0, M3_LAENGEN)
    L['khy_ende_schraube'] = normlaenge(w('m3_scheibe_h')
                                        + w('endstueck_platte') + 4.0,
                                        M3_LAENGEN)
    return L


# Normlaengen fuer die Schraubenwahl am Y-Motorhalter
M3_LAENGEN = (6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40)
M5_LAENGEN = (8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50)


def normlaenge(mindest, reihe):
    """Kuerzeste Normlaenge, die mindestens `mindest` lang ist."""
    for laenge in reihe:
        if laenge >= mindest - 1e-6:
            return float(laenge)
    return float(reihe[-1])


def xk_bogen(L, xw):
    """X, an dem der Obertrum der X-Kette in den Bogen geht, wenn die
    X-Wagenmitte bei xw steht: Untertrum (Festpunkt -> Bogen) und Obertrum
    (Bogen -> bewegtes Gelenk) teilen sich die Kette ohne den Bogen."""
    return (L['xk_fest'] + xw + w('xk_gelenk_x') + L['xk_laenge']
            - math.pi * w('kette_r')) / 2.0


def lage_y_motorhalter():
    """Der Y-Motorhalter in SEINEN Koordinaten (bis Rev. 15 YMotorhalter.py):
    X = 0 ist die Mitte der 2040 (das Teil ist symmetrisch), Y = 0 ihre
    Stirnseite, +Y zeigt vom Profil weg, Z = 0 ihre Unterkante. lage()
    legt ihn an beide vorderen Ecken; tools/y_motorhalter_check.py prueft
    ihn in diesen Koordinaten."""
    H = {}
    halb = w('rahmen_b') / 2.0

    # ---- Profil: je Seitenflaeche zwei Nuten im 20er Raster; in der OBEREN
    #      laeuft der Riemen, in die UNTERE kommen die Nutensteine ---------
    H['profil_name'] = '20{:.0f}'.format(w('rahmen_h'))
    H['nut_unten_z'] = halb
    H['nut_oben_z'] = w('rahmen_h') - halb
    # Unterkante der oberen Nutoeffnung: bis hierhin darf der Halter an der
    # Seitenflaeche reichen, darueber bleibt sie fuer den Riemen frei
    H['nut_oben_z0'] = H['nut_oben_z'] - w('nut_b') / 2.0

    # ---- Riemen: laeuft in den oberen Nuten, Mitte = Nutmitte ------------
    H['riemen_z'] = H['nut_oben_z']
    H['riemen_z0'] = H['riemen_z'] - w('riemen_breite') / 2.0
    H['riemen_z1'] = H['riemen_z'] + w('riemen_breite') / 2.0
    # Der Riemen umschlingt das Ritzel mit der Zahnseite: Wirklinie auf dem
    # Teilkreis, Ruecken aussen, Zahnspitzen innen.
    H['rp'] = w('ritzel_teilkreis') / 2.0
    H['zaehne'] = int(round(math.pi * w('ritzel_teilkreis')
                            / w('riemen_teilung')))
    H['wirk_ruecken'] = (w('riemen_dicke') - w('riemen_zahn_h')
                         - w('riemen_pld'))
    H['wirk_zahn'] = w('riemen_pld') + w('riemen_zahn_h')
    # Ritzel mittig: beide Trume laufen parallel zur 2040 in ihre Nuten.
    # Lage im Nutkanal, gemessen ab der Seitenflaeche nach innen.
    H['trum_ruecken_x'] = H['rp'] + H['wirk_ruecken']
    H['trum_zahn_x'] = H['rp'] - H['wirk_zahn']
    H['trum_tiefe_ruecken'] = halb - H['trum_ruecken_x']
    H['trum_tiefe_zahn'] = halb - H['trum_zahn_x']
    H['luft_lippe'] = H['trum_tiefe_ruecken'] - w('nut_lippe')
    H['luft_nutgrund'] = w('nut_tiefe') - H['trum_tiefe_zahn']
    H['zaehne_im_eingriff'] = H['zaehne'] / 2.0          # 180 Grad
    H['mm_pro_umdrehung'] = H['zaehne'] * w('riemen_teilung')

    # ---- Ritzel auf der Motorwelle, Nabe nach unten: die Spur sitzt in
    #      Riemenmitte, darunter Bord und Nabe mit den Madenschrauben ------
    nabe = w('ritzel_laenge') - w('ritzel_spur') - 2.0 * w('ritzel_bord')
    H['ritzel_nabe'] = nabe
    H['ritzel_z0'] = (H['riemen_z'] - w('ritzel_spur') / 2.0
                      - w('ritzel_bord') - nabe)
    H['ritzel_z1'] = H['ritzel_z0'] + w('ritzel_laenge')
    H['madenschraube_z'] = H['ritzel_z0'] + nabe / 2.0

    # ---- Motor: die gemessene Welle reicht genau durch das ganze Ritzel;
    #      daraus folgt die Hoehe des Flansches und damit der Platte -------
    H['welle_z1'] = H['ritzel_z1']
    H['motor_flansch_z'] = H['welle_z1'] - w('motor_welle_ist')
    H['motor_z0'] = H['motor_flansch_z'] - w('motor_laenge')
    H['bund_z1'] = H['motor_flansch_z'] + w('motor_bund_h')
    H['flach_z0'] = H['welle_z1'] - w('motor_flach_l')

    # ---- Platte und Halter in Z: Joch, Schenkel und Fuehrungswaende enden
    #      oben buendig mit der Platte, diese Flaeche liegt beim Druck auf
    #      dem Bett ---------------------------------------------------------
    H['platte_z0'] = H['motor_flansch_z']
    H['platte_z1'] = H['platte_z0'] + w('ymh_platte_dicke')
    H['ritzel_luft'] = H['ritzel_z0'] - H['platte_z1']
    H['halter_z0'] = w('ymh_rand_unten')
    H['halter_z1'] = H['platte_z1']

    # ---- Breite (X) --------------------------------------------------------
    H['wange_x0'] = halb + w('spiel_locker') / 2.0
    H['wange_x1'] = H['wange_x0'] + w('ymh_wange_dicke')
    H['fuehrung_x0'] = w('motor_flansch') / 2.0 + w('ymh_luft_min')
    H['halbe_breite'] = H['fuehrung_x0'] + w('ymh_fuehrung_dicke')

    # ---- Laenge (Y): der Motor haengt in Hoehe des Profils und bleibt
    #      deshalb ganz vor der Stirnseite, vor dem Joch, das an ihr
    #      anliegt --------------------------------------------------------------
    H['wange_y0'] = -w('ymh_wange_laenge')
    H['joch_y1'] = w('ymh_joch_dicke')
    H['motor_y_min'] = (H['joch_y1'] + w('ymh_luft_min')
                        + w('motor_flansch') / 2.0)
    H['motor_y_max'] = H['motor_y_min'] + w('ymh_spann_weg')
    H['motor_y_mitte'] = (H['motor_y_min'] + H['motor_y_max']) / 2.0
    H['platte_y1'] = (H['motor_y_max'] + w('motor_flansch') / 2.0
                      + w('ymh_rand_vorn'))

    # ---- Lochbilder: M5 in die untere Nut, je Schenkel zwei (Y, Z) ---------
    H['m5_loecher'] = [(-(w('ymh_schraube_y')
                          + i * w('ymh_schraube_abstand')), H['nut_unten_z'])
                       for i in range(2)]
    H['n_m5'] = 2 * len(H['m5_loecher'])
    h = w('motor_loch') / 2.0
    H['motor_langloecher'] = [(sx * h, H['motor_y_mitte'] + sy * h)
                              for sy in (-1, 1) for sx in (-1, 1)]
    H['bund_schlitz_b'] = w('motor_bund_d') + w('spiel_locker')

    # ---- Schrauben: M5 mit Scheibe durch den Schenkel und den Spalt zur
    #      Seitenflaeche, ueber die Lippe in den Nutenstein; die Motor-
    #      schrauben von oben durch Scheibe und Platte in den Flansch ------
    H['m5_klemm'] = (w('m5_scheibe_h') + w('ymh_wange_dicke')
                     + w('spiel_locker') / 2.0)
    H['m5_schraube'] = normlaenge(H['m5_klemm'] + w('nut_lippe') + 3.0,
                                  M5_LAENGEN)
    H['m5_ueberstand'] = H['m5_schraube'] - H['m5_klemm']
    H['m5_eingriff'] = (min(H['m5_ueberstand'],
                            w('nut_lippe') + w('nutenstein_h'))
                        - w('nut_lippe'))
    H['motor_klemm'] = w('ymh_platte_dicke') + w('m3_scheibe_h')
    H['motor_schraube'] = normlaenge(H['motor_klemm'] + 3.0, M3_LAENGEN)
    H['motor_eingriff'] = H['motor_schraube'] - H['motor_klemm']
    H['riemen_verstellung'] = 2.0 * w('ymh_spann_weg')
    return H


def y_riemen_weg(L, dy=0.0):
    """Weg des offenen Y-Riemens einer Seite auf der Wirklinie, das Portal
    dy aus der Mitte verschoben (u ab der Schienenmitte nach innen wie
    oben; beide Ritzel mittig zur 2040, u = 0). In der vorderen Klemme
    laeuft er gerade, dann schraeg an das Ritzel des Motors (tangential,
    innen), um dessen Vorderseite, als Ruecklauf gerade in der aeusseren
    oberen Nut (u = -r), um das hintere Ritzel und schraeg in die hintere
    Klemme. 'winkel' ist die Lage des Tangentenpunkts auf dem Teilkreis
    (rad, 0 = innen), 'schraeg' die Neigung des Trums gegen Y in Grad."""
    r = w('ritzel_teilkreis') / 2.0
    uk = L['yr_wirk_u']
    g = {'r': r, 'uk': uk}
    for teil, yc, yk, ye_ in (
            ('vorn', L['ym_y'], L['kt_y_vorn'][1] + dy,
             L['yr_ende_vorn'] + dy),
            ('hinten', L['yh_y'], L['kt_y_hinten'][0] + dy,
             L['yr_ende_hinten'] + dy)):
        d = math.hypot(uk, yk - yc)
        phi = math.atan2(yk - yc, uk)
        beta = math.acos(r / d)
        a = max((phi + beta, phi - beta), key=math.cos)    # innen, u > 0
        tu, tv = r * math.cos(a), yc + r * math.sin(a)
        g[teil] = {'ritzel_y': yc, 'klemme': (uk, yk), 'ende': (uk, ye_),
                   'winkel': a, 'tangente': (tu, tv),
                   'trum': math.sqrt(d * d - r * r),
                   'schraeg': math.degrees(math.atan2(uk - tu,
                                                      abs(tv - yk))),
                   'in_klemme': abs(yk - ye_)}
    # Umschlingung: vorn vom Tangentenpunkt ueber die Vorderseite bis u = -r,
    # hinten von dort ueber die Rueckseite bis zum Tangentenpunkt
    g['vorn']['bogen'] = math.pi - g['vorn']['winkel']
    g['hinten']['bogen'] = math.pi + g['hinten']['winkel']
    g['ruecklauf'] = L['ym_y'] - L['yh_y']
    v, h = g['vorn'], g['hinten']
    g['laenge'] = (v['in_klemme'] + v['trum'] + r * v['bogen']
                   + g['ruecklauf'] + r * h['bogen'] + h['trum']
                   + h['in_klemme'])
    return g


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
              'Gummi': 1.25,                   # nur die Riemen der Referenz
              'Leiterplatte': 1.85,            # nur Referenz: FR4
              'Kunststoff': 1.10}              # nur Referenz: Gabel
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


def langloecher_y(comp, name, punkte, d, weg, z0, z1, ziel):
    """Senkrechte Langloecher Ø d laengs Maschinen-Y von z0 bis z1, je
    Punkt (X, Y) um +-weg: zwei Kreise plus Rechteck wie bei langloch_x,
    alle Profile geschnitten — die Vereinigung ist das Loch."""
    m = (z0 + z1) / 2.0
    sk = skizze(comp, _ebene(comp, 'z', m, 'E_{}_Z{:.1f}'.format(
        comp.name, m)), 'Sk_' + name)
    r = d / 2.0
    for x, y in punkte:
        kreis(sk, x, y - weg, d)
        kreis(sk, x, y + weg, d)
        rechteck(sk, x - r, y - weg, x + r, y + weg)
    tasche(comp, alle_profile(sk), abs(z1 - z0), ziel)


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


def langloch_quer(sk, u, v, breite_mm, hub_mm):
    """Langloch laengs u: zwei Kreise plus Rechteck, beim Schneiden werden
    alle Profile entfernt (wie langloch_senkrecht in ToolheadZ.py)."""
    r = breite_mm / 2.0
    kreis(sk, u - hub_mm, v, breite_mm)
    kreis(sk, u + hub_mm, v, breite_mm)
    rechteck(sk, u - hub_mm, v - r, u + hub_mm, v + r)


# Farbe fuer die Riemen der Referenz. Namen der Bibliothek sind lokalisiert,
# deshalb mehrere Kandidaten; findet sich keiner, bleibt die Optik des
# Materials. Wird in run() geleert (gehoert zum Dokument).
SCHWARZ = ('Rubber - Black', 'Gummi - schwarz', '(Black)', '(Schwarz)')
_AUSSEHEN = {}


def aussehen(app, design, koerper, kandidaten):
    """Appearance aus der Bibliothek zuweisen — nur Optik, scheitert still."""
    try:
        if kandidaten not in _AUSSEHEN:
            _AUSSEHEN[kandidaten] = None
            libs = app.materialLibraries
            for kand in kandidaten:
                for j in range(libs.count):
                    aps = libs.item(j).appearances
                    for i in range(aps.count):
                        a = aps.item(i)
                        if kand.lower() in a.name.lower():
                            _AUSSEHEN[kandidaten] = \
                                design.appearances.addByCopy(a, a.name)
                            break
                    if _AUSSEHEN[kandidaten]:
                        break
                if _AUSSEHEN[kandidaten]:
                    break
        if _AUSSEHEN[kandidaten]:
            koerper.appearance = _AUSSEHEN[kandidaten]
    except:
        pass


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

    # Wagenschrauben und Schrauben der Klemmtuerme: Durchgang + Senkung
    # von oben, der Kopf verschwindet in der Platte (die des Klemmturms
    # liegen unter dem Rohr).
    for name, lagen in (('Wagen', L['wagen_loecher']),
                        ('Klemmturm_hinten', L['kt_schrauben_hinten']),
                        ('Klemmturm_vorn', L['kt_schrauben_vorn'])):
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

    # Einsaetze fuer Motorhalter bzw. Spannbock, von oben in den Stirnblock
    pkt = [(xu(u), y) for u, y in L['halter_schrauben']]
    bohrung(comp, 'Halter_Einsatz_' + n, 'z', pkt, w('insert_m3_d'),
            L['wand_z1'] - w('insert_tief_t'), L['wand_z1'] + 1.0, k)

    # Kettenhalter Y (seit Rev. 21, nur links): 2x M3 von unten durch die
    # Platte, aussen neben dem Y-Wagen. Ein neu gedruckter Schlitten hat
    # die Loecher; in einen schon gedruckten bohrt man sie mit
    # Bohrlehre_Kettenhalter_Y (dasselbe Lochbild khy_schrauben).
    if s < 0:
        bohrung(comp, 'Kettenhalter_Y_' + n, 'z', L['khy_schrauben'],
                w('m3_durchgang'), L['platte_z0'] - 1.0,
                L['platte_z1'] + 1.0, k)

    # Anschlag fuer den Motorhalter (seit Rev. 24, nur links): steht innen
    # neben seiner aeusseren Saeule auf dem Stirnblock und nimmt den
    # Riemenzug auf, der den Halter nach innen schiebt
    if s < 0:
        quader(comp, 'Anschlag_Motorhalter', xb(L, s, *L['mha_u']),
               L['mha_y'], L['mha_z'], 'dazu', k)

    fussfase(comp, k, 'y', L['platte_z0'], w('fase_fuss'), fehler,
             'Schlitten ' + n)
    bbox_pruefen(k, 'Schlitten ' + n,
                 (x_platte, (L['platte_y0'], L['platte_y1']),
                  (L['platte_z0'],
                   L['mha_z'][1] if s < 0 else L['wand_z1'])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_klemmturm(app, design, comp, L, s, t, fehler):
    """Y-Klemmturm wie in v8, t = 'vorn' oder 'hinten' — beide gleich:
    senkrechter Schlitz auf der Riemenlinie, unten und an beiden Enden
    offen, Rippen an der Wand zur Schiene (dorthin zeigen die Zaehne),
    Querstift Ø3 unter dem Riemen. Riemenende von unten in den Schlitz
    druecken, dann den Stift von innen quer durchschieben — er traegt den
    Riemen. Befestigt mit zwei M3 von oben durch die Platte.

    Drucklage: Oberseite (Plattenseite) aufs Bett. Der Schlitz oeffnet nach
    oben, die Rippen stehen senkrecht, die Stiftbohrung liegt waagerecht."""
    n = seite(s)
    name = 'Klemmturm_{}_{}'.format(t, n)
    xu = lambda u: xs(L, s, u)
    x_turm = xb(L, s, *L['kt_u'])
    ty = L['kt_y_' + t]
    k = quader(comp, name, x_turm, ty, L['kt_z'], 'neu').bodies.item(0)
    k.name = name

    # Klemmschlitz ueber die ganze Laenge, unten offen
    quader(comp, 'Schlitz_' + name, xb(L, s, L['yr_rippe_u0'],
                                        L['yr_wand_u']),
           (ty[0] - 1.0, ty[1] + 1.0),
           (L['kt_z'][0] - 1.0, L['yr_decke_z']), 'weg', k)
    xr = xb(L, s, L['yr_rippe_u0'], L['yr_rippe_u1'])
    rippen(comp, 'Rippen_' + name,
           [(xr[0], y, xr[1], y + w('klemm_rippe_b'))
            for y in L['kt_rippen_y_' + t]],
           L['kt_z'][0], L['yr_decke_z'], k)
    # Querstift unter dem Riemen, von innen durch beide Waende
    a0, a1 = xb(L, s, L['kt_u'][0] - 1.0, L['kt_u'][1] + 1.0)
    bohrung(comp, 'Stift_' + name, 'x',
            [(L['kt_stift_y_' + t], L['stift_z'])], w('klemm_stift_d'),
            a0, a1, k)
    # Gewindeeinsaetze fuer die Schrauben von der Platte, von oben
    bohrung(comp, 'Einsatz_' + name, 'z',
            [(xu(u), y) for u, y in L['kt_schrauben_' + t]],
            w('insert_m3_d'), L['kt_z'][1] - w('insert_m3_t'),
            L['kt_z'][1] + 1.0, k)

    fussfase(comp, k, 'y', L['kt_z'][1], w('fase_fuss'), fehler,
             name.replace('_', ' '))
    bbox_pruefen(k, name.replace('_', ' '), (x_turm, ty, L['kt_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_motorhalter(app, design, comp, L, fehler):
    """X-Motor stehend ueber dem linken Rohrende, Welle nach unten. Das
    Ritzel sitzt mit der Nabe nach oben, seine Spur in Riemenhoehe.

    Die Motorplatte ist duenn, und die Nabe taucht in ihre Bundbohrung
    (Ø22,4 um den Bord Ø16): so reicht die 20-mm-Welle durch das ganze
    Ritzel. Die Madenschrauben liegen unter der Platte und sind von vorn
    erreichbar; das Ritzel passt auch mit dem Motor von oben durch die
    Bohrung.

    Die Motorplatte ruht auf zwei Saeulen: hinten hinter den hinteren
    Motorschrauben, aussen neben den aeusseren. So bleiben alle vier
    Schrauben von unten erreichbar, und die Platte ist an zwei Kanten
    gehalten — der Riemenzug greift unter ihr am Ritzel an und wuerde eine
    nur hinten gehaltene Platte verdrillen. Befestigt mit 2x M3 von oben
    in die Einsaetze des Stirnblocks; die Koepfe liegen neben dem Flansch.
    Seit Rev. 24 liegt die aeussere Saeule innen am Anschlag des linken
    Schlittens: Er nimmt den Riemenzug auf, die Schrauben halten den
    Halter nur noch nieder. Der Halter selbst ist unveraendert.

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


def bau_y_motorhalter(app, design, comp, L, s, fehler):
    """Y-Motorhalter vorn an der 2040 (bis Rev. 15 YMotorhalter.py, Rev. 5),
    ein Druckteil, symmetrisch zur Mitte der 2040: links und rechts dasselbe
    Teil, zweimal drucken.

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
    H = L['ymh']
    n = seite(s)
    name = 'Y-Motorhalter_' + n
    xm, ye, zu = s * L['R'], L['rahmen_y'][1], L['rahmen_z0']
    hb = H['halbe_breite']
    za, ze = zu + H['halter_z0'], zu + H['halter_z1']
    pz = (zu + H['platte_z0'], zu + H['platte_z1'])
    k = quader(comp, 'Y-Motorplatte_' + n, (xm - hb, xm + hb),
               (ye, ye + H['platte_y1']), pz, 'neu').bodies.item(0)
    k.name = name
    quader(comp, 'Y-Joch_' + n, (xm - hb, xm + hb), (ye, ye + H['joch_y1']),
           (za, ze), 'dazu', k)
    for sx in (-1, 1):
        a = sorted((xm + sx * H['wange_x0'], xm + sx * H['wange_x1']))
        quader(comp, 'Y-Schenkel_{}{:+d}'.format(n, sx), a,
               (ye + H['wange_y0'], ye), (za, ze), 'dazu', k)
        f = sorted((xm + sx * H['fuehrung_x0'], xm + sx * hb))
        quader(comp, 'Y-Fuehrung_{}{:+d}'.format(n, sx), f,
               (ye, ye + H['platte_y1']), (za, ze), 'dazu', k)
    # M5 fuer die Nutensteine: quer durch beide Schenkel
    bohrung(comp, 'Y-Schenkel_M5_' + n, 'x',
            [(ye + y, zu + z) for y, z in H['m5_loecher']],
            w('m5_durchgang'), xm - H['wange_x1'] - 1.0,
            xm + H['wange_x1'] + 1.0, k)
    # Zentrierbund und Motorschrauben: Langloecher laengs der 2040
    weg = w('ymh_spann_weg') / 2.0
    langloecher_y(comp, 'Y-Motor_Bund_' + n, [(xm, ye + H['motor_y_mitte'])],
                  H['bund_schlitz_b'], weg, pz[0] - 1.0, pz[1] + 1.0, k)
    langloecher_y(comp, 'Y-Motor_Schrauben_' + n,
                  [(xm + x, ye + y) for x, y in H['motor_langloecher']],
                  w('m3_durchgang'), weg, pz[0] - 1.0, pz[1] + 1.0, k)
    fussfase(comp, k, 'y', ze, w('fase_fuss'), fehler,
             name.replace('_', ' '))
    bbox_pruefen(k, name.replace('_', ' '),
                 ((xm - hb, xm + hb), (ye + H['wange_y0'],
                                       ye + H['platte_y1']), (za, ze)),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def traene(sk, u, v, d_mm, richtung=1.0):
    """Tropfenloch fuer liegend gedruckte Bohrungen: Kreis plus Spitze in
    Druckrichtung (+v bei richtung=1), Flanken etwas steiler als 45 Grad.
    Die Ecken der Spitze liegen knapp im Kreis, damit die Profile sauber
    entstehen; beim Schneiden aller Profile ergibt die Vereinigung das
    Loch (wie langloch_x)."""
    r = d_mm / 2.0
    c = 0.95 * r * math.sqrt(0.5)
    kreis(sk, u, v, d_mm)
    vieleck(sk, [(u - c, v + richtung * c),
                 (u, v + richtung * r * math.sqrt(2.0)),
                 (u + c, v + richtung * c)])


def traenen(comp, name, punkte, d, z0, z1, ziel):
    """Senkrechte Bohrung(en) Ø d von z0 bis z1 als Traene mit der Spitze
    nach +Y — der Lagerschlitten wird auf dem Ruecken liegend gedruckt."""
    m = (z0 + z1) / 2.0
    sk = skizze(comp, _ebene(comp, 'z', m, 'E_{}_Z{:.1f}'.format(
        comp.name, m)), 'Sk_' + name)
    for u, v in punkte:
        traene(sk, u, v, d)
    tasche(comp, alle_profile(sk), abs(z1 - z0), ziel)


def bau_spannbock(app, design, comp, L, fehler):
    """Fester Anschlag der Zugschraube rechts: Boden auf Rohrende, Rueckwand
    und Stirnblock (2x M3 von oben in dessen Einsaetze), innen eine Wand.
    Die M3 geht von aussen durch die Wand in den Gewindeeinsatz im Ruecken
    des Lagerschlittens; ganz gespannt bleibt der Schlitten 0,5 mm vor der
    Wand.

    Drucklage: Boden aufs Bett."""
    s = +1
    xu = lambda u: xs(L, s, u)
    k = quader(comp, 'SB_Boden', xb(L, s, *L['sb_u']), L['sb_y'],
               L['sb_boden_z'], 'neu').bodies.item(0)
    k.name = 'Spannbock'
    quader(comp, 'SB_Wand', xb(L, s, *L['sb_wand_u']), L['sb_wand_y'],
           L['sb_wand_z'], 'dazu', k)
    bohrung(comp, 'SB_Zugschraube', 'x', [(L['zug_y'], L['zug_z'])],
            w('m3_durchgang'), *xb(L, s, L['sb_wand_u'][0] - 1.0,
                                   L['sb_wand_u'][1] + 1.0), k)
    bohrung(comp, 'SB_Schrauben', 'z',
            [(xu(u), y) for u, y in L['halter_schrauben']],
            w('m3_durchgang'), L['wand_z1'] - 1.0, L['sb_boden_z'][1] + 1.0,
            k)
    fussfase(comp, k, 'y', L['wand_z1'], w('fase_fuss'), fehler, 'Spannbock')
    bbox_pruefen(k, 'Spannbock',
                 (xb(L, s, *L['sb_u']), L['sb_y'],
                  (L['wand_z1'], L['sb_wand_z'][1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_lagerschlitten(app, design, comp, L, fehler):
    """X-Umlenkung rechts: Rahmen um das Umlenkritzel. Unten ein Arm mit dem
    Gleitlager, oben einer mit dem Kugellager (von unten eingepresst,
    darueber eine Decke mit dem Durchgang fuer die Welle), hinten der
    Ruecken mit dem Gewindeeinsatz der Zugschraube, vorn ein Pfosten.
    Innen (zum X-Wagen) und aussen offen: dort laeuft der Riemen hinein und
    um das Ritzel. Der Schlitten liegt auf dem Rohr, eine Feder unter dem
    unteren Arm laeuft in der oberen Nut. Gezeichnet in der Mitte des
    Spannwegs.

    Drucklage: auf dem Ruecken liegend. Die Lagersitze liegen dann
    waagerecht und sind als Traene ausgefuehrt, der Pfosten wird eine
    kurze Bruecke zwischen den Armen."""
    s = +1
    ua = w('rolle_u')
    xu = lambda u: xs(L, s, u)
    x_ls = xb(L, s, ua + L['ls_u_rel'][0], ua + L['ls_u_rel'][1])
    k = quader(comp, 'LS_unten', x_ls, L['ls_y'], L['ls_unten_z'],
               'neu').bodies.item(0)
    k.name = 'Lagerschlitten'
    zm = (L['ls_unten_z'][1], L['ls_oben_z'][0])
    quader(comp, 'LS_oben', x_ls, L['ls_y'], L['ls_oben_z'], 'dazu', k)
    quader(comp, 'LS_Ruecken', x_ls, L['ls_ruecken_y'], zm, 'dazu', k)
    quader(comp, 'LS_Pfosten', x_ls, L['ls_pfosten_y'], zm, 'dazu', k)
    # Feder in der oberen Nut des Rohrs, hinten unter 45 Grad
    fy, fz, t = L['ls_feder_y'], L['ls_feder_z'], w('ls_feder_t')
    fu = L['ls_feder_u_rel']
    prisma_vieleck(comp, 'LS_Feder', 'x',
                   [(fy[0], fz[1]), (fy[1], fz[1]), (fy[1], fz[0]),
                    (fy[0] + t, fz[0])],
                   *xb(L, s, ua + fu[0], ua + fu[1]), 'dazu', k)
    # Lagersitze (Presspassung) und Durchgang der Welle in der Decke
    achse = [(xu(ua), L['xr_yc'])]
    traenen(comp, 'LS_Gleitlager', achse, w('gl_d') + w('spiel_press'),
            L['ls_unten_z'][0] - 1.0, L['ls_unten_z'][1] + 1.0, k)
    traenen(comp, 'LS_Kugellager', achse, w('kl_d') + w('spiel_press'),
            L['kl_z'][0] - 1.0, L['kl_z'][1], k)
    traenen(comp, 'LS_Welle', achse, w('uw_d') + 1.0, L['kl_z'][1] - 0.5,
            L['ls_oben_z'][1] + 1.0, k)
    # Zugschraube: Gewindeeinsatz von aussen, dahinter Durchgang bis innen
    e = L['ls_einsatz_u_rel']
    bohrung(comp, 'LS_Einsatz', 'x', [(L['zug_y'], L['zug_z'])],
            w('insert_m3_d'), *xb(L, s, ua + e[0] - 1.0, ua + e[1]), k)
    bohrung(comp, 'LS_Zugschraube', 'x', [(L['zug_y'], L['zug_z'])],
            w('m3_durchgang'), *xb(L, s, ua + e[1] - 0.5,
                                   ua + L['ls_u_rel'][1] + 1.0), k)
    fussfase(comp, k, 'z', L['ls_y'][0], w('fase_fuss'), fehler,
             'Lagerschlitten')
    bbox_pruefen(k, 'Lagerschlitten',
                 (x_ls, L['ls_y'], (L['ls_feder_z'][0], L['ls_oben_z'][1])),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


# --- Energiekette X (seit Rev. 19) ---------------------------------------------
def bau_kettenwanne(app, design, comp, L, fehler):
    """Wanne fuer den Untertrum der X-Kette: U-Profil, oben und an den Enden
    offen, direkt hinter der Traegerplatte ueber Riemen und Riemenhalter. Sie
    liegt auf den Armen der drei Stuetzen. Am Festpunkt schrauben die beiden
    M3 des Endstuecks 180 sie mit auf den Arm, an den anderen Stuetzen je
    eine M3 durch eine Lasche hinter der Rueckwand in den Block.

    Drucklage: Boden aufs Bett, die Waende stehen darauf."""
    x, yi, y = L['wanne_x'], L['wanne_innen_y'], L['wanne_y']
    zb, z = L['wanne_boden_z'], L['wanne_z']
    k = quader(comp, 'Wanne_Boden', x, y, zb, 'neu').bodies.item(0)
    k.name = 'Kettenwanne'
    quader(comp, 'Wanne_Wand_hinten', x, (y[0], yi[0]), (zb[1], z[1]), 'dazu',
           k)
    quader(comp, 'Wanne_Wand_vorn', x, (yi[1], y[1]), (zb[1], z[1]), 'dazu', k)
    hb = w('wanne_lasche_b') / 2.0
    for i, (xl, _) in enumerate(L['wanne_laschen']):
        quader(comp, 'Wanne_Lasche_{}'.format(i + 1), (xl - hb, xl + hb),
               L['wanne_lasche_y'], zb, 'dazu', k)
    bohrung(comp, 'Wanne_Laschen_M3', 'z', L['wanne_laschen'],
            w('m3_durchgang'), zb[0] - 1.0, zb[1] + 1.0, k)
    bohrung(comp, 'Wanne_Festpunkt_M3', 'z', L['xk_fest_loecher'],
            w('m3_durchgang'), zb[0] - 1.0, zb[1] + 1.0, k)
    fussfase(comp, k, 'y', zb[0], w('fase_fuss'), fehler, 'Kettenwanne')
    bbox_pruefen(k, 'Kettenwanne', (x, (L['wanne_lasche_y'][0], y[1]), z),
                 fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_stuetze(app, design, comp, L, n, fehler):
    """Stuetze der Kettenwanne, n = 'Festpunkt', 'mitte' oder 'rechts':
    Platte hinten am Rohr (M5 in einer Hammermutter der hinteren Nut), Block
    auf dem Rohr hinter dem Ruecklauf des X-Riemens, Arm vorn unter dem
    Wannenboden — ueber Riemen und Riemenhalter hinweg. In der Innenecke
    eine Fase in die Stuetze hinein: die Kante des Rohrs sitzt nicht auf,
    ob sie gerundet ist oder scharf. Am Festpunkt breiter, mit den beiden
    Einsaetzen fuer das Endstueck 180 im Arm; sonst ein Einsatz oben im
    Block fuer die Lasche der Wanne. Am Festpunkt dazu links der
    Kabelfluegel (seit Rev. 21): vor ihm laufen die Litzen aus der oberen
    Nut hoch, zwei Kabelbinder durch je zwei Schlitze halten sie.

    Drucklage: Rueckseite der Platte aufs Bett. Block und Arm stehen darauf,
    die M5-Bohrung steht senkrecht, der Fluegel liegt flach."""
    x = L['st_x'][n]
    py, pz = L['st_platte_y'], L['st_platte_z']
    by, bz = L['st_block_y'], L['st_block_z']
    ay, az = L['st_arm_y'], L['st_arm_z']
    f = w('profil_fase')
    punkte = [(py[0], pz[0]), (py[1], pz[0]), (py[1], bz[0] + f),
              (py[1] + f, bz[0]), (by[1], bz[0]), (by[1], az[0]),
              (ay[1], az[0]), (ay[1], az[1]), (py[0], az[1])]
    k = prisma_vieleck(comp, 'ST_Profil_' + n, 'x', punkte, x[0], x[1],
                       'neu').bodies.item(0)
    k.name = 'Wannenstuetze_' + n
    x_aussen = x
    if n == 'Festpunkt':
        quader(comp, 'ST_Kabelfluegel', L['kf_x'], L['kf_y'], L['kf_z'],
               'dazu', k)
        tb, bb = w('kf_binder_t') / 2.0, w('kf_binder_b') / 2.0
        prismen(comp, 'ST_Kabelbinder', 'y',
                [(xk - tb, zk - bb, xk + tb, zk + bb)
                 for xk, zk in L['kf_schlitze']],
                L['kf_y'][0] - 1.0, L['kf_y'][1] + 1.0, 'weg', k)
        x_aussen = (L['kf_x'][0], x[1])
    xm = (x[0] + x[1]) / 2.0
    bohrung(comp, 'ST_M5_' + n, 'y', [(xm, L['kern_z'])], w('m5_durchgang'),
            py[0] - 1.0, py[1] + 1.0, k)
    if n == 'Festpunkt':
        bohrung(comp, 'ST_Einsaetze_' + n, 'z', L['xk_fest_loecher'],
                w('insert_m3_d'), az[0] - 1.0, az[1] + 1.0, k)
    else:
        lasche = [p for p in L['wanne_laschen'] if x[0] < p[0] < x[1]]
        bohrung(comp, 'ST_Einsatz_' + n, 'z', lasche, w('insert_m3_d'),
                bz[1] - w('insert_m3_t'), bz[1] + 1.0, k)
    fussfase(comp, k, 'z', py[0], w('fase_fuss'), fehler,
             'Wannenstuetze ' + n)
    bbox_pruefen(k, 'Wannenstuetze ' + n,
                 (x_aussen, (py[0], ay[1]), (pz[0], az[1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k



# --- Energiekette Y (seit Rev. 21) ---------------------------------------------
def bau_kettenhalter_y(app, design, comp, L, fehler):
    """Kettenhalter Y: traegt das bewegte Ende der Y-Kette. Eine 8 mm dicke
    Platte liegt hinter dem Stirnblock auf der Platte des linken Y-Schlittens
    und reicht nach aussen unter das Anfangsstueck; zwei Leisten fuehren
    es. Das Anfangsstueck liegt mit der Platte nach unten darauf, 2x M3 +
    Scheibe in Gewindeeinsaetze von oben. Dahinter zwei Schlitze fuer den
    Kabelbinder der Zugentlastung.

    Befestigung: 2x M3 von unten durch die Schlittenplatte in Einsaetze im
    Halter (aussen neben dem Y-Wagen). Ein schon gedruckter Schlitten wird
    mit Bohrlehre_Kettenhalter_Y nachgebohrt.

    Drucklage: Unterseite (Auflage auf dem Schlitten) aufs Bett."""
    z0, z1 = L['khy_z']
    k = quader(comp, 'KHY_Platte', L['khy_x'], L['khy_y'], L['khy_z'],
               'neu').bodies.item(0)
    k.name = 'Kettenhalter_Y'
    for name, xl in (('aussen', L['khy_leiste_aussen_x']),
                     ('innen', L['khy_leiste_innen_x'])):
        quader(comp, 'KHY_Leiste_' + name, xl, L['khy_leiste_y'],
               L['khy_leiste_z'], 'dazu', k)
    bohrung(comp, 'KHY_Einsaetze_Ende', 'z', L['khy_loecher'],
            w('insert_m3_d'), z1 - w('insert_m3_t'), z1 + 1.0, k)
    tb, bb = w('khy_binder_t') / 2.0, w('khy_binder_b') / 2.0
    prismen(comp, 'KHY_Binder', 'z',
            [(x - tb, y - bb, x + tb, y + bb) for x, y in L['khy_binder']],
            z0 - 1.0, z1 + 1.0, 'weg', k)
    bohrung(comp, 'KHY_Einsaetze_Schlitten', 'z', L['khy_schrauben'],
            w('insert_m3_d'), z0 - 1.0, z0 + w('insert_m3_t'), k)
    fussfase(comp, k, 'y', z0, w('fase_fuss'), fehler, 'Kettenhalter Y')
    bbox_pruefen(k, 'Kettenhalter Y',
                 (L['khy_x'], L['khy_y'], (z0, L['khy_leiste_z'][1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_kettenwanne_y(app, design, comp, L, fehler):
    """Wanne fuer den Untertrum der Y-Kette, aussen am linken 2040 zwischen
    den beiden 2060. Oben und an den Enden offen; hinten liegt der
    Festpunkt (Endstueck 180, 2x M3 durch Endstueck und Boden in den
    Traeger darunter), dahinter zwei Schlitze fuer den Kabelbinder. Innen
    (zum 2040 hin) zwei Laschen, je eine M3 in den Traeger darunter.

    Drucklage: Boden aufs Bett, laengs."""
    x, xi, y = L['ywanne_x'], L['ywanne_innen_x'], L['ywanne_y']
    zb, z = L['ywanne_boden_z'], L['ywanne_z']
    k = quader(comp, 'WanneY_Boden', x, y, zb, 'neu').bodies.item(0)
    k.name = 'Kettenwanne_Y'
    quader(comp, 'WanneY_Wand_aussen', (x[0], xi[0]), y, (zb[1], z[1]),
           'dazu', k)
    quader(comp, 'WanneY_Wand_innen', (xi[1], x[1]), y, (zb[1], z[1]),
           'dazu', k)
    hb = w('wanne_lasche_b') / 2.0
    for i, (_, yl) in enumerate(L['ywanne_laschen']):
        quader(comp, 'WanneY_Lasche_{}'.format(i + 1), L['ywanne_lasche_x'],
               (yl - hb, yl + hb), zb, 'dazu', k)
    bohrung(comp, 'WanneY_Laschen_M3', 'z', L['ywanne_laschen'],
            w('m3_durchgang'), zb[0] - 1.0, zb[1] + 1.0, k)
    bohrung(comp, 'WanneY_Festpunkt_M3', 'z', L['yk_fest_loecher'],
            w('m3_durchgang'), zb[0] - 1.0, zb[1] + 1.0, k)
    tb, bb = w('khy_binder_t') / 2.0, w('khy_binder_b') / 2.0
    prismen(comp, 'WanneY_Binder', 'z',
            [(xb_ - tb, yb_ - bb, xb_ + tb, yb_ + bb)
             for xb_, yb_ in L['ywanne_binder']],
            zb[0] - 1.0, zb[1] + 1.0, 'weg', k)
    fussfase(comp, k, 'y', zb[0], w('fase_fuss'), fehler, 'Kettenwanne Y')
    bbox_pruefen(k, 'Kettenwanne Y',
                 ((x[0], L['ywanne_lasche_x'][1]), y, z), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_traeger_y(app, design, comp, L, n, fehler):
    """Traeger der Wanne Y, n = 'Festpunkt', 'mitte' oder 'vorn': eine Wand
    an der Aussenseite des linken 2040 (1x M5 in eine Hammermutter der
    unteren Seitennut) und darunter ein Arm nach aussen unter die Wanne.
    Am Festpunkt zwei Einsaetze fuer das Endstueck 180 im Arm, sonst einer
    fuer die Lasche der Wanne.

    Drucklage: die freie Seite des Arms aufs Bett, die Wand steht darauf
    (seit Rev. 22 sitzt der Arm oben: seine Oberseite liegt auf dem Bett)."""
    y = L['ytr_y'][n]
    k = quader(comp, 'TrY_Wand_' + n, L['ytr_wand_x'], y, L['ytr_wand_z'],
               'neu').bodies.item(0)
    k.name = 'Wannentraeger_Y_' + n
    quader(comp, 'TrY_Arm_' + n, L['ytr_arm_x'], y, L['ytr_arm_z'], 'dazu', k)
    bohrung(comp, 'TrY_M5_' + n, 'x', [(L['ytr_m5_y'][n], L['nut_u_z'])],
            w('m5_durchgang'),
            L['ytr_wand_x'][0] - 1.0, L['ytr_wand_x'][1] + 1.0, k)
    if n == 'Festpunkt':
        pkt = L['yk_fest_loecher']
    else:
        pkt = [p for p in L['ywanne_laschen'] if y[0] < p[1] < y[1]]
    bohrung(comp, 'TrY_Einsaetze_' + n, 'z', pkt, w('insert_m3_d'),
            L['ytr_arm_z'][0] - 1.0, L['ytr_arm_z'][1] + 1.0, k)
    # aufs Bett kommt die Seite des Arms, von der die Wand nicht weggeht
    unten = L['ytr_wand_z'][0] >= L['ytr_arm_z'][0]
    bett = L['ytr_arm_z'][0] if unten else L['ytr_arm_z'][1]
    fussfase(comp, k, 'y', bett, w('fase_fuss'), fehler,
             'Wannentraeger Y ' + n)
    bbox_pruefen(k, 'Wannentraeger Y ' + n,
                 ((L['ytr_arm_x'][0], L['ytr_wand_x'][1]), y,
                  L['ytr_wand_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


# --- Endschalter X und Y (bis Rev. 14 in Endschalter.py) -----------------------
def bau_halter_y(app, design, comp, L, fehler):
    """Halter der Y-Lichtschranke aussen am rechten 2040, hinter dem hinteren
    2060. Der Fuss liegt an der Aussenflaeche und haengt mit 2 x M5 in
    Hammermuttern der UNTEREN Nut; ueber der Platine endet er, die obere Nut
    (Ruecklauf des Y-Riemens) bleibt frei. Der Boden steht waagerecht nach
    aussen, die Platine liegt darauf, die Gabel zeigt nach oben und nach
    vorn — von dort kommt die Fahne.

    Drucklage: Fussflaeche (die Seite am Profil) aufs Bett, der Boden steht
    senkrecht nach oben — keine Stuetzen, die M5-Loecher werden rund."""
    fx, fz = L['hy_fuss_x'], L['hy_fuss_z']
    bx, bz = L['hy_boden_x'], L['hy_boden_z']
    y = L['hy_y']
    k = quader(comp, 'Fuss_Y', fx, y, fz, 'neu').bodies.item(0)
    k.name = 'Halter_Y'
    quader(comp, 'Boden_Y', bx, y, bz, 'dazu', k)
    prisma_vieleck(comp, 'Fase_Y', 'y', L['hy_fase_pkt'], y[0], y[1], 'dazu',
                   k)
    bohrung(comp, 'M5_Y', 'x', L['hy_m5'], w('m5_durchgang'), fx[0] - 1.0,
            fx[1] + 1.0, k)
    tx0, tx1, ty0, ty1 = L['hy_tasche']
    prismen(comp, 'Tasche_Y', 'z', [(tx0, ty0, tx1, ty1)],
            bz[1] - w('ls_pin_tasche'), bz[1] + 1.0, 'weg', k)
    # Einpressbohrung fuer die M2-Einsaetze, dahinter die Freibohrung
    bohrung(comp, 'Einsatz_Y', 'z', L['ly_loecher'], w('ls_pcb_loch_d'),
            bz[1] - w('ls_pcb_loch_t'), bz[1] + 1.0, k)
    bohrung(comp, 'Frei_Y', 'z', L['ly_loecher'], w('ls_pcb_frei_d'),
            bz[0] - 1.0, bz[1], k)
    fussfase(comp, k, 'x', L['aussen_x'], w('fase_fuss'), fehler, 'Halter_Y')
    bbox_pruefen(k, 'Halter_Y', ((fx[0], bx[1]), y, (fz[0], bz[1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_fahne_y(app, design, comp, L, fehler):
    """Fahne der Y-Achse: Klammer um die Aussenkante der rechten
    Schlittenplatte, das Blatt haengt aussen neben dem 2040 in die Gabel.
    Die untere Backe bleibt neben dem Y-Wagen, die obere liegt auf dem
    Plattenrand; eine Madenschraube M3 in ihrem Einsatz klemmt. Laengs der
    Kante verschiebbar — so wird der Schaltpunkt eingestellt. Im Modell
    steht das Portal in der Mitte: die Fahne sitzt auf der Platte, nicht in
    der Gabel.

    Drucklage: eine Stirnseite aufs Bett, das ganze Profil steht senkrecht —
    keine Stuetzen. SCHWARZ drucken: helles PETG laesst das Infrarot der
    Schranke durch."""
    y = L['fy_y_rel']
    wx, oz, uz = L['fy_wand_x'], L['fy_backe_o_z'], L['fy_backe_u_z']
    k = quader(comp, 'Wand_FY', wx, y, (uz[0], oz[1]), 'neu').bodies.item(0)
    k.name = 'Fahne_Y'
    quader(comp, 'Backe_oben_FY', L['fy_backe_o_x'], y, oz, 'dazu', k)
    quader(comp, 'Backe_unten_FY', L['fy_backe_u_x'], y, uz, 'dazu', k)
    quader(comp, 'Blatt_FY', L['fy_blatt_x'], y, L['fy_blatt_z'], 'dazu', k)
    bohrung(comp, 'Einsatz_FY', 'z', [(L['fy_einsatz_x'],
                                       L['fy_einsatz_y_rel'])],
            w('insert_m3_d'), oz[0] - 1.0, oz[1] + 1.0, k)
    fussfase(comp, k, 'z', y[0], w('fase_fuss'), fehler, 'Fahne_Y')
    bbox_pruefen(k, 'Fahne_Y', ((L['fy_backe_o_x'][0], wx[1]), y,
                                (L['fy_blatt_z'][0], oz[1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    aussehen(app, design, k, SCHWARZ)
    return k


def bau_halter_x(app, design, comp, L, fehler):
    """Halter der X-Lichtschranke vor dem linken Ende der 2020. Ein Block
    liegt an ihrer Vorderseite, eine Zunge fuehrt ihn in der Nut, rechts
    stoesst er an das Ende der X-Schiene: so steht er beim Einbau immer
    gleich, und der Wagen faende dort einen Anschlag, bevor er von der
    Schiene laeuft. Eine M5 mit versenktem Kopf haengt ihn in eine
    Hammermutter. Die Platine sitzt vorn auf zwei M2-Einsaetzen und deckt
    den Kopf ab — erst den Block anschrauben, dann die Lichtschranke.

    Drucklage: Vorderseite (Platinenseite) aufs Bett, die Zunge oben —
    keine Stuetzen."""
    y = L['hx_y_rel']                      # faehrt mit dem Portal
    k = quader(comp, 'Block_X', L['hx_x'], y, L['hx_z'], 'neu').bodies.item(0)
    k.name = 'Halter_X'
    zb = w('hx_zunge_b') / 2.0
    quader(comp, 'Zunge_X', L['hx_zunge_x'], (y[0] - w('hx_zunge_t'), y[0]),
           (-zb, zb), 'dazu', k)
    m5 = [(L['hx_m5_x'], 0.0)]
    bohrung(comp, 'M5_X', 'y', m5, w('m5_durchgang'),
            y[0] - w('hx_zunge_t') - 1.0, y[1] + 1.0, k)
    bohrung(comp, 'M5_Senkung_X', 'y', m5, w('m5_senkung'),
            y[1] - w('hx_senk_t'), y[1] + 1.0, k)
    tx0, tx1, tz0, tz1 = L['hx_tasche']
    prismen(comp, 'Tasche_X', 'y', [(tx0, tz0, tx1, tz1)],
            y[1] - w('ls_pin_tasche'), y[1] + 1.0, 'weg', k)
    bohrung(comp, 'Einsatz_X', 'y', L['lx_loecher'], w('ls_pcb_loch_d'),
            y[1] - w('ls_pcb_loch_t'), y[1] + 1.0, k)
    bohrung(comp, 'Frei_X', 'y', L['lx_loecher'], w('ls_pcb_frei_d'),
            y[1] - w('ls_pcb_loch_t') - 2.5, y[1], k)
    fussfase(comp, k, 'z', y[1], w('fase_fuss'), fehler, 'Halter_X')
    bbox_pruefen(k, 'Halter_X', (L['hx_x'], (y[0] - w('hx_zunge_t'), y[1]),
                                 L['hx_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_klammer_x(app, design, comp, L, fehler):
    """Klammer an der linken unteren Kante der Traegerplatte, unter dem
    X-Wagen: hintere Backe hinter der Platte, Seitenwand an ihrer Kante,
    vordere Backe vor der Seitenrippe, eine Madenschraube M3 in einem
    Einsatz klemmt auf die Rippe. Ueber dem Wagen bleibt die Wand vor der
    Platte (45 Grad dazwischen) und traegt oben den Kopf mit dem Einsatz fuer
    die Fahne. Im Modell am X-Wagen in der Mitte des X-Wegs.

    Drucklage: Unterkante aufs Bett — die Backen stehen senkrecht, die Wand
    wird nach oben schmaler, unter dem Kopf eine 45-Grad-Fase: keine
    Stuetzen. Schwarz wie die Fahne."""
    xs, dy = L['xw_mitte'], 0.0

    def X(a):
        return (a[0] + xs, a[1] + xs)

    def Y(a):
        return (a[0] + dy, a[1] + dy)
    wx = X(L['kx_wand_x'])
    hy0, vy1 = L['kx_backe_h_y'][0] + dy, L['kx_backe_v_y'][1] + dy
    sy0 = L['kx_steg_y0'] + dy
    hz1 = L['kx_backe_h_z'][1]
    pts = [(hy0, w('kx_z0')), (vy1, w('kx_z0')), (vy1, L['kx_steg_z1']),
           (sy0, L['kx_steg_z1']), (sy0, hz1 + (sy0 - hy0)), (hy0, hz1)]
    k = prisma_vieleck(comp, 'Wand_KX', 'x', pts, wx[0], wx[1],
                       'neu').bodies.item(0)
    k.name = 'Klammer_X'
    quader(comp, 'Backe_hinten_KX', X(L['kx_backe_x']), Y(L['kx_backe_h_y']),
           L['kx_backe_h_z'], 'dazu', k)
    quader(comp, 'Backe_vorn_KX', X(L['kx_backe_x']), Y(L['kx_backe_v_y']),
           L['kx_backe_v_z'], 'dazu', k)
    kx0, kx1 = X(L['kx_kopf_x'])
    kz0, kz1 = L['kx_kopf_z']
    pts = [(kx1, kz1), (kx0, kz1), (kx0, kz0), (wx[0], L['kx_kopf_fase_z']),
           (kx1, L['kx_kopf_fase_z'])]
    fy = Y(L['fx_y_rel'])
    prisma_vieleck(comp, 'Kopf_KX', 'y', pts, fy[0], fy[1], 'dazu', k)
    ex, ez = L['kx_einsatz_v']
    by = Y(L['kx_backe_v_y'])
    bohrung(comp, 'Einsatz_KX_vorn', 'y', [(ex + xs, ez)], w('insert_m3_d'),
            by[0] - 1.0, by[1] + 1.0, k)
    ex, ey = L['kx_einsatz_kopf']
    bohrung(comp, 'Einsatz_KX_Kopf', 'z', [(ex + xs, ey + dy)],
            w('insert_m3_d'), kz0, kz1 + 1.0, k)
    fussfase(comp, k, 'y', w('kx_z0'), w('fase_fuss'), fehler, 'Klammer_X')
    bbox_pruefen(k, 'Klammer_X', ((kx0, X(L['kx_backe_x'])[1]), (hy0, vy1),
                                  (w('kx_z0'), kz1)), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    aussehen(app, design, k, SCHWARZ)
    return k


def bau_fahne_x(app, design, comp, L, fehler):
    """Fahne der X-Achse: flaches Blatt auf dem Kopf der Klammer, mit M3x8 in
    dessen Einsatz. Das Langloch (+-fx_verstellung) stellt den Schaltpunkt
    ein; die Spitze laeuft waagerecht mitten durch den Gabelspalt. Im
    Modell am X-Wagen in der Mitte des X-Wegs.

    Drucklage: flach — SCHWARZ drucken."""
    xs, dy = L['xw_mitte'], 0.0
    x = (L['fx_x_rel'][0] + xs, L['fx_x_rel'][1] + xs)
    y = (L['fx_y_rel'][0] + dy, L['fx_y_rel'][1] + dy)
    k = quader(comp, 'Blatt_FX', x, y, L['fx_z'], 'neu').bodies.item(0)
    k.name = 'Fahne_X'
    ex, ey = L['kx_einsatz_kopf']
    zm = sum(L['fx_z']) / 2.0
    sk = skizze(comp, _ebene(comp, 'z', zm, 'E_Fahne_X_Mitte'),
                'Sk_Langloch_FX')
    langloch_quer(sk, ex + xs, ey + dy, w('m3_durchgang'),
                  w('fx_verstellung'))
    tasche(comp, alle_profile(sk), w('fahne_dicke') + 2.0, k)
    fussfase(comp, k, 'y', L['fx_z'][0], w('fase_fuss'), fehler, 'Fahne_X')
    bbox_pruefen(k, 'Fahne_X', (x, y, L['fx_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    aussehen(app, design, k, SCHWARZ)
    return k


def bau_bohrlehren(app, design, comp, L, fehler):
    """Bohrlehre fuer das Lochbild des Y-Wagens (MGN12H, 20 x 20) — zum
    Aufstecken auf den Wagen, bevor die Schlitten gedruckt werden — und fuer
    die Platine der Lichtschranke (Umriss und Lochbild), bevor die Halter
    der Endschalter gedruckt werden: auflegen, beide Loecher muessen
    fluchten. Liegen abseits, ausgeblendet (Konvention SKILL.md).

    Dazu seit Rev. 21 Bohrlehre_Kettenhalter_Y: die zwei Loecher fuer den
    Kettenhalter Y in der Platte eines schon gedruckten linken Schlittens.

    Weitere Lehren gibt es bewusst nicht: alle anderen Verbindungen liegen
    zwischen Teilen dieses Skripts und haengen an denselben Variablen
    (dieselbe Begruendung wie in ToolheadZ.py)."""
    z = L['tisch_z'] - 20.0
    sk = skizze(comp, ebene_z(comp, z, 'E_Bohrlehre_LM393'),
                'Sk_Bohrlehre_LM393')
    rechteck(sk, L['ly_pcb_x'][0], L['ly_pcb_y'][0], L['ly_pcb_x'][1],
             L['ly_pcb_y'][1])
    for x, y in L['ly_loecher']:
        kreis(sk, x, y, w('ls_pcb_frei_d'))
    lehre = neu_mittig(comp, groesstes_profil(sk),
                       w('lehre_dicke')).bodies.item(0)
    lehre.name = 'Bohrlehre_LM393'
    material_zuweisen(app, design, lehre, 'PLA', fehler)
    lehre.isLightBulbOn = False

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

    # Kettenhalter Y: die Lehre liegt auf der Platte des linken Schlittens,
    # eine Lippe fasst ihre Aussenkante, vorn stoesst sie an den Stirnblock.
    # 6 mm dick, damit sie den Bohrer fuehrt. Gebaut 150 mm tiefer (unter
    # dem Tisch), damit sie nicht im Schlitten steckt.
    dz, x0 = -150.0, -L['platte_x1']
    yl = (L['khy_y'][0], L['stirn_y'][0])
    zl = (L['platte_z1'] + dz, L['platte_z1'] + 6.0 + dz)
    lehre = quader(comp, 'Lehre_KHY_Platte', (x0, x0 + 10.0), yl, zl,
                   'neu').bodies.item(0)
    lehre.name = 'Bohrlehre_Kettenhalter_Y'
    quader(comp, 'Lehre_KHY_Lippe', (x0 - 2.5, x0), yl,
           (L['platte_z0'] + dz, zl[1]), 'dazu', lehre)
    bohrung(comp, 'Lehre_KHY_Loecher', 'z', L['khy_schrauben'],
            w('m3_durchgang'), zl[0] - 1.0, zl[1] + 1.0, lehre)
    material_zuweisen(app, design, lehre, 'PLA', fehler)
    lehre.isLightBulbOn = False


# --- Referenz (nicht drucken) --------------------------------------------------
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


def bau_referenz(app, design, teile, L, fehler):
    """Kaufteile und Riemen, nur zur Ansicht — NICHT drucken. teile: die
    Komponenten Ref_Profile, Ref_Fuehrungen, Ref_Riemen, Ref_Antrieb,
    Ref_Endschalter, Ref_Kette (X- und seit Rev. 21 Y-Kette, vereinfacht;
    sie werden nach ihrem eigenen Modell gedruckt).

    Rahmen und Y-Schienen liegen mittig zum Y-Wagen, das vordere 2060
    35 mm hinter der Stirnseite, das hintere 435 mm (Mitte zu Mitte)
    dahinter — die 2040 stehen hinten 110 mm ueber. Der Toolhead (hier
    nur X-Wagen, Riemenhalter und Traegerplatte vereinfacht) steht in der
    Mitte des X-Wegs, das Umlenkritzel und die Y-Motoren in der Mitte ihres
    Spannwegs. Das hintere Y-Ritzel steht, wo es angenommen ist
    (yh_hinter); seine Welle und Lager sind nicht gezeichnet. Die
    Lichtschranken der Endschalter: Y fest am Rahmen, X vor der 2020.

    Jedes Teil wird fuer sich gebaut: scheitert eines, steht das im Bericht
    und das Skript laeuft weiter. Die Druckteile sind dann schon fertig."""
    d = w('riemen_dicke')
    xp, xu, yc = L['x_motor'], L['x_rolle'], L['xr_yc']
    bo, sp, rf = w('ritzel_bord'), w('ritzel_spur'), w('ritzel_flansch_d')

    def sicher(name, bauen, *args):
        try:
            bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))

    def fertig(k, name, erwartet, material, farbe=None):
        k.name = name
        bbox_pruefen(k, name.replace('_', ' '), erwartet, fehler)
        material_zuweisen(app, design, k, material, fehler)
        if farbe:
            aussehen(app, design, k, farbe)

    def profil(name, laengs, bereich, quer, z):
        k = bau_profil(teile['Ref_Profile'], name, laengs, bereich, quer, z)
        fertig(k, name, (bereich, quer, z) if laengs == 'x'
               else (quer, bereich, z), 'Aluminum 6061')

    def box(c, name, x, y, z, material, kanal=None, farbe=None):
        """Quader; kanal = (x, y, z) wird herausgeschnitten (Wagen)."""
        k = quader(c, name, x, y, z, 'neu').bodies.item(0)
        if kanal:
            quader(c, name + '_Kanal', kanal[0], kanal[1], kanal[2], 'weg', k)
        fertig(k, name, (x, y, z), material, farbe)

    def rad(c, name, mitte, stufen, bohrung_d, material):
        """Ritzel: Zylinder (d, z0, z1) uebereinander, mittig
        gebohrt. Die Spur hat den Fuss der Verzahnung als Durchmesser."""
        k = None
        for i, (dm, a0, a1) in enumerate(stufen):
            f = zylinder(c, '{}_{}'.format(name, i), 'z', mitte, dm, a0, a1,
                         'dazu' if k else 'neu', k)
            k = k or f.bodies.item(0)
        z0, z1 = stufen[0][1], stufen[-1][2]
        bohrung(c, name + '_Bohrung', 'z', [mitte], bohrung_d, z0 - 1.0,
                z1 + 1.0, k)
        r = max(dm for dm, _, _ in stufen) / 2.0
        fertig(k, name, ((mitte[0] - r, mitte[0] + r),
                         (mitte[1] - r, mitte[1] + r), (z0, z1)), material)

    def stab(c, name, mitte, d, z, material):
        """Welle: Vollzylinder senkrecht, z = (z0, z1)."""
        k = zylinder(c, name, 'z', mitte, d, z[0], z[1], 'neu').bodies.item(0)
        r = d / 2.0
        fertig(k, name, ((mitte[0] - r, mitte[0] + r),
                         (mitte[1] - r, mitte[1] + r), z), material)

    def x_riemen():
        """Eine Schleife um Ritzel und Umlenkritzel, beide Enden im
        Riemenhalter. Zaehne innen, Wirklinie auf dem Teilkreis."""
        c = teile['Ref_Riemen']
        rw = w('ritzel_teilkreis') / 2.0
        ra, ri = rw + L['riemen_aussen'], rw - L['riemen_innen']
        x0, x1 = L['rh_x']
        sk = skizze(c, _ebene(c, 'z', L['xr_zm'], 'E_Ref_X-Riemen'),
                    'Sk_X-Riemen')
        zug = [((x0, yc + ra), (xp, yc + ra)),
               ((xp, yc + ra), (xp - ra, yc), (xp, yc - ra)),
               ((xp, yc - ra), (xu, yc - ra)),
               ((xu, yc - ra), (xu + ra, yc), (xu, yc + ra)),
               ((xu, yc + ra), (x1, yc + ra)),
               ((x1, yc + ra), (x1, yc + ri)),
               ((x1, yc + ri), (xu, yc + ri)),
               ((xu, yc + ri), (xu + ri, yc), (xu, yc - ri)),
               ((xu, yc - ri), (xp, yc - ri)),
               ((xp, yc - ri), (xp - ri, yc), (xp, yc + ri)),
               ((xp, yc + ri), (x0, yc + ri)),
               ((x0, yc + ri), (x0, yc + ra))]
        for pkt in zug:
            pp = [punkt(sk, u, v) for u, v in pkt]
            if len(pp) == 2:
                sk.sketchCurves.sketchLines.addByTwoPoints(*pp)
            else:
                sk.sketchCurves.sketchArcs.addByThreePoints(*pp)
        k = neu_mittig(c, groesstes_profil(sk),
                       w('riemen_breite')).bodies.item(0)
        fertig(k, 'X-Riemen', ((xp - ra, xu + ra), (yc - ra, yc + ra),
                               (L['xr_z0'], L['xr_z1'])), 'Gummi', SCHWARZ)

    def kette():
        """X-Energiekette mit dem Toolhead in der Mitte des X-Wegs: das
        bewegte Ende steht dann genau ueber dem Festpunkt. Vereinfacht als
        ein U aus Untertrum, Bogen und Obertrum, die Endstuecke inbegriffen;
        quer so breit wie die Kette."""
        c = teile['Ref_Kette']
        x0 = L['xk_fest'] - w('endstueck_l')
        xb_ = xk_bogen(L, L['xw_mitte'])
        zc, (ri, ra) = L['xk_bogen_z'], L['xk_bogen_r']
        u0, u1 = L['xk_unter_z']
        o0, o1 = L['xk_ober_z']
        sk = skizze(c, _ebene(c, 'y', L['xk_y_mitte'], 'E_Ref_X-Kette'),
                    'Sk_X-Kette')
        zug = [((x0, u0), (xb_, u0)),
               ((xb_, u0), (xb_ + ra, zc), (xb_, o1)),
               ((xb_, o1), (x0, o1)),
               ((x0, o1), (x0, o0)),
               ((x0, o0), (xb_, o0)),
               ((xb_, o0), (xb_ + ri, zc), (xb_, u1)),
               ((xb_, u1), (x0, u1)),
               ((x0, u1), (x0, u0))]
        for pkt in zug:
            pp = [punkt(sk, u, v) for u, v in pkt]
            if len(pp) == 2:
                sk.sketchCurves.sketchLines.addByTwoPoints(*pp)
            else:
                sk.sketchCurves.sketchArcs.addByThreePoints(*pp)
        k = neu_mittig(c, groesstes_profil(sk), w('kette_b')).bodies.item(0)
        fertig(k, 'X-Energiekette', ((x0, xb_ + ra), L['xk_y'], (u0, o1)),
               'PLA', SCHWARZ)

    def kette_y():
        """Y-Energiekette mit dem Portal in der Mitte (wie alles hier):
        Untertrum vom Endstueck 180 in der Wanne nach vorn, Bogen,
        Obertrum zurueck zum Anfangsstueck auf dem Kettenhalter Y.
        Vereinfacht wie die X-Kette."""
        c = teile['Ref_Kette']
        yg = w('yk_gelenk_y')
        y0u = L['yk_fest'] - w('endstueck_l')
        y0o = yg - w('endstueck_l')
        yb = (L['yk_frei'] + L['yk_fest'] + yg) / 2.0
        zc, (ri, ra) = L['yk_bogen_z'], L['xk_bogen_r']
        u0, u1 = L['yk_unter_z']
        o0, o1 = L['yk_ober_z']
        sk = skizze(c, _ebene(c, 'x', L['yk_x_mitte'], 'E_Ref_Y-Kette'),
                    'Sk_Y-Kette')
        zug = [((y0u, u0), (yb, u0)),
               ((yb, u0), (yb + ra, zc), (yb, o1)),
               ((yb, o1), (y0o, o1)),
               ((y0o, o1), (y0o, o0)),
               ((y0o, o0), (yb, o0)),
               ((yb, o0), (yb + ri, zc), (yb, u1)),
               ((yb, u1), (y0u, u1)),
               ((y0u, u1), (y0u, u0))]
        for pkt in zug:
            pp = [punkt(sk, u, v) for u, v in pkt]
            if len(pp) == 2:
                sk.sketchCurves.sketchLines.addByTwoPoints(*pp)
            else:
                sk.sketchCurves.sketchArcs.addByThreePoints(*pp)
        k = neu_mittig(c, groesstes_profil(sk), w('kette_b')).bodies.item(0)
        fertig(k, 'Y-Energiekette', (L['yk_x'], (y0u, yb + ra), (u0, o1)),
               'PLA', SCHWARZ)

    def motor():
        c = teile['Ref_Antrieb']
        fl = w('motor_flansch') / 2.0
        mx, my = (xp - fl, xp + fl), (yc - fl, yc + fl)
        k = quader(c, 'NEMA17_X', mx, my, (L['mp_z1'], L['motor_z1']),
                   'neu').bodies.item(0)
        zylinder(c, 'NEMA17_Bund', 'z', (xp, yc), w('motor_bund_d'),
                 L['bund_z0'], L['mp_z1'], 'dazu', k)
        zylinder(c, 'NEMA17_Welle', 'z', (xp, yc), w('motor_welle_d'),
                 L['welle_ist_z0'], L['bund_z0'], 'dazu', k)
        fertig(k, 'NEMA17_X', (mx, my, (L['welle_ist_z0'], L['motor_z1'])),
               'Steel')

    def y_motor(s):
        """NEMA 17 am Y-Motorhalter: mittig zur 2040, in der Mitte seines
        Spannwegs; die gemessene Welle reicht durch das ganze Ritzel."""
        c = teile['Ref_Antrieb']
        n = seite(s)
        fl = w('motor_flansch') / 2.0
        mx, my = xs(L, s, 0.0), L['ym_y']
        bx, by = (mx - fl, mx + fl), (my - fl, my + fl)
        mz0, mz1 = L['ym_motor_z']
        k = quader(c, 'NEMA17_Y_' + n, bx, by, (mz0, mz1),
                   'neu').bodies.item(0)
        zylinder(c, 'NEMA17_Y_Bund_' + n, 'z', (mx, my), w('motor_bund_d'),
                 mz1, L['ym_bund_z1'], 'dazu', k)
        zylinder(c, 'NEMA17_Y_Welle_' + n, 'z', (mx, my), w('motor_welle_d'),
                 L['ym_bund_z1'], L['ym_welle_z1'], 'dazu', k)
        fertig(k, 'NEMA17_Y_' + n, (bx, by, (mz0, L['ym_welle_z1'])), 'Steel')

    def y_riemen(s):
        """Der offene Y-Riemen einer Seite (y_riemen_weg, Portal in der
        Mitte): gerade in der vorderen Klemme, schraeg an das Ritzel des
        Motors, um dessen Vorderseite, als Ruecklauf gerade in der
        aeusseren oberen Nut, um das hintere Ritzel und schraeg in die
        hintere Klemme. Zaehne innen, Wirklinie auf dem Teilkreis."""
        c = teile['Ref_Riemen']
        n = seite(s)
        g = y_riemen_weg(L)
        r, uk = g['r'], g['uk']
        ao, ai = L['riemen_aussen'], L['riemen_innen']
        ra, ri = r + ao, r - ai
        yf, yh = L['ym_y'], L['yh_y']
        v, h = g['vorn'], g['hinten']
        av, ah = v['winkel'], h['winkel']

        def kr(yc, rad, a):
            return (rad * math.cos(a), yc + rad * math.sin(a))
        yve, yvk = v['ende'][1], v['klemme'][1]
        yhe, yhk = h['ende'][1], h['klemme'][1]
        a_o, b_o = (uk + ao, yve), (uk + ao, yvk)
        a_i, b_i = (uk - ai, yve), (uk - ai, yvk)
        c_o, d_o = (uk + ao, yhk), (uk + ao, yhe)
        c_i, d_i = (uk - ai, yhk), (uk - ai, yhe)
        hinten = 1.5 * math.pi + ah / 2.0          # Mitte des hinteren Bogens
        vorn = (av + math.pi) / 2.0                # Mitte des vorderen Bogens
        zug = [(a_o, b_o), (b_o, kr(yf, ra, av)),
               (kr(yf, ra, av), kr(yf, ra, vorn), (-ra, yf)),
               ((-ra, yf), (-ra, yh)),
               ((-ra, yh), kr(yh, ra, hinten), kr(yh, ra, ah)),
               (kr(yh, ra, ah), c_o), (c_o, d_o), (d_o, d_i), (d_i, c_i),
               (c_i, kr(yh, ri, ah)),
               (kr(yh, ri, ah), kr(yh, ri, hinten), (-ri, yh)),
               ((-ri, yh), (-ri, yf)),
               ((-ri, yf), kr(yf, ri, vorn), kr(yf, ri, av)),
               (kr(yf, ri, av), b_i), (b_i, a_i), (a_i, a_o)]
        sk = skizze(c, _ebene(c, 'z', L['yr_zm'], 'E_Ref_Y-Riemen'),
                    'Sk_Y-Riemen_' + n)
        for pkt in zug:
            pp = [punkt(sk, xs(L, s, u), y) for u, y in pkt]
            if len(pp) == 2:
                sk.sketchCurves.sketchLines.addByTwoPoints(*pp)
            else:
                sk.sketchCurves.sketchArcs.addByThreePoints(*pp)
        k = neu_mittig(c, groesstes_profil(sk),
                       w('riemen_breite')).bodies.item(0)
        fertig(k, 'Y-Riemen_' + n,
               (xb(L, s, -ra, uk + ao), (yh - ra, yf + ra),
                (L['yr_z0'], L['yr_z1'])), 'Gummi', SCHWARZ)

    # ---- Aluprofile ----------------------------------------------------------
    sicher('Portalrohr_2020', profil, 'Portalrohr_2020', 'x',
           (-w('profil_laenge') / 2.0, w('profil_laenge') / 2.0),
           (L['profil_y0'], L['portal_y']), (L['profil_z0'], L['profil_z1']))
    for s in (-1, 1):
        n = seite(s)
        sicher('Rahmen_2040_' + n, profil, 'Rahmen_2040_' + n, 'y',
               L['rahmen_y'],
               xb(L, s, -w('rahmen_b') / 2.0, w('rahmen_b') / 2.0),
               (L['rahmen_z0'], L['rahmen_z1']))
    for t in ('hinten', 'vorn'):
        sicher('Quertraeger_2060_' + t, profil, 'Quertraeger_2060_' + t,
               'x', L['quer_x'], L['quer_y_' + t], L['quer_z'])

    # ---- Linearfuehrungen: Schienen und Wagen (mit Kanal fuer die Schiene) --
    c = teile['Ref_Fuehrungen']
    for s in (-1, 1):
        n = seite(s)
        xsch = xb(L, s, -w('y_schiene_b') / 2.0, w('y_schiene_b') / 2.0)
        zsch = (L['y_schiene_z0'], L['y_schiene_z1'])
        sicher('Y-Schiene_' + n, box, c, 'Y-Schiene_' + n, xsch,
               L['y_schiene_y'], zsch, 'Steel')
        ywg, zwg = (L['wagen_y0'], L['wagen_y1']), (L['y_wagen_z0'],
                                                   L['y_wagen_z1'])
        sicher('Y-Wagen_' + n, box, c, 'Y-Wagen_' + n,
               xb(L, s, -w('y_wagen_breite') / 2.0,
                  w('y_wagen_breite') / 2.0), ywg, zwg, 'Steel',
               (xsch, (ywg[0] - 1.0, ywg[1] + 1.0), (zwg[0] - 1.0, zsch[1])))
    zsch = (-w('x_schiene_b') / 2.0, w('x_schiene_b') / 2.0)
    ysch = (L['portal_y'], L['x_schiene_y1'])
    sicher('X-Schiene', box, c, 'X-Schiene', L['x_schiene_x'], ysch, zsch,
           'Steel')
    xwg = (L['xw_mitte'] - w('x_wagen_laenge') / 2.0,
           L['xw_mitte'] + w('x_wagen_laenge') / 2.0)
    ywg = (L['portal_y'] + w('x_wagen_boden'), 0.0)
    sicher('X-Wagen', box, c, 'X-Wagen', xwg, ywg,
           (-w('x_wagen_breite') / 2.0, w('x_wagen_breite') / 2.0), 'Steel',
           ((xwg[0] - 1.0, xwg[1] + 1.0), (ywg[0] - 1.0, ysch[1]), zsch))

    # ---- Riemen ----------------------------------------------------------------
    sicher('X-Riemen', x_riemen)
    # Y-Riemen je Seite: offen, von Klemme zu Klemme um beide Ritzel, der
    # Ruecklauf in der oberen Nut des 2040
    for s in (-1, 1):
        sicher('Y-Riemen_' + seite(s), y_riemen, s)

    # ---- X-Antrieb: Motor, Ritzel, Umlenkritzel, Riemenhalter ---------------
    c = teile['Ref_Antrieb']
    sicher('NEMA17_X', motor)
    z0 = L['ritzel_z0']
    sicher('Ritzel_X', rad, c, 'Ritzel_X', (xp, yc),
           [(rf, z0, z0 + bo),
            (L['ritzel_fuss_d'], z0 + bo, z0 + bo + sp),
            (rf, z0 + bo + sp, L['ritzel_nabe_z0']),
            (w('ritzel_nabe_d'), L['ritzel_nabe_z0'], L['ritzel_z1'])],
           w('motor_welle_d'), 'Aluminum 6061')
    # Y-Antrieb: Motor haengend, Ritzel mittig zur 2040 mit der Nabe nach
    # unten; hinten das Ritzel auf der Welle (Lage angenommen), gleich hoch
    z0, z1 = L['ym_ritzel_z']
    zn = L['ym_nabe_z1']
    y_stufen = [(w('ritzel_nabe_d'), z0, zn),
                (rf, zn, zn + bo),
                (L['ritzel_fuss_d'], zn + bo, z1 - bo),
                (rf, z1 - bo, z1)]
    for s in (-1, 1):
        n = seite(s)
        sicher('NEMA17_Y_' + n, y_motor, s)
        for t, y in (('vorn', L['ym_y']), ('hinten', L['yh_y'])):
            name = 'Ritzel_Y_{}_{}'.format(t, n)
            sicher(name, rad, c, name, (xs(L, s, 0.0), y), y_stufen,
                   w('motor_welle_d'), 'Aluminum 6061')
    # Umlenkritzel mit Welle und Lagern (Mitte des Spannwegs)
    rz0, rn = L['rolle_z0'], L['rolle_nabe_z0']
    sicher('Umlenkritzel_X', rad, c, 'Umlenkritzel_X', (xu, yc),
           [(rf, rz0, rz0 + bo), (L['ritzel_fuss_d'], rz0 + bo, rn - bo),
            (rf, rn - bo, rn), (w('ritzel_nabe_d'), rn, L['rolle_z1'])],
           w('uw_d'), 'Aluminum 6061')
    sicher('Welle_Umlenkung', stab, c, 'Welle_Umlenkung', (xu, yc),
           w('uw_d'), L['uw_z'], 'Steel')
    sicher('Kugellager_Umlenkung', rad, c, 'Kugellager_Umlenkung', (xu, yc),
           [(w('kl_d'), L['kl_z'][0], L['kl_z'][1])], w('uw_d'), 'Steel')
    sicher('Gleitlager_Umlenkung', rad, c, 'Gleitlager_Umlenkung', (xu, yc),
           [(w('gl_d'), L['gl_z'][0], L['gl_z'][1])], w('uw_d'), 'Steel')
    sicher('Riemenhalter_Toolhead', box, c, 'Riemenhalter_Toolhead',
           L['rh_x'], (-w('rh_tiefe'), 0.0),
           (w('x_wagen_breite') / 2.0,
            w('x_wagen_breite') / 2.0 + w('rh_hoehe')), 'PETG')
    # Traegerplatte vereinfacht, mit der linken Saeulenrippe: daran klemmt
    # die Fahne X (ToolheadZ.py). Sie reicht bis ueber den Kettenhalter.
    xm, xt, td = L['xw_mitte'], w('traeger_x_links'), w('traeger_dicke')
    kh_z = (L['xk_unter_z'][1] + w('luft_bau'), L['xk_ober_z'][0] + 3.0)
    th_z = (w('traeger_z0'), kh_z[1])
    sicher('Traegerplatte_Toolhead', box, c, 'Traegerplatte_Toolhead',
           (xm + xt, xm - xt), (0.0, td), th_z, 'PETG')
    sicher('Saeulenrippe_links_Toolhead', box, c,
           'Saeulenrippe_links_Toolhead', (xm + xt, xm + xt + w('rippe_b')),
           (td, td + w('rippe_t')), th_z, 'PETG')
    # Kettenhalter (ToolheadZ.py) als Huelle: Fuss an der Platte, Auflage
    # unter dem Anfangsstueck, Fuehrungsleisten daneben
    sicher('Kettenhalter_Toolhead', box, c, 'Kettenhalter_Toolhead',
           (xm + xt, xm + w('xk_gelenk_x')),
           (L['wanne_innen_y'][0] - 1.2, 0.0), kh_z, 'PETG')
    sicher('X-Energiekette', kette)
    sicher('Y-Energiekette', kette_y)

    # ---- Lichtschranken der Endschalter: Y fest am Rahmen, X am Portal ------
    c = teile['Ref_Endschalter']
    sicher('LS_Y_Platine', box, c, 'LS_Y_Platine', L['ly_pcb_x'],
           L['ly_pcb_y'], L['ly_pcb_z'], 'Leiterplatte')
    for i, ax in enumerate(L['ly_arme_x']):
        n = 'LS_Y_Gabel_{}'.format(i + 1)
        sicher(n, box, c, n, ax, L['ly_gabel_y'], L['ly_gabel_z'],
               'Kunststoff')
    sicher('LS_X_Platine', box, c, 'LS_X_Platine', L['lx_pcb_x'],
           L['lx_pcb_y_rel'], L['lx_pcb_z'], 'Leiterplatte')
    for i, az in enumerate(L['lx_arme_z']):
        n = 'LS_X_Gabel_{}'.format(i + 1)
        sicher(n, box, c, n, L['lx_gabel_x'], L['lx_gabel_y_rel'], az,
               'Kunststoff')


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/portal_check.py)."""
    R = L['R']
    riemen_x = (2.0 * (L['x_rolle'] - L['x_motor'])
                + math.pi * w('ritzel_teilkreis'))
    dz_nut = (L['yr_z0'] + L['yr_z1']) / 2.0 - L['nut_z']   # + = hoeher
    H = L['ymh']
    g = y_riemen_weg(L)
    # Riemenweg an den Schienenenden gegen die Mitte (schraege Trume)
    d_s = w('y_schiene_laenge') / 2.0 - w('y_wagen_laenge') / 2.0
    mehr_v, mehr_h = (y_riemen_weg(L, dy)['laenge'] - L['yr_laenge']
                      for dy in (d_s, -d_s))
    tisch = L['ym_motor_z'][0] - L['quer_z'][0]       # Motor -> Unterkante 2060
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
        'Y-RIEMEN (Linie wie RiemenklemmeSchlitten v8, Hoehe am Aufbau',
        '  gemessen): Mitte {:.1f} mm innen neben der Schienenmitte, hochkant,'
        .format(w('y_riemen_linie')),
        '  Zaehne zur Schiene, Unterkante Z={:+.1f} ({:.1f} mm unter der'
        .format(L['yr_z0'], w('y_riemen_tiefe')),
        '  Wagenoberseite): mittig in der oberen Nut des 2040. Der Schlitz der',
        '  Klemmtuerme reicht bis {:.1f} mm ueber die Oberkante der Nut.'
        .format(w('kt_decke')),
        '  Beide Ritzel sitzen mittig zur 2040: die Trume der Wagen laufen',
        '  schraeg von der Klemme in die innere obere Nut ({:.1f} Grad vorn,'
        .format(g['vorn']['schraeg']),
        '  {:.1f} hinten, Portal in der Mitte), der Ruecklauf gerade in der'
        .format(g['hinten']['schraeg']),
        '  aeusseren ({:.1f} mm neben der Schienenmitte). Die Zaehne zeigen'
        .format(-L['yr_rueck_u']),
        '  zur Innenseite der Schleife, also zur Schiene: dort stehen die',
        '  Rippen beider Klemmen.',
        '  Zwei gleiche Klemmtuerme je Schlitten wie v8, {:.1f} mm vor und'
        .format(w('turm_abstand')),
        '  hinter der Wagenmitte (Aussenkante), einer je Riemenende: Riemen',
        '  von unten in den Schlitz druecken, Stift Ø3x{0:.0f} (oder M3x{0:.0f})'
        .format(L['kt_stift_l']),
        '  quer von innen unter ihm durchschieben. Gespannt wird am Y-Motor',
        '  (Langloecher, siehe Y-ANTRIEB).',
        '  Klemmschlitz {:.1f} mm, Rippen {:.1f} mm: laesst sich der Riemen'
        .format(w('klemm_schlitz'), w('klemm_rippe')),
        '  nicht eindruecken, klemm_schlitz um 0,1 erhoehen; rutscht er,',
        '  verringern (gilt auch fuer den Riemenhalter in ToolheadZ.py).',
        '  Laenge je Seite ca. {:.0f} mm von Klemme zu Klemme (Wirklinie,'
        .format(L['yr_laenge']),
        '  Portal in der Mitte, Motor in der Mitte des Spannwegs, hinteres',
        '  Ritzel {:.0f} mm hinter der Stirnseite angenommen): die Enden'
        .format(w('yh_hinter')),
        '  stehen bis kurz vor das innere Ende der Klemmtuerme. Weil die',
        '  Trume der Wagen schraeg laufen, wird der Weg zu den Schienen-',
        '  enden hin laenger (vorn +{:.1f}, hinten +{:.1f} mm): dort ist der'
        .format(mehr_v, mehr_h),
        '  in der Mitte gespannte Riemen etwas gedehnt.',
        '  Beide Seiten abgleichen: an einer Ecke die Madenschrauben des',
        '  Y-Ritzels loesen, Portal von Hand durchschieben, bis es frei',
        '  laeuft, festziehen. Grob geht es in der Klemme um einen Zahn.',
        '',
        'Y-ANTRIEB (Y-Motorhalter vorn an jeder 2040, bis Rev. 15',
        '  YMotorhalter.py): NEMA 17 haengend unter der Platte, Welle nach',
        '  OBEN, das Ritzel {:.0f} Z mittig zur 2040 direkt auf der Welle.'
        .format(H['zaehne']),
        '  Motorachse {:.2f} bis {:.2f} mm vor der Stirnseite (Langloecher,'
        .format(H['motor_y_min'], H['motor_y_max']),
        '  jeder mm macht den Riemenweg 2 mm laenger). Flansch bei Z={:+.1f},'
        .format(L['ym_motor_z'][1]),
        '  Motor unten {:.0f} mm ueber der Unterkante der 2060.'.format(tisch),
        '  RITZEL mit der Nabe nach UNTEN bis ans Wellenende schieben: dann',
        '  sitzt die Spur in der oberen Nut, {:.1f} mm ueber der Platte; eine'
        .format(H['ritzel_luft']),
        '  Madenschraube auf die Abflachung.',
        '  Halter: U-Buegel, Joch an der Stirnseite (nimmt den Riemenzug),',
        '  Schenkel an beiden Seitenflaechen mit {}x M5x{:.0f} + Scheibe in'
        .format(H['n_m5'], H['m5_schraube']),
        '  Nutensteinen der UNTEREN Nuten, {:.0f} und {:.0f} mm hinter der'
        .format(w('ymh_schraube_y'),
                w('ymh_schraube_y') + w('ymh_schraube_abstand')),
        '  Stirnseite; die oberen Nuten bleiben fuer den Riemen frei. Motor:',
        '  4x M3x{:.0f} + Scheibe von oben. Links und rechts dasselbe Teil.'
        .format(H['motor_schraube']),
        '  Spannen: Motorschrauben loesen, Motor vom Profil weg ziehen,',
        '  festziehen.',
        '  Beide Motoren an einem Treibersignal (A klont Y), einer umgepolt:',
        '  docs/hardware-notizen.md, Elektronik.',
        '',
        'X-ANTRIEB (GT2 20 Z, Riemen hochkant, Unterkante Z={:+.2f}):'.format(
            L['xr_z0']),
        '  Motor links, Achse X={:+.1f} Y={:+.2f}: stehend, Welle nach unten,'
        .format(L['x_motor'], L['xr_yc']),
        '  Flansch bei Z={:+.2f} auf der {:.1f}-mm-Motorplatte, 4x M3x{:.0f}'
        .format(L['mp_z1'], w('mp_dicke'), L['motor_schraube']),
        '  von unten. Ritzel mit der Nabe nach OBEN, Z {:+.2f} bis {:+.2f}:'
        .format(L['ritzel_z0'], L['ritzel_z1']),
        '  die Nabe taucht {:.1f} mm in die Bundbohrung. Ausgelegt auf'
        .format(L['ritzel_z1'] - L['mp_z0']),
        '  {:.0f} mm Welle; die gemessenen {:.0f} mm enden {:.1f} mm unter dem'
        .format(w('motor_welle_l'), w('motor_welle_ist'),
                L['ritzel_z0'] - L['welle_ist_z0']),
        '  Ritzel, {:.1f} mm ueber dem Rohr. Madenschrauben {:.1f} mm unter der'
        .format(L['welle_ist_z0'] - L['profil_z1'],
                L['mp_z0'] - L['madenschraube_z']),
        '  Platte, Inbus von vorn; eine davon auf die Abflachung der Welle.',
        '  Motorhalter: 2x M3x{:.0f} von oben in die Einsaetze des Stirnblocks.'
        .format(L['mh_schraube']),
        '  ANSCHLAG (seit Rev. 24) auf dem linken Stirnblock, innen neben',
        '  der aeusseren Saeule ({:.1f} mm Luft, {:.1f} x {:.1f} mm Flaeche):'
        .format(w('mha_spiel'), L['mha_y'][1] - L['mha_y'][0],
                w('mha_hoehe')),
        '  er nimmt den Riemenzug auf, der den Halter nach innen schiebt;',
        '  die Schrauben halten ihn nur noch nieder. Passt auch an den',
        '  schon gedruckten Halter.',
        '  Umlenkung rechts, Achse X={:+.2f} (Spannweg {:+.2f} bis {:+.2f}):'
        .format(L['x_rolle'], L['x_rolle_bereich'][0],
                L['x_rolle_bereich'][1]),
        '  Umlenkritzel = GT2-Ritzel 20 Z wie am Motor, Nabe nach OBEN, mit',
        '  den Madenschrauben fest auf einer Welle Ø{:.0f} x {:.0f}. Die Welle'
        .format(w('uw_d'), w('uw_laenge')),
        '  laeuft oben im Kugellager {:.0f}x{:.0f}, unten im Gleitlager'
        .format(w('kl_d'), w('kl_b')),
        '  Ø{:.0f}x{:.0f}; beide sitzen im LAGERSCHLITTEN. Das Ritzel liegt mit'
        .format(w('gl_d'), w('gl_l')),
        '  dem Bord auf dem Gleitlager, ueber der Nabe {:.1f} mm Luft.'
        .format(w('ls_luft')),
        '  Der Schlitten liegt auf dem Rohr, seine Feder laeuft in der oberen',
        '  Nut. Spannen: M3x{:.0f} von aussen durch den SPANNBOCK in den'
        .format(L['zug_schraube']),
        '  Gewindeeinsatz im Ruecken des Schlittens — eindrehen zieht ihn',
        '  nach aussen, die Schraube haelt ihn gegen den Riemenzug.',
        '  Spannbock: 2x M3x{:.0f} von oben in die Einsaetze des Stirnblocks.'
        .format(L['sb_schraube']),
        '  Riemenlaenge: Schleife {:.0f} mm, beide Enden im Riemenhalter'
        .format(riemen_x),
        '  (ToolheadZ.py) — mit dem Schlitten in Mittelstellung ablaengen.',
        '',
        'ENERGIEKETTE X (seit Rev. 19, docs/energiekette.md): gedruckt nach',
        '  dem Modell "Energiekette" (lingnau.florian). Teilung {:.0f}, aussen'
        .format(w('kette_teilung')),
        '  {:.0f} x {:.0f}, innen {:.0f} x {:.1f} mm, Biegeradius {:.0f} mm. Sie liegt'
        .format(w('kette_b'), w('kette_h'), w('kette_innen_b'),
                w('kette_innen_h'), w('kette_r')),
        '  direkt hinter der Traegerplatte (Y {:+.1f} bis {:+.1f}).'.format(
            *L['xk_y']),
        '  Festpunkt: ENDSTUECK 180, Platte unten, Gelenk bei X={:+.2f} (Mitte'
        .format(L['xk_fest']),
        '  des Wegs des bewegten Gelenks), 2x M3x{:.0f} + Scheibe durch'
        .format(L['xk_fest_schraube']),
        '  Endstueck und Wanne in die Einsaetze der Stuetze darunter.',
        '  Bewegtes Ende: ANFANGSSTUECK, Platte unten, auf dem Kettenhalter',
        '  des Toolheads (ToolheadZ.py), Gelenk {:.0f} mm rechts der'
        .format(w('xk_gelenk_x')),
        '  X-Wagenmitte. Schleife nach rechts: {} Glieder = {:.0f} mm zwischen'
        .format(L['xk_glieder'], L['xk_laenge']),
        '  den Gelenken ({:.1f} gebraucht: halber Hub + Bogen), mit den'
        .format(L['xk_noetig']),
        '  Endstuecken {:.0f} mm. Der Untertrum liegt auf den Riegeln, Wannen-'
        .format(L['xk_laenge'] + 2.0 * w('endstueck_l')),
        '  boden Z={:+.1f}, der Obertrum 2 R hoeher (innen Z={:+.1f}). Am'
        .format(w('xk_boden_z'), L['xk_ober_z'][0]),
        '  rechten Ende des X-Wegs geht die Kette bei X={:+.1f} in den Bogen'
        .format(L['xk_bogen_x'][1]),
        '  und laeuft {:.2f} mm ueber den Lagerschlitten.'.format(
            L['xk_unter_z'][0] - L['ls_oben_z'][1]),
        '  Schleife gemessen (2026-10-02): um 180 Grad gebogen aussen 50 mm,',
        '  4 Gelenke im Bogen; gerechnet {:.1f} mm, etwas weiter.'.format(
            2.0 * w('kette_r') + w('kette_h') + 2.0 * w('kette_riegel')),
        '  WANNE: X {:+.2f} bis {:+.2f} ({:.1f} mm), Boden {:.0f}, Waende {:.0f}'
        .format(L['wanne_x'][0], L['wanne_x'][1],
                L['wanne_x'][1] - L['wanne_x'][0], w('wanne_boden'),
                w('wanne_wand_h')),
        '  hoch, links und rechts offen; liegt auf den Armen der Stuetzen,',
        '  an den beiden Laschen je 1x M3x{:.0f} in den Einsatz des Blocks.'
        .format(L['wanne_schraube']),
        '  WANNENSTUETZEN (Festpunkt, mitte X={:+.0f}, rechts X={:+.0f}): je'
        .format(w('st_x_mitte'), w('st_x_rechts')),
        '  1x M5x{:.0f} in eine Hammermutter der HINTEREN Nut des Rohrs. Der'
        .format(L['st_m5_schraube']),
        '  Block steht auf dem Rohr hinter dem Ruecklauf, der Arm reicht',
        '  ueber Riemen und Riemenhalter unter die Wanne.',
        '  KABELWEG (seit Rev. 21) der Litzen W7, W11, W15: vom Kettenhalter Y',
        '  auf der Platte hinter Stirnblock und Rueckwand nach innen, rechts',
        '  neben der Rueckwand hoch und ueber die hintere Kante in die OBERE',
        '  Nut des Rohrs (Nutabdeckung oder Clips), bis links neben die Stuetze',
        '  am Festpunkt. Dort vor dem KABELFLUEGEL hoch, je ein Kabelbinder',
        '  durch zwei Schlitze bei Z={:+.0f} und Z={:+.0f} (Kopf hinten), oben ueber'
        .format(w('kf_binder_z1'), w('kf_binder_z2')),
        '  den Riemen nach vorn und von links in das Endstueck 180.',
        '  In der Kette nur Einzellitzen (Silikon), keine Mantelleitungen:',
        '  fuer sie ist der Biegeradius zu klein (docs/verkabelung.md).',
        '',
        'ENERGIEKETTE Y (seit Rev. 21, docs/energiekette.md): dieselbe',
        '  Kette wie X, aussen am linken 2040 (X {:+.1f} bis {:+.1f}),'
        .format(*L['yk_x']),
        '  Schleife nach vorn. {} Glieder = {:.0f} mm, mit den Endstuecken'
        .format(L['yk_glieder'], L['yk_laenge']),
        '  {:.0f} mm: Arbeitsweg (hinten Schienenende, vorn {:+.0f}) plus'
        .format(L['yk_laenge'] + 2.0 * w('endstueck_l'), w('y_weg_vorn')),
        '  {:.1f} mm Reserve. Weiter vorn haelt die Kette das Portal an.'
        .format(L['yk_reserve_vorn']),
        '  Bewegtes Ende: ANFANGSSTUECK, Platte unten, auf dem KETTENHALTER',
        '  Y hinter dem Stirnblock des linken Schlittens (Gelenk Y={:+.0f}),'
        .format(w('yk_gelenk_y')),
        '  2x M3x{:.0f} + Scheibe in seine Einsaetze. Der Halter: 2x M3x{:.0f}'
        .format(L['khy_ende_schraube'], L['khy_schraube']),
        '  von UNTEN durch die Schlittenplatte in Einsaetze. Schlitten_links',
        '  hat die 2 Loecher Ø{:.1f} im Modell (Neudruck); in den schon'
        .format(w('m3_durchgang')),
        '  gedruckten bohrt man sie mit Bohrlehre_Kettenhalter_Y.',
        '  Festpunkt: ENDSTUECK 180 hinten in der WANNE Y (Y {:+.1f} bis'
        .format(L['ywanne_y'][0]),
        '  {:+.1f}, Boden Z={:+.1f}), 2x M3x{:.0f} + Scheibe in den Traeger'
        .format(L['ywanne_y'][1], L['ywanne_boden_z'][1],
                L['xk_fest_schraube']),
        '  darunter; dahinter zwei Binderschlitze fuer die Zugentlastung.',
        '  Drei TRAEGER Y (Festpunkt, mitte Y={:+.0f}, vorn Y={:+.0f}), je'
        .format(w('ytr_y_mitte'), w('ytr_y_vorn')),
        '  1x M5x{:.0f} in eine Hammermutter der UNTEREN SEITENNUT aussen am'
        .format(L['ytr_m5_schraube']),
        '  2040 (die Nut an der Unterseite ist belegt). Die Wanne an den',
        '  Laschen je M3x{:.0f}. Die Kabel in der Seitennut gehen an jedem'
        .format(L['wanne_schraube']),
        '  Traeger kurz aus der Nut, unter seiner Wand durch.',
        '',
        'ENDSCHALTER (Gabellichtschranken LM393, docs/endschalter.md):',
        '  Im Modell steht das Portal in der Mitte und der Toolhead in der',
        '  Mitte des X-Wegs: die Fahnen stehen NICHT in ihrer Gabel. Beide',
        '  schalten {:.0f} mm vor dem Schienenende: Portal {:+.1f} von der'
        .format(w('schaltabstand'), L['schalt_dy']),
        '  Mitte, X-Wagenmitte {:+.2f}.'.format(L['schalt_xs']),
        '  HALTER_Y: aussen an das rechte 2040, {:.0f} mm hinter dem hinteren'
        .format(L['quer_y_hinten'][0] - L['hy_y'][1]),
        '    2060; 2x M5x{:.0f} mit Scheibe in Hammermuttern der UNTEREN Nut'
        .format(L['hy_m5_schraube']),
        '    (Z {:+.0f}), NICHT in die obere: dort laeuft der Ruecklauf des'
        .format(L['nut_u_z']),
        '    Y-Riemens. Lichtschranke mit 2x M2x6, Gabel oben und vorn.',
        '  FAHNE_Y: von aussen auf die Kante der rechten Schlittenplatte,',
        '    Hinterkante {:.0f} mm vor der Hinterkante der Platte, Maden-'
        .format(w('fy_hinten') - L['platte_y0']),
        '    schraube M3x8 im Einsatz. Schaltpunkt: laengs der Kante schieben.',
        '  HALTER_X: vor das linke Ende der 2020, Hammermutter M5 in ihre',
        '    vordere Nut, Block rechts an das Ende der X-Schiene, M5x{:.0f}'
        .format(L['hx_m5_schraube']),
        '    (Kopf versenkt) — ERST DANN die Lichtschranke mit 2x M2x6, sie',
        '    deckt den Kopf ab. Gabel nach vorn, Spalt waagerecht.',
        '  KLAMMER_X: von links auf die untere Kante der Traegerplatte (unter',
        '    dem X-Wagen), Madenschraube M3x8 vorn auf die Seitenrippe.',
        '  FAHNE_X: M3x{:.0f} auf den Kopf der Klammer, Langloch +-{:.0f} mm'
        .format(L['fx_schraube'], w('fx_verstellung')),
        '    stellt den Schaltpunkt ein.',
        '  Einsaetze: 4x M2 (3,2 x 2,5, Bohrung {:.1f}), 3x M3 (Bohrung {:.1f}).'
        .format(w('ls_pcb_loch_d'), w('insert_m3_d')),
        '  Vor der ersten Referenzfahrt beide Schaltpunkte von Hand pruefen.',
        '',
        'MONTAGEREIHENFOLGE:',
        '  1. Einsaetze einschmelzen: 2 je Klemmturm, 2 je Stirnblock (oben),',
        '     1 von aussen in den Ruecken des Lagerschlittens.',
        '  2. Beide Klemmtuerme unter die Platte, je 2x M3x{:.0f} von oben.'
        .format(L['turm_schraube']),
        '     VOR dem Rohr: die Schrauben des vorderen liegen unter dem Rohr.',
        '  3. Schlitten auf die Y-Wagen, 4x M3x{:.0f} (Kopf in der Senkung).'
        .format(L['wagen_schraube']),
        '  4. Hammermuttern in die hintere Nut des Rohrs, Kernbohrungen M5',
        '     schneiden. Portal (Rohr mit X-Schiene und Toolhead) auf die',
        '     Platten legen, an Rueckwand und Stirnblock: 2x M5x{:.0f} hinten,'
        .format(L['rueck_schraube']),
        '     1x M5x{:.0f} stirnseitig je Seite.'.format(L['kern_schraube']),
        '  5. Motor von oben auf den Motorhalter, 4x M3x{:.0f} von unten.'
        .format(L['motor_schraube']),
        '     Ritzel von unten auf die Welle, Nabe voraus, bis die Welle'
        ' {:.1f} mm'.format(w('welle_ueberstand')),
        '     unten heraussteht; Madenschrauben von vorn. Halter aufs linke',
        '     Rohrende, nach innen an den Anschlag schieben und so',
        '     festziehen (2x M3x{:.0f}).'.format(L['mh_schraube']),
        '  6. Lagerschlitten: Kugellager von unten in den oberen Arm,',
        '     Gleitlager von oben in den unteren (steht {:.1f} mm ueber).'
        .format(w('ls_luft')),
        '     Ritzel (Nabe oben) zwischen die Arme, Welle von oben durch',
        '     Kugellager, Ritzel und Gleitlager, oben buendig; Ritzel auf',
        '     das Gleitlager setzen, Madenschrauben fest. Schlitten aufs',
        '     rechte Rohrende, Feder in die obere Nut. Spannbock auf den',
        '     Stirnblock (2x M3x{:.0f}), Zugschraube M3x{:.0f} lose.'
        .format(L['sb_schraube'], L['zug_schraube']),
        '  7. X-Riemen: ein Ende in den Riemenhalter, um Motor und',
        '     Umlenkritzel, zweites Ende einlegen, spannen. Laeuft er nicht',
        '     mittig in der Spur, das Ritzel nachstellen.',
        '  8. Y-Motorhalter: je Seite 4 Nutensteine in die UNTEREN Nuten',
        '     beider Seitenflaechen, Halter mit dem Joch an die Stirnseite,',
        '     {}x M5x{:.0f} mit Scheibe. Motor von unten, 4x M3x{:.0f} + Scheibe'
        .format(H['n_m5'], H['m5_schraube'], H['motor_schraube']),
        '     von oben, noch lose. Ritzel mit der Nabe nach unten bis ans',
        '     Wellenende, Madenschraube auf die Abflachung.',
        '  9. Y-Riemen (ca. {:.0f} mm): ein Ende in die vordere Klemme, schraeg'
        .format(L['yr_laenge']),
        '     in die innere Nut, um das Ritzel, in der aeusseren Nut nach',
        '     hinten, um das hintere Ritzel, in die hintere Klemme. Motor vom',
        '     Profil weg ziehen, Schrauben fest.',
        ' 10. Energiekette X: Einsaetze einschmelzen, 2 von oben in den Arm',
        '     der Wannenstuetze am Festpunkt, je 1 oben in den Block der',
        '     anderen. Je eine Hammermutter in die hintere Nut, Stuetzen mit',
        '     M5x{:.0f} ans Rohr (Mitte bei X {:+.2f}, {:+.0f} und {:+.0f}).'
        .format(L['st_m5_schraube'], sum(L['st_x']['Festpunkt']) / 2.0,
                w('st_x_mitte'), w('st_x_rechts')),
        '     Wanne auflegen, an den Laschen je M3x{:.0f}. Kette mit {} Glie-'
        .format(L['wanne_schraube'], L['xk_glieder']),
        '     dern, Anfangsstueck an das eine, Endstueck 180 an das andere',
        '     Ende; Endstueck 180 mit 2x M3x{:.0f} + Scheibe auf Wanne und'
        .format(L['xk_fest_schraube']),
        '     Stuetze, Anfangsstueck auf den Kettenhalter. Litzen einziehen,',
        '     am Kettenhalter mit einem Kabelbinder zugentlasten, am',
        '     Festpunkt mit zwei Kabelbindern am Kabelfluegel.',
        ' 11. Energiekette Y: Einsaetze einschmelzen (Kettenhalter Y 2 von',
        '     unten und 2 von oben, Traeger 2 + 1 + 1). Kettenhalter Y mit',
        '     2x M3x{:.0f} von unten an den linken Schlitten. Je eine'
        .format(L['khy_schraube']),
        '     Hammermutter in die untere Seitennut, Traeger mit M5x{:.0f} ans'
        .format(L['ytr_m5_schraube']),
        '     2040; die Koepfe bleiben von aussen unter der Wanne frei.',
        '     Wanne auflegen, Laschen M3x{:.0f}. Kette mit {} Gliedern,'
        .format(L['wanne_schraube'], L['yk_glieder']),
        '     Endstueck 180 hinten mit 2x M3x{:.0f} + Scheibe, Anfangsstueck'
        .format(L['xk_fest_schraube']),
        '     auf den Kettenhalter Y. Litzen einziehen, Kabelbinder an beiden',
        '     Enden. W13 in der Seitennut an jedem Traeger kurz aus der Nut,',
        '     unter seiner Wand durch.',
        '',
        'DRUCK (PETG, Bambu Lab A1, 4 Wandlinien, >=40 % Infill):',
        '  Schlitten ....... Unterseite aufs Bett, Waende stehen darauf;',
        '                    links mit den 2 Loechern fuer den Kettenhalter Y',
        '                    und dem Anschlag fuer den Motorhalter',
        '  Klemmturm (4x) .. Oberseite (Plattenseite) aufs Bett, Schlitz',
        '                    nach oben offen, Rippen senkrecht',
        '  Motorhalter ..... Motorplatte (Oberseite) aufs Bett',
        '  Spannbock ....... Boden aufs Bett',
        '  Lagerschlitten .. auf dem Ruecken liegend, Lagersitze als Traene',
        '  Y-Motorhalter .. Oberseite (Platte) aufs Bett, kopfueber',
        '  Halter_Y ........ Fussflaeche (die Seite am Profil) aufs Bett',
        '  Halter_X ........ Platinenseite aufs Bett, Zunge oben',
        '  Fahne_Y ......... eine Stirnseite aufs Bett   } SCHWARZ: helles',
        '  Klammer_X ....... Unterkante aufs Bett        } PETG laesst das',
        '  Fahne_X ......... flach                       } Infrarot durch',
        '  Kettenwanne ..... Boden aufs Bett, laengs ({:.0f} mm)'.format(
            L['wanne_x'][1] - L['wanne_x'][0]),
        '  Wannenstuetzen .. Rueckseite der Platte aufs Bett (3 Stueck),',
        '                    der Kabelfluegel liegt mit flach',
        '  Kettenhalter Y .. Unterseite (Auflage) aufs Bett',
        '  Kettenwanne Y ... Boden aufs Bett, laengs ({:.0f} mm)'.format(
            L['ywanne_y'][1] - L['ywanne_y'][0]),
        '  Traeger Y ....... Oberseite des Arms aufs Bett (3 Stueck)',
        '  Keine Stuetzen noetig. Rechter Schlitten und rechte Klemmtuerme',
        '  sind gespiegelt — im Slicer NICHT spiegeln, die Koerper so',
        '  exportieren, wie sie im Modell liegen. Die Y-Motorhalter sind',
        '  symmetrisch: zweimal dasselbe Teil.',
        '',
        'NICHT GEMESSEN — vor dem Druck pruefen [?]:',
        '  Lager der Umlenkung: Kugellager {:.0f}x{:.0f} und Gleitlager'
        .format(w('kl_d'), w('kl_b')),
        '    Ø{:.0f}x{:.0f} (Angabe), Bohrung {:.0f} angenommen. Die Sitze haben'
        .format(w('gl_d'), w('gl_l'), w('uw_d')),
        '    spiel_press; sitzen sie zu fest oder zu lose, den Wert anpassen.',
        '  Hinteres Y-Ritzel: {:.0f} mm hinter der Stirnseite angenommen; davon'
        .format(w('yh_hinter')),
        '    haengt nur die Riemenlaenge ab. Es muss wie vorn mit der Spur',
        '    mittig auf dem Riemen stehen ({:.0f} bis {:.0f} mm unter der'.format(
            L['rahmen_z1'] - L['yr_z1'], L['rahmen_z1'] - L['yr_z0']),
        '    Oberkante des 2040).',
        '  Y-Schienen mittig auf den 2040 angenommen: davon haengt ab, wie weit',
        '    das Portal an die Y-Motorhalter heranfaehrt.',
        '  Nut 6 der 2040: Lippe {:.1f} und Nutgrund {:.1f} mm [w] legen fest,'
        .format(w('nut_lippe'), w('nut_tiefe')),
        '    wo der Riemen im Nutkanal laeuft ({:.2f} mm Luft zur Lippe, {:.2f}'
        .format(H['luft_lippe'], H['luft_nutgrund']),
        '    zum Grund).',
        '  Ritzel 20 Z: Spur {:.0f} mm, Nabe {:.0f} mm mit den Madenschrauben in'
        .format(w('ritzel_spur'), L['ritzel_z1'] - L['ritzel_nabe_z0']),
        '    der Mitte angenommen [w]. Bis {:.0f} mm Welle endet sie ueber dem'
        .format(L['mp_z1'] - L['profil_z1'] - 1.0),
        '    Rohr.',
        '  Lichtschranke: Boden des Gabelschlitzes {:.0f} mm ueber der Platine'
        .format(w('ls_schlitz_boden')),
        '    (das Blatt bleibt {:.1f} mm darueber); Loetstifte unter der'
        .format(w('fahne_ab_platine') - w('ls_schlitz_boden')),
        '    Platine (Taschen {:.1f} mm unter der Gabel); ob der X-Wagen links'
        .format(w('ls_pin_tasche')),
        '    einen Schmiernippel hat (die Platine steht {:.0f} mm vor dem'
        .format(w('hx_luft_wagen')),
        '    Wagenende).',
        '  Winkel an den Kreuzungen 2040/2060: 20 mm, direkt am 2060 in der',
        '    unteren Seitennut (bestaetigt 2026-10-02), ihre Schenkel nicht',
        '    gemessen. Wanne Y und Kette Y bleiben ausserhalb.',
        '',
        'REFERENZ (Komponente Referenz_nicht_drucken): nur zur Ansicht,',
        '  NICHT drucken und beim Export weglassen. Eine Gluehbirne blendet',
        '  alles aus.',
        '  Profile: Portalrohr 2020, beide 2040 ({:.0f} mm) und die zwei 2060'
        .format(w('rahmen_laenge')),
        '    quer darunter ({:.0f} mm, {:.0f} mm Mitte zu Mitte), V-Slot'.format(
            w('quer_laenge'), w('quer_abstand')),
        '    vereinfacht. 2040 und Schienen mittig zum Y-Wagen [?], das',
        '    vordere 2060 {:.0f} mm hinter der Stirnseite [v], hinten stehen'
        .format(w('quer_vorn_zurueck')),
        '    die 2040 {:.0f} mm ueber das hintere 2060 [v].'.format(
            L['quer_y_hinten'][0] - L['rahmen_y'][0]),
        '  Fuehrungen: MGN12 ({:.0f} mm) mit MGN12H, MGN15 mit MGN15H. Vom'
        .format(w('y_schiene_laenge')),
        '    Toolhead nur X-Wagen, Riemenhalter, Traegerplatte und Ketten-',
        '    halter (vereinfacht), in der Mitte des X-Wegs.',
        '  X-Energiekette: das bewegte Ende steht dann ueber dem Festpunkt;',
        '    vereinfacht als U aus Untertrum, Bogen und Obertrum. Y-Energie-',
        '    kette ebenso, mit dem Portal in der Mitte seines Wegs.',
        '  Lichtschranken der Endschalter: Y am Rahmen, X vor der 2020.',
        '  X-Riemen: Schleife um Ritzel und Umlenkritzel, beide Enden im',
        '    Riemenhalter.',
        '  Y-Riemen: je Seite offen, schraeg von der Klemme vorn um das',
        '    Ritzel des Y-Motors, der Ruecklauf gerade in der aeusseren',
        '    oberen Nut des 2040 (Z {:+.1f} bis'
        .format(L['yr_rueck_z'][0]),
        ('    {:+.1f}), auf derselben Hoehe wie in der Klemme.'.format(
            L['yr_rueck_z'][1]) if abs(dz_nut) < 0.05
         else '    {:+.1f}), die Klemme haelt ihn {:.1f} mm {}.'.format(
             L['yr_rueck_z'][1], abs(dz_nut),
             'hoeher' if dz_nut > 0 else 'tiefer')),
        '    hinten um das Ritzel auf der Welle (Lage angenommen, Welle und',
        '    Lager nicht gezeichnet), die Enden in den Klemmtuermen.',
        '  Y-Motoren mit Ritzel mittig zur 2040, in der Mitte ihres',
        '    Spannwegs.',
        '  Die Ritzel sind am Fuss der Verzahnung gezeichnet, die',
        '    Massen der Referenzteile stimmen nur grob.',
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
        _AUSSEHEN.clear()
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
        # damit schon an seinem Platz. Nichts bewegt sich gegeneinander (die
        # Spanner sind Einstellungen), also alles fixiert statt Joints.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Schlitten_links', 'Klemmturm_hinten_links',
                     'Klemmturm_vorn_links', 'Motorhalter',
                     'Schlitten_rechts', 'Klemmturm_hinten_rechts',
                     'Klemmturm_vorn_rechts', 'Spannbock', 'Lagerschlitten',
                     'Y-Motorhalter_links', 'Y-Motorhalter_rechts',
                     'Halter_Y', 'Fahne_Y', 'Halter_X', 'Klammer_X',
                     'Fahne_X', 'Kettenwanne', 'Wannenstuetze_Festpunkt',
                     'Wannenstuetze_mitte', 'Wannenstuetze_rechts',
                     'Kettenhalter_Y', 'Kettenwanne_Y',
                     'Wannentraeger_Y_Festpunkt', 'Wannentraeger_Y_mitte',
                     'Wannentraeger_Y_vorn', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o

        for s in (-1, 1):
            n = seite(s)
            bau_schlitten(app, design, occ['Schlitten_' + n].component, L, s,
                          fehler)
            for t in ('hinten', 'vorn'):
                bau_klemmturm(app, design,
                              occ['Klemmturm_{}_{}'.format(t, n)].component,
                              L, s, t, fehler)
            bau_y_motorhalter(app, design,
                              occ['Y-Motorhalter_' + n].component, L, s,
                              fehler)
        bau_motorhalter(app, design, occ['Motorhalter'].component, L, fehler)
        bau_spannbock(app, design, occ['Spannbock'].component, L, fehler)
        bau_lagerschlitten(app, design, occ['Lagerschlitten'].component, L,
                           fehler)
        for name, bauen in (('Halter_Y', bau_halter_y),
                            ('Fahne_Y', bau_fahne_y),
                            ('Halter_X', bau_halter_x),
                            ('Klammer_X', bau_klammer_x),
                            ('Fahne_X', bau_fahne_x)):
            bauen(app, design, occ[name].component, L, fehler)
        bau_kettenwanne(app, design, occ['Kettenwanne'].component, L, fehler)
        for n in ('Festpunkt', 'mitte', 'rechts'):
            bau_stuetze(app, design, occ['Wannenstuetze_' + n].component,
                        L, n, fehler)
        bau_kettenhalter_y(app, design, occ['Kettenhalter_Y'].component, L,
                           fehler)
        bau_kettenwanne_y(app, design, occ['Kettenwanne_Y'].component, L,
                          fehler)
        for n in ('Festpunkt', 'mitte', 'vorn'):
            bau_traeger_y(app, design,
                          occ['Wannentraeger_Y_' + n].component, L, n,
                          fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, fehler)

        for o in occ.values():
            o.isGrounded = True

        # Referenz: eine Komponente, darunter die Gruppen — eine Gluehbirne
        # blendet alles aus, was nicht gedruckt wird
        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Profile', 'Ref_Fuehrungen', 'Ref_Riemen',
                     'Ref_Antrieb', 'Ref_Endschalter', 'Ref_Kette'):
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
