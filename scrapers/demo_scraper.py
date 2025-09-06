#!/usr/bin/env python3
"""
Demo Scraper for monitoring the local HTML demo page
This scraper monitors the demo_notifications.html file for changes and extracts notifications
"""

import json
import os
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class DemoScraper(BaseScraper):
    """Scraper for monitoring the demo HTML page"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.demo_file_path = config.get('demo_file_path', 'demo_notifications.html')
        self.last_hash = None
        self.last_check = None
        
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape the demo notifications from JSON file
        Returns list of notification updates
        """
        try:
            self.logger.info("Scraping demo notifications from JSON file")
            
            # Try to read from JSON file first (preferred method)
            json_file = 'demo_notifications.json'
            if os.path.exists(json_file):
                notifications = self._extract_from_json_file(json_file)
                if notifications:
                    self.logger.info(f"Found {len(notifications)} notifications from JSON file")
                    return notifications
            
            # Fallback: try to extract from HTML file
            if os.path.exists(self.demo_file_path):
                self.logger.info(f"Falling back to HTML parsing: {self.demo_file_path}")
                notifications = self._extract_from_html_file()
                self.logger.info(f"Found {len(notifications)} notifications from HTML file")
                return notifications
            
            self.logger.warning("No demo notifications found")
            return []
            
        except Exception as e:
            self.logger.error(f"Error scraping demo notifications: {e}")
            return []
    
    def _extract_from_json_file(self, json_file: str) -> List[Dict[str, Any]]:
        """Extract notifications from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            notifications = []
            if isinstance(data, list):
                for item in data:
                    notification = self._convert_js_notification(item)
                    if notification:
                        notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            self.logger.error(f"Error reading JSON file: {e}")
            return []
    
    def _extract_from_html_file(self) -> List[Dict[str, Any]]:
        """Extract notifications from HTML file (fallback method)"""
        try:
            with open(self.demo_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract notifications from localStorage data (if available)
            notifications = self._extract_notifications_from_html(soup)
            
            # Also try to extract from script tags
            script_notifications = self._extract_notifications_from_scripts(soup)
            
            # Combine and deduplicate
            all_notifications = notifications + script_notifications
            unique_notifications = self._deduplicate_notifications(all_notifications)
            
            return unique_notifications
            
        except Exception as e:
            self.logger.error(f"Error extracting from HTML file: {e}")
            return []
    
    def _extract_notifications_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract notifications from HTML structure (fallback method)"""
        notifications = []
        
        try:
            # Look for notification cards in the HTML
            notification_cards = soup.find_all('div', class_='notification-card')
            
            for card in notification_cards:
                notification = self._parse_notification_card(card)
                if notification:
                    notifications.append(notification)
                    
        except Exception as e:
            self.logger.error(f"Error extracting notifications from HTML: {e}")
        
        return notifications
    
    def _extract_notifications_from_scripts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract notifications from JavaScript localStorage data"""
        notifications = []
        
        try:
            # Look for script tags that might contain notification data
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    script_content = script.string
                    
                    # Look for localStorage.setItem calls with demoNotifications
                    if 'localStorage.setItem' in script_content and 'demoNotifications' in script_content:
                        # Extract the JSON data from localStorage.setItem
                        js_notifications = self._parse_localStorage_data(script_content)
                        notifications.extend(js_notifications)
                    
                    # Also look for direct notification arrays in the script
                    elif 'demoNotifications' in script_content or 'notifications' in script_content:
                        js_notifications = self._parse_js_notifications(script_content)
                        notifications.extend(js_notifications)
                        
        except Exception as e:
            self.logger.error(f"Error extracting notifications from scripts: {e}")
        
        return notifications
    
    def _parse_localStorage_data(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse localStorage.setItem data from JavaScript"""
        notifications = []
        
        try:
            import re
            
            # Look for localStorage.setItem('demoNotifications', '...')
            pattern = r"localStorage\.setItem\(['\"]demoNotifications['\"],\s*['\"](.*?)['\"]"
            matches = re.findall(pattern, script_content, re.DOTALL)
            
            for match in matches:
                try:
                    # Decode the JSON data
                    json_data = match.replace('\\"', '"').replace("\\'", "'")
                    data = json.loads(json_data)
                    
                    if isinstance(data, list):
                        for item in data:
                            notification = self._convert_js_notification(item)
                            if notification:
                                notifications.append(notification)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing localStorage data: {e}")
        
        return notifications
    
    def _parse_notification_card(self, card) -> Dict[str, Any]:
        """Parse a notification card element"""
        try:
            # Extract title
            title_elem = card.find(class_='notification-title')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract content
            content_elem = card.find(class_='notification-content')
            content = content_elem.get_text(strip=True) if content_elem else ''
            
            # Extract exam type from class
            exam_type = 'jee'  # default
            for class_name in card.get('class', []):
                if class_name in ['jee', 'gate', 'jee_adv', 'upsc']:
                    exam_type = class_name
                    break
            
            # Extract meta information
            meta_items = card.find_all(class_='meta-item')
            source = 'Demo'
            priority = 'medium'
            
            for meta in meta_items:
                meta_text = meta.get_text(strip=True)
                if meta_text.upper() in ['JEE', 'GATE', 'JEE_ADV', 'UPSC']:
                    exam_type = meta_text.lower().replace('_', '_')
                elif meta_text.lower() in ['high', 'medium', 'low']:
                    priority = meta_text.lower()
                elif meta_text not in ['JEE', 'GATE', 'JEE_ADV', 'UPSC'] and len(meta_text) > 2:
                    source = meta_text
            
            # Extract URL if available
            url_elem = card.find('a', href=True)
            url = url_elem['href'] if url_elem else ''
            
            if not title or not content:
                return None
            
            # Generate content hash
            content_hash = self._generate_content_hash(title + content)
            
            return {
                'id': f"demo_{int(time.time())}_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                'title': title,
                'content': content,
                'content_summary': content[:200] + '...' if len(content) > 200 else content,
                'source': source,
                'url': url,
                'exam_type': exam_type,
                'priority': priority,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'scraped_at': datetime.now().isoformat(),
                'content_hash': content_hash,
                'scraper_type': 'demo'
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing notification card: {e}")
            return None
    
    def _parse_js_notifications(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse notifications from JavaScript content"""
        notifications = []
        
        try:
            # This is a simplified parser - in a real scenario, you might need more sophisticated parsing
            # Look for notification objects in the JavaScript
            
            # Try to find JSON-like structures
            import re
            
            # Look for arrays of notification objects
            json_pattern = r'\[.*?\]'
            matches = re.findall(json_pattern, script_content, re.DOTALL)
            
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'title' in item:
                                notification = self._convert_js_notification(item)
                                if notification:
                                    notifications.append(notification)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing JS notifications: {e}")
        
        return notifications
    
    def _convert_js_notification(self, js_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JavaScript notification object to our format"""
        try:
            title = js_item.get('title', '')
            content = js_item.get('content', '')
            
            if not title or not content:
                return None
            
            content_hash = self._generate_content_hash(title + content)
            
            return {
                'id': f"demo_{int(time.time())}_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                'title': title,
                'content': content,
                'content_summary': content[:200] + '...' if len(content) > 200 else content,
                'source': js_item.get('source', 'Demo'),
                'url': js_item.get('url', ''),
                'exam_type': js_item.get('examType', 'jee'),
                'priority': js_item.get('priority', 'medium'),
                'date': js_item.get('date', datetime.now().strftime('%Y-%m-%d')),
                'scraped_at': datetime.now().isoformat(),
                'content_hash': content_hash,
                'scraper_type': 'demo'
            }
            
        except Exception as e:
            self.logger.error(f"Error converting JS notification: {e}")
            return None
    
    def _deduplicate_notifications(self, notifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate notifications based on content hash"""
        seen_hashes = set()
        unique_notifications = []
        
        for notification in notifications:
            content_hash = notification.get('content_hash')
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_notifications.append(notification)
        
        return unique_notifications
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def check_for_changes(self) -> bool:
        """
        Check if the demo file has changed since last check
        Returns True if changes detected
        """
        try:
            if not os.path.exists(self.demo_file_path):
                return False
            
            # Get file modification time
            mod_time = os.path.getmtime(self.demo_file_path)
            
            # Check if file was modified since last check
            if self.last_check is None or mod_time > self.last_check:
                self.last_check = mod_time
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for changes: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the demo file"""
        try:
            if not os.path.exists(self.demo_file_path):
                return {
                    'exists': False,
                    'path': self.demo_file_path
                }
            
            stat = os.stat(self.demo_file_path)
            return {
                'exists': True,
                'path': self.demo_file_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'last_check': self.last_check
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return {
                'exists': False,
                'path': self.demo_file_path,
                'error': str(e)
            }


def main():
    """Test the demo scraper"""
    config = {
        'name': 'Demo Scraper',
        'url': 'file://demo_notifications.html',
        'demo_file_path': 'demo_notifications.html',
        'enabled': True,
        'priority': 'high'
    }
    
    scraper = DemoScraper(config)
    
    print("Testing Demo Scraper...")
    print(f"File info: {scraper.get_file_info()}")
    
    notifications = scraper.scrape()
    print(f"Found {len(notifications)} notifications:")
    
    for i, notification in enumerate(notifications, 1):
        print(f"\n{i}. {notification['title']}")
        print(f"   Type: {notification['exam_type']}")
        print(f"   Source: {notification['source']}")
        print(f"   Content: {notification['content'][:100]}...")


if __name__ == '__main__':
    main()
