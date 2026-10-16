# JARVIS AI — Supported Capabilities Matrix

*Last Verified: October 2026*  
*Total Automated Tests Passing: 18 / 18*

This document provides a truthful, engineering-grade audit of what JARVIS AI can genuinely execute today, what is partially supported with known constraints, what is planned, and what is explicitly unsupported.

---

## 1. Working & Fully Verified Capabilities (Tested & Functional)

| Capability / Workflow | Status | Verification Mechanism | Test / Endpoint Reference |
| :--- | :--- | :--- | :--- |
| **VS Code & Python Program Automation** | **Working** | Creates `.py` script in approved workspace, runs Python interpreter, asserts exitcode=0 and stdout matches target. | `tests/test_local_agent.py::test_workspace_code_execution_and_verification` |
| **Attendance Spreadsheet Analysis & Reporting** | **Working** | Parses CSV attendance sheets, calculates attendance percentage and absent lists, writes formatted Markdown audit report. | `tests/test_local_agent.py::test_attendance_analysis_and_report` |
| **Duplicate File Hash Scanner** | **Working** | Computes SHA-256 hashes of files in specified directory, identifies duplicate groups, computes reclaimable storage bytes. | `tests/test_local_agent.py::test_file_operations_and_duplicates` |
| **Spotify Music Integration** | **Working** | Launches Spotify desktop client and triggers playlist search URI (`spotify:search:...`). | `integrations/spotify/adapter.py` |
| **Browser & YouTube Search** | **Working** | Encodes search terms and opens matching video results in default Windows browser. | `integrations/browser/adapter.py` |
| **Security Path Sandboxing** | **Working** | Blocks path traversal attempts (`../`) outside approved `workspaces/` root via strict canonical path checking. | `tests/test_local_agent.py::test_security_policy_sandboxing` |
| **Multi-Tier Risk Classification & Approval Gates** | **Working** | Classifies actions into `LOW`, `MODERATE`, and `HIGH`. Enforces explicit human approval for destructive operations. | `tests/test_local_agent.py::test_security_risk_classification` |
| **Cognito & JWT Multi-Tenant Authentication** | **Working** | Issues signed JWT access tokens and enforces user-isolated data queries across cloud endpoints. | `tests/test_cloud_api.py::test_auth_login`, `test_cross_user_security_isolation` |
| **Cross-Device Remote Task Dispatch & Progress Sync** | **Working** | Mobile phone dispatches task targeting Windows laptop; laptop polls, executes, and synchronizes verified progress back to cloud. | `tests/test_cloud_api.py::test_cross_device_task_submission_and_sync` |
| **Persistent User Memory Vault** | **Working** | CRUD storage for user preferences and facts across sessions using SQLite and DynamoDB schemas. | `tests/test_api_endpoints.py::test_memory_crud_flow` |
| **Web HUD Command Center** | **Working** | Responsive, glassmorphic HUD dashboard with real-time WebSocket connection, audio visualizer, voice mic, and task feed. | `tests/test_api_endpoints.py::test_dashboard_serve` |
| **Dual-Mode Persistence (Zero-Cost Local Dev)** | **Working** | Automatic fallback to local SQLite for DynamoDB and S3 operations when AWS credentials are not configured. | `services/cloud_api/storage.py` |

---

## 2. Partially Supported Capabilities

| Feature | Current State | Limitations / Pending Enhancements |
| :--- | :--- | :--- |
| **Amazon Bedrock AI Reasoning** | Code implemented with Claude 3 Sonnet schema and local fallback planner. | Requires valid AWS account credentials and Bedrock model access grants in `us-east-1`. In offline mode, the system runs via the built-in deterministic semantic planner. |
| **Voice Interaction** | Working in Chrome/Edge via HTML5 Web Speech API (`webkitSpeechRecognition` & `speechSynthesis`). | Browser must have microphone permission enabled; synthesis voice quality depends on the OS speech engines installed. |
| **Office Word (.docx) Generation** | Generates Markdown formatted documents and reports. | Direct binary `.docx` output utilizes Markdown/text formats unless `python-docx` library is explicitly installed. |

---

## 3. Planned Capabilities

- [ ] **Native Windows OCR & Screen Grounding**: Integrating Windows Media OCR or Tesseract to inspect active non-scriptable legacy windows.
- [ ] **Gmail & Calendar Integration**: Google Workspace OAuth2 integration for querying unread emails and adding calendar reminders.
- [ ] **Cricket Live Score Scraper**: Sports API integration for retrieving live match scoreboards into the HUD stream.
- [ ] **Multi-Agent Swarm Handoff**: Dedicated sub-agents specializing in deep research vs code debugging vs system operations.

---

## 4. Explicitly Unsupported Capabilities

| Feature | Reason for Non-Support |
| :--- | :--- |
| **Arbitrary Unsanctioned File Deletion** | **Prohibited by design** — deleting files outside approved workspace boundaries is rejected by the Security Policy Engine. |
| **Automated Financial Transactions** | **Prohibited by design** — automatic payments, card entries, or monetary transactions are blocked for user safety. |
| **Kernel-level Driver Operations** | JARVIS operates strictly in user-space with standard OS and application privileges. |
