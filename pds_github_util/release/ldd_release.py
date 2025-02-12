"""
LDD Snapshot and Release Util

Tool to tag LDD releases and upload ZIP of assets
"""

import argparse
import github3
import os
import logging
import glob
import sys
import traceback
import datetime

import xml.etree.ElementTree as ETree

from pds_github_util.release.release import delete_snapshot_releases
from pds_github_util.assets.assets import zip_assets
from pds_github_util.tags.tags import Tags
from pds_github_util.utils import addStandardArguments


_logger = logging.getLogger(__name__)

SNAPSHOT_TAG_SUFFIX = '-dev'
PDS_NS = 'http://pds.nasa.gov/pds4/pds/v1'
LDD_NAME_BASE = 'PDS4_{}_{}'
STAGING_DIR = f'/tmp/out_{datetime.datetime.utcnow().timestamp()}'
RELEASE_NAME = '{}_{}'

def convert_pds4_version_to_alpha(pds4_version):
    pds4_version_short = ''
    version_list = pds4_version.split('.')
    for num in version_list:
        if int(num) >= 10:
            pds4_version_short += chr(ord('@') + (int(num) % 10 + 1))
        else:
            pds4_version_short += num

    return pds4_version_short


def find_dependency_ingest_ldds(ingest_ldd_src_dir):
    # Get any dependencies first
    dependencies_path = os.path.join(ingest_ldd_src_dir, 'dependencies')
    dependency_ldds = glob.glob(os.path.join(dependencies_path, '*', 'src', '*IngestLDD*.xml'))
    return dependency_ldds


def find_primary_ingest_ldd(ingest_ldd_src_dir):
    ingest_ldd = glob.glob(os.path.join(ingest_ldd_src_dir, '*IngestLDD*.xml'))
    return ingest_ldd


def get_latest_release(token, dev=False):
    _tags = Tags(GITHUB_ORG, GITHUB_REPO, token=token)
    return _tags._repo.release_from_tag(_tags.get_latest_tag(dev=dev))


def create_release(repo, branch_name, tag_name, tagger, prerelease=False):
    """Create a tag and new release.
    
    From the latest commit on branch_name. Push the assets created in target directory.
    """
    if not prerelease:
        _logger.info(f"create new release {tag_name}")
    else:
        _logger.info("create new SNAPSHOT release")

    our_branch = repo.branch(branch_name)
    repo.create_tag(tag_name,
                    'SNAPSHOT release',
                    our_branch.commit.sha,
                    "commit",
                    tagger)

    # create the release
    release = repo.create_release(tag_name, target_commitish=branch_name, name=tag_name, prerelease=prerelease)
    return release


def get_info(ingest_ldd_src_dir):
    """Get LDD version and namespace id."""
    # look in src directory for ingest LDD
    ingest_ldd = find_primary_ingest_ldd(ingest_ldd_src_dir)

    # get ingest ldd version
    tree = ETree.parse(ingest_ldd[0])
    root = tree.getroot()
    ldd_version = root.findall(f'.//{{{PDS_NS}}}ldd_version_id')[0].text
    ns_id = root.findall(f'.//{{{PDS_NS}}}namespace_id')[0].text
    return ingest_ldd, ns_id, ldd_version


def find_ldds(ldd_output_path, namespace_id, ldd_version, pds4_version):
    """Search repo for LDDs."""
    _logger.info('find and group LDDs into applicable groupings')
    ldd_dict = {}

    pds4_alpha_version = convert_pds4_version_to_alpha(pds4_version)
    ldd_alpha_version = convert_pds4_version_to_alpha(ldd_version)

    release_name = RELEASE_NAME.format(pds4_alpha_version, ldd_alpha_version)
    path_pattern = os.path.join(ldd_output_path, '*', f'*{pds4_alpha_version}*')
    all_ldds = glob.glob(path_pattern)

    # pkg_name = LDD_NAME_BASE.format(namespace_id.upper(), pds4_alpha_version, ldd_alpha_version) 
    ldd_dict[release_name] = []
    ldd_dict[f'{release_name}_dependencies'] = []
    for ldd in all_ldds:
        if namespace_id.upper() in ldd and ldd_alpha_version in ldd:
            ldd_dict[release_name].append(ldd)
        elif namespace_id.upper() not in ldd:
            ldd_dict[f'{release_name}_dependencies'].append(ldd)

    return ldd_dict


def package_assets(ingest_ldd, ldds, namespace_id):
    """Zip up LDDs."""
    # copy all ZIPs to current app dir to ensure 
    assets = []
    for release_name in ldds.keys():
        if ldds[release_name]:
            outzip = os.path.join(STAGING_DIR, LDD_NAME_BASE.format(namespace_id.upper(), release_name) + '.zip')
            pkg_files = list(ldds[release_name])
            pkg_files.extend(ingest_ldd)
            zip_assets(pkg_files, outzip)
            assets.append(outzip)

    return assets


def ldd_upload_assets(release, assets):
    """Zip up LDDs."""
    for a in assets:
        with open(a, 'rb') as f_asset:
            asset_filename = os.path.basename(a)
            _logger.info(f"upload asset file {asset_filename}")
            release.upload_asset('application/zip',
                                 asset_filename,
                                 f_asset)


def main():
    """Main."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)
    addStandardArguments(parser)
    parser.add_argument('--ldd_output_path',
                        help='directory to output generated LDDs',
                        required=True)
    parser.add_argument('--ingest_ldd_src_dir',
                        help='/path/to/src/ dir for IngestLDD file',
                        default=os.path.join('tmp', 'logs'),
                        required=True)
    parser.add_argument('--dev',
                        help='flag to indicate this is a dev release',
                        action='store_true', default=False)
    parser.add_argument('--token',
                        help='github token')
    parser.add_argument('--repo_name',
                        help='full name of github repo (e.g. user/repo)')
    parser.add_argument('--workspace',
                        help=('path of workspace. defaults to current working directory if this '
                              'or GITHUB_WORKSPACE not specified')
                        )
    parser.add_argument('--pds4_version',
                        help='pds4 IM version')

    args, unknown = parser.parse_known_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")
    if args.loglevel != logging.DEBUG:
        # Quiet github3 logging
        logging.getLogger('github3').setLevel(level=logging.WARNING)

    token = args.token or os.environ.get('GITHUB_TOKEN')

    if not token:
        _logger.error('Github token must be provided or set as environment variable (GITHUB_TOKEN).')
        sys.exit(1)

    repo_full_name = args.repo_name or os.environ.get('GITHUB_REPOSITORY')
    if not repo_full_name:
        _logger.error('Github repository must be provided or set as environment variable (GITHUB_REPOSITORY).')
        sys.exit(1)
    org = repo_full_name.split('/')[0]
    repo_name = repo_full_name.split('/')[1]

    workspace = args.workspace or os.environ.get('GITHUB_WORKSPACE')
    if not workspace:
        workspace = os.getcwd()
        os.environ['GITHUB_WORKSPACE'] = workspace

    try:
        ingest_ldd, namespace_id, ldd_version = get_info(args.ingest_ldd_src_dir)

        ldd_dict = find_ldds(args.ldd_output_path, namespace_id, ldd_version, args.pds4_version)

        assets = package_assets(ingest_ldd, ldd_dict, namespace_id)

        tagger = {"name": "PDSEN CI Bot",
                  "email": "pdsen-ci@jpl.nasa.gov"}
        gh = github3.login(token=token)
        repo = gh.repository(org, repo_name)

        delete_snapshot_releases(repo, SNAPSHOT_TAG_SUFFIX)
        for release_name in ldd_dict.keys():
            if 'dependencies' not in release_name:
                if args.dev:
                    tag_name = release_name + SNAPSHOT_TAG_SUFFIX
                else:
                    tag_name = release_name

                # Check tag exists before continuing
                tags = Tags(org, repo_name, token=token)
                if not tags.get_tag(tag_name):
                    release = create_release(repo, "main", tag_name, tagger, args.dev)
                    _logger.info("upload assets")
                    ldd_upload_assets(release, assets)
                else:
                    _logger.warning(f"tag {tag_name} already exists. skipping...")

    except Exception:
        traceback.print_exc()
        sys.exit(1)

    _logger.info('SUCCESS: LDD release complete.')


if __name__ == "__main__":
    main()
