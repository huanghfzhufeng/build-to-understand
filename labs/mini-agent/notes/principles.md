# Principles

## Coding Agent

A coding agent is not a smarter code generator.

It is a control loop around tools:

```text
observe -> decide -> act -> observe -> verify
```

The model or planner does not directly change the world. It emits a tool call. The tool runner changes the world. The result returns as an observation.

## Trace

If an agent cannot show what it did, it cannot be trusted.

Every step should leave an audit trail:

- task;
- decision;
- tool call;
- observation;
- verification result.

## Verification

The agent should not claim success because the patch looks plausible.

It should run the smallest relevant check and report the evidence.
