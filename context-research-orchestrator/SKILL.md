---
name: context-research-orchestrator
description: Evidence-driven codebase research and context packaging for complex tasks. Use when Codex needs to deeply understand a project or task area before planning, freezing rules, coordinating subagents, or executing semantic refactors, especially when the output must include reusable summaries, source references, and freshness metadata.
---

# Context Research Orchestrator

Build trustworthy project context before planning or broad execution.

This skill is for research, not implementation. Use it to gather the minimum sufficient evidence needed to support the next decision safely, then package that evidence so humans and later agents can reuse it.

## What This Skill Produces

- `Research Report` for human and primary-agent understanding
- `Context Pack` for downstream skills or subagents

Read [references/output-templates.md](references/output-templates.md) when you are ready to emit either artifact.

## Non-Goals

Do not:

- read the entire repository unless the evidence requires it
- convert guesses into rules
- replace user decisions on scope or business behavior
- let exploration subagents edit files
- hand downstream agents summary-only packets when source-backed context is required

## Operating Modes

### Targeted research

Default mode. Research only the code, docs, config, and history needed for the current task.

### Deep research

Escalate only when:

- the user explicitly asks for a full project investigation
- the search surface is too unclear for targeted research
- the task is risky enough that shallow context is unsafe
- repeated targeted exploration still leaves critical gaps

## Core Rules

1. Start with a light probe before broad exploration.
2. Escalate depth only when the current evidence is insufficient.
3. Mark important findings as `Fact`, `Inference`, `Open Question`, or `Decision Blocker`.
4. Ground every important claim in project sources.
5. Treat line numbers as convenience, not as the only anchor.
6. Record provenance so later agents can judge freshness.
7. Stop when the next decision can be made safely.

## Workflow

### 1. Intake

Identify:

- the question the research must answer
- the downstream action it supports
- whether you are starting in targeted or deep mode
- what uncertainty is already visible

### 2. Light probe

Perform the smallest useful pass through:

- repository structure
- task-adjacent files
- relevant docs
- obvious entrypoints
- recent git history, but only when it is likely to matter

Use the result to decide whether the primary agent can continue alone.

The light probe is sufficient when the primary agent can answer:
- Which files or modules are directly relevant to the task?
- Are there obvious shared definitions or cross-cutting concerns?
- Is the search surface narrow enough to continue inline, or does it require subagent dispatch?

If all three can be answered with reasonable confidence, proceed to step 3.
If not, escalate depth before continuing.

### 3. Research planning

Choose one:

- continue inline
- dispatch a small number of read-only exploration subagents
- use multi-round exploration

Read [references/delegation-guidance.md](references/delegation-guidance.md) before dispatching any exploration subagent.
For runtime child-agent role guidance, use [agents/read-only-exploration-agent.md](agents/read-only-exploration-agent.md) as the default role contract for read-only exploration work.

### 4. Focused exploration

Collect evidence about:

- rule sources
- call paths and entrypoints
- shared definitions
- data or execution flow
- likely edit surfaces
- exceptions and ambiguous cases

If subagents are used, they must remain read-only and return summaries with source references.
Prefer dispatch packets that explicitly declare `Role: read-only-exploration-agent` and provide must-read sources before wide searching begins.

### 5. Synthesis

Produce:

- `Research Report`
- `Context Pack`

Separate established facts from inferences and unresolved questions. If the evidence still does not support a needed judgment, surface that gap instead of improvising.

### 6. Freshness and handoff check

Before finalizing:

- record git state when available
- note whether the worktree is clean or dirty
- capture timestamps for key files when useful
- check that important anchors are still relocatable when practical
- split task-specific context into reusable packets when later subagent work is likely

## Citation Rules

For each important claim, prefer layered citations:

- `file`
- `anchor`
- `line_at_capture`
- `relocation_hint`
- `captured_claim`

Stable anchors include symbols, unique strings, config keys, section titles, and distinctive phrases. If a claim matters enough to guide later work, explain how to relocate it after code drift.

## Freshness Rules

When available, record:

- `captured_at`
- `research_mode`
- `workspace_state`
- `git_commit`
- `git_branch`
- `related_dirty_files`
- `key_file_timestamps`
- `confidence_scope`

If the repository state changes after capture, downstream agents should re-check important claims before treating them as authoritative.

## Stopping Rules

Continue researching when the remaining uncertainty appears solvable through code, docs, repository structure, or commit history.

Stop and escalate when the unresolved issue depends on:

- business intent
- scope boundaries
- acceptance criteria
- policy decisions
- ambiguous target behavior that project evidence cannot settle

Never silently upgrade an `Inference` into a mandatory implementation rule.

## Rationalization Traps

Stop if the primary agent starts thinking any of these:

| Rationalization | Required response |
| --- | --- |
| "The task is small, I don't need citations." | Evidence is reused by downstream agents. Always cite important claims. |
| "The codebase strongly implies this pattern, so it must be Fact." | If no source explicitly confirms it, label it `Inference`. |
| "I'll escalate to deep research just to be safe." | Start with targeted research. Escalate only when evidence requires it. |
| "This summary is close enough to pass downstream." | If it will guide later agents, back it with source references. |
| "I didn't find the answer, so I'll infer it." | Surface the gap as `Open Question` or `Decision Blocker` instead. |
| "The context pack is getting large, I'll trim the citations." | Preserve citations. Downstream agents need them to judge authority. |
| "The file changed slightly but the claim still seems right." | Re-check the source. Mark as stale-risk if you cannot re-verify. |

## Persistence

Keep output inline for small, one-off investigations.

Persist artifacts when:

- the task is complex
- the research has reuse value
- later planning or orchestration will consume it
- the context would be expensive to reconstruct

When persisting, save the `Research Report` and `Context Pack` under `docs/orchestration/research/`.

Resolve that path relative to the current repository root. If the workspace is not a git repository, resolve it relative to the current working directory unless the user explicitly chooses another output location.

Default file naming:

- `YYYY-MM-DD-<topic>-research-report.md`
- `YYYY-MM-DD-<topic>-context-pack.md`

Add a short handoff note only when it helps later agents find the right blocks quickly.

## Downstream Integration

This skill is a natural precursor to semantic or high-risk orchestration workflows.

Use it before:

- freezing rules for a semantic batch refactor
- partitioning work across subagents
- writing plans that depend on accurate project boundaries
- constructing source-backed task packets

This skill may prepare rule-relevant evidence, shared-file risk notes, and candidate task boundaries. It must not finalize execution rules on behalf of the downstream orchestrator.
