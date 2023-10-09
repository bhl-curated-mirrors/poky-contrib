SUMMARY = "Dummy packages which handle excluding packages from the sdk, e.g. ensuring perl is excluded from buildtools"
LICENSE = "MIT"

PACKAGE_ARCH = "all"

inherit allarch

python() {
    # Put the package somewhere separate to ensure it's never used except
    # when we want it
    # (note that we have to do this in anonymous python here to avoid
    # allarch.bbclass disabling itself)
    d.setVar('PACKAGE_ARCH', '${DUMMYARCH}')
}

ALLOW_EMPTY:${PN} = "1"

PR[vardeps] += "DUMMYPROVIDES"
PR[vardeps] += "DUMMYPROVIDES_PACKAGES"

DUMMYMAXVER ??= "999.9-r9"
DUMMYPROVIDES_PACKAGES ??= ""
DUMMYPROVIDES_PACKAGES_FILTERED = "${@' '.join([pkg for pkg in d.getVar('DUMMYPROVIDES_PACKAGES').split() if d.getVar('IMAGE_INSTALL') is None or pkg not in d.getVar('IMAGE_INSTALL').split()])}"
DUMMYPROVIDES_PACKAGES_MULTILIB = "${@' '.join([multilib_pkg_extend(d, pkg) for pkg in d.getVar('DUMMYPROVIDES_PACKAGES_FILTERED').split()])}"
DUMMYPROVIDES_MAXVER = "${@' '.join(['{} (= {})'.format(pkg, d.getVar('DUMMYMAXVER')) for pkg in d.getVar('DUMMYPROVIDES_PACKAGES_MULTILIB').split()]) + d.getVar('DUMMYPROVIDES')}"

DUMMYPROVIDES += "${DUMMYPROVIDES_PACKAGES_MULTILIB}"

python populate_packages:prepend() {
    p = d.getVar("PN")
    d.appendVar("RPROVIDES:%s" % p, "${DUMMYPROVIDES_MAXVER}")
    d.appendVar("RCONFLICTS:%s" % p, "${DUMMYPROVIDES_PACKAGES_MULTILIB}")
    d.appendVar("RREPLACES:%s" % p, "${DUMMYPROVIDES_PACKAGES_MULTILIB}")
}

