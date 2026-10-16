"""
JARVIS AI — Cloud API & Cross-Device Coordination Service Launcher
Starts the cloud backend on http://127.0.0.1:8000 for cross-device synchronization and remote task dispatching.
"""

import sys
from pathlib import Path
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    print("=" * 60)
    print("       JARVIS AI — Cloud Orchestration & Auth Service")
    print("=" * 60)
    print("Starting Cloud API Server on http://127.0.0.1:8000 ...")
    print("API Documentation (Swagger):  http://127.0.0.1:8000/docs")
    print("Health Check Endpoint:        http://127.0.0.1:8000/health")
    print("-" * 60)

    uvicorn.run(
        "services.cloud_api.api:cloud_app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
