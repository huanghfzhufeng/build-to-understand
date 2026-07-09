from __future__ import annotations

import argparse
from pathlib import Path

from .agent import CodingAgent
from .planner import ScriptedPlanner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny Claude Code-style coding agent.")
    parser.add_argument("task", help="The coding task for the agent.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--max-steps", type=int, default=12)
    args = parser.parse_args()

    agent = CodingAgent(Path(args.root), planner=ScriptedPlanner(), max_steps=args.max_steps)
    observations = agent.run(args.task)

    for obs in observations:
        status = "ok" if obs.ok else "error"
        print(f"\n[{status}] {obs.tool}")
        print(obs.output)


if __name__ == "__main__":
    main()
