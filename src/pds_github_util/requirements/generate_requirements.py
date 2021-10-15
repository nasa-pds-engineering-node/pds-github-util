import argparse
import logging
import sys
from pds_github_util.requirements.requirements import Requirements, NoAppropriateVersionFoundException
from pds_github_util.utils import addStandardArguments


_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Create a requirement report')
    addStandardArguments(parser)
    parser.add_argument('--organization', dest='organization',
                        help='github organization owning the repo (e.g. NASA-PDS)')
    parser.add_argument('--repository', dest='repository',
                        help='github repository name')
    parser.add_argument('--dev', dest='dev',
                        nargs='?',
                        const=True, default=False,
                        help="Generate requirements with impacts related to latest dev/snapshot version")
    parser.add_argument('--output', dest='output',
                        help='directory where version/REQUIREMENTS.md file is created')
    parser.add_argument('--format', dest='format', default='md',
                        help='markdown (md) or html')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")

    try:
        requirements = Requirements(args.organization, args.repository, token=args.token, dev=args.dev)
        requirement_file = requirements.write_requirements(root_dir=args.output, format=args.format)
        print(requirement_file)
    except NoAppropriateVersionFoundException as e:
        print('')  # Write just a newline to stdout I guess
        _logger.error(e)
        sys.exit(0)  # we don't want the github action to fail after that


if __name__ == "__main__":
    main()
