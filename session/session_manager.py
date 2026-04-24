"""
session/session_manager.py — Persistent session state with multi-session support.

Tracks conversation history, current plan, workspace, and goals across the session.
Saves to disk so sessions can survive restarts.
Supports listing, switching, and deleting multiple sessions.
"""

import json
import os
import time
from datetime import datetime

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "sessions")


class SessionManager:
    """Manages a persistent conversational session with multi-session support."""

    def __init__(self, session_id: str = None):
        os.makedirs(SESSION_DIR, exist_ok=True)

        self.session_id = session_id or f"session_{int(time.time())}"
        self.session_file = os.path.join(SESSION_DIR, f"{self.session_id}.json")

        self.state = {
            "session_id": self.session_id,
            "title": "New Chat",
            "created": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "current_goal": None,
            "current_plan": None,
            "workspace_dir": None,
            "conversation": [],
            "mode": "discuss",  # chat | discuss | plan | execute | debug
            "iteration_count": 0,
            "files_created": [],
            "tech_stack": None,       # e.g. {"frontend": "React", "backend": "FastAPI"}
            "file_structure": [],     # current workspace file listing
            "last_task": None,        # last executed task description
            "artifacts": [],          # list of artifacts (code outputs, files, structured data)
            "thinking_mode": False,
            "auto_execute": False,
            "max_debug_iterations": 0,
        }

        # Load existing session if available
        if os.path.exists(self.session_file):
            self._load()

    def _load(self):
        """Load session from disk."""
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                self.state.update(saved)
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        """Persist session to disk."""
        self.state["last_active"] = datetime.now().isoformat()
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)

    def add_message(self, role: str, content: str, artifacts: list = None):
        """Add a message to conversation history.

        Args:
            role: "user" | "assistant" | "system"
            content: Message text.
            artifacts: Optional list of artifact dicts to attach to this message.
        """
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if artifacts:
            msg["artifacts"] = artifacts
        self.state["conversation"].append(msg)

        # Auto-title from first user message
        if role == "user" and self.state.get("title") == "New Chat":
            title = content[:60].strip()
            if len(content) > 60:
                title += "…"
            self.state["title"] = title

        # Keep conversation manageable (last 100 messages)
        if len(self.state["conversation"]) > 100:
            self.state["conversation"] = self.state["conversation"][-100:]
        self.save()

    def add_artifact(self, artifact: dict):
        """Add an artifact to the session.

        Artifact format:
        {
            "type": "code" | "file" | "diff" | "plan" | "result" | "error",
            "title": "Short title",
            "language": "python",  (for code artifacts)
            "content": "...",
            "timestamp": "...",
        }
        """
        artifact["timestamp"] = artifact.get("timestamp", datetime.now().isoformat())
        artifact["id"] = f"art_{int(time.time() * 1000)}"
        self.state.setdefault("artifacts", []).append(artifact)
        # Keep last 50 artifacts
        if len(self.state["artifacts"]) > 50:
            self.state["artifacts"] = self.state["artifacts"][-50:]
        self.save()
        return artifact["id"]

    def get_artifacts(self, last_n: int = 20) -> list:
        """Get recent artifacts."""
        return self.state.get("artifacts", [])[-last_n:]

    def get_conversation_context(self, last_n: int = 10) -> str:
        """Get recent conversation as formatted string for model context."""
        messages = self.state["conversation"][-last_n:]
        lines = []
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            # Truncate long messages in context
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines)

    def set_goal(self, goal: str):
        self.state["current_goal"] = goal
        self.save()

    def set_plan(self, plan: dict):
        self.state["current_plan"] = plan
        self.save()

    def set_workspace(self, workspace_dir: str):
        self.state["workspace_dir"] = workspace_dir
        self.save()

    def set_mode(self, mode: str):
        self.state["mode"] = mode
        self.save()

    def set_title(self, title: str):
        self.state["title"] = title
        self.save()

    def set_setting(self, key: str, value):
        self.state[key] = value
        self.save()

    def add_file(self, filepath: str):
        if filepath not in self.state["files_created"]:
            self.state["files_created"].append(filepath)
            self.save()

    def increment_iteration(self):
        self.state["iteration_count"] += 1
        self.save()

    def set_tech_stack(self, stack: dict):
        """Set the current project's tech stack."""
        self.state["tech_stack"] = stack
        self.save()

    def update_file_structure(self, files: list[str]):
        """Update the tracked file structure."""
        self.state["file_structure"] = files
        self.save()

    def set_last_task(self, task: str):
        """Record the last executed task."""
        self.state["last_task"] = task
        self.save()

    def reset(self):
        """Clear session state for a fresh start."""
        self.state = {
            "session_id": self.session_id,
            "title": "New Chat",
            "created": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "current_goal": None,
            "current_plan": None,
            "workspace_dir": None,
            "conversation": [],
            "mode": "discuss",
            "iteration_count": 0,
            "files_created": [],
            "tech_stack": None,
            "file_structure": [],
            "last_task": None,
            "artifacts": [],
            "thinking_mode": False,
            "auto_execute": False,
            "max_debug_iterations": 0,
        }
        self.save()

    def get_status(self) -> str:
        """Get human-readable session status."""
        s = self.state
        stack = s.get('tech_stack')
        stack_str = "(none)"
        if stack:
            parts = [f"{k}: {v}" for k, v in stack.items() if v]
            stack_str = ", ".join(parts) if parts else "(none)"
        lines = [
            f"  Session:    {s['session_id']}",
            f"  Title:      {s.get('title', 'Untitled')}",
            f"  Mode:       {s['mode']}",
            f"  Goal:       {s.get('current_goal') or '(none)'}",
            f"  Last task:  {s.get('last_task') or '(none)'}",
            f"  Tech stack: {stack_str}",
            f"  Workspace:  {s.get('workspace_dir') or '(none)'}",
            f"  Thinking:   {'on' if s.get('thinking_mode') else 'off'}",
            f"  Auto Exec:  {'on' if s.get('auto_execute') else 'off'}",
            f"  Debug Cap:  {'unlimited' if s.get('max_debug_iterations', 0) == 0 else s.get('max_debug_iterations')}",
            f"  Messages:   {len(s.get('conversation', []))}",
            f"  Files:      {len(s.get('files_created', []))}",
            f"  Artifacts:  {len(s.get('artifacts', []))}",
            f"  Iterations: {s.get('iteration_count', 0)}",
        ]
        return "\n".join(lines)

    def get_history(self, last_n: int = 20) -> str:
        """Get formatted conversation history."""
        messages = self.state["conversation"][-last_n:]
        if not messages:
            return "  No conversation history yet."
        lines = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            prefix = "  > " if role == "user" else "  < "
            lines.append(f"{prefix}{content}")
        return "\n".join(lines)

    # ─── MULTI-SESSION CLASS METHODS ──────────────────────

    @staticmethod
    def list_sessions() -> list[dict]:
        """List all available sessions with metadata.

        Returns:
            List of dicts with session_id, title, created, last_active, message_count.
        """
        os.makedirs(SESSION_DIR, exist_ok=True)
        sessions = []
        for fname in os.listdir(SESSION_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(SESSION_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", fname.replace(".json", "")),
                    "title": data.get("title", "Untitled"),
                    "created": data.get("created", ""),
                    "last_active": data.get("last_active", ""),
                    "message_count": len(data.get("conversation", [])),
                    "mode": data.get("mode", "discuss"),
                    "goal": data.get("current_goal"),
                })
            except (json.JSONDecodeError, IOError):
                continue

        # Sort by last_active descending
        sessions.sort(key=lambda s: s.get("last_active", ""), reverse=True)
        return sessions

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a session by ID."""
        fpath = os.path.join(SESSION_DIR, f"{session_id}.json")
        if os.path.exists(fpath):
            os.remove(fpath)
            return True
        return False

    @staticmethod
    def get_latest_session_id() -> str | None:
        """Get the most recently active session ID."""
        sessions = SessionManager.list_sessions()
        if sessions:
            return sessions[0]["session_id"]
        return None
