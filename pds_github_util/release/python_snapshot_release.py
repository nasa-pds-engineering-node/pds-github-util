import os
import re
import logging
import glob
from pathlib import Path
from pds_github_util.release.release import release_publication

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SNAPSHOT_TAG_SUFFIX = "-dev"

def python_get_version(workspace=None):
    get_version_funcs = [
        'python_get_version_from_version_txt',
        'python_get_version_from_init',
        'python_get_version_from_setup'
    ]
    for get_version_func in get_version_funcs:
        v = eval(get_version_func)(workspace)
        if v:
            return v


def python_get_version_from_setup(workspace=None):
    logger.info("get version from setup.py file")
    workspace = workspace or os.environ.get('GITHUB_WORKSPACE')
    setup_path = os.path.join(workspace, 'setup.py')
    prog = re.compile("version=.*")
    try:
        with open(setup_path, 'r') as f:
            for line in f:
                line = line.strip()
                if prog.match(line):
                    version = line[9:-2]
                    logger.info(f'version {version}')
                    return version
        return None
    except FileNotFoundError:
        return None


def python_get_version_from_init(workspace=None):
    logger.info("get version from package __init__.py file")
    workspace = workspace or os.environ.get('GITHUB_WORKSPACE')
    init_path_pattern =  os.path.join(workspace, "*", "__init__.py")
    found_init = glob.glob(init_path_pattern)
    if len(found_init):
        init_path = found_init[0]
        with open(init_path) as fi:
            result = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fi.read())
            if result:
                version = result.group(1)
                logger.info(f"version {version}")
                return version
            else:
                return None
    else:
        return None

def python_get_version_from_version_txt(workspace=None):
    logger.info("get version from version.text file")
    version_text_filename = 'version.txt'
    try:
        versiontext_file = next(Path('src').rglob(version_text_filename))
        with open(versiontext_file) as f:
            version = f.read()
        return version.strip()
    except StopIteration:
        logger.info(f"no {version_text_filename} file found")
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
    release_publication(SNAPSHOT_TAG_SUFFIX, python_get_version, python_upload_assets)


if __name__ == "__main__":
    main()
