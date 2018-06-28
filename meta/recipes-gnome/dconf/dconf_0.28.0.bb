SUMMARY = "configuation database system"
LICENSE = "LGPLv2.1"
LIC_FILES_CHKSUM = "file://COPYING;md5=2d5025d4aa3495befef8f17206a5b0a1"

SECTION = "x11/gnome"

inherit gnomebase gsettings
SRC_URI[archive.md5sum] = "81faa8e68e5ea71ff0ee75050fc0759c"
SRC_URI[archive.sha256sum] = "61d3b3865ef58b729c3b39aa0979f886c014aa8362f93dcfc74bf5648ed9c742"
GNOME_COMPRESS_TYPE = "xz"

DEPENDS = "dbus glib-2.0 libxml2 intltool-native"

inherit meson vala gtk-doc distro_features_check


EXTRA_OECONF += "--disable-man"

FILES_${PN} += " \
    ${datadir}/dbus-1 \
    ${libdir}/gio/modules/*.so \
    ${datadir}/bash-completion \
"

FILES_${PN}-dbg += "${libdir}/gio/modules/.debug/libdconfsettings.so"
