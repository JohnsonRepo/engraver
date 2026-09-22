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

## Verwindung („windschief")

Der Fehler, um den es beim Ausrichten der Profile hauptsächlich geht: das
Profil ist um seine **eigene Längsachse** verdreht, und zwar unterschiedlich
stark über die Länge. Die Oberseite ist dann keine Ebene mehr, sondern eine
Wendelfläche — vorn liegt sie waagerecht, hinten gekippt. Das Tückische: ein
Lineal quer aufgelegt liegt an *jeder* Stelle sauber auf, und längs aufgelegt
auch. Nur der **Querneigungswinkel** wandert von vorn nach hinten. Genau das
sieht die Box und sonst kein Werkzeug in der Werkstatt.

Warum es hier zählt: die Y-Wagen laufen auf dieser Fläche. Wandert die
Querneigung, rollt das Portal beim Fahren — und der 130-mm-Hebel des Toolheads
macht daraus Strahlversatz (0,1° = 0,23 mm, Tabelle oben). Verwinden sich die
beiden Profile *unterschiedlich*, wird das Portal zusätzlich verspannt: die
Wagen laufen schwerer und verschleißen einseitig.

Woher sie kommt, in dieser Reihenfolge der Häufigkeit:

1. **Aus der Montage.** Nutensteine und Winkel zwingen das Profil in die Form,
   die die Teile darunter vorgeben. Ein Rahmen auf vier nicht in einer Ebene
   liegenden Füßen verwindet sich wie ein wackliger Tisch — und gibt das nach
   oben weiter.
2. **Aus der Strangpresse.** Verwindung ist eine normale Profiltoleranz,
   je nach Güte 0,5–1,5° pro Meter `[w]`. Das ist bis zu zehnmal unsere
   Zielgenauigkeit — deshalb lohnt das Messen, statt es anzunehmen.

**Erst feststellen, wo sie sitzt.** Profil einzeln auf eine flache Fläche
legen (Küchenarbeitsplatte, Tischkreissägentisch, MDF-Platte), nichts
festschrauben, und die Querneigung an beiden Enden messen. Wandert sie schon
so, ist das Profil selbst windschief — dann hilft Unterlegen am Rahmen nicht,
es verschiebt den Fehler nur. Steht sie frei und wandert erst nach dem
Anschrauben, ist es Montagespannung, und die lässt sich wegnehmen.

**Entdrillen heißt dann:** Schrauben lösen, damit sich das Profil entspannt,
an der tiefen Ecke unterlegen (Fühlerlehrenblech, Alufolie ≈ 0,02 mm je Lage,
gedruckte Shims), von der Mitte nach außen wieder anziehen, neu messen. Der
schnelle Vorab-Test am fertigen Rahmen: auf eine flache Fläche stellen und an
einer Ecke drücken. Hebt sich die *gegenüberliegende* Ecke mit, ist der Rahmen
verwunden — wie ein Tisch, der diagonal kippelt.

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
2. **Jedes 2040 einzeln entdrillen.** Box **quer** auf das Profil (die
   Messachse über die 40 mm, nicht über die Länge — längs liest man die
   Steigung, quer die Verwindung), nullen, alle 100 mm ablesen. Änderung =
   Verwindung. Auf der genuteten Fläche steht die Box nur auf den beiden
   äußeren Stegen; sicherer ist ein kurzes gerades Stück quer aufgelegt und
   die Box darauf. Erst hier messen, solange die Profile frei zugänglich sind.
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

2040-Profil kommt krumm aus der Strangpresse: EN 12020-2 erlaubt für
Präzisionsprofile 0,3 mm Geradheitsabweichung je 300 mm Abschnitt `[w]`,
einfachere Güten mehr.
Diese Krümmung ist mit Ausrichten nicht wegzubekommen — sie geht in die
Bewegung ein, sobald die Führung darauf sitzt. Ausrichten kann nur Verwindung
und Verkippung beseitigen. Wenn die Gravur später eine gleichmäßige Welle über
die Y-Achse zeigt, ist das Profilkrümmung und kein Montagefehler.
