# plan.md Template

This file is the main agent's persistent anchor. Write it at the end of the
Light Probe phase and update it at the end of every subsequent phase.

## Template

```markdown
# DeepResearch — Research Plan
status: in_progress
depth: quick | standard | deep
repo: <repo-name>
started: YYYY-MM-DD

## Phase
current: light-probe | dispatching | researching | synthesis | generating | done

## Shard Map
- chunk-01: <shard-label> (<file-count> files)
- chunk-02: <shard-label> (<file-count> files)
...

## Chunks
- [ ] chunk-01.md
- [ ] chunk-02.md
...

## Synthesis
- [ ] synthesis.md

## Output
- [ ] output/YYYY-MM-DD-<repo>-research.md

## Notes
<Record stop reason if context limit was reached, or any anomalies.>
```

## Resume Logic

When the main agent starts (or restarts), read `plan.md` first:

| `current` phase | `plan.md` exists? | Action |
|----------------|-------------------|--------|
| — | No | Run Light Probe → write `plan.md` |
| `light-probe` | Yes, probe incomplete | Re-run Light Probe from scratch → overwrite `plan.md` |
| `dispatching` or `researching` | Yes, chunks incomplete | Re-dispatch missing chunk subagents |
| `synthesis` | Yes, all chunks done | Read chunks in batches → write `synthesis.md` |
| `generating` | Yes, synthesis done | Read `synthesis.md` → write `output/YYYY-MM-DD-<repo>-research.md` |
| `done` | Yes | Report that research is already complete |

## Batch Synthesis Rule

If total chunk content is large (does not fit comfortably in context — typically
more than 4 chunks, or any number of large chunks in deep mode), read chunks in
batches of 3. Write an intermediate partial synthesis per batch, then merge all
partial syntheses into the final `synthesis.md`. Record batch boundaries in
`plan.md`. When in doubt, prefer batching.
