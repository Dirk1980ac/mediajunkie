#!/bin/bash

ID=$(hostname -s)-$(date -u +%Y%m%d%H%M)

podman build --network host --pull=newer --build-arg buildid="$ID" \
	-t mediajunkie:nightly .
