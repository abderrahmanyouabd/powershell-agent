# Quick Start

## 1. Set your API key

```powershell
$env:GROQ_API_KEY = "gsk_..."
```

Get one free at [console.groq.com/keys](https://console.groq.com/keys).

## 2. Install

```powershell
poetry install
```

## 3. Run

```powershell
# Direct prompt
poetry run powershell-agent "check git status and summarise what changed"

# Interactive mode
poetry run powershell-agent
```

---

## Common commands

```powershell
# Review each command before it runs
poetry run powershell-agent --review "create a new git branch"

# Limit agent iterations
poetry run powershell-agent --iterations 3 "find all TODO comments"

# List past sessions
poetry run powershell-agent --history

# Replay a session
poetry run powershell-agent --replay <session-id>

# Query a GitHub repo (needs GITHUB_TOKEN for private repos)
$env:GITHUB_TOKEN = "ghp_..."
poetry run powershell-agent --github "list open issues in owner/repo"
```

---

## Python API

```python
import asyncio
from powershell_agent import PowerShellAgent

async def main():
    agent = PowerShellAgent()
    response = await agent.run("find all python files and count them")
    print(response)

asyncio.run(main())
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GROQ_API_KEY` error | Set the env var (step 1 above) |
| `poetry: command not found` | `pip install poetry` |
| `No module named 'groq'` | `poetry install` |
| Command times out | Set `PS_TIMEOUT=600` env var |

---

See `README.md` for full documentation.
