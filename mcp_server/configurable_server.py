"""
Configurable Server - Updated server that uses the new configurable scraper system
"""

import json
import logging
import time
from datetime import datetime
from scrapers.configurable_scraper import ConfigurableScraper
from plugins.base_plugin import PluginManager
from plugins.example_plugins import NTAAdvancedPlugin, GATEAdvancedPlugin, JSONAPIPlugin
from data.storage import DataStorage
from data.notification_manager import NotificationManager
from .scheduler import Scheduler


class ConfigurableExamScrapingServer:
    """
    Updated server that uses the configurable scraper system instead of individual scraper files.
    This makes the system scalable for any number of exams.
    """
    
    def __init__(self):
        self.storage = DataStorage()
        self.notification_manager = NotificationManager(self.storage)
        self.setup_logging()
        self.load_website_configs()
        self.scrapers = {}
        self.plugin_manager = self._setup_plugin_manager()
        self.init_scrapers()
        self.scheduler = Scheduler(self.scrape_all_websites)
        self.logger.info("Configurable Exam Scraping Server initialized")
    
    def _setup_plugin_manager(self) -> PluginManager:
        """Setup plugin manager with available plugins"""
        plugin_manager = PluginManager()
        
        # Register built-in plugins
        plugin_manager.register_plugin('nta_advanced', NTAAdvancedPlugin)
        plugin_manager.register_plugin('gate_advanced', GATEAdvancedPlugin)
        plugin_manager.register_plugin('json_api', JSONAPIPlugin)
        
        self.logger.info(f"Registered {len(plugin_manager.list_plugins())} plugins")
        return plugin_manager
    
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
        """Initialize scraper instances using the configurable system"""
        for website in self.website_configs['websites']:
            if not website.get('enabled', True):
                self.logger.info(f"Skipping disabled website: {website['name']}")
                continue
            
            try:
                # Use ConfigurableScraper for all websites
                scraper = ConfigurableScraper(website)
                self.scrapers[website['name']] = scraper
                self.logger.info(f"Initialized configurable scraper for {website['name']}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize scraper for {website['name']}: {e}")
    
    def scrape_all_websites(self):
        """Scrape all configured websites using the configurable system"""
        self.logger.info("Starting configurable scraping cycle...")
        all_new_updates = []
        scraping_stats = {}
        
        for name, scraper in self.scrapers.items():
            start_time = time.time()
            try:
                self.logger.info(f"Scraping {name} with configurable scraper...")
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
        
        # Process new updates with notification system
        notification_result = None
        if all_new_updates:
            self.logger.info(f"Processing {len(all_new_updates)} new updates with notification system...")
            try:
                notification_result = self.notification_manager.process_next_scrape_cycle(all_new_updates)
                self.logger.info(f"Notification processing completed: {notification_result['stats']['new_notifications']} new notifications")
            except Exception as e:
                self.logger.error(f"Error processing notifications: {e}")
        else:
            self.logger.info("No new updates found in this cycle")
            # Clear notifications since no new data
            self.notification_manager.clear_notifications()
        
        return {
            'new_updates_count': len(all_new_updates),
            'scraping_stats': scraping_stats,
            'notification_result': notification_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def start_scheduler(self):
        """Start the scheduling system"""
        self.scheduler.start()
        self.logger.info("Scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the scheduling system"""
        self.scheduler.stop()
        self.logger.info("Scheduler stopped")
    
    def get_status(self):
        """Get server status"""
        try:
            recent_updates = self.storage.get_recent_updates(24)
            scraping_stats = self.storage.get_scraping_stats(24)
            db_stats = self.storage.get_database_stats()
            
            return {
                'status': 'running',
                'server_type': 'configurable',
                'last_scrape': datetime.now().isoformat(),
                'total_scrapers': len(self.scrapers),
                'active_scrapers': list(self.scrapers.keys()),
                'recent_updates_24h': len(recent_updates),
                'scraping_stats_24h': scraping_stats,
                'database_stats': db_stats,
                'next_scheduled_run': self.scheduler.get_next_run_time(),
                'schedule_info': self.scheduler.get_schedule_info(),
                'available_plugins': self.plugin_manager.list_plugins()
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
    
    def initial_setup(self):
        """Step 1: Initial scrape and setup of notification system"""
        self.logger.info("Running initial setup...")
        try:
            result = self.notification_manager.initial_scrape_and_setup()
            self.logger.info("Initial setup completed successfully")
            return {
                'success': True,
                'result': result,
                'message': 'Initial setup completed'
            }
        except Exception as e:
            self.logger.error(f"Initial setup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Initial setup failed'
            }
    
    def get_notification_status(self):
        """Get current notification system status"""
        try:
            status = self.notification_manager.get_status()
            return {
                'success': True,
                'status': status
            }
        except Exception as e:
            self.logger.error(f"Error getting notification status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_notifications(self):
        """Clear the updated_notifications.json file"""
        try:
            self.notification_manager.clear_notifications()
            return {
                'success': True,
                'message': 'Notifications cleared successfully'
            }
        except Exception as e:
            self.logger.error(f"Error clearing notifications: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
    
    def get_plugin_info(self):
        """Get information about available plugins"""
        return {
            'available_plugins': self.plugin_manager.list_plugins(),
            'plugin_details': {
                name: self.plugin_manager.get_plugin_info(name)
                for name in self.plugin_manager.list_plugins()
            }
        }
    
    def test_scraper_config(self, config):
        """Test a scraper configuration"""
        try:
            scraper = ConfigurableScraper(config)
            updates = scraper.scrape()
            
            return {
                'success': True,
                'updates_found': len(updates),
                'sample_updates': updates[:3]  # First 3 updates as samples
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
