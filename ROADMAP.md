# Roadmap

This file tracks learning order. Directory names stay unordered so the lab can follow real curiosity.

## Active

- `mini-agent`: build and explain a minimal Claude Code-style coding agent.

## Candidate Labs

- `mini-cpu`: instruction execution, registers, memory, simple assembler.
- `mini-shell`: process execution, pipes, redirects, environment.
- `mini-http`: sockets, request parsing, routing, response lifecycle.
- `mini-redis`: in-memory data structures, protocol, persistence basics.
- `mini-sql`: parser, planner, storage, simple indexes.
- `mini-git`: content-addressed storage, commits, trees, refs, diff.
- `mini-container`: namespaces, cgroups, filesystem isolation.
- `mini-k8s`: desired state, scheduler, controller loop.
- `mini-transformer`: attention, embeddings, training loop.
- `mini-gpt`: tokenization, next-token training, sampling.
- `mini-search`: crawling, indexing, ranking, query serving.

## Selection Rule

Pick the next lab by current leverage, not by numeric order.

For each candidate, ask:

1. What is the black box I want to understand?
2. What is the smallest buildable version?
3. What real implementation or source will I align against?
4. What test will prove the mechanism works?
5. What principle should survive after the code is forgotten?
