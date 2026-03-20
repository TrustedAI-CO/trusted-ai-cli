// TrustedAI Shared Design Tokens
// All templates import this file for consistent branding.

// ──────────────────────────────────────────────
// Typography
// ──────────────────────────────────────────────
// Primary: Hanken Grotesk (from fireside). Install with:
//   brew install --cask font-hanken-grotesk font-fira-code
// Fallbacks: Avenir Next → Avenir → system sans-serif

#let font-body = ("Hanken Grotesk", "Avenir Next", "Avenir")
#let font-title = ("Hanken Grotesk", "Avenir Next", "Avenir")
#let font-mono = ("Fira Code", "Menlo", "Courier New")

#let size-body = 11pt
#let size-small = 9pt
#let size-footnote = 8pt
#let size-h1 = 24pt
#let size-h2 = 18pt
#let size-h3 = 14pt
#let size-title = 32pt
#let size-subtitle = 18pt

// ──────────────────────────────────────────────
// Color palette
// ──────────────────────────────────────────────

#let tai-navy = rgb("1a1a6c")
#let tai-blue = rgb("2d4a9f")
#let tai-sky = rgb("5b7fd9")
#let tai-accent = rgb("e85d3a")
#let tai-warm = rgb("f4f1eb")
#let tai-light = rgb("f8f6f2")
#let tai-gray = rgb("6b7280")
#let tai-dark = rgb("1f2937")
#let tai-white = rgb("ffffff")
#let tai-border = rgb("d1d5db")
#let tai-muted = rgb("9ca3af")

// Semantic aliases
#let color-primary = tai-navy
#let color-secondary = tai-blue
#let color-highlight = tai-accent
#let color-bg = tai-warm
#let color-bg-alt = tai-light
#let color-text = tai-dark
#let color-text-muted = tai-gray

// ──────────────────────────────────────────────
// Spacing
// ──────────────────────────────────────────────

#let space-xs = 0.3em
#let space-sm = 0.6em
#let space-md = 1.2em
#let space-lg = 2em
#let space-xl = 3em

// ──────────────────────────────────────────────
// Shared components
// ──────────────────────────────────────────────

/// Horizontal rule with brand color
#let tai-rule(color: tai-blue, width: 100%) = {
  line(length: width, stroke: 1.5pt + color)
}

/// Accent bar (used in headings, sidebars)
#let accent-bar(height: 3pt, color: tai-accent) = {
  rect(width: 100%, height: height, fill: color)
}

/// Blockquote with left accent bar
#let blockquote(body) = {
  rect(
    stroke: (left: 3pt + tai-blue),
    inset: (left: 1em, y: 0.6em),
    fill: tai-light,
    width: 100%,
    body,
  )
}

/// Highlighted inline text
#let highlight-text(body) = {
  text(fill: tai-accent, weight: "semibold", body)
}

/// Tag / badge component
#let tag(label, color: tai-blue) = {
  box(
    fill: color.lighten(85%),
    inset: (x: 0.5em, y: 0.2em),
    outset: (y: 0.2em),
    radius: 3pt,
    text(fill: color, size: size-body, weight: "medium", label),
  )
}

/// Inline code formatter
#let _code-inline(it) = {
  h(0.2em) + box(fill: tai-light, outset: 0.2em, radius: 2pt, text(font: font-mono, size: 0.75em, it)) + h(0.2em)
}

/// Block code formatter
#let _code-block(it) = {
  block(
    fill: tai-white,
    stroke: 1pt + tai-border,
    inset: 1em,
    radius: 4pt,
    width: 100%,
    text(font: font-mono, size: 0.75em, fill: color-text, it),
  )
}

/// Diagram figure with consistent sizing and caption style
#let diagram-figure(path, caption: none, width: 90%) = {
  if caption != none {
    figure(
      image(path, width: width),
      caption: text(size: size-small, fill: color-text-muted, caption),
    )
  } else {
    image(path, width: width)
  }
}

/// Apply shared text and list styling to the current scope
#let apply-body-style() = {
  set text(font: font-body, size: size-body, fill: color-text)
  set par(justify: true, leading: 0.7em)
  set list(indent: 1em, marker: text(fill: tai-blue, "•"))
  set enum(indent: 1em, numbering: n => text(fill: tai-blue, numbering("1.", n)))
  show link: it => underline(text(fill: tai-blue, it))
  show raw.where(block: false): _code-inline
  show raw.where(block: true): _code-block
}
