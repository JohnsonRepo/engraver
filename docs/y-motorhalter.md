# Y-Motorhalter — Antrieb der Y-Achse

Erzeugt von `fusion/Portal/Portal.py` (seit Rev. 16, jetzt Rev. 24; Komponenten
`Y-Motorhalter_links` und `Y-Motorhalter_rechts`, zweimal dasselbe
Druckteil). Bis Portal Rev. 15 stand er im eigenen Skript
`fusion/YMotorhalter/YMotorhalter.py` (Rev. 5), siehe
[Portal Rev. 16](#portal-rev-16-im-portal-skript-2026-09-30).
Geprüft mit `python3 tools/y_motorhalter_check.py`, zusammen mit dem Portal
in `python3 tools/portal_check.py`. Skizze in
[y-motorhalter.svg](y-motorhalter.svg) (neu erzeugen mit
`python3 tools/y_motorhalter_zeichnen.py`).

![Y-Motorhalter](y-motorhalter.svg)

## Was hier zusammenkommt

So sieht der Y-Antrieb nach deinen Angaben und dem Foto aus (2026-09-26):

* **Zwei NEMA 17, je Seite einer**, jeweils vorn an ihrer 2040. Die 2040
  steht hochkant und liegt auf dem vorderen 2060, das 35 mm hinter ihrer
  Stirnseite sitzt. Oben auf ihr sitzt die Linearführung.
* Der **Y-Riemen läuft in den oberen Nuten** beider Seitenflächen der 2040,
  in der rechten hin und in der linken zurück, und am Profilende um das
  Ritzel.
* Das **Ritzel sitzt direkt auf der Motorwelle**, mittig zur 2040. Der Motor
  hängt unter einer Platte etwa auf Höhe der unteren Nut, die Welle zeigt
  nach oben.
* Befestigt wird mit **Nutensteinen in den unteren Nuten**, weil in den
  oberen der Riemen läuft. Die Schrauben sitzen an **beiden**
  Seitenflächen, der Halter ist also ein U-Bügel.
* Gespannt wird, indem der **Motor in Langlöchern** vom Profilende
  wegrückt.

Er ersetzt den alten Y-Motorhalter von `Portal.py` (bis Rev. 15), den du
gedruckt hast: Dort lag die Motorachse 15,55 mm neben der Profilmitte, und
die M5 saßen in der oberen Nut. Heute baut `Portal.py` diesen hier
([portal-y-schlitten.md](portal-y-schlitten.md#y-antrieb-vorn)).

| Teil | Material | Funktion |
|---|---|---|
| **2× Y-Motorhalter** | PETG, 32 g je Stück (voll gerechnet) | Schenkel an beiden Seitenflächen, Joch vor der Stirnseite, Platte für den Motor, Führungswände |
| 2× NEMA 17 + GT2-Ritzel 20 Z, Bohrung 5 | Kaufteil | Motor hängt unter der Platte, Ritzel auf Höhe der oberen Nut |
| 8× M5×12 + Scheibe + Nutenstein M5 (Nut 6) | Kaufteil | je Halter 4, in den unteren Nuten |
| 8× M3×10 + Scheibe DIN 125 | Kaufteil | je Motor 4, von oben |

Das Teil ist symmetrisch zur Mitte der 2040. **Dasselbe Teil passt links
und rechts**: zweimal drucken, nichts spiegeln.

## Rev. 3: neues Konzept (2026-09-26)

Rev. 1 und 2 beruhten auf einem Missverständnis. Dort saß **ein** Motor
mittig an der hinteren Traverse. Ein geschlossener Riemen trieb über ein
Omega mit zwei Umlenkrollen zwei senkrechte Edelstahlwellen. Dein Foto
zeigt etwas anderes: Der Y-Riemen läuft in den oberen Nuten der 2040 und
kehrt am Profilende um. Genau dort sitzt der Motor, das Ritzel direkt auf
seiner Welle. Rev. 3 ersetzt den alten Halter deshalb ganz. Umlenkrollen,
Motorriemen und Edelstahlwellen braucht der Y-Antrieb nicht mehr.

Deine beiden Korrekturen von vorher gelten weiter:

* **Nutensteine nur in der unteren Nut**, oben läuft der Riemen.
* **Motor in die Profilmitte.** Beim gedruckten Halter aus `Portal.py`
  liegt die Motorachse 15,55 mm neben der Mitte. Jetzt liegt sie genau auf
  X = 0, und beide Trume laufen gerade in ihre Nut.

## Rev. 4: gemessene Motoren (2026-09-27)

Deine Motoren sind am Aufbau gemessen: **37 mm** Körper, **23 mm** Welle
(60 mm mit Welle), eingetragen in den Hardware-Notizen. Rev. 3 rechnete mit
48 und 24 mm. Damit das Ritzel weiter ganz auf der Welle sitzt und seine
Spur auf Höhe der oberen Nut bleibt, rückt die Platte **1 mm höher**
(Z = 11,5 bis 17,5); zwischen Ritzel und Platte bleibt 1 mm. Der Motor
endet jetzt 25,5 mm unter der 2040.

Ist ein Rev.-3-Halter schon gedruckt, geht er auch: dann das Ritzel 1 mm
über das Wellenende hinaus schieben, bis der Riemen gerade in die Nut läuft.

## Rev. 5: kürzere Schenkel (2026-09-27)

Am vorderen 2060, 35 mm hinter der Stirnseite, halten **Winkel** die 2040
an ihren Seitenflächen. Die Schenkel sind deshalb **30 statt 40 mm** lang
und enden 5 mm vor dem 2060, die M5 sitzen bei 8 und 22 mm hinter der
Stirnseite, wie am alten Halter aus `Portal.py`. Die Prüfung liest die Lage
des 2060 aus `Portal.py`.

## Portal Rev. 16: im Portal-Skript (2026-09-30)

Der Halter ist ins Portal-Skript umgezogen. `Portal.py` baut ihn an beiden
vorderen Ecken, das eigene Skript `YMotorhalter.py` gibt es nicht mehr.
Form, Maße und Lage sind dieselben wie in Rev. 5. Seine eigenen Parameter
heißen jetzt `ymh_…`, Profil, Nut, Riemen, Ritzel und Motor nimmt er aus
den gemeinsamen Werten des Portals ([Parametrik](#parametrik)).

Damit rechnen `Ref_Riemen` und `portal_check.py` mit den mittigen Ritzeln
und mit diesem Halter statt mit dem alten. Zwei Dinge zeigen sich dabei,
siehe [Noch offen](#noch-offen), Punkte 4 und 5: Die Riemenlänge ändert sich
über den Y-Weg um bis zu 2 mm, und am vorderen Schienenende kommt der
vordere Klemmturm dem inneren Schenkel nahe.

## Bezug und Koordinaten

**Y = 0 ist die Stirnseite der 2040, +Y zeigt vom Profil weg. Z = 0 ist
ihre Unterkante, X = 0 ihre Mitte.** Im Fusion-Modell sind Y und Z
getauscht wie im Toolhead (Modell-Z = Maschine Y).

### Y-Kette (ab Stirnseite der 2040)

| Y | Ebene |
|---|---|
| −35 | Vorderseite des vorderen 2060 (darunter, mit Winkeln an der 2040) |
| −30 | Schenkel hinten, 5 mm vor dem 2060 |
| −22 / −8 | M5 in der unteren Nut, je Seite |
| **0** | **Stirnseite der 2040 = Anlage des Jochs** |
| +4 | Joch vorn |
| +5,0 | Motor vorn, ganz innen |
| **+26,15 … +34,15** | **Motorachse**, ganz innen … ganz außen (Spannweg 8 mm) |
| +55,3 | Motor hinten, ganz außen |
| +56,8 | Platte und Führungswände vorn |

### Z-Kette (ab Unterkante der 2040)

| Z | Ebene |
|---|---|
| +40 | Oberkante der 2040, darauf die Linearführung |
| +34,5 | Ritzel oben = Wellenende |
| +33 / +27 | Riemen oben / unten |
| **+30** | **Riemenmitte = Mitte der oberen Nut** |
| +26,9 | untere Kante der oberen Nutöffnung |
| +22 | Madenschraube in der Ritzelnabe |
| +18,5 | Ritzel unten (Nabe) |
| **+17,5** | **Platte oben = Oberkante des ganzen Halters** |
| +13,5 | Zentrierbund oben (steckt in der Platte) |
| +11,5 | Motorflansch = Platte unten |
| **+10** | **M5 in der unteren Nut** |
| +1 | Halter unten |
| 0 | Unterkante der 2040 |
| −25,5 | Motor unten (37 mm, gemessen) |

## Der Riemen in der Nut — warum 20 Zähne

Liegt das Ritzel mittig, liegen die beiden Trume genau einen
Teilkreisdurchmesser auseinander. Mit 20 Zähnen sind das 12,73 mm, und beide
Trume laufen in der Mitte ihres Nutkanals:

* Riemenrücken **3,26 mm** hinter der Seitenfläche: **1,46 mm** Luft zur
  Lippe (1,8 mm)
* Zahnspitzen **4,64 mm** hinter der Seitenfläche: **1,36 mm** Luft zum
  Nutgrund (6,0 mm)

| Ritzel | Luft zur Lippe | Luft zum Nutgrund | |
|---|---|---|---|
| 16 Z | 2,73 mm | **0,09 mm** | streift |
| 18 Z | 2,09 mm | 0,73 mm | knapp |
| **20 Z** | **1,46 mm** | **1,36 mm** | **mittig** |
| 22 Z | 0,82 mm | 2,00 mm | knapp |
| 24 Z | **0,18 mm** | 2,64 mm | streift |

Die Nutmaße sind Richtwerte für Nut 6 `[w]`. Ist dein Nutgrund flacher,
`nut_tiefe` eintragen und das Prüfwerkzeug laufen lassen. 40 mm je
Umdrehung, also 80 Schritte/mm bei 1/16. Umschlingung 166 bis 178 Grad, je
nach Stellung des Portals (der Wagen-Trum läuft schräg an), also 9 bis 10
Zähne im Eingriff; am hinteren Ritzel sind es 161 bis 178 Grad.

## Aufbau des Halters

**Schenkel.** Zwei Schenkel, 6 mm dick und 30 mm lang, liegen an beiden
Seitenflächen der 2040 an, von Z = 1 bis 17,5. Jeder hat zwei M5 in der
unteren Nut, bei Y = −8 und −22; dahinter sitzen am 2060 die Winkel. Oberhalb von Z = 17,5 bleibt die
Seitenfläche frei, also auch die ganze obere Nut. Innen sind 0,2 mm Luft
je Seite, die Schrauben ziehen die Schenkel an.

**Joch.** Eine 4 mm dicke Wand quer vor der Stirnseite verbindet die beiden
Schenkel und liegt an der Stirnseite an. Damit sitzt der Halter längs des
Profils immer an derselben Stelle, und der Riemenzug drückt ihn gegen die
Stirnseite, statt an den Schrauben zu ziehen.

**Platte.** Sie ist 6 mm dick und liegt vor der Stirnseite bei Z = 11,5 bis
17,5. Der Motor hängt darunter, der Flansch liegt an ihrer Unterseite an,
die Welle zeigt nach oben. Zentrierbund und Welle gehen durch ein 22,4 mm
breites Langloch, die vier M3 durch Langlöcher. Alle fünf erlauben ±4 mm.
Dicker geht die Platte nicht: 23 mm Motorwelle = 6 mm Platte + 1 mm Luft
+ 16 mm Ritzel.

**Führungswände.** Unter der Platte stehen links und rechts neben dem Motor
zwei 4 mm dicke Wände, je 1 mm vom Motor entfernt. Sie führen ihn beim
Spannen gerade und steifen die Platte aus.

Alles endet oben bündig bei Z = 17,5. Diese Fläche liegt beim Druck auf dem
Bett.

## Ritzel und Motorwelle

Ritzel **mit der Nabe nach unten** aufschieben, bis seine Oberkante bündig
mit dem Wellenende ist (Z = 34,5). Dann steht die 7 mm breite Spur mittig
auf Z = 30, und der 6 mm breite Riemen läuft gerade in die Nut. Die
Madenschraube (Z = 22) trifft die Abflachung, die bei 15 mm Länge `[w]` auf
Z = 19,5 beginnt. Zwischen Ritzel und Platte bleibt 1 mm.

Läuft der Riemen nicht gerade in die Nut, das Ritzel auf der Welle etwas
verschieben. Bis zu 1 mm über das Wellenende hinaus ist in Ordnung.

## Spannen

1. Halter montiert, Motor ganz innen, die vier M3 lose.
2. Riemen um das Ritzel legen, beide Trume in ihre obere Nut.
3. Motor vom Profil weg nach außen ziehen, zum Beispiel mit einem
   Schraubendreher als Hebel zwischen Joch und Motor. Jeder Millimeter macht
   den Riemenweg 2 mm länger, insgesamt sind es **16 mm**.
4. Richtwert **~20 N je Trum**. Zum Prüfen den freien Trum anzupfen und mit
   einer Stimmgeräte-App messen: f = 1/(2·l) · √(T/μ) mit μ ≈ 8 g/m. Bei
   l = 300 mm freier Länge und 20 N sind das **~83 Hz**.
5. Die vier M3 von oben festziehen. Über den Schraubenköpfen ist Platz für
   den Inbus, Riemen und Ritzel bleiben weit weg.

## Freigänge und engste Stellen

| Stelle | Luft | |
|---|---|---|
| Riemenrücken → Lippe der Nut | **1,46 mm** | siehe [20 Zähne](#der-riemen-in-der-nut--warum-20-zähne) |
| Zahnspitzen → Nutgrund | **1,36 mm** | |
| Motor → Joch, ganz innen | 1,0 mm | Anschlag des Spannwegs |
| Motor → Führungswand, je Seite | 1,0 mm | |
| Zentrierbund → Langloch, je Seite | 0,2 mm | führt quer |
| Ritzel → Platte | 1,0 mm | 23 mm Welle, siehe [Rev. 4](#rev-4-gemessene-motoren-2026-09-27) |
| M3-Kopf → Riemen | 6,0 mm | |
| Halter oben → obere Nutöffnung | 9,4 mm | die obere Nut bleibt frei |
| Ritzel oben → Oberkante der 2040 | 5,5 mm | nichts ragt nach oben heraus |
| Steg Bundschlitz → Motorlangloch | 4,3 mm | engster Steg |

## Kräfte und Steifigkeit

Der Riemen zieht das Ritzel mit 2 × 20 N zum Profil hin. Das nimmt das Joch
als Druck an der Stirnseite auf. Weil der Riemen 12,5 mm über der
Oberkante des Jochs zieht, will er den Halter über diese Kante kippen. Die
Schenkel halten unten an den M5 mit rund **67 N** Reibung dagegen. Die vier
M5 klemmen das Sechsfache davon, vorsichtig gerechnet mit 500 N je
Schraube auf PETG und μ = 0,2.

Unter dem Riemenzug kippt der Motor um **0,06 Grad**, das Ritzel weicht um
0,02 mm aus (Platte mit Führungswänden, PETG quer zur Schicht mit
1500 N/mm²). Das Motorgewicht biegt die Platte nicht messbar durch. Das
Haltemoment des Motors (0,45 Nm) halten die vier M3 über Reibung mit
zwölffacher Reserve.

## Verschraubung

| Verbindung | Teile | Hinweis |
|---|---|---|
| Halter → 2040 | **4× M5×12 + Scheibe + Nutenstein M5 (Nut 6)** | je Seite zwei in der unteren Nut; 4,8 mm ragen in die Nut, 3,0 mm Eingriff im Stein |
| NEMA 17 → Platte | **4× M3×10 + Scheibe DIN 125** | von oben durch die Langlöcher, 3,5 mm Eingriff (Gewindetiefe 4,5) |
| Ritzel → Motorwelle | Madenschrauben | Nabe unten, eine auf die Abflachung |

Für beide Seiten zusammen: 8× M5×12, 8 Scheiben M5, 8 Nutensteine, 8× M3×10,
8 Scheiben M3.

## Montage

1. Je Profilende **vier Hammermuttern M5** einsetzen, zwei in die **untere**
   Nut jeder Seitenfläche.
2. **Halter** von vorn über das Profilende schieben, bis das Joch an der
   Stirnseite anliegt. 4× M5×12 mit Scheibe, festziehen.
3. **Motor** von unten zwischen die Führungswände setzen, den Bund in das
   Langloch, ganz nach innen. Den Stecker zur Seite oder nach außen drehen,
   nicht zur 2060. 4× M3×10 mit Scheibe von oben, noch lose.
4. **Ritzel** mit der Nabe nach unten aufschieben, Oberkante bündig mit dem
   Wellenende, Madenschraube auf die Abflachung.
5. **Riemen** um das Ritzel legen, beide Trume in die oberen Nuten.
6. **Spannen** wie oben beschrieben, dann die M3 fest.
7. **Prüfen**, dass der Riemen gerade und ohne die Lippen zu berühren in
   beide Nuten läuft. Wenn nicht, die Ritzelhöhe nachstellen.
8. Dasselbe auf der anderen Seite.
9. **Drehrichtung:** Beide Motoren sind gleich eingebaut, die Y-Riemen
   liegen aber spiegelbildlich: Die Motoren müssen gegenläufig drehen. Am
   CNC Shield bekommt der zweite Y-Motor (A, Klon von Y) dasselbe
   DIR-Signal, deshalb an ihm **eine Spule tauschen**
   ([Zwei Y-Motoren](hardware-notizen.md#zwei-y-motoren)). Vor der ersten
   Fahrt von Hand prüfen, bevor das Portal an beiden Riemen hängt.

## Druck (PETG, Bambu Lab A1)

**Kopfüber drucken: die Oberseite (Z = 17,5) aufs Bett.** Platte, Joch,
Schenkel und Führungswände wachsen dann senkrecht aus der Platte: 16,5 mm
hoch auf 52,3 × 86,8 mm Grundfläche. Das braucht **keine Stützen**, nur die
vier waagerechten M5-Bohrungen (Ø5,5) überbrücken. Die Motorauflage (die
Plattenunterseite) liegt dann oben und wird plan. Anlage am Joch und
Innenseiten der Schenkel sind senkrechte Wände und damit maßhaltig. Eine
Fase von 0,4 mm an der Bettseite hält den Elefantenfuß heraus.

4 Wandlinien, ≥ 40 % Infill. **PETG**, weil der Motor warm wird: PLA
erweicht bei gut 55 °C, das erreicht ein NEMA 17 im Dauerbetrieb.
**Zweimal drucken**, links und rechts ist es dasselbe Teil.

## Keine Bohrlehre

Der Halter verbindet kein zweites Druckteil. Die 2040 wird nicht gebohrt,
die Nutensteine sitzen in den Nuten. Das NEMA-17-Lochbild (31 × 31) passt an
der Z-Achse schon in Konsole und Motoradapter, und die Langlöcher gleichen
längs ohnehin aus. Eine Lehre hätte hier nichts zu prüfen.

## Noch offen

1. **Winkel am vorderen 2060:** gerechnet mit 5 mm Luft zwischen
   Schenkelende und 2060. Die Winkel greifen in die obere Nut des 2060 und
   die untere Nut der 2040 (Angabe vom 2026-09-27) — dieselbe Nut, in der
   die Nutensteine des Halters sitzen. Sitzt einer davon **vor** dem 2060
   an der Seitenfläche, stößt er an den Schenkel: dann `wange_laenge`
   kürzen bzw. die Schrauben verlegen und prüfen.
2. **Nutmaße** `[w]`: Lippe 1,8 und Nutgrund 6,0 mm bestimmen, wo der
   Riemen in der Nut läuft. Bei anderem Profil `nut_lippe` und `nut_tiefe`
   anpassen und prüfen.
3. **Nutensteine** `[w]`: gerechnet mit 1,8 mm Lippe, 4 mm Gewinde und 6 mm
   Platz. Setzt die M5×12 hinten auf, eine Scheibe mehr unter den Kopf.
4. **Riemenlinie im Portal:** Der Riemen läuft in der rechten Nut hin und
   in der linken zurück (Angabe vom 2026-09-27), mit dem mittigen Ritzel also
   bei ±6,37 mm. Die Klemmen bleiben, wo Y-Wagen und Klemmtürme in
   `Portal.py` sie haben, 21,6 mm innen neben der Schienenmitte (Angabe vom
   2026-09-27). Die Wagen-Trume laufen deshalb schräg von der Klemme in die
   innere Nut (1,7° bis 19,3°, je nach Stellung), der Rücklauf gerade in der
   äußeren; das hintere Ritzel sitzt ebenfalls mittig zur 2040 (Angabe).
   Wo ein Trum durch die Nutöffnung in den Kanal läuft, bleiben dem Riemen
   0,1 mm je Seite. Weil die Trume schräg laufen, ist der Riemenweg in der
   Mitte am kürzesten und an den Schienenenden 1,3 bzw. 2,0 mm länger: Ein
   in der Mitte gespannter Riemen wird dort etwas gedehnt. Seit Portal
   Rev. 16 rechnet `Portal.py` das so; Zahlen in
   [portal-y-schlitten.md](portal-y-schlitten.md#y-riemen-und-klemmtürme).
5. **Portal-Prüfung:** Seit Portal Rev. 16 rechnet `portal_check.py` den
   Y-Weg vorn gegen diesen Halter. Der Toolhead fährt am vorderen
   Schienenende ab zc = +37 über ihn hinweg, mit dem Softlimit am vorderen
   2060 erreicht er ihn ohnehin nicht. Am Schienenende selbst (nur von Hand)
   endet der vordere Klemmturm 2,2 mm hinter dem inneren Schenkel, 2,9 mm
   über ihm und 1 mm weiter innen — berühren kann er ihn nicht
   ([portal-y-schlitten.md](portal-y-schlitten.md#y-weg-die-2060-und-die-y-motorhalter)).
6. **Endschalter** gehören nicht zum Halter: Der Y-Endschalter sitzt hinten
   rechts, ohne Auto-Squaring ([endschalter.md](endschalter.md)).
7. **Alte Teile:** Die Umlenkrollen (F625ZZ), der Motorriemen und die
   Edelstahlwellen aus Rev. 1/2 braucht der Y-Antrieb nicht mehr, ebenso
   den alten Y-Motorhalter von `Portal.py` (bis Rev. 15).

## Parametrik

Die Werte stehen in `MASSE` von `Portal.py` und landen als User-Parameter
im Dialog *Ändern → Parameter*; die des Halters beginnen mit `ymh_`. Die
Lagen rechnet `lage_y_motorhalter()` in Python: nach einer Änderung das
Portal-Skript neu laufen lassen und `tools/y_motorhalter_check.py` und
`tools/portal_check.py` ausführen. Bis Portal Rev. 15 hießen sie ohne
`ymh_`, Nutlage und Zähnezahl waren eigene Werte.

| Parameter | Wert | Wirkung |
|---|---|---|
| `rahmen_b` / `rahmen_h` | 20 / 40 mm | Profil; die Nuten liegen eine halbe Breite über der Unterkante (Nutensteine) und unter der Oberkante (Riemen) |
| `nut_lippe` / `nut_tiefe` | 1,8 / 6,0 mm `[w]` | wo der Riemen im Nutkanal läuft, Länge der M5 |
| `ritzel_teilkreis` | 12,73 mm | GT2 20 Z (Zähne = π · Teilkreis / `riemen_teilung`): Abstand der Trume, 40 mm je Umdrehung |
| `motor_welle_ist` | 23 mm (gemessen) | legt mit dem Ritzel die Höhe von Motor und Platte fest |
| `ymh_platte_dicke` | 6 mm | höchstens 7, sonst stößt das Ritzel an |
| `ymh_wange_laenge` | 30 mm | so weit reichen die Schenkel am Profil entlang; enden 5 mm vor dem vorderen 2060 (Winkel) |
| `ymh_schraube_y` / `ymh_schraube_abstand` | 8 / 14 mm | Lage der M5 hinter der Stirnseite (8 und 22 mm) |
| `ymh_joch_dicke` | 4 mm | Anschlag an der Stirnseite, schiebt den Motor nach außen |
| `ymh_spann_weg` | 8 mm | Weg des Motors; der Riemenweg ändert sich um das Doppelte |
| `motor_laenge` | 37 mm (gemessen) | nur Freiraum nach unten |
