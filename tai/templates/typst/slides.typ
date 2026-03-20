// TrustedAI Slides Template
// Layout adapted from definitely-not-isec-slides.
// Uses shared theme tokens for cross-template consistency.

#import "theme.typ": *

// ──────────────────────────────────────────────
// Slide theme configuration
// ──────────────────────────────────────────────

#let slide-font-size = 20pt
#let slide-heading-size = 24pt
#let slide-title-size = 40pt
#let slide-subtitle-size = 26pt
#let slide-footer-size = 13pt
#let slide-code-size = 13pt

// ──────────────────────────────────────────────
// Title slide
// ──────────────────────────────────────────────

#let title-slide(
  title: "",
  subtitle: none,
  author: "",
  date: datetime.today().display("[month repr:long] [day], [year]"),
  institution: none,
  logo: "brand/logo.png",
  extra: none,
) = {
  set page(
    paper: "presentation-16-9",
    margin: (left: 2.2cm, right: 2.2cm, top: 3.2cm, bottom: 2.2cm),
    fill: tai-warm,
    header: none,
    footer: none,
  )

  // Logo
  if logo != none {
    image(logo, width: 5cm)
    v(0.6cm)
  }

  // Title
  block(width: 85%)[
    #text(font: font-title, size: slide-title-size, weight: "bold", fill: color-text, title)
  ]

  v(0.6cm)

  // Subtitle
  if subtitle != none {
    block(width: 70%)[
      #text(font: font-title, size: slide-subtitle-size, fill: color-primary, weight: "bold", subtitle)
    ]
  }

  v(1.5cm)

  // Author
  block(width: 70%)[
    #text(size: 19pt, weight: "medium", author)
  ]

  v(0.9cm)

  // Extra info (conference, date, etc.)
  if extra != none {
    block(width: 70%)[
      #text(size: 15pt, fill: color-text-muted, extra)
    ]
  } else {
    block(width: 70%)[
      #text(size: 15pt, fill: color-text-muted, date)
    ]
  }
}

// ──────────────────────────────────────────────
// Section divider slide
// ──────────────────────────────────────────────

#let section-slide(title, subtitle: none) = {
  set page(
    paper: "presentation-16-9",
    margin: 2cm,
    fill: color-primary,
    header: none,
    footer: none,
  )

  align(center + horizon)[
    #move(dy: -0.4cm)[
      #text(font: font-title, size: 36pt, weight: "semibold", fill: tai-white, title)
      #if subtitle != none {
        linebreak()
        v(0.3em)
        text(font: font-title, size: 20pt, fill: tai-white.darken(10%), subtitle)
      }
    ]
  ]
}

// ──────────────────────────────────────────────
// Content slide
// ──────────────────────────────────────────────

#let content-slide(
  title: "",
  footer-text: "TrustedAI",
  logo: "brand/logo.png",
  slide-number: none,
  total-slides: none,
  body,
) = {
  set page(
    paper: "presentation-16-9",
    margin: (left: 2.2cm, right: 2.2cm, top: 3.2cm, bottom: 2.2cm),
    fill: tai-warm,
    header: {
      set text(size: slide-heading-size, weight: "semibold")
      text(font: font-title, fill: color-primary, title)
      v(0.5em)
    },
    footer: {
      set text(size: slide-footer-size, fill: color-text-muted)
      if slide-number != none {
        box(
          fill: color-primary,
          inset: (x: 0.4em, y: 0.3em),
        )[
          #set align(center + horizon)
          #text(fill: tai-white, size: 12pt, str(slide-number))
        ]
      }
    },
  )

  set text(font: font-body, size: slide-font-size - 2pt, fill: color-text)
  set par(spacing: 0.65em)
  set list(
    indent: 0.8em,
    spacing: 0.8em,
    marker: move(dy: 0.11cm, square(width: 0.4em, height: 0.4em, fill: color-primary)),
  )
  set enum(
    indent: 0.8em,
    spacing: 0.8em,
    numbering: n => {
      box(
        fill: color-primary,
        inset: (x: 0.3em, y: 0.15em),
      )[
        #text(size: 12pt, fill: tai-white, str(n))
      ]
    },
  )
  show heading.where(level: 1): set text(font: font-title, size: 22pt, fill: color-primary, weight: "bold")
  show heading.where(level: 2): set text(font: font-title, size: 20pt, fill: color-primary, weight: "semibold")
  show heading.where(level: 3): set text(font: font-title, size: 17pt, fill: color-primary, weight: "medium")
  show heading: it => { it + v(0.4em) }
  show link: it => underline(text(fill: tai-blue, it))

  show raw.where(block: true): it => {
    block(
      fill: tai-dark,
      inset: 0.8em,
      radius: 4pt,
      width: 100%,
      text(font: font-mono, size: slide-code-size, fill: tai-white, it),
    )
  }

  body
}

// ──────────────────────────────────────────────
// Two-column slide
// ──────────────────────────────────────────────

#let two-col-slide(
  title: "",
  footer-text: "TrustedAI",
  logo: "brand/logo.png",
  slide-number: none,
  total-slides: none,
  left-body,
  right-body,
) = {
  content-slide(
    title: title,
    footer-text: footer-text,
    logo: logo,
    slide-number: slide-number,
    total-slides: total-slides,
  )[
    #grid(
      columns: (1fr, 1fr),
      gutter: 1.5cm,
      left-body,
      right-body,
    )
  ]
}

// ──────────────────────────────────────────────
// Standout / highlight slide
// ──────────────────────────────────────────────

#let standout-slide(body) = {
  set page(
    paper: "presentation-16-9",
    margin: 3cm,
    fill: color-highlight,
    header: none,
    footer: none,
  )

  align(center + horizon)[
    #text(font: font-title, size: 28pt, weight: "semibold", fill: tai-white, body)
  ]
}

// ──────────────────────────────────────────────
// Quote block (left accent bar)
// ──────────────────────────────────────────────

#let quote-block(color: none, body) = {
  let bar-color = if color != none { color } else { color-primary }
  context {
    let content = align(horizon, body)
    let s = measure(width: 100%, content)
    grid(
      columns: (0.2cm, 0.7cm, auto),
      rect(fill: bar-color, width: 0.2cm, height: s.height + 0.5cm),
      [],
      content,
    )
  }
}

// ──────────────────────────────────────────────
// Color block (callout box for slides)
// ──────────────────────────────────────────────

#let callout(title: none, color: tai-blue, body) = {
  rect(
    fill: color.lighten(90%),
    stroke: (left: 4pt + color),
    inset: (x: 0.8em, y: 0.5em),
    radius: (right: 4pt),
    width: 100%,
  )[
    #if title != none {
      text(weight: "semibold", fill: color, title)
      linebreak()
      v(0.3em)
    }
    #body
  ]
}
