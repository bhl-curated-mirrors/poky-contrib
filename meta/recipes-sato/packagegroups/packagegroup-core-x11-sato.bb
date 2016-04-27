#
# Copyright (C) 2007-2008 OpenedHand Ltd.
#

SUMMARY = "Sato desktop"
PR = "r33"

PACKAGE_ARCH = "${MACHINE_ARCH}"

inherit packagegroup distro_features_check
REQUIRED_DISTRO_FEATURES = "x11"

PACKAGES = "${PN} ${PN}-base ${PN}-apps ${PN}-games"

RDEPENDS_${PN} = "\
    ${PN}-base \
    ${PN}-apps \
    ${PN}-games \
    "

NETWORK_MANAGER ?= "connman-gnome"
NETWORK_MANAGER_libc-uclibc = ""

SUMMARY_${PN}-base = "Sato desktop - base packages"
RDEPENDS_${PN}-base = "\
    matchbox-desktop \
    matchbox-session-sato \
    matchbox-keyboard \
    matchbox-keyboard-applet \
    matchbox-keyboard-im \
    matchbox-config-gtk \
    xcursor-transparent-theme \
    gnome-theme-adwaita \
    adwaita-icon-theme \
    settings-daemon \
    shutdown-desktop \
    libsdl \
    ${NETWORK_MANAGER} \
    udev-extraconf \
    ${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', 'pulseaudio-server pulseaudio-client-conf-sato pulseaudio-misc', '', d)} \
    "

FILEMANAGER ?= "pcmanfm"

WEB ?= ""
#WEB = "epiphany"

SUMMARY_${PN}-apps = "Sato desktop - applications"
RDEPENDS_${PN}-apps = "\
    l3afpad \
    gst-player-bin \
    matchbox-terminal \
    sato-screenshot \
    ${FILEMANAGER} \
    ${WEB} \
    "

SUMMARY_${PN}-games = "Sato desktop - games"
RDEPENDS_${PN}-games = "\
    puzzles \
    "
