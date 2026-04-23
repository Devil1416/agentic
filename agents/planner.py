"""
agents/planner.py — Planning agent.

Takes a user task and outputs a STRICT JSON plan including:
  - files to create
  - dependencies
  - entrypoint
  - architecture reasoning
"""

import json
from model_router import call_model
from tool_registry import get_tools_description
from memory.vector_store import get_relevant_context

PLANNER_SYSTEM = """You are a senior software architect. Your role is to create detailed implementation plans.

Given a task, you MUST output a JSON plan with this EXACT structure:

```json
{
  "action": "done",
  "args": {
    "result": {
      "project_name": "name",
      "description": "what this project does",
      "architecture": "brief architecture description",
      "language": "python",
      "frontend": null,
      "backend": null,
      "communication": null,
      "dependencies": ["dep1", "dep2"],
      "files": [
        {
          "path": "relative/path/to/file.py",
          "purpose": "what this file does"
        }
      ],
      "entrypoint": "main.py",
      "build_steps": ["step1", "step2"],
      "existing_files_to_modify": [
        {
          "path": "relative/path/to/existing_file.py",
          "purpose": "why we are modifying this file"
        }
      ],
      "subtasks": [
        {
          "name": "subtask name",
          "description": "what this subtask does",
          "files": ["file1.py"]
        }
      ]
    }
  }
}
```

For FULLSTACK projects, fill in frontend/backend/communication:
  "frontend": "React + Vite" or "vanilla HTML/CSS/JS" or null,
  "backend": "FastAPI" or "Express" or "Flask" or null,
  "communication": "REST" or "GraphQL" or "WebSocket" or null,

For subtasks, break the project into sequential phases:
  e.g. "setup backend" -> "create API" -> "build frontend" -> "connect API" -> "test"

Rules:
- Output ONLY valid JSON, no explanations
- Be specific about file paths and purposes
- Keep it practical and minimal
- Consider the dependencies carefully
- The entrypoint must be one of the files listed
- For fullstack: include both frontend and backend files
- Always include subtasks for complex projects
"""


def run_planner(task: str, workspace_dir: str) -> dict:
    """
    Generate an implementation plan for a given task.

    Args:
        task: User's request describing what to build.
        workspace_dir: Directory where the project will be created.

    Returns:
        Parsed plan dictionary.
    """
    # Fetch relevant memories and codebase context
    memory_context = get_relevant_context(task)
    
    codebase_context = ""
    try:
        from codebase.retriever import get_context_for_prompt
        codebase_context = get_context_for_prompt(task, workspace_dir, top_k=5)
    except Exception:
        pass

    prompt = f"""Task: {task}

Workspace: {workspace_dir}

Codebase Context:
{codebase_context}

Memory:
{memory_context}

Create a detailed implementation plan. Output ONLY the JSON plan, nothing else.
Remember to wrap your response in the exact format shown in the system prompt."""

    print("\n" + "=" * 60)
    print("🧠 PLANNER — Generating architecture plan...")
    print("=" * 60)

    response = call_model(
        role="planner",
        prompt=prompt,
        system_prompt=PLANNER_SYSTEM,
        temperature=0.2,
    )

    plan = _extract_plan(response)
    if plan:
        print(f"\n✅ Plan: {plan.get('project_name', 'unnamed')}")
        print(f"   Files: {len(plan.get('files', []))}")
        print(f"   Entry: {plan.get('entrypoint', 'N/A')}")
        print(f"   Lang:  {plan.get('language', 'N/A')}")
    else:
        print("\n⚠ Could not parse plan, using raw response")

    return plan or {"raw_response": response}


def _extract_plan(text: str) -> dict | None:
    """Extract the plan JSON from model output."""
    import re

    # Try fenced JSON blocks
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    for block in fenced:
        try:
            obj = json.loads(block)
            # Handle wrapped format
            if "action" in obj and "args" in obj:
                result = obj["args"].get("result", obj["args"])
                if isinstance(result, dict):
                    return result
            if "files" in obj:
                return obj
        except json.JSONDecodeError:
            continue

    # Try raw JSON
    try:
        obj = json.loads(text.strip())
        if "action" in obj and "args" in obj:
            result = obj["args"].get("result", obj["args"])
            if isinstance(result, dict):
                return result
        if "files" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    # Try to find any JSON object with "files" key
    matches = re.findall(r'\{[^{}]*"files"\s*:\s*\[.*?\].*?\}', text, re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue

    return None
