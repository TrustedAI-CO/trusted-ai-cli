---
id: SPEC-gates-action
type: spec
status: approved
approved_at: 2026-06-29T16:37:18Z
implements: [prd]
parent: architecture
children: []
related: [SPEC-gates-view, 0001-markdown-docs]
code: tai/commands/gate.py
tests: tests/test_gate_action.py
---

# tai gate — Spec (CLI, WRITE — the control plane)

> Lets a human clear a gate from the terminal instead of hand-editing frontmatter:
> approve a spec, accept an ADR, resolve a REVIEW item. This is the one surface that
> **writes to gated source docs**, so its invariants are strict. It mirrors `/tai-flow`'s
> GATE C/B semantics — the human running the command IS the authorization.

## Overview
A new `tai gate` command group with three actions that flip a gate's status field, stamp
provenance, and commit — nothing else. It complements `tai dashboard gates` (the read
board): the board shows what's pending + the verb; this performs the verb. PRD signing is
deliberately excluded (human-only, edited manually — see Open questions).

## Invariants
- INV1: **Human-initiated only.** Invoked by a human at the terminal; the invocation is the
  authorization (same principle as flow GATE C). It MUST NOT be called by an agent
  autonomously / non-interactively, and there is no code path that auto-invokes it.
- INV2: **Flips status + stamps + commits — never edits content.** `approve` changes a
  spec's `status: draft → approved` and stamps `approved_at`; `accept` changes an ADR's
  `status: proposed → accepted`; `resolve` marks a REVIEW item resolved. It NEVER touches a
  doc's body, Interface, Behavior, or any other field. (This is the permitted gate write,
  not a content edit — it does not violate doc-first.)
- INV3: **Refuses invalid transitions.** `approve` only a `draft` spec; `accept` only a
  `proposed` ADR; `resolve` only an open `PENDING` review item. Any other current state →
  error, NO write.
- INV4: **Auditable.** Every successful action makes exactly one git commit whose message
  records the gate, the id, and the new status (git history = the audit trail).

## Interface
```
tai gate approve <SPEC-id>   [--yes]   # GATE C: spec draft → approved (+ approved_at)
tai gate accept  <ADR-id>    [--yes]   # GATE B: ADR proposed → accepted
tai gate resolve <REVIEW-id> [--yes]   # REVIEW: open PENDING item → resolved
```
Without `--yes`, prints what it will do (file, transition) and asks for confirmation;
`--yes` skips the prompt (still human-initiated). All exit 0 on success, 1 on any refusal.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | a spec at `status: draft` | `tai gate approve SPEC-x --yes` | spec → `status: approved`, `approved_at` stamped, one commit; exit 0 |
| R2 | a spec already `approved`/`implemented` | `tai gate approve SPEC-x` | error "not in draft", no write, exit 1 |
| R3 | an ADR at `status: proposed` | `tai gate accept 0003-x --yes` | ADR → `status: accepted`, one commit; exit 0 |
| R4 | an ADR not `proposed` | `tai gate accept 0003-x` | error, no write, exit 1 |
| R5 | a REVIEW item with `Status: PENDING` | `tai gate resolve REVIEW-001 --yes` | item marked resolved (moved/flagged), one commit; exit 0 |
| R6 | a REVIEW id not pending / absent | `tai gate resolve REVIEW-999` | error, no write, exit 1 |
| R7 | an unknown id | any action `NOPE` | "not found" + nearest-id hint, exit 1 |
| R8 | no `--yes` | `tai gate approve SPEC-x` | prints the transition and asks confirm; declining = no write, exit 1 |
| R9 | any successful action | after it runs | ONLY the status/approved_at line(s) changed in the target file — body byte-identical (INV2) |
| R10 | a successful action | after it runs | exactly one new git commit; message names gate + id + new status (INV4) |

## Acceptance
- [ ] R1–R10 each referenced by a passing test (tests/test_gate_action.py); use a temp git repo.
- [ ] INV2 test: diff the target file pre/post — only frontmatter status/approved_at changed.
- [ ] INV3 tests: every wrong-state transition refuses with no write (R2/R4/R6).
- [ ] INV4 test: exactly one commit, message records the action.
- [ ] `code:` `tai/commands/gate.py` + `tests:` exist; registered in `tai/main.py`; sits under
      the Command-groups container (architecture.md §4).

## Open questions
- **PRD sign** is excluded (human-only). gates-view shows it with action `sign` but
  gate-action does not implement it — confirm we keep PRD signing a manual edit.
- `resolve` mechanics: move the block to `## Resolved Items` vs flip a `Status:` line in
  place? Decide at execute; either satisfies "marked resolved" + INV2 (body otherwise intact).
