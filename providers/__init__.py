# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
providers/__init__.py — Provider package for Reflexion.
Mirrors free-claude-code providers structure, backed by Ollama.
"""
from providers.base import BaseProvider, ProviderConfig
from providers.ollama_provider import OllamaProvider
from providers.registry import ProviderRegistry

__all__ = ["BaseProvider", "ProviderConfig", "OllamaProvider", "ProviderRegistry"]
