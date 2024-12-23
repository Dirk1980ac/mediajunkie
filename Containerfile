# We use the 'latest' tag from fedora bootc which refers to the actual fedora release.
FROM registry.fedoraproject.org/fedora-bootc:latest

# Will later be used te generate GPU specific images
ARG GPUTYPE="generic"

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

# install the software we want to have, set the firewall and install some additional
# RPMFusion packages.
#
# TODO: Address the GPU problem somehow
#
# NOTE: This does not install gpu specific drivers at the moment. Raspberry Pi
#		is fully supported out of the box.
#       DNF complains about already existing files for package 'rootfiles' and
#       fails with an error. So we just exlude this package for now.
RUN dnf install -y lightdm firewalld freeipa-client glibc-langpack-de kodi \
	kodi-firewalld 	kodi-inputstream-adaptive kodi-inputstream-rtmp \
	kodi-pvr-iptvsimple cockpit cockpit-storaged realmd watchdog \
	greenboot greenboot-default-health-checks fedora-remix-logos \
	usbutils --setopt="install_weak_deps=False" && \
	dnf -y install rpmfusion-free-release-tainted \
	rpmfusion-nonfree-release-tainted && \
	dnf -y install libdvdcss &&\
	dnf -y --repo=rpmfusion-nonfree-tainted install "*-firmware" && \
	dnf clean all -y && \
	firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit,ssh} && \
	systemctl enable cockpit.socket sshd watchdog greenboot-task-runner \
	greenboot-healthcheck greenboot-status greenboot-loading-message \
	greenboot-grub2-set-counter greenboot-grub2-set-success \
	greenboot-rpm-ostree-grub2-check-fallback redboot-auto-reboot \
	redboot-task-runner

# Let's lay back in our rocking chair whiile the magic does it's work
