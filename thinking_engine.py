"""
thinking_engine.py — Multi-agent thinking and synthesis engine.

Implements the Strict Mode reasoning pipeline:
Architect, Engineer, Critic, Optimizer, Realist.
Decomposes task -> debate -> critique -> refine -> vote -> synthesis.
Yields reasoning tokens (thoughts) and final response.
"""

import json
from typing import Generator
from model_router import call_model

def get_agent_prompt(role: str, task: str, context: str) -> str:
    prompts = {
        "Architect": "Focus on high-level system design, scalability, and patterns.",
        "Engineer": "Focus on concrete implementation details, syntax, and algorithms.",
        "Critic": "Focus on finding edge cases, security flaws, and logical gaps.",
        "Optimizer": "Focus on performance, memory constraints, and efficiency.",
        "Realist": "Focus on practical constraints, MVP delivery, and keeping it simple."
    }
    
    return f"""You are the {role} in a panel of experts.
{prompts.get(role, "")}

Analyze the following task and provide your perspective.
Be concise but deep in your reasoning. Focus only on your area of expertise.

Context:
{context}

Task: {task}
"""

def synthesize_thought(task: str, context: str) -> Generator[str, None, None]:
    """
    Run the multi-agent thinking pipeline.
    Yields thoughts inside <thought> tags, then yields the final synthesized response.
    """
    yield "<thought>\n"
    yield "🧠 Starting Multi-Agent Thinking Engine...\n\n"
    
    agents = ["Architect", "Engineer", "Critic", "Optimizer", "Realist"]
    perspectives = {}
    
    # Step 1: Multi-Agent Perspectives
    yield "### Phase 1: Multi-Agent Analysis\n"
    for agent in agents:
        yield f"**{agent}** is analyzing...\n"
        prompt = get_agent_prompt(agent, task, context)
        
        # We use 'think' role if available, otherwise fallback to 'planner'
        # To avoid blocking too long, we don't stream the internal monologue, just wait for it
        # However, for UX, we could stream it. We'll do blocking to gather perspectives.
        response = call_model(
            role="planner",  # use planner as think fallback for now
            prompt=prompt,
            system_prompt=f"You are the {agent}.",
            temperature=0.4
        )
        perspectives[agent] = response
        
        # Yield a tiny summary or just a checkmark
        yield f"✓ {agent} finished analysis.\n"
        
    # Step 2: Synthesis & Refinement
    yield "\n### Phase 2: Synthesis & Refinement\n"
    yield "Synthesizing perspectives into a cohesive solution...\n"
    
    synthesis_prompt = f"""You are the Master Synthesizer.
Review the user task and the perspectives from your panel of experts.
Synthesize a single, definitive, and highly optimal response that addresses the user's task.
Incorporate the best ideas, address the criticisms, and ensure practical implementation.

Task: {task}

Expert Perspectives:
"""
    for agent, text in perspectives.items():
        synthesis_prompt += f"\n--- {agent} ---\n{text}\n"

    synthesis_prompt += "\nNow, provide the final synthesized response to the user. Use markdown. Be direct and helpful."
    
    yield "</thought>\n"
    
    # Step 3: Stream final answer to user
    yield from call_model(
        role="planner", # Using planner as fallback for deep reasoning
        prompt=synthesis_prompt,
        system_prompt="You are niggativity, an advanced autonomous coding agent.",
        temperature=0.3,
        stream=True
    )
