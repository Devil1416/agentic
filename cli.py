#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
cli.py — Reflexion CLI (Claude Code-compatible session UX)

Usage:
    python cli.py              # interactive chat
    python cli.py "build X"   # single task, then interactive
    python cli.py --resume     # resume latest session
    python cli.py --check      # system check only
"""
import io
import json
import os
import sys
import threading
import time

# Windows encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

_PROVENANCE = {
    "author": "Harsh Ashar",
    "github": "github.com/doriangraypng",
    "project": "Reflexion",
    "integrity": "cli_v2_parallel",
}

# ── ANSI colours ──────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
BLUE = "\033[34m"

# ── Spinner frames ────────────────────────────────────────────
_SPIN = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]


# ─── Helpers ─────────────────────────────────────────────────

def _print(msg: str, color: str = ""):
    print(f"{color}{msg}{R}" if color else msg)


def _banner():
    # Use simpler box chars if windows encoding is risky, but we have a fix at top.
    print(f"""
{BOLD}{MAGENTA}╔══════════════════════════════════════════════════════╗{R}
{BOLD}{MAGENTA}║{R}          {BOLD}{CYAN}⚡  R E F L E X I O N   v2.0{R}              {BOLD}{MAGENTA}║{R}
{BOLD}{MAGENTA}║{R}       {DIM}Local-First Autonomous Coding Agent{R}           {BOLD}{MAGENTA}║{R}
{BOLD}{MAGENTA}║{R}       {DIM}Powered by Ollama — Zero Cloud Deps{R}           {BOLD}{MAGENTA}║{R}
{BOLD}{MAGENTA}╚══════════════════════════════════════════════════════╝{R}
{DIM}  Type your goal or /help for commands{R}
""")


def _compact_status(msg: str, frame_idx: int = 0) -> str:
    spinner = _SPIN[frame_idx % len(_SPIN)]
    return f"  {CYAN}{spinner}{R} {DIM}{msg[:70]}{R}"


# ─── Live streaming print ─────────────────────────────────────

class StreamingPrinter:
    """Print tokens as they arrive, then finish with newline."""

    def __init__(self, prefix: str = ""):
        self._prefix_printed = False
        self._prefix = prefix
        self._buf = []

    def token(self, t: str):
        if not self._prefix_printed:
            sys.stdout.write(f"\n{GREEN}◆{R} {self._prefix}")
            self._prefix_printed = True
        sys.stdout.write(t)
        sys.stdout.flush()
        self._buf.append(t)

    def done(self) -> str:
        if self._prefix_printed:
            sys.stdout.write("\n")
        return "".join(self._buf)


# ─── Background build with live status ───────────────────────

class BackgroundBuild:
    def __init__(self):
        self._lines: list[str] = []
        self._done = False
        self._result = None
        self._error: str | None = None
        self._lock = threading.Lock()
        self._idx = 0

    def status_cb(self, msg: str):
        with self._lock:
            self._lines.append(msg)
            self._idx += 1
            # Overwrite single line
            clean = msg.strip()[:72]
            sys.stdout.write(f"\r{CYAN}{_SPIN[self._idx % len(_SPIN)]}{R} {DIM}{clean}{R}   \r")
            sys.stdout.flush()

    def run(self, goal: str, workspace: str, max_iter: int, parallel: bool):
        def _bg():
            try:
                from orchestrator import run as _run
                self._result = _run(
                    goal,
                    workspace_name=os.path.basename(workspace),
                    status_cb=self.status_cb,
                    max_iterations=max_iter,
                    parallel=parallel,
                )
            except Exception as exc:
                self._error = str(exc)
            finally:
                self._done = True

        t = threading.Thread(target=_bg, daemon=True)
        t.start()
        return t

    def wait_with_spinner(self, t: threading.Thread):
        i = 0
        while not self._done:
            time.sleep(0.12)
            i += 1
        t.join()
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()


# ─── Command handler ──────────────────────────────────────────

COMMANDS = {
    "/help":         "Show this help",
    "/status":       "Session state",
    "/history":      "Conversation log",
    "/plan":         "Current plan",
    "/files":        "List workspace files",
    "/show <file>":  "Print file contents",
    "/run":          "Execute current goal",
    "/think on|off": "Toggle thinking mode",
    "/auto on|off":  "Toggle auto-execute",
    "/parallel on|off": "Toggle parallel agents",
    "/models":       "List installed Ollama models",
    "/sessions":     "List saved sessions",
    "/resume <id>":  "Load a past session",
    "/new":          "Start a new session",
    "/reset":        "Clear current session history",
    "/clear":        "Clear terminal screen",
    "/improve":      "Self-improve mode",
    "/exit":         "Save & quit",
}


def _help():
    _print("\n  Commands:", BOLD)
    for cmd, desc in COMMANDS.items():
        print(f"    {CYAN}{cmd:<22}{R} {desc}")
    print()


class CLI:
    def __init__(self, session_id: str | None = None):
        from session.session_manager import SessionManager
        self.session = SessionManager(session_id=session_id)
        self._tools_ready = False
        self._parallel = os.getenv("REFLEXION_PARALLEL_AGENTS", "true").lower() == "true"
        self.last_workspace: str | None = None

    def _ensure_tools(self):
        if not self._tools_ready:
            from orchestrator import init_tools
            init_tools()
            self._tools_ready = True

    def _workspace(self) -> str:
        ws = self.session.state.get("workspace_dir")
        if not ws:
            ws = os.path.join(ROOT, "workspace", f"project_{int(time.time())}")
            os.makedirs(ws, exist_ok=True)
            self.session.set_workspace(ws)
        return ws

    # ── Commands ──────────────────────────────────────────────

    def _cmd_status(self):
        print(self.session.get_status())

    def _cmd_history(self):
        print(self.session.get_history(last_n=20))

    def _cmd_plan(self):
        plan = self.session.state.get("current_plan")
        if not plan:
            _print("  No plan yet.", DIM)
            return
        print(json.dumps(plan, indent=2)[:2000])

    def _cmd_files(self):
        ws = self.session.state.get("workspace_dir")
        if not ws or not os.path.isdir(ws):
            _print("  No workspace.", DIM)
            return
        _print(f"\n  Workspace: {ws}", DIM)
        for r, dirs, fnames in os.walk(ws):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git", "venv", ".variants")]
            for fn in fnames:
                rel = os.path.relpath(os.path.join(r, fn), ws).replace("\\", "/")
                size = os.path.getsize(os.path.join(r, fn))
                print(f"    {CYAN}{rel}{R}  {DIM}({size} bytes){R}")
        print()

    def _cmd_show(self, args: list[str]):
        if not args:
            _print("  Usage: /show <filename>", YELLOW)
            return
        ws = self._workspace()
        path = os.path.join(ws, args[0])
        if not os.path.isfile(path):
            _print(f"  File not found: {args[0]}", RED)
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        _print(f"\n  ── {args[0]} ──", CYAN)
        print(content[:3000])
        if len(content) > 3000:
            _print(f"  ... ({len(content)} chars total)", DIM)
        print()

    def _cmd_models(self):
        from model_router import get_installed_models, pick_model
        models = get_installed_models()
        if not models:
            _print("  No models found — is Ollama running?", RED)
            return
        _print(f"\n  {len(models)} model(s) installed:", BOLD)
        for m in models:
            print(f"    {GREEN}•{R} {m}")
        _print("\n  Role assignments:", BOLD)
        for role in ["planner", "builder", "debugger", "judge", "refiner", "chat"]:
            m = pick_model(role, models) or "(none)"
            print(f"    {CYAN}{role:<12}{R} → {m}")
        print()

    def _cmd_sessions(self):
        from session.session_manager import SessionManager
        sessions = SessionManager.list_sessions()
        if not sessions:
            _print("  No saved sessions.", DIM)
            return
        _print(f"\n  {len(sessions)} session(s):", BOLD)
        for s in sessions[:10]:
            active = " ◀ current" if s["session_id"] == self.session.session_id else ""
            print(f"    {CYAN}{s['session_id']}{R}  {s['title'][:40]}  {DIM}{s['last_active'][:10]}{R}{GREEN}{active}{R}")
        print()

    def _cmd_resume(self, args: list[str]):
        from session.session_manager import SessionManager
        if not args:
            _print("  Usage: /resume <session_id>", YELLOW)
            return
        sid = args[0]
        self.session = SessionManager(session_id=sid)
        _print(f"  Resumed: {sid}", GREEN)

    def _cmd_new(self):
        from session.session_manager import SessionManager
        self.session = SessionManager()
        _print(f"  New session: {self.session.session_id}", GREEN)

    def _cmd_reset(self):
        self.session.reset()
        _print("  Session cleared.", GREEN)

    def _cmd_clear(self):
        os.system("cls" if os.name == "nt" else "clear")
        _banner()

    def _cmd_think(self, args: list[str]):
        val = (args[0].lower() == "on") if args else not self.session.state.get("thinking_mode")
        self.session.set_setting("thinking_mode", val)
        _print(f"  Thinking mode: {'on' if val else 'off'}", CYAN)

    def _cmd_auto(self, args: list[str]):
        val = (args[0].lower() == "on") if args else not self.session.state.get("auto_execute")
        self.session.set_setting("auto_execute", val)
        _print(f"  Auto-execute: {'on' if val else 'off'}", CYAN)

    def _cmd_parallel(self, args: list[str]):
        val = (args[0].lower() == "on") if args else not self._parallel
        self._parallel = val
        _print(f"  Parallel agents: {'on' if val else 'off'}", CYAN)

    # ── Build pipeline ────────────────────────────────────────

    def _run_build(self, goal: str):
        self._ensure_tools()
        ws = self._workspace()
        max_iter = self.session.state.get("max_debug_iterations") or 5

        _print(f"\n  ⚡ Building: {goal}", BOLD)
        _print(f"  Workspace: {ws}", DIM)
        if self._parallel:
            _print("  Mode: parallel agents (2 variants)", DIM)
        print()

        build = BackgroundBuild()
        t = build.run(goal, ws, max_iter, self._parallel)
        build.wait_with_spinner(t)

        if build._error:
            _print(f"\n  ✗ Build error: {build._error}", RED)
            self.session.add_message("assistant", f"Build error: {build._error}")
            return

        result = build._result
        if result:
            v = result.get("verdict", {})
            score = v.get("score", "?")
            verdict = v.get("verdict", "done")
            ws_out = result.get("workspace", ws)
            self.session.set_workspace(ws_out)
            self.session.set_mode("discuss")
            self.session.increment_iteration()
            self.session.add_message("assistant", f"Build complete. Verdict: {verdict} (score: {score}/10)")
            _print(f"\n  ✓ Done! Verdict: {GREEN}{verdict}{R}  Score: {CYAN}{score}/10{R}", BOLD)
            _print(f"  Output: {ws_out}", DIM)
            _print("  Type /files to see generated files, /show <file> to view one.\n", DIM)
        else:
            _print("\n  Build finished (no result returned).\n", DIM)

    def _cmd_run(self):
        goal = self.session.state.get("current_goal")
        if not goal:
            _print("  No goal set — tell me what to build first.", YELLOW)
            return
        self._run_build(goal)

    def _cmd_improve(self):
        _print("\n  Self-improvement mode — scanning core files…", CYAN)
        self._ensure_tools()
        from orchestrator import init_tools, generate_plan, execute_plan
        goal = "Analyse and improve the Reflexion codebase: fix bugs, add missing features, improve robustness."
        plan = generate_plan(goal, workspace_name="reflexion_self")
        if "error" in plan:
            _print(f"  Planner failed: {plan['error']}", RED)
            return

        def cb(msg): print(f"  {DIM}{msg[:70]}{R}")
        result = execute_plan(plan, goal, plan["workspace_dir"], status_cb=cb, is_self_improve=True)
        if result:
            v = result.get("verdict", {})
            _print(f"\n  Self-improve complete: {v.get('verdict','done')} ({v.get('score','?')}/10)", GREEN)

    # ── Intent routing ────────────────────────────────────────

    def _is_build_intent(self, text: str) -> bool:
        """Check if user input expresses build intent.

        AUTONOMOUS POLICY: aggressively matches build/create/generate
        keywords and multi-file patterns. Uses _quick_classify first
        (zero-cost regex) and only falls back to model if needed.
        """
        from agents.conversation_agent import _quick_classify
        quick = _quick_classify(text)
        if quick and quick.get("mode") == "EXECUTE":
            return True

        from agents.conversation_agent import classify_intent
        try:
            result = classify_intent(text, self.session.state)
            mode = result if isinstance(result, str) else result.get("mode", "")
            return mode in ("EXECUTE", "BUILD", "CREATE")
        except Exception:
            low = text.lower()
            return any(k in low for k in ["build", "create", "make", "generate", "write", "implement", "add", "project", "app", "application"])

    def _chat_respond(self, text: str) -> str:
        """Stream a conversational reply and return it."""
        from model_router import call_model
        from memory.vector_store import get_relevant_context
        try:
            ctx = get_relevant_context(text)
        except Exception:
            ctx = ""
        context = self.session.get_conversation_context(last_n=6)
        sys_prompt = (
            "You are Reflexion, a local autonomous coding assistant. "
            "Be concise, direct, and practical. Use markdown where helpful."
        )
        prompt = f"{context}\n{ctx}\nUser: {text}"

        printer = StreamingPrinter()
        role = "think" if self.session.state.get("thinking_mode") else "chat"
        try:
            for token in call_model(role=role, prompt=prompt, stream=True, system_prompt=sys_prompt):
                printer.token(token)
        except Exception as exc:
            _print(f"\n  Model error: {exc}", RED)
            return ""
        return printer.done()

    # ── Input dispatch ────────────────────────────────────────

    def _dispatch(self, raw: str) -> bool:
        """Process one line of input. Returns False to exit."""
        line = raw.strip()
        if not line:
            return True

        if line.startswith("/"):
            parts = line.split()
            cmd, args = parts[0].lower(), parts[1:]

            if cmd in ("/exit", "/quit", "/q"):
                self.session.save()
                _print("\n  Session saved. Goodbye!\n", DIM)
                return False

            dispatch = {
                "/help":     _help,
                "/status":   self._cmd_status,
                "/history":  self._cmd_history,
                "/plan":     self._cmd_plan,
                "/files":    self._cmd_files,
                "/show":     lambda: self._cmd_show(args),
                "/run":      self._cmd_run,
                "/models":   self._cmd_models,
                "/sessions": self._cmd_sessions,
                "/resume":   lambda: self._cmd_resume(args),
                "/new":      self._cmd_new,
                "/reset":    self._cmd_reset,
                "/clear":    self._cmd_clear,
                "/think":    lambda: self._cmd_think(args),
                "/auto":     lambda: self._cmd_auto(args),
                "/parallel": lambda: self._cmd_parallel(args),
                "/improve":  self._cmd_improve,
            }

            fn = dispatch.get(cmd)
            if fn:
                fn()
            else:
                _print(f"  Unknown command: {cmd}  (try /help)", YELLOW)
            return True

        # Natural language
        self.session.add_message("user", line)

        if self._is_build_intent(line):
            # AUTONOMOUS BUILDER: always execute immediately — no manual
            # "continue" loops or "/run" gates.  Build intent = instant build.
            self.session.set_goal(line)
            self._run_build(line)
        else:
            response = self._chat_respond(line)
            if response:
                self.session.add_message("assistant", response)
                # Store in memory
                try:
                    from memory.vector_store import add_memory
                    add_memory(f"Q: {line}\nA: {response[:300]}", category="conversation")
                except Exception:
                    pass

        return True

    # ── Main loop ─────────────────────────────────────────────

    def run(self):
        _banner()
        from model_router import get_installed_models
        models = get_installed_models()
        if not models:
            _print("  ⚠  No Ollama models found. Run: ollama serve && ollama pull llama3:8b\n", YELLOW)
        else:
            _print(f"  {GREEN}✓{R} {len(models)} model(s) available  |  "
                   f"Session: {DIM}{self.session.session_id}{R}  |  "
                   f"Parallel: {CYAN}{'on' if self._parallel else 'off'}{R}\n", "")

        while True:
            try:
                line = input(f"{CYAN}reflexion{R}> ").strip()
            except (EOFError, KeyboardInterrupt):
                _print("\n  Interrupted — saving session.", DIM)
                self.session.save()
                break
            if not self._dispatch(line):
                break


# ── Entrypoints ───────────────────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser(description="Reflexion — local autonomous coding agent")
    sub = p.add_subparsers(dest="command")

    # ── reflexion build <task> ────────────────────────────────────
    build_p = sub.add_parser("build", help="Build a project from a task description")
    build_p.add_argument("task", help="Task description (what to build)")
    build_p.add_argument("--workspace", default=None, help="Workspace name")
    build_p.add_argument("--max-iter", type=int, default=5, help="Max debug iterations")
    build_p.add_argument("--sequential", action="store_true", help="Disable parallel agents")

    # ── reflexion run [workspace] ────────────────────────────────
    run_p = sub.add_parser("run", help="Execute the entrypoint of an existing workspace")
    run_p.add_argument("workspace", nargs="?", default=None, help="Workspace directory or name")

    # ── reflexion fix [workspace] ────────────────────────────────
    fix_p = sub.add_parser("fix", help="Run debugger on an existing workspace")
    fix_p.add_argument("workspace", nargs="?", default=None, help="Workspace directory or name")

    # ── reflexion test [workspace] ───────────────────────────────
    test_p = sub.add_parser("test", help="Execute + judge an existing workspace")
    test_p.add_argument("workspace", nargs="?", default=None, help="Workspace directory or name")

    # ── Legacy flags (interactive mode) ────────────────────────────
    p.add_argument("--resume", action="store_true", help="Resume the latest session")
    p.add_argument("--session", default=None, help="Specific session ID to load")
    p.add_argument("--check", action="store_true", help="System check only")
    p.add_argument("--sequential", action="store_true", help="Disable parallel agents")

    # Handle legacy "python cli.py <task>" syntax:
    # If first arg doesn't match a subcommand and isn't a flag, treat as build task
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] not in ("build", "run", "fix", "test", "--help", "-h", "--check", "--resume", "--session", "--sequential"):
        # Legacy mode: rewrite as "build <task>"
        _sys.argv = [_sys.argv[0], "build", " ".join(_sys.argv[1:])]

    args = p.parse_args()

    # ── Subcommand dispatch ──────────────────────────────────────
    if args.command == "build":
        from orchestrator import run as _run, init_tools
        init_tools()
        parallel = not args.sequential
        result = _run(
            args.task,
            workspace_name=args.workspace,
            max_iterations=args.max_iter,
            parallel=parallel,
        )
        if result:
            v = result.get("verdict", {})
            _print(f"\n  ✓ Build complete. Verdict: {v.get('verdict','done')}  Score: {v.get('score','?')}/10", GREEN)
            _print(f"  Output: {result.get('workspace', '?')}", DIM)
        else:
            _print("\n  ✗ Build failed.", RED)
        return

    if args.command == "run":
        from orchestrator import init_tools, WORKSPACE_BASE
        init_tools()
        ws = _resolve_workspace(args.workspace)
        if not ws:
            _print("  No workspace found. Specify a workspace name or path.", RED)
            return
        from tools.executor import auto_detect_and_run
        result = auto_detect_and_run(ws)
        print(result)
        return

    if args.command == "fix":
        from orchestrator import init_tools, WORKSPACE_BASE, _get_project_files
        init_tools()
        ws = _resolve_workspace(args.workspace)
        if not ws:
            _print("  No workspace found. Specify a workspace name or path.", RED)
            return
        from tools.executor import auto_detect_and_run
        exec_result = auto_detect_and_run(ws)
        if "error" in exec_result.lower() or "traceback" in exec_result.lower():
            _print(f"  Error detected, running debugger...", YELLOW)
            from agents.debugger import run_debugger
            debug_result = run_debugger(exec_result, ws, _get_project_files(ws))
            if debug_result.get("fixed"):
                _print(f"  ✓ Fix applied: {debug_result.get('summary', '')}", GREEN)
            else:
                _print(f"  ✗ Could not fix: {debug_result.get('summary', '')}", RED)
        else:
            _print("  No errors detected.", GREEN)
        return

    if args.command == "test":
        from orchestrator import init_tools, WORKSPACE_BASE, _get_project_files
        init_tools()
        ws = _resolve_workspace(args.workspace)
        if not ws:
            _print("  No workspace found. Specify a workspace name or path.", RED)
            return
        from tools.executor import auto_detect_and_run
        exec_result = auto_detect_and_run(ws)
        print(exec_result)
        from agents.judge import run_judge
        verdict = run_judge("test run", [{"files_written": _get_project_files(ws), "errors": []}], [exec_result], workspace_dir=ws)
        _print(f"\n  Verdict: {verdict.get('verdict','?')}  Score: {verdict.get('score','?')}/10", CYAN)
        if verdict.get("issues"):
            for issue in verdict["issues"]:
                _print(f"    ✗ {issue}", YELLOW)
        return

    # ── Legacy / interactive mode ────────────────────────────────
    if args.check:
        from orchestrator import check_system, init_tools
        init_tools()
        check_system()
        return

    sid = args.session
    if args.resume and not sid:
        from session.session_manager import SessionManager
        sid = SessionManager.get_latest_session_id()

    cli = CLI(session_id=sid)

    if args.sequential:
        cli._parallel = False

    cli.run()


def _resolve_workspace(ws_arg):
    """Resolve a workspace argument to an absolute path."""
    if not ws_arg:
        # Find most recent workspace
        ws_base = os.path.join(ROOT, "workspace")
        if not os.path.isdir(ws_base):
            return None
        entries = sorted(
            [os.path.join(ws_base, d) for d in os.listdir(ws_base) if os.path.isdir(os.path.join(ws_base, d))],
            key=os.path.getmtime, reverse=True,
        )
        return entries[0] if entries else None
    if os.path.isdir(ws_arg):
        return os.path.abspath(ws_arg)
    candidate = os.path.join(ROOT, "workspace", ws_arg)
    if os.path.isdir(candidate):
        return candidate
    return None


if __name__ == "__main__":
    main()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vZG9yaWFuZ3JheXBuZyB8IFJlZmxleGlvbiDigJQgQWxsIHJpZ2h0cyBvYnNlcnZlZC4="

# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
