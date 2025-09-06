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
            
            # 1. Parse marquee section - main announcements
            marquee_updates = self.parse_marquee_section(soup)
            updates.extend(marquee_updates)
            
            # 2. Parse announcements section
            announcements_updates = self.parse_announcements_section(soup)
            updates.extend(announcements_updates)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping JEE Advanced website: {e}")
            return []

    def parse_marquee_section(self, soup):
        """Parse the marquee section for main announcements"""
        updates = []
        try:
            # Find the marquee element
            marquee = soup.select_one('marquee')
            if marquee:
                content = marquee.get_text(strip=True)
                if self.is_relevant_jee_advanced_update(content) and len(content) > 20:
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
            self.logger.error(f"Error parsing JEE Advanced marquee section: {e}")
            
        return updates

    def parse_announcements_section(self, soup):
        """Parse the announcements section"""
        updates = []
        try:
            # Find announcement items
            announcements = soup.select('.announcement__head')
            for announcement in announcements:
                try:
                    title = announcement.get_text(strip=True)
                    if self.is_relevant_jee_advanced_update(title):
                        # Find the parent container to get the full announcement
                        parent = announcement.find_parent()
                        if parent:
                            # Look for links in the announcement
                            link_elem = parent.select_one('a')
                            href = link_elem.get('href', '') if link_elem else ''
                            
                            # Look for date in the announcement
                            date_elem = parent.select_one('.font-monospace')
                            date_text = date_elem.get_text(strip=True) if date_elem else self.extract_date_from_title(title)
                            
                            update = {
                                'title': title,
                                'date': self.parse_date(date_text),
                                'url': self.resolve_url(href) if href else self.config['url'],
                                'content_summary': title,
                                'source': self.config['name'],
                                'scraped_at': datetime.now().isoformat(),
                                'content_hash': hashlib.md5(title.encode('utf-8')).hexdigest(),
                                'priority': self.config.get('priority', 'high')
                            }
                            updates.append(update)
                            
                except Exception as e:
                    self.logger.error(f"Error processing JEE Advanced announcement: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing JEE Advanced announcements section: {e}")
            
        return updates

    def is_relevant_jee_advanced_update(self, title):
        """Check if JEE Advanced update is relevant"""
        relevant_keywords = [
            'jee advanced', 'admit card', 'result', 'registration', 'application',
            'exam date', 'notification', 'important', 'schedule', 'answer key',
            'counselling', 'seat allotment', 'cutoff', 'merit list', 'rank list',
            'qualifying criteria', 'eligibility', 'scorecard', 'josaa', 'allotment',
            'round', 'deadline', 'withdrawal', 'aat', 'architecture', 'aptitude test',
            'candidate portal', 'question paper', 'provisional', 'final', 'response'
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
