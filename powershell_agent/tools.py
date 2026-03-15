"""
Tool registry for the PowerShell Agent.

A ToolRegistry holds named tool schemas (Groq/OpenAI function-calling format)
and maps tool names to async handlers. Adding a new tool is a one-liner.
"""

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


async def _handle_read_file(
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
    limit: int = 100,
    **_: Any,
) -> Dict[str, Any]:
    """Read a file with line numbers, supports line ranges."""
    try:
        target = Path(path)
        if not target.exists():
            return {"status": "error", "output": "", "error": f"File not found: {path}", "return_code": -1}

        lines = target.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)

        if end_line is None:
            end_line = min(start_line + limit - 1, total_lines)

        start_line = max(1, start_line)
        end_line = min(end_line, total_lines)

        if start_line > end_line:
            return {"status": "error", "output": "", "error": "Invalid line range", "return_code": -1}

        selected_lines = {i + 1: lines[i] for i in range(start_line - 1, end_line)}

        stat = target.stat()
        return {
            "status": "success",
            "lines": selected_lines,
            "total_lines": total_lines,
            "file_info": {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "path": str(target.absolute()),
            },
            "error": None,
            "return_code": 0,
        }
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_edit_file(
    path: str,
    operation: str,
    start_line: int | None = None,
    end_line: int | None = None,
    new_content: str | None = None,
    search_text: str | None = None,
    replace_text: str | None = None,
    **_: Any,
) -> Dict[str, Any]:
    """Edit a file with line-aware operations: insert, replace, delete, replace_text."""
    import shutil

    try:
        target = Path(path)
        if not target.exists():
            return {"status": "error", "output": "", "error": f"File not found: {path}", "return_code": -1}

        backup_path = Path(f"{path}.bak")
        shutil.copy2(target, backup_path)

        lines = target.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)

        if operation == "insert":
            if start_line is None or start_line < 0 or start_line > total_lines:
                return {"status": "error", "output": "", "error": f"Invalid insert position: {start_line}", "return_code": -1}
            new_lines = new_content.splitlines() if new_content else []
            lines = lines[:start_line] + new_lines + lines[start_line:]
            action = f"Inserted {len(new_lines)} lines after line {start_line}"

        elif operation == "replace":
            if start_line is None or end_line is None:
                return {"status": "error", "output": "", "error": "start_line and end_line required for replace", "return_code": -1}
            start_line = max(1, start_line)
            end_line = min(end_line, total_lines)
            if start_line > end_line:
                return {"status": "error", "output": "", "error": "Invalid line range", "return_code": -1}
            new_lines = new_content.splitlines() if new_content else []
            lines = lines[:start_line - 1] + new_lines + lines[end_line:]
            action = f"Replaced lines {start_line}-{end_line} with {len(new_lines)} lines"

        elif operation == "delete":
            if start_line is None or end_line is None:
                return {"status": "error", "output": "", "error": "start_line and end_line required for delete", "return_code": -1}
            start_line = max(1, start_line)
            end_line = min(end_line, total_lines)
            if start_line > end_line:
                return {"status": "error", "output": "", "error": "Invalid line range", "return_code": -1}
            lines = lines[:start_line - 1] + lines[end_line:]
            action = f"Deleted lines {start_line}-{end_line}"

        elif operation == "replace_text":
            if search_text is None:
                return {"status": "error", "output": "", "error": "search_text required for replace_text", "return_code": -1}
            content = target.read_text(encoding="utf-8")
            if search_text not in content:
                return {"status": "error", "output": "", "error": f"Text not found: {search_text}", "return_code": -1}
            count = content.count(search_text)
            content = content.replace(search_text, replace_text or "")
            target.write_text(content, encoding="utf-8")
            return {
                "status": "success",
                "backup_created": str(backup_path),
                "replacements_made": count,
                "output": f"Replaced {count} occurrence(s) of '{search_text}'",
                "error": None,
                "return_code": 0,
            }

        else:
            return {"status": "error", "output": "", "error": f"Unknown operation: {operation}", "return_code": -1}

        target.write_text("\n".join(lines), encoding="utf-8")

        return {
            "status": "success",
            "backup_created": str(backup_path),
            "lines_modified": action,
            "total_lines": len(lines),
            "output": f"File updated. {action}. Backup saved to {backup_path}",
            "error": None,
            "return_code": 0,
        }
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_list_files(
    path: str = ".",
    pattern: str = "*",
    recursive: bool = False,
    include_hidden: bool = False,
    **_: Any,
) -> Dict[str, Any]:
    """List files and directories using Get-ChildItem."""
    try:
        import json

        cmd = f"Get-ChildItem -Path '{path}' -Filter '{pattern}'"
        if recursive:
            cmd += " -Recurse"
        if include_hidden:
            cmd += " -Force"
        cmd += " | Select-Object Name, FullName, PSIsContainer, Length, LastWriteTime | ConvertTo-Json -Compress"

        result = await run_powershell(cmd, stream_output=False)

        if result["return_code"] != 0:
            return result

        try:
            data = json.loads(result["output"]) if result["output"] else []
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            return {"status": "error", "output": "", "error": "Failed to parse output", "return_code": -1}

        files = []
        for item in data:
            files.append({
                "name": item.get("Name"),
                "full_path": item.get("FullName"),
                "type": "Directory" if item.get("PSIsContainer") else "File",
                "size": item.get("Length", 0),
                "modified": str(item.get("LastWriteTime", "")),
            })

        return {
            "status": "success",
            "files": files,
            "total": len(files),
            "output": f"Found {len(files)} items",
            "error": None,
            "return_code": 0,
        }
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_copy_file(
    path: str,
    destination: str,
    overwrite: bool = False,
    **_: Any,
) -> Dict[str, Any]:
    """Copy a file or directory. REQUIRES --review mode."""
    try:
        force_flag = "-Force" if overwrite else ""
        cmd = f"Copy-Item -Path '{path}' -Destination '{destination}' {force_flag} -PassThru | Select-Object FullName, Exists | ConvertTo-Json"
        return await run_powershell(cmd, stream_output=True)
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_move_file(
    path: str,
    destination: str,
    overwrite: bool = False,
    **_: Any,
) -> Dict[str, Any]:
    """Move or rename a file or directory. REQUIRES --review mode."""
    try:
        force_flag = "-Force" if overwrite else ""
        cmd = f"Move-Item -Path '{path}' -Destination '{destination}' {force_flag} -PassThru | Select-Object FullName, Exists | ConvertTo-Json"
        return await run_powershell(cmd, stream_output=True)
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_delete_item(
    path: str,
    recursive: bool = False,
    force: bool = False,
    **_: Any,
) -> Dict[str, Any]:
    """Delete a file or directory. REQUIRES --review mode."""
    try:
        recurse_flag = "-Recurse" if recursive else ""
        force_flag = "-Force" if force else ""
        confirm_flag = "-Confirm:$false"
        cmd = f"Remove-Item -Path '{path}' {recurse_flag} {force_flag} {confirm_flag} -ErrorAction Stop"
        return await run_powershell(cmd, stream_output=True)
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


async def _handle_search_content(
    path: str,
    pattern: str,
    case_sensitive: bool = True,
    recursive: bool = False,
    file_pattern: str = "*",
    **_: Any,
) -> Dict[str, Any]:
    """Search for content within files using Select-String (PowerShell grep)."""
    try:
        import json

        case_flag = "" if case_sensitive else "-CaseSensitive"
        recurse_flag = "-Recurse" if recursive else ""
        cmd = f"Select-String -Path '{path}\\{file_pattern}' -Pattern '{pattern}' {case_flag} {recurse_flag} -AllMatches | Select-Object Path, LineNumber, Line | ConvertTo-Json -Compress"

        result = await run_powershell(cmd, stream_output=False)

        if result["return_code"] != 0:
            if "no matches" in result.get("output", "").lower():
                return {"status": "success", "matches": [], "total_matches": 0, "output": "No matches found", "error": None, "return_code": 0}
            return result

        try:
            data = json.loads(result["output"]) if result["output"] else []
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            return {"status": "success", "matches": [], "total_matches": 0, "output": "No matches found", "error": None, "return_code": 0}

        matches = []
        for item in data:
            matches.append({
                "file": Path(item.get("Path", "")).name,
                "full_path": item.get("Path"),
                "line": item.get("LineNumber"),
                "content": item.get("Line", "").strip(),
            })

        return {
            "status": "success",
            "matches": matches,
            "total_matches": len(matches),
            "output": f"Found {len(matches)} match(es)",
            "error": None,
            "return_code": 0,
        }
    except Exception as exc:
        return {"status": "error", "output": "", "error": str(exc), "return_code": -1}


_SCHEMA_READ_FILE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read a file with line numbers. Supports reading specific line ranges "
            "to avoid loading large files. Returns lines as a dictionary with line numbers as keys."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative or absolute file path to read."},
                "start_line": {"type": "integer", "description": "Starting line number (1-indexed). Default 1."},
                "end_line": {"type": "integer", "description": "Ending line number. Default: start_line + limit."},
                "limit": {"type": "integer", "description": "Maximum lines to read. Default 100."},
            },
            "required": ["path"],
        },
    },
}

_SCHEMA_EDIT_FILE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Edit a file with line-aware operations: insert, replace, delete, or replace_text. "
            "ALWAYS creates a .bak backup before modification. "
            "Use start_line/end_line for line ranges, or search_text for text replacement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit."},
                "operation": {"type": "string", "description": "Operation: insert, replace, delete, or replace_text."},
                "start_line": {"type": "integer", "description": "For insert: line to insert AFTER. For replace/delete: range start."},
                "end_line": {"type": "integer", "description": "For replace/delete: range end."},
                "new_content": {"type": "string", "description": "Content to insert or replace with."},
                "search_text": {"type": "string", "description": "Text to find for replace_text operation."},
                "replace_text": {"type": "string", "description": "Replacement text for replace_text operation."},
            },
            "required": ["path", "operation"],
        },
    },
}

_SCHEMA_LIST_FILES: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": (
            "List files and directories using PowerShell Get-ChildItem. "
            "Supports pattern filtering, recursive search, and hidden files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list. Default '.'."},
                "pattern": {"type": "string", "description": "Filter pattern (e.g., '*.ps1', '*.txt'). Default '*'."},
                "recursive": {"type": "boolean", "description": "Include subdirectories. Default false."},
                "include_hidden": {"type": "boolean", "description": "Include hidden files. Default false."},
            },
        },
    },
}

_SCHEMA_COPY_FILE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "copy_file",
        "description": (
            "Copy a file or directory to a destination. "
            "WARNING: This is a destructive operation. REQUIRES --review mode."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Source path to copy."},
                "destination": {"type": "string", "description": "Destination path."},
                "overwrite": {"type": "boolean", "description": "Overwrite if destination exists. Default false."},
            },
            "required": ["path", "destination"],
        },
    },
}

_SCHEMA_MOVE_FILE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "move_file",
        "description": (
            "Move or rename a file or directory. "
            "WARNING: This is a destructive operation. REQUIRES --review mode."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Source path to move."},
                "destination": {"type": "string", "description": "Destination path."},
                "overwrite": {"type": "boolean", "description": "Overwrite if destination exists. Default false."},
            },
            "required": ["path", "destination"],
        },
    },
}

_SCHEMA_DELETE_ITEM: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "delete_item",
        "description": (
            "Delete a file or directory. "
            "WARNING: This is a destructive operation. REQUIRES --review mode."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete."},
                "recursive": {"type": "boolean", "description": "Delete directories recursively. Default false."},
                "force": {"type": "boolean", "description": "Force delete read-only/hidden files. Default false."},
            },
            "required": ["path"],
        },
    },
}

_SCHEMA_SEARCH_CONTENT: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_content",
        "description": (
            "Search for text within files using PowerShell Select-String (grep equivalent). "
            "Returns matching lines with file paths and line numbers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory or file path to search."},
                "pattern": {"type": "string", "description": "Search pattern (regex or literal)."},
                "case_sensitive": {"type": "boolean", "description": "Case sensitive search. Default true."},
                "recursive": {"type": "boolean", "description": "Search recursively. Default false."},
                "file_pattern": {"type": "string", "description": "File filter pattern (e.g., '*.ps1'). Default '*'."},
            },
            "required": ["path", "pattern"],
        },
    },
}


def build_default_registry() -> ToolRegistry:
    """Return a ToolRegistry pre-loaded with all built-in tools."""
    registry = ToolRegistry()
    registry.register(_SCHEMA_RUN_POWERSHELL, _handle_run_powershell)
    registry.register(_SCHEMA_WRITE_FILE, _handle_write_file)
    registry.register(_SCHEMA_READ_FILE, _handle_read_file)
    registry.register(_SCHEMA_EDIT_FILE, _handle_edit_file)
    registry.register(_SCHEMA_LIST_FILES, _handle_list_files)
    registry.register(_SCHEMA_COPY_FILE, _handle_copy_file)
    registry.register(_SCHEMA_MOVE_FILE, _handle_move_file)
    registry.register(_SCHEMA_DELETE_ITEM, _handle_delete_item)
    registry.register(_SCHEMA_SEARCH_CONTENT, _handle_search_content)
    return registry
