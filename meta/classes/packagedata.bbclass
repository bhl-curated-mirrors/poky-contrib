python read_subpackage_metadata () {
    import oe.packagedata

<<<<<<< HEAD
    vars = {
        "PN" : d.getVar('PN', True), 
        "PE" : d.getVar('PE', True), 
        "PV" : d.getVar('PV', True),
        "PR" : d.getVar('PR', True),
    }

    data = oe.packagedata.read_pkgdata(vars["PN"], d)
=======
    data = oe.packagedata.read_pkgdata(d.getVar('PN', True), d)
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

    for key in data.keys():
        d.setVar(key, data[key])

    for pkg in d.getVar('PACKAGES', True).split():
        sdata = oe.packagedata.read_subpkgdata(pkg, d)
        for key in sdata.keys():
<<<<<<< HEAD
            if key in vars:
                if sdata[key] != vars[key]:
                    if key == "PN":
                        bb.fatal("Recipe %s is trying to create package %s which was already written by recipe %s. This will cause corruption, please resolve this and only provide the package from one recipe or the other or only build one of the recipes." % (vars[key], pkg, sdata[key]))
                    bb.fatal("Recipe %s is trying to change %s from '%s' to '%s'. This will cause do_package_write_* failures since the incorrect data will be used and they will be unable to find the right workdir." % (vars["PN"], key, vars[key], sdata[key]))
                continue
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
            d.setVar(key, sdata[key])
}
