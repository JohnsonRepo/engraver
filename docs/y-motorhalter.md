# Y-Motorhalter — Antrieb der Y-Achse

Erzeugt von `fusion/YMotorhalter/YMotorhalter.py` (ein Druckteil, Rev. 1).
Geprüft mit `python3 tools/y_motorhalter_check.py`, Skizze in
[y-antrieb.svg](y-antrieb.svg) (neu erzeugen mit
`python3 tools/y_antrieb_zeichnen.py`).

![Y-Antrieb](y-antrieb.svg)

## Was hier zusammenkommt

Der Antrieb der Y-Achse, wie du ihn beschrieben hast (2026-09-24):

* Die **hintere 2060-Traverse steht hochkant** (60 mm hoch).
* Jede Seite hat eine eigene **senkrechte Edelstahlwelle Ø5** in 625ZZ-Lagern,
  hinter der 2060 auf der Motorseite.
* Auf jeder Welle sitzen **zwei GT2-Ritzel**: das **obere** treibt den
  Y-Riemen des Wagens, das **untere** sitzt auf Höhe der **obersten Nut** der
  2060 und hängt am Motorriemen. Es lässt sich auf der Welle etwas
  verschieben.
* **Ein** geschlossener Motorriemen läuft um beide unteren Ritzel.

Der Halter bringt den NEMA 17 in die Mitte dieses Riemens. Er sitzt an der
Rückseite der 2060, befestigt mit vier M5-Nutensteinen. Die Lager der Wellen
gehören nicht dazu.

| Teil | Material | Funktion |
|---|---|---|
| **Y-Motorhalter** | PETG, ~85 g (gerechnet) | Anlageplatte an der 2060, Boden für den Motor, Block mit den Rollenachsen, Führungsrippen, Spannlasche |
| NEMA 17 + GT2-Ritzel 20 Z, Bohrung 5 | Kaufteil | steht auf dem Boden, Welle nach unten |
| 2 Umlenkrollen, je 2× F625ZZ | Kaufteil | legen den Riemen als Omega um das Motorritzel |
| Endlosriemen GT2, 6 mm | Kaufteil | Länge nach [Riemenlänge](#riemenlänge) |

## Warum zwei Umlenkrollen

Ein Motor mitten in einem gerade durchlaufenden Riemen treibt nichts an. Der
Riemen berührt sein Ritzel nur so weit, wie er aus der Linie gedrückt wird.
Bei 3 mm Versatz auf 250 mm Trumlänge sind das **1,4 Grad**, also weniger als
ein Zahn. Das Ritzel rutscht durch.

Deshalb lenken zwei glatte Rollen den hinteren Trum als **Omega** um das
Motorritzel:

* Die Rollen stehen genau so weit neben der Motorachse, dass die beiden
  Omega-Trume **parallel** ans Ritzel laufen. Das Ritzel ist damit
  **180 Grad** umschlungen, **10 Zähne** im Eingriff, und zwar in jeder
  Spannstellung.
* Gespannt wird, indem der Motor nach hinten rückt. Jeder Millimeter macht
  den Riemenweg **2 mm** länger.
* Die Rollen laufen auf dem glatten Riemenrücken: je zwei F625ZZ Rücken an
  Rücken, Flansche außen, dazwischen 8 mm Lauffläche für den 6-mm-Riemen.

Die Alternative wäre ein Motor an einem Ende, als dritte Ecke der
Riemenschleife neben einer Welle. Dann teilen sich Motorritzel und
Nachbarwelle eine halbe Umschlingung: je rund 90 Grad, 5 Zähne. Außerdem
säße der Motor asymmetrisch. Mit dem Omega bleiben beide Wellenritzel bei
180 Grad.

Die Rollen tragen keine Welle, sie gehören zum Motorantrieb. Damit bleibt es
bei deiner Vorgabe: **der Halter trägt nur den Motor**, die Wellen haben
eigene Lager.

## Drehrichtung — wichtig für die Y-Wagen

Ein Riemen kann nur **gleichsinnig** antreiben. Alle Ritzel, die er mit der
Zahnseite umschlingt, drehen in dieselbe Richtung: beide Wellen und der
Motor. Nur die Rollen auf dem Rücken drehen andersherum.

Für die Y-Riemen heißt das: dreht die linke Welle von oben gesehen gegen den
Uhrzeigersinn, fährt an beiden Y-Riemen der **rechte Trum** (vom Bediener
aus) nach hinten und der linke nach vorn. Damit die Wagen gemeinsam fahren,
müssen **beide am selben Trum** hängen, also beide rechts oder beide links.
Spiegelbildlich eingebaut (beide innen oder beide außen) fahren sie
**gegeneinander**, und das Portal verklemmt sofort.

> **Vor dem Festziehen prüfen:** Motorritzel von Hand drehen. Beide Wagen
> müssen in dieselbe Richtung laufen. Wenn nicht, einen der beiden Wagen
> an den anderen Trum seines Y-Riemens klemmen. Am Motor lässt sich das
> nicht lösen.

## Bezug und Koordinaten

**Y = 0 ist die Rückseite der 2060, Z = 0 ihre Oberkante, X = 0 die Mitte
des Halters.** Y zählt **nach hinten**, weg von der Maschine. Im Fusion-Modell
sind Y und Z getauscht wie im Toolhead (Modell-Z = Maschine Y).

### Y-Kette (ab Rückseite der 2060)

| Y | Ebene |
|---|---|
| −20,0 | Vorderseite der 2060 (Maschinenseite) |
| **0** | **Rückseite der 2060 = Anlagefläche** |
| +6,0 | Anlageplatte hinten |
| +13,6 | vorderer Trum (Wirklinie), 7,3 mm hinter der Anlageplatte |
| +20,0 | Wellenachsen — **angenommen**, nicht gemessen |
| +26,4 | hinterer Trum |
| +34,7 | Achsen der Umlenkrollen (X = ±14,74) |
| +40,2 | Block und Spannlasche hinten |
| +64,7 … +84,7 | Motorachse, ganz vorn … ganz hinten (Spannweg 20 mm) |
| +108,4 | Boden hinten |

### Z-Kette (ab Oberkante der 2060)

| Z | Ebene |
|---|---|
| +50 | Oberkante Motor (48er; ein 40er endet bei +42) |
| +22 | Oberkante Spannlasche |
| +17 | Spannschraube |
| +12 | Oberkante Block, Führungsrippen und Anlageplatte |
| **+2** | **Motorflansch = Oberseite Boden** |
| −4 | Unterseite Boden |
| −5,5 | Ritzel oben (1,5 mm unter dem Boden) |
| **−10** | **Riemenmitte = Höhe der obersten Nut** |
| −15 | Rollen unten |
| −21,5 / −22 | Ritzel unten / Ende der Motorwelle |
| −30, −50 | M5-Schrauben in der mittleren und unteren Nut |
| −58 | Anlageplatte unten (2060 endet bei −60) |

## Aufbau des Halters

**Anlageplatte.** 6 mm dick, 48,7 mm breit, von Z = −58 bis +12. Je zwei
M5 sitzen in der **mittleren und unteren Nut** (X = ±15). Die oberste Nut
bleibt frei, auf ihrer Höhe läuft der Riemen. Weil in jeder Nut zwei Steine
30 mm auseinander sitzen, steht der Halter von selbst waagerecht.

**Boden.** Er kragt 108 mm nach hinten aus. Der Motor steht **oben** darauf,
die Welle zeigt nach unten. Ritzel und Rollen hängen darunter in der
Riemenebene. Oben statt unten, weil die 2060 das unterste Profil ist: ein
hängender Motor (Welle nach oben) reichte bis Z = −70, also 10 mm unter die
Profilunterkante auf den Tisch. Hinter der Traverse ist oben dagegen frei.

Der Boden ist **6 mm** dick, mehr geht nicht: 24 mm Motorwelle = 6 mm Boden
+ 1,5 mm Luft + 16 mm Ritzel + 0,5 mm Rest. Der Zentrierbund des Motors
(Ø22 × 2) sitzt in einer 2,4 mm tiefen Tasche, die Welle geht durch ein
8 mm breites Langloch. Beide sind so lang wie der Spannweg.

**Führungsrippen.** Zwei Rippen fassen den Motor links und rechts mit
0,2 mm Luft und führen ihn beim Spannen gerade nach hinten. Zusammen mit dem
Boden bilden sie ein U-Profil. Das hält Motor und Rollen parallel (siehe
[Steifigkeit](#steifigkeit)).

**Block.** Er liegt vorn zwischen den Rippen, von der Anlageplatte bis
5,5 mm hinter die Rollenachsen. Zusammen mit dem Boden ist er 16 mm dick und
trägt die beiden Rollenachsen: M5×40 von oben mit Scheibe, unter dem Boden
Scheibe, 2× F625ZZ, Scheibe und Sicherungsmutter. Die Scheibe zwischen Boden
und Rolle liegt nur am Innenring an. Der Flansch der Rolle bleibt 1 mm unter
dem Boden.

**Spannlasche.** Sie sitzt oben auf dem Block, 12 mm breit, und hat hinten
einen **Messing-Einsatz M3** (Ø4,6 × 7, die vorhandenen). Die Spannschraube
**M3×35** geht von vorn hindurch und drückt mit der Spitze auf die
Vorderseite des Motors. Den Einsatz von der Motorseite einschmelzen: dann
drückt die Riemenkraft ihn tiefer in die Bohrung und nicht heraus. Der Kopf
liegt über dem Block und ist mit dem Inbus von oben erreichbar. Die
Vorderseite der Lasche fällt unter 45 Grad ab, damit sie ohne Stützen
druckt.

**Unter dem Boden ist alles offen.** Der vordere Trum läuft zwischen
Anlageplatte und Rollen durch, 7,3 mm hinter der Platte und 3 mm unter dem
Boden. Der Riemen lässt sich von unten einlegen.

## Riemenlänge

Der Motorriemen ist **endlos** (geschlossen, GT2, 6 mm breit). Ein offener
Riemen mit Klemme ginge nicht: die Klemme müsste über den ganzen Y-Weg auf
einem freien Trum bleiben, und in der Mitte liegt der Halter im Weg.

**L = 2 · S + 56,8 + 2 · Ω**

* **S** ist der Abstand der beiden Wellen. **Er ist noch nicht gemessen**, im
  Skript stehen 500 mm.
* **Ω** ist die Tiefe des Omegas, von den Rollenachsen zur Motorachse:
  **30 mm** mit dem Motor ganz vorn, **50 mm** ganz hinten.
* 56,8 = zwei halbe Umschlingungen an den Wellen (40,0) plus der Rest um
  Rollen und Motorritzel. Das Prüfwerkzeug rechnet die Formel gegen die
  Summe der Einzelstücke nach.

| S | passender Riemen |
|---|---|
| 400 mm | 917 … 957 mm |
| 450 mm | 1017 … 1057 mm |
| **500 mm** | **1117 … 1157 mm** |
| 550 mm | 1217 … 1257 mm |
| 600 mm | 1317 … 1357 mm |
| 650 mm | 1417 … 1457 mm |

Das Fenster ist **40 mm** breit. Also: S von Wellenachse zu Wellenachse
messen, dann einen Riemen suchen, der hineinpasst, am besten in die Mitte.
Findest du keinen, gibt es zwei Stellschrauben im Skript:

* `omega_min`: größer für einen **längeren** Riemen (die Langlöcher
  wandern nach hinten), kleiner für einen kürzeren, aber nicht unter
  29,0 mm, sonst laufen die vorderen Motorschrauben in die Rollenflansche.
* `spann_weg` größer: ein breiteres Fenster, aber ein längerer Boden.

## Spannen

1. Motor ganz vorn, Riemen aufgelegt, die vier Motorschrauben lose.
2. Spannschraube eindrehen, sie schiebt den Motor nach hinten.
3. Richtwert **~20 N Vorspannung**. Nachprüfen am vorderen Trum, der frei
   zwischen den Wellen läuft:
   * **Frequenz:** anzupfen, mit einer Stimmgeräte-App messen. Bei 20 N und
     S = 500 mm sind es **~50 Hz** (allgemein f = 1/(2·S) · √(T/μ), μ ≈ 8 g/m).
   * **Durchhang:** 100 g (1 N) in der Mitte drücken ihn **~6 mm** durch
     (allgemein S/80 bei 20 N).
4. Die vier Motorschrauben festziehen. Die Spannschraube bleibt als Anschlag
   stehen: sie hält den Motor, auch wenn das PETG unter den Schrauben mit der
   Zeit nachgibt.
5. Nach den ersten Betriebsstunden nachhören, ob die Frequenz gleich
   geblieben ist.

Die Vorspannung muss nicht hoch sein. Der Motorriemen überträgt nur, was die
Y-Wagen brauchen (grob 10 N beim Beschleunigen des Portals). Zu stramm
belastet er nur die Lager der Wellen und das Motorlager.

## Die Wellenlage ist nicht gemessen — was der Halter verträgt

Die Rollen sitzen so, dass der hintere Trum bei `welle_y` = 20 mm gerade
anläuft. Stehen die Wellen woanders, läuft er leicht schräg an. Das ist
harmlos. Enger wird es am vorderen Trum, der zwischen Anlageplatte und
Rollenflanschen durchmuss:

| welle_y | vorderer Trum vor der Platte | vor den Rollen | hinterer Trum |
|---|---|---|---|
| 12 | **−0,7** ✗ | 19,1 | −1,9° |
| 14 | 1,3 | 17,1 | −1,5° |
| 20 (gebaut) | 7,3 | 11,1 | 0° |
| 25 | 12,3 | 6,1 | +1,2° |
| 30 | 17,3 | 1,1 | +2,4° |

**Ohne neuen Lauf passt der Halter für Wellen 14 bis 30 mm hinter der 2060.**
Außerhalb davon `welle_y` eintragen, das Skript neu laufen lassen und
`tools/y_motorhalter_check.py` ausführen.

## Freigänge und engste Stellen

| Stelle | Luft | |
|---|---|---|
| vordere Motorschraube (Kopf + Scheibe unter dem Boden) → Rollenflansch, Motor ganz vorn | **2,0 mm** | bestimmt `omega_min` |
| Motor → Führungsrippe, je Seite | 0,2 mm | gewollt: führt beim Spannen |
| Motorritzel → Unterseite Boden | 1,5 mm | beim Aufschieben einstellen |
| Riemen → Unterseite Boden | 3,0 mm | |
| vorderer Trum → Anlageplatte | 7,3 mm | siehe Wellenlage |
| Omega-Trum → vordere Motorschraube | 5,3 mm | seitlich, in jeder Stellung |
| Motor ganz vorn → Spannlasche | 3,35 mm | |
| Steg Motorlangloch → Bundtasche | 2,6 mm | engster Materialsteg |
| Wand hinter der Rollenachse | 2,75 mm | |

## Steifigkeit

Der Riemen zieht Rollen und Motor mit rund 2 × 20 N zueinander. Er greift
in der Riemenebene an, 11 mm unter der Schwerachse von Boden und Rippen. Das
biegt den Boden zwischen den Rollen und dem Motor. Mit dem U-Profil kippen
Rollen- und Motorachse gegeneinander um höchstens **0,20 Grad** (Motor ganz
hinten, PETG quer zur Schicht mit 1500 N/mm² gerechnet). Ohne die Rippen
wären es 1,1 Grad. Genau deshalb laufen sie über die ganze Länge.

Das Motorgewicht (0,35 kg auf 79 mm Hebel, 0,27 Nm) biegt den Boden am
Motor um 0,02 mm durch. Die Anlageplatte klemmen vier M5, das trägt das
leicht.

## Verschraubung

| Verbindung | Teile | Hinweis |
|---|---|---|
| Halter → 2060 | **4× M5×12 + Scheibe + Nutenstein M5 (Nut 6)** | mittlere und untere Nut; 5 mm ragen in die Nut, 3,2 mm Eingriff im Stein |
| Umlenkrollen | **2× M5×40**, 6× Scheibe M5, 2× Sicherungsmutter M5, **4× F625ZZ** | von oben durch Block und Boden; Innenringe klemmen, Rolle muss frei laufen |
| NEMA 17 → Boden | **4× M3×10 + Scheibe DIN 125** | von unten durch die Langlöcher, 3,5 mm Eingriff (Gewindetiefe 4,5) |
| Spannschraube | **1× M3×35 + 1× Messing-Einsatz M3** | Einsatz von der Motorseite einschmelzen |
| Ritzel → Motorwelle | Madenschraube | Nabe nach unten, Madenschraube auf die Abflachung |

## Montage

1. **Messing-Einsatz** in die Spannlasche einschmelzen, von der Motorseite.
2. **Vier Hammermuttern M5** in die mittlere und untere Nut der hinteren
   2060 (Rückseite). Halter mittig zwischen den Wellen ansetzen, 4× M5×12
   mit Scheibe, festziehen.
3. **Umlenkrollen:** M5×40 mit Scheibe von oben durch Block und Boden.
   Unten Scheibe, zwei F625ZZ mit den Flanschen nach außen, Scheibe,
   Sicherungsmutter. Nur so fest, dass die Innenringe klemmen und die Rolle
   frei dreht.
4. **Spannschraube** M3×35 von vorn in den Einsatz, ganz zurückgedreht.
5. **Motor** zwischen die Rippen setzen, Welle nach unten, Bund in die
   Tasche, ganz nach vorn schieben. 4× M3×10 mit Scheibe von unten, lose.
6. **Ritzel** von unten auf die Motorwelle, Nabe nach unten, **1,5 mm Luft**
   zum Boden. Ein 1,5er Inbus dazwischen dient als Fühlerlehre.
   Madenschraube auf die Abflachung.
7. **Riemen** um die unteren Ritzel beider Wellen legen. Den vorderen Trum
   von unten hinter der Anlageplatte durchführen, den hinteren Trum zwischen
   den Rollen nach hinten ums Motorritzel ziehen.
8. **Höhe der Wellenritzel** so nachstellen, dass der Riemen mittig zwischen
   den Rollenflanschen läuft (Riemenmitte = Mitte der obersten Nut).
9. **Drehrichtung prüfen**, siehe [oben](#drehrichtung--wichtig-für-die-y-wagen).
10. **Spannen** wie oben beschrieben, dann die Motorschrauben fest.

## Druck (PETG, Bambu Lab A1)

**Anlagefläche aufs Bett**, Aufbaurichtung = Maschine Y. Boden, Block und
Rippen wachsen dann als Wand nach oben, 108 mm hoch, 48,7 × 80 mm
Grundfläche. Die Lasche hat eine 45-Grad-Unterseite: **keine Stützen**. Die
M5-Bohrungen und die Spannschraube stehen senkrecht und werden rund. Die
Anlagefläche kommt vom Bett und ist damit plan, wichtig für die Nutensteine.
Eine Fase von 0,4 mm hält den Elefantenfuß heraus.

Die Rollenachsen und die Motorlanglöcher liegen in dieser Lage waagerecht.
Das sind Durchgangsbohrungen, ein leichtes Durchhängen oben stört dort
nicht. Genauso wurde die Motorkonsole an der Trägerplatte gedruckt.

4 Wandlinien, ≥ 40 % Infill. **PETG**, weil der Motor warm wird: PLA
erweicht bei gut 55 °C, das erreicht ein NEMA 17 im Dauerbetrieb.

## Keine Bohrlehre

Der Halter verbindet kein zweites Druckteil. Die 2060 wird nicht gebohrt,
die Nutensteine sitzen in den Nuten. Das NEMA-17-Lochbild (31 × 31) passt an
der Z-Achse schon in Konsole und Motoradapter. Die Langlöcher gleichen
längs ohnehin aus. Eine Lehre hätte hier nichts zu prüfen, wie beim
Mutternwinkel am Toolhead.

## Noch offen

1. **Wellenabstand S** messen (Achse zu Achse): davon hängt die Riemenlänge
   ab.
2. **Wellen hinter der 2060** (`welle_y`) messen: ohne neuen Lauf passen
   14 bis 30 mm.
3. **Welcher Trum trägt die Wagen?** Beide müssen am selben Trum hängen,
   siehe [Drehrichtung](#drehrichtung--wichtig-für-die-y-wagen).
4. **Freiraum hinter der Traverse:** Motor bis Z = +50, Halter und Motor
   bis Y = 108. Portal und Toolhead dürfen in der hintersten Stellung nicht
   hineinfahren.
5. **Motorlänge:** 48 mm angenommen, nur für den Freiraum.
6. **Nutensteine:** gerechnet mit 1,8 mm Lippe, 4 mm Gewinde und 6 mm Platz
   in der Nut `[w]`. Setzt die M5×12 hinten auf, eine Scheibe mehr unter
   den Kopf.

## Parametrik

Alle Werte aus `MASSE` landen als User-Parameter im Dialog *Ändern →
Parameter*. Die Zähnezahlen sind einheitenlos. Die Lagen rechnet `lage()`
in Python: nach einer Änderung das Skript neu laufen lassen und
`tools/y_motorhalter_check.py` ausführen.

| Parameter | Wert | Wirkung |
|---|---|---|
| `welle_y` | 20 mm `[?]` | Wellen hinter der 2060, legt die Rollen fest |
| `welle_abstand` | 500 mm `[?]` | Abstand der Wellen, nur für die Riemenlänge |
| `riemen_z` | −10 mm | Riemenebene = oberste Nut |
| `omega_min` | 30 mm | Omega-Tiefe mit dem Motor ganz vorn (Minimum 29,0) |
| `spann_weg` | 20 mm | Weg des Motors, Riemenfenster = 2 × spann_weg |
| `boden_dicke` | 6 mm | höchstens 6,5, sonst reicht die Motorwelle nicht durchs Ritzel |
| `block_hoehe` | 10 mm | Höhe von Block und Führungsrippen über dem Boden |
| `schraube_x` | 15 mm | Abstand der M5 von der Mitte |
| `ritzel_z_motor` / `ritzel_z_welle` | 20 / 20 | Zähnezahlen (1:1, 40 mm je Umdrehung) |
| `motor_laenge` | 48 mm | nur Freiraum |
