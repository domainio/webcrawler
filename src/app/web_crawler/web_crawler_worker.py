#!/usr/bin/env python3
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import validators
from typing import Set, Tuple

from ..models import CrawlPageResult

class WebCrawlerWorker:
    """Worker class for crawling individual URLs."""
    
    def __init__(self, headers: dict, timeout: int):
        """Initialize the crawler worker.
        
        Args:
            headers: HTTP headers to use for requests
            timeout: Request timeout in seconds
        """
        self.headers = headers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(headers)

    def normalize_url(self, url: str) -> str:
        """Normalize URL with scheme."""
        parsed = urlparse(url)
        if parsed.scheme:
            return url
            
        # Try HTTPS first, then HTTP
        for scheme in ['https://', 'http://']:
            try:
                full_url = f"{scheme}{url}"
                response = requests.head(full_url, timeout=5)
                if response.status_code < 400:
                    return full_url
            except requests.RequestException:
                continue
                
        raise ValueError(f"Failed to verify URL: {url}")

    def extract_links(self, html_content: str, base_url: str) -> Tuple[Set[str], float]:
        """Extract and analyze links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        total_links = 0
        same_domain_count = 0
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            try:
                full_url = urljoin(base_url, href)
                if not validators.url(full_url):
                    continue
                
                links.add(full_url)
                total_links += 1
                
                if urlparse(full_url).netloc == base_domain:
                    same_domain_count += 1
            except Exception:
                continue

        ratio = same_domain_count / total_links if total_links > 0 else 0
        return links, ratio

    def crawl_url(self, url: str, depth: int) -> CrawlPageResult:
        """Crawl a single URL and return results"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return CrawlPageResult(
                    url=url,
                    depth=depth,
                    ratio=0.0,
                    success=False,
                    error="Not an HTML page"
                )

            links, ratio = self.extract_links(response.text, url)
            
            return CrawlPageResult(
                url=url,
                discovered_links=links,
                depth=depth,
                ratio=ratio,
                success=True
            )

        except requests.RequestException as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            return CrawlPageResult(
                url=url,
                depth=depth,
                ratio=0.0,
                success=False,
                error=str(e)
            )
