# engraver

CNC-Engraver mit Diodenlaser — Konstruktionsskripte, Prüfwerkzeuge und Notizen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil, darauf 2 × 2040 Aluprofil |
| Y-Achse | 2 Linearführungen oben auf den 2040ern |
| Y-Antrieb | je Seite eine senkrechte Edelstahlwelle Ø5 hinter der hinteren Traverse (2040 hochkant), ein Endlosriemen zum NEMA 17 in der Mitte |
| Portal | Halterungen auf den Y-Schlitten, dazwischen ein 2020 Aluprofil |
| X-Achse | Linearführung MGN15 am Portalprofil |
| Z-Achse | Toolhead am MGN15H-Wagen: eigene MGN9-Führung, NEMA 17 über Tr8×2-Spindel |
| Werkzeug | Diodenlaser am Z-Schlitten |

## Inhalt

```
fusion/ToolheadZ/              Baugruppe: kompletter Toolhead mit Z-Achse  ← aktuell
fusion/YMotorhalter/           Y-Motorhalter an der hinteren 2040  ← neu
fusion/ToolheadGrundplatte/    nur die Laserplatte (vom Toolhead überholt)
docs/toolhead-z.md             Maßkette, Antrieb, Montage, Druck, Prüfliste
docs/toolhead-z-layout.svg     maßstäbliche Seiten- und Vorderansicht
docs/toolhead-z-antrieb.svg    Skizze des Z-Antriebs: Motor, Kupplung, Spindel, Garnitur
docs/toolhead-grundplatte.md   Doku der Einzelplatte
docs/hardware-notizen.md       Kaufteilmaße mit Verifizierungsstatus
docs/ausrichten.md             Gestell und Y-Achse mit einer Winkel-Messbox ausrichten
docs/y-motorhalter.md          Y-Antrieb: Riemenlauf, Riemenlänge, Spannen, Montage, Druck
docs/y-antrieb.svg             Skizze: Motorriemen von oben, Halter, Schnitt
tools/bauraum.py               Bauräume als Quader — Quelle für Prüfung + Zeichnung
tools/toolhead_check.py        rechnerische Prüfung der Baugruppe (ohne Fusion)
tools/layout_zeichnen.py       erzeugt die Layout-Zeichnung
tools/antrieb_zeichnen.py      erzeugt die Antriebsskizze
tools/geometrie_check.py       Prüfung der Einzelplatte
tools/y_motorhalter_check.py   rechnerische Prüfung des Y-Motorhalters
tools/y_antrieb_zeichnen.py    erzeugt die Y-Antriebsskizze
```

## Teile

### Toolhead Z-Achse (aktuell)

Kompletter Toolhead als Baugruppe aus sechs gedruckten Teilen: **Trägerplatte**
am MGN15H-Wagen des Portals — mit angeformter Motorkonsole für den NEMA 17 —,
ein **Motoradapter**, der den Motor 10 mm über die Konsole hebt,
**Schlittenplatte** auf dem MGN9H-Z-Wagen mit dem Laser, ein **Mutternwinkel**
als Flanschsitz für die Tr8×2-Anti-Backlash-Garnitur, schwimmend verschraubt,
eine schwarze **Schaltfahne** und ein **Endschalterhalter** für die
Gabellichtschranke.

Nutzbarer Z-Verfahrweg **93,6 mm** (MGN9-Schiene 200 mm), Strahlachse 58,5 mm
vor der X-Wagen-Stirnfläche, NEMA 17 mit allen vier Schrauben zugänglich. Die
Laserhöhe ist über senkrechte Langlöcher ±8 mm verstellbar, damit der
Fokusabstand des Moduls nicht in der Geometrie steckt. Werkstückhöhe bis 59 mm
— begrenzt nicht vom Verfahrweg, sondern von der Plattenunterkante, die in X
mitfährt — die 200-mm-Spindel wird dafür auf 160 mm gekürzt. Details in
[docs/toolhead-z.md](docs/toolhead-z.md).

### Y-Motorhalter (neu)

Hält den NEMA 17 der Y-Achse an der Rückseite der hinteren 2040, mit zwei
M5-Nutensteinen in der unteren Nut — vor der oberen läuft der Riemen. Der
Motor steht auf einem auskragenden Boden, Ritzel und zwei Umlenkrollen hängen
darunter auf Höhe der oberen Nut. Die Rollen legen den Endlosriemen, der beide senkrechten
Wellen verbindet, als **Omega** um das Motorritzel: 180 Grad, 10 Zähne im
Eingriff. Gerade durchlaufend wäre es weniger als ein Zahn. Gespannt wird
über Langlöcher und eine Spannschraube.

**Wichtig:** Ein Riemen dreht beide Wellen gleichsinnig. Die Y-Wagen müssen
deshalb am **selben Trum** ihres Y-Riemens hängen, nicht spiegelbildlich.
Wellenabstand und Wellenlage sind noch nicht gemessen; die Riemenlänge folgt
aus dem Abstand. Details in [docs/y-motorhalter.md](docs/y-motorhalter.md).

### Toolhead-Grundplatte (überholt)

Die erste Ausführung: nur die Platte, die den Laser am MGN9-Z-Wagen hält, ohne
Z-Antrieb. Das Konzept — Auflagepad, das die Montagehöhe des Wagens aufnimmt —
steckt unverändert in der Schlittenplatte des Toolheads.
Siehe [docs/toolhead-grundplatte.md](docs/toolhead-grundplatte.md).

## Skript in Fusion ausführen

Den Ordner unter `fusion/` (`.py` **und** `.manifest`) hierhin kopieren:

* macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`
* Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`

Dann in Fusion *Utilities → Scripts and Add-Ins → ToolheadZ (bzw. YMotorhalter)
→ Run*. Jeder Lauf
legt ein **neues Dokument** an, das aktive bleibt unberührt. Am Ende erscheint
ein Validierungsbericht mit Maßkette, Verfahrweg, Schraubenliste und
Montagereihenfolge.

## Prüfen und zeichnen

```sh
python3 tools/toolhead_check.py     # Maßkette, Kollisionen, Schrauben, Druck
python3 tools/layout_zeichnen.py    # docs/toolhead-z-layout.svg neu erzeugen
python3 tools/antrieb_zeichnen.py   # docs/toolhead-z-antrieb.svg neu erzeugen
python3 tools/geometrie_check.py    # nur die Einzelplatte
python3 tools/y_motorhalter_check.py  # Y-Motorhalter: Riemenlauf, Freigänge, Schrauben
python3 tools/y_antrieb_zeichnen.py   # docs/y-antrieb.svg neu erzeugen
```

`toolhead_check.py` importiert das Fusion-Skript mit gestubbtem `adsk`-Modul und
prüft dieselbe Maßkette, die das Skript zum Bauen verwendet: Y-Kette,
Verfahrweg mit allen vier Begrenzungen, Kollisionen über 21 Stellungen des
Verfahrwegs, Materialstege, Schraubenlängen und -eingriffstiefen,
**Werkzeugzugang für jede Schraube** (freie Inbus-Länge im Zustand, in dem sie
verschraubt wird), Lochbildtoleranzen, Druckbarkeit — und statisch, dass jeder
im Skript benutzte Maß- und Lageschlüssel existiert. Exit-Code 0 = alles
bestanden.

**Stand:** alle Prüfungen bestanden (Rev. 14). Der Zugangskonflikt zwischen
Laser und Z-Wagen ist gelöst, indem der Laser 30,75 mm tiefer hängt und über
senkrechte Langlöcher eingestellt wird —
[Laserhöhe](docs/toolhead-z.md#laserhöhe-langloch-statt-rechnen).
