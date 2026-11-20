# Autofokus in CNCjs

Ein Klick in CNCjs stellt Z auf den Fokus. Die Kamera im
[Kamerahalter](kamerahalter.md) sieht den Laserpunkt schräg von vorn
rechts. Je dicker das Werkstück, desto weiter wandert er im Bild. Das
Programm läuft auf dem Pi im Dienst `kamera-live`, zusammen mit dem
[Live-Bild](pi.md#kamera): [`pi/autofokus.py`](../pi/autofokus.py), die
Verbindung zu CNCjs in [`pi/cncjs_client.py`](../pi/cncjs_client.py), die
Seite in [`pi/autofokus.html`](../pi/autofokus.html). In CNCjs erscheint es
als eigenes Widget mit Kamerabild und Knopf **Autofokus**.

Ein Makro allein reicht dafür nicht: Makros schicken nur G-Code an GRBL,
und GRBL sieht kein Bild.

## Was beim Klick passiert

1. **Prüfen, ohne zu fahren:** CNCjs ist mit der Maschine verbunden, GRBL
   steht (`Idle`), kein Auftrag läuft, der Messpunkt ist gesetzt, mindestens
   drei Dicken sind gelernt, der Messpunkt liegt im Verfahrweg.
2. **Z ganz hoch** (Maschine Z −2), dann der Kopf zum **Messpunkt**. Beides
   mit `G53`, also in Maschinenkoordinaten, unabhängig vom Nullpunkt.
3. **Laser 1 s mit 1 %**: `G1 F600`, `M3 S10`, `G4 P1.00`, `M5`, als ein
   Block. GRBL schaltet den Laser nach dem G4 selbst ab, auch wenn der Pi
   dabei hängen bleibt. Danach prüft das Programm, dass GRBL Spindel 0
   meldet und der Punkt im Bild verschwunden ist; sonst sendet es noch
   einmal `M5` und bricht ab.
4. **Bild:** Die Kamera nimmt dem Live-Bild dafür kurz die Kamera weg und
   misst mit fester Belichtung (2 ms, das sind zwei PWM-Perioden des Uno,
   Verstärkung 1). Verglichen wird ein Bild vor dem Laser mit dem hellsten
   während: Die stärkste Aufhellung ist der Punkt, sein Schwerpunkt die Lage.
5. **Fokus-Z** aus der Lerntabelle, dann `G53 G0 Z…` und dort `G10 L20 P1
   Z0`: Z 0 im Nullpunkt G54 ist jetzt der Fokus. LightBurn-Dateien ohne
   Z laufen unverändert.

Das Messbild mit einem Kreuz auf dem gefundenen Punkt zeigt das Widget
unter **Messbild**.

**Schutzbrille** wie beim Makro „Laserpunkt 1 %“: Der Laser geht bei jedem
Messen und Lernen kurz an.

## In CNCjs einrichten

Einmal auf dem Pi installieren, dann in jedem Browser einmal das Widget
anlegen; CNCjs speichert Widgets je Browser.

1. **Auf dem Pi:** Den Ordner `pi` vom Mac kopieren und das Skript laufen
   lassen; es fragt nach dem sudo-Passwort.

   ```sh
   scp -r pi laser@laser.local:
   ssh laser@laser.local
   sh pi/einrichten.sh
   ```

   Es legt die Dateien nach `/usr/local/lib/engraver` und startet den
   Dienst neu. Danach öffnet `http://laser.local:8080/autofokus` die Seite
   auch allein im Browser.
2. **In CNCjs:** Oben in der rechten Spalte **Widgets verwalten**,
   **Benutzerspezifisches Widget** einschalten, **OK**.
3. Im neuen Widget das **Zahnrad**: Titel `Autofokus`, URL
   `http://laser.local:8080/autofokus`, **Änderungen speichern**. Dann den
   **Schalter** oben im Widget einschalten (er steht nach dem Anlegen auf
   aus).
4. Das **Webcam-Widget** links kann weg (**⋮ → Widget entfernen**): Das Bild
   steckt jetzt im Autofokus, und jedes offene Bild kostet rund 7 Mbit/s im
   WLAN.

Im Hotspot heißt die URL `http://10.42.0.1:8080/autofokus`. Der Knopf
**Neu laden** im Kopf des Widgets tut bei dieser Seite nichts (CNCjs darf
eine Seite von einem anderen Port nicht neu laden); dann die ganze
CNCjs-Seite neu laden.

## Einlernen (einmal)

Unter **Einlernen** im Widget. Vorher **Homing**.

**1. Messpunkt setzen.** Eine Stelle, die die Kamera sieht und die jedes
Werkstück am Anschlag bedeckt. Vorgesehen ist 30 mm links und 58 mm
hinter der Innenecke des Anschlagwinkels: Mit dem Nullpunkt in der Ecke
([spannmittel.md](spannmittel.md#nullpunkt-einrichten-einmal)) in der
Konsole `G0 X-30 Y58`. Ein Werkstück an den Anschlag legen, Makro
**Laserpunkt 1 %**: Der Punkt muss im Live-Bild zu sehen sein, gut im
Bild und nicht am Rand. **Laser aus**, dann **Messpunkt = aktuelle
Position**. Gespeichert wird die Maschinenposition (X, Y); ein späteres
Verschieben des Nullpunkts verschiebt den Messpunkt nicht. Neu setzen
leert die Tabelle.

**2. Dicken lernen**, mindestens drei: die leere Opferplatte oder die
dünnste Platte, die dickste, die du bearbeitest, und eine dazwischen. Je
Dicke:

1. Werkstück an den Anschlag.
2. Scharfstellen, am genauesten mit dem [Fokustest](fokustest.md) neben
   dem Messpunkt. Für weitere Dicken reicht oft der Messschieber
   ([Fokustest, Danach](fokustest.md#danach)).
3. Einen Namen eintragen (z. B. „leere Platte“, „6 mm Pappel“) und
   **Fokus lernen**.

Die Maschine fährt Z hoch, zum Messpunkt, der Laser geht 1 s an, dann
fährt Z zurück auf das Fokus-Z. Gespeichert werden dieses Z und die Lage
des Punkts. Den Fokusabstand des Lasers muss niemand kennen.

Ab drei Punkten legt das Programm eine **projektive Kurve** durch sie:
So bildet eine Kamera Punkte auf einer Geraden ab, hier auf dem
senkrechten Strahl. Mit zwei Punkten wäre es eine Gerade; dazwischen lag
sie in der Prüfung bis 0,9 mm daneben, deshalb sind es mindestens drei.

**Neu lernen**, wenn die Kamera, ihr Halter oder die Linse des Lasers
bewegt wurde, oder nach einem neuen Messpunkt. Einzelne Einträge löscht
das **×** in der Tabelle.

Die Tabelle steht auf dem Pi in `~/.config/engraver/autofokus.json`.

## Benutzen

1. Homing (einmal nach dem Einschalten).
2. Werkstück an den Anschlag; es muss den Messpunkt bedecken, in der Ecke
   also mindestens etwa 40 × 65 mm groß sein.
3. **Autofokus**, Schutzbrille. Die Meldung sagt das Fokus-Z und wie weit
   die Oberfläche über dem dünnsten gelernten Eintrag liegt.
4. Datei laden, **Rahmen**, **Start**.

**Abbrechen** hält eine laufende Fahrt an (Feedhold, dann Reset). Danach
Homing, weil GRBL beim Reset in der Fahrt die Position verliert. Der
Not-Aus bleibt der Not-Aus.

## Wenn es nicht klappt

| Meldung | Ursache | Abhilfe |
|---|---|---|
| CNCjs ist nicht mit der Maschine verbunden | in CNCjs kein Port offen | in CNCjs verbinden, Homing |
| Die Maschine ist nicht bereit (Alarm) | nach dem Einschalten oder Reset | Homing |
| Kein Laserpunkt im Bild | Werkstück bedeckt den Messpunkt nicht; Laser aus (Schalter, Not-Aus); Punkt außerhalb des Bilds | Werkstück größer oder an den Anschlag; Schalter an; unter **Messbild** nachsehen, wo die Kamera hinsieht |
| Zwei helle Stellen im Bild | Spiegelung, Licht ging an oder aus | noch einmal; blanke Flächen abdecken |
| Der Punkt liegt … px neben der gelernten Linie | Kamera, Halter oder Messpunkt bewegt | Tabelle neu lernen |
| Die Dicke liegt außerhalb des Gelernten | dicker oder dünner als alles Gelernte (mehr als ein Viertel der Spanne) | diese Dicke von Hand scharfstellen und lernen |
| Gelernte Punkte … widersprechen sich | zwei Einträge gleicher Dicke, oder ein Eintrag falsch scharfgestellt | den falschen Eintrag löschen |
| Der Laser meldet sich nicht aus / Punkt nach M5 noch zu sehen | M5 kam nicht an | Laser beobachten, Schalter aus; `M5` in der Konsole |
| Kamera für die Messung nicht verfügbar | ein anderes Programm hat die Kamera (`rpicam-still`) | warten, noch einmal |
| Widget bleibt leer | Dienst läuft nicht oder alte Version | `http://laser.local:8080/autofokus` direkt öffnen; `pi/einrichten.sh` noch einmal |

Klares Acryl und spiegelnde Flächen lassen den Punkt durch oder spiegeln
ihn weg: Schutzfolie oder Abdeckpapier drauflassen.

## Einstellungen

Die Werte stehen oben in [`pi/autofokus.py`](../pi/autofokus.py)
(`EINSTELLUNGEN`). Einzelne lassen sich in der Tabellendatei unter
`"einstellungen"` überschreiben, z. B. `"laser_s": 15`, wenn der Punkt zu
schwach ist. Danach den Dienst neu starten (`sudo systemctl restart
kamera-live`).

| Wert | Vorgabe | |
|---|---|---|
| `z_mess` | −2 | Maschinen-Z beim Messen (ganz oben) |
| `laser_s` | 10 | Laserleistung S, 1 % bei `$30=1000` |
| `laser_dauer_s` | 1,0 | Dauer des G4, so lange brennt der Punkt höchstens |
| `belichtung_us` | 2048 | feste Belichtung der Kamera |
| `min_anstieg` | 40 | so viel heller (0–255) muss der Punkt sein |
| `quer_min_px` | 15 | so weit darf der Punkt neben der gelernten Linie liegen |
| `ueberstand` | 0,25 | so weit über die gelernten Dicken hinaus wird gerechnet |

## Prüfen ohne Maschine

```sh
python3 tools/autofokus_check.py
```

Bildauswertung an künstlichen Bildern, Lerntabelle, der ganze Ablauf
gegen eine simulierte Maschine und Kamera (erst Z hoch, Laser nur im
G4-Block, Abbrüche ohne Fahrt), der Socket gegen einen nachgebauten
CNCjs-Server und die Webseite.

## Noch offen

Auf der Maschine noch nicht erprobt (Stand 2026-11-20): Die Verbindung
zu CNCjs ist am Pi geprüft (Zustand lesen, `G4 P0.01` senden). Noch nicht
geprüft sind die Rohbilder der Kamera im Messbetrieb (1280 × 960, YUV420)
und wie hell der Punkt bei 1 % und 2 ms wirklich ist. Wenn
`min_anstieg` nicht passt, zeigt das **Messbild** den Punkt.
