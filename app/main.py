"""
app/main.py — Niggativity Desktop Application.

Uses PyQt6 and QtWebEngine to embed the local web UI in a native window.
Automatically starts and manages the backend FastAPI server.
"""

import sys
import os
import subprocess
import time
import atexit
import threading
import urllib.request
import urllib.error

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from PyQt6.QtCore import QUrl, QTimer, Qt
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print("Error: PyQt6 and PyQt6-WebEngine are required.")
    print("Please install them with: pip install PyQt6 PyQt6-WebEngine")
    sys.exit(1)

# Global reference to backend process
backend_process = None

def start_backend():
    """Start the FastAPI backend in a subprocess."""
    global backend_process
    server_script = os.path.join(ROOT, "backend", "server.py")
    
    # Run server without showing console window (on Windows)
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    print("[Desktop] Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, server_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

def stop_backend():
    """Stop the backend subprocess."""
    global backend_process
    if backend_process:
        print("[Desktop] Stopping backend server...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        backend_process = None

# Ensure backend stops when app exits
atexit.register(stop_backend)

class LoadingScreen(QWidget):
    """Simple loading screen while backend starts."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel("Starting Niggativity...")
        self.label.setStyleSheet("color: white; font-size: 24px; font-family: Inter, sans-serif;")
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1a1c23;")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("niggativity")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # Start loading screen
        self.loading = LoadingScreen()
        self.setCentralWidget(self.loading)
        
        # Web view (created but not shown yet)
        self.web_view = QWebEngineView()
        
        # Start checking if backend is up
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_backend)
        self.check_timer.start(500)  # Check every 500ms
        self.attempts = 0

    def check_backend(self):
        """Poll the backend until it's ready, then load the UI."""
        self.attempts += 1
        try:
            req = urllib.request.Request("http://localhost:8000/")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    self.check_timer.stop()
                    self.load_ui()
                    return
        except (urllib.error.URLError, ConnectionError):
            pass
            
        if self.attempts > 30:  # 15 seconds max wait
            self.check_timer.stop()
            self.loading.label.setText("Error: Backend failed to start.\nPlease check logs.")
            self.loading.label.setStyleSheet("color: #ef4444; font-size: 20px;")

    def load_ui(self):
        """Switch from loading screen to web view."""
        self.web_view.setUrl(QUrl("http://localhost:8000/ui"))
        self.setCentralWidget(self.web_view)

def main():
    # Start backend in a separate thread so it doesn't block UI init
    threading.Thread(target=start_backend, daemon=True).start()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
