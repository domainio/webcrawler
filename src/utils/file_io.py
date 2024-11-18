import csv
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse
from pathlib import Path

from ..app.models import CrawlProcessResult
from .config import Config

def _generate_filename(url: str, extension: str) -> str:
    """Generate a filename based on domain and timestamp with specified extension."""
    domain = urlparse(url).netloc or url
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{domain}_{timestamp}.{extension}"

def save_scrape_content(url: str, content: str) -> str:
    """Save scraped HTML content to a file."""
    output_dir = Config.get_scrape_dir()
    os.makedirs(output_dir, exist_ok=True)
    filename = _generate_filename(url, "html")
    output_path = os.path.join(output_dir, filename)
    output_path.write_text(content)
    return output_path

def save_crawl_results(results: CrawlProcessResult) -> str:
    """Save crawl results to a TSV file."""
    output_dir = Config.get_results_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    filename = _generate_filename(results.start_url, "tsv")
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'URL', 
            'Depth', 
            'Same Domain Links Count',
            'Total Links Count',
            'Ratio', 
            'External Links Count', 
            'Success', 
            'Error'
        ])
        
        for url, page_result in results.crawled_pages.items():
            writer.writerow([
                url,
                page_result.depth,
                page_result.same_domain_links_count,
                len(page_result.links),
                f"{page_result.ratio:.2f}",
                page_result.external_links_count,
                page_result.success,
                page_result.error or 'None'
            ])
    
    return output_path
