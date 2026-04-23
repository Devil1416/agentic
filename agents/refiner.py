"""
agents/refiner.py — Code optimization and polish agent.

Takes working code and improves quality, performance, and readability.
"""

import os
from model_router import call_model
from tool_registry import get_tools_description, parse_tool_calls, execute_tool

REFINER_SYSTEM = """You are a code optimization expert. You improve working code.

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
                suggestions: list[str] = None) -> dict:
    """
    Refine and optimize code files.

    Args:
        workspace_dir: Project directory.
        files: List of files to potentially refine.
        suggestions: Specific improvements suggested by the judge.

    Returns:
        Summary of refinements applied.
    """
    tools_desc = get_tools_description()
    system = REFINER_SYSTEM.format(tools=tools_desc)

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
                print(f"   ✨ {result_text}")
                return {"refinements": refinements, "summary": result_text}

            # Fix relative paths
            if "path" in call.get("args", {}):
                call["args"]["path"] = _normalize_workspace_path(call["args"]["path"], workspace_dir)

            result = execute_tool(call)

            if result.get("success"):
                if call["action"] in ("edit_file_diff", "write_file"):
                    refinements.append(call)
                    print(f"   ✏️  Refined: {call.get('args', {}).get('path', 'unknown')}")
                conversation.append(f"Tool result: {result['result']}\n\nContinue refining.")
            else:
                conversation.append(f"Tool error: {result.get('error')}. Skip and continue.")

    return {"refinements": refinements, "summary": "Refinement rounds complete"}
