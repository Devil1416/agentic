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

import ast
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

# (MAX_TOOL_ROUNDS removed — builder now iterates per-file, not tool rounds)


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
        # Use normcase for case-insensitive comparison on Windows
        common = os.path.commonpath([os.path.normcase(candidate), os.path.normcase(workspace_dir)])
        if common != os.path.normcase(workspace_dir):
            # Preserve relative path structure instead of just basename
            # e.g., "src/utils.py" stays "src/utils.py", not just "utils.py"
            candidate = os.path.join(workspace_dir, "/".join(parts))
    except ValueError:
        # Different drives on Windows — use relative parts
        candidate = os.path.join(workspace_dir, "/".join(parts))

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

    # ── Graphify context: compact project structure (token-optimized) ────
    graphify_context = ""
    try:
        from codebase.retriever import get_tree_context
        graphify_context = get_tree_context(workspace_dir, max_files=20)
    except Exception:
        pass

    # Build a compact plan summary instead of dumping the full plan JSON
    plan_summary_parts = [
        f"Project: {plan.get('project_name', 'unnamed')}",
        f"Description: {plan.get('description', 'N/A')}",
        f"Language: {language}",
        f"Entrypoint: {plan.get('entrypoint', 'main.py')}",
        f"Dependencies: {', '.join(deps) if deps else 'None'}",
        "Files to create:",
    ]
    for fi in files:
        if isinstance(fi, dict):
            plan_summary_parts.append(f"  - {fi.get('path', '?')}: {fi.get('purpose', '')}")
        else:
            plan_summary_parts.append(f"  - {fi}")
    plan_summary = "\n".join(plan_summary_parts)

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

Project Structure (compact):
{plan_summary}

{f"Existing Codebase (Graphify index):{chr(10)}{graphify_context}" if graphify_context and "no files indexed" not in graphify_context.lower() else ""}

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

                # ── SYNTAX VALIDATION: ast.parse() every Python file ──────────
                syntax_ok = True
                if full_path.endswith(".py"):
                    try:
                        ast.parse(content_resp)
                        print(f"   [SYNTAX OK] {rel_path}")
                    except SyntaxError as syn_err:
                        print(f"   ⚠ [SYNTAX ERROR] {rel_path}: {syn_err}")
                        syntax_ok = False
                        # Auto-fix: invoke debugger to repair syntax
                        fix_attempts = 0
                        MAX_SYNTAX_FIXES = 3
                        while fix_attempts < MAX_SYNTAX_FIXES:
                            fix_attempts += 1
                            print(f"   [AUTO-FIX] Attempt {fix_attempts}/{MAX_SYNTAX_FIXES} for {rel_path}")
                            fix_prompt = f'''Fix the following SyntaxError in this Python file.

File: {path}
Error: {syn_err}

Current code:
```python
{content_resp}
```

Output ONLY the corrected raw source code. No explanations. No markdown blocks.'''
                            fixed_resp = call_model(
                                role="debugger",
                                prompt=fix_prompt,
                                system_prompt="You fix Python syntax errors. Output ONLY raw corrected source code.",
                                temperature=0.1,
                            ).strip()
                            # Strip markdown fences if present
                            if fixed_resp.startswith("```"):
                                flines = fixed_resp.split("\n")
                                if len(flines) > 1 and flines[0].startswith("```"):
                                    flines = flines[1:]
                                if flines and flines[-1].strip().startswith("```"):
                                    flines = flines[:-1]
                                fixed_resp = "\n".join(flines).strip()
                            try:
                                ast.parse(fixed_resp)
                                content_resp = fixed_resp
                                with open(full_path, "w", encoding="utf-8") as f2:
                                    f2.write(content_resp)
                                print(f"   ✅ [SYNTAX FIXED] {rel_path} (attempt {fix_attempts})")
                                syntax_ok = True
                                break
                            except SyntaxError as retry_err:
                                syn_err = retry_err
                                if fix_attempts >= MAX_SYNTAX_FIXES:
                                    err_msg = f"Syntax unfixable after {MAX_SYNTAX_FIXES} attempts in {rel_path}: {retry_err}"
                                    print(f"   ❌ {err_msg}")
                                    errors.append(err_msg)
                # ── END SYNTAX VALIDATION ─────────────────────────────────────

                # ── DISK VERIFICATION + CONDITIONAL APPEND ────────────────────
                if not os.path.isfile(full_path):
                    err_msg = f"File not found on disk after write: {rel_path}"
                    print(f"   ❌ {err_msg}")
                    errors.append(err_msg)
                elif not syntax_ok:
                    print(f"   ⚠ [SKIPPED] {rel_path} — syntax broken, not added to files_written")
                else:
                    files_written.append(rel_path)
                    shared_context.append({"file": path, "code": content_resp})
                    print(f"   [FILE WRITTEN] {rel_path}")
                # ── END DISK VERIFICATION ─────────────────────────────────────
            except Exception as e:
                err_msg = f"Failed to write {rel_path}: {e}"
                print(f"   ❌ Tool error: {err_msg}")
                errors.append(err_msg)

    # ── FINAL COMPLETENESS CHECK ──────────────────────────────────────────
    planned_paths = []
    for f_info in files:
        p = f_info.get("path") if isinstance(f_info, dict) else f_info
        if p:
            planned_paths.append(p)
    written_set = set(os.path.normpath(w).replace("\\", "/") for w in files_written)
    for pp in planned_paths:
        norm_pp = os.path.normpath(pp).replace("\\", "/")
        if norm_pp not in written_set:
            err_msg = f"Planned file not written: {pp}"
            if err_msg not in errors:
                errors.append(err_msg)
                print(f"   ❌ {err_msg}")
    # ── END COMPLETENESS CHECK ────────────────────────────────────────────

    # ── IMPORT VALIDATION: check local imports resolve ────────────────────
    import_warnings = []
    # Build set of module names available in the workspace
    available_modules = set()
    for fw in files_written:
        if fw.endswith(".py"):
            # "src/utils.py" → module names: "src.utils", "utils"
            mod_path = fw.replace("/", ".").replace("\\", ".")[:-3]  # strip .py
            available_modules.add(mod_path)
            # Also add just the basename (e.g., "utils")
            basename_mod = os.path.splitext(os.path.basename(fw))[0]
            available_modules.add(basename_mod)

    stdlib_top_level = {
        "os", "sys", "json", "re", "math", "time", "datetime", "collections",
        "itertools", "functools", "pathlib", "typing", "abc", "io", "copy",
        "hashlib", "random", "string", "subprocess", "threading", "logging",
        "argparse", "unittest", "dataclasses", "enum", "csv", "sqlite3",
        "http", "urllib", "shutil", "tempfile", "glob", "textwrap", "traceback",
        "inspect", "ast", "dis", "struct", "socket", "ssl", "email",
        "html", "xml", "pdb", "profile", "pprint", "decimal", "fractions",
        "statistics", "secrets", "contextlib", "operator", "bisect", "heapq",
        "array", "queue", "multiprocessing", "concurrent", "asyncio",
        "signal", "mmap", "ctypes", "platform", "webbrowser", "base64",
        "binascii", "codecs", "configparser", "difflib", "fileinput",
        "fnmatch", "getpass", "gettext", "locale", "pickle", "shelve",
        "marshal", "dbm", "gzip", "bz2", "lzma", "zipfile", "tarfile",
        "zlib", "select", "selectors", "pty", "fcntl", "termios", "tty",
        "cgi", "cgitb", "wsgiref", "xmlrpc", "ipaddress", "uuid",
        "warnings", "weakref", "types", "importlib", "pkgutil", "site",
    }

    for fw in files_written:
        if not fw.endswith(".py"):
            continue
        fw_full = os.path.join(workspace_dir, fw)
        try:
            with open(fw_full, "r", encoding="utf-8") as rf:
                tree = ast.parse(rf.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    top_module = node.module.split(".")[0]
                    if (top_module not in available_modules
                            and top_module not in stdlib_top_level
                            and top_module not in (d.lower().replace("-", "_") for d in deps)):
                        import_warnings.append(
                            f"{fw}: unresolved local import 'from {node.module} import ...'"
                        )
        except Exception:
            pass  # file may have been skipped due to syntax errors

    if import_warnings:
        print(f"   ⚠ Import warnings ({len(import_warnings)}):")
        for iw in import_warnings[:5]:
            print(f"      {iw}")
    # ── END IMPORT VALIDATION ─────────────────────────────────────────────

    if errors:
        print(f"   ⚠ Builder #{variant_id} completed with {len(errors)} error(s) ({len(files_written)} files OK)")
    else:
        print(f"   ✅ Builder #{variant_id} done ({len(files_written)} files)")
    return {"files_written": files_written, "errors": errors, "import_warnings": import_warnings}


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
