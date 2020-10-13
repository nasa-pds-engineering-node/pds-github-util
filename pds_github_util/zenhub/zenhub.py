"""ZenhubWrapper."""

import github3
import logging
import time
import requests

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ZENHUB_URL = 'https://api.zenhub.com{}?access_token={}'

# GET /p1/repositories/:repo_id/reports/releases
RELEASES_API = '/p1/repositories/{}/reports/releases'

# GET /p1/repositories/:repo_id/issues/:issue_number
ISSUES_API = '/p1/repositories/{}/issues/{}'

# GET /p1/reports/release/:release_id/issues
RELEASE_ISSUES_API = '/p1/reports/release/{}/issues'

# GET /p1/repositories/:repo_id/epics
EPICS_API = '/p1/repositories/{}/epics'

# GET /p1/repositories/:repo_id/epics/:epic_id
EPICS_DATA_API = '/p1/repositories/{}/epics/{}'


class Zenhub():
    """Wrapper for Zenhub API.

    https://github.com/ZenHubIO/API
    """

    def __init__(self, token):
        """TBD."""
        self._token = token
        # self._ = issue_sys['api'] + '/' + git_repo_id + ISSUES_SUFFIX + "/" + str(git_number)

    def query(self, rest_query):
        """Simple requests wrapper for Zenhu API REST queries."""
        url = ZENHUB_URL.format(rest_query, self._token)
        zen_issue_data = requests.get(url)
        while zen_issue_data.status_code == 403 and zen_issue_data.text == u'{"message":"API Rate limit reached."}':
            logger.warn("waiting for zenhub api reset")
            time.sleep(60.5)
            logger.warn("resuming")
            zen_issue_data = requests.get(url)

        return zen_issue_data.json()

    def issue(self, repo_id, issue_number):
        """Get Zenhub issue object."""
        return self.query(ISSUES_API.format(repo_id, issue_number))

    def get_issues_by_release(self, repo_id, title):
        """Get issue by release title.

        GET /p1/repositories/:repo_id/reports/releases
        """
        for release in self.query(RELEASES_API.format(repo_id)):
            if release['title'].lower().strip() == title.lower().strip():
                return self.query(RELEASE_ISSUES_API.format(release['release_id']))

    def get_epics(self, repo):
        """Get epics by repo.

        Return an object that contains epics mapped to child issues
        """
        epics = {}
        epics['epics'] = []
        epics['children'] = []
        epic_issues = self.query(EPICS_API.format(repo.id))['epic_issues']

        for epic_issue in epic_issues:
            epics['epics'].append(epic_issue['issue_number'])

            epic_data = self.query(EPICS_DATA_API.format(repo.id, epic_issue['issue_number']))

            for issue in epic_data['issues']:
                epics['children'].append(issue['issue_number'])

        return epics

    def get_epic_children(self, gh, org, repo_id, epic_id):
        """Get child issues of epic.

        returns list of epic child issues
        """
        epic_data = self.query(EPICS_DATA_API.format(repo_id, epic_id))

        epic_children = []
        for child in epic_data['issues']:
            # get repo name
            child_repo = gh.repository_with_id(child['repo_id'])
            epic_children.append({
                'repo': child_repo,
                'issue': gh.issue(org.login, child_repo.name, child['issue_number'])
            })

        return epic_children

