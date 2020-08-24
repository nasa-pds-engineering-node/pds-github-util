'''
PDS Validate Wrapper

Tool that downloads PDS Validate Tool and executes based upon
input arguments.
'''
import argparse
import glob
import logging
import os
import requests
import sys
import traceback

from datetime import datetime
from subprocess import Popen, CalledProcessError, PIPE, STDOUT
from zipfile import ZipFile

from pds_github_util.tags.tags import Tags
from pds_github_util.assets.assets import download_asset, unzip_asset
from pds_github_util.utils.ldd_gen import convert_pds4_version_to_alpha

GITHUB_ORG = 'NASA-PDS'
GITHUB_REPO = 'validate'

# Schema download constants
PDS_SCHEMA_URL = 'https://pds.nasa.gov/pds4/pds/v1/'
PDS_DEV_SCHEMA_URL = 'https://pds.nasa.gov/datastandards/schema/develop/pds/'
DOWNLOAD_PATH = '/tmp'

# Quiet github3 logging
logger = logging.getLogger('github3')
logger.setLevel(level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_latest_release(token, dev=False):
    _tags = Tags(GITHUB_ORG, GITHUB_REPO, token=token)
    return _tags._repo.release_from_tag(_tags.get_latest_tag(dev=dev))


def exec_validate(executable, args, log_path=os.path.expanduser('~')):
    dtime = datetime.now().strftime('%Y%m%d%H%M%S')
    log_out = os.path.join(log_path, f'validate_report_{dtime}.txt')
    if not os.path.exists(os.path.dirname(log_out)):
        os.makedirs(os.path.dirname(log_out))

    cmd = ['bash', executable ]
    # print(args)
    cmd.extend(args)
    with Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True) as p:
        with open(log_out, 'w') as f:
            for line in p.stdout:
                print(line, end='') # process line here
                f.write(line)

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)


def download_schemas(download_path, pds4_version, dev_release=False):
    pds4_version_short = convert_pds4_version_to_alpha(pds4_version)
    try:
        if not dev_release:
            base_url = PDS_SCHEMA_URL
        else:
            base_url = PDS_DEV_SCHEMA_URL

        fname = 'PDS4_PDS_' + pds4_version_short
        for suffix in ['.xsd', '.sch']:
            logger.info(f'Downloading {base_url + fname + suffix}')
            r = requests.get(base_url + fname + suffix, allow_redirects=True)
            with open(os.path.join(download_path, fname + suffix), 'wb') as f:
                f.write(r.content)

    except Exception as e:
        logger.error('Failure attempting to download schemas.')
        raise e
        traceback.print_exc
        sys.exit(1)


def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    parser.add_argument('--deploy_dir',
                        help='directory to deploy the validate tool on the file system',
                        default='/tmp')
    parser.add_argument('--token',
                        help='github token')
    parser.add_argument('--schemas',
                        help='path(s) to schemas to validate against')
    parser.add_argument('--schematrons',
                        help='path(s) to schematrons to validate against')
    parser.add_argument('--skip_content_validation',
                        help='validate: skip content validation',
                        action='store_true', default=False)
    parser.add_argument('--failure_expected', dest='failure_expected',
                        help='validate expected to fail',
                        action='store_true', default=False)
    parser.add_argument('--datapath',
                        help='path(s) to data to validate',
                        required=True)
    parser.add_argument('--output_log_path',
                        help='path(s) to output validate run log file',
                        default=os.path.join('tmp', 'logs'))
    parser.add_argument('--with_pds4_version',
                        help=('force the following PDS4 version. software will '
                              'download and validate with this version of the '
                              'PDS4 Information Model. this version should be '
                              'the semantic numbered version. e.g. 1.14.0.0'))
    parser.add_argument('--development_release',
                        help=('flag to indicate this should be tested with a '
                              'development release of the PDS4 Standard.'),
                        action='store_true', default=False)

    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')

    if not token:
        logger.error(f'Github token must be provided or set as environment variable (GITHUB_TOKEN).')
        sys.exit(1)

    try:
        validate_args = ['-R', 'pds4.label']

        if args.skip_content_validation:
            validate_args.append('--skip-content-validation')

        schemas = []
        if args.schemas:
            schemas.extend(glob.glob(args.schemas, recursive=True))

        schematrons = []
        if args.schematrons:
            # validate_args.append('-S')
            schematrons.extend(glob.glob(args.schematrons, recursive=True))

        if args.development_release:
            if not args.with_pds4_version:
                raise argparse.ArgumentError('--with_pds4_version must be specified when using --development_release')

        if args.with_pds4_version:
            download_schemas(DOWNLOAD_PATH, args.with_pds4_version, dev_release=args.development_release)
            schemas.extend(glob.glob(os.path.join(DOWNLOAD_PATH, '*.xsd')))
            schematrons.extend(glob.glob(os.path.join(DOWNLOAD_PATH, '*.sch')))

        if schemas:
            validate_args.append('-x')
            validate_args.extend(schemas)

        if schematrons:
            validate_args.append('-S')
            validate_args.extend(schematrons)

        validate_args.append('-t')
        validate_args.extend(glob.glob(args.datapath, recursive=True))


        pkg = download_asset(get_latest_release(token), args.deploy_dir, file_extension='.zip')
        sw_dir = unzip_asset(pkg, args.deploy_dir)

        exec_validate(os.path.join(sw_dir, 'bin', 'validate'), validate_args, log_path=args.output_log_path)
    except CalledProcessError:
        if not args.failure_expected:
            logger.error(f'FAILED: Validate failed unexpectedly. See output logs.')
            sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

    logger.info(f'SUCCESS: Validation complete.')

if __name__ == '__main__':
    main()
