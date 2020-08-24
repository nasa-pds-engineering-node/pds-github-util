import unittest
import os
from pds_github_util.gh_pages.build_summaries import build_summaries

TOKEN = os.environ.get('GITHUB_TOKEN')

class MyTestCase(unittest.TestCase):
    def test_something(self):
        build_summaries(TOKEN)


if __name__ == '__main__':
    unittest.main()
