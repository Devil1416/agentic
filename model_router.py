"""
model_router.py — Ollama model routing with optimized speed + quality.

DESIGN: "Fast when chatting, powerful when building."

- CHAT → gemma:7b (fast, lightweight)
- DISCUSS → llama3:8b or mixtral (reasoning)
- EXECUTE → full agent loop with specialized models
- Max 1-2 models loaded simultaneously
"""

import json
import time
import requests
from typing import Generator, Optional

OLLAMA_BASE = "http://localhost:11434"

# Role → preferred models in priority order (optimized)
ROLE_MODELS = {
    "planner":  ["llama3:8b", "llama3", "mixtral:latest", "mixtral", "mistral:7b", "gemma:7b"],
    "builder":  ["deepseek-coder:6.7b", "deepseek-coder", "codellama:7b", "llama3:8b", "gemma:7b"],
    "debugger": ["deepseek-coder:6.7b", "deepseek-coder", "codellama:7b", "llama3:8b", "gemma:7b"],
    "judge":    ["mixtral:latest", "mixtral", "llama3:8b", "llama3", "mistral:7b", "gemma:7b"],
    "refiner":  ["mixtral:latest", "mixtral", "mistral:7b", "llama3:8b", "gemma:7b"],
    "chat":     ["gemma:7b", "gemma", "gemma2:2b", "llama3:8b", "mistral:7b"],
    "vision":   ["llava:7b", "llava:13b", "llava", "bakllava", "llava-llama3", "moondream"],
    "think":    ["mixtral:latest", "mixtral", "llama3:8b", "llama3", "mistral:7b"]
}

FALLBACK_CHAIN = ["gemma:7b", "gemma", "llama3:8b", "llama3", "mistral:7b", "mistral"]

# Speed tiers — chat NEVER uses heavy models
FAST_ROLES = {"chat"}
MEDIUM_ROLES = {"planner", "judge", "refiner", "think"}
HEAVY_ROLES = {"builder", "debugger"}

# Heavy models that should NOT be used for chat
HEAVY_MODELS = {"mixtral:latest", "mixtral", "deepseek-coder:6.7b", "deepseek-coder", "codellama:7b"}

# Request logging
_request_log = []
_model_cache = {"models": [], "timestamp": 0}
MODEL_CACHE_TTL = 30  # seconds


def get_installed_models() -> list[str]:
    """Query Ollama for locally available models. Cached for performance."""
    now = time.time()
    if _model_cache["models"] and (now - _model_cache["timestamp"]) < MODEL_CACHE_TTL:
        return _model_cache["models"]
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        _model_cache["models"] = models
        _model_cache["timestamp"] = now
        return models
    except Exception as e:
        print(f"[model_router] ⚠ Cannot reach Ollama: {e}")
        return _model_cache.get("models", [])


def pick_model(role: str, installed: list[str]) -> Optional[str]:
    """Pick the best available model for a given role."""
    candidates = get_candidate_models(role, installed)
    return candidates[0] if candidates else None


def get_candidate_models(role: str, installed: list[str]) -> list[str]:
    """Return installed models in preference order for a role."""
    requested = ROLE_MODELS.get(role, []) + FALLBACK_CHAIN

    if role in FAST_ROLES:
        requested = [m for m in requested if m not in HEAVY_MODELS]

    resolved = []

    for model in requested:
        if model in installed and model not in resolved:
            resolved.append(model)

    for model in requested:
        base = model.split(":")[0]
        for inst in installed:
            if inst.startswith(base):
                if role in FAST_ROLES and inst in HEAVY_MODELS:
                    continue
                if inst not in resolved:
                    resolved.append(inst)

    for inst in installed:
        if inst not in resolved:
            resolved.append(inst)

    return resolved


def _log_request(role: str, model: str, prompt_len: int, duration_ms: int):
    """Log model request for debugging and optimization."""
    entry = {
        "role": role,
        "model": model,
        "prompt_chars": prompt_len,
        "duration_ms": duration_ms,
        "timestamp": time.time(),
    }
    _request_log.append(entry)
    # Keep last 100 entries
    if len(_request_log) > 100:
        _request_log[:] = _request_log[-100:]


def get_request_log() -> list[dict]:
    """Return recent model request log."""
    return list(_request_log)


def call_model(role: str, prompt: str, stream: bool = False,
               system_prompt: str = "", temperature: float = 0.3,
               max_tokens: int = 4096) -> str | Generator[str, None, None]:
    """
    Call Ollama model for a given role.
    If stream=True, returns a generator yielding tokens.
    If stream=False, returns the full response string.
    """
    installed = get_installed_models()
    candidates = get_candidate_models(role, installed)

    if not candidates:
        raise RuntimeError(
            f"[model_router] No model available for role '{role}'. "
            f"Installed: {installed}. Install a model with: ollama pull llama3:8b"
        )

    model = candidates[0]

    # Optimize token limits per role
    if role in FAST_ROLES:
        max_tokens = min(max_tokens, 1024)  # Cap chat responses
        temperature = max(temperature, 0.5)  # More natural chat

    print(f"[model_router] 🧠 {role} → {model} (prompt: {len(prompt)} chars)")

    start = time.time()

    if stream:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        return _stream_response(payload, role, start)
    else:
        errors = []
        for candidate in candidates:
            payload = {
                "model": candidate,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if system_prompt:
                payload["system"] = system_prompt

            try:
                result = _blocking_response(payload)
                duration_ms = int((time.time() - start) * 1000)
                _log_request(role, candidate, len(prompt), duration_ms)
                return result
            except Exception as e:
                errors.append(f"{candidate}: {e}")
                if candidate != candidates[-1]:
                    print(f"[model_router] Fallback from {candidate} for role '{role}': {e}")

        raise RuntimeError(
            f"[model_router] All candidate models failed for role '{role}'. "
            + " | ".join(errors)
        )


def _blocking_response(payload: dict) -> str:
    """Non-streaming Ollama call."""
    payload["stream"] = False
    resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json().get("response", "")


def _stream_response(payload: dict, role: str = "", start: float = 0) -> Generator[str, None, None]:
    """Streaming Ollama call — yields tokens as they arrive."""
    payload["stream"] = True
    with requests.post(f"{OLLAMA_BASE}/api/generate", json=payload,
                       stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        if start:
                            duration_ms = int((time.time() - start) * 1000)
                            _log_request(role, payload.get("model", "?"), 0, duration_ms)
                        return
                except json.JSONDecodeError:
                    continue


def call_model_streaming_print(role: str, prompt: str,
                               system_prompt: str = "",
                               temperature: float = 0.3) -> str:
    """Stream tokens to stdout in real-time and return the full response."""
    full = []
    for token in call_model(role, prompt, stream=True,
                            system_prompt=system_prompt,
                            temperature=temperature):
        print(token, end="", flush=True)
        full.append(token)
    print()  # newline after streaming
    return "".join(full)
