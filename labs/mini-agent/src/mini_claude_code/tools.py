from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

from .messages import Observation, ToolCall
from .safety import SafetyError, assert_safe_command


class ToolRunner:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def run(self, call: ToolCall) -> Observation:
        try:
            if call.name == "list_files":
                return self._ok(call.name, self.list_files())
            if call.name == "read_file":
                return self._ok(call.name, self.read_file(call.args["path"]))
            if call.name == "grep":
                return self._ok(call.name, self.grep(call.args["pattern"]))
            if call.name == "apply_patch":
                return self._ok(call.name, self.apply_patch(call.args["patch"]))
            if call.name == "show_diff":
                return self._ok(call.name, self.show_diff())
            if call.name == "run_command":
                return self._ok(call.name, self.run_command(call.args["command"]))
            if call.name == "finish":
                return self._ok(call.name, call.args.get("summary", "done"))
        except Exception as exc:
            return Observation(call.name, False, f"{type(exc).__name__}: {exc}")
        return Observation(call.name, False, f"unknown tool: {call.name}")

    def list_files(self) -> str:
        paths = []
        for path in sorted(self.root.rglob("*")):
            if path.is_dir() or self._is_ignored(path):
                continue
            paths.append(str(path.relative_to(self.root)))
        return "\n".join(paths)

    def read_file(self, relative_path: str) -> str:
        path = self._resolve(relative_path)
        return path.read_text(encoding="utf-8")

    def grep(self, pattern: str) -> str:
        matches: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if path.is_dir() or self._is_ignored(path):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if pattern in line:
                    matches.append(f"{path.relative_to(self.root)}:{line_no}: {line}")
        return "\n".join(matches)

    def apply_patch(self, patch: str) -> str:
        proc = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            input=patch,
            text=True,
            cwd=self.root,
            capture_output=True,
            timeout=10,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        return "patch applied"

    def show_diff(self) -> str:
        proc = subprocess.run(
            ["git", "diff", "--"],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=10,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        return proc.stdout.strip() or "no diff"

    def run_command(self, command: str) -> str:
        command = command.replace("{python}", sys.executable)
        try:
            assert_safe_command(command)
        except SafetyError:
            raise

        proc = subprocess.run(
            command,
            shell=True,
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=20,
        )
        output = (proc.stdout + proc.stderr).strip()
        if proc.returncode != 0:
            raise RuntimeError(output or f"command failed with exit code {proc.returncode}")
        return output or "command succeeded"

    def _resolve(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"path escapes workspace: {relative_path}")
        if self._is_ignored(path):
            raise ValueError(f"path is ignored: {relative_path}")
        return path

    def _is_ignored(self, path: Path) -> bool:
        rel = str(path.relative_to(self.root))
        patterns = [
            ".git/*",
            ".mini-claude-code/*",
            "__pycache__/*",
            "*.pyc",
            ".pytest_cache/*",
        ]
        return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)

    def _ok(self, tool: str, output: str) -> Observation:
        return Observation(tool=tool, ok=True, output=output)
