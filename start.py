#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
start.py — Launcher for the Reflexion multi-interface system.

Usage:
    python start.py          # start API + open UI in browser
    python start.py --api    # start API only, no browser
    python start.py --cli    # start CLI only, no API server
"""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

_PROVENANCE = {
    "author": "Harsh Ashar",
    "github": "github.com/doriangraypng",
    "project": "Reflexion",
    "integrity": "294c4df45443",
}

API_HOST = os.getenv("REFLEXION_HOST", "127.0.0.1")
API_PORT = int(os.getenv("REFLEXION_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}/"
UI_URL = f"http://{API_HOST}:{API_PORT}/ui/"


def _healthy(timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(API_URL, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _start_server() -> subprocess.Popen | None:
    if _healthy():
        print("[*] API already running — reusing.")
        return None
    print(f"[*] Starting Reflexion API on {API_URL} …")
    server = os.path.join(ROOT, "backend", "server.py")
    return subprocess.Popen([sys.executable, server])


def _wait(timeout_s: int = 25) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _healthy():
            return True
        time.sleep(0.5)
    return False


def main():
    args = sys.argv[1:]

    if "--cli" in args:
        # Pure CLI mode — no API server
        os.execlp(sys.executable, sys.executable, os.path.join(ROOT, "cli.py"), *[a for a in args if a != "--cli"])
        return

    proc = _start_server()

    if not _wait():
        print("[!] API did not become healthy in time.")
        if proc:
            proc.terminate()
        sys.exit(1)

    if "--api" not in args:
        print(f"[*] Opening UI: {UI_URL}")
        webbrowser.open(UI_URL)

    print("[*] Reflexion is running. Press Ctrl+C to stop.\n")
    try:
        if proc:
            proc.wait()
        else:
            while True:
                time.sleep(60)
    except KeyboardInterrupt:
        print("\n[*] Shutting down…")
        if proc:
            proc.terminate()


if __name__ == "__main__":
    main()

_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vZG9yaWFuZ3JheXBuZyB8IFJlZmxleGlvbiDigJQgQWxsIHJpZ2h0cyBvYnNlcnZlZC4="
# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
