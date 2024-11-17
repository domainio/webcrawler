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
        
    def calc_page_rank(self, same_domain_count: int, total_links: int) -> float:
        """Calculate the rank of a page based on its same domain links vs total links."""
        return same_domain_count / total_links if total_links > 0 else 0
    
    async def extract_links(self, html_content: str, base_url: str) -> tuple[set[str], float]:
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
                    
                normalized_url = normalize_url(full_url, self.raw_timeout, self.headers)
                if normalized_url not in links:
                    links.add(normalized_url)
                    total_links += 1
                    if is_same_domain(normalized_url, base_url):
                        same_domain_count += 1
                        
            except Exception as e:
                self.logger.debug(f"Error processing link {href}: {str(e)}")
                continue

        ratio = self.calc_page_rank(same_domain_count, total_links)
        return links, ratio

    async def crawl_url(self, url: str, depth: int) -> CrawlPageResult:
        try:
            normalized_url = normalize_url(url, self.raw_timeout, self.headers)
            result = CrawlPageResult(
                url=normalized_url,
                depth=depth,
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
                    links, ratio = await self.extract_links(content, normalized_url)
                    
                    result.discovered_links = links
                    result.ratio = ratio
                    result.success = True
                    self.logger.debug(f"Successfully crawled {normalized_url}")
                    
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            result = CrawlPageResult(
                url=url,
                depth=depth,
                ratio=0.0,
                success=False,
                error=str(e)
            )
            
        return result
