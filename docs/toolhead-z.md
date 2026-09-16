# Toolhead Z-Achse — kompletter Aufbau

Erzeugt von `fusion/ToolheadZ/ToolheadZ.py` (Baugruppe, vier gedruckte Teile).
Geprüft mit `python3 tools/toolhead_check.py`, Layout in
[toolhead-z-layout.svg](toolhead-z-layout.svg).

![Layout](toolhead-z-layout.svg)

## Was hier zusammenkommt

Der Toolhead hängt am **MGN15H-Wagen der Portalführung** und bringt seine
eigene Z-Achse mit: eine MGN9-Führung, angetrieben von einem NEMA 17 über eine
flexible Kupplung auf eine M6-Gewindestange. Der Laser sitzt auf dem Z-Schlitten.

| Pos | Teil | Material | Funktion |
|---|---|---|---|
| 1 | **Trägerplatte** mit angeformter **Motorkonsole** | PETG, 8 mm | sitzt auf dem X-Wagen, trägt Schienensockel, Konsole und Führungsrippen |
| 2 | **Schlittenplatte** | PETG | auf dem MGN9H-Z-Wagen, trägt den Laser |
| 3 | **Mutternblock** | PETG | zwei M6-Muttern, federverspannt, schwimmend verschraubt |

Die Motorkonsole ist **Teil der Trägerplatte**, kein eigenes Bauteil — siehe
[Motorbefestigung](#motorbefestigung-warum-nur-zwei-schrauben).

## Bezugsebene und Koordinaten

**Ursprung = Mitte des X-Wagen-Lochbildes, auf seiner Stirnfläche.** Das ist die
Passfläche, an der die Trägerplatte anliegt — genau die Ebene, deren Höhe beim
ersten Versuch gefehlt hat. Alles ist von hier aus bemaßt.

* X = quer, längs des Portals
* Y = nach vorn, weg vom Portal
* Z = senkrecht, Verfahrrichtung der Z-Achse

Im Fusion-Modell sind Y und Z getauscht (Modell-Z = Maschine Y), damit alle
Plattenskizzen in einer Ebenenfamilie liegen und es keine
Richtungsverwechslungen beim Extrudieren gibt.

## Y-Kette (ab X-Wagen-Stirnfläche)

| Y | Ebene |
|---|---|
| −16,0 | Portalprofil, Auflage der MGN15-Schiene |
| −6,0 | Oberkante X-Schiene (6 mm Luft zur Trägerplatte) |
| **0** | **X-Wagen-Stirnfläche = Rückseite Trägerplatte** |
| +8,0 | Vorderseite Trägerplatte |
| +13,0 | Sockelfläche = Auflage der MGN9-Z-Schiene |
| +19,5 | Oberkante Z-Schiene |
| +23,0 | Stirnfläche Z-Wagen = Rückseite Auflagepad |
| +29,0 | Rückseite Schlittenplatte |
| +35,0 | Anschraubfläche des Lasers |
| **+52,5** | **Strahlachse** |

Die MGN9-Schiene sitzt auf einem **Sockel von 5 mm** — nur so sitzen die
M3-Gewindeeinsätze 7 mm tief im Material. Der Sockel ist **genau so breit wie
die Schiene (9 mm)**; wäre er breiter, würden die Schürzen des Wagens daran
streifen. Das prüft `toolhead_check.py` ausdrücklich.

## Z-Kette und Verfahrweg

| Z | Ebene |
|---|---|
| −83,6 | Laser-Unterkante (Linse), tiefste Stellung |
| −60,0 | Unterkante MGN9-Schiene (95 mm lang, 5 Schrauben) |
| −40,1 … +8,9 | Bereich der Wagenmitte `zc` |
| +35,0 | Oberkante MGN9-Schiene |
| +39,0 … +64,0 | flexible Kupplung |
| +68,0 | Unterseite Motorkonsole = Oberkante Trägerplatte |
| +76,0 | Motorflansch |
| +116,0 | Oberkante NEMA 17 |

**Nutzbarer Verfahrweg: 48,95 mm.** Vier Dinge begrenzen ihn; das Skript rechnet
alle vier aus und nennt die bindende:

| Grenze | zc max |
|---|---|
| **Laser-Oberkante gegen Motorkonsole** | **+8,9** ← bindend |
| Wagen am oberen Schienenende | +15,1 |
| Schlittenplatte gegen Kupplung | +19,0 |
| Mutternblock gegen Kupplung | +23,0 |

Mehr Weg gibt es also nicht durch eine längere Schiene, sondern nur durch eine
höhere Konsole (`konsole_unten`) — dann wird der Toolhead entsprechend höher.

Die Kollisionsprüfung fährt den Weg in 21 Stellungen ab und prüft jedes bewegte
Teil gegen jedes feste, einschließlich Portalprofil und X-Schiene.

## Motorbefestigung: warum nur zwei Schrauben

Ein NEMA 17 hat **Gewinde im Flansch**, kein Durchgangsloch. Er wird also
zwangsläufig **von unten** verschraubt — ein Durchstecken von oben ist nicht
möglich.

Die hintere Schraubenreihe liegt bei Y = +5,5 mm und damit **mitten im
Querschnitt der Trägerplatte** (Y = 0…8). Von unten kommt dort nie ein
Werkzeug hin: die Platte ist eine durchgehende Wand über ihre ganze Höhe. Ein
separater Motorhalter ändert daran nichts — die Platte steht so oder so im Weg.
Die Ursache ist, dass die Motorachse an der Spindelachse hängt und die bei
Y = 21 mm liegen muss, damit der Mutternblock hinter die Schlittenplatte passt.

Die Lösung besteht deshalb aus zwei Teilen:

* **Zwei M3×12 in der vorderen Reihe** (Y = 36,5 mm). Der Zugangskorridor ist
  dort frei — auch an der Kupplung vorbei, die 2,5 mm neben den Bohrungen
  verläuft. `toolhead_check.py` prüft für jede benutzte Schraube einen freien
  senkrechten Korridor von Ø7 mm und weist ausdrücklich nach, dass die hintere
  Reihe blockiert ist.
* **Zwei Führungsrippen**, 3 mm hoch, die den Motorflansch links und rechts mit
  0,4 mm Spiel fassen. Sie nehmen das Motormoment formschlüssig auf — bei
  0,4 Nm Haltemoment sind das rund 9 N je Rippe. Die Schrauben halten den Motor
  damit nur noch nieder, sie müssen kein Moment übertragen.

Die hinteren beiden Bohrungen werden **nicht gebohrt**; sie wären nur
irreführend.

**Falls du alle vier Schrauben willst:** dann muss die Motorachse nach vorn,
mindestens auf Y ≈ 28,5 mm. Das zieht die ganze Y-Kette mit (`pad_hoehe` von 6
auf 12 mm, damit der Mutternblock noch hinter die Schlittenplatte passt), die
Strahlachse wandert auf 58,5 mm und die Z-Wagenschrauben werden M3×14. Sag
Bescheid, dann rechne ich das durch.

## Warum Trägerplatte und Konsole ein Teil sind

Du hast es selbst vorgeschlagen, und es ist die bessere Lösung:

* Die Verschraubung Halter ↔ Platte entfällt komplett — vier Schrauben, vier
  Muttern und zwei Anschraublaschen weniger, und nichts kann sich lösen.
* Die Konsole wird steifer: sie hängt nicht an vier M3, sondern ist
  durchgehendes Material.
* **Es druckt sich sogar besser.** Mit der Rückseite (Passfläche) auf dem Bett
  stehen Platte, Sockel, Konsole *und* Führungsrippen alle auf dem Bett. Die
  Konsole wächst als Wand in Aufbaurichtung mit, ohne Überhang — kein
  Stützmaterial. Das Kragmoment des Motors an der Konsole beträgt 0,04 Nm; die
  Biegespannung quer zur Schicht liegt bei etwa 0,07 MPa, also weit unter allem,
  was PETG in der Schichthaftung kann.

Das Bauteil wird damit 78 × 48 × 145 mm groß und passt aufrecht in den A1.

## Z-Antrieb: M6 behalten, aber spielfrei und schwimmend

Die Gewindestange bleibt — geändert ist, **wie** die Mutter angebunden ist. Zwei
Dinge machen den Unterschied:

**Spielfrei durch zwei Muttern mit Feder.** Im Mutternblock sitzen zwei
M6-Muttern in nach vorn offenen Taschen; dazwischen liegt eine Druckfeder
(Ø8 × 11 mm) in einer Kammer. Die Feder drückt die untere Mutter auf den Boden
und die obere unter die Decke des Blocks. Beide Muttern tragen damit auf
gegenüberliegenden Gewindeflanken — das Flankenspiel der Gewindestange ist
aufgebraucht, ohne dass etwas klemmt. Die Schlittenplatte schließt die Taschen,
die Muttern können nicht herausfallen.

**Schwimmend verschraubt.** Der Block ist mit **zwei M3 durch Ø4,6-Bohrungen**
(statt 3,4) plus großen Scheiben an der Schlittenplatte befestigt. Vorgehen:
Schrauben locker, Z-Achse mehrmals über den ganzen Weg fahren, **dann**
festziehen. Der Block findet dabei die Lage, die die Gewindestange vorgibt —
eine krumme Stange kämpft so nicht gegen die Linearführung. Zusammen mit der
flexiblen Kupplung 5→6 mm bleibt der Rundlauffehler oben, wo er nicht stört.

**Wenn du später doch auf T8/TR8x8 umsteigen willst:** nur der Mutternblock wird
neu gedruckt, alles andere bleibt. Dafür brauche ich das Flanschlochbild deiner
POM-Antibacklash-Mutter — das steht nicht in `hardware.md` und will gemessen
werden.

## Verschraubung

| Verbindung | Schrauben | Hinweis |
|---|---|---|
| Trägerplatte → X-Wagen (MGN15H) | 4 × M3×12 + Scheibe | 3,5 mm Gewindeeingriff bei 4 mm verfügbarer Tiefe |
| Z-Schiene → Sockel | 5 × M3×10 Senkkopf DIN 7991 + 5 × ruthex M3 | Einsätze vor der Montage einschmelzen |
| NEMA 17 → Konsole | **2 × M3×12**, vordere Reihe | 4 mm Eingriff; Moment über die Führungsrippen, Zentrierbund in Ø22,4 |
| Schlittenplatte → Z-Wagen (MGN9H) | 4 × M3×8 | nur 2 mm Eingriff — MGN9 hat ~2,5 mm Gewinde, **nicht länger** |
| Laser → Schlittenplatte | 4 × M3×10 + Scheibe DIN 9021 | Scheibe wegen der Langlöcher Pflicht |
| Mutternblock → Schlittenplatte | 2 × M3×16 + Mutter + Scheibe | Ø4,6-Bohrung, ausrichten dann festziehen |

Kaufteile: MGN9-Schiene 95 mm + Wagen MGN9H · NEMA 17 (Körper 40 mm, Welle 5 mm)
· M6-Gewindestange, Zuschnitt **120 mm** (110 mm werden gebraucht) · flexible
Kupplung 5→6 mm, 25 mm lang · 2 × M6-Mutter · Druckfeder Ø8 × 11 mm.

## Montagereihenfolge

Die Reihenfolge ist nicht beliebig — die Köpfe der X-Wagen-Schrauben sind später
von der Schlittenplatte verdeckt:

1. Gewindeeinsätze in den Schienensockel einschmelzen
2. **Trägerplatte an den X-Wagen** (4 × M3×12 + Scheibe)
3. Z-Schiene auf den Sockel (Senkkopf M3×10)
4. **Laser an die Schlittenplatte** — die Köpfe der oberen Schraubenreihe
   liegen in den Ø10-Freiräumen im Auflagepad
5. Schlittenplatte auf den Z-Wagen (4 × M3×8)
6. NEMA 17 zwischen die Führungsrippen setzen, 2 × M3×12 von unten
7. Kupplung und Gewindestange, Mutternblock zuletzt ausrichten und festziehen

## Zwei Details, die beim Konstruieren aufgefallen sind

**Lochbild des Lasers gegen das des Z-Wagens.** Beide liegen bei X = ±7,5 mm.
Die Lochbildmitte des Lasers liegt deshalb **19,5 mm unter der Wagenmitte** —
damit liegt die obere Laser-Schraubenreihe genau mittig zwischen den beiden
Schraubenreihen des Wagens (±8) und die Ø6,5-Freibohrungen überschneiden die
Langlöcher nicht. Bei anderen Werten tun sie es; `toolhead_check.py` prüft alle
vier Kombinationen.

**Kopf-Freiraum im Auflagepad.** Die obere Laser-Schraubenreihe liegt innerhalb
des Auflagepads. Zwei **Ø10-Durchbrüche im Pad** nehmen Kopf und Scheibe auf;
die Scheibe liegt trotzdem auf der Plattenrückseite auf, weil der Durchbruch nur
das Pad durchdringt. Vom Pad bleiben 571 mm² Auflage auf dem Wagen.

## Druck (PETG, Bambu Lab A1)

| Teil | Lage aufs Bett | Warum |
|---|---|---|
| Trägerplatte (mit Konsole) | Rückseite (Passfläche) unten | Platte, Sockel, Konsole und Rippen stehen alle auf dem Bett — keine Stützen, alle Kräfte in der Schicht |
| Schlittenplatte | Laser-Anschraubfläche unten | Brücke 10,5 mm zwischen den Rippen |
| Mutternblock | Unterseite unten | Spindelbohrung wird rund |

4 Wandlinien, ≥ 40 % Infill. An jeder Auflagefläche sitzt eine Fase von
0,4 × 45° — ohne sie hebt der Elefantenfuß der ersten Schicht das Teil von der
Passfläche ab.

## Vor dem Druck prüfen

Das Skript legt vier **ausgeblendete Bohrlehren** an (3 mm, PLA): im Browser
einblenden, drucken, ans reale Teil halten.

| Lehre | prüft |
|---|---|
| `Bohrlehre_XWagen` | 25 × 25 mm — sitzt am Portal wirklich ein MGN15H? |
| `Bohrlehre_ZWagen` | inneres Lochpaar = MGN9C (10 mm), äußeres = MGN9H (16 mm) |
| `Bohrlehre_Laser` | 39 × 15 mm |
| `Bohrlehre_Mutternblock` | Verbindung zweier gedruckter Teile |

Offene Punkte aus `hardware-notizen.md`: das Laser-Bohrbild ist als 39 × 15
angenommen, `hardware.md` nennt 40 × 16 aus eigener Messung — die Langlöcher
decken beides ab (quer 12,4–17,6, hoch 37,6–40,4 mm). Die dort notierte Messung
„26 × 25 mm am Toolhead-Wagen" passt zum **X**-Wagen (MGN15H), nicht zur
MGN9-Z-Achse.

## Wenn ein Teil an der falschen Stelle landet

Fusion orientiert die Achsen einer Skizzenebene und die Normale einer
Offset-Ebene nicht immer so, wie man es erwartet — und meldet dabei **keinen
Fehler**, das Teil landet einfach gespiegelt oder verschoben. Das Skript
verlässt sich deshalb an drei Stellen nicht auf Annahmen (Rev. 2):

* **Offset-Ebenen messen ihre eigene Lage nach** und korrigieren das
  Vorzeichen selbst, statt es zu raten.
* **Skizzenpunkte** werden über `modelToSketchSpace` aus Maschinenkoordinaten
  umgerechnet, statt die Achsrichtung der Ebene anzunehmen.
* **Durchgangs- und Taschenschnitte sind symmetrisch** um ihre Skizzenebene.
  Damit ist die Normalenrichtung irrelevant — ein einseitiger `ThroughAll`
  bricht sonst mit `EXTRUDE_ZERO_DISTANCE_ERROR` ab, sobald die Normale vom
  Material wegzeigt.

Zusätzlich prüft das Skript nach jedem Teil die **Bounding Box gegen den
erwarteten Bauraum** und schreibt Abweichungen in den Validierungsbericht.
Steht dort eine Zeile wie `Mutternblock: Y liegt -29.0..-12.0, erwartet
12.0..29.0`, ist eine Achse gespiegelt — dann bitte melden, die Zeile sagt
genau, welche.

## Parametrik

Alle Werte aus dem `MASSE`-Block landen als Fusion-User-Parameter im Dialog
*Ändern → Parameter*. Die **absoluten Lagen** rechnet `lage()` in Python aus
diesen Werten — nach einer Parameteränderung also das Skript neu laufen lassen
und `tools/toolhead_check.py` ausführen. Die wichtigsten Stellschrauben:

| Parameter | Wert | Wirkung |
|---|---|---|
| `z_schiene_laenge` | 95 mm | Länge der Z-Führung |
| `konsole_unten` | 68 mm | Höhe der Motorkonsole — bindet den Verfahrweg |
| `spindel_x` / `spindel_y` | 30 / 21 mm | Lage der Spindelachse |
| `laser_versatz_z` | −19,5 mm | Lage des Lasers am Schlitten |
| `traeger_dicke` | 8 mm | Dicke der Trägerplatte |
| `konsole_unten` / `konsole_dicke` | 68 / 8 mm | Lage und Dicke der Motorkonsole |
| `motor_rippe_hoehe` | 3 mm | Höhe der Führungsrippen am Motorflansch |
| `m3_uebermass` | 4,6 mm | Ausrichtspiel des Mutternblocks |
