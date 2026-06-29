---
id: SPEC-dashboard-render
type: spec
status: approved
approved_at: 2026-06-29T14:39:39Z
implements: [prd]
parent: architecture
children: []
related: [0001-markdown-docs]
code: tai/commands/dashboard.py
tests: tests/test_dashboard.py
---

# tai dashboard — Spec

> One public surface: the `tai dashboard` CLI command. Reads the `docs/` tree and renders
> a single-screen project overview so a human can glance project state + monitor what's
> going on. Read-only.

## Overview
`tai dashboard` parses the committed `docs/` document-driven tree (frontmatter graph,
spec statuses, matrix, REVIEW.md, changelog) and renders a one-screen terminal summary
of project state. It is a **monitoring/overview** tool — the human's "glance" at the
whole project. It never writes to `docs/`.

## Invariants
- INV1: **Read-only.** The command never creates, edits, or deletes any file under
  `docs/` (or anywhere). It only reads.
- INV2: **Never crashes on a malformed doc.** A missing field, broken YAML, or bad link
  degrades to a flagged warning in the output, never an unhandled exception.

## Interface
```
tai dashboard            # render the overview to the terminal
tai dashboard --json     # emit the same data as structured JSON (no decoration)
```
Exit codes: `0` on success (including when doc-health warnings exist); `1` only when
`docs/` is absent or unreadable.

JSON shape (stable keys):
```
{
  "pipeline": {"draft": int, "approved": int, "implemented": int, "total": int},
  "coverage": {"covered": int, "total": int, "percent": number|null},
  "needs_you": [{"id": str, "title": str}],     # REVIEW.md PENDING items
  "recent":    [{"version": str, "entries": [str]}],  # changelog, newest first
  "doc_health": {"orphans": [str], "broken_links": [str], "missing_frontmatter": [str]}
}
```

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | a repo with a `docs/` tree | `tai dashboard` | prints a single screen with sections: Pipeline, Coverage, Needs-You, Recent, Doc Health |
| R2 | `docs/specs/*.md` with statuses (ignoring `*template*`) | `tai dashboard` | Pipeline shows counts grouped by `status` (draft/approved/implemented) + total |
| R3 | `docs/REVIEW.md` has N `Status: PENDING` open items | `tai dashboard` | Needs-You lists each PENDING item id+title with a count badge |
| R4 | `docs/matrix.md` has a Coverage Summary | `tai dashboard` | Coverage shows COVERED/total and percent (or "n/a" when total is 0) |
| R5 | `docs/changelog.md` with an Unreleased + version sections | `tai dashboard` | Recent shows the newest version block (or Unreleased) entries |
| R6 | no `docs/` directory in the repo | `tai dashboard` | prints a friendly error + hint "run /docs-init or tai ..." and exits 1 |
| R7 | a doc with missing frontmatter, an orphan, or a broken parent/children/related link | `tai dashboard` | Doc Health lists each issue; exit stays 0 (warnings, not failure) |
| R8 | `--json` flag | `tai dashboard --json` | emits the JSON shape above, no terminal decoration; same data as the rendered view |

## Acceptance
- [ ] Each Behavior row R1–R8 referenced by a passing test (`test_R1_*` … or `# covers: SPEC-dashboard-render R1`).
- [ ] INV1 (read-only) has an assertion test: docs/ mtime/content unchanged after a run.
- [ ] INV2 (no crash) has a test feeding a malformed doc.
- [ ] `code:` `tai/commands/dashboard.py` and `tests:` `tests/test_dashboard.py` exist; code sits under the "Command groups" container (architecture.md §4).

## Open questions
- Rendering lib: reuse the existing `tai/core/style.py` helpers vs `rich` directly? (decide at execute)
