---
name: flow-execute
version: 1.0.0
description: |
  [TAI] The BUILD half of the pipeline (ADR 0006). Assumes the relevant specs are already
  approved, then auto-chains /tai-execute → /review → /qa → /ship, with auto-fix-retry on
  failure and a QA surface-type guard. Use when asked to "execute the plan", "build it",
  "flow execute", or to run the build half after planning. For planning, use /tai-flow-plan;
  for both, use /tai-flow.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
  - Skill
  - Agent
---

## Framework Guardrails (read first)

Orchestrates the BUILD half. Read **`docs-philosophy.md`** (single source of truth).
Non-negotiable: **no code merges under a spec's `code:` path until that spec is
`status: approved`**; never edit a source layer (spec/PRD/ADR) to make a step pass — flag
`[CRITICAL]` and HALT for human reconciliation.

This skill DELEGATES — it chains the build stage skills, never reimplements them.

## Conventions

Shared conventions live in `docs-conventions.md` (ADR 0005). Loaded once here for the run.

## Preamble (run first)

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_STATE_DIR="$_REPO_ROOT/.tai/state"; mkdir -p "$_STATE_DIR"
rm -f "$_STATE_DIR/flow-session"
trap 'rm -f "$_STATE_DIR/flow-session"' EXIT INT TERM
date +%s > "$_STATE_DIR/flow-session"
git branch --show-current
```
Read `docs-philosophy.md` + `docs-conventions.md` ONCE. Remove the marker on every exit.

## Precondition — specs approved

Glob `docs/specs/*.md`. If the spec(s) governing this task are NOT `status: approved`
(still `draft`), STOP: this is the plan half's job — tell the dev to run **`/tai-flow-plan`**
first. Do NOT build against an unapproved or missing spec (doc-first gate).

## Build chain (auto-chain, no asking between steps)

```
/tai-execute (auto-picks solo vs team; maintains derived docs live)
  → /review        (2 parallel blind reviewers, converge — ADR 0003)
    → /qa          (web only; CLI/lib → smoke check or skip — see guard)
      → /ship      (verifies derived docs in sync; ends the chain)
```

- `/tai-execute` auto-selects solo vs team (team when `docs/plan/tasks.md` has ≥2
  independent sub-phases).
- **QA surface-type guard.** `/qa` is a web/browser tester. Before it, detect surface type:
  web app (frontend / a servable target) → run `/qa`; CLI/library/backend (no servable UI)
  → do NOT run `/qa` (it emits a vacuous "clean" report = false confidence). Instead run a
  CLI/lib smoke check (invoke the surface, assert exit codes/stdout/file effects/error
  paths vs the Behavior rows), or SKIP with an explicit line. Never a silent green on a
  non-web target.
- Announce each transition one line (`▶ review (specs: 3, diff: 412 lines)`). Surface to
  the human only on failure, a new `docs/REVIEW.md` entry, or DONE.

## Auto-fix + retry on failure

When a step fails (test fail, review CRITICAL/HIGH, qa bug, ship gate block):
1. Classify (impl bug / spec gap / environment).
2. Fix: test/qa bug → `/investigate` then `/tai-execute`; review CRITICAL/HIGH → feed back
   to `/tai-execute`.
3. Retry the failed step ONCE. Passes → resume. Still fails → HALT with failure + repro +
   what was tried.
Never edit a source layer to pass. If the spec is wrong → `[CRITICAL]` + HALT (a spec fix
is the plan half's job via `/tai-flow-plan`).

## Report

```
flow-execute: {stage reached}
  ✓ done: {steps completed}
  ⏸ paused at: {failure}  — OR —  ✅ DONE: shipped (docs maintained live)
  next: {what a re-run does, or what the human must fix}
```
