---
name: flow
version: 1.0.0
description: |
  [TAI] Pipeline orchestrator. Detects where a task sits in the document-driven
  pipeline (plan → approve → build → ship), then drives it forward as far as it
  can — auto-routing to the right plan skill, auto-chaining build steps, auto-fixing
  failures, and halting only at human gates (PRD signoff, ADR accept, spec approve).
  Use when asked to "drive this", "take it from here", "run the pipeline", "flow",
  "do the whole thing", or when a dev wants one command instead of typing eight.
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

This skill orchestrates the Document-Driven pipeline. Read **`docs-philosophy.md`**
(single source of truth) before acting. Non-negotiable:

1. **`docs/prd.md` is HUMAN-owned** — draft/quote, never finalize.
2. **Doc-first order** — spec before code, same PR; no code merges under a spec's
   `code:` path until that spec is `status: approved`.
3. **Never edit `docs/specs/`, `docs/prd.md`, or `docs/decisions/` to match shipped
   code** — flag staleness as `[CRITICAL]`; a human reconciles.
4. **Tests reference Behavior row IDs** (`test_R3_*` / `// covers: SPEC-... R3`).

This skill DELEGATES. It never reimplements plan/build/ship logic — it reads pipeline
state, calls the right existing skill, and chains. All gate philosophy lives in the
delegated skills; flow only decides *which* to run and *when to stop*.

## Preamble (run first)

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_DOCS_DIR="$_REPO_ROOT/docs"
_STATE_DIR="$_REPO_ROOT/.tai/state"
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
mkdir -p "$_STATE_DIR"
# Self-heal: a pre-existing marker means a prior flow died without cleanup. A new run
# owns the session, so clear any orphan first, then write OUR marker with a timestamp,
# and trap so Ctrl-C / TERM still clean up (SIGKILL/context-reset won't — hence timestamp).
rm -f "$_STATE_DIR/flow-session"
trap 'rm -f "$_STATE_DIR/flow-session"' EXIT INT TERM
date +%s > "$_STATE_DIR/flow-session"   # signals downstream skills to skip redundant preamble
echo "BRANCH: $_BRANCH"
echo "DOCS: $_DOCS_DIR"
ls "$_DOCS_DIR" 2>/dev/null || echo "NO docs/ — repo not initialized"
```

Downstream skills that honor the marker should treat it as **absent if older than ~2h**
(`flow-session` holds an epoch timestamp): `[ -f F ] && [ $(( $(date +%s) - $(cat F) )) -lt 7200 ]`.
A stale marker from a crashed run then can't silently suppress a later standalone skill's
preamble.

Then read **`docs-philosophy.md` AND `docs-conventions.md` ONCE** for this whole flow run
(the framework rules + the shared interaction conventions — AskUserQuestion Format,
Boil-the-Lake, field-report). The `flow-session` marker tells every delegated skill these
are already loaded, so they skip re-reading — load them here, not 5× downstream.

**Always remove the marker before flow returns** (at any HALT, gate, failure, or DONE):

```bash
rm -f "$_REPO_ROOT/.tai/state/flow-session"
```

A stale marker would make a later standalone skill run skip its own preamble. Treat
removal as mandatory cleanup on every exit path.

## The Pipeline — flow = plan half + build half (ADR 0006)

`/tai-flow` is the **one-shot orchestrator**: it delegates to the two halves and never
duplicates their logic.

```
/tai-flow-plan      S0 init → S1 plan (talk-then-write) → /tai-plan-review (converge)
                    → GATE A/B/C (human approves)        →  specs approved
        │
        ▼  (once the relevant specs are approved)
/tai-flow-execute   /tai-execute → /review → /qa → /ship
```

## Step 1 — Detect stage, then delegate

Read state (don't guess): `ls docs/`; is `prd.md` signed; glob `docs/specs/*.md` statuses.

- **Any relevant spec missing / `draft` / a spec-evolution (implemented but the change
  exceeds its Behavior rows), or no docs/ yet** → the plan is not locked → invoke
  **`/tai-flow-plan`**. It inits, plans (talk-then-write), runs `/tai-plan-review` to
  converge, and halts at the human gates. When it reports DONE-PLAN (specs approved),
  continue below.
- **The relevant spec(s) already `approved` (or `implemented`) and code not yet shipped**
  → invoke **`/tai-flow-execute`** (build → review → qa → ship).

Never skip a gate; `/tai-flow-plan` owns them. Never build against an unapproved spec;
`/tai-flow-execute` enforces that precondition.

## Step 2 — Run end-to-end

For a fresh task, run `/tai-flow-plan` first; when it reaches DONE-PLAN, run
`/tai-flow-execute`. If invoked mid-pipeline, Step 1's detection picks the right half to
(re-)enter. `/tai-flow` is idempotent — re-running at a completed stage reports DONE.

## Report

```
flow: {plan | build | done}
  ⏸ paused at: {gate (in flow-plan) / failure (in flow-execute)}
  ✅ DONE: shipped (docs maintained live)
  next: {what to run next, or what the human must do}
```
