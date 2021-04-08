#!/usr/bin/env python
"""
Tool to generate simple markdown issue reports
"""
import argparse
import logging
import os
import sys

from github3 import login
from mdutils.mdutils import MdUtils

DEFAULT_GITHUB_ORG = 'NASA-PDS'

# Quiet github3 logging
logger = logging.getLogger('github3')
logger.setLevel(level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ISSUE_TYPES = ['bug', 'enhancement', 'requirement', 'theme']
TOP_PRIORITIES = ['p.must-have', 's.high', 's.critical']
IGNORE_LABELS = ['wontfix', 'duplicate', 'invalid']


def get_issue_type(issue):
    for label in issue.labels():
        if label.name in ISSUE_TYPES:
            return label.name


def get_issue_priority(short_issue):
    for label in short_issue.labels():
        if 'p.' in label.name or 's.' in label.name:
            return label.name

    return "unk"


def ignore_issue(labels):
    for label in labels:
        if label.name in IGNORE_LABELS:
            return True

    return False


def get_issues_groupby_type(repo, state, start_time, ignore_types=None):
    issues = {}
    for t in ISSUE_TYPES:
        print(f'++++++++{t}')
        if ignore_types and t in ignore_types:
            continue

        issues[t] = []
        for issue in repo.issues(state=state, labels=t, direction='asc', since=start_time):
            if ignore_issue(issue.labels):
                continue

            issues[t].append(issue)

    return issues


def convert_issues_to_planning_report(md_file, repo_name, issues_map):
    md_file.new_header(level=1, title=repo_name)

    for issue_type in issues_map:
        md_file.new_header(level=2, title=issue_type)

        table = ["Issue", "Priority / Bug Severity", "On Deck"]
        count = 1
        for short_issue in issues_map[issue_type]:
            issue = f'[{repo_name}#{short_issue.number}]({short_issue.html_url}) - {short_issue.title}'
            priority = get_issue_priority(short_issue)

            ondeck = ''
            if priority in TOP_PRIORITIES:
                ondeck = 'X'

            table.extend([issue, priority, ondeck])
            count += 1

        md_file.new_line()
        md_file.new_table(columns=3, rows=int(len(table)/3), text=table, text_align='left')
        md_file.create_md_file()

def connect(token):
    return login(token=token)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument('--github_org',
                        help='github org',
                        default=DEFAULT_GITHUB_ORG)
    parser.add_argument('--github_repos',
                        nargs='*',
                        help='github repo names. if not specified, tool will include all repos in org by default.')
    parser.add_argument('--token',
                        help='github token.')
    parser.add_argument('--issue_state',
                        choices=['open', 'closed', 'all'],
                        default='all',
                        help='Return open, closed, or all issues')
    parser.add_argument('--start-time',
                        help='Start datetime for tickets to find. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.')
    parser.add_argument('--end-time',
                        help='End datetime for tickets to find. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.')

    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        logger.error(f'Github token must be provided or set as environment variable (GITHUB_TOKEN).')
        sys.exit(1)

    gh = login(token=token)
    _md_file = MdUtils(file_name='pdsen_issues', title='PDS EN Issues')
    for _repo in gh.repositories_by(args.github_org):
        if args.github_repos and _repo.name not in args.github_repos:
            continue

        issues_map = get_issues_groupby_type(_repo, args.issue_state, args.start_time)

        convert_issues_to_planning_report(_md_file, _repo.name, issues_map)
