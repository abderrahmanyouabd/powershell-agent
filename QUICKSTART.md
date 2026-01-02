# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Set Your API Key

Get a free Groq API key from [console.groq.com/keys](https://console.groq.com/keys)

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY="your-actual-api-key-here"
```

**Or create a `.env` file:**
```bash
cp .env.example .env
# Then edit .env and add your API key
```

### 2. Install Dependencies

```powershell
poetry install
```

### 3. Run It!

**Interactive Mode (Recommended for first time):**
```powershell
poetry run python powershell_agent.py
```

Then try these prompts:
- `Check git status`
- `Find all Python files`
- `Search for TODO in all files`
- `List the 5 largest files`

**Direct Command Mode:**
```powershell
poetry run python powershell_agent.py "List all Python files and count them"
```

**Run Examples:**
```powershell
poetry run python examples.py
```

## 🎯 What Can It Do?

### Git Operations
```
"Show me the git status"
"Get the last 10 commits"
"Show what changed in the last commit"
```

### File Searching (like grep)
```
"Search for 'import' in all Python files"
"Find TODO comments"
"Search for function definitions in .py files"
```

### File Management
```
"List all files larger than 1MB"
"Count how many .md files there are"
"Show the 10 largest files"
```

### System Info
```
"Show running processes"
"Get disk space info"
"Show system information"
```

### Complex Multi-Step Tasks
The AI automatically breaks these down into multiple PowerShell commands:
```
"Check git status and show me the last 5 commits"
"Find all Python files, count them, and show the largest one"
"Search for TODO and FIXME comments and count how many there are"
```

## 🔥 Key Features

✅ **Single Universal Tool** - One function that runs ANY PowerShell command
✅ **Streaming Output** - See results in real-time as they happen
✅ **Parallel Execution** - Multiple commands run simultaneously
✅ **AI-Powered** - Natural language → PowerShell commands automatically
✅ **Efficient** - Async/await for maximum performance

## 📖 Examples

### Example 1: Basic Usage
```python
import asyncio
from powershell_agent import PowerShellAgent

async def main():
    agent = PowerShellAgent()
    
    # Single command
    result = await agent.run_powershell_command("git status")
    print(result)

asyncio.run(main())
```

### Example 2: Parallel Commands
```python
async def main():
    agent = PowerShellAgent()
    
    commands = [
        "git status",
        "git log -n 5 --oneline",
        "Get-ChildItem *.py"
    ]
    
    results = await agent.run_parallel_commands(commands)
    for r in results:
        print(f"{r['command']}: {r['status']}")

asyncio.run(main())
```

### Example 3: Agentic Mode
```python
async def main():
    agent = PowerShellAgent()
    
    # AI decides which commands to run
    response = await agent.run_agent(
        "Find all Python files and tell me how many there are"
    )
    print(response)

asyncio.run(main())
```

## 🛠️ Troubleshooting

**"GROQ_API_KEY not set"**
- Set the environment variable: `$env:GROQ_API_KEY="your-key"`
- Or create a `.env` file with your key

**"poetry: command not found"**
- Install Poetry: `pip install poetry`

**"No module named 'groq'"**
- Run: `poetry install`

**Commands timeout**
- Default timeout is 300 seconds (5 minutes)
- Modify in code if needed: `timeout=600` parameter

## 💡 Pro Tips

1. **Use Natural Language** - Don't worry about exact PowerShell syntax, the AI figures it out
2. **Chain Operations** - Ask for multiple things in one prompt
3. **Parallel for Speed** - When running multiple independent commands, use `run_parallel_commands()`
4. **Stream for Long Commands** - Keep `stream_output=True` (default) to see progress
5. **Check Examples** - Run `python examples.py` to see all capabilities

## 🎓 Learn More

- Full documentation: See `README.md`
- All examples: Run `python examples.py`
- Source code: `powershell_agent.py`

Enjoy your powerful PowerShell agent! 🚀
