---
name: slides
version: 4.0.0
description: |
  [TAI] Render beautiful presentation slides. Takes content for one or more slides,
  selects the best layout from 16 slide types, maps content to typography roles, and
  outputs a single self-contained HTML file. Uses deck-stage web component for
  1920x1080 fixed canvas, keyboard nav, and print-to-PDF. Opens directly from file://
  with no server needed. Use when asked to "make slides", "render this as a slide",
  "present this data", "create a presentation", "build a deck", or any request to
  turn content into presentation slides. No animations. Layout and style focused.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - AskUserQuestion
---

# /slides — Slide Renderer

Turn content into the best possible visual slide(s).
Not a storyteller. A renderer. Focused on layout and style.

**Input:** Content + intent for slide(s).
**Output:** Single self-contained `.html` file. Opens from `file://`, no server needed.

## Philosophy

- **One slide, one message.** If you need two messages, make two slides.
- **Layout is the decision.** The skill's job is picking the right visual form.
- **No animation, no transformation.** Static, clean, layout-focused.
- **Brand is structural.** All colors/fonts from CSS custom properties.

---

## Template System

`assets/` contains the **reference implementation** — the design system source of truth.
Read these files to understand layouts, tokens, and patterns. Do NOT load them at runtime.

```
assets/
├── styles.css         — design tokens + all CSS primitives (INLINE into output)
├── deck-stage.js      — web component: nav, scaling, print (INLINE into output)
├── icons.jsx          — icon library (CONVERT to createElement, inline)
├── slides-a.jsx       — layout reference: hero, divider, big-number, quote, card-grid, stat-row
├── slides-b.jsx       — layout reference: split, table, timeline, chart, list
├── slides-c.jsx       — layout reference: matrix, title-content, two-column, blank, closing
└── AI Solution Proposal Template.html — dev template with all 22 demo slides
```

**Output is always a single `.html` file** with everything inlined.
**Design canvas:** Fixed 1920x1080px. `deck-stage` auto-scales to viewport.
**Navigation:** Arrow keys, PgUp/PgDn, Space, number keys. No scroll.
**Print:** `@media print` outputs one-page-per-slide PDF.
**Opens from:** `file://` — no server needed.

---

## Workflow

```
User provides content
        │
        ▼
Step 1: CLASSIFY — what kind of message is this?
        │
        ▼
Step 2: SELECT LAYOUT — which of 16 layout types fits?
        │
        ▼
Step 3: MAP CONTENT — what goes where in the component props?
        │
        ▼
Step 4: ENFORCE DENSITY — too much? split. too sparse? consolidate.
        │
        ▼
Step 5: RENDER — inline assets, write createElement, assemble HTML
        │
        ▼
Step 6: OPEN — preview in browser
```

### Step 1: Classify

Determine the **intent** of each slide:

| Intent | Signal |
|--------|--------|
| `cover` | Title, opening, presentation name |
| `section` | Chapter/section divider |
| `big-stat` | One dramatic number with context |
| `quote` | Quote or testimonial |
| `cards` | Grid of items (features, pillars, use cases, team, KPIs) |
| `flow` | Sequential pipeline, workflow steps |
| `stats` | Row of key metrics |
| `split` | Before/after, two-column comparison |
| `table` | Structured comparison, feature matrix |
| `timeline` | Gantt-style roadmap with phases |
| `chart` | Data visualization (line, bar, donut) |
| `list` | Agenda, table of contents, numbered items |
| `matrix` | 2x2 quadrant, priority matrix |
| `free-form` | Custom content that doesn't fit other layouts |
| `closing` | Thank you + contact info |

### Step 2: Select Layout

Load `references/layout-selection.md` for full decision tree.

Each intent maps to a React component:

| Intent | Component | Card Style / Variant | File |
|--------|-----------|---------------------|------|
| `cover` | `SlideHero` | — | slides-a.jsx |
| `section` | `SlideDivider` | — | slides-a.jsx |
| `big-stat` | `SlideBigNumber` | — | slides-a.jsx |
| `quote` | `SlideQuote` | — | slides-a.jsx |
| `cards` (features) | `SlideCardGrid` | `cardStyle="default"` | slides-a.jsx |
| `cards` (steps) | `SlideCardGrid` | `cardStyle="numbered"` | slides-a.jsx |
| `cards` (KPIs) | `SlideCardGrid` | `cardStyle="metric"` | slides-a.jsx |
| `cards` (team) | `SlideCardGrid` | `cardStyle="profile"` | slides-a.jsx |
| `flow` | `SlideCardGrid` | `connected={true}` | slides-a.jsx |
| `stats` | `SlideStatRow` | — | slides-a.jsx |
| `split` | `SlideSplit` | — | slides-b.jsx |
| `table` | `SlideTable` | — | slides-b.jsx |
| `timeline` | `SlideTimeline` | — | slides-b.jsx |
| `chart` (line) | `SlideChart` | `chartType="line"` | slides-b.jsx |
| `chart` (bar) | `SlideChart` | `chartType="bar"` | slides-b.jsx |
| `chart` (donut) | `SlideChart` | `chartType="donut"` | slides-b.jsx |
| `list` | `SlideList` | — | slides-b.jsx |
| `matrix` | `SlideMatrix` | — | slides-c.jsx |
| `free-form` (single area) | `SlideTitleContent` | — | slides-c.jsx |
| `free-form` (two areas) | `SlideTwoColumn` | — | slides-c.jsx |
| `free-form` (full canvas) | `SlideBlank` | — | slides-c.jsx |
| `closing` | `SlideClosing` | — | slides-c.jsx |

### Step 3: Map Content

Each component accepts props. Map user content to props:

**Common patterns across components:**
- Title text → main heading prop (`.jp` class)
- Eyebrow → section label prop (uppercase, tracked)
- List items → array prop with `{icon, title, desc}` or `{jp, en}` objects
- Numbers → dedicated stat/value props
- Source/date → meta text

**Typography hierarchy (from styles.css):**
- `.title` — 60-120px, Plus Jakarta Sans 700-800, navy-800
- `.subtitle` — 34-44px, weight 400-500
- `.lead` — 36px, ink-700, weight 400
- `.body` — 28px, ink-500, weight 400
- `.eyebrow` — 22-24px, uppercase, tracked, with coral bar
- `.big-num` — 280-300px, weight 800, navy-900
- `.micro` — 24px, ink-400, tracked

**Card system:**
- `.card` — white bg, border, shadow, rounded-16-20
- `.card-dark` — navy-800 bg, white text, no ghost shadow
- `.card-plain` — white bg, no border, shadow only

### Step 4: Enforce Density

| Layout | Maximum |
|--------|---------|
| Hero | title + subtitle + footer meta. NO buttons, NO checkmarks. |
| Divider | title + lead |
| Big Number | 1 number + context paragraph |
| Quote | 1 quote + attribution |
| Card Grid | 2-8 cards (2-4 columns, 1-2 rows) |
| Card Grid (connected) | 5 steps max (horizontal) |
| Stat Row | 3-4 metrics |
| Split | 4 items per column |
| Table | 6 rows max |
| Timeline | 4 phases on 12-month axis |
| Chart | 1 chart + 4 summary items |
| List | 8 items (4x2 grid) |
| Matrix | 4 quadrants (2x2) |
| Title+Content | title + one content area |
| Two Column | title + two content areas |
| Blank | full creative freedom |
| Closing | contact info block |

**If content exceeds limits:** Tell user → split into multiple slides.

### Step 5: Render

Output is a **single self-contained `.html` file** that opens from `file://`.

1. Read `assets/styles.css` — inline into `<style>` block
2. Read `assets/deck-stage.js` — inline into `<script>` block
3. Read `assets/icons.jsx` — convert Icon components to plain JS `React.createElement`
   calls, inline into `<script>` block
4. Read the relevant `assets/slides-*.jsx` files for selected layouts — use as
   **reference patterns only**. Write slide components as plain `React.createElement`
   calls (no JSX, no Babel needed)
5. Write `SlideChrome` component inline
6. Write `App` component that mounts slides into section portals
7. Assemble single HTML file:
   - Google Fonts + React/ReactDOM from CDN (only external deps)
   - `<style>` with full CSS from styles.css
   - `<deck-stage>` with `<section>` elements
   - `<script>` blocks: deck-stage.js, icons, slide components, app — all plain JS

**Critical rules for single-file output:**
- NO JSX syntax. Use `React.createElement(tag, props, ...children)` or shorthand `h()`
- NO Babel. No `<script type="text/babel">`
- NO external file references (no `src="styles.css"`)
- All CSS inlined in `<style>`
- All JS inlined in `<script>`
- Only CDN: Google Fonts, React 18, ReactDOM 18

**Pattern for converting JSX to createElement:**
```js
// JSX (in assets/ reference):
// <div className="card"><h2 className="title jp">Title</h2></div>

// Plain JS (in output):
const h = React.createElement;
h("div", { className: "card" },
  h("h2", { className: "title jp" }, "Title")
)
```

### Step 6: Open

```bash
open output/index.html  # macOS
```

---

## Design Tokens (from styles.css)

| Token | Value | Usage |
|-------|-------|-------|
| `--navy-900` | `#050A30` | Darkest bg |
| `--navy-800` | `#0A1640` | Primary text, dark cards |
| `--accent` | `#E63946` | Coral accent (configurable) |
| `--accent-soft` | `#FDECEE` | Accent tint bg |
| `--bg-page` | `#FAFBFD` | Slide background |
| `--surface` | `#FFFFFF` | Card background |
| `--fg-body` | `#2B3353` | Body text |
| `--fg-muted` | `#6B7280` | Secondary text |
| `--border-subtle` | `#E5E9F0` | Card borders |

**Fonts:** Plus Jakarta Sans (display/body) + Noto Sans JP (Japanese) + JetBrains Mono (code/labels)

**Canvas:** 1920x1080 fixed. All font sizes in px, not clamp().

---

## Bilingual Content

All slides support JP/EN bilingual content:
- Titles in Japanese (`.jp` class)
- Subtitles/descriptions in English
- `.en-sub` class for English annotations under JP headings
- Use `font-family: var(--font-jp)` for Japanese text

---

## CSS Primitives (from styles.css)

Key classes to use in slide JSX:

| Class | Purpose |
|-------|---------|
| `.slide-pad` | Full-slide padding container |
| `.slide-grid-bg` | Subtle grid texture background |
| `.eyebrow` | Section label with coral bar |
| `.title` | Main heading (supports `.underline` spans) |
| `.card` / `.card-dark` | Content cards |
| `.icon-chip` / `.icon-chip-sm` | Circular icon containers |
| `.pill` / `.pill-accent` / `.pill-navy` | Tag pills |
| `.big-num` | Giant display number |
| `.cmp-table` | Comparison table |
| `.btn` / `.btn-primary` / `.btn-ghost` | Buttons |
| `.row` / `.col` | Flex containers |
| `.gap-16/24/32/48/64` | Gap utilities |

---

## SlideChrome Footer

Every slide (except Hero and Closing) needs a chrome footer:

```jsx
<SlideChrome num={slideNumber} total={totalSlides} />
```

The `SlideChrome` component renders: brand mark left + page number right. No section names.

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Add CSS transitions/animations | Keep static |
| Use inline styles for colors | Use CSS custom properties |
| Create new CSS classes | Use existing primitives from styles.css |
| Overflow slide content | Split into multiple slides |
| Use emoji | Use Icon component from icons.jsx |
| Mix font families arbitrarily | Follow token hierarchy |
| Use text smaller than 18px | Minimum 18px for any readable content; 24px preferred |
| Add CTA buttons or checkmarks on cover | Cover = title + subtitle + meta only |
| Add ghost shadow on card-dark | `card-dark` has no `::after` pseudo-element |
| Put section names in chrome footer | Chrome = brand mark + page number only |
| Use English sub-labels in comparison tables | Keep table cells clean — one language per cell |

---

## File References

| File | Load When |
|------|-----------|
| `references/layout-selection.md` | Step 2 (selecting layout) |
| `references/checklist.md` | Before output (quality gate) |
| `assets/styles.css` | Understanding design tokens |
| `assets/slides-a.jsx` | Reference for Hero, Divider, BigNumber, Quote, CardGrid, StatRow |
| `assets/slides-b.jsx` | Reference for Split, Table, Timeline, Chart, List |
| `assets/slides-c.jsx` | Reference for Matrix, TitleContent, TwoColumn, Blank, Closing |
| `assets/icons.jsx` | Available icon names |
