"ADS scraper."

from urllib.parse import quote_plus

import re

import requests
import bibtexparser

from paperstack.data.scraper import Scraper
from paperstack.filesystem.file import File
from paperstack.interface.util import clean_text

from paperstack.data.constants import ADS_MACROS


class ADSScraper(Scraper):
    """Scraper for the NASA/Harvard Astrophysics Data System. We need an
    API key for this one, specified in the config under [ads]/key.
    """

    SUGGESTED_FIELDS = [
        ('bibcode', 'Bibcode'),
        ('doi', 'DOI'),
        ('title', 'Title')
    ]

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

        if 'bibcode' in self.record and self.record['bibcode']:
            bibcode = self.record['bibcode']
            identifier = f'bibcode:"{bibcode}"'
        elif 'doi' in self.record and self.record['doi']:
            doi = self.record['doi']
            identifier = f'doi:"{doi}"'
        elif 'title' in self.record and self.record['title']:
            title = clean_text(self.record['title'])
            identifier = f'title:"{title}"'
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

        if 'journal' in record:
            for macro, expansion in ADS_MACROS:
                if macro in record['journal']:
                    record['journal'] = re.sub(
                        f'^\\s*\\{macro}\\s*$', expansion, record['journal']
                    )
                    break

        if 'abstract' in metadata:
            record['abstract'] = metadata['abstract']

        if 'path' in self.record:
            record['path'] = self.record['path']

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

            return response
        except requests.ConnectionError:
            self.messenger.send_warning('Having trouble connecting to ADS.')
        except requests.Timeout:
            self.messenger.send_warning('Request timed out while connecting to ADS.')


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
            absolute_path = File(
                self.config.get('paths', 'data'), True
            ).join(save_path)

            with open(absolute_path, 'wb') as f:
                f.write(response.content)
        except:
            self.messenger.send_warning('Could not write PDF to data directory.')
            return

        self.record['path'] = str(save_path)
