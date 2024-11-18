import csv
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse
from pathlib import Path
from tabulate import tabulate

from ..app.models import CrawlProcessResult
from .config import Config
from . import tsv_util

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

def save_crawl_results(result: CrawlProcessResult) -> str:
    """Save crawl results to a TSV file."""
    output_dir = Config.get_results_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    filename = _generate_filename(result.start_url, "tsv")
    output_path = os.path.join(output_dir, filename)
    
    data = tsv_util.formulate(result)
    tsv = tabulate(data, headers='firstrow', tablefmt='tsv')
    with open(output_path, 'w') as f:
        f.write(tsv)
    
    return output_path
