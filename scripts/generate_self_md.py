# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
import os
import ast
import json

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "82b945d7de75",
}
# ─── /fingerprint ───────────────────────────────────────────


def generate_self_md():


    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    self_md_path = os.path.join(root_dir, "NIGGATIVITY_SELF.md")
    
    # 1. Architecture
    architecture = []
    py_files = []
    for dirpath, dirs, files in os.walk(root_dir):
        if any(ignored in dirpath for ignored in ["node_modules", ".git", "__pycache__", "venv", ".venv", "workspace", "session", "logs", "codebase", "ui"]):
            continue
        for f in files:
            if f.endswith('.py') and not f.startswith('test_'):
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                py_files.append((rel_path, full_path))

    for rel_path, full_path in sorted(py_files):
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            role = docstring.split("\n")[0] if docstring else "No description available."
            architecture.append(f"- **{rel_path}**: {role}")
        except Exception:
            architecture.append(f"- **{rel_path}**: Unparseable")

    # 2. Capabilities
    capabilities = [
        "- **Agents**: Planner, Builder, Debugger, Judge, Refiner, Conversation Agent",
        "- **Tools**: read_file, write_file, edit_file_diff, list_files, run_python, run_node, run_command, auto_detect_and_run, install_dependencies, analyze_image, git_init, git_commit, git_rollback",
        "- **Commands**: /help, /exit, /status, /history, /plan, /files, /show, /open, /memory, /reset, /run, /improve, /capabilities, /limitations"
    ]

    # Generate MD
    md_content = f"""# NIGGATIVITY SYSTEM KNOWLEDGE

## System Overview
Niggativity is a local-first autonomous coding assistant powered by Ollama. It features a conversational CLI, full-stack application building capabilities, deterministic self-healing loops, and an execution environment.

## Current Capabilities
{chr(10).join(capabilities)}

## Architecture
{chr(10).join(architecture)}

## Known Limitations

## Improvement History
"""

    with open(self_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Generated NIGGATIVITY_SELF.md")

if __name__ == "__main__":
    generate_self_md()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
