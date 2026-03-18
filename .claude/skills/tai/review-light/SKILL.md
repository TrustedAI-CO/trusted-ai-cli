---
name: review-light
version: 1.0.0
description: |
  [TAI] Fast single-pass PR review. Checks CRITICAL categories only (SQL safety, race
  conditions, LLM trust boundaries, enum completeness) with no interactive stops.
  Outputs findings as a list and moves on. For the full interactive review with
  auto-fixing and design checks, use /review instead.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# /review-light: Fast Single-Pass PR Review

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

This is the light version of `/review`. It trades thoroughness for speed — critical issues only, no interactive stops, no auto-fixing.

## Step 0: Detect base branch

1. `gh pr view --json baseRefName -q .baseRefName`
   If this succeeds, use that branch.
2. If no PR: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. Fallback: `main`.

## Step 1: Check branch and get diff

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

1. If on the base branch, output: **"Nothing to review — on base branch."** and stop.
2. Fetch and diff:
   ```bash
   git fetch origin <base> --quiet
   git diff origin/<base> --stat
   ```
3. If no diff, output: **"Nothing to review — no changes against base."** and stop.
4. Get the full diff: `git diff origin/<base>`

## Step 2: Single-pass CRITICAL review

Scan the diff for these categories ONLY:

### SQL & Data Safety
- Raw SQL with string interpolation
- Missing parameterized queries
- Unvalidated user input in queries
- Mass assignment / unscoped deletes or updates

### Race Conditions & Concurrency
- Read-then-write without locks
- Missing database-level constraints for uniqueness
- Shared mutable state without synchronization
- Time-of-check to time-of-use (TOCTOU) gaps

### LLM Output Trust Boundary
- LLM output used directly in SQL, HTML, or shell commands
- LLM response not validated/typed before database write
- Missing schema validation on structured LLM output
- Prompt injection vectors in user-controlled input passed to LLM

### Enum & Value Completeness
When the diff introduces a new enum value, status, tier, or type constant:
- Use Grep to find all files referencing sibling values
- Read those files to check the new value is handled everywhere (switch/case, if/else chains, mappings)

## Step 3: Output findings

Format output as:

```
## /review-light: N findings

1. [CRITICAL] file:line — Problem description
   Fix: Concrete fix suggestion

2. [CRITICAL] file:line — Problem description
   Fix: Concrete fix suggestion

No findings = "review-light: Clean — no critical issues found."
```

Do NOT:
- Use AskUserQuestion — just output the list
- Auto-fix anything — report only
- Review informational categories (dead code, magic numbers, naming, style)
- Run design sub-review
- Check Greptile comments
- Cross-reference TODOS.md
- Check documentation staleness

## Step 4: Log result

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
echo '{"skill":"plan-eng","variant":"light","timestamp":"TIMESTAMP","status":"STATUS","findings":N}' >> "$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: TIMESTAMP = ISO 8601 datetime, STATUS = "clean" if 0 findings else "issues_found", N = finding count.

## Important Rules

- **Be fast.** The whole review should take under 60 seconds.
- **CRITICAL only.** Skip anything that isn't a security risk, data corruption risk, or correctness bug.
- **No interaction.** Output findings and stop. No questions, no fixes.
- **Read the FULL diff before commenting.** Do not flag issues already addressed in the diff.
- **One line problem, one line fix.** No preamble, no explanations beyond what's needed.
