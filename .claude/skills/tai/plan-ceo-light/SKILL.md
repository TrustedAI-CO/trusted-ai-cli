---
name: plan-ceo-light
version: 1.0.0
description: |
  [TAI] Fast CEO-mode plan scan. Premise challenge, dream state mapping, and top 3
  risks — no 10-section walkthrough, no interactive stops, no expansion ceremonies.
  For the full mega plan review, use /plan-ceo instead.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# /plan-ceo-light: Fast CEO Plan Scan

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

This is the light version of `/plan-ceo`. Quick strategic sanity check — not a full review.

## Step 0: Detect base branch

1. `gh pr view --json baseRefName -q .baseRefName`
   If this succeeds, use that branch.
2. If no PR: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. Fallback: `main`.

## Step 1: Gather context

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
git log --oneline -15
git diff <base> --stat 2>/dev/null || echo "No diff from base"
```

Read any plan documents, PRDs, or architecture docs referenced by the user or found in the repo. Read CLAUDE.md and TODOS.md if they exist.

## Step 2: Premise challenge

Answer these three questions (2-3 sentences each):

1. **Is this the right problem?** Could a different framing yield a simpler or more impactful solution?
2. **What is the actual user/business outcome?** Is the plan the most direct path, or is it solving a proxy problem?
3. **What happens if we do nothing?** Real pain point or hypothetical?

## Step 3: Dream state mapping

```
CURRENT STATE                  THIS PLAN                  12-MONTH IDEAL
[describe in 1-2 lines]  ---> [describe delta]    --->   [describe target]
```

One sentence: does this plan move toward or away from the ideal?

## Step 4: Top 3 risks

List the 3 biggest risks to this plan succeeding. For each:

```
### Risk N: Title
**What could go wrong:** One sentence.
**Likelihood:** High / Medium / Low
**Mitigation:** One sentence — what to do about it.
```

If fewer than 3 risks, say so. If a risk is critical enough to block the plan, say: "BLOCKER — resolve before proceeding."

## Step 5: Verdict

One of:
- **Ship it** — plan is sound, risks are manageable
- **Adjust** — plan is directionally right but needs [specific change]
- **Rethink** — [fundamental concern that changes the approach]
- **Kill it** — this isn't worth doing because [reason]

## Step 6: Output format

Format the entire output as a single document:

```
## /plan-ceo-light: {Plan/Feature Name}

### Premise
{premise challenge answers}

### Dream State
{current → plan → ideal mapping}

### Top Risks
{numbered risks}

### Verdict: {Ship it / Adjust / Rethink / Kill it}
{One paragraph explanation}
```

Skip these (they belong to the full `/plan-ceo`):
- System audit
- Mode selection (expansion/hold/reduction)
- All 10 review sections (architecture, errors, security, data, quality, tests, perf, observability, deploy, long-term)
- Design review section
- Expansion opt-in / cherry-pick ceremonies
- CEO plan persistence to disk
- Review readiness dashboard
- TODOS.md updates
- Failure modes registry
- Error & rescue map

## Step 7: Log result

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
echo '{"skill":"plan-ceo","variant":"light","timestamp":"TIMESTAMP","status":"STATUS","verdict":"VERDICT"}' >> "$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: TIMESTAMP = ISO 8601 datetime, STATUS = "clean" if verdict is "ship it" else "issues_found", VERDICT = the verdict string.

## Important Rules

- **Be fast.** The whole scan should take under 2 minutes.
- **No interaction.** Output the document and stop. No AskUserQuestion calls.
- **Strategic only.** Don't review code, architecture details, tests, or performance — those are other skills' jobs.
- **Be direct.** CEO mode means no hedging. State your opinion.
- **Founder perspective.** Think about whether this is worth the team's time, not whether the code is clean.
