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
**Portalführung** (X-Achse), wo MGN15H = 25 × 25 passt. Dort steht die
Bestätigung mit `Bohrlehre_XWagen` noch aus.

Die `Bohrlehre_ZWagen` trug bis dahin beide MGN9-Lochbilder (10 und 16 mm
längs), um die Baugröße zu entscheiden. Sie folgt jetzt dem Parameter
`z_wagen_loch_laengs` und hat nur noch vier Löcher.

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
Langlöcher (±8 mm, nach oben nutzbar +2,8 mm) eingestellt. Der
Validierungsbericht rechnet die Stellung je f aus.

Selbst messen: Papier aufs Bett, 1–2 % Leistung, Höhe variieren bis der Punkt
am kleinsten ist, dann Gehäuseunterkante → Papier messen. Sobald der Wert
bekannt ist, hier eintragen und auf `[v]` setzen.

## Maschinenmaße für die Z-Achse

| Wert | Maß | Status |
|---|---|---|
| Bezugsebene (Mitte X-Wagen-Lochbild) → Bettoberfläche | **130 mm** | `[?]` am 2026-09-17 genannt, auf cm gerundet |
| dickstes Werkstück | **50 mm** | Vorgabe |

Beide stehen als `bett_abstand` und `werkstueck_max` im Skript — sie erzeugen
keine Geometrie, sondern nur die Fokusrechnung im Bericht. Aus ihnen folgt die
harte Grenze **f ≤ 27,1 mm**, damit 0–50 mm Werkstückdicke erreichbar bleiben;
darüber sind es `77,1 mm − f`. Grund: die obere Laser-Schraubenreihe muss beim
Verschrauben neben dem Z-Wagen liegen, und das begrenzt, wie hoch der Laser
sitzen darf.

Eine dickere Opferplatte wirkt wie eine Langlochstellung nach unten (1 mm
dicker = 1 mm tiefer) und verschiebt das Fenster nur in diese Richtung.

## Normteile (aus hardware.md, `[w]`)

| Gewinde | Durchgang | Kopf-Ø | Kopfhöhe |
|---|---|---|---|
| M3 | 3,4 | 5,5 | 3,0 |

Scheiben M3: DIN 125 Ø 7 × 0,5 am Laser (Langloch 4,0 breit, 1,5 mm Auflage je
Seite) · DIN 9021 Ø 9 × 0,8 am schwimmenden Mutternblock (deckt dort das
Übermaß Ø4,6).
