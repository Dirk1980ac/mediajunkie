# Use the 'latest' tag from fedora-bootc.
FROM registry.fedoraproject.org/fedora-bootc:42

# Build arguments
ARG buildid="unset"
ARG gputype="generic"

#Environment
ENV imagename="mediajunkie"

# Set labels
LABEL org.opencontainers.image.version=${buildid}
LABEL org.opencontainers.image.authors="Dirk Gottschalk"
LABEL org.opencontainers.image.name=${imagename}
LABEL org.opencontainers.image.desciption="A bootc based media player image"

# Install the software we want to have.
#
# NOTE: To create images with (proprietary) GPU drivers you have to add:
#               --build-arg gputype=amd        (For AMD)
#               --build-arg gputype=intel      (for Intel)
RUN <<END_OF_BLOCK
set -eu

echo "IMAGE_ID=$imagename}" >>/usr/lib/os-release
echo "IMAGE_VERSION=$buildid" >>/usr/lib/os-release

dnf -y install \
	https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
	https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

dnf -y install \
	rpmfusion-free-release-tainted \
	rpmfusion-nonfree-release-tainted

dnf -y --setopt="install_weak_deps=False" install \
	lightdm \
	cockpit \
	cockpit-storaged \
	cockpit-networkmanager \
	cockpit-bridge \
	cockpit-selinux \
	cockpit-ws \
	cockpit-ws-selinux \
	firewalld \
	freeipa-client \
	glibc-all-langpacks \
	kodi \
	kodi-firewalld \
	kodi-inputstream-adaptive \
	kodi-inputstream-rtmp \
	kodi-pvr-iptvsimple \
	kodi-peripheral-joystick \
	libaacs \
	cockpit \
	cockpit-storaged \
	realmd \
	watchdog \
	greenboot \
	greenboot-default-health-checks \
	mc \
	libdvdcss \
	libbluray \
	usbutils \
	zram-generator \
	zram-generator-defaults

dnf -y --repo=rpmfusion-nonfree-tainted --repo=rpmfusion-free-tainted install "*-firmware"

if [ "$gputype" != "generic" ]; then
	if [ "$gputype" == "amd" ]; then
		dnf -y swap mesa-va-drivers mesa-va-drivers-freeworld
		dnf -y swap mesa-vdpau-drivers mesa-vdpau-drivers-freeworld
	elif [ "$gputype" == "intel" ]; then
		dnf -y install intel-media-driver
	else
		echo "Unknown GPU type: $gputype" >&2
		exit 1
	fi
fi
dnf clean all -y
END_OF_BLOCK

# Copy the prepared stuff we need into the image
COPY --chmod=644 configs/watchdog.conf /etc/watchdog.conf
COPY --chmod=600 configs/sudoers-wheel /etc/sudoers.d/wheel
COPY --chmod=644 configs/lightdm.conf /etc/lightdm/lightdm.conf
COPY --chmod=700 scripts/device-init.sh /usr/bin/device-init.sh
COPY systemd/device-init.service /usr/lib/systemd/system/device-init.service
COPY systemd/bootc-fetch-apply-updates.timer /usr/lib/systemd/system/bootc-fetch-apply-updates.timer
COPY skel /etc/skel

# Pull BluRay keydb.
RUN <<END_OF_BLOCK
set -eu
mkdir -p /etc/skel/.config/aacs
curl -k https://vlc-bluray.whoknowsmy.name/files/KEYDB.cfg -o /etc/skel/.config/aacs/KEYDB.cfg
END_OF_BLOCK

RUN <<END_OF_BLOCK
set -eu

# Enable services
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
	systemd-zram-setup@zram0.service \
	device-init

# Setup Firewall
firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit}

rm -rf /var/[spool,cache]
END_OF_BLOCK

RUN bootc container lint
