import asyncio
import logging
import threading
from queue import PriorityQueue
from typing import Dict, List, Tuple
from multiprocessing import cpu_count

from ..models import CrawlProcessResult, CrawlPageResult
from ...utils import Config
from .web_crawler_worker import WebCrawlerWorker


class WebCrawlerManager:
    """Manager class for coordinating web crawling operations."""
    
    def __init__(self, root_url: str, max_depth: int, logger: logging.Logger, n_jobs: int = -1):
        self.logger = logger
        self.max_depth = max_depth
        self.n_jobs = n_jobs
        self.root_url = root_url
        
        # Thread-safe queue for URL processing
        self.url_queue = PriorityQueue()
        # Thread-safe tracking of visited URLs
        self.visited_urls = set()
        self.visited_lock = threading.Lock()
        
        self.process_result = CrawlProcessResult(start_url=root_url)
        
        # Init web session configuration
        self.headers = {'User-Agent': Config.get_user_agent()}
        self.timeout = Config.get_timeout()

    def crawl(self) -> CrawlProcessResult:
        """Start the crawling process."""
        return asyncio.run(self._crawl_async())
        
    async def _crawl_async(self) -> CrawlProcessResult:
        self.logger.info(f"Starting crawl from {self.root_url} with max depth {self.max_depth}")
        
        with self.visited_lock:
            self.visited_urls.add(self.root_url)
            self.url_queue.put((1, self.root_url))
            
        batch_size = self._calc_batch_size()
        
        while not self.url_queue.empty() and self.url_queue.queue[0][0] <= self.max_depth:
            urls_with_depth = self._prepare_batch(batch_size)
            if not urls_with_depth:
                continue
            
            page_results = await self._process_batch(urls_with_depth)
            self._update_process_result(page_results)
            self.logger.info(self.process_result.format_progress(self.url_queue.qsize()))

        return self.process_result

    def _create_worker(self) -> WebCrawlerWorker:
        """Create a new worker instance."""
        return WebCrawlerWorker(self.headers, self.timeout, self.logger)

    def _prepare_batch(self, batch_size: int) -> List[Tuple[str, int]]:
        """Prepare a batch of URLs with their depths for processing.
        Returns a list of (url, depth) tuples in priority order."""
        urls_with_depth = []
        
        while len(urls_with_depth) < batch_size and not self.url_queue.empty():
            depth, url = self.url_queue.get()
            urls_with_depth.append((url, depth))
        
        return urls_with_depth

    async def _process_batch(self, urls_with_depth: List[Tuple[str, int]]) -> List[CrawlPageResult]:
        """Process a batch of URLs in parallel using asyncio."""
        worker = self._create_worker()
        tasks = [asyncio.create_task(worker.crawl_url(url, depth)) for url, depth in urls_with_depth]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def _update_process_result(self, page_results: List[CrawlPageResult]) -> None:
        """Update process results and queue new URLs."""
        for result in page_results:
            self.process_result.crawled_pages[result.url] = result
            if result.success:
                self.process_result.all_urls.update(set(result.links))
                next_depth = result.depth + 1
                if next_depth <= self.max_depth:
                    self._queue_new_urls(result.links, next_depth)

    def _queue_new_urls(self, new_urls: List[str], next_depth: int) -> None:
        """Queue new unvisited URLs for crawling. Thread-safe."""
        for new_url in new_urls:
            with self.visited_lock:
                if new_url not in self.visited_urls:
                    self.visited_urls.add(new_url)
                    self.url_queue.put((next_depth, new_url))

    def _calc_batch_size(self) -> int:
        """Calculate the optimal batch size for async operations."""
        n_workers = cpu_count() if self.n_jobs == -1 else self.n_jobs
        return max(Config.get_max_batch_size(), n_workers * 8)
