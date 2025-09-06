from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re


class NTAScraper(BaseScraper):
    def scrape(self):
        """Scrape NTA JEE Main website"""
        try:
            response = self.fetch_page(self.config['url'])
            updates = self.parse_content(response.text)
            
            # Additional NTA-specific parsing
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for specific NTA elements
            notification_links = soup.select('.notification-list a, .latest-news a, .updates a')
            for link in notification_links[:15]:  # Limit to recent 15
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if self.is_relevant_nta_update(title):
                        update = {
                            'title': title,
                            'date': self.extract_date_from_title(title),
                            'url': self.resolve_url(href),
                            'content_summary': title,
                            'source': self.config['name'],
                            'scraped_at': datetime.now().isoformat(),
                            'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                            'priority': self.config.get('priority', 'high')
                        }
                        updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing NTA link: {e}")
            
            # Look for announcement sections
            announcements = soup.select('.announcement, .notice, .alert')
            for announcement in announcements:
                try:
                    title_elem = announcement.select_one('h3, h4, .title, .heading')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if self.is_relevant_nta_update(title):
                            link_elem = announcement.select_one('a')
                            href = link_elem.get('href', '') if link_elem else ''
                            
                            update = {
                                'title': title,
                                'date': self.extract_date_from_title(title),
                                'url': self.resolve_url(href),
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'high')
                            }
                            updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing NTA announcement: {e}")
                    
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping NTA website: {e}")
            return []

    def is_relevant_nta_update(self, title):
        """Check if NTA update is relevant"""
        relevant_keywords = [
            'admit card', 'hall ticket', 'application', 'result', 'exam date', 
            'registration', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'allotment', 'cutoff', 'merit list', 'rank list'
        ]
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in relevant_keywords)

    def extract_date_from_title(self, title):
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
