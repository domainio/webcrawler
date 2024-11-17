"""Web crawler module."""

from .web_crawler_worker import WebCrawlerWorker
from .web_crawler_manager import WebCrawlerManager

__all__ = [
    'WebCrawlerManager',
    'WebCrawlerWorker',
]
