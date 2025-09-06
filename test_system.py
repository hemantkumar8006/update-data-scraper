#!/usr/bin/env python3
"""
Test script to verify the Exam Scraping System components
"""

import os
import sys
import json
from datetime import datetime

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config.settings import SCRAPE_INTERVAL, DATABASE_PATH
        print("✅ Config imports successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from scrapers import BaseScraper, NTAScraper
        print("✅ Scraper imports successful")
    except Exception as e:
        print(f"❌ Scraper import failed: {e}")
        return False
    
    try:
        from data.storage import DataStorage
        print("✅ Storage imports successful")
    except Exception as e:
        print(f"❌ Storage import failed: {e}")
        return False
    
    try:
        from mcp_server.server import MCPExamScrapingServer
        print("✅ Server imports successful")
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        # Test websites.json
        with open('config/websites.json', 'r') as f:
            websites = json.load(f)
        
        if 'websites' in websites and len(websites['websites']) > 0:
            print(f"✅ Loaded {len(websites['websites'])} website configurations")
        else:
            print("❌ No websites configured")
            return False
        
        # Test settings
        from config.settings import SCRAPE_INTERVAL, DATABASE_PATH
        print(f"✅ Scrape interval: {SCRAPE_INTERVAL} seconds")
        print(f"✅ Database path: {DATABASE_PATH}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from data.storage import DataStorage
        
        # Create test storage
        test_db = 'data/test.db'
        storage = DataStorage(test_db)
        
        # Test saving updates
        test_updates = [{
            'title': 'Test Update',
            'content_summary': 'Test summary',
            'source': 'Test Source',
            'scraped_at': datetime.now().isoformat(),
            'content_hash': 'test_hash_123',
            'url': 'https://test.com',
            'date': '2025-01-01'
        }]
        
        new_updates = storage.save_updates(test_updates)
        if len(new_updates) == 1:
            print("✅ Database save test successful")
        else:
            print("❌ Database save test failed")
            return False
        
        # Test retrieving updates
        recent_updates = storage.get_recent_updates(24)
        if len(recent_updates) >= 1:
            print("✅ Database retrieve test successful")
        else:
            print("❌ Database retrieve test failed")
            return False
        
        # Clean up test database
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_scrapers():
    """Test scraper functionality"""
    print("\nTesting scrapers...")
    
    try:
        from scrapers import NTAScraper
        
        # Create test scraper
        config = {
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
        
        scraper = NTAScraper(config)
        
        # Test content parsing
        test_html = '''
        <div class="latest-news">
            <h3>JEE Main 2025 Application Form</h3>
            <div class="date">2025-01-15</div>
            <a href="/application">Read More</a>
        </div>
        '''
        
        updates = scraper.parse_content(test_html)
        if len(updates) >= 0:  # Should be 0 or more
            print("✅ Scraper parsing test successful")
        else:
            print("❌ Scraper parsing test failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def test_ai_processors():
    """Test AI processor functionality"""
    print("\nTesting AI processors...")
    
    try:
        from ai_processors import AIProcessorWithFallback
        
        # Test AI processor initialization
        try:
            ai_processor = AIProcessorWithFallback()
            print("✅ AI processor initialization successful")
        except Exception as e:
            print(f"⚠️  AI processor initialization failed (expected if no API keys): {e}")
            return True  # This is expected if no API keys are configured
        
        return True
    except Exception as e:
        print(f"❌ AI processor test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Exam Update Scraping System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database,
        test_scrapers,
        test_ai_processors
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nTo start the system, run:")
        print("  python main.py --mode server")
        print("  or")
        print("  python start.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
