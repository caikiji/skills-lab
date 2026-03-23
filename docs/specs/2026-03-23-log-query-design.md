# Log Query Skill Design

## Summary

`log-query` is a lightweight skill for answering natural-language questions over large log files or log directories. It is designed for cases where logs may be too large to inspect directly, log formats may be unknown at first, and the user needs evidence-backed statistics and summaries rather than a blind full-text dump.

The skill is workflow-only. It does not ship with built-in helper scripts. Instead, it teaches the agent to:

- inspect only small samples first
- translate the user's question into a staged filtering plan
- prefer platform-native text tools such as `rg`, `grep`, or PowerShell-compatible search commands
- use semantic analysis only after the candidate set has been reduced
- return conclusions with representative evidence and clear uncertainty labels

## Goals

- Support natural-language log questions over large local log sets.
- Prefer explainable text filtering over black-box semantic scanning.
- Produce conservative, evidence-backed results.
- Output both human-readable summaries and structured statistics.
- Stay lightweight in this repository by avoiding permanent utility scripts unless proven necessary later.

## Non-Goals

- Real-time log monitoring.
- Long-lived multi-round research state.
- Guaranteed root-cause analysis.
- Full semantic understanding of entire log corpora.
- A permanent scripts toolbox for every possible log shape.

## Primary Use Case

The first target workflow is:

1. The user points the agent at a log directory or one or more log files.
2. The user asks a natural-language question, usually about errors, anomalies, or a topic-specific subset of logs.
3. The agent samples the logs, builds a filtering plan, runs staged text filtering, optionally applies limited semantic narrowing, and returns statistics plus evidence.

Typical questions include:

- "Summarize the error patterns in this directory."
- "Count logs related to checkout failure, excluding retries and health checks."
- "Find entries matching this topic, then summarize the main clusters."

## Input Contract

The skill assumes the user provides:

- one or more file or directory paths
- a natural-language question

The user may also provide:

- time-window hints
- include or exclude hints
- file-name patterns
- a preference for error-only analysis

If details are missing, the agent should make conservative assumptions and state them explicitly.

## Output Contract

The default output should contain:

1. `Question`
   The user's request in operational form.
2. `Scope`
   Which paths were inspected, whether sampling was used, and whether only a subset was scanned.
3. `Filter Plan`
   The include, exclude, and narrowing logic used.
4. `Findings`
   Counts, clusters, or other statistics.
5. `Evidence`
   Representative log lines or event snippets.
6. `Uncertainties`
   Gaps, ambiguities, or likely blind spots.
7. `Structured Output`
   JSON and optionally CSV statistics when useful.

The default reporting mode is:

- Markdown summary for humans
- JSON statistics for downstream reuse
- CSV only when a tabular export adds value

## Core Workflow

### 1. Explore

Read only a very small sample first. Determine:

- approximate log size and file count
- whether logs are mostly single-line or multi-line
- whether they appear structured, semi-structured, or plain text
- whether timestamps, levels, request ids, or stable fields are visible

The agent must not start by reading the entire corpus.

### 2. Translate

Convert the natural-language request into a staged query plan:

- target concept
- include terms
- exclude terms
- likely synonyms or related terms
- likely noise patterns
- whether simple line statistics are sufficient
- whether event-block extraction may be needed

### 3. Filter

Run staged text filtering with platform-appropriate tools:

- prefer `rg` when available
- use `grep` where appropriate
- use PowerShell-compatible search when native shell constraints require it

Filtering should proceed from broad to narrow:

- file scope
- broad include filter
- exclude filter
- context or adjacency expansion if needed
- second-pass narrowing when required

### 4. Aggregate

Default to line-based statistics:

- total matches
- per-file distribution
- recurring phrases or patterns
- representative examples

If the question clearly depends on multi-line context, the agent may switch to event-block handling, but this is not the default.

### 5. Semantic Narrowing

Only use semantic analysis after the candidate set is small enough to inspect safely.

Semantic analysis is allowed when:

- the user query is inherently semantic
- text filtering still leaves too many mixed candidates
- the agent needs to cluster near-duplicate but differently worded messages

Any semantic grouping must be labeled as an inference, not a direct fact.

### 6. Report

Return a conservative report with:

- statistics
- representative evidence
- any inferred clusters clearly marked
- explicit limitations

## Hard Rules

- Never start with a full read of large logs.
- Never use semantic analysis as the first filter layer.
- Never present unsupported inference as fact.
- Never return summary-only output without evidence.
- Default to line-level statistics unless the task clearly requires event-level grouping.
- Prefer transparent command pipelines over opaque one-off heuristics.

## Red Flags

These indicate the agent is about to misuse the skill:

- "I'll just scan the whole directory first."
- "This sounds semantic, so I'll classify everything directly."
- "The grep results are large, but I can summarize from a few samples."
- "These messages look similar enough; I'll merge them."
- "The user only asked for a summary, so evidence is optional."

## Platform Strategy

The workflow is cross-platform by intent:

- prefer `rg` where installed
- otherwise use the strongest native text-search tool available
- keep the workflow stable even if the exact command changes by platform

The skill teaches the decision process, not one fixed command syntax.

## Pressure Scenarios

The first validation set should cover:

1. Huge log directory pressure
   The user pushes for a quick answer; the agent must still sample first.
2. Semantic-only request pressure
   The query is vague and thematic; the agent must still translate it into explicit filters.
3. Multi-layer include/exclude filtering
   The task requires several narrowing passes.
4. Multi-line stack trace temptation
   The logs contain stack traces, but the agent should not default to event-block mode unless necessary.
5. Summary-without-evidence pressure
   The user asks for only a conclusion; the agent must still include representative evidence.
6. Over-merge pressure
   Similar-looking messages should not be merged without care.

## Future Expansion

Possible later additions, if proven necessary:

- a small reference file with output templates
- optional helper snippets for repeated shell patterns
- stronger guidance for JSONL-heavy logs
- specialized variants for error clustering versus topic extraction
