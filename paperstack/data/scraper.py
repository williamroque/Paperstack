"Module in charge of web scraping."

import requests
from urllib.parse import quote_plus

import bibtexparser

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
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    """

    def __init__(self, record, config, messenger):
        self.record = record

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


class ADSScraper(Scraper):
    """Scraper for the NASA/Harvard Astrophysics Data System. We need an
    API key for this one, specified in the config under [ads]/key.
    """

    def get_headers(self):
        "Generate request headers."

        key = self.config.get('ads', 'key')

        if not key:
            self.messenger.send_error('Specify a valid API key to scrape ADS.')

        return {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }


    def get_metadata(self):
        """Get bibcode and abstract from DOI or title by communicating with
        ADS.
        """

        if 'bibcode' in self.record:
            bibcode = self.record['bibcode']
            identifier = f'bibcode:{bibcode}'
        elif 'doi' in self.record:
            doi = self.record['doi']
            identifier = f'doi:{doi}'
        elif 'title' in self.record:
            title = self.record['title']
            identifier = f'title:{title}'
        else:
            self.messenger.send_error('Bibcode, DOI, or title is needed to scrape with ADS.')

        identifier = quote_plus(identifier)
        url = f'https://api.adsabs.harvard.edu/v1/search/query?q={identifier}&fl=bibcode,abstract'

        try:
            response = requests.get(
                url,
                headers = self.get_headers(),
                timeout = float(self.config.get('ads', 'timeout'))
            )

            if not response.ok:
                raise requests.ConnectionError
        except requests.ConnectionError:
            self.messenger.send_error('Having trouble connecting to ADS.')
        except requests.Timeout:
            self.messenger.send_error('Request timed out while connecting to ADS.')

        data = response.json()['response']['docs']

        if len(data) == 0 or 'bibcode' not in data[0]:
            self.messenger.send_error('Could not find record on ADS.')

        metadata = {
            'bibcode': data[0]['bibcode']
        }

        if 'abstract' in data[0]:
            metadata['abstract'] = data[0]['abstract']

        return metadata


    def scrape(self):
        metadata = self.get_metadata()
        identifier = {'bibcode': [metadata['bibcode']]}

        try:
            response = requests.post(
                'https://api.adsabs.harvard.edu/v1/export/bibtex',
                headers = self.get_headers(),
                timeout = float(self.config.get('ads', 'timeout')),
                json = identifier
            )
        except requests.ConnectionError:
            self.messenger.send_error('Having trouble connecting to ADS.')
        except requests.Timeout:
            self.messenger.send_error('Request timed out while connecting to ADS.')

        data = bibtexparser.loads(
            response.json()['export']
        ).entries[0]

        entries = [
            ('record_type', 'ENTRYTYPE'),
            ('author', 'author'),
            ('title', 'title'),
            ('journal', 'journal'),
            ('year', 'year'),
            ('volume', 'volume'),
            ('number', 'number'),
            ('pages', 'pages'),
            ('month', 'month'),
            ('doi', 'doi'),
            ('issn', 'issn'),
            ('bibnote', 'adsnote'),
        ]

        record = {
            'bibcode': metadata['bibcode']
        }

        for record_key, data_key in entries:
            if data_key in data:
                record[record_key] = data[data_key]

        if 'abstract' in metadata:
            record['abstract'] = metadata['abstract']

        self.record = record


scraper_constructors = {
    'ads': ADSScraper
}
