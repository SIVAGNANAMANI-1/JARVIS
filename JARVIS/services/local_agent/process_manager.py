"""
JARVIS AI - Windows Process & Application Manager
Discovers, launches, and verifies local operating system applications.
"""

import os
import shutil
import subprocess
import time
from typing import Dict, Any, List, Optional
import psutil


class ProcessManager:
    def __init__(self):
        # Known common application executables and aliases on Windows
        self.app_registry = {
            "vscode": ["code.cmd", "code.exe", "Code"],
            "spotify": ["Spotify.exe", "spotify"],
            "chrome": ["chrome.exe", "Google Chrome"],
            "edge": ["msedge.exe", "Microsoft Edge"],
            "notepad": ["notepad.exe"],
            "calc": ["calc.exe", "CalculatorApp.exe"],
            "explorer": ["explorer.exe"],
            "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
        }

    def find_executable(self, app_name: str) -> Optional[str]:
        """
        Locates executable path using PATH and standard Windows install locations.
        """
        app_key = app_name.lower().strip()
        candidates = self.app_registry.get(app_key, [app_name])

        for candidate in candidates:
            # Check standard PATH
            path = shutil.which(candidate)
            if path:
                return path

            # Check LocalAppData & ProgramFiles
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("ProgramFiles", "")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "")

            common_paths = [
                os.path.join(local_appdata, "Programs", "Microsoft VS Code", "Code.exe"),
                os.path.join(local_appdata, "Microsoft", "WindowsApps", candidate),
                os.path.join(local_appdata, "Spotify", "Spotify.exe"),
                os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
                os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "notepad.exe"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "explorer.exe"),
            ]

            for p in common_paths:
                if os.path.exists(p) and (candidate.lower() in p.lower() or app_key in p.lower()):
                    return p

        return None

    def launch_application(self, app_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Launches an application and verifies using psutil that the process is alive.
        """
        args = args or []
        app_key = app_name.lower().strip()

        # Handle URI protocols (e.g. spotify:, https://)
        if app_key == "spotify" and not self.find_executable("spotify"):
            # Launch via Windows protocol handler
            uri = "spotify:" if not args else args[0]
            try:
                os.startfile(uri)
                time.sleep(1.0)
                is_running = self.is_application_running("spotify")
                return {
                    "success": True,
                    "method": "protocol_handler",
                    "uri": uri,
                    "verified": is_running,
                    "message": "Spotify protocol invoked." if is_running else "Spotify protocol invoked (process startup pending)."
                }
            except Exception as e:
                return {
                    "success": False,
                    "verified": False,
                    "error": f"Failed to invoke protocol handler: {str(e)}"
                }

        exe_path = self.find_executable(app_name)
        if not exe_path:
            # Fallback to direct Windows start command
            try:
                cmd = f"start {app_name}"
                subprocess.Popen(cmd, shell=True)
                time.sleep(1.0)
                verified = self.is_application_running(app_name)
                return {
                    "success": True,
                    "method": "shell_start",
                    "command": cmd,
                    "verified": verified,
                    "message": f"Application '{app_name}' launched via shell start."
                }
            except Exception as e:
                return {
                    "success": False,
                    "verified": False,
                    "error": f"Executable not found for '{app_name}': {str(e)}"
                }

        try:
            full_cmd = [exe_path] + args
            proc = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0,
                close_fds=True
            )
            time.sleep(0.8)

            # Verification: Check if process or matching child process is running
            verified = proc.poll() is None or self.is_application_running(app_name)
            return {
                "success": True,
                "pid": proc.pid,
                "executable": exe_path,
                "verified": verified,
                "message": f"Successfully launched '{app_name}' (PID: {proc.pid})."
            }
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "error": f"Failed to execute '{exe_path}': {str(e)}"
            }

    def is_application_running(self, app_name: str) -> bool:
        """
        Uses psutil to inspect real running OS processes.
        """
        app_str = app_name.lower().replace(".exe", "")
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                if app_str in pname:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def list_running_applications(self) -> List[Dict[str, Any]]:
        """
        Returns active applications running on the user's system.
        """
        active = []
        seen = set()
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                name = proc.info['name']
                if name.lower() not in seen and not name.lower().startswith(('svchost', 'system', 'registry')):
                    seen.add(name.lower())
                    active.append({
                        "pid": proc.info['pid'],
                        "name": name,
                        "memory_percent": round(proc.info.get('memory_percent') or 0, 2)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(active, key=lambda x: x["memory_percent"], reverse=True)[:30]
