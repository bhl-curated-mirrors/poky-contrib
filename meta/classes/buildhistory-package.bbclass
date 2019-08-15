BUILDHISTORY_DIR_PACKAGE = "${BUILDHISTORY_DIR}/packages/${MULTIMACH_TARGET_SYS}/${PN}"

BUILDHISTORY_OLD_DIR_PACKAGE = "${BUILDHISTORY_OLD_DIR}/packages/${MULTIMACH_TARGET_SYS}/${PN}"

SSTATEPOSTINSTFUNCS_append = " buildhistory_emit_pkghistory"
# We want to avoid influencing the signatures of sstate tasks - first the function itself:
sstate_install[vardepsexclude] += "buildhistory_emit_pkghistory"
# then the value added to SSTATEPOSTINSTFUNCS:
SSTATEPOSTINSTFUNCS[vardepvalueexclude] .= "| buildhistory_emit_pkghistory"

# All items excepts those listed here will be removed from a recipe's
# build history directory by buildhistory_emit_pkghistory(). This is
# necessary because some of these items (package directories, files that
# we no longer emit) might be obsolete.
#
# When extending build history, derive your class from buildhistory.bbclass
# and extend this list here with the additional files created by the derived
# class.
BUILDHISTORY_PRESERVE = "latest latest_srcrev sysroot"


#
# Write out the contents of the sysroot
#
buildhistory_emit_sysroot() {
	mkdir --parents ${BUILDHISTORY_DIR_PACKAGE}
	case ${CLASSOVERRIDE} in
	class-native|class-cross|class-crosssdk)
		BASE=${SYSROOT_DESTDIR}/${STAGING_DIR_NATIVE}
		;;
	*)
		BASE=${SYSROOT_DESTDIR}
		;;
	esac
	buildhistory_list_files_no_owners $BASE ${BUILDHISTORY_DIR_PACKAGE}/sysroot
}

#
# Write out metadata about this package for comparison when writing future packages
#
python buildhistory_emit_pkghistory() {
    if not d.getVar('BB_CURRENTTASK') in ['packagedata', 'packagedata_setscene']:
        return 0

    if not "package" in (d.getVar('BUILDHISTORY_FEATURES') or "").split():
        return 0

    if d.getVar('BB_CURRENTTASK') in ['populate_sysroot', 'populate_sysroot_setscene']:
        bb.build.exec_func("buildhistory_emit_sysroot", d)

    import re
    import json
    import shlex
    import errno

    pkghistdir = d.getVar('BUILDHISTORY_DIR_PACKAGE')
    oldpkghistdir = d.getVar('BUILDHISTORY_OLD_DIR_PACKAGE')

    class RecipeInfo:
        def __init__(self, name):
            self.name = name
            self.pe = "0"
            self.pv = "0"
            self.pr = "r0"
            self.depends = ""
            self.packages = ""
            self.srcrev = ""
            self.layer = ""


    class PackageInfo:
        def __init__(self, name):
            self.name = name
            self.pe = "0"
            self.pv = "0"
            self.pr = "r0"
            # pkg/pkge/pkgv/pkgr should be empty because we want to be able to default them
            self.pkg = ""
            self.pkge = ""
            self.pkgv = ""
            self.pkgr = ""
            self.size = 0
            self.depends = ""
            self.rprovides = ""
            self.rdepends = ""
            self.rrecommends = ""
            self.rsuggests = ""
            self.rreplaces = ""
            self.rconflicts = ""
            self.files = ""
            self.filelist = ""
            # Variables that need to be written to their own separate file
            self.filevars = dict.fromkeys(['pkg_preinst', 'pkg_postinst', 'pkg_prerm', 'pkg_postrm'])

    # Should check PACKAGES here to see if anything removed

    def readPackageInfo(pkg, histfile):
        pkginfo = PackageInfo(pkg)
        with open(histfile, "r") as f:
            for line in f:
                lns = line.split('=', 1)
                name = lns[0].strip()
                value = lns[1].strip(" \t\r\n").strip('"')
                if name == "PE":
                    pkginfo.pe = value
                elif name == "PV":
                    pkginfo.pv = value
                elif name == "PR":
                    pkginfo.pr = value
                elif name == "PKG":
                    pkginfo.pkg = value
                elif name == "PKGE":
                    pkginfo.pkge = value
                elif name == "PKGV":
                    pkginfo.pkgv = value
                elif name == "PKGR":
                    pkginfo.pkgr = value
                elif name == "RPROVIDES":
                    pkginfo.rprovides = value
                elif name == "RDEPENDS":
                    pkginfo.rdepends = value
                elif name == "RRECOMMENDS":
                    pkginfo.rrecommends = value
                elif name == "RSUGGESTS":
                    pkginfo.rsuggests = value
                elif name == "RREPLACES":
                    pkginfo.rreplaces = value
                elif name == "RCONFLICTS":
                    pkginfo.rconflicts = value
                elif name == "PKGSIZE":
                    pkginfo.size = int(value)
                elif name == "FILES":
                    pkginfo.files = value
                elif name == "FILELIST":
                    pkginfo.filelist = value
        # Apply defaults
        if not pkginfo.pkg:
            pkginfo.pkg = pkginfo.name
        if not pkginfo.pkge:
            pkginfo.pkge = pkginfo.pe
        if not pkginfo.pkgv:
            pkginfo.pkgv = pkginfo.pv
        if not pkginfo.pkgr:
            pkginfo.pkgr = pkginfo.pr
        return pkginfo

    def getlastpkgversion(pkg):
        try:
            histfile = os.path.join(oldpkghistdir, pkg, "latest")
            return readPackageInfo(pkg, histfile)
        except EnvironmentError:
            return None

    def sortpkglist(string):
        pkgiter = re.finditer(r'[a-zA-Z0-9.+-]+( \([><=]+[^)]+\))?', string, 0)
        pkglist = [p.group(0) for p in pkgiter]
        pkglist.sort()
        return ' '.join(pkglist)

    def sortlist(string):
        items = string.split(' ')
        items.sort()
        return ' '.join(items)

    pn = d.getVar('PN')
    pe = d.getVar('PE') or "0"
    pv = d.getVar('PV')
    pr = d.getVar('PR')
    layer = bb.utils.get_file_layer(d.getVar('FILE'), d)

    pkgdata_dir = d.getVar('PKGDATA_DIR')
    packages = ""
    try:
        with open(os.path.join(pkgdata_dir, pn)) as f:
            for line in f.readlines():
                if line.startswith('PACKAGES: '):
                    packages = oe.utils.squashspaces(line.split(': ', 1)[1])
                    break
    except IOError as e:
        if e.errno == errno.ENOENT:
            # Probably a -cross recipe, just ignore
            return 0
        else:
            raise

    packagelist = packages.split()
    preserve = d.getVar('BUILDHISTORY_PRESERVE').split()
    if not os.path.exists(pkghistdir):
        bb.utils.mkdirhier(pkghistdir)
    else:
        # Remove non-preserved files, as well as directories corresponding to packages that no longer exist
        for item in os.listdir(pkghistdir):
            if item not in preserve:
                if item not in packagelist:
                    itempath = os.path.join(pkghistdir, item)
                    if os.path.isdir(itempath):
                        for subfile in os.listdir(itempath):
                            os.unlink(os.path.join(itempath, subfile))
                        os.rmdir(itempath)
                    else:
                        os.unlink(itempath)

    rcpinfo = RecipeInfo(pn)
    rcpinfo.pe = pe
    rcpinfo.pv = pv
    rcpinfo.pr = pr
    rcpinfo.depends = sortlist(oe.utils.squashspaces(d.getVar('DEPENDS') or ""))
    rcpinfo.packages = packages
    rcpinfo.layer = layer
    write_recipehistory(rcpinfo, d)

    pkgdest = d.getVar('PKGDEST')
    for pkg in packagelist:
        pkgdata = {}
        with open(os.path.join(pkgdata_dir, 'runtime', pkg)) as f:
            for line in f.readlines():
                item = line.rstrip('\n').split(': ', 1)
                key = item[0]
                if key.endswith('_' + pkg):
                    key = key[:-len(pkg)-1]
                pkgdata[key] = item[1].encode('latin-1').decode('unicode_escape')

        pkge = pkgdata.get('PKGE', '0')
        pkgv = pkgdata['PKGV']
        pkgr = pkgdata['PKGR']
        #
        # Find out what the last version was
        # Make sure the version did not decrease
        #
        lastversion = getlastpkgversion(pkg)
        if lastversion:
            last_pkge = lastversion.pkge
            last_pkgv = lastversion.pkgv
            last_pkgr = lastversion.pkgr
            r = bb.utils.vercmp((pkge, pkgv, pkgr), (last_pkge, last_pkgv, last_pkgr))
            if r < 0:
                msg = "Package version for package %s went backwards which would break package feeds from (%s:%s-%s to %s:%s-%s)" % (pkg, last_pkge, last_pkgv, last_pkgr, pkge, pkgv, pkgr)
                package_qa_handle_error("version-going-backwards", msg, d)

        pkginfo = PackageInfo(pkg)
        # Apparently the version can be different on a per-package basis (see Python)
        pkginfo.pe = pkgdata.get('PE', '0')
        pkginfo.pv = pkgdata['PV']
        pkginfo.pr = pkgdata['PR']
        pkginfo.pkg = pkgdata['PKG']
        pkginfo.pkge = pkge
        pkginfo.pkgv = pkgv
        pkginfo.pkgr = pkgr
        pkginfo.rprovides = sortpkglist(oe.utils.squashspaces(pkgdata.get('RPROVIDES', "")))
        pkginfo.rdepends = sortpkglist(oe.utils.squashspaces(pkgdata.get('RDEPENDS', "")))
        pkginfo.rrecommends = sortpkglist(oe.utils.squashspaces(pkgdata.get('RRECOMMENDS', "")))
        pkginfo.rsuggests = sortpkglist(oe.utils.squashspaces(pkgdata.get('RSUGGESTS', "")))
        pkginfo.rreplaces = sortpkglist(oe.utils.squashspaces(pkgdata.get('RREPLACES', "")))
        pkginfo.rconflicts = sortpkglist(oe.utils.squashspaces(pkgdata.get('RCONFLICTS', "")))
        pkginfo.files = oe.utils.squashspaces(pkgdata.get('FILES', ""))
        for filevar in pkginfo.filevars:
            pkginfo.filevars[filevar] = pkgdata.get(filevar, "")

        # Gather information about packaged files
        val = pkgdata.get('FILES_INFO', '')
        dictval = json.loads(val)
        filelist = list(dictval.keys())
        filelist.sort()
        pkginfo.filelist = " ".join([shlex.quote(x) for x in filelist])

        pkginfo.size = int(pkgdata['PKGSIZE'])

        write_pkghistory(pkginfo, d)

    # Create files-in-<package-name>.txt files containing a list of files of each recipe's package
    bb.build.exec_func("buildhistory_list_pkg_files", d)
}

def write_recipehistory(rcpinfo, d):
    bb.debug(2, "Writing recipe history")

    pkghistdir = d.getVar('BUILDHISTORY_DIR_PACKAGE')

    infofile = os.path.join(pkghistdir, "latest")
    with open(infofile, "w") as f:
        if rcpinfo.pe != "0":
            f.write(u"PE = %s\n" %  rcpinfo.pe)
        f.write(u"PV = %s\n" %  rcpinfo.pv)
        f.write(u"PR = %s\n" %  rcpinfo.pr)
        f.write(u"DEPENDS = %s\n" %  rcpinfo.depends)
        f.write(u"PACKAGES = %s\n" %  rcpinfo.packages)
        f.write(u"LAYER = %s\n" %  rcpinfo.layer)

    write_latest_srcrev(d, pkghistdir)

def write_pkghistory(pkginfo, d):
    bb.debug(2, "Writing package history for package %s" % pkginfo.name)

    pkghistdir = d.getVar('BUILDHISTORY_DIR_PACKAGE')

    pkgpath = os.path.join(pkghistdir, pkginfo.name)
    if not os.path.exists(pkgpath):
        bb.utils.mkdirhier(pkgpath)

    infofile = os.path.join(pkgpath, "latest")
    with open(infofile, "w") as f:
        if pkginfo.pe != "0":
            f.write(u"PE = %s\n" %  pkginfo.pe)
        f.write(u"PV = %s\n" %  pkginfo.pv)
        f.write(u"PR = %s\n" %  pkginfo.pr)

        if pkginfo.pkg != pkginfo.name:
            f.write(u"PKG = %s\n" % pkginfo.pkg)
        if pkginfo.pkge != pkginfo.pe:
            f.write(u"PKGE = %s\n" % pkginfo.pkge)
        if pkginfo.pkgv != pkginfo.pv:
            f.write(u"PKGV = %s\n" % pkginfo.pkgv)
        if pkginfo.pkgr != pkginfo.pr:
            f.write(u"PKGR = %s\n" % pkginfo.pkgr)
        f.write(u"RPROVIDES = %s\n" %  pkginfo.rprovides)
        f.write(u"RDEPENDS = %s\n" %  pkginfo.rdepends)
        f.write(u"RRECOMMENDS = %s\n" %  pkginfo.rrecommends)
        if pkginfo.rsuggests:
            f.write(u"RSUGGESTS = %s\n" %  pkginfo.rsuggests)
        if pkginfo.rreplaces:
            f.write(u"RREPLACES = %s\n" %  pkginfo.rreplaces)
        if pkginfo.rconflicts:
            f.write(u"RCONFLICTS = %s\n" %  pkginfo.rconflicts)
        f.write(u"PKGSIZE = %d\n" %  pkginfo.size)
        f.write(u"FILES = %s\n" %  pkginfo.files)
        f.write(u"FILELIST = %s\n" %  pkginfo.filelist)

    for filevar in pkginfo.filevars:
        filevarpath = os.path.join(pkgpath, "latest.%s" % filevar)
        val = pkginfo.filevars[filevar]
        if val:
            with open(filevarpath, "w") as f:
                f.write(val)
        else:
            if os.path.exists(filevarpath):
                os.unlink(filevarpath)

buildhistory_list_pkg_files() {
	# Create individual files-in-package for each recipe's package
	for pkgdir in $(find ${PKGDEST}/* -maxdepth 0 -type d); do
		pkgname=$(basename $pkgdir)
		outfolder="${BUILDHISTORY_DIR_PACKAGE}/$pkgname"
		outfile="$outfolder/files-in-package.txt"
		# Make sure the output folder exists so we can create the file
		if [ ! -d $outfolder ] ; then
			bbdebug 2 "Folder $outfolder does not exist, file $outfile not created"
			continue
		fi
		buildhistory_list_files $pkgdir $outfile fakeroot
	done
}
