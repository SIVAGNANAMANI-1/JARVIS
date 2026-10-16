# JARVIS AI — Security, Sandboxing & Permission Architecture

## 1. Principles of Least Privilege & Human-in-the-Loop
JARVIS AI adheres strictly to deterministic security guarantees:
1. **Never perform destructive actions silently**: Operations with high blast radius (file deletion, external communications, arbitrary shell outside workspace) are blocked unless explicitly confirmed by the user.
2. **Approved Workspace Boundary Sandboxing**: Script creation, file modification, and process execution are restricted by default to `workspaces/`. Path traversal (`../`) is blocked cryptographically.
3. **Verified Authentication & Multi-Tenant Isolation**: Every API endpoint is guarded by signed JWT tokens. Database queries are isolated by user partition key.
4. **No Plaintext Secret Commits**: Sensitive credentials (AWS access keys, JWT signing keys) are never hardcoded and are loaded via environment variables or secure credential stores.

---

## 2. Risk Classification Matrix

| Risk Level | Trigger Criteria | Automated Policy | Action Examples |
| :--- | :--- | :--- | :--- |
| **`LOW`** | Read-only operations, status checks, safe app launches | Auto-approved & executed immediately | Open Spotify, search YouTube, read attendance sheet, check ping, list memories |
| **`MODERATE`** | Modifying workspace files, code generation & execution in sandbox | Logged and auto-approved inside bounded workspace | Write `assignment.py`, execute Python script with stdout capture, save user preferences |
| **`HIGH`** | Deleting files, modifying files outside workspace, external emails/messages, arbitrary raw shell | **Requires Explicit Human Approval** | Deleting folders, modifying system files, raw bash/cmd commands outside sandbox |

---

## 3. Path Sandboxing Implementation
The `SecurityPolicyEngine` (`packages/security_policy/policy.py`) verifies all file paths using real path resolution:

```python
resolved = Path(path).resolve()
# Ensure resolved path is strictly a descendant of workspace_root
if not str(resolved).startswith(str(self.workspace_root)):
    raise PermissionError(f"Access denied: {resolved} is outside approved workspace {self.workspace_root}")
```

Attempts to pass paths such as `../../Windows/System32` or `../secret.txt` raise immediate `PermissionError` and abort task planning.

---

## 4. Emergency Stop
The local agent and web dashboard provide a dedicated **Emergency Stop** trigger (`POST /tasks/{task_id}/cancel` or pressing `Esc` in the HUD). This immediately terminates subprocesses and updates task state to `CANCELLED`.
