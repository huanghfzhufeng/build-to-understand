import shutil
import subprocess
from pathlib import Path

from mini_claude_code.agent import CodingAgent
from mini_claude_code.planner import ScriptedPlanner


def test_scripted_agent_fixes_buggy_project(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "examples" / "buggy_project"
    project = tmp_path / "buggy_project"
    shutil.copytree(source, project)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=project, check=True, capture_output=True)

    agent = CodingAgent(project, planner=ScriptedPlanner())
    observations = agent.run("Fix the TODO bug and run tests.")

    assert observations[-1].tool == "finish"
    assert observations[-1].ok
    assert any(obs.tool == "show_diff" and "-    return a - b" in obs.output for obs in observations)
    assert "return a + b" in (project / "calculator.py").read_text(encoding="utf-8")
    assert (project / ".mini-claude-code" / "session.jsonl").exists()
