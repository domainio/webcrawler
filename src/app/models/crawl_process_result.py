from typing import Dict, Set
from datetime import datetime
from pydantic import BaseModel, Field

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
