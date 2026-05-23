# Docs Preamble — Shared Init for Document-Driven Skills

This file is referenced by TAI skills that read or write to the `docs/` tree.
Include the relevant sections in your skill's preamble or init steps.

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
mkdir -p "$_DOCS_DIR/trace"
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
type: intent | decision | design | spec | trace | plan | review
parent: parent-doc-id | null
children: [child-id-1, child-id-2]
related: [related-id-1]
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

### ID Conventions

| Type | Pattern | Example |
|------|---------|---------|
| intent | `intent` | `intent` |
| decision | `dec-NNN-slug` | `dec-001-token-storage` |
| design | `design-{slug}` | `design-system`, `design-visual` |
| spec | `spec-{module}` | `spec-auth`, `spec-gateway` |
| trace | `trace-{slug}` | `trace-matrix`, `trace-code-map` |
| plan | `plan-{slug}` | `plan-tasks`, `plan-milestones` |
| review | `review` | `review` |

## Document Source Resolution

```bash
if [ -f "$_DOCS_DIR/plan/tasks.md" ]; then
  _PLAN_SOURCE="$_DOCS_DIR/plan/tasks.md"
else
  _PLAN_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/design/visual.md" ]; then
  _DESIGN_SOURCE="$_DOCS_DIR/design/visual.md"
else
  _DESIGN_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/plan/todos.md" ]; then
  _TODOS_SOURCE="$_DOCS_DIR/plan/todos.md"
else
  _TODOS_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/trace/testing.md" ]; then
  _TESTING_SOURCE="$_DOCS_DIR/trace/testing.md"
else
  _TESTING_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/trace/code-map.md" ]; then
  _ARCHITECTURE_SOURCE="$_DOCS_DIR/trace/code-map.md"
else
  _ARCHITECTURE_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/contributing.md" ]; then
  _CONTRIBUTING_SOURCE="$_DOCS_DIR/contributing.md"
else
  _CONTRIBUTING_SOURCE=""
fi
```

```bash
if [ -f "$_DOCS_DIR/changelog.md" ]; then
  _CHANGELOG_SOURCE="$_DOCS_DIR/changelog.md"
else
  _CHANGELOG_SOURCE=""
fi
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
decisions not covered by existing docs.

```markdown
---
id: review
type: review
parent: null
children: []
related: []
---

# Human Attention Log

Items below need human review. Agent appends when making decisions
not covered by existing specs or when deviating from plan.

## Open Items

### [REVIEW-NNN] Short title
- **Date:** YYYY-MM-DD
- **Skill:** /tai-{skill}
- **Context:** What was being implemented and what decision was needed
- **Decision made:** What the agent chose
- **Risk if wrong:** What breaks or needs rework
- **Related spec:** specs/{module}.md (REQ-ID) or "none"
- **Status:** PENDING

## Resolved Items

(Entries moved here after human reviews. Add resolution note.)

### [REVIEW-NNN] Short title
- ... (same fields as above)
- **Status:** APPROVED | OVERRIDDEN
- **Resolution:** Human's decision and rationale
- **Resolved by:** Human, YYYY-MM-DD
```

## Spec File Format

```markdown
---
id: spec-{module}
type: spec
parent: design-system
children: []
related: [dec-NNN-slug]
---

# {Module Name} Module

## Overview
Brief description of module purpose and boundaries.

## Requirements

### REQ-{MOD}-001: Requirement title
- **Priority:** P0 | P1 | P2
- **Description:** What the system must do
- **Acceptance:** Observable behavior that proves this works
- **Edge cases:** Known edge cases to handle

## Interfaces
API contracts, data models, events emitted.

## Dependencies
What this module depends on, what depends on it.
```

## Traceability Matrix Format

```markdown
---
id: trace-matrix
type: trace
parent: null
children: []
related: []
---

# Traceability Matrix

| REQ ID | Spec | Code | Tests | Status |
|--------|------|------|-------|--------|
| REQ-AUTH-001 | specs/auth.md | app/auth/register.py | tests/test_register.py | COVERED |

## Coverage Summary
- Total REQs: N
- COVERED: N (N%)
- PARTIAL: N (N%) — has code but no tests, or has tests but incomplete
- NOT_STARTED: N (N%)

## Untraced Code
Files with significant changes not mapped to any REQ:
- (none)
```
