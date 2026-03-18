# Output Templates

Use these templates to keep research output consistent and reusable.

## Research Report

```md
# Research Report

## Objective
- What question this research was meant to answer
- What downstream action it supports

## Scope
- Areas covered
- Areas intentionally not covered

## Method
- Research mode: targeted / deep / escalated-targeted
- Whether git history was consulted
- Whether read-only exploration subagents were used

## Key Findings
- [Fact] ...
- [Inference] ...
- [Open Question] ...
- [Decision Blocker] ...

## Architecture or Flow Summary
- Relevant modules, entrypoints, definitions, and flow notes

## Risks
- Most likely ways later planning or execution could go wrong

## Recommended Next Step
- Write plan / continue research / clarify with user / proceed to orchestration
```

## Context Pack

```md
# Context Pack

## Capture Provenance
- captured_at:
- research_mode:
- workspace_state:
- git_commit:
- git_branch:
- related_dirty_files:
- key_file_timestamps:
- confidence_scope:

## Global Theme Blocks
- [Block title]

## Task-Specific Blocks
- [Block title]
```

## Standard Block Schema

```md
### Block: [Title]
- Purpose:
- Classification: Fact | Inference | Open Question | Decision Blocker
- Summary:
- Why It Matters:
- Evidence List:
  - [evidence item]
- Primary References:
  - File:
  - Anchor:
  - Line at capture:
  - Relocation hint:
  - Captured claim:
- Relocation Hints:
  - [hint]
- Freshness Notes:
- Safe Reuse Boundary:
```

## Example Block

```md
### Block: Shared definitions shape downstream packet boundaries
- Purpose: Capture where packet-shaping rules are likely to be constrained by shared files.
- Classification: Fact
- Summary: Shared definition files should usually remain under primary-agent ownership before broad parallel execution.
- Why It Matters: Downstream packet design becomes unsafe if multiple agents edit shared rule sources independently.
- Evidence List:
  - Orchestration guidance keeps shared definition files with the primary agent unless ownership is isolated.
- Primary References:
  - File: semantic-batch-refactor-orchestrator/SKILL.md
  - Anchor: "Shared definition files should stay with the primary agent"
  - Line at capture: 1
  - Relocation hint: search for "shared definition files" or "ownership is explicitly isolated"
  - Captured claim: Shared rule-bearing files are default contention surfaces and should not be casually split.
- Relocation Hints:
  - Search for "shared definitions"
- Freshness Notes:
  - Re-check if the orchestration skill changed after this context pack was captured.
- Safe Reuse Boundary:
  - Safe to reuse when preparing orchestration packets; re-verify before editing shared rule files.
```
