"""Validate all CLI subsystems."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("CLI UPGRADE — Validation")
print("=" * 50)

# 1. Command parser
from utils.command_parser import parse_input, get_help_text

r1 = parse_input("/exit")
assert r1["type"] == "command" and r1["command"] == "/exit"
r2 = parse_input("/show main.py")
assert r2["type"] == "command" and r2["args"] == ["main.py"]
r3 = parse_input("build me a REST API")
assert r3["type"] == "message"
r4 = parse_input("")
assert r4["type"] == "empty"
r5 = parse_input("/quit")
assert r5["command"] == "/exit"  # alias
print("[PASS] command_parser")

# 2. Help text
help_text = get_help_text()
assert "/exit" in help_text
assert "/run" in help_text
print("[PASS] help text")

# 3. Session manager
from session.session_manager import SessionManager
sm = SessionManager("test_validation")
sm.reset()
sm.add_message("user", "hello")
sm.add_message("assistant", "hi there")
sm.set_goal("test goal")
sm.set_mode("execute")
assert len(sm.state["conversation"]) == 2
assert sm.state["current_goal"] == "test goal"
ctx = sm.get_conversation_context()
assert "hello" in ctx
status = sm.get_status()
assert "test goal" in status
sm.reset()
assert sm.state["current_goal"] is None
# Cleanup
os.remove(sm.session_file)
print("[PASS] session_manager")

# 4. Conversation agent (import only - don't call model)
from agents.conversation_agent import classify_intent, brainstorm, _quick_classify

# Test quick classification
q1 = _quick_classify("build me a REST API")
assert q1 and q1["mode"] == "EXECUTE", f"Got: {q1}"
q2 = _quick_classify("fix the error in main.py")
assert q2 and q2["mode"] == "DEBUG", f"Got: {q2}"
q3 = _quick_classify("show me the files")
assert q3 and q3["mode"] == "SHOW", f"Got: {q3}"
q4 = _quick_classify("create a todo app")
assert q4 and q4["mode"] == "EXECUTE", f"Got: {q4}"
q5 = _quick_classify("let's think about approaches")
assert q5 is None  # should go to model for nuanced discussion
q6 = _quick_classify("it's not working")
assert q6 and q6["mode"] == "DEBUG", f"Got: {q6}"
print("[PASS] conversation_agent quick_classify")

# 5. CLI import
from cli import CLI
print("[PASS] cli importable")

print()
print("=" * 50)
print("ALL CLI CHECKS PASSED [OK]")
print("=" * 50)
print()
print("To run: python cli.py")
