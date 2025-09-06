# 🎓 Demo Guide - Step by Step Instructions

This guide will walk you through the complete demo workflow of the Exam Scraper Notification System.

## 🚀 Quick Start

### Option 1: Automated Demo (Recommended)

```bash
python start_demo.py
```

### Option 2: Manual Start

```bash
python main.py --mode server
```

## 📋 Complete Demo Workflow

### Step 1: Start the System

1. **Open Terminal/Command Prompt**

   ```bash
   cd C:\Users\heman\Desktop\kollegeapply\Kapp-Data-Scraper
   ```

2. **Start the Demo System**

   ```bash
   python start_demo.py
   ```

3. **Expected Output**

   ```
   🎯 Starting Exam Scraper Demo System
   ==================================================
   ✅ All required files found

   🚀 Starting demo server on port 8080...
   🎓 Starting main scraper server on port 5000...

   🌐 Demo server started at: http://localhost:8080
   🎓 Main dashboard will be at: http://localhost:5000

   📝 Instructions:
   1. Open http://localhost:5000 to access the main dashboard
   2. Scroll down to the 'Demo Notification System' section
   3. Click 'Initialize Notifications' to set up the system
   4. Add notifications using the embedded demo interface
   5. Click 'Run Scrape' to process notifications and save to database
   6. Watch real-time updates in the dashboard
   ```

### Step 2: Access the Dashboard

1. **Open Browser**

   - Navigate to: http://localhost:5000
   - You should see the main dashboard

2. **Dashboard Features**
   - System status and statistics
   - Website management
   - **Demo Notification System** (embedded iframe)
   - Recent notifications display

### Step 3: Initialize the System

1. **Click "Initialize Notifications"**

   - This sets up the notification system
   - Creates necessary data files
   - You should see a success message

2. **Verify Initialization**
   - Check that `data/exam_data.json` is created
   - Check that `data/updated_notifications.json` is created

### Step 4: Add Demo Notifications

1. **Scroll to Demo Section**

   - Find the "Demo Notification System" section
   - You'll see an embedded interface

2. **Add Your First Notification**

   - **Title**: "JEE Main 2024 Registration Open"
   - **Content**: "Registration for JEE Main 2024 is now open. Students can apply through the official NTA website."
   - **Exam Type**: Select "JEE Main"
   - **Source**: "NTA"
   - **Priority**: "High"
   - **URL**: "https://jeemain.nta.ac.in"
   - **Date**: Today's date

3. **Click "Add Notification"**

   - Notification should appear in the list
   - Statistics should update
   - Data is saved to `demo_notifications.json`

4. **Add More Notifications**
   - Try different exam types (GATE, JEE Advanced, UPSC)
   - Test different priorities and sources
   - Notice real-time updates

### Step 5: Run the Scraper

1. **Click "Run Scrape" Button**

   - This triggers the scraping process
   - The `DemoScraper` reads from `demo_notifications.json`
   - New notifications are processed and saved to database

2. **Watch the Process**

   - Check terminal for scraping logs
   - Watch dashboard for real-time updates
   - Look for toast notifications

3. **Verify Database Storage**
   - Check `data/exam_updates.db` for new entries
   - Check `data/exam_data.json` for updated data

### Step 6: View Results

1. **Dashboard Updates**

   - New notifications appear in the dashboard
   - Statistics update in real-time
   - Toast notifications show new items

2. **Real-time Features**
   - Auto-refresh every 5 seconds
   - Live connection status
   - Real-time statistics

## 🔍 Testing Different Scenarios

### Scenario 1: Basic Notification Flow

1. Add 3-4 notifications with different exam types
2. Run scrape
3. Verify all notifications appear in dashboard
4. Check database for entries

### Scenario 2: Edit and Delete

1. Edit an existing notification
2. Delete another notification
3. Run scrape again
4. Verify changes are reflected

### Scenario 3: Real-time Updates

1. Keep dashboard open
2. Add new notifications
3. Run scrape
4. Watch real-time updates

### Scenario 4: System Management

1. Go to "Website Management" section
2. Disable "Demo Notifications" scraper
3. Add notifications and run scrape
4. Notice no new notifications are detected
5. Re-enable scraper and run again

## 🛠️ Troubleshooting

### Common Issues

1. **Server Won't Start**

   ```bash
   # Check if port 5000 is available
   netstat -an | findstr :5000

   # Try different port
   python main.py --mode server --port 5001
   ```

2. **Demo Interface Not Loading**

   - Check if `demo_notifications.html` exists
   - Verify file permissions
   - Check browser console for errors

3. **Notifications Not Saving**

   - Check if `demo_notifications.json` is writable
   - Verify POST requests are working
   - Check terminal for error messages

4. **Scraper Not Detecting Changes**
   - Ensure demo scraper is enabled in `config/websites.json`
   - Check file permissions
   - Verify JSON file format

### Debug Mode

1. **Enable Debug Logging**

   ```python
   # In main.py, change logging level
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Logs**

   ```bash
   # View real-time logs
   tail -f logs/scraper.log
   ```

3. **Verify Files**
   ```bash
   # Check if files exist
   ls -la demo_notifications.*
   ls -la data/
   ```

## 📊 Expected Results

### After Adding Notifications

- `demo_notifications.json` should contain your notifications
- Dashboard should show real-time statistics
- Toast notifications should appear

### After Running Scraper

- `data/exam_updates.db` should have new entries
- `data/exam_data.json` should be updated
- Dashboard should show all notifications
- Real-time updates should work

### Database Verification

```sql
-- Check notifications table
SELECT * FROM notifications WHERE scraper_type = 'demo';

-- Check recent entries
SELECT * FROM notifications ORDER BY scraped_at DESC LIMIT 10;
```

## 🎯 Success Indicators

✅ **System Started Successfully**

- No error messages in terminal
- Dashboard loads at http://localhost:5000
- All sections visible

✅ **Notifications Working**

- Can add notifications via demo interface
- Notifications appear in list
- Statistics update in real-time

✅ **Scraper Working**

- "Run Scrape" button works
- New notifications detected
- Database updated with new entries

✅ **Real-time Updates**

- Dashboard auto-refreshes
- Toast notifications appear
- Statistics update live

## 🚀 Next Steps

After completing the demo:

1. **Explore the Code**

   - Check `scrapers/demo_scraper.py` for scraping logic
   - Review `data/notification_manager.py` for data processing
   - Examine `templates/dashboard.html` for UI

2. **Add Real Websites**

   - Modify `config/websites.json`
   - Create new scrapers
   - Test with real exam websites

3. **Customize the System**

   - Modify notification templates
   - Add new exam types
   - Customize the dashboard

4. **Deploy the System**
   - Set up production environment
   - Configure scheduled scraping
   - Set up monitoring

## 📝 Notes

- The demo system uses `demo_notifications.json` as the data source
- The `DemoScraper` reads from this file and processes notifications
- All data is stored in SQLite database (`data/exam_updates.db`)
- The system supports real-time updates via Server-Sent Events
- CORS is enabled for cross-origin requests

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in `logs/scraper.log`
3. Verify all files exist and have correct permissions
4. Check the terminal output for error messages

---

**Happy Demo-ing! 🎓✨**
