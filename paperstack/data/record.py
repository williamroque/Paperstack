"Module providing Record base data class."

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
        self.validate()


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


    def to_sql(self):
        values = ', '.join(
            '"{}"'.format(
                value.replace('"', '%QUOTE') if value else None
            ) for value in self.record.values()
        )

        return """
        INSERT INTO library (
            author,
            title,
            journal,
            year,
            volume,
            number,
            pages,
            month,
            doi,
            issn,
            bibnote,
            note,
            path
        ) VALUES ({})
        """.format(values)
