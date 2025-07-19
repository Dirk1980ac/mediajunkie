#!/bin/bash

# Find the last created user with UID >= 1000
LATEST_USER=$(getent passwd | awk -F: '$3 >= 1000 {print $1}' | tail -n 1)

if [ -n "$LATEST_USER" ]; then
    # Check if the user is already configured for autologin
    if ! grep -q "AutomaticLogin=${LATEST_USER}" /etc/gdm/custom.conf; then
        # Add or update the autologin settings
        sed -i '/^\[daemon\]/aAutomaticLoginEnable=true\nAutomaticLogin='${LATEST_USER}'' /etc/gdm/custom.conf

        # Disable the systemd service so it only runs once
        systemctl disable autologin-setup.service

        echo "Autologin configured for user: ${LATEST_USER}"
    fi
fi
