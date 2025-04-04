# Use the 'latest' tag from fedora-bootc.
FROM registry.fedoraproject.org/fedora-bootc:latest

# Will later be used te generate GPU specific images
# Will later be used to generate GPU specific images
ARG gputype="generic"

# Build ID to identify the generated image
ARG buildid

# Set some image labels for identification
LABEL org.opencontainers.image.name="MediaJunkie"
LABEL org.opencontainers.image.desciptionr="A bootc based media player image"
LABEL org.opencontainers.image.description="A bootc based media player image"
LABEL org.opencontainers.image.authors="Dirk Gottschalk"
LABEL image.build-id=$buildid

# Copy the prepared stuff we need into the image
COPY etc /etc

# Install the software we want to have, set the firewall and install some
# additional RPMFusion packages.
#
# NOTE: To create images with (proprietary) GPU drivers you have to add:
#               --build-arg gputype=amd        (For AMD)
#               --build-arg gputype=intel      (for Intel)
# NOTE: Support for NVidia with proprietary drivers will follow later.
RUN <<'EOF'
set -eu

echo "$buildid" >/usr/bootc-image/build.id

dnf -y install --setopt="install_weak_deps=False" \
	lightdm \
	firewalld \
	freeipa-client \
	glibc-langpack-de \
	kodi \
	kodi-firewalld \
	kodi-inputstream-adaptive \
	kodi-inputstream-rtmp \
	kodi-pvr-iptvsimple \
	cockpit \
	cockpit-storaged \
	realmd \
	watchdog \
	greenboot \
	greenboot-default-health-checks \
	fedora-remix-logos \
	mc \
	usbutils \
	zram-generator \
	zram-generator-defaults

dnf -y install rpmfusion-free-release-tainted rpmfusion-nonfree-release-tainted
dnf -y install libdvdcss
dnf -y --repo=rpmfusion-nonfree-tainted install "*-firmware"
dnf -y swap ffmpeg-free ffmpeg --allowerasing
dnf clean all -y

firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit}

systemctl enable \
	cockpit.socket \
	sshd \
	watchdog \
	greenboot-task-runner \
	greenboot-healthcheck \
	greenboot-status \
	greenboot-loading-message \
	greenboot-grub2-set-counter \
	greenboot-grub2-set-success \
	greenboot-rpm-ostree-grub2-check-fallback \
	redboot-auto-reboot \
	redboot-task-runner \
	systemd-zram-setup@zram0.service

if [ $? -eq 0 ]; then
	if [ "$gputype" == "amd" ]; then
		dnf -y swap mesa-va-drivers mesa-va-drivers-freeworld
		dnf -y swap mesa-vdpau-drivers mesa-vdpau-drivers-freeworld
	elif [ "$gputype" == "intel" ]; then
		dnf -y install intel-media-driver
	elif [ "$gputype" == "generic" ]; then
		: # No GPU specific drivers needed.
	else
		echo "Unknown GPU type: $gputype" >&2
		exit 1
	fi
else
	exit 1
fi
EOF

# Let's lay back in our rocking chair while the magic happens
