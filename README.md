# Skills

This repository stores reusable local agent skills and their supporting documents.

## Repository Layout

- `semantic-batch-refactor-orchestrator/`: the skill itself and its validation scenarios
- `docs/superpowers/specs/`: design documents for skills
- `docs/superpowers/plans/`: implementation plans for skills

## Current Skills

### `semantic-batch-refactor-orchestrator`

Use this skill when a large semantic codebase change needs careful requirement convergence, read-only exploration, safe task partitioning, and controlled multi-subagent execution.

Main files:

- `semantic-batch-refactor-orchestrator/SKILL.md`
- `semantic-batch-refactor-orchestrator/pressure-scenarios.md`
- `docs/superpowers/specs/2026-03-18-semantic-batch-refactor-orchestrator-design.md`
- `docs/superpowers/plans/2026-03-18-semantic-batch-refactor-orchestrator.md`

## Adding New Skills

Recommended pattern:

1. Write a design spec in `docs/superpowers/specs/`
2. Write an implementation plan in `docs/superpowers/plans/`
3. Create a new top-level skill directory with `SKILL.md`
4. Add any focused validation or reference files next to the skill
5. Update this README with the new skill entry
