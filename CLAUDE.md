# build-to-understand — working agreement

This repo exists to **understand systems by rebuilding their mechanisms** (a
Karpathy-style "build to understand"). Reading, quoting, or being able to call a
tool is NOT understanding. Understanding means: rebuild the mechanism at small
scale, identify the structure at large scale, debug it when it breaks, abstract
the pattern when it transfers, and teach it so someone else gets the mental model.

## How to work with me here

- Push me from **consuming / opining / tool-calling** back toward the loop:
  **smallest buildable thing → align with the real system → explain the failure
  → compress to a principle → teach it clearly.** Prefer producing something
  **runnable, verifiable, and re-explainable** over prose.
- When I ask "what's next", answer with the next mechanism to make concrete, not
  a reading list.
- Respond in **Chinese** (I write in Chinese). Keep code comments in English to
  match the existing labs.

## Lab conventions (match existing labs exactly)

Each topic lives in `labs/<topic>/` — **directories are NOT numbered**; learning
order is tracked in `ROADMAP.md`. A lab has:

```
labs/<topic>/
  src/<pkg>/__init__.py + modules   # src-layout, snake_case package
  tests/test_*.py                   # pytest; each test pins ONE mechanism property
  notes/explain.md                  # explain it simply
  notes/principles.md               # the idea that survives after the code is forgotten
  notes/failures.md                 # what broke and the lesson (read the actual error)
  notes/references.md               # primary sources + how the toy is simplified vs real
  pyproject.toml                    # hatchling; see below
  README.md                         # from templates/lab-template: Black Box / Smallest
                                    # Build / Reference Alignment / Run / Verify / Done Gates
```

`pyproject.toml` uses hatchling, `requires-python >=3.11`, `dev = ["pytest>=8.0"]`,
and crucially:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

## Run & verify

```bash
cd labs/<topic>
PYTHONPATH=src python3 -m pytest        # verify
PYTHONPATH=src python3 -m <pkg>.demo    # run the narrated demo
```

- Tests must actually pass before a lab is called done. Report failures with the
  real output; never claim green without running.
- **Done Gates** (in each README) must all be checked: Runnable, Verifiable,
  Aligned, Explainable, Compressed.

## Tooling notes for this machine

- No system `black`/`ruff`/`pip install` (macOS PEP 668). Use **`uvx ruff format`**
  / `uvx ruff check` to format/lint ephemerally. `uv` is installed.
- A PostToolUse hook auto-formats `.py` files with `uvx ruff format` on save.

## Git

- Commit/push only when I ask. One focused commit per lab or step; subject like
  `labs: add mini-<topic> (...)`. Don't sweep unrelated changes into it.

## Standing constraint

Do **not** probe the data endpoints of my live TikTok analyzer server
(`104.131.123.99:8001`). Identify what it is and reason about it; never enumerate
its data.
