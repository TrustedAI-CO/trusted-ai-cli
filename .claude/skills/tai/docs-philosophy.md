# Document-Driven Framework

**This file is the single source of truth for the framework.** Every pipeline skill
links here instead of restating the layer model. If a skill's behavior contradicts
this file, this file wins.

## The Problem

When AI agents implement complex features, humans lose visibility. The plan is too
high-level. The code diff is too low-level. There is no middle layer where a human
can see what happened, why, and whether it's correct — without reading code.

## The Solution

A structured `docs/` tree committed to git, organized as ordered layers. The agent
writes code AND maintains the documentation that proves the code matches an approved
contract. The human reviews documentation, not code — and owns the gates.

All docs are **Markdown only** — YAML frontmatter for metadata. No HTML, no `_assets/`.

## The Layers (L0 → L3)

| Layer | File(s) | Answers | Owner | Gate |
|-------|---------|---------|-------|------|
| **L0** | `docs/prd.md` | WHY — product intent / PRD | **Human** | Agents draft/quote, never finalize. Human signs off wording. |
| **L1** | `docs/decisions/` + `docs/architecture.md` | WHY this shape — ADRs + C4 | Human-accepted | Agent may *draft* an ADR; a **human** flips `status: accepted`. |
| **L2** | `docs/specs/{area}-{name}.md` | WHAT each surface does — behavioral contract | Agent-drafted | A **human** sets `status: approved` before any code under the spec's `code:` path merges. |
| **L3** | code + tests | HOW — implementation | Agent | Tests reference the spec's Behavior row IDs. |

**Layer model:** L0 `prd.md` (human) → L1 `decisions/` + `architecture.md` → **L2 `specs/`** → L3 code.

## Core Invariant — Doc-First Order

> **Change the spec before the code, in the same PR.**
> **No code under a spec's `code:` path may merge until that spec is `status: approved`.**

`docs/specs/` is the L2 layer and the contract code is verified against — never the
reverse. **Never edit a spec, PRD, or ADR to match code that has already been written.**
That inverts doc-first order: it rewrites the contract to fit the implementation instead
of the implementation fitting the contract, silently destroying the source of truth.

If a spec / PRD / ADR is out of date versus shipped code: **DO NOT fix it.** Flag it as a
`[CRITICAL]` doc-first violation and let a human reconcile through the proper spec-first
flow.

## Spec Evolution — Changing a Shipped Surface

The status lifecycle is `draft → approved → implemented`, but it is **not terminal**. A
shipped surface evolves — `notes add` gains a `--tag` option, an endpoint adds a field.
That is a change to an existing spec, **not** a new spec (one spec = one surface, for the
life of the surface).

> **Editing the Interface or any Behavior row of an `implemented` spec RESETS it to
> `status: draft` and CLEARS `approved_at`.**

Then it re-enters the normal gate: append the new Behavior rows (new R-ids — never renumber
or reuse existing ones; old rows keep their history), a human re-approves (which re-stamps
`approved_at`), and only then may code under the spec merge.
This guarantees a behavior change to a shipped surface gets the **same human gate** as a
new one — without it, `implemented` would be a hole through which unreviewed contract
changes ship. Editing prose-only sections (Overview, Open questions) does not require a
reset; only Interface/Behavior/Invariants do.

## PR Discipline — Change Unit & Trace

Three rules make every change reviewable and traceable:

1. **Every change ships via a PR.** No direct pushes to the base branch. The PR is the
   review gate and the trace anchor. (Enforced by `/ship`.)
2. **A PR declares every spec it touches; all must be `status: approved`.** There is NO
   hard "one spec per PR" law — coupled specs (a new interface and its caller) ship
   together rather than forcing merge ordering. But aim for one spec per PR (smallest
   reviewable contract change), and the PR body MUST list the full declared set. A
   touched-but-undeclared spec is a trace gap → ship FAILs.
3. **`changelog.md` is the trace index.** Each bullet that ships code under a spec names
   the governing spec id(s) and the PR number: `- {change} — SPEC-{id} (#NNN)`. This one
   anchor chains to the spec's git history (`git log docs/specs/{id}.md`), the matrix
   (R-id → code → test), and the PR diff. Full bidirectional trace, no extra files.

## Source vs Derived Layers

| | Layers | Who edits | When |
|--|--------|-----------|------|
| **Source** (authored, gated) | `docs/prd.md`, `docs/decisions/`, `docs/specs/` | Human-gated | Before code, via plan skills + human approval |
| **Derived** (living, agent-maintained) | `README.md`, `docs/architecture.md`, `docs/matrix.md`, `docs/changelog.md`, `docs/contributing.md`, `CLAUDE.md` | Agent | Any time, incl. post-ship via `docs-update` |

`docs-update` is **post-ship** and touches **derived docs only**. It must NEVER edit a
source layer (`specs/`, `prd.md`, `decisions/`).

**Derived docs carry a trust marker so a human reading one knows not to trust it as
source.** Every derived doc has `derived: true` in frontmatter AND a one-line banner
right under the frontmatter:

```
> ⚠️ Derived doc — generated/maintained post-ship by an agent; may lag the code. Source
> of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.
```

Without this, a human opening `architecture.md` or `matrix.md` cannot tell — while
reading — that it is derived and possibly stale (the distinction otherwise lives only in
this philosophy file). Source docs carry `status:`; derived docs carry `derived: true`.

## Directory Structure

```
project-root/
├── README.md                  ← repo entry point (derived)
├── CLAUDE.md                  ← AI agent rules (derived)
├── docs/
│   ├── prd.md                 ← L0 PRD / product intent — HUMAN-owned (source)
│   ├── architecture.md        ← L1 C4 Context+Container + §4 container→dir map (derived)
│   ├── matrix.md              ← derived conformance: spec R-id → code → test → status
│   ├── REVIEW.md              ← human attention log (decisions needing review)
│   ├── decisions/
│   │   └── NNNN-slug.md        ← L1 one ADR per decision (agent drafts, human accepts)
│   ├── specs/
│   │   └── {area}-{name}.md    ← L2 behavioral contract — one spec per public surface
│   ├── design/
│   │   └── visual.md           ← UI/UX design system (owned by /design-consultation)
│   ├── plan/
│   │   ├── tasks.md  backlog.md
│   ├── contributing.md
│   └── changelog.md
└── .tai/                       ← gitignored, ephemeral agent workspace
    ├── state/  cache/  logs/
```

> **Trimmed by design.** Keep docs few or they rot. Code-derivable prose is NOT
> maintained as docs: the codebase shape lives in `architecture.md` (§4 dir map),
> conventions + testing live in `CLAUDE.md`, the stack lives in `README.md`, deferred
> work + tech debt live in `plan/backlog.md`. Per-concept walkthroughs are **generated
> on demand** (e.g. a tutorial run), never kept current as files. The only derived
> "map" docs are `architecture.md` (authored, coarse, stable) and `matrix.md`
> (generated, disposable) — regenerate, don't trust as source.

## Spec Layer Detail (L2)

One spec = one public surface (an exported API / CLI command / module boundary). Never
one per internal function; never one giant spec for many surfaces.

Each spec MUST carry:
- **Frontmatter:** `id: SPEC-{area}-{name}`, `status:` (`draft` → `approved` →
  `implemented`), `implements:` (the PRD/ADR ids), and **`code:` / `tests:`** paths telling
  `/tai-execute` exactly where the implementation and its tests live.
  `code:` must sit under a container in `architecture.md` §4.
- **Behavior:** a table of observable rules, each with a **stable R-id** (`R1`, `R2`, …),
  Given / When / Then columns.
- **Invariants:** always-true properties. Priority order when reviewing: **Invariants >
  Interface > Behavior**.

**Traceability:** every Behavior row ID (`R1…RN`) must be referenced by a passing test —
either a `test_R3_*` function name or a `// covers: <SPEC-id> R3` tag (use the comment
syntax for the language). Each Invariant gets a property/assertion test.

## Where Notes Go — Capture Reflex

Mid-flow, ideas and deferrals surface (agent proposes feature B while you build A; you
decline or postpone). Each kind has exactly one home — don't lose it, don't act on it:

| Note kind | Home |
|-----------|------|
| Deferred / declined / someday idea | **`docs/plan/backlog.md`** |
| Explicit non-goal (product scope) | `docs/prd.md` → Out of scope |
| Surface-local open question | the spec's `## Open questions` |
| Decision the agent made needing human review | `docs/REVIEW.md` (→ ADR if load-bearing) |

**Capture reflex (all agents):** when the user declines or defers a suggestion, append
**one line** to `docs/plan/backlog.md` before continuing — then move on. `backlog.md` has
two sections:

```markdown
## Active            # scheduled deferred — will do, just not this PR
- [ ] {task} — from {feature/spec}, deferred YYYY-MM-DD

## Backlog           # unscheduled — someday / maybe / declined ideas + tech debt
- {idea} — noted YYYY-MM-DD, from {feature}, why deferred: {reason}
```

## REVIEW.md — The Human Attention Log

When an agent makes a decision not covered by existing docs, or hits a doc-first conflict,
it appends to `docs/REVIEW.md`. This is the one place humans must look. Human resolves by
marking items APPROVED or OVERRIDDEN; the agent then propagates the decision into the
relevant source doc through the proper flow.

## Frontmatter Contract

Every `docs/*.md` file has YAML frontmatter:

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

A doc without frontmatter is broken. Specs and ADRs additionally carry `status:`; it is
the gate humans flip.

## Committed vs Gitignored

- **`docs/`** — committed. Shows in PRs, blame, diffs. Human-reviewable.
- **`.tai/`** — gitignored. Agent workspace: execute state, review JSONL, cache, logs.

## How Skills Map to Layers

| Skill | Reads | Writes | Layer role |
|-------|-------|--------|-----------|
| `/plan-product`, `/plan-ceo` | — | `docs/prd.md` (draft for human), `docs/decisions/` | L0 — assist human, never finalize |
| `/plan-eng` | prd, architecture | `docs/architecture.md`, `docs/specs/` (draft), `docs/plan/tasks.md` | L1+L2 — author spec contracts |
| `/plan-design` | prd, design/visual | `docs/design/visual.md`, `docs/decisions/` (ADRs) | L1 — design ADRs |
| `/design-consultation` | — | `docs/design/visual.md` | design system |
| `/tai-execute` (auto solo/team) | plan/tasks, **approved** specs | code+tests, `docs/matrix.md`, `docs/REVIEW.md` | L3 — implement against approved L2 |
| `/review` | specs, matrix | — (conformance check) | L2 gate check |
| `/ship` | REVIEW, matrix | — (pre-merge gates) | enforces doc-first gate |
| `/docs-update` | all derived docs | derived docs only | post-ship — never touches source |
| `/docs-init` | — | scaffolds the whole tree | bootstrap |

See `docs-preamble.md` for init constants, frontmatter rules, and the spec/matrix file
formats. See `docs-validate.md` for the validation + doc-first conformance gate.
