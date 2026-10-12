#!/bin/sh
# hotspot.sh — oeffnet ein eigenes WLAN, wenn der Pi nach dem Start kein
# bekanntes findet (docs/pi.md, "Ohne WLAN: Hotspot"). Laeuft einmal beim
# Start als Dienst hotspot.service; die Verbindung "hotspot" legt
# pi/einrichten.sh an. Der Hotspot bleibt bis zum naechsten Start.

WARTEN=60    # Sekunden, die der Pi nach dem Start das Heimnetz sucht

i=0
while [ "$i" -lt "$WARTEN" ]; do
    if nmcli -t -f DEVICE,STATE device 2> /dev/null | grep -qx 'wlan0:connected'; then
        exit 0
    fi
    sleep 1
    i=$((i + 1))
done

echo "Nach $WARTEN s kein WLAN: Hotspot an"
exec nmcli connection up hotspot
