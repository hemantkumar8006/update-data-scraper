#!/usr/bin/env python3
"""
Smart scheduler that integrates with the smart export system
"""

import schedule
import time
import threading
import logging
from datetime import datetime
from config.settings import SCRAPE_INTERVAL

# Handle imports
try:
    from .server import MCPExamScrapingServer
    from ..data.smart_export import SmartExporter
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_server.server import MCPExamScrapingServer
    from data.smart_export import SmartExporter


class SmartScheduler:
    """Smart scheduler that maintains a single JSON file with incremental updates"""
    
    def __init__(self, scraping_function, export_file="data/exam_data.json"):
        self.scraping_function = scraping_function
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_running = False
        self.scheduler_thread = None
        self.smart_exporter = SmartExporter(export_file=export_file)
        self.is_first_run = True

    def start(self):
        """Start the smart scheduler"""
        if self.is_running:
            self.logger.warning("Smart scheduler is already running")
            return
        
        self.is_running = True
        
        # Schedule scraping every SCRAPE_INTERVAL minutes
        schedule.every(SCRAPE_INTERVAL // 60).minutes.do(self.run_smart_scraping)
        
        # Schedule daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.daily_cleanup)
        
        # Schedule weekly database optimization
        schedule.every().week.do(self.weekly_optimization)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Smart scheduler started successfully")
        
        # Run initial fresh scrape
        self.run_fresh_scrape()

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        self.logger.info("Smart scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Smart scheduler error: {e}")
                time.sleep(60)

    def run_fresh_scrape(self):
        """Run fresh scrape and create initial file"""
        try:
            self.logger.info("Starting fresh scrape...")
            start_time = time.time()
            
            # Run the scraping function to get fresh data
            scraping_result = self.scraping_function()
            
            # Create fresh export file
            filepath = self.smart_exporter.fresh_scrape_and_create_file()
            
            duration = time.time() - start_time
            self.logger.info(f"Fresh scrape completed in {duration:.2f} seconds")
            self.logger.info(f"Export file created: {filepath}")
            
            self.is_first_run = False
            
        except Exception as e:
            self.logger.error(f"Fresh scrape failed: {e}")

    def run_smart_scraping(self):
        """Run smart scraping with incremental updates"""
        try:
            self.logger.info("Starting smart scraping cycle...")
            start_time = time.time()
            
            # Run the scraping function to get new data
            scraping_result = self.scraping_function()
            
            # Perform incremental update
            filepath = self.smart_exporter.incremental_update()
            
            duration = time.time() - start_time
            self.logger.info(f"Smart scraping completed in {duration:.2f} seconds")
            self.logger.info(f"Export file updated: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Smart scraping failed: {e}")

    def daily_cleanup(self):
        """Daily maintenance tasks"""
        try:
            self.logger.info("Running daily cleanup...")
            
            # Import here to avoid circular imports
            from data.storage import DataStorage
            storage = DataStorage()
            
            # Clean up old data (keep last 30 days)
            deleted_updates, deleted_logs = storage.cleanup_old_data(days=30)
            
            # Check database integrity
            if not storage.check_database_integrity():
                self.logger.warning("Database integrity check failed")
            
            self.logger.info(f"Daily cleanup completed: {deleted_updates} updates and {deleted_logs} logs cleaned")
            
        except Exception as e:
            self.logger.error(f"Daily cleanup failed: {e}")

    def weekly_optimization(self):
        """Weekly database optimization"""
        try:
            self.logger.info("Running weekly optimization...")
            
            from data.storage import DataStorage
            storage = DataStorage()
            
            # Optimize database
            import sqlite3
            with sqlite3.connect(storage.db_path) as db:
                db.execute("VACUUM")
                db.execute("ANALYZE")
            
            self.logger.info("Weekly optimization completed")
            
        except Exception as e:
            self.logger.error(f"Weekly optimization failed: {e}")

    def get_next_run_time(self):
        """Get the next scheduled run time"""
        next_run = schedule.next_run()
        return next_run.isoformat() if next_run else None

    def get_schedule_info(self):
        """Get information about the current schedule"""
        jobs = schedule.get_jobs()
        return [
            {
                'job': str(job.job_func),
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'interval': str(job.interval) if hasattr(job, 'interval') else 'N/A'
            }
            for job in jobs
        ]

    def get_export_file_info(self):
        """Get information about the export file"""
        return self.smart_exporter.get_file_info()

    def force_fresh_scrape(self):
        """Force a fresh scrape (useful for manual triggers)"""
        self.run_fresh_scrape()

    def force_incremental_update(self):
        """Force an incremental update (useful for manual triggers)"""
        self.run_smart_scraping()
