#!/usr/bin/env python
"""
Tool to generate simple markdown issue reports
"""
import argparse
import logging
import os
import sys


from mdutils.mdutils import MdUtils


from pds_github_util.utils import GithubConnection, RstClothReferenceable

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


def get_issues_groupby_type(repo, state='all', start_time=None, ignore_types=None):
    issues = {}
    for t in ISSUE_TYPES:
        print(f'++++++++{t}')
        if ignore_types and t in ignore_types:
            continue

        issues[t] = []
        for issue in repo.issues(state=state, labels=t, direction='asc', since=start_time):
            if ignore_issue(issue.labels()):
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



def add_rst_sub_section(d, repo, type, issues):
    d.h3(type)

    columns = ["Issue", "Priority / Bug Severity"]

    #issue = f'[{repo_name}#{short_issue.number}]({short_issue.html_url}) - {short_issue.title}'

    data = []
    for issue in issues:
        d.hyperlink(f'{repo}_{issue.number}', issue.html_url)
        data.append([f'{repo}_{issue.number}_ {issue.title}'.replace('|', ''), get_issue_priority(issue)])

    d.table(columns,
            data=data)




def write_rst_repo_section(d, repo, issues_map):
    
    d.h2(repo)

    for issue_type,issues in issues_map.items():
        if issues:
            print(issues)
            add_rst_sub_section(d, repo, issue_type, issues)







def create_md_issue_report(org, repos, issue_state='all', start_time=None, token=None):

    gh = GithubConnection.getConnection(token=token)

    _md_file = MdUtils(file_name='pdsen_issues', title='PDS EN Issues')
    for _repo in gh.repositories_by(org):
        if repos and _repo.name not in repos:
            continue
        issues_map = get_issues_groupby_type(_repo, state=issue_state, start_time=start_time)
        convert_issues_to_planning_report(_md_file, _repo.name, issues_map)

    md_file.create_md_file()


def create_rst_issue_report(org, repos,
                            title='Release Description Document (build 11.1)',
                            issue_state='all',
                            start_time=None,
                            token=None):

    gh = GithubConnection.getConnection(token=token)

    d = RstClothReferenceable()
    d.title(title)

    for _repo in gh.repositories_by(org):
        if repos and _repo.name not in repos:
            continue
        issues_map = get_issues_groupby_type(_repo, state=issue_state, start_time=start_time)

        write_rst_repo_section(d, _repo.name, issues_map)

    logger.info(f'Create file pdsen_issues.rst.rst')
    d.write(f'pdsen_issues.rst')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument('--github-org',
                        help='github org',
                        default=DEFAULT_GITHUB_ORG)
    parser.add_argument('--github-repos',
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
    parser.add_argument('--format', default='md',
                        help='rst or md')

    args = parser.parse_args()

    if args.format == 'md':
        create_md_issue_report(
            args.github_org,
            args.github_repos,
            issue_state=args.issue_state,
            start_time=args.start_time,
            token=args.token
        )

    elif args.format == 'rst':
        create_rst_issue_report(
            args.github_org,
            args.github_repos,
            issue_state=args.issue_state,
            start_time=args.start_time,
            token=args.token
        )
    else:
        logger.error("unsupported format %s, must be rst or md", args.format)

