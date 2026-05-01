# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
agents/debugger.py — Error analysis and auto-fix agent.

Analyzes execution errors and applies diff-based fixes.
"""

import json
import os
from model_router import call_model
from tool_registry import get_tools_description, parse_tool_calls, execute_tool
from memory.vector_store import get_relevant_context, add_memory

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
"integrity": "addcf2a82b51",
}
# ─── /fingerprint ───────────────────────────────────────────


DEBUGGER_SYSTEM = """You are an expert debugger. You analyze errors and fix code.

{tools}

When you find a bug:
1. First use read_file to examine the problematic file
2. Then use edit_file_diff to apply a targeted fix
3. Do NOT rewrite entire files unless absolutely necessary

Diff format for edit_file_diff:
--- old
+++ new
@@ -line_num,count +line_num,count @@
 context line (unchanged)
-line to remove
+line to add

RULES:
- ONLY: fix imports, create missing files, fix syntax errors.
- NEVER: run git, NEVER modify unrelated files.
- Fix ONE issue at a time
- Use minimal, targeted diffs
- After fixing, output: {{"action": "done", "args": {{"result": "description of fix"}}}}
- If you cannot fix the issue, output: {{"action": "done", "args": {{"result": "CANNOT_FIX: reason"}}}}
"""

MAX_DEBUG_ROUNDS = 5


def _normalize_workspace_path(path: str, workspace_dir: str) -> str:
    """Keep debugger edits constrained to the active workspace root."""


    workspace_dir = os.path.abspath(workspace_dir)
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part and part != "."]

    if ".variants" in parts:
        idx = parts.index(".variants")
        if len(parts) > idx + 3:
            parts = parts[idx + 3:]
        else:
            parts = parts[-1:]
        normalized = "/".join(parts)

    candidate = normalized
    if os.path.isabs(candidate):
        candidate = os.path.abspath(candidate)
    else:
        candidate = os.path.abspath(os.path.join(workspace_dir, candidate))

    try:
        # Use normcase for case-insensitive comparison on Windows
        common = os.path.commonpath([os.path.normcase(candidate), os.path.normcase(workspace_dir)])
        if common != os.path.normcase(workspace_dir):
            # Preserve relative path structure instead of just basename
            candidate = os.path.join(workspace_dir, "/".join(parts))
    except ValueError:
        # Different drives on Windows — use relative parts
        candidate = os.path.join(workspace_dir, "/".join(parts))

    return candidate


def run_debugger(error_output: str, workspace_dir: str, files: list[str] = None, status_cb=None) -> dict:
    """
    Analyze and fix errors from code execution.

    Args:
        error_output: The stderr/error output from execution.
        workspace_dir: Project directory.
        files: List of relevant file paths.
        status_cb: Optional callback to stream status to UI.

    Returns:
        Dict with fixes applied and status.
    """
    tools_desc = get_tools_description()
    system = DEBUGGER_SYSTEM.format(tools=tools_desc)

    # Get relevant memories of past fixes
    memory_context = get_relevant_context(f"error fix: {error_output[:200]}")

    file_list = "\n".join(f"  - {f}" for f in (files or []))

    # ── Extract file paths from traceback for accurate targeting ──────
    import re as _re
    traceback_files = []
    for match in _re.finditer(r'File "([^"]+)", line (\d+)', error_output):
        abs_path = match.group(1)
        line_num = match.group(2)
        # Map absolute path to workspace-relative path
        try:
            rel = os.path.relpath(abs_path, workspace_dir).replace("\\", "/")
            if not rel.startswith(".."):
                traceback_files.append(f"  - {rel} (line {line_num})")
        except ValueError:
            pass  # different drives on Windows

    traceback_mapping = ""
    if traceback_files:
        traceback_mapping = (
            "\nTraceback file mapping (use THESE paths for read_file/edit_file_diff):\n"
            + "\n".join(traceback_files)
        )
    # ─────────────────────────────────────────────────────────────────

    prompt = f"""The following error occurred when running the project:

```
{error_output}
```

Project directory: {workspace_dir}
Project files:
{file_list}
{traceback_mapping}

{memory_context}

Analyze the error and fix it using the available tools.
Start by reading the file mentioned in the error trace."""

    print(f"\n{'=' * 60}")
    print(f"🐛 DEBUGGER — Analyzing error...")
    print(f"{'=' * 60}")

    fixes = []
    conversation = [prompt]
    _prev_response = None  # convergence detection

    for round_num in range(MAX_DEBUG_ROUNDS):
        current_prompt = "\n\n---\n\n".join(conversation[-4:])

        response = call_model(
            role="debugger",
            prompt=current_prompt,
            system_prompt=system,
            temperature=0.1,
        )

        # ── Convergence detection: break if model repeats itself ────────
        if _prev_response and response.strip() == _prev_response.strip():
            print("   ⚠ Debugger stuck (same response). Exiting.")
            break
        _prev_response = response
        # ──────────────────────────────────────────────────────────────────

        calls = parse_tool_calls(response)

        if not calls:
            if round_num > 1:
                break
            conversation.append(response)
            conversation.append(
                "Please output a valid JSON tool call to investigate or fix the error."
            )
            continue

        for call in calls:
            if call["action"] == "done":
                result_text = call.get("args", {}).get("result", "")
                print(f"   🔧 Debugger: {result_text}")

                # Store fix in memory
                if not result_text.startswith("CANNOT_FIX"):
                    add_memory(
                        f"Error: {error_output[:200]}\nFix: {result_text}",
                        category="fix"
                    )

                return {
                    "fixed": not result_text.startswith("CANNOT_FIX"),
                    "fixes": fixes,
                    "summary": result_text,
                }

            # Fix relative paths
            if "path" in call.get("args", {}):
                call["args"]["path"] = _normalize_workspace_path(call["args"]["path"], workspace_dir)

            result = execute_tool(call)

            if result.get("success"):
                print(f"   🔍 {call['action']}: OK")
                if call["action"] in ("edit_file_diff", "write_file"):
                    fixes.append(call)
                    try:
                        p = call.get("args", {}).get("path", "unknown")
                        rel_path = os.path.relpath(p, workspace_dir)
                        if status_cb:
                            status_cb(f"[FILE UPDATED] {rel_path}")
                        else:
                            print(f"   [FILE UPDATED] {rel_path}")
                    except Exception:
                        pass
                conversation.append(f"Tool result:\n{result['result']}\n\nContinue debugging.")
            else:
                print(f"   ❌ {call['action']}: {result.get('error', 'failed')}")
                conversation.append(f"Tool error: {result.get('error')}. Try a different approach.")

    # Store failure in memory
    add_memory(f"Unresolved error: {error_output[:300]}", category="error")

    return {"fixed": False, "fixes": fixes, "summary": "Max debug rounds reached"}


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
