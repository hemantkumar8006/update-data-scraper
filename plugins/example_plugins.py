"""
Example plugins demonstrating custom parsing logic
"""

from .base_plugin import BasePlugin
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import hashlib
from datetime import datetime
import re


class NTAAdvancedPlugin(BasePlugin):
    """
    Advanced plugin for NTA websites with complex structure
    """
    
    version = "1.0.0"
    description = "Advanced parsing for NTA websites with ticker and notices"
    author = "Exam Scraper Team"
    
    def parse(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse NTA website with advanced logic"""
        updates = []
        
        # Parse news ticker
        ticker_updates = self._parse_news_ticker(soup, scraper_config)
        updates.extend(ticker_updates)
        
        # Parse scrollable notices
        notices_updates = self._parse_scrollable_notices(soup, scraper_config)
        updates.extend(notices_updates)
        
        # Parse main announcements
        main_updates = self._parse_main_announcements(soup, scraper_config)
        updates.extend(main_updates)
        
        return updates
    
    def _parse_news_ticker(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the news ticker section"""
        updates = []
        
        try:
            # Find the news ticker slides
            ticker_slides = soup.select('.newsticker .slides li')
            for slide in ticker_slides:
                try:
                    content = slide.get_text(strip=True)
                    if self._is_relevant_nta_update(content) and len(content) > 20:
                        link_elem = slide.select_one('a')
                        href = link_elem.get('href', '') if link_elem else ''
                        
                        update = {
                            'title': content,
                            'date': self._extract_date_from_title(content),
                            'url': self._resolve_url(href, scraper_config) if href else scraper_config['url'],
                            'content_summary': content,
                            'source': scraper_config['name'],
                            'scraped_at': datetime.now().isoformat(),
                            'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                            'priority': scraper_config.get('priority', 'high'),
                            'exam_type': scraper_config.get('exam_type', 'unknown')
                        }
                        updates.append(update)
                        
                except Exception as e:
                    self.logger.error(f"Error processing NTA ticker slide: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing NTA news ticker: {e}")
            
        return updates
    
    def _parse_scrollable_notices(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the scrollable notices section"""
        updates = []
        
        try:
            notices_container = soup.select_one('.scrollable-notices')
            if notices_container:
                notice_items = notices_container.select('a, .notice-item, .update-item')
                for item in notice_items:
                    try:
                        title = item.get_text(strip=True)
                        if self._is_relevant_nta_update(title) and len(title) > 10:
                            href = item.get('href', '') if item.name == 'a' else ''
                            
                            update = {
                                'title': title,
                                'date': self._extract_date_from_title(title),
                                'url': self._resolve_url(href, scraper_config) if href else scraper_config['url'],
                                'content_summary': title,
                                'source': scraper_config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': scraper_config.get('priority', 'medium'),
                                'exam_type': scraper_config.get('exam_type', 'unknown')
                            }
                            updates.append(update)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing NTA notice item: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing NTA scrollable notices: {e}")
            
        return updates
    
    def _parse_main_announcements(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse main announcements section"""
        updates = []
        
        try:
            # Look for main announcement containers
            announcement_containers = soup.select('.announcements, .main-news, .latest-updates')
            
            for container in announcement_containers:
                items = container.select('.announcement-item, .news-item, .update-item')
                
                for item in items:
                    try:
                        title_elem = item.select_one('h1, h2, h3, .title, .headline')
                        date_elem = item.select_one('.date, .publish-date, .timestamp')
                        link_elem = item.select_one('a')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if self._is_relevant_nta_update(title):
                                update = {
                                    'title': title,
                                    'date': date_elem.get_text(strip=True) if date_elem else self._extract_date_from_title(title),
                                    'url': self._resolve_url(link_elem.get('href', ''), scraper_config) if link_elem else scraper_config['url'],
                                    'content_summary': title,
                                    'source': scraper_config['name'],
                                    'scraped_at': datetime.now().isoformat(),
                                    'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                    'priority': scraper_config.get('priority', 'medium'),
                                    'exam_type': scraper_config.get('exam_type', 'unknown')
                                }
                                updates.append(update)
                                
                    except Exception as e:
                        self.logger.error(f"Error processing main announcement item: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing main announcements: {e}")
            
        return updates
    
    def _is_relevant_nta_update(self, title: str) -> bool:
        """Check if NTA update is relevant"""
        relevant_keywords = [
            'admit card', 'hall ticket', 'application', 'result', 'exam date', 
            'registration', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'allotment', 'cutoff', 'merit list', 'rank list',
            'jee main', 'nta', 'joint entrance', 'engineering', 'entrance exam',
            'public notice', 'circular', 'announcement', 'update', 'latest',
            'deadline', 'extension', 'postponed', 'cancelled', 'rescheduled'
        ]
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in relevant_keywords)
    
    def _extract_date_from_title(self, title: str) -> str:
        """Extract date from title if present"""
        date_patterns = [
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group()
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _resolve_url(self, url: str, scraper_config: Dict[str, Any]) -> str:
        """Resolve relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        from urllib.parse import urljoin
        return urljoin(scraper_config['url'], url)


class GATEAdvancedPlugin(BasePlugin):
    """
    Advanced plugin for GATE websites
    """
    
    version = "1.0.0"
    description = "Advanced parsing for GATE websites"
    author = "Exam Scraper Team"
    
    def parse(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse GATE website with advanced logic"""
        updates = []
        
        # Parse ticker section
        ticker_updates = self._parse_ticker_section(soup, scraper_config)
        updates.extend(ticker_updates)
        
        # Parse important dates
        dates_updates = self._parse_important_dates(soup, scraper_config)
        updates.extend(dates_updates)
        
        # Parse highlights
        highlights_updates = self._parse_highlights_section(soup, scraper_config)
        updates.extend(highlights_updates)
        
        return updates
    
    def _parse_ticker_section(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the ticker section for main announcements"""
        updates = []
        
        try:
            ticker_marquee = soup.select_one('.ticker .news .news-content')
            if ticker_marquee:
                content = ticker_marquee.get_text(strip=True)
                if self._is_relevant_gate_update(content) and len(content) > 20:
                    update = {
                        'title': content,
                        'date': self._extract_date_from_title(content),
                        'url': scraper_config['url'],
                        'content_summary': content,
                        'source': scraper_config['name'],
                        'scraped_at': datetime.now().isoformat(),
                        'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                        'priority': scraper_config.get('priority', 'high'),
                        'exam_type': scraper_config.get('exam_type', 'unknown')
                    }
                    updates.append(update)
                    
        except Exception as e:
            self.logger.error(f"Error parsing GATE ticker section: {e}")
            
        return updates
    
    def _parse_important_dates(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the important dates section"""
        updates = []
        
        try:
            dates_section = soup.select_one('.imp-dates-item')
            if dates_section:
                date_items = dates_section.select('li')
                for item in date_items:
                    try:
                        date_span = item.select_one('.text-warning')
                        if date_span:
                            date_text = date_span.get_text(strip=True)
                            description = item.get_text(strip=True)
                            if self._is_relevant_gate_update(description) and len(description) > 20:
                                update = {
                                    'title': f"Important Date: {description}",
                                    'date': date_text,
                                    'url': scraper_config['url'],
                                    'content_summary': description,
                                    'source': scraper_config['name'],
                                    'scraped_at': datetime.now().isoformat(),
                                    'content_hash': hashlib.md5(description.encode('utf-8')).hexdigest(),
                                    'priority': scraper_config.get('priority', 'high'),
                                    'exam_type': scraper_config.get('exam_type', 'unknown')
                                }
                                updates.append(update)
                    except Exception as e:
                        self.logger.error(f"Error processing GATE date item: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing GATE important dates: {e}")
            
        return updates
    
    def _parse_highlights_section(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the highlights section for important links"""
        updates = []
        
        try:
            highlight_items = soup.select('.highlight-item')
            for item in highlight_items:
                try:
                    title_elem = item.select_one('.title a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')
                        
                        if self._is_relevant_gate_update(title):
                            update = {
                                'title': title,
                                'date': self._extract_date_from_title(title),
                                'url': self._resolve_url(href, scraper_config),
                                'content_summary': title,
                                'source': scraper_config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': scraper_config.get('priority', 'medium'),
                                'exam_type': scraper_config.get('exam_type', 'unknown')
                            }
                            updates.append(update)
                            
                except Exception as e:
                    self.logger.error(f"Error processing GATE highlight item: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing GATE highlights section: {e}")
            
        return updates
    
    def _is_relevant_gate_update(self, title: str) -> bool:
        """Check if GATE update is relevant"""
        relevant_keywords = [
            'gate', 'admit card', 'result', 'registration', 'application',
            'exam date', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'admission', 'cutoff', 'merit list', 'rank list',
            'interview', 'final selection', 'waiting list', 'seat allotment',
            'qualifying criteria', 'eligibility', 'syllabus', 'pattern',
            'portal', 'live', 'opens', 'closes', 'deadline', 'announcement',
            'engineering', 'science', 'paper', 'test', 'examination'
        ]
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in relevant_keywords)
    
    def _extract_date_from_title(self, title: str) -> str:
        """Extract date from title if present"""
        date_patterns = [
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group()
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _resolve_url(self, url: str, scraper_config: Dict[str, Any]) -> str:
        """Resolve relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        from urllib.parse import urljoin
        return urljoin(scraper_config['url'], url)


class JSONAPIPlugin(BasePlugin):
    """
    Plugin for parsing JSON API responses
    """
    
    version = "1.0.0"
    description = "Plugin for parsing JSON API responses"
    author = "Exam Scraper Team"
    
    def parse(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON API response"""
        updates = []
        
        try:
            # This plugin expects the response to be JSON, not HTML
            # The soup parameter might contain JSON data
            import json
            
            # Try to parse as JSON
            try:
                if hasattr(soup, 'get_text'):
                    json_data = json.loads(soup.get_text())
                else:
                    json_data = soup
            except:
                # If not JSON, return empty list
                return updates
            
            # Extract items using configured path
            api_config = scraper_config.get('api_config', {})
            data_path = api_config.get('data_path', '')
            field_mapping = api_config.get('field_mapping', {})
            
            items = self._extract_api_items(json_data, data_path)
            
            for item in items:
                update = self._convert_api_item_to_update(item, field_mapping, scraper_config)
                if update:
                    updates.append(update)
                    
        except Exception as e:
            self.logger.error(f"Error parsing JSON API: {e}")
            
        return updates
    
    def _extract_api_items(self, data: Dict, data_path: str) -> List[Dict]:
        """Extract items from API response using data path"""
        if not data_path:
            return [data] if isinstance(data, dict) else data if isinstance(data, list) else []
        
        current = data
        for key in data_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []
        
        return current if isinstance(current, list) else [current]
    
    def _convert_api_item_to_update(self, item: Dict, field_mapping: Dict, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API item to standard update format"""
        update = {
            'title': self._get_field_value(item, field_mapping.get('title', 'title')),
            'date': self._get_field_value(item, field_mapping.get('date', 'date')),
            'url': self._get_field_value(item, field_mapping.get('url', 'url')),
            'content_summary': self._get_field_value(item, field_mapping.get('content', 'content')),
            'source': scraper_config['name'],
            'scraped_at': datetime.now().isoformat(),
            'content_hash': hashlib.md5(str(item).encode('utf-8')).hexdigest(),
            'priority': scraper_config.get('priority', 'medium'),
            'exam_type': scraper_config.get('exam_type', 'unknown')
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
