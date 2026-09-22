# ToolheadZ.py — kompletter Laser-Toolhead mit NEMA17-Z-Achse
#
# Baugruppe (vier gedruckte Teile), weil sich Teile relativ zueinander bewegen:
#   Traegerplatte   — geerdet, sitzt auf dem MGN15H-Wagen der Portalfuehrung,
#                     traegt die MGN9-Z-Schiene (Sockel) und die Motorkonsole
#   Motorhalter     — U-Konsole oben, traegt den NEMA 17 (Welle nach unten)
#   Schlittenplatte — auf dem MGN9H-Z-Wagen, traegt den Diodenlaser
#   Mutternwinkel   — Winkel fuer die Tr8x2-Anti-Backlash-Garnitur: Regal
#                     ueber der Plattenoberkante, Ruecken schwimmend an der
#                     Schlittenplatte verschraubt
#
# Koordinatensystem = Maschinenkoordinaten, global fuer alle Komponenten:
#   X = quer, laengs des Portals          Y = nach vorn, weg vom Portal
#   Z = senkrecht (Verfahrrichtung Z)     Ursprung = Mitte des X-Wagen-
#   Lochbildes AUF seiner Stirnflaeche (die Passflaeche der Traegerplatte).
#
# Alle Ebenen und Achsen leitet `lage()` aus MASSE ab — eine Quelle fuer
# Geometrie und fuer die Pruefung in tools/toolhead_check.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'ToolheadZ'
REVISION = 24

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Kaufteil: Portalfuehrung MGN15H ------------------------------------
    # quer = senkrecht zur Schiene = Z, laengs = laengs der Schiene = X
    # Das Lochbild 25 x 25 ist am 2026-09-21 mit Bohrlehre_XWagen am Wagen
    # geprueft und bestaetigt [v] — damit ist es ein MGN15H (ein MGN15C
    # haette 25 x 20) und die alte Messung "26 x 25" ist widerlegt: bei
    # Ø3,4-Lochlehre auf M3 wuerde 1 mm Abweichung nicht mehr passen.
    'x_wagen_loch_quer':   (25.0,  'MGN15H Wagen: Lochabstand in Z'),
    'x_wagen_loch_laengs': (25.0,  'MGN15H Wagen: Lochabstand in X'),
    'x_wagen_breite':      (32.0,  'MGN15H Wagen: Breite (in Z)'),
    'x_wagen_laenge':      (58.8,  'MGN15H Wagen: Laenge (in X)'),
    'x_wagen_hoehe':       (16.0,  'MGN15 Montagehoehe: Wagenflaeche ueber Profil'),
    'x_schiene_hoehe':     (10.0,  'MGN15 Schiene: Hoehe'),
    'x_gewinde_tiefe':     (4.0,   'MGN15 Wagen: M3-Gewindetiefe'),

    # --- Kaufteil: Z-Fuehrung MGN9H (hardware.md [w]) ----------------------
    # quer = X, laengs = Z (Schiene steht senkrecht)
    'z_wagen_loch_quer':   (15.0,  'MGN9H Wagen: Lochabstand in X'),
    'z_wagen_loch_laengs': (16.0,  'MGN9H Wagen: Lochabstand in Z'),
    'z_wagen_breite':      (20.0,  'MGN9H Wagen: Breite (in X)'),
    'z_wagen_laenge':      (39.9,  'MGN9H Wagen: Laenge (in Z)'),
    'z_wagen_hoehe':       (10.0,  'MGN9 Montagehoehe: Wagenflaeche ueber Sockel'),
    'z_schiene_breite':    (9.0,   'MGN9 Schiene: Breite'),
    'z_schiene_hoehe':     (6.5,   'MGN9 Schiene: Hoehe'),
    # 200 mm ist die vorhandene Schiene [v]; 10 + 9*20 + 10 = 200, also
    # 10 Loecher. Die Schiene sitzt in Z FEST (sie haengt am X-Wagen), ihr
    # unteres Ende ist damit ein dauerhaftes Hindernis: es muss ueber dem
    # dicksten Werkstueck bleiben. Deshalb waechst sie nach OBEN, nicht nach
    # unten — Unterkante bleibt, wo sie war.
    'z_schiene_laenge':   (200.0,  'MGN9 Schiene: Laenge (10 + 9*20 + 10)'),
    'z_schiene_lochab':    (20.0,  'MGN9 Schiene: Lochabstand'),
    'z_schiene_randab':    (10.0,  'MGN9 Schiene: Randabstand'),
    'z_schiene_senkung':   (3.3,   'MGN9 Schiene: Tiefe der Senkung'),
    'z_gewinde_tiefe':     (2.5,   'MGN9 Wagen: M3-Gewindetiefe'),

    # --- Kaufteil: NEMA 17 (hardware.md [w]) -------------------------------
    'motor_flansch':       (42.3,  'NEMA17: Flanschmass'),
    'motor_loch':          (31.0,  'NEMA17: Lochbild 31 x 31'),
    'motor_bund_d':        (22.0,  'NEMA17: Zentrierbund Durchmesser'),
    'motor_bund_h':        (2.0,   'NEMA17: Zentrierbund Hoehe'),
    'motor_welle_l':       (24.0,  'NEMA17: Wellenlaenge'),
    'motor_laenge':        (40.0,  'NEMA17: Koerperlaenge (nur Freigang)'),

    # --- Kaufteil: Antrieb -------------------------------------------------
    # Trapezgewinde Tr8x2 mit Anti-Backlash-Garnitur (hardware.md). Die
    # Spindel hat KEINEN angedrehten Zapfen: Ø8 ist der Gewindeaussen-
    # durchmesser, die Klemmnabe der Kupplung greift auf die Gewindespitzen.
    # Das traegt (siehe Momentenrechnung in toolhead_check.py, Abschnitt 7).
    'spindel_d':           (8.0,   'Tr8x2: Gewindeaussendurchmesser'),
    'spindel_durchgang':   (8.6,   'Tr8x2 Durchgang (+0,6 wie M6 vorher)'),
    'kupplung_d':          (19.0,  'Wendelkupplung 5->8: Durchmesser'),
    'kupplung_l':          (25.0,  'Wendelkupplung 5->8: Laenge'),
    # Einstecktiefe = Laenge der massiven KLEMMNABE, nicht die halbe Kupplung:
    # in der Mitte sitzt der Wendelschnitt, und der muss frei bleiben. Stossen
    # Welle und Spindel dort zusammen, ist die Nachgiebigkeit ueberbrueckt —
    # aus der Ausgleichskupplung wird eine starre Huelse, im schlimmsten Fall
    # reisst der Steg. 8 mm ist geschaetzt [?] (= ein Spindeldurchmesser, die
    # uebliche Klemmlaenge); am gelieferten Teil die Nabenlaenge messen.
    'kupplung_griff':       (8.0,  'Wendelkupplung: Klemmlaenge je Seite'),
    # Die Garnitur: Flanschmutter auf dem Regal, Feder und Gleitmutter
    # darueber. Die Befestigungsloecher im Flansch sind DURCHGANGSloecher,
    # das Gewinde sitzt also im Druckteil (M3-Messingeinsaetze).
    't8_flansch_d':        (22.0,  'Tr8x2 Flanschmutter: Flanschdurchmesser'),
    't8_lochkreis':        (16.0,  'Tr8x2 Flanschmutter: Lochkreis (4x M3)'),
    # 45 = Flanschmutter 15 + Feder vorgespannt ~15 + Gleitmutter 15. Nur
    # geschaetzt [?] — am gelieferten Teil messen, der Wert allein bestimmt
    # die obere Verfahrgrenze (siehe zc_grenzen).
    't8_garnitur_h':       (45.0,  'Tr8x2 Garnitur: Bauhoehe ueber dem Regal'),
    # Erzeugen keine Geometrie, nur Bericht und Pruefung: die bestellte Laenge
    # und die Laenge, auf die sie gekuerzt wird. Kuerzen ist nicht optional —
    # ungekuerzt haengt das untere Ende tiefer als die Plattenunterkante und
    # wird selbst zur Werkstueckgrenze (siehe werkstueck_frei_lang).
    'spindel_bestellt':   (200.0,  'Tr8x2: bestellte Spindellaenge'),
    'spindel_zuschnitt':  (150.0,  'Tr8x2: Laenge nach dem Kuerzen'),

    # --- Kaufteil: Diodenlaser (Nutzerangabe + hardware.md) ----------------
    # 40,5 x 16,5 — am 2026-09-17 mit Bohrlehre_Laser (Ø3,4 Rundloecher) am
    # Modul geprueft und bestaetigt [v]. Dritte Messung an diesem Modul,
    # vorher 39 x 15 und 40 x 16.
    # Die Befestigungen sind weiterhin Langloecher. Der Grund dafuer ist jetzt
    # nicht mehr das unsichere Bohrbild, sondern nur noch Toleranzausgleich
    # (Schrumpf ueber 40,5 mm PETG). Rundloecher Ø4,0 wuerden auch reichen —
    # siehe docs/toolhead-z.md.
    'laser_loch_quer':     (16.5,  'Laser: Lochabstand quer (X)'),
    'laser_loch_hoch':     (40.5,  'Laser: Lochabstand senkrecht (Z)'),
    'laser_breite':        (35.0,  'Laser: Gehaeusebreite'),
    'laser_tiefe':         (35.0,  'Laser: Gehaeusetiefe — treibt die Strahlachse'),
    'laser_laenge':        (99.6,  'Laser: Gehaeuselaenge (senkrecht)'),
    'laser_loch_ab_unten': (4.5,   'Laser: untere Lochreihe ueber Gehaeuseunterkante'),

    # --- Normteile ---------------------------------------------------------
    'm3_durchgang':        (3.4,   'M3 Durchgang'),
    'm3_uebermass':        (4.6,   'M3 Durchgang mit Ausrichtspiel (Mutternwinkel)'),
    'm3_senkung':          (6.5,   'Freibohrung fuer M3-Zylinderkopf + Werkzeug'),
    'm3_mutter_sw':        (5.5,   'M3 Mutter: Schluesselweite'),
    'm3_mutter_h':         (2.4,   'M3 Mutter: Hoehe'),
    # Mutterntaschen bewusst enger als die Faustregel in hardware.md
    # (SW + 0,2..0,3): die Muttern sollen VOR dem Festschrauben von allein
    # sitzen. Falls eine Tasche zu stramm wird, hier erhoehen.
    'tasche_spiel':        (0.15,  'Mutterntasche: Spiel auf die Schluesselweite'),
    'm3_scheibe_h':        (0.5,   'M3 Scheibe DIN 125: Dicke'),
    'inbus_frei_d':        (6.0,   'Werkzeugkorridor fuer den 2,5er Inbus'),
    # 4,6 statt 4,0: die vorhandenen Messingeinsaetze haben 5 mm Aussen-
    # durchmesser [v] (ruthex M3 hat 4,6 und will 4,0). 0,4 mm Untermass —
    # ein Einschmelzeinsatz muss Material verdraengen, um zu greifen.
    # Der Sockel ist so breit wie die Schiene und darf nicht breiter werden;
    # es bleiben (9 - 4,6)/2 = 2,20 mm Wand je Seite, Minimum ist 2,0.
    'insert_m3_d':         (4.6,   'Gewindeeinsatz M3: Einpressbohrung'),
    'insert_m3_t':         (7.0,   'Gewindeeinsatz M3: Sacklochtiefe'),

    # --- Traegerplatte -----------------------------------------------------
    'traeger_dicke':       (8.0,   'Traegerplatte: Dicke'),
    'traeger_x_links':    (-22.0,  'Traegerplatte: linke Kante'),
    'traeger_x_rechts':    (22.0,  'Traegerplatte: rechte Kante der Hauptsaeule'),
    'traeger_x_kopf':      (56.0,  'Traegerplatte: rechte Kante des Kopfbereichs'),
    'traeger_z_unten':    (-66.0,  'Traegerplatte: Unterkante'),
    # Der Kopf ist nur breit, weil er die Konsole tragen muss — er beginnt
    # deshalb erst kurz unter ihr, sonst waere die lange Saeule unnoetig
    # schwer.
    'traeger_kopf_unten': (115.0,  'Traegerplatte: Unterkante des Kopfbereichs'),
    # Versteifung der Saeule: zwei Rippen auf der Vorderseite, an den Kanten
    # der Saeule. Ohne sie biegt der Motor (2,75 N auf 132,5 mm Hebel ab der
    # Verschraubung am X-Wagen) die 8-mm-Platte um 0,57 mm durch, mit ihnen um
    # 0,22 mm — der Bericht rechnet beides aus.
    # 18..22 statt weiter innen, weil dazwischen kein Platz ist: bei X=+14,5
    # laeuft der Korridor der hinteren Motorschraube durch, bei |X|<13 der
    # Z-Wagen. An der Kante wirkt die Rippe ohnehin am besten.
    'saeule_rippe_x0':     (18.0,  'Saeulenrippe: Innenkante (Abstand zur Achse)'),
    'saeule_rippe_x1':     (22.0,  'Saeulenrippe: Aussenkante'),
    # 6,0 mm tief: der Ø22-Flansch der Antriebsmutter sitzt mittig auf der
    # Spindelachse und reicht damit bis Y=17,5 nach hinten — mehr als 6,0
    # laesst dort keine 3,5 mm Luft mehr. Steifigkeit siehe check 4.
    'saeule_rippe_tiefe':   (6.0,  'Saeulenrippe: Hoehe ueber der Plattenvorderseite'),
    'sockel_breite':        (9.0,  'Schienensockel: Breite = Schienenbreite!'),
    'sockel_hoehe':        (5.0,   'Schienensockel: Hoehe ueber der Plattenvorderseite'),

    # --- Lage der Spindelachse und der Motorkonsole ------------------------
    'spindel_x':           (30.0,  'Spindelachse: X (Abstand von der Schienenachse)'),
    # 28,5 statt 21: nur so liegt die hintere Motorschraubenreihe
     # (spindel_y - motor_loch/2) vor der Traegerplatte und ist von unten
     # erreichbar. Nach vorn begrenzt die Haut vor der Spindelbohrung im
     # Ruecken des Mutternwinkels (schlitten_y1 - spindel_y
     # - spindel_durchgang/2 >= 2).
    'spindel_y':           (28.5,  'Spindelachse: Y ab X-Wagen-Stirnflaeche'),
    # Die Konsole ist Teil der Traegerplatte (ein Druckteil) — keine Laschen.
    # 145: 5 mm ueber dem oberen Schienenende (-60 + 200 = +140).
    'konsole_unten':      (145.0,  'Motorkonsole: Unterseite (= Oberkante Saeule)'),
    'konsole_dicke':       (8.0,   'Motorkonsole: Dicke'),
    'konsole_y_vorn':      (56.0,  'Motorkonsole: vordere Kante'),
    'konsole_rand':        (4.5,   'Motorkonsole: Rand neben den Fuehrungsrippen'),
    'motor_rippe_breite':  (3.0,   'Fuehrungsrippe am Motorflansch: Breite'),
    'motor_rippe_hoehe':   (3.0,   'Fuehrungsrippe: Hoehe ueber der Konsole'),
    # --- Endschalter: Gabellichtschranke (LM393-Modul) ---------------------
    # Platine 25 x 20 mm, Gabel an einer Stirnseite (1 mm von der 20-mm-Kante),
    # Schlitzbreite 10 mm, zwei M3-Loecher in den Ecken der Gegenseite [v].
    # Lochmitte 2,5 mm von jeder Kante (der Nutzer hat "1 mm von beiden
    # Kanten" gemessen — bei Ø3 kann das nur der Lochrand sein), Lochabstand
    # damit 15 mm. Der Halter hat dafuer Langloecher.
    'ls_pcb_laenge':      (25.0,  'Lichtschranke: Platinenlaenge (in Z)'),
    'ls_pcb_breite':      (20.0,  'Lichtschranke: Platinenbreite (in Y)'),
    'ls_pcb_dicke':        (1.8,  'Lichtschranke: Platinendicke'),
    'ls_pcb_rand':         (2.5,  'Lichtschranke: Lochmitte von der Kante'),
    'ls_schlitz':         (10.0,  'Lichtschranke: Schlitzbreite (Gabelspalt)'),
    # ANGENOMMEN: Strahlachse 5 mm ueber der Stirnkante der Platine. Genau
    # dafuer sitzen die Anschraubloecher des Halters in Langloechern — der
    # Schaltpunkt wird beim Einstellen gefunden, das Mass muss nicht stimmen.
    'ls_strahl_ab_kante':  (5.0,  'Lichtschranke: Strahlachse ueber der Stirnkante'),
    'ls_halter_dicke':     (4.0,  'Endschalterhalter: Wandstaerke'),
    'ls_wand_versatz':     (6.0,  'Endschalterhalter: Wand links neben der Platte'),
    'ls_flansch_dicke':    (3.0,  'Endschalterhalter: Dicke des Anschraubflansches'),
    'ls_justage':          (4.0,  'Endschalterhalter: Langlochverstellung je Richtung'),
    'ls_schraub_abstand': (20.0,  'Endschalterhalter: Abstand der Anschraubpunkte'),
    'ls_sockel_hoehe':     (8.0,  'Endschaltersockel an der Platte: Hoehe in Y'),
    'ls_sockel_x1':      (-13.0,  'Endschaltersockel: rechte Kante'),
    # Die vorhandenen M2-Einsaetze haben 3,2 mm Aussendurchmesser und sind
    # 2,5 mm lang [v] — Ø2,8 ist dafuer die Einpressbohrung (0,4 mm Untermass,
    # dieselbe Regel wie bei den M3 am Schienensockel). Dahinter bleibt eine
    # Freibohrung fuer die Schraubenspitze, damit der Einsatz nicht
    # durchgedrueckt werden kann.
    'ls_pcb_loch_d':       (2.8,  'Lichtschranke: Einpressbohrung M2-Einsatz'),
    'ls_pcb_loch_t':       (3.0,  'Lichtschranke: Tiefe der Einpressbohrung'),
    'ls_pcb_frei_d':       (2.4,  'Lichtschranke: Freibohrung fuer die Schraubenspitze'),
    # Abstand der Platinenunterkante zum Flansch. 1 mm war zu wenig: der
    # Flansch stand 0,9 mm in die untere Platinenbohrung hinein (am
    # gedruckten Teil aufgefallen). Mit 3 mm bleibt unter dem Loch 1,6 mm
    # Wand stehen.
    'ls_pcb_luft':         (3.0,  'Lichtschranke: Platine ueber dem Flansch'),
    'ls_fahne_hoehe':     (15.0,  'Schaltfahne: Hoehe in Z'),
    'ls_fahne_dicke':      (2.0,  'Schaltfahne: Dicke (laeuft im Gabelspalt)'),
    # 9 mm Tiefe, 3,5 mm vor der Platine: die Fahne deckt damit jede
    # Strahlhoehe zwischen 3,5 und 12,5 mm ueber der Platine ab und bleibt
    # trotzdem 3,7 mm vom Z-Wagen weg.
    'ls_fahne_tiefe':      (9.0,  'Schaltfahne: Tiefe quer zur Platine'),
    'ls_fahne_luft_pcb':   (3.5,  'Schaltfahne: Luft zur Platinenoberflaeche'),
    'ls_ueberfahrt':       (8.0,  'Weg nach dem Schaltpunkt bis zur Grenze'),

    # --- Schlittenplatte (Konzept aus ToolheadGrundplatte) -----------------
    # 12 statt 6: schiebt die Schlittenplatte so weit nach vorn, dass der
    # Ruecken des Mutternwinkels hinter ihr Platz hat, obwohl die Spindelachse
    # bei 28,5 liegt. Der Ø22-Flansch der Antriebsmutter passt hier NICHT
    # dahinter — deshalb liegt sein Regal ueber der Plattenoberkante.
    'pad_hoehe':           (12.0,  'Auflagepad: Versatz Wagenflaeche -> Platte'),
    # 30: der Kopffreiraum sitzt bei X = +-8,25 und braucht Wand zum Padrand.
    # Seit der Umstellung auf Ø4,0-Rundloecher (kleinere Scheibe, Freiraum Ø8)
    # waeren auch 28 mm ausreichend — 30 laesst Reserve.
    'pad_breite':          (30.0,  'Auflagepad: Breite'),
    'pad_laenge':          (26.0,  'Auflagepad: Hoehe'),
    'schlitten_dicke':     (6.0,   'Schlittenplatte: Dicke'),
    'schlitten_breite_l':  (17.5,  'Schlittenplatte: Kante links der Schienenachse'),
    'schlitten_rand':      (4.0,   'Schlittenplatte: Rand um das Lochfeld'),
    # Nur zur Dokumentation und fuer die Fokusrechnung im Bericht — keine
    # Geometrie. Gemessen 2026-09-17: Lochbildmitte X-Wagen -> Bettoberflaeche.
    'bett_abstand':        (130.0, 'Maschine: Bezugsebene -> Bettoberflaeche'),
    'werkstueck_max':      (50.0,  'Maschine: dickstes Werkstueck'),
    'rippe_mitte_breite':  (5.0,   'Mittelrippe: Breite'),
    # 13,5: die Scheibe der Laserschraube liegt zwischen Mittel- und
    # Seitenrippe. Mit der DIN-125-Scheibe (Ø7) bleiben dort 1,75 mm Luft.
    'rippe_seite_innen':   (13.5,  'Seitenrippe links: Innenkante'),
    # -46: zwei Bedingungen zugleich. (1) MONTAGE — das Gewinde der
    # Laserbefestigung sitzt im Modul, also wird von hinten verschraubt. Liegt
    # die obere Lochreihe auf der Wagenmitte, steht der Z-Wagen davor und der
    # Inbus hat nur 12 mm Platz. Sie muss um mehr als halbe Wagenlaenge plus
    # Werkzeugradius (19,95 + 3) von der Wagenmitte weg — das gilt auch fuer
    # die eingestellte Langlochstellung, siehe langloch_auf_max in lage().
    # (2) FOKUS — mit bett_abstand und werkstueck_max liegt das Fokusfenster
    # damit richtig; der Bericht rechnet die Langlochstellung je Fokusabstand
    # aus. -46 statt -44 laesst 2,8 mm statt 0,8 mm Luft nach oben.
    'laser_versatz_z':     (-46.0, 'Laser-Lochbildmitte gegen die Wagenmitte'),
    # Senkrechter Verstellweg: damit haengt die Laserhoehe nicht am genauen
    # Fokusabstand des Moduls, der auf dem Modul nicht steht.
    'laser_langloch_hub':   (8.0,  'Laser-Befestigung: Verstellweg je Richtung'),
    'kopf_freiraum':        (8.0,  'Freiraum im Pad fuer Kopf+Scheibe der Laserschraube'),
    # Langloch SENKRECHT (nicht quer): 4,0 mm Breite gibt wie bisher +-0,5 mm
    # je Loch Lochbildtoleranz quer, die Laenge ist die Hoehenverstellung.
    'laser_loch_d':         (4.0,  'Laser-Befestigung: Langlochbreite'),

    # --- Mutternwinkel -----------------------------------------------------
    # Winkel statt Block: die gekaufte Garnitur bringt die Spielfreiheit mit
    # (zwei Mutternhaelften, von einer Feder gegeneinander gedrueckt), sie
    # braucht nur einen plangedrehten Flanschsitz. Das Regal liegt UEBER der
    # Oberkante der Schlittenplatte — der Ø22-Flansch wuerde sonst in die
    # Platte laufen (Spindelachse Y=28,5, Plattenrueckseite Y=35).
    'winkel_x_links':      (16.0,  'Mutternwinkel: linke Kante'),
    'winkel_x_rechts':     (44.0,  'Mutternwinkel: rechte Kante'),
    'winkel_ruecken':      (8.0,   'Mutternwinkel: Dicke des senkrechten Ruecken'),
    'winkel_unten':        (8.0,   'Mutternwinkel: Ruecken unter der Schraubenreihe'),
    # 10 mm: der Flanschsitz muss den M3-Einsatz (7 mm) aufnehmen und
    # darunter Material lassen (hardware.md: mindestens 9 mm).
    'winkel_regal_dicke':  (10.0,  'Mutternwinkel: Dicke des Flanschregals'),
    'winkel_luft':         (0.5,   'Mutternwinkel: Luft Regal -> Plattenoberkante'),

    # --- Druckgerecht + Freigaenge -----------------------------------------
    'luft_bau':            (3.0,   'Mindestfreigang zwischen bewegten Teilen'),
    'fase_fuss':           (0.4,   'Fase gegen Elefantenfuss an Auflageflaechen'),
    'spiel_locker':        (0.4,   'Montagespiel, diametral'),
    'lehre_dicke':         (3.0,   'Bohrlehren: Plattendicke'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def c(name):
    """Wert in cm (API-Einheit fuer Point3D)."""
    return MASSE[name][0] / 10.0


def lage():
    """Alle abgeleiteten Ebenen, Achsen und Verfahrgrenzen in globalen
    Maschinenkoordinaten (mm). Einzige Quelle fuer Geometrie UND Pruefung."""
    L = {}

    # ---- Y-Kette: vom Portal nach vorn --------------------------------------
    L['portal_y'] = -w('x_wagen_hoehe')                      # Profilflaeche
    L['x_schiene_y'] = -w('x_wagen_hoehe') + w('x_schiene_hoehe')
    L['traeger_y0'] = 0.0                                    # = X-Wagen-Stirnflaeche
    L['traeger_y1'] = w('traeger_dicke')
    L['sockel_y1'] = L['traeger_y1'] + w('sockel_hoehe')     # Auflage der Z-Schiene
    L['z_schiene_y1'] = L['sockel_y1'] + w('z_schiene_hoehe')
    L['z_wagen_y'] = L['sockel_y1'] + w('z_wagen_hoehe')     # Stirnflaeche Z-Wagen
    L['schlitten_y0'] = L['z_wagen_y']
    L['schlitten_y1'] = L['z_wagen_y'] + w('pad_hoehe')      # Rueckseite Platte
    L['laser_y'] = L['schlitten_y1'] + w('schlitten_dicke')  # Anschraubflaeche
    L['laser_vorn_y'] = L['laser_y'] + w('laser_tiefe')
    L['strahl_y'] = L['laser_y'] + w('laser_tiefe') / 2.0

    # ---- Z-Kette: Schiene, Wagen, Kupplung, Motor ---------------------------
    L['saeule_rippe_x'] = [(-w('saeule_rippe_x1'), -w('saeule_rippe_x0')),
                           (w('saeule_rippe_x0'), w('saeule_rippe_x1'))]
    L['z_schiene_ueberstand'] = 6.0        # Schienenende ueber der Plattenunterkante
    L['z_schiene_z0'] = w('traeger_z_unten') + L['z_schiene_ueberstand']
    L['z_schiene_z1'] = L['z_schiene_z0'] + w('z_schiene_laenge')
    L['konsole_z0'] = w('konsole_unten')
    L['konsole_z1'] = L['konsole_z0'] + w('konsole_dicke')
    L['motor_flansch_z'] = L['konsole_z1']                   # Motor sitzt oben auf
    L['motor_z1'] = L['motor_flansch_z'] + w('motor_laenge')
    L['welle_z0'] = L['motor_flansch_z'] - w('motor_welle_l')
    L['kupplung_z1'] = L['welle_z0'] + w('kupplung_griff')
    L['kupplung_z0'] = L['kupplung_z1'] - w('kupplung_l')
    # Oberkante der Spindel: so weit in die untere Klemmnabe, wie diese lang
    # ist — NICHT bis an die Motorwelle. Dazwischen bleibt der Wendelbereich.
    L['spindel_z1'] = L['kupplung_z0'] + w('kupplung_griff')
    L['kupplung_frei'] = L['welle_z0'] - L['spindel_z1']

    # ---- Schlittenplatte und Laser, relativ zur Wagenmitte zc ---------------
    lochmitte = w('laser_versatz_z')                         # Lochbildmitte ueber zc
    L['laser_loch_unten_rel'] = lochmitte - w('laser_loch_hoch') / 2.0
    L['laser_loch_oben_rel'] = lochmitte + w('laser_loch_hoch') / 2.0
    L['laser_unten_rel'] = L['laser_loch_unten_rel'] - w('laser_loch_ab_unten')
    L['laser_oben_rel'] = L['laser_unten_rel'] + w('laser_laenge')
    L['schlitten_oben_rel'] = w('pad_laenge') / 2.0 + w('schlitten_rand')
    # Das Langloch braucht nach unten Material fuer den ganzen Hub; nach oben
    # bleibt die Platte, wie sie war, damit der Verfahrweg nicht schrumpft
    # (die Oberkante bindet gegen die Kupplung).
    L['schlitten_unten_rel'] = L['laser_loch_unten_rel'] \
        - w('laser_loch_d') / 2.0 - w('laser_langloch_hub') \
        - w('schlitten_rand')
    # Liegt die obere Lochreihe ausserhalb des Auflagepads, braucht sie dort
    # keinen Kopffreiraum — der Schnitt entfaellt dann ganz.
    L['laser_oben_im_pad'] = (abs(L['laser_loch_oben_rel'])
                              < w('pad_laenge') / 2.0)
    # ---- Mutternwinkel: Ruecken an der Platte, Regal darueber -------------
    # Der Ruecken liegt an der Plattenrueckseite (Y = schlitten_y1) und reicht
    # von winkel_unten unter der Schraubenreihe bis an die Regaloberseite.
    L['winkel_y0'] = L['schlitten_y1'] - w('winkel_ruecken')
    L['winkel_unten_rel'] = -w('winkel_unten')
    # Das Regal setzt erst ueber der Plattenoberkante an — sonst laeuft der
    # Ø22-Flansch in die Platte (siehe MASSE-Kommentar).
    L['regal_z0_rel'] = L['schlitten_oben_rel'] + w('winkel_luft')
    L['regal_z1_rel'] = L['regal_z0_rel'] + w('winkel_regal_dicke')
    # Das Regal traegt den runden Flansch, also genau dessen Durchmesser tief.
    L['regal_y0'] = w('spindel_y') - w('t8_flansch_d') / 2.0
    L['regal_y1'] = w('spindel_y') + w('t8_flansch_d') / 2.0
    # Garnitur: Flanschmutter, Feder und Gleitmutter stehen NACH OBEN auf dem
    # Regal. Nach unten waere kein Platz — dort sitzt die Schlittenplatte.
    L['garnitur_z1_rel'] = L['regal_z1_rel'] + w('t8_garnitur_h')
    # Lochkreis um 45 Grad gedreht: so bleibt der Flanschsitz in Y schlank
    # (Loecher bei +-lochkreis/(2*sqrt2) statt +-lochkreis/2). Der runde
    # Flansch laesst sich beliebig drehen, die Lage ist also frei waehlbar.
    r45 = w('t8_lochkreis') / 2.0 / math.sqrt(2.0)
    L['t8_loecher'] = [(w('spindel_x') + sx * r45, w('spindel_y') + sy * r45)
                       for sx in (-1, 1) for sy in (-1, 1)]

    # ---- Verfahrgrenzen: jede Begrenzung einzeln, damit sichtbar bleibt,
    #      welche bindet ------------------------------------------------------
    luft = w('luft_bau')
    L['zc_min'] = L['z_schiene_z0'] + w('z_wagen_laenge') / 2.0
    grenzen = {
        'Schiene (Wagen am obersten Ende)':
            L['z_schiene_z1'] - w('z_wagen_laenge') / 2.0,
        'Laser-Oberkante gegen Motorkonsole':
            L['konsole_z0'] - luft - L['laser_oben_rel'],
        'Schlittenplatte gegen Kupplung':
            L['kupplung_z0'] - luft - L['schlitten_oben_rel'],
        'Antriebsmutter gegen Kupplung':
            L['kupplung_z0'] - luft - L['garnitur_z1_rel'],
    }
    L['zc_grenzen'] = grenzen
    L['zc_max'] = min(grenzen.values())
    L['zc_bindend'] = min(grenzen, key=lambda k: grenzen[k])
    L['z_weg'] = L['zc_max'] - L['zc_min']

    # ---- Fokusfenster: Hoehe der Gehaeuseunterkante ueber dem Bett. Reine
    #      Rechnung fuer den Bericht, keine Geometrie.
    L['linse_tief'] = w('bett_abstand') + L['laser_unten_rel'] + L['zc_min']
    L['linse_hoch'] = w('bett_abstand') + L['laser_unten_rel'] + L['zc_max']
    # Die festen Teile (Plattenunterkante, Schienenende) haengen auf einer
    # Hoehe und fahren in X mit: sie begrenzen die Werkstueckhoehe unabhaengig
    # vom Verfahrweg. Mit langem Verfahrweg ist das die eigentliche Grenze.
    L['werkstueck_frei'] = min(
        w('traeger_z_unten'), L['z_schiene_z0']) + w('bett_abstand') - 5.0
    # Dasselbe gilt fuer das untere Spindelende: es haengt frei nach unten und
    # faehrt in X mit. Auf spindel_zuschnitt gekuerzt stoert es nicht,
    # ungekuerzt ist es die niedrigste Kante der ganzen Maschine.

    # ---- Endschalter: Gabellichtschranke links neben der Saeule ------------
    # Geschaltet wird beim Hochfahren: die Oberkante der Schaltfahne (= die
    # der Schlittenplatte) erreicht den Strahl, kurz bevor der Wagen
    # mechanisch ansteht. ls_ueberfahrt ist der Rest bis dahin.
    L['ls_strahl_z'] = (L['zc_max'] - w('ls_ueberfahrt')
                        + L['schlitten_oben_rel'])
    L['ls_pcb_z0'] = L['ls_strahl_z'] - w('ls_strahl_ab_kante')
    L['ls_pcb_z1'] = L['ls_pcb_z0'] + w('ls_pcb_laenge')
    L['ls_sockel_z0'] = L['ls_pcb_z0'] - 5.0
    L['ls_sockel_z1'] = L['ls_pcb_z1'] + 5.0
    # Sockel an der Plattenvorderseite: die 8 mm dicke Platte allein traegt
    # keinen Gewindeeinsatz (Wand 1,7 mm), mit Sockel sind es 16 mm Material.
    L['ls_sockel_y1'] = L['traeger_y1'] + w('ls_sockel_hoehe')
    L['ls_schraub_x'] = (w('traeger_x_links') + w('ls_sockel_x1')) / 2.0
    L['ls_schraub_z'] = [L['ls_sockel_z0'] + 8.0,
                         L['ls_sockel_z0'] + 8.0 + w('ls_schraub_abstand')]
    # Halter: Flansch auf dem Sockel, Wand links davon traegt die Platine.
    L['ls_flansch_y1'] = L['ls_sockel_y1'] + w('ls_flansch_dicke')
    L['ls_wand_x1'] = w('traeger_x_links') - w('ls_wand_versatz')
    L['ls_wand_x0'] = L['ls_wand_x1'] - w('ls_halter_dicke')
    # Die Platine sitzt auf der Wand, die auf dem Flansch steht — beide
    # beginnen also auf der Sockelflaeche, damit das Teil plan aufs Bett geht.
    L['ls_pcb_y0'] = L['ls_flansch_y1'] + w('ls_pcb_luft')
    L['ls_pcb_y1'] = L['ls_pcb_y0'] + w('ls_pcb_breite')
    L['ls_wand_y1'] = L['ls_pcb_y1'] + 1.0
    # Die Fahne laeuft in der Schlitzmitte der Gabel, also mittig zur Platine.
    L['ls_fahne_y0'] = ((L['ls_pcb_y0'] + L['ls_pcb_y1']) / 2.0
                        - w('ls_fahne_dicke') / 2.0)
    L['ls_fahne_y1'] = L['ls_fahne_y0'] + w('ls_fahne_dicke')
    L['ls_pcb_loch_y'] = [L['ls_pcb_y0'] + w('ls_pcb_rand'),
                          L['ls_pcb_y1'] - w('ls_pcb_rand')]
    L['ls_pcb_loch_z'] = L['ls_pcb_z1'] - w('ls_pcb_rand')
    # Fahne in X: vor der Platine beginnen, damit sie den Strahl quert, und
    # vor dem Z-Wagen enden.
    L['ls_fahne_x0'] = (L['ls_wand_x1'] + w('ls_pcb_dicke')
                        + w('ls_fahne_luft_pcb'))
    L['ls_fahne_x1'] = L['ls_fahne_x0'] + w('ls_fahne_tiefe')
    # Oberkante der Fahne = Oberkante der Schlittenplatte; sie schaltet also,
    # wenn die Platte in die Gabel einfaehrt.
    L['ls_fahne_z1_rel'] = L['schlitten_oben_rel']
    L['ls_fahne_z0_rel'] = L['ls_fahne_z1_rel'] - w('ls_fahne_hoehe')

    # ---- Grenzen der Langlochstellung (mm nach oben, 0 = Lochmitte).
    #      Nach oben bindet die MONTAGE: schiebt man den Laser hoch, wandert
    #      die obere Schraubenreihe hinter den Z-Wagen und ist nicht mehr zu
    #      erreichen. Nach unten bindet der Hub selbst.
    L['langloch_auf_max'] = -(w('z_wagen_laenge') / 2.0
                              + w('inbus_frei_d') / 2.0) \
        - L['laser_loch_oben_rel']
    L['langloch_auf_max'] = min(L['langloch_auf_max'], w('laser_langloch_hub'))
    L['langloch_ab_max'] = -w('laser_langloch_hub')

    # ---- Schraubenlaenge Schlittenplatte -> Z-Wagen -------------------------
    # Naechste gerade Laenge ueber pad_hoehe + Mindesteingriff. Nicht
    # verdrahten: sie muss mit pad_hoehe mitwandern, sonst passt sie nach einer
    # Parameteraenderung stillschweigend nicht mehr.
    L['z_wagen_schraube'] = 2.0 * int((w('pad_hoehe') + 1.5) / 2.0 + 0.999)
    L['z_wagen_eingriff'] = L['z_wagen_schraube'] - w('pad_hoehe')

    # ---- Schraubenlaenge Mutternwinkel -> Schlittenplatte -------------------
    # Geklemmt werden Platte + Ruecken bis zur Mutter, die in der Tasche
    # sitzt. Plus grosse Scheibe (0,8) und 1 mm Reserve, aufgerundet auf die
    # naechste gerade Laenge.
    L['winkel_klemm'] = (w('schlitten_dicke') + w('winkel_ruecken')
                         - (w('m3_mutter_h') + 0.3) + w('m3_mutter_h'))
    L['winkel_schraube'] = 2.0 * int((L['winkel_klemm'] + 0.8 + 1.0) / 2.0
                                     + 0.999)

    # ---- Benoetigte Laenge der Gewindespindel -------------------------------
    # Unten muss sie die Flanschmutter in der tiefsten Stellung noch ganz
    # tragen (die Mutter steht auf dem Regal, greift also ab Regaloberseite
    # nach oben) plus 5 mm Anlauf.
    L['spindel_z0'] = L['zc_min'] + L['regal_z1_rel'] - 5.0
    L['spindel_laenge'] = L['spindel_z1'] - L['spindel_z0']
    # Unteres Ende nach dem Kuerzen — und was ungekuerzt daraus wuerde.
    L['spindel_z0_ist'] = L['spindel_z1'] - w('spindel_zuschnitt')
    L['spindel_z0_lang'] = L['spindel_z1'] - w('spindel_bestellt')
    frei = lambda z: min(L['werkstueck_frei'], z + w('bett_abstand') - 5.0)
    L['werkstueck_frei_ist'] = frei(L['spindel_z0_ist'])
    L['werkstueck_frei_lang'] = frei(L['spindel_z0_lang'])

    # ---- Lochbilder (absolute Lagen, X/Z) -----------------------------------
    L['x_wagen_loecher'] = [
        (sx * w('x_wagen_loch_laengs') / 2.0, sz * w('x_wagen_loch_quer') / 2.0)
        for sx in (-1, 1) for sz in (-1, 1)]
    n = int(round((w('z_schiene_laenge') - 2 * w('z_schiene_randab'))
                  / w('z_schiene_lochab'))) + 1
    L['z_schiene_loecher'] = [
        L['z_schiene_z0'] + w('z_schiene_randab') + i * w('z_schiene_lochab')
        for i in range(n)]
    # Motorkonsole: Teil der Traegerplatte, kein eigenes Bauteil.
    L['konsole_x0'] = w('spindel_x') - w('motor_flansch') / 2.0 - w('konsole_rand')
    L['konsole_x1'] = w('spindel_x') + w('motor_flansch') / 2.0 + w('konsole_rand')

    # Der Motor wird von UNTEN verschraubt — NEMA17 hat Gewinde im Flansch, ein
    # Durchstecken von oben ist nicht moeglich. Beide Schraubenreihen liegen
    # jetzt vor der Traegerplatte, es sind also alle VIER erreichbar. Die
    # Fuehrungsrippen bleiben: der Motor findet damit beim Einsetzen selbst
    # seine Lage und die Schrauben muessen kein Moment uebertragen.
    # Pruefung der Zugangskorridore: tools/toolhead_check.py.
    innen = w('motor_flansch') / 2.0 + w('spiel_locker') / 2.0
    L['motor_rippe_x'] = [
        (w('spindel_x') - innen - w('motor_rippe_breite'),
         w('spindel_x') - innen),
        (w('spindel_x') + innen,
         w('spindel_x') + innen + w('motor_rippe_breite'))]
    L['motor_rippe_y1'] = w('spindel_y') + w('motor_flansch') / 2.0
    L['motor_rippe_z1'] = L['konsole_z1'] + w('motor_rippe_hoehe')
    L['motor_schrauben'] = [
        (w('spindel_x') + sx * w('motor_loch') / 2.0,
         w('spindel_y') + sy * w('motor_loch') / 2.0)
        for sy in (-1, 1) for sx in (-1, 1)]
    # Freie Luft zwischen dem Zugangskorridor der hinteren Reihe und der
    # Vorderseite der Traegerplatte — die Groesse, die spindel_y bestimmt.
    L['korridor_luft'] = (w('spindel_y') - w('motor_loch') / 2.0
                          - 3.0 - w('traeger_dicke'))

    # Lochbild des Z-Wagens, relativ zur Wagenmitte zc
    L['z_wagen_loecher'] = [
        (sx * w('z_wagen_loch_quer') / 2.0, sz * w('z_wagen_loch_laengs') / 2.0)
        for sx in (-1, 1) for sz in (-1, 1)]
    # Schwimmende Verschraubung des Mutternwinkels, links und rechts der
    # Spindel. 5 mm Randabstand: die Sechskanttasche der M3-Mutter ist ueber
    # Eck 6,5 mm breit und braucht noch Wand zum Rand.
    L['winkel_schraube_x'] = [w('winkel_x_links') + 5.0,
                              w('winkel_x_rechts') - 5.0]

    L['motor_loecher'] = [
        (w('spindel_x') + sx * w('motor_loch') / 2.0,
         w('spindel_y') + sy * w('motor_loch') / 2.0)
        for sx in (-1, 1) for sy in (-1, 1)]
    return L


# --- Materialien -------------------------------------------------------------
# Weicht vom Standardblock der SKILL.md ab. Der dortige Helfer sucht das
# Basismaterial unter dem englischen Namen "ABS Plastic" und faellt sonst auf
# eine TEILSTRING-Suche nach dem eigenen Namen zurueck. In einer deutschen
# Fusion-Installation ist die Folge:
#   PETG -> Teilstring "petg" findet nichts -> kein Material gesetzt ->
#           der Koerper behaelt den Design-Default, also STAHL (7,85 g/cm3)
#   PLA  -> Teilstring "pla"  findet z.B. "Plaster"/"Plastic" -> ~1,8 g/cm3
# Beides laeuft ohne Fehlermeldung durch; im Bericht standen deshalb 608 g
# fuer die Traegerplatte. Deshalb hier:
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


def langloch_senkrecht(sk, u, v, breite_mm, hub_mm):
    """Senkrechtes Langloch (Achse = Maschine Z) als zwei Kreise plus
    Rechteck, Masse in mm. Beim Schneiden werden ALLE Profile der Skizze
    entfernt; die Vereinigung ergibt das Langloch. Robuster als ein aus
    Linien und Boegen zusammengesetztes Profil, das bei Rundungsfehlern nicht
    schliesst — diese Variante ist in Fusion bereits gelaufen (Rev. 10/11,
    damals quer).
    """
    r = breite_mm / 2.0
    kreis(sk, u, v - hub_mm, breite_mm)
    kreis(sk, u, v + hub_mm, breite_mm)
    rechteck(sk, u - r, v - hub_mm, u + r, v + hub_mm)


def sechskant(sk, cu, cv, sw, flach_quer=True):
    """Regelmaessiges Sechskant ueber die Schluesselweite sw (Abstand der
    parallelen Flanken), Masse in mm.

    flach_quer=True: zwei Flanken stehen senkrecht zur v-Achse. Die Mutter wird
    dann in v-Richtung eingeschoben und liegt am Taschenboden mit einer FLANKE
    an, nicht mit einer Ecke — sie kann nicht kippen und sitzt formschluessig
    auf allen sechs Flanken.

    Die Ecken werden ueber die SketchPoints der Nachbarlinien verkettet, damit
    das Profil sicher schliesst.
    """
    r = sw / math.sqrt(3.0)                      # Umkreisradius
    start = 0.0 if flach_quer else 30.0
    ecken = [(cu + r * math.cos(math.radians(start + i * 60.0)),
              cv + r * math.sin(math.radians(start + i * 60.0)))
             for i in range(6)]
    linien = sk.sketchCurves.sketchLines
    erste = linien.addByTwoPoints(punkt(sk, *ecken[0]), punkt(sk, *ecken[1]))
    vorher = erste
    for i in range(1, 5):
        vorher = linien.addByTwoPoints(vorher.endSketchPoint,
                                       punkt(sk, *ecken[i + 1]))
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


def weg(comp, prof, hoehe_mm, ziel):
    return extrudieren(comp, prof, hoehe_mm,
                       adsk.fusion.FeatureOperations.CutFeatureOperation, ziel)


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


def durch(comp, prof, ziel, reichweite_mm=400.0):
    """Durchgangsschnitt: symmetrisch und grosszuegig statt ThroughAll, damit
    die Normalenrichtung der Skizzenebene keine Rolle spielt. participantBodies
    begrenzt die Wirkung auf den Zielkoerper."""
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


def langloch_stellung(L, f_mm, dicke_mm):
    """Welche Langlochstellung (mm nach oben) passt zu einem Fokusabstand f?
    Dickes Material braucht die Linse oben (dicke + f ueber dem Bett), duennes
    unten (f ueber dem Bett). Liefert (von, bis); von > bis heisst, der
    Verfahrweg reicht fuer diesen Dickenbereich nicht.
    """
    return (dicke_mm + f_mm - L['linse_hoch'], f_mm - L['linse_tief'])


def fokus_zeilen(L, w, kandidaten=(15.0, 20.0, 25.0, 30.0, 35.0)):
    """Berichtszeilen: welche Langlochstellung passt zu welchem Fokusabstand?
    Geht eine Dicke nicht mehr auf, wird gesagt, was stattdessen erreichbar
    ist — die Stellung ist nach oben durch die Montage begrenzt."""
    zeilen = []
    for f in kandidaten:
        von, bis = langloch_stellung(L, f, w('werkstueck_max'))
        von = max(von, L['langloch_ab_max'])         # Hub nach unten
        bis = min(bis, L['langloch_auf_max'])        # Montage nach oben
        if von <= bis:
            # Innerhalb des gueltigen Fensters moeglichst die Lochmitte, dann
            # bleibt in beide Richtungen Luft zum Nachstellen.
            stellung, hinweis = min(max(0.0, von), bis), 'passt'
        else:
            stellung = L['langloch_auf_max']
            hinweis = 'nur {:.0f} mm Werkstueck'.format(
                L['linse_hoch'] + stellung - f)
        zeilen.append('    f = {:.0f} mm  ->  Laser {:+.1f} mm  ({})'.format(
            f, stellung, hinweis))
    return zeilen


# --- Bauteile ----------------------------------------------------------------
def bau_traegerplatte(app, design, comp, L, fehler):
    """Traegerplatte MIT angeformter Motorkonsole — ein Druckteil.

    Ein separater Motorhalter brachte keinen Vorteil: die hintere
    Schraubenreihe des NEMA 17 liegt ueber dem Querschnitt der Platte und ist
    von unten so oder so nicht erreichbar. Angeformt entfaellt dafuer die
    Verschraubung Halter/Platte vollstaendig, und die Konsole wird steifer.

    Der Motor sitzt oben auf der Konsole (Welle nach unten durch die
    Bundbohrung), gehalten von der vorderen Schraubenreihe und zwei
    Fuehrungsrippen, die den Flansch seitlich fassen und das Motormoment
    formschluessig aufnehmen.

    Drucklage: Rueckseite (Passflaeche) aufs Bett, Aufbaurichtung = Maschine Y.
    Platte, Sockel, Konsole und Rippen stehen dann alle auf dem Bett — kein
    Stuetzmaterial, und alle Kraefte liegen in der Schicht."""
    e_hinten = ebene_y(comp, 0.0, 'E_Traeger_hinten')
    e_vorn = ebene_y(comp, L['traeger_y1'], 'E_Traeger_vorn')
    e_sockel = ebene_y(comp, L['sockel_y1'], 'E_Sockel_vorn')
    e_konsole = ebene_z(comp, (L['konsole_z0'] + L['konsole_z1']) / 2.0,
                        'E_Konsole_mitte')

    sk = skizze(comp, e_hinten, 'Sk_Hauptsaeule')
    rechteck(sk, w('traeger_x_links'), w('traeger_z_unten'),
             w('traeger_x_rechts'), w('traeger_kopf_unten'))
    koerper = neu(comp, groesstes_profil(sk), w('traeger_dicke')).bodies.item(0)
    koerper.name = 'Traegerplatte'

    # Kopfbereich: verbreitert sich nach rechts und traegt die Konsole
    sk = skizze(comp, e_hinten, 'Sk_Kopfbereich')
    rechteck(sk, w('traeger_x_links'), w('traeger_kopf_unten'),
             w('traeger_x_kopf'), L['konsole_z0'])
    dazu(comp, groesstes_profil(sk), w('traeger_dicke'), koerper)

    # Motorkonsole: waagerechte Platte, kragt nach vorn aus
    sk = skizze(comp, e_hinten, 'Sk_Motorkonsole')
    rechteck(sk, L['konsole_x0'], L['konsole_z0'], L['konsole_x1'],
             L['konsole_z1'])
    dazu(comp, groesstes_profil(sk), w('konsole_y_vorn'), koerper)

    # Fuehrungsrippen: fassen den Motorflansch links und rechts
    sk = skizze(comp, e_hinten, 'Sk_Fuehrungsrippen')
    for x0, x1 in L['motor_rippe_x']:
        rechteck(sk, x0, L['konsole_z1'], x1, L['motor_rippe_z1'])
    dazu(comp, alle_profile(sk), L['motor_rippe_y1'], koerper)

    # Schienensockel: genau so breit wie die Schiene, damit die Schuerzen des
    # Wagens frei laufen; 5 mm hoch, damit die M3-Inserts 7 mm tief sitzen.
    sk = skizze(comp, e_vorn, 'Sk_Schienensockel')
    rechteck(sk, -w('sockel_breite') / 2, L['z_schiene_z0'],
             w('sockel_breite') / 2, L['z_schiene_z1'])
    dazu(comp, groesstes_profil(sk), w('sockel_hoehe'), koerper)

    # Versteifung der Saeule: zwei Rippen an den Saeulenkanten, von der
    # Plattenunterkante bis unter die Konsole. Sie tragen das Kragmoment des
    # Motors — ohne sie biegt die 8-mm-Platte am oberen Ende um 0,57 mm durch,
    # mit ihnen um 0,22 mm. Drucklage bleibt: sie stehen wie der Sockel nach
    # oben, kein Stuetzmaterial.
    sk = skizze(comp, e_vorn, 'Sk_Saeulenrippen')
    for x0, x1 in L['saeule_rippe_x']:
        rechteck(sk, x0, w('traeger_z_unten'), x1, L['konsole_z0'])
    dazu(comp, alle_profile(sk), w('saeule_rippe_tiefe'), koerper)

    # Verschraubung zum X-Wagen (Kopf liegt frei vor der Platte)
    sk = skizze(comp, e_hinten, 'Sk_Bohrungen_XWagen')
    for x, z in L['x_wagen_loecher']:
        kreis(sk, x, z, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Sacklochbohrungen fuer die Gewindeeinsaetze der Z-Schiene: von der
    # Sockelflaeche NACH HINTEN, deshalb negative Extrusion.
    sk = skizze(comp, e_sockel, 'Sk_Inserts_Schiene')
    for z in L['z_schiene_loecher']:
        kreis(sk, 0.0, z, w('insert_m3_d'))
    weg(comp, alle_profile(sk), -w('insert_m3_t'), koerper)

    # Bundbohrung und die beiden erreichbaren Motorschrauben
    sk = skizze(comp, e_konsole, 'Sk_Motorbefestigung')
    kreis(sk, w('spindel_x'), w('spindel_y'),
          w('motor_bund_d') + w('spiel_locker'))
    for x, y in L['motor_schrauben']:
        kreis(sk, x, y, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Sockel fuer den Endschalterhalter. Die 8 mm dicke Platte allein traegt
    # keinen Gewindeeinsatz (Ø4,6 laesst nur 1,7 mm Wand), mit dem Sockel sind
    # es 16 mm Material. Er endet 3 mm vor dem Z-Wagen.
    sk = skizze(comp, e_vorn, 'Sk_Endschaltersockel')
    rechteck(sk, w('traeger_x_links'), L['ls_sockel_z0'],
             w('ls_sockel_x1'), L['ls_sockel_z1'])
    dazu(comp, groesstes_profil(sk), w('ls_sockel_hoehe'), koerper)

    sk = skizze(comp, ebene_y(comp, L['ls_sockel_y1'], 'E_LS_Sockel'),
                'Sk_Inserts_Endschalter')
    for z in L['ls_schraub_z']:
        kreis(sk, L['ls_schraub_x'], z, w('insert_m3_d'))
    weg(comp, alle_profile(sk), -w('insert_m3_t'), koerper)

    fussfase(comp, koerper, 'z', 0.0, w('fase_fuss'), fehler, 'Traegerplatte')
    bbox_pruefen(koerper, 'Traegerplatte',
                 ((w('traeger_x_links'), w('traeger_x_kopf')),
                  (L['traeger_y0'], w('konsole_y_vorn')),
                  (w('traeger_z_unten'), L['motor_rippe_z1'])), fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def bau_schlittenplatte(app, design, comp, L, zc, fehler):
    """Auf dem MGN9H-Z-Wagen: Auflagepad + Rippen, davor die Platte mit dem
    Laser-Lochbild, rechts eine Lasche fuer den Mutternwinkel.
    Drucklage: Laser-Anschraubflaeche aufs Bett, Aufbaurichtung = -Maschine Y
    (im Slicer spiegeln/drehen), oder Pad-Rueckseite unten mit Stuetzen."""
    e_pad = ebene_y(comp, L['schlitten_y0'], 'E_Pad_hinten')
    e_platte = ebene_y(comp, L['schlitten_y1'], 'E_Platte_hinten')
    z_u = zc + L['schlitten_unten_rel']
    z_o = zc + L['schlitten_oben_rel']

    sk = skizze(comp, e_pad, 'Sk_Auflagepad')
    rechteck(sk, -w('pad_breite') / 2, zc - w('pad_laenge') / 2,
             w('pad_breite') / 2, zc + w('pad_laenge') / 2)
    koerper = neu(comp, groesstes_profil(sk), w('pad_hoehe')).bodies.item(0)
    koerper.name = 'Schlittenplatte'

    sk = skizze(comp, e_pad, 'Sk_Mittelrippe')
    rechteck(sk, -w('rippe_mitte_breite') / 2, z_u,
             w('rippe_mitte_breite') / 2, z_o)
    dazu(comp, groesstes_profil(sk), w('pad_hoehe'), koerper)

    # Nur links eine Seitenrippe — rechts sitzt der Mutternwinkel.
    sk = skizze(comp, e_pad, 'Sk_Seitenrippe')
    rechteck(sk, -w('schlitten_breite_l'), z_u, -w('rippe_seite_innen'), z_o)
    dazu(comp, groesstes_profil(sk), w('pad_hoehe'), koerper)

    sk = skizze(comp, e_platte, 'Sk_Platte')
    rechteck(sk, -w('schlitten_breite_l'), z_u, w('schlitten_breite_l'), z_o)
    dazu(comp, groesstes_profil(sk), w('schlitten_dicke'), koerper)

    # Lasche fuer den Mutternwinkel: sie reicht nach oben bis an die
    # Plattenoberkante (dort setzt das Regal des Winkels an) und nach unten
    # 3 mm unter den Ruecken.
    sk = skizze(comp, e_platte, 'Sk_Lasche_Mutternwinkel')
    rechteck(sk, w('schlitten_breite_l'), zc + L['winkel_unten_rel'] - 3.0,
             w('winkel_x_rechts'), zc + L['schlitten_oben_rel'])
    dazu(comp, groesstes_profil(sk), w('schlitten_dicke'), koerper)

    # Verschraubung zum Z-Wagen: Durchgang im Pad, Freibohrung in der Platte
    sk = skizze(comp, e_pad, 'Sk_Bohrungen_ZWagen')
    for x, z in L['z_wagen_loecher']:
        kreis(sk, x, zc + z, w('m3_durchgang'))
    weg(comp, alle_profile(sk), w('pad_hoehe') + w('schlitten_dicke'), koerper)

    sk = skizze(comp, e_platte, 'Sk_Freibohrungen_ZWagen')
    for x, z in L['z_wagen_loecher']:
        kreis(sk, x, zc + z, w('m3_senkung'))
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    # Freiraum im Pad fuer Kopf + Scheibe der OBEREN Laserschraubenreihe —
    # nur noetig, solange diese Reihe ueberhaupt im Pad liegt. Seit der Laser
    # tiefer haengt (laser_versatz_z = -46), liegt sie darunter: kein Schnitt,
    # volle Auflage auf dem Wagen, und der Kanal wird auch nicht als
    # Werkzeugzugang gebraucht (der Laser kommt jetzt zuletzt dran).
    if L['laser_oben_im_pad']:
        sk = skizze(comp, e_pad, 'Sk_Kopffreiraum_Laser')
        for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2):
            kreis(sk, x, zc + L['laser_loch_oben_rel'], w('kopf_freiraum'))
        weg(comp, alle_profile(sk), w('pad_hoehe'), koerper)

    # Laser: SENKRECHTE Langloecher, 4,0 mm breit, +-laser_langloch_hub lang.
    # Quer bleibt es bei 4,0 mm und damit bei +-1,0 mm Lochbildtoleranz (das
    # Bohrbild ist am Teil bestaetigt); die Laenge ist die Hoehenverstellung
    # fuer den Fokusabstand des Moduls, der nicht auf dem Modul steht.
    sk = skizze(comp, e_platte, 'Sk_Langloecher_Laser')
    for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2):
        for rel in (L['laser_loch_oben_rel'], L['laser_loch_unten_rel']):
            langloch_senkrecht(sk, x, zc + rel, w('laser_loch_d'),
                               w('laser_langloch_hub'))
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    # Schaltfahne fuer die Gabellichtschranke: ein Block an der linken oberen
    # Ecke. Er waechst aus der Seitenrippe heraus und ist nach hinten von der
    # verbreiterten Plattenecke getragen — in der Drucklage (Laserflaeche auf
    # dem Bett, Aufbaurichtung -Y) steht damit jede Schicht auf Material.
    sk = skizze(comp, e_platte, 'Sk_Fahnenecke')
    rechteck(sk, L['ls_fahne_x0'], zc + L['ls_fahne_z0_rel'],
             -w('schlitten_breite_l'), zc + L['ls_fahne_z1_rel'])
    dazu(comp, groesstes_profil(sk), w('schlitten_dicke'), koerper)

    sk = skizze(comp, ebene_y(comp, L['ls_fahne_y0'], 'E_LS_Fahne'),
                'Sk_Schaltfahne')
    rechteck(sk, L['ls_fahne_x0'], zc + L['ls_fahne_z0_rel'],
             L['ls_fahne_x1'], zc + L['ls_fahne_z1_rel'])
    dazu(comp, groesstes_profil(sk),
         L['schlitten_y1'] - L['ls_fahne_y0'], koerper)

    # Schwimmende Verschraubung des Mutternwinkels: Uebermass zum Ausrichten
    sk = skizze(comp, e_platte, 'Sk_Bohrungen_Mutternwinkel')
    for x in L['winkel_schraube_x']:
        kreis(sk, x, zc, w('m3_uebermass'))
    weg(comp, alle_profile(sk), w('schlitten_dicke'), koerper)

    fussfase(comp, koerper, 'z', L['schlitten_y0'], w('fase_fuss'), fehler,
             'Schlittenplatte')
    # Die Platte reicht links bis an die Schaltfahne heran.
    bbox_pruefen(koerper, 'Schlittenplatte',
                 ((L['ls_fahne_x0'], w('winkel_x_rechts')),
                  (L['schlitten_y0'], L['laser_y']), (z_u, z_o)), fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def bau_endschalterhalter(app, design, comp, L, fehler):
    """Haelt die Gabellichtschranke links neben der Saeule.

    Eigenes Druckteil, mit Absicht: die genaue Gabelgeometrie des Moduls ist
    nicht vermessen (Strahlhoehe ueber der Platine angenommen). Ein Irrtum
    kostet hier 4 g statt der 154-g-Traegerplatte, und der Schaltpunkt bleibt
    ueber die Langloecher justierbar.
    Drucklage: Flansch aufs Bett, Wand steht nach oben — keine Stuetzen.
    """
    e_flansch = ebene_y(comp, L['ls_sockel_y1'], 'E_LS_Flansch')

    sk = skizze(comp, e_flansch, 'Sk_LS_Flansch')
    rechteck(sk, L['ls_wand_x0'], L['ls_sockel_z0'],
             w('ls_sockel_x1'), L['ls_sockel_z1'])
    koerper = neu(comp, groesstes_profil(sk),
                  w('ls_flansch_dicke')).bodies.item(0)
    koerper.name = 'Endschalterhalter'

    sk = skizze(comp, e_flansch, 'Sk_LS_Wand')
    rechteck(sk, L['ls_wand_x0'], L['ls_sockel_z0'],
             L['ls_wand_x1'], L['ls_sockel_z1'])
    dazu(comp, groesstes_profil(sk),
         L['ls_wand_y1'] - L['ls_sockel_y1'], koerper)

    # Anschraubung an den Sockel: Langloecher, damit der Schaltpunkt um
    # +-ls_justage verschoben werden kann, ohne neu zu drucken.
    sk = skizze(comp, e_flansch, 'Sk_LS_Anschraubung')
    for z in L['ls_schraub_z']:
        langloch_senkrecht(sk, L['ls_schraub_x'], z, w('m3_durchgang'),
                           w('ls_justage'))
    weg(comp, alle_profile(sk), w('ls_flansch_dicke'), koerper)

    # Platinenloecher quer durch die Wand — Ebene senkrecht zu Maschinen-X.
    # Zweistufig: vorn die Einpressbohrung fuer den M2-Einsatz, dahinter eine
    # schmalere Freibohrung. Der Einsatz sitzt damit auf Anschlag, und die
    # Schraubenspitze hat trotzdem Platz.
    e_platine = ebene_x(comp, L['ls_wand_x1'], 'E_LS_Platine')
    sk = skizze(comp, e_platine, 'Sk_LS_Einpressbohrung')
    for y in L['ls_pcb_loch_y']:
        kreis(sk, y, L['ls_pcb_loch_z'], w('ls_pcb_loch_d'))
    weg(comp, alle_profile(sk), -w('ls_pcb_loch_t'), koerper)

    sk = skizze(comp, e_platine, 'Sk_LS_Freibohrung')
    for y in L['ls_pcb_loch_y']:
        kreis(sk, y, L['ls_pcb_loch_z'], w('ls_pcb_frei_d'))
    weg(comp, alle_profile(sk), -w('ls_halter_dicke'), koerper)

    fussfase(comp, koerper, 'z', L['ls_sockel_y1'], w('fase_fuss'), fehler,
             'Endschalterhalter')
    bbox_pruefen(koerper, 'Endschalterhalter',
                 ((L['ls_wand_x0'], w('ls_sockel_x1')),
                  (L['ls_sockel_y1'], L['ls_wand_y1']),
                  (L['ls_sockel_z0'], L['ls_sockel_z1'])), fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def bau_mutternwinkel(app, design, comp, L, zc, fehler):
    """Winkel fuer die gekaufte Tr8x2-Anti-Backlash-Garnitur.

    Die Spielfreiheit kommt jetzt aus dem Kaufteil (zwei Mutternhaelften, von
    einer Feder gegeneinander gedrueckt) — das Druckteil muss nur noch einen
    plangedrehten Flanschsitz mit vier Gewinden liefern. Deshalb Winkel statt
    Block: senkrechter RUECKEN schwimmend an der Lasche der Schlittenplatte,
    darueber ein waagerechtes REGAL mit dem Lochkreis.

    Das Regal liegt UEBER der Oberkante der Schlittenplatte. Der Flansch hat
    Ø22 und sitzt mittig auf der Spindelachse (Y=28,5); die Plattenrueckseite
    liegt bei Y=35, es waeren also nur 6,5 mm — der Flansch wuerde in die
    Platte laufen. Ueber der Oberkante ist er frei, und pad_hoehe (und damit
    die Strahlachse) bleibt unveraendert.

    Die Garnitur steht NACH OBEN: nach unten ist kein Platz. Das kostet
    Verfahrweg nach oben (siehe zc_grenzen), aber der ist reichlich da.

    Drucklage: Regaloberseite (der Flanschsitz) aufs Bett, Aufbaurichtung
    = -Maschine Z. Der Ruecken haengt dann vollstaendig unter dem Regal, jede
    Schicht steht auf Material, Spindel- und Einsatzbohrungen werden rund."""
    e_ruecken = ebene_y(comp, (L['winkel_y0'] + L['schlitten_y1']) / 2.0,
                        'E_Winkel_Ruecken_mitte')
    e_hinten = ebene_y(comp, L['winkel_y0'], 'E_Winkel_hinten')
    e_regal = ebene_z(comp, zc + (L['regal_z0_rel'] + L['regal_z1_rel']) / 2.0,
                      'E_Regal_mitte')
    sx, sy = w('spindel_x'), w('spindel_y')

    # Ruecken: senkrechte Platte an der Lasche, symmetrisch um ihre Mittel-
    # ebene extrudiert (die Normalenrichtung der Offsetebene ist unbekannt).
    sk = skizze(comp, e_ruecken, 'Sk_Winkel_Ruecken')
    rechteck(sk, w('winkel_x_links'), zc + L['winkel_unten_rel'],
             w('winkel_x_rechts'), zc + L['regal_z1_rel'])
    koerper = neu_mittig(comp, groesstes_profil(sk),
                         w('winkel_ruecken')).bodies.item(0)
    koerper.name = 'Mutternwinkel'

    # Regal: so tief wie der Flansch, damit er rundum aufliegt.
    sk = skizze(comp, e_regal, 'Sk_Winkel_Regal')
    rechteck(sk, w('winkel_x_links'), L['regal_y0'],
             w('winkel_x_rechts'), L['regal_y1'])
    dazu_mittig(comp, groesstes_profil(sk), w('winkel_regal_dicke'), koerper)

    # Durchgang fuer die Spindel — durch Regal UND Ruecken: die Spindel laeuft
    # unter dem Regal weiter nach unten und steht bei Y=28,5 genau im Ruecken.
    # Vor der Bohrung bleibt dort eine duenne Haut stehen (Pruefung in
    # toolhead_check.py, Abschnitt 7) — sie haelt die beiden Schenkel des
    # Ruecken zusammen und gibt der Lasche eine durchgehende Anlageflaeche.
    sk = skizze(comp, e_regal, 'Sk_Spindeldurchgang')
    kreis(sk, sx, sy, w('spindel_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Vier Sacklochbohrungen fuer die M3-Messingeinsaetze auf dem Lochkreis.
    # Die Loecher im Flansch sind Durchgangsloecher, das Gewinde muss also
    # hier sitzen. Symmetrisch um die halbe Einsatztiefe geschnitten, damit
    # die Richtung der Ebenennormale keine Rolle spielt.
    e_einsatz = ebene_z(comp, zc + L['regal_z1_rel'] - w('insert_m3_t') / 2.0,
                        'E_Winkel_Einsaetze')
    sk = skizze(comp, e_einsatz, 'Sk_Einsaetze_Flansch')
    for x, y in L['t8_loecher']:
        kreis(sk, x, y, w('insert_m3_d'))
    tasche(comp, alle_profile(sk), w('insert_m3_t'), koerper)

    # Schwimmende Verschraubung: Durchgang im Ruecken, Sechskanttasche hinten.
    sk = skizze(comp, e_hinten, 'Sk_Bohrungen_Winkel')
    for x in L['winkel_schraube_x']:
        kreis(sk, x, zc, w('m3_durchgang'))
    durch(comp, alle_profile(sk), koerper)

    # Sechskant, damit die M3-Mutter beim Anziehen von der Tasche gehalten
    # wird und man sie nicht von hinten gegenhalten muss.
    sk = skizze(comp, e_hinten, 'Sk_Mutterntaschen_Winkel')
    for x in L['winkel_schraube_x']:
        sechskant(sk, x, zc, w('m3_mutter_sw') + w('tasche_spiel'))
    weg(comp, alle_profile(sk), w('m3_mutter_h') + 0.3, koerper)

    fussfase(comp, koerper, 'y', zc + L['regal_z1_rel'], w('fase_fuss'),
             fehler, 'Mutternwinkel')
    # Nach vorn bindet das Regal (bis regal_y1), nicht der Ruecken.
    bbox_pruefen(koerper, 'Mutternwinkel',
                 ((w('winkel_x_links'), w('winkel_x_rechts')),
                  (L['regal_y0'], L['regal_y1']),
                  (zc + L['winkel_unten_rel'], zc + L['regal_z1_rel'])),
                 fehler)
    material_zuweisen(app, design, koerper, 'PETG', fehler)
    return koerper


def bau_bohrlehren(app, design, comp, L, zc, fehler):
    """Duenne Lehrenplatten mit den kritischen Lochbildern — auflegen,
    anzeichnen, pruefen. Nach dem Lauf ausgeblendet (Konvention SKILL.md).
    Alle Lehren liegen hinter der Maschine auf einer eigenen Ebene.

    Eine Lehre gibt es nur fuer Lochbilder von Teilen, die dieses Skript NICHT
    selbst erzeugt: Kaufteile (X-Wagen, Z-Wagen, Laser). Damit weicht das
    bewusst von der SKILL.md-Konvention ab, die auch fuer Verbindungen zwischen
    zwei getrennt gedruckten Teilen eine Lehre vorsieht — fuer
    Mutternwinkel <-> Schlittenplatte waere sie ohne Nutzen: beide Lochbilder
    haengen an derselben Variable (winkel_schraube_x), und die Bohrung in der
    Platte ist mit m3_uebermass absichtlich groesser als die im Block, damit
    sich der Block schwimmend ausrichten laesst. Was eine Lehre pruefen
    wuerde, ist dort also schon als Verstellbarkeit eingebaut."""
    ebene = ebene_y(comp, -40.0, 'E_Bohrlehren')
    lehren = [
        ('XWagen', (-95.0, 0.0), L['x_wagen_loecher']),
        # Frueher trug diese Lehre beide MGN9-Lochbilder (10 und 16 mm laengs),
        # weil offen war, welcher Wagen verbaut ist. Am 2026-09-17 am Teil
        # geprueft: MGN9H, 16 mm. Die Lehre folgt jetzt dem Parameter.
        ('ZWagen', (-40.0, 55.0),
         [(x, z)
          for x in (-w('z_wagen_loch_quer') / 2, w('z_wagen_loch_quer') / 2)
          for z in (-w('z_wagen_loch_laengs') / 2,
                    w('z_wagen_loch_laengs') / 2)]),
        ('Laser', (-40.0, -45.0),
         [(x, z) for x in (-w('laser_loch_quer') / 2, w('laser_loch_quer') / 2)
          for z in (L['laser_loch_unten_rel'] - L['laser_loch_oben_rel'], 0.0)]),
    ]
    for name, (mx, mz), punkte in lehren:
        sk = skizze(comp, ebene, 'Sk_Bohrlehre_' + name)
        for u, v in punkte:
            kreis(sk, mx + u, mz + v, w('m3_durchgang'))
        us = [mx + u for u, _ in punkte]
        vs = [mz + v for _, v in punkte]
        rand = 8.0
        rechteck(sk, min(us) - rand, min(vs) - rand,
                 max(us) + rand, max(vs) + rand)
        lehre = neu(comp, groesstes_profil(sk), w('lehre_dicke')).bodies.item(0)
        lehre.name = 'Bohrlehre_' + name
        material_zuweisen(app, design, lehre, 'PLA', fehler)
        lehre.isLightBulbOn = False


def hinweise_bauen(L, zc, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/toolhead_check.py)."""
    # Lochbildtoleranz der Laser-Rundloecher (Schaft Ø3 im Loch, beide Loecher
    # koennen gegenlaeufig wandern)
    laser_tol = w('laser_loch_d') - 3.0
    h = [
        'BEZUGSEBENE: Ursprung = Mitte des X-Wagen-Lochbildes AUF seiner',
        '  Stirnflaeche. X = quer, Y = nach vorn, Z = senkrecht.',
        '  Im Modell ist Y und Z getauscht (Modell-Z = Maschine Y), damit',
        '  alle Plattenskizzen in einer Ebenenfamilie liegen.',
        '',
        'Y-KETTE (ab X-Wagen-Stirnflaeche):',
        '  Portalprofil ............ {:+.1f} mm'.format(L['portal_y']),
        '  Traegerplatte vorn ...... {:+.1f} mm'.format(L['traeger_y1']),
        '  Auflage der Z-Schiene ... {:+.1f} mm'.format(L['sockel_y1']),
        '  Stirnflaeche Z-Wagen .... {:+.1f} mm'.format(L['z_wagen_y']),
        '  Laser-Anschraubflaeche .. {:+.1f} mm'.format(L['laser_y']),
        '  Strahlachse ............. {:+.1f} mm'.format(L['strahl_y']),
        '',
        'Z-ACHSE:',
        '  Wagenmitte zc von {:+.1f} bis {:+.1f} mm'.format(
            L['zc_min'], L['zc_max']),
        '  nutzbarer Verfahrweg: {:.1f} mm'.format(L['z_weg']),
        '  begrenzt durch: {}'.format(L['zc_bindend']),
        '  gebaut bei zc = {:+.1f} mm (Mitte des Verfahrwegs)'.format(zc),
        '  Laser-Unterkante: {:+.1f} bis {:+.1f} mm'.format(
            L['zc_min'] + L['laser_unten_rel'],
            L['zc_max'] + L['laser_unten_rel']),
        '  Tr8x2-Spindel: {:.0f} mm benoetigt, {:.0f} mm bestellt,'.format(
            L['spindel_laenge'], w('spindel_bestellt')),
        '    KUERZEN auf {:.0f} mm (unteres Ende dann bei {:+.1f} mm).'.format(
            w('spindel_zuschnitt'), L['spindel_z0_ist']),
        '    Ungekuerzt haengt sie bis {:+.1f} mm und laesst nur noch'.format(
            L['spindel_z0_lang']),
        '    {:.0f} mm Werkstueck zu statt {:.0f} mm.'.format(
            L['werkstueck_frei_lang'], L['werkstueck_frei_ist']),
        '',
        'MOTORBEFESTIGUNG: NEMA17 hat Gewinde im Flansch, es wird also von',
        '  UNTEN verschraubt — durchstecken von oben geht nicht. Alle VIER',
        '  Schrauben (4x M3x12) sind erreichbar: die hintere Reihe liegt bei',
        '  Y={:+.1f} und damit {:.1f} mm vor der Traegerplatte (Y=0..{:.0f}).'.format(
            w('spindel_y') - w('motor_loch') / 2, L['korridor_luft'],
            w('traeger_dicke')),
        '  Genau dafuer sitzt die Spindelachse bei Y={:+.1f} und die'.format(
            w('spindel_y')),
        '  Schlittenplatte entsprechend weiter vorn (pad_hoehe={:.0f}).'.format(
            w('pad_hoehe')),
        '  Zwei Fuehrungsrippen ({:.0f} mm hoch) fassen den Flansch seitlich —'.format(
            w('motor_rippe_hoehe')),
        '  der Motor findet beim Einsetzen selbst seine Lage.',
        '  Die Konsole ist an die Traegerplatte angeformt: ein Druckteil,',
        '  keine Verschraubung Halter/Platte.',
        '',
        'ANTRIEB: NEMA 17 oben, Welle nach unten, Klemmkupplung 5->8 mm auf',
        '  eine Tr8x2-Trapezgewindespindel. Die Spindel hat keinen ange-',
        '  drehten Zapfen: die Klemmnabe greift auf die Gewindespitzen. Das',
        '  Moment dafuer ist klein (Rechnung in toolhead_check.py, 7).',
        '  SPIELFREIHEIT kommt aus der gekauften Anti-Backlash-Garnitur:',
        '  Flanschmutter und Gleitmutter, von einer Feder gegeneinander',
        '  gedrueckt. Das Druckteil liefert nur den Flanschsitz.',
        '  MUTTERNWINKEL: senkrechter Ruecken ({:.0f} mm) an der Lasche der'.format(
            w('winkel_ruecken')),
        '  Schlittenplatte, darueber das Regal ({:.0f} mm) mit dem Lochkreis'.format(
            w('winkel_regal_dicke')),
        '  Ø{:.0f}. Das Regal liegt {:.1f} mm UEBER der Plattenoberkante —'.format(
            w('t8_lochkreis'), w('winkel_luft')),
        '  der Ø{:.0f}-Flansch sitzt mittig auf der Spindelachse (Y={:.1f})'.format(
            w('t8_flansch_d'), w('spindel_y')),
        '  und wuerde hinter der Platte (Y={:.0f}) nicht durchgehen.'.format(
            L['schlitten_y1']),
        '  Die Garnitur steht NACH OBEN: nach unten ist kein Platz. Sie',
        '  begrenzt damit den Verfahrweg nach oben (Bauhoehe {:.0f} mm [?]).'.format(
            w('t8_garnitur_h')),
        '  OBEN KEIN LAGER: die Spindel haengt am Motorlager, das traegt',
        '  Schlitten und Spindel zusammen (5,6 N gegen typ. 10 N) und die',
        '  kritische Biegedrehzahl liegt bei 50000 1/min gegen 300 im',
        '  Betrieb. Ein Gleitlager kaeme ohnehin nur auf die Gewindespitzen.',
        '  Damit traegt die KUPPLUNG die Z-Last axial: nur einteilige nehmen',
        '  (starre Klemmhuelse oder Wendelkupplung). Oldham- und Klauen-',
        '  kupplungen halten ihre Naben nicht axial zusammen — der Schlitten',
        '  wuerde absinken. Klemmnabe statt Madenschraube, nachziehen.',
        '  WENDELKUPPLUNG: nur bis zur massiven Nabe einstecken ({:.0f} mm je'.format(
            w('kupplung_griff')),
        '  Seite), dazwischen bleibt der Wendelschnitt ueber {:.0f} mm frei.'.format(
            L['kupplung_frei']),
        '  Stossen Welle und Spindel dort zusammen, ist die Nachgiebigkeit',
        '  ueberbrueckt — dann ist es eine starre Huelse mit Sollbruchstelle.',
        '  GEWINDE IM DRUCKTEIL: die Flanschloecher sind Durchgangsloecher,',
        '  also 4x M3-Messingeinsatz Ø{:.1f} x {:.0f} von oben ins Regal.'.format(
            w('insert_m3_d'), w('insert_m3_t')),
        '  Der Lochkreis ist um 45 Grad gedreht, damit das Regal in Y',
        '  schlank bleibt; der runde Flansch laesst sich beliebig drehen.',
        '  Die beiden M3-Muttern der schwimmenden Verschraubung sitzen in',
        '  Sechskanttaschen (SW+{:.2f}) und muessen nicht gegengehalten'.format(
            w('tasche_spiel')),
        '  werden. Der Winkel ist mit Uebermass ({:.1f} statt {:.1f}) ver-'.format(
            w('m3_uebermass'), w('m3_durchgang')),
        '  schraubt: Z-Achse mehrmals durchfahren, DANN festziehen. So',
        '  kaempft die krumme Spindel nicht gegen die Linearfuehrung.',
        '',
        'MONTAGEREIHENFOLGE (wichtig, sonst kommt man nicht mehr dran):',
        '  1. Gewindeeinsaetze in den Schienensockel einschmelzen',
        '  2. Traegerplatte an den X-Wagen (4x M3x12 + Scheibe) — die Koepfe',
        '     sind spaeter von der Schlittenplatte verdeckt. Schlanken Inbus',
        '     nehmen, der Korridor streift den Z-Wagen um 0,5 mm.',
        '  3. Z-Schiene auf den Sockel ({:.0f}x Senkkopf M3x10 in die'.format(
            len(L['z_schiene_loecher'])),
        '     Inserts): der Wagen verdeckt je Stellung zwei Schrauben —',
        '     erst mit dem Wagen unten, die letzten zwei mit ihm oben',
        '  4. Schlittenplatte auf den Z-Wagen (4x M3x{:.0f} von vorn durch die'.format(
            L['z_wagen_schraube']),
        '     Freibohrungen) — nur solange der Laser NICHT dran ist',
        '  5. Gewindeeinsaetze ins Regal des Mutternwinkels einschmelzen,',
        '     2x M3-Mutter in die Taschen des Ruecken',
        '  6. Motor zwischen die Fuehrungsrippen, 4x M3x12 von unten —',
        '     mit dem Z-Schlitten unten bequemer (164 statt 28 mm Platz)',
        '  7. Spindel auf {:.0f} mm kuerzen, entgraten, anfasen. Mutternwinkel'.format(
            w('spindel_zuschnitt')),
        '     an die Lasche (2x M3x{:.0f} + grosse Scheibe von'.format(
            L['winkel_schraube']),
        '     vorn). Garnitur auf die Spindel drehen, Flansch aufs Regal',
        '     (4x M3x8 von oben), dann die Spindel oben in die Kupplung —',
        '     nur bis zur Nabe, nicht bis an die Motorwelle.',
        '     Alles lose lassen, mehrmals durchfahren, DANN festziehen',
        '  8. Laser ZULETZT, 4x M3x10 + Scheibe von hinten, Z-Schlitten',
        '     dafuer nach unten fahren ({:.0f} mm freier Korridor)'.format(
            L['schlitten_y1'] - L['traeger_y1']),
        '  9. Endschalterhalter auf den Sockel (2x M3x12 in die Einsaetze),',
        '     Lichtschranke aufschrauben, Schaltpunkt im Langloch einstellen',
        '',
        'FOKUS UND LANGLOCH (senkrechte Langloecher, +-{:.0f} mm):'.format(
            w('laser_langloch_hub')),
        '  Der Fokusabstand f des Moduls steht nicht auf dem Modul. Statt ihn',
        '  in die Geometrie zu giessen, ist die Laserhoehe verstellbar:',
        '  Linse ueber dem Bett in Lochmitte ... {:.1f} bis {:.1f} mm'.format(
            L['linse_tief'], L['linse_hoch']),
        '  Werkstueck moeglich bis ........... {:.0f} mm (nicht der'.format(
            L['werkstueck_frei']),
        '    Verfahrweg begrenzt das, sondern die Plattenunterkante: sie',
        '    faehrt in X mit und muss ueber dem Werkstueck bleiben)',
        '  nutzbare Langlochstellung ......... {:+.1f} bis {:+.1f} mm'.format(
            L['langloch_ab_max'], L['langloch_auf_max']),
        '  Nach oben bindet nicht der Hub, sondern die Montage: hoeher',
        '  gestellt wandert die obere Schraubenreihe hinter den Z-Wagen.',
        '  Einstellung fuer {:.0f} mm Werkstueck (bett_abstand {:.0f} mm):'.format(
            w('werkstueck_max'), w('bett_abstand')),
    ] + fokus_zeilen(L, w) + [
        '',
        'ENDSCHALTER: Gabellichtschranke (LM393-Modul) links neben der',
        '  Saeule, Schaltfahne an der oberen linken Ecke der Schlittenplatte.',
        '  Referenziert wird NACH OBEN, weg vom Werkstueck.',
        '  Schaltpunkt (Strahlachse) ... Z = {:+.1f} mm'.format(L['ls_strahl_z']),
        '  danach bis zur Grenze ....... {:.0f} mm'.format(w('ls_ueberfahrt')),
        '  justierbar ueber Langloecher  +-{:.0f} mm'.format(w('ls_justage')),
        '  Die Strahlhoehe ueber der Platine ist ANGENOMMEN ({:.0f} mm). Die'.format(
            w('ls_strahl_ab_kante')),
        '  Fahne deckt {:.1f} bis {:.1f} mm ab, der Halter justiert den Rest.'.format(
            w('ls_fahne_luft_pcb'),
            w('ls_fahne_luft_pcb') + w('ls_fahne_tiefe')),
        '  Fahne {:.0f} mm dick im {:.0f}-mm-Spalt — je Seite {:.0f} mm Luft.'.format(
            w('ls_fahne_dicke'), w('ls_schlitz'),
            (w('ls_schlitz') - w('ls_fahne_dicke')) / 2),
        '  VOR DEM DRUCK: Modul an den Halter halten und pruefen, dass die',
        '  Gabel zur Fahne zeigt. Die Fahne muss undurchsichtig sein —',
        '  helles PETG laesst Infrarot durch, also dunkel drucken.',
        '',
        'GEWINDEEINSAETZE (Z-Schiene -> Sockel, {:.0f} Stueck):'.format(
            len(L['z_schiene_loecher'])),
        '  Einpressbohrung Ø{:.1f} mm, {:.0f} mm tief (Sackloch) — {:.1f} mm'.format(
            w('insert_m3_d'), w('insert_m3_t'),
            5.0 - w('insert_m3_d')),
        '  unter dem Aussendurchmesser, damit der Einsatz greift.',
        '  Wand je Seite im Sockel .... {:.2f} mm (Minimum 2,0)'.format(
            (w('sockel_breite') - w('insert_m3_d')) / 2.0),
        '  Material hinter der Bohrung  {:.1f} mm'.format(
            w('sockel_hoehe') + w('traeger_dicke') - w('insert_m3_t')),
        '  Der Sockel ist genau so breit wie die Schiene ({:.0f} mm) und kann'.format(
            w('sockel_breite')),
        '  nicht breiter werden — sonst streifen die Wagenschuerzen. Die',
        '  Bohrung ist damit die engste Stelle im Teil: beim Einschmelzen',
        '  wenig Druck, Einsatz buendig, nicht ueberhitzen.',
        '',
        'LEHREN — nur fuer KAUFTEIL-Lochbilder; fuer',
        '  Mutternwinkel <-> Schlittenplatte braucht es keine, beide kommen aus',
        '  diesem Skript und die Platte hat dort Uebermass zum Ausrichten:',
        '  Bohrlehre_XWagen ...... {:.0f} x {:.0f} mm (MGN15H, am Teil '
        'bestaetigt)'.format(
            w('x_wagen_loch_laengs'), w('x_wagen_loch_quer')),
        '  Bohrlehre_ZWagen ...... {:.0f} x {:.0f} mm (MGN9H, am Teil bestaetigt)'.format(
            w('z_wagen_loch_laengs'), w('z_wagen_loch_quer')),
        '  Bohrlehre_Laser ....... {:.2f} x {:.2f} mm (am Teil bestaetigt)'.format(
            w('laser_loch_hoch'), w('laser_loch_quer')),
        '    Lehre Ø{:.1f} rund; in der Platte senkrechtes Langloch {:.1f}'.format(
            w('m3_durchgang'), w('laser_loch_d')),
        '    breit: Lochbildtoleranz +-{:.1f} mm quer.'.format(laser_tol),
        '  Alle drei Lochbilder sind damit am realen Teil bestaetigt. Beim',
        '  X-Wagen war die Frage, ob dort ein MGN15H (25 x 25) oder ein',
        '  MGN15C (25 x 20) sitzt und wohin die alte Messung "26 x 25 mm am',
        '  Toolhead-Wagen" gehoert. Die Lehre passt: es ist ein MGN15H, und',
        '  1 mm Abweichung wuerde eine Ø3,4-Lehre auf M3 nicht durchlassen.',
        '',
        'MATERIAL: Druckteile PETG ({:.2f} g/cm3), Bohrlehren PLA ({:.2f}).'.format(
            ZIELDICHTE['PETG'], ZIELDICHTE['PLA']),
        '  Die Dichte wird nach der Zuweisung eingemessen und korrigiert —',
        '  Bibliotheksnamen sind lokalisiert, ein Kopiervorlage-Treffer allein',
        '  garantiert die Dichte nicht. Steht oben eine andere Dichte, sind',
        '  die Massen falsch (Fusion-Default ist Stahl, 7,85).',
        '  Fuer den DRUCK ist das ohne Bedeutung — der Slicer rechnet mit der',
        '  Dichte des gewaehlten Filamentprofils. Die Masse hier ist nur die',
        '  Plausibilitaetskontrolle und gilt fuer 100 % Fuellung; mit 4 Wand-',
        '  linien und 40 % Infill wiegt der Druck rund ein Drittel weniger.',
        '',
        'ANZIEHEN: die Z-Wagen-Schrauben klemmen {:.0f} mm PETG (Kopf sitzt in'.format(
            w('pad_hoehe')),
        '  der Freibohrung auf der Pad-Vorderseite). Handfest anziehen und',
        '  Schraubensicherung verwenden — eine lange Kunststoffsaeule setzt',
        '  sich mehr als eine kurze.',
        '',
        'DRUCK (PETG, Bambu Lab A1):',
        '  Traegerplatte ... Rueckseite (Passflaeche) aufs Bett. Platte, Sockel,',
        '                    Konsole, Saeulen- und Fuehrungsrippen stehen alle',
        '                    auf dem Bett — keine Stuetzen, alle Kraefte in',
        '                    der Schicht. 222 mm lang, passt liegend in den A1.',
        '  Schlittenplatte . Laser-Anschraubflaeche aufs Bett',
        '  Mutternwinkel ... Regaloberseite (Flanschsitz) aufs Bett. Der',
        '                    Ruecken haengt darunter, Spindel- und Einsatz-',
        '                    bohrungen werden rund, keine Stuetzen.',
        '  4 Wandlinien, >=40% Infill. PETG wegen der Abwaerme des Lasers.',
        '',
        'PARAMETRIK: MASSE landet als User-Parameter im Dialog. Die absoluten',
        '  Lagen rechnet lage() in Python — nach einer Parameteraenderung das',
        '  Skript neu laufen lassen und tools/toolhead_check.py ausfuehren.',
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
            if up.itemByName(name) is None:
                up.add(name, adsk.core.ValueInput.createByString(
                    '{} mm'.format(wert)), 'mm', kommentar)

        L = lage()
        zc = (L['zc_min'] + L['zc_max']) / 2.0      # Bauzustand: Mitte des Wegs

        # Baugruppe: alle Komponenten am globalen Maschinenursprung. Damit
        # stehen sie bereits richtig zueinander und As-Built-Joints genuegen.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Traegerplatte', 'Schlittenplatte',
                     'Mutternwinkel', 'Endschalterhalter', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o

        bau_traegerplatte(app, design, occ['Traegerplatte'].component, L, fehler)
        bau_schlittenplatte(app, design, occ['Schlittenplatte'].component,
                            L, zc, fehler)
        bau_mutternwinkel(app, design, occ['Mutternwinkel'].component,
                          L, zc, fehler)
        bau_endschalterhalter(app, design,
                              occ['Endschalterhalter'].component, L, fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, zc, fehler)

        occ['Traegerplatte'].isGrounded = True
        occ['Endschalterhalter'].isGrounded = True
        occ['Bohrlehren'].isGrounded = True

        # Starrer As-Built-Joint fuer die feste Verschraubung ...
        for a, b in (('Mutternwinkel', 'Schlittenplatte'),):
            try:
                ein = root.asBuiltJoints.createInput(occ[a], occ[b], None)
                ein.setAsRigidJointMotion()
                root.asBuiltJoints.add(ein)
            except:
                fehler.append('Joint {} <-> {} nicht gesetzt'.format(a, b))

        # ... und ein Schubgelenk fuer die Z-Achse, damit sich der Verfahrweg
        # im Modell pruefen laesst. Richtung Maschine Z = Modell-Y.
        try:
            koerper = occ['Schlittenplatte'].component.bRepBodies.item(0)
            flaeche = None
            for i in range(koerper.faces.count):
                f = koerper.faces.item(i)
                if (f.geometry.surfaceType
                        == adsk.core.SurfaceTypes.PlaneSurfaceType
                        and abs(f.centroid.z - L['schlitten_y0'] / 10.0) < 1e-4
                        and (flaeche is None or f.area > flaeche.area)):
                    flaeche = f
            geo = adsk.fusion.JointGeometry.createByPlanarFace(
                flaeche.createForAssemblyContext(occ['Schlittenplatte']), None,
                adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            ein = root.asBuiltJoints.createInput(
                occ['Schlittenplatte'], occ['Traegerplatte'], geo)
            ein.setAsSliderJointMotion(
                adsk.fusion.JointDirections.YAxisJointDirection)
            root.asBuiltJoints.add(ein)
        except:
            fehler.append('Schubgelenk der Z-Achse nicht gesetzt — '
                          'Teile stehen trotzdem richtig (starr pruefen)')

        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        app.activeViewport.fit()
        validierungs_bericht(app, design, ui,
                             hinweise=hinweise_bauen(L, zc, fehler))

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
