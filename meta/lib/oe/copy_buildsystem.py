#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: GPL-2.0-only
#
# This class should provide easy access to the different aspects of the
# buildsystem such as layers, bitbake location, etc.
#
# SDK_LAYERS_EXCLUDE: Layers which will be excluded from SDK layers.
# SDK_LAYERS_EXCLUDE_PATTERN: The simiar to SDK_LAYERS_EXCLUDE, this supports
#                             python regular expression, use space as separator,
#                              e.g.: ".*-downloads closed-.*"
#

import stat
import shutil

def _smart_copy(src, dest):
    import subprocess
    # smart_copy will choose the correct function depending on whether the
    # source is a file or a directory.
    mode = os.stat(src).st_mode
    if stat.S_ISDIR(mode):
        bb.utils.mkdirhier(dest)
        cmd = "tar --exclude='.git' --exclude='__pycache__' --xattrs --xattrs-include='*' -chf - -C %s -p . \
        | tar --xattrs --xattrs-include='*' -xf - -C %s" % (src, dest)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    else:
        shutil.copyfile(src, dest)
        shutil.copymode(src, dest)

class BuildSystem(object):
    def __init__(self, context, d):
        self.d = d
        self.context = context
        self.layerdirs = [os.path.abspath(pth) for pth in d.getVar('BBLAYERS').split()]
        self.layers_exclude = (d.getVar('SDK_LAYERS_EXCLUDE') or "").split()
        self.layers_exclude_pattern = d.getVar('SDK_LAYERS_EXCLUDE_PATTERN')

    def copy_bitbake_and_layers(self, destdir, workspace_name=None):
        import re
        # Copy in all metadata layers + bitbake (as repositories)
        copied_corebase = None
        layers_copied = []
        bb.utils.mkdirhier(destdir)
        layers = list(self.layerdirs)

        corebase = os.path.abspath(self.d.getVar('COREBASE'))
        layers.append(corebase)
        # The bitbake build system uses the meta-skeleton layer as a layout
        # for common recipies, e.g: the recipetool script to create kernel recipies
        # Add the meta-skeleton layer to be included as part of the eSDK installation
        layers.append(os.path.join(corebase, 'meta-skeleton'))

        # Exclude layers
        for layer_exclude in self.layers_exclude:
            if layer_exclude in layers:
                bb.note('Excluded %s from sdk layers since it is in SDK_LAYERS_EXCLUDE' % layer_exclude)
                layers.remove(layer_exclude)

        if self.layers_exclude_pattern:
            layers_cp = layers[:]
            for pattern in self.layers_exclude_pattern.split():
                for layer in layers_cp:
                    if re.match(pattern, layer):
                        bb.note('Excluded %s from sdk layers since matched SDK_LAYERS_EXCLUDE_PATTERN' % layer)
                        layers.remove(layer)

        workspace_newname = workspace_name
        if workspace_newname:
            layernames = [os.path.basename(layer) for layer in layers]
            extranum = 0
            while workspace_newname in layernames:
                extranum += 1
                workspace_newname = '%s-%d' % (workspace_name, extranum)

        corebase_files = self.d.getVar('COREBASE_FILES').split()
        corebase_files = [corebase + '/' +x for x in corebase_files]
        # Make sure bitbake goes in
        bitbake_dir = bb.__file__.rsplit('/', 3)[0]
        corebase_files.append(bitbake_dir)

        for layer in layers:
            layerconf = os.path.join(layer, 'conf', 'layer.conf')
            layernewname = os.path.basename(layer)
            workspace = False
            if os.path.exists(layerconf):
                with open(layerconf, 'r') as f:
                    if f.readline().startswith("# ### workspace layer auto-generated by devtool ###"):
                        if workspace_newname:
                            layernewname = workspace_newname
                            workspace = True
                        else:
                            bb.plain("NOTE: Excluding local workspace layer %s from %s" % (layer, self.context))
                            continue

            # If the layer was already under corebase, leave it there
            # since layers such as meta have issues when moved.
            layerdestpath = destdir
            if corebase == os.path.dirname(layer):
                layerdestpath += '/' + os.path.basename(corebase)
            # If the layer is located somewhere under the same parent directory
            # as corebase we keep the layer structure.
            elif os.path.commonpath([layer, corebase]) == os.path.dirname(corebase):
                layer_relative = os.path.relpath(layer, os.path.dirname(corebase))
                if os.path.dirname(layer_relative) != layernewname:
                    layerdestpath += '/' + os.path.dirname(layer_relative)

            layerdestpath += '/' + layernewname

            layer_relative = os.path.relpath(layerdestpath,
                                             destdir)
            # Treat corebase as special since it typically will contain
            # build directories or other custom items.
            if corebase == layer:
                copied_corebase = layer_relative
                bb.utils.mkdirhier(layerdestpath)
                for f in corebase_files:
                    f_basename = os.path.basename(f)
                    destname = os.path.join(layerdestpath, f_basename)
                    _smart_copy(f, destname)
            else:
                layers_copied.append(layer_relative)

                if os.path.exists(os.path.join(layerdestpath, 'conf/layer.conf')):
                    bb.note("Skipping layer %s, already handled" % layer)
                else:
                    _smart_copy(layer, layerdestpath)

            if workspace:
                # Make some adjustments original workspace layer
                # Drop sources (recipe tasks will be locked, so we don't need them)
                srcdir = os.path.join(layerdestpath, 'sources')
                if os.path.isdir(srcdir):
                    shutil.rmtree(srcdir)
                # Drop all bbappends except the one for the image the SDK is being built for
                # (because of externalsrc, the workspace bbappends will interfere with the
                # locked signatures if present, and we don't need them anyway)
                image_bbappend = os.path.splitext(os.path.basename(self.d.getVar('FILE')))[0] + '.bbappend'
                appenddir = os.path.join(layerdestpath, 'appends')
                if os.path.isdir(appenddir):
                    for fn in os.listdir(appenddir):
                        if fn == image_bbappend:
                            continue
                        else:
                            os.remove(os.path.join(appenddir, fn))
                # Drop README
                readme = os.path.join(layerdestpath, 'README')
                if os.path.exists(readme):
                    os.remove(readme)
                # Filter out comments in layer.conf and change layer name
                layerconf = os.path.join(layerdestpath, 'conf', 'layer.conf')
                with open(layerconf, 'r') as f:
                    origlines = f.readlines()
                with open(layerconf, 'w') as f:
                    for line in origlines:
                        if line.startswith('#'):
                            continue
                        line = line.replace('workspacelayer', workspace_newname)
                        f.write(line)

        # meta-skeleton layer is added as part of the build system
        # but not as a layer included in the build, therefore it is
        # not reported to the function caller.
        for layer in layers_copied:
            if layer.endswith('/meta-skeleton'):
                layers_copied.remove(layer)
                break

        return copied_corebase, layers_copied

def generate_locked_sigs(sigfile, d):
    bb.utils.mkdirhier(os.path.dirname(sigfile))
    depd = d.getVar('BB_TASKDEPDATA', False)
    tasks = ['%s:%s' % (v[2], v[1]) for v in depd.values()]
    bb.parse.siggen.dump_lockedsigs(sigfile, tasks)

def prune_lockedsigs(excluded_tasks, excluded_targets, lockedsigs, onlynative, pruned_output):
    with open(lockedsigs, 'r') as infile:
        bb.utils.mkdirhier(os.path.dirname(pruned_output))
        with open(pruned_output, 'w') as f:
            invalue = False
            for line in infile:
                if invalue:
                    if line.endswith('\\\n'):
                        splitval = line.strip().split(':')
                        if not splitval[1] in excluded_tasks and not splitval[0] in excluded_targets:
                            if onlynative:
                                if 'nativesdk' in splitval[0]:
                                    f.write(line)
                            else:
                                f.write(line)
                    else:
                        f.write(line)
                        invalue = False
                elif line.startswith('SIGGEN_LOCKEDSIGS'):
                    invalue = True
                    f.write(line)

def merge_lockedsigs(copy_tasks, lockedsigs_main, lockedsigs_extra, merged_output, copy_output=None):
    merged = {}
    arch_order = []
    with open(lockedsigs_main, 'r') as f:
        invalue = None
        for line in f:
            if invalue:
                if line.endswith('\\\n'):
                    merged[invalue].append(line)
                else:
                    invalue = None
            elif line.startswith('SIGGEN_LOCKEDSIGS_t-'):
                invalue = line[18:].split('=', 1)[0].rstrip()
                merged[invalue] = []
                arch_order.append(invalue)

    with open(lockedsigs_extra, 'r') as f:
        invalue = None
        tocopy = {}
        for line in f:
            if invalue:
                if line.endswith('\\\n'):
                    if not line in merged[invalue]:
                        target, task = line.strip().split(':')[:2]
                        if not copy_tasks or task in copy_tasks:
                            tocopy[invalue].append(line)
                        merged[invalue].append(line)
                else:
                    invalue = None
            elif line.startswith('SIGGEN_LOCKEDSIGS_t-'):
                invalue = line[18:].split('=', 1)[0].rstrip()
                if not invalue in merged:
                    merged[invalue] = []
                    arch_order.append(invalue)
                tocopy[invalue] = []

    def write_sigs_file(fn, types, sigs):
        fulltypes = []
        bb.utils.mkdirhier(os.path.dirname(fn))
        with open(fn, 'w') as f:
            for typename in types:
                lines = sigs[typename]
                if lines:
                    f.write('SIGGEN_LOCKEDSIGS_%s = "\\\n' % typename)
                    for line in lines:
                        f.write(line)
                    f.write('    "\n')
                    fulltypes.append(typename)
            f.write('SIGGEN_LOCKEDSIGS_TYPES = "%s"\n' % ' '.join(fulltypes))

    if copy_output:
        write_sigs_file(copy_output, list(tocopy.keys()), tocopy)
    if merged_output:
        write_sigs_file(merged_output, arch_order, merged)

def create_locked_sstate_cache(lockedsigs, input_sstate_cache, output_sstate_cache, d, fixedlsbstring="", filterfile=None):
    import shutil
    bb.note('Generating sstate-cache...')

    nativelsbstring = d.getVar('NATIVELSBSTRING')
    stdout, stderr = bb.process.run("PYTHONDONTWRITEBYTECODE=1 gen-lockedsig-cache %s %s %s %s %s" % (lockedsigs, input_sstate_cache, output_sstate_cache, nativelsbstring, filterfile or ''))
    bb.note(stdout)
    bb.note(stderr)
    if fixedlsbstring and nativelsbstring != fixedlsbstring:
        nativedir = output_sstate_cache + '/' + nativelsbstring
        if os.path.isdir(nativedir):
            destdir = os.path.join(output_sstate_cache, fixedlsbstring)
            for root, _, files in os.walk(nativedir):
                for fn in files:
                    src = os.path.join(root, fn)
                    dest = os.path.join(destdir, os.path.relpath(src, nativedir))
                    if os.path.exists(dest):
                        # Already exists, and it'll be the same file, so just delete it
                        os.unlink(src)
                    else:
                        bb.utils.mkdirhier(os.path.dirname(dest))
                        shutil.move(src, dest)

def check_sstate_task_list(d, targets, filteroutfile, cmdprefix='', cwd=None, logfile=None):
    import subprocess

    bb.note('Generating sstate task list...')

    if not cwd:
        cwd = os.getcwd()
    if logfile:
        logparam = '-l %s' % logfile
    else:
        logparam = ''
    cmd = "%sPYTHONDONTWRITEBYTECODE=1 BB_SETSCENE_ENFORCE=1 PSEUDO_DISABLED=1 oe-check-sstate %s -s -o %s %s" % (cmdprefix, targets, filteroutfile, logparam)
    env = dict(d.getVar('BB_ORIGENV', False))
    env.pop('BUILDDIR', '')
    env.pop('BBPATH', '')
    pathitems = env['PATH'].split(':')
    env['PATH'] = ':'.join([item for item in pathitems if not item.endswith('/bitbake/bin')])
    stdout, stderr = bb.process.run(cmd, stderr=subprocess.STDOUT, env=env, cwd=cwd, executable='/bin/bash')
    bb.note(stdout)
    bb.note(stderr)
