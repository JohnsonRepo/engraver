# Kamerahalter.py — Halter fuer das Raspberry Pi Camera Module 3 auf dem
# hinteren 2060, direkt vor dem Elektronikfach
#
# Wozu: Autofokus ueber Z. Der Kopf faehrt an einen festen Messpunkt kurz
# innerhalb der Anschlagecke (Spannmittel.py), Z ganz oben, und schaltet den
# Laser kurz und schwach ein. Der Strahl steht senkrecht, der Punkt liegt
# also bei jeder Werkstueckdicke an derselben Stelle. Die Kamera sieht ihn
# von hinten rechts, je nach Dicke hoeher oder tiefer im Bild: ein Bild
# ergibt die Hoehe der Oberflaeche, Z faehrt auf den Fokus. Das Kabel zum
# Pi ist kurz, weil die Kamera direkt vor dem Fach sitzt.
#
# Ein Druckteil, dazu Lehre und Referenzteile:
#   Kamerahalter  Fuss auf der Oberseite des hinteren 2060, 2 x M5x10 in
#                 Hammermuttern der Nut; darauf eine senkrechte Wand, zur
#                 Ecke gedreht, mit einer Rippe dahinter. Vier Polster
#                 tragen die Kamera hochkant: an der Kabelseite 2 x M2x8 mit
#                 Mutter in Taschen hinter der Wand, vorn 2 Zapfen durch die
#                 Loecher (Schraubenkoepfe waeren dort der vorderste Punkt
#                 und kosteten 1,5 mm Luft zur Traegerplatte). Die
#                 Kabelkante zeigt nach hinten links zum Fach.
#   Bohrlehre_Kamera  ausgeblendet: Umriss und Lochbild des Camera Module 3
#                 zum Auflegen auf die Platine, bevor der Halter gedruckt
#                 wird.
#   Referenz_nicht_drucken  Stueck des hinteren 2060, Vorderwand und Deckel
#                 des Elektronikfachs (Ausschnitt), die Kamera, Schrauben und
#                 die Sichtlinien zum Messpunkt.
#
# Warum hochkant und ohne Neigung: Quer (41 Grad Bildwinkel senkrecht)
# muesste die Kamera rund 17 Grad nach unten kippen; dann haengen Polster
# und Wand ueber, und der Halter braucht Stuetzen. Hochkant sind es 66 Grad
# senkrecht, der Punkt liegt 8 bis 27 Grad unter der Achse, und die Wand
# steht senkrecht. Hochkant ist die Kamera ausserdem schmal genug fuer den
# Streifen zwischen Fach und Traegerplatte: Am Ende des Y-Wegs faehrt die
# Traegerplatte bis luft_bau an ihre Vorderkante heran.
#
# Drucklage: Fuss aufs Bett, die Wand steht senkrecht. Polster als Traene mit
# der Spitze unten, Loecher fuer die M2 als Traene mit der Spitze oben,
# Muttertaschen als Sechseck mit einer Ecke oben, Rippe mit 45 Grad. Keine
# Stuetzen.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: X nach rechts, Y nach
# vorn, Z senkrecht, Z = 0 in der Mitte des Portalrohrs. Im Fusion-Modell
# sind Y und Z getauscht (Modell-Z = Maschine Y). Der Bauplan steht in einem
# eigenen Rahmen, in dem die Wand achsparallel liegt ("lokal"): x laengs der
# Platine (Kabelkante bei x < 0), y in Blickrichtung (Linsenfront bei
# y = 0), z = Maschine Z. Der fertige Koerper wird um Z gedreht und an
# seinen Platz geschoben. tools/stl_export.py fuehrt denselben Bauplan aus;
# fuer den Druck ist die Drehung um Z gleichgueltig. Pruefung:
# tools/kamerahalter_check.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback
import math

SKRIPT_NAME = 'Kamerahalter'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog). Winkel in Grad und
# Pixelzahlen stehen in EINHEIT.
MASSE = {
    # --- Rahmen (wie Portal.py und Elektronikfach.py) [v] -------------------
    'quer_y1':           (-250.0, 'hinteres 2060: Rueckseite (Maschine Y)'),
    'rahmen_b':            (20.0, 'Profil: Breite (2060 hochkant: in Y)'),
    'quer_h':              (60.0, 'hinteres 2060: Hoehe'),
    'rahmen_z0':          (-69.0, 'Oberseite des 2060 = Unterkante der 2040'),
    # Nut 6 [w], wie Kabelhalter.py
    'nut_lippe':            (1.8, 'Nut 6: Dicke der Lippe'),
    'nut_tiefe':            (6.0, 'Nut 6: Platz ab Profilflaeche bis zum Nutgrund'),
    'nutenstein_h':         (4.0, 'Hammermutter M5: Gewindelaenge'),
    # V-Slot vereinfacht (nur Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),

    # --- Elektronikfach (Elektronikfach.py Rev. 1, Zwischenstand) [v] -------
    'fach_vorn_y':       (-253.0, 'Fach: Aussenseite der Vorderwand'),
    'fach_wand':            (2.0, 'Fach: Vorderwand (Montageplatte), Dicke'),
    'fach_rand_z':        (-50.0, 'Fach: Oberkante der Waende'),
    'deckel_z1':          (-47.5, 'Fach: Oberseite des Deckels'),
    'fach_boden_z':      (-127.0, 'Fach: Unterseite'),
    # Kamerabuchse des Pi: vordere Schmalseite (die SD-Karte ist hinten),
    # Mitte; X auf der Bauteilseite [?]
    'pi_buchse_x':        (-10.5, 'Pi: Kamerabuchse, Maschine X'),
    'pi_buchse_y':       (-275.0, 'Pi: Kamerabuchse, Maschine Y'),
    'pi_buchse_z':        (-73.0, 'Pi: Kamerabuchse, Maschine Z'),

    # --- was hinten herankommt (tools/kamerahalter_check.py rechnet nach) --
    # Traegerplatte am Schienenende des Y-Wegs, ab ihrer Unterkante
    'th_hinten_y':       (-227.3, 'Toolhead: hinterste Lage der Traegerplatte'),
    'th_hinten_z':        (-66.0, 'Toolhead: Unterkante der Traegerplatte'),
    'xwagen_hinten_y':   (-243.3, 'X-Wagen: hinterste Lage'),
    'xwagen_z0':          (-16.0, 'X-Wagen: Unterkante'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),

    # --- Messpunkt (Spannmittel.py, Opferplatte.py) [v] ---------------------
    'ecke_x':           (-199.85, 'Anschlagwinkel: Innenecke, Maschine X'),
    'ecke_y':           (-164.80, 'Anschlagwinkel: Innenecke, Maschine Y'),
    # 30/35 statt dicht an der Ecke: so liegt der Punkt fuer jede Dicke
    # mindestens 6 Grad im Bild (siehe Pruefung, Abschnitt Sicht)
    'mp_rechts':           (30.0, 'Messpunkt: so weit rechts der Innenecke'),
    'mp_vorn':             (35.0, 'Messpunkt: so weit vor der Innenecke'),
    'platte_z1':         (-129.0, 'Oberseite der Opferplatte'),
    'werkstueck_max':      (58.0, 'dickstes Werkstueck unter dem Toolhead'),

    # --- Camera Module 3, Normalobjektiv [w] -----------------------------
    # Massblatt RP-008153 (Raspberry Pi, 2023) und Datenblatt; Bohrlehre
    # an die Platine halten, bevor der Halter gedruckt wird.
    'cam_b':               (25.0, 'Kamera: Platine, Breite (laengs der Kabelkante)'),
    'cam_h':             (23.862, 'Kamera: Platine, Hoehe (quer zur Kabelkante)'),
    'cam_pcb':             (1.12, 'Kamera: Platinendicke'),
    'cam_linse':          (9.462, 'Kamera: Linsenmitte ab der Kabelkante'),
    'cam_front':           (7.43, 'Kamera: Linsenfront vor der Platine (6,98 + 0,45)'),
    'cam_block':           (10.8, 'Kamera: Linsenblock, Kantenlaenge'),
    'cam_block_t':        (4.325, 'Kamera: Linsenblock mit Abstand, Dicke'),
    'cam_tubus_d':         (5.75, 'Kamera: Objektiv, Durchmesser'),
    'cam_loch_d':           (2.2, 'Kamera: Befestigungsloecher'),
    'cam_loch_rand':        (2.0, 'Kamera: Loecher ab Gegenkante und Seiten'),
    'cam_loch_ab':         (12.5, 'Kamera: Lochabstand quer zur Kabelkante'),
    'cam_pad_frei':        (4.75, 'Kamera: freier Ring um die Loecher'),
    'cam_stecker_b':      (19.61, 'Kamera: Stecker hinten, Breite'),
    'cam_stecker_h':       (5.71, 'Kamera: Stecker, Tiefe ab der Kabelkante'),
    'cam_stecker_t':       (2.75, 'Kamera: Stecker, Hoehe ueber der Rueckseite'),
    'cam_f':               (4.74, 'Kamera: Brennweite'),
    'cam_pixel':         (0.0014, 'Kamera: Pixelgroesse'),
    'cam_px_b':          (4608.0, 'Kamera: Pixel laengs der Kabelkante'),
    'cam_px_h':          (2592.0, 'Kamera: Pixel quer zur Kabelkante'),
    'cam_fov_b':           (66.0, 'Kamera: Bildwinkel laengs der Kabelkante'),
    'cam_fov_h':           (41.0, 'Kamera: Bildwinkel quer zur Kabelkante'),
    'cam_fokus':          (100.0, 'Kamera: naechster Fokus'),
    'kabel_l':            (200.0, 'Kamerakabel Standard-Mini: Laenge'),
    'kabel_b':             (16.0, 'Kamerakabel: Breite an der Kamera'),
    'kabel_steif':          (3.0, 'Kamerakabel: steifes Ende vor der Kabelkante'),

    # --- Lage der Kamera -------------------------------------------------------
    'blick_az':           (130.0, 'Kamera: Blickrichtung in Grad gegen +X, von oben gegen den Uhrzeigersinn'),
    'linse_x':            (-40.0, 'Kamera: Linsenfront, Maschine X'),
    'linse_z':            (-47.5, 'Kamera: Linsenmitte, Maschine Z'),

    # --- Halter ------------------------------------------------------------------
    # Rev. 1: erster Stand.
    'fuss_t':               (4.5, 'Fuss: Dicke (M5x10: 5,5 in der Nut, 3,7 im Stein)'),
    'fuss_hinten':          (0.5, 'Fuss: so weit vor der Rueckseite des 2060'),
    'fuss_vorn':            (1.0, 'Fuss: so weit hinter der Vorderseite des 2060'),
    'fuss_rand':            (6.0, 'Fuss: reicht so weit ueber die Mitte der M5'),
    'm5_links':           (-50.0, 'Fuss: linke M5, Maschine X'),
    'm5_rechts':          (-10.0, 'Fuss: rechte M5, Maschine X'),
    'wand_t':               (4.0, 'Wand: Dicke'),
    'pad_h':                (2.0, 'Polster: Hoehe (Platz fuer die Bauteile hinten)'),
    'pad_d':                (4.5, 'Polster: Durchmesser der Traene'),
    'wand_rand':            (1.0, 'Wand: reicht so weit ueber die Polster'),
    'wand_oben':            (1.0, 'Wand: endet so weit ueber der Platine'),
    'stecker_luft':         (0.5, 'Wand: endet so weit vor dem Stecker'),
    'rippe_x':              (6.5, 'Rippe hinter der Wand: Mitte (lokal x)'),
    'rippe_b':              (4.0, 'Rippe: Dicke'),
    'rippe_l':              (7.0, 'Rippe: Laenge am Fuss und Hoehe an der Wand'),
    # Zapfen in den vorderen Loechern (Ø2,2): Traene mit der Spitze unten,
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
EINHEIT = {'blick_az': 'deg', 'cam_fov_b': 'deg', 'cam_fov_h': 'deg',
           'cam_px_b': '', 'cam_px_h': ''}

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


# --- Rahmen lokal <-> Maschine ------------------------------------------------
def welt(L, x, y):
    """Lokal (x, y) -> Maschine (X, Y); z bleibt."""
    return (L['linse'][0] + x * L['sin'] + y * L['cos'],
            L['linse'][1] - x * L['cos'] + y * L['sin'])


def lokal(L, X, Y):
    """Maschine (X, Y) -> lokal (x, y)."""
    dx, dy = X - L['linse'][0], Y - L['linse'][1]
    return (dx * L['sin'] - dy * L['cos'], dx * L['cos'] + dy * L['sin'])


def ecken_quader(x, y, z):
    return [(a, b, c) for a in x for b in y for c in z]


def lage():
    """Alle Lagen (mm) und der Bauplan. Einzige Quelle fuer Geometrie, STL,
    Zeichnung und Pruefung (tools/kamerahalter_check.py, stl_export.py,
    kamerahalter_zeichnen.py)."""
    L = {}
    A = math.radians(w('blick_az'))
    L['sin'], L['cos'] = math.sin(A), math.cos(A)
    zl = w('linse_z')

    # ---- Kamera im lokalen Rahmen: Linsenfront bei (0, 0), hochkant ------
    kab = -w('cam_linse')                          # Kabelkante
    geg = w('cam_h') - w('cam_linse')              # Gegenkante
    hz = w('cam_b') / 2.0                           # halbe Hoehe
    yv = -w('cam_front')                            # Platine vorn
    yh = yv - w('cam_pcb')                          # Platine hinten
    ys = yh - w('cam_stecker_t')                    # Stecker hinten
    L['platine'] = ((kab, geg), (yh, yv), (zl - hz, zl + hz))
    L['stecker'] = ((kab, kab + w('cam_stecker_h')), (ys, yh),
                    (zl - w('cam_stecker_b') / 2.0,
                     zl + w('cam_stecker_b') / 2.0))
    bk = w('cam_block') / 2.0
    yb = yv + w('cam_block_t')
    L['block'] = ((-bk, bk), (yv, yb), (zl - bk, zl + bk))
    tr = w('cam_tubus_d') / 2.0
    L['tubus'] = ((-tr, tr), (yb, 0.0), (zl - tr, zl + tr))
    # Loecher: das Paar an der Kabelseite traegt die Schrauben, das vordere
    # (an der Gegenkante) die Zapfen
    xz = geg - w('cam_loch_rand')
    xs_ = xz - w('cam_loch_ab')
    zz = [zl + s * (hz - w('cam_loch_rand')) for s in (-1, 1)]
    L['loecher_schraube'] = [(xs_, z) for z in zz]
    L['loecher_zapfen'] = [(xz, z) for z in zz]
    L['loecher'] = L['loecher_schraube'] + L['loecher_zapfen']
    rk = w('m2_kopf_d') / 2.0
    L['koepfe'] = [((x - rk, x + rk), (yv, yv + w('m2_kopf_h')),
                    (z - rk, z + rk)) for x, z in L['loecher_schraube']]
    L['zapfen_y'] = (yh - 0.5, yv + w('zapfen_ueber'))
    L['kabel_aus'] = (kab, (yh + ys) / 2.0, zl)

    # ---- Halter im lokalen Rahmen ---------------------------------------
    zf0 = w('rahmen_z0')
    zf1 = zf0 + w('fuss_t')
    wy1 = yh - w('pad_h')                           # Wand vorn
    wy0 = wy1 - w('wand_t')                         # Wand hinten
    xs = [x for x, _ in L['loecher']]
    pr = w('pad_d') / 2.0
    wx0 = L['stecker'][0][1] + w('stecker_luft')
    wx1 = max(xs) + pr + w('wand_rand')
    wz1 = zl + hz + w('wand_oben')
    L['wand'] = ((wx0, wx1), (wy0, wy1), (zf1, wz1))
    L['fuss_z'] = (zf0, zf1)
    L['pad_y'] = (wy1, yh)
    L['pad_kappe'] = max(0.0, w('cam_pad_frei') / 2.0 - pr)
    rb, rl = w('rippe_b') / 2.0, w('rippe_l')
    L['rippe'] = ((w('rippe_x') - rb, w('rippe_x') + rb),
                  [(wy0, zf1), (wy0 - rl, zf1), (wy0, zf1 + rl)])
    tasche = w('m2_mutter_h') + w('mutter_spiel')
    L['tasche_y'] = (wy0, wy0 + tasche)
    L['tasche_sw'] = w('m2_mutter_sw') + w('mutter_spiel')

    # ---- Linse in Y so weit vorn, dass die Traegerplatte luft_bau bleibt --
    # Alle Punkte von Kamera und Wand ueber der Unterkante der
    # Traegerplatte; der Fuss liegt fest im Maschinenrahmen.
    zr = w('zapfen_d') / 2.0
    punkte = (ecken_quader(*L['platine'][:2], (0.0,))
              + ecken_quader(*L['stecker'][:2], (0.0,))
              + ecken_quader(*L['block'][:2], (0.0,))
              + ecken_quader((-tr, tr), (yb, 0.0), (0.0,))
              + [p for k in L['koepfe'] for p in ecken_quader(*k[:2], (0.0,))]
              + [p for x, _ in L['loecher_zapfen']
                 for p in ecken_quader((x - zr, x + zr), L['zapfen_y'],
                                       (0.0,))]
              + ecken_quader(*L['wand'][:2], (0.0,)))
    vorn = max(-x * L['cos'] + y * L['sin'] for x, y, _ in punkte)
    ly = w('th_hinten_y') - w('luft_bau') - vorn
    L['linse'] = (w('linse_x'), ly, zl)

    # ---- Fuss: im Maschinenrahmen auf der Oberseite des 2060 -------------
    q0, q1 = w('quer_y1'), w('quer_y1') + w('rahmen_b')
    fx = (w('m5_links') - w('fuss_rand'), w('m5_rechts') + w('fuss_rand'))
    fy = (q0 + w('fuss_hinten'), q1 - w('fuss_vorn'))
    L['quer_y'] = (q0, q1)
    L['nut_y'] = (q0 + q1) / 2.0
    L['fuss_x'], L['fuss_y'] = fx, fy
    L['fuss_welt'] = [(fx[0], fy[0]), (fx[1], fy[0]), (fx[1], fy[1]),
                      (fx[0], fy[1])]
    L['fuss'] = [lokal(L, X, Y) for X, Y in L['fuss_welt']]
    L['m5_welt'] = [(w('m5_links'), L['nut_y']), (w('m5_rechts'), L['nut_y'])]
    L['m5'] = [lokal(L, X, Y) for X, Y in L['m5_welt']]
    # M5x10: Kopf auf dem Fuss, Rest in der Nut
    L['m5_in_nut'] = w('m5_l') - w('fuss_t')
    L['m5_eingriff'] = (min(L['m5_in_nut'], w('nut_lippe')
                            + w('nutenstein_h')) - w('nut_lippe'))
    # M2x8: Kopf auf der Platine, Mutter in der Tasche
    L['m2_stapel'] = w('cam_pcb') + w('pad_h') + w('wand_t')
    L['m2_bis_mutter'] = L['m2_stapel'] - tasche + w('m2_mutter_h')
    L['m2_rest'] = w('m2_l') - L['m2_bis_mutter']

    # ---- Bauplan des Kamerahalters (lokal) -------------------------------
    tz = list(L['loecher'])
    ts = list(L['loecher_schraube'])
    L['plan'] = {'Kamerahalter': [
        schritt('dazu', 'Fuss', 'z', 'vieleck', [L['fuss']], (zf0, zf1)),
        quader_schritt('dazu', 'Wand', L['wand'][0], L['wand'][1],
                       L['wand'][2]),
        schritt('dazu', 'Rippe', 'x', 'vieleck', [L['rippe'][1]],
                L['rippe'][0]),
        schritt('dazu', 'Polster', 'y', 'tropfen', tz, L['pad_y'],
                d=w('pad_d'), spitze=-1.0, kappe=L['pad_kappe']),
        schritt('dazu', 'Zapfen', 'y', 'tropfen', L['loecher_zapfen'],
                L['zapfen_y'], d=w('zapfen_d'), spitze=-1.0,
                kappe=w('zapfen_kappe')),
        schritt('weg', 'M2_Loecher', 'y', 'tropfen', ts,
                (wy0 - 1.0, yh + 1.0), d=w('m2_durchgang'), spitze=1.0,
                kappe=w('m2_kappe')),
        schritt('weg', 'Muttertaschen', 'y', 'vieleck',
                [sechseck(x, z, L['tasche_sw']) for x, z in ts],
                (wy0 - 1.0, L['tasche_y'][1])),
        schritt('weg', 'M5_Loecher', 'z', 'kreis', L['m5'],
                (zf0 - 1.0, zf1 + 1.0), d=w('m5_durchgang')),
    ]}
    xs_f = [p[0] for p in L['fuss']]
    ys_f = [p[1] for p in L['fuss']]
    bb = ((min(min(xs_f), wx0), max(max(xs_f), wx1)),
          (min(min(ys_f), wy0 - rl), max(max(ys_f), L['zapfen_y'][1])),
          (zf0, wz1))
    # Drucklage: Fuss bei z = 0, die Drehung um Z bleibt
    L['teile'] = {'Kamerahalter': {
        'bbox': bb,
        'druck': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -zf0]],
        'auflage': ('z', zf0)}}

    # ---- Messpunkt und Sicht ----------------------------------------------
    mp = (w('ecke_x') + w('mp_rechts'), w('ecke_y') + w('mp_vorn'))
    L['mp'] = mp
    fpx = w('cam_f') / w('cam_pixel')
    L['f_px'] = fpx
    vx, vy = lokal(L, *mp)                    # vy = Abstand laengs der Achse
    L['mp_lokal'] = (vx, vy)
    sicht = []
    for t in DICKEN + (w('werkstueck_max'),):
        dz = (w('platte_z1') + t) - zl
        sicht.append(dict(
            t=t, quer=math.degrees(math.atan2(vx, vy)),
            unter=math.degrees(math.atan2(-dz, vy)),
            abstand=math.sqrt(vx * vx + vy * vy + dz * dz),
            px_quer=fpx * vx / vy, px_hoch=fpx * -dz / vy))
    L['sicht'] = sicht
    L['px_je_mm'] = fpx / vy                  # senkrecht: konstant
    # hochkant: quer zum Bild ist cam_px_h / cam_fov_h, hoch cam_px_b
    L['bild_halb'] = (w('cam_fov_h') / 2.0, w('cam_fov_b') / 2.0)
    L['bild_px_halb'] = (w('cam_px_h') / 2.0, w('cam_px_b') / 2.0)

    # ---- Kabel: Austritt, Weg zum Pi (Schaetzung) ---------------------------
    # Das Kabel tritt nach hinten links aus, laeuft aussen an der Vorderwand
    # des Fachs nach links bis neben den Fuss, dort ueber die Oberkante der
    # Wand unter den Deckel, innen hinunter in die Signalgasse und darin
    # nach rechts zur Buchse des Pi.
    ax, ay = welt(L, L['kabel_aus'][0], L['kabel_aus'][1])
    L['kabel_aus_welt'] = (ax, ay, zl)
    L['kabel_wand'] = ay - w('fach_vorn_y')
    sx, sy = welt(L, L['kabel_aus'][0] - w('kabel_steif'),
                  L['kabel_aus'][1])
    L['kabel_steif_welt'] = (sx, sy, zl)
    L['kabel_steif_wand'] = sy - w('fach_vorn_y')
    L['kabel_eintritt_x'] = fx[0] - 5.0
    innen = w('fach_vorn_y') - w('fach_wand')
    weg = [w('kabel_steif'),
           abs(sx - L['kabel_eintritt_x']),            # aussen nach links
           abs(zl - w('fach_rand_z')) + 5.0,           # zur Oberkante
           w('fach_wand') + 2.0,                       # ueber die Wand
           w('fach_rand_z') - w('pi_buchse_z'),        # innen hinunter
           abs(L['kabel_eintritt_x'] - w('pi_buchse_x')),  # in der Gasse
           abs(innen - w('pi_buchse_y')),              # zur Buchse
           20.0]                                       # Falten
    L['kabel_weg'] = sum(weg)

    # ---- Punkte im Maschinenrahmen (fuer Pruefung und Zeichnung) -----------
    def quader_welt(q):
        return [welt(L, x, y) + (z,) for x, y, z in ecken_quader(*q)]
    L['kamera_teile'] = {
        'Platine': L['platine'], 'Stecker': L['stecker'],
        'Linsenblock': L['block'], 'Objektiv': L['tubus']}
    for i, k in enumerate(L['koepfe']):
        L['kamera_teile']['M2-Kopf {}'.format(i + 1)] = k
    L['halter_teile'] = {
        'Wand': L['wand'],
        'Rippe': (L['rippe'][0], (wy0 - rl, wy0), (zf1, zf1 + rl)),
        'Polster': ((min(xs) - pr, max(xs) + pr), L['pad_y'],
                    (min(z for _, z in tz) - pr * math.sqrt(2.0),
                     max(z for _, z in tz) + pr)),
        'Zapfen': ((L['loecher_zapfen'][0][0] - zr,
                    L['loecher_zapfen'][0][0] + zr), L['zapfen_y'],
                   (min(z for _, z in tz) - zr * math.sqrt(2.0),
                    max(z for _, z in tz) + zr))}
    L['welt'] = {n: quader_welt(q) for n, q in
                 list(L['kamera_teile'].items())
                 + list(L['halter_teile'].items())}
    L['welt']['Fuss'] = [(X, Y, z) for X, Y in L['fuss_welt']
                         for z in L['fuss_z']]
    alle = [p for n, ps in L['welt'].items() if n != 'Fuss' for p in ps]
    L['vorn_y'] = max(p[1] for p in alle)
    L['hinten_y'] = min(p[1] for p in alle)
    L['oben_z'] = max(p[2] for p in alle)

    # ---- Bohrlehre und Referenzen ------------------------------------------
    L['lehre_z'] = w('platte_z1') - 60.0
    L['lehre_ursprung'] = (40.0, -275.0)     # neben dem Fach, unter dem Tisch
    L['ref_x'] = (fx[0] - 20.0, fx[1] + 20.0)
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


def verschieben(comp, koerper, L):
    """Koerper aus dem lokalen Rahmen an ihren Platz (Move-Feature, bleibt
    im Verlauf)."""
    coll = adsk.core.ObjectCollection.create()
    for k in koerper:
        coll.add(k)
    mf = comp.features.moveFeatures
    try:
        ein = mf.createInput2(coll)
        ein.defineAsFreeMove(verschiebung(L))
    except AttributeError:
        ein = mf.createInput(coll, verschiebung(L))
    return mf.add(ein)


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
    """Der Halter aus dem Bauplan, lokal gebaut, dann gedreht und
    verschoben; Fussfase, Bauraum-Pruefung, PETG."""
    T = L['teile']['Kamerahalter']
    k = plan_bauen(comp, L['plan']['Kamerahalter'], 'Kamerahalter', fehler)
    fussfase(comp, k, 'y', T['auflage'][1], w('fase_fuss'), fehler,
             'Kamerahalter')
    bbox_pruefen(k, 'Kamerahalter (lokal)', T['bbox'], fehler)
    verschieben(comp, [k], L)
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
    """Hinteres 2060, Ausschnitt des Elektronikfachs, die Kamera, Schrauben
    und Sichtlinien — nur zur Ansicht, NICHT drucken. Jedes Teil fuer sich:
    scheitert eines, steht das im Bericht."""
    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    rx = L['ref_x']
    pr = teile['Ref_Rahmen']
    zr = (w('rahmen_z0') - w('quer_h'), w('rahmen_z0'))
    k = sicher('2060', bau_profil, pr, '2060_hinten', 'x', rx,
               L['quer_y'], zr)
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)

    def quader_neu(comp, name, x, y, z):
        kk = quader(comp, name, x, y, z, 'neu').bodies.item(0)
        kk.name = name
        return kk

    fv = w('fach_vorn_y')
    for name, y, z in (
            ('Fach_Vorderwand', (fv - w('fach_wand'), fv),
             (w('fach_boden_z'), w('fach_rand_z'))),
            ('Fach_Deckel', (fv - 40.0, fv),
             (w('fach_rand_z'), w('deckel_z1')))):
        k = sicher(name, quader_neu, pr, name, rx, y, z)
        if k:
            material_zuweisen(app, design, k, 'PETG', fehler)

    # Kamera im lokalen Rahmen, dann wie der Halter verschieben
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
        'MESSPUNKT: {:.0f} mm rechts, {:.0f} mm vor der Innenecke des'.format(
            w('mp_rechts'), w('mp_vorn')),
        '  Anschlags (X {:+.1f}, Y {:+.1f}); mit dem Nullpunkt in der Ecke'
        .format(*L['mp']),
        '  G54 X{:.0f} Y{:.0f}. Dort darf nichts aufs Werkstueck.'.format(
            w('mp_rechts'), -w('mp_vorn')),
        '',
        'KAMERA: Camera Module 3, Normalobjektiv (nicht Wide), hochkant,',
        '  Kabelkante nach hinten links. Linse X {:+.1f}, Y {:+.1f}, Z {:+.1f};'
        .format(lx, ly, lz),
        '  Blick {:.0f} Grad gegen +X, waagerecht.'.format(w('blick_az')),
        '  Punkt {:.1f} Grad neben der Achse (Bild +-{:.1f}), {:.1f} bis'
        .format(s0['quer'], L['bild_halb'][0], s1['unter']),
        '  {:.1f} Grad darunter (Bild +-{:.1f}), {:.0f} bis {:.0f} mm weit.'
        .format(s0['unter'], L['bild_halb'][1], s1['abstand'],
                s0['abstand']),
        '  {:.1f} Pixel je mm Hoehe ({:.3f} mm je Pixel).'.format(
            L['px_je_mm'], 1.0 / L['px_je_mm']),
        '',
        'LUFT: vorn bis Y {:+.1f}, die Traegerplatte faehrt bis {:+.1f};'
        .format(L['vorn_y'], w('th_hinten_y')),
        '  oben bis Z {:+.1f}, der X-Wagen unten bei {:+.1f}; hinten bis'
        .format(L['oben_z'], w('xwagen_z0')),
        '  Y {:+.1f}, das Fach bei {:+.1f}.'.format(L['hinten_y'],
                                                   w('fach_vorn_y')),
        '',
        'DRUCK: PETG, Fuss aufs Bett, keine Stuetzen. Polster, Zapfen und',
        '  Loecher als Traene, Muttertaschen als Sechseck mit Ecke oben.',
        'MONTAGE: 1. zwei Muttern M2 in die Taschen hinter der Wand.',
        '  2. Kamera auf die Zapfen, an der Kabelseite 2 x M2x{:.0f};'
        .format(w('m2_l')),
        '  Kabel einstecken.',
        '  3. 2 Hammermuttern M5 in die Nut oben auf dem hinteren 2060,',
        '  Halter mit 2 x M5x{:.0f} bei X {:+.0f} / {:+.0f} (Inbus von oben).'
        .format(w('m5_l'), m5[0][0], m5[1][0]),
        '  4. Kabel aussen an der Vorderwand des Fachs nach links bis',
        '  X {:+.0f}, dort ueber ihre Oberkante unter den Deckel, innen in'
        .format(L['kabel_eintritt_x']),
        '  der Signalgasse nach rechts zur Buchse des Pi.',
        '  Geschaetzt {:.0f} mm, Kabel Standard-Mini {:.0f} mm.'.format(
            L['kabel_weg'], w('kabel_l')),
        '',
        'NICHT GEMESSEN [w]/[?]: Kamera nach Massblatt (Bohrlehre_Kamera),',
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
