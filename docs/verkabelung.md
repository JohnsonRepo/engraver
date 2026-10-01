# Verkabelung — Strom, Motoren, Lichtschranken, Laser

Die ganze Verdrahtung, vom Steckernetzteil bis zum Laser, Schritt für
Schritt. Jede Leitung hat eine Nummer (W1 … W17). Sie steht an beiden Enden
auf dem Kabel, im [Anschlussplan](elektronik-anschluss.svg) und in den
Tabellen hier.

Die Kabelliste steht einmal in `tools/verkabelung.py`. Daraus entstehen die
Tabellen dieser Anleitung (`python3 tools/verkabelung.py`, schreibt nur
zwischen den Markierungen) und der Anschlussplan
(`python3 tools/anschluss_zeichnen.py`). `python3 tools/elektronik_check.py`
prüft in Abschnitt 15 die Netze (kein Kurzschluss, der Not-Aus trennt alle
24 V), Signale und Pins, Kontakte, Klemmen und Längen und ob die Tabellen
hier aktuell sind. Wo Gehäuse, Kabelwege und Ketten liegen, steht
in [elektronik.md](elektronik.md). Pins, Treiber und Jumper im Einzelnen
stehen in [hardware-notizen.md](hardware-notizen.md#elektronik).

![Anschlussplan](elektronik-anschluss.svg)

## Vorab: sechs Regeln

1. **Nichts unter Spannung an- oder abstecken**, vor allem keine Motoren.
   Ein Motorstecker, der unter Strom abgeht, kostet den Treiber.
2. **Die 24 V messen, bevor das Shield dran ist.** Verpolt sind die
   Treiber hin.
3. **Den Wandler ohne Laser auf 12,0 V stellen.**
4. **Einschalten: erst USB, dann 24 V. Ausschalten umgekehrt.** Dann läuft
   GRBL schon und hält den Laser aus, wenn er Strom bekommt.
5. **Beim ersten Lasertest eine Schutzbrille für 450 nm tragen**, auch bei
   wenig Leistung.
6. **Jede Leitung an beiden Enden mit ihrer W-Nummer beschriften.**

## Übersicht

Drei Spannungen, eine gemeinsame Masse:

| Spannung | kommt von | versorgt | geschaltet |
|---|---|---|---|
| **+24 V** | Steckernetzteil 24 V / 3 A über Einbaubuchse, Schalter und Not-Aus | Shield (vier Treiber), Wandler, Lüfter | Schalter und Not-Aus |
| **+12 V** | Wandler 24 → 12 V | nur den Laser | mit den 24 V |
| **+5 V** | Uno über USB, Stift 5V am Shield | die drei Lichtschranken | USB |
| **GND** | alles verbunden, Stern an der Wago GND | | |

Signale: Die Lichtschranken X, Y und Z melden an D9, D10 und D12. Der Laser
bekommt seine Leistung als PWM von D11. Ein Spannungsteiler an den 24 V
meldet an A0 (Abort), wenn sie fehlen.

Kein 230 V in der Maschine: Das Steckernetzteil liefert 24 V, am Rahmen
muss nichts geerdet werden. Eine Sicherung braucht es nicht, das Netzteil
begrenzt den Strom selbst.

## Leitungen

<!-- tabelle:leitungen -->
| Nr | Leitung | Litze | Weg | Länge | kaufen | Kette |
|---|---|---|---|---|---|---|
| W1 | **Eingang** | 0,75 mm² (AWG 18) | im Kasten | ≈ 0,15 m je Ader | Rolle | — |
| W2 | **Not-Aus-Kreis** — beide Adern führen +24 V: an beiden Enden rot markieren; NO bleibt frei | 2 × 0,75 mm² (AWG 18) | vorn raus, Kanal, Rückseite hinteres 2060, untere Nut außen am rechten 2040 nach vorn, obere Nut vorn am 2060 zum Gehäuse | 1,01 m | **1,5 m** | — |
| W3 | **Shield** | 0,75 mm² (AWG 18) | im Kasten | ≈ 0,15 m je Ader | Rolle | — |
| W4 | **Wandler-Eingang** | 0,75 mm² (AWG 18) | im Kasten | ≈ 0,15 m je Ader | Rolle | — |
| W5 | **Lüfter 24 V** — Litze dünner als 0,14 mm²: abisoliert doppelt legen | Litze des Lüfters | im Kasten, durch die Öffnung im Deckel | — | — | — |
| W6 | **5 V für die Lichtschranken** | 0,25 mm² (AWG 24) | im Kasten | ≈ 0,15 m je Ader | Rolle | — |
| W7 | **Laser** | 3 Silikonlitzen 0,34 mm² (AWG 22) | links raus, untere Nut außen am linken 2040, hinten in die Y-Kette, hinter dem Schlitten in die obere Nut des Rohrs, am Kabelflügel hoch in die X-Kette, Trägerplatte | 1,64 m | **2 m** | Y + X |
| W8 | **Pull-down 10 kΩ** — hält den Laser aus, solange der Uno startet oder ohne USB ist | Widerstand | auf dem Shield | — | — | — |
| W9 | **Lichtschranke X** | 3 Silikonlitzen 0,25 mm² (AWG 24) | links raus, untere Nut außen am linken 2040, Y-Kette, hinter dem Schlitten über das Rohr nach vorn zum Halter X | 0,85 m | **1 m** | Y |
| W10 | **Lichtschranke Y** | 3 × 0,25 mm² (AWG 24) | vorn raus, Kanal, Rückseite hinteres 2060, untere Nut außen am rechten 2040 nach hinten | 0,49 m | **1 m** | — |
| W11 | **Lichtschranke Z** | 3 Silikonlitzen 0,25 mm² (AWG 24) | wie W7 bis zur Trägerplatte, dann zum Halter am Toolhead | 1,49 m | **2 m** | Y + X |
| W12 | **X-Motor** — in der Kette nur die losen Adern, ohne Schlauch | 4 × 0,2 mm² (AWG 24) | links raus, untere Nut außen am linken 2040, Y-Kette, hinter dem Motorhalter hoch zum Motor | 0,82 m | mitgeliefert (1 m) | Y |
| W13 | **Y-Motor links** | 4 × 0,2 mm² (AWG 24) | links raus, untere Nut außen am linken 2040 nach vorn; an den drei Trägern der Wanne Y kurz aus der Nut, über ihre Wand | 0,71 m | mitgeliefert (1 m) | — |
| W14 | **Y-Motor rechts** — Spule A getauscht: dreht gegen den linken | 4 × 0,2 mm² (AWG 24) | vorn raus, Kanal, Rückseite hinteres 2060, untere Nut außen am rechten 2040 nach vorn | 0,98 m | **1,5 m**, fertig | — |
| W15 | **Z-Motor** — in den Ketten nur die losen Adern, ohne Schlauch | 4 × 0,2 mm² (AWG 24) | wie W7 bis zur Trägerplatte, dann zum Motor oben | 1,56 m | **2 m**, fertig | Y + X |
| W16 | **24-V-Wächter an Abort** — fehlen die 24 V (Not-Aus, Schalter, Netzteil), bricht GRBL ab | Widerstand | im Kasten | — | — | — |
| W17 | **USB** | USB-Kabel A–B | hinten raus zum PC | — | vorhanden | — |
<!-- /tabelle:leitungen -->

„Länge“ ist der Weg wie in [elektronik-platz.svg](elektronik-platz.svg)
gezeichnet, „kaufen“ dieser Weg plus 15 % und aufgerundet. Was übrig ist,
bleibt als Schlaufe beim Gehäuse. Die Motorfarben sind die übliche Belegung
von Stepperonline `[w]`: A+ schwarz, A− grün, B+ rot, B− blau. Vor dem
Anschließen mit dem Ohmmeter prüfen
([Motoren](#6-motoren-w12w15)).

## Anschlussliste

<!-- tabelle:anschluesse -->
| Nr | Ader | Farbe | von | an |
|---|---|---|---|---|
| W1 | +24 V | rot | Einbaubuchse, Mittelstift (+) | Schalter, Kontakt 1 |
|  | GND | schwarz | Einbaubuchse, Hülse (−) | Wago GND |
| W2 | +24 V hin | Ader 1 | Schalter, Kontakt 2 | Not-Aus, C |
|  | +24 V zurück | Ader 2 | Not-Aus, NC | Wago +24 V |
| W3 | +24 V | rot | Wago +24 V | Shield, Schraubklemme + |
|  | GND | schwarz | Wago GND | Shield, Schraubklemme − |
| W4 | +24 V | rot | Wago +24 V | Wandler IN+ |
|  | GND | schwarz | Wago GND | Wandler IN− |
| W5 | +24 V | rot | Lüfter, rote Litze | Wago +24 V |
|  | GND | schwarz | Lüfter, schwarze Litze | Wago GND |
| W6 | +5 V | rot | Shield, Stift 5V | Wago +5 V |
| W7 | +12 V | rot | Wandler OUT+ | Laser, XH rechts: +12 V |
|  | GND | schwarz | Wandler OUT− | Laser, XH Mitte: GND |
|  | PWM | weiß | Shield Z+ (D11), Signalstift | Laser, XH links: PWM |
| W8 | 10 kΩ | — | Shield Z− (D11), Signalstift | Shield Z−, GND-Stift |
| W9 | +5 V | rot | Wago +5 V | Lichtschranke X, VCC |
|  | GND | schwarz | Wago GND | Lichtschranke X, GND |
|  | Signal | gelb | Shield X− (D9), Signalstift | Lichtschranke X, D0 |
| W10 | +5 V | rot | Wago +5 V | Lichtschranke Y, VCC |
|  | GND | schwarz | Wago GND | Lichtschranke Y, GND |
|  | Signal | gelb | Shield Y+ (D10), Signalstift | Lichtschranke Y, D0 |
| W11 | +5 V | rot | Wago +5 V | Lichtschranke Z, VCC |
|  | GND | schwarz | Wago GND | Lichtschranke Z, GND |
|  | Signal | gelb | Shield SpnEn (D12) | Lichtschranke Z, D0 |
| W12 | Spule A | schwarz · grün | Shield Motor X, 2B · 2A | X-Motor, Spule A: A+ · A− |
|  | Spule B | rot · blau | Shield Motor X, 1A · 1B | X-Motor, Spule B: B+ · B− |
| W13 | Spule A | schwarz · grün | Shield Motor Y, 2B · 2A | Y-Motor links, Spule A: A+ · A− |
|  | Spule B | rot · blau | Shield Motor Y, 1A · 1B | Y-Motor links, Spule B: B+ · B− |
| W14 | Spule A, getauscht | grün · schwarz | Shield Motor A, 2B · 2A | Y-Motor rechts, Spule A: A− · A+ |
|  | Spule B | rot · blau | Shield Motor A, 1A · 1B | Y-Motor rechts, Spule B: B+ · B− |
| W15 | Spule A | schwarz · grün | Shield Motor Z, 2B · 2A | Z-Motor, Spule A: A+ · A− |
|  | Spule B | rot · blau | Shield Motor Z, 1A · 1B | Z-Motor, Spule B: B+ · B− |
| W16 | R1 22 kΩ | — | Wago +24 V | Shield Abort (A0) |
|  | R2 4,7 kΩ ∥ 100 nF | — | Shield Abort (A0) | Wago GND |
| W17 | USB | — | Uno, USB-B | PC |
<!-- /tabelle:anschluesse -->

## Klemmen: Wago und Shield

<!-- tabelle:wago -->
| Klemme | Typ | belegt | frei | angeschlossen |
|---|---|---|---|---|
| **Wago +24 V** | 221-415 | 5 von 5 | 0 | W2 Not-Aus, NC · W3 Shield, Schraubklemme + · W4 Wandler IN+ · W5 Lüfter, rote Litze · W16 Shield Abort (A0) |
| **Wago GND** | 221-420 | 8 von 10 | 2 (einer davon für OUT− eines isolierten Wandlers) | W1 Einbaubuchse, Hülse (−) · W3 Shield, Schraubklemme − · W4 Wandler IN− · W5 Lüfter, schwarze Litze · W9 Lichtschranke X, GND · W10 Lichtschranke Y, GND · W11 Lichtschranke Z, GND · W16 Shield Abort (A0) |
| **Wago +5 V** | 221-420 | 4 von 10 | 6 | W6 Shield, Stift 5V · W9 Lichtschranke X, VCC · W10 Lichtschranke Y, VCC · W11 Lichtschranke Z, VCC |
<!-- /tabelle:wago -->

<!-- tabelle:shield -->
| Stift | Uno-Pin | Aufgabe | angeschlossen |
|---|---|---|---|
| Schraubklemme + | — | 24 V für die Treiber (12–36 V) | W3 → Wago +24 V |
| Schraubklemme − | — | GND | W3 → Wago GND |
| Stift 5V | 5 V | Versorgung der Lichtschranken (vom USB des Uno) | W6 → Wago +5 V |
| X− (D9), Signalstift | D9 | Endschalter X (X+ ist derselbe Pin) | W9 → Lichtschranke X, D0 |
| Y+ (D10), Signalstift | D10 | Endschalter Y (Y− ist derselbe Pin) | W10 → Lichtschranke Y, D0 |
| SpnEn (D12) | D12 | Endschalter Z — GRBL 1.1 legt ihn auf D12 | W11 → Lichtschranke Z, D0 |
| Z+ (D11), Signalstift | D11 | Laser-PWM — kein Endschalter | W7 → Laser, XH links: PWM |
| Z− (D11), Signalstift | D11 | Pull-down 10 kΩ zum GND-Stift daneben | W8 → Shield Z−, GND-Stift |
| Abort (A0) | A0 | 24-V-Wächter: ohne 24 V bricht GRBL ab | W16 → Wago +24 V · W16 → Wago GND |
| Motor X, Y, Z, A | — | 2B · 2A · 1A · 1B je Treiber; A klont Y (Jumper) | W12 · W13 · W15 · W14 |
<!-- /tabelle:shield -->

* Auf dem Shield liegen **X+ und X− auf demselben Pin** (D9), ebenso Y+/Y−
  (D10) und Z+/Z− (D11). Stecken nur dort, wo die Tabelle es sagt: An
  Z+/Z− liegt die Laser-PWM, das ist ein Ausgang.
* Die Masse der Lichtschranken geht an die Wago GND, nicht an einen
  GND-Stift am Shield. So muss niemand GND-Stifte suchen, und neben SpnEn
  gibt es womöglich keinen.
* **Jumper:** MS1 + MS2 an allen vier Treibern (1/16), MS3 frei. A klont
  Y: A.STEP ↔ Y.STEP und A.DIR ↔ Y.DIR. Die Jumper **D12/D13 für A nicht
  stecken**, denn D12 ist der Z-Endschalter. EN/GND bleibt offen, GRBL
  schaltet die Treiber über D8.
* **Treiber** mit dem EN-Pin zum EN-Aufdruck stecken.

## Material und Werkzeug

<!-- tabelle:material -->
| Menge | Teil | für |
|---|---|---|
| 0,5 m | Einzelader 0,75 mm² (AWG 18), rot | W1 0,15 m · W3 0,15 m · W4 0,15 m |
| 0,5 m | Einzelader 0,75 mm² (AWG 18), schwarz | W1 0,15 m · W3 0,15 m · W4 0,15 m |
| 1,5 m | 2 × 0,75 mm² (AWG 18) | W2 1,5 m |
| 1,5 m | 3 × 0,25 mm² (AWG 24) | W6 0,15 m · W10 1 m |
| 2 m | Silikonlitze 0,34 mm² (AWG 22), rot | W7 2 m |
| 2 m | Silikonlitze 0,34 mm² (AWG 22), schwarz | W7 2 m |
| 2 m | Silikonlitze 0,34 mm² (AWG 22), weiß | W7 2 m |
| 3 m | Silikonlitze 0,25 mm² (AWG 24), rot | W9 1 m · W11 2 m |
| 3 m | Silikonlitze 0,25 mm² (AWG 24), schwarz | W9 1 m · W11 2 m |
| 3 m | Silikonlitze 0,25 mm² (AWG 24), gelb | W9 1 m · W11 2 m |
| 1 + 1 | Motorkabel 1,5 m und 2 m, 4 × AWG 24, PH-Stecker zum Motor, Dupont 4-polig zum Shield; für W15 lose Adern ohne Mantel (läuft durch beide Ketten) | W14, W15 (W12, W13: die mitgelieferten 1-m-Kabel) |
| 17 + Reserve | Dupont-Crimpkontakte (Buchse) | Shield, Lichtschranken, W8, W16 |
| 6 · 1 · 3 | Dupont-Gehäuse 1-, 2- und 3-polig | Shield, Pull-down, Lichtschranken |
| 1 + 3 | XH2.54-Gehäuse 3-polig + Crimpkontakte | Laser |
| 2 | Aderendhülse 0,34 mm² | Schraubklemmen |
| 4 | Aderendhülse 0,75 mm² | Schraubklemmen |
| 1 | Widerstand 10 kΩ, ¼ W | W8 |
| 1 + 1 + 1 | Widerstand 22 kΩ und 4,7 kΩ, ¼ W; Kondensator 100 nF | W16 |
| — | Not-Aus-Pilztaster 16 mm, Wechsler C/NO/NC, 3 A / 250 V (vorhanden), Gehäuse aus [NotAus.py](notaus.md) | W2 |
| — | Schrumpfschlauch 2–6 mm, Kabelbinder, Beschriftung (W-Nummer an beiden Enden) | alle |
<!-- /tabelle:material -->

* **Litze:** in den Ketten nur Einzellitzen aus Silikon, keine
  Mantelleitungen: Die gedruckten Ketten biegen mit R 32
  ([energiekette.md](energiekette.md#litzen-in-der-kette)). Für die
  Signale 0,25 mm²: Das hält sicher in der
  Wago (ab 0,14 mm²), und in den Dupont-Kontakt passen bis 0,34 mm². Ist
  schon Litze mit 0,14 mm² oder AWG 26 (0,13 mm²) da, geht sie auch: in
  der Wago das abisolierte Ende doppelt legen.
* **Werkzeug:** Crimpzange für Dupont und XH (2,54 mm, z. B. SN-28B),
  Zange für Aderendhülsen, Abisolierzange, Lötkolben, Multimeter mit
  Durchgangsprüfer, Schrumpfschlauch.
* **Wago 221:** 11 mm abisolieren, Hebel auf, Litze bis zum Anschlag, Hebel
  zu. Ohne Aderendhülse.
* **Schraubklemmen** (Shield, Wandler): immer mit Aderendhülse.
  Verzinnte Litze gibt in der Klemme mit der Zeit nach.
* **Dupont und XH:** 2 mm abisolieren, crimpen, an jedem Kontakt ziehen.
  Die Kontakte rasten im Gehäuse hörbar ein.

## Schritt für Schritt

Zuerst alles im Gehäuse, dann nach außen zur Maschine. Die Prüfungen der
[Inbetriebnahme](#inbetriebnahme) gehören jeweils dazwischen.

### 1. Vorbereiten

* Die Leitungen nach der Tabelle ablängen und an beiden Enden mit der
  W-Nummer beschriften.
* Einbaubuchse und Schalter hinten ins Gehäuse setzen (Mutter innen,
  Schalter rastet ein), die Wago-Klemmen mit Klebeband auf ihren Platz:
  von links **+5 V**, **GND**, **+24 V**.

### 2. 24 V: Buchse, Schalter, Not-Aus (W1, W2)

1. **Einbaubuchse:** Mit dem Durchgangsprüfer die Lötfahne des
   Mittelstifts suchen. Dann das Netzteil einstecken und messen: Am
   Mittelstift liegen **+24 V** gegen die Hülse (bei diesen Netzteilen
   üblich `[w]`, trotzdem messen). Hat die Buchse eine dritte Fahne
   (Schaltkontakt), bleibt sie frei.
2. **W1:** rot von der Mittelfahne an Kontakt 1 des Schalters, schwarz von
   der Hülse an die **Wago GND**. Anlöten, Schrumpfschlauch darüber.
3. **W2** zum Not-Aus nach vorn. Er hat einen **Wechsler** mit drei
   Lötfahnen, C, NO und NC `[v]` (Bild). Ader 1 kommt von Kontakt 2 des
   Schalters an **C**, Ader 2 geht von **NC** zurück an die **Wago
   +24 V**. Beide Adern führen +24 V, deshalb an beiden Enden rot
   markieren. **NO bleibt frei:** Beim Drücken liegt dort C, also +24 V.
   Anlöten, Schrumpfschlauch über jede Fahne. Der Not-Aus sitzt in seinem
   Gehäuse vorn am vorderen 2060 ([notaus.md](notaus.md)); W2 kommt von
   rechts in der oberen Nut des 2060.

Dann [Prüfung A und B](#a-ohne-strom).

### 3. Shield, Wandler, Lüfter (W3–W5)

1. **W3:** Wago +24 V → Schraubklemme **+** des Shields, Wago GND →
   Schraubklemme **−**. Die Polung steht neben der Klemme. **Nicht
   vertauschen.**
2. **W4:** Wago +24 V → **IN+** des Wandlers, Wago GND → **IN−**.
3. **W5:** Die Litzen des Lüfters in die Wagos, rot an +24 V, schwarz an
   GND. Ist die Litze dünner als 0,14 mm², das abisolierte Ende doppelt
   legen. Der Lüfter bläst nach unten auf die Treiber (Pfeil am Rahmen).
4. **Masse des Wandlers:** Durchgang zwischen IN− und OUT− prüfen. Die
   üblichen Wandler haben eine gemeinsame Masse. Ohne Durchgang eine Brücke
   von OUT− an die Wago GND legen, der Platz dort ist frei gehalten.

Dann [Prüfung C](#c-wandler-auf-120-v).

### 4. 5 V und Lichtschranken (W6, W9–W11)

1. **W6:** vom Stift **5V** des Shields (Dupont 1-polig) an die **Wago
   +5 V**.
2. An jeder Lichtschranke ein 3-poliges Dupont-Gehäuse, die Adern nach dem
   Aufdruck am Modul: **VCC** rot, **GND** schwarz, **D0** gelb. Hat das
   Modul noch einen Stift A0, bleibt er frei.
3. Im Gehäuse: rot an die **Wago +5 V**, schwarz an die **Wago GND**, gelb
   mit einem 1-poligen Dupont-Gehäuse auf den Eingang: X → **X−** (D9),
   Y → **Y+** (D10), Z → **SpnEn** (D12).
4. Wege: X durch die Y-Kette, hinter dem Schlitten über das Rohr nach
   vorn zum Halter ([endschalter.md](endschalter.md)); Y durch den Kanal
   und in der unteren Nut außen am rechten 2040 nach hinten; Z durch beide
   Ketten zum Toolhead. Hat die Z-Lichtschranke schon ein Kabel: Es muss
   bis zum Gehäuse reichen, also 2 m lang sein.

Dann [Prüfung D](#d-uno-grbl-und-lichtschranken).

### 5. Laser (W7, W8)

1. **W7** an den Laser: XH-Stecker 3-polig, von links **PWM · GND ·
   +12 V** `[v]` Angabe. **Vor dem ersten Einschalten mit dem Aufdruck an
   der Buchse des Lasers vergleichen**: Vertauscht bekäme der PWM-Eingang
   12 V.
2. Im Gehäuse: rot an **OUT+** des Wandlers, schwarz an **OUT−**, weiß mit
   einem 1-poligen Dupont-Gehäuse auf den Signalstift von **Z+** (D11).
3. **W8:** einen Widerstand 10 kΩ in ein 2-poliges Dupont-Gehäuse crimpen
   und auf **Z−** stecken, Signal- und GND-Stift. Z− und Z+ liegen beide
   auf D11: Der Widerstand zieht die PWM auf 0 V, solange der Uno startet
   oder ohne USB ist. Ohne ihn kann der Laser in dieser Zeit aufblitzen.
4. Den Stecker am Laser erst bei [Prüfung H](#h-laser) aufstecken.

### 6. Motoren (W12–W15)

1. **Spulen finden:** Zwischen den zwei Adern einer Spule zeigt das
   Ohmmeter wenige Ohm (etwa 2–3 Ω), zwischen Adern verschiedener Spulen
   nichts.
2. **Am Shield** gehört jede Spule auf ein Stiftpaar: **2B · 2A** und
   **1A · 1B**, wie neben jedem Treiber aufgedruckt. Welche Spule auf
   welchem Paar liegt und wie herum, bestimmt nur die Drehrichtung.
3. X-Motor → **X**, Y-Motor links → **Y**, Z-Motor → **Z**, Y-Motor rechts →
   **A**.
4. **Y-Motor rechts mit getauschter Spule:** Beide Y-Motoren bekommen
   dasselbe Signal, müssen aber gegenläufig drehen. Deshalb am Stecker des
   rechten zwei Adern **einer** Spule tauschen, schwarz und grün. Die
   Kontakte lassen sich mit einer Nadel aus dem Dupont-Gehäuse lösen. Den
   4-poligen Stecker um 180° gedreht aufzustecken, wirkt genauso
   ([Zwei Y-Motoren](hardware-notizen.md#zwei-y-motoren)).
5. **In den Ketten nur die losen Adern:** Beim X-Motor (W12) und beim
   Z-Motor (W15) den Schlauch oder Mantel so weit entfernen, wie das Kabel
   durch die Ketten läuft, und die vier Adern einzeln einziehen.
6. Alles nur bei ausgeschaltetem Strom.

### 7. 24-V-Wächter (W16)

Der Not-Aus trennt die 24 V. Motoren und Laser sind dann stromlos, der Uno
läuft aber über USB weiter, und GRBL arbeitet den Auftrag weiter ab. Wird
der Not-Aus wieder entriegelt, bekommen Motoren und Laser mitten im Auftrag
wieder Strom, und der Laser brennt mit der Leistung, die gerade gilt.

Dagegen hilft der **24-V-Wächter**, ein Spannungsteiler an **Abort** (A0):

* **R1 22 kΩ** von der **Wago +24 V** an Abort,
* **R2 4,7 kΩ** und parallel dazu **100 nF** von Abort an die **Wago GND**.

Mit 24 V liegen an A0 4,1 bis 4,5 V, also HIGH. Fehlen die 24 V, zieht R2
den Eingang auf unter 1 V. GRBL bricht dann sofort ab, schaltet den Laser
aus und meldet ALARM; im Status steht `Pn:R`, solange die 24 V fehlen. Das
gilt für den Not-Aus, für den Schalter und für ein abgezogenes Netzteil.
Der Kondensator filtert Störungen aus der 24-V-Leitung.

Bauen: An jedes Ende eine kurze Litze 0,25 mm² anlöten, die Verbindung
beider Widerstände mit dem Kondensator in Schrumpfschlauch, von dort ein
1-poliger Dupont-Stecker auf **Abort**. Die Litzen enden in den Wagos. Auch
wenn der Stecker verrutscht, fließt über 22 kΩ höchstens 1 mA; das hält
jeder Pin aus.

Warum nicht der zweite Kontakt des Not-Aus: Er ist ein Wechsler, an NO läge
beim Drücken C, also +24 V. Das zerstört den Uno. Der Wächter braucht keinen
Kontakt und meldet mehr als nur den Not-Aus.

### 8. USB (W17)

Uno an den PC. Das USB-Kabel versorgt den Uno und damit die 5 V der
Lichtschranken.

## Kabelwege und Ketten

Die Wege zeigt [elektronik-platz.svg](elektronik-platz.svg), beschrieben
sind sie in [elektronik.md](elektronik.md#kabel).

* **Links aus dem Gehäuse** unter dem linken 2040 durch in dessen untere
  Außennut: W13 nach vorn zum linken Y-Motor, an jedem der drei Träger der
  Wanne Y kurz aus der Nut und über seine Wand; W7, W9, W11, W12 und W15
  bis hinter die Wanne Y, dort aus der Nut und von hinten in das Endstück
  180 der Y-Kette (zwei Kabelbinder durch die Schlitze im Wannenboden).
* **Vorn aus dem Gehäuse** in den Kanal, darin nach rechts, an der
  Rückseite des hinteren 2060 (mittlere Nut) zum rechten 2040 und in dessen
  untere Außennut: W14 und W2 nach vorn, W10 nach hinten zum Halter Y. W2
  verlässt die Nut vor dem 2060, läuft in dessen oberer Nut vorn nach
  links und rechts oben ins Gehäuse des Not-Aus.
* **Y-Kette:** W7, W9, W11, W12, W15. Sie kommen hinten aus dem
  Anfangsstück auf dem Kettenhalter Y (ein Kabelbinder). W12 läuft hinter
  dem Motorhalter hoch zum X-Motor, W9 über das Rohr nach vorn zum Halter X.
  W7, W11 und W15 laufen auf der Schlittenplatte hinter Rückwand und
  Motorhalter nach innen, rechts daneben in die obere Nut des Rohrs, darin
  bis an den Kabelflügel der Wannenstütze am Festpunkt, vor ihm hoch (zwei
  Kabelbinder) und oben über den Riemen nach vorn in das Endstück 180 der
  X-Kette ([energiekette.md](energiekette.md#kabelweg-am-festpunkt)).
* **X-Kette:** W7, W11, W15 bis zum Kettenhalter hinten an der
  Trägerplatte ([energiekette.md](energiekette.md)).

In den Ketten: Die Adern liegen lose nebeneinander, nicht verdrillt, auch
die der Motorkabel, ohne Schlauch. Am Kettenhalter des Toolheads hält sie
ein Kabelbinder durch die zwei Schlitze neben dem Anfangsstück. Keine Löt-
oder Steckstelle in der Kette.
In den Nuten halten Nutabdeckungen oder Clips die Kabel.

## Inbetriebnahme

In dieser Reihenfolge. Jede Stufe prüft, was die nächste braucht.

### A. Ohne Strom

* Jede Ader gegen die [Anschlussliste](#anschlussliste) prüfen und an jedem
  Kontakt ziehen.
* Ohmmeter zwischen Wago +24 V und Wago GND: **kein Kurzschluss**. Der Wert
  steigt langsam, weil die Kondensatoren laden, das ist in Ordnung.
  Dasselbe zwischen Wago +5 V und GND.
* Jede Motorspule zeigt 2–3 Ω, zwischen den Spulen ist offen.

### B. 24 V ohne Verbraucher

* W3 und W4 noch nicht in den Wagos, der Lüfter darf dran sein.
* Netzteil einstecken, Schalter an: An der Wago +24 V liegen **+24 V gegen
  GND**, nicht −24 V.
* Not-Aus drücken: 0 V. Entriegeln: 24 V. Schalter aus: 0 V.

### C. Wandler auf 12,0 V

* W4 in die Wagos, Schalter an, am Ausgang des Wandlers messen und am Poti
  auf **12,0 V** stellen. Das Poti hat viele Umdrehungen; ab Werk steht oft
  eine andere Spannung.

### D. Uno, GRBL und Lichtschranken

1. GRBL 1.1h auf den Uno spielen (Arduino-IDE, Bibliothek `grbl`, Beispiel
   `grblUpload`), nur über USB.
2. Shield aufstecken, noch ohne Treiber, nur USB. Gegen GND messen: An den
   Signalstiften von X−, Y+ und an SpnEn liegen **etwa 5 V** (die Pull-ups
   von GRBL), an Z+ und Z− **0 V**, am Stift 5V **5 V**. Liegt an SpnEn
   nichts,
   ist GRBL ohne variable Spindel gebaut und der Z-Endschalter läge auf
   D11. Stimmt etwas davon nicht, hat das Shield eine andere Belegung:
   dann hier aufhören und nachsehen.
3. W6 und W9–W11 anschließen, weiter nur USB.
4. In der Konsole `?` senden. Ohne Fahne in der Gabel erscheint kein `Pn:`,
   mit Fahne `Pn:X` (bzw. Y, Z). Ist es umgekehrt, `$5` umstellen. Diese
   Module melden „unterbrochen“ meist mit HIGH `[w]`, also `$5=1`. Dann
   meldet auch eine gebrochene Signalader „ausgelöst“, die sichere
   Richtung.

### E. Treiber und Vref

1. Alles aus. Die Treiber stecken, EN zum EN-Aufdruck, dazu die Jumper wie
   [oben](#klemmen-wago-und-shield). **Motoren noch nicht anschließen.**
2. W3 in die Wagos. USB an, dann Schalter an.
3. Vref zwischen GND und dem Schleifer des Potis messen und auf **1,37 V**
   stellen, an allen vier gleich. Das gibt bei jedem üblichen
   Messwiderstand höchstens 1,05 A
   ([Vref](hardware-notizen.md#treiber-und-versorgung)).
4. Alles aus.

### F. Motoren und Drehrichtung

1. Bei ausgeschaltetem Strom W12–W15 anstecken.
2. USB an, dann 24 V. Die Motoren halten, von Hand drehen sie schwer.
3. Jede Achse ein paar Millimeter langsam fahren, z. B. `$J=G91 X5 F500`
   (steht GRBL in ALARM, erst `$X`).
   **X+ fährt nach rechts, Y+ nach hinten, Z+ nach oben.** Sonst das Bit
   der Achse in `$3` setzen (X = 1, Y = 2, Z = 4, zusammenzählen).
4. **Y:** Beide Seiten müssen das Portal in dieselbe Richtung ziehen.
   Hängen die Riemen noch nicht, von oben auf die Wellen schauen: Sie
   drehen gegenläufig. Wenn nicht, an A eine Spule tauschen, bei
   ausgeschaltetem Strom.

### G. Referenzfahrt

* GRBL-Werte wie [unten](#grbl-einstellungen), die Hand am Not-Aus.
* `$H`: Z fährt nach oben bis zu seiner Lichtschranke, dann X nach links
  und Y nach hinten, beide zugleich. Jede Achse muss an ihrer eigenen
  Lichtschranke anhalten und darf nirgends anschlagen.
* Den Schaltpunkt von X und Y stellst du wie in
  [endschalter.md](endschalter.md#schaltpunkt-einstellen) ein.

### H. Laser

1. Alles aus. Den XH-Stecker aufstecken, die Reihenfolge am Aufdruck
   prüfen.
2. `$32=1` (Lasermodus) und `$30=1000`.
3. **Schutzbrille auf**, Karton unter den Laser, Fokus grob einstellen.
4. Mit 1 % Leistung eine kurze Linie: `G91`, `M3 S10`, `G1 X10 F600`, `M5`,
   `G90`. In LightBurn geht dasselbe mit „Fire“ bei 1 %.
5. Nach `M5` und im Stillstand ist der Laser aus.
6. **Ohne USB** die 24 V einschalten: Der Laser muss aus bleiben. Das prüft
   den Pull-down (W8).

### I. Not-Aus

* Bei einer langsamen Fahrt drücken: Motoren und Laser stehen sofort, GRBL
  meldet ALARM, und `?` zeigt `Pn:R`.
* Den Pilz drehen, bis er herausspringt. `Pn:R` verschwindet. Dann mit `$H`
  neu referenzieren.
* Schalter aus: auch dann steht `Pn:R` im Status, das ist richtig.

## GRBL-Einstellungen

<!-- tabelle:grbl -->
| Einstellung | Wert | warum |
|---|---|---|
| `$3` | nach dem Test | Drehrichtung: X+ nach rechts, Y+ nach hinten, Z+ nach oben ([Motoren](#f-motoren-und-drehrichtung)) |
| `$5` | 1 `[w]` | Lichtschranken melden „unterbrochen“ mit HIGH; im Test prüfen ([Lichtschranken](#d-uno-grbl-und-lichtschranken)) |
| `$20` | 1 | Softlimits an |
| `$21` | 0 | Hardlimits aus, bis die Schalter nie falsch auslösen |
| `$22` | 1 | Referenzfahrt an: erst Z, dann X und Y |
| `$23` | 1 | X referenziert nach links (minus), Y nach hinten und Z nach oben (plus) |
| `$27` | 1 | 1 mm Rückzug vom Schalter |
| `$30` | 1000 | S1000 = volle Laserleistung |
| `$32` | 1 | Lasermodus |
| `$100` | 80 | X: GT2, 20 Zähne, 1/16 |
| `$101` | 80 | Y: GT2, 20 Zähne, 1/16 |
| `$102` | 1600 | Z: Tr8×2, 1/16 |
| `$130` | 385 | X: 388,2 mm vom Schaltpunkt bis ans rechte Schienenende, minus Rückzug und Reserve |
| `$131` | 327 | Y: 330,3 mm vom Schaltpunkt bis vor das vordere 2060, minus Rückzug und Reserve |
| `$132` | 82 | Z: 85,55 mm Arbeitsweg vom Schaltpunkt bis ganz unten, minus Rückzug und Reserve |
<!-- /tabelle:grbl -->

`$3` und `$5` ergeben sich aus den Tests. `$130` bis `$132` rechnet
`tools/verkabelung.py` aus Portal, Toolhead und Endschaltern: vom
Schaltpunkt bis ans andere Ende, minus 1 mm Rückzug und 2 mm Reserve. Die
Schaltpunkte von X und Y stehen in [endschalter.md](endschalter.md), der
von Z in [toolhead-z.md](toolhead-z.md). Alles Übrige bleibt auf dem
Standardwert von GRBL.

## Fehlersuche

| Was passiert | Ursache | Abhilfe |
|---|---|---|
| `Pn:X` erscheint ohne Fahne oder nie | `$5` falsch herum, Signal auf dem falschen Stift, VCC fehlt | `$5` umstellen; Stift nach der [Tabelle](#klemmen-wago-und-shield); 5 V am Modul messen |
| ALARM „Hard limit“ mitten im Auftrag | `$21=1` und Störungen auf der Signalleitung | `$21=0`; 100 nF zwischen Eingang und GND am Shield; Signalleitung nicht neben Motorkabeln führen |
| Motor zittert oder brummt, dreht aber nicht | Spulenpaare vertauscht | Spulen mit dem Ohmmeter suchen, je ein Paar auf 2B·2A und 1A·1B |
| Motor dreht falsch herum | Richtung | Bit in `$3`; bei Y gegen A: an A eine Spule tauschen |
| Motoren verlieren Schritte oder werden über 70 °C heiß | Strom zu klein oder zu groß | Vref nach [hardware-notizen.md](hardware-notizen.md#treiber-und-versorgung) |
| Laser brennt nicht | Lasermodus aus, PWM falsch gesteckt, keine 12 V | `$32=1`, `$30=1000`; PWM auf Z+; 12 V am Stecker messen |
| Laser blitzt beim Einschalten kurz auf | Pull-down fehlt, 24 V vor USB | W8 stecken; erst USB, dann 24 V |
| Netzteil schaltet ab | Kurzschluss oder Überlast | 24-V-Leitungen prüfen; Vref nicht über 1,05 A |
| `Pn:R` im Status, GRBL bricht ab | keine 24 V: Not-Aus gedrückt, Schalter aus, Netzteil ab; oder R1 von W16 lose | Not-Aus entriegeln, 24 V einschalten; an Abort gegen GND messen: mit 24 V 4–4,5 V |
| GRBL bricht mitten im Auftrag ab, `Pn:R` blitzt kurz | die 24 V brechen ein (Stecker, Netzteil überlastet) | Hohlstecker und Netzteil prüfen; Vref nicht über 1,05 A |
| Uno verliert die Verbindung | USB | kürzeres oder besseres USB-Kabel |

## Geändert gegen den alten Anschlussplan

* **Masse der Lichtschranken** jetzt an die Wago GND. Vorher war der
  GND-Stift neben dem Eingang vorgesehen, und neben SpnEn gibt es womöglich
  keinen.
* **X-Lichtschranke an X−** statt X+. Beides ist D9, minus passt zur
  Referenz links.
* **Signalleitungen 0,25 statt 0,14 mm².** 0,14 mm² ist das Minimum der
  Wago, AWG 26 hat nur 0,13 mm².
* **Neu:** der Pull-down 10 kΩ an Z− (W8), der 24-V-Wächter an Abort (W16)
  und die Einschaltreihenfolge.
* **Not-Aus** (2026-09-30): Wechsler C/NO/NC, 3 A / 250 V, C und NC in der
  24-V-Leitung, NO frei; im eigenen Gehäuse vorn am vorderen 2060.
* **Lüfter:** 24 V an den Wagos. Der Hinweis auf einen 12-V-Lüfter ist
  gestrichen.
* **GRBL:** `$130=385` und `$132=82`, beide mit 1 mm Rückzug und 2 mm
  Reserve wie Y. Vorher standen dort ≈ 387 und ≈ 84.

## Noch offen

1. **Motorfarben** `[w]`: die übliche Belegung von Stepperonline. Beim
   Anschließen mit dem Ohmmeter prüfen.
2. **Lichtschranken** `[w]`: Reihenfolge der Stifte am Modul und ob D0 beim
   Unterbrechen HIGH wird. Das zeigt Prüfung D.
3. **Wandler:** Schraubklemmen oder Lötpunkte, und ob IN− und OUT−
   verbunden sind. Beides zeigt ein Blick auf das Modul.
