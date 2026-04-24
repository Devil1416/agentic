"""
orchestrator.py - Main execution loop for niggativity.

PLAN -> BUILD -> EXECUTE -> DEBUG -> JUDGE -> REFINE -> REPEAT
"""

import io
import json
import os
import shutil
import sys
import time
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from agents.builder import run_builder
from agents.debugger import run_debugger
from agents.judge import run_judge
from agents.planner import run_planner
from agents.refiner import run_refiner
from memory.vector_store import add_memory, get_relevant_context, search_memory
from model_router import get_installed_models, pick_model
from tool_registry import list_tools, register_tool
from tools.diff_editor import edit_file_diff
from tools.executor import auto_detect_and_run, install_dependencies, run_command, run_node, run_python
from tools.fs import list_files, read_file, write_file
from tools.git_tools import git_commit, git_init, git_rollback
from tools.vision import analyze_image

MAX_ITERATIONS = 5
WORKSPACE_BASE = os.path.join(os.path.dirname(__file__), "workspace")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
VARIANTS_DIRNAME = ".variants"
IGNORED_DIRS = {"node_modules", "__pycache__", ".git", "venv", ".venv", VARIANTS_DIRNAME}


def init_tools():
    """Register all tools in the global registry."""
    register_tool("read_file", read_file, "Read file contents. Args: path (str)")
    register_tool("write_file", write_file, "Write content to file. Args: path (str), content (str)")
    register_tool("edit_file_diff", edit_file_diff, "Apply unified diff patch to file. Args: path (str), diff (str)")
    register_tool("list_files", list_files, "List files in directory. Args: path (str)")

    register_tool("run_python", run_python, "Run Python script. Args: project_dir (str), entrypoint (str), timeout (int, optional)")
    register_tool("run_node", run_node, "Run Node.js script. Args: project_dir (str), entrypoint (str), timeout (int, optional)")
    register_tool("run_command", run_command, "Run shell command. Args: command (str), cwd (str, optional), timeout (int, optional)")
    register_tool("auto_detect_and_run", auto_detect_and_run, "Auto-detect runtime and execute project. Args: project_dir (str), entrypoint (str, optional)")
    register_tool("install_dependencies", install_dependencies, "Install project deps (pip/npm). Args: project_dir (str), language (str, optional), deps (list, optional)")

    register_tool("analyze_image", analyze_image, "Analyze image with vision model. Args: path (str), prompt (str, optional)")

    register_tool("git_init", git_init, "Initialize git repo. Args: project_dir (str)")
    register_tool("git_commit", git_commit, "Stage and commit all changes. Args: project_dir (str), message (str, optional)")
    register_tool("git_rollback", git_rollback, "Rollback to previous commit. Args: project_dir (str), steps (int, optional)")

    print(f"[orchestrator] Registered {len(list_tools())} tools: {list_tools()}")


def check_system():
    """Verify Ollama is running and models are available."""
    print("\n" + "=" * 60)
    print("SYSTEM CHECK")
    print("=" * 60)

    models = get_installed_models()
    if not models:
        print("No Ollama models found.")
        print("Make sure Ollama is running: ollama serve")
        print("Install a model: ollama pull llama3:8b")
        return False

    print(f"Ollama connected - {len(models)} models available:")
    for model_name in models:
        print(f"  - {model_name}")

    roles = ["planner", "builder", "debugger", "judge", "refiner", "chat", "vision"]
    for role in roles:
        model = pick_model(role, models)
        status = model or "(none - install with ollama pull)"
        print(f"  {role:>10} -> {status}")

    return True


def generate_plan(task: str, workspace_name: str = None) -> dict:
    """Generate an implementation plan with codebase awareness."""
    init_tools()

    if not check_system():
        print("\nSystem check failed. Aborting.")
        return {"error": "System check failed"}

    if not workspace_name:
        workspace_name = f"project_{int(time.time())}"

    workspace_dir = os.path.join(WORKSPACE_BASE, workspace_name)
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    try:
        from codebase.indexer import Indexer

        indexer = Indexer(workspace_dir)
        indexer.update_index()
    except ImportError:
        pass

    print(f"\n{'=' * 60}")
    print("NIGGATIVITY - Planning Task")
    print(f"{'=' * 60}")
    print(f"Task: {task}")
    print(f"Workspace: {workspace_dir}")

    plan = run_planner(task, workspace_dir)

    if "raw_response" in plan and "files" not in plan:
        print("\nPlanner produced non-structured output. Attempting recovery...")
        plan = {
            "project_name": workspace_name,
            "description": task,
            "language": "python",
            "dependencies": [],
            "files": [{"path": "main.py", "purpose": "Main entry point"}],
            "entrypoint": "main.py",
            "subtasks": [],
            "existing_files_to_modify": [],
        }

    plan["workspace_dir"] = workspace_dir
    return plan


def execute_plan(plan: dict, task: str, workspace_dir: str, status_cb=None, max_iterations: int | None = None):
    """Execute a generated plan."""
    init_tools()

    def log_status(message: str):
        if status_cb:
            status_cb(message)
        print(message)

    iteration_limit = _resolve_iteration_limit(plan, max_iterations)

    print(f"\n{'=' * 60}")
    print("NIGGATIVITY - Executing Plan")
    print(f"{'=' * 60}")
    print(f"Max iterations: {'unlimited' if iteration_limit == 0 else iteration_limit}")
    print()

    session_log = {
        "task": task,
        "workspace": workspace_dir,
        "started": datetime.now().isoformat(),
        "iterations": [],
        "plan": plan,
    }

    deps = _clean_dependencies(plan.get("dependencies", []), plan.get("language", "python"))
    if deps:
        language = plan.get("language", "python")
        if language == "python":
            _install_python_deps(deps, workspace_dir)
        elif language in ("javascript", "node"):
            _install_node_deps(deps, workspace_dir)

    best_result = None

    iteration = 0
    while iteration_limit == 0 or iteration < iteration_limit:
        iter_log = {"iteration": iteration + 1, "timestamp": datetime.now().isoformat()}
        print(f"\n{'-' * 60}")
        if iteration_limit == 0:
            print(f"ITERATION {iteration + 1}")
        else:
            print(f"ITERATION {iteration + 1}/{iteration_limit}")
        print(f"{'-' * 60}")

        entrypoint = plan.get("entrypoint", "main.py")
        language = plan.get("language", "python")
        num_variants = 2 if iteration == 0 else 1
        variants = []
        variant_workspaces = []
        execution_results = []
        verdict = None

        if iteration_limit == 0:
            log_status(f"\n[BUILDER] Iteration {iteration + 1}")
        else:
            log_status(f"\n[BUILDER] Iteration {iteration + 1}/{iteration_limit}")

        for variant_id in range(1, num_variants + 1):
            variant_workspace = _prepare_variant_workspace(
                workspace_dir,
                iteration + 1,
                variant_id,
                seed_from_workspace=(iteration == 0),
            )
            variant = run_builder(plan, variant_workspace, variant_id=variant_id, status_cb=log_status)
            variant["workspace_dir"] = variant_workspace
            variants.append(variant)
            variant_workspaces.append(variant_workspace)

        iter_log["variants"] = variants

        for variant_id, variant_workspace in enumerate(variant_workspaces, start=1):
            full_entry_path = os.path.join(variant_workspace, entrypoint)
            if not os.path.isfile(full_entry_path):
                from tools.executor import _detect_entrypoint
                detected = _detect_entrypoint(variant_workspace)
                if detected:
                    entrypoint = detected
                    plan["entrypoint"] = detected
                    full_entry_path = os.path.join(variant_workspace, entrypoint)
                    
            # VALIDATION BEFORE EXECUTION
            files_missing = False
            variant_files = _get_project_files(variant_workspace)
            for f_info in plan.get("files", []):
                p = f_info.get("path") if isinstance(f_info, dict) else f_info
                if p and p not in variant_files:
                    files_missing = True
                    break

            if files_missing or not os.path.isfile(full_entry_path):
                print(f"\n[EXECUTOR] Variant #{variant_id} missing files. Triggering builder.")
                execution_results.append(f"Error: Missing required files.")
                continue

            log_status(f"\n[EXECUTOR] Executing variant #{variant_id}...")
            exec_result = _run_entrypoint(variant_workspace, entrypoint, language)

            # --- AUTO-INSTALL & SELF-REPAIR ---
            if "ModuleNotFoundError:" in exec_result:
                import re
                m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", exec_result)
                if m:
                    module = m.group(1)
                    mod_file = f"{module}.py"
                    full_mod_path = os.path.join(variant_workspace, mod_file)
                    
                    if not os.path.exists(full_mod_path):
                        print(f"\n[SELF-REPAIR] triggered")
                        print(f"[SELF-REPAIR] root cause: ModuleNotFoundError for {module}. Missing local file.")
                        print(f"[BUILDER] Creating file: {mod_file}")
                        run_builder({"files": [mod_file]}, variant_workspace, variant_id=variant_id, status_cb=log_status)
                        exec_result = _run_entrypoint(variant_workspace, entrypoint, language)
                    else:
                        if "error_history" not in session_log:
                            session_log["error_history"] = []
                        session_log["error_history"].append(module)
                        
                        if session_log["error_history"].count(module) >= 2:
                            print(f"\n[SELF-REPAIR] triggered for repeated error on {module}.")
                        else:
                            mapped = {"cv2": "opencv-python", "opencv": "opencv-python", "pil": "Pillow", "sklearn": "scikit-learn"}.get(module.lower(), module)
                            print(f"\n[DEPENDENCY] installing {mapped} (auto-fallback)")
                            _install_python_deps([mapped], variant_workspace)
                            exec_result = _run_entrypoint(variant_workspace, entrypoint, language)
            # ----------------------------------

            print(f"   {exec_result[:200]}")
            execution_results.append(exec_result)

        iter_log["execution"] = execution_results

        has_error = not execution_results or any(
            "error" in result.lower() or "traceback" in result.lower() or "exit_code: 1" in result.lower()
            for result in execution_results
        )

        chosen_workspace = variant_workspaces[0] if variant_workspaces else workspace_dir
        
        # VALIDATE FILES
        files_missing = False
        project_files = _get_project_files(chosen_workspace)
        if not project_files or not os.path.isfile(os.path.join(chosen_workspace, entrypoint)):
            files_missing = True
        else:
            for f_info in plan.get("files", []):
                p = f_info.get("path") if isinstance(f_info, dict) else f_info
                if p and p not in project_files:
                    files_missing = True
                    break
        
        if files_missing:
            log_status("\n[BUILDER] triggered (no files found or entrypoint missing). Skipping debug.")
            iter_log["debug"] = "Skipped - missing files"
            session_log["iterations"].append(iter_log)
            iteration += 1
            continue

        if len(variants) > 1 and execution_results:
            verdict = run_judge(task, variants, execution_results)
            iter_log["judge"] = verdict
            best_variant_idx = max(0, min(len(variants) - 1, verdict.get("best_variant", 1) - 1))
            chosen_workspace = variant_workspaces[best_variant_idx]

        if variant_workspaces:
            _sync_variant_to_workspace(chosen_workspace, workspace_dir)

        if not has_error:
            if verdict and verdict.get("verdict") == "refine":
                log_status("\n[REFINER] Applying judge suggestions...")
                refine_result = run_refiner(
                    chosen_workspace,
                    _get_project_files(chosen_workspace),
                    verdict.get("suggestions", []),
                )
                iter_log["refine"] = refine_result

                rerun_result = _run_entrypoint(chosen_workspace, entrypoint, language)
                execution_results = [rerun_result]
                iter_log["execution_after_refine"] = execution_results
                has_error = (
                    "error" in rerun_result.lower()
                    or "traceback" in rerun_result.lower()
                    or "exit_code: 1" in rerun_result.lower()
                )
                _sync_variant_to_workspace(chosen_workspace, workspace_dir)

            if not has_error:
                log_status("\n[EXECUTOR] Success! Exit code 0, no errors detected.")
                best_result = {
                    "verdict": verdict or {"verdict": "accept", "score": 10, "best_variant": 1},
                    "execution": execution_results,
                    "workspace": workspace_dir,
                }
                session_log["iterations"].append(iter_log)
                break

        log_status("\n[DEBUGGER] Errors detected - analyzing and fixing...")
        error_output = "\n\n".join(execution_results) if execution_results else f"Error: Entrypoint {entrypoint} missing."
        log_status(f"[ERROR]\n{error_output}")

        debug_result = run_debugger(error_output, chosen_workspace, _get_project_files(chosen_workspace), status_cb=log_status)
        iter_log["debug"] = debug_result

        if debug_result.get("fixed"):
            print("\n[EXECUTOR] Re-executing after fix...")
            rerun_result = _run_entrypoint(chosen_workspace, entrypoint, language)
            print(f"   {rerun_result[:200]}")
            execution_results = [rerun_result]
            iter_log["execution_after_debug"] = execution_results
            _sync_variant_to_workspace(chosen_workspace, workspace_dir)
            has_error = (
                "error" in rerun_result.lower()
                or "traceback" in rerun_result.lower()
                or "exit_code: 1" in rerun_result.lower()
            )
            if not has_error:
                log_status("\n[EXECUTOR] Debug fix successful! Exit code 0.")
                best_result = {
                    "verdict": verdict or {"verdict": "accept", "score": 10, "best_variant": 1},
                    "execution": execution_results,
                    "workspace": workspace_dir,
                }
                session_log["iterations"].append(iter_log)
                break

        session_log["iterations"].append(iter_log)
        best_result = {
            "verdict": verdict or {"verdict": "retry", "score": 5, "best_variant": 1},
            "execution": execution_results,
            "workspace": workspace_dir,
        }

        if iteration_limit != 0 and iteration >= iteration_limit - 1:
            log_status("\n[EXECUTOR] Max iterations reached. Stopping auto-continue.")
            break

        log_status(f"\nRetrying (iteration {iteration + 2})...")
        iteration += 1

    print(f"\n{'=' * 60}")
    print("SESSION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Task: {task}")
    print(f"Workspace: {workspace_dir}")
    print(f"Iterations: {len(session_log['iterations'])}")

    if best_result:
        verdict = best_result["verdict"]
        print(f"Final verdict: {verdict.get('verdict', 'N/A')} (score: {verdict.get('score', '?')}/10)")

    log_file = os.path.join(LOGS_DIR, f"session_{int(time.time())}.json")
    with open(log_file, "w", encoding="utf-8") as handle:
        json.dump(session_log, handle, indent=2, default=str)
    print(f"Session log: {log_file}")

    print("\nFinal project files:")
    for filepath in _get_project_files(workspace_dir):
        print(f"  {filepath}")

    return best_result


def run(task: str, workspace_name: str = None, status_cb=None, max_iterations: int | None = None):
    """Plan and execute a task end-to-end."""
    plan = generate_plan(task, workspace_name=workspace_name)
    if "error" in plan:
        return plan
    return execute_plan(plan, task, plan["workspace_dir"], status_cb=status_cb, max_iterations=max_iterations)


def _run_entrypoint(workspace_dir: str, entrypoint: str, language: str) -> str:
    if language == "python":
        return run_python(workspace_dir, entrypoint, timeout=30)
    if language in ("javascript", "node"):
        return run_node(workspace_dir, entrypoint, timeout=30)
    return run_command(f"python {entrypoint}", cwd=workspace_dir, timeout=30)


def _resolve_iteration_limit(plan: dict, override: int | None) -> int:
    """Resolve the debug/build retry cap. Zero means unlimited."""
    if override is not None:
        return max(0, int(override))

    plan_value = plan.get("max_debug_iterations")
    if plan_value is not None:
        return max(0, int(plan_value))

    env_value = os.getenv("NIGGATIVITY_MAX_DEBUG_ITERATIONS")
    if env_value:
        try:
            return max(0, int(env_value))
        except ValueError:
            pass

    return MAX_ITERATIONS


def _get_project_files(workspace_dir: str) -> list[str]:
    """List all project files in workspace."""
    files = []
    if os.path.isdir(workspace_dir):
        for root, dirs, filenames in os.walk(workspace_dir):
            dirs[:] = [dirname for dirname in dirs if dirname not in IGNORED_DIRS and not dirname.startswith(".")]
            for filename in filenames:
                files.append(os.path.relpath(os.path.join(root, filename), workspace_dir))
    return sorted(files)


def _prepare_variant_workspace(workspace_dir: str, iteration: int, variant_id: int, seed_from_workspace: bool) -> str:
    """Create a variant sandbox for competitive builds."""
    variant_dir = os.path.join(
        workspace_dir,
        VARIANTS_DIRNAME,
        f"iteration_{iteration}",
        f"variant_{variant_id}",
    )
    if os.path.isdir(variant_dir):
        import stat
        def force_remove(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(variant_dir, onerror=force_remove)
    os.makedirs(variant_dir, exist_ok=True)

    if seed_from_workspace:
        _copy_project_tree(workspace_dir, variant_dir)

    return variant_dir


def _sync_variant_to_workspace(variant_dir: str, workspace_dir: str):
    """Copy the selected variant into the canonical workspace."""
    _copy_project_tree(variant_dir, workspace_dir)


def _copy_project_tree(src_dir: str, dst_dir: str):
    """Copy project files, skipping caches and variant directories."""
    if not os.path.isdir(src_dir):
        return

    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        rel_root = "" if rel_root == "." else rel_root
        dirs[:] = [dirname for dirname in dirs if dirname not in IGNORED_DIRS and not dirname.startswith(".")]

        for filename in files:
            if filename == ".niggativity_index.json":
                continue
            src_file = os.path.join(root, filename)
            rel_path = os.path.normpath(os.path.join(rel_root, filename))
            dst_file = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)


def _install_python_deps(deps: list[str], workspace_dir: str):
    """Install Python dependencies."""
    if not deps:
        return

    if sys.version_info >= (3, 13):
        print(f"\n[DEPENDENCY] Warning: Python >= 3.13 detected ({sys.version.split()[0]}). Some packages might fail.")

    print(f"\nInstalling Python deps: {deps}")
    for d in deps:
        print(f"[DEPENDENCY] installing {d}")

    dep_str = " ".join(deps)
    result = run_command(f'"{sys.executable}" -m pip install {dep_str}', cwd=workspace_dir, timeout=120)
    print(f"   {result[:200]}")
    
    if "error:" in result.lower() or "no matching distribution" in result.lower():
        print("   Dependency install failed. Attempting to fix names and retry...")
        fixed_deps = [d.replace("opencv", "opencv-python").replace("cv2", "opencv-python") for d in deps]
        fixed_deps = ["Pillow" if "pil" in d.lower() else d for d in fixed_deps]
        if fixed_deps != deps:
            dep_str = " ".join(fixed_deps)
            result = run_command(f'"{sys.executable}" -m pip install {dep_str}', cwd=workspace_dir, timeout=120)
            print(f"   Retry result: {result[:200]}")


def _install_node_deps(deps: list[str], workspace_dir: str):
    """Install Node.js dependencies."""
    if not deps:
        return
    pkg_json = os.path.join(workspace_dir, "package.json")
    if not os.path.exists(pkg_json):
        run_command("npm init -y", cwd=workspace_dir, timeout=30)

    print(f"\nInstalling Node deps: {deps}")
    dep_str = " ".join(deps)
    result = run_command(f"npm install {dep_str}", cwd=workspace_dir, timeout=120)
    print(f"   {result[:200]}")


def _clean_dependencies(deps: list[str], language: str) -> list[str]:
    """Drop empty or obviously invalid dependency names."""
    cleaned = []
    invalid = {"python", "python3", "node", "javascript", "js", language.lower()}
    
    mapping = {
        "opencv": "opencv-python",
        "cv2": "opencv-python",
        "opencv-python": "opencv-python",
        "pillow": "Pillow",
        "pil": "Pillow"
    }

    for dep in deps or []:
        dep_name = str(dep).strip()
        if not dep_name:
            continue
        if dep_name.lower() in invalid:
            continue
            
        mapped_name = mapping.get(dep_name.lower(), dep_name)
        cleaned.append(mapped_name)

    return cleaned
