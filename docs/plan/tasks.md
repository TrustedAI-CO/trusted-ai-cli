---
id: plan-tasks
type: plan
parent: null
children: []
related: [SPEC-dashboard-render]
---

# Execution Tasks

## SPEC-dashboard-render — `tai dashboard`

Single sub-phase (one command, one module) → solo execution.

- [ ] T1 — `tai/commands/dashboard.py`: docs/ parser (frontmatter graph, spec statuses,
      matrix summary, REVIEW PENDING, changelog) — pure, read-only functions. (R1–R5, R7, INV1/INV2)
- [ ] T2 — render layer: terminal one-screen view via existing `tai/core/style.py`. (R1)
- [ ] T3 — `--json` output path. (R8)
- [ ] T4 — no-docs error path + exit codes. (R6)
- [ ] T5 — register the command group in `tai/main.py`.
- [ ] T6 — `tests/test_dashboard.py`: one test per R-id + INV1 (read-only) + INV2 (malformed doc).
