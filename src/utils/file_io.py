import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from pathvalidate import sanitize_filename
from tabulate import tabulate

from ..app.models import CrawlProcessResult
from .config import Config
from ..utils import tsv_util

def get_job_path(root_url: str) -> Path:
    """Get the job directory path for a given root URL."""
    domain = urlparse(root_url).netloc or root_url
    job_name = sanitize_filename(domain)[:255]
    return Path(Config.get_jobs_dir()) / job_name

def save_scrape_content(root_url: str, url: str, content: str) -> str:
    """Save scraped HTML content to a file."""
    job_path = get_job_path(root_url)
    url_dir = sanitize_filename(url)[:255]
    target_dir = job_path / Config.get_scrape_dir() / url_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{sanitize_filename(url)[:255]}.html"
    file_path.write_text(content)
    return str(file_path)

def save_crawl_results(result: CrawlProcessResult) -> str:
    """Save crawl results to a TSV file."""
    job_path = get_job_path(result.start_url)
    job_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    domain = urlparse(result.start_url).netloc or result.start_url
    filename = f"crawler_{sanitize_filename(domain)}_{timestamp}.tsv"
    file_path = job_path / filename
    data = tsv_util.formulate(result)
    tsv = tabulate(data, headers='firstrow', tablefmt='tsv')
    file_path.write_text(tsv)
    return str(file_path)