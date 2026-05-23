---
name: docs-init
version: 1.0.0
description: |
  [TAI] Repository bootstrap for TAI workflows. Initializes the docs/ tree and .tai/
  state/cache/log directories so other skills have the source-of-truth files they expect,
  then maps the codebase into docs/trace/. Use when starting a new repo,
  onboarding an existing repo, setting up docs so skills work properly, refreshing the
  baseline project context, or when asked to "init repo", "setup tai", "bootstrap docs",
  "initialize project docs", or "make tai skills work".
allowed-tools:
  - Agent
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# TAI Setup — Repo Docs Bootstrap + Codebase Map

Initialize a repository for TAI skills by creating the shared `docs/` structure,
minimal source-of-truth documents, `.tai/` runtime directories, and the codebase
map that downstream skills consume.

This skill handles both initial bootstrap and codebase mapping. It is idempotent —
safe to re-run to refresh `docs/trace/` or repair missing docs.

## Outputs

Creates or refreshes:

```text
docs/
  intent.md
  REVIEW.md
  changelog.md
  contributing.md
  decisions/
  design/
    system.md          # architecture/design placeholder; visual.md is owned by /design-consultation
  plan/
    tasks.md
    todos.md
    milestones.md
  specs/
  trace/
    stack.md
    code-map.md
    conventions.md
    concerns.md
    testing.md
.tai/
  state/
  cache/
  logs/
```

Do **not** invent a full visual design system here. If `docs/design/visual.md`
is missing, leave it missing and recommend `/design-consultation` when visual UI
work is relevant.

## Preamble

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_DOCS_DIR="$_REPO_ROOT/docs"
_STATE_DIR="$_REPO_ROOT/.tai/state"
_CACHE_DIR="$_REPO_ROOT/.tai/cache"
_LOGS_DIR="$_REPO_ROOT/.tai/logs"
_DATE=$(date +%Y-%m-%d)
echo "BRANCH: $_BRANCH"
echo "REPO_ROOT: $_REPO_ROOT"
echo "DATE: $_DATE"
```

## Language

Respond in the same language the user is using. Keep generated `docs/` section
headers in English for machine consumption. Keep technical terms, paths, commands,
and JSON/log output in English.

## Safety Rules

- Preserve existing human-written docs. Never overwrite or delete non-empty files
  without first reading them and asking the user.
- Reorganization/deletion is allowed only after an explicit AskUserQuestion choice.
  Prefer moving legacy docs into canonical `docs/` paths over deleting them.
- `.tai/` is runtime state/cache/logs and should be gitignored.
- `docs/` is committed project knowledge and should not be gitignored.
- Do not read secrets. Note existence only for `.env*`, private keys, credential
  files, token files, and ignored files that appear secret-bearing.
- Prefer creating small, honest stubs over pretending decisions have been made.
- This skill prepares the repo; it does not do product strategy, engineering plan
  review, design-system creation, implementation, QA, or shipping.

## Step 1: Detect Current State

Run:

```bash
find "$_DOCS_DIR" -maxdepth 3 -type f 2>/dev/null | sort || true
ls "$_DOCS_DIR/trace/"*.md 2>/dev/null && echo "EXISTING_MAP=true" || echo "EXISTING_MAP=false"
test -f "$_DOCS_DIR/intent.md" && echo "HAS_INTENT=true" || echo "HAS_INTENT=false"
test -f "$_DOCS_DIR/design/visual.md" && echo "HAS_VISUAL=true" || echo "HAS_VISUAL=false"
test -f "$_DOCS_DIR/plan/tasks.md" && echo "HAS_TASKS=true" || echo "HAS_TASKS=false"
test -f "$_DOCS_DIR/plan/todos.md" && echo "HAS_TODOS=true" || echo "HAS_TODOS=false"
```

If docs already exist, treat this as an **idempotent repair/refresh**:
- Create missing directories/files.
- Preserve existing content.
- Refresh `docs/trace/` only after asking if an existing map is present.

## Step 1A: Discover Legacy or Scattered Docs

Before creating new docs, look for existing planning/design/project documents that
other skills may need but that are outside the canonical structure.

Run:

```bash
find "$_REPO_ROOT" -maxdepth 3 \( \
  -path "$_REPO_ROOT/.git" -o \
  -path "$_REPO_ROOT/.tai" -o \
  -path "$_REPO_ROOT/node_modules" -o \
  -path "$_REPO_ROOT/.venv" -o \
  -path "$_REPO_ROOT/vendor" \
\) -prune -o -type f \( \
  -iname 'PLAN.md' -o -iname 'PLANNING.md' -o -iname 'ROADMAP.md' -o \
  -iname 'TODO.md' -o -iname 'TODOS.md' -o -iname 'BACKLOG.md' -o \
  -iname 'DESIGN.md' -o -iname 'ARCHITECTURE.md' -o -iname 'SYSTEM.md' -o \
  -iname 'SPEC.md' -o -iname 'SPECS.md' -o -iname 'REVIEW.md' -o \
  -iname 'CHANGELOG.md' -o -iname 'CONTRIBUTING.md' -o -iname 'README.md' \
\) -print | sort
```

Classify findings:

| Legacy/scattered file | Canonical destination |
|---|---|
| `PLAN.md`, `PLANNING.md` | `docs/plan/tasks.md` |
| `ROADMAP.md` | `docs/plan/milestones.md` |
| `TODO.md`, `TODOS.md`, `BACKLOG.md` | `docs/plan/todos.md` |
| `DESIGN.md` | `docs/design/visual.md` if visual/brand-focused; `docs/design/system.md` if architecture-focused |
| `ARCHITECTURE.md`, `SYSTEM.md` | `docs/design/system.md` |
| `SPEC.md`, `SPECS.md` | `docs/specs/{slug}.md` |
| root `REVIEW.md` | `docs/REVIEW.md` |
| root `CHANGELOG.md` | `docs/changelog.md` |
| root `CONTRIBUTING.md` | `docs/contributing.md` |
| `README.md` | keep in place; optionally link/summarize from `docs/intent.md` |

If any legacy/scattered docs exist, read only enough to classify them and ask one
batched AskUserQuestion before reorganizing:

```text
I found existing project docs outside the canonical TAI docs structure.

Recommended migration:
1. PLAN.md → docs/plan/tasks.md (merge, then delete old file)
2. DESIGN.md → docs/design/visual.md (move, then delete old file)
3. ARCHITECTURE.md → docs/design/system.md (merge, then delete old file)
...

RECOMMENDATION: Choose A because keeping one canonical docs tree prevents skills
from reading stale files.

A) Reorganize — merge/move into canonical docs paths and delete old files after successful migration
B) Copy only — copy/merge into canonical docs paths but keep old files with a "migrated" note
C) Leave as-is — create missing canonical docs but do not touch old files
```

Rules:
- If **A**, migrate content, verify destination exists and contains the old content,
  then delete the old file. Never delete `README.md`.
- If **B**, migrate/copy content but keep old files. Add a short note at the top of
  old docs: `Moved to docs/... on YYYY-MM-DD; kept for compatibility.`
- If **C**, leave old files untouched and mention stale-doc risk in final concerns.
- If a destination already has substantial content, merge under a section named
  `## Migrated from {old path} ({date})` instead of overwriting.
- Add or preserve YAML frontmatter in the canonical destination.
- Track every migrated/copied/deleted file for the final report.

## Step 2: Initialize Directories and Gitignore

```bash
mkdir -p "$_DOCS_DIR/decisions" "$_DOCS_DIR/design" "$_DOCS_DIR/specs" "$_DOCS_DIR/trace" "$_DOCS_DIR/plan"
mkdir -p "$_STATE_DIR" "$_CACHE_DIR" "$_LOGS_DIR"
if [ -f "$_REPO_ROOT/.gitignore" ]; then
  grep -q '^\.tai/' "$_REPO_ROOT/.gitignore" 2>/dev/null || echo '.tai/' >> "$_REPO_ROOT/.gitignore"
else
  echo '.tai/' > "$_REPO_ROOT/.gitignore"
fi
```

## Step 3: Create or Merge Core Docs

Only create a file if it does not exist. If it exists, leave it untouched unless
it is empty, missing frontmatter, or the user approved migration from a legacy doc.
When merging approved legacy docs, append migrated content under a clearly labeled
section rather than replacing existing canonical content.

### `docs/intent.md`

```markdown
---
id: intent
type: intent
parent: null
children: [design-system, plan-tasks, plan-milestones]
related: [trace-code-map]
---

# Product Intent

## Purpose
TODO: Describe what this product/repo is for and who it serves.

## Current Outcome
TODO: Describe the user/business outcome this repo is meant to produce.

## Non-Goals
- TODO: Add explicit non-goals as they are decided.

## Next Recommended Skill
Run `/plan-product` for product discovery or `/tai-plan-ceo` for strategic scope review.
```

### `docs/design/system.md`

```markdown
---
id: design-system
type: design
parent: intent
children: []
related: [trace-code-map, trace-stack]
---

# System Design

## Architecture Summary
TODO: Run `/tai-plan-eng` to replace this placeholder with the reviewed system design.

## Key Decisions
- TODO: Add architectural decisions or link `docs/decisions/*.md`.

## Visual Design
Visual identity is intentionally not defined here. Run `/design-consultation` to create `docs/design/visual.md`.
```

### `docs/plan/tasks.md`

```markdown
---
id: plan-tasks
type: plan
parent: intent
children: []
related: [plan-milestones]
---

# Execution Tasks

## Backlog
- [ ] TODO: Run `/tai-plan-eng` to generate implementation-ready tasks.
```

### `docs/plan/milestones.md`

```markdown
---
id: plan-milestones
type: plan
parent: intent
children: [plan-tasks]
related: []
---

# Milestones

## Current Milestone
TODO: Define the next meaningful milestone.
```

### `docs/plan/todos.md`

```markdown
---
id: plan-todos
type: plan
parent: intent
children: []
related: []
---

# TODOS

Organize deferred work by skill/component and priority. Keep enough context that
someone can pick an item up months later.

## P0 — Critical

## P1 — High

## P2 — Medium

## P3 — Low

## P4 — Someday

## Completed
```

### `docs/REVIEW.md`

```markdown
---
id: review
type: review
parent: null
children: []
related: []
---

# Human Attention Log

Items below need human review. Agents append when making decisions not covered by
existing specs or when deviating from plan.

## Open Items

## Resolved Items
```

### `docs/changelog.md`

```markdown
---
id: changelog
type: trace
parent: null
children: []
related: []
---

# Changelog

## Unreleased
- Initialized TAI docs scaffold.
```

### `docs/contributing.md`

```markdown
---
id: contributing
type: trace
parent: null
children: []
related: [trace-conventions]
---

# Contributing

## Local Development
TODO: Run `/docs-init` to refresh conventions, then document setup commands here.

## Tests
TODO: Document test commands after detection or bootstrap.
```

### `docs/trace/testing.md`

```markdown
---
id: trace-testing
type: trace
parent: null
children: []
related: [trace-conventions]
---

# Testing Trace

## Current Test Setup
TODO: Filled by `/docs-init`, `/qa`, or `/ship` once tests are detected or bootstrapped.
```

## Step 4: Codebase Map

If `docs/trace/stack.md`, `code-map.md`, `conventions.md`, or `concerns.md`
already exist, ask:

> This repo already has trace docs. Refresh them now as part of setup?
> A) Refresh all trace docs
> B) Keep existing trace docs
> C) Refresh only selected docs

If there is no existing map, create all 4 trace documents.

### Shared Mapping Rules

1. Use Agent tool in parallel when available; otherwise run sequentially.
2. Each agent writes directly to `docs/trace/{file}.md`.
3. Include YAML frontmatter.
4. Include concrete file paths in backticks.
5. Be prescriptive, not merely descriptive.
6. Never read or quote secret-bearing files. Note existence only.
7. Limit searches; avoid unbounded scans of dependency/vendor/build dirs.

### Mapping Agent Prompts

#### Agent 1 — Stack Analysis → `docs/trace/stack.md`

Analyze manifests, runtime versions, config files, integrations, database/storage,
CI/CD, and deployment. Start with:

```yaml
---
id: trace-stack
type: trace
parent: null
children: []
related: [trace-code-map]
---
```

Use sections: `# Technology Stack`, `Languages`, `Runtime & Package Manager`,
`Frameworks & Key Dependencies`, `External Integrations`, `Data Storage`,
`CI/CD & Deployment`, `Configuration`.

#### Agent 2 — Architecture Analysis → `docs/trace/code-map.md`

Analyze directory layout, entry points, module boundaries, representative data
flow, state management, error handling, and where to add new code. Start with:

```yaml
---
id: trace-code-map
type: trace
parent: null
children: []
related: [trace-stack, trace-conventions, trace-concerns]
---
```

Use sections: `# Code Map`, `Pattern Overview`, `Directory Layout`, `Layers &
Boundaries`, `Data Flow`, `Entry Points`, `Key Abstractions`, `Error Handling
Strategy`, `Where to Add New Code`.

#### Agent 3 — Conventions Analysis → `docs/trace/conventions.md`

Analyze formatting/linting, representative source files, import order, naming,
test framework/config, test organization, mocking, and coverage. Start with:

```yaml
---
id: trace-conventions
type: trace
parent: null
children: []
related: [trace-code-map, trace-testing]
---
```

Use sections: `# Coding Conventions & Testing`, `Code Style`, `Naming Patterns`,
`Import Organization`, `Error Handling Conventions`, `Logging Conventions`,
`Testing`, `Framework & Config`, `Test Organization`, `Test Patterns`, `Mocking
Approach`, `Coverage`.

Also update `docs/trace/testing.md` with detected test commands and coverage
expectations if possible.

#### Agent 4 — Concerns Analysis → `docs/trace/concerns.md`

Analyze TODO/FIXME/HACK/XXX comments, large files, high-churn files, broad
exception handling, duplication patterns, source files without tests, dependency
concerns, and likely security review surfaces. Start with:

```yaml
---
id: trace-concerns
type: trace
parent: null
children: []
related: [trace-code-map, trace-conventions]
---
```

Use sections: `# Codebase Concerns`, `Tech Debt`, `TODO/FIXME Inventory`,
`Complexity Hotspots`, `Fragile Areas`, `Missing Test Coverage`, `Dependency
Concerns`, `Security Surface`.

## Step 5: Validate Docs

Run lightweight validation:

```bash
for f in $(find "$_DOCS_DIR" -name '*.md'); do
  if ! head -1 "$f" | grep -q '^---$'; then
    echo "MISSING FRONTMATTER: $f"
  fi
done

_IDS=$(grep -R '^id:' "$_DOCS_DIR" --include='*.md' | sed 's/.*id: *//' | sort)
echo "$_IDS" | uniq -d | sed 's/^/DUPLICATE ID: /'
```

If validation finds missing frontmatter in files this skill created, fix it.
If existing human docs are missing frontmatter, report them as concerns and do
not rewrite large files without user approval.

## Step 6: Summarize and Recommend Next Skills

Run:

```bash
find "$_DOCS_DIR" -maxdepth 3 -type f | sort
wc -l "$_DOCS_DIR/trace/"*.md 2>/dev/null || true
mkdir -p "$_LOGS_DIR"
echo "{\"skill\":\"setup\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"complete\"}" >> "$_LOGS_DIR/setup-log.jsonl"
```

Final response:

```text
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED

Docs initialized:
- [list created/kept files]

Docs reorganized:
- [list migrated/copied/deleted legacy files, or "none"]

Codebase map:
- docs/trace/stack.md — [status]
- docs/trace/code-map.md — [status]
- docs/trace/conventions.md — [status]
- docs/trace/concerns.md — [status]

Validation:
- [frontmatter/duplicate-id result]

Recommended next:
- /plan-product — if product intent is unclear
- /design-consultation — if UI/visual direction matters and docs/design/visual.md is missing
- /plan-ceo — for product/scope review
- /plan-eng — for implementation-ready plan/tasks
```

## Completion Status

- **DONE** — core docs exist, `.tai/` is gitignored, trace map written/refreshed,
  and validation has no errors in generated files.
- **DONE_WITH_CONCERNS** — setup completed but some existing docs need human cleanup,
  mapping fell back to sequential mode, or some optional context could not be inferred.
- **BLOCKED** — repository is unreadable/unwritable or required user choice was not answered.
