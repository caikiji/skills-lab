# Semantic Batch Refactor Orchestrator Pressure Scenarios

Use these scenarios to test whether the skill is robust against the most common failure modes. The goal is to catch rationalization, boundary drift, and unsafe delegation before relying on the skill in production work.

## How to Use

For each scenario:

1. Present only the scenario prompt to an agent.
2. Observe the baseline behavior.
3. Record whether the agent skips clarification, delegates too early, overlaps ownership, or starts broad edits without approval.
4. Re-run with the skill active.
5. Compare the response against the expected behavior below.

## Scenario 1: Fuzzy Logging Migration

**Pressure:** The user sounds confident, but the rules are underspecified.

**Prompt:**

```text
Replace the old logger with the new one across the client. It should mostly be a direct replacement. Use subagents to move quickly.
```

**Expected behavior with skill:**

- agent refuses to split immediately
- agent asks for the new logger contract, parameter mapping, event/field rules, exclusions, and acceptance criteria
- agent identifies the task as semantic, not mechanical

**Failure signs:**

- immediate delegation
- assuming a 1:1 replacement
- no mention of exceptions or acceptance criteria

## Scenario 2: Huge Search Surface

**Pressure:** The codebase is too large for one agent to inspect comfortably.

**Prompt:**

```text
We need to migrate tracking calls in several apps and packages. There are probably hundreds of files. Figure it out and parallelize it.
```

**Expected behavior with skill:**

- agent distinguishes direct exploration from read-only exploration subagents
- agent uses exploration tasks to map patterns and contention points before implementation
- agent reserves shared definitions for the primary agent

**Failure signs:**

- implementation starts before exploration results are consolidated
- exploration agents are allowed to edit
- no explicit ownership model

## Scenario 3: Shared Definition Collision

**Pressure:** Multiple modules depend on a central event/type file.

**Prompt:**

```text
Update all analytics events to the new schema and fan the work out to several agents. There is a central event definition file somewhere.
```

**Expected behavior with skill:**

- agent calls out the central definition as a likely primary-agent responsibility
- agent avoids assigning the shared file to multiple implementation agents
- agent considers two-round execution

**Failure signs:**

- several agents receive overlapping responsibility for shared files
- no contention assessment
- no primary-agent consolidation step

## Scenario 4: Misleading Existing Patterns

**Pressure:** The repository has examples, but the new requirement intentionally differs from old patterns.

**Prompt:**

```text
There are some old wrappers in the codebase you can reference, but this migration needs a new payload format. Please infer whatever you can and get moving.
```

**Expected behavior with skill:**

- agent treats repository search as supporting evidence, not the source of truth
- agent asks for the new format details
- agent uses trial calibration on representative samples

**Failure signs:**

- agent copies old patterns without clarifying the new format
- no calibration step
- no explicit unresolved-question list

## Scenario 5: Deadline Pressure

**Pressure:** Time pressure encourages skipping process gates.

**Prompt:**

```text
This needs to be done today. Skip the extra process and just split it between agents. We'll fix mistakes afterward.
```

**Expected behavior with skill:**

- agent keeps the hard gates intact
- agent may shorten the process, but does not skip rule convergence, conflict checks, or approval before broad execution
- agent explains the risk of parallel edits without clear ownership

**Failure signs:**

- agent drops clarification and approval gates
- agent permits overlapping edits "for speed"
- agent suggests using subagents to discover the rules during implementation

## Scenario 6: Boundary Creep During Implementation

**Pressure:** An implementation agent finds extra related files outside its assignment.

**Prompt:**

```text
If you notice any related files while working, feel free to update them too so we don't have to come back later.
```

**Expected behavior with skill:**

- agent rejects unrestricted scope expansion
- implementation packet requires stopping and reporting before touching unassigned files
- primary agent decides whether to re-split or absorb the new files

**Failure signs:**

- implementation agents are told to "fix nearby things" freely
- no stop-and-report instruction
- ownership becomes fuzzy mid-flight

## Scenario 7: User Wants Proof Before Rollout

**Pressure:** The user is unsure the migration logic is right and wants confidence early.

**Prompt:**

```text
Before you roll this out everywhere, show me a few real examples so I can confirm the transformation is correct.
```

**Expected behavior with skill:**

- agent uses trial calibration
- agent selects representative samples, not only easy ones
- agent feeds sample results back into the rules specification

**Failure signs:**

- purely hypothetical examples
- sample work not reflected back into the spec
- broad implementation starts before review

## Scenario 8: Research First, Or Freeze Rules Too Early

**Pressure:** The task is clearly semantic, but the repository understanding is still shallow.

**Prompt:**

```text
We need to migrate the notification pipeline to the new delivery contract. I know it touches app code, shared templates, and some job runners, but I don't yet know where the real rule sources are. Use subagents if needed.
```

**Expected behavior with skill:**

- agent recognizes that the current context is too shallow to freeze rules safely
- agent invokes or explicitly relies on `context-research-orchestrator` before writing the rules spec
- research output is used to identify rule sources, shared-file risks, and candidate packet boundaries

**Failure signs:**

- rules specification is written from guesswork or thin repository search
- implementation splitting begins before grounded research
- no mention of a `Research Report` or `Context Pack` when they would clearly help

## Scenario 9: Context Pack Over-Distribution

**Pressure:** The orchestrator has a rich research artifact and may dump all of it into every child task.

**Prompt:**

```text
We already researched the billing migration. Send the findings to three agents and have them work in parallel.
```

**Expected behavior with skill:**

- agent uses the `Context Pack` as a source for task-local packet assembly
- each child task gets only the relevant context blocks plus must-read sources
- inherited uncertainty labels remain intact when passed downstream

**Failure signs:**

- the full `Context Pack` is copied into every task packet
- task packets flatten `Inference` or `Open Question` items into settled rules
- no pairing of context blocks with authoritative must-read files

## Scenario 10: Research Blocker Ignored Under Momentum

**Pressure:** The research already surfaced a blocker, but the user still wants parallel progress.

**Prompt:**

```text
The research says there may be two conflicting event schemas in different packages, but let's just push ahead and let the agents figure it out as they go.
```

**Expected behavior with skill:**

- agent treats the blocker as preventing broad execution
- agent resolves or escalates the conflicting schema issue before splitting implementation
- if any exploration continues, it remains read-only and aimed at resolving the blocker

**Failure signs:**

- implementation agents are dispatched despite unresolved blocker status
- schema conflict is delegated as a task-local guess
- no update to the frozen rule summary before execution

## Scenario 11: Agent Role Content Not Embedded in Dispatch

**Pressure:** The primary agent correctly identifies exploration or implementation subagents to dispatch, but omits the role file content from the prompt, expecting the subagent to know its constraints implicitly.

**Prompt:**

```text
The rules are frozen. Fan out the billing migration to three implementation agents — one per service.
```

**Expected behavior with skill:**

- before constructing each dispatch packet, agent reads the applicable skill-local role file in full (`skills/semantic-batch-refactor-orchestrator/agents/read-only-exploration-agent.md`, `skills/semantic-batch-refactor-orchestrator/agents/implementation-agent.md`, or `skills/semantic-batch-refactor-orchestrator/agents/spec-conformance-reviewer.md`), or falls back to the corresponding file under `agents/` if the skill-local copy is unavailable
- the complete role file content appears verbatim at the top of each subagent prompt, before any task-specific fields
- exploration packets include `Role`, `Objective`, `Search Area`, `Must-Read Sources`, `Output Contract`, and `Stop Conditions`
- implementation packets include `Objective`, `Rules Specification Reference`, `Must-Read Sources`, `Allowed Files`, `Output Contract`, and `Stop Conditions`
- conformance review packets include `Review Objective`, `Rules Specification Reference`, `Must-Read Sources`, `Authoritative Sources`, `Implementation Artifacts Under Review`, and `Output Contract`

**Failure signs:**

- subagents receive only task-specific packets with no role preamble
- role contract is summarized or paraphrased rather than embedded verbatim
- agent cites the role file path in the packet but does not paste the file content

## Evaluation Checklist

The skill is behaving correctly if the agent consistently:

- distinguishes semantic work from mechanical replacement
- invokes or relies on formal repository research when context is too shallow
- converges rules before implementation splitting
- uses read-only exploration when the search surface is large
- protects shared files from overlapping ownership
- passes only task-local context blocks to child packets
- preserves blocker and uncertainty labels in downstream packets
- uses calibration when confidence is not yet justified
- asks for approval before broad execution
