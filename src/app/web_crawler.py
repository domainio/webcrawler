#!/usr/bin/env python3
import os
from collections import defaultdict
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import validators
from tqdm import tqdm
import logging
from ..utils.config import Config
from ..utils import io_file_writer

class WebCrawler:
    def __init__(self, root_url: str, max_depth: int, logger: logging.Logger):
        """Initialize the WebCrawler.
        
        Args:
            root_url (str): The URL to start crawling from
            max_depth (int): Maximum depth to crawl
            logger (logging.Logger): Logger instance for the crawler
        """
        self.logger = logger  # Set logger first since normalize_url uses it
        self.root_url = self.normalize_url(root_url)
        self.max_depth = max_depth
        self.visited_urls = set()
        self.results = defaultdict(dict)
        self.session = requests.Session()
        
        # Get configuration from environment
        self.session.headers.update({
            'User-Agent': Config.get_user_agent()
        })
        self.timeout = Config.get_timeout()
        
    def verify_url(self, url: str) -> tuple[str, bool]:
        """Verify URL works and return status."""
        try:
            response = requests.head(url, timeout=5)
            return url, response.status_code < 400
        except requests.RequestException:
            return url, False

    def normalize_url(self, url: str) -> str:
        """Normalize URL: verify existing scheme, or try HTTPS first, otherwise fallback to HTTP."""
        parsed = urlparse(url)
        
        # Handle URLs with scheme
        if parsed.scheme:
            if parsed.scheme not in ('http', 'https'):
                raise ValueError(f"Unsupported scheme: {parsed.scheme}")
            url, ok = self.verify_url(parsed._replace(fragment='').geturl())
            if not ok:
                raise ValueError(f"Failed to verify URL: {url}")
            return url
            
        # Try HTTPS then HTTP
        https_url, ok = self.verify_url(f"https://{url}")
        if ok:
            return https_url
        http_url, ok = self.verify_url(f"http://{url}")
        if ok:
            return http_url
        raise ValueError(f"Failed to verify URL: {url}")

    def get_domain(self, url):
        """Extract domain from URL."""
        return urlparse(url).netloc

    def is_same_domain(self, url1, url2):
        """Check if two URLs belong to the same domain."""
        return self.get_domain(url1) == self.get_domain(url2)

    def is_dynamic_link(self, tag):
        """Check if link might be dynamically added by JavaScript."""
        # Check for common JavaScript indicators
        if tag.get('onclick') or tag.get('onmouseover'):
            return True
        href = tag.get('href', '')
        return href.startswith('javascript:') or href.startswith('#!')

    def handle_relative_url(self, base_url, url):
        """Handle relative URLs."""
        return urljoin(base_url, url)
    
    def extract_links(self, html_content, base_url):
        """Extract and normalize all links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        same_domain_count = 0
        total_links = 0

        for tag in soup.find_all('a', href=True):
            if self.is_dynamic_link(tag):
                continue

            href = tag['href']
            if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue

            full_url = self.handle_relative_url(base_url,href)
            
            try:
                full_url = self.normalize_url(full_url)
            except ValueError:
                continue

            if validators.url(full_url):
                links.add(full_url)
                total_links += 1
                if self.is_same_domain(base_url, full_url):
                    same_domain_count += 1

        ratio = same_domain_count / total_links if total_links > 0 else 0
        return links, ratio

    def crawl_page(self, url, depth):
        """Crawl a single page and return its links and ratio."""
        if url in self.visited_urls:
            return set()

        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Check if content type is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return set()

            links, ratio = self.extract_links(response.text, url)
            
            # Store results with timestamp
            self.results[url] = {
                'depth': depth,
                'ratio': ratio,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return links

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            return set()

    def crawl(self) -> dict:
        """Main crawling method with progress bar."""
        queue = [(self.root_url, 0)]  # Start counting current depth from 0
        with tqdm(desc=f"Crawling (max depth: {self.max_depth})") as pbar:
            while queue:
                url, current_depth = queue.pop(0)
                
                if current_depth >= self.max_depth:  # Stop when we reach user-specified depth
                    continue
                    
                links = self.crawl_page(url, current_depth)
                pbar.update(1)
                pbar.set_description(
                    f"Depth: {current_depth}/{self.max_depth-1} "  # Show 0-based depth to user
                    f"(visited: {len(self.visited_urls)}, queue: {len(queue)})"
                )
                
                # Add new links to queue
                for link in links:
                    if link not in self.visited_urls:
                        queue.append((link, current_depth + 1))
        
        self.logger.info("Crawl completed.")
        return dict(self.results)
