# Log Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `log-query` skill that guides agents through evidence-backed, natural-language log analysis over large local log sets using staged text filtering and optional post-filter semantic narrowing.

**Architecture:** The implementation adds one new skill directory with a workflow-only `SKILL.md` and a matching `pressure-scenarios.md`. The skill stays lightweight by preferring platform-native text tools (`rg`, `grep`, PowerShell-compatible search) and explicitly avoiding permanent helper scripts. Repository docs are then updated so the new skill appears in the top-level index and layout guidance.

**Tech Stack:** Markdown skill documents, repository documentation, git

---

## File Structure

- Create: `docs/plans/2026-03-23-log-query-implementation.md`
- Create: `skills/log-query/SKILL.md`
- Create: `skills/log-query/pressure-scenarios.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

## Task 1: Create The Skill Skeleton

**Files:**
- Create: `skills/log-query/SKILL.md`
- Create: `skills/log-query/pressure-scenarios.md`

- [ ] **Step 1: Create the `skills/log-query/` directory**

Run: `New-Item -ItemType Directory -Force skills/log-query`
Expected: directory exists at `skills/log-query`

- [ ] **Step 2: Draft `skills/log-query/SKILL.md` with YAML front matter**

Include:
- `name: log-query`
- a trigger-only `description` that starts with `Use when...`
- an overview that states the skill is workflow-only and does not ship helper scripts

- [ ] **Step 3: Add the core workflow to `skills/log-query/SKILL.md`**

Document these stages in order:
- Explore
- Translate
- Filter
- Aggregate
- Semantic Narrowing
- Report

- [ ] **Step 4: Add hard rules and red flags to `skills/log-query/SKILL.md`**

Cover:
- sample first, never full-read large logs first
- semantic analysis must not be the first filter layer
- default to line-level statistics
- evidence is mandatory
- inferences must be labeled

- [ ] **Step 5: Draft `skills/log-query/pressure-scenarios.md`**

Add first-pass scenarios for:
- huge log directory pressure
- semantic-only request pressure
- multi-layer include/exclude pressure
- multi-line stack trace temptation
- summary-without-evidence pressure
- over-merge pressure

- [ ] **Step 6: Review both new files for consistency with the approved design**

Check:
- no permanent scripts are referenced as required implementation
- cross-platform tool guidance stays abstract enough to support `rg`, `grep`, and PowerShell
- the workflow stays conservative and evidence-backed

- [ ] **Step 7: Commit the skill skeleton**

Run:
```bash
git add skills/log-query/SKILL.md skills/log-query/pressure-scenarios.md
git commit -m "feat: add log-query skill"
```

Expected: a commit containing only the new skill files

## Task 2: Register The Skill In Repository Docs

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the skill index in `README.md`**

Add a row for `log-query` describing:
- natural-language log questions
- large local logs
- staged text filtering
- evidence-backed statistics and summaries

- [ ] **Step 2: Update the repository layout section in `README.md`**

Add `skills/log-query/` to the top-level skill list with a short description.

- [ ] **Step 3: Add a dedicated `log-query` section in `README.md`**

Describe:
- when to use the skill
- its lightweight, workflow-only design
- its preference for platform-native text tools

- [ ] **Step 4: Update `AGENTS.md` skill inventory**

Add `skills/log-query/` anywhere the repo-level skill set is enumerated so future agents know it exists.

- [ ] **Step 5: Update `CLAUDE.md` skill inventory**

Mirror the same additions made to `AGENTS.md` so the repository guidance remains aligned across both documents.

- [ ] **Step 6: Verify the documentation does not claim helper scripts exist**

Search for accidental references to:
- `skills/log-query/scripts/`
- built-in parser utilities
- fixed implementation commands that contradict the workflow-only design

- [ ] **Step 7: Commit the documentation updates**

Run:
```bash
git add README.md AGENTS.md CLAUDE.md
git commit -m "docs: document log-query skill"
```

Expected: a commit containing only repository documentation updates

## Task 3: Validate Skill Quality Before Execution Handoff

**Files:**
- Test: `skills/log-query/SKILL.md`
- Test: `skills/log-query/pressure-scenarios.md`
- Test: `README.md`
- Test: `AGENTS.md`
- Test: `CLAUDE.md`

- [ ] **Step 1: Run a repository search for the new skill name**

Run: `Get-ChildItem -Recurse -File | Select-String -Pattern 'log-query'`
Expected: hits in the new skill files and the updated repo docs

- [ ] **Step 2: Verify the YAML front matter manually**

Check that `skills/log-query/SKILL.md` includes only:
- `name`
- `description`

Expected: valid front matter with no extra keys

- [ ] **Step 3: Verify the trigger description is about when to use the skill**

Check that the `description` explains triggering conditions and does not summarize the whole workflow.

- [ ] **Step 4: Review the pressure scenarios against the hard rules**

Confirm each scenario tests one or more of:
- premature full scans
- premature semantic analysis
- missing evidence
- over-aggregation

- [ ] **Step 5: Run a final diff review**

Run: `git diff --stat HEAD~2..HEAD`
Expected: only the new skill files and repository documentation appear in the recent implementation range

- [ ] **Step 6: Commit any final consistency fixes**

Run:
```bash
git add skills/log-query/SKILL.md skills/log-query/pressure-scenarios.md README.md AGENTS.md CLAUDE.md
git commit -m "chore: polish log-query skill docs"
```

Expected: either no-op if nothing changed, or a small cleanup commit

## Notes For Execution

- Follow the approved design in `docs/specs/2026-03-23-log-query-design.md`.
- Keep the skill workflow-only; do not add helper scripts unless the scope is explicitly re-opened.
- Prefer concise, high-signal wording because skills are loaded into model context.
- Treat pressure scenarios as the first validation mechanism since this repository does not have a build or test suite.
