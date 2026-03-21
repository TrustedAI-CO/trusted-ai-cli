---
name: second-opinion
version: 1.0.0
description: |
  [TAI] Multi-model second opinion. Spawns a separate Claude session (or external AI CLI)
  to independently review code, challenge assumptions, or provide adversarial feedback.
  Use when asked for "second opinion", "cross-check", "adversarial review", or "challenge this".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - AskUserQuestion
---

# /second-opinion: Multi-Model Review

Get an independent second opinion by spawning a separate AI session that reviews
the same code without seeing your current conversation context.

## Language

Respond in the same language the user is using.
Keep these in English: severity labels, technical terms, log output.

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

## Step 0: Detect base branch

1. `gh pr view --json baseRefName -q .baseRefName`
2. If no PR: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. Fallback: `main`.

## Step 1: Detect available AI CLIs

Check which AI tools are available:

```bash
echo "--- AI CLI availability ---"
command -v claude >/dev/null 2>&1 && echo "CLAUDE: available" || echo "CLAUDE: not found"
command -v codex >/dev/null 2>&1 && echo "CODEX: available" || echo "CODEX: not found"
command -v gemini >/dev/null 2>&1 && echo "GEMINI: available" || echo "GEMINI: not found"
```

**Priority order:** codex > gemini > claude (prefer a DIFFERENT model family for true independence).

If only `claude` is available, use it — a separate session with no shared context still provides value.
If none are available, report: "No AI CLI found. Install `claude`, `codex`, or `gemini` CLI to use /second-opinion." and stop.

## Step 2: Select mode

Three modes based on what the user needs:

### Mode: Review (default)
Independent code review of the current branch's diff.

### Mode: Challenge
Adversarial challenge — the second model tries to break your implementation
or find flaws in your reasoning.

### Mode: Consult
Open-ended question passed to the second model for an independent answer.

If the user doesn't specify a mode, default to **Review**.

## Step 3: Prepare context

Gather the diff and relevant files:

```bash
git fetch origin <base> --quiet 2>/dev/null
DIFF=$(git diff origin/<base> 2>/dev/null)
STAT=$(git diff origin/<base> --stat 2>/dev/null)
```

## Step 4: Execute

### Review mode

Construct a prompt and send it to the secondary AI:

```bash
# Using codex (if available):
echo "$REVIEW_PROMPT" | codex exec --quiet 2>/dev/null

# Using gemini (if available):
echo "$REVIEW_PROMPT" | gemini -p 2>/dev/null

# Fallback to claude:
echo "$REVIEW_PROMPT" | claude -p --model sonnet 2>/dev/null
```

**Review prompt template:**
```
You are a staff engineer doing a pre-landing code review. Review this diff for:
1. Security vulnerabilities (SQL injection, XSS, auth bypass)
2. Race conditions and concurrency bugs
3. Logic errors and edge cases
4. Performance issues
5. Missing error handling

Be specific: cite file:line, describe the problem, suggest a fix.
If no issues found, say "Clean — no issues found."

DIFF:
{diff content}
```

### Challenge mode

```
You are an adversarial code reviewer. Your job is to BREAK this implementation.
For each attack vector you find:
1. Describe the attack
2. Show how to exploit it
3. Rate severity (CRITICAL/HIGH/MEDIUM/LOW)
4. Suggest a fix

Think like a hostile user, a race condition, a network failure, an edge case.
Be creative. If you can't find anything, say so honestly.

DIFF:
{diff content}
```

### Consult mode

Pass the user's question directly to the secondary AI with the repo context.

## Step 5: Cross-model analysis

After receiving the second opinion, compare it with the current session's findings:

```
SECOND OPINION REPORT
=====================
Model: {which AI was used}
Mode: {Review / Challenge / Consult}

FINDINGS:
{list findings from the second model}

CROSS-MODEL ANALYSIS:
- Overlapping findings (both models agree): {list}
- Unique to second model: {list}
- Unique to primary review: {list — if /review was run before}

RECOMMENDATION: {what to action based on the combined analysis}
```

**Overlapping findings** are high-confidence — both models independently spotted the same issue.
**Unique findings** from either model deserve attention — they may catch blind spots.

## Step 6: Action

Present findings via AskUserQuestion. For each actionable finding:

```
Second opinion found N issues (M overlap with /review, K new):

1. [SEVERITY] file:line — Problem
   Fix: suggested fix
   → A) Fix  B) Skip  C) Disagree — explain why

RECOMMENDATION: {which to fix}
```

## Review Log

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
echo "{\"skill\":\"second-opinion\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"STATUS\",\"commit_hash\":\"$_COMMIT\",\"model\":\"MODEL\",\"mode\":\"MODE\",\"findings\":N,\"overlapping\":M}" >> "$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
```

## Important Rules

- **Independence matters.** The second model must NOT see the current conversation.
  It reviews the raw diff with a fresh perspective.
- **Different model preferred.** codex or gemini > claude for true independence.
  A separate claude session is still valuable but less independent.
- **Don't auto-fix.** Present findings to the user. The second opinion informs, not dictates.
- **Cross-reference.** Always compare with /review findings if available.
- **Be honest about limitations.** If the secondary AI gives low-quality output, say so.
