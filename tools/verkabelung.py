#!/usr/bin/env python3
"""Kabelliste der Maschine — eine Quelle fuer Anleitung, Anschlussplan und
Pruefung.

Jede Leitung steht hier genau einmal: ihre Adern mit Farbe und Anschluss an
beiden Enden, Querschnitt, Weg und Kauflaenge. Die Wege an der Maschine
kommen aus den Kabelwegen in tools/elektronik_zeichnen.py (Rahmen, Portal,
Toolhead, Gehaeuse und Endschalter aus den Fusion-Skripten), die
Querschnitte aus dessen Litzen-Konstanten, die GRBL-Wege aus Portal,
Toolhead und Endschalter.

    python3 tools/verkabelung.py   ->  Tabellen in docs/verkabelung.md neu

Die Tabellen stehen in der Anleitung zwischen Markierungen
(<!-- tabelle:NAME --> ... <!-- /tabelle:NAME -->); nur dort wird
geschrieben. tools/elektronik_check.py (Abschnitt 15) prueft Kontakte,
Klemmen, Pins und Laengen und dass die Tabellen in der Anleitung aktuell
sind.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import elektronik_zeichnen as ez                      # noqa: E402
from antrieb_zeichnen import de                       # noqa: E402

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
ANLEITUNG = os.path.join(DOCS, 'verkabelung.md')

# ---- Kontaktarten: welche Litzen sie nehmen (mm2) [w] ----------------------
# Datenblattwerte der ueblichen Kontakte; die Aderendhuelse gehoert in jede
# Schraubklemme, in die Wago nicht.
KONTAKT = {
    'Dupont': (0.08, 0.34),          # Crimpkontakt 2,54 mm, AWG 28-22
    'XH': (0.08, 0.34),              # JST XH, AWG 28-22
    'PH': (0.05, 0.22),              # JST PH, AWG 30-24 (am Motor)
    'Wago': (0.14, 4.0),             # 221, feindraehtig
    'Schraubklemme': (0.25, 1.5),    # mit Aderendhuelse
    'Loeten': (0.05, 1.5),           # Loetfahne, Schrumpfschlauch darueber
}
AWG = {0.14: 26, 0.2: 24, 0.25: 24, 0.34: 22, 0.5: 20, 0.75: 18, 1.0: 18}

# ---- Anschluesse: Beschriftung in der Anleitung und Kontaktart -------------
# Kontaktart None: das Geraet bringt seine Litze oder sein Kabel mit.
ANSCHLUSS = {
    'Buchse +': ('Einbaubuchse, Mittelstift (+)', 'Loeten'),
    'Buchse −': ('Einbaubuchse, Hülse (−)', 'Loeten'),
    'Schalter 1': ('Schalter, Kontakt 1', 'Loeten'),
    'Schalter 2': ('Schalter, Kontakt 2', 'Loeten'),
    # Wechsler mit Loetfahnen [v] Bild 2026-09-30: C, NO, NC
    'Not-Aus C': ('Not-Aus, C', 'Loeten'),
    'Not-Aus NC': ('Not-Aus, NC', 'Loeten'),
    'Not-Aus NO': ('Not-Aus, NO (frei)', 'Loeten'),
    'Wago +24 V': ('Wago +24 V', 'Wago'),
    'Wago GND': ('Wago GND', 'Wago'),
    'Wago +5 V': ('Wago +5 V', 'Wago'),
    'Shield +': ('Shield, Schraubklemme +', 'Schraubklemme'),
    'Shield −': ('Shield, Schraubklemme −', 'Schraubklemme'),
    'Shield 5V': ('Shield, Stift 5V', 'Dupont'),
    'Shield X−': ('Shield X− (D9), Signalstift', 'Dupont'),
    'Shield Y+': ('Shield Y+ (D10), Signalstift', 'Dupont'),
    'Shield SpnEn': ('Shield SpnEn (D12)', 'Dupont'),
    'Shield Z+': ('Shield Z+ (D11), Signalstift', 'Dupont'),
    'Shield Z− S': ('Shield Z− (D11), Signalstift', 'Dupont'),
    'Shield Z− GND': ('Shield Z−, GND-Stift', 'Dupont'),
    'Shield Abort': ('Shield Abort (A0)', 'Dupont'),
    'Wandler IN+': ('Wandler IN+', 'Schraubklemme'),
    'Wandler IN−': ('Wandler IN−', 'Schraubklemme'),
    'Wandler OUT+': ('Wandler OUT+', 'Schraubklemme'),
    'Wandler OUT−': ('Wandler OUT−', 'Schraubklemme'),
    'Lüfter +': ('Lüfter, rote Litze', None),
    'Lüfter −': ('Lüfter, schwarze Litze', None),
    'Laser PWM': ('Laser, XH links: PWM', 'XH'),
    'Laser GND': ('Laser, XH Mitte: GND', 'XH'),
    'Laser +12 V': ('Laser, XH rechts: +12 V', 'XH'),
    'Uno USB': ('Uno, USB-B', None),
    # Pi auf dem Pi-Halter (docs/pi.md), mit seinem Abwaertswandler
    # 24 -> 5 V: Eingang mit Schraubklemmen, Ausgang USB-A [?]
    '5V-Wandler IN+': ('5-V-Wandler IN+', 'Schraubklemme'),
    '5V-Wandler IN−': ('5-V-Wandler IN−', 'Schraubklemme'),
    '5V-Wandler USB': ('5-V-Wandler, USB-A', None),
    'Pi PWR': ('Pi, Micro-USB „PWR IN“', None),
    'Pi USB': ('Pi, Micro-USB „USB“', None),
}
for _a in ('X', 'Y', 'Z'):
    ANSCHLUSS['LS {} VCC'.format(_a)] = ('Lichtschranke {}, VCC'.format(_a),
                                         'Dupont')
    ANSCHLUSS['LS {} GND'.format(_a)] = ('Lichtschranke {}, GND'.format(_a),
                                         'Dupont')
    ANSCHLUSS['LS {} D0'.format(_a)] = ('Lichtschranke {}, D0'.format(_a),
                                        'Dupont')
# Motoren: je Spule ein Adernpaar. Am Shield liegen die Paare 2B·2A und
# 1A·1B nebeneinander, am Motor sitzt der PH-Stecker des Herstellers.
for _s in ('X', 'Y', 'Z', 'A'):
    ANSCHLUSS['Shield {} 2B·2A'.format(_s)] = (
        'Shield Motor {}, 2B · 2A'.format(_s), 'Dupont')
    ANSCHLUSS['Shield {} 1A·1B'.format(_s)] = (
        'Shield Motor {}, 1A · 1B'.format(_s), 'Dupont')
# Stecker ab Werk [v]: außen schwarz und rot, innen grün und blau, also
# A+ · A− · B− · B+. Mit Schwarz an 2B passt er ohne Umstecken.
MOTOR_STECKER = ('A+', 'A−', 'B−', 'B+')
for _m in ('X-Motor', 'Y-Motor links', 'Y-Motor rechts', 'Z-Motor'):
    ANSCHLUSS[_m + ' A'] = (_m + ', Spule A: A+ · A−', 'PH')
    ANSCHLUSS[_m + ' A getauscht'] = (_m + ', Spule A: A− · A+', 'PH')
    ANSCHLUSS[_m + ' B'] = (_m + ', Spule B: B− · B+', 'PH')

# Klemmleisten im Verteiler (Bestand [v], Plaetze nach Datenblatt [w])
WAGO = (('Wago +24 V', '221-415', 5), ('Wago GND', '221-420', 10),
        ('Wago +5 V', '221-420', 10))
# Frei halten fuer einen Wandler mit getrennten Massen (OUT− an GND)
WAGO_RESERVE = {'Wago GND': 1}

# Shield V3 unter GRBL 1.1 (hardware-notizen.md, Pins): Stift, Uno-Pin,
# Aufgabe. Z+ und Z− liegen beide auf D11 (Laser-PWM), X+/X− beide auf D9,
# Y+/Y− beide auf D10.
SHIELD = (
    ('Shield +', '—', '24 V für die Treiber (12–36 V)'),
    ('Shield −', '—', 'GND'),
    ('Shield 5V', '5 V', 'Versorgung der Lichtschranken (vom USB des Uno)'),
    ('Shield X−', 'D9', 'Endschalter X (X+ ist derselbe Pin)'),
    ('Shield Y+', 'D10', 'Endschalter Y (Y− ist derselbe Pin)'),
    ('Shield SpnEn', 'D12', 'Endschalter Z — GRBL 1.1 legt ihn auf D12'),
    ('Shield Z+', 'D11', 'Laser-PWM — kein Endschalter'),
    ('Shield Z− S', 'D11', 'Pull-down 10 kΩ zum GND-Stift daneben'),
    ('Shield Abort', 'A0', '24-V-Wächter: ohne 24 V bricht GRBL ab'),
)
EINGAENGE = {'Shield X−': 'X', 'Shield Y+': 'Y', 'Shield SpnEn': 'Z'}

# Stromaufnahme aus 5 V [w]: stehen in tools/elektronik_zeichnen.py, weil
# die Leistungsbilanz den Pi mitrechnet
USB_MA = ez.USB_MA                  # Polyfuse am USB-Eingang des Uno
LS_MA = ez.LS_MA
UNO_MA = ez.UNO_MA
TREIBER_LOGIK_MA = ez.TREIBER_LOGIK_MA

SIG = ez.LITZE_SIGNAL


def leitungen():
    """Alle Leitungen in der Reihenfolge der Anleitung. Adern:
    (Funktion, Farbe, von, an); von/an sind Schluessel in ANSCHLUSS."""
    kasten = 0.15            # m, im Kasten ablaengen
    return [
        dict(nr='W1', name='Eingang', art='Einzeladern',
             mm2=ez.LITZE_24V, laenge=kasten, strom=3.0,
             weg='im Kasten',
             adern=[('+24 V', 'rot', 'Buchse +', 'Schalter 1'),
                    ('GND', 'schwarz', 'Buchse −', 'Wago GND')]),
        dict(nr='W2', name='Not-Aus-Kreis', art='Leitung 2-adrig',
             mm2=ez.LITZE_24V, kabel='Not-Aus', strom=3.0,
             weg='vorn raus, Kanal, Rückseite hinteres 2060, untere Nut '
                 'außen am rechten 2040 nach vorn, obere Nut vorn am 2060 '
                 'zum Gehäuse',
             hinweis='beide Adern führen +24 V: an beiden Enden rot '
                     'markieren; NO bleibt frei',
             adern=[('+24 V hin', 'Ader 1', 'Schalter 2', 'Not-Aus C'),
                    ('+24 V zurück', 'Ader 2', 'Not-Aus NC',
                     'Wago +24 V')]),
        dict(nr='W3', name='Shield', art='Einzeladern', mm2=ez.LITZE_24V,
             laenge=kasten, strom=3.0, weg='im Kasten',
             adern=[('+24 V', 'rot', 'Wago +24 V', 'Shield +'),
                    ('GND', 'schwarz', 'Wago GND', 'Shield −')]),
        dict(nr='W4', name='Wandler-Eingang', art='Einzeladern',
             mm2=ez.LITZE_24V, laenge=kasten, strom=1.0, weg='im Kasten',
             adern=[('+24 V', 'rot', 'Wago +24 V', 'Wandler IN+'),
                    ('GND', 'schwarz', 'Wago GND', 'Wandler IN−')]),
        dict(nr='W5', name='Lüfter 24 V', art='Litze des Lüfters', mm2=None,
             strom=0.1, weg='im Kasten, durch die Öffnung im Deckel',
             hinweis='Litze dünner als 0,14 mm²: abisoliert doppelt legen',
             adern=[('+24 V', 'rot', 'Lüfter +', 'Wago +24 V'),
                    ('GND', 'schwarz', 'Lüfter −', 'Wago GND')]),
        dict(nr='W6', name='5 V für die Lichtschranken', art='Einzelader',
             mm2=SIG, laenge=kasten, strom=0.1, weg='im Kasten',
             adern=[('+5 V', 'rot', 'Shield 5V', 'Wago +5 V')]),
        dict(nr='W7', name='Laser', art='Litzen 3-adrig, Silikon',
             mm2=ez.LITZE_LASER, kabel='Laser (12 V + PWM)',
             strom=ez.LASER_A, kette='Y + X',
             weg='links raus, untere Nut außen am linken 2040, hinten in die '
                 'Y-Kette, hinter dem Schlitten in die obere Nut des Rohrs, '
                 'am Kabelflügel hoch in die X-Kette, Trägerplatte',
             adern=[('+12 V', 'rot', 'Wandler OUT+', 'Laser +12 V'),
                    ('GND', 'schwarz', 'Wandler OUT−', 'Laser GND'),
                    ('PWM', 'weiß', 'Shield Z+', 'Laser PWM')]),
        dict(nr='W8', name='Pull-down 10 kΩ', art='Widerstand', mm2=None,
             weg='auf dem Shield',
             hinweis='hält den Laser aus, solange der Uno startet oder '
                     'ohne USB ist',
             adern=[('10 kΩ', '—', 'Shield Z− S', 'Shield Z− GND')]),
        dict(nr='W9', name='Lichtschranke X', art='Litzen 3-adrig, Silikon',
             mm2=SIG, kabel='X-Endschalter', strom=0.03, kette='Y',
             weg='links raus, untere Nut außen am linken 2040, Y-Kette, '
                 'hinter dem Schlitten über das Rohr nach vorn zum Halter X',
             adern=[('+5 V', 'rot', 'Wago +5 V', 'LS X VCC'),
                    ('GND', 'schwarz', 'Wago GND', 'LS X GND'),
                    ('Signal', 'gelb', 'Shield X−', 'LS X D0')]),
        dict(nr='W10', name='Lichtschranke Y', art='Leitung 3-adrig',
             mm2=SIG, kabel='Y-Endschalter', strom=0.03,
             weg='vorn raus, Kanal, Rückseite hinteres 2060, untere Nut '
                 'außen am rechten 2040 nach hinten',
             adern=[('+5 V', 'rot', 'Wago +5 V', 'LS Y VCC'),
                    ('GND', 'schwarz', 'Wago GND', 'LS Y GND'),
                    ('Signal', 'gelb', 'Shield Y+', 'LS Y D0')]),
        dict(nr='W11', name='Lichtschranke Z', art='Litzen 3-adrig, Silikon',
             mm2=SIG, kabel='Z-Endschalter', strom=0.03, kette='Y + X',
             weg='wie W7 bis zur Trägerplatte, dann zum Halter am Toolhead',
             adern=[('+5 V', 'rot', 'Wago +5 V', 'LS Z VCC'),
                    ('GND', 'schwarz', 'Wago GND', 'LS Z GND'),
                    ('Signal', 'gelb', 'Shield SpnEn', 'LS Z D0')]),
        dict(nr='W12', name='X-Motor', art='Motorkabel 4-adrig',
             mm2=ez.LITZE_MOTOR, kabel='X-Motor', strom=ez.MOTOR_I,
             kette='Y', fertig=True, mitgeliefert=1.0,
             hinweis='in der Kette nur die losen Adern, ohne Schlauch',
             weg='links raus, untere Nut außen am linken 2040, Y-Kette, '
                 'hinter dem Motorhalter hoch zum Motor',
             adern=[('Spule A', 'schwarz · grün', 'Shield X 2B·2A',
                     'X-Motor A'),
                    ('Spule B', 'blau · rot', 'Shield X 1A·1B',
                     'X-Motor B')]),
        dict(nr='W13', name='Y-Motor links', art='Motorkabel 4-adrig',
             mm2=ez.LITZE_MOTOR, kabel='Y-Motor links', strom=ez.MOTOR_I,
             fertig=True, mitgeliefert=1.0,
             weg='links raus, untere Nut außen am linken 2040 nach vorn; in '
                 'den Kabelhaltern unter den Wänden der drei Träger der Wanne '
                 'Y durch',
             adern=[('Spule A', 'schwarz · grün', 'Shield Y 2B·2A',
                     'Y-Motor links A'),
                    ('Spule B', 'blau · rot', 'Shield Y 1A·1B',
                     'Y-Motor links B')]),
        dict(nr='W14', name='Y-Motor rechts', art='Motorkabel 4-adrig',
             mm2=ez.LITZE_MOTOR, kabel='Y-Motor rechts', strom=ez.MOTOR_I,
             fertig=True, mitgeliefert=1.0,
             weg='vorn raus, Kanal, Rückseite hinteres 2060, untere Nut '
                 'außen am rechten 2040 nach vorn',
             hinweis='Spule A getauscht: dreht gegen den linken',
             adern=[('Spule A, getauscht', 'grün · schwarz',
                     'Shield A 2B·2A', 'Y-Motor rechts A getauscht'),
                    ('Spule B', 'blau · rot', 'Shield A 1A·1B',
                     'Y-Motor rechts B')]),
        dict(nr='W15', name='Z-Motor', art='Motorkabel 4-adrig',
             mm2=ez.LITZE_MOTOR, kabel='Z-Motor', strom=ez.MOTOR_I,
             kette='Y + X', fertig=True, mitgeliefert=1.0,
             hinweis='in den Ketten nur die losen Adern, ohne Schlauch',
             weg='wie W7 bis zur Trägerplatte, dann zum Motor oben',
             adern=[('Spule A', 'schwarz · grün', 'Shield Z 2B·2A',
                     'Z-Motor A'),
                    ('Spule B', 'blau · rot', 'Shield Z 1A·1B',
                     'Z-Motor B')]),
        dict(nr='W16', name='24-V-Wächter an Abort', art='Widerstand',
             mm2=None, weg='im Kasten',
             hinweis='fehlen die 24 V hinter Schalter und Not-Aus, bricht '
                     'GRBL ab',
             adern=[('R1 22 kΩ', '—', 'Wago +24 V', 'Shield Abort'),
                    ('R2 4,7 kΩ ∥ 100 nF', '—', 'Shield Abort',
                     'Wago GND')]),
        dict(nr='W17', name='USB zum Pi', art='USB-Kabel Micro-B–B (OTG)',
             mm2=None, fertig=True, kabel='USB Pi–Uno',
             weg='hinten aus dem USB-Fenster, hinter dem Kasten nach rechts, '
                 'an seiner rechten Wand nach vorn zum Pi-Halter',
             hinweis='Micro-B in die Buchse „USB“ des Pi, nicht in „PWR IN“',
             adern=[('USB', '—', 'Uno USB', 'Pi USB')]),
        dict(nr='W18', name='24 V für den Pi', art='Leitung 2-adrig',
             mm2=ez.LITZE_24V, kabel='Pi 24 V', strom=3.0,
             weg='an der Buchse gelötet, vorn raus, Kanal, an der Rückseite '
                 'des hinteren 2060 unter dem Pi-Halter durch, dahinter hoch '
                 'zum 5-V-Wandler',
             hinweis='vor Schalter und Not-Aus: Pi und Uno bleiben an',
             adern=[('+24 V', 'rot', 'Buchse +', '5V-Wandler IN+'),
                    ('GND', 'schwarz', 'Buchse −', '5V-Wandler IN−')]),
        dict(nr='W19', name='5 V für den Pi', art='USB-Kabel A–Micro-B',
             mm2=None, fertig=True, kabel='Pi 5 V',
             weg='am Pi-Halter: vom USB-Ausgang des Wandlers in „PWR IN“',
             hinweis='Stromadern mindestens AWG 24, sonst meldet der Pi '
                     'Unterspannung',
             adern=[('5 V', '—', '5V-Wandler USB', 'Pi PWR')]),
    ]


# Verbindungen in den Geraeten: (a, b, wann) — wann None: immer, sonst der
# Zustand, in dem sie besteht. Widerstaende verbinden nicht.
INNEN = (
    ('Schalter 1', 'Schalter 2', 'ein'),
    ('Not-Aus C', 'Not-Aus NC', 'nicht gedrueckt'),
    ('Not-Aus C', 'Not-Aus NO', 'gedrueckt'),
    ('Wandler IN−', 'Wandler OUT−', None),        # gemeinsame Masse [w]
    ('Shield −', 'Shield Z− GND', None),          # GND des Shields
    ('Shield Z+', 'Shield Z− S', None),           # beide D11
    ('Pi PWR', 'Pi USB', None),         # 5 V des Pi an beiden Buchsen [w]
    ('Uno USB', 'Shield 5V', None),     # 5 V vom USB auf den 5-V-Stift [w]
)
BETRIEB = ('ein', 'nicht gedrueckt')

# 24-V-Waechter an Abort (A0): Spannungsteiler vom +24 V hinter dem Not-Aus.
# Fehlen die 24 V, zieht R2 den Eingang auf LOW, und GRBL bricht ab —
# gleich, ob der Not-Aus gedrueckt, der Schalter aus oder das Netzteil ab
# ist. ATmega328P [w] (Datenblatt): Pull-up 20-50 kOhm, LOW bis 0,3 x VCC,
# HIGH ab 0,6 x VCC.
WAECHTER_R1, WAECHTER_R2 = 22e3, 4.7e3
PULLUP = (20e3, 50e3)
VCC, V_IL, V_IH = 5.0, 1.5, 3.0
NETZ_TOLERANZ = 0.05        # 24 V +- 5 %

# Not-Aus: Kontakte 3 A / 250 V [v] (Angabe 2026-09-30), wie bei solchen
# Tastern ein Wechselstromwert. Bei 24 V Gleichstrom genuegt das fuer die
# Dauerlast der Maschine von gut 2 A [w]; elektronik_check.py vergleicht.
NOTAUS_A, NOTAUS_V = 3.0, 250.0


def waechter_spannung(u24, r_pullup):
    """Spannung an A0 (V): Knoten aus R1 zu u24, R2 zu GND und dem
    Pull-up zu VCC."""
    g = 1.0 / WAECHTER_R1 + 1.0 / WAECHTER_R2 + 1.0 / r_pullup
    return (u24 / WAECHTER_R1 + VCC / r_pullup) / g
# Energieketten: gedruckt (Portal.py, seit Rev. 19), innen 10 x 8,8 mm,
# Biegeradius 20 mm (Schleife gemessen, seit Rev. 22). Darin nur
# Einzellitzen — eine Mantelleitung ist fuer den Radius zu steif.
# Aussendurchmesser der Silikonlitzen [w]; die mitgelieferten Motorkabel
# haben lose Adern in einem Schlauch [v] (AWG 26 [w], hier wie 0,2 mm2
# gerechnet), der Schlauch kommt ab. Fuellgrad hoechstens 60 % [w].
ADER_D = {0.34: 1.7, 0.25: 1.5, 0.2: 1.4}
FUELLGRAD_MAX = 0.6


def kette_querschnitt():
    """Lichter Querschnitt der Kette in mm2 (Portal.py)."""
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    return pm.w('kette_innen_b') * pm.w('kette_innen_h')


def kette_fuellung(lts, kette):
    """(Adern, Flaeche in mm2) aller Adern in der Kette 'Y' oder 'X'.
    Ein Motorkabel hat vier Adern (zwei Paare in den Adernlisten)."""
    adern, flaeche = 0, 0.0
    for lt in lts:
        if kette not in lt.get('kette', '').split():
            continue
        n = 4 if lt['art'].startswith('Motorkabel') else len(lt['adern'])
        d = ADER_D[lt['mm2']]
        adern += n
        flaeche += n * math.pi * d * d / 4.0
    return adern, flaeche


def netze(zustand=BETRIEB, lts=None):
    """{Anschluss: Menge der Anschluesse im selben Netz}, gebildet aus den
    Adern und den Verbindungen in den Geraeten im gegebenen Zustand."""
    eltern = {}

    def finde(a):
        eltern.setdefault(a, a)
        while eltern[a] != a:
            eltern[a] = eltern[eltern[a]]
            a = eltern[a]
        return a

    def vereinen(a, b):
        eltern[finde(a)] = finde(b)

    for lt in lts or leitungen():
        for _, _, a, b in lt['adern']:
            if lt['art'] == 'Widerstand':
                finde(a)
                finde(b)
            else:
                vereinen(a, b)
    for a, b, wann in INNEN:
        if wann is None or wann in zustand:
            vereinen(a, b)
        else:
            finde(a)
            finde(b)
    gruppen = {}
    for a in list(eltern):
        gruppen.setdefault(finde(a), set()).add(a)
    return {a: gruppen[finde(a)] for a in eltern}


def laden():
    """Rahmen, Portal, Toolhead, Gehaeuse und Endschalter wie
    tools/elektronik_zeichnen.py; liefert die Kabelwege und die Werte fuer
    GRBL."""
    th = bauraum.modul_laden()
    tw, TL = th.w, th.lage()
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    w, L = pm.w, pm.lage()
    em = bauraum.modul_laden(ez.ELEKTRONIK, 'elektronik')
    K = ez.konzept(w, L, tw, TL, em.w, em.lage())
    # die Endschalter stehen seit Rev. 15 in Portal.py
    return {'L': L, 'TL': TL, 'K': K, 'es_w': w}


def laenge_m(lt, K):
    """(Weg in m oder None, Kauflaenge in m oder None)."""
    if 'kabel' in lt:
        mm = K['kabel'][lt['kabel']][0]
        return mm / 1000.0, ez.kauflaenge(mm)
    return None, None


def enden(lts=None):
    """Alle Aderenden: (Leitung, Ader, Anschluss-Schluessel)."""
    for lt in lts or leitungen():
        for ader in lt['adern']:
            for a in (ader[2], ader[3]):
                yield lt, ader, a


def wago_belegung(lts=None):
    """{Wago-Schluessel: [(Nr, Funktion, Gegenstelle)]}."""
    bel = {n: [] for n, _, _ in WAGO}
    for lt in lts or leitungen():
        for f, _, a, b in lt['adern']:
            for hier, dort in ((a, b), (b, a)):
                if hier in bel:
                    bel[hier].append((lt['nr'], f, dort))
    return bel


def shield_belegung(lts=None):
    """{Shield-Stift: [(Nr, Funktion, Gegenstelle)]} fuer die Stifte in
    SHIELD."""
    bel = {s: [] for s, _, _ in SHIELD}
    for lt in lts or leitungen():
        for f, _, a, b in lt['adern']:
            for hier, dort in ((a, b), (b, a)):
                if hier in bel:
                    bel[hier].append((lt['nr'], f, dort))
    return bel


def grbl(Q):
    """GRBL-Einstellungen; die Wege folgen aus den Schaltpunkten: vom
    Schaltpunkt bis ans andere Ende, minus 1 mm Rueckzug und 2 mm Reserve
    (dort stuende der Wagen sonst genau am Schienenende)."""
    L, TL, K, es_w = Q['L'], Q['TL'], Q['K'], Q['es_w']
    s = es_w('schaltabstand')
    x = (L['xw_max'] - L['xw_min']) - s - 1.0 - 2.0
    y = K['d_vorn'] + K['d_schiene'] - s - 1.0 - 2.0
    z = TL['z_arbeit'] - 1.0 - 2.0
    return [
        ('$3', 'nach dem Test', 'Drehrichtung: X+ nach rechts, Y+ nach '
         'hinten, Z+ nach oben ([Motoren](#f-motoren-und-drehrichtung))'),
        ('$5', '1 `[w]`', 'Lichtschranken melden „unterbrochen“ mit HIGH; '
         'im Test prüfen ([Lichtschranken](#d-uno-grbl-und-lichtschranken))'),
        ('$20', '1', 'Softlimits an: schützen beide Enden, auch die '
         'Motorseite von Y, aber nur nach `$H` ([warum](endschalter.md'
         '#softlimits-statt-zweitem-y-schalter))'),
        ('$21', '0', 'Hardlimits aus, bis die Schalter nie falsch auslösen'),
        ('$22', '1', 'Referenzfahrt an: erst Z, dann X und Y'),
        ('$23', '1', 'X referenziert nach links (minus), Y nach hinten und '
         'Z nach oben (plus)'),
        ('$27', '1', '1 mm Rückzug vom Schalter'),
        ('$30', '1000', 'S1000 = volle Laserleistung'),
        ('$32', '1', 'Lasermodus'),
        ('$100', '80', 'X: GT2, 20 Zähne, 1/16'),
        ('$101', '80', 'Y: GT2, 20 Zähne, 1/16'),
        ('$102', '1600', 'Z: Tr8×2, 1/16'),
        ('$130', '{:.0f}'.format(math.floor(x)), 'X: {} mm vom Schaltpunkt '
         'bis ans rechte Schienenende, minus Rückzug und Reserve'.format(
             de(x + 3.0, 2))),
        ('$131', '{:.0f}'.format(math.floor(y)), 'Y: {} mm vom Schaltpunkt '
         'bis vor das vordere 2060, minus Rückzug und Reserve'.format(
             de(y + 3.0, 2))),
        ('$132', '{:.0f}'.format(math.floor(z)), 'Z: {} mm Arbeitsweg vom '
         'Schaltpunkt bis ganz unten, minus Rückzug und Reserve'.format(
             de(z + 3.0, 2))),
    ]


# ---- Tabellen fuer die Anleitung --------------------------------------------

def _mm2(x):
    return '{} mm²'.format(de(x, 2))


def _awg(mm2):
    return ' (AWG {})'.format(AWG[mm2]) if mm2 in AWG else ''


def _litze(lt):
    if lt['mm2'] is None:
        return lt['art']
    if lt['art'].startswith('Motorkabel'):
        return '4 × {}{}'.format(_mm2(lt['mm2']), _awg(lt['mm2']))
    if lt['art'].startswith('Leitung'):
        n = int(lt['art'].split()[1][0])
        return '{} × {}{}'.format(n, _mm2(lt['mm2']), _awg(lt['mm2']))
    if lt['art'].startswith('Litzen'):
        n = int(lt['art'].split()[1][0])
        return '{} Silikonlitzen {}{}'.format(n, _mm2(lt['mm2']),
                                               _awg(lt['mm2']))
    return _mm2(lt['mm2']) + _awg(lt['mm2'])


def tab_leitungen(K):
    z = ['| Nr | Leitung | Litze | Weg | Länge | kaufen | Kette |',
         '|---|---|---|---|---|---|---|']
    for lt in leitungen():
        weg, kauf = laenge_m(lt, K)
        if weg is not None:
            lang, k = '{} m'.format(de(weg, 2)), '**{} m**'.format(
                de(kauf, 2))
            if lt.get('mitgeliefert') and kauf <= lt['mitgeliefert']:
                k = 'mitgeliefert ({} m)'.format(de(lt['mitgeliefert'], 1))
            elif lt.get('fertig'):
                k += ', fertig'
        elif lt.get('laenge'):
            lang, k = '≈ {} m je Ader'.format(de(lt['laenge'], 2)), 'Rolle'
        else:
            lang, k = '—', 'vorhanden' if lt.get('fertig') else '—'
        name = '**{}**'.format(lt['name'])
        if lt.get('hinweis'):
            name += ' — ' + lt['hinweis']
        z.append('| {} | {} | {} | {} | {} | {} | {} |'.format(
            lt['nr'], name, _litze(lt), lt['weg'], lang, k,
            lt.get('kette', '') or '—'))
    return '\n'.join(z)


def tab_anschluesse():
    z = ['| Nr | Ader | Farbe | von | an |', '|---|---|---|---|---|']
    for lt in leitungen():
        for i, (f, farbe, a, b) in enumerate(lt['adern']):
            z.append('| {} | {} | {} | {} | {} |'.format(
                lt['nr'] if i == 0 else '', f, farbe, ANSCHLUSS[a][0],
                ANSCHLUSS[b][0]))
    return '\n'.join(z)


def tab_wago():
    bel = wago_belegung()
    z = ['| Klemme | Typ | belegt | frei | angeschlossen |',
         '|---|---|---|---|---|']
    for name, typ, plaetze in WAGO:
        b = bel[name]
        rest = plaetze - len(b)
        frei = str(rest)
        if WAGO_RESERVE.get(name):
            frei += ' (einer davon für OUT− eines isolierten Wandlers)'
        z.append('| **{}** | {} | {} von {} | {} | {} |'.format(
            name, typ, len(b), plaetze, frei, ' · '.join(
                '{} {}'.format(nr, ANSCHLUSS[d][0]) for nr, _, d in b)))
    return '\n'.join(z)


def tab_shield():
    bel = shield_belegung()
    z = ['| Stift | Uno-Pin | Aufgabe | angeschlossen |', '|---|---|---|---|']
    for s, pin, aufgabe in SHIELD:
        z.append('| {} | {} | {} | {} |'.format(
            ANSCHLUSS[s][0].replace('Shield, ', '').replace('Shield ', ''),
            pin, aufgabe,
            ' · '.join('{} → {}'.format(nr, ANSCHLUSS[d][0])
                       for nr, _, d in bel[s]) or '—'))
    z.append('| Motor X, Y, Z, A | — | 2B · 2A · 1A · 1B je Treiber; A '
             'klont Y (Jumper) | W12 · W13 · W15 · W14 |')
    return '\n'.join(z)


def material(K):
    """Kaufliste aus den Leitungen: Meter je Leitungsart, Kontakte je Art
    (ohne fertig konfektionierte Kabel), Aderendhuelsen je Querschnitt."""
    meter, kontakte, huelsen, gehaeuse = {}, {}, {}, {}
    for lt in leitungen():
        weg, kauf = laenge_m(lt, K)
        if lt['mm2'] is not None and not lt.get('fertig'):
            if lt['art'].startswith('Leitung'):
                meter.setdefault(_litze(lt), []).append(
                    (lt['nr'], kauf or lt.get('laenge') or 0.0))
            elif lt['art'].startswith('Litzen'):
                # in den Ketten: je Ader eine Silikonlitze in ihrer Farbe
                for _, farbe, _, _ in lt['adern']:
                    meter.setdefault('Silikonlitze {}{}, {}'.format(
                        _mm2(lt['mm2']), _awg(lt['mm2']), farbe),
                        []).append((lt['nr'], kauf or 0.0))
            elif lt['mm2'] == SIG:
                # eine Ader aus der Signalleitung
                meter.setdefault('3 × {}{}'.format(
                    _mm2(SIG), _awg(SIG)), []).append(
                        (lt['nr'], lt['laenge']))
            else:
                for _, farbe, _, _ in lt['adern']:
                    meter.setdefault('Einzelader {}, {}'.format(
                        _litze(lt), farbe), []).append(
                            (lt['nr'], lt['laenge']))
        if lt['art'] == 'Widerstand':
            # je Anschluss am Shield ein Kontakt; an der Wago eine kurze
            # Litze, an die der Widerstand geloetet wird
            kontakte['Dupont'] = kontakte.get('Dupont', 0) + len(
                {x for _, _, a, b in lt['adern'] for x in (a, b)
                 if ANSCHLUSS[x][1] == 'Dupont'})
        if lt.get('fertig') or lt['mm2'] is None:
            continue
        for _, _, a, b in lt['adern']:
            for x in (a, b):
                art = ANSCHLUSS[x][1]
                if art in ('Dupont', 'XH'):
                    kontakte[art] = kontakte.get(art, 0) + 1
                if art == 'Schraubklemme':
                    huelsen[lt['mm2']] = huelsen.get(lt['mm2'], 0) + 1
    # Dupont-Gehaeuse: am Shield je Signal ein 1-poliges, an jeder
    # Lichtschranke ein 3-poliges, der Pull-down im 2-poligen
    am_shield = {x for lt in leitungen() if not lt.get('fertig')
                 for _, _, a, b in lt['adern'] for x in (a, b)
                 if x.startswith('Shield') and ANSCHLUSS[x][1] == 'Dupont'}
    gehaeuse['Dupont 1-polig'] = len(am_shield - {'Shield Z− S',
                                                  'Shield Z− GND'})
    gehaeuse['Dupont 3-polig'] = 3
    gehaeuse['Dupont 2-polig'] = 1
    return meter, kontakte, huelsen, gehaeuse


def tab_material(K):
    meter, kontakte, huelsen, gehaeuse = material(K)
    z = ['| Menge | Teil | für |', '|---|---|---|']
    for art, teile in meter.items():
        summe = sum(m for _, m in teile)
        z.append('| {} m | {} | {} |'.format(
            de(math.ceil(summe * 2.0) / 2.0, 1), art, ' · '.join(
                '{} {} m'.format(nr, de(m, 2)) for nr, m in teile)))
    z.append('| 1 + 1 | Motorkabel 1,5 m und 2 m, 4 × AWG 24, PH-Stecker '
             'zum Motor, Dupont 4-polig zum Shield; für W15 lose Adern ohne '
             'Mantel (läuft durch beide Ketten) | W14, W15 (W12, W13: die '
             'mitgelieferten 1-m-Kabel) |')
    for nr in ('W17', 'W19'):
        lt = next(lt for lt in leitungen() if lt['nr'] == nr)
        _, kauf = laenge_m(lt, K)
        z.append('| 1 | {}, {} m | {} ({}) |'.format(
            lt['art'], de(kauf, 2), nr, lt['name']))
    z.append('| {} + Reserve | Dupont-Crimpkontakte (Buchse) | Shield, '
             'Lichtschranken, W8, W16 |'.format(kontakte.get('Dupont', 0)))
    z.append('| {} · {} · {} | Dupont-Gehäuse 1-, 2- und 3-polig | Shield, '
             'Pull-down, Lichtschranken |'.format(
                 gehaeuse['Dupont 1-polig'], gehaeuse['Dupont 2-polig'],
                 gehaeuse['Dupont 3-polig']))
    z.append('| 1 + {} | XH2.54-Gehäuse 3-polig + Crimpkontakte | Laser |'
             .format(kontakte.get('XH', 0)))
    for mm2 in sorted(huelsen):
        z.append('| {} | Aderendhülse {} | Schraubklemmen |'.format(
            huelsen[mm2], _mm2(mm2)))
    z.append('| 1 | Widerstand 10 kΩ, ¼ W | W8 |')
    z.append('| 1 + 1 + 1 | Widerstand 22 kΩ und 4,7 kΩ, ¼ W; Kondensator '
             '100 nF | W16 |')
    z.append('| — | Not-Aus-Pilztaster 16 mm, Wechsler C/NO/NC, {:.0f} A / '
             '{:.0f} V (vorhanden), Gehäuse aus [NotAus.py](notaus.md) | '
             'W2 |'.format(NOTAUS_A, NOTAUS_V))
    z.append('| — | Schrumpfschlauch 2–6 mm, Kabelbinder, Beschriftung '
             '(W-Nummer an beiden Enden) | alle |')
    return '\n'.join(z)


def tab_grbl(Q):
    z = ['| Einstellung | Wert | warum |', '|---|---|---|']
    for k, v, warum in grbl(Q):
        z.append('| `{}` | {} | {} |'.format(k, v, warum))
    return '\n'.join(z)


def tabellen(Q):
    K = Q['K']
    return {'leitungen': tab_leitungen(K), 'anschluesse': tab_anschluesse(),
            'wago': tab_wago(), 'shield': tab_shield(),
            'material': tab_material(K), 'grbl': tab_grbl(Q)}


def marken(name):
    return '<!-- tabelle:{} -->'.format(name), '<!-- /tabelle:{} -->'.format(
        name)


def auslesen(text, name):
    a, e = marken(name)
    if a not in text or e not in text:
        return None
    return text[text.index(a) + len(a):text.index(e)].strip('\n')


def einsetzen(text, name, inhalt):
    a, e = marken(name)
    i, j = text.index(a) + len(a), text.index(e)
    return text[:i] + '\n' + inhalt + '\n' + text[j:]


def main():
    Q = laden()
    with open(ANLEITUNG, encoding='utf-8') as f:
        text = f.read()
    for name, inhalt in tabellen(Q).items():
        if auslesen(text, name) is None:
            print('Markierung fehlt:', name)
            continue
        text = einsetzen(text, name, inhalt)
    with open(ANLEITUNG, 'w', encoding='utf-8') as f:
        f.write(text)
    print('geschrieben:', os.path.relpath(ANLEITUNG))
    for lt in leitungen():
        weg, kauf = laenge_m(lt, Q['K'])
        if weg is not None:
            print('  {:4s} {:26s} Weg {:5.2f} m  -> {} m'.format(
                lt['nr'], lt['name'], weg, kauf))


if __name__ == '__main__':
    main()
