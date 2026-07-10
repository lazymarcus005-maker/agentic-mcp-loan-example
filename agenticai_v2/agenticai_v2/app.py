from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agenticai_v2.agent import answer_question
from agenticai_v2.config import (
    AVAILABLE_PROVIDERS,
    get_app_host,
    get_app_port,
    get_env_api_key,
    get_env_openai_compatible_base_url,
    get_mcp_mssql_url,
    mask_secret,
)
from agenticai_v2.mcp_client import mcp_tool_to_openai_schema, open_mcp_session
from agenticai_v2.state import get_app_state

app = FastAPI(title="Agentic AI - LOAN Q&A")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

# Bumps on every process restart so browsers fetch fresh static assets
# instead of serving a stale cached copy after a redeploy.
STATIC_VERSION = uuid.uuid4().hex[:8]


class SessionSummary(BaseModel):
    id: str
    title: str
    message_count: int


class MessageOut(BaseModel):
    role: str
    content: str
    tools_used: list[str] = []
    model: str | None = None
    duration_seconds: float | None = None
    tokens_per_second: float | None = None


class SessionDetail(BaseModel):
    id: str
    title: str
    messages: list[MessageOut]


class SendMessageRequest(BaseModel):
    question: str


class ApiKeyInfo(BaseModel):
    masked: str
    has_value: bool


class SettingsOut(BaseModel):
    provider: str
    model: str
    available_providers: list[str]
    api_keys: dict[str, ApiKeyInfo]
    openai_compatible_base_url: str


class SettingsIn(BaseModel):
    provider: str
    model: str
    api_key: str | None = None
    openai_compatible_base_url: str | None = None


class McpToolOut(BaseModel):
    name: str
    description: str


class McpToolsOut(BaseModel):
    mcp_url: str
    mcp_name: str
    tools: list[McpToolOut]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"static_version": STATIC_VERSION})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "settings.html", {"static_version": STATIC_VERSION}
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionSummary)
async def create_session() -> SessionSummary:
    session = get_app_state().create_session()
    return SessionSummary(id=session.id, title=session.title, message_count=0)


@app.get("/api/sessions", response_model=list[SessionSummary])
async def list_sessions() -> list[SessionSummary]:
    return [
        SessionSummary(id=s.id, title=s.title, message_count=len(s.messages))
        for s in get_app_state().list_sessions()
    ]


@app.get("/api/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail:
    session = get_app_state().get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(
        id=session.id,
        title=session.title,
        messages=[
            MessageOut(
                role=m.role,
                content=m.content,
                tools_used=m.tools_used,
                model=m.model,
                duration_seconds=m.duration_seconds,
                tokens_per_second=m.tokens_per_second,
            )
            for m in session.messages
        ],
    )


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    deleted = get_app_state().delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@app.post("/api/sessions/{session_id}/messages", response_model=MessageOut)
async def send_message(session_id: str, request: SendMessageRequest) -> MessageOut:
    state = get_app_state()
    session = state.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state.add_message(session_id, "user", request.question)
    conversation = [{"role": m.role, "content": m.content} for m in session.messages]

    result = await answer_question(
        conversation,
        state.provider,
        state.model,
        api_key=state.get_api_key_override(state.provider),
        base_url=state.get_base_url_override(state.provider),
    )

    state.add_message(
        session_id,
        "assistant",
        result.content,
        tools_used=result.tools_used,
        model=result.model,
        duration_seconds=result.duration_seconds,
        tokens_per_second=result.tokens_per_second,
    )
    return MessageOut(
        role="assistant",
        content=result.content,
        tools_used=result.tools_used,
        model=result.model,
        duration_seconds=result.duration_seconds,
        tokens_per_second=result.tokens_per_second,
    )


def _build_settings_out() -> SettingsOut:
    state = get_app_state()
    api_keys: dict[str, ApiKeyInfo] = {}
    for p in AVAILABLE_PROVIDERS:
        effective = state.get_api_key_override(p)
        if effective is None:
            effective = get_env_api_key(p)
        api_keys[p] = ApiKeyInfo(masked=mask_secret(effective), has_value=bool(effective))

    base_url = state.get_base_url_override("openai_compatible")
    if base_url is None:
        base_url = get_env_openai_compatible_base_url()

    return SettingsOut(
        provider=state.provider,
        model=state.model,
        available_providers=AVAILABLE_PROVIDERS,
        api_keys=api_keys,
        openai_compatible_base_url=base_url,
    )


@app.get("/api/settings", response_model=SettingsOut)
async def get_settings() -> SettingsOut:
    return _build_settings_out()


@app.put("/api/settings", response_model=SettingsOut)
async def update_settings(request: SettingsIn) -> SettingsOut:
    if request.provider not in AVAILABLE_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
    state = get_app_state()
    state.update_settings(request.provider, request.model)
    if request.api_key:
        state.set_api_key(request.provider, request.api_key)
    if request.openai_compatible_base_url:
        state.set_base_url("openai_compatible", request.openai_compatible_base_url)
    return _build_settings_out()


@app.get("/api/mcp/tools", response_model=McpToolsOut)
async def get_mcp_tools() -> McpToolsOut:
    async with open_mcp_session() as (session, init_result):
        result = await session.list_tools()
        tools = [mcp_tool_to_openai_schema(t)["function"] for t in result.tools]
        return McpToolsOut(
            mcp_url=get_mcp_mssql_url(),
            mcp_name=init_result.serverInfo.name,
            tools=[McpToolOut(name=t["name"], description=t["description"]) for t in tools],
        )


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=get_app_host(), port=get_app_port())


if __name__ == "__main__":
    main()
