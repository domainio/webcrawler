import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Set, Tuple

from ..models import CrawlPageResult
from ...utils import validate_url, make_full_url, is_same_domain, normalize_url

class WebCrawlerWorker:
    """Worker class for crawling individual URLs asynchronously."""
    
    def __init__(self, headers: Dict[str, str], timeout: int, logger: logging.Logger):
        self.headers = headers
        self.raw_timeout = timeout
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.logger = logger
        
    def calc_page_rank(self, same_domain_links_count: int, total_links_count: int) -> float:
        """Calculate the rank of a page based on its same domain links vs total links."""
        return same_domain_links_count / total_links_count if total_links_count > 0 else 0
    
    async def extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract and normalize links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()

        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            try:
                full_url = make_full_url(base_url, href)
                if not validate_url(full_url):
                    continue
                    
                normalized_url = normalize_url(full_url, self.raw_timeout, self.headers)
                if normalized_url not in links:
                    links.add(normalized_url)
                        
            except Exception as e:
                self.logger.debug(f"Error processing link {href}: {str(e)}")
                continue

        return links

    def classify_links(self, links: Set[str], base_url: str) -> Tuple[int, int]:
        """Classify links as same-domain or external."""
        same_domain_links_count = sum(1 for link in links if is_same_domain(link, base_url))
        external_links_count = len(links) - same_domain_links_count
        
        total = same_domain_links_count + external_links_count
        if total != len(links):
            raise ValueError(f"Link classification mismatch: {total} classified vs {len(links)} total")
            
        return same_domain_links_count, external_links_count

    async def crawl_url(self, url: str, depth: int) -> CrawlPageResult:
        try:
            normalized_url = normalize_url(url, self.raw_timeout, self.headers)
            result = CrawlPageResult(
                url=normalized_url,
                depth=depth,
                discovered_links=[],
                same_domain_links_count=0,
                external_links_count=0,
                ratio=0.0,
                success=False
            )
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(normalized_url, allow_redirects=True) as response:
                    if response.status != 200:
                        return result
                        
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        return result
                        
                    content = await response.text()
                    
                    links = await self.extract_links(content, normalized_url)
                    same_domain_links_count, external_links_count = self.classify_links(links, normalized_url)
                    
                    result.discovered_links = list(links)
                    result.same_domain_links_count = same_domain_links_count
                    result.external_links_count = external_links_count
                    result.ratio = self.calc_page_rank(same_domain_links_count, len(links))
                    result.success = True
                    
                    self.logger.debug(f"Successfully crawled {normalized_url}")
                    
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            result = CrawlPageResult(
                url=url,
                depth=depth,
                discovered_links=[],
                same_domain_links_count=0,
                external_links_count=0,
                ratio=0.0,
                success=False,
                error=str(e)
            )
            
        return result
