"""Metrics models for the web crawler."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    URL_QUEUED = "url_queued"
    URL_PROCESSING = "url_processing"
    URL_PROCESSED = "url_processed"
    URL_FAILED = "url_failed"
    SCRAPE_STARTED = "scrape_started"
    SCRAPE_COMPLETED = "scrape_completed"
    SCRAPE_FAILED = "scrape_failed"


class CrawlerMetrics(BaseModel):
    # Timestamps
    start_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)
    
    # URL counts
    urls_queued: int = Field(default=0)
    urls_processing: int = Field(default=0)
    urls_processed: int = Field(default=0)
    urls_failed: int = Field(default=0)
    
    # Scrape counts
    scrapes_started: int = Field(default=0)
    scrapes_completed: int = Field(default=0)
    scrapes_failed: int = Field(default=0)
    
    # URL tracking
    processed_urls: List[str] = Field(default_factory=list)
    failed_urls: List[str] = Field(default_factory=list)
    
    # Performance metrics
    elapsed_seconds: float = Field(default=0.0)
    urls_per_second: float = Field(default=0.0)
    success_rate: float = Field(default=0.0)
    
    def update(self, metric_type: MetricType, url: str) -> None:
        """Update metrics based on the metric type."""
        self.last_update = datetime.now()
        self.elapsed_seconds = (self.last_update - self.start_time).total_seconds()
        
        # Update counts based on metric type
        if metric_type == MetricType.URL_QUEUED:
            self.urls_queued += 1
        elif metric_type == MetricType.URL_PROCESSING:
            self.urls_processing += 1
            self.urls_queued = max(0, self.urls_queued - 1)
        elif metric_type == MetricType.URL_PROCESSED:
            self.urls_processed += 1
            self.urls_processing = max(0, self.urls_processing - 1)
            self.processed_urls.append(url)
        elif metric_type == MetricType.URL_FAILED:
            self.urls_failed += 1
            self.urls_processing = max(0, self.urls_processing - 1)
            self.failed_urls.append(url)
        elif metric_type == MetricType.SCRAPE_STARTED:
            self.scrapes_started += 1
        elif metric_type == MetricType.SCRAPE_COMPLETED:
            self.scrapes_completed += 1
        elif metric_type == MetricType.SCRAPE_FAILED:
            self.scrapes_failed += 1
        
        # Update performance metrics
        total_urls = self.urls_processed + self.urls_failed
        if total_urls > 0:
            self.success_rate = (self.urls_processed / total_urls) * 100
            if self.elapsed_seconds > 0:
                self.urls_per_second = total_urls / self.elapsed_seconds
