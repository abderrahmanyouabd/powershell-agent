"""
Session memory: persist every agent run to disk for later inspection or replay.

Each session is saved as a JSON file under ~/.powershell-agent/history/.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .config import HISTORY_DIR


class Session:
    """Represents one agent run from prompt to final response."""

    def __init__(self, user_prompt: str) -> None:
        self.id: str = uuid4().hex[:12]
        self.user_prompt: str = user_prompt
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.finished_at: Optional[str] = None
        self.commands: List[Dict[str, Any]] = []
        self.iterations: int = 0
        self.final_response: Optional[str] = None
        self._t0: float = time.monotonic()

    def record_command(self, command: str, result: Dict[str, Any]) -> None:
        self.commands.append({
            "command": command,
            "status": result.get("status"),
            "return_code": result.get("return_code"),
            "output_preview": (result.get("output") or "")[:300],
        })

    def finish(self, response: str) -> None:
        self.final_response = response
        self.finished_at = datetime.now(timezone.utc).isoformat()

    def duration_seconds(self) -> float:
        return round(time.monotonic() - self._t0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_prompt": self.user_prompt,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds(),
            "iterations": self.iterations,
            "commands_run": len(self.commands),
            "commands": self.commands,
            "final_response": self.final_response,
        }


def save_session(session: Session) -> Path:
    """Persist a session to disk. Returns the path written."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = HISTORY_DIR / f"{ts}_{session.id}.json"
    path.write_text(json.dumps(session.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most-recent N session summaries."""
    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:limit]
    summaries = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            summaries.append({
                "id": data.get("id"),
                "started_at": data.get("started_at", ""),
                "duration_s": data.get("duration_seconds", "?"),
                "iterations": data.get("iterations", "?"),
                "commands_run": data.get("commands_run", 0),
                "prompt_preview": (data.get("user_prompt") or "")[:80],
            })
        except Exception:
            continue
    return summaries


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Load a full session by its 12-char hex ID."""
    for f in HISTORY_DIR.glob("*.json"):
        if session_id in f.name:
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None


def clear_sessions() -> int:
    """Delete all saved sessions from the history directory. Returns number of files deleted."""
    count = 0
    for f in HISTORY_DIR.glob("*.json"):
        try:
            f.unlink()
            count += 1
        except Exception:
            pass
    return count
