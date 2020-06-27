import unittest
from pds_github_util.gh_pages.root_index import update_index


class MyTestCase(unittest.TestCase):
    def test_root_index(self):
        update_index('output')

if __name__ == '__main__':
    unittest.main()
