# Elektronik — Platz, Endschalter, Kabel (Vorschlag)

Wohin mit Steuerung, Netzteil, Endschaltern und Kabeln. Der Platz ist
gerechnet: `python3 tools/portal_check.py`, Abschnitt 16. Die Zeichnung
erzeugt `python3 tools/elektronik_zeichnen.py`; sie gibt auch die
Kabellängen aus. **Stand: Konzept.** Die Halter kommen, sobald Netzteil,
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
daran, lange bevor er das Fach erreicht. Die Prüfung fährt Portal und Toolhead über den ganzen Y-Weg bis an
das Schienenende, dazu über X und Z, und lässt nur Stellungen gelten, in
denen der Toolhead kein 2060 durchdringt.

**Die Tiefe hängt an der Lage des hinteren 2060** — angenommen sind 400 mm
Mitte zu Mitte hinter dem vorderen `[?]`, also 145 mm Überstand der 2040.
Bitte nachmessen: Rückseite hinteres 2060 bis hinteres Ende der 2040.

## Was hinein kommt

| Teil | Platz | Stand |
|---|---|---|
| Steuerung: Uno R3 + CNC Shield V3 + 4 × TMC2209 | links im Fach, in einem gedruckten Gehäuse mit 40-mm-Lüfter über den Treibern; USB nach hinten | Platzhalter 95 × 80 × 55 |
| Netzteil 24 V | daneben, flach liegend (gelochtes Gehäuse, kühlt durch Konvektion) | Modell offen, Platzhalter 159 × 97 × 30 (Mean Well LRS-150-24 `[w]`) |
| Netzanschluss | hinten rechts: Kaltgerätebuchse mit Schalter und Sicherung | — |
| Not-Aus | vorn, gut erreichbar; schaltet mindestens den Laser stromlos | — |

Alles hängt an der **Rückseite des hinteren 2060** (drei Nuten) mit M5 in
Hammermuttern, wie die übrigen Halter — der Tisch trägt nichts, die Maschine
steht weiter nur auf den 2060. 55 mm Höhe reichen knapp für Uno, Shield,
Treiber mit Kühlkörper und einen Lüfter darüber. Wird es mehr, rückt das
Gehäuse 15 mm vom 2060 ab und darf dann höher werden.

## Endschalter

Alle drei als **LM393-Gabellichtschranke**, wie Z (Maße in
[hardware-notizen.md](hardware-notizen.md#endschalter)): 5 V direkt an die
Eingänge des Shields, ohne Pegelwandler. Der induktive LJ12A3 ginge an X
und Y auch, bräuchte aber 6–36 V und einen Optokoppler.

| Achse | wo | Fahne | Referenz |
|---|---|---|---|
| X | links am Portal, beim X-Motor | am Toolhead | nach links |
| Y | außen am linken 2040, hinten | am linken Y-Schlitten | nach hinten |
| Z | am Toolhead (vorhanden) | Schaltfahne (vorhanden) | nach oben |

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
  Nut außen am linken 2040** — dort entlang zum linken Y-Motor, zum
  Y-Endschalter und zum Festpunkt der Y-Kette;
* das Kabel des rechten Y-Motors an der **Rückseite des hinteren 2060**
  nach rechts, dann in der unteren Nut außen am rechten 2040 nach vorn.

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
| Y-Endschalter | 0,15 m | 0,5 m |
| Z-Endschalter | 1,26 m | 1,5 m |

In den Ketten nur **hochflexible Litzen** (Schleppkettenkabel), kein
Massivdraht und keine starren Flachbandkabel. Die üblichen 1-m-Motorkabel
reichen also nur links und für X; das Kabel am Laser braucht vermutlich eine
Verlängerung.

## Elektrisch, kurz

* **230 V:** Kaltgerätebuchse → Schalter und Sicherung → Netzteil. Den
  Schutzleiter an das Netzteil **und an den Alurahmen** (Ringöse auf einer
  Hammermutter im 2060) — die Halter sind aus Kunststoff, der Rahmen wäre
  sonst nicht geerdet. Die Klemmen des Netzteils abdecken. Wenn du dir bei
  Netzspannung nicht sicher bist, lass das von einer Elektrofachkraft
  anschließen.
* **24 V:** Netzteil → Schraubklemme des Shields (**Polung prüfen**, verpolt
  sind die Treiber hin) und → Laser, wenn er 24 V braucht. Lüfter mit 24 V
  direkt, sonst über einen Spannungsregler.
* **Signale:** Laser-PWM an D11 (Aufdruck Z+/Z−) und GND,
  Lichtschranken an 5 V, GND und die Endschaltereingänge — Belegung in
  [hardware-notizen.md](hardware-notizen.md#pins-grbl-11-gegen-den-aufdruck).
  Der Uno bekommt seine 5 V über USB.

## Was noch fehlt

Bevor die Halter gezeichnet werden:

1. **Netzteil:** Modell oder Maße (L × B × H), wo die Klemmen und die
   Befestigungslöcher sitzen. Noch keins gekauft? Dann Spannung und Strom
   vom **Typenschild des Lasers** — daraus folgt die Leistung.
2. **Energieketten:** vorhanden? Innen- und Außenmaß, Biegeradius. Sonst
   zwei Stück 10 × 15 mm (innen), R18, je 1 m.
3. **Lüfter:** 40 mm vorhanden, mit welcher Spannung?
4. **Überstand hinten:** Rückseite hinteres 2060 bis hinteres Ende der 2040
   (angenommen 145 mm) — und ob die 2040 mit Winkeln am 2060 sitzen.
5. **Gabellichtschranken:** Sind außer der an Z noch zwei übrig?
