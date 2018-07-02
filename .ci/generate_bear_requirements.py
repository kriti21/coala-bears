#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import itertools
import json
import os
import sys
from collections import OrderedDict

from yaml import dump
from pyprint.NullPrinter import NullPrinter

from coalib.bears.BEAR_KIND import BEAR_KIND
from coalib.collecting.Collectors import collect_bears

from dependency_management.requirements.GemRequirement import GemRequirement
from dependency_management.requirements.NpmRequirement import NpmRequirement
from dependency_management.requirements.PipRequirement import PipRequirement

BEAR_REQUIREMENTS_YAML = "bear-requirements.yaml"

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

PROJECT_BEAR_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'bears'))

PINNED_PACKAGES = (
   'radon',
   'lxml',
   'vim-vint',
)

def get_args():
    parser = argparse.ArgumentParser(
        description='This program generates a yaml requirement file for '
                    'installation of linters that are used by the bears.')
    parser.add_argument('--output', '-o',
                        help='name of file to generate, or - for stdout',
                        default=os.path.join(PROJECT_DIR,
                                             BEAR_REQUIREMENTS_YAML))
    parser.add_argument('--bear-dirs', '-d', nargs='+', metavar='DIR',
                        help='additional directories which may contain bears')

    args = parser.parse_args()

    return args


def get_all_bears(bear_dirs):
    local_bears, global_bears = collect_bears(
        bear_dirs,
        ['**'],
        [BEAR_KIND.LOCAL, BEAR_KIND.GLOBAL],
        warn_if_unused_glob=False)
    return list(itertools.chain(local_bears, global_bears))


def get_inherited_requirements():
    inherited_requirements = set()

    in_inherited = False
    with open(os.path.join(PROJECT_DIR, 'requirements.txt'), 'r') as file:
        for line in file.read().splitlines():
            if 'inherited' in line:
                in_inherited = True
                continue
            if in_inherited:
                if line.startswith('# '):
                    requirement = line[2:]
                    inherited_requirements.add(requirement.replace('-', '_'))
                    inherited_requirements.add(requirement.replace('_', '-'))
                else:
                    in_inherited = False

    return inherited_requirements


def get_all_requirements(bears):
    pip_requirements = []
    npm_requirements = []
    gem_requirements = []

    for bear in bears:
        for requirement in bear.REQUIREMENTS:
            if isinstance(requirement, PipRequirement) and \
               requirement not in pip_requirements:
                pip_requirements.append(requirement)
            elif isinstance(requirement, NpmRequirement) and \
               requirement not in npm_requirements:
                npm_requirements.append(requirement)
            elif isinstance(requirement, GemRequirement) and \
               requirement not in gem_requirements:
                gem_requirements.append(requirement)

    return (
        sorted(pip_requirements, key=lambda requirement: requirement.package),
        sorted(npm_requirements, key=lambda requirement: requirement.package),
        sorted(gem_requirements, key=lambda requirement: requirement.package)
        )


def _to_entry(obj, version=None):
    entry = {}

    if version:
        entry['version'] = version
    elif obj.version:
        entry['version'] = obj.version
    else:
        return True

    return entry


def get_gem_requirements(requirements):
    gem_dependencies = {}

    for requirement in requirements:
        gem_dependencies[requirement.package] = _to_entry(requirement)

    return gem_dependencies


def get_npm_requirements(requirements):
    npm_dependencies = {}

    for requirement in requirements:
        package_name = requirement.package
        req_version = requirement.version
        if req_version:
            if req_version[0] not in ('<', '>', '~', '='):
                req_version = "~" + req_version
        npm_dependencies[package_name] = _to_entry(requirement, req_version)

    return npm_dependencies


def get_pip_requirements(requirements):
    inherited_requirements = get_inherited_requirements()

    pip_requirements = {}

    for requirement in requirements:
        if requirement.package in inherited_requirements:
            continue

        package_name = requirement.package
        req_version = None
        if requirement.version:
            marker = '==' if requirement.package in PINNED_PACKAGES else '~='
            req_version = '{0}{1}'.format(marker, requirement.version)

        pip_requirements[package_name] = _to_entry(requirement, req_version)

    return pip_requirements


if __name__ == '__main__':
    args = get_args()

    bear_dirs = [PROJECT_BEAR_DIR]

    if args.bear_dirs is not None:
        bear_dirs.extend(args.bear_dirs)

    pip_reqs, npm_reqs, gem_reqs = (
        get_all_requirements(get_all_bears(bear_dirs)))

    requirements = {}
    requirements['overrides'] = 'coala-build.yaml'
    requirements['pip_requirements'] = get_pip_requirements(pip_reqs)
    requirements['npm_requirements'] = get_npm_requirements(npm_reqs)
    requirements['gem_requirements'] = get_gem_requirements(gem_reqs)

    output = None

    if args.output == '-':
        output = sys.stdout
    else:
        output = open(args.output, 'w')

    dump(requirements, output, default_flow_style=False)
    output.close()
