"Re-export scrapers."

from paperstack.data.scrapers.ads import ADSScraper
from paperstack.data.scrapers.arxiv import ArXivScraper
from paperstack.data.scrapers.mnras import MNRASScraper


scraper_constructors = {
    'ads': ADSScraper,
    'arxiv': ArXivScraper,
    'mnras': MNRASScraper
}
