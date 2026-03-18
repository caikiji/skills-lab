# Context Research Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `context-research-orchestrator` skill so agents can perform evidence-driven project research, optionally coordinate read-only exploration subagents, and emit reusable research artifacts with robust citations and provenance.

**Architecture:** The implementation centers on a concise `SKILL.md` that encodes the workflow, decision rules, and output contracts, plus focused bundled references for output templates and delegation guidance. The skill should stay lightweight in core instructions while offloading reusable schemas and packet templates into reference files that can be loaded only when needed.

**Tech Stack:** Markdown skill files, repository docs under `docs/orchestration/`, optional bundled references

---

### Task 1: Scaffold The Skill Directory

**Files:**
- Create: `context-research-orchestrator/SKILL.md`
- Create: `context-research-orchestrator/references/output-templates.md`
- Create: `context-research-orchestrator/references/delegation-guidance.md`
- Modify: `README.md`

- [ ] **Step 1: Confirm the target skill shape from the approved design**

Read: `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`
Expected: Clear list of required workflow sections, artifact shapes, and reference files to create.

- [ ] **Step 2: Create the new skill directory and references directory**

Create:
- `context-research-orchestrator/`
- `context-research-orchestrator/references/`

Expected: Empty directory structure exists and matches repository conventions.

- [ ] **Step 3: Add placeholder files with the final intended filenames**

Create:
- `context-research-orchestrator/SKILL.md`
- `context-research-orchestrator/references/output-templates.md`
- `context-research-orchestrator/references/delegation-guidance.md`

Expected: Implementation can proceed file-by-file without renaming later.

- [ ] **Step 4: Update the repository index to mention the new skill**

Modify: `README.md`
Expected: Skill list mentions `context-research-orchestrator` and points to the new design and plan docs.

- [ ] **Step 5: Commit the scaffolding**

```bash
git add README.md context-research-orchestrator docs/orchestration/plans/2026-03-18-context-research-orchestrator.md docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md
git commit -m "chore: scaffold context research orchestrator skill"
```

### Task 2: Write The Core SKILL.md Workflow

**Files:**
- Modify: `context-research-orchestrator/SKILL.md`
- Reference: `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`

- [ ] **Step 1: Write the YAML frontmatter**

Add:
```yaml
---
name: context-research-orchestrator
description: Evidence-driven codebase research and context packaging for complex tasks. Use when Codex needs to deeply understand a project or task area before planning, freezing rules, coordinating subagents, or executing semantic refactors, especially when the output must include reusable summaries, source references, and freshness metadata.
---
```

Expected: Trigger text is explicit about both general research and orchestration-prep use cases.

- [ ] **Step 2: Write the opening overview and non-goals**

Include concise sections that explain:
- what the skill does
- what artifacts it produces
- what it must not do

Expected: Another agent can understand the skill boundary without reading the full design doc.

- [ ] **Step 3: Write the operating modes and escalation rules**

Cover:
- targeted research
- deep research
- evidence-driven escalation
- stop conditions

Expected: The skill defaults to minimal sufficient exploration and only escalates when justified.

- [ ] **Step 4: Write the workflow steps**

Include:
- intake
- light probe
- research planning
- focused exploration
- synthesis
- freshness and handoff check

Expected: Workflow is executable and ordered, not just descriptive.

- [ ] **Step 5: Write the certainty-classification and citation rules**

Include required labels:
- `Fact`
- `Inference`
- `Open Question`
- `Decision Blocker`

Also define layered citations and anti-drift behavior.

Expected: Output rules are strong enough to prevent unsupported conclusions.

- [ ] **Step 6: Write the persistence and downstream integration guidance**

Cover:
- when to keep output inline
- when to persist files
- how to support `semantic-batch-refactor-orchestrator`

Expected: The skill clearly hands off reusable context without overstepping into rule-freezing.

- [ ] **Step 7: Self-review for concision and progressive disclosure**

Check:
- the file is concise
- references are pointed to directly
- detailed templates are moved out of `SKILL.md`

Expected: `SKILL.md` stays lean enough to load comfortably.

- [ ] **Step 8: Commit the core workflow**

```bash
git add context-research-orchestrator/SKILL.md
git commit -m "feat: add context research orchestrator workflow"
```

### Task 3: Add Reusable Output Templates

**Files:**
- Modify: `context-research-orchestrator/references/output-templates.md`
- Reference: `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`

- [ ] **Step 1: Define the `Research Report` template**

Include a compact template for:
- `Objective`
- `Scope`
- `Method`
- `Key Findings`
- `Architecture or Flow Summary`
- `Risks`
- `Recommended Next Step`

Expected: Agents can emit consistent reports without bloating `SKILL.md`.

- [ ] **Step 2: Define the `Context Pack` top-level template**

Include sections for:
- `Capture Provenance`
- `Global Theme Blocks`
- `Task-Specific Blocks`

Expected: The structure matches the design and is easy to reuse.

- [ ] **Step 3: Define the standard block schema**

Include fields for:
- `Title`
- `Purpose`
- `Classification`
- `Summary`
- `Why It Matters`
- `Evidence List`
- `Primary References`
- `Relocation Hints`
- `Freshness Notes`
- `Safe Reuse Boundary`

Expected: Context blocks are machine- and human-friendly.

- [ ] **Step 4: Add one compact example block**

Expected: The example demonstrates layered citations and reuse boundaries without overfitting to one repository.

- [ ] **Step 5: Commit the output templates**

```bash
git add context-research-orchestrator/references/output-templates.md
git commit -m "feat: add context research output templates"
```

### Task 4: Add Delegation Guidance For Read-Only Exploration

**Files:**
- Modify: `context-research-orchestrator/references/delegation-guidance.md`
- Reference: `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`

- [ ] **Step 1: Write delegation decision criteria**

Cover when to:
- stay inline
- dispatch a few subagents
- use multi-round exploration

Expected: Agents have a clear rubric for deciding whether subagent exploration is worth the cost.

- [ ] **Step 2: Write a read-only exploration packet template**

Include fields for:
- objective
- search area
- questions to answer
- required output
- constraints

Expected: Child packets request evidence and summaries, not edits.

- [ ] **Step 3: Write synthesis guidance for combining subagent output**

Cover:
- merging overlapping findings
- preserving citations
- resolving disagreements
- marking unsupported claims as `Inference` or `Open Question`

Expected: The primary agent can safely turn multiple exploration passes into one context pack.

- [ ] **Step 4: Add failure-handling guidance**

Cover what to do when:
- anchors cannot be relocated
- evidence conflicts
- the worktree changes during research
- subagent scopes turn out to overlap

Expected: The skill has explicit behavior for drift and ambiguity.

- [ ] **Step 5: Commit the delegation guidance**

```bash
git add context-research-orchestrator/references/delegation-guidance.md
git commit -m "feat: add context research delegation guidance"
```

### Task 5: Integrate And Validate The Skill

**Files:**
- Modify: `README.md`
- Modify: `context-research-orchestrator/SKILL.md`
- Modify: `context-research-orchestrator/references/output-templates.md`
- Modify: `context-research-orchestrator/references/delegation-guidance.md`

- [ ] **Step 1: Cross-check the skill files against the approved design**

Read:
- `docs/orchestration/specs/2026-03-18-context-research-orchestrator-design.md`
- `context-research-orchestrator/SKILL.md`
- `context-research-orchestrator/references/output-templates.md`
- `context-research-orchestrator/references/delegation-guidance.md`

Expected: All required concepts from the design are represented somewhere in the implementation.

- [ ] **Step 2: Cross-check the skill against repository conventions**

Verify:
- concise `SKILL.md`
- reference files linked directly from `SKILL.md`
- README entry is accurate

Expected: The skill is discoverable and follows the current repository pattern.

- [ ] **Step 3: Run a lightweight validation pass**

Validation checklist:
- frontmatter is valid
- file paths in references are correct
- sections mentioned in `SKILL.md` exist
- no obvious contradiction between workflow and references

Expected: The skill is internally consistent.

- [ ] **Step 4: Perform a manual scenario spot-check**

Mentally test at least these scenarios:
- user asks for task-focused project research before writing a plan
- user asks for deep repository research before a semantic refactor
- later orchestration needs source-bound task packet inputs

Expected: The skill gives clear guidance in all three scenarios.

- [ ] **Step 5: Update the README status and key files if needed**

Expected: The repository index accurately reflects the completed skill.

- [ ] **Step 6: Commit the integrated skill**

```bash
git add README.md context-research-orchestrator
git commit -m "feat: add context research orchestrator skill"
```
