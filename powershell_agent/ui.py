"""
UI utilities for PowerShell Agent CLI.

Simple, clean terminal output with color coding.
Works in PowerShell, CMD, and all terminals.
"""

import sys
from typing import Optional


# Color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
RESET = "\033[0m"


# Wrap stdout for UTF-8 encoding on Windows (skip in pytest)
if sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def header(version: str, model: str, max_iter: int) -> None:
    """Print the main header."""
    print(f"{CYAN}> PowerShell Agent v{version}{RESET}")
    print(f"{GRAY}  Model: {model} | Max iter: {max_iter}{RESET}")
    print(separator())


def prompt(prompt_text: str) -> None:
    """Print user prompt."""
    print(f"{CYAN}> {prompt_text}{RESET}")
    print(separator())


def tool_start(name: str, command: str) -> None:
    """Print tool execution start."""
    print(f"  {CYAN}[tool] {name}{RESET}")
    print(f"  {GRAY}-> Running: {command}{RESET}")


def tool_result(status: str, duration: float = 0) -> None:
    """Print tool result with color."""
    if status == "success":
        print(f"  {GREEN}[+]{RESET} {GRAY}success ({duration:.2f}s){RESET}")
    elif status == "error":
        print(f"  {RED}[x]{RESET} {GRAY}error ({duration:.2f}s){RESET}")
    elif status == "timeout":
        print(f"  {YELLOW}[!]{RESET} {GRAY}timeout ({duration:.2f}s){RESET}")
    else:
        print(f"  [{status}] {GRAY}({duration:.2f}s){RESET}")


def error(message: str, suggestion: Optional[str] = None) -> None:
    """Print error message with optional suggestion."""
    print(f"  {RED}[x] Error: {message}{RESET}")
    if suggestion:
        print(f"    {GRAY}{suggestion}{RESET}")


def success(message: str) -> None:
    """Print success message."""
    print(f"  {GREEN}[+] {message}{RESET}")


def warning(message: str) -> None:
    """Print warning message."""
    print(f"  {YELLOW}[!] {message}{RESET}")


def info(message: str) -> None:
    """Print info message."""
    print(f"  {GRAY}{message}{RESET}")


def iteration(current: int, total: int) -> None:
    """Print iteration progress."""
    print(f"\n{CYAN}[*] Iteration {current}/{total}{RESET}")


def separator(char: str = "─", length: int = 40) -> str:
    """Return a separator line."""
    return f"{GRAY}{char * length}{RESET}"


def print_separator(char: str = "─", length: int = 40) -> None:
    """Print a separator line."""
    print(separator(char, length))


def result(message: str) -> None:
    """Print final result."""
    print_separator()
    print(f"{GREEN}Result:{RESET}")
    print(f"  {message}")
    print_separator()


def review_prompt(command: str, is_destructive: bool = False) -> str:
    """Print review mode prompt and return user choice."""
    if is_destructive:
        print(f"\n  {YELLOW}⚠️  DESTRUCTIVE COMMAND{RESET}")
        print(f"  {GRAY}└─ {command}{RESET}")
        choice = input(f"  {YELLOW}Approve?{RESET} [y]es / [n]o / [e]dit / [q]uit: ").strip().lower()
    else:
        print(f"\n  {CYAN}Command: {command}{RESET}")
        choice = input(f"  {GRAY}Run?{RESET} [y/n/e(dit)/q(uit)]: ").strip().lower()
    return choice


def thinking() -> None:
    """Show thinking indicator."""
    sys.stdout.write(f"  {YELLOW}⚡ Thinking...{RESET}\r")
    sys.stdout.flush()


def clear_thinking() -> None:
    """Clear thinking indicator."""
    sys.stdout.write(" " * 20 + "\r")
    sys.stdout.flush()


def format_table(headers: list, rows: list) -> str:
    """Format data as a simple ASCII table."""
    if not rows:
        return "No data"

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    lines = []

    header_line = "│ " + " │ ".join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    ) + " │"
    lines.append(header_line)

    separator_line = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    lines.append(separator_line)

    for row in rows:
        row_line = "│ " + " │ ".join(
            str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
        ) + " │"
        lines.append(row_line)

    return "\n".join(lines)


def history_table(sessions: list) -> None:
    """Print history as a table."""
    if not sessions:
        info("No sessions found.")
        return

    print(f"\n{GRAY}Sessions (most recent first):{RESET}")
    headers = ["ID", "Started", "Iter", "Cmds", "Prompt"]
    rows = []
    for s in sessions:
        ts = s["started_at"][:19].replace("T", " ")
        rows.append([
            s["id"][:12],
            ts,
            str(s.get("iterations", "?")),
            str(s.get("commands_run", "?")),
            s["prompt_preview"][:40]
        ])
    print(format_table(headers, rows))


def usage() -> None:
    """Print usage information."""
    print(f"""
{CYAN}PowerShell Agent CLI{RESET}
{separator()}
{GRAY}Usage:{RESET} powershell-agent [options] "your prompt"

{CYAN}Options:{RESET}
  --review          Approve each command before running
  --model NAME      Override LLM model
  --iterations N    Max iterations (default: 10)
  --history         Show past sessions
  --clear-history   Delete all saved sessions
  --replay ID       Replay a session
  --github "query"  Query GitHub via MCP
  --version         Show version

{CYAN}Examples:{RESET}
  {GRAY}powershell-agent "find *.py files"{RESET}
  {GRAY}powershell-agent --review "delete old logs"{RESET}
  {GRAY}powershell-agent --history{RESET}

{CYAN}Environment:{RESET}
  GROQ_API_KEY     Your Groq API key
  MODEL_PS         Default model
  PS_TIMEOUT       Command timeout (default: 300s)
""")
