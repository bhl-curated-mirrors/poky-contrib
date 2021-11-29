SUMMARY = "OpenGL function pointer management library"
DESCRIPTION = "It hides the complexity of dlopen(), dlsym(), \
glXGetProcAddress(), eglGetProcAddress(), etc. from the app developer, with \
very little knowledge needed on their part. They get to read GL specs and \
write code using undecorated function names like glCompileShader()."
HOMEPAGE = "https://github.com/anholt/libepoxy/"
SECTION = "libs"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=58ef4c80d401e07bd9ee8b6b58cf464b"

SRC_URI = "git://github.com/anholt/libepoxy;branch=master;protocol=https"
SRCREV = "c84bc9459357a40e46e2fec0408d04fbdde2c973"
S = "${WORKDIR}/git"

inherit meson pkgconfig github-releases

PACKAGECONFIG ??= "${@bb.utils.contains('DISTRO_FEATURES', 'api-documentation', 'docs', '', d} \
                   ${@bb.utils.contains('DISTRO_FEATURES', 'opengl', 'egl', '', d)} \
                   ${@bb.utils.contains('DISTRO_FEATURES', 'opengl x11', 'glx x11' d)} egl"
PACKAGECONFIG[egl] = "-Degl=yes, -Degl=no, virtual/egl"
PACKAGECONFIG[glx] = "-Dglx=yes, -Dglx=no"
PACKAGECONFIG[x11] = "-Dx11=true, -Dx11=false, virtual/libx11"
PACKAGECONFIG[docs] = "-Ddocs=true, -Ddocs=false, doxygen-native"

EXTRA_OEMESON += "-Dtests=false"

PACKAGECONFIG:class-native = "egl glx x11"
PACKAGECONFIG:class-nativesdk = "egl glx x11"

BBCLASSEXTEND = "native nativesdk"
