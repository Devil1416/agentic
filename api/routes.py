# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
api/routes.py — FastAPI route handlers for Reflexion.

Implements:
  POST   /v1/messages          — Claude-compatible streaming chat
  GET    /v1/models            — Model listing
  POST   /v1/messages/count_tokens
  GET    /health
  POST   /run                  — Trigger full build pipeline
  POST   /run/execute          — Execute an approved plan
  GET    /session              — Session state
  POST   /session/reset        — Reset session
  GET/POST /sessions/*         — Multi-session management
  GET    /history              — Conversation history
  GET    /artifacts            — Session artifacts
  GET    /files                — Workspace file listing
  GET    /file                 — Read a workspace file
  GET    /models               — Ollama model info
  POST   /stop                 — Stop all running tasks
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from api.models import (
    ExecuteRequest,
    MessagesRequest,
    ModelsListResponse,
    ModelInfo,
    RunRequest,
    TokenCountRequest,
    TokenCountResponse,
)
from config.settings import ReflexionSettings, get_settings
from model_router import call_model, get_installed_models, pick_model
from session.session_manager import SessionManager

router = APIRouter()

# ── Module-level state shared with app.py ────────────────────
_session: Optional[SessionManager] = None
_tools_initialized = False
_orchestrator_lock = threading.Lock()


def _get_session() -> SessionManager:
    global _session
    if _session is None:
        latest = SessionManager.get_latest_session_id()
        _session = SessionManager(session_id=latest) if latest else SessionManager()
    return _session


def _ensure_tools():
    global _tools_initialized
    if not _tools_initialized:
        from orchestrator import init_tools
        init_tools()
        _tools_initialized = True


# ── Auth dependency ──────────────────────────────────────────

def require_api_key(request: Request, settings: ReflexionSettings = Depends(get_settings)):
    if not settings.require_auth:
        return  # Auth disabled → always allow
    auth = request.headers.get("Authorization", "")
    key = auth.removeprefix("Bearer ").strip()
    if key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Claude-compatible SSE helper ─────────────────────────────

def _anthropic_sse_stream(body):
    return StreamingResponse(
        body,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _stream_chat_sse(
    request_data: MessagesRequest,
    session: SessionManager,
    settings: ReflexionSettings,
):
    """Core SSE generator: calls Ollama via model_router, emits Claude-style events."""
    model_id = f"req_{uuid.uuid4().hex[:12]}"

    # Build flat prompt from messages
    context = session.get_conversation_context(last_n=8)
    user_text = request_data.messages[-1].text_content() if request_data.messages else ""

    # Role hint: determine which agent role to use
    role = request_data.role_hint or "chat"
    if request_data.thinking:
        role = "think"

    # Memory + codebase context
    try:
        from memory.vector_store import get_relevant_context
        mem_ctx = get_relevant_context(user_text)
    except Exception:
        mem_ctx = ""

    sys_prompt = (
        request_data.system
        or "You are Reflexion, a local autonomous coding assistant. "
           "Be direct, insightful, and practical. Use markdown formatting."
    )

    prompt = f"{context}\n{mem_ctx}\nUser: {user_text}"

    # ── SSE: message_start ────────────────────────────────────
    yield _sse_event("message_start", {
        "type": "message_start",
        "message": {
            "id": model_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": request_data.model,
            "stop_reason": None,
            "usage": {"input_tokens": len(prompt) // 4, "output_tokens": 0},
        },
    })
    yield _sse_event("content_block_start", {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    })
    yield _sse_event("ping", {"type": "ping"})

    # ── Token stream ─────────────────────────────────────────
    full_text_parts: list[str] = []
    output_tokens = 0
    try:
        for token in call_model(
            role=role,
            prompt=prompt,
            stream=True,
            system_prompt=sys_prompt,
            temperature=request_data.temperature,
            max_tokens=request_data.max_tokens,
        ):
            full_text_parts.append(token)
            output_tokens += len(token.split())
            yield _sse_event("content_block_delta", {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": token},
            })
    except Exception as exc:
        yield _sse_event("error", {"type": "error", "error": {"type": "api_error", "message": str(exc)}})
        return

    full_text = "".join(full_text_parts)

    # ── Save to session ───────────────────────────────────────
    session.add_message("user", user_text)
    session.add_message("assistant", full_text)

    # ── SSE: message_delta / stop ─────────────────────────────
    yield _sse_event("content_block_stop", {"type": "content_block_stop", "index": 0})
    yield _sse_event("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    })
    yield _sse_event("message_stop", {"type": "message_stop"})


# ── /v1/messages ─────────────────────────────────────────────

@router.post("/v1/messages")
async def create_message(
    request_data: MessagesRequest,
    request: Request,
    _auth=Depends(require_api_key),
    settings: ReflexionSettings = Depends(get_settings),
):
    """Claude-compatible streaming messages endpoint."""
    session = _get_session()

    # Handle /think slash command
    if request_data.messages:
        last_msg = request_data.messages[-1].text_content().strip()
        if last_msg == "/think_on":
            session.state["thinking_mode"] = True
            session.save()
        elif last_msg == "/think_off":
            session.state["thinking_mode"] = False
            session.save()

    return _anthropic_sse_stream(_stream_chat_sse(request_data, session, settings))


@router.api_route("/v1/messages", methods=["HEAD", "OPTIONS"])
async def probe_messages(_auth=Depends(require_api_key)):
    return Response(status_code=204, headers={"Allow": "POST, HEAD, OPTIONS"})


@router.post("/v1/messages/count_tokens")
async def count_tokens(
    request_data: TokenCountRequest,
    _auth=Depends(require_api_key),
):
    """Approximate token count (4 chars ≈ 1 token)."""
    total = sum(len(m.text_content()) // 4 for m in request_data.messages)
    if request_data.system:
        total += len(request_data.system) // 4
    return TokenCountResponse(input_tokens=total)


# ── /v1/models ───────────────────────────────────────────────

@router.get("/v1/models", response_model=ModelsListResponse)
async def list_models(_auth=Depends(require_api_key)):
    """List all locally available Ollama models as Claude-compatible model objects."""
    installed = get_installed_models()
    data = [
        ModelInfo(
            id=m,
            display_name=m,
            created_at="1970-01-01T00:00:00Z",
            provider="ollama",
        )
        for m in installed
    ]
    # Always include reflexion-auto as a virtual model
    data.insert(0, ModelInfo(id="reflexion-auto", display_name="Reflexion Auto (role-based routing)", provider="ollama"))
    return ModelsListResponse(
        data=data,
        first_id=data[0].id if data else None,
        last_id=data[-1].id if data else None,
    )


@router.get("/models")
async def models_info():
    """Get installed models and role assignments (legacy endpoint)."""
    models = get_installed_models()
    roles = {r: pick_model(r, models) for r in ["planner", "builder", "debugger", "judge", "refiner", "chat", "vision"]}
    return {"installed": models, "roles": roles}


# ── Root / health ────────────────────────────────────────────

@router.get("/")
async def root(settings: ReflexionSettings = Depends(get_settings)):
    models = get_installed_models()
    session = _get_session()
    return {
        "status": "ok",
        "service": "reflexion",
        "version": "2.0.0",
        "provider": "ollama",
        "models": len(models),
        "session_id": session.session_id,
    }


@router.api_route("/", methods=["HEAD", "OPTIONS"])
async def probe_root(_auth=Depends(require_api_key)):
    return Response(status_code=204, headers={"Allow": "GET, HEAD, OPTIONS"})


@router.get("/health")
async def health():
    """Health check — also verifies Ollama reachability."""
    models = get_installed_models()
    return {
        "status": "healthy",
        "ollama": len(models) > 0,
        "models_available": len(models),
    }


@router.api_route("/health", methods=["HEAD", "OPTIONS"])
async def probe_health():
    return Response(status_code=204, headers={"Allow": "GET, HEAD, OPTIONS"})


# ── Build pipeline ────────────────────────────────────────────

@router.post("/run")
async def run_task(req: RunRequest, _auth=Depends(require_api_key), settings: ReflexionSettings = Depends(get_settings)):
    """Trigger the full Reflexion build pipeline."""
    session = _get_session()
    _ensure_tools()

    goal = req.goal or session.state.get("current_goal")
    if not goal:
        raise HTTPException(400, "No goal specified")

    session.set_goal(goal)
    session.set_mode("plan")
    session.add_message("assistant", f"Generating plan for: {goal}")

    ws = session.state.get("workspace_dir")
    if not ws or not os.path.isdir(ws):
        ws = os.path.join(settings.workspace_base, f"project_{int(time.time())}")
        os.makedirs(ws, exist_ok=True)
        session.set_workspace(ws)

    from orchestrator import generate_plan, execute_plan

    plan = generate_plan(goal, os.path.basename(ws))
    if "error" in plan:
        raise HTTPException(500, plan["error"])

    max_iter = req.max_iterations or settings.max_iterations
    plan["max_debug_iterations"] = max_iter

    session.add_artifact({"type": "plan", "title": f"Plan: {goal[:40]}", "content": json.dumps(plan, indent=2)})

    if req.auto_execute or settings.auto_execute:
        session.add_message("assistant", "Auto-execute ON. Starting execution…")

        def _bg():
            with _orchestrator_lock:
                try:
                    def cb(msg):
                        session.add_message("assistant", msg)
                    result = execute_plan(plan, goal, ws, status_cb=cb, max_iterations=max_iter)
                    v = result.get("verdict", {}) if result else {}
                    session.add_message("assistant", f"Build complete. Verdict: {v.get('verdict', 'N/A')}")
                except Exception as exc:
                    session.add_message("assistant", f"Build error: {exc}")

        threading.Thread(target=_bg, daemon=True).start()
        return {"status": "started", "goal": goal, "workspace": ws, "plan": plan, "auto_executed": True}

    session.add_message("assistant", "Plan ready. Auto-execute is OFF — approve to continue.")
    return {"status": "planned", "goal": goal, "workspace": ws, "plan": plan, "auto_executed": False}


@router.post("/run/execute")
async def execute_task(req: ExecuteRequest, _auth=Depends(require_api_key)):
    """Execute a previously-approved plan."""
    session = _get_session()
    _ensure_tools()
    session.set_mode("execute")
    session.add_message("assistant", "User approved. Starting execution…")

    def _run():
        with _orchestrator_lock:
            try:
                from orchestrator import execute_plan
                def cb(msg):
                    session.add_message("assistant", msg)
                result = execute_plan(req.plan, req.task, req.workspace_dir, status_cb=cb, max_iterations=req.max_iterations)
                if result:
                    v = result.get("verdict", {})
                    session.add_message("assistant", f"Build complete. Verdict: {v.get('verdict','N/A')} (score: {v.get('score','?')}/10)")
                    session.set_mode("discuss")
            except Exception as exc:
                session.add_message("assistant", f"Build error: {exc}")

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "goal": req.task, "workspace": req.workspace_dir}


# ── Session management ────────────────────────────────────────

@router.get("/session")
async def get_session_state():
    s = _get_session().state
    return {k: s.get(k) for k in [
        "session_id", "title", "mode", "current_goal", "workspace_dir",
        "iteration_count", "thinking_mode", "auto_execute", "max_debug_iterations",
    ]}


@router.post("/session/reset")
async def reset_session():
    global _session
    _get_session().reset()
    _session = None
    return {"status": "reset"}


@router.get("/sessions")
async def list_sessions():
    sessions = SessionManager.list_sessions()
    current = _get_session().session_id
    return {"sessions": sessions, "current_session_id": current}


@router.post("/sessions/switch")
async def switch_session(body: dict):
    global _session
    sid = body.get("session_id")
    if not sid:
        raise HTTPException(400, "session_id required")
    _session = SessionManager(session_id=sid)
    return {"status": "switched", "session_id": _session.session_id}


@router.post("/sessions/new")
async def new_session(body: dict = {}):
    global _session
    _session = SessionManager()
    title = body.get("title", "New Chat")
    if title and title != "New Chat":
        _session.set_title(title)
    return {"status": "created", "session_id": _session.session_id, "title": _session.state.get("title", "New Chat")}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    current = _get_session().session_id
    if session_id == current:
        raise HTTPException(400, "Cannot delete the active session")
    deleted = SessionManager.delete_session(session_id)
    if not deleted:
        raise HTTPException(404, f"Session not found: {session_id}")
    return {"status": "deleted", "session_id": session_id}


# ── History & artifacts ───────────────────────────────────────

@router.get("/history")
async def get_history(last_n: int = Query(50)):
    s = _get_session()
    msgs = s.state.get("conversation", [])[-last_n:]
    return {"session_id": s.session_id, "messages": msgs, "total": len(s.state.get("conversation", []))}


@router.get("/artifacts")
async def get_artifacts(last_n: int = Query(20)):
    s = _get_session()
    return {"session_id": s.session_id, "artifacts": s.get_artifacts(last_n=last_n)}


# ── File operations ───────────────────────────────────────────

@router.get("/files")
async def list_files():
    session = _get_session()
    ws = session.state.get("workspace_dir")
    if not ws or not os.path.isdir(ws):
        return {"workspace": None, "files": []}
    files = []
    for r, dirs, fnames in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git", "venv")]
        for fn in fnames:
            fp = os.path.join(r, fn)
            files.append({"path": os.path.relpath(fp, ws).replace("\\", "/"), "size": os.path.getsize(fp)})
    return {"workspace": ws, "files": sorted(files, key=lambda f: f["path"])}


@router.get("/file")
async def read_file_endpoint(path: str = Query(...)):
    session = _get_session()
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


# ── Stop ─────────────────────────────────────────────────────

@router.post("/stop")
async def stop_all(request: Request, _auth=Depends(require_api_key)):
    """Stop all running tasks."""
    if _orchestrator_lock.locked():
        return {"status": "busy", "message": "Orchestrator is running; cannot interrupt cleanly."}
    return {"status": "idle", "message": "No active tasks."}


# ── Legacy /chat SSE (UI compatibility) ───────────────────────

@router.post("/chat")
async def chat_legacy(req: MessagesRequest, settings: ReflexionSettings = Depends(get_settings)):
    """Legacy /chat SSE endpoint for the existing Web UI."""
    session = _get_session()
    return _anthropic_sse_stream(_stream_legacy_chat(req, session))


async def _stream_legacy_chat(req: MessagesRequest, session: SessionManager):
    """Old-style SSE: {token, done, full_response}."""
    user_text = req.messages[-1].text_content() if req.messages else ""
    context = session.get_conversation_context(last_n=8)
    role = req.role_hint or "chat"

    try:
        from memory.vector_store import get_relevant_context
        mem_ctx = get_relevant_context(user_text)
    except Exception:
        mem_ctx = ""

    prompt = f"{context}\n{mem_ctx}\nUser: {user_text}"
    sys_prompt = "You are Reflexion, a local autonomous coding assistant. Be direct and practical."

    full_parts: list[str] = []
    try:
        for token in call_model(role=role, prompt=prompt, stream=True, system_prompt=sys_prompt):
            full_parts.append(token)
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
        return

    full = "".join(full_parts)
    session.add_message("user", user_text)
    session.add_message("assistant", full)
    yield f"data: {json.dumps({'token': '', 'done': True, 'full_response': full})}\n\n"
