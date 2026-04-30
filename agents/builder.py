# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
agents/builder.py — Code generation agent.

Takes a plan and generates actual code files using tool calls.
Runs in a tool-calling loop: generate code → emit write_file → repeat.
"""

import json
import os
from model_router import call_model
from tool_registry import get_tools_description, parse_tool_calls, execute_tool

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
"integrity": "2d37dd140d9a",
}
# ─── /fingerprint ───────────────────────────────────────────


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


def run_builder(plan: dict, workspace_dir: str, variant_id: int = 1, status_cb=None, is_self_improve: bool = False) -> dict:
    files = plan.get("files", [])
    deps = plan.get("dependencies", [])
    language = plan.get("language", "python")

    files_written = []
    errors = []

    # Enforce contract
    contract_path = os.path.join(workspace_dir, "contract.json")
    if not os.path.exists(contract_path):
        err = "contract.json missing. Builder halted. Request planner to regenerate it."
        print(f"   ❌ {err}")
        return {"files_written": [], "errors": [err]}

    with open(contract_path, "r", encoding="utf-8") as f:
        contract_data = f.read()

    shared_context = []

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

        if is_self_improve:
            # Self Improvement Mode: Generate unified diff
            prompt = f'''Modify the following file using a Unified Diff format: {path}
Purpose: {purpose}

INTERFACE CONTRACT: {contract_data}

Rules:
1. You MUST output ONLY a valid unified diff (starting with --- and +++).
2. NO full file rewrites.
3. NO new file creation or deletion.
4. DO NOT wrap in markdown.
'''
            response = call_model(role="builder", prompt=prompt, system_prompt="You are modifying your own system. Output ONLY a valid unified diff.", temperature=0.2)
            content_resp = response.strip()
            if content_resp.startswith("```"):
                lines = content_resp.split("\n")
                if len(lines) > 1 and lines[0].startswith("```"): lines = lines[1:]
                if len(lines) > 0 and lines[-1].strip().startswith("```"): lines = lines[:-1]
                content_resp = "\n".join(lines).strip()
            
            try:
                from tools.diff_editor import edit_file_diff
                import ast
                # Write patch to temp file and validate syntax
                temp_file = full_path + ".temp"
                import shutil
                if os.path.exists(full_path):
                    shutil.copy2(full_path, temp_file)
                else:
                    open(temp_file, "w").close()
                edit_file_diff(temp_file, content_resp)
                
                # Run ast.parse
                if full_path.endswith(".py"):
                    with open(temp_file, "r", encoding="utf-8") as tf:
                        temp_code = tf.read()
                    try:
                        ast.parse(temp_code)
                    except SyntaxError as e:
                        raise Exception(f"SyntaxError in generated code: {e}")
                
                # If valid, replace original file
                shutil.copy2(temp_file, full_path)
                os.remove(temp_file)
                files_written.append(rel_path)
                shared_context.append({"file": path, "code": "diff applied"})
                print(f"   [FILE PATCHED] {rel_path}")
            except Exception as e:
                err_msg = f"Failed to patch {rel_path}: {e}"
                print(f"   ❌ Tool error (PATCH REJECTED): {err_msg}")
                errors.append(err_msg)

        else:
            prompt = f'''Write the complete, production-ready code for the file: {path}
Purpose: {purpose}
Language: {language}
Dependencies: {', '.join(deps) if deps else 'None'}
Project Plan: {json.dumps(plan)}

INTERFACE CONTRACT (strict, no deviation): 
{contract_data}

Rules:
1. Provide ONLY the raw source code.
2. DO NOT wrap the code in markdown code blocks (e.g. ```python).
3. DO NOT output any explanations or text outside the code.
4. Ensure all imports are correct and matches the filenames.
5. Ensure required modules (e.g., parser, analyzer, utils) are imported correctly.
6. HTML must use html_ids exactly.
7. JS must reference html_ids and use fetch(api_base + route) - NO RELATIVE PATHS.
8. All file paths in href/src must match static_files exactly.

Previously Generated Files in this iteration:
{json.dumps([{"file": sc["file"], "content_snippet": sc["code"][:200] + "..."} for sc in shared_context], indent=2)}
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
                shared_context.append({"file": path, "code": content_resp})
                print(f"   [FILE UPDATED] {rel_path}")
            except Exception as e:
                err_msg = f"Failed to write {rel_path}: {e}"
                print(f"   ❌ Tool error: {err_msg}")
                errors.append(err_msg)

    print(f"   ✅ Builder #{variant_id} done ({len(files_written)} files)")
    return {"files_written": files_written, "errors": errors}


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
