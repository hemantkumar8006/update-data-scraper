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
            
            # 1. Parse "What's New" section - main updates
            whats_new_updates = self.parse_whats_new_section(soup)
            updates.extend(whats_new_updates)
            
            # 2. Parse ticker section - important announcements
            ticker_updates = self.parse_ticker_section(soup)
            updates.extend(ticker_updates)
            
            # 3. Parse forthcoming examinations section
            exam_updates = self.parse_forthcoming_exams(soup)
            updates.extend(exam_updates)
            
            # 4. Parse header announcements (static links in view-header)
            header_updates = self.parse_header_announcements(soup)
            updates.extend(header_updates)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error scraping UPSC website: {e}")
            return []

    def parse_whats_new_section(self, soup):
        """Parse the 'What's New' section for updates"""
        updates = []
        try:
            # Find the main "What's New" view content
            view_content = soup.select_one('.view-what-new .view-content')
            if not view_content:
                return updates
            
            # Parse each views-row in the content
            rows = view_content.select('.views-row')
            for row in rows[:20]:  # Limit to 20 most recent
                try:
                    # Look for exam name field
                    exam_name_field = row.select_one('.views-field-field-exam-name')
                    if exam_name_field:
                        link_elem = exam_name_field.select_one('a')
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                            href = link_elem.get('href', '')
                            
                            if self.is_relevant_upsc_update(title):
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
                    
                    # Also check for post/vacancy field
                    post_field = row.select_one('.views-field-field-name-of-post-vaccancy')
                    if post_field:
                        link_elem = post_field.select_one('a')
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                            href = link_elem.get('href', '')
                            
                            if self.is_relevant_upsc_update(title) and len(title) > 10:
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
                    self.logger.error(f"Error processing What's New row: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing What's New section: {e}")
            
        return updates

    def parse_ticker_section(self, soup):
        """Parse the ticker section for important announcements"""
        updates = []
        try:
            # Find the ticker view
            ticker_view = soup.select_one('.view-ticker .view-content')
            if not ticker_view:
                return updates
            
            # Parse ticker table rows
            table_rows = ticker_view.select('th.views-field-title')
            for row in table_rows:
                try:
                    link_elem = row.select_one('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        href = link_elem.get('href', '')
                        
                        if self.is_relevant_upsc_update(title) and len(title) > 15:
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
                    self.logger.error(f"Error processing ticker row: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing ticker section: {e}")
            
        return updates

    def parse_forthcoming_exams(self, soup):
        """Parse the forthcoming examinations section"""
        updates = []
        try:
            # Find the forthcoming exams view
            exam_view = soup.select_one('.view-exams .view-content')
            if not exam_view:
                return updates
            
            # Parse exam rows
            exam_rows = exam_view.select('.views-row')
            for row in exam_rows:
                try:
                    exam_field = row.select_one('.views-field-field-exam-name')
                    if exam_field:
                        link_elem = exam_field.select_one('a')
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                            href = link_elem.get('href', '')
                            
                            if self.is_relevant_upsc_update(title):
                                update = {
                                    'title': f"Forthcoming: {title}",
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
                    self.logger.error(f"Error processing forthcoming exam row: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing forthcoming exams: {e}")
            
        return updates

    def parse_header_announcements(self, soup):
        """Parse header announcements from view-header"""
        updates = []
        try:
            # Find header announcements in the What's New view-header
            header_links = soup.select('.view-what-new .view-header a')
            for link in header_links:
                try:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if self.is_relevant_upsc_update(title) and len(title) > 20:
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
                    self.logger.error(f"Error processing header announcement: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing header announcements: {e}")
            
        return updates

    def is_relevant_upsc_update(self, title):
        """Check if UPSC update is relevant"""
        relevant_keywords = [
            'upsc', 'civil services', 'ias', 'ips', 'ifs', 'irs', 'exam', 'notification',
            'result', 'admit card', 'application', 'registration', 'important', 'schedule',
            'answer key', 'interview', 'personality test', 'final result', 'merit list',
            'cutoff', 'qualifying criteria', 'eligibility', 'syllabus', 'pattern',
            'preliminary', 'mains', 'optional', 'general studies', 'engineering services',
            'medical services', 'defence', 'academy', 'recruitment', 'advertisement',
            'corrigendum', 'addendum', 'notice', 'press note', 'written result',
            'interview schedule', 'final result', 'reserve list', 'marks', 'answer key'
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
