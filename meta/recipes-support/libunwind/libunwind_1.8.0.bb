require libunwind.inc

SRC_URI = "https://github.com/libunwind/libunwind/releases/download/v${PV}/libunwind-${PV}.tar.gz \
           file://0003-x86-Stub-out-x86_local_resume.patch;apply=0 \
           file://0004-Fix-build-on-mips-musl.patch;apply=0 \
           file://0005-ppc32-Consider-ucontext-mismatches-between-glibc-and.patch;apply=0 \
           file://0006-Fix-for-X32.patch;apply=0 \
           file://install-tests.patch \
           file://sve.patch \
           "
SRC_URI:append:libc-musl = " file://musl-header-conflict.patch;apply=0"

SRC_URI[sha256sum] = "b6b3df40a0970c8f2865fb39aa2af7b5d6f12ad6c5774e266ccca4d6b8b72268"

EXTRA_OECONF = "--enable-static"

# http://errors.yoctoproject.org/Errors/Details/20487/
ARM_INSTRUCTION_SET:armv4 = "arm"
ARM_INSTRUCTION_SET:armv5 = "arm"

COMPATIBLE_HOST:riscv32 = "null"

LDFLAGS += "-Wl,-z,relro,-z,now ${@bb.utils.contains('DISTRO_FEATURES', 'ld-is-gold', ' -fuse-ld=bfd ', '', d)}"

SECURITY_LDFLAGS:append:libc-musl = " -lssp_nonshared"
CACHED_CONFIGUREVARS:append:libc-musl = " LDFLAGS='${LDFLAGS} -lucontext'"

do_install:append() {
    makefile-getvar ${B}/tests/Makefile TESTS | sed s/run-check-namespace// >${D}${libexecdir}/${BPN}/tests
}
