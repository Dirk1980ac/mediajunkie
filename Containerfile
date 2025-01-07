# Use the 'latest' tag from fedora-bootc.
FROM registry.fedoraproject.org/fedora-bootc:latest

# Will later be used te generate GPU specific images
ARG gputype="generic"

# Build ID to identify the generated image
ARG buildid

# Set some image labels for identification
LABEL image.name="MediaJunkie"
LABEL image.descr="A bootc based media player image"
LABEL vendor.name="Dirk Gottschalk"
LABEL vendor.email="dirk.gottschalk1980@googlemail.com"
LABEL image.build-id=$buildid

# Copy the prepared stuff we need into the image
COPY etc /etc

# Install the software we want to have, set the firewall and install some
# additional RPMFusion packages.
#
# NOTE: To create images with (proprietary) GPU drivers you have to add:
#               --build-arg gputype=amd        (For AMD)
#               --build-arg gputype=intel      (for Intel)
#
# NOTE: Support for NVidia with proprietary drivers will follow later.
#

RUN <<EOF
echo "$buildid" >/etc/img-build-id
dnf install -y lightdm firewalld freeipa-client glibc-langpack-de kodi \
	kodi-firewalld 	kodi-inputstream-adaptive kodi-inputstream-rtmp \
	kodi-pvr-iptvsimple cockpit cockpit-storaged realmd watchdog greenboot \
	greenboot-default-health-checks fedora-remix-logos mc usbutils \
	zram-generator zram-generator-defaults \
	--setopt="install_weak_deps=False"
dnf -y install rpmfusion-free-release-tainted \
	rpmfusion-nonfree-release-tainted
dnf -y install libdvdcss
dnf -y --repo=rpmfusion-nonfree-tainted install "*-firmware"
dnf -y swap ffmpeg-free ffmpeg --allowerasing
if [ $gputype == "amd" ]; then
	dnf -y swap mesa-va-drivers mesa-va-drivers-freeworld
	dnf -y swap mesa-vdpau-drivers mesa-vdpau-drivers-freeworld
elif [ $gputype == "intel" ]; then
	dnf -y install intel-media-driver
fi
dnf clean all -y
firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit} && \
systemctl enable cockpit.socket sshd watchdog greenboot-task-runner \
	greenboot-healthcheck greenboot-status greenboot-loading-message \
	greenboot-grub2-set-counter greenboot-grub2-set-success \
	greenboot-rpm-ostree-grub2-check-fallback redboot-auto-reboot \
	redboot-task-runner systemd-zram-setup@zram0.service
EOF

# Let's lay back in our rocking chair while the magic does it's work
