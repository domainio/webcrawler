from typing import List
from tabulate import tabulate

from ..app.models import CrawlProcessResult, CrawlPageResult

def formulate(results: CrawlProcessResult) -> List[List[str]]:
    """Formulate crawl results into a list of rows for TSV output."""
    # Define field order and get titles
    field_order = [
        'url', 'depth', 'same_domain_links_count', 'links',
        'ratio', 'external_links_count', 'timestamp', 'success', 'error'
    ]
    
    titles = []
    for field_name in field_order:
        field = CrawlPageResult.__fields__[field_name]
        # The field itself is the FieldInfo in Pydantic
        title = field.title if hasattr(field, 'title') else field_name.replace('_', ' ').title()
        titles.append(title)
    
    # Prepare data with headers and rows
    data = [titles]  # First row is headers
    for page in results.crawled_pages.values():
        row = [
            page.url,
            str(page.depth),
            str(page.same_domain_links_count),
            str(len(page.links)),
            f"{page.ratio:.2f}",
            str(page.external_links_count),
            page.timestamp,
            str(page.success),
            page.error or 'None'
        ]
        data.append(row)
    
    return data

def display(results: CrawlProcessResult) -> None:
    """Print crawl results in TSV format."""
    data = formulate(results)
    tsv = tabulate(data, headers='firstrow', tablefmt='tsv')
    print(tsv)