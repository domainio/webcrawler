"""Web crawler components.

Contains the main crawler factory and worker implementations.
"""

from .web_crawler_factory import WebCrawlerFactory
from .web_crawler_worker import WebCrawlerWorker

__all__ = [
    'WebCrawlerFactory',
    'WebCrawlerWorker',
]
