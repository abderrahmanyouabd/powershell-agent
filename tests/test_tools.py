"""
Unit tests for powershell_agent.tools (ToolRegistry + built-in tools)
"""

import asyncio
import pytest
from powershell_agent.tools import ToolRegistry, build_default_registry




def test_default_registry_has_two_tools():
    reg = build_default_registry()
    schemas = reg.schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "run_powershell" in names
    assert "write_file" in names
    assert len(schemas) == 2


def test_registry_schema_structure():
    reg = build_default_registry()
    for schema in reg.schemas():
        assert schema["type"] == "function"
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]


def test_can_register_custom_tool():
    reg = ToolRegistry()
    custom_schema = {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "test",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
    async def my_handler(**kwargs):
        return {"status": "success", "output": "hi", "error": None, "return_code": 0}

    reg.register(custom_schema, my_handler)
    assert len(reg.schemas()) == 1
    assert reg.schemas()[0]["function"]["name"] == "my_tool"




@pytest.mark.asyncio
async def test_write_file_creates_file(tmp_path):
    reg = build_default_registry()
    target = str(tmp_path / "out.txt")
    result = await reg.call("write_file", {"path": target, "content": "hello world"})
    assert result["status"] == "success"
    with open(target) as f:
        assert f.read() == "hello world"


@pytest.mark.asyncio
async def test_write_file_append(tmp_path):
    reg = build_default_registry()
    target = str(tmp_path / "append.txt")
    await reg.call("write_file", {"path": target, "content": "line1\n"})
    await reg.call("write_file", {"path": target, "content": "line2\n", "append": True})
    with open(target) as f:
        content = f.read()
    assert "line1" in content and "line2" in content




@pytest.mark.asyncio
async def test_unknown_tool_returns_error():
    reg = build_default_registry()
    result = await reg.call("does_not_exist", {})
    assert result["status"] == "error"
    assert "Unknown tool" in result["error"]
