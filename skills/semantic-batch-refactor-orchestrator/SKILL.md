---
name: semantic-batch-refactor-orchestrator
description: Use when a codebase-wide semantic change is large enough for parallel work but needs strict requirement clarification, conflict-aware task partitioning, and controlled subagent execution
---

# Semantic Batch Refactor Orchestrator

## Overview

Use this skill for large semantic code changes where each edit may be simple, but the overall task is risky because the rules are unclear, the search surface is wide, and parallel agents could diverge or collide. The primary agent must freeze the rules before broad implementation begins.

When repository understanding is still too shallow to freeze rules safely, use `context-research-orchestrator` first to produce a `Research Report` and `Context Pack`. Treat those artifacts as input to orchestration, not as a replacement for rule-freezing.

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
- Task packets must include concrete must-read sources, not only summaries.
- Exploration subagents are strictly read-only.
- Implementation subagents must not invent new mappings, event schemas, or exception logic.
- If two task packets may touch the same file, the partition is invalid.
- Shared definition files should stay with the primary agent unless ownership is explicitly isolated.
- Broad execution requires an explicit user approval checkpoint.
- Parallel exploration may begin early; parallel modification may not.
- If `context-research-orchestrator` reports a `Decision Blocker`, broad execution must not begin until it is resolved.
- When dispatching any subagent, read the applicable agent role file in full and paste its complete content verbatim at the top of the subagent prompt, before any task-specific fields.
- Total parallel subagents must not exceed 6 at any time, across both exploration and implementation rounds.

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

3. **Decide whether repository research must be formalized first**

   Use this table to decide:

   | Situation | Action |
   |-----------|--------|
   | Task crosses ≥ 3 modules | Run CRO first |
   | Shared files / types / event definitions not yet located | Run CRO first |
   | Primary agent cannot write rules without reading source | Run CRO first |
   | Task limited to 1–2 modules with clear boundaries | Inline exploration |
   | Fresh Context Pack already exists | Consume directly — skip CRO |

   **If a Context Pack exists:** check freshness before use. Compare `git_commit`
   in the pack against the current HEAD. If significant commits have landed on
   in-scope files since `captured_at`, re-run CRO on the affected areas. A pack
   is safe to reuse when `sbro_readiness` is `ready_to_freeze` and no in-scope
   files have changed since capture.

   **After CRO completes:** check `sbro_readiness` before continuing:
   - `ready_to_freeze` — proceed to step 4
   - `needs_verification` — verify the flagged Inferences from source before writing the rules specification
   - `blocked` — resolve Decision Blockers with the user; do not proceed to step 4

   Fill in the Research Intake Template (see below) whenever a Context Pack
   is being consumed, so the state of incoming research is explicit before
   rule-freezing begins.

4. **Write a rules specification**
   Turn the clarified requirements into an execution spec. This is not a summary. It must be detailed enough that multiple agents will make the same decision on the same input.

5. **Choose an exploration strategy**
   The primary agent may explore critical files directly. If a `Context Pack` already exists, use it to identify likely rule sources, contention surfaces, and candidate search areas first. If the search surface is still too large, dispatch read-only exploration subagents to gather patterns, candidate files, and likely contention points. **Mandatory before any exploration dispatch:** read the skill-local role file `skills/semantic-batch-refactor-orchestrator/agents/read-only-exploration-agent.md` in full and paste its complete content verbatim at the top of each exploration subagent prompt, before any task-specific fields. If that file is unavailable in the current installation, fall back to `agents/read-only-exploration-agent.md`. The subagent will otherwise not know its role, constraints, or output format.

6. **Run trial calibration**
   First reason through representative examples. Then make a small real sample edit set that covers multiple common patterns. Use the results to expose missing rules, hidden exceptions, and contested files.

7. **Assess conflicts and select execution mode**
   Use single-round parallel execution only when the rules are stable and ownership is clear. Otherwise use two rounds:
   - round 1: read-only exploration
   - middle: primary-agent consolidation and shared-file handling
   - round 2: implementation on non-overlapping file sets

8. **Partition by ownership**
   Split by explicit file ownership first. Directory or module boundaries are acceptable only when they resolve cleanly into non-overlapping file sets.

9. **Bind source-backed context into each task packet**
   Every task packet must include the exact documents or code files the subagent must read before acting. If a `Context Pack` exists, extract only the task-relevant blocks and pair them with must-read source paths. Summaries may help orient the work, but they are not the authority. **Mandatory before any implementation dispatch:** read the skill-local role file `skills/semantic-batch-refactor-orchestrator/agents/implementation-agent.md` in full and paste its complete content verbatim at the top of each implementation subagent prompt, before any task-specific fields. If that file is unavailable in the current installation, fall back to `agents/implementation-agent.md`. The subagent will otherwise not know its authority hierarchy, decision boundaries, or escalation rules.

10. **Ask the user to approve the plan**
   Present the frozen rule summary, execution mode, primary-agent responsibilities, subagent responsibilities, and known risks. Do not start broad implementation before approval.

11. **Execute and consolidate**
   Dispatch task packets, collect results, and validate the aggregate outcome against the spec before declaring success.

12. **Feed corrections back into the shared guidance**
   If user feedback or execution results expose a mistaken rule, missing exception, or ambiguous instruction:
   - pause affected downstream work
   - clarify remaining uncertainty with the user if needed
   - update the shared rules specification
   - update task notes for later rounds
   - reissue the changed guidance before resuming implementation

   If the correction is substantive (alters rule mapping, reveals a new shared
   file, or changes scope boundaries), also write a correction note to
   `docs/orchestration/research/YYYY-MM-DD-<topic>-corrections.md` using the
   Context Pack block schema. Future CRO runs can treat this file as prior
   research and avoid repeating the same investigation.

   **Re-approval rule:** If the rule change is minor (a local edge case, no effect on
   other packets or shared files), apply it inline without returning to step 10. If the
   rule change is substantial — it alters the core mapping logic, changes scope
   boundaries, affects shared files, or would change what any future packets do — stop
   broad execution, present a revised Execution Checkpoint to the user, and wait for
   approval before resuming. When in doubt, treat the change as substantial.

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

If `context-research-orchestrator` has already been run, review its outputs for:

- `Fact` findings that can support rule freezing
- `Inference` findings that still need verification
- `Open Question` and `Decision Blocker` items that limit execution
- `Shared Files` or equivalent contention notes
- task-specific blocks that may later become child task packet context
- whether the latest persisted `Context Pack` in `docs/orchestration/research/` is still fresh enough to use directly

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
- cite the provided sources when reporting rule-relevant findings

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

## Source-Bound Context

Summaries are only orientation aids. Any rule that affects implementation must be backed by explicit, readable sources inside the task packet.

If `context-research-orchestrator` has produced a `Context Pack`, treat it as a context index, not as the authority itself. The pack helps choose what to pass, but must-read sources still carry final authority.

Each task packet should separate:

- `Must-read sources`
- `Reference sources`
- `Authoritative source for rule conflicts`
- `Relevant context blocks`
- `Open questions or blockers that still affect this task`

Required behavior:

1. The subagent reads the must-read sources before acting.
2. If the task packet summary conflicts with an authoritative source, the authoritative source wins.
3. If the required sources do not support a needed judgment, the subagent must stop and report instead of inferring.
4. If the primary agent wants a specific sample or rule to guide implementation, it must include the file path directly.
5. If a `Context Pack` exists, include only the task-local blocks the subagent needs; do not dump the entire pack into every child task.
6. If a relevant context block is marked `Inference`, `Open Question`, or `Decision Blocker`, keep that label in the task packet instead of flattening it into a settled rule.

Never rely on "the primary agent probably summarized it correctly" as a substitute for source-backed context.

## Feedback Incorporation

When the user reports that a completed subtask is wrong, treat it as a possible rules problem first, not only as a local fix.

Required response:

1. Determine whether the issue is local, pattern-wide, or spec-wide.
2. If the primary agent still has doubts, clarify with the user before more delegation.
3. Update the shared rules specification with the corrected rule, exception, or example.
4. Update the task notes for all future or paused rounds so subagents do not keep following stale guidance.
5. Pause or reissue affected tasks before resuming execution.

Never fix one result silently and continue with stale task packets.

When the primary agent wants a focused standards check after implementation, read the skill-local role file `skills/semantic-batch-refactor-orchestrator/agents/spec-conformance-reviewer.md` in full and paste its complete content verbatim at the top of each conformance review subagent prompt, before any task-specific fields. If that file is unavailable in the current installation, fall back to `agents/spec-conformance-reviewer.md`.

## Execution Mode Selection

Use **single-round** execution only when:

- rules are stable
- project patterns are reliable
- shared-file risk is low
- sample calibration did not expose major ambiguity
- files can be partitioned cleanly
- no unresolved `Decision Blocker` remains in the latest research output

**How single-round relates to the Hard Rules:** Single-round execution does not
eliminate exploration — it compresses it. The primary agent performs all necessary
exploration inline (steps 5–6) before partitioning. Parallel file modification still
cannot begin until ownership is frozen and the execution plan is approved. The only
difference from two-round execution is that exploration is not dispatched to parallel
subagents; it stays with the primary agent in the same session.

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

### Research Intake Template

```md
## Research Intake
- Was `context-research-orchestrator` run?:
- Research artifact locations:
- Facts safe to rely on:
- Inferences that still need verification:
- Open questions:
- Decision blockers:
- Shared-file or ownership warnings:
- Candidate task-local context blocks:
```

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
- Rule revisions:
- Latest correction summary:
- Sample reference:
```

### Exploration Task Template

```md
## Exploration Task
- Role: read-only-exploration-agent
- Objective:
- Must-Read Sources:
  - [path]
- Search Area:
- Questions to answer:
- Patterns to classify:
- Shared-file types to identify:
- Output Contract:
  - summary of findings
  - source references with anchors
  - open questions
  - suspected contention surfaces
- Stop Conditions:
  - stop if the must-read sources are missing or insufficient
  - stop if critical evidence lies outside the assigned search area
  - stop if the packet cannot resolve conflicting source material
- Helpful reference sources:
  - [path]
- Findings that require source citation:
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
- Must-read sources:
- Reference sources:
- Authoritative source for rule conflicts:
- Relevant context blocks:
- Inherited open questions or blockers:
- Allowed files:
- Forbidden files:
- May expand to new files?:
- Shared-file handling rule:
- What to do if the spec does not cover a case:
- If required context is missing: stop, report, and do not infer
- Latest rule updates to honor:
- Superseded guidance to ignore:
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
- If a research artifact is stale, refresh the affected sources or rerun `context-research-orchestrator` before broad execution.
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
| "We fixed that bad result already, so there is no need to update the packets." | Update the shared spec and future task notes before resuming later rounds. |
| "The summary is enough; the subagent does not need the actual files." | Add must-read source paths to the packet before dispatch. |
