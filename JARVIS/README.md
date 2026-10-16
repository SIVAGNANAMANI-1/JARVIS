# JARVIS AI — Autonomous, Voice-Enabled, Cross-Platform Personal AI Assistant

[![Tests](https://img.shields.io/badge/tests-18%20passed-00ff88.svg?style=flat-square)](docs/supported-capabilities.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Web%20%7C%20Mobile-00f0ff.svg?style=flat-square)](docs/architecture.md)
[![Architecture](https://img.shields.io/badge/architecture-Hybrid%20Cloud%20%2B%20Edge-9d4edd.svg?style=flat-square)](docs/architecture.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)

JARVIS AI is an intelligent personal digital operator that understands natural language and voice commands, decomposes complex multi-step instructions, executes verified automations on Windows hardware, learns user-approved preferences, and synchronizes work across mobile phones, laptops, and web browsers.

---

## ⚡ Key Highlights

- **Dual-Brain Hybrid Architecture**: Amazon Bedrock (Claude 3 Sonnet) for high-order reasoning + Windows Local Edge Agent for OS execution, process control, and verified sandboxing.
- **Zero-Cost Local Development Mode**: Automatically runs out-of-the-box without requiring AWS cloud resources or charges by emulating cloud state with SQLite.
- **Deterministic Verification Engine**: Rejects simulated success. Every action confirms physical OS indicators (return code = 0, process verified, stdout match, files checked).
- **Security & Risk Sandboxing**: Actions are classified into `LOW`, `MODERATE`, and `HIGH` risk tiers. Traversal outside approved workspaces is cryptographically blocked; destructive actions require explicit user approval.
- **Cross-Platform Mesh**:
  - **Web Command Center** (`apps/web`): Futuristic glassmorphic HUD dashboard with real-time WebSockets, Web Speech API voice control, and audio frequency visualizers.
  - **Desktop Host** (`apps/desktop`): Electron wrapper with global shortcut summon (`Ctrl+Alt+J`) and tray integration.
  - **Mobile Dispatcher** (`apps/mobile`): React Native / Expo client to pair devices and dispatch tasks from an Android/iOS device to your Windows laptop.
- **Universal Tool Adapters**:
  - 💻 **VS Code & Python**: Generate script files in sandbox, execute with timeout, assert stdout output.
  - 🎵 **Spotify**: Control music playback and open study playlists via Spotify URI protocol.
  - 📺 **Browser & YouTube**: Launch search queries and stream tutorial videos.
  - 📊 **Office & Data Analytics**: Calculate attendance statistics from CSVs and generate Markdown reports.
  - 🔍 **File Operations**: Scan workspace folders for SHA-256 duplicate files and compute reclaimable storage.
  - 🧠 **Memory Vault**: Persistent user preferences and fact storage.

---

## 🚀 Quick Start

### 1. Launch JARVIS Local Agent & Web Dashboard
```powershell
# Set up virtual environment
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install httpx

# Start JARVIS (launches agent & opens browser automatically)
.\.venv\Scripts\python start_jarvis.py
```
Open **`http://127.0.0.1:8765/`** in your browser to interact with the HUD.

### 2. Run All Automated Tests
```powershell
.\.venv\Scripts\pytest -v
```

### 3. Launch Cloud Coordination Server (Optional for Cross-Device)
```powershell
.\.venv\Scripts\python run_cloud_api.py
```

---

## 📂 Repository Structure

```
JARVIS/
├── apps/
│   ├── web/               # Responsive HTML5/CSS3 glassmorphic HUD dashboard
│   ├── desktop/           # Electron native host with global summon (Ctrl+Alt+J)
│   └── mobile/            # React Native / Expo cross-device dispatcher
├── data/                  # Local SQLite databases for zero-cost offline emulation
├── docs/                  # Engineering specifications & guides
│   ├── architecture.md    # System design, data flow, hybrid cloud-edge
│   ├── setup.md           # Local setup and running instructions
│   ├── aws-deployment.md  # AWS SAM CloudFormation deployment guide
│   ├── security.md        # Risk classification, sandboxing, approval gates
│   ├── cost-estimation.md # Honest AWS pricing and cost control analysis
│   └── supported-capabilities.md # Working, partial, and planned capabilities
├── infrastructure/
│   └── aws-sam/           # AWS SAM template (Cognito, DynamoDB, S3, API Gateway, Lambda)
├── integrations/          # Hardware & application adapters
│   ├── browser/           # Web search and YouTube query adapter
│   ├── office/            # Attendance analysis & Markdown report generator
│   ├── spotify/           # Spotify desktop client & URI protocol adapter
│   └── vscode/            # VS Code script generation, execution & verification
├── packages/
│   ├── security_policy/   # Sandboxing, canonical path validation, risk engine
│   └── shared_types/      # Core Pydantic contracts across local, cloud & clients
├── services/
│   ├── agent_core/        # Bedrock Claude 3 client + local semantic fallback planner
│   ├── cloud_api/         # Central FastAPI service, Cognito JWT auth, task routing
│   └── local_agent/       # Windows Edge FastAPI & WebSocket service (Port 8765)
├── tests/                 # Automated unit and integration test suite
├── workspaces/            # Sandboxed directory for generated scripts and reports
├── start_jarvis.py        # One-click launcher for local agent and web dashboard
└── run_cloud_api.py       # One-click launcher for cloud coordination API
```

---

## 📖 Documentation
- 📐 [Architecture Deep Dive](docs/architecture.md)
- 🛠️ [Setup & Installation](docs/setup.md)
- ☁️ [AWS Cloud Deployment](docs/aws-deployment.md)
- 🛡️ [Security, Sandboxing & Approvals](docs/security.md)
- 💰 [Cost Breakdown & Estimations](docs/cost-estimation.md)
- 📋 [Supported Capabilities Audit](docs/supported-capabilities.md)
