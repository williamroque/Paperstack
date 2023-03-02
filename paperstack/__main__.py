"""Paperstack: A universal bibliography management tool"""

import argparse
import os

from paperstack.data.library import Library
from paperstack.data.record import record_constructors
from paperstack.data.scrapers import scraper_constructors

from paperstack.filesystem.config import Config
from paperstack.filesystem.file import File

from paperstack.interface.message import Messenger
from paperstack.interface.message import AppMessenger

from paperstack.utility import parse_dict
from paperstack.utility import open_path

from paperstack.interface.app import App


def list_records(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    records = library.filter([])

    for record in records:
        if args.field:
            if args.field in record.record and record.record[args.field]:
                messenger.send_neutral(record.record[args.field])
        else:
            messenger.send_neutral(record)


def filter_records(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    try:
        filters = list(parse_dict(args.query).items())

        records = library.filter(filters)

        for record in records:
            messenger.send_neutral(record)
    except ValueError:
        messenger.send_error('Invalid entries string.')


def add_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    if args.type not in record_constructors:
        messenger.send_error('Invalid record type.')

    constructor = record_constructors[args.type]

    try:
        record = constructor(parse_dict(args.entries), config, messenger)

        library.add(record)
        library.commit()

        messenger.send_success('Added item.')
    except ValueError:
        messenger.send_error('Invalid entries string.')


def remove_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    record = library.get(args.id)

    if 'path' in record.record and record.record['path']:
        path = File(
            config.get('paths', 'data'), True
        ).join(record.record['path'])

        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    library.remove(args.id)
    library.commit()

    messenger.send_success('Removed item.')


def update_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    try:
        library.update(args.id, parse_dict(args.entries))
        library.commit()

        messenger.send_success('Updated item.')
    except ValueError:
        messenger.send_error('Invalid entries string.')


def get_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    record = library.get(args.id)

    if args.field:
        if not args.field in record.record or not record.record[args.field]:
            messenger.send_error(f'No field `{args.field}` in record.')

        messenger.send_neutral(record.record[args.field])
    else:
        messenger.send_neutral(record)


def open_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    record = library.get(args.id)

    if not 'path' in record.record or not record.record['path']:
        messenger.send_error(f'No path specified in record.')

    path = File(
        config.get('paths', 'data'), True
    ).join(record.record['path'])

    try:
        open_path(path)
    except Exception:
        messenger.send_error('Could not open PDF in preferred application.')


def scrape(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)

    messenger = Messenger(args.ansi)

    if args.database not in scraper_constructors:
        messenger.send_error('Invalid database name.')

    constructor = scraper_constructors[args.database]

    try:
        scraper = constructor(
            parse_dict(args.entries),
            config,
            messenger
        )

        record = scraper.create_record()

        if args.add:
            record.download_pdf(scraper)

            library = Library(config, messenger)
            library.add(record)
            library.commit()

            messenger.send_neutral(record)

            messenger.send_success('Added item.')
        else:
            messenger.send_neutral(record)
    except ValueError:
        messenger.send_error('Invalid entries string.')


def export_record(args):
    messenger = Messenger(args.ansi)
    config = Config(messenger, args.config_path)
    library = Library(config, messenger)

    messenger = Messenger(args.ansi)

    ids = args.ids

    for record_id in ids.split(','):
        record_id = record_id.strip()
        record = library.get(record_id)

        citation_types = record.get_csl()

        options = {
            'bibtex': (record.to_bibtex, None)
        }

        for citation_type, path in citation_types.items():
            options[citation_type] = (record.to_citation, path)

        option_names = ', '.join(options.keys())

        if not args.option in options:
            messenger.send_error(f'Export option needs to be one of: {option_names}.')

        option, argument = options[args.option]

        messenger.send_neutral(option(argument))


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

    list_parser.add_argument(
        '--field',
        type = str,
        help = 'The specific field to get (optional).',
        default = None
    )

    filter_parser = subparsers.add_parser(
        'filter',
        help = 'Filter and list library records.'
    )
    filter_parser.set_defaults(func=filter_records)

    filter_parser.add_argument(
        'query',
        type = str,
        help = 'Query to search columns (e.g., "author: `lucretius; title: way things"). Use a backtick for literal search.'
    )

    get_parser = subparsers.add_parser(
        'get',
        help = 'Get a library record.'
    )
    get_parser.set_defaults(func=get_record)

    get_parser.add_argument(
        'id',
        type = str,
        help = 'Record ID.'
    )

    get_parser.add_argument(
        '--field',
        type = str,
        help = 'The specific field to get (optional).',
        default = None
    )

    open_parser = subparsers.add_parser(
        'open',
        help = 'Open library record PDF if it exists.'
    )
    open_parser.set_defaults(func=open_record)

    open_parser.add_argument(
        'id',
        type = str,
        help = 'Record ID.'
    )

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
        help = 'Record ID.'
    )

    update_parser = subparsers.add_parser(
        'update',
        help = 'Update a library record.'
    )
    update_parser.set_defaults(func=update_record)

    update_parser.add_argument(
        'id',
        type = str,
        help = 'Record ID.'
    )

    update_parser.add_argument(
        'entries',
        type = str,
        help = 'Entries to update (e.g., "author: Will Roque; year: 2021").'
    )

    scrape_parser = subparsers.add_parser(
        'scrape',
        help = 'Scrape a database.'
    )
    scrape_parser.set_defaults(func=scrape)

    scrape_parser.add_argument(
        'database',
        type = str,
        help = 'Which database to scrape from (ads/arxiv/mnras).'
    )

    scrape_parser.add_argument(
        'entries',
        type = str,
        help = 'Entries used to find record (e.g., "bibcode: 2015RaSc...50..916A").'
    )

    scrape_parser.add_argument(
        '--add',
        help = 'Add scraped record to the database.',
        default = False,
        action = 'store_true'
    )
    scrape_parser.add_argument(
        '--no-add',
        help = 'Do not add scraped reecord to the database.',
        dest = 'add',
        action = 'store_false'
    )

    export_parser = subparsers.add_parser(
        'export',
        help = 'Export a library record.'
    )
    export_parser.set_defaults(func=export_record)

    export_parser.add_argument(
        'option',
        type = str,
        help = 'The export option (bibtex/html).'
    )

    export_parser.add_argument(
        'ids',
        type = str,
        help = 'Record IDs (comma separated).'
    )

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        messenger = AppMessenger(args.ansi)
        config = Config(messenger, args.config_path)

        messenger.editor_command = config.get('editor', 'command')
        messenger.editor_extension = config.get('editor', 'extension')

        library = Library(config, messenger)

        app = App(config, messenger, library)

        messenger.connect_app(app)

        app.start()


if __name__ == '__main__':
    main()
