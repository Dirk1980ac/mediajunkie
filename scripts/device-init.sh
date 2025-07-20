#!/bin/bash
set -eu

HOMEROOT="/home"

# If no user home exists
if [ -z "$(ls -A "$HOMEROOT")" ]; then
	# Add default user mjunkie with password mjunkie
	useradd -m -c "MediaJunkie" -d /home/mjunkie -G wheel -s /bin/sh mjunkie
	echo "mjunkie:mjunkie" | chpasswd
fi
