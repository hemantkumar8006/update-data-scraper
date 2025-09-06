from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re


class CATScraper(BaseScraper):
    def scrape(self):
        """Scrape CAT IIM website"""
        try:
            response = self.fetch_page(self.config['url'])
            updates = self.parse_content(response.text)
            
            # Additional CAT-specific parsing
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for specific CAT elements
            news_items = soup.select('.news-item, .announcement, .update, .notice')
            for item in news_items[:12]:  # Limit to recent 12
                try:
                    title_elem = item.select_one('h3, h4, .title, .announcement-title, .news-title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if self.is_relevant_cat_update(title):
                            link_elem = item.select_one('a')
                            href = link_elem.get('href', '') if link_elem else ''
                            
                            date_elem = item.select_one('.date, .publish-date, .timestamp, .news-date')
                            date = date_elem.get_text(strip=True) if date_elem else self.extract_date_from_title(title)
                            
                            update = {
                                'title': title,
                                'date': self.parse_date(date),
                                'url': self.resolve_url(href),
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'medium')
                            }
                            updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing CAT item: {e}")
            
            # Look for important notices
            notices = soup.select('.important-notice, .urgent-notice, .alert-notice')
            for notice in notices:
                try:
                    title = notice.get_text(strip=True)
                    if self.is_relevant_cat_update(title) and len(title) > 15:
                        update = {
                            'title': title,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'url': self.config['url'],
                            'content_summary': title,
                            'source': self.config['name'],
                            'scraped_at': datetime.now().isoformat(),
                            'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                            'priority': self.config.get('priority', 'medium')
                        }
                        updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing CAT notice: {e}")
                    
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping CAT website: {e}")
            return []

    def is_relevant_cat_update(self, title):
        """Check if CAT update is relevant"""
        relevant_keywords = [
            'cat', 'mba', 'admit card', 'result', 'registration', 'application',
            'exam date', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'admission', 'cutoff', 'merit list', 'rank list',
            'interview', 'gdpi', 'final selection', 'waiting list'
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
