# Hardware-Notizen (projektlokal)

Ergänzung zur `references/hardware.md` des `fusion-python`-Skills, damit die
Werte dieses Projekts auch ohne den Skill nachvollziehbar sind.

Status: `[v]` am realen Teil verifiziert · `[w]` Datenblatt/Web, ungeprüft ·
`[?]` eigene Messung mit unsicherer Messbasis → im Skript als Langloch ausführen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil, darauf 2 × 2040 Aluprofil |
| Y-Achse | 2 Linearführungen oben auf den 2040ern |
| Portal | Halterungen auf den Y-Schlitten, dazwischen 2020 Aluprofil |
| X-Achse | Linearführung am Portalprofil |
| Z-Achse | Grundplatte am X-Wagen, darauf Linearführung; Toolhead auf dem Z-Wagen |
| Werkzeug | Diodenlaser am Toolhead |

## Z-Achse / Toolhead

| Wert | Maß | Status |
|---|---|---|
| Linearführung Z | **MGN9H** | `[v]` am 2026-09-17 mit Bohrlehre geprüft |
| Schienenlänge | **200 mm** | `[v]` vorhandene Schiene |
| Randabstand / Lochabstand | **10 / 20 mm** → 10 Löcher | `[v]` gemessen |
| Wagen-Lochbild | **15 quer × 16 längs** | `[v]` |
| Montagehöhe Wagen | 10 mm über der Schienen-Auflageebene | `[w]` |
| Schiene MGN9 | 9 breit × 6,5 hoch | `[w]` |
| Gewindetiefe im Wagen | ~2,5 mm (M3) → max. M3×8 bei 6 mm Pad | `[w]` |

**Widerspruch aufgelöst.** `hardware.md` notierte eine Messung am
„Toolhead-Wagen" von 26 längs × 25 quer, was nicht zu MGN9 passt. Die Bohrlehre
am Z-Wagen hat am 2026-09-17 das äußere Lochpaar (16 mm) bestätigt — die
Z-Achse ist also **MGN9H**. Die 26 × 25 gehören folglich zum Wagen der
**Portalführung** (X-Achse), wo MGN15H = 25 × 25 passt. Am 2026-09-21 hat
`Bohrlehre_XWagen` dort gepasst `[v]`: es ist ein **MGN15H mit 25 × 25**
(ein MGN15C hätte 25 × 20), und die 26 × 25 sind damit auch als Messung des
X-Wagens widerlegt — 1 mm Abweichung lässt eine Ø3,4-Lehre auf M3 nicht durch.

Die `Bohrlehre_ZWagen` trug bis dahin beide MGN9-Lochbilder (10 und 16 mm
längs), um die Baugröße zu entscheiden. Sie folgt jetzt dem Parameter
`z_wagen_loch_laengs` und hat nur noch vier Löcher.

## Portalführung (X-Achse)

| Wert | Maß | Status |
|---|---|---|
| Linearführung X | **MGN15H** | `[v]` am 2026-09-21 mit `Bohrlehre_XWagen` geprüft |
| Wagen-Lochbild | **25 × 25 mm** | `[v]` am 2026-09-21 geprüft |
| Wagen | 32 breit (in Z) × 58,8 lang (in X) | `[w]` |
| Montagehöhe Wagen | 16 mm über der Profilfläche | `[w]` |
| Gewindetiefe im Wagen | 4 mm (M3) → M3×12 mit Scheibe | `[w]` |

Damit ist das Lochbild der Trägerplatte bestätigt — sie trägt den ganzen
Toolhead und war das letzte Teil, das auf eine Messung gewartet hat.

## Diodenlaser

| Wert | Maß | Status |
|---|---|---|
| Bohrbild | **40,5 hoch × 16,5 quer**, 4 × M3 | `[v]` am 2026-09-17 mit Bohrlehre am Modul bestätigt |
| Gehäuse (angenommen) | 35 × 35 mm Querschnitt | `[w]` |

Messhistorie an diesem Modul: **39 × 15** (erste Angabe) → **40 × 16**
(`hardware.md`, eigene Messung) → **40,5 × 16,5** — mit `Bohrlehre_Laser`
(Ø3,4 Rundlöcher) am Teil geprüft und bestätigt. Damit war auch belegt, dass
Rundlöcher an dieser Stelle funktionieren — die Schlittenplatte hatte deshalb
in Rev. 12/13 **Rundlöcher Ø4,0**. Seit Rev. 14 sind es **senkrechte
Langlöcher 4,0 × ±8 mm**, aber aus einem anderen Grund: nicht Lochbildtoleranz,
sondern Höhenverstellung für den unbekannten Fokusabstand (unten).

Die Lochbildtoleranz beträgt damit **±1,0 mm je Achse** (Ø4,0 auf Schaft Ø3),
deckt also 39,5 – 41,5 hoch und 15,5 – 17,5 quer ab — die Messung 40 × 16
liegt noch darin, die erste Angabe 39 × 15 nicht mehr. `toolhead_check.py`
führt Toleranz und Messhistorie im Bericht mit. Reicht der Bereich gegen den
Schrumpf nicht, genügt `laser_loch_d` von 4,0 auf 4,5 mm.

Ist das Gehäuse tiefer oder flacher als 35 mm, `laser_tiefe` anpassen — davon
hängt nur die berechnete Lage der Strahlachse ab, nicht die Geometrie.

### Gewindeeinsätze `[v]`

| Wert | Maß | Status |
|---|---|---|
| Typ | Messing-Einschmelzeinsatz M3 | `[v]` |
| Außendurchmesser | **5,0 mm** | `[v]` am Teil |
| Einpressbohrung im Skript | **4,6 mm** × 7 mm tief | `[v]` |
| Wand im Schienensockel | **2,20 mm** je Seite | Minimum aus `hardware.md`: 2,0 |

Nicht die ruthex-Maße aus `references/hardware.md` (M3: OD 4,6 → Bohrung 4,0).
Die Bohrung liegt 0,4 mm unter dem Außendurchmesser, damit der Einsatz beim
Einschmelzen Material verdrängt und greift. Der Schienensockel ist 9 mm breit
und darf es bleiben — damit ist diese Bohrung die engste Stelle im ganzen
Teil.

### Fokusabstand `[?]` — offen

| Wert | Maß | Status |
|---|---|---|
| Fokusabstand f (Gehäuseunterkante → Material) | **unbekannt** | steht nicht auf dem Modul, Modul nicht benannt |

`hardware.md` führt als Kandidaten das *Laser Tree LT-20W-A* mit „Fokus
einstellbar 20–35 mm" `[w]` — ob es dasselbe Modul ist, ist offen. Deshalb
steckt f **nicht** in der Geometrie: die Laserhöhe wird über senkrechte
Langlöcher (±8 mm, nach oben nutzbar +7,8 mm) eingestellt. Der
Validierungsbericht rechnet die Stellung je f aus.

Selbst messen: Papier aufs Bett, 1–2 % Leistung, Höhe variieren bis der Punkt
am kleinsten ist, dann Gehäuseunterkante → Papier messen. Sobald der Wert
bekannt ist, hier eintragen und auf `[v]` setzen.

## Endschalter

| Wert | Maß | Status |
|---|---|---|
| Typ | Gabellichtschranke LM393 (Hailege) | `[v]` |
| Platine | **25 × 20 mm** | `[v]` gemessen |
| Gabelspalt | **10 mm** | `[v]` |
| Lage der Gabel | 1 mm von der 20-mm-Kante | `[v]` |
| Bohrbild | 2 × M3 in den Ecken der Gegenseite, Lochrand 1 mm von beiden Kanten → **Lochmitten 2,5 mm, Abstand 15 mm** | `[v]` gemessen, Lochmitte abgeleitet |
| Strahlhöhe über der Platine | **5 mm angenommen** | `[?]` nicht gemessen |
| Versorgung | 3,3 / 5 V, D0 digital | `[w]` |
| Befestigung | 2 × M2×6 in Heat Inserts **M2 Ø3,2 × 2,5** | `[v]` vorhanden |

Einpressbohrung für die M2-Einsätze: **Ø2,8 × 3 mm**, also 0,4 mm unter dem
Außendurchmesser — dieselbe Regel wie bei den M3-Einsätzen am Schienensockel.

Die angenommene Strahlhöhe ist der Grund, warum der Halter ein eigenes
Druckteil ist: er kostet 6 g statt 154. Die Schaltfahne deckt zudem 3,5 bis
12,5 mm über der Platine ab.

Ebenfalls vorhanden: **induktiver Näherungsschalter LJ12A3-4-Z/BX** (M12,
Sn 4 mm, NPN Schließer, 6–36 V). Für Z am Toolhead ungeeignet — 60 g,
Pegelwandler nötig, ±0,1…0,2 mm Wiederholgenauigkeit. Vorgesehen für X und Y
am Rahmen. Achtung: Schließer meldet bei Kabelbruch nicht; der Öffner
(`/AX`) wäre für Endschalter die sichere Variante.

## Maschinenmaße für die Z-Achse

| Wert | Maß | Status |
|---|---|---|
| Bezugsebene (Mitte X-Wagen-Lochbild) → Bettoberfläche | **130 mm** | `[?]` am 2026-09-17 genannt, auf cm gerundet |
| dickstes Werkstück | **50 mm** | Vorgabe |

Beide stehen als `bett_abstand` und `werkstueck_max` im Skript — sie erzeugen
keine Geometrie, sondern nur die Fokusrechnung im Bericht. Aus ihnen folgt das
Fenster **f = 6 … 57 mm**, in dem 0–50 mm Werkstückdicke erreichbar bleiben
(oben gerechnet bis zum Schaltpunkt des Endschalters, nicht bis zur
mechanischen Grenze — bis Rev. 28 stand hier fälschlich 49; mit dem
10-mm-Motoradapter und der gemessenen Garnitur von 38 mm sind es seit
Rev. 31 57 mm).
Nach oben begrenzt es die Montage (die obere Laser-Schraubenreihe muss beim
Verschrauben neben dem Z-Wagen liegen, also höchstens +7,8 mm über Lochmitte),
nach unten der Langlochhub von −8 mm. Seit Rev. 27 hängt der Laser dafür 5 mm
tiefer am Schlitten; vorher reichte das Fenster erst ab f = 11 mm.
Mit der 95-mm-Schiene stand hier einmal `f ≤ 27,1 mm` — das war die alte,
kurze Z-Achse.

Eine dickere Opferplatte wirkt wie eine Langlochstellung nach unten (1 mm
dicker = 1 mm tiefer) und verschiebt das Fenster nur in diese Richtung.

## Z-Antrieb: Trapezgewindespindel Tr8×2 mit Anti-Backlash-Garnitur `[w]`

**Bestellt** (Spindel + Garnitur + Kupplung), Maße aus den Herstellerbildern
der Angebote — noch nicht am Teil gemessen:

| Wert | Maß | Status |
|---|---|---|
| Spindel | Tr8×2, 1-gängig, Steigung = Vorschub 2 mm, 200 mm lang | `[w]` |
| Ende | kein angedrehter Zapfen — Ø8 ist der Gewindeaußendurchmesser | `[w]` |
| Flanschmutter: Flansch | **Ø22 mm**, Bauhöhe **15 mm** | `[w]` |
| Flanschmutter: Bund Ø10 × 2 mm | auf der **Oberseite**, Flansch unten **glatt** | `[v]` am Teil |
| Flanschmutter: Dicke der Flanschplatte | **3,5 mm** | `[v]` am Teil gemessen |
| Flanschmutter: Lochkreis | **Ø16 mm**, **4 × Ø3,5 durchgehend** (kein Gewinde!) | `[w]` |
| Gleitmutter (zweite Hälfte) | **Ø14 × 15 mm**, mit Mitnehmernut | `[w]` |
| Druckfeder | **Ø12 × 50 mm** freie Länge | `[w]` |
| Garnitur eingebaut (Unterseite Flansch bis Oberkante Gleitmutter) | **38 mm** | `[v]` am Teil gemessen |
| Kupplung | UniTak3D 5 → 8 mm (B096G1GZH5), **starre Klemmkupplung**, seitliche Klemmschrauben | `[w]`, Maße am Teil messen |

Wichtig für den Entwurf: die Befestigungslöcher sind **Durchgangslöcher**, das
Gewinde muss also im Druckteil sitzen — mit den vorhandenen M3-Messingeinsätzen
(Ø4,6 × 7) braucht der Flanschsitz mindestens 9 mm Material. Das Regal des
Mutternwinkels ist deshalb 10 mm dick.

Im Skript steckt das als `spindel_d` 8,0 · `spindel_durchgang` 8,6 ·
`t8_flansch_d` 22 · `t8_lochkreis` 16 · `t8_garnitur_h` 45.

**Zur Kupplung:** weil es kein oberes Spindellager gibt, hängt der Z-Schlitten
(5,6 N) axial an der Kupplung. Damit sind **Oldham- und Klauenkupplungen
ausgeschlossen** — ihre Naben sind nicht axial verbunden, sie setzen Wellen
voraus, die jede für sich gelagert sind. Bleiben die einteiligen: starre
Klemmhülse oder Wendelkupplung. Bestellt ist die UniTak3D 5 × 8, eine
**starre Klemmkupplung** mit seitlichen Klemmschrauben — die beste Bauart für
diese Achse: trägt die Last axial voll und greift rundum auf die
Gewindespitzen. Beide Wellen über den ganzen Klemmbereich einstecken, etwa bis
zur Mitte — Begründung in `toolhead-z.md`.

**Am gelieferten Teil zu prüfen (drei Dinge):**

1. ~~Einbauhöhe der Garnitur~~ **Erledigt** `[v]`: **38 mm** gemessen
   (`t8_garnitur_h`, bis Rev. 30 auf 45 mm geschätzt). Sie bindet den
   Verfahrweg nach oben, der damit 93,6 mm beträgt.
2. ~~Flanschfläche plan?~~ **Erledigt** `[v]`: die Unterseite des Flansches
   ist glatt, der Bund Ø10 × 2 sitzt oben. Die glatte Seite liegt auf dem
   Regal, es braucht keinen Freiraum und keinen Zwischenring (Rev. 25–27 gab
   es einen Flanschring, weil der Bund unten vermutet war). Mit 3,5 mm
   Flanschdicke genügen **M3×8** bei 4,5 mm Eingriff.
3. **Maße der Kupplung**: Länge, Durchmesser, Länge des Klemmschlitzes.
   Daraus folgt `kupplung_griff` (modelliert 8 mm, für diese Kupplung eher 12).
   Der Wert verschiebt die Kupplung in Z und damit den Verfahrweg. Seit dem
   Motoradapter (Rev. 30) kommt die Kupplung ohnehin nur 8 mm auf die
   Motorwelle, sonst rutscht ihre obere Klemmschraube in die Konsole — also
   auch nachsehen, **wo die Klemmschrauben sitzen** (angenommen: Mitte der
   Nabe).

Und eine Entscheidung, die daraus schon feststeht: **die Spindel wird
gekürzt**, auf `spindel_zuschnitt` = 160 mm (gebraucht 147,6 mm). Ungekürzt
hängt das untere Ende bis Z = −80 und drückt die mögliche Werkstückhöhe von 59
auf 45 mm — unter die geforderten 50.

Steigungswinkel 5,2° am Flankendurchmesser → **selbsthemmend** (TR8×8 mit 20°
wäre es nicht). Betriebsmoment ≈ 70 mNm, davon 64 mNm allein die
Federvorspannung der Garnitur; eine Klemmnabe auf Ø8 trägt ein Mehrfaches,
auch auf Gewindespitzen. Rechnung in `tools/toolhead_check.py`, Abschnitt 7.

## Schrittmotortreiber: A4988 oder TMC? `[w]`

**Empfehlung: TMC2209 — aber nicht wegen des Microsteppings.** Das ist der
verbreitete Denkfehler, und die Zahlen dieser Achse zeigen warum.

### Warum die Auflösung kein Argument ist

| | 1/16 (A4988-Maximum) | 1/256 (TMC) |
|---|---|---|
| Z, Tr8×2 | 1600 Schritte/mm → **0,63 µm** | 25 600/mm → 0,04 µm |
| X/Y, GT2-20T (40 mm/U, angenommen) | 80 Schritte/mm → **12,5 µm** | 1280/mm → 0,8 µm |

Zwei Gründe, warum das untere Ende dieser Tabelle nichts bringt:

1. **Reibungstotzone.** Der Rotor rückt erst weiter, wenn das Moment die
   Reibung überwindet: `T = T_halt · sin(el. Winkel)`, 90 el. Grad = ein
   Vollschritt = 1,8 mech. Grad. Bei 70 mNm Reibung (davon 64 mNm allein die
   Federvorspannung der Anti-Backlash-Garnitur) gegen 400 mNm Haltemoment sind
   das 0,20 mech. Grad, also **1,1 µm Totzone** in Z. Ein 1/16-Mikroschritt ist
   mit 0,63 µm schon feiner als das, was die Achse überhaupt auflösen kann.
   `toolhead_check.py` Abschnitt 7 rechnet beide Werte mit.
2. **Schrittrate.** 1/256 extern ist bei Gravurgeschwindigkeit nicht
   übertragbar: 300 mm/s auf X wären bei 1/16 schon 24 kHz Schrittrate (nahe
   am Limit eines 8-Bit-GRBL), bei 1/256 rechnerisch 384 kHz. Deshalb
   **interpoliert** der TMC intern (MicroPlyer): man füttert ihn mit 1/16 und
   bekommt die Laufruhe von 1/256, ohne Schrittrate zu bezahlen. Das ist der
   eigentliche Nutzen — Laufruhe, nicht Genauigkeit.

### Was der TMC wirklich bringt

* **Leise.** StealthChop2 arbeitet oberhalb des Hörbereichs. Bei
  Gravurjobs über Stunden ist das der praktisch größte Unterschied.
* **Kühler und sauberer geregelt.** Weniger Stromwelligkeit heißt weniger
  Motorerwärmung und weniger Resonanz — Resonanz zeigt sich in der Gravur als
  Streifen.
* **Strom per UART setzen** (TMC2209) statt Vref-Poti abgleichen; dazu
  Diagnose (Übertemperatur, Leitungsbruch) und CoolStep.
* StallGuard4 könnte sensorlos referenzieren — brauchen wir nicht, die
  Z-Achse hat die Gabellichtschranke.

Dagegen der A4988: **billiger** (~1,50 € gegen 4–6 €), robust, nichts zu
konfigurieren, und er verträgt bis 35 V. Für 3 Achsen ist der Aufpreis rund
15 € — gegenüber Spindel plus Garnitur belanglos.

| | A4988 | TMC2209 |
|---|---|---|
| Versorgung | 8–35 V | ~5–28 V (abs. max 29) |
| Strom | bis 2 A/Phase (IC), ohne Kühlung real ~1 A | bis 2 A RMS (IC), Modul je nach Kühlkörper ~1,2–1,4 A |
| Microstepping | max. 1/16 | 8/16/32/64 extern, intern auf 1/256 interpoliert |
| Konfiguration | Jumper + Vref-Poti | Jumper oder UART |

Bei 24 V passen beide. Über 29 V fällt der TMC2209 aus (dann TMC2130/5160
oder DRV8825). Nur wenn die Motoren 2-A-Typen sind, wird es am 2209-Modul eng.

### Fallstricke, falls es TMC wird

* **Nicht mitten in der Bewegung zwischen StealthChop und SpreadCycle
  umschalten** (`TPWMTHRS`): der Sprung ist beim Laser als Linie sichtbar. Für
  X/Y einen Modus über den ganzen Geschwindigkeitsbereich wählen — SpreadCycle,
  wenn schnell gefahren wird. Für Z ist StealthChop unkritisch, die Achse
  fährt nur zwischen den Jobs.
* **Drehrichtung.** In einem A4988-Sockel läuft ein TMC-Modul
  spiegelbildlich (DIR-Logik), also Stecker drehen oder in der Firmware
  invertieren.
* Standalone-Betrieb kann StealthChop bei hoher Beschleunigung Schritte
  verlieren — mit UART ist das einstellbar, ohne nicht.

Offen: **welches Board** die Maschine bekommt. Nur mit UART-Anbindung
(SKR/Octopus, FluidNC am ESP32 o. ä.) sind Strom und Chopper einstellbar; auf
einem klassischen Uno-CNC-Shield bleibt es beim Standalone-Modus mit Jumpern.

## Normteile (aus hardware.md, `[w]`)

| Gewinde | Durchgang | Kopf-Ø | Kopfhöhe |
|---|---|---|---|
| M3 | 3,4 | 5,5 | 3,0 |

Scheiben M3: DIN 125 Ø 7 × 0,5 am Laser (Langloch 4,0 breit, 1,5 mm Auflage je
Seite) · DIN 9021 Ø 9 × 0,8 am schwimmenden Mutternwinkel (deckt dort das
Übermaß Ø4,6).
