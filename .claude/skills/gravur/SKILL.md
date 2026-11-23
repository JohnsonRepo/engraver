---
name: gravur
description: Erzeugt Lasergravuren als geprüften G-Code für den eigenen CNC-Diodenlaser dieses Repos (GRBL 1.1h am Uno, CNCjs auf dem Pi laser.local, Nullpunkt G54 an der Anschlagecke vorn rechts) – Schriftzüge und Namensschilder, Logos und Zeichnungen aus SVG, Fotos und Bilder (PNG/JPG) als Dither, Graustufen, Schwellwert oder Linienbild, Materialtests Leistung × Vorschub; mit Vorschau-PNG, Laufzeit, Prüfung gegen Werkstück und Arbeitsfeld und auf Wunsch Upload in den Ordner ~/gcode auf dem Pi. Immer nutzen, wenn der Nutzer etwas gravieren, lasern, brennen oder einbrennen will (Holz, Spanplatte, Sperrholz, MDF, Leder, Schiefer, Acryl …), wissen will, mit welcher Leistung oder Geschwindigkeit ein Material graviert wird, einen Materialtest braucht oder eine G-Code- oder LightBurn-Datei (.gc, .nc, .gcode) für den Laser prüfen will – auch wenn er nicht „G-Code“ oder „Skill“ sagt. Nicht für die Konstruktion der Maschine (Fusion-Skripte) und nicht für die Fokustest-Makros (tools/fokustest.py).
---

# Gravuren für den Engraver

Dieser Skill macht aus Text, SVG oder Bild eine `.gc`-Datei, die auf genau
dieser Maschine läuft, prüft sie wie GRBL und zeigt eine Vorschau. Gestartet
wird der Auftrag immer vom Nutzer an der Maschine – nie von dir. Ein Laser
brennt, und der Stopp-Knopf im Browser hängt am WLAN; nur wer danebensteht,
erreicht den Not-Aus.

Skripte (Python 3 mit numpy, Pillow, scipy, fontTools) liegen in `scripts/`
neben dieser Datei. Die Befehle unten nehmen an:

```sh
S=.claude/skills/gravur/scripts     # vom Repo-Ordner aus, sonst <Skill-Ordner>/scripts
```

| Skript | wofür |
|---|---|
| `gravur.py` | erzeugen: `text`, `svg`, `bild`, `materialtest`, `materialien` |
| `gcode_check.py` | jede `.gc` prüfen, auch aus LightBurn, mit `--vorschau` |
| `grbl_lesen.js` | Einstellungen und Nullpunkt vom Pi lesen (nur lesend) |
| `materialien.json` | Leistung/Vorschub je Material, gemessen oder Startwert |
| `selbsttest.py` | nach Änderungen an den Skripten: alles ohne Maschine prüfen |

`python3 $S/gravur.py <befehl> --help` zeigt alle Optionen.

## Die Maschine in Kürze

```
                hinten (Y+)
     ┌─────────────────────────┐▐
     │                         │▐  Anschlagwinkel (3 mm hoch)
     │        Werkstück        │▐
     │     X ≤ 0 und Y ≥ 0     │▐   X+ nach rechts, Y+ nach hinten
     └─────────────────────────●▐
      ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀   ● = G54 X0 Y0, Innenecke vorn rechts
                  vorn
```

- **Nullpunkt:** Das Werkstück liegt in der Anschlagecke vorn rechts, von
  Exzentern hineingeschoben. Oben im Bild = hinten an der Maschine, so liest
  sich die Gravur von vorn. `--werkstueck BxT` heißt Breite in X × Tiefe in Y.
- **Laser:** LASER TREE 4 W, 450 nm. `$30=1000` (S0…S1000), `$32=1`
  (Lasermodus). Gebrannt wird mit **M4**: Die Leistung folgt der
  Geschwindigkeit, Ecken und Zeilenenden brennen nicht nach.
- **Fahren:** höchstens 3000 mm/min, 500 mm/s² (seit 2026-11-18).
- **Platz:** Arbeitsfeld etwa 391 × 285 mm, Werkstück höchstens 32 mm dick.
  Wo ein Niederhalter sitzt, 6 mm Rand zur Gravur lassen.
- **Z und Fokus:** Die Dateien fahren nie Z. Fokussiert wird vorher mit
  dem Autofokus-Widget oder den Fokustest-Makros (`docs/fokustest.md`).
  Der Messpunkt des Autofokus liegt bei G54 X−30 Y58, das Werkstück muss
  ihn bedecken.
- **Pi:** CNCjs unter `http://laser.local:8000`, Dateien in `~/gcode`
  erscheinen dort unter „Watch Directory“.

Mehr dazu, mit Quellen und offenen Punkten: `references/maschine.md`.

## Ablauf

### 1. Klären, was fehlt

Frag nur nach dem, was du nicht erschließen kannst, am besten in einer
Nachricht:

- **Motiv:** Text (welche Schrift?), SVG, Bild/Foto, oder ein Materialtest.
- **Material** und ob es roh oder beschichtet ist. Melamin-beschichtete
  Spanplatte ist nicht „spanplatte“.
- **Werkstück:** Breite (links–rechts) × Tiefe (vorn–hinten) in mm, Dicke.
- **Größe und Lage** der Gravur. Ohne Angabe: mittig, sinnvolle Größe
  vorschlagen.

Liegt der Nullpunkt ausnahmsweise nicht an der Anschlagecke (der Nutzer
hat ihn mit dem Laserpunkt an eine andere Werkstückecke gesetzt), gib
`--ursprung` an: `hinten-links`, `vorn-links`, `hinten-rechts`, `mitte`.

### 2. Leistung wählen

```sh
python3 $S/gravur.py materialien
```

- Steht beim Material **„gemessen“**, nimm `--material NAME`.
- Steht dort **„Startwert“**, ist es eine Annahme. Biete zuerst einen
  Materialtest auf einem Reststück an (Schritt 3, `materialtest`). Will der
  Nutzer direkt los, nimm die Startwerte und sag, dass sie ungetestet sind.
- Unbekanntes Material: erst prüfen, ob es überhaupt gelasert werden darf
  (Abschnitt Sicherheit), dann Materialtest mit `--leistung`/`--vorschub`.

Energie je Millimeter ist `E = S/F`. Auf roher Spanplatte brennt ab
E 0,2 alles schwarz (S400 F2000). Mehr Energie macht nicht schwärzer,
nur breiter und brandiger.

### 3. Erzeugen

Immer mit `--werkstueck` (sonst prüft niemand, ob die Gravur draufpasst)
und, wenn bekannt, `--dicke`:

```sh
python3 $S/gravur.py text "Werkstatt" --hoehe 12 --werkstueck 150x60 --dicke 25 --material spanplatte
python3 $S/gravur.py svg logo.svg --breite 60 --werkstueck 80x80 --material spanplatte
python3 $S/gravur.py bild foto.jpg --art dither --breite 80 --werkstueck 100x70 --material mdf
python3 $S/gravur.py materialtest --material sperrholz_birke --werkstueck 70x70
```

Welche Art für welches Motiv:

| Motiv | Befehl | Hinweis |
|---|---|---|
| Schrift, Schild | `text`, `--art fuellen` | `--hoehe` = Versalhöhe (H). Unter 2 mm wird Füllen unleserlich |
| große Schrift, schnell | `text --art kontur` | nur die Umrisse, eine Linie |
| Logo, Piktogramm als SVG | `svg --art fuellen` | weiße Flächen radieren, Text vorher in Pfade |
| Strichzeichnung, Plan | `svg --art linie` | nur Linien mit Strich, sonst alle Umrisse |
| Logo nur als PNG/JPG | `bild --art schwellwert` | `--schwelle` 0…1 |
| Foto | `bild --art dither` | Standard 0,15 mm Pixel; meist besser als Graustufen |
| Foto, weiche Verläufe | `bild --art graustufen` | braucht einen Graustufentest auf dem Material |
| Foto als Zeichnung | `bild --art linien` | `--detail`, `--staerke`, `--dunkel` |
| neues Material | `materialtest` | Kreuz am Anfang und Ende zeigt Schrittverluste |

Lage: `--lage mitte` (Standard) oder eine Ecke mit `--abstand`; genau mit
`--links/--rechts/--vorn/--hinten` (Abstand zur jeweiligen Kante).
Drehen mit `--drehen 90|180|270` (gegen den Uhrzeiger, Größe gilt vor dem
Drehen), Spiegeln mit `--spiegeln`. Tiefer brennen: `--durchgaenge 2`.

Mehrere Motive auf einem Werkstück (Schrift und Logo): je Motiv eine Datei
mit demselben `--werkstueck` und eigener Lage (`--vorn`, `--hinten` …),
nacheinander laufen lassen. Oder beides vorher in ein SVG legen.

Ausgabe: `~/Documents/Gravuren/<Datum>_<name>/<name>.gc` und
`<name>_vorschau.png` daneben (`-o` für einen anderen Ort). Der Kopf der
Datei hält Befehl, Material, Lage und Dauer fest, damit sie sich später
nachvollziehen lässt. Arbeitsdateien gehören nicht ins Scratchpad: Das
wird gelöscht, und der Nutzer findet sie dort nicht.

### 4. Prüfen und zeigen

`gravur.py` prüft selbst und endet mit `Keine Fehler.` oder einer Liste:

- **FEHL** muss weg, bevor die Datei zur Maschine geht: Gravur über dem
  Werkstückrand, Ziel außerhalb des Arbeitsfelds (GRBL bricht sonst mitten
  im Auftrag mit ALARM:2 ab), Z-Fahrt, S über 1000, Werkstück zu dick.
- **WARN** dem Nutzer nennen und begründet entscheiden, z. B. „der Uno
  kommt nicht nach“ → gröberes `--intervall` oder kleineres `--f`.

Sieh dir die Vorschau selbst an (Read auf das PNG), bevor du sie zeigst:
Steht die Schrift richtig herum, liegt alles auf dem Holz, ist das Foto
erkennbar? Dann zeig sie dem Nutzer (SendUserFile, wo es das gibt, sonst
den Pfad nennen), mit Größe, Lage, Leistung und Dauer in einem Satz.

LightBurn-Dateien oder fremden G-Code prüfst du genauso:

```sh
python3 $S/gcode_check.py auftrag.gc --werkstueck 140x100 --material spanplatte --vorschau auftrag.png
```

### 5. Genauer: Zustand vom Pi (wenn er läuft)

Das Feld aus der Doku stimmt nur ungefähr (`$130` stand an der Maschine
zuletzt auf 367 statt 385). Ist der Pi an und CNCjs mit dem Uno verbunden,
lies die echten Grenzen und den Nullpunkt, nur lesend:

```sh
ssh -i ~/.ssh/id_ed25519_claude -o IdentitiesOnly=yes -o ConnectTimeout=5 \
    laser@laser.local 'node -' < $S/grbl_lesen.js > zustand.json
python3 $S/gravur.py … --pi zustand.json      # oder gcode_check.py … --pi zustand.json
```

Antwortet `laser.local` nicht: Maschine aus, oder der Pi heißt nach einem
Namenskonflikt `laser-2.local`, im Hotspot `10.42.0.1`. Dann ohne Pi
weiter und das im Ergebnis sagen.

### 6. Hochladen – nur wenn der Nutzer es will

```sh
scp -i ~/.ssh/id_ed25519_claude -o IdentitiesOnly=yes datei.gc laser@laser.local:gcode/
ssh -i ~/.ssh/id_ed25519_claude -o IdentitiesOnly=yes laser@laser.local sha256sum gcode/datei.gc
shasum -a 256 datei.gc        # beide gleich?
```

Damit liegt die Datei in CNCjs unter „Watch Directory“. Starten, Fokus
setzen oder GRBL-Einstellungen ändern tust du nicht; das macht der Nutzer.

### 7. Übergabe an der Maschine

Gib dem Nutzer diese Schritte mit (kurz, an seinen Auftrag angepasst):

1. Schutzbrille, Lüftung an. Schalter an, eine Minute warten.
2. CNCjs öffnen, verbinden, **Homing** (`$H`).
3. Werkstück in die Anschlagecke, Exzenter zu, dünne Platten mit
   Niederhaltern.
4. Fokus: Autofokus-Widget oder Fokustest; Z bleibt dann stehen, die
   Datei fährt es nicht.
5. Datei laden, Makro **Rahmen** fahren, Hand am Not-Aus.
6. **Start** – und dabei bleiben, bis er fertig ist.

### 8. Ergebnis festhalten

Meldet der Nutzer, wie es geworden ist (Foto vom Materialtest, „zu hell“,
„Brandränder“), trag das Gelernte in `$S/materialien.json` ein: Werte,
`schwarz_ab_e`, `stand: "gemessen JJJJ-MM-TT: …"`, kurze Notiz. So wird
aus einem Startwert ein gemessener Wert, und die nächste Gravur passt
sofort. Die Datei liegt im Repo; frag, ob du committen sollst.

## Sicherheit

- **Nie lasern:** PVC, Vinyl, Kunstleder (Chlorgas, Salzsäure, rostet die
  Maschine), Polycarbonat, ABS, glasfaser- oder kohlefaserverstärkte
  Kunststoffe, PTFE. Bei unbekanntem Kunststoff: nicht lasern.
- **Geht nicht mit 450 nm:** klares, blaues oder durchsichtiges Acryl, Glas
  und blankes Metall (nur eloxiert oder beschichtet).
- **Langsam und stark** (F unter 300 oder E weit über dem Schwarzwert) kann
  Flammen schlagen, vor allem Karton, Kork, Papier.
- Werkstück höchstens 32 mm dick; darüber stößt der Toolhead an.

## Wenn etwas nicht passt

`references/techniken.md` erklärt Intervall, Overscan, Zeilenversatz,
Fotos, SVG-Eigenheiten und hat eine Tabelle „was passiert → was tun“
(versetzte Zeilen, stockende Fahrt, zu hell/zu dunkel, ALARM:2, Rahmen
fährt nach 0,0).
