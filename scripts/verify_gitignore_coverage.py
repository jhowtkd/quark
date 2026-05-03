#!/usr/bin/env python3
"""
Verify that .gitignore covers all sensitive directories.

Lists directories in backend/uploads/ and backend/logs/, checks if each
is covered by .gitignore via git check-ignore, and returns exit code 0
if all covered, 1 if gaps exist.
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "backend", "uploads")
LOGS_DIR = os.path.join(PROJECT_ROOT, "backend", "logs")


def git_ignores(path: str) -> bool:
    """Return True if git ignores the given path."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: git not found in PATH", file=sys.stderr)
        sys.exit(1)


def collect_directories(base_dir: str) -> list[str]:
    """Return all first-level directories under base_dir."""
    if not os.path.isdir(base_dir):
        return []
    dirs = []
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if os.path.isdir(entry_path):
            dirs.append(entry_path)
    return dirs


def main() -> int:
    gaps = []

    # Check uploads subdirectories
    for d in collect_directories(UPLOADS_DIR):
        test_file = os.path.join(d, ".gitignore_test_probe")
        if not git_ignores(test_file):
            gaps.append(f"{d} (test file not ignored)")

    # Check logs directory itself and any subdirectories
    for d in [LOGS_DIR] + collect_directories(LOGS_DIR):
        test_file = os.path.join(d, ".gitignore_test_probe")
        if not git_ignores(test_file):
            gaps.append(f"{d} (test file not ignored)")

    if gaps:
        print("GITIGNORE COVERAGE GAPS FOUND:")
        for gap in gaps:
            print(f"  - {gap}")
        return 1

    print("All sensitive directories are covered by .gitignore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
