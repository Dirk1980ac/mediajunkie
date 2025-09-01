# Use the 'latest' tag from fedora-bootc.
FROM quay.io/fedora/fedora-bootc:latest

ARG gputype="generic"

#Environment
ENV imagename="mediajunkie"

# Install the software we want to have.
#
# NOTE: To create images with (proprietary) GPU drivers you have to add:
#               --build-arg gputype=amd        (For AMD)
#               --build-arg gputype=intel      (for Intel)
RUN <<END_OF_BLOCK
set -eu

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
COPY --chmod=600 configs/ssh-00-0local.conf /usr/bin/device-init.sh
COPY --chmod=600 configs/ssh-00-0local.conf /etc/ssh/sshd_config.d/00-0local.conf
COPY systemd/bootc-fetch-apply-updates.timer /usr/lib/systemd/system/bootc-fetch-apply-updates.timer
COPY skel /etc/skel

# Image signature settings
COPY --chmod=644 configs/registries-sigstore.yaml /etc/containers/registries.d/sigstore.yaml
COPY --chmod=644 configs/containers-toolbox.conf /etc/containers/toolbox.conf
COPY --chmod=644 configs/containers-policy.json /etc/containers/policy.json
COPY --chmod=644 keys/dirk1980.pub /usr/share/containers/dirk1980.pub
COPY --chmod=644 keys/dirk1980-backup.pub /usr/share/containers/dirk1980-backup.pub

# Build arguments
ARG buildid="unset"
ARG sshkeys=""

# Set labels
LABEL org.opencontainers.image.version=${buildid}
LABEL org.opencontainers.image.authors="Dirk Gottschalk"
LABEL org.opencontainers.image.name=${imagename}
LABEL org.opencontainers.image.desciption="A bootc based media player image"

# Pull BluRay keydb.
RUN <<END_OF_BLOCK
set -eu
mkdir -p /etc/skel/.config/aacs
curl -k https://vlc-bluray.whoknowsmy.name/files/KEYDB.cfg -o /etc/skel/.config/aacs/KEYDB.cfg
END_OF_BLOCK

# Assume Raspberry PI if building aarch64. At least for now.
RUN --mount=type=bind,source=./scripts,target=/scripts <<EORUN
set -eu

if [ "$(arch)" == "aarch64" ]; then
	dnf install -y bcm2711-firmware uboot-images-armv8
	cp -P /usr/share/uboot/rpi_arm64/u-boot.bin /boot/efi/rpi-u-boot.bin
	mkdir -p /usr/lib/bootc-raspi-firmwares
	cp -a /boot/efi/. /usr/lib/bootc-raspi-firmwares/
	dnf remove -y bcm2711-firmware uboot-images-armv8
	mkdir /usr/bin/bootupctl-orig
	mv /usr/bin/bootupctl /usr/bin/bootupctl-orig/
	cp /scripts/bootupctl-shim /usr/bin/bootupctl
fi
EORUN

RUN <<END_OF_BLOCK
set -eu

echo "IMAGE_ID=$imagename}" >>/usr/lib/os-release
echo "IMAGE_VERSION=$buildid" >>/usr/lib/os-release

if [[ -n "$sshkeys" ]]; then
	mkdir -p /usr/ssh
	echo $sshkeys > /usr/ssh/root.pub
fi

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
	bootloader-update.service

# Setup Firewall
firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit}

# Clean up.
rm -rf /var/{cache,log,tmp,spool}/*
END_OF_BLOCK

RUN bootc container lint
