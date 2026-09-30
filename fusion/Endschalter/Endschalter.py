# Endschalter.py — Halter und Schaltfahnen fuer die Gabellichtschranken X, Y
#
# Baugruppe aus fuenf Druckteilen und einer Bohrlehre. Nichts bewegt sich
# gegeneinander; jedes Teil steht dort, wo es eingebaut wird:
#   Halter_Y    aussen am rechten 2040, hinter dem hinteren 2060: Fuss mit
#               2 x M5 in Hammermuttern der UNTEREN Aussennut — in der oberen
#               laeuft der Ruecklauf des Y-Riemens (hardware-notizen.md).
#               Darauf ein waagerechter Boden mit zwei M2-Einsaetzen fuer die
#               Platine, die Gabel zeigt nach oben, der Spalt laeuft laengs Y.
#   Fahne_Y     Klammer um die Aussenkante der rechten Schlittenplatte, das
#               Blatt haengt aussen neben dem 2040 in die Gabel. Laengs der
#               Kante verschiebbar, eine Madenschraube M3 in einem Einsatz
#               klemmt sie.
#   Halter_X    Block vor dem linken Ende des Portalrohrs: M5 in einer
#               Hammermutter der vorderen Rohrnut, Zunge in der Nut, stoesst
#               rechts an das Ende der X-Schiene (Anschlag beim Einbau und
#               fuer den Wagen). Die Platine steht senkrecht davor, die Gabel
#               zeigt nach vorn, der Spalt liegt waagerecht.
#   Klammer_X   um die linke untere Kante der Traegerplatte und ihre
#               Seitenrippe, Madenschraube M3 in einem Einsatz; oben ein Kopf
#               mit Einsatz fuer die Fahne.
#   Fahne_X     flaches Blatt auf dem Kopf, Langloch +-fx_verstellung: damit
#               wird der Schaltpunkt eingestellt.
#   Bohrlehre_LM393  ausgeblendet: Umriss und Lochbild der Platine zum
#               Anhalten, bevor die Halter gedruckt werden.
#   Referenz_nicht_drucken  nur zur Ansicht: Profile, Schienen, Schlitten,
#               Wagen, Traegerplatte, die beiden Lichtschranken.
#
# Beide Schalter schalten schaltabstand bevor ein Wagen am Schienenende
# steht (elektronik.md, Endschalter): die Wagen duerfen nicht ueber das Ende
# hinaus, sonst fallen Kugeln heraus. Im Modell stehen Portal und Toolhead
# genau am Schaltpunkt — beide Fahnen stecken mit der Vorderkante im Strahl.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py: Portal in der Mitte
# seines Wegs, Y nach vorn, Z senkrecht, X = 0 und Z = 0 in der Mitte des
# Portalrohrs, Y = 0 an der Stirnflaeche des X-Wagens. Teile am Portal
# (Fahne_Y, Halter_X) und am Toolhead (Klammer_X, Fahne_X) werden relativ
# dazu gerechnet und fuers Modell an den Schaltpunkt geschoben. Im
# Fusion-Modell sind Y und Z getauscht (Modell-Z = Maschine Y). Die Masse
# von Rahmen, Portal und Toolhead stehen hier noch einmal (Fusion-Skripte
# sind eigenstaendig); tools/endschalter_check.py vergleicht sie mit
# Portal.py und ToolheadZ.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'Endschalter'
REVISION = 1

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen (wie Portal.py, Portal in der Mitte) [v] -------------------
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Rahmen 2040 hochkant: Breite'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_y0':         (-360.0, 'Rahmen: hintere Stirnseite der 2040'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'nut_mitte':           (10.0, 'Profil: Nutmitte 10 mm von der Kante'),
    'quer_y1':           (-250.0, 'Rahmen: Rueckseite des hinteren 2060'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
    'y_schiene_y0':      (-310.0, 'Y-Schiene: hinteres Ende'),
    'y_schiene_b':         (12.0, 'Y-Schiene MGN12: Breite'),
    'y_schiene_h':          (8.0, 'Y-Schiene MGN12: Hoehe'),
    # V-Slot vereinfacht (Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),
    # Y-Weg nach hinten: das Portal steht von der Mitte bis ans hintere
    # Schienenende (tools/portal_check.py, y_weg) — dort sind die Y-Wagen
    # buendig mit dem Ende der Schiene.
    'y_weg_hinten':       (227.3, 'Y-Weg: Portal von der Mitte bis ans Schienenende'),

    # --- Rechter Y-Schlitten (wie Portal.py) [v] ----------------------------
    'platte_z0':          (-16.0, 'Schlittenplatte: Unterseite'),
    'platte_dicke':         (6.0, 'Schlittenplatte: Dicke'),
    'platte_aussen':       (22.0, 'Schlittenplatte: reicht so weit aussen neben die Schiene'),
    'platte_y0':         (-101.0, 'Schlittenplatte: Hinterkante'),
    'platte_y1':          (-19.0, 'Schlittenplatte: Vorderkante'),
    'y_wagen_breite':      (27.0, 'Y-Wagen MGN12H: Breite'),
    'y_wagen_y0':         (-82.7, 'Y-Wagen: Hinterkante'),
    'y_wagen_y1':         (-37.3, 'Y-Wagen: Vorderkante'),
    'y_wagen_z0':         (-26.0, 'Y-Wagen: Unterkante'),
    'wagen_loch_y':       (-70.0, 'Y-Wagen: hintere Schraubenreihe (Y)'),
    'wagen_loch_y2':      (-50.0, 'Y-Wagen: vordere Schraubenreihe (Y)'),
    'm3_senkung_d':         (6.0, 'Wagenschraube: Senkung in der Platte'),

    # --- Linkes Rohrende, X-Schiene, X-Wagen (Portal.py, ToolheadZ.py) [v] --
    'rohr_x0':           (-250.0, 'Portalrohr: linkes Ende'),
    'rohr_y0':            (-36.0, 'Portalrohr: Rueckseite'),
    'rohr_y1':            (-16.0, 'Portalrohr: Vorderseite (X-Schiene)'),
    'rohr_h':              (20.0, 'Portalrohr 2020: Hoehe'),
    'x_schiene_x0':     (-233.25, 'X-Schiene: linkes Ende'),
    'x_schiene_b':         (15.0, 'X-Schiene MGN15: Breite (in Z)'),
    'x_schiene_h':         (10.0, 'X-Schiene MGN15: Hoehe (in Y)'),
    'xw_min':           (-203.85, 'X-Wagenmitte am linken Schienenende'),
    'x_wagen_laenge':      (58.8, 'X-Wagen MGN15H: Laenge'),
    'x_wagen_breite':      (32.0, 'X-Wagen MGN15H: Breite (in Z)'),
    'traeger_x_links':    (-22.0, 'Traegerplatte: linke Kante ab Wagenmitte'),
    'traeger_dicke':        (8.0, 'Traegerplatte: Dicke (Y 0 bis 8)'),
    'traeger_z0':         (-66.0, 'Traegerplatte: Unterkante'),
    'rippe_b':              (4.0, 'Saeulenrippe links: Breite (X)'),
    'rippe_t':              (6.0, 'Saeulenrippe links: Tiefe vor der Platte (Y)'),
    'stirn_x0':          (-279.0, 'Stirnblock links: Aussenkante'),
    'stirn_y0':           (-46.0, 'Stirnblock links: Hinterkante'),
    'stirn_y1':           (-19.0, 'Stirnblock links: Vorderkante'),

    # --- Lichtschranke LM393 (Hailege), wie ToolheadZ.py [v] -----------------
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

    # --- Schaltpunkt und Blatt (beide Achsen) -------------------------------
    'schaltabstand':        (3.0, 'Schalter schaltet so weit vor dem Schienenende'),
    'fahne_dicke':          (3.0, 'Blatt: Dicke im Gabelspalt (wie Z)'),
    # Blatt reicht bis 7,5 mm an die Platine (1,5 ueber den Schlitzboden,
    # 1,5 ueber den Strahl hinaus) und 2 mm ueber die offene Seite der Gabel
    'fahne_ab_platine':     (7.5, 'Blatt: Kante so weit ueber der Platine'),
    'fahne_ueber_gabel':    (2.0, 'Blatt: reicht so weit ueber die offene Gabelseite'),

    # --- Halter Y ------------------------------------------------------------
    # 16: der innere Arm der Gabel bleibt 3 mm neben dem Y-Wagen, der am
    # Schienenende ueber die Gabel faehrt
    'gy_mitte_aussen':     (16.0, 'Y: Spaltmitte so weit neben der Aussenflaeche des 2040'),
    'ly_unter_kante':       (8.0, 'Y: Platine so weit unter der Oberkante der 2040'),
    'hy_fuss_dicke':        (6.0, 'Halter Y: Fuss am 2040 (wie YMotorhalter)'),
    'hy_fuss_unten':        (2.0, 'Halter Y: Fuss endet so weit ueber der Unterkante'),
    'hy_boden':             (5.0, 'Halter Y: Boden unter der Platine'),
    'hy_rand':              (1.5, 'Halter Y: Boden steht so weit um die Platine'),
    'hy_m5_rand':           (6.0, 'Halter Y: M5 so weit von den Enden'),
    'hy_fase':              (3.0, 'Halter Y: Fase unter dem Boden am Fuss'),

    # --- Fahne Y ---------------------------------------------------------------
    # Hinterkante auf der Platte (Portal in der Mitte): zwischen den
    # Wagenschrauben (Y -70 und -50), so steht der Halter 35 mm hinter dem
    # 2060 und weit vor dem hinteren Ritzel.
    'fy_hinten':          (-66.0, 'Fahne Y: Hinterkante (Y, Portal in der Mitte)'),
    'fy_laenge':           (12.0, 'Fahne Y: Laenge laengs der Plattenkante'),
    'kl_spiel':             (0.3, 'Klammern: Spiel auf die geklemmte Dicke'),
    'kl_kante':             (0.2, 'Klammern: Luft zur geklemmten Kante'),
    'fy_backe_o':           (6.0, 'Fahne Y: obere Backe (Einsatz M3)'),
    'fy_backe_u':           (2.5, 'Fahne Y: untere Backe'),
    'fy_backe_innen':       (9.0, 'Fahne Y: obere Backe reicht so weit auf die Platte'),
    'fy_wagen_luft':        (1.0, 'Fahne Y: untere Backe neben dem Y-Wagen'),

    # --- Halter X --------------------------------------------------------------
    'hx_luft_wagen':        (3.0, 'X: Platine so weit links vom Wagenende am Schienenende'),
    'hx_dicke':            (11.0, 'Halter X: Block vor dem Rohr (Y)'),
    'hx_h':                (22.0, 'Halter X: Hoehe des Blocks (Z)'),
    'hx_rand':              (1.0, 'Halter X: Block steht links so weit ueber die Platine'),
    'hx_zunge_b':           (5.8, 'Halter X: Zunge in der Rohrnut (Breite)'),
    'hx_zunge_t':           (2.0, 'Halter X: Zunge in der Rohrnut (Tiefe)'),
    'm5_senk_t':            (5.2, 'Halter X: M5-Kopf versenkt'),
    'm5_senk_d':            (9.0, 'Halter X: Senkung fuer den M5-Kopf'),

    # --- Klammer X und Fahne X (relativ zur X-Wagenmitte, Z absolut) --------
    'kx_z0':              (-40.0, 'Klammer X: Unterkante'),
    'kx_z1':              (-20.0, 'Klammer X: Oberkante der Backen'),
    'kx_wand':              (3.0, 'Klammer X: Seitenwand'),
    'kx_backe_h':           (2.5, 'Klammer X: hintere Backe'),
    # 5,85: 3 mm vor dem Pad des Z-Schlittens; der Einsatz ist 5,7 lang
    'kx_backe_v':          (5.85, 'Klammer X: vordere Backe (Einsatz M3)'),
    # bis 3 mm vor den Z-Wagen (dessen linke Kante bei -10 ab Wagenmitte)
    'kx_breite':            (9.2, 'Klammer X: Backen reichen so weit auf die Platte'),
    'kx_wagen_luft':        (3.0, 'Klammer X: ueber dem Wagen nur vor der Platte'),
    'kx_kopf_b':            (6.0, 'Klammer X: Kopf steht links ueber die Wand'),
    'kx_kopf_h':            (6.0, 'Klammer X: Kopf (Einsatz M3 fuer die Fahne)'),
    'fx_verstellung':       (2.0, 'Fahne X: Langloch je Richtung'),

    # --- Normteile und Regeln ------------------------------------------------
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'm3_durchgang':         (3.4, 'M3 Durchgang'),
    'insert_m3_d':          (4.6, 'Gewindeeinsatz M3: Einpressbohrung'),
    'luft_bau':             (3.0, 'Mindestfreigang zu bewegten Teilen'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
    'lehre_dicke':          (2.0, 'Bohrlehre: Plattendicke'),
}


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/endschalter_check.py).

    Schluessel mit _rel liegen relativ zum Portal in der Mitte (Fahne_Y,
    Halter_X) bzw. zur X-Wagenmitte (Klammer_X, Fahne_X); ohne _rel stehen
    sie so, wie das Modell sie zeigt: Portal und Toolhead am Schaltpunkt."""
    L = {}
    R = w('y_schienen_abstand') / 2.0
    b = w('rahmen_b')
    L['R'] = R
    L['rahmen_z1'] = w('rahmen_z0') + w('rahmen_h')
    L['nut_u_z'] = w('rahmen_z0') + w('nut_mitte')     # untere Seitennut
    L['nut_o_z'] = L['rahmen_z1'] - w('nut_mitte')     # obere: Y-Riemen
    L['aussen_x'] = R + b / 2.0                         # rechtes 2040 aussen
    L['quer_y'] = (w('quer_y1'), w('quer_y1') + b)
    L['tisch_z'] = w('rahmen_z0') - w('quer_h')
    # Portal am Y-Schaltpunkt; Toolhead am X-Schaltpunkt
    L['dy'] = -(w('y_weg_hinten') - w('schaltabstand'))
    L['dy_ende'] = -w('y_weg_hinten')
    L['xs'] = w('xw_min') + w('schaltabstand')
    pl, pb, pd = w('ls_pcb_laenge'), w('ls_pcb_breite'), w('ls_pcb_dicke')
    r = w('ls_pcb_rand')
    s, gb = w('ls_schlitz') / 2.0, w('ls_gabel_breite') / 2.0

    # ---- Y: Fahne auf der Platte, Strahl an ihrer Hinterkante --------------
    L['fy_y_rel'] = (w('fy_hinten'), w('fy_hinten') + w('fy_laenge'))
    L['fy_y'] = tuple(y + L['dy'] for y in L['fy_y_rel'])
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

    # ---- Halter Y -------------------------------------------------------------
    rand = w('hy_rand')
    L['hy_y'] = (L['ly_pcb_y'][0] - rand, L['ly_pcb_y'][1] + rand)
    L['hy_boden_z'] = (L['ly_pcb_z'][0] - w('hy_boden'), L['ly_pcb_z'][0])
    L['hy_boden_x'] = (L['aussen_x'], L['ly_pcb_x'][1] + rand)
    L['hy_fuss_x'] = (L['aussen_x'], L['aussen_x'] + w('hy_fuss_dicke'))
    L['hy_fuss_z'] = (w('rahmen_z0') + w('hy_fuss_unten'),
                      L['hy_boden_z'][1])
    L['hy_m5'] = [(y, L['nut_u_z']) for y in (L['hy_y'][0] + w('hy_m5_rand'),
                                            L['hy_y'][1] - w('hy_m5_rand'))]
    # mit Scheibe (1) wie am YMotorhalter: Fuss 6, dann 5 mm in die Nut —
    # 1,8 Lippe, 3,2 im Stein, 1 mm vor dem Nutgrund
    L['hy_m5_schraube'] = 12.0
    # Tasche fuer die Loetstifte der Gabel, so breit wie die Platine
    L['hy_tasche'] = (L['ly_pcb_x'][0], L['ly_pcb_x'][1],
                      L['ly_gabel_y'][0] - 0.75, L['ly_gabel_y'][1] + 0.75)
    fa = w('hy_fase')
    L['hy_fase_pkt'] = [(L['hy_fuss_x'][1], L['hy_boden_z'][0]),
                        (L['hy_fuss_x'][1] + fa, L['hy_boden_z'][0]),
                        (L['hy_fuss_x'][1], L['hy_boden_z'][0] - fa)]

    # ---- Fahne Y: Klammer um die Plattenkante, Blatt aussen ----------------
    pz0 = w('platte_z0')
    pz1 = pz0 + w('platte_dicke')
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

    # ---- X: Lichtschranke senkrecht vor dem linken Rohrende ----------------
    # Platine bis hx_luft_wagen vor das Wagenende am Schienenende; die Gabel
    # an der rechten Stirnkante (dorther kommt die Fahne), Spalt waagerecht.
    px1 = w('x_schiene_x0') - w('hx_luft_wagen')
    L['lx_pcb_x'] = (px1 - pl, px1)
    L['hx_y_rel'] = (w('rohr_y1'), w('rohr_y1') + w('hx_dicke'))
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

    # ---- Halter X: Block vor dem Rohr, stoesst an das Schienenende ---------
    L['hx_x'] = (L['lx_pcb_x'][0] - w('hx_rand'), w('x_schiene_x0'))
    L['hx_z'] = (-w('hx_h') / 2.0, w('hx_h') / 2.0)
    # M5 mitten im freien Stueck Rohr links der Schiene, auf der Nut
    L['hx_m5_x'] = (w('rohr_x0') + w('x_schiene_x0')) / 2.0
    # ohne Scheibe (Kopf in der Senkung): 5,8 Block, dann 6,2 in die Rohrnut
    # — 1,8 Lippe, 4 im Stein, 1,3 vor dem Grund (wie Portal.py)
    L['hx_m5_schraube'] = 12.0
    L['hx_zunge_x'] = (w('rohr_x0') + 0.5, w('x_schiene_x0') - 0.75)
    L['hx_tasche'] = (L['lx_gabel_x'][0] - 0.75, L['lx_gabel_x'][1] + 0.75,
                      -gb - 0.75, gb + 0.75)

    # ---- Klammer X (relativ zur X-Wagenmitte; Z absolut) ------------------
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
    # Fahne X: Blatt waagerecht mitten im Spalt; Spitze erreicht den Strahl,
    # wenn der Wagen am Schaltpunkt steht
    L['fx_z'] = (-w('fahne_dicke') / 2.0, w('fahne_dicke') / 2.0)
    L['fx_spitze_rel'] = L['lx_strahl_x'] - L['xs']
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


# --- Bauteile ------------------------------------------------------------------
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
    Kante verschiebbar — so wird der Schaltpunkt eingestellt.

    Drucklage: eine Stirnseite aufs Bett, das ganze Profil steht senkrecht —
    keine Stuetzen. SCHWARZ drucken: helles PETG laesst das Infrarot der
    Schranke durch."""
    y = L['fy_y']
    wx, oz, uz = L['fy_wand_x'], L['fy_backe_o_z'], L['fy_backe_u_z']
    k = quader(comp, 'Wand_FY', wx, y, (uz[0], oz[1]), 'neu').bodies.item(0)
    k.name = 'Fahne_Y'
    quader(comp, 'Backe_oben_FY', L['fy_backe_o_x'], y, oz, 'dazu', k)
    quader(comp, 'Backe_unten_FY', L['fy_backe_u_x'], y, uz, 'dazu', k)
    quader(comp, 'Blatt_FY', L['fy_blatt_x'], y, L['fy_blatt_z'], 'dazu', k)
    ym = L['fy_einsatz_y_rel'] + L['dy']
    bohrung(comp, 'Einsatz_FY', 'z', [(L['fy_einsatz_x'], ym)],
            w('insert_m3_d'), oz[0] - 1.0, oz[1] + 1.0, k)
    fussfase(comp, k, 'z', y[0], w('fase_fuss'), fehler, 'Fahne_Y')
    bbox_pruefen(k, 'Fahne_Y', ((L['fy_backe_o_x'][0], wx[1]), y,
                                (L['fy_blatt_z'][0], oz[1])), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_halter_x(app, design, comp, L, fehler):
    """Halter der X-Lichtschranke vor dem linken Ende des Portalrohrs. Ein
    Block liegt an der Rohrvorderseite, eine Zunge fuehrt ihn in der Nut,
    rechts stoesst er an das Ende der X-Schiene: so steht er beim Einbau
    immer gleich, und der Wagen faende dort einen Anschlag, bevor er von der
    Schiene laeuft. Eine M5 mit versenktem Kopf haengt ihn in eine
    Hammermutter. Die Platine sitzt vorn auf zwei M2-Einsaetzen und deckt
    den Kopf ab — erst den Block anschrauben, dann die Lichtschranke.

    Drucklage: Vorderseite (Platinenseite) aufs Bett, die Zunge oben —
    keine Stuetzen."""
    dy = L['dy']
    y = tuple(v + dy for v in L['hx_y_rel'])
    k = quader(comp, 'Block_X', L['hx_x'], y, L['hx_z'], 'neu').bodies.item(0)
    k.name = 'Halter_X'
    zb = w('hx_zunge_b') / 2.0
    quader(comp, 'Zunge_X', L['hx_zunge_x'], (y[0] - w('hx_zunge_t'), y[0]),
           (-zb, zb), 'dazu', k)
    m5 = [(L['hx_m5_x'], 0.0)]
    bohrung(comp, 'M5_X', 'y', m5, w('m5_durchgang'),
            y[0] - w('hx_zunge_t') - 1.0, y[1] + 1.0, k)
    bohrung(comp, 'M5_Senkung_X', 'y', m5, w('m5_senk_d'),
            y[1] - w('m5_senk_t'), y[1] + 1.0, k)
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
    die Fahne.

    Drucklage: Unterkante aufs Bett — die Backen stehen senkrecht, die Wand
    wird nach oben schmaler, unter dem Kopf eine 45-Grad-Fase: keine
    Stuetzen. Schwarz wie die Fahne."""
    xs, dy = L['xs'], L['dy']

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
    return k


def bau_fahne_x(app, design, comp, L, fehler):
    """Fahne der X-Achse: flaches Blatt auf dem Kopf der Klammer, mit M3x8 in
    dessen Einsatz. Das Langloch (+-fx_verstellung) stellt den Schaltpunkt
    ein; die Spitze laeuft waagerecht mitten durch den Gabelspalt.

    Drucklage: flach — SCHWARZ drucken."""
    xs, dy = L['xs'], L['dy']
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
    return k


def bau_bohrlehre(app, design, comp, L, fehler):
    """Umriss und Lochbild der Platine zum Anhalten, bevor die Halter
    gedruckt werden: die Platine auflegen, beide Loecher muessen fluchten.
    Liegt unter dem Tisch, ausgeblendet (Konvention SKILL.md)."""
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


# --- Referenz (nicht drucken) --------------------------------------------------
def bau_referenz(app, design, teile, L, fehler):
    """Profile, Schienen, Schlitten, Rohr, Wagen, Traegerplatte und die
    beiden Lichtschranken — nur zur Ansicht, NICHT drucken. Portal und
    Toolhead stehen am Schaltpunkt. Jedes Teil wird fuer sich gebaut:
    scheitert eines, steht das im Bericht."""
    R, b = L['R'], w('rahmen_b')
    dy, xs = L['dy'], L['xs']
    z0, z1 = w('rahmen_z0'), L['rahmen_z1']

    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    def box(comp, name, x, y, z, mat):
        def bauen():
            kk = quader(comp, name, x, y, z, 'neu').bodies.item(0)
            kk.name = name
            return kk
        k = sicher(name, bauen)
        if k:
            material_zuweisen(app, design, k, mat, fehler)
        return k

    pr = teile['Ref_Rahmen']
    y_hinten = (w('rahmen_y0'), L['quer_y'][1] + 30.0)
    y_links = (-300.0, -170.0)             # unter dem linken Rohrende
    for name, laengs, bereich, quer, z in (
            ('2040_rechts', 'y', y_hinten, (R - b / 2.0, R + b / 2.0),
             (z0, z1)),
            ('2040_links', 'y', y_links, (-R - b / 2.0, -R + b / 2.0),
             (z0, z1)),
            ('2060_hinten', 'x', (R - 30.0, R + 43.0), L['quer_y'],
             (L['tisch_z'], z0))):
        k = sicher(name, bau_profil, pr, name, laengs, bereich, quer, z)
        if k:
            material_zuweisen(app, design, k, 'Aluminum 6061', fehler)
    hb = w('y_schiene_b') / 2.0
    box(pr, 'Y-Schiene_rechts', (R - hb, R + hb),
        (w('y_schiene_y0'), y_hinten[1]), (z1, z1 + w('y_schiene_h')), 'Steel')
    box(pr, 'Y-Schiene_links', (-R - hb, -R + hb), y_links,
        (z1, z1 + w('y_schiene_h')), 'Steel')

    po = teile['Ref_Portal']
    box(po, 'Schlittenplatte_rechts', (R - 30.0, L['platte_x1']),
        (w('platte_y0') + dy, w('platte_y1') + dy), L['platte_z'], 'PETG')
    hw = w('y_wagen_breite') / 2.0
    box(po, 'Y-Wagen_rechts', (R - hw, R + hw),
        (w('y_wagen_y0') + dy, w('y_wagen_y1') + dy),
        (w('y_wagen_z0'), w('platte_z0')), 'Steel')
    rh = w('rohr_h') / 2.0
    ry = (w('rohr_y0') + dy, w('rohr_y1') + dy)

    def rohr():
        return bau_profil(po, 'Portalrohr', 'x', (w('rohr_x0'), -150.0), ry,
                          (-rh, rh))
    k = sicher('Portalrohr', rohr)
    if k:
        material_zuweisen(app, design, k, 'Aluminum 6061', fehler)
    sb = w('x_schiene_b') / 2.0
    box(po, 'X-Schiene', (w('x_schiene_x0'), -150.0),
        (ry[1], ry[1] + w('x_schiene_h')), (-sb, sb), 'Steel')
    box(po, 'Stirnblock_links', (w('stirn_x0'), w('rohr_x0')),
        (w('stirn_y0') + dy, w('stirn_y1') + dy), (-rh, rh), 'PETG')

    to = teile['Ref_Toolhead']
    wl, wb = w('x_wagen_laenge') / 2.0, w('x_wagen_breite') / 2.0
    box(to, 'X-Wagen', (xs - wl, xs + wl), (ry[1], dy), (-wb, wb), 'Steel')
    xt, td = w('traeger_x_links'), w('traeger_dicke')
    box(to, 'Traegerplatte', (xs + xt, xs - xt), (dy, dy + td),
        (w('traeger_z0'), wb + 4.0), 'PETG')
    box(to, 'Saeulenrippe_links', (xs + xt, xs + xt + w('rippe_b')),
        (dy + td, dy + td + w('rippe_t')), (w('traeger_z0'), wb + 4.0),
        'PETG')

    ls = teile['Ref_Lichtschranken']
    box(ls, 'LS_Y_Platine', L['ly_pcb_x'], L['ly_pcb_y'], L['ly_pcb_z'],
        'Leiterplatte')
    for i, ax in enumerate(L['ly_arme_x']):
        box(ls, 'LS_Y_Gabel_{}'.format(i + 1), ax, L['ly_gabel_y'],
            L['ly_gabel_z'], 'Kunststoff')
    lx_y = (L['lx_pcb_y_rel'][0] + dy, L['lx_pcb_y_rel'][1] + dy)
    box(ls, 'LS_X_Platine', L['lx_pcb_x'], lx_y, L['lx_pcb_z'],
        'Leiterplatte')
    gy = (L['lx_gabel_y_rel'][0] + dy, L['lx_gabel_y_rel'][1] + dy)
    for i, az in enumerate(L['lx_arme_z']):
        box(ls, 'LS_X_Gabel_{}'.format(i + 1), L['lx_gabel_x'], gy, az,
            'Kunststoff')


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/endschalter_check.py)."""
    y_hinten = L['quer_y'][0] - L['hy_y'][1]
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py. Im Modell stehen Portal',
        '  und Toolhead am Schaltpunkt: Portal {:+.1f} von der Mitte ({:.0f} mm'
        .format(L['dy'], w('schaltabstand')),
        '  vor dem hinteren Schienenende), X-Wagenmitte {:+.2f} ({:.0f} mm vor'
        .format(L['xs'], w('schaltabstand')),
        '  dem linken Schienenende). Beide Fahnen stehen mit der Kante im Strahl.',
        '',
        'HALTER_Y: aussen an das rechte 2040, {:.0f} mm hinter dem hinteren 2060;'
        .format(y_hinten),
        '  2 x M5x{:.0f} mit Scheibe in Hammermuttern der UNTEREN Nut (Z {:+.0f}).'
        .format(L['hy_m5_schraube'], L['nut_u_z']),
        '  NICHT in die obere Nut — dort laeuft der Ruecklauf des Y-Riemens.',
        '  Lichtschranke mit 2 x M2x6 in die Einsaetze, Gabel oben und vorn.',
        'FAHNE_Y: von aussen auf die Kante der rechten Schlittenplatte, Hinterkante',
        '  {:.0f} mm vor der Hinterkante der Platte; Madenschraube M3x8 im Einsatz.'
        .format(w('fy_hinten') - w('platte_y0')),
        '  Schaltpunkt: Klammer laengs der Kante verschieben.',
        'HALTER_X: vor das linke Rohrende, Hammermutter M5 in die vordere Nut,',
        '  Block rechts an das Ende der X-Schiene schieben, M5x{:.0f} (Kopf'
        .format(L['hx_m5_schraube']),
        '  versenkt) — ERST DANN die Lichtschranke mit 2 x M2x6 (sie deckt den',
        '  Kopf ab). Gabel nach vorn, Spalt waagerecht.',
        'KLAMMER_X: von links auf die untere Kante der Traegerplatte (unter dem',
        '  X-Wagen), Madenschraube M3x8 im vorderen Einsatz auf die Seitenrippe.',
        'FAHNE_X: mit M3x{:.0f} auf den Kopf der Klammer, Langloch +-{:.0f} mm stellt'
        .format(L['fx_schraube'], w('fx_verstellung')),
        '  den Schaltpunkt ein.',
        '',
        'DRUCK (PETG, Bambu Lab A1): Fahnen und Klammern SCHWARZ (helles PETG',
        '  laesst das Infrarot durch). Halter_Y auf der Fussflaeche, Fahne_Y auf',
        '  der Stirnseite, Halter_X mit der Platinenseite aufs Bett, Klammer_X',
        '  auf der Unterkante, Fahne_X flach. Keine Stuetzen.',
        'EINSAETZE: 4 x M2 (3,2 x 2,5, Bohrung {:.1f}), 3 x M3 (Bohrung {:.1f}).'
        .format(w('ls_pcb_loch_d'), w('insert_m3_d')),
        '',
        'NICHT GEMESSEN [?]: Boden des Gabelschlitzes ({:.0f} mm ueber der'
        .format(w('ls_schlitz_boden')),
        '  Platine, das Blatt bleibt {:.1f} mm darueber); Loetstifte unter der'
        .format(w('fahne_ab_platine') - w('ls_schlitz_boden')),
        '  Platine (Taschen {:.1f} mm unter der Gabel); ob der X-Wagen links'
        .format(w('ls_pin_tasche')),
        '  einen Schmiernippel hat (die Platine steht {:.0f} mm vor dem Wagenende).'
        .format(w('hx_luft_wagen')),
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
        occ = {}
        for name, bauen in (('Halter_Y', bau_halter_y),
                            ('Fahne_Y', bau_fahne_y),
                            ('Halter_X', bau_halter_x),
                            ('Klammer_X', bau_klammer_x),
                            ('Fahne_X', bau_fahne_x),
                            ('Bohrlehren', bau_bohrlehre)):
            o = root.occurrences.addNewComponent(einheit)
            o.component.name = name
            occ[name] = o
            bauen(app, design, o.component, L, fehler)
        for o in occ.values():
            o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Rahmen', 'Ref_Portal', 'Ref_Toolhead',
                     'Ref_Lichtschranken'):
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
