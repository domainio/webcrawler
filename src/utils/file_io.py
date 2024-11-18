import csv
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse
from pathlib import Path
from tabulate import tabulate
from pathvalidate import sanitize_filename

from ..app.models import CrawlProcessResult
from .config import Config
from . import tsv_util

def save_scrape_content(root_url:str, url: str, content: str) -> str:
    """Save scraped HTML content to a file."""
    project_dir = os.getcwd()
    jobs_dir = Config.get_jobs_dir()
    domain = urlparse(root_url).netloc or root_url
    
    scrape_dir = Config.get_scrape_dir()

    current_job_dir = sanitize_filename(domain)[:255]
    current_scrape_dir = sanitize_filename(url)[:255]
    target_path = Path(os.path.join(project_dir, jobs_dir, current_job_dir, scrape_dir,current_scrape_dir))
    target_path.mkdir(parents=True, exist_ok=True)
    
    file_name = sanitize_filename(f"{url}.html")[:255]
    output_path = target_path / file_name
    
    output_path.write_text(content)
    return str(output_path)

def save_crawl_results(result: CrawlProcessResult) -> str:
    """Save crawl results to a TSV file."""
    project_dir = os.getcwd()
    jobs_dir = Config.get_jobs_dir()
    domain = urlparse(result.start_url).netloc or result.start_url
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    current_job_dir = sanitize_filename(domain)[:255]
    target_path = os.path.join(project_dir, jobs_dir, current_job_dir)    
    
    os.makedirs(target_path, exist_ok=True)
    
    file_name = sanitize_filename(f"crawler_{domain}_{timestamp}.tsv")[:255]
    output_path = os.path.join(target_path, file_name)
    
    data = tsv_util.formulate(result)
    tsv = tabulate(data, headers='firstrow', tablefmt='tsv')
    with open(output_path, 'w') as f:
        f.write(tsv)
    
    return output_path