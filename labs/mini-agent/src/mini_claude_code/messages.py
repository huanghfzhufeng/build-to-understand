from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ToolName = Literal["list_files", "read_file", "grep", "apply_patch", "show_diff", "run_command", "finish"]


@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    args: dict[str, str]


@dataclass(frozen=True)
class Observation:
    tool: str
    ok: bool
    output: str


@dataclass(frozen=True)
class AgentStep:
    thought: str
    tool_call: ToolCall
