from pathlib import Path

from mini_claude_code.messages import ToolCall
from mini_claude_code.tools import ToolRunner


def test_read_file_stays_inside_workspace(tmp_path: Path) -> None:
    runner = ToolRunner(tmp_path)
    obs = runner.run(ToolCall("read_file", {"path": "../outside.txt"}))

    assert not obs.ok
    assert "escapes workspace" in obs.output


def test_grep_finds_text(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello agent\n", encoding="utf-8")
    runner = ToolRunner(tmp_path)

    obs = runner.run(ToolCall("grep", {"pattern": "agent"}))

    assert obs.ok
    assert "note.txt:1: hello agent" in obs.output


def test_show_diff_returns_git_diff(tmp_path: Path) -> None:
    runner = ToolRunner(tmp_path)
    runner.run(ToolCall("run_command", {"command": "git init"}))
    (tmp_path / "note.txt").write_text("before\n", encoding="utf-8")
    runner.run(ToolCall("run_command", {"command": "git add note.txt"}))
    runner.run(ToolCall("run_command", {"command": "git commit -m initial"}))
    (tmp_path / "note.txt").write_text("after\n", encoding="utf-8")

    obs = runner.run(ToolCall("show_diff", {}))

    assert obs.ok
    assert "-before" in obs.output
    assert "+after" in obs.output
