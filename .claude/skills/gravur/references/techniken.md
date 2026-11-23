# Techniken und Fehlersuche

## Inhalt

1. Raster: Intervall, Overscan, Zeilenversatz
2. Schrift
3. SVG
4. Bilder und Fotos
5. Materialtest lesen
6. Was passiert → was tun

## 1. Raster: Intervall, Overscan, Zeilenversatz

Füllen und Bilder brennen in waagrechten Zeilen: X fährt nur den Toolhead,
Y das ganze Portal und nur einen Schritt je Zeile. Hinten fängt es an,
dann abwechselnd nach rechts und nach links.

- **Intervall** (`--intervall`, Zeilenabstand und bei Bildern die
  Pixelgröße): 0,1 mm Standard, so breit wie der Brennfleck. Fotos im
  Dither 0,15 mm, sonst verschwimmen die Punkte auf Holz. Feiner (0,08) nur
  bei Eloxal. Die Dauer wächst mit 1/Intervall.
- **Overscan:** Jede Zeile fährt vor und nach dem Brennen ein Stück mit
  `S0` weiter, damit der Kopf auf Tempo ist. Standard aus F und
  Beschleunigung: 1,3 · v²/(2a), bei F2000 1,4 mm, bei F3000 3,3 mm. Er
  ragt über die Gravur hinaus (Laser aus) und wird nur gegen das
  Arbeitsfeld geprüft, nicht gegen das Werkstück.
- **Zeilenversatz:** Bidirektional verschieben sich Hin- und Rückzeilen um
  Bruchteile eines Millimeters (Riemenspiel, Verzug des Lasers). Zu sehen
  als gezackte senkrechte Kanten. Prüfen: großes „IIII“ in Arial Black
  füllen (`text IIII --schrift "Arial Black" --hoehe 15`). Liegen die Rückzeilen (rechts → links)
  um d mm zu weit links, `--zeilenversatz d`; zu weit rechts, `-d`. Oder
  `--einseitig` (doppelte Zeit). Gemessenen Wert in
  `references/maschine.md` und hier eintragen.
- **M4** hält die Schwärzung auch dann gleich, wenn die Fahrt stockt;
  nur die Zeit wird länger.

## 2. Schrift

- `--hoehe` ist die **Versalhöhe** (ein H), nicht die Höhe mit
  Unterlängen. `--breite` ist die ganze Breite der Tinte.
- Gefüllt lesbar ab etwa 2 mm Versalhöhe, darunter fette Schriften
  (`--schrift "Arial Bold"`, `"Arial Black"`). Große Schrift ab etwa 40 mm
  geht mit `--art kontur` viel schneller.
- Schriften: Name oder Pfad. Auf dem Mac z. B. Arial, Arial Bold, Arial
  Black, Georgia, Georgia Bold, Times New Roman, Futura, DIN Alternate
  Bold, Avenir Next, Courier New, Trebuchet MS, Brush Script, Snell
  Roundhand, Chalkduster. In `.ttc`-Sammlungen wählt der volle Name die
  Schnitt (z. B. "Avenir Next Bold"). Fehlt ein Zeichen, sagt das Skript
  welches.
- Mehrere Zeilen mit `\n` im Text, `--ausrichtung links|mitte|rechts`,
  `--zeilenfaktor` (Standard 1,25).

## 3. SVG

- Gelesen werden `path`, `rect` (auch gerundet), `circle`, `ellipse`,
  `line`, `polyline`, `polygon`, Gruppen mit `transform`, Farben aus
  Attributen, `style=` und einfachen CSS-Klassen (`.cls-1{fill:#fff}` wie
  aus Illustrator), `fill-rule`.
- **Nicht gelesen:** `<text>` (in Inkscape: Pfad → Objekt in Pfad),
  eingebettete Bilder (die mit `bild` gravieren), `<use>`/Klone
  (Verknüpfung lösen), Masken und Beschneidungspfade, Verläufe (gelten als
  dunkel). Das Skript meldet, was es übersprungen hat.
- **Füllen** malt wie ein Browser in Reihenfolge: dunkle Flächen brennen,
  helle radieren, was darunter liegt (weißer Stern im schwarzen Kreis).
  Ein weißer Hintergrund fällt weg und zählt nicht zur Größe.
- **Linie** fährt die Mittellinie; `stroke-width` wird nicht beachtet.
  Gibt es Striche im SVG, nur die; sonst die Umrisse aller Flächen.
- Ohne `--breite`/`--hoehe` gilt die Größe aus `width`/`viewBox` (mm, cm,
  in; px = 1/96 Zoll).

## 4. Bilder und Fotos

| Art | wann | Stellschrauben |
|---|---|---|
| `schwellwert` | Logo, Schrift, Scherenschnitt als PNG/JPG | `--schwelle` 0…1 (Dunkelheit), Standard 0,5 |
| `dither` | Fotos; der Diodenlaser kann kein echtes Grau | `--gamma` > 1 hellt Mitteltöne auf, Intervall 0,15–0,2 |
| `graustufen` | weiche Verläufe auf gleichmäßigem Material (MDF, Birke) | `--s-min` (hellstes Grau, Standard 40 % von S), `--stufen` |
| `linien` | Foto als Zeichnung (Tierportrait, Gesicht) | `--detail` (mm, größer = gröber), `--staerke` (größer = weniger), `--dunkel` 0,2–0,35 füllt dunkle Flächen |

- Vor dem Raster: EXIF-Drehung, Transparenz wird weiß, weiße Ränder fallen
  weg (`--nicht-zuschneiden`), Autokontrast 1–99 %
  (`--kein-autokontrast`).
- **Schiefer und Eloxal** brennen hell: `--invertieren`, damit dunkle
  Bildteile dunkel bleiben.
- Gute Fotos: Motiv freigestellt, heller Hintergrund, kräftiger Kontrast.
  Hintergrund vorher entfernen spart Zeit (weiße Pixel brennen nicht).
- Graustufen auf Holz sind nicht linear: Ohne Test auf dem Material lieber
  `dither`.

## 5. Materialtest lesen

`materialtest` brennt Felder Leistung (Spalten, %) × Vorschub (Zeilen,
mm/min), beschriftet, mit einem Kreuz oben links, das am Anfang und am
Ende brennt.

- Das **Kreuz doppelt** → Schritte verloren: Beschleunigung oder Riemen
  prüfen, bevor man den Werten glaubt.
- **Zum Füllen** das Feld mit der kleinsten Energie E = S/F wählen, das
  gleichmäßig dunkel ist. Mehr Energie gibt Brandränder und breitere
  Linien.
- **Für Linien** dieselbe Energie oder etwas mehr.
- **Grenze nach unten** (gerade sichtbar) als Hinweis für `--s-min` bei
  Graustufen notieren.
- Eintragen in `scripts/materialien.json`: `fuellen`, `linie`,
  `schwarz_ab_e`, `test`, `stand: "gemessen JJJJ-MM-TT: …"`, `notiz`.

## 6. Was passiert → was tun

| Was passiert | Ursache | Abhilfe |
|---|---|---|
| Senkrechte Kanten gezackt | Zeilenversatz bidirektional | `--zeilenversatz` messen (Abschnitt 1) oder `--einseitig` |
| Fahrt stockt, Gravur dauert viel länger als geschätzt | zu viele sehr kurze Befehle für Uno/WLAN | `--intervall` gröber, `--f` kleiner, `schwellwert` statt `dither` |
| Zu hell, fleckig | zu wenig Energie, Fokus daneben | Fokustest, dann S höher oder F kleiner (Materialtest) |
| Brandränder, Rauchfahnen | zu viel Energie | E senken; Lüftung/Air Assist |
| Bild gespiegelt oder auf dem Kopf | Ursprung falsch angenommen | `--ursprung` prüfen; Vorschau zeigt hinten oben |
| ALARM:2 mitten im Auftrag | Ziel hinter dem Softlimit | vorher `gcode_check.py --pi zustand.json`; Gravur verschieben |
| `error:15` beim Rahmen | Datei nicht auf den Nullpunkt bezogen oder G54 falsch | G54 an der Anschlagecke neu setzen |
| Rahmen fährt nach 0, 0 | 3D-Ansicht in CNCjs aus oder keine Datei geladen | Datei laden, 3D-Ansicht an |
| Laser brennt im Stillstand Punkte | M3 statt M4, oder `$32=0` | M4; `$32=1` |
| Erste Zeile/Ecke dunkler | M3 oder kein Overscan | M4, Overscan nicht auf 0 |
| Schrift fehlt ein Zeichen | Schrift hat das Zeichen nicht | andere Schrift (Arial hat Umlaute, ß, €) |
| SVG brennt alles schwarz | Farben in `<style>` mit Selektoren, die das Skript nicht kennt | im Editor Stil in Attribute umwandeln, oder `--art linie` |
