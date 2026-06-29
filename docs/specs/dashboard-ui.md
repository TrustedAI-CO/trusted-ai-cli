---
id: SPEC-dashboard-ui
type: spec
status: approved
approved_at: 2026-06-29T16:57:40Z
implements: [prd, 0002-dashboard-web-stack]
parent: architecture
children: []
related: [SPEC-dashboard-serve, SPEC-docs-query, SPEC-gates-view, SPEC-gates-action]
code: tai/commands/dashboard.py
tests: tests/test_dashboard_ui.py
---

# tai dashboard --serve UI — Spec (end-stage web UI/UX)

> The deferred UI/UX phase: turn the bare `--serve` page into the human-facing control
> panel — tabs, search, **mermaid render**, and **approve/accept/resolve buttons** wired to
> the gate control plane. Stdlib only (ADR 0002). Reuses every existing collector + the
> gate write logic; adds NO new data path or write path.

## Overview
Extends `tai dashboard --serve` (SPEC-dashboard-serve) from a one-screen overview into a
small single-page app over the same local server: navigate Overview / Specs / Gates,
search, open a doc (markdown + rendered mermaid), and clear a gate with a button. The
button POSTs to gate endpoints that call the **exact same functions** as `tai gate`
(SPEC-gates-action) — the click is the human authorization (localhost only).

## Invariants
- INV1: **Writes only via explicit gate POSTs.** All `GET` endpoints are read-only; the
  only writes are `POST /api/gate/{approve|accept|resolve}`, each triggered by a human
  button click. No GET mutates.
- INV2: **One write path.** Gate POSTs call the same core functions as `tai gate` — same
  flip-only-status, same one-commit-with-rollback, same invalid-transition refusal. The web
  must not reimplement gate logic (no divergence between CLI and web).
- INV3: **Localhost only** (inherited from SPEC-dashboard-serve INV3). The write endpoints
  are never exposed beyond loopback without an explicit `--host`.

## Interface
Served by `tai dashboard --serve`. Endpoints:
```
GET  /                          # single-page app (tabs: Overview, Specs, Gates)
GET  /api/dashboard.json        # (existing) overview data
GET  /api/docs[?type=&status=]  # list specs+ADRs (collect_list)
GET  /api/search?q=<query>      # search (collect_search)
GET  /api/doc/<id>              # one doc: {frontmatter, body, mermaid: [blocks]}
GET  /api/gates                 # pending board (collect_gates)
POST /api/gate/approve {id}     # → gate approve logic
POST /api/gate/accept  {id}     # → gate accept logic
POST /api/gate/resolve {id}     # → gate resolve logic
```
POST returns `{ok: bool, message: str}`; the page refreshes the affected view.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | server running | `GET /` | single-page app with nav tabs Overview / Specs / Gates |
| R2 | specs + ADRs exist | open Specs tab | lists them (id/type/status/title), filter by type/status |
| R3 | a doc with a ```mermaid block (e.g. architecture.md) | open its detail | markdown body shown; mermaid block rendered as a diagram (mermaid.js, CDN) |
| R4 | a query typed in the search box | search | results from `/api/search` shown |
| R5 | open Gates tab | render | pending board (A/B/C/REVIEW) with an action button per item |
| R6 | a draft spec in Gates | click Approve → confirm | `POST /api/gate/approve` flips it to approved + commits; board refreshes, item gone |
| R7 | a gate POST for an invalid transition | e.g. approve a non-draft | `{ok:false, message}`, no write (reuses gate refusal) |
| R8 | a `GET` endpoint | any read | never writes any file (INV1) |
| R9 | gate POST | success | same single audited commit as `tai gate` (INV2) — one write path |
| R10 | default bind | server start | loopback only (INV3) |

## Acceptance
- [ ] R1–R10 referenced by passing tests (tests/test_dashboard_ui.py) — drive the HTTP
      endpoints (GET shapes, POST approve/accept/resolve happy + refusal) against a temp git repo.
- [ ] INV1: a GET sweep leaves docs/ byte-identical. INV2: web approve == `tai gate approve`
      (same status flip + one commit) — assert by calling both paths. INV3: loopback bind.
- [ ] `gate.py` core extracted into callable functions used by BOTH the `tai gate` commands
      and the web POST handlers (no duplicate write logic).
- [ ] Mermaid via CDN client-side; degrades to showing the raw fenced block if the CDN is unavailable.

## Open questions
- Confirmation on the web Approve button: a JS `confirm()` dialog is enough (the click +
  confirm = human authorization); no server-side prompt.
- Keep the page dependency-light: mermaid.js from CDN is the only external asset.
