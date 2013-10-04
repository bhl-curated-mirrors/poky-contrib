inherit siteinfo

<<<<<<< HEAD
# If applicable on the architecture, this routine will rename the header and
# add a unique identifier to the name for the ABI/bitsize that is being used.
# A wrapper will be generated for the architecture that knows how to call
# all of the ABI variants for that given architecture.
#
oe_multilib_header() {
        # We use
        # For ARM: We don't support multilib builds.
        # For MIPS: "n32" is a special case, which needs to be
        # distinct from both 64-bit and 32-bit.
        case ${TARGET_ARCH} in
        arm*)   return
                ;;
        mips*)  case "${MIPSPKGSFX_ABI}" in
                "-n32")
                       ident=n32   
                       ;;
                *)     
                       ident=${SITEINFO_BITS}
                       ;;
                esac
                ;;
        *)      ident=${SITEINFO_BITS}
        esac
=======
# If applicable on the architecture, this routine will rename the header and add
# a unique identifier to the name for the ABI/bitsize that is being used.  A wrapper will
# be generated for the architecture that knows how to call all of the ABI variants for that
# given architecture.
#
# TODO: mips64 n32 is not yet recognized in this code
# when that is identified the name of the wrapped item should be "n32" and appropriately
# determined int he if coding...
#
oe_multilib_header() {
	# Do nothing on ARM, only one ABI is supported at once
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	if echo ${TARGET_ARCH} | grep -q arm; then
	    return
	fi
	for each_header in "$@" ; do
	   if [ ! -f "${D}/${includedir}/$each_header" ]; then
	      bberror "oe_multilib_header: Unable to find header $each_header."
	      continue
	   fi
	   stem=$(echo $each_header | sed 's#\.h$##')
<<<<<<< HEAD
=======
	   ident=${SITEINFO_BITS}
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	   # if mips64/n32 set ident to n32
	   mv ${D}/${includedir}/$each_header ${D}/${includedir}/${stem}-${ident}.h

	   sed -e "s#ENTER_HEADER_FILENAME_HERE#${stem}#g" ${COREBASE}/scripts/multilib_header_wrapper.h > ${D}/${includedir}/$each_header
	done
}
<<<<<<< HEAD

# Dependencies on arch variables like MIPSPKGSFX_ABI can be problematic.
# We don't need multilib headers for native builds so brute force things.
oe_multilib_header_class-native () {
	return
}
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
