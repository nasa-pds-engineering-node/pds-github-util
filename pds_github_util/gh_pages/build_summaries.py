import os
import argparse
from functools import partial
from shutil import copytree, rmtree, copy
from pds_github_util.branches.git_actions import loop_checkout_on_branch
from pds_github_util.gh_pages.summary import write_build_summary
from pds_github_util.gh_pages.root_index import update_index


def copy_resources():
    resources = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'resources')
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


def main():
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--output', dest='output',
                        default='.',
                        help='markdown output file name')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    args = parser.parse_args()

    copy_resources()

    loop_checkout_on_branch('NASA-PDS/pdsen-corral',
                            '[0-9]+\.[0-9]+',
                            partial(write_build_summary,
                                    root_dir=os.getcwd(),
                                    gitmodules='/tmp/pdsen-corral/.gitmodules',
                                    token=args.token,
                                    dev=False),
                            token=args.token,
                            local_git_tmp_dir='/tmp')

    loop_checkout_on_branch('NASA-PDS/pdsen-corral',
                            'master',
                            partial(write_build_summary,
                                    root_dir=os.getcwd(),
                                    gitmodules='/tmp/pdsen-corral/.gitmodules',
                                    token=args.token,
                                    dev=True),
                            token=args.token,
                            local_git_tmp_dir='/tmp')



    print(args.output)




if __name__ == "__main__":
    main()

