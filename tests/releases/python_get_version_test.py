import unittest
import os
import logging
from pds_github_util.release.python_snapshot_release import python_get_version

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PythonGetVersionTestCase(unittest.TestCase):

    def setUp(self):
        if 'GITHUB_WORKSPACE' not in os.environ:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            os.environ['GITHUB_WORKSPACE'] = os.path.join(current_dir, '..', '..')

    def test_python_get_version(self):
        version = python_get_version()
        logger.info(f"found version is {version}")
        self.assertGreaterEqual(len(version), 3)

    def tearDown(self):
        del os.environ['GITHUB_WORKSPACE']


if __name__ == '__main__':
    unittest.main()
