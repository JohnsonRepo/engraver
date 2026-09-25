# Elektronik — Platz, Endschalter, Kabel (Vorschlag)

Wohin mit Steuerung, Netzteil, Endschaltern und Kabeln. Der Platz ist
gerechnet: `python3 tools/portal_check.py`, Abschnitt 16. Die Zeichnung
erzeugt `python3 tools/elektronik_zeichnen.py`; sie gibt auch die
Kabellängen aus. **Stand: Konzept.** Die Halter kommen, sobald Laser,
Ketten und Lüfter feststehen ([offen](#was-noch-fehlt)). Pinbelegung,
Treiber und Jumper stehen in
[hardware-notizen.md, Elektronik](hardware-notizen.md#elektronik).

![Platz für die Elektronik](elektronik-platz.svg)

## Wohin: das Fach hinter dem hinteren 2060

Hinter dem hinteren 2060 stehen die 2040 frei nach hinten über. Darunter,
zwischen Tisch und 2040, fährt nichts hin:

| | |
|---|---|
| Fach | **488 × 139 × 55 mm** (Breite × Tiefe × Höhe) |
| Lage | zwischen den Innenseiten der 2040, von 3 mm hinter dem 2060 bis 3 mm vor ihr hinteres Ende, von 2 mm über dem Tisch bis 3 mm unter die 2040 |
| engste Stelle | **6 mm**: die Trägerplatte, wenn das Portal am hinteren Schienenende steht — das geht nur mit Z oben |
| höher geht es | in der Mitte (\|X\| ≤ 225 mm) ab 15 mm hinter dem 2060 bis 10 mm über die Oberkante der 2040 (108 mm über dem Fachboden) |

Mit Z unten steht das hintere 2060 selbst im Weg: Der Toolhead stieße
daran, lange bevor er das Fach erreicht. Die Prüfung fährt Portal und
Toolhead über den ganzen Y-Weg bis an das Schienenende, dazu über X und Z,
und lässt nur Stellungen gelten, in denen der Toolhead kein 2060
durchdringt.

Die Tiefe hängt an der Lage des hinteren 2060 — angenommen sind 400 mm
Mitte zu Mitte hinter dem vorderen `[?]`, also 145 mm Überstand der 2040.
Seit das Netzteil außerhalb steht, ist das unkritisch: Die Steuerung
braucht rund 85 mm.

## Was hinein kommt

| Teil | Platz | Stand |
|---|---|---|
| Steuerung: Uno R3 + CNC Shield V3 + 4 × TMC2209 | links im Fach, in einem gedruckten Gehäuse mit 40-mm-Lüfter über den Treibern; USB nach hinten | Platzhalter 95 × 80 × 55 |
| Netzteil | **Steckernetzteil GIDEALED 24 V / 3 A (72 W)**, steht außerhalb — ins Fach kommt nur seine 24-V-Leitung | vorhanden |
| 24-V-Eingang | hinten im Fach: Einbaubuchse für den Hohlstecker, dahinter ein Schalter für ≥ 3 A Gleichstrom | Steckermaß offen |
| Not-Aus | vorn, gut erreichbar, in der 24-V-Leitung (≥ 3 A Gleichstrom) — schaltet Laser und Motoren ab | — |

Alles hängt an der **Rückseite des hinteren 2060** (drei Nuten) mit M5 in
Hammermuttern, wie die übrigen Halter — der Tisch trägt nichts, die Maschine
steht weiter nur auf den 2060. 55 mm Höhe reichen knapp für Uno, Shield,
Treiber mit Kühlkörper und einen Lüfter darüber. Wird es mehr, rückt das
Gehäuse 15 mm vom 2060 ab und darf dann höher werden.

## Leistung: Reichen 72 W?

Für die Motoren und den Lüfter ja, für den Laser bleiben dauernd **rund
40 W**:

| Verbraucher | Leistung |
|---|---|
| 4 × NEMA 17 an TMC2209, je ≈ 1 A eingestellt | ≈ 18 W — je Motor 2 Phasen × (1 A)² × 2 Ω plus 0,6 W im Treiber; Wicklungswiderstand angenommen `[?]` |
| Lüfter 40 mm | ≈ 2 W |
| Uno | über USB, nicht aus dem Netzteil |
| Netzteil, dauernd (85 % von 72 W) | 61 W |
| **bleibt für den Laser** | **≈ 41 W** dauernd, kurz bis ≈ 52 W |

Ein Chopper-Treiber zieht aus dem Netzteil nicht die Spulenströme, sondern
nur die Verluste in Wicklung und Treiber, dazu die mechanische Leistung —
bei einem Laser-Portal wenige Watt. Deshalb reichen für vier Motoren knapp
20 W.

Ob es für den Laser reicht, steht auf **seinem Typenschild** (Spannung und
Strom, oder die Leistungsaufnahme). Ein Modul mit rund 5 W Lichtleistung
nimmt meist 20–40 W auf und passt. Eines mit 10 W oder mehr Lichtleistung
nimmt meist 60 W und mehr auf `[w]` — dann braucht es ein größeres
24-V-Netzteil (≥ 5 A; nicht über 28 V, das vertragen die TMC2209 nicht).
Wird das Steckernetzteil überlastet, schaltet es ab: Die Motoren verlieren
Schritte, GRBL merkt davon nichts, weil der Uno über USB weiterläuft.
Braucht der Laser 12 V, kommt ein Abwärtswandler 24 → 12 V dazu, ausgelegt
auf den Laserstrom plus 20 %.

## Endschalter

Alle drei als **LM393-Gabellichtschranke**, wie Z (Maße in
[hardware-notizen.md](hardware-notizen.md#endschalter)): 5 V direkt an die
Eingänge des Shields, ohne Pegelwandler. Der induktive LJ12A3 ginge an X
und Y auch, bräuchte aber 6–36 V und einen Optokoppler.

| Achse | wo | Fahne | Referenz |
|---|---|---|---|
| X | links am Portal, beim X-Motor | am Toolhead | nach links |
| Y | außen am **rechten** 2040, hinten | am rechten Y-Schlitten | nach hinten |
| Z | am Toolhead (vorhanden) | Schaltfahne (vorhanden) | nach oben |

**Y rechts, weil links die Y-Kette läuft:** Die Fahne hinge außen neben dem
Schlitten, genau dort, wo links die Kette neben dem 2040 liegt, und der
obere Trum der Kette liegt über ihr. Rechts ist die Seite frei. Das Kabel
läuft mit dem des rechten Y-Motors an der Rückseite des 2060 entlang.

**X links ist eng:** Am linken Wegende steht der X-Motor 3 mm neben der
Trägerplatte, und der X-Riemen läuft vom Ritzel zum Riemenhalter. Wo die
Lichtschranke dort Platz findet, klärt die Prüfung, wenn die Halter
gezeichnet werden. Sonst kommt sie rechts an die Umlenkung, und X
referenziert nach rechts.

Die Näherungssensoren (LJ12A3) brauchst du dafür nicht, sie sind die
Reserve.

**Warum Y hinten am 2060 referenziert:** Der Schalter sitzt da, wo der
Toolhead mit Z unten 3 mm vor dem hinteren 2060 steht. Dann liegt der ganze
Weg der Softlimits zwischen den beiden 2060: 321 mm (215 hinter und 106 vor
der Mitte). Weiter hinten, bis zum Schienenende, kommt das Portal nur beim
Verfahren von Hand.

GRBL, vorläufig — die Werte folgen aus den Schaltpunkten, wenn die Halter
feststehen:

| | |
|---|---|
| `$22=1` | Referenzfahrt an: erst Z nach oben, dann X und Y |
| `$23=1` | X referenziert nach links (minus). Y nach hinten und Z nach oben sind die Plus-Richtungen, wenn `$3` so gesetzt ist, dass Y+ das Portal nach hinten fährt |
| `$27=1` | 1 mm vom Schalter zurück |
| `$20=1` | Softlimits an |
| `$130≈387` | X: 391 mm Weg, minus Schaltweg und Rückzug |
| `$131≈318` | Y: 321 mm zwischen den 2060, minus Rückzug und Reserve |
| `$132≈84` | Z: vom Schaltpunkt (8 mm unter der oberen Grenze) bis ganz unten, 85,6 mm |

Welche Richtung ausgelöst heißt, zeigt GRBL selbst: Mit `?` steht im Status
`Pn:X` (bzw. Y, Z), solange ein Schalter als ausgelöst gilt. `$5` so setzen,
dass `Pn` nur beim Unterbrechen erscheint. Wird D0 beim Unterbrechen HIGH
(bei diesen Modulen üblich `[w]`), meldet ein Kabelbruch über den internen
Pull-up „ausgelöst“ — die sichere Richtung.

## Kabel

**Fest verlegt** in den Nuten, mit Nutabdeckungen oder Clips gehalten:

* die Kabel aus dem Fach nach links unter dem 2040 durch, in die **untere
  Nut außen am linken 2040** — dort entlang zum linken Y-Motor und zum
  Festpunkt der Y-Kette;
* die Kabel des rechten Y-Motors und des Y-Endschalters an der **Rückseite
  des hinteren 2060** nach rechts, dann in der unteren Nut außen am rechten
  2040 nach vorn bzw. nach hinten zum Endschalter.

**Bewegt** in zwei Energieketten:

| | Y-Kette | X-Kette |
|---|---|---|
| wo | außen am linken 2040, neben dem Schlitten (der steht bis 12 mm über das 2040 hinaus) | über dem Portalrohr, hinter dem X-Riemen |
| Hub | 321 mm | 391 mm |
| Festpunkt | 273 mm vom hinteren Ende des 2040 (halber Hub) | Mitte des X-Wegs |
| Schleife | nach hinten; die Wanne hängt in der unteren Nut außen am 2040 | nach rechts — links stünde am Wegende der X-Motor darin |
| bewegtes Ende | linker Y-Schlitten, am Stirnblock | hinten an der Trägerplatte, über dem Riemenhalter |
| Länge (R18, mit Anschlussgliedern) | ≈ 257 mm | ≈ 292 mm |
| darin | X- und Z-Motor, Laser, X- und Z-Endschalter | Z-Motor, Laser, Z-Endschalter |

Längen bis zum Gerät, Weg wie gezeichnet, 15 % Reserve, aufgerundet:

| Kabel | Weg | kaufen |
|---|---|---|
| Y-Motor links | 0,64 m | 1 m |
| Y-Motor rechts | 0,99 m | **1,5 m** |
| X-Motor | 0,65 m | 1 m |
| Z-Motor | 1,35 m | **2 m** |
| Laser (Versorgung + PWM) | 1,36 m | **2 m** |
| X-Endschalter | 0,66 m | 1 m |
| Y-Endschalter | 0,59 m | 1 m |
| Z-Endschalter | 1,26 m | 1,5 m |

In den Ketten nur **hochflexible Litzen** (Schleppkettenkabel), kein
Massivdraht und keine starren Flachbandkabel. Die üblichen 1-m-Motorkabel
reichen also nur links und für X; das Kabel am Laser braucht vermutlich eine
Verlängerung.

## Elektrisch, kurz

* **Kein 230 V in der Maschine:** Das Steckernetzteil liefert 24 V, am
  Rahmen muss nichts geerdet und keine Netzklemme abgedeckt werden.
* **24 V:** Hohlstecker → Einbaubuchse → Schalter → Not-Aus → Schraubklemme
  des Shields (**Polung prüfen**, verpolt sind die Treiber hin) und → Laser,
  wenn er 24 V braucht. Lüfter mit 24 V direkt, sonst über einen
  Spannungsregler. Eine Sicherung braucht es nicht, das Netzteil begrenzt den
  Strom selbst; die Leitungen bis zum Abzweig für 3 A auslegen (0,5 mm²).
* **Signale:** Laser-PWM an D11 (Aufdruck Z+/Z−) und GND,
  Lichtschranken an 5 V, GND und die Endschaltereingänge — Belegung in
  [hardware-notizen.md](hardware-notizen.md#pins-grbl-11-gegen-den-aufdruck).
  Der Uno bekommt seine 5 V über USB.

## Was noch fehlt

Bevor die Halter gezeichnet werden:

1. **Laser:** Spannung und Strom (oder Leistungsaufnahme) vom Typenschild —
   entscheidet, ob die 72 W reichen.
2. **Hohlstecker des Netzteils:** 5,5 × 2,1 oder 5,5 × 2,5 mm (steht meist
   auf dem Netzteil) — für die Einbaubuchse.
3. **Energieketten:** vorhanden? Innen- und Außenmaß, Biegeradius. Sonst
   zwei Stück 10 × 15 mm (innen), R18, je 1 m.
4. **Lüfter:** 40 mm vorhanden, mit welcher Spannung? 24 V ginge direkt.
5. Nicht mehr dringend: Überstand der 2040 hinter dem hinteren 2060
   (angenommen 145 mm) und ob die 2040 mit Winkeln am 2060 sitzen.

Geklärt (2026-09-25): Netzteil ist das Steckernetzteil 24 V / 3 A;
Gabellichtschranken für X und Y sind da, Näherungssensoren als Reserve.
