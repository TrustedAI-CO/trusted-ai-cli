---
id: SPEC-docs-query
type: spec
status: implemented
approved_at: 2026-06-29T15:47:05Z
implements: [prd]
parent: architecture
children: []
related: [SPEC-dashboard-render]
code: tai/commands/dashboard.py
tests: tests/test_docs_query.py
---

# tai dashboard list / search / show — Spec (CLI, read)

> Browse the `docs/` tree from the terminal: list + filter specs/ADRs, full-text search,
> and show one doc. Read-only (extends SPEC-dashboard-render's collectors). Web rendering
> (tabs, mermaid) is deferred to the end-stage UI/UX spec — this is CLI only.

## Overview
Adds three read subcommands to `tai dashboard` for working with the document tree as a
queryable system: `list`, `search`, `show`. All read-only; reuse the frontmatter parser
and doc walk from SPEC-dashboard-render.

## Invariants
- INV1: **Read-only** (inherited). Never writes any file.
- INV2: **Never crashes on a malformed doc** (inherited) — degrade to a flagged note.

## Interface
```
tai dashboard list [--type spec|decision|all] [--status draft|approved|implemented|proposed|accepted] [--json]
tai dashboard search <query> [--json]      # match id + title + body, case-insensitive
tai dashboard show <id> [--json]           # print one doc: frontmatter summary + body
```
`list`/`search` print a table (id · type · status · title). `show <id>` prints the doc's
frontmatter (parsed) + its markdown body to the terminal **as-is**, including any
```mermaid fenced block verbatim (no rendering in CLI). `--json` emits structured data.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | docs/ with specs + ADRs | `tai dashboard list` | table of all specs + ADRs: id, type, status, title |
| R2 | `--type spec` | `tai dashboard list --type spec` | only `type: spec` docs |
| R3 | `--status draft` | `tai dashboard list --status draft` | only docs whose `status` is draft |
| R4 | a query string | `tai dashboard search auth` | docs whose id/title/body contains "auth" (case-insensitive), ranked id+title first |
| R5 | an existing doc id | `tai dashboard show SPEC-x-y` | parsed frontmatter summary + full markdown body printed; mermaid fences shown raw |
| R6 | a non-existent id | `tai dashboard show NOPE` | friendly "not found" + nearest-id hint, exit 1 |
| R7 | `--json` on any of the three | `… --json` | structured output (list of {id,type,status,title[,path]}; show adds {frontmatter, body}) |
| R8 | no docs/ | any subcommand | same friendly error + exit 1 as SPEC-dashboard-render R6 |

## Acceptance
- [ ] R1–R8 each referenced by a passing test (`test_R1_*` … in tests/test_docs_query.py).
- [ ] INV1 read-only assertion test; INV2 malformed-doc test.
- [ ] Reuses SPEC-dashboard-render's parser/walk — no duplicate frontmatter parser.

## Open questions
- Ranking for search: exact-id > title-hit > body-hit is enough for v1.
