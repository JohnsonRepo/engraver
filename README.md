# engraver

CNC-Engraver mit Diodenlaser — Konstruktionsskripte und Notizen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil, darauf 2 × 2040 Aluprofil |
| Y-Achse | 2 Linearführungen oben auf den 2040ern |
| Portal | Halterungen auf den Y-Schlitten, dazwischen ein 2020 Aluprofil |
| X-Achse | Linearführung am Portalprofil |
| Z-Achse | Grundplatte am X-Wagen, darauf eine Linearführung |
| Werkzeug | Diodenlaser am Toolhead auf dem Z-Wagen |

## Inhalt

```
fusion/ToolheadGrundplatte/   Fusion-Skript + Manifest für die Toolhead-Grundplatte
docs/toolhead-grundplatte.md  Maßkette, Verschraubung, Druck- und Prüfhinweise
docs/hardware-notizen.md      Kaufteilmaße mit Verifizierungsstatus
tools/geometrie_check.py      rechnerische Prüfung der Grundplatte (ohne Fusion)
```

## Teile

### Toolhead-Grundplatte (Z-Achse)

Trägt den Diodenlaser auf dem MGN9-Wagen der Z-Achse. Die Platte ist eine
Versatzplatte: ein 6 mm hohes Auflagepad setzt sie von der Stirnfläche des
Wagens ab, die Laser-Anschraubfläche liegt 12 mm davor. Damit ist die
Montagehöhe des Wagens (10 mm) explizit in der Maßkette enthalten — das war
die Ursache dafür, dass die erste Platte nicht bündig saß.

Laser-Bohrbild 39 × 15 mm (4 × M3), als Langlöcher ausgeführt, solange das
Bohrbild nicht am Teil verifiziert ist. Details in
[docs/toolhead-grundplatte.md](docs/toolhead-grundplatte.md).

## Skript in Fusion ausführen

Den Ordner `fusion/ToolheadGrundplatte/` (`.py` **und** `.manifest`) hierhin
kopieren:

* macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`
* Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`

Dann in Fusion *Utilities → Scripts and Add-Ins → ToolheadGrundplatte → Run*.
Jeder Lauf legt ein **neues Dokument** an, das aktive bleibt unberührt. Am Ende
erscheint ein Validierungsbericht mit Maßkette, Schraubenliste und den noch zu
prüfenden Maßen.

Maße danach über *Ändern → Parameter* anpassen — Lochbilder, Dicken,
Durchmesser und Musterabstände hängen an User-Parametern.

## Geometrie prüfen

```sh
python3 tools/geometrie_check.py
```

Prüft ohne Fusion die Maßkette, Freigänge zur Führung, Materialstege,
Schraubenlängen, Scheibenauflage, Langloch-Toleranzen und Druckbarkeit gegen
beide Wagenvarianten (MGN9C und MGN9H). Exit-Code 0 = alles bestanden.
