import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Set, Tuple
from urllib.parse import urlparse
from datetime import datetime

from ..models import CrawlPageResult
from ...utils import validate_url, make_full_url, is_same_domain, normalize_url

class WebCrawlerWorker:
    """Worker class for crawling individual URLs asynchronously."""
    
    def __init__(self, headers: Dict[str, str], timeout: int, logger: logging.Logger):
        self.headers = headers
        self.raw_timeout = timeout
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.logger = logger
        
    def _calc_page_rank(self, same_domain_links_count: int, total_links_count: int) -> float:
        """Calculate the rank of a page based on its same domain links vs total links."""
        return same_domain_links_count / total_links_count if total_links_count > 0 else 0
    
    async def _extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract and normalize links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()

        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue
            full_url = make_full_url(base_url, href)
            links.add(full_url)

        return links

    def _classify_links(self, links: Set[str], base_url: str) -> Tuple[int, int]:
        """Classify links as same-domain or external."""
        same_domain_links_count = sum(1 for link in links if is_same_domain(link, base_url))
        external_links_count = len(links) - same_domain_links_count
        
        total = same_domain_links_count + external_links_count
        if total != len(links):
            raise ValueError(f"Link classification mismatch: {total} classified vs {len(links)} total")
            
        return same_domain_links_count, external_links_count

    async def crawl_url(self, url: str, depth: int) -> CrawlPageResult:
        """Crawl a single URL and return the results."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=self.timeout) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
                    links = await self._extract_links(content, url)
                    same_domain_links_count, external_links_count = self._classify_links(links, url)
                    
                    result = CrawlPageResult(
                        url=url,
                        depth=depth,
                        success=True,
                        error=None,
                        links=list(links),
                        same_domain_links_count=same_domain_links_count,
                        external_links_count=external_links_count,
                        ratio=same_domain_links_count / len(links) if links else 0,
                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    self.logger.debug(f"Successfully crawled {url}")
                    return result
                    
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            return CrawlPageResult(
                url=url,
                depth=depth,
                success=False,
                error=str(e),
                links=[],
                same_domain_links_count=0,
                external_links_count=0,
                ratio=0,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
