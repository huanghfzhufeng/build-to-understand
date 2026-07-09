import json
from pathlib import Path

from mini_claude_code.session import SessionLog


def test_session_log_serializes_nested_paths(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log = SessionLog(log_path)

    log.write("event", {"root": tmp_path, "items": [tmp_path / "file.txt"]})

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["payload"]["root"] == str(tmp_path)
    assert record["payload"]["items"] == [str(tmp_path / "file.txt")]
