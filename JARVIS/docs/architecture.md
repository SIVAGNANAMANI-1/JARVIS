# JARVIS AI — System Architecture Specification

## 1. Architectural Philosophy
JARVIS AI is built on a **hybrid cloud-and-edge model** that combines the infinite scale and cognitive capabilities of the cloud with the direct execution authority and low latency of local hardware.

```
                      +---------------------------------------+
                      |       Clients & Interfaces           |
                      |  - Web Command Center (HTML5/CSS3)    |
                      |  - Desktop Native Host (Electron)     |
                      |  - Mobile Client (React Native/Expo)  |
                      +-------------------+-------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
         Direct Local Control (Localhost)     Cloud Synchronization (HTTPS/WSS)
                        |                                   |
                        v                                   v
         +------------------------------+    +------------------------------+
         |   Local Windows Edge Agent   |    |    AWS Cloud Infrastructure  |
         |   (Port 8765 - FastAPI)      |    |    (Serverless & Bedrock)    |
         +------------------------------+    +------------------------------+
         | • Process Manager (Windows)  |    | • Amazon Cognito (JWT Auth)  |
         | • Workspace Sandbox Runner   |    | • API Gateway (HTTP API v2)  |
         | • File Operations Engine     |    | • AWS Lambda (Orchestrator)  |
         | • Tool Adapters:             |    | • Amazon Bedrock (Claude 3)  |
         |   - VS Code automation       |    | • DynamoDB (State & Tasks)   |
         |   - Spotify deep-links       |    | • Amazon S3 (Artifacts)      |
         |   - Browser / YouTube nav    |    | • Dual Mode: Local SQLite    |
         |   - Office doc generators    |    |   zero-cost emulation        |
         | • Risk & Security Policy     |    +------------------------------+
         | • Verification Observer      |                   ^
         | • Local SQLite Memory        |                   |
         +--------------+---------------+                   |
                        |                                   |
                        +----------- Verified Progress -----+
                                     Synchronization
```

---

## 2. Component Breakdown

### A. Local Edge Agent (`services/local_agent`)
- **FastAPI Core**: Runs on `127.0.0.1:8765`, serving both REST endpoints (`/tasks/execute`, `/health`, `/device/info`, `/memory`) and a real-time WebSocket connection (`/ws`) for instantaneous telemetry and event broadcast.
- **Process Manager (`process_manager.py`)**: Launches installed executables (VS Code, Spotify, browsers, Office, Windows terminal), monitors processes via `psutil`, and captures process exit codes.
- **Workspace Runner (`workspace_runner.py`)**: Sandboxes Python code generation and execution strictly inside `workspaces/`. Executes scripts with timeouts, captures `stdout` / `stderr`, and verifies output against cryptographic assertions.
- **Security Policy Engine (`packages/security_policy/policy.py`)**: Classifies all requested actions into `LOW`, `MODERATE`, and `HIGH` risk tiers. Traversal outside approved paths triggers an automatic security block or approval gate.

### B. Agent Core & Cognitive Layer (`services/agent_core`)
- **Bedrock Model Provider (`bedrock_client.py`)**: Interfaces with Amazon Bedrock foundation models (Claude 3 Sonnet / Titan) via `boto3`.
- **Intelligent Local Fallback**: When AWS credentials are not configured or network connectivity is unavailable, seamlessly switches to a rule-based semantic planning engine, guaranteeing full offline functionality.
- **Verification Engine**: Prohibits synthetic success claims. Every action is verified against physical OS indicators (file existence, exit code = 0, stdout match).

### C. Cloud Orchestration API (`services/cloud_api`)
- **Authentication & Multi-Tenant Isolation (`auth.py`)**: Generates and verifies HMAC-SHA256 signed JWT tokens, mapping users strictly to their owned devices and tasks. Cross-user data leakage is prevented by strict database partition filtering.
- **Device Registry & Task Dispatch (`storage.py`)**: Manages device heartbeat records, queued remote tasks, and bidirectional progress synchronization between phone, web, and desktop.
- **Dual-Mode Persistence**: Automatically detects live DynamoDB and S3 connectivity. If absent, transparently falls back to local SQLite databases (`data/cloud_emulation.db`), enabling full cloud-style integration testing with zero AWS expenditure.

### D. Universal Integrations (`integrations/`)
- `vscode`: Automates workspace script creation and execution verification.
- `spotify`: Interacts with Spotify desktop application and Spotify URI search schemas.
- `browser`: Launches Google search and YouTube video tutorials via system default browsers.
- `office`: Generates attendance spreadsheets, summaries, and Markdown audit reports.
