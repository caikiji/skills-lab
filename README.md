# Skills Lab

This repository stores reusable local agent skills and their supporting documents.

## Installation

### From GitHub (any machine)

```
/plugin marketplace add https://github.com/Cai-ki/skills-lab
/plugin install easywork@skills-lab
```

### From local path (already cloned)

```bash
git submodule update --init --recursive
```

```
/plugin marketplace add path\to\skills-lab
/plugin install easywork@skills-lab
```

After installing, run `/plugin reload-plugins` or restart Claude Code.
All 19 skills load automatically - no separate superpowers installation needed.

## Repository Layout

- `agents/`: shared child-agent role contracts used across multiple skills
- `skills/context-pack/`: the skill itself and its reusable reference files
- `skills/batch-refactor/`: the skill itself and its validation scenarios
- `skills/deepresearch/`: the skill itself and its references, agents, and scripts
- `skills/log-query/`: natural-language log analysis over large local log sets using staged text filtering
- `skills/using-easywork/`: the entry guide for choosing among the orchestration skills
- `superpowers/`: git submodule - general-purpose skills library

## Skill Index

| Skill | Purpose | Status |
| --- | --- | --- |
| `context-pack` | Evidence-driven codebase research; produces `Research Report` + `Context Pack` with `sbro_readiness` signal for downstream agents | Active |
| `deepresearch` | User-facing codebase research; produces a layered Markdown report with Mermaid diagrams | Active |
| `batch-refactor` | Specification-first orchestration for large semantic batch refactors; consumes a `Context Pack` when one exists | Active |
| `log-query` | Answers natural-language questions over large local log files with staged text filtering, evidence-backed statistics, and optional post-filter semantic narrowing | Active |
| `using-easywork` | Selects the right orchestration skill and sequence for human-facing research, downstream-agent context packaging, and semantic batch refactors | Active |
| `brainstorming` | Before any creative work - explores intent, proposes approaches, gets design approval | Active |
| `writing-plans` | Turns a spec into a precise, step-by-step implementation plan | Active |
| `writing-skills` | Creates and validates skill documents using TDD methodology | Active |
| `subagent-driven-development` | Executes a plan in the current session with per-task subagents and two-stage review | Active |
| `executing-plans` | Fallback plan execution without subagents | Active |
| `dispatching-parallel-agents` | Runs 2+ independent tasks concurrently via parallel subagents | Active |
| `using-git-worktrees` | Creates isolated git worktrees before feature work | Active |
| `test-driven-development` | Write failing test first, then minimal implementation | Active |
| `systematic-debugging` | Four-phase root-cause debugging before any fix attempt | Active |
| `verification-before-completion` | Runs verification commands and reads output before claiming work is done | Active |
| `requesting-code-review` | Dispatches a reviewer subagent with precise git SHA range | Active |
| `receiving-code-review` | Technically evaluates review feedback before implementing | Active |
| `finishing-a-development-branch` | Verifies tests, presents merge/PR/keep/discard options, cleans up worktree | Active |
| `using-superpowers` | Session startup - establishes how to find and invoke skills | Active |

## Skill Relationships

The three orchestration skills connect at defined handoff points.

```
deepresearch ----------------------------------> human reader
                (if codebase-wide change found)
                       suggests running context-pack --> (user decides)

context-pack
  + Context Pack
        + sbro_readiness: ready_to_freeze | needs_verification | blocked
        + SBRO Handoff Block (facts / inferences / blockers / shared-file risks)
              v
batch-refactor
  + step 3: checks sbro_readiness; gates execution on blocked/needs_verification
  + step 12: writes corrections.md in Context Pack schema -> future context-pack runs can read it
```

**When to run context-pack before batch-refactor:**

| Situation | Action |
|-----------|--------|
| Task crosses >= 3 modules | Run `context-pack` first |
| Shared files / types / event definitions not yet located | Run `context-pack` first |
| Primary agent cannot write rules without reading source | Run `context-pack` first |
| Task limited to 1-2 modules with clear boundaries | Inline exploration in `batch-refactor` |
| Fresh Context Pack already exists | Consume directly - skip `context-pack` |

**deepresearch vs context-pack:** Both research codebases but serve different consumers.
Use `deepresearch` when the output is a document for a human to read.
Use `context-pack` when the output feeds downstream agents or `batch-refactor`.
Use `using-easywork` when the agent first needs to make that selection and sequence the handoff correctly.

## Orchestration And Analysis Skills (`agents/`, `skills/context-pack/`, `skills/deepresearch/`, `skills/batch-refactor/`, `skills/log-query/`)

### `using-easywork`

Entry guide for the orchestration layer in this repository. Helps the agent decide:

- when a user-facing report calls for `deepresearch`
- when reusable, source-backed context calls for `context-pack`
- when a large semantic code change calls for `batch-refactor`
- when the right path is `context-pack -> batch-refactor`

- `skills/using-easywork/SKILL.md`

### `context-pack`

Evidence-driven codebase research and context packaging. Produces a `Research Report`
for human understanding and a `Context Pack` for downstream agents. Includes a
`sbro_readiness` field and `SBRO Handoff Block` when semantic batch execution is
likely downstream.

- `skills/context-pack/SKILL.md`
- `skills/context-pack/references/output-templates.md`
- `skills/context-pack/references/delegation-guidance.md`
- `skills/context-pack/pressure-scenarios.md`

### `deepresearch`

User-facing codebase research. Produces a layered Markdown document with embedded
Mermaid diagrams. Uses parallel subagents and persistent multi-round state so large
codebases can be researched across context resets. Accepts `depth: quick | standard | deep`.

Not a substitute for `context-pack` when structured agent-consumable output is needed.

- `skills/deepresearch/SKILL.md`
- `skills/deepresearch/agents/exploration-agent.md`
- `skills/deepresearch/references/subagent-scaling.md`
- `skills/deepresearch/references/plan-template.md`
- `skills/deepresearch/references/output-document-template.md`

### `batch-refactor`

Specification-first orchestration for large semantic code changes. Consumes a
`Context Pack` when one exists, checks `sbro_readiness` before rule-freezing, and
writes `corrections.md` after execution so future `context-pack` runs can treat corrections as
prior research.

- `skills/batch-refactor/SKILL.md`
- `skills/batch-refactor/pressure-scenarios.md`

### `log-query`

Natural-language log analysis for large local log sets. The skill is workflow-only:
it teaches the agent to sample first, translate the question into explicit include
and exclude filters, prefer platform-native text tools such as `rg`, `grep`, or
PowerShell-compatible search, and only use semantic narrowing after the candidate
set is small enough to inspect safely.

- `skills/log-query/SKILL.md`
- `skills/log-query/pressure-scenarios.md`

## Superpowers Skills (`superpowers/skills/`)

General-purpose development workflow skills. Load automatically alongside the
orchestration skills - no separate installation needed.

| Skill | When to use |
|-------|-------------|
| `using-superpowers` | Session startup - establishes how to find and invoke skills |
| `brainstorming` | Before any creative work: features, components, behavior changes |
| `writing-plans` | When you have a spec and need a step-by-step implementation plan |
| `writing-skills` | When creating or editing skill documents (applies TDD to documentation) |
| `subagent-driven-development` | Executing a plan in the current session with per-task subagents and two-stage review |
| `executing-plans` | Fallback when subagents are unavailable - inline sequential execution |
| `dispatching-parallel-agents` | When 2+ independent tasks can be worked on concurrently |
| `using-git-worktrees` | Before feature work that needs an isolated workspace |
| `test-driven-development` | Before writing any implementation code - write the failing test first |
| `systematic-debugging` | When encountering any bug or unexpected behavior - find root cause before fixing |
| `verification-before-completion` | Before claiming work is done - run the verification command and read the output |
| `requesting-code-review` | After completing a task or feature - dispatch a reviewer subagent |
| `receiving-code-review` | When acting on review feedback - verify before implementing |
| `finishing-a-development-branch` | When implementation is complete - verify tests, choose merge/PR/keep/discard |

## Adding New Skills

1. Create `<skill>/SKILL.md` and supporting files
2. Update this README skill index table

## Maintenance Notes

- Keep the Skill Index table updated when adding or renaming skills.
- Prefer one top-level directory per skill.
- When editing canonical agent files under `agents/`, sync the same change to local copies in skill-specific `agents/` directories.
