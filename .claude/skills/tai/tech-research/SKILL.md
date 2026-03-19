---
name: tech-research
version: 2.0.0
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
  - AskUserQuestion
---

# Technical Research

Produce research that changes how engineers think about a problem — not a Wikipedia
summary with citations. Output goes directly to the user unless they specify
otherwise (file, Notion, etc.).

## Research Prime Directives

These are non-negotiable. Every research output must satisfy all of them.

1. **Decision over information.** Research exists to make a specific decision easier,
   not to make someone "more informed." If the output doesn't change or confirm a
   decision, it failed.
2. **Adversarial depth.** Every recommendation must survive a red team attack.
   If you can't argue against your own conclusion, you haven't researched enough.
3. **Source triangulation.** No major claim stands on a single source or source type.
   Official docs + community experience + benchmark data = confidence.
4. **Specificity kills shallowness.** Never say "it depends." Say "it depends on X —
   if X is true, do A; if X is false, do B." Never say "performance vs flexibility" —
   say "handles 10k req/s but requires 3x the boilerplate."
5. **Contrarian evidence is mandatory.** Every "use X" must include at least one
   real-world failure story or limitation of X. If you can't find one, state that
   explicitly — it's suspicious.
6. **Recency matters.** Prefer sources from the current year. Flag anything older than
   18 months: `[YYYY data — may be outdated]`. Technology moves fast — a 2-year-old
   benchmark might be meaningless.
7. **Diagrams are not optional.** Any non-trivial concept, architecture, or comparison
   gets an ASCII diagram. If you can't diagram it, you don't understand it well enough.

## Research Thinking Instincts

These are cognitive moves that separate deep research from surface-level summarization.
Internalize them — don't enumerate them in output.

1. **Inversion reflex** — For every "why use X?" also research "why NOT use X?"
   and "what have people regretted about X?" The failure stories are often more
   informative than the success stories.
2. **Second-order effects** — Don't just evaluate the tool. Evaluate what happens
   6 months after adopting it: hiring (can you find devs?), ecosystem (are plugins
   maintained?), upgrade path (are major versions painful?).
3. **Proxy skepticism** — GitHub stars != quality. "Industry standard" != best for your
   case. "Used by Netflix" != appropriate at your scale. Challenge every popularity proxy.
4. **Temporal depth** — Technologies have lifecycles. Is this on the upswing or plateau?
   Check: commit frequency trend, conference talk frequency, job posting mentions.
5. **Boundary conditions** — Every technology has a sweet spot and a breaking point.
   Find both. "Works great up to X, starts struggling at Y, breaks at Z."
6. **Migration cost awareness** — The best technology you can't adopt is worse than the
   good-enough technology you already have. Always factor in switching cost.
7. **Survivorship bias** — Blog posts about "how we scaled with X" don't mention the
   companies that failed with X. Search for the failures too.

## Depth Mode Selection

Before starting research, determine the appropriate depth. If the user doesn't specify,
detect from context and confirm.

### Quick Mode (15-20 min)

**When:** Simple binary decisions, "should I use X?", quick sanity checks.

- 3-5 sources minimum
- Executive summary + recommendation
- Skip triangulation protocol and red team
- Skip interactive checkpoints
- Abbreviated completion summary

### Standard Mode (30-45 min) — DEFAULT

**When:** Library comparisons, architecture decisions, most research requests.

- 8-12 sources minimum
- Full template with all sections
- Triangulation protocol required
- Red team section required
- One checkpoint after initial findings
- Full completion summary

### Deep Mode (1-2 hours)

**When:** High-stakes decisions, unfamiliar domains, "I need to really understand this."

- 15+ sources across multiple rounds of search
- Full template with extended analysis
- Triangulation protocol required (strict — 3+ source types per claim)
- Red team section required (extended — multiple attack angles)
- Checkpoints after initial findings AND after red team
- ASCII diagrams required for all non-trivial concepts
- Failure mode analysis for each option
- Implementation roadmap section added
- Full completion summary

AskUserQuestion to confirm depth when not obvious:

```
Research topic: {topic}
Detected complexity: {Quick/Standard/Deep} based on {reason}.

A) Quick — 3-5 sources, exec summary, recommendation. Best for simple "X or Y?" decisions.
B) Standard — 8-12 sources, full analysis, red team. Best for most research.
C) Deep — 15+ sources, multi-round, failure modes, implementation plan. Best for high-stakes decisions.
```

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
  "production experience", "problems", "regret", and the current year
- **Architecture decision:** search for "{pattern} vs {pattern}", "{pattern} at scale",
  case studies, post-mortems, "{pattern} failure stories"
- **Deep dive:** search for official spec/RFC, reference implementation,
  "{topic} explained", "{topic} internals", "{topic} gotchas"
- **Troubleshooting:** search for the exact error message, GitHub issues,
  Stack Overflow, known CVEs

**Depth-specific search intensity:**
- **Quick:** 1 round of searches, 3-5 queries
- **Standard:** 1-2 rounds, 6-10 queries. Second round targets gaps from first.
- **Deep:** 2-3 rounds, 10-15 queries. Each round targets gaps and contradictions
  found in previous rounds. Specifically search for failure stories, post-mortems,
  and "X years later" retrospectives.

## Multi-Source Triangulation Protocol

**Required in Standard and Deep modes. Skipped in Quick.**

For every major claim or finding, verify across at least 3 different source TYPES:

```
SOURCE TYPE              EXAMPLES                          TRUST LEVEL
─────────────────────────────────────────────────────────────────────────
Official documentation   API docs, specs, RFCs             HIGH (but may lag reality)
Benchmark data           Published benchmarks, repro       HIGH (if methodology shown)
Community experience     GitHub issues, HN/Reddit threads  MEDIUM (anecdotal but real)
Production case study    Blog posts from companies at      MEDIUM-HIGH
                         scale, conference talks
Academic/research        Papers, surveys, formal analysis   HIGH (but may lack practice)
Expert opinion           Core maintainer statements,        MEDIUM (authority != data)
                         recognized expert blog posts
```

For each major claim, note the source types used:

```
CLAIM: "{claim}"
├─ Official docs: {source or "not found"}
├─ Benchmark: {source or "not found"}
└─ Community: {source or "not found"}
CONFIDENCE: {High (3+ types) / Medium (2 types) / Low (1 type)}
```

If a claim relies on only 1 source type, flag it:
`[Single-source-type finding — lower confidence]`

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
3. **Forcing questions (ask yourself, don't skip):**
   - What happens to each candidate in 2 years? Growing or declining?
   - What's the migration cost if we need to switch away?
   - What's the worst production incident reported with each?
   - Who maintains this, and what's their funding model?
4. **Head-to-head analysis** — For each dimension, state which candidate wins and why.
   Include real benchmark numbers where available.
5. **Run triangulation** (Standard/Deep) — Verify key performance and adoption claims.

**STOP (Standard/Deep).** Present initial findings. AskUserQuestion:
"Initial findings lean toward {X}. Before I finalize, anything I should weight more
heavily or any concern I should dig into?"

6. **Recommendation** — Pick one. State the conditions under which you'd pick differently.

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
3. **Forcing questions (ask yourself, don't skip):**
   - What breaks first at 10x scale? At 100x?
   - What's the rollback plan if this choice is wrong?
   - What's the second-order effect on team velocity?
   - What operational burden does each option create?
4. **Evaluate each option** — Pros, cons, risks, effort, operational complexity.
   Reference real-world case studies or post-mortems where available.
5. **Run triangulation** (Standard/Deep) — Verify case study claims.

**STOP (Standard/Deep).** Present initial findings. AskUserQuestion:
"Leaning toward {X}. Key tradeoff is {Y vs Z}. Before I finalize and red-team this,
anything to adjust?"

6. **Decision** — Recommend one. State it as: "We will use X because Y."
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
3. **Forcing questions (ask yourself, don't skip):**
   - What's the key insight that makes this technology work?
   - What's the fundamental tradeoff this design chose?
   - Where does the abstraction leak?
   - What's the most common misunderstanding about this?
4. **How it works** — Walk through the mechanism step by step. Reference the spec/RFC
   or source code where possible.
5. **Tradeoffs and limitations** — What does this design sacrifice? Where does it break?

**STOP (Standard/Deep).** Present core mechanism. AskUserQuestion:
"Does this level of depth match what you need, or should I go deeper on any aspect?"

6. **Practical implications** — What does an engineer need to know to use this correctly?

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
3. **Forcing questions (ask yourself, don't skip):**
   - Is this a known issue with a fix, or genuinely novel?
   - Could this be a version incompatibility rather than a bug?
   - What changed recently in the environment that could cause this?
   - Are there related CVEs or security advisories?
4. **Root cause analysis** — Identify the most likely cause. Rank alternatives by
   likelihood. Reference sources for each hypothesis.
5. **Solution** — Provide the fix. If multiple fixes exist, recommend the safest one.
   Include a verification step ("after applying, you should see X").

---

## Adversarial Red Team

**Required in Standard and Deep modes. Skipped in Quick.**

After completing the main research and forming a recommendation, switch perspective
and attack your own conclusion. This is the single biggest lever for depth.

### Red Team Protocol

1. **Steel-man the alternatives** — For each option you DIDN'T recommend, write the
   strongest possible case FOR it. What would a passionate advocate of that option say
   about your analysis?

2. **Attack the recommendation** — Find and present:
   - The worst production incident or failure story involving your recommended option
   - The strongest technical argument against it
   - The scenario where your recommendation is the WRONG choice
   - The hidden cost or risk you might be underweighting

3. **Survivorship bias check** — Are you only seeing success stories? Search specifically
   for: "{recommendation} problems", "{recommendation} regret", "{recommendation} migration away"

4. **Confidence calibration** — After red-teaming, state your confidence:
   ```
   RECOMMENDATION CONFIDENCE: {High/Medium/Low}
   ├─ High: Red team found no compelling counterarguments
   ├─ Medium: Red team found valid concerns but recommendation still holds
   └─ Low: Red team raised serious doubts — consider the alternative
   ```

5. **If confidence drops to Low**, present both options as viable and ask the user
   to weigh in rather than forcing a recommendation.

**STOP (Deep only).** After red team, present findings. AskUserQuestion:
"My red team found {X}. This {does/doesn't} change my recommendation. Does this
concern you, or should I proceed with the final output?"

## Default Output Structure

Unless the user requests a different format, structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding and recommendation.
   This should be opinionated, not balanced. Take a stance.
2. **Key Findings** — bulleted, each sourced. Separate fact from inference.
3. **Detailed Analysis** — mode-specific sections from templates above
4. **Triangulation Summary** (Standard/Deep) — source type coverage per major claim
5. **Red Team Results** (Standard/Deep) — adversarial findings and confidence calibration
6. **Risks & Caveats** — what could make this research wrong. Be specific:
   not "things might change" but "if {specific event} happens, reconsider because {reason}"
7. **Recommendation** — concrete, actionable, opinionated.
   Include: "Choose differently if: {specific conditions}"
8. **Sources** — numbered list with URLs, dates, and brief descriptions.
   Group by source type (Official / Benchmark / Community / Case Study).

## Quality Gate

Before delivering, read the quality checklist:

```bash
cat "${SKILL_DIR}/references/research-quality-checklist.md" 2>/dev/null || cat ~/.claude/skills/tai-tech-research/references/research-quality-checklist.md 2>/dev/null
```

Verify every item. If any check fails, fix the output before delivering.

## Completion Summary

After delivering research, produce this summary:

```
+====================================================================+
|              TECH RESEARCH — COMPLETION SUMMARY                     |
+====================================================================+
| Topic                | {research topic}                             |
| Mode                 | {Comparison/Architecture/Deep Dive/Troubleshoot}|
| Depth                | {Quick/Standard/Deep}                        |
| Sources cited        | ___ total (___ official, ___ benchmark,       |
|                      |   ___ community, ___ case study)             |
| Triangulation        | ___ claims verified, ___ single-source flags |
| Red Team             | Confidence: {High/Medium/Low}                |
| Recommendation       | {one-line summary}                           |
| Key risk             | {biggest caveat}                             |
+====================================================================+
```

## Research Log

After delivering, log the session:

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
mkdir -p ~/.tai-skills/projects/$_SLUG
```

```bash
echo '{"skill":"tech-research","timestamp":"TIMESTAMP","mode":"MODE","depth":"DEPTH","topic":"TOPIC","sources":N,"confidence":"CONFIDENCE","output":"PATH_OR_INLINE"}' >> ~/.tai-skills/projects/$_SLUG/research-log.jsonl
```

Substitute: TIMESTAMP = ISO 8601 datetime, MODE = mode used (comparison/architecture/
deep-dive/troubleshooting), DEPTH = depth level (quick/standard/deep),
TOPIC = research topic (max 80 chars), N = number of sources cited,
CONFIDENCE = red team confidence (high/medium/low/skipped), PATH_OR_INLINE = output
file path or "inline".

## Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting (what decision this informs,
   what constraints exist, what they've already tried)
2. Do NOT produce generic research — specificity is the whole point
3. If still unclear after clarification, narrow the scope yourself and state
   what you're NOT covering
