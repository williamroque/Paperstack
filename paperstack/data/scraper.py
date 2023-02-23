"Module in charge of web scraping."


from paperstack.data.record import record_constructors


class Scraper:
    """Superclass for web scrapers. Children will specialize in their
    respective databases.

    Parameters
    ----------
    record : dict
        Keep track of scraped information.
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger

    Attributes
    ----------
    SUGGESTED_FIELDS : list
        Fields potentially needed to scrape information.
    record : dict
        Keep track of scraped information.
    pdf_url : str
        Keep track of PDF download url after scraping.
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    """

    SUGGESTED_FIELDS = []

    def __init__(self, record, config, messenger):
        self.record = record
        self.pdf_url = None

        self.config = config
        self.messenger = messenger


    @property
    def suggested_fields(self):
        "Get suggested fields."

        return self.__class__.SUGGESTED_FIELDS


    def scrape(self):
        """Use select `self.record` entries (e.g., DOI; will throw error if
        they are not present) to get more data. Populate `self.record` with
        scraped data.
        """

        raise NotImplementedError


    def download_pdf(self, save_path):
        """Download PDF from database using scraped `pdf_url` and save to
        specified path.

        Parameters
        ----------
        save_path : str
        """

        raise NotImplementedError


    def create_record(self):
        """Create `Record` instance based on scraped data.

        Returns
        -------
        paperstack.data.record.Record
        """

        self.scrape()

        if 'record_type' not in self.record:
            self.messenger.send_error('Record type must be specified to build record.')

        record_type = self.record['record_type']

        if record_type not in record_constructors:
            self.messenger.send_error('Invalid record type.')

        return record_constructors[record_type](
            self.record,
            self.config,
            self.messenger
        )


    def populate_record(self, record):
        """Populate `Record` instance using scraped data.
        """

        self.scrape()

        record.record = {**self.record, **record.record}
