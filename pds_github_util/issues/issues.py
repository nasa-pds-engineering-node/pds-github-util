"""Github issues wrapper."""

import github3
import mimetypes
import os
import subprocess
import sys
from . import util
from . import zenhub

DEFAULT_BUILD_DIR = '/tmp'

ASSET_MIME_TYPES = ['application/zip',
                    'application/x-tar',
                    'application/java-archive']

BuildJava = os.path.join(os.environ['CONMAN_HOME'], 'scripts', 'build-java.sh')

ReleaseOptions = {
    'M': 'major',
    'm': 'minor',
    'p': 'patch',
    # 'rc': 'candidate',
    's': 'skip'
}


class NotFoundException(Exception):
    pass


class GithubWrapper:
    def __init__(self, github_token, sys_name, github_url=, repos_subset=None):
        username, password = util.get_creds(issue_sys)

        self._gh = github3.GitHubEnterprise(issue_sys['url'], username, password)

        self._repos = []
        for org_name in issue_sys['orgs'].keys():
            for repo_name in issue_sys['orgs'][org_name]:
                if not repos_subset or repo_name in repos_subset:
                    self._repos.append(self._gh.repository(org_name, repo_name))

    def getLatestVersions(self):
        versions = {}
        for repo in self._repos:
            try:
                versions[repo.name] = repo.latest_release().tag_name
            except github3.exceptions.NotFoundError as e:
                # Skip if no release found
                None

        return versions

    # if any of the report things are designated, lets write out a report
    def getIssues(self, start_time, end_time, options):
        all_summaries = {}

        for repo in self._repos:
            summary = IssueSummary(repo)

            for issue in repo.issues(state='all', direction='asc'):
                # ignore pull requests for now
                if '/pull/' in issue.html_url:
                    continue

                create_time = issue.created_at.replace(tzinfo=None)

                if issue.state == 'closed' and start_time <= issue.closed_at.replace(tzinfo=None) <= end_time:
                    summary.addIssue(issue, *util.get_issue_type(issue))

                if issue.state == 'open' and create_time <= end_time:
                    summary.addIssue(issue, *util.get_issue_type(issue))

            all_summaries[repo] = summary

        return all_summaries

    def get_requirements(self):
        all_summaries = {}

        for repo in self._repos:
            summary = {}

            topic_assigned = None
            for issue in repo.issues(state='all', direction='asc', labels='requirement'):
                # ignore pull requests for now
                if '/pull/' in issue.html_url:
                    continue

                topic_assigned = False
                for label in issue.labels():
                    if label.name.startswith("requirement-topic"):
                        requirement_topic = label.name.split(':')[1]
                        if requirement_topic not in summary.keys():
                            summary[requirement_topic] = []
                        summary[requirement_topic].append(issue)
                        topic_assigned = True
                        continue

            if not topic_assigned:
                if "default" not in summary.keys():
                    summary["default"] = []
                summary["default"].append(issue)

            all_summaries[repo] = summary

        return all_summaries

    def getIssuesByRelease(self, release_title):
        # get a zenhub object
        # assumes all repos are in the release
        if not self._repos:
            return None

        zen = zenhub.ZenhubWrapper(self._zenhub_config)
        release_issues = zen.getIssuesByRelease(self._repos[0].id, release_title)

        if not release_issues:
            return {}

        # epics = {}
        repo_id_mapping = {}
        all_summaries = {}
        epics = {}
        for release_issue in release_issues:
            if release_issue['repo_id'] not in repo_id_mapping.keys():
                repo = self._gh.repository_with_id(release_issue['repo_id'])
                print(repo)
                repo_id_mapping[release_issue['repo_id']] = repo

                # Get all Epic Children so we ignore those in the report
                # epics[repo] = zen.getEpics(repo)

                summary = IssueSummary(repo)
            else:
                repo = repo_id_mapping[release_issue['repo_id']]
                # print(all_summaries.keys())
                summary = all_summaries[repo]

            # Get epics if we don't have them for this repo
            if repo.id not in epics:
                epics[repo.id] = zen.getEpics(repo)

            if release_issue['issue_number'] not in epics[repo.id]['children']:
                issue = repo.issue(release_issue['issue_number'])

                # print(repo.name + "#" + str(issue.number) + " " + issue.title)
                # if issue.number in epics[repo]['epics'] or issue.number not in epics[repo]['children']:
                # create_time = issue.created_at.replace(tzinfo=None)f

                summary.addIssue(issue, *util.get_issue_type(issue))

                # if issue.state == 'closed':
                #     # summary.addClosed(issue, epics[repo], *util.get_issue_type(issue))
                #     summary.addClosed(issue, *util.get_issue_type(issue))

                # if issue.state == 'open':
                #     # summary.addOpen(issue, epics[repo], *util.get_issue_type(issue))
                #     summary.addOpen(issue, *util.get_issue_type(issue))

            all_summaries[repo] = summary

        return all_summaries

        # for repo in self._repos:
        #     summary = IssueSummary(repo)

        #     for issue in repo.issues(state='all', direction='asc'):
        #         # ignore pull requests for now
        #         if '/pull/' in issue.html_url:
        #             continue

        #         create_time = issue.created_at.replace(tzinfo=None)

        #         if issue.state == 'closed' and start_time <= issue.closed_at.replace(tzinfo=None) <= end_time:
        #             summary.addClosed(issue, *util.get_issue_type(issue))

        #         if issue.state == 'open' and create_time <= end_time:
        #             summary.addOpen(issue, *util.get_issue_type(issue))

        #     all_summaries[repo] = summary

        # return all_summaries

    def create_sprint(self, sprint_title, due_date, description=None):
        if not due_date:
            parser.print_help()
            raise Exception("ERROR: Must specify due date when adding milestone")

        state = 'open'
        due_on = due_date.strftime(util.ISSUE_DATE_FORMAT)

        if not description:
            description = ''

        for repo in self._repos:
            try:
                repo.create_milestone(sprint_title, state=state, description=description, due_on=due_on)
                print(f"Created milestone {sprint_title} in {repo}")
            except github3.exceptions.UnprocessableEntity as e:
                # Exception from library is vague, let's just assume it
                # already exists and move on
                print(f"ERROR: Failed to create milestone {sprint_title} in {repo}.")
                print(f"Milestone already exists. Skipping...")

    def close_sprint(self, sprint_title, force=False):
        # Get the milestone info ready
        state = 'closed'

        print(f'Closing milestone "{sprint_title}"')
        for repo in self._repos:
            try:
                print(repo)
                m = self.get_milestone(repo, sprint_title)
                if m.open_issues_count != 0:
                    raise Exception(f"{m.open_issues_count} open issues exist.")

                m.update(state='closed')
            except NotFoundException as e:
                None
            except Exception as e:
                print(f"ERROR: Failed to close milestone {sprint_title} in {repo}")
                print(str(e))
                print(f"Skipping...")

    def delete_sprint(self, sprint_title):
        print(f"Deleting milestone {sprint_title}")
        for repo in self._repos:
            try:
                print(repo)
                m = self.get_milestone(repo, sprint_title)
                m.delete()
            except NotFoundException as e:
                None
            except Exception as e:
                print(f"ERROR: Failed to delete milestone {sprint_title} in {repo}")
                print(str(e))
                print(f"Skipping...")

    def get_milestone(self, repo, sprint_title):
        milestone = None
        for m in repo.milestones():
            if m.title.lower() == sprint_title.lower():
                milestone = m

        if not milestone:
            raise NotFoundException('Milestone not found.')

        return milestone

    def create_label(self, label_name, label_color):
        print('Creating label "%s" (color: "%s")' % (label_name, label_color))
        for repo in self._repos:
            try:
                repo.create_label(label_name, label_color)
                print('%s: Creation SUCCESS' % repo)
            except github3.exceptions.UnprocessableEntity:
                try:
                    label = repo.label(label_name)
                    label.update(label_name, label_color)
                    print('%s: Update SUCCESS' % repo)
                except Exception as e:
                    print('ERROR: Create/update failed.')
                    print(e)
                    sys.exit(1)

    def release(self, start_time, end_time, options):
        for repo in self._repos:
            print('*************************************************')
            print('+++ {} +++'.format(repo))
            print('\n---\n- Closed Issues / PRs:')

            prs = []
            bugs = []
            enhance = []
            rqmt = []

            if start_time and end_time:
                for issue in repo.issues(state='closed'):
                    if util.valid_issue(issue) and start_time <= issue.closed_at.replace(tzinfo=None) <= end_time:
                        title = issue.title
                        if '/pull/' in issue.html_url:
                            title = 'PR: ' + title
                        else:
                            title = 'Issue: ' + title
                        
                        print(title)
                        print('    * Closed: ' + str(issue.closed_at))

            print('\n---\n- Continuing onto release:')
            user_input = input('Major, minor, patch, or skip? [M/m/p/s]  ')
            if user_input != 's':
                if user_input in ['M', 'm', 'p']:
                    # get the last version for the repo
                    try:
                        last_version = repo.latest_release().tag_name.lstrip('v')
                    except github3.exceptions.NotFoundError as e:
                        print("ERROR: No released versions exist. Tool does not currently handle this use case.")
                        print("       Perform a release manually in Github to enable autoamted releases.")
                        # cmd = 'mvn org.apache.maven.plugins:maven-help-plugin:3.1.0:evaluate -Dexpression=project.version -q -DforceStdout'
                        # p = subprocess.Popen([cmd, stdout=subprocess.PIPE)
                        # version = p.stdout.readline()

                    next_version = util.get_next_version(last_version, ReleaseOptions[user_input])
                    next_dev_version = util.get_next_java_dev_version(next_version)

                    p = None
                    try:
                        p = subprocess.Popen([BuildJava, str(repo), repo.ssh_url, next_version, next_dev_version], stdout=subprocess.PIPE)
                        while True:
                            output = p.stdout.readline()
                            if p.poll() == 0:
                                break

                            if p.poll() == 1:
                                print('ERROR: {} did not complete as expected. check output.'.format(BuildJava))
                                sys.exit(1)

                            if output:
                                out = output.strip()
                                print(out)

                            rc = p.poll()
                    except KeyboardInterrupt:
                        if p:
                            p.terminate()

                    # Should probably have a better way of checking this, but it works
                    if 'success' in str(out).lower():
                        tagged_version = next_version
                        release_name = str(repo).split('/')[1] + ' ' + tagged_version

                        print('\n---\n- Creating formal Github Release {}'.format(tagged_version))
                        release = repo.create_release(tagged_version, target_commitish=None,
                                                      name=release_name, body=None,
                                                      draft=False, prerelease=False)
                        if release:
                            print('SUCCESS')
                        else:
                            print('ERROR: Github release creation failed. Check output.')
                            sys.exit(1)

                        print('\n---\n- Uploading Assets')
                        assets = self.assets(repo)
                        for a in assets.keys():
                            with open(a, 'rb') as file:
                                print('  * {}'.format(os.path.basename(a)))
                                release.upload_asset(assets[a], os.path.basename(a), file)
                    else:
                        print('ERROR: {} did not complete as expected. check output.'.format(BuildJava))
                        sys.exit(1)

                if user_input in ['rc']:
                    print('NOT YET SUPPORTED')
                    sys.exit(1)

            print('\n\n')

    def assets(self, repo, build_dir=None):
        ''' Get all repo assets that were built

        Assumes all assets are in build_dir/repo/target
        '''
        if not build_dir:
            build_dir = DEFAULT_BUILD_DIR

        repo_name = str(repo).split('/')[1]

        # Go to build_dir/repo_name/target and get list of files
        assets = {}
        path = os.path.join(build_dir, repo_name)

        for dirpath, dirnames, filenames in os.walk(path):
            for d in dirnames:
                if d == 'target':
                    target_path = os.path.join(dirpath, d)

                    for f in os.listdir(target_path):
                        file = os.path.join(target_path, f)
                        if os.path.isfile(file):
                            mimetype = mimetypes.MimeTypes().guess_type(file)[0]
                            if mimetype in ASSET_MIME_TYPES:
                                assets[file] = mimetype

        return assets

