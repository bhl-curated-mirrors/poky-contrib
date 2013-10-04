# syslinux.bbclass
# Copyright (C) 2004-2006, Advanced Micro Devices, Inc.  All Rights Reserved
# Released under the MIT license (see packages/COPYING)

# Provide syslinux specific functions for building bootable images.

# External variables
# ${INITRD} - indicates a filesystem image to use as an initrd (optional)
# ${ROOTFS} - indicates a filesystem image to include as the root filesystem (optional)
# ${AUTO_SYSLINUXMENU} - set this to 1 to enable creating an automatic menu
# ${LABELS} - a list of targets for the automatic config
# ${APPEND} - an override list of append strings for each label
# ${SYSLINUX_OPTS} - additional options to add to the syslinux file ';' delimited
<<<<<<< HEAD
# ${SYSLINUX_SPLASH} - A background for the vga boot menu if using the boot menu
# ${SYSLINUX_SERIAL} - Set an alternate serial port or turn off serial with empty string
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

do_bootimg[depends] += "syslinux:do_populate_sysroot \
                        syslinux-native:do_populate_sysroot"

SYSLINUXCFG  = "${S}/syslinux.cfg"
<<<<<<< HEAD

ISOLINUXDIR = "/isolinux"
SYSLINUXDIR = "/"
SYSLINUX_SERIAL ?= "0 115200"
=======
SYSLINUXMENU = "${S}/menu"

ISOLINUXDIR = "/isolinux"
SYSLINUXDIR = "/"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
ISO_BOOTIMG = "isolinux/isolinux.bin"
ISO_BOOTCAT = "isolinux/boot.cat"
MKISOFS_OPTIONS = "-no-emul-boot -boot-load-size 4 -boot-info-table"
APPEND_prepend = " ${SYSLINUX_ROOT} "

syslinux_populate() {
	DEST=$1
	BOOTDIR=$2
	CFGNAME=$3

	install -d ${DEST}${BOOTDIR}

	# Install the config files
	install -m 0644 ${SYSLINUXCFG} ${DEST}${BOOTDIR}/${CFGNAME}
<<<<<<< HEAD
=======
	if [ -f ${SYSLINUXMENU} ]; then
		install -m 0644 ${SYSLINUXMENU} ${DEST}${BOOTDIR}
	fi
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
}

syslinux_iso_populate() {
	syslinux_populate ${ISODIR} ${ISOLINUXDIR} isolinux.cfg
<<<<<<< HEAD
	install -m 0644 ${STAGING_DATADIR}/syslinux/isolinux.bin ${ISODIR}${ISOLINUXDIR}
	if [ "${AUTO_SYSLINUXMENU}" = 1 ] ; then
		install -m 0644 ${STAGING_DATADIR}/syslinux/vesamenu.c32 ${ISODIR}${ISOLINUXDIR}/vesamenu.c32
		if [ "${SYSLINUX_SPLASH}" != "" ] ; then
			install -m 0644 ${SYSLINUX_SPLASH} ${ISODIR}${ISOLINUXDIR}/splash.lss
		fi
	fi
=======
	install -m 0644 ${STAGING_LIBDIR}/syslinux/isolinux.bin ${ISODIR}${ISOLINUXDIR}
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
}

syslinux_hddimg_populate() {
	syslinux_populate ${HDDDIR} ${SYSLINUXDIR} syslinux.cfg
<<<<<<< HEAD
	install -m 0444 ${STAGING_DATADIR}/syslinux/ldlinux.sys ${HDDDIR}${SYSLINUXDIR}/ldlinux.sys
	if [ "${AUTO_SYSLINUXMENU}" = 1 ] ; then
		install -m 0644 ${STAGING_DATADIR}/syslinux/vesamenu.c32 ${HDDDIR}${SYSLINUXDIR}/vesamenu.c32
		if [ "${SYSLINUX_SPLASH}" != "" ] ; then
			install -m 0644 ${SYSLINUX_SPLASH} ${HDDDIR}${SYSLINUXDIR}/splash.lss
		fi
	fi
=======
	install -m 0444 ${STAGING_LIBDIR}/syslinux/ldlinux.sys ${HDDDIR}${SYSLINUXDIR}/ldlinux.sys
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
}

syslinux_hddimg_install() {
	syslinux ${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.hddimg
}

<<<<<<< HEAD
syslinux_hdddirect_install() {
	DEST=$1
	syslinux $DEST
=======
python build_syslinux_menu () {
    import copy
    import sys

    workdir = d.getVar('WORKDIR', True)
    if not workdir:
        bb.error("WORKDIR is not defined")
        return
        
    labels = d.getVar('LABELS', True)
    if not labels:
        bb.debug(1, "LABELS not defined, nothing to do")
        return
    
    if labels == []:
        bb.debug(1, "No labels, nothing to do")
        return

    cfile = d.getVar('SYSLINUXMENU', True)
    if not cfile:
        raise bb.build.FuncFailed('Unable to read SYSLINUXMENU')

    try:
        cfgfile = file(cfile, 'w')
    except OSError:
        raise bb.build.funcFailed('Unable to open %s' % (cfile))

    # Beep the speaker and Clear the screen
    cfgfile.write('\x07\x0C')

    # The title should be configurable
    cfgfile.write('Linux Boot Menu\n')
    cfgfile.write('The following targets are available on this image:\n')
    cfgfile.write('\n')

    for label in labels.split():
        from copy import deepcopy
        localdata = deepcopy(d)

        overrides = localdata.getVar('OVERRIDES')
        if not overrides:
            raise bb.build.FuncFailed('OVERRIDES not defined')
        overrides = localdata.expand(overrides)
    
        localdata.setVar('OVERRIDES', label + ':' + overrides)
        bb.data.update_data(localdata)

        usage = localdata.getVar('USAGE', True)
        cfgfile.write('  \x0F\x30\x3E%16s\x0F\x30\x37: ' % (label))
        cfgfile.write('%s\n' % (usage))

        del localdata

    cfgfile.write('\n')
    cfgfile.close()
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
}

python build_syslinux_cfg () {
    import copy
    import sys

    workdir = d.getVar('WORKDIR', True)
    if not workdir:
        bb.error("WORKDIR not defined, unable to package")
        return
        
    labels = d.getVar('LABELS', True)
    if not labels:
        bb.debug(1, "LABELS not defined, nothing to do")
        return
    
    if labels == []:
        bb.debug(1, "No labels, nothing to do")
        return

    cfile = d.getVar('SYSLINUXCFG', True)
    if not cfile:
        raise bb.build.FuncFailed('Unable to read SYSLINUXCFG')

    try:
        cfgfile = file(cfile, 'w')
    except OSError:
        raise bb.build.funcFailed('Unable to open %s' % (cfile))

    cfgfile.write('# Automatically created by OE\n')

    opts = d.getVar('SYSLINUX_OPTS', True)

    if opts:
        for opt in opts.split(';'):
            cfgfile.write('%s\n' % opt)

    cfgfile.write('ALLOWOPTIONS 1\n');
<<<<<<< HEAD
    syslinux_serial = d.getVar('SYSLINUX_SERIAL', True)
    if syslinux_serial:
        cfgfile.write('SERIAL %s\n' % syslinux_serial)

    menu = d.getVar('AUTO_SYSLINUXMENU', True)

    if menu and syslinux_serial:
        cfgfile.write('DEFAULT Graphics console %s\n' % (labels.split()[0]))
    else:
        cfgfile.write('DEFAULT %s\n' % (labels.split()[0]))
=======
    cfgfile.write('DEFAULT %s\n' % (labels.split()[0]))
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

    timeout = d.getVar('SYSLINUX_TIMEOUT', True)

    if timeout:
        cfgfile.write('TIMEOUT %s\n' % timeout)
    else:
        cfgfile.write('TIMEOUT 50\n')

    prompt = d.getVar('SYSLINUX_PROMPT', True)
    if prompt:
        cfgfile.write('PROMPT %s\n' % prompt)
    else:
        cfgfile.write('PROMPT 1\n')

<<<<<<< HEAD
    if menu:
        cfgfile.write('ui vesamenu.c32\n')
        cfgfile.write('menu title Select kernel options and boot kernel\n')
        cfgfile.write('menu tabmsg Press [Tab] to edit, [Return] to select\n')
        splash = d.getVar('SYSLINUX_SPLASH', True)
        if splash:
            cfgfile.write('menu background splash.lss\n')
=======
    menu = d.getVar('AUTO_SYSLINUXMENU', True)

    # This is ugly.  My bad.

    if menu:
        bb.build.exec_func('build_syslinux_menu', d)
        mfile = d.getVar('SYSLINUXMENU', True)
        cfgfile.write('DISPLAY %s\n' % (mfile.split('/')[-1]) )
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
    
    for label in labels.split():
        localdata = bb.data.createCopy(d)

        overrides = localdata.getVar('OVERRIDES', True)
        if not overrides:
            raise bb.build.FuncFailed('OVERRIDES not defined')
<<<<<<< HEAD

        localdata.setVar('OVERRIDES', label + ':' + overrides)
        bb.data.update_data(localdata)
    
        btypes = [ [ "", "console=tty0" ] ]
        if menu and syslinux_serial:
            btypes = [ [ "Graphics console ", " console=tty0" ],
                [ "Serial console ",  " console=ttyS0,115200" ] ]

        for btype in btypes:
            cfgfile.write('LABEL %s%s\nKERNEL /vmlinuz\n' % (btype[0], label))

            append = localdata.getVar('APPEND', True)
            initrd = localdata.getVar('INITRD', True)

            if append:
                cfgfile.write('APPEND ')

                if initrd:
                    cfgfile.write('initrd=/initrd ')

                cfgfile.write('LABEL=%s '% (label))

                cfgfile.write('%s %s\n' % (append, btype[1]))
            else:
                cfgfile.write('APPEND %s\n' % btype[1])
=======
    
        localdata.setVar('OVERRIDES', label + ':' + overrides)
        bb.data.update_data(localdata)
    
        cfgfile.write('LABEL %s\nKERNEL /vmlinuz\n' % (label))

        append = localdata.getVar('APPEND', True)
        initrd = localdata.getVar('INITRD', True)

        if append:
            cfgfile.write('APPEND ')

            if initrd:
                cfgfile.write('initrd=/initrd ')

            cfgfile.write('LABEL=%s '% (label))

            cfgfile.write('%s\n' % (append))
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

    cfgfile.close()
}
