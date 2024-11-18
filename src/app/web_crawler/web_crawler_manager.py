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
        """Prepare a batch of URLs at the same depth for processing."""
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
        worker = self.create_worker()
        self.logger.info(f"Processing {len(urls)} URLs at depth {depth}")
        
        results = await asyncio.gather(
            *[worker.crawl_url(url, depth) for url in urls],
            return_exceptions=True
        )
        
        self.logger.info(f"Batch completed: processed {len(urls)} URLs")
        return results

    def calc_batch_size(self) -> int:
        """Calculate the optimal batch size for async operations."""
        n_workers = cpu_count() if self.n_jobs == -1 else self.n_jobs
        return max(Config.get_max_batch_size(), n_workers * 8)

    async def crawl_async(self) -> CrawlProcessResult:
        """Execute the crawling process asynchronously."""
        self.logger.info(f"Starting crawl from {self.root_url} with max depth {self.max_depth}")
        self.start_time = datetime.now()
        
        url_queue = [(self.root_url, 1)]
        batch_size = self.calc_batch_size()
        urls_processed = 0
        
        while url_queue and url_queue[0][1] <= self.max_depth:
            urls, depth = self.prepare_batch(url_queue, batch_size)
            if not urls:
                continue
            
            page_results = await self.process_batch(urls, depth)
            
            # Update results and queue new URLs
            for result in page_results:
                if not isinstance(result, Exception) and result.success:
                    self.process_result.crawled_pages[result.url] = result
                    self.process_result.all_urls.update(result.links)
                    
                    # Queue new URLs for next depth
                    for new_url in result.links:
                        with self.visited_lock:
                            if new_url not in self.visited_urls:
                                url_queue.append((new_url, depth + 1))
            
            urls_processed += len(urls)
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
            urls_per_second = urls_processed / elapsed_seconds if elapsed_seconds > 0 else 0
            self.logger.info(
                f"Progress: {urls_processed} URLs processed ({urls_per_second:.1f} URLs/sec), "
                f"{len(url_queue)} URLs in queue"
            )
        
        # Finalize results
        self.process_result.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_time = (datetime.now() - self.start_time).total_seconds()
        final_urls_per_second = urls_processed / total_time if total_time > 0 else 0
        
        self.logger.info(
            f"Crawl completed: {urls_processed} pages crawled in {total_time:.1f} seconds "
            f"({final_urls_per_second:.1f} URLs/sec)"
        )
        
        return self.process_result

    def crawl(self) -> CrawlProcessResult:
        """Execute the crawling process."""
        return asyncio.run(self.crawl_async())
