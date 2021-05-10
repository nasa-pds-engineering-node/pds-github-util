from pds_github_util.utils import GithubConnection, RstClothReferenceable

import logging
import os
import sys

from .utils import get_issue_type, get_issue_priority, ignore_issue, get_issues_groupby_type

class RstRddReport:

    ISSUE_TYPES = ['bug', 'enhancement', 'requirement', 'theme']
    IGNORED_LABELS = {'wontfix', 'duplicate', 'invalid', 'I&T', 'untestable'}
    IGNORED_REPOS = {'PDS-Software-Issues-Repo', 'pds-template-repo-python', 'pdsen-corral', 'pdsen-operations', 'roundup-action', 'github-actions-base'}

    def __init__(self,
                 org,
                 title='Release Description Document (build 11.1), software changes',
                 start_time=None,
                 token=None):

        # Quiet github3 logging
        self._logger = logging.getLogger('github3')
        self._logger.setLevel(level=logging.WARNING)

        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)

        self._org = org
        self._gh = GithubConnection.getConnection(token=token)
        self._start_time = start_time
        self._rst_doc = RstClothReferenceable()
        self._rst_doc.title(title)

    def available_repos(self):
        for _repo in self._gh.repositories_by(self._org):
            if _repo.name not in RstRddReport.IGNORED_REPOS:
                yield _repo

    def add_repo(self, repo):
        issues_map = self._get_issues_groupby_type(repo, state='closed', start_time=self._start_time)
        issue_count = sum([len(issues) for _, issues in issues_map.items()])
        if issue_count > 0:
            self._write_repo_section(repo.name, issues_map)

    def _get_issues_groupby_type(self, repo, state='closed', start_time=None):
        issues = {}
        for t in RstRddReport.ISSUE_TYPES:
            self._logger.info(f'++++++++{t}')
            issues[t] = []
            for issue in repo.issues(state=state, labels=t, direction='asc', since=start_time):
                if not ignore_issue(issue.labels(), ignore_labels=RstRddReport.IGNORED_LABELS):
                    issues[t].append(issue)

        return issues

    def _write_repo_section(self, repo, issues_map):
        self._rst_doc.h2(repo)

        for issue_type, issues in issues_map.items():
            if issues:
                self._add_rst_sub_section(repo, issue_type, issues)

    def _add_rst_sub_section(self, repo, type, issues):
        self._rst_doc.h3(type)

        columns = ["Issue", "Priority / Bug Severity"]

        data = []
        for issue in issues:
            self._rst_doc.hyperlink(f'{repo}_{issue.number}', issue.html_url)
            data.append([f'{repo}_{issue.number}_ {issue.title}'.replace('|', ''), get_issue_priority(issue)])

        self._rst_doc.table(
            columns,
            data=data)

    def write(self, filename):
        self._logger.info('Create file %s', filename)
        self._rst_doc.write(filename)