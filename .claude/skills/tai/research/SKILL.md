---
name: research
version: 1.0.0
description: |
  [TAI] Decision-oriented research in three modes — tech, market, or design. Pass a
  domain argument (tech | market | design); if omitted, infer it from the request.
  TECH: library/tool comparison, architecture decisions, technology deep dives,
  troubleshooting (web search + optional context7/chub). MARKET: competitive analysis,
  market sizing (TAM/SAM/SOM), startup idea validation. DESIGN: competitor UI analysis,
  design trend exploration, UX pattern research, design system research (web + screenshots).
  Uses real-time web search and applies mode-specific frameworks for sourced, opinionated
  output. Use when asked to "research", "research tech", "compare libraries",
  "architecture decision", "deep dive", "troubleshoot", "research the market",
  "competitive analysis", "market sizing", "TAM SAM SOM", "validate this idea",
  "research design", "find design inspiration", "analyze competitor UIs", or
  "explore UX patterns".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# Research

Produce research that changes how the user thinks about a problem and makes a specific
decision easier — not a Wikipedia summary, a Pinterest board, or research theater.
Output goes directly to the user unless they specify otherwise (file, Notion, etc.).

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

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
echo "SLUG: $_SLUG"
```

Each mode runs additional preamble steps below (CHUB check for tech, prior-research
check for market). Capture `BRANCH` and `SLUG` for logging.

## Mode Selection

This skill operates in three modes that share method but differ in lens, sources, and
frameworks. Pick the mode from the user's argument: `tech` | `market` | `design`.

If no argument is given, infer the mode from the request:
- **tech** — libraries, frameworks, tools, architecture, protocols, algorithms,
  build-vs-buy, errors/bugs, performance, "should I use X?", "X vs Y" (engineering),
  "how does X work internally", "debug this error".
- **market** — competitors, market size, TAM/SAM/SOM, funding, pricing, customer
  segments, "validate this idea", "is this worth building", investor research,
  go-to-market, business viability.
- **design** — UI, UX, visual language, design trends, interaction patterns, design
  systems, "find design inspiration", "analyze competitor UIs", "what do others do
  for this screen", typography/color/layout decisions.

If the request genuinely spans modes (e.g., "research this startup idea and its tech
stack"), ask which lens to lead with, or run the most relevant mode first and offer the
others. If still ambiguous, AskUserQuestion to confirm the mode before starting.

Once the mode is chosen, follow ONLY that mode's section below. Each mode is
self-contained: it has its own prime directives, thinking instincts, depth levels,
sub-modes, web-search strategy, output structure, quality gate, completion summary,
and logging.

---

# Mode: Tech

Technical research: library/tool comparison, architecture decisions, technology deep
dives, and troubleshooting. Produce research that changes how engineers think about a
problem — not a Wikipedia summary with citations.

## Tech — Research Prime Directives

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

## Tech — Research Thinking Instincts

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

## Tech — Depth Mode Selection

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

## Tech — When to Activate

- Comparing libraries, frameworks, or tools for a specific use case
- Making an architecture or design decision (build vs buy, monolith vs micro, etc.)
- Understanding how a protocol, algorithm, or system works in depth
- Debugging a weird error or unexpected behavior with no obvious fix

## Tech — Mode Preamble

```bash
which chub >/dev/null 2>&1 && echo "CHUB: available" || echo "CHUB: unavailable"
_SKILL_DIR=$(dirname "$(find ~/.claude/skills -path '*/research/tech-references/research-quality-checklist.md' 2>/dev/null | head -1)" 2>/dev/null)
_SKILL_DIR="${_SKILL_DIR%/tech-references}"
echo "SKILL_DIR: ${_SKILL_DIR:-NOT_FOUND}"
```

Capture `CHUB` status and `SKILL_DIR`. If `SKILL_DIR` is `NOT_FOUND`, fall back to
`~/.claude/skills/tai/research` (templates live under `tech-templates/` and
`tech-references/`).

## Tech — Documentation Lookup (before web search)

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

## Tech — Web Search (mandatory)

Before drafting any output, search for real-time data:

1. **Use WebSearch** to find current data: release notes, benchmarks, GitHub issues,
   API changelogs, conference talks, RFCs.
2. **Use WebFetch** to pull specific pages: official docs, benchmark results,
   GitHub discussions, Stack Overflow answers.
3. **Cross-reference** at least 2-3 sources for any critical claim.
4. **If search returns nothing useful**, state: "Limited real-time data available for X —
   the following is based on training data as of [cutoff]."

Search strategy per sub-mode:
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

## Tech — Multi-Source Triangulation Protocol

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

## Tech — Sub-Modes

Detect the research type from the user's prompt. If ambiguous, ask which sub-mode to use.

---

### Tech Sub-Mode 1: Library/Tool Comparison

**Goal:** Compare 2-5 candidates and recommend one for the user's specific use case.

Read the comparison matrix template:

```bash
cat "${SKILL_DIR}/tech-templates/comparison-matrix.md" 2>/dev/null || cat ~/.claude/skills/tai/research/tech-templates/comparison-matrix.md 2>/dev/null
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

### Tech Sub-Mode 2: Architecture Decision

**Goal:** Evaluate architectural approaches and recommend one, in ADR format.

Read the ADR template:

```bash
cat "${SKILL_DIR}/tech-templates/architecture-decision-record.md" 2>/dev/null || cat ~/.claude/skills/tai/research/tech-templates/architecture-decision-record.md 2>/dev/null
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

### Tech Sub-Mode 3: Technology Deep Dive

**Goal:** Build a thorough mental model of how a technology works internally.

Read the deep dive template:

```bash
cat "${SKILL_DIR}/tech-templates/deep-dive-summary.md" 2>/dev/null || cat ~/.claude/skills/tai/research/tech-templates/deep-dive-summary.md 2>/dev/null
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

### Tech Sub-Mode 4: Troubleshooting Research

**Goal:** Find the root cause and solution for a technical problem.

Read the troubleshooting template:

```bash
cat "${SKILL_DIR}/tech-templates/troubleshooting-report.md" 2>/dev/null || cat ~/.claude/skills/tai/research/tech-templates/troubleshooting-report.md 2>/dev/null
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

## Tech — Adversarial Red Team

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

## Tech — Default Output Structure

Unless the user requests a different format, structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding and recommendation.
   This should be opinionated, not balanced. Take a stance.
2. **Key Findings** — bulleted, each sourced. Separate fact from inference.
3. **Detailed Analysis** — sub-mode-specific sections from templates above
4. **Triangulation Summary** (Standard/Deep) — source type coverage per major claim
5. **Red Team Results** (Standard/Deep) — adversarial findings and confidence calibration
6. **Risks & Caveats** — what could make this research wrong. Be specific:
   not "things might change" but "if {specific event} happens, reconsider because {reason}"
7. **Recommendation** — concrete, actionable, opinionated.
   Include: "Choose differently if: {specific conditions}"
8. **Sources** — numbered list with URLs, dates, and brief descriptions.
   Group by source type (Official / Benchmark / Community / Case Study).

## Tech — Quality Gate

Before delivering, read the quality checklist:

```bash
cat "${SKILL_DIR}/tech-references/research-quality-checklist.md" 2>/dev/null || cat ~/.claude/skills/tai/research/tech-references/research-quality-checklist.md 2>/dev/null
```

Verify every item. If any check fails, fix the output before delivering.

## Tech — Completion Summary

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

## Tech — Research Log

After delivering, log the session:

```bash
mkdir -p ~/.tai-skills/projects/$_SLUG
```

```bash
echo '{"skill":"tech-research","timestamp":"TIMESTAMP","mode":"MODE","depth":"DEPTH","topic":"TOPIC","sources":N,"confidence":"CONFIDENCE","output":"PATH_OR_INLINE"}' >> ~/.tai-skills/projects/$_SLUG/research-log.jsonl
```

Substitute: TIMESTAMP = ISO 8601 datetime, MODE = sub-mode used (comparison/architecture/
deep-dive/troubleshooting), DEPTH = depth level (quick/standard/deep),
TOPIC = research topic (max 80 chars), N = number of sources cited,
CONFIDENCE = red team confidence (high/medium/low/skipped), PATH_OR_INLINE = output
file path or "inline".

## Tech — Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting (what decision this informs,
   what constraints exist, what they've already tried)
2. Do NOT produce generic research — specificity is the whole point
3. If still unclear after clarification, narrow the scope yourself and state
   what you're NOT covering

---

# Mode: Market

Startup market research: competitive analysis, market sizing (TAM/SAM/SOM), and idea
validation. Produce research that supports decisions, not research theater.

## Market — Mode Preamble

```bash
_SKILL_DIR=$(dirname "$(find ~/.claude/skills -path '*/research/market-references/research-quality-checklist.md' 2>/dev/null | head -1)" 2>/dev/null)
_SKILL_DIR="${_SKILL_DIR%/market-references}"
echo "SKILL_DIR: ${_SKILL_DIR:-NOT_FOUND}"
ls ~/.tai-skills/projects/$_SLUG/market-intel/ 2>/dev/null && echo "PRIOR_RESEARCH: found" || echo "PRIOR_RESEARCH: none"
```

Capture `SKILL_DIR` and `PRIOR_RESEARCH` status. If `SKILL_DIR` is `NOT_FOUND`,
fall back to `~/.claude/skills/tai/research` (templates live under `market-templates/`
and `market-references/`).

If `PRIOR_RESEARCH: found`, list the files and ask the user:
"I found existing market research from prior sessions. Want me to build on it or start fresh?"

## Market — When to Activate

- Analyzing competitors in a market or category
- Estimating market size (TAM/SAM/SOM)
- Validating a startup idea before building
- Preparing research for investors, strategy, or product decisions

## Market — Thinking Frameworks

These are not checklist items. They are thinking instincts — the cognitive moves that
separate insightful market analysis from surface-level research. Let them shape your
analysis throughout. Don't enumerate them; internalize them.

1. **Jobs-to-be-Done lens** — Never ask "what does the competitor do?" Ask "what job
   does the customer hire this product for?" The job reveals the real competitive
   landscape — which is always wider than the product category suggests. A spreadsheet
   and a project management tool compete for the same "organize my work" job.

2. **Porter's structural analysis** — For every market, instinctively assess the five
   forces: buyer power, supplier power, substitutes, new entrants, rivalry. Don't list
   them mechanically — let them shape your judgment about market attractiveness. A market
   with high buyer power and low switching costs is structurally unattractive regardless
   of size.

3. **Inversion reflex** — For every bullish claim, immediately ask: "What would make
   this market shrink?" "What would make customers stop paying?" "What would make this
   company fail?" The bear case must be genuine, not a strawman. If you can't construct
   a strong bear case, you haven't understood the market deeply enough.

4. **Timing obsession** — "Why now?" is the most important question in market research.
   Every interesting market has a timing story: an enabling technology, a regulatory
   change, a behavior shift, a cost curve crossing a threshold. If you can't articulate
   the timing story, the market thesis is incomplete.

5. **Moat classification** — Instinctively categorize competitive advantages: network
   effects (demand-side scale), switching costs (lock-in), economies of scale
   (supply-side), data advantages (gets better with use), brand/trust (earned over time),
   regulatory capture (licenses, compliance). Most startups have NO moat at launch —
   the question is whether the business model creates one over time.

6. **Blue Ocean / Red Ocean awareness** — Is this a crowded market with established
   players fighting for share (red ocean), or is there an opportunity to create a new
   market category (blue ocean)? Most founders think they're in a blue ocean when they're
   actually in a red one with poor positioning. Challenge this honestly.

7. **Proxy skepticism** — Market size numbers, growth rates, and user counts are proxies
   for reality. Always ask: "What is this number actually measuring? Is the methodology
   sound? Would a different methodology give a different answer?" TAM numbers from analyst
   reports are especially prone to definitional arbitrage.

8. **Willingness-to-pay test** — "People want this" and "people will pay for this" are
   different claims. Search for evidence of actual payment behavior: funded competitors
   (someone is paying), pricing pages with real prices (not "contact us"), reviews
   mentioning price (signals price sensitivity). Free tools with no paid competitors
   are a red flag, not a blue ocean.

9. **Distribution instinct** — The best product doesn't win; the best-distributed
   product wins. For every market, ask: how do customers find and buy solutions today?
   Is there a distribution advantage available? Underestimating distribution cost is
   the #1 startup killer after building something nobody wants.

10. **Second-order thinking** — If this market grows 10x, what happens next? Does the
    growth attract incumbents (Google, Microsoft) who can replicate the product in 6
    months? Does success create regulatory scrutiny? Does scale change the unit
    economics? Think two moves ahead.

## Market — Research Standards

1. **Every important claim needs a source.** Use `[Source Name, Date]` inline.
   Prefer official docs, analyst reports, and financial data over blog posts.
2. **Prefer recent data.** Flag anything older than 18 months: `[YYYY data — may be outdated]`.
3. **Include contrarian evidence.** Every bullish finding needs at least one genuine
   bearish counterpoint. Apply the inversion reflex.
4. **Separate fact, inference, and recommendation.** Label each clearly.
5. **Translate findings into a decision.** End with a concrete recommendation, not a summary.
6. **Specificity over generality.** Never write "large market" — write "$4.2B [Gartner, 2025]."
   Never write "strong growth" — write "24% CAGR [Statista, 2025]."

## Market — Web Search (mandatory)

Before drafting any research output, search for real-time data:

1. **Use WebSearch** to find current data points: market reports, funding rounds,
   company announcements, pricing pages, industry trends.
2. **Use WebFetch** to pull specific pages: competitor websites, press releases,
   analyst reports, public financial data, pricing pages, user reviews.
3. **Cross-reference** at least 2-3 sources for any critical claim (market size,
   funding amounts, user counts).
4. **If search returns nothing useful**, state: "Limited real-time data available for X —
   the following is based on training data as of [cutoff]."
5. **Per-query failure handling:** If some searches succeed and others fail, note which
   claims have real-time sourcing and which are based on training data.

Search strategy per sub-mode:
- **Competitor analysis:** search for each competitor by name + "funding", "pricing",
  "reviews 2026", "market share", "revenue", "layoffs", "hiring". Search product
  review sites (G2, Capterra, Product Hunt). Search for negative reviews specifically.
- **Market sizing:** search for "{industry} market size 2026", "{industry} TAM",
  industry analyst reports (Gartner, Statista, IBISWorld, Grand View Research).
  Search for contradicting estimates. Search for bottom-up data (company revenues,
  pricing × customer counts).
- **Idea validation:** search for "{problem} solutions 2026", "{target audience} pain points",
  "{category} startups funded 2026", Reddit/HN discussions about the problem,
  Google Trends for related terms, job postings in the domain.

## Market — Depth Levels

Every research sub-mode supports three depth levels. Auto-detect from the user's prompt,
or ask if unclear.

### Quick Scan (~5 min)
- Executive summary + key findings only
- 3-5 sources minimum
- Top-level numbers without deep verification
- No AskUserQuestion stops (deliver straight through)
- Skip sections marked "standard + deep only"

### Standard (~15 min) — default
- Full mode output with all template sections
- 8-12 sources minimum
- All depth matrix cells filled
- 1-2 AskUserQuestion stops at key decision points
- Include contrarian analysis

### Deep Dive (~30 min)
- Standard + extended analysis sections
- 15+ sources minimum
- Product teardowns (sign up for free trials, analyze UX)
- User review analysis (aggregate sentiment from G2, Capterra, Reddit)
- Pricing intelligence (compare plans, calculate unit economics)
- 2-3 AskUserQuestion stops
- Include all "standard + deep only" sections

## Market — Sub-Modes

Detect the research type from the user's prompt. If ambiguous, ask which sub-mode to use.

---

### Market Sub-Mode 1: Competitor Analysis

**Goal:** Understand the competitive landscape — who's playing, how they're positioned,
and where the gaps are.

Read the competitor analysis template:

```bash
cat "${SKILL_DIR}/market-templates/competitor-analysis.md" 2>/dev/null || cat ~/.claude/skills/tai/research/market-templates/competitor-analysis.md 2>/dev/null
```

**Step 1 — Identify competitors (3-10 total)**

Categorize into three groups:
- **Direct:** Same product, same market (e.g., Notion vs. Coda)
- **Indirect:** Different product, same problem (e.g., Notion vs. Google Docs + Trello)
- **Replacement:** Alternative ways the user solves the problem today (e.g., spreadsheets,
  manual processes, hiring someone)

Apply the **Jobs-to-be-Done lens**: the competitor list should include everything the
customer "hires" to do the same job, not just products in the same category.

**>>> AskUserQuestion STOP** (standard + deep): Present the competitor list and ask:
"I identified these N competitors. Should I go deep on all of them, focus on the top 3-5,
or am I missing any important ones?"

**Step 2 — Build the competitive depth matrix**

Fill every cell in the template's Competitive Depth Matrix with specifics. Apply the
**willingness-to-pay test** and **distribution instinct** when analyzing each competitor.

For **deep dive** depth: also analyze user reviews (aggregate from G2, Capterra, Reddit),
sign up for free tiers to evaluate UX firsthand, and analyze their content/SEO strategy.

**Step 3 — Positioning analysis**

Build the 2x2 positioning map from the template. Choose dimensions that reveal genuine
strategic differences, not obvious ones (avoid "price vs. features" — everyone uses that).

Apply **Blue Ocean / Red Ocean awareness**: is there an empty quadrant, or is the
entire map crowded?

**Step 4 — SWOT synthesis**

Produce the SWOT matrix from the template. Apply the **inversion reflex** to every
strength (how could it become a weakness?) and every opportunity (why might it not
materialize?).

**Step 5 — Positioning gaps**

Identify 2-3 specific positioning opportunities using the template's gap table.
Apply **second-order thinking**: if you fill this gap, what happens next?

**Step 6 — Contrarian analysis**

Fill the contrarian analysis table from the template. The bear case must be genuine —
not "competition is intense" but specific threats with evidence.

**>>> AskUserQuestion STOP** (deep): Present contrarian findings and ask:
"I found some strong bear cases. Want me to dig deeper into any of these risks?"

---

### Market Sub-Mode 2: Market Sizing (TAM/SAM/SOM)

**Goal:** Quantify the market opportunity with investor-grade rigor.

Read the market sizing template:

```bash
cat "${SKILL_DIR}/market-templates/market-sizing.md" 2>/dev/null || cat ~/.claude/skills/tai/research/market-templates/market-sizing.md 2>/dev/null
```

**Step 1 — Define the market**

Fill the Market Definition table from the template. Be precise about inclusion and
exclusion boundaries. Apply **proxy skepticism**: is the market definition too broad
(inflates TAM) or too narrow (misses adjacencies)?

**Step 2 — TAM (top-down)**

Find 2+ analyst estimates. If they disagree by >20%, explain why (different definitions,
methodologies, or geographies). Apply **proxy skepticism** to every number.

**Step 3 — SAM (filtered)**

Show the math explicitly using the template format. Each filter must have a sourced
rationale, not just a percentage.

**>>> AskUserQuestion STOP** (standard + deep): Present TAM → SAM math and ask:
"The SAM calculation depends on these filters. Are these the right boundaries for your
product? Should I include/exclude any segments?"

**Step 4 — SOM (bottom-up)**

Build the bottom-up model using the template. Apply the **distribution instinct**:
the SOM is determined by distribution capacity, not market desire.

**Step 5 — Sanity checks**

Run every sanity check in the template. If any check fails, revise the numbers and
explain why.

**Step 6 — Market dynamics** (standard + deep)

Fill Porter's Five Forces table from the template. Apply **structural analysis** instinct.

**Step 7 — Contrarian analysis**

For each growth assumption, state what would prove it wrong and what leading indicator
to watch.

---

### Market Sub-Mode 3: Idea Validation

**Goal:** Pressure-test a startup idea against real market evidence before building.

Read the idea validation template:

```bash
cat "${SKILL_DIR}/market-templates/idea-validation.md" 2>/dev/null || cat ~/.claude/skills/tai/research/market-templates/idea-validation.md 2>/dev/null
```

**Step 1 — Problem clarity**

Fill the Problem Definition table from the template. Apply the **Jobs-to-be-Done lens**:
what job is the customer hiring this product for? Apply the **willingness-to-pay test**:
is this a problem people pay to solve, or just complain about?

**Step 2 — Target audience definition**

Build the persona table from the template. Apply the **distribution instinct**: can
you actually reach these people?

**>>> AskUserQuestion STOP** (standard + deep): Present the problem definition and
persona. Ask: "Does this match your understanding of the target customer? Should I
adjust the persona before continuing?"

**Step 3 — Demand signals**

Fill every row of the Demand Signals table with sourced data. "No signal found" is
acceptable; leaving rows blank is not. Apply **proxy skepticism**: search volume ≠
purchase intent, community discussion ≠ willingness to pay.

**Step 4 — Competitive gap analysis**

Fill the template's gap analysis table. Apply the **inversion reflex**: "What if existing
solutions are actually good enough?" Apply **timing obsession**: why is the market
timing right NOW?

**Step 5 — Timing analysis** (standard + deep)

Fill the Timing Analysis table from the template. This is where the **timing obsession**
instinct does its deepest work. The "Why not 5 years ago?" and "Why not 5 years from
now?" questions are mandatory.

**Step 6 — Moat assessment** (standard + deep)

Fill the Moat Assessment table from the template. Apply **moat classification** instinct.
Be honest — most early-stage ideas have no moat. The question is whether the business
model creates one over time.

**Step 7 — Go / No-Go scorecard**

Fill the scorecard from the template. Apply **second-order thinking** to the verdict:
if this succeeds, what happens next?

**>>> AskUserQuestion STOP** (deep): Before delivering the final verdict, present the
scorecard and ask: "Based on the evidence, here's where I'm landing. Any data points
I'm missing that could change the verdict?"

---

## Market — Investor-Ready Output Format

When the user requests investor-ready output (or when doing market sizing / idea
validation for fundraising context), overlay the investor template:

```bash
cat "${SKILL_DIR}/market-templates/investor-ready.md" 2>/dev/null || cat ~/.claude/skills/tai/research/market-templates/investor-ready.md 2>/dev/null
```

This is a format overlay, not a new research sub-mode. Any sub-mode's findings can be
restructured into investor-ready format. The key additions:
- 2x2 positioning map
- Comparable company analysis
- Risk factors with mitigations
- Key metrics and benchmarks
- Narrative summary in memo format

## Market — Default Output Structure

Unless the user requests a different format (or investor-ready), structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding
2. **Key Findings** — bulleted, each sourced
3. **Detailed Analysis** — sub-mode-specific sections from template
4. **Contrarian Analysis** — structured table of bear cases
5. **Risks & Caveats** — what could make this research wrong
6. **Recommendation** — concrete, actionable, opinionated
7. **Sources** — numbered list with URLs, dates, and brief descriptions

## Market — Quality Gate

Before delivering, read the quality checklist:

```bash
cat "${SKILL_DIR}/market-references/research-quality-checklist.md" 2>/dev/null || cat ~/.claude/skills/tai/research/market-references/research-quality-checklist.md 2>/dev/null
```

Verify every item. If any check fails, fix the output before delivering.

## Market — Research Persistence

After delivering research, persist findings for cross-referencing in future sessions.

### Session Logging

```bash
mkdir -p ~/.tai-skills/projects/$_SLUG
```

```bash
echo '{"skill":"market-research","timestamp":"TIMESTAMP","mode":"MODE","depth":"DEPTH","topic":"TOPIC","sources":N,"verdict":"VERDICT","output":"PATH_OR_INLINE"}' >> ~/.tai-skills/projects/$_SLUG/research-log.jsonl
```

Substitute: TIMESTAMP = ISO 8601 datetime, MODE = competitor/sizing/validation,
DEPTH = quick/standard/deep, TOPIC = research topic (max 80 chars),
N = number of sources cited, VERDICT = recommendation summary (max 100 chars),
PATH_OR_INLINE = output file path or "inline".

### Market Intelligence Persistence

For standard and deep depth levels, also persist structured findings:

```bash
mkdir -p ~/.tai-skills/projects/$_SLUG/market-intel
```

Write sub-mode-specific files:
- **Competitor analysis** → `market-intel/competitors-{YYYY-MM-DD}.json`
- **Market sizing** → `market-intel/sizing-{YYYY-MM-DD}.json`
- **Idea validation** → `market-intel/validation-{YYYY-MM-DD}.json`

JSON format (keep it simple — these are for cross-referencing, not full reports):

```json
{
  "date": "YYYY-MM-DD",
  "topic": "...",
  "mode": "competitor|sizing|validation",
  "key_findings": ["finding 1", "finding 2"],
  "competitors": [{"name": "...", "type": "direct|indirect|replacement", "funding": "...", "key_signal": "..."}],
  "market_size": {"tam": "...", "sam": "...", "som_y1": "...", "som_y3": "..."},
  "verdict": "...",
  "top_risks": ["risk 1", "risk 2"],
  "sources_count": N
}
```

Include only the fields relevant to the sub-mode. Mark any data >30 days old with
`"stale": true` when loading in future sessions.

## Market — Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting:
   - What market/category?
   - What geography and customer segment?
   - What decision does this research inform?
   - What depth level? (quick scan, standard, deep dive)
2. Do NOT produce generic research — specificity is the whole point

---

# Mode: Design

Design research: competitor UI analysis, design trend exploration, UX pattern research,
and design system research. Produce research that changes how designers and builders
think about their product's visual and interaction design — not a Pinterest board with
no analysis.

## Design — Research Prime Directives

1. **Decision over inspiration.** Research exists to inform a specific design decision,
   not to collect pretty screenshots. If the output doesn't narrow choices, it failed.
2. **Pattern extraction over preference.** Don't say "I like this." Say "this pattern
   works because X, and the data/adoption suggests Y."
3. **Context-aware analysis.** A design pattern that works for Stripe doesn't necessarily
   work for a Japanese B2B SaaS. Always factor in audience, platform, and market.
4. **Specificity kills shallowness.** Never say "use modern design." Say "use 16px body
   text, 48px section spacing, muted accent palette — here's why those values work for
   this use case."
5. **Contrarian evidence is mandatory.** Every "use this pattern" must include at least
   one context where it fails or backfires.
6. **Recency matters.** Design trends shift fast. Prefer sources from the current year.
   Flag anything older than 12 months: `[YYYY — trend may have shifted]`.

## Design — Research Thinking Instincts

1. **User context reflex** — Who is the end user? B2B vs B2C, mobile vs desktop,
   power user vs casual — these change everything about what "good design" means.
2. **Conversion awareness** — Beautiful design that hurts conversion is bad design.
   Research what actually performs, not just what looks good.
3. **Accessibility baseline** — Every design recommendation must pass WCAG AA minimum.
   Flag patterns that sacrifice accessibility for aesthetics.
4. **Cultural sensitivity** — Design conventions differ across markets. Japanese web
   design conventions differ from Western ones. Don't assume universal norms.
5. **Implementation cost** — A design pattern that requires a custom rendering engine
   is different from one achievable with Tailwind. Factor in build cost.
6. **Trend lifecycle** — Is this design trend emerging, peaking, or fading? Glass
   morphism peaked in 2022. Bento grids peaked in 2024. What's current?

## Design — Depth Mode Selection

### Quick Mode (15-20 min)

**When:** Simple "what do others do for X?", quick pattern check.

- 3-5 competitor/reference sites analyzed
- Summary + recommendation
- Skip deep analysis and red team

### Standard Mode (30-45 min) — DEFAULT

**When:** Competitor analysis, design system decisions, UX pattern exploration.

- 8-12 reference sites/products analyzed
- Full analysis with pattern extraction
- Comparative matrix required
- One checkpoint after initial findings

### Deep Mode (1-2 hours)

**When:** Full design language research, major redesign, entering new market.

- 15+ references across multiple categories
- Full analysis with trend mapping
- Historical context (how did we get here?)
- Checkpoints after initial findings AND after pattern synthesis
- Moodboard-style reference collection with URLs

## Design — Web Search (mandatory)

Before drafting any output, search for real-time data and gather visual references via
WebSearch and WebFetch. Cross-reference live implementations rather than relying on
memory. If search returns nothing useful, state: "Limited real-time data available for X —
the following is based on training data as of [cutoff]."

## Design — Sub-Modes

### Design Sub-Mode 1: Competitor UI Analysis

**Goal:** Analyze 3-10 competitor/reference products and extract actionable patterns.

**Steps:**

1. **Identify competitors** — Direct competitors, adjacent products, and aspirational
   references. Ask user if the list isn't clear.
2. **For each product, analyze:**
   - Visual language: color palette, typography, spacing system, imagery style
   - Layout patterns: navigation, content hierarchy, grid system
   - Interaction patterns: forms, modals, transitions, feedback
   - Mobile approach: responsive vs adaptive, native-feel vs web
   - Unique differentiators: what does this product do that others don't?
3. **Build comparison matrix** — Dimensions vs products. Score each 1-5 with notes.
4. **Extract patterns** — What do the best products share? Where do they diverge?
5. **Gaps and opportunities** — What does nobody do well? Where can user differentiate?

**STOP (Standard/Deep).** Present matrix. AskUserQuestion:
"Initial analysis shows {pattern}. Should I dig deeper on any specific aspect?"

6. **Recommendation** — Concrete design direction with rationale.

---

### Design Sub-Mode 2: UX Pattern Research

**Goal:** Find the best UX pattern for a specific interaction or flow.

**Steps:**

1. **Frame the interaction** — What user action? What context? What constraints?
2. **Survey patterns** — Search for established patterns: Material Design, Apple HIG,
   Nielsen Norman Group research, Baymard Institute studies.
3. **Collect real examples** — Find 5-10 live implementations across products.
4. **Evaluate each pattern:**
   - Learnability: How intuitive is it for first-time users?
   - Efficiency: How fast for repeat users?
   - Error rate: How often do users make mistakes?
   - Accessibility: Screen reader, keyboard, touch target compliance?
   - Implementation complexity: How hard to build well?
5. **A/B test data** — Search for published test results comparing patterns.

**STOP (Standard/Deep).** Present pattern options. AskUserQuestion:
"Pattern {X} has strongest evidence for your context. Any constraints I should factor in?"

6. **Recommendation** — Pick one pattern. State when to use alternatives.

---

### Design Sub-Mode 3: Design Trend Exploration

**Goal:** Map current design trends relevant to the user's product category.

**Steps:**

1. **Scope the exploration** — What product category? What audience? What platform?
2. **Survey current trends** — Search design blogs (Designmodo, Muzli, Awwwards),
   conference talks, Dribbble/Behance featured work, product launches.
3. **For each trend, analyze:**
   - What problem does it solve? (or is it purely aesthetic?)
   - Who's adopting it? (startups vs enterprise, which industries?)
   - Lifecycle stage: emerging, mainstream, or declining?
   - Implementation difficulty
   - Accessibility implications
4. **Separate signal from noise** — Which trends reflect real user needs vs designer
   echo chamber? Check: is anyone A/B testing this? Are users requesting it?
5. **Map to user's context** — Which trends are relevant? Which are distractions?

**STOP (Standard/Deep).** Present trend map. AskUserQuestion:
"These trends seem relevant to your product. Any direction you're already leaning?"

6. **Recommendation** — Which trends to adopt, which to watch, which to ignore.

---

### Design Sub-Mode 4: Design System Research

**Goal:** Research design system approaches for building or evolving a product's visual language.

**Steps:**

1. **Understand current state** — Does a design system exist? What's working, what's not?
2. **Survey reference systems** — Research 5-10 established design systems:
   - Open source: Radix, shadcn/ui, Chakra, Ant Design, Carbon
   - Company: Linear, Stripe, Vercel, Notion, Figma
3. **For each system, analyze:**
   - Token architecture: how they structure colors, spacing, typography
   - Component philosophy: composable vs opinionated, headless vs styled
   - Theming approach: CSS variables, design tokens, runtime switching
   - Documentation quality: how maintainable is this long-term?
4. **Extract architecture patterns** — Token naming, scale systems, responsive approaches.
5. **Evaluate fit** — Which approach matches the user's team size, tech stack, and needs?

**STOP (Standard/Deep).** Present options. AskUserQuestion:
"Leaning toward {approach} based on your stack and team. Thoughts?"

6. **Recommendation** — Specific system architecture with implementation notes.

---

## Design — Design Knowledge Reference

Use these to inform analysis — do NOT display as raw tables to the user.

**Aesthetic directions:**
- Brutally Minimal — Type and whitespace only. No decoration. Modernist.
- Maximalist Chaos — Dense, layered, pattern-heavy. Y2K meets contemporary.
- Retro-Futuristic — Vintage tech nostalgia. CRT glow, pixel grids, warm monospace.
- Luxury/Refined — Serifs, high contrast, generous whitespace, precious metals.
- Playful/Toy-like — Rounded, bouncy, bold primaries. Approachable and fun.
- Editorial/Magazine — Strong typographic hierarchy, asymmetric grids, pull quotes.
- Brutalist/Raw — Exposed structure, system fonts, visible grid, no polish.
- Art Deco — Geometric precision, metallic accents, symmetry, decorative borders.
- Organic/Natural — Earth tones, rounded forms, hand-drawn texture, grain.
- Industrial/Utilitarian — Function-first, data-dense, monospace accents, muted palette.

**Font recommendations by purpose:**
- Display/Hero: Satoshi, General Sans, Instrument Serif, Fraunces, Clash Grotesk, Cabinet Grotesk
- Body: Instrument Sans, DM Sans, Source Sans 3, Geist, Plus Jakarta Sans, Outfit
- Data/Tables: Geist (tabular-nums), DM Sans (tabular-nums), JetBrains Mono, IBM Plex Mono
- Code: JetBrains Mono, Fira Code, Berkeley Mono, Geist Mono

**Font blacklist** (never recommend):
Papyrus, Comic Sans, Lobster, Impact, Jokerman, Bleeding Cowboys, Permanent Marker,
Bradley Hand, Brush Script, Hobo, Trajan, Raleway, Clash Display, Courier New (for body)

**Overused fonts** (flag when analyzing competitors):
Inter, Roboto, Arial, Helvetica, Open Sans, Lato, Montserrat, Poppins

**AI slop anti-patterns** (flag when found in competitor analysis):
- Purple/violet gradients as default accent
- 3-column feature grid with icons in colored circles
- Centered everything with uniform spacing
- Uniform bubbly border-radius on all elements
- Gradient buttons as primary CTA pattern
- Generic stock-photo-style hero sections

---

## Design — Default Output Structure

1. **Executive Summary** — 3-5 sentences. Opinionated, not balanced.
2. **Key Findings** — Bulleted, each sourced or referenced.
3. **Detailed Analysis** — Sub-mode-specific sections from above.
4. **Visual References** — URLs to live examples with brief annotations.
5. **Risks & Caveats** — What could make this research wrong.
6. **Recommendation** — Concrete, actionable, opinionated.
   Include: "Choose differently if: {specific conditions}"
7. **Sources** — Numbered list with URLs and dates.

## Design — Completion Summary

```
+====================================================================+
|              DESIGN RESEARCH — COMPLETION SUMMARY                   |
+====================================================================+
| Topic                | {research topic}                             |
| Mode                 | {Competitor/UX Pattern/Trend/Design System}   |
| Depth                | {Quick/Standard/Deep}                        |
| References analyzed  | ___ products/sites                           |
| Patterns extracted   | ___ actionable patterns                      |
| Recommendation       | {one-line summary}                           |
| Key risk             | {biggest caveat}                             |
+====================================================================+
```

## Design — Handling Ambiguity

If the user's prompt is too vague:
1. Ask 2-3 clarifying questions (what product, what audience, what decision this informs)
2. Do NOT produce generic "design trends 2026" output — specificity is the point
3. If still unclear, narrow scope yourself and state what you're NOT covering

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
