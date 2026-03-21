---
name: investigate
version: 1.0.0
description: |
  [TAI] Systematic debugging: root cause investigation, hypothesis testing, and verified fixes.
  Iron Law: no fixes without root cause. Auto-freezes edits to the affected module.
  3-strike escalation. Use when asked to "debug", "investigate", "find the bug",
  or "why is this broken".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

# /investigate: Systematic Debugging

## Iron Law

**No fixes without root cause investigation.** Do not change code until you understand
WHY the bug exists. A fix without root cause understanding is a coin flip.

## Language

Respond in the same language the user is using.
Keep these in English regardless of language:
- Severity labels: [CRITICAL], [WARNING], [ROOT CAUSE], [HYPOTHESIS], [VERIFIED]
- Phase names: Investigation, Hypothesis, Test, Fix, Verification
- Log/machine-readable output
- Technical terms

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

---

## Phase 1: Understand the Bug

Before touching any code:

1. **Reproduce:** Can you trigger the bug? Run the failing test, hit the endpoint, reproduce the error.
   If you cannot reproduce, STOP and ask the user for reproduction steps.

2. **Scope lock:** Identify the module/directory most likely responsible.
   ```
   SCOPE: {directory or module}
   ```
   All edits are restricted to this scope until root cause is confirmed.
   If you need to edit outside the scope, ask first via AskUserQuestion.

3. **Gather evidence:**
   - Read the error message/stack trace carefully
   - Read the relevant source files (full files, not just snippets)
   - Check git blame for recent changes to the affected area
   - Check if tests exist for this code path
   - Look for related issues in TODOS.md

4. **State the symptoms clearly:**
   ```
   BUG REPORT
   Symptom: {what happens}
   Expected: {what should happen}
   Scope: {module/directory}
   First seen: {commit or date if known}
   ```

---

## Phase 2: Hypothesize

Form up to 3 hypotheses for the root cause. For each:

```
HYPOTHESIS N: {one sentence}
Evidence for: {what supports this}
Evidence against: {what contradicts this}
Test: {how to confirm or rule out}
```

**Rank by likelihood.** Test the most likely first.

---

## Phase 3: Test Hypotheses

For each hypothesis, starting with the most likely:

1. **Design a test** that would confirm or rule out this hypothesis
2. **Run the test** (add a print/log, run a specific test case, check a value)
3. **Record the result:**
   ```
   HYPOTHESIS N: {CONFIRMED | RULED OUT}
   Evidence: {what the test showed}
   ```

### 3-Strike Rule

If 3 hypotheses are ruled out without finding the root cause:

**STOP.** Escalate via AskUserQuestion:
```
I've tested 3 hypotheses and none explain the bug:
1. {hypothesis} — ruled out because {reason}
2. {hypothesis} — ruled out because {reason}
3. {hypothesis} — ruled out because {reason}

Options:
A) Widen scope — investigate {broader area} (RECOMMENDATION)
B) Add instrumentation — add logging/tracing to narrow down
C) Pair debug — walk me through what you know about this code path
D) Defer — capture in TODOS.md and move on
```

Do NOT keep guessing after 3 strikes. The pattern of repeated failed hypotheses
means you're missing context that only escalation can provide.

---

## Phase 4: Fix

Only after root cause is CONFIRMED:

1. **State the root cause:**
   ```
   [ROOT CAUSE] {one sentence explanation}
   File: {file:line}
   Why: {why this code is wrong}
   When introduced: {commit hash if identifiable}
   ```

2. **Describe the fix before applying it:**
   ```
   FIX: {what you will change and why}
   Blast radius: {what else this change affects}
   ```

3. **Check blast radius:** Use Grep to find all callers/consumers of the changed code.
   If the fix affects more than the scoped module, ask via AskUserQuestion before proceeding.

4. **Apply the minimal fix.** Change as little as possible. This is not a refactoring opportunity.

---

## Phase 5: Verify

1. **Run the reproduction case** — does the bug no longer occur?
2. **Run existing tests** — did the fix break anything?
3. **Write a regression test** for this specific bug if one doesn't exist.
4. **Produce a debug report:**

```
DEBUG REPORT
============
Symptom: {what was broken}
Root cause: {why it was broken}
Fix: {what was changed}
Regression test: {test file:line or "added" or "existing test covers it"}
Hypotheses tested: {N} ({M} ruled out)
Scope: {module/directory}
Blast radius: {files affected by fix}
```

---

## Review Log

After producing the debug report, persist the result:

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
_BRANCH_SAFE=$(git branch --show-current | tr '/' '-')
_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
mkdir -p "$HOME/.tai-skills/projects/$_SLUG"
echo "{\"skill\":\"investigate\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"STATUS\",\"commit_hash\":\"$_COMMIT\",\"hypotheses_tested\":N,\"root_cause_found\":BOOL,\"regression_test\":BOOL}" >> "$HOME/.tai-skills/projects/$_SLUG/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: STATUS = "resolved" or "escalated" or "deferred", N = hypotheses tested, BOOL = true/false.

## Important Rules

- **Iron Law:** No code changes before root cause is confirmed. Period.
- **Scope lock:** Stay in the identified module. Ask before editing outside it.
- **3-strike rule:** Escalate after 3 failed hypotheses. Do not keep guessing.
- **Minimal fix:** Fix the bug, not the neighborhood. No drive-by refactoring.
- **Regression test:** Every fix gets a test. No exceptions.
- **Blast radius check:** Always check what else your fix affects before applying it.
