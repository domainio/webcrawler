#!/usr/bin/env python3
from pydantic import BaseModel, Field

class PageData(BaseModel):
    """Data model for a single page crawl result."""
    depth: int = Field(description="Depth level in the crawl tree")
    ratio: float = Field(description="Ratio of same-domain links to total links", ge=0, le=1)
    timestamp: str = Field(description="Timestamp of when the page was crawled")

    class Config:
        json_schema_extra = {
            "example": {
                "depth": 1,
                "ratio": 0.75,
                "timestamp": "2024-02-14 12:00:00"
            }
        }
