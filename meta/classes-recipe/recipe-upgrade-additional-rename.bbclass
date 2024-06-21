# This class can be used to add file renames in devtool version upgrades
# operations when there are supplemental recipes that need to be updated
# in lockstep with the main one by renaming the files. This is common,
# e.g. glib, cmake, mesa, libva, etc have this issue.
#
# Example (from glib which has glib-initial to handle):
#
# inherit recipe-upgrade-additional-rename
# RECIPE_UPGRADE_ADDITIONAL_RENAME = "glib-2.0-initial_{pv}.bb"
#
RECIPE_UPGRADE_FINISH_EXTRA_TASKS += "do_recipe_upgrade_additional_rename"
addtask do_recipe_upgrade_additional_rename

python do_recipe_upgrade_additional_rename() {
    import glob
    origpath = d.getVar("THISDIR")
    newpv = d.getVar("PV")

    for f_pattern in d.getVar("RECIPE_UPGRADE_ADDITIONAL_RENAME").split():
        for f_disk in glob.glob(os.path.join(origpath, f_pattern.format(pv="*"))):
            os.rename(f_disk, os.path.join(origpath, f_pattern.format(pv=newpv)))
}
