SUMMARY = "GTK GUI for ConnMan"
HOMEPAGE = "https://github.com/jgke/connman-gtk"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://LICENSE;md5=b234ee4d69f5fce4486a80fdaf4a4263"

DEPENDS = "gtk+3 dbus-glib"

SRCREV = "b72c6ab3bb19c07325c8e659902b046daa23c506"
SRC_URI = "git://github.com/jgke/connman-gtk.git;protocol=https;branch=master \
           file://0001-update-schema.patch \
          "
S = "${WORKDIR}/git"

inherit pkgconfig meson gsettings gtk-icon-cache features_check

ANY_OF_DISTRO_FEATURES = "${GTK3DISTROFEATURES}"

FILES:${PN} += "${datadir}/glib-2.0"
RDEPENDS:${PN} = "connman"
