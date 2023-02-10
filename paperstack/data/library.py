"""Provides Library database class."""

import sqlite3

from paperstack.filesystem.file import File
from paperstack.data.constants import COLUMNS
from paperstack.data.record import build_record


class Library:
    """Library class. This is in charge of communicating with the database
    and creating `Record` instances.

    Parameters
    -----------
    config : paperstack.filesystem.config.Config
        `Config` instance.
    messenger : paperstack.interface.message.Messenger

    Attributes
    ----------
    config : paperstack.filesystem.config.Config
        `Config` instance.
    messenger : paperstack.interface.message.Messenger
    data_dir : paperstack.filesystem.file.File
        The directory where library data will be stored.
    connection : sqlite3.Connection
    """

    def __init__(self, config, messenger):
        self.config = config
        self.messenger = messenger

        self.data_dir = File(
            self.config.get('paths', 'data'),
            True
        )
        self.data_dir.ensure()

        self.connection = None
        self.cursor = None

        self.connect()

        columns_string = ', '.join(
            ' '.join(column) for column in COLUMNS
        )

        self.cursor.execute(
            f'CREATE TABLE IF NOT EXISTS library ({columns_string})'
        )


    def connect(self):
        "Connect to sqlite3 library database."

        self.connection = sqlite3.connect(
            self.data_dir.join('library.db')
        )
        self.cursor = self.connection.cursor()


    def commit(self):
        "Commit a change to the database."

        self.connection.commit()


    def close(self):
        "Close connection to library database."

        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.cursor = None


    def add(self, record):
        """Use record SQL export to add to library.

        Parameters
        ----------
        record : paperstack.data.record.Record
        """

        try:
            self.cursor.execute(record.to_sql())
        except sqlite3.OperationalError:
            self.messenger.send_error(
                'Bad query. Make sure all columns exist.'
            )
        except sqlite3.IntegrityError:
            self.messenger.send_error(
                'Bad query. Make sure record is unique.'
            )


    def remove(self, record_id):
        """Remove record using record ID.

        Parameters
        ----------
        record_id : int
        """

        self.get(record_id)

        try:
            self.cursor.execute(
                f'DELETE FROM library WHERE record_id = "{record_id}"'
            )
        except sqlite3.OperationalError:
            self.messenger.send_error(
                'Bad query. Make sure all columns exist.'
            )


    def update(self, record_id, entries):
        """Use record SQL export to update entry in library.

        Parameters
        ----------
        record_id : int
        entries : dict
            Dictionary containing the fields and values to update.
        """

        if len(entries) == 0:
            return

        record = self.get(record_id)
        record.record = {**record.record, **entries}
        record.validate()
        record.sanitize()

        for key in entries:
            entries[key] = record.record[key]

        update_strings = []

        for field, value in entries.items():
            if value:
                value = value.replace('"', '%QUOTE')
            else:
                value = ''

            update_strings.append(f'{field} = "{value}"')

        update_string = ', '.join(update_strings)

        try:
            self.cursor.execute(
                f'UPDATE library SET {update_string} WHERE record_id = "{record_id}"'
            )
        except sqlite3.OperationalError:
            self.messenger.send_error(
                'Bad query. Make sure all columns exist.'
            )


    def get(self, record_id):
        """Select item corresponding to record id.

        Parameters
        ----------
        record_id : str

        Returns
        -------
        paperstack.data.record.Record
        """

        try:
            result = self.connection.execute(
                f'SELECT * FROM library WHERE record_id = "{record_id}"'
            )
            result = result.fetchall()[0]
        except sqlite3.OperationalError:
            self.messenger.send_error(
                'Bad query. Make sure all columns exist.'
            )
        except IndexError:
            self.messenger.send_error(
                f'Could not find record with ID "{record_id}".'
            )

        return build_record(result, self.config, self.messenger)


    def filter(self, filters):
        """Select all items satisfying filters and build records.

        Parameters
        ----------
        filters : list
            Each filter is a tuple with (field, query).

        Returns
        -------
        list
        """

        try:
            if len(filters):
                filter_strings = []

                for field, query in filters:
                    query = query.strip()
                    query = query.replace('"', '')

                    if field == 'tags':
                        filter_strings.append(f'{field} LIKE "%;{query};%"')
                    elif query and query[0] == '`':
                        filter_strings.append(f'{field} = "{query[1:]}"')
                    else:
                        filter_strings.append(f'{field} LIKE "%{query}%"')

                filter_string = ', '.join(filter_strings)

                result = self.connection.execute(
                    f'SELECT * FROM library WHERE {filter_string}'
                )
            else:
                result = self.connection.execute(f'SELECT * FROM library')

            result = result.fetchall()
        except sqlite3.OperationalError:
            self.messenger.send_error(
                'Bad query. Make sure all columns exist.'
            )

        records = [
            build_record(row, self.config, self.messenger)
            for row in result
        ]

        return records
