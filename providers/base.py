# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
providers/base.py — Abstract base class for all Reflexion providers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional


@dataclass
class ProviderConfig:
    """Configuration shared by all providers."""
    base_url: str = "http://localhost:11434"
    api_key: str = ""
    timeout: int = 300
    max_retries: int = 2


class BaseProvider(ABC):
    """Abstract provider interface — all backends must implement this."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return list of available model IDs."""
        ...

    @abstractmethod
    async def stream_completion(
        self,
        model: str,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream tokens for a chat completion."""
        ...

    async def complete(
        self,
        model: str,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> str:
        """Non-streaming completion — default collects stream."""
        parts: list[str] = []
        async for token in self.stream_completion(
            model, messages, system, max_tokens, temperature, **kwargs
        ):
            parts.append(token)
        return "".join(parts)

    async def cleanup(self) -> None:
        """Release any held resources."""
        pass
