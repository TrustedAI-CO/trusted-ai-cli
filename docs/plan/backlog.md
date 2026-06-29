---
id: plan-backlog
type: plan
parent: null
children: []
related: []
---

# Backlog

## Active
- [ ] (scheduled deferred work)

## Backlog
- gate nits (#79 review LOW, deferred): `_flip_status` doesn't match quoted YAML
  (`status: "draft"`) → misleading "is 'draft', not 'draft'" message; CRLF normalization
  behavior documented but untested; no-git case writes-then-reverts (transient on-disk
  mutation if SIGKILL between write and rollback) — INV4 presumes git.
- Dashboard nits (#78 review LOW, deferred): subcommands honor only local `--json`, not the
  global `tai --json` app-context flag (bare dashboard does) — fold global json into subcommands;
  minor double-read in collect_search / re-walk in find_doc_by_id (fine at current tree size).
- Review nits (round-5 LOW, deferred — non-blocking): docs-update guardrails block says
  "part of the Document-Driven pipeline" (→ "framework"); docs-test-prompt stale skill name
  `document-release` (→ docs-update) + Check 3 execute-writes row understates §4/prose;
  execute Team Engineer template step 3 "Update Traceability" lags the live derived-doc DoD;
  ship gate check 7 changelog sub-bullet not scoped to spec-touching changes like the matrix one.
- Framework finding (dogfood, 2026-06-29): `docs-validate` A1 orphan rule says every doc
  must be reachable except `REVIEW.md`, but `docs-init` scaffolds root derived/plan docs
  (changelog, matrix, contributing, plan/tasks, plan/backlog) with `parent: null` and
  nothing linking them → they are orphans by the rule. The `tai dashboard` Doc Health
  check flagged all 5 on a fresh scaffold. Fix: A1 should exempt standalone root types
  (matrix/changelog/contributing/plan/design), or docs-init should cross-link them.
  Dashboard already exempts these types in its orphan check as a workaround.
