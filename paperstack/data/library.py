"""Provides Library database class."""

import sqlite3

from paperstack.filesystem.file import File


class Library:
    """Library class. This is in charge of communicating with the database
    and creating `Record` instances.

    Parameters
    -----------
    config : paperstack.filesystem.config.Config
        `Config` instance.

    Attributes
    ----------
    config : paperstack.filesystem.config.Config
        `Config` instance.
    data_dir : paperstack.filesystem.file.File
        The directory where library data will be stored.
    connection : sqlite3.Connection
    """

    def __init__(self, config):
        self.config = config

        self.data_dir = File(
            self.config.get('paths', 'data'),
            True
        )
        self.data_dir.ensure()

        self.connection = None
        self.cursor = None

        self.connect()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS library (
                record_id INTEGER PRIMARY KEY,
                record_type TEXT,
                author TEXT,
                organization TEXT,
                title TEXT,
                journal TEXT,
                publisher TEXT,
                year TEXT,
                volume TEXT,
                series TEXT,
                number TEXT,
                pages TEXT,
                month TEXT,
                address TEXT,
                edition TEXT,
                howpublished TEXT,
                url TEXT,
                urldate TEXT,
                doi TEXT,
                issn TEXT,
                bibnote TEXT,
                note TEXT,
                bibcode TEXT,
                arxiv TEXT,
                path TEXT
            )
            """
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

        self.cursor.execute(record.to_sql())


    def remove(self, record_id):
        """Remove record using record ID.

        Parameters
        ----------
        record_id : int
        """

        self.cursor.execute(
            f'DELETE FROM library WHERE record_id = {record_id}'
        )


    def update(self, arg):
        pass


    def filter(self, filters):
        """Select all items satisfying filters and build records.

        Parameters
        ----------
        filters : list
            Each filter is a tuple with (field, query).
        """

        if len(filters):
            filter_strings = []

            for field, query in filters:
                query = query.replace('"', '')
                filter_strings.append(f'{field} LIKE "%{query}%"')

            filter_string = ', '.join(filter_strings)

            result = self.connection.execute(
                f'SELECT * FROM library WHERE {filter_string}'
            )
        else:
            result = self.connection.execute(f'SELECT * FROM library')

        result = result.fetchall()

        print(result)
