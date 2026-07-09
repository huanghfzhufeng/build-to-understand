# Operating System

Everything I Understand, I Can Build.

This document defines the source layer of this repository. It is the rule that decides what counts as understanding, what enters a lab, and how each lab should be built.

## Hard Definition

Understanding is not knowing, believing, repeating, bookmarking, or calling a tool.

Understanding means:

1. I can rebuild the mechanism at low complexity.
2. I can recognize the same structure inside a real high-complexity system.
3. I can debug it when it fails.
4. I can align it against a real implementation, paper, spec, dataset, or source.
5. I can abstract it when it transfers to another domain.
6. I can teach it so another person gains a debuggable mental model.

This is the bottom-level calibration for learning, engineering, research, writing, and product judgment in this repository.

## Core Principles

### Buildability

If I cannot build it, I do not fully understand it.

When facing a black box, first build the smallest working version instead of collecting concepts, courses, references, or frameworks.

### Visibility

Complexity must be reduced until causality becomes visible.

A minimal system is not a toy. It is a microscope. It exposes errors, dependencies, data flow, gradient flow, control flow, state, and boundary conditions.

### Alignment

A self-built system must be compared against reality.

Building from scratch is not for self-satisfaction. It is the path into the real system. Each lab needs a reference, baseline, test, reproduction target, official spec, source implementation, or real metric.

### Paradigm Sense

Mechanisms should reveal shifts in how software is made.

Do not only ask, "How do I use this tool?" Also ask:

- What programming model does this change?
- What kind of work does it move from humans to systems?
- What new interface does it create?
- Where does value move?
- What becomes easier, cheaper, or newly possible?

### Teachability

Teaching is part of the understanding loop.

The goal is not to produce impressive opinions. The goal is to give another person a mental model they can use, test, and debug.

## Anti-Patterns

Return to the source layer when any of these appear:

- Treating reading, bookmarking, or retelling as completion.
- Treating API, framework, or agent usage as understanding.
- Discussing grand paradigms before a minimal working mechanism exists.
- Introducing many unverified complexities at once.
- Replacing mechanism, experiment, failure notes, and reproducible evidence with abstractions.
- Chasing new tools without extracting transferable generative principles.

## Training Loop

Every important topic should pass through this loop:

1. See the black box: name the mechanism I do not understand. Do not hide ignorance behind familiar words.
2. Shrink it: reduce the target to a version that can be built in a day or a few days.
3. Build it: create code, experiments, diagrams, traces, or workflows that can be inspected.
4. Align it: compare against papers, source code, official docs, real systems, real data, or user feedback.
5. Explain failure: record where it diverged, why it failed, and which assumption was broken.
6. Compress principles: extract the mechanism, boundary, tradeoff, and transfer rule.
7. Teach it: explain it so another smart person can rebuild the mental model.

## Lab Protocol

Before creating or extending a lab, answer:

1. What is the black box?
2. What is the smallest buildable version?
3. Which reference or real system will anchor it?
4. What unverified complexity is being introduced?
5. How will failures be observed and located?
6. What will count as verification?
7. What principle should remain after the implementation details fade?
8. Can this be explained to another person as a debuggable model?

## Lab Done Gates

A lab is not done because the code runs once.

A lab is done when it has:

1. a runnable demo;
2. a repeatable verification command;
3. reference alignment notes;
4. failure notes;
5. compressed principles;
6. a simple explanation for another learner.

## Rhythm

A sustainable rhythm for this repository:

1. Choose one black box.
2. Build one minimal working version.
3. Align it against one reference.
4. Write one failure record.
5. Compress one principle.
6. Explain it in one page.

The repository should grow through working mechanisms, not through passive accumulation.
