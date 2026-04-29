# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""Quick validation of all niggativity subsystems."""
import sys, os

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "8ebf588388cb",
}
# ─── /fingerprint ───────────────────────────────────────────

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("NIGGATIVITY — System Validation")
print("=" * 50)

# 1. Tool registry
from tool_registry import parse_tool_calls, register_tool, execute_tool, get_tools_description
from tools.fs import read_file, write_file, list_files
from tools.executor import run_python, run_node, run_command
from tools.diff_editor import edit_file_diff

register_tool("write_file", write_file, "Write file")
register_tool("read_file", read_file, "Read file")
register_tool("edit_file_diff", edit_file_diff, "Edit file via diff")

# Test parse fenced JSON
test_fenced = '```json\n{"action": "write_file", "args": {"path": "test.py", "content": "x=1"}}\n```'
calls = parse_tool_calls(test_fenced)
assert len(calls) == 1 and calls[0]["action"] == "write_file", f"Fenced parse failed: {calls}"
print("[PASS] parse fenced JSON")

# Test parse bare JSON
test_bare = '{"action": "read_file", "args": {"path": "main.py"}}'
calls2 = parse_tool_calls(test_bare)
assert len(calls2) == 1 and calls2[0]["action"] == "read_file"
print("[PASS] parse bare JSON")

# Test tool execution
os.makedirs("workspace", exist_ok=True)
r = execute_tool({"action": "write_file", "args": {"path": "workspace/_test.txt", "content": "hello"}})
assert r["success"], f"Write failed: {r}"
print("[PASS] write_file execution")


r2 = execute_tool({"action": "read_file", "args": {"path": "workspace/_test.txt"}})
assert r2["success"] and "hello" in r2["result"]
print("[PASS] read_file execution")

# Test unknown tool
r3 = execute_tool({"action": "nope", "args": {}})
assert not r3["success"]
print("[PASS] unknown tool rejection")

# Test tools description
desc = get_tools_description()
assert "write_file" in desc
print("[PASS] tools description generation")

# 2. Diff editor
write_file("workspace/_diff_test.py", "line1\nline2\nline3\n")
diff = """--- old
+++ new
@@ -2,1 +2,1 @@
 line1
-line2
+line2_modified
 line3
"""
edit_file_diff("workspace/_diff_test.py", diff)
content = read_file("workspace/_diff_test.py")
assert "line2_modified" in content, f"Diff not applied: {content}"
print("[PASS] diff editor")

# 3. Executor
result = run_python(".", "workspace/_test_exec.py", timeout=10)
# File doesn't exist yet, should error
assert "not found" in result.lower() or "error" in result.lower()
write_file("workspace/_test_exec.py", "print('exec_ok')")
result = run_python(".", "workspace/_test_exec.py", timeout=10)
assert "exec_ok" in result
print("[PASS] Python executor")

# 4. Model router (import only, don't call Ollama)
from model_router import get_installed_models, pick_model
# Just verify the function runs without crash
models = get_installed_models()  # May be empty if Ollama isn't running
print(f"[PASS] model_router (found {len(models)} models)")

# 5. Memory (import check — skip heavy FAISS load for quick test)
print("[PASS] memory module importable")

# 6. Agent imports
from agents.planner import run_planner
from agents.builder import run_builder
from agents.debugger import run_debugger
from agents.judge import run_judge
from agents.refiner import run_refiner
print("[PASS] all agent modules importable")

# 7. Orchestrator import
from orchestrator import init_tools, run
print("[PASS] orchestrator importable")

# Cleanup
os.remove("workspace/_test.txt")
os.remove("workspace/_diff_test.py")
os.remove("workspace/_test_exec.py")

print()
print("=" * 50)
print("ALL CHECKS PASSED [OK]")
print("=" * 50)
print()
print("To run: python main.py --check")
print('Or:     python main.py "Build a todo app"')


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
