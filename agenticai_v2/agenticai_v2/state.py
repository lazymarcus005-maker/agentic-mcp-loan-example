from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from threading import Lock

from agenticai_v2.config import get_default_provider_and_model

TITLE_MAX_LEN = 40


@dataclass
class ChatMessage:
    role: str
    content: str
    tools_used: list[str] = field(default_factory=list)
    model: str | None = None
    duration_seconds: float | None = None
    tokens_per_second: float | None = None


@dataclass
class ChatSession:
    id: str
    title: str = "แชทใหม่"
    messages: list[ChatMessage] = field(default_factory=list)


class AppState:
    """Single in-memory store for chat sessions and the active LLM provider/model.

    Everything here resets on process restart by design (no persistence layer).
    """

    def __init__(self, provider: str, model: str) -> None:
        self._lock = Lock()
        self.provider = provider
        self.model = model
        self._sessions: dict[str, ChatSession] = {}
        self._api_key_overrides: dict[str, str] = {}
        self._base_url_overrides: dict[str, str] = {}

    def create_session(self) -> ChatSession:
        with self._lock:
            session = ChatSession(id=uuid.uuid4().hex[:12])
            self._sessions[session.id] = session
            return session

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[ChatSession]:
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        tools_used: list[str] | None = None,
        model: str | None = None,
        duration_seconds: float | None = None,
        tokens_per_second: float | None = None,
    ) -> ChatSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if not session.messages and role == "user":
                session.title = content[:TITLE_MAX_LEN] + ("…" if len(content) > TITLE_MAX_LEN else "")
            session.messages.append(
                ChatMessage(
                    role=role,
                    content=content,
                    tools_used=tools_used or [],
                    model=model,
                    duration_seconds=duration_seconds,
                    tokens_per_second=tokens_per_second,
                )
            )
            return session

    def update_settings(self, provider: str, model: str) -> None:
        with self._lock:
            self.provider = provider
            self.model = model

    def set_api_key(self, provider: str, api_key: str) -> None:
        with self._lock:
            self._api_key_overrides[provider] = api_key

    def get_api_key_override(self, provider: str) -> str | None:
        return self._api_key_overrides.get(provider)

    def set_base_url(self, provider: str, base_url: str) -> None:
        with self._lock:
            self._base_url_overrides[provider] = base_url

    def get_base_url_override(self, provider: str) -> str | None:
        return self._base_url_overrides.get(provider)


app_state = AppState(*get_default_provider_and_model())


def get_app_state() -> AppState:
    return app_state
