# Use the 'latest' tag from fedora-bootc.
FROM registry.fedoraproject.org/fedora-bootc:42

# Build arguments
ARG buildid="unset"
ARG gputype="generic"

# Set labels
LABEL org.opencontainers.image.build-id="$buildid"
LABEL org.opencontainers.image.authors="Dirk Gottschalk"
LABEL org.opencontainers.image.name="MediaJunkie"
LABEL org.opencontainers.image.desciptionr="A bootc based media player image"

# Copy the prepared stuff we need into the image
COPY etc /etc

# Install the software we want to have.
#
# NOTE: To create images with (proprietary) GPU drivers you have to add:
#               --build-arg gputype=amd        (For AMD)
#               --build-arg gputype=intel      (for Intel)
RUN <<END_OF_BLOCK
set -eu

mkdir -p /usr/bootc-image
echo $buildid > /usr/bootc-image/build-id

dnf -y install \
	https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
	https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

dnf -y install \
	rpmfusion-free-release-tainted \
	rpmfusion-nonfree-release-tainted

dnf -y --setopt="install_weak_deps=False" install \
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
	libdvdcss \
	usbutils \
	zram-generator \
	zram-generator-defaults

dnf -y --repo=rpmfusion-nonfree-tainted install "*-firmware"

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

dnf clean all -y

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
	bootc-fetch-apply-updates.timer \
	redboot-auto-reboot \
	redboot-task-runner \
	systemd-zram-setup@zram0.service

firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit}

END_OF_BLOCK

RUN bootc container lint
