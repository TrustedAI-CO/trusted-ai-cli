---
name: next
version: 1.0.0
description: |
  [TAI] Quick "what should I do next?" dashboard. Reads PLAN.md, git worktrees,
  and tai-skills pipeline state to show phase progress, active worktrees,
  pipeline status, and recommended next action. Avoids conflicts with parallel
  sessions using git worktree awareness. Use when asked "what's next", "status",
  "where are we", "what should I work on", "next phase", "check progress", or
  at the start of any new session/worktree. Proactively suggest when a session
  starts with no clear task, or when the user finishes a phase and needs direction.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# TAI Next — What Should I Do Next?

A fast, read-only dashboard that answers: "Where are we? What's next? What are other sessions doing?"

Gathers data from three sources, synthesizes a recommendation, and gets out of the way.

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
echo "BRANCH_SAFE: $_BRANCH_SAFE"
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
echo "SLUG: $_SLUG"
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $_REPO_ROOT"
_STATE_DIR="$HOME/.tai-skills/projects/$_SLUG"
echo "STATE_DIR: $_STATE_DIR"
```

Store these values — they're used throughout.

## Data Gathering

Run these three steps **in parallel** (they're independent):

### Step A: Read PLAN.md

Read `$_REPO_ROOT/PLAN.md`. Extract:
- Each `## Phase N — Title` header
- Each `### N.M — Sub-phase title` under it
- The `## Module Ownership Map` section (which modules can be worked in parallel)

If PLAN.md doesn't exist, note "No PLAN.md found" and skip phase analysis.

### Step B: Git Worktree Scan

Run this bash block to get all worktree info in one shot:

```bash
echo "=== WORKTREES ==="
git worktree list
echo ""
for wt in $(git worktree list --porcelain | grep "^worktree " | sed 's/^worktree //'); do
  echo "--- $wt ---"
  echo "BRANCH: $(git -C "$wt" branch --show-current 2>/dev/null || echo 'detached')"
  echo "RECENT COMMITS:"
  git -C "$wt" log --oneline -5 2>/dev/null || echo "(no commits)"
  echo "DIRTY FILES: $(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  echo ""
done
```

For each worktree, infer what phase/module it's working on by matching branch name and commit subjects against phase keywords:
- Phase 1 keywords: auth, user, org, agent, login, register, jwt, role
- Phase 2 keywords: training, rag, ingest, chunk, embed, qdrant, minio, upload, knowledge, datasource
- Phase 3 keywords: chat, stream, sse, conversation, message
- Phase 4 keywords: widget, iframe, embed, snippet
- Phase 5 keywords: lead, escalation, capture
- Phase 6 keywords: analytics, assessment, knowledge-gap, metric
- Phase 7 keywords: billing, stripe, subscription, plan, payment

### Step C: Pipeline Status

Read the reviews JSONL and execute state. The slug from the remote may differ from directory names, so check both:

```bash
echo "=== PIPELINE STATE ==="
# Check under both possible slugs
for slug_dir in "$HOME/.tai-skills/projects/$_SLUG" "$HOME/.tai-skills/projects/company"; do
  if [ -d "$slug_dir" ]; then
    echo "--- State dir: $slug_dir ---"
    # Reviews for current branch
    REVIEWS_FILE="$slug_dir/${_BRANCH_SAFE}-reviews.jsonl"
    if [ -f "$REVIEWS_FILE" ]; then
      echo "REVIEWS ($REVIEWS_FILE):"
      cat "$REVIEWS_FILE"
    else
      echo "NO REVIEWS for branch $_BRANCH"
    fi
    echo ""
    # Execute state
    EXEC_FILE="$slug_dir/execute-state.json"
    if [ -f "$EXEC_FILE" ]; then
      echo "EXECUTE STATE:"
      cat "$EXEC_FILE"
    fi
    echo ""
    # Also check reviews for other branches (to show cross-branch awareness)
    echo "ALL REVIEW FILES:"
    ls "$slug_dir"/*-reviews.jsonl 2>/dev/null || echo "(none)"
  fi
done
```

## Dashboard Output

After gathering all data, synthesize and output these four sections:

### Section 1: Project Phase Status

Show each phase with a completion indicator. Rules for determining status:

- **COMPLETE**: All sub-phases have corresponding committed code, and subsequent phases have active work. Phase 0 is always COMPLETE if the repo has backend/, frontend/, docker-compose.yml, and CI/CD.
- **IN PROGRESS**: At least one sub-phase has an active worktree or recent pipeline activity.
- **NOT STARTED**: No worktree activity, no commits referencing this phase.

For each sub-phase within the active phase, show:
- `[worktree: NAME]` if a worktree is working on it
- `available` if no worktree claims it
- `available (parallel with N.M)` if the Module Ownership Map says it can run alongside another active sub-phase

Format:
```
## Project Phase Status
Phase 0: Foundation & DevOps ............. COMPLETE
Phase 1: Auth & Core CRUD ................ IN PROGRESS
  1.1 Auth module                         [worktree: san-francisco-v1]
  1.2 Organizations & users              available
  1.3 Agent CRUD                          available (parallel with 1.1)
  1.4 Frontend auth pages                 available (parallel with 1.1)
Phase 2: Training & Knowledge Base ....... NOT STARTED (blocked by Phase 1)
Phase 3-7: Not started
```

### Section 2: Active Worktrees

Show a table of all worktrees with their inferred work area and dirty status:

```
## Active Worktrees
| Worktree | Branch | Working On | Uncommitted | Recent Activity |
|----------|--------|------------|-------------|-----------------|
| company | main | — | clean | chore: add README... |
| san-francisco-v1 | thien-trustedai/san-francisco-v1 | Phase 1: Auth | 3 files | feat(auth): add JWT... |
```

### Section 3: Pipeline Status (Current Branch)

Show the TAI pipeline steps for the current branch. Parse the JSONL for the **latest** entry per skill name:

```
## Pipeline Status (branch: feature/auth)
| Step | Status | Last Run | Notes |
|------|--------|----------|-------|
| plan-ceo | — | never | optional |
| plan-eng | clean | 2026-04-07 | |
| execute | ALL_SUCCESS (4/4) | 2026-04-02 | |
| review | — | never | next step |
| ship+docs | — | never | |
```

Mark entries older than 7 days as `STALE` in the Notes column.

The pipeline steps in order are: `plan-ceo` (optional) → `plan-eng` → `execute` → `review` → `ship+docs`. Identify the **first incomplete required step** and mark it as "next step" in Notes.

Note: The `ship+docs` step runs `/tai-ship` which merges the PR, then immediately runs `/tai-document-release` to update README, CHANGELOG, ARCHITECTURE, and CLAUDE.md in the same session. These are a single step, not two separate pipeline stages.

### Section 4: Recommended Next Action

Apply this priority logic:

**Priority 1 — Current branch has pipeline work to continue:**
If the current branch has started the pipeline (any entries in reviews.jsonl), recommend the next incomplete step:
- plan-eng done, no execute → "Run /tai-execute [plan-file-path]"
- execute done, no review → "Run /tai-review or /tai-review-light"
- review done, no ship → "Run /tai-ship, then /tai-document-release to update docs"

**Priority 2 — On main or branch with completed pipeline:**
Look at PLAN.md for the next available sub-phase that is NOT being worked on in any worktree:
- Recommend creating a new worktree
- Suggest a branch name following the project convention (e.g., `feature/phase1-agents`)
- Recommend starting with `/tai-plan-eng`

**Priority 3 — Fresh session, nothing in progress anywhere:**
Recommend the first sub-phase of the earliest incomplete phase.

**Always include:**
- The exact `/tai-*` command to run
- A worktree creation command if applicable
- A warning about what to avoid (sub-phases claimed by other worktrees)

Format:
```
## Recommended Next Action
-> Pick up: Phase 1.3 Agent CRUD (backend/agents module)
-> Create worktree: git worktree add ../agent-crud -b feature/phase1-agents
-> Then run: /tai-plan-eng with Phase 1.3 tasks from PLAN.md
!! Avoid: Phase 1.1 Auth (active in worktree san-francisco-v1)
```

## Language

Respond in the user's language. Keep status labels, branch names, and technical terms in English.

## Important

- This skill is **read-only**. Never create files, write state, or modify anything.
- Keep it fast. Avoid heavy git operations (no `git log --all`, no blame).
- If data is missing or ambiguous, say so rather than guessing.
- Show the dashboard even if some sections have no data — empty sections with "none" are better than skipping them.
