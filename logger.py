"""Logs every MCP interaction (tool call request + response) to both the
console and a log file, satisfying functionality #3 of the project
("mantener y mostrar un log de todas las interacciones con los
servidores MCP").
"""

import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent / "mcp_interactions.log"


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write(line: str) -> None:
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_tool_call(server_name: str, tool_name: str, arguments: dict) -> None:
    entry = {
        "timestamp": _timestamp(),
        "direction": "request",
        "server": server_name,
        "tool": tool_name,
        "arguments": arguments,
    }
    _write(f"[MCP -> {server_name}] {json.dumps(entry, ensure_ascii=False)}")


def log_tool_result(server_name: str, tool_name: str, result: object, is_error: bool = False) -> None:
    entry = {
        "timestamp": _timestamp(),
        "direction": "response",
        "server": server_name,
        "tool": tool_name,
        "is_error": is_error,
        "result": str(result)[:2000],  # avoid dumping huge payloads
    }
    _write(f"[MCP <- {server_name}] {json.dumps(entry, ensure_ascii=False)}")


def log_info(message: str) -> None:
    _write(f"[INFO {_timestamp()}] {message}")
