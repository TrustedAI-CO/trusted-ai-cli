// TrustedAI Article Template
// Warm, minimal single-page documents — articles, briefs, memos.
// Inspired by fireside's warm beige aesthetic.
// Uses shared theme tokens for cross-template consistency.

#import "theme.typ": *

#let article(
  title: "",
  subtitle: none,
  author: "",
  date: datetime.today().display("[month repr:long] [day], [year]"),
  icon: none,
  show-page-numbers: true,
  body,
) = {
  set document(title: title, author: author)

  // ── Global styles ──────────────────────────
  apply-body-style()
  show heading: set text(font: font-title, fill: color-primary)
  show heading.where(level: 1): it => { v(space-md) + it + v(space-sm) }
  show heading.where(level: 2): it => { v(space-sm) + it + v(space-xs) }

  // ── Page setup ─────────────────────────────
  set page(
    margin: 2.1cm,
    fill: tai-warm,
    numbering: if show-page-numbers { "1" } else { none },
    number-align: center,
    header: none,
  )

  // ── Title block ────────────────────────────
  v(space-lg)
  text(font: font-title, size: size-h1, weight: "bold", fill: color-primary, title)
  if subtitle != none {
    linebreak()
    v(0.3em)
    text(font: font-title, size: size-subtitle, weight: "medium", fill: color-secondary, subtitle)
  }

  v(space-md)

  // ── Author & date ──────────────────────────
  if author != "" {
    text(weight: "semibold", author)
    h(1.5em)
  }
  text(size: size-small, fill: color-text-muted, date)

  v(space-md)
  tai-rule(color: tai-border)
  v(space-lg)

  // ── Body ───────────────────────────────────
  body
}
