import argparse
from pds_github_util.requirements.requirements import Requirements



def main():
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--organization', dest='organization',
                        help='github organization owning the repo (e.g. NASA-PDS)')
    parser.add_argument('--repository', dest='repository',
                        help='github repository name')
    parser.add_argument('--output', dest='output',
                        help='markdown output file name')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    args = parser.parse_args()

    requirements = Requirements(args.organization, args.repository, token=args.token)
    requirements.write_requirements(args.output)


if __name__ == "__main__":
    main()
