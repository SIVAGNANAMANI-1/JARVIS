"""
JARVIS AI - Automated Unit & Integration Tests
Validates local agent capabilities, workspace execution sandbox, security policy, and adapters.
"""

import os
import pytest
from pathlib import Path
from packages.shared_types.models import RiskLevel, TaskStep, TaskStatus
from packages.security_policy.policy import SecurityPolicyEngine
from services.local_agent.workspace_runner import WorkspaceRunner
from services.local_agent.file_ops import FileOperations
from services.local_agent.process_manager import ProcessManager
from services.local_agent.storage import LocalStorage
from integrations.office.adapter import OfficeDocumentAdapter


@pytest.fixture
def test_workspace(tmp_path):
    ws = tmp_path / "test_workspace"
    ws.mkdir()
    return str(ws)


def test_security_policy_sandboxing(test_workspace):
    policy = SecurityPolicyEngine(test_workspace)

    # Within workspace
    safe_path = policy.sanitize_workspace_path("scripts/test.py")
    assert str(safe_path).startswith(str(Path(test_workspace).resolve()))

    # Traversal attempt outside workspace
    with pytest.raises(PermissionError):
        policy.sanitize_workspace_path("../../secret.txt")


def test_security_risk_classification(test_workspace):
    policy = SecurityPolicyEngine(test_workspace)

    # Low risk
    step_low = TaskStep(tool_name="spotify_control", action_description="Play music")
    risk, approval = policy.evaluate_step(step_low)
    assert risk == RiskLevel.LOW
    assert approval is False

    # Moderate risk
    step_mod = TaskStep(tool_name="create_file", action_description="Create assignment.py")
    risk, approval = policy.evaluate_step(step_mod)
    assert risk == RiskLevel.MODERATE
    assert approval is False

    # High risk
    step_high = TaskStep(tool_name="delete_file", action_description="Delete folder")
    risk, approval = policy.evaluate_step(step_high)
    assert risk == RiskLevel.HIGH
    assert approval is True


def test_workspace_code_execution_and_verification(test_workspace):
    runner = WorkspaceRunner(test_workspace)

    # 1. Write Python file
    code = (
        "import sys\n"
        "vals = [1, 2, 3, 4, 5]\n"
        "print('RESULT_SUM=' + str(sum(vals)))\n"
    )
    write_res = runner.write_code_file("sum_test.py", code)
    assert write_res["success"] is True
    assert write_res["verified"] is True

    # 2. Execute and verify expected output
    exec_res = runner.execute_python_script("sum_test.py", expected_output="RESULT_SUM=15")
    assert exec_res["success"] is True
    assert exec_res["verified"] is True
    assert "RESULT_SUM=15" in exec_res["stdout"]

    # 3. Test failure on wrong expectation
    exec_res_fail = runner.execute_python_script("sum_test.py", expected_output="UNMATCHED_STRING")
    assert exec_res_fail["verified"] is False


def test_file_operations_and_duplicates(test_workspace):
    file_ops = FileOperations(test_workspace)
    ws_path = Path(test_workspace)

    # Create two duplicate files and one distinct file
    (ws_path / "doc1.txt").write_text("JARVIS Duplicate Content Test", encoding="utf-8")
    (ws_path / "doc2.txt").write_text("JARVIS Duplicate Content Test", encoding="utf-8")
    (ws_path / "unique.txt").write_text("Unique Content", encoding="utf-8")

    result = file_ops.find_duplicate_files(test_workspace)
    assert result["success"] is True
    assert result["total_files_scanned"] == 3
    assert result["duplicate_groups_count"] == 1
    assert result["reclaimable_bytes"] > 0


def test_attendance_analysis_and_report(test_workspace):
    file_ops = FileOperations(test_workspace)
    ws_path = Path(test_workspace)

    # Create CSV
    csv_path = ws_path / "attendance.csv"
    csv_path.write_text(
        "Student,Mon,Tue,Wed,Thu,Fri\n"
        "Alice,P,P,P,P,P\n"
        "Bob,A,A,P,A,A\n",
        encoding="utf-8"
    )

    analysis = file_ops.analyze_attendance_sheet(str(csv_path))
    assert analysis["success"] is True
    assert analysis["total_individuals"] == 2
    assert analysis["below_75_percent_count"] == 1  # Bob is 20%

    # Generate document report
    reporter = OfficeDocumentAdapter(str(ws_path / "reports"))
    report = reporter.generate_attendance_report(analysis)
    assert report["success"] is True
    assert report["verified"] is True
    assert Path(report["report_path"]).exists()


def test_local_storage_crud(tmp_path):
    db_file = tmp_path / "test_jarvis.db"
    store = LocalStorage(str(db_file))

    # Test memory
    mem_id = store.set_memory("preference", "favorite_language", "Python")
    memories = store.get_memories("preference")
    assert len(memories) == 1
    assert memories[0]["value"] == "Python"

    # Test task persistence
    store.save_task({
        "task_id": "test_t1",
        "command": "Test Command",
        "status": "COMPLETED",
        "result_summary": "Success"
    })
    saved = store.get_task("test_t1")
    assert saved is not None
    assert saved["status"] == "COMPLETED"


def test_process_manager_lookup():
    pm = ProcessManager()
    # Check that notepad or cmd or calc is registered
    notepad = pm.find_executable("notepad")
    assert notepad is not None or os.name == 'nt'
