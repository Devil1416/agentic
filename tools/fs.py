"""
tools/fs.py — Filesystem tools: read, write, list, edit via diff.
"""

import os


def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"


def list_files(path: str = ".") -> str:
    """List all files recursively under the given directory."""
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a directory: {path}")

    result = []
    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and common noise
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                   ('node_modules', '__pycache__', '.git', 'venv', '.venv')]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), path)
            result.append(rel)

    if not result:
        return "Directory is empty."
    return "\n".join(sorted(result))
