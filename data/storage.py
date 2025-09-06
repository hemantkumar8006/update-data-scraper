import sqlite3
import json
import os
import shutil
import time
import logging
from datetime import datetime, timedelta
from config.settings import DATABASE_PATH, JSON_BACKUP_PATH


class DataStorage:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create updates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_summary TEXT,
                ai_summary TEXT,
                category TEXT,
                importance TEXT,
                urgency TEXT,
                action_required TEXT,
                key_dates TEXT,
                source TEXT NOT NULL,
                url TEXT,
                date TEXT,
                scraped_at TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                processed_by TEXT,
                priority TEXT,
                is_new BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_content_hash ON updates(content_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source ON updates(source)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scraped_at ON updates(scraped_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_importance ON updates(importance)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON updates(category)
        ''')
        
        # Create scraping_log table for monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                updates_found INTEGER DEFAULT 0,
                error_message TEXT,
                duration_seconds REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Database initialized successfully")

    def save_updates(self, updates):
        """Save updates to database with duplicate detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_updates = []
        
        for update in updates:
            try:
                # Check if update already exists
                cursor.execute('SELECT id FROM updates WHERE content_hash = ?', (update['content_hash'],))
                if cursor.fetchone():
                    continue  # Skip duplicate
                
                cursor.execute('''
                    INSERT INTO updates 
                    (title, content_summary, ai_summary, category, importance, urgency,
                     action_required, key_dates, source, url, date, scraped_at, 
                     content_hash, processed_by, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    update['title'],
                    update.get('content_summary', ''),
                    update.get('ai_summary', ''),
                    update.get('category', ''),
                    update.get('importance', ''),
                    update.get('urgency', ''),
                    update.get('action_required', ''),
                    update.get('key_dates', ''),
                    update['source'],
                    update.get('url', ''),
                    update.get('date', ''),
                    update['scraped_at'],
                    update['content_hash'],
                    update.get('processed_by', ''),
                    update.get('priority', 'medium')
                ))
                
                if cursor.rowcount > 0:
                    new_updates.append(update)
                    
            except sqlite3.Error as e:
                self.logger.error(f"Database error saving update: {e}")
                
        conn.commit()
        conn.close()
        
        # Save JSON backup
        if new_updates:
            self.save_json_backup(new_updates)
            
        return new_updates

    def save_json_backup(self, updates):
        """Save updates as JSON backup"""
        backup_dir = JSON_BACKUP_PATH
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{backup_dir}/updates_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(updates, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON backup saved: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON backup: {e}")

    def get_recent_updates(self, hours=24, limit=100):
        """Get recent updates from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM updates 
            WHERE datetime(scraped_at) > datetime('now', '-{} hours')
            ORDER BY scraped_at DESC
            LIMIT ?
        '''.format(hours), (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        updates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return updates

    def get_updates_by_source(self, source, limit=50):
        """Get updates from specific source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM updates 
            WHERE source = ?
            ORDER BY scraped_at DESC
            LIMIT ?
        ''', (source, limit))
        
        columns = [desc[0] for desc in cursor.description]
        updates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return updates

    def get_updates_by_importance(self, importance, limit=50):
        """Get updates by importance level"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM updates 
            WHERE importance = ?
            ORDER BY scraped_at DESC
            LIMIT ?
        ''', (importance, limit))
        
        columns = [desc[0] for desc in cursor.description]
        updates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return updates

    def check_existing_hash(self, content_hash):
        """Check if content hash exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM updates WHERE content_hash = ?', (content_hash,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists

    def log_scraping_attempt(self, source, status, updates_found=0, error_message=None, duration=None):
        """Log scraping attempt for monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_log 
            (source, status, updates_found, error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (source, status, updates_found, error_message, duration))
        
        conn.commit()
        conn.close()

    def get_scraping_stats(self, hours=24):
        """Get scraping statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                source,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_attempts,
                SUM(updates_found) as total_updates,
                AVG(duration_seconds) as avg_duration
            FROM scraping_log 
            WHERE datetime(scraped_at) > datetime('now', '-{} hours')
            GROUP BY source
        '''.format(hours))
        
        stats = cursor.fetchall()
        conn.close()
        
        return [
            {
                'source': row[0],
                'total_attempts': row[1],
                'successful_attempts': row[2],
                'total_updates': row[3],
                'avg_duration': row[4] if row[4] else 0
            }
            for row in stats
        ]

    def cleanup_old_data(self, days=30):
        """Clean up old data to prevent database bloat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old updates (keep only recent ones)
        cursor.execute('''
            DELETE FROM updates 
            WHERE datetime(scraped_at) < datetime('now', '-{} days')
        '''.format(days))
        
        deleted_updates = cursor.rowcount
        
        # Delete old scraping logs
        cursor.execute('''
            DELETE FROM scraping_log 
            WHERE datetime(scraped_at) < datetime('now', '-{} days')
        '''.format(days))
        
        deleted_logs = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleanup completed: {deleted_updates} old updates and {deleted_logs} old logs deleted")
        return deleted_updates, deleted_logs

    def robust_save(self, updates):
        """Save with database corruption handling"""
        try:
            return self.save_updates(updates)
        except sqlite3.DatabaseError as e:
            self.logger.error(f"Database error: {e}")
            
            # Try to backup and recreate database
            backup_path = f"{self.db_path}.backup_{int(time.time())}"
            try:
                shutil.copy2(self.db_path, backup_path)
                self.logger.info(f"Database backed up to: {backup_path}")
            except Exception as backup_error:
                self.logger.error(f"Backup failed: {backup_error}")
            
            # Reinitialize database
            try:
                os.remove(self.db_path)
                self.init_database()
                self.logger.info("Database reinitialized")
                
                # Retry save
                return self.save_updates(updates)
            except Exception as init_error:
                self.logger.error(f"Database reinitialization failed: {init_error}")
                raise

    def check_database_integrity(self):
        """Check SQLite database integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            return result == "ok"
        except Exception as e:
            self.logger.error(f"Database integrity check failed: {e}")
            return False

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total updates count
        cursor.execute('SELECT COUNT(*) FROM updates')
        total_updates = cursor.fetchone()[0]
        
        # Get updates by source
        cursor.execute('''
            SELECT source, COUNT(*) 
            FROM updates 
            GROUP BY source
        ''')
        updates_by_source = dict(cursor.fetchall())
        
        # Get updates by importance
        cursor.execute('''
            SELECT importance, COUNT(*) 
            FROM updates 
            GROUP BY importance
        ''')
        updates_by_importance = dict(cursor.fetchall())
        
        # Get recent activity
        cursor.execute('''
            SELECT COUNT(*) 
            FROM updates 
            WHERE datetime(scraped_at) > datetime('now', '-24 hours')
        ''')
        recent_updates = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_updates': total_updates,
            'updates_by_source': updates_by_source,
            'updates_by_importance': updates_by_importance,
            'recent_updates_24h': recent_updates,
            'database_size_mb': round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
        }
