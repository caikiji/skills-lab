# Skills

This repository stores reusable local agent skills and their supporting documents.

## Repository Layout

- `agents/`: shared child-agent role contracts used across multiple skills
- `context-research-orchestrator/`: the skill itself and its reusable reference files
- `semantic-batch-refactor-orchestrator/`: the skill itself and its validation scenarios
- `superpowers/`: git submodule dependency from `https://github.com/Cai-ki/superpowers`
- `docs/orchestration/specs/`: design documents for skills
- `docs/orchestration/research/`: persisted research reports and context packs

## Skill Index

| Skill | Purpose | Status | Key Files |
| --- | --- | --- | --- |
| `context-research-orchestrator` | Evidence-driven codebase research and context packaging for complex tasks, with optional read-only exploration subagents and reusable source-bound outputs | Active | `context-research-orchestrator/SKILL.md`, `context-research-orchestrator/references/output-templates.md`, `context-research-orchestrator/references/delegation-guidance.md`, `context-research-orchestrator/pressure-scenarios.md` |
| `deepresearch` | User-facing codebase research skill that produces a layered Markdown report with embedded Mermaid diagrams, from shallow project overview to deep module analysis, using parallel subagents and persistent multi-round state | Active | `deepresearch/SKILL.md`, `deepresearch/agents/exploration-agent.md`, `deepresearch/references/subagent-scaling.md`, `deepresearch/references/plan-template.md`, `deepresearch/references/output-document-template.md` |
| `semantic-batch-refactor-orchestrator` | Specification-first orchestration for large semantic batch refactors with safe multi-subagent execution, source-bound task context, feedback-driven rule updates, and formal handoff from `context-research-orchestrator` when repository understanding is still shallow | Active | `semantic-batch-refactor-orchestrator/SKILL.md`, `semantic-batch-refactor-orchestrator/pressure-scenarios.md` |

## Current Skills

### `context-research-orchestrator`

Use this skill when a task needs grounded project research before planning, rule freezing, or subagent orchestration, and the output should be reusable as a `Research Report` plus `Context Pack`.

Main files:

- `context-research-orchestrator/SKILL.md`
- `context-research-orchestrator/references/output-templates.md`
- `context-research-orchestrator/references/delegation-guidance.md`
- `context-research-orchestrator/pressure-scenarios.md`
- `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`

Related docs:

- Design spec: `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`

### `deepresearch`

User-facing codebase research skill. Produces a single Markdown document with
embedded Mermaid diagrams, layered from shallow project overview to deep module
analysis. Uses parallel subagents and persistent multi-round state so large
codebases can be researched safely across context resets.

**Key files:**
- `deepresearch/SKILL.md`
- `deepresearch/agents/exploration-agent.md`
- `deepresearch/references/subagent-scaling.md`
- `deepresearch/references/plan-template.md`
- `deepresearch/references/output-document-template.md`
- `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md`

**Depth modes:** `quick` | `standard` | `deep`

**Design spec:** `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md`

### `semantic-batch-refactor-orchestrator`

Use this skill when a large semantic codebase change needs careful requirement convergence, safe consumption of repository research, read-only exploration, task-local context packets, and controlled multi-subagent execution.

Main files:

- `semantic-batch-refactor-orchestrator/SKILL.md`
- `semantic-batch-refactor-orchestrator/pressure-scenarios.md`
- `docs/orchestration/specs/2026-03-18-semantic-batch-refactor-orchestrator-design.md`

Related docs:

- Design spec: `docs/orchestration/specs/2026-03-18-semantic-batch-refactor-orchestrator-design.md`
- Validation scenarios: `semantic-batch-refactor-orchestrator/pressure-scenarios.md`

## Adding New Skills

Recommended pattern:

1. Write a design spec in `docs/orchestration/specs/`
2. Persist reusable research artifacts in `docs/orchestration/research/` when the task warrants it
3. Create a new top-level skill directory with `SKILL.md`
4. Add any focused validation or reference files next to the skill
5. Update this README with the new skill entry

## Maintenance Notes

- Run `git submodule update --init --recursive` after cloning this repository.
- Keep the `Skill Index` table updated when adding or renaming skills.
- Prefer one top-level directory per skill.
- Store orchestration design and research documents under `docs/orchestration/` so they stay easy to browse.
- Resolve `docs/orchestration/` paths relative to the current repository root. If the workspace is not a git repository, resolve them relative to the current working directory unless the user explicitly chooses another location.
