import os
import logging
import argparse
import sys
from pkg_resources import resource_filename
from functools import partial
from shutil import copytree, rmtree, copy
from pds_github_util.branches.git_actions import loop_checkout_on_branch
from pds_github_util.gh_pages.summary import write_build_summary
from pds_github_util.gh_pages.root_index import update_index
from pds_github_util.utils.tokens import GITHUB_TOKEN
from pds_github_util.utils import addStandardArguments


_logger = logging.getLogger(__name__)


def copy_resources():
    _logger.info("write static resources (img, config)...")
    resources = resource_filename(__name__, 'resources')
    for f in os.listdir(resources):
        i_p = os.path.join(resources, f)
        o_p = os.path.join(os.getcwd(), f)
        if os.path.isdir(i_p):
            if os.path.exists(o_p):
                rmtree(o_p, ignore_errors=True)
            copytree(i_p, o_p)
        else:
            if os.path.exists(o_p):
                os.remove(o_p)
            copy(i_p, os.getcwd())


def build_summaries(token, path=os.getcwd(), format='md', version_pattern=None):
    copy_resources()

    herds = []

    if not version_pattern:
        # dev release on main
        herd = next(loop_checkout_on_branch(
            'NASA-PDS/pdsen-corral',
            'main',
            partial(write_build_summary,
                root_dir=path,
                gitmodules='/tmp/pdsen-corral/.gitmodules',
                token=token,
                dev=True,
                format=format),
            token=token,
            local_git_tmp_dir='/tmp'))
        herds.append(herd)
        version_pattern = r'[0-9]+\.[0-9]+'

    # loop on selected version patterns
    for herd in loop_checkout_on_branch(
            'NASA-PDS/pdsen-corral',
            version_pattern,
            partial(write_build_summary,
                    root_dir=path,
                    gitmodules='/tmp/pdsen-corral/.gitmodules',
                    token=token,
                    dev=False,
                    format=format),
            token=token,
            local_git_tmp_dir='/tmp'):
        herds.append(herd)

    update_index(path, herds)


def main():
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    addStandardArguments(parser)
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    parser.add_argument('--path', dest='path', default='./output/',
                        help='directory where the summary will be created')
    parser.add_argument('--format', dest='format', default='rst',
                        help='format of the summary, accepted formats are md and rst')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")

    token = args.token or GITHUB_TOKEN
    if not token:
        _logger.error('Github token must be provided or set as environment variable (GITHUB_TOKEN).')
        sys.exit(1)

    build_summaries(token, args.path, args.format)


if __name__ == "__main__":
    main()
