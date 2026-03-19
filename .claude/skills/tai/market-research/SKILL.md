---
name: market-research
version: 2.0.0
description: |
  [TAI] Startup market research: competitive analysis, market sizing (TAM/SAM/SOM),
  and idea validation. Uses web search for real-time data, applies startup-specific
  frameworks, and delivers sourced, decision-oriented output.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# Market Research for Startups

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

Produce research that supports decisions, not research theater.
Output goes directly to the user unless they specify otherwise (file, Notion, etc.).

## Preamble (run first)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
_SKILL_DIR=$(dirname "$(find ~/.claude/skills -name 'research-quality-checklist.md' -path '*/market-research/*' 2>/dev/null | head -1)" 2>/dev/null)
_SKILL_DIR="${_SKILL_DIR%/references}"
echo "SKILL_DIR: ${_SKILL_DIR:-NOT_FOUND}"
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
echo "SLUG: $_SLUG"
ls ~/.tai-skills/projects/$_SLUG/market-intel/ 2>/dev/null && echo "PRIOR_RESEARCH: found" || echo "PRIOR_RESEARCH: none"
```

Capture `SKILL_DIR`, `SLUG`, and `PRIOR_RESEARCH` status. If `SKILL_DIR` is `NOT_FOUND`,
fall back to `~/.claude/skills/tai/market-research`.

If `PRIOR_RESEARCH: found`, list the files and ask the user:
"I found existing market research from prior sessions. Want me to build on it or start fresh?"

## When to Activate

- Analyzing competitors in a market or category
- Estimating market size (TAM/SAM/SOM)
- Validating a startup idea before building
- Preparing research for investors, strategy, or product decisions

## Market Thinking Frameworks

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

## Research Standards

1. **Every important claim needs a source.** Use `[Source Name, Date]` inline.
   Prefer official docs, analyst reports, and financial data over blog posts.
2. **Prefer recent data.** Flag anything older than 18 months: `[YYYY data — may be outdated]`.
3. **Include contrarian evidence.** Every bullish finding needs at least one genuine
   bearish counterpoint. Apply the inversion reflex.
4. **Separate fact, inference, and recommendation.** Label each clearly.
5. **Translate findings into a decision.** End with a concrete recommendation, not a summary.
6. **Specificity over generality.** Never write "large market" — write "$4.2B [Gartner, 2025]."
   Never write "strong growth" — write "24% CAGR [Statista, 2025]."

## Web Search (mandatory)

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

Search strategy per mode:
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

## Depth Levels

Every research mode supports three depth levels. Auto-detect from the user's prompt,
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

## Research Modes

Detect the research type from the user's prompt. If ambiguous, ask which mode to use.

---

### Mode 1: Competitor Analysis

**Goal:** Understand the competitive landscape — who's playing, how they're positioned,
and where the gaps are.

Read the competitor analysis template:

```bash
cat "${SKILL_DIR}/templates/competitor-analysis.md" 2>/dev/null || cat ~/.claude/skills/tai/market-research/templates/competitor-analysis.md 2>/dev/null
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

### Mode 2: Market Sizing (TAM/SAM/SOM)

**Goal:** Quantify the market opportunity with investor-grade rigor.

Read the market sizing template:

```bash
cat "${SKILL_DIR}/templates/market-sizing.md" 2>/dev/null || cat ~/.claude/skills/tai/market-research/templates/market-sizing.md 2>/dev/null
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

### Mode 3: Idea Validation

**Goal:** Pressure-test a startup idea against real market evidence before building.

Read the idea validation template:

```bash
cat "${SKILL_DIR}/templates/idea-validation.md" 2>/dev/null || cat ~/.claude/skills/tai/market-research/templates/idea-validation.md 2>/dev/null
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

## Investor-Ready Output Format

When the user requests investor-ready output (or when doing market sizing / idea
validation for fundraising context), overlay the investor template:

```bash
cat "${SKILL_DIR}/templates/investor-ready.md" 2>/dev/null || cat ~/.claude/skills/tai/market-research/templates/investor-ready.md 2>/dev/null
```

This is a format overlay, not a new research mode. Any mode's findings can be
restructured into investor-ready format. The key additions:
- 2x2 positioning map
- Comparable company analysis
- Risk factors with mitigations
- Key metrics and benchmarks
- Narrative summary in memo format

## Default Output Structure

Unless the user requests a different format (or investor-ready), structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding
2. **Key Findings** — bulleted, each sourced
3. **Detailed Analysis** — mode-specific sections from template
4. **Contrarian Analysis** — structured table of bear cases
5. **Risks & Caveats** — what could make this research wrong
6. **Recommendation** — concrete, actionable, opinionated
7. **Sources** — numbered list with URLs, dates, and brief descriptions

## Quality Gate

Before delivering, read the quality checklist:

```bash
cat "${SKILL_DIR}/references/research-quality-checklist.md" 2>/dev/null || cat ~/.claude/skills/tai/market-research/references/research-quality-checklist.md 2>/dev/null
```

Verify every item. If any check fails, fix the output before delivering.

## Research Persistence

After delivering research, persist findings for cross-referencing in future sessions.

### Session Logging

```bash
_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || echo "project")
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

Write mode-specific files:
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

Include only the fields relevant to the mode. Mark any data >30 days old with
`"stale": true` when loading in future sessions.

## Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting:
   - What market/category?
   - What geography and customer segment?
   - What decision does this research inform?
   - What depth level? (quick scan, standard, deep dive)
2. Do NOT produce generic research — specificity is the whole point
