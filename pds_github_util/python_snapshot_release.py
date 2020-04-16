import os
import re
import glob
import logging
import glob
from .snapshot_release import snapshot_release_publication

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SNAPSHOT_TAG_SUFFIX = "+dev"

def python_get_version():
    version = python_get_version_from_init()
    if not version:
        version = python_get_version_from_setup()
    return version


def python_get_version_from_setup():
    setup_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'setup.py')
    prog = re.compile("version=.*")
    try:
        with open(setup_path, 'r') as f:
            for line in f:
                line = line.strip()
                if prog.match(line):
                    version = line[9:-2]
                    logger.info("version {version}")
                    return version
        return None
    except FileNotFoundError:
        return None

def python_get_version_from_init():
    init_path_pattern =  os.path.join(os.environ.get('GITHUB_WORKSPACE'), "*", "__init__.py")
    init_path = glob.glob(init_path_pattern)[0]
    try:
        with open(init_path) as fi:
            result = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fi.read())
            if result:
                return result.group(1)
            else:
                return None
    except FileNotFoundError:
        return None


def python_upload_assets(repo_name, tag_name, release):
    """
          Upload packages produced by python setup.py

    """
    package_pattern = os.path.join(os.environ.get('GITHUB_WORKSPACE'),
                                        'dist',
                                        '*')
    packages = glob.glob(package_pattern)
    for package in packages:
        with open(package, 'rb') as f_asset:
            asset_filename = os.path.basename(package)
            logger.info(f"Upload asset file {asset_filename}")
            release.upload_asset('application/zip',
                                 asset_filename,
                                 f_asset)


def main():
    snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, python_get_version, python_upload_assets)


if __name__ == "__main__":
    main()
