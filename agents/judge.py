"""
agents/judge.py — Solution evaluation agent.

Compares build variants, evaluates quality, and decides next action.
"""

import json
from model_router import call_model

JUDGE_SYSTEM = """You are a senior code reviewer and quality judge.

You evaluate code solutions based on:
1. Correctness — does it work?
2. Completeness — are all requirements met?
3. Code quality — clean, readable, well-structured?
4. Error handling — robust against edge cases?

You MUST output your verdict as JSON:

```json
{
  "action": "done",
  "args": {
    "result": {
      "verdict": "accept" or "retry" or "refine",
      "best_variant": 1 or 2,
      "score": 0-10,
      "reasoning": "explanation",
      "issues": ["issue1", "issue2"],
      "suggestions": ["suggestion1"]
    }
  }
}
```

Verdicts:
- "accept": Solution works and meets requirements
- "refine": Solution mostly works but needs polish
- "retry": Solution has fundamental issues, needs rebuild
"""


def run_judge(task: str, variants: list[dict], execution_results: list[str]) -> dict:
    """
    Judge the quality of build variants.

    Args:
        task: Original user task.
        variants: List of build variant summaries.
        execution_results: Execution output for each variant.

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
        print(f"   Score: {verdict.get('score', '?')}/10")
        print(f"   Verdict: {verdict.get('verdict', '?')}")
        print(f"   Reasoning: {verdict.get('reasoning', 'N/A')[:100]}")
    else:
        # Default to refine if can't parse
        verdict = {
            "verdict": "refine",
            "best_variant": 1,
            "score": 5,
            "reasoning": "Could not parse judge output, defaulting to refine.",
            "issues": [],
            "suggestions": [],
        }

    return verdict


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
    import re

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
