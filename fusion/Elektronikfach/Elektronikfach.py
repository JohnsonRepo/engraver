# Elektronikfach.py — Fach fuer Steuerung, Pi und Stromverteilung hinter
# dem hinteren 2060
#
# Ersetzt das Elektronik-Gehaeuse (Elektronik.py, Rev. 4) und den Pi-Halter
# (PiHalter.py, Rev. 3): Uno mit CNC Shield, Raspberry Pi Zero 2 W, beide
# Abwaertswandler, Wago-Klemmen, Buchse und Schalter liegen jetzt in einem
# Fach ueber die ganze Breite zwischen den 2040. Die Kabel laufen in zwei
# Gassen laengs des Fachs, getrennt nach Art:
#   Signalgasse vorn   an der Montageplatte: Lichtschranken, 5 V, Waechter
#   Leistungsgasse hinten an der Rueckwand: 24 V, 12 V zum Laser, Motoren
# Dazwischen stehen die Geraete; niedrige Leitwaende trennen die Gassen vom
# Uno, Oesen am Boden nehmen Kabelbinder auf. Jede Gasse hat in den
# Endwaenden ein eigenes Fenster mit Zugentlastung, in der Fuge zwischen
# den Haelften ein eigenes Fenster.
#
# Baugruppe aus vier Druckteilen (je hoechstens 250 mm, Bambu Lab A1):
#   Fach_links    Kasten links mit Ohr: Uno auf Stehbolzen, darueber der
#                 Luefter im Deckel; links die 5-V-Klemmen und die Fenster;
#                 der Pi steht senkrecht an der Fugenwand, davor der
#                 Wandler 24 -> 12 V fuer den Laser (kurzer Weg hinaus).
#   Fach_rechts   Kasten rechts mit Ohr: Wandler 24 -> 5 V (Pi,
#                 Lichtschranken), Wago 24 V und GND, hinten Einbaubuchse
#                 5,5 x 2,1 und runder Wippschalter; Platz fuer ein
#                 Air-Assist-Modul mit Durchbruch in der Rueckwand.
#   Deckel_links  mit dem 24-V-Luefter 40 mm ueber den Treibern
#   Deckel_rechts mit Lueftungsschlitzen ueber den Wandlern
# Die Haelften stossen in der Mitte mit je einer Fugenwand aneinander:
# 4 x M3 mit Mutter, 2 Rauten-Zapfen richten sie aus. Jede Haelfte haengt
# mit der Montageplatte an der Rueckseite des hinteren 2060: aussen ein Ohr
# mit 2 x M5 (untere und obere Nut), innen 1 x M5 (obere Nut).
#   Bohrlehren   ausgeblendet: Uno, Pi, Fuge
#   Referenz_nicht_drucken  hinteres 2060, Enden der 2040, Uno mit Stapel,
#                Pi mit Steckern, Wandler, Adapter, Wago, Luefter, Buchse,
#                Schalter, Air-Assist-Platz.
#
# Die Geometrie steht als Bauplan in lage(): Schritte aus Quadern,
# Zylindern, Vielecken und Traenen, die hier Fusion und in
# tools/stl_export.py manifold3d gleich ausfuehren — die beiden koennen
# nicht auseinanderlaufen. Pruefung: tools/elektronik_check.py.
#
# Koordinaten = Maschinenkoordinaten wie in Portal.py, Portal in der Mitte
# seines Wegs: X nach rechts, Y nach vorn, Z senkrecht, Z = 0 in der Mitte
# des Portalrohrs. Im Fusion-Modell sind Y und Z getauscht (Modell-Z =
# Maschine Y). Die Rahmenmasse stehen hier noch einmal (Fusion-Skripte sind
# eigenstaendig); tools/elektronik_check.py vergleicht sie mit Portal.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback
import math

SKRIPT_NAME = 'Elektronikfach'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen, Portal in der Mitte — muss zu Portal.py passen [v] --------
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_y0':         (-360.0, 'Rahmen: hintere Stirnseite der 2040'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'quer_y1':           (-250.0, 'Rahmen: Rueckseite des hinteren 2060'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
    'quer_laenge':        (600.0, '2060 quer: Laenge'),
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
    # Fach: Abstand zu Rahmen und Tisch (wie tools/portal_check.py)
    'fach_rand':            (3.0, 'Fach: Abstand zu 2060 und 2040'),
    'fach_tisch':           (2.0, 'Fach: Abstand zum Tisch'),

    # --- Kasten -----------------------------------------------------------------
    # Aussen bleibt das Fach 55 mm hoch (bis 3 mm unter die 2040); der
    # Kasten steht in der Mitte (|X| <= 225) und darf dort hoeher sein: bis
    # Z -19 ist frei (tools/elektronik_check.py). 77 mm Wand reichen fuer
    # den senkrechten Pi und viel Luft ueber den Treibern.
    'geh_x1':             (222.0, 'Kasten: halbe Breite aussen (Endwand)'),
    'geh_h':               (77.0, 'Kasten: Hoehe der Waende ab Unterkante'),
    'wand':                 (2.5, 'Kasten: Endwand und Rueckwand'),
    'boden':                (2.5, 'Kasten: Boden'),
    'fuge_wand':            (2.5, 'Fuge: Wand je Haelfte'),
    'platte_dicke':         (5.0, 'Montageplatte: Dicke (Vorderwand am 2060)'),
    'ohr_b':               (21.0, 'Ohr: so breit neben der Endwand'),
    'ohr_loch':            (10.5, 'Ohr: M5 so weit neben der Endwand'),
    'm5_innen_x':          (70.0, 'M5 innen (obere Nut): so weit von der Mitte'),
    'm5_l':                (12.0, 'Schraube M5x12 (Platte -> Hammermutter)'),

    # --- Gassen und Leitwaende -------------------------------------------------
    'gasse_vorn':          (20.0, 'Signalgasse: Breite ab der Montageplatte'),
    'gasse_hinten_r':      (16.5, 'Leistungsgasse rechts: Breite ab der Rueckwand'),
    'leitwand_d':           (2.0, 'Leitwand: Dicke'),
    'leitwand_h':          (18.0, 'Leitwand: Hoehe ueber dem Boden'),
    'oese_l':               (8.0, 'Oese: Laenge laengs der Gasse'),
    'oese_b':              (12.0, 'Oese: Breite quer zur Gasse'),
    'oese_h':               (5.0, 'Oese: Hoehe ueber dem Boden'),
    'oese_tunnel_b':        (4.0, 'Oese: Tunnel fuer den Kabelbinder, breit'),
    'oese_tunnel_h':        (2.5, 'Oese: Tunnel fuer den Kabelbinder, hoch'),
    'binder_b':             (5.0, 'Kabelbinder-Schlitz im Boden: Laenge'),
    'binder_t':             (2.2, 'Kabelbinder-Schlitz im Boden: Breite'),

    # --- Fenster (Endwaende und Fuge) -------------------------------------------
    'fenster_sig_h':       (20.5, 'Fenster Signalgasse: Hoehe ueber dem Boden'),
    'fenster_pow_h':       (24.5, 'Fenster Leistung: Hoehe bis zum 45-Grad-Dach'),
    'fenster_pow_l':       (22.0, 'Fenster Leistung links: Breite (darueber 5-V-Klemmen)'),
    'fenster_pow_r':       (30.0, 'Fenster Leistung rechts: Breite'),
    'fenster_rand':         (2.0, 'Fenster: so weit innerhalb der Gasse'),
    'fuge_fenster_h':      (24.5, 'Fenster in der Fuge: Hoehe ueber dem Boden'),
    'fuge_fenster_hinten': (14.0, 'Fenster in der Fuge, Leistung: Breite'),

    # --- Arduino Uno R3 mit CNC Shield V3 und 4 x TMC2209 ---------------------
    'uno_l':              (68.58, 'Uno: Platine, lange Seite (laengs X)'),
    'uno_b':              (53.34, 'Uno: Platine, kurze Seite (laengs Y)'),
    'uno_pcb':              (1.6, 'Uno: Platinendicke'),
    'uno_buchse_vor':       (6.3, 'Uno: USB-Buchse steht so weit ueber die Kante'),
    'uno_buchse_h':        (11.0, 'Uno: USB-Buchse, Hoehe ueber der Platine'),
    'uno_usb_y':           (38.1, 'Uno: USB-B Mitte ab der Kante unter der Hohlbuchse [w]'),
    'stapel_h':            (28.0, 'Uno + Shield + Treiber: Hoehe ab Unterseite Uno [v]'),
    'uno_steg_h':           (5.0, 'Uno: Stehbolzen, Hoehe ueber dem Boden'),
    'uno_steg_d':           (6.5, 'Uno: Stehbolzen, Durchmesser'),
    'uno_schraube_d':       (2.8, 'Uno: Kernloch fuer M3 selbstschneidend'),
    'uno_luft_vorn':        (2.0, 'Uno: Luft zur vorderen Leitwand'),
    'uno_luft_hinten':      (2.0, 'Uno: Luft zur hinteren Leitwand'),
    'links_zone':          (34.0, 'links: Platz neben dem Uno (Kabel, Klemmen an der Wand)'),
    # W17: kurzes OTG-Kabel Micro-B auf USB-B (15 bis 30 cm)
    'usb_b_stecker_l':     (32.0, 'USB-B-Stecker mit Knickschutz: Laenge [w]'),
    'usb_b_stecker_b':     (16.0, 'USB-B-Stecker: Breite [w]'),
    'usb_b_stecker_h':     (11.0, 'USB-B-Stecker: Hoehe [w]'),

    # --- Raspberry Pi Zero 2 W, senkrecht an der Fugenwand links [w] -----------
    'pi_l':                (65.0, 'Pi Zero 2 W: Platine, lange Seite (laengs Y)'),
    'pi_b':                (30.0, 'Pi Zero 2 W: Platine, kurze Seite (Z)'),
    'pi_pcb':               (1.4, 'Pi: Platinendicke [?]'),
    'pi_bauteile':          (4.0, 'Pi: hoechstes Bauteil ueber der Platine [?]'),
    'pi_loch_rand':         (3.5, 'Pi: Bohrungen so weit von den Kanten (58 x 23)'),
    'pi_loch_d':           (2.75, 'Pi: Bohrung fuer M2.5'),
    'pi_hdmi':             (12.4, 'Pi: Mini-HDMI, Mitte ab der Kante mit der SD-Karte'),
    'pi_usb':              (41.4, 'Pi: Micro-USB "USB", Mitte ab der SD-Kante'),
    'pi_pwr':              (54.0, 'Pi: Micro-USB "PWR IN", Mitte ab der SD-Kante'),
    'pi_hinten':           (14.5, 'Pi: SD-Kante so weit vor der Rueckwand (innen)'),
    'pi_oben':              (8.0, 'Pi: Oberkante so weit unter dem Rand'),
    'pi_steg_h':            (5.0, 'Pi: Stehbolzen an der Fugenwand, Laenge'),
    'pi_steg_d':            (6.0, 'Pi: Stehbolzen, Durchmesser (Traene)'),
    'm25_kern':             (2.2, 'Pi: Kernloch fuer M2.5 selbstschneidend'),
    'stecker_b':           (11.0, 'Micro-USB-Stecker: Breite'),
    'stecker_t':            (7.5, 'Micro-USB-Stecker: Dicke'),
    'stecker_l':           (24.0, 'Micro-USB-Stecker: Laenge ab der Platinenkante'),
    'stecker_mitte':        (1.4, 'Micro-USB: Steckermitte ueber der Platine'),

    # --- Abwaertswandler ------------------------------------------------------
    # 24 -> 5 V fuer Pi und Lichtschranken: 63 x 30 mm, bis 20 mm hoch,
    # Eingang Schraubklemmen, Ausgang USB-A [v]. Am Ausgang steckt ein
    # USB-A-Adapter mit Schraubklemmen [?]; von ihm gehen die 5 V an die
    # Wago +5 V (W6).
    'w5_l':                (63.0, '5-V-Wandler: Laenge (X) [v]'),
    'w5_b':                (30.0, '5-V-Wandler: Breite (Y) [v]'),
    'w5_h':                (20.0, '5-V-Wandler: hoechstens so hoch [v]'),
    'w5_x0':               (60.0, '5-V-Wandler: Kante mit der USB-A-Buchse (X)'),
    'w5_vorn':              (4.5, '5-V-Wandler: so weit hinter der vorderen Leitwand'),
    'adapter_l':           (40.0, 'USB-A-Adapter mit Klemmen: Laenge ab Buchse [?]'),
    'adapter_b':           (20.0, 'USB-A-Adapter: Breite [?]'),
    'adapter_h':           (15.0, 'USB-A-Adapter: Hoehe [?]'),
    # 24 -> 12 V / 5 A fuer den Laser [v]: links, nah am Fenster, damit das
    # Laserkabel kurz bleibt; der Eingang kommt durch die Fuge
    'w12_l':               (43.0, '12-V-Wandler: Laenge (X) [v]'),
    'w12_b':               (24.0, '12-V-Wandler: Breite (Y) [v]'),
    'w12_h':               (20.0, '12-V-Wandler: Hoehe [v]'),
    'w12_x0':            (-108.0, '12-V-Wandler: Kante mit dem Ausgang (X)'),
    'wandler_binder':      (15.0, 'Wandler: Kabelbinder so weit neben der Mitte'),

    # --- Wago, Buchse, Schalter -------------------------------------------------
    'wago_luecke':          (3.0, 'Wago: Abstand nebeneinander'),
    'wago5_luft':           (2.0, 'Wago 5 V: so weit ueber dem Fenster Leistung'),
    'wago5_vorn':           (9.0, 'Wago 5 V: so weit hinter der Montageplatte'),
    'wago24_x0':          (133.0, 'Wago 24 V: linke Kante (X)'),
    'buchse_d':             (8.2, 'Einbaubuchse 5,5 x 2,1, Gewinde M8'),
    'buchse_x':           (145.0, 'Einbaubuchse: Mitte (X)'),
    'schalter_d':          (20.2, 'Wippschalter rund: Einbauloch [?]'),
    'schalter_blende_d':   (22.5, 'Wippschalter rund: Blende aussen [v]'),
    'schalter_kappe':       (0.6, 'Schalterloch: oben flach, so weit ueber dem Kreis'),
    'schalter_wand':        (1.6, 'Wippschalter: Wand am Loch (Rastnasen)'),
    'schalter_rand':        (3.0, 'Wippschalter: verduennter Rand um das Loch'),
    'schalter_x':         (180.0, 'Wippschalter: Mitte (X)'),
    'eingang_z':           (39.5, 'Buchse und Schalter: Mitte ueber dem Boden'),

    # --- Reserve: Air Assist ------------------------------------------------------
    'aa_x0':               (10.0, 'Air Assist: Platz fuer das Modul, linke Kante'),
    'aa_l':                (50.0, 'Air Assist: Platz laengs X'),
    'aa_b':                (25.0, 'Air Assist: Platz laengs Y'),
    'ausbruch_d':          (12.0, 'Air Assist: Durchbruch in der Rueckwand'),
    'ausbruch_haut':        (0.6, 'Durchbruch: Haut innen, zum Ausbrechen'),
    'ausbruch_z':          (14.5, 'Durchbruch: Mitte ueber dem Boden'),

    # --- Fuge zwischen den Haelften --------------------------------------------
    'm3_durchgang':         (3.4, 'M3 Durchgang'),
    'zapfen_r':             (2.5, 'Rauten-Zapfen: halbe Diagonale'),
    'zapfen_l':             (2.4, 'Rauten-Zapfen: Laenge (in der Wand rechts)'),
    'zapfen_spiel':        (0.25, 'Rauten-Zapfen: Spiel im Loch'),

    # --- Deckel, Dome, Luefter ---------------------------------------------------
    'deckel_dicke':         (2.5, 'Deckel: Dicke'),
    'lippe_b':              (1.2, 'Deckel: Lippe, Breite'),
    'lippe_h':              (3.0, 'Deckel: Lippe, Hoehe'),
    'lippe_spiel':          (0.3, 'Deckel: Lippe, Spiel zur Wand'),
    'dom_a':               (10.0, 'Deckeldom: Kante (quadratisch, an der Wand)'),
    'dom_h':               (12.0, 'Deckeldom: Hoehe unter dem Rand (darunter 45 Grad)'),
    'dom_innen':           (40.0, 'Deckeldome: so weit von der Fuge'),
    'dom_aussen':          (17.0, 'Deckeldome: Mitte so weit vor der Endwand (innen)'),
    'insert_m3_d':          (4.6, 'Gewindeeinsatz M3: Einpressbohrung'),
    'insert_m3_t':          (7.0, 'Gewindeeinsatz M3: Sacklochtiefe'),
    'luefter':             (40.0, 'Luefter 40 x 40 x 10, 24 V'),
    'luefter_h':           (10.0, 'Luefter: Hoehe'),
    'luefter_loch':        (32.0, 'Luefter: Lochabstand'),
    'luefter_d':           (38.0, 'Luefter: Oeffnung im Deckel'),
    'gitter_b':             (2.0, 'Deckel: Steg in der Luefteroeffnung'),
    'lueftung_b':           (3.0, 'Lueftungsschlitz: Breite'),
    'lueftung_h':          (12.0, 'Lueftungsschlitz Rueckwand: Hoehe'),
    'lueftung_oben':        (6.0, 'Lueftungsschlitz Rueckwand: so weit unter dem Rand'),
    'lueftung_teilung':    (14.0, 'Lueftungsschlitze: Abstand'),

    # --- Normteile und Regeln ----------------------------------------------------
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'inbus_frei_d':         (6.0, 'Werkzeugkorridor fuer den Inbus'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
    'lehre_dicke':          (2.0, 'Bohrlehre: Plattendicke'),
}

# Lochbild des Uno R3 in Platinenkoordinaten (mm): x laengs ab der Kante mit
# USB- und Hohlbuchse, y quer ab der Kante unter der Hohlbuchse [w]
# (Arduino-Massblatt, in mil: 550/100, 600/2000, 2600/300, 2600/1400).
UNO_LOECHER = ((13.97, 2.54), (15.24, 50.80), (66.04, 7.62), (66.04, 35.56))

# Wago-Klemmen [w] nach Datenblatt, je die groessere Angabe der Haendler:
# (Name, Typ, breit (Hebelreihe), tief (Draht), hoch). 24 V und GND liegen
# rechts bei Buchse und Wandlern auf dem Boden, die Draehte von vorn, die
# Hebel oben. Die beiden 5-V-Klemmen kleben senkrecht an der linken
# Endwand ueber dem Fenster Leistung: die Draehte kommen von unten (aus
# dem Fenster der Lichtschranken und der Signalgasse), die Hebel zeigen in
# den Kasten. So bleibt links nur ein schmaler Streifen, und die Kabel
# nach links sind kurz.
# Bestand [v]: 2 x 221-420, 1 x 221-415, 1 x 221-413; die zweite 221-415
# (GND 5 V) ist neu.
WAGO = (('+5 V', '221-415', 30.2, 18.8, 8.6),
        ('GND 5 V', '221-415', 30.2, 18.8, 8.6),
        ('+24 V', '221-420', 29.8, 18.3, 15.8),
        ('GND', '221-420', 29.8, 18.3, 15.8))

# Schrauben M3 und Zapfen der Fuge in (Y, Z): ausserhalb der Fenster, des Pi
# (links an der Fugenwand) und der Wandler (rechts).
FUGE_BOLZEN = ((-349.0, -60.0), (-349.0, -90.0), (-265.0, -62.0),
               (-316.0, -118.0))
FUGE_ZAPFEN = ((-300.0, -120.0), (-330.0, -62.0))

SEITEN = ('links', 'rechts')
BRUECKE = 25.0          # breiter wird eine Oeffnung oben nicht gedruckt


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


# --- Bauplan: Schritte, die Fusion und manifold3d gleich ausfuehren -----------
# Jeder Schritt ist ein Prisma: Formen in der Ebene quer zu `achse`, entlang
# `achse` von a[0] bis a[1]. In der Ebene gilt (u, v) = (X, Y) fuer 'z',
# (X, Z) fuer 'y' und (Y, Z) fuer 'x'. art 'dazu' vereint, 'weg' schneidet;
# der erste Schritt eines Teils legt den Koerper an.
def schritt(art, name, achse, form, formen, a, **mehr):
    s = dict(art=art, name=name, achse=achse, form=form,
             formen=list(formen), a=(min(a), max(a)))
    s.update(mehr)
    return s


def quader_schritt(art, name, x, y, z):
    """Achsparalleler Quader: Rechteck in (X, Y), entlang Z."""
    return schritt(art, name, 'z', 'rechteck', [(x[0], y[0], x[1], y[1])], z)


def tropfen_geometrie(u, v, d, spitze=1.0, kappe=None):
    """Traene in (u, v): unten (spitze +1) ein Kreisbogen, oben zwei
    45-Grad-Flanken bis zur Spitze — oder bis `kappe` ueber dem Kreis
    flach. spitze -1 dreht sie um (Spitze unten, fuer Zapfen, die aus einer
    senkrechten Wand ragen). Liefert ((Bogen: Start, Mitte, Ende),
    [Ecken vom Bogenende zum Bogenstart])."""
    r = d / 2.0
    s = r / math.sqrt(2.0)
    bogen = ((u + s, v + spitze * s), (u, v - spitze * r),
             (u - s, v + spitze * s))
    if kappe is None:
        ecken = [(u, v + spitze * r * math.sqrt(2.0))]
    else:
        h = r + kappe
        b = r * math.sqrt(2.0) - h
        ecken = [(u - b, v + spitze * h), (u + b, v + spitze * h)]
    return bogen, ecken


def tropfen_punkte(u, v, d, spitze=1.0, kappe=None, sehne=0.4):
    """Umriss der Traene als Vieleck (fuer STL und Zeichnungen)."""
    r = d / 2.0
    n = max(24, int(math.ceil(1.5 * math.pi * r / sehne)))
    bogen = [(u + r * math.cos(t), v + spitze * r * math.sin(t))
             for t in (math.radians(45.0 - 270.0 * i / n)
                       for i in range(n + 1))]
    return bogen + tropfen_geometrie(u, v, d, spitze, kappe)[1]


def raute(u, v, r):
    """Quadrat auf der Spitze: alle Flanken 45 Grad, druckt in beide
    Richtungen ohne Stuetzen."""
    return [(u, v + r), (u - r, v), (u, v - r), (u + r, v)]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm) und der Bauplan
    der vier Druckteile. Einzige Quelle fuer Geometrie, STL und Pruefung
    (tools/elektronik_check.py, tools/stl_export.py)."""
    L = {}
    L['R'] = w('y_schienen_abstand') / 2.0
    L['tisch_z'] = w('rahmen_z0') - w('quer_h')
    L['quer_y'] = (w('quer_y1'), w('quer_y1') + w('rahmen_b'))
    L['quer_nut_z'] = [L['tisch_z'] + w('quer_nut_1') + i * w('quer_nut_teilung')
                       for i in range(3)]
    # Fach wie tools/portal_check.py (elektronikfach)
    xi = L['R'] - w('rahmen_b') / 2.0 - w('fach_rand')
    L['fach_x'] = (-xi, xi)
    L['fach_y'] = (w('rahmen_y0') + w('fach_rand'),
                   w('quer_y1') - w('fach_rand'))
    L['fach_z'] = (L['tisch_z'] + w('fach_tisch'),
                   w('rahmen_z0') - w('fach_rand'))

    wa, fw = w('wand'), w('fuge_wand')
    z0 = L['fach_z'][0]
    L['z0'] = z0
    L['boden_z'] = z0 + w('boden')
    L['rand_z'] = z0 + w('geh_h')
    bz, rz = L['boden_z'], L['rand_z']
    L['platte_y'] = (w('quer_y1') - w('platte_dicke'), w('quer_y1'))
    gx = w('geh_x1')
    L['geh_x'] = (-gx, gx)
    L['geh_y'] = (L['fach_y'][0], L['platte_y'][1])
    L['geh_z'] = (z0, rz)
    L['innen_y'] = (L['geh_y'][0] + wa, L['platte_y'][0])
    L['haelfte_x'] = {'links': (-gx, 0.0), 'rechts': (0.0, gx)}
    L['innen_x'] = {'links': (-gx + wa, -fw), 'rechts': (fw, gx - wa)}
    L['fuge_x'] = {'links': (-fw, 0.0), 'rechts': (0.0, fw)}
    L['endwand_x'] = {'links': (-gx, -gx + wa), 'rechts': (gx - wa, gx)}
    L['ohr_x'] = {'links': (-gx - w('ohr_b'), -gx),
                  'rechts': (gx, gx + w('ohr_b'))}
    L['ohr_z'] = (z0, L['fach_z'][1])
    iy = L['innen_y']

    # Gassen: vorn Signale an der Platte, hinten Leistung an der Rueckwand;
    # dazwischen der Uno mit Luft zu den Leitwaenden
    lw = w('leitwand_d')
    L['gasse_vorn'] = (iy[1] - w('gasse_vorn'), iy[1])
    L['leitwand_vorn_y'] = (L['gasse_vorn'][0] - lw, L['gasse_vorn'][0])
    uy1 = L['leitwand_vorn_y'][0] - w('uno_luft_vorn')
    uy0 = uy1 - w('uno_b')
    L['leitwand_hinten_y'] = (uy0 - w('uno_luft_hinten') - lw,
                              uy0 - w('uno_luft_hinten'))
    L['gasse_hinten'] = {'links': (iy[0], L['leitwand_hinten_y'][0]),
                         'rechts': (iy[0], iy[0] + w('gasse_hinten_r'))}
    L['leitwand_z'] = (bz, bz + w('leitwand_h'))

    # Uno: Platine laengs X, die Kante mit USB und Hohlbuchse rechts (+X,
    # zum Pi), die Stiftleisten der Endschalter links (zu den Fenstern).
    # Platinen-x -> -X, Platinen-y -> +Y: von oben gesehen um 180 Grad
    # gedreht, die Bauteilseite bleibt oben.
    ux_fern = L['innen_x']['links'][0] + w('links_zone')
    ux0 = ux_fern + w('uno_l')                       # Kante mit USB
    L['uno_x'] = (ux_fern, ux0)
    L['uno_y'] = (uy0, uy1)
    L['uno_loecher'] = [(ux0 - xb, uy0 + yb) for xb, yb in UNO_LOECHER]
    L['uno_z0'] = bz + w('uno_steg_h')
    L['uno_z1'] = L['uno_z0'] + w('uno_pcb')
    L['stapel_z1'] = L['uno_z0'] + w('stapel_h')
    yu = uy0 + w('uno_usb_y')
    zu = L['uno_z1'] + w('uno_buchse_h') / 2.0
    xm = ux0 + w('uno_buchse_vor')                   # Mund der USB-B-Buchse
    L['usb_b'] = (xm, yu, zu)
    hb, hh = w('usb_b_stecker_b') / 2.0, w('usb_b_stecker_h') / 2.0
    L['usb_b_stecker'] = ((xm, xm + w('usb_b_stecker_l')), (yu - hb, yu + hb),
                          (zu - hh, zu + hh))
    L['luefter_mitte'] = ((L['uno_x'][0] + L['uno_x'][1]) / 2.0,
                          (uy0 + uy1) / 2.0)
    fm, h = L['luefter_mitte'], w('luefter_loch') / 2.0
    L['luefter_loecher'] = [(fm[0] + a * h, fm[1] + b * h)
                            for a in (-1, 1) for b in (-1, 1)]

    # Pi senkrecht an der Fugenwand links: Bauteile nach links (-X), die
    # Buchsen unten, die SD-Karte hinten. Die Oberkante liegt ueber dem
    # 2060 (WLAN), USB und PWR unten zeigen zu Uno und Signalgasse.
    xf = L['innen_x']['links'][1]
    L['pi_steg_x'] = (xf - w('pi_steg_h'), xf)
    L['pi_pcb_x'] = (L['pi_steg_x'][0] - w('pi_pcb'), L['pi_steg_x'][0])
    L['pi_bauteile_x'] = (L['pi_pcb_x'][0] - w('pi_bauteile'),
                          L['pi_pcb_x'][0])
    py0 = iy[0] + w('pi_hinten')                       # Kante mit der SD-Karte
    L['pi_y'] = (py0, py0 + w('pi_l'))
    pz1 = rz - w('pi_oben')
    L['pi_z'] = (pz1 - w('pi_b'), pz1)
    r = w('pi_loch_rand')
    L['pi_loecher'] = [(y, z) for y in (py0 + r, py0 + w('pi_l') - r)
                       for z in (L['pi_z'][0] + r, pz1 - r)]
    L['pi_buchse_y'] = {'HDMI': py0 + w('pi_hdmi'), 'USB': py0 + w('pi_usb'),
                        'PWR': py0 + w('pi_pwr')}
    xs = L['pi_pcb_x'][0] - w('stecker_mitte')
    ht, hb = w('stecker_t') / 2.0, w('stecker_b') / 2.0
    L['pi_stecker'] = {n: ((xs - ht, xs + ht), (L['pi_buchse_y'][n] - hb,
                                                L['pi_buchse_y'][n] + hb),
                           (L['pi_z'][0] - w('stecker_l'), L['pi_z'][0]))
                       for n in ('USB', 'PWR')}

    # 5-V-Klemmen links neben dem Uno, die Draehte von vorn aus der
    # Signalgasse; 24-V-Klemmen rechts vor der Rueckwand bei Buchse und
    # Schalter
    L['wago'] = []
    xw = L['innen_x']['links'][0]
    y = iy[1] - w('wago5_vorn')
    z = bz + w('fenster_pow_h') + w('wago5_luft')
    for name, typ, b, t, hh in WAGO[:2]:
        L['wago'].append((name, typ, (xw, xw + hh), (y - b, y), (z, z + t)))
        y -= b + w('wago_luecke')
    x = w('wago24_x0')
    y0 = L['gasse_hinten']['rechts'][1]
    for name, typ, b, t, hh in WAGO[2:]:
        L['wago'].append((name, typ, (x, x + b), (y0, y0 + t), (bz, bz + hh)))
        x += b + 2.0 * w('wago_luecke')

    # Wandler: 12 V links hinten an der Leistungsgasse (Ausgang zum Fenster
    # links), 5 V rechts vorn an der Signalgasse, der USB-A-Adapter zur Fuge
    L['w12_x'] = (w('w12_x0'), w('w12_x0') + w('w12_l'))
    L['w12_y'] = (y0, y0 + w('w12_b'))
    L['w12_z'] = (bz, bz + w('w12_h'))
    y5 = L['leitwand_vorn_y'][0] - w('w5_vorn')
    L['w5_x'] = (w('w5_x0'), w('w5_x0') + w('w5_l'))
    L['w5_y'] = (y5 - w('w5_b'), y5)
    L['w5_z'] = (bz, bz + w('w5_h'))
    ym = (L['w5_y'][0] + L['w5_y'][1]) / 2.0
    L['adapter'] = ((w('w5_x0') - w('adapter_l'), w('w5_x0')),
                    (ym - w('adapter_b') / 2.0, ym + w('adapter_b') / 2.0),
                    (bz + 3.0, bz + 3.0 + w('adapter_h')))
    # Kabelbinder laengs Y, je ein Schlitzpaar vor und hinter dem Wandler
    rand = w('binder_t') / 2.0 + 1.0
    L['binder'] = []
    for wx, wy in ((L['w12_x'], L['w12_y']), (L['w5_x'], L['w5_y'])):
        xm = (wx[0] + wx[1]) / 2.0
        L['binder'] += [(x, y, 'y') for x in (xm - w('wandler_binder'),
                                              xm + w('wandler_binder'))
                        for y in (wy[0] - rand, wy[1] + rand)]

    # Buchse und Schalter hinten rechts, hoch ueber der Leistungsgasse
    L['eingang_z'] = bz + w('eingang_z')
    L['buchse'] = (w('buchse_x'), L['eingang_z'])
    L['schalter'] = (w('schalter_x'), L['eingang_z'])

    # Reserve Air Assist rechts hinten an der Fuge: Modul bis 50 x 28 mit
    # zwei Kabelbindern laengs Y; Durchbruch in der Rueckwand dahinter
    L['aa_x'] = (w('aa_x0'), w('aa_x0') + w('aa_l'))
    L['aa_y'] = (y0, y0 + w('aa_b'))
    xm = (L['aa_x'][0] + L['aa_x'][1]) / 2.0
    L['binder'] += [(x, y, 'y') for x in (xm - w('wandler_binder'),
                                          xm + w('wandler_binder'))
                    for y in (L['aa_y'][0] - rand, L['aa_y'][1] + rand)]
    L['ausbruch'] = (xm, bz + w('ausbruch_z'))

    # Fenster: in jeder Endwand eines fuer die Signalgasse und eines fuer
    # Motoren und Leistung (hinten, mit 45-Grad-Dach); in der Fuge eines je
    # Gasse
    gv, fr = L['gasse_vorn'], w('fenster_rand')
    L['fenster_sig_y'] = (gv[0] + fr, gv[1] - fr)
    L['fenster_sig_z'] = (bz, bz + w('fenster_sig_h'))
    L['fenster_pow'] = {}
    for s, b in (('links', w('fenster_pow_l')), ('rechts', w('fenster_pow_r'))):
        ya = iy[0] + 2.5
        L['fenster_pow'][s] = ((ya, ya + b), (bz, bz + w('fenster_pow_h')))
    L['fuge_fenster'] = [((gv[0] + fr, gv[1] - fr),
                          (bz, bz + w('fuge_fenster_h'))),
                         ((iy[0] + 2.5, iy[0] + 2.5 + w('fuge_fenster_hinten')),
                          (bz, bz + w('fuge_fenster_h')))]
    L['kabel_links_y'] = sum(L['fenster_pow']['links'][0]) / 2.0

    # Leitwaende (vorn: Signalgasse; hinten links: Leistungsgasse hinter
    # dem Uno). Luecken dort, wo Kabel die Gasse verlassen.
    L['leitwaende'] = {
        'links': [((ux_fern, -25.0), L['leitwand_vorn_y']),
                  ((-205.0, ux0 - 3.0), L['leitwand_hinten_y'])],
        'rechts': [((18.0, 125.0), L['leitwand_vorn_y']),
                   ((135.0, 215.0), L['leitwand_vorn_y'])]}

    # Oesen fuer Kabelbinder: Tunnel quer zur Gasse; die ersten gleich hinter
    # den Fenstern sind die Zugentlastung
    yv = (gv[0] + gv[1]) / 2.0
    yh = {s: sum(L['gasse_hinten'][s]) / 2.0 for s in SEITEN}
    xo = L['innen_x']['links'][0] + 7.5
    L['oesen'] = {
        'links': [(xo, yv), (-120.0, yv), (-60.0, yv),
                  (xo, L['kabel_links_y']), (-170.0, yh['links']),
                  (-130.0, yh['links']), (-50.0, yh['links'])],
        'rechts': [(-xo, yv), (50.0, yv), (110.0, yv), (170.0, yv),
                   (-xo, sum(L['fenster_pow']['rechts'][0]) / 2.0),
                   (30.0, yh['rechts']), (90.0, yh['rechts']),
                   (150.0, yh['rechts'])]}

    # Deckeldome an Rueckwand und Montageplatte, oben 45 Grad abgestuetzt
    da = w('dom_a')
    xd = (w('dom_innen'), gx - wa - w('dom_aussen'))
    L['dom_y'] = {'hinten': (iy[0], iy[0] + da), 'vorn': (iy[1] - da, iy[1])}
    L['dom_z'] = (rz - w('dom_h'), rz)
    L['dome'] = {s: [(sx * x, sum(L['dom_y'][e]) / 2.0, e) for x in xd
                     for e in ('hinten', 'vorn')]
                 for s, sx in (('links', -1.0), ('rechts', 1.0))}

    # Montage: M5 im Ohr (untere und obere Nut), innen eine in der oberen
    L['m5'] = {}
    for s, sx in (('links', -1.0), ('rechts', 1.0)):
        xo = sx * (gx + w('ohr_loch'))
        L['m5'][s] = [(xo, L['quer_nut_z'][0]), (xo, L['quer_nut_z'][2]),
                      (sx * w('m5_innen_x'), L['quer_nut_z'][2])]

    # Lueftung: Schlitze oben in der Rueckwand, frei von Domen und Schalter;
    # rechts dazu Schlitze im Deckel ueber den Wandlern
    lt, lb = w('lueftung_teilung'), w('lueftung_b')
    frei = da / 2.0 + lb / 2.0 + 2.0
    L['lueftung_z'] = (rz - w('lueftung_oben') - w('lueftung_h'),
                       rz - w('lueftung_oben'))
    L['lueftung_x'] = {}
    for s, sx in (('links', -1.0), ('rechts', 1.0)):
        a, e = L['innen_x'][s]
        xs = [a + 12.0 + i * lt for i in range(int((e - a - 24.0) // lt) + 1)]
        L['lueftung_x'][s] = [x for x in xs
                              if all(abs(x - d[0]) >= frei
                                     for d in L['dome'][s])]
    ys = (L['aa_y'][0] - 4.0, L['w5_y'][1] - 4.0)
    L['deckel_schlitze'] = [((x - lb / 2.0, x + lb / 2.0), ys)
                            for x in [L['aa_x'][0] + 15.0 + 12.0 * i
                                      for i in range(9)]]

    # Zuordnung der Fugenteile; Bohrlehre in derselben Lage
    L['fuge_bolzen'] = list(FUGE_BOLZEN)
    L['fuge_zapfen'] = list(FUGE_ZAPFEN)

    L['plan'] = {'Fach_links': plan_fach(L, 'links'),
                 'Fach_rechts': plan_fach(L, 'rechts'),
                 'Deckel_links': plan_deckel(L, 'links'),
                 'Deckel_rechts': plan_deckel(L, 'rechts')}
    # Bauraum je Teil (Maschine) und Drucklage: (X, Y, Z) -> Druck
    dz = L['rand_z'] + w('deckel_dicke')
    L['deckel_z'] = (rz, dz)
    L['lippe_z'] = (rz - w('lippe_h'), rz)
    L['luefter_z'] = (dz, dz + w('luefter_h'))
    L['teile'] = {}
    for s in SEITEN:
        hx = L['haelfte_x'][s]
        x0 = min(hx[0], L['ohr_x'][s][0])
        x1 = max(hx[1], L['ohr_x'][s][1])
        if s == 'links':
            x1 += w('zapfen_l')                  # Zapfen ragen in die Fuge
        L['teile']['Fach_' + s] = dict(
            bbox=((x0, x1), L['geh_y'], L['geh_z']),
            auflage=('z', z0),
            druck=[[1, 0, 0, -x0], [0, 1, 0, -L['geh_y'][0]],
                   [0, 0, 1, -z0]])
        L['teile']['Deckel_' + s] = dict(
            bbox=(hx, L['geh_y'], (L['lippe_z'][0], dz)),
            auflage=('z', dz),
            druck=[[1, 0, 0, -hx[0]], [0, -1, 0, L['geh_y'][1]],
                   [0, 0, -1, dz]])
    return L


def plan_fach(L, s):
    """Bauplan einer Haelfte des Fachs (s: 'links' | 'rechts')."""
    sx = -1.0 if s == 'links' else 1.0
    wa = w('wand')
    z0, bz, rz = L['z0'], L['boden_z'], L['rand_z']
    gy, iy = L['geh_y'], L['innen_y']
    hx, ix = L['haelfte_x'][s], L['innen_x'][s]
    P = [quader_schritt('dazu', 'Kasten', hx, gy, L['geh_z']),
         quader_schritt('weg', 'Innenraum', ix, iy, (bz, rz + 1.0)),
         quader_schritt('dazu', 'Ohr', L['ohr_x'][s], L['platte_y'],
                        L['ohr_z'])]
    # Leitwaende und Oesen
    P.append(schritt('dazu', 'Leitwaende', 'z', 'rechteck',
                     [(x[0], y[0], x[1], y[1])
                      for x, y in L['leitwaende'][s]],
                     (bz - 0.5, L['leitwand_z'][1])))
    ol, ob = w('oese_l') / 2.0, w('oese_b') / 2.0
    P.append(schritt('dazu', 'Oesen', 'z', 'rechteck',
                     [(x - ol, y - ob, x + ol, y + ob)
                      for x, y in L['oesen'][s]],
                     (bz - 0.5, bz + w('oese_h'))))
    # Deckeldome: Quader an der Wand, darunter eine 45-Grad-Stuetze
    da = w('dom_a')
    dz = L['dom_z']
    P.append(schritt('dazu', 'Dome', 'z', 'rechteck',
                     [(x - da / 2.0, L['dom_y'][e][0], x + da / 2.0,
                       L['dom_y'][e][1]) for x, _, e in L['dome'][s]], dz))
    for x in sorted(set(d[0] for d in L['dome'][s])):
        P.append(schritt('dazu', 'Domstuetzen', 'x', 'vieleck',
                         [[(iy[0], dz[0]), (iy[0] + da, dz[0]),
                           (iy[0], dz[0] - da)],
                          [(iy[1], dz[0]), (iy[1] - da, dz[0]),
                           (iy[1], dz[0] - da)]],
                         (x - da / 2.0, x + da / 2.0)))
    if s == 'links':
        P.append(schritt('dazu', 'Uno_Stehbolzen', 'z', 'kreis',
                         L['uno_loecher'], (bz - 0.5, L['uno_z0']),
                         d=w('uno_steg_d')))
        P.append(schritt('dazu', 'Pi_Stehbolzen', 'x', 'tropfen',
                         L['pi_loecher'],
                         (L['pi_steg_x'][0], L['pi_steg_x'][1] + 0.5),
                         d=w('pi_steg_d'), spitze=-1.0))
        P.append(schritt('dazu', 'Zapfen', 'x', 'vieleck',
                         [raute(y, z, w('zapfen_r'))
                          for y, z in L['fuge_zapfen']],
                         (-0.5, w('zapfen_l'))))
    # --- Schnitte ---
    tb, th = w('oese_tunnel_b') / 2.0, w('oese_tunnel_h')
    P.append(schritt('weg', 'Oesen_Tunnel', 'z', 'rechteck',
                     [(x - tb, y - ob - 1.0, x + tb, y + ob + 1.0)
                      for x, y in L['oesen'][s]], (bz, bz + th)))
    P.append(schritt('weg', 'Dom_Einsatz', 'z', 'kreis',
                     [(x, y) for x, y, _ in L['dome'][s]],
                     (rz - w('insert_m3_t'), rz + 1.0),
                     d=w('insert_m3_d')))
    if s == 'links':
        P.append(schritt('weg', 'Uno_Kernloch', 'z', 'kreis',
                         L['uno_loecher'], (z0 + 1.0, L['uno_z0'] + 1.0),
                         d=w('uno_schraube_d')))
        P.append(schritt('weg', 'Pi_Kernloch', 'x', 'kreis',
                         L['pi_loecher'],
                         (L['pi_steg_x'][0] - 1.0, L['pi_steg_x'][1] + 0.5),
                         d=w('m25_kern')))
    # Fenster in der Endwand: Signale vorn, Leistung hinten mit Dach
    ex = L['endwand_x'][s]
    ea = (ex[0] - 1.0, ex[1] + 1.0)
    (sy0, sy1), (sz0, sz1) = L['fenster_sig_y'], L['fenster_sig_z']
    P.append(schritt('weg', 'Fenster_Signal', 'x', 'rechteck',
                     [(sy0, sz0, sy1, sz1)], ea))
    (py0, py1), (pz0, pz1) = L['fenster_pow'][s]
    ym = (py0 + py1) / 2.0
    dach = [(ym, pz1 + (py1 - py0) / 2.0)] if py1 - py0 > BRUECKE else []
    P.append(schritt('weg', 'Fenster_Leistung', 'x', 'vieleck',
                     [[(py0, pz0), (py1, pz0), (py1, pz1)] + dach
                      + [(py0, pz1)]], ea))
    # Fuge: Fenster je Gasse, Schrauben, Loecher fuer die Zapfen
    fx = L['fuge_x'][s]
    fa = (fx[0] - 1.0, fx[1] + 1.0)
    P.append(schritt('weg', 'Fuge_Fenster', 'x', 'rechteck',
                     [(y[0], z[0], y[1], z[1]) for y, z in L['fuge_fenster']],
                     fa))
    P.append(schritt('weg', 'Fuge_Schrauben', 'x', 'kreis', L['fuge_bolzen'],
                     fa, d=w('m3_durchgang')))
    if s == 'rechts':
        P.append(schritt('weg', 'Zapfen_Loecher', 'x', 'vieleck',
                         [raute(y, z, w('zapfen_r') + w('zapfen_spiel')
                                * math.sqrt(2.0))
                          for y, z in L['fuge_zapfen']], fa))
    # Montage: M5 durch Ohr und Platte (Traene, Spitze oben)
    P.append(schritt('weg', 'M5', 'y', 'tropfen', L['m5'][s],
                     (L['platte_y'][0] - 1.0, L['platte_y'][1] + 1.0),
                     d=w('m5_durchgang'), spitze=1.0))
    # Kabelbinder-Schlitze im Boden (Binder laengs Y bzw. X)
    rt, rb = w('binder_t') / 2.0, w('binder_b') / 2.0
    schlitze = [((x - rb, y - rt, x + rb, y + rt) if r == 'y'
                 else (x - rt, y - rb, x + rt, y + rb))
                for x, y, r in L['binder'] if sx * x > 0]
    if schlitze:
        P.append(schritt('weg', 'Binder_Schlitze', 'z', 'rechteck', schlitze,
                         (z0 - 1.0, bz + 1.0)))
    # Rueckwand: Lueftung oben; rechts Buchse und Schalter, links der
    # Durchbruch fuer Air Assist
    ra = (gy[0] - 1.0, iy[0] + 1.0)
    lz, lb = L['lueftung_z'], w('lueftung_b') / 2.0
    P.append(schritt('weg', 'Lueftung', 'y', 'rechteck',
                     [(x - lb, lz[0], x + lb, lz[1])
                      for x in L['lueftung_x'][s]], ra))
    if s == 'rechts':
        P.append(schritt('weg', 'Buchse', 'y', 'tropfen', [L['buchse']], ra,
                         d=w('buchse_d'), spitze=1.0))
        P.append(schritt('weg', 'Schalter', 'y', 'tropfen', [L['schalter']],
                         ra, d=w('schalter_d'), spitze=1.0,
                         kappe=w('schalter_kappe')))
        P.append(schritt('weg', 'Schalter_Rand', 'y', 'kreis',
                         [L['schalter']], (gy[0] + w('schalter_wand'),
                                           iy[0] + 1.0),
                         d=w('schalter_d') + 2.0 * w('schalter_rand')))
        P.append(schritt('weg', 'Durchbruch_AirAssist', 'y', 'tropfen',
                         [L['ausbruch']],
                         (gy[0] - 1.0, iy[0] - w('ausbruch_haut')),
                         d=w('ausbruch_d'), spitze=1.0))
    return P


def plan_deckel(L, s):
    """Bauplan eines Deckels: Platte auf dem Rand, Lippe innen an den
    Waenden (ausgespart an den Domen), 4 x M3 in die Einsaetze. Links der
    Luefter mit Gitter, rechts Lueftungsschlitze."""
    rz = L['rand_z']
    dz = (rz, rz + w('deckel_dicke'))
    hx, ix, iy = L['haelfte_x'][s], L['innen_x'][s], L['innen_y']
    sp, lb = w('lippe_spiel'), w('lippe_b')
    lz = (rz - w('lippe_h'), rz)
    ax, ay = (ix[0] + sp, ix[1] - sp), (iy[0] + sp, iy[1] - sp)
    P = [quader_schritt('dazu', 'Deckelplatte', hx, L['geh_y'], dz),
         quader_schritt('dazu', 'Lippe', ax, ay, lz),
         quader_schritt('weg', 'Lippe_innen', (ax[0] + lb, ax[1] - lb),
                        (ay[0] + lb, ay[1] - lb), (lz[0] - 1.0, rz))]
    da = w('dom_a') / 2.0 + 0.5
    P.append(schritt('weg', 'Lippe_Dome', 'z', 'rechteck',
                     [(x - da, L['dom_y'][e][0] - 1.0, x + da,
                       L['dom_y'][e][1] + 1.0) for x, _, e in L['dome'][s]],
                     (lz[0] - 1.0, rz)))
    P.append(schritt('weg', 'Deckel_Schrauben', 'z', 'kreis',
                     [(x, y) for x, y, _ in L['dome'][s]],
                     (lz[0] - 1.0, dz[1] + 1.0), d=w('m3_durchgang')))
    if s == 'links':
        fm = L['luefter_mitte']
        P.append(schritt('weg', 'Luefter_Oeffnung', 'z', 'kreis', [fm],
                         (dz[0] - 1.0, dz[1] + 1.0), d=w('luefter_d')))
        r, g = w('luefter_d') / 2.0 + 0.5, w('gitter_b') / 2.0
        P.append(schritt('dazu', 'Gitter', 'z', 'rechteck',
                         [(fm[0] - r, fm[1] - g, fm[0] + r, fm[1] + g),
                          (fm[0] - g, fm[1] - r, fm[0] + g, fm[1] + r)], dz))
        P.append(schritt('weg', 'Luefter_Schrauben', 'z', 'kreis',
                         L['luefter_loecher'], (dz[0] - 1.0, dz[1] + 1.0),
                         d=w('m3_durchgang')))
    else:
        P.append(schritt('weg', 'Schlitze', 'z', 'rechteck',
                         [(x[0], y[0], x[1], y[1])
                          for x, y in L['deckel_schlitze']],
                         (dz[0] - 1.0, dz[1] + 1.0)))
    return P


# --- Materialien -------------------------------------------------------------
# Block unveraendert aus Elektronik.py (dort begruendet): Basismaterial ueber
# eine Kandidatenliste, Dichte nach der Zuweisung einmessen und nachziehen,
# Abweichungen landen im Bericht.
ZIELDICHTE = {'PLA': 1.24, 'PETG': 1.27,        # g/cm3
              'Leiterplatte': 1.85,            # nur Referenz: FR4
              'Kunststoff': 1.10}              # nur Referenz: Luefter, Huelle


# Kandidaten fuer das Basismaterial, aus dem kopiert wird (Reihenfolge = Vorzug)
BASIS_KANDIDATEN = ('ABS Plastic', 'ABS', 'ABS-Kunststoff', 'Nylon',
                    'Polycarbonate', 'Polyethylene', 'Polypropylene',
                    'Kunststoff', 'Plastic')


DICHTE_PROPERTY = ('Density', 'Dichte')


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


# Bibliotheksmaterialien direkt zuweisen (siehe Elektronik.py); wird in
# run() geleert.
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


# --- Geometrie-Helfer (wie Elektronik.py) --------------------------------------
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
    """Konstruktionsebene senkrecht zu Maschinen-Y.
    Skizzenkoordinaten darauf sind (Maschine X, Maschine Z)."""
    if abs(y_mm) < 1e-9:
        return comp.xYConstructionPlane
    # Modell-Z entspricht Maschine Y
    return _offsetebene(comp, comp.xYConstructionPlane, y_mm / 10.0, 'z', name)


def ebene_x(comp, x_mm, name):
    """Konstruktionsebene senkrecht zu Maschinen-X.
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
    """Welche Maschinenachse steht senkrecht auf der Skizze, und wo liegt
    die Ebene? Liefert (feste Achse, Wert in mm), aus der echten Geometrie."""
    pl = adsk.core.Plane.cast(sk.referencePlane.geometry)
    if abs(pl.normal.z) > 0.9:       # Modell-Z = Maschine Y
        return 'y', pl.origin.z * 10.0
    if abs(pl.normal.x) > 0.9:       # Modell-X = Maschine X
        return 'x', pl.origin.x * 10.0
    return 'z', pl.origin.y * 10.0   # Modell-Y = Maschine Z


def punkt(sk, u_mm, v_mm):
    """Punkt der Ebene in Maschinenkoordinaten -> Skizzenkoordinaten (cm).
    (u, v) = (X, Z) auf Ebenen quer zu Y, (Y, Z) quer zu X, (X, Y) quer zu
    Z — wie im Bauplan. Der Umweg ueber modelToSketchSpace macht das
    Ergebnis unabhaengig davon, wie Fusion die Achsen der Ebene orientiert."""
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
    return sk.sketchCurves.sketchLines.addTwoPointRectangle(
        punkt(sk, u0, v0), punkt(sk, u1, v1))


def kreis(sk, u, v, d_mm):
    return sk.sketchCurves.sketchCircles.addByCenterRadius(
        punkt(sk, u, v), d_mm / 20.0)


def vieleck(sk, punkte):
    """Geschlossener Linienzug, die Enden verbunden (ein Profil)."""
    linien = sk.sketchCurves.sketchLines
    p = [punkt(sk, u, v) for u, v in punkte]
    erste = linien.addByTwoPoints(p[0], p[1])
    letzte = erste
    for q in p[2:]:
        letzte = linien.addByTwoPoints(letzte.endSketchPoint, q)
    linien.addByTwoPoints(letzte.endSketchPoint, erste.startSketchPoint)


def tropfen(sk, u, v, d, spitze=1.0, kappe=None):
    """Traene aus tropfen_geometrie(): Kreisbogen plus Flanken."""
    (p0, pm, p1), ecken = tropfen_geometrie(u, v, d, spitze, kappe)
    bogen = sk.sketchCurves.sketchArcs.addByThreePoints(
        punkt(sk, *p0), punkt(sk, *pm), punkt(sk, *p1))
    a, e = bogen.startSketchPoint, bogen.endSketchPoint
    q1 = punkt(sk, *p1)
    if abs(a.geometry.x - q1.x) < 1e-6 and abs(a.geometry.y - q1.y) < 1e-6:
        a, e = e, a                    # a liegt jetzt bei p0, e bei p1
    linien = sk.sketchCurves.sketchLines
    vorher = e
    for ecke in ecken:
        l = linien.addByTwoPoints(vorher, punkt(sk, *ecke))
        vorher = l.endSketchPoint
    linien.addByTwoPoints(vorher, a)


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
    """Extrusion symmetrisch um die Skizzenebene: `laenge_mm` ist die
    Gesamtlaenge, die Ebene liegt in der Mitte. Damit ist die Richtung der
    Ebenennormale irrelevant."""
    ein = comp.features.extrudeFeatures.createInput(prof, operation)
    ein.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(laenge_mm / 10.0), True)
    if ziel is not None:
        ein.participantBodies = [ziel]
    return comp.features.extrudeFeatures.add(ein)


def neu_mittig(comp, prof, dicke_mm):
    return _symmetrisch(comp, prof, dicke_mm,
                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)


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
    Maschinenkoordinaten. erwartet: ((x0,x1),(y0,y1),(z0,z1)) in mm."""
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
        fehler.append('{}: Fussfase uebersprungen — Auflageflaeche pruefen!'
                      .format(was))


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
    """Achsparalleler Quader in Maschinenkoordinaten (mm), als Schritt."""
    return _schritt_bauen(comp, quader_schritt('dazu', name, x, y, z), art,
                          ziel)


def _schritt_bauen(comp, s, art, ziel):
    """Ein Schritt des Bauplans: Skizze in der Mitte von a, symmetrisch
    extrudiert."""
    a0, a1 = s['a']
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, s['achse'], m, 'E_{}_{}{:.2f}'.format(
        comp.name, s['achse'].upper(), m)), 'Sk_' + s['name'])
    if s['form'] == 'rechteck':
        for u0, v0, u1, v1 in s['formen']:
            rechteck(sk, u0, v0, u1, v1)
    elif s['form'] == 'kreis':
        for u, v in s['formen']:
            kreis(sk, u, v, s['d'])
    elif s['form'] == 'vieleck':
        for p in s['formen']:
            vieleck(sk, p)
    elif s['form'] == 'tropfen':
        for u, v in s['formen']:
            tropfen(sk, u, v, s['d'], s['spitze'], s.get('kappe'))
    else:
        raise ValueError('unbekannte Form ' + s['form'])
    return _symmetrisch(comp, alle_profile(sk), a1 - a0, _op(art), ziel)


def plan_bauen(comp, plan, name, fehler):
    """Fuehrt den Bauplan aus; der erste Schritt legt den Koerper an.
    Scheitert ein Schritt, steht er im Bericht, die anderen laufen weiter."""
    k = None
    for s in plan:
        if k is None:
            k = _schritt_bauen(comp, s, 'neu', None).bodies.item(0)
            k.name = name
            continue
        try:
            _schritt_bauen(comp, s, s['art'], k)
        except Exception:
            fehler.append('{}: Schritt {} nicht gebaut: {}'.format(
                name, s['name'],
                traceback.format_exc().strip().splitlines()[-1]))
    return k


# --- Referenzprofil (wie Portal.py) --------------------------------------------
def bau_profil(comp, name, laengs, bereich, quer, z):
    """Aluprofil als Referenz, V-Slot vereinfacht: an jeder 20er-Teilung
    aller vier Seiten eine Nut, in jeder Zelle die Kernbohrung."""
    b = w('rahmen_b')
    if laengs == 'y':
        s = schritt('dazu', name, 'y', 'rechteck',
                    [(quer[0], z[0], quer[1], z[1])], bereich)
    else:
        s = schritt('dazu', name, 'x', 'rechteck',
                    [(quer[0], z[0], quer[1], z[1])], bereich)
    k = _schritt_bauen(comp, s, 'neu', None).bodies.item(0)
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
    a = (bereich[0] - 1.0, bereich[1] + 1.0)
    _schritt_bauen(comp, schritt('weg', 'Nuten_' + name, laengs, 'rechteck',
                                 r, a), 'weg', k)
    _schritt_bauen(comp, schritt('weg', 'Kern_' + name, laengs, 'kreis',
                                 [(u, v) for u in qm for v in zm], a,
                                 d=w('kern_d')), 'weg', k)
    return k


# --- Bauteile ------------------------------------------------------------------
def bau_teil(app, design, comp, L, name, fehler):
    """Ein Druckteil aus dem Bauplan, mit Fussfase, Bauraum-Pruefung und
    PETG."""
    T = L['teile'][name]
    k = plan_bauen(comp, L['plan'][name], name, fehler)
    achse, wert = T['auflage']
    fussfase(comp, k, 'y', wert, w('fase_fuss'), fehler, name)
    bbox_pruefen(k, name, T['bbox'], fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_bohrlehren(app, design, comp, L, fehler):
    """Lehren zum Anhalten vor dem Druck, alle ausgeblendet (SKILL.md):
    Uno und Pi auf ihr Lochbild legen, die Fuge an beide Fugenwande halten.
    Sie liegen unter dem Tisch bzw. neben dem Fach."""
    lehren = []
    z = L['tisch_z'] - 20.0
    sk = skizze(comp, ebene_z(comp, z, 'E_Bohrlehre_Uno'),
                'Sk_Bohrlehre_Uno')
    for x, y in L['uno_loecher']:
        kreis(sk, x, y, w('m3_durchgang'))
    rechteck(sk, L['uno_x'][0], L['uno_y'][0], L['uno_x'][1], L['uno_y'][1])
    lehren.append(('Bohrlehre_Uno', groesstes_profil(sk)))
    # Pi: Lochbild in (Y, Z) auf einer Ebene quer zu X, links neben dem Fach
    x = L['fach_x'][0] - 60.0
    sk = skizze(comp, ebene_x(comp, x, 'E_Bohrlehre_Pi'), 'Sk_Bohrlehre_Pi')
    for y, zz in L['pi_loecher']:
        kreis(sk, y, zz, w('pi_loch_d'))
    rechteck(sk, L['pi_y'][0], L['pi_z'][0], L['pi_y'][1], L['pi_z'][1])
    lehren.append(('Bohrlehre_Pi', groesstes_profil(sk)))
    # Fuge: Umriss der Fugenwand mit Schrauben und Zapfen
    x = L['fach_x'][0] - 90.0
    sk = skizze(comp, ebene_x(comp, x, 'E_Bohrlehre_Fuge'),
                'Sk_Bohrlehre_Fuge')
    for y, zz in L['fuge_bolzen']:
        kreis(sk, y, zz, w('m3_durchgang'))
    for y, zz in L['fuge_zapfen']:
        vieleck(sk, raute(y, zz, w('zapfen_r') + w('zapfen_spiel')
                          * math.sqrt(2.0)))
    rechteck(sk, L['geh_y'][0], L['geh_z'][0], L['innen_y'][1],
             L['geh_z'][1])
    lehren.append(('Bohrlehre_Fuge', groesstes_profil(sk)))
    for name, prof in lehren:
        try:
            k = neu_mittig(comp, prof, w('lehre_dicke')).bodies.item(0)
            k.name = name
            material_zuweisen(app, design, k, 'PLA', fehler)
            k.isLightBulbOn = False
        except Exception:
            fehler.append('{} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))


def referenz_quader(L):
    """Kaufteile und Platzhalter als Quader: (Name, x, y, z, Material)."""
    fm, h = L['luefter_mitte'], w('luefter') / 2.0
    bz = L['boden_z']
    q = [('Uno', L['uno_x'], L['uno_y'], (L['uno_z0'], L['uno_z1']),
          'Leiterplatte'),
         ('Shield_und_Treiber', L['uno_x'], L['uno_y'],
          (L['uno_z1'], L['stapel_z1']), 'Kunststoff'),
         ('USB_B_Stecker', ) + L['usb_b_stecker'] + ('Kunststoff',),
         ('Luefter', (fm[0] - h, fm[0] + h), (fm[1] - h, fm[1] + h),
          L['luefter_z'], 'Kunststoff'),
         ('Pi', L['pi_pcb_x'], L['pi_y'], L['pi_z'], 'Leiterplatte'),
         ('Pi_Bauteile', L['pi_bauteile_x'], L['pi_y'], L['pi_z'],
          'Kunststoff'),
         ('Wandler_12V', L['w12_x'], L['w12_y'], L['w12_z'], 'Leiterplatte'),
         ('Wandler_5V', L['w5_x'], L['w5_y'], L['w5_z'], 'Leiterplatte'),
         ('USB_A_Adapter', ) + L['adapter'] + ('Kunststoff',),
         ('AirAssist_Platz', L['aa_x'], L['aa_y'], (bz, bz + 20.0),
          'Kunststoff')]
    for n in ('USB', 'PWR'):
        q.append(('Pi_Stecker_' + n, ) + L['pi_stecker'][n] + ('Kunststoff',))
    for name, _, x, y, z in L['wago']:
        q.append(('Wago_' + name.replace('+', '').replace(' ', ''), x, y, z,
                  'Kunststoff'))
    iy0 = L['innen_y'][0]
    bx, ez = L['buchse']
    q.append(('Buchse', (bx - 5.5, bx + 5.5), (iy0, iy0 + 15.0),
              (ez - 5.5, ez + 5.5), 'Kunststoff'))
    sx, _ = L['schalter']
    q.append(('Schalter', (sx - 10.0, sx + 10.0), (iy0, iy0 + 20.0),
              (ez - 10.0, ez + 10.0), 'Kunststoff'))
    return q


def bau_referenz(app, design, teile, L, fehler):
    """Hinteres 2060, die hinteren Enden der 2040 und die Kaufteile — nur
    zur Ansicht, NICHT drucken. Jedes Teil wird fuer sich gebaut: scheitert
    eines, steht das im Bericht."""
    R = L['R']

    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    pr = teile['Ref_Profile']
    k = sicher('2060', bau_profil, pr, '2060_hinten', 'x',
               (-w('quer_laenge') / 2.0, w('quer_laenge') / 2.0),
               L['quer_y'], (L['tisch_z'], w('rahmen_z0')))
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)
    for s in (-1, 1):
        n = 'links' if s < 0 else 'rechts'
        x = sorted((s * (R - w('rahmen_b') / 2.0),
                    s * (R + w('rahmen_b') / 2.0)))
        k = sicher('2040 ' + n, bau_profil, pr, '2040_hinten_' + n, 'y',
                   (w('rahmen_y0'), L['quer_y'][1] + 40.0), tuple(x),
                   (w('rahmen_z0'), w('rahmen_z0') + w('rahmen_h')))
        if k:
            material_zuweisen(app, design, k, 'Aluminum 6061', fehler)

    el = teile['Ref_Elektronik']
    for name, x, y, z, mat in referenz_quader(L):
        def quader_ref(name=name, x=x, y=y, z=z):
            kk = quader(el, name, x, y, z, 'neu').bodies.item(0)
            kk.name = name
            return kk
        k = sicher(name, quader_ref)
        if k:
            material_zuweisen(app, design, k, mat, fehler)


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/elektronik_check.py)."""
    gx, gy, gz = L['geh_x'], L['geh_y'], L['geh_z']
    fm = L['luefter_mitte']
    m5 = L['m5']['links']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py, Portal in der Mitte',
        '  seines Wegs (Y nach vorn, Z senkrecht, X = 0 Mitte Portalrohr).',
        '  Im Modell sind Y und Z getauscht (Modell-Z = Maschine Y).',
        '',
        'LAGE: im Fach hinter dem hinteren 2060, unter den 2040.',
        '  Kasten X {:+.1f}..{:+.1f}, Y {:+.1f}..{:+.1f}, Z {:+.1f}..{:+.1f}'
        .format(gx[0], gx[1], gy[0], gy[1], gz[0], gz[1]),
        '  ({:.0f} x {:.0f} x {:.0f} mm), dazu die Ohren bis X {:+.1f}.'.format(
            gx[1] - gx[0], gy[1] - gy[0], gz[1] - gz[0],
            L['ohr_x']['rechts'][1]),
        '  Ueber das Fach (55 mm) ragen nur Kasten, Deckel und Luefter in',
        '  der Mitte (|X| <= 225), bis Z {:+.1f}; dort faehrt nichts so tief.'
        .format(L['luefter_z'][1]),
        '',
        'TEILE (PETG, je <= 250 mm): Fach_links, Fach_rechts, Deckel_links,',
        '  Deckel_rechts. Die Fachhaelften stehen beim Druck auf dem Boden,',
        '  die Deckel liegen mit der Oberseite auf dem Bett. Keine Stuetzen:',
        '  Fenster mit 45-Grad-Dach, waagerechte Loecher als Traene, Dome mit',
        '  45-Grad-Stuetze, Pi-Stehbolzen als Traene mit der Spitze unten.',
        '',
        'FUGE: die Haelften mit 4 x M3x12 und Mutter durch beide',
        '  Fugenwaende, 2 Rauten-Zapfen links richten aus (Bohrlehre_Fuge).',
        'MONTAGE: leer an die Rueckseite des hinteren 2060: je Ohr 2 x',
        '  M5x{:.0f} in Hammermuttern der unteren und oberen Nut (Z {:+.0f} /'
        .format(w('m5_l'), m5[0][1]),
        '  {:+.0f}), innen je 1 x M5x{:.0f} in der oberen Nut bei X {:+.0f} /'
        .format(m5[1][1], w('m5_l'), L['m5']['links'][2][0]),
        '  {:+.0f}. Inbus von hinten; vor dem Verkabeln anziehen.'.format(
            L['m5']['rechts'][2][0]),
        '',
        'GASSEN: vorn Signale (Lichtschranken, 5 V, Waechter), hinten',
        '  Leistung (24 V, 12 V Laser, Motoren). Leitwaende {:.0f} mm hoch,'
        .format(w('leitwand_h')),
        '  Oesen fuer Kabelbinder 2,5 mm am Boden; Fenster je Gasse in den',
        '  Endwaenden (Zugentlastung an der ersten Oese) und in der Fuge.',
        'UNO: Platine laengs X, USB rechts zum Pi, Endschalter-Stifte links.',
        '  4 x M3x8 selbstschneidend in die Stehbolzen, vor dem Shield.',
        'PI: senkrecht an der Fugenwand links, 4 x M2.5x6 in die',
        '  Stehbolzen; Buchsen unten, SD-Karte hinten. W17 kurzes OTG-Kabel.',
        'LUEFTER 24 V: auf dem linken Deckel ueber dem Uno (X {:+.1f},'
        .format(fm[0]),
        '  Y {:+.1f}), 4 x M3x16 mit Mutter, blaest nach unten; Stecker an'
        .format(fm[1]),
        '  der Litze, damit der Deckel abgeht.',
        'RECHTS: 5-V-Wandler vorn mit USB-A-Adapter (Schraubklemmen, 5 V',
        '  direkt an die Wago +5 V), 2 Kabelbinder durch Schlitze im Boden.',
        '  Wago 24 V und GND vor der Rueckwand, Buchse (Loch {:.1f}) und'
        .format(w('buchse_d')),
        '  Schalter (Loch {:.1f}) hinten. Platz fuer ein Air-Assist-Modul'
        .format(w('schalter_d')),
        '  bis {:.0f} x {:.0f} an der Fuge, Durchbruch in der Rueckwand.'
        .format(w('aa_l'), w('aa_b')),
        'LINKS: Wago +5 V und GND 5 V senkrecht an der Endwand (Klebeband,',
        '  Draehte von unten, Hebel nach innen); 12-V-Wandler hinten neben',
        '  dem Uno, Ausgang nach links, 2 Kabelbinder durch den Boden.',
        'DECKEL: Lippe innen, 4 x M3x8 in Einsaetze M3 der Dome je Seite.',
        '',
        'NICHT GEMESSEN [w]/[?]: Wago (Datenblatt), USB-A-Adapter, Stecker,',
        '  Lochbild des Pi (Bohrlehre_Pi), Einbauloch des Schalters.',
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
        # schon an seinem Platz; nichts bewegt sich, alles fixiert.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Fach_links', 'Fach_rechts', 'Deckel_links',
                     'Deckel_rechts', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o
        for name in ('Fach_links', 'Fach_rechts', 'Deckel_links',
                     'Deckel_rechts'):
            bau_teil(app, design, occ[name].component, L, name, fehler)
        bau_bohrlehren(app, design, occ['Bohrlehren'].component, L, fehler)
        for o in occ.values():
            o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Profile', 'Ref_Elektronik'):
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
