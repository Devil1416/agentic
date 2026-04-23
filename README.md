# niggativity

**Local-First Autonomous Coding Agent** — powered entirely by Ollama. Zero cloud dependencies.

Conversational AI coding partner that plans, builds, executes, debugs, and refines code autonomously.

---

## Quick Start

```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Pull models
ollama pull llama3:8b
ollama pull deepseek-coder:6.7b

# 3. Install deps
cd d:\n1ggaman\agentic
pip install -r requirements.txt

# 4. Launch
python cli.py
```

Then just talk:
```
you> build me a REST API with Flask
you> let's brainstorm a CLI tool idea
you> fix the error in main.py
you> show me what you built
```

---

## Architecture

```
                    +-------------+
                    |   CLI.py    |  <-- conversational interface
                    +------+------+
                           |
                    +------+------+
                    | CONVERSATION|  <-- intent classifier
                    |   AGENT     |     (DISCUSS/EXECUTE/DEBUG/PLAN/SHOW)
                    +------+------+
                           |
              +------------+-------------+
              |                          |
     +--------+--------+       +--------+--------+
     |   DISCUSS MODE  |       | EXECUTE/DEBUG   |
     |  brainstorm,    |       |                 |
     |  clarify, chat  |       +--------+--------+
     +-----------------+                |
                                +-------+-------+
                                | ORCHESTRATOR  |
                                +-------+-------+
                                        |
          +--------+--------+--------+--+--+--------+
          |        |        |        |     |        |
       PLANNER  BUILDER  EXECUTOR  DEBUG  JUDGE  REFINER
       llama3   deepseek subprocess deepseek llama3 mistral
                                        |
                                   +----+----+
                                   |  MEMORY  |
                                   |  FAISS   |
                                   +----------+
```

## CLI Commands

| Command    | Action                              |
|------------|-------------------------------------|
| `/help`    | Show all commands                   |
| `/run`     | Execute current plan (skip confirm) |
| `/plan`    | Show current plan                   |
| `/files`   | List workspace files                |
| `/show X`  | Display file contents               |
| `/memory`  | Show stored memories                |
| `/status`  | Session status                      |
| `/history` | Conversation history                |
| `/reset`   | Clear session                       |
| `/exit`    | Quit                                |

Or just type naturally — the system figures out your intent.

---

## Modes

| Mode    | Triggered By                        | Behavior                        |
|---------|-------------------------------------|---------------------------------|
| DISCUSS | "let's think...", "what if..."      | Brainstorm, no code execution   |
| EXECUTE | "build X", "create Y"               | Full build pipeline             |
| DEBUG   | "not working", "fix the error"      | Auto-diagnose + diff fix        |
| PLAN    | "how would you build...", "plan X"  | Generate plan only              |
| SHOW    | "show me", "open main.py"           | Display files                   |

---

## Project Structure

```
agentic/
├── cli.py                  # Interactive conversational CLI
├── main.py                 # Legacy CLI entry point
├── orchestrator.py         # PLAN->BUILD->EXECUTE->DEBUG->JUDGE->REFINE loop
├── model_router.py         # Ollama auto-detection + streaming
├── tool_registry.py        # Tool registration + JSON parsing
├── requirements.txt
│
├── agents/
│   ├── conversation_agent.py  # Intent classification + brainstorm
│   ├── planner.py             # Architecture planning (JSON)
│   ├── builder.py             # Code generation (tool calls)
│   ├── debugger.py            # Error analysis + diff fixes
│   ├── judge.py               # Solution scoring
│   └── refiner.py             # Code optimization
│
├── tools/
│   ├── fs.py               # read_file, write_file, list_files
│   ├── executor.py         # run_python, run_node, run_command
│   └── diff_editor.py      # Unified diff patching
│
├── memory/
│   └── vector_store.py     # FAISS + sentence-transformers (3-tier fallback)
│
├── session/
│   └── session_manager.py  # Persistent session state
│
├── utils/
│   └── command_parser.py   # Slash command + NL input router
│
├── workspace/              # Generated projects
└── logs/                   # Session logs + memory
    └── sessions/           # Persistent session files
```

---

## Key Features

- **Conversational** — natural language, not command syntax
- **Intent Detection** — auto-routes to build/debug/discuss/plan
- **Human-in-the-Loop** — confirms before executing (bypass with /run)
- **Streaming Output** — real-time token streaming from Ollama
- **Persistent Sessions** — remembers goals, plans, conversation
- **Auto-Debug** — detects errors and applies diff fixes
- **Brainstorm Mode** — discuss ideas without running code
- **File Explorer** — view what was built inline
- **Vector Memory** — FAISS-backed recall of past errors/fixes

---

## Model Routing

| Role         | Preferred Model         | Fallback                   |
|--------------|------------------------|----------------------------|
| Planner      | `llama3:8b`            | mistral -> gemma           |
| Builder      | `deepseek-coder:6.7b`  | codellama -> llama3        |
| Debugger     | `deepseek-coder:6.7b`  | codellama -> llama3        |
| Judge        | `llama3:8b`            | mistral -> gemma           |
| Refiner      | `mistral:7b`           | llama3 -> gemma            |
| Conversation | `llama3:8b`            | (uses planner role)        |

---

## Hardware

- **RAM**: 16GB (sequential agents, 1 model at a time)
- **GPU**: Optional, faster inference
- **Disk**: ~10GB for models

---

## Design Principles

- Feels like chatting with a developer, not operating a machine
- Deterministic > clever
- Real execution > fake reasoning
- Sequential agents to respect RAM limits
- Ollama only, zero cloud
