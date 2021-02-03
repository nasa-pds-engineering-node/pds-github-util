import unittest
import os
import logging
from pds_github_util.release.maven_release import maven_get_version

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MavenGetVersionTestCase(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.environ['GITHUB_WORKSPACE'] = os.path.join(current_dir, 'data')

    def test_maven_get_version(self):
        version = maven_get_version()
        logger.info(f"found version is {version}")
        self.assertGreaterEqual(len(version), 3)

    def tearDown(self):
        del os.environ['GITHUB_WORKSPACE']


if __name__ == '__main__':
    unittest.main()
