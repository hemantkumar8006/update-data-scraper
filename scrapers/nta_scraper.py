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
            
            # 1. Parse news ticker section
            ticker_updates = self.parse_news_ticker(soup)
            updates.extend(ticker_updates)
            
            # 2. Parse scrollable notices section
            notices_updates = self.parse_scrollable_notices(soup)
            updates.extend(notices_updates)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping NTA website: {e}")
            return []

    def parse_news_ticker(self, soup):
        """Parse the news ticker section"""
        updates = []
        try:
            # Find the news ticker slides
            ticker_slides = soup.select('.newsticker .slides li')
            for slide in ticker_slides:
                try:
                    # Get the content from the slide
                    content = slide.get_text(strip=True)
                    if self.is_relevant_nta_update(content) and len(content) > 20:
                        # Look for links in the slide
                        link_elem = slide.select_one('a')
                        href = link_elem.get('href', '') if link_elem else ''
                        
                        update = {
                            'title': content,
                            'date': self.extract_date_from_title(content),
                            'url': self.resolve_url(href) if href else self.config['url'],
                            'content_summary': content,
                            'source': self.config['name'],
                            'scraped_at': datetime.now().isoformat(),
                            'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                            'priority': self.config.get('priority', 'high')
                        }
                        updates.append(update)
                        
                except Exception as e:
                    self.logger.error(f"Error processing NTA ticker slide: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing NTA news ticker: {e}")
            
        return updates

    def parse_scrollable_notices(self, soup):
        """Parse the scrollable notices section"""
        updates = []
        try:
            # Find scrollable notices container
            notices_container = soup.select_one('.scrollable-notices')
            if notices_container:
                # Look for notice items within the container
                notice_items = notices_container.select('a, .notice-item, .update-item')
                for item in notice_items:
                    try:
                        title = item.get_text(strip=True)
                        if self.is_relevant_nta_update(title) and len(title) > 10:
                            href = item.get('href', '') if item.name == 'a' else ''
                            
                            update = {
                                'title': title,
                                'date': self.extract_date_from_title(title),
                                'url': self.resolve_url(href) if href else self.config['url'],
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'medium')
                            }
                            updates.append(update)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing NTA notice item: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing NTA scrollable notices: {e}")
            
        return updates

    def is_relevant_nta_update(self, title):
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
