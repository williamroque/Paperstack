"""Paperstack: A universal bibliography management tool"""


import argparse
import sys


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config-path',
        type = argparse.FileType('r'),
        help = 'Path to Paperstack configuration.',
        default = None
    )

    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser(
        'list',
        help = 'List all library records.'
    )
    list_parser.set_defaults(func=list_records)

    add_parser = subparsers.add_parser(
        'add',
        help = 'Add a library record.'
    )
    add_parser.set_defaults(func=add_record)

    add_parser.add_argument(
        'record-type',
        type = str,
        help = 'Record type (article/book/website).'
    )

    add_parser.add_argument(
        'title',
        type = str,
        help = 'Record title.'
    )

    add_parser.add_argument(
        '--entries',
        type = str,
        help = 'Additional entries relating to record type (e.g., "author: W. Roque and A. Mosenkov; year: 2020; journal: Astronomy and Computing").'
    )

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help(sys.stderr)


if __name__ == '__main__':
    main()
