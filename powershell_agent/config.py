"""
Central configuration for PowerShell Agent.
All settings are overridable via environment variables.
"""

import os
from pathlib import Path
# model
DEFAULT_MODEL = os.getenv("MODEL_PS", "llama-3.3-70b-versatile")
DEFAULT_TEMPERATURE = float(os.getenv("PS_TEMPERATURE", "0.1"))
MAX_ITERATIONS = int(os.getenv("PS_MAX_ITERATIONS", "10"))
#timeout 
COMMAND_TIMEOUT = int(os.getenv("PS_TIMEOUT", "300"))
# history
HISTORY_DIR = Path(os.getenv("PS_HISTORY_DIR", Path.home() / ".powershell-agent" / "history"))
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

VERSION = "0.3.0"

# mcp setup
GITHUB_MCP_URL = "https://mcp.github.com/v1"
GITHUB_MCP_LABEL = "github"
GITHUB_MCP_DESCRIPTION = (
    "Access GitHub repositories: list/read files, search code, create/read issues, "
    "get commit history, check pull requests, and browse repository structure."
)
