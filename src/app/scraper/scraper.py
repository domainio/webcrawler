import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
from playwright.async_api import async_playwright, Page

from ...utils.file_io import save_scrape_content
from ...utils.config import Config

class Scraper:
    """Core scraper component that handles web page content extraction and storage."""
    
    def __init__(self, logger: logging.Logger, root_url: str):
        """Initialize scraper with logger and root URL."""
        self.logger = logger
        self.root_url = root_url
        self.save_dir = Path(Config.get_scrape_dir())
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
    async def _setup_browser(self) -> Tuple[Page, Any]:
        """Setup and configure browser for scraping."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=Config.get_headless_mode()
        )
        page = await browser.new_page()
        
        # Configure page
        await page.set_extra_http_headers({
            'User-Agent': Config.get_user_agent()
        })
        
        return page, browser
        
    async def _navigate_to_page(self, page: Page, url: str) -> None:
        """Navigate to URL and wait for page load."""
        await page.goto(
            url,
            wait_until='networkidle',
            timeout=Config.get_timeout() * 1000
        )
        
    async def _extract_content(self, page: Page) -> Tuple[str, str]:
        """Extract content and title from page."""
        content = await page.content()
        title = await page.title()
        return content, title
        
    async def _save_content(self, url: str, content: str) -> Path:
        return save_scrape_content(self.root_url,url, content)
        
    def _create_result(self, url: str, title: str, saved_path: Path) -> Dict[str, Any]:
        """Create successful scrape result."""
        return {
            'url': url,
            'title': title,
            'saved_path': str(saved_path),
            'timestamp': datetime.now().isoformat()
        }
        
    async def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single URL and save its content."""
        page = None
        browser = None
        
        try:
            page, browser = await self._setup_browser()
            await self._navigate_to_page(page, url)
            content, title = await self._extract_content(page)
            saved_path = await self._save_content(url, content)
            return self._create_result(url, title, saved_path)
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
            
        finally:
            if page:
                await page.close()
            if browser:
                await browser.close()
