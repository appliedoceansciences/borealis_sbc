#!/bin/sh

# Save to both locations the network manager searches in
RUN_CONN=/run/NetworkManager/system-connections
ETC_CONN=/etc/NetworkManager/system-connections

BACKUP=/etc/wifi_backup

mkdir -p "$BACKUP"

has_valid() { [ -n "$(find "$1" -maxdepth 1 -type f -size +0c 2>/dev/null)" ]; }

# Copy the original valid network connection into the backup directory
if has_valid "$RUN_CONN" || has_valid "$ETC_CONN"; then
    if ! has_valid "$BACKUP"; then
        cp "$ETC_CONN"/* "$BACKUP"/
        cp "$RUN_CONN"/* "$BACKUP"/
        chmod 600 "$BACKUP"/*
        logger -t wifi_restore "backed up Wi-Fi credentials to $BACKUP"
    fi
fi

# Copy both sections with the backup
if has_valid "$BACKUP"; then
    rm -f "$ETC_CONN"/*
    rm -f "$RUN_CONN"/*
    cp "$BACKUP"/* "$ETC_CONN"/
    cp "$BACKUP"/* "$RUN_CONN"/
    chmod 600 "$ETC_CONN"/*
    chmod 600 "$RUN_CONN"/*
    logger -t wifi_restore "restored Wi-Fi credentials from $BACKUP"
else
    logger -t wifi_restore "WARNING: no credentials found in $ETC_CONN or $BACKUP"
fi
