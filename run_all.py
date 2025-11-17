"""
Utility script to start the token server, web UI, and Python agent with one command.

Usage:
    python run_all.py
"""

import os
import subprocess
import sys
import time
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

COMMANDS: List[Tuple[str, str, str]] = [
    ("Token server", "npm start", os.path.join(BASE_DIR, "token-server")),
    ("Web UI", "npm run dev", os.path.join(BASE_DIR, "nevira-ui")),
    ("Python agent", f'"{sys.executable}" agent.py dev', BASE_DIR),
]


def start_process(name: str, command: str, cwd: str) -> subprocess.Popen:
    print(f"[launcher] Starting {name}: {command} (cwd={cwd})")
    return subprocess.Popen(command, cwd=cwd, shell=True)


def main() -> None:
    processes: List[Tuple[str, subprocess.Popen]] = []
    try:
        for name, command, cwd in COMMANDS:
            proc = start_process(name, command, cwd)
            processes.append((name, proc))

        print("[launcher] All services started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            for name, proc in processes:
                if proc.poll() is not None:
                    raise RuntimeError(f"{name} exited with code {proc.returncode}")
    except KeyboardInterrupt:
        print("\n[launcher] Ctrl+C received, shutting down...")
    except Exception as exc:
        print(f"[launcher] Error: {exc}")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                print(f"[launcher] Stopping {name}...")
                proc.terminate()
        for name, proc in processes:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"[launcher] Force killing {name}...")
                proc.kill()
        print("[launcher] All services stopped.")


if __name__ == "__main__":
    main()

