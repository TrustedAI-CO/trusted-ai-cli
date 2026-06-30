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
_MARK="$_STATE_DIR/flow-session"
# Inherited LIVE marker (<2h) means a parent /tai-flow owns the session + already loaded the
# framework — don't clobber it, don't re-read philosophy, don't remove it on exit.
if [ -f "$_MARK" ] && [ $(( $(date +%s) - $(cat "$_MARK") )) -lt 7200 ]; then _OWN=0; else
  _OWN=1; date +%s > "$_MARK"; trap 'rm -f "$_MARK"' INT TERM; fi
# No EXIT trap: each Bash call is its own shell; EXIT would delete the marker immediately.
# Remove it explicitly on every exit path (halt/done); 2h timestamp self-heals crashes.
git branch --show-current
```
If `_OWN=1`, read `docs-philosophy.md` + `docs-conventions.md` ONCE and remove the marker on
every exit. If `_OWN=0`, a parent flow already loaded them — skip.

## Precondition — governing spec approved AND covers the task

Glob `docs/specs/*.md`; read the frontmatter `status:` and Behavior rows of the spec(s)
governing this task. Decide per spec:

- **`approved` OR `implemented`, and its Behavior rows cover the task** → PROCEED to build.
  (`implemented` is a built `approved` spec; flow routes both here.)
- **missing, or `draft`** → STOP. Planning isn't done — tell the dev to run
  **`/tai-flow-plan`** first. Never build against a missing/unapproved spec (doc-first gate).
- **`approved` OR `implemented` BUT the requested change exceeds its Behavior rows** (new
  option, new rule, changed interface) → this is a **spec evolution**. STOP and route to
  **`/tai-flow-plan`**: the spec must be revised, which resets it to `draft` and re-gates
  via GATE C. Building behavior never approved at GATE C — against a stale `approved` or
  `implemented` spec — skips the human gate. Flag `[CRITICAL]` if asked to proceed anyway.

When invoked standalone (not via `/tai-flow`), also confirm `docs/prd.md` is signed (GATE A)
and the spec's depended-on ADRs are `accepted` (GATE B) before building — a hand-edited
`approved` spec could sit atop an unsigned PRD or un-accepted ADR. **Whether a change "exceeds Behavior rows" is a judgment call — resolve
ambiguity toward STOP/`/tai-flow-plan`, never toward proceed.**

## Resume — don't redo completed steps

Before starting, find the highest completed build step from `.tai/state/` logs + `git
status` (code present? review entry in `docs/REVIEW.md`? ship/changelog done?). Resume at
the first incomplete step rather than restarting at `/tai-execute`. Re-running at a
finished chain detects completion and reports DONE — idempotent.

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
