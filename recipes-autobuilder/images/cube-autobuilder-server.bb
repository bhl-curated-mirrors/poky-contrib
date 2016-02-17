dSUMMARY = "A container image for the yocto-autobuilder which can build itself"
DESCRIPTION = "Launched from the essential image, this is a container image \
               which provides a working yocto-autobuilder that can produce and 
	       deploy itself. \
              "
HOMEPAGE = "http://www.yoctoproject.org"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/LICENSE;md5=4d92cd373abda3937c2bc47fbc49d690 \
                    file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

IMAGE_FEATURES += "package-management doc-pkgs x11-base"
IMAGE_FSTYPES = "tar.bz2"

PACKAGE_EXCLUDE = "busybox*"

# Exclude documention packages, which can be installed later
PACKAGE_EXCLUDE_COMPLEMENTARY = "ruby|ruby-shadow|puppet|hiera|facter"

CUBE_AUTOBUILDER_SERVER_EXTRA_INSTALL ?= ""

IMAGE_INSTALL += "packagegroup-core-boot \
                        packagegroup-dom0 \
                        packagegroup-util-linux \
                        packagegroup-core-ssh-openssh \
                        packagegroup-core-full-cmdline \
                        packagegroup-builder \
                        packagegroup-xfce \
                        packagegroup-container \
                        packagegroup-container \
                        packagegroup-self-hosted \
                        ntp \
                        ntpdate \
                        ntp-utils \
			yocto-autobuilder \
                        ${CUBE_AUTOBUILDER_SERVER_EXTRA_INSTALL} \
                       "

XSERVER_append = "xserver-xorg \
                  xserver-xorg-extension-dri \
                  xserver-xorg-extension-dri2 \
                  xserver-xorg-extension-glx \
                  xserver-xorg-extension-extmod \
                  xserver-xorg-extension-dbe \
                  xserver-xorg-module-libint10 \
                  xf86-input-evdev \
                  xf86-input-keyboard \
                  xf86-input-mouse \
                  xf86-input-synaptics \
                  xf86-input-vmmouse \
                  xf86-video-ati \
                  xf86-video-fbdev \
                  xf86-video-intel \
                  xf86-video-mga \
                  xf86-video-modesetting \
                  xf86-video-nouveau \
                  xf86-video-vesa \
                  xf86-video-vmware \
                 "

ALTERNATIVE_PRIORITY_xfce4-session[x-session-manager] = "60"

inherit core-image
inherit builder-base
