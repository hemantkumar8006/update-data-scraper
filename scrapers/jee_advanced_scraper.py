from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re


class JEEAdvancedScraper(BaseScraper):
    def scrape(self):
        """Scrape JEE Advanced website"""
        try:
            response = self.fetch_page(self.config['url'])
            updates = self.parse_content(response.text)
            
            # Additional JEE Advanced-specific parsing
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for specific JEE Advanced elements
            news_items = soup.select('.news-item, .announcement-item, .update-item')
            for item in news_items[:10]:  # Limit to recent 10
                try:
                    title_elem = item.select_one('h3, h4, .title, .announcement-title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if self.is_relevant_jee_advanced_update(title):
                            link_elem = item.select_one('a')
                            href = link_elem.get('href', '') if link_elem else ''
                            
                            date_elem = item.select_one('.date, .publish-date, .timestamp')
                            date = date_elem.get_text(strip=True) if date_elem else self.extract_date_from_title(title)
                            
                            update = {
                                'title': title,
                                'date': self.parse_date(date),
                                'url': self.resolve_url(href),
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'high')
                            }
                            updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing JEE Advanced item: {e}")
            
            # Look for notification banners
            banners = soup.select('.notification-banner, .alert-banner, .important-notice')
            for banner in banners:
                try:
                    title = banner.get_text(strip=True)
                    if self.is_relevant_jee_advanced_update(title) and len(title) > 10:
                        update = {
                            'title': title,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'url': self.config['url'],
                            'content_summary': title,
                            'source': self.config['name'],
                            'scraped_at': datetime.now().isoformat(),
                            'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                            'priority': self.config.get('priority', 'high')
                        }
                        updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing JEE Advanced banner: {e}")
                    
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping JEE Advanced website: {e}")
            return []

    def is_relevant_jee_advanced_update(self, title):
        """Check if JEE Advanced update is relevant"""
        relevant_keywords = [
            'jee advanced', 'admit card', 'result', 'registration', 'application',
            'exam date', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'seat allotment', 'cutoff', 'merit list', 'rank list',
            'qualifying criteria', 'eligibility'
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
