// Proposal template — company-branded layout with logo, colors, and sections.
//
// Usage: #show: doc => template(doc, company-name: "TrustedAI", logo: image("logo.png"))

#let template(
  doc,
  company-name: "TrustedAI",
  logo: none,
  primary-color: rgb("#1a73e8"),
  secondary-color: rgb("#4a4a4a"),
) = {
  set document(author: company-name)
  set page(
    paper: "a4",
    margin: (top: 3cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      if counter(page).get().first() > 1 {
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(size: 9pt, fill: secondary-color, company-name),
          text(size: 9pt, fill: secondary-color)[Proposal],
        )
        line(length: 100%, stroke: 0.5pt + secondary-color)
      }
    },
    footer: context {
      let page-num = counter(page).get().first()
      let total = counter(page).final().first()
      align(center, text(size: 9pt, fill: secondary-color)[
        #page-num / #total
      ])
    },
  )
  set text(font: "Helvetica Neue", size: 11pt, fill: luma(30))
  set par(justify: true, leading: 0.8em)

  // Title page
  v(4cm)
  if logo != none {
    align(center, box(width: 6cm, logo))
    v(1cm)
  }
  align(center, text(size: 14pt, fill: secondary-color, company-name))
  v(2cm)

  // Heading styles
  show heading.where(level: 1): it => {
    v(1em)
    text(size: 18pt, weight: "bold", fill: primary-color, it.body)
    v(0.5em)
    line(length: 100%, stroke: 1pt + primary-color)
    v(0.5em)
  }

  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 14pt, weight: "bold", fill: primary-color, it.body)
    v(0.3em)
  }

  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 12pt, weight: "bold", fill: secondary-color, it.body)
    v(0.2em)
  }

  doc
}
