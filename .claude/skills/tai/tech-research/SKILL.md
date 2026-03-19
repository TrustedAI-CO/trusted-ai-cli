---
name: tech-research
version: 1.0.0
description: |
  [TAI] Technical research: library/tool comparison, architecture decisions,
  technology deep dives, and troubleshooting. Uses web search + optional
  context7/chub for real-time sourced, decision-oriented output.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
---

# Technical Research

Produce research that supports engineering decisions, not research theater.
Output goes directly to the user unless they specify otherwise (file, Notion, etc.).

## When to Activate

- Comparing libraries, frameworks, or tools for a specific use case
- Making an architecture or design decision (build vs buy, monolith vs micro, etc.)
- Understanding how a protocol, algorithm, or system works in depth
- Debugging a weird error or unexpected behavior with no obvious fix

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
which chub >/dev/null 2>&1 && echo "CHUB: available" || echo "CHUB: unavailable"
_SKILL_DIR=$(dirname "$(find ~/.claude/skills -name 'research-quality-checklist.md' -path '*/tech-research/*' 2>/dev/null | head -1)" 2>/dev/null)
_SKILL_DIR="${_SKILL_DIR%/references}"
echo "SKILL_DIR: ${_SKILL_DIR:-NOT_FOUND}"
```

Capture `CHUB` status and `SKILL_DIR`. If `SKILL_DIR` is `NOT_FOUND`, fall back to
`~/.claude/skills/tai-tech-research`.

## Research Standards

1. **Every important claim needs a source.** Use `[Source Name, Date]` inline.
   Prefer official docs, GitHub repos, RFCs, and benchmarks over blog posts.
2. **Prefer recent data.** Flag anything older than 18 months: `[YYYY data — may be outdated]`.
3. **Include contrarian evidence.** Every "use X" recommendation needs at least one
   reason NOT to use X.
4. **Separate fact, inference, and recommendation.** Label each clearly.
5. **Translate findings into a decision.** End with a concrete recommendation, not a summary.

## Documentation Lookup (before web search)

For library/tool research, attempt to pull official documentation first.
These steps are **optional** — skip gracefully if tools are unavailable.

### context7 (MCP, if available)

Try `resolve-library-id` for each library being researched. If it returns a valid ID,
call `query-docs` with the user's specific question. If either call fails, skip silently
and proceed to web search.

### chub CLI (if installed)

Only if the preamble printed `CHUB: available`:

```bash
chub search "$(echo "$TOPIC" | tr -dc 'a-zA-Z0-9 .-')"
```

If results are found, fetch relevant docs with `chub get`. If no results or chub
errors, skip and proceed to web search.

**Important:** Always sanitize the topic before passing to chub — strip shell
metacharacters as shown above.

## Web Search (mandatory)

Before drafting any output, search for real-time data:

1. **Use WebSearch** to find current data: release notes, benchmarks, GitHub issues,
   API changelogs, conference talks, RFCs.
2. **Use WebFetch** to pull specific pages: official docs, benchmark results,
   GitHub discussions, Stack Overflow answers.
3. **Cross-reference** at least 2-3 sources for any critical claim.
4. **If search returns nothing useful**, state: "Limited real-time data available for X —
   the following is based on training data as of [cutoff]."

Search strategy per mode:
- **Library comparison:** search each candidate + "benchmark", "vs", "migration",
  "production experience", and the current year
- **Architecture decision:** search for "{pattern} vs {pattern}", "{pattern} at scale",
  case studies, post-mortems
- **Deep dive:** search for official spec/RFC, reference implementation,
  "{topic} explained", "{topic} internals"
- **Troubleshooting:** search for the exact error message, GitHub issues,
  Stack Overflow, known CVEs

## Research Modes

Detect the research type from the user's prompt. If ambiguous, ask which mode to use.

---

### Mode 1: Library/Tool Comparison

**Goal:** Compare 2-5 candidates and recommend one for the user's specific use case.

Read the comparison matrix template:

```bash
cat "${SKILL_DIR}/templates/comparison-matrix.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/templates/comparison-matrix.md 2>/dev/null
```

**Steps:**

1. **Clarify use case** — Ask what matters most: performance, DX, ecosystem,
   maintenance burden, team familiarity. If the user lists >5 candidates, ask to narrow.
2. **Build the comparison matrix** — For each candidate, research: maturity, performance
   benchmarks, ecosystem (plugins/integrations), maintenance health (commit frequency,
   open issues, bus factor), learning curve, licensing, and production adoption signals.
3. **Head-to-head analysis** — For each dimension, state which candidate wins and why.
   Include real benchmark numbers where available.
4. **Recommendation** — Pick one. State the conditions under which you'd pick differently.

---

### Mode 2: Architecture Decision

**Goal:** Evaluate architectural approaches and recommend one, in ADR format.

Read the ADR template:

```bash
cat "${SKILL_DIR}/templates/architecture-decision-record.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/templates/architecture-decision-record.md 2>/dev/null
```

**Steps:**

1. **Frame the decision** — What exactly needs to be decided? What constraints exist?
2. **Identify options** (2-4) — Name each approach. Include "do nothing" if applicable.
3. **Evaluate each option** — Pros, cons, risks, effort, operational complexity.
   Reference real-world case studies or post-mortems where available.
4. **Decision** — Recommend one. State it as: "We will use X because Y."
   Include the conditions that would trigger revisiting this decision.

---

### Mode 3: Technology Deep Dive

**Goal:** Build a thorough mental model of how a technology works internally.

Read the deep dive template:

```bash
cat "${SKILL_DIR}/templates/deep-dive-summary.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/templates/deep-dive-summary.md 2>/dev/null
```

**Steps:**

1. **Scope the dive** — What specific aspect? (If too broad, ask the user to narrow.)
2. **Core concepts** — Define the key primitives and how they relate. Use ASCII diagrams.
3. **How it works** — Walk through the mechanism step by step. Reference the spec/RFC
   or source code where possible.
4. **Tradeoffs and limitations** — What does this design sacrifice? Where does it break?
5. **Practical implications** — What does an engineer need to know to use this correctly?

---

### Mode 4: Troubleshooting Research

**Goal:** Find the root cause and solution for a technical problem.

Read the troubleshooting template:

```bash
cat "${SKILL_DIR}/templates/troubleshooting-report.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/templates/troubleshooting-report.md 2>/dev/null
```

**Steps:**

1. **Reproduce the context** — Ask for: error message, environment (OS, runtime version,
   dependencies), what changed recently, and whether it's intermittent or consistent.
2. **Search for known issues** — GitHub issues, CVEs, Stack Overflow, release notes
   for breaking changes. Search the exact error message first.
3. **Root cause analysis** — Identify the most likely cause. Rank alternatives by
   likelihood. Reference sources for each hypothesis.
4. **Solution** — Provide the fix. If multiple fixes exist, recommend the safest one.
   Include a verification step ("after applying, you should see X").

---

## Default Output Structure

Unless the user requests a different format, structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding and recommendation
2. **Key Findings** — bulleted, each sourced
3. **Detailed Analysis** — mode-specific sections above
4. **Risks & Caveats** — what could make this research wrong
5. **Recommendation** — concrete, actionable, opinionated
6. **Sources** — numbered list with URLs, dates, and brief descriptions

## Quality Gate

Before delivering, read the quality checklist:

```bash
cat "${SKILL_DIR}/references/research-quality-checklist.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/references/research-quality-checklist.md 2>/dev/null
```

Verify every item. If any check fails, fix the output before delivering.

## Research Log

After delivering, log the session:

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
mkdir -p ~/.tai-skills/projects/$_SLUG
```

```bash
echo '{"skill":"tech-research","timestamp":"TIMESTAMP","mode":"MODE","topic":"TOPIC","sources":N,"output":"PATH_OR_INLINE"}' >> ~/.tai-skills/projects/$_SLUG/research-log.jsonl
```

Substitute: TIMESTAMP = ISO 8601 datetime, MODE = mode used (comparison/architecture/
deep-dive/troubleshooting), TOPIC = research topic (max 80 chars), N = number of
sources cited, PATH_OR_INLINE = output file path or "inline".

## Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting (what decision this informs,
   what constraints exist, what they've already tried)
2. Do NOT produce generic research — specificity is the whole point
