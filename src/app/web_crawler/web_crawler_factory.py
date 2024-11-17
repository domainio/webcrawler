#!/usr/bin/env python3
from collections import defaultdict
import logging
from threading import Lock
from typing import List, Set, Dict, Tuple
from joblib import Parallel, delayed
from tqdm import tqdm

from ...utils.config import Config
from .web_crawler_worker import WebCrawlerWorker

class WebCrawlerFactory:
    """Factory class for managing web crawling operations."""
    
    def __init__(self, root_url: str, max_depth: int, logger: logging.Logger, n_jobs: int = -1):
        """Initialize the crawler factory.
        
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
        self.results = defaultdict(dict)
        
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

    def process_batch(self, urls_batch: List[Tuple[str, int]]) -> Tuple[Set[str], Dict[str, dict]]:
        """Process a batch of URLs in parallel."""
        worker = self.create_worker()
        
        results = Parallel(n_jobs=self.n_jobs)(
            delayed(worker.crawl_url)(url, depth) for url, depth in urls_batch
        )
        
        all_links = set()
        batch_results = {}
        
        for result in results:
            all_links.update(result.links)
            batch_results.update(result.data)
            
        return all_links, batch_results

    def crawl(self) -> dict:
        """Execute the crawling process.
        
        Returns:
            Dictionary containing crawl results for each URL.
        """
        queue = [(self.root_url, 1)]
        batch_size = max(100, self.n_jobs * 2)
        
        with tqdm(desc=f"Crawling (max depth: {self.max_depth})") as pbar:
            while queue and queue[0][1] <= self.max_depth:
                current_batch = self.prepare_batch(queue, batch_size)
                if not current_batch:
                    continue
                
                new_links, batch_results = self.process_batch(current_batch)
                self.results.update(batch_results)
                
                # Add new URLs to queue and update progress
                current_depth = current_batch[0][1]
                for link in new_links:
                    with self.visited_lock:
                        if link not in self.visited_urls:
                            queue.append((link, current_depth + 1))
                
                pbar.update(len(current_batch))
                pbar.set_description(
                    f"Depth: {current_depth}/{self.max_depth} "
                    f"(visited: {len(self.visited_urls)}, queue: {len(queue)})"
                )
        
        self.logger.info("Crawl completed.")
        return dict(self.results)
