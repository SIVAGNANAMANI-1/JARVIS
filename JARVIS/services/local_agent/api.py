"""
JARVIS AI - Local Agent REST & WebSocket API
The local edge server running on Windows for device automation, process control, and task execution.
"""

import os
import platform
import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.shared_types.models import (
    DeviceInfo,
    DeviceType,
    DeviceStatus,
    TaskRequest,
    TaskStep,
    TaskStatus,
    RiskLevel,
    ApprovalDecision,
    UserMemory
)
from packages.security_policy.policy import SecurityPolicyEngine
from services.local_agent.storage import LocalStorage
from services.local_agent.process_manager import ProcessManager
from services.local_agent.workspace_runner import WorkspaceRunner
from services.local_agent.file_ops import FileOperations
from integrations.spotify.adapter import SpotifyAdapter
from integrations.browser.adapter import BrowserAdapter
from integrations.vscode.adapter import VSCodeAdapter
from integrations.office.adapter import OfficeDocumentAdapter
from services.agent_core.bedrock_client import BedrockModelProvider
from services.agent_core.qa_engine import QAEngine

app = FastAPI(
    title="JARVIS AI - Local Edge Agent",
    version="1.0.0",
    description="Local Windows edge automation service for JARVIS AI"
)

# CORS middleware for desktop (Electron) and local web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
storage = LocalStorage()
process_mgr = ProcessManager()
workspace_runner = WorkspaceRunner()
file_ops = FileOperations()
security_engine = SecurityPolicyEngine(str(workspace_runner.workspace_root))
bedrock_provider = BedrockModelProvider()
qa_engine = QAEngine(bedrock_provider)

spotify_adapter = SpotifyAdapter(process_mgr)
browser_adapter = BrowserAdapter(process_mgr)
vscode_adapter = VSCodeAdapter(process_mgr, workspace_runner)
office_adapter = OfficeDocumentAdapter()


# Active WebSocket connections
active_connections: List[WebSocket] = []


async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Sends live updates to all connected clients (desktop UI, web, mobile)."""
    payload = {"event": event_type, "timestamp": time.time(), "data": data}
    dead_connections = []
    for conn in active_connections:
        try:
            await conn.send_json(payload)
        except Exception:
            dead_connections.append(conn)
    for dc in dead_connections:
        if dc in active_connections:
            active_connections.remove(dc)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "jarvis-local-agent",
        "platform": platform.system(),
        "os_version": platform.version(),
        "node": platform.node(),
        "workspace_root": str(workspace_runner.workspace_root),
        "timestamp": time.time()
    }


@app.get("/device/info", response_model=DeviceInfo)
def get_device_info():
    return DeviceInfo(
        device_id="win_desktop_" + platform.node().lower(),
        user_id="default_user",
        device_name=f"Windows PC ({platform.node()})",
        device_type=DeviceType.WINDOWS,
        os_version=f"{platform.system()} {platform.release()}",
        status=DeviceStatus.ONLINE,
        capabilities=[
            "process_launch",
            "vscode_automation",
            "workspace_code_execution",
            "file_system_analysis",
            "browser_navigation",
            "spotify_control",
            "document_generation"
        ]
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial device status
        await websocket.send_json({
            "event": "connected",
            "device": get_device_info().model_dump()
        })
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping / messages if needed
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


class DirectCommandPayload(BaseModel):
    command: str
    target_device_id: Optional[str] = "local"
    user_id: Optional[str] = "default_user"


@app.post("/tasks/execute")
async def execute_task_endpoint(payload: DirectCommandPayload):
    """
    Submits a user command for planning, tool execution, and verification.
    """
    task = TaskRequest(
        task_id=f"task_{uuid.uuid4().hex[:10]}",
        user_id=payload.user_id or "default_user",
        command=payload.command,
        origin_device_id="local",
        target_device_id=payload.target_device_id or "local",
        status=TaskStatus.SUBMITTED
    )
    storage.save_task(task.model_dump())
    await broadcast_event("task_created", task.model_dump())

    # Decompose command and execute
    task.status = TaskStatus.RUNNING
    await broadcast_event("task_running", task.model_dump())

    cmd_lower = payload.command.lower()
    executed_steps = []
    result_summary = ""

    try:
        # Workflow 0: Direct General Question Answering (Math, Science, Concepts, Knowledge)
        if qa_engine.is_question(payload.command):
            step = TaskStep(
                tool_name="answer_question",
                action_description=f"Answer question: {payload.command}",
                risk_level=RiskLevel.LOW
            )
            ans_res = qa_engine.answer(payload.command)
            step.output = ans_res
            step.verified = ans_res.get("verified", True)
            step.status = TaskStatus.COMPLETED
            executed_steps.append(step)
            result_summary = ans_res.get("answer", "Answer retrieved.")

        # Workflow 1: Spotify
        elif "spotify" in cmd_lower:

            step = TaskStep(
                tool_name="spotify_control",
                action_description="Control Spotify playback / playlist",
                risk_level=RiskLevel.LOW
            )
            if "playlist" in cmd_lower:
                query = cmd_lower.split("playlist")[-1].strip() or "study playlist"
                res = spotify_adapter.open_playlist(query)
            else:
                res = spotify_adapter.launch()

            step.output = res
            step.verified = res.get("verified", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = res.get("message", "Spotify task executed.")

        # Workflow 2: YouTube / Video
        elif "youtube" in cmd_lower:
            step = TaskStep(
                tool_name="browser_search_youtube",
                action_description="Search YouTube and open video results",
                risk_level=RiskLevel.LOW
            )
            res = browser_adapter.search_youtube(payload.command)
            step.output = res
            step.verified = res.get("verified", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = res.get("message", "YouTube search executed.")

        # Workflow 3: Online Code Compilers (e.g. Python online compiler & Hello World)
        elif "compiler" in cmd_lower or ("python" in cmd_lower and "online" in cmd_lower) or ("python" in cmd_lower and "hello world" in cmd_lower):
            # Step 1: Open online compiler URL
            step1 = TaskStep(
                tool_name="open_online_compiler",
                action_description="Open interactive online Python compiler",
                risk_level=RiskLevel.LOW
            )
            res_browser = browser_adapter.open_online_compiler("python")
            step1.output = res_browser
            step1.verified = res_browser.get("verified", False)
            step1.status = TaskStatus.COMPLETED
            executed_steps.append(step1)

            # Step 2: Write and execute code locally in workspace
            step2 = TaskStep(
                tool_name="workspace_run_code",
                action_description="Write Hello World script in workspace, execute, and verify stdout",
                risk_level=RiskLevel.MODERATE
            )
            code_content = "# JARVIS AI - Hello World Program\ndef main():\n    print('Hello World from JARVIS!')\n\nif __name__ == '__main__':\n    main()\n"
            workspace_runner.write_code_file("hello_world.py", code_content)
            res_exec = workspace_runner.execute_python_script("hello_world.py", expected_output="Hello World from JARVIS!")
            step2.output = res_exec
            step2.verified = res_exec.get("verified", False)
            step2.status = TaskStatus.COMPLETED if res_exec.get("success") else TaskStatus.FAILED
            executed_steps.append(step2)

            result_summary = f"Opened online compiler at {res_browser.get('url')}. Executed Python code locally: stdout='{res_exec.get('stdout')}' (verified={res_exec.get('verified')})."

        # Workflow 4: VS Code / Python file creation & execution
        elif "vs code" in cmd_lower or "vscode" in cmd_lower or ("python" in cmd_lower and "program" in cmd_lower):
            step = TaskStep(
                tool_name="vscode_run_program",
                action_description="Create Python program in approved workspace, execute, and verify",
                risk_level=RiskLevel.MODERATE
            )
            filename = "assignment.py"
            code = (
                "# Generated by JARVIS AI\n"
                "import sys\n\n"
                "def main():\n"
                "    print('Hello from JARVIS Autonomous Workspace!')\n"
                "    print(f'Python Version: {sys.version.split()[0]}')\n"
                "    total = sum(i**2 for i in range(1, 11))\n"
                "    print(f'Computed sum of squares 1..10: {total}')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
            res = vscode_adapter.create_and_run_python(
                filename=filename,
                code_content=code,
                expected_output="Computed sum of squares 1..10: 385",
                open_in_editor=True
            )
            step.output = res
            step.verified = res.get("verified", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = f"Created {filename}, executed: stdout='{res.get('stdout')}', verified={res.get('verified')}."

        # Workflow 5: Duplicate files scan
        elif "duplicate" in cmd_lower:
            step = TaskStep(
                tool_name="find_duplicate_files",
                action_description="Scan workspace files and identify SHA-256 duplicates",
                risk_level=RiskLevel.LOW
            )
            res = file_ops.find_duplicate_files()
            step.output = res
            step.verified = res.get("success", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = f"Scanned {res.get('total_files_scanned', 0)} files. Found {res.get('duplicate_groups_count', 0)} duplicate groups."

        # Workflow 6: Attendance spreadsheet calculation & report
        elif "attendance" in cmd_lower:
            step1 = TaskStep(
                tool_name="analyze_attendance",
                action_description="Analyze attendance statistics",
                risk_level=RiskLevel.LOW
            )
            sample_attendance_csv = workspace_runner.workspace_root / "attendance.csv"
            if not sample_attendance_csv.exists():
                sample_attendance_csv.write_text(
                    "Name,Day1,Day2,Day3,Day4,Day5,Day6,Day7,Day8,Day9,Day10\n"
                    "Alice,P,P,P,P,P,P,P,P,P,P\n"
                    "Bob,P,A,P,P,A,P,A,P,A,P\n"
                    "Charlie,P,P,P,A,P,P,P,P,P,P\n"
                    "David,A,A,P,A,A,P,A,P,A,A\n",
                    encoding="utf-8"
                )
            
            res_analysis = file_ops.analyze_attendance_sheet("attendance.csv")
            step1.output = res_analysis
            step1.verified = res_analysis.get("success", False)
            step1.status = TaskStatus.COMPLETED
            executed_steps.append(step1)

            step2 = TaskStep(
                tool_name="generate_attendance_report",
                action_description="Generate Markdown attendance report",
                risk_level=RiskLevel.LOW
            )
            res_report = office_adapter.generate_attendance_report(res_analysis)
            step2.output = res_report
            step2.verified = res_report.get("verified", False)
            step2.status = TaskStatus.COMPLETED
            executed_steps.append(step2)
            result_summary = f"Analyzed attendance: avg={res_analysis.get('overall_attendance_average')}%. Report generated at: {res_report.get('filename')}."

        # Workflow 7: Remember preference / Memory
        elif "remember" in cmd_lower:
            step = TaskStep(
                tool_name="save_memory",
                action_description="Store user preference into persistent memory",
                risk_level=RiskLevel.LOW
            )
            preference_text = payload.command.replace("remember", "").replace("that", "").strip()
            mem_id = storage.set_memory("preference", "user_stated_preference", preference_text)
            step.output = {"memory_id": mem_id, "saved": preference_text}
            step.verified = True
            step.status = TaskStatus.COMPLETED
            executed_steps.append(step)
            result_summary = f"Remembered preference: '{preference_text}'"

        # Workflow 8: Specific desktop apps (Notepad, Calculator, Terminal, etc.)
        elif any(app in cmd_lower for app in ["notepad", "calculator", "calc", "terminal", "powershell", "cmd", "explorer"]):
            app_target = "notepad"
            for candidate in ["notepad", "calculator", "calc", "terminal", "powershell", "cmd", "explorer"]:
                if candidate in cmd_lower:
                    app_target = candidate
                    break
            step = TaskStep(
                tool_name="launch_application",
                action_description=f"Launch application '{app_target}'",
                risk_level=RiskLevel.LOW
            )
            res = process_mgr.launch_application(app_target)
            step.output = res
            step.verified = res.get("verified", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = res.get("message", f"Application '{app_target}' invocation finished.")

        # Workflow 9: Smart Web Navigation (Amazon, E-commerce, Google, Wikipedia, URLs)
        else:
            step = TaskStep(
                tool_name="browser_smart_navigate",
                action_description=f"Navigate to requested destination: {payload.command}",
                risk_level=RiskLevel.LOW
            )
            res = browser_adapter.smart_navigate(payload.command)
            step.output = res
            step.verified = res.get("verified", False)
            step.status = TaskStatus.COMPLETED if res.get("success") else TaskStatus.FAILED
            executed_steps.append(step)
            result_summary = res.get("message", f"Navigated to: {res.get('url')}")


        task.steps = executed_steps
        task.result_summary = result_summary
        task.status = TaskStatus.COMPLETED if all(s.status == TaskStatus.COMPLETED for s in executed_steps) else TaskStatus.FAILED

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        result_summary = f"Task execution failed: {str(e)}"

    task.updated_at = time.time()
    storage.save_task(task.model_dump())
    await broadcast_event("task_updated", task.model_dump())

    return task


@app.get("/tasks/recent")
def list_recent_tasks():
    return storage.list_recent_tasks()


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = TaskStatus.CANCELLED
    task["updated_at"] = time.time()
    task["error_message"] = "Cancelled by user emergency stop."
    storage.save_task(task)
    await broadcast_event("task_cancelled", task)
    return {"message": "Task cancelled successfully", "task": task}


@app.get("/memory")
def get_memories(category: Optional[str] = None):
    return storage.get_memories(category)


@app.post("/memory")
def save_memory(memory: UserMemory):
    mem_id = storage.set_memory(memory.category, memory.key, memory.value)
    return {"status": "saved", "memory_id": mem_id}


@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    deleted = storage.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "deleted", "memory_id": memory_id}


# Mount Web Dashboard
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

web_path = Path(__file__).resolve().parent.parent.parent / "apps" / "web"
if web_path.exists():
    css_path = web_path / "css"
    js_path = web_path / "js"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

    @app.get("/")
    def serve_dashboard():
        return FileResponse(str(web_path / "index.html"))

