import os
import re
import glob
import logging
from .snapshot_release import snapshot_release_publication

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SNAPSHOT_TAG_SUFFIX = "+dev"


def python_get_version():
    setup_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'setup.py')
    prog = re.compile("version=.*")
    with open(setup_path, 'r') as f:
        for line in f:
            line = line.strip()
            if prog.match(line):
                return line[9:-2]


def python_upload_assets(repo_name, tag_name, release):
    """
          Upload packages produced by python setup.py

    """
    # upload assets
    targz_package = os.path.join(os.environ.get('GITHUB_WORKSPACE'),
                                 'dist',
                                 f'{repo_name}-{tag_name}.tar.gz')
    with open(targz_package, 'rb') as f_asset:
        asset_filename = f'{repo_name}-{tag_name}.tar.gz'
        logger.info(f"Upload asset file {asset_filename}")
        release.upload_asset('application/tar+gzip',
                             asset_filename,
                             f_asset)

    whl_packages_pattern = os.path.join(os.environ.get('GITHUB_WORKSPACE'),
                                        'dist',
                                        f'{repo_name}-{tag_name}-*-*-*.whl')
    whl_packages = glob.glob(whl_packages_pattern)
    for whl_package in whl_packages:
        with open(whl_package, 'rb') as f_asset:
            asset_filename = os.path.basename(whl_package)
            logger.info(f"Upload asset file {asset_filename}")
            release.upload_asset('application/zip',
                                 asset_filename,
                                 f_asset)


def main():
    snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, python_get_version, python_upload_assets)


if __name__ == "__main__":
    main()
