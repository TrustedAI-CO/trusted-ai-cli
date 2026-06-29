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
- Framework finding (dogfood, 2026-06-29): `docs-validate` A1 orphan rule says every doc
  must be reachable except `REVIEW.md`, but `docs-init` scaffolds root derived/plan docs
  (changelog, matrix, contributing, plan/tasks, plan/backlog) with `parent: null` and
  nothing linking them → they are orphans by the rule. The `tai dashboard` Doc Health
  check flagged all 5 on a fresh scaffold. Fix: A1 should exempt standalone root types
  (matrix/changelog/contributing/plan/design), or docs-init should cross-link them.
  Dashboard already exempts these types in its orphan check as a workaround.
