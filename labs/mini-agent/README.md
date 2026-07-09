# mini-agent

A minimal, readable, end-to-end coding agent for learning how Claude Code-style terminal agents work.

This is not a Claude Code clone. It is a small learning project that exposes the core loop:

```text
task
-> gather project context
-> choose a tool
-> run the tool
-> observe the result
-> edit files
-> run verification
-> summarize evidence
```

## Why This Exists

Most people first see coding agents as magic: prompt in, code out.

This lab takes the opposite path. It keeps the system small enough that you can inspect every moving part:

- `agent.py` is the loop.
- `planner.py` chooses the next action.
- `tools.py` reads files, searches text, applies patches, and runs commands.
- `show_diff` lets the agent inspect its own edits before verification.
- `safety.py` blocks a few destructive commands.
- `session.py` writes an append-only JSONL trace.
- `examples/buggy_project` is a tiny project the agent can fix.

The first version uses `ScriptedPlanner`, a deterministic planner, so the whole demo runs without an API key. A real LLM planner can replace it later without changing the tool layer or the agent loop.

## Quick Start

```bash
git clone https://github.com/huanghfzhufeng/build-to-understand.git
cd build-to-understand/labs/mini-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the demo agent against the buggy example:

```bash
cd examples/buggy_project
git init
git add .
git commit -m baseline
python3 -m mini_claude_code.cli "Fix the TODO bug and run tests."
```

The agent will:

1. list files
2. search for `TODO`
3. read `calculator.py`
4. apply a small patch
5. inspect the git diff
6. run the equivalent of `python -m pytest`
7. write a trace to `.mini-claude-code/session.jsonl`

## The Minimal Agent Contract

A coding agent needs five pieces:

| Piece | In this repo | Job |
| --- | --- | --- |
| Context | `list_files`, `read_file`, `grep` | See the real project before editing |
| Tools | `ToolRunner` | Turn model/tool decisions into effects |
| Loop | `CodingAgent.run` | Feed observations back into the next decision |
| Safety | `assert_safe_command` | Block obvious destructive commands |
| Verification | `run_command("{python} -m pytest")` | Check whether the edit worked |

`{python}` is replaced with the current Python executable, so verification uses the same environment that is running the agent.

The key idea is that tool results go back into the loop. Without that feedback, the system is just a code generator. With it, the system can act, observe, and correct.

## Learning Notes

The lab record lives in `notes/`:

- `notes/references.md`: alignment sources and current gaps.
- `notes/failures.md`: wrong assumptions and debugging notes.
- `notes/principles.md`: compressed ideas that should transfer.
- `notes/explain.md`: a plain explanation for teaching.

## Current Limits

This lab is intentionally small:

- no real LLM planner yet
- no streaming UI
- no permission prompts
- no MCP
- no subagents
- no long-term memory

Those are later layers. The first layer is the complete local loop.

## Roadmap

- [ ] Add an OpenAI-compatible planner.
- [ ] Add a Claude/Anthropic planner.
- [ ] Add explicit user approval for patches and commands.
- [ ] Add diff previews before edits.
- [ ] Add project memory loading from `AGENTS.md`.
- [ ] Add trace viewer for session logs.
- [ ] Add tutorial chapters for each layer.

## Learning Rule

Do not treat this repo as a finished tool. Treat it as a microscope.

When adding a feature, ask:

1. What part of a coding agent does this reveal?
2. What is the smallest working version?
3. How do we verify it?
4. Can a reader understand it from the code and trace?
