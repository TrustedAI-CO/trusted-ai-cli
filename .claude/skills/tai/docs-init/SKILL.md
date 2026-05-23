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
  _assets/
    style.css
    docs.js
  intent.html
  REVIEW.html
  changelog.html
  contributing.html
  decisions/
    _template.html       # ADR template (proposed→accepted→superseded)
  design/
    system.html          # architecture/design placeholder; visual.html is owned by /design-consultation
  plan/
    tasks.html
    todos.html
    milestones.html
  specs/
    _template.html       # feature spec template (draft→implemented)
  trace/
    stack.html
    code-map.html
    conventions.html
    concerns.html
    testing.html
    matrix.html          # requirements traceability matrix
.tai/
  state/
  cache/
  logs/
```

Do **not** invent a full visual design system here. If `docs/design/visual.html`
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
ls "$_DOCS_DIR/trace/"*.html 2>/dev/null && echo "EXISTING_MAP=true" || echo "EXISTING_MAP=false"
test -f "$_DOCS_DIR/intent.html" && echo "HAS_INTENT=true" || echo "HAS_INTENT=false"
test -f "$_DOCS_DIR/design/visual.html" && echo "HAS_VISUAL=true" || echo "HAS_VISUAL=false"
test -f "$_DOCS_DIR/plan/tasks.html" && echo "HAS_TASKS=true" || echo "HAS_TASKS=false"
test -f "$_DOCS_DIR/plan/todos.html" && echo "HAS_TODOS=true" || echo "HAS_TODOS=false"
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
  -iname 'CHANGELOG.md' -o -iname 'CONTRIBUTING.md' -o -iname 'README.md' -o \
  -iname 'PLAN.html' -o -iname 'PLANNING.html' -o -iname 'ROADMAP.html' -o \
  -iname 'TODO.html' -o -iname 'TODOS.html' -o -iname 'BACKLOG.html' -o \
  -iname 'DESIGN.html' -o -iname 'ARCHITECTURE.html' -o -iname 'SYSTEM.html' -o \
  -iname 'SPEC.html' -o -iname 'SPECS.html' -o -iname 'REVIEW.html' -o \
  -iname 'CHANGELOG.html' -o -iname 'CONTRIBUTING.html' \
\) -print | sort
```

Classify findings:

| Legacy/scattered file | Canonical destination |
|---|---|
| `PLAN.md`, `PLANNING.md` | `docs/plan/tasks.html` |
| `ROADMAP.md` | `docs/plan/milestones.html` |
| `TODO.md`, `TODOS.md`, `BACKLOG.md` | `docs/plan/todos.html` |
| `DESIGN.md` | `docs/design/visual.html` if visual/brand-focused; `docs/design/system.html` if architecture-focused |
| `ARCHITECTURE.md`, `SYSTEM.md` | `docs/design/system.html` |
| `SPEC.md`, `SPECS.md` | `docs/specs/{slug}.html` |
| root `REVIEW.md` | `docs/REVIEW.html` |
| root `CHANGELOG.md` | `docs/changelog.html` |
| root `CONTRIBUTING.md` | `docs/contributing.html` |
| `README.md` | keep in place; optionally link/summarize from `docs/intent.html` |

If any legacy/scattered docs exist, read only enough to classify them and ask one
batched AskUserQuestion before reorganizing:

```text
I found existing project docs outside the canonical TAI docs structure.

Recommended migration:
1. PLAN.md → docs/plan/tasks.html (merge, then delete old file)
2. DESIGN.md → docs/design/visual.html (move, then delete old file)
3. ARCHITECTURE.md → docs/design/system.html (merge, then delete old file)
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
- Convert migrated Markdown content to HTML when placing into canonical destinations.
- Track every migrated/copied/deleted file for the final report.

## Step 2: Initialize Directories and Gitignore

```bash
mkdir -p "$_DOCS_DIR/decisions" "$_DOCS_DIR/design" "$_DOCS_DIR/specs" "$_DOCS_DIR/trace" "$_DOCS_DIR/plan" "$_DOCS_DIR/_assets"
mkdir -p "$_STATE_DIR" "$_CACHE_DIR" "$_LOGS_DIR"
if [ -f "$_REPO_ROOT/.gitignore" ]; then
  grep -q '^\.tai/' "$_REPO_ROOT/.gitignore" 2>/dev/null || echo '.tai/' >> "$_REPO_ROOT/.gitignore"
else
  echo '.tai/' > "$_REPO_ROOT/.gitignore"
fi
```

Copy shared assets from the tai bundle:

```bash
# Copy shared assets from tai bundle
python3 -c "
from tai.commands.docs import _copy_assets
from pathlib import Path
_copy_assets(Path('$_DOCS_DIR/_assets'))
print('Assets copied to $_DOCS_DIR/_assets/')
"
```

## Step 3: Create or Merge Core Docs

Only create a file if it does not exist. If it exists, leave it untouched unless
it is empty or the user approved migration from a legacy doc.
When merging approved legacy docs, append migrated content under a clearly labeled
section rather than replacing existing canonical content.

### `docs/intent.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="intent">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Product Intent</title>
  <link rel="stylesheet" href="_assets/style.css">
</head>
<body>
  <article>
    <h1>Product Intent</h1>
    <section data-section="context">
      <h2>Context</h2>
      <p>TODO: Describe the background and context for this product/repo.</p>
    </section>
    <section data-section="problem">
      <h2>Problem</h2>
      <p>TODO: Describe the problem this product/repo solves and who it serves.</p>
    </section>
    <section data-section="solution">
      <h2>Solution</h2>
      <p>TODO: Describe the solution approach and current outcome.</p>
    </section>
    <section data-section="success-criteria">
      <h2>Success Criteria</h2>
      <ul>
        <li>TODO: Add explicit success criteria as they are decided.</li>
      </ul>
      <p>Run <code>/plan-product</code> for product discovery or <code>/tai-plan-ceo</code> for strategic scope review.</p>
    </section>
  </article>
  <script src="_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/design/system.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="design">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>System Design</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>System Design</h1>
    <section data-section="overview">
      <h2>Overview</h2>
      <p>TODO: Run <code>/tai-plan-eng</code> to replace this placeholder with the reviewed system design.</p>
    </section>
    <section data-section="components">
      <h2>Components</h2>
      <ul>
        <li>TODO: Add architectural components or link <code>docs/decisions/*.html</code>.</li>
      </ul>
      <p>Visual identity is intentionally not defined here. Run <code>/design-consultation</code> to create <code>docs/design/visual.html</code>.</p>
    </section>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/plan/tasks.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="plan">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Execution Tasks</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Execution Tasks</h1>
    <section data-section="phases">
      <h2>Phases</h2>
      <ul>
        <li>TODO: Run <code>/tai-plan-eng</code> to generate implementation-ready tasks.</li>
      </ul>
    </section>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/plan/milestones.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="plan">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Milestones</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Milestones</h1>
    <section data-section="phases">
      <h2>Phases</h2>
      <p>TODO: Define the next meaningful milestone.</p>
    </section>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/plan/todos.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="plan">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>TODOs</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>TODOs</h1>
    <p>Organize deferred work by skill/component and priority. Keep enough context that
    someone can pick an item up months later.</p>
    <section data-section="phases">
      <h2>Phases</h2>
      <h3>P0 — Critical</h3>
      <h3>P1 — High</h3>
      <h3>P2 — Medium</h3>
      <h3>P3 — Low</h3>
      <h3>P4 — Someday</h3>
      <h3>Completed</h3>
    </section>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/REVIEW.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="review">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Human Attention Log</title>
  <link rel="stylesheet" href="_assets/style.css">
</head>
<body>
  <article>
    <h1>Human Attention Log</h1>
    <p>Items below need human review. Agents append when making decisions not covered by
    existing specs or when deviating from plan.</p>
    <section data-section="findings">
      <h2>Findings</h2>
      <h3>Open Items</h3>
      <h3>Resolved Items</h3>
    </section>
  </article>
  <script src="_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/changelog.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="changelog">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Changelog</title>
  <link rel="stylesheet" href="_assets/style.css">
</head>
<body>
  <article>
    <h1>Changelog</h1>
    <h2>Unreleased</h2>
    <ul>
      <li>Initialized TAI docs scaffold.</li>
    </ul>
  </article>
  <script src="_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/contributing.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="guide">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Contributing</title>
  <link rel="stylesheet" href="_assets/style.css">
</head>
<body>
  <article>
    <h1>Contributing</h1>
    <section data-section="overview">
      <h2>Overview</h2>
      <h3>Local Development</h3>
      <p>TODO: Run <code>/docs-init</code> to refresh conventions, then document setup commands here.</p>
      <h3>Tests</h3>
      <p>TODO: Document test commands after detection or bootstrap.</p>
    </section>
  </article>
  <script src="_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/trace/testing.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Testing Trace</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Testing Trace</h1>
    <h2>Current Test Setup</h2>
    <p>TODO: Filled by <code>/docs-init</code>, <code>/qa</code>, or <code>/ship</code> once tests are detected or bootstrapped.</p>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

### `docs/specs/_template.html`

This is a template for creating new feature specifications. Do not fill it in —
skills like `/plan-product` and `/plan-eng` create concrete specs from this template.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="spec">
  <meta name="doc-status" content="draft">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>{Feature Name}</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>{Feature Name}</h1>

    <section data-section="problem">
      <h2>Problem</h2>
      <p>Why this needs to exist. What user pain or business gap.</p>
    </section>

    <section data-section="requirements">
      <h2>Requirements</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Requirement</th><th>Priority</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td>REQ-001</td><td>{requirement}</td><td>must</td><td>open</td></tr>
          <tr><td>REQ-002</td><td>{requirement}</td><td>should</td><td>open</td></tr>
          <tr><td>REQ-003</td><td>{requirement}</td><td>could</td><td>open</td></tr>
        </tbody>
      </table>
      <p>Priority uses MoSCoW: <code>must</code>, <code>should</code>, <code>could</code>, <code>wont</code>.<br>
      Status: <code>open</code>, <code>in-progress</code>, <code>done</code>, <code>cut</code>.</p>
    </section>

    <section data-section="acceptance-criteria">
      <h2>Acceptance Criteria</h2>
      <ul>
        <li>{concrete, testable criterion}</li>
      </ul>
    </section>

    <h2>Dependencies</h2>
    <ul>
      <li>{other spec, external service, or blocker}</li>
    </ul>

    <h2>Out of Scope</h2>
    <ul>
      <li>{explicit non-goals for this spec}</li>
    </ul>

    <h2>Open Questions</h2>
    <ul>
      <li>{unresolved decisions — spawn ADR when answered}</li>
    </ul>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

### `docs/decisions/_template.html`

This is a template for Architecture Decision Records. Skills like `/plan-eng`
and `/research-tech` create concrete ADRs from this template.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="decision">
  <meta name="doc-status" content="proposed">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>ADR-{NNN}: {Decision Title}</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>ADR-{NNN}: {Decision Title}</h1>

    <section data-section="context">
      <h2>Context</h2>
      <p>{What is the issue that we're seeing that is motivating this decision?}</p>
      <p><strong>Related spec:</strong> <a href="../specs/{slug}.html">{spec title}</a></p>
    </section>

    <h2>Decision Drivers</h2>
    <ul>
      <li>{driver 1}</li>
      <li>{driver 2}</li>
    </ul>

    <h2>Options Considered</h2>
    <h3>Option A: {name}</h3>
    <p>{description, pros, cons}</p>
    <h3>Option B: {name}</h3>
    <p>{description, pros, cons}</p>

    <section data-section="decision">
      <h2>Decision</h2>
      <p>{Which option was chosen and why.}</p>
    </section>

    <section data-section="consequences">
      <h2>Consequences</h2>
      <ul>
        <li>{positive consequence}</li>
        <li>{negative consequence or trade-off}</li>
      </ul>
    </section>

    <h2>Revisit Triggers</h2>
    <ul>
      <li>{condition that would make us reconsider this decision}</li>
    </ul>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

### `docs/trace/matrix.html`

The traceability matrix — the "are we done?" dashboard. Links specs, requirements,
implementation files, and test files.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Requirements Traceability Matrix</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Requirements Traceability Matrix</h1>

    <table>
      <thead>
        <tr>
          <th>REQ ID</th><th>Spec</th><th>Requirement</th>
          <th>Impl Files</th><th>Test Files</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colspan="6"><em>No specs created yet. Run <code>/plan-product</code> or <code>/plan-eng</code> to create specs.</em></td>
        </tr>
      </tbody>
    </table>

    <h2>Coverage Summary</h2>
    <ul>
      <li>Total REQs: 0</li>
      <li>Done: 0</li>
      <li>In Progress: 0</li>
      <li>Open: 0</li>
      <li>Cut: 0</li>
    </ul>

    <h2>Untraced Code</h2>
    <p>Files with significant logic not linked to any REQ — populated by <code>/docs-update</code>.</p>
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Replace `YYYY-MM-DD` with the actual date (`$_DATE`).

## Step 4: Codebase Map

If `docs/trace/stack.html`, `code-map.html`, `conventions.html`, or `concerns.html`
already exist, ask:

> This repo already has trace docs. Refresh them now as part of setup?
> A) Refresh all trace docs
> B) Keep existing trace docs
> C) Refresh only selected docs

If there is no existing map, create all 4 trace documents.

### Shared Mapping Rules

1. Use Agent tool in parallel when available; otherwise run sequentially.
2. Each agent writes directly to `docs/trace/{file}.html`.
3. Use HTML format with `<meta name="doc-type" content="trace">` and `<meta name="doc-date" content="YYYY-MM-DD">`.
4. Include concrete file paths in `<code>` tags.
5. Be prescriptive, not merely descriptive.
6. Never read or quote secret-bearing files. Note existence only.
7. Limit searches; avoid unbounded scans of dependency/vendor/build dirs.
8. For all trace docs in `docs/trace/`, use `../_assets/style.css` and `../_assets/docs.js`.

### Mapping Agent Prompts

#### Agent 1 — Stack Analysis → `docs/trace/stack.html`

Analyze manifests, runtime versions, config files, integrations, database/storage,
CI/CD, and deployment. Write an HTML file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Technology Stack</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Technology Stack</h1>
    <!-- Sections: Languages, Runtime & Package Manager,
         Frameworks & Key Dependencies, External Integrations,
         Data Storage, CI/CD & Deployment, Configuration -->
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

#### Agent 2 — Architecture Analysis → `docs/trace/code-map.html`

Analyze directory layout, entry points, module boundaries, representative data
flow, state management, error handling, and where to add new code. Write an HTML file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Code Map</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Code Map</h1>
    <!-- Sections: Pattern Overview, Directory Layout, Layers &
         Boundaries, Data Flow, Entry Points, Key Abstractions,
         Error Handling Strategy, Where to Add New Code -->
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

#### Agent 3 — Conventions Analysis → `docs/trace/conventions.html`

Analyze formatting/linting, representative source files, import order, naming,
test framework/config, test organization, mocking, and coverage. Write an HTML file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Coding Conventions &amp; Testing</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Coding Conventions &amp; Testing</h1>
    <!-- Sections: Code Style, Naming Patterns, Import Organization,
         Error Handling Conventions, Logging Conventions, Testing,
         Framework & Config, Test Organization, Test Patterns,
         Mocking Approach, Coverage -->
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

Also update `docs/trace/testing.html` with detected test commands and coverage
expectations if possible.

#### Agent 4 — Concerns Analysis → `docs/trace/concerns.html`

Analyze TODO/FIXME/HACK/XXX comments, large files, high-churn files, broad
exception handling, duplication patterns, source files without tests, dependency
concerns, and likely security review surfaces. Write an HTML file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="YYYY-MM-DD">
  <title>Codebase Concerns</title>
  <link rel="stylesheet" href="../_assets/style.css">
</head>
<body>
  <article>
    <h1>Codebase Concerns</h1>
    <!-- Sections: Tech Debt, TODO/FIXME Inventory, Complexity Hotspots,
         Fragile Areas, Missing Test Coverage, Dependency Concerns,
         Security Surface -->
  </article>
  <script src="../_assets/docs.js"></script>
</body>
</html>
```

## Step 5: Validate Docs

Run validation using the tai Python validator:

```bash
python3 -c "
from tai.commands.docs import validate_all, find_docs_root
issues = validate_all(find_docs_root())
if issues:
    for path, errs in issues.items():
        for e in errs:
            print(f'ISSUE: {path}: {e}')
else:
    print('All docs valid.')
"
```

If validation finds issues in files this skill created, fix them.
If existing human docs have issues, report them as concerns and do
not rewrite large files without user approval.

## Step 6: Summarize and Recommend Next Skills

Run:

```bash
find "$_DOCS_DIR" -maxdepth 3 -type f | sort
wc -l "$_DOCS_DIR/trace/"*.html 2>/dev/null || true
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
- docs/trace/stack.html — [status]
- docs/trace/code-map.html — [status]
- docs/trace/conventions.html — [status]
- docs/trace/concerns.html — [status]

Validation:
- [validation result]

Recommended next:
- /plan-product — if product intent is unclear
- /design-consultation — if UI/visual direction matters and docs/design/visual.html is missing
- /plan-ceo — for product/scope review
- /plan-eng — for implementation-ready plan/tasks
```

To serve docs locally, run: `tai docs serve`

## Completion Status

- **DONE** — core docs exist, `.tai/` is gitignored, trace map written/refreshed,
  and validation has no errors in generated files.
- **DONE_WITH_CONCERNS** — setup completed but some existing docs need human cleanup,
  mapping fell back to sequential mode, or some optional context could not be inferred.
- **BLOCKED** — repository is unreadable/unwritable or required user choice was not answered.
