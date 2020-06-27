import unittest
import os
import logging
from pds_github_util.branches.git_actions import ping_repo_branch

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

class MyTestCase(unittest.TestCase):
    def test_ping_branch(self):
        ping_repo_branch('NASA-PDS/pdsen-corral', 'gh-pages', 'test commit message', token=GITHUB_TOKEN)


if __name__ == '__main__':
    unittest.main()
