# Ausrichten mit einer Winkel-Messbox

Eine digitale Neigungsbox (Winkelwürfel, typisch 4 × 90°, Auflösung 0,1°) zeigt
nur Winkel gegen die Schwerkraft, keine Höhen und keine Abstände. Für das
Ausrichten der Y-Profile ist das **fast genau das richtige Werkzeug** — man muss
nur wissen, welche Fehler sie sieht und welche nicht.

## Der entscheidende Punkt: absolut nivelliert muss nichts sein

Die Maschine muss nicht waagerecht stehen. Was zählt, ist ausschließlich
**relativ**:

* die beiden Y-Führungen in *einer* Ebene (keine Verwindung),
* das Bett parallel zur Ebene, in der das Portal fährt,
* X rechtwinklig zu Y.

Alle drei sind Differenzen — und Differenzen ist das, was die Box kann. Die
Null-Taste ist also kein Notbehelf, sondern das eigentliche Feature.

Ein Grund, das Gestell trotzdem vorher grob waagerecht zu stellen: MEMS-Sensoren
haben ihre beste Auflösung nahe 0°, weil dort die Empfindlichkeit auf Kippung
maximal ist. Grob waagerecht = alle folgenden Messungen im besten Bereich.

## Zwei Hebel, zwei Genauigkeiten

Wofür die Box taugt, entscheidet der Hebelarm, auf den der Winkel wirkt.

**Hebel 1: der Toolhead, 130 mm.** Vom Lochbild des X-Wagens bis zur
Bettoberfläche (`bett_abstand`). Kippt das Portal, wandert der Strahl:

| Kippwinkel | Strahlversatz am Bett |
|---|---|
| 0,05° | 0,11 mm |
| **0,10°** | **0,23 mm** |
| 0,20° | 0,45 mm |
| 0,50° | 1,13 mm |

Ein *konstanter* Versatz ist harmlos (er verschiebt nur den Nullpunkt);
**Änderungen über die Bettfläche** verzerren die Gravur. Daraus folgt ein
brauchbares Abnahmekriterium: **die Anzeige darf über die ganze Fläche um nicht
mehr als eine Stelle wandern.** Bei 0,1° Auflösung entspricht das 0,23 mm — die
letzte Stelle der Box *ist* die Toleranz.

**Hebel 2: die Messspanne, 400–600 mm.** Als Höhenmessgerät über die
Profilbreite hinweg ist dieselbe Box grob:

| Winkel | 60 mm | 100 mm | 200 mm | 400 mm | 600 mm |
|---|---|---|---|---|---|
| 0,05° | 0,05 | 0,09 | 0,17 | 0,35 | 0,52 |
| 0,10° | 0,10 | 0,17 | 0,35 | 0,70 | 1,05 |
| 0,20° | 0,21 | 0,35 | 0,70 | 1,40 | 2,09 |
| 0,50° | 0,52 | 0,87 | 1,75 | 3,49 | 5,24 |

Also: **gut für Verwindung, schlecht für Höhendifferenzen über große Spannen.**
Die 60-mm-Spalte ist zugleich die Warnung — die Box steht selbst nur auf rund
60 mm Grundfläche, 0,1 mm Schmutz unter einer Kante sind schon 0,1° Fehler.
Fläche abwischen, Box immer in derselben Orientierung auf dieselbe Stelle.

## Vier Tricks

**1. Nullen statt nivellieren.** Box auf die linke Führung an den Anfang
legen, nullen, dann alle anderen Messstellen ablesen. Der Messwert *ist* der
Fehler gegen die Referenzstelle — keine Umrechnung, kein Absolutbezug nötig.

**2. Umschlagmessung gegen den eigenen Nullfehler.** Box ablesen, an
derselben Stelle um 180° drehen, wieder ablesen. Der echte Winkel ist
`(A − B) / 2`, der Nullfehler der Box `(A + B) / 2`. Damit wird aus ±0,2°
Gerätegenauigkeit eine Wiederholbarkeit in der Größe der Auflösung. Dasselbe
beim Vergleich zweier Profile: Box umdrehen, dann fällt auch eine unebene
Grundfläche der Box heraus.

**3. Die Maschine als Messgerät.** Sobald das Portal fährt: Box **auf den
Toolhead** setzen und in Y verfahren. Sind die beiden Y-Führungen nicht in
einer Ebene, verwindet sich das Portal beim Fahren und die Anzeige wandert.
Das misst die Koplanarität dort, wo sie zählt — am Werkzeug — und braucht
kein Lineal. Dasselbe in X gegen Verwindung des Portalprofils.

**4. Referenzbrücke für Höhen.** Braucht man doch eine Höhendifferenz
zwischen den Profilen, ein gerades Teil (Reststück Profil, Stahllineal) quer
darüberlegen und die Box darauf: Winkel × Spanne = Höhendifferenz, siehe
Tabelle oben. Nur eben mit der dort genannten Auflösung.

## Was die Box nicht kann — und was stattdessen

| Fehler | Werkzeug |
|---|---|
| **Abstand / Parallelität** der beiden Y-Führungen | Maßband an mehreren Stationen; danach Portal von Hand durchschieben und auf Klemmen fühlen |
| **Rechtwinkligkeit X ⊥ Y** (Gierwinkel — sieht kein Neigungsmesser) | gleiche Diagonalen im Rechteck, oder die Maschine selbst: ein 200-mm-Quadrat leicht auf Pappe gravieren und beide Diagonalen messen. **1 mm Differenz = 0,20° schief** (`ε = Δd / (a·√2)`) |
| **Krümmung** der Profile in der Waagerechten | gespannte Angelschnur oder langes Stahllineal + Fühlerlehre |
| **Bett parallel zur Portalebene** | Etwas am Toolhead nach unten reichen lassen (Schraube, Messuhr) und die Fläche abfahren — das misst direkt, was der Laser sieht |

Zur letzten Zeile: die Schärfentiefe eines komprimierten Diodenspots liegt grob
bei ±0,3…0,5 mm. Das ist die Toleranz für „Bett parallel", und eine Messuhr am
Toolhead ist dafür das ehrlichere Werkzeug als jeder Winkelmesser.

## Reihenfolge

1. **Gestell grob waagerecht** (Sensor in den besten Bereich bringen).
2. **Jedes 2040 einzeln entdrillen.** Box längs auf das Profil, nullen, alle
   100 mm ablesen. Änderung = Verwindung. Erst hier, solange die Profile noch
   frei zugänglich sind.
3. **Die beiden 2040er koplanar.** Box auf Profil A nullen, auf Profil B an
   derselben Y-Station ablesen, Station für Station. Unterlegen/nachziehen, bis
   die Anzeige über die Länge steht.
4. **Linearführungen aufschrauben** — und ab jetzt auf der *geschliffenen
   Schienenoberseite* messen, nicht auf dem Profil. Eine dünne Schiene folgt
   beim Anziehen dem Profil, sie richtet es nicht; deshalb Schritt 2 und 3
   vorher.
5. **Abstand und Rechtwinkligkeit** mit Maßband und Diagonalen (Tabelle oben).
6. **Portal montieren, Box auf den Toolhead, Fläche abfahren** (Trick 3).
   Zielwert: Anzeige wandert um höchstens eine Stelle.
7. **Bett parallel** mit Messuhr am Toolhead, Bett unterlegen.
8. **Nach dem Festziehen alles nochmal** — Nutensteine ziehen Profile beim
   Anziehen messbar aus der Lage.

## Was die Box am Gestell prinzipiell nicht leisten kann

2040-Profil kommt mit rund 0,2–0,5 mm Krümmung je Meter aus der Strangpresse.
Diese Krümmung ist mit Ausrichten nicht wegzubekommen — sie geht in die
Bewegung ein, sobald die Führung darauf sitzt. Ausrichten kann nur Verwindung
und Verkippung beseitigen. Wenn die Gravur später eine gleichmäßige Welle über
die Y-Achse zeigt, ist das Profilkrümmung und kein Montagefehler.
