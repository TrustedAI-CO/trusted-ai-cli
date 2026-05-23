---
name: research-design
version: 1.0.0
description: |
  [TAI] Design research: competitor UI analysis, design trend exploration,
  UX pattern research, and design inspiration gathering. Uses web search +
  screenshots for real-time sourced, decision-oriented design output.
  Use when asked to "research design", "find design inspiration",
  "analyze competitor UIs", or "explore UX patterns".
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# Design Research

Produce research that changes how designers and builders think about their product's
visual and interaction design — not a Pinterest board with no analysis. Output goes
directly to the user unless they specify otherwise.

## Research Prime Directives

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

## Research Thinking Instincts

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

## Depth Mode Selection

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

## Research Modes

### Mode 1: Competitor UI Analysis

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

### Mode 2: UX Pattern Research

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

### Mode 3: Design Trend Exploration

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

### Mode 4: Design System Research

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

## Design Knowledge Reference

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

## Default Output Structure

1. **Executive Summary** — 3-5 sentences. Opinionated, not balanced.
2. **Key Findings** — Bulleted, each sourced or referenced.
3. **Detailed Analysis** — Mode-specific sections from above.
4. **Visual References** — URLs to live examples with brief annotations.
5. **Risks & Caveats** — What could make this research wrong.
6. **Recommendation** — Concrete, actionable, opinionated.
   Include: "Choose differently if: {specific conditions}"
7. **Sources** — Numbered list with URLs and dates.

## Completion Summary

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

## Handling Ambiguity

If the user's prompt is too vague:
1. Ask 2-3 clarifying questions (what product, what audience, what decision this informs)
2. Do NOT produce generic "design trends 2026" output — specificity is the point
3. If still unclear, narrow scope yourself and state what you're NOT covering
