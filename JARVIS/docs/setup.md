# JARVIS AI — Local Development & Setup Guide

## 1. Prerequisites
Ensure the following runtimes are installed on your workstation:
- **Python**: 3.11+ (Python 3.14.2 verified)
- **Node.js**: v18+ (Node v22.14.0 verified)
- **Git**: 2.30+

---

## 2. Quickstart Installation

### Step 1: Clone and Set Up Virtual Environment
```powershell
cd c:\Users\91790\OneDrive\Desktop\JARVIS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
pip install httpx
```

### Step 3: Run Automated Test Suite
Ensure all 17 integration and unit tests pass:
```powershell
.\.venv\Scripts\pytest -v
```

---

## 3. Running JARVIS Services

### Option A: Launch Everything with One Command
Run the unified launcher:
```powershell
.\.venv\Scripts\python start_jarvis.py
```
This will:
1. Initialize the local Windows Edge Agent on `http://127.0.0.1:8765`.
2. Connect WebSocket feed on `ws://127.0.0.1:8765/ws`.
3. Automatically launch your default browser to the **JARVIS HUD Command Center** (`http://127.0.0.1:8765/`).

### Option B: Run Cloud API (Optional for Cross-Device Testing)
In a separate terminal window:
```powershell
.\.venv\Scripts\python run_cloud_api.py
```
Runs the cloud orchestration backend on `http://127.0.0.1:8000`.

---

## 4. Running Native Frontends

### Running Desktop App (Electron)
```powershell
cd apps/desktop
npm install
npm start
```
*Note: Press `Ctrl+Alt+J` anywhere on your computer to summon or hide the JARVIS window.*

### Running Mobile App (Expo / React Native)
```powershell
cd apps/mobile
npm install
npm start
```
Scan the QR code with the Expo Go app on Android or iOS.
