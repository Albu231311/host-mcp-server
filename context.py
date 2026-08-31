"""Keeps the running conversation history for a single chat session.

Anthropic's Messages API is stateless: every call must include the full
message history for the model to "remember" earlier turns. This class
is just that list, plus small helpers to append user/assistant/tool
turns in the shape the API expects.
"""

from typing import Any


class ConversationContext:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, content: Any) -> None:
        """content is the raw content blocks list returned by the API
        (may include text blocks and tool_use blocks)."""
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_results(self, tool_results: list[dict[str, Any]]) -> None:
        """tool_results must be a list of {"type": "tool_result", ...} blocks,
        sent back as a single user-role message per Anthropic's API."""
        self.messages.append({"role": "user", "content": tool_results})

    def as_list(self) -> list[dict[str, Any]]:
        return self.messages

    def reset(self) -> None:
        self.messages.clear()
