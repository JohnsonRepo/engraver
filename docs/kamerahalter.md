# Kamerahalter — Autofokus über Z

Eine Kamera am Pi soll den Fokus selbst einstellen. Dieser Halter trägt sie
**vorn rechts auf dem vorderen 2060**, am rechten 2040 und vor dem
Elektronikfach. Dort sitzt die Kamera an der Maschine schon, und von dort
reicht ihr 200-mm-Kabel bis zum Pi. Sie schaut schräg nach hinten links und
nach unten zu einem festen Messpunkt kurz innerhalb der Anschlagecke vorn
rechts.

![Kamerahalter von oben, Blick zur Ecke, Schnitt längs der Sichtlinie, Halter im Schnitt, Wand in Blickrichtung](kamerahalter.svg)

Die Maße stehen in `fusion/Kamerahalter/Kamerahalter.py` (Rev. 3). Geprüft
wird mit `python3 tools/kamerahalter_check.py`:

- Lage auf dem 2060
- Freiraum zu allem, was Toolhead und Portal über den ganzen Weg
  überstreichen, zum Fach und Deckel, zum 2040, zum Eckwinkel, zum Y-Riemen
  und zum Y-Motor
- Sicht zum Messpunkt für jede Dicke: frei, im Bild, scharf
- Schrauben, Druck und Kabel

Die Zeichnung erzeugt `python3 tools/kamerahalter_zeichnen.py`.

**Rev. 3 (2026-11-21):** nur die Höhe der Opferplatte. Maschine und
Platte stehen auf demselben Tisch, die Oberfläche liegt bei Z −103,7 statt
−129; die Führungsfüße darunter gab es nur im Modell
([opferplatte.md](opferplatte.md)). Der Halter bleibt, wie er gedruckt
ist: Seine Neigung zielt weiter auf Oberflächen von −129 bis −71 mm, der
Punkt liegt jetzt in der oberen Hälfte des Bilds. **Nicht neu drucken.**

**Rev. 2 (2026-11-19):**
- **Neu für vorn rechts.** Rev. 1 stand hinten links vor dem Fach und hielt
  die Kamera waagerecht. Seit Elektronikfach Rev. 2 steht das Fach vorn.
  Die Kamera ist an der Maschine vorn rechts montiert, mit dem Halter Rev. 1
  um 180° gedreht, und soll dort bleiben.
- **Der Anschlag kommt vor die Kamera**, in die Ecke vorn rechts
  ([spannmittel.md](spannmittel.md), Spannmittel Rev. 2). Von hier liegt der
  Messpunkt 16° bis 40° unter der Linse. Das Bild reicht hochkant nur ±27°,
  deshalb ist die Kamera jetzt geneigt.

## Wie der Autofokus misst

1. Der Kopf fährt an den **Messpunkt**: 30 mm links und 58 mm hinter der
   Innenecke des Anschlagwinkels. Mit dem Nullpunkt in der Ecke
   ([spannmittel.md](spannmittel.md#nullpunkt-einrichten-einmal)) ist das
   `G54 X-30 Y58`; Y+ zeigt bei GRBL nach hinten. Z fährt ganz nach oben.
2. Der Laser geht kurz und schwach an, wie beim Makro „Laserpunkt 1 %“, nur
   kürzer.
3. Der Strahl steht senkrecht. Der Punkt liegt deshalb bei jeder
   Werkstückdicke an derselben Stelle, nur höher oder tiefer. Die Kamera
   sieht ihn von vorn rechts oben: Je dicker das Werkstück, desto höher
   liegt er im Bild.
4. Ein Bild genügt. Aus der Lage des Punkts im Bild folgt über eine einmal
   gelernte Tabelle das Z, bei dem der Laser scharf ist. Z fährt dorthin.

Dafür muss die **Linse des Lasers fest** stehen. Den Fokusabstand muss
niemand kennen: Gelernt wird mit drei oder mehr Werkstücken, die von Hand
scharfgestellt sind. Programm, Widget in CNCjs, Einlernen und Fehlersuche:
[autofokus.md](autofokus.md).

Klares Acryl und spiegelnde Flächen lassen den Punkt durch oder spiegeln ihn
weg: Schutzfolie oder Abdeckpapier drauflassen.

## Kamera

An der Maschine steckt eine **Raspberry Pi Kamera v1.3** (OV5647, Modul
„P5V04A SUNNY“, rote LED; Foto vom 2026-11-19), kein Camera Module 3. Für
den Halter ist das gleich: Platine, Lochbild und Steckerkante sind dieselben.
Ein Camera Module 3 passt also auch. Sein Linsenblock ist gut 2 mm höher, die
Linse säße dann etwas weiter vorn.

| | v1.3 (verbaut, gerechnet) |
|---|---|
| Optik | f = 3,6 mm, f/2,9, 2592 × 1944 Pixel zu 1,4 µm, Bildwinkel 53,5° × 41,4° |
| Fokus | **fest**, ab Werk 1 m bis unendlich: muss auf den Messabstand gedreht werden ([unten](#fokus-der-kamera-einstellen)) |
| Bautiefe | 9 mm; die Linsenfront 5,25 mm vor der Platine ist daraus geschätzt `[?]` |

## Lage

| | |
|---|---|
| Fuß | oben auf dem vorderen 2060, X +190 … +230 (Maschinenkoordinaten wie `Portal.py`), 2 × M5×10 in Hammermuttern der Nut bei X +196 und +207 |
| Eckwinkel | innen am rechten 2040 sitzt ein 20-mm-Winkel in der oberen Nut des 2060 ([hardware-notizen.md](hardware-notizen.md)). Fuß und Steg sind darüber unter 45° ausgespart, 1 mm Luft zur Hülle 20 × 20 |
| Kamera | hochkant, die Kabelkante zeigt nach vorn links zum Fach |
| Linse | X +216,5, Y +185, Z −42: über der Innenkante des 2060, **30,5 mm vom rechten 2040** und **62 mm über der Platte** |
| Blick | 232,6° gegen +X, also schräg nach hinten links, und **27,8° nach unten** geneigt |
| Messpunkt | X +153,35, Y +102,5; **108 bis 121 mm** von der Linse |
| Im Bild | quer genau auf der Achse (Bild ±20,7°), senkrecht 2,9° unter (leere Platte) bis 12,2° über der Achse (32,7 mm Werkstück) (Bild ±26,8°): mindestens 14,6° vom Rand |
| Auflösung | 18,4 Pixel je mm Höhe, also 0,05 mm je Pixel; ein Diodenlaser verzeiht etwa ±0,5–1 mm |
| Luft | 3,5 mm zum Laser am Ende des Y-Wegs; 1 mm zum Fach, der Deckel geht ab; 4,7 mm zum Y-Riemen; 6 mm zum Y-Motorhalter |

### Warum geneigt

Von der Ecke vorn rechts aus liegt der Punkt für die leere Platte 40° und für
58 mm Werkstück 16° unter der Waagerechten. Waagerecht hochkant reicht das
Bild nur ±27°. Die Neigung zielt auf die Mitte: Dann liegen die dünnste und
die dickste Platte gleich weit unter und über der Bildmitte. Gerechnet war
das mit der Platte bei Z −129; tatsächlich liegt sie bei −103,7 (Rev. 3),
und das dickste Werkstück ist 32,7 mm. Der Punkt bleibt trotzdem mindestens
14,6° vom Bildrand. Die Wand lehnt
28° nach vorn; ihre Kameraseite hängt so weit über, das druckt ohne Stützen.

### Warum genau dort

- **Laser:** Er fährt vorn bis Y 182, aber nur bis X 204,8. Rechts davon
  kommt nur die Schlittenplatte, und die nur bis Y 147.
- **Platz:** Deshalb darf die Kamera nur rechts von X 208 vor die Innenkante
  des 2060 ragen.
- **Riemen und Fach:** Rechts bleibt sie links vom Y-Riemen (X 242,4), hinten
  frei vom Fach.
- **Wahl:** Linse und Neigung kommen aus einer Suche über X, Y und Z, mit
  dem größten kleinsten Abstand zu Laser, Fach und Riemen.

### Warum dieser Messpunkt

So bleibt die Kamera auch beim dicksten Werkstück über 100 mm entfernt, und
der Punkt liegt für alle Dicken weit genug im Bild.

- **Werkstück:** Es muss den Punkt abdecken. Ab der Ecke braucht es
  mindestens etwa 35 mm nach links und 63 mm nach hinten. Kleinere Teile
  fokussierst du von Hand.
- **Frei halten:** Am Punkt und etwa 15 mm davon in Richtung Kamera (nach
  vorn rechts) darf nichts auf dem Werkstück stehen, auch kein Niederhalter.
  Weiter weg läuft die Sichtlinie hoch genug über alles hinweg, auch über
  den Anschlag (dort etwa 60 mm hoch).

## Teile

| Menge | Teil | wofür |
|---|---|---|
| 1 | Kamerahalter, PETG: `stl/Kamerahalter_r2.stl` (siehe [Druck](#druck)) oder aus Fusion | Halter |
| 1 | Raspberry Pi Kamera v1.3 (verbaut; ein Camera Module 3 passt auch) | Autofokus |
| 1 | Kamerakabel **Standard–Mini** (15 auf 22 Pole), 200 mm | zum Pi Zero |
| 2 + 2 | M5×10 Zylinderkopf + Hammermutter M5 Nut 6 | Fuß → Nut oben auf dem 2060 |
| 2 + 2 | M2×8 Zylinderkopf + Mutter M2 | Kamera oben; unten stecken zwei Zapfen |

## Druck

- **Lage:** PETG, der Fuß liegt auf dem Bett. Keine Stützen.
- **Wand:** Sie lehnt 28° nach vorn. Polster und Zapfen sind Tränen mit der
  Spitze unten, die Löcher für die M2 Tränen mit der Spitze oben, jeweils im
  geneigten Rahmen.
- **Muttertaschen:** Sechsecke mit einer Ecke oben.
- **Aussparung für den Eckwinkel:** Sie hat genau 45°.
- **Fuß:** Am Fuß sitzt die übliche Fase von 0,4 mm gegen den Elefantenfuß.
- **Menge:** Etwa 5,9 cm³, also gut 7 g.

Vorher die **Bohrlehre_Kamera** drucken. In Fusion ist sie ausgeblendet: eine
2-mm-Platte mit Umriss, Lochbild und Linsenmitte der Kamera. Auf die Platine
legen: Passen die vier Löcher, stimmt das Lochbild der Polster.

Die STL schreibt `tools/stl_export.py` aus demselben Bauplan wie Fusion:

```sh
pip install manifold3d
python3 tools/stl_export.py Kamerahalter
```

## Fokus der Kamera einstellen

Die v1.3 ist ab Werk auf 1 m bis unendlich eingestellt. Bei 108 bis 121 mm
wäre der Punkt ein Fleck von rund 30 Pixeln. Die Linse wird deshalb einmal
auf **114 mm** gedreht. Dann ist der Punkt überall höchstens 1,6 Pixel
unscharf, und seine Mitte findet das Skript genau. Hast du sie schon auf
120 mm gedreht (Rev. 2), lass es so: Das sind höchstens etwa 3 Pixel.

1. Kamera am Pi, Bild live im Browser ansehen:
   **`http://laser.local:8080`** ([pi.md](pi.md#kamera)). `rpicam-hello`
   zeigt am Pi ohne Bildschirm nichts.
2. Ein bedrucktes Blatt 114 mm vor die Linse halten, gut beleuchtet: Zeigt
   die Seite „zu dunkel“, rauscht das Bild zu stark zum Scharfstellen.
3. Die Linse mit einer Spitzzange oder dem Fokusring vorsichtig **gegen den
   Uhrzeigersinn** herausdrehen, bis die Schrift scharf ist. Ab Werk ist sie
   mit einem Punkt Kleber gesichert, der beim ersten Drehen bricht. Nicht
   mehr als nötig drehen.
4. Die Zahl **Schärfe** oben auf der Seite hilft: Sie steigt, je schärfer
   das Bild. Etwas über den besten Wert hinausdrehen, bis sie wieder fällt,
   dann zurück. Vergleichbar ist sie nur bei demselben Blatt an derselben
   Stelle und gleichem Licht.

Das geht auch mit der Kamera im Halter; die Linse zeigt frei nach vorn.

## Montage

1. Den alten Halter (Rev. 1) abschrauben. Die Hammermuttern bleiben in der
   Nut, schiebe sie auf X +196 und +207: 20,5 und 9,5 mm links von der
   Linse.
2. **Eckwinkel ansehen:** Sitzt innen am rechten 2040 ein Winkel auf dem
   2060? Ist er größer als 20 × 20 mm, sag Bescheid, bevor du druckst.
3. Zwei Muttern M2 von hinten in die Sechskanttaschen oben in der Wand
   drücken.
4. Die Kamera hochkant mit der Kabelkante zum Fach (nach vorn links) auf die
   Polster legen, die beiden Zapfen unten in die Löcher. Oben mit
   2 × M2×8 von vorn festschrauben.
5. Das Kabel an der Kamera einstecken, die Kontakte zur Platine.
6. Den Halter auf das 2060 setzen und mit 2 × M5×10 festziehen. Der Inbus
   geht von oben, auch mit eingesetzter Kamera.
7. **Kabel:** Es tritt zum Fach hin aus. Führe es über das 2060 ins Fach zum
   Pi. Am Aufbau reicht das 200-mm-Kabel. Im Modell liegt der Pi anders und
   der Weg wäre etwa 290 mm; das Innere des Fachs ist noch Zwischenstand.

### Kamerakabel

Das Flachbandkabel ist isoliert: Die Leiter liegen zwischen zwei
Kunststofffolien, blank sind nur die Kontakte an den versteiften Enden, und
die stecken in den Buchsen. Andere Kabel, das Profil oder das Fach darf es
berühren.

* **Abstand zu Störern:** Es überträgt schnelle Bilddaten und ist nicht
  abgeschirmt. Nicht lang parallel zu Motorleitungen, der Laserleitung (W7,
  PWM und 12 V) oder der 24-V-Versorgung legen und nicht mit ihnen bündeln;
  quer kreuzen ist kein Problem. Im Fach gehört es in die Signalgasse, nicht
  in die Leistungsgasse. Am rechten Y-Motor nicht entlangführen.
* **Bildfehler** (Aussetzer, Streifen, Kamera nicht gefunden): erst den
  Sitz beider Stecker prüfen, dann, ob das Kabel doch an Motor- oder
  Laserleitungen liegt.
* **Falten statt knicken:** Richtung mit 45°-Falten wechseln, nicht
  mehrmals an derselben Stelle falten, nie direkt hinter dem steifen Ende
  knicken.
* **Kanten:** Wo das Kabel über eine Profil- oder Gehäusekante läuft, die
  Kante entgraten oder ein Stück Kapton-Band darüberkleben.
* **Befestigen** mit Klebeband, nicht mit festgezogenen Kabelbindern; die
  schneiden in die Folie. Das Kabel liegt fest und bewegt sich nicht —
  dauerndes Biegen wie in einer Energiekette hält es nicht aus.
* **Einstecken nur stromlos:** Der Pi hängt vor Schalter und Not-Aus, der
  Schalter macht ihn nicht stromlos. Erst in CNCjs **Pi herunterfahren**,
  dann das Netzteil ziehen.
* **Enden:** das breite (15 Pole) an die Kamera, das schmale (22 Pole) an
  den Pi. Bügel der Buchse vorsichtig öffnen, Kabel gerade bis zum Anschlag
  einschieben, Bügel schließen; an beiden Enden zeigen die blanken Kontakte
  zur Platine. Die Kamera nur an den Kanten anfassen.

## Parameter

| Name | Wert | Wirkung |
|---|---|---|
| `linse_x`, `linse_y`, `linse_z` | +216,5 / +185 / −42 mm | Lage der Linsenfront. Blick und Neigung rechnet das Skript daraus und aus dem Messpunkt |
| `mp_links`, `mp_hinten` | 30 / 58 mm | Messpunkt ab der Innenecke des Anschlags |
| `ecke_x`, `ecke_y` | +183,35 / +160,5 mm | Innenecke des Anschlags vorn rechts (wie `Spannmittel.py`) |
| `kabel_seite` | −1 | Kabelkante zum Fach (+1: gespiegelt) |
| `pad_h` | 2 mm | Polster: Platz für die Bauteile hinten auf der Kamera |
| `fuss_x0`, `m5_links`, `m5_rechts` | +190 / +196 / +207 mm | Fuß und Schrauben; rechts endet der Fuß am Schnitt über dem Eckwinkel |
| `winkel_l`, `winkel_luft` | 20 / 1 mm | Hülle des Eckwinkels und Luft dazu |
| `cam_*` | v1.3 | Kamera: Platine, Linse, Optik |

Wer einen Wert ändert, lässt danach `tools/kamerahalter_check.py` laufen.
Die Prüfung meldet, ob der Punkt im Bild bleibt und scharf ist, ob die Luft
reicht und ob der Halter am Stück druckt.

## Noch offen

- **Eckwinkel** `[?]`: Die Schenkel sind nicht gemessen. Gerechnet ist mit
  einer Hülle 20 × 20 mm unter der Schräge.
- **Kamera** `[w]`/`[?]`: Lochbild nach dem Maßblatt, die Linsenhöhe der
  v1.3 geschätzt. Vor dem Druck die Bohrlehre an die Platine halten.
- **Fokus der Kamera:** auf 114 mm drehen (oben); 120 mm aus Rev. 2 reichen.
- **Elektronikfach:** Zwischenstand. Am Aufbau liegt der Pi anders als im
  Modell.
- **Y-Endschalter:** referenziert seit Portal Rev. 32 vorn; am Messpunkt
  in G54 ändert das nichts, G54 selbst einmal neu setzen
  ([spannmittel.md](spannmittel.md#nullpunkt-einrichten-einmal)).
- **Fokusabstand** des Lasers: noch nicht gemessen. Ohne ihn weiß der
  Autofokus nicht, wohin er Z fahren soll.
- **Software** auf dem Pi: Bild mit fester Belichtung aufnehmen, den Punkt
  finden, die Höhe aus der Tabelle, Z über CNCjs.
