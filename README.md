# PowerShell Agentic Tool

A powerful agentic tool for executing **any** PowerShell command with streaming output and parallel execution support. Built with Poetry and Groq AI.

## Features

✨ **Single Universal Function** - One `run_powershell` tool that can execute ANY PowerShell command
🔄 **Streaming Output** - See command progress in real-time as it executes
⚡ **Parallel Execution** - Run multiple commands simultaneously for maximum efficiency
🤖 **Agentic Loop** - AI-powered autonomous decision making and command execution
🎯 **Comprehensive Support** - Git, grep (Select-String), file operations, system commands, and more

## Installation

```powershell
# Install dependencies
poetry install

# Set your Groq API key (get one free at console.groq.com)
$env:GROQ_API_KEY="your-api-key-here"
```

## Usage

### Interactive Mode

```powershell
poetry run python powershell_agent.py
```

Then enter natural language requests like:
- "Check the git status"
- "Find all Python files in this directory"
- "Search for the word 'function' in all .py files"
- "List all processes using more than 100MB of memory"

### Command Line Mode

```powershell
poetry run python powershell_agent.py "Search for TODO comments in all Python files"
```

### Programmatic Usage

```python
import asyncio
from powershell_agent import PowerShellAgent

async def example():
    agent = PowerShellAgent()
    
    # Single command with streaming
    result = await agent.run_powershell_command("git status")
    print(result)
    
    # Multiple commands in parallel
    commands = [
        "git status",
        "git log -n 5 --oneline",
        "Get-ChildItem -Recurse -Filter *.py"
    ]
    results = await agent.run_parallel_commands(commands)
    
    # Use the agentic loop
    response = await agent.run_agent("Find all Python files and count them")
    print(response)

asyncio.run(example())
```

## Tool Schema

The agent exposes a single powerful tool:

**`run_powershell`** - Execute any PowerShell command

Parameters:
- `command` (string, required): The PowerShell command to execute
- `stream_output` (boolean, optional): Whether to stream output in real-time (default: true)

## Example Commands

### Git Operations
```
"Show git status"
"Get the last 10 commits"
"Show files changed in the last commit"
```

### File Searching (grep equivalent)
```
"Search for 'function' in all Python files"
"Find TODO comments in this project"
"Search for import statements in .py files"
```

### File Operations
```
"List all files in the current directory"
"Find all files larger than 1MB"
"Count the number of Python files"
```

### System Operations
```
"Show running processes"
"Get system information"
"Check disk space"
```

### Complex Multi-Command Operations
The agent can break down complex requests into multiple PowerShell commands automatically!

```
"Check git status and show me the last 5 commits"
"Find all Python files and count how many there are"
"Search for TODO and FIXME comments across the codebase"
```

## How It Works

1. **User Input** - You provide a natural language request
2. **AI Planning** - The Groq LLM decides which PowerShell command(s) to run
3. **Streaming Execution** - Commands execute with real-time output streaming
4. **Result Processing** - AI interprets the results and responds in natural language
5. **Iteration** - The agent can make multiple tool calls to complete complex tasks

## Architecture

- **PowerShellAgent** - Main agent class with async execution support
- **run_powershell_command()** - Execute single commands with streaming
- **run_parallel_commands()** - Execute multiple commands concurrently
- **run_agent()** - Agentic loop with LLM orchestration

## Performance

- ⚡ **Async/Await** - Non-blocking command execution
- 🔄 **Parallel Processing** - Multiple commands run simultaneously
- 📊 **Streaming** - Real-time output without buffering delays
- ⏱️ **Timeout Protection** - Commands auto-terminate after 300s (configurable)

## Security Notes

⚠️ **Important**: This tool executes PowerShell commands on your system. Only use it with:
- Trusted prompts
- In controlled environments
- With appropriate access controls

## Requirements

- Python 3.10+
- Poetry
- Windows (for PowerShell)
- Groq API key (free tier available)

## License

MIT

## Contributing

Contributions welcome! This is an efficient, production-ready agentic PowerShell execution tool.
