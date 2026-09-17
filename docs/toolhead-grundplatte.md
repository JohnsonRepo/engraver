# Toolhead-Grundplatte (Z-Achse, Diodenlaser)

Erzeugt von `fusion/ToolheadGrundplatte/ToolheadGrundplatte.py`.
Rechnerische Nachprüfung: `python3 tools/geometrie_check.py`.

## Warum eine Versatzplatte und keine flache Platte

Die Passfläche des Toolheads ist die **Stirnfläche des MGN9-Z-Wagens**, nicht die
Fläche der Z-Platte, auf der die Schiene sitzt. Zwischen beiden liegt die
Montagehöhe des Wagens: **10 mm** (Schiene 6,5 mm hoch, Wagen sitzt 3,5 mm
darüber). Wird diese Höhe beim Konstruieren übersehen, sitzt das Teil um genau
diesen Betrag falsch — die Flächen werden nicht bündig.

Die Platte nimmt die Höhe deshalb explizit auf:

* Der **Ursprung des Modells** liegt in der Mitte des Wagen-Lochbildes, **auf**
  der Wagen-Stirnfläche. Das ist die Bezugsebene, ab der alles bemaßt ist.
* Ein **Auflagepad** (6 mm) setzt die Plattenrückseite vom Wagen ab. Nur dieses
  Pad und die Rippen berühren den Wagen — nichts liegt auf der Schiene auf.
* Die Laser-Anschraubfläche liegt damit **12 mm** vor der Wagen-Stirnfläche und
  **22 mm** vor der Fläche der Z-Platte.

## Maßkette in Modell-Z (ab Wagen-Stirnfläche = 0)

| Ebene | Lage |
|---|---|
| Auflageebene der MGN9-Schiene (Fläche der Z-Platte) | −10,0 mm |
| Oberkante Schiene | −3,5 mm |
| Wagen-Stirnfläche = Rückseite Pad/Rippen | 0 mm |
| Rückseite Grundplatte | +6,0 mm |
| Anschraubfläche des Lasers | +12,0 mm |
| **Strahlachse** (Laser 35 mm tief, mittig) | **+29,5 mm** |
| Strahlachse ab Fläche der Z-Platte | +39,5 mm |

Freigänge: 3,5 mm zur Schienenoberkante, 10 mm zur Z-Platte, Seitenrippen
3,0 mm außerhalb des 20 mm breiten Wagens.

## Koordinatensystem

Das Modell steht in Druckorientierung, deshalb sind Modell- und Maschinenachsen
vertauscht:

| Modell | Maschine | Bedeutung |
|---|---|---|
| X | X | quer, längs des Portals |
| Y | Z | senkrecht, Verfahrrichtung der Z-Achse |
| Z | Y | nach vorn, weg vom Portal — zugleich Druckrichtung |

## Aufbau

```
              Modell-Z (nach vorn) ->
  Z-Platte    Wagen   Pad/Rippen   Grundplatte    Laser
   |            |      6 mm          6 mm          35 mm tief
  -10          0      0..6          6..12         12..47
```

* **Grundplatte** 35 × 52 × 6 mm — trägt den Laser, 4 Langlöcher.
* **Auflagepad** 28 × 26 × 6 mm — liegt auf dem Wagen, enthält die 4
  M3-Durchgangslöcher.
* **Mittelrippe** 5 mm breit und **zwei Seitenrippen** (Innenkante 13 mm ab
  Mitte) über die volle Höhe, 6 mm tief. Sie versteifen gegen das Kippmoment
  des Lasers, halten die Druckbrücke auf 10,5 mm und bilden den Freiraum, in
  dem die Schraubenköpfe der Laserverschraubung liegen.
* **Fase 0,4 × 45°** an der Auflagefläche: ohne sie hebt der Elefantenfuß der
  ersten Druckschicht das Teil vom Wagen ab.

## Verschraubung

| Verbindung | Schrauben | Hinweis |
|---|---|---|
| Platte → MGN9-Wagen | 4 × M3×8 Zylinderkopf (DIN 912) | 6 mm Kunststoff, ca. 2 mm Gewindeeingriff. MGN9 bietet nur ~2,5 mm Gewindetiefe — **keine längere Schraube**, sie setzt sonst auf dem Gewindegrund auf und klemmt nicht. |
| Laser → Platte | 4 × M3×10 + große Scheibe DIN 9021 (Ø9) | Scheibe ist wegen der Langlöcher Pflicht. Gewindetiefe im Lasergehäuse prüfen. |

Die Wagenschrauben werden durch Ø6,5-Freibohrungen in der Platte angezogen.
Der Kopf versinkt 3 mm unter der Laser-Anschraubfläche, der Laser liegt also
plan auf.

**Montagereihenfolge: erst den Laser an die Platte, dann die Platte an den
Wagen.** Die Köpfe der Laserschrauben liegen im Rippenraum hinter der Platte;
bei einem MGN9H-Wagen (39,9 mm lang) stehen sie über dem Wagen und sind
montiert nicht mehr zugänglich. Bei einem MGN9C (28,9 mm) liegen sie mit
2,3 mm Luft frei neben dem Wagen.

## Druck (PETG, Bambu Lab A1)

* **Laser-Anschraubfläche nach unten** aufs Bett legen — Modell-Z ist die
  Aufbaurichtung. So liegen alle Kräfte in der Schicht, alle Bohrungen stehen
  senkrecht, und es sind keine Stützen nötig.
* Die Platte überbrückt 10,5 mm zwischen Mittel- und Seitenrippe — unkritisch.
* 4 Wandlinien, ≥ 40 % Infill. PETG wegen der Abwärme des Lasers.
* Gewicht voll gerechnet ca. 21 g.

## Vor dem Druck prüfen

Beide Lochbilder sind noch nicht am Teil verifiziert (Status `[?]`, siehe
`hardware-notizen.md`). Das Skript erzeugt deshalb zwei **ausgeblendete**
Bohrlehren (3 mm, PLA) — im Browser einblenden, drucken, an das reale Teil
halten:

* `Bohrlehre_Laser` — 4 × M3 auf 40,5 × 16,5 mm.
* `Bohrlehre_Wagen` — 8 Löcher: inneres Paar = MGN9C (10 mm), äußeres Paar =
  MGN9H (16 mm). Damit ist auch geklärt, welcher Wagen verbaut ist.

Die Langlöcher am Laser fangen Abweichungen ab: quer 13,9 – 19,1 mm,
senkrecht 39,1 – 41,9 mm. Das deckt die frühere Messung 40 × 16 mm mit ab. Weicht das reale Bohrbild stärker ab, reicht es,
`laser_loch_hoch` bzw. `laser_loch_quer` im Parameter-Dialog zu ändern.

## Parameter

Alle Maße aus dem `MASSE`-Block des Skripts werden als Fusion-User-Parameter
angelegt (*Ändern → Parameter*). Die wichtigsten:

| Parameter | Wert | Zweck |
|---|---|---|
| `wagen_loch_laengs` | 16 mm | **MGN9H = 16, MGN9C = 10** — am Wagen prüfen |
| `wagen_loch_quer` | 15 mm | MGN9 Lochbild quer |
| `wagen_hoehe` | 10 mm | Montagehöhe — treibt den Freigang zur Schiene |
| `laser_loch_hoch` / `laser_loch_quer` | 40,5 / 16,5 mm | Bohrbild des Lasers |
| `laser_tiefe` | 35 mm | treibt die Lage der Strahlachse |
| `pad_hoehe` | 6 mm | Versatz Wagenfläche → Plattenrückseite |
| `dicke_platte` | 6 mm | Plattendicke |
