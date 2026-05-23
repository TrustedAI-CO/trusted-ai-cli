# Document-Driven Development

## The Problem

When AI agents implement complex features, humans lose visibility. The plan is too
high-level. The code diff is too low-level. There is no middle layer where a human
can see what happened, why, and whether it's correct — without reading code.

## The Solution

A structured `docs/` tree committed to git. Every project artifact lives in `docs/`.
The agent writes code AND maintains documentation that proves the code matches intent.
The human reviews documentation, not code.

```
Human controls                    Agent controls
──────────────                    ──────────────
Intent (WHY)                      Code
Scope decisions                   Tests
Trade-off calls                   Traceability (REQ → test → code)
Approve/override REVIEW.md        Spec drafts
                                  Design docs
                                  Execution plans
```

The agent can write at any level — intent, specs, code. But humans intervene at
two triggers: **trade-offs** (no clear winner) and **decisions with consequences**
(scope, architecture, risk acceptance). Everything else: agent proposes, agent
executes, agent validates. Human reviews async via `docs/`.

## Directory Structure

```
project-root/
├── README.md                      ← only root-level docs allowed
├── CLAUDE.md                      ← only root-level docs allowed
├── docs/
│   ├── REVIEW.md                  ← human attention log
│   ├── intent.md                  ← WHY we're building this
│   ├── decisions/                 ← trade-off records
│   │   └── NNN-slug.md
│   ├── design/
│   │   ├── system.md              ← architecture, boundaries, data flow
│   │   └── visual.md              ← UI/UX design system
│   ├── specs/                     ← module behavior contracts
│   │   └── {module}.md            ← with REQ IDs
│   ├── trace/                     ← traceability (agent-maintained)
│   │   ├── matrix.md              ← REQ → test → code
│   │   ├── code-map.md            ← codebase architecture
│   │   ├── conventions.md         ← coding standards
│   │   ├── concerns.md            ← tech debt, risks
│   │   ├── testing.md             ← test framework, patterns
│   │   └── stack.md               ← technology stack
│   ├── plan/
│   │   ├── tasks.md               ← implementation tasks + waves
│   │   ├── milestones.md          ← exit criteria
│   │   └── todos.md               ← deferred work
│   ├── contributing.md            ← contributor guide
│   └── changelog.md               ← version history
└── .tai/                          ← gitignored, ephemeral
    ├── state/                     ← execute-state.json, review JSONL
    ├── cache/
    └── logs/
```

## Three Laws

### 1. No Orphans

Every document links to at least one other document. Every link resolves.
Parent-child links are bidirectional. The doc tree is a connected graph,
not a pile of files.

### 2. Every Layer Stays at Its Abstraction

| Layer | Answers | Contains | Does NOT contain |
|-------|---------|----------|-----------------|
| intent | WHY | User-facing promises, product goals | Architecture, modules, code |
| decisions | WHY this choice | Context, options, rationale | Implementation detail |
| design | HOW components interact | Boundaries, data flow, diagrams | File paths, line numbers |
| specs | WHAT each module does | Behavior contracts, REQ IDs | Code snippets, test details |
| trace | WHERE it lives | REQ → test → code mapping | Business logic, requirements |
| plan | WHEN and in what order | Tasks, waves, exit criteria | Architecture decisions |

If a sentence belongs at a different layer, move it there.

### 3. Traceability Closes the Loop

Every requirement (REQ-ID) in a spec must trace to:
- A test that proves the behavior
- Code that implements it

```
specs/auth.md           ← "REQ-AUTH-001: Users register with email"
  ↕ linked via
trace/matrix.md         ← "REQ-AUTH-001 | specs/auth.md | app/auth/register.py | tests/test_register.py | COVERED"
```

If a REQ has no test, it's PARTIAL. If it has no code, it's NOT_STARTED.
The human checks coverage percentage, never reads code.

## Root File Policy

Only two files at project root: `README.md` and `CLAUDE.md`.

Everything else lives in `docs/`:
- ~~DESIGN.md~~ → `docs/design/visual.md`
- ~~ARCHITECTURE.md~~ → `docs/trace/code-map.md`
- ~~PLAN.md~~ → `docs/plan/tasks.md`
- ~~TODOS.md~~ → `docs/plan/todos.md`
- ~~TESTING.md~~ → `docs/trace/testing.md`
- ~~CONTRIBUTING.md~~ → `docs/contributing.md`
- ~~CHANGELOG.md~~ → `docs/changelog.md`

No fallbacks. No "check root first." The `docs/` path is the only path.

## REVIEW.md — The Human Attention Log

When an agent makes a decision not covered by existing docs, it appends to
`docs/REVIEW.md`. This is the one place humans must look.

Agent appends when:
- Choosing between options with real trade-offs
- Deviating from the plan (Tier 4 decisions)
- Making architecture choices not in design docs
- Picking a library, format, or strategy not specified in specs

Agent does NOT append for:
- Trivial implementation choices (variable names, loop structure)
- Decisions already covered by existing specs
- Bug fixes within scope

Human resolves by marking items APPROVED or OVERRIDDEN. Agent propagates
the decision into the relevant spec or design doc.

## Frontmatter Contract

Every `docs/*.md` file has YAML frontmatter:

```yaml
---
id: unique-id
type: intent | decision | design | spec | trace | plan | review
parent: parent-doc-id | null
children: [child-id-1, child-id-2]
related: [related-id-1]
---
```

This is not optional decoration. It's the structure that makes validation,
navigation, and orphan detection work. A doc without frontmatter is broken.

## Committed vs Gitignored

**`docs/`** — committed. Shows in PRs, blame, diffs. Human-reviewable.

**`.tai/`** — gitignored. Agent workspace. Execute state, review JSONL,
cache, logs. Survives across sessions but not part of the project record.

Rule: if a human should see it → `docs/`. If agent-only ephemeral → `.tai/`.

## How Skills Map to Docs

| Skill | Reads | Writes |
|-------|-------|--------|
| /plan-ceo | — | `docs/intent.md`, `docs/decisions/` |
| /plan-eng | intent, design | `docs/design/system.md`, `docs/specs/`, `docs/plan/tasks.md` |
| /plan-design | design/visual | `docs/design/visual.md` |
| /design-consultation | — | `docs/design/visual.md` |
| /execute | plan/tasks, specs | `docs/trace/matrix.md`, `docs/REVIEW.md` |
| /map | — | `docs/trace/` (code-map, conventions, concerns, stack) |
| /next | plan, specs, trace, REVIEW | — (read-only dashboard) |
| /review | specs, trace/matrix | — (check coverage, flag scope creep) |
| /ship | REVIEW, trace/matrix | — (pre-merge gates) |
| /document-release | all docs/ | updates stale docs |

## Validation

Run after every doc change:
1. Every doc has frontmatter with all required fields
2. Every `id` is unique
3. Every `parent`/`children`/`related` ID resolves to an existing doc
4. Parent-child links are bidirectional
5. No orphan docs (except REVIEW.md)
6. Every REQ in specs has a trace entry (warning, not error)
7. Each doc stays at its abstraction layer (advisory)
