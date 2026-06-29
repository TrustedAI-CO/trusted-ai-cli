# Docs Preamble — Shared Init for Document-Driven Skills

This file is referenced by TAI skills that read or write to the `docs/` tree. Include
the relevant sections in your skill's preamble or init steps. For the layer model and
ownership rules, read `docs-philosophy.md` (the single source of truth).

## Directory Constants

Add these to your preamble bash block:

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_DOCS_DIR="$_REPO_ROOT/docs"
_STATE_DIR="$_REPO_ROOT/.tai/state"
_CACHE_DIR="$_REPO_ROOT/.tai/cache"
_LOGS_DIR="$_REPO_ROOT/.tai/logs"
```

## Init docs/ Structure

Run this when your skill needs to write to `docs/`. Only creates directories
that don't exist yet — safe to call multiple times.

```bash
mkdir -p "$_DOCS_DIR/decisions"
mkdir -p "$_DOCS_DIR/design"
mkdir -p "$_DOCS_DIR/specs"
mkdir -p "$_DOCS_DIR/plan"
mkdir -p "$_STATE_DIR"
mkdir -p "$_CACHE_DIR"
mkdir -p "$_LOGS_DIR"
```

## Ensure .tai/ is Gitignored

```bash
if [ -f "$_REPO_ROOT/.gitignore" ]; then
  grep -q '^\.tai/' "$_REPO_ROOT/.gitignore" 2>/dev/null || echo '.tai/' >> "$_REPO_ROOT/.gitignore"
else
  echo '.tai/' > "$_REPO_ROOT/.gitignore"
fi
```

## Frontmatter Format

Every document in `docs/` must have YAML frontmatter:

```yaml
---
id: unique-id
type: prd | decision | architecture | spec | matrix | plan | design | review
parent: parent-doc-id | null
children: [child-id-1, child-id-2]
related: [related-id-1]
status: draft | approved | accepted | implemented   # source layers only
---
```

### Rules

- `id` must be unique across all docs in the tree
- `parent` is the doc one level up in the hierarchy (null for root-level docs)
- `children` lists docs one level down
- `related` lists cross-links (decisions affecting a spec, concerns about a module)
- If A lists B as child, B must list A as parent (bidirectional)
- Every doc must be reachable from at least one other doc (no orphans)
- Exception: `REVIEW.md` is always root-level (parent: null) and doesn't need a parent reference
- Source-layer docs (`spec`, `decision`) carry `status:`. It is the gate a **human** flips.

### ID Conventions

| Type | Pattern | Example |
|------|---------|---------|
| prd | `prd` | `prd` |
| decision | `NNNN-slug` | `0001-token-storage` |
| architecture | `architecture` | `architecture` |
| spec | `SPEC-{area}-{name}` | `SPEC-auth-login`, `SPEC-hub-create` |
| design | `design-{slug}` | `design-visual` |
| matrix | `matrix` | `matrix` |
| plan | `plan-{slug}` | `plan-tasks`, `plan-backlog` |
| review | `review` | `review` |

## Document Source Resolution

```bash
[ -f "$_DOCS_DIR/prd.md" ]            && _PRD_SOURCE="$_DOCS_DIR/prd.md"            || _PRD_SOURCE=""
[ -f "$_DOCS_DIR/architecture.md" ]   && _ARCH_SOURCE="$_DOCS_DIR/architecture.md"  || _ARCH_SOURCE=""
[ -f "$_DOCS_DIR/plan/tasks.md" ]     && _PLAN_SOURCE="$_DOCS_DIR/plan/tasks.md"    || _PLAN_SOURCE=""
[ -f "$_DOCS_DIR/design/visual.md" ]  && _DESIGN_SOURCE="$_DOCS_DIR/design/visual.md" || _DESIGN_SOURCE=""
[ -f "$_DOCS_DIR/plan/backlog.md" ]   && _BACKLOG_SOURCE="$_DOCS_DIR/plan/backlog.md" || _BACKLOG_SOURCE=""
[ -f "$_DOCS_DIR/matrix.md" ]         && _MATRIX_SOURCE="$_DOCS_DIR/matrix.md"      || _MATRIX_SOURCE=""
[ -f "$_DOCS_DIR/contributing.md" ]   && _CONTRIBUTING_SOURCE="$_DOCS_DIR/contributing.md" || _CONTRIBUTING_SOURCE=""
[ -f "$_DOCS_DIR/changelog.md" ]      && _CHANGELOG_SOURCE="$_DOCS_DIR/changelog.md" || _CHANGELOG_SOURCE=""
```

## State Directory Migration

Skills that previously wrote to `~/.tai-skills/projects/$_SLUG/` should write to
`.tai/state/` instead:

```bash
if [ -d "$_STATE_DIR" ]; then
  _REVIEW_LOG="$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl"
elif [ -d "$HOME/.tai-skills/projects/$_SLUG" ]; then
  _REVIEW_LOG="$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
else
  mkdir -p "$_STATE_DIR"
  _REVIEW_LOG="$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl"
fi
```

## REVIEW.md Format

`docs/REVIEW.md` is the human attention log. Agent appends entries when making
decisions not covered by existing docs, or when it hits a doc-first conflict.

```markdown
---
id: review
type: review
parent: null
children: []
related: []
---

# Human Attention Log

Items below need human review. Agent appends when making decisions not covered by
existing specs, when deviating from plan, or when a source layer is out of date.

## Open Items

### [REVIEW-NNN] Short title
- **Date:** YYYY-MM-DD
- **Skill:** /tai-{skill}
- **Context:** What was being implemented and what decision was needed
- **Decision made:** What the agent chose (or: flagged, awaiting human)
- **Risk if wrong:** What breaks or needs rework
- **Related spec:** SPEC-{area}-{name} (R-id) or "none"
- **Status:** PENDING

## Resolved Items

(Entries moved here after human reviews. Add resolution note.)

### [REVIEW-NNN] Short title
- ... (same fields as above)
- **Status:** APPROVED | OVERRIDDEN
- **Resolution:** Human's decision and rationale
- **Resolved by:** Human, YYYY-MM-DD
```

## Spec File Format (L2 — behavioral contract)

One spec = one public surface. Agent drafts at `status: draft`; a **human** sets
`status: approved` before any code under `code:` may merge.

```markdown
---
id: SPEC-{area}-{name}
type: spec
status: draft            # draft → approved (human gate) → implemented
implements: [prd, 0003-some-adr]
parent: architecture
children: []
related: []
code: {dir or file under an architecture.md §4 container}
tests: {dir or file}
---

# {Surface Name}

## Overview
What this surface does and its boundary.

## Invariants
Always-true properties (highest review priority).
- INV1: {property that must always hold}

## Interface
API contracts, data models, events emitted.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | {precondition} | {action, concrete values} | {observable result} |
| R2 | ... | ... | ... |

## Acceptance
- [ ] Each Behavior row ID (R1…RN) is referenced by a passing test
      (`test_R3_*` or `// covers: SPEC-{area}-{name} R3`).
- [ ] Each Invariant has a property/assertion test.
- [ ] `code:` and `tests:` paths exist; `code:` sits under a container in `architecture.md` §4.
```

## Traceability Matrix Format (`docs/matrix.md`, derived — generated, never hand-authored)

```markdown
---
id: matrix
type: matrix
parent: null
children: []
related: []
---

# Traceability Matrix

| Spec | R-id | Code | Test | Status |
|------|------|------|------|--------|
| SPEC-auth-login | R1 | app/auth/login.py | tests/test_login.py::test_R1_* | COVERED |

## Coverage Summary
- Total Behavior rows: N
- COVERED: N (N%)
- PARTIAL: N (N%) — has code but no test, or test but incomplete
- NOT_STARTED: N (N%)

## Untraced Code
Files with significant changes not mapped to any spec R-id:
- (none)
```
