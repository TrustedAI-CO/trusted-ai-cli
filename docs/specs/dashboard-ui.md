---
id: SPEC-dashboard-ui
type: spec
status: approved
approved_at: 2026-06-29T17:31:09Z
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
small single-page app over the same local server: navigate Overview / Specs / Decisions /
Gates / Architecture, search, open a doc (markdown **rendered to HTML** + rendered mermaid),
and clear a gate with a button. The button POSTs to gate endpoints that call the **exact
same functions** as `tai gate` (SPEC-gates-action) — the click is the human authorization
(localhost only).

**Revision (2026-06-30):** split Specs into separate **Specs** (type spec) and **Decisions**
(type decision) tabs; add an **Architecture** tab (renders `docs/architecture.md` — markdown
+ its C4 mermaid diagrams); and the doc detail must **render markdown to HTML** (headings,
tables, lists, emphasis, code, links, blockquote), not show raw markdown text.

## Invariants
- INV1: **Writes only via explicit gate POSTs.** All `GET` endpoints are read-only; the
  only writes are `POST /api/gate/{approve|accept|resolve}`, each triggered by a human
  button click. No GET mutates.
- INV2: **One write path.** Gate POSTs call the same core functions as `tai gate` — same
  flip-only-status, same one-commit-with-rollback, same invalid-transition refusal. The web
  must not reimplement gate logic (no divergence between CLI and web).
- INV3: **Localhost only** (inherited from SPEC-dashboard-serve INV3). The write endpoints
  are never exposed beyond loopback without an explicit `--host`.
- INV4: **Markdown render is XSS-safe.** Rendering doc body to HTML escapes first and emits
  only a known tag set — no raw HTML/script from doc content executes (mermaid stays
  `securityLevel:'strict'`).

## Interface
Served by `tai dashboard --serve`. Endpoints:
```
GET  /                          # single-page app (tabs: Overview, Specs, Decisions, Gates, Architecture)
GET  /api/dashboard.json        # (existing) overview data
GET  /api/docs[?type=&status=]  # Specs tab uses ?type=spec; Decisions tab uses ?type=decision
GET  /api/doc/architecture      # Architecture tab uses the existing doc-detail endpoint
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
| R1 | server running | `GET /` | single-page app with nav tabs **Overview / Specs / Decisions / Gates / Architecture** |
| R2 | specs exist | open Specs tab | lists **specs only** (`type: spec`) — id/status/title, clickable |
| R3 | a doc detail is opened | render | markdown body **rendered to HTML** (headings, tables, lists, emphasis, inline/block code, links, blockquote) AND ```mermaid blocks rendered as diagrams — NOT raw markdown text |
| R4 | a query typed in the search box | search | results from `/api/search` shown |
| R5 | open Gates tab | render | pending board (A/B/C/REVIEW) with an action button per item |
| R6 | a draft spec in Gates | click Approve → confirm | `POST /api/gate/approve` flips it to approved + commits; board refreshes, item gone |
| R7 | a gate POST for an invalid transition | e.g. approve a non-draft | `{ok:false, message}`, no write (reuses gate refusal) |
| R8 | a `GET` endpoint | any read | never writes any file (INV1) |
| R9 | gate POST | success | same single audited commit as `tai gate` (INV2) — one write path |
| R10 | default bind | server start | loopback only (INV3) |
| R11 | ADRs exist | open Decisions tab | lists **decisions only** (`type: decision`) — id/status/title, clickable to detail |
| R12 | `docs/architecture.md` exists | open Architecture tab | renders architecture.md as HTML with its C4 **mermaid diagrams** drawn (reuses doc detail + R3 rendering) |
| R13 | a doc body with `<script>`/HTML | render | escaped, not executed (INV4 — markdown render is XSS-safe) |

## Acceptance
- [ ] R1–R13 referenced by passing tests (tests/test_dashboard_ui.py) — drive the HTTP
      endpoints (GET shapes incl. ?type filters, POST approve/accept/resolve happy + refusal)
      against a temp git repo.
- [ ] R3/R13: a markdown-render unit test — body with headings/table/list/code/link renders to
      the expected HTML tags; a `<script>` in body is escaped, not executed (INV4).
- [ ] INV1: a GET sweep leaves docs/ byte-identical. INV2: web approve == `tai gate approve`
      (same status flip + one commit). INV3: loopback bind + writes refused when bound non-loopback.
- [ ] `gate.py` core extracted into callable functions used by BOTH the `tai gate` commands
      and the web POST handlers (no duplicate write logic).
- [ ] Markdown rendered escape-first (no new deps); mermaid via CDN, degrades to raw fenced block if unavailable.

## Open questions
- Markdown rendering is escape-first hand-rolled (no marked/dompurify deps) to honor ADR 0002's
  dependency-light stack + keep INV4 simple. Revisit only if doc markdown needs outgrow it.
- Confirmation on the web Approve button: a JS `confirm()` dialog is enough (the click +
  confirm = human authorization); no server-side prompt.
