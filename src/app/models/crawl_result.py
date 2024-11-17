#!/usr/bin/env python3
from typing import Dict, Set
from pydantic import BaseModel, Field

from .page_data import PageData

class CrawlResult(BaseModel):
    """Data model for storing crawl results."""
    links: Set[str] = Field(default_factory=set, description="Set of discovered URLs")
    data: Dict[str, PageData] = Field(
        default_factory=dict, 
        description="Dictionary mapping URLs to their page data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "links": {"https://example.com", "https://example.com/page1"},
                "data": {
                    "https://example.com": {
                        "depth": 1,
                        "ratio": 0.75,
                        "timestamp": "2024-02-14 12:00:00"
                    }
                }
            }
        }
