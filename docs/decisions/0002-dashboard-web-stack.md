---
id: 0002-dashboard-web-stack
type: decision
status: accepted
parent: architecture
children: []
related: [SPEC-dashboard-serve]
supersedes: none
---

# 0002-dashboard-web-stack: Web stack for `tai dashboard --serve`

## Context
`tai dashboard --serve` (SPEC-dashboard-serve) needs to serve a local web view of the
`docs/`-derived data. `tai` is a terminal CLI with a deliberately light dependency set;
adding a web framework is a real cost. Options span from zero-new-dep stdlib to a full
app framework.

## Options

| Option | What | Pros | Cons |
|--------|------|------|------|
| **A. stdlib `http.server` + static HTML/JS** | serve one self-contained HTML page that polls `GET /api/dashboard.json` (which calls `build_dashboard`) | **zero new deps**, tiny, starts instantly, matches "light CLI" ethos, trivially localhost-only | hand-rolled refresh; charts need a vendored JS lib or Mermaid CDN |
| **B. Streamlit** | `streamlit run` an app module | fast to build rich/interactive UI, charts free, auto-reload | **heavy dep + its own runtime/process model**, slow cold start, awkward to embed in a Typer CLI, opinionated layout |
| **C. FastAPI + Uvicorn + small frontend** | real API + SPA | flexible, scalable | overkill for a read-only local viewer; multiple new deps |

## Decision (proposed)
**Option A — stdlib `http.server` + a static self-contained HTML page** that fetches
`/api/dashboard.json`. Reuse `build_dashboard()` as the single data source (SPEC INV2).
Use Mermaid (already used elsewhere in the repo) client-side for the dependency graph.
Client-side poll for live-refresh (R4) in v1; file-watch + SSE is a later optimization.

Rationale: keeps the CLI dependency-light, localhost-only is trivial, instant startup,
and the data layer is already built. Streamlit's interactivity isn't worth a heavy
runtime for a read-only local viewer.

## Consequences
- Easier: no new runtime deps; one binary still; INV3 (localhost) trivial; CLI and web
  share one parser so numbers can't diverge.
- Harder: richer interactivity (filtering, live charts) is more manual than Streamlit.
  Acceptable for a monitoring glance; revisit with a new ADR if the viewer grows.

## Alternatives considered
- B (Streamlit) — rejected for v1: heavy dep + separate runtime in a light CLI.
- C (FastAPI) — rejected: overkill for a read-only localhost viewer.
