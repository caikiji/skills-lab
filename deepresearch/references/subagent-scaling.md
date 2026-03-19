# Subagent Scaling Reference

Use this reference during the Light Probe phase to determine how many
subagents to dispatch and how to shard the codebase.

## Step 1: Estimate Codebase Size

Count source files (exclude `node_modules`, `vendor`, `.git`, build output).
Classify as Small, Medium, or Large.

| Size | File Count |
|------|-----------|
| Small | < 50 |
| Medium | 50–300 |
| Large | > 300 |

## Step 2: Select Subagent Count

| Size | quick | standard | deep |
|------|-------|----------|------|
| Small | 1 | 2 | 3 |
| Medium | 2 | 4 | 6 |
| Large | 3 | 6 | see ceiling rule |

### Deep Mode Ceiling (Large codebases)

In deep mode for large codebases, shard by functional domain with at most
50 files per shard. Cap total subagent count at **12** regardless of
codebase size. If the codebase has more domains than the cap allows,
merge smaller domains and note which ones were combined in `plan.md`.

## Step 3: Define Shards

**Shard by functional domain, not by file count.**

Priority order:
1. Top-level source directories (`src/api/`, `src/core/`, `src/ui/`, etc.)
2. Feature modules when the source tree is flat
3. File-count-based splits only as a last resort

Each shard must:
- Contain at most 50 files (deep mode) or 100 files (quick/standard)
- Have a clear label (e.g., `api-layer`, `core-engine`, `ui-components`)
- Be given to exactly one subagent

## Step 4: Assign Objectives

| Shard Type | Objective |
|-----------|-----------|
| Entry-point shard | Map top-level structure and primary request chains |
| Domain shard | Map module responsibilities, dependencies, and key call paths |
| Config/infra shard | Map build pipeline, environment config, deployment artifacts |

Always give each subagent a `Must-Read Sources` list: the 2–5 files most
likely to be entry points for its shard.
