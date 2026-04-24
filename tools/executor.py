"""
tools/executor.py — Real code execution via subprocess.

Supports Python and Node.js with timeout, stdout/stderr capture.
"""

import os
import subprocess
import sys


def run_python(project_dir: str, entrypoint: str, timeout: int = 30) -> str:
    """
    Run a Python file via subprocess.

    Args:
        project_dir: Directory containing the project.
        entrypoint: Python file to run (relative to project_dir).
        timeout: Max seconds before killing the process.

    Returns:
        Combined output string with exit code, stdout, stderr.
    """
    project_dir = os.path.abspath(project_dir)
    script = os.path.join(project_dir, entrypoint)

    if not os.path.exists(script):
        return f"ERROR: File not found: {script}"

    return _run_command(
        [sys.executable, script],
        cwd=project_dir,
        timeout=timeout,
        label=f"python {entrypoint}"
    )


def run_node(project_dir: str, entrypoint: str, timeout: int = 30) -> str:
    """
    Run a Node.js file via subprocess.

    Args:
        project_dir: Directory containing the project.
        entrypoint: JS file to run (relative to project_dir).
        timeout: Max seconds before killing the process.

    Returns:
        Combined output string with exit code, stdout, stderr.
    """
    project_dir = os.path.abspath(project_dir)
    script = os.path.join(project_dir, entrypoint)

    if not os.path.exists(script):
        return f"ERROR: File not found: {script}"

    return _run_command(
        ["node", script],
        cwd=project_dir,
        timeout=timeout,
        label=f"node {entrypoint}"
    )


def run_command(command: str, cwd: str = ".", timeout: int = 30) -> str:
    """
    Run an arbitrary shell command.

    Args:
        command: Shell command string.
        cwd: Working directory.
        timeout: Max seconds.

    Returns:
        Combined output with exit code.
    """
    cwd = os.path.abspath(cwd)
    return _run_command(
        command,
        cwd=cwd,
        timeout=timeout,
        label=command,
        shell=True
    )


def _run_command(cmd, cwd: str, timeout: int, label: str, shell: bool = False) -> str:
    """Internal: execute a command and capture results."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        parts = [f"[exec] {label}", f"cwd: {cwd}"]
        parts.append(f"exit_code: {proc.returncode}")

        if proc.stdout.strip():
            stdout = proc.stdout.strip()
            # Truncate very long output
            if len(stdout) > 3000:
                stdout = stdout[:1500] + "\n... (truncated) ...\n" + stdout[-1500:]
            parts.append(f"stdout:\n{stdout}")

        if proc.stderr.strip():
            stderr = proc.stderr.strip()
            if len(stderr) > 2000:
                stderr = stderr[:1000] + "\n... (truncated) ...\n" + stderr[-1000:]
            parts.append(f"stderr:\n{stderr}")

        if proc.returncode == 0 and not proc.stdout.strip() and not proc.stderr.strip():
            parts.append("(no output)")

        return "\n".join(parts)

    except subprocess.TimeoutExpired:
        return f"[exec] {label}\nERROR: Timed out after {timeout}s"
    except FileNotFoundError:
        return f"[exec] {label}\nERROR: Command not found"
    except Exception as e:
        return f"[exec] {label}\nERROR: {e}"


def auto_detect_and_run(project_dir: str, entrypoint: str = None,
                        timeout: int = 30) -> str:
    """
    Auto-detect runtime and execute the project.

    Detection order:
      1. Explicit entrypoint extension (.py -> python, .js -> node)
      2. package.json -> npm run dev (or npm start)
      3. requirements.txt + .py files -> python
      4. Fallback to python

    Args:
        project_dir: Project directory.
        entrypoint: Optional entrypoint file. Auto-detected if None.
        timeout: Execution timeout in seconds.

    Returns:
        Execution output string.
    """
    project_dir = os.path.abspath(project_dir)

    # Auto-detect entrypoint if not provided
    if not entrypoint:
        entrypoint = _detect_entrypoint(project_dir)

    if not entrypoint:
        return "ERROR: Could not detect entrypoint. No .py or .js files found."

    ext = os.path.splitext(entrypoint)[1].lower()

    # Check for package.json with scripts
    pkg_json = os.path.join(project_dir, "package.json")
    if os.path.exists(pkg_json) and ext in (".js", ".ts", ".jsx", ".tsx", ""):
        try:
            import json
            with open(pkg_json) as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "dev" in scripts:
                return _run_command("npm run dev", cwd=project_dir,
                                    timeout=timeout, label="npm run dev", shell=True)
            elif "start" in scripts:
                return _run_command("npm start", cwd=project_dir,
                                    timeout=timeout, label="npm start", shell=True)
        except Exception:
            pass

    if ext == ".py":
        return run_python(project_dir, entrypoint, timeout)
    elif ext in (".js", ".mjs"):
        return run_node(project_dir, entrypoint, timeout)
    elif ext in (".ts", ".tsx"):
        # Try ts-node or npx tsx
        return _run_command(f"npx tsx {entrypoint}", cwd=project_dir,
                            timeout=timeout, label=f"tsx {entrypoint}", shell=True)
    else:
        # Default to python
        return run_python(project_dir, entrypoint, timeout)


def _detect_entrypoint(project_dir: str) -> str | None:
    """Auto-detect the project entrypoint."""
    candidates = [
        "main.py", "app.py", "server.py", "index.py",
        "index.js", "app.js", "server.js", "main.js",
        "index.ts", "app.ts", "server.ts", "main.ts",
    ]
    for c in candidates:
        if os.path.exists(os.path.join(project_dir, c)):
            return c
    # Search for any .py or .js file
    for f in os.listdir(project_dir):
        if f.endswith(".py"):
            return f
    for f in os.listdir(project_dir):
        if f.endswith(".js"):
            return f
    return None


def install_dependencies(project_dir: str, language: str = "auto",
                         deps: list = None) -> str:
    """
    Install project dependencies.

    Auto-detects language from project files if not specified.

    Args:
        project_dir: Project directory.
        language: 'python', 'node', or 'auto'.
        deps: Specific dependencies to install. If None, uses
              requirements.txt or package.json.

    Returns:
        Installation output.
    """
    project_dir = os.path.abspath(project_dir)

    if language == "auto":
        language = _detect_language(project_dir)

    results = []

    if language == "python":
        req_file = os.path.join(project_dir, "requirements.txt")
        if deps:
            dep_str = " ".join(deps)
            results.append(run_command(
                f'"{sys.executable}" -m pip install {dep_str}',
                cwd=project_dir, timeout=120
            ))
        elif os.path.exists(req_file):
            results.append(run_command(
                f'"{sys.executable}" -m pip install -r requirements.txt',
                cwd=project_dir, timeout=120
            ))
        else:
            return "No requirements.txt found and no deps specified."

    elif language in ("node", "javascript"):
        pkg_json = os.path.join(project_dir, "package.json")
        if deps:
            dep_str = " ".join(deps)
            if not os.path.exists(pkg_json):
                run_command("npm init -y", cwd=project_dir, timeout=15)
            results.append(run_command(
                f"npm install {dep_str}",
                cwd=project_dir, timeout=120
            ))
        elif os.path.exists(pkg_json):
            results.append(run_command(
                "npm install",
                cwd=project_dir, timeout=120
            ))
        else:
            return "No package.json found and no deps specified."

    return "\n".join(results) if results else "Nothing to install."


def _detect_language(project_dir: str) -> str:
    """Detect project language from files."""
    if os.path.exists(os.path.join(project_dir, "package.json")):
        return "node"
    if os.path.exists(os.path.join(project_dir, "requirements.txt")):
        return "python"
    # Check file extensions
    for f in os.listdir(project_dir):
        if f.endswith(".py"):
            return "python"
        if f.endswith((".js", ".ts", ".jsx", ".tsx")):
            return "node"
    return "python"
