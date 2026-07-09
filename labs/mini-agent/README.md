# mini-agent

Build and explain a minimal Claude Code-style coding agent.

## Current Build

The first working build lives as an independent open-source repository:

- Repository: https://github.com/huanghfzhufeng/mini-claude-code
- Local checkout: `/Users/zeke/agent dome/zhufeng/mini-claude-code`

This lab page is the learning record inside `build-to-understand`. The implementation remains in its own repository to keep it usable as a public teaching project.

## Black Box

How does a terminal coding agent turn a user task into real code changes?

## Smallest Build

A deterministic coding agent that can:

1. inspect a tiny project;
2. find a TODO bug;
3. read the relevant file;
4. apply a patch;
5. inspect the git diff;
6. run tests;
7. write a session trace.

## Core Mechanism

```text
observations
-> planner.next_step()
-> tool call
-> tool runner
-> observation
-> repeat
```

The core is not code generation. The core is feedback: tool results become observations, and observations drive the next action.

## Current Status

- runnable: yes
- verifiable: yes, `python3 -m pytest`
- aligned: partially, mirrors the local loop of Claude Code-style agents
- explainable: initial README exists
- compressed: initial principles recorded below

## Principle Snapshot

1. A coding agent is a loop, not a prompt.
2. Tools turn decisions into effects.
3. Observations turn effects back into context.
4. Trace makes the loop auditable.
5. Verification separates coding agents from code generators.
6. Diff inspection lets the agent see its own edits before testing.
