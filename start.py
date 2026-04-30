#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                            ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
start.py - Launcher for the reflexion multi-interface system.

Usage:
    python start.py          # Starts backend if needed and opens UI in browser
    python start.py --api    # Starts backend API only
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Reflexion",
"integrity": "294c4df45443",
}
# ─── /fingerprint ───────────────────────────────────────────


ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_URL = "http://127.0.0.1:8000/"
UI_URL = "http://127.0.0.1:8000/ui"


def backend_is_healthy(timeout: float = 1.0) -> bool:


    try:
        req = urllib.request.Request(BACKEND_URL)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, ConnectionError):
        return False


def start_backend():
    if backend_is_healthy():
        print("[*] Reusing backend already running on port 8000.")
        return None

    print("[*] Starting backend server...")
    server_path = os.path.join(ROOT, "backend", "server.py")
    return subprocess.Popen([sys.executable, server_path])


def wait_for_backend(timeout_s: int = 20) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if backend_is_healthy():
            return True
        time.sleep(0.5)
    return False


def main():
    backend_process = start_backend()

    if "--api" in sys.argv:
        if not wait_for_backend():
            print("[!] Backend did not become healthy in time.")
            if backend_process:
                backend_process.terminate()
            sys.exit(1)
        try:
            if backend_process:
                backend_process.wait()
            else:
                while True:
                    time.sleep(60)
        except KeyboardInterrupt:
            print("\n[*] Shutting down backend...")
            if backend_process:
                backend_process.terminate()
        return

    if not wait_for_backend():
        print("[!] Backend did not become healthy in time.")
        if backend_process:
            backend_process.terminate()
        sys.exit(1)

    print(f"[*] Opening UI in browser: {UI_URL}")
    webbrowser.open(UI_URL)

    print("\n[*] System is running. Press Ctrl+C to exit.\n")
    try:
        if backend_process:
            backend_process.wait()
        else:
            while True:
                time.sleep(60)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        if backend_process:
            backend_process.terminate()


if __name__ == "__main__":
    main()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Reflexion. Tampering with attribution is detectable.
