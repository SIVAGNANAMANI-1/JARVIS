"""
JARVIS AI - Approved Workspace Runner
Creates, executes, and verifies code files safely inside approved workspace directory.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
from packages.security_policy.policy import SecurityPolicyEngine


class WorkspaceRunner:
    def __init__(self, workspace_root: Optional[str] = None):
        if not workspace_root:
            # Default workspace inside JARVIS root
            workspace_root = str(Path(__file__).resolve().parent.parent.parent / "workspaces")
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.policy = SecurityPolicyEngine(str(self.workspace_root))

    def write_code_file(self, filename: str, code_content: str) -> Dict[str, Any]:
        """
        Safely writes code to a file inside the approved workspace.
        """
        try:
            safe_path = self.policy.sanitize_workspace_path(filename)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(code_content, encoding="utf-8")
            
            return {
                "success": True,
                "file_path": str(safe_path),
                "relative_path": str(safe_path.relative_to(self.workspace_root)),
                "bytes_written": len(code_content.encode("utf-8")),
                "verified": safe_path.exists() and safe_path.stat().st_size > 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file '{filename}': {str(e)}",
                "verified": False
            }

    def execute_python_script(
        self,
        filename: str,
        timeout_seconds: int = 20,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a Python script located within the approved workspace.
        Captures stdout, stderr, and verifies the outcome.
        """
        try:
            safe_path = self.policy.sanitize_workspace_path(filename)
            if not safe_path.exists():
                return {
                    "success": False,
                    "verified": False,
                    "error": f"File does not exist: {safe_path}"
                }

            # Use the active python executable
            python_bin = sys.executable
            start_time = time.time()

            result = subprocess.run(
                [python_bin, str(safe_path)],
                cwd=str(self.workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                env=os.environ.copy()
            )

            duration = round(time.time() - start_time, 3)
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            is_success = (result.returncode == 0)

            # Verification check
            verified = is_success
            if expected_output:
                verified = is_success and (expected_output in stdout)

            return {
                "success": is_success,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": duration,
                "verified": verified,
                "expected_matched": expected_output in stdout if expected_output else True,
                "file_executed": str(safe_path)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "verified": False,
                "error": f"Execution timed out after {timeout_seconds} seconds."
            }
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "error": f"Execution failed: {str(e)}"
            }
