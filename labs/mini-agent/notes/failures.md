# Failures

## 2026-07-09

- `python` was not available on the local machine; changed commands to use `python3`.
- Running tests through a subprocess used the wrong Python environment; introduced `{python}` replacement so command execution uses the current interpreter.
- CLI module did not execute when run with `python -m`; added `if __name__ == "__main__": main()`.
- Session logging failed on nested `Path` values; made JSON conversion recursive.
- `show_diff` returned `no diff` in a fresh git repo because there was no baseline commit; demo instructions and tests now create a baseline commit before running the agent.
