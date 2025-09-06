import schedule
import time
import threading
import logging
from config.settings import SCRAPE_INTERVAL


class Scheduler:
    def __init__(self, scraping_function):
        self.scraping_function = scraping_function
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_running = False
        self.scheduler_thread = None

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        
        # Schedule scraping every SCRAPE_INTERVAL minutes (configurable)
        schedule.every(SCRAPE_INTERVAL // 60).minutes.do(self.run_scraping)
        
        # Schedule daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.daily_cleanup)
        
        # Schedule weekly database optimization
        schedule.every().week.do(self.weekly_optimization)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started successfully")
        
        # Run initial scraping
        self.run_scraping()

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        self.logger.info("Scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def run_scraping(self):
        """Run the scraping function"""
        try:
            self.logger.info("Starting scheduled scraping cycle...")
            start_time = time.time()
            
            self.scraping_function()
            
            duration = time.time() - start_time
            self.logger.info(f"Scheduled scraping completed in {duration:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Scheduled scraping failed: {e}")

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
            conn = storage.db_path
            import sqlite3
            with sqlite3.connect(conn) as db:
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
