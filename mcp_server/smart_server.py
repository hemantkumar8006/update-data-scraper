#!/usr/bin/env python3
"""
Smart MCP Exam Scraping Server with file-based incremental updates
"""

import json
import logging
import time
from datetime import datetime
from scrapers import (
    NTAScraper, JEEAdvancedScraper, 
    GATEScraper, UPSCScraper
)
from data.storage import DataStorage
from .smart_scheduler import SmartScheduler
from config.settings import SCRAPE_INTERVAL


class SmartMCPExamScrapingServer:
    """Smart MCP Exam Scraping Server with incremental file updates"""
    
    def __init__(self, export_file="data/exam_data.json"):
        self.storage = DataStorage()
        self.export_file = export_file
        self.setup_logging()
        self.load_website_configs()
        self.scrapers = {}
        self.init_scrapers()
        self.scheduler = SmartScheduler(self.scrape_all_websites, export_file)
        self.logger.info("Smart MCP Exam Scraping Server initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_website_configs(self):
        """Load website configurations"""
        try:
            with open('config/websites.json', 'r') as f:
                self.website_configs = json.load(f)
            self.logger.info(f"Loaded {len(self.website_configs['websites'])} website configurations")
        except Exception as e:
            self.logger.error(f"Failed to load website configurations: {e}")
            self.website_configs = {'websites': []}

    def init_scrapers(self):
        """Initialize scraper instances"""
        scraper_classes = {
            'NTAScraper': NTAScraper,
            'JEEAdvancedScraper': JEEAdvancedScraper,
            'GATEScraper': GATEScraper,
            'UPSCScraper': UPSCScraper
        }
        
        for website in self.website_configs['websites']:
            if not website.get('enabled', True):
                self.logger.info(f"Skipping disabled website: {website['name']}")
                continue
                
            scraper_class = scraper_classes.get(website['scraper_class'])
            if scraper_class:
                try:
                    self.scrapers[website['name']] = scraper_class(website)
                    self.logger.info(f"Initialized scraper for {website['name']}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize scraper for {website['name']}: {e}")
            else:
                self.logger.warning(f"No scraper class found for {website['scraper_class']}")

    def scrape_all_websites(self):
        """Scrape all configured websites"""
        self.logger.info("Starting scraping cycle...")
        all_new_updates = []
        scraping_stats = {}
        
        for name, scraper in self.scrapers.items():
            start_time = time.time()
            try:
                self.logger.info(f"Scraping {name}...")
                updates = scraper.scrape()
                
                if updates:
                    self.logger.info(f"Found {len(updates)} updates from {name}")
                    
                    # Save raw scraped data directly to storage
                    new_updates = self.storage.save_updates(updates)
                    all_new_updates.extend(new_updates)
                    
                    # Log successful scraping
                    duration = time.time() - start_time
                    self.storage.log_scraping_attempt(
                        source=name,
                        status='success',
                        updates_found=len(new_updates),
                        duration=duration
                    )
                    
                    scraping_stats[name] = {
                        'status': 'success',
                        'updates_found': len(new_updates),
                        'duration': duration
                    }
                    
                else:
                    self.logger.info(f"No updates found from {name}")
                    
                    # Log successful scraping with no updates
                    duration = time.time() - start_time
                    self.storage.log_scraping_attempt(
                        source=name,
                        status='success',
                        updates_found=0,
                        duration=duration
                    )
                    
                    scraping_stats[name] = {
                        'status': 'success',
                        'updates_found': 0,
                        'duration': duration
                    }
                    
            except Exception as e:
                self.logger.error(f"Error scraping {name}: {e}")
                
                # Log failed scraping
                duration = time.time() - start_time
                self.storage.log_scraping_attempt(
                    source=name,
                    status='error',
                    updates_found=0,
                    error_message=str(e),
                    duration=duration
                )
                
                scraping_stats[name] = {
                    'status': 'error',
                    'updates_found': 0,
                    'duration': duration,
                    'error': str(e)
                }
        
        # Log new updates found
        if all_new_updates:
            self.logger.info(f"Total new updates found: {len(all_new_updates)}")
        else:
            self.logger.info("No new updates found in this cycle")
        
        return {
            'new_updates_count': len(all_new_updates),
            'scraping_stats': scraping_stats,
            'timestamp': datetime.now().isoformat()
        }

    def start_scheduler(self):
        """Start the smart scheduling system"""
        self.scheduler.start()
        self.logger.info("Smart scheduler started successfully")

    def stop_scheduler(self):
        """Stop the scheduling system"""
        self.scheduler.stop()
        self.logger.info("Smart scheduler stopped")

    def get_status(self):
        """Get server status"""
        try:
            recent_updates = self.storage.get_recent_updates(24)
            scraping_stats = self.storage.get_scraping_stats(24)
            db_stats = self.storage.get_database_stats()
            export_info = self.scheduler.get_export_file_info()
            
            return {
                'status': 'running',
                'last_scrape': datetime.now().isoformat(),
                'total_scrapers': len(self.scrapers),
                'active_scrapers': list(self.scrapers.keys()),
                'recent_updates_24h': len(recent_updates),
                'scraping_stats_24h': scraping_stats,
                'database_stats': db_stats,
                'export_file_info': export_info,
                'next_scheduled_run': self.scheduler.get_next_run_time(),
                'schedule_info': self.scheduler.get_schedule_info()
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_recent_updates(self, hours=24, limit=100):
        """Get recent updates"""
        return self.storage.get_recent_updates(hours, limit)

    def get_updates_by_source(self, source, limit=50):
        """Get updates from specific source"""
        return self.storage.get_updates_by_source(source, limit)

    def get_updates_by_exam_type(self, exam_type, limit=50):
        """Get updates by exam type"""
        return self.storage.get_updates_by_exam_type(exam_type, limit)

    def get_all_exam_types(self):
        """Get all available exam types with counts"""
        return self.storage.get_all_exam_types()

    def run_single_scrape(self):
        """Run scraping once without scheduling"""
        return self.scrape_all_websites()

    def force_fresh_export(self):
        """Force a fresh export"""
        return self.scheduler.force_fresh_scrape()

    def force_incremental_export(self):
        """Force an incremental export"""
        return self.scheduler.force_incremental_update()

    def get_export_file_info(self):
        """Get export file information"""
        return self.scheduler.get_export_file_info()

    def add_website(self, website_config):
        """Add new website to configuration"""
        try:
            self.website_configs['websites'].append(website_config)
            
            # Save updated configuration
            with open('config/websites.json', 'w') as f:
                json.dump(self.website_configs, f, indent=2)
            
            # Reinitialize scrapers
            self.init_scrapers()
            
            self.logger.info(f"Added new website: {website_config['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add website: {e}")
            return False

    def remove_website(self, website_name):
        """Remove website from configuration"""
        try:
            self.website_configs['websites'] = [
                w for w in self.website_configs['websites'] 
                if w['name'] != website_name
            ]
            
            # Save updated configuration
            with open('config/websites.json', 'w') as f:
                json.dump(self.website_configs, f, indent=2)
            
            # Remove from active scrapers
            if website_name in self.scrapers:
                del self.scrapers[website_name]
            
            self.logger.info(f"Removed website: {website_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove website: {e}")
            return False

    def enable_website(self, website_name):
        """Enable a website"""
        return self._toggle_website(website_name, True)

    def disable_website(self, website_name):
        """Disable a website"""
        return self._toggle_website(website_name, False)

    def _toggle_website(self, website_name, enabled):
        """Toggle website enabled/disabled status"""
        try:
            for website in self.website_configs['websites']:
                if website['name'] == website_name:
                    website['enabled'] = enabled
                    break
            
            # Save updated configuration
            with open('config/websites.json', 'w') as f:
                json.dump(self.website_configs, f, indent=2)
            
            # Reinitialize scrapers
            self.init_scrapers()
            
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"{website_name} {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to toggle website {website_name}: {e}")
            return False
