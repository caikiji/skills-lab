---
name: deepresearch
description: User-facing codebase research skill. Produces a layered Markdown report with Mermaid diagrams, from shallow project overview to deep module analysis. Use when the user asks to deeply understand a codebase, generate a research report, or map how a repository works. Accepts a depth parameter: quick, standard, or deep.
---

# DeepResearch

Produce a layered codebase research document for the user. The output is designed
to be read directly — not to package context for downstream agents. For agent-context
packaging, use `context-research-orchestrator` instead.

## Phase 0: Intake

Accept:
- `depth`: `quick` | `standard` | `deep` (default: `standard`)
- `target`: path to the repository root (default: current working directory)

Determine the session directory path:
```
docs/deepresearch/<repo-name>-<YYYY-MM-DD>/
```

Determine `<repo-name>` from: (1) the final path component of the `git remote get-url origin` URL (strip `.git` suffix if present), or (2) the root directory name if no git remote exists.

## Phase 1: Resume Check

Before doing any research, check whether `state/plan.md` already exists inside the
session directory.

Read [references/plan-template.md](references/plan-template.md) for the resume
logic table. Follow it exactly:

- If `plan.md` does not exist → proceed to Phase 2 (Light Probe)
- If `plan.md` exists → skip to whichever phase is indicated by `current`

## Phase 2: Light Probe

Perform the minimum scan needed to estimate codebase size and define shards:

1. Count source files (exclude `node_modules`, `vendor`, `.git`, build output)
2. List top-level directories
3. Identify obvious functional domains from directory names

Read [references/subagent-scaling.md](references/subagent-scaling.md) to select
subagent count and define shards.

Write `state/plan.md` using the template in [references/plan-template.md](references/plan-template.md).
Set `current: dispatching`.

Create `state/chunks/` directory.

## Phase 3: Parallel Research

Dispatch subagents in parallel using the `dispatching-parallel-agents` skill.

If the `dispatching-parallel-agents` skill is not available, dispatch subagents
sequentially instead. Mark each chunk complete in `plan.md` as it finishes before
dispatching the next.

**Mandatory before any dispatch:** Read `agents/exploration-agent.md` in full.
Paste its complete content verbatim at the top of every subagent prompt, before
any task-specific fields. Dispatching without the embedded role content is not
allowed — the subagent will not know its constraints or output format otherwise.

For each shard, construct a dispatch packet with all required fields (see
[agents/exploration-agent.md](agents/exploration-agent.md)):

| Field | Value |
|-------|-------|
| `Role` | `read-only-exploration-agent` |
| `Objective` | Analyze this shard: map structure, key modules, and flows |
| `Shard` | List of directories/files for this shard |
| `Depth` | The depth parameter from Phase 0 |
| `Must-Read Sources` | 2–5 likely entry-point files in the shard |
| `Output Contract` | `state/chunks/chunk-NN.md` (absolute path) |
| `Stop Conditions` | Report if shard requires context outside its boundaries |

After dispatch, update `plan.md`: set `current: researching`.

As chunks complete, mark them in `plan.md`. If a chunk fails or is missing,
re-dispatch that subagent before proceeding.

## Phase 4: Synthesis

When all chunks are marked complete in `plan.md`:

Estimate total chunk content size before synthesizing.

If total chunk content is small (all chunks fit comfortably in context — typically
chunks ≤ 4 for quick/standard mode on a Small or Medium codebase): read all chunks
and write `state/synthesis.md` in one pass.

Otherwise: process in batches of 3 (see batch synthesis rule in
[references/plan-template.md](references/plan-template.md)). Write one partial
synthesis per batch, then merge into `state/synthesis.md`.

When in doubt, prefer batching over a single pass.

Update `plan.md`: mark synthesis complete, set `current: generating`.

**Context limit rule:** If synthesizing all chunks would exceed your context
window, write whatever partial synthesis you have completed to `synthesis.md`,
note the stopping point in `plan.md` under `Notes`, and stop. The next round
will resume from this point.

## Phase 5: Document Generation

Read `state/synthesis.md`. Generate the final document following the template
and mode coverage matrix in [references/output-document-template.md](references/output-document-template.md).

Write to: `output/YYYY-MM-DD-<repo>-research.md` (relative to the session directory).

Update `plan.md`: mark output complete, set `current: done`.

## Completion

Report the output path to the user.

To convert the Markdown output to PDF or DOCX with real rendered Mermaid diagrams,
use the bundled conversion script:

```bash
python deepresearch/scripts/convert.py <output/report.md> [--format pdf|docx|both]
```

**Requirements:**
- Node.js + `npm install -g @mermaid-js/mermaid-cli`
- Python + `pip install python-docx reportlab`

The script renders each Mermaid code block to a PNG via mmdc (the official
Mermaid CLI), then embeds the images into the final PDF or DOCX.
See `scripts/convert.py` for full usage and `--out-dir` option.

## Non-Goals

Do not:
- modify any project files during research
- use this skill when the output is for downstream agents (use `context-research-orchestrator`)
- attempt to complete Phase 3–5 in one context window for large/deep runs — let the state system do its job
