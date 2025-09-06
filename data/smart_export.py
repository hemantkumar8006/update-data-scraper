#!/usr/bin/env python3
"""
Smart export system that maintains a single JSON file with incremental updates
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Set

# Handle both relative and absolute imports
try:
    from .storage import DataStorage
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.storage import DataStorage


class SmartExporter:
    """Smart exporter that maintains a single JSON file with incremental updates"""
    
    def __init__(self, storage: DataStorage = None, export_file: str = "data/exam_data.json"):
        self.storage = storage or DataStorage()
        self.export_file = export_file
        self.backup_dir = "data/backups"
        os.makedirs(os.path.dirname(self.export_file), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current data from JSON file"""
        if not os.path.exists(self.export_file):
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
            with open(self.export_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading existing file: {e}")
            return {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_notification": 0,
                "last_updated": None,
                "last_scrape": None
            }
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file with backup"""
        # Create backup of existing file
        if os.path.exists(self.export_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"exam_data_backup_{timestamp}.json")
            try:
                import shutil
                shutil.copy2(self.export_file, backup_file)
                print(f"📁 Backup created: {backup_file}")
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")
        
        # Save new data
        try:
            with open(self.export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Data saved to: {self.export_file}")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            raise
    
    def get_existing_hashes(self, current_data: Dict[str, Any]) -> Set[str]:
        """Get all existing content hashes from current data"""
        hashes = set()
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            for item in current_data.get(category, []):
                if 'content_hash' in item:
                    hashes.add(item['content_hash'])
        return hashes
    
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
    
    def update_with_new_data(self, new_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update existing data with new updates"""
        print(f"🔄 Processing {len(new_updates)} new updates...")
        
        # Get current data
        current_data = self.get_current_data()
        existing_hashes = self.get_existing_hashes(current_data)
        
        # Track new items added
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
                current_data[category].append(formatted_update)
                existing_hashes.add(content_hash)
                new_items_count += 1
            else:
                # Update existing item if needed
                category = self.determine_category(update)
                formatted_update = self.format_update(update)
                
                # Find and update existing item
                for i, existing_item in enumerate(current_data[category]):
                    if existing_item.get('content_hash') == content_hash:
                        current_data[category][i] = formatted_update
                        updated_items_count += 1
                        break
        
        # Sort each category by scraped_at date (newest first)
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            current_data[category].sort(
                key=lambda x: x.get('scraped_at', ''), 
                reverse=True
            )
        
        # Update metadata
        current_data["total_notification"] = sum(
            len(current_data[category]) for category in ["jee", "gate", "jee_adv", "upsc"]
        )
        current_data["last_updated"] = datetime.now().isoformat()
        current_data["last_scrape"] = datetime.now().isoformat()
        
        print(f"📊 Update summary:")
        print(f"   - New items added: {new_items_count}")
        print(f"   - Items updated: {updated_items_count}")
        print(f"   - Total notifications: {current_data['total_notification']}")
        
        return current_data
    
    def fresh_scrape_and_create_file(self) -> str:
        """Perform fresh scrape and create initial file"""
        print("🚀 Starting fresh scrape...")
        
        # Get all current data from database
        all_updates = self.storage.get_recent_updates(hours=24*365, limit=10000)
        
        if not all_updates:
            print("⚠️  No data found in database")
            all_updates = []
        
        # Create fresh data structure
        fresh_data = {
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
            fresh_data[category].append(formatted_update)
        
        # Sort each category by scraped_at date (newest first)
        for category in ["jee", "gate", "jee_adv", "upsc"]:
            fresh_data[category].sort(
                key=lambda x: x.get('scraped_at', ''), 
                reverse=True
            )
        
        # Save fresh data
        self.save_data(fresh_data)
        
        print(f"✅ Fresh scrape completed!")
        print(f"📊 Fresh data summary:")
        print(f"   - JEE: {len(fresh_data['jee'])} notifications")
        print(f"   - GATE: {len(fresh_data['gate'])} notifications")
        print(f"   - JEE Advanced: {len(fresh_data['jee_adv'])} notifications")
        print(f"   - UPSC: {len(fresh_data['upsc'])} notifications")
        print(f"   - Total: {fresh_data['total_notification']} notifications")
        
        return self.export_file
    
    def incremental_update(self) -> str:
        """Perform incremental update with new scraped data"""
        print("🔄 Starting incremental update...")
        
        # Get recent updates from database (last 30 minutes)
        recent_updates = self.storage.get_recent_updates(hours=0.5, limit=1000)  # 30 minutes
        
        if not recent_updates:
            print("ℹ️  No new updates found in the last 30 minutes")
            return self.export_file
        
        # Update existing data with new updates
        updated_data = self.update_with_new_data(recent_updates)
        
        # Save updated data
        self.save_data(updated_data)
        
        print(f"✅ Incremental update completed!")
        return self.export_file
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the current export file"""
        if not os.path.exists(self.export_file):
            return {"exists": False}
        
        try:
            data = self.get_current_data()
            file_stats = os.stat(self.export_file)
            
            return {
                "exists": True,
                "file_path": self.export_file,
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "data_summary": {
                    "jee": len(data.get("jee", [])),
                    "gate": len(data.get("gate", [])),
                    "jee_adv": len(data.get("jee_adv", [])),
                    "upsc": len(data.get("upsc", [])),
                    "total": data.get("total_notification", 0)
                },
                "last_updated": data.get("last_updated"),
                "last_scrape": data.get("last_scrape")
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}


def main():
    """Command line interface for smart export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart export system for exam data')
    parser.add_argument('--action', choices=['fresh', 'update', 'info'], 
                       default='update', help='Action to perform')
    parser.add_argument('--file', default='data/exam_data.json',
                       help='Export file path')
    
    args = parser.parse_args()
    
    exporter = SmartExporter(export_file=args.file)
    
    try:
        if args.action == 'fresh':
            filepath = exporter.fresh_scrape_and_create_file()
            print(f"\n🎉 Fresh scrape completed! File: {filepath}")
            
        elif args.action == 'update':
            filepath = exporter.incremental_update()
            print(f"\n🎉 Incremental update completed! File: {filepath}")
            
        elif args.action == 'info':
            info = exporter.get_file_info()
            if info.get("exists"):
                print(f"\n📊 File Information:")
                print(f"   - Path: {info['file_path']}")
                print(f"   - Size: {info['file_size_mb']} MB")
                print(f"   - Last Modified: {info['last_modified']}")
                print(f"   - Last Updated: {info['last_updated']}")
                print(f"   - Last Scrape: {info['last_scrape']}")
                print(f"   - Data Summary: {info['data_summary']}")
            else:
                print(f"\n❌ File does not exist: {args.file}")
                print("   Run with --action fresh to create initial file")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
