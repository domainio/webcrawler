#!/usr/bin/env python3
from collections import defaultdict
import logging
from threading import Lock
from typing import List, Set, Dict, Tuple
from datetime import datetime
from joblib import Parallel, delayed
from tqdm import tqdm

from ...utils.config import Config
from .web_crawler_worker import WebCrawlerWorker
from ..models import CrawlProcessResult, CrawlPageResult

class WebCrawlerManager:
    """Manager class for coordinating web crawling operations."""
    
    def __init__(self, root_url: str, max_depth: int, logger: logging.Logger, n_jobs: int = -1):
        """Initialize the crawler manager.
        
        Args:
            root_url: Starting URL for crawling
            max_depth: Maximum depth to crawl
            logger: Logger instance
            n_jobs: Number of parallel jobs (-1 for all cores)
        """
        self.logger = logger
        self.max_depth = max_depth
        self.n_jobs = n_jobs
        self.visited_urls = set()
        self.visited_lock = Lock()
        self.crawl_session = CrawlProcessResult(start_url=root_url)
        
        # Create session configuration
        self.headers = {'User-Agent': Config.get_user_agent()}
        self.timeout = Config.get_timeout()
        
        # Initialize root URL
        worker = self.create_worker()
        self.root_url = worker.normalize_url(root_url)

    def create_worker(self) -> WebCrawlerWorker:
        """Create a new worker instance."""
        return WebCrawlerWorker(self.headers, self.timeout)

    def prepare_batch(self, queue: List[Tuple[str, int]], batch_size: int) -> List[Tuple[str, int]]:
        """Prepare a batch of URLs at the same depth for processing."""
        current_batch = []
        current_depth = queue[0][1]
        
        while queue and queue[0][1] == current_depth and len(current_batch) < batch_size:
            url, depth = queue.pop(0)
            with self.visited_lock:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    current_batch.append((url, depth))
                
        return current_batch

    def process_batch(self, urls_batch: List[Tuple[str, int]]) -> Tuple[Set[str], Dict[str, CrawlPageResult]]:
        """Process a batch of URLs in parallel."""
        worker = self.create_worker()
        
        results = Parallel(n_jobs=self.n_jobs)(
            delayed(worker.crawl_url)(url, depth) for url, depth in urls_batch
        )
        
        all_discovered_urls = set()
        crawled_pages = {}
        
        for result in results:
            all_discovered_urls.update(result.discovered_links)
            crawled_pages[result.url] = result
            
        return all_discovered_urls, crawled_pages

    def crawl(self) -> CrawlProcessResult:
        """Execute the crawling process.
        
        Returns:
            CrawlProcessResult containing all crawl data and metadata.
        """
        queue = [(self.root_url, 1)]
        batch_size = max(100, self.n_jobs * 2)
        
        with tqdm(desc=f"Crawling (max depth: {self.max_depth})") as pbar:
            while queue and queue[0][1] <= self.max_depth:
                current_batch = self.prepare_batch(queue, batch_size)
                if not current_batch:
                    continue
                
                new_urls, page_results = self.process_batch(current_batch)
                self.crawl_session.crawled_pages.update(page_results)
                self.crawl_session.all_discovered_urls.update(new_urls)
                
                # Add new URLs to queue and update progress
                current_depth = current_batch[0][1]
                for url in new_urls:
                    with self.visited_lock:
                        if url not in self.visited_urls:
                            queue.append((url, current_depth + 1))
                
                pbar.update(len(current_batch))
                pbar.set_description(
                    f"Depth: {current_depth}/{self.max_depth} "
                    f"Queue: {len(queue)} "
                    f"Crawled: {len(self.crawl_session.crawled_pages)}"
                )
        
        self.crawl_session.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.crawl_session