from typing import Callable, List
from ..app.models.metrics import CrawlerMetrics, MetricType


class MetricsPubSub:
    def __init__(self):
        self._subscribers: List[Callable[[MetricType, str], None]] = []
        self.metrics = CrawlerMetrics()
    
    def subscribe(self, callback: Callable[[MetricType, str], None]) -> None:
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[MetricType, str], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def publish(self, metric_type: MetricType, url: str) -> None:
        self.metrics.update(metric_type, url)
        for subscriber in self._subscribers:
            try:
                subscriber(metric_type, url)
            except Exception as e:
                print(f"Error notifying subscriber: {str(e)}")
    
    def get_metrics(self) -> CrawlerMetrics:
        return self.metrics
