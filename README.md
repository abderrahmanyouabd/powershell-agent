# powershell-agent

A natural language interface for PowerShell, powered by Groq. You describe what you want done, and the agent figures out which commands to run, executes them step by step, and gives you a summary of what happened.

## Requirements

- Python 3.10+
- Windows (PowerShell)
- [Groq API key](https://console.groq.com/keys) (free tier works)

## Setup

```powershell
poetry install

$env:GROQ_API_KEY = "gsk_..."
```

Optional overrides:

| Variable | Default | Description |
|---|---|---|
| `MODEL_PS` | `llama-3.3-70b-versatile` | Groq model to use |
| `GITHUB_TOKEN` | — | GitHub PAT for `--github` queries |
| `PS_MAX_ITERATIONS` | `10` | Max agent loop iterations |
| `PS_TIMEOUT` | `300` | Command timeout in seconds |
| `PS_HISTORY_DIR` | `~/.powershell-agent/history` | Where sessions are saved |

## Usage

```powershell
# Direct prompt
poetry run powershell-agent "find all TODO comments in python files"

# Review each command before it runs
poetry run powershell-agent --review "create a feature branch for dark mode"

# Interactive
poetry run powershell-agent
```

## CLI Flags

| Flag | Description |
|---|---|
| `--review` | Approve / skip / edit / quit each command before it runs |
| `--model <name>` | Override the model for this session |
| `--iterations <n>` | Max number of agent iterations |
| `--history` | List past sessions |
| `--replay <id>` | Print the commands and response from a past session |
| `--github "<query>"` | Query GitHub via MCP (see below) |
| `--version` | Print version |

## GitHub MCP

The agent can query GitHub repositories using the [Model Context Protocol](https://modelcontextprotocol.io/) via Groq's Responses API. Set `GITHUB_TOKEN` for private repos; public repos work without it.

**Supported models for `--github`** (Groq Responses API restriction):
`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen/qwen3-32b`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`

Models like `mixtral` and `gemma` are **not supported** and will return an error. The default model works fine.

```powershell
$env:GITHUB_TOKEN = "ghp_..."

poetry run powershell-agent --github "summarise the open issues in abderrahmanyouabd/powershell-agent"
poetry run powershell-agent --github "what changed in the last 5 commits of abderrahmanyouabd/powershell-agent"
```

## Session History

Every run is saved to disk automatically.

```powershell
# List sessions
poetry run powershell-agent --history

# Replay one
poetry run powershell-agent --replay abc123def456
```

## Developer Usage

```python
import asyncio
from powershell_agent import PowerShellAgent, list_sessions

async def main():
    agent = PowerShellAgent()
    response = await agent.run("find all python files and count them")
    print(response)

    # Past sessions
    for s in list_sessions(limit=5):
        print(s["id"], s["prompt_preview"])

asyncio.run(main())
```

### Adding a custom tool

```python
from powershell_agent.tools import build_default_registry

registry = build_default_registry()

schema = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Does something useful.",
        "parameters": {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        },
    },
}

async def my_handler(input: str, **_):
    return {"status": "success", "output": f"got: {input}", "error": None, "return_code": 0}

registry.register(schema, my_handler)
agent = PowerShellAgent(registry=registry)
```

## Running Tests

```powershell
poetry run pytest tests/ -v
```

## Architecture

```
powershell_agent/
  config.py     # all constants + env-var overrides
  executor.py   # PowerShell subprocess engine
  tools.py      # ToolRegistry + built-in tools (run_powershell, write_file)
  prompt.py     # system prompt builder
  memory.py     # session persistence
  agent.py      # agentic loop
  mcp.py        # GitHub MCP via Groq Responses API
cli.py          # CLI entry point
tests/          # pytest suite
```

## Security

This tool executes PowerShell commands on your machine. Use `--review` mode when you want to approve each command before it runs, especially for unfamiliar prompts.

## License

[MIT](LICENSE)
