# Test Prompt: Document-Driven Development Framework

Copy the section below and give it to another agent session.

---

## Task: Verify Document-Driven Development Integration

We've migrated all TAI skills to use a structured `docs/` tree instead of
root-level markdown files. Your job is to verify the migration is complete
and internally consistent.

### Background

Read these files first:
- `/Users/dizzyvn/workspace/trusted-ai/internal/cli/.claude/skills/tai/docs-philosophy.md` — the design philosophy
- `/Users/dizzyvn/workspace/trusted-ai/internal/cli/.claude/skills/tai/docs-preamble.md` — shared init and formats
- `/Users/dizzyvn/workspace/trusted-ai/internal/cli/.claude/skills/tai/docs-validate.md` — validation rules

### Checks to Run

#### 1. No Root-Level Doc References (CRITICAL)

Grep all `SKILL.md` files in `.claude/skills/tai/` for references to root-level
files that should now be in `docs/`. These are violations:

```
ARCHITECTURE.md → should be docs/architecture.md (§4 holds the container→dir map)
TODOS.md → should be docs/plan/backlog.md
DESIGN.md → should be docs/design/visual.md
TESTING.md → should be CLAUDE.md (testing conventions live here)
CONTRIBUTING.md → should be docs/contributing.md
CHANGELOG.md → should be docs/changelog.md
PLAN.md → should be docs/plan/tasks.md
```

Note: the old `docs/trace/` folder is gone. Code map → `docs/architecture.md` §4;
testing → `CLAUDE.md`; conventions → `CLAUDE.md`; stack → `README.md`;
conformance matrix → `docs/matrix.md`. Any reference to `docs/trace/*` is a violation.

**Allowed exceptions:**
- References inside `docs-preamble.md` (it defines the framework)
- References inside `docs-philosophy.md` (it explains the migration)
- References inside `docs-test-prompt.md` (this file)
- A single informational note in `plan-eng/SKILL.md` about keeping legacy PLAN.md
- References to `README.md` and `CLAUDE.md` at root (these stay)
- References to `VERSION` file (stays at root)
- References to `.claude/skills/tai/review/TODOS-format.md` (skill reference, not project file)

Everything else is a bug. Report each violation with file path and line number.

#### 2. State Directory Migration (CRITICAL)

Grep all `SKILL.md` files for `~/.tai-skills/` or `$HOME/.tai-skills/`. These should
all be migrated to `.tai/state/`, `.tai/logs/`, or `.tai/cache/`.

**Allowed exception:** `docs-preamble.md` state migration section (shows old path for context).

#### 3. Output Path Consistency (HIGH)

For each skill that WRITES files, verify it writes to the correct `docs/` path:

| Skill | Should write to |
|-------|----------------|
| map | `docs/architecture.md` (§4 container→dir map); conventions/testing → `CLAUDE.md`, stack → `README.md` |
| plan-ceo / plan-product | `docs/prd.md` (draft for human), `docs/decisions/` |
| plan-eng | `docs/architecture.md`, `docs/specs/*.md`, `docs/plan/tasks.md` |
| plan-design | reads/modifies `docs/design/visual.md` |
| design-consultation | `docs/design/visual.md` |
| execute | `docs/matrix.md`, `docs/REVIEW.md` |
| ship | `docs/plan/backlog.md`, `docs/changelog.md` |
| document-release | updates files in `docs/` |

#### 4. Frontmatter in Agent Prompts (MEDIUM)

Check that skills which generate docs include frontmatter instructions.
These skills should tell their agents/subagents to add YAML frontmatter:

- map (4 agent prompts should include frontmatter blocks)
- plan-ceo / plan-product (prd.md draft and decision docs)
- plan-eng (architecture.md, specs, tasks.md)
- design-consultation (visual.md)

#### 4b. Framework Guardrails + Doc-First Gate (CRITICAL)

- Every pipeline skill (`plan-*`, `execute`, `review`, `ship`, `design-consultation`)
  has a "Framework Guardrails (read first)" block referencing `docs-philosophy.md`.
  `docs-update` also carries the guardrails block, though it is on-demand, not a pipeline
  step. `docs-init` defines the framework, so it is exempt.
- `docs-update` must NEVER write to `docs/specs/`, `docs/prd.md`, or `docs/decisions/`
  (gate G2). Grep its body for edits to those paths — any is a violation.
- `ship` and `review` run the doc-first gate G1: code under a spec's `code:` path may not
  merge while that spec is not `status: approved`. Confirm both reference the gate.
- `docs/prd.md` is HUMAN-owned: `plan-ceo`/`plan-product` must draft-and-present, never
  finalize or overwrite human content.

#### 5. REVIEW.md Integration (MEDIUM)

Check that these skills reference `docs/REVIEW.md`:
- execute — should append when Tier 4 deviations are resolved
- execute — subagent template should have REVIEW.md append section
- next — should show pending items from REVIEW.md
- ship — should check for PENDING items as pre-merge gate
- review — should note PENDING items count

#### 6. Traceability Matrix Integration (MEDIUM)

Check that these skills reference `docs/matrix.md`:
- execute — subagent template should update matrix after each task
- next — should show spec coverage from matrix
- review — should check matrix for scope creep
- ship — should show coverage percentage

#### 7. Cross-Skill Consistency (LOW)

Verify that skills reading from docs/ match what other skills write:
- plan-eng writes `docs/plan/tasks.md` → execute reads `docs/plan/tasks.md`
- plan-eng writes `docs/specs/*.md` → review reads `docs/specs/*.md`
- map writes `docs/architecture.md` (§4 dir map) → document-release reads `docs/architecture.md`
- design-consultation writes `docs/design/visual.md` → plan-design reads `docs/design/visual.md`

### Output Format

```
## Verification Results

### 1. Root-Level Doc References
- PASS / FAIL
- [list violations if any]

### 2. State Directory Migration
- PASS / FAIL
- [list violations if any]

### 3. Output Path Consistency
- [per-skill status]

### 4. Frontmatter in Agent Prompts
- [per-skill status]

### 5. REVIEW.md Integration
- [per-skill status]

### 6. Traceability Matrix Integration
- [per-skill status]

### 7. Cross-Skill Consistency
- [per-skill status]

### Summary
- Critical issues: N
- High issues: N
- Medium issues: N
- Low issues: N
```
