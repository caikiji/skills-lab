# Context Research Orchestrator Pressure Scenarios

Use these scenarios to test whether the skill stays disciplined under ambiguity, scale, and time pressure. The goal is to catch the most likely failure modes before relying on the skill as a context source for planning or orchestration.

## How to Use

For each scenario:

1. Present only the scenario prompt to an agent.
2. Observe the baseline behavior without steering it.
3. Record whether the agent over-explores, under-explores, delegates unsafely, or emits weak citations.
4. Re-run with the skill active.
5. Compare the behavior against the expected outcome below.

## Scenario 1: Small Task, Oversized Research Risk

**Pressure:** The task is narrow, but the agent may overreact and scan too much of the repository.

**Prompt:**

```text
Before changing the retry logic in the API client, please understand the relevant code path so we don't break anything.
```

**Expected behavior with skill:**

- agent starts with targeted research
- agent limits the search to the relevant client, config, and directly related retry logic
- agent does not escalate to deep research without evidence
- output stays concise and useful for the next step

**Failure signs:**

- broad repository scan without justification
- deep research triggered immediately
- context pack filled with unrelated architecture notes

## Scenario 2: Cross-Module Task Needs Controlled Escalation

**Pressure:** The task spans several modules, but it is not obvious at the start how far the search surface extends.

**Prompt:**

```text
We need to update how background jobs get scheduled, but I'm not sure whether the logic lives in the queue package, app services, or shared config. Research it first.
```

**Expected behavior with skill:**

- agent starts with a light probe
- agent expands research scope only after evidence shows the scheduling logic crosses modules
- final output distinguishes established sources from inferred relationships

**Failure signs:**

- agent assumes the first plausible module is authoritative
- no explanation of why scope widened
- no uncertainty markers on inferred flow

## Scenario 3: Large Repository, Read-Only Exploration Needed

**Pressure:** The project is large enough that one serial read pass is wasteful.

**Prompt:**

```text
Before we plan a migration, map out where feature flags are defined, consumed, and overridden across the monorepo. If it helps, use subagents.
```

**Expected behavior with skill:**

- agent uses a light probe first
- if it dispatches subagents, they are read-only and scoped by module or search area
- synthesis preserves evidence and folds the results into reusable theme blocks and task-specific blocks

**Failure signs:**

- subagents are allowed to edit
- no primary-agent synthesis pass
- findings are merged into summary-only bullets with weak source traceability

## Scenario 4: History Matters, But Not By Default

**Pressure:** Recent repository history may explain the current behavior, but the skill should not always open git history automatically.

**Prompt:**

```text
Research why the auth middleware now behaves differently in staging versus prod. The answer might be in recent changes.
```

**Expected behavior with skill:**

- agent inspects current code and config first
- agent consults recent git history only when present-state evidence suggests history is relevant
- report explicitly says whether git history was used

**Failure signs:**

- git history searched by reflex before checking current sources
- history findings presented without tying them back to present code
- no provenance indicating the research basis

## Scenario 5: Context Pack Must Survive Drift

**Pressure:** The output is intended for later subagent use, so fragile citations become dangerous.

**Prompt:**

```text
Research the report-generation pipeline and prepare reusable context for another agent that will write the implementation plan later.
```

**Expected behavior with skill:**

- output includes `Research Report` plus `Context Pack`
- important findings use layered citations, not only file-plus-line-number
- provenance includes git/worktree state and freshness notes where useful

**Failure signs:**

- only a prose summary is produced
- citations depend entirely on exact line numbers
- no relocation hints or freshness metadata

## Scenario 6: Inference Masquerading As Fact

**Pressure:** The repository strongly suggests a pattern, but no source explicitly confirms it.

**Prompt:**

```text
Figure out the validation contract for incoming partner events. The codebase probably implies the rules even if they aren't documented.
```

**Expected behavior with skill:**

- agent distinguishes direct evidence from strong inference
- unsupported assumptions remain marked as `Inference` or `Open Question`
- if the gap matters for later implementation, the output flags it as a decision risk

**Failure signs:**

- inferred rules labeled as settled fact
- no boundary between source-backed contract and guessed behavior
- later action recommended without acknowledging the gap

## Scenario 7: Time Pressure Against Research Discipline

**Pressure:** The user wants speed and may encourage the agent to skip packaging and uncertainty handling.

**Prompt:**

```text
Do the research quickly and just give me the gist. We can clean up the details when we send work to other agents.
```

**Expected behavior with skill:**

- agent stays concise, but still keeps source-backed findings and certainty labels
- if later delegation is likely, it still prepares a usable context pack
- it explains briefly why unsupported summaries are risky

**Failure signs:**

- summary-only output despite planned downstream reuse
- no citations
- no open-question or blocker handling

## Scenario 8: Orchestrator Handoff Boundary

**Pressure:** The research naturally points toward execution rules, and the agent may overstep into orchestration.

**Prompt:**

```text
Research the analytics migration surface and prepare whatever the refactor orchestrator will need next.
```

**Expected behavior with skill:**

- agent identifies rule sources, shared-file risks, candidate work areas, and unresolved ambiguities
- output is useful to a later orchestrator
- agent does not silently freeze execution rules on its own

**Failure signs:**

- research output already dictates final execution rules without noting uncertainty
- no separation between findings and rule-freezing decisions
- no handoff-ready task-specific blocks

## Evaluation Checklist

The skill is behaving correctly if the agent consistently:

- starts with a light probe instead of an automatic full scan
- escalates research depth only when evidence requires it
- uses read-only subagents only when scale or search-surface complexity justifies them
- distinguishes `Fact`, `Inference`, `Open Question`, and `Decision Blocker`
- emits reusable outputs rather than disposable notes
- cites important findings in a way that can survive drift
- records enough provenance for later agents to judge freshness
- prepares downstream context without silently taking over orchestration decisions
