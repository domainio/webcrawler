import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class to manage environment variables."""
    
    @staticmethod
    def get_results_dir() -> str:
        """Get the directory for storing crawl results."""
        results_dir = os.getenv('CRAWL_RESULTS_DIR', './.crawls')
        # Convert relative path to absolute path
        if results_dir.startswith('./'):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            relative_path = results_dir[2:]  # Remove './' but keep any other dots
            return os.path.join(base_dir, relative_path)
        return results_dir

    @staticmethod
    def get_user_agent() -> str:
        """Get the User-Agent string for HTTP requests."""
        return os.getenv('USER_AGENT', 'Mozilla/5.0 (compatible; PythonCrawler/1.0; +http://example.com)')

    @staticmethod
    def get_timeout() -> int:
        """Get the request timeout in seconds."""
        return int(os.getenv('REQUEST_TIMEOUT', '10'))

    @staticmethod
    def get_log_level() -> int:
        """Get the logging level from environment or default to INFO."""
        try:
            return getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
        except AttributeError:
            return logging.INFO
