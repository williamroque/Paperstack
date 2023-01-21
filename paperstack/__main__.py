"""Paperstack: A universal bibliography management tool"""


import argparse
import sys

from paperstack.data.library import Library
from paperstack.data.record import Article
from paperstack.filesystem.config import Config
from paperstack.interface.message import Messenger


def list_records(args):
    config = Config(args.config_path)
    library = Library(config)

    library.filter([])


def add_record(args):
    config = Config(args.config_path)
    library = Library(config)

    messenger = Messenger(args.ansi)

    record_types = {
        'article': Article
    }

    if args.type not in record_types:
        messenger.send_error('Invalid record type.')

    constructor = record_types[args.type]

    record_dict = {}
    entries = args.entries.split(';')

    for entry in entries:
        if entry.strip():
            key, value = entry.split(':')

            record_dict[key.strip()] = value.strip()

    record = constructor(record_dict)

    library.add(record)
    library.commit()

    messenger.send_success('Added item.')


def remove_record(args):
    config = Config(args.config_path)
    library = Library(config)

    messenger = Messenger(args.ansi)

    library.remove(args.id)
    library.commit()

    messenger.send_success('Removed item.')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config-path',
        type = str,
        help = 'Path to Paperstack configuration.',
        default = None
    )

    parser.add_argument(
        '--ansi',
        help = 'Use ANSI colors in the output.',
        default = True,
        action = 'store_true'
    )
    parser.add_argument(
        '--no-ansi',
        help = 'Do not use ANSI colors in the output.',
        dest = 'ansi',
        action = 'store_false'
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
        'type',
        type = str,
        help = 'Record type (article/book/website).'
    )

    add_parser.add_argument(
        'entries',
        type = str,
        help = 'Entries relating to record type (e.g., "title: Life and Works; author: W. Roque and A. Mosenkov; year: 2020; journal: Astronomy and Computing").'
    )

    remove_parser = subparsers.add_parser(
        'remove',
        help = 'Remove a library record.'
    )
    remove_parser.set_defaults(func=remove_record)

    remove_parser.add_argument(
        'id',
        type = str,
        help = 'Numerical record ID.'
    )

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help(sys.stderr)


if __name__ == '__main__':
    main()
