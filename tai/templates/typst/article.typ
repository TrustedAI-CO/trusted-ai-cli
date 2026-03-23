// TrustedAI Article Template
// Warm, minimal single-page documents — articles, briefs, memos.
// Inspired by fireside's warm beige aesthetic.
// Uses shared theme tokens for cross-template consistency.

#import "theme.typ": *

#let article(
  title: "",
  subtitle: none,
  author: "",
  organization: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  version: none,
  show-logo: true,
  body,
) = {
  set document(title: title, author: author)

  // ── Global styles ──────────────────────────
  apply-body-style()

  show heading: set text(font: font-title, fill: color-primary)
  set heading(numbering: "1.1.")
  show heading.where(level: 1): it => { v(space-md) + it + v(space-sm) }
  show heading.where(level: 2): it => { v(space-sm) + it + v(space-xs) }
  set figure.caption(separator: [ — ], position: top)

  // ── Page setup ─────────────────────────────
  set page(
    margin: 2.1cm,
    fill: tai-warm,
    numbering: "1",
    number-align: center,
  )

  // ── Logo ──────────────────────────────────
  if show-logo {
    image("brand/logo.png", width: 4cm)
    v(space-md)
  }

  // ── Title block ────────────────────────────
  text(font: font-title, size: size-h1, weight: "bold", fill: color-primary, title)
  if subtitle != none {
    linebreak()
    v(0.3em)
    text(font: font-title, size: size-subtitle, weight: "medium", fill: color-secondary, subtitle)
  }

  v(space-md)

  // ── Author & meta ─────────────────────────
  if author != "" {
    text(weight: "semibold", author)
  }
  if organization != none {
    if author != "" { h(0.8em) + text(fill: color-text-muted, "·") + h(0.8em) }
    text(fill: color-text-muted, organization)
  }
  linebreak()
  text(size: size-small, fill: color-text-muted, date)
  if version != none {
    h(0.8em)
    tag("v" + version)
  }

  v(space-md)
  tai-rule(color: tai-border)
  v(space-lg)

  // ── Hide thematic breaks (---) ────────────
  show line: none

  // ── Body ───────────────────────────────────
  body
}
