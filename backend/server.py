#!/usr/bin/env python3
"""
backend/server.py — FastAPI server bridging UI/VSCode to the niggativity orchestrator.

Start: python backend/server.py

Endpoints:
    POST /chat          — Send message, receive streamed SSE response
    POST /run           — Trigger orchestrator execution loop
    GET  /files         — List workspace files
    GET  /file          — Read file content
    GET  /session       — Get current session state
    POST /session/reset — Reset current session
    GET  /sessions      — List all sessions
    POST /sessions/switch — Switch to a different session
    POST /sessions/new    — Create a new session
    DELETE /sessions/{id} — Delete a session
    GET  /history       — Get conversation history
    GET  /models        — Get model info
    GET  /artifacts     — Get session artifacts
"""
import sys, os, io, json, threading
from typing import Optional

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from session.session_manager import SessionManager
from model_router import call_model, get_installed_models, pick_model
from memory.vector_store import get_relevant_context

UI_DIR = os.path.join(ROOT, "ui")

app = FastAPI(title="niggativity API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

_session: Optional[SessionManager] = None
_tools_initialized = False
_orchestrator_lock = threading.Lock()
WORKSPACE_BASE = os.path.join(ROOT, "workspace")


def get_session() -> SessionManager:
    global _session
    if _session is None:
        latest = SessionManager.get_latest_session_id()
        if latest:
            _session = SessionManager(session_id=latest)
        else:
            _session = SessionManager()
    return _session


def ensure_tools():
    global _tools_initialized
    if not _tools_initialized:
        from orchestrator import init_tools
        init_tools()
        _tools_initialized = True


# ─── Request Models ────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    context_lines: int = 8
    thinking_mode: bool = False

class RunRequest(BaseModel):
    goal: Optional[str] = None

class SwitchSessionRequest(BaseModel):
    session_id: str

class NewSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"


# ─── Root ──────────────────────────────────────────────

@app.get("/")
async def root():
    models = get_installed_models()
    session = get_session()
    return {
        "status": "ok",
        "service": "niggativity",
        "version": "2.0.0",
        "models": len(models),
        "session_id": session.session_id,
        "session_title": session.state.get("title", "Untitled"),
    }


# ─── Chat (SSE Streaming) ─────────────────────────────

@app.post("/chat")
async def chat(req: ChatRequest):
    session = get_session()
    msg = req.message.strip()
    if not msg:
        raise HTTPException(400, "Empty message")
        
    # Handle slash commands for Strict Mode / Auto Execute
    if msg == "/think_on":
        session.state["thinking_mode"] = True
        session.save()
        return StreamingResponse(iter(["data: {\"token\": \"\", \"done\": true, \"full_response\": \"🧠 Thinking Mode ENABLED. I will use multi-agent reasoning for complex tasks.\"}\n\n"]), media_type="text/event-stream")
    elif msg == "/think_off":
        session.state["thinking_mode"] = False
        session.save()
        return StreamingResponse(iter(["data: {\"token\": \"\", \"done\": true, \"full_response\": \"⚡ Thinking Mode DISABLED. Fast chat mode active.\"}\n\n"]), media_type="text/event-stream")
    elif msg == "/auto_on":
        session.state["auto_execute"] = True
        session.save()
        return StreamingResponse(iter(["data: {\"token\": \"\", \"done\": true, \"full_response\": \"🚀 Auto-Execute ENABLED. I will run plans without asking for confirmation.\"}\n\n"]), media_type="text/event-stream")
    elif msg == "/auto_off":
        session.state["auto_execute"] = False
        session.save()
        return StreamingResponse(iter(["data: {\"token\": \"\", \"done\": true, \"full_response\": \"🛡️ Auto-Execute DISABLED. I will ask for approval before executing plans.\"}\n\n"]), media_type="text/event-stream")

    session.add_message("user", msg)

    context = session.get_conversation_context(last_n=req.context_lines)
    goal = session.state.get("current_goal")

    # Classify intent to see if we should auto-execute
    from agents.conversation_agent import classify_intent
    intent = classify_intent(msg, context, goal, session.state.get("mode", "discuss"))
    
    if intent and intent.get("mode") == "EXECUTE":
        new_goal = intent.get("goal", msg)
        session.set_goal(new_goal)
        # Yield a special SSE event to tell the frontend to trigger /run
        return StreamingResponse(iter([f"data: {json.dumps({'token': '', 'done': True, 'intent': 'EXECUTE', 'goal': new_goal, 'full_response': intent.get('response', 'Starting execution...')})}\n\n"]), media_type="text/event-stream")

    # Inject codebase awareness context if workspace exists
    codebase_ctx = ""
    ws = session.state.get("workspace_dir")
    if ws and os.path.isdir(ws):
        from codebase.retriever import get_context_for_prompt
        codebase_ctx = "\n" + get_context_for_prompt(msg, ws, top_k=5) + "\n"

    memory_ctx = get_relevant_context(msg)
    ctx_block = f"\nRecent conversation:\n{context}\n" if context else ""
    goal_block = f"\nCurrent goal: {goal}\n" if goal else ""

    prompt = f"""{ctx_block}{codebase_ctx}{goal_block}{memory_ctx}
User: {msg}
Respond as a helpful senior developer. Be concise and practical. Do NOT output JSON.

RULES:
- If the user asks about code, provide code blocks with language tags
- If you produce code, wrap it in triple backticks with the language name
- Be direct and useful
- Use markdown formatting for structure"""

    sys_prompt = ("You are niggativity, a local autonomous coding assistant. "
                  "Be direct, insightful, and practical. Use markdown formatting.")

    # Check if thinking mode is forced by session state or request
    use_thinking = req.thinking_mode or session.state.get("thinking_mode", False)

    async def sse():
        full = []
        try:
            if use_thinking:
                from thinking_engine import synthesize_thought
                generator = synthesize_thought(msg, f"{ctx_block}{codebase_ctx}{goal_block}{memory_ctx}")
            else:
                generator = call_model(role="chat", prompt=prompt, stream=True,
                                        system_prompt=sys_prompt, temperature=0.5)
                                        
            for token in generator:
                full.append(token)
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            text = "".join(full)

            # Detect and track artifacts from the response
            artifacts = _extract_artifacts(text)
            session.add_message("assistant", text, artifacts=artifacts if artifacts else None)

            # Store artifacts in session
            for art in artifacts:
                session.add_artifact(art)

            yield f"data: {json.dumps({'token': '', 'done': True, 'full_response': text, 'artifacts': artifacts})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                                      "X-Accel-Buffering": "no"})


def _extract_artifacts(text: str) -> list[dict]:
    """Extract code blocks and structured artifacts from response text."""
    import re
    artifacts = []
    # Find fenced code blocks
    pattern = r'```(\w*)\n([\s\S]*?)```'
    for match in re.finditer(pattern, text):
        lang = match.group(1) or "text"
        code = match.group(2).strip()
        if len(code) > 20:  # Only track substantial code blocks
            artifacts.append({
                "type": "code",
                "language": lang,
                "content": code,
                "title": f"{lang} snippet",
            })
    return artifacts


# ─── Run Orchestrator ──────────────────────────────────

class ExecuteRequest(BaseModel):
    plan: dict
    task: str
    workspace_dir: str

@app.post("/run")
async def run_task(req: RunRequest):
    session = get_session()
    ensure_tools()
    goal = req.goal or session.state.get("current_goal")
    if not goal:
        raise HTTPException(400, "No goal specified")
    session.set_goal(goal)
    session.set_mode("plan")
    session.add_message("assistant", f"Generating plan for: {goal}")

    workspace = session.state.get("workspace_dir")
    if not workspace or not os.path.isdir(workspace):
        import time
        workspace = os.path.join(WORKSPACE_BASE, f"project_{int(time.time())}")
        os.makedirs(workspace, exist_ok=True)
        session.set_workspace(workspace)

    from orchestrator import generate_plan, execute_plan
    
    plan = generate_plan(goal, os.path.basename(workspace))
    if "error" in plan:
        raise HTTPException(500, plan["error"])
        
    session.add_artifact({
        "type": "plan",
        "title": f"Implementation Plan: {goal[:30]}...",
        "content": json.dumps(plan, indent=2),
    })

    auto_exec = session.state.get("auto_execute", False)
    if auto_exec:
        session.add_message("assistant", "Auto-execute is ON. Starting execution immediately...")
        # Fire off execution in background
        def _bg_execute():
            with _orchestrator_lock:
                try:
                    def status_cb(msg):
                        session.add_message("assistant", msg)
                    result = execute_plan(plan, goal, workspace, status_cb=status_cb)
                    v = result.get("verdict", {}) if result else {}
                    session.add_message("assistant", f"Build complete. Verdict: {v.get('verdict','N/A')}")
                except Exception as e:
                    session.add_message("assistant", f"Build error: {e}")
        
        threading.Thread(target=_bg_execute, daemon=True).start()
        return {"status": "started", "goal": goal, "workspace": workspace, "plan": plan, "auto_executed": True}
    else:
        session.add_message("assistant", "Plan generated. Auto-execute is OFF. Please review the plan in artifacts and approve to continue.")
        return {"status": "planned", "goal": goal, "workspace": workspace, "plan": plan, "auto_executed": False}

@app.post("/run/execute")
async def execute_task(req: ExecuteRequest):
    session = get_session()
    ensure_tools()
    session.set_mode("execute")
    session.add_message("assistant", "User approved plan. Starting execution...")

    def _run():
        with _orchestrator_lock:
            try:
                from orchestrator import execute_plan
                def status_cb(msg):
                    session.add_message("assistant", msg)
                result = execute_plan(req.plan, req.task, req.workspace_dir, status_cb=status_cb)
                if result:
                    v = result.get("verdict", {})
                    session.add_message("assistant",
                        f"Build complete. Verdict: {v.get('verdict','N/A')} (score: {v.get('score','?')}/10)")
                    session.add_artifact({
                        "type": "result",
                        "title": f"Build result: {req.task[:50]}",
                        "content": json.dumps(v, indent=2),
                    })
                    session.set_mode("discuss")
            except Exception as e:
                session.add_message("assistant", f"Build error: {e}")
                session.add_artifact({
                    "type": "error",
                    "title": "Build Error",
                    "content": str(e),
                })

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "goal": req.task, "workspace": req.workspace_dir}


# ─── File Operations ───────────────────────────────────

@app.get("/files")
async def list_files():
    session = get_session()
    ws = session.state.get("workspace_dir")
    if not ws or not os.path.isdir(ws):
        return {"workspace": None, "files": []}
    files = []
    for r, dirs, fnames in os.walk(ws):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules","__pycache__",".git","venv")]
        for fn in fnames:
            fp = os.path.join(r, fn)
            files.append({"path": os.path.relpath(fp, ws).replace("\\","/"), "size": os.path.getsize(fp)})
    return {"workspace": ws, "files": sorted(files, key=lambda f: f["path"])}


@app.get("/file")
async def read_file(path: str = Query(...)):
    session = get_session()
    ws = session.state.get("workspace_dir")
    if not ws:
        raise HTTPException(404, "No workspace")
    full = os.path.normpath(os.path.join(ws, path))
    if not full.startswith(os.path.normpath(ws)):
        raise HTTPException(403, "Path traversal blocked")
    if not os.path.isfile(full):
        raise HTTPException(404, f"Not found: {path}")
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {"path": path, "content": content, "size": os.path.getsize(full)}


# ─── Session Management ───────────────────────────────

@app.get("/session")
async def get_session_state():
    s = get_session().state
    return {k: s.get(k) for k in ["session_id", "title", "mode", "current_goal", "workspace_dir",
                                    "iteration_count", "tech_stack", "last_task", "files_created"]}

@app.post("/session/reset")
async def reset_session():
    global _session
    get_session().reset()
    _session = None
    return {"status": "reset"}


# ─── Multi-Session ─────────────────────────────────────

@app.get("/sessions")
async def list_sessions():
    """List all available sessions."""
    sessions = SessionManager.list_sessions()
    current = get_session().session_id
    return {"sessions": sessions, "current_session_id": current}

@app.post("/sessions/switch")
async def switch_session(req: SwitchSessionRequest):
    """Switch to a different session."""
    global _session
    _session = SessionManager(session_id=req.session_id)
    return {
        "status": "switched",
        "session_id": _session.session_id,
        "title": _session.state.get("title", "Untitled"),
    }

@app.post("/sessions/new")
async def new_session(req: NewSessionRequest):
    """Create a new session and switch to it."""
    global _session
    _session = SessionManager()
    if req.title and req.title != "New Chat":
        _session.set_title(req.title)
    return {
        "status": "created",
        "session_id": _session.session_id,
        "title": _session.state.get("title", "New Chat"),
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session by ID."""
    current = get_session().session_id
    if session_id == current:
        raise HTTPException(400, "Cannot delete the currently active session")
    deleted = SessionManager.delete_session(session_id)
    if not deleted:
        raise HTTPException(404, f"Session not found: {session_id}")
    return {"status": "deleted", "session_id": session_id}


# ─── History & Artifacts ──────────────────────────────

@app.get("/history")
async def get_history(last_n: int = Query(50)):
    s = get_session()
    msgs = s.state.get("conversation", [])[-last_n:]
    return {"session_id": s.state.get("session_id"), "messages": msgs, "total": len(s.state.get("conversation",[]))}

@app.get("/artifacts")
async def get_artifacts(last_n: int = Query(20)):
    """Get recent artifacts from the current session."""
    s = get_session()
    artifacts = s.get_artifacts(last_n=last_n)
    return {"session_id": s.session_id, "artifacts": artifacts}


# ─── Models ────────────────────────────────────────────

@app.get("/models")
async def get_models():
    models = get_installed_models()
    roles = {r: pick_model(r, models) for r in ["planner","builder","debugger","judge","refiner","chat","vision"]}
    return {"installed": models, "roles": roles}


# ─── UI Serving ────────────────────────────────────────

@app.get("/ui")
@app.get("/ui/")
async def serve_ui():
    """Serve the web UI index page."""
    index = os.path.join(UI_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index, media_type="text/html")
    raise HTTPException(404, "UI not found")

# Mount static files LAST to avoid overriding API routes
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui-static")


# ─── Main ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  NIGGATIVITY — API Server v2.0")
    print("="*60)
    print("  Backend: http://localhost:8000")
    print("  Docs:    http://localhost:8000/docs")
    print("  UI:      http://localhost:8000/ui")
    print("="*60 + "\n")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
