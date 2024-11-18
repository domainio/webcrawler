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

    def crawl(self) -> CrawlProcessResult:
        return asyncio.run(self._crawl_async())
        
    async def _crawl_async(self) -> CrawlProcessResult:
        self.logger.info(f"Starting crawl from {self.root_url} with max depth {self.max_depth}")
        
        url_queue = [(self.root_url, 1)]
        batch_size = self._calc_batch_size()
        
        while url_queue and url_queue[0][1] <= self.max_depth:
            urls, depth = self._prepare_batch(url_queue, batch_size)
            if not urls:
                continue
            
            page_results = await self._process_batch(urls, depth)
            self._update_process_result(page_results, depth, url_queue)
            self.logger.info(self.process_result.format_progress(len(url_queue)))
        
        # Finalize results
        self.process_result.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(self.process_result.format_completion())
        
        return self.process_result
    
    def _create_worker(self) -> WebCrawlerWorker:
        """Create a new worker instance."""
        return WebCrawlerWorker(self.headers, self.timeout, self.logger)

    def _prepare_batch(self, url_queue: List[Tuple[str, int]], batch_size: int) -> List[Tuple[List[str], int]]:
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

    async def _process_batch(self, urls: List[str], depth: int) -> List[CrawlPageResult]:
        """Process a batch of URLs in parallel."""
        worker = self._create_worker()
        self.logger.info(f"Processing {len(urls)} URLs at depth {depth}")
        
        results = await asyncio.gather(
            *[worker.crawl_url(url, depth) for url in urls],
            return_exceptions=True
        )
        
        self.logger.info(f"Batch completed: processed {len(urls)} URLs")
        return results

    def _update_process_result(self, page_results: List[CrawlPageResult], depth: int, url_queue: List[Tuple[str, int]]) -> None:
        """Update process results and queue new URLs."""
        for result in page_results:
            if not isinstance(result, Exception) and result.success:
                self.process_result.crawled_pages[result.url] = result
                self.process_result.all_urls.update(result.links)
                self._queue_new_urls(result, depth, url_queue)

    def _queue_new_urls(self, result: CrawlPageResult, depth: int, url_queue: List[Tuple[str, int]]) -> None:
        """Queue new unvisited URLs for crawling."""
        for new_url in result.links:
            with self.visited_lock:
                if new_url not in self.visited_urls:
                    url_queue.append((new_url, depth + 1))

    def _calc_batch_size(self) -> int:
        """Calculate the optimal batch size for async operations."""
        n_workers = cpu_count() if self.n_jobs == -1 else self.n_jobs
        return max(Config.get_max_batch_size(), n_workers * 8)
