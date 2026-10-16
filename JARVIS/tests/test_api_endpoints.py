"""
JARVIS AI - API Endpoint Integration Tests
Tests local agent REST endpoints with genuine payloads and verification assertions.
"""

from fastapi.testclient import TestClient
from services.local_agent.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "jarvis-local-agent"
    assert "platform" in data


def test_device_info_endpoint():
    response = client.get("/device/info")
    assert response.status_code == 200
    data = response.json()
    assert data["device_type"] == "WINDOWS"
    assert data["status"] == "ONLINE"
    assert "workspace_code_execution" in data["capabilities"]


def test_execute_python_assignment_workflow():
    payload = {
        "command": "Open VS Code, create a Python file, write a program, execute it, and show me the output.",
        "target_device_id": "local"
    }
    response = client.post("/tasks/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert len(data["steps"]) >= 1
    step = data["steps"][0]
    assert step["verified"] is True
    assert "385" in data["result_summary"]


def test_execute_attendance_analysis_workflow():
    payload = {
        "command": "Find the attendance spreadsheet, calculate the monthly statistics, and create a report.",
        "target_device_id": "local"
    }
    response = client.post("/tasks/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert len(data["steps"]) == 2
    assert data["steps"][0]["verified"] is True
    assert data["steps"][1]["verified"] is True


def test_execute_duplicate_files_workflow():
    payload = {
        "command": "Find duplicate files in my Downloads folder and show me what can be removed.",
        "target_device_id": "local"
    }
    response = client.post("/tasks/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["steps"][0]["verified"] is True


def test_memory_crud_flow():
    # 1. Save memory
    mem_payload = {
        "user_id": "default_user",
        "category": "preference",
        "key": "ml_framework",
        "value": "PyTorch and Python"
    }
    save_resp = client.post("/memory", json=mem_payload)
    assert save_resp.status_code == 200
    mem_id = save_resp.json()["memory_id"]

    # 2. Retrieve memories
    get_resp = client.get("/memory?category=preference")
    assert get_resp.status_code == 200
    memories = get_resp.json()
    assert any(m["key"] == "ml_framework" for m in memories)

    # 3. Delete memory
    del_resp = client.delete(f"/memory/{mem_id}")
    assert del_resp.status_code == 200


def test_dashboard_serve():
    response = client.get("/")
    assert response.status_code == 200
    assert "JARVIS AI" in response.text
    assert "Autonomous Edge & Cloud Operator" in response.text


def test_question_answering_endpoint():
    # Test calculation question
    payload = {"command": "What is 25 * 48?", "target_device_id": "local"}
    response = client.post("/tasks/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "1200" in data["result_summary"]
    assert any(s["tool_name"] == "answer_question" for s in data["steps"])

    # Test general concept question
    payload_concept = {"command": "What is quantum computing?", "target_device_id": "local"}
    resp_concept = client.post("/tasks/execute", json=payload_concept)
    assert resp_concept.status_code == 200
    data_concept = resp_concept.json()
    assert data_concept["status"] == "COMPLETED"
    assert len(data_concept["result_summary"]) > 20


def test_smart_navigation_endpoint():
    payload = {"command": "go to amazon and find belts for men", "target_device_id": "local"}
    response = client.post("/tasks/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert any("amazon.com" in s["output"].get("url", "") for s in data["steps"])


