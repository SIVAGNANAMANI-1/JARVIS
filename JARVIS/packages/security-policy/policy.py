"""
JARVIS AI - Security & Permission Policy Engine
Enforces risk classification, workspace boundary sandboxing, and approval requirements.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
from packages.shared_types.models import RiskLevel, TaskStep


class SecurityPolicyEngine:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # High risk action identifiers
        self.high_risk_actions = {
            "delete_file",
            "send_email",
            "send_message",
            "execute_raw_shell",
            "modify_system_settings",
            "access_credentials",
        }

        # Moderate risk action identifiers
        self.moderate_risk_actions = {
            "create_file",
            "edit_file",
            "run_approved_program",
            "read_external_file",
        }

    def evaluate_step(self, step: TaskStep) -> Tuple[RiskLevel, bool]:
        """
        Evaluates a task step, returning (RiskLevel, requires_approval).
        """
        tool = step.tool_name
        args = step.input_args

        # 1. High risk check
        if tool in self.high_risk_actions:
            return RiskLevel.HIGH, True

        # Check for destructive keywords in generic tools
        if tool == "manage_files" and args.get("action") == "delete":
            return RiskLevel.HIGH, True

        # 2. Path sandboxing check
        if "file_path" in args or "target_path" in args:
            raw_path = args.get("file_path") or args.get("target_path")
            if raw_path:
                is_safe, msg = self.validate_path(str(raw_path))
                if not is_safe:
                    # Path is outside workspace; escalating risk
                    return RiskLevel.HIGH, True

        # 3. Moderate risk check
        if tool in self.moderate_risk_actions:
            return RiskLevel.MODERATE, False

        # 4. Default to Low risk (safe reading, launching registered apps, queries)
        return RiskLevel.LOW, False

    def validate_path(self, target_path: str) -> Tuple[bool, str]:
        """
        Verifies that target_path resolves safely within the approved workspace_root.
        Prevents directory traversal attacks.
        """
        try:
            resolved = (self.workspace_root / target_path).resolve() if not os.path.isabs(target_path) else Path(target_path).resolve()
            
            # Check if resolved path starts with workspace_root
            if self.workspace_root in resolved.parents or resolved == self.workspace_root:
                return True, "Path is within approved workspace."
            return False, f"Path traversal violation: '{resolved}' is outside approved workspace '{self.workspace_root}'."
        except Exception as e:
            return False, f"Invalid path syntax: {e}"

    def sanitize_workspace_path(self, relative_or_absolute: str) -> Path:
        """
        Returns a guaranteed safe Path within workspace_root.
        """
        cleaned = os.path.normpath(relative_or_absolute).lstrip("\\/").replace("..", "")
        safe_path = (self.workspace_root / cleaned).resolve()
        # Guarantee it remains within root
        if not (self.workspace_root in safe_path.parents or safe_path == self.workspace_root):
            raise PermissionError(f"Security restriction: Access to '{relative_or_absolute}' denied.")
        return safe_path
