import os
import logging
import argparse
import re
from git import Repo
import github3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def broadcast_commit(repo_full_name, branch_regex, message, token=None):
    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    gh = github3.login(token=token)
    gh_repo = gh.repository(org, repo_name)

    prog = re.compile(branch_regex)

    for branch in gh_repo.branches():
        if prog.match(branch.name):
            logger.info(f'branch {branch.name}')
            remote_url = gh_repo.git_url.replace('git://', f'https://{token}:x-oauth-basic@')
            g_repo = clone_checkout_branch(remote_url, os.path.join('/tmp', repo_name), branch.name)
            g_repo.index.commit(message)
            origin = g_repo.remote(name='origin')
            origin.push()


def clone_checkout_branch(git_remote_url, local_repo, branch):
    repo = Repo.init(local_repo)
    if len(repo.remotes) == 0 or 'origin' not in [r.name for r in repo.remotes]:
        repo.create_remote('origin', git_remote_url)
    repo.git.fetch()
    repo.git.checkout(branch)
    return repo


def main():
    parser = argparse.ArgumentParser(description='Broadcast empty commit on branches')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    parser.add_argument('--branch', dest='branch',
                        help='branch regex')
    parser.add_argument('--message', dest='message',
                        help='commit message')
    args = parser.parse_args()

    # read organization and repository name
    repo_full_name = os.environ.get('GITHUB_REPOSITORY')
    broadcast_commit(repo_full_name, args.branch, args.message, token=args.token)


if __name__ == '__main__':
    main()