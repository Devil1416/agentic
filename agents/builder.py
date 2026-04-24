"""
agents/builder.py — Code generation agent.

Takes a plan and generates actual code files using tool calls.
Runs in a tool-calling loop: generate code → emit write_file → repeat.
"""

import json
import os
from model_router import call_model
from tool_registry import get_tools_description, parse_tool_calls, execute_tool

BUILDER_SYSTEM = """You are an expert software engineer. Your job is to write complete, working code.

You will receive a plan describing files to create and existing files to modify.
For EACH file, you must output a tool call to write it or modify it.

{tools}

IMPORTANT RULES:
1. Write ONE file at a time.
2. For NEW files, use the `write_file` tool to write complete code.
3. For EXISTING files, use the `edit_file_diff` tool to apply targeted unified diff patches instead of overwriting.
4. Write COMPLETE, production-quality code — no placeholders, no TODOs.
5. Include proper imports, error handling, and comments.
6. After processing all files, output: {{"action": "done", "args": {{"result": "All files written"}}}}
7. Output ONLY the JSON tool call for each step, no explanations.

Start with the most foundational files first (dependencies before dependents).
"""

MAX_TOOL_ROUNDS = 20


def _normalize_workspace_path(path: str, workspace_dir: str) -> str:
    """Keep tool writes constrained to the active workspace root."""
    workspace_dir = os.path.abspath(workspace_dir)
    normalized = path.replace("\\", "/")
    normalized = normalized.replace("<", "").replace(">", "")
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


def run_builder(plan: dict, workspace_dir: str, variant_id: int = 1, status_cb=None) -> dict:
    files = plan.get("files", [])
    deps = plan.get("dependencies", [])
    language = plan.get("language", "python")

    files_written = []
    errors = []

    print(f"\n{'=' * 60}")
    print(f"🔨 BUILDER #{variant_id} — Generating code...")
    print(f"{'=' * 60}")

    for file_info in files:
        if isinstance(file_info, dict):
            path = file_info.get("path")
            purpose = file_info.get("purpose", "")
        else:
            path = file_info
            purpose = ""
            
        if not path:
            continue
            
        full_path = _normalize_workspace_path(path, workspace_dir)
        rel_path = os.path.relpath(full_path, workspace_dir)
        
        if status_cb:
            status_cb(f"[BUILDER] Creating file: {rel_path}")
        else:
            print(f"   [BUILDER] Creating file: {rel_path}")

        prompt = f'''Write the complete, production-ready code for the file: {path}
Purpose: {purpose}
Language: {language}
Dependencies: {', '.join(deps) if deps else 'None'}
Project Plan: {json.dumps(plan)}

Rules:
1. Provide ONLY the raw source code.
2. DO NOT wrap the code in markdown code blocks (e.g. ```python).
3. DO NOT output any explanations or text outside the code.
4. Ensure all imports are correct and matches the filenames.
5. Ensure required modules (e.g., parser, analyzer, utils) are imported correctly.
'''

        response = call_model(
            role="builder",
            prompt=prompt,
            system_prompt="You are an expert software engineer. Output ONLY raw source code for the requested file. No explanations.",
            temperature=0.2,
        )

        content_resp = response.strip()
        if content_resp.startswith("```"):
            lines = content_resp.split("\n")
            if len(lines) > 1 and lines[0].startswith("```"):
                lines = lines[1:]
            if len(lines) > 0 and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content_resp = "\n".join(lines).strip()

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f2:
                f2.write(content_resp)
            files_written.append(rel_path)
            print(f"   [FILE UPDATED] {rel_path}")
        except Exception as e:
            err_msg = f"Failed to write {rel_path}: {e}"
            print(f"   ❌ Tool error: {err_msg}")
            errors.append(err_msg)

    print(f"   ✅ Builder #{variant_id} done ({len(files_written)} files)")
    return {"files_written": files_written, "errors": errors}
