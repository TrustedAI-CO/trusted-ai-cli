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
touch "$_STATE_DIR/flow-session"   # signals downstream skills to skip redundant preamble
echo "BRANCH: $_BRANCH"
echo "DOCS: $_DOCS_DIR"
ls "$_DOCS_DIR" 2>/dev/null || echo "NO docs/ — repo not initialized"
```

Then read **`docs-philosophy.md` ONCE** for this whole flow run. The `flow-session`
marker tells every delegated skill the framework + interaction conventions are already
loaded, so they skip re-reading it — load it here, not 5 times downstream.

**Always remove the marker before flow returns** (at any HALT, gate, failure, or DONE):

```bash
rm -f "$_REPO_ROOT/.tai/state/flow-session"
```

A stale marker would make a later standalone skill run skip its own preamble. Treat
removal as mandatory cleanup on every exit path.

## The Pipeline (stages flow advances through)

```
[S0 init]   docs/ missing            → /docs-init
[S1 plan]   no spec, or task unclear → plan cluster (auto-route, see below)
[GATE A]    prd.md draft/unsigned    → HALT: human signs PRD wording
[GATE B]    ADR status != accepted   → HALT: human flips status: accepted
[GATE C]    spec status != approved  → HALT: human flips status: approved
[S2 build]  specs approved           → /tai-execute (auto-picks solo vs team)
[S3 review] code written             → /review
[S4 qa]     review clean             → /qa
[S5 ship]   qa clean                 → /ship
[S6 docs]   shipped                  → /docs-update
[DONE]
```

## Step 1 — Detect Stage

Read state, do not guess from conversation:

1. `ls docs/` — present? If not → **S0**, run `/docs-init`, then re-detect.
2. `docs/prd.md` exists with signed-off wording? Frontmatter present, not a bare
   draft stub? If missing/stub → **S1 plan**.
3. Glob `docs/specs/*.md`. Read frontmatter `status:` of each.
   - No spec covering the current task → **S1 plan**.
   - Spec exists, `status: draft` → **GATE C** (halt for human approval).
   - Spec exists and `status: implemented` BUT the requested change exceeds what its
     Behavior rows cover (a new option, a new rule, a changed interface) → this is a
     **spec evolution**: route to **S1 plan** to revise the spec. Per the philosophy
     "Spec Evolution" rule, editing its Interface/Behavior resets it to `draft` and
     clears `approved_at`/`baseline_sha`/`autonomous_ok` → it then flows through
     **GATE C** for re-approval. Do NOT let code for the new behavior proceed against an
     `implemented` spec that doesn't cover it.
     **Verify the reset before routing onward:** after plan-eng revises an evolved spec,
     confirm its `status` is now `draft` (plan-eng owns this write). If a spec whose
     Interface/Behavior just changed is still `implemented`, the reset was missed — do
     NOT advance to build; force it back to `draft` and GATE C. This is the backstop
     against silently skipping the human gate on a shipped-surface change.
4. Any `docs/decisions/*.md` with `status:` not `accepted` that the task depends on
   → **GATE B**.
5. All relevant specs `approved`, code not yet matching → **S2 build**.
6. Code present but not reviewed/qa'd/shipped this branch → walk S3→S6 using
   `.tai/state/` logs + git status to find the highest completed step.

When ambiguous which stage, state your reading and the evidence, then proceed with
the earliest plausible stage (never skip a gate).

## Step 2 — Plan Cluster Auto-Routing

When in **S1**, pick ONE plan skill from the task's nature. Do not run all three.

| Task signal | Route to |
|-------------|----------|
| Scope/ambition question, "think bigger", strategy, business bet | `/plan-ceo` |
| Clear feature, needs architecture + spec contracts before code | `/plan-eng` |
| UI/UX-heavy, interaction/IA/accessibility decisions | `/plan-design` |

Heuristic: default to `/plan-eng` to author specs once intent is clear. `/plan-ceo`
and `/plan-design` are invoked only when the task explicitly raises scope or design
questions. `/plan-product` is OUT of flow scope — product discovery ("is this worth
building") is a human-driven step run manually before `/flow`. If the task has no clear
product intent yet, HALT and tell the dev to run `/plan-product` first. State your
routing choice + the signal that drove it before delegating.

After a plan skill produces draft specs/ADRs/PRD → advance to the matching GATE and HALT.

## Step 3 — Human Gates (HALT points)

At GATE A/B/C the human must consciously authorize before flow crosses. The gate
exists so a *human decides* — NOT so the agent is forbidden from writing the byte.
An explicit in-session approval IS that decision. Auto-flipping on agent judgment is
banned; flipping because the human just clicked Approve is allowed.

Present the doc for decision, then offer interactive approval:

```
⏸  GATE {A|B|C} — needs human decision

  What: {PRD wording | ADR 0003-slug | SPEC-auth-login}
  Status: {draft | proposed}  →  needs: {signed | accepted | approved}
  File: docs/{path}
  Summary: {2-3 line plain-English summary of what's being approved}
  Why it matters: {one line}
```

Then `AskUserQuestion`:
- **Approve** → flow writes the `status:` field (`draft`→`approved`, `proposed`→
  `accepted`, PRD→signed). **For a spec, in the SAME write also stamp the staleness
  anchor:** `approved_at: <current ISO timestamp>` and `baseline_sha: $(git rev-parse
  HEAD)`. These are non-negotiable — `/tai-loop`'s staleness check diffs against
  `baseline_sha`; leaving it empty silently breaks autonomous re-validation. Commit the
  frontmatter change, then CONTINUE the pipeline. The click is the authorization; flow
  only types the keystroke the human ordered.
- **Request changes** → flow records the feedback, routes back to the matching plan
  skill to revise the draft, then re-presents the gate.

**Async fallback:** if running headless / no human present, do NOT flip. Print the gate
report and HALT — the human edits `status:` in the file directly later and re-runs
`/flow`. Never flip a status on agent judgment alone in either mode.

## Step 4 — Build Cluster Auto-Chain

Once gates clear, chain WITHOUT asking between steps:

```
/tai-execute (auto-picks solo vs team)
  → /review
    → /qa
      → /ship
        → /docs-update
```

- `/tai-execute` auto-selects its strategy: it uses the parallel team strategy when
  `docs/plan/tasks.md` has ≥2 independent sub-phases, otherwise the solo
  single-context strategy. No manual choice needed.
- Pass each step's output to the next. Announce each transition with one line:
  `▶ S3 review (specs: 3, diff: 412 lines)`.
- Surface to the human only on: failure (see Step 5), a new `docs/REVIEW.md` entry,
  or DONE.

## Step 5 — Auto-Fix + Retry on Failure

When a step fails (test fail, review `[CRITICAL]`/`[HIGH]`, qa bug, ship gate block):

1. **Classify** the failure: implementation bug, spec gap, or environment.
2. **Spawn a fix pass** with the right skill:
   - Test/logic failure or qa bug → `/investigate` (root-cause) then `/tai-execute`
     to apply the verified fix.
   - Review CRITICAL/HIGH → feed findings back to `/tai-execute` for targeted fix.
3. **Retry the failed step ONCE.** If it now passes → resume the chain.
4. **If it still fails → HALT.** Print failure + repro + what was tried:

```
✗ S{n} {step} failed after auto-fix retry

  Failure: {message, quoted exactly}
  Repro: {command / steps}
  Auto-fix tried: {what investigate/execute changed}
  Still failing because: {hypothesis}

  Needs human. Pipeline paused at S{n}.
```

Never edit a source layer (spec/PRD/ADR) to make a step pass — that inverts doc-first
order. If the failure is a spec/code mismatch where the spec is wrong, flag `[CRITICAL]`
and HALT for human reconciliation.

## Step 6 — Report

End every run with a one-block status so the dev knows where things stand:

```
flow: {stage reached}
  ✓ done: {steps completed this run}
  ⏸ paused at: {gate / failure}  — OR —  ✅ DONE: shipped + docs updated
  next: {what /flow will do on next invocation, or what human must do}
```

## Loop Behavior

`/flow` advances as far as it can per invocation, then halts at the next gate/failure.
The dev re-runs `/flow` after clearing a gate. It is idempotent: re-running at a
completed stage detects completion and reports DONE rather than redoing work.
