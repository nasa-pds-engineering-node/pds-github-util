import os
import re
from .snapshot_release import snapshot_release_publication


SNAPSHOT_TAG_SUFFIX = "+dev"


def python_get_version():
    setup_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'setup.py')
    prog = re.compile("version=.*")
    with open(setup_path, 'r') as f:
        for line in f:
            line = line.strip()
            if prog.match(line):
                return line[9:-2]


if __name__ == "__main__":
    snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, python_get_version)
