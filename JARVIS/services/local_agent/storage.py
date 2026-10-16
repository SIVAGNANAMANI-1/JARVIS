"""
JARVIS AI - Local Agent SQLite Storage
Manages local audit logs, execution cache, device preferences, and offline memory.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time


class LocalStorage:
    def __init__(self, db_path: str = "data/jarvis_local.db"):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Task history and audit log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    task_id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    target_device TEXT,
                    status TEXT NOT NULL,
                    result_summary TEXT,
                    error_message TEXT,
                    steps_json TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            # Local memory & preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_memory (
                    memory_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at REAL
                )
            """)
            # Device configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_config (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_task(self, task_data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_history (
                    task_id, command, target_device, status,
                    result_summary, error_message, steps_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    result_summary = excluded.result_summary,
                    error_message = excluded.error_message,
                    steps_json = excluded.steps_json,
                    updated_at = excluded.updated_at
            """, (
                task_data["task_id"],
                task_data.get("command", ""),
                task_data.get("target_device_id", "local"),
                task_data.get("status", "SUBMITTED"),
                task_data.get("result_summary"),
                task_data.get("error_message"),
                json.dumps(task_data.get("steps", [])),
                task_data.get("created_at", time.time()),
                time.time()
            ))
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_history WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["steps"] = json.loads(data["steps_json"]) if data.get("steps_json") else []
            return data

    def list_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_history ORDER BY updated_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["steps"] = json.loads(item["steps_json"]) if item.get("steps_json") else []
                results.append(item)
            return results

    def set_memory(self, category: str, key: str, value: str) -> str:
        memory_id = f"mem_{category}_{key}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO local_memory (memory_id, category, key, value, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (memory_id, category, key, value, time.time()))
            conn.commit()
        return memory_id

    def get_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM local_memory WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT * FROM local_memory")
            return [dict(r) for r in cursor.fetchall()]

    def delete_memory(self, memory_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM local_memory WHERE memory_id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
