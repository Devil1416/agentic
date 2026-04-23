#!/usr/bin/env python3
"""
start.py — Launcher for the niggativity multi-interface system.

Usage:
    python start.py          # Starts backend and opens UI in browser
    python start.py --api    # Starts backend API only
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))

def start_backend():
    print("[*] Starting backend server...")
    server_path = os.path.join(ROOT, "backend", "server.py")
    return subprocess.Popen([sys.executable, server_path])

def main():
    if "--api" in sys.argv:
        backend_process = start_backend()
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n[*] Shutting down backend...")
            backend_process.terminate()
        return

    # Start backend
    backend_process = start_backend()
    
    # Wait a moment for server to bind
    time.sleep(2)
    
    # Open UI
    ui_url = "http://localhost:8000/ui"
    print(f"[*] Opening UI in browser: {ui_url}")
    webbrowser.open(ui_url)
    
    print("\n[*] System is running. Press Ctrl+C to exit.\n")
    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        backend_process.terminate()

if __name__ == "__main__":
    main()
