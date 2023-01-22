"Module in charge of web scraping."

from paperstack.data.record import record_constructors


class Scraper:
    """Superclass for web scrapers. Children will specialize in their
    respective databases.

    Parameters
    ----------
    record : dict
        Keep track of scraped information.
    record_type : str
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger

    Attributes
    ----------
    record : dict
        Keep track of scraped information.
    record_type : str
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    """

    def __init__(self, record, record_type, config, messenger):
        self.record = record
        self.record_type = record_type

        if self.record_type not in record_constructors:
            messenger.send_error('Invalid record type.')

        self.config = config
        self.messenger = messenger


    def scrape(self):
        """Use select `self.record` entries (e.g., DOI; will throw error if
        they are not present) to get more data. Populate `self.record` with
        scraped data.
        """

        raise NotImplementedError


    def create_record(self):
        """Create `Record` instance based on scraped data.

        Returns
        -------
        paperstack.data.record.Record
        """

        self.scrape()

        return record_constructors[self.record_type](
            self.record,
            self.config,
            self.messenger
        )


    def populate_record(self, record):
        """Populate `Record` instance using scraped data.
        """

        self.scrape()

        record.record = {**record.record, **self.record}
