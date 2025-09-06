from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re


class UPSCScraper(BaseScraper):
    def scrape(self):
        """Scrape UPSC website"""
        try:
            response = self.fetch_page(self.config['url'])
            updates = self.parse_content(response.text)
            
            # Additional UPSC-specific parsing
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for specific UPSC elements
            news_items = soup.select('.news-item, .announcement-item, .update-item, .notice-item')
            for item in news_items[:15]:  # Limit to recent 15
                try:
                    title_elem = item.select_one('h3, h4, .title, .announcement-title, .news-title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if self.is_relevant_upsc_update(title):
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
                                'priority': self.config.get('priority', 'high')
                            }
                            updates.append(update)
                except Exception as e:
                    self.logger.error(f"Error processing UPSC item: {e}")
            
            # Look for important notices and circulars
            notices = soup.select('.important-notice, .circular, .notification, .alert')
            for notice in notices:
                try:
                    title = notice.get_text(strip=True)
                    if self.is_relevant_upsc_update(title) and len(title) > 20:
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
                    self.logger.error(f"Error processing UPSC notice: {e}")
            
            # Look for exam-related links
            exam_links = soup.select('a[href*="exam"], a[href*="notification"], a[href*="result"]')
            for link in exam_links[:10]:  # Limit to 10
                try:
                    title = link.get_text(strip=True)
                    if self.is_relevant_upsc_update(title) and len(title) > 10:
                        href = link.get('href', '')
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
                    self.logger.error(f"Error processing UPSC link: {e}")
                    
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping UPSC website: {e}")
            return []

    def is_relevant_upsc_update(self, title):
        """Check if UPSC update is relevant"""
        relevant_keywords = [
            'upsc', 'civil services', 'ias', 'ips', 'ifs', 'irs', 'exam', 'notification',
            'result', 'admit card', 'application', 'registration', 'important', 'schedule',
            'answer key', 'interview', 'personality test', 'final result', 'merit list',
            'cutoff', 'qualifying criteria', 'eligibility', 'syllabus', 'pattern',
            'preliminary', 'mains', 'optional', 'general studies'
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
