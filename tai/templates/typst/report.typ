// TrustedAI Full Report Template
// Warm beige aesthetic with bubble-style cover page.
// Structure: cover → abstract → TOC → body.
// Uses shared theme tokens for cross-template consistency.

#import "theme.typ": *

#let full-report(
  title: "",
  subtitle: none,
  author: "",
  organization: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  version: none,
  body,
) = {
  set document(author: author, title: title)

  // ── Global styles ──────────────────────────
  apply-body-style()

  show heading: set text(font: font-title, fill: color-primary)
  set heading(numbering: (..nums) => {
    let level = nums.pos().len()
    let pattern = if level == 1 { "I." } else if level == 2 { "I.1." } else { none }
    if pattern != none { numbering(pattern, ..nums) }
  })
  show heading.where(level: 1): it => { v(space-md) + it + v(space-sm) }
  show heading.where(level: 2): it => { v(space-sm) + it + v(space-xs) }
  set figure.caption(separator: [ — ], position: top)

  // ── Cover page ─────────────────────────────
  set page(margin: 2.1cm, fill: tai-warm)

  v(2fr)

  // Logo
  align(center, image("brand/logo.png", width: 5cm))

  // Title block
  align(center)[
    #text(font: font-title, size: size-title, weight: "bold", fill: color-primary, title)
  ]

  if subtitle != none {
    align(center, text(font: font-title, size: size-subtitle, weight: "medium", fill: color-secondary, subtitle))
  }

  v(0.3em)
  align(center, tai-rule(width: 30%))

  v(2fr)

  // Author block
  align(center)[
    #if author != "" { text(weight: "semibold", author) }
    #if organization != none {
      if author != "" { h(0.8em) + text(fill: color-text-muted, "·") + h(0.8em) }
      text(fill: color-text-muted, organization)
    }
    #linebreak()
    #text(size: size-small, fill: color-text-muted, date)
    #if version != none { h(0.8em); tag("v" + version) }
  ]

  v(1fr)
  pagebreak()

  // ── Document body ──────────────────────────
  set page(
    numbering: "1 / 1",
    number-align: center,
    header: {
      set text(size: size-small, fill: color-text-muted)
      emph(title)
      h(1fr)
      emph(author)
      v(0.3em)
      line(length: 100%, stroke: 0.5pt + tai-border)
    },
  )

  // Table of contents
  outline(indent: 1.5em, depth: 3)
  pagebreak()

  // ── Hide thematic breaks (---) ────────────
  show line: none

  body
}
