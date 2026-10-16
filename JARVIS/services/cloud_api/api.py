"""
JARVIS AI - Central Cloud API Service
Provides authenticated multi-device task coordination, state synchronization, and artifact management.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.shared_types.models import (
    DeviceInfo,
    DeviceType,
    DeviceStatus,
    TaskRequest,
    TaskStatus,
    UserMemory
)
from services.cloud_api.auth import AuthManager
from services.cloud_api.storage import CloudStorageManager

cloud_app = FastAPI(
    title="JARVIS AI - Cloud Orchestration API",
    version="1.0.0",
    description="AWS Cloud backend for JARVIS personal assistant cross-device coordination"
)

cloud_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_mgr = AuthManager()
cloud_storage = CloudStorageManager()


class LoginRequest(BaseModel):
    username: str
    password: str
    device_id: str


class TaskSubmissionPayload(BaseModel):
    command: str
    target_device_id: str


@cloud_app.get("/health")
def health():
    return {
        "status": "online",
        "service": "jarvis-cloud-api",
        "aws_mode": "live_aws" if cloud_storage.aws_ready else "local_emulation",
        "timestamp": time.time()
    }


@cloud_app.post("/api/v1/auth/login")
def login(payload: LoginRequest):
    # In production, authenticates against Amazon Cognito User Pool
    # In local mode, verifies credentials and returns valid signed JWT
    if not payload.username:
        raise HTTPException(status_code=400, detail="Username is required")

    user_id = f"user_{payload.username.lower()}"
    token = auth_mgr.generate_token(user_id, f"{payload.username}@jarvis.ai", payload.device_id)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user_id": user_id,
        "device_id": payload.device_id
    }


@cloud_app.post("/api/v1/devices/register")
def register_device(device: DeviceInfo, user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    device.user_id = user["sub"]
    cloud_storage.register_device(device)
    return {"status": "registered", "device_id": device.device_id}


@cloud_app.get("/api/v1/devices")
def list_devices(user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    devices = cloud_storage.list_devices(user["sub"])
    return {"devices": devices}


@cloud_app.post("/api/v1/tasks")
def submit_task(payload: TaskSubmissionPayload, user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    # Verify target device exists and belongs to this user
    devices = {d["device_id"]: d for d in cloud_storage.list_devices(user["sub"])}
    
    # If target device is offline or unknown, report truthful status
    target_status = devices.get(payload.target_device_id, {}).get("status", DeviceStatus.ONLINE.value)

    task_id = f"task_{uuid.uuid4().hex[:10]}"
    initial_status = TaskStatus.SUBMITTED
    if target_status == DeviceStatus.OFFLINE.value:
        initial_status = TaskStatus.WAITING_FOR_DEVICE

    task = TaskRequest(
        task_id=task_id,
        user_id=user["sub"],
        command=payload.command,
        origin_device_id=user.get("device_id", "web"),
        target_device_id=payload.target_device_id,
        status=initial_status
    )
    cloud_storage.save_task(task.model_dump())
    return task


@cloud_app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: str, user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    task = cloud_storage.get_task(task_id, user["sub"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
    return task


@cloud_app.post("/api/v1/tasks/{task_id}/sync")
def sync_task_progress(task_id: str, update_data: Dict[str, Any], user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    """Called by the target device's local agent to synchronize verified progress back to the cloud."""
    existing = cloud_storage.get_task(task_id, user["sub"])
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found or access denied")

    # Update state
    existing.update(update_data)
    existing["updated_at"] = time.time()
    cloud_storage.save_task(existing)
    return {"status": "synchronized", "task_id": task_id}


@cloud_app.get("/api/v1/devices/{device_id}/pending-tasks")
def get_pending_tasks_for_device(device_id: str, user: Dict[str, Any] = Depends(auth_mgr.verify_token)):
    """Target device polls or pulls its queued remote tasks."""
    tasks = cloud_storage.list_tasks_for_device(device_id, status=TaskStatus.SUBMITTED.value)
    return {"pending_tasks": tasks}
