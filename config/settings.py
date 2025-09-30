import os
from dotenv import load_dotenv

load_dotenv()

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# API Keys (loaded from env only)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# Scraping Configuration
SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', str(30 * 60)))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

# Data Storage
# Prefer DATABASE_URL for SQLAlchemy (e.g., postgresql+psycopg2://user:pass@host:5432/dbname)
DATABASE_URL = os.getenv('DATABASE_URL')

# Retain JSON backups, but path is configurable
JSON_BACKUP_PATH = os.getenv('JSON_BACKUP_PATH', 'data/backups/')

# Logging - structured JSON to stdout in prod
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'

# Web Interface
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', '5000'))

# AI Processing
AI_BATCH_SIZE = int(os.getenv('AI_BATCH_SIZE', '5'))
AI_RATE_LIMIT_DELAY = float(os.getenv('AI_RATE_LIMIT_DELAY', '1'))

# Performance
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))

# Notifications
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
NOTIFICATION_WEBHOOK_URL = os.getenv('NOTIFICATION_WEBHOOK_URL')
NOTIFICATION_WEBHOOK_SECRET = os.getenv('NOTIFICATION_WEBHOOK_SECRET')
