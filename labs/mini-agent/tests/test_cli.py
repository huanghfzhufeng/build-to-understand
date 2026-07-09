import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_module_runs_demo(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "examples" / "buggy_project"
    src_path = Path(__file__).parents[1] / "src"
    project = tmp_path / "buggy_project"
    shutil.copytree(source, project)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=project, check=True, capture_output=True)

    proc = subprocess.run(
        [sys.executable, "-m", "mini_claude_code.cli", "Fix the TODO bug and run tests."],
        cwd=project,
        env={"PYTHONPATH": str(src_path)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert "[ok] finish" in proc.stdout
    assert "[ok] show_diff" in proc.stdout
    assert "-    return a - b" in proc.stdout
    assert "return a + b" in (project / "calculator.py").read_text(encoding="utf-8")
