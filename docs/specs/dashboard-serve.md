---
id: SPEC-dashboard-serve
type: spec
status: approved
approved_at: 2026-06-29T14:54:10Z
implements: [prd, 0002-dashboard-web-stack]
parent: architecture
children: []
related: [SPEC-dashboard-render, 0002-dashboard-web-stack]
code: tai/commands/dashboard.py
tests: tests/test_dashboard_serve.py
---

# tai dashboard --serve — Spec (follow-up, web surface)

> Follow-up to [SPEC-dashboard-render](dashboard-render.md). Adds a **local web view** of
> the same project state for live, visual monitoring on a screen. **Reuses the exact same
> read-only collectors** (`build_dashboard` / `Dashboard.to_dict`) — the web view is a
> second *renderer*, never a second *data source*. WEB surface → its QA path is the
> browser tester, not the CLI smoke check.
>
> **Gating:** the server/stack choice is load-bearing → requires ADR
> [0002-dashboard-web-stack](../decisions/0002-dashboard-web-stack.md) `accepted` (GATE B)
> before this spec is `approved` (GATE C) and any code merges.

## Overview
`tai dashboard --serve` starts a local web server that renders the same `docs/`-derived
data as `tai dashboard`, refreshed live, with interactive views (clickable dependency
graph, drill-down per spec). It is a monitoring dashboard for a second screen — "what's
going on right now," auto-updating, without re-running the command.

## Invariants
- INV1: **Read-only.** Never writes under `docs/` (inherited from SPEC-dashboard-render).
- INV2: **Single source of data.** The web view renders exactly `build_dashboard()` output
  — the served numbers can never disagree with `tai dashboard` / `--json`.
- INV3: **Localhost only.** The server binds `127.0.0.1` by default; it is never exposed
  on `0.0.0.0` without an explicit, documented flag. No auth = no external surface.

## Interface
```
tai dashboard --serve [--port N] [--no-open] [--host 127.0.0.1]
  --serve            start the web server (default port: auto-pick free, e.g. 8787)
  --port N           bind a specific port
  --no-open          do not auto-open the browser
  --host             bind host (default 127.0.0.1; documented warning if not loopback)
```
Prints the URL, opens the browser (unless `--no-open`), serves until Ctrl-C (graceful
shutdown). A `GET /api/dashboard.json` endpoint returns the same JSON as `--json`.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | a repo with `docs/` | `tai dashboard --serve` | binds a local port, prints the URL, opens the browser (unless `--no-open`) |
| R2 | the server is running | `GET /api/dashboard.json` | returns the same payload as `tai dashboard --json` (INV2) |
| R3 | the browser page loaded | render | shows Pipeline, Coverage, Needs-You, Recent, Doc Health — parity with the CLI view |
| R4 | a `docs/` file changes while serving | next refresh (poll or file-watch) | the view updates without a manual restart |
| R5 | `--port N` given and free | `tai dashboard --serve --port N` | binds exactly N |
| R6 | `--port N` given but in use | start | fails with a clear error + hint (no silent fallback) |
| R7 | no `docs/` directory | `tai dashboard --serve` | same friendly error + exit 1 as the CLI (R6 of dashboard-render) |
| R8 | Ctrl-C while serving | interrupt | shuts down cleanly, frees the port, exit 0 |
| R9 | default invocation | `tai dashboard --serve` | binds `127.0.0.1` only (INV3); never `0.0.0.0` without `--host` |

## Acceptance
- [ ] Each Behavior row R1–R9 referenced by a passing test (browser/QA covers R3/R4).
- [ ] INV2 test: served `/api/dashboard.json` byte-equals `tai dashboard --json` for the same tree.
- [ ] INV3 test: default bind is loopback; assert no non-loopback bind without `--host`.
- [ ] ADR 0002 is `accepted` and the chosen stack is reflected here before approval.
- [ ] `code:`/`tests:` paths exist; reuses SPEC-dashboard-render collectors (no duplicate parser).

## Open questions
- Live-refresh: client poll (simple, dep-free) vs server file-watch + SSE (snappier, more code)?
- Dependency-graph render: Mermaid (client-side, matches repo's mermaid use) vs a JS graph lib?
- Resolved by ADR 0002 below.
