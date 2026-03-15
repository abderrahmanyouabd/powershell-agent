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
    assert "read_file" in names
    assert "edit_file" in names
    assert "list_files" in names
    assert "copy_file" in names
    assert "move_file" in names
    assert "delete_item" in names
    assert "search_content" in names
    assert len(schemas) == 9


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


@pytest.mark.asyncio
async def test_read_file_basic(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n", encoding="utf-8")
    
    result = await reg.call("read_file", {"path": str(test_file)})
    assert result["status"] == "success"
    assert result["total_lines"] == 3
    assert 1 in result["lines"]
    assert result["lines"][1] == "line1"


@pytest.mark.asyncio
async def test_read_file_line_range(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")
    
    result = await reg.call("read_file", {"path": str(test_file), "start_line": 2, "end_line": 4})
    assert result["status"] == "success"
    assert result["total_lines"] == 5
    assert 2 in result["lines"]
    assert 4 in result["lines"]
    assert result["lines"][2] == "line2"
    assert result["lines"][4] == "line4"


@pytest.mark.asyncio
async def test_read_file_not_found(tmp_path):
    reg = build_default_registry()
    result = await reg.call("read_file", {"path": str(tmp_path / "nonexistent.txt")})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_edit_file_replace_text(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world\nfoo bar\n", encoding="utf-8")
    
    result = await reg.call("edit_file", {
        "path": str(test_file),
        "operation": "replace_text",
        "search_text": "world",
        "replace_text": "universe",
    })
    assert result["status"] == "success"
    assert result["replacements_made"] == 1
    assert ".bak" in result["backup_created"]
    content = test_file.read_text(encoding="utf-8")
    assert "hello universe" in content
    assert "world" not in content


@pytest.mark.asyncio
async def test_edit_file_insert(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline3\n", encoding="utf-8")
    
    result = await reg.call("edit_file", {
        "path": str(test_file),
        "operation": "insert",
        "start_line": 1,
        "new_content": "line2",
    })
    assert result["status"] == "success"
    content = test_file.read_text(encoding="utf-8")
    assert "line1" in content
    assert "line2" in content
    assert "line3" in content


@pytest.mark.asyncio
async def test_edit_file_replace(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nold_content\nline3\n", encoding="utf-8")
    
    result = await reg.call("edit_file", {
        "path": str(test_file),
        "operation": "replace",
        "start_line": 2,
        "end_line": 2,
        "new_content": "new_content",
    })
    assert result["status"] == "success"
    content = test_file.read_text(encoding="utf-8")
    assert "old_content" not in content
    assert "new_content" in content


@pytest.mark.asyncio
async def test_edit_file_delete(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n", encoding="utf-8")
    
    result = await reg.call("edit_file", {
        "path": str(test_file),
        "operation": "delete",
        "start_line": 2,
        "end_line": 2,
    })
    assert result["status"] == "success"
    content = test_file.read_text(encoding="utf-8")
    assert "line2" not in content
    assert "line1" in content
    assert "line3" in content


@pytest.mark.asyncio
async def test_edit_file_creates_backup(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "test.txt"
    test_file.write_text("original content", encoding="utf-8")
    
    await reg.call("edit_file", {
        "path": str(test_file),
        "operation": "replace_text",
        "search_text": "original",
        "replace_text": "modified",
    })
    
    backup_file = tmp_path / "test.txt.bak"
    assert backup_file.exists()
    assert backup_file.read_text(encoding="utf-8") == "original content"


@pytest.mark.asyncio
async def test_list_files_basic(tmp_path):
    reg = build_default_registry()
    (tmp_path / "file1.txt").write_text("content")
    (tmp_path / "file2.ps1").write_text("content")
    (tmp_path / "subdir").mkdir()
    
    result = await reg.call("list_files", {"path": str(tmp_path)})
    assert result["status"] == "success"
    assert result["total"] >= 3


@pytest.mark.asyncio
async def test_list_files_pattern(tmp_path):
    reg = build_default_registry()
    (tmp_path / "file.txt").write_text("content")
    (tmp_path / "file.ps1").write_text("content")
    (tmp_path / "file.md").write_text("content")
    
    result = await reg.call("list_files", {"path": str(tmp_path), "pattern": "*.txt"})
    assert result["status"] == "success"
    file_names = [f["name"] for f in result["files"]]
    assert "file.txt" in file_names
    assert "file.ps1" not in file_names


@pytest.mark.asyncio
async def test_search_content_basic(tmp_path):
    reg = build_default_registry()
    test_file1 = tmp_path / "file1.txt"
    test_file1.write_text("hello world\nfoo bar\n", encoding="utf-8")
    test_file2 = tmp_path / "file2.txt"
    test_file2.write_text("hello there\n", encoding="utf-8")
    
    result = await reg.call("search_content", {
        "path": str(tmp_path),
        "pattern": "hello",
        "file_pattern": "*.txt",
    })
    assert result["status"] == "success"
    assert result["total_matches"] >= 2


@pytest.mark.asyncio
async def test_search_content_no_matches(tmp_path):
    reg = build_default_registry()
    test_file = tmp_path / "file.txt"
    test_file.write_text("foo bar\n", encoding="utf-8")
    
    result = await reg.call("search_content", {
        "path": str(tmp_path),
        "pattern": "nonexistent",
        "file_pattern": "*.txt",
    })
    assert result["status"] == "success"
    assert result["total_matches"] == 0
