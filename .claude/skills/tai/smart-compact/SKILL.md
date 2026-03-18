---
name: smart-compact
version: 1.0.0
description: |
  [TAI] Smart context compaction guide. Suggests when and how to compact
  based on tai workflow phases (/plan-ceo → /plan-eng → implement → /review → /ship).
  Use when sessions are long, context is stale, or transitioning between phases.
allowed-tools:
  - Bash
  - Read
---

# Smart Compact

Suggests manual `/compact` at smart points in your workflow rather than relying on arbitrary auto-compaction.

## When to Compact

### tai Workflow Phase Transitions

| Transition | Compact? | Why |
|---|---|---|
| After `/plan-ceo` → before `/plan-eng` | **Yes** | CEO vision is persisted to disk (`~/.tai-skills/projects/`). Free context for engineering details. |
| After `/plan-eng` → before implementation | **Yes** | Plan is captured in tasks/TodoWrite. Free context for code. |
| After implementation → before `/review` | **Maybe** | Keep if review needs implementation context. Compact if the diff speaks for itself. |
| After `/review` → before `/ship` | **Yes** | Review findings are in PR comments and code. Ship needs a clean slate. |
| After `/ship` → before next feature | **Yes** | Previous feature is done. Start fresh. |
| After debugging → before next task | **Yes** | Debug traces pollute context for unrelated work. |
| After a failed approach → retry | **Yes** | Clear dead-end reasoning before trying a new approach. |
| Mid-implementation | **No** | Losing variable names, file paths, and partial state is costly. |

### General Signals

- Session has been running for a long time (200K+ tokens)
- Responses are slowing down or becoming less coherent
- Switching between unrelated tasks within the same session
- After completing a major milestone

## What Survives Compaction

| Persists | Lost |
|---|---|
| CLAUDE.md instructions | Intermediate reasoning and analysis |
| TodoWrite task list | File contents previously read |
| Memory files (`~/.claude/memory/`) | Multi-step conversation context |
| Git state (commits, branches) | Tool call history and counts |
| Files on disk (including `.context/`) | Nuanced preferences stated verbally |
| `.context/compact-resume.md` (auto-saved) | Detailed error traces and debug output |

## How the Hooks Work

Two hooks support smart compaction (installed via `tai claude setup-hooks`):

1. **suggest-compact** (PreToolUse on Edit/Write) — Counts tool calls and nudges you at ~50 calls, then every 25 after that. The nudge appears on stderr; you decide whether to act.

2. **pre-compact** (PreCompact) — Runs automatically before any `/compact`. Saves a resume note to `.context/compact-resume.md` with your current working state so you can pick up where you left off.

## Best Practices

1. **Write important context to files before compacting.** Memory files, `.context/` notes, and TodoWrite all survive.
2. **Compact after planning, not during.** Once the plan is finalized in TodoWrite or a file, compact to start implementation fresh.
3. **Use `/compact` with a summary message.** Example: `/compact Focus on implementing the compact-status CLI command next.`
4. **Read the hook suggestion but decide yourself.** The 50-call threshold is a guideline, not a rule. If you're mid-flow, keep going.
5. **Check session health with `tai claude compact-status`.** See your current tool call count and compaction history.

## Checking Session Health

Run from a terminal (outside or alongside your Claude session):

```bash
tai claude compact-status          # human-readable summary
tai claude compact-status --json   # machine-readable output
```

This reads the session's tool-call counter and compaction log to tell you whether it's time to compact.

## Resume Notes

The pre-compact hook automatically writes `.context/compact-resume.md` before each compaction. This file contains:
- What you were working on (from git status and recent changes)
- Key files involved
- Timestamp of the compaction

This file is gitignored and local-only — it is never committed.
