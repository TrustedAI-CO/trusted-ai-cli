---
name: map
version: 1.0.0
description: |
  [TAI] Codebase mapping: spawns parallel agents to analyze stack, architecture,
  conventions, and concerns. Produces structured Markdown documents in .tai/map/
  that other skills can consume as context. Run once per project, refresh as needed.
  Use when starting work on an unfamiliar codebase, before /plan-eng or /plan-ceo,
  or when someone asks "what does this codebase look like".
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

# Codebase Mapping

Analyze the current codebase and produce structured reference documents that other
skills and future sessions can consume. Output goes to `.tai/map/`.

## Preamble (run first)

```bash
_DATE=$(date +%Y-%m-%d)
echo "DATE: $_DATE"
ls .tai/map/*.md 2>/dev/null && echo "EXISTING_MAP=true" || echo "EXISTING_MAP=false"
```

## Language

Respond in the same language the user is using. If the user writes in Japanese,
respond entirely in Japanese. If Vietnamese, respond entirely in Vietnamese.
Keep these in English regardless of language:
- Severity labels: [CRITICAL], [WARNING], [AUTO-FIXED], [HIGH], [MEDIUM], [LOW]
- Section headers in generated `.tai/map/*.md` files (always English for machine consumption)
- Log/machine-readable output (.jsonl entries, bash commands)
- Technical terms: SQL, CSRF, API, LLM, XSS, etc.
- File paths and code snippets
Translate all prose, explanations, and AskUserQuestion text.

## Completion Status Protocol

When completing this skill, report status using one of:
- **DONE** — All 4 documents written successfully.
- **DONE_WITH_CONCERNS** — Some documents written, but issues occurred. List each concern.
- **BLOCKED** — Cannot proceed. State what is blocking and what was tried.

## Step 1: Check for existing map

If `EXISTING_MAP=true`, use AskUserQuestion:

"This project already has a codebase map in `.tai/map/`. What would you like to do?"
- A) Refresh — delete existing and remap the full codebase
- B) Keep existing — skip mapping
- C) Update specific documents only

If **A**: delete `.tai/map/` and continue to Step 2.
If **B**: read and summarize the existing map for the user, then stop.
If **C**: ask which documents to update using this mapping:
  - stack → Agent 1
  - architecture → Agent 2
  - conventions → Agent 3
  - concerns → Agent 4

  Confirm the selection with the user, then spawn only those agents in Step 3.

## Step 2: Create output directory

```bash
mkdir -p .tai/map
```

If `.gitignore` exists and does not already contain `.tai/`, append it:

```bash
grep -q '^\.tai/' .gitignore 2>/dev/null || echo '.tai/' >> .gitignore
```

## Step 3: Spawn mapping agents

Launch 4 agents in parallel using the Agent tool. Each agent explores one focus area
and writes one document directly to `.tai/map/`.

**All agents share these rules:**

1. Explore thoroughly using Read, Glob, Grep, and Bash (for `wc -l`, `find`, etc.)
2. Write your document directly to `.tai/map/{filename}.md` using the Write tool
3. Run `date +%Y-%m-%d` to get the current date for the "Analysis date" header
4. Always include file paths in backticks: `src/core/auth.py`
5. Be prescriptive ("Use snake_case for functions") not descriptive ("snake_case is used")
6. Return only a brief confirmation — do NOT return document contents
7. NEVER read or quote contents from any of these file patterns. Note their
   EXISTENCE only:
   - `.env`, `.env.*`, `*.env` — environment variables with secrets
   - `*.pem`, `*.key`, `*.p12`, `*.pfx` — certificates and private keys
   - `*_rsa`, `*_ed25519`, `*_ecdsa`, `id_rsa*`, `id_ed25519*` — SSH keys
   - `*secret*`, `*credential*`, `*token*` — secret/credential files
   - `serviceAccountKey.json`, `google-services.json` — cloud service credentials
   - `.npmrc`, `.pypirc`, `.netrc` — package manager auth tokens
   - `.vault-token` — HashiCorp Vault tokens
   - Any `*.json` file whose name contains `key`, `auth`, `secret`, or `credential`
   - Any file in `.gitignore` that appears to contain secrets
8. Limit searches: use `head_limit` on Grep, avoid unbounded Glob on huge directories.
   Focus on `src/`, `lib/`, `app/`, and root config files first.

---

### Agent 1: Stack Analysis

**Prompt:**

```
Analyze this codebase's technology stack. Write your findings to .tai/map/stack.md

Run `date +%Y-%m-%d` first to get today's date for the document header.

Explore:
- Package manifests (package.json, pyproject.toml, go.mod, Cargo.toml, requirements.txt)
- Runtime versions (.nvmrc, .python-version, .tool-versions, rust-toolchain.toml)
- Config files (tsconfig.json, biome.json, ruff.toml, .eslintrc.*, etc.)
- External service integrations (grep for SDK imports: stripe, supabase, aws, etc.)
- Database connections (grep for connection strings, ORM config)
- CI/CD config (.github/workflows/, Dockerfile, docker-compose.yml)
- Note existence of .env files but NEVER read their contents

Write .tai/map/stack.md with this structure:

# Technology Stack
Analysis date: [insert date]

## Languages
- Primary: [language] [version] — [where used]
- Secondary: [language] [version] — [where used]

## Runtime & Package Manager
- [runtime] [version]
- [package manager] — lockfile: [present/missing]

## Frameworks & Key Dependencies
- [framework] [version] — [purpose]

## External Integrations
For each integration found:
- [Service] — [what it's used for]
  - SDK/Client: [package]
  - Auth: [env var name, existence only]

## Data Storage
- [database type/provider]
  - Client: [ORM/driver]
- File storage: [service or "local filesystem"]
- Caching: [service or "none detected"]

## CI/CD & Deployment
- Hosting: [platform or "not detected"]
- CI: [service and config file path]

## Configuration
- Build config: [files]
- Environment: [how configured, DO NOT include values]

Return only: "Stack analysis complete. Wrote .tai/map/stack.md ({N} lines)."
```

### Agent 2: Architecture Analysis

**Prompt:**

```
Analyze this codebase's architecture and structure. Write your findings to .tai/map/architecture.md

Run `date +%Y-%m-%d` first to get today's date for the document header.

Explore:
- Directory layout (top-level and one level deep)
- Entry points (main.*, index.*, app.*, server.*)
- Module boundaries and import patterns
- Data flow between layers (how a request/command flows through the system)
- State management approach
- Error handling strategy (grep for try/catch, raise, Error classes)
- Key abstractions (base classes, interfaces, protocols)

Write .tai/map/architecture.md with this structure:

# Architecture
Analysis date: [insert date]

## Pattern Overview
- Overall: [pattern name — MVC, layered, hexagonal, microservices, CLI, etc.]
- Key characteristics: [2-3 bullets]

## Directory Layout
```
project-root/
├── [dir]/          # [Purpose]
└── [file]          # [Purpose]
```

## Layers & Boundaries
For each layer:
- **[Layer name]**
  - Purpose: [what this layer does]
  - Location: `[path]`
  - Depends on: [what it imports]
  - Used by: [what imports it]

## Data Flow
Trace one representative flow through the system:
1. [Entry point] receives [input]
2. [Layer] processes [what]
3. [Layer] persists/returns [result]

## Entry Points
- `[path]`: [what it does, how it's invoked]

## Key Abstractions
- `[class/interface]` in `[path]`: [purpose, what extends/implements it]

## Error Handling Strategy
- Pattern: [how errors flow — exceptions, result types, error codes]
- Error hierarchy: [base error class, if any]

## Where to Add New Code
- New feature: `[path]`
- New tests: `[path]`
- New utility: `[path]`
- New command/route: `[path]`

Return only: "Architecture analysis complete. Wrote .tai/map/architecture.md ({N} lines)."
```

### Agent 3: Conventions Analysis

**Prompt:**

```
Analyze this codebase's coding conventions and testing patterns. Write your findings to .tai/map/conventions.md

Run `date +%Y-%m-%d` first to get today's date for the document header.

Explore:
- Linting/formatting config (eslint, prettier, ruff, black, biome, etc.)
- Sample source files — read 3-5 representative files to extract patterns
- Import organization patterns
- Naming patterns (files, functions, variables, classes)
- Test framework and config (jest, vitest, pytest, go test, etc.)
- Test file organization (co-located vs separate directory)
- Test patterns (read 2-3 test files for mocking, fixture, assertion style)
- Coverage config and thresholds

Write .tai/map/conventions.md with this structure:

# Coding Conventions & Testing
Analysis date: [insert date]

## Code Style
- Formatter: [tool and config file]
- Linter: [tool and config file]
- Key rules: [notable settings]

## Naming Patterns
- Files: [pattern — kebab-case, snake_case, PascalCase]
- Functions: [pattern with example]
- Variables: [pattern]
- Classes/Types: [pattern]

## Import Organization
- Order: [1. stdlib, 2. third-party, 3. local — or whatever is used]
- Path aliases: [if any]

## Error Handling Conventions
- Pattern: [how this codebase handles errors — show a real example]

## Logging Conventions
- Framework: [tool or "print/console"]
- Pattern: [when and how to log]

## Testing

### Framework & Config
- Runner: [framework] [version]
- Config: `[config file path]`
- Run command: `[command]`

### Test Organization
- Location: [co-located / separate `tests/` directory]
- Naming: [pattern — test_*.py, *.test.ts, etc.]

### Test Patterns
Show a representative test from the codebase:
```
[actual test code excerpt showing setup/assertion style]
```

### Mocking Approach
- Framework: [tool]
- Pattern: [what gets mocked, what doesn't]

### Coverage
- Target: [percentage or "not enforced"]
- Command: `[coverage command]`

Return only: "Conventions analysis complete. Wrote .tai/map/conventions.md ({N} lines)."
```

### Agent 4: Concerns Analysis

**Prompt:**

```
Analyze this codebase for technical debt, known issues, and areas of concern. Write your findings to .tai/map/concerns.md

Run `date +%Y-%m-%d` first to get today's date for the document header.

Explore:
- TODO/FIXME/HACK/XXX comments (grep across the codebase)
- Large files (find files over 500 lines — potential complexity hotspots)
- Files with many recent changes (git log --since=30.days if git repo)
- Empty catch blocks, broad exception handling (grep for catch-all patterns)
- Duplicated code patterns (similar function signatures across files)
- Missing test coverage (source files without corresponding test files)
- Dependency health (outdated, deprecated, or security-flagged packages)
- DO NOT read .env or credential files — note existence only

Write .tai/map/concerns.md with this structure:

# Codebase Concerns
Analysis date: [insert date]

## Tech Debt
For each area found:
- **[Area/Component]**
  - Issue: [what's the shortcut or workaround]
  - Files: `[file paths]`
  - Impact: [what breaks or degrades]
  - Fix approach: [how to address it]

## TODO/FIXME Inventory
- Total: [count]
- By area:
  - `[file]`: [count] — [summary of what's deferred]

## Complexity Hotspots
Files over 500 lines or with high churn:
- `[file]` ([N] lines) — [why it's large, what could be extracted]

## Fragile Areas
Code that breaks easily or is hard to modify safely:
- `[file/module]` — [why fragile, what to watch for]

## Missing Test Coverage
Source files without corresponding tests:
- `[source file]` → no test file found

## Dependency Concerns
- [package] — [issue: outdated, deprecated, security advisory, etc.]

## Security Surface
Areas that /tai-review should focus on:
- [area] in `[file]` — [what to check]

NOTE: This is NOT a security audit. It flags areas for deeper review.

Return only: "Concerns analysis complete. Wrote .tai/map/concerns.md ({N} lines)."
```

## Step 4: Collect results and summarize

After all 4 agents complete, read each output file and present a summary:

```bash
wc -l .tai/map/*.md
```

Display to the user:

```
## Codebase Map Complete

4 documents written to `.tai/map/`:

| Document | Lines | Key Findings |
|----------|-------|--------------|
| stack.md | {N} | {1-line summary} |
| architecture.md | {N} | {1-line summary} |
| conventions.md | {N} | {1-line summary} |
| concerns.md | {N} | {1-line summary} |

These documents are now available as context for other skills
(/plan-eng, /plan-ceo, /review, etc.).

To refresh: run `/tai-map` again.
```

## Step 5: Log completion

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
mkdir -p ~/.tai-skills/projects/$_SLUG
echo "{\"skill\":\"map\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"complete\",\"documents\":4}" >> ~/.tai-skills/projects/$_SLUG/map-log.jsonl
```

Report status: **DONE** — 4 codebase mapping documents written to `.tai/map/`.

## Sequential Fallback

If the Agent tool is unavailable or agents fail, run the analysis sequentially
in the main context. Follow the same exploration steps and write the same 4 files.
This uses more context but produces the same output.

If some agents succeed and others fail, run only the failed agents sequentially
in the main context before proceeding to Step 4. Report status as
**DONE_WITH_CONCERNS** noting which agents required fallback.
