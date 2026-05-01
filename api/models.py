# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                     ║
# ║  github.com/doriangraypng                               ║
# ╚══════════════════════════════════════════════════════════╝
"""
api/models.py — Pydantic request/response models for the Reflexion API.

Implements the Claude-compatible /v1/messages schema so that
Claude Code (and compatible clients) can connect unchanged.
"""
from __future__ import annotations

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field


# ── Message types ────────────────────────────────────────────

class ContentBlock(BaseModel):
    type: str
    text: Optional[str] = None


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: Union[str, list[ContentBlock]]

    def text_content(self) -> str:
        if isinstance(self.content, str):
            return self.content
        return " ".join(b.text or "" for b in self.content if b.text)


# ── Request models ───────────────────────────────────────────

class MessagesRequest(BaseModel):
    model: str = "reflexion-auto"
    messages: list[Message]
    system: Optional[str] = None
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    stream: bool = True
    metadata: Optional[dict[str, Any]] = None

    # Reflexion extensions
    role_hint: Optional[str] = None        # planner / builder / debugger / chat
    thinking: Optional[bool] = False
    workspace: Optional[str] = None


class TokenCountRequest(BaseModel):
    model: str = "reflexion-auto"
    messages: list[Message]
    system: Optional[str] = None


class RunRequest(BaseModel):
    goal: str
    workspace: Optional[str] = None
    max_iterations: Optional[int] = None
    auto_execute: bool = False
    thinking: bool = False


class ExecuteRequest(BaseModel):
    plan: dict
    task: str
    workspace_dir: str
    max_iterations: Optional[int] = None


# ── Response models ──────────────────────────────────────────

class ModelInfo(BaseModel):
    id: str
    display_name: str
    created_at: str = "1970-01-01T00:00:00Z"
    provider: str = "ollama"
    object: str = "model"


class ModelsListResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]
    first_id: Optional[str] = None
    last_id: Optional[str] = None
    has_more: bool = False


class TokenCountResponse(BaseModel):
    input_tokens: int


class UsageInfo(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class MessageResponse(BaseModel):
    id: str
    type: str = "message"
    role: str = "assistant"
    content: list[ContentBlock]
    model: str
    stop_reason: Optional[str] = "end_turn"
    stop_sequence: Optional[str] = None
    usage: UsageInfo = Field(default_factory=UsageInfo)
