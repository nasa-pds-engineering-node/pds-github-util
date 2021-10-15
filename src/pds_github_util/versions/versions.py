import os
import logging
from configparser import ConfigParser
import github3

from pds_github_util.corral.cattle_head import is_dev_version, get_max_tag

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def grab_latest_versions(token, dev=False):

    config = ConfigParser()
    config.read(os.path.join(os.getcwd(), ".gitmodules"))

    latest_versions = {}

    for section in config.sections():
        submodule_name = section.split(" ")[1].strip('"')
        github_path = config.get(section, "url").strip("/")
        org = github_path.split("/")[-2]
        repo_name =  github_path.split("/")[-1]  # use submodule_name would make no difference but I feel like I better trust the value in the url
        gh = github3.login(token=token)
        repo = gh.repository(org, repo_name)
        latest_tag = None
        for tag in repo.tags():
            if is_dev_version(tag.name) and dev: # if we have a dev version and we look for dev version
                latest_tag = get_max_tag(tag.name, latest_tag) if latest_tag else tag.name
            elif not (is_dev_version(tag.name) or dev): # if we don't have a dev version and we look for stable version
                latest_tag = get_max_tag(tag.name, latest_tag) if latest_tag else tag.name
        if latest_tag:
            latest_versions[repo_name] = latest_tag.__str__()

    return latest_versions

