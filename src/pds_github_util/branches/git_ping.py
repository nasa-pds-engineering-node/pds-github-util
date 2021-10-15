import argparse, logging
from pds_github_util.branches.git_actions import ping_repo_branch
from pds_github_util.utils import addStandardArguments


def main():
    parser = argparse.ArgumentParser(description='empty commit on a repo branch')
    addStandardArguments(parser)
    parser.add_argument('--repo', dest='repo',
                        help='repostory full name with owner, e.g. nasa-pds/pdsen-corral')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    parser.add_argument('--branch', dest='branch',
                        help='branch name')
    parser.add_argument('--message', dest='message',
                        help='commit message')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")
    
    # read organization and repository name
    ping_repo_branch(args.repo, args.branch, args.message, token=args.token)


if __name__ == '__main__':
    main()
