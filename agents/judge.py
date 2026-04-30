# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
agents/judge.py — Solution evaluation agent.

Compares build variants, evaluates quality, and decides next action.
After scoring, performs strict cross-file validation against contract.json.
"""

import json
import os
import re
from model_router import call_model

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Reflexion",
"integrity": "b25522cfe935",
}
# ─── /fingerprint ───────────────────────────────────────────


JUDGE_SYSTEM = """You are a senior code reviewer and quality judge.

You evaluate code solutions based on:
1. Correctness — does it work?
2. Completeness — are all requirements met?
3. Code quality — clean, readable, well-structured?
4. Error handling — robust against edge cases?

You MUST output your verdict as STRICT JSON:

```json
{
  "verdict": "accept" or "retry" or "refine",
  "best_variant": 1 or 2,
  "score": 0-10,
  "reasoning": "explanation"
}
```

Verdicts:
- "accept": Solution works and meets requirements
- "refine": Solution mostly works but needs polish
- "retry": Solution has fundamental issues, needs rebuild
"""


def run_judge(task: str, variants: list[dict], execution_results: list[str],


              workspace_dir: str = None) -> dict:
    """
    Judge the quality of build variants.

    Args:
        task: Original user task.
        variants: List of build variant summaries.
        execution_results: Execution output for each variant.
        workspace_dir: Variant workspace root to validate against contract.

    Returns:
        Verdict dict with decision and reasoning.
    """
    print(f"\n{'=' * 60}")
    print(f"⚖️  JUDGE — Evaluating solutions...")
    print(f"{'=' * 60}")

    variants_text = ""
    for i, (variant, exec_result) in enumerate(zip(variants, execution_results), 1):
        files = variant.get("files_written", [])
        errors = variant.get("errors", [])
        variants_text += f"""
--- Variant #{i} ---
Files written: {len(files)}
  {chr(10).join(f'  - {f}' for f in files)}
Build errors: {len(errors)}
  {chr(10).join(f'  - {e}' for e in errors)}

Execution output:
{exec_result}
"""

    prompt = f"""Original Task: {task}

{variants_text}

Evaluate the solution(s) and provide your verdict.
Consider: Does the code actually run? Are there errors? Is the output correct?

Output your verdict as JSON."""

    try:
        response = call_model(
            role="judge",
            prompt=prompt,
            system_prompt=JUDGE_SYSTEM,
            temperature=0.1,
        )
        verdict = _extract_verdict(response)
    except Exception as e:
        print(f"   Judge fallback: {e}")
        verdict = _heuristic_verdict(execution_results)

    if verdict:
        best_var = verdict.get("best_variant")
        if best_var is None:
            verdict["best_variant"] = 1
        print(f"   Score: {verdict.get('score', '?')}/10")
        print(f"   Verdict: {verdict.get('verdict', '?')}")
        print(f"   Reasoning: {verdict.get('reasoning', 'N/A')[:100]}")
    else:
        verdict = {
            "verdict": "refine",
            "best_variant": 1,
            "score": 5,
            "reasoning": "Could not parse judge output, defaulting to refine.",
            "issues": [],
            "suggestions": [],
        }

    # ── Strict cross-file contract validation ────────────────────────────
    if workspace_dir:
        mismatches = _validate_contract(workspace_dir, variants, verdict)
        if mismatches:
            verdict["verdict"] = "refine"
            verdict["issues"] = verdict.get("issues", []) + mismatches
            verdict["suggestions"] = verdict.get("suggestions", []) + [
                f"Fix mismatch: {m}" for m in mismatches
            ]
            print(f"   [JUDGE] Contract violations found ({len(mismatches)}):")
            for m in mismatches:
                print(f"      ✗ {m}")
        else:
            print(f"   [JUDGE] Contract validation passed ✓")
    # ─────────────────────────────────────────────────────────────────────

    return verdict


def _validate_contract(workspace_dir: str, variants: list[dict], verdict: dict) -> list[str]:
    """Perform strict cross-file validation against contract.json.

    Checks:
    1. html_ids exist in HTML AND are referenced in JS
    2. api_routes are declared as @app.route in Flask files
    3. JS fetch calls use api_base (not relative paths)
    4. script/src/href references match static_files and exist on disk
    """
    contract_path = os.path.join(workspace_dir, "contract.json")
    if not os.path.exists(contract_path):
        return ["contract.json missing — cannot validate"]

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)
    except Exception as e:
        return [f"contract.json unreadable: {e}"]

    mismatches = []
    api_base = contract.get("api_base", "http://localhost:5000")
    api_routes = contract.get("api_routes", [])
    static_files = contract.get("static_files", {})
    html_ids = contract.get("html_ids", [])

    # Collect file contents
    html_content = ""
    js_content = ""
    py_content = ""

    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in {".variants", ".git", "__pycache__", "node_modules"}]
        for fn in files:
            fpath = os.path.join(root, fn)
            try:
                text = open(fpath, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if fn.endswith(".html"):
                html_content += text + "\n"
            elif fn.endswith(".js"):
                js_content += text + "\n"
            elif fn.endswith(".py"):
                py_content += text + "\n"

    # 1. Validate html_ids exist in HTML
    if html_ids:
        for hid in html_ids:
            if f'id="{hid}"' not in html_content and f"id='{hid}'" not in html_content:
                mismatches.append(f"html_id '{hid}' not found in any HTML file")

    # 2. Validate html_ids are referenced in JS
    if html_ids:
        for hid in html_ids:
            if html_content and (f'getElementById("{hid}")' not in js_content
                                 and f"getElementById('{hid}')" not in js_content
                                 and f'querySelector("#' + hid + '"' not in js_content
                                 and f"querySelector('#" + hid + "'" not in js_content):
                mismatches.append(f"html_id '{hid}' not referenced in any JS file")

    # 3. Validate api_routes are declared as @app.route in Flask files
    if api_routes:
        for route in api_routes:
            # strip variable segments for basic route matching
            base_route = re.sub(r"/<[^>]+>", "", route).rstrip("/") or "/"
            if py_content and f'@app.route("{base_route}"' not in py_content and f"@app.route('{base_route}'" not in py_content:
                mismatches.append(f"api_route '{route}' not declared as @app.route in any Python file")

    # 4. Validate JS fetch calls use api_base, not relative paths
    fetch_calls = re.findall(r'fetch\(([^)]+)\)', js_content)
    for call in fetch_calls:
        call_stripped = call.strip().strip('"\'')
        if call_stripped.startswith("/") and not call_stripped.startswith(api_base):
            mismatches.append(
                f"JS fetch uses relative path '{call_stripped[:60]}' — must use api_base '{api_base}'"
            )

    # 5. Validate static_files exist on disk and are referenced correctly
    paths = static_files.values() if isinstance(static_files, dict) else static_files
    for rel_path in paths:
        if not rel_path or not isinstance(rel_path, str):
            continue
        abs_path = os.path.join(workspace_dir, rel_path)
        if not os.path.exists(abs_path):
            mismatches.append(f"static_file expected at '{rel_path}' but file does not exist")
        # Check HTML references the exact rel_path
        if html_content and rel_path not in html_content:
            mismatches.append(f"HTML does not reference static_file path '{rel_path}'")

    return mismatches


def _heuristic_verdict(execution_results: list[str]) -> dict:
    """Fallback verdict when the judge model is unavailable."""
    best_variant = 1
    saw_success = False

    for idx, result in enumerate(execution_results, start=1):
        failed = "error" in result.lower() or "traceback" in result.lower() or "exit_code: 1" in result.lower()
        if not failed:
            best_variant = idx
            saw_success = True
            break

    if saw_success:
        return {
            "verdict": "accept",
            "best_variant": best_variant,
            "score": 8,
            "reasoning": "Fallback heuristic selected the first successful variant.",
            "issues": [],
            "suggestions": [],
        }

    return {
        "verdict": "retry",
        "best_variant": 1,
        "score": 3,
        "reasoning": "All variants failed execution during heuristic fallback.",
        "issues": ["Execution failed for every variant."],
        "suggestions": ["Rebuild or debug the project before continuing."],
    }


def _extract_verdict(text: str) -> dict | None:
    """Extract verdict JSON from judge output."""

    # Try fenced JSON
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    for block in fenced:
        try:
            obj = json.loads(block)
            if "action" in obj:
                result = obj.get("args", {}).get("result", {})
                if isinstance(result, dict) and "verdict" in result:
                    return result
            if "verdict" in obj:
                return obj
        except json.JSONDecodeError:
            continue

    # Try raw JSON
    try:
        obj = json.loads(text.strip())
        if "action" in obj:
            result = obj.get("args", {}).get("result", {})
            if isinstance(result, dict):
                return result
        if "verdict" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    # Extract verdict keyword from free text
    text_lower = text.lower()
    if "accept" in text_lower:
        return {"verdict": "accept", "score": 7, "reasoning": text[:200],
                "best_variant": 1, "issues": [], "suggestions": []}
    elif "retry" in text_lower:
        return {"verdict": "retry", "score": 3, "reasoning": text[:200],
                "best_variant": 1, "issues": [], "suggestions": []}

    return None


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Reflexion. Tampering with attribution is detectable.
