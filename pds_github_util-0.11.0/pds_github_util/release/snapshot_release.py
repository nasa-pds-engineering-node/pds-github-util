import os
import logging
import github3
import argparse


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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


def snapshot_release_publication(suffix, get_version, upload_assets):
    """
    Script made to work in the context of a github action.
    """
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    args = parser.parse_args()

    # read organization and repository name
    repo_full_name = os.environ.get('GITHUB_REPOSITORY')
    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    tag_name = get_version()
    if tag_name.endswith(suffix):
        tagger = {"name": "GitHub Action",
                  "email": "action@github.com"}

        gh = github3.login(token=args.token)
        repo = gh.repository(org, repo_name)

        delete_snapshot_releases(repo, suffix)
        create_snapshot_release(repo, repo_name, "master", tag_name, tagger, upload_assets)