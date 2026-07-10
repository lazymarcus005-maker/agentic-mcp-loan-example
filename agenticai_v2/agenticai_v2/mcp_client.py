from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import InitializeResult

from agenticai_v2.config import get_mcp_mssql_url


def mcp_tool_to_openai_schema(tool: Any) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }


@asynccontextmanager
async def open_mcp_session(
    url: str | None = None,
) -> AsyncIterator[tuple[ClientSession, InitializeResult]]:
    """Opens one MCP session for the duration of a single agent request.

    Kept as one session per request (not per tool call) so a multi-tool-call
    turn reuses the same connection instead of re-initializing repeatedly.
    """
    async with streamablehttp_client(url or get_mcp_mssql_url()) as (read, write, _):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            yield session, init_result
