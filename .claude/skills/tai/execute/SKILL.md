---
name: execute
version: 1.0.0
description: |
  [TAI] Autonomous plan executor with auto-selected strategy. Reads a reviewed
  engineering plan (docs/plan/tasks.md) and AUTO-PICKS how to implement it:
  if the plan has ≥2 independent sub-phases it launches a parallel TEAM of
  engineers (each in an isolated git worktree, coordinated via TeamCreate with
  review ↔ fix and QA ↔ fix loops before merge); otherwise it runs SOLO in a
  single context, breaking the plan into tasks and dispatching each to a
  fresh-context subagent with wave execution, 4-tier deviation rules,
  self-verification, and resume from interruption. Use after /tai-plan-eng
  produces a plan, or when the user says "execute the plan", "implement this",
  "launch a team", "parallel implement", or "start phase N".
  Invoke with: /tai-execute [path-to-plan]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - TeamCreate
  - TaskCreate
  - TaskList
  - TaskGet
  - TaskUpdate
  - SendMessage
  - AskUserQuestion
---

## Framework Guardrails (read first)

This skill is part of the Document-Driven pipeline. Read **`docs-philosophy.md`** (the
single source of truth) before acting. Non-negotiable:

> **Flow mode:** if `.tai/state/flow-session` exists, the orchestrator already loaded
> `docs-philosophy.md` and established the shared interaction conventions (AskUserQuestion
> format, Boil-the-Lake completeness) — SKIP re-reading the philosophy file and skip
> restating those blocks; assume them in effect. The numbered rules below still apply.

1. **`docs/prd.md` is HUMAN-owned** — draft/quote, never finalize.
2. **Doc-first order** — spec before code, same PR; no code merges under a spec's `code:`
   path until that spec is `status: approved`.
3. **Never edit `docs/specs/`, `docs/prd.md`, or `docs/decisions/` to match shipped code** —
   flag staleness as `[CRITICAL]`; a human reconciles.
4. **Tests reference Behavior row IDs** (`test_R3_*` / `// covers: SPEC-... R3`).

## Conventions

Shared conventions (AskUserQuestion Format, Boil-the-Lake, tai Field Report) live in
`docs-conventions.md` (ADR 0005). `/tai-flow` loads it once per run; in a standalone run,
read it once.

## Language

Respond in the same language the user is using. If the user writes in Japanese,
respond entirely in Japanese. If Vietnamese, respond entirely in Vietnamese.
Keep these in English regardless of language:
- Status labels: DONE, FAILED, SKIPPED_DEPENDENCY, CHECKPOINT_NEEDED, ALL_SUCCESS, PARTIAL_SUCCESS, ALL_FAILED
- Tier labels: Tier 1, Tier 2, Tier 3, Tier 4
- Log/machine-readable output (.jsonl entries, bash commands)
- Technical terms: SQL, CSRF, API, LLM, XSS, etc.
- Branch names and status labels

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $_REPO_ROOT"
_DOCS_DIR="$_REPO_ROOT/docs"
_STATE_DIR="$_REPO_ROOT/.tai/state"
echo "STATE_DIR: $_STATE_DIR"
mkdir -p "$_STATE_DIR"
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
echo "SLUG: $_SLUG"
```

## Auto-Branch (if on main)

If the current branch is `main` or the repo's default branch, automatically
create a feature branch before executing:

```bash
_DEFAULT=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
if [ "$_BRANCH" = "$_DEFAULT" ]; then
  _NEW_BRANCH="feat/execute-$(date +%Y%m%d-%H%M%S)"
  git checkout -b "$_NEW_BRANCH"
  _BRANCH="$_NEW_BRANCH"
  _BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
  echo "Created branch: $_NEW_BRANCH"
fi
```

This protects main from half-done work. After execution, the user can `/ship`
to merge the branch or continue working on it.

---

## Strategy Selection (auto-pick)

You do NOT ask the user to choose between solo and team. Read the plan, count the
independent sub-phases, and pick automatically.

### Step S0: Read the plan and count independent sub-phases

1. Locate the plan file:
   - If the user provided a path argument, use that file.
   - Otherwise auto-discover `$_DOCS_DIR/plan/tasks.md`.
   - If no plan is found, stop: **"No plan found for branch {branch}. Run /tai-plan-eng
     first, or provide a path: /tai-execute path/to/plan.md"**
2. Read the plan. Identify the target phase (the next incomplete phase, or the
   phase the user named — "start phase 2", "team up on phase X").
3. Count the **independent sub-phases** in the target phase. A sub-phase is
   independent of another when they do NOT share database models, migrations,
   or target files, and neither requires the other's API contract first. Use the
   plan's **Module Ownership Map** (if present) and the sub-phase `depends_on`
   relationships to judge independence.

### Step S1: Pick the strategy

| Condition | Strategy |
|-----------|----------|
| The target phase has **≥2 independent sub-phases** that can run in parallel | **Team** (parallel) — go to `## Strategy: Team` |
| Otherwise (single sub-phase, or all sub-phases are serially dependent, or the plan is a flat task list with no parallelizable sub-phases) | **Solo** (single-context) — go to `## Strategy: Solo` |

Announce the choice in one line before proceeding, e.g.
"Plan has 3 independent sub-phases → using the parallel team strategy." or
"Plan has no parallelizable sub-phases → using the solo single-context strategy."

The user may override by saying "solo" / "single" or "team" / "parallel"
explicitly — honor an explicit override.

---

## Strategy: Solo

You are the **orchestrator**. Your job is thin: parse the plan, group tasks into waves,
dispatch each task to a fresh subagent, collect results, and write the execution summary.
You do NOT implement code yourself. You delegate everything.

```
/tai-plan-eng ──► [plan file] ──► /tai-execute (solo) ──► [commits + summary] ──► /tai-ship
```

### Step 0: Discover and Parse Plan

#### 0A. Find the plan file

You already located it in Strategy Selection (Step S0). Re-use that path.

```bash
if [ -f "$_DOCS_DIR/plan/tasks.md" ]; then
  echo "PLAN_SOURCE: $_DOCS_DIR/plan/tasks.md"
fi
```

#### 0B. Parse ## Implementation Tasks

Read the plan file. Find the `## Implementation Tasks` section. Extract each task:

**Required fields per task:**
- **name** — from the `### Task N: {name}` header
- **files** — list of files with (create) or (modify) annotation
- **depends_on** — task references or "none"
- **acceptance** — criteria for completion

**Optional fields:**
- **test_command** — specific test command (default: auto-discovered)

**Validation checks:**
1. At least 1 task exists → otherwise stop with "Plan has no Implementation Tasks section"
2. All tasks have name, files, depends_on, acceptance → otherwise stop listing missing fields
3. No circular dependencies → otherwise stop showing the cycle
4. All depends_on references point to existing tasks → otherwise stop showing orphan

If the plan file does NOT have a `## Implementation Tasks` section but has other
structured content (architecture notes, requirements), ask the user:
"This plan doesn't have an ## Implementation Tasks section. Would you like me to
generate tasks from this plan, or should you re-run /tai-plan-eng?"

#### 0C. Build Dependency DAG and Group Waves

Topological sort on depends_on:
- **Wave 1:** All tasks with `depends_on: none`
- **Wave 2:** Tasks whose dependencies are all in Wave 1
- **Wave N:** Tasks whose dependencies are all in Waves 1..(N-1)

**Parallel safety check:** Before finalizing each wave, verify no two tasks in the
same wave share target files. If overlap detected, move the later task (by task number)
to the next wave. Log: "Task {X} moved to wave {N+1} due to file overlap with Task {Y} on {file}."

#### 0D. Check for Resume

```bash
cat "$_STATE_DIR/execute-state.json" 2>/dev/null || echo "NO_STATE"
```

If a state file exists AND matches the current branch AND the plan path:
- Show completed tasks, failed tasks, and remaining tasks
- Ask: "Previous execution found. Resume from where it left off?"
  - A) Resume (skip completed, re-run FAILED + SKIPPED_DEPENDENCY)
  - B) Start fresh (ignore previous state)

If the branch has diverged (new commits since last execution):
- Warn: "Branch has {N} new commits since last execution. Resume may cause conflicts."
- Still allow resume if user chooses

#### 0E. Show Execution Plan

Before starting, display the plan:

```
╔══════════════════════════════════════════════════════╗
║              /tai-execute (solo) — Execution Plan     ║
╠══════════════════════════════════════════════════════╣
║  Plan: {plan file path}                              ║
║  Branch: {branch}                                    ║
║  Tasks: {N} total across {M} waves                   ║
╠══════════════════════════════════════════════════════╣
║  Wave 1: Task 1 (Create user model)                  ║
║          Task 3 (Add user config)        [parallel]  ║
║  Wave 2: Task 2 (Add user API)           [depends: 1]║
╠══════════════════════════════════════════════════════╣
║  Mode: interactive (use --auto for autonomous)       ║
╚══════════════════════════════════════════════════════╝
```

### Step 1: Execute Waves

For each wave, in order:

#### 1A. Route and Dispatch Subagents (parallel within wave)

Coding subagents are routed to the best backend based on **complexity first,
then file type**. The orchestrator (you) stays in Claude Code for coordination.

**Step 1: Complexity gate — decide Claude vs external CLI:**

| Complexity signal | Route to | Reason |
|-------------------|----------|--------|
| Task touches 5+ files across multiple modules | **Claude Code** (`Agent()`) | Needs deep cross-file reasoning |
| Task involves architectural wiring (new module, new API layer, DI setup) | **Claude Code** (`Agent()`) | Needs codebase-wide context |
| Task requires reading 3+ existing files to understand context before writing | **Claude Code** (`Agent()`) | External CLIs have limited context |
| Task has complex dependencies on prior tasks (shared types, interfaces) | **Claude Code** (`Agent()`) | Needs access to full conversation context |
| Task is a refactor that changes signatures used by other modules | **Claude Code** (`Agent()`) | Blast radius requires careful reasoning |
| Task is straightforward CRUD, single-file, or well-scoped feature | **External CLI** (codex/gemini) | Fast, parallel, cost-effective |
| Task is adding tests for existing code | **External CLI** (codex/gemini) | Mechanical, well-scoped |
| Task is config, docs, or boilerplate | **External CLI** (codex/gemini) | Simple, no deep reasoning needed |

**Heuristic shortcut:** If the task's `files` list has ≤ 3 files AND `depends_on`
references ≤ 1 prior task AND the acceptance criteria don't mention cross-module
integration → route to external CLI. Otherwise → Claude Code.

**Step 2: For external CLI tasks, pick backend by file type:**

| Signal | Backend | Reason |
|--------|---------|--------|
| Task files are `.py`, `.go`, `.rs`, `.sql`, `Dockerfile`, `*.yaml`/`*.toml` config | **codex** | Strongest at backend/systems code |
| Task files are `.ts`, `.tsx`, `.jsx`, `.css`, `.scss`, `.html`, `.vue`, `.svelte` | **gemini** | Strongest at frontend/UI code |
| Task files are mixed backend + frontend | **codex** | Default tiebreaker |
| Task involves DB migrations, schema changes | **codex** | Better at SQL/ORM |
| Task involves test writing only | **codex** | Faster execution |
| Task involves docs, markdown, config only | **codex** | Faster execution |

**File-type routing algorithm (apply in order):**
1. Collect all file extensions from the task's `files` list
2. Classify each as `backend` or `frontend` using the table above
3. If majority frontend → `gemini`; otherwise → `codex`
4. If classification is ambiguous (50/50 split) → `codex` (default)

**Dispatch via `tai agent run`:**

Write the subagent prompt to a temp file, then dispatch:

```bash
# Write prompt to file (avoids shell escaping issues)
cat > "/tmp/tai-task-{task_id}-prompt.md" << 'PROMPTEOF'
{subagent_prompt_from_template_below}
PROMPTEOF

# Dispatch to routed backend (run in background via &)
tai --json agent run \
  --backend {codex_or_gemini} \
  --dir "{repo_root}" \
  --timeout 300 \
  "$(cat /tmp/tai-task-{task_id}-prompt.md)" \
  > "$_STATE_DIR/task-{task_id}-result.json" 2>&1 &
```

Launch all tasks in the wave as background processes, then wait:

```bash
wait  # blocks until all background jobs finish
```

**Fallback chain — if a task fails, retry with the other backend:**

After collecting results (Step 1B), for each task with `status: "error"`:
1. Check the result JSON: if `exit_code` is non-zero or output contains
   clear failure indicators (timeout, crash, empty output)
2. Re-dispatch to the **other backend** (codex→gemini or gemini→codex)
3. Mark the fallback attempt in the state file: `"fallback_backend": "{other}"`
4. If the fallback also fails → mark task as FAILED (no further retries)

Only retry once via fallback. The goal is resilience, not infinite loops.

Wait for all agents in the wave to complete before proceeding to the next wave.

#### 1B. Collect Results

After all background jobs finish, read both the agent result and the per-task summary:

```bash
# 1. Check agent-level result (did the CLI itself succeed?)
cat "$_STATE_DIR/task-{task_id}-result.json" 2>/dev/null

# 2. Check task-level summary (did the subagent complete its work?)
cat "$_STATE_DIR/task-{task_id}-summary.md" 2>/dev/null
```

**Result interpretation:**
- Agent result has `"status": "success"` AND summary has `status: done` → task complete
- Agent result has `"status": "success"` BUT summary has `status: failed` → subagent ran but task failed (code issue)
- Agent result has `"status": "error"` or `"status": "timeout"` → agent-level failure, trigger fallback
- No summary file exists → subagent crashed before writing summary, trigger fallback

For each task, update the execution state:
- If status is `done` → record commit hash, move to next
- If status is `failed` (code issue, not agent crash) → record error, check downstream tasks
- If agent-level failure → trigger fallback chain (re-dispatch to other backend)
- If status is `checkpoint_needed` → handle checkpoint (see Step 2)

#### 1C. Update State File

After each wave, write the merged state to `execute-state.json`:

Write the state as JSON with this schema:

```json
{
  "plan_path": "{plan_path}",
  "branch": "{branch}",
  "started_at": "{iso_datetime}",
  "updated_at": "{iso_datetime}",
  "status": "in_progress",
  "waves": [
    {
      "wave_number": 1,
      "status": "completed",
      "tasks": [
        {
          "id": "task-1",
          "name": "Create user model",
          "status": "done",
          "commit": "abc1234",
          "files_changed": 3,
          "deviations": 0,
          "error": null
        }
      ]
    }
  ]
}
```

Task status values: `done`, `failed`, `skipped_dependency`, `checkpoint_needed`, `in_progress`, `pending`.
Wave status values: `completed`, `in_progress`, `pending`.

#### 1D. Wave Failure Propagation

After collecting wave results:
1. For each FAILED task: find all tasks in later waves that depend on it (directly or transitively)
2. Mark those downstream tasks as `skipped_dependency` with `blocked_by: {failed_task_id}`
3. Continue to the next wave — run all non-skipped tasks

### Step 2: Handle Checkpoints

When a subagent returns with status `checkpoint_needed`, read its checkpoint file:

```bash
cat "$_STATE_DIR/task-{task_id}-checkpoint.md" 2>/dev/null
```

The checkpoint file contains:
- **type:** `decision` | `human-action`
- **description:** what the subagent encountered
- **options:** (for decision type) list of choices

**For `decision` checkpoints (Tier 4 deviation):**
Use AskUserQuestion to present the options. Then resume the subagent with the user's choice
by dispatching a new Agent with the decision included in the prompt context.

After the user resolves a Tier 4 decision, append it to `docs/REVIEW.md` so the human
has a record of architectural decisions made during execution. Use the REVIEW.md format
from `docs-preamble.md`.

**For `human-action` checkpoints:**
Tell the user what manual action is needed. Wait for them to confirm completion.
Then resume the subagent.

**Checkpoint concurrency:** Since subagents run in background and the orchestrator
only reads results after ALL tasks in a wave complete, checkpoints are naturally
batched. If multiple subagents in the same wave return `checkpoint_needed`:
1. Present each checkpoint sequentially via AskUserQuestion (one at a time)
2. After all checkpoints are resolved, dispatch new agents for the checkpoint tasks
   with the user's decisions included in their prompts
3. Wait for the resumed tasks to complete before moving to the next wave

### Step 3: Write Execution Summary

After all waves complete (or all remaining tasks are failed/skipped):

```bash
cat > "$_STATE_DIR/${_BRANCH_SAFE}-execution-summary.md" << 'SUMEOF'
# Execution Summary
Generated by /tai-execute (solo) on {date}
Branch: {branch}
Plan: {plan_path}

## Results
| Task | Status | Commit | Files Changed | Deviations |
|------|--------|--------|---------------|------------|
{rows}

## Overall
- Tasks completed: {done}/{total}
- Tasks failed: {failed}/{total}
- Tasks skipped: {skipped}/{total}
- Total commits: {commit_count}
- Total deviations: {deviation_count} ({auto_fixed} auto-fixed, {escalated} escalated)
- Status: {ALL_SUCCESS | PARTIAL_SUCCESS | ALL_FAILED}

{if failed tasks, list each with failure reason and user action needed}
SUMEOF
```

Update `execute-state.json` with final status.

Display the summary to the user. If ALL_SUCCESS: "All tasks complete. Run /tai-ship when ready."
If PARTIAL_SUCCESS: "Some tasks failed. Review the failures above. You can fix manually and /tai-ship, or re-run /tai-execute to retry failed tasks."

### Subagent Prompt Template (Solo)

When dispatching each subagent via the Agent tool, construct this prompt:

```
You are implementing a single task from an engineering plan. Work autonomously.

## Capture Reflex
When the user declines or defers a suggestion, append one line to `docs/plan/backlog.md`
before continuing — don't lose it, don't act on it.

## Your Task
Name: {task_name}
Files to modify/create: {file_list}
Acceptance criteria: {acceptance_criteria}
Test command: {test_command or "uv run pytest"}
Governing spec: {spec_path — the APPROVED docs/specs/*.md this task implements}

## Doc-First Execution (READ THIS FIRST)

This task implements an APPROVED behavioral spec. The spec is the ground truth;
your code is verified against it — never the other way around.

1. **Read the governing spec** at `{spec_path}` in full before writing any code.
   Confirm its frontmatter `status: approved`. If it is `draft` or missing, STOP —
   write a checkpoint file (Tier 4) flagging that the spec is not approved. Do not
   implement against an unapproved spec.
2. **Write code under the spec's `code:` path** (from its frontmatter) and tests
   under its `tests:` path. Stay within the spec's declared surface.
3. **Tests MUST reference the Behavior row IDs they cover.** Each row ID (R1…RN) in
   the spec's Behavior table must appear in the test that covers it — either as a
   `test_R3_*` function name or a `// covers: <SPEC-id> R3` tag (use the comment
   syntax for your language). Add a property/assertion test for each Invariant.
4. **NEVER edit the spec to match the code you wrote.** That inverts doc-first order.
   If the spec is wrong, insufficient, or contradicts a real constraint you hit
   during implementation, STOP and write a Tier 4 checkpoint flagging a spec update
   is needed. The spec must be revised and re-approved by a human before you continue.
   `docs/specs/` is off-limits to your edits, always.
5. The spec governs *behavior* (what, observable) — it is silent on security,
   performance, and maintainability. You still write safe, clean code: validate
   inputs at boundaries, no SQL string interpolation, no untrusted LLM output in
   SQL/HTML/shell, handle errors, keep functions small and immutable. Behavioral
   conformance is necessary, not sufficient.

## Context
Read these files first to understand the codebase:
{curated_file_list}

(The orchestrator builds this list as follows:
1. All files listed in the task's `files` field (target files to create/modify)
2. For each target file that exists, include its parent directory's __init__.py or index file
3. All `task-{id}-summary.md` files from previously completed tasks in earlier waves
4. The task's section from the original plan file (architecture notes, requirements)
Do NOT include the entire plan file — only the relevant task section.)

## Implementation Protocol

1. **Read** the governing spec (see Doc-First Execution above), then the target files
2. **Write** the implementation under the spec's `code:` path, plus tests under its
   `tests:` path that reference the Behavior row IDs (`test_R3_*` or `// covers: <SPEC-id> R3`)
3. **Run tests** using: {test_command}
4. **Fix** any test failures (see Deviation Rules below)
5. **Commit** with message: "feat({scope}): {task_name}"
6. **Self-verify** (see Verification Checklist below)
7. **Maintain derived docs live** (see Derived-Doc Maintenance below)
8. **Write summary** to {summary_file_path}

## Deviation Rules

When you encounter issues during implementation:

| Tier | What happened | What to do | Limit |
|------|--------------|------------|-------|
| 1: Bug | Tests fail, runtime error | Fix it inline | 3 attempts per issue |
| 2: Missing | Linter flags missing validation | Add it | 3 attempts per issue |
| 3: Blocking | Import error, type mismatch within local code | Fix it | 3 attempts per issue |
| 4: Architectural | Need new package, new DB table, schema change | STOP — write checkpoint file | N/A |
| 4: Spec conflict | Spec is wrong, insufficient, unapproved, or contradicts a real constraint | STOP — write checkpoint file; NEVER edit the spec to match code | N/A |

**Tier 3 vs Tier 4 boundary:** If fixing the issue requires modifying a file OUTSIDE
your task's declared `files` list, or requires adding a new dependency to a lockfile
or package manifest (pyproject.toml, package.json, go.mod), treat it as **Tier 4**.
If the fix is contained within the task's declared files, it's **Tier 3**.

**Scope boundary:** Only fix issues CAUSED BY your changes. Do not refactor unrelated code.
**Attempt counting:** Each individual issue gets up to 3 fix attempts (1 original + 2 retries).
If a single issue exhausts 3 attempts, mark the task as FAILED. A task may encounter
multiple issues — each tracked independently. Maximum 9 total fix attempts per task
across all issues (3 issues x 3 attempts each).

**For Tier 4 deviations**, write a checkpoint file instead of proceeding:
```bash
cat > "{state_dir}/task-{task_id}-checkpoint.md" << 'CPEOF'
type: decision
description: {what you encountered and why it's architectural}
options:
  - A) {option description}
  - B) {option description}
  - C) Skip this task
CPEOF
```
Then return immediately with: "CHECKPOINT_NEEDED: {one-line description}"

## Analysis Paralysis Guard

You MUST write code. Track your consecutive read-only tool calls:
- Read-only = Read, Grep, Glob, or Bash commands that don't modify files
  (ls, cat, git log, git status, git diff, find, wc, head, tail, grep, etc.)
- Write = Edit, Write, or Bash commands that modify files (git commit, rm, mv, etc.)

If you make **8 consecutive read-only tool calls** without a single write,
you MUST either:
- Write code on your very next tool call, OR
- Return with: "BLOCKED: {description of what's preventing progress}"

If you exceed **15 total read-only calls** across the entire task without
any write, you MUST stop and return BLOCKED.

Do NOT loop on reading files without producing output.

## Verification Checklist

After committing, verify each claim:

1. **Files exist:** For each file you created, run `ls {file}` to confirm
2. **Tests pass:** Run `{test_command}` and confirm exit code 0
3. **Commit exists:** Run `git log --oneline -1` and confirm your commit message
4. **Spec conformance:** Every Behavior row ID in the governing spec is referenced by
   a passing test (`test_R3_*` or `// covers: <SPEC-id> R3`); each Invariant has a test.
   You did NOT edit any file under `docs/specs/`. Code lives under the spec's `code:` path.
5. **Review checks:** Scan your changes for:
   - Raw SQL with string interpolation → FAIL
   - Read-then-write without locks → FAIL
   - LLM output used directly in SQL/HTML/shell → FAIL
   - New enum values not handled in all switch/case/if-else chains → FAIL
   If any check fails, fix it (counts as a Tier 1 deviation).

## Derived-Doc Maintenance — Live, part of Definition-of-Done

**Doc-driven means docs are maintained AS you implement, never caught up afterward.**
There is no post-ship docs-update sweep to rely on — keeping the derived docs current is
part of a task's definition-of-done, and `/ship`'s conformance gate (check 7) will FAIL a
ship whose derived docs are stale. After committing + verifying a task, update — in the
same change — every derived doc the work touched:

1. **`docs/matrix.md`** — for each REQ/R-id in the task's `REQs covered`:
   - Add/update a row `| SPEC-id | R-id | {code} | {test} | COVERED |` (PARTIAL if no test).
   - Mark COVERED only if the referencing test actually exists and passes — never assert
     coverage you didn't verify. Update the Coverage Summary. (Create matrix from the
     docs-preamble template if missing.)
2. **`docs/architecture.md` §4** — if the task introduced a new top-level code directory /
   container, add it to the §4 container→directory map (so it stays the gate's truth, not
   a lagging mirror). A genuinely new architectural container also warrants flagging for an
   ADR — note it in `docs/REVIEW.md`.
3. **Touched derived prose** — if the change alters something `README.md`, `CLAUDE.md`, or
   `docs/contributing.md` describes (a new command, a changed setup/test step, a convention),
   update that doc in the same PR. Don't touch source layers (`specs/`, `prd.md`,
   `decisions/`) here — those lead, they don't follow code.

Commit derived-doc updates with the task (or `docs: maintain derived docs for {task}`).
Skip a sub-item only when the task genuinely didn't touch what it covers.

## REVIEW.md Append

If during implementation you made a decision not covered by existing specs
(e.g., chose a library, picked a data format, decided on an error handling strategy),
AND this decision could affect other modules or future work, append to `docs/REVIEW.md`:

```markdown
### [REVIEW-NNN] {Short title}
- **Date:** {today}
- **Skill:** /tai-execute solo (Task {N})
- **Context:** {What was being implemented}
- **Decision made:** {What you chose}
- **Risk if wrong:** {What breaks}
- **Related spec:** {REQ-ID or "none"}
- **Status:** PENDING
```

Only append for decisions with real trade-offs. Don't log trivial implementation choices.

## Summary Output

After completing (or failing), write your summary:

```bash
cat > "{state_dir}/task-{task_id}-summary.md" << 'SUMEOF'
# Task Summary: {task_name}
status: {done | failed | checkpoint_needed}
commit: {hash or "none"}
files_changed: {count}
deviations: {count}
deviation_details: {list of what was auto-fixed}
error: {if failed, describe why}
SUMEOF
```

Return your summary status as the final message.
```

### Resume Protocol (Solo)

When resuming from a previous execution:

1. Read `execute-state.json`
2. **Clean up partial state from failed tasks:** Before re-running any failed task,
   check for uncommitted changes on its target files:
   ```bash
   git diff --name-only
   git diff --cached --name-only
   ```
   If any of the failed task's target files have uncommitted changes, reset them:
   ```bash
   git checkout -- {file1} {file2} ...
   ```
   This ensures the retried subagent starts from a clean, known-good state.
3. Skip all tasks with status `done` (they have commits already)
4. Re-run tasks with status `failed` (fresh attempt on clean files)
5. Re-run tasks with status `skipped_dependency` IF their blocking task is now `done`
6. Skip tasks with status `skipped_dependency` if their blocker is still `failed`

When building subagent prompts for resumed tasks, include summaries from previously
completed tasks in the context so the subagent knows what already exists.

### Test Command Discovery (Solo)

If a task has no explicit `test_command`, discover it:

```bash
# Check for pyproject.toml (Python)
if [ -f pyproject.toml ]; then echo "uv run pytest"; fi

# Check for package.json (Node.js)
if [ -f package.json ]; then echo "npm test"; fi

# Check for Makefile
if [ -f Makefile ] && grep -q "^test:" Makefile; then echo "make test"; fi

# Check for go.mod (Go)
if [ -f go.mod ]; then echo "go test ./..."; fi
```

Default fallback: `uv run pytest` for Python projects (detected from pyproject.toml presence).

### Error Handling (Solo)

| Error | Action |
|-------|--------|
| Plan file not found | Stop with clear message + suggestion to run /tai-plan-eng |
| Plan has no tasks | Stop listing expected format |
| Missing required fields | Stop listing which fields are missing on which tasks |
| Circular dependency | Stop showing the cycle (e.g., "A → B → A") |
| Orphan dependency | Stop: "Task 3 depends on 'task-99' which doesn't exist" |
| Agent spawn fails | Retry 1x, then mark task FAILED |
| Subagent returns empty | Mark task FAILED: "subagent returned no result" |
| Test timeout (300s) | Mark task FAILED: "tests timed out after 300 seconds" |
| State file corrupted | Warn user, start fresh |
| Branch diverged | Warn user, allow resume if they choose |

### Execution Log (Solo)

After execution completes, log the result:

```bash
_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "{\"skill\":\"execute\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"STATUS\",\"tasks_total\":TOTAL,\"tasks_done\":DONE,\"tasks_failed\":FAILED,\"commit_hash\":\"$_COMMIT\"}" >> "$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl"
```

---

## Strategy: Team

You are the **team lead**. Your ONLY job is to coordinate — read the plan, create a
team, assign sub-phases, relay messages, and manage merges. You are a project manager,
not an engineer.

### Team Lead Iron Rules

1. **NEVER write code, edit files, or fix bugs yourself.** Every code change happens
   through an engineer agent. If something needs fixing, send a message to the
   responsible engineer or spawn a fix agent — do not touch the code.
2. **NEVER run tests, lint, or type-check yourself.** Engineers own their quality
   gates. You only check CI status via `gh run list`.
3. **NEVER review code yourself.** Send review requests to the reviewer agent.
   You relay findings between reviewer and engineer — you don't analyze diffs.
4. **ALWAYS use TeamCreate.** This is mandatory, not optional. Every team session
   starts with `TeamCreate`. Standalone `Agent()` calls without a team are forbidden
   because they cannot receive follow-up messages for the review/fix loop.
5. **Your tools are:** TeamCreate, TaskCreate/Update/List, SendMessage, AskUserQuestion,
   Bash (only for `gh` commands and git status checks), and Read (only for the plan
   and design docs during planning). That's it.

### Step 0: Understand the Target Phase

#### 0A. Parse user input

The user may say:
- "Launch a team for phase 2" → target Phase 2
- "Start phase 2" → target Phase 2
- "Parallel implement training & knowledge base" → match by title
- No phase specified → read the plan file and identify the next incomplete phase

#### 0B. Read plan and design docs

Read `$_REPO_ROOT/docs/plan/tasks.md`.
Extract the target phase's sub-phases.

For each sub-phase, also check if relevant design docs exist in `docs/design/` and
specs in `docs/specs/`. Read CLAUDE.md for the pre-PR quality gate checklist.

#### 0C. Dependency analysis

Determine which sub-phases can run in parallel by checking:
1. The **Module Ownership Map** in the plan file
2. Whether sub-phases share database models, migrations, or files
3. Whether one sub-phase's API contract is needed by another

Group sub-phases into **waves**:
- **Wave 1**: Foundation sub-phases (shared models, migrations, base services)
- **Wave 2**: Independent feature sub-phases that depend on Wave 1
- **Wave 3**: Integration sub-phases (frontend, cross-module features)

If ALL sub-phases are independent (no shared models/migrations), they can all
be Wave 1. The point of waves is to avoid the merge conflict hell from Phase 1 —
foundation gets merged to main first, then dependent work branches off updated main.

#### 0D. Generate API contracts (if frontend + backend in parallel)

If the phase has both backend and frontend sub-phases running in parallel,
extract a lightweight API contract from the design docs before spawning engineers:

```markdown
## API Contract: Phase N
### Endpoint: POST /api/v1/example
Request: { field1: string, field2: number }
Response: { id: string, status: "ok" }
```

Include this contract in both the backend and frontend engineer's task description.
This prevents the "org_name was required but frontend didn't know" bug from Phase 1.

#### 0E. Present the plan

Show the user what you're about to launch:

```
╔═══════════════════════════════════════════════════════════╗
║              /tai-execute (team) — Launch Plan             ║
╠═══════════════════════════════════════════════════════════╣
║  Target: Phase 2 — Training & Knowledge Base               ║
║  Engineers: 3                                               ║
║  Waves: 2                                                   ║
╠═══════════════════════════════════════════════════════════╣
║  Wave 1 (foundation):                                       ║
║    eng-1: 2.1 File storage (MinIO integration)              ║
║    eng-2: 2.2 Training sources CRUD                         ║
║  Wave 2 (depends on Wave 1):                                ║
║    eng-3: 2.3 RAG ingestion pipeline                        ║
║    eng-4: 2.4 Frontend training UI                          ║
╠═══════════════════════════════════════════════════════════╣
║  Orchestration: Claude Code (team lead, engineers, review)   ║
║  Coding agents: routed per task complexity + file type        ║
║    Complex (5+ files, cross-module) → Claude Code            ║
║    Backend (.py, .go, .sql)         → Codex (fallback: Gemini)║
║    Frontend (.tsx, .css, .vue)      → Gemini (fallback: Codex)║
║  Engineer: /tai-plan-eng → /tai-execute (solo) → /tai-ship    ║
║  Reviewer: /tai-review    QA: /tai-qa                       ║
╚═══════════════════════════════════════════════════════════╝
```

Ask the user to confirm before proceeding.

### Step 1: Create the Team

#### 1A. TeamCreate (MANDATORY — first action after user confirms)

Create a persistent team. This is the very first thing you do after the user
confirms the launch plan. Everything else depends on this — engineers, reviewers,
and fixers are all team members who communicate via SendMessage.

Never use standalone `Agent()` without `team_name`. Standalone agents cannot
receive follow-up messages, which breaks the review/fix loop entirely.

```
TeamCreate(
  team_name: "phase-{N}-impl",
  description: "Phase {N}: {title} — parallel implementation team"
)
```

#### 1B. Create tasks

Create one task per sub-phase using TaskCreate. Include:
- Sub-phase number and title
- Key files/modules involved
- Dependencies (which tasks must complete first)
- The API contract (if applicable)
- Wave assignment

For wave 2+ tasks, mark them as blocked by their wave 1 dependencies.

#### 1C. Spawn the reviewer

Spawn ONE persistent reviewer agent for the entire phase. This reviewer
handles all PRs using `/tai-review` — it stays alive and receives review
requests via SendMessage.

```
Agent(
  name: "reviewer",
  team_name: "phase-{N}-impl",
  subagent_type: "general-purpose",
  description: "Code reviewer for Phase {N}",
  prompt: "You are the code reviewer for Phase {N}. You will receive review
    requests via SendMessage from the team lead. For each request:
    1. Run /tai-review on the branch specified in the message.
       /tai-review analyzes the diff against main for SQL safety, LLM trust
       boundary violations, conditional side effects, and structural issues.
    2. Send the review findings back to the team lead via SendMessage.
    3. Stay alive — you will review multiple PRs across this phase.
    Do NOT exit after reviewing one PR.
    Do NOT review code manually — always use /tai-review.",
  run_in_background: true
)
```

#### 1D. Spawn engineers for Wave 1

For each Wave 1 sub-phase, spawn a **named team agent**:

```
Agent(
  name: "eng-{slug}",
  team_name: "phase-{N}-impl",
  subagent_type: "general-purpose",
  description: "Implement phase {N}.{M}: {title}",
  prompt: <see Engineer Prompt Template below>,
  run_in_background: true
)
```

Each engineer works in an **isolated git worktree** — this is critical. The
engineer prompt instructs them to create their own worktree. Never let parallel
engineers share a working directory.

### Step 2: Review, Fix, and Merge

Each PR goes through a review → feedback → fix loop before merging.
No PR merges without passing both code review and QA.

All communication happens via **SendMessage** between named team agents.
Never spawn standalone Agent() calls for reviews or fixes — use the existing
team agents so they retain context from prior messages.

**Reminder: you are the coordinator.** You read messages, relay them between
agents, check CI status with `gh`, and run `gh pr merge`. You never read diffs,
analyze code, write fixes, or run tests yourself. If something needs doing,
send a message to the right agent.

#### 2A. Track progress

Engineers report back via SendMessage to the team lead. Track:
- Which sub-phases have PRs ready for review
- Which are in the review/fix cycle
- Which are blocked or failed

#### 2B. Review each PR

When an engineer sends a message that their PR is ready:

1. **Verify CI is green**: `gh run list --branch <branch> --limit 1`
   - If CI red → `SendMessage(to: "eng-{slug}", ...)` with fix instructions

2. **Request review from the persistent reviewer via SendMessage**:
   ```
   SendMessage(
     to: "reviewer",
     content: "Review PR for phase {N}.{M} on branch {branch}.
       Run /tai-review on the branch.
       Send findings back to me (team-lead)."
   )
   ```
   The reviewer runs `/tai-review`, which analyzes the diff and produces
   a structured report. The reviewer sends findings back.

3. **Forward review findings to engineer via SendMessage**:
   ```
   SendMessage(
     to: "eng-{slug}",
     content: "Review found {N} issues:\n{findings}\n\nFix all issues, push, and confirm."
   )
   ```
   The engineer receives this, fixes the issues in their worktree, pushes,
   and sends back a confirmation message. This loop continues because the
   engineer agent is persistent — it doesn't need to be re-spawned.

4. **Re-review**: When engineer confirms fixes are pushed, either re-review
   inline or send another reviewer. Repeat until clean.

5. **Mark review as passed** when no issues remain.

#### 2C. QA each PR before merge

After code review passes:

1. **Spawn QA agent within the team** (never run QA inline — always delegate):
   ```
   Agent(
     name: "qa-{slug}",
     team_name: "phase-{N}-impl",
     subagent_type: "general-purpose",
     description: "QA test phase {N}.{M}",
     prompt: "You are the QA tester for phase {N}.{M} on branch {branch}.
       1. Check out the branch: git checkout {branch}
       2. Run /tai-qa to systematically test the changes.
          /tai-qa produces a structured report with health score,
          screenshots, and repro steps — it never fixes anything.
       3. Send the full QA report back to the team lead via SendMessage.
       Do NOT fix any bugs — report only. Do NOT use any other QA approach.",
     run_in_background: true
   )
   ```

2. **If QA finds bugs** → send report to engineer via SendMessage:
   ```
   SendMessage(
     to: "eng-{slug}",
     content: "QA found {N} bugs:\n{report}\n\nFix all bugs, push, and confirm."
   )
   ```
   Engineer fixes → pushes → confirms → re-QA. Same persistent agent loop.

3. **If QA is clean** → PR is ready to merge.

#### 2D. Merge and advance waves

Once a PR passes both review and QA:
1. Merge the PR: `gh pr merge <number> --squash --delete-branch`
2. **Remove the engineer's worktree** (branch is gone; the dir would otherwise
   linger forever): `git worktree remove ../eng-{slug} --force`. If the engineer
   is still alive, `SendMessage` it to stop first. Worktrees left on disk are the
   #1 cleanup miss — never skip this.
3. Verify main CI stays green: `gh run list --branch main --limit 1`
4. After ALL Wave N PRs are merged + main CI green → spawn Wave N+1
   engineers (new agents in the same team, branching off updated main)

Rolling merge within a wave: merge PRs as they pass review+QA — don't wait
for all engineers in the same wave to finish. This unblocks downstream work faster.

#### 2E. Handle blockers

If an engineer reports a blocker via SendMessage:
- **Tier 4 deviation** (architectural): Present to user via AskUserQuestion
- **Spec conflict** (spec wrong/insufficient/unapproved): Engineer must NOT edit the
  spec. Escalate to user via AskUserQuestion for a spec update + human re-approval
  before that engineer continues
- **Merge conflict**: `SendMessage(to: "eng-{slug}", ...)` with rebase instructions
- **CI failure**: Prioritize — CI-green is non-negotiable before merge
- **Cross-dependency**: If eng-A needs eng-B's work, coordinate merge order
- **Review disagreement**: Escalate to user if engineer and reviewer can't align

#### 2F. Ad-hoc fix tasks

For bug fixes, QA fixes, or review findings that need a dedicated engineer
(e.g., the original engineer's context is exhausted), spawn a new named agent
within the team:

```
Agent(
  name: "eng-fix-{slug}",
  team_name: "phase-{N}-impl",
  subagent_type: "general-purpose",
  description: "Fix {context} for phase {N}",
  prompt: <detailed fix instructions with file paths and expected changes>,
  run_in_background: true
)
```

This agent is also a team member — the team lead can send follow-up messages
if the fix needs iteration. Always point fix agents at the existing worktree
or branch, never create a new one for the same sub-phase.

### Step 3: Completion

When all sub-phases have passed review + QA + merged:

1. Verify all PRs merged and main CI green
2. Verify all sub-phase branches merged into main
3. **Sweep stale worktrees**: `git worktree prune` then `git worktree list` —
   confirm no `../eng-*` dirs remain. Force-remove any leftover:
   `git worktree remove ../eng-{slug} --force`. The phase is not COMPLETE until
   the worktree list is clean.
4. Report to user:

```
╔═══════════════════════════════════════════════════════════╗
║              Phase {N} — COMPLETE                          ║
╠═══════════════════════════════════════════════════════════╣
║  Sub-phases: {done}/{total}                                ║
║  PRs merged: {list with PR numbers}                        ║
║  Tests: {total test count}                                 ║
║  CI: GREEN                                                 ║
╚═══════════════════════════════════════════════════════════╝
```

4. Shut down the team: send `{type: "shutdown_request"}` to all engineers
5. Confirm each engineer maintained its derived docs live (matrix + architecture §4 +
   touched prose) as part of definition-of-done — `/ship`'s gate will verify this. Do NOT
   run `/docs-update` (it is on-demand only, not a pipeline step).

### Engineer Prompt Template (Team)

Each engineer gets this prompt, customized for their sub-phase:

```
You are an engineer on a parallel implementation team. You own one sub-phase
and drive it through the full tai pipeline autonomously.

## Capture Reflex
When the user declines or defers a suggestion, append one line to `docs/plan/backlog.md`
before continuing — don't lose it, don't act on it.

## Your Assignment
Sub-phase: {N.M} — {title}
Module: {module path}
Branch name: feat/phase-{N}.{M}-{slug}
Wave: {wave number}

## Key Files & Design Docs
{list of relevant design docs from docs/design/ to read}
{list of relevant spec files from docs/specs/ to read}
{list of key existing files to understand}

## API Contract (if applicable)
{contract extracted from design docs}

## Governing Specs
{list of APPROVED docs/specs/*.md files your sub-phase implements}

## Doc-First Execution (READ THIS FIRST)

Your sub-phase implements APPROVED behavioral specs in `docs/specs/`. The spec is
the ground truth; code is verified against it — never the reverse.

1. **Read each governing spec in full** before planning or coding. Confirm its
   frontmatter `status: approved`. If a spec is `draft`, missing, or insufficient,
   STOP and tell the team lead via SendMessage — the spec must be revised and
   re-approved by a human before you implement against it.
2. **Write code under each spec's `code:` path** and tests under its `tests:` path,
   staying within the spec's declared surface.
3. **Tests MUST reference the Behavior row IDs they cover** — each row ID (R1…RN)
   appears in its test as a `test_R3_*` name or a `// covers: <SPEC-id> R3` tag.
   Each Invariant gets a property/assertion test.
4. **NEVER edit a spec to match code you wrote** — that inverts doc-first order.
   `docs/specs/` is off-limits to your edits. If the code reveals the spec is wrong,
   STOP and flag the team lead for a spec update + human re-approval before continuing.
5. The spec governs *behavior* only — it is silent on security, performance, and
   maintainability. You still write safe, clean code: validate inputs at boundaries,
   no SQL string interpolation, no untrusted LLM output in SQL/HTML/shell, handle
   errors, keep functions small and immutable. Behavioral conformance is necessary,
   not sufficient.

## Setup — Create Your Worktree

You MUST work in an isolated git worktree. Create it first:

```bash
cd $(git rev-parse --show-toplevel)
git worktree add ../eng-{slug} -b feat/phase-{N}.{M}-{slug}
cd ../eng-{slug}
```

## Your Pipeline — MANDATORY tai-xxx skills

You MUST use the following tai skills in order. Do NOT skip any step or
implement manually what a skill already handles.

### 1. Plan: run /tai-plan-eng
Run `/tai-plan-eng` for your sub-phase. This produces a reviewed engineering
plan with architecture decisions, data flow, edge cases, and test coverage.
Do NOT start coding until the plan is reviewed and approved.

### 2. Execute: run /tai-execute
Run `/tai-execute` on the plan produced by step 1. For a single sub-phase plan
it auto-selects the solo single-context strategy, which breaks the plan into
tasks and dispatches each coding task to an external AI CLI (Codex or Gemini)
via `tai agent run`. The routing is automatic — /tai-execute picks the best
backend based on file types in each task:
- Backend code (.py, .go, .rs, .sql, config) → Codex
- Frontend code (.ts, .tsx, .jsx, .css, .vue) → Gemini
- Mixed or ambiguous → Codex (default)
If a backend fails, /tai-execute retries with the other backend automatically.

Do NOT write implementation code manually — let /tai-execute handle it.

### 3. Update Traceability
After /tai-execute completes, verify that `docs/matrix.md` was updated
with entries for the REQs your tasks covered. If any are missing, add them.

### 4. Ship: run /tai-ship
Run `/tai-ship` to ship your work. /tai-ship handles the FULL pre-PR
pipeline automatically:
- Detects and merges base branch
- Runs all tests
- Reviews the diff
- Bumps VERSION and updates CHANGELOG
- Commits, pushes, and creates the PR

Do NOT manually run quality gate checks or create PRs — /tai-ship does
all of this. If /tai-ship fails (tests, lint, etc.), fix the issues and
run /tai-ship again.

### 5. Notify team lead via SendMessage
After /tai-ship creates the PR, send a message to the team lead:

```
SendMessage(
  to: "team-lead",
  content: "PR ready: {url}\nCI status: {status}\nBlockers: {none or description}"
)
```

Then **stay alive and wait for review feedback**. You are a persistent
team agent — you will receive messages from the team lead with review
findings or QA bugs to fix. Do NOT exit after creating the PR.

### 6. Review → Fix loop (via SendMessage)
1. Team lead sends you review findings via SendMessage
2. For small fixes (< 20 lines): fix directly in your worktree
3. For larger fixes: dispatch to external backend via `tai agent run`:
   ```bash
   tai agent run \
     --backend {codex_or_gemini} \
     --dir "../eng-{slug}" \
     "Fix the following review issues in {files}: {findings}"
   ```
   Use the same routing rules as /tai-execute (backend vs frontend files).
   If the first backend fails, retry with the other.
4. Push the fixes and verify CI green
5. Send confirmation back:
   ```
   SendMessage(
     to: "team-lead",
     content: "Review fixes pushed. CI: {status}. Changes: {summary}"
   )
   ```
6. Wait for team lead to re-review or send more feedback
7. Repeat until team lead confirms review passed

### 6. QA → Fix loop (via SendMessage)
Same pattern as review. Team lead sends QA bug report, you dispatch fixes
to the appropriate backend via `tai agent run`, push, and confirm via
SendMessage.

Once QA is clean → team lead merges your PR.

Do NOT merge your own PR. The team lead controls merge timing
to coordinate wave execution and avoid conflicts.

Do NOT exit until the team lead sends a shutdown message or
confirms your PR has been merged.

## Rules

- Never push directly to main — always via PR
- Never merge your own PR — team lead merges after review + QA
- CI must be green before requesting review
- If you need code from another engineer's sub-phase, tell the team lead
  — do not cherry-pick across branches
- One concern per PR. Split if > 800 lines
- Use conventional commits: feat({scope}): {description}
- After merge, verify main CI stays green
- Address ALL review feedback before requesting re-review
- Coding work is dispatched to Codex/Gemini — you coordinate, not hand-code
- Implement against APPROVED specs only; never edit `docs/specs/` to match your code.
  If a spec is wrong or unapproved, STOP and flag the team lead for human re-approval
- Every Behavior row ID (R1…RN) must be covered by a test that references it
  (`test_R3_*` or `// covers: <SPEC-id> R3`)
```

### Error Recovery (Team)

| Situation | Action |
|-----------|--------|
| Engineer spawn fails | Retry 1x, then report to user |
| CI red after merge | Stop all work, fix main first |
| Merge conflict | Engineer rebases with `--force-with-lease` |
| Engineer stuck (no progress) | Check in via SendMessage, offer help |
| Wave 1 PR has issues | Fix before spawning Wave 2 |
| User cancels mid-phase | Gracefully shut down team, note progress |

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
