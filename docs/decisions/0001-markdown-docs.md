---
id: 0001-markdown-docs
type: decision
status: accepted
parent: architecture
children: []
related: []
supersedes: none
---

# 0001-markdown-docs: Markdown document-driven framework

## Context
The repo originally documented itself in an HTML docs site (`docs.old/`, ADR
`001-html-docs`). The TAI skills now expect a markdown, frontmatter-graph,
doc-first tree (`docs/`) that downstream skills read and gate against.

## Decision
Adopt the markdown document-driven framework. Migrate the HTML tree to `docs.old/`
for reference and rebuild `docs/` via `/docs-init`. Markdown only — no HTML, no
`_assets/`.

## Consequences
- Easier: skills (plan-eng, execute, review, ship, docs-update) can read/gate docs;
  diffs are reviewable in PRs; frontmatter graph is machine-parseable.
- Cost: one-time migration; legacy HTML kept in `docs.old/` until ported.

## Alternatives considered
- Keep HTML docs — rejected: skills can't parse/gate them; not PR-diffable as content.
