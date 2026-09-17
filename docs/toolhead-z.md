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
[Motorbefestigung](#motorbefestigung-alle-vier-schrauben-erreichbar).

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
| +35,0 | Rückseite Schlittenplatte (Auflagepad 12 mm) |
| +41,0 | Anschraubfläche des Lasers |
| **+58,5** | **Strahlachse** |

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

## Motorbefestigung: alle vier Schrauben erreichbar

Ein NEMA 17 hat **Gewinde im Flansch**, kein Durchgangsloch. Er wird also
zwangsläufig **von unten** verschraubt — ein Durchstecken von oben ist nicht
möglich. Beide Schraubenreihen brauchen deshalb einen freien senkrechten
Korridor.

Genau daran hängt die Lage der Spindelachse:

* Die hintere Reihe liegt bei `spindel_y − 15,5`. Damit ein Ø6-Korridor an der
  Trägerplatte (Y = 0…8) vorbeikommt, muss `spindel_y ≥ 28` sein.
* Nach vorn begrenzt die Wand vor der Spindelbohrung im Mutternblock:
  `schlitten_y1 ≥ spindel_y + 6,3`.

Gewählt: **`spindel_y` = 28,5 mm**, damit 2,0 mm Luft zum Korridor und 3,2 mm
Wand im Mutternblock. Die Schlittenplatte muss dafür mit nach vorn — über
`pad_hoehe` = 12 mm (statt 6). Damit liegen die hinteren Schrauben bei
Y = +13,0 mm, also **13 mm vor der Trägerplatte**.

Zusätzlich fassen **zwei Führungsrippen** (3 mm hoch) den Motorflansch links und
rechts mit 0,4 mm Spiel: der Motor findet beim Einsetzen selbst seine Lage, und
die Schrauben müssen kein Moment übertragen (bei 0,4 Nm Haltemoment wären es
rund 9 N je Rippe).

`toolhead_check.py` prüft für **jede** der vier Schrauben einen freien
senkrechten Korridor von Ø6 mm gegen alle festen Teile — auch an der Kupplung
vorbei — und prüft die Luft zur Trägerplatte als eigene Größe.

### Was diese Variante kostet

| | vorher | jetzt |
|---|---|---|
| Spindelachse Y | 21,0 | **28,5** mm |
| `pad_hoehe` | 6 | **12** mm |
| Strahlachse | 52,5 | **58,5** mm |
| Z-Wagen-Schraube | M3×8 | **M3×14** |
| Schlittenplatte | ~25 g | **~33 g** |

Verfahrweg (48,95 mm), Trägerplatte, Z-Schiene und Gewindestange bleiben
unverändert.

**Beim Anziehen beachten:** die Z-Wagen-Schrauben klemmen jetzt **12 mm PETG**
statt 6 (der Kopf sitzt in der Ø6,5-Freibohrung auf der Pad-Vorderseite). Eine
doppelt so lange Kunststoffsäule setzt sich auch doppelt so viel, wenn das
Material kriecht — handfest anziehen und Schraubensicherung verwenden. Die
Freibohrung tiefer ins Pad zu legen (und so nur 6 mm zu klemmen) geht nicht
kostenlos: sie käme dem Ø10-Kopffreiraum der oberen Laserschraube auf 0,25 mm
nahe.

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
M6-Muttern in Sechskanttaschen; dazwischen liegt eine Druckfeder (Ø8 × 11 mm)
in einer Kammer. Die Feder drückt die untere Mutter auf den Boden und die obere
unter die Decke des Blocks. Beide Muttern tragen damit auf gegenüberliegenden
Gewindeflanken — das Flankenspiel der Gewindestange ist aufgebraucht, ohne dass
etwas klemmt.

**Die Mutterntaschen halten die Mutter vor dem Festschrauben.** Jede Tasche ist
ein echtes Sechskant mit SW + 0,15 mm, gedreht so, dass die Mutter mit einer
**Flanke** am Taschenboden anliegt und nicht mit einer Ecke — Formschluss auf
allen sechs Flanken, die Mutter kann nicht kippen. Davor sitzt ein um 0,20 mm
**engeres Mundstück** (1,4 mm lang): die Mutter wird einmal hineingedrückt und
rastet hinter einer Stufe von 0,19 mm je Seite ein. Beim Zusammenbauen fällt
sie damit nicht mehr heraus, auch bevor die Schlittenplatte die Tasche
verschließt.

Im Sechskant selbst hat die Mutter bewusst 0,15 mm Spiel und bleibt **in Z
beweglich** — sonst könnte die Feder sie nicht gegen Boden bzw. Decke drücken
und die Spielfreiheit wäre hin. Beide Werte hängen an Parametern
(`tasche_spiel`, `tasche_klemmung`); wird eine Tasche im Druck zu stramm,
reicht eine Änderung im Parameter-Dialog.

Die beiden **M3-Muttern der schwimmenden Verschraubung** sitzen ebenfalls in
Sechskanttaschen (statt vorher quadratischen) und müssen beim Anziehen nicht
von hinten gegengehalten werden. Dafür rücken ihre Bohrungen 5 mm vom Blockrand
ein: über Eck ist die Tasche 6,5 mm breit und braucht noch Wand.

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
| NEMA 17 → Konsole | **4 × M3×12** | 4 mm Eingriff; Führungsrippen zentrieren, Zentrierbund in Ø22,4 |
| Schlittenplatte → Z-Wagen (MGN9H) | 4 × **M3×14** | nur 2 mm Eingriff — MGN9 hat ~2,5 mm Gewinde, **nicht länger**. Länge wird aus `pad_hoehe` abgeleitet |
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
5. Schlittenplatte auf den Z-Wagen (4 × M3×14)
6. NEMA 17 zwischen die Führungsrippen setzen, 4 × M3×12 von unten
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
| `Bohrlehre_ZWagen` | 16 × 15 mm — MGN9H, am 2026-09-17 am Teil bestätigt `[v]` |
| `Bohrlehre_Laser` | 39 × 15 mm |
| `Bohrlehre_Mutternblock` | Verbindung zweier gedruckter Teile |

Stand der offenen Punkte aus `hardware-notizen.md`:

* **Z-Führung: geklärt.** MGN9H, am 2026-09-17 mit der Bohrlehre am Wagen
  bestätigt (äußeres Lochpaar, 16 mm längs). Die Lehre hat seitdem nur noch ein
  Lochbild und folgt dem Parameter.
* **X-Wagen: offen.** Die alte Messung „26 × 25 mm am Toolhead-Wagen" gehört
  zu ihm, nicht zur Z-Achse — MGN15H = 25 × 25 passt dazu, ist aber noch nicht
  mit der Lehre bestätigt.
* **Laser-Bohrbild: offen.** Angenommen sind 39 × 15, `hardware.md` nennt
  40 × 16 aus eigener Messung. Die Langlöcher decken beides ab (quer
  12,4–17,6, hoch 37,6–40,4 mm).

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
| `spindel_x` / `spindel_y` | 30 / 28,5 mm | Lage der Spindelachse; `spindel_y` bestimmt den Schraubzugang |
| `laser_versatz_z` | −19,5 mm | Lage des Lasers am Schlitten |
| `traeger_dicke` | 8 mm | Dicke der Trägerplatte |
| `konsole_unten` / `konsole_dicke` | 68 / 8 mm | Lage und Dicke der Motorkonsole |
| `motor_rippe_hoehe` | 3 mm | Höhe der Führungsrippen am Motorflansch |
| `m3_uebermass` | 4,6 mm | Ausrichtspiel des Mutternblocks |
| `tasche_spiel` | 0,15 mm | Spiel der Mutterntaschen auf die Schlüsselweite |
| `tasche_klemmung` | 0,20 mm | Untermaß im Mundstück — hält die M6-Mutter |
