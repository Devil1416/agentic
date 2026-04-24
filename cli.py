#!/usr/bin/env python3
"""
cli.py — Interactive conversational CLI for niggativity.

Run: python cli.py

Provides a persistent, conversational coding assistant experience.
Supports slash commands and natural language input.
"""

import sys
import os
import io
import time

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

WORKSPACE_BASE = os.path.join(ROOT, "workspace")


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

        else:
            print(f"\n  Unknown command: {cmd}")
            print(f"  Type /help for available commands.\n")

    def _handle_message(self, user_input: str):
        """Handle natural language input through the conversation agent."""
        self.session.add_message("user", user_input)

        # Get conversation context
        context = self.session.get_conversation_context(last_n=8)
        current_goal = self.session.state.get("current_goal")
        current_mode = self.session.state.get("mode", "discuss")

        # Classify intent
        try:
            result = classify_intent(
                user_input,
                conversation_context=context,
                current_goal=current_goal,
                current_mode=current_mode,
            )
        except Exception as e:
            print(f"\n  [error] Intent classification failed: {e}")
            print("  Treating as discussion...\n")
            result = {"mode": "DISCUSS", "response": None}

        mode = result.get("mode", "DISCUSS").upper()
        response = result.get("response", "")

        lower_input = user_input.lower()
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
        self.session.set_goal(goal)
        self.session.set_mode("plan")

        if response:
            print(f"\n  {response}")

        print(f"\n  [PLANNER] Creating plan for: {goal}\n")

        self._ensure_tools()
        workspace = self._get_workspace()

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

    def _run_orchestrator(self, goal: str):
        """Run the full orchestration pipeline."""
        self._ensure_tools()
        workspace = self._get_workspace()

        print()
        print("  " + "=" * 56)
        print("  [NIGGATIVITY] Autonomous build starting...")
        print("  " + "=" * 56)
        print()

        try:
            from orchestrator import run as orchestrator_run
            result = orchestrator_run(goal, workspace_name=os.path.basename(workspace))

            if result:
                verdict = result.get("verdict", {})
                self.session.set_mode("discuss")
                self.session.increment_iteration()

                score = verdict.get("score", "?")
                v = verdict.get("verdict", "unknown")
                self.session.add_message(
                    "assistant",
                    f"Build complete. Verdict: {v} (score: {score}/10)"
                )

                # Update plan if we got one
                plan = self.session.state.get("current_plan")
                if not plan:
                    # Try to infer from workspace
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
            print("\n\n  Build interrupted.\n")
            self.session.add_message("assistant", "Build interrupted by user.")
        except Exception as e:
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
