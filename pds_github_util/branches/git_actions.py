import os
import logging
import shutil
import re
from git import Repo
import github3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def loop_checkout_on_branch(repo_full_name, branch_regex, callback, token=None, local_git_tmp_dir='/tmp'):
    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    gh = github3.login(token=token)
    gh_repo = gh.repository(org, repo_name)

    prog = re.compile(branch_regex)

    local_path = os.path.join(local_git_tmp_dir, repo_name)
    if os.path.exists(local_path):
      shutil.rmtree(local_path)

    for branch in gh_repo.branches():
        if prog.match(branch.name):
            logger.info(f'branch {branch.name}')
            remote_url = gh_repo.git_url.replace('git://', f'https://{token}:x-oauth-basic@')
            g_repo = clone_checkout_branch(remote_url, local_path, branch.name)

            yield callback()



def ping_repo_branch(repo_full_name, branch, message, token=None):
    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    gh = github3.login(token=token)
    gh_repo = gh.repository(org, repo_name)

    remote_url = gh_repo.git_url.replace('git://', f'https://{token}:x-oauth-basic@')
    g_repo = clone_checkout_branch(remote_url, os.path.join('/tmp', repo_name), branch)
    g_repo.index.commit(message)
    origin = g_repo.remote(name='origin')
    origin.push()



def clone_checkout_branch(git_remote_url, local_repo, branch):
    os.makedirs(local_repo, exist_ok=True)
    repo = Repo.init(local_repo)
    if len(repo.remotes) == 0 or 'origin' not in [r.name for r in repo.remotes]:
        repo.create_remote('origin', git_remote_url)
    repo.git.fetch()
    repo.git.checkout(branch)
    repo.git.pull()
    return repo


