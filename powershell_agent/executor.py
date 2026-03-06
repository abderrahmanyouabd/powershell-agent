"""
PowerShell subprocess executor.
Handles process creation, streaming stdout/stderr, and timeout enforcement.
"""

import asyncio
from typing import Dict, Any

from .config import COMMAND_TIMEOUT


_UTF8_SETUP = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; "


def _decode(raw: bytes) -> str:
    """Decode bytes preferring UTF-8, falling back to cp1252 for French/Western Windows."""
    try:
        return raw.decode("utf-8").rstrip()
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace").rstrip()


async def run_powershell(
    command: str,
    stream_output: bool = True,
    timeout: int = COMMAND_TIMEOUT,
) -> Dict[str, Any]:
    """
    Spawn a PowerShell process, stream its output, and return a result dict.

    Returns a dict with keys: status, command, output, error, return_code.
    UTF-8 output encoding is forced regardless of the system locale.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _UTF8_SETUP + command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=False,
        )

        output_lines: list[str] = []
        error_lines: list[str] = []

        async def _drain(stream: asyncio.StreamReader, lines: list[str], prefix: str) -> None:
            while True:
                raw = await stream.readline()
                if not raw:
                    break
                decoded = _decode(raw)
                lines.append(decoded)
                if stream_output and decoded:
                    print(f"{prefix}{decoded}")

        await asyncio.gather(
            _drain(process.stdout, output_lines, "  "),
            _drain(process.stderr, error_lines, "  ⚠  "),
        )

        try:
            return_code = await asyncio.wait_for(process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return {
                "status": "timeout",
                "command": command,
                "output": "\n".join(output_lines),
                "error": f"Command timed out after {timeout}s",
                "return_code": -1,
            }

        ok = return_code == 0
        return {
            "status": "success" if ok else "error",
            "command": command,
            "output": "\n".join(output_lines),
            "error": "\n".join(error_lines) if error_lines else None,
            "return_code": return_code,
        }

    except Exception as exc:
        return {
            "status": "exception",
            "command": command,
            "output": "",
            "error": str(exc),
            "return_code": -1,
        }
