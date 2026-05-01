#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
backend/server.py — Reflexion FastAPI server entry point.

Delegates to api/app.py for the full route set.
Supports uvicorn hot-reload for development.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if __name__ == "__main__":
    import uvicorn
    from config.settings import get_settings

    s = get_settings()
    print(f"""
************************************************
*  Reflexion API v2.0                          *
*  Local-first autonomous coding agent         *
*  Provider: Ollama  |  {s.api_host}:{s.api_port:<5}          *
************************************************
    """)
    uvicorn.run(
        "api.app:create_app",
        host=s.api_host,
        port=s.api_port,
        factory=True,
        log_level=s.log_level.lower(),
        reload=os.getenv("REFLEXION_RELOAD", "false").lower() == "true",
    )
