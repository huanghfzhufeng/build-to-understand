from __future__ import annotations

from abc import ABC, abstractmethod

from .messages import AgentStep, Observation, ToolCall


class Planner(ABC):
    @abstractmethod
    def next_step(self, task: str, observations: list[Observation]) -> AgentStep:
        raise NotImplementedError


class ScriptedPlanner(Planner):
    """A deterministic planner that demonstrates the agent loop without an API key.

    It fixes the example project by discovering the TODO, reading the file,
    applying a patch, and running the tests. A real model-backed planner can
    replace this class without changing the tool runner or agent loop.
    """

    def next_step(self, task: str, observations: list[Observation]) -> AgentStep:
        successful_tools = [obs.tool for obs in observations if obs.ok]

        if not observations:
            return AgentStep("Start by seeing the workspace shape.", ToolCall("list_files", {}))

        if "grep" not in successful_tools:
            return AgentStep("Find the explicit bug marker.", ToolCall("grep", {"pattern": "TODO"}))

        if "read_file" not in successful_tools:
            return AgentStep("Read the buggy file before editing.", ToolCall("read_file", {"path": "calculator.py"}))

        if "apply_patch" not in successful_tools:
            patch = """diff --git a/calculator.py b/calculator.py
index 8b4a1c1..8c0f5a6 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,5 @@
 def add(a: int, b: int) -> int:
-    # TODO: fix this bug
-    return a - b
+    return a + b
 
 
 def multiply(a: int, b: int) -> int:
"""
            return AgentStep("Apply the smallest patch that fixes the behavior.", ToolCall("apply_patch", {"patch": patch}))

        if "show_diff" not in successful_tools:
            return AgentStep("Inspect the code change before running tests.", ToolCall("show_diff", {}))

        if "run_command" not in successful_tools:
            return AgentStep("Verify with the project test suite.", ToolCall("run_command", {"command": "{python} -m pytest"}))

        return AgentStep(
            "The tests passed, so finish with the evidence.",
            ToolCall("finish", {"summary": "Fixed calculator.add and verified with the project test suite."}),
        )
