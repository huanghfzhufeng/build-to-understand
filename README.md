# build-to-understand

Everything I Understand, I Can Build.

This repository is a long-term lab for understanding systems by building their smallest working versions.

It is not a bookmark collection. It is not a course list. It is not a place for passive notes.

An idea enters this repo only when it becomes a concrete build:

```text
black box
-> smallest buildable version
-> working implementation
-> reference alignment
-> failure record
-> compressed principles
-> teachable explanation
```

## Repository Shape

```text
build-to-understand/
  MANIFESTO.md
  ROADMAP.md
  labs/
    mini-agent/
  templates/
    lab-template/
  tools/
```

Labs are intentionally not numbered. The order of learning changes with curiosity and need. The current sequence lives in `ROADMAP.md`, not in directory names.

## What Counts As Done

A lab is not done because I watched a course or read a book.

A lab is done only when it passes five gates:

1. Runnable: one clear command runs the core demo.
2. Verifiable: tests, examples, or reference outputs prove behavior.
3. Aligned: the lab states how it differs from the real system.
4. Explainable: another reader can understand the mechanism.
5. Compressed: the final notes extract transferable principles.

## Current Labs

| Lab | Status | Build |
| --- | --- | --- |
| `mini-agent` | active | Minimal Claude Code-style coding agent |

## Rule

Do not add knowledge here to feel productive.

Add only the part that can be built, checked, debugged, aligned, and taught.
