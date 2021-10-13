# encoding: utf-8

'''😡 Argument parsing utilities'''

from argparse import ArgumentParser
from pds_github_util import __version__
import logging


def addStandardArguments(parser: ArgumentParser):
    '''Add a set of standard command-line arguments to the given ``parser``. Currently, the
    standard consits of:

    • ``--version``, to give the standard version metadata
    '''

    parser.add_argument('--version', action='version', version=__version__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--debug',
        action='store_const', const=logging.DEBUG, default=logging.INFO, dest='loglevel',
        help='Log copious debugging messages suitable for developers'
    )
    group.add_argument(
        '-q', '--quiet',
        action='store_const', const=logging.WARNING, dest='loglevel',
        help="Don't log anything except warnings and critically-important messages"
    )
