"Module providing Record base data class."

import re

from paperstack.data.constants import COLUMNS


class InvalidRecord(Exception):
    """A catchall exception for invalid records.

    Attributes
    ----------
    message : str

    Parameters
    ----------
    message : str
    """

    def __init__(self, message=None):
        self.message = 'Invalid record'

        if message is not None:
            self.message += ': ' + message

        super().__init__(self.message)


class Record:
    """Library record handling validation. This is the most basic data
    class in the program. Database information will be deserialized into
    this. Each `Record` instance will be in charge of its own BibTeX entry
    when exporting.

    Parameters
    ----------
    record : dict
        The entries of the record.
    record_type : {'article', 'book', 'website'}
        The type of record.

    Attributes
    ----------
    record : dict
        The entries of the record.
    record_type : {'article', 'book', 'website'}
        The type of record.
    requirements : list
        A list of requirement tuples.
    """

    RECORD_TYPE = None

    def __init__(self, record):
        self.record = record

        self.requirements = []

        self.setup()
        self.validate()


    def __str__(self):
        output = ''

        record = {}

        for key, value in self.record.items():
            if value is not None:
                width = max(len(key), len(value))

                key = key.center(width, ' ')
                value = value.ljust(width, ' ')

                record[key] = value

        output += ' │ '.join(record.keys())
        output += '\n'
        output += ' │ '.join(record.values())

        return output


    def validate(self):
        """Validate record according to requirements. Fields can be marked
        as required and constraints can be placed based on type and pattern
        matching.

        Raises
        ------
        InvalidRecord
            Raised when a requirement is not met in the record.
        """

        for requirement in self.requirements:
            field, field_type, required, pattern = requirement

            if field in self.record and self.record[field] is not None:
                if not isinstance(self.record[field], field_type):
                    raise InvalidRecord(
                        'Expected type `{}` for field "{}", but instead got `{}`'.format(
                            field_type.__name__,
                            field,
                            type(self.record[field]).__name__
                        )
                    )

                if pattern is not None and not re.match(pattern, self.record[field]):
                    raise InvalidRecord(
                        f'Field `{field}` does not match pattern `{pattern}`'
                    )
            elif required:
                raise InvalidRecord(f'Field `{field}` required')
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

    def __init__(self, record):
        super().__init__(record)


    def setup(self):
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


record_constructors = {
    'article': Article
}


def build_record(record_list):
    """Build `Record` instance from well-ordered record list. This is the
    type of list that would come from a SELECT query.

    Parameters
    ----------
    record_list : list
    """

    _, record_type, *record_list = record_list
    columns = COLUMNS[2:]

    record_dict = {
        columns[i][0] : value for i, value in enumerate(record_list)
    }

    constructor = record_constructors[record_type]

    record = constructor(record_dict)

    return record
