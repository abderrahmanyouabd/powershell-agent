"""
PowerShell Agent package.

Public API: import from here, not from submodules directly.
"""

from .agent import PowerShellAgent
from .config import VERSION
from .memory import clear_sessions, list_sessions, load_session, save_session
from .mcp import run_with_github_mcp
from .tools import build_default_registry, ToolRegistry

__version__ = VERSION
__all__ = [
    "PowerShellAgent",
    "ToolRegistry",
    "build_default_registry",
    "list_sessions",
    "load_session",
    "save_session",
    "run_with_github_mcp",
    "__version__",
]
