#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                            ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
cli.py — Interactive conversational CLI for reflexion.

Run: python cli.py

Provides a persistent, conversational coding assistant experience.
Supports slash commands and natural language input.
"""

import sys
import os
import io
import time

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
"integrity": "04b45e93a8f3",
}
# ─── /fingerprint ───────────────────────────────────────────


# Fix Windows terminal encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root is on path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from utils.command_parser import parse_input, get_help_text
from session.session_manager import SessionManager
from agents.conversation_agent import classify_intent, brainstorm, chat_respond, ask_clarification
from memory.vector_store import search_memory, get_relevant_context
from tools.fs import read_file, list_files
from model_router import get_installed_models, pick_model
import threading
import shutil as _shutil

WORKSPACE_BASE = os.path.join(ROOT, "workspace")

# ─── ANSI Live Progress Display ────────────────────────────────────────────────

_ANSI_UP   = "\033[{}A"
_ANSI_CLEAR = "\033[2K\r"
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_GREEN = "\033[32m"
_CYAN  = "\033[36m"
_YELLOW = "\033[33m"
_BLUE  = "\033[34m"
_MAGENTA = "\033[35m"
_RED   = "\033[31m"


def _bar(pct: float, width: int = 24) -> str:


    filled = int(width * pct)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return f"[{bar}] {int(pct * 100):3d}%"


_SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]


class LiveProgress:
    """
    In-place ANSI progress display — exactly 8 fixed lines, redrawn on every
    status_cb call using \\033[nA + \\033[2K so it never floods the terminal.
    All output via sys.stdout.write(); no print() inside the block.
    """

    PHASES = ["Planning", "Building", "Executing", "Judging", "Debugging", "Refining"]
    PHASE_KEYWORDS = {
        "planner":        "Planning",
        "plan":           "Planning",
        "[planner]":      "Planning",
        "[orchestrator]": "Planning",
        "contract":       "Planning",
        "builder":        "Building",
        "[builder]":      "Building",
        "build":          "Building",
        "file updated":   "Building",
        "[file updated]": "Building",
        "creating file":  "Building",
        "executor":       "Executing",
        "[executor]":     "Executing",
        "executing":      "Executing",
        "judge":          "Judging",
        "[judge]":        "Judging",
        "evaluating":     "Judging",
        "debugger":       "Debugging",
        "[debugger]":     "Debugging",
        "debug":          "Debugging",
        "refiner":        "Refining",
        "[refiner]":      "Refining",
        "refine":         "Refining",
        "patching":       "Refining",
    }
    PHASE_COLORS = {
        "Planning":  _CYAN,
        "Building":  _BLUE,
        "Executing": _GREEN,
        "Judging":   _YELLOW,
        "Debugging": _MAGENTA,
        "Refining":  _CYAN,
    }

    BLOCK_LINES = 8  # strict fixed height

    def __init__(self, total_files: int = 0, max_iterations: int = 5):
        self._lock = threading.Lock()
        self.total_files = max(total_files, 1)
        self.max_iterations = max_iterations
        self.files_done = 0
        self.current_iteration = 1
        self.current_phase = "Planning"
        self.current_file = ""
        self.log: list[str] = []
        self._rendered = False
        self._active = True
        self._spin_idx = 0

    def _detect_phase(self, msg: str) -> str:
        lower = msg.lower()
        for keyword, phase in self.PHASE_KEYWORDS.items():
            if keyword in lower:
                return phase
        return self.current_phase

    def _extract_meta(self, msg: str) -> str:
        """Parse iteration counter and current filename from a status message."""
        import re
        m = re.search(r'(?:creating file|file updated)[:\s]+([^\s\r\n]+)', msg, re.IGNORECASE)
        if m:
            self.current_file = m.group(1).strip()
        m2 = re.search(r'(?:iteration)\s+(\d+)(?:\s*/\s*(\d+))?', msg, re.IGNORECASE)
        if m2:
            self.current_iteration = int(m2.group(1))
            if m2.group(2):
                self.max_iterations = int(m2.group(2))
        return self.current_file

    def update(self, msg: str):
        """Called by status_cb on every agent status message."""
        with self._lock:
            if not self._active:
                return
            self.current_phase = self._detect_phase(msg)
            self._extract_meta(msg)
            lower = msg.lower()
            if any(k in lower for k in ("file updated", "[file updated]", "creating file", "files_written")):
                self.files_done = min(self.files_done + 1, self.total_files)
            self.log.append(msg.strip())
            if len(self.log) > 50:
                self.log = self.log[-50:]
            self._spin_idx = (self._spin_idx + 1) % len(_SPINNER_FRAMES)
            self._redraw()

    def _redraw(self):
        """Erase exactly BLOCK_LINES lines upward and redraw the block."""
        tw = max(_shutil.get_terminal_size((80, 24)).columns - 2, 40)

        if self._rendered:
            # move cursor up BLOCK_LINES rows
            sys.stdout.write(f"\033[{self.BLOCK_LINES}A")

        spinner = _SPINNER_FRAMES[self._spin_idx]
        phase_color = self.PHASE_COLORS.get(self.current_phase, _CYAN)
        pct = self.files_done / self.total_files
        bar = _bar(pct, width=min(24, tw - 20))

        # Build exactly BLOCK_LINES lines
        lines = []

        # line 1 — top border
        lines.append(f"{_BOLD}{_CYAN}\u250c{'\u2500' * (tw - 2)}\u2510{_RESET}")

        # line 2 — phase + spinner + iteration
        spin_str = f"{phase_color}{spinner}{_RESET}"
        phase_str = f"{phase_color}{_BOLD}{self.current_phase:<12}{_RESET}"
        iter_str = f"{_YELLOW}{self.current_iteration}/{self.max_iterations}{_RESET}"
        lines.append(f"{_CYAN}\u2502{_RESET}  {spin_str} {phase_str}  Iter: {iter_str}")

        # line 3 — progress bar + current file
        file_label = f"{_DIM}{self.current_file[:tw - 40]}{_RESET}" if self.current_file else ""
        lines.append(f"{_CYAN}\u2502{_RESET}  {_GREEN}{bar}{_RESET}  {file_label}")

        # line 4 — phase pills
        pills = ""
        for ph in self.PHASES:
            col = self.PHASE_COLORS.get(ph, _CYAN) if ph == self.current_phase else _DIM
            dot = "\u25cf" if ph == self.current_phase else "\u25cb"
            pills += f" {col}{dot} {ph}{_RESET}"
        lines.append(f"{_CYAN}\u2502{_RESET}{pills}")

        # line 5 — separator
        lines.append(f"{_CYAN}\u2502{_RESET}  {_DIM}{'\u2500' * (tw - 4)}{_RESET}")

        # lines 6-7 — last 2 log entries
        recent = self.log[-2:]
        for i in range(2):
            if i < len(recent):
                entry = recent[i].replace("\r", "").replace("\n", " ")[:tw - 6]
                lines.append(f"{_CYAN}\u2502{_RESET}  {_DIM}{entry}{_RESET}")
            else:
                lines.append(f"{_CYAN}\u2502{_RESET}")

        # line 8 — bottom border
        lines.append(f"{_BOLD}{_CYAN}\u2514{'\u2500' * (tw - 2)}\u2518{_RESET}")

        # Ensure exactly BLOCK_LINES lines
        lines = lines[:self.BLOCK_LINES]
        while len(lines) < self.BLOCK_LINES:
            lines.append("")

        for line in lines:
            sys.stdout.write(f"\033[2K\r{line}\n")
        sys.stdout.flush()
        self._rendered = True

    def start(self):
        """Reserve BLOCK_LINES blank lines then draw first frame."""
        with self._lock:
            sys.stdout.write("\n" * self.BLOCK_LINES)
            sys.stdout.flush()
            self._rendered = False
            self._redraw()

    def finish(self):
        """Mark complete; leave the block visible."""
        with self._lock:
            self._active = False

# ──────────────────────────────────────────────────────────────────────────────


def should_inject_self_context(user_input: str, intent: str, self_improvement_mode: bool) -> bool:
    if not self_improvement_mode or intent == "EXECUTE":
        return False
    lower_input = user_input.lower()
    if any(k in lower_input for k in ["what can you do", "capabilities", "features"]) or \
       (intent == "DISCUSS" and any(k in lower_input for k in ["reflexion", "system", "agent", "how do you work"])):
        return True
    return False

def print_banner():
    print(r"""
 +---------------------------------------------------------+
 |                                                         |
 |  _   _ ___ ____ ____    _  _____ _____     _____ _____  |
 | | \ | |_ _/ ___|/ ___|  / \|_   _|_ _\ \   / /_ _|_   _|\ \ / /|
 | |  \| || | |  _| |  _  / _ \ | |  | | \ \ / / | |  | |  \   / |
 | | |\  || | |_| | |_| |/ ___ \| |  | |  \ V /  | |  | |   | |  |
 | |_| \_|___\____|\____/_/   \_\_| |___|  \_/  |___| |_|   |_|  |
 |                                                         |
 |        Local-First Autonomous Coding Agent              |
 |        Powered by Ollama - Your AI Dev Partner          |
 |                                                         |
 +---------------------------------------------------------+
""")


def print_welcome(session: SessionManager):
    """Print contextual welcome message."""
    goal = session.state.get("current_goal")
    workspace = session.state.get("workspace_dir")
    msg_count = len(session.state.get("conversation", []))

    if msg_count > 0 and goal:
        print(f"  Welcome back! Resuming session.")
        print(f"  Current goal: {goal}")
        if workspace:
            print(f"  Workspace: {workspace}")
    else:
        print("  Hey! I'm your local coding partner.")
        print("  Tell me what you want to build, or just chat.")
    print()
    print("  Type /help for commands, or just talk to me.")
    print()


class CLI:
    """Main interactive CLI loop."""

    def __init__(self):
        self.session = SessionManager()
        self.running = True
        self._tools_initialized = False
        self.last_workspace: str | None = None  # updated after every successful build
        self.self_improvement_mode = False
        self.self_context = ""
        self._load_self_context()

    def _load_self_context(self):
        md_path = os.path.join(ROOT, "REFLEXION_SELF.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                self.self_context = f.read()

    def _ensure_tools(self):
        """Lazy-init the tool registry."""
        if self._tools_initialized:
            return
        from orchestrator import init_tools
        init_tools()
        self._tools_initialized = True

    def _get_workspace(self) -> str:
        """Get or create the current workspace directory."""
        ws = self.session.state.get("workspace_dir")
        if ws and os.path.isdir(ws):
            return ws
        ws = os.path.join(WORKSPACE_BASE, f"project_{int(time.time())}")
        os.makedirs(ws, exist_ok=True)
        self.session.set_workspace(ws)
        return ws

    def run(self):
        """Main loop."""
        print_banner()

        # Quick system check
        models = get_installed_models()
        if not models:
            print("  [!] Cannot reach Ollama. Make sure it's running: ollama serve")
            print("  [!] Then install a model: ollama pull llama3:8b")
            return
        print(f"  [{len(models)} models ready]")

        print_welcome(self.session)

        while self.running:
            try:
                user_input = input("\033[1;36myou>\033[0m ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Bye!\n")
                break

            if not user_input:
                continue

            parsed = parse_input(user_input)

            if parsed["type"] == "command":
                self._handle_command(parsed)
            elif parsed["type"] == "message":
                self._handle_message(user_input)

        self.session.save()

    def _handle_command(self, parsed: dict):
        """Handle slash commands."""
        cmd = parsed["command"]
        args = parsed["args"]

        if cmd == "/exit":
            print("\n  Bye! Session saved.\n")
            self.running = False

        elif cmd == "/help":
            print(get_help_text())

        elif cmd == "/status":
            print(f"\n{self.session.get_status()}\n")

        elif cmd == "/history":
            print(f"\n{self.session.get_history()}\n")

        elif cmd == "/plan":
            self._show_plan()

        elif cmd == "/files":
            self._show_files()

        elif cmd == "/show":
            self._show_file(args)

        elif cmd == "/open":
            self._show_file(args)

        elif cmd == "/image":
            self._handle_image_command(args)

        elif cmd == "/memory":
            self._show_memory()

        elif cmd == "/reset":
            self.session.reset()
            print("\n  Session reset. Fresh start!\n")

        elif cmd == "/run":
            self._force_execute()

        elif cmd == "/improve":
            self.self_improvement_mode = True
            goal = " ".join(args)
            if not goal:
                goal = "Improve the system."
            core_files = [
                "cli.py", "orchestrator.py", "model_router.py",
                "agents/planner.py", "agents/builder.py", "agents/judge.py",
                "tools/executor.py", "agents/conversation_agent.py"
            ]
            plan = {
                "project_name": "Reflexion Self-Improvement",
                "language": "python",
                "entrypoint": "cli.py",
                "files": [{"path": f, "purpose": "System core file"} for f in core_files],
                "dependencies": []
            }
            self.session.set_plan(plan)
            print("\n  [SELF] Entering Self-Improvement Mode.\n")
            self._run_orchestrator(goal, override_workspace=ROOT, is_self_improve=True)
            
        elif cmd == "/capabilities":
            if self.self_context:
                import re
                cap = re.search(r'## Current Capabilities\n(.*?)(?=\n##|$)', self.self_context, re.DOTALL)
                hist = re.search(r'## Improvement History\n(.*?)(?=\n##|$)', self.self_context, re.DOTALL)
                print("\nCurrent Capabilities:")
                print(cap.group(1).strip() if cap else "None")
                print("\nImprovement History:")
                print(hist.group(1).strip() if hist else "None\n")
            else:
                print("\n  [SELF] REFLEXION_SELF.md not found.\n")
                
        elif cmd == "/limitations":
            if self.self_context:
                import re
                lim = re.search(r'## Known Limitations\n(.*?)(?=\n##|$)', self.self_context, re.DOTALL)
                print("\nKnown Limitations:")
                print(lim.group(1).strip() if lim else "None\n")
            else:
                print("\n  [SELF] REFLEXION_SELF.md not found.\n")

        else:
            print(f"\n  Unknown command: {cmd}")
            print(f"  Type /help for available commands.\n")

    def _handle_message(self, user_input: str):
        """Handle natural language input through the conversation agent."""
        # Fix 4: strip leading semicolons / shell artefacts
        user_input = user_input.lstrip(";: ").strip()
        if not user_input:
            return

        self.session.add_message("user", user_input)

        # Get conversation context
        context = self.session.get_conversation_context(last_n=8)
        current_goal = self.session.state.get("current_goal")
        current_mode = self.session.state.get("mode", "discuss")

        # Classify intent
        result = None
        try:
            result = classify_intent(
                user_input,
                conversation_context=context,
                current_goal=current_goal,
                current_mode=current_mode,
                last_project_path=self.last_workspace,
                self_improvement_mode=self.self_improvement_mode,
            )
        except Exception as e:
            print(f"\n  [error] Intent classification failed: {e}")
            # Fix 3: default to EXECUTE so we always try to run the planner
            print("  Defaulting to EXECUTE mode...\n")
            result = {"mode": "EXECUTE", "goal": user_input, "response": ""}

        if result is None:
            result = {"mode": "EXECUTE", "goal": user_input, "response": ""}

        mode = result.get("mode", "EXECUTE").upper()
        response = result.get("response", "")

        if self.self_context:
            if should_inject_self_context(user_input, mode, self.self_improvement_mode):
                print("  [SELF] context injected")
                context += "\n\n[SYSTEM SELF-CONTEXT]\n" + self.self_context
            else:
                print("  [SELF] context skipped")

        lower_input = user_input.lower()
        if lower_input in ["run", "start", "test run", "execute it", "launch it"] and self.last_workspace:
            print(f"\n  [EXECUTOR] Directly running existing workspace: {self.last_workspace}")
            from tools.executor import run_python, _detect_entrypoint
            detected_entrypoint = _detect_entrypoint(self.last_workspace) or "main.py"
            result_out = run_python(self.last_workspace, detected_entrypoint, timeout=30)
            print(f"\n{result_out}\n")
            self.session.add_message("assistant", f"Ran existing project. Output:\n{result_out}")
            return

        if any(keyword in lower_input for keyword in ["build", "create", "implement", "fix", "run"]):
            mode = "EXECUTE"
            if "goal" not in result:
                result["goal"] = user_input

        if mode == "CHAT":
            self._handle_chat(user_input, response, context)

        elif mode == "DISCUSS":
            self._handle_discuss(user_input, response, context)

        elif mode == "EXECUTE":
            goal = result.get("goal", user_input)
            self._handle_execute(goal, response)

        elif mode == "DEBUG":
            goal = result.get("goal", user_input)
            self._handle_debug(goal, response)

        elif mode == "PLAN":
            goal = result.get("goal", user_input)
            self._handle_plan_mode(goal, response)

        elif mode == "SHOW":
            target = result.get("target", "all")
            self._handle_show(target, response)

        else:
            self._handle_discuss(user_input, response, context)

    # ─── MODE HANDLERS ────────────────────────────────

    def _handle_chat(self, user_input: str, response: str, context: str):
        """Handle lightweight casual chat."""
        self.session.set_mode("chat")

        if response and len(response) > 10:
            print(f"\n  {response}\n")
            self.session.add_message("assistant", response)
        else:
            full = chat_respond(user_input, context)
            print()
            self.session.add_message("assistant", full)

    def _handle_discuss(self, user_input: str, response: str, context: str):
        """Handle brainstorm/discussion mode."""
        self.session.set_mode("discuss")

        if response and len(response) > 20:
            # Use pre-generated response
            print(f"\n  {response}\n")
            self.session.add_message("assistant", response)
        else:
            # Generate a streaming brainstorm response
            print()
            print("  ", end="")
            full = brainstorm(user_input, context)
            print()
            self.session.add_message("assistant", full)

    def _handle_execute(self, goal: str, response: str):
        """Handle execution mode with human-in-the-loop confirmation."""
        self.session.set_goal(goal)
        self.session.set_mode("execute")

        if response:
            print(f"\n  {response}")

        print(f"\n  Goal: {goal}")
        print()

        # Human-in-the-loop confirmation
        try:
            confirm = input("  Proceed? (y/n/plan) > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.\n")
            return

        if confirm in ("n", "no"):
            print("  Cancelled. Tell me more about what you want.\n")
            self.session.add_message("assistant", f"Cancelled execution of: {goal}")
            return
        elif confirm in ("plan", "p"):
            self._handle_plan_mode(goal, "")
            return
        # Fix 5: anything other than n/no/plan/p is treated as confirmation

        # Execute
        self.session.add_message("assistant", f"Executing: {goal}")
        self._run_orchestrator(goal)

    def _handle_debug(self, goal: str, response: str):
        """Handle debug mode."""
        self.session.set_mode("debug")

        if response:
            print(f"\n  {response}")

        workspace = self.session.state.get("workspace_dir")
        if not workspace or not os.path.isdir(workspace):
            print("\n  No active workspace to debug.")
            print("  Build something first, or tell me what project to look at.\n")
            return

        print(f"\n  Debugging workspace: {workspace}")
        self.session.add_message("assistant", f"Debugging: {goal}")

        self._ensure_tools()

        # Find entrypoint
        plan = self.session.state.get("current_plan", {})
        entrypoint = plan.get("entrypoint", "main.py")
        language = plan.get("language", "python")

        # Run and capture errors
        from tools.executor import run_python, run_node
        print(f"\n  [EXECUTOR] Running {entrypoint}...")

        if language in ("javascript", "node"):
            exec_result = run_node(workspace, entrypoint, timeout=30)
        else:
            exec_result = run_python(workspace, entrypoint, timeout=30)

        print(f"  {exec_result[:300]}")

        has_error = "error" in exec_result.lower() or "traceback" in exec_result.lower()

        if has_error:
            print("\n  [DEBUGGER] Analyzing errors...\n")
            from agents.debugger import run_debugger
            files = self._list_workspace_files(workspace)
            debug_result = run_debugger(exec_result, workspace, files)

            if debug_result.get("fixed"):
                print("\n  [DEBUGGER] Fix applied. Re-running...\n")
                if language in ("javascript", "node"):
                    rerun = run_node(workspace, entrypoint, timeout=30)
                else:
                    rerun = run_python(workspace, entrypoint, timeout=30)
                print(f"  {rerun[:300]}")
                self.session.add_message("assistant", f"Debug result: {debug_result.get('summary', 'Fixed')}")
            else:
                print(f"\n  [DEBUGGER] Could not auto-fix: {debug_result.get('summary', 'Unknown')}")
                self.session.add_message("assistant", f"Debug failed: {debug_result.get('summary', '')}")
        else:
            print("\n  Looks like it ran without errors!")
            self.session.add_message("assistant", "Code ran successfully, no errors detected.")

        print()

    def _handle_plan_mode(self, goal: str, response: str):
        """Handle plan-only mode."""
        self.improve_workspace = ROOT if getattr(self, 'self_improvement_mode', False) else None
        override_workspace = getattr(self, 'improve_workspace', None)
        self.session.set_goal(goal)
        self.session.set_mode("plan")

        if response:
            print(f"\n  {response}")

        print(f"\n  [PLANNER] Creating plan for: {goal}\n")

        self._ensure_tools()
        workspace = override_workspace if override_workspace else self._get_workspace()

        from agents.planner import run_planner
        plan = run_planner(goal, workspace)

        self.session.set_plan(plan)

        # Display plan
        if "files" in plan:
            print(f"\n  Project: {plan.get('project_name', 'unnamed')}")
            print(f"  Language: {plan.get('language', 'N/A')}")
            print(f"  Entry: {plan.get('entrypoint', 'N/A')}")
            print(f"  Files:")
            for f in plan.get("files", []):
                path = f.get("path", f) if isinstance(f, dict) else f
                purpose = f.get("purpose", "") if isinstance(f, dict) else ""
                print(f"    - {path}  {purpose}")
            deps = plan.get("dependencies", [])
            if deps:
                print(f"  Dependencies: {', '.join(deps)}")
            print()
            print("  Type /run to execute this plan, or tell me to adjust it.")
        else:
            print(f"\n  Raw plan output:")
            print(f"  {str(plan)[:500]}")

        self.session.add_message("assistant", f"Plan created for: {goal}")
        print()

    def _handle_show(self, target: str, response: str):
        """Handle file exploration."""
        workspace = self.session.state.get("workspace_dir")

        if not workspace or not os.path.isdir(workspace):
            print("\n  No workspace yet. Build something first!\n")
            return

        if target == "all" or not target:
            self._show_files()
        else:
            # Try to find the file
            filepath = os.path.join(workspace, target)
            if os.path.exists(filepath):
                self._display_file(filepath)
            else:
                # Search for partial match
                files = self._list_workspace_files(workspace)
                matches = [f for f in files if target in f]
                if matches:
                    for m in matches:
                        self._display_file(os.path.join(workspace, m))
                else:
                    print(f"\n  File not found: {target}")
                    self._show_files()

    # ─── COMMAND HANDLERS ────────────────────────────

    def _show_plan(self):
        """Display current plan."""
        plan = self.session.state.get("current_plan")
        if not plan:
            print("\n  No plan yet. Tell me what to build!\n")
            return

        print("\n  Current Plan:")
        print(f"  Project: {plan.get('project_name', 'unnamed')}")
        print(f"  Language: {plan.get('language', 'N/A')}")
        print(f"  Entry: {plan.get('entrypoint', 'N/A')}")
        for f in plan.get("files", []):
            path = f.get("path", f) if isinstance(f, dict) else f
            print(f"    - {path}")
        print()

    def _show_files(self):
        """List workspace files."""
        workspace = self.session.state.get("workspace_dir")
        if not workspace or not os.path.isdir(workspace):
            print("\n  No workspace yet.\n")
            return

        files = self._list_workspace_files(workspace)
        if not files:
            print("\n  Workspace is empty.\n")
            return

        print(f"\n  Workspace: {workspace}")
        for f in files:
            size = ""
            full = os.path.join(workspace, f)
            if os.path.isfile(full):
                size = f" ({os.path.getsize(full)} bytes)"
            print(f"    {f}{size}")
        print()

    def _show_file(self, args: list):
        """Show a specific file."""
        if not args:
            print("\n  Usage: /show <filename>\n")
            return

        target = " ".join(args)
        workspace = self.session.state.get("workspace_dir")

        if not workspace:
            print("\n  No workspace yet.\n")
            return

        filepath = os.path.join(workspace, target)
        if os.path.exists(filepath):
            self._display_file(filepath)
        elif os.path.exists(target):
            self._display_file(target)
        else:
            files = self._list_workspace_files(workspace)
            matches = [f for f in files if target in f]
            if matches:
                for m in matches:
                    self._display_file(os.path.join(workspace, m))
            else:
                print(f"\n  File not found: {target}\n")

    def _display_file(self, filepath: str):
        """Pretty-print a file's contents."""
        try:
            content = read_file(filepath)
            basename = os.path.basename(filepath)
            lines = content.split("\n")
            print(f"\n  --- {basename} ({len(lines)} lines) ---")
            for i, line in enumerate(lines, 1):
                print(f"  {i:4d} | {line}")
            print(f"  --- end {basename} ---\n")
        except Exception as e:
            print(f"\n  Error reading file: {e}\n")

    def _show_memory(self):
        """Display stored memories."""
        results = search_memory("", top_k=10)
        if not results:
            print("\n  No memories stored yet.\n")
            return

        print(f"\n  Stored Memories ({len(results)}):")
        for r in results:
            cat = r.get("category", "general")
            text = r["text"][:100]
            print(f"    [{cat}] {text}")
        print()

    def _force_execute(self):
        """Execute current plan without confirmation."""
        goal = self.session.state.get("current_goal")
        if not goal:
            print("\n  No goal set. Tell me what to build first.\n")
            return

        print(f"\n  Executing: {goal}\n")
        self.session.add_message("assistant", f"Force-executing: {goal}")
        self._run_orchestrator(goal)

    def _run_orchestrator(self, goal: str, override_workspace: str = None, is_self_improve: bool = False):
        """Run the full orchestration pipeline with live progress display."""
        self._ensure_tools()
        workspace = override_workspace if override_workspace else self._get_workspace()

        MAX_ITER = 5

        # Estimate file count from session plan (fallback=6)
        plan = self.session.state.get("current_plan", {})

        # Fix 2: guard against None plan before dereferencing
        if plan is None:
            print("[ERROR] Planner failed — no plan generated. Aborting execution.")
            return

        print(f"[DEBUG] Plan generated: {bool(plan)}")

        total_files = len(plan.get("files", [])) * 2 or 6  # x2 for 2 variants

        progress = LiveProgress(total_files=total_files, max_iterations=MAX_ITER)
        progress.start()

        def status_cb(msg: str):
            progress.update(msg)

        try:
            if is_self_improve:
                from orchestrator import execute_plan
                result = execute_plan(
                    plan,
                    goal,
                    workspace,
                    status_cb=status_cb,
                    max_iterations=MAX_ITER,
                    is_self_improve=True
                )
                if result and result.get("verdict", {}).get("verdict") == "accept":
                    md_path = os.path.join(ROOT, "REFLEXION_SELF.md")
                    with open(md_path, "a", encoding="utf-8") as f:
                        from datetime import datetime
                        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}]\nmodified: core files\nsummary: {goal}\n")
                    print("  [SELF] reflexion updated successfully")
                    self._load_self_context()
            else:
                from orchestrator import run as orchestrator_run
                result = orchestrator_run(
                    goal,
                    workspace_name=os.path.basename(workspace),
                    status_cb=status_cb,
                    max_iterations=MAX_ITER,
                )

            progress.finish()
            # Move past the progress block
            sys.stdout.write("\n")

            if result:
                verdict = result.get("verdict", {})
                self.session.set_mode("discuss")
                self.session.increment_iteration()

                # Update last_workspace so classify_intent stays current
                self.last_workspace = result.get("workspace", workspace)

                score = verdict.get("score", "?")
                v = verdict.get("verdict", "unknown")
                self.session.add_message(
                    "assistant",
                    f"Build complete. Verdict: {v} (score: {score}/10)"
                )

                # Update plan if we got one
                plan = self.session.state.get("current_plan")
                if not plan:
                    files = self._list_workspace_files(workspace)
                    if files:
                        self.session.set_plan({
                            "files": [{"path": f} for f in files],
                            "entrypoint": "main.py",
                            "language": "python",
                        })

                print(f"\n  Done! Score: {score}/10")
                print(f"  Verdict: {v}")
                print(f"  Type /files to see what was built, or /show <file> to view a file.\n")
            else:
                print("\n  Build completed (no result returned).\n")

        except KeyboardInterrupt:
            progress.finish()
            print("\n\n  Build interrupted.\n")
            self.session.add_message("assistant", "Build interrupted by user.")
        except Exception as e:
            progress.finish()
            print(f"\n  Build error: {e}\n")
            self.session.add_message("assistant", f"Build error: {e}")
            import traceback
            traceback.print_exc()

    def _handle_image_command(self, args: list):
        """Handle /image command for vision-based UI generation."""
        if not args:
            print("\n  Usage: /image <path_to_image> [description]")
            print("  Example: /image mockup.png build this dashboard UI\n")
            return

        image_path = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""

        # Resolve path
        if not os.path.isabs(image_path):
            workspace = self.session.state.get("workspace_dir", ".")
            image_path = os.path.join(workspace, image_path)

        if not os.path.exists(image_path):
            print(f"\n  Image not found: {image_path}\n")
            return

        self._ensure_tools()

        print(f"\n  [VISION] Analyzing image: {os.path.basename(image_path)}...")

        from tools.vision import analyze_image
        analysis = analyze_image(image_path)

        if analysis.startswith("ERROR"):
            print(f"  {analysis}\n")
            return

        print(f"\n  [VISION] Analysis complete.\n")
        print(f"  {analysis[:500]}")
        if len(analysis) > 500:
            print(f"  ... ({len(analysis)} chars total)")

        self.session.add_message("assistant", f"Image analysis: {analysis[:300]}")

        # If user wants to build from the image
        if description:
            goal = f"{description}\n\nUI Analysis from image:\n{analysis}"
            self._handle_execute(goal, "I'll build the UI based on the image analysis.")
        else:
            print("\n  Tell me what to do with this analysis.")
            print("  e.g., 'build this UI' or /run\n")
            self.session.set_goal(f"Build UI from image analysis:\n{analysis[:500]}")

    # ─── UTILS ────────────────────────────────────────

    def _list_workspace_files(self, workspace: str) -> list[str]:
        """List files in workspace."""
        files = []
        if os.path.isdir(workspace):
            for root, dirs, filenames in os.walk(workspace):
                dirs[:] = [d for d in dirs if not d.startswith('.')
                           and d not in ('node_modules', '__pycache__', '.git', 'venv')]
                for fn in filenames:
                    files.append(os.path.relpath(os.path.join(root, fn), workspace))
        return sorted(files)


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
