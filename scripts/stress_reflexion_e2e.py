from __future__ import annotations

import compileall
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RUN_ID = time.strftime("%Y%m%d_%H%M%S")
WORKSPACE_NAME = f"stress_e2e_{RUN_ID}"
REPORT_PATH = ROOT / "logs" / f"stress_e2e_{RUN_ID}.json"
PHASE_PREFIXES = ("[PLANNER]", "[BUILDER]", "[EXECUTOR]", "[DEBUGGER", "[JUDGE]", "[REFINER]")


def now() -> float:
    return time.perf_counter()


def stage(report: dict, name: str):
    class StageTimer:
        def __enter__(self):
            self.start = now()
            print(f"\n=== STAGE {name} ===", flush=True)
            return self

        def __exit__(self, exc_type, exc, tb):
            elapsed = now() - self.start
            report.setdefault("timings", {})[name] = round(elapsed, 3)
            if exc:
                report.setdefault("errors", {})[name] = "".join(traceback.format_exception(exc_type, exc, tb))[-4000:]
                print(f"STAGE {name}: FAIL in {elapsed:.2f}s: {exc}", flush=True)
                return True
            print(f"STAGE {name}: OK in {elapsed:.2f}s", flush=True)
            return False

    return StageTimer()


def run_cmd(args: list[str], cwd: Path = ROOT, timeout: int = 120) -> dict:
    start = now()
    proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    return {
        "args": args,
        "returncode": proc.returncode,
        "elapsed_s": round(now() - start, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def detect_entrypoint(workspace: Path) -> Path | None:
    candidates = [
        "main.py",
        "app.py",
        "cli.py",
        "app/main.py",
        "src/main.py",
        "insight_cli/main.py",
    ]
    for rel in candidates:
        path = workspace / rel
        if path.is_file():
            return path
    for path in workspace.rglob("*.py"):
        if "__pycache__" not in path.parts and ".variants" not in path.parts:
            if path.name in {"main.py", "app.py", "cli.py"}:
                return path
    return None


def list_project_files(workspace: Path) -> list[str]:
    if not workspace.exists():
        return []
    ignored = {".variants", "__pycache__", ".git", ".venv", "node_modules"}
    files: list[str] = []
    for path in workspace.rglob("*"):
        if path.is_file() and not any(part in ignored for part in path.parts):
            files.append(path.relative_to(workspace).as_posix())
    return sorted(files)


def main() -> int:
    os.chdir(ROOT)
    (ROOT / "logs").mkdir(exist_ok=True)
    report: dict = {
        "run_id": RUN_ID,
        "workspace_name": WORKSPACE_NAME,
        "workspace": str(ROOT / "workspace" / WORKSPACE_NAME),
        "timings": {},
        "checks": {},
        "errors": {},
    }

    with stage(report, "cli_surface"):
        reflexion = shutil.which("reflexion")
        help_result = run_cmd([sys.executable, "cli.py", "--help"], timeout=60)
        help_text = help_result["stdout_tail"] + help_result["stderr_tail"]
        report["checks"]["cli_surface"] = {
            "reflexion_binary": reflexion,
            "cli_help_returncode": help_result["returncode"],
            "literal_subcommands_present": {
                verb: (f" {verb}" in help_text or f"/{verb}" in help_text)
                for verb in ("build", "run", "fix", "test")
            },
            "help_tail": help_text[-1000:],
        }

    with stage(report, "api_surface"):
        from fastapi.testclient import TestClient
        from api.app import create_app

        client = TestClient(create_app())
        health = client.get("/health")
        models = client.get("/v1/models")
        tokens = client.post(
            "/v1/messages/count_tokens",
            json={"model": "reflexion-auto", "messages": [{"role": "user", "content": "hello world"}]},
        )
        report["checks"]["api_surface"] = {
            "health": {"status_code": health.status_code, "json": health.json()},
            "models": {"status_code": models.status_code, "count": len(models.json().get("data", []))},
            "count_tokens": {"status_code": tokens.status_code, "json": tokens.json()},
        }

    with stage(report, "model_router_fallback"):
        import model_router

        original_get_models = model_router.get_installed_models
        original_blocking = model_router._blocking_response
        original_failures = dict(model_router._model_failure_until)
        attempts: list[str] = []

        def fake_models() -> list[str]:
            return ["mixtral:latest", "deepseek-coder:6.7b", "llama3:8b", "gemma4:latest", "gemma:7b"]

        def fake_blocking(payload: dict) -> str:
            attempts.append(payload["model"])
            if len(attempts) == 1:
                raise RuntimeError("simulated provider failure")
            return "fallback-ok"

        try:
            model_router.get_installed_models = fake_models
            model_router._blocking_response = fake_blocking
            result = model_router.call_model("builder", "router stress probe", stream=False)
        finally:
            model_router.get_installed_models = original_get_models
            model_router._blocking_response = original_blocking
            model_router._model_failure_until.clear()
            model_router._model_failure_until.update(original_failures)

        chat_candidates = model_router.get_candidate_models(
            "chat",
            ["mixtral:latest", "deepseek-coder:6.7b", "llama3:8b", "gemma4:latest", "gemma:7b"],
        )
        report["checks"]["model_router_fallback"] = {
            "result": result,
            "attempts": attempts,
            "fallback_used": len(attempts) >= 2 and result == "fallback-ok",
            "chat_candidates": chat_candidates,
            "chat_avoids_heavy_first": bool(chat_candidates and chat_candidates[0] not in {"mixtral:latest", "deepseek-coder:6.7b"}),
        }

    with stage(report, "dependency_setup"):
        from tools.executor import install_dependencies

        dep_workspace = ROOT / "workspace" / f"stress_deps_{RUN_ID}"
        dep_workspace.mkdir(parents=True, exist_ok=True)
        install_result = install_dependencies(str(dep_workspace), language="python", deps=["colorama==0.4.6"])
        python_exe = dep_workspace / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        verify = run_cmd([str(python_exe), "-c", "import colorama; print(colorama.__version__)"], cwd=dep_workspace, timeout=60)
        report["checks"]["dependency_setup"] = {
            "workspace": str(dep_workspace),
            "install_tail": install_result[-2000:],
            "verify": verify,
            "passed": verify["returncode"] == 0,
        }

    task = (
        "Build a non-trivial Python multi-module CLI application named insight_cli. "
        "It must analyze CSV and JSON event logs using internal APIs and cross-module interactions. "
        "Use separate planned subtasks for core logic, utilities, integration/router, and tests. "
        "Use colorama as a dependency and include dependency metadata. "
        "Write all artifacts to files in the workspace, never print source code as the result. "
        "Required files should include an executable main.py or app/main.py, core models/analyzer modules, "
        "a utility formatting module, an internal command/router module, and tests or a smoke validation module. "
        "The executable must run without arguments using built-in sample data and print total events, unique users, "
        "top action, and a SMOKE PASS marker. Keep it terminal-only, no web server."
    )

    with stage(report, "autonomous_build_pipeline"):
        from orchestrator import init_tools, run

        init_tools()
        status_events: list[dict] = []
        phase_times: dict[str, dict] = {}
        build_start = now()

        def status_cb(message: str):
            elapsed = round(now() - build_start, 3)
            status_events.append({"t": elapsed, "message": message})
            print(f"[stress-status +{elapsed:07.3f}s] {message}", flush=True)
            for prefix in PHASE_PREFIXES:
                if prefix in message:
                    data = phase_times.setdefault(prefix, {"first_s": elapsed, "last_s": elapsed, "count": 0})
                    data["last_s"] = elapsed
                    data["count"] += 1

        result = run(
            task,
            workspace_name=WORKSPACE_NAME,
            status_cb=status_cb,
            max_iterations=3,
            parallel=True,
        )
        report["checks"]["autonomous_build_pipeline"] = {
            "result": result,
            "status_event_count": len(status_events),
            "status_events_tail": status_events[-50:],
            "phase_times": phase_times,
            "parallel_observed": any("parallel" in e["message"].lower() for e in status_events)
            and any("variant #1" in e["message"].lower() for e in status_events)
            and any("variant #2" in e["message"].lower() for e in status_events),
            "pipeline_markers": {
                "planner": any("[PLANNER]" in e["message"] for e in status_events),
                "builder": any("[BUILDER]" in e["message"] for e in status_events),
                "executor": any("[EXECUTOR]" in e["message"] for e in status_events),
                "judge": any("[JUDGE]" in e["message"] for e in status_events),
                "debugger_or_refiner": any("[DEBUGGER" in e["message"] or "[REFINER]" in e["message"] for e in status_events),
            },
        }

    workspace = ROOT / "workspace" / WORKSPACE_NAME

    with stage(report, "artifact_validation_and_run"):
        files = list_project_files(workspace)
        entrypoint = detect_entrypoint(workspace)
        compile_ok = compileall.compile_dir(str(workspace), quiet=1, force=True)
        run_result = None
        if entrypoint:
            run_result = run_cmd([sys.executable, str(entrypoint.relative_to(workspace))], cwd=workspace, timeout=60)
        report["checks"]["artifact_validation_and_run"] = {
            "file_count": len(files),
            "files": files[:80],
            "contract_exists": (workspace / "contract.json").exists(),
            "entrypoint": str(entrypoint.relative_to(workspace)) if entrypoint else None,
            "compile_ok": bool(compile_ok),
            "run_result": run_result,
            "run_passed": bool(run_result and run_result["returncode"] == 0),
        }

    with stage(report, "debugger_fault_injection"):
        from agents.debugger import run_debugger
        from orchestrator import init_tools

        init_tools()
        fault_file = workspace / "fault_injection_debug_probe.py"
        fault_file.write_text(
            "def main():\n"
            "    print('fault probe ready')\n\n"
            "if __name__ == '__main__':\n"
            "    main(\n",
            encoding="utf-8",
        )
        first = run_cmd([sys.executable, fault_file.name], cwd=workspace, timeout=30)
        debug_result = run_debugger(
            (first["stdout_tail"] + "\n" + first["stderr_tail"])[-4000:],
            str(workspace),
            files=[fault_file.name],
            status_cb=lambda m: print(f"[stress-debugger] {m}", flush=True),
        )
        second = run_cmd([sys.executable, fault_file.name], cwd=workspace, timeout=30)
        report["checks"]["debugger_fault_injection"] = {
            "initial_returncode": first["returncode"],
            "initial_stderr_tail": first["stderr_tail"][-1000:],
            "debug_result": debug_result,
            "rerun": second,
            "fixed": first["returncode"] != 0 and second["returncode"] == 0,
        }

    with stage(report, "test_command_validation"):
        tests_dir = workspace / "tests"
        if tests_dir.is_dir():
            test_result = run_cmd([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=workspace, timeout=60)
        else:
            test_result = {
                "returncode": 2,
                "elapsed_s": 0,
                "stdout_tail": "",
                "stderr_tail": "No tests directory generated.",
            }
        report["checks"]["test_command_validation"] = {
            "tests_dir_exists": tests_dir.is_dir(),
            "result": test_result,
            "passed": test_result["returncode"] == 0,
        }

    checks = report["checks"]
    report["success_criteria"] = {
        "literal_reflexion_build_run_fix_test_commands": bool(
            checks.get("cli_surface", {}).get("reflexion_binary")
            and all(checks.get("cli_surface", {}).get("literal_subcommands_present", {}).values())
        ),
        "api_router_reliable": checks.get("api_surface", {}).get("health", {}).get("status_code") == 200
        and checks.get("model_router_fallback", {}).get("fallback_used") is True,
        "dependency_setup": checks.get("dependency_setup", {}).get("passed") is True,
        "autonomous_pipeline": checks.get("autonomous_build_pipeline", {}).get("result") is not None,
        "parallel_agents_observed": checks.get("autonomous_build_pipeline", {}).get("parallel_observed") is True,
        "artifacts_executable": checks.get("artifact_validation_and_run", {}).get("run_passed") is True,
        "debugger_auto_fix": checks.get("debugger_fault_injection", {}).get("fixed") is True,
        "tests_pass": checks.get("test_command_validation", {}).get("passed") is True,
    }
    report["overall_pass"] = all(report["success_criteria"].values())

    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("\n=== STRESS SUMMARY ===", flush=True)
    print(json.dumps({
        "report": str(REPORT_PATH),
        "workspace": str(workspace),
        "timings": report["timings"],
        "success_criteria": report["success_criteria"],
        "overall_pass": report["overall_pass"],
    }, indent=2), flush=True)
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
