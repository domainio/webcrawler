import csv
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse

from ..app.models import CrawlProcessResult
from .config import Config

def generate_filename(url: str) -> str:
    """Generate a filename based on domain and timestamp."""
    domain = urlparse(url).netloc or url
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"crawl_{domain}_{timestamp}.tsv"

def write(results: CrawlProcessResult, filename: str = None) -> str:
    """Write crawling results to a TSV file in the configured output directory.
    
    Args:
        results: The crawl results to write
        filename: Optional filename, if not provided one will be generated
        
    Returns:
        The full path to the written file
    """
    # Get output directory from config and ensure it exists
    output_dir = Config.get_results_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate or use provided filename
    if not filename:
        filename = generate_filename(str(results.start_url))
    
    # Create full output path
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['URL', 'Depth', 'Link Ratio', 'Discovered Links', 'Success', 'Error'])
        
        for url, page_result in results.crawled_pages.items():
            writer.writerow([
                url,
                page_result.depth,
                f"{page_result.ratio:.2f}",
                len(page_result.discovered_links),
                page_result.success,
                page_result.error or 'None'
            ])
    
    return output_path
