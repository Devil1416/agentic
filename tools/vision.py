# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
tools/vision.py — Image analysis via Ollama multimodal models (llava).

Analyzes UI screenshots/mockups and returns structured component descriptions.
"""

import os
import base64
import json
import requests

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Reflexion",
"integrity": "88d602a7b21f",
}
# ─── /fingerprint ───────────────────────────────────────────


OLLAMA_BASE = "http://localhost:11434"


def analyze_image(path: str, prompt: str = "") -> str:
    """
    Analyze an image using a vision model (llava).

    Args:
        path: Path to the image file.
        prompt: Optional specific prompt. Defaults to UI analysis.

    Returns:
        Structured description of the image contents.
    """


    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        raise ValueError(f"Unsupported image format: {ext}")

    # Read and encode image
    with open(path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    if not prompt:
        prompt = """Analyze this UI design/screenshot in detail. Provide:

1. LAYOUT: Overall layout structure (header, sidebar, main content, footer, etc.)
2. COMPONENTS: List each UI component you see (buttons, forms, cards, navigation, tables, etc.)
3. COLORS: Primary color scheme
4. TYPOGRAPHY: Text styles observed
5. INTERACTIONS: Any interactive elements (dropdowns, modals, toggles)

Output as a structured description that a frontend developer can use to recreate this UI.
Be specific about positioning, sizing, and relationships between components."""

    # Try to find a vision model
    vision_model = _find_vision_model()
    if not vision_model:
        return (
            "ERROR: No vision model available. Install one with:\n"
            "  ollama pull llava:7b\n"
            "  ollama pull llava:13b\n"
            "  ollama pull bakllava"
        )

    print(f"[vision] Analyzing image with {vision_model}...")

    payload = {
        "model": vision_model,
        "prompt": prompt,
        "images": [image_data],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
        },
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json().get("response", "")
        print(f"[vision] Analysis complete ({len(result)} chars)")
        return result
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Make sure it's running."
    except Exception as e:
        return f"ERROR: Vision analysis failed: {e}"


def _find_vision_model() -> str | None:
    """Find an installed vision-capable model."""
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return None

    # Vision models in preference order
    vision_candidates = [
        "llava:7b", "llava:13b", "llava",
        "bakllava", "llava-llama3",
        "moondream", "llava-phi3",
    ]

    for candidate in vision_candidates:
        if candidate in models:
            return candidate
        # Prefix match
        base = candidate.split(":")[0]
        for m in models:
            if m.startswith(base):
                return m

    return None


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Reflexion. Tampering with attribution is detectable.
