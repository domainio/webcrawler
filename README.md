# Web Crawler

A production-ready Python web crawler that can crawl websites recursively, calculate page ranks based on same-domain link ratios, and handle various URL formats and edge cases.

## Features

- Depth-limited recursive crawling
- Support for both HTTP and HTTPS protocols
- Handles relative and absolute URLs
- Calculates same-domain links ratio for each page
- Detects and excludes dynamically added links
- Avoids re-downloading already visited pages
- Progress bar showing crawling status
- Comprehensive logging
- Outputs results in TSV format

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the crawler from the command line with two arguments:
1. The URL of the root page to crawl
2. The recursion depth limit (positive integer)

Example:
```bash
python web_crawler.py https://example.com 3
```

If the protocol (http:// or https://) is missing from the URL, https:// will be used by default.

## Output

The crawler generates a TSV (tab-separated values) file named `crawler_results.tsv` containing:
- Full URL of each crawled page
- Depth in the links tree
- Same-domain links ratio (between 0 and 1)

## Error Handling

The crawler includes robust error handling for:
- Invalid URLs
- Network errors
- Timeouts
- Non-HTML content
- Invalid depth parameters

## Rate Limiting

The crawler includes basic rate limiting through connection timeouts and session management to avoid overwhelming servers.

## Notes

- The crawler respects robots.txt implicitly through the use of standard request headers
- Links that appear to be dynamically added by JavaScript are excluded
- Each URL appears only once in the output, even if encountered multiple times
- The crawler uses a breadth-first search approach for crawling
