SUMMARY = "ALSA sound utilities"
HOMEPAGE = "http://www.alsa-project.org"
BUGTRACKER = "http://alsa-project.org/main/index.php/Bug_Tracking"
SECTION = "console/utils"
LICENSE = "GPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=59530bdf33659b29e73d4adb9f9f6552 \
                    file://alsactl/utils.c;beginline=1;endline=20;md5=fe9526b055e246b5558809a5ae25c0b9"
DEPENDS = "alsa-lib ncurses libsamplerate0"

PACKAGECONFIG ??= "udev ${@bb.utils.filter('DISTRO_FEATURES', 'systemd', d)}"

# alsabat can be built also without fftw support (with reduced functionality).
# It would be better to always enable alsabat, but provide an option for
# enabling/disabling fftw. The configure script doesn't support that, however
# (at least in any obvious way), so for now we only support alsabat with fftw
# or no alsabat at all.
PACKAGECONFIG[bat] = "--enable-bat,--disable-bat,fftwf"

PACKAGECONFIG[udev] = "--with-udev-rules-dir=`unset PKG_CONFIG_SYSROOT_DIR; pkg-config --variable=udevdir udev`/rules.d,,udev"
PACKAGECONFIG[manpages] = "--enable-xmlto, --disable-xmlto, xmlto-native docbook-xml-dtd4-native docbook-xsl-stylesheets-native"
PACKAGECONFIG[systemd] = "--with-systemdsystemunitdir=${systemd_unitdir}/system/,,systemd"

SRC_URI = "ftp://ftp.alsa-project.org/pub/utils/alsa-utils-${PV}.tar.bz2 \
           file://0001-alsactl-don-t-let-systemd-unit-restore-the-volume-wh.patch \
          "

SRC_URI[md5sum] = "dfe6ea147a5e07a056919591c2f5dac3"
SRC_URI[sha256sum] = "320bd285e91db6e7fd7db3c9ec6f55b02f35449ff273c7844780ac6a5a3de2e8"

# On build machines with python-docutils (not python3-docutils !!) installed
# rst2man (not rst2man.py) is detected and compile fails with
# | make[1]: *** No rule to make target 'alsaucm.1', needed by 'all-am'.  Stop.
# Avoid this by disabling expicitly
EXTRA_OECONF = "--disable-rst2man"

inherit autotools gettext pkgconfig manpages

# This are all packages that we need to make. Also, the now empty alsa-utils
# ipk depends on them.

ALSA_UTILS_PKGS = "\
             ${@bb.utils.contains('PACKAGECONFIG', 'bat', 'alsa-utils-alsabat', '', d)} \
             alsa-utils-alsamixer \
             alsa-utils-alsatplg \
             alsa-utils-midi \
             alsa-utils-aplay \
             alsa-utils-amixer \
             alsa-utils-aconnect \
             alsa-utils-iecset \
             alsa-utils-speakertest \
             alsa-utils-aseqnet \
             alsa-utils-aseqdump \
             alsa-utils-alsactl \
             alsa-utils-alsaloop \
             alsa-utils-alsaucm \
            "

PACKAGES += "${ALSA_UTILS_PKGS}"
RDEPENDS_${PN} += "${ALSA_UTILS_PKGS}"

FILES_${PN} = ""
FILES_alsa-utils-alsabat     = "${bindir}/alsabat"
FILES_alsa-utils-alsatplg    = "${bindir}/alsatplg"
FILES_alsa-utils-aplay       = "${bindir}/aplay ${bindir}/arecord"
FILES_alsa-utils-amixer      = "${bindir}/amixer"
FILES_alsa-utils-alsamixer   = "${bindir}/alsamixer"
FILES_alsa-utils-speakertest = "${bindir}/speaker-test ${datadir}/sounds/alsa/ ${datadir}/alsa/speaker-test/"
FILES_alsa-utils-midi        = "${bindir}/aplaymidi ${bindir}/arecordmidi ${bindir}/amidi"
FILES_alsa-utils-aconnect    = "${bindir}/aconnect"
FILES_alsa-utils-aseqnet     = "${bindir}/aseqnet"
FILES_alsa-utils-iecset      = "${bindir}/iecset"
FILES_alsa-utils-alsactl     = "${sbindir}/alsactl */udev/rules.d */*/udev/rules.d ${systemd_unitdir} ${localstatedir}/lib/alsa ${datadir}/alsa/init/"
FILES_alsa-utils-aseqdump    = "${bindir}/aseqdump"
FILES_alsa-utils-alsaloop    = "${bindir}/alsaloop"
FILES_alsa-utils-alsaucm     = "${bindir}/alsaucm"

SUMMARY_alsa-utils-alsabat      = "Command-line sound tester for ALSA sound card driver"
SUMMARY_alsa-utils-alsatplg     = "Converts topology text files into binary format for kernel"
SUMMARY_alsa-utils-aplay        = "Play (and record) sound files using ALSA"
SUMMARY_alsa-utils-amixer       = "Command-line control for ALSA mixer and settings"
SUMMARY_alsa-utils-alsamixer    = "ncurses-based control for ALSA mixer and settings"
SUMMARY_alsa-utils-speakertest  = "ALSA surround speaker test utility"
SUMMARY_alsa-utils-midi         = "Miscellaneous MIDI utilities for ALSA"
SUMMARY_alsa-utils-aconnect     = "ALSA sequencer connection manager"
SUMMARY_alsa-utils-aseqnet      = "Network client/server for ALSA sequencer"
SUMMARY_alsa-utils-iecset       = "ALSA utility for setting/showing IEC958 (S/PDIF) status bits"
SUMMARY_alsa-utils-alsactl      = "Saves/restores ALSA-settings in /etc/asound.state"
SUMMARY_alsa-utils-aseqdump     = "Shows the events received at an ALSA sequencer port"
SUMMARY_alsa-utils-alsaloop     = "ALSA PCM loopback utility"
SUMMARY_alsa-utils-alsaucm      = "ALSA Use Case Manager"

RRECOMMENDS_alsa-utils-alsactl = "alsa-states"

ALLOW_EMPTY_alsa-utils = "1"

do_install() {
	autotools_do_install

	# We don't ship this here because it requires a dependency on bash.
	# See alsa-utils-scripts_${PV}.bb
	rm ${D}${sbindir}/alsaconf
	rm ${D}${sbindir}/alsa-info.sh
	rm -f ${D}${sbindir}/alsabat-test.sh

	if ${@bb.utils.contains('PACKAGECONFIG', 'udev', 'false', 'true', d)}; then
		# This is where alsa-utils will install its rules if we don't tell it anything else.
		rm -rf ${D}${nonarch_base_libdir}/udev
		rmdir --ignore-fail-on-non-empty ${D}${nonarch_base_libdir}
	fi
}
