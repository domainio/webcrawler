from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CrawlPageResult(BaseModel):
    """Result of crawling a single page."""
    url: str = Field(description="URL of the crawled page")
    links: List[str] = Field(description="List of URLs discovered on this page")
    same_domain_links_count: int = Field(description="Number of same-domain links found")
    external_links_count: int = Field(description="Number of external domain links found")
    depth: int = Field(description="Depth level in the crawl tree")
    ratio: float = Field(
        default=0,
        description="Ratio of same-domain links to total links",
        ge=0,
        le=1
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Timestamp when the page was crawled"
    )
    success: bool = Field(
        default=True,
        description="Whether the page was successfully crawled"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if crawl failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "links": [
                    "https://example.com/about",
                    "https://example.com/products",
                    "https://external.com"
                ],
                "same_domain_links_count": 2,
                "external_links_count": 1,
                "depth": 1,
                "ratio": 0.75,
                "timestamp": "2024-02-14 12:00:00",
                "success": True,
                "error": None
            }
        }
