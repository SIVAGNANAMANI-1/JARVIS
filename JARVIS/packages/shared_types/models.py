"""
JARVIS AI - Shared Type Definitions and Data Models
Defines core data contracts across local agents, cloud APIs, and clients.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time
import uuid


class RiskLevel(str, Enum):
    LOW = "LOW"            # Read-only, opening apps, checking status, safe workspace ops
    MODERATE = "MODERATE"  # Modifying files, editing code, changing non-critical configs
    HIGH = "HIGH"          # Deleting files, sending emails, shell outside workspace, payment


class TaskStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    WAITING_FOR_DEVICE = "WAITING_FOR_DEVICE"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DeviceType(str, Enum):
    WINDOWS = "WINDOWS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB = "WEB"
    MACOS = "MACOS"
    LINUX = "LINUX"


class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    BUSY = "BUSY"


class DeviceInfo(BaseModel):
    device_id: str
    user_id: str
    device_name: str
    device_type: DeviceType
    os_version: str
    status: DeviceStatus = DeviceStatus.ONLINE
    capabilities: List[str] = Field(default_factory=list)
    last_heartbeat: float = Field(default_factory=time.time)


class TaskStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str
    action_description: str
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    approved: Optional[bool] = None
    input_args: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    verified: bool = False
    verification_details: Optional[str] = None
    status: TaskStatus = TaskStatus.SUBMITTED
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    user_id: str = "default_user"
    command: str
    origin_device_id: str
    target_device_id: str
    status: TaskStatus = TaskStatus.SUBMITTED
    steps: List[TaskStep] = Field(default_factory=list)
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ApprovalRequest(BaseModel):
    task_id: str
    step_id: str
    action_summary: str
    risk_level: RiskLevel
    details: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    task_id: str
    step_id: str
    approved: bool
    user_id: str
    reason: Optional[str] = None


class UserMemory(BaseModel):
    memory_id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:8]}")
    user_id: str
    category: str = "preference"  # "preference", "fact", "workflow"
    key: str
    value: str
    timestamp: float = Field(default_factory=time.time)
