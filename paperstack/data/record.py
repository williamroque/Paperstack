"Module providing Record base data class."

import re
import os
import sys

from paperstack.data.constants import COLUMNS


class Record:
    """Library record handling validation. This is the most basic data
    class in the program. Database information will be deserialized into
    this. Each `Record` instance will be in charge of its own BibTeX entry
    when exporting.

    Parameters
    ----------
    record : dict
        The entries of the record.
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger

    Attributes
    ----------
    RECORD_TYPE : {'article', 'book', 'website'}
        The type of record.
    record : dict
        The entries of the record.
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    requirements : list
        A list of requirement tuples.
    """

    RECORD_TYPE = None

    def __init__(self, record, config, messenger):
        self.record = record
        self.config = config
        self.messenger = messenger

        self.requirements = []

        self.setup()
        self.validate()


    def tabulate_horizontal(self):
        """Represent the record as a horizontal table.

        Returns
        -------
        str
        """

        record = {}
        
        for key, value in self.record.items():
            if value is not None:
                width = max(len(key), len(value))

                key = key.center(width, ' ')
                value = value.ljust(width, ' ')

                record[key] = value

        output = '│ ' + ' │ '.join(record.keys()) + ' │'

        header_width = len(output) - 2

        output += '\n'
        output += '│ ' + ' │ '.join(record.values()) + ' │'

        output = '┌' + '─' * header_width + '┐' + '\n' + output
        output += '\n' + '└' + '─' * header_width + '┘'

        return output


    def tabulate_vertical(self):
        """Represent the record as a vertical table.

        Returns
        -------
        str
        """

        keys = map(str, self.record.keys())
        values = map(str, self.record.values())

        key_width = max(*map(len, keys))
        value_width = max(*map(len, values))

        output_lines = []
        
        for key, value in self.record.items():
            if value is not None:
                key = key.center(key_width, ' ')
                value = value.center(value_width, ' ')

                output_lines.append(f'│ {key} │ {value} │')

        output = '\n'.join(output_lines)

        header_width = len(output.split('\n', maxsplit=1)[0]) - 2

        output = '┌' + '─' * header_width + '┐' + '\n' + output
        output += '\n' + '└' + '─' * header_width + '┘'

        return output


    def __str__(self):
        output = self.tabulate_horizontal()

        output_lines = output.split('\n')
        output_width = max(*map(len, output_lines))

        if output_width > os.get_terminal_size().columns:
            output = self.tabulate_vertical()

        return output


    def validate(self):
        """Validate record according to requirements. Fields can be marked
        as required and constraints can be placed based on type and pattern
        matching.
        """

        for requirement in self.requirements:
            field, field_type, required, pattern = requirement

            if field in self.record and self.record[field] is not None:
                if not isinstance(self.record[field], field_type):
                    self.messenger.send_error(
                        'Invalid record. Expected type `{}` for field "{}", but instead got `{}`'.format(
                            field_type.__name__,
                            field,
                            type(self.record[field]).__name__
                        )
                    )
                elif pattern is not None and not re.match(pattern, self.record[field]):
                    self.messenger.send_error(
                        f'Invalid record. Field `{field}` does not match pattern `{pattern}`'
                    )
            elif required:
                self.messenger.send_error(f'Invalid record. Field `{field}` required')
            else:
                self.record[field] = None


    def add_requirement(self, field, field_type, required=True, pattern=None):
        """Add a field requirement.

        Parameters
        ----------
        field : str
            Which field to add requirement to
        field_type : any
            Python type of field
        required : bool, optional
            Whether field must exist
        pattern : str, optional
            RegEx pattern for field if type is str"""

        self.requirements.append((field, field_type, required, pattern))


    def generate_id(self):
        """Generate unique record ID (later used as BibTeX key) based on
        configuration.

        Returns
        -------
        str
        """

        record_type = self.__class__.RECORD_TYPE

        if record_type is None:
            raise NotImplementedError

        record_id = self.config.get(record_type, 'id-format').strip()

        item_pattern = re.compile(r'(\w+)@(\d+)')

        for field, length in item_pattern.findall(record_id):
            length = int(length)

            if field not in self.record:
                self.messenger.send_error(f'Cannot create record ID with non-existent field {field}.')

            if field == 'author':
                authors = self.record['author'].split(' and ')[:length]
                sub = '-'.join(authors)
            else:
                sub = self.record[field][:length].strip()

            record_id = record_id.replace(f'{field}@{length}', sub)

        record_id = re.sub(r'\s', '-', record_id)
        record_id = re.sub(r'[^0-9A-Za-z-]', '', record_id)
        record_id = record_id.lower()

        return record_id


    def setup(self):
        "Set up requirements according to record type."

        raise NotImplementedError


    def to_sql(self):
        "Export to SQL (SQL insert command)."

        fields = 'record_type, {}'.format(
            ', '.join(self.record.keys())
        )

        values = '"{}", '.format(self.__class__.RECORD_TYPE)

        values += ', '.join(
            '"{}"'.format(
                value.replace('"', '%QUOTE')
            ) if value else 'NULL' for value in self.record.values()
        )

        return f'INSERT INTO library ({fields}) VALUES ({values})'


class Article(Record):
    """Article record for academic papers.

    Parameters
    ----------
    record : dict
        The entries of the record."""

    RECORD_TYPE = 'article'

    def __init__(self, record, config, messenger):
        super().__init__(record, config, messenger)


    def setup(self):
        if 'record_id' not in self.record or self.record['record_id'] is None:
            self.record['record_id'] = self.generate_id()

        self.add_requirement('record_id', str, True)
        self.add_requirement('author', str, True)
        self.add_requirement('title', str, True)
        self.add_requirement('journal', str, True)
        self.add_requirement('year', str, True)
        self.add_requirement('volume', str, False)
        self.add_requirement('number', str, False)
        self.add_requirement('pages', str, False)
        self.add_requirement('month', str, False)
        self.add_requirement('doi', str, False)
        self.add_requirement('issn', str, False)
        self.add_requirement('bibnote', str, False)
        self.add_requirement('note', str, False)
        self.add_requirement('path', str, False)
        self.add_requirement('tags', str, False)


record_constructors = {
    'article': Article
}


def build_record(record_list, config, messenger):
    """Build `Record` instance from well-ordered record list. This is the
    type of list that would come from a SELECT query.

    Parameters
    ----------
    record_list : list
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    """

    record_dict = {
        COLUMNS[i][0] : value.replace('%QUOTE', '"') if value else value
        for i, value in enumerate(record_list)
    }

    constructor = record_constructors[record_list[1]]

    record = constructor(record_dict, config, messenger)

    return record
