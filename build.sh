#!/bin/bash

ID=$(date -u +%Y%m%d%H%M)

podman build --pull=newer --build-arg buildid="$ID" -t mediajunkie:nightly .
