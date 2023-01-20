"""Provides Library database class."""

import re


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

    def __init__(self, record, record_type):
        self.record = record
        self.record_type = record_type

        self.requirements = []

        self.setup()


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

            if field in self.record:
                if not isinstance(self.record[field], field_type):
                    raise InvalidRecord(
                        'Expected type `{}` for field `{}`, but instead got {}'.format(
                            field_type,
                            field,
                            type(self.record[field])
                        )
                    )

                if not re.match(pattern, self.record[field]):
                    raise InvalidRecord(
                        f'Field `{field}` does not match pattern `{pattern}`'
                    )
            elif required:
                raise InvalidRecord(f'Field `{field}` required')


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


class Article(Record):
    """Article record for academic papers.

    Parameters
    ----------
    record : dict
        The entries of the record."""

    def __init__(self, record):
        super().__init__(record, 'article')


    def setup(self):
        self.add_requirement('author', str, True)
        self.add_requirement('title', str, True)
        self.add_requirement('journal', str, True)
        self.add_requirement('year', int, True)
        self.add_requirement('volume', int, False)
        self.add_requirement('number', int, False)
        self.add_requirement('pages', str, False)
        self.add_requirement('month', str, False)
        self.add_requirement('doi', str, False)
        self.add_requirement('issn', str, False)
        self.add_requirement('note', str, False)


class Library:
    "Library class."

    def __init__(self, path):
        self.path = path


    def add(self, record):
        pass


    def remove(self, record_id):
        pass


    def update(self, arg):
        pass


    def filter(self, filters):
        pass
