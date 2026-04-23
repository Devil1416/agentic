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
    """
    Generate code files based on the plan.

    Args:
        plan: Parsed plan from the planner.
        workspace_dir: Target directory for code generation.
        variant_id: Builder variant number (1 or 2).
        status_cb: Optional callback for progress updates.

    Returns:
        Summary dict with files_written and any errors.
    """
    tools_desc = get_tools_description()
    system = BUILDER_SYSTEM.format(tools=tools_desc)

    files = plan.get("files", [])
    existing_files = plan.get("existing_files_to_modify", [])
    deps = plan.get("dependencies", [])
    entrypoint = plan.get("entrypoint", "main.py")
    language = plan.get("language", "python")

    plan_summary = json.dumps({
        "files_to_create": files,
        "files_to_modify": existing_files,
        "dependencies": deps,
        "entrypoint": entrypoint,
        "language": language,
        "description": plan.get("description", ""),
        "architecture": plan.get("architecture", ""),
    }, indent=2)

    # Fetch contents of existing files to provide context to the builder
    existing_contents = ""
    for ef in existing_files:
        path = ef.get("path", "")
        full_path = os.path.join(workspace_dir, path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                existing_contents += f"\n--- EXISTING FILE: {path} ---\n```\n{content}\n```\n"
            except Exception:
                pass

    prompt = f"""Build Variant #{variant_id}

Project Plan:
{plan_summary}

Workspace directory: {workspace_dir}

{existing_contents}

Execute the plan. Use `write_file` for new files and `edit_file_diff` for existing files.
File paths should be relative to the workspace: {workspace_dir}/path/to/file

Begin processing files now. Start with the first file."""

    print(f"\n{'=' * 60}")
    print(f"🔨 BUILDER #{variant_id} — Generating code...")
    print(f"{'=' * 60}")

    files_written = []
    errors = []
    conversation = [prompt]

    for round_num in range(MAX_TOOL_ROUNDS):
        current_prompt = "\n\n---\n\n".join(conversation[-3:])  # Keep context window manageable

        response = call_model(
            role="builder",
            prompt=current_prompt,
            system_prompt=system,
            temperature=0.2,
        )

        # Parse tool calls from response
        calls = parse_tool_calls(response)

        if not calls:
            # No valid tool calls — check if builder is done
            if "done" in response.lower() or round_num > len(files) + 2:
                print(f"   Builder #{variant_id} finished ({len(files_written)} files)")
                break
            # Nudge the model
            conversation.append(response)
            conversation.append(
                "Please output a valid JSON tool call. Use write_file to write the next file, "
                "or {\"action\": \"done\", \"args\": {\"result\": \"complete\"}} if finished."
            )
            continue

        for call in calls:
            if call["action"] == "done":
                print(f"   ✅ Builder #{variant_id} done ({len(files_written)} files)")
                return {"files_written": files_written, "errors": errors}

            # Fix relative paths
            if call["action"] in ("write_file", "edit_file_diff") and "path" in call.get("args", {}):
                call["args"]["path"] = _normalize_workspace_path(call["args"]["path"], workspace_dir)

            result = execute_tool(call)

            if result.get("success"):
                action = call.get("action")
                if action in ("write_file", "edit_file_diff"):
                    try:
                        p = call.get("args", {}).get("path", "unknown")
                        rel_path = os.path.relpath(p, workspace_dir)
                        if status_cb:
                            status_cb(f"[FILE UPDATED] {rel_path}")
                        else:
                            print(f"   [FILE UPDATED] {rel_path}")
                        files_written.append(rel_path)
                    except Exception:
                        pass
                
                conversation.append(f"Tool {call['action']} executed successfully.")
            else:
                err_msg = result.get("error", "Unknown error")
                print(f"   ❌ Tool error: {err_msg}")
                errors.append(err_msg)
                conversation.append(f"Tool {call['action']} failed: {err_msg}")

    return {"files_written": files_written, "errors": errors}
