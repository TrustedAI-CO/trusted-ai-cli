---
id: 0005-skill-pruning
type: decision
status: accepted
parent: architecture
children: []
related: [0003-review-loop-parallel, 0004-plan-talk-first]
supersedes: none
---

# 0005-skill-pruning: Apply the "great skills" rubric — dedupe + prune the tai skills

## Context
Source: "Building Great Agent Skills: The Missing Manual" (Matt, aihero.dev). Its rubric —
**trigger / structure / steering / pruning** — maps onto problems in our 22-skill set,
which has grown large this session with no pruning pass:
- `execute` 1271 lines, `ship` 1102, `plan-eng` 706, `review` 566.
- **11 skills each inline the SAME convention blocks** ("AskUserQuestion Format",
  "Completeness Principle — Boil the Lake", the numbered Framework-Guardrails rules) —
  ~40 duplicated lines per skill (~440 total). That is textbook **sediment**: copy-pasted
  reference that bloats every file and every standalone run's context.
- Large `SKILL.md` files mix **steps + reference** inline rather than hiding branch-only
  reference behind context pointers.

The talk's other principles we already satisfy (validated, no action): split skills so the
agent sees one step at a time (our plan→execute→review→ship + flow); clarify-then-write
(plan-product grill + ADR 0004 talk-then-write); human-in-loop gates; shared docs-*.md as
context pointers.

## Decision
Adopt the rubric as a maintenance standard and do a pruning pass:

1. **Extract the repeated convention blocks to ONE shared file behind a context pointer.**
   Create `docs-conventions.md` (sibling of `docs-philosophy.md`) holding the AskUserQuestion
   Format + Boil-the-Lake/Completeness baseline. Each skill replaces its inlined copy with a
   one-line pointer: *"Interaction + completeness conventions: see `docs-conventions.md`
   (already loaded in flow-mode)."* Single source of truth; ~440 lines of sediment removed.
2. **Deletion-test no-ops + de-sediment** the largest skills (`execute`, `ship`, `plan-eng`,
   `review`): for each paragraph, ask "if I delete this, does agent behavior change?" — if
   not, cut. Remove stale/irrelevant accreted material.
3. **Formalize leading words.** Keep our coined high-density phrases consistent across skills:
   `doc-first`, `one spec = one surface`, `blind reviewer`, `talk-then-write`, `boil the lake`,
   `vertical slice`. These are the steering levers; don't dilute them with paraphrases.
4. **Trigger note (no change now):** pipeline-internal skills (`execute`, `review`, `qa`,
   `ship`) are invoked BY flow, not usually model-chosen — candidates for user/flow-invoked
   only to cut model-description context load. Deferred: harness-specific; revisit separately.

Scope: a structure/pruning pass, NOT a behavior rewrite. The skills must do the same thing,
smaller. Verify by spot-checking that each skill still reads coherently with the shared
pointer.

## Consequences
- Smaller `SKILL.md` files: lower token cost on every run, easier to audit/maintain, one
  place to change a convention.
- A shared `docs-conventions.md` the skills depend on (like `docs-philosophy.md`); flow-mode
  already loads shared files once.
- Cost: a one-time restructure touching most skills; risk of an over-eager deletion removing
  a load-bearing line — mitigated by the deletion-test discipline + spot review.

## Alternatives considered
- Leave skills as-is — rejected: sediment compounds; token + maintenance cost grows.
- Per-skill full rewrite — rejected: too risky/large; a targeted dedupe + deletion-test pass
  gets most of the value.
