"""
JARVIS AI - Hybrid Cloud & Emulation Storage Layer
Abstracts DynamoDB & S3 operations with automatic local fallback for zero-cost offline development.
"""

import os
import time
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from packages.shared_types.models import DeviceInfo, DeviceStatus, TaskStatus


class CloudStorageManager:
    def __init__(self, db_path: str = "data/cloud_emulation.db", s3_dir: str = "data/s3_artifacts"):
        self.region_name = os.environ.get("AWS_REGION", "us-east-1")
        self.tasks_table_name = os.environ.get("DYNAMODB_TASKS_TABLE", "JarvisTasks")
        self.devices_table_name = os.environ.get("DYNAMODB_DEVICES_TABLE", "JarvisDevices")
        self.s3_bucket_name = os.environ.get("S3_ARTIFACTS_BUCKET", "jarvis-artifacts-store")

        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.s3_dir = Path(s3_dir).resolve()
        self.s3_dir.mkdir(parents=True, exist_ok=True)

        self.aws_ready = False
        self._init_aws()
        self._init_sqlite()

    def _init_aws(self):
        try:
            session = boto3.Session(region_name=self.region_name)
            creds = session.get_credentials()
            if creds and creds.access_key:
                self.dynamo = session.resource("dynamodb", region_name=self.region_name)
                self.s3 = session.client("s3", region_name=self.region_name)
                # Test connectivity
                self.dynamo.Table(self.tasks_table_name).load()
                self.aws_ready = True
        except Exception:
            self.aws_ready = False

    def _init_sqlite(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS cloud_tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    origin_device_id TEXT,
                    target_device_id TEXT,
                    status TEXT NOT NULL,
                    result_summary TEXT,
                    error_message TEXT,
                    steps_json TEXT,
                    artifacts_json TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS cloud_devices (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    os_version TEXT,
                    status TEXT NOT NULL,
                    capabilities_json TEXT,
                    last_heartbeat REAL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS cloud_memory (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at REAL
                )
            """)
            conn.commit()

    # --- Task Management ---

    def save_task(self, task_data: Dict[str, Any]):
        if self.aws_ready:
            try:
                table = self.dynamo.Table(self.tasks_table_name)
                table.put_item(Item=task_data)
                return
            except Exception:
                pass

        # Emulated storage
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO cloud_tasks (
                    task_id, user_id, command, origin_device_id, target_device_id,
                    status, result_summary, error_message, steps_json, artifacts_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    result_summary = excluded.result_summary,
                    error_message = excluded.error_message,
                    steps_json = excluded.steps_json,
                    artifacts_json = excluded.artifacts_json,
                    updated_at = excluded.updated_at
            """, (
                task_data["task_id"],
                task_data.get("user_id", "default_user"),
                task_data.get("command", ""),
                task_data.get("origin_device_id", "web"),
                task_data.get("target_device_id", "win_desktop"),
                task_data.get("status", "SUBMITTED"),
                task_data.get("result_summary"),
                task_data.get("error_message"),
                json.dumps(task_data.get("steps", [])),
                json.dumps(task_data.get("artifacts", [])),
                task_data.get("created_at", time.time()),
                time.time()
            ))
            conn.commit()

    def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        # Enforce user boundary
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM cloud_tasks WHERE task_id = ? AND user_id = ?", (task_id, user_id))
            row = c.fetchone()
            if not row:
                return None
            data = dict(row)
            data["steps"] = json.loads(data["steps_json"]) if data.get("steps_json") else []
            data["artifacts"] = json.loads(data["artifacts_json"]) if data.get("artifacts_json") else []
            return data

    def list_tasks_for_device(self, target_device_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if status:
                c.execute("SELECT * FROM cloud_tasks WHERE target_device_id = ? AND status = ? ORDER BY created_at ASC", (target_device_id, status))
            else:
                c.execute("SELECT * FROM cloud_tasks WHERE target_device_id = ? ORDER BY created_at DESC LIMIT 20", (target_device_id,))
            rows = c.fetchall()
            res = []
            for r in rows:
                item = dict(r)
                item["steps"] = json.loads(item["steps_json"]) if item.get("steps_json") else []
                item["artifacts"] = json.loads(item["artifacts_json"]) if item.get("artifacts_json") else []
                res.append(item)
            return res

    # --- Device Registry ---

    def register_device(self, device: DeviceInfo):
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO cloud_devices (
                    device_id, user_id, device_name, device_type, os_version,
                    status, capabilities_json, last_heartbeat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    device_name = excluded.device_name,
                    status = excluded.status,
                    capabilities_json = excluded.capabilities_json,
                    last_heartbeat = excluded.last_heartbeat
            """, (
                device.device_id,
                device.user_id,
                device.device_name,
                device.device_type.value,
                device.os_version,
                device.status.value,
                json.dumps(device.capabilities),
                time.time()
            ))
            conn.commit()

    def list_devices(self, user_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM cloud_devices WHERE user_id = ?", (user_id,))
            rows = c.fetchall()
            devices = []
            now = time.time()
            for r in rows:
                item = dict(r)
                item["capabilities"] = json.loads(item["capabilities_json"]) if item.get("capabilities_json") else []
                # Check heartbeat: offline if no heartbeat in 60s
                if now - item.get("last_heartbeat", 0) > 60:
                    item["status"] = DeviceStatus.OFFLINE.value
                devices.append(item)
            return devices

    def save_artifact(self, filename: str, content: bytes, user_id: str) -> str:
        """Stores artifact into S3 bucket or local emulated artifact path."""
        safe_key = f"{user_id}/{filename}"
        if self.aws_ready:
            try:
                self.s3.put_object(Bucket=self.s3_bucket_name, Key=safe_key, Body=content)
                return f"s3://{self.s3_bucket_name}/{safe_key}"
            except Exception:
                pass

        user_dir = self.s3_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_dir / filename
        file_path.write_bytes(content)
        return str(file_path)
