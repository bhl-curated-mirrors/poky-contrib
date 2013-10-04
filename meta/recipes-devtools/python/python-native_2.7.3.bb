require python.inc

EXTRANATIVEPATH += "bzip2-native"
DEPENDS = "openssl-native bzip2-replacement-native zlib-native readline-native sqlite3-native"
PR = "${INC_PR}.1"

<<<<<<< HEAD
SRC_URI += "\
=======
SRC_URI += "file://04-default-is-optimized.patch \
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
           file://05-enable-ctypes-cross-build.patch \
           file://06-ctypes-libffi-fix-configure.patch \
           file://10-distutils-fix-swig-parameter.patch \
           file://11-distutils-never-modify-shebang-line.patch \
           file://12-distutils-prefix-is-inside-staging-area.patch \
           file://debug.patch \
           file://unixccompiler.patch \
           file://nohostlibs.patch \
           file://multilib.patch \
           file://add-md5module-support.patch \
<<<<<<< HEAD
           file://builddir.patch \
           "
S = "${WORKDIR}/Python-${PV}"

FILESPATH = "${FILE_DIRNAME}/python-native/:${FILE_DIRNAME}/python/"

inherit native

RPROVIDES += "python-distutils-native python-compression-native python-textutils-native python-codecs-native python-core-native"
=======
           "
S = "${WORKDIR}/Python-${PV}"

inherit native

RPROVIDES += "python-distutils-native python-compression-native python-textutils-native python-core-native"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

EXTRA_OECONF_append = " --bindir=${bindir}/${PN}"

EXTRA_OEMAKE = '\
  BUILD_SYS="" \
  HOST_SYS="" \
  LIBC="" \
  STAGING_LIBDIR=${STAGING_LIBDIR_NATIVE} \
  STAGING_INCDIR=${STAGING_INCDIR_NATIVE} \
'

do_configure_prepend() {
	autoreconf --verbose --install --force --exclude=autopoint Modules/_ctypes/libffi || bbnote "_ctypes failed to autoreconf"
}

do_install() {
	oe_runmake 'DESTDIR=${D}' install
	install -d ${D}${bindir}/${PN}
	install -m 0755 Parser/pgen ${D}${bindir}/${PN}

	# Make sure we use /usr/bin/env python
	for PYTHSCRIPT in `grep -rIl ${bindir}/${PN}/python ${D}${bindir}/${PN}`; do
		sed -i -e '1s|^#!.*|#!/usr/bin/env python|' $PYTHSCRIPT
	done
<<<<<<< HEAD

	# Add a symlink to the native Python so that scripts can just invoke
	# "nativepython" and get the right one without needing absolute paths
	# (these often end up too long for the #! parser in the kernel as the
	# buffer is 128 bytes long).
	ln -s python-native/python ${D}${bindir}/nativepython
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
}
