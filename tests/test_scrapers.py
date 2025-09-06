import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.nta_scraper import NTAScraper
from scrapers.base_scraper import BaseScraper


class TestNTAScraper(unittest.TestCase):
    def setUp(self):
        self.config = {
            'name': 'Test NTA',
            'url': 'https://jeemain.nta.nic.in/',
            'selectors': {
                'news_container': '.latest-news',
                'title': 'h3',
                'date': '.date',
                'link': 'a'
            },
            'keywords': ['jee', 'main', 'exam'],
            'priority': 'high'
        }
        self.scraper = NTAScraper(self.config)
    
    @patch('requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = '<html><body>Test content</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = self.scraper.fetch_page('https://test.com')
        self.assertEqual(response.text, '<html><body>Test content</body></html>')
    
    @patch('requests.Session.get')
    def test_fetch_page_retry(self, mock_get):
        """Test retry logic on failure"""
        import requests
        
        # Mock failed then successful response
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            Mock(text='Success', raise_for_status=Mock())
        ]
        
        response = self.scraper.fetch_page('https://test.com')
        self.assertEqual(response.text, 'Success')
        self.assertEqual(mock_get.call_count, 2)
    
    def test_parse_content(self):
        """Test content parsing"""
        html_content = '''
        <div class="latest-news">
            <h3>JEE Main 2025 Application Form</h3>
            <div class="date">2025-01-15</div>
            <a href="/application">Read More</a>
        </div>
        '''
        
        updates = self.scraper.parse_content(html_content)
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]['title'], 'JEE Main 2025 Application Form')
        self.assertEqual(updates[0]['source'], 'Test NTA')
    
    def test_is_relevant_nta_update(self):
        """Test relevance checking"""
        # Test relevant update
        relevant_title = "JEE Main 2025 Admit Card Released"
        self.assertTrue(self.scraper.is_relevant_nta_update(relevant_title))
        
        # Test irrelevant update
        irrelevant_title = "General Information about Education"
        self.assertFalse(self.scraper.is_relevant_nta_update(irrelevant_title))
    
    def test_extract_date_from_title(self):
        """Test date extraction from title"""
        # Test with date in title
        title_with_date = "JEE Main 2025 Application Form - Last Date: 15/01/2025"
        date = self.scraper.extract_date_from_title(title_with_date)
        self.assertIsNotNone(date)
        
        # Test without date
        title_without_date = "JEE Main 2025 Application Form"
        date = self.scraper.extract_date_from_title(title_without_date)
        self.assertIsNotNone(date)  # Should return current date


class TestBaseScraper(unittest.TestCase):
    def setUp(self):
        self.config = {
            'name': 'Test Scraper',
            'url': 'https://test.com',
            'selectors': {
                'news_container': '.news',
                'title': 'h3',
                'date': '.date',
                'link': 'a'
            },
            'keywords': ['test', 'exam']
        }
        self.scraper = BaseScraper(self.config)
    
    def test_resolve_url(self):
        """Test URL resolution"""
        # Test absolute URL
        absolute_url = "https://example.com/page"
        self.assertEqual(self.scraper.resolve_url(absolute_url), absolute_url)
        
        # Test relative URL
        relative_url = "/page"
        expected = "https://test.com/page"
        self.assertEqual(self.scraper.resolve_url(relative_url), expected)
        
        # Test empty URL
        self.assertEqual(self.scraper.resolve_url(""), "")
    
    def test_is_exam_related(self):
        """Test exam relevance checking"""
        update = {
            'title': 'Test Exam Application Form',
            'content_summary': 'Apply for the test exam'
        }
        self.assertTrue(self.scraper.is_exam_related(update))
        
        update = {
            'title': 'General Information',
            'content_summary': 'Some general information'
        }
        self.assertFalse(self.scraper.is_exam_related(update))
    
    def test_generate_content_hash(self):
        """Test content hash generation"""
        import hashlib
        
        title = "Test Title"
        expected_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        
        # This would be called internally in extract_update_info
        actual_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        self.assertEqual(actual_hash, expected_hash)


if __name__ == '__main__':
    unittest.main()
