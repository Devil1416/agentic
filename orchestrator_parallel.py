# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
orchestrator_parallel.py — Parallel agent execution engine for Reflexion.

Enables true concurrent execution of independent agents:
  - Planner always runs first (serial)
  - Builder variants run in parallel threads
  - Debugger + Refiner run concurrently when both have work
  - Judge collects all variant results and picks the best deterministically
  - Results are merged with strict interface-contract enforcement
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import time
from datetime import datetime
from typing import Callable, Optional

from model_router import get_installed_models, pick_model
from tools.executor import auto_detect_and_run, run_python, run_node
from tools.fs import list_files, read_file, write_file


# ─── Logging helpers ────────────────────────────────────────

def _log(msg: str, cb: Optional[Callable] = None):
    print(msg)
    if cb:
        cb(msg)


# ─── Variant workspace management ───────────────────────────

def _make_variant_workspace(base: str, iteration: int, variant_id: int) -> str:
    path = os.path.join(base, ".variants", f"iter{iteration}_v{variant_id}")
    os.makedirs(path, exist_ok=True)
    return path


def _seed_variant(src: str, dst: str):
    """Copy existing workspace files into variant dir."""
    if not os.path.isdir(src):
        return
    for item in os.listdir(src):
        if item.startswith("."):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)
        elif os.path.isdir(s) and item not in ("node_modules", "__pycache__", "venv"):
            shutil.copytree(s, d, dirs_exist_ok=True)
    # Safety net: ensure contract.json is always present in variant
    contract_src = os.path.join(src, "contract.json")
    contract_dst = os.path.join(dst, "contract.json")
    if os.path.isfile(contract_src) and not os.path.isfile(contract_dst):
        shutil.copy2(contract_src, contract_dst)


def _sync_to_workspace(src: str, dst: str):
    """Copy chosen variant back to the main workspace."""
    for item in os.listdir(src):
        if item.startswith("."):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)
        elif os.path.isdir(s) and item not in ("node_modules", "__pycache__", "venv"):
            shutil.copytree(s, d, dirs_exist_ok=True)


def _get_project_files(workspace: str) -> list[str]:
    """List relative file paths in workspace, skipping ignored dirs."""
    ignored = {"node_modules", "__pycache__", ".git", "venv", ".venv", ".variants"}
    result = []
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in ignored]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), workspace)
            result.append(rel.replace("\\", "/"))
    return sorted(result)


# ─── Execution helper ────────────────────────────────────────

def _run_entrypoint(workspace: str, entrypoint: str, language: str, timeout: int = 30) -> str:
    """Run the project entrypoint and return stdout/stderr as string."""
    try:
        if language in ("javascript", "node"):
            return run_node(workspace, entrypoint, timeout=timeout)
        return run_python(workspace, entrypoint, timeout=timeout)
    except Exception as exc:
        return f"Error: {exc}"


# ─── Parallel build task ─────────────────────────────────────

def _build_variant(plan: dict, workspace: str, variant_id: int, status_cb=None) -> dict:
    """Build one variant. Designed to run in a thread pool."""
    from agents.builder import run_builder
    _log(f"[BUILDER] Variant #{variant_id} starting in {os.path.basename(workspace)}", status_cb)
    result = run_builder(plan, workspace, variant_id=variant_id, status_cb=status_cb)
    result["workspace_dir"] = workspace
    return result


def _debug_variant(error: str, workspace: str, files: list[str], status_cb=None) -> dict:
    """Debug one variant. Can run concurrently with another variant's debug."""
    from agents.debugger import run_debugger
    return run_debugger(error, workspace, files, status_cb=status_cb)


def _refine_variant(workspace: str, files: list[str], suggestions: list, mismatches: list, status_cb=None) -> dict:
    """Refine one variant. Can run concurrently with debugger."""
    from agents.refiner import run_refiner
    return run_refiner(workspace, files, suggestions=suggestions, mismatches=mismatches)


# ─── Main parallel pipeline ──────────────────────────────────

class ParallelOrchestrator:
    """
    Parallel orchestration engine.

    Architecture:
      1. Planner (serial) → generates plan + interface contract
      2. Builder ×N (parallel threads) → N variant workspaces
      3. Execution (parallel per variant)
      4. Debugger + Refiner (concurrent where applicable)
      5. Judge (serial, deterministic winner selection)
      6. Sync winner → main workspace
    """

    def __init__(
        self,
        workspace_dir: str,
        max_iterations: int = 5,
        num_variants: int = 2,
        parallel: bool = True,
        status_cb: Optional[Callable] = None,
    ):
        self.workspace_dir = workspace_dir
        self.max_iterations = max_iterations
        self.num_variants = num_variants
        self.parallel = parallel
        self.status_cb = status_cb
        self._last_errors: dict[int, str] = {}

    def _log(self, msg: str):
        _log(msg, self.status_cb)

    # ── Phase 1: Plan ────────────────────────────────────────

    def plan(self, task: str) -> dict:
        from agents.planner import run_planner
        self._log(f"\n[PLANNER] Generating plan for: {task}")
        plan = run_planner(task, self.workspace_dir)

        # Recover from non-structured planner output
        if "raw_response" in plan and "files" not in plan:
            self._log("[PLANNER] Recovery: non-structured output — using default scaffold")
            plan = {
                "project_name": os.path.basename(self.workspace_dir),
                "description": task,
                "language": "python",
                "dependencies": [],
                "files": [{"path": "main.py", "purpose": "Main entry point"}],
                "entrypoint": "main.py",
            }

        plan["workspace_dir"] = self.workspace_dir
        self._log(f"[PLANNER] Plan ready: {len(plan.get('files', []))} files, lang={plan.get('language', '?')}")
        return plan

    # ── Phase 2: Build variants (parallel) ───────────────────

    def build_variants(self, plan: dict, iteration: int) -> tuple[list[dict], list[str]]:
        """Build all variants concurrently. Returns (variants, workspace_paths)."""
        n = self.num_variants if iteration == 0 else 1
        variant_workspaces: list[str] = []
        tasks_map: dict[int, str] = {}

        for vid in range(1, n + 1):
            vws = _make_variant_workspace(self.workspace_dir, iteration + 1, vid)
            if iteration == 0:
                _seed_variant(self.workspace_dir, vws)
            variant_workspaces.append(vws)
            tasks_map[vid] = vws

        if self.parallel and n > 1:
            self._log(f"[BUILDER] Running {n} variants in parallel…")
            with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
                futures = {
                    pool.submit(_build_variant, plan, vws, vid, self.status_cb): vid
                    for vid, vws in tasks_map.items()
                }
                variants: list[dict] = [None] * n
                for fut in concurrent.futures.as_completed(futures):
                    vid = futures[fut]
                    try:
                        variants[vid - 1] = fut.result()
                    except Exception as exc:
                        self._log(f"[BUILDER] Variant #{vid} failed: {exc}")
                        variants[vid - 1] = {"files_written": [], "errors": [str(exc)], "workspace_dir": tasks_map[vid]}
        else:
            self._log(f"[BUILDER] Running {n} variant(s) sequentially…")
            variants = []
            for vid, vws in tasks_map.items():
                variants.append(_build_variant(plan, vws, vid, self.status_cb))

        return variants, variant_workspaces

    # ── Phase 3: Execute variants ────────────────────────────

    def execute_variants(
        self, plan: dict, variants: list[dict], variant_workspaces: list[str]
    ) -> list[str]:
        """Execute each variant's entrypoint (parallel or serial)."""
        entrypoint = plan.get("entrypoint", "main.py")
        language = plan.get("language", "python")

        def _exec(args):
            vid, vws = args
            ep = entrypoint
            full = os.path.join(vws, ep)
            if not os.path.isfile(full):
                # Try auto-detect
                from tools.executor import _detect_entrypoint
                detected = _detect_entrypoint(vws)
                if detected:
                    ep = detected
                else:
                    return f"Error: entrypoint '{ep}' not found"
            self._log(f"[EXECUTOR] Running variant #{vid}…")
            return _run_entrypoint(vws, ep, language)

        if self.parallel and len(variants) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(variants)) as pool:
                results = list(pool.map(_exec, enumerate(variant_workspaces, 1)))
        else:
            results = [_exec((i + 1, vws)) for i, vws in enumerate(variant_workspaces)]

        return results

    # ── Phase 4: Debug + Refine (SEQUENTIAL — no race conditions) ──

    def debug_and_refine(
        self,
        error_output: str,
        chosen_workspace: str,
        verdict: Optional[dict] = None,
    ) -> tuple[dict, dict]:
        """
        Run debugger then refiner SEQUENTIALLY on the same workspace.
        Previously concurrent — caused race conditions with both agents
        modifying the same files simultaneously.
        Returns (debug_result, refine_result).
        """
        files = _get_project_files(chosen_workspace)
        suggestions = verdict.get("suggestions", []) if verdict else []
        mismatches = verdict.get("issues", []) if verdict else []

        # Debugger first: fix errors
        debug_result = _debug_variant(error_output, chosen_workspace, files, self.status_cb)

        # Refiner second: polish after debug fixes have landed
        # Re-read files in case debugger created/modified them
        files = _get_project_files(chosen_workspace)
        refine_result = _refine_variant(chosen_workspace, files, suggestions, mismatches, self.status_cb)

        return debug_result, refine_result

    # ── Phase 5: Judge ───────────────────────────────────────

    def judge(self, task: str, variants: list[dict], exec_results: list[str], chosen_workspace: str) -> dict:
        from agents.judge import run_judge
        self._log("[JUDGE] Evaluating variants…")
        return run_judge(task, variants, exec_results, workspace_dir=chosen_workspace)

    # ── Main run loop ────────────────────────────────────────

    def run(self, task: str) -> Optional[dict]:
        """Execute the full parallel pipeline. Returns final result dict or None."""
        os.makedirs(self.workspace_dir, exist_ok=True)

        # ── Graphify context: ensure index exists (lazy, no re-scan if cached) ──
        try:
            from codebase.indexer import Indexer, INDEX_FILE_NAME
            index_path = os.path.join(self.workspace_dir, INDEX_FILE_NAME)
            if not os.path.exists(index_path):
                indexer = Indexer(self.workspace_dir)
                indexer.update_index()
                self._log(f"[orchestrator] Built Graphify index for {self.workspace_dir}")
            else:
                self._log(f"[orchestrator] Graphify index already cached — skipping re-scan")
        except ImportError:
            pass

        plan = self.plan(task)

        # Install deps
        from orchestrator import _clean_dependencies, _install_python_deps, _install_node_deps
        deps = _clean_dependencies(plan.get("dependencies", []), plan.get("language", "python"))
        if deps:
            if plan.get("language", "python") == "python":
                _install_python_deps(deps, self.workspace_dir)
            else:
                _install_node_deps(deps, self.workspace_dir)

        best_result = None
        session_log = {
            "task": task,
            "workspace": self.workspace_dir,
            "started": datetime.now().isoformat(),
            "iterations": [],
            "plan": plan,
        }

        for iteration in range(self.max_iterations):
            iter_log: dict = {"iteration": iteration + 1, "timestamp": datetime.now().isoformat()}
            self._log(f"\n{'─' * 60}")
            self._log(f"ITERATION {iteration + 1}/{self.max_iterations}")
            self._log(f"{'─' * 60}")

            # ── Build ─────────────────────────────────────────────
            variants, variant_workspaces = self.build_variants(plan, iteration)
            iter_log["variants"] = [v.get("files_written", []) for v in variants]

            # ── Execute ───────────────────────────────────────────
            exec_results = self.execute_variants(plan, variants, variant_workspaces)
            iter_log["execution"] = exec_results

            # ── Choose best workspace ─────────────────────────────
            chosen_workspace = variant_workspaces[0] if variant_workspaces else self.workspace_dir
            verdict: Optional[dict] = None

            has_error = any(
                "error" in r.lower() or "traceback" in r.lower() or "exit_code: 1" in r.lower()
                for r in exec_results
            )

            # ── Judge (if multiple variants) ──────────────────────
            if len(variants) > 1 and exec_results:
                verdict = self.judge(task, variants, exec_results, chosen_workspace)
                iter_log["judge"] = verdict
                best_idx = max(0, min(len(variants) - 1, verdict.get("best_variant", 1) - 1))
                chosen_workspace = variant_workspaces[best_idx]
                # Recompute has_error for the SELECTED best variant only
                if best_idx < len(exec_results):
                    best_exec = exec_results[best_idx]
                    has_error = (
                        "error" in best_exec.lower()
                        or "traceback" in best_exec.lower()
                        or "exit_code: 1" in best_exec.lower()
                    )

            _sync_to_workspace(chosen_workspace, self.workspace_dir)

            if not has_error:
                if verdict and verdict.get("verdict") == "refine":
                    self._log("[REFINER] Judge requested refinement…")
                    _, refine_result = self.debug_and_refine("", chosen_workspace, verdict)
                    iter_log["refine"] = refine_result
                    # Re-run after refine
                    ep = plan.get("entrypoint", "main.py")
                    rerun = _run_entrypoint(chosen_workspace, ep, plan.get("language", "python"))
                    exec_results = [rerun]
                    has_error = "error" in rerun.lower() or "traceback" in rerun.lower()
                    _sync_to_workspace(chosen_workspace, self.workspace_dir)

                if not has_error:
                    self._log("[EXECUTOR] ✓ Success!")
                    best_result = {
                        "verdict": verdict or {"verdict": "accept", "score": 10, "best_variant": 1},
                        "execution": exec_results,
                        "workspace": self.workspace_dir,
                    }
                    session_log["iterations"].append(iter_log)
                    break

            # ── Debug + Refine concurrently ───────────────────────
            self._log("[DEBUGGER+REFINER] Running concurrently…")
            error_output = "\n\n".join(exec_results) if exec_results else "Missing entrypoint"
            self._log(f"[ERROR]\n{error_output[:500]}")

            debug_result, refine_result = self.debug_and_refine(error_output, chosen_workspace, verdict)
            iter_log["debug"] = debug_result
            iter_log["refine"] = refine_result

            # Re-run if debugger fixed
            if debug_result.get("fixed"):
                self._log("[EXECUTOR] Re-running after debug fix…")
                ep = plan.get("entrypoint", "main.py")
                rerun = _run_entrypoint(chosen_workspace, ep, plan.get("language", "python"))
                exec_results = [rerun]
                iter_log["execution_after_debug"] = exec_results
                _sync_to_workspace(chosen_workspace, self.workspace_dir)
                if not ("error" in rerun.lower() or "traceback" in rerun.lower()):
                    self._log("[EXECUTOR] ✓ Debug fix worked!")
                    best_result = {
                        "verdict": verdict or {"verdict": "accept", "score": 8, "best_variant": 1},
                        "execution": exec_results,
                        "workspace": self.workspace_dir,
                    }
                    session_log["iterations"].append(iter_log)
                    break

            best_result = {
                "verdict": verdict or {"verdict": "retry", "score": 5, "best_variant": 1},
                "execution": exec_results,
                "workspace": self.workspace_dir,
            }
            session_log["iterations"].append(iter_log)

        # ── Save log ──────────────────────────────────────────
        logs_dir = os.path.join(os.path.dirname(self.workspace_dir), "..", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, f"session_{int(time.time())}.json")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(session_log, f, indent=2, default=str)
        except Exception:
            pass

        return best_result
