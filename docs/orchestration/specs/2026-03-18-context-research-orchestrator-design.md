# Context Research Orchestrator Design

> **For agentic workers:** This document defines the design for a reusable skill. Use it as the source of truth before writing an implementation plan or editing the skill files.

**Goal:** Create a reusable skill that performs evidence-driven project research, optionally coordinates read-only exploration subagents, and produces source-bound research artifacts that can be reused by later planning and orchestration work.

**Status:** Approved design draft

---

## 1. Summary

`context-pack` is a general-purpose research skill for building trustworthy project context before planning, rule-freezing, semantic batch refactors, or multi-subagent execution.

Its job is not to read as much of the repository as possible. Its job is to gather the minimum sufficient evidence needed to produce reusable context that is:

- traceable back to project sources
- resilient to code drift
- safe to hand off to later agents
- explicit about uncertainty

The skill must support two operating modes:

- **Targeted research:** Default mode. Research only the areas needed for the current task.
- **Deep research:** Escalated mode for large, unclear, risky, or user-requested repository investigation.

The skill is designed as a standalone capability, but it explicitly supports downstream consumers such as `batch-refactor`.

## 2. Non-Goals

The skill must not:

- maximize repository coverage for its own sake
- silently convert guesses into rules
- replace user decisions on business logic or scope boundaries
- act as a general implementation skill
- allow exploration subagents to edit files or invent mappings

## 3. Triggering Intent

The skill should trigger in medium-strength cases, not on every small code-reading task.

It should trigger when:

- the user explicitly asks for deep project research or wants understanding before changes
- the next step will likely involve planning, rule freezing, migration, or semantic refactoring
- reliable context must be prepared for subagent dispatch
- the task spans multiple modules or has shared-definition risk
- the current session context is too shallow to proceed safely

It should usually not trigger when:

- the task is small, local, and low-risk
- the active agent already has enough grounded context
- there is no expected reuse value in producing research artifacts

## 4. Core Design Principles

### 4.1 Evidence-driven escalation

Start with the smallest useful exploration pass. Expand the search surface only when the evidence says the current view is insufficient.

### 4.2 Research assets, not disposable notes

The output must be reusable by humans, later skills, and subagents. Findings should be structured so they can survive beyond the current turn.

### 4.3 Source-bound conclusions

Every important claim must point back to project evidence. Citations must remain useful even when exact line numbers drift.

### 4.4 Explicit certainty levels

Important findings must be marked as one of:

- `Fact`
- `Inference`
- `Open Question`
- `Decision Blocker`

### 4.5 Safe delegation

Subagents may help explore, but only through read-only investigation with tightly scoped prompts and clearly bounded output expectations.

## 5. Operating Modes

### 5.1 Targeted research

Use when the current task has a reasonably clear target and the agent mainly needs project-specific evidence, structure, and references.

Typical examples:

- preparing for an implementation plan
- understanding a migration surface
- locating rule sources before a semantic refactor
- gathering context to package into task packets

### 5.2 Deep research

Use when:

- the user explicitly requests a full project investigation
- the project is large and the relevant surface cannot be identified cheaply
- the task is high-risk and later mistakes would be expensive
- repeated escalation from targeted research still leaves major uncertainty

Deep research still follows the same principle: stop when evidence is sufficient for the next action, not when every file has been read.

## 6. Workflow

### 6.1 Intake

Read the user request, available thread context, and current workspace state.

Decide:

- what question the research must answer
- what downstream action it is supporting
- whether the starting mode is targeted or deep
- what uncertainty is already visible

### 6.2 Light probe

Perform a minimal pass to build an initial map.

Typical sources:

- repository structure
- relevant directories
- obvious entrypoints
- task-adjacent code
- task-adjacent docs
- small amounts of recent git history when it is likely to matter

The goal is to answer:

- where the likely evidence lives
- whether the work crosses modules
- whether there are shared definitions or contention surfaces
- whether the active agent can continue alone

### 6.3 Research planning

Choose one of:

- continue inline with the primary agent
- dispatch a small number of read-only exploration subagents
- run exploration in rounds

This is a planning step, not yet synthesis. It determines how much exploration is needed and how to spend tokens safely.

### 6.4 Focused exploration

Collect evidence about:

- relevant rules and rule sources
- entrypoints and call paths
- data flow and execution flow
- shared files and ownership risks
- exceptions and ambiguous cases
- likely edit surfaces

If subagents are used:

- they must be read-only
- they must not invent rules
- they must return summaries with source references
- their scopes must avoid overlapping reasoning goals when possible

### 6.5 Synthesis

Turn the evidence into two outputs:

- `Research Report`
- `Context Pack`

At this stage the skill must separate confirmed facts from inferences and unresolved questions.

### 6.6 Freshness and handoff check

Before finalizing:

- capture provenance metadata
- record git state when available
- record key file timestamps
- verify that important anchors are still relocatable when practical
- prepare task-ready slices when later subagent dispatch is expected

## 7. Delegation Strategy

The skill defaults to adaptive delegation.

### 7.1 Stay inline when

- the task is narrow
- the relevant evidence is concentrated
- the primary agent can already explain the likely rule boundaries
- there is little value in parallel exploration

### 7.2 Dispatch read-only exploration subagents when

- evidence is distributed across multiple cleanly separable modules
- the next stage depends on broader context
- later orchestration will need robust task packets
- the project is large enough that serial exploration is wasteful

### 7.3 Use multi-round exploration when

- many shared files appear relevant
- module boundaries are unclear
- the task is still semantically ambiguous
- premature partitioning would likely create inconsistent context packs

## 8. Stopping and Escalation Rules

Stop research when there is enough evidence to support the next decision safely.

Continue researching when uncertainty still appears solvable through:

- source code
- repository docs
- commit history
- repository structure

Escalate to the user or controlling agent when the unresolved issue is about:

- business rules
- intended scope
- acceptance criteria
- policy decisions
- ambiguous behavioral targets that source evidence cannot settle

The skill must never silently upgrade an `Inference` into a mandatory implementation rule.

## 9. Output Artifacts

## 9.1 Research Report

The `Research Report` is for human and primary-agent understanding.

It should contain:

- `Objective`
- `Scope`
- `Method`
- `Key Findings`
- `Architecture or Flow Summary`
- `Risks`
- `Recommended Next Step`

The report style is adaptive:

- small tasks: concise summary-first output
- complex tasks: more engineering-oriented structure

## 9.2 Context Pack

The `Context Pack` is a structured research asset for later machine and human consumption.

It should contain:

### A. Capture Provenance

- `captured_at`
- `research_mode`
- `workspace_state`
- `git_commit`
- `git_branch`
- `related_dirty_files`
- `key_file_timestamps`
- `confidence_scope`

### B. Global Theme Blocks

Examples:

- `Module Boundaries`
- `Entrypoints`
- `Shared Definitions`
- `Config Sources`
- `Data Flow`
- `Execution Flow`
- `Known Exceptions`
- `Contention Surfaces`

### C. Task-Specific Blocks

Examples:

- `Rule Sources`
- `Relevant Call Sites`
- `Candidate Edit Surfaces`
- `Shared Files to Avoid Parallel Editing`
- `Known Ambiguities`
- `Hypotheses to Verify`
- `Suggested Packet Boundaries`

### D. Block Schema

Every important block should include:

- `Title`
- `Purpose`
- `Classification`
- `Summary`
- `Why It Matters`
- `Evidence List`
- `Primary References`
- `Relocation Hints`
- `Freshness Notes`
- `Safe Reuse Boundary`

## 10. Citation and Drift Resistance

Line numbers alone are not enough.

Each important reference should prefer a layered citation model:

- `file`
- `anchor`
- `line_at_capture`
- `relocation_hint`
- `captured_claim`

Where useful, also include:

- symbol names
- search terms
- related definitions

Citation design rules:

- treat line numbers as accelerators, not truth anchors
- prefer stable symbols, strings, or structural anchors
- explain how to re-find the evidence if files drift
- include the claim captured from the evidence, not just the location

## 11. Freshness Model

The `Context Pack` must indicate what repository state it reflects.

When available:

- record current `HEAD`
- record current branch
- state whether the worktree is clean or dirty
- list relevant dirty files
- capture timestamps for key files

Downstream agents should:

- trust `Fact` conditionally, after a quick freshness check when state has changed
- treat `Inference` as something to verify before turning into a rule
- never ignore `Open Question` or `Decision Blocker`
- re-check any claim whose anchor cannot be relocated

## 12. Integration with Semantic Batch Refactor Orchestration

This skill is a natural precursor to `batch-refactor`.

Recommended integration points:

- after initial requirement clarification, before freezing rules
- before designing exploration rounds
- before partitioning by file ownership

The research outputs should help that orchestrator answer:

- what the real rule sources are
- which files are shared-risk surfaces
- which work areas are safe to split
- what context must travel in child task packets
- which ambiguities still block broad execution

The research skill may prepare these categories, but it must not finalize execution rules on behalf of the orchestrator.

## 13. Persistence Strategy

Use adaptive persistence.

Do not always write files. Write files when:

- the task is complex
- the research has reuse value
- later planning or orchestration will consume it
- the context would be expensive to reconstruct

When persisting artifacts, save:

- the `Research Report`
- the `Context Pack`
- optionally a short handoff summary

## 14. Example Context Block

```md
### Block: Shared rule source for task packet construction
- Classification: Fact
- Summary: Task packets are expected to stay source-bound rather than passing only paraphrased summaries.
- Why It Matters: Any downstream subagent packet that drops source references risks divergence from the orchestration rules.
- Primary References:
  - File: batch-refactor/SKILL.md
  - Anchor: "Task Packet Inputs"
  - Line at capture: 1
  - Relocation hint: search for "task packets" and "source-bound"
  - Captured claim: The orchestration workflow depends on passing grounded context into child packets.
- Freshness Notes: Re-check if the orchestrator skill changed after this pack was captured.
- Safe Reuse Boundary: Safe to reuse for downstream orchestration tasks; re-verify before changing packet schema.
```

## 15. Implementation Notes

The eventual skill implementation should likely include:

- a concise `SKILL.md`
- optional references for output templates and delegation prompts
- possibly a lightweight script or template support if structured context packs are repeatedly generated

The first implementation should optimize for:

- correctness of workflow
- strong output shape
- robust citation behavior
- compatibility with later orchestration skills

It should not optimize for maximum automation before the workflow proves stable.
