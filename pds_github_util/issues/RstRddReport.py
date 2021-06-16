from pds_github_util.utils import GithubConnection, RstClothReferenceable
from datetime import datetime

import logging


from pds_github_util.issues.utils import get_issue_priority, ignore_issue

class RddReport:

    ISSUE_TYPES = ['bug', 'enhancement', 'requirement', 'theme']
    IGNORED_LABELS = {'wontfix', 'duplicate', 'invalid', 'I&T', 'untestable'}
    IGNORED_REPOS = {'PDS-Software-Issues-Repo', 'pds-template-repo-python', 'pdsen-corral', 'pdsen-operations', 'roundup-action', 'github-actions-base'}

    def __init__(self,
                 org,
                 start_time=None,
                 end_time=None,
                 token=None):

        # Quiet github3 logging
        self._logger = logging.getLogger('github3')
        self._logger.setLevel(level=logging.WARNING)

        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)

        self._org = org
        self._gh = GithubConnection.getConnection(token=token)
        self._start_time = start_time
        self._end_time = end_time

    def available_repos(self):
        for _repo in self._gh.repositories_by(self._org):
            if _repo.name not in RstRddReport.IGNORED_REPOS:
                yield _repo

    def _get_issues_groupby_type(self, repo, state='closed'):
        issues = {}
        for t in RstRddReport.ISSUE_TYPES:
            self._logger.info(f'++++++++{t}')
            issues[t] = []
            for issue in repo.issues(state=state,
                                     labels=t,
                                     direction='asc',
                                     since=self._start_time,
                                     until=self._end_time):
                if not ignore_issue(issue.labels(), ignore_labels=RstRddReport.IGNORED_LABELS):
                    issues[t].append(issue)

        return issues





class MetricsRddReport(RddReport):

    def __init__(self,
                 org,
                 start_time=None,
                 end_time=None,
                 token=None):
        super().__init__(org, start_time, end_time, token)
        self.issues_type_counts = {}
        for t in self.ISSUE_TYPES:
            self.issues_type_counts[t] = 0

        self.issues_type_five_biggest = {}
        for t in self.ISSUE_TYPES:
            self.issues_type_five_biggest[t] = []

        self.bugs_open_closed = {}
        self.bugs_severity = {};

        self.high_and_critical_open_bugs = ""


    def create(self, repos):
        for _repo in self.available_repos():
            if not repos or _repo.name in repos:
                self.add_repo(_repo)

        print('Issues types')
        print(self.issues_type_counts)

        print('Bug states')
        print(self.bugs_open_closed)

        print('Bug severity')
        print(self.bugs_severity)

        print('Open high and critical bugs')
        print(self.high_and_critical_open_bugs)

    def _non_bug_metrics(self, type, repo):
        for issue in repo.issues(
                state='closed',
                labels=type,
                direction='asc',
                since=self._start_time
        ):
            if not ignore_issue(issue.labels(), ignore_labels=RstRddReport.IGNORED_LABELS) \
                    and issue.created_at <  datetime.fromisoformat(self._end_time):
                self.issues_type_counts[type] += 1

    def _bug_metrics(self, repo):
        for issue in repo.issues(
                state='all',
                labels='bug',
                direction='asc',
                since=self._start_time
        ):
            if not ignore_issue(issue.labels(), ignore_labels=RstRddReport.IGNORED_LABELS) \
                    and issue.created_at < datetime.fromisoformat(self._end_time):
                # get severity
                severity = 's.unknown'
                for label in issue.labels():
                    if label.name.startswith('s.'):
                        severity = label.name
                        break
                if severity in self.bugs_severity.keys():
                    self.bugs_severity[severity] += 1
                else:
                    self.bugs_severity[severity] = 1

                # get state
                if issue.state in self.bugs_open_closed.keys():
                    self.bugs_open_closed[issue.state] += 1
                else:
                    self.bugs_open_closed[issue.state] = 1

                self._logger.info("%s#%i %s %s %s", repo, issue.number, issue.title, severity, issue.state)
                if issue.state == 'open' and severity in {'s.critical', 's.high'}:
                    self.high_and_critical_open_bugs.append("%s#%i %s %s\n" % repo, issue.number, issue.title, severity)


                # get count
                if issue.state == 'closed':
                    self.issues_type_counts['bug'] += 1
                else:
                    self._logger.info("this issues is still open %s#%i: %s", repo, issue.number, issue.title)

    def _get_issue_type_count(self, repo):
        for t in RstRddReport.ISSUE_TYPES:
            if t == 'bug':
                self._bug_metrics(repo)
            else:
                self._non_bug_metrics(t, repo)

    def add_repo(self, repo):
        self._logger.info("add repo %s", repo)
        self._get_issue_type_count(repo)


class RstRddReport(RddReport):

    def __init__(self,
                 org,
                 title='Release Description Document (build 11.1), software changes',
                 start_time=None,
                 token=None):

        super().__init__(org,
                         start_time,
                         token)

        self._rst_doc = RstClothReferenceable()
        self._rst_doc.title(title)



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

    def add_repo(self, repo):
        issues_map = self._get_issues_groupby_type(
            repo,
            state='closed',
            start_time=self._start_time,
            end_time=self._end_time
        )
        issue_count = sum([len(issues) for _, issues in issues_map.items()])
        if issue_count > 0:
            self._write_repo_section(repo.name, issues_map)

    def create(self, repos, filename):
        for _repo in self.available_repos():
            if not repos or _repo.name in repos:
                self.add_repo(_repo)

        self.write('pdsen_issues.rst')

    def write(self, filename):
        self._logger.info('Create file %s', filename)
        self._rst_doc.write(filename)