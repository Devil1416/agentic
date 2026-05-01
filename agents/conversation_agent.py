# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
agents/conversation_agent.py — Conversational intent classifier and responder.

Determines user intent (CHAT, DISCUSS, EXECUTE, PLAN, DEBUG, SHOW) and either:
  - Responds with lightweight chat (greetings, casual)
  - Responds conversationally (brainstorm, clarify, discuss)
  - Triggers the execution pipeline
  - Handles file exploration requests
"""

import json
import re
from model_router import call_model, call_model_streaming_print
from memory.vector_store import get_relevant_context

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
"integrity": "5a4469994f13",
}
# ─── /fingerprint ───────────────────────────────────────────


CONVERSATION_SYSTEM = """You are reflexion, a local autonomous coding assistant. You are conversational, helpful, and direct.

You are chatting with a developer. Based on their message, decide what to do.

MODES:
- CHAT: casual greetings, small talk, quick questions (lightweight, no code)
- DISCUSS: brainstorming, ideation, comparing approaches, architecture exploration
- EXECUTE: user wants to build/create something specific
- DEBUG: user reports an error or wants to fix something
- PLAN: user wants to see a plan before building
- SHOW: user wants to see files or project contents

RULES:
1. If the user says hi, hello, thanks, or casual chat, choose CHAT
2. If the user gives a clear build task ("build me X", "create a Y"), choose EXECUTE
3. If the user is exploring ideas ("let's think about", "what if", "brainstorm"), choose DISCUSS
4. If the user mentions errors, bugs, "not working", choose DEBUG
5. If the user says "show me", "open", "what did you build", choose SHOW
6. If the user says "plan", "how would you", choose PLAN
7. In CHAT mode, be brief and friendly
8. In DISCUSS mode, explore ideas deeply, suggest architectures, ask follow-ups
9. In EXECUTE/DEBUG/PLAN mode, extract the specific goal

You MUST respond with ONLY a JSON block:

For CHAT mode:
```json
{
  "mode": "CHAT",
  "response": "Brief, friendly response."
}
```

For DISCUSS mode:
```json
{
  "mode": "DISCUSS",
  "response": "Your conversational response here. Explore ideas, ask questions."
}
```

For EXECUTE mode:
```json
{
  "mode": "EXECUTE",
  "goal": "Clear description of what to build",
  "response": "I'll build X for you. Here's what I'm thinking..."
}
```

For DEBUG mode:
```json
{
  "mode": "DEBUG",
  "goal": "What to debug/fix",
  "response": "Let me look into that..."
}
```

For PLAN mode:
```json
{
  "mode": "PLAN",
  "goal": "What to plan",
  "response": "Let me think through the architecture..."
}
```

For SHOW mode:
```json
{
  "mode": "SHOW",
  "target": "file path or 'all'",
  "response": "Here's what we have..."
}
```

Be natural and conversational. You're a developer colleague, not a robot."""


def classify_intent(user_input: str, conversation_context: str = "",


                    current_goal: str = None, current_mode: str = "discuss",
                    self_improvement_mode: bool = False,
                    **kwargs) -> dict:
    """
    Classify user intent and generate appropriate response.

    Args:
        user_input: What the user typed.
        conversation_context: Recent conversation history.
        current_goal: Current active goal (if any).
        current_mode: Current session mode.
        self_improvement_mode: Whether self improvement is active.

    Returns:
        Dict with mode, response, and optional goal/target.
    """
    # Quick pattern matching for obvious intents (skip model call)
    quick = _quick_classify(user_input)
    if quick:
        return quick

    # Build context-rich prompt
    memory_context = get_relevant_context(user_input)

    context_block = ""
    if conversation_context:
        context_block = f"\nRecent conversation:\n{conversation_context}\n"

    goal_block = ""
    if current_goal:
        goal_block = f"\nCurrent active goal: {current_goal}\n"

    prompt = f"""{context_block}{goal_block}{memory_context}

Current mode: {current_mode}

User says: {user_input}

Classify the intent and respond. Output ONLY the JSON block."""

    system_prompt = CONVERSATION_SYSTEM
    if self_improvement_mode:
        system_prompt += "\n\nYou are modifying your own system. Only patch specific functions using edit_file_diff. Do not rewrite entire files. Preserve all unrelated logic."

    response = call_model(
        role="planner",  # Use planner model for reasoning
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.4,
    )

    result = _parse_response(response)

    if not result:
        # Fallback: treat as discussion
        return {
            "mode": "DISCUSS",
            "response": response.strip() if response.strip() else "Could you tell me more about what you'd like to do?",
        }

    return result


def brainstorm(user_input: str, conversation_context: str = "") -> str:
    """
    Pure brainstorm/discussion mode — stream a thoughtful response.

    Returns the full response text.
    """
    context_block = ""
    if conversation_context:
        context_block = f"\nConversation so far:\n{conversation_context}\n"

    prompt = f"""{context_block}

User: {user_input}

Respond as a thoughtful senior developer colleague. Explore ideas, suggest approaches,
compare tradeoffs, ask follow-up questions. Be concise but insightful.
Do NOT output JSON. Respond naturally."""

    system = (
        "You are reflexion, a senior developer assistant. "
        "You're having a natural conversation about software. "
        "Be direct, insightful, and opinionated. Keep responses focused and practical. "
        "Ask follow-up questions when the user's intent is unclear."
    )

    print()
    response = call_model_streaming_print(
        role="planner",
        prompt=prompt,
        system_prompt=system,
        temperature=0.6,
    )
    return response


def chat_respond(user_input: str, conversation_context: str = "") -> str:
    """
    Lightweight chat mode — brief, friendly responses for casual conversation.
    Uses the 'chat' model role for speed.
    """
    context_block = ""
    if conversation_context:
        context_block = f"\nRecent conversation:\n{conversation_context}\n"

    prompt = f"""{context_block}
User: {user_input}

Respond briefly and naturally. Keep it short (1-3 sentences). Be friendly.
Do NOT output JSON. Just respond naturally."""

    system = (
        "You are reflexion, a friendly coding assistant. "
        "Give brief, natural responses to casual chat. Keep it short."
    )

    print()
    response = call_model_streaming_print(
        role="chat",
        prompt=prompt,
        system_prompt=system,
        temperature=0.7,
    )
    return response


def ask_clarification(user_input: str, context: str = "") -> str:
    """Generate a clarifying question when intent is ambiguous."""
    prompt = f"""The user said: "{user_input}"

{context}

Ask 1-2 specific clarifying questions to understand what they want to build.
Be brief and direct. Do NOT output JSON."""

    system = "You are reflexion. Ask short, specific clarifying questions. Be direct."

    print()
    response = call_model_streaming_print(
        role="planner",
        prompt=prompt,
        system_prompt=system,
        temperature=0.5,
    )
    return response


def _quick_classify(text: str) -> dict | None:
    """Fast pattern matching for common intents — avoids model call.

    AUTONOMOUS BUILDER POLICY:
    Any prompt containing build/create/generate keywords OR multi-file
    requirements MUST auto-trigger EXECUTE mode without entering chat
    or asking for confirmation.
    """
    lower = text.lower().strip()

    # ── Image input detection (must come before build patterns) ──
    image_patterns = [
        r'(build this ui|from this image|from this screenshot|this design)',
        r'(implement this|recreate this|clone this).*(ui|design|layout|screen)',
    ]
    for pat in image_patterns:
        if re.search(pat, lower):
            return {
                "mode": "EXECUTE",
                "goal": text,
                "response": "I'll analyze the image and build the UI.",
                "needs_image": True,
            }

    # ── Debug patterns ───────────────────────────────────────────
    debug_patterns = [
        r"(not working|doesn't work|broken|bug|error|fix|crash|fail)",
        r"(debug|troubleshoot|what's wrong|went wrong)",
    ]
    for pat in debug_patterns:
        if re.search(pat, lower):
            return {
                "mode": "DEBUG",
                "goal": text,
                "response": "Let me investigate and fix that.",
            }

    # ── AUTONOMOUS EXECUTE: aggressive build-intent detection ────
    # 1. Explicit build/create/generate keywords (anywhere in text)
    build_keywords = [
        r'\b(build|create|generate|write|implement|code|develop|construct|scaffold|bootstrap|setup|set up)\b',
        r'\b(generate\s+project|generate\s+a\s+project)\b',
        r'^(run)\b',
    ]
    for pat in build_keywords:
        if re.search(pat, lower):
            return {
                "mode": "EXECUTE",
                "goal": text,
                "response": "Executing autonomous build pipeline.",
            }

    # 2. Multi-file / multi-module requirement detection
    multifile_patterns = [
        r'\b(files?|modules?|components?)\b.*\b(and|with|plus|,)\b',  # "X module and Y module"
        r'\b(frontend|backend|api|database|server|client|routes?)\b',  # fullstack signals
        r'\b(main\.py|index\.js|app\.py|server\.py|index\.html)\b',  # explicit file references
        r'\b(\w+\.py|\w+\.js|\w+\.html|\w+\.css|\w+\.ts)\b.*\b(\w+\.py|\w+\.js|\w+\.html|\w+\.css|\w+\.ts)\b',  # two+ file references
        r'\b(project|application|app|tool|system|service|pipeline|package)\b',  # project-level language
        r'\b(with|using|that has|including|contains?)\b.*\b(module|class|function|endpoint|route|page|view)\b',
    ]
    for pat in multifile_patterns:
        if re.search(pat, lower):
            return {
                "mode": "EXECUTE",
                "goal": text,
                "response": "Multi-file project detected. Executing full build pipeline.",
            }

    # ── Show patterns ────────────────────────────────────────────
    show_patterns = [
        r'^(show|open|display|cat|view|print)\b',
        r'(what did you|what.*built|see the|look at)',
    ]
    for pat in show_patterns:
        if re.search(pat, lower):
            target = text.split()[-1] if len(text.split()) > 1 else "all"
            return {
                "mode": "SHOW",
                "target": target,
                "response": "Here you go.",
            }

    # ── Chat / greeting patterns ─────────────────────────────────
    chat_patterns = [
        r'^(hi|hello|hey|sup|yo|hola|howdy|good morning|good evening|gm|gn)\b',
        r'^(thanks|thank you|thx|ty|cheers|cool|nice|great|awesome|ok|okay|got it|sure)\b',
        r'^(how are you|what\'s up|wassup|whats up)\b',
        r'^(lol|lmao|haha|heh|xd)\b',
        r'^(bye|goodbye|see ya|later|peace)\b',
    ]
    for pat in chat_patterns:
        if re.match(pat, lower):
            return {
                "mode": "CHAT",
                "response": "",  # Will be generated by chat_respond
            }

    # ── Brainstorm signals ───────────────────────────────────────
    discuss_patterns = [
        r"(let's think|brainstorm|what if|how about|should I|would you|compare)",
        r"(pros and cons|trade.?off|approach|architecture|design)",
        r"(explain|tell me about|how does|what is|why)",
    ]
    for pat in discuss_patterns:
        if re.search(pat, lower):
            return None  # Let the model handle nuanced discussion

    # Very short non-keyword input
    if len(lower.split()) <= 2 and not any(kw in lower for kw in ["build", "create", "fix", "run", "implement", "generate"]):
        return None  # Let model handle

    return None


def _parse_response(text: str) -> dict | None:
    """Extract the intent JSON from model output."""
    # Try fenced JSON
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    for block in fenced:
        try:
            obj = json.loads(block)
            if "mode" in obj:
                return obj
        except json.JSONDecodeError:
            continue

    # Try bare JSON
    try:
        # Find JSON-like content
        match = re.search(r'\{[^{}]*"mode"[^{}]*\}', text, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            if "mode" in obj:
                return obj
    except json.JSONDecodeError:
        pass

    # Try brace-balanced extraction
    from tool_registry import _extract_json_objects
    for obj_str in _extract_json_objects(text):
        try:
            obj = json.loads(obj_str)
            if "mode" in obj:
                return obj
        except json.JSONDecodeError:
            continue

    return None


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
