import logging
import os
import sys

from github3 import login

# Quiet github3 logging
logger = logging.getLogger('github3')
logger.setLevel(level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GithubConnection():

    gh = None

    @classmethod
    def getConnection(cls, token=None):
        if not cls.gh:
            token = token or os.environ.get('GITHUB_TOKEN')
            if not token:
                logger.error(f'Github token must be provided or set as environment variable (GITHUB_TOKEN).')
                sys.exit(1)

            cls.gh = login(token=token)

        return cls.gh
