import os
import logging
from pathlib import Path
from environs import Env

env = Env()
env.read_env()

class Config:
    """Configuration class to manage environment variables."""
    
    CRAWL_RESULTS_DIR = env.str('CRAWL_RESULTS_DIR', './.crawls')
    SCRAPE_DIR = env.str('SCRAPE_DIR', './.scrape')
    USER_AGENT = env.str('WEB_PAGE_USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    REQUEST_TIMEOUT = env.int('HTTP_REQUEST_TIMEOUT', 10)
    LOG_LEVEL = env.log_level('LOG_LEVEL', logging.INFO)
    MAX_BATCH_SIZE = env.int('MAX_BATCH_SIZE', 100)
    HEADLESS_MODE = env.bool('BROWSER_HEADLESS', True)
    
    @classmethod
    def get_abs_path(cls, path: str) -> str:
        """Convert relative path to absolute path."""
        if path.startswith('./'):
            base_dir = Path(__file__).parent.parent.parent
            return str(base_dir / path[2:])
        return path
    
    @classmethod
    def get_results_dir(cls) -> str:
        return cls.get_abs_path(cls.CRAWL_RESULTS_DIR)
    
    @classmethod
    def get_scrape_dir(cls) -> str:
        return cls.get_abs_path(cls.SCRAPE_DIR)
    
    @classmethod
    def get_user_agent(cls) -> str:
        return cls.USER_AGENT
    
    @classmethod
    def get_timeout(cls) -> int:
        return cls.REQUEST_TIMEOUT
    
    @classmethod
    def get_log_level(cls) -> int:
        return cls.LOG_LEVEL
    
    @classmethod
    def get_max_batch_size(cls) -> int:
        return cls.MAX_BATCH_SIZE
    
    @classmethod
    def get_headless_mode(cls) -> bool:
        return cls.HEADLESS_MODE
