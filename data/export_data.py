import json
import os
from datetime import datetime
from typing import List, Dict, Any

from config.settings import JSON_BACKUP_PATH
from data.storage import DataStorage


class DataExporter:
    def __init__(self, storage: DataStorage | None = None):
        self.storage = storage or DataStorage()

    def _write_file(self, data: List[Dict[str, Any]], prefix: str) -> str:
        os.makedirs(JSON_BACKUP_PATH, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(JSON_BACKUP_PATH, f"{prefix}_{ts}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def export_to_json(self, hours: int = 720, limit: int = 1000) -> str:
        """Export recent updates (default last 30 days)."""
        data = self.storage.get_recent_updates(hours=hours, limit=limit)
        return self._write_file(data, 'export_all')

    def export_latest_data(self, hours: int = 24, limit: int = 500) -> str:
        data = self.storage.get_recent_updates(hours=hours, limit=limit)
        return self._write_file(data, 'export_latest')

    def export_by_exam_type(self, exam_type: str, limit: int = 1000) -> str:
        data = self.storage.get_updates_by_exam_type(exam_type, limit=limit)
        return self._write_file(data, f"export_{exam_type.lower()}")



