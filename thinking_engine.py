"""
thinking_engine.py - Multi-agent thinking and synthesis engine.

Implements a debate-style pipeline:
decompose -> initial takes -> cross critique -> refinement -> voting -> synthesis.
"""

import json
import re
from typing import Generator

from model_router import call_model

AGENTS = [
    {
        "name": "Architect",
        "focus": "Focus on system design, decomposition, interfaces, and extensibility.",
    },
    {
        "name": "Engineer",
        "focus": "Focus on concrete implementation details, correctness, and deliverable steps.",
    },
    {
        "name": "Critic",
        "focus": "Focus on flaws, hidden assumptions, regressions, and edge cases.",
    },
    {
        "name": "Optimizer",
        "focus": "Focus on latency, throughput, resource usage, and simplification opportunities.",
    },
    {
        "name": "Realist",
        "focus": "Focus on practical tradeoffs, sequencing, and what will work reliably today.",
    },
]


def _shorten(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _extract_json(text: str) -> dict | None:
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = fenced or [text.strip()]
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _role_prompt(role: str, task: str, context: str, decomposition: str = "", peer_context: str = "") -> str:
    focus = next((agent["focus"] for agent in AGENTS if agent["name"] == role), "")
    return f"""You are the {role} in a panel of agents.
{focus}

Task:
{task}

Context:
{context or "(none)"}

Problem decomposition:
{decomposition or "(not provided)"}

Peer context:
{peer_context or "(none)"}

Respond in markdown with:
1. Your recommended approach
2. Key tradeoffs
3. Concrete next actions
Keep it direct and high signal."""


def _vote_prompt(task: str, decomposition: str, refined_views: dict[str, str]) -> str:
    views = []
    for role, text in refined_views.items():
        views.append(f"## {role}\n{_shorten(text, 600)}")
    return f"""You are the voting coordinator for a multi-agent reasoning panel.

Task:
{task}

Decomposition:
{decomposition}

Refined proposals:
{chr(10).join(views)}

Return ONLY JSON:
{{
  "winner": "agent name",
  "confidence": 0.0,
  "reasoning": "short explanation",
  "best_points": [
    {{"agent": "name", "point": "idea to preserve"}}
  ]
}}"""


def _synthesis_prompt(task: str, context: str, decomposition: str, refined_views: dict[str, str], vote: dict) -> str:
    views = []
    for role, text in refined_views.items():
        views.append(f"## {role}\n{_shorten(text, 700)}")
    return f"""You are niggativity's master synthesizer.

Task:
{task}

Context:
{context or "(none)"}

Decomposition:
{decomposition}

Voting result:
{json.dumps(vote, indent=2)}

Refined agent views:
{chr(10).join(views)}

Produce the final answer for the user in markdown.
Include:
- a short final recommendation
- the best merged plan
- major risks or caveats
- a confidence score line at the end formatted exactly as: Confidence: NN%"""


def _decompose_task(task: str, context: str) -> str:
    prompt = f"""Break this task into 3-6 practical concerns or steps.

Task:
{task}

Context:
{context or "(none)"}

Use markdown bullets only."""
    return call_model(
        role="think",
        prompt=prompt,
        system_prompt="You decompose software tasks into clear concerns before solutioning.",
        temperature=0.2,
    )


def _initial_perspective(role: str, task: str, context: str, decomposition: str) -> str:
    return call_model(
        role="think",
        prompt=_role_prompt(role, task, context, decomposition=decomposition),
        system_prompt=f"You are the {role}. Stay in role and be concise.",
        temperature=0.35,
    )


def _cross_critique(role: str, task: str, context: str, decomposition: str, peers: dict[str, str]) -> str:
    peer_context = []
    for peer_role, text in peers.items():
        if peer_role == role:
            continue
        peer_context.append(f"### {peer_role}\n{_shorten(text, 500)}")
    prompt = f"""You are {role}. Critique the other agents and sharpen the solution.

Return markdown with:
1. What the other agents got right
2. What they missed
3. Your revised recommendation

{_role_prompt(role, task, context, decomposition=decomposition, peer_context=chr(10).join(peer_context))}"""
    return call_model(
        role="think",
        prompt=prompt,
        system_prompt=f"You are the {role}. Critique rigorously but constructively.",
        temperature=0.3,
    )


def _vote(task: str, decomposition: str, refined_views: dict[str, str]) -> dict:
    response = call_model(
        role="think",
        prompt=_vote_prompt(task, decomposition, refined_views),
        system_prompt="You return only valid JSON for the panel vote.",
        temperature=0.2,
    )
    parsed = _extract_json(response)
    if parsed:
        return parsed

    return {
        "winner": next(iter(refined_views.keys()), "Architect"),
        "confidence": 0.65,
        "reasoning": "Fallback vote because the structured result could not be parsed.",
        "best_points": [],
    }


def synthesize_thought(task: str, context: str) -> Generator[str, None, None]:
    """
    Run the debate-style multi-agent thinking pipeline.
    Yields thought text first, then streams the final synthesis.
    """
    yield "<thought>\n"
    yield "Starting Multi-Agent Thinking Engine...\n\n"

    yield "### Phase 1: Decomposition\n"
    decomposition = _decompose_task(task, context)
    yield decomposition + "\n\n"

    initial_views = {}
    yield "### Phase 2: Initial Perspectives\n"
    for agent in AGENTS:
        role = agent["name"]
        yield f"**{role}** is drafting a first take...\n"
        response = _initial_perspective(role, task, context, decomposition)
        initial_views[role] = response
        yield f"> {_shorten(response)}\n\n"

    refined_views = {}
    yield "### Phase 3: Cross-Critique\n"
    for agent in AGENTS:
        role = agent["name"]
        yield f"**{role}** is critiquing the panel...\n"
        response = _cross_critique(role, task, context, decomposition, initial_views)
        refined_views[role] = response
        yield f"> {_shorten(response)}\n\n"

    yield "### Phase 4: Voting\n"
    vote = _vote(task, decomposition, refined_views)
    confidence = vote.get("confidence", 0.65)
    yield f"Winner: {vote.get('winner', 'Architect')}\n"
    yield f"Reasoning: {_shorten(vote.get('reasoning', 'No reasoning provided.'))}\n"
    yield f"Confidence seed: {int(float(confidence) * 100)}%\n\n"

    yield "</thought>\n"

    synthesis_prompt = _synthesis_prompt(task, context, decomposition, refined_views, vote)
    yield from call_model(
        role="think",
        prompt=synthesis_prompt,
        system_prompt="You synthesize the best ideas from a multi-agent reasoning panel.",
        temperature=0.25,
        stream=True,
    )
