# Semantic Batch Refactor Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a reusable skill in `D:\workspace\skills` that guides a primary agent through requirement convergence, exploration, calibration, safe partitioning, and user-approved multi-subagent execution for semantic batch refactors.

**Architecture:** The implementation will create one new skill directory with a concise but prescriptive `SKILL.md`. The document will encode the operating principles, workflow, decision gates, and reusable templates described in the approved design so future agents can apply the process consistently.

**Tech Stack:** Markdown, YAML frontmatter, local filesystem skill directory structure

---

### Task 1: Create the skill directory layout

**Files:**
- Create: `D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md`
- Modify: `D:\workspace\skills\docs\superpowers\plans\2026-03-18-semantic-batch-refactor-orchestrator.md`

- [ ] **Step 1: Confirm the target skill directory does not already exist**

Run: `Test-Path 'D:\workspace\skills\semantic-batch-refactor-orchestrator'`
Expected: `False`

- [ ] **Step 2: Create the directory if missing**

Run: `New-Item -ItemType Directory -Force 'D:\workspace\skills\semantic-batch-refactor-orchestrator'`
Expected: directory created or confirmed present

- [ ] **Step 3: Re-list `D:\workspace\skills`**

Run: `Get-ChildItem 'D:\workspace\skills'`
Expected: includes `semantic-batch-refactor-orchestrator`

### Task 2: Write the initial skill document

**Files:**
- Create: `D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md`
- Reference: `D:\workspace\skills\docs\superpowers\specs\2026-03-18-semantic-batch-refactor-orchestrator-design.md`

- [ ] **Step 1: Write YAML frontmatter with compliant name and trigger-focused description**

The frontmatter should use:

```yaml
---
name: semantic-batch-refactor-orchestrator
description: Use when a codebase-wide semantic change is large enough for parallel work but needs strict requirement clarification, conflict-aware task partitioning, and controlled subagent execution
---
```

- [ ] **Step 2: Write the overview and when-to-use sections**

Include the target problem, trigger conditions, and non-applicable scenarios.

- [ ] **Step 3: Write the hard rules and main workflow**

Encode the mandatory gates:

- rules must converge before splitting
- exploration agents are read-only
- parallel modification cannot start before boundaries are safe
- user approval is required before broad execution

- [ ] **Step 4: Write the template section**

Include compact, copyable templates for:

- rules specification
- exploration packet
- trial calibration packet
- implementation packet
- user approval checkpoint

### Task 3: Review for clarity and loopholes

**Files:**
- Modify: `D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md`

- [ ] **Step 1: Review the skill for ambiguous language**

Look for weak verbs such as "consider", "maybe", or "often" in places that should be mandatory.

- [ ] **Step 2: Review the skill for missing boundary controls**

Confirm the skill clearly prohibits:

- exploration edits
- overlapping implementation ownership
- rule invention by subagents

- [ ] **Step 3: Tighten any sections where an agent could rationalize skipping the gates**

Rewrite weak statements into explicit checks or stop conditions.

### Task 4: Validate installability and discoverability

**Files:**
- Modify: `D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md`

- [ ] **Step 1: Check the final file exists**

Run: `Test-Path 'D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md'`
Expected: `True`

- [ ] **Step 2: Read back the skill file for final verification**

Run: `Get-Content 'D:\workspace\skills\semantic-batch-refactor-orchestrator\SKILL.md'`
Expected: frontmatter plus concise procedural guidance and templates

- [ ] **Step 3: Verify the frontmatter remains within the supported fields**

Expected:

- only `name`
- only `description`

- [ ] **Step 4: Verify the description describes triggers, not the workflow summary**

Expected: the description explains when to use the skill, not the full process
