# 🗑️ Quick Database Management Commands

## 🚀 **Quick Methods to Clear Database:**

### **Method 1: Interactive Script (Recommended)**

```bash
python clear_database.py
```

- Choose option 1-4 based on what you want to clear
- Most comprehensive and safe method

### **Method 2: Quick Command Line**

```bash
# Delete entire database file (will recreate on restart)
del data\exam_updates.db

# Or using PowerShell
Remove-Item data\exam_updates.db
```

### **Method 3: Python One-liner**

```bash
# Clear all data but keep database structure
python -c "from data.storage import DataStorage; import sqlite3; conn = sqlite3.connect('data/exam_updates.db'); conn.execute('DELETE FROM updates'); conn.execute('DELETE FROM scraping_log'); conn.commit(); conn.close(); print('Database cleared')"
```

### **Method 4: Clear Specific Data**

```bash
# Clear only updates (keep logs)
python -c "import sqlite3; conn = sqlite3.connect('data/exam_updates.db'); conn.execute('DELETE FROM updates'); conn.commit(); conn.close(); print('Updates cleared')"

# Clear only logs (keep updates)
python -c "import sqlite3; conn = sqlite3.connect('data/exam_updates.db'); conn.execute('DELETE FROM scraping_log'); conn.commit(); conn.close(); print('Logs cleared')"
```

## 📊 **Check Database Status:**

### **View Current Data:**

```bash
# Check database stats
python -c "from data.storage import DataStorage; storage = DataStorage(); stats = storage.get_database_stats(); print('Stats:', stats)"

# View recent updates
python -c "from data.storage import DataStorage; storage = DataStorage(); recent = storage.get_recent_updates(24, 5); print(f'Recent updates: {len(recent)}'); [print(f'- {u[\"title\"]} ({u[\"source\"]})') for u in recent]"
```

### **View Database File Info:**

```bash
# Check if database exists and its size
dir data\exam_updates.db

# Or using PowerShell
Get-Item data\exam_updates.db | Select-Object Name, Length, LastWriteTime
```

## 🔄 **Complete Reset Process:**

### **Step 1: Stop the System**

- Press `Ctrl+C` in the terminal where the scraper is running

### **Step 2: Clear Database**

```bash
# Option A: Use the interactive script
python clear_database.py

# Option B: Quick delete
del data\exam_updates.db
```

### **Step 3: Clear Backups (Optional)**

```bash
# Clear JSON backup files
del data\backups\*.json
```

### **Step 4: Restart System**

```bash
python main.py --mode server --port 5000
```

## 🎯 **When to Clear Database:**

### **Clear Database When:**

- ✅ You want fresh data for testing
- ✅ Database has old/irrelevant data
- ✅ You're testing new scraping logic
- ✅ You want to see "new updates found" messages
- ✅ Database has become too large

### **Don't Clear Database When:**

- ❌ System is actively running (stop first)
- ❌ You want to keep historical data
- ❌ You're in production with important data

## 📈 **After Clearing Database:**

### **What Happens:**

1. **Next Scraping Cycle**: Will find all updates as "new"
2. **Web Dashboard**: Will show fresh data
3. **Logs**: Will show "Found X new updates" messages
4. **Database**: Will be recreated if deleted, or cleared if using script

### **Expected Behavior:**

```
2025-09-06 17:20:00 - INFO - Found 3 new updates from UPSC
2025-09-06 17:20:00 - INFO - Total new updates found: 3
```

## 🛠️ **Troubleshooting:**

### **If Database Won't Clear:**

```bash
# Check if system is running
tasklist | findstr python

# Stop all Python processes if needed
taskkill /f /im python.exe

# Then try clearing again
python clear_database.py
```

### **If Database Won't Recreate:**

```bash
# Manually initialize database
python -c "from data.storage import DataStorage; DataStorage().init_database(); print('Database initialized')"
```

## 📝 **Quick Reference:**

| Action                   | Command                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Clear all data**       | `python clear_database.py`                                                                           |
| **Delete database file** | `del data\exam_updates.db`                                                                           |
| **Check stats**          | `python -c "from data.storage import DataStorage; print(DataStorage().get_database_stats())"`        |
| **View recent updates**  | `python -c "from data.storage import DataStorage; print(len(DataStorage().get_recent_updates(24)))"` |
| **Restart system**       | `python main.py --mode server --port 5000`                                                           |

**🎯 Use the interactive script for the safest and most comprehensive database management!**
