import argparse
import os
import logging
import github3
import sys


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_release(repo, repo_name, branch_name, tag_name, tagger, upload_assets):
    """Create a tag, if needed, and release.
    
    Push the assets created in target directory.
    """
    logger.info("create new release")

    our_branch = repo.branch(branch_name)
    repo.create_tag(tag_name,
                    f'release',
                    our_branch.commit.sha,
                    "commit",
                    tagger)

    # create the release
    release = repo.create_release(tag_name, target_commitish=branch_name, name=repo_name + " " + tag_name, prerelease=False)

    logger.info("upload assets")
    upload_assets(repo_name, tag_name, release)

def delete_snapshot_releases(_repo, suffix):
    """
        Delete all pre-existing snapshot releases
    """
    logger.info("delete previous releases")
    for release in _repo.releases():
        if release.tag_name.endswith(suffix):
            release.delete()


def create_snapshot_release(repo, repo_name, branch_name, tag_name, tagger, upload_assets):
    """
    Create a tag and new release from the latest commit on branch_name.
    Push the assets created in target directory.
    """
    logger.info("create new snapshot release")
    our_branch = repo.branch(branch_name)
    repo.create_tag(tag_name,
                    f'SNAPSHOT release',
                    our_branch.commit.sha,
                    "commit",
                    tagger)

    # create the release
    release = repo.create_release(tag_name, target_commitish=branch_name, name=repo_name + " " + tag_name, prerelease=True)

    logger.info("upload assets")
    upload_assets(repo_name, tag_name, release)


def release_publication(suffix, get_version, upload_assets):
    """
    Script made to work in the context of a github action.
    """
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    parser.add_argument('--repo_name',
                        help='full name of github repo (e.g. user/repo)')
    parser.add_argument('--workspace',
                        help='path of workspace. defaults to current working directory if this or GITHUB_WORKSPACE not specified')
    args, unknown = parser.parse_known_args()

    # read organization and repository name
    repo_full_name = args.repo_name or os.environ.get('GITHUB_REPOSITORY')
    if not repo_full_name:
        logger.error(f'Github repository must be provided or set as environment variable (GITHUB_REPOSITORY).')
        sys.exit(1)

    workspace = args.workspace or os.environ.get('GITHUB_WORKSPACE')
    if not workspace:
        workspace = os.getcwd()
        os.environ['GITHUB_WORKSPACE'] = workspace

    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        logger.error(f'Github token must be provided or set as environment variable (GITHUB_TOKEN).')

    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    tag_name = get_version()
    print(tag_name)
    tagger = {"name": "PDSEN CI Bot",
              "email": "pdsen-ci@jpl.nasa.gov"}

    gh = github3.login(token=token)
    repo = gh.repository(org, repo_name)

    delete_snapshot_releases(repo, suffix)
    if tag_name.endswith(suffix):
        create_snapshot_release(repo, repo_name, "master", tag_name, tagger, upload_assets)
    else:
        create_release(repo, repo_name, "master", tag_name, tagger, upload_assets)