"""LDD Release.

Tool to clone an LDD Repo and deploy either a development or
operational release for an LDD

For development release:
* required inputs: pds4 version
* execution for each repo:
    * clone the repo
    * update CI/CD YAML with:
        * new PDS4 version
        * add to includes portion of YAML
          - pds4_version: '1.15.0.0'
            lddtool_development_release: True
            pds4_development_release: True
    * push update to new branch
    * use github3 to create PR

"""
import argparse
import collections
import github3
import glob
import logging
import os
import requests
import shutil
import sys
import traceback
import yaml

from functools import partial
from six import iteritems
from subprocess import Popen, CalledProcessError, PIPE, STDOUT
from yaml import load, dump, Loader, Dumper
from yaml.resolver import Resolver

from pds_github_util.utils.ldd_gen import convert_pds4_version_to_alpha
from pds_github_util.branches.git_actions import loop_checkout_on_branch

GITHUB_ORG = 'pds-data-dictionaries'

# Discipline LDD Repos
# GITHUB_LDD_REPOS = [ 'ldd-multi', 'ldd-particle', 'ldd-wave', 'ldd-rings',
#                      'ldd-img', 'ldd-disp', 'ldd-msn', 'ldd-msn_surface',
#                      'ldd-proc', 'ldd-img_surface', 'ldd-ctli', 'ldd-speclib',
#                      'ldd-msss_cam_mh', 'ldd-cart', 'ldd-geom' ] #'ldd-spectral' ]
GITHUB_LDD_REPOS = [ 'ldd-multi' ]

EXTRA_HARDCODE_INCLUDE = {'pds4_version': '1.14.0.0',
                  'lddtool_development_release': True}

# Quiet github3 logging
# logger = logging.getLogger('github3')
# logger.setLevel(level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(iteritems(data))

def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)

# remove resolver entries for On/Off/Yes/No
for ch in "OoYyNn":
    if len(Resolver.yaml_implicit_resolvers[ch]) == 1:
        del Resolver.yaml_implicit_resolvers[ch]
    else:
        Resolver.yaml_implicit_resolvers[ch] = [x for x in
                Resolver.yaml_implicit_resolvers[ch] if x[0] != 'tag:yaml.org,2002:bool']

# def maven_get_version():
#     # read current version
#     pom_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'pom.xml')
#     pom_doc = etree.parse(pom_path)
#     r = pom_doc.xpath('/pom:project/pom:version',
#                       namespaces={'pom': 'http://maven.apache.org/POM/4.0.0'})
#     return r[0].text


# def maven_upload_assets(repo_name, tag_name, release):
#     assets = ['*-bin.tar.gz', '*-bin.zip', '*.jar']
#     for dirname, subdirs, files in os.walk(os.environ.get('GITHUB_WORKSPACE')):
#         if dirname.endswith('target'):
#             for extension in assets:
#                 for filename in fnmatch.filter(files, extension):
#                     with open(os.path.join(dirname, filename), 'rb') as f_asset:
#                         release.upload_asset('application/tar+gzip',
#                                              filename,
#                                              f_asset)


# def clone_repo(repo_name):
#     loop_checkout_on_branch()

def set_include_config(matrix_obj, pds4_version):
    # remove include object if it already exists
    try:
        del matrix_obj['include']
    except KeyError as e:
        None

    # Set the include object
    matrix_obj['include'] = []
    # TODO - remove after Build 11.0 is released
    matrix_obj['include'].append(EXTRA_HARDCODE_INCLUDE)
    matrix_obj['include'].append(
        {
            'pds4_version': pds4_version,
            'lddtool_development_release': True,
            'pds4_development_release': True
        })

def update_action(root_dir='.', github_action_path=None, pds4_version=None, development_release=False):
    # if not output_file_name:
    action_file_name = os.path.join(root_dir, github_action_path)
    print(action_file_name)

    with open(action_file_name, 'rb') as yml:
        doc = load(yml, Loader=Loader)

        # pds4_versions = doc['jobs']['build']['strategy']['matrix']['pds4_version']
        doc['jobs']['build']['strategy']['matrix']['pds4_version'].append(pds4_version)
        print(doc['jobs']['build']['strategy']['matrix']['pds4_version'])

        if development_release:
            set_include_config(doc['jobs']['build']['strategy']['matrix'], pds4_version)

        print(dump(doc, Dumper=Dumper))


def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    parser.add_argument('--workspace',
                        help='path to clone and update repos',
                        default='/tmp')
    parser.add_argument('--github_action_path',
                        help='filepath to github action file',
                        default='.github/workflows/ldd-ci.yml')
    parser.add_argument('--development_release',
                        help='flag to denote this is a development release of the PDS4 IM',
                        action='store_true', default=False)
    parser.add_argument('--token',
                        help='github token')
    # parser.add_argument('--output_log_path',
    #                     help='path(s) to output validate run log file',
    #                     default=os.path.join('tmp', 'logs'))
    parser.add_argument('--with_pds4_version',
                        help=('adds new PDS4 version to the CI / CD config. '
                              'this version should be the semantic numbered '
                              'version. e.g. 1.14.0.0'),
                        required=True)
    parser.add_argument('--repos',
                        help=('list of names of all LDDs to include in this '
                              'processing'),
                        type=list,
                        default=GITHUB_LDD_REPOS)
    # parser.add_argument('--use_lddtool_unstable',
    #                     help=('force the use of the latest unstable LDDTool release. '
    #                           'by default, uses latest stable release'),
    #                     action='store_true', default=False)

    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')

    for repo in args.repos:
        repo_name = f'{GITHUB_ORG}/{repo}'
        root_dir = os.path.join(args.workspace, repo)
        for branch in loop_checkout_on_branch(repo_name,
                                              'master',
                                              partial(update_action,
                                                      root_dir=root_dir,
                                                      github_action_path=args.github_action_path,
                                                      pds4_version=args.with_pds4_version,
                                                      development_release=args.development_release),
                                              token=token,
                                              local_git_tmp_dir='/tmp'):
            print(branch)

if __name__ == "__main__":
    main()
