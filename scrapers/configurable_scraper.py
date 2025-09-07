"""
Configurable Scraper - A flexible, configuration-driven scraper that can adapt to any website structure.
This eliminates the need for individual scraper files for each exam.
"""

import requests
from bs4 import BeautifulSoup
import hashlib
import time
import re
import json
from datetime import datetime
import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from config.settings import REQUEST_TIMEOUT, MAX_RETRIES, USER_AGENT
from typing import Dict, List, Any, Optional


class ConfigurableScraper:
    """
    A flexible scraper that can adapt to any website structure based on configuration.
    This replaces the need for individual scraper files.
    """
    
    def __init__(self, config: Dict[str, Any]):
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
        self.logger = logging.getLogger(f"ConfigurableScraper-{config.get('name', 'Unknown')}")
        
        # Load custom parsing plugins if specified
        self.custom_parsers = self._load_custom_parsers()
        
    def _load_custom_parsers(self) -> Dict[str, Any]:
        """Load custom parsing plugins if specified in config"""
        custom_parsers = {}
        if 'custom_parsers' in self.config:
            for parser_name, parser_config in self.config['custom_parsers'].items():
                try:
                    # Dynamic import of custom parser
                    module_path = parser_config['module']
                    class_name = parser_config['class']
                    
                    import importlib
                    module = importlib.import_module(module_path)
                    parser_class = getattr(module, class_name)
                    custom_parsers[parser_name] = parser_class(parser_config)
                    
                    self.logger.info(f"Loaded custom parser: {parser_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load custom parser {parser_name}: {e}")
        
        return custom_parsers

    def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method that adapts based on configuration"""
        try:
            # Handle different URL types
            if self.config['url'].startswith('file://'):
                return self._scrape_file()
            else:
                return self._scrape_web()
                
        except Exception as e:
            self.logger.error(f"Error scraping {self.config.get('name', 'Unknown')}: {e}")
            return []

    def _scrape_web(self) -> List[Dict[str, Any]]:
        """Scrape web-based content"""
        response = self.fetch_page(self.config['url'])
        soup = BeautifulSoup(response.text, 'lxml')
        
        updates = []
        
        # Use custom parsers if available
        if self.custom_parsers:
            for parser_name, parser in self.custom_parsers.items():
                try:
                    parser_updates = parser.parse(soup, self.config)
                    updates.extend(parser_updates)
                except Exception as e:
                    self.logger.error(f"Custom parser {parser_name} failed: {e}")
        
        # Use configuration-based parsing
        config_updates = self._parse_with_config(soup)
        updates.extend(config_updates)
        
        return updates

    def _scrape_file(self) -> List[Dict[str, Any]]:
        """Scrape file-based content (for demo/testing)"""
        file_path = self.config['url'].replace('file://', '')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml')
            return self._parse_with_config(soup)
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []

    def _parse_with_config(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse content using configuration-based selectors"""
        updates = []
        
        # Get parsing strategy from config
        strategy = self.config.get('parsing_strategy', 'standard')
        
        if strategy == 'standard':
            updates = self._parse_standard(soup)
        elif strategy == 'multi_section':
            updates = self._parse_multi_section(soup)
        elif strategy == 'dynamic':
            updates = self._parse_dynamic(soup)
        elif strategy == 'api':
            updates = self._parse_api()
        
        return updates

    def _parse_standard(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Standard parsing using configured selectors"""
        updates = []
        
        # Find containers using configured selectors
        containers = self._find_containers(soup)
        
        for container in containers:
            try:
                update = self._extract_update_info(container)
                if update and self._is_relevant_update(update):
                    updates.append(update)
            except Exception as e:
                self.logger.error(f"Error extracting update: {e}")
                continue
                
        return updates

    def _parse_multi_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse multiple sections with different selectors"""
        updates = []
        
        sections = self.config.get('sections', [])
        for section in sections:
            try:
                section_containers = soup.select(section['container_selector'])
                for container in section_containers:
                    update = self._extract_update_info(container, section.get('selectors', {}))
                    if update and self._is_relevant_update(update):
                        updates.append(update)
            except Exception as e:
                self.logger.error(f"Error parsing section {section.get('name', 'Unknown')}: {e}")
                
        return updates

    def _parse_dynamic(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Dynamic parsing that adapts to page structure"""
        updates = []
        
        # Try multiple selector strategies
        selector_strategies = self.config.get('dynamic_selectors', [])
        
        for strategy in selector_strategies:
            try:
                containers = soup.select(strategy['container'])
                if containers:
                    self.logger.info(f"Found {len(containers)} containers with strategy: {strategy['name']}")
                    
                    for container in containers:
                        update = self._extract_update_info(container, strategy.get('selectors', {}))
                        if update and self._is_relevant_update(update):
                            updates.append(update)
                    break  # Use first successful strategy
            except Exception as e:
                self.logger.error(f"Dynamic strategy {strategy.get('name', 'Unknown')} failed: {e}")
                continue
                
        return updates

    def _parse_api(self) -> List[Dict[str, Any]]:
        """Parse API-based content"""
        updates = []
        
        api_config = self.config.get('api_config', {})
        if not api_config:
            return updates
            
        try:
            # Make API request
            response = self.session.get(
                api_config['url'],
                params=api_config.get('params', {}),
                headers=api_config.get('headers', {}),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse API response
            items = self._extract_api_items(data, api_config.get('data_path', ''))
            
            for item in items:
                update = self._convert_api_item_to_update(item, api_config.get('field_mapping', {}))
                if update and self._is_relevant_update(update):
                    updates.append(update)
                    
        except Exception as e:
            self.logger.error(f"API parsing failed: {e}")
            
        return updates

    def _find_containers(self, soup: BeautifulSoup) -> List:
        """Find news containers using configured selectors"""
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

    def _extract_update_info(self, container, custom_selectors: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Extract update information from container"""
        selectors = custom_selectors or self.config['selectors']
        
        title_elem = self._find_element(container, selectors['title'])
        date_elem = self._find_element(container, selectors.get('date', ''))
        link_elem = self._find_element(container, selectors.get('link', ''))
        
        if not title_elem:
            return None
            
        title = title_elem.get_text(strip=True)
        if not title:
            return None
            
        date = self._parse_date(date_elem.get_text(strip=True) if date_elem else "")
        link = self._resolve_url(link_elem.get('href') if link_elem else "")
        
        # Generate content hash for change detection
        content_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        
        return {
            'title': title,
            'date': date,
            'url': link,
            'content_summary': title,
            'source': self.config['name'],
            'scraped_at': datetime.now().isoformat(),
            'content_hash': content_hash,
            'priority': self.config.get('priority', 'medium'),
            'exam_type': self.config.get('exam_type', 'unknown')
        }

    def _find_element(self, container, selector_string: str):
        """Find element using multiple selectors"""
        if not selector_string:
            return None
            
        selectors = selector_string.split(', ')
        for selector in selectors:
            element = container.select_one(selector.strip())
            if element:
                return element
        return None

    def _is_relevant_update(self, update: Dict[str, Any]) -> bool:
        """Check if update is relevant using configured keywords"""
        text = (update['title'] + ' ' + update.get('content_summary', '')).lower()
        keywords = [keyword.lower() for keyword in self.config.get('keywords', [])]
        
        # If no keywords configured, consider all updates relevant
        if not keywords:
            return True
            
        return any(keyword in text for keyword in keywords)

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to standard format"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Use custom date parser if configured
        if 'date_parser' in self.config:
            try:
                return self._custom_date_parse(date_str, self.config['date_parser'])
            except Exception as e:
                self.logger.error(f"Custom date parsing failed: {e}")
        
        # Default date parsing
        date_patterns = [
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                return date_str  # Return original for now
        
        return date_str

    def _custom_date_parse(self, date_str: str, parser_config: Dict) -> str:
        """Custom date parsing based on configuration"""
        # Implement custom date parsing logic based on parser_config
        # This could include specific patterns, date formats, etc.
        return date_str

    def _resolve_url(self, url: str) -> str:
        """Resolve relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        return urljoin(self.config['url'], url)

    def _extract_api_items(self, data: Dict, data_path: str) -> List[Dict]:
        """Extract items from API response using data path"""
        if not data_path:
            return [data] if isinstance(data, dict) else data if isinstance(data, list) else []
        
        # Navigate through nested data structure
        current = data
        for key in data_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []
        
        return current if isinstance(current, list) else [current]

    def _convert_api_item_to_update(self, item: Dict, field_mapping: Dict) -> Dict[str, Any]:
        """Convert API item to standard update format"""
        update = {
            'title': self._get_field_value(item, field_mapping.get('title', 'title')),
            'date': self._get_field_value(item, field_mapping.get('date', 'date')),
            'url': self._get_field_value(item, field_mapping.get('url', 'url')),
            'content_summary': self._get_field_value(item, field_mapping.get('content', 'content')),
            'source': self.config['name'],
            'scraped_at': datetime.now().isoformat(),
            'content_hash': hashlib.md5(str(item).encode('utf-8')).hexdigest(),
            'priority': self.config.get('priority', 'medium'),
            'exam_type': self.config.get('exam_type', 'unknown')
        }
        
        return update

    def _get_field_value(self, item: Dict, field_path: str) -> str:
        """Get field value from nested dictionary using dot notation"""
        if not field_path:
            return ""
            
        current = item
        for key in field_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return ""
        
        return str(current) if current is not None else ""

    def fetch_page(self, url: str, retries: int = MAX_RETRIES):
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


class CustomParser(ABC):
    """Base class for custom parsing plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"CustomParser-{config.get('name', 'Unknown')}")
    
    @abstractmethod
    def parse(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse content and return list of updates"""
        pass
