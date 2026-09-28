# Elektronik — Platz, Gehäuse, Endschalter, Kabel

Wohin mit Steuerung, Netzteil, Endschaltern und Kabeln. Der Platz ist
gerechnet: `python3 tools/portal_check.py`, Abschnitt 16. Das
[Gehäuse](#gehäuse-elektronikpy) erzeugt `fusion/Elektronik/Elektronik.py`,
geprüft mit `python3 tools/elektronik_check.py`. Die Zeichnung erzeugt
`python3 tools/elektronik_zeichnen.py`; sie gibt auch die Kabellängen und
die Spannungsfälle der [Litzen](#litzen) aus;
die [Draufsicht auf das Gehäuse](#gehäuse-elektronikpy)
`python3 tools/elektronik_box_zeichnen.py`, den
[Anschlussplan](#anschlussplan)
`python3 tools/anschluss_zeichnen.py`. **Stand:** Gehäuse gezeichnet
(Elektronik.py Rev. 2, mit den Angaben vom Aufbau vom 2026-09-27:
Stapelhöhe, Wandler 12 V / 5 A, Wago-Bestand, 110 mm Überstand der 2040
hinten, Ketten 15 × 27 mm außen, Laseranschluss); die Halter für
Endschalter und Ketten folgen
([offen](#was-noch-fehlt)). Pinbelegung, Treiber und Jumper stehen in
[hardware-notizen.md, Elektronik](hardware-notizen.md#elektronik).

![Platz für die Elektronik](elektronik-platz.svg)

## Wohin: das Fach hinter dem hinteren 2060

Hinter dem hinteren 2060 stehen die 2040 frei nach hinten über. Darunter,
zwischen Tisch und 2040, fährt nichts hin:

| | |
|---|---|
| Fach | **488 × 104 × 55 mm** (Breite × Tiefe × Höhe) |
| Lage | zwischen den Innenseiten der 2040, von 3 mm hinter dem 2060 bis 3 mm vor ihr hinteres Ende, von 2 mm über dem Tisch bis 3 mm unter die 2040 |
| engste Stelle | **23 mm**: der hintere linke Klemmturm des Y-Schlittens über dem Fach, wenn das Portal am hinteren Schienenende steht |
| höher geht es | in der Mitte (\|X\| ≤ 225 mm) gleich hinter dem 2060 bis 10 mm über die Oberkante der 2040 (108 mm über dem Fachboden) |

Nach hinten begrenzt das **Schienenende** den Y-Weg, nicht das 2060: Dort
steht der Toolhead mit Z unten noch 26 mm vor dem hinteren 2060, die
Trägerplatte 23 mm vor der Montageplatte. Die Prüfung fährt Portal und
Toolhead über den ganzen Y-Weg bis an das Schienenende, dazu über X und Z,
und lässt nur Stellungen gelten, in denen der Toolhead kein 2060
durchdringt.

Die Tiefe folgt aus dem Überstand der 2040 hinter dem hinteren 2060:
**110 mm** `[v]` (bis Rev. 1 waren 145 mm angenommen), die 2060 liegen damit
**435 mm** Mitte zu Mitte auseinander. Kasten, Kabelkanal und Montageplatte
brauchen 107 mm ab der Rückseite des 2060 und enden 3,4 mm vor dem Ende der
2040 — dafür ist der Kanal 11 statt 12 mm breit.

## Was hinein kommt

| Teil | Platz | Stand |
|---|---|---|
| Steuerung: Uno R3 + CNC Shield V3 + 4 × TMC2209 | im [Gehäuse](#gehäuse-elektronikpy) links, 24-V-Lüfter im Deckel über den Treibern; USB nach hinten | gezeichnet |
| Netzteil | **Steckernetzteil GIDEALED 24 V / 3 A (72 W)**, steht außerhalb — ins Gehäuse kommt nur seine 24-V-Leitung | vorhanden |
| 24-V-Eingang | hinten am Gehäuse: Einbaubuchse 5,5 × 2,1 mm (M8) und Wippschalter KCD1 | gezeichnet |
| Verteiler | im Gehäuse rechts: Abwärtswandler 24 → 12 V / 5 A für den Laser (43 × 24 × 20 mm), davor drei Wago-Klemmen: +5 V für die Lichtschranken (221-420), GND (221-420), +24 V (221-415) | gezeichnet, Wandler und Wago vorhanden |
| Not-Aus | vorn, gut erreichbar, in der 24-V-Leitung (≥ 3 A Gleichstrom) — schaltet Laser und Motoren ab | — |

Das Gehäuse hängt an der **Rückseite des hinteren 2060** (untere und obere
Nut) mit 4 × M5 in Hammermuttern, wie die übrigen Halter — der Tisch trägt
nichts, die Maschine steht weiter nur auf den 2060.

## Gehäuse (Elektronik.py)

![Elektronik-Gehäuse von oben](elektronik-box.svg)

| Teil | Druck (PETG) | Masse (voll) | Bauraum |
|---|---|---|---|
| Gehäuse mit Montageplatte | auf dem Boden stehend | 148 cm³ ≈ 188 g | 202 × 107 × 55 mm |
| Deckel | Oberseite nach unten | 37 cm³ ≈ 47 g | 173 × 91 × 5,5 mm |
| Bohrlehre_Uno (PLA, ausgeblendet) | flach | 7 cm³ ≈ 9 g | 53 × 69 × 2 mm |

Die Massen sind aus den Schritten des Skripts nachgerechnet (Voxel,
0,2 mm); maßgeblich ist der erste Lauf in Fusion. Keine Stützen,
4 Wandlinien, ≥ 30 % Infill. Die Oberkante des USB-Fensters ist eine
48-mm-Brücke.

**Aufbau:** Kasten 160 × 91 × 44 mm, 16 mm hinter dem 2060. Die
Montageplatte liegt am 2060 an und trägt den Kasten über den Kanalboden und
drei niedrige Rippen; der Spalt dazwischen (11 mm) ist der **Kabelkanal**
nach rechts. Links im Kasten der Uno auf vier Stehbolzen, die Buchsenkante
hinten am **USB-Fenster**. Rechts der Verteiler: hinten **Einbaubuchse** und
**Schalter**, davor der **Wandler** (12 V / 5 A, 43 × 24 × 20 mm) quer,
mittig vor dem Schalter, mit zwei Kabelbindern 15 mm neben seiner Mitte —
sie laufen durch Schlitze im Boden, zwischen Buchse und Schalter bzw.
rechts am Schalter vorbei, und liegen 4 mm innerhalb seiner Enden. Links
und rechts vom Wandler bleiben 22,5 bzw. 28,5 mm für die Drähte. Davor die
drei **Wago-Klemmen** nebeneinander (Klebeband), von links: **+5 V**
(221-420, neben dem Uno), **GND** (221-420), **+24 V** (221-415, beim
Schalter); zusammen 89,8 mm auf 92 mm Platz. Kabelausschnitte oben offen:
links zur Y-Kette und zum linken Y-Motor, vorn in den Kanal.
Lüftungsschlitze rechts oben. Der Deckel sitzt mit einer Lippe innen an den
Wänden und 4 × M3 in Domen außen an den Seitenwänden; der **Lüfter** steht
obenauf über der Mitte des Uno und bläst auf die Treiber.

**Warum es passt:** Kasten und Deckel bleiben im Fach. Nur der Lüfter ragt
1 mm darüber hinaus, 43 mm hinter dem 2060 und in der Mitte — dort ist bis
unter den X-Wagen Platz. `tools/elektronik_check.py` fährt Portal und
Toolhead über den ganzen Weg dagegen: engste Stelle 22,7 mm (Montageplatte
↔ Trägerplatte, Portal am hinteren Schienenende).

**Montage:**

1. **Bohrlehre_Uno** drucken und den Uno darauflegen: Alle vier Löcher
   müssen fluchten. Erst dann das Gehäuse drucken.
2. 4 Messing-Einsätze M3 von oben in die Dome.
3. Uno mit 4 × M3×8 auf die Stehbolzen (Kernloch 2,8, die Schraube schneidet
   ihr Gewinde) — **bevor das Shield aufgesteckt wird**, danach liegt es über
   den Schrauben.
4. Shield aufstecken, Treiber (EN-Pin zum EN-Aufdruck), Jumper.
5. Einbaubuchse (Mutter innen) und Schalter (rastet ein) hinten einsetzen.
6. Wandler mit 2 Kabelbindern, Wago-Klemmen mit Klebeband; verdrahten nach
   dem [Anschlussplan](#anschlussplan). Den Wandler **ohne Laser** auf
   12,0 V stellen.
7. 4 Hammermuttern in die untere und obere Nut der Rückseite des hinteren
   2060, Gehäuse ansetzen, 4 × M5×12. Der Inbus kommt von hinten neben dem
   Kasten vorbei.
8. Kabel links durch den Ausschnitt; die für rechts vorn in den Kanal und
   darin nach rechts.
9. Lüfter mit 4 × M3×16 und Muttern auf den Deckel, **blasend nach unten**
   (Pfeil am Lüfterrahmen), Kabel durch die Öffnung. Deckel aufsetzen,
   4 × M3×8.

**Gemessen `[v]` (2026-09-27):** die Höhe von Uno, Shield und Treibern mit
Kühlkörper, **28 mm** ab Unterseite Uno (bis Rev. 1 mit 34 mm angenommen) —
der Deckel liegt 8 mm darüber, der Kasten ist dadurch 6 mm niedriger; das
Lochbild des Uno stimmt mit der Bohrlehre; der Wandler, 43 × 24 × 20 mm.

**Nicht gemessen `[w]`:** die Einbaubuchse (Loch 8,2 für M8), der Schalter
KCD1 (Ausschnitt 19,2 × 12,9, Wand dort 1,6 mm für die Rastnasen) und die
Wago-Klemmen nach Datenblatt: 221-415 30,2 × 18,8 × 8,6 mm, 221-420
(10 Leiter, zwei Reihen) 29,8 × 18,3 × 15,8 mm (Breite × Tiefe × Höhe, je
die größere Händlerangabe).

| Parameter | Wert | Wirkung |
|---|---|---|
| `geh_x0` | −205 mm | linke Außenkante des Kastens |
| `geh_abstand` | 11 mm | Kabelkanal zwischen Montageplatte und Kasten |
| `stapel_h` / `luft_luefter` | 28 `[v]` / 8 mm | Höhe Uno + Shield + Treiber, Luft bis zum Deckel — bestimmen die Kastenhöhe |
| `vert_b` | 94 mm | Breite des Verteilers (3 Wago nebeneinander) |
| `wandler_l` / `_b` / `_h` | 43 / 24 / 20 mm `[v]` | Wandler; `wandler_binder` 15 mm: Kabelbinder neben seiner Mitte |
| `buchse_d` | 8,2 mm | Loch der Einbaubuchse |
| `schalter_b` / `schalter_h` / `schalter_wand` | 19,2 / 12,9 / 1,6 mm | Ausschnitt und Wand am Schalter |
| `uno_schraube_d` | 2,8 mm | Kernloch in den Stehbolzen |

## Leistung: Reichen 72 W?

Ja, mit Reserve: Alles zusammen braucht **≈ 49 W**, das Netzteil gibt
dauernd 61 W ab.

| Verbraucher | Leistung |
|---|---|
| 4 × NEMA 17 (Stepperonline, 1,5 A) an TMC2209, je 1,05 A eingestellt | ≈ 23 W — je Motor 2 Phasen × (1,05 A)² × 2,3 Ω plus 0,6 W im Treiber; 2,3 Ω laut Datenblatt des 17HE15-1504S `[w]` |
| Lüfter 40 mm | ≈ 2 W |
| Laser LASER TREE 4 W: 12 V × 1,8 A (obere Angabe) = 21,6 W, über den Wandler (90 %) | ≈ 24 W |
| Uno | über USB, nicht aus dem Netzteil |
| **zusammen** | **≈ 49 W**, also ≈ 2,0 A auf der 24-V-Leitung |
| Netzteil, dauernd (85 % von 72 W) | 61 W — **≈ 12,5 W Reserve** |

Ein Chopper-Treiber zieht aus dem Netzteil nicht die Spulenströme, sondern
nur die Verluste in Wicklung und Treiber, dazu die mechanische Leistung —
bei einem Laser-Portal wenige Watt. Deshalb reichen für vier Motoren rund
23 W.

Wird das Steckernetzteil überlastet, schaltet es ab: Die Motoren verlieren
Schritte, GRBL merkt davon nichts, weil der Uno über USB weiterläuft. Die
Reserve ist dafür da. Ein stärkerer Laser (10 W Lichtleistung und mehr, meist
60 W Aufnahme `[w]`) bräuchte ein größeres 24-V-Netzteil — nicht über 28 V,
das vertragen die TMC2209 nicht.

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

**Warum Y hinten am Schienenende referenziert:** Seit die 2060 435 mm
auseinander liegen (gemessen), kommt der Toolhead mit Z unten nicht mehr an
das hintere 2060 — am hinteren Schienenende steht er noch 26 mm davor. Nach
hinten begrenzen also die Y-Wagen, die dort bündig mit dem Schienenende
stehen. Der Schalter soll 3 mm davor schalten: Die Wagen dürfen nicht über
das Ende hinaus, sonst fallen Kugeln heraus. Der Weg der Softlimits reicht
dann vom Schaltpunkt bis 3 mm vor das vordere 2060 (Z unten): 333 mm
zwischen Schienenende und vorderem 2060 (227 hinter und 106 vor der Mitte),
davon gehen Schaltabstand und Rückzug ab.

GRBL, vorläufig — die Werte folgen aus den Schaltpunkten, wenn die Halter
feststehen:

| | |
|---|---|
| `$22=1` | Referenzfahrt an: erst Z nach oben, dann X und Y |
| `$23=1` | X referenziert nach links (minus). Y nach hinten und Z nach oben sind die Plus-Richtungen, wenn `$3` so gesetzt ist, dass Y+ das Portal nach hinten fährt |
| `$27=1` | 1 mm vom Schalter zurück |
| `$20=1` | Softlimits an |
| `$130≈387` | X: 391 mm Weg, minus Schaltweg und Rückzug |
| `$131≈327` | Y: 333 mm zwischen Schienenende und vorderem 2060, minus 3 mm Schaltabstand, 1 mm Rückzug und 2 mm Reserve |
| `$132≈84` | Z: vom Schaltpunkt (8 mm unter der oberen Grenze) bis ganz unten, 85,6 mm |

Welche Richtung ausgelöst heißt, zeigt GRBL selbst: Mit `?` steht im Status
`Pn:X` (bzw. Y, Z), solange ein Schalter als ausgelöst gilt. `$5` so setzen,
dass `Pn` nur beim Unterbrechen erscheint. Wird D0 beim Unterbrechen HIGH
(bei diesen Modulen üblich `[w]`), meldet ein Kabelbruch über den internen
Pull-up „ausgelöst“ — die sichere Richtung.

## Kabel

**Fest verlegt** in den Nuten, mit Nutabdeckungen oder Clips gehalten:

* links aus dem Gehäuse, unter dem linken 2040 durch in die **untere Nut
  außen am linken 2040** — dort entlang zum linken Y-Motor und zum Festpunkt
  der Y-Kette;
* vorn aus dem Gehäuse in den Kabelkanal, darin nach rechts, dann an der
  **Rückseite des hinteren 2060** (mittlere Nut) zum rechten 2040 und in
  dessen unterer Nut außen nach vorn zum rechten Y-Motor bzw. nach hinten
  zum Y-Endschalter; das Kabel zum Not-Aus ebenso nach vorn.
* Vorn belegt der [Y-Motorhalter](y-motorhalter.md) die letzten 30 mm der
  unteren Nuten beider Seitenflächen (Nutensteine), dahinter sitzen am
  vorderen 2060 die Winkel, die die 2040 halten. Das Motorkabel verlässt die
  Nut vor dem Winkel und läuft außen an Winkel und Schenkel zum Motor. Am
  hinteren 2060 sitzen ebenfalls Winkel (8 je Kreuzung), dort genauso.

**Bewegt** in zwei Energieketten:

| | Y-Kette | X-Kette |
|---|---|---|
| wo | außen am linken 2040, neben dem Schlitten (der steht bis 12 mm über das 2040 hinaus) | über dem Portalrohr, hinter dem X-Riemen |
| Hub | 333 mm | 391 mm |
| Festpunkt | 267 mm vom hinteren Ende des 2040 (halber Hub) | Mitte des X-Wegs |
| Schleife | nach hinten; die Wanne hängt in der unteren Nut außen am 2040 | nach rechts — links stünde am Wegende der X-Motor darin |
| bewegtes Ende | linker Y-Schlitten, am Stirnblock | hinten an der Trägerplatte, über dem Riemenhalter |
| Länge (R18, mit Anschlussgliedern) | ≈ 263 mm | ≈ 292 mm |
| darin | X- und Z-Motor, Laser, X- und Z-Endschalter | Z-Motor, Laser, Z-Endschalter |

Gekauft sind zwei Ketten mit **10 × 20 mm innen, 15 × 27 mm außen**, je
1 m `[v]` — so gezeichnet: Die Y-Kette steht 27 mm breit außen neben dem
linken 2040, die X-Kette liegt 27 mm tief hinter dem X-Riemen. Noch
angenommen sind der Biegeradius (R18 `[?]`) und die Anschlussglieder
(zusammen 40 mm `[?]`); davon hängen die Längen ab — 1 m reicht für beide
reichlich.

Längen bis zum Gerät, Weg wie gezeichnet, 15 % Reserve, aufgerundet:

| Kabel | Weg | kaufen |
|---|---|---|
| Y-Motor links | 0,70 m | 1 m |
| Y-Motor rechts | 0,99 m | **1,5 m** |
| X-Motor | 0,73 m | 1 m |
| Z-Motor | 1,43 m | **2 m** |
| Laser (12 V + PWM) | 1,43 m | **2 m** |
| X-Endschalter | 0,73 m | 1 m |
| Y-Endschalter | 0,53 m | 1 m |
| Z-Endschalter | 1,34 m | **2 m** (bis Rev. 1: 1,5 m) |

In den Ketten nur **hochflexible Litzen** (Schleppkettenkabel), kein
Massivdraht und keine starren Flachbandkabel. Die üblichen 1-m-Motorkabel
reichen also nur links und für X. Der Laser bekommt ein eigenes 3-adriges
Kabel mit XH-Stecker ([Einkaufsliste](#einkaufsliste-vorschlag)).

### Litzen

Kupfer, feindrähtig. Der Querschnitt folgt aus Strom und Länge und aus dem,
was Stecker und Klemmen nehmen `[w]`: XH-Crimpkontakt 0,08–0,34 mm²
(AWG 28–22), PH 0,05–0,22 mm² (AWG 30–24), Dupont AWG 28–22, Wago 221
feindrähtig 0,14–4 mm². Gerechnet in `tools/elektronik_zeichnen.py`, geprüft
in `tools/elektronik_check.py` (Abschnitt 14), jeweils am längsten Weg:

| Leitung | Strom | Litze | warum |
|---|---|---|---|
| 24 V: Buchse → Schalter → Not-Aus → Wago +24 V, Buchse − → Wago GND, Wago → Shield und Wandler | bis 3 A (Netzteil) | **0,75 mm² (AWG 18)**, rot und schwarz | belastbar 6 A (VDE 0298-4, flexible Leitung); 0,5 mm² hätte genau die 3 A. Not-Aus 1,5 m hin und zurück: 0,21 V bei 3 A |
| Laser: +12 V, GND, PWM | 1,8 A | **3 × 0,34 mm² (AWG 22)** | dicker passt nicht in den XH-Kontakt am Laser; 2 m: 0,37 V = 3 % von 12 V |
| Motoren | 1,05 A je Spule | **4 × AWG 24 (0,2 mm²)** | dicker passt nicht in den PH-Kontakt am Motor; Z-Motor, 2 m: 0,35 Ω = 15 % der Wicklung. Fertige Motorkabel mit AWG 26 gehen auch (24 %) |
| Endschalter: 5 V, GND, Signal | ≈ 20 mA | **3 × 0,14 mm² (AWG 26)** oder dicker | dünner hält die Wago nicht |
| Lüfter | < 0,1 A | seine eigene Anschlusslitze | |

* In Schraubklemmen (Shield, Wandler, Not-Aus) mit **Aderendhülse**, in die
  Wago ohne.
* In den Ketten Silikonlitze oder Schleppkettenleitung. Je kleiner der
  Biegeradius der Kette, desto eher dünne Einzeladern statt dicker
  Mantelleitungen — der Radius der gekauften Ketten fehlt noch
  ([Was noch fehlt](#was-noch-fehlt)).
* Die Y-Kette trägt fünf Leitungen (X- und Z-Motor, Laser, X- und
  Z-Endschalter), die X-Kette drei. In 10 × 20 mm innen passen fünf
  Mantelleitungen bis etwa 4,5 mm Außendurchmesser in zwei Lagen — beim
  Kauf darauf achten.

## Anschlussplan

![Anschlussplan](elektronik-anschluss.svg)

Kein 230 V in der Maschine: Das Steckernetzteil liefert 24 V, am Rahmen muss
nichts geerdet und keine Netzklemme abgedeckt werden.

| von | an | Hinweis |
|---|---|---|
| Hohlstecker + | Einbaubuchse → Schalter → Not-Aus → Wago +24 V | 0,75 mm², das Netzteil liefert bis 3 A ([Litzen](#litzen)) |
| Hohlstecker − | Wago GND | |
| Wago +24 V / GND | Schraubklemme des Shields + / − | **Polung prüfen** — verpolt sind die Treiber hin |
| Wago +24 V / GND | Abwärtswandler IN+ / IN− | |
| Wago +24 V / GND | Lüfter (24-V-Typ; ein 12-V-Lüfter kommt an den Wandler) | |
| Wandler OUT+ / OUT− | Laser 12 V / GND | **Wandler erst ohne Laser auf 12,0 V stellen**, dann anschließen |
| Shield Z+ (D11), Signalstift | Laser PWM | im selben 3-adrigen Kabel, 2 m, durch beide Ketten |
| Shield X, Y, Z, A | X-Motor, Y-Motor links, Z-Motor, Y-Motor rechts | am Y-Motor rechts **eine Spule getauscht** ([Zwei Y-Motoren](hardware-notizen.md#zwei-y-motoren)) |
| Shield X+ (D9), Y+ (D10), SpnEn (D12) | D0 der Lichtschranken X, Y, Z | GND der Lichtschranke an den GND-Stift daneben |
| Shield 5 V | Wago +5 V → VCC der drei Lichtschranken | |
| Uno USB | PC | versorgt auch den Uno |

* **Abwärtswandler:** vorhanden, **12 V / 5 A**, 43 × 24 × 20 mm `[v]`.
  Der Laser zieht höchstens 1,8 A, der Wandler ist damit zu 36 % belastet —
  reichlich Luft. Den Ausgang vor dem Anschließen des Lasers messen
  (12,0 V). Die gängigen Wandler haben ein gemeinsames Minus: Laser-GND und
  Uno-GND sind damit verbunden, wie es die PWM braucht. Hat der Wandler
  getrennte Massen (IN− und OUT− ohne Durchgang), OUT− zusätzlich an den
  Wago GND.
* **Laserstecker:** XH2.54, 3-polig, **von links PWM · GND · +12 V**
  `[v]` Angabe. Vor dem ersten Einschalten mit dem Aufdruck neben der
  Buchse vergleichen — vertauscht bekäme der PWM-Eingang 12 V.
* **Wago** (vorhanden): **+24 V an der 221-415** (5 Plätze: vom Not-Aus,
  Shield, Wandler, Lüfter, einer frei), **GND an einer 221-420** (10 Plätze:
  Buchse −, Shield, Wandler, Lüfter, frei für OUT− eines Wandlers mit
  getrennten Massen), **+5 V an der zweiten 221-420** (5-V-Pin des Shields,
  drei Lichtschranken). Die **221-413** bleibt Reserve.
* **Treiber:** GERUI TMC2209 V2.0 mit Kühlkörper (5 Stück: 4 + Ersatz),
  standalone, 1/16 über MS1 + MS2. Strom am Vref-Poti, Ziel **1,05 A eff.**
  = 70 % des Nennstroms 1,5 A. Vref hängt vom Messwiderstand ab: **1,37 V**
  bei R100, **1,48 V** bei R110, **1,94 V** bei R150. Ein Aufdruck R110 ist
  auf den Modulen nicht zu finden — deshalb **mit 1,37 V anfangen**: Das
  gibt bei jedem der drei höchstens 1,05 A. Rechnung und Vorgehen in
  [hardware-notizen.md](hardware-notizen.md#treiber-und-versorgung).
* **Sicherung:** braucht es nicht, das Netzteil begrenzt den Strom selbst.
* Pins und Jumper im Einzelnen:
  [hardware-notizen.md](hardware-notizen.md#pins-grbl-11-gegen-den-aufdruck).
  Nichts unter Spannung an- oder abstecken, vor allem keine Motoren.

## Einkaufsliste (Vorschlag)

| Menge | Teil | wofür |
|---|---|---|
| 1 | Abwärtswandler 24 → 12 V / 5 A, 43 × 24 × 20 mm | vorhanden |
| 1 | Einbaubuchse 5,5 × 2,1 mm mit M8-Gewinde (Gehäuse: Loch 8,2) | 24-V-Eingang |
| 1 | Wippschalter KCD1 (Ausschnitt 19,2 × 12,9 mm), ≥ 3 A | EIN/AUS |
| 1 | Not-Aus-Pilzschalter mit Öffner, ≥ 3 A Gleichstrom | vorn |
| 1 | Lüfter 40 × 40 × 10 mm, 24 V | über den Treibern |
| 2 | Energiekette 10 × 20 mm innen, 15 × 27 mm außen, 1 m | Y und X — gekauft |
| 1 + 1 | Motorkabel 1,5 m und 2 m, 4 × AWG 24, Stecker passend zum Motor (meist JST-PH 6-polig) auf Dupont 4-polig | Y-Motor rechts, Z-Motor |
| 2 m + 1 | 3-adrige Schleppkettenlitze 3 × 0,34 mm² (AWG 22) + XH2.54-Stecker 3-polig mit Crimpkontakten | Laser |
| 1,5 m | 2-adrige Leitung 2 × 0,75 mm² | Not-Aus |
| je 1 m | Litze 0,75 mm², rot und schwarz | 24 V im Kasten |
| 4 m | 3-adrige Leitung 3 × 0,14 mm² (AWG 26), hochflexibel | Endschalter X 1 m, Y 1 m, Z 2 m |
| 1 | Aderendhülsen 0,75 und 0,34 mm² | Schraubklemmen |
| 1 + 2 | Wago 221-415 (+24 V), 221-420 (GND, +5 V); 221-413 Reserve | vorhanden |
| 4 + 4 | M5×12 + Hammermutter M5 (Nut 6) | Gehäuse → Rückseite des 2060 |
| 4 + 4 | M3×8 + Messing-Einsatz M3 Ø5 | Deckel |
| 4 | M3×8 | Uno → Stehbolzen |
| 4 + 4 | M3×16 + M3-Mutter | Lüfter → Deckel |
| 2 | Kabelbinder, doppelseitiges Klebeband | Wandler, Wago |

Die übrigen Motoren reichen mit 1 m ([Kabel](#kabel)).

## Was noch fehlt

1. **Halter der Endschalter** X und Y (mit Fahnen) — kommen als Nächstes,
   alle Maße sind da. Y schaltet jetzt am hinteren Schienenende
   ([Endschalter](#endschalter)).
2. **Energieketten** (15 × 27 außen): Biegeradius und die Anschlussglieder
   (Lochbild, Breite) messen — dann Längen, Wannen, Festpunkte und bewegte
   Enden. Den Radius zeigt eine um 180° gebogene Kette: Außenhöhe der
   Schleife minus 15, geteilt durch 2.
3. **Treiber:** Messwiderstand unbekannt — mit Vref 1,37 V anfangen (siehe
   [Anschlussplan](#anschlussplan)). Wer den Aufdruck der zwei kleinen
   Widerstände neben dem Chip findet (je nach Modul oben oder unten),
   stellt nach der Tabelle ein.
4. **Winkel vor dem vorderen 2060:** Sitzt ein Winkel mit einem Schenkel an
   der Seitenfläche der 2040 **vor** dem 2060, also in den 35 mm bis zur
   Stirnseite? Dort belegt der [Y-Motorhalter](y-motorhalter.md) die untere
   Nut.

Geklärt (2026-09-25/26): Netzteil ist das Steckernetzteil 24 V / 3 A mit
Hohlstecker 5,5 × 2,1; der Laser ein LASER TREE 4 W mit 12 V / 1,6 A;
Lüfter 24 V; Gabellichtschranken für X und Y sind da, Näherungssensoren
als Reserve; Wago-Klemmen sind da. 2026-09-27: das CNC Shield V3 ist da;
die 2040 sitzen mit Winkeln an den 2060 (8 je Kreuzung, zwei davon in der
oberen Nut); Stapelhöhe 28 mm, Lochbild des Uno stimmt; Motoren
Stepperonline NEMA 17 (1,5 A); Treiber GERUI TMC2209 V2.0; die 2040 stehen
hinten 110 mm über; Wandler 43 × 24 × 20 mm; Wago: 1 × 221-413,
1 × 221-415, 2 × 221-420; Ketten 10 × 20 mm innen. Später am 2026-09-27:
Ketten 15 × 27 mm außen, je 1 m; Wandler 12 V / 5 A; 5 Treiber, ohne
Aufdruck R110; Motoren 17HE15-1504S (Etikett); hinteres Y-Ritzel mittig
zur 2040; die Winkel greifen in die obere Nut des 2060 und die untere der
2040; Laserstecker von links PWM · GND · +12 V.
