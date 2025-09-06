#!/usr/bin/env python3
"""
Startup script to run both the demo server and the main scraper server
This provides a complete demo environment for testing the notification system
"""

import subprocess
import sys
import time
import threading
import os
from pathlib import Path

def run_demo_server():
    """Run the demo HTTP server"""
    print("🚀 Starting demo server on port 8080...")
    subprocess.run([sys.executable, "demo_server.py"])

def run_main_server():
    """Run the main scraper server"""
    print("🎓 Starting main scraper server on port 5000...")
    subprocess.run([sys.executable, "main.py", "--mode", "server"])

def main():
    """Start both servers"""
    print("🎯 Starting Exam Scraper Demo System")
    print("=" * 50)
    
    # Check if required files exist
    required_files = [
        "demo_notifications.html",
        "main.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            return 1
    
    print("✅ All required files found")
    print()
    
    # Start demo server in a separate thread
    demo_thread = threading.Thread(target=run_demo_server, daemon=True)
    demo_thread.start()
    
    # Wait a moment for demo server to start
    time.sleep(2)
    
    print()
    print("🌐 Demo server started at: http://localhost:8080")
    print("🎓 Main dashboard will be at: http://localhost:5000")
    print()
    print("📝 Instructions:")
    print("1. Open http://localhost:5000 to access the main dashboard")
    print("2. Scroll down to the 'Demo Notification System' section")
    print("3. Click 'Initialize Notifications' to set up the system")
    print("4. Add notifications using the embedded demo interface")
    print("5. Click 'Run Scrape' to process notifications and save to database")
    print("6. Watch real-time updates in the dashboard")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 50)
    
    try:
        # Start main server (this will block)
        run_main_server()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all servers...")
        return 0

if __name__ == '__main__':
    sys.exit(main())
