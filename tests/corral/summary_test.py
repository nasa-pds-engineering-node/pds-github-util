import unittest
import os
import logging
from pds_github_util.corral.herd import Herd
from pds_github_util.gh_pages.summary import write_build_summary
from pds_github_util.utils.tokens import GITHUB_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyTestCase(unittest.TestCase):

    gitmodules = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '.gitmodules')

    def test_gather_the_herd(self):
        herd = Herd(gitmodules=self.gitmodules,
                    token=GITHUB_TOKEN)
        cattle_heads = herd.get_cattle_heads()
        version = herd.get_shepard_version()

    def test_summary_dev(self):
        write_build_summary(gitmodules=self.gitmodules,
                            output_file_name='output/dev_summary.md',
                            token=GITHUB_TOKEN, dev=True,
                            version='10.0-SNAPSHOT')

    def test_summary_release(self):
        write_build_summary(gitmodules=self.gitmodules,
                            output_file_name='output/rel_summary.md',
                            token=GITHUB_TOKEN, dev=False,
                            version='10.0')


if __name__ == '__main__':
    unittest.main()
