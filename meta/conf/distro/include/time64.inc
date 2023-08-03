# To simulate Y2038 occurring in qemu, add to your build configuration:
# QB_OPT_APPEND:append = " -rtc base=2040-02-02"
#
# Note that this does result in ptest failures on qemux86:
#
# (none known at this point)
#
# and some ptest failures appear in qemux86-64 as well:
#
# openssl https://github.com/openssl/openssl/issues/21671
#
# Working to address those (before Y2038 rolls in) will be appreciated.
#
# Note: some issues occur on 32 bit regardless of the date set:
#
# lttng-tools ptest is not going to pass on 32 bit in any case until 2.14.x is released
#

GLIBC_64BIT_TIME_FLAGS = " -D_TIME_BITS=64 -D_FILE_OFFSET_BITS=64"

# Only needed for some 32-bit architectures, some relatively newer
# architectures do not need it ( e.g. riscv32 )
TARGET_CC_ARCH:append:arm = "${GLIBC_64BIT_TIME_FLAGS}"
TARGET_CC_ARCH:append:armeb = "${GLIBC_64BIT_TIME_FLAGS}"
TARGET_CC_ARCH:append:mipsarcho32 = "${GLIBC_64BIT_TIME_FLAGS}"
TARGET_CC_ARCH:append:powerpc = "${@bb.utils.contains('TUNE_FEATURES', 'm32', '${GLIBC_64BIT_TIME_FLAGS}', '', d)}"
TARGET_CC_ARCH:append:x86 = "${@bb.utils.contains('TUNE_FEATURES', 'm32', '${GLIBC_64BIT_TIME_FLAGS}', '', d)}"

GLIBC_64BIT_TIME_FLAGS:pn-glibc = ""
GLIBC_64BIT_TIME_FLAGS:pn-glibc-y2038-tests = ""
GLIBC_64BIT_TIME_FLAGS:pn-glibc-testsuite = ""
# pipewire-v4l2 explicitly sets _FILE_OFFSET_BITS=32 to get access to
# both 32 and 64 bit file APIs.  But it does not handle the time side?
# Needs further investigation
GLIBC_64BIT_TIME_FLAGS:pn-pipewire = ""
# Pulseaudio override certain LFS64 functions e.g. open64 and intentionally
# undefines _FILE_OFFSET_BITS, which wont work when _TIME_BITS=64 is set
# See https://gitlab.freedesktop.org/pulseaudio/pulseaudio/-/issues/3770
GLIBC_64BIT_TIME_FLAGS:pn-pulseaudio = ""
# Undefines _FILE_OFFSET_BITS on purpose in
# libsanitizer/sanitizer_common/sanitizer_platform_limits_posix.cpp
GLIBC_64BIT_TIME_FLAGS:pn-gcc-sanitizers = ""

# Caused by the flags exceptions above
INSANE_SKIP:append:pn-gcc-sanitizers = " 32bit-time"
INSANE_SKIP:append:pn-glibc = " 32bit-time"
INSANE_SKIP:append:pn-glibc-y2038-tests = " 32bit-time"
INSANE_SKIP:append:pn-pulseaudio = " 32bit-time"

# Strace has tests that call 32 bit API directly, which is fair enough, e.g.
# /usr/lib/strace/ptest/tests/ioctl_termios uses 32-bit api 'ioctl'
INSANE_SKIP:append:pn-strace = " 32bit-time"

# Additionally cargo_common class (i.e. everything written in rust)
# has the same INSANE_SKIP setting.
# Please check the comment in meta/classes-recipe/cargo_common.bbclass
# for information about why, and the overall Y2038 situation in rust.
