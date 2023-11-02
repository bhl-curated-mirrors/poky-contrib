#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

python do_populate_build_replica () {
    import oe.copy_buildsystem

    topdir = d.getVar('WORKDIR') + "/replica"
    sigfile = topdir + '/locked-sigs.inc'
    preserved_sstate_dir = topdir + "/sstate-cache"
    oe.copy_buildsystem.generate_locked_sigs(sigfile, d)
    oe.copy_buildsystem.create_locked_sstate_cache(sigfile, d.getVar('SSTATE_DIR'), preserved_sstate_dir, d)

    layerdir = topdir + "/meta-build-config"
    bb.process.run("bitbake-layers create-layer {}".format(layerdir))
    bb.process.run("bitbake-layers save-build-conf {} replica".format(layerdir))
    bb.process.run("bitbake-layers create-layers-setup {}".format(topdir))
}

# Shamelessly copied from populate_sdk_ext class
def get_replica_depends(d):
    # Note: the deps varflag is a list not a string, so we need to specify expand=False
    deps = d.getVarFlag('do_image_complete', 'deps', False)
    pn = d.getVar('PN')
    deplist = ['%s:%s' % (pn, dep) for dep in deps]
    tasklist = bb.build.tasksbetween('do_image_complete', 'do_build', d)
    tasklist.append('do_rootfs')
    for task in tasklist:
        deplist.extend((d.getVarFlag(task, 'depends') or '').split())
    return ' '.join(deplist)


do_populate_build_replica[depends] = "${@get_replica_depends(d)}"
addtask populate_build_replica
