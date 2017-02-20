SUMMARY = "Package manager forked from Yum, using libsolv as a dependency resolver"
LICENSE = "GPLv2"
LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263 \
                    file://PACKAGE-LICENSING;md5=bfc29916e11321be06924c4fb096fdcc \
                   "

SRC_URI = "git://github.com/rpm-software-management/dnf.git \
           file://0028-Use-backports.lzma-not-lzma.patch \
           file://0029-Do-not-set-PYTHON_INSTALL_DIR-by-running-python.patch \
           file://0030-Run-python-scripts-using-env.patch \
           file://0001-Do-not-prepend-installroot-to-logdir.patch \
           file://0001-Do-not-hardcode-etc-and-systemd-unit-directories.patch \
           file://0001-Corretly-install-tmpfiles.d-configuration.patch \
           "

PV = "2.0.0+git${SRCPV}"
SRCREV = "f0093d672d3069cfee8447973ae70ef615fd8886"

S = "${WORKDIR}/git"

inherit cmake gettext bash-completion distutils-base systemd

DEPENDS += "libdnf librepo libcomps python-pygpgme python-iniparse"
# python 2.x only, drop when moving to python 3.x
DEPENDS += "python-backports-lzma"

# manpages generation requires http://www.sphinx-doc.org/
EXTRA_OECMAKE = " -DWITH_MAN=0 -DPYTHON_INSTALL_DIR=${PYTHON_SITEPACKAGES_DIR}"

BBCLASSEXTEND = "native nativesdk"

RDEPENDS_${PN}_class-target += "python-core python-codecs python-netclient python-email python-threading python-distutils librepo python-shell python-subprocess libcomps libdnf python-sqlite3 python-compression python-pygpgme python-backports-lzma python-rpm python-iniparse python-json python-importlib python-curses python-argparse"

# Direct dnf-native to read rpm configuration from our sysroot, not the one it was compiled in
do_install_append_class-native() {
        create_wrapper ${D}/${bindir}/dnf-2 \
                RPM_CONFIGDIR=${STAGING_LIBDIR_NATIVE}/rpm \
                RPM_NO_CHROOT_FOR_SCRIPTS=1
}

