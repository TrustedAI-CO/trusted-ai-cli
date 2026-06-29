---
name: loop
version: 1.0.0
description: |
  [TAI] Autonomous loop driver. Drains docs/plan/backlog.md by running the pipeline
  over approved, non-stale specs WITHOUT a human at the keyboard. Builds one item at a
  time (serial), auto-approves low-risk specs by policy, parks high-risk or stale ones
  for async human review (never blocks the loop), and pushes gate decisions to the
  human's phone. The walk-away / close-the-laptop mode. Use when asked to "run the
  loop", "drain the backlog", "work autonomously", "tai loop", "keep building", or
  "do this while I'm away". For one interactive advance instead, use /tai-flow.
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

## What this is

`/tai-loop` is the **trigger/loop layer** over `/tai-flow`. Flow advances one item one
step; loop runs flow repeatedly over the backlog until nothing approved is left to
build. Read **`docs-philosophy.md`** (single source of truth) before acting.

> **The intelligence is in the loop, not the agent.** The loop's job is: find work →
> check it's buildable → drive flow → record outcome → repeat. It does NOT reimplement
> plan/build/ship — it calls `/tai-flow`, which calls the pipeline skills.

Non-negotiable (same as flow):
1. **`docs/prd.md` is HUMAN-owned.**
2. **Doc-first order** — no code merges under a spec's `code:` until `status: approved`.
3. **Never edit `docs/specs/`, `docs/prd.md`, `docs/decisions/` to match shipped code.**

## Design (the 4 decisions, locked)

1. **Serial.** Build one spec at a time. This is why there are no content hashes, no
   topological sort, no container locks — a serial loop can't race itself. Parallelism
   is a later optimization, added only if the loop is too slow.
2. **Park, don't halt.** The loop never stalls on one item needing a human. It parks
   that item and moves to the next buildable one. It sleeps only when the *approved +
   non-stale* queue is empty.
3. **Risk-tiered auto-approve.** Low-risk specs are approved by policy and built without
   a human. High-risk specs are always parked for human review.
4. **Async gate, pushed to human.** Parked items go to `docs/REVIEW.md` and a phone
   push. The human approves out-of-band (taps Approve); the loop picks them up next pass.

## Preamble (run first)

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_DOCS_DIR="$_REPO_ROOT/docs"
_STATE_DIR="$_REPO_ROOT/.tai/state"
_BACKLOG="$_DOCS_DIR/plan/backlog.md"
mkdir -p "$_STATE_DIR"
echo "BACKLOG: $_BACKLOG"
ls "$_DOCS_DIR/specs/" 2>/dev/null || echo "NO specs — nothing to loop on"
```

Loop bookkeeping (current item, pass count) lives in `.tai/state/` — **disposable
cache, rebuildable**. Durable memory (what's approved, what's parked, what's deferred)
lives in committed `docs/` only. A fresh clone / cloud run must work from `docs/` alone.

## Risk Policy (who needs a human)

Default policy. A project MAY override in `docs/prd.md` (a "Loop policy" section).

| Tier | Spec touches… | Gate |
|------|---------------|------|
| **Low** (auto) | internal helper, copy/string change, test-only, isolated pure function, docs | loop auto-approves, logs to REVIEW.md, builds |
| **High** (human) | schema/migration, auth/permissions, public API surface, money/billing, deletion, external calls, security boundary | always parked for human |

When unsure which tier → treat as **High**. Never auto-approve on a guess.

## The Loop (one pass)

```
for each candidate spec, in backlog order:
  1. APPROVED + FRESH?   status in {approved, implemented}  AND  not stale (see below)
        no (approved + STALE) → PARK for human re-approval (step 2-STALE) — its ground
                                moved; NEVER auto-approve a stale spec, any tier.
        no (draft/unapproved) → step 2-NEW (gate it)
        yes                   → step 1b
  1b. AUTONOMY GATE (always runs, even for already-approved specs — THIS is the fix):
        compute the spec's risk tier (see Risk Policy).
        Low risk                         → buildable, step 4
        High risk AND autonomous_ok: true → buildable, step 4   (human pre-authorized)
        High risk AND NOT autonomous_ok   → PARK (reason: high-risk), SKIP.
                                            (status: approved is NOT enough to
                                            auto-build a high-risk spec.)
  2-STALE. Stale spec (was approved, code path moved): PARK (reason: stale) — append
        REVIEW.md, push phone, SKIP. Human re-approves (which re-stamps baseline_sha).
        Do NOT auto-approve, regardless of risk tier — the preamble is explicit:
        "treat it exactly like an unapproved spec: re-park for human re-approval."
  2-NEW. Never-approved spec — RISK TIER?
        Low  → auto-approve: set status: approved, approved_at, baseline_sha=HEAD;
               commit; log to REVIEW.md; → step 4
        High → PARK (reason: needs-approval), push phone, SKIP item
  3. (parked items are skipped this pass; human approves/authorizes async)
  4. DEPENDENCIES MET?  every id in the spec's depends_on: is status implemented?
        no  → SKIP (not buildable yet — NOT a failure); do not park, do not retry-spin
        yes → BUILD
  4b. BUILD: invoke /tai-flow for this item → execute → review → qa → ship → docs-update
        flow halts on its own gates/failures; loop respects that halt
  5. OUTCOME:
        success → record to REVIEW.md / changelog; mark backlog item done
        failed (flow HALT / retry exhausted) → write last_attempt_failed_sha to the
               spec; mark ⚠ failed; SKIP re-build until code or spec changes (no
               re-attempt every pass — that just burns budget)
  6. next item

end of pass:
  any items built?   → start another pass (newly-unblocked work may exist)
  none built, parked/failed/blocked set unchanged from last pass → no-progress → SLEEP
  SLEEP report: separate ⏸ parked (awaiting human) from ⚠ failed (needs debug) from
                ⛓ blocked (waiting on a dependency)
```

> **Why 1b is critical.** `status: approved` is approval of the *contract*, not blanket
> authorization to build a dangerous surface unattended. A high-risk spec (auth, schema,
> money) ALWAYS needs a human to either run the build interactively or set
> `autonomous_ok: true` in its frontmatter. Without 1b, an approved auth spec would ship
> overnight with no human in the loop — the exact failure the risk policy exists to stop.

### Staleness check (the only gate machinery — one diff)

```bash
# spec is approved; is its code path still as it was at approval?
git diff --name-only "$baseline_sha" HEAD | grep -qF "$code_path" && echo "STALE"
```

Touched since approval → STALE → re-park. No hashes, no dep graph. Git already knows
what changed. (See `docs-preamble.md` → Approval anchor.)

## Async Gate — Push to Human

When parking a High-risk or stale spec:

**Upsert, don't duplicate.** Before appending, check `docs/REVIEW.md` for an existing
open PENDING entry for this spec id. If one exists, leave it (don't append a second).
Only append when there's no open entry for that spec — otherwise a re-parked item
accretes a new entry every pass.

Frontmatter fields this references (set by a human, never the loop):
- `autonomous_ok: true` — human authorizes unattended build of a high-risk spec.
- `depends_on: [SPEC-ids]` — specs that must be `implemented` before this one builds.

1. Append to `docs/REVIEW.md` Open Items (the committed, durable queue). **The
   remediation line MUST match the park reason** — a wrong instruction strands the
   item forever (e.g. telling a human to "flip status: approved" on an already-approved
   high-risk spec is a no-op):
   ```
   ### [REVIEW-NNN] Unblock SPEC-{id} for autonomous build
   - Skill: /tai-loop
   - Why parked: {reason}
   - Summary: {2-3 lines plain English}
   - To unblock:
       reason = needs-approval → flip status: approved (flow re-stamps approved_at/baseline_sha)
       reason = high-risk      → set autonomous_ok: true in docs/specs/{file}
                                 (or run /tai-flow on it interactively)
       reason = stale          → re-approve: re-confirm the spec vs moved code, then
                                 flow re-stamps baseline_sha=HEAD
   - Status: PENDING
   ```
2. Push a notification (Discord / PushNotification if available) with the same summary +
   the file path. Human taps Approve from anywhere → edits the spec status async.
3. SKIP the item. Do not block. Move to the next.

The human moved from keyboard-typist to **phone reviewer**. That is the vision: you
communicate a decision; the loop does the rest.

## Termination & Safety (loop failure modes)

Hard guards — a loop without these is dangerous:

| Failure | Guard |
|---------|-------|
| Infinite loop | **Hard pass cap** (default 20 passes/run) + **no-progress detector**: if a pass builds 0 items and parks the same set as last pass → SLEEP, don't spin. |
| Reward hacking | Gates (risk policy) + flow's own gates. Loop never relaxes a gate to make progress. |
| Hallucinated success | "Built" requires flow's `/review` + `/qa` to pass — deterministic verifiers, not the agent's say-so. Matrix R-id coverage is the `achieved` audit. |
| Cost explosion | **Token/time budget** per run. On exhaustion: finish the in-flight item, write a progress summary to REVIEW.md, SLEEP. Never abandon a half-built item. |
| Drift | Staleness check re-parks specs whose ground moved. |
| Source-layer corruption | Inherits flow's rule: never edit spec/prd/adr to pass. Stale spec → re-gate, never rewrite. |

On any flow HALT (its gate, or auto-fix-retry exhausted) → record, park the item,
continue the loop with the next item. One stuck item never stops the whole loop.

## Modes (trigger)

- `/tai-loop` — one autonomous pass over the backlog now, then report.
- `/tai-loop "drain backlog"` — keep passing until the approved queue is empty or a
  budget/cap is hit (the goal-loop / Ralph-style mode).
- Pair with `/loop` or `/schedule` (this CLI's interval/cron primitives) to run on a
  heartbeat or timer for true walk-away operation.

## Report (end of every run)

```
tai-loop: pass {n}
  ✓ built + shipped: {SPEC-ids}
  ⏸ parked (need human): {SPEC-ids} — pushed to phone, see REVIEW.md
  ⚠ failed: {SPEC-ids} — {one-line reason each}
  budget: {spent}/{total}
  next: {another pass | SLEEP — N parked awaiting approval}
```
