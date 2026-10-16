"""
JARVIS AI - VS Code & Python Programming Adapter
Manages workspace file creation, opens VS Code, executes programs, and verifies output.
"""

from typing import Dict, Any, Optional
from services.local_agent.process_manager import ProcessManager
from services.local_agent.workspace_runner import WorkspaceRunner


class VSCodeAdapter:
    def __init__(
        self,
        process_manager: Optional[ProcessManager] = None,
        workspace_runner: Optional[WorkspaceRunner] = None
    ):
        self.pm = process_manager or ProcessManager()
        self.runner = workspace_runner or WorkspaceRunner()

    def open_workspace(self, relative_subfolder: Optional[str] = None) -> Dict[str, Any]:
        """Opens the VS Code editor pointing to the approved workspace."""
        target_path = str(self.runner.workspace_root)
        if relative_subfolder:
            target_path = str(self.runner.workspace_root / relative_subfolder)

        res = self.pm.launch_application("vscode", [target_path])
        return {
            "success": res.get("success", False),
            "action": "open_workspace",
            "path": target_path,
            "verified": res.get("verified", False),
            "message": f"Opened VS Code at '{target_path}'."
        }

    def open_file(self, filename: str) -> Dict[str, Any]:
        """Opens a specific file in VS Code."""
        safe_path = self.runner.policy.sanitize_workspace_path(filename)
        res = self.pm.launch_application("vscode", [str(safe_path)])
        return {
            "success": res.get("success", False),
            "action": "open_file",
            "file": str(safe_path),
            "verified": res.get("verified", False),
            "message": f"Opened file '{filename}' in VS Code."
        }

    def create_and_run_python(
        self,
        filename: str,
        code_content: str,
        expected_output: Optional[str] = None,
        open_in_editor: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a Python program file in the approved workspace,
        optionally opens it in VS Code, executes it, and verifies stdout.
        """
        write_res = self.runner.write_code_file(filename, code_content)
        if not write_res.get("success"):
            return write_res

        if open_in_editor:
            self.open_file(filename)

        exec_res = self.runner.execute_python_script(
            filename=filename,
            expected_output=expected_output
        )

        return {
            "success": exec_res.get("success", False),
            "action": "create_and_run_python",
            "file_path": write_res.get("file_path"),
            "stdout": exec_res.get("stdout"),
            "stderr": exec_res.get("stderr"),
            "verified": exec_res.get("verified", False),
            "duration_seconds": exec_res.get("duration_seconds"),
            "message": f"Created '{filename}', executed with returncode {exec_res.get('return_code')}, output verified: {exec_res.get('verified')}."
        }
