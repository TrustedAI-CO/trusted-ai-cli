---
name: flow-plan
version: 1.0.0
description: |
  [TAI] The PLAN half of the pipeline (ADR 0006). Detects stage, auto-routes to the right
  plan skill (talk-then-write), runs /tai-plan-review to converge the plan, then halts at
  the human gates (PRD sign / ADR accept / spec approve). STOPS once the relevant specs are
  approved — writes no code. Use when asked to "plan this", "just plan", "draft the spec",
  "flow plan", or to do planning without building. For the build half, use /tai-flow-execute;
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

Orchestrates the PLAN half of the Document-Driven pipeline. Read **`docs-philosophy.md`**
(single source of truth). Non-negotiable: `docs/prd.md` is HUMAN-owned; doc-first order
(spec before code, approved before code merges); never edit a source layer to match code.

This skill DELEGATES — it routes to plan skills + `/tai-plan-review` and stops at gates.

## Conventions

Shared conventions live in `docs-conventions.md` (ADR 0005). Loaded once here for the run.

## Preamble (run first)

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_STATE_DIR="$_REPO_ROOT/.tai/state"; mkdir -p "$_STATE_DIR"
_MARK="$_STATE_DIR/flow-session"
# Inherited LIVE marker (<2h) means a parent /tai-flow already owns the session and loaded
# the framework — don't clobber it, don't read philosophy again, don't remove it on exit.
if [ -f "$_MARK" ] && [ $(( $(date +%s) - $(cat "$_MARK") )) -lt 7200 ]; then _OWN=0; else
  _OWN=1; date +%s > "$_MARK"; trap 'rm -f "$_MARK"' EXIT INT TERM; fi
git branch --show-current
ls "$_REPO_ROOT/docs" 2>/dev/null || echo "NO docs/"
```
If `_OWN=1`, read `docs-philosophy.md` + `docs-conventions.md` ONCE here and remove the
marker on every exit (gate/halt/done). If `_OWN=0`, a parent flow already loaded them — skip.

## Stages (this skill owns S0 → gates)

```
[S0 init]   docs/ missing            → /docs-init
[S1 plan]   no spec / task unclear   → plan cluster (auto-route below), talk-then-write
[S1.5 review] plan drafted           → /tai-plan-review (2 parallel reviewers, converge)
[GATE A]    prd.md unsigned          → HALT: human signs PRD
[GATE B]    ADR not accepted         → HALT: human accepts ADR
[GATE C]    spec not approved        → HALT: human approves spec
[DONE-PLAN] relevant specs approved  → tell the dev to run /tai-flow-execute
```

## Step 1 — Detect stage
Read state, don't guess; never skip a gate:
1. `ls docs/` — missing → S0 (`/docs-init`), then re-detect.
2. `docs/prd.md` signed? missing/stub → S1 plan (or `/plan-product` if no product intent).
3. Glob `docs/specs/*.md`, read each `status:`:
   - no spec covering the task → S1 plan.
   - `draft` → GATE C.
   - `implemented` but the change exceeds its Behavior rows → **spec evolution** → S1 plan
     to revise. Editing a spec's Interface/Behavior resets it to `draft` and clears
     `approved_at`, so it re-flows through GATE C.
4. Any depended-on `docs/decisions/*.md` not `accepted` → GATE B.

**Spec-evolution reset backstop:** after a plan skill revises an evolved spec, verify its
`status` is now `draft`. If a spec whose Interface/Behavior just changed is still
`implemented`, the reset was missed — force it back to `draft` and GATE C, never advance.
This is the guard against silently skipping the human gate on a shipped-surface change.

## Step 2 — Plan cluster auto-routing
When in S1, pick ONE plan skill (do not run all):

| Task signal | Route to |
|-------------|----------|
| Scope/ambition, "think bigger", strategy | `/plan-ceo` |
| Clear feature, needs architecture + spec contracts | `/plan-eng` (default) |
| UI/UX-heavy | `/plan-design` |

`/plan-product` is out of scope — if product intent is missing, HALT and tell the dev to
run `/plan-product` first. The plan skill presents the plan VISUALLY and confirms before
writing (talk-then-write, ADR 0004). State your routing choice + the signal.

## Step 3 — Plan review (converge before the gate)
After the plan skill drafts specs/ADRs, run **`/tai-plan-review`** — it spawns 2 parallel
blind reviewers and iterates until they converge (nothing CRITICAL/HIGH), hardening the
draft. The human then approves a *reviewed* plan, not a first draft. Specs stay
`status: draft` through review; plan-review never flips status.

## Step 4 — Human gates (HALT)
At GATE A/B/C present the (now reviewed) doc + offer interactive approval. The gate exists
so a *human decides* — an explicit in-session approval IS that decision; auto-flipping on
agent judgment alone is banned.
- **Approve** → flow-plan writes `status:` (`draft`→`approved` / `proposed`→`accepted` /
  PRD→signed), stamps `approved_at` for specs, commits, continues to the next gate.
- **Request changes** → route back to the plan skill to revise, re-run plan-review,
  re-present.
Async/headless: do NOT flip; print the gate report and HALT.

## Step 5 — Done (plan)
When the relevant specs are `approved`:
```
flow-plan: DONE — plan approved
  ✓ specs approved: {ids}   ADRs accepted: {ids}
  → next: run /tai-flow-execute to build → review → qa → ship
```
