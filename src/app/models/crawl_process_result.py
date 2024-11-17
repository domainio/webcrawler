from typing import Dict, Set
from datetime import datetime
from pydantic import BaseModel, Field, validator
import requests

from ...utils.url_utils import validate_url, normalize_url
from ...utils.config import Config
from .crawl_page_result import CrawlPageResult

class CrawlProcessResult(BaseModel):
    """Result of a complete crawl process."""
    
    start_url: str = Field(description="Starting URL for the crawl")
    start_time: str = Field(
        default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        description="Timestamp when the crawl started"
    )
    end_time: str = Field(
        default="",
        description="Timestamp when the crawl completed"
    )
    crawled_pages: Dict[str, CrawlPageResult] = Field(
        default_factory=dict,
        description="Dictionary mapping URLs to their crawl results"
    )
    all_discovered_urls: Set[str] = Field(
        default_factory=set,
        description="Set of all unique URLs discovered during the entire crawl"
    )

    @validator('start_url')
    def validate_and_normalize_url(cls, v):
        """Validate and normalize the start URL."""
        try:
            # First normalize the URL
            normalized_url = normalize_url(v, Config.get_timeout(), {'User-Agent': Config.get_user_agent()})
            
            # Then validate the normalized URL
            if not validate_url(normalized_url):
                raise ValueError(f"Invalid URL format: {normalized_url}")
                
            return normalized_url
        except Exception as e:
            raise ValueError(f"Could not access URL {v}: {str(e)}")

    class Config:
        json_schema_extra = {
            "example": {
                "start_url": "https://example.com",
                "crawled_pages": {
                    "https://example.com": {
                        "url": "https://example.com",
                        "discovered_links": {
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
                "all_discovered_urls": {
                    "https://example.com",
                    "https://example.com/about",
                    "https://example.com/products"
                },
                "start_time": "2024-02-14 12:00:00",
                "end_time": "2024-02-14 12:01:00"
            }
        }
