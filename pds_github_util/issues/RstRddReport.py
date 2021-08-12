from pds_github_util.utils import GithubConnection, RstClothReferenceable
from datetime import datetime

import logging
from datetime import datetime

from github3.issues.issue import ShortIssue

from pds_github_util.issues.utils import get_issue_priority, ignore_issue


class PDSIssue(ShortIssue):

    def get_rationale(self):
        splitted_body = self.body.split('Rationale:')
        if len(splitted_body) == 2:
            return splitted_body[1]\
                .replace('\n', ' ')\
                .replace('\r', ' ')\
                .replace('*', '')\
                .strip()
        else:
            return None


from pds_github_util.issues.utils import get_issue_priority, ignore_issue

class RddReport:

    ISSUE_TYPES = ['bug', 'enhancement', 'requirement', 'theme']
    IGNORED_LABELS = {'wontfix', 'duplicate', 'invalid', 'I&T', 'untestable'}
    IGNORED_REPOS = {'PDS-Software-Issues-Repo', 'pds-template-repo-python', 'pdsen-corral', 'pdsen-operations',
                     'roundup-action', 'github-actions-base'}
    REPO_INFO = '*{}*\n\n' \
                '.. list-table:: \n' \
                '   :widths: 15 15 15 15 15 15\n\n' \
                '   * - `User Guide <{}>`_\n' \
                '     - `Github Repo <{}>`_\n' \
                '     - `Issue Tracking <{}/issues>`_ \n' \
                '     - `Backlog <{}/issues?q=is%3Aopen+is%3Aissue+label%3Abacklog>`_ \n' \
                '     - `Stable Release <{}/releases/latest>`_ \n' \
                '     - `Dev Release <{}/releases>`_ \n\n'
    SWG_REPO_NAME = 'pds-swg'


    def __init__(self,
                 org,
                 title='Release Description Document (build 11.1)',
                 start_time=None,
                 end_time=None,
                 build=None,
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
        self._build = build
        self._rst_doc = RstClothReferenceable()
        self._rst_doc.title(title)

    def available_repos(self):
        for _repo in self._gh.repositories_by(self._org):
            if _repo.name not in RstRddReport.IGNORED_REPOS:
                yield _repo

    def add_repo(self, repo):
        issues_map = self._get_issues_groupby_type(repo, state='closed')
        issue_count = sum([len(issues) for _, issues in issues_map.items()])
        if issue_count > 0:
            self._write_repo_change_section(repo, issues_map)

    def _get_issues_groupby_type(self, repo, state='closed'):
        issues = {}
        for t in RstRddReport.ISSUE_TYPES:
            issues[t] = []

            if self._start_time:
                self._logger.info("get %s issues from start time %s on ", t,  self._start_time)
                type_issues = repo.issues(state=state, labels=t, direction='asc', start=self._start_time)
            else:
                labels = [t, self._build]
                self._logger.info("get %s issues for build %s", t, self._build)
                type_issues = repo.issues(state=state, labels=','.join(labels), direction='asc')

            for issue in type_issues:
                if not ignore_issue(issue.labels(), ignore_labels=RstRddReport.IGNORED_LABELS) \
                   and (self._end_time is None or issue.created_at < datetime.fromisoformat(self._end_time)):
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
        self.bugs_severity = {}

        self.high_and_critical_open_bugs = ""

        self.epic_closed_for_the_build = {}

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

        print('Closed EPICS')
        print(self.epic_closed_for_the_build)


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


                if issue.state == 'open' and severity in {'s.critical', 's.high'}:
                    self._logger.info("%s#%i %s %s %s", repo, issue.number, issue.title, severity, issue.state)
                    self.high_and_critical_open_bugs += "%s#%i %s %s\n" % (repo, issue.number, issue.title, severity)


                # get count
                if issue.state == 'closed':
                    self.issues_type_counts['bug'] += 1
                else:
                    self._logger.info("this issues is still open %s#%i: %s", repo, issue.number, issue.title)


    def _get_epics_count(self, repo, build):

        epics = repo.issues(state='closed', labels=f'{build},Epic')
        n = 0

        for _ in epics:
            n += 1

        return n





    def _get_issue_type_count(self, repo):

        # count epics
        n_epics = self._get_epics_count(repo, 'B11.1')
        if n_epics>0:
            self.epic_closed_for_the_build[repo.name] = n_epics

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
                 end_time=None,
                 build=None,
                 token=None):

        super().__init__(org,
                         title=title,
                         start_time=start_time,
                         end_time=end_time,
                         build=build,
                         token=token)

        self._rst_doc = RstClothReferenceable()
        self._rst_doc.title(title)


    def _write_repo_section(self, repo, issues_map):
        self._rst_doc.h2(repo)

    def _get_change_requests(self):
        self._logger.info(
            "Getting change requests from %s/%s for build %s",
            self._org,
            RstRddReport.SWG_REPO_NAME,
            self._build
        )
        swg_repo = self._gh.repository(self._org, RstRddReport.SWG_REPO_NAME)

        change_requests = swg_repo.issues(state='closed', labels=','.join(['change-request', self._build]))

        columns = ["Issue", "Title", "Rationale"]
        data = []
        for cr in change_requests:
            self._rst_doc.hyperlink(f'{RstRddReport.SWG_REPO_NAME}_{cr.number}', cr.html_url)
            cr.__class__ = PDSIssue  # python cast
            data.append([f'{RstRddReport.SWG_REPO_NAME}_{cr.number}_ {cr.title}'.replace('|', ''), cr.title, cr.get_rationale()])

        self._rst_doc.table(
            columns,
            data=data)

    def _add_repo_description(self, repo):
        repo_info = RstRddReport.REPO_INFO.format(
                                     repo.description,
                                     repo.homepage or repo.html_url + '#readme',
                                     repo.html_url,
                                     repo.html_url,
                                     repo.html_url,
                                     repo.html_url,
                                     repo.html_url)
        self._rst_doc._add(repo_info)

    def _write_repo_change_section(self, repo, issues_map):
        self._rst_doc.h2(repo.name)

        self._add_repo_description(repo)

        for issue_type, issues in issues_map.items():
            if issues:
                self._add_rst_repo_change_sub_section(repo, issue_type, issues)

    def _add_rst_repo_change_sub_section(self, repo, type, issues):
        self._rst_doc.h3(type)

        columns = ["Issue", "Priority / Bug Severity"]

        data = []
        for issue in issues:
            self._rst_doc.hyperlink(f'{repo.name}#{issue.number}', issue.html_url)
            data.append([f'`{repo.name}#{issue.number}`_ {issue.title}'.replace('|', ''), get_issue_priority(issue)])

        self._rst_doc.table(
            columns,
            data=data)

    def _add_software_changes(self, repos):
        self._logger.info("Add software changes")
        self._rst_doc.h1('Software changes')
        for _repo in self.available_repos():
            if not repos or _repo.name in repos:
                self.add_repo(_repo)

    def _add_liens(self):
        self._logger.info("Add liens")
        self._rst_doc.h1('Liens')
        self._get_change_requests()

    def _add_software_catalogue(self):
        self._logger.info("Add software catalog")
        self._rst_doc.h1('Engineering Node Software Catalog')
        self._rst_doc.content(
            f'The Engineering Node Software resources are listed in the `software release summary ({self._build})`_'
        )
        self._rst_doc.newline()
        self._rst_doc.hyperlink(
            f'software release summary ({self._build})',
            f'https://nasa-pds.github.io/releases/{self._build}/index.html'
        )


    def _add_install_and_operation(self):
        self._logger.info("Add installation and operations")
        self._rst_doc.h1('Installation and operation')
        self._rst_doc.content(
            'PDS Engineering node software are meant to be deployed in 3 contexts: standalone, discipline nodes or engineering node')

        self._rst_doc.content('For the installation and operation manual see the `user''s manuals` in the software summary sections below:' )

        self._add_li('`PDS Standalone`_')
        self._add_li('`PDS Discipline Nodes`_')
        self._add_li('`PDS Engineering Node only`_')

        self._rst_doc.hyperlink(
            'PDS Standalone',
            'https://nasa-pds.github.io/releases/11.1/index.html#standalone-tools-and-libraries'
        )

        self._rst_doc.hyperlink(
            'PDS Discipline Nodes',
            'https://nasa-pds.github.io/releases/11.1/index.html#discipline-node-services'
        )

        self._rst_doc.hyperlink(
            'PDS Engineering Node only',
            'https://nasa-pds.github.io/releases/11.1/index.html#enineering-node-services'
        )

        self._rst_doc.newline()


    def _add_li(self, s):
        self._rst_doc.newline()
        self._rst_doc.li(s, wrap=False)

    def _add_reference_docs(self):
        self._logger.info("Add reference docs")
        self._rst_doc.h1('Reference documents')
        self._rst_doc.content(
            'This section details the controlling and applicable documents referenced for this release. The controlling documents are as follows:')

        self._add_li('PDS Level 1, 2 and 3 Requirements, April 20, 2017.')
        self._add_li('PDS4 Project Plan, July 17, 2013.')
        self._add_li('PDS4 System Architecture Specification, Version 1.3, September 1, 2013.')
        self._add_li('PDS4 Operations Concept, Version 1.0, September 1, 2013.')
        self._add_li(
            'PDS Harvest Tool Software Requirements and Design Document (SRD/SDD), Version 1.2, September 1, 2013.')
        self._add_li(
            'PDS Preparation Tools Software Requirements and Design Document (SRD/SDD), Version 0.3, September 1, 2013.')
        self._add_li(
            'PDS Registry Service Software Requirements and Design Document (SRD/SDD), Version 1.1, September 1, 2013.')
        self._add_li(
            'PDS Report Service Software Requirements and Design Document (SRD/SDD), Version 1.1, September 1, 2013.')
        self._add_li(
            'PDS Search Service Software Requirements and Design Document (SRD/SDD), Version 1.0, September 1, 2013.')
        self._add_li('PDS Search Scenarios, Version 1.0, September 1, 2013.')
        self._add_li('PDS Search Protocol, Version 1.2, March 21, 2014.')
        self._add_li('PDAP Search Protocol, Version 1.0, March 21, 2014.')
        self._add_li(
            'PDS Security Service Software Requirements and Design Document (SRD/SDD), Version 1.1, September 1, 2013.')
        self._add_li('`PDS Deep Archive Sotware Requirements and Design Document (SRD/SDD)`_')
        self._add_li('`PDS DOI Service Requirements and Design Document (SRD/SDD)`_')

        self._rst_doc.newline()

        self._rst_doc.hyperlink(
            'PDS Deep Archive Sotware Requirements and Design Document (SRD/SDD)',
            'https://github.com/NASA-PDS/pds-deep-archive/blob/master/docs/pds4_nssdca_delivery_design_20191219.docx'
        )
        self._rst_doc.hyperlink(
            'PDS DOI Service Requirements and Design Document (SRD/SDD)',
            'https://github.com/NASA-PDS/pds-doi-service/blob/master/docs/design/pds-doi-service-srd.md'
        )


    def _add_introduction(self):
        self._logger.info("Add introduction")
        self._rst_doc.content('This release of the PDS4 System is intended as an operational release of the system components to date.')
        self._rst_doc.content(f'The original plan for this release can be found here: `plan {self._build}`_')
        self._rst_doc.newline()
        self._rst_doc.content('The following sections can be found in this document:')
        self._rst_doc.hyperlink(f'plan {self._build}', f'https://nasa-pds.github.io/releases/{self._build[1:]}/plan.html')  # remove B prefix from the build code
        self._rst_doc.newline()
        self._rst_doc.directive('toctree', fields=[('glob', ''), ('maxdepth', 2)], content='rdd.rst')
        self._rst_doc.newline()

    def _add_standard_and_information_model_changes(self):
        self._logger.info("Add standard updates")
        IM_REPO = "pds4-information-model"

        self._rst_doc.h1('PDS4 Standards and Information Model Changes')
        self._rst_doc.content(
            'This section details the changes to the PDS4 Standards and Information Model approved by the PDS4 Change '
            'Control Board and implemented by the PDS within the latest build period.'
        )

        columns = ["Ref", "Title"]

        data = []

        repository = self._gh.repository(self._org, IM_REPO)
        for issue in repository.issues(state='closed', labels='pending-scr', direction='asc', since=self._start_time):
            self._rst_doc.hyperlink(f'{IM_REPO}#{issue.number}', issue.html_url)
            data.append([f'`{IM_REPO}#{issue.number}`_'.replace('|', ''), issue.title])

        if data:
            self._rst_doc.table(
                columns,
                data=data)
        else:
            self._rst_doc.content("no PDS4 standard updates")

    def create(self, repos, filename):
        self._logger.info("Create RDD rst")
        self._add_introduction()
        self._add_standard_and_information_model_changes()
        self._add_software_changes(repos)
        self._add_liens()
        self._add_software_catalogue()
        self._add_install_and_operation()
        self._add_reference_docs()
        self.write(filename)

    def add_repo(self, repo):
        issues_map = self._get_issues_groupby_type(
            repo,
            state='closed'
        )
        issue_count = sum([len(issues) for _, issues in issues_map.items()])

        if issue_count > 0:
            self._write_repo_section(repo.name, issues_map)

    def write(self, filename):
        self._logger.info('Create file %s', filename)
        self._rst_doc.write(filename)