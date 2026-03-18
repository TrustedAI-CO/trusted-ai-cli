---
name: plan-eng-light
version: 1.0.0
description: |
  [TAI] Fast engineering plan review. Scope challenge + architecture diagram + top
  concerns only. No interactive stops, no code quality/test/performance sections.
  For the full interactive 4-section review, use /plan-eng instead.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# /plan-eng-light: Fast Engineering Plan Review

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

This is the light version of `/plan-eng`. Scope check and architecture only — no interactive walkthrough.

## Step 0: Detect base branch

1. `gh pr view --json baseRefName -q .baseRefName`
   If this succeeds, use that branch.
2. If no PR: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. Fallback: `main`.

## Step 1: Gather context

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
git log --oneline -10
git diff <base> --stat 2>/dev/null || echo "No diff from base"
```

Read any plan documents, PRDs, or architecture docs referenced by the user or found in the repo.

## Step 2: Scope challenge

Answer these questions concisely (2-3 sentences each):

1. **What existing code already partially or fully solves each sub-problem?** Can we reuse existing flows?
2. **What is the minimum set of changes?** Flag anything deferrable.
3. **Complexity smell:** If the plan touches >8 files or introduces >2 new classes/services, call it out and suggest a simpler path.

## Step 3: Architecture review

Produce ONE ASCII diagram showing:
- New components and their relationships to existing ones
- Data flow direction (arrows)
- External dependencies

Then list the **top 3 architectural concerns**, each in this format:

```
### Concern N: Title
**Risk:** What could go wrong.
**Suggestion:** What to do about it.
```

If fewer than 3 concerns exist, say so: "Architecture looks clean — N concerns."

Skip these (they belong to the full `/plan-eng`):
- Code quality review
- Test diagram and test plan artifact
- Performance review
- Interactive AskUserQuestion stops
- Failure modes registry
- TODOS cross-reference

## Step 4: Output summary

Format the entire output as a single document:

```
## /plan-eng-light: {Plan/Feature Name}

### Scope Check
{scope challenge findings}

### Architecture
{ASCII diagram}

### Concerns
{numbered list of concerns}

### Verdict
{One sentence: "Proceed as planned" / "Simplify first — [specific suggestion]" / "Rethink — [reason]"}
```

## Step 5: Log result

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
echo '{"skill":"plan-eng","variant":"light","timestamp":"TIMESTAMP","status":"STATUS","concerns":N}' >> "$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: TIMESTAMP = ISO 8601 datetime, STATUS = "clean" if verdict is "proceed" else "issues_found", N = concern count.

## Important Rules

- **Be fast.** The whole review should take under 2 minutes.
- **No interaction.** Output the summary and stop. No AskUserQuestion calls.
- **Architecture only.** Skip code quality, tests, and performance — those are `/plan-eng`'s job.
- **Opinionated.** State your recommendation directly. Don't hedge.
- **Diagram is mandatory.** No review without an ASCII architecture diagram.
