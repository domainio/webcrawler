from typing import Set
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class CrawlPageResult(BaseModel):
    """Result of crawling a single page."""
    url: HttpUrl = Field(description="The URL that was crawled")
    discovered_links: Set[str] = Field(
        default_factory=set,
        description="Set of URLs discovered on this page"
    )
    depth: int = Field(description="Depth level in the crawl tree")
    ratio: float = Field(
        description="Ratio of same-domain links to total links",
        ge=0,
        le=1
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        description="Timestamp when the page was crawled"
    )
    success: bool = Field(
        default=True,
        description="Whether the page was successfully crawled"
    )
    error: str = Field(
        default="",
        description="Error message if crawl failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "discovered_links": {
                    "https://example.com/about",
                    "https://example.com/products"
                },
                "depth": 1,
                "ratio": 0.75,
                "timestamp": "2024-02-14 12:00:00",
                "success": True,
                "error": ""
            }
        }
