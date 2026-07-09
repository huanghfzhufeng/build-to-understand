# References

## Primary Sources

- Claude Code docs: https://code.claude.com/docs
- Claude Code SDK docs: https://code.claude.com/docs/en/agent-sdk/overview
- Current build: https://github.com/huanghfzhufeng/mini-claude-code

## Alignment Notes

The current build aligns with the local agent loop:

```text
gather context -> act with tools -> observe result -> verify
```

It does not yet include:

- model-backed planning;
- permission prompts;
- long-term memory;
- MCP;
- hooks;
- subagents;
- streaming UI.
