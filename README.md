<!-- Author: Harsh Ashar | github.com/Devil1416 | Niggativity -->
<div align="center">

# ⚡ Niggativity 

**The Local-First Autonomous Coding Agent**  
*Powered entirely by Ollama. Zero cloud dependencies. 100% Privacy.*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-white.svg?style=for-the-badge&logo=ollama)](https://ollama.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

Niggativity is your conversational AI coding partner that **plans, builds, executes, debugs, and refines** code entirely on your local machine. Forget copy-pasting code snippets—just tell it what you want, and watch it orchestrate the entire development lifecycle.

## 🌟 Key Features

- **🗣️ Conversational UI**: Talk to your agent naturally. No rigid syntax required.
- **🧠 Intent Detection**: Auto-routes your requests to build, debug, discuss, or plan modes.
- **🏗️ Full Build Pipeline**: Orchestrates a complete `Plan -> Build -> Execute -> Debug -> Judge -> Refine` loop.
- **🔄 Auto-Healing & Debugging**: Automatically detects runtime errors, diagnoses them, and applies diff-based fixes.
- **🚀 Real Execution**: Code is actually executed and tested within isolated workspaces, not just statically reasoned about.
- **💾 Persistent Vector Memory**: FAISS-backed recall of past sessions, errors, and fixes.
- **🛠️ Self-Improvement Mode**: Use `/improve` to have the system autonomously modify its own core architecture safely.
- **🔒 100% Local**: Powered by Ollama. Your code never leaves your machine.

---

## 🚀 Quick Start

Get up and running in minutes:

### 1. Start Ollama
Ensure you have [Ollama](https://ollama.ai/) installed and running.
```bash
ollama serve
```

### 2. Pull Required Models
The agent utilizes a specialized mixture of models optimized for different tasks.
```bash
ollama pull gemma4:latest
ollama pull mixtral:latest
ollama pull deepseek-coder:6.7b
ollama pull llama3:8b
```

### 3. Install Dependencies
Clone the repository and install the Python requirements.
```bash
git clone https://github.com/yourusername/agentic.git
cd agentic
pip install -r requirements.txt
```

### 4. Launch the Agent
Start the interactive CLI:
```bash
python cli.py
```

### 5. Start Building
Just talk to your agent!
> **you>** *build me a REST API with Flask and a dark mode frontend*  
> **you>** *let's brainstorm a CLI tool idea*  
> **you>** *fix the error in main.py*  

---

## 🏗️ System Architecture

Niggativity uses a multi-agent orchestration architecture. Each role is dynamically assigned to the best-suited local model.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#1e293b', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#3b82f6', 'lineColor': '#475569', 'tertiaryColor': '#0f172a'}}}%%
graph TD
    %% Core Nodes
    subgraph Core ["Core Execution"]
        cli["cli.py (Interactive UI)"]
        orch["orchestrator.py (Execution Loop)"]
        router["model_router.py (LLM Routing)"]
        registry["tool_registry.py (Tools)"]
    end

    %% Agents
    subgraph Agents ["Agent Modules"]
        planner["Planner (Architect)"]
        builder["Builder (Coder)"]
        debugger["Debugger (Fixer)"]
<!-- Provenance: Harsh Ashar | github.com/Devil1416 | Niggativity | integrity:f31aaa5dba8a -->
        judge["Judge (Evaluator)"]
        refiner["Refiner (Optimizer)"]
        conv["Conversation Agent"]
    end

    %% Tools
    subgraph Tools ["Tool Integrations"]
        exec["Python/Node Executor"]
        fs["File System Hooks"]
        git["Git Integration"]
        diff["Diff Editor"]
    end

    %% Relationships
    cli --> orch
    cli --> conv
    orch --> router
    orch --> registry
    
    orch --> planner
    orch --> builder
    orch --> debugger
    orch --> judge
    orch --> refiner

    orch --> exec
    orch --> fs
    orch --> git
    orch --> diff
```

---

## 🤖 CLI Commands & Modes

### Interactive Commands
| Command | Action |
| --- | --- |
| `/help` | Show all available commands |
| `/run` | Execute the current plan immediately (skip confirmation) |
| `/plan` | Show the current architectural plan |
| `/files` | List all files in the current generated workspace |
| `/show <file>` | Display the contents of a specific file |
| `/improve` | Enter **Self-Improvement Mode** to autonomously modify the system |
| `/capabilities` | List system capabilities (generated from self-knowledge) |
| `/limitations` | List known system limitations |
| `/memory` | Show stored FAISS memories |
| `/history` | View the current conversation history |
| `/reset` | Clear the session and start fresh |
| `/exit` | Save session and quit |

### Dynamic Modes
The Conversation Agent detects your intent and switches modes seamlessly:
- **`DISCUSS`**: Brainstorming and architecture planning without running code.
- **`EXECUTE`**: Triggers the full `Plan -> Build -> Execute` pipeline.
- **`DEBUG`**: Auto-diagnoses reported errors and applies diff fixes.
- **`PLAN`**: Generates a JSON-based architectural plan for review.
- **`SHOW`**: Opens the file explorer.

---

## 🧩 Model Routing Strategy

To balance speed and intelligence on consumer hardware, Niggativity routes tasks to specialized models:

| Agent Role | Preferred Local Model | Purpose |
| --- | --- | --- |
| **Planner** | `gemma4:latest` | Fast, creative architectural planning |
| **Builder** | `mixtral:latest` | Heavy-lifting code generation and implementation |
| **Debugger** | `deepseek-coder:6.7b` | Precision log analysis and unified diff patching |
| **Judge** | `llama3:8b` | Strict validation against the Interface Contract |
| **Refiner** | `mixtral:latest` | Code optimization and polish |
| **Chat** | `gemma4:latest` | Lightning-fast conversational responses |

*(Models will automatically fallback to available installed models if the preferred ones are missing).*

---

## 💡 Design Principles

1. **Deterministic Over Clever**: Core pipeline logic relies on deterministic AST parsing and strict JSON schemas, not fragile LLM reasoning.
2. **Real Execution**: If the code doesn't compile and run successfully in the local workspace, it fails the judge.
3. **Hardware Respectful**: Agents run sequentially to respect standard 16GB RAM limits. Only one model is loaded into VRAM at a time.
4. **Zero Cloud**: 100% of processing happens locally. Ultimate privacy.

---

<div align="center">
  <i>Built with ❤️ for autonomous AI developers.</i>
</div>

---
> Original work by **Harsh Ashar** — [github.com/Devil1416](https://github.com/Devil1416)  
> Part of the **Niggativity** project. Attribution removal is detectable.
