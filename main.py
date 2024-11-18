import sys
import logging
from src.app.web_crawler import WebCrawlerManager
from src.utils.logger import setup_logger
from src.utils import tsv_util, file_io, with_progress_bar

def main():
    # Set up logging
    logger = setup_logger('webcrawler')
    
    # Validate command line arguments
    if len(sys.argv) != 3:
        logger.error("Usage: python main.py <url> <max_depth>")
        sys.exit(1)
    
    url = sys.argv[1]
    try:
        max_depth = int(sys.argv[2])
    except ValueError:
        logger.error("Max depth must be an integer")
        sys.exit(1)
    
    try:
        crawler = WebCrawlerManager(url, max_depth, logger)
        results = with_progress_bar(
            operation=crawler.crawl,
            desc=f"Crawling {url} (max depth: {max_depth})"
        )
        output_path = file_io.save_crawl_results(results)
        logger.info(f"Results written to {output_path}")
        tsv_util.display(results)
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
