import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from typing import Set, Tuple, Dict

from ..models import CrawlPageResult
from ...utils import validate_url, normalize_url, make_full_url, is_same_domain

class WebCrawlerWorker:
    """Worker class for crawling individual URLs."""
    
    def __init__(self, headers: Dict[str, str], timeout: int, logger: logging.Logger):
        """Initialize the crawler worker.
        
        Args:
            headers: HTTP headers to use for requests
            timeout: Request timeout in seconds
            logger: Logger instance
        """
        self.headers = headers
        self.timeout = timeout
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(headers)

    def calc_page_rank(self, same_domain_count: int, total_links: int) -> float:
        """Calculate the rank of a page based on its same domain linkes vs total links"""
        return same_domain_count / total_links if total_links > 0 else 0
    
    def extract_links(self, html_content: str, base_url: str) -> Tuple[Set[str], float]:
        """Extract and analyze links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        total_links = 0
        same_domain_count = 0

        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            try:
                full_url = make_full_url(base_url, href)
                if not validate_url(full_url):
                    continue
                    
                normalized_url = normalize_url(full_url, self.timeout, self.headers)
                if normalized_url not in links:
                    links.add(normalized_url)
                    total_links += 1
                    
                    if is_same_domain(normalized_url, base_url):
                        same_domain_count += 1
            except Exception:
                continue

        ratio = self.calc_page_rank(same_domain_count, total_links)
        return links, ratio

    def crawl_url(self, url: str, depth: int) -> CrawlPageResult:
        """Crawl a single URL and return results"""
        try:
            normalized_url = normalize_url(url, self.timeout, self.headers)
            
            response = self.session.get(normalized_url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return CrawlPageResult(
                    url=normalized_url,
                    depth=depth,
                    ratio=0.0,
                    success=False,
                    error="Not an HTML page"
                )

            links, ratio = self.extract_links(response.text, normalized_url)
            
            return CrawlPageResult(
                url=normalized_url,
                discovered_links=links,
                depth=depth,
                ratio=ratio,
                success=True
            )

        except requests.RequestException as e:
            return CrawlPageResult(
                url=url,
                depth=depth,
                ratio=0.0,
                success=False,
                error=str(e)
            )
