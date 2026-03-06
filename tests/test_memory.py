"""
Unit tests for powershell_agent.memory (session save/load/list)
"""

import json
import pytest
from pathlib import Path
from powershell_agent.memory import Session, save_session, list_sessions, load_session
from powershell_agent.config import HISTORY_DIR


def _make_session(prompt: str = "test prompt") -> Session:
    s = Session(prompt)
    s.record_command("Get-Date", {"status": "success", "output": "Monday", "return_code": 0})
    s.iterations = 2
    s.finish("Done.")
    return s




def test_session_has_unique_ids():
    a = Session("hello")
    b = Session("hello")
    assert a.id != b.id


def test_session_records_command():
    s = Session("p")
    s.record_command("ls", {"status": "success", "output": "file.txt", "return_code": 0})
    assert len(s.commands) == 1
    assert s.commands[0]["command"] == "ls"


def test_session_to_dict_keys():
    s = _make_session()
    d = s.to_dict()
    for key in ("id", "user_prompt", "started_at", "finished_at", "iterations", "commands_run", "commands", "final_response"):
        assert key in d, f"Missing key: {key}"


def test_session_commands_run_count():
    s = _make_session()
    assert s.to_dict()["commands_run"] == 1




def test_save_and_load_session():
    s = _make_session("save and load test")
    path = save_session(s)
    assert path.exists()

    loaded = load_session(s.id)
    assert loaded is not None
    assert loaded["id"] == s.id
    assert loaded["user_prompt"] == "save and load test"
    assert loaded["final_response"] == "Done."

    # cleanup
    path.unlink(missing_ok=True)


def test_list_sessions_returns_list():
    sessions = list_sessions(limit=5)
    assert isinstance(sessions, list)


def test_list_sessions_summary_keys():
    s = _make_session("list test")
    path = save_session(s)
    sessions = list_sessions(limit=5)
    ids = [x["id"] for x in sessions]
    assert s.id in ids
    path.unlink(missing_ok=True)


def test_load_nonexistent_session():
    result = load_session("000000000000")
    assert result is None
