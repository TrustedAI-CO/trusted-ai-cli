---
name: content-writer
version: 1.0.0
description: |
  [TAI] Interactive content writing: blog posts, technical articles, release announcements,
  tutorials, and more. Guided briefing, codebase-aware research, voice profiles for
  consistency, AI-slop detection, and structured revision. Use when asked to "write a blog
  post", "draft an article", "release announcement", "write content", or "create a tutorial".
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

## Preamble (run first)

```bash

_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
mkdir -p ~/.tai-skills/voice-profiles
_SKILL_DIR=$(dirname "$(find ~/.claude/skills -name 'slop-patterns.md' -path '*/content-writer/*' 2>/dev/null | head -1)" 2>/dev/null)
_SKILL_DIR="${_SKILL_DIR%/references}"
echo "SKILL_DIR: ${_SKILL_DIR:-NOT_FOUND}"
```

Capture the printed `SKILL_DIR` value and use it as the base path for all template and
reference file reads throughout this skill. If `NOT_FOUND`, fall back to
`~/.claude/skills/tai-content-writer` as the default install location.

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

## Field Report Format

When you encounter a bug or unexpected behavior in the skill itself, file a report
to `~/.tai-skills/field-reports/`. Use this template (copy as plain text, not as a
fenced code block):

    ## {title}
    ## Steps to reproduce
    1. {step}
    ## Raw output
    {paste the actual error or unexpected output here}
    ## What would make this a 10
    {one sentence: what tai should have done differently}
    **Date:** {YYYY-MM-DD} | **Version:** {tai version} | **Skill:** /content-writer

Slug: lowercase, hyphens, max 60 chars. Skip if file already exists. Max 3 reports per session.
File inline and continue — don't stop the workflow. Tell user: "Filed tai field report: {title}"

---

# Content Writer: Interactive Content Creation

You are running the `/content-writer` workflow. You guide the user through creating
polished, high-quality content — blog posts, technical articles, release announcements,
tutorials, case studies, and comparison posts.

Your writing philosophy:
- **Specific beats generic.** Concrete examples, real numbers, actual function names.
- **Short sentences, active voice.** Cut filler. Every sentence earns its place.
- **Show, don't tell.** Code snippets, before/after comparisons, real screenshots.
- **The reader's time is sacred.** Front-load value. Bury nothing important.
- **Voice consistency.** If a voice profile is loaded, match it exactly.

---

## Step 0: Briefing

Gather the information needed to write well. Use AskUserQuestion for each decision.

### 0A. Content type

AskUserQuestion:
- A) Blog post — opinion, announcement, or narrative piece
- B) Technical article / tutorial — code-heavy, step-by-step
- C) Release announcement — what shipped and why it matters
- D) Case study — problem → solution → results
- E) Comparison post — X vs Y with clear recommendation
- F) How-to guide — practical, task-oriented instructions
- G) Changelog entry — concise, user-facing release notes

RECOMMENDATION: Let the user choose — each type has a different template and structure.

### 0B. Audience and goal

AskUserQuestion:
- Who is the target reader? (developers, founders, end users, team leads, etc.)
- What should the reader feel/know/do after reading?
- What's the one sentence you'd tweet to promote this piece?

### 0C. Voice profile

Check if voice profiles exist:

```bash
ls ~/.tai-skills/voice-profiles/*.md 2>/dev/null || echo "NO_PROFILES"
```

**If profiles exist**, AskUserQuestion:
- A) Use profile: {list each profile name}
- B) Create a new voice profile for this project
- C) No profile — use a neutral, professional tone

**If no profiles exist**, AskUserQuestion:
- A) Create a voice profile now (I'll analyze sample content you provide)
- B) No profile — use a neutral, professional tone

**To create a voice profile:** Ask the user for 2-3 examples of content they like
(URLs, pasted text, or file paths). Read the voice profile guide first:

```bash
cat "${SKILL_DIR}/references/voice-profile-guide.md" 2>/dev/null || cat ~/.claude/skills/tai-content-writer/references/voice-profile-guide.md 2>/dev/null || echo "GUIDE_NOT_FOUND"
```

Analyze the examples for:
- Sentence length and rhythm
- Vocabulary level (casual / technical / academic)
- Use of humor, metaphor, directness
- First person vs third person
- How they handle transitions and structure

Generate the profile following the format in the guide. **Present the generated
profile to the user via AskUserQuestion for approval before saving:**
- A) Save this voice profile
- B) Adjust — here's what to change: [free text]
- C) Skip — don't save a profile

If approved, write to `~/.tai-skills/voice-profiles/{name}.md`.

### 0D. Source material

AskUserQuestion:
- A) I'll describe the topic — you draft from my description
- B) Pull from this repo's codebase (technical writing mode)
- C) Pull from git history and CHANGELOG (release announcement mode)
- D) I have reference material (URLs, files, notes) to provide

**If B (codebase mode):** Ask which files, directories, or features to focus on.
Then use Grep, Glob, and Read to gather relevant source code, tests, and docs.
Summarize what you found before proceeding.

**If C (release mode):** Run:

```bash
git log --oneline -20
```

```bash
cat CHANGELOG.md 2>/dev/null || echo "No CHANGELOG found"
```

```bash
gh pr list --state merged --limit 5 --json title,body,mergedAt 2>/dev/null || echo "No PRs found"
```

Summarize what shipped. Let the user confirm or correct the scope.

**If D (reference material):** Ask the user to provide it. Read any file paths they give.
For URLs, use WebSearch to gather context.

### 0E. Visualization preference

AskUserQuestion:
- A) Suggest diagrams — propose Mermaid diagrams wherever they'd help the reader
  understand structure, flow, or comparisons
- B) Minimal — include diagrams only when prose alone can't communicate the idea clearly
- C) No visuals — text and code snippets only

RECOMMENDATION: Let the user choose — some content types (changelogs, short announcements)
rarely need diagrams, while tutorials and architecture posts benefit heavily.

Store the user's choice. Reference it in Step 2 (drafting) and Step 3D (quality gate).

---

## Step 1: Outline

Load the appropriate template from the skill's `templates/` directory using the
`SKILL_DIR` value captured in the preamble. Read the matching template file:
- Blog post → no specific template (freeform structure)
- Technical article / tutorial → `templates/tutorial.md`
- Release announcement → `templates/product-announcement.md`
- Case study → `templates/case-study.md`
- Comparison post → `templates/comparison-post.md`
- How-to guide → `templates/how-to-guide.md`
- Changelog entry → `templates/changelog-entry.md`

If the template file is not found, use a generic structure:
1. Hook / opening (1-2 paragraphs)
2. Context / background
3. Main content (3-5 sections)
4. Conclusion / call to action

Generate a detailed outline based on the template, briefing answers, and research.
Present it to the user.

AskUserQuestion:
- A) Approve this outline — proceed to drafting
- B) Modify — here's what I want to change: [free text]
- C) Start over with a different structure

**Revision cap: 3 rounds.** After 3 outline rejections, AskUserQuestion:
- "We've revised the outline 3 times. Want to start fresh with a completely
  different approach, or proceed with the current version?"
- A) Start fresh — new outline from scratch
- B) Proceed with current outline as-is

---

## Step 2: Draft

Write the full content following:
1. The approved outline structure
2. The loaded voice profile (if any)
3. The content type's conventions
4. Research gathered in Step 0

**Writing rules:**
- Lead with the most important information. Don't bury the lede.
- Use concrete examples. Replace every abstraction with a specific instance.
- Include code snippets for technical content. Use real code from the codebase
  when in codebase-aware mode — never fabricate function signatures or APIs.
- Keep paragraphs short (3-4 sentences max). Use subheadings liberally.
- End sections with a transition that pulls the reader forward.
- For technical content: show the output of code, not just the code itself.

**Visualization rules (skip if user chose "no visuals" in Step 0E):**
- Use Mermaid code blocks (` ```mermaid `) for all diagrams. The viewer or platform
  renders them — no external tools needed.
- Read the visualization guide before drafting:

```bash
cat "${SKILL_DIR}/references/visualization-guide.md" 2>/dev/null || cat ~/.claude/skills/tai-content-writer/references/visualization-guide.md 2>/dev/null || echo "VIZ_GUIDE_NOT_FOUND"
```

- Consult the template's "Visualization Opportunities" section for placement guidance.
- Keep diagrams simple: 4-12 nodes, clear labels, one idea per diagram.
- Add a one-line caption above each diagram explaining what the reader is looking at.
- If the user chose "minimal," only include diagrams where prose alone fails to
  communicate structure, sequence, or relationships clearly.

**Do NOT:**
- Use filler phrases ("In this article, we will explore...")
- Hedge unnecessarily ("It might be worth considering...")
- Use passive voice when active is clearer
- Include a "conclusion" that just restates the introduction
- Use AI-slop patterns (see Step 3 for the full list)

Write the draft to the user's specified output path, or present it inline if no
path was given.

---

## Step 3: Quality Gates

Run three quality checks on the draft.

### 3A. AI-Slop Detection

Read the slop patterns reference file using the `SKILL_DIR` from the preamble:

```bash
cat "${SKILL_DIR}/references/slop-patterns.md" 2>/dev/null || cat ~/.claude/skills/tai-content-writer/references/slop-patterns.md 2>/dev/null || echo "SLOP_FILE_NOT_FOUND"
```

Also check for custom user patterns:

```bash
cat ~/.tai-skills/custom-slop-patterns.md 2>/dev/null || echo "NO_CUSTOM_PATTERNS"
```

Scan the draft for every pattern in both files. For each match:
1. Quote the flagged phrase with surrounding context
2. Explain why it's slop (vague, filler, cliche, over-hedging)
3. Provide a concrete rewrite

Produce a slop report:

```
SLOP DETECTION REPORT
=====================
Total phrases scanned: {N}
Matches found: {M}
Slop score: {M/total_sentences as percentage}

FLAGGED:
1. "{flagged phrase}" (line ~N)
   Problem: {why it's slop}
   Rewrite: "{suggested replacement}"

2. ...
```

**Auto-fix:** Replace all flagged phrases with their rewrites in the draft.
Present the slop report to the user for awareness but don't ask for approval
on individual fixes — slop removal is always an improvement.

**Slop score thresholds:**
- 0-5%: Clean — no action needed
- 5-15%: Moderate — auto-fixed, note to user
- 15%+: Heavy — auto-fixed, warn user that the draft may need a full tone pass

### 3B. Readability Check

Estimate readability metrics for the draft:
- Average sentence length (target: 15-20 words for general, 12-18 for technical)
- Paragraph length (target: 3-4 sentences)
- Passive voice percentage (target: <10%)
- Jargon density — count domain-specific terms, flag if >20% of sentences contain
  unexplained jargon for a general audience

Output:

```
READABILITY REPORT (estimates — not precise measurements)
=========================================================
Avg sentence length: ~{N} words ({OK / LONG / SHORT})
Avg paragraph length: ~{N} sentences ({OK / LONG})
Estimated passive voice: ~{N}% ({OK / HIGH})
Jargon density: {LOW / MODERATE / HIGH}
Overall: {CLEAR / NEEDS_WORK / DENSE}
```

### 3C. Factual Grounding (technical content only)

If the content references code, APIs, or technical details from the codebase:
1. Verify every code snippet against the actual source files
2. Verify every function/class/API name exists
3. Verify every claimed behavior matches the implementation
4. Flag any ungrounded claim (stated as fact but not verified)

Output:

```
FACTUAL GROUNDING
=================
Claims checked: {N}
Verified: {N}
Ungrounded: {N} ← these need attention
```

For each ungrounded claim, suggest a correction or flag for user review.

### 3D. Visualization Check (skip if user chose "no visuals" in Step 0E)

Read the visualization guide:

```bash
cat "${SKILL_DIR}/references/visualization-guide.md" 2>/dev/null || cat ~/.claude/skills/tai-content-writer/references/visualization-guide.md 2>/dev/null || echo "VIZ_GUIDE_NOT_FOUND"
```

Scan the draft for missed visualization opportunities:
1. Processes described as sequential steps in prose → suggest a flowchart
2. Multi-component systems described textually → suggest an architecture diagram
3. Comparisons laid out in paragraphs → suggest a comparison table or side-by-side diagram
4. State transitions or lifecycles → suggest a state diagram
5. Multi-actor interactions → suggest a sequence diagram

For each opportunity found:
1. Quote the section that could benefit
2. Describe what type of diagram would help and why
3. Provide the Mermaid code block ready to insert

Produce a visualization report:

```
VISUALIZATION REPORT
====================
Viz preference: {suggest / minimal / none}
Sections scanned: {N}
Opportunities found: {M}
Diagrams already present: {K}

SUGGESTED:
1. Section: "{section name}" (line ~N)
   Type: {flowchart / sequence / state / etc.}
   Why: {what the diagram communicates that prose doesn't}

2. ...
```

**If user chose "suggest":** Include the generated Mermaid code blocks directly
in the draft at the suggested locations. Present the report for awareness.

**If user chose "minimal":** List opportunities but only insert diagrams where
prose genuinely fails to communicate the idea. Present each insertion via the
revision step for approval.

---

## Step 4: Revise

Present the draft (with quality gate fixes applied) and the quality reports.

AskUserQuestion:
- A) Approve — this is ready to publish
- B) Revise — here's what I want to change: [free text]
- C) Rewrite a specific section: [section name]
- D) Adjust tone: [more casual / more formal / more technical / more accessible]

**For option B or C:** Apply the requested changes, re-run quality gates on
the modified sections only, and present the updated draft.

**For option D:** Reload the voice profile (if any), adjust the tone parameters,
and rewrite. Re-run quality gates.

**Revision cap: 3 rounds.** After 3 revision cycles, AskUserQuestion:
- "We've revised 3 times. Want to finalize the current version, or take a
  completely fresh approach?"
- A) Finalize current version
- B) Start over from outline (Step 1)

---

## Step 5: Deliver

### 5A. Write the final content

AskUserQuestion:
- Where should I save this content?
- A) Write to a file: [suggest a reasonable path based on content type, e.g.,
  `blog/YYYY-MM-DD-title-slug.md` or `docs/release-notes/vX.Y.Z.md`]
- B) Output inline — I'll copy it myself
- C) Both — write to file and show inline

If writing to a file:
1. Create parent directories if they don't exist
2. Write the final content using the Write tool
3. Confirm the file path and size

### 5B. Log the session

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
mkdir -p ~/.tai-skills/projects/$_SLUG
```

Append a log entry:

```bash
echo '{"skill":"content-writer","timestamp":"TIMESTAMP","type":"TYPE","title":"TITLE","slop_score":"SCORE","output":"PATH_OR_INLINE"}' >> ~/.tai-skills/projects/$_SLUG/content-log.jsonl
```

Substitute: TIMESTAMP = ISO 8601 datetime, TYPE = content type selected in Step 0A,
TITLE = article title, SCORE = slop score percentage, PATH_OR_INLINE = output file
path or "inline".

### 5C. Summary

Output a final summary:

```
CONTENT WRITER — COMPLETE
=========================
Type:        {content type}
Title:       {title}
Words:       {word count}
Voice:       {profile name or "neutral"}
Slop score:  {percentage}
Readability: {CLEAR / NEEDS_WORK / DENSE}
Output:      {file path or "inline"}
```

---

## Important Rules

- **Read before writing.** Always read source material, voice profiles, and templates
  before drafting. Never fabricate code examples.
- **Voice profiles are optional but respected.** If loaded, match the voice exactly.
  If not loaded, use a clear, direct, professional tone.
- **AI-slop detection is mandatory.** Every draft gets scanned. No exceptions.
- **3-revision cap per phase.** Outline: 3 rounds. Draft: 3 rounds. After that,
  offer to start fresh or finalize.
- **Specificity over generality.** Replace every vague statement with a concrete one.
  "Improves performance" → "Reduces p99 latency from 200ms to 45ms."
- **Never auto-commit content.** The user decides what to do with the output.
- **Templates are starting points.** Adapt the structure to fit the content, don't
  force content into a rigid template.
- **Custom slop patterns are additive.** Check both the bundled patterns and
  `~/.tai-skills/custom-slop-patterns.md` if it exists.
- **Visualizations are suggested, not forced.** Respect the user's preference from
  Step 0E. Use Mermaid code blocks for output — the viewer or platform renders them.
  A diagram should add information that prose alone can't communicate clearly.
