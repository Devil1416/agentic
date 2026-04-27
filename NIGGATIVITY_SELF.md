# NIGGATIVITY SYSTEM KNOWLEDGE

## System Overview
Niggativity is a local-first autonomous coding assistant powered by Ollama. It features a conversational CLI, full-stack application building capabilities, deterministic self-healing loops, and an execution environment.

## Current Capabilities
- **Agents**: Planner, Builder, Debugger, Judge, Refiner, Conversation Agent
- **Tools**: read_file, write_file, edit_file_diff, list_files, run_python, run_node, run_command, auto_detect_and_run, install_dependencies, analyze_image, git_init, git_commit, git_rollback
- **Commands**: /help, /exit, /status, /history, /plan, /files, /show, /open, /memory, /reset, /run, /improve, /capabilities, /limitations

## Architecture
- **agents/__init__.py**: No description available.
- **agents/builder.py**: agents/builder.py — Code generation agent.
- **agents/conversation_agent.py**: agents/conversation_agent.py — Conversational intent classifier and responder.
- **agents/debugger.py**: agents/debugger.py — Error analysis and auto-fix agent.
- **agents/judge.py**: agents/judge.py — Solution evaluation agent.
- **agents/planner.py**: agents/planner.py — Planning agent.
- **agents/refiner.py**: agents/refiner.py — Code optimization and patch agent.
- **app/main.py**: app/main.py - Niggativity desktop application.
- **backend/__init__.py**: No description available.
- **backend/server.py**: backend/server.py — FastAPI server bridging UI/VSCode to the niggativity orchestrator.
- **cli.py**: cli.py — Interactive conversational CLI for niggativity.
- **main.py**: main.py — Entry point for niggativity.
- **memory/__init__.py**: No description available.
- **memory/vector_store.py**: memory/vector_store.py - Persistent memory via FAISS + sentence-transformers.
- **model_router.py**: model_router.py - Ollama model routing with speed and reliability safeguards.
- **orchestrator.py**: orchestrator.py - Main execution loop for niggativity.
- **patch_builder.py**: No description available.
- **scripts/generate_self_md.py**: No description available.
- **start.py**: start.py - Launcher for the niggativity multi-interface system.
- **thinking_engine.py**: thinking_engine.py - Multi-agent thinking and synthesis engine.
- **tool_registry.py**: tool_registry.py — Central tool registration, parsing, and dispatch.
- **tools/__init__.py**: No description available.
- **tools/diff_editor.py**: tools/diff_editor.py — Unified-diff-based file editing.
- **tools/executor.py**: tools/executor.py — Real code execution via subprocess.
- **tools/fs.py**: tools/fs.py — Filesystem tools: read, write, list, edit via diff.
- **tools/git_tools.py**: tools/git_tools.py — Git operations for project management.
- **tools/vision.py**: tools/vision.py — Image analysis via Ollama multimodal models (llava).
- **utils/__init__.py**: No description available.
- **utils/command_parser.py**: utils/command_parser.py — Parse user input into commands or natural language.

## Known Limitations

## Improvement History
