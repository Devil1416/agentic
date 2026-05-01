# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
config/settings.py — Reflexion system settings.
Mirrors the free-claude-code Settings pattern but routes everything locally.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReflexionSettings:
    """Central settings for the Reflexion system."""

    # ── Ollama connection ────────────────────────────────────
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # ── API server ───────────────────────────────────────────
    api_host: str = field(default_factory=lambda: os.getenv("REFLEXION_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: int(os.getenv("REFLEXION_PORT", "8000")))
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("REFLEXION_API_KEY", "sk-reflexion-local")
    )
    require_auth: bool = field(
        default_factory=lambda: os.getenv("REFLEXION_REQUIRE_AUTH", "false").lower() == "true"
    )

    # ── Build pipeline ───────────────────────────────────────
    max_iterations: int = field(
        default_factory=lambda: int(os.getenv("REFLEXION_MAX_ITERATIONS", "5"))
    )
    workspace_base: str = field(
        default_factory=lambda: os.getenv(
            "REFLEXION_WORKSPACE",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace"),
        )
    )
    auto_execute: bool = field(
        default_factory=lambda: os.getenv("REFLEXION_AUTO_EXECUTE", "false").lower() == "true"
    )
    parallel_agents: bool = field(
        default_factory=lambda: os.getenv("REFLEXION_PARALLEL_AGENTS", "true").lower() == "true"
    )

    # ── Logging ──────────────────────────────────────────────
    log_level: str = field(default_factory=lambda: os.getenv("REFLEXION_LOG_LEVEL", "INFO"))
    log_raw_events: bool = field(
        default_factory=lambda: os.getenv("REFLEXION_LOG_RAW", "false").lower() == "true"
    )

    # ── Model tiers ──────────────────────────────────────────
    provider_type: str = "ollama"
    model: str = field(
        default_factory=lambda: os.getenv("REFLEXION_MODEL", "auto")
    )

    @property
    def ui_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}/ui"

    @property
    def api_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def v1_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}/v1"


# Module-level singleton
_settings: Optional[ReflexionSettings] = None


def get_settings() -> ReflexionSettings:
    global _settings
    if _settings is None:
        _settings = ReflexionSettings()
    return _settings
