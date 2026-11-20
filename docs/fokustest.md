# Fokustest

Ein Makro in CNCjs brennt elf kurze Linien, jede eine Stufe tiefer in Z.
Die dünnste, dunkelste Linie liegt im Fokus. Das ist genauer als der
Laserpunkt mit 1 %: Der sieht durch die Schutzbrille über rund einen
Millimeter fast gleich aus. Eine Linie mit echter Leistung wird schon bei
wenigen Zehnteln neben dem Fokus sichtbar breiter und heller.

Den Fokus brauchst du für den [Autofokus](autofokus.md#einlernen-einmal)
beim Lernen, und ohne Autofokus für jedes Werkstück.

## Die Makros

| Makro | Linien | Stufe | Z um die Starthöhe |
|---|---|---|---|
| **Fokustest grob (±1 mm)** | 11 | 0,2 mm | +1 bis −1 mm |
| **Fokustest fein (±0,5 mm)** | 11 | 0,1 mm | +0,5 bis −0,5 mm |

Beide brennen mit `M4 S400 F2000` (40 %, 2000 mm/min). Das ist die
kleinste Leistung, die in der Materialprobe auf Spanplatte ganz schwarz
brannte, und gibt die dünnsten Linien.

Gebrannt wird ab der Stelle, an der der Kopf steht, nach links und nach
hinten, auf 22 × 17 mm. Alles ist relativ (`G91`), der Nullpunkt spielt
keine Rolle. Am Ende steht der Kopf wieder am Start, auf der Starthöhe.
Von vorn gesehen:

```
          |
|         |         |
| | | | | | | | | | |
| | | | | | | | | | |
-1       0,0       +1      Kopf tiefer ← → Kopf höher
```

* Die Linien beginnen **vorn** auf einer Höhe und laufen nach hinten.
* **Rechts** brennt der Kopf am höchsten, **links** am tiefsten.
* Die **lange** Linie (15 mm) ist die Starthöhe, **mittellange** (12,5 mm)
  liegen auf jedem halben Millimeter, die anderen sind 10 mm lang.

Z fährt zwischen den Linien nur abwärts. So liegt jede Stufe auf derselben
Seite des Spiels der Spindel.

## Ablauf

1. Ein Reststück oder eine freie Stelle des Werkstücks, flach aufliegend,
   nicht auf dem Messpunkt des Autofokus. Eingebrannte Linien machen den
   Punkt dort dunkler. Schutzbrille, Lüftung.
2. **Grob scharfstellen:** Makro **Laserpunkt 1 %**, dann Z in der Konsole
   in kleinen Schritten, bis der Punkt am kleinsten ist (`G91 G1 Z-0.2
   F60`, Pfeil hoch und Enter wiederholt die Zeile; `Z0.2` geht hoch).
   Danach **Laser aus** und `G90`. Die Pfeiltasten im Achsen-Widget fahren
   mit G0, dabei geht der Punkt aus. Auf ±1 mm genau reicht.
3. Den Kopf mit den Pfeiltasten in X und Y über die **rechte vordere
   Ecke** der freien Fläche fahren. Z nicht mehr verstellen.
4. Makro **Fokustest grob (±1 mm)**. Es dauert unter einer Minute.
5. **Lesen**, am besten mit Lupe oder einem nahen Handyfoto: Welche Linie
   ist am dünnsten und schärfsten? Von der langen Linie aus zählen: Jede
   Linie nach rechts ist 0,2 mm höher, jede nach links 0,2 mm tiefer.
6. **Kopf auf diese Höhe**, in der Konsole, z. B. zwei Linien rechts der
   langen:

   ```
   G91 G0 Z0.4
   G90
   ```

   Liegt die dünnste Linie ganz außen, kann der Fokus noch weiter weg
   liegen: auf diese Höhe, an einer neuen Stelle noch einmal grob.
7. **Genauer:** Auf der neuen Höhe, an einer neuen Stelle, **Fokustest fein
   (±0,5 mm)**. Zählen wie in Schritt 5, je Linie 0,1 mm, dann wie in
   Schritt 6 auf diese Höhe.

Abbrechen mit **Feedhold** und **Reset** in CNCjs. Der Reset setzt auch
`G90` wieder; ohne Reset danach `M5` und `G90` senden.

## Danach

* **Autofokus lernen:** Liegt das Werkstück am Anschlag und bedeckt den
  Messpunkt, jetzt **Fokus lernen**. Z steht schon im Fokus.
* **Ohne Autofokus:** `G10 L20 P1 Z0`: Z 0 im Nullpunkt G54 ist jetzt der
  Fokus, wie nach dem Autofokus.
* **Weitere Dicken ohne neuen Test:** Der Fokus liegt immer gleich weit
  unter dem Laser. Ist eine Platte d mm dicker, liegt der Fokus d mm
  höher. Die Maschinenposition Z aus CNCjs notieren und die Dicke beider
  Platten mit dem Messschieber am Messpunkt messen. Für die neue Platte
  `G53 G0 Z` mit Z alt + (Dicke neu − Dicke alt), dann **Fokus lernen**.
  Beispiel: 3-mm-Platte scharf bei Z −61,40, die 6,2-mm-Platte dann bei
  −61,40 + 3,2 = −58,20 (`G53 G0 Z-58.2`). Z fährt auf einer
  Tr8×2-Spindel, die Millimeter stimmen.

## In CNCjs anlegen

[`pi/einrichten.sh`](../pi/einrichten.sh) schreibt
[`pi/cncrc.json`](../pi/cncrc.json) mit den Makros nur, wenn es noch keine
`~/.cncrc` gibt. In einem schon eingerichteten CNCjs die Makros von Hand
anlegen: Im Makro-Widget **+**, Name und Inhalt aus

```sh
python3 tools/fokustest.py --zeigen
```

einfügen.

## Anpassen

Leistung, Vorschub, Abstand und Längen stehen oben in
[`tools/fokustest.py`](../tools/fokustest.py), die beiden Makros in
`MAKROS`. Brennen die Linien auf einem Material zu breit oder gar nicht,
`S` und `F` wie bei einer Materialprobe wählen: Die geringste Leistung,
die gerade noch dunkel brennt, gibt die dünnsten Linien und den
deutlichsten Unterschied. Danach:

```sh
python3 tools/fokustest.py
python3 tools/fokustest_check.py
```

Das erste schreibt die Makros in `pi/cncrc.json`, das zweite spielt sie
durch einen GRBL-Nachbau im Lasermodus. Es prüft, dass nur Linien nach
hinten brennen, rechts hoch und links tief, Z dabei nur abwärts fährt und
der Laser nie bei einer Z-Fahrt an ist. Am Ende muss der Kopf auf dem
Start stehen, mit `M5` und `G90`.
