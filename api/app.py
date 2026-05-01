# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
api/app.py — FastAPI application factory for Reflexion.

Creates and configures the app with:
- Claude-compatible /v1/messages API
- Reflexion build pipeline routes
- Web UI static serving
- Startup/shutdown lifecycle hooks
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from config.settings import get_settings
from providers.registry import get_registry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(ROOT, "ui")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Reflexion API",
        description=(
            "Local-first autonomous coding agent. "
            "Claude Code-compatible API backed entirely by Ollama."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Lifecycle ─────────────────────────────────────────────
    @app.on_event("startup")
    async def _startup():
        """Warm Ollama model cache on startup."""
        import threading

        def _warm():
            try:
                from model_router import get_installed_models
                models = get_installed_models()
                print(f"[reflexion] {len(models)} Ollama models available at startup.")
                from memory.vector_store import warm_memory_system
                warm_memory_system()
            except Exception as exc:
                print(f"[reflexion] warmup skipped: {exc}")

        threading.Thread(target=_warm, daemon=True).start()

        # Start async model discovery
        registry = get_registry(settings.ollama_base_url)
        registry.start_background_refresh()
        app.state.provider_registry = registry

    @app.on_event("shutdown")
    async def _shutdown():
        registry = getattr(app.state, "provider_registry", None)
        if registry:
            await registry.cleanup()

    # ── Routers ───────────────────────────────────────────────
    app.include_router(router)

    # ── UI serving ────────────────────────────────────────────
    @app.get("/ui")
    async def redirect_ui():
        return RedirectResponse(url="/ui/")

    @app.get("/ui/")
    async def serve_ui():
        index = os.path.join(UI_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index, media_type="text/html")
        return {"error": "UI not found"}

    if os.path.isdir(UI_DIR):
        app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui-static")

    return app
