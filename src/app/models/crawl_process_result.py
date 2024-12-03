from typing import Dict, Set
from datetime import datetime
from pydantic import BaseModel, Field, validator
import requests

from ...utils.url_utils import validate_url, normalize_url
from ...utils.config import Config
from .crawl_page_result import CrawlPageResult

class CrawlProcessResult(BaseModel):
    """Result of a complete crawl process."""
    
    root_url: str = Field(description="Starting URL for the crawl")
    start_time: str = Field(
        default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        description="Timestamp when the crawl started"
    )
    end_time: str = Field(
        default="",
        description="Timestamp when the crawl completed"
    )
    max_depth_reached: int = Field(
        default=0,
        description="Maximum depth reached during crawl"
    )
    crawled_pages: Dict[str, CrawlPageResult] = Field(
        default_factory=dict,
        description="Dictionary mapping URLs to their crawl results"
    )
    all_urls: Set[str] = Field(
        default_factory=set,
        description="Set of all unique URLs discovered during the entire crawl"
    )

    @validator('root_url')
    def validate_and_normalize_url(cls, v):
        """Validate and normalize the root URL."""
        try:
            # First normalize the URL
            normalized_url = normalize_url(v, Config.get_timeout(), {'User-Agent': Config.get_user_agent()})
            
            # Then validate the normalized URL
            if not validate_url(normalized_url):
                raise ValueError(f"Invalid URL format: {normalized_url}")
                
            return normalized_url
        except Exception as e:
            raise ValueError(f"Could not access URL {v}: {str(e)}")

    @property
    def elapsed_seconds(self) -> float:
        """Calculate elapsed time in seconds."""
        if not self.end_time:
            current = datetime.now()
        else:
            current = datetime.strptime(self.end_time, '%Y-%m-%d %H:%M:%S')
        start = datetime.strptime(self.start_time, '%Y-%m-%d %H:%M:%S')
        return (current - start).total_seconds()
    
    @property
    def urls_per_second(self) -> float:
        """Calculate URLs processed per second."""
        return len(self.crawled_pages) / (self.elapsed_seconds or 1)

    def format_progress(self, queue_size: int) -> str:
        """Format progress message."""
        return (
            f"Progress: {len(self.crawled_pages):,d} URLs processed "
            f"({self.urls_per_second:.1f} URLs/sec), "
            f"{queue_size:,d} URLs in queue"
        )

    def format_completion(self) -> str:
        """Format completion message."""
        return (
            f"Crawl completed in {self.elapsed_seconds:.1f} seconds:\n"
            f"- Processed: {len(self.crawled_pages):,d} URLs\n"
            f"- Discovered: {len(self.all_urls):,d} total URLs\n"
            f"- Max depth reached: {self.max_depth_reached}\n"
            f"- Speed: {self.urls_per_second:.1f} URLs/sec\n"
            f"- Start time: {self.start_time}\n"
            f"- End time: {self.end_time}"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "root_url": "https://example.com",
                "crawled_pages": {
                    "https://example.com": {
                        "url": "https://example.com",
                        "links": {
                            "https://example.com/about",
                            "https://example.com/products"
                        },
                        "depth": 0,
                        "ratio": 0.75,
                        "timestamp": "2024-02-14 12:00:00",
                        "success": True,
                        "error": ""
                    }
                },
                "all_urls": {
                    "https://example.com",
                    "https://example.com/about",
                    "https://example.com/products"
                },
                "start_time": "2024-02-14 12:00:00",
                "end_time": "2024-02-14 12:01:00",
                "max_depth_reached": 1
            }
        }
