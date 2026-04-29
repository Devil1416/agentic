# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
tool_registry.py — Central tool registration, parsing, and dispatch.

Agents emit JSON tool calls. This module:
  1. Registers available tools
  2. Parses tool calls from model output
  3. Executes them and returns results
"""

import json
import re
from typing import Any, Callable

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "d5b26b63bf79",
}
# ─── /fingerprint ───────────────────────────────────────────


# Global tool registry
_TOOLS: dict[str, Callable] = {}
_TOOL_DOCS: dict[str, str] = {}


def register_tool(name: str, func: Callable, doc: str = ""):
    """Register a tool function by name."""


    _TOOLS[name] = func
    _TOOL_DOCS[name] = doc or (func.__doc__ or "No description.")


def get_tool(name: str) -> Callable | None:
    return _TOOLS.get(name)


def list_tools() -> list[str]:
    return list(_TOOLS.keys())


def get_tools_description() -> str:
    """Generate a tool description block for agent system prompts."""
    lines = ["Available tools:\n"]
    for name, doc in _TOOL_DOCS.items():
        lines.append(f"  - {name}: {doc.strip()}")
    lines.append("")
    lines.append("To use a tool, output EXACTLY one JSON block:")
    lines.append('```json')
    lines.append('{')
    lines.append('  "action": "<tool_name>",')
    lines.append('  "args": { ... }')
    lines.append('}')
    lines.append('```')
    lines.append("")
    lines.append("If you have no tool to call, output:")
    lines.append('```json')
    lines.append('{"action": "done", "args": {"result": "your final answer"}}')
    lines.append('```')
    return "\n".join(lines)


def parse_tool_calls(text: str) -> list[dict]:
    """
    Extract tool call JSON objects from model output.
    Handles markdown code fences and raw JSON with nested braces.
    Returns list of {action, args} dicts.
    """
    calls = []

    # Try markdown-fenced JSON blocks first
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    for block in fenced:
        parsed = _try_parse(block)
        if parsed:
            calls.append(parsed)

    # Try brace-balanced JSON extraction if no fenced blocks found
    if not calls:
        for obj_str in _extract_json_objects(text):
            parsed = _try_parse(obj_str)
            if parsed:
                calls.append(parsed)

    return calls


def _extract_json_objects(text: str) -> list[str]:
    """Extract top-level JSON objects from text using brace balancing."""
    objects = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            depth = 0
            start = i
            in_string = False
            escape = False
            while i < len(text):
                ch = text[i]
                if escape:
                    escape = False
                elif ch == '\\' and in_string:
                    escape = True
                elif ch == '"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            candidate = text[start:i + 1]
                            if '"action"' in candidate:
                                objects.append(candidate)
                            break
                i += 1
        i += 1
    return objects


def _try_parse(text: str) -> dict | None:
    """Attempt to parse a JSON tool call."""
    try:
        obj = json.loads(text)
        if "action" in obj:
            return {
                "action": obj["action"],
                "args": obj.get("args", {}),
            }
    except json.JSONDecodeError:
        # Try fixing common LLM JSON mistakes
        fixed = text.replace("'", '"')
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            obj = json.loads(fixed)
            if "action" in obj:
                return {
                    "action": obj["action"],
                    "args": obj.get("args", {}),
                }
        except json.JSONDecodeError:
            pass
    return None


def execute_tool(call: dict) -> dict:
    """
    Execute a parsed tool call.
    Returns {"success": bool, "result": str} or {"success": False, "error": str}.
    """
    action = call.get("action", "")
    args = call.get("args", {})

    if action == "done":
        return {"success": True, "result": args.get("result", "Done."), "done": True}

    func = get_tool(action)
    if not func:
        return {
            "success": False,
            "error": f"Unknown tool: '{action}'. Available: {list_tools()}"
        }

    try:
        result = func(**args)
        return {"success": True, "result": str(result)}
    except TypeError as e:
        return {"success": False, "error": f"Bad arguments for '{action}': {e}"}
    except Exception as e:
        return {"success": False, "error": f"Tool '{action}' failed: {e}"}

import subprocess

def pull_ollama_model(model_name: str) -> str:
    """Pull an Ollama model."""
    print(f"\n[tool_registry] Pulling Ollama model: {model_name}...")
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            print(line, end="")
        process.wait(timeout=300)
        if process.returncode == 0:
            return f"Successfully pulled {model_name}"
        return f"Failed to pull {model_name}"
    except Exception as e:
        return f"Error pulling model: {e}"

register_tool("pull_ollama_model", pull_ollama_model, "Pull an Ollama model.")


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
