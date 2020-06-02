import os
import logging
import github3
import re
from mdutils import MdUtils
from pds_github_util.tags.tags import Tags

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Requirements:

    def __init__(self, org, repo, token=None):
        self._organization = org
        self._repository = repo

        gh = github3.login(token=token)
        self._repo = gh.repository(self._organization, self._repository)
        self._requirements = self._get_requirements_from_issues()
        self._tags = Tags(org, repo, token=token)
        self._requirements_tag_map = self._get_requirement_tag_map()

    def _get_requirements_from_issues(self):
        summary = {}

        for issue in self._repo.issues(state='all', direction='asc', labels='requirement'):
            topic_assigned = False
            for label in issue.labels():
                if label.name.startswith("requirement-topic"):
                    requirement_topic = label.name.split(':')[1]
                    if requirement_topic not in summary.keys():
                        summary[requirement_topic] = []
                    summary[requirement_topic].append({'number': issue.number,
                                                       'title': issue.title,
                                                       'link': issue.url})
                    topic_assigned = True
                    continue

        if not topic_assigned:
            if "default" not in summary.keys():
                summary["default"] = []
            summary["default"].append({'number': issue.number,
                                       'title': issue.title,
                                       'link': issue.url})

        return summary

    def _get_requirement_tag_map(self):

        requirements_tag_map = {}
        for issue in self._repo.issues(state='closed', direction='asc'):
            body_sections = issue.body.split("**Applicable requirements")
            if len(body_sections) > 1:
                impacted_requirements_str = body_sections[1]
                prog = re.compile("#[0-9]+")
                requirements = prog.findall(impacted_requirements_str)
                requirements = [ int(req[1:]) for req in requirements] # remove leading # and convert to int to be consistent with requirement dictionnary
                for req in requirements:
                    if req not in requirements_tag_map.keys():
                        requirements_tag_map[req] = set()
                    issue_date_isoz = issue.closed_at.isoformat().replace('+00:00', 'Z')
                    earliest_tag_closed_after = self._tags.get_earliest_tag_after(issue_date_isoz)
                    requirements_tag_map[req].add(earliest_tag_closed_after)
        return requirements_tag_map

    def get_requirements(self):
        return self._requirements

    @staticmethod
    def _version_paragraph_intro(versions_len):
        if versions_len == 0:
            return ''
        elif versions_len ==1:
            return 'The version implementing or impacting this requirement is:'
        else:
            return 'The versions implementing or impacting this requirement are:'

    def write_requirements(self, output_file_name):

        output_file_dir = os.path.dirname(output_file_name)
        if len(output_file_dir):
            os.makedirs(output_file_dir, exist_ok=True)
        requirements_md = MdUtils(file_name=output_file_name, title="Requirements Summary")

        for req_topic in self._requirements:
            requirements_md.new_header(level=1, title=req_topic)
            for req in self._requirements[req_topic]:
                title = f"{req['title']} ([#{req['number']}](https://github.com/{self._repo}/issues/{req['number']}))"
                requirements_md.new_header(level=2, title=title)
                versions = self._requirements_tag_map[req['number']] if req['number'] in self._requirements_tag_map.keys() else []
                requirements_md.new_paragraph(self._version_paragraph_intro(len(versions)))
                for v in versions:
                    requirements_md.new_paragraph(f'- [{v}](https://github.com/{self._repo}/releases/tag/{v})')

        requirements_md.create_md_file()