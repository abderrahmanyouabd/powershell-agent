"""
System prompt builder.

Centralises prompt logic so it can be tested and iterated without
touching the agent loop.  Sections are clearly named so a tech lead
can read the prompt like a document.
"""

import os
import platform
from pathlib import Path


class PromptBuilder:
    """
    Build the system prompt for the PowerShell agent.

    Context injected at runtime:
    - current working directory
    - OS / PowerShell version awareness
    - available tools (dynamic, injected by caller)
    """

    # Sections

    _ROLE = (
        "You are an expert PowerShell agentic assistant that completes tasks "
        "step-by-step by executing commands and reasoning about their output. "
        "You run on Windows and have full access to PowerShell, git, and the filesystem."
    )

    _FILE_OPS = """
FILE OPERATIONS
───────────────
SMART FILE READING:
- For targeted searches use Select-String with -Pattern and -Context (never read whole large files blindly).
- For general inspection, read incrementally: Get-Content file -TotalCount 30, then request more if needed.

FILE MODIFICATION:
- Write/overwrite: Set-Content or Out-File
- Replace text: (Get-Content f) -replace 'old','new' | Set-Content f
- Append: Add-Content
- Create new files with meaningful content using the write_file tool (no shell quoting issues)."""

    _NO_HALLUCINATE = """
NEVER HALLUCINATE FILE PATHS
─────────────────────────────
If asked about "the json file", "the config", etc. you DO NOT KNOW the exact name.
→ ALWAYS run `ls *.ext` or `Get-ChildItem *.ext` FIRST to discover what exists.
→ DO NOT assume names like Cargo.toml, package.json, settings.py — always discover first."""

    _STRATEGY = """
EXECUTION STRATEGY
──────────────────
- Run ONE command per tool call — observe output — then decide next step.
- Use pipes only when truly interdependent (e.g. Get-Process | Where-Object).
- Major workflow steps (search → analyze → modify) must be separate calls.
- Multiple iterations are expected and encouraged — use them.
- CRITICAL: When making a tool call, DO NOT explain what you are going to do first. Output ONLY the JSON tool call strictly, with no preamble text."""

    _EXPLAIN_VS_EXECUTE = """
EXPLAIN vs EXECUTE
──────────────────
- "how do I list files?" → just answer, no tool call.
- "list all files" → execute Get-ChildItem.
- When in doubt: questions → answer; instructions → execute."""

    #  Public API

    def build(self, cwd: str | None = None) -> str:
        """Return the complete system prompt string."""
        cwd_line = f"Current working directory: {cwd or Path.cwd()}"
        parts = [
            self._ROLE,
            f"\n{cwd_line}",
            self._FILE_OPS,
            self._NO_HALLUCINATE,
            self._STRATEGY,
            self._EXPLAIN_VS_EXECUTE,
            "\nAlways use the available tools. DO NOT hallucinate. Be concise in explanations.",
        ]
        return "\n".join(parts)


# Singleton for convenience
_builder = PromptBuilder()


def build_system_prompt(cwd: str | None = None) -> str:
    return _builder.build(cwd=cwd)
