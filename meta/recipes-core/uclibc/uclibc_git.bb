require uclibc.inc
require uclibc-package.inc
require uclibc-git.inc

STAGINGCC = "gcc-cross-initial"
<<<<<<< HEAD
STAGINGCC_class-nativesdk = "gcc-crosssdk-initial"
=======
STAGINGCC_virtclass-nativesdk = "gcc-crosssdk-initial"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

PROVIDES += "virtual/libc virtual/${TARGET_PREFIX}libc-for-gcc"

DEPENDS = "virtual/${TARGET_PREFIX}binutils \
           virtual/${TARGET_PREFIX}gcc-initial \
           virtual/${TARGET_PREFIX}libc-initial \
<<<<<<< HEAD
           linux-libc-headers ncurses-native \
           kern-tools-native"
=======
           linux-libc-headers ncurses-native"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

RDEPENDS_${PN}-dev = "linux-libc-headers-dev"
RPROVIDES_${PN}-dev += "libc-dev virtual-libc-dev"
# uclibc does not really have libsegfault but then using the one from glibc is also not
# going to work. So we pretend that we have it to make bitbake not pull other recipes
# to satisfy this dependency for the images/tasks

RPROVIDES_${PN} += "libsegfault rtld(GNU_HASH)"
