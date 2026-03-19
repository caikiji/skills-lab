# Delegation Guidance

Use this file only when deciding whether to dispatch read-only exploration subagents or when packaging their work.

## Decision Criteria

Stay inline when:

- the task is narrow
- evidence is concentrated in a few files
- the primary agent can already explain the likely boundaries and risks

Dispatch a few read-only exploration subagents when:

- evidence is spread across multiple separable modules
- later planning or orchestration needs broader context
- the repository is large enough that serial exploration is wasteful

Use multi-round exploration when:

- shared files appear across many candidate areas
- the search surface is still poorly mapped
- early parallel exploration is likely to produce conflicting packets

## Read-Only Exploration Packet Template

```md
## Exploration Task
- Objective:
- Search area:
- Questions to answer:
- Must-read sources:
  - [path]
- Helpful reference sources:
  - [path]
- Required output:
  - summary of findings
  - source references with anchors
  - open questions
  - suspected contention surfaces
- Constraints:
  - read-only
  - no edits
  - no rule invention
  - report unsupported conclusions as uncertainty
```

## Synthesis Guidance

When combining multiple exploration results:

1. Merge duplicate findings into one stronger statement.
2. Preserve the best source references instead of paraphrasing away the evidence.
3. If two summaries disagree, downgrade the combined conclusion to `Inference` or `Open Question` until the primary agent resolves it from source material.
4. Keep task-relevant detail in task-specific blocks and reusable structure in global theme blocks.
5. If a child summary makes a strong claim without support, do not promote it to `Fact`.

## Failure Handling

If anchors cannot be relocated:

- mark the affected claim as stale-risk
- keep the source path, but do not treat the claim as fresh without re-checking

If evidence conflicts:

- identify whether the conflict is temporal, contextual, or interpretive
- prefer authoritative source files over summaries
- escalate if the repository does not settle the disagreement

If the worktree changes during research:

- record that the context pack reflects a moving target
- refresh the most important references before finalizing

If subagent scopes overlap:

- do not merge them blindly
- reframe the packets around non-overlapping questions or ownership
- preserve any useful evidence already gathered, but mark overlap as a confidence risk
