# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "1cf9ee47813e",
}
# ─── /fingerprint ───────────────────────────────────────────

"""
utils/command_parser.py — Parse user input into commands or natural language.

Handles slash commands and routes everything else to the conversation agent.
"""

COMMANDS = {
    "/exit": "Quit the session",
    "/quit": "Quit the session",
    "/run": "Execute the current plan immediately",
    "/plan": "Show the current plan",
    "/files": "List workspace files",
    "/open": "Display file contents (usage: /open <file>)",
    "/show": "Display file contents (usage: /show <file>)",
    "/reset": "Clear session and start fresh",
    "/memory": "Show stored memories",
    "/help": "Show available commands",
    "/status": "Show current session status",
    "/history": "Show conversation history",
    "/image": "Analyze image for UI code gen (usage: /image <path> [desc])",
}

def parse_input(raw: str) -> dict:
    """
    Parse user input into a structured command.

    Returns:
        {
            "type": "command" | "message",
            "command": str | None,
            "args": list[str],
            "raw": str
        }
    """


    raw = raw.strip()
    if not raw:
        return {"type": "empty", "command": None, "args": [], "raw": ""}

    if raw.startswith("/"):
        parts = raw.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        # Normalize aliases
        if cmd in ("/q", "/quit"):
            cmd = "/exit"

        return {
            "type": "command",
            "command": cmd,
            "args": args,
            "raw": raw,
        }

    return {
        "type": "message",
        "command": None,
        "args": [],
        "raw": raw,
    }


def get_help_text() -> str:
    """Generate formatted help text for all commands."""
    lines = ["\n  Available Commands:\n"]
    for cmd, desc in COMMANDS.items():
        lines.append(f"    {cmd:<12} {desc}")
    lines.append("")
    lines.append("  Or just type naturally — I'll figure out what you mean.")
    lines.append("")
    return "\n".join(lines)


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
