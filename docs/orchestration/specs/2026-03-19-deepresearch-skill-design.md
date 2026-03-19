# DeepResearch Skill — Design Spec

**Date:** 2026-03-19
**Status:** Draft

---

## Overview

`deepresearch` is a codebase research skill that produces a single, user-facing Markdown document with embedded Mermaid diagrams. Unlike `context-research-orchestrator` (which packages context for downstream agents), this skill's output is designed to be read directly by the user.

The output is layered "from shallow to deep": visual structure first, then execution flows, then detailed module analysis, then architectural insights.

---

## Scope and Non-Goals

**In scope:**
- Codebase research (current repository)
- Generating a structured Markdown report with Mermaid diagrams
- Three depth modes: `quick`, `standard`, `deep`
- Multi-round execution with persistent state (context-length safe)
- Dynamic subagent count based on codebase size

**Out of scope:**
- General-purpose topic research (web search, non-code domains)
- Real-time interactive exploration
- Automatic conversion to PDF/DOCX (can be done separately via pdf/docx skills)

---

## Architecture

### High-Level Flow

```
deepresearch skill
│
├── 1. Intake
│      Accept: depth (quick | standard | deep), target repo path
│
├── 2. Light Probe
│      Estimate codebase size (file count, top-level structure)
│      Determine sharding strategy
│      Write state/plan.md
│
├── 3. Parallel Research (subagents)
│      Dispatch N subagents based on size × depth
│      Each subagent writes to state/chunks/chunk-NN.md
│
├── 4. Synthesis
│      Main agent reads completed chunks (in batches if needed)
│      Writes state/synthesis.md
│
└── 5. Document Generation
       Reads synthesis.md
       Writes output/YYYY-MM-DD-<repo>-research.md
```

### Persistent State Directory

```
docs/deepresearch/<repo-name>-<YYYY-MM-DD>/
├── state/
│   ├── plan.md            ← research plan + progress (main agent's anchor)
│   ├── chunks/
│   │   ├── chunk-01.md   ← subagent research results
│   │   ├── chunk-02.md
│   │   └── ...
│   └── synthesis.md       ← intermediate merged summary
└── output/
    └── research.md        ← final deliverable
```

---

## Dynamic Subagent Scaling

After the Light Probe, the main agent estimates codebase size and selects a subagent count:

| Size | Files | quick | standard | deep |
|------|-------|-------|----------|------|
| Small | < 50 | 1 | 2 | 3 |
| Medium | 50–300 | 2 | 4 | 6 |
| Large | > 300 | 3 | 6 | per-domain (≤ 50 files/agent) |

**Sharding principles:**
- Prefer functional domain splits (`src/api/`, `src/core/`, `src/ui/`) over equal file-count splits
- Each subagent receives only its shard's file list — never the full codebase
- Subagent output format is standardized: Mermaid diagram(s) + summary text

---

## Multi-Round Execution Model

`plan.md` is the main agent's persistent anchor across context resets:

```markdown
# Research Plan
status: in_progress

## Phase
current: synthesis

## Chunks
- [x] chunk-01.md
- [x] chunk-02.md
- [ ] chunk-03.md

## Synthesis
- [x] chunks 01-02 merged into synthesis.md
- [ ] chunk-03 pending

## Notes
<reason for stopping, if context limit was reached>
```

**Main agent startup logic (every round):**

```
Read plan.md
  ├── Not started?            → Light Probe → write plan.md → dispatch subagents
  ├── Chunks incomplete?      → re-dispatch missing subagent(s)
  ├── All chunks done,        → read chunks in batches → write synthesis.md
  │   synthesis pending?
  └── Synthesis done,         → read synthesis.md → write output/research.md
      output pending?
```

The main agent updates `plan.md` at the end of each phase before proceeding. Any interruption leaves a recoverable state.

---

## Output Document Structure

```markdown
# [Project Name] — Deep Research Report
> Generated: YYYY-MM-DD | Mode: quick/standard/deep | Commit: abc1234

---

## 1. Project Overview  [all modes]
One paragraph: what this project is and does.

### Directory Structure
[Mermaid graph]

### Module Dependency Map
[Mermaid graph LR]

---

## 2. Core Flows  [all modes; quick = main flow only]

### Primary Request Chain
[Mermaid sequenceDiagram]

### Data Flow
[Mermaid flowchart LR]

---

## 3. Module Deep-Dive  [standard: key modules; deep: full]

### Module A: [Name]
- Responsibility: ...
- Key files: `src/core/xxx.ts:42`
- Public interface: ...
- Internal logic notes: ...

---

## 4. Design Insights  [standard + deep only]
- Observed architectural patterns
- Trade-offs and coupling risks
- Git history notes  [deep only]

---

## Appendix
- Coverage: directories and files analyzed
- Exclusions: what was skipped and why
- Confidence markers: Fact / Inference / Open Question
```

### Mode Coverage Matrix

| Section | quick | standard | deep |
|---------|-------|----------|------|
| 1. Overview | ✓ | ✓ | ✓ |
| 2. Core Flows | main flow | ✓ | ✓ |
| 3. Module Deep-Dive | — | key modules | all modules |
| 4. Design Insights | — | ✓ | ✓ + git history |
| Appendix | ✓ | ✓ | ✓ |

---

## Subagent Contract

Each subagent receives a dispatch packet with:

```markdown
Role: read-only-exploration-agent
Shard: [list of directories/files to analyze]
Depth: quick | standard | deep
Output file: state/chunks/chunk-NN.md

Required output sections:
1. Mermaid diagram (structure or flow, as appropriate)
2. Module/file summaries (one paragraph each)
3. Key findings tagged as: Fact | Inference | Open Question
```

Subagents are **read-only** — they may not edit any project files.

---

## Skill Integration

- Uses `dispatching-parallel-agents` skill for subagent dispatch
- Output `.md` can be converted to PDF via `pdf` skill or DOCX via `docx` skill on demand
- `context-research-orchestrator` remains the preferred skill when the output is intended for downstream agents rather than users

---

## Open Questions

- Should `plan.md` support a `paused` status for long deep-mode runs across multiple sessions?
- Should the skill emit a brief "executive summary" block at the very top for quick-mode runs, before the full document structure?
