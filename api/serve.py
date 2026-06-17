"""Entry point for `privguard serve`."""
from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

_WEB_DIR = Path(__file__).parent.parent / "web"
_API_HOST = "127.0.0.1"
_API_PORT = 8000
_NEXT_PORT = 3000


def main() -> None:
    prod = "--prod" in sys.argv

    print("Starting PrivGuard...")

    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app",
         "--host", _API_HOST, "--port", str(_API_PORT), "--reload"],
        cwd=str(Path(__file__).parent.parent),
    )

    if prod:
        time.sleep(1.5)
        url = f"http://localhost:{_API_PORT}"
        print(f"PrivGuard running at {url}")
        webbrowser.open(url)
        try:
            api_proc.wait()
        except KeyboardInterrupt:
            api_proc.terminate()
        return

    if not _WEB_DIR.exists():
        print(f"NOTE: web/ directory not found — API-only mode on port {_API_PORT}.", file=sys.stderr)
        time.sleep(1.5)
        url = f"http://localhost:{_API_PORT}/api/docs"
        webbrowser.open(url)
        try:
            api_proc.wait()
        except KeyboardInterrupt:
            api_proc.terminate()
        return

    next_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(_WEB_DIR),
        shell=sys.platform == "win32",
    )

    time.sleep(3)
    url = f"http://localhost:{_NEXT_PORT}"
    print(f"PrivGuard running at {url}")
    webbrowser.open(url)

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        api_proc.terminate()
        next_proc.terminate()
