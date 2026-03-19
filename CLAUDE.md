# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of reusable Claude Code skills for orchestrating complex agentic workflows. All skill content is Markdown — there is no application code, build system, or test suite.

After cloning:
```bash
git submodule update --init --recursive
```

## Converting deepresearch Output to PDF/DOCX

```bash
python deepresearch/scripts/convert.py <report.md>                        # both formats
python deepresearch/scripts/convert.py <report.md> --format pdf
python deepresearch/scripts/convert.py <report.md> --format both --out-dir exports/
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
- `read-only-exploration-agent.md` — gathers source-bound findings, never edits files, classifies claims as `Fact` / `Inference` / `Open Question`
- `implementation-agent.md` — executes within a frozen rule set, escalates scope conflicts
- `spec-conformance-reviewer.md` — compares delivered work against a spec, returns Conformant / Partially Conformant / Non-Conformant

The `Fact` / `Inference` / `Open Question` / `Decision Blocker` certainty labels are used consistently across all skills and all agent roles.

## Skills and Their Relationships

| Skill | Output consumer | When to use |
|-------|----------------|-------------|
| `context-research-orchestrator` | Downstream agents | Before planning, rule-freezing, or orchestration — produces `Research Report` + `Context Pack` with provenance and citations |
| `deepresearch` | Human user | When a user wants a readable layered report with Mermaid diagrams; accepts `depth: quick / standard / deep` |
| `semantic-batch-refactor-orchestrator` | Downstream agents + user | Large semantic code changes; rules must be frozen before execution; optionally consumes CRO output as upstream research |

**CRO → SBRO**: `context-research-orchestrator` is the intended upstream precursor to `semantic-batch-refactor-orchestrator` when repository context is shallow.

**deepresearch vs CRO**: Both research codebases but serve different consumers. Use `deepresearch` when the output is a document for a human to read; use `context-research-orchestrator` when the output feeds downstream agents.

## Skill Directory Structure

Each skill follows this layout:

```
<skill>/
├── SKILL.md                  # entry point: workflow, phases, rules
├── agents/                   # skill-local role contract copies (for portability)
├── references/               # reference files loaded by SKILL.md as needed
├── scripts/                  # supporting scripts (e.g., deepresearch/scripts/convert.py)
└── pressure-scenarios.md     # adversarial validation scenarios (where present)
```

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
| `docs/orchestration/plans/` | Step-by-step implementation plans |
| `docs/orchestration/research/` | Persisted CRO research reports and context packs |
| `docs/deepresearch/` | deepresearch session state and output |

## Adding a New Skill

1. Write a design spec → `docs/orchestration/specs/YYYY-MM-DD-<name>-design.md`
2. Write an implementation plan → `docs/orchestration/plans/YYYY-MM-DD-<name>.md`
3. Create `<skill>/SKILL.md` and supporting files
4. Update the `README.md` skill index table
