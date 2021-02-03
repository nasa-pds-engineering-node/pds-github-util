import os
import unittest
from pds_github_util.corral.cattle_head import CattleHead
from pds_github_util.utils.tokens import GITHUB_TOKEN

class MyTestCase(unittest.TestCase):
    def test_get_changelog_signet(self):
        cattle_head = CattleHead("validate", "https://github.com/nasa-pds/validate", "validate PDS formats", token=GITHUB_TOKEN)
        changelog_signet = cattle_head._get_changelog_signet()


if __name__ == '__main__':
    unittest.main()
