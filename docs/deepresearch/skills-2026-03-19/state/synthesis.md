# Synthesis — skills repo (quick mode)

## What This Repo Is

A collection of Claude Code skills for orchestrating complex agentic workflows. Three active skills, a shared agent role library, and a docs structure that separates design specs from implementation plans.

## Skill Inventory

| Skill | Consumer | Purpose |
|-------|----------|---------|
| `context-research-orchestrator` | Downstream agents | Build trustworthy project context before planning/execution; outputs Research Report + Context Pack |
| `deepresearch` | Human user | Produce a layered codebase research Markdown document with Mermaid diagrams |
| `semantic-batch-refactor-orchestrator` | Downstream agents + user | Orchestrate large semantic code changes with frozen rules and parallel implementation |

## Architecture: Three-Layer Agent System

All skills share the same foundational pattern:

```
Role Contract (agents/*.md)
  + Task Packet (assembled per dispatch)
  + Skill (SKILL.md workflow)
= Child Agent
```

Three shared roles: `read-only-exploration-agent`, `implementation-agent`, `spec-conformance-reviewer`.

## Skill Relationships

- **CRO → SBRO**: CRO is the required upstream precursor to SBRO when repo context is too shallow to freeze rules safely.
- **deepresearch vs CRO**: Both research codebases but for different consumers. deepresearch → user. CRO → downstream agents.
- **SBRO uses all three roles**; CRO uses only exploration; deepresearch uses a specialized exploration variant.

## Key Cross-Cutting Conventions

1. Certainty labels: `Fact` / `Inference` / `Open Question` / `Decision Blocker` — used by all skills and all agent roles
2. Persistent state under `docs/` for long-running or resumable workflows
3. Local role-contract copies in skill subdirectories for portability (maintenance risk: may drift from shared originals)
4. Design specs → `docs/orchestration/specs/`, implementation plans → `docs/orchestration/plans/`

## Notable Gaps

- `dispatching-parallel-agents` skill is referenced by `deepresearch` Phase 3 but not present in this repo (lives in `superpowers/` submodule — unconfirmed)
- `docs/orchestration/research/` is empty — no CRO persisted artifacts yet
- Two open design questions in deepresearch: `paused` status support; executive summary block for quick mode
