"""
Example Usage of PowerShell Agentic Tool
Demonstrates various capabilities including streaming, parallel execution, and agentic loops.
"""

import asyncio
from powershell_agent import PowerShellAgent


async def example_1_basic_command():
    """Example 1: Execute a simple command with streaming."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Command Execution with Streaming")
    print("="*80)
    
    agent = PowerShellAgent()
    result = await agent.run_powershell_command("Get-Date")
    
    print(f"\nResult: {result}")


async def example_2_git_commands():
    """Example 2: Execute git commands."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Git Commands")
    print("="*80)
    
    agent = PowerShellAgent()
    
    # Check git status
    result = await agent.run_powershell_command("git status")
    
    # Get recent commits
    result2 = await agent.run_powershell_command("git log -n 5 --oneline")


async def example_3_file_searching():
    """Example 3: Search for patterns in files (grep equivalent)."""
    print("\n" + "="*80)
    print("EXAMPLE 3: File Searching with Select-String")
    print("="*80)
    
    agent = PowerShellAgent()
    
    # Search for 'import' in Python files
    command = "Select-String -Path *.py -Pattern 'import' | Select-Object -First 10"
    result = await agent.run_powershell_command(command)


async def example_4_parallel_execution():
    """Example 4: Execute multiple commands in parallel."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Parallel Command Execution")
    print("="*80)
    
    agent = PowerShellAgent()
    
    commands = [
        "Get-ChildItem -Filter *.py",
        "Get-ChildItem -Filter *.md",
        "Get-Process | Select-Object -First 5",
        "Get-Date"
    ]
    
    results = await agent.run_parallel_commands(commands)
    
    print(f"\n✅ Executed {len(results)} commands in parallel!")
    for i, result in enumerate(results, 1):
        print(f"\nCommand {i}: {result['command']}")
        print(f"Status: {result['status']}")


async def example_5_agentic_loop():
    """Example 5: Use the full agentic loop."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Agentic Loop - Natural Language Commands")
    print("="*80)
    
    agent = PowerShellAgent()
    
    # The agent will autonomously decide which commands to run
    prompts = [
        "Check the git status of this repository",
        "Find all Python files in the current directory",
        "Search for the word 'agent' in all .py files"
    ]
    
    for prompt in prompts:
        print(f"\n{'─'*80}")
        print(f"Prompt: {prompt}")
        print('─'*80)
        
        response = await agent.run_agent(prompt)
        print(f"\nAgent Response:\n{response}")


async def example_6_complex_operations():
    """Example 6: Complex multi-step operations."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Complex Multi-Step Operations")
    print("="*80)
    
    agent = PowerShellAgent()
    
    # The agent will break this down into multiple commands automatically
    prompt = """
    Do the following:
    1. List all Python files in the current directory
    2. Count how many there are
    3. Show me the first 5 lines of each Python file
    """
    
    response = await agent.run_agent(prompt)
    print(f"\nAgent Response:\n{response}")


async def example_7_system_operations():
    """Example 7: System information and monitoring."""
    print("\n" + "="*80)
    print("EXAMPLE 7: System Operations")
    print("="*80)
    
    agent = PowerShellAgent()
    
    commands = [
        "Get-ComputerInfo | Select-Object CsName, OsArchitecture, WindowsVersion",
        "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU, WorkingSet",
        "Get-PSDrive | Where-Object {$_.Provider -like '*FileSystem*'} | Select-Object Name, Used, Free"
    ]
    
    results = await agent.run_parallel_commands(commands)


async def example_8_custom_no_streaming():
    """Example 8: Execute command without streaming output."""
    print("\n" + "="*80)
    print("EXAMPLE 8: Command Without Streaming")
    print("="*80)
    
    agent = PowerShellAgent()
    
    # Execute without streaming (collect all output at once)
    result = await agent.run_powershell_command(
        "Get-Process | Measure-Object",
        stream_output=False
    )
    
    print(f"\nFull result:\n{result}")


async def run_all_examples():
    """Run all examples sequentially."""
    examples = [
        example_1_basic_command,
        example_2_git_commands,
        example_3_file_searching,
        example_4_parallel_execution,
        example_5_agentic_loop,
        example_6_complex_operations,
        example_7_system_operations,
        example_8_custom_no_streaming
    ]
    
    for example in examples:
        await example()
        await asyncio.sleep(1)  # Small delay between examples


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                  PowerShell Agentic Tool - Examples                        ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nRunning all examples...")
    print("Note: Some examples require a git repository and Groq API key\n")
    
    asyncio.run(run_all_examples())
    
    print("\n✅ All examples completed!")
