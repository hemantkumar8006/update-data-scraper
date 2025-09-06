# 🐛 Debugging Reference Guide

## 📍 Entry Points & Debugging Commands

### Main Entry Points

#### 1. **Primary Entry Point: `main.py`**

```python
# Location: ./main.py
# Purpose: Main application with multiple execution modes

# Debug commands:
python main.py --mode single-run  # Test scraping once
python main.py --mode web --port 5001  # Test web interface only
python main.py --mode server --port 5000  # Full system
```

**Key Functions to Debug:**

- `create_web_interface()` - Web dashboard creation
- `main()` - Argument parsing and mode selection

#### 2. **Simple Entry Point: `start.py`**

```python
# Location: ./start.py
# Purpose: Requirement checking and system startup

# Debug commands:
python start.py  # Full system check and start
python -c "from start import check_requirements; check_requirements()"  # Test requirements only
```

**Key Functions to Debug:**

- `check_requirements()` - System validation
- `main()` - Startup orchestration

### Core System Components

#### 3. **Server Logic: `mcp_server/server.py`**

```python
# Location: ./mcp_server/server.py
# Class: MCPExamScrapingServer

# Debug commands:
python -c "
from mcp_server.server import MCPExamScrapingServer
server = MCPExamScrapingServer()
print('Server initialized:', len(server.scrapers), 'scrapers')
print('Status:', server.get_status())
"

# Test individual scraping:
python -c "
from mcp_server.server import MCPExamScrapingServer
server = MCPExamScrapingServer()
result = server.run_single_scrape()
print('Scraping result:', result)
"
```

**Key Methods to Debug:**

- `scrape_all_websites()` - Main scraping logic
- `get_status()` - System health check
- `init_scrapers()` - Scraper initialization

#### 4. **Scheduler: `mcp_server/scheduler.py`**

```python
# Location: ./mcp_server/scheduler.py
# Class: Scheduler

# Debug commands:
python -c "
from mcp_server.scheduler import Scheduler
def test_func(): print('Test run')
scheduler = Scheduler(test_func)
print('Scheduler created')
print('Next run:', scheduler.get_next_run_time())
"
```

**Key Methods to Debug:**

- `start()` - Scheduler initialization
- `run_scraping()` - Scraping execution
- `_run_scheduler()` - Main scheduler loop

### Data & Storage

#### 5. **Database: `data/storage.py`**

```python
# Location: ./data/storage.py
# Class: DataStorage

# Debug commands:
python -c "
from data.storage import DataStorage
storage = DataStorage()
print('Database initialized')
stats = storage.get_database_stats()
print('Stats:', stats)
"

# Test database operations:
python -c "
from data.storage import DataStorage
storage = DataStorage()
recent = storage.get_recent_updates(24, 5)
print('Recent updates:', len(recent))
for update in recent[:2]:
    print(f'- {update[\"title\"]} ({update[\"source\"]})')
"
```

**Key Methods to Debug:**

- `init_database()` - Database creation
- `save_updates()` - Data storage
- `get_recent_updates()` - Data retrieval
- `check_database_integrity()` - Database health

### AI Processing

#### 6. **AI Processor: `ai_processors/base_processor.py`**

```python
# Location: ./ai_processors/base_processor.py
# Class: AIProcessorWithFallback

# Debug commands:
python -c "
from ai_processors import AIProcessorWithFallback
processor = AIProcessorWithFallback()
print('AI processor initialized')
"

# Test with sample data:
python -c "
from ai_processors import AIProcessorWithFallback
processor = AIProcessorWithFallback()
test_updates = [{'title': 'Test Update', 'content_summary': 'Test content', 'source': 'Test', 'scraped_at': '2025-01-01', 'content_hash': 'test123'}]
try:
    result = processor.enhance_content(test_updates)
    print('AI processing successful')
except Exception as e:
    print('AI processing failed:', e)
"
```

#### 7. **Gemini Processor: `ai_processors/gemini_processor.py`**

```python
# Location: ./ai_processors/gemini_processor.py
# Class: GeminiProcessor

# Debug commands:
python -c "
from ai_processors.gemini_processor import GeminiProcessor
try:
    processor = GeminiProcessor()
    print('Gemini processor initialized successfully')
except Exception as e:
    print('Gemini initialization failed:', e)
"
```

### Website Scrapers

#### 8. **Base Scraper: `scrapers/base_scraper.py`**

```python
# Location: ./scrapers/base_scraper.py
# Class: BaseScraper

# Debug commands:
python -c "
from scrapers.base_scraper import BaseScraper
from config.settings import USER_AGENT
print('Base scraper imports OK')
print('User agent:', USER_AGENT)
"
```

#### 9. **Individual Scrapers**

```python
# Test NTA Scraper:
python -c "
from scrapers.nta_scraper import NTAScraper
config = {'name': 'Test', 'url': 'https://jeemain.nta.nic.in/', 'selectors': {'news_container': '.news', 'title': 'h3', 'date': '.date', 'link': 'a'}, 'keywords': ['jee']}
scraper = NTAScraper(config)
try:
    updates = scraper.scrape()
    print(f'NTA scraper found {len(updates)} updates')
except Exception as e:
    print('NTA scraper failed:', e)
"

# Test UPSC Scraper:
python -c "
from scrapers.upsc_scraper import UPSCScraper
config = {'name': 'Test', 'url': 'https://upsc.gov.in/', 'selectors': {'news_container': '.news', 'title': 'h3', 'date': '.date', 'link': 'a'}, 'keywords': ['upsc']}
scraper = UPSCScraper(config)
try:
    updates = scraper.scrape()
    print(f'UPSC scraper found {len(updates)} updates')
except Exception as e:
    print('UPSC scraper failed:', e)
"
```

## 🔍 Step-by-Step Debugging Process

### 1. **System Health Check**

```bash
# Complete system validation
python -c "
import sys
print(f'Python: {sys.version}')

try:
    from main import main
    print('✅ Main module')
except Exception as e:
    print(f'❌ Main module: {e}')

try:
    from data.storage import DataStorage
    storage = DataStorage()
    print('✅ Database')
except Exception as e:
    print(f'❌ Database: {e}')

try:
    from ai_processors import AIProcessorWithFallback
    processor = AIProcessorWithFallback()
    print('✅ AI processor')
except Exception as e:
    print(f'❌ AI processor: {e}')

try:
    from mcp_server.server import MCPExamScrapingServer
    server = MCPExamScrapingServer()
    print(f'✅ Server ({len(server.scrapers)} scrapers)')
except Exception as e:
    print(f'❌ Server: {e}')
"
```

### 2. **Configuration Validation**

```bash
# Check configuration files
python -c "
import json
import os

# Check .env file
if os.path.exists('.env'):
    print('✅ .env file exists')
    with open('.env', 'r') as f:
        content = f.read()
        if 'GEMINI_API_KEY' in content and 'your_gemini_api_key_here' not in content:
            print('✅ API key configured')
        else:
            print('❌ API key not configured')
else:
    print('❌ .env file missing')

# Check websites.json
try:
    with open('config/websites.json', 'r') as f:
        config = json.load(f)
        print(f'✅ Websites config ({len(config[\"websites\"])} websites)')
except Exception as e:
    print(f'❌ Websites config: {e}')

# Check settings
try:
    from config.settings import GEMINI_API_KEY, SCRAPE_INTERVAL
    print(f'✅ Settings loaded (interval: {SCRAPE_INTERVAL}s)')
except Exception as e:
    print(f'❌ Settings: {e}')
"
```

### 3. **Network & Scraping Test**

```bash
# Test individual website scraping
python -c "
import requests
from config.settings import USER_AGENT

websites = [
    'https://jeemain.nta.nic.in/',
    'https://jeeadv.ac.in/',
    'https://iimcat.ac.in/',
    'https://gate2026.iitg.ac.in/',
    'https://upsc.gov.in/'
]

for url in websites:
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
        print(f'✅ {url}: {response.status_code}')
    except Exception as e:
        print(f'❌ {url}: {e}')
"
```

### 4. **Database Operations Test**

```bash
# Test database operations
python -c "
from data.storage import DataStorage
import os

storage = DataStorage()

# Check database file
db_path = 'data/exam_updates.db'
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f'✅ Database exists ({size} bytes)')
else:
    print('❌ Database file missing')

# Test database operations
try:
    stats = storage.get_database_stats()
    print(f'✅ Database stats: {stats[\"total_updates\"]} updates')
except Exception as e:
    print(f'❌ Database stats: {e}')

try:
    recent = storage.get_recent_updates(24, 5)
    print(f'✅ Recent updates: {len(recent)} found')
except Exception as e:
    print(f'❌ Recent updates: {e}')
"
```

### 5. **AI Processing Test**

```bash
# Test AI processing
python -c "
import os
from ai_processors.gemini_processor import GeminiProcessor

# Check API key
api_key = os.getenv('GEMINI_API_KEY')
if api_key and api_key != 'your_gemini_api_key_here':
    print('✅ API key configured')

    try:
        processor = GeminiProcessor()
        print('✅ Gemini processor initialized')

        # Test with sample data
        test_update = {
            'title': 'Test Exam Notification',
            'content_summary': 'This is a test notification',
            'source': 'Test',
            'scraped_at': '2025-01-01T00:00:00',
            'content_hash': 'test123'
        }

        result = processor.analyze_single_update(test_update)
        print('✅ AI processing test successful')

    except Exception as e:
        print(f'❌ AI processing test failed: {e}')
else:
    print('❌ API key not configured')
"
```

### 6. **Web Interface Test**

```bash
# Test web interface
python -c "
from main import create_web_interface
import threading
import time
import requests

try:
    app = create_web_interface()
    print('✅ Web interface created')

    # Start in background thread
    def run_app():
        app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # Wait for server to start
    time.sleep(2)

    # Test endpoints
    try:
        response = requests.get('http://127.0.0.1:5001/status', timeout=5)
        print(f'✅ Status endpoint: {response.status_code}')
    except Exception as e:
        print(f'❌ Status endpoint: {e}')

except Exception as e:
    print(f'❌ Web interface: {e}')
"
```

## 🚨 Common Error Patterns & Solutions

### Import Errors

```bash
# Pattern: ModuleNotFoundError
# Solution: Check virtual environment and dependencies
venv\Scripts\activate
pip install -r requirements.txt
```

### API Key Errors

```bash
# Pattern: API key not valid
# Solution: Check .env file
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('GEMINI_API_KEY')[:10] + '...' if os.getenv('GEMINI_API_KEY') else 'Not set')
"
```

### Database Errors

```bash
# Pattern: Database corruption
# Solution: Recreate database
python -c "
import os
if os.path.exists('data/exam_updates.db'):
    os.remove('data/exam_updates.db')
    print('Database removed, will recreate on next run')
"
```

### Network Errors

```bash
# Pattern: Connection timeout
# Solution: Check network and website availability
python -c "
import requests
try:
    response = requests.get('https://google.com', timeout=5)
    print('✅ Internet connection OK')
except Exception as e:
    print(f'❌ Network issue: {e}')
"
```

## 📊 Performance Monitoring

### Memory Usage

```bash
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

### Scraping Performance

```bash
# Monitor scraping times in logs
python -c "
import re
with open('logs/scraper.log', 'r') as f:
    content = f.read()
    times = re.findall(r'completed in ([\d.]+) seconds', content)
    if times:
        avg_time = sum(float(t) for t in times[-5:]) / len(times[-5:])
        print(f'Average scraping time: {avg_time:.2f} seconds')
    else:
        print('No scraping times found in logs')
"
```

---

## 🎯 Quick Debug Checklist

- [ ] **System Health**: All imports working
- [ ] **Configuration**: .env file with valid API key
- [ ] **Database**: File exists and accessible
- [ ] **Network**: Can reach target websites
- [ ] **AI Processing**: Gemini API working
- [ ] **Web Interface**: Dashboard accessible
- [ ] **Scraping**: At least one scraper working
- [ ] **Scheduling**: Automated runs happening

**Use this reference to quickly identify and resolve issues! 🚀**
