"""Web crawler package."""

__version__ = '0.1.0'

from .app import WebCrawlerManager, WebCrawlerWorker
from .utils import Config

__all__ = [
    'Config',
    'WebCrawlerManager',
    'WebCrawlerWorker',
]
