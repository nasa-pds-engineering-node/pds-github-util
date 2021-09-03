# encoding: utf-8

'''😡 Argument parsing utilities'''

from argparse import ArgumentParser
from pds_github_util import __version__


def addStandardArguments(parser: ArgumentParser):
    '''Add a set of standard command-line arguments to the given ``parser``. Currently, the
    standard consits of:

    • ``--version``, to give the standard version metadata
    '''

    parser.add_argument('--version', action='version', version=__version__)
