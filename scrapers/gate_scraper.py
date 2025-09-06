from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re


class GATEScraper(BaseScraper):
    def scrape(self):
        """Scrape GATE website"""
        try:
            response = self.fetch_page(self.config['url'])
            updates = self.parse_content(response.text)
            
            # Additional GATE-specific parsing
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 1. Parse ticker section - main announcements
            ticker_updates = self.parse_ticker_section(soup)
            updates.extend(ticker_updates)
            
            # 2. Parse important dates section
            dates_updates = self.parse_important_dates(soup)
            updates.extend(dates_updates)
            
            # 3. Parse highlights section
            highlights_updates = self.parse_highlights_section(soup)
            updates.extend(highlights_updates)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping GATE website: {e}")
            return []

    def parse_ticker_section(self, soup):
        """Parse the ticker section for main announcements"""
        updates = []
        try:
            # Find the ticker marquee
            ticker_marquee = soup.select_one('.ticker .news .news-content')
            if ticker_marquee:
                content = ticker_marquee.get_text(strip=True)
                if self.is_relevant_gate_update(content) and len(content) > 20:
                    update = {
                        'title': content,
                        'date': self.extract_date_from_title(content),
                        'url': self.config['url'],
                        'content_summary': content,
                        'source': self.config['name'],
                        'scraped_at': datetime.now().isoformat(),
                        'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                        'priority': self.config.get('priority', 'high')
                    }
                    updates.append(update)
                    
        except Exception as e:
            self.logger.error(f"Error parsing GATE ticker section: {e}")
            
        return updates

    def parse_important_dates(self, soup):
        """Parse the important dates section"""
        updates = []
        try:
            # Find the important dates section
            dates_section = soup.select_one('.imp-dates-item')
            if dates_section:
                # Parse each date item
                date_items = dates_section.select('li')
                for item in date_items:
                    try:
                        # Look for date spans with text-warning class
                        date_span = item.select_one('.text-warning')
                        if date_span:
                            date_text = date_span.get_text(strip=True)
                            # Get the description text
                            description = item.get_text(strip=True)
                            if self.is_relevant_gate_update(description) and len(description) > 20:
                                update = {
                                    'title': f"Important Date: {description}",
                                    'date': self.parse_date(date_text),
                                    'url': self.config['url'],
                                    'content_summary': description,
                                    'source': self.config['name'],
                                    'scraped_at': datetime.now().isoformat(),
                                    'content_hash': hashlib.md5(description.encode('utf-8')).hexdigest(),
                                    'priority': self.config.get('priority', 'high')
                                }
                                updates.append(update)
                    except Exception as e:
                        self.logger.error(f"Error processing GATE date item: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing GATE important dates: {e}")
            
        return updates

    def parse_highlights_section(self, soup):
        """Parse the highlights section for important links"""
        updates = []
        try:
            # Find highlight items
            highlight_items = soup.select('.highlight-item')
            for item in highlight_items:
                try:
                    title_elem = item.select_one('.title a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')
                        
                        if self.is_relevant_gate_update(title):
                            update = {
                                'title': title,
                                'date': self.extract_date_from_title(title),
                                'url': self.resolve_url(href),
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'medium')
                            }
                            updates.append(update)
                            
                except Exception as e:
                    self.logger.error(f"Error processing GATE highlight item: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing GATE highlights section: {e}")
            
        return updates

    def is_relevant_gate_update(self, title):
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
