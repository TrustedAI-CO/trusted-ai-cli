---
id: 0004-plan-talk-first
type: decision
status: accepted
parent: architecture
children: []
related: []
supersedes: none
---

# 0004-plan-talk-first: Plan skills present the plan in conversation before writing the file

## Context
The doc-authoring plan skills (`/plan-eng`, `/plan-product`, `/plan-ceo`, `/plan-design`)
currently **draft the artifact to a file first**, then ask for approval at the end
(`plan-eng` line 425: "present the drafted spec and ask whether to mark approved"). In a
TUI a silent file write is invisible — the human can't review the plan's *shape* before it
lands on disk, and (in flow) the first real conversational checkpoint is GATE C, after the
file already exists. Observed: "it writes the plan to file directly instead of talking to
me." This is write-then-ask; we want talk-then-write.

## Decision
Plan skills must **present the plan in the conversation, then write the file** — not the
reverse. Before creating/updating a `docs/` artifact (spec, prd, ADR, design doc), the
skill:
1. Presents the plan's **shape in chat, VISUALLY** — lead with an **ASCII diagram** (and
   compact tables) over prose: e.g. the surface/component layout, the data/flow, the spec's
   Behavior rows as a table, the `code:`/`tests:` → architecture mapping. Goal: the human
   greps the plan's structure at a glance in a TUI, not by reading paragraphs.
2. **Confirms/steers via AskUserQuestion** (proceed as-is / adjust / cancel), per the
   existing batching rules.
3. Writes the file **only after** the human confirms the direction.

Visual-first is the point: an ASCII diagram of the structure/flow + a Behavior-row table is
the primary artifact of the "talk" step; prose is supporting, not leading.

The downstream human gate is unchanged: specs still land at `status: draft` and pass
GATE C (approve) before code. This adds an *upstream* conversational checkpoint so the
plan is reviewed before it's committed to a file.

## Consequences
- Easier: TUI users see + confirm the plan before any file write; fewer "where did this
  file come from" surprises; steering happens before the artifact is shaped.
- Cost: one more interaction per plan artifact (the upfront present+confirm). Acceptable —
  it's the point. `quick`/abbreviated modes may present a one-shot outline instead of a
  per-section walk.
- Applies to all doc-authoring plan skills: `plan-eng`, `plan-product`, `plan-ceo`,
  `plan-design`.

## Alternatives considered
- Write file + print its content inline, then ask — rejected: the file still lands before
  confirmation; talk-first is cleaner.
- One upfront outline only (no per-section talk) — folded in as the `quick`-mode behavior.
