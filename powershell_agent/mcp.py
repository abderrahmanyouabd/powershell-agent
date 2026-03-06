"""
GitHub MCP integration via Groq Responses API.

Allows querying GitHub repositories (read files, search code, list issues,
get commit history) as additional context alongside local PowerShell execution.

Authentication: set GITHUB_TOKEN env var (classic PAT with repo scope).
Public repos work without a token.

Note: the Groq Responses API only supports a subset of models for MCP.
See MCP_SUPPORTED_MODELS below.
"""

import os
from typing import Any, Dict, List, Optional

import openai

from .config import GITHUB_MCP_URL, GITHUB_MCP_LABEL, GITHUB_MCP_DESCRIPTION, DEFAULT_MODEL


MCP_SUPPORTED_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2-instruct-0905",
    "meta-llama/llama-4-scout-17b-16e-instruct",
}


def _responses_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=os.environ.get("GROQ_API_KEY", ""),
        base_url="https://api.groq.com/openai/v1",
    )


def build_mcp_tools(github_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the MCP tool definition for the GitHub server."""
    token = github_token or os.environ.get("GITHUB_TOKEN", "")
    tool: Dict[str, Any] = {
        "type": "mcp",
        "server_label": GITHUB_MCP_LABEL,
        "server_url": GITHUB_MCP_URL,
        "server_description": GITHUB_MCP_DESCRIPTION,
        "require_approval": "never",
    }
    if token:
        tool["headers"] = {"Authorization": f"Bearer {token}"}
    return [tool]


def run_with_github_mcp(
    user_prompt: str,
    github_token: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Run a single-shot query against Groq Responses API with GitHub MCP tools enabled.

    Raises ValueError if the model does not support the Groq Responses API + MCP.

    Useful for tasks like:
        "Summarise the latest 3 commits in owner/repo"
        "Find all usages of run_powershell in abderrahmanyouabd/powershell-agent"

    Returns the final text response.
    """
    if model not in MCP_SUPPORTED_MODELS:
        supported = ", ".join(sorted(MCP_SUPPORTED_MODELS))
        raise ValueError(
            f"Model '{model}' does not support the Groq Responses API (required for --github).\n"
            f"Supported models: {supported}\n"
            f"Set MODEL_PS to one of the above, or leave it unset to use the default (llama-3.3-70b-versatile)."
        )

    client = _responses_client()
    tools = build_mcp_tools(github_token)

    response = client.responses.create(
        model=model,
        input=[{"type": "message", "role": "user", "content": user_prompt}],
        tools=tools,  # type: ignore[arg-type]
        stream=False,
    )

    for item in response.output:  # type: ignore[attr-defined]
        if getattr(item, "type", None) == "message":
            for chunk in item.content:
                if getattr(chunk, "type", None) == "output_text":
                    return chunk.text
    return str(response)
