"""
Tool registry for the PowerShell Agent.

A ToolRegistry holds named tool schemas (Groq/OpenAI function-calling format)
and maps tool names to async handlers. Adding a new tool is a one-liner.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List

from .executor import run_powershell


Handler = Callable[..., Coroutine[Any, Any, Dict[str, Any]]]


class ToolRegistry:
    """
    Stores OpenAI-style tool schemas and their corresponding async handlers.

    Usage:
        registry = ToolRegistry()
        registry.register(schema_dict, my_handler)
        tools_json = registry.schemas()
        result = await registry.call("my_tool", {"arg": "val"})
    """

    def __init__(self) -> None:
        self._schemas: List[Dict[str, Any]] = []
        self._handlers: Dict[str, Handler] = {}

    def register(self, schema: Dict[str, Any], handler: Handler) -> None:
        name = schema["function"]["name"]
        self._schemas.append(schema)
        self._handlers[name] = handler

    def schemas(self) -> List[Dict[str, Any]]:
        return list(self._schemas)

    async def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            return {
                "status": "error",
                "error": f"Unknown tool: {name}",
                "output": "",
                "return_code": -1,
            }
        return await handler(**args)


async def _handle_run_powershell(
    command: str,
    stream_output: bool = True,
    **_: Any,
) -> Dict[str, Any]:
    if isinstance(stream_output, str):
        stream_output = stream_output.lower() in ("true", "1", "yes")
    if not isinstance(stream_output, bool):
        stream_output = True
    return await run_powershell(command, stream_output=stream_output)


async def _handle_write_file(
    path: str,
    content: str,
    append: bool = False,
    **_: Any,
) -> Dict[str, Any]:
    """Write or append text content to a local file."""
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(target, mode, encoding="utf-8") as fh:
            fh.write(content)
        action = "appended to" if append else "written to"
        return {
            "status": "success",
            "output": f"Content {action} {path} ({len(content)} chars)",
            "error": None,
            "return_code": 0,
        }
    except Exception as exc:
        return {
            "status": "error",
            "output": "",
            "error": str(exc),
            "return_code": -1,
        }


_SCHEMA_RUN_POWERSHELL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_powershell",
        "description": (
            "Execute any PowerShell command: git, filesystem, system info, "
            "Select-String (grep), registry, networking, and more. "
            "Output is streamed in real-time. "
            "Prefer separate calls for distinct steps rather than one huge pipeline."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The PowerShell command string to execute.",
                },
            },
            "required": ["command"],
        },
    },
}

_SCHEMA_WRITE_FILE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write or append text content to a file on disk. "
            "Use this to create new files, save generated code, patch config files, "
            "or write reports."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute file path to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write into the file.",
                },
                "append": {
                    "type": "boolean",
                    "description": "If true, append instead of overwrite. Default false.",
                },
            },
            "required": ["path", "content"],
        },
    },
}


def build_default_registry() -> ToolRegistry:
    """Return a ToolRegistry pre-loaded with all built-in tools."""
    registry = ToolRegistry()
    registry.register(_SCHEMA_RUN_POWERSHELL, _handle_run_powershell)
    registry.register(_SCHEMA_WRITE_FILE, _handle_write_file)
    return registry
