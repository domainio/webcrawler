from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from ...utils.url_utils import validate_url, normalize_url
from ...utils.config import Config

class CrawlPageResult(BaseModel):
    """Result of crawling a single page."""
    
    url: str = Field(title="URL", description="URL of the crawled page")
    links: List[str] = Field(title="Total Links Count", default_factory=list, description="List of URLs discovered on this page")
    same_domain_links_count: int = Field(title="Same Domain Links Count", description="Number of same-domain links found")
    external_links_count: int = Field(title="External Links Count", description="Number of external domain links found")
    depth: int = Field(title="Depth", description="Depth level in the crawl tree")
    ratio: float = Field(
        title="Ratio",
        default=0,
        description="Ratio of same-domain links to total links",
        ge=0,
        le=1
    )
    timestamp: str = Field(
        title="Timestamp",
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Timestamp when the page was crawled"
    )
    success: bool = Field(
        title="Success",
        default=True,
        description="Whether the page was successfully crawled"
    )
    error: Optional[str] = Field(
        title="Error",
        default=None,
        description="Error message if crawl failed"
    )

    @validator('links', pre=True)
    def validate_links(cls, v):
        """Validate and normalize URLs in the links list, skipping invalid ones."""
        if not v:
            return []
        
        valid_links = []
        for url in v:
            try:
                if validate_url(url):
                    normalized = normalize_url(url, Config.get_timeout(), {'User-Agent': Config.get_user_agent()})
                    valid_links.append(normalized)
            except Exception:
                continue
        return valid_links

    class Config:
        arbitrary_types_allowed = True
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
