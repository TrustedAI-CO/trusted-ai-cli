---
id: changelog
type: changelog
parent: null
children: []
related: []
derived: true
---

> ⚠️ Derived doc — maintained live by an agent as code changes; may still lag. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.

# Changelog

## [0.37.2] - 2026-07-01

### Fixed
- `/tai-execute` team mode now removes each engineer's git worktree after its PR
  merges (`git worktree remove --force`) and sweeps stragglers with `git worktree
  prune` at phase completion — stale `../eng-*` worktrees no longer linger on disk.

## [0.37.0] - 2026-06-30

### Added
- `tai dashboard` — one-screen project overview from the `docs/` tree: spec pipeline by
  status, matrix coverage, REVIEW.md needs-you, recent changelog, doc-graph health.
  `--json` for machines. (SPEC-dashboard-render)
- `tai dashboard --serve` — live localhost web view (stdlib, zero new deps): a single-page
  app with Overview / Specs / Decisions / Gates / Architecture tabs, search, doc detail with
  **rendered markdown + mermaid diagrams**, gate action buttons, light theme.
  (SPEC-dashboard-serve, SPEC-dashboard-ui)
- `tai dashboard list | search | show | gates` — browse/filter/search specs + ADRs, view
  one doc, and a pending-gates board (A/B/C + REVIEW). (SPEC-docs-query, SPEC-gates-view)
- `tai gate approve | accept | resolve <id>` — clear a doc-driven gate from the terminal:
  flips the status field (+ stamps approved_at) and makes one audited git commit; the web
  UI's gate buttons call the same core. (SPEC-gates-action)

### Changed
- Migrated project docs from the legacy HTML tree (`docs.old/`) to the markdown
  document-driven framework.
