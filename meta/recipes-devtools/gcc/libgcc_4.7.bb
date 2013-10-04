require recipes-devtools/gcc/gcc-${PV}.inc
<<<<<<< HEAD
require libgcc.inc

=======

INHIBIT_DEFAULT_DEPS = "1"

DEPENDS = "virtual/${TARGET_PREFIX}gcc virtual/${TARGET_PREFIX}g++"

PACKAGES = "\
  ${PN} \
  ${PN}-dev \
  ${PN}-dbg \
  libgcov-dev \
  "

FILES_${PN} = "${base_libdir}/libgcc*.so.*"
FILES_${PN}-dev = " \
  ${base_libdir}/libgcc*.so \
  ${libdir}/${TARGET_SYS}/${BINV}/*crt* \
  ${libdir}/${TARGET_SYS}/${BINV}/libgcc*"
FILES_libgcov-dev = " \
  ${libdir}/${TARGET_SYS}/${BINV}/libgcov.a \
  "
FILES_${PN}-dbg += "${base_libdir}/.debug/"

do_configure () {
	target=`echo ${MULTIMACH_TARGET_SYS} | sed -e s#-nativesdk##`
	install -d ${D}${base_libdir} ${D}${libdir}
	cp -fpPR ${STAGING_INCDIR_NATIVE}/gcc-build-internal-$target/* ${B}
	mkdir -p ${B}/${BPN}
	cd ${B}/${BPN}
	chmod a+x ${S}/${BPN}/configure
	${S}/${BPN}/configure ${CONFIGUREOPTS} ${EXTRA_OECONF}
}

do_compile () {
	target=`echo ${TARGET_SYS} | sed -e s#-nativesdk##`
	cd ${B}/${BPN}
	oe_runmake MULTIBUILDTOP=${B}/$target/${BPN}/
}

do_install () {
	target=`echo ${TARGET_SYS} | sed -e s#-nativesdk##`
	cd ${B}/${BPN}
	oe_runmake 'DESTDIR=${D}' MULTIBUILDTOP=${B}/$target/${BPN}/ install

	# Move libgcc_s into /lib
	mkdir -p ${D}${base_libdir}
	if [ -f ${D}${libdir}/nof/libgcc_s.so ]; then
		mv ${D}${libdir}/nof/libgcc* ${D}${base_libdir}
	else
		mv ${D}${libdir}/libgcc* ${D}${base_libdir} || true
	fi

	# install the runtime in /usr/lib/ not in /usr/lib/gcc on target
	# so that cross-gcc can find it in the sysroot

	mv ${D}${libdir}/gcc/* ${D}${libdir}
	rm -rf ${D}${libdir}/gcc/
	# unwind.h is installed here which is shipped in gcc-cross
	# as well as target gcc and they are identical so we dont
	# ship one with libgcc here
	rm -rf ${D}${libdir}/${TARGET_SYS}/${BINV}/include
}

do_package[depends] += "virtual/${MLPREFIX}libc:do_package"
do_package_write_ipk[depends] += "virtual/${MLPREFIX}libc:do_package"
do_package_write_deb[depends] += "virtual/${MLPREFIX}libc:do_package"
do_package_write_rpm[depends] += "virtual/${MLPREFIX}libc:do_package"

BBCLASSEXTEND = "nativesdk"

INSANE_SKIP_${PN}-dev = "staticdev"
INSANE_SKIP_${MLPREFIX}libgcov-dev = "staticdev"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
