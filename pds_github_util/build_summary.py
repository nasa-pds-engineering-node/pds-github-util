import argparse

from pds_github_util.gh_pages.summary import write_build_summary


def main():
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--output', dest='output',
                        default='output',
                        help='markdown output file name')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    parser.add_argument('--dev', dest='dev',
                        action='store_true',
                        default=False,
                        help='if present we search for dev versions, otherwise stable versions are returned')
    args = parser.parse_args()

    output_dir = write_build_summary(root_dir=args.output, token=args.token, dev=args.dev)
    print(output_dir)




if __name__ == "__main__":
    main()

