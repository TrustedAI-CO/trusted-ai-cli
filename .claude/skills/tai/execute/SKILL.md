---
name: execute
version: 1.0.0
description: |
  [TAI] Autonomous plan executor. Reads a reviewed engineering plan, breaks it
  into tasks, and implements each task via fresh-context subagents. Supports
  parallel wave execution, 4-tier deviation rules, self-verification, and
  resume from interruption. Use after /tai-plan-eng produces a plan.
  Invoke with: /tai-execute [path-to-plan]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
echo "SLUG: $_SLUG"
echo "STATE_DIR: $HOME/.tai-skills/projects/$_SLUG"
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
```

## Language

Respond in the same language the user is using. If the user writes in Japanese,
respond entirely in Japanese. If Vietnamese, respond entirely in Vietnamese.
Keep these in English regardless of language:
- Status labels: DONE, FAILED, SKIPPED_DEPENDENCY, CHECKPOINT_NEEDED, ALL_SUCCESS, PARTIAL_SUCCESS, ALL_FAILED
- Tier labels: Tier 1, Tier 2, Tier 3, Tier 4
- Log/machine-readable output (.jsonl entries, bash commands)
- Technical terms: SQL, CSRF, API, LLM, XSS, etc.

---

# /tai-execute: Autonomous Plan Executor

You are the **orchestrator**. Your job is thin: parse the plan, group tasks into waves,
dispatch each task to a fresh subagent, collect results, and write the execution summary.
You do NOT implement code yourself. You delegate everything.

```
/tai-plan-eng ──► [plan file] ──► /tai-execute ──► [commits + summary] ──► /tai-ship
```

---

## Step 0: Discover and Parse Plan

### 0A. Find the plan file

If the user provided a path argument, use that file.

Otherwise, auto-discover. Branch names with `/` (e.g., `feature/foo`) must be
sanitized for glob matching since `/` acts as a path separator:

```bash
_BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
ls -t "$HOME/.tai-skills/projects/$_SLUG/"*"$_BRANCH_SAFE"*test-plan* 2>/dev/null | head -5
```

If no match with sanitized name, also try the raw branch name:
```bash
ls -t "$HOME/.tai-skills/projects/$_SLUG/"*test-plan* 2>/dev/null | grep "$_BRANCH" | head -5
```

If multiple files found, use the most recent (first in `ls -t` output).
If no files found, stop: **"No plan found for branch {branch}. Run /tai-plan-eng first, or provide a path: /tai-execute path/to/plan.md"**

### 0B. Parse ## Implementation Tasks

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

### 0C. Build Dependency DAG and Group Waves

Topological sort on depends_on:
- **Wave 1:** All tasks with `depends_on: none`
- **Wave 2:** Tasks whose dependencies are all in Wave 1
- **Wave N:** Tasks whose dependencies are all in Waves 1..(N-1)

**Parallel safety check:** Before finalizing each wave, verify no two tasks in the
same wave share target files. If overlap detected, move the later task (by task number)
to the next wave. Log: "Task {X} moved to wave {N+1} due to file overlap with Task {Y} on {file}."

### 0D. Check for Resume

```bash
cat "$HOME/.tai-skills/projects/$_SLUG/execute-state.json" 2>/dev/null || echo "NO_STATE"
```

If a state file exists AND matches the current branch AND the plan path:
- Show completed tasks, failed tasks, and remaining tasks
- Ask: "Previous execution found. Resume from where it left off?"
  - A) Resume (skip completed, re-run FAILED + SKIPPED_DEPENDENCY)
  - B) Start fresh (ignore previous state)

If the branch has diverged (new commits since last execution):
- Warn: "Branch has {N} new commits since last execution. Resume may cause conflicts."
- Still allow resume if user chooses

### 0E. Show Execution Plan

Before starting, display the plan:

```
╔══════════════════════════════════════════════════════╗
║              /tai-execute — Execution Plan            ║
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

---

## Step 1: Execute Waves

For each wave, in order:

### 1A. Route and Dispatch Subagents (parallel within wave)

Each coding subagent is dispatched to an external AI CLI (Codex or Gemini) via
`tai agent run`. The orchestrator (you) stays in Claude Code for coordination.

**Backend routing rules — decide per task:**

| Signal | Backend | Reason |
|--------|---------|--------|
| Task files are `.py`, `.go`, `.rs`, `.sql`, `Dockerfile`, `*.yaml`/`*.toml` config | **codex** | Strongest at backend/systems code |
| Task files are `.ts`, `.tsx`, `.jsx`, `.css`, `.scss`, `.html`, `.vue`, `.svelte` | **gemini** | Strongest at frontend/UI code |
| Task files are mixed backend + frontend | **codex** | Default tiebreaker |
| Task involves DB migrations, schema changes | **codex** | Better at SQL/ORM |
| Task involves test writing only | **codex** | Faster execution |
| Task involves docs, markdown, config only | **codex** | Faster execution |

**Routing algorithm (apply in order):**
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
  > "$HOME/.tai-skills/projects/$_SLUG/task-{task_id}-result.json" 2>&1 &
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

### 1B. Collect Results

After all background jobs finish, read both the agent result and the per-task summary:

```bash
# 1. Check agent-level result (did the CLI itself succeed?)
cat "$HOME/.tai-skills/projects/$_SLUG/task-{task_id}-result.json" 2>/dev/null

# 2. Check task-level summary (did the subagent complete its work?)
cat "$HOME/.tai-skills/projects/$_SLUG/task-{task_id}-summary.md" 2>/dev/null
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

### 1C. Update State File

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

### 1D. Wave Failure Propagation

After collecting wave results:
1. For each FAILED task: find all tasks in later waves that depend on it (directly or transitively)
2. Mark those downstream tasks as `skipped_dependency` with `blocked_by: {failed_task_id}`
3. Continue to the next wave — run all non-skipped tasks

---

## Step 2: Handle Checkpoints

When a subagent returns with status `checkpoint_needed`, read its checkpoint file:

```bash
cat "$HOME/.tai-skills/projects/$_SLUG/task-{task_id}-checkpoint.md" 2>/dev/null
```

The checkpoint file contains:
- **type:** `decision` | `human-action`
- **description:** what the subagent encountered
- **options:** (for decision type) list of choices

**For `decision` checkpoints (Tier 4 deviation):**
Use AskUserQuestion to present the options. Then resume the subagent with the user's choice
by dispatching a new Agent with the decision included in the prompt context.

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

---

## Step 3: Write Execution Summary

After all waves complete (or all remaining tasks are failed/skipped):

```bash
cat > "$HOME/.tai-skills/projects/$_SLUG/$_BRANCH-execution-summary.md" << 'SUMEOF'
# Execution Summary
Generated by /tai-execute on {date}
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

---

## Subagent Prompt Template

When dispatching each subagent via the Agent tool, construct this prompt:

```
You are implementing a single task from an engineering plan. Work autonomously.

## Your Task
Name: {task_name}
Files to modify/create: {file_list}
Acceptance criteria: {acceptance_criteria}
Test command: {test_command or "uv run pytest"}

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

1. **Read** the target files and understand the current code
2. **Write** the implementation (code + tests)
3. **Run tests** using: {test_command}
4. **Fix** any test failures (see Deviation Rules below)
5. **Commit** with message: "feat({scope}): {task_name}"
6. **Self-verify** (see Verification Checklist below)
7. **Write summary** to {summary_file_path}

## Deviation Rules

When you encounter issues during implementation:

| Tier | What happened | What to do | Limit |
|------|--------------|------------|-------|
| 1: Bug | Tests fail, runtime error | Fix it inline | 3 attempts per issue |
| 2: Missing | Linter flags missing validation | Add it | 3 attempts per issue |
| 3: Blocking | Import error, type mismatch within local code | Fix it | 3 attempts per issue |
| 4: Architectural | Need new package, new DB table, schema change | STOP — write checkpoint file | N/A |

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
4. **Review checks:** Scan your changes for:
   - Raw SQL with string interpolation → FAIL
   - Read-then-write without locks → FAIL
   - LLM output used directly in SQL/HTML/shell → FAIL
   - New enum values not handled in all switch/case/if-else chains → FAIL
   If any check fails, fix it (counts as a Tier 1 deviation).

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

---

## Resume Protocol

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

---

## Test Command Discovery

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

---

## Error Handling

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

---

## Execution Log

After execution completes, log the result:

```bash
_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "{\"skill\":\"execute\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"STATUS\",\"tasks_total\":TOTAL,\"tasks_done\":DONE,\"tasks_failed\":FAILED,\"commit_hash\":\"$_COMMIT\"}" >> "$HOME/.tai-skills/projects/$_SLUG/$_BRANCH-reviews.jsonl"
```
