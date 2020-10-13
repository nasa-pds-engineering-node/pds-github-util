"""Release Planning."""

import argparse
import github3
import logging
import os
import sys
import traceback

from pds_github_util.zenhub.zenhub import Zenhub
from pkg_resources import resource_string
from pystache import Renderer

# PDS Github Org
GITHUB_ORG = 'NASA-PDS'

REPO_INFO = ('\n--------\n\n'
             '{}\n'
             '{}\n\n'
             '*{}*\n\n'
             '.. list-table:: \n'
             '   :widths: 15 15 15 15 15 15\n\n'
             '   * - `User Guide <{}>`_\n'
             '     - `Github Repo <{}>`_\n'
             '     - `Issue Tracking <{}/issues>`_ \n'
             '     - `Backlog <{}/issues?q=is%3Aopen+is%3Aissue+label%3Abacklog>`_ \n'
             '     - `Stable Release <{}/releases/latest>`_ \n'
             '     - `Dev Release <{}/releases>`_ \n\n')

# Quiet github3 logging
logger = logging.getLogger('github3')
logger.setLevel(level=logging.WARNING)

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    parser.add_argument('--github_token',
                        help='github API token')
    parser.add_argument('--zenhub_token',
                        help='zenhub API token')
    parser.add_argument('--build_number',
                        help='build number',
                        required=True)
    parser.add_argument('--delivery_date',
                        help='EN delivery to I&T date',
                        required=True)
    parser.add_argument('--trr_date',
                        help='EN TRR date',
                        required=True)
    parser.add_argument('--ddr_date',
                        help='EN DDR date',
                        required=True)
    parser.add_argument('--release_date',
                        help='EN DDR date',
                        required=True)

    # parser.add_argument('--deploy_dir',
    #                     help='directory to deploy the validate tool on the file system',
    #                     default='/tmp')
    # parser.add_argument('--schemas',
    #                     help='path(s) to schemas to validate against')
    # parser.add_argument('--schematrons',
    #                     help='path(s) to schematrons to validate against')
    # parser.add_argument('--skip_content_validation',
    #                     help='validate: skip content validation',
    #                     action='store_true', default=False)
    # parser.add_argument('--failure_expected', dest='failure_expected',
    #                     help='validate expected to fail',
    #                     action='store_true', default=False)
    # parser.add_argument('--datapath',
    #                     help='path(s) to data to validate',
    #                     required=True)
    # parser.add_argument('--output_log_path',
    #                     help='path(s) to output validate run log file',
    #                     default=os.path.join('tmp', 'logs'))
    # parser.add_argument('--with_pds4_version',
    #                     help=('force the following PDS4 version. software will '
    #                           'download and validate with this version of the '
    #                           'PDS4 Information Model. this version should be '
    #                           'the semantic numbered version. e.g. 1.14.0.0'))
    # parser.add_argument('--development_release',
    #                     help=('flag to indicate this should be tested with a '
    #                           'development release of the PDS4 Standard.'),
    #                     action='store_true', default=False)

    args = parser.parse_args()

    # set output filename
    output_fname = f'plan.rst'

    # get github token or throw error
    github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
    if not github_token:
        logger.error(f'github API token must be provided or set as environment'
                     ' variable (GITHUB_TOKEN).')
        sys.exit(1)

    # get zenhub token or throw error
    zenhub_token = args.github_token or os.environ.get('ZENHUB_TOKEN')
    if not zenhub_token:
        logger.error(f'zenhub API token must be provided or set as environment'
                     ' variable (ZENHUB_TOKEN).')
        sys.exit(1)

    try:
        gh = github3.login(token=github_token)
        # gh = github3.GitHub('jordanpadams','Ph1ll1es$8008')
        org = gh.organization(GITHUB_ORG)
        repos = org.repositories()

        issues = []
        repo_dict = {}
        zen = Zenhub(zenhub_token)
        for repo in repos:
            if not issues:
                issues = zen.get_issues_by_release(repo.id, f'B{args.build_number}')

            repo_dict[repo.id] = {'repo': repo,
                                  'issues': []}

        # Build up dictionary of repos + issues in release
        issue_dict = {}
        for issue in issues:
            repo_dict[issue['repo_id']]['issues'].append(issue['issue_number'])

        # Loop through repos
        plan_output = ''
        maintenance_output = ''
        ddwg_plans = ''
        for repo_id in repo_dict:
            r = repo_dict[repo_id]['repo']
            issues = repo_dict[repo_id]['issues']
            repo_output = ''
            if issues:
                for issue_num in issues:
                    gh_issue = gh.issue(org.login, repo_dict[repo_id]['repo'].name, issue_num)
                    zen_issue = zen.issue(repo_id, issue_num)

                    # Custom handling for pds4-information-model SCRs
                    if 'CCB-' in gh_issue.title:
                        ddwg_plans += f'* `{r.name}#{issue_num} <{gh_issue.html_url}>`_ **{gh_issue.title}**\n'

                    # we only want epics in the plan
                    elif zen_issue['is_epic']:
                        repo_output += f'* `{r.name}#{issue_num} <{gh_issue.html_url}>`_ **{gh_issue.title}**\n'
                        for child in zen.get_epic_children(gh, org, repo_id, issue_num):
                            child_repo = child['repo']
                            child_issue = child['issue']
                            repo_output += f'   * `{child_repo.name}#{child_issue.number} <{child_issue.html_url}>`_ {child_issue.title}\n'
                    # print(repo_output)

            repo_info = REPO_INFO.format(r.name,
                                         '#' * len(r.name),
                                         r.description,
                                         r.homepage or r.html_url + '#readme',
                                         r.html_url,
                                         r.html_url,
                                         r.html_url,
                                         r.html_url,
                                         r.html_url)
            # only output the header
            if repo_output:
                plan_output += repo_info
                plan_output += repo_output

        with open(output_fname, 'w') as f_out:

            pystache_dict = {
                'output': output_fname,
                'build_number': args.build_number,
                'delivery_date': args.delivery_date,
                'trr_date': args.trr_date,
                'ddr_date': args.ddr_date,
                'release_date': args.release_date,
                'pds4_changes': ddwg_plans,
                'planned_changes': plan_output
            }
            renderer = Renderer()
            template = resource_string(__name__,  'plan.template.rst')
            rst_str = renderer.render(template, pystache_dict)
            f_out.write(rst_str)

            # else:
            #     maintenance_output += repo_info

            #                     print(f'## {r.name}')
            #     print(f'Description: {r.description}')
            #     print(f'User Guide: {r.homepage}')
            #     print(f'Github Repo: {r.html_url}')
            #     print(f'Issue Tracker: {r.html_url}/issues')

                    # print(repo_dict[repo_id]['repo'].name)
                    # print(repo_dict[repo_id]['issues'])

        # print(repo_dict)

        # for repo in repos:


    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

    logger.info(f'SUCCESS: Release Plan generated successfully.')

if __name__ == '__main__':
    main()
