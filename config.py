"""Declares which MCP servers the host connects to and how to launch each
one. Add/remove entries here to plug in more servers (e.g. classmates'
servers in Part 2, or the remote server in Part 2 item 7).
"""

import os
import subprocess

# Directory the Filesystem MCP server is allowed to read/write.
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# The Git MCP server refuses to start unless this is already a git repo.
if not os.path.isdir(os.path.join(WORKSPACE_DIR, ".git")):
    subprocess.run(["git", "init"], cwd=WORKSPACE_DIR, capture_output=True, check=False)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/Albu231311/mcp-redes-repo-default.git"],
        cwd=WORKSPACE_DIR, capture_output=True, check=False
    )

RENTAFLIX_SERVER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "rentaflix-mcp", "server.py"
)

COMPA_RRHH_SERVER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "mcp-server-rrhh-construccion", "server.py"
)

COMPA_HOTEL_SRC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hotel-mcp-server", "src"
)
hotel_env = dict(os.environ)
hotel_env["PYTHONPATH"] = os.path.abspath(COMPA_HOTEL_SRC_PATH)

MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", WORKSPACE_DIR],
        "env": dict(os.environ),  # npx needs its full env (proxy, npm config, etc.)
    },
    "git": {
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", WORKSPACE_DIR],
        "env": dict(os.environ),
    },
    "rentaflix": {
        "command": "python3",
        "args": [os.path.abspath(RENTAFLIX_SERVER_PATH)],
    },
    # Part 2, item 6: add two classmates' servers here once published, e.g.
    "compa_rrhh": {
        "command": "python3",
        "args": [os.path.abspath(COMPA_RRHH_SERVER_PATH)],
    },
    "compa_hotel": {
        "command": "python3",
        "args": ["-m", "hotel_mcp"],
        "env": hotel_env,
    },
    "git_pusher": {
        "command": "python3",
        "args": [os.path.join(os.path.dirname(__file__), "git_pusher.py")],
    },
    #
    # Part 2, item 7: remote MCP server (QuoteOfTheDay)
    # Deployed to Render.
    "remote_quotes": {
        "url": "https://remote-mcp-server-j94b.onrender.com/mcp",
    },
}
