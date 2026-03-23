---
name: log-query
description: Use when a user provides local log files or directories plus a natural-language question, and the logs may be too large or too mixed to inspect directly without staged text filtering, evidence-backed statistics, and optional semantic narrowing on a reduced candidate set.
---

# Log Query

Answer natural-language questions over large local log sets without pretending the model can safely read everything at once.

This skill is workflow-only. Prefer platform-native text tools such as `rg`, `grep`, or PowerShell-compatible search commands. Only use semantic analysis after the candidate set is small enough to inspect safely.

## When to Use

Use this skill when:

- the user points to one or more local log files or directories
- the user asks a natural-language question rather than giving a ready-made search command
- the logs may be too large to read directly
- the task needs explainable filtering, statistics, clustering, or evidence-backed summary
- the task may need multiple include and exclude passes before any semantic grouping

Do not use this skill when:

- the user already provided an exact one-step command to run
- the input is small enough to inspect directly without staged filtering
- the task is real-time monitoring rather than local log analysis
- the task requires durable multi-round research state

## Core Rule

**Sample first, filter second, infer last.**

- Start with a tiny sample.
- Translate the request into explicit include and exclude logic.
- Use transparent text filtering before any semantic narrowing.
- Keep conclusions tied to evidence.

## Workflow

### 1. Explore

Read only a very small sample first to determine:

- approximate size and file count
- single-line versus multi-line log shape
- plain text versus structured-looking records
- visible timestamps, levels, request ids, or recurring fields

Do not begin with a full scan of a large log directory.

### 2. Translate

Convert the user's question into an explicit query plan:

- target concept
- include terms
- exclude terms
- likely synonyms or related phrases
- likely noise sources
- whether line-level statistics are enough
- whether event-block extraction may be required later

If the user request is broad, tighten it into an operational plan before scanning deeply.

### 3. Filter

Use staged text filtering with platform-appropriate tools:

- prefer `rg` when available
- otherwise use `grep` or the strongest native text-search command available
- on Windows, use PowerShell-compatible search when shell constraints require it

Filter from broad to narrow:

1. scope files and directories
2. run broad include filters
3. remove known noise with exclude filters
4. expand context only if needed
5. run a second-pass narrowing filter if the candidate set is still too large

### 4. Aggregate

Default to line-level statistics:

- total matches
- per-file distribution
- recurring phrases or patterns
- representative examples

Only switch to event-block handling when the question clearly depends on stack traces or multi-line context.

### 5. Semantic Narrowing

Use semantic analysis only after filtering has reduced the candidate set to a safe size.

This is allowed when:

- the user query is inherently semantic
- text filtering still leaves mixed but manageable candidates
- near-duplicate messages need light clustering

Any semantic grouping must be labeled as `Inference`, not direct fact.

### 6. Report

Return:

- a Markdown summary for the user
- structured statistics in JSON, and CSV when a table is useful
- representative evidence
- explicit uncertainties and likely blind spots

## Output Shape

Default output sections:

1. `Question`
2. `Scope`
3. `Filter Plan`
4. `Findings`
5. `Evidence`
6. `Uncertainties`
7. `Structured Output`

## Hard Rules

- Never start by reading an entire large log corpus.
- Never use semantic analysis as the first filter layer.
- Never present unsupported inference as fact.
- Never give summary-only output without evidence.
- Default to line-level statistics unless event grouping is truly required.
- Prefer transparent commands over opaque one-off heuristics.

## Red Flags

If you think any of these, stop and tighten the workflow:

- "I'll just scan the whole directory first."
- "This sounds semantic, so I'll classify everything directly."
- "The grep results are big, but a few samples are enough to summarize."
- "These messages look similar enough; I'll merge them."
- "The user only wants the conclusion, so evidence is optional."

## Quick Reference

| Situation | Response |
| --- | --- |
| Huge log directory | sample first, do not full-read |
| Natural-language question | translate to include and exclude filters |
| Too many matches | add another explicit narrowing pass |
| Multi-line stack traces | stay line-based unless event context is required |
| Similar but non-identical messages | separate facts from inferred clusters |
| User asks for "just the summary" | still include representative evidence |

## Common Mistakes

- Treating semantic classification as a replacement for text filtering.
- Jumping from a vague query directly to a full repository-sized scan.
- Mixing direct hits and inferred clusters into one undifferentiated summary.
- Switching to event-level analysis when line-level counting would answer the question.
- Omitting the file scope, filters, or sampling method from the final answer.

## Boundaries

This skill helps answer local log questions with staged filtering and evidence-backed reporting.

It does not guarantee:

- complete understanding of every log line
- real-time monitoring coverage
- automatic root-cause analysis
- correct semantic clustering without uncertainty markers
