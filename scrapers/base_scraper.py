import requests
from bs4 import BeautifulSoup
import hashlib
import time
import re
from datetime import datetime
import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from config.settings import REQUEST_TIMEOUT, MAX_RETRIES, USER_AGENT


class BaseScraper(ABC):
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_page(self, url, retries=MAX_RETRIES):
        """Fetch webpage content with retry logic and exponential backoff"""
        for attempt in range(retries):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    self.logger.error(f"Max retries reached for {url}: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def parse_content(self, html_content):
        """Parse HTML content and extract updates"""
        soup = BeautifulSoup(html_content, 'lxml')
        updates = []
        
        # Find news containers using multiple selectors
        containers = self.find_containers(soup)
        
        for container in containers:
            try:
                update = self.extract_update_info(container)
                if update and self.is_exam_related(update):
                    updates.append(update)
            except Exception as e:
                self.logger.error(f"Error extracting update: {e}")
                continue
                
        return updates

    def find_containers(self, soup):
        """Find news containers using adaptive parsing"""
        containers = []
        selectors = self.config['selectors']['news_container'].split(', ')
        
        for selector in selectors:
            elements = soup.select(selector.strip())
            if elements:
                containers.extend(elements)
                self.logger.debug(f"Found {len(elements)} containers with selector: {selector}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in containers:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        return unique_containers

    def extract_update_info(self, container):
        """Extract update information from container"""
        title_elem = self.find_element(container, self.config['selectors']['title'])
        date_elem = self.find_element(container, self.config['selectors']['date'])
        link_elem = self.find_element(container, self.config['selectors']['link'])
        
        if not title_elem:
            return None
            
        title = title_elem.get_text(strip=True)
        if not title:
            return None
            
        date = self.parse_date(date_elem.get_text(strip=True) if date_elem else "")
        link = self.resolve_url(link_elem.get('href') if link_elem else "")
        
        # Generate content hash for change detection
        content_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        
        return {
            'title': title,
            'date': date,
            'url': link,
            'content_summary': title,  # Will be enhanced by AI
            'source': self.config['name'],
            'scraped_at': datetime.now().isoformat(),
            'content_hash': content_hash,
            'priority': self.config.get('priority', 'medium')
        }

    def find_element(self, container, selector_string):
        """Find element using multiple selectors"""
        selectors = selector_string.split(', ')
        for selector in selectors:
            element = container.select_one(selector.strip())
            if element:
                return element
        return None

    def is_exam_related(self, update):
        """Check if update is exam-related using keywords"""
        text = (update['title'] + ' ' + update.get('content_summary', '')).lower()
        keywords = [keyword.lower() for keyword in self.config['keywords']]
        return any(keyword in text for keyword in keywords)

    def parse_date(self, date_str):
        """Parse date string to standard format"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',  # YYYY/MM/DD or YYYY-MM-DD
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})\b',  # DD Month YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:
                        # Try to parse the matched date
                        match.groups()
                        # This is a simplified date parsing - in production, use dateutil.parser
                        return date_str  # Return original for now
                except:
                    continue
        
        return date_str

    def resolve_url(self, url):
        """Resolve relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        return urljoin(self.config['url'], url)

    def get_fallback_selectors(self, selector_type):
        """Get fallback selectors for different types"""
        fallbacks = {
            'title': ['h1', 'h2', 'h3', 'h4', '.title', '.heading', '.announcement-title'],
            'date': ['.date', '.published', '.timestamp', '.time', '.publish-date'],
            'link': ['a', '.link', '.read-more', '.more-link']
        }
        return fallbacks.get(selector_type, [])

    def handle_network_errors(self, func, *args, **kwargs):
        """Handle network-related errors with exponential backoff"""
        max_retries = 5
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Max retries reached: {e}")
                    raise
                
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Network error, retrying in {delay}s: {e}")
                time.sleep(delay)
            except requests.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    delay = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {delay}s")
                    time.sleep(delay)
                else:
                    raise

    @abstractmethod
    def scrape(self):
        """Main scraping method to be implemented by subclasses"""
