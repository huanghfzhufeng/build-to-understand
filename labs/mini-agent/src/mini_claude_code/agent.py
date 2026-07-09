from __future__ import annotations

from pathlib import Path

from .messages import Observation
from .planner import Planner
from .session import SessionLog
from .tools import ToolRunner


class CodingAgent:
    def __init__(self, root: Path, planner: Planner, max_steps: int = 12) -> None:
        self.root = root
        self.planner = planner
        self.max_steps = max_steps
        self.tools = ToolRunner(root)
        self.log = SessionLog(root / ".mini-claude-code" / "session.jsonl")

    def run(self, task: str) -> list[Observation]:
        observations: list[Observation] = []
        self.log.write("task", {"task": task, "root": self.root})

        for step_no in range(1, self.max_steps + 1):
            step = self.planner.next_step(task, observations)
            self.log.write("agent_step", {"step": step_no, "thought": step.thought, "tool_call": step.tool_call})

            observation = self.tools.run(step.tool_call)
            observations.append(observation)
            self.log.write("observation", observation)

            if step.tool_call.name == "finish":
                break

        return observations
