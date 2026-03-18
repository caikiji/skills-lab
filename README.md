# Skills

This repository stores reusable local agent skills and their supporting documents.

## Repository Layout

- `semantic-batch-refactor-orchestrator/`: the skill itself and its validation scenarios
- `superpowers/`: git submodule dependency from `https://github.com/Cai-ki/superpowers`
- `docs/superpowers/specs/`: design documents for skills
- `docs/superpowers/plans/`: implementation plans for skills

## Skill Index

| Skill | Purpose | Status | Key Files |
| --- | --- | --- | --- |
| `semantic-batch-refactor-orchestrator` | Specification-first orchestration for large semantic batch refactors with safe multi-subagent execution, source-bound task context, and feedback-driven rule updates | Active | `semantic-batch-refactor-orchestrator/SKILL.md`, `semantic-batch-refactor-orchestrator/pressure-scenarios.md` |

## Current Skills

### `semantic-batch-refactor-orchestrator`

Use this skill when a large semantic codebase change needs careful requirement convergence, read-only exploration, safe task partitioning, and controlled multi-subagent execution.

Main files:

- `semantic-batch-refactor-orchestrator/SKILL.md`
- `semantic-batch-refactor-orchestrator/pressure-scenarios.md`
- `docs/superpowers/specs/2026-03-18-semantic-batch-refactor-orchestrator-design.md`
- `docs/superpowers/plans/2026-03-18-semantic-batch-refactor-orchestrator.md`

Related docs:

- Design spec: `docs/superpowers/specs/2026-03-18-semantic-batch-refactor-orchestrator-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-18-semantic-batch-refactor-orchestrator.md`
- Validation scenarios: `semantic-batch-refactor-orchestrator/pressure-scenarios.md`

## Adding New Skills

Recommended pattern:

1. Write a design spec in `docs/superpowers/specs/`
2. Write an implementation plan in `docs/superpowers/plans/`
3. Create a new top-level skill directory with `SKILL.md`
4. Add any focused validation or reference files next to the skill
5. Update this README with the new skill entry

## Maintenance Notes

- Run `git submodule update --init --recursive` after cloning this repository.
- Keep the `Skill Index` table updated when adding or renaming skills.
- Prefer one top-level directory per skill.
- Store design and plan documents under `docs/superpowers/` so they stay easy to browse.
