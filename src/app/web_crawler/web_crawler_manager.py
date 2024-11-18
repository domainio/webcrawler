from collections import defaultdict
import logging
import asyncio
from threading import Lock
from typing import List, Tuple
from datetime import datetime
from multiprocessing import cpu_count

from ...utils.config import Config
from .web_crawler_worker import WebCrawlerWorker
from ..models import CrawlProcessResult, CrawlPageResult

class WebCrawlerManager:
    """Manager class for coordinating web crawling operations."""
    
    def __init__(self, root_url: str, max_depth: int, logger: logging.Logger, n_jobs: int = -1):
        self.logger = logger
        self.max_depth = max_depth
        self.n_jobs = n_jobs
        self.visited_urls = set()
        self.visited_lock = Lock()
        self.process_result = CrawlProcessResult(start_url=root_url)
        self.root_url = root_url
        self.start_time = None
        
        # Init web session configuration
        self.headers = {'User-Agent': Config.get_user_agent()}
        self.timeout = Config.get_timeout()

    def create_worker(self) -> WebCrawlerWorker:
        """Create a new worker instance."""
        return WebCrawlerWorker(self.headers, self.timeout, self.logger)

    def prepare_batch(self, url_queue: List[Tuple[str, int]], batch_size: int) -> List[Tuple[List[str], int]]:
        """Prepare a batch of URLs at the same depth for processing. """
        if not url_queue:
            return [], 0
            
        urls_to_process = []
        current_depth = url_queue[0][1]
        
        while url_queue and url_queue[0][1] == current_depth and len(urls_to_process) < batch_size:
            url, depth = url_queue.pop(0)
            with self.visited_lock:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    urls_to_process.append(url)
                
        return urls_to_process, current_depth

    async def process_batch(self, urls: List[str], depth: int) -> List[CrawlPageResult]:
        """Process a batch of URLs in parallel."""
        if not urls:
            return []
            
        worker = self.create_worker()
        self.logger.info(f"Processing {len(urls)} URLs at depth {depth}")
        
        # Process URLs concurrently
        results = await asyncio.gather(
            *[worker.crawl_url(url, depth) for url in urls],
            return_exceptions=True
        )
        
        # Filter out exceptions and return valid results
        valid_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error processing {url}: {str(result)}")
                continue
            valid_results.append(result)
            
        successful = sum(1 for r in valid_results if r.success)
        self.logger.info(f"Batch completed: {successful}/{len(urls)} successful")
        return valid_results

    def calc_batch_size(self) -> int:
        """Calculate the optimal batch size for async operations."""
        n_workers = cpu_count() if self.n_jobs == -1 else self.n_jobs
        return max(Config.get_max_batch_size(), n_workers * 8)

    def log_progress(self, urls_processed: int, queue_size: int) -> None:
        """Log crawling progress."""
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        urls_per_second = urls_processed / elapsed_seconds if elapsed_seconds > 0 else 0
        
        self.logger.info(
            f"Progress: {urls_processed} URLs processed ({urls_per_second:.1f} URLs/sec), "
            f"{queue_size} URLs in queue"
        )

    def log_completion(self, urls_processed: int) -> None:
        """Log crawling completion stats."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        final_urls_per_second = urls_processed / total_time if total_time > 0 else 0
        
        self.logger.info(
            f"Crawl completed: {urls_processed} pages crawled in {total_time:.1f} seconds "
            f"({final_urls_per_second:.1f} URLs/sec)"
        )

    def store_page_result(self, page_result: CrawlPageResult) -> None:
        """Store a successful page crawl result."""
        self.process_result.crawled_pages[page_result.url] = page_result
        self.process_result.all_urls.update(page_result.links)

    def queue_new_urls(self, urls: List[str], next_depth: int, url_queue: List[Tuple[str, int]]) -> None:
        """Add new unvisited URLs to the crawl queue."""
        for url in urls:
            with self.visited_lock:
                if url not in self.visited_urls:
                    url_queue.append((url, next_depth))

    def update_results(self, page_results: List[CrawlPageResult], url_queue: List[Tuple[str, int]], depth: int) -> None:
        """Process successful crawl results and queue new URLs for crawling."""
        for page_result in page_results:
            if not page_result.success:
                continue
            
            # Store this page's results
            self.store_page_result(page_result)
            
            # Queue newly discovered URLs for next depth
            self.queue_new_urls(page_result.links, depth + 1, url_queue)
    
    async def crawl_async(self) -> CrawlProcessResult:
        """Execute the crawling process asynchronously."""
        self.logger.info(f"Starting crawl from {self.root_url} with max depth {self.max_depth}")
        self.start_time = datetime.now()
        
        url_queue = [(self.root_url, 1)]
        batch_size = self.calc_batch_size()
        urls_processed = 0
        
        while url_queue and url_queue[0][1] <= self.max_depth:
            # Get next batch of URLs at current depth
            urls, depth = self.prepare_batch(url_queue, batch_size)
            if not urls:
                continue
            
            # Process batch and update results
            page_results = await self.process_batch(urls, depth)
            self.update_results(page_results, url_queue, depth)
            
            # Log progress
            urls_processed += len(urls)
            self.log_progress(urls_processed, len(url_queue))
        
        # Finalize results
        self.process_result.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_completion(urls_processed)
        
        return self.process_result
        
    def crawl(self) -> CrawlProcessResult:
        """Execute the crawling process."""
        return asyncio.run(self.crawl_async())
