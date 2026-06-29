---
name: docs-update
version: 1.0.0
description: |
  [TAI] On-demand derived-docs refresh. NOT a pipeline step — derived docs are maintained
  live by /tai-execute and verified by /ship's gate. Use this only to deliberately refresh
  or regenerate derived docs (README/architecture/contributing/CLAUDE/changelog voice,
  backlog cleanup, optional VERSION bump) — e.g. onboarding an existing repo, regenerating
  a disposable map, or a periodic consistency pass. Use when asked to "refresh the docs",
  "regenerate the docs map", or "do a docs consistency pass".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

## Not a pipeline step (read first)

**Derived docs are maintained LIVE, not synced at the end.** `/tai-execute` keeps matrix +
architecture §4 + touched derived prose current as it implements; `/ship` writes the
changelog and its gate VERIFIES derived docs are in sync (failing the ship if not). So
this skill is **not** auto-chained by `/tai-flow` and is **not** run by `/ship`. It exists
only as an **on-demand** tool: onboarding an existing/legacy repo, regenerating a
deliberately-disposable map, or a periodic consistency pass a human chooses to run. If
you reached here as part of a normal ship, you don't need it — the docs are already current.

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

# Document Refresh: On-Demand Derived-Docs Pass

You are running the `/docs-update` workflow. This is an **on-demand** refresh — NOT a
pipeline step, NOT run by `/ship`. A human invokes it deliberately (onboarding an existing
repo, regenerating a disposable map, or a periodic consistency pass). Normal feature work
keeps derived docs current live via `/tai-execute`. Your job here: ensure every derived
documentation file is accurate, up to date, and written in a friendly, user-forward voice.

You are mostly automated. Make obvious factual updates directly. Stop and ask only for risky or
subjective decisions.

---

## ⛔ HARD RULE — DERIVED DOCS ONLY (READ FIRST, NON-NEGOTIABLE)

This is an **on-demand** skill (not a pipeline step). It may update **derived / living docs ONLY**:

- `README.md`
- `docs/architecture.md` (derived sections only — e.g. §4 code map)
- `docs/matrix.md`
- `docs/plan/backlog.md`
- `docs/changelog.md`
- `docs/contributing.md`
- `CLAUDE.md`

Content that used to live under `docs/trace/` now lives in these derived targets:
code map → `docs/architecture.md` §4; stack → `README.md`; conventions & testing →
`CLAUDE.md`; tech-debt & deferred work → `docs/plan/backlog.md`. The `docs/trace/`
folder no longer exists.

**It MUST NEVER edit any of the following — these are authored, doc-first source layers:**

- `docs/specs/` (any spec file)
- `docs/prd.md`
- `docs/decisions/` (any ADR)

**Why:** The framework requires doc-first order (L0 intent → L1 decisions/architecture →
L2 specs → L3 code). Editing a spec, intent, or decision to match code that has **already
shipped** inverts that order — it rewrites the contract to fit the implementation instead of
the implementation fitting the contract. That silently destroys the source of truth.

**If a spec / intent / decision is out of date versus the shipped code:** DO NOT fix it.
**FLAG it as a doc-first violation for the human** (in your output, as a `[CRITICAL]` finding)
and let a human reconcile it through the proper spec-first flow. Never silently edit these
files, even if the fix looks trivial and obviously correct.

**Only stop for:**
- Risky/questionable doc changes (narrative, philosophy, security, removals, large rewrites)
- VERSION bump decision (if not already bumped)
- New backlog items to add
- Cross-doc contradictions that are narrative (not factual)

**Never stop for:**
- Factual corrections clearly from the diff
- Adding items to tables/lists
- Updating paths, counts, version numbers
- Fixing stale cross-references
- CHANGELOG voice polish (minor wording adjustments)
- Marking backlog items complete
- Cross-doc factual inconsistencies (e.g., version number mismatch)

**NEVER do:**
- Overwrite, replace, or regenerate CHANGELOG entries — polish wording only, preserve all content
- Bump VERSION without asking — always use AskUserQuestion for version changes
- Use `Write` tool on docs/changelog.md — always use `Edit` with exact `old_string` matches
- Edit `docs/specs/`, `docs/prd.md`, or `docs/decisions/` — these are doc-first source layers; flag staleness, never fix it

---

## Step 1: Pre-flight & Diff Analysis

1. Check the current branch. If on the base branch, **abort**: "You're on the base branch. Run from a feature branch."

2. Gather context about what changed:

```bash
git diff <base>...HEAD --stat
```

```bash
git log <base>..HEAD --oneline
```

```bash
git diff <base>...HEAD --name-only
```

3. Discover all documentation files in the repo. All docs are Markdown — root-level files
   (README.md, CLAUDE.md) and everything under `docs/`:

```bash
find . -maxdepth 1 -name "*.md" -not -path "./.git/*" | sort
find ./docs -maxdepth 3 -name "*.md" 2>/dev/null | sort
```

4. Classify the changes into categories relevant to documentation:
   - **New features** — new files, new commands, new skills, new capabilities
   - **Changed behavior** — modified services, updated APIs, config changes
   - **Removed functionality** — deleted files, removed commands
   - **Infrastructure** — build system, test infrastructure, CI

5. Output a brief summary: "Analyzing N files changed across M commits. Found K documentation files to review."

---

## Step 2: Per-File Documentation Audit

Read each documentation file and cross-reference it against the diff. Use these generic heuristics
(adapt to whatever project you're in — these are not tai-specific):

**README.md:**
- Does it describe all features and capabilities visible in the diff?
- Are install/setup instructions consistent with the changes?
- Are examples, demos, and usage descriptions still valid?
- Are troubleshooting steps still accurate?
- Is the stack/tech-list section (formerly in trace) still accurate?

**docs/architecture.md (§4 code map):**
- Do ASCII diagrams and component descriptions match the current code?
- Are design decisions and "why" explanations still accurate?
- Be conservative — only update things clearly contradicted by the diff. Architecture docs
  describe things unlikely to change frequently.
- Markdown structure uses standard headings and frontmatter for metadata.

**docs/contributing.md — New contributor smoke test:**
- Walk through the setup instructions as if you are a brand new contributor.
- Are the listed commands accurate? Would each step succeed?
- Do test tier descriptions match the current test infrastructure?
- Are workflow descriptions (dev setup, contributor mode, etc.) current?
- Flag anything that would fail or confuse a first-time contributor.

**CLAUDE.md / project instructions:**
- Does the project structure section match the actual file tree?
- Are listed commands and scripts accurate?
- Do build/test instructions match what's in package.json (or equivalent)?
- Are the conventions and testing sections (formerly in trace) still accurate?

**docs/ tree (if exists):**
- Check `docs/architecture.md` — is the architecture description (incl. §4 code map) still accurate after this release?
- Check `docs/matrix.md` — are all REQs from `docs/specs/*.md` still valid? (Read-only — if a
  spec is stale vs. shipped code, FLAG it per the HARD RULE; never edit `docs/specs/`.)
- Markdown docs use frontmatter and standard headings for metadata.
- Run doc validation using the Python validator:

```bash
python3 -c "
from tai.commands.docs import validate_all, find_docs_root
issues = validate_all(find_docs_root())
if issues:
    for path, errs in issues.items():
        for e in errs:
            print(f'ISSUE: {path}: {e}')
else:
    print('All docs valid.')
"
```

- Flag stale docs for update or removal (subject to the HARD RULE — source-layer docs are
  flag-only, never edited here).

**Any other .md files under docs/ (excluding the forbidden source layers):**
- Read the file, determine its purpose and audience.
- Cross-reference against the diff to check if it contradicts anything the file says.

**Any root-level .md files (README.md, CLAUDE.md, etc.):**
- These remain Markdown. Read and audit as before.

**Derived-doc trust marker (auto-fix, every derived doc this skill maintains):**

Every derived doc must advertise that it is derived so a human reading it knows not to
trust it as source. For each derived doc you maintain — `README.md`, `docs/architecture.md`,
`docs/matrix.md`, `docs/changelog.md`, `docs/contributing.md`, `CLAUDE.md` — ensure BOTH of
these are present, and **insert them if missing** during this audit (this is how existing
repos pick up the banner on their next `/docs-update` run):

1. `derived: true` in the YAML frontmatter. (Root `README.md` / `CLAUDE.md` may have no
   frontmatter — if so, leave their structure alone and just ensure the banner line is the
   first line of the file.)
2. The one-line trust banner immediately after the closing `---` of the frontmatter (or as
   the first line if there is no frontmatter):

   ```
   > ⚠️ Derived doc — maintained live by an agent as code changes; may still lag. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.
   ```

This is a factual, mechanical auto-fix — apply it directly, do not ask. **NEVER** add
`derived: true` or this banner to a source-layer doc (`docs/specs/`, `docs/prd.md`,
`docs/decisions/`) — those carry `status:`, not `derived:`, and are off-limits per the HARD
RULE. Do not duplicate the banner if it already exists.

For each file, classify needed updates as:

- **Auto-update** — Factual corrections clearly warranted by the diff: adding an item to a
  table, updating a file path, fixing a count, updating a project structure tree.
- **Ask user** — Narrative changes, section removal, security model changes, large rewrites
  (more than ~10 lines in one section), ambiguous relevance, adding entirely new sections.

---

## Step 2.5: Requirement Status Reconciliation (specs are READ-ONLY here)

**⛔ Per the HARD RULE, this skill MUST NOT edit `docs/specs/`.** Spec status is part of the
doc-first source layer and a human owns it. This step is **flag-only**.

If `docs/specs/` has `.md` files (skip `spec.template.md`):

1. **Read each spec (do not write).** Parse the Behavior rows / requirements — each has an
   R-id (R1…RN) or REQ-id, description, and status (`open`, `in-progress`, `done`, `cut`).

2. **Cross-reference the diff.** For each requirement with status `open` or `in-progress`:
   - Check whether the diff implements it (new files, new functions, schema changes that match).
   - If it appears clearly implemented but the spec still says `open`/`in-progress`, the spec
     is **stale versus shipped code** — that is a doc-first violation.

3. **FLAG, never fix.** Emit a `[CRITICAL]` finding for the human, e.g.:
   `[CRITICAL] docs/specs/space-meetings.md: REQ-MTG-001 appears shipped but status is 'open'.
   Spec is out of date vs code — reconcile via the spec-first flow. (Not auto-fixed.)`

4. Do NOT change spec status cells, frontmatter, or any `docs/specs/` content under any
   circumstance — even if the correct value is obvious. Editing a spec to match already-shipped
   code inverts doc-first order.

A `done` → `open` regression spotted in a spec is likewise flag-only.

---

## Step 3: Apply Auto-Updates

Make all clear, factual updates directly using the Edit tool.

For each file modified, output a one-line summary describing **what specifically changed** — not
just "Updated README.md" but "README.md: added /new-skill to skills table, updated skill count
from 9 to 10."

**Never auto-update:**
- README introduction or project positioning
- `docs/architecture.md` philosophy or design rationale
- Security model descriptions
- Do not remove entire sections from any document

---

## Step 4: Ask About Risky/Questionable Changes

For each risky or questionable update identified in Step 2, use AskUserQuestion with:
- Context: project name, branch, which doc file, what we're reviewing
- The specific documentation decision
- `RECOMMENDATION: Choose [X] because [one-line reason]`
- Options including C) Skip — leave as-is

Apply approved changes immediately after each answer.

---

## Step 5: CHANGELOG Voice Polish

**CRITICAL — NEVER CLOBBER CHANGELOG ENTRIES.**

This step polishes voice. It does NOT rewrite, replace, or regenerate CHANGELOG content.

A real incident occurred where an agent replaced existing CHANGELOG entries when it should have
preserved them. This skill must NEVER do that.

**Rules:**
1. Read the entire `docs/changelog.md` first. Understand what is already there.
2. Only modify wording within existing entries. Never delete, reorder, or replace entries.
3. Never regenerate a CHANGELOG entry from scratch. The entry was written by `/ship` from the
   actual diff and commit history. It is the source of truth. You are polishing prose, not
   rewriting history.
4. If an entry looks wrong or incomplete, use AskUserQuestion — do NOT silently fix it.
5. Use Edit tool with exact `old_string` matches — never use Write to overwrite the changelog file.

**If CHANGELOG (docs/changelog.md) was not modified in this branch:** skip this step.

**If CHANGELOG was modified in this branch**, review the entry for voice:

- **Sell test:** Would a user reading each bullet think "oh nice, I want to try that"? If not,
  rewrite the wording (not the content).
- Lead with what the user can now **do** — not implementation details.
- "You can now..." not "Refactored the..."
- Flag and rewrite any entry that reads like a commit message.
- Internal/contributor changes belong in a separate "### For contributors" subsection.
- Auto-fix minor voice adjustments. Use AskUserQuestion if a rewrite would alter meaning.

---

## Step 6: Cross-Doc Consistency & Discoverability Check

After auditing each file individually, do a cross-doc consistency pass:

1. Does the README's feature/capability list match what CLAUDE.md (or project instructions) describes?
2. Does `docs/architecture.md`'s component list match `docs/contributing.md`'s project structure description?
3. Does CHANGELOG's latest version match the VERSION file?
4. **Discoverability:** Is every documentation file reachable from README.md or CLAUDE.md? If
   `docs/architecture.md` exists but neither README nor CLAUDE.md links to it, flag it. Every doc
   should be discoverable from one of the two entry-point files.
5. Flag any contradictions between documents. Auto-fix clear factual inconsistencies (e.g., a
   version mismatch). Use AskUserQuestion for narrative contradictions.

---

## Step 7: docs/plan/backlog.md Cleanup

This is a second pass that complements `/ship`'s Step 5.5. The backlog uses two sections:
`## Active` and `## Backlog`.

If `docs/plan/backlog.md` doesn't exist, skip this step.

1. **Completed items not yet marked:** Cross-reference the diff against open backlog items. If an
   item is clearly completed by the changes in this branch, mark it complete
   with `**Completed:** vX.Y.Z.W (YYYY-MM-DD)`. Be conservative — only mark items with clear
   evidence in the diff.

2. **Items needing description updates:** If a backlog item references files or components that were
   significantly changed, its description may be stale. Use AskUserQuestion to confirm whether
   the item should be updated, completed, or left as-is.

3. **New deferred work:** Check the diff for `TODO`, `FIXME`, `HACK`, and `XXX` comments. For
   each one that represents meaningful deferred work (not a trivial inline note), use
   AskUserQuestion to ask whether it should be captured in docs/plan/backlog.md.

---

## Step 8: VERSION Bump Question

**CRITICAL — NEVER BUMP VERSION WITHOUT ASKING.**

1. **If VERSION does not exist:** Skip silently.

2. Check if VERSION was already modified on this branch:

```bash
git diff <base>...HEAD -- VERSION
```

3. **If VERSION was NOT bumped:** Use AskUserQuestion:
   - RECOMMENDATION: Choose C (Skip) because docs-only changes rarely warrant a version bump
   - A) Bump PATCH (X.Y.Z+1) — if doc changes ship alongside code changes
   - B) Bump MINOR (X.Y+1.0) — if this is a significant standalone release
   - C) Skip — no version bump needed

4. **If VERSION was already bumped:** Do NOT skip silently. Instead, check whether the bump
   still covers the full scope of changes on this branch:

   a. Read the CHANGELOG entry for the current VERSION. What features does it describe?
   b. Read the full diff (`git diff <base>...HEAD --stat` and `git diff <base>...HEAD --name-only`).
      Are there significant changes (new features, new skills, new commands, major refactors)
      that are NOT mentioned in the CHANGELOG entry for the current version?
   c. **If the CHANGELOG entry covers everything:** Skip — output "VERSION: Already bumped to
      vX.Y.Z, covers all changes."
   d. **If there are significant uncovered changes:** Use AskUserQuestion explaining what the
      current version covers vs what's new, and ask:
      - RECOMMENDATION: Choose A because the new changes warrant their own version
      - A) Bump to next patch (X.Y.Z+1) — give the new changes their own version
      - B) Keep current version — add new changes to the existing CHANGELOG entry
      - C) Skip — leave version as-is, handle later

   The key insight: a VERSION bump set for "feature A" should not silently absorb "feature B"
   if feature B is substantial enough to deserve its own version entry.

---

## Step 9: Commit & Output

**Empty check first:** Run `git status` (never use `-uall`). If no documentation files were
modified by any previous step, output "All documentation is up to date." and exit without
committing.

**Commit:**

1. Stage modified documentation files by name (never `git add -A` or `git add .`).
2. Create a single commit:

```bash
git commit -m "$(cat <<'EOF'
docs: update project documentation for vX.Y.Z.W

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

3. Push to the current branch:

```bash
git push
```

**PR body update (idempotent, race-safe):**

1. Read the existing PR body into a PID-unique tempfile:

```bash
gh pr view --json body -q .body > /tmp/tai-pr-body-$$.md
```

2. If the tempfile already contains a `## Documentation` section, replace that section with the
   updated content. If it does not contain one, append a `## Documentation` section at the end.

3. The Documentation section should include a **doc diff preview** — for each file modified,
   describe what specifically changed (e.g., "README.md: added /docs-update to skills
   table, updated skill count from 9 to 10").

4. Write the updated body back:

```bash
gh pr edit --body-file /tmp/tai-pr-body-$$.md
```

5. Clean up the tempfile:

```bash
rm -f /tmp/tai-pr-body-$$.md
```

6. If `gh pr view` fails (no PR exists): skip with message "No PR found — skipping body update."
7. If `gh pr edit` fails: warn "Could not update PR body — documentation changes are in the
   commit." and continue.

**Structured doc health summary (final output):**

Output a scannable summary showing every documentation file's status:

```
Documentation health:
  README.md                [status] ([details])
  docs/architecture.md     [status] ([details])
  docs/contributing.md     [status] ([details])
  docs/changelog.md        [status] ([details])
  docs/plan/backlog.md     [status] ([details])
  VERSION                  [status] ([details])
```

Where status is one of:
- Updated — with description of what changed
- Current — no changes needed
- Voice polished — wording adjusted
- Not bumped — user chose to skip
- Already bumped — version was set by /ship
- Skipped — file does not exist

---

## Important Rules

- **Read before editing.** Always read the full content of a file before modifying it.
- **Never clobber CHANGELOG.** Polish wording only. Never delete, replace, or regenerate entries.
- **Never bump VERSION silently.** Always ask. Even if already bumped, check whether it covers the full scope of changes.
- **Be explicit about what changed.** Every edit gets a one-line summary.
- **Generic heuristics, not project-specific.** The audit checks work on any repo.
- **Discoverability matters.** Every doc file should be reachable from README or CLAUDE.md.
- **Voice: friendly, user-forward, not obscure.** Write like you're explaining to a smart person
  who hasn't seen the code.

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
