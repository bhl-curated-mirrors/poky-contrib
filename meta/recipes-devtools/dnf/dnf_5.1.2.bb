SUMMARY = "Command-line package manager"
HOMEPAGE = "https://github.com/rpm-software-management/dnf"
# TODO: split the packages so we can add OR LGPL to the right pieces
LICENSE = "GPL-2.0-or-later & LGPL-2.1-or-later"
LIC_FILES_CHKSUM = "file://COPYING.md;md5=a269fa07bd73176fceeabb4513111a51"

SRC_URI = "git://github.com/rpm-software-management/dnf5/;protocol=https;branch=main"
SRCREV = "3b81d0d66972b72f7f883e3a57a97d62239b69e3"

S = "${WORKDIR}/git"

inherit cmake pkgconfig bash-completion

DEPENDS = "toml11 fmt libsolv sqlite3 json-c libmodulemd librepo rpm glib-2.0"

# shouldn't need comps, disable here and libsolv when https://github.com/rpm-software-management/dnf5/issues/274 fixed
PACKAGECONFIG ??= "comps"
PACKAGECONFIG[comps] = "-DWITH_COMPS=ON,-DWITH_COMPS=OFF,libxml2"
PACKAGECONFIG[zchunk] = "-DWITH_ZCHUNK=ON,-DWITH_ZCHUNK=OFF,zchunk"

# TODO api docs with doxygen
EXTRA_OECMAKE += "-DWITH_HTML=OFF -DWITH_MAN=OFF"

EXTRA_OECMAKE += "-DWITH_TESTS=OFF -DWITH_PERL5=OFF -DWITH_PYTHON3=OFF -DWITH_RUBY=OFF -DWITH_GO=OFF"
EXTRA_OECMAKE += "-DWITH_DNF5DAEMON_CLIENT=OFF -DWITH_DNF5DAEMON_SERVER=OFF"

FILES:${PN} += "${datadir}/dnf5 ${libdir}/dnf5/plugins ${libdir}/libdnf5/plugins"

BBCLASSEXTEND = "native nativesdk"
