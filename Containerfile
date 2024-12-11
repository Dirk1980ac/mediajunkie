# We use the 'latest'  tag from fedora bootc which refers to the actual fedora release.
FROM registry.fedoraproject.org/fedora-bootc:latest

# Will later be used te generate GPU specific images
ARG GPUTYPE="generic"

# Build ID to identify the generated image
ARG buildid


# Set some image labels for identification
LABEL image.name="MediaJunkie"
LABEL image.release-status="alpha"
LABEL vendor.name="Dirk Gottschalk"
LABEL vendor.email="dirk.gottschalk1980@googlemail.com"
LABEL image.build-id="$buildid"

# Copy the prepared stuff we need into the image
COPY etc /etc

# install the software we want to have, set the firewall and install some additional
# RPMFusion packages.
#
# NOTE: This does not install gpu specific drivers at the moment. Raspberry Pi is
#       fully supported out of the box.
#
# TODO: Address the GPU problem somehow
RUN dnf -y group install sound-and-video && \
	dnf install -y lxdm firewalld freeipa-client glibc-langpack-de kodi \
	kodi-firewalld 	kodi-inputstream-adaptive kodi-inputstream-rtmp \
	kodi-pvr-iptvsimple cockpit cockpit-storaged realmd && \
	dnf -y install rpmfusion-free-release-tainted && \
	dnf -y install libdvdcss  &&\
	dnf -y install rpmfusion-nonfree-release-tainted && \
	dnf -y --repo=rpmfusion-nonfree-tainted install "*-firmware" --skip-broken && \
	dnf -y remove rpm-ostree flatpak && \
	dnf clean all -y && \
	firewall-offline-cmd --add-service={kodi-http,kodi-jsonrpc,cockpit} && \
	systemctl enable cockpit

# Let's lay back in our rocking chair whiile the magic does it's work
