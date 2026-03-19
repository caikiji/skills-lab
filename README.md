# Skills

This repository stores reusable local agent skills and their supporting documents.

## Installation

### From GitHub (any machine)

```
/plugin marketplace add https://github.com/Cai-ki/agent-skills-lab
/plugin install agent-skills-lab@agent-skills-lab
```

### From local path (already cloned)

```bash
git submodule update --init --recursive
```

```
/plugin marketplace add D:\path\to\skills
/plugin install agent-skills-lab@agent-skills-lab
```

After installing, run `/plugin reload-plugins` or restart Claude Code.
All 17 skills load automatically — no separate superpowers installation needed.

## Repository Layout

- `agents/`: shared child-agent role contracts used across multiple skills
- `skills/context-research-orchestrator/`: the skill itself and its reusable reference files
- `skills/semantic-batch-refactor-orchestrator/`: the skill itself and its validation scenarios
- `skills/deepresearch/`: the skill itself and its references, agents, and scripts
- `superpowers/`: git submodule — general-purpose skills library
- `docs/orchestration/specs/`: design documents for skills

## Skill Index

| Skill | Purpose | Status |
| --- | --- | --- |
| `context-research-orchestrator` | Evidence-driven codebase research; produces `Research Report` + `Context Pack` with `sbro_readiness` signal for downstream agents | Active |
| `deepresearch` | User-facing codebase research; produces a layered Markdown report with Mermaid diagrams | Active |
| `semantic-batch-refactor-orchestrator` | Specification-first orchestration for large semantic batch refactors; consumes CRO Context Pack | Active |
| `brainstorming` | Before any creative work — explores intent, proposes approaches, gets design approval | Active |
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
| `using-superpowers` | Session startup — establishes how to find and invoke skills | Active |

## Skill Relationships

The three orchestration skills connect at defined handoff points.

```
deepresearch ──────────────────────────────────→ human reader
                (if codebase-wide change found)
                       suggests running CRO ──→ (user decides)

context-research-orchestrator (CRO)
  └── Context Pack
        ├── sbro_readiness: ready_to_freeze | needs_verification | blocked
        └── SBRO Handoff Block (facts / inferences / blockers / shared-file risks)
              ▼
semantic-batch-refactor-orchestrator (SBRO)
  ├── step 3: checks sbro_readiness; gates execution on blocked/needs_verification
  └── step 12: writes corrections.md in Context Pack schema → future CRO reads it
```

**When to run CRO before SBRO:**

| Situation | Action |
|-----------|--------|
| Task crosses ≥ 3 modules | Run CRO first |
| Shared files / types / event definitions not yet located | Run CRO first |
| Primary agent cannot write rules without reading source | Run CRO first |
| Task limited to 1–2 modules with clear boundaries | Inline exploration in SBRO |
| Fresh Context Pack already exists | Consume directly — skip CRO |

**deepresearch vs CRO:** Both research codebases but serve different consumers.
Use `deepresearch` when the output is a document for a human to read.
Use `context-research-orchestrator` when the output feeds downstream agents or SBRO.

## Orchestration Skills (`agents/`, `skills/context-research-orchestrator/`, `skills/deepresearch/`, `skills/semantic-batch-refactor-orchestrator/`)

### `context-research-orchestrator`

Evidence-driven codebase research and context packaging. Produces a `Research Report`
for human understanding and a `Context Pack` for downstream agents. Includes a
`sbro_readiness` field and `SBRO Handoff Block` when semantic batch execution is
likely downstream.

- `skills/context-research-orchestrator/SKILL.md`
- `skills/context-research-orchestrator/references/output-templates.md`
- `skills/context-research-orchestrator/references/delegation-guidance.md`
- `skills/context-research-orchestrator/pressure-scenarios.md`

### `deepresearch`

User-facing codebase research. Produces a layered Markdown document with embedded
Mermaid diagrams. Uses parallel subagents and persistent multi-round state so large
codebases can be researched across context resets. Accepts `depth: quick | standard | deep`.

Not a substitute for CRO when structured agent-consumable output is needed.

- `skills/deepresearch/SKILL.md`
- `skills/deepresearch/agents/exploration-agent.md`
- `skills/deepresearch/references/subagent-scaling.md`
- `skills/deepresearch/references/plan-template.md`
- `skills/deepresearch/references/output-document-template.md`

### `semantic-batch-refactor-orchestrator`

Specification-first orchestration for large semantic code changes. Consumes a CRO
`Context Pack` when one exists, checks `sbro_readiness` before rule-freezing, and
writes `corrections.md` after execution so future CRO runs can treat corrections as
prior research.

- `skills/semantic-batch-refactor-orchestrator/SKILL.md`
- `skills/semantic-batch-refactor-orchestrator/pressure-scenarios.md`

## Superpowers Skills (`superpowers/skills/`)

General-purpose development workflow skills. Load automatically alongside the
orchestration skills — no separate installation needed.

| Skill | When to use |
|-------|-------------|
| `using-superpowers` | Session startup — establishes how to find and invoke skills |
| `brainstorming` | Before any creative work: features, components, behavior changes |
| `writing-plans` | When you have a spec and need a step-by-step implementation plan |
| `writing-skills` | When creating or editing skill documents (applies TDD to documentation) |
| `subagent-driven-development` | Executing a plan in the current session with per-task subagents and two-stage review |
| `executing-plans` | Fallback when subagents are unavailable — inline sequential execution |
| `dispatching-parallel-agents` | When 2+ independent tasks can be worked on concurrently |
| `using-git-worktrees` | Before feature work that needs an isolated workspace |
| `test-driven-development` | Before writing any implementation code — write the failing test first |
| `systematic-debugging` | When encountering any bug or unexpected behavior — find root cause before fixing |
| `verification-before-completion` | Before claiming work is done — run the verification command and read the output |
| `requesting-code-review` | After completing a task or feature — dispatch a reviewer subagent |
| `receiving-code-review` | When acting on review feedback — verify before implementing |
| `finishing-a-development-branch` | When implementation is complete — verify tests, choose merge/PR/keep/discard |

## Adding New Skills

1. Write a design spec → `docs/orchestration/specs/YYYY-MM-DD-<name>-design.md`
2. Create `<skill>/SKILL.md` and supporting files
3. Update this README skill index table

## Maintenance Notes

- Keep the Skill Index table updated when adding or renaming skills.
- Prefer one top-level directory per skill.
- Store design documents under `docs/orchestration/specs/`.
- When editing canonical agent files under `agents/`, sync the same change to local copies in skill-specific `agents/` directories.
