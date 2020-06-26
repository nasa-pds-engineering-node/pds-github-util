import unittest
import os
import logging
from pds_github_util.branches.broadcast_commit import broadcast_commit

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

class MyTestCase(unittest.TestCase):
    def test_broadcast_commit(self):
        broadcast_commit('NASA-PDS/pdsen-corral', '[0-9]+.[0-9]+', 'test commit message', token=GITHUB_TOKEN)


if __name__ == '__main__':
    unittest.main()
