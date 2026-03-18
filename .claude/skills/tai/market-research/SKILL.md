---
name: market-research
version: 1.0.0
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
---

# Market Research for Startups

Produce research that supports decisions, not research theater.
Output goes directly to the user unless they specify otherwise (file, Notion, etc.).

## When to Activate

- Analyzing competitors in a market or category
- Estimating market size (TAM/SAM/SOM)
- Validating a startup idea before building
- Preparing research for investors, strategy, or product decisions

## Research Standards

1. **Every important claim needs a source.** Use `[Source Name, Date]` inline.
2. **Prefer recent data.** Flag anything older than 18 months: `[YYYY data — may be outdated]`.
3. **Include contrarian evidence.** Every bullish finding needs at least one bearish counterpoint.
4. **Separate fact, inference, and recommendation.** Label each clearly.
5. **Translate findings into a decision.** End with a concrete recommendation, not a summary.

## Web Search (mandatory)

Before drafting any research output, search for real-time data:

1. **Use WebSearch** to find current data points: market reports, funding rounds,
   company announcements, pricing pages, industry trends.
2. **Use WebFetch** to pull specific pages: competitor websites, press releases,
   analyst reports, public financial data.
3. **Cross-reference** at least 2-3 sources for any critical claim.
4. **If search returns nothing useful**, state: "Limited real-time data available for X —
   the following is based on training data as of [cutoff]."

Search strategy per mode:
- **Competitor analysis:** search for each competitor by name + "funding", "pricing",
  "reviews", "market share", and the current year
- **Market sizing:** search for "{industry} market size {year}", "{industry} TAM",
  industry analyst reports (Gartner, Statista, IBISWorld, Grand View Research)
- **Idea validation:** search for "{problem} solutions", "{target audience} pain points",
  "{category} startups funded {year}"

## Research Modes

Detect the research type from the user's prompt. If ambiguous, ask which mode to use.

---

### Mode 1: Competitor Analysis

**Goal:** Understand the competitive landscape — who's playing, how they're positioned,
and where the gaps are.

**Step 1 — Identify competitors (3-10 total)**

Categorize into three groups:
- **Direct:** Same product, same market (e.g., Notion vs. Coda)
- **Indirect:** Different product, same problem (e.g., Notion vs. Google Docs + Trello)
- **Replacement:** Alternative ways the user solves the problem today (e.g., spreadsheets, manual processes)

**Step 2 — Build the competitive matrix**

For each competitor, research and present:

| Dimension | What to find |
|-----------|-------------|
| Product | Core features, UX quality, platform coverage |
| Pricing | Plans, pricing model, free tier, enterprise pricing |
| Traction | Users, revenue, growth signals (job postings, web traffic, app store reviews) |
| Funding | Total raised, last round, investors, valuation if known |
| Distribution | How they acquire customers (SEO, sales, partnerships, PLG) |
| Strengths | What they do well — be honest |
| Weaknesses | Where they fall short — look at negative reviews, support forums, churn signals |

**Step 3 — SWOT synthesis**

Produce a SWOT matrix comparing the user's position against the competitive landscape:
- **Strengths:** Where you have an edge
- **Weaknesses:** Where competitors outperform you
- **Opportunities:** Gaps no competitor is filling well
- **Threats:** Competitive moves that could hurt you

**Step 4 — Positioning gaps**

Identify 2-3 specific positioning opportunities:
- Underserved segments competitors ignore
- Feature gaps across the category
- Pricing gaps (overpriced incumbents, no mid-market option, etc.)

---

### Mode 2: Market Sizing (TAM/SAM/SOM)

**Goal:** Quantify the market opportunity with investor-grade rigor.

**Step 1 — Define the market**

Clearly state:
- What product/service category
- What geography
- What customer segment (B2B, B2C, enterprise, SMB, etc.)

**Step 2 — TAM (Total Addressable Market)**

Use **top-down** approach:
1. Find industry-level market size from analyst reports
2. Note the source, date, and growth rate (CAGR)
3. State assumptions clearly

**Step 3 — SAM (Serviceable Addressable Market)**

Narrow TAM by applying filters:
- Geographic reach (which countries/regions you can serve)
- Customer segment fit (enterprise only? SMB only?)
- Product capability constraints
- Regulatory or licensing barriers

Show the math: `TAM × filter1 × filter2 = SAM`

**Step 4 — SOM (Serviceable Obtainable Market)**

Use **bottom-up** approach:
1. Estimate realistic customer acquisition per channel
2. Apply conversion rates from comparable startups
3. Factor in competition: if 3 players hold 80% share, acknowledge it
4. Project 1-year and 3-year SOM

Show the math: `units × price = revenue`

**Step 5 — Sanity check**

- Does bottom-up SOM make sense relative to top-down TAM?
- Are growth assumptions realistic given comparable companies?
- What would need to be true for these numbers to be wrong?

**Output format for this mode:**

```
TAM: $X  (source, date, CAGR X%)
 └─ SAM: $Y  (filters applied: ...)
     └─ SOM: $Z  (year 1) → $W (year 3)
         └─ Assumptions: ...
```

---

### Mode 3: Idea Validation

**Goal:** Pressure-test a startup idea against real market evidence before building.

**Step 1 — Problem clarity**

Answer:
- What specific problem does this solve?
- Who experiences this problem? (be precise — not "everyone")
- How do they solve it today? (existing alternatives, workarounds)
- How painful is it? (frequency, cost, emotional weight)

**Step 2 — Target audience definition**

Build a buyer persona:
- Demographics: role, company size, industry, geography
- Psychographics: values, priorities, buying behavior
- Behavioral: where they look for solutions, how they evaluate, who decides

**Step 3 — Demand signals**

Search for evidence that people want this:
- Search volume for related terms (Google Trends)
- Community discussions (Reddit, HN, Twitter/X, forums)
- Existing solutions and their traction (funded competitors = demand exists)
- Job postings mentioning the problem domain
- Industry reports projecting growth in the category

**Step 4 — Competitive gap analysis**

- Are existing solutions good enough? If yes, what's your differentiation?
- Are they too expensive, too complex, missing a segment?
- Is the market timing right? (enabling technology, regulatory change, behavior shift)

**Step 5 — Go / No-Go assessment**

Deliver a clear recommendation:

| Signal | Bullish | Bearish |
|--------|---------|---------|
| Problem severity | Real, frequent, costly | Mild inconvenience |
| Existing solutions | Poor, overpriced, fragmented | Strong incumbent, satisfied users |
| Market timing | Enabling trends emerging | Stable market, no catalyst |
| Target audience | Reachable, willing to pay | Hard to reach, price-sensitive |
| Competitive moat | Clear differentiation | Easy to replicate |

Final verdict: **GO** / **CONDITIONAL GO** (with conditions) / **NO-GO** (with reasons)

---

## Default Output Structure

Unless the user requests a different format, structure all research as:

1. **Executive Summary** — 3-5 sentences, the headline finding
2. **Key Findings** — bulleted, each sourced
3. **Detailed Analysis** — mode-specific sections above
4. **Risks & Caveats** — what could make this research wrong
5. **Recommendation** — concrete, actionable, opinionated
6. **Sources** — numbered list with URLs, dates, and brief descriptions

## Quality Gate

Before delivering, verify:
- [ ] All quantitative claims have a source or are labeled as estimates
- [ ] Data older than 18 months is flagged
- [ ] At least one contrarian argument or risk is included per major finding
- [ ] The recommendation follows logically from the evidence
- [ ] Web search was used for real-time data (not just training data)
- [ ] The output makes a specific decision easier — not just "more informed"

## Handling Ambiguity

If the user's prompt is too vague to produce useful research:
1. Ask 2-3 clarifying questions before starting (market, geography, stage, what decision this informs)
2. Do NOT produce generic research — specificity is the whole point
