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
| Linearführung Z | MGN9 (C oder H — noch offen) | `[?]` |
| Wagen-Lochbild | 15 quer × 16 längs (MGN9H) bzw. 15 × 10 (MGN9C) | `[w]` |
| Montagehöhe Wagen | 10 mm über der Schienen-Auflageebene | `[w]` |
| Schiene MGN9 | 9 breit × 6,5 hoch | `[w]` |
| Gewindetiefe im Wagen | ~2,5 mm (M3) → max. M3×8 bei 6 mm Pad | `[w]` |

**Offener Widerspruch:** `hardware.md` notiert eine eigene Messung am
Toolhead-Wagen von **26 längs × 25 quer**, was MGN15H entspricht, nicht MGN9.
Vor dem Druck mit `Bohrlehre_Wagen` klären. Ist es doch MGN15H, ändern sich
`wagen_loch_quer` = 25, `wagen_loch_laengs` = 25, `wagen_hoehe` = 16 und
`wagen_breite` = 32 — die Platte baut sich über die Parameter um, das
Auflagepad muss dann auf mindestens 32 × 32 mm wachsen.

## Diodenlaser

| Wert | Maß | Status |
|---|---|---|
| Bohrbild (Konstruktionsgrundlage) | 39 hoch × 15 quer, 4 × M3 | Nutzerangabe, am Teil noch nicht gegengeprüft |
| Gehäuse (angenommen) | 35 × 35 mm Querschnitt | `[w]` |

`hardware.md` führt für das Modul *Laser Tree LT-20W-A* ein gemessenes
Bohrbild von **40 hoch × 16 quer** (`[?]`, Messbasis unsicher). Beide Werte
liegen genau 1 mm auseinander — das riecht nach unterschiedlicher Messbasis
(Lochkante statt Lochmitte) und nicht nach zwei verschiedenen Modulen. Die
Langlöcher der Grundplatte decken deshalb quer 12,4 – 17,6 mm und senkrecht
37,6 – 40,4 mm ab, damit beide Varianten passen.

Ist das Gehäuse tiefer oder flacher als 35 mm, `laser_tiefe` anpassen — davon
hängt nur die berechnete Lage der Strahlachse ab, nicht die Geometrie.

## Normteile (aus hardware.md, `[w]`)

| Gewinde | Durchgang | Kopf-Ø | Kopfhöhe |
|---|---|---|---|
| M3 | 3,4 | 5,5 | 3,0 |

Große Scheibe DIN 9021 M3: Ø 9 × 0,8 — bei Langlöchern Pflicht.
