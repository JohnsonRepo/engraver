# Opferplatte.py — Anschlag und Fuehrung der Opferplatte am Gestell
#
# Maschine und Opferplatte stehen auf demselben Tisch: Die Plattenober-
# flaeche liegt 25,3 mm ueber der Unterkante der 2060. Bis Rev. 3 hob das
# Modell die Maschine auf vier Fuesse, die es an der Maschine nie gab
# (Rev. 4, 2026-11-21). Die Z-Grenze ueber der Platte rechnet ToolheadZ.py.
#
# Fuenf Druckteile, dazu die Platte und Referenzteile nur zur Ansicht:
#   Anschlag_vorn, Anschlag_hinten   am linken Ende der beiden 2060
#   Fuehrung_vorn, Fuehrung_hinten   am rechten Ende
#               Je ein Halter steht innen an einem Ende eines 2060 auf dem
#               Tisch, gehalten von 2x M5 in Hammermuttern der inneren
#               unteren Seitennut. Er reicht bis an die Platte und fuehrt
#               sie in Y. Vorn ist dort nur 11,65 mm Platz: voller Block,
#               die M5 versenkt. Hinten Flansch am 2060, Boden und Wand an
#               der Platte. Die linken tragen den Anschlag fuer das
#               Plattenende, die rechten eine Einfuehrschraege:
#               herausgezogen wird die Platte nach rechts. Fuehrung_vorn
#               traegt dazu vor dem Ende des 2060 eine Endplatte mit dem
#               Ausleger und dem Lagerbock fuer den Riegel.
#   Riegel      Klappriegel vor dem rechten Plattenende (Rev. 3), damit die
#               Platte nicht nach rechts herausrutscht. Er dreht sich um
#               eine M5 laengs X: Ein Stoss gegen die Platte drueckt ihn
#               laengs der Achse an den Lagerbock und kann ihn nicht
#               aufklappen. Zu liegt er vor dem Plattenende, offen nach vorn
#               umgeklappt; in beiden Lagen liegt er auf dem Ausleger, die
#               Schwerkraft haelt ihn. Der Sechskantkopf sitzt in einer
#               Tasche im Riegel, die Stoppmutter stellt man von rechts nach.
#   Opferplatte  Spanplatte 615 x 349 x 25 (vorhanden, Angabe vom
#               2026-10-02), gemessen 25,3 dick [v]. Sie liegt auf dem
#               Tisch zwischen den 2060 und den Haltern,
#               mittig unter dem Arbeitsfeld, und steht rechts ueber das
#               Gestell hinaus: dort fasst man sie zum Herausziehen.
#   Referenz_nicht_drucken  die beiden 2060 und die beiden 2040.
#
# Koordinaten = Maschinenkoordinaten wie Portal.py, Portal in der Mitte
# seines Wegs: X nach rechts, Y nach vorn, Z senkrecht, Z = 0 in der Mitte
# des Portalrohrs. Im Fusion-Modell sind Y und Z getauscht (Modell-Z =
# Maschine Y). tools/opferplatte_check.py vergleicht Rahmen und Arbeitsfeld
# mit Portal.py und ToolheadZ.py.
#
# Konventionen: siehe fusion-python/SKILL.md und references/baugruppen.md.
# Eine Bohrlehre gibt es nicht: Die Halter sind in Hammermuttern
# geschraubt, die Achse des Riegels verbindet zwei Druckteile durch fertig
# gedruckte Loecher. Gebohrt wird nichts.

import math

import adsk.core, adsk.fusion, traceback

SKRIPT_NAME = 'Opferplatte'
REVISION = 4

# --- Masse (einzige Quelle; erzeugt 1:1 die Fusion-User-Parameter) -----------
# Name: (Wert in mm, Kommentar fuer den Parameter-Dialog)
MASSE = {
    # --- Rahmen (wie Portal.py) [v] -----------------------------------------
    'y_schienen_abstand': (514.0, 'Y-Schienen: Abstand Mitte zu Mitte'),
    'rahmen_b':            (20.0, 'Profil: Breite (20er Raster)'),
    'rahmen_h':            (40.0, 'Rahmen 2040 hochkant: Hoehe'),
    'rahmen_laenge':      (600.0, 'Rahmen 2040: Laenge'),
    'rahmen_y1':          (240.0, 'Rahmen: vordere Stirnseite der 2040'),
    'rahmen_z0':          (-69.0, 'Rahmen: Unterkante der 2040 = Oberkante 2060'),
    'quer_laenge':        (600.0, '2060 quer: Laenge'),
    'quer_h':              (60.0, '2060 quer, hochkant: Hoehe'),
    'quer_vorn_y0':       (185.0, 'vorderes 2060: Innenseite'),
    'quer_hinten_y0':    (-250.0, 'hinteres 2060: Aussenseite'),
    'nut_mitte':           (10.0, 'Profil: Nutmitte 10 mm von der Kante'),
    # V-Slot vereinfacht (Referenz), wie Portal.py
    'nut_oben':             (6.0, 'V-Slot: Oberkante der Nutoeffnung unter der Kante'),
    'nut_v_t':              (1.0, 'V-Slot vereinfacht: Tiefe des V aussen'),
    'nut_b':                (6.2, 'V-Slot: Nutoeffnung innen (Engstelle)'),
    'nut_t':                (2.0, 'V-Slot vereinfacht: Tiefe der Engstelle'),
    'nut_kammer_b':         (8.0, 'V-Slot vereinfacht: Breite der Kammer'),
    'nut_kammer_t':         (5.5, 'V-Slot vereinfacht: Tiefe bis Kammergrund'),
    'kern_d':               (4.2, 'V-Slot: Kernbohrung'),

    # --- Arbeitsfeld: wo der Strahl hinkommt --------------------------------
    # X wie die X-Wagenmitte (der Laser sitzt mittig), Y = Strahlachse plus
    # der Y-Weg des Portals: hinten bis ans Schienenende, vorn mit Z unten
    # bis 3 mm vor das 2060. tools/opferplatte_check.py rechnet es aus
    # Portal.py und ToolheadZ.py nach.
    'feld_x0':          (-203.85, 'Arbeitsfeld: links'),
    'feld_x1':           (187.35, 'Arbeitsfeld: rechts'),
    'feld_y0':           (-168.8, 'Arbeitsfeld: hinten'),
    'feld_y1':            (164.5, 'Arbeitsfeld: vorn'),

    # --- Opferplatte [v] Angabe 2026-10-02 ------------------------------------
    # Nennmass 25, gemessen 25,3 (Rev. 2, 2026-10-02). Sie liegt auf dem
    # Tisch, auf dem auch die 2060 stehen.
    'platte_l':           (615.0, 'Opferplatte: Laenge (X, wird nach rechts gezogen)'),
    'platte_b':           (349.0, 'Opferplatte: Breite (Y)'),
    'platte_dicke':        (25.3, 'Opferplatte: Dicke (gemessen)'),
    'platte_spiel':         (1.0, 'Opferplatte: Luft je Seite zur Fuehrung'),

    # --- Halter innen an den 2060 (Rev. 4) ----------------------------------
    # 50 mm wie bisher die Fuesse: unter der Kreuzung mit dem 2040, die
    # Hammermuttern ganz im Profil.
    'halter_l':            (50.0, 'Halter: Laenge (X) am Ende des 2060'),
    'flansch_t':            (6.0, 'Halter hinten: Flansch innen am 2060, Dicke'),
    'flansch_ueber':       (19.0, 'Halter: Flansch reicht so weit ueber den Tisch'),
    'wand_t':               (6.0, 'Halter: Fuehrungswand an der Platte, Dicke'),
    'boden_t':              (5.0, 'Halter: Boden zwischen Flansch und Wand, Dicke'),
    'voll_bis':            (20.0, 'Halter: bis zu dieser Breite voller Block'),
    'm5_abstand':          (32.0, 'Halter: Abstand der beiden M5 (X)'),
    # M5 waagerecht in die innere untere Seitennut: 5 mm ueber die
    # Profilflaeche (1,8 Lippe, 3,2 im Stein, 1 mm vor dem Nutgrund).
    # Im vollen Halter (vorn) sitzt der Kopf ohne Scheibe in einer Senkung.
    'nut_ein':              (5.0, 'M5: so weit ueber die Profilflaeche in die Nut'),
    'senk_d':              (10.0, 'Senkung fuer den M5-Zylinderkopf (voller Halter)'),
    'senk_luft':            (0.5, 'Kopf mindestens so weit unter der Fuehrungsflaeche'),
    'anschlag_t':           (5.0, 'Anschlag (links): Dicke in X'),
    'anschlag_tief':       (15.0, 'Anschlag: greift so weit vor das Plattenende'),
    'anschlag_h':          (20.0, 'Anschlag: Hoehe ueber dem Tisch'),
    'einfuehr':             (5.0, 'Einfuehrschraege (rechts): 45 Grad, so weit'),
    # Endplatte vorn rechts vor dem Ende des 2060: traegt den Ausleger auf
    # ganzer Breite und verlaengert die Fuehrung, die Einfuehrschraege sitzt
    # dort an ihrem Ende.
    'endplatte_t':          (6.0, 'Endplatte (vorn rechts): Dicke in X'),
    'endplatte_h':         (20.0, 'Endplatte: Hoehe ueber dem Tisch'),

    # --- Riegel vorn rechts (Rev. 3) -----------------------------------------
    # Klappt um eine M5 laengs X. Lagerbock und Ausleger liegen vor der
    # Flucht der Fuehrung, also ausserhalb der Bahn, auf der die Platte
    # herausgezogen wird. Der Ausleger liegt so tief, dass der Riegel zu
    # wie offen mit riegel_luft Luft ueber ihm liegt.
    'riegel_spiel':         (1.0, 'Riegel: Luft zum Plattenende (X)'),
    'riegel_dicke':         (9.0, 'Riegel: Dicke (X)'),
    'riegel_h':            (15.0, 'Riegel: Hoehe (Z) = Durchmesser der Nabe'),
    'riegel_ueber':        (17.0, 'Riegel: greift so weit vor das Plattenende (Y)'),
    'riegel_luft':          (0.5, 'Riegel: Luft ueber dem Ausleger'),
    'ausleger_luft':        (2.0, 'Ausleger: Abstand zur Flucht der Fuehrung (Y)'),
    'ausleger_t':           (6.0, 'Ausleger: Dicke auf dem Tisch'),
    'lager_t':              (7.0, 'Lagerbock: Dicke (X)'),
    'lager_b':             (20.0, 'Lagerbock: Breite (Y)'),
    'lager_ueber':          (8.0, 'Lagerbock: reicht so weit ueber die Achse'),

    # --- Normteile und Regeln ------------------------------------------------
    'm5_durchgang':         (5.5, 'M5 Durchgang'),
    'm5_scheibe_d':        (10.0, 'M5 Scheibe DIN 125: Durchmesser'),
    'm5_scheibe_h':         (1.0, 'M5 Scheibe DIN 125: Dicke'),
    'm5_kopf_h':            (5.0, 'M5 Zylinderkopf: Hoehe'),
    'm5_kopf_d':            (8.5, 'M5 Zylinderkopf: Durchmesser'),
    # Achse des Riegels: Sechskantschraube, der Kopf sitzt in einer Tasche
    # im Riegel und dreht sich mit ihm; die Stoppmutter stellt man von
    # rechts mit dem Maulschluessel nach
    'm5_sw':                (8.0, 'M5 Sechskant (Kopf ISO 4017, Mutter DIN 985): SW'),
    'm5_sk_k':              (3.5, 'M5 Sechskantschraube ISO 4017: Kopfhoehe'),
    'm5_mutter_h':          (5.0, 'M5 Stoppmutter DIN 985: Hoehe'),
    'sk_spiel':             (0.3, 'Sechskanttasche: Zugabe auf die Schluesselweite'),
    'ueberstand':           (1.5, 'Schraube: Ueberstand ueber die Stoppmutter'),
    'luft_bau':             (3.0, 'Mindestfreigang'),
    'fase_fuss':            (0.4, 'Fase gegen Elefantenfuss'),
}

SEITEN = ('vorn', 'hinten')         # welches 2060
ENDEN = ('links', 'rechts')         # welches Ende
TEIL = {'links': 'Anschlag', 'rechts': 'Fuehrung'}
RIEGEL_AN = ('vorn', 'rechts')      # dieser Halter traegt den Riegel (lage()
                                    # rechnet ihn fuer vorn rechts)
M5_LAENGEN = (8.0, 10.0, 12.0, 16.0, 20.0, 25.0)


def halter_name(s, e):
    """Name des Halters an Seite s ('vorn' | 'hinten'), Ende e."""
    return '{}_{}'.format(TEIL[e], s)


def w(name):
    """Wert in mm."""
    return MASSE[name][0]


def lage():
    """Alle abgeleiteten Lagen in Maschinenkoordinaten (mm). Einzige Quelle
    fuer Geometrie UND Pruefung (tools/opferplatte_check.py)."""
    L = {}
    R = w('y_schienen_abstand') / 2.0
    L['R'] = R
    b = w('rahmen_b')
    ql = w('quer_laenge') / 2.0
    L['quer_x'] = (-ql, ql)
    L['quer_z'] = (w('rahmen_z0') - w('quer_h'), w('rahmen_z0'))
    L['quer_y'] = {'vorn': (w('quer_vorn_y0'), w('quer_vorn_y0') + b),
                   'hinten': (w('quer_hinten_y0'), w('quer_hinten_y0') + b)}
    L['rahmen_y'] = (w('rahmen_y1') - w('rahmen_laenge'), w('rahmen_y1'))
    L['rahmen_z'] = (w('rahmen_z0'), w('rahmen_z0') + w('rahmen_h'))
    z_u = L['quer_z'][0]                     # Unterkante der 2060 = Tisch
    L['z_2060'] = z_u
    # untere Nut und untere Seitennut der 2060 (die Seitennut innen nimmt
    # die Hammermuttern der Halter)
    L['nut_unten_y'] = {s: (y[0] + y[1]) / 2.0 for s, y in L['quer_y'].items()}
    L['nut_seite_z'] = z_u + w('nut_mitte')

    # ---- Opferplatte: auf dem Tisch, auf dem auch die 2060 stehen; mittig
    #      unter dem Arbeitsfeld (Y), links am Anschlag.
    fy = (w('feld_y0') + w('feld_y1')) / 2.0
    pb = w('platte_b') / 2.0
    L['platte_y'] = (fy - pb, fy + pb)
    L['tisch_z'] = z_u
    L['platte_z'] = (z_u, z_u + w('platte_dicke'))
    top = L['platte_z'][1]
    x0 = L['quer_x'][0] + w('anschlag_t')
    L['platte_x'] = (x0, x0 + w('platte_l'))
    L['platte_ueber'] = L['platte_x'][1] - L['quer_x'][1]   # rechts zum Fassen

    # ---- Halter: innen an den Enden der beiden 2060 ------------------------
    hl = w('halter_l')
    L['halter_x'] = {'links': (L['quer_x'][0], L['quer_x'][0] + hl),
                     'rechts': (L['quer_x'][1] - hl, L['quer_x'][1])}
    sp = w('platte_spiel')
    L['fuehrung_y'] = {'vorn': L['platte_y'][1] + sp,
                       'hinten': L['platte_y'][0] - sp}
    # Block und Wand reichen bis zur Plattenoberflaeche, nicht darueber
    L['halter_z'] = (z_u, top)
    L['flansch_z'] = (z_u, z_u + w('flansch_ueber'))
    for k in ('aus', 'innen', 'innen_y', 'voll', 'wand_y', 'boden_y',
              'flansch_y', 'anschlag_y', 'm5_schraube', 'm5_scheibe',
              'unter_kopf', 'auflage_y', 'senk_y'):
        L[k] = {}
    for s in SEITEN:
        q0, q1 = L['quer_y'][s]
        aus = 1.0 if s == 'vorn' else -1.0   # von der Platte zum 2060 hin
        innen = q0 if s == 'vorn' else q1    # Innenseite des 2060
        g = L['fuehrung_y'][s]
        L['aus'][s] = aus
        L['innen'][s] = innen
        L['innen_y'][s] = (min(g, innen), max(g, innen))
        breite = abs(innen - g)
        # schmal: voller Block; breit: Flansch am 2060, Boden, Wand
        L['voll'][s] = breite <= w('voll_bis')
        wg = g + aus * w('wand_t')
        L['wand_y'][s] = (min(g, wg), max(g, wg))
        fi = innen - aus * w('flansch_t')
        L['flansch_y'][s] = (min(fi, innen), max(fi, innen))
        L['boden_y'][s] = (min(wg, fi), max(wg, fi))
        ag = g - aus * w('anschlag_tief')
        L['anschlag_y'][s] = (min(g, ag), max(g, ag))
        # M5: immer nut_ein ueber die Profilflaeche. Im vollen Block ohne
        # Scheibe versenkt: die laengste Schraube, deren Kopf noch
        # senk_luft unter der Fuehrungsflaeche bleibt. Am Flansch mit
        # Scheibe.
        if L['voll'][s]:
            ls = max(l for l in M5_LAENGEN
                     if breite - (l - w('nut_ein'))
                     >= w('m5_kopf_h') + w('senk_luft'))
            unter, scheibe = ls - w('nut_ein'), False
        else:
            ls = min(l for l in M5_LAENGEN
                     if l >= w('flansch_t') + w('m5_scheibe_h')
                     + w('nut_ein'))
            unter, scheibe = w('flansch_t'), True
        L['m5_schraube'][s] = ls
        L['m5_scheibe'][s] = scheibe
        L['unter_kopf'][s] = unter
        auflage = innen - aus * unter        # Kopf (oder Scheibe) liegt hier
        L['auflage_y'][s] = auflage
        L['senk_y'][s] = ((min(g, auflage), max(g, auflage))
                          if L['voll'][s] else None)
    # zwei M5 je Halter, waagerecht in die innere untere Seitennut
    L['m5_x'] = {e: [(x[0] + x[1]) / 2.0 + d * w('m5_abstand') / 2.0
                     for d in (-1, 1)] for e, x in L['halter_x'].items()}
    L['anschlag_x'] = (L['quer_x'][0], L['quer_x'][0] + w('anschlag_t'))
    L['anschlag_z'] = (L['tisch_z'], L['tisch_z'] + w('anschlag_h'))

    # ---- Endplatte vorn rechts: vor dem Ende des vorderen 2060, von der
    #      Flucht der Fuehrung bis ueber den Ausleger. Sie verlaengert die
    #      Fuehrung um ihre Dicke; die Einfuehrschraege sitzt deshalb dort.
    x1 = L['quer_x'][1]
    L['endplatte_x'] = (x1, x1 + w('endplatte_t'))
    L['endplatte_z'] = (L['tisch_z'], L['tisch_z'] + w('endplatte_h'))
    L['fuehrung_ende_x'] = {s: x1 + (w('endplatte_t')
                                     if (s, 'rechts') == RIEGEL_AN else 0.0)
                            for s in SEITEN}
    # Einfuehrschraege am rechten Ende der Fuehrung: Dreieck in X/Y, ueber
    # die Kanten hinaus verlaengert, damit der Schnitt sauber durchgeht
    e_ = w('einfuehr')
    L['einfuehr_pkt'] = {}
    for s in SEITEN:
        g, aus, xe = L['fuehrung_y'][s], L['aus'][s], L['fuehrung_ende_x'][s]
        L['einfuehr_pkt'][s] = [(xe - e_ - 1.0, g - aus), (xe + 1.0, g - aus),
                                (xe + 1.0, g + aus * (e_ + 1.0))]

    # ---- Riegel vorn rechts: dreht sich um eine M5 laengs X ----------------
    #      Lagerbock und Ausleger beginnen ausleger_luft vor der Flucht der
    #      Fuehrung: Die Bahn, auf der die Platte herausgezogen wird, bleibt
    #      frei. Die Nabe hat den Durchmesser riegel_h, so liegt die Leiste
    #      zu (Nase nach hinten) wie offen (nach vorn) gleich hoch ueber dem
    #      Ausleger.
    L['riegel_an'] = RIEGEL_AN
    rx0 = L['platte_x'][1] + w('riegel_spiel')
    L['riegel_x'] = (rx0, rx0 + w('riegel_dicke'))
    ai = L['fuehrung_y']['vorn'] + w('ausleger_luft')
    L['lager_y'] = (ai, ai + w('lager_b'))
    rh = w('riegel_h') / 2.0
    yp = ai + w('lager_b') / 2.0
    zp = L['tisch_z'] + w('ausleger_t') + w('riegel_luft') + rh
    L['riegel_achse'] = (yp, zp)
    L['riegel_nase_y'] = L['platte_y'][1] - w('riegel_ueber')
    L['riegel_l'] = yp - L['riegel_nase_y']          # Achse bis Nase
    L['riegel_y'] = (L['riegel_nase_y'], yp)         # Leiste, dazu die Nabe
    L['riegel_z'] = (zp - rh, zp + rh)
    L['lager_x'] = (L['riegel_x'][1], L['riegel_x'][1] + w('lager_t'))
    L['lager_z'] = (L['tisch_z'], zp + w('lager_ueber'))
    L['ausleger_x'] = (x1, L['lager_x'][1])
    L['ausleger_y'] = (ai, yp + L['riegel_l'] + 1.0)  # offen liegt er darauf
    L['ausleger_z'] = (L['tisch_z'], L['tisch_z'] + w('ausleger_t'))
    L['endplatte_y'] = (L['fuehrung_y']['vorn'],
                        max(L['ausleger_y'][1], L['quer_y']['vorn'][1]))
    # Sechskantkopf auf der Plattenseite in einer Tasche, 0,5 mm unter der
    # Flaeche; hinter dem Lagerbock Scheibe und Stoppmutter. Laenge auf
    # 5 mm aufgerundet.
    L['riegel_tasche_t'] = w('m5_sk_k') + 0.5
    L['riegel_tasche_sw'] = w('m5_sw') + w('sk_spiel')
    noetig = (w('riegel_dicke') - L['riegel_tasche_t'] + w('lager_t')
              + w('m5_scheibe_h') + w('m5_mutter_h') + w('ueberstand'))
    L['riegel_schraube'] = 5.0 * math.ceil(noetig / 5.0)

    # ---- Bauraum je Halter: links reicht der Anschlag vor die Fuehrung,
    #      vorn rechts Endplatte, Ausleger und Lagerbock nach rechts und vorn
    L['halter_bb_x'], L['halter_bb_y'] = {}, {}
    for s in SEITEN:
        for e in ENDEN:
            n = halter_name(s, e)
            x, y = L['halter_x'][e], L['innen_y'][s]
            if e == 'links':
                a = L['anschlag_y'][s]
                y = (min(y[0], a[0]), max(y[1], a[1]))
            if (s, e) == RIEGEL_AN:
                x = (x[0], L['ausleger_x'][1])
                y = (min(y[0], L['endplatte_y'][0]),
                     max(y[1], L['endplatte_y'][1]))
            L['halter_bb_x'][n], L['halter_bb_y'][n] = x, y
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
              'Spanplatte': 0.65}              # die Opferplatte


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


def sechseck(cu, cv, sw):
    """Ecken eines regelmaessigen Sechsecks mit der Schluesselweite sw um
    (cu, cv), zwei Flanken parallel zu u (wie sechskant in ToolheadZ.py)."""
    r = sw / math.sqrt(3.0)                      # Umkreisradius
    return [(cu + r * math.cos(math.radians(i * 60.0)),
             cv + r * math.sin(math.radians(i * 60.0))) for i in range(6)]


def prisma_vieleck(comp, name, achse, punkte, a0, a1, art, ziel=None):
    """Vieleck quer zu `achse` (u, v wie bei prismen), entlang `achse` von a0
    bis a1, symmetrisch um die Mitte extrudiert."""
    m = (a0 + a1) / 2.0
    sk = skizze(comp, _ebene(comp, achse, m, 'E_{}_{}{:.1f}'.format(
        comp.name, achse.upper(), m)), 'Sk_' + name)
    vieleck(sk, punkte)
    return _symmetrisch(comp, groesstes_profil(sk), abs(a1 - a0), _op(art),
                        ziel)


def bau_halter(app, design, comp, L, s, e, fehler):
    """Halter innen an einem Ende eines 2060 (s = 'vorn' | 'hinten', e =
    'links' | 'rechts'), steht auf dem Tisch: schmal (vorn) ein voller
    Block mit versenkten M5, breit (hinten) Flansch am 2060, Boden und
    Fuehrungswand. Links der Anschlag fuer das Plattenende, rechts die
    Einfuehrschraege. Vorn rechts dazu die Endplatte vor dem Ende des
    2060 mit Ausleger und Lagerbock fuer den Riegel.

    Drucklage: Unterseite (Tischseite) aufs Bett. Block, Flansch, Wand,
    Anschlag, Endplatte und Lagerbock stehen senkrecht, die M5-Loecher und
    die Senkungen waagerecht — keine Stuetzen."""
    name = halter_name(s, e)
    x, tz = L['halter_x'][e], L['tisch_z']
    if L['voll'][s]:
        k = quader(comp, 'Block_' + name, x, L['innen_y'][s], L['halter_z'],
                   'neu').bodies.item(0)
    else:
        k = quader(comp, 'Wand_' + name, x, L['wand_y'][s], L['halter_z'],
                   'neu').bodies.item(0)
        quader(comp, 'Boden_' + name, x, L['boden_y'][s],
               (tz, tz + w('boden_t')), 'dazu', k)
        quader(comp, 'Flansch_' + name, x, L['flansch_y'][s], L['flansch_z'],
               'dazu', k)
    k.name = name
    if e == 'links':
        quader(comp, 'Anschlag_' + name, L['anschlag_x'], L['anschlag_y'][s],
               L['anschlag_z'], 'dazu', k)
    else:
        if (s, e) == RIEGEL_AN:
            quader(comp, 'Endplatte_' + name, L['endplatte_x'],
                   L['endplatte_y'], L['endplatte_z'], 'dazu', k)
        prisma_vieleck(comp, 'Einfuehrung_' + name, 'z', L['einfuehr_pkt'][s],
                       tz - 1.0, L['halter_z'][1] + 1.0, 'weg', k)
    if (s, e) == RIEGEL_AN:
        # Ausleger flach auf dem Tisch nach rechts (erst nach der Schraege,
        # sonst kerbt deren Schnitt ihn an), darauf der Lagerbock mit dem
        # Loch fuer die Achse des Riegels
        quader(comp, 'Ausleger_' + name, L['ausleger_x'], L['ausleger_y'],
               L['ausleger_z'], 'dazu', k)
        quader(comp, 'Lagerbock_' + name, L['lager_x'], L['lager_y'],
               L['lager_z'], 'dazu', k)
        bohrung(comp, 'Achse_' + name, 'x', [L['riegel_achse']],
                w('m5_durchgang'), L['lager_x'][0] - 1.0,
                L['lager_x'][1] + 1.0, k)
    # 2x M5 waagerecht in die innere untere Seitennut; im vollen Block mit
    # Senkung fuer den Kopf von der Plattenseite
    zn = L['nut_seite_z']
    punkte = [(mx, zn) for mx in L['m5_x'][e]]
    y = L['innen_y'][s] if L['voll'][s] else L['flansch_y'][s]
    bohrung(comp, 'M5_' + name, 'y', punkte, w('m5_durchgang'), y[0] - 1.0,
            y[1] + 1.0, k)
    if L['voll'][s]:
        g, aus = L['fuehrung_y'][s], L['aus'][s]
        bohrung(comp, 'Senkung_' + name, 'y', punkte, w('senk_d'),
                g - aus * 1.0, L['auflage_y'][s], k)
    fussfase(comp, k, 'y', tz, w('fase_fuss'), fehler, name.replace('_', ' '))
    bbox_pruefen(k, name.replace('_', ' '),
                 (L['halter_bb_x'][name], L['halter_bb_y'][name],
                  L['halter_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_riegel(app, design, comp, L, fehler):
    """Klappriegel vor dem rechten Plattenende: Leiste mit runder Nabe um
    die Achse, M5 laengs X. Der Sechskantkopf sitzt auf der Plattenseite in
    einer Tasche und dreht sich mit dem Riegel. Gebaut in der Lage 'zu'
    (Nase nach hinten vor dem Plattenende); offen ist er um 180 Grad nach
    vorn umgeklappt.

    Drucklage: Seite ohne Tasche (zum Lagerbock) aufs Bett, die Bohrung
    steht senkrecht — keine Stuetzen."""
    rx, (yp, zp) = L['riegel_x'], L['riegel_achse']
    k = quader(comp, 'Leiste_Riegel', rx, L['riegel_y'], L['riegel_z'],
               'neu').bodies.item(0)
    k.name = 'Riegel'
    zylinder(comp, 'Nabe_Riegel', 'x', (yp, zp), w('riegel_h'), rx[0], rx[1],
             'dazu', k)
    bohrung(comp, 'Achse_Riegel', 'x', [(yp, zp)], w('m5_durchgang'),
            rx[0] - 1.0, rx[1] + 1.0, k)
    prisma_vieleck(comp, 'Kopftasche_Riegel', 'x',
                   sechseck(yp, zp, L['riegel_tasche_sw']), rx[0] - 1.0,
                   rx[0] + L['riegel_tasche_t'], 'weg', k)
    fussfase(comp, k, 'x', rx[1], w('fase_fuss'), fehler, 'Riegel')
    bbox_pruefen(k, 'Riegel',
                 (rx, (L['riegel_y'][0], yp + w('riegel_h') / 2.0),
                  L['riegel_z']), fehler)
    material_zuweisen(app, design, k, 'PETG', fehler)
    return k


def bau_platte(app, design, comp, L, fehler):
    """Die Opferplatte (Spanplatte, vorhanden): nur fuer Ansicht, Masse und
    Pruefung — nicht drucken."""
    k = quader(comp, 'Platte', L['platte_x'], L['platte_y'], L['platte_z'],
               'neu').bodies.item(0)
    k.name = 'Opferplatte'
    bbox_pruefen(k, 'Opferplatte',
                 (L['platte_x'], L['platte_y'], L['platte_z']), fehler)
    material_zuweisen(app, design, k, 'Spanplatte', fehler)
    return k


def bau_referenz(app, design, teile, L, fehler):
    """Die beiden 2060 und die beiden 2040 — nur zur Ansicht, NICHT drucken.
    Jedes Profil wird fuer sich gebaut: scheitert eines, steht das im
    Bericht."""
    R, b = L['R'], w('rahmen_b')

    def sicher(name, bauen, *args):
        try:
            return bauen(*args)
        except Exception:
            fehler.append('Referenz {} nicht gebaut: {}'.format(
                name, traceback.format_exc().strip().splitlines()[-1]))
            return None

    pr = teile['Ref_Rahmen']
    profile = [('2060_{}'.format(s), 'x', L['quer_x'], L['quer_y'][s],
                L['quer_z']) for s in SEITEN]
    profile += [('2040_{}'.format(e), 'y', L['rahmen_y'],
                 (sx * R - b / 2.0, sx * R + b / 2.0), L['rahmen_z'])
                for e, sx in (('links', -1), ('rechts', 1))]
    for name, laengs, bereich, quer, z in profile:
        k = sicher(name, bau_profil, pr, name, laengs, bereich, quer, z)
        if k:
            material_zuweisen(app, design, k, 'Aluminum 6061', fehler)


def hinweise_bauen(L, fehler):
    """Hinweiszeilen des Validierungsberichts. Modulebene, damit der Block
    ohne Fusion getestet werden kann (tools/opferplatte_check.py)."""
    px, py, pz = L['platte_x'], L['platte_y'], L['platte_z']
    yp, zp = L['riegel_achse']
    hl, hr = L['halter_x']['links'], L['halter_x']['rechts']
    sv, sh = L['m5_schraube']['vorn'], L['m5_schraube']['hinten']
    h = [
        'BEZUG: Maschinenkoordinaten wie Portal.py (X rechts, Y nach vorn,',
        '  Z = 0 Rohrmitte), Portal in der Mitte seines Wegs.',
        '',
        'TISCH: Maschine und Opferplatte stehen auf demselben Tisch',
        '  (Unterkante der 2060, Z {:+.0f}). Fuesse gibt es nicht (bis'.format(
            L['tisch_z']),
        '  Rev. 3 standen sie im Modell, an der Maschine nie).',
        '',
        'HALTER (4, PETG): innen an den Enden der beiden 2060, X {:+.0f}'
        .format(hl[0]),
        '  bis {:+.0f} und {:+.0f} bis {:+.0f}, auf dem Tisch. Je 2x M5 in '
        'Hammer-'.format(hl[1], hr[0], hr[1]),
        '  muttern der INNEREN unteren Seitennut (Z {:+.0f}). Sie fuehren'
        .format(L['nut_seite_z']),
        '  die Platte in Y, {:.1f} mm Luft je Seite.'.format(
            w('platte_spiel')),
        '  vorn: voller Block {:.2f} mm breit, M5x{:.0f} OHNE Scheibe in einer'
        .format(L['innen_y']['vorn'][1] - L['innen_y']['vorn'][0], sv),
        '    Senkung von der Plattenseite',
        '  hinten: Flansch am 2060, Boden und Wand, M5x{:.0f} + Scheibe'
        .format(sh),
        '  Anschlag_vorn/_hinten (links): ANSCHLAG {:.0f} mm vor das'.format(
            w('anschlag_tief')),
        '    Plattenende, {:.1f} mm unter der Oberflaeche.'.format(
            pz[1] - L['anschlag_z'][1]),
        '  Fuehrung_vorn/_hinten (rechts): EINFUEHRSCHRAEGE {:.0f} mm, 45'
        .format(w('einfuehr')),
        '    Grad. Fuehrung_vorn traegt vor dem Ende des 2060 die Endplatte',
        '    mit dem Ausleger bis X {:+.0f} und dem Lagerbock fuer den Riegel.'
        .format(L['ausleger_x'][1]),
        '',
        'RIEGEL (PETG) vor dem rechten Plattenende: dreht sich um eine M5',
        '  laengs X (Y {:+.1f}, Z {:+.1f}). Zu greift er {:.0f} mm vor das'
        .format(yp, zp, w('riegel_ueber')),
        '  Plattenende, {:.1f} mm Luft. Ein Stoss gegen die Platte drueckt'
        .format(w('riegel_spiel')),
        '  ihn laengs der Achse an den Lagerbock: aufklappen kann er so',
        '  nicht. Offen liegt er um 180 Grad nach vorn umgeklappt auf dem',
        '  Ausleger, zu liegt er hinten auf dessen Kante; beide Male haelt',
        '  ihn die Schwerkraft. Zwischen Anschlag und Riegel sind {:.1f} mm:'
        .format(L['riegel_x'][0] - L['anschlag_x'][1]),
        '  laenger darf die Platte nicht sein.',
        '',
        'OPFERPLATTE (Spanplatte {:.0f} x {:.0f} x {:.1f}, vorhanden): liegt '
        'auf'.format(w('platte_l'), w('platte_b'), w('platte_dicke')),
        '  dem Tisch zwischen den Haltern, Y {:+.1f} bis {:+.1f} (mittig'
        .format(py[0], py[1]),
        '  unter dem Arbeitsfeld), X {:+.1f} bis {:+.1f}: links am Anschlag,'
        .format(px[0], px[1]),
        '  rechts steht sie {:.0f} mm ueber das Gestell, dort herausziehen.'
        .format(L['platte_ueber']),
        '  Oberflaeche Z {:+.1f}, {:.1f} mm ueber der Unterkante der 2060.'
        .format(pz[1], pz[1] - L['z_2060']),
        '  Z ganz unten und die Werkstueckhoehe rechnet ToolheadZ.py',
        '  (bett_abstand, Softlimit $132).',
        '',
        'MONTAGE (ohne Platte):',
        '  1. 8 Hammermuttern M5 in die untere Seitennut INNEN an beiden',
        '     2060, je 2 nahe jedem Ende.',
        '  2. Halter innen an das Ende stellen, auf den Tisch und ans',
        '     Profil: vorn 2x M5x{:.0f} ohne Scheibe in die Senkungen, hinten'
        .format(sv),
        '     2x M5x{:.0f} + Scheibe durch den Flansch. Fuehrung_vorn mit'
        .format(sh),
        '     der Endplatte am Ende des 2060.',
        '  3. Riegel: Sechskantschraube M5x{:.0f} (ISO 4017) von links'
        .format(L['riegel_schraube']),
        '     (Plattenseite) durch Riegel und Lagerbock, der Kopf in die',
        '     Tasche; rechts Scheibe + Stoppmutter M5 (DIN 985). Mit SW 8',
        '     so fest, dass er nicht wackelt, aber von Hand klappt.',
        '  4. Riegel nach vorn klappen, Platte von rechts zwischen die',
        '     Halter schieben, bis sie links am Anschlag steht, Riegel',
        '     zurueckklappen. Herausnehmen: Riegel nach vorn, Platte nach',
        '     rechts ziehen.',
        '',
        'DRUCK (PETG, Bambu Lab A1): Halter mit der Unterseite',
        '  (Tischseite) aufs Bett, Block, Wand, Anschlag, Endplatte und',
        '  Lagerbock stehen senkrecht. Riegel mit der Seite ohne Tasche',
        '  aufs Bett. Keine Stuetzen, 4 Wandlinien, 20 % Infill. Vier',
        '  verschiedene Halter: links mit Anschlag, rechts mit Schraege,',
        '  vorn voll, hinten mit Flansch, vorn rechts mit Endplatte.',
        '',
        'KEINE BOHRLEHRE: Die Halter gehen in Hammermuttern, die Achse des',
        '  Riegels ist ein einzelnes gedrucktes Loch je Teil.',
        '',
        'GEMESSEN (2026-10-02): Platte {:.1f} mm dick (Nennmass 25).'.format(
            w('platte_dicke')),
        '  NICHT GEMESSEN: ob die innere untere Seitennut an den Enden der',
        '  2060 frei ist.',
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
        for s in SEITEN:
            for e in ENDEN:
                o = root.occurrences.addNewComponent(einheit)
                o.component.name = halter_name(s, e)
                bau_halter(app, design, o.component, L, s, e, fehler)
                o.isGrounded = True

        # Der Riegel steht in der Lage 'zu'; offen ist er um 180 Grad um
        # seine Achse nach vorn geklappt (tools/opferplatte_zeichnen.py)
        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Riegel'
        bau_riegel(app, design, o.component, L, fehler)
        o.isGrounded = True

        o = root.occurrences.addNewComponent(einheit)
        o.component.name = 'Opferplatte'
        bau_platte(app, design, o.component, L, fehler)
        o.isGrounded = True

        ref = root.occurrences.addNewComponent(einheit)
        ref.component.name = 'Referenz_nicht_drucken'
        teile = {}
        for name in ('Ref_Rahmen',):
            oo = ref.component.occurrences.addNewComponent(einheit)
            oo.component.name = name
            teile[name] = oo.component
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
