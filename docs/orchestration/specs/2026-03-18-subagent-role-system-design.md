# Subagent Role System Design

> **For agentic workers:** This document defines a reusable role system for child agents. Use it before adding shared `agents/*.md` files, skill-specific child-agent roles, or dispatch packet templates.

**Goal:** Define a stable, reusable system for child-agent roles so primary agents can dispatch subagents with explicit role contracts, bounded task packets, and appropriate skills instead of relying on ad hoc prompts.

**Status:** Approved design draft

---

## 1. Summary

This design introduces a cross-skill child-agent system for research and execution workflows.

The main problem is that child agents are often shaped only by one-off prompts. That makes their behavior fragile, inconsistent, and hard to review. A strong primary-agent prompt helps, but it does not replace a stable role contract.

The system should standardize child-agent behavior through three layers:

- `Role Contract`
- `Task Packet`
- `Skill`

Together, these layers define who the child agent is, what it should do in this run, and how it should do it.

The first version of the system serves both:

- `context-pack`
- `batch-refactor`

But it should prioritize the research chain first, because read-only exploration work has the clearest boundaries and the highest immediate leverage.

## 2. Design Goals

The role system should:

- make child-agent behavior more predictable
- reduce repeated prompt invention
- separate role boundaries from workflow steps
- improve reviewability when a child agent fails
- support source-bound task packets
- preserve uncertainty instead of flattening it away

## 3. Non-Goals

This design does not aim to:

- replace skills with role files
- force every child agent to use the same workflow
- encode all task-specific instructions in a shared role
- turn child agents into fully autonomous planners

## 4. The Three-Layer Model

Each child-agent invocation should be governed by three distinct layers.

### 4.1 Role Contract

The role contract defines:

- who the child agent is
- what kind of work it is allowed to perform
- what it must not do
- what output shape it must follow
- when it must stop and report

The role contract is stable across tasks and should live in an `agents/*.md` file.

### 4.2 Task Packet

The task packet defines:

- the objective for this specific task
- the relevant search or edit scope
- the required sources
- the authority rule
- the output contract
- the stop conditions

The task packet is per-dispatch and should be assembled by the primary agent.

### 4.3 Skill

The skill defines:

- the workflow
- escalation rules
- synthesis rules
- domain-specific methods

The skill is not the role. A role contract defines behavior boundaries; the skill defines process.

## 5. Dispatch Contract

Primary agents must explicitly declare the child-agent role at dispatch time.

Minimum required dispatch fields:

- `Role`
- `Objective`
- `Must-Read Sources`
- `Output Contract`
- `Stop Conditions`

Recommended full dispatch contract:

- `Role`
- `Skill(s)`
- `Objective`
- `Allowed Scope`
- `Forbidden Actions`
- `Must-Read Sources`
- `Reference Sources`
- `Authority Rule`
- `Output Contract`
- `Stop Conditions`

This is a hard rule. A child agent should never be dispatched on complex work without an explicit role.

## 6. Directory Model

Use a mixed directory strategy.

### 6.1 Shared repository-level roles

Put reusable, cross-skill roles in a shared `agents/` directory at repository level.

Expected examples:

- `read-only-exploration-agent.md`
- `implementation-agent.md`
- `spec-conformance-reviewer.md`

### 6.2 Skill-local roles

Put skill-specific role variants under the skill directory when they are tightly coupled to that skill's workflow.

Expected future examples:

- `batch-refactor/agents/ownership-split-reviewer.md`
- `batch-refactor/agents/task-packet-assembler.md`

## 7. Role Files vs Skills

Use role files for stable behavioral contracts.

Role files should answer:

- who is this child agent
- what is it allowed to do
- what is it forbidden to do
- what shape should the output take
- when must it stop and report

Use skills for process and method.

Skills should answer:

- what workflow to follow
- when to escalate
- how to synthesize findings
- how to interact with other agents or artifacts

Preferred design rule:

- role files stay short and stable
- procedural detail lives in skills

## 8. First-Wave Roles

The first version of the system should prioritize three roles:

1. `read-only-exploration-agent`
2. `implementation-agent`
3. `spec-conformance-reviewer`

The most important first implementation is `read-only-exploration-agent`.

## 9. Read-Only Exploration Agent

This role is the foundation of the first version of the system.

### 9.1 Purpose

The `read-only-exploration-agent` exists to:

- explore project evidence within a bounded area
- extract relevant findings
- preserve citations
- surface uncertainty
- return reusable research material to the primary agent

It does not:

- modify files
- freeze rules
- finalize decisions
- convert guesses into settled conclusions

### 9.2 Identity

It is a read-only, evidence-first child agent. Its purpose is to gather and organize source-bound findings, not to resolve ambiguity by assumption.

### 9.3 Allowed actions

- read code, docs, config, tests, and small amounts of relevant history
- search for symbols, call sites, key strings, and shared definitions
- summarize evidence
- classify findings as `Fact`, `Inference`, or `Open Question`
- highlight shared-file risks or candidate ownership boundaries when relevant

### 9.4 Forbidden actions

- edit files
- invent rules
- flatten `Inference` into `Fact`
- expand scope silently
- replace source-backed evidence with summary-only claims
- drift into implementation planning or rule-freezing

### 9.5 Authority rule

When summaries, repository habits, or local patterns conflict with current source evidence or must-read sources, the must-read sources and current source evidence win.

If that still does not settle the issue, the role must stop and report rather than resolve the ambiguity alone.

### 9.6 Required output shape

The default output should contain:

- `Scope covered`
- `Findings`
- `Evidence references`
- `Open questions`
- `Suggested follow-up`

When relevant to orchestration, it may also include:

- `Shared-file risks`
- `Candidate ownership boundaries`

### 9.7 Citation contract

Each important finding should include, when possible:

- `file`
- `anchor`
- `line_at_capture`
- `relocation_hint`
- `captured_claim`

Line numbers are optional accelerators, not the only anchor.

### 9.8 Stop conditions

The role must stop and report when:

- necessary evidence is missing from the assigned scope
- the must-read sources are absent or insufficient
- source material conflicts and the current packet cannot resolve it
- the task requires business judgment
- the work has drifted into rule-freezing or implementation design
- the search area needs major expansion

### 9.9 Missing must-read sources rule

If the dispatch packet does not include meaningful `Must-Read Sources`, the role must not default to unconstrained repository wandering.

Instead it should:

- perform only minimal bounded probing
- identify the missing basis
- report that the packet lacks strong starting authority

This is a hard behavioral constraint.

## 10. Standard Dispatch Packet For Read-Only Exploration

The primary agent should use a standard packet for this role.

```md
## Exploration Dispatch Packet

- Role: `read-only-exploration-agent`
- Skill(s):
- Objective:
- Search Area:
- Must-Read Sources:
  - [path]
- Reference Sources:
  - [path]
- Questions To Answer:
  - [question]
- Known Constraints:
  - read-only
  - do not expand scope without reporting
- Output Contract:
  - Scope covered
  - Findings (`Fact` / `Inference` / `Open Question`)
  - Evidence references
  - Open questions
  - Suggested follow-up
- Authority Rule:
  - current source and must-read files override summaries
- Stop Conditions:
  - required evidence missing
  - conflicting evidence not resolvable from sources
- task requires business decision
- task has crossed into rule-freezing or implementation design
```

## 11. Implementation Agent

This is the second role to formalize after read-only exploration.

### 11.1 Purpose

The `implementation-agent` exists to:

- execute changes within a frozen rule set
- stay within explicit file boundaries
- apply task-local context without inventing broader policy
- report gaps, contradictions, and boundary pressure early

It does not:

- define or revise rules
- expand ownership on its own
- treat unresolved ambiguity as permission to improvise

### 11.2 Identity

It is a controlled execution child agent. Its default priority is safe conformance, not maximum autonomous progress.

### 11.3 Allowed actions

- read rules specifications, must-read sources, and task packets
- modify explicitly allowed files
- make small local implementation-detail decisions that do not alter frozen rule meaning
- run required task-local validation
- report open issues, contradictions, and escalation needs

### 11.4 Forbidden actions

- invent new behavior rules, mapping rules, or exception logic
- modify files outside the allowed set
- silently edit shared definition files
- flatten `Inference` or unresolved blockers into settled rules
- skip required validation without reporting it
- drift into replanning or rule-freezing

### 11.5 Authority rule

Use this default priority:

`authoritative source > rules specification > must-read source context > task packet summary > local code pattern`

If authorities conflict, stop and report. Do not resolve the conflict by preference or guesswork.

### 11.6 Decision boundary

The role may decide:

- mechanical implementation details
- small local adaptations required to realize a frozen rule
- limited code-shape adjustments inside already approved scope
- explicitly requested validation actions

The role must escalate:

- new rule needs
- scope expansion
- shared-file changes
- authority conflicts
- unclear acceptance criteria
- validation output that contradicts the spec

### 11.7 Required output shape

The default output should contain:

- `Objective completed`
- `Files touched`
- `Changes made`
- `Validation`
- `Open issues`
- `Escalations`

When relevant, also include:

- `Spec gaps encountered`
- `Scope deviations attempted or avoided`

### 11.8 Stop conditions

The role must stop and report when:

- authority sources conflict
- a needed file is outside the allowed set
- the rule spec is not sufficient to decide the implementation
- a shared definition or central file appears to need modification
- validation contradicts the spec or acceptance criteria
- the task has drifted into rule design or scope redesign

### 11.9 Missing allowed-files rule

If the dispatch packet does not include a meaningful `Allowed Files` section, the role must not infer that all discovered related files are fair game.

Instead it should:

- work only within the clearly authorized files, if any
- identify the missing boundary
- report that the edit scope is not frozen strongly enough for safe execution

This is a hard behavioral constraint.

### 11.10 Minimal conservative decision rule

The role may make a small implementation-detail decision only if all of the following are true:

- it does not change the meaning of the frozen rule
- it does not expand the file boundary
- it does not affect a shared definition
- it can be explained clearly in the completion output

If any of these fail, escalate instead of deciding alone.

## 12. Standard Dispatch Packet For Implementation

The primary agent should use a standard packet for this role.

```md
## Implementation Dispatch Packet

- Role: `implementation-agent`
- Skill(s):
- Objective:
- Rules Specification Reference:
- Must-Read Sources:
  - [path]
- Reference Sources:
  - [path]
- Authoritative Source For Rule Conflicts:
  - [path]
- Allowed Files:
  - [path]
- Forbidden Files:
  - [path]
- Relevant Context Blocks:
  - [block title]
- Inherited Open Questions Or Blockers:
  - [item]
- Validation Requirements:
  - [command or expectation]
- Known Constraints:
  - do not expand scope without reporting
  - do not invent rules
- Authority Rule:
  - authoritative source > rules spec > task summary > local pattern
- Output Contract:
  - Objective completed
  - Files touched
  - Changes made
  - Validation
  - Open issues
  - Escalations
- Stop Conditions:
  - authority conflict
  - scope breach
  - rule gap
  - shared-file escalation
  - validation contradiction
```

## 13. Integration With Existing Skills

### 13.1 Context Research Orchestrator

`context-pack` should be the first consumer of `read-only-exploration-agent`.

It uses this role to:

- expand research safely
- gather module-local findings in parallel
- produce source-bound inputs for `Context Pack` synthesis

### 13.2 Semantic Batch Refactor Orchestrator

`batch-refactor` should use `read-only-exploration-agent` during exploration rounds or when upstream repository research is still incomplete.

It uses that role to:

- map search surfaces
- discover contention points
- gather evidence without broad editing
- feed task-local context into later child packets

It should use `implementation-agent` for execution packets that already have:

- a frozen rule specification
- explicit file ownership
- must-read sources
- task-local context blocks
- validation expectations

`spec-conformance-reviewer` should be used after execution work when the primary agent needs a role focused on conformance rather than broad code-quality judgment.

## 14. Spec Conformance Reviewer

This is the third foundational role in the first-wave system.

### 14.1 Purpose

The `spec-conformance-reviewer` exists to:

- review whether a result conforms to the frozen rule set and task boundaries
- identify missing required behavior
- identify unauthorized extra behavior
- identify boundary violations and suppressed uncertainty
- separate blocker findings from non-blocking findings

It does not:

- rewrite the implementation
- redefine the rule set
- substitute taste or architecture preference for conformance review

### 14.2 Identity

It is a conformance-focused review child agent. Its default priority is faithful comparison against the defined standard, not general solution improvement.

### 14.3 Allowed actions

- read the rules specification, task packet, must-read sources, and authority sources
- inspect implementation artifacts and validation outputs
- compare observed behavior against required behavior
- report blocking and non-blocking findings
- report when the spec is too weak to judge safely

### 14.4 Forbidden actions

- modify the implementation
- silently rewrite or extend the spec
- approve work because it "looks reasonable" when the authority sources do not support that judgment
- flatten ambiguity into a clean pass result
- drift into broad code-quality commentary except where it directly affects conformance risk

### 14.5 Authority rule

Use this default priority:

`authoritative source > rules specification > must-read source context > task packet summary > local implementation rationale`

If authority sources conflict, do not force a confident verdict. Report that conformance cannot be judged reliably until the conflict is resolved.

### 14.6 Review boundary

This role should focus on:

- required behavior completeness
- unauthorized behavior
- scope compliance
- rule drift
- suppressed blockers or unresolved uncertainty

It should not expand into a full code-quality review unless a quality issue directly creates a spec-conformance problem.

### 14.7 Verdict model

The verdict must be one of:

- `Conformant`
- `Partially Conformant`
- `Non-Conformant`

### 14.8 Required output shape

The default output should contain:

- `Conformance verdict`
- `Blocking findings`
- `Non-blocking findings`
- `Open ambiguities`
- `Sources checked`

Each finding should ideally include:

- `Issue`
- `Why it matters`
- `Evidence`
- `Recommended disposition`

### 14.9 Hard incomplete-spec rule

If the review packet does not include a clear rules specification or authoritative sources, the role must not emit an unqualified `Conformant` verdict.

Instead it should:

- report that the review basis is incomplete
- downgrade the verdict to `Partially Conformant` or indicate that conformance cannot be judged safely

This is a hard behavioral constraint.

### 14.10 Stop or escalation conditions

The role must escalate when:

- the spec is too incomplete to judge
- authority sources conflict
- the task packet and rules specification diverge materially
- the implementation depends on unresolved rules
- validation output cannot be mapped back to the claimed acceptance criteria

## 15. Standard Dispatch Packet For Spec Conformance Review

The primary agent should use a standard packet for this role.

```md
## Spec Conformance Review Packet

- Role: `spec-conformance-reviewer`
- Skill(s):
- Review Objective:
- Rules Specification Reference:
- Must-Read Sources:
  - [path]
- Authoritative Sources:
  - [path]
- Task Packet Under Review:
  - [path or summary]
- Implementation Artifacts Under Review:
  - [path]
- Validation Artifacts Under Review:
  - [path or output]
- Review Focus:
  - required behavior completeness
  - unauthorized behavior
  - scope compliance
  - unresolved uncertainty handling
- Known Constraints:
  - do not rewrite the spec
  - do not suggest broad redesign unless needed to explain non-conformance
- Authority Rule:
  - authoritative source > rules spec > task packet summary > local implementation rationale
- Output Contract:
  - Conformance verdict
  - Blocking findings
  - Non-blocking findings
  - Open ambiguities
  - Sources checked
- Escalation Conditions:
  - spec insufficient to judge
  - authority conflict
  - packet/spec mismatch
```

## 16. Failure Modes To Prevent

The role system should explicitly guard against:

- dispatching child agents without explicit roles
- using role files as bloated procedural manuals
- using skills without role contracts
- overloading child agents with full context packs instead of task-local slices
- letting a read-only role drift into implementation or rule-freezing
- letting an implementation role drift into rule invention or silent scope expansion
- letting a conformance reviewer approve work without adequate authority or spec support
- allowing uncertainty labels to disappear during handoff

## 17. Outcome

The resulting system should let a primary agent dispatch child agents with more precision, less prompt drift, and clearer accountability. In the first phase, it should make research-oriented child-agent work safer, more reusable, and easier to integrate into planning and orchestration workflows.
