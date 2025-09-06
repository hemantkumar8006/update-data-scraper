#!/usr/bin/env python3
"""
Demonstration script for the notification workflow
This script shows how the notification system works step by step
"""

import json
import os
from data.notification_manager import NotificationManager
from data.storage import DataStorage


def demonstrate_workflow():
    """Demonstrate the complete notification workflow"""
    print("🚀 Notification System Workflow Demonstration")
    print("=" * 60)
    
    # Initialize components
    storage = DataStorage()
    notification_manager = NotificationManager(storage)
    
    # Step 1: Initial scrape and setup
    print("\n📋 Step 1: Initial Scrape and Setup")
    print("-" * 40)
    print("This step:")
    print("• Scrapes all existing data from database")
    print("• Creates exam_data.json with all current data")
    print("• Clears updated_notifications.json (should be empty)")
    
    try:
        initial_result = notification_manager.initial_scrape_and_setup()
        print("✅ Initial setup completed successfully!")
        print(f"📊 Initial data summary:")
        print(f"   - Total notifications: {initial_result['total_notification']}")
        print(f"   - JEE: {len(initial_result['jee'])}")
        print(f"   - GATE: {len(initial_result['gate'])}")
        print(f"   - JEE Advanced: {len(initial_result['jee_adv'])}")
        print(f"   - UPSC: {len(initial_result['upsc'])}")
    except Exception as e:
        print(f"❌ Initial setup failed: {e}")
        return
    
    # Step 2: Check initial status
    print("\n📋 Step 2: Check Initial Status")
    print("-" * 40)
    status = notification_manager.get_status()
    print("📊 Current Status:")
    print(f"   - Main file exists: {status['main_file_exists']}")
    print(f"   - Notification file exists: {status['notification_file_exists']}")
    print(f"   - Main data: {status['main_data_summary']}")
    print(f"   - Notifications: {status['notification_summary']}")
    
    # Step 3: Simulate new scraped data
    print("\n📋 Step 3: Simulate New Scraped Data")
    print("-" * 40)
    print("Simulating new data from scraping cycle...")
    
    # Create some mock new data
    mock_new_data = [
        {
            'id': 1001,
            'title': 'JEE Main 2025 Application Form Released',
            'content_summary': 'New application form for JEE Main 2025 is now available',
            'source': 'NTA JEE Main',
            'exam_type': 'JEE',
            'url': 'https://jeemain.nta.nic.in/application',
            'date': '2025-01-15',
            'scraped_at': '2025-01-15T10:30:00',
            'content_hash': 'hash_new_jee_001',
            'priority': 'high'
        },
        {
            'id': 1002,
            'title': 'GATE 2025 Result Declaration Date',
            'content_summary': 'GATE 2025 results will be declared on March 15, 2025',
            'source': 'GATE Official',
            'exam_type': 'GATE',
            'url': 'https://gate.iit.ac.in/results',
            'date': '2025-01-15',
            'scraped_at': '2025-01-15T11:00:00',
            'content_hash': 'hash_new_gate_001',
            'priority': 'high'
        }
    ]
    
    print(f"📥 Mock new data: {len(mock_new_data)} items")
    for item in mock_new_data:
        print(f"   - {item['title']} ({item['exam_type']})")
    
    # Step 4: Process new data
    print("\n📋 Step 4: Process New Data")
    print("-" * 40)
    print("This step:")
    print("• Compares new data with existing data")
    print("• Updates exam_data.json with new + existing data")
    print("• Creates updated_notifications.json with only NEW data")
    
    try:
        result = notification_manager.process_next_scrape_cycle(mock_new_data)
        print("✅ New data processing completed!")
        print(f"📊 Processing summary:")
        print(f"   - New items added: {result['stats']['new_items']}")
        print(f"   - Items updated: {result['stats']['updated_items']}")
        print(f"   - New notifications: {result['stats']['new_notifications']}")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return
    
    # Step 5: Check final status
    print("\n📋 Step 5: Check Final Status")
    print("-" * 40)
    final_status = notification_manager.get_status()
    print("📊 Final Status:")
    print(f"   - Main file exists: {final_status['main_file_exists']}")
    print(f"   - Notification file exists: {final_status['notification_file_exists']}")
    print(f"   - Main data: {final_status['main_data_summary']}")
    print(f"   - Notifications: {final_status['notification_summary']}")
    
    # Step 6: Show file contents
    print("\n📋 Step 6: File Contents")
    print("-" * 40)
    
    # Show main data file
    if os.path.exists("data/exam_data.json"):
        with open("data/exam_data.json", 'r') as f:
            main_data = json.load(f)
        print("📄 exam_data.json contains:")
        print(f"   - Total notifications: {main_data['total_notification']}")
        print(f"   - Last updated: {main_data['last_updated']}")
    
    # Show notification file
    if os.path.exists("data/updated_notifications.json"):
        with open("data/updated_notifications.json", 'r') as f:
            notification_data = json.load(f)
        print("📄 updated_notifications.json contains:")
        print(f"   - New notifications: {notification_data['total_new_notifications']}")
        print(f"   - Last updated: {notification_data['last_updated']}")
        if notification_data['total_new_notifications'] > 0:
            print("   - New items:")
            for category in ['jee', 'gate', 'jee_adv', 'upsc']:
                if notification_data[category]:
                    print(f"     • {category.upper()}: {len(notification_data[category])} items")
    
    # Step 7: Next cycle simulation
    print("\n📋 Step 7: Next Cycle Simulation")
    print("-" * 40)
    print("Simulating next scraping cycle with no new data...")
    
    # Clear notifications for next cycle
    notification_manager.clear_notifications()
    print("✅ Notifications cleared for next cycle")
    
    # Simulate no new data
    empty_result = notification_manager.process_next_scrape_cycle([])
    print("✅ Empty cycle processed (no new data)")
    
    # Check status after empty cycle
    empty_status = notification_manager.get_status()
    print(f"📊 Status after empty cycle:")
    print(f"   - Notifications: {empty_status['notification_summary']}")
    
    print("\n🎉 Workflow demonstration completed!")
    print("\n💡 Key Points:")
    print("1. Initial setup creates exam_data.json with all existing data")
    print("2. Each scraping cycle compares new data with existing data")
    print("3. Only NEW data goes into updated_notifications.json")
    print("4. exam_data.json contains ALL data (existing + new)")
    print("5. updated_notifications.json is cleared after each cycle")
    print("6. If no new data, updated_notifications.json remains empty")


def main():
    """Main function"""
    try:
        demonstrate_workflow()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
