# 🚀 Exam Scraper Setup & Debugging Guide

## 📋 Project Overview

This is a comprehensive exam update scraping system that monitors major Indian examination websites (JEE Main, JEE Advanced, CAT, GATE, UPSC) and provides real-time updates with AI-powered content analysis using Google Gemini.

## 🛠️ Quick Setup Guide

### Prerequisites

- Python 3.8 or higher ✅ (Current: Python 3.13.7)
- Internet connection for web scraping
- Google Gemini API key (for AI content analysis)

### Step 1: Environment Setup

1. **Activate Virtual Environment**

   ```bash
   venv\Scripts\activate
   ```

2. **Install Dependencies** (Already done)

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   - Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Edit `.env` file and replace the placeholder:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

### Step 2: Start the System

**Option A: Full Server with Web Dashboard (Recommended)**

```bash
python main.py --mode server --port 5000
```

**Option B: Simple Startup Script**

```bash
python start.py
```

**Option C: Single Run (Test Mode)**

```bash
python main.py --mode single-run
```

### Step 3: Access Dashboard

- Open browser: **http://localhost:5000**
- Monitor real-time scraping activity
- View recent updates and statistics

## 📁 Project Structure & Entry Points

### Main Entry Points

#### 1. `main.py` - Primary Application Entry Point

```python
# Main entry point with multiple modes
python main.py --mode [server|single-run|web] --port 5000 --host 0.0.0.0
```

**Modes:**

- `server`: Full system with scheduler + web interface
- `single-run`: One-time scraping, no scheduling
- `web`: Web interface only (no scraping)

#### 2. `start.py` - Simple Startup Script

```python
# Checks requirements and starts the system
python start.py
```

**What it does:**

- Validates Python version
- Checks for .env file
- Creates database if needed
- Starts the main application

### Core Components

#### 3. `mcp_server/server.py` - Main Server Logic

- **Class**: `MCPExamScrapingServer`
- **Purpose**: Orchestrates scraping, AI processing, and data storage
- **Key Methods**:
  - `scrape_all_websites()`: Main scraping function
  - `get_status()`: System health check
  - `start_scheduler()`: Start automated scraping

#### 4. `mcp_server/scheduler.py` - Scheduling System

- **Class**: `Scheduler`
- **Purpose**: Manages automated scraping every 30 minutes
- **Key Methods**:
  - `start()`: Start scheduler
  - `run_scraping()`: Execute scraping cycle
  - `daily_cleanup()`: Database maintenance

#### 5. `scrapers/` - Website Scrapers

- **Base**: `base_scraper.py` - Common scraping logic
- **Implementations**:
  - `nta_scraper.py` - JEE Main (NTA)
  - `jee_advanced_scraper.py` - JEE Advanced
  - `cat_scraper.py` - CAT (IIM)
  - `gate_scraper.py` - GATE 2026
  - `upsc_scraper.py` - UPSC

#### 6. `ai_processors/` - AI Processing

- **Base**: `base_processor.py` - AI processor interface
- **Implementation**: `gemini_processor.py` - Google Gemini integration

#### 7. `data/storage.py` - Data Management

- **Class**: `DataStorage`
- **Purpose**: SQLite database operations, JSON backups
- **Key Methods**:
  - `save_updates()`: Store scraped data
  - `get_recent_updates()`: Retrieve data
  - `cleanup_old_data()`: Maintenance

## 🐛 Debugging Process

### 1. Check System Status

**Test Basic Imports:**

```bash
python -c "from main import main; print('✅ Main module OK')"
python -c "from data.storage import DataStorage; print('✅ Database OK')"
python -c "from ai_processors import AIProcessorWithFallback; print('✅ AI processor OK')"
```

**Test Database:**

```bash
python -c "from data.storage import DataStorage; storage = DataStorage(); print('✅ Database initialized')"
```

### 2. Common Issues & Solutions

#### Issue: "API key not valid"

**Symptoms:**

```
Gemini API error: 400 API key not valid. Please pass a valid API key.
```

**Solution:**

1. Check `.env` file exists and has correct API key
2. Verify API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Ensure no extra spaces in `.env` file

#### Issue: "No updates found"

**Symptoms:**

```
No updates found from [Website Name]
```

**Possible Causes:**

- Website structure changed (update selectors in `config/websites.json`)
- Network connectivity issues
- Website blocking requests

**Debug Steps:**

1. Check network connectivity
2. Test individual scraper:
   ```bash
   python -c "from scrapers.nta_scraper import NTAScraper; scraper = NTAScraper({'name': 'test', 'url': 'https://jeemain.nta.nic.in/', 'selectors': {...}, 'keywords': [...]}); print(scraper.scrape())"
   ```

#### Issue: "Database errors"

**Symptoms:**

```
Database error: [error message]
```

**Solution:**

1. Check file permissions on `data/` directory
2. Ensure disk space available
3. Delete corrupted database: `rm data/exam_updates.db` (will recreate)

#### Issue: "Import errors"

**Symptoms:**

```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**

1. Ensure virtual environment is activated: `venv\Scripts\activate`
2. Reinstall dependencies: `pip install -r requirements.txt`

### 3. Log Analysis

**Main Log File:** `logs/scraper.log`

**Key Log Patterns:**

```
✅ Success: "Found X updates from [Website]"
❌ Error: "Error scraping [Website]: [error]"
⚠️ Warning: "Failed to initialize [component]"
```

**Monitor Logs in Real-time:**

```bash
# Windows PowerShell
Get-Content logs\scraper.log -Wait -Tail 10

# Or use any text editor to view the file
```

### 4. Database Debugging

**Check Database Contents:**

```bash
python -c "
from data.storage import DataStorage
storage = DataStorage()
stats = storage.get_database_stats()
print('Database Stats:', stats)
recent = storage.get_recent_updates(24, 5)
print('Recent Updates:', len(recent))
"
```

**View Raw Database:**

```bash
# Install sqlite3 command line tool, then:
sqlite3 data/exam_updates.db "SELECT * FROM updates LIMIT 5;"
```

### 5. Web Interface Debugging

**Check Web Interface:**

1. Visit: http://localhost:5000
2. Check API endpoints:
   - http://localhost:5000/status
   - http://localhost:5000/recent_updates/24
   - http://localhost:5000/websites

**Common Web Issues:**

- Port 5000 already in use: Use different port `--port 5001`
- Firewall blocking: Allow Python through firewall
- Browser cache: Clear browser cache or use incognito mode

### 6. Performance Monitoring

**Check System Resources:**

```bash
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\".\").percent}%')
"
```

**Monitor Scraping Performance:**

- Check `logs/scraper.log` for timing information
- Look for "Scheduled scraping completed in X.XX seconds"
- Normal range: 5-30 seconds per cycle

## 🔧 Configuration Files

### `config/websites.json`

- Website configurations and selectors
- Add/remove websites here
- Update selectors if websites change structure

### `config/settings.py`

- System-wide settings
- Scraping intervals, timeouts, etc.
- Modify for performance tuning

### `.env`

- API keys and sensitive configuration
- **Never commit to version control**

## 📊 Monitoring & Maintenance

### Daily Checks

1. **Log Review**: Check `logs/scraper.log` for errors
2. **Database Health**: Verify updates are being saved
3. **API Usage**: Monitor Gemini API quota

### Weekly Maintenance

1. **Database Cleanup**: Old data automatically cleaned (30 days)
2. **Log Rotation**: Archive old log files
3. **Performance Review**: Check scraping times

### Monthly Tasks

1. **Website Selectors**: Update if websites change
2. **Dependencies**: Update packages if needed
3. **Backup Review**: Ensure backups are working

## 🚨 Emergency Procedures

### System Won't Start

1. Check Python version: `python --version`
2. Verify virtual environment: `venv\Scripts\activate`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check logs: `logs/scraper.log`

### Database Corruption

1. Stop the system
2. Backup current database: `copy data\exam_updates.db data\exam_updates.db.backup`
3. Delete corrupted database: `del data\exam_updates.db`
4. Restart system (will recreate database)

### API Quota Exceeded

1. Check Gemini API usage in Google Cloud Console
2. System will continue without AI processing
3. Update API key or wait for quota reset

## 📞 Support & Troubleshooting

### Quick Health Check

```bash
# Run this command to check system health
python -c "
try:
    from main import main
    from data.storage import DataStorage
    from ai_processors import AIProcessorWithFallback
    print('✅ All imports successful')

    storage = DataStorage()
    stats = storage.get_database_stats()
    print(f'✅ Database: {stats[\"total_updates\"]} updates')

    print('✅ System is healthy!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### Getting Help

1. Check this guide first
2. Review log files for specific errors
3. Test individual components
4. Check GitHub issues (if applicable)

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with valid Gemini API key
- [ ] Database initialized (automatic on first run)
- [ ] System started (`python main.py --mode server`)
- [ ] Web dashboard accessible (http://localhost:5000)
- [ ] First scraping cycle completed successfully

**🎉 You're ready to scrape exam updates!**
