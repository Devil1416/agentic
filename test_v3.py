# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""Validate all v3 upgrade changes."""
import sys, os

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "a5c913e6d761",
}
# ─── /fingerprint ───────────────────────────────────────────

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("NIGGATIVITY v3 — Upgrade Validation")
print("=" * 50)

# 1. New tool imports
from tools.vision import analyze_image, _find_vision_model
print("[PASS] tools.vision importable")

from tools.git_tools import git_init, git_commit, git_rollback, git_log, git_diff
print("[PASS] tools.git_tools importable")

from tools.executor import auto_detect_and_run, install_dependencies, _detect_entrypoint, _detect_language
print("[PASS] executor new functions importable")

# 2. Model router with new roles
from model_router import ROLE_MODELS, pick_model
assert "chat" in ROLE_MODELS, "Missing chat role"
assert "vision" in ROLE_MODELS, "Missing vision role"
print("[PASS] model_router has chat + vision roles")

# 3. Conversation agent with CHAT mode
from agents.conversation_agent import classify_intent, brainstorm, chat_respond, _quick_classify

q1 = _quick_classify("hello!")
assert q1 and q1["mode"] == "CHAT", f"Expected CHAT, got: {q1}"
q2 = _quick_classify("thanks!")
assert q2 and q2["mode"] == "CHAT", f"Expected CHAT, got: {q2}"
q3 = _quick_classify("build me a REST API")
assert q3 and q3["mode"] == "EXECUTE", f"Expected EXECUTE, got: {q3}"
q4 = _quick_classify("not working")
assert q4 and q4["mode"] == "DEBUG", f"Expected DEBUG, got: {q4}"


q5 = _quick_classify("build this UI from this screenshot")
assert q5 and q5.get("needs_image"), f"Expected needs_image, got: {q5}"
print("[PASS] conversation_agent CHAT mode + image detection")

# 4. Session manager with new fields
from session.session_manager import SessionManager
sm = SessionManager("test_v3")
sm.reset()
sm.set_tech_stack({"frontend": "React", "backend": "FastAPI"})
sm.set_last_task("Build a todo app")
sm.update_file_structure(["main.py", "app.py"])
assert sm.state["tech_stack"]["frontend"] == "React"
assert sm.state["last_task"] == "Build a todo app"
assert len(sm.state["file_structure"]) == 2
status = sm.get_status()
assert "React" in status
assert "Build a todo app" in status
sm.reset()
os.remove(sm.session_file)
print("[PASS] session_manager new fields (tech_stack, last_task, file_structure)")

# 5. Planner with fullstack support
from agents.planner import PLANNER_SYSTEM
assert "frontend" in PLANNER_SYSTEM
assert "backend" in PLANNER_SYSTEM
assert "subtasks" in PLANNER_SYSTEM
print("[PASS] planner has fullstack + subtask support")

# 6. Orchestrator registers all new tools
from orchestrator import init_tools
from tool_registry import list_tools
init_tools()
tools = list_tools()
assert "analyze_image" in tools, f"Missing analyze_image, got: {tools}"
assert "git_init" in tools
assert "git_commit" in tools
assert "git_rollback" in tools
assert "auto_detect_and_run" in tools
assert "install_dependencies" in tools
print(f"[PASS] orchestrator registers {len(tools)} tools (includes new ones)")

# 7. Command parser with new commands
from utils.command_parser import COMMANDS, parse_input
assert "/open" in COMMANDS
assert "/image" in COMMANDS
r = parse_input("/open main.py")
assert r["command"] == "/open" and r["args"] == ["main.py"]
print("[PASS] command_parser has /open + /image")

# 8. Auto-detect entrypoint
os.makedirs("workspace/_test_detect", exist_ok=True)
with open("workspace/_test_detect/app.py", "w") as f:
    f.write("print('hello')")
ep = _detect_entrypoint("workspace/_test_detect")
assert ep == "app.py", f"Expected app.py, got: {ep}"
lang = _detect_language("workspace/_test_detect")
assert lang == "python"
os.remove("workspace/_test_detect/app.py")
os.rmdir("workspace/_test_detect")
print("[PASS] auto_detect_and_run entrypoint detection")

# 9. CLI import with all new features
from cli import CLI
print("[PASS] cli.py importable with all upgrades")

print()
print("=" * 50)
print("ALL V3 CHECKS PASSED [OK]")
print("=" * 50)
print()
print("To run: python cli.py")


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
