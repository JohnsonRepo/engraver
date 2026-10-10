#!/bin/sh
# einrichten.sh — richtet den Raspberry Pi Zero 2 W als Steuerrechner fuer
# den Engraver ein (docs/pi.md): CNCjs als Dienst auf Port 8000, ein Ordner
# fuer G-Code-Dateien, Makros (Rahmen, Laserpunkt, Laser aus), Befehle zum
# Herunterfahren und Neustarten, WLAN-Energiesparen aus.
#
# Auf dem Pi, als der Benutzer aus dem Raspberry Pi Imager (nicht als root):
#
#     sh pi/einrichten.sh
#     sudo reboot
#
# Eine vorhandene ~/.cncrc bleibt unveraendert; wer sie neu haben will,
# loescht sie vorher. Der Lauf darf wiederholt werden.

set -eu

HIER=$(cd "$(dirname "$0")" && pwd)
BENUTZER=$(id -un)
CNCJS_VERSION=1.11.5              # geprueft mit dieser Version (Node >= 18)

if [ "$BENUTZER" = root ]; then
    echo "Bitte als normaler Benutzer starten, nicht mit sudo." >&2
    exit 1
fi

echo "== Pakete: Node.js und npm"
sudo apt-get update
sudo apt-get install -y nodejs npm

echo "== CNCjs $CNCJS_VERSION (dauert auf dem Zero einige Minuten)"
sudo npm install -g "cncjs@$CNCJS_VERSION"
CNCJS=$(command -v cncjs)

echo "== Ordner und Konfiguration"
mkdir -p "$HOME/gcode"
if [ -e "$HOME/.cncrc" ]; then
    echo "$HOME/.cncrc gibt es schon, sie bleibt unveraendert."
else
    sed "s|@GCODE@|$HOME/gcode|" "$HIER/cncrc.json" > "$HOME/.cncrc"
fi

echo "== Dienst cncjs"
sed -e "s|@BENUTZER@|$BENUTZER|" -e "s|@CNCJS@|$CNCJS|" -e "s|@HOME@|$HOME|" \
    "$HIER/cncjs.service" | sudo tee /etc/systemd/system/cncjs.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable cncjs

echo "== Herunterfahren und Neustarten aus CNCjs"
TMP=$(mktemp)
sed "s|@BENUTZER@|$BENUTZER|" "$HIER/sudoers-cncjs" > "$TMP"
sudo visudo -cf "$TMP"
sudo install -m 440 "$TMP" /etc/sudoers.d/cncjs
rm -f "$TMP"

echo "== WLAN-Energiesparen aus"
if [ -d /etc/NetworkManager/conf.d ]; then
    sudo install -m 644 "$HIER/wlan-energiesparen-aus.conf" \
        /etc/NetworkManager/conf.d/
else
    echo "Kein NetworkManager gefunden: nach dem Neustart von Hand" >&2
    echo "    sudo iw dev wlan0 set power_save off" >&2
fi

echo
echo "Fertig. Jetzt neu starten:  sudo reboot"
echo "Danach im Browser:          http://$(hostname).local:8000"
