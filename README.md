# RentaFlix Host

Console chatbot host for Universidad del Valle de Guatemala's CC3067
Networks, Project 1. It connects to Claude's API and coordinates
multiple MCP servers (Filesystem, Git, and the custom RentaFlix server)
as tools.

## Features implemented here

1. **LLM API connection** — talks to Claude via the official `anthropic`
   Python SDK (`main.py`).
2. **Session context** — `context.py` keeps the full message history so
   follow-up questions ("¿en qué fecha nació?" after "¿quién fue Alan
   Turing?") resolve correctly, since the whole history is resent on
   every call.
3. **MCP interaction log** — every tool request/response is printed to
   the console and appended to `mcp_interactions.log` (`logger.py`).
4. **Official MCP servers** — Filesystem and Git servers are wired up in
   `config.py` and dispatched through the same generic tool-call path as
   any other server (`mcp_client_manager.py`).
5. **Custom local MCP server** — RentaFlix (see the sibling
   `rentaflix-mcp/` repo) is loaded the same way, no special-casing
   needed.

## Requirements

- Python 3.10+
- Node.js + `npx` (for the official Filesystem MCP server)
- `uv` / `uvx` (for the official Git MCP server) — install from
  https://docs.astral.sh/uv/getting-started/installation/
- An Anthropic API key

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
export $(cat .env | xargs)   # or use a tool like python-dotenv / direnv
```

Make sure the RentaFlix server's dependencies are installed too (see
`../rentaflix-mcp/README.md`) and that `rentaflix.db` has been seeded:

```bash
cd ../rentaflix-mcp && pip install -r requirements.txt && python seed.py
```

## Running

```bash
python main.py
```

On startup it connects to all servers listed in `config.py`
(`filesystem`, `git`, `rentaflix`), auto-initializing a git repo inside
`host/workspace/` if one doesn't exist yet (the Git MCP server requires
that directory to already be a repo).

## Example session (functionality #4 demo)

```
You: create a file called notes.md with the text "hello from MCP", add it to git, and commit it
Assistant: [uses filesystem__write_file, then git__git_add, then git__git_commit]
           Done — created notes.md, staged it, and committed it with hash <...>.

You: who was Alan Turing?
Assistant: Alan Turing was a British mathematician and computer scientist...

You: what date was he born?
Assistant: June 23, 1912 (this follows up correctly because the
           conversation context includes the previous turn).

You: is "El Padrino" available to rent right now?
Assistant: [uses rentaflix__buscar_pelicula / verificar_disponibilidad]
           No copies are available right now; the next one is expected
           back on 2026-09-09. Similar titles with a free copy: ...
```

## Adding more servers

- **Part 2, item 6 (classmates' servers):** add entries to
  `MCP_SERVERS` in `config.py` pointing at their published repos.
- **Part 2, item 7 (remote server):** MCP over HTTP/SSE isn't wired up
  yet in `mcp_client_manager.py` (it currently only speaks stdio) — add
  an `streamablehttp_client`/`sse_client` branch there once the remote
  server is deployed, and capture that traffic with Wireshark for
  item 8.

## Project structure

```
host/
├── main.py                 # chat loop
├── context.py               # conversation history
├── logger.py                 # MCP interaction logging
├── config.py                  # which MCP servers to connect to
├── mcp_client_manager.py       # multi-server MCP connection + dispatch
├── requirements.txt
├── .env.example
└── workspace/                 # sandbox dir for Filesystem/Git MCP servers (gitignored)
```
