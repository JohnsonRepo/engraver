# Opferplatte und Anschlag

Erzeugt von `fusion/Opferplatte/Opferplatte.py` (zwei Druckteile, Rev. 6).
Geprüft mit `python3 tools/opferplatte_check.py`, Zeichnung in
[opferplatte.svg](opferplatte.svg) (neu erzeugen mit
`python3 tools/opferplatte_zeichnen.py`).
Wie du das Werkstück auf der Platte spannst (Anschlag, Exzenter,
Niederhalter), steht in [spannmittel.md](spannmittel.md).

![Opferplatte zwischen den 2060, Anschläge am linken Ende](opferplatte.svg)

## Die Platte

Deine Opferplatte ist eine **Spanplatte 615 × 349 × 25 mm** (Angabe vom
2026-10-02, die Länge von 615 mm hast du bestätigt), gemessen **25,3 mm**
dick `[v]`, rund 3,5 kg. Gezogen wird sie **nach rechts**, sie liegt also
längs in X.

**Maschine und Platte stehen auf demselben Tisch**, die Plattenoberfläche
liegt 25,3 mm über der Unterkante der 2060. **Die beiden 2060 sind so nah
zusammengeschoben, dass die Platte ohne Spalt zwischen ihnen liegt**
(innen 349 mm, 369 mm Mitte zu Mitte, das vordere 30 mm hinter dem
vorderen Ende der 2040; Angabe 2026-11-21). Die Profile führen sie damit
in Y; es
braucht nur noch einen Anschlag für das linke Plattenende. Rechts hält
nichts, dort wird sie herausgezogen.

| Rev. | |
|---|---|
| 1–3 | vier Füße unter den 2060, die es an der Maschine nie gab |
| 4 | vier Halter zwischen Platte und 2060, rechts ein Klappriegel. Zwischen Platte und 2060 ist aber kein Platz |
| 5 | zwei Anschläge um das linke Ende der 2060, sonst nichts |
| **6** | **dasselbe, der Rahmen jetzt wie in `Portal.py` Rev. 36** (die Platte zwischen den 2060, das Arbeitsfeld hinten kürzer) |

## Wo sie liegt

Koordinaten wie in `Portal.py`: X nach rechts, Y nach vorn, Z = 0 in der
Mitte des Portalrohrs, das Portal in der Mitte seines Wegs.

| | |
|---|---|
| X | −297 bis +318: links an den Nasen der Anschläge, rechts steht sie 15 mm über die 2060, dort fasst du sie zum Herausziehen |
| Y | −159 bis +190: zwischen den 2060, ohne Spalt |
| Z | −129 bis −103,7: auf dem Tisch wie die 2060, unter den 2040 durch (34,7 mm Luft) |
| Arbeitsfeld | 391 × 285 mm (X −204 bis +187, Y −120,5 bis +164,5), so weit kommt der Strahl |
| Rand | in Y hinten 38,5 und vorn 25,5 mm Platte über das Feld hinaus, in X links 93 und rechts 131 mm |

**Das Arbeitsfeld ist hinten kürzer als bisher (285 statt 333 mm).** Das
hintere 2060 steht so weit vorn, dass der Toolhead mit Z unten 48 mm vor
dem hinteren Schienenende an ihm anstieße. Das Softlimit `$131=282` hält
ihn 3 mm davor ([endschalter.md](endschalter.md#grbl)). Vorn bleibt es,
wie es war: Die Lichtschranke ist nicht mit dem vorderen 2060 gewandert.

## Die Anschläge

Je einer sitzt am **linken Ende eines 2060** und greift um das Profilende
herum. Zwischen Platte und 2060 steckt nichts.

| | |
|---|---|
| Flansch | außen am 2060 (vorn an der Vorderseite, hinten an der Rückseite), 6 mm dick, 50 mm lang ab dem Profilende, 19 mm hoch. **2 × M5×12 mit Scheibe** in Hammermuttern der **äußeren unteren Seitennut** (10 mm über dem Tisch), 32 mm auseinander, von außen erreichbar |
| Endplatte | 6 mm dick vor der Stirnseite des 2060, 20 mm hoch, vom Flansch bis zur Innenseite des Profils |
| Nase | vor dem Plattenende, greift 15 mm in die Bahn der Platte, 20 mm hoch, also 5,3 mm unter der Oberfläche |
| Versatz | Links ragt das vordere 2060 30 mm, das hintere 35 mm über das 2040 (Angabe 2026-11-21): Das hintere endet 5 mm weiter links. Seine Nase ist deshalb 11 statt 6 mm dick; beide liegen in einer Flucht am Plattenende |

Ein Stoß gegen die Platte nach links drückt die Endplatte auf die
Stirnseite des 2060, nicht auf die Schrauben. Bei 100 N biegt sich die
Nase mit 6,3 MPa, die Pressung an der Stirnseite ist 0,25 MPa. Das trägt
PETG weit.

Vorn liegt der Flansch 4 mm neben dem Ohr des Elektronikfachs, das an
derselben Seite des 2060 sitzt. Die Hammermuttern sitzen ganz im Profil,
3,75 mm hinter dem Ende.

Eine Bohrlehre gibt es nicht: Die Anschläge gehen in Hammermuttern.
Gebohrt wird nichts.

## Höhen

| Z | was |
|---|---|
| −69 | Oberkante der 2060 |
| −98,2 | Unterkante des Lasers, Z am Softlimit, Laser ganz unten im Langloch |
| −99,7 | tiefster Punkt des Toolheads (Schlittenplatte), Z am Softlimit |
| **−103,7** | **Oberfläche der Platte** |
| −109 | Oberkante von Endplatte und Nase |
| −110 | Oberkante des Flansches |
| −119 | untere Seitennut außen: M5 der Anschläge |
| **−129** | **Tisch** = Unterkante der 2060 |

* **Z ganz unten:** Mechanisch käme die Schlittenplatte bis 21,6 mm unter
  die Plattenoberfläche. Das Softlimit hält sie 4 mm darüber: **`$132=56`**
  statt bisher 82 ([toolhead-z.md](toolhead-z.md#opferplatte-und-softlimit-rev-39),
  [GRBL-Tabelle](verkabelung.md)). Es greift nur nach `$H`.
* **Werkstückhöhe:** 32,7 mm über der Platte bis 5 mm unter die tiefste feste
  Kante des Toolheads (−66).
* **Toolhead über der Platte:** Am Softlimit bleiben 4 mm, über dem ganzen
  X- und Y-Weg; über den Anschlägen mehr, sie bleiben 5,3 mm unter der
  Plattenoberfläche.
* **Fokus:** `ToolheadZ.py` rechnet mit 103,7 mm von der Rohrmitte bis zur
  Plattenoberfläche. Das Fokusfenster ist f = 5,5 … 49 mm für 0–32 mm
  Werkstück.
* **Ohne Platte**, zum Beispiel auf einem großen Werkstück direkt auf dem
  Tisch: Dessen Oberfläche liegt 25,3 mm tiefer als die Platte. Mit
  `$132=56` reicht der Laser dann erst ab rund 31 mm Fokusabstand an sie
  heran. Mehr Weg nach unten (`$132` bis 82) nur, solange die Platte
  draußen ist.

## Montage

Ohne Platte:

1. Je 2 Hammermuttern M5 in die untere Seitennut **außen** am linken Ende
   beider 2060 einschwenken, ihre Mitten 9 und 41 mm vom Profilende.
2. Den Anschlag ans Profilende stellen: Endplatte an die Stirnseite,
   Flansch außen an das Profil, unten auf dem Tisch. 2 × M5×12 mit Scheibe
   von außen durch den Flansch in die Hammermuttern.
3. Die Platte von rechts zwischen die 2060 schieben, bis sie an beiden
   Nasen anliegt.

**Herausnehmen:** Platte nach rechts ziehen.

## Druck (PETG, Bambu Lab A1)

Unterseite (Tischseite) aufs Bett: Flansch, Endplatte und Nase stehen
senkrecht, die M5-Löcher liegen waagerecht. Keine Stützen, 4 Wandlinien,
20 % Infill.

| Teil | Volumen | Masse (voll) | Bauraum |
|---|---|---|---|
| Anschlag_vorn | 10,3 cm³ | ≈ 13 g | 56 × 41 × 20 mm |
| Anschlag_hinten | 11,8 cm³ | ≈ 15 g | 56 × 41 × 20 mm |

## Stückliste

| Stück | Teil | wofür |
|---|---|---|
| 2 | Anschlag (PETG): Anschlag_vorn, Anschlag_hinten | linkes Plattenende |
| 4 | M5×12 Zylinderkopf + Scheibe DIN 125 | Flansch → Hammermutter |
| 4 | Hammermutter M5 (Nut 6) | untere Seitennut außen am linken Ende beider 2060 |
| 1 | Spanplatte 615 × 349 × 25 mm (gemessen 25,3) | Opferplatte (vorhanden) |

Die Teile aus Rev. 4 (vier Halter, Riegel) und die Füße aus Rev. 1–3
brauchst du nicht.

## Noch offen

* **Nicht gemessen:** ob Kappen auf den Profilenden sitzen, und ob die
  äußere untere Seitennut am linken Ende frei ist (bis Rev. 3 war sie es).
* **`$132=56` und `$131=282`** an der Maschine setzen, falls noch nicht
  geschehen ([verkabelung.md](verkabelung.md)).

## Parametrik

Alle Werte aus dem `MASSE`-Block landen als Fusion-User-Parameter. Nach
einer Änderung das Skript neu laufen lassen und
`tools/opferplatte_check.py` ausführen.

| Parameter | Wert | Wirkung |
|---|---|---|
| `platte_l` / `platte_b` / `platte_dicke` | 615 / 349 / 25,3 mm | Opferplatte |
| `quer_innen` | 349 mm | Innenseiten der 2060 auseinander; liegen an der Platte an |
| `quer_ueber_vorn` / `quer_ueber_hinten` | 30 / 35 mm | so weit ragen die 2060 links über die Außenseite des 2040; legt die Profilenden und die Dicke der Nasen fest |
| `feld_x0` … `feld_y1` | −203,85 / +187,35 / −168,8 / +164,5 mm | Arbeitsfeld: die Platte liegt in Y mittig darunter |
| `flansch_l` / `flansch_t` / `flansch_h` | 50 / 6 / 19 mm | Flansch außen am 2060 |
| `endplatte_t` | 6 mm | Endplatte vor der Stirnseite; so dick ist auch die vordere Nase |
| `anschlag_h` / `anschlag_tief` | 20 / 15 mm | Höhe von Endplatte und Nase, so weit greift die Nase vor das Plattenende |
| `m5_abstand` / `nut_ein` | 32 / 5 mm | Abstand der beiden M5; so weit geht jede in die Nut (daraus M5×12) |
