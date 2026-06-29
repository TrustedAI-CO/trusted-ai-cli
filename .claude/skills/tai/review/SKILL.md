---
name: review
version: 1.0.0
description: |
  [TAI] Pre-landing PR review. Analyzes diff against the base branch for SQL safety, LLM trust
  boundary violations, conditional side effects, and other structural issues. Use when
  asked to "review this PR", "code review", "pre-landing review", or "check my diff".
allowed-tools:
  - Agent
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
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
## Unbiased Review — Always Use Subagent

**CRITICAL:** The review MUST run in a fresh subagent to avoid bias from the
current conversation. If you wrote the code being reviewed, you cannot objectively
review it — a subagent with no conversation history can.

When this skill is invoked, spawn **2 fresh reviewers in parallel** (one message, two
Agent calls — see "Review Loop" below), each given:
- The full review instructions (everything below)
- The branch name and base branch (from preamble)
- The repo path
- Optionally a complementary angle (e.g. one security/XSS, one correctness/regressions)

Do NOT run the review steps yourself. The subagents do the work and report back findings;
you union them, present to the user, and handle AskUserQuestion fix decisions.

```
Agent prompt template:
"You are a code reviewer. You have NOT seen this code before — review it fresh.
Repo: {repo_path}
Branch: {branch}
Base: {base_branch}

Follow the review checklist below exactly. Be honest and critical.
Report findings as: [SEVERITY] file:line — description.

{paste all steps below into the agent prompt}
"
```

## Review Loop — Iterate Until Clean (2 parallel blind reviewers per round)

Review is **not single-pass**. The skill is a loop controller: review → fix → review
again → fix → … until a round comes back clean. The controller (you) owns the loop; each
reviewer is a **fresh, stateless subagent**.

**Two reviewers per round, in parallel.** Every round spawns **2 fresh blind reviewers at
once** (one message, two Agent calls), given complementary angles where it helps — e.g.
security/XSS vs correctness/regressions, or two different dimensions of the diff. Running
two independent eyes *in parallel* is what replaces sequential re-rounds: a round is
**clean only when BOTH reviewers find nothing CRITICAL/HIGH**. One round of two parallel
reviewers finishes the loop — no second confirming round needed.

**The blind-reviewer rule (non-negotiable).** Each reviewer is given ONLY the current diff
(`base...HEAD`) + the specs/architecture. NEVER told what a prior round/reviewer found,
that anything was "already fixed," or to "re-check"/"focus on" anything. Fixes carry
between rounds **only as commits** — already in the next round's diff, so a fresh reviewer
re-derives whatever is still wrong. A reviewer told "we fixed the SQL injection"
rubber-stamps that area; a blind reviewer re-checks it. The *code* carries state across
rounds; the *findings list never does*. Each reviewer is a cold read.

**The loop:**
```
for round in 1..MAX (MAX = 4):
    [a, b] = spawn 2 FRESH blind reviewers IN PARALLEL (current diff + specs only;
             complementary angles)
    worth_fixing = (a ∪ b) findings with severity CRITICAL or HIGH
    if worth_fixing is empty:
        → DONE — both parallel reviewers found nothing worth fixing (one clean round)
    else:
        fix worth_fixing (Step 5 flow / investigate→execute), commit
        # nits (LOW/INFO from either) → docs/plan/backlog.md, never block, never fixed in-loop
if round == MAX and still not clean:  →  HALT to human with the outstanding findings
```

**Termination bar = "worth fixing," not "zero nits."** CRITICAL/HIGH gate the loop;
LOW/INFO/style nits are logged to `backlog.md` and do not keep the loop running. Don't
chase perfection — stop at "nothing worth fixing, twice."

## Preamble (run first)

```bash

_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

## Conventions

Shared conventions live in `docs-conventions.md` (single source of truth, ADR 0005):
**AskUserQuestion Format**, **Boil-the-Lake Completeness**, and the **tai Field Report**
template. `/tai-flow` loads that file once per run; in a standalone run, read it once.
Per-skill AskUserQuestion additions, if any, are noted below.

## Language

Respond in the same language the user is using. If the user writes in Japanese,
respond entirely in Japanese. If Vietnamese, respond entirely in Vietnamese.
Keep these in English regardless of language:
- Severity labels: [CRITICAL], [WARNING], [AUTO-FIXED], [HIGH], [MEDIUM], [LOW]
- Verdict strings: Ship it, Adjust, Rethink, Kill it
- Section headers from skill templates (e.g., ### Premise, ### Top Risks)
- Log/machine-readable output (.jsonl entries, bash commands)
- Technical terms: SQL, CSRF, API, LLM, XSS, etc.
Translate all prose, explanations, recommendations, and AskUserQuestion text.

## Step 0: Detect base branch

Determine which branch this PR targets. Use the result as "the base branch" in all subsequent steps.

1. Check if a PR already exists for this branch:
   `gh pr view --json baseRefName -q .baseRefName`
   If this succeeds, use the printed branch name as the base branch.

2. If no PR exists (command fails), detect the repo's default branch:
   `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`

3. If both commands fail, fall back to `main`.

Print the detected base branch name. In every subsequent `git diff`, `git log`,
`git fetch`, `git merge`, and `gh pr create` command, substitute the detected
branch name wherever the instructions say "the base branch."

---

# Pre-Landing PR Review

You are running the `/review` workflow. Analyze the current branch's diff against the base branch for structural issues that tests don't catch.

---

## Step 1: Check branch

1. Run `git branch --show-current` to get the current branch.
2. If on the base branch, output: **"Nothing to review — you're on the base branch or have no changes against it."** and stop.
3. Run `git fetch origin <base> --quiet && git diff origin/<base> --stat` to check if there's a diff. If no diff, output the same message and stop.

---

## Step 2: Read the checklist

Read `.claude/skills/review/checklist.md`.

**If the file cannot be read, STOP and report the error.** Do not proceed without the checklist.

---

## Step 2.5: Check for Greptile review comments

Read `.claude/skills/review/greptile-triage.md` and follow the fetch, filter, classify, and **escalation detection** steps.

**If no PR exists, `gh` fails, API returns an error, or there are zero Greptile comments:** Skip this step silently. Greptile integration is additive — the review works without it.

**If Greptile comments are found:** Store the classifications (VALID & ACTIONABLE, VALID BUT ALREADY FIXED, FALSE POSITIVE, SUPPRESSED) — you will need them in Step 5.

---

## Step 3: Get the diff

Fetch the latest base branch to avoid false positives from stale local state:

```bash
git fetch origin <base> --quiet
```

Run `git diff origin/<base>` to get the full diff. This includes both committed and uncommitted changes against the latest base branch.

---

## Step 3.5: Scope drift detection

Before reviewing code quality, check whether the diff matches its stated intent.

1. **Gather intent signals:**
   - Read commit messages on this branch: `git log origin/<base>..HEAD --format="%s%n%b"`
   - Read PR description if available: `gh pr view --json body -q .body 2>/dev/null`
   - Read `docs/plan/backlog.md` if it exists — check for items this branch claims to address
   - Check branch name for intent clues

2. **Compare diff against intent:**
   - **Scope creep:** Are there changes in the diff that don't match any stated intent? Files touched that have nothing to do with the branch's purpose?
   - **Missing requirements:** Does the intent describe work that ISN'T in the diff? Features mentioned in commits/PR but not implemented?
   - **Unrelated cleanup:** Changes that are fine individually but unrelated to this PR's goal (rename refactors, formatting, unrelated fixes)

3. **Output (only if drift detected):**
   ```
   ⚠ SCOPE DRIFT DETECTED

   Stated intent: {summary of what commits/PR say this branch does}

   SCOPE CREEP (changes beyond stated intent):
   - {file} — {what it does that's unrelated}

   MISSING (stated but not implemented):
   - {feature/fix described in commits but not in diff}

   UNRELATED CLEANUP (not harmful, but clutters the diff):
   - {file} — {what changed}
   ```

   If no drift detected, skip this step silently.

---

## Step 4: Two-pass review

Apply the checklist against the diff in two passes:

1. **Pass 1 (CRITICAL):** SQL & Data Safety, Race Conditions & Concurrency, LLM Output Trust Boundary, Enum & Value Completeness
2. **Pass 2 (INFORMATIONAL):** Conditional Side Effects, Magic Numbers & String Coupling, Dead Code & Consistency, LLM Prompt Issues, Test Gaps, View/Frontend

**Enum & Value Completeness requires reading code OUTSIDE the diff.** When the diff introduces a new enum value, status, tier, or type constant, use Grep to find all files that reference sibling values, then Read those files to check if the new value is handled. This is the one category where within-diff review is insufficient.

Follow the output format specified in the checklist. Respect the suppressions — do NOT flag items listed in the "DO NOT flag" section.

---

## Step 4.5: Design Review (conditional)

## Design Review (conditional, diff-scoped)

Check if the diff touches frontend files using `tai-diff-scope`:

```bash
_DIFF_FILES=$(git diff --name-only <base>...HEAD 2>/dev/null); SCOPE_FRONTEND=$(echo "$_DIFF_FILES" | grep -qE "\.(tsx|jsx|css|html|vue|svelte)$" && echo true || echo false)
```

**If `SCOPE_FRONTEND=false`:** Skip design review silently. No output.

**If `SCOPE_FRONTEND=true`:**

1. **Check for design doc.** Check `docs/design/visual.md`. All design findings are calibrated against it — patterns blessed in the design doc are not flagged. If not found, use universal design principles.

2. **Read `.claude/skills/review/design-checklist.md`.** If the file cannot be read, skip design review with a note: "Design checklist not found — skipping design review."

3. **Read each changed frontend file** (full file, not just diff hunks). Frontend files are identified by the patterns listed in the checklist.

4. **Apply the design checklist** against the changed files. For each item:
   - **[HIGH] mechanical CSS fix** (`outline: none`, `!important`, `font-size < 16px`): classify as AUTO-FIX
   - **[HIGH/MEDIUM] design judgment needed**: classify as ASK
   - **[LOW] intent-based detection**: present as "Possible — verify visually or run /design-review"

5. **Include findings** in the review output under a "Design Review" header, following the output format in the checklist. Design findings merge with code review findings into the same Fix-First flow.

6. **Log the result** for the Review Readiness Dashboard:

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
mkdir -p "$_REPO_ROOT/.tai/state"
echo '{"skill":"design-review-lite","timestamp":"TIMESTAMP","status":"STATUS","findings":N,"auto_fixed":M}' >> "$_REPO_ROOT/.tai/state/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: TIMESTAMP = ISO 8601 datetime, STATUS = "clean" if 0 findings or "issues_found", N = total findings, M = auto-fixed count.

Include any design findings alongside the findings from Step 4. They follow the same Fix-First flow in Step 5 — AUTO-FIX for mechanical CSS fixes, ASK for everything else.

---

## Step 4.7: Spec Conformance + Traceability Review (conditional)

Check if `docs/specs/` exists and has `.md` files. If not, skip silently.

If specs exist:

1. **Read each spec** in `docs/specs/*.md` (skip `spec.template.md`). Parse the
   Behavior table — each row has: ID (`R1`…`RN`), Given, When, Then. Read the
   frontmatter `code:`, `tests:`, and `status:` fields.

2. **Check implementation matches spec:** For each Behavior row, check if the diff
   contains changes that implement it:
   - Read the row's Given/When/Then
   - Search the diff for files/patterns that match
   - Flag rows that appear implemented but whose spec is still `status: draft`:
     `[INFO] SPEC-mtg-create R2 appears implemented in this diff but spec status is still "draft"`

3. **Check for spec violations:** For specs with `status: implemented`, verify the
   implementation still exists (hasn't been reverted or broken by this diff):
   - `[WARNING] SPEC-mtg-create marked implemented but code: file was modified/deleted`

4. **Scope creep detection:** For each file changed in the diff with >20 lines added,
   check if it relates to any spec. Files with significant changes not traceable to
   any spec:
   - `[INFO] SCOPE CREEP: {file} changed but not traceable to any spec`

5. **Matrix check:** If `docs/matrix.md` exists, check spec coverage.

6. **REVIEW.md check:** If `docs/REVIEW.md` has PENDING items, note them:
   - `[INFO] {N} pending review items in docs/REVIEW.md`

Include these findings in the review output. Spec conformance findings are
INFORMATIONAL — they flag spec/code drift for human attention (via `docs/REVIEW.md` → an
ADR or a spec revision through the proper doc-first flow). Never auto-edit specs to match
code, and don't route this to `docs-update` (it never touches source layers).

---

## Step 4.8: Framework Conformance (advisory — report, don't block)

Run this dimension **in the same fresh subagent** that performs the rest of the
review. Framework Conformance is **ADVISORY**: report findings as `[INFO]`
(or `[WARNING]` for clear violations) but **never block, never AUTO-FIX** — these
findings inform the author, and the blocking version of this gate lives in `/ship`.

Skip silently if `docs/specs/` does not exist.

Run these five checks against the diff and the `docs/` tree:

1. **Trace** — every `docs/specs/*.md` `code:`/`tests:` path exists on disk, and each
   `code:` path sits under a container path declared in `docs/architecture.md` §4
   (container→dir map). Flag any missing path or any `code:` outside all containers:
   `[WARNING] SPEC-auth-login code: api/src/auth/ not found under any container in architecture.md §4`

2. **Doc-first** — if the diff changes a spec's **Interface** section or a **Behavior**
   row, require a matching spec change in the same diff AND that the spec is
   `status: approved`. Trigger ONLY on interface/behavior change, NOT on any file
   touch under `code:`:
   `[WARNING] api/src/auth/login.ts changes the login interface but SPEC-auth-login is status: draft (must be approved)`

3. **Row coverage** — every Behavior row ID (`R1`…`RN`) in each spec is referenced by a
   passing test under that spec's `tests:` path, via test name (`test_R3_*`) or a tag
   comment (`// covers: <SPEC-id> R3`). Flag uncovered rows:
   `[INFO] SPEC-auth-login R3 has no test under tests: (expected test_R3_* or "// covers: SPEC-auth-login R3")`

4. **Unspec'd module** — code added under spec-required paths (the `code:` globs /
   container dirs) with no governing spec → flag:
   `[INFO] api/src/billing/ has code changes but no governing spec in docs/specs/`

5. **spec-exempt escape hatch** — a `spec-exempt:` marker may waive a doc-first or
   unspec'd finding, but ONLY when: it is **reviewer-applied (not the author)**, its
   category is one of the fixed set `refactor` / `docs` / `revert`, and each use is
   **counted** in the output. Report the count and reject author-applied or
   out-of-category exemptions:
   `[INFO] 2 spec-exempt waivers applied (1 refactor, 1 docs)` /
   `[WARNING] spec-exempt category "hotfix" is not allowed (must be refactor/docs/revert)`

Include all Framework Conformance findings in the review output under a
"Framework Conformance (advisory)" header. They are reported only — they do not
enter the AUTO-FIX/ASK Fix-First flow.

---

## Step 5: Fix-First Review

**Every finding gets action — not just critical ones.**

Output a summary header: `Pre-Landing Review: N issues (X critical, Y informational)`

### Step 5a: Classify each finding

For each finding, classify as AUTO-FIX or ASK per the Fix-First Heuristic in
checklist.md. Critical findings lean toward ASK; informational findings lean
toward AUTO-FIX.

### Step 5b: Auto-fix all AUTO-FIX items

Apply each fix directly. For each one, output a one-line summary:
`[AUTO-FIXED] [file:line] Problem → what you did`

### Step 5c: Batch-ask about ASK items

If there are ASK items remaining, present them in ONE AskUserQuestion:

- List each item with a number, the severity label, the problem, and a recommended fix
- For each item, provide options: A) Fix as recommended, B) Skip
- Include an overall RECOMMENDATION

Example format:
```
I auto-fixed 5 issues. 2 need your input:

1. [CRITICAL] app/models/post.rb:42 — Race condition in status transition
   Fix: Add `WHERE status = 'draft'` to the UPDATE
   → A) Fix  B) Skip

2. [INFORMATIONAL] app/services/generator.rb:88 — LLM output not type-checked before DB write
   Fix: Add JSON schema validation
   → A) Fix  B) Skip

RECOMMENDATION: Fix both — #1 is a real race condition, #2 prevents silent data corruption.
```

If 3 or fewer ASK items, you may use individual AskUserQuestion calls instead of batching.

### Step 5d: Apply user-approved fixes

Apply fixes for items where the user chose "Fix." Output what was fixed. Commit the
fixes (they become the input to the next round's diff).

If no ASK items exist (everything was AUTO-FIX), skip the question entirely.

### Step 5e: Loop back (blind next round)

After fixes are committed, **return to the Review Loop**: spawn the NEXT round's **2
parallel fresh blind reviewers** on the now-current diff. Do NOT carry this round's
findings or "I fixed X" into them — they read cold (see "Review Loop — Iterate Until
Clean"). Continue until **one round's two parallel reviewers both** find nothing
CRITICAL/HIGH, or the round cap (4) is hit → HALT to human with the outstanding findings.
LOW/INFO nits go to `backlog.md` and never keep the loop running.

### Greptile comment resolution

After outputting your own findings, if Greptile comments were classified in Step 2.5:

**Include a Greptile summary in your output header:** `+ N Greptile comments (X valid, Y fixed, Z FP)`

Before replying to any comment, run the **Escalation Detection** algorithm from greptile-triage.md to determine whether to use Tier 1 (friendly) or Tier 2 (firm) reply templates.

1. **VALID & ACTIONABLE comments:** These are included in your findings — they follow the Fix-First flow (auto-fixed if mechanical, batched into ASK if not) (A: Fix it now, B: Acknowledge, C: False positive). If the user chooses A (fix), reply using the **Fix reply template** from greptile-triage.md (include inline diff + explanation). If the user chooses C (false positive), reply using the **False Positive reply template** (include evidence + suggested re-rank), save to both per-project and global greptile-history.

2. **FALSE POSITIVE comments:** Present each one via AskUserQuestion:
   - Show the Greptile comment: file:line (or [top-level]) + body summary + permalink URL
   - Explain concisely why it's a false positive
   - Options:
     - A) Reply to Greptile explaining why this is incorrect (recommended if clearly wrong)
     - B) Fix it anyway (if low-effort and harmless)
     - C) Ignore — don't reply, don't fix

   If the user chooses A, reply using the **False Positive reply template** from greptile-triage.md (include evidence + suggested re-rank), save to both per-project and global greptile-history.

3. **VALID BUT ALREADY FIXED comments:** Reply using the **Already Fixed reply template** from greptile-triage.md — no AskUserQuestion needed:
   - Include what was done and the fixing commit SHA
   - Save to both per-project and global greptile-history

4. **SUPPRESSED comments:** Skip silently — these are known false positives from previous triage.

---

## Step 5.5: TODOS cross-reference

Read `docs/plan/backlog.md` if it exists. Cross-reference the PR against open TODOs:

- **Does this PR close any open TODOs?** If yes, note which items in your output: "This PR addresses TODO: <title>"
- **Does this PR create work that should become a TODO?** If yes, flag it as an informational finding.
- **Are there related TODOs that provide context for this review?** If yes, reference them when discussing related findings.

If `docs/plan/backlog.md` doesn't exist, skip this step silently.

---

## Step 5.6: Documentation staleness check

Cross-reference the diff against documentation files. For each `.md` file in the repo root and `docs/` directory (README.md, docs/architecture.md, docs/contributing.md, CLAUDE.md, etc.):

1. Check if code changes in the diff affect features, components, or workflows described in that doc file.
2. If the doc file was NOT updated in this branch but the code it describes WAS changed, flag it as an INFORMATIONAL finding:
   "Documentation may be stale: [file] describes [feature/component] but code changed in this branch. Consider running `/document-release`."

This is informational only — never critical. The fix action is `/document-release`.

If no documentation files exist, skip this step silently.

---

## Important Rules

- **Read the FULL diff before commenting.** Do not flag issues already addressed in the diff.
- **Fix-first, not read-only.** AUTO-FIX items are applied directly. ASK items are only applied after user approval. Never commit, push, or create PRs — that's /ship's job.
- **Be terse.** One line problem, one line fix. No preamble.
- **Only flag real problems.** Skip anything that's fine.
- **Use Greptile reply templates from greptile-triage.md.** Every reply includes evidence. Never post vague replies.

## Review Log

After completing the review, persist the result with the current commit hash for staleness tracking:

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
_COMMITS_ON_BRANCH=$(git rev-list --count origin/<base>..HEAD 2>/dev/null || echo "0")
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
mkdir -p "$_REPO_ROOT/.tai/state"
echo "{\"skill\":\"review\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"STATUS\",\"commit_hash\":\"$_COMMIT\",\"commits_on_branch\":$_COMMITS_ON_BRANCH,\"findings\":N,\"auto_fixed\":M,\"scope_drift\":DRIFT}" >> "$_REPO_ROOT/.tai/state/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: STATUS = "clean" if 0 findings or "issues_found", N = total findings, M = auto-fixed count, DRIFT = true/false (whether scope drift was detected in Step 3.5).

## Review Staleness

When displaying the Review Readiness Dashboard (in /ship or /plan-eng), check review staleness:

1. Read the last review entry's `commit_hash`
2. Count commits since that hash: `git rev-list --count {commit_hash}..HEAD`
3. If >0 commits since last review, show: `⚠ STALE — N commits since last review at {commit_hash}`
4. If 0 commits, show: `✓ FRESH — reviewed at current HEAD`

A stale review doesn't block shipping but should be flagged visibly in the dashboard.

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
