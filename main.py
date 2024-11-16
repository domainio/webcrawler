#!/usr/bin/env python3
import sys
import logging
from src.app.web_crawler import WebCrawler
from src.utils.logger import setup_logger
from src.utils import io_file_writer

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
    
    # Initialize and run crawler
    try:
        crawler = WebCrawler(url, max_depth, logger)
        results = crawler.crawl()
        
        # Save results to file
        output_file = io_file_writer.write_results(url, results, logger)
        logger.info(f"Crawl completed. Results saved to: {output_file}")
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
