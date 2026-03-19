# DeepResearch Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `deepresearch` skill so agents can perform structured codebase research and produce a single user-facing Markdown document with embedded Mermaid diagrams, layered from shallow overview to deep module analysis, using parallel subagents and persistent multi-round state.

**Architecture:** The skill centers on a `SKILL.md` that encodes the five-phase workflow (Intake → Light Probe → Parallel Research → Synthesis → Document Generation), with persistent `plan.md` state enabling safe resumption across context resets. Three reference files carry the subagent scaling table, `plan.md` template, and output document template to keep `SKILL.md` focused and readable.

**Tech Stack:** Markdown skill files, Mermaid diagram syntax, `docs/orchestration/` for docs

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `deepresearch/SKILL.md` | Core workflow: intake, resume logic, light probe, dispatch, synthesis, doc generation |
| Create | `deepresearch/agents/exploration-agent.md` | Subagent role contract: read-only, chunk output format, dispatch packet fields |
| Create | `deepresearch/references/subagent-scaling.md` | Size table, sharding principles, subagent count ceiling |
| Create | `deepresearch/references/plan-template.md` | Template for `state/plan.md` including all status fields and resume logic |
| Create | `deepresearch/references/output-document-template.md` | Final document structure with mode coverage matrix |
| Modify | `README.md` | Add `deepresearch` to skill table and add skill section |

---

### Task 1: Scaffold the Skill Directory

**Files:**
- Create: `deepresearch/SKILL.md` (placeholder)
- Create: `deepresearch/agents/exploration-agent.md` (placeholder)
- Create: `deepresearch/references/subagent-scaling.md` (placeholder)
- Create: `deepresearch/references/plan-template.md` (placeholder)
- Create: `deepresearch/references/output-document-template.md` (placeholder)

- [ ] **Step 1: Confirm the design spec is present and readable**

Read: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md`
Expected: File loads, contains Architecture, Dynamic Subagent Scaling, Multi-Round Execution Model, Output Document Structure, and Subagent Contract sections.

- [ ] **Step 2: Create the directory structure**

Create directories:
- `deepresearch/`
- `deepresearch/agents/`
- `deepresearch/references/`

Expected: Directory tree exists under the repo root.

- [ ] **Step 3: Create placeholder files with final filenames**

Create the following files each with a single placeholder line `# TODO`:
- `deepresearch/SKILL.md`
- `deepresearch/agents/exploration-agent.md`
- `deepresearch/references/subagent-scaling.md`
- `deepresearch/references/plan-template.md`
- `deepresearch/references/output-document-template.md`

Expected: All five files exist. No file will need renaming later.

- [ ] **Step 4: Commit scaffolding**

```bash
git add deepresearch/
git commit -m "chore: scaffold deepresearch skill directory"
```

---

### Task 2: Write the Exploration Agent Contract

**Files:**
- Modify: `deepresearch/agents/exploration-agent.md`
- Reference: `context-research-orchestrator/agents/read-only-exploration-agent.md` (pattern)
- Reference: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md` (Subagent Contract section)

- [ ] **Step 1: Read the base role contract for reference**

Read: `context-research-orchestrator/agents/read-only-exploration-agent.md`
Expected: Understand the standard fields — Role, Objective, Search Area, Must-Read Sources, Output Contract, Stop Conditions, Authority Rule.

- [ ] **Step 2: Write the exploration agent contract**

Write `deepresearch/agents/exploration-agent.md` with the following content:

```markdown
# DeepResearch Exploration Agent

You are a read-only exploration child agent dispatched by the `deepresearch` skill.

Your job is to analyze the shard of the codebase assigned to you, produce Mermaid
diagrams and structured summaries, and write your findings to the output file
specified in your dispatch packet. You do not modify project files.

## Allowed Actions

- Read code, config, tests, and docs within your assigned shard
- Search for symbols, entry points, dependencies, and call sites
- Produce Mermaid diagrams (graph, flowchart, sequenceDiagram)
- Summarize each file or module in one paragraph
- Tag findings as `Fact`, `Inference`, or `Open Question`

## Forbidden Actions

- Edit any project file
- Read files outside your assigned shard (unless critical cross-references require it — note these explicitly)
- Invent relationships not evidenced in source
- Silently expand scope

## Authority Rule

When summaries, comments, or conventions conflict with current source evidence,
trust current source evidence. If evidence conflicts internally, stop and report
the conflict rather than picking a side.

## Dispatch Packet Fields (Required)

Expect the primary agent to provide all of the following:

| Field | Description |
|-------|-------------|
| `Role` | `read-only-exploration-agent` |
| `Objective` | What this shard analysis must answer |
| `Shard` | The list of directories/files to analyze |
| `Depth` | `quick` / `standard` / `deep` |
| `Must-Read Sources` | Entry points, key files to start from |
| `Output Contract` | Path to write chunk output (`state/chunks/chunk-NN.md`) |
| `Stop Conditions` | When to stop and report rather than continue |

If any required field is missing in a way that blocks safe work, report the gap and
return the strongest partial findings you can.

## Required Output Format

Write findings to the path given in `Output Contract`. Use this structure:

```markdown
# Chunk NN — [Shard Name]

## Diagram
[Mermaid block: graph or flowchart for structure; sequenceDiagram for flows]

## Module Summaries
### [File or Module Name]
- Responsibility: ...
- Key entry points: `path/to/file.ts:line`
- Dependencies: ...

## Key Findings
- [Fact] ...
- [Inference] ...
- [Open Question] ...

## Coverage
- Analyzed: [list of files/dirs covered]
- Skipped: [list + reason]
```

## Stop and Report When

- The shard contains files you cannot read
- Critical context lies entirely outside your shard
- Evidence conflicts and you cannot resolve it from source
- The task requires business judgment
```

- [ ] **Step 3: Verify the file reads as intended**

Read: `deepresearch/agents/exploration-agent.md`
Expected: All sections present, dispatch packet table complete, output format block is clear.

- [ ] **Step 4: Commit**

```bash
git add deepresearch/agents/exploration-agent.md
git commit -m "feat: add deepresearch exploration agent contract"
```

---

### Task 3: Write the Subagent Scaling Reference

**Files:**
- Modify: `deepresearch/references/subagent-scaling.md`
- Reference: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md` (Dynamic Subagent Scaling section)

- [ ] **Step 1: Write the subagent scaling reference**

Write `deepresearch/references/subagent-scaling.md` with the following content:

```markdown
# Subagent Scaling Reference

Use this reference during the Light Probe phase to determine how many
subagents to dispatch and how to shard the codebase.

## Step 1: Estimate Codebase Size

Count source files (exclude `node_modules`, `vendor`, `.git`, build output).
Classify as Small, Medium, or Large.

| Size | File Count |
|------|-----------|
| Small | < 50 |
| Medium | 50–300 |
| Large | > 300 |

## Step 2: Select Subagent Count

| Size | quick | standard | deep |
|------|-------|----------|------|
| Small | 1 | 2 | 3 |
| Medium | 2 | 4 | 6 |
| Large | 3 | 6 | see ceiling rule |

### Deep Mode Ceiling (Large codebases)

In deep mode for large codebases, shard by functional domain with at most
50 files per shard. Cap total subagent count at **12** regardless of
codebase size. If the codebase has more domains than the cap allows,
merge smaller domains and note which ones were combined in `plan.md`.

## Step 3: Define Shards

**Shard by functional domain, not by file count.**

Priority order:
1. Top-level source directories (`src/api/`, `src/core/`, `src/ui/`, etc.)
2. Feature modules when the source tree is flat
3. File-count-based splits only as a last resort

Each shard must:
- Contain at most 50 files (deep mode) or 100 files (quick/standard)
- Have a clear label (e.g., `api-layer`, `core-engine`, `ui-components`)
- Be given to exactly one subagent

## Step 4: Assign Objectives

| Shard Type | Objective |
|-----------|-----------|
| Entry-point shard | Map top-level structure and primary request chains |
| Domain shard | Map module responsibilities, dependencies, and key call paths |
| Config/infra shard | Map build pipeline, environment config, deployment artifacts |

Always give each subagent a `Must-Read Sources` list: the 2–5 files most
likely to be entry points for its shard.
```

- [ ] **Step 2: Verify file is readable and the ceiling rule is explicit**

Read: `deepresearch/references/subagent-scaling.md`
Expected: File loads, ceiling of 12 is present, sharding steps 1–4 are clear.

- [ ] **Step 3: Commit**

```bash
git add deepresearch/references/subagent-scaling.md
git commit -m "feat: add deepresearch subagent scaling reference"
```

---

### Task 4: Write the Plan Template Reference

**Files:**
- Modify: `deepresearch/references/plan-template.md`
- Reference: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md` (Multi-Round Execution Model section)

- [ ] **Step 1: Write the plan template reference**

Write `deepresearch/references/plan-template.md` with the following content:

```markdown
# plan.md Template

This file is the main agent's persistent anchor. Write it at the end of the
Light Probe phase and update it at the end of every subsequent phase.

## Template

```markdown
# DeepResearch — Research Plan
status: in_progress
depth: quick | standard | deep
repo: <repo-name>
started: YYYY-MM-DD

## Phase
current: light-probe | dispatching | researching | synthesis | generating | done

## Shard Map
- chunk-01: <shard-label> (<file-count> files)
- chunk-02: <shard-label> (<file-count> files)
...

## Chunks
- [ ] chunk-01.md
- [ ] chunk-02.md
...

## Synthesis
- [ ] synthesis.md

## Output
- [ ] output/YYYY-MM-DD-<repo>-research.md

## Notes
<Record stop reason if context limit was reached, or any anomalies.>
```

## Resume Logic

When the main agent starts (or restarts), read `plan.md` first:

| `current` phase | `plan.md` exists? | Action |
|----------------|-------------------|--------|
| — | No | Run Light Probe → write `plan.md` |
| `light-probe` | Yes, probe incomplete | Re-run Light Probe from scratch → overwrite `plan.md` |
| `dispatching` or `researching` | Yes, chunks incomplete | Re-dispatch missing chunk subagents |
| `synthesis` | Yes, all chunks done | Read chunks in batches → write `synthesis.md` |
| `generating` | Yes, synthesis done | Read `synthesis.md` → write `output/YYYY-MM-DD-<repo>-research.md` |
| `done` | Yes | Report that research is already complete |

## Batch Synthesis Rule

If the number of completed chunks is large (> 4), read chunks in batches of 3.
Write an intermediate partial synthesis per batch, then merge all partial
syntheses into the final `synthesis.md`. Record batch boundaries in `plan.md`.
```

- [ ] **Step 2: Verify the resume logic table covers all states**

Read: `deepresearch/references/plan-template.md`
Expected: Every possible value in the `current` field has a corresponding row in the resume logic table, including `light-probe`.

- [ ] **Step 3: Commit**

```bash
git add deepresearch/references/plan-template.md
git commit -m "feat: add deepresearch plan template reference"
```

---

### Task 5: Write the Output Document Template Reference

**Files:**
- Modify: `deepresearch/references/output-document-template.md`
- Reference: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md` (Output Document Structure section)

- [ ] **Step 1: Write the output document template**

Write `deepresearch/references/output-document-template.md` with the following content:

```markdown
# Output Document Template

The final document is written to `output/YYYY-MM-DD-<repo>-research.md` inside the state directory.

## Mode Coverage

| Section | quick | standard | deep |
|---------|-------|----------|------|
| 1. Project Overview | ✓ | ✓ | ✓ |
| 2. Core Flows | main flow only | ✓ | ✓ |
| 3. Module Deep-Dive | — | key modules | all modules |
| 4. Design Insights | — | ✓ | ✓ + git history |
| Appendix | ✓ | ✓ | ✓ |

## Document Template

```markdown
# [Project Name] — Deep Research Report
> Generated: YYYY-MM-DD | Mode: quick/standard/deep | Commit: <git-sha>

---

## 1. Project Overview

[One paragraph: what this project is and what it does.]

### Directory Structure

\```mermaid
graph TD
  root --> src
  root --> tests
  src --> ...
\```

### Module Dependency Map

\```mermaid
graph LR
  moduleA --> moduleB
  moduleB --> moduleC
\```

---

## 2. Core Flows

### Primary Request Chain

\```mermaid
sequenceDiagram
  Client->>Entry: request
  Entry->>Core: process
  Core->>Storage: query
\```

### Data Flow
[standard + deep only]

\```mermaid
flowchart LR
  Input --> Validate --> Transform --> Persist
\```

---

## 3. Module Deep-Dive
[standard: key modules only; deep: all modules; omit entirely for quick]

### [Module Name]
- **Responsibility:** ...
- **Key files:** `path/to/file.ts:line`
- **Public interface:** ...
- **Internal logic notes:** ...

---

## 4. Design Insights
[standard + deep only; omit for quick]

- **Observed patterns:** ...
- **Trade-offs and coupling risks:** ...
- **Git history notes:** [deep only] ...

---

## Appendix

### Coverage
- Analyzed: [list of directories/files]

### Exclusions
- [path]: [reason skipped]

### Confidence Markers
- [Fact]: ...
- [Inference]: ...
- [Open Question]: ...
```

## Mermaid Diagram Guidance

- **Directory Structure**: use `graph TD` (top-down tree)
- **Module Dependencies**: use `graph LR` (left-right, shows import/call direction)
- **Request Chains**: use `sequenceDiagram`
- **Data Flows**: use `flowchart LR`
- Keep each diagram to ≤ 15 nodes. If a diagram would exceed this, split into sub-diagrams with a title for each.
```

- [ ] **Step 2: Verify the mode coverage table and diagram guidance are present**

Read: `deepresearch/references/output-document-template.md`
Expected: Mode coverage table shows all 5 sections, Mermaid guidance block is present.

- [ ] **Step 3: Commit**

```bash
git add deepresearch/references/output-document-template.md
git commit -m "feat: add deepresearch output document template"
```

---

### Task 6: Write the Core SKILL.md

**Files:**
- Modify: `deepresearch/SKILL.md`
- Reference: `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md`
- Reference: `deepresearch/references/subagent-scaling.md`
- Reference: `deepresearch/references/plan-template.md`
- Reference: `deepresearch/references/output-document-template.md`
- Reference: `deepresearch/agents/exploration-agent.md`

- [ ] **Step 1: Read all reference files to confirm they are complete before writing SKILL.md**

Read the following files in sequence:
- `deepresearch/references/subagent-scaling.md`
- `deepresearch/references/plan-template.md`
- `deepresearch/references/output-document-template.md`
- `deepresearch/agents/exploration-agent.md`

Expected: All four files load without errors and contain substantive content.

- [ ] **Step 2: Write the core SKILL.md**

Write `deepresearch/SKILL.md` with the following content:

```markdown
---
name: deepresearch
description: User-facing codebase research skill. Produces a single Markdown document
  with embedded Mermaid diagrams, layered from shallow overview to deep module analysis.
  Use when the user asks to deeply understand a codebase, generate a project research
  report, or produce a visual + textual map of how a repository works.
  Accepts a depth parameter: quick, standard, or deep.
---

# DeepResearch

Produce a layered codebase research document for the user. The output is designed
to be read directly — not to package context for downstream agents. For agent-context
packaging, use `context-research-orchestrator` instead.

## Phase 0: Intake

Accept:
- `depth`: `quick` | `standard` | `deep` (default: `standard`)
- `target`: path to the repository root (default: current working directory)

Determine the state directory path:
```
docs/deepresearch/<repo-name>-<YYYY-MM-DD>/
```

## Phase 1: Resume Check

Before doing any research, check whether `state/plan.md` already exists inside the
state directory.

Read [references/plan-template.md](references/plan-template.md) for the resume
logic table. Follow it exactly:

- If `plan.md` does not exist → proceed to Phase 2 (Light Probe)
- If `plan.md` exists → skip to whichever phase is indicated by `current`

## Phase 2: Light Probe

Perform the minimum scan needed to estimate codebase size and define shards:

1. Count source files (exclude `node_modules`, `vendor`, `.git`, build output)
2. List top-level directories
3. Identify obvious functional domains from directory names

Read [references/subagent-scaling.md](references/subagent-scaling.md) to select
subagent count and define shards.

Write `state/plan.md` using the template in [references/plan-template.md](references/plan-template.md).
Set `current: dispatching`.

Create `state/chunks/` directory.

## Phase 3: Parallel Research

Dispatch subagents in parallel using the `dispatching-parallel-agents` skill.

For each shard, construct a dispatch packet with all required fields (see
[agents/exploration-agent.md](agents/exploration-agent.md)):

| Field | Value |
|-------|-------|
| `Role` | `read-only-exploration-agent` |
| `Objective` | Analyze this shard: map structure, key modules, and flows |
| `Shard` | List of directories/files for this shard |
| `Depth` | The depth parameter from Phase 0 |
| `Must-Read Sources` | 2–5 likely entry-point files in the shard |
| `Output Contract` | `state/chunks/chunk-NN.md` (absolute path) |
| `Stop Conditions` | Report if shard requires context outside its boundaries |

After dispatch, update `plan.md`: set `current: researching`.

As chunks complete, mark them in `plan.md`. If a chunk fails or is missing,
re-dispatch that subagent before proceeding.

## Phase 4: Synthesis

When all chunks are marked complete in `plan.md`:

If chunks ≤ 4: read all chunks and write `state/synthesis.md` in one pass.

If chunks > 4: process in batches of 3 (see batch synthesis rule in
[references/plan-template.md](references/plan-template.md)). Write one partial
synthesis per batch, then merge into `state/synthesis.md`.

Update `plan.md`: mark synthesis complete, set `current: generating`.

**Context limit rule:** If synthesizing all chunks would exceed your context
window, write whatever partial synthesis you have completed to `synthesis.md`,
note the stopping point in `plan.md` under `Notes`, and stop. The next round
will resume from this point.

## Phase 5: Document Generation

Read `state/synthesis.md`. Generate the final document following the template
and mode coverage matrix in [references/output-document-template.md](references/output-document-template.md).

Write to: `output/YYYY-MM-DD-<repo>-research.md` (relative to the state directory).

Update `plan.md`: mark output complete, set `current: done`.

## Completion

Report the output path to the user. Mention that the document can be converted
to PDF or DOCX using the `pdf` or `docx` skills if needed.

## Non-Goals

Do not:
- modify any project files during research
- use this skill when the output is for downstream agents (use `context-research-orchestrator`)
- attempt to complete Phase 3–5 in one context window for large/deep runs — let the state system do its job
```

- [ ] **Step 3: Verify the SKILL.md is coherent**

Read: `deepresearch/SKILL.md`
Expected:
- Frontmatter `name` and `description` are present
- All 6 phases are present (Intake, Resume Check, Light Probe, Parallel Research, Synthesis, Document Generation)
- All three reference files are linked
- Context limit rule is present in Phase 4
- Non-goals section is present

- [ ] **Step 4: Commit**

```bash
git add deepresearch/SKILL.md
git commit -m "feat: write deepresearch core SKILL.md"
```

---

### Task 7: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README to understand its structure**

Read: `README.md`
Expected: There is a skill table and per-skill sections. Note the exact format used for existing entries (e.g., `context-research-orchestrator`).

- [ ] **Step 2: Add deepresearch to the skill table**

In the skills table, add a new row after the `context-research-orchestrator` row:

```markdown
| `deepresearch` | User-facing codebase research skill that produces a layered Markdown report with embedded Mermaid diagrams, from shallow project overview to deep module analysis, using parallel subagents and persistent multi-round state | Active | `deepresearch/SKILL.md`, `deepresearch/agents/exploration-agent.md`, `deepresearch/references/subagent-scaling.md`, `deepresearch/references/plan-template.md`, `deepresearch/references/output-document-template.md` |
```

- [ ] **Step 3: Add a deepresearch skill section**

After the `context-research-orchestrator` section, add:

```markdown
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
- `docs/orchestration/plans/2026-03-19-deepresearch-skill.md`

**Depth modes:** `quick` | `standard` | `deep`

**Design spec:** `docs/orchestration/specs/2026-03-19-deepresearch-skill-design.md`
**Implementation plan:** `docs/orchestration/plans/2026-03-19-deepresearch-skill.md`
```

- [ ] **Step 4: Verify the README changes**

Read: `README.md`
Expected: `deepresearch` appears in the skill table and has its own section with all key files listed.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add deepresearch skill to README"
```

---

### Task 8: Final Coherence Check

**Files:**
- Read: all `deepresearch/` files

- [ ] **Step 1: Cross-check all internal references**

For each file path linked in `SKILL.md` (the three `references/` files and the `agents/` file), confirm the file exists and the link text matches the actual filename.

Expected: No broken references.

- [ ] **Step 2: Verify the dispatching-parallel-agents skill exists**

Check that `dispatching-parallel-agents/SKILL.md` (or equivalent) is present in the skills directory.

Expected: The skill exists. If it does not, note the gap — Phase 3 of `deepresearch/SKILL.md` references it by name and will fail at runtime without it.

- [ ] **Step 3: Verify the subagent dispatch packet contract is aligned**

Read both:
- `deepresearch/SKILL.md` (Phase 3 dispatch packet table)
- `deepresearch/agents/exploration-agent.md` (Dispatch Packet Fields section)

Expected: The fields listed in Phase 3's dispatch table exactly match the required fields listed in the agent contract. No field is present in one and absent from the other.

- [ ] **Step 4: Commit the plan document itself**

```bash
git add docs/orchestration/plans/2026-03-19-deepresearch-skill.md
git commit -m "docs: add deepresearch skill implementation plan"
```
