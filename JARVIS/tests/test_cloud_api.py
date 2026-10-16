"""
JARVIS AI - Cloud API & Cross-Device Coordination Tests
Validates authentication, device registration, remote task delivery, and cross-user isolation.
"""

from fastapi.testclient import TestClient
from services.cloud_api.api import cloud_app
from packages.shared_types.models import DeviceType, DeviceStatus

client = TestClient(cloud_app)


def test_auth_login():
    resp = client.post("/api/v1/auth/login", json={
        "username": "siva",
        "password": "valid_password_123",
        "device_id": "phone_android_01"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user_id"] == "user_siva"
    assert data["token_type"] == "Bearer"


def test_device_registration_and_listing():
    # 1. Login user
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "siva",
        "password": "password",
        "device_id": "phone_android_01"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register Windows Laptop
    win_device = {
        "device_id": "laptop_win_01",
        "user_id": "user_siva",
        "device_name": "Siva's Windows Laptop",
        "device_type": "WINDOWS",
        "os_version": "Windows 11",
        "status": "ONLINE",
        "capabilities": ["vscode_automation", "workspace_code_execution", "spotify_control"]
    }
    reg_resp = client.post("/api/v1/devices/register", json=win_device, headers=headers)
    assert reg_resp.status_code == 200

    # 3. List devices
    list_resp = client.get("/api/v1/devices", headers=headers)
    assert list_resp.status_code == 200
    devices = list_resp.json()["devices"]
    assert any(d["device_id"] == "laptop_win_01" for d in devices)


def test_cross_device_task_submission_and_sync():
    """
    Scenario: User Siva on his Android phone asks his Windows Laptop to run an assignment.
    """
    # 1. Login Siva on Android
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "siva",
        "password": "password",
        "device_id": "phone_android_01"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Android submits task targeting Windows Laptop
    task_payload = {
        "command": "Open VS Code on my laptop and run my Python assignment.",
        "target_device_id": "laptop_win_01"
    }
    submit_resp = client.post("/api/v1/tasks", json=task_payload, headers=headers)
    assert submit_resp.status_code == 200
    task_data = submit_resp.json()
    task_id = task_data["task_id"]
    assert task_data["target_device_id"] == "laptop_win_01"

    # 3. Windows Laptop queries pending tasks
    pending_resp = client.get("/api/v1/devices/laptop_win_01/pending-tasks", headers=headers)
    assert pending_resp.status_code == 200
    pending_tasks = pending_resp.json()["pending_tasks"]
    assert any(t["task_id"] == task_id for t in pending_tasks)

    # 4. Windows Laptop executes and syncs progress
    sync_payload = {
        "status": "COMPLETED",
        "result_summary": "Executed Python assignment successfully. Output verified: returncode=0, stdout='Verified'."
    }
    sync_resp = client.post(f"/api/v1/tasks/{task_id}/sync", json=sync_payload, headers=headers)
    assert sync_resp.status_code == 200

    # 5. Android checks task status and sees verified completion
    get_resp = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert get_resp.status_code == 200
    updated_task = get_resp.json()
    assert updated_task["status"] == "COMPLETED"
    assert "Executed Python assignment successfully" in updated_task["result_summary"]


def test_cross_user_security_isolation():
    """
    User B should NEVER be able to read or tamper with User A's tasks or devices.
    """
    # Login User A
    login_a = client.post("/api/v1/auth/login", json={"username": "userA", "password": "pwd", "device_id": "devA"}).json()
    headers_a = {"Authorization": f"Bearer {login_a['access_token']}"}

    # User A creates a task
    t_resp = client.post("/api/v1/tasks", json={"command": "Secret Financial Audit", "target_device_id": "devA"}, headers=headers_a)
    task_id = t_resp.json()["task_id"]

    # Login User B
    login_b = client.post("/api/v1/auth/login", json={"username": "userB", "password": "pwd", "device_id": "devB"}).json()
    headers_b = {"Authorization": f"Bearer {login_b['access_token']}"}

    # User B attempts to access User A's task
    forbidden_resp = client.get(f"/api/v1/tasks/{task_id}", headers=headers_b)
    assert forbidden_resp.status_code == 404
