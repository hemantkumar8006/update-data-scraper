# pyright: reportMissingImports=false
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, Boolean,
    DateTime, Float, Index, select, func, insert, delete
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL, JSON_BACKUP_PATH


class DataStorage:
    def __init__(self, database_url: str | None = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.database_url = database_url or DATABASE_URL
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set. Configure it via environment variables.")

        # Engine and Session
        self.engine: Engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

        # Define metadata and tables
        self.metadata = MetaData()
        self.updates = Table(
            'updates', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('title', Text, nullable=False),
            Column('content_summary', Text),
            Column('source', String(255), nullable=False),
            Column('exam_type', String(50), nullable=False),
            Column('url', Text),
            Column('date', String(50)),
            Column('scraped_at', DateTime, nullable=False),
            Column('content_hash', String(128), unique=True),
            Column('priority', String(50)),
            Column('is_new', Boolean, default=True),
            Column('created_at', DateTime, server_default=func.now()),
            Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
            extend_existing=True,
        )
        Index('idx_content_hash', self.updates.c.content_hash)
        Index('idx_source', self.updates.c.source)
        Index('idx_scraped_at', self.updates.c.scraped_at)
        Index('idx_exam_type', self.updates.c.exam_type)

        self.scraping_log = Table(
            'scraping_log', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('source', String(255), nullable=False),
            Column('status', String(50), nullable=False),
            Column('updates_found', Integer, default=0),
            Column('error_message', Text),
            Column('duration_seconds', Float),
            Column('scraped_at', DateTime, server_default=func.now()),
            extend_existing=True,
        )

        self.init_database()

    def init_database(self) -> None:
        """Create tables and indexes if not exist."""
        try:
            self.metadata.create_all(self.engine)
            self.logger.info("Database initialized successfully")
        except SQLAlchemyError as exc:
            self.logger.error(f"Failed to initialize database: {exc}")
            raise

    def save_updates(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save updates with duplicate detection based on content_hash."""
        if not updates:
            return []

        saved: List[Dict[str, Any]] = []
        with self.engine.begin() as conn:
            for upd in updates:
                try:
                    # Skip if content_hash exists
                    if upd.get('content_hash'):
                        exists_q = select(self.updates.c.id).where(
                            self.updates.c.content_hash == upd['content_hash']
                        )
                        if conn.execute(exists_q).first():
                            continue

                    values = {
                        'title': upd['title'],
                        'content_summary': upd.get('content_summary', ''),
                        'source': upd['source'],
                        'exam_type': upd.get('exam_type', self._determine_exam_type(upd['source'])),
                        'url': upd.get('url', ''),
                        'date': upd.get('date', ''),
                        'scraped_at': self._parse_datetime(upd.get('scraped_at')),
                        'content_hash': upd.get('content_hash'),
                        'priority': upd.get('priority', 'medium'),
                        'is_new': True,
                    }
                    conn.execute(insert(self.updates).values(**values))
                    saved.append(upd)
                except IntegrityError:
                    # Duplicate content_hash or constraint violation; skip
                    continue
                except SQLAlchemyError as exc:
                    self.logger.error(f"DB error saving update: {exc}")
        if saved:
            self.save_json_backup(saved)
        return saved

    def _parse_datetime(self, dt_value: Any) -> datetime:
        if isinstance(dt_value, datetime):
            return dt_value
        try:
            # Accept ISO strings
            return datetime.fromisoformat(str(dt_value))
        except Exception:
            return datetime.utcnow()

    def _determine_exam_type(self, source: str) -> str:
        source_lower = source.lower()
        if 'jee' in source_lower:
            return 'JEE'
        if 'gate' in source_lower:
            return 'GATE'
        if 'upsc' in source_lower:
            return 'UPSC'
        return 'OTHER'

    def save_json_backup(self, updates: List[Dict[str, Any]]) -> None:
        backup_dir = JSON_BACKUP_PATH
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{backup_dir}/updates_{timestamp}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(updates, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON backup saved: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON backup: {e}")

    def get_recent_updates(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - timedelta(hours=hours)
        with self.engine.connect() as conn:
            q = (
                select(self.updates)
                .where(self.updates.c.scraped_at > since)
                .order_by(self.updates.c.scraped_at.desc())
                .limit(limit)
            )
            rows = conn.execute(q).mappings().all()
            return [dict(row) for row in rows]

    def get_updates_by_source(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            q = (
                select(self.updates)
                .where(self.updates.c.source == source)
                .order_by(self.updates.c.scraped_at.desc())
                .limit(limit)
            )
            rows = conn.execute(q).mappings().all()
            return [dict(row) for row in rows]

    def get_updates_by_exam_type(self, exam_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            q = (
                select(self.updates)
                .where(self.updates.c.exam_type == exam_type)
                .order_by(self.updates.c.scraped_at.desc())
                .limit(limit)
            )
            rows = conn.execute(q).mappings().all()
            return [dict(row) for row in rows]

    def get_all_exam_types(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            q = (
                select(self.updates.c.exam_type, func.count())
                .group_by(self.updates.c.exam_type)
                .order_by(func.count().desc())
            )
            rows = conn.execute(q).all()
            return [{'exam_type': row[0], 'count': row[1]} for row in rows]

    def check_existing_hash(self, content_hash: str) -> bool:
        with self.engine.connect() as conn:
            q = select(self.updates.c.id).where(self.updates.c.content_hash == content_hash)
            return conn.execute(q).first() is not None

    def log_scraping_attempt(self, source: str, status: str, updates_found: int = 0, error_message: str | None = None, duration: float | None = None) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.scraping_log).values(
                    source=source,
                    status=status,
                    updates_found=updates_found,
                    error_message=error_message,
                    duration_seconds=duration,
                )
            )

    def get_scraping_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - timedelta(hours=hours)
        with self.engine.connect() as conn:
            q = (
                select(
                    self.scraping_log.c.source,
                    func.count().label('total_attempts'),
                    func.sum(func.case((self.scraping_log.c.status == 'success', 1), else_=0)).label('successful_attempts'),
                    func.sum(self.scraping_log.c.updates_found).label('total_updates'),
                    func.avg(self.scraping_log.c.duration_seconds).label('avg_duration'),
                )
                .where(self.scraping_log.c.scraped_at > since)
                .group_by(self.scraping_log.c.source)
            )
            rows = conn.execute(q).all()
            return [
                {
                    'source': row[0],
                    'total_attempts': row[1],
                    'successful_attempts': row[2] or 0,
                    'total_updates': row[3] or 0,
                    'avg_duration': float(row[4]) if row[4] is not None else 0.0,
                }
                for row in rows
            ]

    def cleanup_old_data(self, days: int = 30) -> Tuple[int, int]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self.engine.begin() as conn:
            del_updates = conn.execute(
                delete(self.updates).where(self.updates.c.scraped_at < cutoff)
            )
            deleted_updates = del_updates.rowcount or 0

            del_logs = conn.execute(
                delete(self.scraping_log).where(self.scraping_log.c.scraped_at < cutoff)
            )
            deleted_logs = del_logs.rowcount or 0

        self.logger.info(
            f"Cleanup completed: {deleted_updates} old updates and {deleted_logs} old logs deleted"
        )
        return deleted_updates, deleted_logs

    def get_database_stats(self) -> Dict[str, Any]:
        with self.engine.connect() as conn:
            total_updates = conn.execute(select(func.count()).select_from(self.updates)).scalar() or 0

            updates_by_source_rows = conn.execute(
                select(self.updates.c.source, func.count()).group_by(self.updates.c.source)
            ).all()
            updates_by_source = {row[0]: row[1] for row in updates_by_source_rows}

            updates_by_exam_type_rows = conn.execute(
                select(self.updates.c.exam_type, func.count()).group_by(self.updates.c.exam_type)
            ).all()
            updates_by_exam_type = {row[0]: row[1] for row in updates_by_exam_type_rows}

            recent_updates = conn.execute(
                select(func.count()).select_from(self.updates).where(
                    self.updates.c.scraped_at > datetime.utcnow() - timedelta(hours=24)
                )
            ).scalar() or 0

        return {
            'total_updates': int(total_updates),
            'updates_by_source': updates_by_source,
            'updates_by_exam_type': updates_by_exam_type,
            'recent_updates_24h': int(recent_updates),
        }
