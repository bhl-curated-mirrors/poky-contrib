#!/usr/bin/env python
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# patchtestdata: module used to share command line arguments between
#                patchtest & test suite and a data store between test cases
#
# Copyright (C) 2016 Intel Corporation
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
#
# Author: Leo Sandoval <leonardo.sandoval.gonzalez@linux.intel.com>
#
# NOTE: Strictly speaking, unit test should be isolated from outside,
#       but patchtest test suites uses command line input data and
#       pretest and test test cases may use the datastore defined
#       on this module

import os
import argparse
import json
import collections
from tempfile import mkstemp
import logging

logger=logging.getLogger('patchtest')
info=logger.info

# Data store commonly used to share values between pre and post-merge tests
PatchTestDataStore = collections.defaultdict(str)

class PatchTestStdIn(object):
    """Gather patch data from standard input"""

    @classmethod
    def namespace_stdin(cls, inputlines):
        (_, patch) = mkstemp()
        with open(patch,'w') as patchfd:
            for line in inputlines:
                patchfd.write(line)
        return patch

class PatchTestArgs(object):
    """Abstract the patchtest argument parser"""

    @classmethod
    def set_namespace(cls):
        parser = cls.get_parser()
        parser.parse_args(namespace=cls)

    @classmethod
    def get_parser(cls):
        parser = argparse.ArgumentParser()

        parser.add_argument('patch', metavar='PATCH',
                            help='The patch to be tested by patchtest')

        parser.add_argument('--repo-dir', '-r',
                            dest='repodir',
                            type=os.path.abspath,
                            default=os.getcwd(),
                            help="Name of the repository where patch is merged")

        parser.add_argument('--top-level-directory', '-t',
                            dest='topdir',
                            default=None,
                            help="Top level directory of project (defaults to start directory)")

        startdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests')
        parser.add_argument('--start-dir', '-s',
                            dest='startdir',
                            type=os.path.abspath,
                            default=startdir,
                            help="Directory to start discover")

        parser.add_argument('--pattern', '-p',
                            dest='pattern',
                            default='test*.py',
                            help="Pattern to match test files")

        parser.add_argument('--base-branch', '-b',
                            dest='basebranch',
                            help="Branch name used by patchtest to branch from. By default, it uses the current one.")

        parser.add_argument('--base-commit', '-c',
                            dest='basecommit',
                            help="Commit ID used by patchtest to branch from. By default, it uses HEAD.")

        parser.add_argument('--debug', '-d',
                            action='store_true',
                            help='Enable debug output')

        parser.add_argument('--json', '-j',
                            action='store_true',
                            dest='json',
                            help='Print results in JSON format')

        return parser

# Class used as a namespace to share data from patchtest to the test suites
class PatchTestInput(PatchTestArgs, PatchTestStdIn):
    """ PatchTest wrapper input class"""
    pass
