"""
JARVIS AI — Local Edge Agent & Dashboard Launcher
Starts the FastAPI local automation server and opens the interactive HUD command center.
"""

import sys
import os
import webbrowser
import time
from pathlib import Path
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    print("=" * 60)
    print("           JARVIS AI — Personal Digital Operator")
    print("=" * 60)
    print("Starting Local Windows Edge Agent on http://127.0.0.1:8765 ...")
    print("Interactive Web HUD Dashboard: http://127.0.0.1:8765/")
    print("WebSocket Realtime Feed:       ws://127.0.0.1:8765/ws")
    print("Approved Workspace Sandbox:    " + str(PROJECT_ROOT / "workspaces"))
    print("-" * 60)

    # Launch browser after a short pause
    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8765/")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI server via uvicorn
    uvicorn.run(
        "services.local_agent.api:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
