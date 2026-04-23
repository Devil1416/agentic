"""
tools/git_tools.py — Git operations for project management.

Provides init, commit, and rollback capabilities.
"""

import os
from tools.executor import run_command


def git_init(project_dir: str) -> str:
    """Initialize a git repository in the project directory."""
    project_dir = os.path.abspath(project_dir)
    if os.path.exists(os.path.join(project_dir, ".git")):
        return f"Git already initialized in {project_dir}"

    result = run_command("git init", cwd=project_dir, timeout=10)

    # Create .gitignore
    gitignore = os.path.join(project_dir, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write(
                "__pycache__/\n*.pyc\nnode_modules/\n.env\nvenv/\n"
                ".venv/\ndist/\nbuild/\n*.egg-info/\n"
            )

    return result


def git_commit(project_dir: str, message: str = "auto-commit") -> str:
    """Stage all changes and commit."""
    project_dir = os.path.abspath(project_dir)
    if not os.path.exists(os.path.join(project_dir, ".git")):
        init_result = git_init(project_dir)

    run_command("git add -A", cwd=project_dir, timeout=10)
    result = run_command(
        f'git commit -m "{message}" --allow-empty',
        cwd=project_dir,
        timeout=10,
    )
    return result


def git_rollback(project_dir: str, steps: int = 1) -> str:
    """Rollback to a previous commit."""
    project_dir = os.path.abspath(project_dir)
    if not os.path.exists(os.path.join(project_dir, ".git")):
        return "ERROR: Not a git repository."

    result = run_command(
        f"git reset --hard HEAD~{steps}",
        cwd=project_dir,
        timeout=10,
    )
    return result


def git_log(project_dir: str, count: int = 5) -> str:
    """Show recent git log."""
    project_dir = os.path.abspath(project_dir)
    if not os.path.exists(os.path.join(project_dir, ".git")):
        return "Not a git repository."

    return run_command(
        f"git log --oneline -n {count}",
        cwd=project_dir,
        timeout=10,
    )


def git_diff(project_dir: str) -> str:
    """Show current unstaged changes."""
    project_dir = os.path.abspath(project_dir)
    return run_command("git diff", cwd=project_dir, timeout=10)
