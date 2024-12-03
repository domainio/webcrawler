# Advanced Asynchronous Web Crawler

A high-performance, asynchronous web crawler with integrated scraping capabilities. This crawler combines efficient URL processing with powerful content extraction, making it suitable for both large-scale web crawling and focused content scraping tasks.

## Key Features

- **Asynchronous Processing**: 
  - Asynchronous URL crawling and content scraping
  - Batch processing with configurable batch sizes
  - Efficient resource utilization
- **Smart Content Extraction**: 
  - Playwright-based dynamic content scraping
  - Handles JavaScript-rendered content
  - Configurable timeouts and retries
- **Metrics and Progress Tracking**:
  - Real-time crawling metrics
  - Progress visualization with tqdm
  - Comprehensive crawl statistics
- **Robust Error Handling**:
  - Per-URL error tracking
  - Detailed error logging
  - Process recovery capabilities
- **Organized Output**:
  - Structured content storage
  - TSV report generation
  - Detailed crawl results

## Architecture

The crawler consists of three main components:

1. **WebCrawlerManager**
   - Manages the crawling process
   - Handles URL queue and depth tracking
   - Coordinates batch processing
   - Collects and aggregates results

2. **WebCrawlerWorker**
   - Processes individual URLs
   - Extracts and validates links
   - Manages page-level operations
   - Reports crawl results

3. **Scraper**
   - Controls Playwright browser automation
   - Handles page navigation and content extraction
   - Manages content storage
   - Reports scraping metrics

### Data Models

The crawler uses Pydantic models for robust data validation and serialization:

- `CrawlProcessResult`: Tracks overall crawl process including:
  - Crawled pages
  - All discovered URLs
  - Process statistics
  - Timing information

- `CrawlPageResult`: Represents individual page crawl results with:
  - URL and depth information
  - Link statistics (same-domain vs external)
  - Success/error status
  - Timestamp data

## Installation

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)

### Setup

1. Extract the project:
   ```bash
   unzip webcraler.zip -d <local-directory>
   cd <local-directory>
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # Or on Windows:
   # .venv\Scripts\activate
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. (Optional) Install Playwright browser - only needed if you haven't installed Chromium before:
   ```bash
   poetry run playwright install chromium
   ```

Note: The Playwright package is required for the crawler to work, but installing the browser is optional if you already have Chromium installed on your system.

### Environment Setup

Create a `.env` file in the project root with your configuration:

```env
JOBS_DIR=.jobs
SCRAPE_DIR=scrape
LOG_LEVEL=INFO
MAX_BATCH_SIZE=100
BROWSER_HEADLESS=true
```

## Usage

Basic usage with command line interface:

```bash
python main.py <url> <max_depth>
```

Example:
```bash
python main.py https://example.com 3
```

### Configuration

Configure the crawler through environment variables:

- `SCRAPE_DIR`: Directory for scraped content (default: 'scrape')
- `WEB_PAGE_USER_AGENT`: Custom user agent string
- `HTTP_REQUEST_TIMEOUT`: Request timeout in seconds (default: 10)
- `MAX_BATCH_SIZE`: Maximum URLs to process in a batch (default: 100)
- `BROWSER_HEADLESS`: Run browser in headless mode (default: true)

## Output

The crawler generates two main types of output:

### 1. Scraped Content

All scraped content is saved in a structured directory format:
```
.
└── .jobs
    └── <domain>
        └── <url>.tsv
        └── scrape
            └── <url>.html
```

### 2. Crawl Report (TSV)

After completion, the crawler generates a detailed TSV report with the following fields:

| Field | Description |
|-------|-------------|
| URL | The crawled URL |
| Depth | Crawl depth from root URL |
| Same Domain Links Count | Number of links to same domain |
| Links | Total number of links found |
| Ratio | Ratio of same-domain to total links |
| External Links Count | Number of links to other domains |
| Timestamp | When the URL was crawled |
| Success | Whether crawl was successful |
| Error | Error message if failed, 'None' if successful |

Sample TSV output:
```tsv
URL	Depth	Same Domain Links Count	Links	Ratio	External Links Count	Timestamp	Success	Error
https://example.com	1	15	20	0.75	5	2024-02-15 10:30:45	True	None
https://example.com/about	2	8	12	0.67	4	2024-02-15 10:30:47	True	None
https://example.com/404	2	0	0	0.00	0	2024-02-15 10:30:48	False	404 Not Found
```

## Metrics and Progress

The crawler provides real-time metrics:
- URLs queued/processed/failed
- Current crawl depth
- Processing success rate
- Time elapsed
- Progress visualization

## Error Handling

The crawler handles various error scenarios:
- Network timeouts
- Invalid URLs
- Failed page loads
- Browser errors
- Resource cleanup

## Development

### Project Structure
```
src/
├── app/
│   ├── models/         # Data models
│   ├── scraper/        # Content scraping
│   └── web_crawler/    # Core crawler logic
├── utils/
│   ├── config.py       # Configuration management
│   ├── file_io.py      # File operations
│   ├── logger.py       # Logging setup
│   └── metrics_pubsub.py  # Metrics system
└── main.py             # CLI entry point
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
