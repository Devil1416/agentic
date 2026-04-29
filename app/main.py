# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
app/main.py - Niggativity desktop application.

Embeds the local web UI in a native PyQt6 window and either reuses an existing
backend or launches a managed one with logs written to disk.
"""

import atexit
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "4f1f81bd53e5",
}
# ─── /fingerprint ───────────────────────────────────────────


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from PyQt6.QtCore import QTimer, Qt, QUrl
    from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print("Error: PyQt6 and PyQt6-WebEngine are required.")
    print("Please install them with: pip install PyQt6 PyQt6-WebEngine")
    sys.exit(1)

BACKEND_URL = "http://127.0.0.1:8000/"
UI_URL = "http://127.0.0.1:8000/ui"
backend_process = None
started_backend_here = False
backend_log_path = os.path.join(ROOT, "app_log.txt")


def backend_is_healthy(timeout: float = 1.0) -> bool:
    """Return True when the backend health endpoint responds."""


    try:
        request = urllib.request.Request(BACKEND_URL)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, ConnectionError):
        return False


def start_backend():
    """Start the FastAPI backend unless one is already healthy."""
    global backend_process, started_backend_here

    if backend_is_healthy():
        print("[Desktop] Reusing existing backend on port 8000.")
        started_backend_here = False
        return

    server_script = os.path.join(ROOT, "backend", "server.py")
    os.makedirs(os.path.dirname(backend_log_path) or ROOT, exist_ok=True)
    log_handle = open(backend_log_path, "a", encoding="utf-8")

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

    print("[Desktop] Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, server_script],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    started_backend_here = True


def stop_backend():
    """Stop the managed backend subprocess."""
    global backend_process
    if backend_process and started_backend_here:
        print("[Desktop] Stopping backend server...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    backend_process = None


atexit.register(stop_backend)


class LoadingScreen(QWidget):
    """Simple loading screen while backend starts."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Starting Niggativity...")
        self.label.setStyleSheet("color: white; font-size: 24px; font-family: Segoe UI, sans-serif;")
        layout.addWidget(self.label)

        self.detail = QLabel("Preparing backend and warming local services.")
        self.detail.setStyleSheet("color: #c9d1d9; font-size: 13px; font-family: Segoe UI, sans-serif;")
        layout.addWidget(self.detail)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #11161d;")

    def set_status(self, title: str, detail: str):
        self.label.setText(title)
        self.detail.setText(detail)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("niggativity")
        self.resize(1280, 860)
        self.setMinimumSize(960, 640)

        self.loading = LoadingScreen()
        self.setCentralWidget(self.loading)
        self.web_view = QWebEngineView()

        self.attempts = 0
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_backend)
        self.check_timer.start(400)

    def check_backend(self):
        """Poll the backend until it's ready, then load the UI."""
        self.attempts += 1
        self.loading.set_status(
            "Starting Niggativity...",
            "Waiting for backend health check." if self.attempts < 6 else "Still warming local services.",
        )

        if backend_is_healthy():
            self.check_timer.stop()
            self.load_ui()
            return

        if backend_process and backend_process.poll() is not None and started_backend_here:
            self.check_timer.stop()
            self.loading.set_status(
                "Backend failed to start.",
                f"See log: {backend_log_path}",
            )
            self.loading.label.setStyleSheet("color: #ef4444; font-size: 22px; font-family: Segoe UI, sans-serif;")
            return

        if self.attempts > 45:
            self.check_timer.stop()
            self.loading.set_status(
                "Backend is taking longer than expected.",
                f"Check {backend_log_path} or run backend/server.py manually.",
            )
            self.loading.label.setStyleSheet("color: #f59e0b; font-size: 20px; font-family: Segoe UI, sans-serif;")

    def load_ui(self):
        """Switch from loading screen to the embedded web UI."""
        self.web_view.setUrl(QUrl(UI_URL))
        self.setCentralWidget(self.web_view)


def main():
    start_backend()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
