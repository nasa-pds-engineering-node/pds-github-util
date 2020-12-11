import logging
import requests
from bs4 import BeautifulSoup
import github3
from packaging import version
from datetime import datetime
logging.basicConfig(level=logging.INFO)

import http.client
http.client.HTTPConnection.debuglevel = 1

logger = logging.getLogger(__name__)


requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

VOID_URL = 'https://en.wikipedia.org/wiki/Void_(astronomy)'
SHORT_DESCRIPTION_LEN = 50

def is_dev_version(tag_name):
    return tag_name.endswith("-dev") or tag_name.endswith("-SNAPSHOT")


def get_max_tag(tag, other_tag):
    vers = version.parse(tag.name)
    other_vers = version.parse(other_tag.name)
    return tag if (vers > other_vers) else other_tag



class CattleHead():

    _icon_dict = {
        'manual': 'https://nasa-pds.github.io/pdsen-corral/images/manual.png',
        'changelog': 'https://nasa-pds.github.io/pdsen-corral/images/changelog.png',
        'requirements': 'https://nasa-pds.github.io/pdsen-corral/images/requirements.png',
        'download': 'https://nasa-pds.github.io/pdsen-corral/images/download.png',
        'license' : 'https://nasa-pds.github.io/pdsen-corral/images/license.png',
        'feedback': 'https://nasa-pds.github.io/pdsen-corral/images/feedback.png'
    }

    def __init__(self, name, github_path, version=None, dev=False, token=None):
        logger.info(f'create cattleHead {name}, {github_path}')
        self._name = name
        self._github_path = github_path
        self._org = self._github_path.split("/")[-2]
        self._repo_name = self._github_path.split("/")[-1]
        self._token = token
        gh = github3.login(token=self._token)
        self._repo = gh.repository(self._org, self._repo_name)
        self._description = self._repo.description
        self._changelog_url = f'https://github.com/{self._org}/{self._repo_name}/blob/master/CHANGELOG.md'
        self._changelog_signets = self._get_changelog_signet()
        self._dev = dev

        self._version = self._get_latest_patch(minor=version)
        self._version_name = self._version.name if self._version else None
        if self._version:
            update_date_iso = self._repo.commit(self._version.commit.sha).as_dict()['commit']['author']['date']
            self._update = datetime.fromisoformat(update_date_iso.replace('Z', '+00:00'))
        else:
            self._update = None

        self.rst_doc = None

    def set_rst(self, d):
        self.rst_doc = d

    def set_icon_replacement_rst(self, function, link_func):
        self.rst_doc.deffered_directive('image', arg=self._icon_dict[function],
                               fields=[('target', link_func)],
                               reference=f'{self._repo}_{function}')

    def get_published_date(self):
        return self._update

    def _get_latest_patch(self, minor=None):

        latest_tag = None
        for tag in self._repo.tags():
            if is_dev_version(tag.name) and self._dev:  # if we have a dev version and we look for dev version
                latest_tag = get_max_tag(tag, latest_tag) if latest_tag else tag
            elif not (is_dev_version(tag.name) or self._dev):  # if we don't have a dev version and we look for stable version
                if minor is None \
                        or (minor and (tag.name.startswith(minor) or tag.name.startswith(f'v{minor}'))):
                    latest_tag = get_max_tag(tag, latest_tag) if latest_tag else tag

        return latest_tag if latest_tag else None

    @staticmethod
    def _reachable(url):
        logger.info(f'try url {url}')
        time_out = 5;

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-encoding': 'gzip,deflate,br',
            'Accept-language': 'en-US,en',
            'Content-Type': 'text/html; charset=utf-8',
            'Connection': 'close',
            'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36'
        }

        try:
            response = requests.head(url, timeout=time_out, headers=headers)
            return response.status_code != 404
        except requests.exceptions as e:
            logger.info(f'url {url} not reachable in {time_out}s')
            return False


    def _get_cell(self, function, format='md'):
        link_func = eval(f'self._get_{function}_link()')
        if format == 'md':
            return f'[![{function}]({self._icon_dict[function]})]({link_func} "{function}")' if link_func else ' '
        elif format == 'rst':
            self.set_icon_replacement_rst(function, link_func)
            return f'|{self._repo}_{function}|' if link_func else ' '
        else:
            logger.error(f'Unsupported format {format} for tool summary table cell (_get_cell)')
            return None

    def _get_download_link(self):
        return f'{self._github_path}/releases/tag/{self._version}'

    def _get_manual_link(self):
        if self._version_name:
            url = f'https://{self._org}.github.io/{self._repo_name}/{self._version_name}'
            if self._reachable(url):
                return url
            elif self._version_name[0] == 'v':
                url = f'https://{self._org}.github.io/{self._repo_name}/{self._version_name[1:]}'
                if self._reachable(url):
                    return url

        return f'https://{self._org}.github.io/{self._repo_name}'


    def _get_changelog_link(self):
        if self._version_name:
            if self._version_name in self._changelog_signets:
                return self._changelog_signets[self._version_name]
            else:
                return None
        else:
            return "https://www.gnupg.org/gph/en/manual/r1943.html"

    def _get_requirements_link(self):
        url = f'https://github.com/{self._org}/{self._repo_name}/blob/master/docs/requirements/{self._version_name}/REQUIREMENTS.md'

        if self._version_name and self._reachable(url):
            return url
        else:
            return None

    def _get_license_link(self):
        return f'https://raw.githubusercontent.com/NASA-PDS/{self._repo_name}/master/LICENSE.txt'

    def _get_feedback_link(self):
        return f'{self._github_path}/issues/new/choose'

    def get_table_row(self, format='md'):
        icon_cells = [self._get_cell(k, format) for k in self._icon_dict.keys()]

        description = self._description[:SHORT_DESCRIPTION_LEN]
        if len(self._description)>SHORT_DESCRIPTION_LEN:
            if format=='md':
                description += f" [...]({self._github_path} 'more')"
            elif format=='rst':
                description += f"`...<{self._github_path}/>`_"
            else:
                logger.error(f'format {format} not supported to write long description link (get_table_row)')

        return [self._name,
                self._version_name if self._version_name else "None",
                self._update.strftime('%Y-%m-%d') if self._update else "N/A",
                description,
                *icon_cells
        ]

    def _get_changelog_signet(self):
        headers = requests.utils.default_headers()
        changelog = requests.get(self._changelog_url, headers)
        soup = BeautifulSoup(changelog.content, 'html.parser')
        changelog_signets = {}
        for h2 in soup.find_all('h2'):
            version , signet = self._extract_signet_from_h2(h2)
            if version:
                changelog_signets[version] = signet

        return changelog_signets

    def _extract_signet_from_h2(self, h2_tag):
        a_tags = h2_tag.find_all("a")
        if len(a_tags) == 2:
            href_attr = a_tags[0].get('href')
            if href_attr:
                return a_tags[1].text, ''.join([self._changelog_url, href_attr])

        return None, None



