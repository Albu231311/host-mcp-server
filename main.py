"""
RentaFlix Host — console chatbot that connects to Claude's API and uses
one or more MCP servers (Filesystem, Git, RentaFlix, ...) as tools.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python main.py
"""

import asyncio
import os

import anthropic

import logger
from config import MCP_SERVERS
from context import ConversationContext
from mcp_client_manager import MCPClientManager

MODEL = "claude-sonnet-4-5"  # swap for whichever model you have credits for
SYSTEM_PROMPT = (
    "You are the assistant for RentaFlix, a physical movie rental store. "
    "Use the available tools to check real catalog, inventory, rental, "
    "and recommendation data instead of guessing. Always confirm "
    "availability and dates through the tools before answering."
)


async def run_chat() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set the ANTHROPIC_API_KEY environment variable first.")

    client = anthropic.Anthropic()
    context = ConversationContext()
    manager = MCPClientManager(MCP_SERVERS)

    await manager.connect_all()
    await manager.refresh_schemas()
    tools = manager.anthropic_tool_schemas()
    logger.log_info(f"Loaded {len(tools)} tools from {len(MCP_SERVERS)} configured servers.")

    print("RentaFlix chatbot ready. Type 'exit' to quit.\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                continue

            context.add_user_message(user_input)
            await handle_turn(client, context, manager, tools)
    finally:
        await manager.close()


async def handle_turn(
    client: anthropic.Anthropic,
    context: ConversationContext,
    manager: MCPClientManager,
    tools: list[dict],
) -> None:
    """Runs one user turn to completion, looping through as many tool
    calls as the model requests before printing the final text answer."""
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=context.as_list(),
            tools=tools,
        )

        context.add_assistant_message(response.content)

        text_blocks = [b.text for b in response.content if b.type == "text"]
        if text_blocks:
            print(f"Assistant: {' '.join(text_blocks)}")

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break  # model gave a final answer, no more tools requested

        tool_results = []
        for block in tool_use_blocks:
            result_text = await manager.call_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                }
            )
        context.add_tool_results(tool_results)
        # Loop again so the model can see the tool results and respond.


if __name__ == "__main__":
    asyncio.run(run_chat())
