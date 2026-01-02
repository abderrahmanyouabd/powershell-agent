"""
PowerShell Agentic Tool
A powerful agentic tool for executing PowerShell commands with streaming output and parallel execution support.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from typing import Optional, List, Dict, Any
from groq import Groq


class PowerShellAgent:
    """Agent for executing PowerShell commands with streaming support."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the PowerShell agent with Groq API client."""
        self.client = Groq(api_key=api_key) if api_key else Groq()
        # Get model from environment variable or use default
        self.model = os.getenv("MODEL_PS", "llama-3.3-70b-versatile")
        
    async def run_powershell_command(
        self, 
        command: str, 
        stream_output: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a PowerShell command with optional streaming output.
        
        Args:
            command: The PowerShell command to execute
            stream_output: Whether to stream output in real-time
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary containing status, output, and error information
        """
        print(f"\n🚀 Executing PowerShell command: {command}\n")
        
        try:
            # Create subprocess for PowerShell execution
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=False
            )
            
            output_lines = []
            error_lines = []
            
            async def read_stream(stream, is_error=False):
                """Read from stream and optionally print in real-time."""
                lines = error_lines if is_error else output_lines
                prefix = "❌ " if is_error else "✅ "
                
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    lines.append(decoded)
                    
                    if stream_output and decoded:
                        print(f"{prefix}{decoded}")
            
            # Read both stdout and stderr concurrently
            await asyncio.gather(
                read_stream(process.stdout, is_error=False),
                read_stream(process.stderr, is_error=True)
            )
            
            # Wait for process to complete
            try:
                return_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "status": "timeout",
                    "command": command,
                    "output": "\n".join(output_lines),
                    "error": f"Command timed out after {timeout} seconds",
                    "return_code": -1
                }
            
            result = {
                "status": "success" if return_code == 0 else "error",
                "command": command,
                "output": "\n".join(output_lines),
                "error": "\n".join(error_lines) if error_lines else None,
                "return_code": return_code
            }
            
            print(f"\n{'✅ Command completed successfully' if return_code == 0 else '❌ Command failed with exit code ' + str(return_code)}\n")
            
            return result
            
        except Exception as e:
            return {
                "status": "exception",
                "command": command,
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    async def run_parallel_commands(
        self,
        commands: List[str],
        stream_output: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple PowerShell commands in parallel.
        
        Args:
            commands: List of PowerShell commands to execute
            stream_output: Whether to stream output in real-time
            
        Returns:
            List of result dictionaries for each command
        """
        print(f"\n🔥 Executing {len(commands)} commands in parallel...\n")
        
        tasks = [
            self.run_powershell_command(cmd, stream_output=stream_output)
            for cmd in commands
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    def create_tool_schema(self) -> List[Dict[str, Any]]:
        """Create the tool schema for the run_powershell function."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_powershell",
                    "description": (
                        "Execute any PowerShell command including git commands, grep/Select-String, "
                        "file operations, system commands, or any other PowerShell operations. "
                        "Returns the command output with streaming support. "
                        "Can handle complex commands with pipes, redirections, and multiple statements."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": (
                                    "The PowerShell command to execute. Examples: "
                                    "'git status', 'Get-ChildItem -Recurse', "
                                    "'Select-String -Path *.py -Pattern \"function\"', "
                                    "'Get-Process | Where-Object {$_.CPU -gt 100}'"
                                )
                            },
                            "stream_output": {
                                "type": "boolean",
                                "description": "Whether to stream output in real-time (default: true)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
    
    async def execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call from the LLM with robust error handling."""
        try:
            # Parse function arguments
            function_args = json.loads(tool_call.function.arguments)
            
            # Validate required parameters
            command = function_args.get("command")
            if not command:
                return {
                    "status": "error",
                    "command": "",
                    "output": "",
                    "error": "No command provided by LLM",
                    "return_code": -1
                }
            
            # Ensure command is a string
            if not isinstance(command, str):
                command = str(command)
            
            # Get stream_output with type conversion
            stream_output = function_args.get("stream_output", True)
            
            # Handle string to boolean conversion (LLM sometimes returns "true" instead of true)
            if isinstance(stream_output, str):
                stream_output = stream_output.lower() in ('true', '1', 'yes', 'on')
            elif not isinstance(stream_output, bool):
                # If it's neither string nor bool, default to True
                stream_output = True
            
            # Execute command
            result = await self.run_powershell_command(command, stream_output=stream_output)
            return result
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "command": "",
                "output": "",
                "error": f"Failed to parse tool call arguments: {str(e)}",
                "return_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "command": function_args.get("command", "") if 'function_args' in locals() else "",
                "output": "",
                "error": f"Unexpected error in tool execution: {str(e)}",
                "return_code": -1
            }
    
    async def run_agent(self, user_prompt: str, max_iterations: int = 10) -> str:
        """
        Run the agentic loop with tool calling.
        
        Args:
            user_prompt: The user's request
            max_iterations: Maximum number of agent iterations
            
        Returns:
            Final response from the agent
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a PowerShell command execution assistant. "
                    "You can execute any PowerShell command the user requests including git commands, "
                    "file searches with Select-String (PowerShell's grep), directory listings, "
                    "system operations, and any other PowerShell operations. "
                    "When executing commands, always use the run_powershell tool. "
                    "Provide clear, helpful responses about what you're doing and the results."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        tools = self.create_tool_schema()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n📍 Agent iteration {iteration}/{max_iterations}")
            
            try:
                # Call the LLM
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.3
                )
            except Exception as e:
                error_msg = str(e)
                print(f"\n❌ Error calling LLM API: {error_msg}\n")
                
                # Provide helpful error messages
                if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    return "❌ API Key Error: Please set a valid GROQ_API_KEY environment variable. Get one at: https://console.groq.com/keys"
                elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                    return "❌ Rate Limit Error: You've hit the API rate limit. Please wait a moment and try again."
                elif "timeout" in error_msg.lower():
                    return "❌ Timeout Error: The API request timed out. Please try again."
                else:
                    return f"❌ API Error: {error_msg}"
            
            response_message = response.choices[0].message
            messages.append(response_message)
            
            # Check if we're done
            if not response_message.tool_calls:
                print("\n✅ Agent completed - no more tool calls needed\n")
                return response_message.content
            
            # Execute tool calls
            print(f"\n🔧 Executing {len(response_message.tool_calls)} tool call(s)...")
            
            for tool_call in response_message.tool_calls:
                result = await self.execute_tool_call(tool_call)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(result, indent=2)
                })
        
        return "⚠️ Max iterations reached. The agent may need more steps to complete the task."


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """Main CLI interface for the PowerShell agent."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PowerShell Agentic Tool - Execute PowerShell commands via natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  powershell-agent "Check git status"
  powershell-agent "Find all Python files and count them"
  powershell-agent "Search for TODO comments in all files"
  powershell-agent    # Interactive mode

Environment Variables:
  GROQ_API_KEY    Your Groq API key (required)
  MODEL_PS        LLM model to use (default: llama-3.3-70b-versatile)

For more information, visit: https://github.com/abderrahmanyouabd/powershell-agent
        """
    )
    
    parser.add_argument(
        'prompt',
        nargs='*',
        help='Natural language prompt for what you want to do'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Override MODEL_PS environment variable'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("=" * 80)
    print("🤖 PowerShell Agentic Tool - Streaming Command Execution")
    print("=" * 80)
    
    # Initialize agent
    agent = PowerShellAgent()
    
    # Override model if specified
    if args.model:
        agent.model = args.model
        print(f"\n🎯 Using model: {agent.model}")
    
    # Get user prompt
    if args.prompt:
        # Use command line argument as prompt
        user_prompt = " ".join(args.prompt)
    else:
        # Interactive mode
        print("\nEnter your request (what PowerShell command would you like to run?)")
        print("Examples:")
        print("  - 'Check git status'")
        print("  - 'Find all Python files'")
        print("  - 'Search for the word function in all py files'")
        print("  - 'List all running processes using more than 100MB memory'\n")
        
        user_prompt = input("👤 You: ").strip()
        
        if not user_prompt:
            print("❌ No prompt provided. Exiting.")
            return
    
    print(f"\n📝 User request: {user_prompt}\n")
    print("-" * 80)
    
    # Run the agent
    final_response = await agent.run_agent(user_prompt)
    
    print("\n" + "=" * 80)
    print("🎯 FINAL RESPONSE")
    print("=" * 80)
    print(final_response)
    print("=" * 80 + "\n")


def cli():
    """Entry point for the Poetry script installation."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
