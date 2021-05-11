import unittest
import os
from pds_github_util.gh_pages.summary import write_build_summary
from pds_github_util.utils.tokens import GITHUB_TOKEN


class MyTestCase(unittest.TestCase):
    def test_simple_rst(self):
        current_dir = os.path.dirname(__file__)
        gitmodules = os.path.join(current_dir, '.gitmodules')
        write_build_summary(gitmodules=gitmodules, root_dir='./tmp',
                            token=GITHUB_TOKEN, dev=False, version='11.0', format='rst')


if __name__ == '__main__':
    unittest.main()
