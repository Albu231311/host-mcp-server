import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("git_pusher")

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")

@mcp.tool()
def git_push() -> str:
    """Sube (push) los commits locales del repositorio al servidor remoto."""
    try:
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return f"Push exitoso:\n{result.stdout}\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Error haciendo push:\n{e.stderr}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
