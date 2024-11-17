"""Web crawler package.

A robust, parallel-processing web crawler with advanced link analysis capabilities.
"""

from .app import WebCrawlerFactory, WebCrawlerWorker
from .app.models import CrawlResult, PageData
from .utils import setup_logger, Config, write_results

__all__ = [
    'WebCrawlerFactory',
    'WebCrawlerWorker',
    'CrawlResult',
    'PageData',
    'setup_logger',
    'Config',
    'write_results',
]
