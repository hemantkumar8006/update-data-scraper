#!/usr/bin/env python3
"""
Database Clearing/Flushing Script for Exam Data Scraper

This script provides comprehensive options for clearing/flushing the database
and related data files. Use with caution as this will permanently delete data.

Usage:
    python clear_database.py --help
    python clear_database.py --all                    # Clear everything (with confirmation)
    python clear_database.py --db-only                # Clear only database tables
    python clear_database.py --json-only              # Clear only JSON files
    python clear_database.py --backups-only           # Clear only backup files
    python clear_database.py --notifications-only     # Clear only notification files
    python clear_database.py --older-than 7           # Clear data older than 7 days
    python clear_database.py --source nta             # Clear data from specific source
    python clear_database.py --exam-type JEE          # Clear data for specific exam type
"""

import os
import sys
import sqlite3
import shutil
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import DATABASE_URL, JSON_BACKUP_PATH
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Try to import NotificationManager, but allow script to proceed without it (and without SQLAlchemy)
NotificationManager = None
try:
    from data.notification_manager import NotificationManager as _NotificationManager
    NotificationManager = _NotificationManager
except Exception:
    # Likely missing optional deps like SQLAlchemy; we'll degrade gracefully
    NotificationManager = None


class DatabaseCleaner:
    """Comprehensive database and data cleaning utility"""
    
    def __init__(self):
        # Derive SQLite file path from DATABASE_URL for direct sqlite3 operations
        self.db_path = self._resolve_db_path_from_url(DATABASE_URL)
        self.backup_dir = JSON_BACKUP_PATH
        self.data_dir = "data"
        
        # File paths
        self.exam_data_file = os.path.join(self.data_dir, "exam_data.json")
        self.notifications_file = os.path.join(self.data_dir, "updated_notifications.json")
        self.notification_queue_file = os.path.join(self.data_dir, "notification_queue.json")
        
        # Initialize notification manager if available
        self.notification_manager = None
        if NotificationManager is not None:
            try:
                self.notification_manager = NotificationManager()
            except Exception:
                # If initialization fails (e.g., missing SQLAlchemy), continue without it
                self.notification_manager = None
        
        print(f"🗂️  Database Cleaner initialized")
        print(f"   - Database: {self.db_path}")
        print(f"   - Backup dir: {self.backup_dir}")
        print(f"   - Data dir: {self.data_dir}")
    
    def _resolve_db_path_from_url(self, database_url: str | None) -> str:
        """Resolve a filesystem path to the SQLite database from DATABASE_URL.

        Falls back to the legacy default path if URL is missing or not sqlite.
        """
        # Default fallback to legacy path
        default_path = os.path.join("data", "exam_updates.db")
        if not database_url:
            return default_path

        if not database_url.lower().startswith("sqlite:"):
            # Not a sqlite URL; we don't support direct file operations
            # for other engines here. Fall back to default to avoid crashes.
            return default_path

        # Parse URL to extract path
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(database_url)
            raw_path = unquote(parsed.path or "")
            # Handle leading slashes and Windows drive letters
            # Examples:
            #  - sqlite:///data/exam_updates.db  -> /data/exam_updates.db (relative)
            #  - sqlite:////C:/path/to/db.db     -> /C:/path/to/db.db (absolute on Windows)
            #  - sqlite://///mnt/data/db.db      -> //mnt/data/db.db (absolute on Unix)
            path_candidate = raw_path
            if os.name == 'nt' and len(path_candidate) >= 3 and path_candidate[0] == '/' and path_candidate[2] == ':':
                # Strip leading slash before drive letter, e.g. /C:/...
                path_candidate = path_candidate[1:]

            # Make relative paths relative to project root (where this script lives)
            project_root = os.path.dirname(os.path.abspath(__file__))
            normalized = path_candidate.lstrip('/') if os.name != 'nt' else path_candidate
            if not os.path.isabs(normalized):
                return os.path.join(project_root, normalized)
            return normalized
        except Exception:
            return default_path

    def get_database_stats(self):
        """Get current database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM updates")
            updates_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scraping_log")
            logs_count = cursor.fetchone()[0]
            
            # Get database size
            db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            
            conn.close()
            
            return {
                'updates_count': updates_count,
                'logs_count': logs_count,
                'db_size_mb': round(db_size, 2)
            }
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return None
    
    def get_file_stats(self):
        """Get statistics about data files"""
        stats = {}
        
        # Check JSON files
        files_to_check = [
            self.exam_data_file,
            self.notifications_file,
            self.notification_queue_file
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / 1024  # KB
                stats[os.path.basename(file_path)] = {
                    'exists': True,
                    'size_kb': round(size, 2)
                }
            else:
                stats[os.path.basename(file_path)] = {
                    'exists': False,
                    'size_kb': 0
                }
        
        # Check backup files
        backup_count = 0
        backup_size = 0
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    backup_count += 1
                    file_path = os.path.join(self.backup_dir, file)
                    backup_size += os.path.getsize(file_path)
        
        stats['backups'] = {
            'count': backup_count,
            'size_kb': round(backup_size / 1024, 2)
        }
        
        return stats
    
    def show_current_status(self):
        """Display current database and file status"""
        print("\n📊 Current Status:")
        print("=" * 50)
        
        # Database stats
        db_stats = self.get_database_stats()
        if db_stats:
            print(f"🗄️  Database ({self.db_path}):")
            print(f"   - Updates: {db_stats['updates_count']:,} records")
            print(f"   - Logs: {db_stats['logs_count']:,} records")
            print(f"   - Size: {db_stats['db_size_mb']} MB")
        
        # File stats
        file_stats = self.get_file_stats()
        print(f"\n📁 Data Files:")
        for filename, info in file_stats.items():
            if filename == 'backups':
                print(f"   - {filename}: {info['count']} files ({info['size_kb']} KB)")
            else:
                status = "✅" if info['exists'] else "❌"
                print(f"   - {filename}: {status} ({info['size_kb']} KB)")
    
    def clear_database_tables(self, confirm=True):
        """Clear all database tables"""
        if confirm:
            response = input("\n⚠️  Are you sure you want to clear ALL database tables? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get counts before deletion
            cursor.execute("SELECT COUNT(*) FROM updates")
            updates_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scraping_log")
            logs_count = cursor.fetchone()[0]
            
            # Clear tables
            cursor.execute("DELETE FROM updates")
            cursor.execute("DELETE FROM scraping_log")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='updates'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='scraping_log'")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Database cleared successfully:")
            print(f"   - Removed {updates_count:,} update records")
            print(f"   - Removed {logs_count:,} log records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            return False
    
    def clear_database_by_date(self, days_old, confirm=True):
        """Clear database records older than specified days"""
        if confirm:
            response = input(f"\n⚠️  Clear records older than {days_old} days? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear old updates
            cursor.execute('''
                DELETE FROM updates 
                WHERE datetime(scraped_at) < datetime('now', '-{} days')
            '''.format(days_old))
            deleted_updates = cursor.rowcount
            
            # Clear old logs
            cursor.execute('''
                DELETE FROM scraping_log 
                WHERE datetime(scraped_at) < datetime('now', '-{} days')
            '''.format(days_old))
            deleted_logs = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"✅ Cleared old records:")
            print(f"   - Removed {deleted_updates:,} old update records")
            print(f"   - Removed {deleted_logs:,} old log records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing old records: {e}")
            return False
    
    def clear_database_by_source(self, source, confirm=True):
        """Clear database records from specific source"""
        if confirm:
            response = input(f"\n⚠️  Clear all records from source '{source}'? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear updates from source
            cursor.execute("DELETE FROM updates WHERE source = ?", (source,))
            deleted_updates = cursor.rowcount
            
            # Clear logs from source
            cursor.execute("DELETE FROM scraping_log WHERE source = ?", (source,))
            deleted_logs = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"✅ Cleared records from source '{source}':")
            print(f"   - Removed {deleted_updates:,} update records")
            print(f"   - Removed {deleted_logs:,} log records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing records from source: {e}")
            return False
    
    def clear_database_by_exam_type(self, exam_type, confirm=True):
        """Clear database records for specific exam type"""
        if confirm:
            response = input(f"\n⚠️  Clear all records for exam type '{exam_type}'? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear updates for exam type
            cursor.execute("DELETE FROM updates WHERE exam_type = ?", (exam_type,))
            deleted_updates = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"✅ Cleared records for exam type '{exam_type}':")
            print(f"   - Removed {deleted_updates:,} update records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing records for exam type: {e}")
            return False
    
    def clear_json_files(self, confirm=True):
        """Clear all JSON data files"""
        if confirm:
            response = input("\n⚠️  Clear all JSON data files? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        files_cleared = []
        
        # Clear main data files
        files_to_clear = [
            self.exam_data_file,
            self.notifications_file,
            self.notification_queue_file
        ]
        
        for file_path in files_to_clear:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_cleared.append(os.path.basename(file_path))
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")
        
        if files_cleared:
            print(f"✅ Cleared JSON files: {', '.join(files_cleared)}")
        else:
            print("ℹ️  No JSON files to clear")
        
        return len(files_cleared) > 0
    
    def clear_backup_files(self, confirm=True):
        """Clear all backup files"""
        if confirm:
            response = input("\n⚠️  Clear all backup files? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        if not os.path.exists(self.backup_dir):
            print("ℹ️  No backup directory found")
            return True
        
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    backup_files.append(file)
                    os.remove(os.path.join(self.backup_dir, file))
            
            if backup_files:
                print(f"✅ Cleared {len(backup_files)} backup files")
            else:
                print("ℹ️  No backup files to clear")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing backup files: {e}")
            return False
    
    def clear_notification_files(self, confirm=True):
        """Clear notification-related files"""
        if confirm:
            response = input("\n⚠️  Clear notification files? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
        
        files_cleared = []
        
        # Clear notification files
        notification_files = [
            self.notifications_file,
            self.notification_queue_file
        ]
        
        for file_path in notification_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_cleared.append(os.path.basename(file_path))
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")
        
        # Clear notification queue using manager if available
        if self.notification_manager is not None:
            try:
                self.notification_manager.clear_queue()
                files_cleared.append("notification_queue (via manager)")
            except Exception as e:
                print(f"⚠️  Error clearing notification queue: {e}")
        else:
            print("ℹ️  NotificationManager unavailable; cleared files only")
        
        if files_cleared:
            print(f"✅ Cleared notification files: {', '.join(files_cleared)}")
        else:
            print("ℹ️  No notification files to clear")
        
        return len(files_cleared) > 0
    
    def clear_all(self, confirm=True):
        """Clear everything - database, JSON files, and backups"""
        if confirm:
            print("\n🚨 DANGER: This will clear ALL data!")
            print("   - All database records")
            print("   - All JSON data files")
            print("   - All backup files")
            print("   - All notification files")
            response = input("\n⚠️  Are you absolutely sure? Type 'DELETE ALL' to confirm: ")
            if response != 'DELETE ALL':
                print("❌ Operation cancelled")
                return False
        
        print("\n🧹 Starting complete data cleanup...")
        
        success = True
        
        # Clear database
        print("\n1️⃣  Clearing database...")
        if not self.clear_database_tables(confirm=False):
            success = False
        
        # Clear JSON files
        print("\n2️⃣  Clearing JSON files...")
        if not self.clear_json_files(confirm=False):
            success = False
        
        # Clear backup files
        print("\n3️⃣  Clearing backup files...")
        if not self.clear_backup_files(confirm=False):
            success = False
        
        # Clear notification files
        print("\n4️⃣  Clearing notification files...")
        if not self.clear_notification_files(confirm=False):
            success = False
        
        if success:
            print("\n🎉 Complete cleanup finished successfully!")
        else:
            print("\n⚠️  Cleanup completed with some errors")
        
        return success
    
    def create_backup_before_clear(self, backup_name=None):
        """Create a backup before clearing data"""
        if backup_name is None:
            backup_name = f"backup_before_clear_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = os.path.join(self.data_dir, "emergency_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            # Backup database
            if os.path.exists(self.db_path):
                db_backup = os.path.join(backup_dir, f"{backup_name}.db")
                shutil.copy2(self.db_path, db_backup)
                print(f"📁 Database backed up to: {db_backup}")
            
            # Backup JSON files
            json_files = [
                self.exam_data_file,
                self.notifications_file,
                self.notification_queue_file
            ]
            
            for file_path in json_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    backup_path = os.path.join(backup_dir, f"{backup_name}_{filename}")
                    shutil.copy2(file_path, backup_path)
                    print(f"📁 {filename} backed up to: {backup_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Database Clearing/Flushing Script for Exam Data Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_database.py --status                    # Show current status
  python clear_database.py --all                       # Clear everything (with confirmation)
  python clear_database.py --db-only                   # Clear only database tables
  python clear_database.py --json-only                 # Clear only JSON files
  python clear_database.py --backups-only              # Clear only backup files
  python clear_database.py --notifications-only        # Clear only notification files
  python clear_database.py --older-than 7              # Clear data older than 7 days
  python clear_database.py --source nta                # Clear data from specific source
  python clear_database.py --exam-type JEE             # Clear data for specific exam type
  python clear_database.py --backup-before --all       # Create backup before clearing all
        """
    )
    
    # Action arguments
    parser.add_argument('--status', action='store_true', 
                       help='Show current database and file status')
    parser.add_argument('--all', action='store_true', 
                       help='Clear everything (database, JSON files, backups)')
    parser.add_argument('--db-only', action='store_true', 
                       help='Clear only database tables')
    parser.add_argument('--json-only', action='store_true', 
                       help='Clear only JSON data files')
    parser.add_argument('--backups-only', action='store_true', 
                       help='Clear only backup files')
    parser.add_argument('--notifications-only', action='store_true', 
                       help='Clear only notification files')
    
    # Selective clearing arguments
    parser.add_argument('--older-than', type=int, metavar='DAYS',
                       help='Clear records older than specified days')
    parser.add_argument('--source', type=str, metavar='SOURCE',
                       help='Clear records from specific source')
    parser.add_argument('--exam-type', type=str, metavar='TYPE',
                       help='Clear records for specific exam type')
    
    # Safety arguments
    parser.add_argument('--backup-before', action='store_true',
                       help='Create backup before clearing data')
    parser.add_argument('--no-confirm', action='store_true',
                       help='Skip confirmation prompts (use with caution)')
    parser.add_argument('--backup-name', type=str, metavar='NAME',
                       help='Custom name for backup (used with --backup-before)')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # Initialize cleaner
    try:
        cleaner = DatabaseCleaner()
    except Exception as e:
        print(f"❌ Failed to initialize database cleaner: {e}")
        return 1
    
    # Show status if requested
    if args.status:
        cleaner.show_current_status()
        return 0
    
    # Check if any clearing action is specified
    clearing_actions = [
        args.all, args.db_only, args.json_only, args.backups_only,
        args.notifications_only, args.older_than, args.source, args.exam_type
    ]
    
    if not any(clearing_actions):
        print("❌ No clearing action specified. Use --help for options.")
        return 1
    
    # Create backup if requested
    if args.backup_before:
        print("📁 Creating backup before clearing...")
        if not cleaner.create_backup_before_clear(args.backup_name):
            print("❌ Backup failed. Aborting.")
            return 1
    
    # Determine confirmation setting
    confirm = not args.no_confirm
    
    # Execute clearing actions
    success = True
    
    try:
        if args.all:
            success = cleaner.clear_all(confirm=confirm)
        
        elif args.db_only:
            success = cleaner.clear_database_tables(confirm=confirm)
        
        elif args.json_only:
            success = cleaner.clear_json_files(confirm=confirm)
        
        elif args.backups_only:
            success = cleaner.clear_backup_files(confirm=confirm)
        
        elif args.notifications_only:
            success = cleaner.clear_notification_files(confirm=confirm)
        
        elif args.older_than:
            success = cleaner.clear_database_by_date(args.older_than, confirm=confirm)
        
        elif args.source:
            success = cleaner.clear_database_by_source(args.source, confirm=confirm)
        
        elif args.exam_type:
            success = cleaner.clear_database_by_exam_type(args.exam_type, confirm=confirm)
        
        # Show final status
        print("\n📊 Final Status:")
        cleaner.show_current_status()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
