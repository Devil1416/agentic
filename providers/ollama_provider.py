# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
providers/ollama_provider.py — Ollama backend implementing BaseProvider.

Wraps the raw Ollama /api/generate and /api/tags endpoints to expose
the same async streaming interface the rest of Reflexion expects.
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx

from providers.base import BaseProvider, ProviderConfig


class OllamaProvider(BaseProvider):
    """Ollama local LLM provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def list_models(self) -> list[str]:
        """Return all locally available Ollama model names."""
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            print(f"[OllamaProvider] Cannot list models: {exc}")
            return []

    async def stream_completion(
        self,
        model: str,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion from Ollama using /api/chat (chat format)."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            # Prepend system as a system message
            payload["messages"] = [{"role": "system", "content": system}] + list(messages)

        async with self._client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        return
                except json.JSONDecodeError:
                    continue

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        stream: bool = False,
    ) -> AsyncIterator[str]:
        """Raw /api/generate wrapper (prompt-based, not chat-based)."""
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        if stream:
            async with self._client.stream("POST", "/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            return
                    except json.JSONDecodeError:
                        continue
        else:
            resp = await self._client.post("/api/generate", json={**payload, "stream": False})
            resp.raise_for_status()
            data = resp.json()
            yield data.get("response", "")

    async def cleanup(self) -> None:
        await self._client.aclose()
