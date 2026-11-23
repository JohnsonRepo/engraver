# Gravur: Hanfblatt

Hanfblatt mit sieben gezahnten Fiedern und Stiel, **66,6 × 80 mm**. Zwei
Ausführungen aus derselben Geometrie, jede als SVG für LightBurn und als
fertiger G-Code für CNCjs.

<p>
<img src="hanfblatt-flaeche.svg" width="300" alt="Hanfblatt als Fläche mit ausgesparten Adern">
<img src="hanfblatt-linie.svg" width="300" alt="Hanfblatt als Strichgravur">
</p>

| Datei | Inhalt | Laufzeit |
|---|---|---|
| [`hanfblatt-flaeche.gc`](hanfblatt-flaeche.gc) | Fläche zeilenweise (0,1 mm), Mittelrippen und Seitenadern bleiben hell, danach der Umriss als Linie | etwa 1 h 04 min |
| [`hanfblatt-linie.gc`](hanfblatt-linie.gc) | Strichgravur: Umriss, 7 Mittelrippen, 154 Seitenadern | etwa 9 min |
| [`hanfblatt-flaeche.svg`](hanfblatt-flaeche.svg) | Umriss und Adern als geschlossene Formen, für **Fill** in LightBurn | |
| [`hanfblatt-linie.svg`](hanfblatt-linie.svg) | Umriss und Adern als Linien, für **Line** in LightBurn | |

Die Laufzeit rechnet `tools/gravur_hanfblatt.py` mit dem Planer von GRBL
aus: Beschleunigung, Ecken und Zeilenwenden, mit den Standardwerten
`$110/$111 = 500 mm/min` und `$120/$121 = 10 mm/s²`. Die Fläche dauert so
lange, weil die Maschine nur 500 mm/min fährt (siehe [unten](#warum-500-mmmin)).

## Lage auf dem Werkstück

Der G-Code bezieht sich auf den Werkstücknullpunkt G54 an der Innenecke des
Anschlags vorn rechts ([spannmittel.md](../docs/spannmittel.md#nullpunkt-einrichten-einmal)).

| | |
|---|---|
| Motiv | X −76,6 bis −10, Y 10 bis 90 mm: 10 mm Abstand zum Anschlag in beiden Richtungen |
| Ausrichtung | Spitze nach hinten (Y+), Stiel zum Anschlag hin; von vorn gesehen steht das Blatt aufrecht |
| Fahrten | Die Fläche läuft 2 mm über das Motiv hinaus, mit Laser aus. Alle Fahrten bleiben bei X ≤ 0 und Y ≥ 0 |
| Werkstück | mindestens 80 × 95 mm |

## Gravieren aus CNCjs

1. Werkstück an den Anschlag legen und spannen ([spannmittel.md](../docs/spannmittel.md)).
2. **Homing**, Laser fokussieren ([Autofokus](../docs/autofokus.md)).
3. Datei laden: im Browser mit „Upload G-code“ oder dauerhaft
   `scp gravur/hanfblatt-linie.gc laser@laser.local:gcode/`.
4. Makro **Rahmen**, die Hand am Not-Aus, dann **Start**. Schutzbrille, dabei bleiben.

## Leistung zuerst testen

Die Werte im G-Code sind Startwerte für Holz mit dem 4-W-Modul, nicht
gemessen:

| | Vorschub | Leistung |
|---|---|---|
| Linien und Umriss | F500 | S600 (60 %) |
| Fläche | F500 | S200 (20 %), Zeilenabstand 0,1 mm |

Vor dem ersten Stück auf einem Reststück desselben Holzes testen: in
LightBurn mit dem Material-Test (Laser Tools → Material Test) oder mit
einem kleinen Blatt aus dem Skript. Mit den gefundenen Werten dann neu erzeugen:

```sh
python3 tools/gravur_hanfblatt.py --hoehe 40 --abstand 5     # kleines Testblatt
python3 tools/gravur_hanfblatt.py --linie-s 500 --flaeche-s 250
```

Wird die Fläche streifig oder sind die Kanten der Zeilen versetzt, hat der
Riemen in X Spiel: Die Zeilen laufen abwechselnd hin und her.

## Warum 500 mm/min

`$110` und `$111` stehen noch auf dem GRBL-Standard von 500 mm/min
([verkabelung.md](../docs/verkabelung.md#grbl-einstellungen)). Ein höherer Vorschub im
G-Code bringt nichts: GRBL fährt trotzdem nur 500 mm/min, rechnet die
M4-Leistung aber gegen den programmierten Vorschub, und der Laser brennt
schwächer. Werden `$110/$111` und `$120/$121` später erhöht, mit diesen
Werten neu erzeugen, dann wird die Fläche deutlich schneller, z. B.:

```sh
python3 tools/gravur_hanfblatt.py --max-f 3000 --beschl 500 --flaeche-f 3000 --flaeche-s 600
```

## In LightBurn

* SVG importieren, es kommt in der richtigen Größe (66,6 × 80 mm).
* `hanfblatt-flaeche.svg`: Ebene auf **Fill**, Intervall 0,1 mm. Die Adern
  sind Löcher in der Form und bleiben hell. Für eine scharfe Kante den
  Umriss zusätzlich als Line (Fill + Line).
* `hanfblatt-linie.svg`: Ebene auf **Line**.
* Vorschub höchstens 500 mm/min, solange `$110/$111` so stehen. Speichern wie
  in [pi.md](../docs/pi.md#lightburn-auf-dem-mac): „Absolute Coords“, „Save GCode“.
* Unter etwa 50 mm Höhe werden die Seitenadern der Fläche sehr fein. Dann
  besser die Linienfassung oder mit `--hoehe` neu erzeugen.

## Neu erzeugen

```sh
python3 tools/gravur_hanfblatt.py            # 80 mm hoch, 10 mm vom Nullpunkt
python3 tools/gravur_hanfblatt.py --help     # alle Optionen
```

| Option | Standard | |
|---|---|---|
| `--hoehe` | 80 mm | Höhe mit Stiel, die Breite folgt |
| `--abstand` | 10 mm | Abstand zum Nullpunkt in X und Y |
| `--linie-f` / `--linie-s` | 500 / 600 | Vorschub und Leistung für Linien und Umriss |
| `--flaeche-f` / `--flaeche-s` | 500 / 200 | Vorschub und Leistung für die Fläche |
| `--zeilen` | 0,1 mm | Zeilenabstand der Fläche |
| `--ueberlauf` | 2 mm | Überlauf der Zeilen mit Laser aus |
| `--rippe` / `--ader` | 0,8 / 0,45 mm | Breite der hellen Mittelrippe am Ansatz und der Seitenadern (Fläche) |
| `--max-f` / `--beschl` | 500 / 10 | `$110/$111` und `$120/$121` der Maschine: Grenze für den Vorschub und Laufzeit |

Das Skript braucht nur Python 3 und prüft am Ende: Umriss ohne
Selbstschnitt, Adern ganz im Blatt und ohne Überlappung, alle Fahrten im
Arbeitsfeld und auf dem Werkstück, Laser nur im Motiv an, keine Eilfahrt
mit Laser, Vorschub nicht über `$110/$111`. Exit-Code 0 = alles bestanden.
