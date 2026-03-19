# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of reusable Claude Code skills for orchestrating complex agentic workflows. All skill content is Markdown — there is no application code, build system, or test suite.

After cloning:
```bash
git submodule update --init --recursive
```

### Two skill sets

| Location | What it contains |
|----------|-----------------|
| `skills/context-research-orchestrator/`, `skills/semantic-batch-refactor-orchestrator/`, `skills/deepresearch/` | Skills in this repo — for orchestration, research, and batch refactoring |
| `superpowers/skills/` | Git submodule (https://github.com/obra/superpowers) — general-purpose skills: TDD, debugging, brainstorming, plan writing, parallel agents, git worktrees, etc. |

Both skill sets are registered with Claude Code via the plugin manifests in `superpowers/.claude-plugin/`.

## Converting deepresearch Output to PDF/DOCX

```bash
python skills/deepresearch/scripts/convert.py <report.md>                        # both formats
python skills/deepresearch/scripts/convert.py <report.md> --format pdf
python skills/deepresearch/scripts/convert.py <report.md> --format both --out-dir exports/
```

One-time dependencies: `npm install -g @mermaid-js/mermaid-cli` and `pip install python-docx reportlab`.

## Architecture: Three-Layer Agent System

Every skill in this repo uses the same underlying pattern:

```
Role Contract  (agents/*.md or <skill>/agents/*.md)
  + Task Packet  (assembled at dispatch time by the orchestrating skill)
  + Skill        (<skill>/SKILL.md workflow)
= Child Agent
```

**Shared role contracts** live in `agents/` and are referenced (or locally copied for portability) by each skill:
- `read-only-exploration-agent.md` — gathers source-bound findings, never edits files, classifies claims as `Fact` / `Inference` / `Open Question` / `Decision Blocker`
- `implementation-agent.md` — executes within a frozen rule set, escalates scope conflicts
- `spec-conformance-reviewer.md` — compares delivered work against a spec, returns `Conformant` / `Partially Conformant` / `Non-Conformant`

The four certainty labels `Fact` / `Inference` / `Open Question` / `Decision Blocker` are used consistently across all skills and all agent roles. Never flatten an `Inference` or `Open Question` into a `Fact`.

## Skills and Their Relationships

| Skill | Output consumer | When to use |
|-------|----------------|-------------|
| `context-research-orchestrator` | Downstream agents | Before planning, rule-freezing, or orchestration — produces `Research Report` + `Context Pack` with `sbro_readiness` signal and `SBRO Handoff Block` |
| `deepresearch` | Human user | When a user wants a readable layered report with Mermaid diagrams; accepts `depth: quick / standard / deep` |
| `semantic-batch-refactor-orchestrator` | Downstream agents + user | Large semantic code changes; rules must be frozen before execution; consumes CRO `Context Pack` when one exists |

**Pipeline:**

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

**CRO → SBRO trigger conditions:**

| Situation | Action |
|-----------|--------|
| Task crosses ≥ 3 modules | Run CRO first |
| Shared files / types / event definitions not yet located | Run CRO first |
| Primary agent cannot write rules without reading source | Run CRO first |
| Task limited to 1–2 modules with clear boundaries | Inline exploration in SBRO |
| Fresh Context Pack already exists | Consume directly — skip CRO |

**deepresearch vs CRO**: Both research codebases but serve different consumers. Use `deepresearch` when the output is a document for a human to read; use `context-research-orchestrator` when the output feeds downstream agents or SBRO.

## Skill Directory Structure

Each skill follows this layout:

```
<skill>/
├── SKILL.md                  # entry point: workflow, phases, rules
├── agents/                   # skill-local role contract copies (for portability)
├── references/               # reference files loaded by SKILL.md as needed
├── scripts/                  # supporting scripts (e.g., skills/deepresearch/scripts/convert.py)
└── pressure-scenarios.md     # adversarial validation scenarios (where present)
```

### SKILL.md front-matter

Every `SKILL.md` begins with YAML front-matter that controls discovery and triggering:

```yaml
---
name: skill-name
description: One-sentence description used by Claude to decide when to invoke this skill.
---
```

The `description` field is the trigger signal — write it to match the situations where the skill should fire, not just what the skill does.

### Agent portability pattern

Shared role contracts in `agents/` are the canonical source. Each skill that dispatches subagents also keeps a local copy in `<skill>/agents/` so the skill directory can be dropped into any project and work without depending on the repo-level `agents/` directory.

**Sync rule:** When editing a canonical agent file under `agents/`, apply the same change to every `<skill>/agents/` copy of that file.

## deepresearch Persistent State

When `deepresearch` runs, it creates a resumable session under:
```
docs/deepresearch/<repo-name>-<YYYY-MM-DD>/
├── state/
│   ├── plan.md        # phase tracker and resume anchor
│   ├── chunks/        # one file per subagent shard
│   └── synthesis.md   # merged intermediate summary
└── output/
    └── YYYY-MM-DD-<repo>-research.md   # final deliverable
```

`plan.md` drives multi-round resumption — always read it first before doing any new research work.

## Documentation Layout

| Path | Contents |
|------|----------|
| `docs/orchestration/specs/` | Design specs — source of truth for skill architecture |
| `docs/deepresearch/` | deepresearch session state and output |

## Adding a New Skill

1. Write a design spec → `docs/orchestration/specs/YYYY-MM-DD-<name>-design.md`
2. Create `skills/<skill>/SKILL.md` and supporting files — one top-level directory per skill
3. Update the `README.md` skill index table
4. If the skill dispatches subagents, copy relevant canonical `agents/` contracts into `skills/<skill>/agents/`
