# Kamerahalter.py — Halter fuer die Raspberry Pi Kamera v1.3 (wie verbaut;
# Lochbild wie Camera Module 2/3) vorn rechts auf dem vorderen 2060, vor dem
# Elektronikfach
#
# Wozu: Autofokus ueber Z. Der Kopf faehrt an einen festen Messpunkt kurz
# innerhalb der Anschlagecke vorn rechts (Spannmittel.py Rev. 2), Z ganz
# oben, und schaltet den Laser kurz und schwach ein. Der Strahl steht
# senkrecht, der Punkt liegt also bei jeder Werkstueckdicke an derselben
# Stelle. Die Kamera sieht ihn schraeg von vorn rechts oben, je nach Dicke
# hoeher oder tiefer im Bild: ein Bild ergibt die Hoehe der Oberflaeche, Z
# faehrt auf den Fokus. Das Kabel zum Pi im Fach ist kurz.
#
# Rev. 2 (2026-11-19): neu fuer vorn rechts. An der Maschine steht das Fach
# vorn (Elektronikfach.py Rev. 2), die Kamera sitzt dort auf dem vorderen
# 2060 am rechten 2040 und soll bleiben; der Anschlag kommt vor die Kamera.
# Rev. 1 stand hinten und hielt die Kamera waagerecht. Von vorn liegt der
# Messpunkt 18 bis 43 Grad unter der Linse; das Bild reicht hochkant nur
# +-27 Grad. Deshalb ist die Kamera jetzt geneigt.
#
# Ein Druckteil, dazu Lehre und Referenzteile:
#   Kamerahalter  Fuss auf der Oberseite des vorderen 2060, 2 x M5x10 in
#                 Hammermuttern der Nut; ueber dem Eckwinkel am rechten
#                 2040 unter 45 Grad ausgespart. Ein senkrechter Steg traegt die
#                 Wand, die zum Messpunkt gedreht (blick_az) und nach vorn
#                 unten geneigt ist (neige). Vier Polster tragen die Kamera
#                 hochkant: oben 2 x M2x8 mit Mutter in Taschen hinter der
#                 Wand, unten 2 Zapfen durch die Loecher. Die Kabelkante
#                 zeigt zum Fach und zum Pi.
#   Bohrlehre_Kamera  ausgeblendet: Umriss und Lochbild der Kamera.
#   Referenz_nicht_drucken  die Kamera, M5-Koepfe und die Sichtlinien zum
#                 Messpunkt.
#
# Platz: Vor dem vorderen 2060 faehrt der Laser bis Y 182, aber nur bis
# X 204,8; rechts davon kommt nur die Schlittenplatte, und die bis Y 147.
# Die Kamera ragt deshalb nur rechts von X 208 ueber die Innenkante des 2060
# hinaus. Rechts bleibt sie links vom Y-Riemen (X 242,4), hinten vom Fach
# frei (Deckel geht ab). tools/kamerahalter_check.py prueft das.
#
# Drucklage: Fuss aufs Bett. Die Wand lehnt neige Grad nach vorn, ihre
# Kameraseite haengt damit hoechstens so weit ueber (unter 45 Grad).
# Polster und Zapfen als Traene mit der Spitze unten, Loecher fuer die M2 als
# Traene mit der Spitze oben, Muttertaschen als Sechseck mit einer Ecke oben
# — jeweils im geneigten Rahmen. Keine Stuetzen.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: X nach rechts, Y nach
# vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im Fusion-Modell
# sind Y und Z getauscht (Modell-Z = Maschine Y). Gebaut wird in zwei
# Rahmen:
#   H (Halter): um Z zum Messpunkt gedreht, Ursprung unter der Linsenfront;
#     x quer zum Blick, y in Blickrichtung (waagerecht), z = Maschine Z.
#     Fuss, Steg, M5-Loecher.
#   K (Kamera): H um die x-Achse um neige gekippt, Ursprung in der
#     Linsenfront; y in Blickrichtung (geneigt), z nach oben zur Kamera.
#     Wand, Polster, Zapfen, M2-Loecher, Muttertaschen.
# kippen() bringt K nach H, verschieben() H an die Maschine. tools/
# stl_export.py fuehrt beide Bauplaene aus und vereint sie genauso.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback
import math

SKRIPT_NAME = 'Kamerahalter'
REVISION = 2

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog). Winkel in Grad und
# Pixelzahlen stehen in EINHEIT.
MASSE = {
    # --- Rahmen (wie Portal.py) [v] -----------------------------------------
    'quer_vorn_y0':       (185.0, 'vorderes 2060: Innenseite (Maschine Y)'),
    'quer_vorn_y1':       (205.0, 'vorderes 2060: Vorderseite (Maschine Y)'),
    'rahmen_b':            (20.0, 'Profil: Breite'),
    'quer_h':              (60.0, '2060: Hoehe'),
    'rahmen_z0':          (-69.0, 'Oberseite des 2060 = Unterkante der 2040'),
    'rahmen_x_innen':     (247.0, 'rechtes 2040: Innenseite (Maschine X)'),
    # Nut 6 [w], wie Kabelhalter.py
    'nut_lippe':            (1.8, 'Nut 6: Dicke der Lippe'),
    'nut_tiefe':            (6.0, 'Nut 6: Platz ab Profilflaeche bis zum Nutgrund'),
    'nutenstein_h':         (4.0, 'Hammermutter M5: Gewindelaenge'),
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante (Referenz, wie Portal.py)'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen (Referenz)'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Referenz)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle (Referenz)'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer (Referenz)'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund (Referenz)'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung (Referenz)'),

    # --- Elektronikfach vorn (Elektronikfach.py Rev. 2, gedreht) [v] ---------
    'fach_y0':            (205.0, 'Fach: Montageplatte an der Vorderseite des 2060'),
    'fach_x1':            (222.0, 'Fach: Kasten, halbe Breite'),
    'fach_rand_z':        (-50.0, 'Fach: Oberkante der Waende'),
    'deckel_z1':          (-47.5, 'Fach: Oberseite des Deckels'),
    # Kamerabuchse des Pi im Modell (Fachkoordinaten -10,5 / -275 / -73,
    # gedreht). Am Aufbau liegt der Pi anders (Fotos 2026-11-19); dort
    # reicht das 200-mm-Kabel laut Angabe.
    'pi_buchse_x':         (10.5, 'Pi: Kamerabuchse im Modell, Maschine X [?]'),
    'pi_buchse_y':        (230.0, 'Pi: Kamerabuchse im Modell, Maschine Y [?]'),
    'pi_buchse_z':        (-73.0, 'Pi: Kamerabuchse im Modell, Maschine Z [?]'),

    # --- was vorn herankommt (tools/kamerahalter_check.py rechnet nach) -----
    # Der Laser ueber den ganzen Weg bis zum Softlimit vorn; rechts davon nur
    # noch die Schlittenplatte. Der Y-Riemen laeuft innen am rechten 2040.
    'laser_vorn_y':       (182.0, 'Toolhead: Laser, vorderste Lage (Softlimit)'),
    'laser_x1':           (204.8, 'Toolhead: Laser, rechteste Lage'),
    'schlitten_vorn_y':   (147.0, 'Toolhead: Schlittenplatte, vorderste Lage'),
    'riemen_x0':          (242.4, 'Y-Riemen rechts: Innenseite (Maschine X)'),
    'riemen_z0':          (-42.0, 'Y-Riemen rechts: Unterkante'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),

    # --- Messpunkt (Spannmittel.py Rev. 2, Opferplatte.py) [v] ---------------
    'ecke_x':            (183.35, 'Anschlagwinkel: Innenecke, Maschine X (vorn rechts)'),
    'ecke_y':             (160.5, 'Anschlagwinkel: Innenecke, Maschine Y'),
    # 30 links, 58 hinter der Ecke: so bleibt die Kamera auch beim dicksten
    # Werkstueck ueber 100 mm entfernt, der Punkt fuer alle Dicken im Bild
    'mp_links':            (30.0, 'Messpunkt: so weit links der Innenecke'),
    'mp_hinten':           (58.0, 'Messpunkt: so weit hinter der Innenecke'),
    'platte_z1':         (-129.0, 'Oberseite der Opferplatte'),
    'werkstueck_max':      (58.0, 'dickstes Werkstueck unter dem Toolhead'),

    # --- Kamera v1.3 (OV5647), wie verbaut [w]/[?] --------------------------
    # Foto 2026-11-19: an der Maschine steckt eine Raspberry Pi Kamera v1.3
    # (Modul "P5V04A SUNNY", rote LED D1). Lochbild und Kabelkante wie
    # Camera Module 2/3 (Massblatt RP-008153), also passt auch ein Module 3.
    # Optik nach Raspberry-Pi-Doku [w]; Hoehe des Linsenblocks aus 9 mm
    # Gesamtdicke [?]. Fester Fokus ab Werk 1 m bis unendlich: die Linse
    # wird auf den Messabstand gedreht (Pruefung 6). Bohrlehre an die
    # Platine halten, bevor der Halter gedruckt wird.
    'cam_b':               (25.0, 'Kamera: Platine, Breite (laengs der Kabelkante)'),
    'cam_h':               (24.0, 'Kamera: Platine, Hoehe (quer zur Kabelkante)'),
    'cam_pcb':              (1.0, 'Kamera: Platinendicke'),
    'cam_linse':          (9.462, 'Kamera: Linsenmitte ab der Kabelkante (wie Module 2, Foto passt)'),
    'cam_front':           (5.25, 'Kamera: Linsenfront vor der Platine (9 - 1 - 2,75) [?]'),
    'cam_block':            (8.5, 'Kamera: Linsenblock, Kantenlaenge [?]'),
    'cam_block_t':          (3.5, 'Kamera: Linsenblock, Dicke [?]'),
    'cam_tubus_d':          (6.0, 'Kamera: Objektiv, Durchmesser [?]'),
    'cam_loch_d':           (2.2, 'Kamera: Befestigungsloecher'),
    'cam_loch_rand':        (2.0, 'Kamera: Loecher ab Gegenkante und Seiten'),
    'cam_loch_ab':         (12.5, 'Kamera: Lochabstand quer zur Kabelkante'),
    'cam_pad_frei':        (4.75, 'Kamera: freier Ring um die Loecher'),
    'cam_stecker_b':      (19.61, 'Kamera: Stecker hinten, Breite'),
    'cam_stecker_h':       (5.71, 'Kamera: Stecker, Tiefe ab der Kabelkante'),
    'cam_stecker_t':       (2.75, 'Kamera: Stecker, Hoehe ueber der Rueckseite'),
    'cam_f':                (3.6, 'Kamera: Brennweite'),
    'cam_blende':           (2.9, 'Kamera: Blende f/2,9'),
    'cam_pixel':         (0.0014, 'Kamera: Pixelgroesse'),
    'cam_px_b':          (2592.0, 'Kamera: Pixel laengs der Kabelkante'),
    'cam_px_h':          (1944.0, 'Kamera: Pixel quer zur Kabelkante'),
    'cam_fov_b':           (53.5, 'Kamera: Bildwinkel laengs der Kabelkante'),
    'cam_fov_h':          (41.41, 'Kamera: Bildwinkel quer zur Kabelkante'),
    'kabel_l':            (200.0, 'Kamerakabel Standard-Mini: Laenge'),
    'kabel_b':             (16.0, 'Kamerakabel: Breite an der Kamera'),
    'kabel_steif':          (3.0, 'Kamerakabel: steifes Ende vor der Kabelkante'),

    # --- Lage der Kamera ---------------------------------------------------------
    # Die Linse sitzt ueber der Innenkante des 2060, 30,5 mm vom rechten
    # 2040 (an der Maschine 30 bis 80 mm, Angabe und Foto 2026-11-19):
    # rechts vom Laser-Weg (X 204,8), so dass die Kamera dort vor das 2060
    # ragen darf. Blickrichtung und Neigung rechnet lage() aus der Lage des
    # Messpunkts. Die Lage ist aus einer Suche ueber X, Y, Z: groesster
    # kleinster Abstand zu Laser, Fach und Y-Riemen, Steg ganz auf dem Fuss.
    'linse_x':            (216.5, 'Kamera: Linsenfront, Maschine X'),
    'linse_y':            (185.0, 'Kamera: Linsenfront, Maschine Y'),
    'linse_z':            (-42.0, 'Kamera: Linsenfront, Maschine Z'),
    # +1: die Kabelkante liegt bei lokal x < 0 wie in Rev. 1; -1: die Kamera
    # um ihre Achse gedreht, die Kabelkante bei x > 0 (zum Fach)
    'kabel_seite':         (-1.0, 'Kamera: Kabelkante bei -x (+1) oder +x (-1)'),

    # --- Halter ------------------------------------------------------------------
    # Rev. 1: erster Stand, hinten, waagerecht.
    # Rev. 2: vorn rechts, geneigt, Steg statt Rippe, Zapfen unten.
    'fuss_t':               (4.5, 'Fuss: Dicke (M5x10: 5,5 in der Nut, 3,7 im Stein)'),
    'fuss_innen':           (0.5, 'Fuss: so weit hinter der Innenseite des 2060'),
    'fuss_aussen':          (1.0, 'Fuss: so weit vor der Vorderseite des 2060 (Fach)'),
    # Die M5 sitzen links neben der Kamera: Dort ist der Inbus von oben frei,
    # auch mit eingesetzter Kamera; rechts steht der Steg ueber der Nut
    'fuss_x0':            (190.0, 'Fuss: linke Kante, Maschine X'),
    # Innen am rechten 2040 sitzt ein Eckwinkel in der oberen Nut des 2060
    # (hardware-notizen.md, 2 von 8 je Kreuzung). Seine Schenkel sind nicht
    # gemessen; gerechnet wird mit der Huelle: Dreieck 20 x 20 unter der
    # Schraege. Fuss und Steg sind parallel dazu unter 45 Grad weggeschnitten
    # (druckt ohne Stuetzen); der Fuss endet oben dort, wo der Schnitt ihn
    # trifft. Fehlt der Winkel, schadet der Schnitt nicht.
    'winkel_l':            (20.0, 'Eckwinkel 2040/2060 innen auf dem 2060: Schenkel [v] (Form [?])'),
    'winkel_luft':          (1.0, 'Eckwinkel: Luft senkrecht zur Schraege'),
    'm5_links':           (196.0, 'Fuss: linke M5, Maschine X'),
    'm5_rechts':          (207.0, 'Fuss: rechte M5, Maschine X'),
    'wand_t':               (4.0, 'Wand: Dicke'),
    'pad_h':                (2.0, 'Polster: Hoehe (Platz fuer die Bauteile hinten)'),
    'pad_d':                (4.5, 'Polster: Durchmesser der Traene'),
    'wand_rand':            (1.0, 'Wand: reicht so weit ueber die Polster'),
    'wand_oben':            (1.0, 'Wand: endet so weit ueber der Platine'),
    'stecker_luft':         (0.5, 'Wand: endet so weit vor dem Stecker'),
    'steg_ueber':           (0.5, 'Steg: reicht so weit in die Wand'),
    # Zapfen in den unteren Loechern (Ø2,2): Traene mit der Spitze unten,
    # flach, damit sie ins Loch passt
    'zapfen_d':             (1.8, 'Zapfen: Durchmesser der Traene'),
    'zapfen_kappe':        (0.05, 'Zapfen: flach so weit unter dem Kreis'),
    'zapfen_ueber':         (0.8, 'Zapfen: ragt so weit vor die Platine'),

    # --- Normteile -------------------------------------------------------------
    'm5_l':                (10.0, 'Schraube M5x10 (Zylinderkopf, ohne Scheibe)'),
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'inbus_frei_d':         (6.0, 'Werkzeugkorridor fuer den Inbus'),
    'm2_l':                 (8.0, 'Schraube M2x8 (Zylinderkopf)'),
    'm2_durchgang':         (2.4, 'M2 Durchgang (Traene)'),
    'm2_kappe':             (0.3, 'M2-Traene: flach so weit ueber dem Kreis'),
    'm2_kopf_d':            (3.8, 'M2 Zylinderkopf: Durchmesser'),
    'm2_kopf_h':            (2.0, 'M2 Zylinderkopf: Hoehe'),
    'm2_mutter_sw':         (4.0, 'Mutter M2: Schluesselweite'),
    'm2_mutter_h':          (1.6, 'Mutter M2: Hoehe'),
    'mutter_spiel':         (0.3, 'Muttertasche: Spiel auf SW und Tiefe'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
    'lehre_dicke':          (2.0, 'Bohrlehre: Plattendicke'),
}

# Einheiten der User-Parameter, wo es nicht mm sind
EINHEIT = {'cam_fov_b': 'deg', 'cam_fov_h': 'deg', 'cam_px_b': '',
           'cam_px_h': '', 'kabel_seite': ''}

ZIELDICHTE = {'PLA': 1.24, 'PETG': 1.27,         # g/cm3
              'Leiterplatte': 1.85,             # nur Referenz: FR4
              'Kunststoff': 1.10}               # nur Referenz

# Dicken, fuer die die Sicht gerechnet und im Bericht gezeigt wird (mm)
DICKEN = (0.0, 3.0, 10.0, 20.0, 30.0, 40.0, 50.0)


def w(name):
    """Wert in mm (Winkel in Grad, Pixel als Zahl)."""
    return MASSE[name][0]


# --- Bauplan: Schritte, die Fusion und manifold3d gleich ausfuehren -----------
# Wie Elektronikfach.py: Jeder Schritt ist ein Prisma, Formen in der Ebene
# quer zu `achse`, entlang `achse` von a[0] bis a[1]. In der Ebene gilt
# (u, v) = (x, y) fuer 'z', (x, z) fuer 'y' und (y, z) fuer 'x' — hier im
# lokalen Rahmen. art 'dazu' vereint, 'weg' schneidet; der erste Schritt
# legt den Koerper an.
def schritt(art, name, achse, form, formen, a, **mehr):
    s = dict(art=art, name=name, achse=achse, form=form,
             formen=list(formen), a=(min(a), max(a)))
    s.update(mehr)
    return s


def quader_schritt(art, name, x, y, z):
    """Achsparalleler Quader: Rechteck in (x, y), entlang z."""
    return schritt(art, name, 'z', 'rechteck', [(x[0], y[0], x[1], y[1])], z)


def tropfen_geometrie(u, v, d, spitze=1.0, kappe=None):
    """Traene in (u, v): unten (spitze +1) ein Kreisbogen, oben zwei
    45-Grad-Flanken bis zur Spitze — oder bis `kappe` ueber dem Kreis
    flach. spitze -1 dreht sie um (Spitze unten, fuer Zapfen, die aus einer
    senkrechten Wand ragen). Liefert ((Bogen: Start, Mitte, Ende),
    [Ecken vom Bogenende zum Bogenstart]). Wie Elektronikfach.py."""
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


def sechseck(u, v, sw):
    """Sechseck mit Schluesselweite sw, eine Ecke oben: alle Flanken der
    Tasche stehen 30 Grad aus der Senkrechten, druckt ohne Stuetzen."""
    r = sw / math.sqrt(3.0)
    return [(u + r * math.cos(math.radians(90.0 + 60.0 * i)),
             v + r * math.sin(math.radians(90.0 + 60.0 * i)))
            for i in range(6)]


# --- Rahmen: K (Kamera, geneigt) -> H (Halter) -> Maschine -------------------
def welt(L, x, y):
    """H (x, y) -> Maschine (X, Y); z bleibt."""
    return (L['linse'][0] + x * L['sin'] + y * L['cos'],
            L['linse'][1] - x * L['cos'] + y * L['sin'])


def lokal(L, X, Y):
    """Maschine (X, Y) -> H (x, y)."""
    dx, dy = X - L['linse'][0], Y - L['linse'][1]
    return (dx * L['sin'] - dy * L['cos'], dx * L['cos'] + dy * L['sin'])


def k_nach_h(L, x, y, z):
    """K (x, y, z) -> H (x, y, z): um die x-Achse um neige nach unten
    gekippt, Ursprung in der Linsenfront; H-z ist Maschine Z."""
    sn, cn = L['sin_n'], L['cos_n']
    return (x, y * cn + z * sn, L['linse'][2] - y * sn + z * cn)


def h_nach_k(L, x, y, z):
    """H (x, y, z) -> K (x, y, z)."""
    sn, cn = L['sin_n'], L['cos_n']
    zr = z - L['linse'][2]
    return (x, y * cn - zr * sn, y * sn + zr * cn)


def k_nach_maschine(L, x, y, z):
    xh, yh, zh = k_nach_h(L, x, y, z)
    return welt(L, xh, yh) + (zh,)


def ecken_quader(x, y, z):
    return [(a, b, c) for a in x for b in y for c in z]


def lage():
    """Alle Lagen (mm) und die Bauplaene. Einzige Quelle fuer Geometrie, STL,
    Zeichnung und Pruefung (tools/kamerahalter_check.py, stl_export.py,
    kamerahalter_zeichnen.py)."""
    L = {}
    lx, ly, lz = w('linse_x'), w('linse_y'), w('linse_z')
    L['linse'] = (lx, ly, lz)

    # ---- Messpunkt; Blick waagerecht zu ihm, Neigung auf die Mitte ---------
    # Die Achse zielt waagerecht genau auf den Punkt (quer 0). Geneigt wird so
    # weit, dass der Punkt fuer die duennste und die dickste Platte gleich
    # weit unter und ueber der Bildmitte liegt.
    mp = (w('ecke_x') - w('mp_links'), w('ecke_y') - w('mp_hinten'))
    L['mp'] = mp
    dx, dy = mp[0] - lx, mp[1] - ly
    A = math.atan2(dy, dx)
    L['blick_az'] = math.degrees(A) % 360.0
    L['sin'], L['cos'] = math.sin(A), math.cos(A)
    horiz = math.hypot(dx, dy)
    tief = [math.atan2(lz - (w('platte_z1') + t), horiz)
            for t in (0.0, w('werkstueck_max'))]
    nu = (tief[0] + tief[1]) / 2.0
    L['neige'] = math.degrees(nu)
    sn, cn = math.sin(nu), math.cos(nu)
    L['sin_n'], L['cos_n'] = sn, cn
    # K -> H als Matrix (Zeilen, Maschinenachsen): fuer stl_export und Fusion
    L['k_nach_h'] = [[1.0, 0.0, 0.0, 0.0], [0.0, cn, sn, 0.0],
                     [0.0, -sn, cn, lz]]

    # ---- Kamera im Rahmen K: Linsenfront bei (0, 0, 0), hochkant ----------
    # kabel_seite +1: Kabelkante bei x < 0 (wie Rev. 1), -1: gespiegelt
    s = 1.0 if w('kabel_seite') > 0 else -1.0
    L['kabel_seite'] = s

    def xb(a, b):
        return tuple(sorted((s * a, s * b)))
    kab = -w('cam_linse')                          # Kabelkante
    geg = w('cam_h') - w('cam_linse')              # Gegenkante
    hz = w('cam_b') / 2.0                           # halbe Hoehe
    yv = -w('cam_front')                            # Platine vorn
    yh = yv - w('cam_pcb')                          # Platine hinten
    ys = yh - w('cam_stecker_t')                    # Stecker hinten
    L['platine'] = (xb(kab, geg), (yh, yv), (-hz, hz))
    L['stecker'] = (xb(kab, kab + w('cam_stecker_h')), (ys, yh),
                    (-w('cam_stecker_b') / 2.0, w('cam_stecker_b') / 2.0))
    bk = w('cam_block') / 2.0
    yb = yv + w('cam_block_t')
    L['block'] = ((-bk, bk), (yv, yb), (-bk, bk))
    tr = w('cam_tubus_d') / 2.0
    L['tubus'] = ((-tr, tr), (yb, 0.0), (-tr, tr))
    # Loecher: oben (z > 0) die Schrauben mit Mutter, unten die Zapfen —
    # hinter der Wand unten steht der Steg, dort ist kein Platz fuer Muttern
    xz = s * (geg - w('cam_loch_rand'))
    xs_ = s * (geg - w('cam_loch_rand') - w('cam_loch_ab'))
    zo = hz - w('cam_loch_rand')
    L['loecher_schraube'] = [(xs_, zo), (xz, zo)]
    L['loecher_zapfen'] = [(xs_, -zo), (xz, -zo)]
    L['loecher'] = L['loecher_schraube'] + L['loecher_zapfen']
    rk = w('m2_kopf_d') / 2.0
    L['koepfe'] = [((x - rk, x + rk), (yv, yv + w('m2_kopf_h')),
                    (z - rk, z + rk)) for x, z in L['loecher_schraube']]
    L['zapfen_y'] = (yh - 0.5, yv + w('zapfen_ueber'))
    L['kabel_aus'] = (s * kab, (yh + ys) / 2.0, 0.0)

    # ---- Wand im Rahmen K -------------------------------------------------
    wy1 = yh - w('pad_h')                           # Wand vorn
    wy0 = wy1 - w('wand_t')                         # Wand hinten
    xs = [x for x, _ in L['loecher']]
    pr = w('pad_d') / 2.0
    st = L['stecker'][0]
    if s > 0:
        wx = (st[1] + w('stecker_luft'), max(xs) + pr + w('wand_rand'))
    else:
        wx = (min(xs) - pr - w('wand_rand'), st[0] - w('stecker_luft'))
    wz = (-hz - w('wand_oben'), hz + w('wand_oben'))
    L['wand'] = (wx, (wy0, wy1), wz)
    L['pad_y'] = (wy1, yh)
    L['pad_kappe'] = max(0.0, w('cam_pad_frei') / 2.0 - pr)
    tasche = w('m2_mutter_h') + w('mutter_spiel')
    L['tasche_y'] = (wy0, wy0 + tasche)
    L['tasche_sw'] = w('m2_mutter_sw') + w('mutter_spiel')

    # ---- Fuss (Maschine) und Steg (H) -------------------------------------
    zf0 = w('rahmen_z0')
    zf1 = zf0 + w('fuss_t')
    L['fuss_z'] = (zf0, zf1)
    q0, q1 = w('quer_vorn_y0'), w('quer_vorn_y1')
    # Eckwinkel innen am rechten 2040: Huelle und 45-Grad-Schnitt (MASSE)
    xi, wl = w('rahmen_x_innen'), w('winkel_l')
    L['winkel'] = ((xi - wl, xi), (q0, q1), (zf0, zf0 + wl))
    xc = xi - wl - w('winkel_luft') * math.sqrt(2.0)
    L['winkel_schnitt_x'] = xc              # Schnitt trifft die Oberseite
    fx = (w('fuss_x0'), xc + w('fuss_t'))   # Fuss oben bis zum Schnitt
    fy = (q0 + w('fuss_innen'), q1 - w('fuss_aussen'))
    L['quer_y'] = (q0, q1)
    L['nut_y'] = (q0 + q1) / 2.0
    L['fuss_x'], L['fuss_y'] = fx, fy
    L['fuss_welt'] = [(fx[0], fy[0]), (fx[1], fy[0]), (fx[1], fy[1]),
                      (fx[0], fy[1])]
    L['fuss'] = [lokal(L, X, Y) for X, Y in L['fuss_welt']]
    L['m5_welt'] = [(w('m5_links'), L['nut_y']), (w('m5_rechts'), L['nut_y'])]
    L['m5'] = [lokal(L, X, Y) for X, Y in L['m5_welt']]
    # Steg: senkrecht unter der Unterseite der Wand, vom Fuss bis knapp in
    # die Wand; die Unterseite liegt hinten hoeher als vorn
    sy = (wy0 * cn + wz[0] * sn, wy1 * cn + wz[0] * sn)
    sz1 = lz - wy0 * sn + wz[0] * cn + w('steg_ueber')
    L['steg'] = (wx, sy, (zf1 - 0.5, sz1))
    # M5x10: Kopf auf dem Fuss, Rest in der Nut
    L['m5_in_nut'] = w('m5_l') - w('fuss_t')
    L['m5_eingriff'] = (min(L['m5_in_nut'], w('nut_lippe')
                            + w('nutenstein_h')) - w('nut_lippe'))
    # M2x8: Kopf auf der Platine, Mutter in der Tasche
    L['m2_stapel'] = w('cam_pcb') + w('pad_h') + w('wand_t')
    L['m2_bis_mutter'] = L['m2_stapel'] - tasche + w('m2_mutter_h')
    L['m2_rest'] = w('m2_l') - L['m2_bis_mutter']

    # ---- Bauplaene: H (Fuss, Steg, M5) und K (Wand mit Kamerasitz) ------
    ts = list(L['loecher_schraube'])
    (sx0, sx1), (sy0, sy1), (sz0, sz1_) = L['steg']
    L['plan'] = {
        'Kamerahalter': [
            schritt('dazu', 'Fuss', 'z', 'vieleck', [L['fuss']], (zf0, zf1)),
            quader_schritt('dazu', 'Steg', (sx0, sx1), (sy0, sy1),
                           (sz0, sz1_)),
            schritt('weg', 'M5_Loecher', 'z', 'kreis', L['m5'],
                    (zf0 - 1.0, zf1 + 1.0), d=w('m5_durchgang'))],
        'Kamerahalter_Wand': [
            quader_schritt('dazu', 'Wand', *L['wand']),
            schritt('dazu', 'Polster', 'y', 'tropfen', L['loecher'],
                    L['pad_y'], d=w('pad_d'), spitze=-1.0,
                    kappe=L['pad_kappe']),
            schritt('dazu', 'Zapfen', 'y', 'tropfen', L['loecher_zapfen'],
                    L['zapfen_y'], d=w('zapfen_d'), spitze=-1.0,
                    kappe=w('zapfen_kappe')),
            schritt('weg', 'M2_Loecher', 'y', 'tropfen', ts,
                    (wy0 - 1.0, yh + 1.0), d=w('m2_durchgang'), spitze=1.0,
                    kappe=w('m2_kappe')),
            schritt('weg', 'Muttertaschen', 'y', 'vieleck',
                    [sechseck(x, z, L['tasche_sw']) for x, z in ts],
                    (wy0 - 1.0, L['tasche_y'][1]))],
        # Maschinenkoordinaten: nach dem Verschieben abgezogen
        'Kamerahalter_Winkel': [
            schritt('dazu', 'Winkel_Aussparung', 'y', 'vieleck',
                    [[(xc - 2.0, zf0 - 2.0), (xi + 2.0, zf0 - 2.0),
                      (xi + 2.0, zf0 + xi + 2.0 - xc)]],
                    (q0 - 1.0, q1 + 1.0))]}
    sa_, ca_ = L['sin'], L['cos']
    L['maschine_nach_h'] = [[sa_, -ca_, 0.0, -lx * sa_ + ly * ca_],
                            [ca_, sa_, 0.0, -lx * ca_ - ly * sa_],
                            [0.0, 0.0, 1.0, 0.0]]

    # Bauraum in H (fuer die Pruefung des Koerpers vor dem Verschieben)
    punkte_h = ([(x, y, zf1) for x, y in L['fuss']]
                + [lokal(L, min(X, xc), Y) + (zf0,)
                   for X, Y in L['fuss_welt']]
                + ecken_quader(*L['steg'])
                + [k_nach_h(L, *p) for p in ecken_quader(
                    *L['wand'])]
                + [k_nach_h(L, *p) for x, z in L['loecher'] for p in
                   ecken_quader((x - pr, x + pr), (wy1, L['zapfen_y'][1]),
                                (z - pr * math.sqrt(2.0), z + pr))])
    bb = tuple((min(p[i] for p in punkte_h), max(p[i] for p in punkte_h))
               for i in range(3))
    # vor der Aussparung fuer den Eckwinkel (Fusion prueft vor dem Schnitt)
    roh = punkte_h + [(x, y, zf0) for x, y in L['fuss']]
    bb_roh = tuple((min(p[i] for p in roh), max(p[i] for p in roh))
                   for i in range(3))
    # Drucklage: Fuss bei z = 0, die Drehung um Z bleibt
    L['teile'] = {'Kamerahalter': {
        'bbox': bb, 'bbox_roh': bb_roh,
        'druck': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -zf0]],
        'auflage': ('z', zf0)}}

    # ---- Sicht: der Punkt im Rahmen K fuer jede Dicke ---------------------
    fpx = w('cam_f') / w('cam_pixel')
    L['f_px'] = fpx
    vx, vy = lokal(L, *mp)
    L['mp_lokal'] = (vx, vy)

    def im_bild(t):
        xk, yk, zk = h_nach_k(L, vx, vy, w('platte_z1') + t)
        return xk, yk, zk
    sicht = []
    for t in DICKEN + (w('werkstueck_max'),):
        xk, yk, zk = im_bild(t)
        sicht.append(dict(
            t=t, quer=math.degrees(math.atan2(xk, yk)),
            unter=math.degrees(math.atan2(-zk, yk)),
            abstand=math.sqrt(xk * xk + yk * yk + zk * zk),
            px_quer=fpx * xk / yk, px_hoch=fpx * zk / yk))
    L['sicht'] = sicht
    # Fester Fokus: die Linse wird auf den Abstand gedreht, bei dem die
    # Unschaerfe am naechsten und am weitesten Punkt gleich ist
    # (harmonisches Mittel). Zerstreuungskreis nach der Linsengleichung.
    a_n = min(x['abstand'] for x in sicht)
    a_w = max(x['abstand'] for x in sicht)
    af = 2.0 / (1.0 / a_n + 1.0 / a_w)
    L['fokus_auf'] = af
    f_ = w('cam_f')

    def bild(a):
        return f_ * a / (a - f_)
    for x in sicht:
        v = bild(x['abstand'])
        x['unschaerfe_px'] = (f_ / w('cam_blende') * abs(v - bild(af)) / v
                              / w('cam_pixel'))
    # Pixel je mm Hoehe: am ungunstigsten Ende des Bereichs
    def px(t):
        _, yk, zk = im_bild(t)
        return fpx * zk / yk
    L['px_je_mm'] = min(abs(px(t + 0.5) - px(t - 0.5))
                        for t in (0.5, w('werkstueck_max') - 0.5))
    # hochkant: quer zum Bild ist cam_px_h / cam_fov_h, hoch cam_px_b
    L['bild_halb'] = (w('cam_fov_h') / 2.0, w('cam_fov_b') / 2.0)
    L['bild_px_halb'] = (w('cam_px_h') / 2.0, w('cam_px_b') / 2.0)

    # ---- Kabel: Austritt, Weg zum Pi im Modell (nur Schaetzung) ------------
    # das steife Ende steht von der Kabelkante nach aussen ab
    ka = k_nach_maschine(L, L['kabel_aus'][0] - s * w('kabel_steif'),
                         L['kabel_aus'][1], 0.0)
    L['kabel_aus_welt'] = k_nach_maschine(L, *L['kabel_aus'])
    L['kabel_steif_welt'] = ka
    pb = (w('pi_buchse_x'), w('pi_buchse_y'), w('pi_buchse_z'))
    L['kabel_weg'] = (w('kabel_steif') + sum(abs(a - b) for a, b in
                                             zip(ka, pb)) + 20.0)

    # ---- Punkte an der Maschine (fuer Pruefung und Zeichnung) -------------
    L['kamera_teile'] = {
        'Platine': L['platine'], 'Stecker': L['stecker'],
        'Linsenblock': L['block'], 'Objektiv': L['tubus']}
    for i, k in enumerate(L['koepfe']):
        L['kamera_teile']['M2-Kopf {}'.format(i + 1)] = k
    zr = w('zapfen_d') / 2.0
    L['wand_teile'] = {
        'Wand': L['wand'],
        'Polster': ((min(xs) - pr, max(xs) + pr), L['pad_y'],
                    (-zo - pr * math.sqrt(2.0), zo + pr)),
        'Zapfen': ((min(x for x, _ in L['loecher_zapfen']) - zr,
                    max(x for x, _ in L['loecher_zapfen']) + zr),
                   L['zapfen_y'], (-zo - zr * math.sqrt(2.0), -zo + zr))}
    L['welt'] = {n: [k_nach_maschine(L, *p) for p in ecken_quader(*q)]
                 for n, q in list(L['kamera_teile'].items())
                 + list(L['wand_teile'].items())}
    L['welt']['Steg'] = [welt(L, x, y) + (z,)
                         for x, y, z in ecken_quader(*L['steg'])]
    L['welt']['Fuss'] = [(X, Y, z) for X, Y in L['fuss_welt']
                         for z in L['fuss_z']]
    alle = [p for n, ps in L['welt'].items() if n != 'Fuss' for p in ps]
    L['vorn_y'] = min(p[1] for p in alle)            # zum Arbeitsraum
    L['hinten_y'] = max(p[1] for p in alle)          # zum Fach
    L['rechts_x'] = max(p[0] for p in alle)
    # auf der Hoehe des Y-Riemens (mit Luft) darf es nur bis riemen_x0
    oben = [p for p in alle if p[2] > w('riemen_z0') - w('luft_bau')]
    L['rechts_x_riemen'] = max(p[0] for p in oben) if oben else None
    L['links_x'] = min(p[0] for p in alle)
    L['oben_z'] = max(p[2] for p in alle)

    # ---- Bohrlehre ----------------------------------------------------------
    L['lehre_z'] = w('platte_z1') - 60.0
    L['lehre_ursprung'] = (280.0, 230.0)     # rechts vor dem Fach, unter dem Tisch
    return L


# --- Materialien (Block unveraendert aus Elektronikfach.py) --------------------
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


# --- Geometrie-Helfer (wie Elektronikfach.py) ----------------------------------
def _offsetebene(comp, basis, ziel_cm, achse, name):
    """Offsetebene, deren Lage nachgemessen und bei falschem Vorzeichen
    korrigiert wird. `achse` ist die Modellachse, auf der die Ebene liegen
    soll."""
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


# --- Lokal -> Maschine: Drehung um Z, Verschiebung in X und Y -----------------
def verschiebung(L):
    """Matrix im Modell (Modell-Z = Maschine Y, Modell-Y = Maschine Z): die
    lokale x-Achse geht nach (sin, -cos), die lokale y-Achse nach
    (cos, sin), die Linsenfront nach L['linse']."""
    sa, ca = L['sin'], L['cos']
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(
        adsk.core.Point3D.create(L['linse'][0] / 10.0, 0.0,
                                 L['linse'][1] / 10.0),
        adsk.core.Vector3D.create(sa, 0.0, -ca),
        adsk.core.Vector3D.create(0.0, 1.0, 0.0),
        adsk.core.Vector3D.create(ca, 0.0, sa))
    return m


def _bewegen(comp, koerper, matrix):
    """Koerper mit einer Matrix bewegen (Move-Feature, bleibt im Verlauf)."""
    coll = adsk.core.ObjectCollection.create()
    for k in koerper:
        coll.add(k)
    mf = comp.features.moveFeatures
    try:
        ein = mf.createInput2(coll)
        ein.defineAsFreeMove(matrix)
    except AttributeError:
        ein = mf.createInput(coll, matrix)
    return mf.add(ein)


def verschieben(comp, koerper, L):
    """Koerper aus dem Rahmen H an ihren Platz an der Maschine."""
    return _bewegen(comp, koerper, verschiebung(L))


def kippung(L):
    """K -> H als Matrix im Modell. Beide Rahmen liegen im Modell wie
    Maschinenkoordinaten (Modell-Y = z, Modell-Z = y): x bleibt, z_K geht
    nach (y, z) = (sin, cos) der Neigung, y_K nach (cos, -sin); der
    Ursprung (Linsenfront) liegt in H auf der Hoehe linse_z."""
    sn, cn = L['sin_n'], L['cos_n']
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(
        adsk.core.Point3D.create(0.0, L['linse'][2] / 10.0, 0.0),
        adsk.core.Vector3D.create(1.0, 0.0, 0.0),
        adsk.core.Vector3D.create(0.0, cn, sn),
        adsk.core.Vector3D.create(0.0, -sn, cn))
    return m


def kippen(comp, koerper, L):
    """Koerper aus dem Rahmen K (Kamera, geneigt) in den Rahmen H."""
    return _bewegen(comp, koerper, kippung(L))


def vereinen(comp, ziel, werkzeuge, fehler, was):
    """werkzeuge mit ziel vereinen (Combine, Join)."""
    try:
        coll = adsk.core.ObjectCollection.create()
        for k in werkzeuge:
            coll.add(k)
        cf = comp.features.combineFeatures
        ein = cf.createInput(ziel, coll)
        ein.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        ein.isKeepToolBodies = False
        cf.add(ein)
    except Exception:
        fehler.append('{}: nicht vereint: {}'.format(
            was, traceback.format_exc().strip().splitlines()[-1]))


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
def bau_halter(app, design, comp, L, fehler):
    """Der Halter aus zwei Bauplaenen: Fuss, Steg und M5 im Rahmen H, die
    Wand mit dem Kamerasitz im Rahmen K. Die Wand wird gekippt und mit dem
    Rest vereint; dann Fussfase, Bauraum-Pruefung, an die Maschine
    verschieben, die Aussparung fuer den Eckwinkel abziehen, PETG."""
    T = L['teile']['Kamerahalter']
    k = plan_bauen(comp, L['plan']['Kamerahalter'], 'Kamerahalter', fehler)
    wand = plan_bauen(comp, L['plan']['Kamerahalter_Wand'],
                      'Kamerahalter_Wand', fehler)
    kippen(comp, [wand], L)
    vereinen(comp, k, [wand], fehler, 'Kamerahalter')
    fussfase(comp, k, 'y', T['auflage'][1], w('fase_fuss'), fehler,
             'Kamerahalter')
    bbox_pruefen(k, 'Kamerahalter (Rahmen H)', T['bbox_roh'], fehler)
    verschieben(comp, [k], L)
    try:
        _schritt_bauen(comp, L['plan']['Kamerahalter_Winkel'][0], 'weg', k)
    except Exception:
        fehler.append('Aussparung fuer den Eckwinkel: {}'.format(
            traceback.format_exc().strip().splitlines()[-1]))
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_bohrlehre(app, design, comp, L, fehler):
    """Lehre der Kamera, ausgeblendet (SKILL.md): Umriss der Platine, die
    vier Loecher, die Linsenmitte. u laengs der Kabelkante, v von der
    Gegenkante (v = 0) zur Kabelkante; liegt unter dem Tisch neben dem
    Fach."""
    try:
        u0, v0 = L['lehre_ursprung']
        b, h, r = w('cam_b'), w('cam_h'), w('cam_loch_rand')
        sk = skizze(comp, ebene_z(comp, L['lehre_z'], 'E_Bohrlehre_Kamera'),
                    'Sk_Bohrlehre_Kamera')
        rechteck(sk, u0, v0, u0 + b, v0 + h)
        for u in (r, b - r):
            for v in (r, r + w('cam_loch_ab')):
                kreis(sk, u0 + u, v0 + v, w('m2_durchgang'))
        kreis(sk, u0 + b / 2.0, v0 + h - w('cam_linse'), 1.5)
        k = neu_mittig(comp, groesstes_profil(sk),
                       w('lehre_dicke')).bodies.item(0)
        k.name = 'Bohrlehre_Kamera'
        material_zuweisen(app, design, k, 'PLA', fehler)
        k.isLightBulbOn = False
    except Exception:
        fehler.append('Bohrlehre_Kamera nicht gebaut: {}'.format(
            traceback.format_exc().strip().splitlines()[-1]))


def bau_referenz(app, design, teile, L, fehler):
    """Stueck des vorderen 2060 und das Ende des rechten 2040, die Kamera,
    Schrauben und Sichtlinien — nur zur Ansicht, NICHT drucken. Jedes Teil
    fuer sich: scheitert eines, steht das im Bericht."""
    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    pr = teile['Ref_Rahmen']
    rx = (L['fuss_x'][0] - 20.0, w('rahmen_x_innen') + w('rahmen_b') + 10.0)
    zr = (w('rahmen_z0') - w('quer_h'), w('rahmen_z0'))
    k = sicher('2060', bau_profil, pr, '2060_vorn', 'x', rx, L['quer_y'], zr)
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)
    xi = w('rahmen_x_innen')
    k = sicher('2040', bau_profil, pr, '2040_rechts', 'y',
               (L['quer_y'][0] - 20.0, L['quer_y'][1] + 35.0),
               (xi, xi + w('rahmen_b')), (zr[1], zr[1] + 2.0 * w('rahmen_b')))
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)

    def quader_neu(comp, name, x, y, z):
        kk = quader(comp, name, x, y, z, 'neu').bodies.item(0)
        kk.name = name
        return kk

    # Kamera im Rahmen K, dann gekippt und wie der Halter verschoben
    kc = teile['Ref_Kamera']
    koerper = []
    for name, q in L['kamera_teile'].items():
        mat = 'Leiterplatte' if name == 'Platine' else (
            'Steel' if name.startswith('M2') else 'Kunststoff')
        k = sicher(name, quader_neu, kc, name.replace(' ', '_').replace(
            '-', '_'), *q)
        if k:
            material_zuweisen(app, design, k, mat, fehler)
            koerper.append(k)
    if koerper:
        sicher('Kamera kippen', kippen, kc, koerper, L)
        sicher('Kamera verschieben', verschieben, kc, koerper, L)

    # M5 mit Kopf auf dem Fuss
    sr = teile['Ref_Schrauben']
    zf1 = L['fuss_z'][1]
    for i, (x, y) in enumerate(L['m5_welt']):
        rk = w('m5_kopf_d') / 2.0
        k = sicher('M5 Kopf', quader_neu, sr, 'M5_Kopf_{}'.format(i + 1),
                   (x - rk, x + rk), (y - rk, y + rk),
                   (zf1, zf1 + w('m5_kopf_h')))
        if k:
            material_zuweisen(app, design, k, 'Steel', fehler)

    # Sichtlinien Linse -> Messpunkt fuer die duennste und dickste Platte
    def linien():
        sk = skizze(sr, sr.xZConstructionPlane, 'Sk_Sichtlinien')
        lx, ly, lz = L['linse']
        p0 = sk.modelToSketchSpace(adsk.core.Point3D.create(
            lx / 10.0, lz / 10.0, ly / 10.0))
        for t in (0.0, w('werkstueck_max')):
            p1 = sk.modelToSketchSpace(adsk.core.Point3D.create(
                L['mp'][0] / 10.0, (w('platte_z1') + t) / 10.0,
                L['mp'][1] / 10.0))
            sk.sketchCurves.sketchLines.addByTwoPoints(p0, p1)
        return sk
    sicher('Sichtlinien', linien)


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/kamerahalter_check.py)."""
    lx, ly, lz = L['linse']
    s0, s1 = L['sicht'][0], L['sicht'][-1]
    m5 = L['m5_welt']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py (Y nach vorn, Z senkrecht,',
        '  Z = 0 Mitte Portalrohr). Im Modell sind Y und Z getauscht.',
        '',
        'ZWECK: Autofokus. Kopf an den Messpunkt, Z oben, Laser kurz und',
        '  schwach an; die Kamera sieht den Punkt je nach Dicke hoeher oder',
        '  tiefer. Ein Bild ergibt die Hoehe, Z faehrt auf den Fokus.',
        '',
        'MESSPUNKT: {:.0f} mm links, {:.0f} mm hinter der Innenecke des'
        .format(w('mp_links'), w('mp_hinten')),
        '  Anschlags vorn rechts (X {:+.1f}, Y {:+.1f}); mit dem Nullpunkt in'
        .format(*L['mp']),
        '  der Ecke G54 X-{:.0f} Y+{:.0f} (Y+ zeigt bei GRBL nach hinten).'
        .format(w('mp_links'), w('mp_hinten')),
        '  Dort darf nichts aufs Werkstueck.',
        '',
        'KAMERA: Raspberry Pi Kamera v1.3 (OV5647, wie verbaut), hochkant,',
        '  Kabelkante zum Fach. Linse X {:+.1f}, Y {:+.1f}, Z {:+.1f},'
        .format(lx, ly, lz),
        '  {:.0f} mm vom rechten 2040. Blick {:.1f} Grad gegen +X (schraeg'
        .format(w('rahmen_x_innen') - lx, L['blick_az']),
        '  nach hinten links), {:.1f} Grad nach unten geneigt.'.format(
            L['neige']),
        '  Punkt {:.1f} Grad neben der Achse (Bild +-{:.1f}), {:+.1f} bis'
        .format(abs(s0['quer']), L['bild_halb'][0], -s0['unter']),
        '  {:+.1f} Grad ueber der Achse (Bild +-{:.1f}), {:.0f} bis {:.0f} mm'
        .format(-s1['unter'], L['bild_halb'][1], s1['abstand'],
                s0['abstand']),
        '  weit. Mindestens {:.1f} Pixel je mm Hoehe.'.format(
            L['px_je_mm']),
        '  FOKUS: fest ab Werk (1 m bis unendlich). Linse auf {:.0f} mm'
        .format(L['fokus_auf']),
        '  drehen, dann hoechstens {:.1f} Pixel Unschaerfe.'.format(
            max(x['unschaerfe_px'] for x in L['sicht'])),
        '',
        'LUFT: vorn bis Y {:+.1f} (nur rechts von X {:+.1f}, der Laser kommt'
        .format(L['vorn_y'], w('laser_x1') + w('luft_bau')),
        '  bis X {:+.1f}); hinten bis Y {:+.1f}, das Fach bei {:+.1f}; rechts'
        .format(w('laser_x1'), L['hinten_y'], w('fach_y0')),
        '  bis X {:+.1f}, auf der Hoehe des Y-Riemens bis {:+.1f} (Riemen'
        .format(L['rechts_x'], L['rechts_x_riemen']),
        '  bei {:+.1f}).'.format(w('riemen_x0')),
        '',
        'DRUCK: PETG, Fuss aufs Bett, keine Stuetzen. Die Wand lehnt {:.0f}'
        .format(L['neige']),
        '  Grad nach vorn. Polster, Zapfen und Loecher als Traene,',
        '  Muttertaschen als Sechseck mit Ecke oben (im geneigten Rahmen).',
        'ECKWINKEL: Innen am rechten 2040 sitzt ein Winkel in der Nut. Fuss',
        '  und Steg sind darueber unter 45 Grad ausgespart ({:.0f} mm Luft zur'
        .format(w('winkel_luft')),
        '  Huelle {:.0f} x {:.0f}); der Fuss endet oben bei X {:+.1f}. Schenkel'
        .format(w('winkel_l'), w('winkel_l'), L['fuss_x'][1]),
        '  nicht gemessen [?]: vor dem Druck am Aufbau nachsehen.',
        'MONTAGE: 1. 2 Hammermuttern M5 in die Nut oben auf dem vorderen',
        '  2060, Halter mit 2 x M5x{:.0f} bei X {:+.0f} / {:+.0f} (Inbus von'
        .format(w('m5_l'), m5[0][0], m5[1][0]),
        '  oben, geht auch mit eingesetzter Kamera).',
        '  2. zwei Muttern M2 in die Taschen hinter der Wand (oben).',
        '  3. Kamera unten auf die Zapfen, oben 2 x M2x{:.0f}; Kabel'
        .format(w('m2_l')),
        '  einstecken und ueber das 2060 ins Fach zum Pi fuehren.',
        '  Im Modell {:.0f} mm bis zur Buchse; am Aufbau liegt der Pi'
        .format(L['kabel_weg']),
        '  anders, dort reicht das {:.0f}-mm-Kabel (Angabe).'.format(
            w('kabel_l')),
        '',
        'NICHT GEMESSEN [w]/[?]: Kamera nach Massblatt und Foto, Hoehe des',
        '  Linsenblocks geschaetzt (Bohrlehre_Kamera),',
        '  Lage der Kamerabuchse am Pi, Elektronikfach (Zwischenstand).',
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
            einheit = EINHEIT.get(name, 'mm')
            text = '{} {}'.format(wert, einheit) if einheit else repr(wert)
            if up.itemByName(name) is None:
                up.add(name, adsk.core.ValueInput.createByString(text),
                       einheit, kommentar)

        L = lage()

        # Baugruppe: alle Komponenten am globalen Ursprung, jedes Teil steht
        # schon an seinem Platz; nichts bewegt sich, alles fixiert.
        einheit = adsk.core.Matrix3D.create()
        occ = {}
        for name in ('Kamerahalter', 'Bohrlehren'):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o
        bau_halter(app, design, occ['Kamerahalter'].component, L, fehler)
        bau_bohrlehre(app, design, occ['Bohrlehren'].component, L, fehler)
        for o in occ.values():
            o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Rahmen', 'Ref_Kamera', 'Ref_Schrauben'):
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
