// Technical report template — clean, professional layout for internal/external reports.
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
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      if counter(page).get().first() > 1 {
        grid(
          columns: (1fr, auto),
          align: (left, right),
          text(size: 9pt, fill: secondary-color, company-name),
          text(size: 9pt, fill: secondary-color)[Technical Report],
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

  // Title block
  v(2cm)
  if logo != none {
    align(right, box(width: 4cm, logo))
    v(0.5cm)
  }

  show heading.where(level: 1): it => {
    v(1em)
    text(size: 16pt, weight: "bold", fill: primary-color, it.body)
    v(0.3em)
    line(length: 40%, stroke: 1.5pt + primary-color)
    v(0.5em)
  }

  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 13pt, weight: "bold", fill: primary-color, it.body)
    v(0.3em)
  }

  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 11pt, weight: "bold", fill: secondary-color, it.body)
    v(0.2em)
  }

  // Table styling
  set table(stroke: 0.5pt + luma(200))

  doc
}
