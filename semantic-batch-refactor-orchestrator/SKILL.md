---
name: semantic-batch-refactor-orchestrator
description: Use when a codebase-wide semantic change is large enough for parallel work but needs strict requirement clarification, conflict-aware task partitioning, and controlled subagent execution
---

# Semantic Batch Refactor Orchestrator

## Overview

Use this skill for large semantic code changes where each edit may be simple, but the overall task is risky because the rules are unclear, the search surface is wide, and parallel agents could diverge or collide. The primary agent must freeze the rules before broad implementation begins.

## When to Use

Use when:

- a logging, analytics, API, or call-pattern migration spans many files
- the user request is directionally clear but underspecified
- the new behavior cannot be inferred safely from project search alone
- parallel subagents would help with scale, but shared files or fuzzy rules could cause inconsistent edits

Do not use when:

- the change is a pure text replacement or safe scripted rename
- the task is small enough to complete directly
- the desired target behavior is still fundamentally unknown

## Hard Rules

- Violating the letter of these rules is violating the spirit of these rules.
- If the primary agent cannot state the new rule, the exceptions, and the acceptance criteria, it must not split the work.
- Exploration subagents are strictly read-only.
- Implementation subagents must not invent new mappings, event schemas, or exception logic.
- If two task packets may touch the same file, the partition is invalid.
- Shared definition files should stay with the primary agent unless ownership is explicitly isolated.
- Broad execution requires an explicit user approval checkpoint.
- Parallel exploration may begin early; parallel modification may not.

## Workflow

1. **Classify the task**
   Confirm this is a semantic batch refactor rather than a mechanical rename.

2. **Clarify the requirements**
   Converge these categories before delegation:
   - target outcome
   - scope
   - exclusions
   - old vs new rules
   - edge cases
   - shared definitions
   - acceptance criteria
   - autonomous decision boundaries
   - unresolved questions

3. **Write a rules specification**
   Turn the clarified requirements into an execution spec. This is not a summary. It must be detailed enough that multiple agents will make the same decision on the same input.

4. **Choose an exploration strategy**
   The primary agent may explore critical files directly. If the search surface is too large, dispatch read-only exploration subagents to gather patterns, candidate files, and likely contention points.

5. **Run trial calibration**
   First reason through representative examples. Then make a small real sample edit set that covers multiple common patterns. Use the results to expose missing rules, hidden exceptions, and contested files.

6. **Assess conflicts and select execution mode**
   Use single-round parallel execution only when the rules are stable and ownership is clear. Otherwise use two rounds:
   - round 1: read-only exploration
   - middle: primary-agent consolidation and shared-file handling
   - round 2: implementation on non-overlapping file sets

7. **Partition by ownership**
   Split by explicit file ownership first. Directory or module boundaries are acceptable only when they resolve cleanly into non-overlapping file sets.

8. **Ask the user to approve the plan**
   Present the frozen rule summary, execution mode, primary-agent responsibilities, subagent responsibilities, and known risks. Do not start broad implementation before approval.

9. **Execute and consolidate**
   Dispatch task packets, collect results, and validate the aggregate outcome against the spec before declaring success.

## Clarification Checklist

The primary agent must gather all of the following:

1. **Goal definition**
   What should the final code look like and why is the change being made?

2. **Scope and exclusions**
   Which modules, directories, code paths, test areas, generated files, and legacy areas are in or out?

3. **Rule definition**
   What exactly changes? Capture function signatures, event shapes, field mappings, defaults, return-value differences, and required helper usage.

4. **Exceptions**
   Which cases look similar but must not be changed? Which special environments or compatibility layers behave differently?

5. **Shared definitions**
   Which event/type/helper/config/export files may become contention points?

6. **Acceptance criteria**
   How will correctness be judged? Examples: all old calls removed, new format used everywhere, build passes, targeted tests pass, key paths manually spot-checked.

7. **Decision boundaries**
   Which gaps may the primary agent resolve from project context, and which gaps must go back to the user?

8. **Open questions**
   List unresolved items explicitly. If any unresolved item affects the core mapping logic, stop before splitting.

## Exploration Modes

### Primary-agent exploration

Use for:

- key shared files
- rule-defining utilities
- representative sample edits
- final consolidation decisions

### Exploration subagents

Use for:

- wide codebase search
- pattern clustering
- candidate file lists
- contention discovery
- exception discovery

Exploration subagent constraints:

- read-only
- no edits
- no rule invention
- no scope expansion without reporting it

## Trial Calibration

Run calibration when:

- the target format is new
- project references are sparse or inconsistent
- the search space is large
- the primary agent suspects hidden exceptions

Calibration requirements:

- include read-based reasoning and actual sample edits
- use a small representative file set
- cover multiple common patterns, not just the easiest case
- record newly discovered rules, ambiguities, and contention files

If calibration exposes a core misunderstanding, return to clarification before partitioning.

## Execution Mode Selection

Use **single-round** execution only when:

- rules are stable
- project patterns are reliable
- shared-file risk is low
- sample calibration did not expose major ambiguity
- files can be partitioned cleanly

Use **two-round** execution when:

- the codebase is large and poorly mapped
- shared definitions are numerous
- edge cases are common
- partition boundaries are unclear
- calibration exposed unresolved coordination work

Two-round structure:

1. exploration round
2. primary-agent consolidation and shared-file handling
3. implementation round

## Partitioning Rules

Preferred split order:

1. explicit file lists
2. directory or module ownership with explicit file expansion
3. caller group ownership
4. staged ownership, where shared definitions are handled before downstream call sites

Avoid:

- vague responsibility-only splits
- multiple task packets that could edit the same file
- shared definition edits spread across several implementation agents
- action-based splits that overlap file ownership

Default shared files for the primary agent:

- event definitions
- shared constants
- shared types
- common helper wrappers
- central exports
- global config and adapter layers

## Required Templates

### Rules Specification Template

```md
## Rules Specification
- Goal:
- Background:
- In scope:
- Out of scope:
- Old rule:
- New rule:
- Mapping details:
- Exceptions:
- Shared files:
- Acceptance criteria:
- Agent decision boundary:
- Open questions:
- Sample reference:
```

### Exploration Task Template

```md
## Exploration Task
- Objective:
- Search area:
- Questions to answer:
- Patterns to classify:
- Shared-file types to identify:
- Output required:
- Constraints: read-only, no edits, no rule invention
```

### Trial Calibration Template

```md
## Trial Calibration
- Sample selection rule:
- Sample files:
- Covered patterns:
- Planned edits:
- Actual outcomes:
- New rules found:
- New ambiguities found:
- Contention files found:
- Ready for broad execution?:
```

### Implementation Task Template

```md
## Implementation Task
- Objective:
- Rules specification reference:
- Allowed files:
- Forbidden files:
- May expand to new files?:
- Shared-file handling rule:
- What to do if the spec does not cover a case:
- Required output:
- Self-check:
- Constraints:
  - Do not invent rules.
  - Do not edit files outside the assignment.
  - Stop and report if ownership overlaps or the mapping is unclear.
```

### User Approval Template

```md
## Execution Checkpoint
- Goal as understood:
- Frozen rule summary:
- Execution mode:
- Primary-agent responsibilities:
- Subagent responsibilities:
- Known risks:
- Unresolved items:
- Request: approve or adjust before broad execution
```

## Failure Recovery

- If the core semantics are unresolved, return to clarification.
- If ownership boundaries are unsafe, redesign the split or switch to two rounds.
- If shared files dominate the work, have the primary agent consolidate them first.
- If implementation outputs diverge, pause the rollout, update the rules spec, and resume only after reconvergence.

## Rationalization Traps

Stop if the primary agent starts thinking any of these:

| Rationalization | Required response |
| --- | --- |
| "The user probably means the obvious migration." | Clarify the missing rule details before splitting. |
| "We can let the subagents figure out the edge cases." | Freeze the rules first or send read-only exploration only. |
| "The overlap is small, they can coordinate informally." | Redesign ownership so files do not overlap. |
| "I will do one quick implementation round and clean it up later." | Run calibration or two-round execution instead. |
| "This shared file is tiny, anyone can edit it." | Keep it with the primary agent unless ownership is explicitly isolated. |
| "The user already asked for the change, so approval is implied." | Present the execution checkpoint before broad implementation. |
| "Project patterns are consistent enough; we can skip samples." | Skip calibration only if the primary agent can explain why the risk is truly low. |
