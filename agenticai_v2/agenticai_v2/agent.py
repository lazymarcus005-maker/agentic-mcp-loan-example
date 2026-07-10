from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from agenticai_v2.config import get_system_prompt
from agenticai_v2.llm_client import build_llm_client
from agenticai_v2.mcp_client import mcp_tool_to_openai_schema, open_mcp_session

MAX_TOOL_ITERATIONS = 8


@dataclass
class AnswerResult:
    content: str
    model: str
    tools_used: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    tokens_per_second: float | None = None


async def answer_question(
    conversation: list[dict[str, Any]],
    provider: str,
    model: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AnswerResult:
    """conversation is the prior turns of a session (role/content dicts, no system
    message) ending with the newest user message."""
    client, model = build_llm_client(provider, model, api_key=api_key, base_url=base_url)
    system_prompt = get_system_prompt()

    started = time.monotonic()
    tools_used: list[str] = []
    completion_tokens = 0

    async with open_mcp_session() as (session, _init_result):
        tools_result = await session.list_tools()
        openai_tools = [mcp_tool_to_openai_schema(tool) for tool in tools_result.tools]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *conversation,
        ]

        for _ in range(MAX_TOOL_ITERATIONS):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools,
            )
            if response.usage is not None:
                completion_tokens += response.usage.completion_tokens or 0
            message = response.choices[0].message

            if not message.tool_calls:
                return _build_result(message.content or "", model, tools_used, started, completion_tokens)

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                }
            )

            for tool_call in message.tool_calls:
                if tool_call.function.name not in tools_used:
                    tools_used.append(tool_call.function.name)
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = await session.call_tool(tool_call.function.name, arguments)
                result_text = "\n".join(
                    part.text for part in result.content if hasattr(part, "text")
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )

        fallback = "ขออภัย ไม่สามารถหาคำตอบได้ภายในจำนวนรอบที่กำหนด กรุณาลองถามใหม่อีกครั้ง"
        return _build_result(fallback, model, tools_used, started, completion_tokens)


def _build_result(
    content: str, model: str, tools_used: list[str], started: float, completion_tokens: int
) -> AnswerResult:
    duration = time.monotonic() - started
    tokens_per_second = (completion_tokens / duration) if duration > 0 and completion_tokens else None
    return AnswerResult(
        content=content,
        model=model,
        tools_used=tools_used,
        duration_seconds=duration,
        tokens_per_second=tokens_per_second,
    )
