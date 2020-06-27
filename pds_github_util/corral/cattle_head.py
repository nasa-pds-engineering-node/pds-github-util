import logging
import requests
from bs4 import BeautifulSoup
import github3
from packaging import version

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VOID_URL = 'https://en.wikipedia.org/wiki/Void_(astronomy)'

def is_dev_version(tag_name):
    return tag_name.endswith("-dev") or tag_name.endswith("-SNAPSHOT")


def get_max_tag(tag_name, other_tag_name ):
    vers = version.parse(tag_name)
    other_vers = version.parse(other_tag_name)
    return tag_name if (vers > other_vers) else other_tag_name


class CattleHead():

    _icon_dict = {
        'download': 'https://nasa-pds.github.io/pdsen-corral/images/download.png',
        'manual': 'https://nasa-pds.github.io/pdsen-corral/images/manual.png',
        'changelog': 'https://nasa-pds.github.io/pdsen-corral/images/changelog.png',
        'requirements': 'https://nasa-pds.github.io/pdsen-corral/images/requirements.png',
        'license' : 'https://nasa-pds.github.io/pdsen-corral/images/license.png',
        'feedback': 'https://nasa-pds.github.io/pdsen-corral/images/feedback.png'
    }

    def __init__(self, name, github_path, description, version=None, dev=False, token=None):
        logger.info(f'create cattleHead {name}, {github_path}, {description}')
        self._name = name
        self._github_path = github_path
        self._org = self._github_path.split("/")[-2]
        self._repo_name = self._github_path.split("/")[-1]
        self._description = description
        self._changelog_url = f"http://nasa-pds.github.io/{self._repo_name}/pdsen-corral/CHANGELOG.html"
        self._changelog_signets = self._get_changelog_signet()
        self._dev = dev
        self._token = token
        self._version = self._get_latest_patch(minor=version)

    def _get_latest_patch(self, minor=None):
        gh = github3.login(token=self._token)
        repo = gh.repository(self._org, self._repo_name)
        latest_tag = None
        for tag in repo.tags():
            if is_dev_version(tag.name) and self._dev:  # if we have a dev version and we look for dev version
                latest_tag = get_max_tag(tag.name, latest_tag) if latest_tag else tag.name
            elif not (is_dev_version(tag.name) or self._dev):  # if we don't have a dev version and we look for stable version
                if minor is None \
                        or (minor and (tag.name.startswith(minor) or tag.name.startswith(f'v{minor}'))):
                    latest_tag = get_max_tag(tag.name, latest_tag) if latest_tag else tag.name

        return latest_tag.__str__() if latest_tag else None

    def _get_cell(self, function):
        link_func = eval(f'self._get_{function}_link()')
        return f'[![{function}]({self._icon_dict[function]})]({link_func} "{function}")'

    def _get_download_link(self):
        return f'https://github.com/NASA-PDS/{self._repo_name}/releases/tag/{self._version}'

    def _get_manual_link(self):
        return f'https://nasa-pds.github.io/{self._repo_name}'

    def _get_changelog_link(self):
        if self._version:
            if self._version in self._changelog_signets:
                return self._changelog_signets[self._version]
            else:
                return
        else:
            return "https://www.gnupg.org/gph/en/manual/r1943.html"

    def _get_requirements_link(self):
        url = f'https://nasa-pds.github.io/{self._repo_name}/pdsen-corral/{self._version}/REQUIREMENTS.html'
        logger.info(f'try url {url} for requirements')
        if self._version and requests.get(url).status_code != 404:
            return url
        else:
            return VOID_URL

    def _get_license_link(self):
        return f'https://raw.githubusercontent.com/NASA-PDS/{self._repo_name}/master/LICENSE.txt'

    def _get_feedback_link(self):
        return f'https://github.com/NASA-PDS/{self._repo_name}/issues/new/choose'

    def get_table_row(self):
        icon_cells = [self._get_cell(k) for k in self._icon_dict.keys()]
        return [self._name,
                self._version if self._version else "None",
                self._description,
                *icon_cells
        ]

    def _get_changelog_signet(self):
        headers = requests.utils.default_headers()
        changelog = requests.get(self._changelog_url, headers)
        soup = BeautifulSoup(changelog.content, 'html.parser')
        changelog_signets = {}
        for h2 in soup.find_all('h2'):
            changelog_signets[h2.find("a").text] = "#".join([self._changelog_url, h2.get('id')])

        return changelog_signets


