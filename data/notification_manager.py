import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Set
try:
    from .storage import DataStorage
    from ..utils.webhook_service import create_webhook_service
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.storage import DataStorage
    from utils.webhook_service import create_webhook_service


class NotificationManager:
    """Manages the updated_notifications.json file and data comparison logic"""
    
    def __init__(self, storage: DataStorage = None, notification_file: str = "data/updated_notifications.json"):
        self.storage = storage or DataStorage()
        self.notification_file = notification_file
        self.main_data_file = "data/exam_data.json"
        self.backup_dir = "data/backups"
        
        # Initialize webhook service
        self.webhook_service = create_webhook_service()
        
        # Initialize notification queue (lazy import to avoid circular dependency)
        self.notification_queue = None
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.notification_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.main_data_file), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _get_notification_queue(self):
        """Get notification queue with lazy initialization"""
        if self.notification_queue is None:
            try:
                from .notification_queue import create_notification_queue
            except ImportError:
                from data.notification_queue import create_notification_queue
            self.notification_queue = create_notification_queue(self)
        return self.notification_queue
    
    def get_existing_data(self) -> Dict[str, Any]:
        """Get existing data from the main exam_data.json file"""
        if not os.path.exists(self.main_data_file):
            return {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_notification": 0,
                "last_updated": None,
                "last_scrape": None
            }
        
        try:
            with open(self.main_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading existing data: {e}")
            return {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_notification": 0,
                "last_updated": None,
                "last_scrape": None
            }
    
    def get_existing_hashes(self, data: Dict[str, Any]) -> Set[str]:
        """Get all existing content hashes from the data"""
        hashes = set()
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            for item in data.get(category, []):
                if 'content_hash' in item:
                    hashes.add(item['content_hash'])
        return hashes
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get current notification data"""
        if not os.path.exists(self.notification_file):
            return {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_new_notifications": 0,
                "last_updated": None,
                "scrape_timestamp": None
            }
        
        try:
            with open(self.notification_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading notification data: {e}")
            return {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_new_notifications": 0,
                "last_updated": None,
                "scrape_timestamp": None
            }
    
    def clear_notifications(self) -> None:
        """Clear the updated_notifications.json file"""
        try:
            if os.path.exists(self.notification_file):
                os.remove(self.notification_file)
            print("✅ Cleared updated_notifications.json")
        except Exception as e:
            print(f"❌ Error clearing notifications: {e}")
    
    def determine_category(self, update: Dict[str, Any]) -> str:
        """Determine the correct category for an update"""
        exam_type = update.get('exam_type', '').lower()
        source = update.get('source', '').lower()
        
        # Check for JEE Advanced first (more specific)
        if ('jee advanced' in source or 'jeeadv' in source or 
            'jee advanced' in exam_type or 'jeeadv' in exam_type):
            return "jee_adv"
        
        # Check for GATE
        elif (exam_type == 'gate' or 'gate' in source or 
              'gate' in exam_type):
            return "gate"
        
        # Check for UPSC
        elif (exam_type == 'upsc' or 'upsc' in source or 
              'upsc' in exam_type):
            return "upsc"
        
        # Check for JEE Main (or any JEE that's not Advanced)
        elif (exam_type == 'jee' or 'jee main' in source or 
              'jee' in exam_type or 'jee' in source):
            return "jee"
        
        # Default to JEE if unclear
        else:
            return "jee"
    
    def format_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Format update for frontend consumption"""
        return {
            "id": update.get('id'),
            "title": update.get('title', ''),
            "content_summary": update.get('content_summary', ''),
            "source": update.get('source', ''),
            "url": update.get('url', ''),
            "date": update.get('date', ''),
            "scraped_at": update.get('scraped_at', ''),
            "priority": update.get('priority', 'medium'),
            "content_hash": update.get('content_hash', '')
        }
    
    def save_notifications(self, notification_data: Dict[str, Any]) -> None:
        """Save notification data to updated_notifications.json"""
        try:
            with open(self.notification_file, 'w', encoding='utf-8') as f:
                json.dump(notification_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Notifications saved to: {self.notification_file}")
        except Exception as e:
            print(f"❌ Error saving notifications: {e}")
            raise
    
    def send_webhook_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send notifications to webhook API
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            Dictionary with webhook results
        """
        if not notifications:
            return {
                "success": True,
                "message": "No notifications to send",
                "webhook_results": []
            }
        
        try:
            print(f"📤 Sending {len(notifications)} notifications to webhook...")
            
            # Send notifications to webhook
            webhook_results = self.webhook_service.send_batch_notifications(notifications)
            
            # Log results
            successful = webhook_results["successful"]
            failed = webhook_results["failed"]
            
            if successful > 0:
                print(f"✅ {successful} notifications sent to webhook successfully")
            
            if failed > 0:
                print(f"⚠️  {failed} notifications failed to send to webhook")
            
            return {
                "success": failed == 0,  # Success if no failures
                "message": f"Sent {successful}/{len(notifications)} notifications to webhook",
                "webhook_results": webhook_results
            }
            
        except Exception as e:
            print(f"❌ Error sending webhook notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "webhook_results": []
            }
    
    def save_main_data(self, data: Dict[str, Any]) -> None:
        """Save main data to exam_data.json with backup"""
        # Create backup of existing file (only if it exists and has content)
        if os.path.exists(self.main_data_file) and os.path.getsize(self.main_data_file) > 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"exam_data_backup_{timestamp}.json")
            try:
                import shutil
                shutil.copy2(self.main_data_file, backup_file)
                print(f"📁 Backup created: {backup_file}")
                
                # Clean up old backups (keep only last 5)
                self.cleanup_old_backups()
                
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")
        
        # Save new data
        try:
            with open(self.main_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Main data saved to: {self.main_data_file}")
        except Exception as e:
            print(f"❌ Error saving main data: {e}")
            raise
    
    def cleanup_old_backups(self, keep_count: int = 5) -> None:
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # Get all backup files
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("exam_data_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups (keep only the most recent ones)
            if len(backup_files) > keep_count:
                files_to_remove = backup_files[keep_count:]
                for file_path, _ in files_to_remove:
                    try:
                        os.remove(file_path)
                        print(f"🗑️  Removed old backup: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"⚠️  Failed to remove backup {file_path}: {e}")
                        
        except Exception as e:
            print(f"⚠️  Error during backup cleanup: {e}")
    
    def cleanup_all_backups(self) -> None:
        """Remove all backup files (use with caution)"""
        try:
            if not os.path.exists(self.backup_dir):
                print("📁 No backup directory found")
                return
            
            removed_count = 0
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("exam_data_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        print(f"🗑️  Removed backup: {filename}")
                    except Exception as e:
                        print(f"⚠️  Failed to remove {filename}: {e}")
            
            print(f"✅ Cleanup complete: {removed_count} backup files removed")
            
        except Exception as e:
            print(f"❌ Error during backup cleanup: {e}")
    
    def process_new_scraped_data(self, new_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process new scraped data and compare with existing data
        Returns the updated main data and new notifications
        """
        print(f"🔄 Processing {len(new_updates)} new scraped updates...")
        
        # Get existing data
        existing_data = self.get_existing_data()
        existing_hashes = self.get_existing_hashes(existing_data)
        
        # Initialize notification data
        notification_data = {
            "jee": [],
            "gate": [],
            "jee_adv": [],
            "upsc": [],
            "total_new_notifications": 0,
            "last_updated": datetime.now().isoformat(),
            "scrape_timestamp": datetime.now().isoformat()
        }
        
        # Track statistics
        new_items_count = 0
        updated_items_count = 0
        
        # Process new updates
        for update in new_updates:
            content_hash = update.get('content_hash', '')
            
            if not content_hash:
                continue
            
            # Check if this is a new item
            if content_hash not in existing_hashes:
                category = self.determine_category(update)
                formatted_update = self.format_update(update)
                
                # Add to main data
                existing_data[category].append(formatted_update)
                
                # Add to notifications (only new items)
                notification_data[category].append(formatted_update)
                
                existing_hashes.add(content_hash)
                new_items_count += 1
            else:
                # Update existing item if needed
                category = self.determine_category(update)
                formatted_update = self.format_update(update)
                
                # Find and update existing item in main data
                for i, existing_item in enumerate(existing_data[category]):
                    if existing_item.get('content_hash') == content_hash:
                        existing_data[category][i] = formatted_update
                        updated_items_count += 1
                        break
        
        # Sort each category by scraped_at date (newest first)
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            existing_data[category].sort(
                key=lambda x: x.get('scraped_at', ''), 
                reverse=True
            )
            notification_data[category].sort(
                key=lambda x: x.get('scraped_at', ''), 
                reverse=True
            )
        
        # Update metadata for main data
        existing_data["total_notification"] = sum(
            len(existing_data[category]) for category in ["jee", "gate", "jee_adv", "upsc"]
        )
        existing_data["last_updated"] = datetime.now().isoformat()
        existing_data["last_scrape"] = datetime.now().isoformat()
        
        # Update metadata for notifications
        notification_data["total_new_notifications"] = sum(
            len(notification_data[category]) for category in ["jee", "gate", "jee_adv", "upsc"]
        )
        
        print(f"📊 Processing summary:")
        print(f"   - New items added: {new_items_count}")
        print(f"   - Items updated: {updated_items_count}")
        print(f"   - New notifications: {notification_data['total_new_notifications']}")
        print(f"   - Total notifications in main file: {existing_data['total_notification']}")
        
        return {
            'main_data': existing_data,
            'notification_data': notification_data,
            'stats': {
                'new_items': new_items_count,
                'updated_items': updated_items_count,
                'new_notifications': notification_data['total_new_notifications']
            }
        }
    
    def initial_scrape_and_setup(self) -> Dict[str, Any]:
        """
        Step 1: Initial scrape data and create main file
        """
        print("🚀 Step 1: Initial scrape and setup...")
        
        # Get all current data from database
        all_updates = self.storage.get_recent_updates(hours=24*365, limit=10000)
        
        if not all_updates:
            print("⚠️  No data found in database")
            all_updates = []
        
        # Create initial data structure
        initial_data = {
            "jee": [],
            "gate": [],
            "jee_adv": [],
            "upsc": [],
            "total_notification": len(all_updates),
            "last_updated": datetime.now().isoformat(),
            "last_scrape": datetime.now().isoformat()
        }
        
        # Categorize all updates
        for update in all_updates:
            category = self.determine_category(update)
            formatted_update = self.format_update(update)
            initial_data[category].append(formatted_update)
        
        # Sort each category by scraped_at date (newest first)
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            initial_data[category].sort(
                key=lambda x: x.get('scraped_at', ''), 
                reverse=True
            )
        
        # Save initial data
        self.save_main_data(initial_data)
        
        # Clear notifications (should be empty initially)
        self.clear_notifications()
        
        print(f"✅ Initial setup completed!")
        print(f"📊 Initial data summary:")
        print(f"   - JEE: {len(initial_data['jee'])} notifications")
        print(f"   - GATE: {len(initial_data['gate'])} notifications")
        print(f"   - JEE Advanced: {len(initial_data['jee_adv'])} notifications")
        print(f"   - UPSC: {len(initial_data['upsc'])} notifications")
        print(f"   - Total: {initial_data['total_notification']} notifications")
        
        return initial_data
    
    def process_next_scrape_cycle(self, new_scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 2-6: Process next scrape cycle with comparison logic
        """
        print("🔄 Processing next scrape cycle...")
        
        # Clear previous notifications
        self.clear_notifications()
        
        # Process new data
        result = self.process_new_scraped_data(new_scraped_data)
        
        # Save updated main data
        self.save_main_data(result['main_data'])
        
        # Save new notifications (only if there are new items)
        if result['notification_data']['total_new_notifications'] > 0:
            self.save_notifications(result['notification_data'])
            print(f"✅ New notifications saved: {result['notification_data']['total_new_notifications']} items")
            
            # Automatically send webhook notifications for new updates
            self._send_webhook_for_new_notifications(result['notification_data'])
        else:
            print("ℹ️  No new notifications to save")
        
        return result
    
    def _send_webhook_for_new_notifications(self, notification_data: Dict[str, Any]) -> None:
        """
        Automatically send webhook notifications for new updates using queue system
        
        Args:
            notification_data: Dictionary containing new notifications
        """
        try:
            # Collect all notifications from different exam types
            notifications = []
            for exam_type in ['jee', 'gate', 'jee_adv', 'upsc']:
                if exam_type in notification_data and notification_data[exam_type]:
                    notifications.extend(notification_data[exam_type])
            
            if notifications:
                print(f"📤 Adding {len(notifications)} new notifications to webhook queue...")
                
                # Add notifications to queue for processing
                queue = self._get_notification_queue()
                notification_ids = queue.add_batch_notifications(notifications, "auto_scrape")
                
                print(f"✅ Added {len(notification_ids)} notifications to webhook queue")
            else:
                print("ℹ️  No notifications to send via webhook")
                
        except Exception as e:
            print(f"❌ Error adding notifications to webhook queue: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the notification system"""
        main_data = self.get_existing_data()
        notification_data = self.get_notification_data()
        queue_status = self._get_notification_queue().get_queue_status()
        
        return {
            'main_file_exists': os.path.exists(self.main_data_file),
            'notification_file_exists': os.path.exists(self.notification_file),
            'main_data_summary': {
                'jee': len(main_data.get('jee', [])),
                'gate': len(main_data.get('gate', [])),
                'jee_adv': len(main_data.get('jee_adv', [])),
                'upsc': len(main_data.get('upsc', [])),
                'total': main_data.get('total_notification', 0)
            },
            'notification_summary': {
                'jee': len(notification_data.get('jee', [])),
                'gate': len(notification_data.get('gate', [])),
                'jee_adv': len(notification_data.get('jee_adv', [])),
                'upsc': len(notification_data.get('upsc', [])),
                'total': notification_data.get('total_new_notifications', 0)
            },
            'queue_status': queue_status,
            'last_updated': main_data.get('last_updated'),
            'last_scrape': main_data.get('last_scrape')
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get notification queue status"""
        return self._get_notification_queue().get_queue_status()
    
    def clear_queue(self) -> None:
        """Clear the notification queue"""
        self._get_notification_queue().clear_queue()


def main():
    """Command line interface for notification manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Notification Manager for exam data')
    parser.add_argument('--action', choices=['init', 'clear', 'status'], 
                       default='status', help='Action to perform')
    
    args = parser.parse_args()
    
    manager = NotificationManager()
    
    try:
        if args.action == 'init':
            manager.initial_scrape_and_setup()
            print(f"\n🎉 Initial setup completed!")
            
        elif args.action == 'clear':
            manager.clear_notifications()
            print(f"\n🎉 Notifications cleared!")
            
        elif args.action == 'status':
            status = manager.get_status()
            print(f"\n📊 Notification System Status:")
            print(f"   - Main file exists: {status['main_file_exists']}")
            print(f"   - Notification file exists: {status['notification_file_exists']}")
            print(f"   - Main data: {status['main_data_summary']}")
            print(f"   - Notifications: {status['notification_summary']}")
            print(f"   - Last updated: {status['last_updated']}")
            print(f"   - Last scrape: {status['last_scrape']}")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
