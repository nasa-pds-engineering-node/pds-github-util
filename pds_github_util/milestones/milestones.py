#!/usr/bin/env python

import argparse
import datetime
import logging
import sys
import os

from github3 import login, exceptions

DEFAULT_GITHUB_ORG = 'NASA-PDS'

# Quiet github3 logging
logger = logging.getLogger('github3')
logger.setLevel(level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_milestone(repo, sprint_title):
    _milestone = None
    for m in repo.milestones():
        if m.title.lower() == sprint_title.lower():
            _milestone = m

    return _milestone


def main():
    parser = argparse.ArgumentParser(description="Tool for closing milestones and producing Github issue reports.")

    # group = parser.add_argument_group('Login / Repo Info')
    # group.add_argument('-u', '--username', help='Username to use for authentication')
    # group.add_argument('-p', '--password', help='Password to use for authentication')
    # parser.add_argument('--token',
    #                     help='github token')
    # group.add_argument('-r', '--repos', nargs='*', help='Subset of repositories to use from config.')
    #
    # group = parser.add_argument_group('Milestone Management')
    # group.add_argument('-d', '--due_date', help='Due date. Format: YYYY-MM-DD')
    # group.add_argument('-D', '--delete_milestone', help='Specify name of milestone to DELETE.')
    # group.add_argument('-a', '--add_milestone', help='Specify name of milestone to ADD. Must also specify due_date.')
    # group.add_argument('-c', '--close_milestone', help='Specify name of milestone to CLOSE.')
    # group.add_argument('-f', '--force', action='store_true', help='Force action. i.e. Force close milestone with open issues.')
    #
    # group = parser.add_argument_group('Multiple Milestone Creation')
    # group.add_argument('--auto', action='store_true', help='Auto-generate sprints and titles with format specified in config starting from due date specified.')
    # group.add_argument('--num_sprints', type=int, default=1, help='Number of sprints to create. Uses "days" configuration for increasing due date.')
    # group.add_argument('--counter_start', type=int, default=1, help='Number to start counter if auto-title enabled and using counter in format.')

    parser.add_argument('--github_org',
                        help='github org',
                        default=DEFAULT_GITHUB_ORG)
    parser.add_argument('--github_repos',
                        nargs='*',
                        help='github repo names. if not specified, tool will include all repos in org by default.')
    # parser.add_argument('--close', help='Specify name of milestone to close.')
    parser.add_argument('--add', help='Specify name of milestone to close.')
    parser.add_argument('--length', default=14, help='milestone length in number of days.')
    parser.add_argument('--token', help='github token.')
    parser.add_argument('--create', action='store_true', help='create milestone.')
    parser.add_argument('--delete', action='store_true', help='delete milestone.')
    parser.add_argument('--close', action='store_true', help='close milestone.')
    parser.add_argument('--due_date', help='Due date of first sprint. Format: YYYY-MM-DD')
    parser.add_argument('--sprint_name_file', help=('yaml file containing list of sprint names. tool will create '
                                                    'as many milestones as specified in file.'))
    parser.add_argument('--sprint_names', nargs='*', help='create one sprint with this name')
    parser.add_argument('--prepend_number', type=int,
                        help='specify number to prepend sprint names or to start with. e.g. 01.foo')

    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        logger.error(f'Github token must be provided or set as environment variable (GITHUB_TOKEN).')
        sys.exit(1)

    _sprint_names = args.sprint_names

    if args.sprint_name_file:
        with open(args.sprint_name_file) as f:
            _sprint_names = f.read().splitlines()

    if not _sprint_names:
        logger.error(f'One of --sprint_names or --sprint_name_file must be specified.')
        sys.exit(1)

    _due_date = None
    if args.create:
        if not args.due_date:
            logger.error(f'--due_date must be specified.')
            sys.exit(1)
        else:
            _due_date = datetime.datetime.strptime(args.due_date, '%Y-%m-%d') + datetime. timedelta(hours=8)

    _sprint_number = args.prepend_number
    for n in _sprint_names:
        _sprint_name = n.replace(' ', '.')

        if not _sprint_name:
            continue

        if _sprint_number is not None:
            _sprint_name = f"{str(_sprint_number).zfill(2)}.{_sprint_name}"
            _sprint_number += 1

        # connect to github
        gh = login(token=token)
        for _repo in gh.repositories_by(args.github_org):
            if args.create:
                logger.info(f"+++ milestone: {_sprint_name}, due: {_due_date}")
                try:
                    logger.info(f"CREATE repo: {_repo.name}")
                    _repo.create_milestone(_sprint_name, due_on=_due_date.strftime('%Y-%m-%dT%H:%M:%SZ'))
                except exceptions.UnprocessableEntity:
                    # milestone already exists with this name
                    logger.info(f"CREATE repo: {_repo.name}, already exists. skipping...")
            elif args.close:
                logger.info(f"+++ milestone: {_sprint_name}")
                _milestone = get_milestone(_repo, _sprint_name)
                if _milestone:
                    logger.info(f"CLOSE repo: {_repo.name}")
                    _milestone.update(state='closed')
                else:
                    logger.info(f"CLOSE repo: {_repo.name}, skipping...")
            elif args.delete:
                logger.info(f"+++ milestone: {_sprint_name}")
                _milestone = get_milestone(_repo, _sprint_name)
                if _milestone:
                    logger.info(f"DELETE repo: {_repo.name}")
                    _milestone.delete()
                else:
                    logger.info(f"DELETE repo: {_repo.name}, skipping...")
            else:
                logger.warning("NONE: no action specified")

        if _due_date:
            # Increment due date for next milestone
            _due_date = _due_date + datetime.timedelta(days=args.length)

if __name__ == "__main__":
    main()
