---
id: SPEC-gates-view
type: spec
status: implemented
approved_at: 2026-06-29T15:47:05Z
implements: [prd]
parent: architecture
children: []
related: [SPEC-docs-query]
code: tai/commands/dashboard.py
tests: tests/test_gates_view.py
---

# tai dashboard gates — Spec (CLI, read)

> A pending-gates board: what needs a human right now, and which gate. Read-only. Turns
> the vague "needs-you" count into an actionable queue (the action itself is
> SPEC-gates-action).

## Overview
`tai dashboard gates` scans `docs/` and lists every item awaiting a human gate, grouped by
gate type. Maps the framework's three gates + the attention log:
- **GATE A** — `docs/prd.md` not signed (status not `approved`/`shipped`).
- **GATE B** — ADRs in `docs/decisions/` with `status: proposed` (awaiting accept).
- **GATE C** — specs in `docs/specs/` with `status: draft` (awaiting approval).
- **REVIEW** — `docs/REVIEW.md` open items with `Status: PENDING`.

## Invariants
- INV1: **Read-only** (inherited).
- INV2: **Never crashes on a malformed doc** (inherited).

## Interface
```
tai dashboard gates [--json]
```
Prints a grouped board: each group (GATE A/B/C, REVIEW) with its pending items
(id · title · the action that would clear it). `--json` emits
`{gate_a: [...], gate_b: [...], gate_c: [...], review: [...]}` where each item is
`{id, title, action}` and `action` ∈ `sign|accept|approve|resolve`.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | docs/ with mixed states | `tai dashboard gates` | grouped board with sections GATE A, GATE B, GATE C, REVIEW |
| R2 | a spec at `status: draft` | run | it appears under GATE C with action "approve" |
| R3 | an ADR at `status: proposed` | run | it appears under GATE B with action "accept" |
| R4 | prd.md status not approved/shipped | run | GATE A shows it with action "sign" |
| R5 | REVIEW.md has N PENDING items | run | each listed under REVIEW with action "resolve" |
| R6 | nothing pending anywhere | run | "all clear — no gates open" (exit 0) |
| R7 | `--json` | `tai dashboard gates --json` | the grouped JSON shape above |
| R8 | no docs/ | run | friendly error + exit 1 |

## Acceptance
- [ ] R1–R8 each referenced by a passing test (tests/test_gates_view.py).
- [ ] INV1 read-only + INV2 malformed-doc tests.
- [ ] Reuses SPEC-dashboard-render collectors; the `action` verbs align 1:1 with
      SPEC-gates-action's commands (approve/accept/resolve/sign).

## Open questions
- "sign" (PRD) is human-only and out of any agent's reach — gates-action may only cover
  approve/accept/resolve; PRD signing stays a manual edit. Decide in gates-action.
