# Development tool - standard commands plugin
#
# Copyright (C) 2014-2016 Intel Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Devtool standard plugins"""

import os
import sys
import re
import shutil
import subprocess
import tempfile
import logging
import argparse
import argparse_oe
import scriptutils
import errno
import glob
import filecmp
from collections import OrderedDict
from devtool import exec_build_env_command, setup_tinfoil, check_workspace_recipe, use_external_build, setup_git_repo, recipe_to_append, get_bbclassextend_targets, ensure_npm, DevtoolError
from devtool import parse_recipe

logger = logging.getLogger('devtool')


def add(args, config, basepath, workspace):
    """Entry point for the devtool 'add' subcommand"""
    import bb
    import oe.recipeutils

    if not args.recipename and not args.srctree and not args.fetch and not args.fetchuri:
        raise argparse_oe.ArgumentUsageError('At least one of recipename, srctree, fetchuri or -f/--fetch must be specified', 'add')

    # These are positional arguments, but because we're nice, allow
    # specifying e.g. source tree without name, or fetch URI without name or
    # source tree (if we can detect that that is what the user meant)
    if scriptutils.is_src_url(args.recipename):
        if not args.fetchuri:
            if args.fetch:
                raise DevtoolError('URI specified as positional argument as well as -f/--fetch')
            args.fetchuri = args.recipename
            args.recipename = ''
    elif scriptutils.is_src_url(args.srctree):
        if not args.fetchuri:
            if args.fetch:
                raise DevtoolError('URI specified as positional argument as well as -f/--fetch')
            args.fetchuri = args.srctree
            args.srctree = ''
    elif args.recipename and not args.srctree:
        if os.sep in args.recipename:
            args.srctree = args.recipename
            args.recipename = None
        elif os.path.isdir(args.recipename):
            logger.warn('Ambiguous argument "%s" - assuming you mean it to be the recipe name' % args.recipename)

    if args.srctree and os.path.isfile(args.srctree):
        args.fetchuri = 'file://' + os.path.abspath(args.srctree)
        args.srctree = ''

    if args.fetch:
        if args.fetchuri:
            raise DevtoolError('URI specified as positional argument as well as -f/--fetch')
        else:
            logger.warn('-f/--fetch option is deprecated - you can now simply specify the URL to fetch as a positional argument instead')
            args.fetchuri = args.fetch

    if args.recipename:
        if args.recipename in workspace:
            raise DevtoolError("recipe %s is already in your workspace" %
                               args.recipename)
        reason = oe.recipeutils.validate_pn(args.recipename)
        if reason:
            raise DevtoolError(reason)

    if args.srctree:
        srctree = os.path.abspath(args.srctree)
        srctreeparent = None
        tmpsrcdir = None
    else:
        srctree = None
        srctreeparent = get_default_srctree(config)
        bb.utils.mkdirhier(srctreeparent)
        tmpsrcdir = tempfile.mkdtemp(prefix='devtoolsrc', dir=srctreeparent)

    if srctree and os.path.exists(srctree):
        if args.fetchuri:
            if not os.path.isdir(srctree):
                raise DevtoolError("Cannot fetch into source tree path %s as "
                                   "it exists and is not a directory" %
                                   srctree)
            elif os.listdir(srctree):
                raise DevtoolError("Cannot fetch into source tree path %s as "
                                   "it already exists and is non-empty" %
                                   srctree)
    elif not args.fetchuri:
        if args.srctree:
            raise DevtoolError("Specified source tree %s could not be found" %
                               args.srctree)
        elif srctree:
            raise DevtoolError("No source tree exists at default path %s - "
                               "either create and populate this directory, "
                               "or specify a path to a source tree, or a "
                               "URI to fetch source from" % srctree)
        else:
            raise DevtoolError("You must either specify a source tree "
                               "or a URI to fetch source from")

    if args.version:
        if '_' in args.version or ' ' in args.version:
            raise DevtoolError('Invalid version string "%s"' % args.version)

    if args.color == 'auto' and sys.stdout.isatty():
        color = 'always'
    else:
        color = args.color
    extracmdopts = ''
    if args.fetchuri:
        if args.fetchuri.startswith('npm://'):
            ensure_npm(config, basepath, args.fixed_setup)

        source = args.fetchuri
        if srctree:
            extracmdopts += ' -x %s' % srctree
        else:
            extracmdopts += ' -x %s' % tmpsrcdir
    else:
        source = srctree
    if args.recipename:
        extracmdopts += ' -N %s' % args.recipename
    if args.version:
        extracmdopts += ' -V %s' % args.version
    if args.binary:
        extracmdopts += ' -b'
    if args.also_native:
        extracmdopts += ' --also-native'
    if args.src_subdir:
        extracmdopts += ' --src-subdir "%s"' % args.src_subdir
    if args.autorev:
        extracmdopts += ' -a'

    tempdir = tempfile.mkdtemp(prefix='devtool')
    try:
        while True:
            try:
                stdout, _ = exec_build_env_command(config.init_path, basepath, 'recipetool --color=%s create --devtool -o %s \'%s\' %s' % (color, tempdir, source, extracmdopts), watch=True)
            except bb.process.ExecutionError as e:
                if e.exitcode == 14:
                    # FIXME this is a horrible hack that is unfortunately
                    # necessary due to the fact that we can't run bitbake from
                    # inside recipetool since recipetool keeps tinfoil active
                    # with references to it throughout the code, so we have
                    # to exit out and come back here to do it.
                    ensure_npm(config, basepath, args.fixed_setup)
                    logger.info('Re-running recipe creation process after building nodejs')
                    continue
                elif e.exitcode == 15:
                    raise DevtoolError('Could not auto-determine recipe name, please specify it on the command line')
                else:
                    raise DevtoolError('Command \'%s\' failed' % e.command)
            break

        recipes = glob.glob(os.path.join(tempdir, '*.bb'))
        if recipes:
            recipename = os.path.splitext(os.path.basename(recipes[0]))[0].split('_')[0]
            if recipename in workspace:
                raise DevtoolError('A recipe with the same name as the one being created (%s) already exists in your workspace' % recipename)
            recipedir = os.path.join(config.workspace_path, 'recipes', recipename)
            bb.utils.mkdirhier(recipedir)
            recipefile = os.path.join(recipedir, os.path.basename(recipes[0]))
            appendfile = recipe_to_append(recipefile, config)
            if os.path.exists(appendfile):
                # This shouldn't be possible, but just in case
                raise DevtoolError('A recipe with the same name as the one being created already exists in your workspace')
            if os.path.exists(recipefile):
                raise DevtoolError('A recipe file %s already exists in your workspace; this shouldn\'t be there - please delete it before continuing' % recipefile)
            if tmpsrcdir:
                srctree = os.path.join(srctreeparent, recipename)
                if os.path.exists(tmpsrcdir):
                    if os.path.exists(srctree):
                        if os.path.isdir(srctree):
                            try:
                                os.rmdir(srctree)
                            except OSError as e:
                                if e.errno == errno.ENOTEMPTY:
                                    raise DevtoolError('Source tree path %s already exists and is not empty' % srctree)
                                else:
                                    raise
                        else:
                            raise DevtoolError('Source tree path %s already exists and is not a directory' % srctree)
                    logger.info('Using default source tree path %s' % srctree)
                    shutil.move(tmpsrcdir, srctree)
                else:
                    raise DevtoolError('Couldn\'t find source tree created by recipetool')
            bb.utils.mkdirhier(recipedir)
            shutil.move(recipes[0], recipefile)
            # Move any additional files created by recipetool
            for fn in os.listdir(tempdir):
                shutil.move(os.path.join(tempdir, fn), recipedir)
        else:
            raise DevtoolError('Command \'%s\' did not create any recipe file:\n%s' % (e.command, e.stdout))
        attic_recipe = os.path.join(config.workspace_path, 'attic', recipename, os.path.basename(recipefile))
        if os.path.exists(attic_recipe):
            logger.warn('A modified recipe from a previous invocation exists in %s - you may wish to move this over the top of the new recipe if you had changes in it that you want to continue with' % attic_recipe)
    finally:
        if tmpsrcdir and os.path.exists(tmpsrcdir):
            shutil.rmtree(tmpsrcdir)
        shutil.rmtree(tempdir)

    for fn in os.listdir(recipedir):
        _add_md5(config, recipename, os.path.join(recipedir, fn))

    tinfoil = setup_tinfoil(config_only=True, basepath=basepath)
    try:
        try:
            rd = tinfoil.parse_recipe_file(recipefile, False)
        except Exception as e:
            logger.error(str(e))
            rd = None
        if not rd:
            # Parsing failed. We just created this recipe and we shouldn't
            # leave it in the workdir or it'll prevent bitbake from starting
            movefn = '%s.parsefailed' % recipefile
            logger.error('Parsing newly created recipe failed, moving recipe to %s for reference. If this looks to be caused by the recipe itself, please report this error.' % movefn)
            shutil.move(recipefile, movefn)
            return 1

        if args.fetchuri and not args.no_git:
            setup_git_repo(srctree, args.version, 'devtool', d=tinfoil.config_data)

        initial_rev = None
        if os.path.exists(os.path.join(srctree, '.git')):
            (stdout, _) = bb.process.run('git rev-parse HEAD', cwd=srctree)
            initial_rev = stdout.rstrip()

        if args.src_subdir:
            srctree = os.path.join(srctree, args.src_subdir)

        bb.utils.mkdirhier(os.path.dirname(appendfile))
        with open(appendfile, 'w') as f:
            f.write('inherit externalsrc\n')
            f.write('EXTERNALSRC = "%s"\n' % srctree)

            b_is_s = use_external_build(args.same_dir, args.no_same_dir, rd)
            if b_is_s:
                f.write('EXTERNALSRC_BUILD = "%s"\n' % srctree)
            if initial_rev:
                f.write('\n# initial_rev: %s\n' % initial_rev)

            if args.binary:
                f.write('do_install_append() {\n')
                f.write('    rm -rf ${D}/.git\n')
                f.write('    rm -f ${D}/singletask.lock\n')
                f.write('}\n')

            if bb.data.inherits_class('npm', rd):
                f.write('do_install_append() {\n')
                f.write('    # Remove files added to source dir by devtool/externalsrc\n')
                f.write('    rm -f ${NPM_INSTALLDIR}/singletask.lock\n')
                f.write('    rm -rf ${NPM_INSTALLDIR}/.git\n')
                f.write('    rm -rf ${NPM_INSTALLDIR}/oe-local-files\n')
                f.write('    for symlink in ${EXTERNALSRC_SYMLINKS} ; do\n')
                f.write('        rm -f ${NPM_INSTALLDIR}/${symlink%%:*}\n')
                f.write('    done\n')
                f.write('}\n')

            if bb.data.inherits_class('kernel', rd):
                provider = 'PREFERRED_PROVIDER_virtual/kernel="%s"' % args.recipename
                if args.fixed_setup:
                    f.write("%s" % provider)
                else:
                    logger.warn('Set \'%s\' in order to use the recipe' % provider)

        _add_md5(config, recipename, appendfile)

        logger.info('Recipe %s has been automatically created; further editing may be required to make it fully functional' % recipefile)

    finally:
        tinfoil.shutdown()

    return 0


def _check_compatible_recipe(pn, d):
    """Check if the recipe is supported by devtool"""
    if pn == 'perf':
        raise DevtoolError("The perf recipe does not actually check out "
                           "source and thus cannot be supported by this tool",
                           4)

    if pn in ['kernel-devsrc', 'package-index'] or pn.startswith('gcc-source'):
        raise DevtoolError("The %s recipe is not supported by this tool" % pn, 4)

    if bb.data.inherits_class('image', d):
        raise DevtoolError("The %s recipe is an image, and therefore is not "
                           "supported by this tool" % pn, 4)

    if bb.data.inherits_class('populate_sdk', d):
        raise DevtoolError("The %s recipe is an SDK, and therefore is not "
                           "supported by this tool" % pn, 4)

    if bb.data.inherits_class('packagegroup', d):
        raise DevtoolError("The %s recipe is a packagegroup, and therefore is "
                           "not supported by this tool" % pn, 4)

    if bb.data.inherits_class('meta', d):
        raise DevtoolError("The %s recipe is a meta-recipe, and therefore is "
                           "not supported by this tool" % pn, 4)

    if bb.data.inherits_class('externalsrc', d) and d.getVar('EXTERNALSRC'):
        # Not an incompatibility error per se, so we don't pass the error code
        raise DevtoolError("externalsrc is currently enabled for the %s "
                           "recipe. This prevents the normal do_patch task "
                           "from working. You will need to disable this "
                           "first." % pn)

def _move_file(src, dst):
    """Move a file. Creates all the directory components of destination path."""
    dst_d = os.path.dirname(dst)
    if dst_d:
        bb.utils.mkdirhier(dst_d)
    shutil.move(src, dst)

def _copy_file(src, dst):
    """Copy a file. Creates all the directory components of destination path."""
    dst_d = os.path.dirname(dst)
    if dst_d:
        bb.utils.mkdirhier(dst_d)
    shutil.copy(src, dst)

def _git_ls_tree(repodir, treeish='HEAD', recursive=False):
    """List contents of a git treeish"""
    import bb
    cmd = ['git', 'ls-tree', '-z', treeish]
    if recursive:
        cmd.append('-r')
    out, _ = bb.process.run(cmd, cwd=repodir)
    ret = {}
    if out:
        for line in out.split('\0'):
            if line:
                split = line.split(None, 4)
                ret[split[3]] = split[0:3]
    return ret

def _git_exclude_path(srctree, path):
    """Return pathspec (list of paths) that excludes certain path"""
    # NOTE: "Filtering out" files/paths in this way is not entirely reliable -
    # we don't catch files that are deleted, for example. A more reliable way
    # to implement this would be to use "negative pathspecs" which were
    # introduced in Git v1.9.0. Revisit this when/if the required Git version
    # becomes greater than that.
    path = os.path.normpath(path)
    recurse = True if len(path.split(os.path.sep)) > 1 else False
    git_files = list(_git_ls_tree(srctree, 'HEAD', recurse).keys())
    if path in git_files:
        git_files.remove(path)
        return git_files
    else:
        return ['.']

def _ls_tree(directory):
    """Recursive listing of files in a directory"""
    ret = []
    for root, dirs, files in os.walk(directory):
        ret.extend([os.path.relpath(os.path.join(root, fname), directory) for
                    fname in files])
    return ret


def extract(args, config, basepath, workspace):
    """Entry point for the devtool 'extract' subcommand"""
    import bb

    tinfoil = _prep_extract_operation(config, basepath, args.recipename)
    if not tinfoil:
        # Error already shown
        return 1
    try:
        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        srctree = os.path.abspath(args.srctree)
        initial_rev = _extract_source(srctree, args.keep_temp, args.branch, False, rd, tinfoil)
        logger.info('Source tree extracted to %s' % srctree)

        if initial_rev:
            return 0
        else:
            return 1
    finally:
        tinfoil.shutdown()

def sync(args, config, basepath, workspace):
    """Entry point for the devtool 'sync' subcommand"""
    import bb

    tinfoil = _prep_extract_operation(config, basepath, args.recipename)
    if not tinfoil:
        # Error already shown
        return 1
    try:
        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        srctree = os.path.abspath(args.srctree)
        initial_rev = _extract_source(srctree, args.keep_temp, args.branch, True, rd, tinfoil)
        logger.info('Source tree %s synchronized' % srctree)

        if initial_rev:
            return 0
        else:
            return 1
    finally:
        tinfoil.shutdown()


def _prep_extract_operation(config, basepath, recipename, tinfoil=None):
    """HACK: Ugly workaround for making sure that requirements are met when
       trying to extract a package. Returns the tinfoil instance to be used."""
    if not tinfoil:
        tinfoil = setup_tinfoil(basepath=basepath)

    rd = parse_recipe(config, tinfoil, recipename, True)
    if not rd:
        return None

    if bb.data.inherits_class('kernel-yocto', rd):
        tinfoil.shutdown()
        try:
            stdout, _ = exec_build_env_command(config.init_path, basepath,
                                               'bitbake kern-tools-native')
            tinfoil = setup_tinfoil(basepath=basepath)
        except bb.process.ExecutionError as err:
            raise DevtoolError("Failed to build kern-tools-native:\n%s" %
                               err.stdout)
    return tinfoil


def _extract_source(srctree, keep_temp, devbranch, sync, d, tinfoil):
    """Extract sources of a recipe"""
    import oe.recipeutils

    pn = d.getVar('PN')

    _check_compatible_recipe(pn, d)

    if sync:
        if not os.path.exists(srctree):
                raise DevtoolError("output path %s does not exist" % srctree)
    else:
        if os.path.exists(srctree):
            if not os.path.isdir(srctree):
                raise DevtoolError("output path %s exists and is not a directory" %
                                   srctree)
            elif os.listdir(srctree):
                raise DevtoolError("output path %s already exists and is "
                                   "non-empty" % srctree)

        if 'noexec' in (d.getVarFlags('do_unpack', False) or []):
            raise DevtoolError("The %s recipe has do_unpack disabled, unable to "
                               "extract source" % pn, 4)

    if not sync:
        # Prepare for shutil.move later on
        bb.utils.mkdirhier(srctree)
        os.rmdir(srctree)

    initial_rev = None
    # We need to redirect WORKDIR, STAMPS_DIR etc. under a temporary
    # directory so that:
    # (a) we pick up all files that get unpacked to the WORKDIR, and
    # (b) we don't disturb the existing build
    # However, with recipe-specific sysroots the sysroots for the recipe
    # will be prepared under WORKDIR, and if we used the system temporary
    # directory (i.e. usually /tmp) as used by mkdtemp by default, then
    # our attempts to hardlink files into the recipe-specific sysroots
    # will fail on systems where /tmp is a different filesystem, and it
    # would have to fall back to copying the files which is a waste of
    # time. Put the temp directory under the WORKDIR to prevent that from
    # being a problem.
    tempbasedir = d.getVar('WORKDIR')
    bb.utils.mkdirhier(tempbasedir)
    tempdir = tempfile.mkdtemp(prefix='devtooltmp-', dir=tempbasedir)
    try:
        tinfoil.logger.setLevel(logging.WARNING)

        crd = d.createCopy()
        # Make a subdir so we guard against WORKDIR==S
        workdir = os.path.join(tempdir, 'workdir')
        crd.setVar('WORKDIR', workdir)
        if not crd.getVar('S').startswith(workdir):
            # Usually a shared workdir recipe (kernel, gcc)
            # Try to set a reasonable default
            if bb.data.inherits_class('kernel', d):
                crd.setVar('S', '${WORKDIR}/source')
            else:
                crd.setVar('S', '${WORKDIR}/%s' % os.path.basename(d.getVar('S')))
        if bb.data.inherits_class('kernel', d):
            # We don't want to move the source to STAGING_KERNEL_DIR here
            crd.setVar('STAGING_KERNEL_DIR', '${S}')

        is_kernel_yocto = bb.data.inherits_class('kernel-yocto', d)
        if not is_kernel_yocto:
            crd.setVar('PATCHTOOL', 'git')
            crd.setVar('PATCH_COMMIT_FUNCTIONS', '1')

        # Apply our changes to the datastore to the server's datastore
        for key in crd.localkeys():
            tinfoil.config_data.setVar('%s_pn-%s' % (key, pn), crd.getVar(key, False))

        tinfoil.config_data.setVar('STAMPS_DIR', os.path.join(tempdir, 'stamps'))
        tinfoil.config_data.setVar('T', os.path.join(tempdir, 'temp'))
        tinfoil.config_data.setVar('BUILDCFG_FUNCS', '')
        tinfoil.config_data.setVar('BUILDCFG_HEADER', '')
        tinfoil.config_data.setVar('BB_HASH_IGNORE_MISMATCH', '1')

        tinfoil.set_event_mask(['bb.event.BuildStarted',
                                'bb.event.BuildCompleted',
                                'bb.event.TaskStarted',
                                'logging.LogRecord',
                                'bb.command.CommandCompleted',
                                'bb.command.CommandFailed',
                                'bb.build.TaskStarted',
                                'bb.build.TaskSucceeded',
                                'bb.build.TaskFailedSilent'])

        def runtask(target, task):
            if tinfoil.build_file(target, task):
                while True:
                    event = tinfoil.wait_event(0.25)
                    if event:
                        if isinstance(event, bb.command.CommandCompleted):
                            break
                        elif isinstance(event, bb.command.CommandFailed):
                            raise DevtoolError('Task do_%s failed: %s' % (task, event.error))
                        elif isinstance(event, bb.build.TaskStarted):
                            logger.info('Executing %s...' % event._task)
                        elif isinstance(event, logging.LogRecord):
                            if event.levelno <= logging.INFO:
                                continue
                            logger.handle(event)

        # we need virtual:native:/path/to/recipe if it's a BBCLASSEXTEND
        fn = tinfoil.get_recipe_file(pn)
        runtask(fn, 'unpack')

        if bb.data.inherits_class('kernel-yocto', d):
            # Extra step for kernel to populate the source directory
            runtask(fn, 'kernel_checkout')

        srcsubdir = crd.getVar('S')

        # Move local source files into separate subdir
        recipe_patches = [os.path.basename(patch) for patch in
                          oe.recipeutils.get_recipe_patches(crd)]
        local_files = oe.recipeutils.get_recipe_local_files(crd)

        # Ignore local files with subdir={BP}
        srcabspath = os.path.abspath(srcsubdir)
        local_files = [fname for fname in local_files if
                       os.path.exists(os.path.join(workdir, fname)) and
                       (srcabspath == workdir or not
                       os.path.join(workdir, fname).startswith(srcabspath +
                           os.sep))]
        if local_files:
            for fname in local_files:
                _move_file(os.path.join(workdir, fname),
                           os.path.join(tempdir, 'oe-local-files', fname))
            with open(os.path.join(tempdir, 'oe-local-files', '.gitignore'),
                      'w') as f:
                f.write('# Ignore local files, by default. Remove this file '
                        'if you want to commit the directory to Git\n*\n')

        if srcsubdir == workdir:
            # Find non-patch non-local sources that were "unpacked" to srctree
            # directory
            src_files = [fname for fname in _ls_tree(workdir) if
                         os.path.basename(fname) not in recipe_patches]
            # Force separate S so that patch files can be left out from srctree
            srcsubdir = tempfile.mkdtemp(dir=workdir)
            tinfoil.config_data.setVar('S_task-patch', srcsubdir)
            # Move source files to S
            for path in src_files:
                _move_file(os.path.join(workdir, path),
                           os.path.join(srcsubdir, path))
        elif os.path.dirname(srcsubdir) != workdir:
            # Handle if S is set to a subdirectory of the source
            srcsubdir = os.path.join(workdir, os.path.relpath(srcsubdir, workdir).split(os.sep)[0])

        scriptutils.git_convert_standalone_clone(srcsubdir)

        # Make sure that srcsubdir exists
        bb.utils.mkdirhier(srcsubdir)
        if not os.path.exists(srcsubdir) or not os.listdir(srcsubdir):
            logger.warning("no source unpacked to S, either the %s recipe "
                           "doesn't use any source or the correct source "
                           "directory could not be determined" % pn)

        setup_git_repo(srcsubdir, crd.getVar('PV'), devbranch, d=d)

        (stdout, _) = bb.process.run('git rev-parse HEAD', cwd=srcsubdir)
        initial_rev = stdout.rstrip()

        logger.info('Patching...')
        runtask(fn, 'patch')

        bb.process.run('git tag -f devtool-patched', cwd=srcsubdir)

        kconfig = None
        if bb.data.inherits_class('kernel-yocto', d):
            # Store generate and store kernel config
            logger.info('Generating kernel config')
            runtask(fn, 'configure')
            kconfig = os.path.join(crd.getVar('B'), '.config')


        tempdir_localdir = os.path.join(tempdir, 'oe-local-files')
        srctree_localdir = os.path.join(srctree, 'oe-local-files')

        if sync:
            bb.process.run('git fetch file://' + srcsubdir + ' ' + devbranch + ':' + devbranch, cwd=srctree)

            # Move oe-local-files directory to srctree
            # As the oe-local-files is not part of the constructed git tree,
            # remove them directly during the synchrounizating might surprise
            # the users.  Instead, we move it to oe-local-files.bak and remind
            # user in the log message.
            if os.path.exists(srctree_localdir + '.bak'):
                shutil.rmtree(srctree_localdir, srctree_localdir + '.bak')

            if os.path.exists(srctree_localdir):
                logger.info('Backing up current local file directory %s' % srctree_localdir)
                shutil.move(srctree_localdir, srctree_localdir + '.bak')

            if os.path.exists(tempdir_localdir):
                logger.info('Syncing local source files to srctree...')
                shutil.copytree(tempdir_localdir, srctree_localdir)
        else:
            # Move oe-local-files directory to srctree
            if os.path.exists(tempdir_localdir):
                logger.info('Adding local source files to srctree...')
                shutil.move(tempdir_localdir, srcsubdir)

            shutil.move(srcsubdir, srctree)

            if os.path.abspath(d.getVar('S')) == os.path.abspath(d.getVar('WORKDIR')):
                # If recipe extracts to ${WORKDIR}, symlink the files into the srctree
                # (otherwise the recipe won't build as expected)
                local_files_dir = os.path.join(srctree, 'oe-local-files')
                addfiles = []
                for root, _, files in os.walk(local_files_dir):
                    relpth = os.path.relpath(root, local_files_dir)
                    if relpth != '.':
                        bb.utils.mkdirhier(os.path.join(srctree, relpth))
                    for fn in files:
                        if fn == '.gitignore':
                            continue
                        destpth = os.path.join(srctree, relpth, fn)
                        if os.path.exists(destpth):
                            os.unlink(destpth)
                        os.symlink('oe-local-files/%s' % fn, destpth)
                        addfiles.append(os.path.join(relpth, fn))
                if addfiles:
                    bb.process.run('git add %s' % ' '.join(addfiles), cwd=srctree)
                useroptions = []
                oe.patch.GitApplyTree.gitCommandUserOptions(useroptions, d=d)
                bb.process.run('git %s commit -a -m "Committing local file symlinks\n\n%s"' % (' '.join(useroptions), oe.patch.GitApplyTree.ignore_commit_prefix), cwd=srctree)

        if kconfig:
            logger.info('Copying kernel config to srctree')
            shutil.copy2(kconfig, srctree)

    finally:
        if keep_temp:
            logger.info('Preserving temporary directory %s' % tempdir)
        else:
            shutil.rmtree(tempdir)
    return initial_rev

def _add_md5(config, recipename, filename):
    """Record checksum of a file (or recursively for a directory) to the md5-file of the workspace"""
    import bb.utils

    def addfile(fn):
        md5 = bb.utils.md5_file(fn)
        with open(os.path.join(config.workspace_path, '.devtool_md5'), 'a') as f:
            f.write('%s|%s|%s\n' % (recipename, os.path.relpath(fn, config.workspace_path), md5))

    if os.path.isdir(filename):
        for root, _, files in os.walk(filename):
            for f in files:
                addfile(os.path.join(root, f))
    else:
        addfile(filename)

def _check_preserve(config, recipename):
    """Check if a file was manually changed and needs to be saved in 'attic'
       directory"""
    import bb.utils
    origfile = os.path.join(config.workspace_path, '.devtool_md5')
    newfile = os.path.join(config.workspace_path, '.devtool_md5_new')
    preservepath = os.path.join(config.workspace_path, 'attic', recipename)
    with open(origfile, 'r') as f:
        with open(newfile, 'w') as tf:
            for line in f.readlines():
                splitline = line.rstrip().split('|')
                if splitline[0] == recipename:
                    removefile = os.path.join(config.workspace_path, splitline[1])
                    try:
                        md5 = bb.utils.md5_file(removefile)
                    except IOError as err:
                        if err.errno == 2:
                            # File no longer exists, skip it
                            continue
                        else:
                            raise
                    if splitline[2] != md5:
                        bb.utils.mkdirhier(preservepath)
                        preservefile = os.path.basename(removefile)
                        logger.warn('File %s modified since it was written, preserving in %s' % (preservefile, preservepath))
                        shutil.move(removefile, os.path.join(preservepath, preservefile))
                    else:
                        os.remove(removefile)
                else:
                    tf.write(line)
    os.rename(newfile, origfile)

def modify(args, config, basepath, workspace):
    """Entry point for the devtool 'modify' subcommand"""
    import bb
    import oe.recipeutils

    if args.recipename in workspace:
        raise DevtoolError("recipe %s is already in your workspace" %
                           args.recipename)

    tinfoil = setup_tinfoil(basepath=basepath)
    try:
        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        pn = rd.getVar('PN')
        if pn != args.recipename:
            logger.info('Mapping %s to %s' % (args.recipename, pn))
        if pn in workspace:
            raise DevtoolError("recipe %s is already in your workspace" %
                            pn)

        if args.srctree:
            srctree = os.path.abspath(args.srctree)
        else:
            srctree = get_default_srctree(config, pn)

        if args.no_extract and not os.path.isdir(srctree):
            raise DevtoolError("--no-extract specified and source path %s does "
                            "not exist or is not a directory" %
                            srctree)
        if not args.no_extract:
            tinfoil = _prep_extract_operation(config, basepath, pn, tinfoil)
            if not tinfoil:
                # Error already shown
                return 1
            # We need to re-parse because tinfoil may have been re-initialised
            rd = parse_recipe(config, tinfoil, args.recipename, True)

        recipefile = rd.getVar('FILE')
        appendfile = recipe_to_append(recipefile, config, args.wildcard)
        if os.path.exists(appendfile):
            raise DevtoolError("Another variant of recipe %s is already in your "
                            "workspace (only one variant of a recipe can "
                            "currently be worked on at once)"
                            % pn)

        _check_compatible_recipe(pn, rd)

        initial_rev = None
        commits = []
        if not args.no_extract:
            initial_rev = _extract_source(srctree, False, args.branch, False, rd, tinfoil)
            if not initial_rev:
                return 1
            logger.info('Source tree extracted to %s' % srctree)
            # Get list of commits since this revision
            (stdout, _) = bb.process.run('git rev-list --reverse %s..HEAD' % initial_rev, cwd=srctree)
            commits = stdout.split()
        else:
            if os.path.exists(os.path.join(srctree, '.git')):
                # Check if it's a tree previously extracted by us
                try:
                    (stdout, _) = bb.process.run('git branch --contains devtool-base', cwd=srctree)
                except bb.process.ExecutionError:
                    stdout = ''
                for line in stdout.splitlines():
                    if line.startswith('*'):
                        (stdout, _) = bb.process.run('git rev-parse devtool-base', cwd=srctree)
                        initial_rev = stdout.rstrip()
                if not initial_rev:
                    # Otherwise, just grab the head revision
                    (stdout, _) = bb.process.run('git rev-parse HEAD', cwd=srctree)
                    initial_rev = stdout.rstrip()

        # Check that recipe isn't using a shared workdir
        s = os.path.abspath(rd.getVar('S'))
        workdir = os.path.abspath(rd.getVar('WORKDIR'))
        if s.startswith(workdir) and s != workdir and os.path.dirname(s) != workdir:
            # Handle if S is set to a subdirectory of the source
            srcsubdir = os.path.relpath(s, workdir).split(os.sep, 1)[1]
            srctree = os.path.join(srctree, srcsubdir)

        bb.utils.mkdirhier(os.path.dirname(appendfile))
        with open(appendfile, 'w') as f:
            f.write('FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"\n')
            # Local files can be modified/tracked in separate subdir under srctree
            # Mostly useful for packages with S != WORKDIR
            f.write('FILESPATH_prepend := "%s:"\n' %
                    os.path.join(srctree, 'oe-local-files'))

            f.write('\ninherit externalsrc\n')
            f.write('# NOTE: We use pn- overrides here to avoid affecting multiple variants in the case where the recipe uses BBCLASSEXTEND\n')
            f.write('EXTERNALSRC_pn-%s = "%s"\n' % (pn, srctree))

            b_is_s = use_external_build(args.same_dir, args.no_same_dir, rd)
            if b_is_s:
                f.write('EXTERNALSRC_BUILD_pn-%s = "%s"\n' % (pn, srctree))

            if bb.data.inherits_class('kernel', rd):
                f.write('SRCTREECOVEREDTASKS = "do_validate_branches do_kernel_checkout '
                        'do_fetch do_unpack do_patch do_kernel_configme do_kernel_configcheck"\n')
                f.write('\ndo_configure_append() {\n'
                        '    cp ${B}/.config ${S}/.config.baseline\n'
                        '    ln -sfT ${B}/.config ${S}/.config.new\n'
                        '}\n')
            if initial_rev:
                f.write('\n# initial_rev: %s\n' % initial_rev)
                for commit in commits:
                    f.write('# commit: %s\n' % commit)

        _add_md5(config, pn, appendfile)

        logger.info('Recipe %s now set up to build from %s' % (pn, srctree))

    finally:
        tinfoil.shutdown()

    return 0


def rename(args, config, basepath, workspace):
    """Entry point for the devtool 'rename' subcommand"""
    import bb
    import oe.recipeutils

    check_workspace_recipe(workspace, args.recipename)

    if not (args.newname or args.version):
        raise DevtoolError('You must specify a new name, a version with -V/--version, or both')

    recipefile = workspace[args.recipename]['recipefile']
    if not recipefile:
        raise DevtoolError('devtool rename can only be used where the recipe file itself is in the workspace (e.g. after devtool add)')

    if args.newname and args.newname != args.recipename:
        reason = oe.recipeutils.validate_pn(args.newname)
        if reason:
            raise DevtoolError(reason)
        newname = args.newname
    else:
        newname = args.recipename

    append = workspace[args.recipename]['bbappend']
    appendfn = os.path.splitext(os.path.basename(append))[0]
    splitfn = appendfn.split('_')
    if len(splitfn) > 1:
        origfnver = appendfn.split('_')[1]
    else:
        origfnver = ''

    recipefilemd5 = None
    tinfoil = setup_tinfoil(basepath=basepath, tracking=True)
    try:
        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        bp = rd.getVar('BP')
        bpn = rd.getVar('BPN')
        if newname != args.recipename:
            localdata = rd.createCopy()
            localdata.setVar('PN', newname)
            newbpn = localdata.getVar('BPN')
        else:
            newbpn = bpn
        s = rd.getVar('S', False)
        src_uri = rd.getVar('SRC_URI', False)
        pv = rd.getVar('PV')

        # Correct variable values that refer to the upstream source - these
        # values must stay the same, so if the name/version are changing then
        # we need to fix them up
        new_s = s
        new_src_uri = src_uri
        if newbpn != bpn:
            # ${PN} here is technically almost always incorrect, but people do use it
            new_s = new_s.replace('${BPN}', bpn)
            new_s = new_s.replace('${PN}', bpn)
            new_s = new_s.replace('${BP}', '%s-${PV}' % bpn)
            new_src_uri = new_src_uri.replace('${BPN}', bpn)
            new_src_uri = new_src_uri.replace('${PN}', bpn)
            new_src_uri = new_src_uri.replace('${BP}', '%s-${PV}' % bpn)
        if args.version and origfnver == pv:
            new_s = new_s.replace('${PV}', pv)
            new_s = new_s.replace('${BP}', '${BPN}-%s' % pv)
            new_src_uri = new_src_uri.replace('${PV}', pv)
            new_src_uri = new_src_uri.replace('${BP}', '${BPN}-%s' % pv)
        patchfields = {}
        if new_s != s:
            patchfields['S'] = new_s
        if new_src_uri != src_uri:
            patchfields['SRC_URI'] = new_src_uri
        if patchfields:
            recipefilemd5 = bb.utils.md5_file(recipefile)
            oe.recipeutils.patch_recipe(rd, recipefile, patchfields)
            newrecipefilemd5 = bb.utils.md5_file(recipefile)
    finally:
        tinfoil.shutdown()

    if args.version:
        newver = args.version
    else:
        newver = origfnver

    if newver:
        newappend = '%s_%s.bbappend' % (newname, newver)
        newfile =  '%s_%s.bb' % (newname, newver)
    else:
        newappend = '%s.bbappend' % newname
        newfile = '%s.bb' % newname

    oldrecipedir = os.path.dirname(recipefile)
    newrecipedir = os.path.join(config.workspace_path, 'recipes', newname)
    if oldrecipedir != newrecipedir:
        bb.utils.mkdirhier(newrecipedir)

    newappend = os.path.join(os.path.dirname(append), newappend)
    newfile = os.path.join(newrecipedir, newfile)

    # Rename bbappend
    logger.info('Renaming %s to %s' % (append, newappend))
    os.rename(append, newappend)
    # Rename recipe file
    logger.info('Renaming %s to %s' % (recipefile, newfile))
    os.rename(recipefile, newfile)

    # Rename source tree if it's the default path
    appendmd5 = None
    if not args.no_srctree:
        srctree = workspace[args.recipename]['srctree']
        if os.path.abspath(srctree) == os.path.join(config.workspace_path, 'sources', args.recipename):
            newsrctree = os.path.join(config.workspace_path, 'sources', newname)
            logger.info('Renaming %s to %s' % (srctree, newsrctree))
            shutil.move(srctree, newsrctree)
            # Correct any references (basically EXTERNALSRC*) in the .bbappend
            appendmd5 = bb.utils.md5_file(newappend)
            appendlines = []
            with open(newappend, 'r') as f:
                for line in f:
                    appendlines.append(line)
            with open(newappend, 'w') as f:
                for line in appendlines:
                    if srctree in line:
                        line = line.replace(srctree, newsrctree)
                    f.write(line)
            newappendmd5 = bb.utils.md5_file(newappend)

    bpndir = None
    newbpndir = None
    if newbpn != bpn:
        bpndir = os.path.join(oldrecipedir, bpn)
        if os.path.exists(bpndir):
            newbpndir = os.path.join(newrecipedir, newbpn)
            logger.info('Renaming %s to %s' % (bpndir, newbpndir))
            shutil.move(bpndir, newbpndir)

    bpdir = None
    newbpdir = None
    if newver != origfnver or newbpn != bpn:
        bpdir = os.path.join(oldrecipedir, bp)
        if os.path.exists(bpdir):
            newbpdir = os.path.join(newrecipedir, '%s-%s' % (newbpn, newver))
            logger.info('Renaming %s to %s' % (bpdir, newbpdir))
            shutil.move(bpdir, newbpdir)

    if oldrecipedir != newrecipedir:
        # Move any stray files and delete the old recipe directory
        for entry in os.listdir(oldrecipedir):
            oldpath = os.path.join(oldrecipedir, entry)
            newpath = os.path.join(newrecipedir, entry)
            logger.info('Renaming %s to %s' % (oldpath, newpath))
            shutil.move(oldpath, newpath)
        os.rmdir(oldrecipedir)

    # Now take care of entries in .devtool_md5
    md5entries = []
    with open(os.path.join(config.workspace_path, '.devtool_md5'), 'r') as f:
        for line in f:
            md5entries.append(line)

    if bpndir and newbpndir:
        relbpndir = os.path.relpath(bpndir, config.workspace_path) + '/'
    else:
        relbpndir = None
    if bpdir and newbpdir:
        relbpdir = os.path.relpath(bpdir, config.workspace_path) + '/'
    else:
        relbpdir = None

    with open(os.path.join(config.workspace_path, '.devtool_md5'), 'w') as f:
        for entry in md5entries:
            splitentry = entry.rstrip().split('|')
            if len(splitentry) > 2:
                if splitentry[0] == args.recipename:
                    splitentry[0] = newname
                    if splitentry[1] == os.path.relpath(append, config.workspace_path):
                        splitentry[1] = os.path.relpath(newappend, config.workspace_path)
                        if appendmd5 and splitentry[2] == appendmd5:
                            splitentry[2] = newappendmd5
                    elif splitentry[1] == os.path.relpath(recipefile, config.workspace_path):
                        splitentry[1] = os.path.relpath(newfile, config.workspace_path)
                        if recipefilemd5 and splitentry[2] == recipefilemd5:
                            splitentry[2] = newrecipefilemd5
                    elif relbpndir and splitentry[1].startswith(relbpndir):
                        splitentry[1] = os.path.relpath(os.path.join(newbpndir, splitentry[1][len(relbpndir):]), config.workspace_path)
                    elif relbpdir and splitentry[1].startswith(relbpdir):
                        splitentry[1] = os.path.relpath(os.path.join(newbpdir, splitentry[1][len(relbpdir):]), config.workspace_path)
                    entry = '|'.join(splitentry) + '\n'
            f.write(entry)
    return 0


def _get_patchset_revs(srctree, recipe_path, initial_rev=None):
    """Get initial and update rev of a recipe. These are the start point of the
    whole patchset and start point for the patches to be re-generated/updated.
    """
    import bb

    # Parse initial rev from recipe if not specified
    commits = []
    with open(recipe_path, 'r') as f:
        for line in f:
            if line.startswith('# initial_rev:'):
                if not initial_rev:
                    initial_rev = line.split(':')[-1].strip()
            elif line.startswith('# commit:'):
                commits.append(line.split(':')[-1].strip())

    update_rev = initial_rev
    changed_revs = None
    if initial_rev:
        # Find first actually changed revision
        stdout, _ = bb.process.run('git rev-list --reverse %s..HEAD' %
                                   initial_rev, cwd=srctree)
        newcommits = stdout.split()
        for i in range(min(len(commits), len(newcommits))):
            if newcommits[i] == commits[i]:
                update_rev = commits[i]

        try:
            stdout, _ = bb.process.run('git cherry devtool-patched',
                                        cwd=srctree)
        except bb.process.ExecutionError as err:
            stdout = None

        if stdout is not None:
            changed_revs = []
            for line in stdout.splitlines():
                if line.startswith('+ '):
                    rev = line.split()[1]
                    if rev in newcommits:
                        changed_revs.append(rev)

    return initial_rev, update_rev, changed_revs

def _remove_file_entries(srcuri, filelist):
    """Remove file:// entries from SRC_URI"""
    remaining = filelist[:]
    entries = []
    for fname in filelist:
        basename = os.path.basename(fname)
        for i in range(len(srcuri)):
            if (srcuri[i].startswith('file://') and
                    os.path.basename(srcuri[i].split(';')[0]) == basename):
                entries.append(srcuri[i])
                remaining.remove(fname)
                srcuri.pop(i)
                break
    return entries, remaining

def _replace_srcuri_entry(srcuri, filename, newentry):
    """Replace entry corresponding to specified file with a new entry"""
    basename = os.path.basename(filename)
    for i in range(len(srcuri)):
        if os.path.basename(srcuri[i].split(';')[0]) == basename:
            srcuri.pop(i)
            srcuri.insert(i, newentry)
            break

def _remove_source_files(append, files, destpath):
    """Unlink existing patch files"""
    for path in files:
        if append:
            if not destpath:
                raise Exception('destpath should be set here')
            path = os.path.join(destpath, os.path.basename(path))

        if os.path.exists(path):
            logger.info('Removing file %s' % path)
            # FIXME "git rm" here would be nice if the file in question is
            #       tracked
            # FIXME there's a chance that this file is referred to by
            #       another recipe, in which case deleting wouldn't be the
            #       right thing to do
            os.remove(path)
            # Remove directory if empty
            try:
                os.rmdir(os.path.dirname(path))
            except OSError as ose:
                if ose.errno != errno.ENOTEMPTY:
                    raise


def _export_patches(srctree, rd, start_rev, destdir, changed_revs=None):
    """Export patches from srctree to given location.
       Returns three-tuple of dicts:
         1. updated - patches that already exist in SRCURI
         2. added - new patches that don't exist in SRCURI
         3  removed - patches that exist in SRCURI but not in exported patches
      In each dict the key is the 'basepath' of the URI and value is the
      absolute path to the existing file in recipe space (if any).
    """
    import oe.recipeutils
    from oe.patch import GitApplyTree
    updated = OrderedDict()
    added = OrderedDict()
    seqpatch_re = re.compile('^([0-9]{4}-)?(.+)')

    existing_patches = dict((os.path.basename(path), path) for path in
                            oe.recipeutils.get_recipe_patches(rd))

    # Generate patches from Git, exclude local files directory
    patch_pathspec = _git_exclude_path(srctree, 'oe-local-files')
    GitApplyTree.extractPatches(srctree, start_rev, destdir, patch_pathspec)

    new_patches = sorted(os.listdir(destdir))
    for new_patch in new_patches:
        # Strip numbering from patch names. If it's a git sequence named patch,
        # the numbers might not match up since we are starting from a different
        # revision This does assume that people are using unique shortlog
        # values, but they ought to be anyway...
        new_basename = seqpatch_re.match(new_patch).group(2)
        match_name = None
        for old_patch in existing_patches:
            old_basename = seqpatch_re.match(old_patch).group(2)
            old_basename_splitext = os.path.splitext(old_basename)
            if old_basename.endswith(('.gz', '.bz2', '.Z')) and old_basename_splitext[0] == new_basename:
                old_patch_noext = os.path.splitext(old_patch)[0]
                match_name = old_patch_noext
                break
            elif new_basename == old_basename:
                match_name = old_patch
                break
        if match_name:
            # Rename patch files
            if new_patch != match_name:
                os.rename(os.path.join(destdir, new_patch),
                          os.path.join(destdir, match_name))
            # Need to pop it off the list now before checking changed_revs
            oldpath = existing_patches.pop(old_patch)
            if changed_revs is not None:
                # Avoid updating patches that have not actually changed
                with open(os.path.join(destdir, match_name), 'r') as f:
                    firstlineitems = f.readline().split()
                    # Looking for "From <hash>" line
                    if len(firstlineitems) > 1 and len(firstlineitems[1]) == 40:
                        if not firstlineitems[1] in changed_revs:
                            continue
            # Recompress if necessary
            if oldpath.endswith(('.gz', '.Z')):
                bb.process.run(['gzip', match_name], cwd=destdir)
                if oldpath.endswith('.gz'):
                    match_name += '.gz'
                else:
                    match_name += '.Z'
            elif oldpath.endswith('.bz2'):
                bb.process.run(['bzip2', match_name], cwd=destdir)
                match_name += '.bz2'
            updated[match_name] = oldpath
        else:
            added[new_patch] = None
    return (updated, added, existing_patches)


def _create_kconfig_diff(srctree, rd, outfile):
    """Create a kconfig fragment"""
    # Only update config fragment if both config files exist
    orig_config = os.path.join(srctree, '.config.baseline')
    new_config = os.path.join(srctree, '.config.new')
    if os.path.exists(orig_config) and os.path.exists(new_config):
        cmd = ['diff', '--new-line-format=%L', '--old-line-format=',
               '--unchanged-line-format=', orig_config, new_config]
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = pipe.communicate()
        if pipe.returncode == 1:
            logger.info("Updating config fragment %s" % outfile)
            with open(outfile, 'w') as fobj:
                fobj.write(stdout)
        elif pipe.returncode == 0:
            logger.info("Would remove config fragment %s" % outfile)
            if os.path.exists(outfile):
                # Remove fragment file in case of empty diff
                logger.info("Removing config fragment %s" % outfile)
                os.unlink(outfile)
        else:
            raise bb.process.ExecutionError(cmd, pipe.returncode, stdout, stderr)
        return True
    return False


def _export_local_files(srctree, rd, destdir):
    """Copy local files from srctree to given location.
       Returns three-tuple of dicts:
         1. updated - files that already exist in SRCURI
         2. added - new files files that don't exist in SRCURI
         3  removed - files that exist in SRCURI but not in exported files
      In each dict the key is the 'basepath' of the URI and value is the
      absolute path to the existing file in recipe space (if any).
    """
    import oe.recipeutils

    # Find out local files (SRC_URI files that exist in the "recipe space").
    # Local files that reside in srctree are not included in patch generation.
    # Instead they are directly copied over the original source files (in
    # recipe space).
    existing_files = oe.recipeutils.get_recipe_local_files(rd)
    new_set = None
    updated = OrderedDict()
    added = OrderedDict()
    removed = OrderedDict()
    local_files_dir = os.path.join(srctree, 'oe-local-files')
    git_files = _git_ls_tree(srctree)
    if 'oe-local-files' in git_files:
        # If tracked by Git, take the files from srctree HEAD. First get
        # the tree object of the directory
        tmp_index = os.path.join(srctree, '.git', 'index.tmp.devtool')
        tree = git_files['oe-local-files'][2]
        bb.process.run(['git', 'checkout', tree, '--', '.'], cwd=srctree,
                        env=dict(os.environ, GIT_WORK_TREE=destdir,
                                 GIT_INDEX_FILE=tmp_index))
        new_set = list(_git_ls_tree(srctree, tree, True).keys())
    elif os.path.isdir(local_files_dir):
        # If not tracked by Git, just copy from working copy
        new_set = _ls_tree(os.path.join(srctree, 'oe-local-files'))
        bb.process.run(['cp', '-ax',
                        os.path.join(srctree, 'oe-local-files', '.'), destdir])
    else:
        new_set = []

    # Special handling for kernel config
    if bb.data.inherits_class('kernel-yocto', rd):
        fragment_fn = 'devtool-fragment.cfg'
        fragment_path = os.path.join(destdir, fragment_fn)
        if _create_kconfig_diff(srctree, rd, fragment_path):
            if os.path.exists(fragment_path):
                if fragment_fn not in new_set:
                    new_set.append(fragment_fn)
                # Copy fragment to local-files
                if os.path.isdir(local_files_dir):
                    shutil.copy2(fragment_path, local_files_dir)
            else:
                if fragment_fn in new_set:
                    new_set.remove(fragment_fn)
                # Remove fragment from local-files
                if os.path.exists(os.path.join(local_files_dir, fragment_fn)):
                    os.unlink(os.path.join(local_files_dir, fragment_fn))

    if new_set is not None:
        for fname in new_set:
            if fname in existing_files:
                origpath = existing_files.pop(fname)
                workpath = os.path.join(local_files_dir, fname)
                if not filecmp.cmp(origpath, workpath):
                    updated[fname] = origpath
            elif fname != '.gitignore':
                added[fname] = None

        workdir = rd.getVar('WORKDIR')
        s = rd.getVar('S')
        if not s.endswith(os.sep):
            s += os.sep

        if workdir != s:
            # Handle files where subdir= was specified
            for fname in list(existing_files.keys()):
                # FIXME handle both subdir starting with BP and not?
                fworkpath = os.path.join(workdir, fname)
                if fworkpath.startswith(s):
                    fpath = os.path.join(srctree, os.path.relpath(fworkpath, s))
                    if os.path.exists(fpath):
                        origpath = existing_files.pop(fname)
                        if not filecmp.cmp(origpath, fpath):
                            updated[fpath] = origpath

        removed = existing_files
    return (updated, added, removed)


def _determine_files_dir(rd):
    """Determine the appropriate files directory for a recipe"""
    recipedir = rd.getVar('FILE_DIRNAME')
    for entry in rd.getVar('FILESPATH').split(':'):
        relpth = os.path.relpath(entry, recipedir)
        if not os.sep in relpth:
            # One (or zero) levels below only, so we don't put anything in machine-specific directories
            if os.path.isdir(entry):
                return entry
    return os.path.join(recipedir, rd.getVar('BPN'))


def _update_recipe_srcrev(srctree, rd, appendlayerdir, wildcard_version, no_remove):
    """Implement the 'srcrev' mode of update-recipe"""
    import bb
    import oe.recipeutils

    recipefile = rd.getVar('FILE')
    logger.info('Updating SRCREV in recipe %s' % os.path.basename(recipefile))

    # Get HEAD revision
    try:
        stdout, _ = bb.process.run('git rev-parse HEAD', cwd=srctree)
    except bb.process.ExecutionError as err:
        raise DevtoolError('Failed to get HEAD revision in %s: %s' %
                           (srctree, err))
    srcrev = stdout.strip()
    if len(srcrev) != 40:
        raise DevtoolError('Invalid hash returned by git: %s' % stdout)

    destpath = None
    remove_files = []
    patchfields = {}
    patchfields['SRCREV'] = srcrev
    orig_src_uri = rd.getVar('SRC_URI', False) or ''
    srcuri = orig_src_uri.split()
    tempdir = tempfile.mkdtemp(prefix='devtool')
    update_srcuri = False
    try:
        local_files_dir = tempfile.mkdtemp(dir=tempdir)
        upd_f, new_f, del_f = _export_local_files(srctree, rd, local_files_dir)
        if not no_remove:
            # Find list of existing patches in recipe file
            patches_dir = tempfile.mkdtemp(dir=tempdir)
            old_srcrev = (rd.getVar('SRCREV', False) or '')
            upd_p, new_p, del_p = _export_patches(srctree, rd, old_srcrev,
                                                  patches_dir)

            # Remove deleted local files and "overlapping" patches
            remove_files = list(del_f.values()) + list(upd_p.values())
            if remove_files:
                removedentries = _remove_file_entries(srcuri, remove_files)[0]
                update_srcuri = True

        if appendlayerdir:
            files = dict((os.path.join(local_files_dir, key), val) for
                          key, val in list(upd_f.items()) + list(new_f.items()))
            removevalues = {}
            if update_srcuri:
                removevalues  = {'SRC_URI': removedentries}
                patchfields['SRC_URI'] = '\\\n    '.join(srcuri)
            _, destpath = oe.recipeutils.bbappend_recipe(
                    rd, appendlayerdir, files, wildcardver=wildcard_version,
                    extralines=patchfields, removevalues=removevalues)
        else:
            files_dir = _determine_files_dir(rd)
            for basepath, path in upd_f.items():
                logger.info('Updating file %s' % basepath)
                if os.path.isabs(basepath):
                    # Original file (probably with subdir pointing inside source tree)
                    # so we do not want to move it, just copy
                    _copy_file(basepath, path)
                else:
                    _move_file(os.path.join(local_files_dir, basepath), path)
                update_srcuri= True
            for basepath, path in new_f.items():
                logger.info('Adding new file %s' % basepath)
                _move_file(os.path.join(local_files_dir, basepath),
                           os.path.join(files_dir, basepath))
                srcuri.append('file://%s' % basepath)
                update_srcuri = True
            if update_srcuri:
                patchfields['SRC_URI'] = ' '.join(srcuri)
            oe.recipeutils.patch_recipe(rd, recipefile, patchfields)
    finally:
        shutil.rmtree(tempdir)
    if not 'git://' in orig_src_uri:
        logger.info('You will need to update SRC_URI within the recipe to '
                    'point to a git repository where you have pushed your '
                    'changes')

    _remove_source_files(appendlayerdir, remove_files, destpath)
    return True

def _update_recipe_patch(recipename, workspace, srctree, rd, appendlayerdir, wildcard_version, no_remove, initial_rev):
    """Implement the 'patch' mode of update-recipe"""
    import bb
    import oe.recipeutils

    recipefile = rd.getVar('FILE')
    append = workspace[recipename]['bbappend']
    if not os.path.exists(append):
        raise DevtoolError('unable to find workspace bbappend for recipe %s' %
                           recipename)

    initial_rev, update_rev, changed_revs = _get_patchset_revs(srctree, append, initial_rev)
    if not initial_rev:
        raise DevtoolError('Unable to find initial revision - please specify '
                           'it with --initial-rev')

    dl_dir = rd.getVar('DL_DIR')
    if not dl_dir.endswith('/'):
        dl_dir += '/'

    tempdir = tempfile.mkdtemp(prefix='devtool')
    try:
        local_files_dir = tempfile.mkdtemp(dir=tempdir)
        upd_f, new_f, del_f = _export_local_files(srctree, rd, local_files_dir)

        remove_files = []
        if not no_remove:
            # Get all patches from source tree and check if any should be removed
            all_patches_dir = tempfile.mkdtemp(dir=tempdir)
            upd_p, new_p, del_p = _export_patches(srctree, rd, initial_rev,
                                                  all_patches_dir)
            # Remove deleted local files and  patches
            remove_files = list(del_f.values()) + list(del_p.values())

        # Get updated patches from source tree
        patches_dir = tempfile.mkdtemp(dir=tempdir)
        upd_p, new_p, del_p = _export_patches(srctree, rd, update_rev,
                                              patches_dir, changed_revs)
        updatefiles = False
        updaterecipe = False
        destpath = None
        srcuri = (rd.getVar('SRC_URI', False) or '').split()
        if appendlayerdir:
            files = dict((os.path.join(local_files_dir, key), val) for
                         key, val in list(upd_f.items()) + list(new_f.items()))
            files.update(dict((os.path.join(patches_dir, key), val) for
                              key, val in list(upd_p.items()) + list(new_p.items())))
            if files or remove_files:
                removevalues = None
                if remove_files:
                    removedentries, remaining = _remove_file_entries(
                                                    srcuri, remove_files)
                    if removedentries or remaining:
                        remaining = ['file://' + os.path.basename(item) for
                                     item in remaining]
                        removevalues = {'SRC_URI': removedentries + remaining}
                _, destpath = oe.recipeutils.bbappend_recipe(
                                rd, appendlayerdir, files,
                                wildcardver=wildcard_version,
                                removevalues=removevalues)
            else:
                logger.info('No patches or local source files needed updating')
        else:
            # Update existing files
            files_dir = _determine_files_dir(rd)
            for basepath, path in upd_f.items():
                logger.info('Updating file %s' % basepath)
                if os.path.isabs(basepath):
                    # Original file (probably with subdir pointing inside source tree)
                    # so we do not want to move it, just copy
                    _copy_file(basepath, path)
                else:
                    _move_file(os.path.join(local_files_dir, basepath), path)
                updatefiles = True
            for basepath, path in upd_p.items():
                patchfn = os.path.join(patches_dir, basepath)
                if os.path.dirname(path) + '/' == dl_dir:
                    # This is a a downloaded patch file - we now need to
                    # replace the entry in SRC_URI with our local version
                    logger.info('Replacing remote patch %s with updated local version' % basepath)
                    path = os.path.join(files_dir, basepath)
                    _replace_srcuri_entry(srcuri, basepath, 'file://%s' % basepath)
                    updaterecipe = True
                else:
                    logger.info('Updating patch %s' % basepath)
                logger.debug('Moving new patch %s to %s' % (patchfn, path))
                _move_file(patchfn, path)
                updatefiles = True
            # Add any new files
            for basepath, path in new_f.items():
                logger.info('Adding new file %s' % basepath)
                _move_file(os.path.join(local_files_dir, basepath),
                           os.path.join(files_dir, basepath))
                srcuri.append('file://%s' % basepath)
                updaterecipe = True
            for basepath, path in new_p.items():
                logger.info('Adding new patch %s' % basepath)
                _move_file(os.path.join(patches_dir, basepath),
                           os.path.join(files_dir, basepath))
                srcuri.append('file://%s' % basepath)
                updaterecipe = True
            # Update recipe, if needed
            if _remove_file_entries(srcuri, remove_files)[0]:
                updaterecipe = True
            if updaterecipe:
                logger.info('Updating recipe %s' % os.path.basename(recipefile))
                oe.recipeutils.patch_recipe(rd, recipefile,
                                            {'SRC_URI': ' '.join(srcuri)})
            elif not updatefiles:
                # Neither patches nor recipe were updated
                logger.info('No patches or files need updating')
                return False
    finally:
        shutil.rmtree(tempdir)

    _remove_source_files(appendlayerdir, remove_files, destpath)
    return True

def _guess_recipe_update_mode(srctree, rdata):
    """Guess the recipe update mode to use"""
    src_uri = (rdata.getVar('SRC_URI', False) or '').split()
    git_uris = [uri for uri in src_uri if uri.startswith('git://')]
    if not git_uris:
        return 'patch'
    # Just use the first URI for now
    uri = git_uris[0]
    # Check remote branch
    params = bb.fetch.decodeurl(uri)[5]
    upstr_branch = params['branch'] if 'branch' in params else 'master'
    # Check if current branch HEAD is found in upstream branch
    stdout, _ = bb.process.run('git rev-parse HEAD', cwd=srctree)
    head_rev = stdout.rstrip()
    stdout, _ = bb.process.run('git branch -r --contains %s' % head_rev,
                               cwd=srctree)
    remote_brs = [branch.strip() for branch in stdout.splitlines()]
    if 'origin/' + upstr_branch in remote_brs:
        return 'srcrev'

    return 'patch'

def _update_recipe(recipename, workspace, rd, mode, appendlayerdir, wildcard_version, no_remove, initial_rev):
    srctree = workspace[recipename]['srctree']
    if mode == 'auto':
        mode = _guess_recipe_update_mode(srctree, rd)

    if mode == 'srcrev':
        updated = _update_recipe_srcrev(srctree, rd, appendlayerdir, wildcard_version, no_remove)
    elif mode == 'patch':
        updated = _update_recipe_patch(recipename, workspace, srctree, rd, appendlayerdir, wildcard_version, no_remove, initial_rev)
    else:
        raise DevtoolError('update_recipe: invalid mode %s' % mode)
    return updated

def update_recipe(args, config, basepath, workspace):
    """Entry point for the devtool 'update-recipe' subcommand"""
    check_workspace_recipe(workspace, args.recipename)

    if args.append:
        if not os.path.exists(args.append):
            raise DevtoolError('bbappend destination layer directory "%s" '
                               'does not exist' % args.append)
        if not os.path.exists(os.path.join(args.append, 'conf', 'layer.conf')):
            raise DevtoolError('conf/layer.conf not found in bbappend '
                               'destination layer "%s"' % args.append)

    tinfoil = setup_tinfoil(basepath=basepath, tracking=True)
    try:

        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        updated = _update_recipe(args.recipename, workspace, rd, args.mode, args.append, args.wildcard_version, args.no_remove, args.initial_rev)

        if updated:
            rf = rd.getVar('FILE')
            if rf.startswith(config.workspace_path):
                logger.warn('Recipe file %s has been updated but is inside the workspace - you will need to move it (and any associated files next to it) out to the desired layer before using "devtool reset" in order to keep any changes' % rf)
    finally:
        tinfoil.shutdown()

    return 0


def status(args, config, basepath, workspace):
    """Entry point for the devtool 'status' subcommand"""
    if workspace:
        for recipe, value in workspace.items():
            recipefile = value['recipefile']
            if recipefile:
                recipestr = ' (%s)' % recipefile
            else:
                recipestr = ''
            print("%s: %s%s" % (recipe, value['srctree'], recipestr))
    else:
        logger.info('No recipes currently in your workspace - you can use "devtool modify" to work on an existing recipe or "devtool add" to add a new one')
    return 0


def _reset(recipes, no_clean, config, basepath, workspace):
    """Reset one or more recipes"""

    if recipes and not no_clean:
        if len(recipes) == 1:
            logger.info('Cleaning sysroot for recipe %s...' % recipes[0])
        else:
            logger.info('Cleaning sysroot for recipes %s...' % ', '.join(recipes))
        # If the recipe file itself was created in the workspace, and
        # it uses BBCLASSEXTEND, then we need to also clean the other
        # variants
        targets = []
        for recipe in recipes:
            targets.append(recipe)
            recipefile = workspace[recipe]['recipefile']
            if recipefile and os.path.exists(recipefile):
                targets.extend(get_bbclassextend_targets(recipefile, recipe))
        try:
            exec_build_env_command(config.init_path, basepath, 'bitbake -c clean %s' % ' '.join(targets))
        except bb.process.ExecutionError as e:
            raise DevtoolError('Command \'%s\' failed, output:\n%s\nIf you '
                                'wish, you may specify -n/--no-clean to '
                                'skip running this command when resetting' %
                                (e.command, e.stdout))

    for pn in recipes:
        _check_preserve(config, pn)

        preservepath = os.path.join(config.workspace_path, 'attic', pn, pn)
        def preservedir(origdir):
            if os.path.exists(origdir):
                for root, dirs, files in os.walk(origdir):
                    for fn in files:
                        logger.warn('Preserving %s in %s' % (fn, preservepath))
                        _move_file(os.path.join(origdir, fn),
                                   os.path.join(preservepath, fn))
                    for dn in dirs:
                        preservedir(os.path.join(root, dn))
                os.rmdir(origdir)

        preservedir(os.path.join(config.workspace_path, 'recipes', pn))
        # We don't automatically create this dir next to appends, but the user can
        preservedir(os.path.join(config.workspace_path, 'appends', pn))

        srctree = workspace[pn]['srctree']
        if os.path.isdir(srctree):
            if os.listdir(srctree):
                # We don't want to risk wiping out any work in progress
                logger.info('Leaving source tree %s as-is; if you no '
                            'longer need it then please delete it manually'
                            % srctree)
            else:
                # This is unlikely, but if it's empty we can just remove it
                os.rmdir(srctree)


def reset(args, config, basepath, workspace):
    """Entry point for the devtool 'reset' subcommand"""
    import bb
    if args.recipename:
        if args.all:
            raise DevtoolError("Recipe cannot be specified if -a/--all is used")
        else:
            for recipe in args.recipename:
                check_workspace_recipe(workspace, recipe, checksrc=False)
    elif not args.all:
        raise DevtoolError("Recipe must be specified, or specify -a/--all to "
                           "reset all recipes")
    if args.all:
        recipes = list(workspace.keys())
    else:
        recipes = args.recipename

    _reset(recipes, args.no_clean, config, basepath, workspace)

    return 0


def _get_layer(layername, d):
    """Determine the base layer path for the specified layer name/path"""
    layerdirs = d.getVar('BBLAYERS').split()
    layers = {os.path.basename(p): p for p in layerdirs}
    # Provide some shortcuts
    if layername.lower() in ['oe-core', 'openembedded-core']:
        layerdir = layers.get('meta', None)
    else:
        layerdir = layers.get(layername, None)
    if layerdir:
        layerdir = os.path.abspath(layerdir)
    return layerdir or layername

def finish(args, config, basepath, workspace):
    """Entry point for the devtool 'finish' subcommand"""
    import bb
    import oe.recipeutils

    check_workspace_recipe(workspace, args.recipename)

    no_clean = False
    tinfoil = setup_tinfoil(basepath=basepath, tracking=True)
    try:
        rd = parse_recipe(config, tinfoil, args.recipename, True)
        if not rd:
            return 1

        destlayerdir = _get_layer(args.destination, tinfoil.config_data)
        origlayerdir = oe.recipeutils.find_layerdir(rd.getVar('FILE'))

        if not os.path.isdir(destlayerdir):
            raise DevtoolError('Unable to find layer or directory matching "%s"' % args.destination)

        if os.path.abspath(destlayerdir) == config.workspace_path:
            raise DevtoolError('"%s" specifies the workspace layer - that is not a valid destination' % args.destination)

        # If it's an upgrade, grab the original path
        origpath = None
        origfilelist = None
        append = workspace[args.recipename]['bbappend']
        with open(append, 'r') as f:
            for line in f:
                if line.startswith('# original_path:'):
                    origpath = line.split(':')[1].strip()
                elif line.startswith('# original_files:'):
                    origfilelist = line.split(':')[1].split()

        if origlayerdir == config.workspace_path:
            # Recipe file itself is in workspace, update it there first
            appendlayerdir = None
            origrelpath = None
            if origpath:
                origlayerpath = oe.recipeutils.find_layerdir(origpath)
                if origlayerpath:
                    origrelpath = os.path.relpath(origpath, origlayerpath)
            destpath = oe.recipeutils.get_bbfile_path(rd, destlayerdir, origrelpath)
            if not destpath:
                raise DevtoolError("Unable to determine destination layer path - check that %s specifies an actual layer and %s/conf/layer.conf specifies BBFILES. You may also need to specify a more complete path." % (args.destination, destlayerdir))
            # Warn if the layer isn't in bblayers.conf (the code to create a bbappend will do this in other cases)
            layerdirs = [os.path.abspath(layerdir) for layerdir in rd.getVar('BBLAYERS').split()]
            if not os.path.abspath(destlayerdir) in layerdirs:
                bb.warn('Specified destination layer is not currently enabled in bblayers.conf, so the %s recipe will now be unavailable in your current configuration until you add the layer there' % args.recipename)

        elif destlayerdir == origlayerdir:
            # Same layer, update the original recipe
            appendlayerdir = None
            destpath = None
        else:
            # Create/update a bbappend in the specified layer
            appendlayerdir = destlayerdir
            destpath = None

        # Remove any old files in the case of an upgrade
        if origpath and origfilelist and oe.recipeutils.find_layerdir(origpath) == oe.recipeutils.find_layerdir(destlayerdir):
            for fn in origfilelist:
                fnp = os.path.join(origpath, fn)
                try:
                    os.remove(fnp)
                except FileNotFoundError:
                    pass

        # Actually update the recipe / bbappend
        _update_recipe(args.recipename, workspace, rd, args.mode, appendlayerdir, wildcard_version=True, no_remove=False, initial_rev=args.initial_rev)

        if origlayerdir == config.workspace_path and destpath:
            # Recipe file itself is in the workspace - need to move it and any
            # associated files to the specified layer
            no_clean = True
            logger.info('Moving recipe file to %s' % destpath)
            recipedir = os.path.dirname(rd.getVar('FILE'))
            for root, _, files in os.walk(recipedir):
                for fn in files:
                    srcpath = os.path.join(root, fn)
                    relpth = os.path.relpath(os.path.dirname(srcpath), recipedir)
                    destdir = os.path.abspath(os.path.join(destpath, relpth))
                    bb.utils.mkdirhier(destdir)
                    shutil.move(srcpath, os.path.join(destdir, fn))

    finally:
        tinfoil.shutdown()

    # Everything else has succeeded, we can now reset
    _reset([args.recipename], no_clean=no_clean, config=config, basepath=basepath, workspace=workspace)

    return 0


def get_default_srctree(config, recipename=''):
    """Get the default srctree path"""
    srctreeparent = config.get('General', 'default_source_parent_dir', config.workspace_path)
    if recipename:
        return os.path.join(srctreeparent, 'sources', recipename)
    else:
        return os.path.join(srctreeparent, 'sources')

def register_commands(subparsers, context):
    """Register devtool subcommands from this plugin"""

    defsrctree = get_default_srctree(context.config)
    parser_add = subparsers.add_parser('add', help='Add a new recipe',
                                       description='Adds a new recipe to the workspace to build a specified source tree. Can optionally fetch a remote URI and unpack it to create the source tree.',
                                       group='starting', order=100)
    parser_add.add_argument('recipename', nargs='?', help='Name for new recipe to add (just name - no version, path or extension). If not specified, will attempt to auto-detect it.')
    parser_add.add_argument('srctree', nargs='?', help='Path to external source tree. If not specified, a subdirectory of %s will be used.' % defsrctree)
    parser_add.add_argument('fetchuri', nargs='?', help='Fetch the specified URI and extract it to create the source tree')
    group = parser_add.add_mutually_exclusive_group()
    group.add_argument('--same-dir', '-s', help='Build in same directory as source', action="store_true")
    group.add_argument('--no-same-dir', help='Force build in a separate build directory', action="store_true")
    parser_add.add_argument('--fetch', '-f', help='Fetch the specified URI and extract it to create the source tree (deprecated - pass as positional argument instead)', metavar='URI')
    parser_add.add_argument('--version', '-V', help='Version to use within recipe (PV)')
    parser_add.add_argument('--no-git', '-g', help='If fetching source, do not set up source tree as a git repository', action="store_true")
    parser_add.add_argument('--autorev', '-a', help='When fetching from a git repository, set SRCREV in the recipe to a floating revision instead of fixed', action="store_true")
    parser_add.add_argument('--binary', '-b', help='Treat the source tree as something that should be installed verbatim (no compilation, same directory structure). Useful with binary packages e.g. RPMs.', action='store_true')
    parser_add.add_argument('--also-native', help='Also add native variant (i.e. support building recipe for the build host as well as the target machine)', action='store_true')
    parser_add.add_argument('--src-subdir', help='Specify subdirectory within source tree to use', metavar='SUBDIR')
    parser_add.set_defaults(func=add, fixed_setup=context.fixed_setup)

    parser_modify = subparsers.add_parser('modify', help='Modify the source for an existing recipe',
                                       description='Sets up the build environment to modify the source for an existing recipe. The default behaviour is to extract the source being fetched by the recipe into a git tree so you can work on it; alternatively if you already have your own pre-prepared source tree you can specify -n/--no-extract.',
                                       group='starting', order=90)
    parser_modify.add_argument('recipename', help='Name of existing recipe to edit (just name - no version, path or extension)')
    parser_modify.add_argument('srctree', nargs='?', help='Path to external source tree. If not specified, a subdirectory of %s will be used.' % defsrctree)
    parser_modify.add_argument('--wildcard', '-w', action="store_true", help='Use wildcard for unversioned bbappend')
    group = parser_modify.add_mutually_exclusive_group()
    group.add_argument('--extract', '-x', action="store_true", help='Extract source for recipe (default)')
    group.add_argument('--no-extract', '-n', action="store_true", help='Do not extract source, expect it to exist')
    group = parser_modify.add_mutually_exclusive_group()
    group.add_argument('--same-dir', '-s', help='Build in same directory as source', action="store_true")
    group.add_argument('--no-same-dir', help='Force build in a separate build directory', action="store_true")
    parser_modify.add_argument('--branch', '-b', default="devtool", help='Name for development branch to checkout (when not using -n/--no-extract) (default "%(default)s")')
    parser_modify.set_defaults(func=modify)

    parser_extract = subparsers.add_parser('extract', help='Extract the source for an existing recipe',
                                       description='Extracts the source for an existing recipe',
                                       group='advanced')
    parser_extract.add_argument('recipename', help='Name of recipe to extract the source for')
    parser_extract.add_argument('srctree', help='Path to where to extract the source tree')
    parser_extract.add_argument('--branch', '-b', default="devtool", help='Name for development branch to checkout (default "%(default)s")')
    parser_extract.add_argument('--keep-temp', action="store_true", help='Keep temporary directory (for debugging)')
    parser_extract.set_defaults(func=extract, no_workspace=True)

    parser_sync = subparsers.add_parser('sync', help='Synchronize the source tree for an existing recipe',
                                       description='Synchronize the previously extracted source tree for an existing recipe',
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                       group='advanced')
    parser_sync.add_argument('recipename', help='Name of recipe to sync the source for')
    parser_sync.add_argument('srctree', help='Path to the source tree')
    parser_sync.add_argument('--branch', '-b', default="devtool", help='Name for development branch to checkout')
    parser_sync.add_argument('--keep-temp', action="store_true", help='Keep temporary directory (for debugging)')
    parser_sync.set_defaults(func=sync)

    parser_rename = subparsers.add_parser('rename', help='Rename a recipe file in the workspace',
                                       description='Renames the recipe file for a recipe in the workspace, changing the name or version part or both, ensuring that all references within the workspace are updated at the same time. Only works when the recipe file itself is in the workspace, e.g. after devtool add. Particularly useful when devtool add did not automatically determine the correct name.',
                                       group='working', order=10)
    parser_rename.add_argument('recipename', help='Current name of recipe to rename')
    parser_rename.add_argument('newname', nargs='?', help='New name for recipe (optional, not needed if you only want to change the version)')
    parser_rename.add_argument('--version', '-V', help='Change the version (NOTE: this does not change the version fetched by the recipe, just the version in the recipe file name)')
    parser_rename.add_argument('--no-srctree', '-s', action='store_true', help='Do not rename the source tree directory (if the default source tree path has been used) - keeping the old name may be desirable if there are internal/other external references to this path')
    parser_rename.set_defaults(func=rename)

    parser_update_recipe = subparsers.add_parser('update-recipe', help='Apply changes from external source tree to recipe',
                                       description='Applies changes from external source tree to a recipe (updating/adding/removing patches as necessary, or by updating SRCREV). Note that these changes need to have been committed to the git repository in order to be recognised.',
                                       group='working', order=-90)
    parser_update_recipe.add_argument('recipename', help='Name of recipe to update')
    parser_update_recipe.add_argument('--mode', '-m', choices=['patch', 'srcrev', 'auto'], default='auto', help='Update mode (where %(metavar)s is %(choices)s; default is %(default)s)', metavar='MODE')
    parser_update_recipe.add_argument('--initial-rev', help='Override starting revision for patches')
    parser_update_recipe.add_argument('--append', '-a', help='Write changes to a bbappend in the specified layer instead of the recipe', metavar='LAYERDIR')
    parser_update_recipe.add_argument('--wildcard-version', '-w', help='In conjunction with -a/--append, use a wildcard to make the bbappend apply to any recipe version', action='store_true')
    parser_update_recipe.add_argument('--no-remove', '-n', action="store_true", help='Don\'t remove patches, only add or update')
    parser_update_recipe.set_defaults(func=update_recipe)

    parser_status = subparsers.add_parser('status', help='Show workspace status',
                                          description='Lists recipes currently in your workspace and the paths to their respective external source trees',
                                          group='info', order=100)
    parser_status.set_defaults(func=status)

    parser_reset = subparsers.add_parser('reset', help='Remove a recipe from your workspace',
                                         description='Removes the specified recipe(s) from your workspace (resetting its state back to that defined by the metadata).',
                                         group='working', order=-100)
    parser_reset.add_argument('recipename', nargs='*', help='Recipe to reset')
    parser_reset.add_argument('--all', '-a', action="store_true", help='Reset all recipes (clear workspace)')
    parser_reset.add_argument('--no-clean', '-n', action="store_true", help='Don\'t clean the sysroot to remove recipe output')
    parser_reset.set_defaults(func=reset)

    parser_finish = subparsers.add_parser('finish', help='Finish working on a recipe in your workspace',
                                         description='Pushes any committed changes to the specified recipe to the specified layer and removes it from your workspace. Roughly equivalent to an update-recipe followed by reset, except the update-recipe step will do the "right thing" depending on the recipe and the destination layer specified.',
                                         group='working', order=-100)
    parser_finish.add_argument('recipename', help='Recipe to finish')
    parser_finish.add_argument('destination', help='Layer/path to put recipe into. Can be the name of a layer configured in your bblayers.conf, the path to the base of a layer, or a partial path inside a layer. %(prog)s will attempt to complete the path based on the layer\'s structure.')
    parser_finish.add_argument('--mode', '-m', choices=['patch', 'srcrev', 'auto'], default='auto', help='Update mode (where %(metavar)s is %(choices)s; default is %(default)s)', metavar='MODE')
    parser_finish.add_argument('--initial-rev', help='Override starting revision for patches')
    parser_finish.set_defaults(func=finish)
