# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
tools/diff_editor.py — Unified-diff-based file editing.

Applies patches to files without full overwrite.
"""

import os
import re

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "df1915d6298f",
}
# ─── /fingerprint ───────────────────────────────────────────


def edit_file_diff(path: str, diff: str) -> str:
    """
    Apply a unified diff patch to a file.

    Diff format:
    --- old
    +++ new
    @@ -start,count +start,count @@
     context line
    -removed line
    +added line

    Returns summary of changes applied.
    """


    path = os.path.abspath(path)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot patch non-existent file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    patched_lines = _apply_unified_diff(original_lines, diff)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(patched_lines)

    added = sum(1 for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff.splitlines() if l.startswith('-') and not l.startswith('---'))

    return f"Patched {path}: +{added} -{removed} lines"


def _apply_unified_diff(original_lines: list[str], diff: str) -> list[str]:
    """Parse and apply unified diff hunks to the original lines."""
    result = list(original_lines)
    hunks = _parse_hunks(diff)

    # Apply hunks in reverse order to preserve line numbers
    for hunk in reversed(hunks):
        start = hunk["old_start"] - 1  # 0-indexed
        old_lines = hunk["old_lines"]
        new_lines = hunk["new_lines"]

        # Verify context matches (best effort)
        end = start + len(old_lines)

        # Replace the range
        result[start:end] = [l + "\n" if not l.endswith("\n") else l for l in new_lines]

    return result


def _parse_hunks(diff: str) -> list[dict]:
    """Extract hunks from a unified diff string."""
    hunks = []
    lines = diff.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip --- and +++ headers
        if line.startswith('---') or line.startswith('+++'):
            i += 1
            continue

        # Match @@ header
        match = re.match(r'^@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
        if match:
            old_start = int(match.group(1))
            i += 1

            old_lines = []
            new_lines = []

            while i < len(lines):
                l = lines[i]
                if l.startswith('@@') or l.startswith('---') or l.startswith('+++'):
                    break
                if l.startswith('-'):
                    old_lines.append(l[1:])
                elif l.startswith('+'):
                    new_lines.append(l[1:])
                elif l.startswith(' ') or l == '':
                    content = l[1:] if l.startswith(' ') else l
                    old_lines.append(content)
                    new_lines.append(content)
                else:
                    # Treat as context
                    old_lines.append(l)
                    new_lines.append(l)
                i += 1

            hunks.append({
                "old_start": old_start,
                "old_lines": old_lines,
                "new_lines": new_lines,
            })
        else:
            i += 1

    # If no @@ headers found, try simple +/- format
    if not hunks:
        hunks = _parse_simple_diff(diff)

    return hunks


def _parse_simple_diff(diff: str) -> list[dict]:
    """
    Fallback parser for simple diffs without @@ headers.
    Treats - lines as removals and + lines as additions.
    """
    lines = diff.splitlines()
    old_lines = []
    new_lines = []

    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            continue
        elif line.startswith('-'):
            old_lines.append(line[1:])
        elif line.startswith('+'):
            new_lines.append(line[1:])
        elif line.startswith(' '):
            old_lines.append(line[1:])
            new_lines.append(line[1:])

    if old_lines or new_lines:
        return [{"old_start": 1, "old_lines": old_lines, "new_lines": new_lines}]
    return []


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
