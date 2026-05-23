# Layout Selection — Decision Tree (v4)

16 layout components. Given content, select the best layout.

## Decision Tree

```
Content has...
│
├─ Title/name/opening for a presentation?
│  → SlideHero (slides-a.jsx)
│
├─ Chapter/section break?
│  → SlideDivider (slides-a.jsx)
│
├─ One dramatic number with context?
│  → SlideBigNumber (slides-a.jsx)
│
├─ Quote or testimonial?
│  → SlideQuote (slides-a.jsx)
│
├─ Grid of items (features, pillars, use cases)?
│  ├─ With icons + descriptions? → SlideCardGrid cardStyle="default"
│  ├─ Numbered steps (non-sequential)? → SlideCardGrid cardStyle="numbered"
│  ├─ KPI/metric values? → SlideCardGrid cardStyle="metric"
│  ├─ People/team profiles? → SlideCardGrid cardStyle="profile"
│  └─ Sequential flow with arrows? → SlideCardGrid connected={true}
│
├─ Row of 3-4 key metrics?
│  → SlideStatRow (slides-a.jsx)
│
├─ Before/after or two-column comparison with items?
│  → SlideSplit (slides-b.jsx)
│
├─ Structured comparison table?
│  → SlideTable (slides-b.jsx)
│
├─ Gantt-style roadmap with phases?
│  → SlideTimeline (slides-b.jsx)
│
├─ Data visualization?
│  ├─ Trend over time? → SlideChart chartType="line"
│  ├─ Comparing quantities? → SlideChart chartType="bar"
│  └─ Composition/share breakdown? → SlideChart chartType="donut"
│
├─ Agenda / table of contents / numbered list?
│  → SlideList (slides-b.jsx)
│
├─ 2x2 quadrant / priority matrix?
│  → SlideMatrix (slides-c.jsx)
│
├─ Content that doesn't fit other layouts?
│  ├─ Title + single content area? → SlideTitleContent (slides-c.jsx)
│  ├─ Title + two content areas? → SlideTwoColumn (slides-c.jsx)
│  └─ Full canvas, no structure needed? → SlideBlank (slides-c.jsx)
│
└─ Thank you / closing?
   → SlideClosing (slides-c.jsx)
```

## Tiebreakers

| Conflict | Winner | Why |
|----------|--------|-----|
| Stats + narrative | BigNumber if 1 number, StatRow if 3-4, CardGrid metric if 4+ with labels | Count determines |
| Items + flow | CardGrid default if unordered, CardGrid connected if sequential | Order matters |
| Problems + comparison | Split if before/after story, Table if structured data | Emotional vs analytical |
| Steps + features | CardGrid numbered if steps, CardGrid default if features | Verb vs noun |
| Two-column content | Split if before/after, TwoColumn if unrelated sides | Transformation vs parallel |
| Free-form | TitleContent first, TwoColumn if two areas, Blank if fully custom | Prefer structure |

## Component Props Reference

### SlideHero (slides-a.jsx)
```
brand, tag, title, subtitle, meta: {client, clientLabel, leftLabel, leftValue, rightLabel, rightValue}
```

### SlideDivider (slides-a.jsx)
```
numLabel ("01"), titleJp, titleEn, lead
```

### SlideBigNumber (slides-a.jsx)
```
eyebrow, number, unit, titleJp, lead, source
```

### SlideQuote (slides-a.jsx)
```
quote, authorName, authorTitle
```

### SlideCardGrid (slides-a.jsx)
```
eyebrow, titleJp, body, cols (2|3|4), cardStyle ("default"|"numbered"|"metric"|"profile"), connected (bool)

cardStyle="default" cards: [{icon, title, desc}, ...]
cardStyle="numbered" cards: [{title, desc}, ...]
cardStyle="metric" cards: [{value, label, labelEn, delta}, ...]
cardStyle="profile" cards: [{name, nameEn, role, bio}, ...]
connected=true cards: [{icon, title, desc}, ...] (max 5, horizontal with arrows)
```

### SlideStatRow (slides-a.jsx)
```
eyebrow, titleJp, stats: [{value, label, source}, ...]  (3-4 items)
```

### SlideSplit (slides-b.jsx)
```
eyebrow, titleJp, leftLabel, rightLabel, leftItems: [string, ...], rightItems: [string, ...]
leftDark (bool), rightDark (bool, default true)
```

### SlideTable (slides-b.jsx)
```
eyebrow, titleJp, headers: [string, ...], rows: [[string, ...], ...]  (max 6 rows)
```

### SlideTimeline (slides-b.jsx)
```
eyebrow, titleJp, months (default 12)
phases: [{name, jp, start, span, color ("soft"|"accent"|"navy"), milestones: [string, ...]}, ...]
```

### SlideChart (slides-b.jsx)
```
eyebrow, titleJp, chartType ("line"|"bar"|"donut"), summary: [{label, val, accent?}, ...]

chartType="line": series: [{name, data: [number, ...]}, ...], labels: [string, ...]
chartType="bar": data: [number, ...], labels: [string, ...]
chartType="donut": data: [{label, value, color}, ...]
```

### SlideList (slides-b.jsx)
```
eyebrow, titleJp, items: [{jp, en}, ...]  (max 8, 4x2 grid)
```

### SlideMatrix (slides-c.jsx)
```
eyebrow, titleJp, xAxis, yAxis
quadrants: [{label, desc, color, bg, textColor}, ...]  (4 items, ordered: bottom-left, top-left, bottom-right, top-right)
```

### SlideTitleContent (slides-c.jsx)
```
eyebrow, titleJp, children (React element for content area)
```

### SlideTwoColumn (slides-c.jsx)
```
eyebrow, titleJp, left (React element), right (React element), ratio (default "1fr 1fr")
```

### SlideBlank (slides-c.jsx)
```
children (React element — full canvas)
```

### SlideClosing (slides-c.jsx)
```
brand, title, subtitle, contact: {name, email, phone, web}
```

## Available Icons (from icons.jsx)

trend, clock, target, building, shield, globe, compass, cpu,
workflow, chart, database, layers, eye, users, lock, check,
zap, chat, book, arrow, star, grid, rocket, lightbulb, calendar, x
