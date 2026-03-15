"""
Unit tests for powershell_agent.executor
"""

import asyncio
import pytest
from powershell_agent.executor import run_powershell


@pytest.mark.asyncio
async def test_successful_command():
    result = await run_powershell("Write-Output 'hello'", stream_output=False)
    assert result["status"] == "success"
    assert result["return_code"] == 0
    assert "hello" in result["output"]


@pytest.mark.asyncio
async def test_failed_command():
    result = await run_powershell("exit 1", stream_output=False)
    assert result["status"] == "error"
    assert result["return_code"] == 1


@pytest.mark.asyncio
async def test_command_captures_output():
    result = await run_powershell("Write-Output 'test_value'", stream_output=False)
    assert "test_value" in result["output"]


@pytest.mark.asyncio
async def test_get_date_command():
    result = await run_powershell("Get-Date -Format 'yyyy'", stream_output=False)
    assert result["status"] == "success"
    assert "202" in result["output"]   # year starts with 202x


@pytest.mark.asyncio
async def test_error_output_captured():
    result = await run_powershell(
        "Write-Error 'something went wrong'",
        stream_output=False,
    )
    # Write-Error exits 0 but puts text in stderr
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_result_keys():
    result = await run_powershell("Write-Output 'ok'", stream_output=False)
    for key in ("status", "command", "output", "error", "return_code"):
        assert key in result, f"Missing key: {key}"


def test_destructive_tools_defined():
    """Test that destructive tools are properly defined for review enforcement."""
    from powershell_agent.agent import DESTRUCTIVE_TOOLS
    assert "copy_file" in DESTRUCTIVE_TOOLS
    assert "move_file" in DESTRUCTIVE_TOOLS
    assert "delete_item" in DESTRUCTIVE_TOOLS
