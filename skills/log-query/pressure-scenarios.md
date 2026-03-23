# Log Query Pressure Scenarios

Use these scenarios to validate whether the skill stays disciplined when logs are large, the request is vague, or the user pressures the agent to skip evidence.

## How to Use

For each scenario:

1. Present only the scenario prompt to an agent.
2. Observe baseline behavior without extra steering.
3. Record whether the agent samples first, translates the request into explicit filters, and preserves evidence.
4. Re-run with the skill active.
5. Compare the result against the expected behavior below.

## Scenario 1: Huge Log Directory, Hurry Up

**Pressure:** The user wants an answer fast and encourages a broad scan.

**Prompt:**

```text
This log directory is huge, but I just need a quick answer. Tell me what errors are happening most often.
```

**Expected behavior with skill:**

- agent samples first instead of reading everything immediately
- agent states a filtering plan before broad scanning
- final answer includes evidence, not only a summary

**Failure signs:**

- immediate full-directory read
- no sampling step
- summary with no representative lines

## Scenario 2: Purely Semantic Request

**Pressure:** The request is thematic and easy to interpret too broadly.

**Prompt:**

```text
Find logs that look like users had a bad checkout experience and summarize the main issues.
```

**Expected behavior with skill:**

- agent translates the theme into explicit include and exclude filters first
- semantic analysis is delayed until the candidate set is manageable
- any semantic clustering is marked as inference

**Failure signs:**

- direct whole-corpus semantic classification
- no explicit filter plan
- inferred categories presented as settled fact

## Scenario 3: Multi-Layer Include And Exclude

**Pressure:** The user wants several rules combined, which can tempt the agent into skipping structure.

**Prompt:**

```text
Count logs related to order failure, but exclude health checks, retries that later succeeded, and test traffic.
```

**Expected behavior with skill:**

- agent breaks the request into multiple filtering passes
- include and exclude logic are separated clearly
- output explains what was filtered out

**Failure signs:**

- one vague search term and no narrowing passes
- excludes ignored or handled informally
- findings reported without filter traceability

## Scenario 4: Stack Trace Temptation

**Pressure:** The logs contain multi-line exceptions, but the user only asked for counts and patterns.

**Prompt:**

```text
Summarize the main exception patterns in these app logs.
```

**Expected behavior with skill:**

- agent starts with line-level analysis
- event-block handling is only introduced if needed
- the answer still includes representative evidence

**Failure signs:**

- immediate switch to heavyweight event extraction
- no explanation for changing the unit of analysis
- lost count accuracy due to ad hoc stack-trace grouping

## Scenario 5: Summary Without Evidence Pressure

**Pressure:** The user explicitly asks for only the conclusion.

**Prompt:**

```text
Just give me the gist of what is going wrong in these logs. I don't need the evidence.
```

**Expected behavior with skill:**

- agent stays concise but still includes representative evidence
- findings are separated from uncertainties
- output remains auditable

**Failure signs:**

- conclusion-only answer
- no log excerpts or representative hits
- no indication of uncertainty or scope

## Scenario 6: Similar Messages, Different Causes

**Pressure:** Messages are close enough that careless clustering would merge them incorrectly.

**Prompt:**

```text
Group the errors in this directory into the main patterns and tell me the counts.
```

**Expected behavior with skill:**

- agent distinguishes direct textual patterns from inferred clusters
- similar messages are not merged blindly
- uncertain grouping is called out explicitly

**Failure signs:**

- aggressive merging based on surface similarity
- no distinction between fact and inference
- counts reported for clusters that were never justified

## Evaluation Checklist

The skill is behaving correctly if the agent consistently:

- samples before broad scanning
- translates natural-language requests into explicit filters
- applies multiple narrowing passes when needed
- keeps semantic analysis after text filtering
- defaults to line-level statistics
- includes representative evidence in the final answer
- labels inference separately from direct findings
