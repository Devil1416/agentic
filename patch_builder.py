import sys
import re

with open(r"d:\n1ggaman\agentic\agents\builder.py", "r", encoding="utf-8") as f:
    content = f.read()

new_builder = """def run_builder(plan: dict, workspace_dir: str, variant_id: int = 1, status_cb=None) -> dict:
    files = plan.get("files", [])
    deps = plan.get("dependencies", [])
    language = plan.get("language", "python")

    files_written = []
    errors = []

    print(f"\\n{'=' * 60}")
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
'''

        response = call_model(
            role="builder",
            prompt=prompt,
            system_prompt="You are an expert software engineer. Output ONLY raw source code for the requested file. No explanations.",
            temperature=0.2,
        )

        content_resp = response.strip()
        if content_resp.startswith("```"):
            lines = content_resp.split("\\n")
            if len(lines) > 1 and lines[0].startswith("```"):
                lines = lines[1:]
            if len(lines) > 0 and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content_resp = "\\n".join(lines).strip()

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
"""

content = re.sub(r'def run_builder\(.*?\) -> dict:.*?(?=\Z)', new_builder, content, flags=re.DOTALL)

with open(r"d:\n1ggaman\agentic\agents\builder.py", "w", encoding="utf-8") as f:
    f.write(content)
