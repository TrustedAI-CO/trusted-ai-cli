# Quality Checklist — Single Slide

Run before outputting any slide. P0 = blocker.

## P0 — Must Pass

- [ ] **Viewport fit:** slide renders within 1920x1080 canvas without overflow
- [ ] **No scroll:** content fits without scrolling. If not → tell user to split
- [ ] **One message:** slide communicates exactly one idea
- [ ] **Font hierarchy:** display/body = Plus Jakarta Sans, labels = JetBrains Mono, JP = Noto Sans JP
- [ ] **Accent budget:** max 2 accent-colored elements per slide
- [ ] **Density within limits:** content respects layout maximum (see SKILL.md Step 4)
- [ ] **All classes exist:** every CSS class used exists in styles.css
- [ ] **No JSX in output:** all components use React.createElement, no Babel

## P1 — Should Pass

- [ ] **Layout matches intent:** content classified correctly per decision tree
- [ ] **Typography mapping correct:** numbers in stat/mono, labels in micro, titles in .title
- [ ] **No bullet wall:** max 6-8 items in any list
- [ ] **Card variety:** card grids use appropriate cardStyle for content type

## P2 — Polish

- [ ] **4px grid:** dimensions, gaps, padding divisible by 4
- [ ] **No emoji:** use Icon component from icons.jsx
- [ ] **Color tokens only:** no raw hex in slide HTML (use CSS custom properties)
- [ ] **Min text size 24px:** body/desc text minimum 24px on 1920x1080 canvas (18px absolute minimum for micro/labels)
- [ ] **Card gaps >= 24px:** cards in grids need breathing room
- [ ] **Chrome is minimal:** brand mark left + page number right, no section names
- [ ] **No card-dark ghost:** `card-dark` has no `::after` pseudo-element or offset shadow
- [ ] **Underline sits below text:** `.underline::after` at `bottom: -0.05em`, not crossing glyphs
- [ ] **Cover is clean:** Hero slide has no buttons, checkmarks, or extra elements — title + subtitle + meta only
- [ ] **Table cells single-language:** no bilingual text in comparison table cells
