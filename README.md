# engraver

CNC-Engraver mit Diodenlaser — Konstruktionsskripte, Prüfwerkzeuge und Notizen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil quer (600 mm, 400 mm auseinander, das vordere 35 mm hinter dem Ende der 2040), darauf 2 × 2040 Aluprofil längs (600 mm), alle hochkant |
| Y-Achse | 2 Linearführungen MGN12H (Schienen 500 mm) oben auf den 2040ern, GT2-Riemen, vorn je Seite ein NEMA 17 mit dem Ritzel direkt auf der Welle |
| Portal | Y-Schlitten auf den MGN12H-Wagen, dazwischen ein 2020-V-Slot-Profil (500 mm); Y-Schienen 514 mm Mitte zu Mitte |
| X-Achse | Linearführung MGN15H (Schiene 450 mm) am Portalprofil, GT2-Riemen: NEMA 17 links, Umlenkung mit Spanner rechts |
| Z-Achse | Toolhead am MGN15H-Wagen: eigene MGN9-Führung, NEMA 17 über Tr8×2-Spindel |
| Werkzeug | Diodenlaser am Z-Schlitten |
| Steuerung | Arduino Uno R3 + CNC Shield V3 + 4 × TMC2209, GRBL 1.1 (geplant), A-Achse klont Y |

## Inhalt

```
fusion/ToolheadZ/              Baugruppe: kompletter Toolhead mit Z-Achse  ← aktuell
fusion/Portal/                 Baugruppe: Y-Schlitten, Y-Klemmtürme, X- und Y-Antrieb  ← neu
fusion/ToolheadGrundplatte/    nur die Laserplatte (vom Toolhead überholt)
docs/toolhead-z.md             Maßkette, Antrieb, Montage, Druck, Prüfliste
docs/portal-y-schlitten.md     Y-Schlitten, Y- und X-Riemen, Klemmen, Montage, Druck
docs/portal-y-schlitten.svg    Draufsicht auf beide Portalenden, Schnitte durch Klemmen und Umlenkung
docs/portal-y-antrieb.svg      Y-Motorhalter vorn: Draufsicht auf die Ecke, Schnitt durch die Motorachse
docs/toolhead-z-layout.svg     maßstäbliche Seiten- und Vorderansicht
docs/toolhead-z-antrieb.svg    Skizze des Z-Antriebs: Motor, Kupplung, Spindel, Garnitur
docs/toolhead-grundplatte.md   Doku der Einzelplatte
docs/elektronik.md             Platz für Steuerung und Netzteil, Endschalter, Kabel (Vorschlag)
docs/elektronik-platz.svg      Draufsicht und Seitenansicht: Elektronikfach, Ketten, Kabelwege
docs/hardware-notizen.md       Kaufteilmaße mit Verifizierungsstatus
docs/ausrichten.md             Gestell und Y-Achse mit einer Winkel-Messbox ausrichten
tools/bauraum.py               Bauräume als Quader — Quelle für Prüfung + Zeichnung
tools/toolhead_check.py        rechnerische Prüfung der Baugruppe (ohne Fusion)
tools/portal_check.py          Prüfung des Portals mit dem Toolhead über X- und Z-Weg
tools/layout_zeichnen.py       erzeugt die Layout-Zeichnung
tools/antrieb_zeichnen.py      erzeugt die Antriebsskizze
tools/portal_zeichnen.py       erzeugt die Portalzeichnung
tools/y_antrieb_zeichnen.py    erzeugt die Zeichnung des Y-Antriebs
tools/elektronik_zeichnen.py   erzeugt die Elektronik-Zeichnung und die Kabellängen
tools/geometrie_check.py       Prüfung der Einzelplatte
```

## Teile

### Toolhead Z-Achse (aktuell)

Kompletter Toolhead als Baugruppe aus sieben gedruckten Teilen: **Trägerplatte**
am MGN15H-Wagen des Portals — mit angeformter Motorkonsole für den NEMA 17 —,
ein **Motoradapter**, der den Motor 10 mm über die Konsole hebt,
**Schlittenplatte** auf dem MGN9H-Z-Wagen mit dem Laser, ein **Mutternwinkel**
als Flanschsitz für die Tr8×2-Anti-Backlash-Garnitur, schwimmend verschraubt,
eine schwarze **Schaltfahne** und ein **Endschalterhalter** für die
Gabellichtschranke, dazu der **Riemenhalter** hinten an der Trägerplatte, der
beide Enden des X-Riemens klemmt (Rev. 33).

Nutzbarer Z-Verfahrweg **93,6 mm** (MGN9-Schiene 200 mm), Strahlachse 58,5 mm
vor der X-Wagen-Stirnfläche, NEMA 17 mit allen vier Schrauben zugänglich. Die
Laserhöhe ist über senkrechte Langlöcher ±8 mm verstellbar, damit der
Fokusabstand des Moduls nicht in der Geometrie steckt. Werkstückhöhe bis 59 mm
— begrenzt nicht vom Verfahrweg, sondern von der Plattenunterkante, die in X
mitfährt — die 200-mm-Spindel wird dafür auf 160 mm gekürzt. Details in
[docs/toolhead-z.md](docs/toolhead-z.md).

### Portal: Y-Schlitten, X- und Y-Antrieb (neu)

Riemenklemmenschlitten für die **MGN12H-Wagen (20 × 20)**, links und rechts
gespiegelt. Sie tragen das Portalrohr von unten und verschrauben es hinten
(Rückwand, 2 × M5 in Hammermuttern) und an der Stirn (M5 in die
Kernbohrung) — die Vorderseite bleibt frei für die X-Schiene. Unter jeder
Platte hängen **zwei gleiche Klemmtürme wie bei v8** mit Rippen und
Querstift, einer je Riemenende.
Links steht der **X-Motor** über dem Rohrende — so tief, dass seine
20-mm-Welle das ganze Ritzel trägt —, rechts die **Umlenkung** mit
einer 20-Z-Rolle, die ein Spannklotz nach außen zieht. Vorn an jedem 2040
sitzt ein **Y-Motorhalter**: NEMA 17 hängend, das Ritzel des Y-Riemens direkt
auf der Welle, gespannt über Langlöcher — Eckwelle und unteres Ritzel
entfallen. Aluprofile, Linearführungen, Riemen und Motoren stehen als Referenz
mit im Modell (Komponente `Referenz_nicht_drucken`, nur zur Ansicht).

X-Weg **391,2 mm** — die ganze Schiene minus Wagen. Der Toolhead fährt an
beiden Enden mit mindestens 3 mm an Motor, Umlenkung, Schlitten und Y-Riemen
vorbei, geprüft über den ganzen X- und Z-Weg. Details in
[docs/portal-y-schlitten.md](docs/portal-y-schlitten.md).

### Toolhead-Grundplatte (überholt)

Die erste Ausführung: nur die Platte, die den Laser am MGN9-Z-Wagen hält, ohne
Z-Antrieb. Das Konzept — Auflagepad, das die Montagehöhe des Wagens aufnimmt —
steckt unverändert in der Schlittenplatte des Toolheads.
Siehe [docs/toolhead-grundplatte.md](docs/toolhead-grundplatte.md).

## Skript in Fusion ausführen

Den Ordner unter `fusion/` (`.py` **und** `.manifest`) hierhin kopieren:

* macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`
* Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`

Dann in Fusion *Utilities → Scripts and Add-Ins → ToolheadZ → Run* (bzw.
*Portal*). Jeder Lauf legt ein **neues Dokument** an, das aktive bleibt
unberührt. Am Ende erscheint
ein Validierungsbericht mit Maßkette, Verfahrweg, Schraubenliste und
Montagereihenfolge.

## Prüfen und zeichnen

```sh
python3 tools/toolhead_check.py     # Maßkette, Kollisionen, Schrauben, Druck
python3 tools/portal_check.py       # Portal + Toolhead über den ganzen Weg
python3 tools/layout_zeichnen.py    # docs/toolhead-z-layout.svg neu erzeugen
python3 tools/antrieb_zeichnen.py   # docs/toolhead-z-antrieb.svg neu erzeugen
python3 tools/portal_zeichnen.py    # docs/portal-y-schlitten.svg neu erzeugen
python3 tools/y_antrieb_zeichnen.py # docs/portal-y-antrieb.svg neu erzeugen
python3 tools/elektronik_zeichnen.py # docs/elektronik-platz.svg + Kabellängen
python3 tools/geometrie_check.py    # nur die Einzelplatte
```

`toolhead_check.py` importiert das Fusion-Skript mit gestubbtem `adsk`-Modul und
prüft dieselbe Maßkette, die das Skript zum Bauen verwendet: Y-Kette,
Verfahrweg mit allen vier Begrenzungen, Kollisionen über 21 Stellungen des
Verfahrwegs, Materialstege, Schraubenlängen und -eingriffstiefen,
**Werkzeugzugang für jede Schraube** (freie Inbus-Länge im Zustand, in dem sie
verschraubt wird), Lochbildtoleranzen, Druckbarkeit — und statisch, dass jeder
im Skript benutzte Maß- und Lageschlüssel existiert. Exit-Code 0 = alles
bestanden.

`portal_check.py` importiert beide Skripte und fährt den Toolhead über
81 X- × 11 Z-Stellungen gegen Schlitten, Motor, Umlenkung, beide Riemen und
den Rahmen; dazu Riemenlage, Klemmung, Spannwege, Wände, Schraubenlängen,
Werkzeugzugang und Druckbarkeit der Portalteile, den Y-Weg gegen die 2060
und die Y-Motorhalter, den Y-Antrieb selbst und das Elektronikfach hinter
dem hinteren 2060, in das weder Portal noch Toolhead hineinfahren.

**Stand:** alle Prüfungen bestanden (ToolheadZ Rev. 33, Portal Rev. 13).
Für die Elektronik gibt es einen Platz und die Kabelwege als Vorschlag
([elektronik.md](docs/elektronik.md)); die Halter folgen. Der
Zugangskonflikt zwischen Laser und Z-Wagen ist gelöst, indem der Laser
30,75 mm tiefer hängt und über senkrechte Langlöcher eingestellt wird —
[Laserhöhe](docs/toolhead-z.md#laserhöhe-langloch-statt-rechnen).
