import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Scraping Configuration
SCRAPE_INTERVAL = 30 * 60  # 30 minutes in seconds
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Data Storage
DATABASE_PATH = 'data/exam_updates.db'
JSON_BACKUP_PATH = 'data/backups/'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scraper.log'

# Web Interface
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000

# AI Processing
AI_BATCH_SIZE = 5
AI_RATE_LIMIT_DELAY = 1  # seconds between AI requests

# Performance
MAX_CONCURRENT_REQUESTS = 5
CACHE_TTL = 300  # 5 minutes

# Notification (Disabled - focusing on data scraping only)
ENABLE_NOTIFICATIONS = False
