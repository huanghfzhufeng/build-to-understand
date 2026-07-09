# Explain It Simply

A mini coding agent has three parts:

1. A planner that chooses the next move.
2. Tools that can read files, edit files, inspect diffs, and run commands.
3. A loop that feeds every tool result back into the planner.

The important idea is feedback.

Without feedback, the system only writes code.

With feedback, it can see what happened, adjust, verify, and stop with evidence.
