# Semantic Batch Refactor Orchestrator Design

**Date:** 2026-03-18

**Goal:** Define a reusable skill for large-scale semantic code changes where the work is usually easy per file, but overall success depends on precise requirement gathering, stable execution rules, safe task partitioning, and disciplined multi-subagent orchestration.

## Problem

Large codebase-wide tasks such as logging migrations, analytics/event rewrites, API call replacement, or signature updates are often suitable for parallel execution. The main failure mode is not implementation difficulty; it is ambiguity.

Common risks:

- The user describes the desired change loosely, leaving hidden rules undefined.
- The primary agent begins delegating before it fully understands the task.
- Different subagents infer different rules and produce inconsistent edits.
- Shared files, central definitions, and generated boundaries create file ownership conflicts.
- Parallel agents overwrite or duplicate each other's work because the split was based on vague scope rather than explicit file boundaries.

The skill must force the primary agent to turn a fuzzy request into a spec-driven execution package before any broad modification begins.

## Scope

This skill targets semantic batch refactors:

- Function/API replacement with non-trivial mapping rules
- Logging or analytics migration with new event shapes or helper functions
- Event definition and call-site rewrites
- Contract or configuration call pattern migration
- Any large code change where project search alone is insufficient to infer the new rules

It does not target:

- Pure text replacement that can be safely scripted
- Small isolated edits
- Exploratory open-ended refactors without a concrete desired outcome

## Core Positioning

The skill is a specification-first orchestration skill with lightweight execution guidance.

When repository understanding is still too shallow to freeze rules safely, the orchestrator should rely on `context-pack` as a formal upstream research layer. That skill produces a `Research Report` and `Context Pack` that help the orchestrator identify real rule sources, ownership risks, and task-local context boundaries before broad execution.

It is responsible for:

- Forcing detailed requirement clarification
- Deciding when formal repository research must happen before rule-freezing
- Producing a rules specification all subagents must follow
- Deciding whether the work should run in one round or two rounds
- Distinguishing read-only exploration agents from implementation agents
- Identifying shared-file and ownership conflicts before broad execution
- Generating task packet templates and user confirmation checkpoints
- Consuming research artifacts without flattening uncertainty into settled rules

It is not responsible for binding execution to one specific subagent platform.

## Required Operating Principles

- If the rules are not converged, the work must not be split.
- If repository understanding is still shallow, formal research must happen before the rules are treated as frozen.
- If two tasks may touch the same file, the split is invalid until corrected.
- Exploration subagents are read-only.
- Implementation subagents must not invent rules.
- Parallel exploration may start early; parallel modification may not.
- The primary agent must present the execution plan to the user and ask for confirmation before the broad implementation phase starts.
- If upstream research contains a `Decision Blocker`, broad implementation must not begin until it is resolved.

## Workflow

1. **Task classification**
   Confirm the request is a semantic batch refactor rather than a simple mechanical change.

2. **Requirement clarification**
   Drive toward complete understanding of:
   - target outcome
   - scope and exclusions
   - old vs new rule set
   - edge cases and exceptions
   - shared definitions
   - acceptance criteria
   - autonomous decision boundaries
   - open questions

3. **Formal research decision**
   Decide whether the current understanding is strong enough to freeze rules directly. If not, run `context-pack` first and treat its `Research Report` and `Context Pack` as formal orchestration inputs.

4. **Rule specification**
   Convert the clarified requirements into an execution-ready spec instead of a conversational summary.

5. **Exploration strategy**
   Decide whether the primary agent can gather enough context alone or needs read-only exploration subagents to scan a large search surface and summarize findings. If a `Context Pack` already exists, use it to identify rule sources, candidate search areas, and likely contention surfaces before dispatching more exploration work.

6. **Trial calibration**
   Perform a small verification cycle:
   - read and reason through representative patterns
   - make a tiny real sample edit set
   - surface missing rules, hidden exceptions, and ownership issues
   - return to clarification if necessary

7. **Conflict assessment and execution mode selection**
   Choose between:
   - single-round parallel implementation
   - two-round execution: exploration first, primary-agent consolidation second, implementation third

8. **Task partitioning**
   Split by non-overlapping file ownership first, not by equal work volume.

9. **Source-bound task packet assembly**
   Every task packet must include concrete must-read sources such as the rule spec, correction notes, authoritative code files, or sample edits. If a `Context Pack` exists, the orchestrator should extract only the task-local blocks that matter to that child task. The primary agent summary is only an orientation layer, not the source of truth.

10. **User approval gate**
   Present the plan, risk points, execution mode, and primary-agent responsibilities to the user. Only proceed when the user approves or adjusts the plan.

11. **Execution and consolidation**
   Dispatch task packets according to the selected mode and validate the aggregate result against the spec.

12. **Feedback incorporation**
   If user feedback or execution output exposes a bad assumption, the primary agent must:
   - determine whether the issue is local or spec-wide
   - clarify unresolved doubt with the user
   - update the shared rules specification
   - update future task guidance
   - pause and reissue affected rounds before continuing

## Clarification Model

The skill should force the primary agent to gather eight categories of information:

1. Goal definition
2. Scope and exclusions
3. Change rules
4. Exceptions and edge cases
5. Shared definitions and likely contention points
6. Acceptance criteria
7. Autonomous decision boundaries
8. Explicit unresolved questions

If the agent cannot answer what the new rule is, what exceptions exist, or how correctness will be judged, it must not proceed to task splitting.

If `context-pack` has already been used, the orchestrator must review its outputs for:

- `Fact` items that are safe candidates for rule-freezing
- `Inference` items that still need direct verification
- `Open Question` and `Decision Blocker` items that constrain execution
- shared-file or ownership warnings
- task-specific context blocks that may later be passed to implementation subagents

## Exploration Model

The skill distinguishes two subagent roles.

### Exploration subagents

Allowed to:

- search widely
- classify patterns
- identify candidate files
- identify central/shared files
- summarize exceptions and unknowns

Not allowed to:

- edit files
- define new rules
- silently expand scope

They should also cite concrete sources when reporting findings that may influence the shared rules.

When upstream research already exists, exploration subagents should build on that map rather than rediscovering it blindly.

### Implementation subagents

Allowed to:

- modify only assigned files
- apply the frozen rule specification
- report gaps or ambiguous cases

Not allowed to:

- modify shared files unless explicitly assigned
- change files outside their packet
- invent new mappings or exception logic

## Trial Calibration Design

Trial calibration is mandatory when:

- the requested format or rule set is new
- project references are weak or inconsistent
- the search space is large
- the primary agent suspects hidden special cases

The calibration pass should:

- include read-based reasoning and actual edits
- use a small set of representative sample files
- cover multiple common patterns, not just the easiest example
- produce a delta report for new rules, new ambiguities, and newly discovered conflict files

If calibration exposes core misunderstanding, the process returns to clarification.

## Execution Modes

### Single-round parallel execution

Use only when:

- the rules are stable
- file ownership can be partitioned clearly
- shared-file risk is low
- trial calibration did not expose major ambiguity
- no unresolved `Decision Blocker` remains in the latest research artifact or rule spec

### Two-round execution

Use when:

- search space is large or poorly mapped
- central/shared files are numerous
- edge cases are common
- partition boundaries are unclear

Round structure:

1. Read-only exploration round
2. Primary-agent consolidation and shared-file handling
3. Parallel implementation round

## Partitioning Rules

Preferred split order:

1. explicit file list ownership
2. directory/module ownership that resolves to explicit files
3. caller group ownership
4. staged ownership, where central definitions are handled before downstream call sites

Disallowed split patterns:

- vague scope-only assignments
- overlapping responsibility without file ownership
- multiple subagents editing the same shared definition file
- splitting by action type alone when files overlap

Default rule:

If two task packets could edit the same file, the partition has failed and must be redesigned.

## Primary-Agent Responsibilities

The primary agent should personally handle or explicitly consolidate:

- event definitions
- shared constants
- shared types
- common helper wrappers
- central exports
- global config and adapter layers

This may happen before implementation dispatch or between round one and round two.

## Template Set

The skill should provide the following reusable templates:

1. Research Intake Template
2. Rules Specification Template
3. Exploration Task Template
4. Trial Calibration Template
5. Implementation Task Template
6. Execution Strategy and Aggregate Acceptance Template
7. User Approval Prompt Template
8. Feedback Update Template
9. Source-Bound Task Packet Fields

The Research Intake Template should capture:

- whether formal repository research was already run
- where the research artifacts live
- which findings are `Fact` vs `Inference`
- what blockers remain unresolved
- which task-local context blocks are candidates for later packet assembly

## Expected User Checkpoint

Before broad execution, the primary agent must present:

- its understanding of the goal
- the frozen rule summary
- chosen execution mode
- what the primary agent will handle directly
- what subagents will handle
- known risks and unresolved items
- a direct request for approval or adjustment

## Failure and Recovery

If the process discovers:

- unresolved core semantics -> return to clarification
- stale or insufficient upstream research -> refresh the sources or rerun `context-pack`
- unclear ownership boundaries -> switch to two rounds or redesign split
- too many contested central files -> primary agent consolidates them first
- inconsistent subagent outputs -> pause, update the spec, and resume only after reconvergence
- user-confirmed rule deviation -> update the spec and downstream task notes before further rounds
- missing authoritative context in task packets -> stop dispatch and add must-read sources first
- context-pack over-distribution -> rebuild child packets using only task-local blocks plus authoritative sources

## Outcome

The resulting skill should give a primary agent a disciplined way to convert ambiguous large-scale semantic edits into a spec-driven, conflict-aware, research-aware, user-approved multi-subagent execution plan.
