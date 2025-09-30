## Refactoring Guide

This document explains the production hardening refactor performed across the codebase.

### Dependency Hardening

- What changed: Pinned versions in `requirements.txt`; added `gunicorn`, `SQLAlchemy`, and `psycopg2-binary`.
- Why: Deterministic builds and a production WSGI server with PostgreSQL support.
- How it impacts local dev: Install with `pip install -r requirements.txt`. For production, create a lock file: `pip freeze > requirements.lock.txt` and use that for stable deployments.

Before (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\requirements.txt
# Core dependencies
requests>=2.31.0
```

After (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\requirements.txt
requests==2.32.3
gunicorn==23.0.0
SQLAlchemy==2.0.34
psycopg2-binary==2.9.9
```

### Configuration: `config/settings.py`

- What changed: All sensitive and environment-specific values are loaded from environment variables. Introduced `DATABASE_URL`, `LOG_FORMAT`, `ENVIRONMENT`.
- Why: Avoid hardcoded secrets/paths; enable 12-factor configuration.
- Local dev impact: Create `.env` from `.env.example`; set PostgreSQL envs or use `docker-compose`.

Before (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\config\settings.py
DATABASE_PATH = 'data/exam_updates.db'
LOG_FILE = 'logs/scraper.log'
```

After (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\config\settings.py
DATABASE_URL = os.getenv('DATABASE_URL')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
```

### Database Migration: `data/storage.py`

- What changed: Replaced SQLite direct usage with SQLAlchemy and PostgreSQL via `DATABASE_URL`. Preserved schema semantics; added indices and robust queries.
- Why: PostgreSQL is more reliable for concurrency, durability, and scaling; SQLAlchemy brings portability and safety.
- Local dev impact: Run Postgres via Docker with `docker-compose`; no local SQLite.

Before (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\data\storage.py
conn = sqlite3.connect(self.db_path)
```

After (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\data\storage.py
self.engine: Engine = create_engine(self.database_url, pool_pre_ping=True)
```

### Logging: `utils/logger.py`

- What changed: Logging now emits JSON to stdout by default; removed file handler dependency.
- Why: Container-friendly logging; integrates with log aggregation.
- Local dev impact: Logs print to console; set `LOG_FORMAT=text` for human-readable.

Before (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\utils\logger.py
file_handler = logging.FileHandler(log_file, encoding='utf-8')
```

After (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\utils\logger.py
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
```

### Application Entrypoint: `main.py`

- What changed: Introduced `create_app()` factory for Gunicorn; centralized logging setup.
- Why: Production WSGI server compatibility and cleaner initialization.
- Local dev impact: Still runnable via `python main.py`; production uses Gunicorn.

Before (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\main.py
def main():
    parser = argparse.ArgumentParser
```

After (excerpt):

```startLine:endLine:c:\Users\heman\Desktop\kollegeapply\update-data-scraper\main.py
def create_app():
    """Application Factory used by Gunicorn"""
```

### Deployment Artifacts

- Added `Dockerfile` (multi-stage), `.dockerignore`, `docker-compose.yml`, and `nginx.conf` for a production stack.
- Why: Standardize deployments with containerization, reverse proxy, and persistent DB storage.
- Local dev impact: One command `docker-compose up --build -d` to run full stack.

### Code Cleanup Recommendations

- Remove development-only artifacts from images: `logs/`, local SQLite files, and JSON backups are excluded by `.dockerignore`.
- Prefer Postgres backups over JSON snapshots for durability; see `DEPLOYMENT_GUIDE.md`.
- Avoid `print()` statements; use `utils/logger.py` instead.

