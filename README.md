# engraver

CNC-Engraver mit Diodenlaser — Konstruktionsskripte, Prüfwerkzeuge und Notizen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil quer (600 mm, 400 mm auseinander, das vordere 35 mm hinter dem Ende der 2040), darauf 2 × 2040 Aluprofil längs (600 mm), alle hochkant |
| Y-Achse | 2 Linearführungen MGN12H (Schienen 500 mm) oben auf den 2040ern; GT2-Riemen in den oberen Nuten der 2040, vorn je Seite ein NEMA 17 mit dem Ritzel direkt auf der Welle, mittig zur 2040 |
| Portal | Y-Schlitten auf den MGN12H-Wagen, dazwischen ein 2020-V-Slot-Profil (500 mm); Y-Schienen 514 mm Mitte zu Mitte |
| X-Achse | Linearführung MGN15H (Schiene 450 mm) am Portalprofil, GT2-Riemen: NEMA 17 links, Umlenkung mit Spanner rechts |
| Z-Achse | Toolhead am MGN15H-Wagen: eigene MGN9-Führung, NEMA 17 über Tr8×2-Spindel |
| Werkzeug | Diodenlaser am Z-Schlitten |
| Steuerung | Arduino Uno R3 + CNC Shield V3 + 4 × TMC2209 (vorhanden), GRBL 1.1, A-Achse klont Y |

## Inhalt

```
fusion/ToolheadZ/              Baugruppe: kompletter Toolhead mit Z-Achse  ← aktuell
fusion/Portal/                 Baugruppe: Y-Schlitten, Y-Klemmtürme, X-Antrieb, Y-Antrieb mit Y-Motorhalter, Endschalter X und Y
fusion/Elektronik/             Gehäuse für Uno + CNC Shield, Wandler, Wago; Deckel mit Lüfter  ← neu
fusion/NotAus/                 Gehäuse für den Not-Aus vorn am vorderen 2060  ← neu
fusion/ToolheadGrundplatte/    nur die Laserplatte (vom Toolhead überholt)
docs/toolhead-z.md             Maßkette, Antrieb, Montage, Druck, Prüfliste
docs/portal-y-schlitten.md     Y-Schlitten, Y- und X-Riemen, Klemmen, Montage, Druck
docs/portal-y-schlitten.svg    Draufsicht auf beide Portalenden, Schnitte durch Klemmen und Umlenkung
docs/toolhead-z-layout.svg     maßstäbliche Seiten- und Vorderansicht
docs/toolhead-z-antrieb.svg    Skizze des Z-Antriebs: Motor, Kupplung, Spindel, Garnitur
docs/toolhead-grundplatte.md   Doku der Einzelplatte
docs/elektronik.md             Platz, Gehäuse, Leistung, Endschalter, Kabel, Anschlussplan
docs/elektronik-platz.svg      Draufsicht und Seitenansicht: Elektronikfach, Ketten, Kabelwege
docs/elektronik-anschluss.svg  Anschlussplan mit Kabelnummern W1–W17 und Kabelliste
docs/verkabelung.md            Verkabelung: Kabelliste, Anschlussliste, Klemmen, Schritt für Schritt, Inbetriebnahme, GRBL
docs/elektronik-box.svg        Elektronik-Gehäuse von oben: Uno, Lüfter, Verteiler, Kabelwege
docs/endschalter.md            Endschalter X und Y: Halter, Fahnen, Montage, Einstellen, GRBL
docs/endschalter.svg           Endschalter: Y von hinten und von außen, X von vorn und von oben, Klammer X
docs/notaus.md                 Not-Aus: Taster, Lage, Gehäuse, Montage, Druck
docs/notaus.svg                Not-Aus-Gehäuse von vorn, im Schnitt und von oben
docs/hardware-notizen.md       Kaufteilmaße mit Verifizierungsstatus
docs/ausrichten.md             Gestell und Y-Achse mit einer Winkel-Messbox ausrichten
docs/y-motorhalter.md          Y-Antrieb: Riemen in der Nut, Aufbau, Spannen, Montage, Druck
docs/y-motorhalter.svg         Y-Motorhalter: Draufsicht, Seitenansicht, Schnitt, Riemen in der Nut
tools/bauraum.py               Bauräume als Quader — Quelle für Prüfung + Zeichnung
tools/toolhead_check.py        rechnerische Prüfung der Baugruppe (ohne Fusion)
tools/portal_check.py          Prüfung des Portals mit dem Toolhead über X- und Z-Weg
tools/layout_zeichnen.py       erzeugt die Layout-Zeichnung
tools/antrieb_zeichnen.py      erzeugt die Antriebsskizze
tools/portal_zeichnen.py       erzeugt die Portalzeichnung
tools/elektronik_check.py      Prüfung des Elektronikgehäuses (Fach, Freiraum, Montage, Druck, Leistung, Litzen) und der Verkabelung
tools/elektronik_zeichnen.py   erzeugt die Elektronik-Zeichnung und die Kabellängen
tools/anschluss_zeichnen.py    erzeugt den Anschlussplan
tools/verkabelung.py           Kabelliste — Quelle für Anleitung, Anschlussplan und Prüfung; schreibt die Tabellen in docs/verkabelung.md
tools/elektronik_box_zeichnen.py erzeugt die Draufsicht auf das Elektronik-Gehäuse
tools/endschalter_check.py     Prüfung der Endschalter: Schaltpunkte, Blatt im Spalt, Freiraum über den ganzen Weg
tools/endschalter_zeichnen.py  erzeugt die Zeichnung der Endschalter
tools/notaus_check.py          Prüfung des Not-Aus-Gehäuses: Lage, Freiraum, Schrauben, Taster, Druck
tools/notaus_zeichnen.py       erzeugt die Zeichnung des Not-Aus-Gehäuses
tools/geometrie_check.py       Prüfung der Einzelplatte
tools/y_motorhalter_check.py   rechnerische Prüfung des Y-Motorhalters
tools/y_motorhalter_zeichnen.py erzeugt die Zeichnung des Y-Motorhalters
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
einem 16 mm langen Umlenkritzel (GT2 20 Z mit Kugellagern, seit Rev. 17),
das ein Spannklotz nach außen zieht. Vorn an jedem 2040
sitzt der [Y-Motorhalter](#y-motorhalter-neu) mit dem Y-Motor, seit Rev. 16
ebenfalls aus `Portal.py`. Aluprofile, Linearführungen,
Riemen und Motoren stehen als Referenz mit im Modell (Komponente
`Referenz_nicht_drucken`, nur zur Ansicht).

X-Weg **391,2 mm** — die ganze Schiene minus Wagen. Der Toolhead fährt an
beiden Enden mit mindestens 3 mm an Motor, Umlenkung, Schlitten und Y-Riemen
vorbei, geprüft über den ganzen X- und Z-Weg. Details in
[docs/portal-y-schlitten.md](docs/portal-y-schlitten.md).

### Y-Motorhalter (neu)

Hält vorn an jeder 2040 einen NEMA 17, dasselbe Teil links und rechts. Der
Y-Riemen läuft in den oberen Nuten beider Seitenflächen und am Profilende um
das Ritzel, das direkt auf der Motorwelle sitzt. Der Motor hängt mittig zur
2040 unter einer Platte, Welle nach oben. Mit 20 Zähnen laufen beide Trume
mittig im Nutkanal. Der Halter ist ein U-Bügel: zwei Schenkel mit 4 × M5 in
den unteren Nuten, ein Joch liegt an der Stirnseite an. Gespannt wird über
Langlöcher, der Motor rückt ±4 mm vom Profil weg. Gedruckt wird kopfüber
ohne Stützen. Seit Portal Rev. 16 baut ihn `Portal.py` mit (vorher das
eigene Skript `YMotorhalter.py`); den alten Halter des Portals, Achse
15,55 mm neben der Profilmitte, gibt es nicht mehr. Details in
[docs/y-motorhalter.md](docs/y-motorhalter.md).

### Elektronikgehäuse (neu)

Gehäuse im Fach hinter dem hinteren 2060, unter den 2040 — dorthin fährt
weder Portal noch Toolhead. Links der **Arduino Uno mit CNC Shield V3** auf
Stehbolzen, USB nach hinten; rechts der **Abwärtswandler 24 → 12 V** für den
Laser (43 × 24 × 20 mm) und drei **Wago-Klemmen** (221-415 für +24 V,
2 × 221-420 für GND und +5 V); hinten **Einbaubuchse** (Hohlstecker
5,5 × 2,1) und **Schalter**. Der **Deckel** trägt den 24-V-Lüfter über den
Treibern. Eine Montageplatte hängt es mit 4 × M5 an die Rückseite des 2060,
dazwischen läuft ein Kabelkanal. Dazu Endschalter, Kabelwege, Energieketten,
Leistungsbilanz des 72-W-Netzteils und der Anschlussplan in
[docs/elektronik.md](docs/elektronik.md).

### Verkabelung (neu)

Alle 17 Leitungen vom Steckernetzteil bis zum Laser mit Nummer, Adern,
Farben, Querschnitt, Weg und Kauflänge; Belegung der Wago-Klemmen und des
Shields; Material, Reihenfolge beim Anschließen und eine Inbetriebnahme in
Stufen (24 V, Wandler, GRBL und Lichtschranken, Vref, Motoren,
Referenzfahrt, Laser, Not-Aus) mit den GRBL-Einstellungen. Neu gegenüber
dem alten Plan: Pull-down 10 kΩ auf der Laser-PWM, 24-V-Wächter an
Abort, Masse der Lichtschranken über die Wago. Details in
[docs/verkabelung.md](docs/verkabelung.md).

### Not-Aus (neu)

Pilztaster mit einem Wechsler (C, NO, NC): C und NC liegen in der
24-V-Leitung, NO bleibt frei. Er sitzt in einem gedruckten Gehäuse vorn am
vorderen 2060, rechts innen neben dem rechten 2040, mit 2 × M5 in der
mittleren Nut und längs verschiebbar. Das Gehäuse ist hinten offen,
45°-Rippen tragen die Laschen, und es druckt ohne Stützen. Dass die 24 V
fehlen, meldet ein Spannungsteiler an Abort, und GRBL bricht ab. Details
in [docs/notaus.md](docs/notaus.md).

### Endschalter X und Y (neu)

Zwei LM393-Gabellichtschranken wie an Z, beide schalten 3 mm vor dem
Schienenende. **Y** sitzt außen am rechten 2040, 35 mm hinter dem hinteren
2060, mit 2 × M5 in der unteren Nut; die obere trägt den Rücklauf des
Y-Riemens. Die Fahne ist eine Klammer an der rechten Schlittenplatte.
**X** sitzt auf einem Block vor dem linken Rohrende, der an das Ende der
X-Schiene stößt und zugleich Anschlag ist. Die Fahne sitzt auf einer
Klammer unten an der Trägerplatte und ist im Langloch ±2 mm verstellbar.
Fahnen und Klammern werden schwarz gedruckt. Details in
[docs/endschalter.md](docs/endschalter.md).

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
*Portal*, *Elektronik* oder *NotAus*). Jeder Lauf legt ein **neues
Dokument** an, das aktive bleibt unberührt. Am Ende erscheint
ein Validierungsbericht mit Maßkette, Verfahrweg, Schraubenliste und
Montagereihenfolge.

## Prüfen und zeichnen

```sh
python3 tools/toolhead_check.py     # Maßkette, Kollisionen, Schrauben, Druck
python3 tools/portal_check.py       # Portal + Toolhead über den ganzen Weg
python3 tools/elektronik_check.py   # Elektronikgehäuse gegen Portal, Toolhead, Rahmen; Verkabelung
python3 tools/layout_zeichnen.py    # docs/toolhead-z-layout.svg neu erzeugen
python3 tools/antrieb_zeichnen.py   # docs/toolhead-z-antrieb.svg neu erzeugen
python3 tools/portal_zeichnen.py    # docs/portal-y-schlitten.svg neu erzeugen
python3 tools/elektronik_zeichnen.py # docs/elektronik-platz.svg + Kabellängen
python3 tools/anschluss_zeichnen.py  # docs/elektronik-anschluss.svg
python3 tools/verkabelung.py         # Tabellen in docs/verkabelung.md
python3 tools/elektronik_box_zeichnen.py  # docs/elektronik-box.svg
python3 tools/geometrie_check.py    # nur die Einzelplatte
python3 tools/y_motorhalter_check.py  # Y-Motorhalter: Riemen in der Nut, Freigänge, Schrauben
python3 tools/y_motorhalter_zeichnen.py  # docs/y-motorhalter.svg neu erzeugen
python3 tools/endschalter_check.py  # Endschalter: Schaltpunkte, Freigänge, Schrauben, Druck
python3 tools/endschalter_zeichnen.py  # docs/endschalter.svg neu erzeugen
python3 tools/notaus_check.py       # Not-Aus-Gehäuse: Lage, Freiraum, Schrauben, Druck
python3 tools/notaus_zeichnen.py    # docs/notaus.svg neu erzeugen
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
und die Y-Motorhalter, den Y-Antrieb selbst mit dem Riemenweg über den
ganzen Y-Weg und das Elektronikfach hinter
dem hinteren 2060, in das weder Portal noch Toolhead hineinfahren.

**Stand:** alle Prüfungen bestanden (ToolheadZ Rev. 34, Portal Rev. 17 mit
dem Y-Motorhalter, `y_motorhalter_check.py`). Portal Rev. 17 baut den
Umlenkhalter für das 16 mm lange Umlenkritzel um (ToolheadZ Rev. 34 ändert
dazu nur einen Kommentar). Portal Rev. 14 legt das
hintere 2060 nach der Messung 435 mm hinter das vordere (die 2040 stehen
hinten 110 mm über); nach hinten begrenzt jetzt das Schienenende den Y-Weg.
Elektronikgehäuse Rev. 2 mit den am Aufbau gemessenen Werten (Stapelhöhe,
Wandler, Wago) gezeichnet und geprüft
([elektronik.md](docs/elektronik.md)). Die Endschalter X und Y baut seit
Rev. 15 `Portal.py` mit, geprüft mit `endschalter_check.py`
([endschalter.md](docs/endschalter.md)),
Not-Aus-Gehäuse Rev. 5 mit `notaus_check.py` ([notaus.md](docs/notaus.md)). Die
Verkabelung steht als Kabelliste in `tools/verkabelung.py`,
`elektronik_check.py` prüft sie (Netze, Not-Aus, Kontakte, Klemmen, Längen,
Tabellen in [verkabelung.md](docs/verkabelung.md)); die Halter der
Energieketten folgen. Der
Zugangskonflikt zwischen Laser und Z-Wagen ist gelöst, indem der Laser
30,75 mm tiefer hängt und über senkrechte Langlöcher eingestellt wird —
[Laserhöhe](docs/toolhead-z.md#laserhöhe-langloch-statt-rechnen).
