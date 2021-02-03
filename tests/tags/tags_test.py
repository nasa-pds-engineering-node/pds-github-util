import unittest
import os
import logging
from datetime import datetime
from pds_github_util.tags.tags import Tags
from pds_github_util.utils.tokens import GITHUB_TOKEN

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MyTestCase(unittest.TestCase):
    def test_get_earliest_tag_after(self):
        tags = Tags('NASA-PDS', 'validate', token=GITHUB_TOKEN)

        tags.get_earliest_tag_after(datetime(2020, 1, 1).isoformat().replace('+00:00', 'Z'))


if __name__ == '__main__':
    unittest.main()
