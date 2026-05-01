# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
providers/registry.py — Provider registry for Reflexion.

Mirrors free-claude-code ProviderRegistry but only manages Ollama.
Responsible for model discovery, caching, and provider lifecycle.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from providers.base import BaseProvider, ProviderConfig
from providers.ollama_provider import OllamaProvider


_SINGLETON: Optional["ProviderRegistry"] = None


class ProviderRegistry:
    """Cache and lifecycle manager for provider instances."""

    SUPPORTED_PROVIDERS = ("ollama",)

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url
        self._providers: dict[str, BaseProvider] = {}
        self._model_cache: dict[str, list[str]] = {}  # provider_id → model_ids
        self._refresh_task: Optional[asyncio.Task] = None

    # ── Factory ──────────────────────────────────────────────

    def _make_provider(self, provider_id: str) -> BaseProvider:
        if provider_id == "ollama":
            return OllamaProvider(ProviderConfig(base_url=self._base_url))
        raise ValueError(f"Unknown provider: {provider_id}")

    def get(self, provider_id: str = "ollama") -> BaseProvider:
        """Return a cached-or-new provider instance."""
        if provider_id not in self._providers:
            self._providers[provider_id] = self._make_provider(provider_id)
        return self._providers[provider_id]

    # ── Model discovery ──────────────────────────────────────

    async def refresh_model_cache(self) -> None:
        """Refresh model list from Ollama."""
        provider = self.get("ollama")
        try:
            models = await provider.list_models()
            self._model_cache["ollama"] = models
        except Exception as exc:
            print(f"[ProviderRegistry] Model refresh failed: {exc}")

    def cached_models(self, provider_id: str = "ollama") -> list[str]:
        return self._model_cache.get(provider_id, [])

    def start_background_refresh(self) -> None:
        """Non-blocking background model cache warmup."""
        if self._refresh_task and not self._refresh_task.done():
            return

        async def _run():
            try:
                await self.refresh_model_cache()
            except Exception:
                pass

        try:
            loop = asyncio.get_event_loop()
            self._refresh_task = loop.create_task(_run())
        except RuntimeError:
            pass  # No running event loop yet — skip

    # ── Lifecycle ────────────────────────────────────────────

    async def cleanup(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        for provider in self._providers.values():
            try:
                await provider.cleanup()
            except Exception:
                pass
        self._providers.clear()
        self._model_cache.clear()


def get_registry(base_url: str = "http://localhost:11434") -> ProviderRegistry:
    """Return module-level singleton registry."""
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = ProviderRegistry(base_url=base_url)
    return _SINGLETON
