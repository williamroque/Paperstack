"arXiv scraper."

import re
from xml.etree import ElementTree

from datetime import datetime

from urllib.parse import quote_plus

import requests

from paperstack.data.scraper import Scraper
from paperstack.filesystem.file import File
from paperstack.interface.util import clean_text


class ArXivScraper(Scraper):
    """Scraper for the arXiv database.
    """

    SUGGESTED_FIELDS = [
        ('arxiv', 'arXiv ID'),
        ('title', 'Title')
    ]

    def scrape(self):
        arxiv = None

        if 'arxiv' in self.record and self.record['arxiv']:
            arxiv = self.record['arxiv'].strip()

            id_match = re.search(r'([0-9]+\.?[0-9]+)([vV0-9]*)$', arxiv)

            if not id_match:
                self.messenger.send_error('Invalid arXiv ID.')

            arxiv = id_match.group(1)

            identifier = f'id:{arxiv}'
        elif 'title' in self.record:
            title = clean_text(self.record['title'])
            identifier = f'ti:{title}'
        else:
            self.messenger.send_error('arXiv ID or title is needed to scrape with arXiv.')

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

        results_count = int(tree.find(
            '{http://a9.com/-/spec/opensearch/1.1/}totalResults'
        ).text)

        if results_count == 0:
            self.messenger.send_error('No results found matching query.')

        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text
        abstract = abstract.strip().replace('\n', ' ').replace('  ', '')

        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        title = title.strip().replace('\n', ' ').replace('  ', '')

        doi_element = entry.find('{http://arxiv.org/schemas/atom}doi')
        doi = None

        if doi_element:
            doi = doi_element.text.strip()

        if not arxiv:
            id_match = re.search(
                r'[0-9vV]+\.?[0-9vV]+$',
                entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
            )

            if id_match:
                arxiv = id_match.group(0)


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
            'journal': 'arXiv e-prints',
            'year': str(date.year),
            'month': str(date.month),
            'doi': doi,
            'arxiv': arxiv
        }

        if comment is not None:
            record['bibnote'] = comment

        if 'path' in self.record:
            record['path'] = self.record['path']

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
            absolute_path = File(
                self.config.get('paths', 'data'), True
            ).join(save_path)

            with open(absolute_path, 'wb') as f:
                f.write(response.content)
        except:
            self.messenger.send_warning('Could not write PDF to data directory.')
            return

        self.record['path'] = str(save_path)
