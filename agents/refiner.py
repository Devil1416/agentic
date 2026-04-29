# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
agents/refiner.py — Code optimization and patch agent.

Applies ONLY targeted patches for specific mismatches reported by the judge.
Does NOT regenerate entire files — uses edit_file_diff for surgical fixes.
"""

import json
import os
import re
from model_router import call_model
from tool_registry import get_tools_description, parse_tool_calls, execute_tool

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "42380febb7d0",
}
# ─── /fingerprint ───────────────────────────────────────────


REFINER_SYSTEM = """You are a surgical code patcher. You fix ONLY the specific mismatches listed.

{tools}

Your job is to:
1. Read only the files that contain the reported mismatches
2. Apply targeted patches using edit_file_diff — do NOT rewrite entire files
3. Fix ONLY the listed issues, touch nothing else

RULES:
- Do NOT regenerate entire files
- Use edit_file_diff for every change
- After ALL patches are applied, output: {{"action": "done", "args": {{"result": "description of patches applied"}}}}
- If a mismatch cannot be fixed with a diff patch, skip it and note it in the done result
"""

GENERIC_REFINER_SYSTEM = """You are a code optimization expert. You improve working code.

{tools}

Your job is to:
1. Read the existing code files
2. Apply targeted improvements via edit_file_diff
3. Improvements include: better error handling, cleaner code, performance, docstrings

RULES:
- Do NOT break working code
- Use edit_file_diff for changes, not full rewrites
- Make small, safe improvements
- After all improvements, output: {{"action": "done", "args": {{"result": "description of improvements"}}}}
"""

MAX_REFINE_ROUNDS = 8


def _normalize_workspace_path(path: str, workspace_dir: str) -> str:
    """Keep refiner edits constrained to the active workspace root."""


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
        if os.path.commonpath([candidate, workspace_dir]) != workspace_dir:
            candidate = os.path.join(workspace_dir, os.path.basename(candidate))
    except ValueError:
        candidate = os.path.join(workspace_dir, os.path.basename(candidate))

    return candidate


def run_refiner(workspace_dir: str, files: list[str],
                suggestions: list[str] = None,
                mismatches: list[str] = None) -> dict:
    """
    Refine and patch code files.

    When mismatches are provided (from judge contract validation), the refiner
    enters PATCH mode and applies only surgical fixes for those mismatches.
    Otherwise falls back to general quality improvement mode.

    Args:
        workspace_dir: Project directory.
        files: List of files to potentially refine.
        suggestions: Specific improvements suggested by the judge.
        mismatches: Exact contract violation strings from judge validation.

    Returns:
        Summary of refinements applied.
    """
    # Load contract for reference
    contract_text = ""
    contract_path = os.path.join(workspace_dir, "contract.json")
    if os.path.exists(contract_path):
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                contract_text = f.read()
        except Exception:
            pass

    tools_desc = get_tools_description()

    if mismatches:
        # PATCH MODE — only fix what the judge flagged
        system = REFINER_SYSTEM.format(tools=tools_desc)
        mismatch_block = "\n".join(f"  [{i+1}] {m}" for i, m in enumerate(mismatches))
        prompt = f"""Apply ONLY the following patches to fix contract mismatches.
Do NOT touch any code that is not directly related to these issues.

Workspace: {workspace_dir}

Files available:
{chr(10).join(f"  - {f}" for f in files)}

INTERFACE CONTRACT:
{contract_text}

MISMATCHES TO FIX (patch ONLY these):
{mismatch_block}

Read the relevant file(s), then apply the minimum diff needed to fix each mismatch."""
        print(f"\n{'=' * 60}")
        print(f"🩹 REFINER — Patching {len(mismatches)} contract mismatch(es)...")
        print(f"{'=' * 60}")
    else:
        # GENERIC IMPROVEMENT MODE
        system = GENERIC_REFINER_SYSTEM.format(tools=tools_desc)
        suggestions_text = ""
        if suggestions:
            suggestions_text = "Suggested improvements:\n" + "\n".join(
                f"  - {s}" for s in suggestions
            )
        file_list = "\n".join(f"  - {f}" for f in files)
        prompt = f"""Refine the following project files:

Project directory: {workspace_dir}

Files:
{file_list}

{suggestions_text}

Start by reading the main files to understand the code, then apply improvements."""
        print(f"\n{'=' * 60}")
        print(f"✨ REFINER — Optimizing code...")
        print(f"{'=' * 60}")

    refinements = []
    conversation = [prompt]

    for round_num in range(MAX_REFINE_ROUNDS):
        current_prompt = "\n\n---\n\n".join(conversation[-3:])

        response = call_model(
            role="refiner",
            prompt=current_prompt,
            system_prompt=system,
            temperature=0.2,
        )

        calls = parse_tool_calls(response)

        if not calls:
            if round_num > 2:
                break
            conversation.append(response)
            conversation.append("Please output a tool call to read or edit a file, or done if finished.")
            continue

        for call in calls:
            if call["action"] == "done":
                result_text = call.get("args", {}).get("result", "Refinement complete")
                icon = "🩹" if mismatches else "✨"
                print(f"   {icon} {result_text}")
                return {"refinements": refinements, "summary": result_text}

            # Fix relative paths
            if "path" in call.get("args", {}):
                call["args"]["path"] = _normalize_workspace_path(call["args"]["path"], workspace_dir)

            result = execute_tool(call)

            if result.get("success"):
                if call["action"] in ("edit_file_diff", "write_file"):
                    refinements.append(call)
                    icon = "🩹" if mismatches else "✏️"
                    print(f"   {icon}  Patched: {call.get('args', {}).get('path', 'unknown')}")
                conversation.append(f"Tool result: {result['result']}\n\nContinue.")
            else:
                conversation.append(f"Tool error: {result.get('error')}. Skip and continue.")

    return {"refinements": refinements, "summary": "Refinement rounds complete"}


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
