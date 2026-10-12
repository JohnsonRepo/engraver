#!/bin/sh
# einrichten.sh — richtet den Raspberry Pi Zero 2 W als Steuerrechner fuer
# den Engraver ein (docs/pi.md): CNCjs als Dienst auf Port 8000, ein Ordner
# fuer G-Code-Dateien, Makros (Rahmen, Laserpunkt, Laser aus), Befehle zum
# Herunterfahren und Neustarten, WLAN-Energiesparen aus und ein eigenes WLAN
# (Hotspot), wenn beim Start keins da ist.
#
# Auf dem Pi, als der Benutzer aus dem Raspberry Pi Imager (nicht als root):
#
#     sh pi/einrichten.sh
#     sudo reboot
#
# Eine vorhandene ~/.cncrc und ein vorhandener Hotspot bleiben unveraendert;
# wer sie neu haben will, loescht sie vorher (den Hotspot mit
# sudo nmcli connection delete hotspot). Der Lauf darf wiederholt werden.

set -eu

HIER=$(cd "$(dirname "$0")" && pwd)
BENUTZER=$(id -un)
CNCJS_VERSION=1.11.5              # geprueft mit dieser Version (Node >= 18)

if [ "$BENUTZER" = root ]; then
    echo "Bitte als normaler Benutzer starten, nicht mit sudo." >&2
    exit 1
fi

# Zuerst, weil er nach dem Passwort fragt; danach laeuft alles ohne Eingabe.
echo "== Hotspot, wenn beim Start kein WLAN da ist"
if ! command -v nmcli > /dev/null; then
    echo "Kein NetworkManager gefunden: kein Hotspot." >&2
else
    if nmcli -t -f NAME connection show | grep -qx hotspot; then
        echo "Den Hotspot gibt es schon, er bleibt unveraendert."
    else
        while :; do
            printf 'Passwort fuer das WLAN "%s", 8 bis 63 Zeichen: ' "$(hostname)"
            read -r PASSWORT
            [ "${#PASSWORT}" -ge 8 ] && [ "${#PASSWORT}" -le 63 ] && break
        done
        # wie "nmcli device wifi hotspot", aber ohne ihn gleich einzuschalten
        sudo nmcli connection add type wifi ifname wlan0 con-name hotspot \
            autoconnect no ssid "$(hostname)" \
            802-11-wireless.mode ap 802-11-wireless.band bg \
            wifi-sec.key-mgmt wpa-psk wifi-sec.proto rsn \
            wifi-sec.pairwise ccmp wifi-sec.group ccmp \
            wifi-sec.psk "$PASSWORT" \
            ipv4.method shared ipv6.method ignore > /dev/null
    fi
    sudo install -m 755 "$HIER/hotspot.sh" /usr/local/sbin/hotspot
    sudo install -m 644 "$HIER/hotspot.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable hotspot
fi

# dnsmasq verteilt im Hotspot die Adressen, ohne ihn schaltet NetworkManager
# den Hotspot nicht ein.
echo "== Pakete: Node.js, npm und dnsmasq"
sudo apt-get update
sudo apt-get install -y nodejs npm dnsmasq-base

echo "== CNCjs $CNCJS_VERSION"
# Version aus dem package.json; "npm ls" taugt nicht, npm 9 meldet auch ein
# fehlendes Paket mit Erfolg.
IST=$(node -p "require('$(npm root -g)/cncjs/package.json').version" \
    2> /dev/null || true)
if [ "$IST" = "$CNCJS_VERSION" ]; then
    echo "Ist schon installiert."
else
    echo "Dauert auf dem Zero etwa 6 Minuten."
    # Nur Fehler zeigen: Die vielen Warnungen kommen aus den alten
    # Abhaengigkeiten von CNCjs und sind harmlos.
    sudo npm install -g --loglevel=error --no-fund "cncjs@$CNCJS_VERSION"
fi
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
if command -v nmcli > /dev/null; then
    echo "Ohne WLAN nach 1 Minute:    WLAN \"$(hostname)\", http://10.42.0.1:8000"
fi
