"""
JARVIS AI - Local Safe File Operations
Provides duplicate file scanning, attendance sheet analysis, and document searching.
"""

import os
import hashlib
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from packages.security_policy.policy import SecurityPolicyEngine


class FileOperations:
    def __init__(self, workspace_root: Optional[str] = None):
        if not workspace_root:
            workspace_root = str(Path(__file__).resolve().parent.parent.parent / "workspaces")
        self.workspace_root = Path(workspace_root).resolve()
        self.policy = SecurityPolicyEngine(str(self.workspace_root))

    def hash_file(self, file_path: Path, block_size: int = 65536) -> str:
        """Computes SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                hasher.update(block)
        return hasher.hexdigest()

    def find_duplicate_files(self, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans a directory (workspace or specified folder) and groups duplicate files by hash.
        """
        search_path = Path(target_dir).resolve() if target_dir else self.workspace_root
        if not search_path.exists():
            return {"success": False, "error": f"Directory does not exist: {search_path}"}

        hashes: Dict[str, List[Dict[str, Any]]] = {}
        total_scanned = 0

        for root, _, files in os.walk(search_path):
            for filename in files:
                filepath = Path(root) / filename
                try:
                    if filepath.is_file() and filepath.stat().st_size > 0:
                        total_scanned += 1
                        file_hash = self.hash_file(filepath)
                        file_info = {
                            "name": filename,
                            "path": str(filepath),
                            "size_bytes": filepath.stat().st_size
                        }
                        hashes.setdefault(file_hash, []).append(file_info)
                except Exception:
                    continue

        duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
        reclaimable_bytes = sum(
            sum(f["size_bytes"] for f in files[1:])
            for files in duplicates.values()
        )

        return {
            "success": True,
            "directory_scanned": str(search_path),
            "total_files_scanned": total_scanned,
            "duplicate_groups_count": len(duplicates),
            "reclaimable_bytes": reclaimable_bytes,
            "duplicates": duplicates
        }

    def analyze_attendance_sheet(self, file_path: str) -> Dict[str, Any]:
        """
        Parses an attendance CSV/spreadsheet and calculates monthly attendance statistics.
        Format expected: Name, Dates/Days (e.g. Present/Absent or P/A or 1/0).
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / file_path

        if not path.exists():
            return {"success": False, "error": f"Attendance file not found: {path}"}

        try:
            records = []
            with open(path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return {"success": False, "error": "CSV file is empty."}

                name_col_idx = 0
                for row in reader:
                    if not row or len(row) <= 1:
                        continue
                    name = row[name_col_idx].strip()
                    statuses = [val.strip().upper() for val in row[1:] if val.strip()]
                    
                    present_count = sum(1 for s in statuses if s in ["P", "PRESENT", "1", "YES", "TRUE"])
                    total_days = len(statuses)
                    percentage = round((present_count / total_days * 100), 2) if total_days > 0 else 0.0

                    records.append({
                        "name": name,
                        "total_days": total_days,
                        "present_days": present_count,
                        "absent_days": total_days - present_count,
                        "attendance_percentage": percentage
                    })

            if not records:
                return {"success": False, "error": "No student or employee records found in sheet."}

            overall_avg = round(sum(r["attendance_percentage"] for r in records) / len(records), 2)
            low_attendance = [r for r in records if r["attendance_percentage"] < 75.0]

            return {
                "success": True,
                "file_analyzed": str(path),
                "total_individuals": len(records),
                "overall_attendance_average": overall_avg,
                "below_75_percent_count": len(low_attendance),
                "below_75_percent_list": low_attendance,
                "all_records": records
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to analyze attendance sheet: {str(e)}"}
