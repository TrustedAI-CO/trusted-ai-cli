---
name: plan-review
version: 1.0.0
description: |
  [TAI] Plan reviewer — the code-reviewer mechanism (ADR 0003) applied to PLANS. Spawns 2
  fresh blind reviewers in parallel on the drafted plan docs (draft specs, proposed ADRs,
  prd) and iterates until a round's two reviewers both find nothing CRITICAL/HIGH, fixing
  the plan between rounds, then presents the converged plan to the human (feeds GATE C).
  Use after a plan skill drafts specs/ADRs (or via /tai-flow-plan), or when asked to
  "review the plan", "harden the spec before approval", "vet this spec".
allowed-tools:
  - Agent
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

## Framework Guardrails (read first)

Part of the Document-Driven pipeline. Read **`docs-philosophy.md`** (single source of truth).
Non-negotiable: `docs/prd.md` is HUMAN-owned; doc-first order; never edit a source layer to
match code; tests reference Behavior row IDs.

> **Flow mode:** if `.tai/state/flow-session` exists, framework + conventions are already
> loaded — skip re-reading.

## Conventions

Shared conventions (AskUserQuestion Format, Boil-the-Lake, tai Field Report) live in
`docs-conventions.md` (ADR 0005). `/tai-flow` loads it once; standalone, read it once.

## What this reviews

Plan-level quality of the drafted artifacts — NOT code (there is no code yet). The diff to
review is the plan docs added/changed this session: `docs/specs/*.md` at `status: draft`,
`docs/decisions/*.md` at `status: proposed`, and `docs/prd.md` if touched. Get them via
`git diff` against the base branch, or read the draft files directly.

Each reviewer checks:
- **Contract soundness** — Behavior rows are observable + testable (Given/When/Then with
  concrete values), each has a stable R-id; Invariants are real always-true properties;
  Interface is complete. One spec = one public surface.
- **Traceability** — `code:`/`tests:` paths are sensible and `code:` sits under an
  `architecture.md` §4 container; `implements:` points at real PRD/ADR ids.
- **Scope** — not over-built (boil the lake, not the ocean) and not under-specified; open
  questions surfaced, not hidden.
- **Doc-first conformance** — for a spec evolution, status was reset to `draft` and R-ids
  are append-only; no source-layer edited to match existing code.
- **ADR quality** (if ADRs drafted) — decision is clear, consequences honest, alternatives real.

## The Review Loop — 2 parallel blind reviewers, converge (ADR 0003 mechanism)

This is the SAME loop as `/tai-review`, applied to the plan. The controller (you) owns it;
each reviewer is a fresh, stateless subagent.

**Blind-reviewer rule:** each reviewer gets ONLY the current plan docs + the framework
rules — NEVER prior findings, "already fixed," or "re-check." Fixes carry between rounds
only as edits to the plan docs; a fresh reviewer re-derives what's still wrong.

```
for round in 1..MAX (MAX = 4):
    [a, b] = spawn 2 FRESH blind reviewers IN PARALLEL (current plan docs + specs/architecture;
             complementary angles — e.g. contract-soundness vs scope/feasibility)
    worth_fixing = (a ∪ b) findings with severity CRITICAL or HIGH
    if worth_fixing is empty:
        → CONVERGED — both reviewers found nothing worth fixing (one clean round)
    else:
        revise the plan docs to address them (keep specs at draft; never approve here),
        commit, and run another parallel round
        # LOW/INFO → the spec's "## Open questions" or docs/plan/backlog.md
if round == MAX and still not clean: → present anyway, listing the unresolved CRITICAL/HIGH
                                       so the human decides at the gate
```

Reviewers must NOT approve the plan or flip any `status:` — that is the human's gate. They
report findings only; the controller fixes the drafts.

## Present the converged plan

When converged (or at the cap), present the vetted plan to the human concisely — lead with
the visual shape (per `/plan-eng` talk-then-write: spec surface + Behavior-row table +
`code:`/`tests:` map), then note what the review rounds changed and any unresolved items.
This hand-off feeds the relevant human gate — **GATE B** for proposed ADRs, **GATE C** for
draft specs (and PRD sign-off if touched). Do NOT flip `status:` yourself.

## Report

```
plan-review: converged in {N} round(s) ({2N} reviewers)
  ✓ hardened: {what the rounds fixed}
  ⚠ unresolved (if capped): {CRITICAL/HIGH left for the human}
  → ready for gate: {spec ids draft → GATE C; ADR ids proposed → GATE B}
```
