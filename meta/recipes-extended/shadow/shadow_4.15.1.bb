require shadow.inc

# Build falsely assumes that if --enable-libpam is set, we don't need to link against
# libcrypt. This breaks chsh.
BUILD_LDFLAGS:append:class-target = " ${@bb.utils.contains('DISTRO_FEATURES', 'pam', '-lcrypt', '', d)}"

# Force static linking of utilities so we can use from the sysroot/sstate for useradd
# without worrying about the dependency libraries being available
do_compile:prepend:class-native () {
	sed -i -e 's#\(LIBS.*\)-lbsd#\1 ${STAGING_LIBDIR}/libbsd.a ${STAGING_LIBDIR}/libmd.a#g' \
	       -e 's#\(LIBBSD.*\)-lbsd#\1 ${STAGING_LIBDIR}/libbsd.a ${STAGING_LIBDIR}/libmd.a#g' ${B}/*/Makefile

}

BBCLASSEXTEND = "native nativesdk"

# https://bugzilla.redhat.com/show_bug.cgi?id=884658
CVE_STATUS[CVE-2013-4235] = "upstream-wontfix: Severity is low and marked as closed and won't fix."
