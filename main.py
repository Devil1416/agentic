#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                            ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
main.py — Entry point for reflexion.

Usage:
    python main.py "Build a Flask REST API with CRUD endpoints for a todo app"
    python main.py --interactive
    python main.py --check
"""

import sys
import os
import io

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
"integrity": "9e68163d3150",
}
# ─── /fingerprint ───────────────────────────────────────────


# Fix Windows terminal encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))


def print_banner():
    banner = r"""
 +---------------------------------------------------------+
 |                                                         |
 |  _   _ ___ ____ ____    _  _____ _____     _____ _______  __|
 | | \ | |_ _/ ___|/ ___|  / \|_   _|_ _\ \   / /_ _|_   _\ \/ /|
 | |  \| || | |  _| |  _  / _ \ | |  | | \ \ / / | |  | |  \  / |
 | | |\  || | |_| | |_| |/ ___ \| |  | |  \ V /  | |  | |  /  \ |
 | |_| \_|___\____|\____/_/   \_\_| |___|  \_/  |___| |_| /_/\_\|
 |                                                         |
 |        Local-First Autonomous Coding System             |
 |        Powered by Ollama - Zero Cloud Dependencies      |
 |                                                         |
 +---------------------------------------------------------+
"""


    print(banner)


def run_interactive():
    """Interactive REPL mode."""
    from orchestrator import run, check_system, init_tools

    init_tools()
    if not check_system():
        print("\n[!] System check failed. Make sure Ollama is running.")
        return

    print("\n[>] Interactive mode. Type your task and press Enter.")
    print("    Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            task = input("reflexion> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        try:
            run(task)
        except KeyboardInterrupt:
            print("\n\n[!] Interrupted. Returning to prompt...")
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()


def run_single(task: str):
    """Single task execution."""
    from orchestrator import run
    run(task)


def run_check():
    """System check only."""
    from orchestrator import check_system, init_tools
    init_tools()
    check_system()


def main():
    print_banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print('  python main.py "Build a Flask REST API"')
        print('  python main.py --interactive')
        print('  python main.py --check')
        print()

        # Default to interactive
        run_interactive()
        return

    arg = sys.argv[1]

    if arg == "--check":
        run_check()
    elif arg == "--interactive":
        run_interactive()
    elif arg == "--help":
        print("Usage:")
        print('  python main.py "<task>"          Run a single task')
        print('  python main.py --interactive     Interactive REPL mode')
        print('  python main.py --check           Check Ollama + models')
    else:
        # Treat as task
        task = " ".join(sys.argv[1:])
        run_single(task)


if __name__ == "__main__":
    main()


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
