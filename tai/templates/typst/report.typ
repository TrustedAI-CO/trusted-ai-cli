// TrustedAI Full Report Template
// Warm beige aesthetic with bubble-style cover page.
// Structure: cover → abstract → TOC → body.
// Uses shared theme tokens for cross-template consistency.

#import "theme.typ": *

#let full-report(
  title: "",
  subtitle: none,
  author: "",
  affiliation: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  banner: none,
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

  // Decorative circles (bubble style)
  place(top + left, dx: -35%, dy: -28%, circle(radius: 150pt, fill: color-primary))
  place(top + left, dx: -10%, dy: -5%, circle(radius: 75pt, fill: color-secondary.lighten(40%)))
  place(bottom + right, dx: 40%, dy: 30%, circle(radius: 150pt, fill: color-secondary.lighten(50%)))
  place(bottom + right, dx: 15%, dy: 20%, circle(radius: 50pt, fill: color-highlight.lighten(60%)))

  // Banner
  if banner != none {
    place(top + right, dx: -0.5cm, dy: 0.5cm, image(banner, width: 6cm))
  }

  v(2fr)

  // Title block
  align(center)[
    #text(font: font-title, size: size-title, weight: "bold", fill: color-primary, title)
  ]

  if subtitle != none {
    v(0.8em, weak: true)
    align(center, text(font: font-title, size: size-subtitle, weight: "medium", fill: color-secondary, subtitle))
  }

  v(1.2em, weak: true)
  align(center, tai-rule(width: 30%))
  v(1em, weak: true)
  align(center, text(size: size-body, fill: color-text-muted, date))

  v(2fr)

  // Author block
  align(center)[
    #if author != "" { text(weight: "semibold", size: 13pt, author); linebreak() }
    #if affiliation != none { text(fill: color-text-muted, affiliation); linebreak() }
    #if version != none { v(0.4em); tag("v" + version) }
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
      text(weight: "medium", "TrustedAI")
      v(0.3em)
      line(length: 100%, stroke: 0.5pt + tai-border)
    },
  )

  // Table of contents
  outline(indent: 1.5em, depth: 3)
  pagebreak()

  body
}
