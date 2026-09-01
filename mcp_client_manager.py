"""Manages connections to one or more MCP servers at once.

Responsibilities:
- Open a stdio **or streamable-http** connection + ClientSession per
  configured server.
- Aggregate every server's tools into the flat list Anthropic's API
  expects (prefixing names to avoid collisions across servers).
- Route a tool_use call from the model back to the right server.
- Log every request/response via logger.py.
"""

from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

import logger

# Anthropic tool names must match ^[a-zA-Z0-9_-]{1,128}$, so we join
# server name and tool name with "__" instead of a dot.
NAME_SEP = "__"


class MCPClientManager:
    def __init__(self, servers: dict[str, dict[str, Any]]) -> None:
        self._server_configs = servers
        self._sessions: dict[str, ClientSession] = {}
        self._stack = AsyncExitStack()
        # combined_name -> (server_name, original_tool_name)
        self._tool_index: dict[str, tuple[str, str]] = {}

    async def connect_all(self) -> None:
        for name, cfg in self._server_configs.items():
            try:
                await self._connect_one(name, cfg)
                logger.log_info(f"Connected to MCP server '{name}'")
            except Exception as exc:  # noqa: BLE001 - surface any startup failure
                logger.log_info(f"Failed to connect to MCP server '{name}': {exc}")

    async def _connect_one(self, name: str, cfg: dict[str, Any]) -> None:
        if "url" in cfg:
            # ---- Remote server (Streamable HTTP) ----
            url = cfg["url"]
            headers = cfg.get("headers", {})
            read, write, _ = await self._stack.enter_async_context(
                streamablehttp_client(url=url, headers=headers)
            )
        else:
            # ---- Local server (stdio) ----
            params = StdioServerParameters(
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )
            read, write = await self._stack.enter_async_context(
                stdio_client(params)
            )

        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[name] = session

        tools = await session.list_tools()
        for t in tools.tools:
            combined = f"{name}{NAME_SEP}{t.name}"
            self._tool_index[combined] = (name, t.name)

    def anthropic_tool_schemas(self) -> list[dict[str, Any]]:
        """Returns tool definitions in the shape Anthropic's Messages API
        expects, pulled live from each connected server's list_tools()."""
        return self._schema_cache

    async def refresh_schemas(self) -> None:
        self._schema_cache: list[dict[str, Any]] = []
        for server_name, session in self._sessions.items():
            tools = await session.list_tools()
            for t in tools.tools:
                self._schema_cache.append(
                    {
                        "name": f"{server_name}{NAME_SEP}{t.name}",
                        "description": t.description or "",
                        "input_schema": t.inputSchema,
                    }
                )

    async def call_tool(self, combined_name: str, arguments: dict[str, Any]) -> str:
        server_name, tool_name = self._tool_index[combined_name]
        session = self._sessions[server_name]

        logger.log_tool_call(server_name, tool_name, arguments)
        try:
            result = await session.call_tool(tool_name, arguments)
        except Exception as exc:  # noqa: BLE001
            logger.log_tool_result(server_name, tool_name, str(exc), is_error=True)
            return f"Error calling {tool_name} on {server_name}: {exc}"

        text_parts = [block.text for block in result.content if hasattr(block, "text")]
        combined_text = "\n".join(text_parts) if text_parts else str(result.content)
        logger.log_tool_result(server_name, tool_name, combined_text, is_error=result.isError)
        return combined_text

    async def close(self) -> None:
        await self._stack.aclose()
