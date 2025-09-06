#!/usr/bin/env python3
"""
Data export functionality to generate JSON files with scraped data
organized by exam type for frontend consumption
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Handle both relative and absolute imports
try:
    from .storage import DataStorage
except ImportError:
    # If running as standalone script, add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.storage import DataStorage


class DataExporter:
    """Export scraped data in frontend-friendly format"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or DataStorage()
        self.export_dir = "data/exports"
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_to_json(self, filename: str = None) -> str:
        """
        Export all scraped data to JSON file with the specified format:
        {
            "jee": [],
            "gate": [],
            "jee_adv": [],
            "upsc": [],
            "total_notification": x
        }
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exam_data_{timestamp}.json"
        
        # Validate filename
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            # Get all updates from database
            all_updates = self.storage.get_recent_updates(hours=24*365, limit=10000)  # Get all data
            
            if not all_updates:
                print("⚠️  No data found to export")
                # Create empty structure
                all_updates = []
            
            # Organize by exam type
            organized_data = {
                "jee": [],
                "gate": [],
                "jee_adv": [],
                "upsc": [],
                "total_notification": len(all_updates)
            }
            
            # Categorize updates by exam type
            for update in all_updates:
                category = self._determine_category(update)
                organized_data[category].append(self._format_update(update))
            
            # Sort each category by scraped_at date (newest first)
            for category in organized_data:
                if category != "total_notification":
                    organized_data[category].sort(
                        key=lambda x: x.get('scraped_at', ''), 
                        reverse=True
                    )
            
            # Write to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(organized_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Data exported successfully to: {filepath}")
            print(f"📊 Export summary:")
            print(f"   - JEE: {len(organized_data['jee'])} notifications")
            print(f"   - GATE: {len(organized_data['gate'])} notifications")
            print(f"   - JEE Advanced: {len(organized_data['jee_adv'])} notifications")
            print(f"   - UPSC: {len(organized_data['upsc'])} notifications")
            print(f"   - Total: {organized_data['total_notification']} notifications")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            raise
    
    def _determine_category(self, update: Dict[str, Any]) -> str:
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
    
    def _format_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Format update for frontend consumption"""
        return {
            "id": update.get('id'),
            "title": update.get('title', ''),
            "content_summary": update.get('content_summary', ''),
            "source": update.get('source', ''),
            "url": update.get('url', ''),
            "date": update.get('date', ''),
            "scraped_at": update.get('scraped_at', ''),
            "priority": update.get('priority', 'medium')
        }
    
    def export_latest_data(self) -> str:
        """Export only the latest data (last 24 hours)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"latest_exam_data_{timestamp}.json"
        
        # Get only recent updates
        recent_updates = self.storage.get_recent_updates(hours=24, limit=1000)
        
        # Create organized data directly
        organized_data = {
            "jee": [],
            "gate": [],
            "jee_adv": [],
            "upsc": [],
            "total_notification": len(recent_updates)
        }
        
        # Categorize updates by exam type
        for update in recent_updates:
            category = self._determine_category(update)
            organized_data[category].append(self._format_update(update))
        
        # Sort each category by scraped_at date (newest first)
        for category in organized_data:
            if category != "total_notification":
                organized_data[category].sort(
                    key=lambda x: x.get('scraped_at', ''), 
                    reverse=True
                )
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(organized_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Latest data exported successfully to: {filepath}")
            print(f"📊 Export summary:")
            print(f"   - JEE: {len(organized_data['jee'])} notifications")
            print(f"   - GATE: {len(organized_data['gate'])} notifications")
            print(f"   - JEE Advanced: {len(organized_data['jee_adv'])} notifications")
            print(f"   - UPSC: {len(organized_data['upsc'])} notifications")
            print(f"   - Total: {organized_data['total_notification']} notifications")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting latest data: {e}")
            raise
    
    def export_by_exam_type(self, exam_type: str) -> str:
        """Export data for a specific exam type"""
        # Validate exam type
        valid_types = ['jee', 'gate', 'jee_adv', 'upsc']
        exam_type_lower = exam_type.lower()
        
        if exam_type_lower not in valid_types:
            raise ValueError(f"Invalid exam type: {exam_type}. Valid types are: {valid_types}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{exam_type_lower}_data_{timestamp}.json"
        
        # Get updates for specific exam type
        updates = self.storage.get_updates_by_exam_type(exam_type.upper(), limit=1000)
        
        if not updates:
            print(f"⚠️  No data found for {exam_type.upper()}")
            updates = []
        
        # Create single-category export
        organized_data = {
            exam_type_lower: [self._format_update(update) for update in updates],
            "total_notification": len(updates)
        }
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(organized_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {exam_type.upper()} data exported to: {filepath}")
            print(f"📊 {len(updates)} notifications exported")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting {exam_type} data: {e}")
            raise
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about available data for export"""
        exam_types = self.storage.get_all_exam_types()
        total_updates = sum(exam_type['count'] for exam_type in exam_types)
        
        return {
            "exam_types": exam_types,
            "total_updates": total_updates,
            "export_directory": self.export_dir,
            "available_exports": self._list_existing_exports()
        }
    
    def _list_existing_exports(self) -> List[str]:
        """List existing export files"""
        if not os.path.exists(self.export_dir):
            return []
        
        files = [f for f in os.listdir(self.export_dir) if f.endswith('.json')]
        return sorted(files, reverse=True)  # Newest first


def main():
    """Command line interface for data export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export scraped exam data to JSON')
    parser.add_argument('--type', choices=['all', 'latest', 'jee', 'gate', 'jee_adv', 'upsc'],
                       default='all', help='Type of export to perform')
    parser.add_argument('--filename', help='Custom filename for export')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    try:
        if args.type == 'all':
            filepath = exporter.export_to_json(args.filename)
        elif args.type == 'latest':
            filepath = exporter.export_latest_data()
        else:
            filepath = exporter.export_by_exam_type(args.type)
        
        print(f"\n🎉 Export completed successfully!")
        print(f"📁 File location: {filepath}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
