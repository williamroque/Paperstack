"MNRAS scraper."

import re
import datetime

from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from paperstack.data.scraper import Scraper
from paperstack.filesystem.file import File


class MNRASScraper(Scraper):
    """Scraper for the NASA/Harvard Astrophysics Data System. We need an
    API key for this one, specified in the config under [mnras]/key.
    """

    SUGGESTED_FIELDS = [
        ('url', 'URL'),
        ('doi', 'DOI')
    ]


    def scrape(self):
        if 'url' in self.record and self.record['url']:
            url = self.record['url']
        elif 'doi' in self.record and self.record['doi']:
            url = self.record['doi']

            if not re.match('https?', url):
                url = f'https://www.doi.org/{url}'
        else:
            self.messenger.send_error('URL or DOI is needed to scrape with MNRAS.')

        try:
            response = requests.get(
                url,
                headers = {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600',
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
                },
                timeout = float(self.config.get('mnras', 'timeout'))
            )

            if not response.ok:
                raise requests.ConnectionError
        except requests.ConnectionError:
            self.messenger.send_error('Having trouble connecting to MNRAS.')
        except requests.Timeout:
            self.messenger.send_error('Request timed out while connecting to MNRAS.')

        url = response.url

        soup = BeautifulSoup(response.content, 'html.parser')

        try:
            author = soup.find('div', {'class': 'at-ArticleAuthors'})
            author = author.find_all('a', {'class': 'linked-name'})
            author = [a.text.strip() for a in author]
            author = ' and '.join(author)

            title = soup.find(
                'h1', {'class': 'at-articleTitle'}
            ).text.strip()

            date = soup.find('div', {'class': 'citation-date'})
            date = datetime.datetime.strptime(
                date.text, '%d %B %Y'
            )

            citation = soup.find('div', {'class': 'ww-citation-primary'})

            volume, issue, pages, doi = re.search(
                'Volume (\d+), Issue (\d+).*Pages (.*), (.*)',
                citation.text
            ).groups()

            doi = re.search(
                r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b',
                doi
            ).group()
        except:
            self.messenger.send_error('Cannot extract all necessary information from MNRAS. May have reached CAPTCHA.')

        try:
            self.pdf_url = urljoin(
                url,
                soup.find('a', {'class': 'article-pdfLink'})['href']
            )
        except:
            pass

        record = {
            'record_type': 'article',
            'author': author,
            'title': title,
            'journal': 'Monthly Notices of the Royal Astronomical Society',
            'year': str(date.year),
            'month': date.strftime('%B'),
            'volume': volume,
            'number': issue,
            'pages': pages,
            'doi': doi
        }

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
                headers = {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600',
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
                },
                timeout = float(self.config.get('mnras', 'timeout'))
            )

            return response
        except requests.ConnectionError:
            self.messenger.send_warning('Having trouble connecting to MNRAS.')
        except requests.Timeout:
            self.messenger.send_warning('Request timed out while connecting to MNRAS.')


    def download_pdf(self, save_path):
        if not self.pdf_url:
            self.messenger.send_warning('Not enough information to download PDF.')
            return

        response = self.attempt_get(self.pdf_url)

        if not response or not response.ok:
            self.messenger.send_warning('Could not retrieve PDF.')
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
