import unittest
import tempfile
import os
import sys
import sqlite3

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.storage import DataStorage


class TestDataStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, 'test.db')
        self.storage = DataStorage(self.test_db)
    
    def tearDown(self):
        # Clean up test database
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        os.rmdir(self.test_dir)
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Check if tables exist
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Check updates table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='updates'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check scraping_log table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_log'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_save_updates(self):
        """Test saving updates to database"""
        test_updates = [
            {
                'title': 'Test Update 1',
                'content_summary': 'Test summary 1',
                'source': 'Test Source',
                'scraped_at': '2025-01-01T10:00:00',
                'content_hash': 'hash1',
                'url': 'https://test.com/1',
                'date': '2025-01-01'
            },
            {
                'title': 'Test Update 2',
                'content_summary': 'Test summary 2',
                'source': 'Test Source',
                'scraped_at': '2025-01-01T10:01:00',
                'content_hash': 'hash2',
                'url': 'https://test.com/2',
                'date': '2025-01-01'
            }
        ]
        
        new_updates = self.storage.save_updates(test_updates)
        self.assertEqual(len(new_updates), 2)
        
        # Verify data was saved
        recent_updates = self.storage.get_recent_updates(24)
        self.assertEqual(len(recent_updates), 2)
    
    def test_duplicate_prevention(self):
        """Test duplicate content prevention"""
        test_update = {
            'title': 'Duplicate Test',
            'content_summary': 'Test summary',
            'source': 'Test Source',
            'scraped_at': '2025-01-01T10:00:00',
            'content_hash': 'duplicate_hash',
            'url': 'https://test.com',
            'date': '2025-01-01'
        }
        
        # Save first time
        new_updates = self.storage.save_updates([test_update])
        self.assertEqual(len(new_updates), 1)
        
        # Try to save duplicate
        new_updates = self.storage.save_updates([test_update])
        self.assertEqual(len(new_updates), 0)  # Should be 0 for duplicate
    
    def test_get_recent_updates(self):
        """Test getting recent updates"""
        # Add some test data
        test_updates = [
            {
                'title': f'Test Update {i}',
                'content_summary': f'Test summary {i}',
                'source': 'Test Source',
                'scraped_at': f'2025-01-01T10:0{i}:00',
                'content_hash': f'hash{i}',
                'url': f'https://test.com/{i}',
                'date': '2025-01-01'
            }
            for i in range(5)
        ]
        
        self.storage.save_updates(test_updates)
        
        # Test getting recent updates
        recent_updates = self.storage.get_recent_updates(24, limit=3)
        self.assertEqual(len(recent_updates), 3)
        
        # Test with different time range
        recent_updates = self.storage.get_recent_updates(1)  # Last 1 hour
        self.assertEqual(len(recent_updates), 0)  # Should be 0 as our data is old
    
    def test_get_updates_by_source(self):
        """Test getting updates by source"""
        test_updates = [
            {
                'title': 'Source 1 Update',
                'content_summary': 'Test summary',
                'source': 'Source 1',
                'scraped_at': '2025-01-01T10:00:00',
                'content_hash': 'hash1',
                'url': 'https://test.com/1',
                'date': '2025-01-01'
            },
            {
                'title': 'Source 2 Update',
                'content_summary': 'Test summary',
                'source': 'Source 2',
                'scraped_at': '2025-01-01T10:01:00',
                'content_hash': 'hash2',
                'url': 'https://test.com/2',
                'date': '2025-01-01'
            }
        ]
        
        self.storage.save_updates(test_updates)
        
        # Test getting updates by source
        source1_updates = self.storage.get_updates_by_source('Source 1')
        self.assertEqual(len(source1_updates), 1)
        self.assertEqual(source1_updates[0]['title'], 'Source 1 Update')
        
        source2_updates = self.storage.get_updates_by_source('Source 2')
        self.assertEqual(len(source2_updates), 1)
        self.assertEqual(source2_updates[0]['title'], 'Source 2 Update')
    
    def test_log_scraping_attempt(self):
        """Test logging scraping attempts"""
        # Log successful attempt
        self.storage.log_scraping_attempt(
            source='Test Source',
            status='success',
            updates_found=5,
            duration=10.5
        )
        
        # Log failed attempt
        self.storage.log_scraping_attempt(
            source='Test Source',
            status='error',
            updates_found=0,
            error_message='Test error',
            duration=5.0
        )
        
        # Verify logs were saved
        stats = self.storage.get_scraping_stats(24)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['source'], 'Test Source')
        self.assertEqual(stats[0]['total_attempts'], 2)
        self.assertEqual(stats[0]['successful_attempts'], 1)
    
    def test_check_existing_hash(self):
        """Test checking for existing content hash"""
        test_update = {
            'title': 'Hash Test',
            'content_summary': 'Test summary',
            'source': 'Test Source',
            'scraped_at': '2025-01-01T10:00:00',
            'content_hash': 'test_hash',
            'url': 'https://test.com',
            'date': '2025-01-01'
        }
        
        # Check before saving
        self.assertFalse(self.storage.check_existing_hash('test_hash'))
        
        # Save update
        self.storage.save_updates([test_update])
        
        # Check after saving
        self.assertTrue(self.storage.check_existing_hash('test_hash'))
    
    def test_database_integrity(self):
        """Test database integrity check"""
        # Should return True for a new, empty database
        self.assertTrue(self.storage.check_database_integrity())
    
    def test_database_stats(self):
        """Test getting database statistics"""
        # Add some test data
        test_updates = [
            {
                'title': f'Test Update {i}',
                'content_summary': f'Test summary {i}',
                'source': f'Source {i % 2}',  # Alternate between Source 0 and Source 1
                'scraped_at': f'2025-01-01T10:0{i}:00',
                'content_hash': f'hash{i}',
                'url': f'https://test.com/{i}',
                'date': '2025-01-01',
                'importance': 'High' if i % 2 == 0 else 'Medium'
            }
            for i in range(4)
        ]
        
        self.storage.save_updates(test_updates)
        
        # Get stats
        stats = self.storage.get_database_stats()
        
        self.assertEqual(stats['total_updates'], 4)
        self.assertEqual(len(stats['updates_by_source']), 2)
        self.assertEqual(len(stats['updates_by_importance']), 2)
        self.assertGreater(stats['database_size_mb'], 0)


if __name__ == '__main__':
    unittest.main()
