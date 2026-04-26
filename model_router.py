"""
model_router.py - Ollama model routing with speed and reliability safeguards.

Design goal: fast when chatting, capable when building, resilient when a
preferred model is temporarily unhealthy.
"""

import json
import time
from typing import Generator, Optional

import requests

OLLAMA_BASE = "http://localhost:11434"
_session = requests.Session()

ROLE_MODELS = {
    "planner": ["gemma4:latest", "llama3:8b", "llama3", "mixtral:latest", "mixtral", "mistral:7b", "gemma:7b"],
    "builder": ["deepseek-coder:6.7b", "deepseek-coder", "codellama:7b", "llama3:8b"],
    "debugger": ["deepseek-coder:6.7b", "deepseek-coder", "codellama:7b", "llama3:8b"],
    "judge": ["llama3:8b", "mixtral:latest", "mixtral", "llama3", "mistral:7b", "gemma:7b"],
    "refiner": ["mixtral:latest", "llama3:8b", "mixtral", "mistral:7b", "gemma:7b"],
    "chat": ["gemma4:latest", "gemma:7b", "gemma", "gemma2:2b", "llama3:8b", "mistral:7b"],
    "vision": ["llava:7b", "llava:13b", "llava", "bakllava", "llava-llama3", "moondream"],
    "think": ["llama3:8b", "mixtral:latest", "llama3", "mixtral", "mistral:7b", "gemma:7b"],
}

FALLBACK_CHAIN = ["gemma:7b", "gemma", "llama3:8b", "llama3", "mistral:7b", "mistral"]
FAST_ROLES = {"chat"}
HEAVY_MODELS = {"mixtral:latest", "mixtral", "deepseek-coder:6.7b", "deepseek-coder", "codellama:7b"}

_request_log = []
_model_cache = {"models": [], "timestamp": 0}
_model_failure_until: dict[str, float] = {}

MODEL_CACHE_TTL = 30
MODEL_FAILURE_BACKOFF_S = 120


def get_installed_models() -> list[str]:
    """Query Ollama for locally available models. Cached for performance."""
    now = time.time()
    if _model_cache["models"] and (now - _model_cache["timestamp"]) < MODEL_CACHE_TTL:
        return _model_cache["models"]

    try:
        resp = _session.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [model["name"] for model in data.get("models", [])]
        _model_cache["models"] = models
        _model_cache["timestamp"] = now
        return models
    except Exception as e:
        print(f"[model_router] Cannot reach Ollama: {e}")
        return _model_cache.get("models", [])


def get_candidate_models(role: str, installed: list[str]) -> list[str]:
    """Return installed models in preference order for a role."""
    requested = ROLE_MODELS.get(role, []) + FALLBACK_CHAIN
    if role in FAST_ROLES:
        requested = [model for model in requested if model not in HEAVY_MODELS]

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

    now = time.time()
    healthy = [model for model in resolved if _model_failure_until.get(model, 0) <= now]
    return healthy or resolved


def pick_model(role: str, installed: list[str]) -> Optional[str]:
    """Pick the best currently available model for a given role."""
    candidates = get_candidate_models(role, installed)
    return candidates[0] if candidates else None


def _log_request(role: str, model: str, prompt_len: int, duration_ms: int):
    entry = {
        "role": role,
        "model": model,
        "prompt_chars": prompt_len,
        "duration_ms": duration_ms,
        "timestamp": time.time(),
    }
    _request_log.append(entry)
    if len(_request_log) > 100:
        _request_log[:] = _request_log[-100:]


def get_request_log() -> list[dict]:
    """Return recent model request log."""
    return list(_request_log)


def _mark_model_failure(model: str):
    _model_failure_until[model] = time.time() + MODEL_FAILURE_BACKOFF_S


def _clear_model_failure(model: str):
    _model_failure_until.pop(model, None)


def call_model(role: str, prompt: str, stream: bool = False,
               system_prompt: str = "", temperature: float = 0.3,
               max_tokens: int = 4096) -> str | Generator[str, None, None]:
    """
    Call an Ollama model for a given role.
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

    if role in FAST_ROLES:
        max_tokens = min(max_tokens, 1024)
        temperature = max(temperature, 0.5)

    start = time.time()

    if stream:
        return _stream_with_fallback(candidates, role, prompt, system_prompt, temperature, max_tokens, start)

    errors = []
    for candidate in candidates:
        print(f"[model_router] {role} -> {candidate} (prompt: {len(prompt)} chars)")
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
            _clear_model_failure(candidate)
            duration_ms = int((time.time() - start) * 1000)
            _log_request(role, candidate, len(prompt), duration_ms)
            return result
        except Exception as e:
            _mark_model_failure(candidate)
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
    try:
        resp = _session.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 500:
            print(f"[model_router] 500 error from {payload.get('model')}, retrying once...")
            time.sleep(2)
            resp = _session.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json().get("response", "")
        raise


def _stream_with_fallback(candidates: list[str], role: str, prompt: str, system_prompt: str,
                          temperature: float, max_tokens: int, start: float) -> Generator[str, None, None]:
    """Streaming Ollama call with fallback across candidate models."""
    errors = []

    for candidate in candidates:
        print(f"[model_router] {role} -> {candidate} (prompt: {len(prompt)} chars)")
        payload = {
            "model": candidate,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        emitted = False
        try:
            for token in _stream_response(payload, role, start):
                emitted = True
                yield token
            _clear_model_failure(candidate)
            return
        except Exception as e:
            _mark_model_failure(candidate)
            errors.append(f"{candidate}: {e}")
            if emitted:
                raise
            if candidate != candidates[-1]:
                print(f"[model_router] Fallback from {candidate} for role '{role}': {e}")

    raise RuntimeError(
        f"[model_router] All candidate models failed for role '{role}'. "
        + " | ".join(errors)
    )


def _stream_response(payload: dict, role: str = "", start: float = 0) -> Generator[str, None, None]:
    """Streaming Ollama call - yields tokens as they arrive."""
    payload["stream"] = True
    with _session.post(f"{OLLAMA_BASE}/api/generate", json=payload, stream=True, timeout=300) as resp:
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
    """Stream tokens to stdout in real time and return the full response."""
    full = []
    for token in call_model(
        role,
        prompt,
        stream=True,
        system_prompt=system_prompt,
        temperature=temperature,
    ):
        print(token, end="", flush=True)
        full.append(token)
    print()
    return "".join(full)
