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
        
        # Init web session configuration
        self.headers = {'User-Agent': Config.get_user_agent()}
        self.timeout = Config.get_timeout()

    def create_worker(self) -> WebCrawlerWorker:
        """Create a new worker instance."""
        return WebCrawlerWorker(self.headers, self.timeout, self.logger)

    def prepare_batch(self, url_queue: List[Tuple[str, int]], batch_size: int) -> List[Tuple[str, int]]:
        """Prepare a batch of URLs at the same depth for processing."""
        current_batch = []
        current_depth = url_queue[0][1]
        
        while url_queue and url_queue[0][1] == current_depth and len(current_batch) < batch_size:
            url, depth = url_queue.pop(0)
            with self.visited_lock:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    current_batch.append((url, depth))
                
        return current_batch

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
    
    async def crawl_async(self) -> CrawlProcessResult:
        """Execute the crawling process asynchronously."""
        self.logger.info(f"Starting crawl from {self.root_url} with max depth {self.max_depth}")
        start_time = datetime.now()
        
        url_queue = [(self.root_url, 1)]
        batch_size = self.calc_batch_size()
        urls_processed = 0
        
        while url_queue and url_queue[0][1] <= self.max_depth:
            current_batch = self.prepare_batch(url_queue, batch_size)
            if not current_batch:
                continue
                
            urls = [url for url, _ in current_batch]
            depth = current_batch[0][1]
            
            # Process batch and update results
            page_results = await self.process_batch(urls, depth)
            for page_result in page_results:
                if page_result.success:
                    self.process_result.crawled_pages[page_result.url] = page_result
                    self.process_result.all_discovered_urls.update(page_result.discovered_links)
                    
                    # Add new URLs to queue
                    for new_url in page_result.discovered_links:
                        with self.visited_lock:
                            if new_url not in self.visited_urls:
                                url_queue.append((new_url, depth + 1))
            
            # Update progress metrics
            urls_processed += len(current_batch)
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            urls_per_second = urls_processed / elapsed_seconds if elapsed_seconds > 0 else 0
            
            self.logger.info(
                f"Progress: {urls_processed} URLs processed ({urls_per_second:.1f} URLs/sec), "
                f"{len(url_queue)} URLs in queue"
            )
                        
        self.process_result.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        total_time = (datetime.now() - start_time).total_seconds()
        final_urls_per_second = urls_processed / total_time if total_time > 0 else 0
        
        self.logger.info(
            f"Crawl completed: {urls_processed} pages crawled in {total_time:.1f} seconds "
            f"({final_urls_per_second:.1f} URLs/sec)"
        )
        
        return self.process_result
        
    def crawl(self) -> CrawlProcessResult:
        """Execute the crawling process."""
        return asyncio.run(self.crawl_async())
