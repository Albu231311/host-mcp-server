import os
from contextlib import asynccontextmanager
from typing import Any

import anthropic
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import logger
from config import MCP_SERVERS
from context import ConversationContext
from mcp_client_manager import MCPClientManager

# Variables Globales (solo para este demo single-user)
MODEL = "claude-sonnet-4-5"  # Match main.py's model string
SYSTEM_PROMPT = (
    "You are the assistant for RentaFlix, a physical movie rental store. "
    "Use the available tools to check real catalog, inventory, rental, "
    "and recommendation data instead of guessing. Always confirm "
    "availability and dates through the tools before answering. "
    "Please format your responses using Markdown."
)

manager: MCPClientManager
client: anthropic.AsyncAnthropic
context = ConversationContext()
tools_schema: list[dict[str, Any]] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, client, tools_schema
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set the ANTHROPIC_API_KEY environment variable first.")
    
    client = anthropic.AsyncAnthropic()
    manager = MCPClientManager(MCP_SERVERS)
    
    logger.log_info("Starting FastAPI server, connecting to MCP servers...")
    await manager.connect_all()
    await manager.refresh_schemas()
    tools_schema = manager.anthropic_tool_schemas()
    logger.log_info(f"Loaded {len(tools_schema)} tools.")
    
    yield
    
    logger.log_info("Shutting down, closing MCP connections...")
    await manager.close()

app = FastAPI(lifespan=lifespan)

# Montar los archivos estaticos del frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Maneja un mensaje del usuario usando el mismo ciclo de tools que main.py"""
    context.add_user_message(req.message)
    
    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=context.as_list(),
            tools=tools_schema,
        )
        
        context.add_assistant_message(response.content)
        
        # Enviar la respuesta de texto si la hay y NO se pidio usar tools.
        # Si pide tools, seguimos el ciclo (y acumulamos el texto)
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        
        if not tool_use_blocks:
            # Fin de las tools, extraer el texto final
            text_blocks = [b.text for b in response.content if b.type == "text"]
            final_reply = " ".join(text_blocks)
            return ChatResponse(reply=final_reply)

        # Ejecutar tools
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
