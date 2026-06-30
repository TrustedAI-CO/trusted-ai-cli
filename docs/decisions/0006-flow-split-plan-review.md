---
id: 0006-flow-split-plan-review
type: decision
status: accepted
parent: architecture
children: []
related: [0003-review-loop-parallel, 0004-plan-talk-first]
supersedes: none
---

# 0006-flow-split-plan-review: Plan-review loop + split flow into /tai-flow-plan and /tai-flow-execute

## Context
Two gaps in the current single `/tai-flow`:
1. **No review of the plan itself.** Code gets the blind parallel review loop (ADR 0003),
   but a drafted spec/ADR/prd goes straight from plan-skill → human GATE C with no
   adversarial vetting. The human approves an unreviewed plan. We want the plan hardened
   *before* it reaches the human, same as code is hardened before merge.
2. **Flow is all-or-nothing.** `/tai-flow` runs plan→gate→build→ship as one command. Users
   want to run *just planning* (stop at approved specs) or *just the build* (specs already
   approved) — separately.

## Decision

### A. New skill `/tai-plan-review` — the code-reviewer mechanism, applied to plans
Mirror `/tai-review` (ADR 0003) for the plan artifacts:
- Spawn **2 fresh blind reviewers in parallel** per round, given ONLY the drafted plan
  docs (`docs/specs/*` draft, `docs/decisions/*` proposed, `docs/prd.md`) + the framework
  rules — never prior findings. Complementary angles (e.g. contract soundness vs
  scope/feasibility).
- They check **plan-level** quality: behavior rows complete + testable, invariants sound,
  `code:`/`tests:` paths sensible + under an architecture §4 container, scope right (not
  over/under-built), doc-first conformance (one spec = one surface, R-id stability), open
  questions surfaced.
- **Iterate until a round's two reviewers both find nothing CRITICAL/HIGH** (converge),
  fixing the plan between rounds; cap 4 rounds. LOW/INFO → the spec's Open questions or
  `backlog.md`.
- Then **present the converged plan to the user** (this feeds GATE C).
Blind-reviewer + leading-word conventions per `docs-conventions.md`.

### B. Split flow into two invocable halves (keep the full `/tai-flow`)
- **`/tai-flow-plan`** — S0 init → S1 plan (auto-route, talk-then-write per ADR 0004) →
  **`/tai-plan-review`** (converge) → GATE A/B/C (human approves PRD/ADR/spec). **STOPS**
  once the relevant specs are `approved`. Output: a vetted, approved plan; no code.
- **`/tai-flow-execute`** — assumes specs `approved`; runs S2 build (`/tai-execute`) →
  S3 `/review` → S4 `/qa` (surface-type guard) → S5 `/ship`. The build half.
- **`/tai-flow`** — unchanged behavior, now defined as **`/tai-flow-plan` then
  `/tai-flow-execute`** (delegates to both). Same end-to-end run for those who want one
  command.

## Consequences
- The human approves a **reviewed** plan, not a first draft — fewer bad specs reach code.
- Clean separation: plan work and build work are independently runnable/resumable.
- `/tai-flow` stays the one-shot path (no migration for existing users).
- Cost: an extra review loop in the plan phase (2 subagents/round) + two new thin
  orchestrator skills that delegate (no logic duplication — they call the same stage skills).

## Alternatives considered
- Plan-review as a *mode* of `/tai-review` — rejected: code-review and plan-review check
  different things; a dedicated skill is clearer and reusable.
- Don't split, add flags to `/tai-flow` (`--plan-only` / `--build-only`) — rejected:
  separate skills are more discoverable + match the user's mental model of two phases.
