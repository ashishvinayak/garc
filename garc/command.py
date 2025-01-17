from __future__ import print_function

import os
import sys
import json
import signal
import codecs
import logging
import argparse
from garc import __version__
from garc.client import Garc
import re 

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input 
    str_type = unicode
else:
    # Python 3
    get_input = input
    str_type = str


commands = [
    'configure',
    'user_agent',
    'help',
    'search',
    'user',
    'userposts',
    'usercomments',
    'top'
]


cleanr = re.compile('<.*?>')
def clean_text(raw_html):
    ''' Cleans up text based on reg exp'''
    clean_text = re.sub(cleanr, '', raw_html)
    return clean_text

def main():
    parser = get_argparser()
    args = parser.parse_args()

    command = args.command
    query = args.query or ""

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # catch ctrl-c so users don't see a stack trace
    signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))

    if command == "version":
        print("garc v%s" % __version__)
        sys.exit()
    elif command == "help" or not command:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    garc search make america great again")
        print("\nFor example:\n\n    garc usercomments username --number_gabs=40 --content_key=content")
        sys.exit(1)

    g = Garc(
        user_account=args.user_account,
        user_password=args.user_password,
        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile)

    # calls that return gabs
    if command == "search":
        things = g.search(
            query,
            search_type=args.search_type,
            gabs=args.number_gabs,
            gabs_after=args.gabs_after,
            gabs_before=args.gabs_before)

    elif command == 'user_agent':
        g.save_user_agent()
        sys.exit()
    elif command == "configure":
        g.input_keys()
        sys.exit()
    elif command == 'user':
        things = g.user(query)

    elif command == 'userposts':
        things = g.userposts(
            query,
            gabs=args.number_gabs,
            gabs_after=args.gabs_after
        )
    elif command == 'usercomments':
        things = g.usercomments(query, gabs=args.number_gabs, gabs_after=args.gabs_after, gabs_before=args.gabs_before)
    elif command == 'followers':
        things = g.followers(query)
    elif command == 'following':
        things = g.following(query)
    elif command == 'publicsearch':
        things = g.public_search(
            query,
            gabs=args.number_gabs
        )
    elif command == 'top':
        things = g.top(timespan=query if query else None)

    else:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    garc search make america great again")
        sys.exit(1)

    # get the output filehandle
    if args.output:
        fh = codecs.open(args.output, 'wb', 'utf8')
    else:
        fh = sys.stdout

    count = 0
    for thing in things:
        if count == int(args.number_gabs):
            break
        count += 1
        context = thing
        if (args.content_key == "content"):
            context = clean_text(context[args.content_key])
        if (args.content_key == "created_at"):
            context = context[args.content_key]
        if args.format == "json":
            print(json.dumps(context), file=fh)
        logging.info("archived %s", thing['id'])
    # add data count to file
    if args.output:
        cwd = os.getcwd()
        os.rename(os.path.join(cwd, args.output), os.path.join(cwd, args.output + '_gabCount_' + str(count)))


def get_argparser():
    """
    Get the command line argument parser.
    """

    parser = argparse.ArgumentParser("garc")
    parser.add_argument('command', choices=commands)
    parser.add_argument('query', nargs='?', default=None)
    parser.add_argument("--log", dest="log",
                        default="garc.log", help="log file")
    parser.add_argument("--user_account",
                        default=None, help="Gab account name")
    parser.add_argument("--user_password",
                        default=None, help="Gab account password")
    parser.add_argument('--config',
                        help="Config file containing Gab account info")
    parser.add_argument('--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('--warnings', action='store_true',
                        help="Include warning messages in output")
    parser.add_argument("--connection_errors", type=int, default="0",
                        help="Number of connection errors before giving up")
    parser.add_argument("--http_errors", type=int, default="0",
                        help="Number of http errors before giving up")
    parser.add_argument("--output", action="store", default=None,
                        dest="output", help="write output to file path")
    parser.add_argument("--format", action="store", default="json",
                        dest="format", choices=["json"],
                        help="set output format")
    parser.add_argument("--search_type", action="store", default="date",
                        dest="search_type", choices=["date"],
                        help="set search type")
    parser.add_argument("--number_gabs", action="store", type=int, default=-1,
                        dest="number_gabs",
                        help="approximate number of gabs to return")
    parser.add_argument("--gabs_after", action="store", default="2000-01-01",
                        dest="gabs_after",
                        help="approximate date of earliest gab you wish to collect")
    parser.add_argument("--gabs_before", action="store", default="2030-01-01",
                        dest="gabs_before",
                        help="approximate date of latest gab you wish to collect")

    parser.add_argument("--content_key", action="store", type=str, default="all",
                        dest="content_key",
                        help="clean up data to return only content key")

    return parser
