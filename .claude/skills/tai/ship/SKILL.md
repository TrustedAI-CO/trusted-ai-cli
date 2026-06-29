---
name: ship
version: 1.0.0
description: |
  [TAI] Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. Use when asked to "ship", "deploy", "push to main", "create a PR", or "merge and push".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
  - WebSearch
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
## Preamble (run first)

```bash

_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

## AskUserQuestion Format

**ALWAYS follow this structure for every AskUserQuestion call:**
1. **Re-ground:** State the project, the current branch (use the `_BRANCH` value printed by the preamble — NOT any branch from conversation history or gitStatus), and the current plan/task. (1-2 sentences)
2. **Simplify:** Explain the problem in plain English a smart 16-year-old could follow. No raw function names, no internal jargon, no implementation details. Use concrete examples and analogies. Say what it DOES, not what it's called.
3. **Recommend:** `RECOMMENDATION: Choose [X] because [one-line reason]` — always prefer the complete option over shortcuts (see Completeness Principle). Include `Completeness: X/10` for each option. Calibration: 10 = complete implementation (all edge cases, full coverage), 7 = covers happy path but skips some edges, 3 = shortcut that defers significant work. If both options are 8+, pick the higher; if one is ≤5, flag it.
4. **Options:** Lettered options: `A) ... B) ... C) ...` — when an option involves effort, show both scales: `(human: ~X / CC: ~Y)`

Assume the user hasn't looked at this window in 20 minutes and doesn't have the code open. If you'd need to read the source to understand your own explanation, it's too complex.

Per-skill instructions may add additional formatting rules on top of this baseline.

## Completeness Principle — Boil the Lake

AI-assisted coding makes the marginal cost of completeness near-zero. When you present options:

- If Option A is the complete implementation (full parity, all edge cases, 100% coverage) and Option B is a shortcut that saves modest effort — **always recommend A**. The delta between 80 lines and 150 lines is meaningless with CC+tai. "Good enough" is the wrong instinct when "complete" costs minutes more.
- **Lake vs. ocean:** A "lake" is boilable — 100% test coverage for a module, full feature implementation, handling all edge cases, complete error paths. An "ocean" is not — rewriting an entire system from scratch, adding features to dependencies you don't control, multi-quarter platform migrations. Recommend boiling lakes. Flag oceans as out of scope.
- **When estimating effort**, always show both scales: human team time and CC+tai time. The compression ratio varies by task type — use this reference:

| Task type | Human team | CC+tai | Compression |
|-----------|-----------|-----------|-------------|
| Boilerplate / scaffolding | 2 days | 15 min | ~100x |
| Test writing | 1 day | 15 min | ~50x |
| Feature implementation | 1 week | 30 min | ~30x |
| Bug fix + regression test | 4 hours | 15 min | ~20x |
| Architecture / design | 2 days | 4 hours | ~5x |
| Research / exploration | 1 day | 3 hours | ~3x |

- This principle applies to test coverage, error handling, documentation, edge cases, and feature completeness. Don't skip the last 10% to "save time" — with AI, that 10% costs seconds.

**Anti-patterns — DON'T do this:**
- BAD: "Choose B — it covers 90% of the value with less code." (If A is only 70 lines more, choose A.)
- BAD: "We can skip edge case handling to save time." (Edge case handling costs minutes with CC.)
- BAD: "Let's defer test coverage to a follow-up PR." (Tests are the cheapest lake to boil.)
- BAD: Quoting only human-team effort: "This would take 2 weeks." (Say: "2 weeks human / ~1 hour CC.")

## Steps to reproduce
1. {step}

## Raw output
```
{paste the actual error or unexpected output here}
```

## What would make this a 10
{one sentence: what tai should have done differently}

**Date:** {YYYY-MM-DD} | **Version:** {tai version} | **Skill:** /{skill}
```

Slug: lowercase, hyphens, max 60 chars (e.g. `browse-js-no-await`). Skip if file already exists. Max 3 reports per session. File inline and continue — don't stop the workflow. Tell user: "Filed tai field report: {title}"

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

# Ship: Fully Automated Ship Workflow

You are running the `/ship` workflow. This is a **non-interactive, fully automated** workflow. Do NOT ask for confirmation at any step. The user said `/ship` which means DO IT. Run straight through and output the PR URL at the end.

## Speed Mode

**Default mode is FAST.** Skip optional steps to ship quickly. Say "thorough" or "full" to run everything.

**Fast mode skips:**
- Step 3.4 (Test Coverage Audit) — note "Skipped — run `/ship thorough` for full coverage audit" in PR body
- Step 3.75 (Greptile Review) — skip silently
- Step 5.5 (docs/plan/backlog.md) — skip silently
- Design review portion of Step 3.5 — skip silently (code review still runs)

**Only stop for:**
- On the base branch (abort)
- Merge conflicts that can't be auto-resolved (stop, show conflicts)
- Test failures (stop, show failures)
- Pre-landing review finds ASK items that need user judgment
- MINOR or MAJOR version bump needed (ask — see Step 4)

**Never stop for:**
- Uncommitted changes (always include them)
- Version bump choice (auto-pick MICRO or PATCH — see Step 4)
- CHANGELOG content (auto-generate from diff)
- Commit message approval (auto-commit)
- Multi-file changesets (auto-split into bisectable commits)
- Auto-fixable review findings (dead code, N+1, stale comments — fixed automatically)

**Thorough mode additionally runs:**
- Step 3.4 (Test Coverage Audit)
- Step 3.75 (Greptile Review) — stops for user decision on comments
- Step 5.5 (docs/plan/backlog.md) — stops if missing or disorganized
- Design review in Step 3.5
- Test coverage gaps (auto-generate and commit, or flag in PR body)
- docs/plan/backlog.md completed-item detection (auto-remove)

---

## Step 1: Pre-flight

1. Check the current branch. If on the base branch, that's fine — ship directly.
   Skip Step 2 (merge base) and Step 8 (create PR) when shipping from the base branch.
   Just run tests, review, version bump, changelog, commit, and push.

2. Run `git status` (never use `-uall`). Uncommitted changes are always included — no need to ask.

3. Run `git diff <base>...HEAD --stat` and `git log <base>..HEAD --oneline` to understand what's being shipped.

4. Check review readiness:

## Review Readiness Dashboard

After completing the review, read the review log and config to display the dashboard.

```bash
_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_BRANCH_SAFE=$(echo "$_BRANCH" | tr '/' '-')
_STATE_DIR="$_REPO_ROOT/.tai/state"
_DOCS_DIR="$_REPO_ROOT/docs"
# Check new state dir first, fall back to old
cat "$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl" 2>/dev/null || cat "$HOME/.tai-skills/projects/$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")/${_BRANCH_SAFE}-reviews.jsonl" 2>/dev/null || echo "NO_REVIEWS"
echo "---CONFIG---"
echo "false"
echo "---DOCS---"
[ -f "$_DOCS_DIR/REVIEW.md" ] && grep -c 'PENDING' "$_DOCS_DIR/REVIEW.md" 2>/dev/null || echo "0"
[ -f "$_DOCS_DIR/matrix.md" ] && echo "MATRIX_EXISTS" || echo "NO_MATRIX"
```

Parse the output. Find the most recent entry for each skill (plan-ceo, plan-eng, plan-design, design-review-lite). Ignore entries with timestamps older than 7 days. For Design Review, show whichever is more recent between `plan-design` (full visual audit) and `design-review-lite` (code-level check). Append "(FULL)" or "(LITE)" to the status to distinguish. Display:

```
+====================================================================+
|                    REVIEW READINESS DASHBOARD                       |
+====================================================================+
| Review          | Runs | Last Run            | Status    | Required |
|-----------------|------|---------------------|-----------|----------|
| Eng Review      |  1   | 2026-03-16 15:00    | CLEAR     | YES      |
| Biz Review      |  0   | —                   | —         | no       |
| Design Review   |  0   | —                   | —         | no       |
+--------------------------------------------------------------------+
| VERDICT: CLEARED — Eng Review passed                                |
+====================================================================+
```

**Review tiers:**
- **Eng Review (required by default):** The only review that gates shipping. Covers architecture, code quality, tests, performance. Can be disabled globally with setting \`TAI_SKIP_ENG_REVIEW=true\` env var (the "don't bother me" setting).
- **Biz Review (optional):** Use your judgment. Recommend it for big product/business changes, new user-facing features, or scope decisions. Skip for bug fixes, refactors, infra, and cleanup.
- **Design Review (optional):** Use your judgment. Recommend it for UI/UX changes. Skip for backend-only, infra, or prompt-only changes.

**Verdict logic:**
- **CLEARED**: Eng Review has >= 1 entry within 7 days with status "clean" (or \`skip_eng_review\` is \`true\`)
- **NOT CLEARED**: Eng Review missing, stale (>7 days), or has open issues
- Biz and Design reviews are shown for context but never block shipping
- If \`skip_eng_review\` config is \`true\`, Eng Review shows "SKIPPED (global)" and verdict is CLEARED

If the Eng Review is NOT "CLEAR":

1. **Check for a prior override on this branch:**
   ```bash
   grep '"skill":"ship-review-override"' "$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl" 2>/dev/null || echo "NO_OVERRIDE"
   ```
   If an override exists, display the dashboard and note "Review gate previously accepted — continuing." Do NOT ask again.

2. **If no override exists,** use AskUserQuestion:
   - Show that Eng Review is missing or has open issues
   - RECOMMENDATION: Choose C if the change is obviously trivial (< 20 lines, typo fix, config-only); Choose B for larger changes
   - Options: A) Ship anyway  B) Abort — run /plan-eng first  C) Change is too small to need eng review
   - If Biz Review is missing, mention as informational ("Biz Review not run — recommended for product changes") but do NOT block
   - For Design Review: run `_DIFF_FILES=$(git diff --name-only <base>...HEAD 2>/dev/null); SCOPE_FRONTEND=$(echo "$_DIFF_FILES" | grep -qE "\.(tsx|jsx|css|html|vue|svelte)$" && echo true || echo false)`. If `SCOPE_FRONTEND=true` and no design review (plan-design or design-review-lite) exists in the dashboard, mention: "Design Review not run — this PR changes frontend code. The lite design check will run automatically in Step 3.5, but consider running /design-review for a full visual audit post-implementation." Still never block.

3. **If the user chooses A or C,** persist the decision so future `/ship` runs on this branch skip the gate:
   ```bash
   mkdir -p "$_STATE_DIR"
   echo '{"skill":"ship-review-override","timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","decision":"USER_CHOICE"}' >> "$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl"
   ```
   Substitute USER_CHOICE with "ship_anyway" or "not_relevant".

---

## Step 1.5: Document-Driven Gates (if docs/ exists)

If `docs/` directory exists in the project, run these additional checks:

**REVIEW.md check:**
If `docs/REVIEW.md` has PENDING items, use AskUserQuestion:
- "There are {N} pending items in docs/REVIEW.md that haven't been reviewed by a human.
  These are decisions the agent made during implementation that may need your approval."
- Show each PENDING item title
- Options: A) Review now (show full details)  B) Defer — ship anyway, I'll review later  C) Abort

**Spec coverage check:**
If `docs/matrix.md` exists, compute coverage:
- Count total REQs from `docs/specs/*.md`
- Count COVERED + PARTIAL rows in matrix
- Display: "Spec coverage: {covered}/{total} ({percentage}%)"
- If coverage < 50%: `[WARNING] Low spec coverage — many requirements are untraced`
- This is informational only, never blocks shipping

Add these to the Review Readiness Dashboard as additional rows:

```
| Doc Review     |  {N}  | PENDING items    | {status} | info       |
| Spec Coverage  |  —    | {X}/{Y} ({Z}%)   | {status} | info       |
```

---

## Step 2: Merge the base branch (BEFORE tests)

Fetch and merge the base branch into the feature branch so tests run against the merged state:

```bash
git fetch origin <base> && git merge origin/<base> --no-edit
```

**If there are merge conflicts:** Try to auto-resolve if they are simple (VERSION, schema.rb, CHANGELOG ordering). If conflicts are complex or ambiguous, **STOP** and show them.

**If already up to date:** Continue silently.

---

## Step 2.5: Test Framework Bootstrap

## Test Framework Bootstrap

**Detect existing test framework and project runtime:**

```bash
# Detect project runtime
[ -f Gemfile ] && echo "RUNTIME:ruby"
[ -f package.json ] && echo "RUNTIME:node"
[ -f requirements.txt ] || [ -f pyproject.toml ] && echo "RUNTIME:python"
[ -f go.mod ] && echo "RUNTIME:go"
[ -f Cargo.toml ] && echo "RUNTIME:rust"
[ -f composer.json ] && echo "RUNTIME:php"
[ -f mix.exs ] && echo "RUNTIME:elixir"
# Detect sub-frameworks
[ -f Gemfile ] && grep -q "rails" Gemfile 2>/dev/null && echo "FRAMEWORK:rails"
[ -f package.json ] && grep -q '"next"' package.json 2>/dev/null && echo "FRAMEWORK:nextjs"
# Check for existing test infrastructure
ls jest.config.* vitest.config.* playwright.config.* .rspec pytest.ini pyproject.toml phpunit.xml 2>/dev/null
ls -d test/ tests/ spec/ __tests__/ cypress/ e2e/ 2>/dev/null
# Check opt-out marker
[ -f .tai/no-test-bootstrap ] && echo "BOOTSTRAP_DECLINED"
```

**If test framework detected** (config files or test directories found):
Print "Test framework detected: {name} ({N} existing tests). Skipping bootstrap."
Read 2-3 existing test files to learn conventions (naming, imports, assertion style, setup patterns).
Store conventions as prose context for use in Phase 8e.5 or Step 3.4. **Skip the rest of bootstrap.**

**If BOOTSTRAP_DECLINED** appears: Print "Test bootstrap previously declined — skipping." **Skip the rest of bootstrap.**

**If NO runtime detected** (no config files found): Use AskUserQuestion:
"I couldn't detect your project's language. What runtime are you using?"
Options: A) Node.js/TypeScript B) Ruby/Rails C) Python D) Go E) Rust F) PHP G) Elixir H) This project doesn't need tests.
If user picks H → write `.tai/no-test-bootstrap` and continue without tests.

**If runtime detected but no test framework — bootstrap:**

### B2. Research best practices

Use WebSearch to find current best practices for the detected runtime:
- `"[runtime] best test framework 2025 2026"`
- `"[framework A] vs [framework B] comparison"`

If WebSearch is unavailable, use this built-in knowledge table:

| Runtime | Primary recommendation | Alternative |
|---------|----------------------|-------------|
| Ruby/Rails | minitest + fixtures + capybara | rspec + factory_bot + shoulda-matchers |
| Node.js | vitest + @testing-library | jest + @testing-library |
| Next.js | vitest + @testing-library/react + playwright | jest + cypress |
| Python | pytest + pytest-cov | unittest |
| Go | stdlib testing + testify | stdlib only |
| Rust | cargo test (built-in) + mockall | — |
| PHP | phpunit + mockery | pest |
| Elixir | ExUnit (built-in) + ex_machina | — |

### B3. Framework selection

Use AskUserQuestion:
"I detected this is a [Runtime/Framework] project with no test framework. I researched current best practices. Here are the options:
A) [Primary] — [rationale]. Includes: [packages]. Supports: unit, integration, smoke, e2e
B) [Alternative] — [rationale]. Includes: [packages]
C) Skip — don't set up testing right now
RECOMMENDATION: Choose A because [reason based on project context]"

If user picks C → write `.tai/no-test-bootstrap`. Tell user: "If you change your mind later, delete `.tai/no-test-bootstrap` and re-run." Continue without tests.

If multiple runtimes detected (monorepo) → ask which runtime to set up first, with option to do both sequentially.

### B4. Install and configure

1. Install the chosen packages (npm/bun/gem/pip/etc.)
2. Create minimal config file
3. Create directory structure (test/, spec/, etc.)
4. Create one example test matching the project's code to verify setup works

If package installation fails → debug once. If still failing → revert with `git checkout -- package.json package-lock.json` (or equivalent for the runtime). Warn user and continue without tests.

### B4.5. First real tests

Generate 3-5 real tests for existing code:

1. **Find recently changed files:** `git log --since=30.days --name-only --format="" | sort | uniq -c | sort -rn | head -10`
2. **Prioritize by risk:** Error handlers > business logic with conditionals > API endpoints > pure functions
3. **For each file:** Write one test that tests real behavior with meaningful assertions. Never `expect(x).toBeDefined()` — test what the code DOES.
4. Run each test. Passes → keep. Fails → fix once. Still fails → delete silently.
5. Generate at least 1 test, cap at 5.

Never import secrets, API keys, or credentials in test files. Use environment variables or test fixtures.

### B5. Verify

```bash
# Run the full test suite to confirm everything works
{detected test command}
```

If tests fail → debug once. If still failing → revert all bootstrap changes and warn user.

### B5.5. CI/CD pipeline

```bash
# Check CI provider
ls -d .github/ 2>/dev/null && echo "CI:github"
ls .gitlab-ci.yml .circleci/ bitrise.yml 2>/dev/null
```

If `.github/` exists (or no CI detected — default to GitHub Actions):
Create `.github/workflows/test.yml` with:
- `runs-on: ubuntu-latest`
- Appropriate setup action for the runtime (setup-node, setup-ruby, setup-python, etc.)
- The same test command verified in B5
- Trigger: push + pull_request

If non-GitHub CI detected → skip CI generation with note: "Detected {provider} — CI pipeline generation supports GitHub Actions only. Add test step to your existing pipeline manually."

### B6. Update CLAUDE.md

First check: If CLAUDE.md already has a `## Testing` section → skip. Don't duplicate.

Append a `## Testing` section (this is now the single home for testing docs — there is no separate testing doc):
- Philosophy: "100% test coverage is the key to great vibe coding. Tests let you move fast, trust your instincts, and ship with confidence — without them, vibe coding is just yolo coding. With tests, it's a superpower."
- Framework name and version
- Run command and test directory
- How to run tests (the verified command from B5)
- Test layers: Unit tests (what, where, when), Integration tests, Smoke tests, E2E tests
- Conventions: file naming, assertion style, setup/teardown patterns
- Test expectations:
  - 100% test coverage is the goal — tests make vibe coding safe
  - When writing new functions, write a corresponding test
  - When fixing a bug, write a regression test
  - When adding error handling, write a test that triggers the error
  - When adding a conditional (if/else, switch), write tests for BOTH paths
  - Never commit code that makes existing tests fail

### B7. Commit

```bash
git status --porcelain
```

Only commit if there are changes. Stage all bootstrap files (config, test directory, CLAUDE.md, .github/workflows/test.yml if created):
`git commit -m "chore: bootstrap test framework ({framework name})"`

---

---

## Step 3: Run tests (on merged code)

**Do NOT run `RAILS_ENV=test bin/rails db:migrate`** — `bin/test-lane` already calls
`db:test:prepare` internally, which loads the schema into the correct lane database.
Running bare test migrations without INSTANCE hits an orphan DB and corrupts structure.sql.

Run both test suites in parallel:

```bash
bin/test-lane 2>&1 | tee /tmp/ship_tests.txt &
npm run test 2>&1 | tee /tmp/ship_vitest.txt &
wait
```

After both complete, read the output files and check pass/fail.

**If any test fails:** Show the failures and **STOP**. Do not proceed.

**If all pass:** Continue silently — just note the counts briefly.

---

## Step 3.25: Eval Suites (conditional)

Evals are mandatory when prompt-related files change. Skip this step entirely if no prompt files are in the diff.

**1. Check if the diff touches prompt-related files:**

```bash
git diff origin/<base> --name-only
```

Match against these patterns (from CLAUDE.md):
- `app/services/*_prompt_builder.rb`
- `app/services/*_generation_service.rb`, `*_writer_service.rb`, `*_designer_service.rb`
- `app/services/*_evaluator.rb`, `*_scorer.rb`, `*_classifier_service.rb`, `*_analyzer.rb`
- `app/services/concerns/*voice*.rb`, `*writing*.rb`, `*prompt*.rb`, `*token*.rb`
- `app/services/chat_tools/*.rb`, `app/services/x_thread_tools/*.rb`
- `config/system_prompts/*.txt`
- `test/evals/**/*` (eval infrastructure changes affect all suites)

**If no matches:** Print "No prompt-related files changed — skipping evals." and continue to Step 3.5.

**2. Identify affected eval suites:**

Each eval runner (`test/evals/*_eval_runner.rb`) declares `PROMPT_SOURCE_FILES` listing which source files affect it. Grep these to find which suites match the changed files:

```bash
grep -l "changed_file_basename" test/evals/*_eval_runner.rb
```

Map runner → test file: `post_generation_eval_runner.rb` → `post_generation_eval_test.rb`.

**Special cases:**
- Changes to `test/evals/judges/*.rb`, `test/evals/support/*.rb`, or `test/evals/fixtures/` affect ALL suites that use those judges/support files. Check imports in the eval test files to determine which.
- Changes to `config/system_prompts/*.txt` — grep eval runners for the prompt filename to find affected suites.
- If unsure which suites are affected, run ALL suites that could plausibly be impacted. Over-testing is better than missing a regression.

**3. Run affected suites at `EVAL_JUDGE_TIER=full`:**

`/ship` is a pre-merge gate, so always use full tier (Sonnet structural + Opus persona judges).

```bash
EVAL_JUDGE_TIER=full EVAL_VERBOSE=1 bin/test-lane --eval test/evals/<suite>_eval_test.rb 2>&1 | tee /tmp/ship_evals.txt
```

If multiple suites need to run, run them sequentially (each needs a test lane). If the first suite fails, stop immediately — don't burn API cost on remaining suites.

**4. Check results:**

- **If any eval fails:** Show the failures, the cost dashboard, and **STOP**. Do not proceed.
- **If all pass:** Note pass counts and cost. Continue to Step 3.5.

**5. Save eval output** — include eval results and cost dashboard in the PR body (Step 8).

**Tier reference (for context — /ship always uses `full`):**
| Tier | When | Speed (cached) | Cost |
|------|------|----------------|------|
| `fast` (Haiku) | Dev iteration, smoke tests | ~5s (14x faster) | ~$0.07/run |
| `standard` (Sonnet) | Default dev, `bin/test-lane --eval` | ~17s (4x faster) | ~$0.37/run |
| `full` (Opus persona) | **`/ship` and pre-merge** | ~72s (baseline) | ~$1.27/run |

---

## Step 3.4: Test Coverage Audit (THOROUGH MODE ONLY — skip in fast mode)

**In fast mode:** Print "Step 3.4: Skipped (fast mode — run `/ship thorough` for coverage audit)" and continue to Step 3.5.

100% coverage is the goal — every untested path is a path where bugs hide and vibe coding becomes yolo coding. Evaluate what was ACTUALLY coded (from the diff), not what was planned.

**0. Before/after test count:**

```bash
# Count test files before any generation
find . -name '*.test.*' -o -name '*.spec.*' -o -name '*_test.*' -o -name '*_spec.*' | grep -v node_modules | wc -l
```

Store this number for the PR body.

**1. Trace every codepath changed** using `git diff origin/<base>...HEAD`:

Read every changed file. For each one, trace how data flows through the code — don't just list functions, actually follow the execution:

1. **Read the diff.** For each changed file, read the full file (not just the diff hunk) to understand context.
2. **Trace data flow.** Starting from each entry point (route handler, exported function, event listener, component render), follow the data through every branch:
   - Where does input come from? (request params, props, database, API call)
   - What transforms it? (validation, mapping, computation)
   - Where does it go? (database write, API response, rendered output, side effect)
   - What can go wrong at each step? (null/undefined, invalid input, network failure, empty collection)
3. **Diagram the execution.** For each changed file, draw an ASCII diagram showing:
   - Every function/method that was added or modified
   - Every conditional branch (if/else, switch, ternary, guard clause, early return)
   - Every error path (try/catch, rescue, error boundary, fallback)
   - Every call to another function (trace into it — does IT have untested branches?)
   - Every edge: what happens with null input? Empty array? Invalid type?

This is the critical step — you're building a map of every line of code that can execute differently based on input. Every branch in this diagram needs a test.

**2. Map user flows, interactions, and error states:**

Code coverage isn't enough — you need to cover how real users interact with the changed code. For each changed feature, think through:

- **User flows:** What sequence of actions does a user take that touches this code? Map the full journey (e.g., "user clicks 'Pay' → form validates → API call → success/failure screen"). Each step in the journey needs a test.
- **Interaction edge cases:** What happens when the user does something unexpected?
  - Double-click/rapid resubmit
  - Navigate away mid-operation (back button, close tab, click another link)
  - Submit with stale data (page sat open for 30 minutes, session expired)
  - Slow connection (API takes 10 seconds — what does the user see?)
  - Concurrent actions (two tabs, same form)
- **Error states the user can see:** For every error the code handles, what does the user actually experience?
  - Is there a clear error message or a silent failure?
  - Can the user recover (retry, go back, fix input) or are they stuck?
  - What happens with no network? With a 500 from the API? With invalid data from the server?
- **Empty/zero/boundary states:** What does the UI show with zero results? With 10,000 results? With a single character input? With maximum-length input?

Add these to your diagram alongside the code branches. A user flow with no test is just as much a gap as an untested if/else.

**3. Check each branch against existing tests:**

Go through your diagram branch by branch — both code paths AND user flows. For each one, search for a test that exercises it:
- Function `processPayment()` → look for `billing.test.ts`, `billing.spec.ts`, `test/billing_test.rb`
- An if/else → look for tests covering BOTH the true AND false path
- An error handler → look for a test that triggers that specific error condition
- A call to `helperFn()` that has its own branches → those branches need tests too
- A user flow → look for an integration or E2E test that walks through the journey
- An interaction edge case → look for a test that simulates the unexpected action

Quality scoring rubric:
- ★★★  Tests behavior with edge cases AND error paths
- ★★   Tests correct behavior, happy path only
- ★    Smoke test / existence check / trivial assertion (e.g., "it renders", "it doesn't throw")

**4. Output ASCII coverage diagram:**

Include BOTH code paths and user flows in the same diagram:

```
CODE PATH COVERAGE
===========================
[+] src/services/billing.ts
    │
    ├── processPayment()
    │   ├── [★★★ TESTED] Happy path + card declined + timeout — billing.test.ts:42
    │   ├── [GAP]         Network timeout — NO TEST
    │   └── [GAP]         Invalid currency — NO TEST
    │
    └── refundPayment()
        ├── [★★  TESTED] Full refund — billing.test.ts:89
        └── [★   TESTED] Partial refund (checks non-throw only) — billing.test.ts:101

USER FLOW COVERAGE
===========================
[+] Payment checkout flow
    │
    ├── [★★★ TESTED] Complete purchase — checkout.e2e.ts:15
    ├── [GAP]         Double-click submit — NO TEST
    ├── [GAP]         Navigate away during payment — NO TEST
    └── [★   TESTED] Form validation errors (checks render only) — checkout.test.ts:40

[+] Error states
    │
    ├── [★★  TESTED] Card declined message — billing.test.ts:58
    ├── [GAP]         Network timeout UX (what does user see?) — NO TEST
    └── [GAP]         Empty cart submission — NO TEST

─────────────────────────────────
COVERAGE: 5/12 paths tested (42%)
  Code paths: 3/5 (60%)
  User flows: 2/7 (29%)
QUALITY:  ★★★: 2  ★★: 2  ★: 1
GAPS: 7 paths need tests
─────────────────────────────────
```

**Fast path:** All paths covered → "Step 3.4: All new code paths have test coverage ✓" Continue.

**5. Generate tests for uncovered paths:**

If test framework detected (or bootstrapped in Step 2.5):
- Prioritize error handlers and edge cases first (happy paths are more likely already tested)
- Read 2-3 existing test files to match conventions exactly
- Generate unit tests. Mock all external dependencies (DB, API, Redis).
- Write tests that exercise the specific uncovered path with real assertions
- Run each test. Passes → commit as `test: coverage for {feature}`
- Fails → fix once. Still fails → revert, note gap in diagram.

Caps: 30 code paths max, 20 tests generated max (code + user flow combined), 2-min per-test exploration cap.

If no test framework AND user declined bootstrap → diagram only, no generation. Note: "Test generation skipped — no test framework configured."

**Diff is test-only changes:** Skip Step 3.4 entirely: "No new application code paths to audit."

**6. After-count and coverage summary:**

```bash
# Count test files after generation
find . -name '*.test.*' -o -name '*.spec.*' -o -name '*_test.*' -o -name '*_spec.*' | grep -v node_modules | wc -l
```

For PR body: `Tests: {before} → {after} (+{delta} new)`
Coverage line: `Test Coverage Audit: N new code paths. M covered (X%). K tests generated, J committed.`

---

## Step 3.5: Pre-Landing Review

Review the diff for structural issues that tests don't catch.

1. Read `.claude/skills/review/checklist.md`. If the file cannot be read, **STOP** and report the error.

2. Run `git diff origin/<base>` to get the full diff (scoped to feature changes against the freshly-fetched base branch).

3. Apply the review checklist in two passes:
   - **Pass 1 (CRITICAL):** SQL & Data Safety, LLM Output Trust Boundary
   - **Pass 2 (INFORMATIONAL):** All remaining categories

## Design Review (THOROUGH MODE ONLY — skip in fast mode)

**In fast mode:** Skip this design review subsection silently. Continue to step 4 (after code review output).

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
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
mkdir -p "$_STATE_DIR"
echo '{"skill":"design-review-lite","timestamp":"TIMESTAMP","status":"STATUS","findings":N,"auto_fixed":M}' >> "$_STATE_DIR/${_BRANCH_SAFE}-reviews.jsonl"
```

Substitute: TIMESTAMP = ISO 8601 datetime, STATUS = "clean" if 0 findings or "issues_found", N = total findings, M = auto-fixed count.

   Include any design findings alongside the code review findings. They follow the same Fix-First flow below.

4. **Classify each finding as AUTO-FIX or ASK** per the Fix-First Heuristic in
   checklist.md. Critical findings lean toward ASK; informational lean toward AUTO-FIX.

5. **Auto-fix all AUTO-FIX items.** Apply each fix. Output one line per fix:
   `[AUTO-FIXED] [file:line] Problem → what you did`

6. **If ASK items remain,** present them in ONE AskUserQuestion:
   - List each with number, severity, problem, recommended fix
   - Per-item options: A) Fix  B) Skip
   - Overall RECOMMENDATION
   - If 3 or fewer ASK items, you may use individual AskUserQuestion calls instead

7. **After all fixes (auto + user-approved):**
   - If ANY fixes were applied: commit fixed files by name (`git add <fixed-files> && git commit -m "fix: pre-landing review fixes"`), then **STOP** and tell the user to run `/ship` again to re-test.
   - If no fixes applied (all ASK items skipped, or no issues found): continue to Step 4.

8. Output summary: `Pre-Landing Review: N issues — M auto-fixed, K asked (J fixed, L skipped)`

   If no issues found: `Pre-Landing Review: No issues found.`

Save the review output — it goes into the PR body in Step 8.

---

## Step 3.75: Address Greptile review comments (THOROUGH MODE ONLY — skip in fast mode)

**In fast mode:** Skip this step silently. Continue to Step 4.

Read `.claude/skills/review/greptile-triage.md` and follow the fetch, filter, classify, and **escalation detection** steps.

**If no PR exists, `gh` fails, API returns an error, or there are zero Greptile comments:** Skip this step silently. Continue to Step 4.

**If Greptile comments are found:**

Include a Greptile summary in your output: `+ N Greptile comments (X valid, Y fixed, Z FP)`

Before replying to any comment, run the **Escalation Detection** algorithm from greptile-triage.md to determine whether to use Tier 1 (friendly) or Tier 2 (firm) reply templates.

For each classified comment:

**VALID & ACTIONABLE:** Use AskUserQuestion with:
- The comment (file:line or [top-level] + body summary + permalink URL)
- `RECOMMENDATION: Choose A because [one-line reason]`
- Options: A) Fix now, B) Acknowledge and ship anyway, C) It's a false positive
- If user chooses A: apply the fix, commit the fixed files (`git add <fixed-files> && git commit -m "fix: address Greptile review — <brief description>"`), reply using the **Fix reply template** from greptile-triage.md (include inline diff + explanation), and save to both per-project and global greptile-history (type: fix).
- If user chooses C: reply using the **False Positive reply template** from greptile-triage.md (include evidence + suggested re-rank), save to both per-project and global greptile-history (type: fp).

**VALID BUT ALREADY FIXED:** Reply using the **Already Fixed reply template** from greptile-triage.md — no AskUserQuestion needed:
- Include what was done and the fixing commit SHA
- Save to both per-project and global greptile-history (type: already-fixed)

**FALSE POSITIVE:** Use AskUserQuestion:
- Show the comment and why you think it's wrong (file:line or [top-level] + body summary + permalink URL)
- Options:
  - A) Reply to Greptile explaining the false positive (recommended if clearly wrong)
  - B) Fix it anyway (if trivial)
  - C) Ignore silently
- If user chooses A: reply using the **False Positive reply template** from greptile-triage.md (include evidence + suggested re-rank), save to both per-project and global greptile-history (type: fp)

**SUPPRESSED:** Skip silently — these are known false positives from previous triage.

**After all comments are resolved:** If any fixes were applied, the tests from Step 3 are now stale. **Re-run tests** (Step 3) before continuing to Step 4. If no fixes were applied, continue to Step 4.

---

## Step 4: Version bump (auto-decide)

1. Read the current `VERSION` file (4-digit format: `MAJOR.MINOR.PATCH.MICRO`)

2. **Auto-decide the bump level based on the diff:**
   - Count lines changed (`git diff origin/<base>...HEAD --stat | tail -1`)
   - **MICRO** (4th digit): < 50 lines changed, trivial tweaks, typos, config
   - **PATCH** (3rd digit): 50+ lines changed, bug fixes, small-medium features
   - **MINOR** (2nd digit): **ASK the user** — only for major features or significant architectural changes
   - **MAJOR** (1st digit): **ASK the user** — only for milestones or breaking changes

3. Compute the new version:
   - Bumping a digit resets all digits to its right to 0
   - Example: `0.19.1.0` + PATCH → `0.19.2.0`

4. Write the new version to the `VERSION` file.

---

## Step 5: CHANGELOG (auto-generate)

1. Read `docs/changelog.md` header to know the format.

2. Auto-generate the entry from **ALL commits on the branch** (not just recent ones):
   - Use `git log <base>..HEAD --oneline` to see every commit being shipped
   - Use `git diff <base>...HEAD` to see the full diff against the base branch
   - The CHANGELOG entry must be comprehensive of ALL changes going into the PR
   - If existing CHANGELOG entries on the branch already cover some commits, replace them with one unified entry for the new version
   - Categorize changes into applicable sections:
     - `### Added` — new features
     - `### Changed` — changes to existing functionality
     - `### Fixed` — bug fixes
     - `### Removed` — removed features
   - Write concise, descriptive bullet points
   - Insert after the file header (line 5), dated today
   - Format: `## [X.Y.Z.W] - YYYY-MM-DD`

**Spec + PR cross-reference (REQUIRED when `docs/specs/` exists).** Every bullet that
ships code under a spec's `code:` path must name the governing spec id(s) and the PR
number. This makes `changelog.md` the durable trace index — one anchor that chains to
the spec's git history and the PR diff. Format:

```
### Added
- Workspace project creation — SPEC-hub-create, SPEC-auth (#142)
### Fixed
- Token refresh race — SPEC-auth-token (#143)
```

If the PR number isn't known yet at this step (PR created in Step 8), write the spec
ids now and backfill `(#NNN)` after Step 8. Bullets touching no spec (pure refactor,
docs) need no spec id.

**Do NOT ask the user to describe changes.** Infer from the diff and commit history.

---

## Step 5.5: docs/plan/backlog.md (THOROUGH MODE ONLY — skip in fast mode)

**In fast mode:** Skip this step silently. Continue to Step 6.

Cross-reference the project's `docs/plan/backlog.md` (the deferred-work doc) against the changes being shipped. Remove completed items automatically; prompt only if the file is missing or disorganized.

**1. Check if `docs/plan/backlog.md` exists.**

**If it doesn't exist:** Use AskUserQuestion:
- Message: "GStack recommends maintaining a `docs/plan/backlog.md` split into a `## Active` section (work in flight) and a `## Backlog` section (deferred work). Would you like to create one?"
- Options: A) Create it now, B) Skip for now
- If A: Create `docs/plan/backlog.md` with a skeleton (`# Backlog` heading + `## Active` and `## Backlog` sections). Continue to step 3.
- If B: Skip the rest of Step 5.5. Continue to Step 6.

**2. Check structure and organization:**

Read `docs/plan/backlog.md` and verify it has an `## Active` section and a `## Backlog` section.

**If disorganized** (missing `## Active` or `## Backlog` section): Use AskUserQuestion:
- Message: "docs/plan/backlog.md doesn't follow the recommended structure (## Active and ## Backlog sections). Would you like to reorganize it?"
- Options: A) Reorganize now (recommended), B) Leave as-is
- If A: Reorganize in-place into `## Active` and `## Backlog`. Preserve all content — only restructure, never delete items.
- If B: Continue to step 3 without restructuring.

**3. Detect completed items:**

This step is fully automatic — no user interaction.

Use the diff and commit history already gathered in earlier steps:
- `git diff <base>...HEAD` (full diff against the base branch)
- `git log <base>..HEAD --oneline` (all commits being shipped)

For each backlog item, check if the changes in this PR complete it by:
- Matching commit messages against the item title and description
- Checking if files referenced in the item appear in the diff
- Checking if the item's described work matches the functional changes

**Be conservative:** Only mark an item as completed if there is clear evidence in the diff. If uncertain, leave it alone.

**4. Remove completed items** from the `## Active` and `## Backlog` sections — once shipped, the work leaves the backlog.

**5. Output summary:**
- `docs/plan/backlog.md: N items marked complete (item1, item2, ...). M items remaining.`
- Or: `docs/plan/backlog.md: No completed items detected. M items remaining.`
- Or: `docs/plan/backlog.md: Created.` / `docs/plan/backlog.md: Reorganized.`

**6. Defensive:** If `docs/plan/backlog.md` cannot be written (permission error, disk full), warn the user and continue. Never stop the ship workflow for a backlog failure.

Save this summary — it goes into the PR body in Step 8.

---

## Step 5.75: Framework Conformance Gate (BLOCKING)

**This is the real enforcement gate. It runs AFTER changelog/todos and BEFORE any commit, push, or PR.** It is the blocking counterpart to the advisory framework check in `/review`. If it fails, you HARD-STOP the ship — do not commit, do not push, do not open a PR.

**Skip only if** `docs/specs/` does not exist in the project (no spec layer to enforce). Print "Framework Conformance Gate: no docs/specs/ — skipped." and continue to Step 6.

Otherwise, run the same checklist as the review skill (framework-reviewer, contract §4). Gather the diff against the base branch (`git diff origin/<base>...HEAD`) and the spec/architecture sources, then check:

**1. Trace.** For every `docs/specs/*.md`, read its `code:` and `tests:` frontmatter.
   - Every `code:` and `tests:` path must exist on disk.
   - Every `code:` path must sit under a container directory declared in `docs/architecture.md` §4 (container → directory map).
   - Any missing path, or a `code:` path with no matching container → **FAIL**.

**2. Doc-first.** For each spec, detect whether the diff changes that spec's **Interface** section or any **Behavior** row (the contract surface — not just any file touch under `code:`).
   - If an Interface/Behavior change is detected in the code, there must be a matching change to the governing spec in the **same diff**, AND that spec must be `status: approved` in its frontmatter.
   - Interface/Behavior changed in code but spec unchanged, or spec changed but still `status: draft` → **FAIL**.
   - **`status: implemented` does NOT satisfy this for a behavior change.** Per the
     "Spec Evolution" rule, changing the Interface/Behavior of an already-`implemented`
     spec must reset it to `draft` and re-approve it to `approved` (re-stamping
     `approved_at`). An Interface/Behavior change shipping against a spec
     still marked `implemented` (never re-approved) → **FAIL** — this is the hole that
     lets unreviewed contract changes ship on a shipped surface.

**3. Row coverage.** For every Behavior row ID (`R1`…`RN`) in each spec, there must be a passing test under that spec's `tests:` path that references the ID — named `test_R3_*` or tagged `// covers: <SPEC-id> R3`.
   - Any Behavior row with no referencing passing test → **FAIL**.

**4. Unspec'd module.** Any code under the project's `spec-required` paths (the globs that require a governing spec) that has no spec naming it via `code:` → **FAIL**.

**5. Declared specs (one PR, declared + approved).** A PR may touch more than one spec
when the work is genuinely coupled, but it must DECLARE every spec it touches and all of
them must be approved. There is NO hard "one spec per PR" rule — coupled specs (a new
interface its caller depends on) ship together rather than forcing merge-ordering across
PRs. The enforceable rule:
   - Compute the set of specs whose `code:` paths the diff touches.
   - **Every** such spec must be `status: approved` (or `implemented`) — already covered
     by check 2 per-spec; here verify the *whole set*.
   - The PR body must list that set (Step 8 `## Specs`). A touched spec missing from the
     list → **FAIL** (trace gap).
   - Aim for one spec per PR (smallest reviewable contract change); >1 is allowed but
     each must be declared + approved.

**6. spec-exempt escape hatch.** A `spec-exempt:` marker may waive a finding ONLY when ALL hold:
   - It was **reviewer-applied**, not author-applied (the ship operator/reviewer adds it during this gate — never carried in by the diff author).
   - Its category is one of the fixed set: `refactor`, `docs`, `revert`. Any other category is invalid.
   - It is **counted** and reported (how many findings it waived, and which).
   - An exempt that is author-supplied, mis-categorized, or uncounted does NOT waive — treat the finding as a **FAIL**.

**On any FAIL (not waived by a valid spec-exempt):**

**HARD-STOP the ship.** Do NOT run Step 6 (commit), Step 7 (push), or Step 8 (PR). Report each violation with: the check that failed (Trace / Doc-first / Row coverage / Unspec'd module / Declared specs), the spec ID and/or file:line, and what is missing. Then use AskUserQuestion (following the AskUserQuestion Format above — re-ground, simplify, recommend, options):
- Explain in plain English which framework rule was broken and why it blocks the ship.
- `RECOMMENDATION: Choose A because the spec is the ground truth code is verified against — fixing it now keeps doc and code in sync.`
- Options:
  - A) Fix the violation now (write/approve the spec, add the missing test, correct the path) — `Completeness: 10/10`
  - B) Apply a governed `spec-exempt` (reviewer-applied, category `refactor`/`docs`/`revert`, counted) if and only if the change genuinely qualifies — `Completeness: 6/10`
  - C) Abort the ship — `Completeness: —`
- If A: apply the fix, then **STOP** and tell the user to re-run `/ship` so the gate re-evaluates against the corrected state.
- If B: record the exempt with its category and the count of findings it waives, report it, then re-run the checklist; continue only if the gate is now clean.
- If C: abort without committing.

**On PASS:** Print `Framework Conformance Gate: PASS — N specs traced, all Behavior rows covered, doc-first satisfied{, M spec-exempt applied}.` Continue to Step 6.

---

## Step 6: Commit (bisectable chunks)

**Goal:** Create small, logical commits that work well with `git bisect` and help LLMs understand what changed.

1. Analyze the diff and group changes into logical commits. Each commit should represent **one coherent change** — not one file, but one logical unit.

2. **Commit ordering** (earlier commits first):
   - **Infrastructure:** migrations, config changes, route additions
   - **Models & services:** new models, services, concerns (with their tests)
   - **Controllers & views:** controllers, views, JS/React components (with their tests)
   - **VERSION + docs/changelog.md + docs/plan/backlog.md:** always in the final commit

3. **Rules for splitting:**
   - A model and its test file go in the same commit
   - A service and its test file go in the same commit
   - A controller, its views, and its test go in the same commit
   - Migrations are their own commit (or grouped with the model they support)
   - Config/route changes can group with the feature they enable
   - If the total diff is small (< 50 lines across < 4 files), a single commit is fine

4. **Each commit must be independently valid** — no broken imports, no references to code that doesn't exist yet. Order commits so dependencies come first.

5. Compose each commit message:
   - First line: `<type>: <summary>` (type = feat/fix/chore/refactor/docs)
   - Body: brief description of what this commit contains
   - Only the **final commit** (VERSION + CHANGELOG) gets the version tag and co-author trailer:

```bash
git commit -m "$(cat <<'EOF'
chore: bump version and changelog (vX.Y.Z.W)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Step 7: Push

Push to the remote with upstream tracking:

```bash
git push -u origin <branch-name>
```

---

## Step 8: Create PR

Create a pull request using `gh`:

```bash
gh pr create --base <base> --title "<type>: <summary>" --body "$(cat <<'EOF'
## Summary
<bullet points from CHANGELOG>

## Specs
<If docs/specs/ exists: list every spec this PR touches, each with status — e.g.
"- SPEC-hub-create (approved)\n- SPEC-auth (approved)". This is the declared set from
Step 5.75 check 5; all must be approved. If the PR touches no spec: "No spec touched
(refactor/docs).">

## Test Coverage
<coverage diagram from Step 3.4, or "All new code paths have test coverage.">
<If Step 3.4 ran: "Tests: {before} → {after} (+{delta} new)">

## Pre-Landing Review
<findings from Step 3.5 code review, or "No issues found.">

## Design Review
<If design review ran: "Design Review (lite): N findings — M auto-fixed, K skipped. AI Slop: clean/N issues.">
<If no frontend files changed: "No frontend files changed — design review skipped.">

## Eval Results
<If evals ran: suite names, pass/fail counts, cost dashboard summary. If skipped: "No prompt-related files changed — evals skipped.">

## Greptile Review
<If Greptile comments were found: bullet list with [FIXED] / [FALSE POSITIVE] / [ALREADY FIXED] tag + one-line summary per comment>
<If no Greptile comments found: "No Greptile comments.">
<If no PR existed during Step 3.75: omit this section entirely>

## Backlog
<If items marked complete: bullet list of completed items with version>
<If no items completed: "No backlog items completed in this PR.">
<If docs/plan/backlog.md created or reorganized: note that>
<If docs/plan/backlog.md doesn't exist and user skipped: omit this section>

## Test plan
- [x] All Rails tests pass (N runs, 0 failures)
- [x] All Vitest tests pass (N tests)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Output the PR URL.**

**Backfill changelog PR refs.** If the changelog bullets (Step 5) were written with spec
ids but no `(#NNN)` because the PR didn't exist yet, edit `docs/changelog.md` now to add
the PR number to each new bullet, then amend the final commit (or include in the Step 8.5
docs commit). The changelog is the trace index — it must carry the PR number.

---

## Step 8.5: Documentation Update (if docs/ exists)

If `docs/` directory exists, run the docs-update workflow inline:

1. **Sync derived docs** — Cross-reference the diff against `docs/matrix.md` and
   `docs/architecture.md`. Auto-update factual content (paths, commands, component
   lists; architecture §4 container → directory map). Leave narrative sections alone.

2. **Sync derived docs only** — Update `README`, `docs/matrix.md`,
   `docs/architecture.md`, `changelog.md`, `contributing.md`, `CLAUDE.md`. NEVER
   touch `docs/specs/`, `docs/prd.md`, or
   `docs/decisions/` here — post-ship edits to those invert doc-first. If a spec is
   stale vs shipped code, that's a Framework Conformance failure (Step 5.75), not a
   docs-update fix.

3. **Commit docs changes** (if any) and push:

```bash
git add docs/
git diff --cached --quiet || git commit -m "docs: sync documentation for $(git log -1 --format=%s HEAD~1)"
git push
```

This is a lightweight inline version. For full docs audit (CHANGELOG voice polish,
cross-doc consistency, VERSION check), run `/docs-update` separately.

---

## Important Rules

- **Never skip tests.** If tests fail, stop.
- **Never skip the pre-landing review.** If checklist.md is unreadable, stop.
- **Never force push.** Use regular `git push` only.
- **Never ask for confirmation** except for MINOR/MAJOR version bumps and pre-landing review ASK items (batched into at most one AskUserQuestion).
- **Always use the 4-digit version format** from the VERSION file.
- **Date format in CHANGELOG:** `YYYY-MM-DD`
- **Split commits for bisectability** — each commit = one logical change.
- **docs/plan/backlog.md completion detection must be conservative.** Only mark items as completed when the diff clearly shows the work is done.
- **Use Greptile reply templates from greptile-triage.md.** Every reply includes evidence (inline diff, code references, re-rank suggestion). Never post vague replies.
- **Step 3.4 generates coverage tests.** They must pass before committing. Never commit failing tests.
- **The goal is: user says `/ship`, next thing they see is the review + PR URL.**

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
