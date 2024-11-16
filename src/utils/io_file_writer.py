import csv
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse
import logging
from .config import Config

def generate_filename(root_url: str) -> str:
    """Generate a filename for the results based on domain and timestamp."""
    domain = urlparse(root_url).netloc
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"crawl_{domain}_{timestamp}.tsv"

def ensure_dir_exists(directory: str) -> None:
    """Ensure the output directory exists."""
    os.makedirs(directory, exist_ok=True)

def write_results(root_url: str, results: Dict[str, Dict[str, Any]], logger: logging.Logger) -> str:
    """Write crawling results to a TSV file."""
    output_dir = Config.get_results_dir()
    ensure_dir_exists(output_dir)
    
    output_file = generate_filename(root_url)
    output_path = os.path.join(output_dir, output_file)
    
    try:
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['datetime', 'url', 'depth', 'ratio'])
            
            for url, data in results.items():
                writer.writerow([
                    data['timestamp'],
                    url,
                    data['depth'],
                    f"{data['ratio']:.3f}"
                ])
        
        logger.info(f"Results saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error writing results to {output_path}: {str(e)}")
        raise
