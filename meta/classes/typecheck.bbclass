# Check types of bitbake configuration variables
#
# See oe.types for details.

python check_types() {
    import oe.types
<<<<<<< HEAD
    for key in e.data.keys():
        if e.data.getVarFlag(key, "type"):
            oe.data.typed_value(key, e.data)
}
addhandler check_types
check_types[eventmask] = "bb.event.ConfigParsed"
=======
    if isinstance(e, bb.event.ConfigParsed):
        for key in e.data.keys():
            if e.data.getVarFlag(key, "type"):
                oe.data.typed_value(key, e.data)
}
addhandler check_types
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
