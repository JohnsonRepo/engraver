# Die Maschine aus Sicht der Gravur

Stand 2026-11-23. Quellen sind die Dateien in `docs/` des Repos; was nur
an der Maschine eingestellt und nicht in der Doku steht, ist so markiert.
Die Zahlen, die die Skripte brauchen, stehen in `scripts/maschine.py`.

## Inhalt

1. Koordinaten und Nullpunkt
2. Arbeitsfeld und Softlimits
3. Höhe, Spannmittel, Autofokus
4. Laser und GRBL
5. CNCjs und Pi
6. LightBurn
7. Offene Punkte

## 1. Koordinaten und Nullpunkt

- **G54 X0 Y0 = Innenecke des Anschlagwinkels vorn rechts** auf der
  Opferplatte (`docs/spannmittel.md`, Spannmittel Rev. 2 ff.). Gesetzt wird
  er einmal mit dem Laserpunkt 1 % auf der Innenecke und
  `G10 L20 P1 X0 Y0`; GRBL behält ihn im EEPROM.
- GRBL-Achsen: **X+ nach rechts, Y+ nach hinten**, Z+ nach oben. Das
  Werkstück liegt also bei **X ≤ 0 und Y ≥ 0**.
- Referenziert wird vorn links (`$23=3`, seit Portal Rev. 32): X nach
  links, Y nach vorn, Z nach oben. Der Maschinenraum ist wie immer bei GRBL
  negativ: X von −`$130` bis 0, Y von −`$131` bis 0, Z von −`$132` bis 0.
  G54 = Maschinenposition − WCO.
- Wird die Referenz geändert, verschiebt sich G54 mit: dann neu setzen.
- Im Modell (`Portal.py`) liegt die Innenecke bei X +183,35, Y +160,5
  (Portal-Koordinaten, Y+ dort nach vorn), 4 mm im Arbeitsfeld.

## 2. Arbeitsfeld und Softlimits

- Arbeitsfeld laut Modell (Portal Rev. 36, `docs/opferplatte.md`):
  391 × 285 mm. Relativ zum Nullpunkt: **X −387,2 bis +4,0, Y −4,0 bis
  +281,0**. Das ist der Rückfallwert in `maschine.py`.
- Softlimits sind an (`$20=1`): Ein Ziel außerhalb bricht einen Auftrag mit
  ALARM:2 ab, ein Jog bekommt `error:15`. Sie stimmen nur nach `$H`.
- `$130`: Doku 385, an der Maschine am 2026-11-18 vom Nutzer auf **367**
  gestellt (vorher 380). Ist das noch so, endet das Feld rechts bis zu
  18 mm früher, als das Modell sagt. Den echten Wert liefert
  `grbl_lesen.js`; ohne Pi das Makro **Rahmen** vor dem Start fahren.
- `$131=282`: hinten endet Y 3 mm vor dem hinteren 2060 (Toolhead mit Z
  unten). `$132=56`: Z hält 4 mm über der Opferplatte.

## 3. Höhe, Spannmittel, Autofokus

- Die Opferplatte (Spanplatte 615 × 349 × 25,3 mm) liegt mit der Maschine
  auf demselben Tisch. **Werkstücke bis 32 mm** passen unter den Toolhead.
- Zwischen zwei Linien hebt der Laser nicht ab: Der Toolhead fährt in
  Arbeitshöhe über alles. Anschlag und Exzenter sind 3 mm hoch, der
  Niederhalter ragt 2,5 mm über das Werkstück; der Toolhead bleibt
  mindestens 4 mm über dem Werkstück. Overscan über den Anschlag ist also
  unkritisch.
- **Exzenter** (2 Stück) schieben das Werkstück in die Ecke.
  **Niederhalter** gibt es für 2, 3, 4, 5 und 6 mm Material; ihre Lippe
  liegt 5 mm auf dem Rand → **6 mm zwischen Gravur und Kante**, wo einer
  sitzt. Verzogene Platten hohl nach oben legen.
- **Autofokus:** Messpunkt **G54 X−30 Y58** (30 mm links, 58 mm hinter der
  Ecke). Das Werkstück muss ihn bedecken; der Laser macht dort einen
  schwachen Punkt. Danach steht Z im Fokus (`docs/autofokus.md`; an der
  Maschine noch nicht erprobt).
- **Fokustest:** Makros „Fokustest grob (±1 mm)“ und „fein (±0,5 mm)“ in
  CNCjs brennen 11 Linien in Z-Stufen, die dünnste ist der Fokus
  (`docs/fokustest.md`). Nicht auf dem Messpunkt des Autofokus brennen.

## 4. Laser und GRBL

- Modul **LASER TREE 4 W, 450 nm**, Fokus am Modul einstellbar,
  Fokusabstand f nicht gemessen. 12 V über einen Abwärtswandler, PWM an
  D11 (Z+ am Shield), Pull-down 10 kΩ hält den Laser beim Einschalten aus.
- GRBL 1.1h. Für Gravuren wichtig:

| Wert | Einstellung | Quelle |
|---|---|---|
| `$30` | 1000 – S1000 = volle Leistung | docs/verkabelung.md |
| `$32` | 1 – Lasermodus | docs/verkabelung.md |
| `$110`, `$111` | 3000 mm/min | an der Maschine 2026-11-18, nicht in der Doku-Tabelle |
| `$120`, `$121` | 500 mm/s² | an der Maschine 2026-11-18, nicht in der Doku-Tabelle |
| `$11` | 0,010 (Standard) | GRBL |
| `$130`/`$131`/`$132` | 385 (Maschine: 367)/282/56 | docs/verkabelung.md |
| `$100`/`$101` | 80 Schritte/mm (0,0125 mm) | docs/verkabelung.md |

- **Lasermodus:** Bei G0 ist der Laser immer aus. **M4** (dynamisch)
  skaliert die Leistung mit der tatsächlichen Geschwindigkeit, beim
  Beschleunigen und in Ecken brennt nichts nach. **M3** hält die Leistung
  konstant, auch im Stillstand, wenn G1 aktiv ist – so arbeitet das Makro
  „Laserpunkt 1 %“ (`G1 F600`, `M3 S10`).
- In Lasermodus fährt GRBL durch S-Wechsel ohne Halt: Rasterzeilen mit
  vielen `X… S…` laufen durch.
- GRBL-Zeilenpuffer 80 Zeichen; Kommentare zählen nicht.

## 5. CNCjs und Pi

- CNCjs 1.11.5 auf dem Pi Zero 2 W: `http://laser.local:8000`, im Hotspot
  `http://10.42.0.1:8000`. Port `/dev/ttyACM0`, 115200 Baud.
- Dateien: Ordner **`~/gcode`** auf dem Pi = „Watch Directory“ in CNCjs.
  Oder im Browser „Upload G-code“ (bleibt nur bis zum Neustart).
- Makros (`pi/cncrc.json`): **Rahmen** (fährt die Außenkante der
  geladenen Datei mit G0, Laser aus; braucht die 3D-Ansicht),
  **Laserpunkt 1 %**, **Laser aus**, **Fokustest grob/fein**. Befehle
  **Pi herunterfahren**, **Pi neu starten**.
- **Zugang für Claude:** `ssh -i ~/.ssh/id_ed25519_claude -o
  IdentitiesOnly=yes laser@laser.local`. sudo nur für reboot/shutdown.
  Nach einem Namenskonflikt heißt der Pi `laser-2.local`; IP im Heimnetz
  war 192.168.178.50 (dann `-o HostKeyAlias=laser.local`).
- `grbl_lesen.js` holt über `GET /api/controllers` Einstellungen, Lage und
  WCO. Es braucht einen offenen Port in CNCjs und schreibt nichts. Den Uno
  nie über den seriellen Port selbst ansprechen (CNCjs hält ihn), und
  GRBL-Einstellungen nur ändern, wenn der Nutzer es ausdrücklich will.
- Ablauf an der Maschine (`docs/pi.md`): Schalter an, eine Minute warten,
  verbinden, `$H`, Werkstück an den Anschlag, Datei laden, Rahmen, Start,
  dabei bleiben. Danach „Pi herunterfahren“, 20 s warten, Schalter aus.

## 6. LightBurn

Wer lieber in LightBurn arbeitet (`docs/pi.md`): Ursprung **vorn rechts**,
„Start From: **Absolute Coords**“, „Constant Power Mode“ aus (M4), mit
„Save GCode“ speichern und in `~/gcode` legen. `gcode_check.py` prüft
solche Dateien wie die eigenen.

## 7. Offene Punkte

- `$130` an der Maschine (zuletzt 367) gegen 385 in der Doku.
- Zeilenversatz bei bidirektionalem Raster mit F2000 nicht gemessen
  (seit der Katze vom 2026-11-18 offen).
- Wie viele Befehle je Sekunde Uno und CNCjs schaffen, ist nicht
  gemessen; `gcode_check.py` warnt ab 10 % Fahrzeit in Befehlen unter
  4 ms (Erfahrungswert).
- Gemessen ist nur rohe Spanplatte; alle anderen Materialien sind
  Startwerte.
- Fokusabstand f des Moduls.
