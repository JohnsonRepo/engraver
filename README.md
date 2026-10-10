# engraver

CNC-Engraver mit Diodenlaser — Konstruktionsskripte, Prüfwerkzeuge und Notizen.

## Aufbau der Maschine

| Ebene | Aufbau |
|---|---|
| Gestell | 2 × 2060 Aluprofil quer (600 mm, 435 mm Mitte zu Mitte, das vordere 35 mm hinter dem Ende der 2040), darauf 2 × 2040 Aluprofil längs (600 mm), alle hochkant; steht auf 4 gedruckten Führungsfüßen 25,3 mm über dem Tisch, dazwischen die Opferplatte |
| Y-Achse | 2 Linearführungen MGN12H (Schienen 500 mm) oben auf den 2040ern; GT2-Riemen in den oberen Nuten der 2040, vorn je Seite ein NEMA 17 mit dem Ritzel direkt auf der Welle, mittig zur 2040 |
| Portal | Y-Schlitten auf den MGN12H-Wagen, dazwischen ein 2020-V-Slot-Profil (500 mm); Y-Schienen 514 mm Mitte zu Mitte |
| X-Achse | Linearführung MGN15H (Schiene 450 mm) am Portalprofil, GT2-Riemen: NEMA 17 links, Umlenkung mit Spanner rechts |
| Z-Achse | Toolhead am MGN15H-Wagen: eigene MGN9-Führung, NEMA 17 über Tr8×2-Spindel |
| Werkzeug | Diodenlaser am Z-Schlitten |
| Steuerung | Arduino Uno R3 + CNC Shield V3 + 4 × TMC2209 (vorhanden), GRBL 1.1, A-Achse klont Y; ohne PC über einen Raspberry Pi Zero 2 W mit CNCjs |

## Inhalt

```
fusion/ToolheadZ/              Baugruppe: kompletter Toolhead mit Z-Achse  ← aktuell
fusion/Portal/                 Baugruppe: Y-Schlitten, Y-Klemmtürme, X-Antrieb, Y-Antrieb mit Y-Motorhalter, Endschalter X und Y, Wanne der X-Energiekette
fusion/Elektronik/             Gehäuse für Uno + CNC Shield, Wandler, Wago; Deckel als Haube mit Lüfter (Rev. 3)  ← neu
fusion/NotAus/                 Gehäuse für den Not-Aus vorn am vorderen 2060  ← neu
fusion/Kabelhalter/            Kabelhalter für die untere Seitennut außen an den 2040  ← neu
fusion/PiHalter/               Halter für Pi Zero 2 W und 5-V-Wandler an der Rückseite des hinteren 2060  ← neu
fusion/Opferplatte/            Führungsfüße unter den 2060 und Riegel für die Opferplatte (Spanplatte)  ← neu
fusion/Spannmittel/           Anschlagwinkel, Exzenter und Niederhalter für das Werkstück auf der Opferplatte  ← neu
fusion/ToolheadGrundplatte/    nur die Laserplatte (vom Toolhead überholt)
stl/                           druckfertige STL ohne Fusion: Kasten und Haube des Elektronik-Gehäuses, Kabelhalter, Pi-Halter
pi/                            Pi: Einrichtungsskript, CNCjs-Konfiguration mit Makros, Dienst, sudoers, WLAN-Energiesparen aus
docs/toolhead-z.md             Maßkette, Antrieb, Montage, Druck, Prüfliste
docs/portal-y-schlitten.md     Y-Schlitten, Y- und X-Riemen, Klemmen, Montage, Druck
docs/portal-y-schlitten.svg    Draufsicht auf beide Portalenden, Schnitte durch Klemmen und Umlenkung
docs/toolhead-z-layout.svg     maßstäbliche Seiten- und Vorderansicht
docs/toolhead-z-antrieb.svg    Skizze des Z-Antriebs: Motor, Kupplung, Spindel, Garnitur
docs/toolhead-grundplatte.md   Doku der Einzelplatte
docs/elektronik.md             Platz, Gehäuse, Leistung, Endschalter, Kabel, Anschlussplan
docs/elektronik-platz.svg      Draufsicht und Seitenansicht: Elektronikfach, Ketten, Kabelwege
docs/elektronik-anschluss.svg  Anschlussplan mit Kabelnummern W1–W19 und Kabelliste
docs/elektronik-verkabelung.svg  Verkabelung Schritt für Schritt: jede Ader von Klemme zu Klemme
docs/motoren-anschluss.svg     Motoren anschließen: Steckplätze am Shield, Adern je Achse
docs/verkabelung.md            Verkabelung: Kabelliste, Anschlussliste, Klemmen, Schritt für Schritt, Inbetriebnahme, GRBL
docs/elektronik-box.svg        Elektronik-Gehäuse von oben: Uno, Lüfter, Verteiler, Kabelwege
docs/endschalter.md            Endschalter X und Y: Halter, Fahnen, Montage, Einstellen, GRBL
docs/endschalter.svg           Endschalter: Y von hinten und von außen, X von vorn und von oben, Klammer X
docs/notaus.md                 Not-Aus: Taster, Lage, Gehäuse, Montage, Druck
docs/notaus.svg                Not-Aus-Gehäuse von vorn, im Schnitt und von oben
docs/kabelhalter.md            Kabelhalter: Rinne, Kabel, Plätze links und rechts, Montage, Druck
docs/kabelhalter.svg           Kabelhalter im Schnitt am 2040 und seine Plätze
docs/pi.md                     Pi: Maschine ohne PC über CNCjs — Teile, Halter, Strom, Einrichten, LightBurn, Ablauf, Fehlersuche
docs/pihalter.svg              Pi-Halter von hinten und im Schnitt am 2060
docs/opferplatte.md            Opferplatte, Führungsfüße und Riegel: Lage, Höhen, Montage, Druck
docs/opferplatte.svg           Gestell von oben mit Platte, Füßen und Riegel, Schnitte durch Füße, Riegel und Anschlag
docs/spannmittel.md            Werkstück spannen: Anschlag als Nullpunkt, Exzenter, Niederhalter, Höhe unter dem Toolhead
docs/spannmittel.svg           Ecke der Opferplatte mit Spannmitteln von oben, Schnitte durch Niederhalter und Anschlag, Exzenter
docs/hardware-notizen.md       Kaufteilmaße mit Verifizierungsstatus
docs/ausrichten.md             Gestell und Y-Achse mit einer Winkel-Messbox ausrichten
docs/y-motorhalter.md          Y-Antrieb: Riemen in der Nut, Aufbau, Spannen, Montage, Druck
docs/y-motorhalter.svg         Y-Motorhalter: Draufsicht, Seitenansicht, Schnitt, Riemen in der Nut
docs/energiekette.md           Energieketten X und Y (gedruckt): Kette, Lage, Halter, Wannen, Stützen, Träger, Kabelweg, Montage, Druck
docs/energiekette.svg          X-Energiekette von vorn, im Schnitt durch eine Wannenstütze und durch den Kabelflügel
docs/energiekette-y.svg        Y-Energiekette von links und im Schnitt durch einen Träger
tools/bauraum.py               Bauräume als Quader — Quelle für Prüfung + Zeichnung
tools/toolhead_check.py        rechnerische Prüfung der Baugruppe (ohne Fusion)
tools/portal_check.py          Prüfung des Portals mit dem Toolhead über X- und Z-Weg
tools/layout_zeichnen.py       erzeugt die Layout-Zeichnung
tools/antrieb_zeichnen.py      erzeugt die Antriebsskizze
tools/portal_zeichnen.py       erzeugt die Portalzeichnung
tools/elektronik_check.py      Prüfung des Elektronikgehäuses (Fach, Freiraum, Montage, Druck, Leistung, Litzen) und der Verkabelung
tools/elektronik_zeichnen.py   erzeugt die Elektronik-Zeichnung und die Kabellängen
tools/anschluss_zeichnen.py    erzeugt den Anschlussplan
tools/verkabelung_zeichnen.py  erzeugt das Bild „Verkabelung Schritt für Schritt“
tools/motoren_zeichnen.py      erzeugt das Bild „Motoren anschließen“
tools/verkabelung.py           Kabelliste — Quelle für Anleitung, Anschlussplan und Prüfung; schreibt die Tabellen in docs/verkabelung.md
tools/elektronik_box_zeichnen.py erzeugt die Draufsicht auf das Elektronik-Gehäuse
tools/endschalter_check.py     Prüfung der Endschalter: Schaltpunkte, Blatt im Spalt, Freiraum über den ganzen Weg
tools/endschalter_zeichnen.py  erzeugt die Zeichnung der Endschalter
tools/notaus_check.py          Prüfung des Not-Aus-Gehäuses: Lage, Freiraum, Schrauben, Taster, Druck
tools/notaus_zeichnen.py       erzeugt die Zeichnung des Not-Aus-Gehäuses
tools/kabelhalter_check.py     Prüfung der Kabelhalter: Schraube, Rinne und Kabel, Plätze, Freiraum, Druck; schreibt die Plätze in docs/kabelhalter.md
tools/kabelhalter_zeichnen.py  erzeugt die Zeichnung der Kabelhalter
tools/pihalter_check.py        Prüfung des Pi-Halters: Lage, Freiraum zu Portal, Kasten und Kabeln, Schrauben, Pi, Wandler, Druck
tools/pihalter_zeichnen.py     erzeugt die Zeichnung des Pi-Halters
tools/stl_export.py            schreibt stl/ aus denselben Maßen wie die Fusion-Skripte (braucht manifold3d)
tools/opferplatte_check.py     Prüfung von Opferplatte, Füßen und Riegel: Arbeitsfeld, Höhen, Freiraum, Riegel, Schrauben, Druck
tools/opferplatte_zeichnen.py  erzeugt die Zeichnung von Opferplatte, Füßen und Riegel
tools/spannmittel_check.py     Prüfung der Spannmittel: Höhe unter dem Toolhead, Lage, Selbsthemmung, Schrauben, Druck
tools/spannmittel_zeichnen.py  erzeugt die Zeichnung der Spannmittel
tools/kette_zeichnen.py        erzeugt die Zeichnung der X-Energiekette
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
Querstift, einer je Riemenende — seit Rev. 25 dicht an der 2040, damit
der Y-Riemen in die Nut läuft, seit Rev. 27 unter den Gewindeeinsätzen
schmal, seit Rev. 28 an der engsten Stelle 1 mm neben der 2040.
Links steht der **X-Motor** über dem Rohrende — so tief, dass seine
20-mm-Welle das ganze Ritzel trägt —, rechts die **Umlenkung**: ein Ritzel
wie am Motor auf einer Welle in Kugel- und Gleitlager, beide in einem
Lagerschlitten, den eine M3 nach außen zieht (seit Rev. 18). Vorn an jedem 2040
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
Stehbolzen, USB nach hinten zum Pi; rechts der **Abwärtswandler 24 → 12 V** für den
Laser (43 × 24 × 20 mm) und drei **Wago-Klemmen** (221-415 für +24 V,
2 × 221-420 für GND und +5 V); hinten **Einbaubuchse** (Hohlstecker
5,5 × 2,1) und runder **Schalter** (Blende Ø22,5, seit Rev. 4). Der
**Deckel** trägt den 24-V-Lüfter über den Treibern. Seit Rev. 3 ist er
eine Haube, deren Platte 25 mm höher liegt. Eine Montageplatte hängt es mit 4 × M5 an die Rückseite des 2060,
dazwischen läuft ein Kabelkanal. Dazu Endschalter, Kabelwege, Energieketten,
Leistungsbilanz des 72-W-Netzteils und der Anschlussplan in
[docs/elektronik.md](docs/elektronik.md).

### Verkabelung (neu)

Alle 19 Leitungen vom Steckernetzteil bis zum Laser und zum Pi mit Nummer, Adern,
Farben, Querschnitt, Weg und Kauflänge; Belegung der Wago-Klemmen und des
Shields; Material, Reihenfolge beim Anschließen und eine Inbetriebnahme in
Stufen (24 V, Wandler, GRBL und Lichtschranken, Vref, Motoren,
Referenzfahrt, Laser, Not-Aus) mit den GRBL-Einstellungen. Neu gegenüber
dem alten Plan: Pull-down 10 kΩ auf der Laser-PWM, 24-V-Wächter an
Abort, Masse der Lichtschranken über die Wago. Dazu ein Bild, das jeden
der acht Schritte für sich zeigt, jede Ader von Klemme zu Klemme in ihrer
Farbe ([elektronik-verkabelung.svg](docs/elektronik-verkabelung.svg)).
Details in [docs/verkabelung.md](docs/verkabelung.md).

### Pi und Pi-Halter (neu)

Ein **Raspberry Pi Zero 2 W** mit [CNCjs](https://cnc.js.org/) ersetzt den
PC am USB des Uno. LightBurn auf dem Mac speichert Aufträge als G-Code-Datei,
gestartet werden sie im Browser am iPad, iPhone oder Mac. Der Pi schickt die
Datei selbst an den Uno, ein Abbruch des WLAN hält den Auftrag nicht an.
Er hängt mit einem **5-V-Wandler** vor Schalter und Not-Aus an der Buchse
(W18, W19) und versorgt über USB den Uno (W17). Not-Aus und Schalter
trennen weiter Motoren, Laser und Lüfter, der 24-V-Wächter meldet es an
GRBL. Pi und Wandler sitzen auf einem gedruckten **Pi-Halter** rechts neben
dem Elektronikgehäuse, mit 2 × M5 in der oberen Nut des hinteren 2060.
Der Pi liegt ganz über dem 2060, vor seiner Antenne ist kein Aluminium.
Die Software in [`pi/`](pi) richtet ein Skript ein (CNCjs 1.11.5 als
Dienst, Makros für Rahmen und Laserpunkt, Herunterfahren aus dem Browser).
Details in [docs/pi.md](docs/pi.md).

### Not-Aus (neu)

Pilztaster mit einem Wechsler (C, NO, NC): C und NC liegen in der
24-V-Leitung, NO bleibt frei. Er sitzt in einem gedruckten Gehäuse vorn am
vorderen 2060, rechts innen neben dem rechten 2040, mit 2 × M5 in der
mittleren Nut und längs verschiebbar. Das Gehäuse ist hinten offen,
45°-Rippen tragen die Laschen, und es druckt ohne Stützen. Dass die 24 V
fehlen, meldet ein Spannungsteiler an Abort, und GRBL bricht ab. Details
in [docs/notaus.md](docs/notaus.md).

### Kabelhalter (neu)

Die fest verlegten Kabel passen nicht in die untere Seitennut der 2040.
Neun gedruckte Halter, links fünf und rechts vier, hängen deshalb mit je
einer M5×10 in einer Hammermutter an der Nut. Eine Feder in der Nutöffnung
richtet sie aus. Darunter liegt eine offene Rinne (13 × 12 mm) mit Lippe,
in die die Kabel von oben fallen. Sie liegt 1 mm unter den Wänden der
Träger Y, die Kabel laufen dort also gerade durch. Links und rechts ist es
derselbe Halter, gedruckt liegend und ohne Stützen. Plätze und Kabel stehen
in [docs/kabelhalter.md](docs/kabelhalter.md).

### Opferplatte und Führungsfüße (neu)

Die Opferplatte ist eine Spanplatte 615 × 349 × 25 mm (gemessen 25,3 mm
dick). Sie liegt auf dem
Tisch zwischen vier gedruckten **Führungsfüßen** unter den Enden der
beiden 2060. Die Füße sind so hoch, wie die Platte dick ist: Ihre
Oberfläche liegt dort, wo bisher der Tisch war, und Fokus und
Werkstückhöhe (58 mm) bleiben. Jeder Fuß greift mit einer Feder in die
untere Nut und hält mit einem Flansch und 2 × M5 in Hammermuttern der
unteren Seitennut. Innen führen die Füße die Platte, links sitzt der
Anschlag, nach rechts wird sie herausgezogen. Dort hält sie ein
**Klappriegel** auf einer M5 längs X. Ein Stoß gegen die Platte drückt
ihn längs der Achse an seinen Lagerbock und kann ihn nicht aufklappen;
zum Herausnehmen klappt man ihn nach vorn um. Details in
[docs/opferplatte.md](docs/opferplatte.md).

### Spannmittel (neu)

Ein Laser drückt nicht auf das Werkstück. Gespannt wird, damit es an einer
bekannten Stelle liegt, nicht verrutscht und dünnes, verzogenes Material
flach bleibt. Ein **Anschlagwinkel** sitzt fest hinten links auf der
Opferplatte, seine Innenecke ist der Nullpunkt (`G10 L20 P1 X0 Y0`). Zwei
selbsthemmende **Exzenter** schieben das Werkstück in die Ecke, und
**Niederhalter** je Materialstärke (2–6 mm) halten dünne Platten am Rand
flach. Alles ist so flach, dass der Toolhead darüberfährt: Anschlag und
Exzenter sind 3 mm hoch, der Niederhalter ragt 2,5 mm über das Werkstück,
und der Toolhead bleibt mindestens 3,7 mm darüber. Befestigt wird mit
Spanplattenschrauben 3,0 × 20. Details in
[docs/spannmittel.md](docs/spannmittel.md).

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

### Energieketten X und Y (neu)

Beide Energieketten sind gedruckt (Modell „Energiekette“, Teilung 16,
außen 18 × 14 mm, R 20). Die X-Kette liegt direkt hinter der Trägerplatte. Der Festpunkt
sitzt in der Mitte des X-Wegs auf einer **Wanne** über dem Portalrohr, die
Schleife zeigt nach rechts. Drei **Stützen** halten die Wanne. Sie sitzen mit
je einer M5 in der hinteren Nut des Rohrs und reichen über X-Riemen und
Riemenhalter. Am Toolhead trägt ein **Kettenhalter** über dem Riemenhalter
das bewegte Ende. 17 Glieder reichen, am rechten Ende läuft der Bogen
3,25 mm über den Lagerschlitten. Wanne und Stützen baut `Portal.py`
(seit Rev. 19), den Kettenhalter `ToolheadZ.py` (seit Rev. 35), mit einer
Bohrlehre für die schon gedruckte Trägerplatte. Seit Portal Rev. 22 und
ToolheadZ Rev. 37 rechnen beide wieder mit R 20: Die Schleife der
gedruckten Kette ist außen 50 mm hoch (gemessen). Seit Portal Rev. 21 laufen die Litzen in der
oberen Nut des Rohrs zum Festpunkt, ein **Kabelflügel** an der Stütze hält
sie mit zwei Kabelbindern. Die **Y-Kette** (16 Glieder) liegt außen am
linken 2040: Ihr bewegtes Ende trägt ein **Kettenhalter Y** auf dem linken
Schlitten, der Untertrum läuft in einer **Wanne Y** auf drei **Trägern** an
der unteren Seitennut, die Schleife zeigt nach vorn. Details in
[docs/energiekette.md](docs/energiekette.md).

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
*Portal*, *Elektronik*, *NotAus*, *Kabelhalter*, *PiHalter*, *Opferplatte* oder *Spannmittel*). Jeder Lauf legt ein **neues
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
python3 tools/verkabelung_zeichnen.py # docs/elektronik-verkabelung.svg
python3 tools/motoren_zeichnen.py     # docs/motoren-anschluss.svg
python3 tools/verkabelung.py         # Tabellen in docs/verkabelung.md
python3 tools/elektronik_box_zeichnen.py  # docs/elektronik-box.svg
python3 tools/geometrie_check.py    # nur die Einzelplatte
python3 tools/y_motorhalter_check.py  # Y-Motorhalter: Riemen in der Nut, Freigänge, Schrauben
python3 tools/y_motorhalter_zeichnen.py  # docs/y-motorhalter.svg neu erzeugen
python3 tools/endschalter_check.py  # Endschalter: Schaltpunkte, Freigänge, Schrauben, Druck
python3 tools/endschalter_zeichnen.py  # docs/endschalter.svg neu erzeugen
python3 tools/notaus_check.py       # Not-Aus-Gehäuse: Lage, Freiraum, Schrauben, Druck
python3 tools/notaus_zeichnen.py    # docs/notaus.svg neu erzeugen
python3 tools/kabelhalter_check.py  # Kabelhalter: Schraube, Rinne, Plätze, Freiraum (--doku: Tabelle neu)
python3 tools/kabelhalter_zeichnen.py  # docs/kabelhalter.svg neu erzeugen
python3 tools/pihalter_check.py     # Pi-Halter: Lage, Freiraum, Schrauben, Pi, Wandler, Druck
python3 tools/pihalter_zeichnen.py  # docs/pihalter.svg neu erzeugen
pip install manifold3d && python3 tools/stl_export.py  # stl/ neu: Kasten, Haube, Kabelhalter und Pi-Halter in Drucklage (mit Namen, z. B. PiHalter: nur diese)
python3 tools/opferplatte_check.py  # Opferplatte, Füße, Riegel: Feld, Höhen, Freiraum, Schrauben
python3 tools/opferplatte_zeichnen.py  # docs/opferplatte.svg neu erzeugen
python3 tools/spannmittel_check.py  # Spannmittel: Höhe unter dem Toolhead, Lage, Exzenter, Schrauben
python3 tools/spannmittel_zeichnen.py  # docs/spannmittel.svg neu erzeugen
python3 tools/kette_zeichnen.py     # docs/energiekette.svg und energiekette-y.svg neu erzeugen
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
ganzen Y-Weg, das Elektronikfach hinter
dem hinteren 2060, in das weder Portal noch Toolhead hineinfahren, die
X-Energiekette mit Wanne und Stützen über den ganzen X-Weg samt Kabelweg
und die Y-Energiekette mit Halter, Wanne und Trägern über den ganzen
Y-Weg.

**Stand:** alle Prüfungen bestanden (ToolheadZ Rev. 38, Portal Rev. 28 mit
dem Y-Motorhalter, `y_motorhalter_check.py`, Opferplatte Rev. 3,
Spannmittel Rev. 1). Neu ist Portal Rev. 28: Die Klemmtürme aus Rev. 26/27
streiften an der engsten Stelle an der 2040. Rev. 26 hatte die an einer
Stelle gemessenen 3,0 statt 2 mm Luft für den ganzen Weg angenommen. Jetzt
stehen die Türme an der engsten Stelle 1 mm neben der 2040, an der
weitesten 2 mm (`kt_luft_mehr` 0, `kt_luft_streuung` 1 mm). Die
Riemenmitte liegt 3,9 bis 4,9 mm vor der Seitenfläche, der vordere Trum
taucht auch an der weitesten Stelle in die Nut. Nur die vier Klemmtürme
neu drucken, die Stifte bleiben
([portal-y-schlitten.md](docs/portal-y-schlitten.md#1-mm-neben-der-2040-seit-rev-26)).
Davor kam Portal Rev. 27: Die Klemmtürme sind nur noch oben, im Block um
die Gewindeeinsätze, so breit wie bisher; darunter ist die Wand innen neben
dem Riemen 5,4 statt 12,2 mm dick. Der Querstift wurde ein Ø3 × 8 oder
M3×8, ein Turm braucht gut ein Drittel weniger Material
([portal-y-schlitten.md](docs/portal-y-schlitten.md#schmaler-unter-den-einsätzen-seit-rev-27)).
Davor kam Portal Rev. 26: Die Klemmtürme rückten 2 mm an die 2040 heran,
der Querstift steckt seitdem in einem Sackloch und kann nicht zur 2040
hinauswandern.
Davor kam Portal Rev. 25: Die Y-Klemmtürme rückten von 7,2 mm an die 2040
heran, damit der Riemen in die obere Nut läuft.
Davor kam `Spannmittel.py`: Anschlagwinkel als
Nullpunkt, Exzenter und Niederhalter für das Werkstück, alles flach genug
für den Toolhead. Davor kam `Opferplatte.py`: vier Führungsfüße für die Spanplatte 615 × 349 × 25 mm,
seit Rev. 2 so hoch wie ihre gemessenen 25,3 mm; die Maschine steht
darauf, die Plattenoberfläche liegt auf der alten Tischhöhe. Rev. 3 hält
die Platte an der offenen rechten Seite mit einem Klappriegel, den ein
Ausleger am Fuß vorn rechts trägt. Portal Rev. 24
stellt auf den
linken Stirnblock einen Anschlag für den X-Motorhalter: Bis dahin hielt
ihn nur die Reibung unter seinen zwei Schrauben, und bei kräftig
gespanntem Riemen rutschte er nach innen. Der gedruckte Halter passt
weiter, neu gedruckt wird nur der linke Schlitten. Portal Rev. 23 und ToolheadZ
Rev. 38 geben der Kette 0,5 mm Spiel je Seite in Wannen und Kettenhaltern
(vorher 0,3); die X-Kette liegt dafür 0,2 mm weiter hinten. Der linke
Schlitten hat die zwei Löcher für den Kettenhalter Y im Modell (seit
Rev. 21, für einen Neudruck), in den schon gedruckten bohrt man sie mit
der Bohrlehre. Portal Rev. 22 und ToolheadZ
Rev. 37 rechnen die Ketten wieder mit R 20, nach der gemessenen Schleife
(außen 50 mm, 4 Gelenke im Bogen): X 17, Y 16 Glieder, der Kettenhalter
24 mm tiefer, die Wanne Y 24 mm höher. Portal Rev. 21 bringt die
gedruckte Y-Energiekette (Kettenhalter Y, Wanne Y, drei Träger)
und den Kabelweg zur X-Kette in der oberen Nut mit dem Kabelflügel am
Festpunkt ([energiekette.md](docs/energiekette.md)). Portal Rev. 19 und ToolheadZ
Rev. 35 bringen die gedruckte X-Energiekette: Wanne mit Festpunkt und drei
Stützen am Portalrohr, Kettenhalter an der Trägerplatte
([energiekette.md](docs/energiekette.md)). Portal Rev. 20 und ToolheadZ
Rev. 36 rechneten sie mit R 32, nach einer Schätzung von 30° je Glied.
Portal Rev. 18 lenkt den
X-Riemen mit einem Ritzel auf einer Welle um, die in Kugel- und Gleitlager
im Lagerschlitten läuft; Spannbock und Schlitten ersetzen Umlenkhalter und
Spannklotz (ToolheadZ Rev. 34 ändert dazu nur einen Kommentar). Portal
Rev. 14 legt das
hintere 2060 nach der Messung 435 mm hinter das vordere (die 2040 stehen
hinten 110 mm über); nach hinten begrenzt jetzt das Schienenende den Y-Weg.
Elektronikgehäuse Rev. 2 mit den am Aufbau gemessenen Werten (Stapelhöhe,
Wandler, Wago) gezeichnet, geprüft und gedruckt, seit Rev. 3 mit einer
höheren Haube als Deckel, seit Rev. 4 mit rundem Schalterloch
([elektronik.md](docs/elektronik.md)). Die Endschalter X und Y baut seit
Rev. 15 `Portal.py` mit, geprüft mit `endschalter_check.py`
([endschalter.md](docs/endschalter.md)),
Not-Aus-Gehäuse Rev. 5 mit `notaus_check.py` ([notaus.md](docs/notaus.md)),
Kabelhalter Rev. 2 mit `kabelhalter_check.py` ([kabelhalter.md](docs/kabelhalter.md)),
Pi-Halter Rev. 2 mit `pihalter_check.py` ([pi.md](docs/pi.md)). Die
Verkabelung steht als Kabelliste in `tools/verkabelung.py`,
`elektronik_check.py` prüft sie (Netze, Not-Aus, Kontakte, Klemmen, Längen,
Tabellen in [verkabelung.md](docs/verkabelung.md)). Der
Zugangskonflikt zwischen Laser und Z-Wagen ist gelöst, indem der Laser
30,75 mm tiefer hängt und über senkrechte Langlöcher eingestellt wird —
[Laserhöhe](docs/toolhead-z.md#laserhöhe-langloch-statt-rechnen).
