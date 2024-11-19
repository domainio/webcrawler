import click
import logging
from src.app.web_crawler import WebCrawlerManager
from src.utils.logger import setup_logger
from src.utils import MetricsPubSub, tsv_util, file_io, with_progress_bar, normalize_and_validate_url

@click.command()
@click.argument('url', callback=lambda ctx, param, value: normalize_and_validate_url(value))
@click.argument('max_depth', type=click.IntRange(min=1))
def main(url, max_depth):
    logger = setup_logger('webcrawler')
    metrics = MetricsPubSub()
    
    try:
        crawler = WebCrawlerManager(url, max_depth, logger, metrics)
        results = with_progress_bar(
            operation=crawler.crawl,
            desc=f"Crawling {url} (max depth: {max_depth})"
        )
        output_path = file_io.save_crawl_results(results)
        logger.info(f"Report written to {output_path}")
        tsv_util.display(results)
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        raise click.Abort()

if __name__ == "__main__":
    main()
