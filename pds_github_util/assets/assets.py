import argparse
import logging
import os
import sys

from zipfile import ZipFile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_asset(release, output_path, file_extension=None):
    """Download asset from Github"""
    for _asset in release.assets():
        # print(a.name)
        if (_asset.name.endswith(file_extension)):
            logger.info(f'Downloading asset {_asset.name}')
            _output = os.path.join(output_path, _asset.name)
            _asset.download(path=_output)
            break

    return _output


def unzip_asset(inzip, output_path):
    """Unzip Zip package of assets."""
    if not os.path.exists(inzip):
        raise Exception(f'Github Asset "{inzip}" not found. Check release.')

    if not os.path.exists(output_path):
        raise Exception(f'Output path "{output_path}" not found.')

    logger.info(f'Unzipping asset {inzip}')
    with ZipFile(inzip, 'r') as _zip_ref:
        _zip_ref.extractall(output_path)
        _outdir = os.path.join(output_path, _zip_ref.namelist()[0])

    return _outdir


def zip_assets(file_paths, outzip):
    """Zip assets into one package."""
    if os.path.exists(outzip):
        raise Exception(f'"{outzip}" already exists.')

    if not os.path.exists(os.path.dirname(outzip)):
        os.makedirs(os.path.dirname(outzip))

    logger.info(f'zipping assets')
    with ZipFile(outzip,'w') as z:
        for f in file_paths: 
            z.write(f, os.path.basename(f))

    logger.info(f'zip package created: {outzip}')
