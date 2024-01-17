SUMMARY = "Library for obtaining the call-chain of a program"
DESCRIPTION = "a portable and efficient C programming interface (API) to determine the call-chain of a program"
HOMEPAGE = "http://www.nongnu.org/libunwind"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=2d80c8ed4062b8339b715f90fa68cc9f"
DEPENDS:append:libc-musl = " libucontext"

SRC_URI = "https://github.com/libunwind/libunwind/releases/download/v${PV}/libunwind-${PV}.tar.gz \
           file://mips-byte-order.patch \
           file://mips-coredump-register.patch \
           file://0001-Handle-musl-on-PPC32.patch \
           file://linux-musl.patch \
           file://force-enable-man.patch \
           "

SRC_URI[sha256sum] = "b6b3df40a0970c8f2865fb39aa2af7b5d6f12ad6c5774e266ccca4d6b8b72268"

inherit autotools multilib_header

COMPATIBLE_HOST:riscv32 = "null"

PACKAGECONFIG ??= ""
PACKAGECONFIG[lzma] = "--enable-minidebuginfo,--disable-minidebuginfo,xz"
PACKAGECONFIG[zlib] = "--enable-zlibdebuginfo,--disable-zlibdebuginfo,zlib"

EXTRA_OECONF = "--enable-static"

# http://errors.yoctoproject.org/Errors/Details/20487/
ARM_INSTRUCTION_SET:armv4 = "arm"
ARM_INSTRUCTION_SET:armv5 = "arm"

LDFLAGS += "-Wl,-z,relro,-z,now ${@bb.utils.contains('DISTRO_FEATURES', 'ld-is-gold', ' -fuse-ld=bfd ', '', d)}"

DEPENDS:append:libc-musl:powerpc = " libatomic-ops"
LDFLAGS:append:libc-musl:powerpc = " -latomic"

SECURITY_LDFLAGS:append:libc-musl = " -lssp_nonshared"

do_install:append () {
	oe_multilib_header libunwind.h
}

BBCLASSEXTEND = "native"
