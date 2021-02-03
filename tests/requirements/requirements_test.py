import unittest
import os
import logging
from pds_github_util.requirements.requirements import Requirements
from pds_github_util.utils.tokens import GITHUB_TOKEN

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyTestCase(unittest.TestCase):
    def test_get_requirements(self):
        requirements = Requirements('NASA-PDS', 'pds-doi-service', token=GITHUB_TOKEN)
        requirement_summary = requirements.get_requirements()
        logger.info(requirement_summary)


    def test_get_requirement_task_map(self):
        requirements = Requirements('NASA-PDS', 'pds-doi-service', token=GITHUB_TOKEN)
        requirement_summary = requirements._get_requirement_tag_map()


    def test_generate_requirement_file(self):
        requirements = Requirements('NASA-PDS', 'pds-doi-service', token=GITHUB_TOKEN, dev=True)
        requirements.write_requirements(md_file_name='output/REQUIREMENTS.md')

    def test_generate_requirement_file_in_dir(self):
        requirements = Requirements('NASA-PDS', 'pds-doi-service', token=GITHUB_TOKEN, dev=True)
        requirements.write_requirements(root_dir='pdsen-corral')

    def test_generate_requirement_file_in_html(self):
        requirements = Requirements('NASA-PDS', 'pds-doi-service', token=GITHUB_TOKEN, dev=True)
        requirements.write_requirements(root_dir='pdsen-corral', format='html')


if __name__ == '__main__':
    unittest.main()
