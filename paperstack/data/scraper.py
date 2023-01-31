"Module in charge of web scraping."

from urllib.parse import quote_plus
from xml.etree import ElementTree

from datetime import datetime

import requests

import bibtexparser

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
    record : dict
        Keep track of scraped information.
    pdf_url : str
        Keep track of PDF download url after scraping.
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.Messenger
    """

    def __init__(self, record, config, messenger):
        self.record = record
        self.pdf_url = None

        self.config = config
        self.messenger = messenger


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

        self.pdf_url = 'https://ui.adsabs.harvard.edu/link_gateway/{}/'.format(
            metadata['bibcode']
        )

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


    def attempt_get(self, url):
        """Attempt to get URL.

        Parameters
        ----------
        url : str
        """

        try:
            response = requests.get(
                url,
                timeout = float(self.config.get('ads', 'timeout')),
            )
        except requests.ConnectionError:
            self.messenger.send_warning('Having trouble connecting to ADS.')
        except requests.Timeout:
            self.messenger.send_warning('Request timed out while connecting to ADS.')

        return response


    def download_pdf(self, save_path):
        if not self.pdf_url:
            self.messenger.send_warning('Not enough information to download PDF.')
            return

        response = self.attempt_get(self.pdf_url + 'PUB_PDF')

        if not response or not response.ok:
            response = self.attempt_get(self.pdf_url + 'EPRINT_PDF')

        if not response or not response.ok:
            return

        try:
            with open(save_path, 'wb') as f:
                f.write(response.content)
        except:
            self.messenger.send_warning('Could not write PDF to data directory.')
            return

        self.record['path'] = str(save_path)


class ArXivScraper(Scraper):
    """Scraper for the arXiv database.
    """

    def scrape(self):
        if 'arxiv' in self.record:
            arxiv = self.record['arxiv']
            identifier = f'id:{arxiv}'
        elif 'title' in self.record:
            title = self.record['title']
            identifier = f'ti:{title}'
        else:
            self.messenger.send_error('ArXiv ID or title is needed to scrape with arXiv.')

        identifier = quote_plus(identifier)
        url = f'http://export.arxiv.org/api/query?search_query={identifier}&start=0&max_results=1'

        try:
            response = requests.get(
                url,
                timeout = float(self.config.get('arxiv', 'timeout')),
                headers = {'Content-Type': 'application/json'}
            )
        except requests.ConnectionError:
            self.messenger.send_error('Having trouble connecting to arXiv.')
        except requests.Timeout:
            self.messenger.send_error('Request timed out while connecting to arXiv.')

        tree = ElementTree.fromstring(response.content)
        entry = tree[-1]

        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text
        abstract = abstract.strip().replace('\n', ' ').replace('  ', '')

        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        title = title.strip().replace('\n', ' ').replace('  ', '')

        doi = entry.find('{http://arxiv.org/schemas/atom}doi').text.strip()

        date = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')

        comment_tag = entry.find('{http://arxiv.org/schemas/atom}comment')
        comment = None

        if comment_tag is not None:
            comment = comment_tag.text.strip().replace('\n', ' ').replace('  ', '')

        authors = []

        for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
            authors.append(
                author.find('{http://www.w3.org/2005/Atom}name').text
            )

        authors = ' and '.join(authors)

        for child in entry:
            if 'title' in child.attrib and child.attrib['title'] == 'pdf':
                if 'href' in child.attrib:
                    self.pdf_url = child.attrib['href']
                    break

        record = {
            'record_type': 'article',
            'author': authors,
            'title': title,
            'journal': 'arXiv',
            'year': str(date.year),
            'month': str(date.month),
            'doi': doi
        }

        if comment is not None:
            record['bibnote'] = comment

        self.record = record


    def download_pdf(self, save_path):
        if not self.pdf_url:
            self.messenger.send_warning('Could not download PDF.')
            return

        try:
            response = requests.get(
                self.pdf_url,
                timeout = float(self.config.get('arxiv', 'timeout')),
            )
        except requests.ConnectionError:
            self.messenger.send_warning('Having trouble connecting to arXiv.')
            return
        except requests.Timeout:
            self.messenger.send_warning('Request timed out while connecting to arXiv.')
            return

        try:
            with open(save_path, 'wb') as f:
                f.write(response.content)
        except:
            self.messenger.send_warning('Could not write PDF to data directory.')
            return

        self.record['path'] = str(save_path)


scraper_constructors = {
    'ads': ADSScraper,
    'arxiv': ArXivScraper
}
