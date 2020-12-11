import unittest
import os
from pds_github_util.gh_pages.build_summaries import build_summaries

TOKEN = os.environ.get('GITHUB_TOKEN')

class MyTestCase(unittest.TestCase):
    def test_default_summaries(self):
        #pass
        build_summaries(TOKEN, path='tmp', format='md')

    def test_rst_summaries(self):
        #pass
        build_summaries(TOKEN, path='tmp', format='rst')


if __name__ == '__main__':
    unittest.main()
